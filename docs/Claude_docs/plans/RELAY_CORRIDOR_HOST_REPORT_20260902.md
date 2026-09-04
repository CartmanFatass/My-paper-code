# Relay corridor host — implementation report, 2026-09-02

Object: the relay corridor host family for duration-plan E2–E4.

Specification followed, unchanged and unedited by this work:

* `ADR_02_RELAY_CORRIDOR_HOST.md` (revision 4, accepted) — Decision, Parameters,
  nine Invariants, nine Tests-as-specs, Metrics to log, Resolution arithmetic.
* `RELAY_CORRIDOR_MECHANICS_20260902.md` (finalised normative companion).
* `../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` Part IV (§§IV.0–IV.8.1)
  and Part V (§§V.0–V.3, in particular V.2 "Notes for the host implementer").
* `FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` §§5–6 and
  `../toy_studies/untied_k_n/RESULTS.md` (the `C(k, lambda)` table).

Status: the host, the references, the adapter and the nine tests exist and pass.
No learner was trained; every learner-side quantity in ADR 02's "Could not
verify" list remains prospective.

---

## 1. What was built and where

| Object | Path | Contents |
| --- | --- | --- |
| Package | `envs/relay_corridor/` | pure NumPy; no torch, no native code, no import from `experiments/candidates` |
| Parameters | `envs/relay_corridor/config.py` | `RelayCorridorConfig`, `PROPOSAL_GRID`, `proposal_config`, `validate_horizon`, `rows_per_rollout` |
| RNG | `envs/relay_corridor/rng.py` | `stream_key`, `stream_generator`, `STREAM_ENTITY`, `STREAM_REGION_EVENT` |
| Event processes | `envs/relay_corridor/renewal.py` | `BernoulliHazard`, `DeterministicLaw`, `GeometricLaw`, `RoundedLognormalLaw`, `make_renewal_law` |
| Host core | `envs/relay_corridor/host.py` | `RelayCorridorHost`, `obs_layout`, `state_layout`, `KEEP`, `RENEW` |
| References and margins | `envs/relay_corridor/references.py` | `dp_service_profile`, `enumerate_references`, `ReferenceReport`, the four scripted policies, `rollout_reference`, and the closed forms as check values |
| Adapter | `envs/relay_corridor/adapter.py` | `RelayCorridorAdapter` |
| Tests | `tests/relay_corridor_host_test.py` | ADR 02 tests-as-specs 1–9, in order |
| This report | `docs/Claude_docs/plans/RELAY_CORRIDOR_HOST_REPORT_20260902.md` | — |

The host file location is not fixed by ADR 02; review §V.2 note 3 names `envs/`
as the natural home. `envs/pettingzoo/relay/` already exists and is unrelated
routed-relay work; its name was not reused. `git check-ignore -v` was run on
every new path: the package and the test are not ignored, and the report matches
the `!docs/Claude_docs/**` re-include on `.gitignore:138`.

### Run command

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py `
    admit-memory --out temp/relay_corridor_receipts/preflight_20260902.json
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q `
    tests/relay_corridor_host_test.py `
    --basetemp <worktree>/temp/pytest_relay_corridor
```

Result: `9 passed in 14.76s`. The memory preflight passed before the run
(13.5 GiB physical and effective available against the 4 GiB floor,
`measurement_source = GlobalMemoryStatusEx`). Note that `--basetemp` empties its
directory at session start, so a receipt written inside
`temp/pytest_relay_corridor/` does not survive the run; the retained receipt is
at `temp/relay_corridor_receipts/preflight_20260902.json` (ignored path).

### Step order

