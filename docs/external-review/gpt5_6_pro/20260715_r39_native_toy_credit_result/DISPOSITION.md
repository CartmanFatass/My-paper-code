# GPT-5.6 Pro R39 Failure Review Disposition

Date: 2026-07-15

Source model: GPT-5.6 Pro (`Pro` web conversation)

Reviewed commit: `c650346384769193c0214ad5f6279be1808078bf`

Raw evidence: `GPT5_6_PRO_RESPONSE_RAW.md`

## Verdict

**Modify.** Accept the route selection and the R39 retirement, but do not
execute the proposed numerical R40 contract until two factual defects are
corrected.

## Accepted

- `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR` is a valid scientific failure with
  no identified M0 defect.
- Retire `two_timescale_role_free_actions` as a credit and open-roster
  substrate; do not rescue it with oracle/counterfactual credit or another run.
- Select one public fixed-`N` ordinary-policy access gate before another HMASD,
  lifetime, intrinsic, or variable-team experiment.
- Use official MPE `simple_spread`, fixed `N=3`, PettingZoo 1.24.3, recurrent
  MAPPO, local actor observations, centralized critic state, native external
  reward only, 25-step episodes, and no skill or open-roster path.
- A PASS may authorize only a native fixed-`k` HMASD comparison on the same
  substrate.

## Required Corrections

1. `local_ratio=1.0` does not make the actor decentralized. PettingZoo 1.24.3
   computes

   ```text
   reward_i = global_reward * (1 - local_ratio)
              + local_collision_reward_i * local_ratio
   ```

   Therefore `1.0` removes the landmark-coverage team reward and leaves only
   the agent-local collision term. Actor decentralization is already determined
   by the information contract. A cooperative access gate needs an explicit
   justified reward mixture, plausibly `local_ratio=0.0` for pure shared team
   reward; this choice must be fixed before implementation.
2. PettingZoo `simple_spread_v3` exposes no native `success` field or completion
   predicate. Its native global reward is the negative sum, over landmarks, of
   the closest-agent distance. The proposed `success >= 0.30` and 3/4-seed
   `success > 0` gates are therefore undefined. The corrected gate must use a
   valid preregistered quantity: native episode return and/or a precisely
   declared evaluator-only state statistic with a non-arbitrary material floor.
3. With `continuous_actions=True`, the native action space is
   `Box(0, 1, (5,), float32)`, not a generic two-dimensional velocity. The
   collector and squashed policy likelihood must describe the actually executed
   five-component MPE action without an undocumented remapping.

These are contract defects in the proposed next experiment, not defects in the
completed R39 result. A focused follow-up must correct them before R40 is
registered or implemented.
