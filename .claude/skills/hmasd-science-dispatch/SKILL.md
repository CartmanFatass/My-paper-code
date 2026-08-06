---
name: hmasd-science-dispatch
description: Use before sending any question, registration, or alignment audit to External Pro in the HMASD project, and when deciding whether a question belongs to Pro at all. Enforces the routing rule and the pre-dispatch gate.
---

# HMASD Science Dispatch

## Contract boundary

This skill grants no scientific authority. External Pro decides estimand,
population, null, identification, registration admissibility, and what a result
may be claimed to establish. This skill governs only **which questions reach
Pro and in what condition** — and it is subordinate to
`.claude/ORCHESTRATOR_WORKFLOW.md` Section 3, which it operationalizes.
`AGENTS.md` remains the sole project authority.

```text
skill_kind=science_dispatch_gate
supersedes=nothing; operationalizes ORCHESTRATOR_WORKFLOW.md Section 3
scientific_authority=none
pro_round_trip_minutes=15..40
pro_transport_concurrency=1          # single tab, strictly sequential
local_verification_cost=seconds
gate_script=.claude/skills/hmasd-science-dispatch/scripts/hmasd_dispatch_receipt.py
gate_is_blocking=true                # non-zero exit means do not dispatch
document_review_required=true
document_review_agent=hmasd-reviewer
document_review_terminal=DOCUMENT_MATCHES_SOURCE
receipt=30_DISPATCH_RECEIPT.json
manifest=10_DISPATCH_MANIFEST.json
number_traceability=strict           # every substantive literal or a whitelist reason
whitelist_requires_reason=true
resend_after_fetch_failed=forbidden  # a client abort means SUBMITTED
```

## Why this exists, and why prose alone was not enough

`ORCHESTRATOR_WORKFLOW.md` already carried a "self-check before dispatch"
instruction, and two mechanically-findable defects reached Pro anyway: a
bias-only quantity reported as a GRU update gate, and gate saturation reported
as bitwise carry. In both, what the reviewer actually did was read the source
and recompute — mechanical verification spent on the scientific-judgment
channel.

So the load-bearing parts of this skill are **the script and the subagent**, not
this document. A future orchestrator that reads this file and skips the script
has gained nothing. The script exits non-zero; that is the guarantee.

## Step 1 — Route. Does this belong to Pro at all?

**Send to Pro** — Pro alone decides:

- estimand, population, null, unit of analysis;
- whether a design identifies what it claims to identify;
- whether a registration is admissible for execution, before any registered
  kernel is observed;
- what a measured result may and may not be claimed, and the exact sentence;
- park / closure / reactivation;
- the reading of a number whose arithmetic is not in dispute.

**Never send. Settle locally, always:**

- whether a computed quantity is the quantity it is named after;
- whether two objects are equal, disjoint, independent, or held out — write the
  predicate and run it over the actual registered constants;
- whether a default equals the registered value;
- whether an identity holds in the executed library at the executed version —
  execute it;
- arithmetic, digests, counts, file contents, source facts;
- whether an inference is valid **given** facts that can be measured.

**The one-line test.** Before dispatching, state what this round buys that a
local check could not. If the answer is "confirmation that my arithmetic or my
reading of the source is right", do not dispatch — check it.

This applies to numbers that arrive *from* Pro too. An arithmetic slip in a
returned ruling is corrected locally and recorded with both derivations; it is
not worth a round trip. (This has happened: a licensed interval endpoint was
quoted one digit high, and the gate caught it.)

## Step 2 — Measure, then write

Write the document from measured numbers. Never write the numbers from the
document. Paste tool output rather than re-typing it: hand-formatted tables are
where transcription errors live, and the gate in Step 4 exists because one
reached Pro.

Where a claim is of the form "this is not generic" or "this is not a
formality", **measure it before writing the argument** — the measurement often
determines what the argument should say.

## Step 3 — Clean-context document review (mandatory)

Spawn `hmasd-reviewer` on the outgoing document **and** the source it describes.
Its position is structurally the same as Pro's: a reader holding both, who has
not seen the implementation reasoning. Every registration round rejected for a
prose/code mismatch would have been visible to one.