Review §V.2 note 1 is written into `RelayCorridorHost.step`'s docstring and
implemented as three numbered phases inside it: score at `t` (a `RENEW` at `t`
contributes exactly zero), apply `RENEW` at `t` (stamp the region's current
epoch), then realise the transition into `t + 1` (draw one event per region, redraw
`theta_r` among the `K - 1` others, increment the epoch so every regional lease
goes stale, raise the change flag at `t + 1`, and write the cue *before* the
latent moves so `y_{r,t+1} = theta_{r,t}`). There are `H` scored steps and
therefore `H - 1` transitions; the final call scores `t = H - 1` and draws no
event. That count is what makes
`J_sw = Delta * sum_r w_r (1 + (H - 1)(1 - lambda_r)) / H` exact.

---

## 2. How each invariant is met

| # | Invariant | Where it is met | Test |
| --- | --- | --- | --- |
| 1 | Ragged, unpadded host-boundary entities as a family property | `RelayCorridorHost.public_state_records` returns lists at the live cardinality; `RelayCorridorHost.record_padding` is `False`; no sentinel or padding column exists | `test_1_family_instances_emit_ragged_unpadded_records` (N = 3, 5, 6, 9) |
| 2 | Key-stable, order-independent entity and region-event streams | `rng.stream_key` / `rng.stream_generator` build one `SeedSequence` + Philox per `(seed, episode, kind, id)`; `RelayCorridorHost._build_tapes` draws each lane from its own key, never from a shared generator; `stream_tapes()` exposes them | `test_2_keyed_streams_are_stable_and_order_independent` (permuted batch, solo-lane rehost, realised trajectories, and a different master seed) |
| 3 | Every positive `N` valid; no `N mod K` rule | `RelayCorridorConfig.__post_init__` has no divisibility check; `region_of_agent` / `zone_of_agent` split by balanced sizes and round robin | `test_3_every_positive_n_is_valid_there_is_no_n_mod_k_rule` (N = 1…8, both divisible and non-divisible by `K = 2`) |
| 4 | Pinning; registered hazards and dwell laws; full deterministic initial dwell; laws share only `E[D]` | `config.region_of_agent` / `zone_of_agent` are static properties never mutated by `step`; `renewal.py` expresses every law as a discrete hazard table indexed by dwell age, and the age is `0` at reset, so the first dwell is a full draw | `test_4_pinning_dwell_laws_and_reported_variances` |
| 5 | Enumeration reproduces every stated `m` and `m_dur`; `m_dur >= 3 sigma_Delta / sqrt(E_eval)` | `references.enumerate_references`; `ReferenceReport.m`, `.m_dur`, `.resolution_ok` | `test_5_enumerated_margins_match_the_proposal_table` |
| 6 | `H >= 10 max(D0_k_set)`; D2 `k_max` exempt and reports `M` | `config.validate_horizon`, `config.HorizonValidationError`, `config.rows_per_rollout` | `test_6_horizon_rule_rejects_only_fixed_k_d0_and_emits_m` |
| 7 | Argmax roles and ADR-01 renew mask; pre-cost shared reward in `[0, 1]`; per-agent indicators logged; probe/coupling-off behavior exact | `RelayCorridorHost.decode_roles`, `RelayCorridorAdapter.step` (`renew_mask` / `renew_indices`), `host.step` reward line, `obs_layout` blocks `probe_theta` / `probe_valid` / `coupling`, and the config refusing `e5_coupling_enabled`, `c_probe != 0`, `rho != 0` | `test_7_adapter_argmax_renew_mask_reward_and_disabled_fields` |
| 8 | References, D0 cut, setup outage, deterministic `k = D` equality, cue timing, `K = 2` greedy equality | `references.SwitchingOracle` / `FixedKOracle` / `OpenLoopPlan` / `GreedyOnPublicState` and the DP behind them; `host.step` ordering | `test_8_reference_traces_step_order_cue_timing_and_equalities` |
| 9 | Native-disabled NumPy checked against the recorded `1e4` steps/s/core target | benchmark subprocess in the test, pinned to one thread, asserting no torch / no `envs.native` / no `experiments.*` import | `test_9_native_disabled_numpy_throughput_against_the_recorded_target` |

