# SCDMP foundation-conditioned event-order value implementation threshold

Status: `PRODUCTION_PIPELINE_IMPLEMENTED_SCIENTIFIC_INFERENCE_HOLD`

The retained conclusion-blind review is terminal and rejects the earlier 18-action finite-selector
opportunity law at the definition level. The separately frozen fixed-state, fixed-`k`, precommitted
2×3 candidate-action gate below avoids both selector regret and assay-state copula ambiguity and
has a technically accepted implementation. It inherits no polarity from the rejected object. Its
reserved phase entry is fail-closed before every result-bearing effect because the historical
Student-t rule below lacks a frozen finite-sample coverage justification.

## Scientific object

At `QUAD-UAV-PALLET-GANTRY-24P5M-v1`, test whether each graph-matched precommitted first action beats
its graph-mismatched counterpart and one common conservative action on native full-mission value,
conditional on one fresh competent order-erased foundation.

This is a fixed-host event-order-value gate, not learned duration/hazard/lease, arbitrary-K,
arbitrary-word semigroup, adapter value, variable population, safety, or deployment work. Freeze
primitive tick `0.1s`, horizon 364, and external `k=13`.

Foundation training uses the prospectively completed product law

```text
Uv, Uy, Uphi iid Uniform[0,1)
v=0.03*Uv
y=0.02*Uy-0.01
phi=0.02*Uphi-0.01
x=w=omega=z_1:4=f=0
prior action=1
prior held load-share command r_1:4=0
n=0
```

with no graph or disturbance dependence. The claim assay uses the reachable public Dirac state

```text
s0=(x=0,v=0.015,y=0,w=0,phi=0,omega=0,
    z_1:4=0,f=0,prior action=1,prior held load-share command r_1:4=0,n=0,k=13)
```

under exactly two interventions:

```text
HR: (HOOK_HANDOFF, FORMATION_ROTATE), p=(4,2,1,3), q=1
RH: (FORMATION_ROTATE, HOOK_HANDOFF), p=(1,4,2,3), q=0
```

First-renewal public observations must be byte-identical; only latent support assignment differs.
Roster/entity identity stays fixed and no membership or partner-adaptation claim is made.

## Competent order-erased foundation

Train one fresh `FoundationActorCritic` from genesis for 160 updates, 12 complete fixed-13 episodes
per update, balanced across graphs. No historical checkpoint/result/seed selection/retry transfers;
the actor and critic receive no graph `q`, ordered token, or latent assignment.

Competence uses 120 fresh missions, 60 per graph, and a seven-member Bonferroni family with
`alpha=0.05/7`. The exact one-sided Clopper--Pearson bounds are

```text
L(s,n)=0                         if s=0
L(s,n)=BetaInv(alpha;s,n-s+1)    otherwise

U(s,n)=1                         if s=n
U(s,n)=BetaInv(1-alpha;s+1,n-s)  otherwise
```

Competence resets use the same displayed product law. Their RNG is fresh and disjoint from both
training and the 2×3 assay, and competence missions are independent across graphs rather than
cross-graph tape-paired.

Require each graph safe-docking lower bound `>0.72`, pooled lower bound `>0.84`, and each of four
pooled physical-failure upper bounds `<0.10`. Boundary contact, incomplete evaluation, or a valid
nonpass stops before assay tapes exist.

## Exact 2 × 3 assay

Precommit existing catalogue actions:

```text
COMMON = index 0  = (1,(0,0,0,0))
A_HR   = index 10 = (2,(1,-1,0,0))
A_RH   = index 12 = (2,(0,0,1,-1))
```

An analytic frozen fixture gives the registered local loaded-cable witness: `0.84` matched, `0.94`
mismatched, and common-action maximum `0.66`. The existing native TEST_ONLY observable must reproduce
the corresponding threshold classifications; it does not expose exact load values and therefore is
not described as an exact-value measurement. Bind 24 complete disturbance tapes addressed only by
tape/tick/component; every tape is shared across all six graph/action cells, giving one accepted
width-144 native session.

Force the precommitted action for the first 13 ticks or absorption, then return active lanes to the
same immutable foundation under deterministic lexicographic argmax. The first hold is not a
foundation query. No realized tape selects an action.

The sole endpoint is

\[
U_{lga}=1\{\text{safe dock}\}(1-\text{dock tick}/364).
\]

Failure and timeout are zero. Training reward, interval reward, instantaneous load, RATE diagnostics,
and partial cells cannot activate a branch. With `a0=A_RH`, `a1=A_HR`, and `c=COMMON`, freeze

```text
d_0m = mu_0,a0 - mu_0,a1
d_1m = mu_1,a1 - mu_1,a0
d_0c = mu_0,a0 - mu_0,c
d_1c = mu_1,a1 - mu_1,c

I   = 0.5*(d_0m+d_1m)
V_A = min(0.5*d_0m,
          0.5*d_1m,
          0.5*(d_0c+d_1c))
```

Compute these only after all cells terminate. Across 24 tape blocks use one four-member family on
`(d_0m,d_1m,d_0c,d_1c)` of one-sided paired Student-t bounds with `df=23`, critical quantile
`1-0.05/4`, float64 `fsum` reductions, and explicit zero-variance handling.
`TARGET_CANDIDATE_ORDER_VALUE_ESTABLISHED` requires every adjusted lower bound strictly positive.
Every other complete valid outcome closes this exact state/K/foundation/candidate-set gate before
any adapter.

