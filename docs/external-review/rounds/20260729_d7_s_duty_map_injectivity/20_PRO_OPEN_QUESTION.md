# D7.S — both arms of D_A fail to realize their own semantics, and I need the treatment domain redefined

A paired negative that could not go red found this. Obligation C's "non-eligible
incumbent moved" mutation was a no-op three times, because the two duties it
swapped were held by **the same UAV**.

**The decision I need is §5.** Everything before it is evidence, and every
measured claim in it is offered as something to falsify, not as progress.

Discarding this question's framing is a legitimate answer.

## 1. Frozen inputs — not review surface

- Your R5 ruling in full: one-sided falsification control; `V_D <= V*_notP`;
  equivalence refutes necessity while materially-worse does not establish it;
  the R4-style "full-sync worse => Part A passes" rule is not retained.
- Your R4 ruling: 5b(ii) INSTRUMENT VERDICT. `PART_A_CONTRADICTION` stands as
  emitted, `MATERIALITY_MARGIN = 5.0` is sound, and the named defect was the
  Part-A CONTROL failing to exclude incumbents.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`. No threshold moves,
  no sign flip, no clipping.
- The six-condition eligibility definition and the four-way `EXPOSURE_OK`
  conjunction, both as you ruled them.
- The eight R4 topologies are observed and may never carry a successor
  confirmatory result.
- D7.3 and D8 remain blocked. Nothing here asks to unblock them.

## 2. Provenance

**Repository fact** unless marked. `[INFERENCE]` marks my own reading, which is
not a result.

Everything in §3 and §4 is reproduced from the development topology
`TOPOLOGY_SEED_DEV = 20260725`, which carries no scientific reading. No
conclusion-bearing compute was spent and none is requested here.

## 3. The finding — repository fact

### 3.1 The treatment arm can put one UAV on two duties

`constructive_mixed_update`'s REJOIN branch assigns the rejoining UAV the
nearest uncovered duty **without checking whether that UAV already holds one**
(`scripts/audit_d7_s_event_aligned.py`, the `elif event == "REJOIN"` branch).
Three lines reproduce it with no environment at all:

```text
duty_map        {0: 2}          UAV 2 already holds duty 0
REJOIN(uav=2)
result          {0: 2, 1: 2}    UAV 2 now holds two duties
```

`full_sync_set_update` deletes each chosen UAV from `remaining` as it assigns,
so it is injective by construction. **The defect exists in exactly one of the
two arms `D_A` contrasts.**

### 3.2 The audit's own action rule then hides it

`scripted_source_actions` inverts the duty map with
`uav_to_duty = {u: d for d, u in duty_map.items()}`. That inversion is lossy
precisely when the map is non-injective: the UAV keeps whichever duty dict
iteration order visits last, and the other duty **disappears**. No UAV flies to
it. The duty map still reports it covered.

I call that a *phantom duty* below. Which duty becomes the phantom is decided by
dict insertion order — deterministic, but not a modelled choice.

### 3.3 Rate — 8 episodes x 1500 steps, development topology

```text
steps                             12000
steps with a duplicate holder      4034   (33.62%)
check boundaries                   1200
check boundaries with a duplicate   400   (33.33%)
max duplicate excess on one map       1   never three duties on one UAV
episodes affected                   8/8
first occurrence                    ep 0 step 911
```

One check boundary in three. Interventions launch at check boundaries, so
`[INFERENCE]` roughly one intervention window in three begins from a map
carrying a phantom duty.

### 3.4 The mechanism, measured rather than assumed

Every onset in 12000 steps fell in one class, with no second class at all:
`LEAVE + REJOIN in the same step`, 8 of 8.

1. `airborne_positions` is built from `charging_after`, so a UAV whose falling
   edge fires **this** step is in it.
2. `update_duty_map_on_transitions` processes every LEAVE first, then every
   REJOIN.
3. The LEAVE re-match therefore has the rejoining UAV in its survivor pool and
   gives it a duty.
4. The REJOIN loop then hands the same UAV the duty the LEAVE left uncovered.

Episode 0 step 910, `leaves=[7] rejoins=[5]`:

```text
before  {0:0, 1:6, 2:2, 3:3, 4:4, 5:1, 6:7}
after   {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:5}   UAV 5 holds duties 5 and 7
```

A LEAVE alone never does it; a REJOIN alone never does it.

### 3.5 The control arm has the MIRROR defect, by a different route

```text
                    steps with a duplicate   steps where a CHARGING UAV
                    holder                   still held a duty
constructive_mixed  4042  (33.68%)             0   (0.00%)
full_sync_SET          0  ( 0.00%)           291   (2.42%)
```

`full_sync_SET` cannot double-book — but it recomputes only at
`step_index % DELTA == 0` and carries the map forward unchanged in between, which
you ruled correct for "reassigns every duty at each check". A UAV that starts
charging mid-interval therefore keeps its duty in the map until the next
boundary, and while docked it does not fly there.

`constructive_mixed` drops the duty on the LEAVE edge immediately, so it never
shows this.

**Both arms emit phantom duties, by opposite mechanisms, at rates differing by
more than an order of magnitude.** I did not go looking for this; it came out of
the same diagnostic and I am reporting it because it bears on §5(b).

Counting the phantoms directly — duties the map calls covered against duties the
audit's own inversion will fly someone to:

```text
                    steps with a duty claimed-but-not-flown   phantoms per step
constructive_mixed  4034  (33.62%)                            always exactly 1
full_sync_SET          0  ( 0.00%)                            --

