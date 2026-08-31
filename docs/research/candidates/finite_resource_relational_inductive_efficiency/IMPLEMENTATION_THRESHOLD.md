# FRRIE implementation threshold

Status: `INFERENCE_BLOCKED`

The first object is fixed-roster per episode with adaptation-free held-out-size evaluation. It does
not exercise join, leave, rejoin, replacement, or within-episode churn and cannot support those
claims.

## Single learned host

Use a fresh FRRIE-owned `RIDGEGATE-2Z/RSCF` object. No historical SGSP seed, checkpoint,
update-154 state, result, threshold, or run-control state transfers.

Exactly two learned arms exist:

- `PHY_TRUST`: projects the relational residual `beta` to `[-0.15, 0.15]`;
- `EDGE_FLEX`: projects the same residual to `[-1.50, 1.50]`.

`UNIFORM_LEGAL` is evaluation-only. Both learned arms use the same 35,513-parameter actor/critic and

\[
\omega_{ab}(n)=K^0_{ab}(n)\exp(\beta_{ab,0}+\beta_{ab,1}v(n)).
\]

Only the projection box differs. Inclusion is literal and `beta=0.60` is the strict-capacity
witness. Both arms receive the same 22-field entity observations, public physical/role relations,
messages, masks, recurrent history, and tapes. Entity/slot identity, arm label, hidden/future
outcomes, reward decomposition, and result-derived features are forbidden.

## Work, cells, and endpoint

Freeze bit-identical initialization, minibatch order, potential outcomes, 512 updates, 64 episodes
per update split over train `N={9,15}`, one backward/Adam step per update, and 256 evaluations per
cell. Each seed block is one inferential unit. The candidate panel uses exactly 24 fresh
blocks; fewer, missing, filtered, or replacement blocks invalidate it. Update 512 is the sole
evaluable checkpoint.

For each 16-pair roster/update schedule and role, one side-free base-slot draw is shared across the
pair: side 0 uses `b` and side 1 uses `11-b`. Each side then makes its own independent uniform
role-local index draw at an address that includes side (encoded by its episode coordinate). Thus
`role_local_entity_shared_across_pair_sides=false` and
`role_local_entity_draws_independent_across_pair_sides=true`; equality may occur by chance. Both
learned arms share the selected origin at the same episode coordinate. Forcing one entity across
pair sides is a different trainer and is forbidden.

Evaluate adaptation-free at held-out `N={6,21}` and under symmetric
`SEMANTIC_COLUMN_ROTATE` while simulator physics, observations, reward, and tapes stay fixed. The
native endpoint is

\[
J=0.65(D_W+D_E)/6+0.25\min(D_W,D_E)/3+0.10(1-\mathrm{WASTE}).
\]

Primary candidate fixed-work estimand is the minimum held-out `PHY_TRUST - EDGE_FLEX` native-return
contrast at update 512. A future valid simultaneous method must bound it from the two separately
inferred held-out means rather than an observed pooled minimum.
Work-to-threshold, first crossing, learning-curve, update-saving, sample-saving, and compute-saving
estimands are absent from this first object. Any such claim requires a separately frozen checkpoint
population, censoring law, multiplicity family, and result map before another checkpoint is
evaluated.

Match environment slots, learned decisions, backward calls, parameter bytes, FLOPs, workers,
threads, native width, dtype, checkpoint I/O, and evaluation opportunities. CPU/native FP32 and
float64 reductions are fixed; no GPU or network. Fresh resource preflight is required before result
activity.

Detection, uplink, base, and action tapes use the exact FP32 lattice law
`U=TOP24(AddressedRNG.block(address,0))/2^24`, with support
`{0,2^-24,...,1-2^-24}`. No 53-bit-to-FP32 rounding, clamp, retry, or endpoint folding is allowed;
an exact wider-register representation is harmless only when its binary32 store has the formula's
literal bits. Integer rejection draws and raw-byte initialization are unchanged. This mapping and
its strict `U<p` boundary are part of the DGP, not an implementation option.

## Output-disconnected controls

- FRRIE-owned CCIC arity-three typed-wedge compiler fixture;
- exact `Fraction` EGRCR pair-aware conditional-Q/Rao--Blackwell equality fixture;
- immutable intact/reassociated raw-value rows whose opposite labels force balanced accuracy `1/2`;
- FRRIE-owned VQFP LR, `MARG0`, marginal-heap, utility, MASS/MASS-P, and half-cycle-reassociation
  fixtures.

