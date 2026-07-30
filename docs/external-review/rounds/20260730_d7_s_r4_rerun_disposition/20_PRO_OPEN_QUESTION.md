# D7.S — the R4 re-run landed, it exonerates the artifact you invalidated, and it exposed something worse

The post-repair R4 re-run is in. Two things in it need your ruling, and one of
them argues against a disposition you issued on 2026-07-29.

**Short version.** `rejoin_events = 0` across the entire R4 population. The
defective REJOIN branch never executed, the pre- and post-repair trajectories
coincide, and the branch reproduces exactly. But explaining why the *point
estimates* still moved uncovered a reproducibility failure in the world
provenance, and I think that is now the more serious of the two.

Every measured claim below is offered as a claim to falsify, not for
confirmation. Discarding this question's framing is a legitimate answer,
including the claim in §4 that your `INVALID_R4_REALIZATION` disposition should
be retracted.

## 0. Provenance and confidence

Three labels, used throughout:

- `[REPO]` — a repository fact, verifiable at `stage_commit` from the paths given.
- `[MEASURED]` — I ran it. The invocation is given so you can refuse it.
- `[MY INFERENCE]` — mine, not established. Attack these first.

**Verified by reading source, not only by tests:** the REJOIN repair's scope in
`constructive_mixed_update`, the counting site in `roll_prefix_and_find_event`,
the `contract_id` defaults in `_derived_seed` / `user_world_seed`, the charge
arithmetic in `_apply_energy_dynamics`
(`envs/pettingzoo/scenario7_energy_aware.py`), and the `controls` expression in
`episode_world_fingerprint`.

**Verified only by tests, look here first:** that the native geometry prefill in
`envs/pettingzoo/scenario_base.py` is inert — it is default-off and is *not* on
the R4 path, but it is new in this stage commit and I would rather you know it
exists than discover it.

## 1. Frozen inputs — not review surface

- Your 2026-07-29 ruling stands as issued, except where §4 asks you to revisit
  one clause of it.
- `MATERIALITY_MARGIN = 5.0`, `DELTA = 10`, `H_STABLE = 139`, `T_E_MAX = 950`.
  No threshold moves, and none is proposed.
- The frozen R4 population `20260734..20260741`. Not re-selected.
- Both shard sets stay immutable. Nothing is rewritten.
- The repair `23fecff3` itself is not under review. It is correct and it stays.
- Contract identity `D7_S_R4_ABSOLUTE_FOCAL_MARGIN`.

## 2. `[MEASURED]` The defect never fired on R4

Run `30479940700`, tag `d7s-audit-4`, stage commit `56a64c3c`, 8/8 shards. The
first R4 artifact carrying both the repair and the `roll_power` instrument
(`scripts/audit_d7_s_event_aligned.py`, counters in
`roll_prefix_and_find_event`).

```text
totals over the whole population   rejoin_events        0
                                   leave_events       109
                                   injectivity_checks 225,048
                                   steps_rolled   111,433
                                   refusals             0
```

The 225,048 checks say the guard ran; the 109 leaves say charging occurred, so
zero rejoins is not arithmetic over an empty set.

**`[MY INFERENCE]`, and the load-bearing one: R4's horizon cannot reach a
REJOIN at all.** A REJOIN is a falling edge of `uav_charging`. From
`_apply_energy_dynamics`: `charging_power_w = 1000`, `time_step = 1`,
`battery_capacity_wh = 160`, so charging adds `0.2778 Wh/step` = 0.174% of
capacity per step, and 2% to full is **~565 steps**. Charging onset sits near
step 900 and the prefix is capped at `T_E_MAX = 950`. The only other route to a
falling edge is losing station selection to contention, which did not occur
across all 109 charging entries.

If that is right, R4 is **structurally insensitive** to the source-assignment
repair, and no R4 artifact — before or after — can exercise it.

## 3. `[MEASURED]` H's episodes are the repaired code's episodes

Three independent checks, all on the frozen population:

1. H's `scripts/audit_d7_s_event_aligned.py` at `a00612ad` and the version at
   this stage commit were loaded into one process and rolled the same R4
   episodes from the same derived seeds. **Bit-identical recorded action
   prefixes**, same event step, same leave count — topologies 20260734 and
   20260739, audit block, episode 0.
2. SHA-256 over each shard's `audit_events`: **identical on 8 of 8 topologies**.
3. A structural diff of `calibration_reports` / `audit_reports`, H versus the
   re-run, on every topology, returns exactly one difference: the added
   `roll_power` field.

`[REPO]` The repair's scope is an early return inside the `event == "REJOIN"`
branch of `constructive_mixed_update`, plus a universal
`assert_partial_injection` that can only raise. `[MY INFERENCE]` With zero
rejoins and zero refusals, that code is inert, so H's trajectories *are* the
repaired code's trajectories.

## 4. DECISION ONE — does this retract `INVALID_R4_REALIZATION` for H?

You ruled the earlier R4 artifact `INVALID_R4_REALIZATION:
DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`, and I applied the same disposition
to H (`30403322062`) from the commit graph.

I now think that was wrong for H, and I want to be explicit that the error was
partly mine and not an inheritance of yours: my own probe
(`scripts/d7_s_r4_rejoin_exposure_probe.py`) derived its seeds **without**
`contract_id`, so it rolled R3-namespace episodes at R4 topology coordinates —
every derived seed different — and reported `R4_REJOIN_PROBE_FIRED` about
episodes no R4 artifact contains. That verdict is withdrawn and the probe now
refuses the wrong namespace.

Ruling needed, and please treat 4a and 4b separately:

- **4a.** Does the §3 measurement retract the invalid-realization disposition for
  H specifically?
