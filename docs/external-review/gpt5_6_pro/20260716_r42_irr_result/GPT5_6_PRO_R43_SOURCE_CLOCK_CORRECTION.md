# GPT-5.6 Pro Focused Correction: R43 Source Clock Versus Environment Auto-Reset

Date: 2026-07-16

## Scope

The preceding response is accepted on R42 validity and on the need for a true
renewal factor with conditional non-incumbent skill assignment and separated
credit. Before implementation, direct source inspection exposed one concrete
contract contradiction. Resolve only this contradiction and return one corrected
R43 contract. Do not reopen R42, propose parallel routes, or add compute.

## Concrete source behavior

The original Alice--Bob environment terminates immediately on success, not only
at the 100-step limit:

```python
if np.all(self.goals_reach):
    reward = 1.0
    done = True
    info_['battle_won'] = True

if self._episode_steps >= self.episode_limit:
    done = True
```

The official vector wrapper immediately resets an environment whenever all
agents are done:

```python
ob, s_ob, reward, done, info, available_actions = env.step(data)
if np.all(done):
    ob, s_ob, available_actions = env.reset()
```

However, the original HMASD Alice--Bob runner samples a high action only at
global rollout steps divisible by `skill_interval=50`:

```python
for step in range(self.episode_length):
    if step % self.skill_interval == 0:
        h_values, h_actions, h_action_log_probs = self.h_collect(
            step // self.skill_interval
        )
```

There is no per-environment high assignment after an early vector auto-reset.
The just-reset environment continues using the previously held `team_skill` and
`indi_skill` until the next global check. The high buffer has exactly two rows
per 100-step rollout and source optimizer exposure is based on those rows.

This is not merely theoretical. In the valid R42 fixed arm, 98 of 100 final
evaluation episodes terminated before step 100; average episode length was
`58.56`, with a minimum of `56`. The positive checkpoint therefore commonly
reaches `done` after the global `t=50` assignment. During training, vector
workers auto-reset such environments and run the remaining rollout steps before
the next high assignment at the next outer rollout's `t=0`.

## Contradiction in the accepted response

The response simultaneously requires:

1. a complete source-exact fixed comparator and source-global native `k0=50`
   high clock;
2. treatment warm start whose effective post-skill distribution exactly equals
   the source distribution;
3. `episode reset: all agents force initial RENEW`;
4. skill-event credit ending at episode terminal and a new initial segment after
   reset;
5. exactly two global high rows and 3,000 source optimizer steps per arm.

Under the actual auto-reset collector these cannot all hold. Forcing a new high
assignment on every early reset adds per-environment high events, changes RNG and
trajectory distributions, requires a variable-length event buffer, and is not
the source fixed continuation. Not forcing it violates the stated reset/segment
contract and leaves a post-reset continuation with no newly sampled skill
factor.

## Repository files to inspect

Read all of the following before answering:

- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/GPT5_6_PRO_RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/fixed_refresh_seed_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/original_source/envs/env_wrappers.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/envs/alice_and_bob/alice_and_bob0.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/alice_and_bob_runner.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/base_runner.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/utils/h_shared_buffer.py`
- `scripts/run_r42_native_roster_residual_arm.py`
- `scripts/r42_native_roster_residual.py`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/ExpRecord.md`

## Requested decision

Return one integrated correction containing:

1. **Contradiction verdict.** Confirm or reject the source reading with a precise
   code-based reason. Do not treat rollout index `episode` as an environment
   episode if the vector worker has already auto-reset internally.
2. **Choose exactly one reset semantics.** Select one of the following, or one
   precisely specified structurally different resolution:
   - preserve the source-global high clock and define how segments, ages, and
     skill-event credit behave across an exogenous environment auto-reset with
     no new high action;
   - introduce true per-reset initial assignments and redefine both comparator
     arms, event storage, likelihood, optimizer exposure, and the meaning of
     source-exactness;
   - retire this R43 Alice--Bob gate because source-exact comparison and the
     requested reset semantics are incompatible, then select exactly one other
     fixed-`N` causal gate.
3. **Correct probability and segment contract.** State whether a reset creates
   a policy factor, whether the incumbent survives, whether age resets, whether
   the open skill segment is terminally closed or censored, and what action is
   responsible for post-reset execution.
4. **Correct credit contract.** Give exact return endpoints and bootstrap/mask
   behavior for renewal and conditional skill factors when success occurs at
   step 56--99 and the vector worker immediately starts another environment
   episode within the same 100-step rollout.
5. **Correct buffer/update counts.** State whether the high/event row count is
   fixed or variable, how PPO minibatches are normalized, and whether the
   registered 3,000 source optimizer steps remain exact.
6. **Comparator validity.** Explain how the fixed arm remains the proven R41B
   continuation and how treatment zero initialization remains distribution
   equivalent at every action opportunity actually present in the collector.
7. **Revised M0 and gate.** Replace only the clauses affected by reset/clock
   semantics. Preserve seed `43041`, two concurrent 16-env arms, 320,000 steps
   per arm, service margin, temporal thresholds, and the single
   `VALID_FAIL_R43_NRC` abandonment branch unless the selected resolution makes
   one of them mathematically undefined.

Do not add environment-specific intrinsic reward, lifetime reward, renewal
entropy, forced refresh, task fields, a duration action, R42 residual rescue, or
variable `N`. The answer must leave exactly one implementable R43 causal edge.
