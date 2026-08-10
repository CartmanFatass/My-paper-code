# VSP02-B1V2 code-science index

This is the isolated source binding for
`VSP02-B1V2-LEARNED-CUE-CONDITIONED-LIFECYCLE-CONTROL`. It records
implementation evidence only. Integration, review, execution readiness, the
sole registered full, technical acceptance, result publication, scientific
intake, and successor choice remain outside this package.

```text
treatment=VSP02-B1V2-LEARNED-CUE-CONDITIONED-LIFECYCLE-CONTROL
candidate=CAND-VSP-02@adversarial-revision-v8
source=experiments/candidates/vsp_02/learned_cue_conditioned_lifecycle_control_v2.py
runner=scripts/run_vsp02_b1v2_learned_cue_conditioned_lifecycle_control.py
tests=tests/experiments/candidates/vsp_02/test_learned_cue_conditioned_lifecycle_control_v2.py
index=docs/research/candidates/vsp_02/VSP02_B1V2_CODE_SCIENCE_INDEX.md
host=VSP02-A2-PHYSICAL-LIFECYCLE-HOST-v1
immediate_runtime_dependency=experiments/candidates/vsp_02/owner_action_responsive_lifecycle.py
resource_class=B_TOY_LIGHT
pool_units=1
formal=false
learned_arms=FULL_LIFECYCLE_GRU_ACTOR_CRITIC|X_MEMORY_TABULAR_MONTE_CARLO|CUE_BLIND_GRU|CUE_SHUFFLED_GRU|CURRENT_ONLY_GRU|RAW_HISTORY_TABULAR_MEMORIZER
fixed_references=ALWAYS_RELEASE|ALWAYS_HOLD|UNIFORM_RANDOM
evaluator_only_oracle=RELEASE iff X_b=1 else HOLD
registered_seeds=VSP02-B1-20260809-S00..S04
registered_training=30 fits|30720 real episodes|640 neural Adam updates|10240 tabular sample-mean updates
registered_evaluation=2176 forced real-host episodes
rng=first eight big-endian SHA256 bytes of seed_id/stream for init|action|episode_order|cue_shuffle
terminal_precedence=TERMINAL>INTERRUPT>AUTHORIZED_RELEASE>NATURAL>HORIZON
positive_control=correct strict heldout argmax and J_eval>=1.30 in at least 4/5 X-memory seeds
table_exactness=support-valid correct X-memory seed has abs(J_eval-1.35)<=1e-12
candidate_gate=Psi>0.05|mean Kappa>=0.70|correct strict heldout argmax in at least 4/5 full seeds
result_precedence=B1V2_INVALID_HOST_OR_INFORMATION_LEAK>B1V2_ACTIVITY_OR_SUPPORT_INSUFFICIENT>B1V2_LEARNING_PIPELINE_UNCALIBRATED>B1V2_FULL_LEARNER_FAILED>B1V2_CUE_ATTRIBUTION_FAILED>B1V2_CURRENT_ONLY_SHORTCUT_SUFFICIENT>B1V2_RAW_MEMORIZATION_NOT_EXCLUDED>B1V2_CUE_LEARNING_PARTIAL_TABULAR_STRONGER>B1V2_CUE_CONDITIONED_LIFECYCLE_LEARNING_TABULAR_SUFFICIENT>B1V2_EVALUATION_DOMINANCE_INVARIANT_VIOLATED
artifact_lifecycle=frozen_manifest.json->registered_claim.json->training.json->evaluation.json->analysis.json->raw_result.json
artifact_kinds=vsp02_b1v2_frozen_manifest|vsp02_b1v2_registered_full_claim|vsp02_b1v2_training|vsp02_b1v2_evaluation|vsp02_b1v2_analysis|vsp02_b1v2_result
root_marker=vsp02_b1v2_learned_cue_conditioned_lifecycle_control
retry_rescue_sweep_checkpoint_selection=0
implementation_status=SOURCE_ONLY_PENDING_CPM_ACCEPTANCE_AND_REGISTERED_FULL
```

## Protected host, learner, and retention semantics

The real reset/step host imports A1 authority, CLAIM, owner-bound RELEASE,
boundary precedence, and version-closure primitives; it never imports the A2
enumerator. `CUE_OBSERVE` exposes the presented bit once at physical clock zero.
The byte-stable `DECIDE` observation masks the bit and advances no physical,
primitive, or boundary clock. `RELEASE` commits `ENDED_RELEASE` with reward
`[1]`; `HOLD` executes the frozen primitive and commits `ENDED_NATURAL` with
`[-1,0]` for `X_b=1` or `[2,0]` for `X_b=0`. `TARGET_CLOSE` consumes the one
owner-epoch/version/action-likelihood escrow record exactly once into a
tombstone while preserving the end cause before version advance.

Neural arms remain float64 `GRUCell(10,16)` actor-critics with exactly zero
actor weights and biases, the frozen `0.8*softmax + 0.2*Uniform` behavior
probability, actor/entropy and critic losses, Adam `0.003`, batch 32, clip 1.0,
and 32 updates per neural arm/seed. Table arms retain the frozen
`0.8*greedy + 0.2*Uniform` policy and update only the executed cell to its real
return sample mean. A zero-valued table cell still uses RELEASE as its training
policy tie action. Evaluation mapping instead uses strict `argmax_a mu`: equal
probabilities record a tie and fail the held-out mapping.

## Amended gates and exhaustive dominance invariant

The table calibration follows directly from the unchanged evaluation mixture:
the correct cue table has `P(RELEASE|1)=0.9`, `P(RELEASE|0)=0.1`, `Kappa=0.8`,
and `J_X=1.35`. A correct held-out table seed must therefore satisfy
`abs(J_X-1.35)<=1e-12`; at least four of five seeds must also have the correct
strict argmax and `J_X>=1.30`. The full candidate requires `Psi>0.05`, mean
`Kappa>=0.70`, and the correct strict mapping in at least four of five seeds.

After the unchanged host, support, calibration, full-learning, attribution,
current-only, and raw-memorization gates, define `gap=J_X-J_full`. The three
remaining branches are exhaustive and asymmetric:

- `B1V2_CUE_LEARNING_PARTIAL_TABULAR_STRONGER` when `gap>0.05`.
- `B1V2_CUE_CONDITIONED_LIFECYCLE_LEARNING_TABULAR_SUFFICIENT` when
  `-1e-12<=gap<=0.05`.
- `B1V2_EVALUATION_DOMINANCE_INVARIANT_VIOLATED` when `gap< -1e-12`.

There is no finite-budget-signal branch. Independent validators reconstruct
episode physics, escrow closure, cue masks, clock invariance, schedules,
support, activity, forced-panel values, estimands, gates, strict argmax ties,
and terminal classification from retained rows. Old v1 treatment/artifact IDs,
the old root marker, altered phase artifacts, reward tampering, and closure
tampering fail closed.

The registered hard caps remain one full, 30 fits, 30,720 training episodes,
245,760 training environment transitions, 300,000 total environment
transitions, 2,176 evaluation episodes, 75,000 policy-observation calls,
30,720 learner calls, 30,720 trainer calls, 640 neural updates, and 10,240
tabular updates, with no retry, rescue, sweep, extra seed/arm/checkpoint, or
result-conditioned change. This source establishes no recurrent or escrow
superiority, long-horizon credit, multi-boundary adaptation, partner learning,
transfer, promotion, retirement, C, or formal claim.
