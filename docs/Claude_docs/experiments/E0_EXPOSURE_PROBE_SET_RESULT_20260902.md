# E0 result — exposure line and frozen probe set on scenario 1 (`off` versus D0)

Executed 2026-09-02 by Claude Code (Fable 5.1) against the launch contract
`E0_EXPOSURE_PROBE_SET_20260902.md`. **Claim ceiling B — EXPLORE, integrity and exposure only.**
Nothing here is a performance comparison between the arms; the `off`-versus-D0 numbers in §6 are
integrity checks, and the returns in §5 are counters, not results.

Runner: `scripts/run_flexible_skill_duration_e0.py` (new file; `git check-ignore -v` on the path
returns nothing, i.e. it is tracked). Interpreter for every command:
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

Sections 1–3 were written and committed to the working tree **before** the arms were launched, as
contract §4 step 2 requires. Sections 4 onwards were written after.

| Fact | Value |
| --- | --- |
| Code sha recorded in every manifest (worktree HEAD at launch) | `9a8cd9011f42` (`Add the E0 launch contract …`); `b251d0f2d` is an ancestor, so contract §2's "at or after `b251d0f2d`" holds |
| Worktree cleanliness at launch | `git status --porcelain` listed **two** entries, both untracked documents of this task (`E0_EXPOSURE_PROBE_SET_RESULT_20260902.md`, `E0_probe_set_sample_seed1.json`). **No** modification under `hmasd/`, `config_1.py`, `envs/` or `tests/`. The manifests' `code_dirty: true` refers only to those two documents |
| Machine | `Jacob`, Windows-10-10.0.26200-SP0, AMD64 Family 25 Model 117 (AMD), 16 logical CPUs |
| Interpreter / libraries | Python 3.10.20, torch 2.7.0+cpu, numpy 1.26.3, device `cpu` |
| Run directories | `temp/directions/flexible_skill_duration/exp/E0_20260902/{timing_off_1thread, timing_off_4thread, off_seed1, d0_seed1}` (gitignored) |

---

## 1. Choices the contract left open

The contract is the whole authority. Where it is silent, the reading that keeps this run an
integrity check (no performance claim) was taken, and the choice is recorded here.

| Point | Choice | Why |
| --- | --- | --- |
| Meaning of `base_seed` for the training lanes | the arm's `--seed`, so lanes carry seeds `S, S+1, …, S+num_envs-1`; the same integer also seeds `random`, `numpy.random` and `torch` | contract §2 says "seeds `base_seed + rank`" without naming `base_seed`; tying it to the arm seed is the only reading that makes seed 1 and seed 2 different runs |
| Who runs the resource preflight | the runner itself, as its first action, before any RNG master, model, optimizer, buffer or result exists; a missing or non-passing receipt raises and quarantines the arm | contract §4 step 3 requires it "immediately before every arm" and §6 lists `preflight.json` among the runner's outputs; running it inside the runner satisfies both and cannot be forgotten |
| Evaluation isolation | a **second** `HMASDAgent` on its own 8 lanes, weight- and normaliser-synced from the learner before each evaluation and held in `train(False)`; construction and every evaluation run inside a saved/restored RNG state | `agent.step` keeps per-environment skills, timers and hidden states keyed by lane index, so evaluating on the learner would overwrite training lanes 0–7. The RNG save/restore makes the learner's trajectory independent of the evaluation schedule, which is what lets the rollout-1 integrity checks mean anything |
| Evaluation schedule | after rollout `r` when `r % 5 == 0` or `r == R` (deduplicated), plus immediately before an instability stop | contract §3: "every 5 rollouts and after the last" |
| `M` for the `off` arm | `high_level_valid_mask[:T].sum()` | contract §3: "`off`: valid mask count" |
| `M` for the D0 arm | `rows_M` from `get_d2_metrics()` (the union of the agent and team row masks) | contract §3 |
| High-level target scale | `mean(abs(returns))` over the valid rows of the head, read from the rollout buffer after `agent.update` computed the advantages and **before** `clear_buffers` | this is the exact quantity `hmasd/agent.py` already records as `target_scale_team` / `target_scale_agent` for `d2` (agent.py:5878-5886); computing the `off` side the same way is the only way the ratio compares like with like |
| Direction of the target-scale ratio | reported as `off / d2`, which is the direction that equals `tau(1-gamma)/(1-gamma^tau) = 1.045829` | contract §3 names `off / d2`; the D2 implementation report §6 item 2 records the same convention question |
| Optimizer step counts | the runner replaces the bound `step` of each of the agent's optimizer *instances* with a counting wrapper (coordinator, discoverer actor, discoverer critic, team discriminator, individual discriminator) | the agent exposes no such counter, and the task forbids editing `hmasd/`; an instance attribute leaves the imported module untouched |
| Probe-set digest | both a `file_sha256` of the `.npz` and a container-independent `content_sha256` over the named arrays (dtype, shape, bytes, sorted by key) | `np.savez` writes a zip whose entries carry the wall-clock time, so the file digest is not reproducible across regenerations; the content digest is the one that answers "did the regenerated set match" |
| 32-probe JSON sample | the first 32 probes in the npz's canonical order (rollout ascending, then flat `(t, lane)` position ascending) | contract §5 asks for "a 32-probe sample with the same fields" and does not fix which 32; a deterministic prefix keeps the sample checkable |
| Bootstrap for the discoverer at a rollout boundary | copied verbatim from the Phase 0 fingerprint driver (`train_multiproc_config_1.py:4942-5005`) | contract §2 names that loop. With `rollout_length == episode_length` every lane is on a fresh reset at the boundary, so `next_env_step % k != 0` always and the `assign_skills` branch is never taken in either arm — no extra RNG draw, no arm asymmetry |
| `scripts/hmasd_run.py` not used | as contract §7 directs; the runner writes its own `manifest.json` with the code sha, config dump, arm, seed, machine identity, torch/numpy versions, thread setting, command line, preflight receipt and start/end times | contract §7 |

