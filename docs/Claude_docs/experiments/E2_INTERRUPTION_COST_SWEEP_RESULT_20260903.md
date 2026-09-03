# E2 result — D2 interruption-cost sweep against the fixed-`k` sweep on the homogeneous relay corridor

Executed 2026-09-03 by Claude Code (Fable 5.1) against the launch contract
`E2_INTERRUPTION_COST_SWEEP_20260903.md`. **Claim ceiling B — EXPLORE.** Nothing here is a
claim that one arm is better; the returns are counters carried with the E0/E1 caveat, and the
only verdict offered is the contract's own §5 reading rule applied to its own numbers.

Runner `scripts/run_flexible_skill_duration_e2.py`; study-level aggregator
`scripts/run_flexible_skill_duration_e2_aggregate.py`; launch queue
`scripts/run_flexible_skill_duration_e2_queue.py`; test
`tests/flexible_skill_duration_e2_test.py`. `git check-ignore` returns nothing for all four,
i.e. they are tracked. Interpreter for every command:
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.

| Fact | Value |
| --- | --- |
| Launch commit (recorded in every manifest as `launch_commit`) | `92243f413` ("Add the E2 interruption-cost-sweep runner, aggregator, queue and test") |
| Full sha | `92243f413f22100cb19757687de33abda4b519d1` |
| Worktree branch | `worktree-agent-a88287f2315bb99a0`, forked from `main` at `036fe4eff` |
| `code_sha` in the manifests | the same `92243f413…`; `code_dirty` `false` in every run |
| Launch condition (contract §1) | met: P4 reviewed and integrated (review Part XII), predictions on record (plan §11, 2026-09-03) |
| Machine | `Jacob`, Windows-10-10.0.26200-SP0, AMD64 Family 25 Model 117 Stepping 2 (AMD), 16 logical CPUs |
| Interpreter / libraries | Python 3.10.20, torch 2.7.0+cpu, numpy 1.26.3, device `cpu`, `torch.set_num_threads(4)` |
| Study root (gitignored) | `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E2_20260903/` |
| Study-level output | `E2_summary.json` at the study root |

<!-- PLACEHOLDER: the §5 reading, up front -->

---

## 1. Question, claim ceiling, predictions on record (contract §1)

Question, quoted: *on the homogeneous relay corridor (both regions at the same event hazard),
does policy-based interruption (D2) at some finite cost `c` reach the return of the best fixed
skill duration `k`, and do its interruptions behave as an event-driven boundary (segment length
increasing in `c`, interruptions concentrated at event flags) rather than as noise in the
coordinator's log-probability gap?*

Predictions on record (plan §11, 2026-09-03), unchanged by this document:

* **Owner** — mechanism A, event-driven interruption, some finite `c` reaches or exceeds the
  best fixed `k`.
* **Reviewer** — mechanism A as well, with the best `c` between 0.5 and 1.0 and the fraction of
  interruptions at event flags above one half at that `c`. The reviewer's two numerical clauses
  are scored separately in §7.3.

Non-goals, quoted and observed: no heterogeneous hazard (E3), no random event durations (E4), no
age feature (E1 settled it), no team-level asynchrony study (E5), no claim about the UAV host
(E2b), no seed-count claim beyond direction and obvious instability.

## 2. Choices the contract left open

The contract is the whole authority. Where it is silent the reading recorded here is the one that
was used; each is stated so a reader can disagree with it explicitly. Nothing in this section is a
deviation — the deviations are §8.

