# G53 common-entropy attribution — code/science index

Status: implementation candidate for CM review; this index records code
bindings, not a scientific result or technical acceptance.

Frozen authority is
`CONTINUOUS_ROSTER_NATIVE_SIX_G31_COMMON_ENTROPY_ATTRIBUTION_G53_SCIENTIFIC_FREEZE_PACKET.md`
and internal handoff SHA-256
`d49f6b32878f172fc37db2200fde8342a4f1456b1bdd9efe465e3d9f8c3ba948`.
The implementation is confined to the fresh G53 source, runner, two focused
test files, and this index. G50 and G51 are provenance/objective authorities;
no predecessor artifact initializes G53 and G52 is absent.

| Frozen assertion | Concrete binding | Enforced invariant | Focused proof |
|---|---|---|---|
| Candidate/source/claim identity | `ALGORITHM_ID`, `SOURCE_ID`, `CLAIM_IDENTITY`, `ESTIMAND` | strict manifest identity; positive delta favors common entropy | `test_exact_identity_budget_seeds_and_zero_g52_dependency`; runner configuration test |
| G50/G51 commit-pinned provenance only | G50/G51 commit and branch constants; `source_controls` | predecessor artifact initialization count is zero | runner source-controls test |
| Zero G52 authority/state/artifact/result | `G52_CARRY_STATE_COUNT`; static/config/source controls/checkpoint fields | count is exact zero; no G52 import or artifact parameter | identity test; source-controls test; static source scan |
| Coefficients `0.01` / `0x1.47ae147ae147bp-7` and exact `0.0` / `0x0.0p+0` | `REFERENCE_ENTROPY_COEFFICIENT`, `NULL_ENTROPY_COEFFICIENT`, immutable `ENTROPY_COEFFICIENTS`, `entropy_coefficient` | `float.fromhex` plus exact `.hex()` assertions; arm is the only lookup key | identity test; static certificate |
| Do not mutate the G40/g19 coefficient | `reconstruct_static_certificate` | G40 and g19 remain exact 0.01 authorities | static-gate test |
| Same raw entropy forward/autograd graph in both arms | `_build_entropy_plan`, `_phase_A_plan`, `_phase_B_plan` | both arms call `g40._entropy` and `_gradient_rows`; zero arm multiplies finite raw rows by exact zero without skip/detach/replacement | same-graph test; first-batch certificate |
| Coefficient immutable in both phases and both passes | `_optimize_update` and phase-specific plan builders | observable `coefficient_read_audit` must contain exactly one ordered read per arm/pass; monkeypatched callable proves construction/configuration/checkpoint/result paths do not read it | source monkeypatch test; strict nested pass-record tamper test |
| Objective `L_PPO(center_and_population_RMS(r_t))-c*H_active_mean` | `_normalized_reward`, `g49._single_immediate_target`, `g49._normalize_single`, `g40._policy_loss_from_normalized_advantage`, `g40._entropy` | one 384-row float64 center/population-RMS normalization per realized arm batch; exact-zero scale handled by G49 | same-graph test; update pass records |
| Actor input/action/entropy host unchanged | inherited G40/G47 actor and `_actor_trajectory` | six-coordinate input, active-mask/log-count, autoregressive prefix, action dimension 2, clamped Normal entropy | static certificate binds 17-name actor order and entropy support; runner source controls |
| Baseline-free before trajectory or optimizer | `make_phase_A_models` | exactly one `g40.make_model`; exactly one `G51NoBaselinePhaseAProjection`; then two deep clones; no `g51.make_phase_A_models` | fresh-factory test; `phase_A_boundary_audit` |
| Storage-disjoint arms with equal unexposed slow critic through Phase A | `make_phase_A_models`, `phase_A_boundary_audit` | zero shared storage; slow-critic bytes/masks equal; optimizer is actor-only | fresh-factory test |
| Common boundary deletes Phase-A slow critic and Adam | `project_phase_B_models` | actor/log-std bytes retained; slow critic/baseline/critic/delayed-residual keys absent; Phase-A optimizer disposed | phase-boundary test |
| Fresh empty Phase-B Adam, exact class/hyperparameters/order | `make_phase_B_optimizers` | accepted G50/G41 actor-head Adam; empty state and actor parameter order | phase-boundary test; checkpoint validator |
| One update-0 stored object, collected before treatment | `_train_root`, `optimize_phase_A_update`, `_optimize_update` | one object is exposed twice; both complete plans precede either step | update-object test; first-batch certificate |
| Update 1 onward separately on-policy | `_train_root`, `_optimize_update` | same-object reuse is rejected after update 0; each arm collects from its current policy | update-object test; update records |
| Paired exogenous episode/ledger/action-noise roles | `_train_root`, `_actor_trajectory`, `_optimize_update` | episode IDs must match; seeds match by update while trajectories remain arm-local | update records and manifest work counts |
| Reverse preparation is non-mutating | `_optimize_update` | forward/reverse assigned gradients match and direct snapshots prove model, Adam, gradient slots, and RNG unchanged before steps | synthetic update-0 proof; strict pass-record validator |
| First-batch activation certificate | `_activation`, `_optimize_update` | model/mask/RNG/metadata/Adam/replay/target/normalization/policy-gradient equality; raw support exactly `policy.log_std`; null scaled bytes zero; reference scaled norm positive; coefficient sole delta; post-step state diverges | source focused first-batch test path; manifest validation |
| `q_H` definition and activation | `_activation` | both-zero maps to zero; otherwise float64 difference norm divided by max arm norm; nonfinite rejected; active iff `q_H>0` | first-batch certificate and validation |
| Exact nonformal counts | constants and `static_configuration_certificate` | 1 root, 10/10 updates, 8 envs, H=48, 2 passes, `post_treatment_arm_local_physical_collections_per_root=38`, 39 total physical collections (=1 shared + 38 post-treatment), 40 arm-update exposures, 14,976 train, 6,912 evaluation, 21,888 total, 80 optimizer steps, 250 bootstrap | identity/budget test; strict nested-manifest tamper tests |
| Corrected seeds and offset | `SEED_BASES`, `BOOTSTRAP_SEED`, `NONFORMAL_SEED_OFFSET`, `seed_block`, `bootstrap_seed` | frozen bases 10541000..10551053; nonformal offset 900000; no seed search | identity/budget test |
| Native backend and resources | `_native_backend_identity`, `_cpu_configuration`, spawned train/evaluation workers | required C++ batch, no Python fallback, CPU/process 2/2, spawn, thread env and Torch threads 1, RSS ≤2 GiB, wall ≤1200 s | runner configuration test; strict manifest resource validators |
| No search/retry/rescue | static/configuration certificates | K=0, zero hypothetical trajectories/transitions, no nested rollout/replanning/sweep/extra root | identity/budget test |
| Fresh root and artifact inventory | `_fresh_root`, `train`, validators | nonempty root rejected; exactly two final checkpoints plus three positive JSON artifacts; transient payloads deleted | fresh-root test; training/evaluation/analysis validators |
| Strict checkpoint schema and reload/tamper guards | `build_final_checkpoint`, `validate_final_checkpoint`, `load_final_checkpoint_model`, runner digest validators | exact actor/Adam inventories; tensor type/shape/dtype/finite; Adam scalar float32 step 20; strict boundary predicates; SHA-256/source/boundary identity before evaluation | NaN/scalar/shape/dtype/step/boundary/foreign-key tamper test |
| Evaluation source/cells | `_processes`, `_evaluate_task`, `validate_evaluation_artifacts` | exact arm×capacity×cell order/index; accepted G34 fixed/random dispatch; 24 cells and six strict episode mappings; lifecycle true; zero optimizer/coefficient/baseline reads | evaluation dispatch test; order/lifecycle/fixed-source/coefficient tamper test |
| Branch precedence and one-root claim ceiling | `select_result_branch`, `_expected_analysis_metrics`, `analyze` | prerequisites and metrics recomputed from strict train/evaluation evidence; invalid precedes nonformal complete; future claims empty; ranking/retry/scientific/formal-terminal flags false | branch-precedence and analysis flag/branch tamper tests |
| Formal CLI fails closed | `configuration`, `train`, `_reject_formal` | any formal flag/authority rejected | formal-fail-closed test |
| Readiness is proof-only | `_strict_readiness_train`, `_load_readiness_train`, readiness functions | valid commit and exact train schema; zero scientific roots/transitions/optimizer/bootstrap; downstream phases reject wrong phase/commit/failed evidence; reload binds SHA-256; creates no nonformal manifest | readiness commit/phase/digest tamper tests |

The package intentionally does not claim entropy-code deletion, necessity,
coefficient optimality, directed exploration, centering/reset attribution,
multi-root generalization, or broad MARL/deployment effects. The zero arm is
still stochastic because its Normal sampling path is unchanged.