---

## 2. Timing run (contract §4 step 1) — not evidence

Two rollouts of the `off` arm at the §2 configuration (scenario 1, `n_uavs = 6`, `n_users = 50`,
`episode_length = 500`, `rollout_length = 500`, `num_envs = 32`, `k = 10`, seed 1), once with
`torch.set_num_threads(1)` and once with `torch.set_num_threads(4)`. Both wrote a passing preflight
receipt. Each ran one evaluation (after the last rollout), so the evaluation cost is measured too.

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e0.py \
  --arm off --seed 1 --rollouts 2 --num-envs 32 --threads 1 \
  --run-name timing_off_1thread \
  --output-root temp/directions/flexible_skill_duration/exp/E0_20260902

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e0.py \
  --arm off --seed 1 --rollouts 2 --num-envs 32 --threads 4 \
  --run-name timing_off_4thread \
  --output-root temp/directions/flexible_skill_duration/exp/E0_20260902
```

| Setting | collection s (r1, r2) | update s (r1, r2) | rollout+update mean s | evaluation s | 2-rollout wall s | rows `M` |
| --- | --- | --- | --- | --- | --- | --- |
| `torch.set_num_threads(1)` | 242.0, 241.7 | 330.9, 331.1 | **572.8** | 60.8 | 1209.3 | 1600, 1600 |
| `torch.set_num_threads(4)` | 239.7, 240.5 | 181.3, 182.8 | **422.2** | 61.0 | 908.4 | 1600, 1600 |

**4 threads is the faster setting and was kept** (1.357× faster per rollout). The gain is entirely
in the PPO update (331.0 s → 182.1 s, 1.82×); collection is unchanged (241.9 s → 240.1 s) because
it is 500 sequential small-batch inference calls interleaved with single-threaded Python
environment stepping. This does not contradict the `torch.set_num_threads(1)` default recorded in
`CLAUDE.md`: that default was measured at ~15k parameters and batch 16, whereas the E0 update runs
15 PPO epochs over 16,000 × 6 low-level rows. Both timing runs independently show `M = 1600` at
`num_envs = 32`, i.e. the contract's own arithmetic (`32 × 500 / 10`) holds at its configuration.

## 3. Choice of `R`, and one recorded deviation (contract §4 step 2)

At the measured 4-thread rate, one arm at `num_envs = 32` and `R = 10` would cost
`10 × 422.2 + 2 × 61 = 4344 s = 72.4 min`, which **exceeds the contract's 60-minute ceiling**, and
two arms would exceed the session's wall-clock budget. The contract also forbids `R < 10`.

**Deviation D1, recorded:** `num_envs` reduced from 32 to **16**; `R = 10` kept. This is the
deviation the executing instruction prescribes for exactly this case ("if the timing run says two
arms cannot fit at `R = 10`, reduce `num_envs` to 16, recording the deviation, rather than `R`
below 10").

Consequences, stated so no reader is misled:

- transitions per arm: `10 × 500 × 16 = 80,000`, **not** the contract's 160,000. The contract's
  "at least 160,000 transitions per arm" clause is **not met**; this is a shortfall, not a
  reinterpretation.
- the expected high-level row count becomes `M = num_envs × rollout_length / k = 16 × 500 / 10 =
  **800**` per rollout, not the contract's 1600. The check in §6 is therefore run as "`M` equals
  800 in both arms and the two arms agree", the same test with the `num_envs`-dependent constant
  recomputed. `M = 1600` at `num_envs = 32` is confirmed separately by the two timing runs.
- everything else is unchanged: seeds, `k = 10`, `episode_length = rollout_length = 500`, the
  8 evaluation lanes with seeds `10_000 + rank`, the probe recipe.

**Estimate written before launch:** ~215–230 s per rollout, so `R = 10` plus two evaluations was
estimated at **38–42 min for the `off` arm** and **45–60 min for the D0 arm**. Measured: `off`
2260.4 s = **37.7 min** (213.6 s per rollout), D0 2392.4 s = **39.9 min** (225.2 s per rollout).
The D0 estimate was pessimistic: the extra teacher-forced coordinator pass cost 12.4 s of
coordinator inference over 549 calls per rollout, about 5% of collection, not the 9× the D2
implementation report measured for the *skill-assignment sub-step alone* at a much smaller
configuration.

---

## 4. Configuration actually run

| Field | `off` arm | D0 arm |
| --- | --- | --- |
| `policy_interruption_mode` | `off` | `d2` |
| `interruption_cost_c`, `interruption_cost_c_Z` | — | `inf`, `inf` |
| `skill_cap_k_max`, `team_cap_k_Z`, `interruption_delta`, `age_feature` | — | 10, 10, 1, `off` |
| `n_agents` / `n_uavs` / `n_users` | 6 / 6 / 50 | 6 / 6 / 50 |
| `num_envs`, `rollout_length`, `episode_length`, `k` | 16, 500, 500, 10 | 16, 500, 500, 10 |
| `gamma`, `ppo_epochs`, `lr_coordinator`, `use_valuenorm` | 0.99, 15, 1e-4, True | same |
| `n_Z`, `n_z`, `state_dim`, `obs_dim` | 6, 6, 119, 104 | same |
| `total_timesteps` (replaced by `R`) | 80,000 | 80,000 |
| seed / lane seeds | 1 / 1…16 | 1 / 1…16 |
| evaluation lanes / seeds | 8 / 10,000…10,007 | same |
| `torch.set_num_threads` | 4 | 4 |

Commands:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e0.py \
  --arm off --seed 1 --rollouts 10 --num-envs 16 --threads 4 \
  --probe-out temp/directions/flexible_skill_duration/probes/E0_probe_set_seed1.npz \
  --probe-json-out docs/Claude_docs/experiments/E0_probe_set_sample_seed1.json \
  --probe-json-count 32 \
  --output-root temp/directions/flexible_skill_duration/exp/E0_20260902

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e0.py \
  --arm d0 --seed 1 --rollouts 10 --num-envs 16 --threads 4 \
  --reference-dir temp/directions/flexible_skill_duration/exp/E0_20260902/off_seed1 \
  --output-root temp/directions/flexible_skill_duration/exp/E0_20260902
```