No FRRIE file imports historical VQFP packages or native libraries. Historical coefficients,
partial panels, retained operations, and result polarity do not enter fixtures.

## New implementation surface

```text
experiments/candidates/finite_resource_relational_inductive_efficiency/
  contracts/core.py
  contracts/ccic_control.py
  contracts/egrcr_control.py
  contracts/vqfp_controls.py
  controls/raw_value.py
  rng.py
  tapes.py
  host.py
  arms.py
  policy.py
  training.py
  state_codec.py
  work.py
  checkpoint.py
  native_adapter.py
  native/native_abi.py
  native/frrie_ridgegate2z_external.cpp
  preflight.py
  runner.py
  orchestration.py
  evaluator.py
  analysis.py
  lifecycle.py
  fixtures/*.json
  cli.py
  __main__.py

tests/experiments/candidates/finite_resource_relational_inductive_efficiency/
  test_contract_and_containment.py
  test_native_host_and_endpoint.py
  test_pair_work_and_rng.py
  test_policy_training.py
  test_work_v2.py
  test_checkpoint_resume.py
  test_native_step_snapshot.py
  test_native_adapter_and_preflight.py
  test_orchestration_v2.py
  test_controls.py
  test_analysis_and_lifecycle.py
  test_dependency_firewall.py
```

Key API now includes v2 manifest validation, package-owned external-action native admission,
reset/observe/step/snapshot/restore, factual RSCF origins and detached suffixes, the direct FP32
uniform mapping, bit-identical pair initialization, paired Torch updates, corrected one-step
intact/shadow probabilities, deterministic per-block checkpoint serialize/restore, all analytic
fixtures, direct v2 preflight, blocked orchestration, and complete-panel candidate-quantity
analysis. The physical factual replay and corrected work receipts below are now part of that
implemented structural surface.

Current scaffold schemas are `FRRIE_MANIFEST_V1`, `FRRIE_CHECKPOINT_V1`,
`FRRIE_SEALED_SEED_PACKET_V1`, `FRRIE_COMPLETE_PANEL_RESULT_V1`, and `FRRIE_TERMINAL_V1`. They are
TEST/non-result surfaces and are superseded for any future production work by `FRRIE_MANIFEST_V2`,
`FRRIE_CHECKPOINT_V2`, `FRRIE_SEALED_SEED_PACKET_V2`, `FRRIE_COMPLETE_PANEL_RESULT_V2`,
`FRRIE_COMPLETE_PANEL_ANALYSIS_V2`, `FRRIE_TERMINAL_V2`, and
`FRRIE_NATIVE_STEP_ABI_V2_FP32`. V1 cannot be upgraded or accepted by production. The v1
manifest binds host/source identities, arms, cells, dtype/native width, workers/threads, updates,
checkpoints, fresh roots, competence/threshold specs, work parity, fixture identities, and resource
ceilings. The blocked v2 revision must additionally bind the exact structures in
`INFERENCE_AND_EXECUTION_FREEZE.md`, including the fresh DGP/RSCF update law, exactly 24 direct seed
roots, checkpoint `[512]`, eight numeric margins, ordered 28-member candidate estimands and explicit
blocked-inference record,
intact/shadow policy probabilities, state layout, planned and cumulative work/RNG receipts,
the `TOP24/2^24` mapping, three physical factual replays and seven nonfactual continuations per
episode, firewalls, and resource ceilings. It must not add a non-RNG hash, authentication,
identity, lease, or approval gate.

## CLI and non-result acceptance

```text
python -m experiments.candidates.finite_resource_relational_inductive_efficiency describe
python -m experiments.candidates.finite_resource_relational_inductive_efficiency check --manifest PATH --output PATH
python -m experiments.candidates.finite_resource_relational_inductive_efficiency run --manifest PATH --output-root PATH [--resume]
```

Only `describe`, value-blind preflight, and focused tests are permitted; the result command is not
authorized here. No defaults for seeds or resources. The checkpoint and scientific margins are
now frozen in `INFERENCE_AND_EXECUTION_FREEZE.md`; a v2 manifest must carry them literally together
with `ready=false` and the inference blocker.
Invalid contract,
missing native backend, failed preflight, resume mismatch, and technical failure use distinct
nonzero exits and expose no partial scientific values.

