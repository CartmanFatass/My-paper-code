# energy_relay_benchmark — NOTES

Append-only notebook of the `energy_relay_benchmark` direction (Claude DM, WSL session).
Governance: `docs/project/OPERATING_CONSTITUTION.md`. Index: `docs/research/RESEARCH.md`.

## 2026-09-26 — Direction prepared: S7 energy-relay benchmark (prepare only, no launch)

### Owner instructions and status

- 2026-09-26: owner asked the Claude session to run the project as researcher, then clarified
  "prepare now, but don't start" pending a review document from Astral. This entry is the
  preparation: question, frozen host, arms, protocol, pre-registered endpoints, cost, code plan,
  node runbook, prepared index text and a Pro question draft. **Nothing is launched, no index
  row is published, no Pro question is sent.** The plan is revisable when the Astral review lands.
- Basis: `docs/Claude_docs/reviews/RESEARCH_PROGRAM_DIAGNOSIS_AND_RESET_20260926.md` §6
  (option C, track T1) and §8 DECIDE-2 (host freeze on S7), adopted here as the DM's working
  assumption; DECIDE-1 (venue class) stays with the owner and does not block preparation.

### Shared background used and contrary evidence carried forward

- RESEARCH background §3 (MARL adds joint behaviour and information structure) fixes the
  comparator logic: the flat central-snapshot actor (SET) is the same-information control for
  the hierarchy's coordinator, the local actor (LOCAL1) is the decentralised reference; §5
  (skills and asynchrony are organisational choices whose benefit needs evidence) is why HMASD
  enters as a candidate, not a premise; §6 (empirical work narrows explanations under stated
  conditions) is why exposure and seed variation are measured before any mechanism claim.
- `uav_service_auxiliary` B04–B11 (`docs/research/candidates/uav_service_auxiliary/NOTES.md`):
  the 180k-transition HMASD policies do not manage energy on their own. B07 at H3000: O-mode J
  −2,804/−2,656 (final panels of the B04/B05 policies) with cutoff events in 79/80 and depletion
  in 77/80 worlds; the fixed return shield F turns the same policies into J +977/+968, QoS/step
  .335/.334 versus .269/.286, zero risk events, at the price of service losses in some worlds.
  B09 (fresh N/A pair, F panel, seed 925031): initial policy 609.5 J, N 986.4, A 904.3; the
  N arm's own training episodes (O mode) stayed near −3,000 J for all 60 episodes. Feedback-aware
  training (A) did not help (A−N −82 J). Conclusion carried forward: at 180k transitions the
  learners have not started to solve the energy problem; a benchmark at that exposure compares
  untrained controllers.
- `agent_count_generalization` B16/B17 (S1): LOCAL1 ≈ HMASD at equal exposure (H6−LOCAL1 N8
  −.0146 J, N6 +.0266). The hierarchy's advantage is not established on the simpler host either.
- Historical S7 arm A (`baselines/scenario7_arm_a_2400000_metrics.json`): 2.4M steps, S3 stage,
  200 Wh, reward model v1, k=50, 8 evaluation episodes: median episode reward 74.4, mean QoS
  utility .143, 25 % return-violation episodes. Different stage, battery and reward version, so
  a caution about exposure (13× the current 180k), not a comparable score.

### Question

On a frozen energy-aware relay host with two capacity-1 chargers, what service–risk utility do
competent learned controllers reach as a function of exposure; does the actor's information
structure (local observation, central snapshot, skill-conditioned hierarchy with a central
coordinator) change it; and how far do they stay from the fixed return shield and from the
static layout witness? The direction's first study (B01) is the baseline suite with learning
curves; structured coordination candidates enter only where B01 shows a gap worth buying.

MARL structure of the host: eight homogeneous UAVs, one shared scalar reward; coupling through
SINR interference and multi-hop relay routing (service), through two charging slots of
capacity one (temporal resource contention: who leaves service when, and queueing at a slot),
and through RPGM user mobility (the layout that serves now goes stale). Decisions are
continuous per-UAV 4-vectors every 1 s step: velocity command (3) plus a dock-request bit
(`action[3] > 0.5`), see `envs/pettingzoo/relay/energy_aware.py` step. The strongest simpler
explanation for any HMASD gain is central information at decision time, which SET controls;
the strongest simpler explanation for no gain is exposure too small for energy management,
which the curves and the shield comparison expose directly.

### Host freeze (binding for this direction)

