# MCP (Model Context Protocol)

> ⚠️ All company documents used here are fictional sample data written
> for this exercise — not any real employer's actual policies.

| Stage | What it does | Status |
|---|---|---|
| [`01-policy-search-server`](./01-policy-search-server) | A minimal MCP server exposing `search_policy`, a client that discovers and invokes it, and the existing policy agent reconnected through the protocol boundary instead of a direct function call | ✅ Working |

## Why this folder exists separately from `multi-agent/`

`multi-agent/01-supervisor-agents` is about splitting reasoning across
specialist agents *within one codebase*. This folder is about a
different boundary: how an agent talks to a capability that could live
*anywhere* — a different process, a different machine, a different
team's system entirely — through one consistent protocol instead of a
custom integration per tool.

See `01-policy-search-server/README.md` for the Security Design section
and the EM Architecture exercise — the real lesson of this topic is less
about the protocol mechanics and more about what breaks when you scale
this pattern to five real external systems and 500 engineers.
