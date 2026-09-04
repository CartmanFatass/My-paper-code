# FSD E3 heterogeneous-hazard discriminator — science card

Card ID: `FSD-E3-HET-R01`

Frozen: 2026-09-04 by the Direction Manager

Evidence class: **B — EXPLORE**

Claim ceiling: preliminary mechanism signal or counterexample on the three declared relay-corridor
rows; no stable superiority, transfer, C-BENCH, or direction-closure claim

Object-tier provenance:
`FSD_E2_INTERRUPTION_COST_SWEEP_INTAKE_20260904.md`, decision 1(b), `OWNER_DELEGATED`

## Question and non-goals

Question: when two pinned regions have different event hazards, does the existing D2 policy-gap
interruption rule at the prospectively selected `c=0.25` beat the strongest same-information fixed
clock, and is any gain carried by the native event-to-renewal path rather than by an unrelated
optimizer fluctuation?

Non-goals:

- no UAV transfer (E2b), random-duration events (E4), team coupling (E5), probe, churn, variable
  population, `K=3`, learned termination, value-head D3, or retuning `c` after observing E3;
- no claim that `c=0.25` is globally optimal or that a negative closes every D2 threshold;
- no held-out transfer, oracle-retuned C comparison, consumption semantics, or C-class uncertainty
  claim;
- no core performance refactor and no attempt to repair the historical E2 evaluator cost.

## Treatment, comparator, and live explanations

Treatment: the already implemented D2 rule with
`interruption_cost_c = interruption_cost_c_Z = 0.25`, `skill_cap_k_max = 40`,
`team_cap_k_Z = H = 400`, `interruption_delta = 1`, and `age_feature = off`.

Why `c=0.25` is fixed: in E2 it had the highest seed-mean D2 final return, the largest event
alignment in both seeds, and the only frozen-rule return pass (seed 1). Its seed-2 loss remains
contrary evidence; E3 does not hide or retune around it.

Strongest competent same-information comparator: D0 on the same learner, observations, training
budget, evaluator, seeds, and host tapes, with `c = c_Z = infinity` and the exact best fixed `k`
for each registered row:

| row | `(lambda_1, lambda_2)` | `Delta` | D0 `k*` | `m_dur` |
| --- | --- | ---: | ---: | ---: |
| small | `(0.005, 0.02)` | 0.4 | 20 | 0.057037 |
| medium | `(0.005, 0.10)` | 0.6 | 5 | 0.144358 |
| large | `(0.02, 0.20)` | 1.0 | 5 | 0.271219 |

The exact switching and fixed-`k` references are recomputed by the existing corridor enumerator and
recorded as reference facts, not learner outcomes. D0 competence for a seed/row is descriptive but
required before a D2 gain is interpreted: `R_D0 / J_k >= 0.85` at the final checkpoint. A seed pair
below that threshold remains a valid B observation of comparator undertraining but is excluded from
a superiority branch.

Live explanations:

1. **H1 — actionable heterogeneous renewal.** The high-hazard region produces more event-linked
   gap renewals and shorter segments; avoiding one compromised global clock raises native return.
2. **H0 — noisy policy gap.** The threshold changes segment length but renewals remain weakly
   related to events, so D2 does not beat competent D0 even when hazards differ.
3. **Optimization heterogeneity.** Seed-dependent learner quality, not the hazard contrast, creates
   apparent gains. Paired evaluation and the three row shape separate this from H1.
4. **Team-renewal interference.** A team-gap decision renews both regions and can erase the value
   of regional adaptation even when the individual gap is informative.

## Native action and consequence trace

`region event -> latent/lease invalidation -> public change flag plus lagged cue -> coordinator
held-skill gap -> individual or team gap threshold -> RENEW mask -> one setup-outage step and a
fresh lease -> per-agent service -> shared native return`.