Resource preflight, run by the runner as its first action, both passing
(`MINIMUM_AVAILABLE_MEMORY_BYTES = 4 GiB`, `measurement_source: GlobalMemoryStatusEx`):

| Arm | `assessed_at` | available physical = effective | `passed` |
| --- | --- | --- | --- |
| `off` seed 1 | 2026-09-02T17:21:06.474541Z | 18,571,177,984 B (17.3 GiB) | `true` |
| D0 seed 1 | 2026-09-02T17:59:03Z (receipt) | 18,505,515,008 B (17.2 GiB) | `true` |

Both arms ran to `R = 10` with no non-finite loss or return at any rollout, so the stop rule fired
at `R` in both cases. **Nothing was quarantined.**

## 5. The arms

Both arms: 10 of 10 rollouts, **80,000 environment transitions**, **160 completed episodes**
(16 lanes × 10 rollouts; `episode_length == rollout_length`, so every lane completes exactly one
episode per rollout), `M = 800` in every rollout, **2 evaluations** (after rollouts 5 and 10),
8 deterministic episodes each.

Optimizer steps per network, cumulative over the run (identical in the two arms):

| Network | steps per rollout | total over R = 10 |
| --- | --- | --- |
| coordinator | 105 | **1,050** |
| discoverer actor | 2,250 | **22,500** |
| discoverer critic | 2,250 | **22,500** |
| team discriminator | 15 | **150** |
| individual discriminator | 60 | **600** |

