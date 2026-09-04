# FSD A1 same-information headroom census and DM intake

Date: 2026-09-04

Evidence class: **A/RECON, read-only census**

Claim ceiling: arithmetic availability of a same-host upper-reference gap for the registered
relay-corridor rows. This is not evidence that D2 captures the gap, not an MEI threshold, and not a
priority, lifecycle, promotion, or direction decision.

## Question and sources checked

Question: does current FSD evidence already contain a same-host, same-information upper reference
minus a tuned generic baseline, or is a new minimal A/RECON object needed before that raw headroom
can be stated?

I checked:

- `envs/relay_corridor/references.py`, including the distinction between the host-private switching
  oracle, public-state greedy reference, exact fixed-`k` references, and `m_dur`;
- the accepted E2 result and its historical exact-reference table;
- the frozen E3 card and the three registered row configurations; and
- the valid complete E3 small-row D0 summaries under
  `temp/directions/flexible_skill_duration/exp/E3_20260904/`.

No E3 treatment return and no incomplete medium/large learner output was read to choose this census
disposition. The running E3 contract, arm order, and interpretation rule remain unchanged.

## What is actually same-information

At the registered `K=2` host, the public-state greedy reference equals the switching oracle
exactly: the public change flag plus lagged cue identify the only different latent. Thus
`J_greedy = J_switch` supplies a public-information upper reference on the same host and reward
scale as the learner.

Two denominators must remain distinct:

1. `J_best_fixed_k` is the exact, oracle-tuned best fixed clock over the registered `k` grid.
   `J_greedy - J_best_fixed_k = m_dur` is the prospective structural headroom already registered by
   the host. It is not a learned-baseline outcome.
2. The trained D0 final return at that exact registered `k*` is the empirical tuned generic
   baseline. `J_greedy - R_D0` is the observed upper-to-learned headroom. It is available only for
   rows whose D0 seeds have validly completed.

The exact fixed-`k` reference uses oracle stamping at its renewal boundaries. Treating it as the
learned generic baseline would erase optimization shortfall. Conversely, comparing the public
upper to trained D0 is same-information at the learner interface, but includes any D0
undertraining. Both raw quantities are therefore reported and not conflated.

## Raw registered structural headroom

These are reference facts, not learner outcomes.

| object/row | host hazards | public upper `J_greedy = J_switch` | exact tuned fixed-clock `J_best_fixed_k` | raw structural gap `m_dur` |
| --- | --- | ---: | ---: | ---: |
| E2 homogeneous | `(0.02, 0.02)`, `Delta=0.4` | `0.3920199999999997` | `0.3133920282449043` at `k*=20` | `0.0786279717550954` |
| E3 small | `(0.005, 0.02)`, `Delta=0.4` | `0.3950124999999998` | `0.3379750535732167` at `k*=20` | `0.0570374464267831` |
| E3 medium | `(0.005, 0.10)`, `Delta=0.6` | `0.56857875` | `0.4242209625375001` at `k*=5` | `0.14435778746249994` |
| E3 large | `(0.02, 0.20)`, `Delta=1.0` | `0.8902749999999997` | `0.619056016` at `k*=5` | `0.27121898399999966` |

The E3 values were recomputed without learner execution by the already-accepted exact enumerator
on the frozen row configurations and agree with the `m_dur` values frozen in the E3 card.

## Raw observed upper-to-trained-D0 headroom

E2 is complete on the homogeneous host. Its learned best D0 is `k=20` in both seeds:

| seed | trained D0 return | `J_greedy - R_D0` |
| ---: | ---: | ---: |
| 1 | `0.301320475` | `0.0906995249999997` |
| 2 | `0.304232422` | `0.0877875779999997` |
| mean | `0.3027764485` | `0.0892435514999997` |

E3 small is the only heterogeneous row whose three D0 invocations are currently valid complete:

| seed | trained D0 return at `k*=20` | D0/reference competence ratio | `J_greedy - R_D0` |
| ---: | ---: | ---: | ---: |
| 1 | `0.31856608072916803` | `0.9425727649456705` | `0.07644641927083179` |
| 2 | `0.2949214680989587` | `0.8726131262675244` | `0.10009103190104113` |
| 3 | `0.27519759114583386` | `0.8142541534835998` | `0.11981490885416596` |
| mean | `0.2962283799913202` | descriptive only | `0.0987841200086796` |

Seed 3 is below the E3 card's descriptive `0.85` D0 competence line. Its raw gap is retained as an
observation but cannot be read as extra mechanism headroom; it partly reflects comparator
undertraining. Seeds 1 and 2 are competent by that line.

## Missing cells and non-equivalence

- E3 medium and large do not yet have complete trained D0 rows, so their empirical
  `J_greedy - R_D0` gaps are **missing**. Their exact `m_dur` values do not fill that empirical
  cell; they answer the separate oracle-to-oracle structural question.
- The E2 value cannot be substituted for an E3 missing cell: E2 is homogeneous at
  `(0.02, 0.02), Delta=0.4`, while E3 changes hazards and, in two rows, reward scale and best `k`.
- The headroom numbers do not say that D2, or any learner, realizes the upper reference. The frozen
  E3 paired-return and event-path rule remains the only interpretation rule for E3.
- Proposed MEI cutoffs of `5%` or `25%` have not been approved. No percentage threshold is applied,
  and no lifecycle, priority, investment, promotion, or closure conclusion is drawn.

## Decisions this intake produces

Decision 1 — whether to create another A/RECON learner run for headroom:

- **(a)** Accept the already registered structural headroom and the currently available
  same-information observed gaps; let the frozen E3 D0 invocations fill the medium/large cells in
  their ordinary sequence. Do not create a duplicate census run.
- **(b)** Freeze a new minimal A/RECON run solely for the medium/large trained generic baseline.
- **(c)** Substitute the complete E2 homogeneous gap for the missing E3 rows.

Recommendation: **(a)**. It is the smallest reversible choice, preserves the frozen E3 sequence,
and avoids both duplicate compute and host non-equivalence. Option (b) would duplicate D0 arms
already required by E3; option (c) is scientifically invalid.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**.

Provenance: `OWNER_DELEGATED`. Tier: object. No new B object, no new A/RECON science card, and no
change to the live or held E3 invocations follows from this census.

