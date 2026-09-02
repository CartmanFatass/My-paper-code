# D2 implementation report — policy-based interruption on the HMASD base route

Written 2026-09-02 by the implementing session that continued from the Phase 2 pause described in
`D2_EXECUTION_HANDOFF_20260902.md`. Specification: `D2_IMPLEMENTATION_PLAN_20260902.md` (the plan)
against `ADR_01_D2_POLICY_INTERRUPTION.md` (revision 3, accepted) and Part III of
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`. Phases 0–2 were delivered by the previous
session; this report covers Phases 3–8 and the whole object's acceptance evidence.

Nothing in this report is experimental evidence. E0 and later are the owner's.

---

## 1. Status

| Phase | Status | Commit | Diff stat |
| --- | --- | --- | --- |
| 0 — baseline fingerprint | done (previous session) | `307992fe` | — |
| 1 — configuration | done (previous session) | `a85fe706` | — |
| 2 — coordinator API | done (previous session) | `368206861` | — |
| 3 — rollout logic | done | `c3b49f50c` | `hmasd/agent.py` +468 −0 |
| 4 — storage | done | `4087819a7` | `hmasd/agent.py` +218 −2; `hmasd/utils.py` +163 −0 |
| 5 — advantages | done | `e234201ad` | `hmasd/utils.py` +110 −2 |
| 6 — update | done | `e4484efc1` | `hmasd/agent.py` +271 −1; `hmasd/utils.py` +59 −0 |
| 7 — discriminator age | done | `2088a1e4d` | `hmasd/agent.py` +124 −16; `hmasd/networks.py` +47 −11 |
| 8 — tests | done | `5224590d8` | `tests/flexible_skill_duration_d2_test.py` +637 −11 |
| report | this file | (last commit) | — |

No phase was blocked. Files touched across Phases 3–8: `hmasd/agent.py`, `hmasd/utils.py`,
`hmasd/networks.py`, `tests/flexible_skill_duration_d2_test.py`. `config_1.py` was already complete
from Phase 1 and needed no further change. No file outside the plan's scope was created or modified.

Boundary verification before starting (handoff "Operating notes"): `git status --porcelain` limited
to `config_1.py`, `hmasd/networks.py`, `hmasd/agent.py`, `hmasd/utils.py`,
`tests/flexible_skill_duration_d2_test.py` and `tests/fixtures/flexible_skill_duration_d2/` was
empty, and test 1 passed (`1 passed, 14 warnings in 7.99s`).

---

## 2. Phase 0 fingerprint

`tests/fixtures/flexible_skill_duration_d2/fingerprint_off.json`

- canonical-JSON sha256 (the value test 1 compares):
  `3c525b9c3d26ef0385231c660f25a962eccdee87103feb39a4fc361dd225d937`
- raw file sha256: `6ba55c2eb310aa011f34933a1bc79566029a2db2dd2d461c18472ca0d7cf30b4`

Test 1 was re-run after every phase commit and passed every time. The fixture was never
regenerated after a D2 edit.

---

## 3. Tests

Command (explicit interpreter, isolated basetemp):

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -v `
  tests/flexible_skill_duration_d2_test.py `
  --basetemp C:/Projects/HMASD/temp/pytest_d2_policy_interrupt -p no:cacheprovider
```

Output (verbatim; warning summary elided, it is matplotlib/pyparsing deprecation noise):

```
platform win32 -- Python 3.10.20, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe
rootdir: C:\Projects\HMASD
collecting ... collected 10 items
tests/flexible_skill_duration_d2_test.py::test_1_off_mode_matches_phase0_fingerprint PASSED [ 10%]
tests/flexible_skill_duration_d2_test.py::test_1b_off_mode_allocates_no_d2_state PASSED [ 20%]
tests/flexible_skill_duration_d2_test.py::test_2_d0_matches_off_boundaries_and_target_scale PASSED [ 30%]
tests/flexible_skill_duration_d2_test.py::test_3_infinite_costs_permit_no_pre_cap_switch PASSED [ 40%]
tests/flexible_skill_duration_d2_test.py::test_4_zero_cost_samples_every_live_agent PASSED [ 50%]
tests/flexible_skill_duration_d2_test.py::test_5_segment_lengths_partition_live_steps PASSED [ 60%]
tests/flexible_skill_duration_d2_test.py::test_6_ordered_replay_covers_sampled_positions_only PASSED [ 70%]
tests/flexible_skill_duration_d2_test.py::test_7_team_decision_closes_every_agent_segment PASSED [ 80%]
tests/flexible_skill_duration_d2_test.py::test_8_shapes_targets_and_normalized_ages PASSED [ 90%]
tests/flexible_skill_duration_d2_test.py::test_9_trigger_path_draws_no_rng PASSED [100%]
====================== 10 passed, 14 warnings in 24.32s =======================
```

