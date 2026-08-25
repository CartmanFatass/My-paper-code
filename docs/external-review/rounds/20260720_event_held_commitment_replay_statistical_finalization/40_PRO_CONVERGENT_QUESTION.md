# Convergent Final Completion — Event-Held Commitment Replay and Decision Contract

This is the final focused completion of the already selected
`EVENT_HELD_COMMITMENT` source. Do not reopen the divergent portfolio, select a
new route, rescue an earlier experiment, or make ordinary-controller access a
prerequisite. Do not merely list missing fields again.

## Repository files to inspect

- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260720_event_held_commitment_contract_finalization/40_PRO_CONVERGENT_QUESTION.md`
- `docs/external-review/rounds/20260720_event_held_commitment_contract_finalization/41_PRO_CONVERGENT_RAW.md`
- `docs/research/designs/NONCALENDAR_HETEROGENEOUS_TRACKING_G0.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md`

## Required decision

Choose exactly one:

1. `EVENT_HELD_COMMITMENT_CODE_READY_FINAL`; or
2. `STOP_SOURCE`.

If retaining the source, make every remaining scientific and mathematical
choice yourself and return one self-contained contract that a Code
Implementation Manager can implement without choosing a probability model,
clock, detach, optimizer exposure, checkpoint field, threshold, confidence
rule, or branch precedence. If no clean single treatment can satisfy that
condition, choose `STOP_SOURCE` and state the portfolio update.

## A. Recoverable and replay-equivalent execution state machine

Freeze one internally consistent definition of all of the following:

- the exact physical, membership, opportunity, event, segment and credit-clock
  ordering, including coincident JOIN/LEAVE/opportunity/episode boundaries;
- the event policy support. Resolve whether TERMINATE is learned or
  environment-forced. Define legal actions at JOIN and later opportunities and
  remove any declared action that has no executable semantics;
- the full probability law for every event factor. For a continuous RENEW mark,
  give its base distribution, parameterization, transform, bounds, Jacobian,
  sampled value and stored/recomputed log-density. State the joint categorical
  and mark factorization and its masks;
- the precise sampling, application and primitive-action order, including which
  pre-event or post-event commitment the primitive actor and critic consume;
- lifecycle ownership across JOIN, temporary LEAVE, REJOIN, terminal LEAVE,
  rollout truncation and episode termination for recurrent hidden state,
  commitment state, opportunity countdown/RNG, segment id, masks, returns and
  final-reward credit;
- the complete rollout ledger needed to recompute every event and primitive
  likelihood from stored observations, states, masks and actions. Give one
  numerical replay-equality criterion and identify the eligible rows;
- primitive and event advantages, critic targets, truncated-unroll boundaries,
  hidden/commitment detach rules and all score-function paths. Because the
  selected causal claim says credit is unchanged, ordinary, dummy and treatment
  arms must use matched credit and detach semantics; otherwise choose
  `STOP_SOURCE`;
- literal actor, event head and critic dimensions for the ordinary, capacity
  and dummy controls; exact trainable parameter counts; optimizer ownership,
  update order and equal optimizer-step exposure;
- checkpoint/resume contents sufficient for an interrupted run to reproduce the
  uninterrupted next rollout and update: parameters, optimizer state,
  normalizers, all RNG streams, environment/membership state, recurrent and
  commitment state, opportunity clock, masks, lifecycle/segment ledger,
  collector position and update counters. Name the one evaluation checkpoint
  and the equality test for resumed execution.

## B. Exhaustive statistical decision contract

Freeze one result-ready contract, retaining exact existing budget and seed
values where defensible, that defines:

- each training arm and the role of ordinary recurrent, literal
  capacity-matched and dummy-representation controls;
- source and held-out membership/lifetime distributions, transitions, update
  counts, optimizer exposure, evaluation episodes and the single evaluated
  checkpoint;
- the absolute access floor and every comparative external-value estimand;
- eligible populations and estimands for natural event use, heterogeneous
  lifetime and commitment intervention, including treatment of censored
  segments;
- all quantitative thresholds;
- the bootstrap cluster, resampling unit, repetitions, seed, interval type and
  strict comparison rule;
- one explicit precedence order that assigns every possible valid numerical
  result to exactly one branch.

The branch partition must be exhaustive and mutually exclusive and cover at
least:

- `INVALID_IMPLEMENTATION`;
- `NO_ACCESS_THIS_BENCHMARK`;
- `COMMITMENT_SUPPORTED`;
- `ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED`;
- `REPRESENTATION_ONLY`;
- `BENCHMARK_NON_IDENTIFIABLE`;
- a named valid mixed/failure branch for every partial-threshold pattern not
  covered above.

For each branch, state the precise portfolio update and whether it authorizes
engineering repair, integration review, source retirement, a new evidence
source, or stop. `NO_ACCESS_THIS_BENCHMARK` may constrain only this comparison
and must not veto structurally different stronger-MARL research.

## Required closing record

End with:

- causal estimand and strongest simpler explanation;
- retain/add/replace/delete ledger;
- prohibited changes while the source is open;
- exact implementation handoff or `none`;
- exact experiment handoff or `none`;
- a concise Chinese user brief explaining what will be built, why the contract
  identifies event-held commitment, the comparator role and the meaning of
  every result branch.

Keep external reward and the existing stronger-MARL mission. Do not add
intrinsic reward, task shaping, identity, fixed roles, skill classifier,
posterior, duration catalogue, hazard, graph, team latent, communication module
or a new credit objective.
