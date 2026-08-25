# GPT-5.6 Pro R40 Follow-up Disposition

Date: 2026-07-15

Source model: GPT-5.6 Pro (`Pro` web conversation)

Raw evidence: `GPT5_6_PRO_FOLLOWUP_RESPONSE_RAW.md`

## Verdict

**Accept with one implementation-minimizing closure.** The corrected reward,
estimand, exposure, and decision branches are accepted. Use PettingZoo's native
discrete action mode instead of adding the proposed sigmoid-Gaussian family.

## Accepted Contract

- PettingZoo 1.24.3 `simple_spread_v3`, fixed `N=3`, horizon 25,
  `local_ratio=0.0`, native external reward only.
- Ordinary recurrent MAPPO, local actor observations and centralized critic
  state, with no skill, high policy, intrinsic reward, HMASD, lifetime, or
  variable-team mechanism.
- Training seed 40041; 16 environments; rollout/recurrent sequence 25;
  200,000 steps = 500 outer updates; five PPO epochs; sequence batch 64; Adam
  `3e-4`; gamma `0.99`; GAE lambda `0.95`; PPO clip `0.2`; value coefficient
  `0.5`; entropy coefficient `0.01`; gradient clip `0.5`.
- Four 64-episode stochastic evaluation blocks associated with seeds
  40042--40045; a paired uniform-random comparator; 10,000 paired bootstrap
  repetitions with seed 60041.
- Primary access conditions: MAPPO mean episode return `>=-35`, paired
  MAPPO-minus-random 95% lower bound `>5`, and at least three of four blocks
  have mean return `>-35`.
- PASS authorizes only native fixed-k HMASD on this exact substrate. A valid
  failure retires this substrate without retuning, expansion, or rescue.

## Controller Closure: Native Discrete Actions

Set `continuous_actions=False`. Each agent samples one native action from
`Discrete(5)` using the repository's existing Categorical action head. Store
the executed integer and old categorical log probability; PPO replay evaluates
that same integer. This is an exact existing probability contract and avoids a
new sigmoid transform, extra pre-action storage, and an unneeded distribution
implementation in an environment-access gate.

The tracked question explicitly permitted choosing native discrete mode if the
current continuous distribution did not match `Box(0,1,5)`. Repository
inspection confirmed that `ACTLayer`, the strict recurrent MAPPO low policy,
rollout storage, and the PettingZoo adapter already support Discrete actions.

A 256-episode read-only random-policy reference under the frozen discrete
environment gave mean return `-52.5873`, standard deviation `14.8004`, and 90th
percentile `-35.6879`. Thus `-35` is outside roughly 90% of random episodes,
while the paired lower-bound margin `>5` requires a material improvement rather
than merely clearing an absolute threshold. This closes the numerical gate for
the discrete action contract without reading any trained R40 outcome.

The accepted scientific route is unchanged; only the unnecessary continuous
action implementation is removed.