| Point | Choice | Why |
| --- | --- | --- |
| How the runner "imports the E0 runner's manifest, preflight and summary conventions and the corridor driver; does not copy the E0 loop" (contract §6) | `scripts/run_flexible_skill_duration_e2.py` imports `scripts/run_flexible_skill_duration_e0.py` and uses its `_jsonable`, `_git`, `_preserve_rng`, `_sha256_arrays`, `_utc_now`, `_capture_theta0`, `_exposure_line`, `_StepCounter`, `run_preflight`, `CONFIG_DUMP_FIELDS` and `LOSS_FIELDS`; the rollout loop is `RelayCorridorHMASDDriver.run_rollout` from `envs/relay_corridor/hmasd_driver.py`, called unchanged. The E0 file was **not** edited | contract §6. The E0 loop is a UAV-scenario loop and would be wrong here; ADR 02 fixes the corridor loop |
| How the per-step quantities the driver does not return are captured | three **bound methods on instances the runner owns** are wrapped: `driver.adapter.step` (to read `agent._d2_last_step`'s `g_agents` / `g_team` / `agent_cause` / `team_cause` / `sampled_mask` at the same step, and the host's `info['change_flag']`), `driver.agent.get_d2_metrics` (to snapshot the raw segment-length lists before `clear_buffers` drops them), and `driver.agent.update` (to keep its returned loss dict). No module under `hmasd/` or `envs/` is edited or monkeypatched at class level | contract §3 asks for gaps at every step, segment-length deciles and event alignment; `run_rollout` returns none of the three. The alternative was editing `envs/relay_corridor/hmasd_driver.py`, which the assignment forbids |
| Arm ids and directory names | `d0_k1 … d0_k40` and `d2_c0p25`, `d2_c0p5`, `d2_c1p0`, `d2_c2p0` (`.` → `p` for directory safety); run directories `<arm>_seed<S>` | contract §6 names the pattern, not the arm ids |
| Arm configuration | every arm `policy_interruption_mode="d2"`, `interruption_delta=1`, `age_feature="off"`. D0: `interruption_cost_c = interruption_cost_c_Z = inf`, `skill_cap_k_max = team_cap_k_Z = k`. D2: `interruption_cost_c = interruption_cost_c_Z = c`, `skill_cap_k_max = team_cap_k_Z = 40` | contract §2. `age_feature="off"` is review Part XI.2: E1 settled the age input and it is not carried into E2 |
| `config.k` on the corridor learner | set to the arm's `skill_cap_k_max` | in `d2` mode the boundaries come from `k_max` / `k_Z`, never from `config.k`; setting it to `k_max` keeps `off_boundary_masks` (which the driver records but does not act on) meaningful |
| Host master seed and learner seed | both equal `--seed` (1 or 2), so all nine arms at one seed share the host's tapes and the learner's initial parameters | contract §2's matching clause: "all arms at a seed share the host's master seed" |
| Thread count | `RelayCorridorHMASDDriver.__init__` pins `torch.set_num_threads(1)`; the runner restores `torch.set_num_threads(4)` immediately after construction, so every rollout and evaluation runs at four threads | the executing instruction. Recorded because the driver's own default differs |
| The learner config's class | rebound from the function-local `_CorridorConfig` (built inside `build_corridor_learner_config`) to a module-level `E2CorridorConfig(Config)` immediately after construction | `agent.save_model` pickles `self.config`; a class defined in a function body cannot be pickled, so without this no checkpoint could be written. Both classes are empty subclasses of `config_1.Config`, so no attribute, default or behaviour changes — only the pickle path |
| "Return", the evaluation quantity | the **mean per-step shared reward over one 400-step episode**, in `[0, Δ] = [0, 0.4]` | it is then on exactly the same scale as the references, which are Δ-weighted mean per-step service fractions (`_policy_return` = `service.sum() / H`). Any other choice would make "the gap to `J_switch`" meaningless |
| "the event-alignment fraction … within one step after the agent's region flag flipped" | the two-step window `{t_flip, t_flip + 1}`: an interruption of agent `i` at step `t` is aligned when `change_flag[t, region(i)]` is up **or** `change_flag[t-1, region(i)]` was up. The host raises the flag at the step the event is realised *into*, so this is "at the flip, or one step later". The one-step reading (`t` only) is recorded beside it as `aligned_fraction_strict`, and never used for the §5 branch | contract §3 item 2. The wording admits both; the two-step reading is the literal "within one step after" |
| Which interruptions the alignment fraction is taken over | **all** sampled positions (every `i ∈ S_t`, whatever the boundary cause), which is what "interruptions" says literally. The restriction to gap-caused positions (`cause ∈ {gap, team_gap}`) is recorded beside it as `event_alignment_gap_caused_only` and is the more favourable reading for mechanism A | contract §3 item 2 and §5 say "interruptions", not "gap-caused interruptions". Both are reported; §5 is applied to the literal one |
| Segment lengths | the agent-level completed-segment lengths the learner itself records (`agent.d2_metrics['segment_lengths_agent']`), snapshotted per rollout before `clear_buffers`; team segments recorded beside them | contract §3 item 2, "mean and distribution (deciles) of completed segment lengths per agent" |
| "deciles" | the nine quantiles `0.1 … 0.9` (`numpy.quantile`, linear interpolation), reported with count, mean, std, min and max | the word admits 9 or 11 cut points; nine is the standard reading and both endpoints are reported separately |
| Gap deciles | over **every** step, every lane and every agent of the rollout, excluding the reset steps where the coordinator is not evaluated and the agent leaves `g_i = NaN` | contract §3 item 3, "at every step (not only at interruptions)". The reset steps carry no gap at all; they are excluded rather than imputed |
| "fraction of segments closed by the cap `k_max`" | the share of sampled positions whose recorded boundary cause is `cap` or `team_cap`; the gap share (`gap` / `team_gap`) and the reset share are reported beside it | contract §3 item 2. Causes are read from the agent's own `D2_CAUSE_*` codes, never redefined |
| Team switch rate | the count of `team_cause == team_gap` per environment-step, i.e. the `g_Z ≥ c_Z` firings only; the `team_cap` and `reset` team decisions are counted separately | contract §3 item 2, "the team switch rate (`g_Z ≥ c_Z` firings)" |
| "Return by regime" | the 4,096 declared tapes' per-episode **event counts** are a function of the tape alone (one Bernoulli draw per region per transition against a constant hazard), so the split is identical for every arm, seed and checkpoint. Episodes with event count `≤` the median of the evaluated set are the low regime, `>` the median the high regime | contract §3 item 4. Ties at the median go to the low regime, which is stated because the counts are integers and the median is 16 |
| Evaluation mechanism | a **second** `HMASDAgent` (the E0 mechanism), built inside `e0._preserve_rng()`, `state_dict`-synced from the learner with deep-copied `obs_norm`, `state_norm` and both value normalisers before every evaluation, held in `train(False)`, stepped with `deterministic=True` (greedy coordinator, mean low-level action; the host decodes the role by `argmax`). Every evaluation runs inside `_preserve_rng` | contract §3, last paragraph |
| Evaluation lane bookkeeping | the evaluator runs the 400-step episode in chunks of 512 lanes; between chunks it calls `agent.clear_buffers()` and `agent.reset_env_state(lane)` for every lane, and installs the chunk's episode ids on the adapter before `reset()` | the corridor host is one batched object with keyed per-episode streams, so a chunk is exactly the same set of episodes it would be inside one 4,096-lane batch |
| `scripts/hmasd_run.py` not used | as at E0 and E1 (E0 contract §7, spec §11.4) | the runner writes its own manifest with the same facts |
| Study-level `E2_summary.json` | written by a separate script from the finished run directories; it measures nothing and only differences what the runs recorded | contract §6 lists it as an output without saying which program writes it |
| Readings inside §5's rule | five, each named in §7.1 and carried in `E2_summary.json` under `readings` | §5's wording admits more than one in five places |