Evaluation (8 deterministic episodes on lanes seeded `10_000 + rank`):

| Arm | rollout 5 mean ± sd | rollout 10 (final) mean ± sd | wall s per evaluation |
| --- | --- | --- | --- |
| `off` | 25.4862 ± 8.3521 | **22.6482 ± 5.6378** | 60.7, 60.8 |
| D0 | 29.7630 ± 6.7829 | **35.8630 ± 4.0421** | 68.8, 69.0 |

These two evaluation means are **not** compared. Two seeds were not run (§8), one arm never repeats
an evaluation on the same weights, and the contract's non-goals forbid a performance claim.

### 5.1 Exposure line, `off` arm (seed 1)

`||theta - theta_0|| / ||theta_0||`, float64, against parameters captured at `HMASDAgent`
construction. Columns: coordinator, discoverer actor, discoverer critic, team discriminator,
individual discriminator.

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8000 | 16 | 800 | 105 | 21.4564 | 0.4291 | 2.752278e-02 | 1.506677e-01 | 7.449193e-02 | 1.123201e-02 | 2.296593e-02 | 122.3 | 90.9 |
| 2 | 16000 | 32 | 800 | 210 | 21.1580 | 0.4232 | 3.396643e-02 | 2.355439e-01 | 1.052058e-01 | 1.601866e-02 | 3.260627e-02 | 122.5 | 91.1 |
| 3 | 24000 | 48 | 800 | 315 | 16.3960 | 0.3279 | 3.811696e-02 | 2.987660e-01 | 1.261718e-01 | 2.056054e-02 | 4.105406e-02 | 122.1 | 91.2 |
| 4 | 32000 | 64 | 800 | 420 | 24.7321 | 0.4946 | 4.019489e-02 | 3.642779e-01 | 1.476301e-01 | 2.383094e-02 | 4.696318e-02 | 122.7 | 91.7 |
| **5** | 40000 | 80 | 800 | 525 | 22.6619 | 0.4532 | **4.328831e-02** | **4.131838e-01** | **1.651695e-01** | **2.681264e-02** | **5.278171e-02** | 122.2 | 90.8 |
| 6 | 48000 | 96 | 800 | 630 | 19.3800 | 0.3876 | 4.596949e-02 | 4.576649e-01 | 1.796718e-01 | 2.946624e-02 | 5.776127e-02 | 122.1 | 91.2 |
| 7 | 56000 | 112 | 800 | 735 | 23.1133 | 0.4623 | 4.838176e-02 | 5.000100e-01 | 1.931612e-01 | 3.196659e-02 | 6.185062e-02 | 122.9 | 91.3 |
| 8 | 64000 | 128 | 800 | 840 | 17.5864 | 0.3517 | 5.180507e-02 | 5.332780e-01 | 2.067042e-01 | 3.390447e-02 | 6.570330e-02 | 122.1 | 91.2 |
| 9 | 72000 | 144 | 800 | 945 | 20.3213 | 0.4064 | 5.521214e-02 | 5.650638e-01 | 2.193025e-01 | 3.601940e-02 | 6.906774e-02 | 122.4 | 91.3 |
| **10** | 80000 | 160 | 800 | 1050 | 14.0310 | 0.2806 | **5.904588e-02** | **5.901974e-01** | **2.312708e-01** | **3.796294e-02** | **7.204491e-02** | 122.7 | 91.3 |

