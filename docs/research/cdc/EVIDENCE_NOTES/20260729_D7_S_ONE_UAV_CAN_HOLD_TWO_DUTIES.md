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
