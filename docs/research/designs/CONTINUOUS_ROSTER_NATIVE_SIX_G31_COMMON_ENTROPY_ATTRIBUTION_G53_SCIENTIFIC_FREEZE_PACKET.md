# G53 Common-Entropy Attribution — Loop 05 scientific freeze packet

Status: `FREEZE_IMPLEMENTATION`

This public, repository-relative packet records the exact scientific freeze
for the fresh G53 candidate. It is a design and implementation authorization,
not an experimental result or a claim of activation.

## Identity and authorization

- Direction: `CAND-G53-COMMON-ENTROPY-ATTRIBUTION`.
- Candidate: `CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53`.
- Source: `CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53_P0`.
- Loop: `loop_05_replacement`.
- Experiment class: `ORDINARY_NONFORMAL_B_SINGLE_ROOT_CONDITIONAL`.
- Implementation authorization: `ACTIVE_AFTER_ROOT_DISPATCH`.
- Candidate-bound six-phase readiness: required after clean candidate binding.
- Scientific runtime: withheld pending CM technical return and same-direction
  EM intake; formal runtime is not authorized by this freeze.
- Internal handoff SHA-256: `d49f6b32878f172fc37db2200fde8342a4f1456b1bdd9efe465e3d9f8c3ba948`.

CM owns exactly these five fresh paths; predecessor and shared backend paths
are read-only:

1. `ha_ctse_process/continuous_roster_native_six_g31_common_entropy_attribution_g53.py`
2. `scripts/run_continuous_roster_native_six_g31_common_entropy_attribution_g53.py`
3. `tests/ha_ctse_process_continuous_roster_native_six_g31_common_entropy_attribution_g53_test.py`
4. `tests/run_continuous_roster_native_six_g31_common_entropy_attribution_g53_test.py`
5. `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53_CODE_SCIENCE_INDEX.md`

No sixth edit, predecessor mutation, G52 dependency, or predecessor
result/checkpoint/optimizer/manifest/trajectory/run-root initialization is
authorized.

## Commit-pinned provenance

The accepted anchors are provenance only; no predecessor result artifact
initializes G53. The repository is
`https://github.com/CartmanFatass/My-paper-code`.

- G50 source `b8290699f5c10c593bbc21a6666c17950fae84d3`, execution
  `23af6bf7c80a4b73c09cf0423f9f539972b1b55d`, alignment
  `4df41063d077ace7e0c9212e0cbadbf56e1be4b7`; branch
  `FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50`; index
  `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_INDEX.md`;
  result note
  `docs/research/cdc/EVIDENCE_NOTES/20260729_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_RESULT.md`;
  Pro raw
  `docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_formal_result_review/21_PRO_OPEN_RAW.md`.
  Source-pinned URL:
  `https://github.com/CartmanFatass/My-paper-code/blob/b8290699f5c10c593bbc21a6666c17950fae84d3/ha_ctse_process/continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py`.
- G51 source `ce6ed8659c480ca2779155b2871dc82b89fa0e95`, execution
  `fa52274bdc6d90c79ef1658cd5c060046f113692`, aligned implementation
  `188b210975a0f243ae34318d658fbf943d1d63ab`, alignment
  `aa756dcd06a2ea622c155f2983a89bb5d76e9d80`; branch
  `PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51`; index
  `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_CODE_SCIENCE_INDEX.md`;
  exact result `D_G51=0`; result note
  `docs/research/cdc/EVIDENCE_NOTES/20260729_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_FORMAL_RESULT.md`;
  Pro raw
  `docs/external-review/rounds/20260729_g31_phase_a_shadow_baseline_module_reduction_g51_formal_result_review/21_PRO_OPEN_RAW.md`.
  Source-pinned URL:
  `https://github.com/CartmanFatass/My-paper-code/blob/ce6ed8659c480ca2779155b2871dc82b89fa0e95/ha_ctse_process/continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51.py`.

G52 authority, imports, and artifact reads are none. The common Phase-A
ancestor and carry state are forbidden (`G52_CARRY_state_count=0`); G53 is a
fresh end-to-end root.

## Frozen treatment and host

The reference arm uses entropy coefficient `0.01`
(`0x1.47ae147ae147bp-7`); the null arm uses exact `0.0` (`0x0.0p+0`). Both
phases and both PPO passes use the immutable local coefficient. The objective
is `L_c=L_PPO(center_and_population_RMS(r_t))-c*H_active_mean`, where
`H_active_mean` is the active-member/time/batch mean of summed Normal entropy
after `log_std` clamp. Claim identity:
`PRE_TANH_GAUSSIAN_LOG_STD_ENTROPY_BONUS_COEFFICIENT_0P01_VS_EXACT_ZERO`;
estimand `Delta_entropy=U_COMMON_ENTROPY-U_NO_ENTROPY`; positive direction
favors common entropy. Primary utility is capacity-equal final
random/deterministic utility over capacities 6/8/12, margin `0.05`.

Both arms are baseline-free before trajectory or optimizer construction: make
one fresh G50 null/single-immediate model, apply G51 `NoBaselinePhaseAProjection`
once, deep-clone into storage-disjoint arms, retain identical unexposed
slow-critic state through Phase A, then delete it at the common boundary. Do
not use `g51.make_phase_A_models` as the final factory and do not mutate
`g40.ENTROPY_COEFFICIENT`. The same entropy forward/autograd graph is executed
for exact zero, multiplying the finite raw gradient by exact zero; it is never
skipped, detached, or replaced.