- **4b.** Does §2's structural argument extend the retraction to the *earlier*
  R4 artifact you invalidated — i.e. was that clause of your ruling resting on a
  mechanism that R4's horizon cannot reach? I am not asserting this; I am
  reporting that the arithmetic points at it and asking whether it holds.

## 5. `[MEASURED]` The point estimates moved, and that is the real problem

Same pooler (unchanged since H, `git log a00612ad..HEAD` on it is empty), H's
shards re-downloaded and re-pooled so only the run varies:

```text
                       H          re-run
branch                 PART_A_CONTRADICTION   (identical)
limb_states            stable AFFIRMATIVE_NONMATERIAL / flex UNRESOLVED (identical)
d_a_point              0.4839     0.5108
u_star_stable_point    -1.0920    -0.9790
u_star_flex_point      -0.1644    -1.0662
```

If the focal events are bit-identical, these should be too. Running that down:

**Same pinned topology, same user-world seed, three different worlds.** Topology
20260736, calibration episode 0. Identical `pinned_coordinate_hash`
(`cd081d5c...`), identical `user_world_seed` (`7782383802093937592`), identical
`n_users`, and `seed_controls_generation = True` on every side:

```text
local (numpy 1.26.3, python 3.10.20)   d700a69e...
H            (30403322062)             b5007214...
re-run       (30479940700)             6307c329...
```

Between the two cloud runs this affects **3 of 8 topologies** (20260736, 20260739,
20260740) on nearly every episode; the other five are identical.
`requirements_d7s_audit.txt` hard-pins `numpy==1.26.3` and `scipy==1.15.2`, and
the workflow pins python 3.10, so it is not dependency drift.

Ruled out by measurement, each by a separate check: code change (the fingerprint
function returns the same value under H's module and this one), construction
order, `PYTHONHASHSEED`, global RNG state, and the pooler (re-pooling reproduces
every field exactly). `[MY INFERENCE]` What is left is construction-time state
that varies across machines, and `ubuntu-latest` is not one machine.

**`[REPO]` The flag that should have caught this asserts more than it tests.**
`episode_world_fingerprint` in `scripts/audit_d7_s_event_aligned.py` documented
`seed_controls_generation = True` as "rebuilding this episode at the same pinned
topology and the same `user_world_seed` reproduces this fingerprint", while
computing `int(applied) == int(seed_value)` and non-null — a seed-*application*
witness. Both runs report `all_seed_controlled = True` over 128/128 episodes
while disagreeing about three topologies' worlds. I have corrected the
documentation to what it computes and pinned the distinction in
`tests/episode_world_provenance_claim_test.py`. I have **not** changed any
computed value, and `component_digests` was added so the next disagreement is
localizable to one array instead of requiring this investigation again.

`[MY INFERENCE]` What it touches: `selection_diagnostic` (all eight; the re-run's
flex selection is markedly more concentrated — 20260739 flex[0] HHI 0.235 →
0.884) and the point estimates above. What it does not touch: focal events,
branch, limb states, support, conformance, `invalidated_pairs`, topology hashes.

## 6. DECISION TWO — can a conclusion-bearing artifact have irreproducible point estimates?

The re-run is mechanically clean, post-repair, whole-population, passed
`r4_freshness_sentinel` as a hard gate, and reproduces H's branch and both limb
states. Its point estimates are not bit-reproducible across machines.

- **6a.** Does it carry the R4 conclusion as it stands?
- **6b.** If not, what property is missing — bit-reproducibility of the point
  estimates, or something weaker such as a demonstrated interval that contains
  both runs' estimates?
- **6c.** Two runs agreeing on branch and limb states while disagreeing on point
  estimates: is that a replication that *strengthens* the conclusion, or is
  agreement-under-different-worlds evidence that the branch is insensitive to
  something it should be sensitive to?

I do not have a view I trust on 6c and I am not going to manufacture one.

## 7. DECISION THREE — severity of the reproducibility defect

Disclosure in the paper; a repair blocking any published R4 claim; or grounds to
re-scope the provenance contract so it claims only within-run world identity.

If it is a blocking repair, the natural next step is to find which array moves —
`component_digests` now makes that a two-artifact diff rather than an
investigation — but locating it is not the same as being able to fix it, and I
would rather you scope that than have me guess.

## 8. What I have not done

- Not re-run anything on the R4 population. No new formal compute.
- Not rewritten any shard JSON or any pooled artifact.
- Not touched a threshold, the population, or the contract.
- Not attempted to make the fingerprint portable.
- Not integrated the native geometry kernel into any R4 path — it is default-off
  and no production path calls it.
- Not decided whether round 4 closes. That is 6a.

## 9. Required response sections

1. **4a** and **4b**, separately — H's disposition, and whether the earlier R4
   artifact's disposition is affected.
2. **6a**, and **6b** if 6a is no.
3. **6c** — replication, or insensitivity.
4. **Decision three** — severity, with the scope of any repair you require.
5. Anything in §2, §3 or §5 you judge false. The horizon arithmetic in §2 is the
   claim I would most like attacked, because everything in §3 depends on it.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_R4_RERUN_CLOSES_THE_INJECTIVITY_CHARGE.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260729_H_RETURNED_AND_CANNOT_CLOSE_ROUND_4.md`
- `scripts/audit_d7_s_event_aligned.py`
- `scripts/d7_s_r4_rejoin_exposure_probe.py`
- `scripts/pool_d7_s_event_aligned_shards.py`
- `tests/episode_world_provenance_claim_test.py`
- `tests/audit_d7_s_roll_power_test.py`
- `envs/pettingzoo/scenario7_energy_aware.py`
- `requirements_d7s_audit.txt`
