# Freezing the event-aligned contract: the decisions neither of us made yet

Your 2026-07-26 ruling ordered, as evidence action 0, a re-registered
event-aligned D7.S source contract. The draft exists —
`docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md`, status
DRAFT_FOR_PRO_FREEZE — and transcribes every quantity your ruling fixed:
one-Δ interventions, max-over-z with split-sample, evaluator-certified
histories, H_stable=139 / H_flex=450, per-mechanism event-aligned B_m, the
G2 PBRS-free safety score as primary G, linear UCB/LCB gate contrasts,
hierarchical bootstrap over eight fresh topologies, and the branch table
with `PART_A_CONTRADICTION`.

The mandatory pre-freeze adversarial pass then did its job: the exposure is
almost entirely in what **neither the ruling nor the draft decided**, and it
concentrates in the flex limb's event machinery — which repository
arithmetic says operates with roughly 120 steps of slack on its entire
evidentiary support. Every question below is a decision that must exist in
the frozen text. Where a default is proposed, it is marked as a proposal;
the rulings are yours. After your answer the draft is amended verbatim and
frozen; nothing runs before that.

## Cluster 1 — the flex event machinery (answer in this order; later
answers depend on earlier ones)

**Q-E1 — the event anchor `t_e`, and the constant it stands on.** The
environment has no observable "in transit to charge" state:
`uav_target_stations` is set only within the 20 m capture radius and
`uav_charging` flips only at capture (`scenario7_energy_aware.py:1552-1575`).
The only departure decision in the repository lives in the superseded
harness: `dock_trigger = min(0.95, return_reserve_ratio + 0.15) = 0.25`
(`audit_d7_s_persistence_margin.py:306-310`) — registered nowhere. The
capture edge is non-unique (6–30 rising edges per episode in the ep64
record), so it cannot be "the" event.

*(a)* If you anchor `t_e` at the source-control policy's dock-rule firing:
register the trigger level. Is 0.25 correct, or should it derive from the
env's own return-reserve semantics (reserve 0.10)? Then note the arithmetic
consequence: charging from 0.25 is (0.80−0.25)·160 Wh = 88 Wh at 1000 W
≈ 317 steps, plus one mean transit leg 139 ≈ **456 ≈ the registered 450**.
Confirm 450 stands on exactly that derivation, or register the number that
stands on the derivation you choose.
*(b)* If you anchor anywhere else (capture edge, cutoff): the 450 arithmetic
fails (cutoff-anchored gives ≥ 542; departure-to-rejoin ≈ 595) — register
the replacement `H_flex` and answer Q-E3's forced consequences.

Also confirm the certifying observable set: `uav_battery_ratios`,
`uav_charging`, `uav_target_stations`, positions — nothing else exists on
the environment surface to certify transit.

**Q-E2 — the censoring rule, exactly.** The draft says a support rule is
"frozen here" and then does not state one. Proposal: an event at step `t_e`
is eligible iff `t_e <= episode_steps − H_flex`; ineligible events are
excluded from both limbs and from both calibration blocks. Confirm, or
replace with a right-censored estimator (and name it).

**Q-E3 — the initial-energy multiset, which decides flex support.** Under
the recorded drain (0.000323/step) and a 0.25 departure trigger, departure
times are (e0−0.25)/drain: initial 0.55 departs ≈ step 929 (eligible, ~121
steps of slack before the 1050 deadline); 0.60 departs ≈ 1084 (**censored
by 34 steps**); everything higher, later. The G2 *training* multiset
(0.55–0.90) therefore yields about **one** eligible flex event per episode
— and zero under a modestly lower realized drain or a capture anchor. The
`heldout_low` multiset (0.45–0.80) yields 3–4. Name the multiset for audit
and calibration episodes, and rule whether decoupling the audit from the
training distribution (by using heldout_low) is acceptable.

**Q-E4 — one event or all events.** Choose now, not per run:
*(a)* at most one pre-registered qualifying event of each type per episode —
and if so, which one (proposal: the first); or
*(b)* all qualifying events, clustered episode-within-topology in the
hierarchical bootstrap.

