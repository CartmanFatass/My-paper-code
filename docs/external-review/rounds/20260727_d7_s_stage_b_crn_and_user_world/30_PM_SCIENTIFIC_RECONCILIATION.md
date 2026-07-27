# PM scientific reconciliation — Stage B, CRN and user-world provenance

Ruling archived at `21_PRO_OPEN_RAW.md`. Transport facts at
`50_MECHANICAL_INTAKE_RECORD.md`.

```text
disposition = MISMATCH
launch      = NO
blockers    = 1
```

## The blocker, verified against the code rather than accepted

The ruling names one blocking item: `full_state_fingerprint` does not cover the
continuation-sensitive state R3 §C makes load-bearing, so conditions 1C, 2 and 5
are not conclusive.

**Confirmed independently, and the defect is worse than the ruling states.**

`full_state_fingerprint` iterates `sorted(dir(env))` and appends bytes for
exactly three shapes — `np.ndarray`, numeric/bool scalars, and non-empty flat
numeric lists or tuples. **There is no `else` branch.** Anything else falls
through and is never recorded. Measured against the live environment:

| Attribute | Declared type | Reaches the digest? |
|---|---|---|
| `self.routing_paths = {}` | `dict` | **No** |
| `self.user_serving_sets = [[] ...]` | list of lists — fails the `all(numeric)` guard | **No** |
| `self.active_packets = []` | list of dicts | **No** |

The aggravating fact is not the omission but the claim. The function's own
docstring asserts it covers "routing paths and channel caches, service-set
state, ... duty map and service centroids". Three of those are silently dropped.
The code states the R3 requirement and then does not implement it, which is why
a reader — including two prior review rounds — could check the docstring against
R3 and see agreement.

The second half of the blocker also holds: `EventSnapshot` fingerprints the
environment and `duty_map_at_te` only; its constructor receives neither
`duty_positions_at_te` nor `service_centroids_at_te`, both named by R3 as
continuation inputs.

Consequence, in the ruling's terms: two continuation inputs can differ while
condition 1C, mutation isolation and complete-state restoration all pass. The
guard cannot fail for the state it does not read.

## Why the tests did not catch it

The focused tests mutate `user_positions`, UAV positions and batteries — all
`np.ndarray`, all inside the covered set. They establish that the fingerprint
distinguishes worlds *for state it already covers*, which is not the R3
invariant.

This is the same failure shape as the CRN defect disclosed in Q2 of this very
round: a guard that adopts the code's narrowed binding of a term and therefore
cannot fail. That makes two instances found in two consecutive rounds on this
instrument, which is a pattern about how these tests are written, not two
coincidences.

## What was ruled, beyond the blocker

- **Q2(a) CRN repair — correct.** The `EVAL_SHARED_CANDIDATE_TOKEN` realization
  is the right reading of R2 §Replicates. CRN is required *within* a limb;
  cross-limb CRN is not required, so the `limb` field may stay in `stream_seed`.
  Explicitly *not* strengthened into counter-based exogenous randomness.
- **Q2(b) `n_select=2 / n_eval=2` stands.** The repair strengthens the floor's
  admissibility rather than weakening it. Nothing is retracted, because nothing
  was published; internal pre-repair numbers remain non-evidence.
- **Q3(a) the causal contrast survives; the probability measure does not.**
  `U*`, `T_stable`, `T_flex` are unchanged. The measure must be restated as
  topology-conditioned: `T ~ P_T`, `W ~ P(W|T)`. **No new bootstrap level** —
  the existing topology/episode hierarchy already represents it.
- **Q3(b) do not redraw the remote corner per episode.** The old behaviour was
  an ordering defect, not a randomized design. Our reading was upheld.
- **R3 §E wording must be corrected**, and this amendment is ruled here — it
  needs no further freeze round. Our "the statistical distribution remains
  unchanged" phrasing is called too broad; the effective joint distribution and
  variance decomposition did change.

## New constraint we did not ask about

The eight registered topology seeds contain **only three of the four BS-quadrant
classes**. The ensemble stays valid and needs no re-registration, but the result
is an equal-topology-weighted result over those eight, not a claim of uniform
performance across quadrants. Topology records should expose quadrant
composition, and the seed list must not be changed post hoc to balance it.

This is a reporting obligation on the eventual paper, so it is recorded now
rather than rediscovered at writing time.

## Standing of the in-flight compute

The ruling adopts the boundary the question declared: the vehicle-probe
artifacts must not become scientific evidence, margins and `U*`/`B_m` stay
unread, and the run is not pooled as a D7.S result.

Declaring that boundary *before* sending is what makes this cost nothing.

The shards keep running only because their wall clock is the one thing still
worth having and the minutes are free on a public repo. Their outputs are
`VOID_NOT_EVIDENCE`.

## What closes the blocker

Semantic, not a coding recipe: dictionaries, nested lists/tuples, sets, queues
and relevant custom-object state canonically compared or digested; routing paths
and reusable routing/channel caches covered; service-set and handover state
covered where live; packet and source-controller mutable state covered where it
can affect the continuation; duty positions and service centroids bound to event
identity; **exclusions explicit and justified**; and a test proving that changing
a nested routing/service/controller object changes the fingerprint.

Unchanged and not to be touched: direct live snapshotting, the CRN repair, the
`2/2` volume, topology seeds, episode counts, horizons, thresholds, bootstrap,
branch semantics.

The "exclusions explicit and justified" clause is the part that prevents a
repeat. `FINGERPRINT_EXCLUDED_ATTRS` already exists and is justified in
comments; the defect was in the *silent* fall-through, not in the declared
exclusion list.
