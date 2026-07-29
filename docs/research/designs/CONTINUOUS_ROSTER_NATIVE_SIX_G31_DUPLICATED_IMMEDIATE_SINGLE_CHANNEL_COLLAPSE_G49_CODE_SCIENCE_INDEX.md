# G49 Duplicated-Immediate Single-Channel Collapse Code–Science Index

## Frozen boundary

```text
algorithm_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49
source_id=CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49_P0
design_round=20260729_g48_duplicated_immediate_single_channel_collapse_design_assertion_audit
design_stage_commit=fc8288b53401cea1642110994305272905e56c5f
design_disposition=CONTINUE
accepted_G48_formal_source_commit=4abbee66d43ffd592d65624121121bc0109882ab
accepted_G48_aligned_implementation_commit=d96f8f29367b55b5ea655b984631d6064877e237
accepted_G48_alignment_stage_commit=617414f9a175f044eecfbfec4e4b170c6990b47f
accepted_G48_formal_branch=DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48
aligned_G49_implementation_commit=9edddc845d88191bbfbd6c2ec779551edbbcb78a
G49_alignment_recheck_round=20260729_g48_duplicated_immediate_single_channel_collapse_code_science_alignment_correction_recheck
G49_alignment_stage_commit=b56288597c6c91f784fb5f0fcc36ec5ef92de452
G49_alignment_disposition=ALIGNED
reference_arm=NATIVE6_G31_DUPLICATED_IMMEDIATE
reduced_arm=NATIVE6_G31_SINGLE_IMMEDIATE
result_type=exact_functional_and_optimizer_equivalence_not_statistical_noninferiority
formal_compute_started=false
nonformal_compute_started=false
scientific_iteration_cost=zero
```

G49 changes one thing only: it removes the second copy of the immediate target and the entire second normalization/loss/backward/gradient/diagnostic package. It does not change actor inputs, parameters, source, reward, environment interaction, action distribution, entropy, optimizer, checkpoint selection, or accepted G48 provenance.

## Realized equations

The reference executes the accepted G48 route without substitution:

\[
z_{I1}=\operatorname{RMSNorm}(r_t),\qquad
z_{I2}=\operatorname{RMSNorm}(r_t),
\]

\[
v_{\mathrm{DUP}}=0.5(g_{I1}+g_{I2}),\qquad
d_{\mathrm{DUP}}=v_{\mathrm{DUP}}+g_E.
\]

The reduced route materializes and normalizes one row and differentiates one policy loss:

\[
z_I=\operatorname{RMSNorm}(r_t),\qquad
v_{\mathrm{SINGLE}}=g_I,\qquad
d_{\mathrm{SINGLE}}=g_I+g_E.
\]

`_normalize_single` uses exactly the accepted G44 order and dtype: detach, cast to float64, `mean`, subtract, `square().sum()`, `torch.sqrt(sum/384)`, exact-zero scale to zeros, divide otherwise, then cast centered and normalized rows to the input dtype. There is no epsilon, fused reordering, row filter, active-count weighting, running statistic, or second normalization object.

The implementation accepts the collapse only after observing, on each of both PPO passes, actual byte equality of both reference targets, centered rows, scales, normalized rows, policy losses, channel gradients, the actual `0.5*(g1+g2)` result, entropy gradients, assigned gradients, post-step actor and `log_std`, Adam counters/`exp_avg`/`exp_avg_sq`, and deterministic action/log-probability traces.

## Five-path realization

| Path | Authority |
|---|---|
| `ha_ctse_process/continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49.py` | Projection, genuinely single reduced route, exact bytewise pass plan, static factorization certificate, update evidence, final checkpoint projection and validators. |
| `scripts/run_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49.py` | One-shared-batch proof interface, fail-closed formal admission, final-only artifact lifecycle, two-process deterministic proof and six readiness entries. |
| `tests/ha_ctse_process_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49_test.py` | Focused source invariants, actual two-loss-to-one-loss equality, tamper rejection and exception serialization. |
| `tests/run_continuous_roster_native_six_g31_duplicated_immediate_single_channel_collapse_g49_test.py` | Runner closure, final-only reload, two-process proof, backend/configuration/formal gates and artifact tamper rejection. |
| `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49_CODE_SCIENCE_INDEX.md` | This exact contract-to-code-to-test binding. |

No G48 source, runner, test, index, runtime, review, CDC, `CURRENT_WORK`, or workflow path is part of the implementation diff.

## Contract mapping

