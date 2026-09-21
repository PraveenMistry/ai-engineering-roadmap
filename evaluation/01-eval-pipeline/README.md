# Day 13 — Evaluation + Observability

> ⚠️ All company documents are fictional sample data for this exercise.

## A consistency note before anything else

Exercise 6, as written, proposes *"What is our maternity leave
policy?"* as the case that should **abstain**. We already proved this
wrong in Day 7/8: this exact question isn't a clean unanswerable case —
our knowledge base genuinely has a parental leave policy that answers
it, our agent correctly found it and answered with an honest caveat,
and we deliberately rewrote our Day 8 test suite to stop treating this
as a hallucination.

So in `dataset.json`, maternity leave is kept (q020) but graded as
`answer_with_caveat`, not `abstain` — and Exercise 6's actual
before/after regression demo uses **travel reimbursement** instead
(q011), which has zero real overlap with anything in the knowledge
base and is a genuinely clean true-negative. This is itself a small,
real example of the evaluation discipline this whole day is about:
before trusting a test's expected answer, check whether the expected
answer is actually correct.

## Exercise 1 — The dataset

`dataset.json` — 20 questions:

| Category | Count | What it tests |
|---|---|---|
| normal | 5 | Clean, single-document lookups |
| multi-step | 5 | Require combining contractor-policy.md with another document |
| unanswerable | 4 | Zero overlap with the knowledge base — must abstain |
| ambiguous | 3 | Under-specified, no conversation memory exists to resolve them — graded qualitatively |
| adversarial | 3 | Prompt injection, false-authority claims, and the maternity/parental nuance |

## Exercise 2 — Run it

```bash
python ingest.py          # build vector_store.json for this folder
python evaluate.py before # runs all 20, saves results/before_<timestamp>.json
```

Each result captures exactly the schema asked for: `question_id`,
`answer`, `sources`, `status`, `latency_ms`, `input_tokens`,
`output_tokens`, `tool_calls`. Token counts come from
`response.usage_metadata` on each LangChain/Ollama call — check your
`langchain-ollama` version actually populates this; older versions may
return zeros, which is itself worth noticing rather than silently
trusting the number.

## Exercise 3 — Basic metrics

```bash
python metrics.py results/before_<timestamp>.json
```

Computes, deliberately simply:
- **Answer correctness** — substring match of `expected_answer` in the
  generated answer. Crude, but establishes the pipeline; Exercise 4's
  judge is the upgrade path.
- **Abstention accuracy** — for `expected_behavior: "abstain"`
  questions, checks `status == "abstained"` directly from the agent's
  own structured output, not text-sniffing the answer.
- **Retrieval success** — did `expected_source` appear in `sources`?
- **Latency** — average, p50, p95 across all 20 runs.
- **Injection resistance** — for adversarial questions, did the
  `forbidden_answer` (e.g. "100" days, "unlimited" leave) leak into the
  generated answer at all? This is a direct, mechanical check — no
  judge needed to catch an obviously fabricated number appearing verbatim.

## Exercise 4 — LLM Judge

```python
from metrics import run_judge_on_results, load_json
results = load_json("results/before_<timestamp>.json")
dataset = load_json("dataset.json")
judged = run_judge_on_results(results, dataset)
```

Scores `relevance`, `groundedness`, and `completeness` (1-5 each) per
answer, via a **separate** LLM call from the one that generated the
answer — same principle as Day 7's evaluator being distinct from the
generator. A judge that's also the author of the thing it's judging
isn't an independent check, it's the model grading its own homework.

**Worth doing deliberately:** run the judge on q020 (maternity leave)
specifically and read the `reason` field. This is a good test of
whether the judge itself understands the caveat nuance, or just
penalizes any answer that doesn't use the exact phrase from the question.

## Exercise 5 — Trace one multi-agent request

Uses a Day 12 negotiation log (already has per-message latency) as the
multi-agent trace, mapped onto the Supervisor/Agent-A/A2A/Agent-B/Reviewer
picture: `coordinator.py` = Supervisor + A2A layer, `buyer-agent` =
Agent A, `seller-agent` = Agent B, `reviewer.py` = Reviewer.

```bash
# Copy one of Day 12's logs here, or point directly at its path
python -c "
from metrics import analyze_trace_latency
result = analyze_trace_latency('../../a2a/01-negotiation-simulator/logs/<some_conversation_id>.json')
import json
print(json.dumps(result, indent=2))
"
```