`Config("S7-S2")` built exactly as `experiments/candidates/uav_service_auxiliary/b01/native.py`
`make_config` (the B01–B11 host): 8 UAVs, 30 users, 1 ground BS, area 8000 m, RPGM users at
3 m/s, battery 160 Wh with initial ratio .75–1.0, two charging stations `capacity [1, 1]`
(service-anchored, randomised per world), charging 1000 W, capture radius 20 m, docking radius
160 m, episode H3000 at `time_step` 1 s, `k = 10`, comparison gate and physical feasibility check
off. Observation 365 per UAV, state 306, action 4, `tanh_gaussian` actions. Reward per step is the
native S7 reward `qos_satisfaction_ratio − 2·return_constraint_cost − cutoff_event_penalty −
depletion_event_penalty + graph_potential_delta` (asserted by B04 `metric_row`;
`lambda_return = 2.0` fixed). J = episode sum of that reward. No reward, observation or
environment edit belongs to this direction; a host change is a new direction.

### Arms of B01 (config switches of one agent, `hmasd/baselines.py`)

| Arm | Actor input | Critic input | Skills / clock | Switch | Notes |
| --- | --- | --- | --- | --- | --- |
| HMASD | local obs + team/individual skill embeddings | central state | n_Z = n_z = 6, coordinator every k = 10 steps, λ_D .05, λ_d .02 | `apply_algorithm_config(cfg, "hmasd")` + `ordinary_completed_segments = True` | identical learner to B09 N (B08 core contract) |
| SET | local obs + central state snapshot | central state | single constant skill, k = 10 restored | `"mappo"` switch, then `k = 10`, `use_central_snapshot_in_flat_actor = True`, `calculate_and_set_buffer_sizes()` | same-information flat control for the coordinator |
| LOCAL1 | local obs only | central state | single constant skill, k = 10 restored | `"mappo"` switch, then `k = 10`, snapshot off, buffer sizes recomputed | decentralised reference (ACG B16 recipe) |

Verified 2026-09-26 on CPU (this checkout): all three construct on the S7 dimensions and step
a batch; the MAPPO switch alone would set `k = rollout_length + 1 = 3001`, so k is restored as in
ACG `configuration.py`; the MAPPO arms must not carry `ordinary_completed_segments` (the agent
refuses it without high-level training); SET's deterministic action changes when only the
central state is perturbed (max |Δ| .0034), LOCAL1's does not. Parameter counts: HMASD actor
559,368 / critic 543,489 / coordinator 3,869,461; SET actor 1,384,712; LOCAL1 actor 556,808.
Shared across arms: PPO epochs 15, 4 minibatches, lr 1e-4, λ_l .005, value normalisation on,
observation/state normalisation off, same lanes, rollout length, seeds and evaluation. No
per-arm tuning; the hyperparameters are the S7 preset's, which were tuned for HMASD, and this
asymmetry is recorded as a limit of B01, not corrected by a search.

Non-learned references (not arms):

- **F shield** (B06 `apply_feedback`, production layout): a UAV whose legal return margin
  reaches 0 enters return mode and is commanded to the nearest station (dock bit when within
  160 m), leaves the mode at margin ≥ .05. Applied at evaluation to the final and initial policy
  of every fit (F-mode panels). It is the competent rule the previous DM retained ("O + F").
- **Static layout witness**: `estimate_heuristic_qos_feasibility` on a throwaway env at reset
  for each panel world (it mutates positions, so never on a live evaluation env). On the 32 panel
  worlds: QoS ratio mean .9967 (SD .0073, min .9708), met fraction .957, 32/32 feasible, 5–6
  service UAVs at 50 m. It is an achievability witness for a stationary fleet at t = 0 ignoring
  energy and mobility, not an upper bound; it says the QoS term itself is not what limits the
  learned .27–.34 per step.
- **Shield-alone**: the F-mode panel of each fit's initial (untrained) policy; B09's value is
  609.5 J. The learned contribution under the shield is F(final) − F(initial).

### Evaluation protocol

Fixed panel: 32 worlds, seeds 952001–952032 (B09 `PRIMARY_SEEDS`), H3000 each, deterministic
actions, evaluator synchronised from the training agent with frozen normalisers (B04
`evaluate` protocol: `_sync_agent`, `train(False)`, `seed_everything(policy_seed)`), policy
fingerprint checked unchanged before/after. Two modes per checkpoint: O (policy alone) and F
(shield). The panel is vectorised across worlds (parallel workers); this changes RNG consumption
order relative to B09's serial evaluator, so numbers are comparable in distribution, not
bit-identical. Per world: J, QoS/step, delivered Mbps, return-cost sum, cutoff and depletion
event counts, charger input Wh, charge starts and arrivals, minimum battery ratio, zero-service
flag. Panel aggregate = mean over the 32 worlds. Inference unit = fit (seed); per-fit values are
reported, arms are summarised as mean ± SD over seeds with all per-seed values shown.
Training-episode J/QoS (stochastic actions) are logged for every lane as the free curve.