## 3. Configuration actually run

### 3.1 Host point (contract §2)

| Field | Value |
| --- | --- |
| Host | `envs/relay_corridor` (`RelayCorridorHost` → `RelayCorridorAdapter` → `RelayCorridorHMASDDriver`) |
| `n_agents = N` / `n_roles = K` / `n_zones = Z` / `n_regions` / `horizon = H` | 6 / 2 / 4 / 2 / 400 |
| `delta = Δ` | 0.4 |
| `event_process` | `bernoulli` |
| **`lambda_regions`** | **(0.02, 0.02)** — homogeneous, the small row's second-region rate for both |
| `rho`, `c_probe`, `e5_coupling_enabled` | 0.0, 0.0, `false` |
| `role_decode` | `argmax` |
| `D0_k_set` | (1, 2, 5, 20, 40) |
| ADR 02 invariant 6 (`H ≥ 10·max(D0_k_set)`) | `accepted: true`, 400 ≥ 400, 10 segments at the largest `k` |
| Agents per region / zone map | `region_of_agent = [0,0,0,1,1,1]`, `zone_of_agent = [0,1,0,2,3,2]`, region weights (0.5, 0.5) |

### 3.2 Learner (contract §2)

| Field | Value |
| --- | --- |
| Route | HMASD base route through `RelayCorridorHMASDDriver` at the launch commit |
| `policy_interruption_mode` / `interruption_delta` / `age_feature` | `d2` / 1 / `off` (every arm) |
| `num_envs` / `rollout_length` / `episode_length` | 16 / 400 / 400 (one episode per lane per rollout) |
| `n_z` / `n_Z` / `action_dim` / `action_space_type` | 2 / 6 / 2 / `continuous` (team code present and inert, ADR 02) |
| `state_dim` / `obs_dim` / `n_agents` | 77 / 19 / 6 |
| `gamma` / `gae_lambda` / `ppo_epochs` / `num_mini_batch` | 0.99 / 0.95 / 15 / 4 |
| `lr_coordinator` / `lr_discoverer_actor` / `lr_discoverer_critic` / `lr_discriminator` | 1e-4 each |
| `use_valuenorm` / `use_obsnorm` / `use_statenorm` | `True` / `False` / `False` |
| `hidden_size` / `embedding_dim` | 256 / 256 |
| `torch.set_num_threads` | 4 |
| `R` | 20 rollouts (320,000 transitions per run at 16 lanes) |

