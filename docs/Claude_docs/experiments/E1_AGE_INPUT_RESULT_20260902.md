# E1 result — age input to the discriminators at fixed `k` (D0 versus D1, scenario 1)

Executed 2026-09-02/03 by Claude Code (Fable 5.1) against the launch contract
`E1_AGE_INPUT_20260902.md`. **Claim ceiling B — EXPLORE.** Nothing here is a claim that one arm
is better; the returns are counters carried with the E0 caveat, and the only verdict offered is
the contract's own §5 reading rule applied to its own numbers.

Runner: `scripts/run_flexible_skill_duration_e1.py`; study-level aggregator
`scripts/run_flexible_skill_duration_e1_aggregate.py`; test
`tests/flexible_skill_duration_e1_test.py`. `git check-ignore -v` returns nothing for all three,
i.e. they are tracked. Interpreter for every command:
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

| Fact | Value |
| --- | --- |
| Launch commit (contract §2, recorded in every manifest as `e1.launch_commit`) | `6fba1c7ba` ("Accept the throughput refactor P0-P3 (review Part X)") |
| Worktree branch | `e1-age-input-20260902` |
| Branch sha in the manifests (`code_sha`, the worktree HEAD at each launch) | `eb5318ec115d` for the seed-1 pair; `b9290a1ed9ea` for the seed-2 and seed-3 pairs |
| Is the runner the same file in all six runs? | **Yes.** `git diff eb5318ec1 b9290a1ed -- scripts/run_flexible_skill_duration_e1.py` is empty; the intervening commit added the aggregator and edited the test only |
| `code_dirty` | `true` for the seed-1 pair (the aggregator was then untracked and the test edited in the working tree); `false` for the seed-2 and seed-3 pairs |
| Machine | `Jacob`, Windows-10-10.0.26200-SP0, AMD64 Family 25 Model 117 (AMD), 16 logical CPUs |
| Interpreter / libraries | Python 3.10.20, torch 2.7.0+cpu, numpy 1.26.3, device `cpu`, `torch.set_num_threads(4)` |
| Study root | `C:/Projects/HMASD/temp/directions/flexible_skill_duration/exp/E1_20260902/` (gitignored) |
| Run directories carrying evidence | `d0_seed1_r2`, `d1_seed1_r2`, `d0_seed2`, `d1_seed2`, `d0_seed3`, `d1_seed3` |
| Quarantined, carrying no evidence | `d0_seed1`, `d1_seed1` (§8 deviation D1) |
| Study-level output | `E1_summary.json` at the study root |

**The §5 reading, up front** (the deciding numbers are in §7; nothing else in this document is a
verdict). Applying contract §5's rule to the window `r >= 10` it defines: on **team** probe accuracy
the verdict is **`neither`** — the rule's "contradicted" branch needs the `7-9` gain to exceed the
`0-2` gain by more than the across-seed spread in at least two of three seed pairs, and that happens
in **0 of 3**; its "supported" branch needs every seed's gain to be within its bucket's across-seed
spread, and the `7-9` bucket fails that at seed 1. On **individual** probe accuracy the verdict is
**`supported`** — 0 of 3 pairs exceed, and all three buckets are within spread. At the final rollout
both accuracies read **`supported`**. The prediction on record is therefore **not contradicted on
any of the four applications**, and is **supported on three of the four**.

---

## 1. Choices the contract left open

The contract is the whole authority. Where it is silent, the reading recorded here is the one that
was used; each is stated so a reader can disagree with it explicitly.

| Point | Choice | Why |
| --- | --- | --- |
| How the E0 loop is "imported rather than copied" (contract §2) | `scripts/run_flexible_skill_duration_e1.py` imports `scripts/run_flexible_skill_duration_e0.py` and calls its `_execute()` unchanged, wrapping exactly two of its module-level names: `_make_config` (so the `d1` arm's config carries `age_feature="normalized"`) and `_exposure_line` (the per-rollout hook the §3 measurements run in). The E0 file was **not edited**; it is post-evidence | contract §2 says the E1 runner "imports the E0 runner's loop rather than copying it". `_execute` exposes no hook, so the only alternatives were editing E0 (forbidden) or copying it (forbidden) |
| Where in the rollout the §3 measurements are taken | in the `_exposure_line` wrapper, which `_execute` calls exactly once per rollout, **after** `agent.update()` and `agent.clear_buffers()` and **outside** both of E0's timers (`rollout_wall_seconds`, `update_wall_seconds`) | contract §3 says "after every rollout's update". Hooking `agent.update` itself would have inflated E0's `update_wall_seconds`; this seam leaves every E0 counter comparable with E0's own |
| `--arm` values | `d0` and `d1` are passed straight through to E0's `_execute`. E0's `_make_config` branches only on `arm == "off"`, so both E1 arms take the D2/D0 branch; the arm string is what the manifest, the summary and the printed line record | keeps the manifests self-describing without editing E0 |
| Arm configuration | both arms: `policy_interruption_mode="d2"`, `interruption_delta=1`, `interruption_cost_c = interruption_cost_c_Z = inf`, `skill_cap_k_max = team_cap_k_Z = 10`. D0 `age_feature="off"`, D1 `age_feature="normalized"` | contract §2 (the fair D0 of ADR 01) |
| Which discriminators the config actually builds | **`TeamDiscriminator` and `IndividualDiscriminator` from `hmasd/networks.py`, not the compact (HA-CTSE) variants.** `config_1.Config.use_horizon_window = False`, so `HMASDAgent.use_ha_ctse` is `False` and both `use_compact_*_discriminator` flags are `False` (agent.py:524-537, 616-624). `config_1._validate_policy_interruption`'s guard — "`age_feature='normalized'` is not implemented for the compact discriminators" — is therefore not triggered, and the age input reaches a discriminator that accepts it (`age_input_dim = 1`, verified in the test) | the executing instruction asks which discriminator the E0 config uses; this is it, and it is the reason D1 is runnable at all |
| `num_envs` | **32**, the reviewer's decision recorded in `ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` §X.3 from the P3 timing (206 s per rollout at 4 threads, about 70 minutes per run at `R = 20`, inside the contract's 90-minute condition) | contract §2 makes 32 conditional on the P3 timing; the reviewer's launch decision resolved it |
| Execution order and concurrency | the two arms of one seed run **concurrently** as a matched pair, pairs in order seed 1, seed 2, seed 3; never more than two runs at once | the executing instruction. It replaces contract §2's strictly sequential order (D0 s1, D1 s1, D0 s2, …) while keeping its property that a stop after any pair leaves matched seeds |
| Which agent takes the measurements | a **second** `HMASDAgent`, constructed lazily inside `e0._preserve_rng()` at the first measurement and weight-/normaliser-synced from the learner before every measurement, held in `train(False)`; every forward pass under `torch.no_grad()` | contract §3: "a second agent instance synced from the learner (the E0 evaluation mechanism) so that the learner's RNG and per-lane state are untouched". It is a distinct instance from the E0 evaluator, which keeps its own 8 lanes |
| What "synced" copies | `state_dict` of the coordinator, the discoverer and both discriminators, plus deep copies of `obs_norm`, `state_norm`, `value_norm_coordinator` and `value_norm_discoverer` — exactly `Evaluator._sync` in the E0 runner, minus the per-lane resets (the probe agent never steps an environment) | the E0 mechanism, unchanged |
| Normalisation state of the probe inputs | `agent._normalize_states(states, update=False)` and `agent._normalize_observations(observations, update=False)`. **At this configuration both are the identity**: `config_1.Config` has `use_obsnorm = False` and `use_statenorm = False`, and both methods return their input unchanged when the flag is off (agent.py `_normalize_states`, `_normalize_observations`). The calls are made anyway so the code path matches the learner's discriminator path | `_compute_intrinsic_rewards_batch` normalises with `update=False` before calling the discriminators; the probe path is textually the same |
| Team label | `argmax` over `agent._team_discriminator_logits(state_tensor, None, age=team_age)`, i.e. `TeamDiscriminator(state)` on D0 and `TeamDiscriminator(state, age)` on D1 (the compact branch is dead here). Input: the probe's recorded **global state** | contract §3 item 1 |
| Individual label | `argmax` over `agent._individual_discriminator_logits(flat_obs, team_skill_tensor, None, age=agent_age)`, with `flat_obs` the probe observations reshaped to `[1536 × 6, 104]` and `team_skill_tensor` the probe's **recorded team skill** repeated over the six agents. Labels are reshaped back to `[1536, 6]` | contract §3 item 1: "conditioned on the probe's recorded team skill" |
| Age input on D1 | `(env_step mod 10) / 10`, one float32 per probe, used **for both** the team age and every agent's age (the agent age is the same value repeated over the six agents) | contract §3 item 1, verbatim. The values present in the probe set are exactly `{0,…,9}/10` |
| Age input on D0 | none is passed. `agent._d2_uses_age_feature()` is `False`, so the discriminators are called with their `off` signatures and the age array is never constructed | D0 is `age_feature="off"` by construction |
| Label agreement, team | `mean(label_r == label_{r-1})` over the 1,536 probes | contract §3 item 2 |
| Label agreement, individual | the fraction is computed **per agent** over the 1,536 probes and then averaged over the six agents | contract §3 item 2: "the same per agent for individual labels, averaged over agents". With equal probe counts per agent this coincides with the flat mean; the per-agent vector is recorded too |
| Age buckets | `{0,1,2}`, `{3,4,5,6}`, `{7,8,9}` of `env_step mod 10`; every age falls in exactly one bucket (asserted in the test). Bucket sizes on this probe set: 446, 630, 460 for team labels and three times that (2,676 / 3,780 / 2,760) for individual labels | contract §3 item 3 |
| Value heads | `agent.skill_coordinator.get_value(state_tensor, observations_tensor)` → `(state_value [1536,1], agent_values 6 × [1536,1])`, then **denormalised** with `agent._denormalize_values(v, agent.value_norm_coordinator)` because `use_valuenorm = True`. This is the same call and the same denormalisation `assign_skills` and the coordinator update use | contract §3 item 4: "the coordinator's team value head and per-agent value heads evaluated on the probes at each rollout (denormalised)" |
| Value drift | per rollout `r >= 2`, the mean over probes of `abs(V_r - V_{r-1})`; separately for the team head (`[1536]`) and the per-agent heads (mean over the `1536 × 6` entries) | contract §3 item 4, first half |
| "the variance across rollouts `r >= R/2`" | **ambiguous; both readings are reported.** (a) `*_mean_abs_change_var_window`: the variance, across the rollouts of the window, of the per-rollout mean absolute change. (b) `*_var_across_rollouts_mean_over_probes`: the per-probe variance of the value itself across the window's rollouts, averaged over probes — the reading closer to concern C1 ("variance of high-level value targets") | contract §3 item 4, second half, admits both; neither is silently chosen |
| The `r >= R/2` window | `r >= ceil(20/2) = 10`, i.e. rollouts 10…20, **eleven** checkpoints | contract §4 item 1 asks for "ten checkpoints" in the window; `ceil(R/2)` gives eleven rollouts (ten *adjacent-rollout* agreement values, since agreement at `r` needs `r-1`). Recorded as an arithmetic note, not a deviation |
| Age-feature weight share | `norm(W[:, -1]) / norm(W)` in float64, where `W` is `team_discriminator.input_projection.weight` (`[256, 120]`) and `individual_discriminator.obs_input_projection.weight` (`[256, 105]`). The age column is the **last** one because `hmasd/networks.py` appends it with `torch.cat([x, age], dim=-1)` before `input_norm` and the projection | contract §3 item 5. `None` on D0, where `age_input_dim == 0` |
| Probe-set digest | recomputed with E0's `_sha256_arrays` recipe **before anything else is built**, and a mismatch raises before the resource preflight, the RNG masters, the environments or any model exist | contract §3 names the digest; the executing instruction says to refuse the run on a mismatch |
| Study-level `E1_summary.json` | written by a separate script from the finished run directories; it measures nothing and only differences what the runs recorded | contract §6 lists it as an output without saying which program writes it |
| Manifest fields the executing instruction adds | merged into `manifest.json` and `summary.json` under a namespaced `e1` key after the run, and written standalone as `e1_probe_summary.json` | E0's `_execute` writes those two files itself and was not edited; the E1 fields (launch commit, branch sha, `num_envs`, threads, probe-set digest, the derived series) are added around it |
| `scripts/hmasd_run.py` not used | as at E0, per E0 contract §7 and spec §11.4 | the runner writes its own manifest with the same facts |

---

## 2. Configuration actually run

| Field | D0 arm | D1 arm |
| --- | --- | --- |
| `policy_interruption_mode` | `d2` | `d2` |
| `interruption_cost_c`, `interruption_cost_c_Z` | `inf`, `inf` | `inf`, `inf` |
| `skill_cap_k_max`, `team_cap_k_Z`, `interruption_delta` | 10, 10, 1 | 10, 10, 1 |
| **`age_feature`** | **`off`** | **`normalized`** |
| Discriminators built | `TeamDiscriminator` / `IndividualDiscriminator`, `age_input_dim = 0` | the same classes, `age_input_dim = 1` (`input_projection` `[256,120]`, `obs_input_projection` `[256,105]`) |
| `n_agents` / `n_uavs` / `n_users` | 6 / 6 / 50 | same |
| `num_envs`, `rollout_length`, `episode_length`, `k` | 32, 500, 500, 10 | same |
| `gamma`, `gae_lambda`, `ppo_epochs`, `num_mini_batch` | 0.99, 0.95, 15, 4 | same |
| `lr_coordinator` / `lr_discoverer_actor` / `lr_discoverer_critic` / `lr_discriminator` | 1e-4 each | same |
| `use_valuenorm`, `use_obsnorm`, `use_statenorm` | `True`, `False`, `False` | same |
| `n_Z`, `n_z`, `state_dim`, `obs_dim`, `hidden_size`, `embedding_dim` | 6, 6, 119, 104, 256, 256 | same |
| `total_timesteps` (replaced by `R = 20`) | 320,000 | 320,000 |
| seeds / lane seeds | 1, 2, 3 / `S … S+31` | same |
| evaluation lanes / seeds / schedule | 8 / 10,000…10,007 / after rollouts 5, 10, 15, 20 | same |
| `torch.set_num_threads` | 4 | 4 |

Command form (the six evidence-bearing runs differ only in `--arm`, `--seed` and `--run-name`):

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e1.py \
  --arm {d0,d1} --seed {1,2,3} --rollouts 20 --num-envs 32 --threads 4 \
  --launch-commit 6fba1c7ba \
  --output-root C:/Projects/HMASD/temp/directions/flexible_skill_duration/exp/E1_20260902