Summary line of the `-q` run used as the standing check: `10 passed, 14 warnings in 29.87s`.

The plan specifies nine tests. The file contains ten test functions because invariant 1 is split:
test 1 is the fingerprint comparison, test 1b is the plan's second clause for the same row of the
plan's table ("no `d2` attribute allocated"), which needs a different fixture and would otherwise
have hidden a genuine allocation failure behind the fingerprint hash. The mapping to the plan's
table is:

| Plan test | Function | Invariant |
| --- | --- | --- |
| 1 | `test_1_off_mode_matches_phase0_fingerprint` + `test_1b_off_mode_allocates_no_d2_state` | 1 |
| 2 | `test_2_d0_matches_off_boundaries_and_target_scale` | 2, review III.1.2, III.1 P4 |
| 3 | `test_3_infinite_costs_permit_no_pre_cap_switch` | 3 |
| 4 | `test_4_zero_cost_samples_every_live_agent` | 4 |
| 5 | `test_5_segment_lengths_partition_live_steps` | 5 |
| 6 | `test_6_ordered_replay_covers_sampled_positions_only` | 6 |
| 7 | `test_7_team_decision_closes_every_agent_segment` | 7 |
| 8 | `test_8_shapes_targets_and_normalized_ages` | 8 |
| 9 | `test_9_trigger_path_draws_no_rng` | review III.1.3 |

### 3.1 The one failure seen during development, and its cause

On the first full run, test 6 failed:

```
>       assert abs(joint - expected) < 1e-9
E       assert 4.76837158203125e-07 < 1e-09
E        +  where 4.76837158203125e-07 = abs((-5.463428974151611 - -5.463428497314453))
tests\flexible_skill_duration_d2_test.py:820: AssertionError
1 failed, 9 passed, 14 warnings in 24.23s
```

This was a test-tolerance error, not a code defect: the two quantities are the same float32 terms
summed in a different order (`sum()` over the full `[B, N]` tensor versus `sum()` over the masked
subset), so they differ by float32 round-off. The tolerance was raised to `1e-6` with a comment
naming the reason. No production code was changed in response. The equality that actually carries
invariant 6 — `replay log-prob == collection log-prob` and `zero at forced positions` — is asserted
separately at `atol=1e-6` and exactly `== 0.0` respectively, and both passed on the first run.

---

## 4. Smoke rollouts (not evidence)

One 40-step, two-env, three-UAV, scenario-1 rollout per configuration, each followed by one
`agent.update()`. Numbers below are machine-reported from those runs; they exist to show the code
runs and to answer P1/P2, not to support any claim.

Resource preflight was run immediately before every model-creating run:
`scripts/hmasd_resource_preflight.py admit-memory --out temp/pytest_d2_policy_interrupt/preflight_<phase>.json`,
`passed: true` each time (physical and effective available ≈ 15.7 GiB against the 4 GiB floor).

### 4.1 `off`

| Quantity | Value |
| --- | --- |
| high-level rows `M` per rollout | 8 |
| boundaries, env 0 | 0, 10, 20, 30 |
| `_batched_assign_skills` wall time over 40 steps | 0.0876 s (40 calls) |

### 4.2 D0 (`d2`, `c = c_Z = inf`, `k_max = k_Z = k = 10`)

| Quantity | Value |
| --- | --- |
| boundaries, env 0 | 0, 10, 20, 30 (identical to `off`) |
| decision steps / team decisions | 8 / 8 |
| mean `|S_t|` per env-step | 0.30 of 3 agents (`S_t_fraction` 0.10) |
| sampled / forced agent-positions | 24 / 216 |
| boundary causes | `reset` 2, `team_cap` 6, `team_gap` 0, `gap` 0, `cap` 0 |
| rows `M` (union), agent rows, team rows | 8, 24, 8 |
| mean segment length (agent / team) | 10.0 / 10.0 |
| switch count by agent index | [5, 6, 8] |
| `g_i` histogram (n=234) | mean 0.667, std 0.635, min 0.0, q10/q50/q90 0.0 / 0.576 / 1.565, max 1.909 |
| `g_Z` histogram (n=78) | mean 0.369, std 0.453, min 0.0, q10/q50/q90 0.0 / 0.132 / 1.264, max 1.325 |
| optimiser steps | 15 |
| `\|\|theta − theta_0\|\| / \|\|theta_0\|\|` | 8.619e-03 |
| target scale (team / agent) | 2.6806 / 2.6812 |
| target variance (team / agent) | 1.0058 / 1.0065 |
| coordinator inference in the trigger+assign path | 0.7623 s over 43 calls |
| `_batched_assign_skills` wall time over 40 steps | 0.7842 s (40 calls) |