| Frozen assertion | Source interface and primitive evidence | Revalidation and focused rejection |
|---|---|---|
| Accepted G48 duplicated-immediate branch is the only predecessor | `project_g49_arms`, provenance constants, `reconstruct_static_certificate` | `validate_static_certificate`; tests assert all three G48 source/stage identities and accepted branch. |
| Branch start is bitwise paired, storage-disjoint, RNG-free, with empty identical Adam | `project_g49_arms`, `make_g49_optimizers`, `branch_boundary_audit` | Static validator reconstructs arm order, actor state/name/order, Adam inventory/hyperparameters/state, storage and baseline absence. |
| Reduced route owns exactly one target and one normalization | `_single_immediate_target`, `_normalize_single`, `SingleChannelNormalization` | Exact-key `validate_single_normalization_record`; `_reduced_function_dependency_certificate` reports every removed count as zero. |
| Reduced artifact has no hidden second/dummy/compatibility residue | `_reduced_pass_record`, `_REDUCED_PASS_KEYS`, `_SINGLE_NORMALIZATION_KEYS`, `_SINGLE_GRADIENT_EVIDENCE_KEYS`, `_GRADIENT_ROW_KEYS`, `_REDUCED_CHECKPOINT_KEYS`, reduced final checkpoint schema | `_validate_reduced_pass` and `validate_checkpoint_pair` require exact outer key sets; target and gradient validators require exact nested key sets; `validate_reduced_schema` recursively rejects duplicated-immediate, second-channel, equal-mean, averaging, dummy and compatibility identities in keys and free-form string values. Focused update and artifact-reload tamper guards inject the innocuous `legacy` key with `accepted_G48_duplicated_immediate` and `immediate_2` values and fail closed. |
| Actual reference target/normalization bytes equal the single path | `_normalization_equivalence` compares the one reduced row with both accepted G48 rows | `validate_update_evidence` requires every equality observation; focused tamper flips an equality and fails closed. |
| Actual reference `0.5*(g1+g2)` bytes equal one gradient | `_duplicate_probe` calls the inherited literal equal-mean function; `_single_probe` performs one `autograd.grad`; `_pass_equivalence` compares tensors | Every pass validator requires both channel rows, the actual combined row and the single row to be byte-equal. No symbolic-equality flag is accepted alone. |
| Entropy is common and added exactly once | Both probes form the unchanged entropy objective once; reference uses inherited add, reduced uses one tensor addition | Per-pass equality binds entropy and assigned-gradient digests; schemas require one entropy addition. |
| Removed computation has no hidden side effect | Plan snapshots model, optimizer, `.grad` slots and torch RNG around both plans; static certificate binds zero RNG/hook/buffer/stat/scaling/optimizer/checkpoint counts | Any snapshot change fails before either optimizer step for that pass. |
| Both plans precede either step and reference runs first | `optimize_duplicated_immediate_single_channel_update` builds both probes, validates all equality, then calls `_apply_pass` in `ARMS` order | Pass records bind plan-before-step and branch order. `order_swap_guard` executes zero steps and proves inspection-order invariance. |
| Two persistent PPO passes retain exact Adam equality | Pass loop recomputes both plans on the equal current state after pass 1; `_apply_pass` retains accepted Adam | `_post_pass_equivalence` reconstructs state, Adam and actor traces after each pass; update validator requires all exact. |
| One shared 8×48 stored trajectory, no duplicate interaction | Runner collects one `AnchoredRosterTrajectory`, serializes it as a read-only proof input, and sends the same object to both paths | Manifest binds one batch and 384 transitions; process proof loads the same stored trajectory and reports `duplicated_environment_interaction=false`. |
| Inductive equality and `D_SC=0` | Per-pass assigned-gradient/model/Adam/trace equality plus shared source trace | `validate_update_evidence` reconstructs all six registered `D_SC` components and requires each and the maximum to be exactly zero. |
| Full checkpoint schemas intentionally differ | `build_final_checkpoints` retains the accepted two-channel reference schema and a one-channel reduced schema | `validate_checkpoint_pair` compares only the canonical actor/`log_std`/Adam/update/provenance/final-only projection and rejects reduced residue or ordinal drift. |
| Backend and process determinism | Runner requires `ContinuousRosterToyBatch_CPU_CPP`, Python fallback false, fixed worker indexes and single-thread controls | `prove_two_process_equivalence` requires two distinct spawn workers and exact model/Adam/evidence/checkpoint semantic payload equality; `_attach_readiness_process_proof` permits the readiness-complete marker only after that report passes. |
| No statistical result or unauthorized formal entry | Configuration fixes bootstrap zero, one batch, 384 transitions, two passes, `formal_statistical_run=false`; `ALIGNED_IMPLEMENTATION_COMMIT` and `ALIGNMENT_STAGE_COMMIT` bind the exact independently aligned G49 identities | `_formal_admission_errors` reconstructs exact alignment, same-source validated preflight and authorization-token predicates before trajectory collection; focused tests reject missing preflight, wrong aligned source, wrong stage and wrong token. |

## Result branches and claim ceiling

The runner uses first match:

1. `INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49`
2. `UNREGISTERED_DUPLICATED_IMMEDIATE_COUPLING_G49`
3. `DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49`
4. `NUMERICALLY_UNRESOLVED_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49`

The successful branch means only that the duplicate immediate package is structurally removable inside the exact accepted G48 route under the proven dtype/kernel, optimizer, source, horizon and actor interfaces. It makes no fresh training-sufficiency, TEAM-GAE1, optimizer-independent, arbitrary-horizon, delayed-credit, UAV, G33, recurrence, baseline or critic claim.

## Proof inventory and execution readiness

```text
accepted_branch_starts=1
shared_real_trajectory_batches=1
episodes=8
H=48
real_transitions=384
PPO_passes_per_arm=2
actor_optimizer_steps_per_arm=2
bootstrap_resamples=0
formal_statistical_run=false
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
wall_clock_cap_seconds=1200
```

The runner changes an execution entry and artifact schema, so technical acceptance requires all six clean-candidate execution-readiness phases: interface smoke, bounded train exercise, artifact validation, fresh artifact reload, zero-step evaluate entry and analyze entry. The readiness package also requires a real two-process exact semantic comparison. Readiness is proof-only, `formal=false`, conclusion-bearing scientific iteration cost zero, and is not a nonformal or formal scientific run.

## Next boundary

```text
CONTINUOUS_ROSTER_NATIVE_SIX_G31_DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_COLLAPSE_G49_FORMAL_EXECUTION_INTERFACE
```

Formal execution remains closed until a fresh same-source nonformal preflight validates, the exact authorization token is supplied, and the explicit execution interface uses this bound source/stage pair.