### 5.2 Exposure line, D0 arm (seed 1)

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 8000 | 16 | 800 | 105 | 21.4564 | 0.4103 | 2.710806e-02 | 1.506677e-01 | 7.449193e-02 | 1.123201e-02 | 2.296593e-02 | 134.9 | 91.3 |
| 2 | 16000 | 32 | 800 | 210 | 21.1696 | 0.4048 | 3.528706e-02 | 2.438669e-01 | 1.035925e-01 | 1.595166e-02 | 3.232682e-02 | 134.4 | 90.6 |
| 3 | 24000 | 48 | 800 | 315 | 20.3012 | 0.3883 | 3.883664e-02 | 3.047080e-01 | 1.252938e-01 | 2.048543e-02 | 3.998479e-02 | 133.9 | 90.8 |
| 4 | 32000 | 64 | 800 | 420 | 23.8400 | 0.4559 | 4.078251e-02 | 3.637415e-01 | 1.450216e-01 | 2.380407e-02 | 4.626581e-02 | 134.3 | 91.2 |
| **5** | 40000 | 80 | 800 | 525 | 26.3686 | 0.5042 | **4.268218e-02** | **4.200825e-01** | **1.631083e-01** | **2.681622e-02** | **5.197953e-02** | 134.4 | 90.3 |
| 6 | 48000 | 96 | 800 | 630 | 22.5585 | 0.4314 | 4.616657e-02 | 4.661880e-01 | 1.780244e-01 | 2.975020e-02 | 5.690666e-02 | 134.2 | 90.6 |
| 7 | 56000 | 112 | 800 | 735 | 24.5606 | 0.4697 | 4.920188e-02 | 5.075745e-01 | 1.921554e-01 | 3.265503e-02 | 6.155948e-02 | 134.7 | 90.7 |
| 8 | 64000 | 128 | 800 | 840 | 24.6408 | 0.4712 | 5.159370e-02 | 5.396593e-01 | 2.046016e-01 | 3.491855e-02 | 6.640563e-02 | 134.2 | 90.7 |
| 9 | 72000 | 144 | 800 | 945 | 22.0316 | 0.4214 | 5.441876e-02 | 5.709721e-01 | 2.180538e-01 | 3.673762e-02 | 7.028473e-02 | 134.3 | 90.9 |
| **10** | 80000 | 160 | 800 | 1050 | 26.3036 | 0.5030 | **5.692107e-02** | **5.973675e-01** | **2.303658e-01** | **3.853924e-02** | **7.408981e-02** | 134.7 | 90.4 |

**Both learners move.** Every network's exposure line is strictly increasing in the rollout index
in both arms, from ~1e-2 to between 3.8e-2 and 5.9e-1 by rollout 10. The coordinator's D0 exposure
line reproduces `get_d2_metrics()['param_displacement']` to every printed digit at every rollout
(e.g. rollout 10: 0.056921 both ways), which is an independent check that the runner's float64
exposure computation agrees with the one `hmasd/agent.py` already performs.

An unplanned but informative observation: at rollout 1 the **discoverer actor, discoverer critic,
team discriminator and individual discriminator exposure lines are bit-identical between the arms**
(1.506677e-01 / 7.449193e-02 / 1.123201e-02 / 2.296593e-02), and only the coordinator differs
(2.752278e-02 `off` versus 2.710806e-02 D0). That is exactly what the D0 construction predicts: the
first rollout's trajectory, boundaries and skills are identical, so the low-level and discriminator
updates see identical data; only the coordinator's targets differ (undiscounted versus discounted
segment sums). From rollout 2 on the arms diverge everywhere, as contract §3 says they must.

### 5.3 D0-only `get_d2_metrics()` (contract §3)

`d2_metrics` is **reset by `clear_buffers` at agent.py:1481**, so the dict written to
`metrics.jsonl` each rollout is already a per-rollout quantity, not a running total. The values
below were identical in all ten rollouts.

