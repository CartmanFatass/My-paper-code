# D7.S — the manifest replay gate ran, and it fails on the one assertion a manifest cannot satisfy

Your ruling ordered the Route A contract amended, the five manifest blockers
closed, a separate manifest-replay gate built, and that gate run on development
manifests over a full registered horizon. All four are done. This is the result.

**The honest headline: replay reproduced everything it is responsible for, and
assertion 6 failed for a reason that has nothing to do with replay.** I could have
made the gate green by narrowing that assertion. I did not, and whether it should
be narrowed is yours to decide.

Every measured claim is offered to be falsified. Discarding this question's framing
is a legitimate answer, including the recommendation in §5.

## 0. Provenance and confidence

`[REPO]` verifiable at `stage_commit`. `[MEASURED]` I ran it. `[MY INFERENCE]`
mine, attack first.

**Verified by re-reading source before accepting it:** every one of your six
blockers, and both of your §3 refutations. All confirmed. My "scalar trig is the
only non-portable operation" is dead, and so is my claim that Route A never
re-executes the trig.

**Verified by measurement, not by reading:** the isolation in §3. Two previous
explanations in this project came from reading code to explain a surprising
measurement, and both were wrong, so §3 measures instead.

## 1. Frozen inputs — not review surface

- Your 2026-07-30 rulings in full, including `INVALID_R4_REALIZATION` for H and
  the re-run, and that neither carries confirmatory weight.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`, `H_FLEX = 550`,
  `T_E_MAX = 950`. No threshold moves.
- `CLOUD_FLEET_ROOT_CAUSE = UNRESOLVED`, recorded exactly as you specified.
- No confirmatory population selected, generated, inspected or probed. The probe
  **refuses** any R4 topology; all work below is on `TOPOLOGY_SEED_DEV = 20260725`.

## 2. `[REPO]` What was built

Schema 2 closes B1–B5.

```text
B1  load compares an INDEPENDENTLY supplied identity, plus shapes and dtypes
B2  an absent component is refused; completeness checked against the nine
B3  the generator closure is DERIVED from the AST, never listed -- measured EIGHT
    functions where my list said five, the three missing being exactly the trig
    helpers. Configuration is derived twice over: constructor signatures across
    the MRO, union every attribute the closure reads
B4  apply runs the four rebuild calls regenerate_user_world makes, and proves
    they consume no continuation randomness
B5  save is create-once; an inventory set-hashes the population
```

`[MEASURED]` before asserting B4's no-randomness condition: **35 functions are
reachable from those four rebuild calls and none touches `np_random`**, so the
assertion is satisfiable rather than aspirational.

**18 paired negatives, each watched red** under a mutation of the exact property it
names — including one that restores the schema-1 hand list. 58 tests pass.

`scripts/d7_s_manifest_replay_probe.py` + `scripts/d7_s_manifest_replay_gate.py`
implement your eight assertions. Independence is established from the **job**, per
your amendment; `RUNTIME_DISCRIMINATORS` was not carried across. There is no
`--allow-same-runtime` and a test asserts there never will be.

**One condition you did not name, added as a [PM binding].** The gate returns
`UNTESTED` if applying the manifest replaced no component. The probe deliberately
builds with `user_world_seed=None`, so it starts from the non-identifying
construction state; if the readback agreed with a world already present, it tested
nothing.

## 3. `[MEASURED]` The result

Two independent executions, one full registered horizon, `20260725` audit ep 0.

```text
manifest_payload_hash        EQUAL      episode_world_fingerprint    EQUAL
post_roll_world_digests      EQUAL      event_conformance_digest     EQUAL
duty_map_at_te_digest        EQUAL      snapshot_state_hash          EQUAL
unit_stable_digest  EQUAL (H=139)       unit_flex_digest    EQUAL (H=550)
assertions a1-a7             PASS both  replaced_a_different_world   True both

MANIFEST_REPLAY_FAIL:pre_step_state_fingerprint
  6 of 273 attribute(s): current_graph_potential,
  last_min_station_distance_after, last_min_station_distance_before, state,
  uav_return_energy_margins, uav_return_threshold_ratios
```

`replaced_a_different_world=True` matters: each execution started from a
*different* construction-time world, so the equalities above are replay, not
coincidence. **The post-roll world digest is the one that answers your §2 warning**
— it is taken after the prefix roll, so every RPGM waypoint regeneration and every
re-entry into `np.cos`/`np.sin` during the episode is folded into it, and it is
equal.

### `[MEASURED]` Assertion 6's failure is not caused by replay

Two `build_pinned_env` calls in ONE process, identical seeds, **no manifest**:

```text
episode_world_fingerprint   EQUAL      full_state_fingerprint      DIFFERS
episode_graph_pbrs_sum      EQUAL (0.0 both)
station_occupancy / queue   EQUAL      coordinate_hash             EQUAL
```

The failing surface differs between two plain constructions. `full_state_fingerprint`
is include-by-default, so I read the differing attributes off it rather than
hypothesising: **6 of 273**, all station-distance-derived, while the charging-station
coordinates **and** the UAV positions both compare byte-equal.

### `[MEASURED]` One carrier is a stale cache, proven by making it converge

```text
as built                        7 surfaces differ
after apply_energy_profile      5   -- the two return-energy arrays converge
after a second refresh          5   -- no further change

