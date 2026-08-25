# Convergent Focused Completion — Event-Held Commitment

You are completing the already selected `EVENT_HELD_COMMITMENT` source. Do not
reopen Gemini/Open-Pro divergence, reweight the portfolio, select a new source,
rescue G0/D0/D1, or make ordinary-controller access a prerequisite. The only
legal outcomes are a complete executable contract or `STOP_SOURCE`.

## Repository files to inspect

- `docs/external-review/rounds/20260720_event_held_commitment_contract_finalization/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260720_temporal_commitment_event_semantics_retry/40_PRO_CONVERGENT_QUESTION.md`
- `docs/external-review/rounds/20260720_temporal_commitment_event_semantics_retry/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_temporal_commitment_event_semantics_completion/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_temporal_commitment_credit_contract_completion/41_PRO_CONVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_noncalendar_g0_no_access_portfolio/30_EVIDENCE_RECONCILIATION.md`
- `docs/research/designs/NONCALENDAR_HETEROGENEOUS_TRACKING_G0.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md`

## Exact conflict

The prior response made `z_i^c` event-held, but it did not freeze the event
process that creates a learned individual lifetime. Its action support and
lifecycle rules are internally incomplete, and its segment-boundary detach
changes temporal credit despite claiming unchanged PPO credit. Consequently the
proposed treatment, capacity control, likelihood replay and outcome branches
cannot yet identify event-held commitment rather than extra recurrent capacity
or a changed credit horizon.

## Required decision

Choose exactly one:

1. `EVENT_HELD_COMMITMENT_CODE_READY`: provide one self-contained contract that
   fills every material choice below; or
2. `STOP_SOURCE`: explain why no clean event-held treatment can be isolated
   without changing representation and credit together, and update the live
   portfolio accordingly.

Do not answer with another list of missing fields. If you retain the source,
make the choices yourself and freeze them for implementation.

## Required code-ready contract

For `EVENT_HELD_COMMITMENT_CODE_READY`, define:

- the causal estimand and strongest ordinary recurrent/capacity explanation;
- exact ordering of physical, membership, per-agent commitment-opportunity,
  commitment-event, segment and credit clocks, including coincident boundaries;
- the complete event-action support and policy: JOIN initialization, create,
  keep, renew and learned terminate, plus the process that schedules or requests
  each per-agent opportunity without adding a second unregistered mechanism;
- ownership and censoring across JOIN, temporary LEAVE, REJOIN, terminal LEAVE,
  rollout truncation and episode termination, including final-reward credit;
- actor and centralized critic inputs; event and primitive probability
  factorization; sampling/execution order; old-log-probability, mask, segment and
  lifecycle ledger; exact replay equality contract;
- event and primitive return/advantage definitions, truncated-unroll boundaries,
  hidden and commitment detaches, score-function paths, optimizer ownership and
  equal exposure. If credit is unchanged, every detach must be matched; if it is
  not unchanged, stop because that would combine two treatments;
- a literal capacity-matched comparator with exact architectural dimensions and
  a control that identifies representation-only benefit without weakening the
  ordinary recurrent baseline;
- checkpoint/resume contents for parameters, optimizers, normalizers, RNG,
  recurrent state, commitment state, event/segment ledger and membership
  lifecycle, plus the exact evaluation checkpoint;
- frozen source and held-out membership/lifetime distributions, seeds,
  transitions, updates, optimizer steps and evaluation episodes, referring to
  exact existing values where retained;
- absolute access floors and comparative external-value estimands; eligible
  populations for natural use, lifetime diversity and commitment intervention;
  quantitative thresholds; bootstrap cluster, repetitions, interval rule and
  branch priority;
- exhaustive mutually exclusive branches covering `INVALID`,
  `COMMITMENT_SUPPORTED`, ordinary/capacity explanation, representation-only,
  `NO_ACCESS`, and benchmark non-identifiability, with a portfolio update for
  every branch. `NO_ACCESS` may constrain only this benchmark comparison;
- the replacement ledger and prohibited changes;
- a concise Chinese user brief stating what will be built, why it identifies the
  mechanism, the comparator role, and what every result means.

Keep external reward, anonymous membership, survivor continuity and the
ordinary recurrent comparator. Do not add intrinsic reward, task shaping,
identity, roles, skill classifier, posterior, duration catalogue, hazard,
graph, team latent, or a new credit objective.

