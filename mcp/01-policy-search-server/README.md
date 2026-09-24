# Day 11 — MCP Server (Model Context Protocol)

> ⚠️ All company documents used here are fictional sample data written
> for this exercise — not any real employer's actual policies.

## What MCP actually is, in one sentence

MCP standardizes how an agent talks to a tool or data source, so the
agent doesn't need custom integration code for every single system it
touches — it discovers what's available and calls it through one
consistent protocol.

```
Agent
 ↓
MCP Client
 ↓
MCP Server
 ↓
search_policy()
 ↓
Policy documents
```

## Why we're not starting with Jira or GitHub

Those integrations add two kinds of complexity at once: MCP's protocol
mechanics AND a real external system's auth/rate-limits/schema quirks.
Building a server around three markdown files you completely control
means any bug you hit today is genuinely about MCP, not about
"why is Jira's API behaving strangely." Same instinct as every previous
day: isolate the new concept before combining it with something else.

## Exercise 1 — The MCP Server

`mcp_server.py` exposes exactly one tool, `search_policy(query)`, using
plain keyword matching — no LLM, no embeddings. Test it in isolation
first (the server can run standalone and just sits waiting for a
client to connect):

```bash
pip install mcp
python mcp_server.py
```

It'll appear to hang — that's correct. It's waiting on stdio for a
client. Ctrl+C to stop it; you won't normally run it this way, `mcp_client.py`
starts it as a subprocess automatically.

## Exercise 2 — The MCP Client and Capability Discovery

```bash
python mcp_client.py "remote work"
```

Watch the output closely: the client prints `Discovered tools: [...]`
**before** it ever calls `search_policy`. It doesn't hardcode "I know
this server has a search_policy function" — it asks the server what's
available, confirms the tool it wants exists, and only then invokes it
by name.

**Why this matters beyond today's toy example:** in the Architecture
Exercise below, a real company might have five different MCP servers
(Jira, GitHub, Slack, database, deployment). An agent — or more
realistically, a *supervisor* choosing which specialist agent handles a
request — doesn't need custom integration code baked in for each one.
It queries what's available and adapts. That's the actual value
proposition of the protocol, not just today's demo.

## Exercise 3 — Connecting the Agent Through the Protocol Boundary

```bash
python agent_via_mcp.py
```

Compare this file to Day 10's (multi-agent) `research_agent.py` + `policy_agent.py`.
The interpretation logic (the LLM call) is identical — only retrieval
changed, from a direct Python function call to a call mediated by the
MCP client/server round-trip.

**The point worth sitting with:** because the agent only knows the
tool's *name* and its *input/output shape* — not its internals — the
server's `search_policy` implementation could be swapped from today's
naive keyword search to Day 10's (multi-agent) real embeddings-based search, or moved
to a completely different machine, and `agent_via_mcp.py` would not
need a single line changed. That decoupling is the actual reason MCP
exists — not just "a nicer way to call functions."

## Exercise 4 — Security Design

**1. Who can call the MCP server?**
Today's server has zero access control — anything that can spawn the
subprocess can call it. In a real deployment, this needs to change
immediately: only specific, identified clients (specific agents/
services, not "anyone on the network") should be able to connect at all.

**2. How would authentication work?**
Each client (agent or service) should present a credential — an API
key or short-lived token — at connection time, not per-tool-call. For
internal systems, this is typically a service identity issued by
whatever your company already uses for service-to-service auth (mTLS
certs, OAuth client credentials, or an internal secrets-managed token),
not a shared static password.

**3. How would you authorize different agents?**
Authentication proves *who* is calling; authorization decides *what
they're allowed to do*. A Research Agent and a database-writing Agent
should not have the same permissions just because they both
"authenticated successfully." This needs a permission model tied to
agent identity — e.g., "Research Agent role can call `search_policy`
and `search_jira_issues` (read-only), but not `create_ticket` or
`deploy_service`."

**4. Which tools should Research Agent have?**
Read-only, low-blast-radius tools only: `search_policy`,
`search_documentation`, maybe `search_jira_issues` (read). No write
access, no execution capability, nothing that changes state anywhere.
If Research Agent is compromised or hallucinates a bad tool call, worst
case is a wasted search, not a wasted deployment.

**5. Which tools should SQL Agent have?**
This is the one requiring the most care. At minimum: read-only database
access, scoped to specific tables/views it actually needs (not
`SELECT *` on the whole schema), through a role that cannot `DROP`,
`DELETE`, `UPDATE`, or touch tables outside its scope. If it ever needs
write access, that's a fundamentally different trust level requiring
its own review — not something to grant by default "in case it's useful."

**6. Which tools require human approval?**
Anything with real-world, hard-to-reverse consequences: production
deployments, database writes/deletes, sending external communications
(emails, Slack messages to customers), approving financial transactions,
revoking access/credentials. The test I'd apply: *"if this tool call
was wrong, how expensive is undoing it?"* Cheap-to-undo → agent can act
autonomously. Expensive or irreversible → human approval gate, no
exceptions for convenience.