recomputing last_min_station_distance_* from the CURRENT inputs:
  before   equal=False        after   equal=True
```

Both inputs are identical, so a differing output can only have been computed when
one of them was different. `scenario7_energy_aware.py:487-488` computes it at
`reset()`; `build_pinned_env` restores the registered coordinates **after** that,
and nothing recomputes it.

`[REPO]` This **refutes the explanation `full_state_fingerprint`'s own docstring
gives** — it blames `episode_graph_pbrs_sum`, which is `0.0` on both sides.
`current_graph_potential` does **not** converge under that recompute, so the
residue has at least two carriers and only one is localized. I record that as open
rather than folding it into the same sentence.

## 4. `[REPO]` What is NOT established

- **Cross-machine replay.** Both executions were local processes. The gate reports
  independence from `pid`, which is honest about what it proved and is not two
  provisioned runners.
- **That the residue is harmless.** The units agreed in ONE episode on ONE
  topology. `state` — the 306-dim observation — differs, and any path consuming
  observations would see it.
- **That A1 suffices.** Horizon equality held between two processes sharing one
  runtime. The question A1-vs-A2 asks is whether it holds ACROSS runtimes.
- **The `user_cluster_assignments` divergence from the previous round.** Still
  unexplained: the value is an integer written as `cluster_idx` or by an explicit
  `np_random.choice`, and both branches consume a fixed number of draws, so an
  aligned stream should not produce a differing assignment. Your §3.2 called this
  evidence the writer audit is incomplete and it remains so.

## 5. THE DECISIONS

**5a. Assertion 6 — narrow it, or repair the environment?** As written it cannot
pass: the environment carries construction state derived from unseeded OS entropy
(`scenario_base.py:328`) and a manifest defines the user world, not the whole
environment. This project has a parked item whose reactivation condition is
literally *"a result must reproduce the whole event state from registered seeds"* —
assertion 6 is that requirement, so the trigger has fired. Is the station-logistics
repair now in scope, or should assertion 6 be scoped to the surfaces a manifest can
determine? **I decline to narrow it myself**, because narrowing a gate that has
just gone red is repairing the check rather than the defect.

**5b. A1 or A2, on this evidence?** Cross-process horizon equality held, including
after the RPGM trig re-execution you warned about. That is consistent with A1
sufficing and does not establish it, because both processes shared one runtime.
`[MY INFERENCE]` I recommend A1 conditional on a cross-machine repeat, with A2 held
as the fallback if that repeat diverges — my recommendation, not a decision.

**5c. Is cross-process sufficient to proceed, or must cross-machine come first?**
Cross-machine is obtainable: commit the development manifest set and have two cloud
jobs load the same committed bytes. That is a repository addition riding an
existing job, not a new vehicle. It costs one round of latency.

**5d. Does the residue reaching `state` matter to the claim?** The per-limb units
agreed, so it did not reach primary `G` here. `state` is the observation vector.
Is a construction-dependent observation inside or outside the registered evidence
surface?

## 6. What I have not done

- Not narrowed assertion 6, and not marked the gate passing.
- Not wired the manifest into the audit path; a test still enforces that.
- Not selected, generated, inspected or probed any confirmatory topology.
- Not changed a threshold, the contract, or any historical artifact.
- Not repaired the station-logistics staleness — that changes the environment.

## 7. Required response sections

1. **5a** — narrow assertion 6, or reactivate the station-logistics repair.
2. **5b** — A1 or A2, and anything wrong with the evidence for it.
3. **5c** — proceed on cross-process, or obtain cross-machine first.
4. **5d** — whether a construction-dependent `state` is inside the claim.
5. Anything in §3 you judge false. The claim I most want attacked is that the six
   differing attributes are construction-borne and not replay-borne, because
   everything in §5 rests on it.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260730_d7_s_provenance_correction_result/21_PRO_OPEN_RAW.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260730_MANIFEST_REPLAY_GATE_FIRST_RESULT.md`
- `docs/research/designs/D7_S_WORLD_MANIFEST_REPLAY.md`
- `docs/research/designs/D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md`
- `scripts/d7_s_world_manifest.py`
- `scripts/d7_s_manifest_replay_probe.py`
- `scripts/d7_s_manifest_replay_gate.py`
- `envs/pettingzoo/scenario7_energy_aware.py`
