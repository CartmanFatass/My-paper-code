# Return-to-go direction-balanced full actor G31

```text
status=FORMAL_USABLE_TOY_PAIR_CLOSED_UAV_PROMOTION_ELIGIBLE
formal=false
iteration_consumed=false
backend=cpu
torch_threads=1
```

## Single algorithmic delta

G31 preserves the G30 model, observations, exact-zero residual, state-only
critics, two-stage training, channel-wise actor losses, global unit-direction
composition, ordinary Adam and gradient clip. Only the successor actor/baseline
target changes from one-step detached value bootstrap to the detached realized
discounted future reward tail excluding the current reward.

Reverse recurrence is exact:

```text
running = 0
for t from T-1 to 0:
    F_t = gamma * (1-terminal_t) * running
    running = r_t + F_t
```

The final successor target is exactly zero. No epsilon, lambda, learned mixture,
event mask, future observation or environment field is added. The full-return
slow critic target remains unchanged. G30 checkpoints cannot be resumed.

## Bounded paired screen

- G17 fast/return-to-go updates: `100/100`; G18: `100/300`.
- Eight environments, two PPO passes, Adam `1e-3`, `gamma=0.99`, CPU one thread.
- G17 evaluation: 48 IID and 48 held-out episodes; G18: all three slot layouts.
- Fresh G17 model/ledger/action/evaluation-ledger/evaluation-action seeds:
  `9119000/9129000/9139000/9149000/9159000`; G18 model/action:
  `9219000/9239000`.
- Replay `<=1e-6`, raw immediate direction dot `>=-1e-7`, composition identity
  `<=1e-7`, finite credit/gradients, exact terminal tail, lifecycle, ownership,
  inactive rows, single Adam step and zero residual fail closed.

Behavioral thresholds and first-match precedence remain unchanged:

1. `INVALID_RETURN_TO_GO_DIRECTION_BALANCED_G31`;
2. `NONFORMAL_NO_G17_COMPATIBILITY_RETURN_TO_GO_G31`;
3. `NONFORMAL_NO_DELAYED_ACCESS_RETURN_TO_GO_G31`;
4. `NONFORMAL_NO_DELAYED_MECHANISM_RETURN_TO_GO_G31`; or
5. `NONFORMAL_RETURN_TO_GO_DIRECTION_BALANCED_PROMISING_G31`.

Only branch 5 can license a later formal definition. This screen consumes no
conclusion-bearing iteration and cannot support a UAV claim.

The integrated screen selected branch 5 with G17 held-out utility `0.94742`
and G18 utility/spike/rotation `0.994996/0.997803/0.998296`. This is sufficient
only to freeze the following formal paired-toy definition.

## Formal executable definition

```text
algorithm=RETURN_TO_GO_DIRECTION_BALANCED_G31
authorization_token=AUTHORIZE_RETURN_TO_GO_DIRECTION_BALANCED_G31_FORMAL_CPU_V1
replicates=3
num_envs=8
ppo_passes=2
g17_fast_updates=100
g17_return_to_go_updates=100
g18_fast_updates=100
g18_return_to_go_updates=300
g17_eval_episodes_per_domain_per_replicate=128
g18_slot_layouts_per_checkpoint_per_replicate=3
bootstrap_repetitions=10000
backend=cpu
torch_threads=1
```

Fresh formal seed bases are frozen as G17 model/ledger/action/evaluation
ledger/evaluation action `10119000/10129000/10139000/10149000/10159000`, G18
model/action `10219000/10239000`, and bootstrap `10260031`; replicate index is
added exactly once. Exercise seeds add `900000` and cannot become formal.

The first-match formal branches are:

1. `INVALID_RETURN_TO_GO_DIRECTION_BALANCED_G31`;
2. `NO_G17_COMPATIBILITY_RETURN_TO_GO_G31`;
3. `NO_DELAYED_ACCESS_RETURN_TO_GO_G31`;
4. `NO_DELAYED_MECHANISM_RETURN_TO_GO_G31`;
5. `UNSTABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31`; or
6. `USABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31`.

Behavioral gates remain exactly those of G30: G17 IID and held-out utility LCB
`>=0.90`, gain LCB `>=0.10`, minimum episode `>=0.80`, effort/mix correlation
`>=0.90`, and MAE `<=0.05`; G18 utility/gain/spike LCB
`>=0.95/0.10/0.90`, rotating-share LCB `>=0.75`, and minimum replicate utility
`>=0.90`. Operational validity additionally requires finite updates and
targets, exact lifecycle/ownership/inactive-row/terminal-tail/residual closure,
replay `<=1e-6`, raw immediate-direction dot `>=-1e-7`, composition identity
`<=1e-7`, and exactly one actor optimizer step per pass.

Zero/final checkpoints bind algorithm, source commit, formal identity,
replicate, phase exposure and configuration. Evaluation closes the exact cell
inventory and the analyzer recomputes all intervals. A one-update-per-phase
nonformal exercise must close this path and be rejected by formal-required
analysis before launch. No G30 checkpoint or screen artifact can be resumed.

The active G30 formal runner/test were migrated rather than duplicated. The
G31 runner records return-to-go phase exposure and aggregates finite target and
exact terminal-tail telemetry into the final analyzer. Six formal-runner checks
plus six G31 algorithm checks pass; the complete relevant G17/G18/G19/G30/G31
set passes `60` checks on CPU with one thread. The next action is the integrated
nonformal path exercise only.

That exercise completed with exact two-row/seven-cell/four-checkpoint closure,
zero replay and terminal-tail error, and explicit rejection under
formal-required analysis. The frozen formal iteration 21 is now the only next
action.

Formal iteration 21 completes as
`USABLE_RETURN_TO_GO_DIRECTION_BALANCED_G31`. Every G17 and G18 behavioral,
mechanism, stability and operational gate passes across three fresh
replicates. The exact paired-toy package is closed without rerun or tuning.
This licenses a new UAV transport definition but is not itself UAV evidence.

## Proof-sized acceptance

1. Hand-computed normal and mid-trajectory terminal tails are exact; final tail
   is zero and all actor targets are detached.
2. The successor baseline fits `F_t` while the slow critic still fits the full
   return including `r_t`.
3. G30 composition, optimizer state, ownership and first-replay reuse remain
   exact.
4. G17/G18 lifecycle, inactive action, replay, source controls and registered
   branch precedence pass before one bounded screen.
