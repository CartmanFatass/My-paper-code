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

## GPT-5.6 Pro final disposition

GPT-5.6 Pro confirmed `NO_ACCESS_R52_ARFA_SPECIALISTS` and found no
branch-changing implementation defect. The failure is specifically the
registered deterministic specialist-access gate, not absence of stochastic
task-return carrier. The reusable conclusion is that positive stochastic
expected return under valid PPO does not guarantee transport to a stable
greedy-executable joint mode.

The exact R52 contract remains permanently retired and the shared perfect result
remains diagnostic-only. The sole selected successor is `R53-RCMA-G0`, which
places observable residual queue capacity in the autoregressive action support.
Implementation is not yet authorized because the returned design leaves four
estimand-bearing definitions incomplete: the two member inputs, the centralized
critic fields, the initial previous-queue relation, and the within-step
arrival/service/deadline order. One launch clarification will close only those
items without changing the selected route or its registered exposure.

## R53 launch clarification result

GPT-5.6 Pro returned `CONFIRM_R53_RCMA_G0_LAUNCH_EXACT`. The response closes
all four missing definitions without changing the causal edge, exposure,
thresholds, reward, comparator, or no-rescue boundary. The accepted contract
defines:

- actor member fields `has_previous_queue` and `served_previous_step`;
- the seven queue fields and their zero/active conventions;
- four critic-only scalars and the exact 24,737-parameter model;
- reset and update semantics for the focal previous-queue relation;
- arrivals before observation, service before deadline decrement, and burst
  service windows `{3,4,5}` and `{9,10,11}`;
- one paired 128-episode ledger per N and episode-cluster bootstrap.

R53 is now authorized for isolated implementation, one focused M0 smoke, and
the unchanged local toy gate. No other route or mechanism is authorized.

Implementation immediately exposed a pre-training contradiction: mandatory
injective assignment of N agents to N+1 productive queues forces service in
both queue classes, so the registered persistent-only and burst-only `U=0`
controls are not executable for all N. No smoke or training was launched and
the temporary implementation was removed. R53 launch authorization is
suspended pending one action-contract correction.

## R53 feasibility correction result

Automatic exchange 2/8 returned
`CORRECT_R53_RCMA_G0_ACTION_CONTRACT`. The minimum correction is one explicit
anonymous idle/abstain entity with raw capacity N. Source: GPT-5.6 Pro,
2026-07-16; disposition: accept as the binding R53 action contract. The N+1
productive queues retain unit capacity. Idle participates in the same
seven-dimensional entity
encoder, mean pool, episode permutation, pointer key, replay ledger, and focal
previous-action relation; it creates no arrival, service, deadline, completion,
or reward contribution. Full pointer support is therefore N+2 while the model
remains exactly 24,737 parameters.

This resolves the contradiction without weakening a negative control:
constructive, persistent-only, and burst-only schedules now yield
`(F_P,F_B,U)=(1,1,1),(1,0,0),(0,1,0)` for every registered N. The reward,
128K-transition exposure, optimizer counts, M1/M2 thresholds, statistics, and
no-rescue boundary are unchanged. R53 implementation, one focused M0 smoke,
and the registered local CUDA gate are authorized again.
