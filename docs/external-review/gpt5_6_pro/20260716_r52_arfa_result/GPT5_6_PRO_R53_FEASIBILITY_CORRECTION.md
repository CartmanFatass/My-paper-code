# GPT-5.6 Pro correction request: R53 mandatory-service contradiction

## Review boundary

The prior `CONFIRM_R53_RCMA_G0_LAUNCH_EXACT` response closed the requested
field, clock, and statistics definitions. During direct implementation, the
registered negative schedules exposed a mathematical contradiction in the
action/task contract. No R53 training or smoke was launched, and the temporary
implementation was removed.

Do not replace RCMA, propose another route, add intrinsic reward or shaping, or
change the training budget. Resolve only this action-feasibility contradiction
and return one corrected launch-exact contract.

## Repository files to inspect

Read these files in full:

1. `memory/ALGORITHM_PRINCIPLES.md`
2. `memory/CURRENT_WORK.md`
3. the R53 entry in `memory/ExpRecord.md`
4. `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/GPT5_6_PRO_RESPONSE_RAW.md`
5. `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/GPT5_6_PRO_R53_LAUNCH_RESPONSE_RAW.md`
6. `ha_ctse_process/r52_arfa.py` only as the proven reusable pointer substrate.

## Exact contradiction

For every registered team size:

```text
P = floor(N/2)
B = N + 1 - P
K = P + B = N + 1
```

Every primitive step requires all N agents to choose N distinct queues because
each queue has residual capacity one and there is no abstain/no-op action.

At a burst wave all B burst queues contain live work. At most P persistent
queues can absorb selections, so at least

```text
N - P = B - 1
```

burst queues must be selected and immediately serviced. Across both waves this
implies

```text
F_B >= (B - 1) / B > 0.
```

Therefore the registered persistent-only schedule with `F_B=0` cannot exist
for any N.

Conversely, at every persistent-arrival step the B burst queues can absorb at
most B distinct selections. At least

```text
N - B = P - 1
```

persistent queues must be selected while their new work is live. Across eight
arrival steps, for `P>=2` this implies

```text
F_P >= (P - 1) / P > 0.
```

Therefore the registered burst-only schedule with `F_P=0` cannot exist for
N in `{4,5,6}`. More generally, mandatory injective selection creates forced
task service, so the statement "serving only one class yields U=0" is not an
executable negative control under the current action set.

This is not a training, threshold, seed, or optimizer issue. It prevents M0
from being implemented as registered and changes the intended estimand if
silently ignored.

## Requested decision

Return exactly one of:

- `CORRECT_R53_RCMA_G0_ACTION_CONTRACT`, specifying the smallest change that
  makes constructive, persistent-only, and burst-only schedules all executable
  while retaining residual-capacity masking as the causal mechanism; or
- `RETIRE_R53_RCMA_G0_INFEASIBLE_CONTRACT`, if no minimal correction preserves
  the registered causal edge.

If correcting, provide one consolidated launch-exact table that explicitly
defines:

1. the action set, including any idle/abstain option and its capacity;
2. whether idle is represented as an entity, how it is observed, and whether
   it changes `K`, pooling/cardinality, model parameter count, replay, masks, or
   deterministic tie-breaking;
3. corrected constructive, persistent-only, and burst-only schedules for every
   N, with exact expected `F_P`, `F_B`, and `U`;
4. any required correction to the 24,737-parameter count or M0 checks;
5. confirmation that exposure, seeds, PPO, reward, M1/M2 thresholds, bootstrap,
   and no-rescue branches remain unchanged, or the minimum unavoidable update.

Do not solve the contradiction by deleting the negative controls without
explaining the resulting estimand, by allowing duplicate productive service,
by adding a reward-dependent mask, or by changing the terminal utility after
seeing results. Do not authorize implementation until the corrected action and
negative-control schedules are executable for all N.