### 3.3 The nine arms

| Arm | family | `interruption_cost_c` = `c_Z` | `skill_cap_k_max` = `k_Z` |
| --- | --- | --- | --- |
| `d0_k1` | D0 | `inf` | 1 |
| `d0_k2` | D0 | `inf` | 2 |
| `d0_k5` | D0 | `inf` | 5 |
| `d0_k20` | D0 | `inf` | 20 |
| `d0_k40` | D0 | `inf` | 40 |
| `d2_c0p25` | D2 | 0.25 | 40 |
| `d2_c0p5` | D2 | 0.5 | 40 |
| `d2_c1p0` | D2 | 1.0 | 40 |
| `d2_c2p0` | D2 | 2.0 | 40 |

Launch order (contract §2), realised by `scripts/run_flexible_skill_duration_e2_queue.py`:
`d0_k40` seed 1, `d0_k40` seed 2, `d2_c1p0` seed 1, `d2_c1p0` seed 2, then `d0_k1`, `d0_k2`,
`d0_k5`, `d0_k20`, then `d2_c0p25`, `d2_c0p5`, `d2_c2p0`, each seed 1 before seed 2; two
processes at a time.

Command form (the eighteen runs differ only in `--arm` and `--seed`):

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_flexible_skill_duration_e2.py \
  --arm <arm> --seed <1|2> --rollouts 20 --num-envs 16 --threads 4 \
  --output-root <study root> --launch-commit 92243f413 \
  --eval-interval 5 --eval-tape-set 4096 --eval-episodes 2048 \
  --eval-intermediate-episodes 512 --eval-chunk 512 --eval-master-seed 770001
