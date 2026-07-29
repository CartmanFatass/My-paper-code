# The duty map is not injective, and the audit's own inversion hides it

Date: 2026-07-29
Topology: development `20260725` only. Carries no scientific reading.
Found by: obligation C's `non-eligible incumbent moved` paired negative, which
failed to go red.

## The finding

`constructive_mixed_update`'s REJOIN branch assigns the rejoining UAV the
nearest uncovered duty **without checking whether that UAV already holds one**
(`scripts/audit_d7_s_event_aligned.py:893-902`). Three lines reproduce it with
no environment:

```python
m0 = {0: 2}                       # UAV 2 already holds duty 0
dp = {0: [0,0,100], 1: [100,0,100]}
ap = {0: [0,0,0], 2: [90,0,0]}
constructive_mixed_update(duty_map=m0, duty_positions=dp,
                          airborne_positions=ap, event="REJOIN", event_uav=2)
# -> {0: 2, 1: 2}      UAV 2 now holds two duties
```

`full_sync_set_update` cannot do this: it pops each chosen UAV out of
`remaining` (`:958`), so it is injective by construction. **The defect is
arm-specific.**

## Why it was invisible

The audit's per-step action rule inverts the duty map with

```python
uav_to_duty = {u: d for d, u in duty_map.items()}      # :2330
```

which is lossy exactly when the map is non-injective — a UAV holding two duties
keeps whichever duty dict iteration order visits last, and the other duty
**disappears**. Nobody flies to it. The duty map reports it covered; the flown
actions do not serve it. Call it a *phantom duty*.

So the map over-reports coverage, silently, and only in the arm that can produce
a double hold.

## Rate (development topology, 8 episodes x 1500 steps)

```text
steps                        12000
steps with a duplicate holder 4034   (33.62%)
check boundaries              1200
checks with a duplicate        400   (33.33%)
max duplicate excess on one map  1   (never three duties on one UAV)
episodes affected              8/8
first occurrence               ep 0 step 911
                               {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:5}
```

This is not a tail event. One check boundary in three.

## The exact mechanism — measured, not assumed

Every duplication onset in 12000 steps was the same class, with no second class
at all:

```text
duplication ONSET classification (constructive_mixed)
  LEAVE+REJOIN same step      8
  (no other class)            0
```

The path, confirmed against `update_duty_map_on_transitions`:

1. `airborne_positions` is built from `charging_after`
   (`audit_d7_s_event_aligned.py:2408-2411`). A UAV whose falling edge fires
   **this** step has `charging_after == False`, so it IS in that dict.
2. The function processes **every LEAVE first, then every REJOIN** (`:2420`,
   `:2425`).
3. The LEAVE re-match therefore has the rejoining UAV in its survivor pool and
   assigns it a duty.
4. The REJOIN loop then hands that same UAV the duty the LEAVE left uncovered.

Worked example, episode 0 step 910, `leaves=[7] rejoins=[5]`:

```text
before  {0:0, 1:6, 2:2, 3:3, 4:4, 5:1, 6:7}          7 duties covered
after   {0:0, 1:1, 2:2, 3:3, 4:4, 5:5, 6:6, 7:5}     UAV 5 holds duties 5 and 7
```

A LEAVE alone never does it. A REJOIN alone never does it. It takes both in one
step, which is why it reads as a rare coincidence and is in fact a third of all
boundaries once the state persists.

## The other arm has the mirror defect, by a different route

```text
                    steps with a duplicate    steps where a CHARGING UAV
                    holder                    still held a duty
constructive_mixed  4042  (33.68%)              0   (0.00%)
full_sync_SET          0  ( 0.00%)            291   (2.42%)
```

`full_sync_SET` cannot double-book, but it only recomputes at
`step_index % DELTA == 0` and carries the map forward unchanged in between
(`:2412-2417`). A UAV that starts charging mid-interval keeps its duty in the map
until the next check boundary, and while docked it does not fly there.

