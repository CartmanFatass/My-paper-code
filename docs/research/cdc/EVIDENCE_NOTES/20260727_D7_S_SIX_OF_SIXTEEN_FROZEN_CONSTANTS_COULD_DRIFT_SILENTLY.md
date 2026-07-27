# Six of sixteen frozen constants could be changed without a test noticing

Ninth instance, found 2026-07-27 at `287a5edc`. Unlike the first eight it was
not found by reading a test — it was found by **a sweep that needed no reading
at all**, which is the more important half of this note.

## Why the method changed

Iteration 28 closed by naming its own cost: confirming the clean items had taken
most of the reading time. The prescribed cut was to stop reading function bodies
first and instead **pull a difference set** — the production side's inventory of
conditions and reason strings against the test side's inventory of assertions —
and then read only what falls out of the difference.

Three sweeps ran under that method. Two came back clean; one did not.

### Sweep 1 — reason-string difference set: clean

Every `reasons.append(...)` literal in `scripts/audit_d7_s_event_aligned.py`
against every string asserted anywhere in the test suite. **Every reason string
is asserted somewhere.** No gap.

This one cost two self-inflicted false negatives before it was trustworthy, and
both are worth recording because they are the same shape as the defect class
being hunted:

- the extraction pattern `[a-z_]+` silently skipped `displacement_exceeds_X` —
  the capital letter ended the match early, and the tool reported the truncated
  name as covered;
- the alternation used `(?:`, which is PCRE; `grep -E` is ERE, so the whole
  quoted-literal branch matched nothing and reported success.

Both failed **silently and in the safe-looking direction**: the sweep reported
better coverage than it had measured. A tool that under-reports gaps is the
same failure as a test that cannot go red, one level up.

### Sweep 2 — exclusion-reason mutation: clean

`mutsweep.py` deleted each of the eight `reasons.append(EXCLUDE_*)` sites in
turn and ran the suite. **Eight of eight went red.** Zero unguarded.

### Sweep 3 — constant perturbation: six of sixteen unguarded

`constsweep.py` perturbed each registered constant by one step and ran the full
suite. **Six of sixteen were invisible:**

```text
REJOIN_BATTERY_RATIO   0.80 -> 1.2          an impossible ratio -- still green
DELTA                    10 -> 11
H_STABLE                139 -> 140
N_CALIBRATION_EPISODES    8 -> 9
N_AUDIT_EPISODES          8 -> 9
BOOTSTRAP_SEED   2026072601 -> 2026072602
```

Triage confirmed **all six are read on live paths** — none is dead
configuration, so none can be dismissed as harmless.

`H_STABLE` is the starkest, and it is stark for a structural reason rather than
a numerical one: **`H_FLEX` was caught and `H_STABLE` was not.** An asymmetric
guard on a symmetric pair is the signature of coverage that grew by accident
rather than by specification — nobody decided that one horizon needed pinning
and the other did not. And `H_STABLE` sets the window over which `T_stable` is
measured, so a silent change to it changes the estimand itself.

`REJOIN_BATTERY_RATIO` at `1.2` is the clearest demonstration that the sweep is
measuring absence rather than tolerance: a battery ratio above 1.0 is not a
subtle drift, it is impossible, and the suite did not notice.

## Repair

`test_every_registered_constant_matches_the_frozen_contract` pins **eighteen**
constants — the sixteen swept plus two the sweep did not reach — with expected
values taken from **the frozen contract, not from the code**. That is the whole
point: a table read out of the code would be a restatement, green under any
drift, which is instance one of this series all over again. Sources are R2
`:119-120` for the horizons, `:63` for Delta, `:38` for the rejoin ratio, `:227`
for the bootstrap seed, and R3/R2 sections 8-9 for the rest.

The docstring carries the standing instruction for whoever hits it next:

> If a value here and in the contract disagree, the code is wrong until a round
> says otherwise -- never edit this table to match the code.

`test_the_registered_topology_seed_sets_are_exactly_as_frozen` pins both
topology seed lists for the same reason: a silent edit to either changes the
population the audit draws from.

## The paired negative, run systematically

The rule requires a perturbation that drives the guard red, and this repair's
perturbation is not one hand-written case — it is **re-running the sweep that
found the gap**. `constsweep.py` after the repair:

```text
unguarded: 0 of 16
```

Every constant now caught. This is the strongest form the paired negative takes:
the instrument that measured the hole measures its closure, so the claim
"repaired" is not an argument, it is the same measurement returning a different
number.

## What the clean sweeps are worth

Two of the three sweeps found nothing, and they are reported here at the same
length as the one that did. **A sweep that only ever reports hits gives no
information about coverage** — without sweeps 1 and 2 on the record, the next
reader cannot tell whether reason strings were checked and found sound or simply
never examined. The negative result is the coverage claim.

## Running tally, nine instances

| Where | Shape | How found |
|---|---|---|
| CRN seed, fingerprint cluster | both sides same code path | external review |
| six-guard internal sweep | `f(x)==f(x)`, degenerate fixtures, unrealistic seeds | reading |
| S7 return threshold | clamp asserting its own bounds; two copies of one formula | reading |
| S7 cutoff/depletion latch | name quantifies over UAVs, fixture has one | name-as-spec |
| analyzer window latch | the above, plus asserting a diagnostic not the field `G` reads | name-as-spec |
| `certify_stable` | compound `if`, one half never varied | name-as-spec |
| `certify_flex` | chained comparison, upper bound never violated | name-as-spec |
| **sixteen registered constants** | **six perturbable with the suite green** | **mechanical sweep** |

The corollary this instance adds: **the cheapest sweep is the one that reads
nothing.** Perturbing a value and re-running is blind to intent, so it cannot be
talked out of a finding by a plausible-looking test name — which is exactly how
the first eight instances survived as long as they did.
