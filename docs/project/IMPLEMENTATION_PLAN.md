# Useful-effect roster G3 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution, compatibility work and workflow hash handoffs
> are disabled.

```text
active_implementation=USEFUL_EFFECT_ROSTER_G3
implementation_status=AUTHORIZED
design=docs/research/designs/USEFUL_EFFECT_ROSTER_G3.md
backend=cpu
torch_threads=1
primary_comparator=TEAM_REC
primary_estimand=U_ROSTER_ATTN_minus_U_TEAM_REC
formal_run_status=not_launchable_until_implementation_acceptance
closed_G0_G1_G2_mutation=forbidden
backward_compatibility=not_required
```

## Goal

Implement the frozen demand-served ROSTER_ATTN/TEAM_REC/NO_ROSTER event-level
comparison. Keep the passed structural gate as a source-control function; do not
reuse uniqueness as reward or a result metric.

## Task 1 — Paired useful-effect source

**Status:** pending.

Add one active-line module for complete demand vectors, uniform deficit
selection, standing counts `d-one_hot(q)`, paired record/packing histories,
anonymous editor events, lifecycle ownership, nuisance gaps and the four profile
supports.

**Focused proof:** source balance and deterministic reconstruction; duplicate
and zero-demand strata; oracle utility 1.0; analytic NO_ROSTER Bayes utilities;
no actor deficit/count/identity/future leakage; exact demand-served utility;
permutation and lifecycle invariance.

## Task 2 — Matched learned editors and PPO

**Status:** pending.

Implement the shared inventory, query encoder, token attention, TEAM_REC GRU,
three declared logit paths, centralized critic, one-step collection, stored-draw
replay, PPO, gradient fences, counters and same-source CPU checkpoint/resume.

**Focused proof:** matched initialization/inventory/exposure; exact logit paths;
token-order invariance; history reconstruction; critic exclusion; replay and
corruption rejection; unused-treatment zero gradients; exact optimizer/RNG
restore and foreign-source rejection.

## Task 3 — Runner, audit and analyzer

**Status:** pending.

Create train/evaluate/analyze/exercise commands, compact source controls, final
checkpoints, 120 formal evaluation cells and exact-snapshot roster interventions.
Implement paired hierarchical bootstrap and the frozen pure selector.

**Focused proof:** selector precedence; inventory and exposure closure;
source/reference/schema tamper negatives; battery threshold boundaries; exact
formal rejection of exercise artifacts; no import of G0/G1/G2 result selectors.

## Task 4 — Bounded acceptance and active-line replacement

**Status:** pending.

Run only focused G3 tests with the registered CPU interpreter and one thread,
then one fresh reduced `formal=false exercise`. Inspect source scalar loops,
token packing, actor/critic separation, roster permutation, recurrence history,
RNG ownership, replay, checkpoint persistence and serial evaluation.

After acceptance, delete the closed G2 trainable runner/core/environment and
their focused tests in the same boundary. Retain G2 design, Chinese report,
evidence note, ignored formal logs and Git history. Keep the small G3 structural
gate because the learned source reuses it as source-control evidence.

Project Manager then commits and pushes one exact integrated source. Only that
commit can be assigned to the silent experiment operator for formal iteration
4. Implementation and exercise consume zero iterations; two remain.
