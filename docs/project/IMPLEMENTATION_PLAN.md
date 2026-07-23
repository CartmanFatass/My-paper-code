# Count-preserving roster G4 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hash handoffs
> are disabled.

```text
active_implementation=COUNT_PRESERVING_ROSTER_G4
implementation_status=PM_ACCEPTED
design=docs/research/designs/COUNT_PRESERVING_ROSTER_G4.md
backend=cpu
torch_threads=1
primary_comparator=ROSTER_ATTN
mission_comparator=TEAM_REC
primary_estimand=U_ROSTER_SUM_minus_U_ROSTER_ATTN
formal_run_status=launchable_from_integrated_source
closed_G0_G1_G2_G3_mutation=forbidden
backward_compatibility=not_required
```

## Goal

Test one algorithmic correction to the validly underpowered G3 package without
changing its source, reward, budget or thresholds. `ROSTER_SUM` preserves
absolute standing-effect multiplicity through a raw count skip while retaining
learned lifecycle metadata. Compare it directly with the exact normalized
`ROSTER_ATTN` path and the ordinary `TEAM_REC` path.

## Task 1 — Count-preserving active path

**Status:** completed and focused checks accepted.

Replace the active G3 identity with G4. Keep the complete demand source and
shared policy inventory. Add exact masked effect counts, float64 accumulation
for token-order-stable learned means and the `ROSTER_SUM` logit path. Preserve
the G3 attention and team recurrence paths only as active G4 comparators.

**Focused proof:** exact count recovery, permutation invariance, no actor
deficit/count leak beyond current roster tokens, matched initialization,
stored-draw replay, zero unused-path gradients, optimizer/RNG checkpoint restore.

## Task 2 — G4 runner and selector

**Status:** completed and focused checks accepted.

Reuse the accepted source/runner mechanics under new G4 schemas, seeds and
authorization token. Audit only `ROSTER_SUM`. Replace G3 estimands with
`G_attn=U_SUM-U_ATTN` and `G_team=U_SUM-U_TEAM`; make access specific to
ROSTER_SUM and retain the exact battery thresholds and first-match semantics.

**Focused proof:** all selector boundaries; equal arm exposure; exact artifact
inventory; source/reference/utility tamper rejection; exercise rejected as
formal evidence.

## Task 3 — Bounded acceptance and active-line replacement

**Status:** completed and bounded CPU exercise accepted.

The focused G4 suite passes 12 tests with the registered CPU interpreter and
one thread. The fresh nonformal exercise closes train/evaluate/analyze,
checkpoints, three arms, all profiles, causal audit and source controls. The
former G3 implementation/runner/test names are removed; Git history and the G3
design, result evidence, Chinese report and ignored formal artifacts remain.

## Accepted prelaunch evidence

```text
focused_tests=12_passed
exercise=logs/nonformal_count_preserving_roster_g4_20260723_pm1
exercise_source_commit=f3bd0e17ed40ee0e2e5fdfd76d67405c5ef8643d
exercise_formal=false
exercise_checkpoints=3
exercise_evaluation_references=24
exercise_causal_audits=16
exercise_operational_valid=true
exercise_result=SOURCE_NON_IDENTIFIABLE_COUNT_ROSTER_G4
formal_validator_rejects_exercise=true
iteration_cost=0
iterations_remaining=1
```

The reduced exercise intentionally fails only the formal natural-audit quota.
Its result has no scientific meaning. Source controls, evaluation ledgers,
replay, gradients, checkpoints, CPU/thread identity and the G4 selector path
close successfully.

Project Manager will commit and push one integrated G4 source. Only that commit
may be assigned to the silent experiment operator with token
`AUTHORIZE_COUNT_PRESERVING_ROSTER_G4_FORMAL_CPU_V1`. A valid run consumes the
fifth and final conclusion-bearing iteration and requires the Chinese
`docs/report/ITERATION_5.md` before terminal project disposition.
