# R52-ARFA-G0 disposition

- Date: 2026-07-16
- Run: `logs/r52_arfa_20260716_222657`
- Registered status: `NO_ACCESS_R52_ARFA_SPECIALISTS`
- Implementation validity: true

## Binding evidence

- M0 passed with the exact exposure: 320,000 transitions and 1,280,000
  autoregressive token decisions per arm, 625 shared updates, and 125 updates
  per specialist.
- Sampling/replay log probability, prefix, recurrent hidden, focal relation,
  and masked probability errors are all exactly zero.
- Every fixed-N specialist has a positive training-return carrier:
  `P(U>0)=0.9575--0.9985`.
- Every exact-final deterministic specialist has `M=1`, `J=0`, and `U=0`.
  Every final-minus-zero interval and every one of four evaluation blocks is
  zero for every N.
- The shared policy has exact-final `M=J=U=1` for every N, but this result is
  quarantined because the registered fixed-N access prerequisite failed.

## Disposition

Retire the exact R52 task/comparator contract without changing its budget,
optimizer steps, seeds, model, reward, evaluation rule, thresholds, or
aggregation. Do not claim variable-N learning from the quarantined shared arm.
Request one failure review to validate the scientific branch, explain the
stochastic-carrier/deterministic-final contradiction, and choose one genuinely
new falsifiable successor edge.
