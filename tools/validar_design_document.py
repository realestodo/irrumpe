#!/usr/bin/env python3
"""Deterministic validator + upsert-payload builder for Irrumpe Designer documents.

WHY THIS EXISTS
---------------
A Designer "design" is a Brand Center item whose ``typed_payload`` carries a Konva
``EditorDocument``. The MCP write tool (``brand_center_item_upsert``) only checks
that ``typed_payload`` is a JSON object — it never validates the Konva schema. So a
structurally-valid-JSON but Konva-invalid document persists WITHOUT an API error,
then the Designer rejects it on open (``parseEditorDocument`` returns null). With the
Front F1 fix that now blocks a corrupt item instead of silently overwriting it, the
practical consequence of a bad remote write is "the design will not open" rather than
data loss — but either way the author must be told BEFORE the upsert.

This tool is the pre-flight: it mirrors ``parseEditorDocument`` exactly so a remote
agent can guarantee the document will hydrate, and it builds the precise
``brand_center_item_upsert`` arguments (so the envelope is never hand-assembled — the
marketplace rule is "tools own determinism, skills own judgment").

CONTRACT PROVENANCE (keep in sync with the Front source of truth)
-----------------------------------------------------------------
Mirrors ``Irrumpe Front/app/lib/editor/editor-model.ts``:
  - ``parseEditorDocument``      (version === 1, pages[] each isValidPage)
  - ``isValidPage``              (id/name string, durationSeconds finite-if-present, layers[])
  - ``isValidLayerBase``         (id/name string, x/y/rotation/opacity finite, visible/locked bool, parentId null|string)
  - ``isValidLayer``             (per-type required fields for the 11 layer types)
  - ``isCellMatrix``             (table.cells: non-empty rectangular string matrix)
And the envelope from ``editor-brand-library.ts`` ``designTypedPayload`` +
the MCP tool input schema in ``Irrumpe API/cloudflare/mcp-gateway/src/tools/index.ts``
(FLAT args, NOT wrapped in a ``payload`` object).

When the Front validator changes, bump CONTRACT_VERSION and re-run ``--self-test``.
Code comments are in English per the marketplace universal tool exception; JSON field
names are identifiers and stay in English.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from typing import Any

CONTRACT_VERSION = "1"

# Version of the deterministic layout lint (geometry-only, warnings-only).
LAYOUT_LINT_VERSION = "1"

# parseEditorDocument pins this exact value; any other version returns null (corrupt).
DOCUMENT_VERSION = 1

LAYER_TYPES = {
    "frame", "rect", "ellipse", "text", "image", "video",
    "lottie", "icon", "shape", "table", "chart",
}

# resolveChartKind degrades anything outside this set to "bar"; not a parse error.
KNOWN_CHART_KINDS = {"bar", "line", "area", "pie", "donut"}

ANIMATION_EASINGS = {"linear", "ease-in", "ease-out", "ease-in-out", "back-out"}

# Image/video src must resolve to a loadable, export-safe URL. media:// is the
# unresolved Brand Center placeholder; bare http (non-TLS) and unknown schemes
# either fail to load or taint the export canvas.
_SAFE_SRC_PREFIXES = ("https://", "data:")


# ---- structural predicates (mirror editor-model.ts helpers) ----------------------

def _is_record(value: Any) -> bool:
    return isinstance(value, dict)


def _is_string(value: Any) -> bool:
    return isinstance(value, str)


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_finite_number(value: Any) -> bool:
    # JSON numbers only. bool is a subclass of int in Python — exclude it so a
    # stray `true` in a numeric slot is not silently accepted.
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, float)) and math.isfinite(value)


class Report:
    """Accumulates errors (REJECT class: the document will not parse) and warnings
    (the document parses but renders wrong or degrades)."""

    def __init__(self) -> None:
        self.errors: list[dict[str, str]] = []
        self.warnings: list[dict[str, str]] = []

    def error(self, path: str, code: str, expected: str, got: Any, layer_type: str | None = None) -> None:
        entry = {"path": path, "code": code, "expected": expected, "got": _describe(got)}
        if layer_type:
            entry["layer_type"] = layer_type
        self.errors.append(entry)

    def warn(self, path: str, code: str, message: str, layer_type: str | None = None) -> None:
        entry = {"path": path, "code": code, "message": message}
        if layer_type:
            entry["layer_type"] = layer_type
        self.warnings.append(entry)


def _describe(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value[:60])
    if isinstance(value, list):
        return f"array(len={len(value)})"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


# ---- layer validation (mirror isValidLayerBase + isValidLayer) -------------------

def _require_finite(report: Report, layer: dict, key: str, path: str, ltype: str) -> None:
    if not _is_finite_number(layer.get(key)):
        report.error(f"{path}.{key}", "REQUIRED_FINITE_NUMBER", "finite number", layer.get(key), ltype)


def _require_string(report: Report, layer: dict, key: str, path: str, ltype: str) -> None:
    if not _is_string(layer.get(key)):
        report.error(f"{path}.{key}", "REQUIRED_STRING", "string", layer.get(key), ltype)


def _require_bool(report: Report, layer: dict, key: str, path: str, ltype: str) -> None:
    if not _is_bool(layer.get(key)):
        report.error(f"{path}.{key}", "REQUIRED_BOOLEAN", "boolean", layer.get(key), ltype)


def _validate_layer_base(report: Report, layer: dict, path: str, ltype: str) -> None:
    _require_string(report, layer, "id", path, ltype)
    _require_string(report, layer, "name", path, ltype)
    for key in ("x", "y", "rotation", "opacity"):
        _require_finite(report, layer, key, path, ltype)
    _require_bool(report, layer, "visible", path, ltype)
    _require_bool(report, layer, "locked", path, ltype)
    parent = layer.get("parentId")
    if not (parent is None or _is_string(parent)):
        report.error(f"{path}.parentId", "REQUIRED_NULL_OR_STRING", "null or string", parent, ltype)


def _is_cell_matrix(value: Any) -> bool:
    if not isinstance(value, list) or len(value) == 0:
        return False
    first = value[0]
    if not isinstance(first, list) or len(first) == 0:
        return False
    width = len(first)
    return all(
        isinstance(row, list) and len(row) == width and all(_is_string(c) for c in row)
        for row in value
    )


def _validate_animation(report: Report, layer: dict, path: str, ltype: str) -> None:
    # isValidAnimation: an invalid spec is DROPPED on parse (the layer becomes
    # static), never a parse error — so this is a WARN, not an error.
    anim = layer.get("animation")
    if anim is None:
        return
    ok = (
        _is_record(anim)
        and (anim.get("entrance") is None or _is_string(anim.get("entrance")))
        and (anim.get("exit") is None or _is_string(anim.get("exit")))
        and _is_finite_number(anim.get("delay")) and anim.get("delay") >= 0
        and _is_finite_number(anim.get("duration")) and anim.get("duration") >= 0
        and _is_finite_number(anim.get("exitDuration")) and anim.get("exitDuration") >= 0
        and (
            anim.get("timeOnScreen") is None
            or (_is_finite_number(anim.get("timeOnScreen")) and anim.get("timeOnScreen") >= 0)
        )
        and _is_string(anim.get("easing"))
        and anim.get("easing") in ANIMATION_EASINGS
    )
    if not ok:
        report.warn(
            f"{path}.animation", "ANIMATION_DROPPED",
            "animation spec is invalid and will be dropped on parse (layer renders static)",
            ltype,
        )


def _warn_src(report: Report, layer: dict, path: str, ltype: str) -> None:
    src = layer.get("src")
    if not _is_string(src):
        return  # missing/invalid src is already a REJECT via _require_string
    if src.startswith("media://"):
        report.warn(
            f"{path}.src", "SRC_PLACEHOLDER",
            "src is an unresolved media:// placeholder — upload to R2 and use the public URL",
            ltype,
        )
    elif not src.startswith(_SAFE_SRC_PREFIXES):
        report.warn(
            f"{path}.src", "SRC_NOT_LOADABLE",
            "src is not an https:// or data: URL — the canvas may not load it and exports can taint",
            ltype,
        )


def _warn_font(report: Report, layer: dict, path: str, ltype: str) -> None:
    family = layer.get("fontFamily")
    if _is_string(family) and "," not in family:
        report.warn(
            f"{path}.fontFamily", "FONT_NOT_A_STACK",
            "fontFamily has no fallback (no comma) — use a full CSS stack like '\"Brand\", sans-serif'",
            ltype,
        )


def _validate_layer(report: Report, layer: Any, path: str) -> None:
    if not _is_record(layer):
        report.error(path, "LAYER_NOT_OBJECT", "object", layer)
        return
    ltype = layer.get("type")
    if ltype not in LAYER_TYPES:
        report.error(f"{path}.type", "UNKNOWN_LAYER_TYPE", f"one of {sorted(LAYER_TYPES)}", ltype)
        return

    _validate_layer_base(report, layer, path, ltype)
    _validate_animation(report, layer, path, ltype)

    if ltype in ("frame", "rect"):
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
        _require_string(report, layer, "fill", path, ltype)
    elif ltype == "ellipse":
        _require_finite(report, layer, "radiusX", path, ltype)
        _require_finite(report, layer, "radiusY", path, ltype)
        _require_string(report, layer, "fill", path, ltype)
    elif ltype == "text":
        _require_string(report, layer, "text", path, ltype)
        _require_finite(report, layer, "fontSize", path, ltype)
        _require_string(report, layer, "fill", path, ltype)
        _require_finite(report, layer, "width", path, ltype)
        _warn_font(report, layer, path, ltype)
    elif ltype in ("image", "video"):
        _require_string(report, layer, "src", path, ltype)
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
        _warn_src(report, layer, path, ltype)
    elif ltype == "lottie":
        _require_string(report, layer, "src", path, ltype)
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
        fmt = layer.get("format")
        if fmt is not None and not _is_string(fmt):
            report.error(f"{path}.format", "OPTIONAL_STRING", "string or absent", fmt, ltype)
        _warn_src(report, layer, path, ltype)
    elif ltype == "icon":
        _require_string(report, layer, "iconId", path, ltype)
        _require_string(report, layer, "fill", path, ltype)
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
    elif ltype == "shape":
        # shapeId is REQUIRED even when pathData is supplied: pathData overrides
        # at render but isValidLayer still demands shapeId (editor-model.ts).
        _require_string(report, layer, "shapeId", path, ltype)
        _require_string(report, layer, "fill", path, ltype)
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
    elif ltype == "table":
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
        if not _is_cell_matrix(layer.get("cells")):
            report.error(f"{path}.cells", "TABLE_CELLS_MATRIX",
                         "non-empty rectangular string[][] (all rows equal length)",
                         layer.get("cells"), ltype)
        _require_bool(report, layer, "headerRow", path, ltype)
        _require_bool(report, layer, "bandedRows", path, ltype)
        _require_finite(report, layer, "fontSize", path, ltype)
        for key in ("textFill", "headerTextFill", "borderFill", "headerFill", "cellFill", "bandFill"):
            _require_string(report, layer, key, path, ltype)
    elif ltype == "chart":
        _require_string(report, layer, "chartKind", path, ltype)
        _require_finite(report, layer, "width", path, ltype)
        _require_finite(report, layer, "height", path, ltype)
        _validate_chart_data(report, layer, path, ltype)
        palette = layer.get("palette")
        if not (isinstance(palette, list) and all(_is_string(c) for c in palette)):
            report.error(f"{path}.palette", "CHART_PALETTE", "array of strings", palette, ltype)
        elif len(palette) == 0:
            report.warn(f"{path}.palette", "CHART_PALETTE_EMPTY",
                        "empty palette — slices fall back to a default color", ltype)
        for key in ("showLabels", "showValues", "showGrid"):
            _require_bool(report, layer, key, path, ltype)
        _require_string(report, layer, "textFill", path, ltype)
        _require_finite(report, layer, "fontSize", path, ltype)
        kind = layer.get("chartKind")
        if _is_string(kind) and kind not in KNOWN_CHART_KINDS:
            report.warn(f"{path}.chartKind", "CHART_KIND_UNKNOWN",
                        f"'{kind}' is not one of {sorted(KNOWN_CHART_KINDS)} — renders as bar", ltype)
        _warn_font(report, layer, path, ltype)


def _validate_chart_data(report: Report, layer: dict, path: str, ltype: str) -> None:
    data = layer.get("data")
    if not (isinstance(data, list) and len(data) > 0):
        report.error(f"{path}.data", "CHART_DATA_NONEMPTY", "non-empty array", data, ltype)
        return
    all_ok = True
    for i, point in enumerate(data):
        if not (_is_record(point) and _is_string(point.get("label")) and _is_finite_number(point.get("value"))):
            report.error(f"{path}.data[{i}]", "CHART_POINT", "{ label: string, value: finite }", point, ltype)
            all_ok = False
    if all_ok and all(p.get("value", 0) <= 0 for p in data):
        report.warn(f"{path}.data", "CHART_DATA_NONPOSITIVE",
                    "all values are <= 0 — the chart renders as a neutral empty-state", ltype)


# ---- layout lint (geometry-only, warnings-only) ----------------------------------
#
# The model composing a document remotely has no eyes: it cannot see a 3px
# misalignment, an element poking out of the artboard, or white text on a white
# card. All of that IS computable from the document's absolute geometry, so this
# section lints it deterministically. Every finding is a WARNING (never an error):
# rotated "intervention" elements (price badges, washi strips) and deliberate
# overflow are legitimate design, and warnings never block human curation.
#
# Exemptions by design:
#   - layers with rotation != 0 are skipped by alignment/spacing/overlap checks
#     (bounds are still checked via their rotated AABB);
#   - a child covering >= FULL_BLEED_COVERAGE of its frame is a background and is
#     exempt from the out-of-frame check;
#   - invisible layers and zero-opacity layers are skipped entirely.
#
# Text height is an ESTIMATE (average glyph width ~= 0.55 * fontSize); messages
# say so. True text metrics require the real font — that is the server-side
# render's job, out of scope here.

_LINT_EQ_EPS = 0.75          # values closer than this count as "the same edge"
_LINT_EDGE_TOL = 6.0         # max offset from an anchor edge to call it "almost aligned"
_LINT_BOUNDS_TOL = 1.0       # slack before reporting an out-of-frame overflow (px)
_LINT_FULL_BLEED = 0.97      # frame-coverage ratio that marks a background layer
_LINT_GAP_SPREAD_MIN = 1.5   # gap spread below this is treated as already even
_LINT_GAP_SPREAD_MAX = 8.0   # gap spread above this reads as intentional rhythm
_LINT_GAP_CHAIN_BREAK = 300  # a gap larger than this breaks a vertical stack chain
_LINT_MIN_CONTRAST = 2.0     # WCAG ratio below this is flagged (4.5 is the AA bar)
_LINT_AVG_GLYPH_RATIO = 0.55  # estimated average glyph width as a fontSize fraction


def _lint_layer_visible(layer: dict) -> bool:
    if layer.get("visible") is False:
        return False
    opacity = layer.get("opacity")
    return not (_is_finite_number(opacity) and opacity <= 0)


def _estimated_text_height(layer: dict) -> float:
    font_size = float(layer.get("fontSize", 0))
    width = float(layer.get("width", 0))
    line_height = layer.get("lineHeight")
    lh = float(line_height) if _is_finite_number(line_height) and line_height > 0 else 1.2
    text = layer.get("text") or ""
    chars_per_line = max(1, int(width / max(1.0, _LINT_AVG_GLYPH_RATIO * font_size)))
    lines = 0
    for raw_line in text.split("\n"):
        lines += max(1, math.ceil(len(raw_line) / chars_per_line))
    return max(font_size * lh, lines * font_size * lh)


def _layer_size(layer: dict) -> "tuple[float, float] | None":
    """Unrotated (width, height) of a layer, estimating text height."""
    ltype = layer.get("type")
    if ltype == "ellipse":
        return float(layer["radiusX"]) * 2, float(layer["radiusY"]) * 2
    if ltype == "text":
        return float(layer["width"]), _estimated_text_height(layer)
    if ltype in ("frame", "rect", "image", "video", "lottie", "icon", "shape", "table", "chart"):
        return float(layer["width"]), float(layer["height"])
    return None


def _layer_aabb(layer: dict) -> "tuple[float, float, float, float] | None":
    """Axis-aligned bounding box (x0, y0, x1, y1); rotation pivots on (x, y)."""
    size = _layer_size(layer)
    if size is None:
        return None
    x, y = float(layer["x"]), float(layer["y"])
    w, h = size
    rotation = float(layer.get("rotation") or 0) % 360.0
    if rotation == 0:
        return x, y, x + w, y + h
    rad = math.radians(rotation)
    cos_r, sin_r = math.cos(rad), math.sin(rad)
    xs, ys = [], []
    for dx, dy in ((0.0, 0.0), (w, 0.0), (0.0, h), (w, h)):
        xs.append(x + dx * cos_r - dy * sin_r)
        ys.append(y + dx * sin_r + dy * cos_r)
    return min(xs), min(ys), max(xs), max(ys)


def _aabb_intersection_area(a: "tuple[float, float, float, float]",
                            b: "tuple[float, float, float, float]") -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return w * h if w > 0 and h > 0 else 0.0


def _lint_name(layer: dict) -> str:
    return f"'{layer.get('name')}' (id={layer.get('id')})"


def _parse_hex_color(value: Any) -> "tuple[float, float, float] | None":
    """Returns (r, g, b) in 0..255 for opaque #rgb/#rrggbb/#rrggbbaa colors."""
    if not _is_string(value):
        return None
    m = re.fullmatch(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", value)
    if not m:
        return None
    digits = m.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    if len(digits) == 8:
        if int(digits[6:8], 16) < 255:
            return None  # translucent — the effective color depends on what is behind
        digits = digits[:6]
    return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def _relative_luminance(rgb: "tuple[float, float, float]") -> float:
    def channel(c: float) -> float:
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(fg: "tuple[float, float, float]", bg: "tuple[float, float, float]") -> float:
    l1, l2 = _relative_luminance(fg), _relative_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _lint_out_of_frame(report: Report, page: dict, path: str) -> None:
    layers = page["layers"]
    frames = {l["id"]: l for l in layers
              if _is_record(l) and l.get("type") == "frame" and _is_string(l.get("id"))}
    frame_boxes = {fid: _layer_aabb(f) for fid, f in frames.items()}
    for i, layer in enumerate(layers):
        if not _is_record(layer) or layer.get("type") == "frame" or not _lint_layer_visible(layer):
            continue
        box = _layer_aabb(layer)
        if box is None:
            continue
        parent = layer.get("parentId")
        if parent in frame_boxes and frame_boxes[parent] is not None:
            fbox = frame_boxes[parent]
            frame_area = (fbox[2] - fbox[0]) * (fbox[3] - fbox[1])
            coverage = _aabb_intersection_area(box, fbox) / frame_area if frame_area > 0 else 0.0
            if coverage >= _LINT_FULL_BLEED:
                continue  # full-bleed background
            overflow = max(fbox[0] - box[0], fbox[1] - box[1], box[2] - fbox[2], box[3] - fbox[3])
            if overflow > _LINT_BOUNDS_TOL:
                report.warn(
                    f"{path}.layers[{i}]", "LAYOUT_OUT_OF_FRAME",
                    f"{_lint_name(layer)} extends {overflow:.0f}px beyond its clipping frame "
                    f"'{frames[parent].get('name')}' — it will render cut off",
                    layer.get("type"),
                )
        elif parent is None and frame_boxes:
            if all(fb is None or _aabb_intersection_area(box, fb) == 0.0
                   for fb in frame_boxes.values()):
                report.warn(
                    f"{path}.layers[{i}]", "LAYOUT_ROOT_OUTSIDE_ARTBOARD",
                    f"{_lint_name(layer)} does not intersect any frame — it will be "
                    "outside every exported artboard",
                    layer.get("type"),
                )


def _lint_groups(page: dict) -> "dict[Any, list[tuple[int, dict, tuple[float, float, float, float]]]]":
    """Non-frame, visible, unrotated layers grouped by parentId, with their AABBs."""
    groups: dict[Any, list] = {}
    for i, layer in enumerate(page["layers"]):
        if not _is_record(layer) or layer.get("type") == "frame":
            continue
        if not _lint_layer_visible(layer):
            continue
        if float(layer.get("rotation") or 0) % 360.0 != 0:
            continue  # rotated elements are deliberate interventions — skip
        box = _layer_aabb(layer)
        if box is None:
            continue
        groups.setdefault(layer.get("parentId"), []).append((i, layer, box))
    return groups


def _lint_near_alignment(report: Report, page: dict, path: str) -> None:
    for members in _lint_groups(page).values():
        if len(members) < 3:
            continue  # too few siblings to infer an intended shared edge
        edge_kinds = {
            "x": [("left", lambda b: b[0]), ("centerX", lambda b: (b[0] + b[2]) / 2),
                  ("right", lambda b: b[2])],
            "y": [("top", lambda b: b[1]), ("centerY", lambda b: (b[1] + b[3]) / 2),
                  ("bottom", lambda b: b[3])],
        }
        for axis, kinds in edge_kinds.items():
            flagged: set = set()
            for kind, getter in kinds:
                values = sorted(((getter(box), i, layer) for i, layer, box in members),
                                key=lambda t: t[0])
                cluster: list = []
                for entry in values + [(math.inf, -1, {})]:  # sentinel flushes the last cluster
                    if cluster and entry[0] - cluster[-1][0] > _LINT_EDGE_TOL:
                        _flush_alignment_cluster(report, path, axis, kind, cluster, flagged)
                        cluster = []
                    cluster.append(entry)
                # (sentinel remains in `cluster`; it never forms a cluster of 2+ real edges)


def _flush_alignment_cluster(report: Report, path: str, axis: str, kind: str,
                             cluster: list, flagged: set) -> None:
    real = [c for c in cluster if c[1] >= 0]
    if len(real) < 3:
        return
    # Anchor = a coordinate genuinely shared by >= 2 layers; outliers sit 1..6px off it.
    rounded = Counter(round(v * 2) / 2 for v, _, _ in real)
    anchor, count = rounded.most_common(1)[0]
    if count < 2:
        return
    for value, idx, layer in real:
        offset = abs(value - anchor)
        if _LINT_EQ_EPS < offset <= _LINT_EDGE_TOL and idx not in flagged:
            flagged.add(idx)
            report.warn(
                f"{path}.layers[{idx}]", "LAYOUT_NEAR_ALIGNED",
                f"{_lint_name(layer)} {kind} edge is {offset:.1f}px off the {kind} line "
                f"shared by {count} sibling(s) at {anchor:g} — snap it if the alignment "
                "is intended",
                layer.get("type"),
            )


def _lint_vertical_rhythm(report: Report, page: dict, path: str) -> None:
    for members in _lint_groups(page).values():
        stack = sorted(members, key=lambda t: t[2][1])  # by top edge
        gaps: list = []
        for (i_a, la, a), (i_b, lb, b) in zip(stack, stack[1:]):
            h_overlap = min(a[2], b[2]) - max(a[0], b[0])
            min_width = min(a[2] - a[0], b[2] - b[0])
            gap = b[1] - a[3]
            if min_width <= 0 or h_overlap / min_width < 0.5 or not (0 < gap <= _LINT_GAP_CHAIN_BREAK):
                if len(gaps) >= 3:
                    _flush_rhythm(report, path, gaps)
                gaps = []
                continue
            gaps.append((gap, i_b, lb))
        if len(gaps) >= 3:
            _flush_rhythm(report, path, gaps)


def _flush_rhythm(report: Report, path: str, gaps: list) -> None:
    values = [g for g, _, _ in gaps]
    spread = max(values) - min(values)
    if _LINT_GAP_SPREAD_MIN < spread <= _LINT_GAP_SPREAD_MAX:
        median = sorted(values)[len(values) // 2]
        names = ", ".join(_lint_name(layer) for _, _, layer in gaps)
        report.warn(
            path + ".layers", "LAYOUT_IRREGULAR_SPACING",
            f"a vertical stack has almost-even gaps ({', '.join(f'{v:.0f}px' for v in values)}) "
            f"— equalize to {median:.0f}px if even rhythm is intended (stack: {names})",
        )


def _lint_text_overlap(report: Report, page: dict, path: str) -> None:
    for members in _lint_groups(page).values():
        texts = [(i, l, b) for i, l, b in members if l.get("type") == "text"]
        for a_pos in range(len(texts)):
            for b_pos in range(a_pos + 1, len(texts)):
                i_a, la, a = texts[a_pos]
                i_b, lb, b = texts[b_pos]
                # Shrink both estimated boxes 10% so borderline touches stay quiet.
                shrunk = []
                for box in (a, b):
                    dx = (box[2] - box[0]) * 0.05
                    dy = (box[3] - box[1]) * 0.05
                    shrunk.append((box[0] + dx, box[1] + dy, box[2] - dx, box[3] - dy))
                if _aabb_intersection_area(shrunk[0], shrunk[1]) > 0:
                    report.warn(
                        f"{path}.layers[{i_b}]", "LAYOUT_TEXT_OVERLAP",
                        f"{_lint_name(lb)} overlaps {_lint_name(la)} (text heights are "
                        "estimated) — verify they do not collide when rendered",
                        "text",
                    )


def _lint_text_contrast(report: Report, page: dict, path: str) -> None:
    layers = page["layers"]
    boxes = [(_layer_aabb(l) if _is_record(l) else None) for l in layers]
    for i, layer in enumerate(layers):
        if not _is_record(layer) or layer.get("type") != "text" or not _lint_layer_visible(layer):
            continue
        fg = _parse_hex_color(layer.get("fill"))
        box = boxes[i]
        if fg is None or box is None:
            continue
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        background = None
        for j in range(i - 1, -1, -1):  # walk down the z-order
            candidate = layers[j]
            if not _is_record(candidate) or not _lint_layer_visible(candidate):
                continue
            if candidate.get("type") not in ("frame", "rect", "ellipse"):
                continue
            if candidate.get("fillSpec") is not None:
                break  # gradient/image under the text: contrast is unknowable here
            cbox = boxes[j]
            if cbox is None or not (cbox[0] <= cx <= cbox[2] and cbox[1] <= cy <= cbox[3]):
                continue
            background = _parse_hex_color(candidate.get("fill"))
            break  # topmost solid layer under the text decides
        if background is None:
            continue
        ratio = _contrast_ratio(fg, background)
        if ratio < _LINT_MIN_CONTRAST:
            report.warn(
                f"{path}.layers[{i}]", "LAYOUT_LOW_CONTRAST",
                f"{_lint_name(layer)} has contrast {ratio:.2f}:1 against the solid layer "
                f"beneath it — likely unreadable (WCAG AA asks 4.5:1)",
                "text",
            )


def lint_layout(report: Report, document: dict) -> None:
    """Runs geometry-only layout checks. Requires a structurally valid document."""
    for p, page in enumerate(document.get("pages", [])):
        if not _is_record(page) or not isinstance(page.get("layers"), list):
            continue
        path = f"$.pages[{p}]"
        _lint_out_of_frame(report, page, path)
        _lint_near_alignment(report, page, path)
        _lint_vertical_rhythm(report, page, path)
        _lint_text_overlap(report, page, path)
        _lint_text_contrast(report, page, path)


# ---- page + document validation --------------------------------------------------

def _validate_page(report: Report, page: Any, path: str) -> None:
    if not _is_record(page):
        report.error(path, "PAGE_NOT_OBJECT", "object", page)
        return
    if not _is_string(page.get("id")):
        report.error(f"{path}.id", "REQUIRED_STRING", "string", page.get("id"))
    if not _is_string(page.get("name")):
        report.error(f"{path}.name", "REQUIRED_STRING", "string", page.get("name"))
    # parseEditorDocument: `durationSeconds !== undefined && !isFiniteNumber` rejects.
    # In JSON there is no `undefined` — an ABSENT key is OK, but a PRESENT key
    # (including an explicit null) must be a finite number. Do NOT exempt null.
    if "durationSeconds" in page:
        if not _is_finite_number(page.get("durationSeconds")):
            report.error(f"{path}.durationSeconds", "OPTIONAL_FINITE_NUMBER",
                         "finite number when present (absent is allowed; null is not)",
                         page.get("durationSeconds"))
    layers = page.get("layers")
    if not isinstance(layers, list):
        report.error(f"{path}.layers", "REQUIRED_ARRAY", "array", layers)
        return
    if len(layers) == 0:
        report.warn(f"{path}.layers", "PAGE_EMPTY", "page has no layers — renders blank")
    for i, layer in enumerate(layers):
        _validate_layer(report, layer, f"{path}.layers[{i}]")


def validate_design_document(document: Any, layout_lint: bool = True) -> Report:
    """Validates an EditorDocument against parseEditorDocument's exact contract,
    then (when structurally valid) runs the geometry-only layout lint."""
    report = Report()
    if not _is_record(document):
        report.error("$", "DOCUMENT_NOT_OBJECT", "object", document)
        return report
    if document.get("version") != DOCUMENT_VERSION:
        report.error("$.version", "VERSION_MISMATCH", f"exactly {DOCUMENT_VERSION}", document.get("version"))
    pages = document.get("pages")
    if not isinstance(pages, list):
        report.error("$.pages", "REQUIRED_ARRAY", "array", pages)
        return report
    if len(pages) == 0:
        report.warn("$.pages", "NO_PAGES", "document has no pages")
    for i, page in enumerate(pages):
        _validate_page(report, page, f"$.pages[{i}]")
    # Geometry math needs valid fields; lint only what will actually hydrate.
    if layout_lint and not report.errors:
        lint_layout(report, document)
    return report


# ---- envelope + upsert arguments (mirror designTypedPayload + MCP input) ----------

def build_typed_payload(document: Any, design_name: str, source_template_item_id: str | None,
                        cover_frame_id: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "kind": "design_document",
        "schema_version": 1,
        "editor_key": "konva",
        "design_name": design_name,
        "design_document": document,
    }
    if source_template_item_id:
        payload["source_template_item_id"] = source_template_item_id
    # Three-state cover: a frame id (string) or null (fit all) is persisted;
    # absent stays absent (AUTO = first frame).
    if cover_frame_id is not None or cover_frame_id is _COVER_FIT_ALL:
        payload["metadata"] = {
            "coverFrameId": None if cover_frame_id is _COVER_FIT_ALL else cover_frame_id
        }
    return payload


# Sentinel distinguishing "fit all" (explicit null) from "auto" (absent).
_COVER_FIT_ALL = object()


def build_upsert_arguments(document: Any, *, brand_id: str, design_name: str, title: str,
                           dimension_key: str, item_key: str | None,
                           brand_center_item_id: str | None,
                           source_template_item_id: str | None,
                           cover_frame_id: Any) -> dict[str, Any]:
    """The FLAT brand_center_item_upsert arguments — pass verbatim to the MCP tool.
    NOT wrapped in a `payload` object (that older convention is wrong)."""
    args: dict[str, Any] = {
        "brand_id": brand_id,
        "dimension_key": dimension_key,
        "title": title,
        "typed_payload": build_typed_payload(
            document, design_name, source_template_item_id, cover_frame_id
        ),
    }
    if brand_center_item_id:
        args["brand_center_item_id"] = brand_center_item_id  # update path
    elif item_key:
        args["item_key"] = item_key  # create path (auto-generated from title if omitted)
    return args


# ---- CLI -------------------------------------------------------------------------

def _read_document(raw_arg: str) -> Any:
    text = sys.stdin.read() if raw_arg == "-" else open(raw_arg, "r", encoding="utf-8").read()
    return json.loads(text)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate an Irrumpe Designer design_document and build its upsert arguments.",
    )
    parser.add_argument("--design-document", "--documento-diseno", dest="design_document",
                        help="path to the EditorDocument JSON, or - for stdin")
    parser.add_argument("--design-name", "--nombre-diseno", dest="design_name")
    parser.add_argument("--brand-id", "--id-marca", dest="brand_id")
    parser.add_argument("--title", "--titulo", dest="title")
    parser.add_argument("--dimension-key", dest="dimension_key", default="design",
                        choices=["design", "template"])
    parser.add_argument("--item-key", dest="item_key")
    parser.add_argument("--brand-center-item-id", dest="brand_center_item_id")
    parser.add_argument("--source-template-item-id", dest="source_template_item_id")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cover-frame-id", dest="cover_frame_id")
    group.add_argument("--cover-fit-all", dest="cover_fit_all", action="store_true")
    parser.add_argument("--strict-optional", action="store_true",
                        help="treat warnings as failures (exit 1)")
    parser.add_argument("--no-layout-lint", dest="layout_lint", action="store_false",
                        help="skip the geometry layout lint (LAYOUT_* warnings)")
    parser.add_argument("--self-test", action="store_true",
                        help="run the embedded golden fixtures and exit")
    args = parser.parse_args(argv)

    if args.self_test:
        return _run_self_test()

    if not args.design_document:
        parser.error("--design-document is required (path or - for stdin)")

    try:
        document = _read_document(args.design_document)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"valid": False, "io_error": str(exc)}, ensure_ascii=False))
        return 2

    report = validate_design_document(document, layout_lint=args.layout_lint)
    failed = bool(report.errors) or (args.strict_optional and bool(report.warnings))

    if failed and report.errors:
        print(json.dumps({
            "contract_version": CONTRACT_VERSION,
            "layout_lint_version": LAYOUT_LINT_VERSION if args.layout_lint else None,
            "valid": False,
            "errors": report.errors,
            "warnings": report.warnings,
        }, ensure_ascii=False, indent=2))
        return 1

    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
        "layout_lint_version": LAYOUT_LINT_VERSION if args.layout_lint else None,
        "valid": not failed,
        "warnings": report.warnings,
    }
    if failed:  # strict-optional with only warnings
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    # Build upsert arguments only when the design is valid AND enough identity is given.
    if args.brand_id and (args.title or args.design_name):
        cover = _COVER_FIT_ALL if args.cover_fit_all else args.cover_frame_id
        result["upsert_arguments"] = build_upsert_arguments(
            document,
            brand_id=args.brand_id,
            design_name=args.design_name or args.title,
            title=args.title or args.design_name,
            dimension_key=args.dimension_key,
            item_key=args.item_key,
            brand_center_item_id=args.brand_center_item_id,
            source_template_item_id=args.source_template_item_id,
            cover_frame_id=cover,
        )
    else:
        result["upsert_arguments_note"] = (
            "pass --brand-id and --title (or --design-name) to emit upsert_arguments"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# ---- self-test golden fixtures (mirror editor-fixtures.ts / editor-model.test.ts) -

def _base_layer(ltype: str, **extra: Any) -> dict[str, Any]:
    layer = {
        "id": "l1", "name": "Layer", "type": ltype, "x": 0, "y": 0,
        "rotation": 0, "opacity": 1, "visible": True, "locked": False, "parentId": None,
    }
    layer.update(extra)
    return layer


def _valid_document() -> dict[str, Any]:
    return {
        "version": 1,
        "pages": [{
            "id": "p1", "name": "Página 1", "layers": [
                _base_layer("frame", width=1080, height=1920, fill="#ffffff"),
                _base_layer("text", text="Hola", fontSize=48, fill="#0c1719", width=600,
                            fontFamily='"Brand Sans", sans-serif'),
                _base_layer("chart", chartKind="bar", width=400, height=300,
                            data=[{"label": "A", "value": 3}], palette=["#0c1719"],
                            showLabels=True, showValues=False, showGrid=True,
                            textFill="#0c1719", fontSize=12),
            ],
        }],
    }


def _run_self_test() -> int:
    cases: list[tuple[str, Any, bool]] = []

    cases.append(("valid document", _valid_document(), True))
    cases.append(("version 2 rejected", {**_valid_document(), "version": 2}, False))
    cases.append(("pages not array", {"version": 1, "pages": "x"}, False))
    # parseEditorDocument rejects a present-but-null durationSeconds (null !== undefined).
    cases.append(("page durationSeconds null rejected", {"version": 1, "pages": [
        {"id": "p", "name": "p", "durationSeconds": None, "layers": [
            _base_layer("rect", width=10, height=10, fill="#000")]}]}, False))
    cases.append(("page durationSeconds absent ok", {"version": 1, "pages": [
        {"id": "p", "name": "p", "layers": [
            _base_layer("rect", width=10, height=10, fill="#000")]}]}, True))
    cases.append(("layer missing type", {"version": 1, "pages": [
        {"id": "p", "name": "p", "layers": [{"id": "a", "name": "a", "x": 0, "y": 0,
         "rotation": 0, "opacity": 1, "visible": True, "locked": False, "parentId": None}]}]}, False))
    cases.append(("text missing fontSize", {"version": 1, "pages": [
        {"id": "p", "name": "p", "layers": [_base_layer("text", text="x", fill="#000", width=10)]}]}, False))
    cases.append(("shape without shapeId rejected", {"version": 1, "pages": [
        {"id": "p", "name": "p", "layers": [_base_layer("shape", fill="#000", width=10, height=10,
         pathData="M0 0 L10 10")]}]}, False))
    cases.append(("table ragged rows rejected", {"version": 1, "pages": [
        {"id": "p", "name": "p", "layers": [_base_layer("table", width=10, height=10,
         cells=[["a", "b"], ["c"]], headerRow=True, bandedRows=False, fontSize=12,
         textFill="#000", headerTextFill="#000", borderFill="#000", headerFill="#000",
         cellFill="#000", bandFill="#000")]}]}, False))
    cases.append(("chart empty data rejected", {"version": 1, "pages": [
        {"id": "p", "name": "p", "layers": [_base_layer("chart", chartKind="bar", width=10, height=10,
         data=[], palette=["#000"], showLabels=True, showValues=False, showGrid=True,
         textFill="#000", fontSize=12)]}]}, False))

    # Warn-only cases must stay VALID (parse succeeds) but raise a warning.
    media_doc = {"version": 1, "pages": [{"id": "p", "name": "p", "layers": [
        _base_layer("image", src="media://pending", width=10, height=10)]}]}
    cases.append(("media:// src valid-with-warning", media_doc, True))

    failures: list[str] = []
    for name, doc, expect_valid in cases:
        report = validate_design_document(doc)
        actual_valid = not report.errors
        if actual_valid != expect_valid:
            failures.append(f"{name}: expected valid={expect_valid}, got {actual_valid} "
                            f"(errors={report.errors})")

    # media:// must produce a SRC_PLACEHOLDER warning.
    media_report = validate_design_document(media_doc)
    if not any(w["code"] == "SRC_PLACEHOLDER" for w in media_report.warnings):
        failures.append("media:// src did not raise SRC_PLACEHOLDER warning")

    # ---- layout lint fixtures (all warnings-only: documents stay VALID) ----------

    def _lint_codes(doc: Any) -> "set[str]":
        rep = validate_design_document(doc)
        if rep.errors:
            failures.append(f"lint fixture unexpectedly invalid: {rep.errors}")
        return {w["code"] for w in rep.warnings}

    def _page(*layers: dict) -> dict[str, Any]:
        return {"version": 1, "pages": [{"id": "p1", "name": "p", "layers": list(layers)}]}

    frame = _base_layer("frame", id="f1", width=1080, height=1920, fill="#ffffff")

    # 1. Child poking out of its clipping frame warns; a full-bleed child stays quiet.
    poking = _base_layer("rect", id="r1", parentId="f1", x=1000, y=100,
                         width=300, height=100, fill="#000000")
    codes = _lint_codes(_page(frame, poking))
    if "LAYOUT_OUT_OF_FRAME" not in codes:
        failures.append("out-of-frame child did not raise LAYOUT_OUT_OF_FRAME")
    full_bleed = _base_layer("image", id="bg", parentId="f1", x=-20, y=-20,
                             src="https://cdn.example/bg.jpg", width=1120, height=1960)
    codes = _lint_codes(_page(frame, full_bleed))
    if "LAYOUT_OUT_OF_FRAME" in codes:
        failures.append("full-bleed background wrongly raised LAYOUT_OUT_OF_FRAME")

    # 2. A rotated overflowing badge is an intervention: bounds still checked, but a
    #    rotated layer must stay exempt from alignment checks (fixture 3 covers those).
    codes = _lint_codes(_page(frame, _base_layer(
        "rect", id="rot", parentId="f1", x=100, y=100, rotation=25,
        width=200, height=80, fill="#000000")))
    if "LAYOUT_NEAR_ALIGNED" in codes:
        failures.append("rotated layer wrongly entered alignment checks")

    # 3. Two rects sharing left=100 plus one at 103 → near-alignment warning.
    codes = _lint_codes(_page(
        frame,
        _base_layer("rect", id="a", parentId="f1", x=100, y=100, width=200, height=50, fill="#111111"),
        _base_layer("rect", id="b", parentId="f1", x=100, y=300, width=200, height=50, fill="#111111"),
        _base_layer("rect", id="c", parentId="f1", x=103, y=500, width=200, height=50, fill="#111111"),
    ))
    if "LAYOUT_NEAR_ALIGNED" not in codes:
        failures.append("3px-off sibling did not raise LAYOUT_NEAR_ALIGNED")

    # 4. Almost-even vertical gaps (60, 63, 58) → rhythm warning.
    stack = [_base_layer("rect", id=f"s{i}", parentId="f1", x=100, y=y,
                         width=400, height=40, fill="#222222")
             for i, y in enumerate([100, 200, 303, 401])]  # gaps: 60, 63, 58
    codes = _lint_codes(_page(frame, *stack))
    if "LAYOUT_IRREGULAR_SPACING" not in codes:
        failures.append("almost-even gaps did not raise LAYOUT_IRREGULAR_SPACING")

    # 5. Two overlapping text boxes → overlap warning.
    codes = _lint_codes(_page(
        frame,
        _base_layer("text", id="t1", parentId="f1", x=100, y=100, text="Titular grande",
                    fontSize=60, fill="#111111", width=500, fontFamily='"B", sans-serif'),
        _base_layer("text", id="t2", parentId="f1", x=120, y=120, text="Subtítulo",
                    fontSize=40, fill="#111111", width=500, fontFamily='"B", sans-serif'),
    ))
    if "LAYOUT_TEXT_OVERLAP" not in codes:
        failures.append("overlapping texts did not raise LAYOUT_TEXT_OVERLAP")

    # 6. Near-white text on a white frame → contrast warning.
    codes = _lint_codes(_page(
        frame,
        _base_layer("text", id="t3", parentId="f1", x=100, y=100, text="Invisible",
                    fontSize=40, fill="#f4f4f4", width=400, fontFamily='"B", sans-serif'),
    ))
    if "LAYOUT_LOW_CONTRAST" not in codes:
        failures.append("white-on-white text did not raise LAYOUT_LOW_CONTRAST")

    # 7. The canonical valid document must produce ZERO layout warnings (noise guard),
    #    and --no-layout-lint must silence LAYOUT_* codes entirely.
    clean_report = validate_design_document(_valid_document())
    noisy = [w for w in clean_report.warnings if w["code"].startswith("LAYOUT_")]
    if noisy:
        failures.append(f"clean document raised layout noise: {noisy}")
    unlinted = validate_design_document(_page(frame, poking), layout_lint=False)
    if any(w["code"].startswith("LAYOUT_") for w in unlinted.warnings):
        failures.append("layout_lint=False still produced LAYOUT_* warnings")

    # Layer-type coverage: every known type must have a branch (guards drift).
    covered = LAYER_TYPES
    if covered != {"frame", "rect", "ellipse", "text", "image", "video",
                   "lottie", "icon", "shape", "table", "chart"}:
        failures.append("LAYER_TYPES drifted from the 11-type contract")

    if failures:
        print(json.dumps({"self_test": "FAIL", "failures": failures}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"self_test": "PASS", "cases": len(cases),
                      "contract_version": CONTRACT_VERSION}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
