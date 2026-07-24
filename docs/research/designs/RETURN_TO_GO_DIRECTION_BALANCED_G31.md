# Return-to-go direction-balanced full actor G31

```text
status=IMPLEMENTATION_ACCEPTED_BOUNDED_SCREEN_NEXT
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

## Proof-sized acceptance

1. Hand-computed normal and mid-trajectory terminal tails are exact; final tail
   is zero and all actor targets are detached.
2. The successor baseline fits `F_t` while the slow critic still fits the full
   return including `r_t`.
3. G30 composition, optimizer state, ownership and first-replay reuse remain
   exact.
4. G17/G18 lifecycle, inactive action, replay, source controls and registered
   branch precedence pass before one bounded screen.