Actor input is exactly six coordinates (`capability[0:2]`,
`presentation_priority`, `load`, `target_mix`, `log1p(active_count)`), with
active-mask aggregation/log-count, autoregressive action prefix, action
dimension 2, `H=48`, capacity-8 fixed G32 training source, and G34-P0
fixed/random capacity-6/8/12 evaluation. Preserve actor/log_std 17-name order,
Adam class/hyperparameters, PPO clip, two persistent passes, common phase
projection, fresh empty Phase-B Adam, final-only actor checkpoints, no baseline
actor read, and no new observation/action/reward/target/normalization/
centering/phase/RNG/source/evaluation change.

Only Phase-A update 0, collected before either coefficient-dependent optimizer
step, is materialized once and passed as the identical stored object to both
arm plans. Both complete plans exist before either step. From update 1 onward,
collect separately on-policy per arm with paired episode IDs and exogenous
ledger/action-noise roles; never feed a diverged trajectory to its mate or
force post-treatment equality. Count physical collection once while retaining
two arm exposures.

## Exact nonformal budget, seeds, and gates

`formal=false`; one independent root; Phase A/B updates per arm `10/10`;
environments `8`; `H=48`; PPO passes `2`; one shared pretreatment batch and 39
later arm-local batches; training transitions `(2*(10+10)-1)*8*48=14976`;
evaluation capacities `[6,8,12]`, 24 cells, 6 episodes/cell, `6912`
transitions; total `21888`; optimizer steps `80`; bootstrap `250`; CPU/process
`2/2`; spawned workers; all OMP/MKL/OPENBLAS/NUMEXPR and Torch intra-op
threads `1`; native backend `ContinuousRosterToyBatch_CPU_CPP_required`; no
Python fallback; aggregate RSS <= `2147483648`; wall clock <= `1200s`; no
search, nested rollout, replanning, retry, rescue, extra root, coefficient
sweep, margin change, or seed search.

Seeds are exactly: initialization `10541000`; Phase-A ledger/action/gradient
`10542000/10543000/10544000`; Phase-B `10545000/10546000/10547000`;
evaluation ledger/process/action `10548000/10549000/10550000`; bootstrap
`10551053`; nonformal offset `900000`. These are disjoint from G52.

Static gate must bind the g40 entropy callable and g19 coefficient authority,
initial zero `log_std`, finite synthetic entropy and raw gradient support
exactly `[policy.log_std]`, one coefficient call per pass in both builders, no
coefficient read in construction/collection/evaluation/result selection, no
baseline/G52 dependency, exact anchors, native backend, counts, resources, and
fresh roots. The first real common batch must prove byte equality of model,
masks, RNG, actor metadata, Adam state, stored trajectory/replay/
old-logprob/target/centered/normalized/policy gradients, raw entropy scalar/
gradient; null scaled gradient finite and bytewise zero; reference scaled
gradient finite, nonzero only on `policy.log_std`, positive norm; coefficient
is the sole graph delta; post-step actor or Adam state differs. Define
`q_H=0` if both norms are zero, otherwise
`norm64(g_ref-g_null)/max(norm64(g_ref),norm64(g_null))`; nonfinite is invalid;
activation requires `q_H>0`.

Runner phases are `train,evaluate,analyze,exercise,readiness-smoke,
readiness-train,readiness-validate,readiness-reload,readiness-evaluate,
readiness-analyze`. Formal CLI must fail closed. Readiness is proof-only with
zero scientific roots/transitions/optimizer/bootstrap and cannot initialize
nonformal. Positive artifacts are `train_manifest.json`,
`evaluation_manifest.json`, `analysis_result.json`, and final common/exact-zero
checkpoints; transient worker payloads must be removed. Implement strict
schemas, digests, reload/tamper guards, native worker/thread/resource checks,
first-batch certificate, later on-policy pairing, transition formula, branch
isolation, fresh-root, and predecessor-immutability tests.

## Branches, claims, and external review

Branch precedence is:

1. `INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53`
2. `NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53_EXERCISE_COMPLETE`

Branch 2 requires operational/source/pairing/G52-isolation/activation validity
and exact completion; it sets `scientific_branch_selected=false` and
`terminal_for_registered_treatment_if_formal=false`. Any invalid or
operational failure ranks neither arm and authorizes no retry/rescue. The five
claim-bearing branches are frozen future witnesses only and cannot be selected
by this one-root run. With >=3 roots only, apply the stated access floors and
UCB/LCB rules; this run is conditional and cannot generalize across training
roots. Do not claim entropy-code deletion, necessity, optimal coefficient,
directed exploration, centering/reset attribution, or broad MARL/deployment
effects; the zero arm remains stochastic.

External-Pro preview is `NOT_MATERIAL`. After a valid result, Root supplies
the first-bearing publication commit out-of-band to CM, publishes exact
accepted evidence, allocates one new visible G53 direction session, records
its conversation ID, requests science-only convergence, waits for natural
completion without Answer-now/Continue/Retry/Stop controls, archives and
pushes the review, then obtains same-direction EM intake. No Pro session is
allocated before a valid published result.
