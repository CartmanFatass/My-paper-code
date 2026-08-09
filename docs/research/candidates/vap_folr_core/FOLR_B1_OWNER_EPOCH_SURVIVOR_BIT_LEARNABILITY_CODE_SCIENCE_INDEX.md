# FOLR-B1 owner-epoch survivor-bit learnability code/science index

This index binds the implementation of
`FOLR-B1-OWNER-EPOCH-SURVIVOR-BIT-LEARNABILITY` for
`CAND-VAP-FOLR-CORE@constructive-revision-v6`. It is an engineering locator,
not a scientific disposition. The registered result and publication commit are
filled by Code Project Manager after the sole full run.

## Frozen question and boundary

The exact host asks whether an ordinary cue writer can put a private bit into
S03, preserve it through one real typed roster replacement, and use it for
held-out terminal reward. Three matched backends are compared:
`S03_KEEP`, `COMPLETE_RESET`, and `ONE_BIT_OWNER_EPOCH_LATCH`. A1 payload
transplantation, constructed sensitivity weights, hand-aligned heads, critic,
auxiliary loss, replay, recurrence outside the reader, sweeps, retries, rescue,
checkpoint selection, extra arms, C, and External Pro are absent.

The strongest possible result is local to the exact two-transition host and
eight-seed finite panel. It cannot establish cross-task or cross-epoch
generalization, delayed-credit correctness, coordination, sample efficiency,
typed-memory superiority, promotion, retirement, C, or formal validation.

## Critical implementation points

| Claim-bearing point | Code owner | Focused witness |
|---|---|---|
| Typed atomic `TERMINAL_LEAVE inert_q0@0` plus `JOIN inert_q1@0`; `owner_t@0` remains active | `experiments/candidates/folr_core/owner_epoch_survivor_bit_host.py` (`replacement_transaction`, `apply_replacement`) | `test_host_applies_typed_atomic_replacement_without_changing_owner_epoch`, `test_manual_or_changed_epoch_transaction_fails_closed` |
| `LifecycleRecord.high_hidden` itself is the single tensor-backed differentiable S03 authority; typed commit preserves the same owner record and carrier, choice reads that field directly, and reset clears only that field | host module (`cue_transition`, `apply_replacement`, `_require_s03`, `choice_memory`) | `test_backends_preserve_gradient_or_exactly_expire_minimal_latch`, `test_choice_reads_current_committed_s03_and_never_a_stale_activation`, `test_reward_gradient_crosses_committed_registered_s03_to_cue_encoder` |
| Positive control carries exactly raw `(owner key, epoch, bit)`, expires at terminal, and fails closed/clears itself on owner-epoch mismatch | host module (`OwnerEpochBitLatch`, `choice_memory`, `terminal_transition`) | backend test and `test_latch_fails_closed_and_expires_on_owner_epoch_mismatch` |
| All arms share parameter names/order/shapes and matched fresh initialization | `experiments/candidates/folr_core/owner_epoch_survivor_bit_learnability.py` (`SurvivorBitActor`, `train`) | `test_actor_parameter_order_shape_and_initialization_match_across_arms` |
| Environment, bit, initialization, action-sampling, and trainer RNG identities are separated; manifests are paired across arms | learnability module (`_derive_seed`, `build_frozen_manifest`) | `test_manifest_is_balanced_separated_and_paired_across_arms` |
| Each episode has two transitions/two target calls; complete choice kernel is captured before sampling; update follows the complete batch | learnability module (`_episode_batch`, `train`) | three-phase smoke and sidecar validators |
| Matched reset `b=0/b=1` kernels and uniforms are exact | learnability module (`_reset_kernel_evidence`) | `test_reset_matched_bit_kernels_are_bitwise_equal_before_sampling` |
| REINFORCE is terminal-reward-only with batch-mean baseline, gamma 1, Adam 0.003, entropy 0.01, batch 64, one update/batch | learnability module (`registered_config`, `train`) | registered config assertions and canonical train validator |
| `J`, per-bit metrics, complete curves, normalized AUC, seedwise contrasts, `Delta_S`, `Delta_L`, `G`, thresholds, and seven-branch precedence | learnability module (`analyze`, `validate_result`) | three-phase smoke and full fail-closed validator |
| CLI is wiring only and exposes `train -> evaluate -> analyze` plus read-only validators | `scripts/run_folr_b1_owner_epoch_survivor_bit_learnability.py` | CLI help/interface smoke owned by CPM readiness |

## Artifact lifecycle

`train` first writes `frozen_manifest.json`, then streams every training episode
to deterministic gzip JSONL and writes one final-only checkpoint per arm/seed.
`evaluate` reloads only those final checkpoints, performs no update or
intervention, and streams every held-out episode. Compact summaries bind every
sidecar/checkpoint by size and SHA-256. `analyze` reloads canonical summaries and
sidecars, applies the frozen decision precedence, and emits `raw_result.json`.
Technical smoke artifacts remain `technical_only=true`, use the same entries,
and are rejected by full validators.

The registered Experiment Operator receipt is not reimplemented here. Operator
execution uses the current project helper
`.agents/skills/hmasd-agile-research-development/scripts/hmasd_experiment_operator_receipt.py`.

## Registered identities

- Source commit: pending CPM freeze and push.
- Run ID: pending CPM predeclaration.
- Raw evidence: pending sole registered run.
- Result commit and public result locator: pending CPM technical acceptance.