**Inference time ratio `d2 / off` = 8.96** on this configuration (0.7842 s vs 0.0876 s of skill
assignment per 40-step rollout). ADR II.4 predicts roughly `k = 10` times `off`; the measured 8.96
is below that because two of the 40 steps per env are resets, which skip the teacher-forced pass,
and because the assignment pass itself is shared between the two modes. This is a single
unreplicated timing on one machine and one tiny configuration; it is an implementation sanity check,
not a performance measurement.

### 4.3 `c = 0`, `c_Z = inf`, `k_max = 10`, `k_Z = 40` — the P1/P2 probe

| Quantity | Value |
| --- | --- |
| fraction of agent-steps sampled | 1.000 |
| mean `\|S_t\|` | 3.0 of 3 |
| boundary causes | `gap` 234, `reset` 2, everything else 0 |
| team decisions | 2 (the two resets only) |
| rows `M` (union) / agent rows / team rows | 80 / 240 / 2 |
| mean segment length (agent / team) | 1.0 / 40.0 |
| switch rate by agent index | [0.700, 0.800, 0.850] |
| switch count by agent index | [56, 64, 68] |
| fraction of evaluated `g_i` that are strictly positive | 0.6496 |
| fraction of evaluated `g_i` that are exactly 0 | 0.3504 |
| optimiser steps / displacement | 15 / 1.110e-02 |

At `c = c_Z = 0` (both zero) the same rollout gives sampled fraction 1.000, mean `|S_t|` 3.0, and
causes `team_gap` 78, `reset` 2 — the team gap fires first, so every boundary is a team decision.

### 4.4 P1 and P2 (recorded, not interpreted)

**P1 — switch rate by agent index under the causal-prefix test.** At `c = 0`, `c_Z = inf`, three
agents: 0.700, 0.800, 0.850 (counts 56, 64, 68 over 80 env-steps). At D0 the same quantity is
0.0625, 0.075, 0.100 (counts 5, 6, 8 over 80 env-steps). Both orderings are monotone increasing in
the agent's position in the canonical decode prefix. Recorded without interpretation; the ADR names
causal-prefix index bias as a risk and the plan reserves interpretation for the owner.

