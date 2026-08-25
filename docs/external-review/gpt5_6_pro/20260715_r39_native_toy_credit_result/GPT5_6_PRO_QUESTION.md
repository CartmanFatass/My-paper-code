# GPT-5.6 Pro Review: R39 Native-Toy Failure And Next Credit Substrate

Date: 2026-07-15

## Purpose

Audit the valid R39 native-toy failure, then select exactly one new positive
fixed-`N` credit substrate. This is not permission to rescue R39, enter
open-roster, or design an intrinsic reward.

## Repository files to inspect

Read all of the following before deciding:

1. `memory/CURRENT_WORK.md`
2. `memory/ALGORITHM_PRINCIPLES.md`
3. `memory/ExpRecord.md`, especially the R39 dashboard rows and
   `EXP-20260715-r39-native-hmasd-toy-credit`
4. `memory/LTM/R39_NATIVE_TOY_CREDIT_FAILURE_REVIEW_20260715.md`
5. `docs/external-review/gpt5_6_pro/20260715_r39_native_toy_credit_result/r39_native_hmasd_toy_credit.json`
6. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/GPT5_6_PRO_FOLLOWUP_RESPONSE_RAW.md`
7. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/GPT5_6_PRO_FOLLOWUP_DISPOSITION.md`
8. `config_r39_native_hmasd_toy.py`
9. `envs/pettingzoo/two_timescale_role_free_actions.py`
10. `hmasd/agent.py`, especially `NativeToyFixedPrimitiveExecutor`,
    `_batched_select_action`, `update_coordinator`,
    `update_discoverer_from_rollout`, `save_model`, and `load_model`
11. `hmasd/networks.py`, especially `SkillCoordinator` sampling and
    `evaluate_training_batch`
12. `hmasd/utils.py`, especially the high-level buffer, high GAE, and
    coordinator minibatch generator
13. `train_multiproc_config_1.py`, especially
    `validate_r39_native_toy_contract`, `write_r39_native_toy_result`, the
    fixed-primitive bootstrap branch, exact-final save/reload, and evaluation
14. `requirements_server.txt`

## Fixed evidence

- M0 passed: 20/20 outer updates, 60 high optimizer updates, 2,560 stored joint
  replay samples, maximum replay error `4.76837158203125e-7`, zero low and
  discriminator updates, zero numerical repairs, and exact-final reload.
- Final match/slow/fast were
  `0.455078125/0.46484375/0.4453125`, below the registered
  `0.70/0.65/0.65` floors.
- Earlier exact factorization capacity passed with minimum correct unordered
  roster mass `0.999487`.
- Earlier sampled reward alignment passed: correct versus incorrect raw block
  return `4.900994/1.816988` and standardized actor weight
  `+2.120720/-0.192793`.
- The registered valid-fail branch permanently prohibits another run or
  objective on `two_timescale_role_free_actions`, including oracle or
  counterfactual credit.

## Controller disposition to audit

The controller retires the native-toy route and all open-roster work on that
substrate. It rejects another custom Alice--Bob/CTS task because R35--R38 did
not establish reliable ordinary-policy access, rejects R27 as a learned-credit
substrate, and defers immediate S7 compute.

The proposed single next route is:

```text
official fixed-N MPE simple_spread
+ ordinary recurrent MAPPO
+ the environment's native external reward only
-> reproducible positive cooperative access
-> only then test native fixed-k HMASD credit on the same substrate
```

Rationale: `simple_spread` is public, dense, cooperative, supported by the
official MAPPO repository, configurable in `N`, and importable in the project's
installed PettingZoo 1.24.3 runtime. The immediate gate is only an ordinary
policy access anchor. It is not variable-`N`, a skill experiment, or an
algorithm contribution.

## Requested decision

Return one explicit verdict: `ACCEPT R40 SIMPLE_SPREAD ACCESS`,
`MODIFY R40 SIMPLE_SPREAD ACCESS`, or `REJECT R40 SIMPLE_SPREAD ACCESS`.

Then answer all of the following:

1. Audit whether any concrete implementation or estimator defect invalidates
   `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`. If none exists, confirm permanent
   retirement and state the reusable causal conclusion.
2. Decide whether official MPE `simple_spread` is the unique next positive
   fixed-`N` credit substrate. If rejecting it, choose exactly one alternative
   between the exact published HMASD Alice-and-Bob environment and the existing
   S7-S1 positive HMASD reference; do not propose parallel tracks or another
   custom toy.
3. Specify the single immediate causal edge. If `simple_spread` is selected,
   the immediate edge must end at ordinary-policy positive access; do not
   silently include native HMASD or open-roster in the same experiment.
4. Give the smallest implementation boundary and evidence-bearing run. Freeze
   the environment implementation/version, `N`, `local_ratio`, action mode,
   horizon, observation/state contract, policy size, recurrent state, seed(s),
   environment steps, PPO exposure, evaluator, metrics, and numerical
   thresholds. Prefer the smallest gate that can genuinely abandon the
   substrate; do not add a separate test or audit workstream.
5. State the probability, time, information, credit, recurrent-state,
   checkpoint, and collector contracts. Distinguish native environment reward
   from any derived diagnostic.
6. Define mutually exclusive `INVALID`, `PASS`, and valid scientific `FAIL`
   branches with one next action each and no `UNDERPOWERED` escape unless you
   can justify it before seeing results.
7. State exactly what a PASS would authorize next and what remains prohibited.

Do not customize intrinsic reward to the environment. Do not read landmarks,
agent identity, distances, collisions, success predicates, or external reward
inside an intrinsic term. Do not add reward shaping, team-size/join/survival
reward, a new latent, `q_D/q_d`, KEEP/SET, active masks, learned membership,
variable `N`, or open-roster in this gate. Do not rescue R29--R39 with changed
budgets, seeds, thresholds, models, objectives, or reward definitions.