**Ask yourself, looking at `breakdown_by_sender`:** did most latency
come from the buyer's LLM calls, the seller's, or the coordinator's
retry/failure handling? In a real multi-agent system this is exactly
how you'd find out whether to optimize a specific agent's prompt,
parallelize two agents that don't need to run sequentially (Day 10's
lesson), or accept that an occasional retry is just the cost of
reliability (Day 12's Exercise 6 decision).

## Exercise 6 — Regression test (the real demo)

**Step 1 — Establish the baseline** (already done above):
```bash
python evaluate.py before
python metrics.py results/before_<timestamp>.json
```
Note the `abstention_accuracy` — travel reimbursement (q011) should
currently pass (agent abstains correctly).

**Step 2 — Inject a real bug.** In `agent.py`, set:
```python
FORCE_ANSWER_EVERYTHING = True
```
This skips the evaluator's judgment entirely — the agent will now
answer using whatever it retrieved, no matter how thin the evidence,
recreating exactly the kind of hallucination risk Day 7 was built to
prevent.

**Step 3 — Confirm the regression:**
```bash
python evaluate.py after_broken
```
Travel reimbursement should now get answered instead of abstained —
q011 flips from pass to fail.

**Step 4 — Fix it.** Set `FORCE_ANSWER_EVERYTHING = False` again, then:
```bash
python evaluate.py after_fixed
```

**Step 5 — Compare all three, formally:**
```python
from metrics import regression_compare, load_json
dataset = load_json("dataset.json")
print(regression_compare("results/before_<ts>.json", "results/after_broken_<ts>.json", dataset))
print(regression_compare("results/after_broken_<ts>.json", "results/after_fixed_<ts>.json", dataset))
```

The first comparison should show q011 in `regressions`. The second
should show it in `fixes`. This is the actual mechanism a regression
pipeline needs: not eyeballing pass counts, but naming specifically
*which* question flipped and in which direction.

---

## 🧠 EM-Level Thinking: "Accuracy went from 91% to 94%. Should we deploy it?"

The honest answer is: **not yet — that number alone is not sufficient
evidence.** Here's what to actually check first, category by category:

**Quality**
- *Which metric improved?* "Accuracy" is vague — was it answer
  correctness, retrieval success, abstention accuracy, or some blended
  score? These can move in opposite directions while a single combined
  number looks fine.
- *On which dataset?* A 20-question dataset moving from 91% to 94% is
  a difference of roughly half a question — statistically almost
  meaningless. The same delta on a 500-question set is a real signal.
- *Did some category get worse?* An aggregate improving while
  `unanswerable` accuracy quietly drops is a worse outcome than the
  aggregate suggests — exactly the kind of thing category-level
  breakdown (not just one number) is for.

**Reliability**
- *Did tool/retrieval failures increase?* A model that got "better" at
  answering by retrying more aggressively might be masking a retrieval
  problem, not fixing one.
- *Did hallucinations increase?* Possible for a system to answer more
  questions (higher "coverage") while also fabricating more — these
  need to be tracked as separate metrics, not one conflated "success rate."

**Cost**
- *Did token usage increase?* A gain achieved by generating longer,
  more hedge-y answers, or by retrying more before answering, might not
  be worth its added cost per request at production volume.
- *Did we add more LLM calls?* More calls per request (extra rewrite
  attempts, an added judge step) is a legitimate way to improve
  quality — but it needs to be a stated tradeoff, not a surprise
  discovered after rollout.

**Latency**
- *Did p95 increase?* Average latency can look fine while p95 gets
  meaningfully worse — and p95 is what your slowest, most frustrated
  users actually experience.

**Coverage**
- *Are production failures represented in the eval dataset?* If the
  20 (or even 100) questions don't include the actual failure patterns
  real users hit, a high score on this dataset says very little about
  real-world reliability. This is the single most common way an eval
  score lies to you.

**Regression**
- *Did existing golden examples stay stable?* This is literally
  Exercise 6's mechanism — a pass-rate improving overall while a
  previously-solid case (like travel reimbursement) quietly breaks is
  exactly the failure mode `regression_compare()` is built to catch.
  "94% > 91%" tells you nothing about whether that happened.

**The actual difference this section is pointing at:** *"the score
improved"* is an observation. *"We checked quality per category, cost,
latency at p95, whether this dataset represents real failures, and
confirmed no existing golden case regressed"* is evidence. A VP asking
this question deserves the second answer, not the first — and if you
can't produce the second answer yet, the honest response is "not yet,
here's what I still need to check," not a yes.

## Setup

```bash
pip install langchain langchain-ollama langgraph
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Files

```
day-13/
├── README.md
├── dataset.json     Exercise 1 — 20 questions, 5 categories
├── documents/        the 4 policy docs (carried forward)
├── ingest.py         builds vector_store.json
├── retrieve.py        semantic search (unchanged from Day 8)
├── agent.py           Exercise 2 — instrumented LangGraph agent + Exercise 6's bug switch
├── evaluate.py         Exercise 2 — runs the dataset, saves timestamped results
├── metrics.py           Exercises 3, 4, 5, 6 — metrics, judge, trace analysis, regression
└── results/              populated at runtime
```