**P2 — chattering floor at `c = 0`.** The plan's acceptance checklist (§11) expects "the chattering
floor near 5/6 for an untrained coordinator; a value far from it is a bug in the gap computation".
The measured fraction of agents sampled per step is **1.000**, not 5/6, and this is not a gap-
computation bug — it follows from the frozen rule. `g_i = max_z ell_i(z) − ell_i(z_i^held) >= 0`
always, with equality exactly when the held skill is the argmax. The ADR's decision text and
invariant 4 both use a non-strict `>=` ("Put `i` in `S_t` when `g_i >= c`"; "At `c = 0, delta = 1`,
every live agent is sampled every step"), so at `c = 0` every agent is sampled every step by
construction. The quantity that the 5/6 prediction actually describes is the fraction of positions
whose held skill is *not* the argmax, i.e. `g_i` strictly positive. That is **0.6496** here (with
`n_z = 6` skills and three agents), against the 5/6 = 0.833 a uniform-held-skill argument predicts;
the held skill is drawn from the same policy one step earlier rather than uniformly, so it coincides
with the argmax more often (0.3504) than 1/6 = 0.167. Both numbers are recorded; neither is
interpreted here. Invariant 4 and plan test 4 are satisfied, and plan §11's "near 5/6" phrasing is
inconsistent with the ADR's own invariant 4 — see the disagreement list in §6.

---

## 5. Plan-vs-code discrepancies carried forward from the handoff

Reproduced from `D2_EXECUTION_HANDOFF_20260902.md` unedited in substance, as the handoff instructs.
All were confirmed still true against the working tree at the time of this report.

- §2 cites `tests/hmasd_run_test.py` as the construction pattern; it is a subprocess run-manifest
  harness. The usable patterns: agent construction per `tests/intrinsic_reward_batch_test.py`
  (`HMASDAgent(config, log_dir=..., device=...)`); batched rollout loop per
  `train_multiproc_config_1.py:4567-5036` (`agent.step` at agent.py:2399 → env step with
  terminal-state storage semantics → `store_transition_batch` at 3159 → per-env reset bookkeeping
  → discoverer bootstrap at 4942-5005 → `agent.update` at 5712 → `clear_buffers` at 5132);
  scenario-1 env `UAVBaseStationEnv` (main.py:389; `envs/pettingzoo/scenario1.py:4`) with
  `max_steps = episode_length` and per-env seeds `base_seed + rank`, wrapped in
  `ParallelToArrayAdapter` (`envs/pettingzoo/env_adapter.py:17`).
- §4 cites `evaluate_training_batch` at networks.py:868; the def is at 862.
- §4 says "Two new methods" but lists three; three were implemented.
- The `episode_length % k == 0` check at config_1.py:719 sits inside `_validate_scenario7_preset`
  (scenario-7 only), not a general assertion. Phase 1 implemented the plan's intent literally
  (mode-guarded at that site; cap validation in `validate_config()`).
- The real route calls `agent.clear_buffers()` after `agent.update()` (train_multiproc:5132);
  the fingerprint driver mirrors this — without it the second rollout's stores are rejected as
  time steps going backwards.
- `agent.step` is called with `build_infos=False` in the real non-debug route → `infos_batch=None`
  to `store_transition_batch`; `step_data` carries what storage needs.
- After a done, the policy keeps the terminal state (no `reset_state` on the SubprocVecEnv path,
  train_multiproc:4898-4905) while observations use the post-reset obs; the driver mirrors this.
- `use_ha_ctse = bool(getattr(config, 'use_horizon_window', False))` (agent.py:473); config_1 does
  not set `use_horizon_window`, so the base route is the default — D2 configs must not set it.

(Line numbers in the list above are the handoff's, taken before Phases 3–8; `hmasd/agent.py` line
numbers have shifted by roughly +480 since.)

---

## 6. Where the plan, the ADR and the review disagreed

Recorded, not resolved in the plan or the ADR (which were not edited).

1. **Plan §11 "chattering floor near 5/6" versus ADR invariant 4.** Invariant 4 and the ADR's `>=`
   decision rule force *every* agent to be sampled at `c = 0`, i.e. a floor of 1, and plan test 4
   asserts exactly that. The 5/6 figure describes a different quantity (the fraction with a strictly
   positive gap). Both are reported in §4.4. The ADR wins per the plan's own rule, so the code
   implements `>=`; §11's acceptance sentence cannot be satisfied as literally written.
2. **Direction of the target-scale ratio (plan test 2 / review III.1 P4).** The plan asks for a
   "logged target-scale ratio close to `tau(1-gamma)/(1-gamma^tau)` (about 1.046 at `tau = 10`)".
   With a constant reward, `off` stores the undiscounted sum `tau·r` and `d2` the discounted sum
   `(1-gamma^tau)/(1-gamma)·r`, so it is `off / d2` that equals 1.045829 and `d2 / off` that equals
   0.956179. Test 2 asserts both directions explicitly so the intended number appears whichever
   convention a reviewer reads. Nothing in the code depends on the choice.
3. **Plan §7 "add the team normaliser for the team table".** There is no separate team value
   normaliser object on this route; `use_valuenorm` is served by the single
   `self.value_norm_coordinator`, which the `off` path already applies to the team head
   (`state_values`) as well as the per-agent columns. The `d2` path applies it identically
   (denormalising both heads at collection in `_batched_assign_skills_d2`, then running GAE on real
   values with `value_normalizer=None`, exactly as `off` does). No new normaliser was introduced,
   because introducing one would change the `off`-comparable target scale for reasons unrelated to
   D2.
4. **ADR III.1.1 (switch event outside the likelihood) needs no code.** Confirmed: `S_t` is computed
   from the policy's own logits under `torch.no_grad()` and never enters the PPO ratio. Named here
   because the ADR asks for it to be named; nothing was implemented.

---

## 7. New `d2` behaviour, and the design points the plan did not fix

`off` behaviour is unchanged and is guarded by the Phase 0 fingerprint at every commit. The
following are `d2`-only and are new behaviour rather than a restatement of the plan.

1. **Age convention.** `a_x` is the number of steps elapsed since the decision that produced the
   currently held skill, evaluated *before* this step's decision. A skill decided at step `t` has
   age 0 while it executes at `t` and age `k_max` at `t + k_max`, so `a_i >= k_max` reproduces the
   `env_steps % k == 0` boundaries of `off` at `k_max = k_Z = k`. The age written to the buffer at
   step `t` (and fed to the discriminator) is the *executing* age: 0 for agents sampled at `t`, the
   pre-decision age otherwise. This is the convention plan §9's "the ages at the step the
   transition was collected" requires; the plan does not spell out the off-by-one, so it is stated
   here.
2. **Reset detection.** `reset_mask = (env_steps == 0) | dones | invalid_skills_mask`. The plan
   names the last two; `env_steps == 0` was added because it is what makes the very first step of a
   rollout a boundary in `off` (`env_steps % k == 0`), and D0 parity would otherwise fail at `t = 0`
   in a collector that does not invalidate skills on reset. On the base route the three agree,
   because `reset_env_state` sets the skills to −1.
3. **Normaliser update set.** The teacher-forced gap pass calls `_normalize_states` /
   `_normalize_observations` with `update=False`; only the decision subset is normalised with
   `update=True`, exactly the set `off` updates. So at D0 the running normalisers see the same
   states as `off`, and the 10× extra inference does not change normaliser statistics.
4. **Segments at a rollout boundary are flushed, not carried over.** `_d2_flush_open_segments`
   closes every open segment with `terminal = False` at the last stored step, so GAE bootstraps it
   with the value of the next state (plan §6). It then drops the bookkeeping: the next rollout's
   segments open at the next actual decision. The plan defines the close rules but not the
   re-opening rule. Carrying a segment across the boundary would require writing a row at an index
   in the *new* buffer whose stored state is not the state at which the decision was taken, which
   would corrupt PPO replay; that was judged the worse of the two, and no scientific decision was
   invented. **Consequence:** if a rollout begins mid-episode with no decision at its first step,
   the steps before the first decision of that rollout contribute to no segment row, so invariant 5
   holds per rollout only when every env has a decision at `t = 0`. Under the plan's own
   configuration (`episode_length == rollout_length`, so every rollout starts on a reset) no step is
   ever lost, and test 5 checks the partition exactly. The owner should decide whether the E-series
   configuration keeps `rollout_length` a multiple of `episode_length`.
5. **`high_level_valid_mask` in `d2`** is set to the union of the agent and team row masks, so the
   existing count checks, the `_audit_high_replay_likelihood` gate and the `off` sampler surface see
   a coherent row set. The per-head masks (`d2_agent_valid`, `d2_team_valid`) are what the `d2`
   sampler and losses actually use, because a team row and an agent row at the same `(t, e)` do not
   have to be valid together.
6. **The `off` pending/close mechanism is bypassed entirely in `d2`.** `store_transition` returns
   before creating `env_pending_high_level` entries and before calling
   `_store_coordinator_experience`; `d2` storage is `_d2_store_transition`. `update_coordinator`
   dispatches to `update_coordinator_d2` after the flush. `off` reaches neither.
7. **Advantage normalisation in the masked update** uses the masked mean and masked standard
   deviation over the valid team and agent advantages of the minibatch, mirroring `off`'s single
   global normalisation over the concatenated team and agent advantages, but excluding invalid
   positions from the statistics.
8. **Entropy** is `team_entropy·team_valid + sum_i agent_entropy_i·agent_valid_i`, averaged over the
   rows in the minibatch — the `off` formula with the masks applied, matching the ADR's "log-
   probability and entropy sum only over sampled positions". `valid` implies `sampled`, so no forced
   position can contribute.
9. **`theta_0`** for the exposure line is captured at `HMASDAgent` construction, in `d2` only.
   `||theta − theta_0|| / ||theta_0||` is computed in float64 over the coordinator parameters.
10. **Cheap `d2`-only asserts** in `_batched_assign_skills_d2`: `c = inf` implies no `gap` cause,
    `c_Z = inf` implies no `team_gap` cause, and a team decision implies `sampled_mask.all()`.
    These run every step in `d2` and never in `off`.

---

## 8. Acceptance checklist (plan §11), as observed

| Item | Observation |
| --- | --- |
| All nine tests pass under the explicit interpreter with the isolated basetemp | Yes — 10 test functions, `10 passed` (§3) |
| `git diff` shows no change inside any function reachable in `off` except added guarded branches | Yes, by inspection; and enforced empirically by test 1, which hashes the full coordinator, team-discriminator and individual-discriminator `state_dict`s after one `update_coordinator` plus every per-step skill, log-probability and high-level buffer array of two rollouts |
| No change to checkpoint keys in `off` | Yes — the discriminator input dimension only grows under `d2` + `age_feature="normalized"`; test 1b asserts `age_input_dim == 0` in `off`, and the fingerprint's `state_dict` hashes would change if any key or shape moved |
| No new file outside the four source files, the test file and the report | Yes. Files changed in Phases 3–8: `hmasd/agent.py`, `hmasd/utils.py`, `hmasd/networks.py`, `tests/flexible_skill_duration_d2_test.py`, plus this report. `config_1.py` unchanged since Phase 1 |
| The ADR's eight invariants each map to a passing test; III.1 items 2 and 3 covered by tests 2 and 9 | Yes — see the mapping table in §3. III.1.2 (mid-rollout reset) is inside test 2; III.1.3 (no RNG in the trigger path) is test 9 |
| Smoke rollout at `c = 0` shows the chattering floor near 5/6 | **Not as written.** Measured 1.000 sampled fraction, which is what ADR invariant 4 requires; the "near 5/6" quantity is the strictly-positive-gap fraction, measured 0.6496. See §4.4 and §6 item 1 |

---

## 9. Could not verify

- **The measured inference ratio is one unreplicated timing.** `d2 / off = 8.96` comes from a single
  40-step, 2-env, 3-UAV CPU rollout with `torch.set_num_threads(1)`. It is not a benchmark; the ADR's
  `k`-fold prediction is not confirmed or refuted by it.
- **Behaviour at the E-series scale is untested.** Everything here ran at `N = 3`, `num_envs = 2`,
  `rollout_length = 40`, `episode_length = 40`. The ADR's `N = 6`, `num_envs = 32`,
  `rollout_length = 500`, `k_max` up to `H = 500` configuration has not been run. In particular the
  `M = 32` sample-count collapse at `k_max = H` (ADR II.3) is not exercised, and the plan forbids
  running it here.
- **Segment carry-over across rollout boundaries** (§7 item 4) is untested because the plan's
  configuration never produces the case. If the E-series uses a `rollout_length` that is not a
  multiple of `episode_length`, the reward of the steps before each rollout's first decision is
  dropped, and invariant 5 would fail across the boundary. Flagged for the owner.
- **The compact (HA-CTSE) discriminators do not accept the age feature.** `age_feature="normalized"`
  is implemented on `TeamDiscriminator` and `IndividualDiscriminator` only. If
  `use_compact_team_discriminator` / `use_compact_individual_discriminator` are ever combined with
  `d2`, the age is silently not passed. `use_ha_ctse` and `d2` are mutually exclusive dispatch
  branches today, so this is unreachable, but it is not asserted anywhere.
- **`interruption_delta` is validated to be 1 and is otherwise unused.** The `delta > 1` (check every
  `delta` steps) behaviour is not implemented; the ADR fixes `delta = 1` and Phase 1 rejects anything
  else, so no code path exists.
- **Checkpoint save/restore of the D2 tables was not tested.** The D2 segment tables are rollout-
  scoped buffer state, cleared by `clear_buffers` like every other rollout array, and the open-
  segment bookkeeping lives on the agent and is likewise reset. Nothing D2 was added to the
  checkpoint payload. Whether a mid-rollout checkpoint/restore is meaningful under `d2` was not
  examined.
- **`--basetemp` clears its own directory.** Every pytest run with
  `--basetemp C:/Projects/HMASD/temp/pytest_d2_policy_interrupt` deletes the directory contents
  first, including any preflight receipt or scratch file written there earlier. The preflight
  receipts named in §4 were valid when written and were passing; they do not survive the next test
  run. Scratch scripts for this session were therefore kept under `temp/d2_scratch/` (also
  gitignored).
- **No claim is made about learning.** No training run was launched. Nothing in this report speaks to
  whether D2 helps or hurts.
- **A pre-existing unrelated test failure was observed and left alone.**
  `tests/production_backend_policy_test.py` reports `7 failed, 100 passed, 1 skipped`. The failures
  are pinned `source_sha256` assertions over C++ sources under `experiments/candidates/*` (e.g.
  `ddb14c33d822...` expected, `76c715a6a1cc...` measured), and that tree currently carries 37
  uncommitted modifications belonging to other work lines. The file imports nothing from `hmasd/`,
  so the failures cannot come from this change; they were not investigated and nothing there was
  touched. `tests/hmasd_run_test.py` and `tests/intrinsic_reward_batch_test.py` pass.
