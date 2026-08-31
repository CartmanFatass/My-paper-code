# SCDMP foundation-conditioned event-order value implementation threshold

Status: `VALID_COMPLETE_NOT_ESTABLISHED_OBJECT_CONSUMED`

The retained conclusion-blind review is terminal and rejects the earlier 18-action finite-selector
opportunity law at the definition level. The separately frozen fixed-state, fixed-`k`, precommitted
2×3 candidate-action gate below avoids both selector regret and assay-state copula ambiguity and
has a technically accepted V2 implementation and a frozen V3 definition. It inherits no polarity
from the rejected object. The first V3 evidence attempt is quarantined as
`INVALID_EVIDENCE_RESOURCE_ENVELOPE_UNOBSERVED`; missing prospective assessment and run-time
resource telemetry mean that attempt did not completely implement the assignment and did not
consume the scientific object. The fresh `.2` replacement is also non-consuming invalid evidence:
its final atom range-scaled the marginal lower bounds before taking their minimum and therefore
published a raw-utility-scale bound instead of the frozen unit-range-normalized `L_theta`. The fresh
`.3` replacement corrected that atom result-blind, completed validly and returned
`TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION`. The exact purchase is consumed
and no further result-bearing replacement is eligible.

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
not described as an exact-value measurement. Bind exactly 562 complete disturbance tapes addressed
only by tape/tick/component. Every tape is shared across all six graph/action cells. Execute 23
strictly serial slices of 24 tapes/144 lanes followed by one final slice of 10 tapes/60 lanes. Slice
boundaries do not change the tape population or inference unit.

The scientific RNG law treats distinct addressed assay draws as an ideal PRF: mutually independent
fair bits across tape/tick/component addresses and independent of the foundation training and
competence domains. Finite-sample claims are conditional on this explicit abstraction; domain
separation alone is not an information-theoretic independence proof.

Force the precommitted action for the first 13 ticks or absorption, then return active lanes to the
same immutable foundation under deterministic lexicographic argmax. The first hold is not a
foundation query. No realized tape selects an action.

The sole endpoint is

\[
U_{lga}=1\{\text{safe dock}\}(1-\text{dock tick}/364).
\]

Failure and timeout are zero. Training reward, interval reward, instantaneous load, RATE diagnostics,
and partial cells cannot activate a branch. With `a0=A_RH`, `a1=A_HR`, and `c=COMMON`, retain the
raw tape contrasts

```text
d_0m,i = U_i(0,a0) - U_i(0,a1)
d_1m,i = U_i(1,a1) - U_i(1,a0)
d_0c,i = U_i(0,a0) - U_i(0,c)
d_1c,i = U_i(1,a1) - U_i(1,c)

G_RH,i     = 0.5*d_1m,i
G_HR,i     = 0.5*d_0m,i
G_COMMON,i = 0.5*(d_0c,i+d_1c,i)

V_A = min(E[G_RH],E[G_HR],E[G_COMMON]).
```

These three means are exactly the matched mapping's balanced-graph value gaps against the three
graph-blind pure vertices. Their simultaneous positivity is necessary and sufficient for superiority
over every fixed or randomized graph-blind policy on the candidate set. Separate positivity of
`d_0c` and `d_1c` is not required.

Let `B=363/364`. The supports are `G_RH,G_HR in [-B/2,B/2]` with range `B`, and
`G_COMMON in [-B,B]` with range `2B`. Normalize every component by its own complete range:

```text
X_j,i = 0.5 + G_j,i/R_j in [0,1].
```

After all 3,372 cells terminate, compute for each component

```text
p_j = 1                                            if mean(X_j)<=0.5
p_j = exp(-562*kl(mean(X_j)||0.5))                otherwise.
```

The only positive branch is the all-or-none intersection-union decision

```text
max(p_RH,p_HR,p_COMMON) < 0.05.
```

No component pass or marginal lower limit is independently publishable. Invert the three marginal
tests only to publish the single unit-range joint lower bound
`L_theta=min(ell_RH-0.5,ell_HR-0.5,ell_COMMON-0.5)`; `L_theta>0` is equivalent to `V_A>0`. The
scientific margin is zero. Exact endpoint-grid passage
requires integer numerator sums at least `21,046`, `21,046`, and `42,091`; the previous integer never
passes. The planning alternative is a mean gap equal to `0.1` of each component's full support range.
At `n=562` its discrete distribution-free joint-power lower bound is `0.801021247429385`; `n=561`
gives `0.799048262648854`.

The Student-t analyzer remains TEST_ONLY defect provenance and cannot activate any branch. Common
tapes do not justify sign flips or action/graph permutations. Exact formulas, the IUT proof,
counterexamples, zero-margin rationale, numeric conventions and claim ceiling are frozen in
`SCDMP_FCEOV_PROSPECTIVE_FINITE_SAMPLE_INFERENCE_FREEZE_20260831.md`.

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

## Quarantined CLI and replacement-entrypoint threshold

```text
python -m experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value.runner \
  --preflight-only --manifest PATH --result-root PATH

python -m experiments.candidates.scdmp_variable_k.foundation_conditioned_event_order_value.runner \
  --phase FOUNDATION_AND_2X3 --manifest PATH --result-root PATH
```

