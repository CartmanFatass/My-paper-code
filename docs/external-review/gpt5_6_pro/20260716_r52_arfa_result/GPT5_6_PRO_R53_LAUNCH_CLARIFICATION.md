# GPT-5.6 Pro launch clarification: R53-RCMA-G0

## Review boundary

The prior response is accepted as the binding R52 disposition and sole R53
route selection. Do not redesign R53, add another route, change its exposure,
thresholds, model width, reward, comparator, or prohibited-rescue clauses.

This follow-up exists only because four omitted definitions can produce
different AMQA transition kernels, information contracts, parameter counts, or
estimands. Return one launch-exact closure for them.

## Repository files to inspect

Read these files in full:

1. `memory/ALGORITHM_PRINCIPLES.md`
2. `memory/CURRENT_WORK.md`
3. the R52 and preliminary R53 entries in `memory/ExpRecord.md`
4. `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/GPT5_6_PRO_RESPONSE_RAW.md`
5. `ha_ctse_process/r52_arfa.py` only as the proven implementation substrate;
   do not silently inherit an R52 field or transition rule unless you name it.

## Definitions that must be closed

### 1. Exact actor and critic inputs

Name, order, normalization, and zero-denominator convention for both fields of
the registered `member encoder: 2 -> 32 -> 32`. Name the complete centralized
critic input, including the four scalar fields implicitly retained if the exact
24,737-parameter architecture is obtained by reducing R52 self/entity inputs
from 6/8 to 2/7. State explicitly which fields are actor-visible and which are
critic-only.

Also define the queue-view edge cases:

- whether all `K=N+1` queues remain action-active throughout the episode;
- `cumulative_served / cumulative_arrived` before any arrival;
- `expired_fraction` before any burst arrival;
- `deadline_remaining` when no live burst job exists;
- `selected_previous_step_count / N` at step zero.

The residual-capacity mask must remain the only new feasibility mask. Do not
make queue type, backlog, arrival, deadline, or reward an oracle action mask.

### 2. Previous-queue state

Define every focal agent's `previous_queue` at episode reset, the corresponding
`is_previous_queue_for_focal` vector at the first action, and the update rule
after selecting an empty queue. Specify whether this state survives only one
step and confirm it carries no agent identity or fixed role.

### 3. Exact within-step transition order

Give pseudocode for one environment step that orders:

1. persistent and burst arrivals;
2. observation construction and `new_arrival` visibility;
3. external agent ordering and sequential RCMA choices;
4. service application;
5. burst deadline decrement and expiration;
6. previous-step selection-state update;
7. terminal `F_P`, `F_B`, and `U` calculation.

For a burst arriving at `t=3` with deadline 3, list the exact integer time
steps on which it can be served before it expires. Do the same for the wave at
`t=9`. This must make the constructive `F_P=F_B=U=1` schedule reproducible for
every N.

### 4. Exact evaluation and paired statistics

State whether zero/final stochastic and deterministic evaluations share the
same arrival, queue-presentation, external-order, and categorical-uniform
ledgers across arms. Define deterministic decoding under the dynamic mask and
the bootstrap cluster/unit for every per-N gap, block, macro, ratio, and
noninferiority interval. Preserve the registered 128 episodes/N/evaluation and
10,000 bootstrap repetitions.

## Requested decision

Return exactly one of:

- `CONFIRM_R53_RCMA_G0_LAUNCH_EXACT`, with one unambiguous consolidated table
  containing all definitions above; or
- `MODIFY_R53_RCMA_G0_BEFORE_LAUNCH`, naming the minimum correction required
  while preserving the same causal edge.

Then restate only the resulting launch-exact M0/M1/M2 branches and permanent
no-rescue boundary. Do not authorize implementation unless all four sections
are closed. Do not propose field slots, mean field, skills, variable lifetime,
intrinsic reward, shaping, beam search, joint MAP, more training, or a parallel
route.
