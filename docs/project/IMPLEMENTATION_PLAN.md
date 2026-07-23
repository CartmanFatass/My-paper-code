# Useful-effect roster G3 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hash handoffs
> are disabled.

```text
active_implementation=USEFUL_EFFECT_ROSTER_G3
implementation_status=PM_ACCEPTED
design=docs/research/designs/USEFUL_EFFECT_ROSTER_G3.md
backend=cpu
torch_threads=1
primary_comparator=TEAM_REC
primary_estimand=U_ROSTER_ATTN_minus_U_TEAM_REC
formal_run_status=launchable_from_integrated_source
closed_G0_G1_G2_mutation=forbidden
backward_compatibility=not_required
```

## Goal

Implement the frozen demand-served ROSTER_ATTN/TEAM_REC/NO_ROSTER event-level
comparison. Keep the passed structural gate as a source-control function; do not
reuse uniqueness as reward or a result metric.

## Task 1 — Paired useful-effect source

**Status:** completed and focused-source checks accepted.

Add one active-line module for complete demand vectors, uniform deficit
selection, standing counts `d-one_hot(q)`, paired record/packing histories,
anonymous editor events, lifecycle ownership, nuisance gaps and the four profile
supports.

**Focused proof:** source balance and deterministic reconstruction; duplicate
and zero-demand strata; oracle utility 1.0; analytic NO_ROSTER Bayes utilities;
no actor deficit/count/identity/future leakage; exact demand-served utility;
permutation and lifecycle invariance.

## Task 2 — Matched learned editors and PPO

**Status:** completed and replay/gradient/checkpoint checks accepted.

Implement the shared inventory, query encoder, token attention, TEAM_REC GRU,
three declared logit paths, centralized critic, one-step collection, stored-draw
replay, PPO, gradient fences, counters and same-source CPU checkpoint/resume.

**Focused proof:** matched initialization/inventory/exposure; exact logit paths;
token-order invariance; history reconstruction; critic exclusion; replay and
corruption rejection; unused-treatment zero gradients; exact optimizer/RNG
restore and foreign-source rejection.

## Task 3 — Runner, audit and analyzer

**Status:** completed and runner/analyzer checks accepted.

Create train/evaluate/analyze/exercise commands, compact source controls, final
checkpoints, 120 formal evaluation cells and exact-snapshot roster interventions.
Implement paired hierarchical bootstrap and the frozen pure selector.

**Focused proof:** selector precedence; inventory and exposure closure;
source/reference/schema tamper negatives; battery threshold boundaries; exact
formal rejection of exercise artifacts; no import of G0/G1/G2 result selectors.

## Task 4 — Bounded acceptance and active-line replacement

**Status:** completed and bounded CPU exercise accepted.

Run only focused G3 tests with the registered CPU interpreter and one thread,
then one fresh reduced `formal=false exercise`. Inspect source scalar loops,
token packing, actor/critic separation, roster permutation, recurrence history,
RNG ownership, replay, checkpoint persistence and serial evaluation.

After acceptance, delete the closed G2 trainable runner/core/environment and
their focused tests in the same boundary. Retain G2 design, Chinese report,
evidence note, ignored formal logs and Git history. Keep the small G3 structural
gate because the learned source reuses it as source-control evidence.

Project Manager commits and pushes one exact integrated source. Only that commit
is assigned to the silent experiment operator for formal iteration 4.
Implementation and exercise consume zero iterations; two remain.

## Accepted prelaunch evidence

```text
focused_tests=11_passed
exercise=logs/nonformal_useful_effect_roster_g3_20260723_pm1
exercise_formal=false
exercise_checkpoints=3
exercise_evaluation_references=24
exercise_causal_audits=16
exercise_operational_valid=true
exercise_result=SOURCE_NON_IDENTIFIABLE_USEFUL_ROSTER_G3
formal_validator_rejects_exercise=true
iteration_cost=0
iterations_remaining=2
```

The reduced exercise intentionally fails only the formal natural-audit quota:
16 rows are below the frozen formal quota of 128 per replicate. Source controls,
ledger balance, runner closure, replay, gradients, checkpoints and CPU/thread
identity pass. The exercise result is operational evidence only and cannot be
used as a conclusion-bearing branch.