**7. What should be logged?**
Every tool call, regardless of success/failure: which agent/client
called it, what arguments were passed, what was returned (or the error),
a timestamp, and a request ID that ties it back to the original user
request that triggered it. This is the same principle as Day 7's
structured logging, just applied at the protocol boundary instead of
inside one agent — without this, a bad outcome three tool calls deep is
nearly impossible to trace back to its actual cause.

## EM Architecture Exercise

**Scenario:** 500 developers, 20 teams, Jira + GitHub + Slack +
PostgreSQL + an internal deployment platform, and the company wants one
Engineering AI Assistant sitting in front of all of it via MCP.

```
                     AI Assistant
                          ↓
                     MCP Client
                          ↓
   ┌──────────────┬───────┼────────┬──────────────┐
   ↓              ↓       ↓        ↓              ↓
 Jira           GitHub   Slack      DB        Deployment
  MCP             MCP     MCP      MCP            MCP
```

**What can go wrong, mapped to the specific risks called out:**

- **Excessive tool access** — if every request routes through one
  generic AI Assistant with access to all five MCP servers, a prompt
  injection hidden in, say, a Jira ticket description could trick the
  assistant into calling the Deployment MCP server, because nothing
  architecturally stops it. The fix isn't a smarter prompt — it's not
  giving the assistant blanket access to all five servers in the first
  place. Route through specialist agents (Research, SQL, Deploy) each
  scoped to only the servers their job requires, the same pattern from
  Day 10, now applied at the protocol/infrastructure level.

- **Credential management** — five external systems means five sets of
  credentials the MCP layer now holds. A single leaked credential (or a
  single overly-broad service account) becomes a single point of
  failure across every team using the assistant. Credentials need to be
  scoped as narrowly as each server's actual need, rotated regularly,
  and never shared across MCP servers "for simplicity."

- **Authorization** — a junior developer's request and a team lead's
  request going through the same assistant shouldn't have the same
  effective permissions on GitHub or the deployment platform just
  because both are "authenticated." Authorization needs to reflect the
  *actual human's* permissions, not just "the assistant is allowed to
  use this tool at all."

- **Malicious/incorrect tool arguments** — an LLM can construct a
  syntactically valid but semantically wrong or dangerous argument (a
  SQL Agent asked to "find inactive users" might construct a query that
  accidentally matches far more rows than intended). Every MCP server
  needs its own input validation — never trust that the LLM's arguments
  are safe just because they parsed correctly as JSON.

- **Sensitive data exposure** — a database MCP server returning raw
  query results into an LLM's context risks that sensitive data (PII,
  salaries, security details) ending up quoted back in a Slack message
  to someone who shouldn't see it. Tools that touch sensitive data need
  output filtering, not just input authorization.

- **Auditability** — with five servers and potentially dozens of agents
  calling them, a bad outcome needs to be traceable: which team's
  request, which agent, which tool, which arguments, at what time. This
  needs to be centralized logging across all five MCP servers, not five
  separate logs nobody correlates.

- **Tool failures** — the Deployment MCP server being briefly down
  shouldn't take down Jira/GitHub/Slack functionality too. Each server
  needs to fail independently and gracefully (same principle as Day
  10's failure-handling exercise, just at larger scale) — a timeout
  talking to one system is not a reason to abstain on a completely
  unrelated request.

- **Latency** — chaining multiple MCP calls (search Jira, then GitHub,
  then Slack) sequentially for one request could make a simple question
  take 10+ seconds. This is exactly Day 10's parallel-execution lesson,
  now relevant at the infrastructure level: independent lookups across
  different servers should run concurrently, not one after another.

- **Rate limits** — GitHub and Jira both have API rate limits. 500
  developers hitting one shared AI Assistant could burn through a
  shared rate limit budget fast, breaking the assistant for everyone
  the moment one team runs a batch of automated queries. Needs
  per-team or per-use-case rate limiting, not one global budget.

- **Version compatibility** — five MCP servers maintained by
  potentially five different teams (or vendors) means version drift is
  inevitable. A tool's input schema changing on the GitHub MCP server
  without warning could silently break every agent that calls it. This
  needs the same discipline as any internal API: versioned schemas, and
  a deprecation process — not "we updated it, hope nothing broke."

- **Operational ownership** — when the Deployment MCP server goes down
  at 2 AM, whose pager goes off? With five servers spanning
  infrastructure, security, and multiple product teams, ownership needs
  to be explicit per server *before* the incident, not figured out
  during it.

**The actual lesson from this exercise:** the diagram above looks clean
and simple. Every one of these problems is invisible in the diagram and
only shows up once real usage, real scale, and real failure modes hit
it. Drawing the architecture is the easy 10% of this problem — the
governance, security, and operational questions are the other 90%, and
they're exactly what separates a toy demo from something 500 engineers
can actually depend on.

## Setup

```bash
pip install mcp langchain langchain-ollama
ollama pull llama3.2
```

## Files

```
day-11/
├── README.md
├── mcp_server.py       Exercise 1 — exposes search_policy
├── mcp_client.py        Exercise 2 — discovery + invocation
├── agent_via_mcp.py     Exercise 3 — agent through the protocol boundary
└── data/
    ├── leave-policy.md
    ├── remote-work.md
    └── contractor-policy.md
```