`constructive_mixed` removes the duty on the LEAVE edge immediately, so it never
shows this.

**So both arms emit phantom duties — duties the map calls covered that no UAV
flies to — by opposite mechanisms and at rates differing by more than an order of
magnitude.** `D_A = G(full_sync_SET) - G(constructive_mixed)` contrasts exactly
these two.

## Counting the phantoms directly, and what that count cannot see

Comparing the duties the map calls covered against the duties the audit's own
inversion will actually fly someone to:

```text
                    steps with a duty claimed-but-not-flown   phantoms per step
constructive_mixed  4034  (33.62%)                            always exactly 1
full_sync_SET          0  ( 0.00%)                            --

first  ep 0 step 911  {0:0,1:1,2:2,3:3,4:4,5:5,6:6,7:5}  phantom = duty 5
```

Exactly one phantom whenever there is one, which follows from the measured
maximum duplicate excess of 1.

**Do not read the `full_sync_SET` zero as "no phantoms".** This metric compares
`duty_map.keys()` against `set(uav_to_duty.values())`, so it sees only the
phantom the *lossy inversion* creates. A charging incumbent still appears in the
inversion, so the 291 charging-induced cases above are invisible to this count by
construction. The two rows measure different things and only the
`constructive_mixed` row is a phantom census.

## It is absorbing, not transient — POST-FENCE MATERIAL

**Recorded after round `20260729_d7_s_duty_map_injectivity` was dispatched at
`db7ad266`, so Pro has NOT seen this.** It does not justify a follow-up turn; it
is carried to the next touchpoint as context. Noted here so the round's archived
question and this note cannot be confused for one another.

Only **8 onsets** occur in 12000 steps, which reads as negligible until the
onsets are matched against the per-episode duplicate-step counts:

```text
ep   dup_steps   1500 - dup_steps = implied onset
 0        589    911     <- matches the directly observed onset exactly
 1        480   1020     <- onset script independently reported step 1019
 2        516    984     <- onset script independently reported step  983
 3        652    848
 4        457   1043
 5        493   1007
 6        536    964
 7        311   1189
```

Eight onsets across eight episodes is exactly one each, and in every episode the
duplicate-step count equals `1500 - onset`. Had the state ever cleared, that
count would be strictly smaller. It never is.

The two independent scripts agree to the expected one-step offset — one records
the step at which the update runs, the other counts from the following step's
pre-check.

**So every episode enters a duplicated state in its second half and never leaves
it.** The 33% prevalence is not 33% of episodes intermittently affected; it is
every episode, permanently, from roughly step 850-1190 onward.

**Why it persists is NOT yet established, and one wrong explanation is recorded
here so it does not get repeated.** I first wrote that the LEAVE re-match fails
to repair it "because it never asks whether the incoming map was injective".
That is false. With `locked_duties` empty — which is what these runs used, and
what `limb_locked_duties` gives the stable limb — the LEAVE path pops **every**
unlocked duty and re-assigns greedily with `pool.remove(best)`. That is injective
by construction, so a LEAVE should *repair* a duplicated map, not preserve it.

I then guessed that **no LEAVE fires after the onset**. Measured, and false:

```text
ep  onset  leaves_after  rejoins_after  repaired_by_leave  cleared
 0   910        9              9               0            False
 1  1019        3              3               0            False
 2   983        5              5               0            False
 3   847        3              3               0            False
 4  1042       24             24               0            False
 5  1006       18             18               0            False
 6   963       21             21               0            False
 7  1188        7              7               0            False
```

Three to twenty-four LEAVEs fire after the onset in every episode, and the state
is still never cleared.

**That is two wrong mechanisms in a row from me, both produced by reading the
code instead of measuring it.** The observation was never in doubt; only my
explanations were.