### Pre-registered endpoints, predictions and rules

- Primary endpoint: final-checkpoint **O-mode panel mean J** (the learned policy alone).
  Secondary: F-mode panel mean J and QoS/step, O-mode QoS/step, risk-event counts, F(final) −
  F(initial).
- P1 (exposure): with the exposure below, at least one arm reaches O-mode J > 0 at the final
  checkpoint. If no arm does, the reading is "this host at this exposure does not support
  learned energy management", and the next study changes exposure, reward shaping or
  observation, not the algorithm.
- P2 (information): SET ≥ LOCAL1 on the primary endpoint (central snapshot helps positioning
  and slot timing); expected small.
- P3 (hierarchy): no predicted sign for HMASD − SET. This is the benchmark question.
- Structured-candidate rule (from the review): a structured coordination candidate is bought on
  this host only if the primary-endpoint gap between the best and worst learned arm is ≥ 2×
  the between-seed SD of the primary endpoint; otherwise the next investment is exposure,
  reward or host analysis, or track T2.
- Extension rule (fixed now): if at checkpoint 3 of 5 any arm's O-mode J is still rising over
  the last two checkpoints and remains below its own F-mode J, batch B02 doubles exposure with
  new fits; a running fit is never extended after its scores are seen.
- Seeds: 3 per arm in B01 (9 fits), training seeds 931001–931003 shared across arms (paired
  by seed only for the same initial-world sequence, not claimed as a paired design). The
  between-seed SD is measured here; B02 adds two seeds per arm when arm gaps are within 2× of it.

### Exposure and cost (sized from the node probe)

Bounded probe on `wsl_4070` (2026-09-26, B09 source tree, HMASD arm, CUDA FP32, 4 torch
threads; record: `evidence/probe_throughput_wsl4070_20260926.json`; no retained model):

| Measurement | Value |
| --- | ---: |
| Single env, random actions (node CPU) | 12.4 ms / step (this checkout's CPU: 36.1 ms) |
| 8-lane `ShardedSubprocVecEnv`, random actions | 23.4 ms / batch step = 2.93 ms / transition |
| Collection rollout, 8 lanes × 3000 steps = 24,000 transitions | 106.9 s (agent.step 22.8 s, env 67.7 s, store 16.5 s) = 4.46 ms / transition |
| One PPO update on that rollout (15 epochs, 4 minibatches, HMASD) | 172.7 s = 7.2 ms / transition |
| Peak RSS main process / CUDA max allocated | 7,113 MiB / 2,377 MiB; 8 env workers ≈ 2.7 GB more |
| B09 reference (2 serial lanes, B08 loop) | 5,022 s / 180,000 = 27.9 ms / transition |

Sizing of B01 from these numbers (constants in `FitSpec`; the implementer keeps them as
defaults):

- Exposure per fit **1.2 M transitions** = 50 rollouts × 8 lanes × 3000 (6.7× B09; one native
  episode per lane per rollout). Checkpoints at phases 0, 10, 20, 30, 40, 50 (0, 240 k, …, 1.2 M).
- Per fit: collection ≈ 1.5 h, updates ≈ 2.4 h, panels 6 checkpoints × 2 modes × ≈ 3.5–6 min
  (16 or 8 evaluation workers) ≈ 0.7–1.2 h; **≈ 4.6–5.1 h per fit**, 9 fits ≈ 41–46 h.
- Memory ≈ 10 GB per fit on a 15.8 GB node: **serial execution** (one fit at a time) unless the
  first MAPPO fits show a materially lower peak; the kernel's 4 GiB floor is checked only at
  launch, so a second concurrent fit would risk both.
- The update is the bottleneck (62 % of a rollout). The 15 PPO epochs are the S7 preset used by
  B09 N and are kept for comparability; a cheaper learner setting is a separate tuning question,
  not part of B01.
- Total B01 node occupancy ≈ 2 days. B02 (exposure doubling and/or two more seeds per arm)
  would be another 2–4 days; the extension rule above decides it prospectively.

### Engineering plan (L0 scope for `hmasd-implementer`)

New package `experiments/candidates/energy_relay_benchmark/b01/` and guarded entry
`scripts/run_energy_relay_benchmark_b01.py` (`require_admission(__file__,
direction="energy_relay_benchmark")` before any output, env, learner or evaluator). Reuse, do
not copy: `b01.native.make_config/make_env` (host), `hmasd.baselines.apply_algorithm_config`
(arms), `hmasd.sharded_vec_env.ShardedSubprocVecEnv` (collector, `metrics_mode="light"`,
start method spawn, picklable top-level env factories), `b04.evaluation.metric_row/TRACE_FIELDS`
(metrics), `b06.feedback.apply_feedback` (F mode), `b08.training._bootstrap_values` (last
values). One fit per launch: `--arm {HMASD,SET,LOCAL1} --seed S --out runs/...`. The loop is
the launcher's batched pattern (agent.step → vec step → store_transition_batch with step_data
→ reset_env_state on done → update at rollout end), without B08's per-step SHA audit and NPZ
dumps. Outputs: `config.json` (full active config record), `summary.json` (counts, per-phase
update info, per-lane training-episode J/QoS, checkpoints, panel aggregates, walls, RSS, CUDA
peak), `curves.json` (compact), `panels/<ckpt>_<mode>.json` (per-world rows), final and
checkpoint weights. Tests under `tests/experiments/candidates/energy_relay_benchmark/b01/`
with tiny specs (2 lanes, rollout 12, 1–2 rollouts, 2 panel worlds, H 24) and explicit mocked
admission for the entry; a determinism test that the vectorised panel gives the same per-world
J as the serial B04 evaluator on 2 worlds within 1e-5 on CPU. No core edits; if the light
metric set lacks a needed field, the runner recomputes it from `reward_info` keys already in
`SHARED_METRIC_KEYS` (qos_satisfaction_ratio, scenario7_reward, battery_min_ratio,
depleted_uav_count, charging_uav_count are present) and records what it could not recover.

