# HA-CTSE Current Work

Updated: 2026-07-16

## Controller

- **Active controller:** Codex on branch `aggressive`, working directly in
  `C:\project\HMASD`.
- **Versioning:** Git only; push with `git push My-paper-code aggressive`.
- **Project boundary:** IMOD is operational reference only, not HMASD evidence.
- **Shared GPU scheduler:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9`.
- **External review:** the user authorized up to five automated GPT-5.6 Pro
  follow-ups after the manually submitted R45 review. Automatic submissions
  used: `4/5`; reuse the existing `算法探索与交接摘要` conversation only.

## Objective

Complete the final automatic GPT-5.6 Pro result review of the valid
`VALID_FAIL_R48_SBRS` gate. R48 preserved between-target process difference but
did not lower within-skill stochastic variability at either H10 or H40-late.
The registered branch stops fixed-`N` skill/lifetime algorithm exploration;
only a concrete result-changing M0 defect could alter that decision.

Variable team membership remains a separate later axis. Membership transitions
must not renew surviving agents' skills.

## Next Actions

1. Commit and push the R48 terminal result, controller disposition, and one
   tracked result-review question.
2. Use automatic Pro submission `5/5` in the existing consultation conversation
   and archive the raw response before interpretation.
3. Accept only the single final disposition. Do not resume fixed-`N` work or
   begin open-roster/variable-`N` implementation before that review.

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
- Do not begin open-roster or variable-`N` implementation before the fixed-`N`
  temporal gate.
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
  stochastic within-skill variability was not reduced. The registered fixed-`N`
  stop decision is pending only the final result-validity review.
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
- `docs/external-review/legacy/` — legacy external-review evidence.
