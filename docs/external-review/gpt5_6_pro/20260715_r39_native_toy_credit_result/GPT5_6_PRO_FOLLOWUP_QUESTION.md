# GPT-5.6 Pro Follow-up: Correct The R40 Simple-Spread Contract

Date: 2026-07-15

## Purpose

Keep the accepted single route, but repair two factual defects in the proposed
R40 contract before implementation. Do not reopen R39 or select a different
substrate.

## Repository files to inspect

Read all of the following:

1. `docs/external-review/gpt5_6_pro/20260715_r39_native_toy_credit_result/GPT5_6_PRO_QUESTION.md`
2. `docs/external-review/gpt5_6_pro/20260715_r39_native_toy_credit_result/GPT5_6_PRO_RESPONSE_RAW.md`
3. `docs/external-review/gpt5_6_pro/20260715_r39_native_toy_credit_result/DISPOSITION.md`
4. `requirements_server.txt`
5. `hmasd/baselines.py`, especially the `mappo` branch and `create_agent`
6. `hmasd/agent.py`, especially the low actor/critic action likelihood,
   recurrent rollout storage, GAE, and low PPO update
7. `hmasd/networks.py`, especially `SkillDiscoverer`
8. `hmasd/utils.py`, especially the low rollout buffer and recurrent minibatch
9. `train_multiproc_config_1.py`, especially environment construction,
   collector action handling, evaluation, and result writing
10. `envs/pettingzoo/env_adapter.py`

## Concrete defects to correct

PettingZoo 1.24.3 `simple_spread_v3` computes:

```text
reward_i = global_reward * (1 - local_ratio)
           + local_collision_reward_i * local_ratio
```

where `global_reward` is the negative sum of closest-agent distances to all
landmarks. Therefore `local_ratio=1.0` removes the cooperative coverage reward;
it does not define actor decentralization.

The environment also has no native `success` or completion field. Its reset
info is empty, its native observable outcome is reward/return, and any
landmark-coverage statistic would be an explicitly derived evaluator metric.
Consequently `mean success >= 0.30` and `3/4 success > 0` are undefined.

Finally, with `continuous_actions=True`, each agent's action space is
`Box(0.0, 1.0, (5,), float32)`. The contract must describe this executed action
and its behavior likelihood exactly.

## Requested correction

Return exactly one corrected `R40 SIMPLE_SPREAD ACCESS` contract. Do not offer a
menu and do not change the accepted route.

1. Choose and justify one `local_ratio` that retains cooperative task credit.
   Keep actor decentralization in the information contract, not the reward
   parameter.
2. Replace the nonexistent `success` gate with one valid primary access
   estimand. Define it mathematically from native episode reward/return or from
   one explicitly evaluator-only state statistic. Give a material absolute
   floor and a paired random-policy effect floor with 95% CI, and explain why
   those numbers are not arbitrary.
3. State the exact five-component continuous-action sampling, execution, and
   PPO replay contract. If the repository's current tanh-Gaussian cannot match
   `Box(0,1,5)` exactly, prescribe one minimal adapter or choose the native
   discrete action mode instead; do not leave the behavior probability
   ambiguous.
4. Reconfirm or correct the 200,000-step, 16-environment, 500-update, five-epoch
   exposure after inspecting the repository's actual MAPPO path. Freeze the
   recurrent sequence/minibatch semantics and all optimizer coefficients.
5. Give exact M0, access, repeatability, `PASS_R40_SIMPLE_SPREAD_ACCESS`,
   `VALID_FAIL_R40_ACCESS`, and `INVALID_R40_IMPLEMENTATION` conditions, with
   one next action each.

Keep PettingZoo 1.24.3, fixed `N=3`, horizon 25, ordinary recurrent MAPPO,
native external reward only, local actor observation, centralized critic,
random-policy paired evaluation, and no skill/intrinsic/HMASD/lifetime/variable
team/open-roster mechanism. Do not add reward shaping, tune after results, or
create an `UNDERPOWERED` branch.