Metrics from ADR 02's "Metrics to log" are emitted by `host.step`'s info dict and
`references.rollout_reference`: renew masks, per-agent service indicators, shared
reward, segment ages, change flags, cues, dwell ages, probe/coupling switch
state, all reference returns, both margins, `M`, throughput and machine
identity. Tests 4, 5, 6, 8 and 9 write machine-generated JSON records under the
isolated basetemp.

---

## 3. Enumeration results next to the table values

All values below are produced by `enumerate_references` (exact dynamic
programming), not copied. The mechanics page's closed forms are recomputed
independently inside the test and agree with the enumeration to `1e-12`.

### Margin table (`N = 6`, `K = 2`, `Z = 4`, `H = 400`, D0 `k in {1,2,5,20,40}`)

| level | `(lambda_1, lambda_2)` | `Delta` | `m` enumerated | `m` table | `m_dur` enumerated | `m_dur` table | best `k` (enum / table) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| small | (.005, .02) | .4 | 0.226024973213 | .226025 | 0.057037446427 | .057037 | 20 / 20 |
| medium | (.005, .10) | .6 | 0.356468268731 | .356468 | 0.144357787462 | .144358 | 5 / 5 |
| large | (.02, .20) | 1.0 | 0.580746992000 | .580747 | 0.271218984000 | .271219 | 5 / 5 |

Every row reproduces the printed digits. Supporting reference returns:

| level | `J_sw` | `J_1` | `J_2` | `J_5` | `J_20` | `J_40` | `J_open` best | `J_greedy` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| small | 0.39501250 | 0.00100000 | 0.19850000 | 0.31116838 | 0.33797505 | 0.31125478 | 0.16898753 | 0.39501250 |
| medium | 0.56857875 | 0.00150000 | 0.28575000 | 0.42422096 | 0.38943206 | 0.33291125 | 0.21211048 | 0.56857875 |
| large | 0.89027500 | 0.00250000 | 0.44750000 | 0.61905602 | 0.49154888 | 0.38642894 | 0.30952801 | 0.89027500 |

`J_greedy = J_sw` exactly in all three rows, as decision 2 requires at `K = 2`.
The open-loop census is `2^4 x 6 = 96` candidates per row and its maximum equals
`max_k J_k / K` exactly, so all 16 zone-role maps tie — the expected consequence
of the uniform stationary marginal of `theta_r`.

### Measured `sigma_Delta` and the resolution inequality

Measured from 512 matched (common-random-number) reference episodes per level,
switching oracle minus best fixed `k`:

| level | `sigma_Delta` | `3 sigma_Delta / sqrt(4096)` | `m_dur` | paired gap realised |
| --- | --- | --- | --- | --- |
| small | 0.013311 | 0.000624 | 0.057037 | 0.057061 |
| medium | 0.006355 | 0.000298 | 0.144358 | 0.144536 |
| large | 0.013700 | 0.000642 | 0.271219 | 0.271670 |

Every row clears the acceptance-scale requirement by two orders of magnitude,
and the measured `sigma_Delta` is "a few hundredths", as review §IV.6 predicted,
not the `sigma_Delta <= 1` bound the ADR uses. The smallest proposed `m_dur`
also exceeds the ADR's `3/64 = 0.046875`.

### E4 dwell laws at `E[D] = 20`

| law | mean | variance computed | variance stated |
| --- | --- | --- | --- |
| deterministic | 20.000000000000 | 0.000000 | 0 |
| geometric | 20.000000000000 | 380.000000 | 380 |
| rounded lognormal, shape 1 | 20.000000000000 | 687.308622 | 687.309 |

The lognormal log-location is calibrated to `E[D] = 20` by bisection followed by
secant refinement over the CDF-bin masses of `D = max(1, floor(X + 1/2))`,
truncated at `exp(m + 9s) ~ 98,715`. The variance is stable to `3.4e-5` between
truncations at `2e4` and `2e5`, so it rounds to `687.309` either way. Compare the
continuous value `(e - 1) * 400 = 687.312731`.

