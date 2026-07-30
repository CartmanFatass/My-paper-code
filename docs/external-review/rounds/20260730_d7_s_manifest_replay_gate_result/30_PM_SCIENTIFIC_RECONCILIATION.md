# Reconciliation -- 20260730_d7_s_manifest_replay_gate_result

Ruling: `21_PRO_OPEN_RAW.md`, 19708 chars, stage commit
`a666b86caab06990d931ae346b637617ad6993c1`. Transport facts:
`50_MECHANICAL_INTAKE_RECORD.md`.

## What was decided

```text
5a  narrow assertion 6, or repair the environment
      REPAIR THE ENVIRONMENT. Retain complete identity; evaluate it at the ACTUAL
      first-action boundary, which is after the energy permutation, not before.
5b  A1 or A2
      NEITHER IS FROZEN. A1 is the first candidate to test; A2 is the mandatory
      fallback. A conditional decision rule is frozen instead -- see below.
5c  is cross-process enough
      NO. A corrected CROSS-MACHINE replay must pass before A1 is selected or the
      manifest enters the audit path.
5d  is a construction-dependent `state` inside the claim
      YES. It is inside the registered evidence surface and cannot be exempted.
```

The smallest result, in the ruling's own words:

```text
MANIFEST_WORLD_REPLAY_SUPPORTED_ON_THE_EXERCISED_PATH
but
ENVIRONMENT_PRESTEP_CANONICALIZATION_NOT_ESTABLISHED
MANIFEST_REPLAY_NOT_CERTIFIED
```

The conditional rule for 5b is frozen now, before the evidence that resolves it:

```text
corrected cross-machine A1 gate passes            -> select A1
corrected gate first diverges in an exogenous
  continuation trajectory                         -> select A2
gate incomplete, or post-initialization
  generation never exercised                      -> A1 vs A2 stays UNTESTED
```

## What I got right, and it is the part worth keeping

Declining to narrow assertion 6 was correct, and the ruling's reason is stronger
than mine. I argued that narrowing a gate which has just gone red repairs the check
rather than the defect. The ruling adds the part I did not see: `state` is a
**public decision-time input** -- Scenario 7's energy observation contains
`uav_return_threshold_ratios` and `uav_return_energy_margins`, and both are also
appended to the global state. So

> A provenance repair that certifies only the scripted controller while leaving the
> policy input construction-dependent would not certify the source for the next
> research stage.

That reaches D7.3, not just D7.S. Had I narrowed the assertion, the gate would have
gone green on a defect that survives into the learned-policy work.

## Where I was corrected -- five places

### 1. "All station-distance-derived" was too narrow

The ruling: `current_graph_potential` is a graph-service potential computed from
communication, user/UAV geometry and backhaul capacity, not from station distance;
`state` is a composite cache. There are **at least two stale initialization
families**, not one. My own measurement already showed `current_graph_potential`
refusing to converge under the station recompute -- I recorded that as open and
then wrote the summary sentence as though it did not exist. The characterisation
contradicted my own data.

### 2. "Construction-borne, not replay-borne" needed qualification

> The manifest payload does not create these values, but the current manifest
> application path fails to canonicalize or replace construction-derived state that
> remains live at the pre-step boundary. Replay is exonerated as the source of the
> original bytes. It is not exonerated as a complete evidence-population
> reconstruction mechanism.

This is the correction I would least have arrived at alone. I proved where the bytes
came from and stopped, when the question was whether the mechanism is complete.

### 3. Assertion 6 was firing at a state that is never stepped from

The probe fingerprints immediately after manifest application, **before**
`apply_energy_profile`. Two of the six mismatches converge on the formal path
afterwards. So two of my six reported differences were an artifact of measuring at
the wrong boundary. Moving the assertion is not narrowing it.

### 4. The a8 gate is not fail-closed

```python
if field not in ha and field not in hb:
    continue
```

A field absent on both sides is skipped, and `snapshot_state_hash=None` on both
sides compares equal. **Absence is `UNTESTED`, not equality** -- the same defect
class as the two-outcome generator gate I built the three-outcome one to avoid, and
I reintroduced it one layer down.

### 5. B5 is not closed, and my own test concealed it

The inventory's `set_hash` is computed only from `relative_dir=payload_hash`; it
does not cover identity, layout or component digests. And
`verify_manifest_inventory` reloads what the inventory names without scanning disk
for unlisted extras.

The sharper part: my test `test_an_added_episode_is_caught_by_the_set_hash`
compares a **rebuilt** inventory against the frozen one and never calls the
verifier. It is green, it is not wrong about what it asserts, and it left the
module docstring's claim -- that a deleted or added episode is caught -- standing
without support. **A test that asserts something true adjacent to the claim is how
an overclaim survives review.**

### 6. Two gaps in the evidence I did not name

- `post_roll_world_digests` is captured after the prefix event search, so it covers
  RPGM transitions **before** certification, not the trajectories inside each 139-
  and 550-step continuation fork. The unit digests prove estimand-output equality,
  which is weaker than trajectory equality: two divergent exogenous trajectories can
  produce equal aggregates.
- **No liveness witness.** The horizon was long enough to permit waypoint and
  cluster-target regeneration, but nothing records whether any post-initialization
  trigonometric writer actually fired. If they all stayed dormant, the equality
  leaves the exact A1-versus-A2 risk untested -- which is this project's own
  standing trap, `a rate is evidence only if the mechanism fired`, and I walked into
  it while holding the note that names it.

## What is NOT retired by this failure

Route A, the R4 absolute margin, the focal estimands, the hierarchical inference,
R30, D7.3, D8. The smallest failed unit is:

```text
final registered topology/world/energy inputs
  x derived environment initialization
  x complete pre-action state identity
```

## The environment change is now in scope

The ruling authorizes it explicitly, and gives the reason it is not a rescue: the
historical R4 artifacts are already invalid, no adverse valid result is changed, no
threshold or population or branch moves, and fresh evidence would use a new,
explicitly corrected environment realization.

**The repair must NOT be the six observed fields.** Verbatim:

> Do not repair the six observed fields individually and assume the list is
> exhaustive. The same initialization barrier should own the invariant.

That is the third time in a week this project has been bitten by a hand-listed set,
after the generator-function tuple and the configuration-parameter subset. The
barrier must derive its recompute set.

## Next action -- the ruling's §8, unmodified

```text
1  freeze the true first-action initialization order
2  canonicalize every derived state from the final topology, manifest and energy
3  move assertion 6 to that boundary
4  make a8 fail closed on missing fields
5  persist lossless exogenous trajectory digests through stable and flex
6  add a liveness witness that post-initialization regeneration was exercised
7  rerun locally
8  then run the SAME COMMITTED development manifest on two independent cloud jobs
```

Only a corrected cross-machine `MANIFEST_REPLAY_PASS` may select A1 and release the
deterministic fresh-population rule for application.

## Standing constraints reaffirmed

```text
the manifest is NOT wired into a conclusion-bearing path        held
no confirmatory population instantiated, generated or inspected held
the successor selection RULE stays frozen; its APPLICATION held
no formal compute authorized
```

The ruling sharpens the population distinction usefully: the ascending rule plus
the exclusion list and `K = 8` already **determines** the eventual seeds, so the
line that matters is not selected-versus-unnamed but

```text
precommitted and uninstantiated   versus   constructed, generated or inspected
```

which is exactly what the probe's R4 refusal enforces.

One documentation correction ordered: the successor-population document's §1 still
quotes the retired **ratio** estimand while saying the R4 absolute-margin contract
carries the gates. Contradiction, not a threshold change; removed.
