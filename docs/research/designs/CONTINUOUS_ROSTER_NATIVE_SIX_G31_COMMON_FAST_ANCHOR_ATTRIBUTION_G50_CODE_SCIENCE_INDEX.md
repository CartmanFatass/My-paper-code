# G50 Common Fast-Anchor Attribution Code–Science Index

## Acceptance boundary

```text
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_P0
schema_version=2
design_disposition=CONTRACT_IDENTIFIED_B
result_contract_disposition=RESULT_CONTRACT_IDENTIFIED
design_stage_commit=b673032361b36dfc5531a06f4a8a37ce0e2c7b62
result_contract_stage_commit=22df8091c9f0cbd129f1473862186ce84bcb712a
alignment_disposition=ALIGNED
aligned_implementation_commit=b8290699f5c10c593bbc21a6666c17950fae84d3
alignment_stage_commit=4df41063d077ace7e0c9212e0cbadbf56e1be4b7
compute_authority=zero_in_this_alignment_binding_assignment
next_boundary=OPS_FRESH_SAME_SOURCE_NONFORMAL_PREFLIGHT
```

This package implements the frozen G50 result contract only. It does not run or
interpret a nonformal or formal experiment. Existing G40, G41, G48, and G49
files are read-only authorities.

## Owned paths

| Role | Path |
|---|---|
| Algorithm and evidence | `ha_ctse_process/continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py` |
| Result-bearing runner | `scripts/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50.py` |
| Focused algorithm proof | `tests/ha_ctse_process_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_test.py` |
| Focused runner proof | `tests/run_continuous_roster_native_six_g31_common_fast_anchor_attribution_g50_test.py` |
| Traceability and acceptance | this file |

## Scientific identities

| Frozen assertion | Implementation |
|---|---|
| Reference arm | `REFERENCE_ARM=FAST_ANCHOR_THEN_SINGLE_IMMEDIATE` |
| Null arm | `NULL_ARM=SINGLE_IMMEDIATE_FROM_INITIALIZATION` |
| Phase-A authority | `PHASE_A_OBJECTIVE_CONTRACT_ID=G40_COMMON_NATIVE6_FAST_ANCHOR_V1`, source `97a8b237e0cec6c2713dd2a710d324040fa3dfc2` |
| Phase-A interpretation | `B_COMPLETE_HISTORICAL_FAST_ANCHOR_PACKAGE` |
| Phase-B authority | G49 source `8ecb01fd3ac0debf1b792e4e51293e07974d633b`, aligned implementation `9edddc845d88191bbfbd6c2ec779551edbbcb78a`, stage `b56288597c6c91f784fb5f0fcc36ec5ef92de452` |
| Phase-B accepted branch | `DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49` |
| Historical anchor use | objective authority only; G50 initializes both arms freshly from the G50 initialization seed |

## Phase A: complete historical graph and isolated treatment

`make_phase_A_models` creates one exact `G40NativeSixPolicy` initialization and
two deep, storage-disjoint arm clones. `make_phase_A_optimizers` constructs one
Adam per arm over `actor_credit_parameters()` in its exact order: native-six
actor, `log_std`, and every shared two-output `credit_baselines` parameter.
`phase_A_boundary_audit` reconstructs model bytes, buffers, names, masks,
optimizer order, hyperparameters, empty Adam state, and disjoint storage.

The reference actor credit in `optimize_phase_A_update` is the historical G40
PPO gradient driven by

```text
normalize_advantage(r_t - stopgrad(b_I_old(xi_t)))
```

computed once from the complete stored trajectory before both persistent PPO
passes. The null actor credit is the exact G49 float64 population-centered/RMS
normalized `r_t` route. It has exactly one normalization instance and no
baseline read into its advantage, actor gradient, action/log-probability,
checkpoint, evaluation, or result selection. `NULL_READ_CERTIFICATE` binds all
six counts to zero.

Both arms retain the immediate-baseline module and receive the same
reference-owned shadow target, baseline forward, `VALUE_COEFFICIENT` MSE
gradient, parameter order, and Adam exposure. Both arm plans are built and
validated before the fixed reference-then-null optimizer order on every pass.
The code requires baseline loss bytes, baseline parameter-gradient bytes,
baseline state bytes, and baseline-only Adam state bytes to remain equal.
Common entropy is added exactly once to each actor gradient. On the forced
first batch its gradient bytes must be equal. No slow-critic or successor
baseline optimizer step exists; `pre_common_gradient_audit` supplies their
zero-step liveness evidence and restores masks.