Agents remain pinned to regions, membership never changes, and identity is entity identity rather
than slot identity. There is no join, leave, rejoin, replacement, censoring, or variable-population
quantity in this object. Primitive and opportunity time are both reported by region; optimizer
exposure is matched by seed and arm but may diverge after the policy paths diverge.

## Frozen population and matching

- Host: existing `envs/relay_corridor`, `N=6`, three agents per region, `K=2`, `Z=4`, `H=400`,
  Bernoulli events, `rho=0`, no probe, no coupling, continuous two-vector action decoded by
  `argmax`.
- Rows: exactly small, medium, and large in the table above.
- Training seeds: `1, 2, 3`; treatment and comparator at a row share the same host and learner
  master seed.
- Budget per run: 20 rollouts, 16 lanes, 400 steps, 128,000 transitions, 320 training episodes,
  four-thread CPU learner.
- Evaluation: deterministic second-agent evaluator at rollouts 5, 10, 15, and 20; 512 matched
  episodes at the first three checkpoints and 2,048 at the final checkpoint. Within a row the two
  arms use the same keyed episode tapes and preserve per-episode returns so paired differences can
  be formed.
- Development boundary: this is adaptive B work selected after E2. No E3 outcome may be presented
  as prospective C confirmation.

## Observables and estimands

Primary per seed and row:

- `G = mean_episode(R_D2 - R_D0)` on the 2,048 paired final-evaluation tapes, with paired episode
  standard error;
- `Q = G / m_dur`, reported as the fraction of the exact duration margin recovered, without a
  threshold that upgrades the B claim;
- final D0 competence ratio `R_D0 / J_k`.

Mechanism-path quantities, split by region and boundary cause:

- mean and deciles of completed agent-segment length;
- gap-caused renewals per agent-step and team-gap decisions per environment-step;
- event precision: share of gap-caused renewals in `{t_event, t_event+1}`;
- event recall: share of regional events followed by at least one regional gap-caused renewal in
  `{t_event, t_event+1}`;
- cap/reset counts, renewal outage, fresh correct-role service, stale service, and shared return;
- the same exposure ratios, transition/update/evaluation counts, wall time, and peak RSS required
  by the common runner record.

The row shape (small -> medium -> large) is reported for `G`, `Q`, segment contrast, and event-path
quantities. It is supporting evidence, not an extra gate.

## Frozen result branches

First discard no scientific data: an incomplete or instrumentation-defective invocation is
quarantined and is not included in these branches. For each row, a seed is comparator-competent
when `R_D0 / J_k >= 0.85`.

At the **large** row define an `event_path` seed as all of:

1. high-hazard mean segment length is shorter than low-hazard mean segment length;
2. high-hazard gap-caused renewal rate per agent-step exceeds the low-hazard rate; and
3. high-hazard gap-renewal event precision exceeds `0.5`.

Apply in order:

1. **E3-COMPETENCE-BLOCKED:** fewer than two of three large-row seed pairs have a competent D0
   comparator. Report all observations; make no D2 gain claim.
2. **E3-H1-ACTIONABLE:** among competent large-row pairs, `G > 0` in at least two seeds and the
   `event_path` holds in at least those same two seeds. H1 receives preliminary support.
3. **E3-RETURN-WITHOUT-PATH:** `G > 0` in at least two competent seeds but the event path does not
   hold in two. D2 pays for a reason not identified as event-driven renewal.
4. **E3-H0-NO-ADVANTAGE:** `G <= 0` in at least two competent seeds. H0 receives preliminary
   support; this closes only `c=0.25` on the declared large row and budget.
5. **E3-UNSTABLE:** anything else. Report individual seeds and the row shape; do not select a
   mechanism polarity.

The rule is sign-based because this is B exploration. `Q` reports whether a positive signal is
small or material relative to `m_dur`; it does not silently create a C threshold.

## Predictions on record

- **DM prediction:** `E3-H0-NO-ADVANTAGE`. The high-hazard region may shorten segments at
  `c=0.25`, but E2's low event precision and large seed dependence predict that the renewal path
  will not beat competent D0 in at least two of three large-row seeds.