| Field | Value (every rollout) |
| --- | --- |
| `steps` | 8,000 (500 × 16) |
| `decision_steps` / `team_decisions` | 800 / 800 |
| `sampled_total` / `forced_total` | 4,800 / 43,200 |
| `rows_M` / `rows_M_team` / `rows_M_agent` | 800 / 800 / 4,800 |
| `cause_counts` | `reset` 16, `team_cap` 784, **`gap` 0, `team_gap` 0, `cap` 0** |
| `segment_length_agent_mean` / `segment_length_team_mean` | 10.0 / 10.0 |
| `S_t_fraction` (over all steps) | 0.10 |
| `S_t_fraction` at decision steps | `sampled_total / (team_decisions × n_agents) = 4800 / (800 × 6)` = **1.000** |
| `optimizer_steps` (coordinator) | 105 |
| `coordinator_inference_seconds` / `calls` (rollout 10) | 12.4 s / 549 |
| `gap_agent_hist` (rollout 10) | n = 47,904, mean 0.27384, sd 0.25838, min 0.0, q10/q50/q90 = 0.0 / 0.22311 / 0.64437, max 1.65523 |
| `gap_team_hist` (rollout 10) | n = 7,984, mean 0.44342, sd 0.40634, min 0.0, q10/q50/q90 = 0.0 / 0.42157 / 1.00460, max 1.64492 |
| `switch_count_by_agent` (rollout 10) | [653, 658, 685, 668, 652, 646] |

All three of the contract's D0 conditions hold: causes are `reset` and `team_cap` only;
`gap`, `team_gap` and `cap` are zero; `S_t_fraction` at decision steps is 1.0.
`reset` 16 + `team_cap` 784 = 800 = the decision-step count = `M`.

## 6. The three integrity checks (contract §3), rollout 1, `off` versus D0, seed 1

Machine-written to
`temp/directions/flexible_skill_duration/exp/E0_20260902/d0_seed1/integrity_checks.json`.