first  ep 0 step 911  {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:5}  phantom = duty 5
```

**That `full_sync_SET` zero does not mean "no phantoms", and I do not want it
read that way.** The metric compares `duty_map.keys()` against
`set(uav_to_duty.values())`, so it sees only the phantom the lossy inversion
creates. A charging incumbent still appears in the inversion, so the 291
charging-induced cases are invisible to this count by construction. Only the
`constructive_mixed` row is a phantom census; the two rows measure different
things.

### 3.6 It was present in the R4 confirmatory artifact

Both the REJOIN branch and the lossy inversion are present verbatim at
`1b17dfb0`, the stage commit of the R4 formal result (run `30289161086`, tag
`d7s-audit-2`). This is not a defect introduced after that result.

## 4. What I believe it costs, offered as claims to falsify

1. **Obligation A's step A3 is invalid.** I derived `|U_e| = |D_e|` from "`m0` is
   injective on its domain — a UAV holds at most one duty", then restricted an
   injection to a preimage. The premise is false for this source. I do not think
   the conclusion is rescuable by a smaller edit, because a derangement is a
   permutation of a set and there is no set to permute until the ownership
   relation is pinned down.
2. **Obligation B's 1200/1200 feasibility count was computed through the lossy
   inversion.** In the ~1/3 of checks with a double hold, one duty was outside
   the eligibility accounting entirely. The count is not wrong about the view it
   had; the view was missing a duty.
3. **`[INFERENCE]` R4 contrasted two arms, neither of which realizes its stated
   semantics.** `D_A = G(full_sync_SET) - G(constructive_mixed)` is a direct
   contrast of exactly the two. You already ruled the *control* defective for not
   excluding incumbents. The *treatment* arm can double-book a UAV and silently
   drop a duty. I am not claiming this changes the R4 verdict — I am claiming I
   cannot tell, and that it is your call and not mine.
4. **What it does NOT touch:** no registered quantity reads `len(duty_map)` as a
   coverage metric. Step metrics come from `env.step`'s `infos`. The effect
   reaches any result only through the actions actually flown.

## 5. THE DECISION

**What is the treatment domain, given that the incumbent relation is not
injective?** The dependent branches:

**(a) Is the double hold a realization defect or a legitimate state?**

- **(a1) Defect.** REJOIN must refuse a UAV that already holds a duty. Then:
  does the repair change `constructive_mixed`'s behaviour enough that the R4
  artifact no longer describes the arm it names, and if so what is R4's status?
- **(a2) Legitimate.** Then the derangement is not a permutation of duties and
  A3 needs replacing outright. Over what object is it defined — holder-duty
  pairs, the flown duty set, something else?

**(b) Whichever of (a1)/(a2) holds — is the phantom duty covered or uncovered?**
Your R5 ruling already narrowed the domain to the *currently covered* duty set
because `constructive_mixed` leaves a duty uncovered after a LEAVE. That
correction assumed one UAV per covered duty. If a duty nobody flies to counts as
covered, the treated set includes a duty the source never serves; if it counts
as uncovered, "covered" must be read off the flown targets rather than off the
map, and the two definitions disagree at a third of all boundaries.

**(c) Do obligations A and B reopen, and does anything already closed reopen
with them?** I have marked A3 invalid and left B's numbers standing with the
defect named. I have not decided either.

## 6. What I did and deliberately did not do

Recorded, not repaired — the repair is a choice between distinct semantics and
that choice is scientific.

- The property is asserted as a **strict xfail**
  (`test_rejoin_never_gives_one_uav_a_second_duty`), so it turns red the moment
  the defect is fixed without updating the mark, and it can never pass by
  accident.
- Its paired positive (`test_full_sync_set_update_is_injective_by_construction`)
  locks the arm asymmetry.
- Obligation B's inversion is left lossy **on purpose** and commented as such,
  so the probe keeps seeing the duty set the source actually flies rather than a
  repaired one.
- Obligation C now scores an unbuildable negative as `UNCONSTRUCTIBLE` with its
  reason instead of laundering it into either the caught or the missed column.
  The gate stays red:

```text
deranged checks 450, same-support pass 450, refused 0

derangement takes an uncovered duty    caught= 44 missed=0 unconstructible=0  clean=True
non-eligible incumbent moved           caught=136 missed=0 unconstructible=3  clean=False
covered-duty count shrinks             caught=450 missed=0 unconstructible=0  clean=True
charging decision altered              caught=450 missed=0 unconstructible=0  clean=True
ineligible UAV's action changed        caught=258 missed=0 unconstructible=0  clean=True

OBLIGATION_C_CHECKS_PASS=False
```

  So the witness has no demonstrated hole — 136 caught, 0 missed on that same
  mutation. What blocks C is the source state, not the witness. Had those three
  been scored as passes (the tempting reading, since the witness genuinely
  reported correctly), a 33%-prevalence non-injective duty map would still be
  invisible.

## 7. Required response sections

1. The (a) branch you take, and the object the derangement is defined over.
2. The (b) ruling on phantom duties.
3. The (c) disposition for obligations A and B, and for the R4 artifact.
4. Anything in §3 or §4 you judge false.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `scripts/audit_d7_s_event_aligned.py`
- `scripts/d7_s_r5_obligation_a_proof.py`
- `scripts/d7_s_r5_obligation_b_feasibility.py`
- `scripts/d7_s_r5_obligation_c_same_support.py`
- `tests/audit_d7_s_event_aligned_test.py`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_D7_S_ONE_UAV_CAN_HOLD_TWO_DUTIES.md`
- `docs/research/designs/D7_S_R5_OBLIGATION_A_SUPPORT_DERIVATION.md`
- `docs/research/designs/D7_S_R5_OBLIGATION_B_SOURCE_FEASIBILITY.md`
- `docs/research/designs/D7_S_R5_EXPOSURE_CERTIFIED_DERANGEMENT_CONTROL.md`
