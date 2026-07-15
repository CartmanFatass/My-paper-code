# R39 Native-Toy Credit Failure Review

Date: 2026-07-15

## Decision

The fixed-`N` native-HMASD toy gate is a valid
`VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`. Its implementation boundary passed
M0, but it did not learn the registered slow/fast joint roster. Retire this
native GAE/PPO route on `two_timescale_role_free_actions` and do not rescue it
with another seed, budget, epoch count, optimizer, threshold, model size,
checkpoint, reward, label, oracle, or counterfactual objective.

The failure also retires open-roster work on this toy. Variable team size is a
separate architecture axis; it cannot repair a missing fixed-`N` credit anchor.

## Evidence Chain

- Exact joint-factorization capacity passed earlier: the same small high policy
  reached minimum correct unordered-roster mass `0.999487` on the eight toy
  contexts.
- Sampled reward alignment passed earlier: 32 correct and 352 incorrect roster
  rows had pooled raw block returns `4.900994` and `1.816988`, with standardized
  actor weights `+2.120720` and `-0.192793`.
- The native gate then completed 12,800 steps and 20/20 outer updates. It made
  60 high optimizer updates, replayed 2,560 stored joint actions with maximum
  likelihood error `4.76837158203125e-7`, and made zero low or discriminator
  updates with zero numerical repairs.
- Exact-final stochastic evaluation over 32 episodes produced
  match/slow/fast `0.455078125/0.46484375/0.4453125`, below the registered
  `0.70/0.65/0.65` floors.

The reusable causal conclusion is therefore:

```text
expressive autoregressive roster policy
+ directionally aligned sampled external return
+ exact stored-prefix replay
+ native team/agent GAE and PPO
-/-> a positive fixed-N joint-credit anchor on this toy
```

This result does not isolate a single general defect in HMASD credit. It only
falsifies the frozen native-toy anchor. It says nothing about variable skill
lifetimes, variable team size, intrinsic reward, S7 efficacy, or HMASD as a
whole.

## Candidate Substrates

| Candidate | Disposition | Reason |
| --- | --- | --- |
| Another objective or run on `two_timescale_role_free_actions` | Reject | It is a prohibited rescue of the registered valid-fail branch. |
| Existing custom Alice--Bob / CTS tasks | Reject | R35--R38 did not establish reliable ordinary-policy access. |
| R27 forced-capacity substrate | Reject as credit anchor | It is reward-off causal behavior evidence, not a learned task-credit substrate. |
| Immediate S7 R39A | Defer | It is expensive and the accepted R39 branch prohibits entering S7 as a response to this failed toy anchor. |
| Official MPE `simple_spread` | Controller recommendation for external audit | It is a public dense cooperative task, is supported by the official MAPPO implementation, has a configurable fixed team size, and is already available in the project's PettingZoo 1.24.3 runtime. |

The HMASD paper itself provides positive evidence on its exact grid-world
Alice-and-Bob task, SMAC, and Overcooked, but the repository's continuous and
asymmetric Alice--Bob variants are not the exact published environment and do
not inherit that evidence. Reconstructing the paper task remains a possible
alternative, not the controller's current recommendation.

Primary external anchors:

- HMASD paper: https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf
- Official MAPPO implementation and supported MPE tasks:
  https://github.com/marlbenchmark/on-policy
- PettingZoo `simple_spread` definition:
  https://pettingzoo.farama.org/1.23.0/_modules/pettingzoo/mpe/simple_spread/simple_spread/

## Proposed Next Edge For Review

The controller proposes only this immediate causal edge:

```text
unmodified fixed-N public MPE simple_spread
+ ordinary recurrent MAPPO
+ native external reward only
-> reproducible positive cooperative access
-> authorize a native fixed-k HMASD credit anchor on the same substrate
```

This is a substrate-access gate, not a paper contribution and not an
open-roster experiment. It must not add an intrinsic reward, skill code,
KEEP/SET policy, active mask, task hint, landmark identity reward, distance
shaping beyond the environment's native reward, or variable team size. The
official environment version and all parameters must be frozen once. A valid
failure retires this substrate rather than starting another custom benchmark or
silently expanding compute.

The exact environment parameters, action mode, fixed `N`, ordinary-policy
capacity, exposure, access metric, threshold, and terminal branches remain
unregistered until GPT-5.6 Pro selects or rejects this single route.
