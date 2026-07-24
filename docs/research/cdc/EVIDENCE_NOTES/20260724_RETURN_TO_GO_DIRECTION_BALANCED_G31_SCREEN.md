# G31 return-to-go direction-balanced bounded screen

```text
status=COMPLETE_OPERATIONALLY_VALID_PROMISING
formal=false
iteration_consumed=false
source_commit=e552e1e0d097715d0f8505a254864bac098cd68d
run=logs/nonformal_return_to_go_direction_balanced_g31_20260724_e552e1e_pm1
branch=NONFORMAL_RETURN_TO_GO_DIRECTION_BALANCED_PROMISING_G31
```

## Registered evidence

The one frozen paired screen completed on CPU with one Torch thread. G17
retains the immediate-service policy and G18 now crosses the delayed access and
mechanism point gates under the same budgets used for G30:

- G17 final held-out/IID utility is `0.9474206/0.9568875`, held-out gain is
  `0.7315669`, and the minimum episode is `0.9252304`.
- G17 effort/mix correlations are `0.9858675/0.9925977`; MAEs are
  `0.0194835/0.0139196`.
- G18 final utility is `0.9949956`, anchor gain is `0.2690636`, spike utility
  is `0.9978029`, rotating effort share is `0.9982958`, and the minimum step
  utility is `0.8462080`.
- Replay and direction-composition errors are exactly zero, terminal future
  tails are exactly zero, the minimum raw immediate-direction dots are
  `0.0940089` and `0.00727136`, every actor update advances Adam once, and the
  residual remains exactly zero.

The realized future tail therefore separates the G30 spike-access failure at
the bounded-screen level without an event flag, future actor observation,
environment field, coefficient or threshold change. It does not yet establish
fresh-seed stability, a formal result, individual causal credit, or UAV
transport.

## Decision

Select exactly one formal paired-toy iteration. Freeze fresh seeds and the
existing G30 budgets, bootstrap, thresholds and first-match ordering. Add only
G31-specific operational closure for finite return-to-go targets and exact
terminal-zero tails. A valid non-usable branch closes G31 without seed, budget,
threshold or source rescue.