Tests cover literal containment, native shapes/endpoint/no Python fallback, external-action
snapshot isolation, bitwise pair initialization, RSCF update and optimizer resume, arm-independent
addressed RNG, per-block checkpoint/resume, corrected shadow TV, all analytic controls, complete-
only analysis, paired atomic fresh roots, dependency firewalls, and a bounded explicit v2
`TEST_ONLY` chain. It also covers the side-free base-slot/side-specific role-local selector law and
requires evaluator plus standalone analysis to reopen and restore all 24 exact checkpoint files
before asserting byte revalidation. The current integrated suite reported `152 passed, 1 skipped`;
a separate bounded Windows-native smoke passed all eight native tests. The temporary native
artifact was removed, and no production or scientific result command ran.

Every selected W/E/R origin requires a physical factual-label restore and closed-loop suffix replay
on the same immutable model and stored future tapes. Only after direct per-slot native-state,
observation/mask, hidden/probability, action, terminal-primitive, and FP32-return equality may the
observed `J_base` be reused as the factual Q entry. Hashes or metadata existence do not establish
this fact. The retained current factual action is stepped at the post-GRU/pretransition origin;
actor recurrence resumes only at `t+1`, so the origin actor computation is not repeated or charged
again. A mismatch is structural `INVALID`, with no target, update, retry, or partial value.

Per learned arm and seed block, this adds `638,976` factual-replay environment slots, `540,672`
future actor steps, and `6,488,064` future policy decisions to the seven nonfactual continuations.
The required checkpoint and final environment-slot totals are `2,523,136` and `2,547,712`; all
suffix future actor steps are `1,802,240`, all suffix future policy decisions are `21,626,880`,
and all learned decisions are `26,741,760`.
Shadow audit remains zero native environment slots, `6,144` actor steps, and `82,944` policy
decisions. Conventional static FLOPs are `1,958,344,320,512` at checkpoint and
`1,979,786,229,248` at complete panel per arm/block. Across 24 blocks each learned arm has
`61,145,088` final environment slots, `43,253,760` suffix actor steps, `641,802,240` learned
decisions, `12,288` backward calls, `12,288` Adam steps, `49,152` evaluation opportunities, and
`47,514,869,501,952` conventional static FLOPs. The earlier cached-only
`1,884,160`/`1,908,736` totals are withdrawn.
The implementation and tests now match this ledger; none of these work facts is scientific
polarity.

This structural acceptance is not production readiness. Result-process resource observations and
the runtime monitor admission remain unexecuted under
`RESOURCE_RUNTIME_CONFORMANCE_UNOBSERVED`, and no package-native artifact is retained. Both the
technical preflight conditions and the independent inference blocker keep `ready=false`.

## Frozen estimands and blocked inference

The exact candidate estimands, 12 support slacks, 16 target/competence members, canonical order,
fresh margins, and intended comparison semantics are defined only in
`INFERENCE_AND_EXECUTION_FREEZE.md`. No alpha allocation, critical value, or confidence-bound method
is active. Student-`t` is rejected for the finite addressed-root law, and distribution-free bounds
cannot establish the registered seen equivalence or ordinary cut-insensitivity at 24 blocks.

V2 preflight must return `SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS`, `ready=false`, and
perform no result activity. The prospective repair must choose before activity among more blocks,
different margins, a median/majority-block estimand, or a one-sided efficacy-only mean object. A
literal 24-root panel may be reported only as a finite descriptive population without confidence,
generalization, or direction polarity. No replacement seed, second budget, altered threshold, or
post-result rescue is permitted.

Root prospectively narrows this first object to a tight-versus-wide projection/optimizer-package
effect. Same-host compiler absorption and semantic/relational-mechanism polarity are removed, not
waived or treated as passed. A competent same-information compiler is a separate successor object.

After a valid inference repair, the maximum claim is a finite-budget tight-versus-wide
projection/optimizer-package effect on the frozen fixed-roster and held-out-size cells only. At the
current blocker, no sampled-root population claim is available.

## Evidence

- `DIRECTION.md`
- `INFERENCE_AND_EXECUTION_FREEZE.md`
- `docs/research/candidates/semantic_graphon_shared_policy/DIRECTION.md`
- `docs/research/candidates/covariance_calibrated_information_clock/DIRECTION.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/DIRECTION.md`
- `docs/research/candidates/voronoi_quadrature_field_policy/DIRECTION.md`