`phase_A_order_swap_guard` prepares both arm plans in forward and reverse
inspection order without an optimizer step. It reconstructs plan digests and
requires unchanged model bytes, optimizer state, gradient slots, and torch RNG.

## Activation and liveness

`phase_A_activation` uses only the reference-owned pre-update model and
trajectory:

```text
q_A = 0                                      if ||g_F||=||g_I||=0
q_A = ||g_F-g_I|| / max(||g_F||,||g_I||)    otherwise
INVALID                                      for nonfinite rows
active iff q_A > 1e-6
```

Entropy and baseline-loss gradients are excluded from `g_F` and `g_I`.
`_actor_group_evidence` reconstructs every registered G40 actor group, requires
both objective rows finite, and requires each group live in at least one row
with strict norm `>1e-12`. Equality at `1e-6` is inactive; equality at `1e-12`
is not live. `build_phase_A_conclusion_evidence` requires one active pass for
the nonformal replicate and for every formal replicate `0|1|2`; the null arm
contributes zero activation evidence.

## Phase boundary and Phase B

`project_phase_B_models` creates a new `G50PhaseBProjection` for each arm,
copies only actor/`log_std` state, and physically deletes:

- `credit_baselines` and all baseline state;
- `slow_critic`;
- `policy.critic`;
- `policy.delayed_residual`;
- every Phase-A optimizer object and state.

The projection consumes zero RNG and zero optimizer steps. Its disposal
certificate reconstructs deleted modules/state keys and actor byte
preservation. `make_phase_B_optimizers` then creates fresh, empty,
storage-disjoint Adam instances in the exact actor/`log_std` order.

`optimize_phase_B_update` uses G49 `_single_immediate_target`,
`_normalize_single`, `_single_probe`, and `_apply_pass` for both arms. It
therefore retains one `x_I=r_t` channel, one independent population RMS
normalization, one PPO channel gradient, common entropy once, two persistent
passes, and one actor Adam step per pass. No second immediate channel,
realized-successor channel, baseline, or slow critic is present.

## Counts, seeds, and runtime

`static_configuration_certificate` independently reconstructs:

| Inventory | Nonformal | Formal |
|---|---:|---:|
| Replicates | 1 | 3 |
| Phase-A updates per arm | 10 | 100 |
| Phase-B updates per arm | 10 | 100 |
| PPO passes | 2 | 2 |
| Training transitions | 15,360 | 460,800 |
| Evaluation transitions | 6,912 | 165,888 |
| Total real transitions | 22,272 | 626,688 |
| Optimizer steps | 80 | 2,400 |
| Evaluation cells | 24 | 72 |
| Episodes per cell | 6 | 48 |
| Bootstrap draws | 250 | 10,000 |

The seed bases are `10501000` through `10510000` in the registered order and
bootstrap `10511050`. Formal replicate `r` adds `r` once to every
non-bootstrap seed. Nonformal adds `900000` once to every seed, including
bootstrap. `H=48`, `K_search=0`, hypothetical trajectories/transitions are
zero, and nested rollout and replanning are false.

Formal runtime requires `ContinuousRosterToyBatch_CPU_CPP`, no Python fallback,
CPU budget 2, process workers 2, spawn, deterministic preassigned-index merge,
all OMP/MKL/OpenBLAS/NumExpr worker limits 1, and torch intra-op 1.

## Evaluation, confidence, and selector

The runner privately reuses the accepted G48 evaluation machinery after
binding only G50 identities, checkpoint loader, source controls, seeds, and
validators. It evaluates final Phase-B checkpoints at capacities `6|8|12` in
this order:

1. `FINAL_FIXED_DETERMINISTIC`
2. `FINAL_FIXED_STOCHASTIC`
3. `FINAL_RANDOM_DETERMINISTIC`
4. `FINAL_RANDOM_STOCHASTIC`

Formal random cells retain `LRJT|LJRT|JLRT=16|16|16`; nonformal cells retain
`2|2|2`. Episode IDs, fixed/random mates, deterministic/stochastic mates,
source/lifecycle ledgers, reward, action noise, and evaluation noise remain
paired. Evaluation has zero optimizer steps.

