# Irrumpe OS

Public skill pack from **Irrumpe**, installable on both **Claude Code** and **OpenAI Codex**, wired to the Irrumpe MCP for real collaboration on brand data.

> This repository is a compiled, published artifact. Source of truth and maintenance live in the private Irrumpe repository. All data access goes through the Irrumpe MCP — these skills never touch any internal data source directly.

## Main skills

| Skill | Purpose |
| --- | --- |
| `creative-copywriter` | Expert creative copywriting with a genuinely human voice. |
| `content-creation` | Build publishable social-media content briefs in short execution windows. |
| `brand-strategy-creation` | Full reasoning for brand strategy. |
| `conceptualization-creation` | Brand conceptualization: opportunity canvas, creative rationale, core concepts, manifesto. |
| `planning-creation` | Annual social planning, closing with a publish-ready Irrumpe MCP payload. |
| `diseno-irrumpe` | Create, edit and recreate Konva designs in the Irrumpe editor via MCP; validates the design document before upsert. |

### Supporting skills and subagents

The main skills load these bundled reference skills as needed:
`irrumpe-native-surfaces-creative`, `irrumpe-native-surfaces-social`,
`content-creation-guide`, `strategy-framework`, `strategy-types`,
`manifesto-crafting`, `planning-framework`.

Two subagents support `conceptualization-creation`:
`investigador-conceptual` (research) and `publicador-conceptual` (persistence).

`diseno-irrumpe` ships a bundled validator at `tools/validar_design_document.py`
that it runs before every design upsert.

> **Codex note:** the two subagents ship in both formats. Claude Code loads
> `agents/*.md` automatically. For Codex, install the TOML twins from
> `codex-agents/` (see the Codex install section); the plugin manifest does not
> distribute subagents on its own.

## Data access

All skills resolve brand data through the **Irrumpe MCP** at
`https://mcp.realestodo.com/mcp`. Using it requires authenticating with an
Irrumpe account (OAuth). The skills carry no internal IDs or data-source maps.

## Install — Claude Code

```
/plugin marketplace add realestodo/irrumpe
/plugin install irrumpe-os@irrumpe-os
```

Then connect the MCP server and complete the OAuth flow:

```
/mcp
```

## Install — OpenAI Codex

```
codex plugin marketplace add realestodo/irrumpe
```

Install `irrumpe-os` from the plugin directory, then authenticate the MCP server:

```
codex mcp login irrumpe
```

If the bundled remote MCP server is not picked up automatically, add it to
`~/.codex/config.toml`:

```toml
[mcp_servers.irrumpe]
url = "https://mcp.realestodo.com/mcp"
```

### Codex subagents (optional)

The two conceptualization subagents are provided as Codex custom agents under
`codex-agents/`. Codex does not load subagents from a plugin, so copy the TOML
files into your agents directory:

```
mkdir -p .codex/agents
cp codex-agents/*.toml .codex/agents/      # project-scoped
# or: cp codex-agents/*.toml ~/.codex/agents/   # personal
```

## MCP

| Client | Transport config | Auth |
| --- | --- | --- |
| Claude Code | `.mcp.json` → `type: "http"`, `url` | `/mcp` connect + OAuth |
| Codex | `.codex-mcp.json` → `url` | `codex mcp login irrumpe` |
