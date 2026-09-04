# EOCIV-B3 reward-credit learnability index

`EOCIV-B3-REWARD-CREDIT-LEARNABILITY` is a candidate-local, exploratory B
experiment. It asks whether variance-reduced episode-local reward credit makes
the already established B2 content representation learn more stable correct
payload semantics. It does not test or tune a valve and it does not license the
registered C outcome experiment.

## Implemented boundary

- `MC_RETURN` calls the unchanged B2 complete-episode Monte-Carlo actor-critic
  loss.
- `GAE_NORM` uses the same recurrent actor/value architecture with terminal
  zero bootstrap, gamma 0.99, lambda 0.95, population-standardized valid-step
  advantages, detached policy advantages, and detached
  `raw_advantage + value` critic targets.
- Both conditions use only the `content_separating` encoder, ordinary external
  team reward, Adam at `3e-4`, one update per complete episode, and gradient
  cap `0.5`.
- The real `EocivSiblingRosterEnv`, `ArmEpisodeRunner`, actor, learner, trainer,
  and three-arm evaluator are exercised. No hypothetical rollout search is
  performed (`K_search=0`).

## Fixed full plan

Seeds are 86031, 86032, and 86033. Each learner/seed runs 96 root-major,
profile-interleaved training episodes across the three registered profiles.
Immutable actor states are retained at INIT (0 updates), MID (48), and FINAL
(96). Every learner/seed/checkpoint/profile is evaluated on four registered
fresh roots through CORRECT, SWAPPED, and NATIVE_NEUTRAL.

The fixed counts are 576 training episodes, 27,648 training transitions, 576
optimizer updates, 648 evaluation episodes, 31,104 evaluation transitions, and
58,752 total environment transitions/policy calls.

## Observable matching and evidence

The result reports and checks matched initialization, architecture, optimizer
hyperparameters, training root/profile/order, evaluation roots, initial hidden
state, lifecycle identities, always-real routes, and action-noise tapes. It
retains every training return and loss component, value-target error, pre-clip
gradient norm and clip activity, coverage, counts, per-root arm contrasts,
population summaries, checkpoint changes, and checkpoint-specific A/B kernel,
sampled-action, and recurrent-state distances.

The smoke plan keeps both learners, one seed, all profiles and all three
checkpoints, uses six training updates per learner (MID after three), and one
fresh evaluation root per checkpoint/profile/arm. It is a mechanical
implementation check, not scientific evidence.

## Completed fixed B run

The fixed implementation at source commit
`d5c9297f936dc5023386765d0a7b0ff22ee7a293` was executed once as
`eociv_b3_reward_credit_learnability_d5c9297_r1`. The compact public result is
`REWARD_CREDIT_LEARNABILITY_RESULT.json`; the ignored complete raw result and
mechanical analysis remain under the run root recorded there.

All 58,752 transitions/policy calls, 576 optimizer updates, 576 training
episodes and 648 checkpoint evaluation episodes completed. GAE_NORM reduced
mean critic loss, value-target error and pre-clip gradient magnitude relative
to MC_RETURN, and its paired FINAL-minus-INIT contrast exceeded MC_RETURN in
eight of nine seed/profile cells for both registered contrasts. Absolute
correct-semantic direction nevertheless remained heterogeneous across cells,
and all updates in both learners exceeded the 0.5 gradient cap. This is a
nonterminal B diagnostic: it creates no scientific disposition and does not
license the registered C experiment.

## Interpretation limits

Mechanical completion does not assert that either credit estimator is better,
that payload semantics are stable, or that EOCIV has value under a natural
distribution. It provides no superiority, promotion, retirement, task-return,
deployment, valve, or C-level conclusion. The full result artifact is written
only after the separately managed registered B run.