## Cluster 2 — controller and estimand objects

**Q-C1 — `constructive_mixed`, operationally.** The draft names it and
defines nothing. Repository fact: the superseded arm never reassigns a
vacated duty — `duty_of` is a fixed permutation and a docked UAV's duty
goes unserved (`audit_d7_s_persistence_margin.py:290-356`), contradicting
its own docstring. The registered G2 constructive control *recomputes
survivor targets at LEAVE/REJOIN* (`UAV_CHARGE_ROTATION_ROSTER_G2.md`,
source controls). Rule: (a) which duties it holds and which it renews;
(b) at a vacancy — re-cluster with k = airborne service count, reassign the
vacated duty to the best survivor, or leave it unserved; (c) is G2's
CONSTRUCTIVE_CHARGE_ROTATION the binding reference? Note `B_flex =
constructive_mixed − null` **is the value of covering the vacancy**, so this
choice is the numerator of the flex normalizer.

**Q-C2 — `B_m` generation.** Proposal to confirm or correct: source-control
episodes run under `constructive_mixed` until a certified check, then
`constructive_mixed` and `null` continue as a CRN pair from the identical
prefix. Also register the calibration-block size per topology.

**Q-C3 — the legal alternative set for SET.** Duties are audit-internal
constructs (relay posts plus k-means centroids, recomputed as users move).
Rule: the legal set is enumerated from which duty map, snapshotted when
(at `t_e`, or per check); which duties are excluded (the incumbent only, or
also infeasible-transit duties); is the set restricted to airborne UAVs;
may a service focal take a relay post; is the vacated duty itself in the
focal's legal set?

**Q-C4 — the stable certification lacks a legal-alternative clause.** If no
legal `z != z_i` exists at a certified stable check, `V_SET_stable` is
undefined. Add "at least one legal alternative exists" to the stable
certification, or define the arm's behavior on an empty legal set. Which?

**Q-C5 — the certification predicates, decidably.** "Locally optimal or
materially unchanged" and "can cover" name no metric or threshold. Users
drift at most `user_max_speed·Δ` = 150 m per Δ, which sets the natural
scale. Proposal (thresholds yours): stable = recomputed oracle target for
the incumbent's duty within X m of its current target; flex vacancy =
departure within the last Y steps; coverage = survivor transit to the
vacated duty ≤ Z steps. Set X, Y, Z.

## Cluster 3 — inference machinery

**Q-I1 — the sampling distribution of `T_m`.** `T_stable = U*_stable +
0.10·B_stable` mixes a treatment-block and a calibration-block estimate
sharing topology. Proposal to confirm: each topology resample jointly
redraws both blocks and recomputes `T_m` per resample, propagating `B_m`'s
variance and the within-topology covariance. Also register: interval type
(percentile vs BCa), sidedness, resample count (G2 registers 10,000; the
superseded script used 20,000), and the bootstrap seed rule.

**Q-I2 — replicates and the mechanism that holds `h_m` fixed.** Register
`n_select`, `n_eval`, and the seed-derivation rule. Mechanism proposal: the
environment has no snapshot API and all within-episode randomness seeds at
reset, so replicates reach `h_m` by bit-identical prefix replay under CRN,
proven by the conformance derivation, with the continuation RNG forked at
`t_e` per replicate; `E[G | h_m]` is then defined as the mean over
continuation streams so drawn. Confirm or replace.

**Q-I3 — the `PART_A_CONTRADICTION` predicate.** "Matches the mixed
constructive optimum" is a probability-zero event under noise; as written
the branch cannot fire. Proposal: an equivalence test — two one-sided tests
of |full_sync_SET − constructive_mixed| < δ·B_m at 95% — with δ set by you;
state which outcome is a diagnostic flag and which actually reopens Part A.

**Q-I4 — a resolved-negative flex limb.** If `UCB95(T_flex) < 0` with
`LCB95(B_flex) > 0`, the data affirmatively support your preserved
explanation E3 (stable value, no material flexible renewal) — a different
research redirection from "underpowered". Should that outcome carry its own
branch and payload, distinct from `SOURCE_NECESSITY_UNRESOLVED`, or is the
catch-all intended?