```

## 4. The exact references (contract §2, §3 item 1)

Computed by `envs.relay_corridor.references.enumerate_references` on the §3.1 host point
**before the first rollout** and recorded verbatim in every manifest (`manifest.references`) and
every `summary.json`. They are references, not outcomes.

| Reference | Value |
| --- | --- |
| `J_switch` (switching oracle) | `0.3920199999999997` |
| `J_greedy` | `0.3920199999999997` — exactly `J_switch`; at `K = 2` the change flag plus the lagged cue identify the only different latent (ADR 02 invariant 8) |
| `J_fixed_k[1]` | `0.001` |
| `J_fixed_k[2]` | `0.19699999999999984` |
| `J_fixed_k[5]` | `0.3053168127999998` |
| **`J_fixed_k[20]`** | **`0.3133920282449043`** |
| `J_fixed_k[40]` | `0.26814979802452366` |
| `k*` (best fixed `k`) | **20** |
| `J_open_best` (best open-loop map × period) | `0.1566960141224521`, at zone-role map `(0,0,0,0)` with period 20, over 96 candidates |
| `m = J_switch − J_open_best` | `0.2353239858775476` (registered and reported; not an E2 gate) |
| `m_dur = J_switch − max_k J_k` | `0.0786279717550954` (the acceptance scale) |

Margins the study reads against:

| Quantity | Value |
| --- | --- |
| `J_switch − J_fixed_k[1]` | `0.3910199999999997` |
| `J_switch − J_fixed_k[2]` | `0.19501999999999986` |
| `J_switch − J_fixed_k[5]` | `0.0867031871999999` |
| `J_switch − J_fixed_k[20]` = `m_dur` | `0.0786279717550954` |
| `J_switch − J_fixed_k[40]` | `0.12387020197547604` |
| `J_fixed_k[20] − J_fixed_k[5]` (the tightest gap in the `k` grid) | `0.0080752154449045` |
| `J_fixed_k[20] − J_fixed_k[40]` | `0.04524223022038064` |
| Reference ordering of `J_fixed_k`, best first | `20, 5, 40, 2, 1` |

The reference ordering is what the §4/§5 D0 sanity check compares the learner's `k` ordering
against.

### 4.1 The matched evaluation tapes

| Field | Value |
| --- | --- |
| Declared tape set | episode ids `0..4095` at evaluation master seed `770001` |
| `content_sha256` | `9844b04cfe01eda3cb1d1c102b4e8b44631994eadb99f594c7fcca7f0134c5b1` |
| Digest recipe | for each ascending chunk of 512 episode ids, E0's `_sha256_arrays` over the host's four keyed tape arrays (`theta0`, `event_u`, `switch_u`, `role0`); the chunk hex digests are then fed, in order, into one outer sha256 |
| Recomputed | in **every** run, before the learner is built; identical in all of them |
| Per-episode event count (both regions, `H − 1 = 399` transitions) | median 16, mean 15.90087890625, min 3, max 33 |
| Tapes actually evaluated | the first 2,048 at the final checkpoint, the first 512 at rollouts 5, 10 and 15 (deviation **D1**, §8) |

Because the corridor's streams are keyed by `(master seed, episode id)` alone, the same episode
id is the same episode in every arm, every seed and every checkpoint, and a prefix of the set is
still a matched set.

## 5. Budget, timing basis and stop rule (contract §4)

### 5.1 The timing basis

Review Part XII.1 item 5 requires the wall-clock estimate to come from E2's own first rollout,
not from the P3 table. It does. Everything below was measured on this machine at the launch
commit, with two concurrent four-thread processes, 16 lanes and `H = 400`.

| Measurement | Value | When |
| --- | --- | --- |
| Corridor rollout + update, single process | 64.2 s | pre-launch probe |
| Corridor rollout + update, two concurrent processes | 78 s | pre-launch probe (concurrency factor **1.21**) |
| Corridor rollout + update, two concurrent, **the runner as launched** | 86.4 / 85.6 s (`d0_k40` seed 1, rollouts 1–2) and 84.7 / 83.5 s (seed 2) | first pair |
| Evaluation, per episode, two concurrent | 0.46 s | pre-launch probe at 512 lanes |
| Evaluation, per episode, measured in the run | **0.460 s** — 235.6 s for 512 tapes (`d0_k40` seed 1, rollout 5) and 234.8 s (seed 2) | first pair |

The runner's per-rollout figure is about 10% above the probe's because the probe did not carry
the per-step gap, cause and change-flag capture or the per-rollout decile accounting.

### 5.2 Why the contract's evaluation size does not fit, measured

At contract §3's schedule — 4,096 matched tapes every 5 rollouts, four evaluations per run —
one run costs 26 min of training plus 4 × 31.5 min of evaluation = 152 min, so 18 runs at two
concurrent (9 slots) is **22.8 h**, about 2.9× the 8-hour cap (advancement plan §7 decision 3).

Contract §4.4's remedy does not reach it. §4.4 drops runs, not evaluation size: at the
contract's evaluation size the 14-run version is 17.7 h, and only 6 of the 18 runs fit inside
8 h. The binding constraint is the tape count, not the run count.

The cause is measured, not inferred. `cProfile` on the evaluation step at 512 lanes puts 93% of
the time inside `hmasd/networks.py::SkillCoordinator.evaluate_held_batch` — the teacher-forced
transformer pass D2 runs **every step** at `delta = 1`, in every arm including the D0 arms with
`c = inf` — with `torch._C._nn.linear` and `scaled_dot_product_attention` the two largest leaves.
Cost per lane-step is flat from batch 256 to 1024 (0.83, 0.85, 0.83 ms), so batching does not
help, and nothing the runner may touch changes it: fixing it would mean editing `hmasd/`, which
the assignment forbids.

The resolution consequence is small. Deviation **D1** (§8) evaluates the final checkpoint on
2,048 tapes and the intermediate checkpoints on 512.

The per-episode return standard deviation over the matched tapes, measured in the study's first
evaluations, is **0.0302** (`d0_k40` seed 1) and **0.0345** (seed 2). Taking the larger:

| Evaluation size | standard error of the mean | tightest reference gap `J_20 − J_5 = 0.0080752` in standard errors |
| --- | --- | --- |
| 4,096 (contract) | 0.000539 | 15.0 |
| **2,048 (final checkpoints here)** | **0.000762** | **10.6** |
| **512 (intermediate checkpoints here)** | **0.001525** | **5.3** |

ADR 02 invariant 5 asks for `m_dur ≥ 3·σ_Δ/√E_eval`. `m_dur = 0.0786280`; bounding the paired
per-episode difference by `σ_Δ ≤ √2 · 0.0345 = 0.0488` (the two arms treated as independent,
which is the pessimistic direction — matched tapes make the true paired sd smaller), the
requirement at 2,048 tapes is `3 × 0.0488 / 45.25 = 0.00324`, which `m_dur` exceeds by a factor
of 24. It is also satisfied at 512 (`0.00647`, a factor of 12). **Observation, not inference:**
no comparison this study makes is limited by the evaluation size at either checkpoint size; what
limits §5 is `s`, the across-seed range of two seeds, which §7 shows is two orders of magnitude
larger.

### 5.3 Stop rules

* **Per run** (contract §4.3): `R = 20` rollouts, or the first non-finite loss or return. Any
  instrumentation failure quarantines the run — no interpretation, no resume, no salvage; one
  fresh re-run under a new name; a second failure reports the arm-seed as not run. The runner
  writes a `QUARANTINED` marker and returns a non-zero exit code on any exception and on any
  incomplete rollout count.
* **Per study** (contract §4.4): all 18 runs, or the 8-hour machine-time cap, or the owner's
  stop. The cap was projected to be breached by 5.6% after the first rollout; the decision on
  record was to keep all 18 runs (deviation **D2**, §8).

<!-- FILL: realised machine time -->


<!-- PLACEHOLDER: 6. The eighteen runs -->

<!-- PLACEHOLDER: 7. The contract §5 reading rule, applied verbatim -->

## 8. Deviations, each named

| # | Deviation | Status |
| --- | --- | --- |
| **D1** | **Contract §3 item 1's evaluation size was reduced: the final checkpoint is evaluated on 2,048 matched tapes and the intermediate checkpoints (rollouts 5, 10, 15) on 512, instead of 4,096 at every checkpoint.** The §3.1 *schedule* — evaluation every 5 rollouts — is unchanged, as is the deterministic policy, the second-agent mechanism and the matching property: the declared tape set is episode ids `0..4095` at evaluation master seed `770001`, its content digest `9844b04cfe01eda3cb1d1c102b4e8b44631994eadb99f594c7fcca7f0134c5b1` is recomputed and recorded in every run, and what is evaluated is a **prefix** of that set, so every arm, seed and checkpoint still sees the same episodes. Measured basis (§5.1, §5.2): a rollout costs 85.5 s at two concurrent processes and an evaluation episode 0.46 s, so the contract's 4 × 4,096 schedule costs 152 min per run and **22.8 h** for the study against an 8-hour cap; §4.4's drop rule reduces runs, not evaluation size, and cannot reach it (only 6 of 18 runs fit). The cause is measured: 93% of the evaluation step is the coordinator's teacher-forced transformer pass, which D2 runs every step at `delta = 1` in every arm, and its cost per lane-step is flat in the batch size, so no runner-side change helps and the fix would require editing `hmasd/`. **Decided before launch, not after seeing any result**, and approved on the record as a pre-launch contract deviation (ADR review XII.4) with the conditions applied here: the intermediate checkpoints are reported as trajectory reads only and are never a §5 deciding quantity; the 4,096-tape digest is kept and every final checkpoint is retained, so a later contract can evaluate the full declared set on the saved checkpoints |
| **D2** | **The 8-hour machine-time cap (advancement plan §7 decision 3) was projected to be exceeded and the study was run in full anyway.** After the first rollout the projection was 56.3 min per run — 28.5 min of training (20 × 85.5 s) plus 27.5 min of evaluation (3,584 episodes × 0.46 s) — giving 9 slots × 56.3 min = **8.45 h**, a 5.6% overrun. Contract §4.4's remedy (drop seed 2 of the outer arms `k ∈ {1, 2}`, `c ∈ {0.25, 2.0}`, taking the study to 14 runs and ~6.6 h) was weighed and **not** applied: it would remove seed 2 from two of the four `c` arms, which makes §5's mechanism-A clause "the mean segment length is non-decreasing in `c` across the four `c` arms **in both seeds**" unevaluable as written, and would cost the reviewer's numerical clauses a seed at two of the four `c` values — a larger loss than the 27 minutes it saves. The decision on record (ADR review XII.5) keeps all 18 runs, notes that the overrun sits inside the 8–9% between-session timing drift P4 measured on identical code the same day, and requires the projection to be re-checked after every pair with an escalation threshold of 9.0 h. <!-- FILL: realised machine time and whether any re-projection crossed 9.0 h --> |
| **D3** | **`RelayCorridorHMASDDriver.__init__` pins `torch.set_num_threads(1)`; the runner restores 4 immediately after construction.** The contract runs at four threads (executing instruction, and E0/E1's setting). The driver's own default is not a contract quantity and no arm differs from any other in this respect, so it does not affect a comparison; it is recorded because the driver file says one thing and every manifest records `torch_num_threads: 4` |
| **D4** | **The learner config object's class is rebound after construction.** `build_corridor_learner_config` builds its config from a class defined **inside the function body**, which `torch.save` cannot pickle, and `HMASDAgent.save_model` pickles `self.config`; without the rebinding to the module-level `E2CorridorConfig(Config)` no checkpoint could be written at all. Both classes are empty subclasses of `config_1.Config`; no attribute, default or behaviour changes, only the pickle path. `envs/relay_corridor/hmasd_driver.py` was **not** edited |
| **D5** | **Three bound methods on runner-owned instances are wrapped to capture contract §3 quantities the driver does not return.** `adapter.step` (per-step `g_i` / `g_Z`, sampled mask, boundary causes, host change flags), `agent.get_d2_metrics` (the raw completed-segment lists, which `clear_buffers` drops), `agent.update` (its loss dict). These are instance attributes; the imported modules are untouched, exactly as E0's `_StepCounter` treats the optimizers. Without them contract §3 items 2 and 3 could not be measured at all without editing `envs/relay_corridor/hmasd_driver.py` |
| **D6** | **`scripts/hmasd_run.py prepare/execute/reconcile` not used**, as at E0 and E1 (E0 contract §7, spec §11.4). The runner writes its own manifest with the same facts |
| **D7** | **The study ran in a git worktree, not the main tree**, so the study root is `…/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E2_20260903/` rather than `C:/Projects/HMASD/temp/…`. `temp/**` is gitignored in both, so no run output was ever going to enter Git; the path is recorded so the directories can be found |
<!-- FILL: further deviations discovered during the runs -->


## 9. Could not verify

- **Nothing about which arm is better as a matter of algorithm design.** Contract §1's non-goals
  forbid it and the budget would not support it: two seeds, `R = 20` rollouts, 320,000
  transitions per run, four evaluations. Everything in §6 and §7 is the contract's own rule
  applied to its own numbers.
- **A seed-count or variance claim.** Two seeds is what plan §1 asks for — "direction and
  obvious instability" — and no more. Every "across-seed range" in §7 is `max − min` of two
  numbers; it is a range, not an estimate of a standard deviation, and `s` in §5's rule is
  therefore a very coarse scale.
- **The full 4,096-tape evaluation.** Deviation D1 evaluates 2,048 tapes at the final checkpoint
  and 512 at the intermediate ones. The declared 4,096-tape set and its digest are recorded and
  every final checkpoint is retained, so the full set can be evaluated later, but it **was not**
  evaluated here and no number in this document is a 4,096-tape number.
- **That the intermediate checkpoints say anything about the reading.** They are 512-tape
  trajectory reads at a quarter of the final resolution and are excluded from §5 by
  construction; the rule is applied to the final checkpoint only.
- **Whether the observed `c` grid is well centred.** The grid `{0.25, 0.5, 1.0, 2.0}` came from
  **E0's** D0 gap histogram on UAV scenario 1 (agent gap median 0.22, q90 0.64, max 1.66 in
  logit units), not from the corridor. The corridor's own gap distribution is recorded per
  rollout (§6, `gaps.jsonl`) precisely so the next contract can re-centre it; whether this grid
  brackets the corridor's gap scale is an observation this study reports, not a design it
  validated in advance.
- **The event-alignment fraction's window.** "Within one step after the flag flipped" is read as
  the two-step window `{t_flip, t_flip + 1}`. The one-step reading is reported beside every
  value. No test or reference fixes which of the two the contract's author meant; the choice is
  recorded in §2 and the alternative is always visible.
- **Whether "interruptions" in §5 means all of them or only the gap-caused ones.** Both are
  reported everywhere; §5 is applied to the literal reading (all sampled positions). At the D0
  arms, and at any `c` large enough never to fire, the cap and the episode reset are the only
  causes, so the literal alignment fraction of such an arm is a statement about cap boundaries,
  not about the gap.
- **Evaluation isolation is argued, not proved.** Inherited from E0 §10 and E1 §9: the evaluator
  is a second `HMASDAgent` synced by `state_dict` plus deep copies of `obs_norm`, `state_norm`
  and both value normalisers, built and run inside a saved/restored RNG state. If the learner
  carried any other state affecting the forward pass, the evaluation would silently use a stale
  value. No test in the repo compares the two numerically on the same input.
- **Chunking the evaluation is argued from the host's keying, not measured.** The 400-step
  episodes are run in chunks of 512 lanes; the argument that a chunk sees exactly the episodes
  it would see inside one 4,096-lane batch rests on the host's `(master seed, episode id)`
  keying and ADR 02 invariant 2 (which `tests/relay_corridor_host_test.py` covers), not on a
  direct 4,096-lane comparison, which was never run.
- **Checkpoint restore was not exercised.** `checkpoint_final.pt` was written by
  `agent.save_model` in each completed run and never loaded back.
- **No CUDA comparison** is possible: neither declared conda env has CUDA (`CLAUDE.md`).
- **The corridor's `σ_Δ`.** ADR 02's resolution arithmetic is written for the *paired* per-episode
  return difference `σ_Δ`. What this study measures is each arm's own per-episode return
  standard deviation over the matched tapes; paired differences between arms on the same tape
  were not formed, so the ADR's exact quantity is reported as unmeasured and the per-arm sd is
  used as its stand-in wherever a standard error appears.
<!-- FILL: anything further the runs make unverifiable -->

## 10. Interpretation boundary (contract §7)

Bounded to the homogeneous relay corridor at `(λ₁, λ₂) = (0.02, 0.02)`, `Δ = 0.4`, `N = 6`,
`K = 2`, `Z = 4`, `H = 400`, the D0 grid `k ∈ {1, 2, 5, 20, 40}` and the D2 grid
`c ∈ {0.25, 0.5, 1.0, 2.0}` at `k_max = k_Z = 40`, two seeds, `R = 20` rollouts at 16 lanes,
one machine, the measurements of contract §3 as computed in §2, and the evaluation sizes of
deviation D1.

It says whether D2 at some finite `c` reached the best fixed `k` **on this host at this budget**,
and whether its interruptions were event-aligned in the sense §2 fixes. It says nothing about
heterogeneous hazards (E3), random event durations (E4), the UAV host (E2b), which `c` transfers,
or any `K` other than 2. Anything in §6 beyond what §5's rule reads is recorded under §5's last
clause as an observation for E3's design, not as a result.