### Deterministic `D = 20`, fixed `k = 20`

`J_{k=20} = J_sw = 0.381 = 0.4 * 381 / 400` exactly, so `m_dur = 0` at zero dwell
variance. Nineteen events land in the 399 transitions and each costs exactly one
step of service. Driven through the host, the switching oracle, `k in {5, 20,
40}` and greedy all return their DP values to `1e-12` with **zero spread across
lanes** — with a deterministic dwell law and a latent-aware policy the realised
return carries no randomness, so this is an identity and not a Monte-Carlo
agreement.

### `K = 3`, the registered family point

Not required by the ADR, computed as a falsifier for the `K = 2` equality:
`J_greedy = 0.390122 < J_sw = 0.395013` (greedy loses two steps per event, which
matches the two-step closed form `0.390110` to `1.2e-5`), the open-loop census is
`3^4 x 6 = 486` as the page states, `m` rises to 0.282354, and `m_dur` is
unchanged at 0.057037 — as it must be, since it compares two latent-aware
oracles.

### Host-versus-enumeration cross-check on the stochastic laws

Driving all four scripted references through the vectorized host on Bernoulli
tapes reproduces the DP values within about 1.8 standard errors at 400 episodes
per level (switching oracle, best fixed `k`, greedy, best open-loop, all three
levels). Greedy and the switching oracle agree **step for step** on identical
tapes at `K = 2` (`service_indicators` arrays equal element-wise over 64 lanes).

---

## 4. Throughput and machine identity

Measured in a subprocess pinned to one thread
(`OMP_NUM_THREADS = MKL_NUM_THREADS = OPENBLAS_NUM_THREADS = NUMEXPR_NUM_THREADS = 1`),
with the native boundary untouched (the benchmark asserts that `torch`,
`envs.native` and `experiments.*` are absent from `sys.modules`):

| quantity | measurement |
| --- | --- |
| mechanics-only step, `batch = 1` | **30,935 steps/s/core** |
| step including observation assembly, `batch = 1` | 11,557 steps/s/core |
| vectorized `batch = 64`, with observations | 485,648 env-steps/s/core |
| target (advice §3 P7) | 10,000 steps/s/core |
| disposition | `meets_target` (ratio 3.09 on the mechanics measure, 1.16 with observations) |

Machine: `AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD`, host `Jacob`,
`Windows-10-10.0.26200-SP0`, CPython 3.10.20, NumPy 1.26.3, conda env
`hmasd-amd-cpu`. The recorded number is one machine and one NumPy build; the
target is prospective advice, so test 9 records the disposition and does not fail
on a miss.

The mechanics figure is the like-for-like comparison against the speed note,
which enumerates the step as "two event updates, indexed target-role gathers,
freshness/renew masks, one Boolean reduction over `[batch, N]`, and cue/age
updates" — it does not include laying out observation vectors. Both figures are
reported because the learner pays the second one.

---

## 5. Spec-versus-code discrepancies and reading choices

Nothing the ADR or the mechanics page fixes was changed. The items below are
either genuine ambiguities resolved in the direction that keeps the enumeration
equal to the table values, or implementation facts a reviewer should know.

1. **Cue at reset.** The page defines `y_{r,t} = theta_{r,t-1}`, which is
   undefined at `t = 0`. The host sets `y_{r,0} = theta_{r,0}` (the lag is
   degenerate at reset). Any other reading costs greedy the first step at `K = 2`
   and breaks the invariant-8 equality `J_greedy = J_sw`; this reading also sits
   with "reset installs the initial lease before scoring". Recorded here as a
   choice, not a change.

2. **"Initial lease" means freshness, not role correctness.** At `t = 0` an
   open-loop map is right only with probability `1/K`, which is exactly what
   makes `J_open,k = J_k / K` hold at *every* step including the first. The
   latent-aware oracles and greedy are right at `t = 0` because they know or can
   infer `theta_0`, not because reset hands them a role.