### Operations runbook (wsl_4070; not executed now)

1. Publish exact inputs on main (code, tests, this NOTES entry, index row) and note the SHA.
2. Node control checkout `/home/wu/projects/HMASD` is sparse and at `fa7e75d2d5d` with an
   uncommitted hand edit of `docs/research/RESEARCH.md` (the PPC `paused` cell, per the PPC
   handoff) and three files identical to current main (`scripts/hmasd_launch.py`,
   `scripts/hmasd_snapshot_gc.py`, `.codex/hmasd-compute.toml`). Published main already carries
   PPC `paused`, so before launch: `git checkout -- <those four paths>` then
   `git pull --ff-only origin main`, both inside `zsh -lic` (the proxy lives in the login shell;
   a plain ssh `git fetch` hangs, the login-shell fetch takes 2 s). `.git/gc.log` reports
   `fatal: bad tree object 9e40125…` from an earlier auto-gc; fetch and launches still work, the
   object store is not verified healthy.
3. Launch each fit from the node with the configured interpreter, via the network shell:
   `zsh -lic "<python> scripts/hmasd_launch.py launch --node wsl_4070 --source-root
   /home/wu/projects/HMASD --snapshot --direction energy_relay_benchmark --lead '<exact lead
   cell>' --sha <full sha> --output runs/energy_relay_benchmark/<tag> -- scripts/run_energy_
   relay_benchmark_b01.py --out runs/energy_relay_benchmark/<tag> --arm <arm> --seed <seed>
   --launch-sha <full sha>"`. The kernel needs `experiments/` in the snapshot (full linked
   worktree from the SHA), not in the sparse control checkout.
4. Observe with `scripts/hmasd_launch.py status <operation_ref>` from a detached local poller
   (Claude has no Codex wake); collect into `runs/energy_relay_benchmark/<tag>/`, verify, then
   `scripts/hmasd_snapshot_gc.py --apply --snapshot <id>`.

### Prepared index text (apply to RESEARCH.md only after the owner's go)

Active row: `| \`energy_relay_benchmark\` | 冻结S7能源中继宿主（两个容量1充电站）上，
LOCAL1/SET/HMASD-k10 在相同曝光下的服务–风险效用、随曝光的学习曲线、与固定返航规则F及静态布局
见证的差距；只有出现值得购买的差距时才引入结构化协调候选。 | exploring | Claude DM (WSL session)
| **B01 已准备未启动。** 9 fits（3臂×3种子），… | `. Plan paragraph: replace the A/B/C
table's active rows with the benchmark-first plan (review §6), keep PPC paused, FSD/G33 frozen;
the superseded plan retires to `archive/2026-09-26/RESEARCH-benchmark-first-reset.md`.
Routing row: `Claude DM S7 基准 | this session / local | /home/fires/hmasd-wsl · main | …`.

