# SCDMP D6 B01 source-law clarification (2026-09-04)

- Object: `SCDMP-D6-CROSS-K-Q-SHARING-B01`
- Decision tier: object
- Provenance: `OWNER_DELEGATED`
- Timing: before implementation, smoke, cost measurement or scientific observation
- Scientific effect: fixes one omitted finite-population coordinate; all other frozen fields are
  unchanged

## Gap and direct technical observation

CM stopped before editing because the existing native reset requires `pre_event_q` to be exactly
`0` or `1`, while the frozen card had fixed the two source streams, their `COMMON=0` action and
their `k` clocks but not that reset coordinate. Direct inspection of the current native source
path shows that reset installs the bit before prefix transitions; HR/RH composition later
overwrites post-event `q`, while persistent prefix consequences can make the reachable public-state
bytes differ. Therefore silently selecting a value in implementation would select part of the
scientific population.

The stopped B01 object used a prospectively drawn six-cell `q_by_cell` checkerboard for its own
source population. That artifact and rule are excluded from D6. The existing treatment-common
reset helper for ordinary native workload lanes uses the literal `0`. No D6 state, tape, learner,
optimizer, cost measurement or result existed when this gap was found.

## Options, recommendation and decision

1. **(a), recommended:** use literal `pre_event_q=0` for both source streams and every candidate
   prefix renewal.
2. **(b):** use literal `pre_event_q=1` everywhere, an equally fixed but otherwise arbitrary mirror.
3. **(c):** balance, draw or key the bit by stream, duration, target or tape, adding another
   population factor and potentially confounding source-stream duration with the hidden prefix law.

Recommendation: (a). It is the smallest fixed one-cell source law, matches the existing
treatment-common reset path, does not import the stopped B01 checkerboard and leaves duration as
the only intentional difference between the two source clocks. The literal consumes no RNG
address. Native HR/RH event composition continues to overwrite post-event `q`; accumulated prefix
consequences remain part of the public state.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** The card is clarified and
re-frozen before implementation. This action is reversible before launch and changes no result
rule, treatment, comparator, seed, budget, estimand, branch or claim ceiling.

## Result boundary

This clarification is card closure, not an experiment or diagnostic. It produces no D6 polarity,
does not pass the action-relevance gate and does not consume an evidence object. CM may resume only
from the committed clarified card.
