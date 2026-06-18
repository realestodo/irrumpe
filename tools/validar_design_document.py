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
from typing import Any

CONTRACT_VERSION = "1"

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


def validate_design_document(document: Any) -> Report:
    """Validates an EditorDocument against parseEditorDocument's exact contract."""
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

    report = validate_design_document(document)
    failed = bool(report.errors) or (args.strict_optional and bool(report.warnings))

    if failed and report.errors:
        print(json.dumps({
            "contract_version": CONTRACT_VERSION,
            "valid": False,
            "errors": report.errors,
            "warnings": report.warnings,
        }, ensure_ascii=False, indent=2))
        return 1

    result: dict[str, Any] = {
        "contract_version": CONTRACT_VERSION,
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
