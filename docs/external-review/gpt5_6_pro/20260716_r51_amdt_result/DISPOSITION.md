# R51-AMDT Controller Disposition

Date: 2026-07-16

Run: `logs/r51_amdt_20260716_211616`

## Decision

Accept the registered terminal status:

```text
NO_ACCESS_R51_AMDT_SPECIALISTS
```

M0 passed without exceptions. The exact 625-step exposure, paired ledgers,
terminal-only reward contract, active masks, autoregressive prefix, recurrent
replay, gradients, parameter drift, and exact-final checkpoint reload are
valid. Sample/replay error, prefix error, and masked probability mass were all
zero.

M1 failed at the ordinary-policy prerequisite. Exact-final specialist success
was zero for every `N={2,3,4,5,6}`; every per-N final-minus-zero interval and
all four evaluation blocks were zero. None of the 625 training batches in
either arm contained a terminal success. Shared results are therefore
quarantined and do not decide variable-N sharing.

## Binding consequence

Retire the exact AMDT dynamics, 32-step horizon, reset distribution, and
full-conjunction terminal reward contract without changing steps, epochs,
seeds, model width, thresholds, or reward and rerunning R51. The next work is
one environment-design failure review for a newly registered task, not an R51
rescue and not a return to skill/lifetime/intrinsic/UAV work.
