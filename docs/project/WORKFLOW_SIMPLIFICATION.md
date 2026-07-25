# Workflow simplification — what was retired and why

```text
status=IN_FORCE
decided=2026-07-25
decided_by=user
supersedes=the governance apparatus built 2026-07-24/25
```

## The model this replaces everything with

The user's statement, which is the whole of it:

> RL is theory **plus** experiment driven, so only two things actually need
> external review:
>
> 1. **the scientific idea** — already in the workflow;
> 2. **implementation-time detail choices and key algorithms** — confirmed with
>    External Pro **before** implementing.

Everything retired below was machinery for proving a review mechanism worked,
rather than for reviewing anything.

## Why point 2 is the load-bearing one

It is not obvious, so it is worth recording why it holds.

Every expensive failure on this line was an **implementation detail choice that
decided whether a result meant anything** — not a science error and not a coding
error:

- `suffix_noise[intervention_time:]` clobbered positions before `j`, so the audit's
  conditioning history was never fixed. Three stages silently invalidated.
- A pairwise contrast null was used to gate a K-action centered energy — two
  different mathematical objects.
- `P2_AUTHORITY_ZERO_TOLERANCE = 1e-8` against ~`1e-3` sampling noise: a branch
  that could never fire.
- Audit probes drawn uniformly over a grid that includes inactive positions,
  deflating the very quantity being gated.

None of these is a question about *whether the idea is right*. Each is a question
about *how the idea gets realized*, and each was answerable **before writing the
code** by asking "how exactly will this hold `h_j` fixed?" or "is this null the
same object as the statistic?"

That is why post-implementation conformance gates are unnecessary rather than
merely expensive: **the questions they would have caught are answerable earlier
and more cheaply.** Move the question, don't add a gate.

## Retired

| Retired | Was for | Why it goes |
|---|---|---|
| V1 / V2 / V3 validation programme | proving the discovery mechanism transfers | measures the tool, not the science |
| Mechanical gate-close predicate | deciding when a gate may close | there are no gates now, only a pre-implementation question |
| Certificate versioning and dependency closure | invalidating stale approvals | nothing issues certificates |
| Finding-disposition manifest | guaranteeing findings reach the reviewer losslessly | one pass, one author, one round — nothing to lose them in |
| Gate B-core and Gate B-delta | post-implementation conformance and shell drift | the questions move earlier, per above |
| Blinded grading, adjudicator role | scoring the mechanism's recall | no programme to score |
| Task #10 — V0 scoring freeze | freezing thresholds before validation | no validation |

The `adjudicator` reviewer registration **stays registered**. It is idle at zero
cost and re-registering a conversation is more work than leaving it.

## Survives

**The pre-send pass.** One cheap adversarial read of a question before it goes to
Pro. Three for three on catching real defects, including one where the question's
own factual premises were wrong in the direction of the author's preferred plan.
It costs minutes against a serial 15–20 minute Pro round.

**The archetype casebook**, repurposed. It is no longer a gate. It is the
checklist for point 2: *which implementation detail choices must Pro confirm
before we build?* The seventeen archetypes and the Technique class are exactly
that content — each is a real failure where a realization decision silently
decided a result.

**The decision ledger**, minus the certificate machinery. Recording what was
decided, by whom, and what reversing it would change is useful whether or not
anything issues certificates.

## On Pro's ruling

Pro ruled `CHANGES_REQUIRED` on the retired mechanism, listing ten required
changes. That ruling is **not disputed and not overturned**. The mechanism it
ruled on has been retired instead, which is the user's call: the mechanism is
workflow, and workflow is not protected scientific semantics.

The substance Pro contributed survives in the casebook — archetype 17, the
Technique class, and the correction that a reviewer's own unmediated read cannot
be replaced by a reader. What was retired is the apparatus around it.

Recorded so a later reader does not mistake this for ignoring a ruling.

## The cost this was incurred to fix

The apparatus was built in about a day and grew roughly threefold under review of
itself. During that time the science advanced by zero, and a meta-review regress
had no stopping rule. The user's two-point model has one by construction: there
are only two things to review, and neither is the reviewing.
