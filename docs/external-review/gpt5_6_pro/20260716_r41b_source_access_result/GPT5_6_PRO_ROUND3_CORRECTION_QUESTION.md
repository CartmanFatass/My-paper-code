# GPT-5.6 Pro Final Correction: Make R42 Internally Executable

## Status

This is authorized automated consultation round 3 of 3. Round 2 accepted the
R41B source anchor and selected an original-clock native renewal gate, but its
contract cannot yet be implemented without guessing. Read the raw response and
controller disposition, then return one corrected, self-consistent experiment.

Do not reopen R41B or select a parallel route. The only question is the exact
first same-checkpoint temporal intervention.

## Repository files to inspect

1. Round-2 question, response, and disposition:
   - `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/GPT5_6_PRO_QUESTION.md`
   - `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/GPT5_6_PRO_RESPONSE_ROUND2_RAW.md`
   - `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/ROUND2_DISPOSITION.md`
2. Exact R41B evidence:
   - `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`
   - `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/seed1_result.json`
3. Actual original-source implementation:
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/base_runner.py`
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/alice_and_bob_runner.py`
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/utils/h_shared_buffer.py`
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/utils/l_shared_buffer.py`
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/mat_trainer.py`
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/algorithm/transformer_policy.py`
   - `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/algorithm/ma_transformer.py`
4. Current contracts:
   - `memory/ALGORITHM_PRINCIPLES.md`
   - `memory/IMPLEMENTATION_PLAN.md`
   - `memory/ExpRecord.md`

## Corrections that must be closed

### 1. Team `Z` must have one probability contract

Round 2 says `Z` is held at partial checks, but also includes a sampled
`log pi_H(Z|x)` factor in every event. Choose exactly one:

- resample `Z` at every existing `k0=50` check exactly as original HMASD and
  include its action/value/ratio, while explaining why a kept `z_i` under a new
  `Z` leaves the existing `q_d(z_i|o_i,Z)` algorithm unchanged; or
- hold `Z` at a precisely defined partial check, omit the team action/value/ratio
  there, and define when a full refresh occurs without silently changing the
  source team-credit clock.

Do not combine these contracts. State the exact initial assignment and the
check at `t=50` for a 100-step episode.

### 2. Effective action support must be exact

If the original `K=4` categorical sample is reinterpreted, the effective event
support is exactly:

```text
{KEEP} union {SET(z): z != incumbent}
```

with `K` categories, not `{KEEP} union {1,...,K}`. Explain why this is or is not
the same Gate B that round 2 rejected, and resolve the stated `q_d` objection.
Specify the pre-check roster, post-edit working prefix, stored action, agent
order, old log probability, teacher-forced replay, team/agent PPO ratios, and
whether any new parameter exists.

### 3. Budget arithmetic and optimizer exposure must close

Exactly 320,000 continuation steps require either:

- 32 envs x 100-step rollout x 100 outer updates; or
- 16 envs x 100-step rollout x 200 outer updates.

Choose one and justify it against checkpoint batch compatibility and local
resource cost. Give the exact high, low-actor, low-critic, `q_D`, and `q_d`
optimizer-step totals per arm under the actual source epoch/minibatch loops.
Do not state only "matched".

### 4. Positive-control and service gates must be numerical

Both arms load the same R41B exact-final checkpoint and all optimizer/value
normalizer states. Define:

- an M0 compatibility path before continuation;
- a fixed-arm positive-anchor requirement after continuation;
- treatment-versus-fixed paired service noninferiority using the same reset
  stream;
- exact deterministic/stochastic evaluation choice, episode count, bootstrap
  unit/seed, and numerical thresholds.

Separate `INVALID_FIXED_ANCHOR_LOST` from a valid treatment failure.

### 5. Renewal decoupling must be measurable in this horizon

Alice--Bob has a 100-step horizon and `k0=50`, so after the initial assignment
there is only one ordinary check at `t=50`. Completed lifetime sequences are not
naturally paired, and episode-terminal long runs are right-censored. Do not use
undefined `corr(T_i,T_j)` or an unspecified `P(T_i != T_j)`.

Define event-level quantities on the paired `t=50` renewal decisions, such as
per-agent KEEP/SET marginals, discordant-renewal rate, full-sync SET rate, and
skill-supply entropy. If terminal run length is reported, state explicitly how
censoring is handled and do not overclaim a survival distribution. Give exact
cluster/bootstrap units and numerical gates.

## Requested decision

Return exactly one verdict token:

- `ACCEPT_R42_<precise route>`, or
- `REPLACE_R42_<precise route>`.

Then give one implementation-ready contract with:

1. the single causal edge and exact claim boundary;
2. sampling/replay equations consistent with the actual MAT source;
3. clocks, reset, hidden-state, rewards, returns, advantages, detach boundaries,
   buffers, and checkpoint migration;
4. files/functions to modify and files forbidden to modify;
5. exact two-arm local command-level budget and expected optimizer counts;
6. M0 implementation, fixed-anchor, service, renewal-decoupling, and
   skill-supply gates;
7. mutually exclusive PASS, valid-failure, invalid, and operational-failure
   tokens, each with exactly one next action;
8. the strongest objection and whether it changes the route.

The result may claim only renewal decoupling on the original 50-step grid. It
must not claim arbitrary shorter skills, general asynchronous scheduling,
multi-seed efficacy, S7/UAV transfer, or variable-team support.

Still prohibited: `k0=10`, a duration head, independent KEEP Bernoulli,
task-specific intrinsic reward, reward shaping, modified `q_D/q_d`, new team
latent, learned service priority, variable `N`, open roster, five seeds, or any
R29--R40 revival.
