# Restart handoff

Updated: 2026-07-25, before a context compaction. Branch `untied-k`.

Read `AGENTS.md`, then this file, then `docs/project/RESEARCH_GOAL.md`.

## Next action, exactly

**Reconcile the direction ruling.** It arrived and has not been read:

```text
docs/external-review/rounds/20260725_research_direction_and_ledger/21_PRO_OPEN_RAW.md
```

35,630 characters, captured with `Copy response`, byte-equality verified. Six
questions: is the framing a contribution (Q1), is role stability the right
primitive (Q2), **how to order the exploration ledger** (Q3), is measuring first
right (Q4), is holding the identification line right (Q5), and **which mechanism
carries the variable-`k` line — legacy duration head or R30's KEEP/SET clock
(Q6)**.

Q3 and Q6 decide what gets built. Implement nothing before reading them.

Then: order the ledger per the ruling, run the compute gate, proceed.

## What this project is

`docs/project/RESEARCH_GOAL.md` — read before judging whether work is on path.

HMASD fixes the skill period `k`. Unbinding it explodes the action space; the
contribution is a constraint collapsing it onto a few periods for a payable
search cost, accepting suboptimality. The primitive is **stable versus flexible
role**, period following. Goal is a paper.

Standing check: *what does this let us say about variable `k` that we could not
say before?* More than a sentence to answer means it is off the path.

## How work is reviewed

`docs/project/WORKFLOW_SIMPLIFICATION.md`. Two things get external review: the
scientific idea, and implementation detail choices confirmed **before** building.
Nothing else. One cheap pre-send pass before each Pro round.

## Authorization

**Full and unattended.** Never return to the user for resource or compute
permission. Compute is authorized; only timing is gated:

```text
scripts/check_compute_free.ps1  ->  COMPUTE_FREE run | COMPUTE_BUSY wait 1h, recheck
```

Last reading `COMPUTE_BUSY`. The machine is shared with another line, so busy is
ordinary, not a blocker.

## Live state

- **Ledger**: `docs/project/EXPLORATION_LEDGER.md`. D1 leads — one instrumented
  run settling both premises. Its collapse metrics turned out already wired and
  already present in a completed run.
- **Preliminary, zero compute**: duration-policy entropy falls `0.82 -> 0.60` and
  **plateaus**; `max_frac` rises to `0.70`. That is **concentration, not
  collapse**, and both arms track each other so it is not reward-driven. Caveats:
  candidates were `(1,2,3,4)`, one seed, ~41 updates.
- **G20R3** (`docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R3.md`) is
  drafted against Pro's nine blockers and **on hold** — infrastructure, promoted
  only if it blocks a variable-`k` result.
- **Transport is `project_manager_direct`.** Dispatch `hmasd-review-monitor`
  (haiku, read-only) only to report when generation stops; send, capture and
  archive yourself. Capture with `Copy response` per the skill — a rendered-text
  fallback silently strips markdown, which has already corrupted one archive.
- Two registered reviewers: `open_divergent` for science, `adjudicator` blinded
  and idle. Never cross-post between them.

## Constraints that bite

- `aggressive` is not ours. Never push to it; it is excluded from discussion.
- Children never run Git.
- Contract tests are pinned allow-lists. Adding or removing an agent or skill
  needs the test edited in the same commit or the tree is red in between.
- `run_screen` for G20R2 has never executed end to end at any scale.
- Everything is committed and pushed to `origin/untied-k`.