The column that matters is one I did not predict: `leaves_after` equals
`rejoins_after` **exactly**, in all eight episodes. After the onset, every LEAVE
is paired with a REJOIN in the same step. That is the same simultaneity that
creates the state in the first place, which suggests the LEAVE phase repairs the
map and the REJOIN phase immediately re-breaks it within one `step_once` — making
`repaired_by_leave = 0` a measure of the *net* step, not of the LEAVE phase.

### Measured at the intermediate point — this one is established

Replicating `update_duty_map_on_transitions`' own two-phase order (all LEAVEs,
then all REJOINs) and checking injectivity **between** the phases, over every
simultaneous LEAVE+REJOIN step in 8 episodes:

```text
dup_in   dup_after_leaves   dup_out      n
True     False              True       241
False    False              True         8
                                       ---
                                       249
```

- `dup_after_leaves` is **False in all 249**. The LEAVE phase produces an
  injective map every single time.
- `dup_out` is **True in all 249**. The REJOIN phase re-creates the duplicate
  every single time.
- The 8 rows with `dup_in = False` are exactly the 8 onsets.

**So duplication is not persistent state that nothing repairs. It is
continuously re-created, once per simultaneous LEAVE+REJOIN step.** The LEAVE
branch is correct as written; the whole defect is the REJOIN branch acting on a
map the LEAVE phase has just made injective.

This also explains the misleading `repaired_by_leave = 0` in the previous table:
that counter compared the map before and after a whole `step_once`, so the LEAVE
phase's repair was always already undone by the REJOIN phase when it looked. It
measured the net step, not the phase.

The rejoining UAV is in the LEAVE rematch pool because `airborne_positions` is
built from `charging_after`, under which a UAV whose falling edge fires this step
counts as airborne. It receives a duty there, and then the REJOIN loop gives it a
second.

Pro's prescribed repair — one injective post-transition assignment over the final
action-capable UAV set, with a rejoining UAV already assigned in the same batch
barred from a second duty — targets exactly this, and the measurement says the
LEAVE side needs no change.

## What it invalidates

1. **Obligation A's step A3.** It argued `|U_e| = |D_e|` from "`m0` is injective
   on its domain (a UAV holds at most one duty)". That premise is false for this
   source. A derangement is a permutation of a set; when two duties share a
   holder there is no permutation to speak of without first deciding what the
   treated object is.
2. **Obligation B's 1200/1200 feasibility figure.** It was computed through the
   same lossy inversion (`d7_s_r5_obligation_b_feasibility.py:80`), so in the
   ~1/3 of checks with a double hold, one duty was outside the eligibility
   accounting entirely. The number is not wrong *about the view it had*; the view
   was missing a duty.
3. **The frozen treatment domain.** Pro's R5 ruling already corrected the
   derivation to "derange the CURRENTLY COVERED duty set", because
   `constructive_mixed` leaves a duty uncovered after a LEAVE. That correction
   assumed the covered relation is one UAV per covered duty. It is not.

## What it does NOT invalidate

No registered quantity reads `len(duty_map)` as a coverage metric — the effect
reaches the result only through the actions actually flown. This is a
realization defect in the treatment arm, not a metric-reading error.

## Why no test caught it

`test_constructive_mixed_rejoin_covers_an_uncovered_duty`
(`tests/audit_d7_s_event_aligned_test.py:743`) passes
`duty_map_after_leave = {}`. With an empty incoming map the rejoiner cannot
already hold a duty, so the case that fails is unreachable from the test. The
guard cannot go red for the thing that is broken.

There is no injectivity assertion anywhere in `scripts/` or `tests/`.

## Disposition

Claim-defining. It changes what the treatment domain *is*, and the fix is a
choice between at least three semantics (reject the double hold at REJOIN;
permit it and define the derangement over holder-duty pairs; treat a phantom
duty as uncovered). That choice belongs to the next Pro touchpoint, not here.

Related: [[20260729_D7_S_THE_FULL_SYNC_ARM_CAN_HAND_A_DUTY_BACK]].
