# Day 12 — Multi-Agent Negotiation Simulator (A2A in Miniature)

## What this actually demonstrates

Two agents (Buyer, Seller) with **opposing, private constraints**,
talking through a Coordinator using a fixed message contract, reviewed
afterward by a third agent with no stake in the outcome. This is a
small, concrete version of the A2A (agent-to-agent) pattern — agents
communicating as peers, not just an agent calling a tool (that was
Day 11's MCP pattern).

```
Buyer  ↕  Coordinator  ↕  Seller
                ↓
            Reviewer
```

## Exercise 1 — The message contract

`protocol/messages.py` defines the one shape every message follows —
`message_id`, `conversation_id`, `sender`, `receiver`, `type`,
`payload`. Neither Buyer nor Seller needs to know how the other agent
reasons internally — only that messages arriving in this shape are
valid. This is the same decoupling idea as MCP's tool schema (Day 11),
applied between two agents instead of an agent and a tool.

## Exercises 2 & 3 — The enforcement pattern, on both sides

Both `agents/buyer.py` (`max_budget = 950`) and `agents/seller.py`
(`minimum_price = 900`) follow the identical structure:

```
LLM proposes a price
      ↓
Code clamps it to the hard constraint
      ↓
Reasoning gets annotated if clamping actually happened
```

This is the same non-negotiable principle from every previous day:
**the LLM reasons, the code enforces.** The buyer's system prompt tells
the model its budget, but that's just context for generating a
*sensible* offer — the actual guarantee that it never exceeds budget is
`min(proposed_price, self.max_budget)`, a line of code the model cannot
argue its way around no matter how the conversation goes.

Test each in isolation first:
```bash
python -c "from agents.buyer import BuyerAgent; b = BuyerAgent(950); print(b.propose(None, 1))"
python -c "from agents.seller import SellerAgent; s = SellerAgent(900); print(s.propose(None, 1))"
```

## Exercise 4 — Coordinator

```bash
python coordinator.py
```

Every message gets logged with `timestamp`, `message_id`,
`conversation_id`, `sender`, `receiver`, `message_type`, `payload`,
`latency`, and `status` — written to `logs/<conversation_id>.json`
after each run. Same observability philosophy as every previous day's
agent: if a negotiation later looks wrong, you should be able to
reconstruct exactly what was said, in what order, by whom, without
relying on either agent's own account of events.

## Exercise 5 — Reviewer

`agents/reviewer.py` runs AFTER the negotiation completes, not during
it — deliberately kept separate so the audit doesn't depend on the
coordinator's own real-time logic being correct. It checks:

- Was the final price actually within both constraints? (should always
  be "no violation" if enforcement worked — checking anyway is the point)
- How many rounds did it take?
- **Did the enforcement layer actually have to clamp anything?**
  (`clamped_offers` in the review output) — this is genuinely useful
  signal: frequent clamping means the LLM's negotiation strategy is
  poorly calibrated to the real constraints, even though the outcome
  was still safe.

## Exercise 6 — Failure simulation and the decision

Run the built-in demo, which shows the seller failing on round 2's
first attempt and recovering on retry:
```bash
python coordinator.py
```

To see the **permanent failure** path (retries exhausted, negotiation
terminates), force the seller to always fail using a mock — same
pattern as Day 8's test suite:
```python
from unittest.mock import patch
from coordinator import run_negotiation

with patch("agents.seller.SellerAgent.propose", side_effect=TimeoutError("permanently down")):
    result = run_negotiation()
    print(result["status"])  # "terminated_seller_unavailable"
```

### The decision: bounded retry (2 attempts), then terminate

- **Why retry at all** — a single simulated/real timeout could genuinely
  be transient (a slow model response, a momentary resource issue).
  One retry costs little and often just works.
- **Why bounded at 2, not unlimited** — same principle as every
  previous day's retry logic: an unbounded retry loop is not a safety
  net, it's a hidden infinite loop waiting for the right failure mode
  to trigger it. The limit is enforced in code (`MAX_RETRIES_ON_FAILURE`),
  never left to the model or to "it'll probably work eventually."
- **Why terminate, not fall back to a default price** — this is the
  one worth thinking hardest about. It might seem "nicer" to just let
  the buyer's offer auto-win if the seller can't respond. That's wrong:
  silently completing a negotiation the seller never actually agreed to
  is worse than admitting the negotiation failed. A terminated
  negotiation is honest. A negotiation that fabricates the seller's
  consent is not — same "confident wrongness is worse than honest
  failure" principle from Day 7's abstain logic, just applied to a
  two-party protocol instead of a single agent's answer.
- **Why not human approval here** — reserve that for genuinely
  high-stakes actions (Day 10's reasoning still applies: what's the
  cost if this is wrong?). A toy negotiation timing out and needing to
  be retried by the user is low-stakes enough that human-in-the-loop
  would be overkill, unlike, say, an agent about to execute a real
  financial transaction.

---

## 🧠 EM-Level Architecture Challenge

Answering these for the "Engineering Manager AI platform" scenario
(Supervisor → Research/SQL/Architecture agents via A2A → Reviewer):

**1. Who owns each agent?**
Each specialist agent should have a clear owning team — likely the team
whose domain it represents (a data platform team owns the SQL Agent, a
docs/knowledge team owns the Research Agent). The Supervisor and
Reviewer, being cross-cutting, need a dedicated platform/AI-infra team
owning them — nobody's specialist team should also own the shared
orchestration layer, or incentives get misaligned around whose agent's
reliability the on-call rotation actually protects.

**2. Who defines the communication contract?**
Neither individual agent team unilaterally — the message
schema/protocol needs to be owned centrally (the same platform team
from Q1) and versioned like any internal API. If the SQL Agent's team
can silently change the shape of what they send, every other agent
depending on their output breaks without warning.

**3. What happens if an agent is unavailable?**
Depends entirely on whether that agent's contribution is required or
optional for a given request. Exactly today's Exercise 6 logic, scaled
up: bounded retry, then either (a) terminate the whole request honestly
if that agent's input was essential, or (b) proceed with a partial
result and clearly flag what's missing — the same partial-vs-abort
decision from Day 10, now made per-agent rather than per-audience.

**4. How do you authenticate agents?**
Each agent needs its own service identity — not a shared credential
across all of them — issued by whatever internal identity system the
company already uses (mTLS certs or short-lived OAuth tokens are the
standard options). An agent's identity should be verifiable by every
other agent it talks to, not just by the Supervisor.

**5. How do you authorize delegation?**
Authentication proves which agent is calling; authorization decides
what it's allowed to *delegate*. The Research Agent asking the SQL
Agent to run a query needs to be checked against an explicit allow-list
— "Research Agent may request read-only SQL queries" — not implicitly
trusted just because both agents are part of the same platform. This
mirrors Day 11's MCP authorization question, just between two agents
instead of an agent and a tool.

**6. How do you prevent an agent from calling another agent indefinitely?**
A hard hop limit, enforced centrally — e.g., "no single user request
may generate more than N agent-to-agent hops" — tracked via the
`conversation_id`/`request_id` threading through every message (Q7).
Same non-negotiable principle as every retry loop in this entire
program: the limit lives in code the agents can't argue past, not in a
prompt asking them to "please stop eventually."

**7. How do you trace one user request across 10 agents?**
A single `request_id` (or trace ID) generated at the very first entry
point and passed through EVERY message, EVERY agent-to-agent call,
logged at each hop — exactly the `conversation_id` pattern in today's
`messages.py`, just needing to survive across many more hops and
multiple agents' independent logs. Without this, debugging a bad
outcome three agents deep is close to impossible.

**8. When should communication be synchronous?**
When the calling agent genuinely cannot proceed without the answer —
the Supervisor waiting on the SQL Agent's query result before it can
hand off to the Architecture Agent, for example. Synchronous calls are
simpler to reason about but block the caller for the callee's entire
response time.

**9. When should it be asynchronous?**
When multiple independent things can happen at once, or when a
response isn't needed immediately — this is Day 10's parallel
execution lesson again, now at the multi-agent-system level. If
Research and SQL agents don't depend on each other's output, running
them synchronously one after another wastes real wall-clock time for
no correctness benefit.

**10. How do you version agent contracts?**
The same discipline as any internal API: explicit version numbers on
the message schema, backward-compatible changes preferred over
breaking ones, and a real deprecation window before an old contract
version stops being served — never a silent "we changed the shape,
hope nothing downstream broke." An agent receiving a message version it
doesn't recognize should fail loudly and specifically, not attempt to
guess a mapping.

**The actual lesson, again:** none of these questions show up if you
only look at the architecture diagram. They show up the moment 10
agents, multiple owning teams, and real production traffic hit a clean
box-and-arrow picture. The diagram is 10% of the work.

## Setup

```bash
pip install langchain langchain-ollama
ollama pull llama3.2
```

## Files

```
day-12/
├── README.md
├── coordinator.py          Exercises 4 & 6 — routing, logging, failure handling
├── agents/
│   ├── buyer.py             Exercise 2 — LLM proposes, code enforces max_budget
│   ├── seller.py            Exercise 3 — LLM proposes, code enforces minimum_price
│   └── reviewer.py          Exercise 5 — post-negotiation audit
├── protocol/
│   └── messages.py          Exercise 1 — the shared message contract
└── logs/                    populated by coordinator.py at runtime
```
