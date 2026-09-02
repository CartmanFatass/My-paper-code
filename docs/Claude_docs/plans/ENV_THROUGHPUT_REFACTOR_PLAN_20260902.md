# Throughput refactor plan for the scenario-1 experiment loop (2026-09-02)

Written by Claude Code (Fable 5.1) after the owner asked whether the performance observations in
the review could be turned into a refactor ("能否组织重构来增加当前的实验效率"). This is an
engineering plan with two owner decisions (§6); it changes no scientific object. Numbers come from
one cProfile run on 2026-09-02, recorded in §1.

## 1. Where the time goes (measured)

Profile: `scripts/run_flexible_skill_duration_e0.py --arm off --rollouts 1 --num-envs 4
--threads 4` under `cProfile`, i.e. one 500-step rollout on 4 lanes plus one evaluation of 8
episodes on 8 lanes: 6,000 environment steps, one `agent.update`. Total 202.0 s.

| Bucket | Seconds | Share | What it is |
| --- | --- | --- | --- |
| `UAVBaseStationEnv.step` (scenario 1) | 163.5 | 81% | Python scalar channel model |
| of which `scenario1._update_channel_state` | 103.7 | 51% | 3.62 M `_compute_sinr` calls: one per (UAV, user) per step, each with a Python loop over the five interferers and per-pair cache lookups keyed by `ndarray.tobytes()` (49 M `tobytes` calls in the run) |
| of which `_get_observation` → `_get_local_users` | 58.1 | 29% | recomputes `_compute_sinr` for every (UAV, user) pair a second time instead of reading `self.sinr_matrix` |
| of which `_prime_path_loss_matrices` | 51.3 | 25% | 1.81 M scalar `_compute_path_loss_reference` calls (300 per step: 6 × 50 pairs) with `numpy` on scalars |
| `agent.update` | 25.3 | 12% | discoverer PPO 13.9 s, coordinator 7.8 s, discriminators the rest |
| `agent.step` (inference) | 4.6 | 2% | batched; not a target |
| storage, bookkeeping, imports | ~8 | 4% | |

Per lane-step the environment costs about 27 ms; the learner's inference costs about 0.8 ms per
batched step. The E0 numbers agree: at 16 lanes collection took 122 s per 500-step rollout
(15 ms per lane-step after amortising the batched inference), the update 91 s, and evaluation 61 s
for 4,000 lane-steps.

Consequence for the E-series as sized in ADR 01 (32 lanes, 500 steps, 200 rollouts): at the
measured 422 s per rollout one arm costs about 23 hours on this CPU. The environment is 57% of that
and the update 43%.

## 2. What the refactor changes, and what it does not

Target: `envs/pettingzoo/uav_env.py` and `envs/pettingzoo/scenario1.py` only. The channel model
(path loss per `channel_model`, SINR with interference or FDMA, `min_sinr` threshold, greedy
connection assignment by descending SINR with `max_connections`, observation layout) is kept as
written; only its evaluation order changes from scalar loops to array operations.

Not changed: the learner (`hmasd/`), configs, the reward definition, the observation layout, RNG
consumption (the environment's random draws are per reset and per user-movement step, none inside
the channel model), the relay scenarios (they already use the native kernel).

## 3. Phases

**P0 — reference tape and equivalence harness (before any change).** A test
`tests/uav_env_channel_equivalence_test.py` builds scenario 1 at `n_uavs = 6`, `n_users = 50`,
`episode_length = 500`, for each `channel_model` the config can select, drives it with a fixed
seeded action sequence for 2 episodes, and records per step: the SINR matrix, the connection
matrix, per-agent rewards, observations, global state. The tape is written once from the current
code to `temp/directions/flexible_skill_duration/test/uav_env_reference_tape_<sha>.npz` (local;
content sha256 recorded in the test file as the expected digest) and the test compares the live
environment against it. Assertions: connections exactly equal; SINR, rewards, observations and
state within `1e-9` absolute; the number of positions where the difference exceeds `1e-12` is
reported. This is the acceptance instrument for P1 and P2 and stays in the repo afterwards.