- **Owner prediction:** `not taken (unattended)`.

## Budget, per-arm projection, and stop rule

E2 measured the unchanged runner route at

`training seconds = 20 * (64.6 + 0.769 * u)`,

where `u` is coordinator optimizer steps per rollout, plus
`3,584 * 0.46 s = 1,648.64 s` of evaluation. A 15% timing margin is applied below. The current
machine-time cap is **8 h per arm**.

| arm class | `u` used | projected wall per invocation | cap disposition |
| --- | ---: | ---: | --- |
| D0 small, `k=20` | 45 | 1.16 h | admit |
| D0 medium/large, `k=5` | 150 | 1.68 h | admit |
| D2 `c=0.25`, empirical E2 upper observation | 103.5 | 1.45 h | forecast only |
| D2 `c=0.25`, mechanical maximum `M=6,400` | 750 | 4.63 h | conservative admission projection; admit |

No arm projects above 8 h. This projection is per row, seed, and arm; concurrency does not reduce
an arm's charge. E3 has no study-wide elapsed-time gate.

Per-run stop: 20 rollouts, the first non-finite learner loss or return, or the first completed
rollout after 8 h wall time. A time-truncated or learner-instrumentation-defective invocation is
incomplete, quarantined, and uninterpreted. A fresh outcome-blind attempt at a new SHA may implement
the unchanged B object; technical failure creates no result polarity or retry budget.

Immediately before every invocation, run
`scripts/hmasd_resource_preflight.py admit-memory` and require at least 4 GiB physical and effective
available memory. A passing receipt does not override any other blocker.

## Exposure line

The machine-generated quantity is, for each trained network,
`||theta - theta_0||_2 / ||theta_0||_2` in float64. The unchanged D2 route's E2 `c=0.25` runs had
minimum-across-network final ratios `0.04826` and `0.05293`, demonstrating that this budget can move
the learner relative to initialization scale. Every E3 summary must emit the same per-network line
after rollout 1 and rollout 20. Missing learner exposure instrumentation quarantines that invocation;
resource telemetry alone follows the repository telemetry rule.

## Protected semantics and output contract

- Preserve the current learner precision, RNG streams, environment keying, D2/D0 actions, reward,
  checkpoint format, evaluator synchronization, and normalizer-copy behavior.
- Do not edit `hmasd/`, `config_1.py`, or `envs/relay_corridor/` unless CM returns a concrete
  impossibility to the DM; such a change would require a revised card before launch.
- The E3 runner may import E2 utilities and the corridor driver; it must not copy the learner loop.
- Each run writes one `summary.json` containing the quantities the rule reads, one preflight
  receipt, four evaluation records including per-episode paired-return input, 20 learner/path
  records, and a final checkpoint. Checkpoints are evidence artifacts, not a resume protocol.
- External side effects are limited to the declared run directory and normal Git work on the
  implementation branch. No network or provider effect belongs to the experiment.

## Engineering-scope declaration

This object needs **none** of `docs/project/ENGINEERING_SCOPE_SPEC.md` section 4's default-prohibited
machinery. In particular: no queue, scheduler, worker pool, resume/recovery, retry loop, lock,
heartbeat, liveness probe, tamper evidence, content-addressed manifest, currentness guard, incident
tree, schema validator, registry, telemetry beyond wall time/peak RSS, compatibility shim, or
repeated smoke suite.

Expected research surfaces:

- `scripts/run_flexible_skill_duration_e3.py`, at most 600 lines, reusing the E2/corridor loop;
- `tests/flexible_skill_duration_e3_test.py`, one toy-size end-to-end smoke and focused rule tests;
- `temp/directions/flexible_skill_duration/exp/E3_20260904/` for runtime artifacts.

CM technical success can establish that the runner executes the frozen arms, preserves protected
semantics, and records the required quantities. It cannot establish H1, H0, return value, or any
scientific branch; only the completed observations and this rule can do that.