The existing `.1` and `.2` production roots remain permanently quarantined. The valid `.3` root is
immutable consumed evidence. Every phase invocation against any of the three must refuse reentry
before model, master, checkpoint, tape or output creation. `--preflight-only` remains available for
non-result checks only; no further result command is eligible for this object.

The frozen object uses one internally generated OS 256-bit master per evidence instance, 160×12 fixed-13 training,
one update-160/step-1,920 checkpoint, 120 competence records, 23 width-144 slices and one width-60
slice over 562 tape addresses. These counts are the immutable replacement workload.

The frozen maximum is 5,412 episodes/rollouts, 1,969,968 allocated primitive slots, 1,920
AdamW steps, one checkpoint, 3,372 forced actions, and at most 148,164 foundation queries, with one
worker and one native/Torch thread. The frozen ceilings were 300 seconds, 1 GiB peak RSS, 64 MiB
scratch and 64 MiB durable. Non-result checks
cover state serialization, H/R aliasing, action mapping, local headroom, fixed-13 training, exact
competence bounds, width-144 and width-60 inventory, 562-tape equality, selector absence,
full-mission accounting, RATE disconnection, integer/KL branch equality, all-or-none IUT,
complete-only artifacts, same-master frontier resume, legacy-schema rejection, and dependency
firewall.

The production phase must now stop unconditionally before effect because the exact object is
consumed. There is no formal resume of `.1`, `.2` or `.3`; same-master frontier recovery remains only
a TEST_ONLY correctness surface. Changed `n`, thresholds, support, foundation, estimand,
comparators, stopping rule or any result-aware extension is a new scientific object rather than a
replacement.

Root/reviewer final validity found the `.1` artifact's sole invalidator to be the missing
prospective direction-specific `assess-run` plus missing formal-process peak-RSS and scratch-peak
telemetry. Fixed 4 GiB admissions, wall, durable and structural checks passed, but no post-hoc
observation can replace the missing evidence. Therefore no scientific branch exists for the
quarantined `.1` attempt.

Independent scientific intake found `.2` technically complete but scientifically invalid because
its result atom did not contain the required normalized `L_theta`. The stored raw-scale minimum is
a different parameter when component ranges differ. No `.2` scientific outcome may be interpreted;
the artifact cannot be corrected in place and does not consume the object.

Independent scientific intake found `.3` valid and complete. Its exact integer sums were `16,665`,
`16,565` and `14,809`, all below their frozen thresholds. The joint p-value bound was
`0.6905544624698072` and normalized `L_theta` was `-0.03343566747722848`. The disposition is
`TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION`; no component has standalone
claim authority, zero or negative order value is not established, and the exact purchase is
consumed before an adapter.

The completed result-blind replacement work established:

- the existing `.1` and `.2` roots remain quarantined and `.3` is immutable consumed evidence;
- every result reentry or undeclared root refuses before scientific effect;
- stage same-master initialization/finalization atomically;
- create-only persist path, length and full raw bytes for 14 owned Python modules, three allowlisted
  dependencies, native C++ and the actual loaded DLL, then require resume
  `read_bytes()==persisted_bytes`;
- bind a final fixture bundle directly to canonical resolved root, raw master bytes, run record and
  raw-byte snapshot;
- add identity-free prospective direction assessment and live wall/peak-RSS/scratch/durable
  telemetry with missing measurements failing closed.
- `L_theta=min_j(ell_j-0.5)` is published explicitly on its normalized scale, with unequal-range
  synthetic checks separating it from `min_j R_j(ell_j-0.5)`.

Do not add hashes, digests, identity, authentication or approval fields. These surfaces may be
exercised by unit, fixture, TEST_ONLY native and result-blind preflight tests before the replacement
command becomes reachable. Passing tests do not themselves make result evidence admissible; the
replacement must also pass the complete prospective resource contract on its own invocation.

## Claim ceiling

One valid scientific nonpass is available. It establishes only that strict candidate-set dominance
was not established at the frozen resolution; it does not establish zero, negativity or a failed
population component. No component is independently publishable, and no further run or adapter is
eligible for the consumed object. Neither technical hardening nor the result can establish learned
chronology, learned duration, semigroup composition, arbitrary words, variable lifetime/membership,
simulator transfer, UAV safety, deployment or flight.

## Evidence

- `DIRECTION.md`
- `SCDMP_TARGET_BOUND_COMPETENT_CONTROLLER_ORDER_VALUE_SCIENCE_CARD_REVISION_02_20260821.md`
- `SCDMP_OPPORTUNITY_LAW_SYNTHESIS_READY_20260829.md`
- `SCDMP_FCEOV_WAVE2_SCIENTIFIC_INFERENCE_HOLD_20260831.md`
- `SCDMP_FCEOV_PROSPECTIVE_FINITE_SAMPLE_INFERENCE_FREEZE_20260831.md`
- `SCDMP_FCEOV_V3_INVALID_EVIDENCE_RESOURCE_AUDIT_20260831.md`
- `SCDMP_FCEOV_REPLACEMENT_VALIDITY_AND_INTAKE_20260831.md`
- `SCDMP_FCEOV_REPLACEMENT_RESULT_INTAKE_20260831.md`
- `SCDMP_FCEOV_REPLACEMENT_03_VALID_RESULT_INTAKE_20260831.md`
- `docs/research/candidates/opportunity_normalized_lease_gated_rebinding/IMPLEMENTATION_THRESHOLD.md`