### Pro question draft (constitution §5; not sent)

Decision it can change: the arms and endpoints of B01 before the first fit. Question: given
(1) B07/B09 evidence that 180k-transition HMASD policies deplete batteries without the F
shield, (2) a host where per-step QoS is not the binding term (static witness .997) but
charging contention and mobility are, (3) three actor-information arms at equal exposure with
the S7 preset hyperparameters, is the O-mode final panel J the right primary endpoint for a
benchmark paper, or should the shielded F-mode endpoint be primary with O-mode as the
"autonomy" secondary; and is there a cheaper competent learned baseline we are missing (e.g.
a shared recurrent PPO with an explicit battery-threshold action mask) that a wireless-venue
reviewer would demand? Sources to attach: this entry, B07/B09 tables, ACG B16/B17, the S7
config record. Send after the owner's go; record the complete answer here.

## 2026-09-26 — Reconciliation with the Astral review: B01 redefined as a zero-training reference study

### What changed and why

The owner's second review document
(`docs/Claude_docs/inbox/RESEARCH_PROGRAM_RESET_RESPONSE_FOR_CLAUDE_20260926.md`, ChatGPT at the
owner's request) accepts the task-first reset but rejects three things this notebook's first
entry inherited from my 09-26 diagnosis: a benchmark grid bought before the task question is
resolved, a five-seed/2×SD rule as a constitutional threshold, and treating the static layout
estimator as an upper reference. It asks for one S7 task with an explicit control boundary, the
smallest common reference, and one bounded prospective experiment or zero-new-training diagnostic
with outcome branches stated first. The point-by-point evaluation of the review, the corrections
to my diagnosis and the owner decisions are in
`docs/Claude_docs/reviews/RESET_RESPONSE_AND_FIRST_STUDY_20260926.md`; this entry records the
science that changes this direction's plan. The 9-fit suite in the first entry is **demoted to a
conditional B02** (see below); nothing in the first entry was executed.

### Mechanism found in source: the shield's exit margin tethers UAVs to the stations

Read on this checkout (`envs/pettingzoo/relay/energy_aware.py`, constants dumped from a live
`Config("S7-S2")` env at world 952001; scratch record `temp/directions/energy_relay_benchmark/`):

- `_raw_return_energy_margins` prices the return trip at `limp_home_speed_mps` = 3 m/s with
  P(3 m/s, 0) = 157.56 W: required battery ratio = d / 3 × 157.56 / 3600 / 160 ≈ **9.12e-5 per
  metre** of nearest-station distance; margin = battery − required − reserve (.10). Check: UAV 0
  at reset is 4,605 m from its nearest station and its recorded return threshold is .5199 =
  .10 + 4,605 × 9.12e-5. The B11 notebook already noted the 3 m/s model (a "different time/energy
  model"); its consequence for the exit side was not drawn.
- The B06 shield exits return mode at margin ≥ .05, which at the station (d ≈ 0) means battery ≈
  .15. From there the UAV re-enters return mode as soon as required ≥ .05, i.e. at **d ≈ 550 m**
  from a station (less once it consumes). After its first recharge a UAV can therefore serve only
  within roughly half a kilometre of one of the two stations unless the policy itself keeps
  requesting the dock, which the learned policies do not (B07: O charges in 1 of 80 worlds).
- Power model: hover 168.49 W (P0 79.86 + Pi 88.63), 10 m/s 126.03 W, 20 m/s 178.30 W, 30 m/s
  356.29 W. Mean initial battery .875 × 160 Wh = 140 Wh ≈ **2,991 s of hover**: the H3000 episode
  is almost exactly one hover-battery long, so energy decisions bite only in the final third.
- Charging: 2 slots × 1,000 W × 3,000 s = 1,667 Wh available per episode; B09 panels used
  158–194 Wh (≈ 10 %). Fleet hover load 8 × 168.5 W = 1,348 W < 2,000 W slot power, so the fleet
  is sustainable in steady state at ≈ 67 % slot utilisation, travel aside. The observed regime is
  the opposite: near-idle chargers, one-tick charging spells (B09 N: 12,024 of 12,536 spells
  last one tick), up to eight UAVs in return mode with a queue of seven (B07).

Prediction that follows (falsifiable, stated before any run): **raising the shield's exit margin
restores the fleet's service radius after the first recharge and raises complete service; the
entry margin matters less.** The competing prediction from the B10/B11 record: longer charging
removes UAVs for longer and crowds two slots, so complete service falls or is unchanged ("earlier
return may sacrifice useful service; later outer return may thin queue reserves", B11 closing
entry). Both are measured by the same zero-training run.

### Prior record, labelled per the owner's rule

- **TRIED**: F at (enter 0, exit .05) — B06 designed it, B07/B09/B10/B11 deployed it unchanged;
  the B06 entry chose margin 0 deliberately and warned against advancing the threshold in the
  same batch to re-pick a positive.
- **RECORDED and declined**: a constant-earlier-return control and threshold/hysteresis/dwell
  grids. The B10 Pro answer's branch "rules out automatic earlier thresholds, hysteresis, dwell
  grids"; the B11 Pro answer (MATERIAL_DISSENT) advised against buying an approach-aware rule or
  a constant-earlier control as repairs of a fixed policy; the DM ended the direction's investment
  on 09-25 with "neither direction has a measured new package gain". The reason was investment
  value of another *repair* of one fixed policy, not evidence about the timing decision itself.
  No entry/exit margin other than (0, .05) was ever evaluated.
- **NEW**: a mechanism test of the exit side with a source-derived prediction, on fresh worlds,
  on two controllers (the learned N policy and an executed layout heuristic), with the service
  loss decomposed into presence and per-present-UAV service. It selects no production threshold
  from exposed worlds; it measures how much the decision is worth.

### Question, task and boundaries (supersedes the first entry's question)

On the frozen S7-S2/H3000 host with two capacity-1 chargers and the environment's own slot
allocation unchanged (**policy study**, review §3.2), how much complete service is attainable by
lawful ordinary control, how much of the remaining loss is the return/exit timing decision versus
positioning under user mobility, and does any learned controller close either gap?
Information boundary: every controller acts from the legal per-UAV observation (365 dims; it
contains all 30 users, every teammate's battery/charging/dock/waiting fields and both stations'
occupancy and queue); the central state feeds critics only. Team size fixed at 8; no S4
failures; unavailability during charging is not a roster-change claim.

Strongest alternative problem: **positioning and relay formation under mobility**. The learned
policies deliver QoS/step .21 (initial) to .34 (B09 N) while a stationary k-means layout at reset
achieves .997 (constructive witness, 32/32 worlds), so most of the loss occurs while UAVs are
present. B01 measures both gaps in one run and decides which problem the direction pursues.

### B01 — zero-new-training reference study (development; fresh worlds)

- **Worlds**: 32 fresh worlds, seeds 953001–953032, H3000 each. The B09 panel 952001–952032 is
  reused only for a 4-world evaluator-equivalence check (952001–952004) against the recorded B09
  per-world J of N under production F; it is not read for any finding.
- **Controllers** (deterministic, legal observation only): **N** = B09 `N/endpoint/agent.pt`
  (seed 925031; on node `wsl_4070` at
  `/home/wu/hmasd-worktrees/usa-b09-48388289d/runs/uav_service_auxiliary/b09_an_925031_a01/N/endpoint/agent.pt`,
  sha256 recorded in that run's `summary.json`); **H** = executed layout heuristic: every 30 steps
  k-means on observed user positions (6 service centroids) plus 2 relay targets on the BS-to-
  service line, assignment by distance with 300 m switching hysteresis, cruise ≤ 30 m/s, height
  100 m, dock bit from the shield only. Development cap: three parameter variants H1 (6+2, 30 m/s),
  H2 (5+3), H3 (6+2, 10 m/s cruise) evaluated once each under production F; the best by mean J is
  the reference **H** and all three are recorded.
- **Shield grid** (same code path as B06, parametrised): entry margin e ∈ {0, .10, .20}, exit
  margin x ∈ {.05, .25, .45, .65, .85}, pairs with x > e only: 13 settings per controller; (0, .05)
  is the production package. Charging-slot allocation, reward, observation, horizon unchanged.
- **Readings per panel** (mean over 32 worlds, every world kept): native J, QoS/step, delivered
  Mb, return-cost sum, cutoff/depletion counts, zero-service worlds, minimum battery; presence
  fraction (UAV-steps not in return mode, not charging, not waiting) and QoS per present UAV-step;
  first-return step; charger input Wh; one-tick spell share; total wait ticks.
- **Pre-registered predictions**. P1 (mechanism): for N at e = 0, the best x ∈ {.25, .45, .65,
  .85} raises QoS/step by ≥ .03 over production and adds at most one zero-service world. P1′:
  at fixed x, changing e moves QoS/step by < .03. P2 (positioning): the reference H under
  production F reaches QoS/step ≥ .60. The practical threshold .03 QoS/step (≈ 90 cumulative QoS,
  one user of 30 served continuously) is anchored to the record: B09 read A−N = −.027 as no gain,
  and N's whole learning gain was .125.
- **Outcome branches** (decided now):
  (a) P1 and P2 hold → the retained O+F package was mis-specified by its exit margin, not by
  learning; the ordinary reference becomes H (or N) at its best constant margins; **B02** compares
  learned arms against that corrected reference on positioning, ≥ 3 seeds, exposure set from
  curves; timing is a rule-solved component, not the paper's method.
  (b) P1 holds, P2 fails (H < .50 under every setting after the three variants) → the host's
  service is hard even for a re-planned layout; report the feasibility boundary and inspect
  mobility/relay effects before any learned comparison.
  (c) P1 fails for N but H responds by ≥ .03 → timing matters only once positioning is competent;
  the problem is positioning; B02 as in (a) with reference H.
  (d) Neither controller moves by ≥ .03 anywhere on the grid → return/exit timing is not a
  consequential decision on this host at H3000; drop it as a candidate; the remaining loss is
  positioning and exposure.
  (e) Gains exist and the per-world best x differs across worlds (≥ 11 of 32 worlds prefer a
  different x by ≥ .03) → a state-dependent exit decision has value; next is the simplest
  queue-aware rule versus the best constant, before any learned timing component.
- **Cost**: 0 fits, 0 optimizer updates. 26 grid panels + 3 heuristic-development panels + 4
  equivalence worlds ≈ 2.8 M evaluation transitions. At the probe's 12.4 ms per env step with 8
  world-parallel workers ≈ 3–4 min per panel, ≈ 2 h on `wsl_4070`, CPU inference (the recorded
  B09 panels ran on CUDA; the equivalence phase reports the CPU-versus-recorded difference, and
  all B01 comparisons are internal to one device). Memory well under the 4 GiB floor per worker.
  Implementation: one implementer task from `temp/directions/energy_relay_benchmark/L0_b01.md`
  (in progress); one independent engineering review of the parametrised shield and the
  heuristic's observation decode (information rights and shield semantics are scientific inputs).
- **Prerequisites still unresolved**: node checkpoint integrity for `N/endpoint/agent.pt`
  (sha check before launch; the `usa-b09-48388289d` worktree must still exist); the heuristic's
  competence (hence the three-variant cap); the exact legal-observation user record layout
  (implementer reports it with a live-env test); CPU-versus-CUDA policy inference difference on the
  equivalence worlds.

### B02 (conditional; not authorised by this entry)

The first entry's LOCAL1 / SET / HMASD-k10 suite at 1.2 M transitions becomes B02 only under
branch (a) or (c), against the corrected ordinary reference, with exposure chosen from B01's
reference level and development curves rather than preset, ≥ 3 seeds per arm, and the seed SD
measured before any confirmation rule is written. The probe sizing in the first entry stays valid
(≈ 5 h per fit, serial).

### Literature (preliminary; bounded scout retrieval, not an audit)

A Sonnet scout opened the primary texts it cites (working files in the session scratchpad, not
retained). Closest: Brunori et al., arXiv:2105.05094 (2021): tabular RL learns *when to return*
against a "return at 15 % battery" rule, dominates it in 9 cases, but exit is always "charge to
full" and per-station capacity is not stated, so slot contention and the exit decision are not
tested; it releases a Gym environment without relay/backhaul. Kumar et al., arXiv:2409.00572
(2024) and Shakhatreh et al., arXiv:1705.09766 treat contended charging as offline ILP scheduling
with no service metric. No open environment combining finite-capacity charging, mobile users and
relay was found under eight queries. Snippet-only: PPO-UNC (ACM AISS 2021, 403 on fetch). The
usable terms are "recharging scheduling" and "return-to-charging-station policy"; no standard
name for the return+exit pair. Novelty of the *measurement* (exit timing under contended slots
against a competent hysteresis rule) is plausible on this evidence; a publication claim needs a
proper audit later.

### Prepared index text (apply to RESEARCH.md at the owner's go)

Active row: `| \`energy_relay_benchmark\` | 冻结S7-S2/H3000宿主、充电分配不变（policy study）：合法普通控制
可达的完整服务是多少，剩余损失中返航/离站时机与移动用户下的布局各占多少，学习控制器能否缩小任一差距？
| exploring | Claude DM (WSL session) | **B01 零训练参考研究已准备。** 机制预测：F 的离站余量 .05 使首次充电后
服务半径≈550 m；B01 在 32 个新世界上用 B09 N 策略与可执行布局启发式扫描进入/离站余量（13 组），分解在场率与
在场服务，0 fit、≈2.8M 评价步、≈2 h；分支 (a)–(e) 已预登记。B02（LOCAL1/SET/HMASD）仅在分支 (a)/(c) 下购买。
[本条](candidates/energy_relay_benchmark/NOTES.md#2026-09-26--reconciliation-with-the-astral-review-b01-redefined-as-a-zero-training-reference-study) |`.
Routing row: `Claude DM S7 能源中继 | this session / local | /home/fires/hmasd-wsl · main | 结果节点 wsl_4070；
Claude 无 Codex 唤醒，用分离轮询观察。`
The plan section is not rewritten by this direction; the response document proposes the
programme-level text for the owner.

## Pro question 2026-09-26 b01-exit-margin-mechanism-and-reference

Decision this can change: the design of B01 before its first evaluation (controllers, grid,
thresholds, branches), and whether reopening the return/exit timing question is legitimate after
the previous DM's 09-25 investment closure. Constitution §5 point 1 (establishing the question
and key comparator). Sources to read: this entry and the first entry above;
`docs/Claude_docs/reviews/RESET_RESPONSE_AND_FIRST_STUDY_20260926.md`; the S7 notebook
`docs/research/candidates/uav_service_auxiliary/NOTES.md` sections "B07 complete", "B09
complete", "B11 complete" and "Complete approach advice read; end current S7 repair investment";
`experiments/candidates/uav_service_auxiliary/b06/feedback.py`;
`envs/pettingzoo/relay/energy_aware.py` (`_raw_return_energy_margins`, `_apply_energy_dynamics`,
`_select_charging_uavs`, `_energy_observation`).

Questions (answer each; give your reasoning, contrary cases and what would change your view):

1. **Mechanism.** From the source, the shield's exit margin .05 combined with the 3 m/s return
   pricing (≈ 9.12e-5 battery ratio per metre) implies a post-recharge service radius of ≈ 550 m.
   Is this derivation right, and is it sufficient to explain the recorded regime (one-tick charging
   spells, ≈ 10 % slot utilisation, queues of seven, B07 worlds that serve until the first return
   and never again)? Which alternative explanation would you test first if not?
2. **Legitimacy and value of reopening.** The previous DM and your earlier answers declined a
   constant-earlier-return control and threshold/hysteresis grids as repairs of a fixed policy.
   B01 instead measures the size of the timing decision on fresh worlds with a pre-stated
   prediction, on the learned policy and on an executed heuristic, with presence/positioning
   decomposition. Is that a different scientific object, or a re-skin of what was declined? What
   would make it not worth running?
3. **Reference design.** Is the layout heuristic (k-means service centroids + relay chain on the
   BS line, re-planned every 30 s, legal observations only, shield for energy) a competent lawful
   ordinary reference for this host, and what is the strongest simpler executable alternative? Is
   a three-variant development cap defensible?
4. **Predictions and thresholds.** Critique P1/P1′/P2 and the .03 QoS/step practical threshold
   (anchored to B09's A−N = −.027 and N's .125 gain). Should the primary reading be QoS/step,
   native J, or presence-adjusted service, given that J's risk terms are near zero under any
   shield?
5. **Horizon.** Mean initial battery covers ≈ 2,991 s of hover, so energy decisions act only in
   the final third at H3000. Does this invalidate B01 as designed, or only limit its claim? Do not
   propose a host change unless you think B01 is uninformative without one.
6. **Branches.** Are the five outcome branches exhaustive and do they genuinely end the timing
   investment in branch (d)? Name any branch that would tempt a post-hoc rescue.

Constraints: 0 fits are proposed; do not prescribe a threshold grid beyond the 13 settings or a
threshold to adopt from exposed worlds; distinguish source facts, derivations and conjectures;
note explicitly what you could not verify.

### Answer

Pending. Not sent yet; the send is recorded in the transport section of this notebook when it
happens.