**P1 — vectorise the channel model.** Path-loss matrices `[n_uavs, n_users]` and
`[n_uavs, n_uavs]` computed once per step by broadcasting (distances, elevation angles, the
per-model formula); SINR for all pairs by matrix operations (interference as a row-sum over the
other UAVs' linear powers, then `log10`); `_update_channel_state` reads the matrix; the greedy
assignment keeps its exact ordering semantics (sort by SINR descending with the current tie order,
which the harness checks). The scalar path stays selectable as `channel_backend = "reference"`
(the current code, moved but not edited) and is the oracle the harness uses if the tape is lost.

**P2 — observations from the matrices.** `_get_local_users` and `_get_local_uavs` read the SINR
matrices instead of recomputing them, keeping the same ordering and threshold; `_get_observation`
assembles from the precomputed relative positions. Same harness, same tolerances.

**P3 — re-freeze the D2 fingerprint and re-time.** The D2 Phase 0 fixture
`tests/fixtures/flexible_skill_duration_d2/fingerprint_off.json` is regenerated once on the
vectorised environment with the reason recorded in the fixture's provenance and in
`D2_IMPLEMENTATION_REPORT_20260902.md` as an addendum; test 1 then guards later D2 edits as before.
All D2, corridor and integration tests must pass. The E0 timing run (`--rollouts 2 --num-envs 32`,
1 and 4 threads) is repeated and the new rate recorded next to the old one.

**P4 — the update phase (only after P3, and only if measured to matter).** With the environment
fixed the 91 s update at 16 lanes dominates. Candidates, in order of safety: thread count for the
update only (collection is Python-bound and does not benefit); removing repeated host-to-tensor
conversions per minibatch; vectorising the per-agent Python loops in the coordinator value loss.
None of these changes a formula or a minibatch order; each is checked by the fingerprint test
(bit-exact at the fingerprint configuration) or, where thread count changes float reduction order,
by an explicit tolerance and a recorded reason. Minibatch sizes and epoch counts are scientific
parameters and are not touched.

## 4. Expected effect

Vectorised, the channel model costs one `[6, 50]` and one `[6, 6]` array pass per step; the
Python overhead of the greedy assignment and observation assembly remains. Estimate: environment
step from about 27 ms to 1–3 ms per lane-step. At 16 lanes: collection from 122 s to roughly
10–20 s, evaluation from 61 s to under 10 s, rollout-plus-update from 213 s to about 105 s (2×). At
32 lanes and 200 rollouts, one E-series arm from about 23 hours to about 11 hours before P4. These
are estimates from the profile shares, to be replaced by P3's measurement.

## 5. Integrity policy

- Array operations change floating-point summation order, so P1/P2 are tolerance-equivalent to the
  scalar code, not bit-identical. The harness measures the difference; the fingerprint is re-frozen
  once with the harness numbers as the recorded reason. This is a declared numerical-precision
  change under CLAUDE.md's "state material assumptions" rule, not a silent one.
- E0's evidence stands as recorded (its manifests carry the code sha). E1 runs on the refactored
  environment; E1 and E0 are not compared on returns (E0 forbids that anyway).
- The relay scenarios' native kernel is not reused for scenario 1 in this plan: its formulas
  (LOS-probability path loss) differ from scenario 1's `free_space`/`urban`/`suburban`/`3gpp-36777`
  set, and matching them would be a scientific change. If after P3 the environment is again the
  bottleneck, a scenario-1 native kernel with the same harness is the next step.

## 6. Owner decisions

1. Accept tolerance-level equivalence (`1e-9` absolute on SINR, rewards, observations and state;
   connections exact) and one re-freeze of the D2 fingerprint with the recorded reason — or require
   bit-exactness, which rules out vectorisation and leaves only the duplicate-computation removal
   in P2 (about 29% of the environment time, bit-exact by construction).
2. Scope now: P0–P3 only, P4 after measurement — or P0–P4 in one hand-off.

## 7. Hand-off

Implementer: an Opus session on `main` (no other code line is active). Deliverables: the harness
test, the vectorised environment with the reference path selectable, the re-frozen fixture with
its recorded reason, the repeated timing run, and a report
`ENV_THROUGHPUT_REFACTOR_REPORT_<date>.md` with the harness numbers, the before/after timings, and
a could-not-verify list. The reviewer checks the harness, the fixture provenance, and that no
formula changed.