**Q-I5 — registration of the population and the instance.** (a) The eight
fresh topology seeds are currently an exclusion, not a population — register
the list now (proposal: 20260726+k, k = 0..7) or a deterministic generation
rule. (b) The draft never registers the environment instance; proposal:
incorporate the G2 frozen-environment block (S7-S3, n_uavs 8, episode 1500,
2 stations × capacity 1, 1000 W, rejoin 0.80) by explicit reference,
enumerating any deviation — notably the Q-E3 multiset.

**Q-I6 — budget realizability, and the absent expansion rule.** Per
certified event the SET branch needs |legal z|·n_select + n_eval
continuations plus KEEP, across two limbs, plus calibration blocks, across
eight topologies — plausibly ≥ 10× the ep64 run depending on Q-C3/Q-I2.
The draft forbids budget expansion without a pre-frozen rule and freezes
none, so the only lawful response to underpower would be permanent
UNRESOLVED. Freeze either "no expansion, ever" deliberately, or an
expansion rule now.

## Cluster 4 — binding the primary G

**Q-G1 — three bindings and a latching trap.** Components exist per step on
the environment surface, but: (a) is "return_cost" the capped
`return_constraint_cost` (cap 1.0) or the raw value? (b) confirm G is
analyzer-computed from components with the fixed weights 1/−2/−5/−10 —
never reusing `safety_reward_before_pbrs`, whose return term is dynamically
weighted; (c) `new_cutoff`/`new_depletion` are **latched once per UAV per
episode** (`cutoff_event_seen` cleared only at reset), so a window starting
at `t_e` inherits pre-window latches and undercounts recurrences — rule
whether events are episode-latched (current code) or window-latched (first
occurrence within the window, re-derived by the evaluator). These give
different G.

**Q-G2 — a non-degeneracy guard for G.** Its QoS term is the clipped ratio,
whose recorded saturation on this line is 1.0 in 7 of 8 shards — the clipped
proxy was retired on this exact line once already. Should the contract
register a mandatory non-degeneracy diagnostic (per-arm G-component variance
plus saturation fraction, with a declared consequence if the QoS term
separates nothing), so a vacuous-instrument repeat is visible inside the
frozen design rather than after the joint audit?

## Handled by the Project Manager, for confirmation only

- The draft's topology-pinning sentence was corrected to the mechanism that
  actually works (post-construction seeded re-init; construction draws are
  not seed-determined), with the conformance derivation required to prove
  seed-to-coordinates determinism. Confirm sufficient.
- Your standing Scenario-7 provenance rule now lives in `AGENTS.md`
  (*Result interpretation*), where the reuse path reads; the contract keeps
  the origin record.

## Q-final

State any dependency or reordering among your answers explicitly — in
particular where a Cluster-1 anchor choice changes a Cluster-3 budget or
Cluster-2 object — and anything in the amended draft you would override.

## Evidence to read

Repository at the stage commit, paths only.

- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md`
  the draft under freeze, as amended.
- `docs/external-review/rounds/20260726_d7_s_part_b_flex_arm_and_instrument/21_PRO_OPEN_RAW.md`
  your ruling this contract realizes.
- `docs/research/designs/D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md`
  the superseded Part B and the surviving Part A.
- `docs/research/designs/D0_CARRIER_AND_ESTIMAND.md`
  the estimand hierarchy.
- `docs/research/designs/UAV_CHARGE_ROTATION_ROSTER_G2.md`
  the frozen environment block, safety score, and constructive control.
- `scripts/audit_d7_s_persistence_margin.py`
  the superseded instrument: dock trigger, duty map, fixed permutation.
- `envs/pettingzoo/scenario7_energy_aware.py`
  charging capture, event latching, metric components.
- `envs/pettingzoo/scenario_base.py`
  construction-time topology draw, user motion.
- `docs/project/ALGORITHM_PRINCIPLES.md`
  standing contract, required in every round.
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
  standing contract, required in every round.