```

The seed-1 pair additionally carried `--run-name {d0,d1}_seed1_r2` (§8 deviation D1). Each pair was
launched as two detached processes (PowerShell `Start-Process -WindowStyle Hidden`), never more than
two at a time.

## 3. The frozen probe set

| Field | Value |
| --- | --- |
| Path (read-only; nothing was added to it) | `C:/Projects/HMASD/temp/directions/flexible_skill_duration/probes/E0_probe_set_seed1.npz` |
| Expected `content_sha256` (contract §3) | `1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c` |
| Measured before every one of the six runs | **identical**, recorded in each run's `manifest.json` → `e1.probe_set.content_sha256` |
| Digest recipe (E0's `_sha256_arrays`, reproduced not re-implemented) | sha256 over the named arrays sorted by key, each contributing `key ‖ str(dtype) ‖ str(shape) ‖ tobytes()`; container-independent, because `np.savez` stamps its zip entries with the wall clock |
| Arrays | `states (1536,119) float64`, `observations (1536,6,104) float32`, `team_skills (1536,) int64`, `agent_skills (1536,6) int64`, `env_step (1536,) int64`, `rollout_index (1536,) int64`, `lane (1536,) int64` |
| `env_step mod 10` | takes every value 0…9; bucket counts 446 / 630 / 460 |
| Provenance | E0 `off` arm, seed 1, rollouts 1, 5, 10, **at 16 lanes** (E0 deviation D1). E1 runs at 32 lanes; the probe set is frozen input and does not depend on E1's lane count, but it was not collected under E1's configuration. Recorded in §9 |

---

## 4. Budget, timing basis and stop rule (contract §4)

**Estimate written before launch, from the P3 timing.** The reviewer's intake
(`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` §X.1 item 6, §X.3) measured, after the
throughput refactor, 206 s per rollout at 4 threads and 32 lanes for one process — "about 70 minutes
per run at `R = 20`, inside the contract's 90-minute condition for 32 lanes" — and decided
`num_envs = 32` with "two runs concurrent as matched seed pairs, 8-hour study cap".

**Measured.** Two concurrent 4-thread processes on 16 logical cores do **not** run at the
single-process rate. Per-rollout means, including the update:

| Pair | D0 s per rollout | D1 s per rollout | D0 wall | D1 wall |
| --- | --- | --- | --- | --- |
| seed 1 (`_r2`) | 395.3 | 403.7 | 8,048.4 s = 134.1 min | 8,198.2 s = 136.6 min |
| seed 2 | 389.6 | 393.2 | 7,905.6 s = 131.8 min | 7,959.0 s = 132.7 min |
| seed 3 | 299.9 | 303.3 | 6,084.0 s = 101.4 min | 6,138.1 s = 102.3 min |

The seed-1 and seed-2 pairs ran at about 1.9× the single-process per-rollout cost, i.e. the machine
was saturated and concurrency bought no throughput; the seed-3 pair, launched on an idle machine
after a pause, ran at about 1.5×. **The 90-minute-per-run condition of contract §2 was therefore
not met by any run** (101–137 minutes). This is recorded as deviation D3: the condition was
evaluated by the reviewer against a single-process measurement and the decision to run pairs
concurrently was taken separately; no run was stopped for it.

**Study wall.** Two readings, both given because they differ:

| Reading | Value |
| --- | --- |
| Machine-occupied time (the quarantined attempt, plus the elapsed time of each pair, pairs being concurrent within themselves) | ~65 min + 8,198 s + 7,959 s + 6,138 s = **7.28 h** — inside the 8-hour cap |
| Elapsed clock, first launch 2026-09-02T21:46:07Z to last completion 2026-09-03T11:08:34Z | **13.37 h**, of which about 6.05 h (03:23Z → 09:26Z) the machine was idle across a harness interruption between the seed-2 and seed-3 pairs |

The projection made after pair 1 (about 2.2 h per pair, three pairs) fitted the cap on the
machine-occupied reading, so no pair was dropped. The elapsed-clock overrun is recorded as
deviation D8; it is idle time, not compute.

**Resource preflight** ran inside the runner as its first action before every one of the eight
launches (six evidence-bearing, two quarantined), before any RNG master, model, optimizer, buffer
or result existed. All eight passed (`MINIMUM_AVAILABLE_MEMORY_BYTES = 4 GiB`,
`measurement_source: GlobalMemoryStatusEx`, `physical_floor_pass` and `effective_floor_pass` both
true). Per-run receipts are in §5.

**Stop rule.** Every one of the six evidence-bearing runs reached `R = 20` with no non-finite loss
or return at any rollout, so the stop rule fired at `R` in all six. Nothing among the six was
quarantined. The two runs that *were* quarantined are the seed-1 first attempt (deviation D1);
they carry a `QUARANTINED` marker, yield no observation, and were neither resumed nor salvaged.

---

## 5. The six runs

Counters identical in all six runs: **20 of 20 rollouts**, **320,000 environment transitions**,
**640 completed episodes** (32 lanes × 20 rollouts; `episode_length == rollout_length`, so every
lane completes exactly one episode per rollout), **`M = 1600` in every rollout** (the contract's
own arithmetic `32 × 500 / 10`, which E0 could only confirm in its two-rollout timing runs), and
**4 evaluations** (after rollouts 5, 10, 15, 20) of 8 deterministic episodes each.

Optimizer steps per network, cumulative over the run — identical in all six runs:

| Network | steps per rollout | total over `R = 20` |
| --- | --- | --- |
| coordinator | 195 | **3,900** |
| discoverer actor | 4,500 | **90,000** |
| discoverer critic | 4,500 | **90,000** |
| team discriminator | 15 | **300** |
| individual discriminator | 60 | **1,200** |

Every network's exposure line is strictly increasing in the rollout index in all six runs.

### D0 seed 1 (`d0_seed1_r2`)

| Fact | Value |
| --- | --- |
| completed / rollouts | `True` / 20 of 20 |
| transitions / episodes | 320,000 / 640 |
| `M` every rollout | 1600 (all 20 rollouts: constant) |
| optimizer steps (coordinator / disc-actor / disc-critic / team-D / ind-D) | 3,900 / 90,000 / 90,000 / 300 / 1,200 |
| evaluations | 4 |
| wall / mean s per rollout | 8048.4 s (134.1 min) / 395.3 s |
| started / ended (UTC) | 2026-09-02T22:52:58+00:00 / 2026-09-03T01:07:07+00:00 |
| preflight `assessed_at` / available physical = effective / `passed` | 2026-09-02T22:52:58.735662Z / 18,281,533,440 B (17.03 GiB) / `True` |
| manifest `code_sha` / `launch_commit` | `eb5318ec115d` / `6fba1c7ba` |
| quarantined | `False` |

Exposure line and counters per rollout (`||theta - theta_0|| / ||theta_0||`, float64):

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16000 | 32 | 1600 | 195 | 20.8925 | 0.3995 | 3.216142e-02 | 2.062404e-01 | 1.067296e-01 | 1.216308e-02 | 2.120684e-02 | 42.3 | 251.3 |
| 2 | 32000 | 64 | 1600 | 390 | 20.1307 | 0.3850 | 3.842578e-02 | 3.192963e-01 | 1.483094e-01 | 1.809131e-02 | 2.961543e-02 | 40.2 | 243.1 |
| 3 | 48000 | 96 | 1600 | 585 | 23.9860 | 0.4587 | 4.429452e-02 | 4.066767e-01 | 1.799605e-01 | 2.308664e-02 | 3.607994e-02 | 43.4 | 240.8 |
| 4 | 64000 | 128 | 1600 | 780 | 27.9626 | 0.5347 | 4.902200e-02 | 4.825473e-01 | 2.087414e-01 | 2.734782e-02 | 4.193151e-02 | 40.9 | 240.2 |
| 5 | 80000 | 160 | 1600 | 975 | 25.8326 | 0.4940 | 5.370053e-02 | 5.391622e-01 | 2.322615e-01 | 3.089603e-02 | 4.748890e-02 | 42.8 | 233.5 |
| 6 | 96000 | 192 | 1600 | 1170 | 31.5213 | 0.6027 | 5.738745e-02 | 5.934933e-01 | 2.551101e-01 | 3.385505e-02 | 5.169682e-02 | 42.8 | 235.5 |
| 7 | 112000 | 224 | 1600 | 1365 | 34.7310 | 0.6642 | 6.092552e-02 | 6.419269e-01 | 2.752275e-01 | 3.627571e-02 | 5.608704e-02 | 40.5 | 235.1 |
| 8 | 128000 | 256 | 1600 | 1560 | 34.4041 | 0.6579 | 6.507129e-02 | 6.823836e-01 | 2.949191e-01 | 3.859050e-02 | 5.954177e-02 | 44.7 | 294.4 |
| 9 | 144000 | 288 | 1600 | 1755 | 33.5615 | 0.6418 | 6.992591e-02 | 7.250675e-01 | 3.131023e-01 | 4.075491e-02 | 6.330379e-02 | 57.3 | 366.2 |
| 10 | 160000 | 320 | 1600 | 1950 | 33.3323 | 0.6374 | 7.491378e-02 | 7.660887e-01 | 3.313614e-01 | 4.285029e-02 | 6.707532e-02 | 81.4 | 379.1 |
| 11 | 176000 | 352 | 1600 | 2145 | 34.0322 | 0.6508 | 7.977061e-02 | 8.024686e-01 | 3.478785e-01 | 4.453116e-02 | 6.977938e-02 | 74.5 | 406.1 |
| 12 | 192000 | 384 | 1600 | 2340 | 36.3341 | 0.6948 | 8.363886e-02 | 8.358720e-01 | 3.640012e-01 | 4.630665e-02 | 7.251056e-02 | 81.3 | 387.4 |
| 13 | 208000 | 416 | 1600 | 2535 | 31.6086 | 0.6045 | 8.853997e-02 | 8.681892e-01 | 3.797815e-01 | 4.800451e-02 | 7.492330e-02 | 78.2 | 399.6 |
| 14 | 224000 | 448 | 1600 | 2730 | 35.3201 | 0.6754 | 9.327840e-02 | 8.974216e-01 | 3.952213e-01 | 4.953026e-02 | 7.716167e-02 | 77.4 | 400.2 |
| 15 | 240000 | 480 | 1600 | 2925 | 33.1806 | 0.6345 | 9.875076e-02 | 9.281926e-01 | 4.091812e-01 | 5.113581e-02 | 7.962435e-02 | 81.0 | 391.2 |
| 16 | 256000 | 512 | 1600 | 3120 | 33.4609 | 0.6399 | 1.039589e-01 | 9.568528e-01 | 4.240618e-01 | 5.275332e-02 | 8.193205e-02 | 80.9 | 391.4 |
| 17 | 272000 | 544 | 1600 | 3315 | 31.0642 | 0.5941 | 1.095120e-01 | 9.845291e-01 | 4.390709e-01 | 5.442025e-02 | 8.399056e-02 | 77.6 | 383.4 |
| 18 | 288000 | 576 | 1600 | 3510 | 31.7109 | 0.6064 | 1.141716e-01 | 1.010606e+00 | 4.554822e-01 | 5.594726e-02 | 8.578047e-02 | 76.6 | 331.1 |
| 19 | 304000 | 608 | 1600 | 3705 | 30.8810 | 0.5905 | 1.185494e-01 | 1.037585e+00 | 4.685698e-01 | 5.725925e-02 | 8.743414e-02 | 74.9 | 385.7 |
| 20 | 320000 | 640 | 1600 | 3900 | 30.8640 | 0.5902 | 1.241785e-01 | 1.061802e+00 | 4.824408e-01 | 5.835391e-02 | 8.886922e-02 | 141.9 | 390.9 |

Evaluations (8 deterministic episodes, lanes seeded `10_000 + rank`):

| after rollout | episodes | return mean | return sd | wall s |
| --- | --- | --- | --- | --- |
| 5 | 8 | 40.8026 | 4.1026 | 17.9 |
| 10 | 8 | 34.1541 | 5.6433 | 29.9 |
| 15 | 8 | 40.9888 | 4.1000 | 31.8 |
| 20 | 8 | 44.8983 | 4.1635 | 50.2 |

Contract section 3 probe measurements (1,536 frozen probes, after every rollout's update):

| r | team acc all | 0-2 | 3-6 | 7-9 | ind acc all | 0-2 | 3-6 | 7-9 | team agree | ind agree | team d\|V\| | agent d\|V\| | age share team | age share ind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.210938 | 0.228700 | 0.198413 | 0.210870 | 0.193902 | 0.191330 | 0.190212 | 0.201449 | - | - | - | - | - | - |
| 2 | 0.194661 | 0.217489 | 0.196825 | 0.169565 | 0.192057 | 0.198430 | 0.181746 | 0.200000 | 0.757812 | 0.446289 | 0.595776 | 0.594881 | - | - |
| 3 | 0.192057 | 0.213004 | 0.188889 | 0.176087 | 0.181966 | 0.184604 | 0.183333 | 0.177536 | 0.813151 | 0.380859 | 0.799116 | 0.792649 | - | - |
| 4 | 0.184896 | 0.192825 | 0.179365 | 0.184783 | 0.179470 | 0.170404 | 0.178571 | 0.189493 | 0.809245 | 0.364909 | 0.706281 | 0.704716 | - | - |
| 5 | 0.202474 | 0.235426 | 0.206349 | 0.165217 | 0.161784 | 0.161061 | 0.160582 | 0.164130 | 0.617188 | 0.276476 | 0.427668 | 0.462858 | - | - |
| 6 | 0.168620 | 0.174888 | 0.185714 | 0.139130 | 0.170790 | 0.175262 | 0.174868 | 0.160870 | 0.637370 | 0.279839 | 0.671731 | 0.610829 | - | - |
| 7 | 0.156901 | 0.163677 | 0.161905 | 0.143478 | 0.154622 | 0.144245 | 0.167196 | 0.147464 | 0.724609 | 0.322591 | 1.052179 | 0.947625 | - | - |
| 8 | 0.123047 | 0.125561 | 0.123810 | 0.119565 | 0.190647 | 0.184978 | 0.194444 | 0.190942 | 0.546224 | 0.266710 | 0.413355 | 0.354379 | - | - |
| 9 | 0.125000 | 0.130045 | 0.128571 | 0.115217 | 0.175781 | 0.166667 | 0.175397 | 0.185145 | 0.752604 | 0.353082 | 0.345705 | 0.355678 | - | - |
| 10 | 0.156901 | 0.150224 | 0.155556 | 0.165217 | 0.171332 | 0.165919 | 0.176720 | 0.169203 | 0.682943 | 0.392687 | 0.400146 | 0.418236 | - | - |
| 11 | 0.155599 | 0.152466 | 0.141270 | 0.178261 | 0.163845 | 0.159940 | 0.161905 | 0.170290 | 0.699870 | 0.371962 | 0.384098 | 0.373074 | - | - |
| 12 | 0.169271 | 0.159193 | 0.163492 | 0.186957 | 0.163194 | 0.166293 | 0.161111 | 0.163043 | 0.804036 | 0.394748 | 0.457713 | 0.465713 | - | - |
| 13 | 0.162109 | 0.152466 | 0.166667 | 0.165217 | 0.173828 | 0.167040 | 0.176455 | 0.176812 | 0.649089 | 0.437717 | 0.514701 | 0.557078 | - | - |
| 14 | 0.173177 | 0.163677 | 0.171429 | 0.184783 | 0.164171 | 0.166293 | 0.168519 | 0.156159 | 0.852214 | 0.486003 | 0.623376 | 0.561130 | - | - |
| 15 | 0.135417 | 0.121076 | 0.141270 | 0.141304 | 0.177409 | 0.176009 | 0.174603 | 0.182609 | 0.733073 | 0.480903 | 0.225248 | 0.256877 | - | - |
| 16 | 0.130859 | 0.116592 | 0.149206 | 0.119565 | 0.164822 | 0.163677 | 0.158995 | 0.173913 | 0.808594 | 0.473741 | 0.432546 | 0.455648 | - | - |
| 17 | 0.129557 | 0.125561 | 0.134921 | 0.126087 | 0.168077 | 0.175262 | 0.153439 | 0.181159 | 0.791667 | 0.369141 | 0.283683 | 0.312132 | - | - |
| 18 | 0.130208 | 0.125561 | 0.146032 | 0.113043 | 0.169488 | 0.170030 | 0.169312 | 0.169203 | 0.686849 | 0.336589 | 0.404365 | 0.392638 | - | - |
| 19 | 0.111979 | 0.105381 | 0.134921 | 0.086957 | 0.170790 | 0.170030 | 0.170106 | 0.172464 | 0.846354 | 0.425890 | 0.336180 | 0.407221 | - | - |
| 20 | 0.134115 | 0.132287 | 0.144444 | 0.121739 | 0.165690 | 0.172646 | 0.158201 | 0.169203 | 0.817057 | 0.483290 | 0.370567 | 0.466264 | - | - |

Window `r >= R/2` = rollouts 10-20 (11 checkpoints):

| Quantity | Value |
| --- | --- |
| team label agreement, mean over window | 0.761068 |
| individual label agreement, mean over window | 0.422970 |
| team accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.144472 / 0.136771 / 0.149928 / 0.144466 |
| individual accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.168423 / 0.168467 / 0.166306 / 0.171278 |
| team value mean abs change: mean / variance over window | 0.402966 / 1.060234e-02 |
| agent value mean abs change: mean / variance over window | 0.424183 / 7.761662e-03 |
| per-probe variance of the value across window rollouts, mean over probes: team / agent | 0.195903 / 0.220975 |

Verbatim final stdout lines:

```
{"arm": "d0", "seed": 1, "completed": true, "rollouts_completed": 20, "transitions_total": 320000, "episodes_total": 640, "optimizer_steps_total": {"coordinator": 3900, "discoverer_actor": 90000, "discoverer_critic": 90000, "team_discriminator": 300, "individual_discriminator": 1200}, "evaluation_count": 4, "final_evaluation_return_mean": 44.898269407251206, "exposure_line_rollout_last": {"coordinator": 0.12417847339672582, "discoverer_actor": 1.0618018063880967, "discoverer_critic": 0.48244077661167745, "team_discriminator": 0.05835390926222884, "individual_discriminator": 0.08886922418984429}, "wall_seconds_total": 8048.350597199998, "seconds_per_rollout_mean": 395.3344391600032, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d0_seed1_r2"}
{"e1_arm": "d0", "age_feature": "off", "seed": 1, "rollouts": 20, "num_envs": 32, "e0_status": 0, "probe_measurement_rollouts": 20, "probe_set_content_sha256": "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c", "team_accuracy_final": {"overall": 0.13411458333333334, "overall_n": 1536, "0-2": 0.13228699551569506, "0-2_n": 446, "3-6": 0.14444444444444443, "3-6_n": 630, "7-9": 0.12173913043478261, "7-9_n": 460}, "individual_accuracy_final": {"overall": 0.16569010416666666, "overall_n": 9216, "0-2": 0.1726457399103139, "0-2_n": 2676, "3-6": 0.1582010582010582, "3-6_n": 3780, "7-9": 0.16920289855072465, "7-9_n": 2760}, "team_label_agreement_mean_window": 0.7610677083333333, "individual_label_agreement_mean_window": 0.42296993371212116, "age_weight_share_final": null, "e1_wall_seconds": 8048.532200300004, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d0_seed1_r2"}
```

### D1 seed 1 (`d1_seed1_r2`)

| Fact | Value |
| --- | --- |
| completed / rollouts | `True` / 20 of 20 |
| transitions / episodes | 320,000 / 640 |
| `M` every rollout | 1600 (all 20 rollouts: constant) |
| optimizer steps (coordinator / disc-actor / disc-critic / team-D / ind-D) | 3,900 / 90,000 / 90,000 / 300 / 1,200 |
| evaluations | 4 |
| wall / mean s per rollout | 8198.2 s (136.6 min) / 403.7 s |
| started / ended (UTC) | 2026-09-02T22:52:58+00:00 / 2026-09-03T01:09:37+00:00 |
| preflight `assessed_at` / available physical = effective / `passed` | 2026-09-02T22:52:58.734664Z / 18,281,963,520 B (17.03 GiB) / `True` |
| manifest `code_sha` / `launch_commit` | `eb5318ec115d` / `6fba1c7ba` |
| quarantined | `False` |

Exposure line and counters per rollout (`||theta - theta_0|| / ||theta_0||`, float64):

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16000 | 32 | 1600 | 195 | 19.5414 | 0.3737 | 3.683406e-02 | 2.028329e-01 | 1.061253e-01 | 1.123535e-02 | 2.111536e-02 | 41.5 | 251.0 |
| 2 | 32000 | 64 | 1600 | 390 | 19.0622 | 0.3646 | 5.152848e-02 | 3.077643e-01 | 1.468272e-01 | 1.722533e-02 | 2.952808e-02 | 42.5 | 252.7 |
| 3 | 48000 | 96 | 1600 | 585 | 21.3318 | 0.4079 | 5.900034e-02 | 3.863399e-01 | 1.781603e-01 | 2.212113e-02 | 3.563007e-02 | 42.6 | 244.7 |
| 4 | 64000 | 128 | 1600 | 780 | 15.4816 | 0.2961 | 6.379363e-02 | 4.530056e-01 | 2.046114e-01 | 2.590186e-02 | 4.012566e-02 | 39.6 | 247.6 |
| 5 | 80000 | 160 | 1600 | 975 | 25.5992 | 0.4895 | 6.762836e-02 | 5.102847e-01 | 2.293122e-01 | 2.959674e-02 | 4.527805e-02 | 42.4 | 246.7 |
| 6 | 96000 | 192 | 1600 | 1170 | 13.2225 | 0.2529 | 7.319569e-02 | 5.613838e-01 | 2.520682e-01 | 3.272712e-02 | 4.991114e-02 | 45.2 | 238.8 |
| 7 | 112000 | 224 | 1600 | 1365 | 8.6681 | 0.1658 | 8.234351e-02 | 6.098108e-01 | 2.736292e-01 | 3.547515e-02 | 5.319718e-02 | 35.9 | 242.1 |
| 8 | 128000 | 256 | 1600 | 1560 | 21.3199 | 0.4077 | 8.735952e-02 | 6.465065e-01 | 2.916800e-01 | 3.787521e-02 | 5.656491e-02 | 40.1 | 306.8 |
| 9 | 144000 | 288 | 1600 | 1755 | 25.5480 | 0.4886 | 9.067025e-02 | 6.854364e-01 | 3.094399e-01 | 4.022250e-02 | 5.996218e-02 | 54.3 | 387.3 |
| 10 | 160000 | 320 | 1600 | 1950 | 11.3033 | 0.2162 | 9.668469e-02 | 7.182744e-01 | 3.286420e-01 | 4.246052e-02 | 6.273212e-02 | 75.4 | 373.5 |
| 11 | 176000 | 352 | 1600 | 2145 | 28.4947 | 0.5449 | 1.011498e-01 | 7.552038e-01 | 3.457529e-01 | 4.462787e-02 | 6.509776e-02 | 73.4 | 406.3 |
| 12 | 192000 | 384 | 1600 | 2340 | 18.6679 | 0.3571 | 1.063168e-01 | 7.920589e-01 | 3.628266e-01 | 4.668441e-02 | 6.754007e-02 | 74.9 | 397.9 |
| 13 | 208000 | 416 | 1600 | 2535 | 24.9263 | 0.4767 | 1.104976e-01 | 8.276619e-01 | 3.784287e-01 | 4.853841e-02 | 6.974023e-02 | 77.5 | 401.7 |
| 14 | 224000 | 448 | 1600 | 2730 | 25.2698 | 0.4833 | 1.144061e-01 | 8.644399e-01 | 3.914675e-01 | 5.030702e-02 | 7.240663e-02 | 76.1 | 406.3 |
| 15 | 240000 | 480 | 1600 | 2925 | 26.4810 | 0.5064 | 1.180419e-01 | 9.007550e-01 | 4.057833e-01 | 5.197653e-02 | 7.508841e-02 | 76.4 | 393.4 |
| 16 | 256000 | 512 | 1600 | 3120 | 25.2723 | 0.4833 | 1.220622e-01 | 9.359565e-01 | 4.194710e-01 | 5.358055e-02 | 7.818524e-02 | 79.5 | 396.3 |
| 17 | 272000 | 544 | 1600 | 3315 | 25.2167 | 0.4823 | 1.264460e-01 | 9.685263e-01 | 4.322431e-01 | 5.499987e-02 | 8.095598e-02 | 75.3 | 386.3 |
| 18 | 288000 | 576 | 1600 | 3510 | 26.2982 | 0.5029 | 1.306976e-01 | 1.000615e+00 | 4.443878e-01 | 5.653632e-02 | 8.312834e-02 | 67.4 | 338.6 |
| 19 | 304000 | 608 | 1600 | 3705 | 28.4781 | 0.5446 | 1.342852e-01 | 1.031427e+00 | 4.566954e-01 | 5.803819e-02 | 8.547758e-02 | 86.0 | 471.1 |
| 20 | 320000 | 640 | 1600 | 3900 | 29.0401 | 0.5554 | 1.380081e-01 | 1.059333e+00 | 4.677657e-01 | 5.941578e-02 | 8.772487e-02 | 78.7 | 460.3 |

Evaluations (8 deterministic episodes, lanes seeded `10_000 + rank`):

| after rollout | episodes | return mean | return sd | wall s |
| --- | --- | --- | --- | --- |
| 5 | 8 | 18.0177 | 5.0483 | 15.0 |
| 10 | 8 | 29.7017 | 6.1598 | 25.5 |
| 15 | 8 | 25.6679 | 6.1668 | 28.6 |
| 20 | 8 | 23.8099 | 3.5504 | 42.8 |

Contract section 3 probe measurements (1,536 frozen probes, after every rollout's update):

| r | team acc all | 0-2 | 3-6 | 7-9 | ind acc all | 0-2 | 3-6 | 7-9 | team agree | ind agree | team d\|V\| | agent d\|V\| | age share team | age share ind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.218099 | 0.217489 | 0.211111 | 0.228261 | 0.193468 | 0.192825 | 0.187037 | 0.202899 | - | - | - | - | 0.091254 | 0.097355 |
| 2 | 0.199219 | 0.201794 | 0.196825 | 0.200000 | 0.195312 | 0.193946 | 0.194974 | 0.197101 | 0.716146 | 0.570204 | 0.846055 | 0.822559 | 0.091269 | 0.097008 |
| 3 | 0.197917 | 0.186099 | 0.206349 | 0.197826 | 0.185981 | 0.184978 | 0.188095 | 0.184058 | 0.798177 | 0.436957 | 0.763738 | 0.745491 | 0.091346 | 0.096701 |
| 4 | 0.198568 | 0.190583 | 0.206349 | 0.195652 | 0.179470 | 0.186472 | 0.174074 | 0.180072 | 0.792318 | 0.298720 | 0.551504 | 0.575906 | 0.091449 | 0.096525 |
| 5 | 0.212240 | 0.230942 | 0.204762 | 0.204348 | 0.190213 | 0.182735 | 0.191534 | 0.195652 | 0.583333 | 0.313260 | 0.814148 | 0.861487 | 0.091584 | 0.096290 |
| 6 | 0.216146 | 0.228700 | 0.207937 | 0.215217 | 0.186849 | 0.181614 | 0.188095 | 0.190217 | 0.702474 | 0.374349 | 1.085730 | 1.132875 | 0.091691 | 0.095939 |
| 7 | 0.208984 | 0.221973 | 0.201587 | 0.206522 | 0.174588 | 0.177504 | 0.170899 | 0.176812 | 0.804688 | 0.410265 | 0.694779 | 0.737287 | 0.091679 | 0.095761 |
| 8 | 0.207682 | 0.213004 | 0.201587 | 0.210870 | 0.170030 | 0.162182 | 0.169577 | 0.178261 | 0.746094 | 0.213650 | 1.666790 | 1.720210 | 0.091657 | 0.095533 |
| 9 | 0.206380 | 0.219731 | 0.198413 | 0.204348 | 0.178168 | 0.164051 | 0.182011 | 0.186594 | 0.851562 | 0.385525 | 0.606735 | 0.599361 | 0.091737 | 0.095387 |
| 10 | 0.230469 | 0.235426 | 0.230159 | 0.226087 | 0.175998 | 0.166293 | 0.176984 | 0.184058 | 0.707031 | 0.391276 | 1.064614 | 1.048306 | 0.091773 | 0.095352 |
| 11 | 0.201823 | 0.190583 | 0.212698 | 0.197826 | 0.163954 | 0.162556 | 0.162698 | 0.167029 | 0.676432 | 0.321832 | 1.107239 | 1.147615 | 0.091784 | 0.095096 |
| 12 | 0.222005 | 0.226457 | 0.231746 | 0.204348 | 0.171007 | 0.157698 | 0.179365 | 0.172464 | 0.721354 | 0.417860 | 0.670462 | 0.658271 | 0.091800 | 0.095041 |
| 13 | 0.231120 | 0.233184 | 0.242857 | 0.213043 | 0.178819 | 0.178625 | 0.178836 | 0.178986 | 0.798177 | 0.327365 | 0.884223 | 0.855211 | 0.091806 | 0.094796 |
| 14 | 0.241536 | 0.242152 | 0.246032 | 0.234783 | 0.185221 | 0.177877 | 0.188095 | 0.188406 | 0.757812 | 0.429688 | 0.336720 | 0.374567 | 0.091814 | 0.094889 |
| 15 | 0.237630 | 0.251121 | 0.236508 | 0.226087 | 0.174479 | 0.163677 | 0.176455 | 0.182246 | 0.832682 | 0.429905 | 0.534488 | 0.503221 | 0.091759 | 0.094791 |
| 16 | 0.231120 | 0.242152 | 0.236508 | 0.213043 | 0.170898 | 0.165546 | 0.175132 | 0.170290 | 0.858724 | 0.367839 | 0.350858 | 0.351186 | 0.091752 | 0.094661 |
| 17 | 0.224609 | 0.228700 | 0.225397 | 0.219565 | 0.164388 | 0.159940 | 0.163492 | 0.169928 | 0.736979 | 0.351888 | 0.310795 | 0.291397 | 0.091735 | 0.094449 |
| 18 | 0.232422 | 0.237668 | 0.246032 | 0.208696 | 0.164062 | 0.162930 | 0.160847 | 0.169565 | 0.751302 | 0.405273 | 0.337909 | 0.359878 | 0.091706 | 0.094311 |
| 19 | 0.227865 | 0.242152 | 0.234921 | 0.204348 | 0.176324 | 0.176383 | 0.167196 | 0.188768 | 0.694010 | 0.306207 | 0.377738 | 0.400228 | 0.091738 | 0.094253 |
| 20 | 0.218750 | 0.244395 | 0.220635 | 0.191304 | 0.178060 | 0.168909 | 0.178571 | 0.186232 | 0.859375 | 0.494141 | 0.341328 | 0.332802 | 0.091853 | 0.093972 |

Window `r >= R/2` = rollouts 10-20 (11 checkpoints):

| Quantity | Value |
| --- | --- |
| team label agreement, mean over window | 0.763080 |
| individual label agreement, mean over window | 0.385752 |
| team accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.227214 / 0.233999 / 0.233045 / 0.212648 |
| individual accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.173019 / 0.167312 / 0.173425 / 0.177997 |
| team value mean abs change: mean / variance over window | 0.574216 / 8.690132e-02 |
| agent value mean abs change: mean / variance over window | 0.574789 / 8.624461e-02 |
| per-probe variance of the value across window rollouts, mean over probes: team / agent | 0.363445 / 0.377728 |
| age-feature weight share, team: rollout 1 -> rollout 20 | 0.091254 -> 0.091853 |
| age-feature weight share, individual: rollout 1 -> rollout 20 | 0.097355 -> 0.093972 |

Verbatim final stdout lines:

```
{"arm": "d1", "seed": 1, "completed": true, "rollouts_completed": 20, "transitions_total": 320000, "episodes_total": 640, "optimizer_steps_total": {"coordinator": 3900, "discoverer_actor": 90000, "discoverer_critic": 90000, "team_discriminator": 300, "individual_discriminator": 1200}, "evaluation_count": 4, "final_evaluation_return_mean": 23.809878610980192, "exposure_line_rollout_last": {"coordinator": 0.13800811285741582, "discoverer_actor": 1.059332987310602, "discoverer_critic": 0.46776566552678334, "team_discriminator": 0.05941577556624767, "individual_discriminator": 0.08772487480484793}, "wall_seconds_total": 8198.191876199999, "seconds_per_rollout_mean": 403.72143260000087, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d1_seed1_r2"}
{"e1_arm": "d1", "age_feature": "normalized", "seed": 1, "rollouts": 20, "num_envs": 32, "e0_status": 0, "probe_measurement_rollouts": 20, "probe_set_content_sha256": "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c", "team_accuracy_final": {"overall": 0.21875, "overall_n": 1536, "0-2": 0.24439461883408073, "0-2_n": 446, "3-6": 0.22063492063492063, "3-6_n": 630, "7-9": 0.19130434782608696, "7-9_n": 460}, "individual_accuracy_final": {"overall": 0.17805989583333334, "overall_n": 9216, "0-2": 0.16890881913303438, "0-2_n": 2676, "3-6": 0.17857142857142858, "3-6_n": 3780, "7-9": 0.186231884057971, "7-9_n": 2760}, "team_label_agreement_mean_window": 0.7630800189393938, "individual_label_agreement_mean_window": 0.3857520517676768, "age_weight_share_final": {"team": {"age_column_norm": 1.0071063347118894, "input_projection_norm": 10.964279922202351, "age_share": 0.09185339501160747}, "individual": {"age_column_norm": 0.9622277641936315, "input_projection_norm": 10.239469492381154, "age_share": 0.0939724235625286}}, "e1_wall_seconds": 8198.366201399986, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d1_seed1_r2"}
```

### D0 seed 2 (`d0_seed2`)

| Fact | Value |
| --- | --- |
| completed / rollouts | `True` / 20 of 20 |
| transitions / episodes | 320,000 / 640 |
| `M` every rollout | 1600 (all 20 rollouts: constant) |
| optimizer steps (coordinator / disc-actor / disc-critic / team-D / ind-D) | 3,900 / 90,000 / 90,000 / 300 / 1,200 |
| evaluations | 4 |
| wall / mean s per rollout | 7905.6 s (131.8 min) / 389.6 s |
| started / ended (UTC) | 2026-09-03T01:10:26+00:00 / 2026-09-03T03:22:11+00:00 |
| preflight `assessed_at` / available physical = effective / `passed` | 2026-09-03T01:10:26.392350Z / 14,672,064,512 B (13.66 GiB) / `True` |
| manifest `code_sha` / `launch_commit` | `b9290a1ed9ea` / `6fba1c7ba` |
| quarantined | `False` |

Exposure line and counters per rollout (`||theta - theta_0|| / ||theta_0||`, float64):

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16000 | 32 | 1600 | 195 | 20.5310 | 0.3927 | 3.114644e-02 | 2.039308e-01 | 1.102427e-01 | 1.178201e-02 | 2.184070e-02 | 95.8 | 276.9 |
| 2 | 32000 | 64 | 1600 | 390 | 20.6089 | 0.3941 | 3.860790e-02 | 3.109359e-01 | 1.537565e-01 | 1.750888e-02 | 3.039480e-02 | 43.7 | 247.7 |
| 3 | 48000 | 96 | 1600 | 585 | 24.7716 | 0.4737 | 4.378693e-02 | 3.964616e-01 | 1.859807e-01 | 2.231077e-02 | 3.715761e-02 | 45.5 | 234.4 |
| 4 | 64000 | 128 | 1600 | 780 | 21.0531 | 0.4026 | 4.908519e-02 | 4.645599e-01 | 2.144596e-01 | 2.627679e-02 | 4.343861e-02 | 41.8 | 244.0 |
| 5 | 80000 | 160 | 1600 | 975 | 14.7397 | 0.2819 | 5.560381e-02 | 5.230783e-01 | 2.412361e-01 | 2.951347e-02 | 4.776315e-02 | 52.1 | 274.9 |
| 6 | 96000 | 192 | 1600 | 1170 | 13.4898 | 0.2580 | 6.425788e-02 | 5.722700e-01 | 2.656951e-01 | 3.249494e-02 | 5.147047e-02 | 45.6 | 267.4 |
| 7 | 112000 | 224 | 1600 | 1365 | 20.3222 | 0.3886 | 7.164804e-02 | 6.223104e-01 | 2.867922e-01 | 3.513486e-02 | 5.557147e-02 | 66.3 | 377.2 |
| 8 | 128000 | 256 | 1600 | 1560 | 26.5015 | 0.5068 | 7.539047e-02 | 6.681216e-01 | 3.044998e-01 | 3.757146e-02 | 5.952932e-02 | 48.1 | 323.7 |
| 9 | 144000 | 288 | 1600 | 1755 | 28.3959 | 0.5430 | 7.942056e-02 | 7.114166e-01 | 3.221351e-01 | 3.976987e-02 | 6.330097e-02 | 84.6 | 410.4 |
| 10 | 160000 | 320 | 1600 | 1950 | 27.7200 | 0.5301 | 8.336767e-02 | 7.545304e-01 | 3.388143e-01 | 4.200444e-02 | 6.629272e-02 | 85.0 | 416.5 |
| 11 | 176000 | 352 | 1600 | 2145 | 29.8675 | 0.5711 | 8.782261e-02 | 7.946011e-01 | 3.549898e-01 | 4.408481e-02 | 6.985440e-02 | 87.1 | 416.2 |
| 12 | 192000 | 384 | 1600 | 2340 | 27.4953 | 0.5258 | 9.256204e-02 | 8.308939e-01 | 3.706024e-01 | 4.596215e-02 | 7.335824e-02 | 84.1 | 399.3 |
| 13 | 208000 | 416 | 1600 | 2535 | 28.2713 | 0.5406 | 9.684705e-02 | 8.659971e-01 | 3.864209e-01 | 4.766903e-02 | 7.618334e-02 | 59.0 | 400.3 |
| 14 | 224000 | 448 | 1600 | 2730 | 26.3309 | 0.5035 | 1.025452e-01 | 8.984508e-01 | 4.022674e-01 | 4.931727e-02 | 7.898852e-02 | 79.6 | 385.8 |
| 15 | 240000 | 480 | 1600 | 2925 | 23.4998 | 0.4494 | 1.081309e-01 | 9.315655e-01 | 4.184327e-01 | 5.071513e-02 | 8.162888e-02 | 76.2 | 384.8 |
| 16 | 256000 | 512 | 1600 | 3120 | 25.3990 | 0.4857 | 1.135860e-01 | 9.624929e-01 | 4.339697e-01 | 5.207453e-02 | 8.425183e-02 | 79.0 | 391.4 |
| 17 | 272000 | 544 | 1600 | 3315 | 25.8028 | 0.4934 | 1.188631e-01 | 9.914494e-01 | 4.478992e-01 | 5.330299e-02 | 8.615205e-02 | 81.0 | 388.1 |
| 18 | 288000 | 576 | 1600 | 3510 | 24.3648 | 0.4659 | 1.241860e-01 | 1.020222e+00 | 4.629958e-01 | 5.451156e-02 | 8.820293e-02 | 51.0 | 222.0 |
| 19 | 304000 | 608 | 1600 | 3705 | 23.6691 | 0.4526 | 1.295668e-01 | 1.047059e+00 | 4.760684e-01 | 5.576627e-02 | 9.088999e-02 | 42.0 | 221.4 |
| 20 | 320000 | 640 | 1600 | 3900 | 26.0863 | 0.4988 | 1.343304e-01 | 1.071549e+00 | 4.907643e-01 | 5.713520e-02 | 9.304069e-02 | 40.2 | 222.3 |

Evaluations (8 deterministic episodes, lanes seeded `10_000 + rank`):

| after rollout | episodes | return mean | return sd | wall s |
| --- | --- | --- | --- | --- |
| 5 | 8 | 17.4068 | 7.5328 | 18.8 |
| 10 | 8 | 21.5013 | 4.1332 | 38.3 |
| 15 | 8 | 27.4961 | 3.4334 | 27.7 |
| 20 | 8 | 29.3664 | 6.5584 | 14.9 |

Contract section 3 probe measurements (1,536 frozen probes, after every rollout's update):

| r | team acc all | 0-2 | 3-6 | 7-9 | ind acc all | 0-2 | 3-6 | 7-9 | team agree | ind agree | team d\|V\| | agent d\|V\| | age share team | age share ind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.215495 | 0.239910 | 0.204762 | 0.206522 | 0.185221 | 0.181988 | 0.182540 | 0.192029 | - | - | - | - | - | - |
| 2 | 0.218099 | 0.237668 | 0.198413 | 0.226087 | 0.187283 | 0.186099 | 0.185185 | 0.191304 | 0.757812 | 0.816623 | 0.858239 | 0.858230 | - | - |
| 3 | 0.218099 | 0.226457 | 0.209524 | 0.221739 | 0.180230 | 0.178999 | 0.179894 | 0.181884 | 0.896484 | 0.643121 | 0.715265 | 0.759292 | - | - |
| 4 | 0.214844 | 0.244395 | 0.192063 | 0.217391 | 0.172418 | 0.169656 | 0.175397 | 0.171014 | 0.848307 | 0.470703 | 0.361959 | 0.395739 | - | - |
| 5 | 0.214844 | 0.242152 | 0.192063 | 0.219565 | 0.171332 | 0.171151 | 0.173810 | 0.168116 | 0.723958 | 0.410482 | 0.689058 | 0.679951 | - | - |
| 6 | 0.212240 | 0.221973 | 0.190476 | 0.232609 | 0.156359 | 0.156577 | 0.163757 | 0.146014 | 0.756510 | 0.339301 | 0.513515 | 0.576201 | - | - |
| 7 | 0.213542 | 0.226457 | 0.204762 | 0.213043 | 0.170573 | 0.173767 | 0.165608 | 0.174275 | 0.793620 | 0.347982 | 0.711199 | 0.740242 | - | - |
| 8 | 0.220703 | 0.235426 | 0.214286 | 0.215217 | 0.178168 | 0.166293 | 0.179630 | 0.187681 | 0.812500 | 0.313043 | 0.585726 | 0.548393 | - | - |
| 9 | 0.220703 | 0.246637 | 0.207937 | 0.213043 | 0.172635 | 0.171525 | 0.175397 | 0.169928 | 0.702474 | 0.355035 | 0.424591 | 0.391074 | - | - |
| 10 | 0.227214 | 0.253363 | 0.226984 | 0.202174 | 0.160916 | 0.159193 | 0.157672 | 0.167029 | 0.641927 | 0.370551 | 0.380648 | 0.391230 | - | - |
| 11 | 0.195964 | 0.188341 | 0.201587 | 0.195652 | 0.163845 | 0.167788 | 0.162963 | 0.161232 | 0.687500 | 0.328125 | 0.383356 | 0.328475 | - | - |
| 12 | 0.175130 | 0.188341 | 0.177778 | 0.158696 | 0.164062 | 0.162182 | 0.165608 | 0.163768 | 0.669271 | 0.340712 | 0.358391 | 0.371549 | - | - |
| 13 | 0.184896 | 0.210762 | 0.177778 | 0.169565 | 0.160048 | 0.156203 | 0.164550 | 0.157609 | 0.624349 | 0.338542 | 0.331085 | 0.331080 | - | - |
| 14 | 0.180990 | 0.213004 | 0.184127 | 0.145652 | 0.177192 | 0.173767 | 0.181746 | 0.174275 | 0.692057 | 0.347982 | 0.438544 | 0.427639 | - | - |
| 15 | 0.173177 | 0.199552 | 0.158730 | 0.167391 | 0.185004 | 0.185725 | 0.182275 | 0.188043 | 0.646484 | 0.538520 | 0.461448 | 0.491767 | - | - |
| 16 | 0.190104 | 0.217489 | 0.182540 | 0.173913 | 0.174913 | 0.168161 | 0.180688 | 0.173551 | 0.741536 | 0.561306 | 0.426753 | 0.416099 | - | - |
| 17 | 0.206380 | 0.255605 | 0.180952 | 0.193478 | 0.178168 | 0.178625 | 0.175397 | 0.181522 | 0.689453 | 0.547635 | 0.379802 | 0.391037 | - | - |
| 18 | 0.179036 | 0.215247 | 0.176190 | 0.147826 | 0.181532 | 0.175262 | 0.186508 | 0.180797 | 0.641276 | 0.583550 | 0.317881 | 0.349395 | - | - |
| 19 | 0.161458 | 0.179372 | 0.165079 | 0.139130 | 0.172526 | 0.164798 | 0.174603 | 0.177174 | 0.817708 | 0.467448 | 0.229088 | 0.222717 | - | - |
| 20 | 0.152995 | 0.170404 | 0.165079 | 0.119565 | 0.164605 | 0.158445 | 0.163228 | 0.172464 | 0.684896 | 0.495877 | 0.256623 | 0.255352 | - | - |

Window `r >= R/2` = rollouts 10-20 (11 checkpoints):

| Quantity | Value |
| --- | --- |
| team label agreement, mean over window | 0.685133 |
| individual label agreement, mean over window | 0.447295 |
| team accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.184304 / 0.208316 / 0.181530 / 0.164822 |
| individual accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.171165 / 0.168195 / 0.172294 / 0.172497 |
| team value mean abs change: mean / variance over window | 0.360329 / 4.792451e-03 |
| agent value mean abs change: mean / variance over window | 0.361485 / 5.352096e-03 |
| per-probe variance of the value across window rollouts, mean over probes: team / agent | 0.218131 / 0.198254 |

Verbatim final stdout lines:

```
{"arm": "d0", "seed": 2, "completed": true, "rollouts_completed": 20, "transitions_total": 320000, "episodes_total": 640, "optimizer_steps_total": {"coordinator": 3900, "discoverer_actor": 90000, "discoverer_critic": 90000, "team_discriminator": 300, "individual_discriminator": 1200}, "evaluation_count": 4, "final_evaluation_return_mean": 29.366375736725246, "exposure_line_rollout_last": {"coordinator": 0.13433044469809616, "discoverer_actor": 1.071548563664841, "discoverer_critic": 0.4907643349505565, "team_discriminator": 0.05713519754485089, "individual_discriminator": 0.09304069017899746}, "wall_seconds_total": 7905.5599666999915, "seconds_per_rollout_mean": 389.6266874250017, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d0_seed2"}
{"e1_arm": "d0", "age_feature": "off", "seed": 2, "rollouts": 20, "num_envs": 32, "e0_status": 0, "probe_measurement_rollouts": 20, "probe_set_content_sha256": "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c", "team_accuracy_final": {"overall": 0.15299479166666666, "overall_n": 1536, "0-2": 0.17040358744394618, "0-2_n": 446, "3-6": 0.16507936507936508, "3-6_n": 630, "7-9": 0.11956521739130435, "7-9_n": 460}, "individual_accuracy_final": {"overall": 0.1646050347222222, "overall_n": 9216, "0-2": 0.15844544095665172, "0-2_n": 2676, "3-6": 0.16322751322751322, "3-6_n": 3780, "7-9": 0.17246376811594202, "7-9_n": 2760}, "team_label_agreement_mean_window": 0.6851325757575757, "individual_label_agreement_mean_window": 0.44729521780303033, "age_weight_share_final": null, "e1_wall_seconds": 7905.848381200005, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d0_seed2"}
```

### D1 seed 2 (`d1_seed2`)

| Fact | Value |
| --- | --- |
| completed / rollouts | `True` / 20 of 20 |
| transitions / episodes | 320,000 / 640 |
| `M` every rollout | 1600 (all 20 rollouts: constant) |
| optimizer steps (coordinator / disc-actor / disc-critic / team-D / ind-D) | 3,900 / 90,000 / 90,000 / 300 / 1,200 |
| evaluations | 4 |
| wall / mean s per rollout | 7959.0 s (132.7 min) / 393.2 s |
| started / ended (UTC) | 2026-09-03T01:10:26+00:00 / 2026-09-03T03:23:05+00:00 |
| preflight `assessed_at` / available physical = effective / `passed` | 2026-09-03T01:10:26.413465Z / 14,672,789,504 B (13.67 GiB) / `True` |
| manifest `code_sha` / `launch_commit` | `b9290a1ed9ea` / `6fba1c7ba` |
| quarantined | `False` |

Exposure line and counters per rollout (`||theta - theta_0|| / ||theta_0||`, float64):

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16000 | 32 | 1600 | 195 | 20.0775 | 0.3840 | 3.140600e-02 | 1.988274e-01 | 1.084985e-01 | 1.213524e-02 | 2.066349e-02 | 96.0 | 281.8 |
| 2 | 32000 | 64 | 1600 | 390 | 17.9352 | 0.3430 | 4.008899e-02 | 2.960091e-01 | 1.509700e-01 | 1.785530e-02 | 2.916227e-02 | 44.0 | 258.4 |
| 3 | 48000 | 96 | 1600 | 585 | 24.9294 | 0.4767 | 4.475475e-02 | 3.923254e-01 | 1.853027e-01 | 2.227848e-02 | 3.610107e-02 | 45.2 | 243.7 |
| 4 | 64000 | 128 | 1600 | 780 | 25.0829 | 0.4797 | 5.084645e-02 | 4.613629e-01 | 2.132933e-01 | 2.621211e-02 | 4.172614e-02 | 39.4 | 257.7 |
| 5 | 80000 | 160 | 1600 | 975 | 25.9951 | 0.4971 | 5.654033e-02 | 5.198798e-01 | 2.392261e-01 | 2.978447e-02 | 4.597034e-02 | 55.1 | 277.5 |
| 6 | 96000 | 192 | 1600 | 1170 | 16.8093 | 0.3215 | 6.310533e-02 | 5.733513e-01 | 2.623412e-01 | 3.247905e-02 | 4.972913e-02 | 45.0 | 284.8 |
| 7 | 112000 | 224 | 1600 | 1365 | 26.4150 | 0.5051 | 6.871981e-02 | 6.200979e-01 | 2.835323e-01 | 3.503939e-02 | 5.359483e-02 | 83.2 | 351.9 |
| 8 | 128000 | 256 | 1600 | 1560 | 14.1408 | 0.2705 | 7.694488e-02 | 6.615354e-01 | 3.033226e-01 | 3.777402e-02 | 5.698523e-02 | 44.9 | 358.6 |
| 9 | 144000 | 288 | 1600 | 1755 | 20.7409 | 0.3967 | 8.527676e-02 | 7.053001e-01 | 3.230826e-01 | 4.029110e-02 | 6.023807e-02 | 81.1 | 415.4 |
| 10 | 160000 | 320 | 1600 | 1950 | 13.1125 | 0.2508 | 9.329902e-02 | 7.433890e-01 | 3.411133e-01 | 4.273305e-02 | 6.280983e-02 | 79.9 | 435.3 |
| 11 | 176000 | 352 | 1600 | 2145 | 22.2052 | 0.4246 | 1.000957e-01 | 7.822209e-01 | 3.586794e-01 | 4.501510e-02 | 6.547120e-02 | 79.6 | 421.3 |
| 12 | 192000 | 384 | 1600 | 2340 | 15.0586 | 0.2880 | 1.077099e-01 | 8.172418e-01 | 3.749306e-01 | 4.712222e-02 | 6.793209e-02 | 80.8 | 379.1 |
| 13 | 208000 | 416 | 1600 | 2535 | 15.1662 | 0.2901 | 1.143743e-01 | 8.493676e-01 | 3.905302e-01 | 4.895482e-02 | 7.030103e-02 | 83.9 | 391.6 |
| 14 | 224000 | 448 | 1600 | 2730 | 18.9879 | 0.3631 | 1.198993e-01 | 8.827103e-01 | 4.064351e-01 | 5.044475e-02 | 7.254790e-02 | 77.4 | 386.1 |
| 15 | 240000 | 480 | 1600 | 2925 | 24.5677 | 0.4699 | 1.254136e-01 | 9.181012e-01 | 4.203858e-01 | 5.182860e-02 | 7.488613e-02 | 72.5 | 395.8 |
| 16 | 256000 | 512 | 1600 | 3120 | 26.2509 | 0.5020 | 1.303207e-01 | 9.512470e-01 | 4.329598e-01 | 5.339856e-02 | 7.700394e-02 | 77.9 | 400.6 |
| 17 | 272000 | 544 | 1600 | 3315 | 25.7830 | 0.4930 | 1.345729e-01 | 9.844343e-01 | 4.457866e-01 | 5.512290e-02 | 7.919746e-02 | 81.4 | 359.8 |
| 18 | 288000 | 576 | 1600 | 3510 | 22.2812 | 0.4261 | 1.395614e-01 | 1.012930e+00 | 4.601022e-01 | 5.644064e-02 | 8.114217e-02 | 43.3 | 227.7 |
| 19 | 304000 | 608 | 1600 | 3705 | 20.6817 | 0.3956 | 1.438397e-01 | 1.041080e+00 | 4.728424e-01 | 5.766774e-02 | 8.325451e-02 | 40.9 | 227.1 |
| 20 | 320000 | 640 | 1600 | 3900 | 24.2633 | 0.4640 | 1.474143e-01 | 1.069783e+00 | 4.863399e-01 | 5.884998e-02 | 8.514150e-02 | 41.9 | 216.2 |

Evaluations (8 deterministic episodes, lanes seeded `10_000 + rank`):

| after rollout | episodes | return mean | return sd | wall s |
| --- | --- | --- | --- | --- |
| 5 | 8 | 20.6004 | 5.8085 | 16.2 |
| 10 | 8 | 17.1296 | 7.2860 | 27.6 |
| 15 | 8 | 19.2115 | 6.7690 | 25.8 |
| 20 | 8 | 21.1612 | 5.7653 | 12.0 |

Contract section 3 probe measurements (1,536 frozen probes, after every rollout's update):

| r | team acc all | 0-2 | 3-6 | 7-9 | ind acc all | 0-2 | 3-6 | 7-9 | team agree | ind agree | team d\|V\| | agent d\|V\| | age share team | age share ind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.223958 | 0.217489 | 0.220635 | 0.234783 | 0.181641 | 0.180493 | 0.174074 | 0.193116 | - | - | - | - | 0.091223 | 0.097253 |
| 2 | 0.229167 | 0.239910 | 0.230159 | 0.217391 | 0.177843 | 0.176756 | 0.177778 | 0.178986 | 0.770182 | 0.743381 | 0.475938 | 0.468823 | 0.091251 | 0.096958 |
| 3 | 0.227214 | 0.228700 | 0.223810 | 0.230435 | 0.162326 | 0.154335 | 0.162169 | 0.170290 | 0.865885 | 0.515082 | 1.220159 | 1.182563 | 0.091279 | 0.096760 |
| 4 | 0.225911 | 0.226457 | 0.219048 | 0.234783 | 0.170030 | 0.174514 | 0.168254 | 0.168116 | 0.884766 | 0.241862 | 0.740922 | 0.742539 | 0.091293 | 0.096593 |
| 5 | 0.216797 | 0.224215 | 0.209524 | 0.219565 | 0.168403 | 0.170030 | 0.165344 | 0.171014 | 0.884115 | 0.389106 | 0.726257 | 0.710330 | 0.091228 | 0.096381 |
| 6 | 0.201823 | 0.197309 | 0.185714 | 0.228261 | 0.160482 | 0.165172 | 0.154762 | 0.163768 | 0.361979 | 0.410916 | 1.051543 | 1.062009 | 0.091132 | 0.096126 |
| 7 | 0.189453 | 0.181614 | 0.174603 | 0.217391 | 0.158746 | 0.159567 | 0.160847 | 0.155072 | 0.833333 | 0.377821 | 0.958482 | 0.963923 | 0.091189 | 0.096180 |
| 8 | 0.190104 | 0.188341 | 0.177778 | 0.208696 | 0.168403 | 0.173393 | 0.166667 | 0.165942 | 0.705078 | 0.279188 | 1.468815 | 1.481243 | 0.091196 | 0.096063 |
| 9 | 0.174479 | 0.165919 | 0.165079 | 0.195652 | 0.156141 | 0.158072 | 0.151058 | 0.161232 | 0.841146 | 0.356988 | 0.475945 | 0.510529 | 0.091134 | 0.095985 |
| 10 | 0.187500 | 0.168161 | 0.190476 | 0.202174 | 0.155382 | 0.156951 | 0.150529 | 0.160507 | 0.720703 | 0.387153 | 0.475312 | 0.507965 | 0.091201 | 0.095759 |
| 11 | 0.158854 | 0.145740 | 0.155556 | 0.176087 | 0.163303 | 0.169283 | 0.157672 | 0.165217 | 0.731120 | 0.411892 | 0.696629 | 0.672099 | 0.091184 | 0.095565 |
| 12 | 0.160156 | 0.150224 | 0.163492 | 0.165217 | 0.162977 | 0.159567 | 0.163228 | 0.165942 | 0.687500 | 0.374457 | 0.377264 | 0.356549 | 0.091149 | 0.095505 |
| 13 | 0.162760 | 0.143498 | 0.176190 | 0.163043 | 0.164388 | 0.166293 | 0.161111 | 0.167029 | 0.736328 | 0.370443 | 0.591207 | 0.620454 | 0.091184 | 0.095534 |
| 14 | 0.145833 | 0.143498 | 0.141270 | 0.154348 | 0.162435 | 0.165172 | 0.157143 | 0.167029 | 0.569010 | 0.355143 | 0.538479 | 0.551072 | 0.091160 | 0.095189 |
| 15 | 0.156250 | 0.147982 | 0.163492 | 0.154348 | 0.166450 | 0.169656 | 0.153439 | 0.181159 | 0.576823 | 0.384115 | 0.639480 | 0.662957 | 0.091138 | 0.094999 |
| 16 | 0.175781 | 0.172646 | 0.177778 | 0.176087 | 0.167860 | 0.168161 | 0.166667 | 0.169203 | 0.766276 | 0.379774 | 0.299376 | 0.305679 | 0.091151 | 0.094825 |
| 17 | 0.171224 | 0.163677 | 0.174603 | 0.173913 | 0.171658 | 0.166293 | 0.165079 | 0.185870 | 0.772786 | 0.411133 | 0.315283 | 0.331323 | 0.091089 | 0.094660 |
| 18 | 0.171224 | 0.172646 | 0.174603 | 0.165217 | 0.156141 | 0.158819 | 0.151852 | 0.159420 | 0.750651 | 0.482639 | 0.358799 | 0.349498 | 0.091139 | 0.094570 |
| 19 | 0.167969 | 0.159193 | 0.174603 | 0.167391 | 0.159180 | 0.162182 | 0.157143 | 0.159058 | 0.722656 | 0.431641 | 0.348606 | 0.365340 | 0.091168 | 0.094483 |
| 20 | 0.156250 | 0.163677 | 0.163492 | 0.139130 | 0.154622 | 0.159940 | 0.150794 | 0.154710 | 0.763021 | 0.338759 | 0.431346 | 0.442429 | 0.091263 | 0.094553 |

Window `r >= R/2` = rollouts 10-20 (11 checkpoints):

| Quantity | Value |
| --- | --- |
| team label agreement, mean over window | 0.708807 |
| individual label agreement, mean over window | 0.393377 |
| team accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.164891 / 0.157358 / 0.168687 / 0.166996 |
| individual accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.162218 / 0.163847 / 0.157696 / 0.166831 |
| team value mean abs change: mean / variance over window | 0.461071 / 1.716928e-02 |
| agent value mean abs change: mean / variance over window | 0.469579 / 1.764214e-02 |
| per-probe variance of the value across window rollouts, mean over probes: team / agent | 0.292900 / 0.297951 |
| age-feature weight share, team: rollout 1 -> rollout 20 | 0.091223 -> 0.091263 |
| age-feature weight share, individual: rollout 1 -> rollout 20 | 0.097253 -> 0.094553 |

Verbatim final stdout lines:

```
{"arm": "d1", "seed": 2, "completed": true, "rollouts_completed": 20, "transitions_total": 320000, "episodes_total": 640, "optimizer_steps_total": {"coordinator": 3900, "discoverer_actor": 90000, "discoverer_critic": 90000, "team_discriminator": 300, "individual_discriminator": 1200}, "evaluation_count": 4, "final_evaluation_return_mean": 21.161224998417232, "exposure_line_rollout_last": {"coordinator": 0.14741430234640324, "discoverer_actor": 1.069782829355893, "discoverer_critic": 0.48633988159205765, "team_discriminator": 0.058849982691519094, "individual_discriminator": 0.0851415036388816}, "wall_seconds_total": 7959.049102600009, "seconds_per_rollout_mean": 393.1878180499989, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d1_seed2"}
{"e1_arm": "d1", "age_feature": "normalized", "seed": 2, "rollouts": 20, "num_envs": 32, "e0_status": 0, "probe_measurement_rollouts": 20, "probe_set_content_sha256": "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c", "team_accuracy_final": {"overall": 0.15625, "overall_n": 1536, "0-2": 0.16367713004484305, "0-2_n": 446, "3-6": 0.1634920634920635, "3-6_n": 630, "7-9": 0.1391304347826087, "7-9_n": 460}, "individual_accuracy_final": {"overall": 0.15462239583333334, "overall_n": 9216, "0-2": 0.15994020926756353, "0-2_n": 2676, "3-6": 0.15079365079365079, "3-6_n": 3780, "7-9": 0.15471014492753624, "7-9_n": 2760}, "team_label_agreement_mean_window": 0.7088068181818182, "individual_label_agreement_mean_window": 0.3933771306818182, "age_weight_share_final": {"team": {"age_column_norm": 1.0005839358177726, "input_projection_norm": 10.963694199693386, "age_share": 0.09126339330458116}, "individual": {"age_column_norm": 0.9684668284185846, "input_projection_norm": 10.242593705980875, "age_share": 0.09455288926017592}}, "e1_wall_seconds": 7959.381721700003, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d1_seed2"}
```

### D0 seed 3 (`d0_seed3`)

| Fact | Value |
| --- | --- |
| completed / rollouts | `True` / 20 of 20 |
| transitions / episodes | 320,000 / 640 |
| `M` every rollout | 1600 (all 20 rollouts: constant) |
| optimizer steps (coordinator / disc-actor / disc-critic / team-D / ind-D) | 3,900 / 90,000 / 90,000 / 300 / 1,200 |
| evaluations | 4 |
| wall / mean s per rollout | 6084.0 s (101.4 min) / 299.9 s |
| started / ended (UTC) | 2026-09-03T09:26:16+00:00 / 2026-09-03T11:07:40+00:00 |
| preflight `assessed_at` / available physical = effective / `passed` | 2026-09-03T09:26:16.505146Z / 15,586,078,720 B (14.52 GiB) / `True` |
| manifest `code_sha` / `launch_commit` | `b9290a1ed9ea` / `6fba1c7ba` |
| quarantined | `False` |

Exposure line and counters per rollout (`||theta - theta_0|| / ||theta_0||`, float64):

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16000 | 32 | 1600 | 195 | 20.6285 | 0.3945 | 3.495082e-02 | 1.947223e-01 | 1.076494e-01 | 1.096024e-02 | 2.156151e-02 | 42.0 | 254.2 |
| 2 | 32000 | 64 | 1600 | 390 | 18.5902 | 0.3555 | 4.276286e-02 | 3.072238e-01 | 1.493361e-01 | 1.616838e-02 | 3.044424e-02 | 43.7 | 256.2 |
| 3 | 48000 | 96 | 1600 | 585 | 20.6467 | 0.3948 | 4.967441e-02 | 4.064548e-01 | 1.818773e-01 | 2.092516e-02 | 3.768081e-02 | 47.1 | 259.7 |
| 4 | 64000 | 128 | 1600 | 780 | 24.1346 | 0.4615 | 5.435927e-02 | 4.710697e-01 | 2.093320e-01 | 2.545185e-02 | 4.286821e-02 | 44.6 | 246.6 |
| 5 | 80000 | 160 | 1600 | 975 | 25.3276 | 0.4843 | 5.979163e-02 | 5.279326e-01 | 2.331375e-01 | 2.936886e-02 | 4.757063e-02 | 45.2 | 248.6 |
| 6 | 96000 | 192 | 1600 | 1170 | 24.3948 | 0.4665 | 6.417566e-02 | 5.722108e-01 | 2.554604e-01 | 3.266703e-02 | 5.229060e-02 | 41.6 | 245.5 |
| 7 | 112000 | 224 | 1600 | 1365 | 22.6868 | 0.4339 | 6.996883e-02 | 6.220826e-01 | 2.797376e-01 | 3.550013e-02 | 5.666994e-02 | 44.0 | 243.2 |
| 8 | 128000 | 256 | 1600 | 1560 | 25.2270 | 0.4824 | 7.471688e-02 | 6.619089e-01 | 2.985464e-01 | 3.805533e-02 | 6.003666e-02 | 46.1 | 248.1 |
| 9 | 144000 | 288 | 1600 | 1755 | 23.8795 | 0.4567 | 7.964376e-02 | 6.980613e-01 | 3.176340e-01 | 4.010189e-02 | 6.309451e-02 | 49.8 | 273.0 |
| 10 | 160000 | 320 | 1600 | 1950 | 25.5210 | 0.4881 | 8.461814e-02 | 7.355949e-01 | 3.358024e-01 | 4.227833e-02 | 6.582539e-02 | 55.7 | 279.0 |
| 11 | 176000 | 352 | 1600 | 2145 | 28.1359 | 0.5381 | 8.925120e-02 | 7.742326e-01 | 3.530245e-01 | 4.459192e-02 | 6.830995e-02 | 44.1 | 251.0 |
| 12 | 192000 | 384 | 1600 | 2340 | 28.6889 | 0.5486 | 9.374429e-02 | 8.104104e-01 | 3.704213e-01 | 4.652974e-02 | 7.102896e-02 | 50.7 | 255.0 |
| 13 | 208000 | 416 | 1600 | 2535 | 27.4969 | 0.5258 | 9.838683e-02 | 8.448095e-01 | 3.872953e-01 | 4.827989e-02 | 7.380861e-02 | 49.8 | 258.4 |
| 14 | 224000 | 448 | 1600 | 2730 | 26.3933 | 0.5047 | 1.027350e-01 | 8.756959e-01 | 4.038604e-01 | 4.984956e-02 | 7.676220e-02 | 49.5 | 245.5 |
| 15 | 240000 | 480 | 1600 | 2925 | 25.5813 | 0.4892 | 1.076844e-01 | 9.067140e-01 | 4.183464e-01 | 5.131445e-02 | 7.914450e-02 | 45.9 | 235.0 |
| 16 | 256000 | 512 | 1600 | 3120 | 26.6896 | 0.5104 | 1.128087e-01 | 9.378404e-01 | 4.338366e-01 | 5.260232e-02 | 8.162996e-02 | 55.7 | 249.6 |
| 17 | 272000 | 544 | 1600 | 3315 | 25.7483 | 0.4924 | 1.172726e-01 | 9.688093e-01 | 4.502058e-01 | 5.391231e-02 | 8.375652e-02 | 47.0 | 270.4 |
| 18 | 288000 | 576 | 1600 | 3510 | 26.6028 | 0.5087 | 1.211306e-01 | 9.965617e-01 | 4.657275e-01 | 5.546985e-02 | 8.616793e-02 | 53.7 | 268.8 |
| 19 | 304000 | 608 | 1600 | 3705 | 26.7903 | 0.5123 | 1.259419e-01 | 1.024978e+00 | 4.799654e-01 | 5.702990e-02 | 8.843737e-02 | 44.0 | 234.5 |
| 20 | 320000 | 640 | 1600 | 3900 | 27.2701 | 0.5215 | 1.297962e-01 | 1.050289e+00 | 4.941769e-01 | 5.831416e-02 | 8.982481e-02 | 42.7 | 232.0 |

Evaluations (8 deterministic episodes, lanes seeded `10_000 + rank`):

| after rollout | episodes | return mean | return sd | wall s |
| --- | --- | --- | --- | --- |
| 5 | 8 | 30.5253 | 5.1019 | 18.4 |
| 10 | 8 | 28.3837 | 2.8762 | 20.8 |
| 15 | 8 | 31.8389 | 3.7583 | 19.3 |
| 20 | 8 | 39.7849 | 3.9604 | 18.3 |

Contract section 3 probe measurements (1,536 frozen probes, after every rollout's update):

| r | team acc all | 0-2 | 3-6 | 7-9 | ind acc all | 0-2 | 3-6 | 7-9 | team agree | ind agree | team d\|V\| | agent d\|V\| | age share team | age share ind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.143229 | 0.143498 | 0.141270 | 0.145652 | 0.150174 | 0.147235 | 0.157937 | 0.142391 | - | - | - | - | - | - |
| 2 | 0.136719 | 0.139013 | 0.133333 | 0.139130 | 0.161133 | 0.148356 | 0.166931 | 0.165580 | 0.888672 | 0.552409 | 1.069874 | 1.022276 | - | - |
| 3 | 0.143880 | 0.156951 | 0.134921 | 0.143478 | 0.153971 | 0.152093 | 0.156614 | 0.152174 | 0.875000 | 0.464627 | 0.484541 | 0.445735 | - | - |
| 4 | 0.135417 | 0.154709 | 0.119048 | 0.139130 | 0.144531 | 0.147982 | 0.148413 | 0.135870 | 0.878255 | 0.440104 | 0.601124 | 0.718636 | - | - |
| 5 | 0.135417 | 0.159193 | 0.123810 | 0.128261 | 0.145725 | 0.145366 | 0.151587 | 0.138043 | 0.851562 | 0.442491 | 0.495585 | 0.518757 | - | - |
| 6 | 0.137370 | 0.143498 | 0.126984 | 0.145652 | 0.160807 | 0.167788 | 0.160317 | 0.154710 | 0.894531 | 0.299262 | 0.413652 | 0.439805 | - | - |
| 7 | 0.143880 | 0.154709 | 0.134921 | 0.145652 | 0.165148 | 0.163677 | 0.168254 | 0.162319 | 0.878255 | 0.318468 | 0.437694 | 0.484059 | - | - |
| 8 | 0.141927 | 0.145740 | 0.131746 | 0.152174 | 0.165907 | 0.163677 | 0.170370 | 0.161957 | 0.834635 | 0.345486 | 0.515622 | 0.512149 | - | - |
| 9 | 0.151693 | 0.165919 | 0.146032 | 0.145652 | 0.165473 | 0.165546 | 0.165608 | 0.165217 | 0.812500 | 0.310981 | 0.446538 | 0.534425 | - | - |
| 10 | 0.150391 | 0.154709 | 0.147619 | 0.150000 | 0.166341 | 0.161061 | 0.167460 | 0.169928 | 0.791016 | 0.307400 | 0.407512 | 0.460767 | - | - |
| 11 | 0.149740 | 0.156951 | 0.153968 | 0.136957 | 0.162543 | 0.158819 | 0.166402 | 0.160870 | 0.813802 | 0.315647 | 0.376634 | 0.393075 | - | - |
| 12 | 0.167969 | 0.172646 | 0.176190 | 0.152174 | 0.161350 | 0.150224 | 0.170635 | 0.159420 | 0.835938 | 0.388455 | 0.280106 | 0.314857 | - | - |
| 13 | 0.167969 | 0.195067 | 0.158730 | 0.154348 | 0.154405 | 0.158072 | 0.155820 | 0.148913 | 0.833984 | 0.398112 | 0.273013 | 0.390165 | - | - |
| 14 | 0.203776 | 0.221973 | 0.200000 | 0.191304 | 0.164931 | 0.159193 | 0.160847 | 0.176087 | 0.562500 | 0.426107 | 0.331587 | 0.364610 | - | - |
| 15 | 0.176432 | 0.172646 | 0.179365 | 0.176087 | 0.167209 | 0.173767 | 0.162434 | 0.167391 | 0.753255 | 0.490343 | 0.346059 | 0.452790 | - | - |
| 16 | 0.149089 | 0.156951 | 0.155556 | 0.132609 | 0.162760 | 0.162182 | 0.161640 | 0.164855 | 0.638021 | 0.370226 | 0.321295 | 0.386376 | - | - |
| 17 | 0.146484 | 0.161435 | 0.153968 | 0.121739 | 0.161133 | 0.165546 | 0.160847 | 0.157246 | 0.753906 | 0.353407 | 0.401778 | 0.419533 | - | - |
| 18 | 0.151693 | 0.152466 | 0.166667 | 0.130435 | 0.158854 | 0.162556 | 0.158995 | 0.155072 | 0.817057 | 0.380425 | 0.314964 | 0.311324 | - | - |
| 19 | 0.136719 | 0.139013 | 0.133333 | 0.139130 | 0.160807 | 0.159567 | 0.164815 | 0.156522 | 0.733724 | 0.467990 | 0.341973 | 0.304062 | - | - |
| 20 | 0.159505 | 0.147982 | 0.171429 | 0.154348 | 0.165256 | 0.169656 | 0.163492 | 0.163406 | 0.690104 | 0.500868 | 0.244269 | 0.271614 | - | - |

Window `r >= R/2` = rollouts 10-20 (11 checkpoints):

| Quantity | Value |
| --- | --- |
| team label agreement, mean over window | 0.747573 |
| individual label agreement, mean over window | 0.399907 |
| team accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.159979 / 0.166531 / 0.163348 / 0.149012 |
| individual accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.162326 / 0.161877 / 0.163035 / 0.161792 |
| team value mean abs change: mean / variance over window | 0.330835 / 2.465423e-03 |
| agent value mean abs change: mean / variance over window | 0.369925 / 3.572175e-03 |
| per-probe variance of the value across window rollouts, mean over probes: team / agent | 0.139376 / 0.160340 |

Verbatim final stdout lines:

```
{"arm": "d0", "seed": 3, "completed": true, "rollouts_completed": 20, "transitions_total": 320000, "episodes_total": 640, "optimizer_steps_total": {"coordinator": 3900, "discoverer_actor": 90000, "discoverer_critic": 90000, "team_discriminator": 300, "individual_discriminator": 1200}, "evaluation_count": 4, "final_evaluation_return_mean": 39.78489595569327, "exposure_line_rollout_last": {"coordinator": 0.12979619542446905, "discoverer_actor": 1.0502894421389044, "discoverer_critic": 0.49417691360056487, "team_discriminator": 0.05831416433373622, "individual_discriminator": 0.08982480963834708}, "wall_seconds_total": 6083.9991171, "seconds_per_rollout_mean": 299.8711349550038, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d0_seed3"}
{"e1_arm": "d0", "age_feature": "off", "seed": 3, "rollouts": 20, "num_envs": 32, "e0_status": 0, "probe_measurement_rollouts": 20, "probe_set_content_sha256": "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c", "team_accuracy_final": {"overall": 0.15950520833333334, "overall_n": 1536, "0-2": 0.14798206278026907, "0-2_n": 446, "3-6": 0.17142857142857143, "3-6_n": 630, "7-9": 0.15434782608695652, "7-9_n": 460}, "individual_accuracy_final": {"overall": 0.1652560763888889, "overall_n": 9216, "0-2": 0.1696562032884903, "0-2_n": 2676, "3-6": 0.1634920634920635, "3-6_n": 3780, "7-9": 0.16340579710144928, "7-9_n": 2760}, "team_label_agreement_mean_window": 0.7475733901515151, "individual_label_agreement_mean_window": 0.3999072758838384, "age_weight_share_final": null, "e1_wall_seconds": 6084.155057800002, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d0_seed3"}
```

### D1 seed 3 (`d1_seed3`)

| Fact | Value |
| --- | --- |
| completed / rollouts | `True` / 20 of 20 |
| transitions / episodes | 320,000 / 640 |
| `M` every rollout | 1600 (all 20 rollouts: constant) |
| optimizer steps (coordinator / disc-actor / disc-critic / team-D / ind-D) | 3,900 / 90,000 / 90,000 / 300 / 1,200 |
| evaluations | 4 |
| wall / mean s per rollout | 6138.1 s (102.3 min) / 303.3 s |
| started / ended (UTC) | 2026-09-03T09:26:16+00:00 / 2026-09-03T11:08:34+00:00 |
| preflight `assessed_at` / available physical = effective / `passed` | 2026-09-03T09:26:16.509400Z / 15,585,103,872 B (14.51 GiB) / `True` |
| manifest `code_sha` / `launch_commit` | `b9290a1ed9ea` / `6fba1c7ba` |
| quarantined | `False` |

Exposure line and counters per rollout (`||theta - theta_0|| / ||theta_0||`, float64):

| r | transitions | episodes | `M` | coord opt steps | mean ep return | mean HL segment reward | coord | disc-actor | disc-critic | team-D | ind-D | collect s | update s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16000 | 32 | 1600 | 195 | 19.8688 | 0.3800 | 3.461090e-02 | 1.975495e-01 | 1.069066e-01 | 1.250928e-02 | 2.086734e-02 | 41.9 | 253.7 |
| 2 | 32000 | 64 | 1600 | 390 | 18.9616 | 0.3626 | 4.152101e-02 | 3.113781e-01 | 1.493252e-01 | 1.824474e-02 | 2.946128e-02 | 44.4 | 257.3 |
| 3 | 48000 | 96 | 1600 | 585 | 23.9568 | 0.4582 | 4.676057e-02 | 4.081441e-01 | 1.811705e-01 | 2.264006e-02 | 3.716367e-02 | 47.8 | 265.0 |
| 4 | 64000 | 128 | 1600 | 780 | 19.5980 | 0.3748 | 5.252645e-02 | 4.772938e-01 | 2.088862e-01 | 2.656161e-02 | 4.288879e-02 | 44.2 | 253.1 |
| 5 | 80000 | 160 | 1600 | 975 | 14.4023 | 0.2755 | 6.075049e-02 | 5.335451e-01 | 2.351494e-01 | 2.951345e-02 | 4.723462e-02 | 41.7 | 253.4 |
| 6 | 96000 | 192 | 1600 | 1170 | 17.4358 | 0.3335 | 6.724273e-02 | 5.825061e-01 | 2.600061e-01 | 3.255190e-02 | 5.076475e-02 | 42.7 | 250.6 |
| 7 | 112000 | 224 | 1600 | 1365 | 16.3294 | 0.3123 | 7.420785e-02 | 6.317666e-01 | 2.808938e-01 | 3.545634e-02 | 5.425645e-02 | 42.0 | 253.3 |
| 8 | 128000 | 256 | 1600 | 1560 | 16.5490 | 0.3165 | 8.089260e-02 | 6.673825e-01 | 3.030565e-01 | 3.790588e-02 | 5.756564e-02 | 40.2 | 259.3 |
| 9 | 144000 | 288 | 1600 | 1755 | 17.8472 | 0.3413 | 8.708977e-02 | 7.039965e-01 | 3.225579e-01 | 4.013459e-02 | 6.116967e-02 | 47.2 | 282.6 |
| 10 | 160000 | 320 | 1600 | 1950 | 17.0172 | 0.3255 | 9.258748e-02 | 7.406287e-01 | 3.424370e-01 | 4.223790e-02 | 6.482041e-02 | 51.3 | 279.5 |
| 11 | 176000 | 352 | 1600 | 2145 | 29.1730 | 0.5579 | 9.569504e-02 | 7.767596e-01 | 3.596171e-01 | 4.387397e-02 | 6.835230e-02 | 44.7 | 259.2 |
| 12 | 192000 | 384 | 1600 | 2340 | 24.1988 | 0.4628 | 1.001058e-01 | 8.078674e-01 | 3.748768e-01 | 4.523341e-02 | 7.116750e-02 | 51.4 | 257.1 |
| 13 | 208000 | 416 | 1600 | 2535 | 30.2406 | 0.5783 | 1.044598e-01 | 8.378100e-01 | 3.897620e-01 | 4.690123e-02 | 7.348887e-02 | 44.6 | 266.2 |
| 14 | 224000 | 448 | 1600 | 2730 | 29.0178 | 0.5549 | 1.088187e-01 | 8.665046e-01 | 4.045633e-01 | 4.850340e-02 | 7.635570e-02 | 47.6 | 248.4 |
| 15 | 240000 | 480 | 1600 | 2925 | 27.1165 | 0.5185 | 1.133116e-01 | 8.926801e-01 | 4.172401e-01 | 5.020902e-02 | 7.927225e-02 | 45.4 | 249.6 |
| 16 | 256000 | 512 | 1600 | 3120 | 26.0535 | 0.4982 | 1.186331e-01 | 9.174618e-01 | 4.314834e-01 | 5.203428e-02 | 8.213807e-02 | 48.6 | 254.5 |
| 17 | 272000 | 544 | 1600 | 3315 | 27.9838 | 0.5352 | 1.234204e-01 | 9.458339e-01 | 4.451186e-01 | 5.370674e-02 | 8.458489e-02 | 53.8 | 275.1 |
| 18 | 288000 | 576 | 1600 | 3510 | 25.0353 | 0.4788 | 1.278004e-01 | 9.720573e-01 | 4.591563e-01 | 5.511441e-02 | 8.703361e-02 | 54.2 | 259.3 |
| 19 | 304000 | 608 | 1600 | 3705 | 28.3198 | 0.5415 | 1.323711e-01 | 9.966069e-01 | 4.714101e-01 | 5.652162e-02 | 8.920842e-02 | 47.4 | 233.9 |
| 20 | 320000 | 640 | 1600 | 3900 | 28.1981 | 0.5392 | 1.370501e-01 | 1.024360e+00 | 4.844759e-01 | 5.800193e-02 | 9.155238e-02 | 43.7 | 230.2 |

Evaluations (8 deterministic episodes, lanes seeded `10_000 + rank`):

| after rollout | episodes | return mean | return sd | wall s |
| --- | --- | --- | --- | --- |
| 5 | 8 | 24.2197 | 6.8221 | 16.1 |
| 10 | 8 | 26.5257 | 5.1995 | 15.2 |
| 15 | 8 | 32.8199 | 4.7103 | 18.9 |
| 20 | 8 | 36.6170 | 3.0893 | 12.3 |

Contract section 3 probe measurements (1,536 frozen probes, after every rollout's update):

| r | team acc all | 0-2 | 3-6 | 7-9 | ind acc all | 0-2 | 3-6 | 7-9 | team agree | ind agree | team d\|V\| | agent d\|V\| | age share team | age share ind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.139323 | 0.139013 | 0.134921 | 0.145652 | 0.148655 | 0.148729 | 0.155291 | 0.139493 | - | - | - | - | 0.091366 | 0.097412 |
| 2 | 0.138672 | 0.134529 | 0.133333 | 0.150000 | 0.148763 | 0.153961 | 0.149471 | 0.142754 | 0.926432 | 0.680556 | 0.730566 | 0.723469 | 0.091354 | 0.097372 |
| 3 | 0.137370 | 0.139013 | 0.131746 | 0.143478 | 0.153212 | 0.150598 | 0.159788 | 0.146739 | 0.960286 | 0.566298 | 0.877469 | 0.842726 | 0.091349 | 0.096856 |
| 4 | 0.138672 | 0.145740 | 0.126984 | 0.147826 | 0.149306 | 0.144619 | 0.151852 | 0.150362 | 0.955078 | 0.472982 | 0.489296 | 0.456352 | 0.091338 | 0.096483 |
| 5 | 0.136068 | 0.134529 | 0.133333 | 0.141304 | 0.149306 | 0.150598 | 0.148677 | 0.148913 | 0.936849 | 0.534939 | 0.611992 | 0.564859 | 0.091303 | 0.096309 |
| 6 | 0.136719 | 0.136771 | 0.130159 | 0.145652 | 0.155707 | 0.154335 | 0.150000 | 0.164855 | 0.973307 | 0.496853 | 0.573516 | 0.570480 | 0.091312 | 0.096219 |
| 7 | 0.140625 | 0.136771 | 0.131746 | 0.156522 | 0.152344 | 0.150224 | 0.154233 | 0.151812 | 0.960286 | 0.444119 | 0.468876 | 0.452324 | 0.091447 | 0.095959 |
| 8 | 0.135417 | 0.136771 | 0.125397 | 0.147826 | 0.148872 | 0.159567 | 0.142593 | 0.147101 | 0.960938 | 0.358290 | 0.503314 | 0.515176 | 0.091582 | 0.095827 |
| 9 | 0.138672 | 0.143498 | 0.128571 | 0.147826 | 0.165690 | 0.178625 | 0.164815 | 0.154348 | 0.987630 | 0.324870 | 0.492790 | 0.508391 | 0.091708 | 0.095388 |
| 10 | 0.133464 | 0.134529 | 0.122222 | 0.147826 | 0.166233 | 0.173019 | 0.165608 | 0.160507 | 0.975911 | 0.359375 | 0.518724 | 0.498223 | 0.091654 | 0.095128 |
| 11 | 0.134115 | 0.134529 | 0.123810 | 0.147826 | 0.161675 | 0.159940 | 0.160317 | 0.165217 | 0.889323 | 0.318034 | 1.391600 | 1.359611 | 0.091584 | 0.094801 |
| 12 | 0.128906 | 0.114350 | 0.119048 | 0.156522 | 0.158854 | 0.151345 | 0.163492 | 0.159783 | 0.717448 | 0.353733 | 0.433076 | 0.453340 | 0.091538 | 0.094413 |
| 13 | 0.138021 | 0.118834 | 0.130159 | 0.167391 | 0.152018 | 0.158445 | 0.154233 | 0.142754 | 0.770833 | 0.353190 | 0.463953 | 0.558804 | 0.091607 | 0.094299 |
| 14 | 0.137370 | 0.114350 | 0.136508 | 0.160870 | 0.169813 | 0.177877 | 0.167725 | 0.164855 | 0.800130 | 0.239692 | 0.608034 | 0.552544 | 0.091544 | 0.094088 |
| 15 | 0.143880 | 0.134529 | 0.133333 | 0.167391 | 0.161675 | 0.161061 | 0.162698 | 0.160870 | 0.789062 | 0.400391 | 0.329220 | 0.318453 | 0.091569 | 0.093762 |
| 16 | 0.140625 | 0.143498 | 0.133333 | 0.147826 | 0.173720 | 0.186099 | 0.171164 | 0.165217 | 0.828776 | 0.379883 | 0.364685 | 0.346615 | 0.091555 | 0.093593 |
| 17 | 0.138021 | 0.139013 | 0.131746 | 0.145652 | 0.164714 | 0.168909 | 0.165079 | 0.160145 | 0.774089 | 0.378906 | 0.340362 | 0.361179 | 0.091540 | 0.093507 |
| 18 | 0.139323 | 0.130045 | 0.128571 | 0.163043 | 0.155490 | 0.162182 | 0.150794 | 0.155435 | 0.824219 | 0.324002 | 0.314675 | 0.315177 | 0.091586 | 0.093376 |
| 19 | 0.147135 | 0.172646 | 0.141270 | 0.130435 | 0.167969 | 0.176383 | 0.170106 | 0.156884 | 0.740885 | 0.370877 | 0.352660 | 0.374618 | 0.091650 | 0.092985 |
| 20 | 0.128255 | 0.141256 | 0.123810 | 0.121739 | 0.160590 | 0.168161 | 0.157672 | 0.157246 | 0.875651 | 0.381619 | 0.346688 | 0.326305 | 0.091762 | 0.092899 |

Window `r >= R/2` = rollouts 10-20 (11 checkpoints):

| Quantity | Value |
| --- | --- |
| team label agreement, mean over window | 0.816939 |
| individual label agreement, mean over window | 0.350882 |
| team accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.137192 / 0.134325 / 0.129437 / 0.150593 |
| individual accuracy over window: overall / 0-2 / 3-6 / 7-9 | 0.162977 / 0.167584 / 0.162626 / 0.158992 |
| team value mean abs change: mean / variance over window | 0.496698 / 8.774087e-02 |
| agent value mean abs change: mean / variance over window | 0.496806 / 8.209324e-02 |
| per-probe variance of the value across window rollouts, mean over probes: team / agent | 0.353044 / 0.358326 |
| age-feature weight share, team: rollout 1 -> rollout 20 | 0.091366 -> 0.091762 |
| age-feature weight share, individual: rollout 1 -> rollout 20 | 0.097412 -> 0.092899 |

Verbatim final stdout lines:

```
{"arm": "d1", "seed": 3, "completed": true, "rollouts_completed": 20, "transitions_total": 320000, "episodes_total": 640, "optimizer_steps_total": {"coordinator": 3900, "discoverer_actor": 90000, "discoverer_critic": 90000, "team_discriminator": 300, "individual_discriminator": 1200}, "evaluation_count": 4, "final_evaluation_return_mean": 36.617012922564314, "exposure_line_rollout_last": {"coordinator": 0.13705010124047093, "discoverer_actor": 1.0243602767746158, "discoverer_critic": 0.4844758775525375, "team_discriminator": 0.05800192745722801, "individual_discriminator": 0.09155237581164914}, "wall_seconds_total": 6138.149276499986, "seconds_per_rollout_mean": 303.3073087349956, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d1_seed3"}
{"e1_arm": "d1", "age_feature": "normalized", "seed": 3, "rollouts": 20, "num_envs": 32, "e0_status": 0, "probe_measurement_rollouts": 20, "probe_set_content_sha256": "1b983ea98260a6b498fb0a01fb66d245fb4af105eb5dca43a0042d712afbf51c", "team_accuracy_final": {"overall": 0.12825520833333334, "overall_n": 1536, "0-2": 0.1412556053811659, "0-2_n": 446, "3-6": 0.12380952380952381, "3-6_n": 630, "7-9": 0.12173913043478261, "7-9_n": 460}, "individual_accuracy_final": {"overall": 0.1605902777777778, "overall_n": 9216, "0-2": 0.1681614349775785, "0-2_n": 2676, "3-6": 0.15767195767195769, "3-6_n": 3780, "7-9": 0.1572463768115942, "7-9_n": 2760}, "team_label_agreement_mean_window": 0.8169389204545454, "individual_label_agreement_mean_window": 0.35088186553030304, "age_weight_share_final": {"team": {"age_column_norm": 1.0062992360234848, "input_projection_norm": 10.966361747507154, "age_share": 0.091762360132998}, "individual": {"age_column_norm": 0.9520570812971895, "input_projection_norm": 10.248338666306335, "age_share": 0.09289867482885654}}, "e1_wall_seconds": 6138.308254400006, "run_dir": "C:\\Projects\\HMASD\\temp\\directions\\flexible_skill_duration\\exp\\E1_20260902\\d1_seed3"}
```
---

## 6. Per-pair differences (D1 minus D0 at the same seed)

Machine-written to `E1_summary.json` at the study root. Every number below is a difference of
two numbers already printed in §5; nothing new is measured here.

### 6.1a Team probe accuracy, mean over the window `r >= 10`

| seed | D0 overall | D1 overall | gain overall | D0 0-2 | D1 0-2 | **gain 0-2** | D0 3-6 | D1 3-6 | gain 3-6 | D0 7-9 | D1 7-9 | **gain 7-9** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.144472 | 0.227214 | +0.082741 | 0.136771 | 0.233999 | **+0.097228** | 0.149928 | 0.233045 | +0.083117 | 0.144466 | 0.212648 | **+0.068182** |
| 2 | 0.184304 | 0.164891 | -0.019413 | 0.208316 | 0.157358 | **-0.050958** | 0.181530 | 0.168687 | -0.012843 | 0.164822 | 0.166996 | **+0.002174** |
| 3 | 0.159979 | 0.137192 | -0.022786 | 0.166531 | 0.134325 | **-0.032205** | 0.163348 | 0.129437 | -0.033911 | 0.149012 | 0.150593 | **+0.001581** |

Across-seed spread of the gain (max minus min over the 3 seed pairs): 0-2 `0.148186`, 3-6 `0.117027`, 7-9 `0.066601`.

### 6.1b Team probe accuracy, at the final rollout, `r = 20`

| seed | D0 overall | D1 overall | gain overall | D0 0-2 | D1 0-2 | **gain 0-2** | D0 3-6 | D1 3-6 | gain 3-6 | D0 7-9 | D1 7-9 | **gain 7-9** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.134115 | 0.218750 | +0.084635 | 0.132287 | 0.244395 | **+0.112108** | 0.144444 | 0.220635 | +0.076190 | 0.121739 | 0.191304 | **+0.069565** |
| 2 | 0.152995 | 0.156250 | +0.003255 | 0.170404 | 0.163677 | **-0.006726** | 0.165079 | 0.163492 | -0.001587 | 0.119565 | 0.139130 | **+0.019565** |
| 3 | 0.159505 | 0.128255 | -0.031250 | 0.147982 | 0.141256 | **-0.006726** | 0.171429 | 0.123810 | -0.047619 | 0.154348 | 0.121739 | **-0.032609** |

Across-seed spread of the gain (max minus min over the 3 seed pairs): 0-2 `0.118834`, 3-6 `0.123810`, 7-9 `0.102174`.

### 6.2a Individual probe accuracy, mean over the window `r >= 10`

| seed | D0 overall | D1 overall | gain overall | D0 0-2 | D1 0-2 | **gain 0-2** | D0 3-6 | D1 3-6 | gain 3-6 | D0 7-9 | D1 7-9 | **gain 7-9** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.168423 | 0.173019 | +0.004597 | 0.168467 | 0.167312 | **-0.001155** | 0.166306 | 0.173425 | +0.007119 | 0.171278 | 0.177997 | **+0.006719** |
| 2 | 0.171165 | 0.162218 | -0.008947 | 0.168195 | 0.163847 | **-0.004348** | 0.172294 | 0.157696 | -0.014598 | 0.172497 | 0.166831 | **-0.005665** |
| 3 | 0.162326 | 0.162977 | +0.000651 | 0.161877 | 0.167584 | **+0.005707** | 0.163035 | 0.162626 | -0.000409 | 0.161792 | 0.158992 | **-0.002800** |

Across-seed spread of the gain (max minus min over the 3 seed pairs): 0-2 `0.010056`, 3-6 `0.021717`, 7-9 `0.012385`.

### 6.2b Individual probe accuracy, at the final rollout, `r = 20`

| seed | D0 overall | D1 overall | gain overall | D0 0-2 | D1 0-2 | **gain 0-2** | D0 3-6 | D1 3-6 | gain 3-6 | D0 7-9 | D1 7-9 | **gain 7-9** |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.165690 | 0.178060 | +0.012370 | 0.172646 | 0.168909 | **-0.003737** | 0.158201 | 0.178571 | +0.020370 | 0.169203 | 0.186232 | **+0.017029** |
| 2 | 0.164605 | 0.154622 | -0.009983 | 0.158445 | 0.159940 | **+0.001495** | 0.163228 | 0.150794 | -0.012434 | 0.172464 | 0.154710 | **-0.017754** |
| 3 | 0.165256 | 0.160590 | -0.004666 | 0.169656 | 0.168161 | **-0.001495** | 0.163492 | 0.157672 | -0.005820 | 0.163406 | 0.157246 | **-0.006159** |

Across-seed spread of the gain (max minus min over the 3 seed pairs): 0-2 `0.005232`, 3-6 `0.032804`, 7-9 `0.034783`.

### 6.3 Label agreement, value drift and return

| seed | team agreement D0 | D1 | **D1-D0** | ind agreement D0 | D1 | **D1-D0** |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.761068 | 0.763080 | **+0.002012** | 0.422970 | 0.385752 | **-0.037218** |
| 2 | 0.685133 | 0.708807 | **+0.023674** | 0.447295 | 0.393377 | **-0.053918** |
| 3 | 0.747573 | 0.816939 | **+0.069366** | 0.399907 | 0.350882 | **-0.049025** |

Three-seed range of the difference: team `+0.002012` to `+0.069366` (range `0.067353`, mean `+0.031684`); individual `-0.053918` to `-0.037218` (range `0.016700`, mean `-0.046720`).

| seed | team value mean-abs-change D0 | D1 | D1-D0 | agent value mean-abs-change D0 | D1 | D1-D0 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.402966 | 0.574216 | +0.171250 | 0.424183 | 0.574789 | +0.150607 |
| 2 | 0.360329 | 0.461071 | +0.100742 | 0.361485 | 0.469579 | +0.108093 |
| 3 | 0.330835 | 0.496698 | +0.165862 | 0.369925 | 0.496806 | +0.126881 |

| seed | per-probe value variance over the window, team D0 | D1 | D1-D0 | agent D0 | D1 | D1-D0 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.195903 | 0.363445 | +0.167541 | 0.220975 | 0.377728 | +0.156753 |
| 2 | 0.218131 | 0.292900 | +0.074769 | 0.198254 | 0.297951 | +0.099697 |
| 3 | 0.139376 | 0.353044 | +0.213669 | 0.160340 | 0.358326 | +0.197986 |

| seed | D0 final evaluation return mean | D1 | D1-D0 |
| --- | --- | --- | --- |
| 1 | 44.8983 | 23.8099 | -21.0884 |
| 2 | 29.3664 | 21.1612 | -8.2052 |
| 3 | 39.7849 | 36.6170 | -3.1679 |

### 6.4 D1 age-feature weight share (contract §3 item 5)

| seed | team, rollout 1 | team, rollout 10 | team, rollout 20 | individual, rollout 1 | individual, rollout 10 | individual, rollout 20 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.091254 | 0.091773 | 0.091853 | 0.097355 | 0.095352 | 0.093972 |
| 2 | 0.091223 | 0.091201 | 0.091263 | 0.097253 | 0.095759 | 0.094553 |
| 3 | 0.091366 | 0.091654 | 0.091762 | 0.097412 | 0.095128 | 0.092899 |

The initialisation baseline — the share a column would have if every input column carried the
same weight norm — is `1/sqrt(120) = 0.091287` for the team discriminator and
`1/sqrt(105) = 0.097590` for the individual one.

---

## 7. The contract §5 reading rule, applied verbatim

> The prediction on record is contradicted if the D1 minus D0 probe-accuracy gain in the `7-9`
> bucket exceeds the gain in the `0-2` bucket by more than the across-seed spread of either, in
> at least two of three seed pairs. It is supported if the gains are within the spread in every
> bucket.

Two places in that wording leave a choice; both are computed and both are reported, and neither
is resolved silently.

* **Which accuracy.** §5 says "probe-accuracy" without saying team or individual. The rule is
  evaluated on both.
* **"more than the across-seed spread of either".** Strict reading: the excess must exceed
  *both* spreads, i.e. their maximum. Loose reading: at least one of them. The strict reading is
  the one reported as the verdict; the loose count is given beside it.

The window `r >= 10` is the primary application (it is the window the contract itself defines);
the final rollout is reported beside it.

### 7.1a Team accuracy, mean over the window `r >= 10`

| seed | gain 7-9 | gain 0-2 | excess (7-9 minus 0-2) | exceeds max spread? | exceeds min spread? |
| --- | --- | --- | --- | --- | --- |
| 1 | +0.068182 | +0.097228 | -0.029046 | False | False |
| 2 | +0.002174 | -0.050958 | +0.053132 | False | False |
| 3 | +0.001581 | -0.032205 | +0.033786 | False | False |

Across-seed spread: 7-9 `0.066601`, 0-2 `0.148186` -> strict threshold `0.148186`, loose threshold `0.066601`.

Seed pairs exceeding the strict threshold: **0 of 3** (rule needs at least two). Loose: 0 of 3.

"Gains within the spread in every bucket" (every seed's gain has magnitude no larger than that bucket's across-seed spread): 0-2 `True`, 3-6 `True`, 7-9 `False` -> supported = `False`.

**Verdict by the rule's own wording: `neither`.**

### 7.1b Individual accuracy, mean over the window `r >= 10`

| seed | gain 7-9 | gain 0-2 | excess (7-9 minus 0-2) | exceeds max spread? | exceeds min spread? |
| --- | --- | --- | --- | --- | --- |
| 1 | +0.006719 | -0.001155 | +0.007874 | False | False |
| 2 | -0.005665 | -0.004348 | -0.001317 | False | False |
| 3 | -0.002800 | +0.005707 | -0.008507 | False | False |

Across-seed spread: 7-9 `0.012385`, 0-2 `0.010056` -> strict threshold `0.012385`, loose threshold `0.010056`.

Seed pairs exceeding the strict threshold: **0 of 3** (rule needs at least two). Loose: 0 of 3.

"Gains within the spread in every bucket" (every seed's gain has magnitude no larger than that bucket's across-seed spread): 0-2 `True`, 3-6 `True`, 7-9 `True` -> supported = `True`.

**Verdict by the rule's own wording: `supported`.**

### 7.2a Team accuracy, at the final rollout `r = 20`

| seed | gain 7-9 | gain 0-2 | excess (7-9 minus 0-2) | exceeds max spread? | exceeds min spread? |
| --- | --- | --- | --- | --- | --- |
| 1 | +0.069565 | +0.112108 | -0.042542 | False | False |
| 2 | +0.019565 | -0.006726 | +0.026292 | False | False |
| 3 | -0.032609 | -0.006726 | -0.025882 | False | False |

Across-seed spread: 7-9 `0.102174`, 0-2 `0.118834` -> strict threshold `0.118834`, loose threshold `0.102174`.

Seed pairs exceeding the strict threshold: **0 of 3** (rule needs at least two). Loose: 0 of 3.

"Gains within the spread in every bucket" (every seed's gain has magnitude no larger than that bucket's across-seed spread): 0-2 `True`, 3-6 `True`, 7-9 `True` -> supported = `True`.

**Verdict by the rule's own wording: `supported`.**

### 7.2b Individual accuracy, at the final rollout `r = 20`

| seed | gain 7-9 | gain 0-2 | excess (7-9 minus 0-2) | exceeds max spread? | exceeds min spread? |
| --- | --- | --- | --- | --- | --- |
| 1 | +0.017029 | -0.003737 | +0.020766 | False | True |
| 2 | -0.017754 | +0.001495 | -0.019248 | False | False |
| 3 | -0.006159 | -0.001495 | -0.004665 | False | False |

Across-seed spread: 7-9 `0.034783`, 0-2 `0.005232` -> strict threshold `0.034783`, loose threshold `0.005232`.

Seed pairs exceeding the strict threshold: **0 of 3** (rule needs at least two). Loose: 1 of 3.

"Gains within the spread in every bucket" (every seed's gain has magnitude no larger than that bucket's across-seed spread): 0-2 `True`, 3-6 `True`, 7-9 `True` -> supported = `True`.

**Verdict by the rule's own wording: `supported`.**

### 7.3 Label agreement (contract §5, second clause)

> Label agreement: reported as D1 minus D0 per seed pair with the three-seed range; no
> threshold is fixed, the direction is the observation.

Reported in §6.3. The direction, stated because the rule asks for it and for nothing else:

* **team** label agreement is higher under D1 in **all three** seed pairs: `+0.002012`, `+0.023674`,
  `+0.069366`; three-seed range `+0.002012` to `+0.069366` (range `0.067353`, mean `+0.031684`);
* **individual** label agreement is **lower** under D1 in **all three** seed pairs: `-0.037218`,
  `-0.053918`, `-0.049025`; three-seed range `-0.053918` to `-0.037218` (range `0.016700`, mean
  `-0.046720`).

No threshold is fixed by the contract and none is applied here. The two directions are opposite,
and the individual difference is the more consistent of the two (its three-seed range, `0.0167`, is
smaller than the magnitude of every one of its three values).

### 7.4 Return (contract §5, third clause)

> Return: reported with the E0 caveat; a difference within the across-seed range of either arm
> is reported as "no difference observed at this budget".

Across-seed range of the final evaluation return mean: D0 `29.3664` to `44.8983` (range `15.5319`); D1 `21.1612` to `36.6170` (range `15.4558`).

Per-seed differences: -21.0884, -8.2052, -3.1679.

**Verdict by the rule's own wording: a difference outside the across-seed range of both arms.**
---

## 8. Deviations, each named

| # | Deviation | Status |
| --- | --- | --- |
| **D1** | **The seed-1 pair's first attempt was quarantined and seed 1 re-run once from scratch.** `d0_seed1` and `d1_seed1` were launched 2026-09-02T21:46:07Z / 21:46:17Z through the executing harness's background-task facility. About 65 minutes later the harness killed those background tasks, and the two python processes died with them, at **rollout 12 of 20**. The cause is external to the run: the resource preflight had passed, no non-finite loss or return was recorded, `metrics.jsonl` and `probe_metrics.jsonl` were being written normally, and no `summary.json`, `probe_labels.npz` or checkpoint existed. Under contract §4 item 3 and spec §6.2 an incomplete run is quarantined whatever the cause, so a `QUARANTINED` marker naming the cause was written into both directories; **nothing from them is interpreted, resumed or salvaged**, and no number from them appears anywhere in this document. Seed 1 was re-run from scratch under the new run names `d0_seed1_r2` / `d1_seed1_r2`, launched 22:52:58Z as two detached processes (PowerShell `Start-Process -WindowStyle Hidden`) so that the harness could not kill them again. **What changed is the launch mechanism, not the code**: `git diff eb5318ec1 b9290a1ed -- scripts/run_flexible_skill_duration_e1.py` is empty, and the runner is byte-identical across the quarantined attempt, the `_r2` rerun and the seed-2 and seed-3 pairs. This is **the one re-run contract §4 item 3 permits**; it succeeded, so no seed is reported as not run |
| **D2** | **Contract §2's expectation that "rollout 1 is identical up to the first discriminator update" does not hold between D0 and D1.** What *is* identical at rollout 1, and is asserted by the test: the coordinator's and the discoverer's initial parameters (bit-identical, because both are constructed **before** the discriminators), the skill-boundary mask `[500, 32]` and its sha256, the boundary count, `M = 1600`, and the transition, episode and optimizer-step counts. What differs from step 1 of rollout 1: the sampled team and agent skills, hence the actions, the trajectory and the returns. The mechanism, verified directly in `tests/flexible_skill_duration_e1_test.py::test_d0_d1_construction_parity_and_rng_divergence`: the D1 discriminators take one extra input column (`LayerNorm(120)` / `Linear(120,256)` against `LayerNorm(119)` / `Linear(119,256)`, and `105` against `104`), so their initialisation consumes a different number of draws and **the global torch RNG state after `HMASDAgent.__init__` differs between the arms**; every later sample diverges. Removing the divergence would require reordering construction or re-seeding inside `hmasd/`, which the assignment forbids. Because of this the two arms at one seed share the environment seeds and the learner seed but **not** the realised trajectory; they remain a matched pair in the sense the study uses (same seeds, same lanes, same schedule), not in the stronger sense §2 asserts |
| **D3** | **The 90-minute-per-run condition of contract §2 was not met.** Runs took 101–137 minutes (§4). The reviewer's `num_envs = 32` decision rested on a 206 s single-process rate; two concurrent 4-thread processes on this 16-logical-core machine ran at 1.5–1.9× that per-rollout cost. No run was stopped for it and `num_envs` was not reduced, because the concurrency was itself the executing instruction |
| **D4** | **Execution order.** Contract §2 prescribes D0 s1, D1 s1, D0 s2, … strictly sequentially. The executing instruction prescribes the two arms of one seed **concurrently** as a matched pair, pairs in seed order, never more than two runs at once. The instruction was followed. The contract's property that a stop after any pair leaves matched seeds is preserved |
| **D5** | **The bit-identity check named in the executing instruction could not be run against E0.** It asks that the D0 arm's first rollout be bit-identical to an E0 `d0` run at the same seed and lanes. **No E0 `d0` run exists at 32 lanes**: E0 ran both arms at 16 lanes (E0 deviation D1), and its only 32-lane runs are four two-rollout `off`-arm timing runs. `tests/flexible_skill_duration_e1_test.py::test_no_e0_d0_run_exists_at_32_lanes` asserts that absence from the E0 manifests rather than assuming it. Contract §2's fallback was used instead: the two E1 arms' rollout 1 compared to each other, with the outcome recorded as D2 above |
| **D6** | **`manifest.json` and `summary.json` are augmented after the run.** E0's `_execute` writes both and was not edited, so the E1-specific fields the executing instruction requires (launch commit `6fba1c7ba`, worktree branch and branch sha, `num_envs`, thread count, probe-set digest, the derived §3 series) are merged into both files afterwards under a namespaced `e1` key, and written standalone as `e1_probe_summary.json`. No field E0 wrote was altered |
| **D7** | **E0's `d2_metrics_delta` artifact is inherited.** E0 result deviation D4 records that this field is meaningless because `clear_buffers` resets `get_d2_metrics()` each rollout. The E0 runner was not edited, so the field is present in every E1 `metrics.jsonl` and is equally meaningless. The raw `d2_metrics` dict beside it is the correct per-rollout value. Ignore the delta |
| **D8** | **Elapsed study clock.** The study spanned two interruptions of the executing session (API rate limits), with the machine idle for about 6.05 hours between the seed-2 and seed-3 pairs. Machine-occupied time is 7.28 h, inside the 8-hour cap; elapsed clock from first launch to last completion is 13.37 h. No run was affected — each of the six ran to completion in one uninterrupted process |
| **D9** | **The machine was shared during the seed-2 pair.** Two foreign single-thread python processes (another session's work) ran from about 02:09Z to about 03:20Z. They lengthened the seed-2 pair's wall time; they cannot change its numbers, which are deterministic given the seed |
| **D10** | **`scripts/hmasd_run.py prepare/execute/reconcile` not used**, as at E0 (E0 contract §7, spec §11.4). The runner writes its own manifest with the same facts |
| **D11** | **Arithmetic note on the window.** Contract §4 item 1 justifies `R = 20` as giving "ten checkpoints" in the `r >= R/2` window. `r >= ceil(20/2) = 10` selects **eleven** rollouts (10…20) and therefore ten adjacent-rollout agreement values and ten adjacent-rollout drift values. The window used is `r >= 10`; both counts are stated wherever the window appears |

---

## 9. Could not verify

- **Nothing about which arm is better.** Contract §1's non-goals forbid it, and the numbers would
  not support it: the D1-minus-D0 final evaluation return is −21.09, −8.21, −3.17 across the three
  seeds, i.e. always negative but spanning a range comparable to each arm's own across-seed range
  (D0 15.53, D1 15.46). §7.4 applies the contract's rule and returns "a difference outside the
  across-seed range of both arms" — that is the rule's wording, **not** a finding that D1 hurts
  return. Four evaluations per run on three seeds of a learner 320,000 transitions old carry no
  ordering, exactly as E0 §10 records.
- **A seed-count or variance claim.** Three seeds is what spec §5.2 asks for to see "direction and
  obvious instability" and no more. Every "across-seed spread" in §6 and §7 is the max-minus-min of
  three numbers; it is a range, not an estimate of a standard deviation.
- **Whether the age input is *used*.** §6.4 reports the age column's share of the first-layer
  weight norm. In all three D1 seeds it stays within 0.0006 of the value it would have if every
  input column carried the same norm (`1/sqrt(120) = 0.091287` team, `1/sqrt(105) = 0.097590`
  individual): the team share moves 0.09122–0.09137 → 0.09126–0.09185, and the individual share
  *falls* from about 0.0974 to 0.0929–0.0946. This is a norm ratio on one layer, which is a cheap
  indicator and not a causal statement; it does not prove the age is ignored, and a gradient- or
  ablation-based test would be a different measurement.
- **That the probe agent reproduces the learner's own discriminator forward pass.** The probe path
  calls the same `_team_discriminator_logits` / `_individual_discriminator_logits` /
  `skill_coordinator.get_value` methods with the same normalisation flags as
  `_compute_intrinsic_rewards_batch` and `assign_skills`, on a `state_dict`-synced copy. That is an
  argument from construction; no test compares the two numerically on the same input.
- **Evaluation and measurement isolation is argued, not proved.** Inherited from E0 §10: the
  evaluator and the probe measurer are second `HMASDAgent` instances synced by `state_dict` plus
  deep copies of `obs_norm`, `state_norm` and both value normalisers, constructed and run inside a
  saved/restored RNG state. If the learner carried any other state affecting the forward pass, the
  measurement would silently use a stale value. No test in the repo covers this.
- **The probe set's provenance against E1's configuration.** It was collected from the E0 `off`
  arm at seed 1 **at 16 lanes** and before the throughput refactor. It is frozen input, so E1's
  lane count cannot change it; but it is not a sample from E1's own state distribution, and the two
  arms' probe accuracies are therefore accuracies on a fixed external set, not on their own data.
- **Whether the probe accuracies mean anything at this scale.** Both arms sit between 0.11 and 0.24
  on a 6-way team label (chance 0.167) and between 0.15 and 0.20 on a 6-way individual label. Most
  of the reported gains are of the same order as the distance from chance. This document records
  the numbers and applies the contract's rule to them; it does not claim the discriminators have
  learned anything.
- **Checkpoint restore was not exercised.** `checkpoint_final.pt` was written by `agent.save_model`
  in each of the six runs and never loaded back.
- **No CUDA comparison** is possible: neither declared conda env has CUDA (`CLAUDE.md`).
- **The quarantined attempt's 12 rollouts.** They are not compared with the `_r2` rerun's first 12,
  are not inspected, and are not used to argue that the rerun reproduces them. Spec §6.2 forbids
  salvage, and that includes salvage-as-a-cross-check.

---

## 10. Interpretation boundary (contract §7)

Bounded to scenario 1 with six UAVs and fifty users, fixed `k = 10`, `c = c_Z = inf`,
`k_max = k_Z = 10`, one machine, three seeds, `R = 20` rollouts at 32 lanes (320,000 transitions
per run), the frozen 1,536-probe seed-1 set collected under `off` at 16 lanes, and the measurements
of contract §3 as computed in §1. It says what the explicit age input did to label stability, probe
accuracy and coordinator value drift at fixed `k` under this budget, and what the contract's own §5
rule says about the prediction on record. It says nothing about D2, about finite `c`, about the
corridor, about which arm is better, or about any `k` other than 10.

Everything in §6 and §7 beyond the §5 rule — in particular the direction of the label-agreement
difference (team up, individual down, in all three seeds) and the uniformly larger coordinator
value drift under D1 — is recorded under contract §5's last clause as **an observation for E2's
design, not a result**.