The preceding Student-t rule is retained only as historical implementation provenance and a
TEST_ONLY counterexample target. It cannot activate a scientific branch. Under the bounded endpoint
law, each contrast lies in `[-363/364,363/364]`; the zero-variance rule can return four positive
lower bounds with probability `(127/128)^24` even when all four population means are
`-59/11648`. Production remains on `SCIENTIFIC_INFERENCE_HOLD` until Root prospectively freezes a
finite-sample-valid method, material margin or explicit zero margin, tape count, stop rule, atomic
result law and revised resource envelope.

## Typed RATE receiver seam

Add output-disconnected pure contracts for `ClockControlSpec`, primitive spacing, eligible boundary,
executed rate event/receipt, service-cost breakdown, uniform source, and receiver protocol, plus
`rate_probability`, event execution, accounting, and age-ceiling functions.

RATE input contains only real-boundary eligibility and treatment-common primitive spacing. It cannot
receive graph/order, action/logits, task content, age, future tape, reward/outcome, or result values.
Dummy/masked boundaries call neither RNG nor receiver. This host has no native service event or event
charge, so RATE is diagnostic-only and cannot affect `U`, foundation, inference, or branches. No
ONLGR polarity or numeric threshold transfers.

## Isolated implementation surface

```text
experiments/candidates/scdmp_variable_k/foundation_conditioned_event_order_value/
  __init__.py
  __main__.py
  contracts.py
  rng.py
  foundation.py
  training.py
  host_bridge.py
  panel.py
  clock_controls.py
  analysis.py
  lifecycle.py
  artifacts.py
  source_manifest.py
  runner.py

tests/experiments/candidates/scdmp_variable_k/
  test_fceov_contract_and_cli.py
  test_fceov_foundation_training.py
  test_fceov_foundation_competence.py
  test_fceov_native_2x3_panel.py
  test_fceov_pairing_and_analysis.py
  test_fceov_clock_controls.py
  test_fceov_artifact_resume.py
  test_fceov_dependency_firewall.py
```

Reuse only the old action catalogue, host types/backend, foundation model, and schedule-independent
PPO/GAE/AdamW algebra. Do not modify native C++, shared registry, or frozen TBCC lineage. Firewall old
opportunity/production/lifecycle/RNG/result modules that encode the rejected 18-action selector.

Schemas cover manifest, checkpoint, foundation gate, complete 2×3 result, and terminal fact.

## CLI, direct preflight and scientific hold

```text
python -m experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value.runner \
  --preflight-only --manifest PATH --result-root PATH

python -m experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value.runner \
  --phase FOUNDATION_AND_2X3 --manifest PATH --result-root PATH
```

The preflight command exact-validates the prospective V2 manifest, resource/RNG inventories, public
alias and a real native width-144 reset session without creating the result root. The phase command
is reserved but not READY: it reruns preflight and returns `SCIENTIFIC_INFERENCE_HOLD` before result
root creation, fresh-master generation, numerical-runtime mutation, model materialization,
training, competence, tapes, panel execution or publication.

Behind that hold, the private future pipeline fixes one internally generated OS 256-bit master,
160×12 fixed-13 training, one update-160/step-1,920 checkpoint, fresh-genesis direct restore
equality, 120 raw competence records with recomputed bounds, and a raw width-144 precommitted panel.
It has no callable path from raw panel cells to the held t analysis or a passing scientific artifact.

Maximum registered work is 2,184 episodes/rollouts, 794,976 allocated primitive slots, 1,920 AdamW
steps, one checkpoint, 144 forced actions, and at most 61,008 foundation queries, with one worker
and one native/Torch thread. Non-result checks
cover state serialization, H/R aliasing, action mapping, local headroom, fixed-13 training, exact
competence bounds, width-144 inventory, tape equality, selector absence, full-mission accounting,
RATE disconnection, complete-only artifacts, direct resume equality, legacy-schema rejection, and
dependency firewall.

Stop on `SCIENTIFIC_INFERENCE_HOLD`, contract drift, foundation nonpass, alias/headroom failure,
tape leakage, foundation mutation, duplicate/nonterminal lane, resume divergence, partial output,
or resource refusal.

## Claim ceiling

No scientific result is currently available. After a valid future inference freeze, the ceiling is
fixed-simulator, fixed-state, fixed-K, single-foundation candidate-set event-order value against the
best graph-blind fixed or randomized policy on `{A_RH,A_HR,COMMON}` under the registered
disturbance law. It does not compare against the best of all 18 actions or necessarily the
foundation's natural first action. Technical success cannot establish learned chronology,
learned duration, semigroup composition, arbitrary words, variable lifetime/membership, simulator
transfer, UAV safety, deployment, or flight.

## Evidence

- `DIRECTION.md`
- `SCDMP_TARGET_BOUND_COMPETENT_CONTROLLER_ORDER_VALUE_SCIENCE_CARD_REVISION_02_20260821.md`
- `SCDMP_OPPORTUNITY_LAW_SYNTHESIS_READY_20260829.md`
- `SCDMP_FCEOV_WAVE2_SCIENTIFIC_INFERENCE_HOLD_20260831.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/IMPLEMENTATION_THRESHOLD.md`