| Check | Result | Numbers |
| --- | --- | --- |
| **1. boundary mask `[T, E]` identical** | **PASS** | shape (500, 16) = 8,000 entries; **0 mismatches**; 800 boundaries in each arm |
| **1b. `M` equal in both arms and equal to `num_envs × rollout_length / k`** | **PASS** at the deviated `num_envs = 16` | `M` = **800** in both arms, expected 800. (The contract's literal `M = 1600` requires `num_envs = 32`; it was confirmed at that value by both timing runs, §2) |
| **2. rollout-1 team and agent skills identical** | **PASS** | team skills (500, 16): **0 mismatches** of 8,000; agent skills (500, 16, 6): **0 mismatches** of 48,000 |
| **3. high-level target-scale ratio `off / d2` in [1.03, 1.06]** | **PASS** | team head: `2.690068244934082 / 2.5720436573028564` = **1.045887**; agent head: `2.6905159950256348 / 2.572490930557251` = **1.045880**; `tau(1-gamma)/(1-gamma^tau)` at `tau = 10, gamma = 0.99` = **1.045829**. Deviation from the closed form: `+5.8e-05` (team), `+5.1e-05` (agent) |

The measured ratio sits 5.5e-05 above the constant-reward closed form, which is the "spread by the
reward mix" the contract anticipates; it is far inside the [1.03, 1.06] band.

## 7. Probe set (contract §5)

| Field | Value |
| --- | --- |
| Source | `off` arm, seed 1, rollouts **1, 5, 10** (`1`, `ceil(R/2)`, `R`) |
| Probe RNG seed | 20260902 (`numpy.random.default_rng`), a stream separate from the learner's |
| Probes per rollout / total | 512 / **1,536** |
| Local file | `temp/directions/flexible_skill_duration/probes/E0_probe_set_seed1.npz` (5,420,786 B; `*.npz` is gitignored) |
| **`content_sha256`** (array digest, container-independent) | `1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c` |
| `file_sha256` (of the zip container) | `9f25281062b431408b3a4629da4e3033ff111dc0ddc2ab0503ea0e956425d8ad` |
| 32-probe JSON sample | `docs/Claude_docs/experiments/E0_probe_set_sample_seed1.json` (tracked) |

Shapes and dtypes:

| Array | Shape | dtype |
| --- | --- | --- |
| `states` | (1536, 119) | float64 |
| `observations` | (1536, 6, 104) | float32 |
| `team_skills` | (1536,) | int64 |
| `agent_skills` | (1536, 6) | int64 |
| `env_step` | (1536,) | int64 |
| `rollout_index` | (1536,) | int64 |
| `lane` | (1536,) | int64 |

Generation recipe, verbatim from `summary.json`:

> `rng = numpy.random.default_rng(probe_seed); for each rollout in [1, ceil(R/2), R] in ascending
> order: idx = rng.choice(rollout_length * num_envs, size=probes_per_rollout, replace=False), then
> sorted ascending; a position p maps to (t, lane) = divmod(p, num_envs); the probe stores the
> policy input state and observations at step t of that rollout together with the team and agent
> skills `agent.step` assigned at that step, the lane's env_step, the rollout index and the lane
> index.`

Note that the position space is `rollout_length * num_envs = 500 × 16 = 8,000`, a consequence of
deviation D1. Regenerating the set on a different `num_envs` will **not** reproduce this digest.

`np.savez` stamps its zip entries with the wall-clock time, so `file_sha256` is not reproducible
across regenerations; **`content_sha256` is the digest that answers "did it match"**. The copy at
`C:/Projects/HMASD/temp/directions/flexible_skill_duration/probes/E0_probe_set_seed1.npz` was
re-hashed after copying and matches both digits-for-digit.

## 8. Verbatim summary lines

The runner's final stdout line for each arm, unedited:

`off` seed 1:

```
{"arm": "off", "seed": 1, "completed": true, "rollouts_completed": 10, "transitions_total": 80000, "episodes_total": 160, "optimizer_steps_total": {"coordinator": 1050, "discoverer_actor": 22500, "discoverer_critic": 22500, "team_discriminator": 150, "individual_discriminator": 600}, "evaluation_count": 2, "final_evaluation_return_mean": 22.648224557174537, "exposure_line_rollout_last": {"coordinator": 0.05904587990125509, "discoverer_actor": 0.5901973954041629, "discoverer_critic": 0.23127075676401765, "team_discriminator": 0.037962940375973336, "individual_discriminator": 0.07204490920702403}, "wall_seconds_total": 2260.393313099994, "seconds_per_rollout_mean": 213.5957679700019, "run_dir": "C:\\Projects\\HMASD\\.claude\\worktrees\\agent-a5ae2957862d225cd\\temp\\directions\\flexible_skill_duration\\exp\\E0_20260902\\off_seed1"}
```

D0 seed 1:

```
{"arm": "d0", "seed": 1, "completed": true, "rollouts_completed": 10, "transitions_total": 80000, "episodes_total": 160, "optimizer_steps_total": {"coordinator": 1050, "discoverer_actor": 22500, "discoverer_critic": 22500, "team_discriminator": 150, "individual_discriminator": 600}, "evaluation_count": 2, "final_evaluation_return_mean": 35.86302269262961, "exposure_line_rollout_last": {"coordinator": 0.05692106996317533, "discoverer_actor": 0.5973674892741064, "discoverer_critic": 0.2303657501297044, "team_discriminator": 0.03853923711886955, "individual_discriminator": 0.0740898127358075}, "wall_seconds_total": 2392.400967900001, "seconds_per_rollout_mean": 225.15631551999977, "run_dir": "C:\\Projects\\HMASD\\.claude\\worktrees\\agent-a5ae2957862d225cd\\temp\\directions\\flexible_skill_duration\\exp\\E0_20260902\\d0_seed1"}
```

Timing runs (not evidence): 1 thread `"wall_seconds_total": 1209.3`, `"seconds_per_rollout_mean":
572.8`; 4 threads `"wall_seconds_total": 908.4`, `"seconds_per_rollout_mean": 422.2`.

## 9. Deviations, and what was not done

| # | Deviation | Status |
| --- | --- | --- |
| D1 | `num_envs` 32 → 16, hence 80,000 transitions per arm instead of 160,000 and `M = 800` instead of 1600 | §3; forced by the measured rate against the contract's 60-minute-per-arm ceiling; explicitly authorised by the executing instruction |
| D2 | **Seed 2 not run for either arm** | Contract §2's condition ("seed 2 … only if seed 1 of one arm finished within 45 minutes") **was met** — both arms finished in 37.7 and 39.9 minutes. Seed 2 was nevertheless *not* launched because the session's ~3-hour wall-clock cap had already been reached when seed 1 of D0 completed. Recorded as **not run**, with this reason. It is the one contract clause this run declines rather than satisfies |
| D3 | `scripts/hmasd_run.py prepare/execute/reconcile` not used | as contract §7 directs; the runner writes an equivalent manifest |
| D4 | The `d2_metrics_delta` field written into `d0_seed1/metrics.jsonl` is meaningless | It was computed as "this rollout minus the previous rollout" on the assumption that `get_d2_metrics()` accumulates. It does not — `clear_buffers` resets it (agent.py:1481) — so the delta reads zero for rollouts 2–10 while the raw `d2_metrics` dict beside it is already the correct per-rollout value. The raw dict is what §5.3 reports. The runner was **not** edited after the evidence was produced, so the committed script is byte-identical to the one that ran; the field is documented here as an artifact to ignore rather than silently repaired |

## 10. Could not verify

- **Nothing about which arm is better.** Two evaluations per arm, one seed, `R = 10`, no repeats.
  The D0 final evaluation mean (35.86) is higher than `off`'s (22.65) and the per-rollout training
  returns are noisy in both arms; under the contract's non-goals this is **not** a signal and must
  not be quoted as one. A B-class comparison needs E1 and later.
- **Seed 2**, for either arm (deviation D2). No seed-count claim is available.
- **The contract's transition floor.** 80,000 per arm against the contract's 160,000 (deviation
  D1). Whether the exposure lines would look different at 32 lanes is untested.
- **`M = 1600`** is verified only in the two timing runs (2 rollouts each, no probe set, no seed-2
  arm), not in the arms that carry the exposure lines.
- **The `off` arm's high-level target scale** is computed by this runner from the rollout buffer,
  not by `hmasd/agent.py`, which records `target_scale_team` / `target_scale_agent` only in the
  `d2` path. The two computations were made textually identical (`mean(abs(returns))` over the
  head's valid rows, read after `agent.update` and before `clear_buffers`), and the D0 side agrees
  with `get_d2_metrics()` — but the `off` side has no in-repo second implementation to check
  against.
- **Evaluation isolation is argued, not proved.** The evaluation agent is a second `HMASDAgent`
  synced by `state_dict` plus deep copies of `obs_norm`, `state_norm` and both value normalisers.
  If the learner carried any *other* state that affected deterministic action selection, the
  evaluation would silently use a stale value. No test in the repo covers this; the rollout-1
  integrity checks passing after two evaluator constructions is weak evidence that the RNG
  save/restore worked, nothing more.
- **Checkpoint restore was not exercised.** `checkpoint_final.pt` was written by
  `agent.save_model` in each arm and never loaded back. (`agent.save_model` pickles the config
  object, so the runner's config class had to be module-level; that is a runner detail, not a
  finding about `hmasd/`.)
- **The timing comparison is one machine, one day, two runs, no repeats**, and the 1-thread /
  4-thread numbers were taken at `num_envs = 32` while the arms ran at 16. The claim "4 threads is
  faster here" is not a benchmark.
- **No CUDA comparison** is possible: neither declared conda env has CUDA (as `CLAUDE.md` records).
- **The `off` arm's rollout-1 artifacts** (`rollout1_*.npy`) are the *only* reference the D0 arm
  compared against. They were produced in the same session on the same machine; nothing
  independently re-derived them.

---

## 11. Interpretation boundary (contract §8)

Bounded to scenario 1 with six UAVs and fifty users, one machine, **one seed**, `R = 10` rollouts
at **16** lanes, and the measurements above. E0 shows that both learners run and move within their
budget, that at D0 the `d2` path reproduces the `off` boundaries, skills and row count on the first
rollout exactly and its target scale by the predicted `1.0458` factor, and it freezes a 1,536-probe
set for the C1/C2 measurements of E1 and later. It says nothing about which arm is better, about
finite `c`, or about the corridor.
