# D7.S event-aligned audit — conformance derivation (evidence action 1)

Zero-compute. Proves, per the frozen contract's §11.1, what is provable on
paper and by the committed focused suite (127 tests at `cf1a7af`), and names
exactly what only the proof-sized exercise (action 2) can complete. The
adversarial reviewer's measured probes of 2026-07-26 serve as negative
controls: each pre-repair failure is cited as evidence that the covering
test can actually fail.

## Constants frozen by this derivation

The contract deferred two bindings here:

1. **Canonical anonymous ordering** (flex focal tie-break, §2): **ascending
   physical UAV index.** A tie-break only; certification is unaffected.
2. **DOCK_TRIGGER_RULE** — the scripted source control's registered
   departure rule realizing G2's "latest safe station arrival":

   ```text
   t_transit         = ceil(distance_to_station / (max_speed * dt))
   E_transit_wh      = t_transit * calculate_power_consumption(max_speed, 0) * dt / 3600
   dock_trigger_ratio = E_transit_wh / battery_capacity_wh + return_reserve_ratio (0.10)
   depart when battery_ratio <= dock_trigger_ratio, evaluated fresh each step
   ```

   This is a controller implementation constant of event *generation*; the
   event *definition* remains the LEAVE lifecycle edge (§2), so a different
   safe-arrival arithmetic shifts when events occur, never what qualifies.

Also fixed by realization and recorded: `t_e` sits at the LEAVE's own step
boundary (no sub-step check cadence exists); the duty split is
`N_SERVICE_DUTIES = 6`, `N_RELAY_DUTIES = 2`, taken from the environment's
own feasibility heuristic (`estimate_heuristic_qos_feasibility`), not
invented.

## §11.1 items

**Event detection.** `check_leave_eligibility` + `roll_prefix_and_find_event`
realize §2. Tests cover a qualifying planned LEAVE and every exclusion path
(censoring at 950, occupied/queued station via
`station_occupancy_excluding_self`, cutoff/depletion, temporary failure,
off-schedule), the one-joint-event stop rule, and both certifications at
X=50 m / Y=10 / Z=139 including empty-legal-set ineligibility on **both**
limbs (the flex half was absent pre-repair — reviewer blocking defect 5 is
the negative control). Real-env event *occurrence* is action 2's to show.

**Topology restoration.** `build_topology_template` draws BS and station
coordinates from a private RNG seeded by `topology_seed`; the §9 record
(coordinates, canonical hash, seed, procedure version) is serialized by
`write_topology_record`. Tests: same seed twice → equal hashes; different
seeds → different; record round-trip. Negative control: the reviewer
measured three distinct hashes from one seed pre-repair (unseeded
construction draw). `build_pinned_env` performs the frozen order — fresh
env, episode reset, **then** coordinate restore, hash assert — and the
reviewer verified the assert catches a reordering. Episode-seed invariance
of the pinned coordinates is asserted by the same hash check on every arm
and replicate at run time; action 2 exercises it on the real env.

**Duty-map construction and distinct arms.** `constructive_mixed_update`,
`null_update`, `full_sync_set_update` are pairwise distinct **at the
registered fleet shape** (8 duties, 8 UAVs, zero idle survivors): the
hand-worked witness test reassigns a duty-holding survivor to the vacancy,
leaves exactly one duty uncovered, and shows five of eight duties differing
from `null`. Negative control: pre-repair, constructive collapsed onto null
at this exact shape (reviewer blocking defect 1) — the previous witness
used a fleet shape that cannot occur. The leaver-reassignment trap and
locked stable incumbents are separately tested.

**Legal candidate enumeration.** `legal_set_targets`: geometric dedup,
vacated-target inclusion, the exact §6 exclusion list, no reachability
exclusion, cross-duty assignments allowed — each with a failing-mode test.

**Window-local safety components.** `compute_G` hand-worked (−2/−5/−10 on
the capped field); `window_latched_counts` first-transition semantics with
the crafted recovery-recurrence schedule diverging from episode latching;
series convention pinned to H+1 rows, row 0 baseline; saturation computed
on the user-step unit with the 29/30 regime as the failing-mode case
(reviewer non-blocking finding 5 is the negative control).

**Inference layer.** `compute_t_m_bootstrap` applies the 0.10 materiality
coefficient (hand-worked); the shared topology stream is identical across
quantities with unequal event counts, with a companion test reproducing the
pre-repair divergence (reviewer blocking defect 4b); equal topology
weighting hand-worked (4b's third leg); Part-A straddling interval returns
`PART_A_CONFORMANCE_UNRESOLVED`, with confidently-worse and
genuine-equivalence cases verified (blocking defect 3 as negative control);
selection is re-run inside every resample (tested against a fixed-selection
baseline).

**Branch reachability.** `decide_branch` constructs all ten branches in the
frozen precedence, tested row by row including 8-before-9.

## Open engineering item (blocks the joint audit, not the smoke)

`main()` currently stubs the Part-A conformance inputs
(`conformance_ok=True`, `part_a_contradiction=False`); failures fail closed
by exception, so no false branch can be emitted, but branches 1 and 4
cannot yet fire from the driver. Wiring `part_a_conformance` and the
conformance-failure path into the driver is required **before** the joint
audit and will be verified against action 2's artifacts. The flex
hard-support check is a single-trip depletion bound, recorded as such.

## What action 2 must show (and this derivation cannot)

On topology 20260725, smoke scale: a real qualifying joint event exists
under `heldout_low`; the evaluator forward replay and prefix forks
hash-verify on the real env; window G accumulates nonzero components; the
JSON carries the §9 provenance block and support counts. `SMOKE_NOT_A_RESULT`
throughout; no scientific reading.
