# HA-CTSE Current Work

Updated: 2026-07-17

## Controller

- **Active controller:** Codex on branch `aggressive`, working directly in
  `C:\project\HMASD`.
- **Versioning:** Git only; push with `git push My-paper-code aggressive`.
- **Project boundary:** IMOD is operational reference only, not HMASD evidence.
- **Shared GPU scheduler:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9`.
- **External review:** the user authorized eight new automated GPT-5.6 Pro
  exchanges in the existing consultation conversation. Used: `5/8`; remaining:
  `3/8`. Use one only at a real review or launch-clarification boundary.

## Objective

Prepare the isolated `R55-ABRP-G0` ordinary variable-N gate selected by Pro.
It replaces global set representation with direct anonymous member-entity edge
scoring; it does not add a module to the current controller.

## Next Actions

1. Commit/push the complete R54 Pro response and exact disposition.
2. Implement only the isolated 3,906-parameter R55 direct-edge toy gate and one
   focused M0 check.
3. Do not integrate it into the controller or add slots, GNN, mean-field,
   membership change, variable time, skills or intrinsic reward.

## Immediate Constraints

- R41-derived gates execute a fresh `ref/hmasd.tar` extraction rather than
  porting it into the current trainer. Preserve the original HMASD `q_D/q_d`
  terms and do not add shaping or a new intrinsic reward.
- Track the source archive in this repository and use the enclosing project Git
  commit as its version identity; do not add hashes or checksums.
- Alice--Bob is a toy environment and runs locally. R41B used 32 envs, seed 1,
  the original 937 outer updates, 2,998,400 transitions, and 14,055 optimizer
  steps per path. It is the positive source anchor, not an algorithm variant.
- Intrinsic reward must remain environment-agnostic and may not consume task
  identities, goals, contacts, phases, success predicates, distances, or
  external reward.
- R50 is authorized for local toy learning and Git push. It uses only a generic
  external roster reward; intrinsic reward, low-level policy, UAV fields, and
  environment-specific shaping are absent.
- The current external-review request is design-only. It requires one genuine
  task-dynamic variable-N toy, two natural task time scales, anonymous agents,
  sparse shared external reward, no shaping or environment-specific intrinsic,
  local fast iteration, and one evidence-bearing gate that separates
  environment no-access from shared-variable-N failure.
- GPT-5.6 Pro accepted those requirements and selected only `R51-AMDT-G0`:
  a 32-step anonymous maintenance--dispatch assignment graph with stable
  cross-episode `N in {2,3,4,5,6}`, persistent stations, short jobs, terminal
  success reward, a shared set-pointer policy, and fixed-N specialists as the
  ordinary-access prerequisite. The route is accepted pending exposure
  clarification.
- The raw R51 table states 320K transitions, 64K per N, 16 envs, 32-step
  rollouts and PPO epoch 1, which yields 125 N-specific batches per N and 625
  shared steps. Its simultaneous 3,125 shared / 625-per-specialist counts imply
  five data passes or 1.6M transitions. This is the only open question.
- GPT-5.6 Pro confirmed the corrected launch table: 125 balanced cycles, 625
  N-specific batches, 625 shared optimizer steps, 125 steps per specialist,
  625 aggregate specialist steps, 320K transitions per arm, 64K per N, PPO
  epoch 1, and no data reuse. All environment, model, seed, metric, threshold,
  branch, and no-rescue clauses remain unchanged.
- The isolated R51 implementation now contains the AMDT state machine, 24,833
  parameter anonymous recurrent set-pointer actor-critic, paired reset/order/
  categorical ledger, one-epoch token PPO, exact-final evaluator/analyzer, and
  local CUDA runner. The focused smoke passed all M0 checks: 1,280 transitions
  per arm, 10 shared and 10 aggregate specialist steps, zero sample/replay and
  prefix error, zero masked probability mass, finite gradients/drift in every
  registered module, and exact checkpoint reload. Its transient output was
  removed; it is wiring evidence only.
- Formal R51 run `logs/r51_amdt_20260716_211616` completed valid
  `NO_ACCESS_R51_AMDT_SPECIALISTS`. All M0 checks passed with 320K transitions
  and 1.28M tokens/arm, 625 shared and 625 aggregate specialist steps, 64K
  transitions/N, and zero replay/prefix/masked-mass error. Every specialist's
  exact-final success, final-minus-zero interval, and four block means were
  zero. No training batch in either arm ever produced terminal success, and
  every exact-final specialist had station-failure rate 1.0. Retire the exact
  AMDT dynamics/horizon/reset/reward contract; quarantine all shared results.
- GPT-5.6 Pro confirmed `NO_ACCESS_R51_AMDT_SPECIALISTS`, found no
  branch-changing wiring defect, and permanently retired the complete R51
  environment/information/reward contract. It selected only `R52-ARFA-G0`.
  R52 keeps stable cross-episode N, workload scaling, anonymous recurrent
  set-pointer control, specialists, terminal-only reward, and the corrected
  625-step exposure. It changes the task to terminal `U=min(M,J)` with
  recoverable station health, expiring jobs, cumulative weakest-station
  reliability, and a focal `is_current_entity` relation. No shaping or
  intrinsic reward is present.
- The isolated R52 implementation and runner are complete. One focused local
  CUDA dry-run passed every M0 check across 10 N-specific updates and removed
  its transient output. The model has exactly 24,897 parameters; the scripted
  constructive/no-job/partial, recoverable-health, switching, expiration,
  focal-relation, probability replay, prefix/hidden replay, gradient, drift,
  and checkpoint contracts all passed.
- Formal R52 completed in `logs/r52_arfa_20260716_222657` with valid M0 and
  `NO_ACCESS_R52_ARFA_SPECIALISTS`. All probability errors are exactly zero and
  exact exposure is 320K transitions/arm. Specialist training positive-utility
  rates are 0.9575--0.9985, but every deterministic final specialist has
  `M=1,J=0,U=0`, every final-minus-zero CI is `[0,0]`, and all four blocks/N are
  zero. Shared exact-final is `M=J=U=1` for every N, but is quarantined by the
  failed M1 prerequisite. The exact R52 contract is retired without rescue.
- GPT-5.6 Pro confirmed the R52 branch and found no branch-changing wiring
  defect. The narrow reusable result is that a strong stochastic return carrier
  does not guarantee a stable greedy-executable joint mode. Pro selected only
  `R53-RCMA-G0`: anonymous multi-rate queues with residual capacity encoded in
  the autoregressive support, fixed-N specialists as the access prerequisite,
  and an equal-exposure shared variable-N arm. The route is not launch-exact
  until Pro defines the two member inputs, centralized critic fields, reset
  semantics for the focal previous-queue relation, and exact arrival/service/
  deadline step order. No R53 code or run is authorized before that closure.
- Automatic exchange `1/8` returned
  `CONFIRM_R53_RCMA_G0_LAUNCH_EXACT` after 11m56s of Pro processing. It defines
  actor fields `has_previous_queue/served_previous_step`, four critic-only
  scalars, all queue zero conventions, reset/update semantics, arrivals before
  observation, service before deadline decrement, exact burst windows, and
  episode-cluster paired statistics. R53 implementation and its unchanged local
  toy gate are now authorized; no extra mechanism or rescue is authorized.
- Direct implementation found that N mandatory distinct selections among N+1
  productive queues force at least `B-1` burst services at each burst wave and
  at least `P-1` persistent services at each persistent arrival. Therefore the
  registered persistent-only `F_B=0` control is impossible for every N and the
  burst-only `F_P=0` control is impossible for `P>=2`. No R53 run occurred;
  temporary code was removed, and exchange `2/8` closed the contradiction
  before implementation resumed.
- Automatic exchange `2/8` returned
  `CORRECT_R53_RCMA_G0_ACTION_CONTRACT`. R53 now has `N+1` productive queues
  plus one anonymous idle entity, so pointer support size is `N+2`.
  Productive capacities remain one; idle capacity is exactly `N`. Idle shares
  the seven-dimensional entity encoder, pointer key, presentation permutation,
  replay ledger, and previous-action relation, so model parameters remain
  exactly `24,737`. The three scripted schedules now produce `(F_P,F_B,U)` of
  `(1,1,1)`, `(1,0,0)`, and `(0,1,0)` for every registered N. Budget, reward,
  M1/M2 thresholds, and no-rescue clauses are unchanged.
- The corrected R53 focused CUDA smoke passed every registered M0 check across
  ten N-specific updates. Sample/replay log-probability, prefix, heterogeneous
  residual capacity, dynamic mask, previous-action relation, and hidden replay
  errors were zero; all relevant modules received gradients and drifted, the
  exact checkpoint reload passed, and transient smoke output was removed.
- Formal R53 run `logs/r53_rcma_20260717_010744` completed
  `NO_ACCESS_R53_RCMA_SPECIALISTS` with every M0 check true. All specialist and
  shared final deterministic utilities and both component fractions were
  `1.0`; M1 failed only because final-minus-zero LCBs for `N=5,6` were
  `0.1139/0.1193 < 0.15`, and M2 failed only because the shared macro LCB was
  `0.1746 < 0.20`. The result therefore rejects the registered learning-gain
  gate, not executable support or final-policy competence. No rescue is
  authorized pending the exact result review.
- Automatic literature exchange `3/8` returned
  `ACCEPT_WITH_MODIFICATION: ARES-SMDP`. It selects a serial route:
  deterministic variable-N representation sufficiency -> ordinary learning ->
  exogenous dynamic membership -> fixed-roster exogenous heterogeneous `T_i`
  with duration-correct SMDP credit -> joint exogenous `N_t + T_i`. The sole
  post-R53 candidate is the supervised `R54-HFSR-G0` full-set versus
  `hybrid_m8_l2` representation gate. Implementation remains deferred until
  the separate R53 result audit closes.
- Automatic R53 result exchange `4/8` confirmed the immutable runner status
  while narrowing its scientific meaning to
  `VALID_FAIL_R53_CAUSAL_LEARNING_GAIN`. Action support and final-policy
  competence pass; learning gain fails; shared-versus-specialist transport is
  unidentified. The exact R53 combination is retired without rescue. This
  closes the deferral and activates only `R54-HFSR-G0`.
- Formal R54 retry `logs/r54_hfsr_20260717_022452` completed valid
  `NO_ACCESS_R54_FULL_SET_REFERENCE`. Every M0 check passes, including zero
  replay/checkpoint/padding/collision error and exact 600 updates per arm.
  Full-set token accuracy falls from `0.9021` at N8 to `0.2762` at N64;
  critical accuracy falls from `0.6934` to `0.1152`; exact-roster success is
  `0.6328/0.1367/0/0`. All M1 checks fail. The hybrid arm is quarantined and
  no compression conclusion or module integration is authorized.
- Automatic result exchange `5/8` confirmed
  `NO_ACCESS_R54_FULL_SET_REFERENCE`, retired the complete exact R54 contract
  and kept hybrid compression quality `UNIDENTIFIED`. ARES-SMDP is retained
  only as serial research order and probability/event-ownership discipline;
  the HFSR branch is closed. The only successor is `R55-ABRP-G0`, which replaces
  global set context with direct member-entity edge scoring on an anonymous
  typed-backlog toy before any dynamic-membership or time work.
- The focused R50 CUDA smoke passed all M0 checks with four shared updates,
  28 aggregate specialist updates, zero replay error, nonzero relevant-module
  drift, and exact zero KEEP-head drift. This is wiring evidence only.
- Formal R50 run `logs/r50_vnsl_20260716_195649` completed valid
  `NO_ACCESS_R50_SPECIALIST_SUBSTRATE`. M0 passed with 229,376 cases per arm,
  1,671,168 token decisions, 512 shared and 3,584 aggregate specialist
  optimizer steps, and zero replay error. Specialists passed macro/min token
  and macro exact gates but missed only N=16 exact-roster access
  (`0.26953 < 0.30`). Shared numerical M2 metrics all passed
  (`0.95010` macro token, `0.71094` macro exact, `0.44336` N=16 exact), but the
  registered M1 prerequisite quarantines them. R50 therefore does not decide
  cross-N sharing and says nothing about task-dynamic variable teams.
- R43 run
  `logs/r43_nrc_reset_censored_320k_20260716_121756_retry2` completed
  `INVALID_R43_FIXED_ANCHOR_LOST`. M0 passed, but fixed final win/key0/key1 was
  `0.52/0.54/0.81`, below the registered `0.80/0.85/0.85` anchor. Treatment
  outcomes are quarantined and do not retire NRC.
- The source R41B checkpoint evaluates at win `0.89` on seed 1 and `0.93` on
  the R43 seed-43041 reset stream. The R43 fixed final checkpoint evaluates at
  `0.61` and `0.52` on those streams. A same-seed two-update comparison between
  untouched source continuation and the R43 fixed wrapper produced exactly
  zero parameter difference across all five trained modules. This localizes
  the invalidity to source-continuation instability rather than the R43 fixed
  wrapper or evaluation stream. GPT-5.6 Pro confirmed this conclusion and
  selected R44-FS-NRC without another wrapper audit or R43 rerun.
- R44 uses `frozen_source_nrc0` versus `frozen_source_nrc`, seed `43041`, two
  concurrent 16-env local CUDA arms, 320K steps and 200 updates per arm, 3,000
  factor-only optimizer steps, zero source optimizer steps, and 100 paired
  deterministic evaluations. A focused two-update check passed with exact
  source-state freeze, zero replay/conditional-ratio error, control actor zero
  drift and exact zero/final traces, plus nonzero treatment actor and critic
  gradients on every factor step. The formal run completed valid
  `VALID_FAIL_R44_FSNRC`: both arms retained win `0.93`, but both had zero
  discordance, full-sync RENEW `1.0`, and zero minimum KEEP/RENEW marginal.
  Treatment actor relative drift was `0.353245` with 3,000 nonzero gradient
  steps, so actor connectivity does not explain the failed temporal transport.
  The frozen-source timing route is retired without rescue.
- GPT-5.6 Pro confirmed R44 and selected only R45-SDRA-G0. R45 keeps the R41B
  source system and zero renewal residual frozen, collects 160K natural
  source-exact steps in 16 envs, then trains fold-A/B true-Q and action-blind
  sham critics offline. Source and renewal actor optimizer steps remain zero;
  no task field, forced branch, shaping, or new intrinsic reward is present.
  A two-update CUDA wiring check passed: 96 normal factor rows with 148-D
  contexts, source probability error `4.768e-7`, binary replay error `0`,
  prefix mismatch `0`, exact source/actor freeze and zero/final traces, and
  finite nonzero gradients in all four critics. The transient smoke output was
  removed. This is implementation evidence only, not R45 scientific data.
- Formal R45 run `logs/r45_sdra_160k_20260716_144312` completed valid
  `VALID_FAIL_R45_SDRA_IDENTIFIABILITY`. M0 passed; source service remained
  `0.93/1.00/0.93`; M2 passed with true/sham weighted MSE
  `0.03830/0.37667` and ratio-gain lower bound `3.3623`. M1 failed because
  KEEP ESS was `33.59/3.30` and cluster concentration exceeded `0.10`. M3
  failed because both agents' bottom-quartile DR scores remained positive and
  same-check sign discordance was only `0.000314`. Retire Alice--Bob K50
  natural-support renewal credit and this temporal substrate without rescue.
- GPT-5.6 Pro confirmed the R45 validity/M2/retirement boundary and selected
  only `R46-HMRV-G0`: fixed `N=2`, `k0=5`, `H=40`, heterogeneous health
  degradation `{1,2}`, fixed Bernoulli-0.5 natural KEEP/RENEW behavior, zero
  policy/intrinsic updates, and four cross-fitted six-input Q/sham critics.
  The launch-exact clarification fixed `gamma=0.99`, prefix sentinels, Adam
  settings, fold seeds, episode-cluster bootstrap, evaluation seed, and both
  ordered role strata without changing the route, budget, threshold, or
  branches. No R42--R45 rescue, S7, open-roster, or variable-`N` work is
  authorized.
- Formal R46 run `logs/r46_hmrv_64k_20260716_154508` completed valid
  `VALID_FAIL_R46_HMRV_SUBSTRATE`. M0/M1/M2 passed, but agent 0's top quartile
  remained renewal-negative and pooled plus both ordered-role-stratum learned
  sign discordance were exactly zero. Direct enumeration found oracle sign
  discordance near `0.5675`, so the binding failure is learned Q/DR sign
  transport, not absence of heterogeneous value in the transition kernel. The
  exact dynamics/estimand/context/critic/read combination is retired without
  rescue. GPT-5.6 Pro then issued
  `ACCEPT_R47_NSOPM_G0_LAUNCH_EXACT`. R47 is a standalone fixed-`N=2`,
  reward-off gate with zero optimizer steps; its process modes are fit only on
  natural task-blind position/relative-moment transitions and frozen before
  any forced-skill audit.
- Formal R47 run `logs/r47_nsopm_20260716_172711` completed valid
  `VALID_FAIL_R47_NSOPM`. M0 passed with exact counts, snapshot restore,
  covariance-zero view fields, frozen parameters, and zero optimizers. Only
  eigen-rank 0 cleared its temporal null; lag-5 coherence failed. H10 support
  was `0.71875`, both causal-SNR reads were far below one, and H40 skill 0
  assigned contrast was negative. GPT-5.6 Pro confirmed the valid-fail result,
  found no branch-changing M0 defect, and permanently retired the exact line.
  It selected only `R48-SBRS-G0`: 64 source contexts at natural checks
  `{1,2,3,4}`, three nonincumbent targets, two replicas, carry/reset arms,
  40-step branches, explicit Gaussian CRN seed `68041`, 30,720 forced steps,
  no reward read or optimizer, and paired context bootstrap seed `62048`.
  A two-context CUDA check passed exact snapshot, hidden-boundary, CRN, count,
  freeze, and finite-statistic checks; its transient output was removed.
- Formal R48 run `logs/r48_sbrs_20260716_181833` completed valid
  `VALID_FAIL_R48_SBRS`. M0 passed all exact source, context, branch, hidden,
  CRN, freeze, no-reward, support, and finite-statistic checks. H10 reset rho
  lower bound was `0.98468`, reset/carry rho-ratio lower bound `1.11816`, and
  within-ratio upper bound `1.01877`. H40-late reset rho and all target-skill
  rhos passed, but reset/carry rho-ratio lower bound was only `1.00223` and
  within-ratio upper bound `1.00874`. Between-target difference was preserved;
  stochastic within-skill variability was not reduced. GPT-5.6 Pro confirmed
  the valid-fail result, the no-rescue recurrent-boundary retirement, and the
  binding fixed-`N` stop. It selected only the independent architecture gate
  `R49-ORSE-G0`, which has now completed as an interface-only PASS.
- Formal R49 run `logs/r49_orse_20260716_191959` completed
  `PASS_R49_ORSE_ARCHITECTURE`. M0/M1 passed with all registered counts:
  1,024 base cases, 8,192 permutation reads, 1,024 padding variants, 1,024
  sample/replay sequences, and 256 membership pairs. Maximum permutation and
  incremental/full logit errors were `2.98e-8`; padding and replay errors were
  zero; prefix-gradient support was `1.0` with median `0.19933`; membership
  semantics all passed; parameter drift, environment steps, reward reads, and
  optimizer steps were zero. This supports interface correctness only.
- R42 run `logs/r42_irr_native_roster_residual_320k_20260716_100824` completed
  valid `VALID_FAIL_R42_IRR_SERVICE`. Fixed/treatment wins were `0.98/0.88`;
  treatment-minus-fixed win CI was `[-0.17,-0.03]`. Treatment discordance was
  `0.10`, full-sync SET was `0.90`, and SET-target entropy was `0.6514`.
- In source Alice--Bob, success sets `done=True`, the vector wrapper immediately
  resets that environment, and the runner still samples high actions only at
  global rollout steps `0/50`. The R42 fixed evaluation averaged `58.56` steps
  and 98/100 episodes ended before step 100, so this is an exercised boundary.
- Completed branch decisions in `memory/ExpRecord.md` and the cited research
  decision files are binding. Reopen one only through a new registered causal
  edge, not by retuning budgets, seeds, thresholds, rewards, or model size.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — research contract.
- `memory/IMPLEMENTATION_PLAN.md` — latest staged core work and terminal state.
- `memory/ExpRecord.md` — formal contracts and decisions.
- `docs/research/decisions/R39_NATIVE_TOY_CREDIT_FAILURE_REVIEW_20260715.md` —
  R39 boundary.
- `docs/research/decisions/R35_R40_SUBSTRATE_FAILURE_REVIEW_20260715.md` —
  R40/R41 boundary.
- `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/`
  — variable-team disposition.
- `docs/external-review/gpt5_6_pro/20260715_r40_simple_spread_access_result/`
  — raw R40/R41 review and accepted disposition.
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/` — R41B
  evidence, all three Pro rounds, and the final source-level disposition.
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/` — R42 result,
  accepted R43 route, source-clock correction, raw responses, and disposition.
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/` — invalid R43
  result, fixed-anchor diagnostics, raw R44 selection response, and accepted
  disposition.
- `docs/external-review/gpt5_6_pro/20260716_r44_fsnrc_result/` — valid R44
  failure, raw R45 selection response, and accepted disposition.
- `docs/external-review/gpt5_6_pro/20260716_r45_sdra_result/` — valid R45
  result, controller disposition, and next-edge review question.
- `docs/external-review/gpt5_6_pro/20260716_r46_hmrv_result/` — valid R46
  result, corrected disposition, raw Pro response, and R47 launch clarification.
- `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/` — current
  manual Pro design question and Git-visible R50 evidence.
- `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/` — raw R51 result,
  training trace, controller disposition, and the single environment-design
  failure-review question.
- `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/` — raw R52 result,
  Pro-confirmed disposition, selected R53 route, and launch clarification.
- `docs/external-review/legacy/` — legacy external-review evidence.