Give it exactly this job:

> Does this document describe this code? For every claim about behavior, name
> the file and line that implements it, or report the mismatch. For every
> number, say where it came from. Do not evaluate the science.

Save its verbatim output to `15_DOCUMENT_REVIEW.md` in the review item
directory, ending with exactly one terminal line:

```text
DOCUMENT_MATCHES_SOURCE
DOCUMENT_MISMATCH
```

The gate requires the file and the accepting terminal. Do not write the terminal
yourself on the reviewer's behalf.

## Step 4 — Run the gate

Write `10_DISPATCH_MANIFEST.json` in the review item directory:

```json
{
  "question": "20_RAW_QUESTION.md",
  "truth_sources": [
    {"kind": "json", "path": "local_research/portfolio/artifacts/<artifact>.json"},
    {"kind": "text", "path": "local_research/pro_reviews/<prior>/40_RAW_RESPONSE.md"},
    {"kind": "command", "argv": ["<python>", "-c", "<recompute derived values>"]}
  ],
  "preconditions": [
    {"name": "codex_boundary_diff_empty",
     "argv": ["git", "diff", "dd1a9bb4", "--stat", "--",
              "AGENTS.md", ".agents/", ".codex/", "docs/project/",
              "scripts/hmasd_workspace_ticket.py",
              "scripts/hmasd_workspace_boundary_guard.py"],
     "expect_empty_stdout": true},
    {"name": "candidate_tests",
     "argv": ["<python>", "-m", "pytest", "tests/experiments/candidates/<cand>/", "-q"]}
  ],
  "whitelist": {"<literal>": "<why nobody recomputed it>"}
}
```

Then:

```bash
python .claude/skills/hmasd-science-dispatch/scripts/hmasd_dispatch_receipt.py \
    --item local_research/pro_reviews/<item>
```

`DISPATCH_PERMITTED` is required to proceed. On `DISPATCH_BLOCKED`, fix the
document or add the missing derivation — **never widen the whitelist to make a
figure pass.** The whitelist is the list of numbers nobody recomputed, and it
travels in the receipt for exactly that reason.

What the gate checks and what it does not: it proves every substantive figure
was computed. It does not prove the prose is true (Step 3) or that the science
is sound (Pro). Substantive means integers ≥ 3 digits, floats ≥ 2 decimals, hex
≥ 8 characters; list markers, one-decimal section numbers and ISO dates fall
below the floor deliberately, because a checker with false positives gets
switched off.

## Step 5 — Dispatch, once

```bash
node scripts/pro_review_transport.mjs \
    --question local_research/pro_reviews/<item>/20_RAW_QUESTION.md \
    --out      local_research/pro_reviews/<item> \
    --resume   https://chatgpt.com/c/<conversation-id>
```

Same research direction ⇒ same conversation. Different direction ⇒ different
conversation.

**A `fetch failed` after roughly five minutes is a client abort, and it means
the question was SUBMITTED.** Never resend. The transport recovers and
completes; the observed pattern is
`[client abort after submission: fetch failed] observing` followed by
`AGENTIFY_REVIEW_BATCH_RESULT status=COMPLETE`.

Transport is one tab and strictly sequential. A second direction waits.

## Step 6 — Archive verbatim, then act

Write `40_RAW_RESPONSE.md` from the results envelope and **byte-compare it back
before anything else happens to it**; record size and SHA-256. Pro is never
simulated and a response is never paraphrased into the record.

Then apply the ruling, update the portfolio document and
`local_research/RESEARCH_CONTINUITY.md`, and refresh the OneDrive backup —
`local_research/` is gitignored because the repository is public, so the backup
is the only durability it has.

## What this skill does not cover

Implementation, refactoring, debugging, subagent orchestration for engineering
work, commit and push discipline, and the boundary rules. Those live in
`.claude/ORCHESTRATOR_WORKFLOW.md` Sections 2 and 5–8. This skill is only the
dispatch path.
