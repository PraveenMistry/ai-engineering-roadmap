# A2A (Agent-to-Agent Communication)

> ⚠️ This is a simulated negotiation exercise. No real transactions,
> prices, or parties are involved.

| Stage | What it does | Status |
|---|---|---|
| [`01-negotiation-simulator`](./01-negotiation-simulator) | Two agents with opposing, hard-enforced constraints negotiate through a shared message contract, coordinated and reviewed by two more agents | ✅ Working |

## Why this folder exists separately from `mcp/`

`mcp/01-policy-search-server` is about an agent calling a **tool** —
one-directional, tool has no agency of its own. This folder is about
two **peer agents**, each with their own private goals and constraints,
communicating as equals through a shared protocol. That's a genuinely
different coordination problem — see
`01-negotiation-simulator/README.md`'s EM Architecture Challenge for
what changes when this pattern scales to 10 real agents across
multiple owning teams.
