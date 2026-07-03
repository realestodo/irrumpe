# Irrumpe OS

Public operator plugin for the [Irrumpe](https://irrumpe.realestodo.com) platform, for **Claude
Code** and **OpenAI Codex**. It ships one skill and one command, both wired to the Irrumpe remote
MCP (`https://mcp.realestodo.com/mcp`, OAuth with your Irrumpe account):

- **`irrumpe-operator`** — operates the platform through the MCP: edit content and documents,
  approve or reject work (status transitions), create and edit Konva designs, upload and query
  Brand Center assets, read Pulso performance metrics, operate Google Ads campaigns (typed writes
  with explicit dry-run), send briefs, create projects, and manage tasks and document statuses. It
  performs zero creative work: it knows the tool contracts, where each piece of data lives, and the
  guardrails that protect every write.
- **`/onboarding`** — conversational brand onboarding: the 6-stage Mapa Irrumpe questionnaire with
  help subquestions, required-answer and length gates, the 45-statement emotion matrix, and
  submission for human review. It respects platform permissions (brand slots, linked brands) and
  verifies the MCP connection before starting, repairing the wiring when the environment allows it.

> This repository is a published artifact. Source of truth lives in the private Irrumpe repository;
> changes arrive through its publish pipeline.

## Install — Claude Code

```
/plugin marketplace add realestodo/irrumpe
/plugin install irrumpe-os@irrumpe-os
```

The plugin registers the Irrumpe MCP automatically (`.mcp.json`). Authenticate with `/mcp` → select
`irrumpe` → OAuth with your Irrumpe account. Then run `/onboarding` or just ask for platform
operations in natural language.

## Install — Codex

```
codex plugin marketplace add realestodo/irrumpe
codex plugin install irrumpe-os
codex mcp login irrumpe
```

Codex plugins load skills and MCP wiring (`.codex-mcp.json`); slash commands are a Claude Code
surface. On Codex, trigger the onboarding by prompt — for example: *"Haz el onboarding de mi marca
en Irrumpe"*. The skill routes the full flow.

## What the operator enforces

- Write access resolved from capability flags (`can_edit`, `can_manage_*`), never from role labels.
  Denied writes are reported with the missing permission; a write that succeeds when flags said it
  should fail is reported as a possible platform permission fault.
- Design documents validate through `tools/validar_design_document.py` before every upsert; the
  upsert uses the returned arguments verbatim.
- Ads changes preview with `dry_run: true` and apply only with your confirmation; `pre_revision` is
  a valid outcome pending human review.
- Media travels by staged upload to R2 or server-side URL import; never as base64 through the model.
- Onboarding submission requires your explicit confirmation, and personality assignment stays with
  the human review team.

## Requirements

- An Irrumpe account (the MCP authenticates via OAuth).
- Python 3 available on the host for the design validator.

## License

MIT — see [LICENSE](./LICENSE).