3. **Held role versus emitted action.** The page's agent record carries a "held
   role" and the reward formula scores the emitted `a_i`. Both exist: the host
   scores `a_i` exactly as the formula says, and `held_role` (the role stamped at
   the last `RENEW`) is an observation feature only. They differ only when a
   lease is stale, where service is zero either way.

4. **Dynamic-programme factorisation.** The page names the per-region DP state
   `(theta, freshness, fixed-phase)` plus renewal age, and quotes the largest E4
   programme as `2 x 2 x 40 x 401 = 64,160` states. The implementation carries
   `(theta, freshness, plan-match, dwell age, pending-cue)` and runs the fixed
   phase as the explicit step index `t`, which is exact because the phase is a
   deterministic function of `t`. The extra `plan-match` and `pending-cue`
   coordinates let the same programme evaluate open-loop maps and the `K >= 3`
   delayed-cue greedy policy. The state count therefore differs from the page's
   arithmetic; the returns do not — they equal the page's closed forms to
   `1e-12`.

5. **Full initial dwell generalised to all three laws.** The page states the
   convention explicitly for the deterministic law and says "no stationary
   residual-life phase is sampled". The host implements every law through a
   discrete hazard table indexed by dwell age, with age `0` at reset, so all
   three start on a complete dwell.

6. **Per-region E4 laws.** The E4 proposal names one `E[D] = 20` with no
   per-region heterogeneity, so both regions get the same law. The config keeps
   one law per region so a heterogeneous E4 point can be registered later without
   a layout change.

7. **`H` scored steps, `H - 1` transitions.** The final `step()` call scores
   `t = H - 1` and draws no event. This is forced by `J_sw`'s `(H - 1)` factor;
   an implementation that drew `H` events would not reproduce the table.

8. **`e5_coupling_enabled = True` raises.** The switch and the reserved zero
   state field exist, but turning it on raises `NotImplementedError` rather than
   silently doing nothing, because the coupling rule is deliberately deferred
   (review §IV.8.1 decision 3). Likewise `c_probe != 0` and `rho != 0` are
   refused rather than partially honoured.

9. **`K >= 2` enforced.** The Parameters block says `K: positive int`; a switch
   that "draws a different `theta_r`" is undefined at `K = 1`, so the config
   rejects it.

10. **Test 1 reading.** Per review §V.1, test 1 asserts *distinct fixed-`N`
    family instances* with unpadded records; it does not require variable `N`
    inside one object. Test 3 carries the divisible / non-divisible `N` case.

11. **`--basetemp` wipes its directory.** The ADR's run line writes the pytest
    scratch tree to `temp/pytest_relay_corridor`; a resource-preflight receipt
    written to that same directory is deleted at session start. The retained
    receipt lives beside it at `temp/relay_corridor_receipts/`.

12. **Adapter batch shape.** ADR 02 fixes the adapter surface but not its array
    shapes; the adapter follows `envs/pettingzoo/env_adapter.py`
    (`ParallelToArrayAdapter`): `[N, obs_dim]` and a scalar reward with one
    environment, batch-first otherwise. The host core is always batch-first.

---

## 6. Could not verify

* **No learner ran.** `sigma_Delta` above is measured from *reference* tapes, not
  from a trained corridor learner. The corridor learner's `M`, parameter count,
  optimizer-step count and norm displacement remain the machine-generated
  exposure-line quantities ADR 02 lists as unverified. `rows_per_rollout` is an
  arithmetic reproduction of ADR 01 revision 3's two published `M` values, not a
  measurement of this host under a real rollout.