The single G48 paired hierarchical percentile plan resamples replicate blocks,
then whole episode IDs within replicate/capacity, and retains both arms and all
mates. Capacities have equal weight. It never resamples members, primitive
steps, events, phases, channels, or action factors independently. Quantiles are
linear `0.025|0.50|0.975`.

The primary contrast and every component are reference minus null. The margin
is `0.05`. Absolute gates are `0.90` deterministic utility, `0.80` pooled
stochastic utility, `0.85` event/process and minimum replicate mean, and
`-0.05` random-minus-fixed transport. Floor equalities pass; UCB `0.05`
passes noninferiority; primary LCB `0.05` and capacity LCB `0` do not establish
strict advantage.

`select_g50_result_branch` applies exactly:

1. `INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50`
2. `SOURCE_OR_REFERENCE_ACCESS_FAILURE_G50`
3. `FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50`
4. `COMMON_FAST_ANCHOR_FINITE_BUDGET_ADVANTAGE_G50`
5. `MIXED_UNDERPOWERED_COMMON_FAST_ANCHOR_ATTRIBUTION_G50`

Priority 2 is selected for `source_valid=false` or
`reference_access_pass=false`. `reference_access_confident_fail` remains
diagnostic evidence only; it cannot replace the absolute reference-access
predicate. This priority precedes favorable stored comparative booleans.

## Artifacts and reload

Terminal artifacts are `train_manifest.json`, `evaluation_manifest.json`,
`analysis_result.json`, and final-only `replicate × arm` checkpoints. Formal
inventory is exactly six checkpoints. `build_final_checkpoint` and
`validate_final_checkpoint` use an exact top-level schema and bind source,
phase identities, completed updates, configuration, seeds, actor state,
`log_std`, Phase-B Adam state, disposal certificate, G49 route certificate,
and source/process/lifecycle provenance. Extra fields, intermediate kinds, and
baseline/critic/delayed/successor residue fail closed. Reload constructs a
fresh actor-only graph at the requested capacity and strictly loads the
canonical state.

Runner validators recompute configuration, source controls, activation,
checkpoint names and SHA-256 values, checkpoint schemas, cell inventory,
episode counts, zero evaluation steps, and train/evaluation manifest digests.
The analyzer rebuilds access, the shared bootstrap plan, comparative CIs,
branch booleans, and the first match; stored favorable labels are not trusted.

## Formal admission

```text
authorization_token=CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_AUTHORIZATION_V1
alignment_audit_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_CODE_SCIENCE_ALIGNMENT_AUDIT
nonformal_completion_branch=NONFORMAL_CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_EXERCISE_COMPLETE
```

The independent correction-recheck-v2 binds
`ALIGNED_IMPLEMENTATION_COMMIT=b8290699f5c10c593bbc21a6666c17950fae84d3`
and
`ALIGNMENT_STAGE_COMMIT=4df41063d077ace7e0c9212e0cbadbf56e1be4b7`.
Formal admission still fails before runtime configuration, worker creation,
environment collection, or run-root writes unless the CLI supplies those exact
lowercase identities, the token, `ALIGNED`, same-source valid nonformal
manifests/digests/inventory/branch, historical G40 objective authority, G49
authority, wall-clock projection, fresh root, C++ backend, and CPU/process/thread
settings.

## Focused evidence

The source test covers frozen identities and counts, seed offsets, zero and
strict activation cases, complete G40 Phase-A graph/optimizer inventory,
physical Phase-A deletion, fresh Phase-B Adam, exact checkpoint schema/reload,
residue tampering, activation reconstruction, order-swap implementation, and
the null zero-read certificate.

The runner test covers nonformal/formal inventories, source-authority use,
five first-match witnesses, the non-confident absolute reference-access failure
guard and its precedence over favorable comparisons, exact alignment binding
and fail-closed missing-preflight admission, exact six checkpoint names,
paired whole-episode bootstrap indices,
CPU/spawn/thread controls, all six readiness interfaces, and immutable
token/predecessor bindings.

Execution readiness is candidate-bound and formal=false. Its six phases use
only static certificates, synthetic episode/index records, synthetic branch
witnesses, and a real two-process spawn proof over identical static payloads.
`_run_distinct_readiness_workers` assigns one proof task to each of two
dedicated spawned processes and holds both at a release barrier before either
payload is produced, so a pool cannot satisfy the proof by reusing one worker.
They consume zero scientific real transitions, zero optimizer steps, and zero
scientific bootstrap draws.