* **The base-route integration was not executed.** The adapter matches the shape
  contract read off `envs/pettingzoo/env_adapter.py` and `envs/pettingzoo/uav_env.py`,
  but no HMASD training or evaluation run was made from it. The learner
  (`config_1.py`, `hmasd/agent.py`, `hmasd/networks.py`, `hmasd/utils.py`) is
  being changed concurrently on `main` and was deliberately not touched or
  imported here. In particular, that the base-route low-level actor is
  continuous-only (review §IV.0's last row, "the implementer must confirm") was
  **not** confirmed by running the learner; the host simply accepts a continuous
  `K`-vector and takes its argmax, which is compatible with either head.

* **The finite D2 `c`, `c_Z`, `k_max` grid is still unfixed** (ADR 01 revision 3
  and ADR 02's open questions). Test 6 exercises the exemption rule and the `M`
  formula only; it does not run a D2 arm, and it says nothing about the `c`
  threshold at which D2 stops chattering on the immediate change flag.

* **The E5 coupling rule is undefined by design.** Only the default-off switch
  and the reserved zero state field are implemented and tested; there is no
  coupling mechanic to verify.

* **The throughput number is one machine, one build, one day.** No cross-machine
  or cross-NumPy comparison exists, and the `1e4` steps/s/core figure it is
  compared against is a target in the environment advice, not a measurement
  anywhere in the repository.

* **`K = 3` is only partially exercised.** The delayed-cue greedy path and the
  486-candidate census are checked against the DP and a closed form inside test 8,
  and the DP was cross-checked against 800 host episodes offline, but ADR 02
  registers no `K = 3` margin, so no `K = 3` value is a frozen expected value
  here. The probe value `v` is not implemented at all: E2–E4 fix
  `c_probe = 0` and the reserved fields stay zero.

* **Long-`k` sample collapse, lease-stamp structure leakage, low-level argmax
  learning and chattering** — the four learner-side risks ADR 02's "Consequences
  and risks" names — cannot be examined from the host alone and were not.

---

## 7. Integration on the corridor (2026-09-02)

Appended after the review's Parts VI and VII, for the single integration commit
§VII.4 asks for. Sections 1–6 above are unchanged and describe the host as it
was accepted; nothing here revises them.

### What the driver does

`envs/relay_corridor/hmasd_driver.py` holds `build_corridor_learner_config` and
`RelayCorridorHMASDDriver`. It is not imported from `envs/relay_corridor/__init__.py`,
so the host package stays torch-free and test 9's native-disabled subprocess is
unaffected.

* **Dimensions come from the host.** `build_corridor_learner_config` takes
  `obs_dim` and `state_dim` from `RelayCorridorAdapter`, `n_agents = N`,
  `episode_length = H`, and `action_dim = n_z = K` from
  `RelayCorridorConfig.low_level_action_dim` / `.n_z`
  (ADR 02 "Parameters"). At `K = 2`, `Z = 4`, two regions and `N = 3` that is
  `obs_dim = 19`, `state_dim = 47`. `n_Z` is *not* taken from the host: it stays
  at the learner default (6), so the team code remains present and inert
  (ADR 02 "Decision", E5 coupling off).
* **The loop** mirrors the batched base-route loop of
  `train_multiproc_config_1.py` and the driver in
  `tests/flexible_skill_duration_d2_test.py`: `agent.step` on the batched
  observations and global state → continuous actions `[num_envs, N, K]` →
  `RelayCorridorAdapter.step(actions, renew_mask=S_t)` → `store_transition_batch`
  → `agent.update` at the rollout boundary, then `clear_buffers`.
* **`S_t`.** In `d2` the renew mask is the D2 sampled mask of that step,
  `step_data['d2_sampled_mask']` (`[num_envs, n_agents]`). In `off` it is
  all-True exactly at the `off` boundaries — `env_steps % k == 0`, which includes
  the first step of an episode after a reset — and all-False otherwise. So
  `RENEW` opens the segment in both modes, and D0 reproduces the `off` renew
  pattern step for step.
* **Reward and metrics.** The learner receives the shared mean reward
  (`info['shared_reward']`, identical to the adapter's returned reward). The
  per-rollout summary carries the per-agent service indicators `[T, B, N]`, the
  decoded roles, the renew masks, the `off` boundary masks, the sampled masks in
  `d2`, the stored env-reward component, `service_rate_per_agent`,
  `renew_rate_per_agent`, `mean_shared_reward`, the lane episode ids, and (in
  `d2`) the `get_d2_metrics()` snapshot.
* **Lanes and CRNs.** `num_envs` lanes start at episode ids `0..num_envs-1` and
  `advance_episode_ids()` moves every lane on by `num_envs` after each episode,
  so no keyed corridor stream is ever reused (host invariant 2).
* **No file under `hmasd/` was changed for this part.** The existing agent
  consumes the adapter's arrays as they are.

Readings taken where the ADRs are silent (kept so that `off` and D0 boundaries
stay identical, per the task's rule):

1. **Terminal-state storage and reset.** The stored transition keeps the
   terminal next state and the next policy input takes the reset observations,
   while the policy *state* stays the terminal state — the base-route collector
   convention that the phase 0 driver documents. The corridor host is one
   batched object, so every lane terminates together at `t = H - 1`.
2. **Rollout bootstrap.** `last_values` is zero at the rollout boundary. With
   `rollout_length = H` the last stored step is terminal, so the bootstrap is
   multiplied by zero either way.
3. **`off` renew rule.** `env_steps % k == 0` (or a done) is used verbatim; it is
   what `skill_changed` computes in `off`, so the renew mask and the learner's
   own boundary notion cannot drift apart.
4. **D2 metrics snapshot.** `clear_buffers` resets `d2_metrics`, so the summary
   snapshots `get_d2_metrics()` after `agent.update` (which flushes the open
   segments and therefore fixes `M`) and before `clear_buffers`.
5. **Default `k`.** When the caller does not pass `k`, the driver uses `k = H`
   (one `off` segment per episode). The tests pass `k = 10` explicitly.

### B2 — the open item from review §IV.0 (low-level actor)

**The base-route low-level actor is not continuous-*only*; it is continuous by
default and dispatches on `config.action_space_type`, and with
`action_dim = K` it emits a `K`-dimensional continuous action per agent.**

Symbols read: `hmasd/networks.py` `SkillDiscoverer.__init__` builds
`spaces.Discrete(config.action_dim)` when
`getattr(config, 'action_space_type', 'continuous') == 'discrete'` and otherwise
`spaces.Box(low=-config.action_bound, high=config.action_bound, shape=(config.action_dim,))`,
and passes that space to `R_Actor`, whose `ACTLayer`
(`hmasd/r_mappo_utils.py:209`) selects `DiagGaussian` (or `TanhDiagGaussian`) for
a `Box` and `Categorical` for a `Discrete`. `config_1.Config` defaults to
`action_space_type = 'continuous'`, which the corridor learner configuration
keeps, so `R_Actor.forward` returns a `[B*N, K]` sample and
`HMASDAgent._batched_select_action` reshapes it to
`[num_envs, n_agents, config.action_dim]`; the driver asserts that shape at every
step. ADR 02's "the low-level policy emits a continuous `K`-vector each step and
the host takes its `argmax`" is therefore satisfied by configuration, not by a
code change, and the discrete head stays reachable for other routes. The
`DiagGaussian` sample is not clipped to `action_bound` (the `Box` bounds are only
carried by the space object), so the argmax cannot be forced into a tie at the
bound.

### Test results, verbatim

Preflight immediately before the run (receipt at
`temp/relay_corridor_hmasd/preflight.json`, an ignored path;
`--basetemp` is a subdirectory of it and does not wipe it):

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py `
    admit-memory --out C:/Projects/HMASD/temp/relay_corridor_hmasd/preflight.json
"passed": true, "effective_available_bytes": 16461737984,
"minimum_available_bytes": 4294967296, "measurement_source": "GlobalMemoryStatusEx"
```

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q `
    tests/flexible_skill_duration_d2_test.py tests/relay_corridor_host_test.py `
    tests/relay_corridor_hmasd_test.py `
    --basetemp C:/Projects/HMASD/temp/relay_corridor_hmasd/pytest -p no:cacheprovider
26 passed, 14 warnings in 35.34s
```

`tests/relay_corridor_hmasd_test.py` (four tests, `K = 2`, `N = 3`, `Z = 4`,
`H = 40`, `k = 10`, two lanes, one rollout each):

| Test | What it asserts |
| --- | --- |
| 1 `off` smoke | learner dimensions come from the host (`n_z = action_dim = K`, `n_agents = N`, `episode_length = H`, `n_Z = 6` untouched); array shapes; roles in `[0, K)`; `RENEW` exactly at `env_steps % k == 0`; the reward the learner stored (`rollout_buffer.reward_env`) equals the adapter's shared mean reward; a `RENEW` step scores zero service; one `agent.update` completes |
| 2 `d2` at D0 | `c = c_Z = inf`, `k_max = k_Z = k = 10`: the renew masks equal the `off` boundaries and equal the `off` run's own masks; the mask handed to the host is the sampled mask; `gap` and `team_gap` causes are zero; `M = 8`, agent rows `= 24`, `reset = 2`, `team_cap = 6`; one `agent.update` completes |
| 3 `d2` at finite `c` | `c = 0`: the mask handed to the host equals the agent's sampled mask at every step, is all-True, and is not the `off` boundary mask; `M = 80`; the corridor serves nobody, so the shared reward is identically zero |
| 4 config | `build_corridor_learner_config` reads the adapter; the new rollout-boundary guard (review VII F1) fires on this route too |

Observed numbers from one driver run (`master_seed = seed = 20260902`, one
rollout, **not evidence and no claim about learning**):

| Arm | mean shared reward | per-agent service rate | renew fraction | `M` |
| --- | --- | --- | --- | --- |
| `off`, `k = 10` | 0.168333 | 0.3625 / 0.4375 / 0.4625 | 0.100 | — |
| `d2` D0 | 0.168333 | 0.3625 / 0.4375 / 0.4625 | 0.100 | 8 |
| `d2`, `c = 0` | 0.000000 | 0 / 0 / 0 | 1.000 | 80 |

Test 2 also asserts, one level stronger than ADR 01 invariant 2 requires, that
the D0 and `off` runs produce identical decoded roles, service indicators and
rewards on the first rollout (before either has updated). That follows from the
skills being bit-equal at D0 on the same seed, which the D2 report records; only
the boundary equality is a claim of the ADR.

### Could not verify

* **No learning claim.** One or two rollouts per arm, one seed, no E-series run.
  Nothing here says whether the stack learns anything on the corridor.
* **`off` versus D0 beyond the first rollout.** The trajectory equality above is
  asserted only before the first update. After an update the two arms optimise
  different (discounted versus undiscounted) targets and are not expected to
  agree; that was observed to still agree on a second rollout in one manual run,
  which is not asserted anywhere and should not be relied on.
* **Scale.** Everything ran at `N = 3`, `K = 2`, `H = 40`, two lanes, on CPU with
  `torch.set_num_threads(1)`. The E3/E4 proposal object (`N = 6`, `H = 400`,
  `Delta` per level) has not been run through the learner, so the corridor's
  `M`, parameter count, optimizer-step count and norm displacement remain the
  prospective exposure-line quantities section 6 lists.
* **Reference comparison.** The driver logs no reference return; nothing here
  compares the learner against `J_sw`, `J_k` or `J_open`, and no margin is
  measured.
* **Checkpointing.** No checkpoint was saved or restored through this route.
* **The D2 `c` grid** is still unfixed; test 3 uses `c = 0` because it is the
  extreme that makes the mask non-trivially different from the `off` boundaries,
  not because it is a registered arm.
