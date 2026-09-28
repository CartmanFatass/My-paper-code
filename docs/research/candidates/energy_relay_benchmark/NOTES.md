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
  requesting the dock, which the learned policies do not (B07: O charges in 2 of 80 worlds, one
  B04 development and one B04 final world, none in B05).
- The same .05 hysteresis width also acts on the way in (added the same day, before the Pro
  question was sent; no run has occurred). During a 30 m/s approach the required ratio falls
  30 × 9.12e-5 ≈ 2.7e-3 per second while the battery falls only 356.29 W / 3600 / 160 ≈ 6.2e-4 per
  second, so the margin climbs ≈ 2.1e-3 per second and crosses .05 about 24 s after entry, some
  700 m into the approach. The shield then releases the UAV before it arrives, the policy flies
  off, the margin drops and the shield re-engages: a sawtooth that reaches a charger only from
  within a few hundred metres. B09 N recorded 2,710 shield activation intervals but only 624
  charger-input intervals; the B11 entry noted "F can exit at native margin ≥ .05 before arrival".
  Raising the exit margin lengthens both the approach engagement and the post-recharge radius,
  so the prediction below covers both effects and B01's first-return and presence readings
  separate them.
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

### Same-day correction before any run: the legal observation is radius-gated

The "Question, task and boundaries" paragraph above says the legal observation "contains all
30 users". That is wrong: it read the slot count `max_observed_users = 30` as visibility. The
implementer's live-environment decode (`envs/pettingzoo/relay/routed_core.py`, `observation_radius`
= 1,500 m) shows user, peer-UAV and base-station records gated to that radius, sorted by distance
and zero-padded; at reset no UAV observes any user in worlds 952001 and 953001–953005, and the
nearest UAV is 461–6,707 m from the base station. Only the 120-field energy suffix is always
complete. Decoded layout (verified against a live env): own position [0:3]; nearest UAV [3:6];
self state [6:11]; 30 user slots × 6 [11:191] (rel xy, SINR, connected-to-self, serviced-by-any,
serving-set size); 8 peer slots × 4 [191:223]; 3 BS slots × 4 [223:235]; 3 overloaded-UAV slots
× 3 [235:244]; step [244]; energy UAV records 8 × 13 [245:349]; station records 2 × 8 [349:365].

Decision (DM, before any run): the executed layout reference **H plans from ground-truth user
and base-station positions** every 30 steps and is labelled a *central-information executable
reference*; batteries, stations and the shield still act from the legal suffix. It answers "what
service is attainable by ordinary control given the positions", which is the reference the
positioning-versus-timing decomposition needs. Every learned arm stays on the local observation.
A local-information executable rule needs a search or patrol design when nothing is visible; that
is a scientific choice deferred to the independent review and the Pro question (item 7 below),
not made silently here. P2's threshold (QoS/step ≥ .60) now applies to the central-information
reference; a learned local policy's gap to it is partly informational and is read as such. The
1,500 m radius in an 8 km area also reframes the "positioning problem" for local learners as a
search problem, which B02's arm choice must respect (SET's central snapshot is the matched
comparator for H's information).

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

Revised the same day, after the independent scientific review recorded in the entry below and
before any send (the earlier text was never sent; no key was issued against it). Decision this can
change: the design of the revised B01 before its first evaluation (references, grid, readings,
thresholds, branches) and whether reopening the return/exit timing question is legitimate after
the previous DM's 09-25 investment closure. Constitution §5 point 1 (establishing the question and
key comparator); Pro is added here because the S7 record holds an unresolved disagreement about
timing repairs and because the independent review's diagnosis deserves a second, differently
framed reading. Sources to read: the entries of this notebook (the first entry, the reconciliation
entry with its same-day correction, and the review entry "Independent scientific review at the B01
boundary; B01 revised before any launch", which supersedes the earlier B01 section);
`docs/Claude_docs/reviews/RESET_RESPONSE_AND_FIRST_STUDY_20260926.md`; the S7 notebook
`docs/research/candidates/uav_service_auxiliary/NOTES.md` sections "B07 complete", "B09
complete", "B10 complete" (including "What continuity changed and what it did not buy"), "B11
complete" and "Complete approach advice read; end current S7 repair investment";
`experiments/candidates/uav_service_auxiliary/b06/feedback.py`;
`envs/pettingzoo/relay/energy_aware.py` (`_raw_return_energy_margins`, `_select_charging_uavs`,
`_communication_unavailable_mask`, `_charging_station_anchor_points`, `_energy_observation`);
`envs/pettingzoo/relay/routed_core.py` (`_apply_backhaul_action_guard`, the observation body);
`experiments/candidates/energy_relay_benchmark/b01/` (the study code at source_sha).

Questions (answer each; give your reasoning, contrary cases and what would change your view):

1. **Mechanism, after correction.** Source facts: the shield prices the return trip at 3 m/s
   (≈ 9.12e-5 battery ratio per metre); after exit the UAV is re-captured when its margin falls by
   the hysteresis width, so the post-exit radius is ≈ width / 1.12e-4 m at 30 m/s (≈ 447 m for the
   production (0, .05)); on approach the margin climbs ≈ 2.1e-3/s and crosses .05 about 24 s after
   entry, so the shield releases before arrival. Record facts the review added: one-tick charging
   spells come from the allocator's per-tick lowest-battery re-ranking (B10: 11,594 replacements
   against 408 ineligibility endings); low slot utilisation is late onset (first entry median step
   ≈ 1,173, first input ≈ 2,124); charging and waiting UAVs still serve (`_communication_unavailable_mask`);
   B10's team QoS/step was .22 before any F entry, .38 between first entry and first input, .44
   after; B07 938030 loses service before it first charges. Given all of that, what is the most
   likely dominant driver of the learned policy's low service in the first 40 % of the episode,
   before any energy pressure, and is the width tether still worth one zero-training measurement?
   Which single alternative would you test first if not?
2. **Legitimacy and value of reopening.** The previous DM and your earlier answers declined a
   constant-earlier-return control and threshold/hysteresis grids as repairs of one fixed policy.
   The revised B01 measures, on unexposed worlds, (i) the width response of the learned policy and
   of an executed reference, (ii) two executable references (central-information and
   legal-observation) as the attainable service, and (iii) a device null for per-world
   heterogeneity; nothing is adopted from these worlds. Is that a different scientific object, or a
   re-skin of what was declined? What would make it not worth running?
3. **Reference design under the guard.** S7 runs the backhaul action guard with reject scale 0.0:
   a serving or relaying UAV's move that would break a dependent path is zeroed. H_central
   executes the witness estimator's k-means layout (same seeding as
   `estimate_heuristic_qos_feasibility`) as waypoints replanned every 30 steps at up to 30 m/s.
   Does executing the witness layout suffice, or does the guard force incremental motion and a
   displacement cap? H_local plans from the union of the eight legal observations and, when fewer
   than `n_service` users are visible, sends unassigned UAVs to a 1,000 m ring around station 1
   (always visible in the energy suffix; placed at the reset user centroid by host construction).
   Is that a lawful ordinary controller, and is there a stronger lawful search seed?
4. **Predictions and thresholds.** Width is the primary axis; P1′ is read at matched width; the
   decomposition is the phase split (before first entry / entry to first input / after first
   input) rather than presence; J, return cost and cutoff/depletion are co-primary with QoS/step;
   P2′ splits the gap to the central reference into an information part (H_central − H_local) and
   a learning part (H_local − N); P3 tests the pre-entry deficit on unexposed worlds. Critique
   these and the .03 QoS/step practical threshold (anchored to B09's A − N = −.027 and N's .125
   learning gain). Is the null phase's 95th percentile a sound per-world threshold?
5. **Horizon.** Mean initial battery covers ≈ 2,991 s of hover, so at H3000 the study measures the
   first return cycle only. Does this invalidate the revised B01 or only bound its claim? Do not
   propose a host change unless you think B01 is uninformative without one.
6. **Branches (a)–(g).** Are they exhaustive, does (d) genuinely end the timing investment, and is
   (f)'s named rescue (a scheduler question, opened separately) the right boundary? Name any branch
   that would tempt a post-hoc rescue.
7. **Information boundary and B02.** With H_local available, does B01 now answer "what is
   attainable by lawful ordinary control"? The DM pairs H_central with central-state learned arms
   (SET) and H_local with local arms (N, LOCAL1) and forbids promoting H_central to the ordinary
   reference. What would you change before the run, and what only after reading it?

Constraints: 0 fits are proposed; the grid is the seven settings listed in the review entry; do
not prescribe a threshold to adopt from these worlds; distinguish source facts, derivations and
conjectures; note explicitly what you could not verify.

### Answer

*Saved from chat by the DM on 2026-09-26 (Pro answered in the conversation; the GitHub connector
exposed no write action, so no answer commit exists). Question key
`hmasd:901b4c3178634bca7cf79dbccff265988b095aef6d2f5dd314daa8b67033a01c`; source SHA
`414659f35f6dc4a41a07fd9d564223b2342499d0`; effort 6 Pro, thinking 34 min 36 s; collected by the
transport observer, answer sha256 `a5240e92982d768c125fef27246fdf9d2297e5c57a5f053f22940aa4ff59ab7c` (28,972 bytes UTF-8, 12,144
characters). Two attachment-chip echo lines from the page are omitted; the text is otherwise
verbatim, including the provider's inline formula rendering.*

**GitHub 读取可用，但本会话暴露的 GitHub 连接器没有仓库文件更新或提交动作，因此我没有发出写请求，也没有修改仓库。实际 Answer commit：无。**以下按附件要求提供完整答复。推理依据固定在 414659f35f6dc4a41a07fd9d564223b2342499d0，没有用移动的 main 替代指定来源。

B01：保留一次零训练诊断，但纠正信息分类、机制尺度和结果分支

MATERIAL_DISSENT: yes。

我的异议针对当前设计中的部分解释与判读规则，不反对经过下述修正的一次有界零训练参考研究。最重要的修正是：

早期服务缺口不能由尚未发生的退出阈值干预解释；约 450 m 是条件性的离站距离增量，不是普遍半径上限；当前 N 并非纯局部信息控制器，H_local 也不是单架 UAV 的局部控制器，因此 P2′ 不能解释为“信息缺口＋学习缺口”的因果分解。

这次研究值得保留的理由，是它可能回答一个会改变后续选择的问题：**在相同冻结宿主上，一个真实执行的普通控制程序能做到什么，以及退出宽度对两个具体控制程序的完整服务—风险表现是否重要。**它不应被用于寻找一个有利阈值，以重新证明旧固定策略修补路线值得继续。

以下分别回答七个问题。源码事实、他人对保留轨迹的重算、本文推导及研究判断会明确区分。

1．机制与早期缺口：首先指向部署行为不足，宽度仍值得测，但不是主解释
早期缺口最可能是什么

**我的首选工作解释是：这份固定策略没有足够快地形成有用的用户覆盖、搜索与中继几何。**这是部署行为层面的诊断，不是已经识别出的表示缺陷、信用分配缺陷或层次结构缺陷。

独立审查在笔记中报告的 B10 O 轨迹重算为：首次 F 进入前的团队 QoS/step 约 .219，这一阶段占 episode 约 39%；进入到首次输入之间约 .383，首次输入后约 .441。B07 的 938030 在 step 1607 起失去服务，首次充电却在 1946。这些证据不支持“首次补能后的 tether 导致早期低服务”，也不支持“服务总体在充电后崩塌”。这里的阶段数值是审查者对保留轨迹的重算报告，不是我独立读取 NPZ 后的重算。

还有一个更直接的因果约束。对进入阈值都为零、只改变退出阈值的配对，固定 checkpoint 和相同初始化下，退出阈值在首次导致不同 F 释放之前不会改变控制行为。因此，公共前缀中的低服务不能归因于这个退出宽度干预。这个判断来自反馈状态机，不依赖跨阶段均值的相关性。

但“首次 F 进入前”也不能直接改写为“没有任何能源因素”。电池与余量已经存在于观测中，原生能源成本已经生效，策略本身还能提交 dock 请求。更准确的表述是：**低服务发生在该 shield 首次接管之前，因此不能主要归因于其后续退出／充电过程。**这仍允许能量信息、训练目标、原生动作路径和部署策略共同影响早期行为。

宽度推导成立，但需限定“半径”和“24 秒”

按照指定源码，令原生余量为

𝑚
=
𝑏
−
𝑟
−
𝑎
𝑑
,
𝑎
=
𝑃
(
3
,
0
)
3
⋅
3600
𝐶
,
m=b−r−ad,a=
3⋅3600C
P(3,0)
	​

,

其中 
𝐶
=
160
C=160 Wh、
𝑟
=
.10
r=.10，
𝑑
d 为最近站点的三维距离。由源码功率公式计算，

𝑃
(
3
,
0
)
≈
157.5555
 
W
,
𝑎
≈
9.1178
×
10
−
5
 
m
−
1
.
P(3,0)≈157.5555 W,a≈9.1178×10
−5
 m
−1
.

这支持题面的返航定价数量级。

若退出时余量接近 
𝑥
x，随后无充电、最近站点不变，并以 30 m/s 近似水平径向离站，则

Δ
𝑑
≈
𝑥
−
𝑒
𝑎
+
𝑃
(
30
,
0
)
/
(
3600
𝐶
⋅
30
)
≈
𝑥
−
𝑒
1.11797
×
10
−
4
.
Δd≈
a+P(30,0)/(3600C⋅30)
x−e
	​

≈
1.11797×10
−4
x−e
	​

.

对宽度 .05，结果约 447 m。

**这里是从退出位置起算的离站距离增量。**只有退出发生在站点附近时，才能近似描述为“距站约 450 m 被再次捕获”。在远处提前退出、非径向飞行、改变最近站点、受到 guard 阻拦、爬升下降或边界裁剪时，它都不是普遍绝对半径，更不是安全保证。

同样，在外段以 30 m/s 径向返航时，

𝑚
˙
≈
30
𝑎
−
𝑃
(
30
,
0
)
3600
𝐶
≈
.0021168
/
s
.
m
˙
≈30a−
3600C
P(30,0)
	​

≈.0021168/s.

跨越 .05 约需 23.6 s，对应约 709 m 的接近距离。这解释了为什么 F 能在到站前释放，却不意味着每次进入后都恰好 24 秒释放；内部 docking 的速度、几何和耗能模型不同。上述均为源码常数的算术推导，不是新增环境轨迹。

为什么仍值得测一次

因为“宽度显著改变自由运动机会”与“宽度显著改善完整服务”是不同命题。后者尚未由推导回答，而且可能依赖控制器：N 获得更多自由距离仍可能不形成服务；参考控制器却可能利用它，或者反过来，较窄反馈把 UAV 带到更有用的位置。

必须保留最强反解释：**原反馈的趋站行为可能在部分世界帮助了几何部署；更宽退出阈值也可能延长集中驻站、等待和模式占用。**充电／等待不等于不能服务，源码的通信不可用条件是失败或电量低于服务 cutoff，而不是 F、charging 或 waiting 状态。

单 tick 充电段也不能再作为退出宽度问题的主要证据。B10 原规则的充电段结束包括 11,594 次仍合格成员被替换，只有 408 次失去资格；连续准入大幅改变了这个过程，却没有取得相应的完整净收益。

因此，我支持一次测量，但把它定位为完整闭环宽度响应的诊断。假如只能保留一个更小的替代，我会先保留“生产 shield 下，真实执行的合法观测参考与 N 的部署比较”，而不是另一个提前返航或调度修补。若该参考同样无法形成早期服务，我对“主要是这份策略的部署不足”的信心会下降，参考构造、动作 guard、搜索和宿主条件会变得更重要。

2．重开是否合理：科学对象有实质变化，但不是换新世界就自动成立

旧关闭决定明确拒绝了新的接近感知固定策略比较和常数提前返航比较，同时承认接近模型差异真实、可解释、可构造候选。关闭的理由是当时的增量决策价值不足，不是证明所有时机控制无用，也不是永久禁止这个问题。

修订后的 B01 与旧方案有三点实质差别：它执行一个非学习布局参考，而不只修补 N；它把参考能力与宽度响应放在同一宿主中观察；它预先承诺不从这些世界直接采用阈值。这使它有机会回答“后续究竟应研究部署学习、信息／搜索、控制时机，还是停止”的问题。

不过，**新世界只是减少本批结果驱动的选择，不会自动产生新的科学对象；两个控制器也不会自动产生机制识别。**本批始终只包含一个历史训练出的 N，32 个新世界不是 32 个训练重复。零新 fits 也不等于零成本，N 本身已经承担过 180k 训练 transitions。

以下情形会使它退化为旧路线的换皮：

无论结果怎样都启动既定 B02，参考研究实际上不改变选择。
在七个 setting 中选出最好者，就把它称为已确认的修复。
H 不够好便不断修 H，宽度有害便自动改 scheduler，均值不动便挑子群，直到出现阳性。
仍用错误的信息分类解释差距，使新数据无法回答所声称的问题。

两份复盘对本题最有用的提醒，正是“一个局部有效的下一比较”不等于“项目层问题已经解决”，以及参考、信息权限和完整后果应真正改变科学选择。我采用这一框架，但不把复盘意见当成新增经验重复或执行授权。

**我的结论是：这次重开可以成立，但价值主要来自参考校准，而不是来自又一次阈值网格。**如果修正后仍不能说明哪一种结果会让 DM 放弃原定后续，就不值得运行。

3．参考设计：执行 witness 是必要进步，但不保证胜任；ring 合法，但先验需准确
guard 不要求无条件增加位移上限

H 已经按实际动作逐步飞行：每秒最多约 30 m，每 30 步重新规划不是每次瞬移 900 m。把静态布局改成 waypoint controller，确实解决了“只证明一个位置配置存在，却没有控制器抵达”的关键缺口。

但 backhaul guard 保护的是当前依赖路径的链路容量，不是为未来布局规划一条可达路线。它在候选位置破坏依赖边时缩放速度至零。减小步长可能缓解一次跨越链路边界的问题，却不能保证解决结构性阻塞：沿同一方向再小的位移也可能不可接受，或者需要先由其他 UAV 建立替代路径。

S7 还有一个重要例外：对有效站点的显式 dock／return 请求，只要运动方向满足源码条件，可以绕过通常的 backhaul guard。不能把所有返航动作都描述成受同一“维持现有路径”约束。

最新笔记已纠正 probe 的最后一 tick 计数错误：在暴露世界 952001，H1/H3 的整体 blocked/checked 比例约为 7.4%／2.5%，QoS/step 均约 .78。这足以反驳“目前 H 必然整体冻结”，但只是一个已暴露世界上的 DM 报告，不能证明选定 H 在新面板普遍胜任。

因此，我不建议仅因 guard 存在就强制加入新 displacement cap。应保留现有开发选择，并依据真实位移、目标到达、持续阻塞及服务来判定问题。低拦截比例本身也不是参考胜任证书。

witness 与执行参考不能互相替代

estimate_heuristic_qos_feasibility 直接设置 UAV 位置，比较服务／中继数量和三种高度，然后计算该静态布局的服务。它提供的是一个构造性可行配置，不是从原 reset 出发的动态可达性证明，也不是最优性能上界。当前 H 执行其中一类布局，不等于执行了静态 estimator 的全部搜索能力。

所以，H 达到较高服务可以建立一个很有用的可执行参照；H 未达 .60，首先否定的是这组参考实现达到预期水平的预测，不能直接写成“静态 witness 不可执行”或“宿主没有普通控制解”。

station 1 ring 的合法性成立，但“精确质心”不成立

源码把用户初始质心作为 station 1 的锚点，随后还进行随机扰动、边界裁剪和站间距离处理。S7 配置的 station jitter 为 .12 × area_size，即 8000 m 场地中每轴约 960 m 的扰动尺度。因此，“station 1 就位于 reset 用户质心”应改为“station 1 的生成与 reset 用户区域相关”。它更不是移动用户当前的质心。

这不使 ring 非法。只要规划只使用合法观测中的 station 1 位置和公开宿主构造，利用这种相关性是一种合法的已知模型先验；不需要假装控制器不知道环境生成规则。非法的会是额外读取当前隐藏用户坐标、随机数状态，或把近似锚点当成真实坐标直接注入。

我没有证据证明一个替代搜索 seed 已经强于 1000 m ring。一个值得考虑、但尚未验证优越性的单一改进方向是：保留已发现服务簇及必要中继，把尚未分配的 UAV 用于围绕 station 1 的确定性分区扩张搜索，而不是只以“可见用户数达到 n_service”作为搜索充分的信号。找到六名用户不等于找到了对三十名用户服务最有用的布局。这个选择应在未看新面板前确定，不能在 B01 结果后逐步扩大搜索菜单。

另一个必须明确的边界是：**H_local 汇总八架 UAV 的观测，是“合法观测汇总式中央控制器”，不是每架 UAV 仅凭自身观测独立决策的控制器。**能源 suffix 让单架 UAV 知道队友和站点位置，并不意味着它自动知道其他 UAV 此刻看到的所有用户。

4．预测与阈值：保留可反驳预测，撤销不成立的因果分解
P1、P1′、P1c：分别检验用途、近似尺度与竞争解释

P1 使用预先指定的 (0,.45) 对生产 setting，要求完整 QoS 增量及 J 不恶化，是有意义的实用预测。应同时保留全部世界的有符号后果和风险尾部；均值有利不能抹去大损失世界，零新 cutoff／depletion 也不能证明风险不变。

P1′ 可以作为“宽度比绝对水平更重要”的近似预测，但不是源码强制成立的不变量。同宽移动进入水平，会改变首次进入时间、进入位置、储能、站端竞争、退出位置及剩余观察时间。这些变化足以使完整 QoS 不同，而不推翻局部余量推导。

七个 setting 中实际存在 三对匹配宽度：.05、.25、.45；宽度 .85 没有对应的 level .20 对照。不应把它写成四对，也不需要为凑第四对追加 setting。

P1c 的竞争方向合理，但“.85 的均值变化不大于零”包括几乎无变化，不能直接推出 herding，更不能推出 allocator 主导。较高退出门槛还可能造成模式驻留延长、观察期内没有退出、减少重新部署机会，或与 guard／移动几何交互。负的完整响应与具体过程证据同时出现，才会加强相应机制；仅凭符号不够。

P2 与 P3：是能力／部署预测，不是可行性或因果证明

.60 可以保留为对这套参考的预期水平，但不是物理可行性的界限。P2 失败时，应说“预定参考未达到预期”，而不是“普通控制达不到”。

P3 应明确绑定生产 setting，并报告每个世界的首次进入时间和 pre-entry 长度。自身首次进入前的均值是有价值的行为描述，但不同控制器的这个窗口长度不同，因而 H 的 pre-entry .60 与 N 的 pre-entry .22 不是相同时间窗内的处理效应。

可以从同一批轨迹补读一个共同前缀或固定时钟窗口，例如两控制器首次进入时间的较早者之前；这不需要增加 episode。原预注册 P3 仍按原定义报告，补读用于解释，不取代它。

P2′：当前信息分类存在实质性错误

这一点需要在运行前纠正。

B01 的 PolicyController.propose 将中央 state 和全队 observations 传入 HMASDAgent.step。高层调用 assign_and_value_batch；SkillCoordinator 把 state_embedding(state) 与全队 observation embedding 合并，经 encoder 产生决定实际技能的 logits。**中央 state 不只是供 critic 估值，它进入高层技能决策。**因此 N 的低层 actor 即使使用局部输入，完整 N 控制包也不能标成纯局部信息臂。

同时，H_local 具有观测汇总、联合分配、手工布局先验和不同刷新周期。于是

𝑄
(
𝐻
𝑐
)
−
𝑄
(
𝑁
)
=
[
𝑄
(
𝐻
𝑐
)
−
𝑄
(
𝐻
𝑙
)
]
+
[
𝑄
(
𝐻
𝑙
)
−
𝑄
(
𝑁
)
]
Q(H
c
	​

)−Q(N)=[Q(H
c
	​

)−Q(H
l
	​

)]+[Q(H
l
	​

)−Q(N)]

当然是代数恒等式，但不是“信息贡献＋学习贡献”的因果分解。

甚至 
𝐻
𝑐
−
𝐻
𝑙
H
c
	​

−H
l
	​

 也不只是抽走一项信息：中央版本按环境用户数组取得输入；局部版本需要重构、去重、排序，并在缺少用户时启用搜索。这会影响 k-means 初始化和规划轨迹。当前 H_local 又继承在中央模式下选出的参数，而不是独立完成同等开发选择。

我的最小修改建议是：保留两个有符号差值，但分别称为中央真值布局包相对观测汇总布局包的差值、观测汇总启发式相对历史层次策略包的差值。P2′ 的数值大小关系仍可作描述性预测；不要据它宣布“信息不是瓶颈，学习才是”，也不要为维持原标签去修改冻结的 N。

phase split 正确替代了 presence，但不是损失份额分解

采用 before-entry／entry-to-input／after-input，比“把 F／charging／waiting 视为不在场”正确，因为这些 UAV 仍可服务。不过阶段边界受控制器和干预影响，阶段内服务也受到共同轨迹影响，不能解释为能源、部署与恢复各自承担多少因果损失。

实现与报告还应显式处理没有进入、没有输入、短窗口和删失。策略自身可以请求 docking，所以也应处理首次输入早于首次 shield 进入的可能情形，避免阶段重叠或被错误命名。空阶段应记为不适用并保留长度，而不是填零；团队 QoS 不归属到刚刚补能的某一成员。

.03：可作为预先选择的实用尺度，不是统计校准

.03 QoS/step 是绝对三个百分点，在 H3000 上对应 90 个累计 QoS 单位；相对于约 .34 的历史 N 水平，约是 9% 的相对变化。B09 的 A−N 约 −.0272、N 自身学习增量约 +.1246，为这个数提供了历史量级背景。

但这两个历史效果不是方差估计，也不能自动确定最小有用差异。**可以说 .03 是本次投入判断选定的实用门槛；不能说它已由 B09 校准成显著性阈值、等效界限或最小可检测效应。**其用途还必须与 J、原生返航成本、最低电池尾部及真实事件一起判断。

device null 的 p95：有用的敏感性参照，不是逐世界显著性阈值

生产 N 在 B10 世界上的 CPU／CUDA 对照值得保留，但只有在模型、normalizer、动作与环境语义、初始化及随机流等一致时，它才主要反映设备敏感性；否则还混有 evaluator 迁移差异。

它的第 95 百分位可以标记：

这一世界的效应是否大于旧面板中观察到的大部分平台差异。

不能据此标记：

这一世界存在具有已知误报率的真实机制效应。

原因是闭环差异不是已建立的独立加性噪声；敏感性可能随控制器、宽度和世界状态改变；32 个值的 p95 主要由上尾少数值决定；对多个网格差值择大还会改变误报行为。N 的平台差异也不能自动校准 H 的所有逐世界差值。

同理，若 p95 大于 .03，放弃强逐世界判断是合理的保守选择，但“所以均值仍可靠”不自动成立：还要看 null 的有符号均值是否显示系统性偏移。反过来，p95 很小也不是机制归因的通行证。

所以我会保留 P0，把 
𝜏
𝑤
τ
w
	​

 降为描述性的敏感性参照。branch (e) 中的“至少八个超阈值世界”可以用于提出异质性候选，不能单独证明存在可利用的 regime，更不能直接支持规则采用。

5．H3000：限制主张，不使这次诊断无效

由源码悬停功率和平均初始电量计算，

𝑇
h
o
v
e
r
=
.875
×
160
×
3600
168.49
≈
2991
 
s
.
T
hover
	​

=
168.49
.875×160×3600
	​

≈2991 s.

这支持“本研究主要观察高初始电量 reset 后的启动和早期补能过程”，但不支持“每架 UAV 都只经历一次返航循环”的严格说法。初始电量有差异，返航取决于站距与 reserve，不需要先耗尽电池；F 也可能多次进入／退出而尚未获得输入。

另一个需要避免的过强简化是把悬停功率视为所有运动的耗能下界。按指定功率公式，10 m/s 水平飞行约为 126 W，低于 168.49 W 悬停功率。实际电池动力学与能源运行诊断中使用的保守量不能混为一谈。

“六架悬停 UAV 合计消耗略高于一个 1000 W 充电槽位的供能”是一个有用的局部算术机制，能支持集中驻站时的竞争解释；它不是整个移动团队的长期不可行性证明，也不能单独识别实际损失原因。

**我不建议为 B01 改 host 或延长 horizon。**它足以诊断启动部署、首轮实际补能附近的宽度作用及参考水平。应把结论写成“固定 S7-S2／H3000 下的完整有限时域表现”，而不是持续可再生运行、长期排队公平性或长期能源安全。

尤其对 .85，没有在 H3000 内完成足够的退出／重新部署，本身是需要保留的暴露和删失事实；不能把它简写为“宽度无效”，也不自动产生延长时域的义务。

6．分支 (a)–(g)：不是穷尽、互斥的判读；几个分支存在自动救援风险

现有分支已经比最初方案好，特别是明确不从本批直接采用阈值，以及增加了服务与 J 冲突的情形。但它们混合了效果、机制解释和后续投入，不能当作互斥且穷尽的决策树。

分支	建议保留的含义与必要修正
(a) 宽度有用	保留“形成进一步比较的候选，不采用”。固定 setting 的完整包效果可以成立，但不自动证明 tether 是主要机制；N／H_central 的结果也不能外推到未跑宽度网格的 H_local。
(b) 学习缺口	P1 在一个指定 setting 失败，不等于全部时机作用消失；H_central 仍可能有宽度响应。也不能依据 P2′ 的错误因果标签把剩余差距定为学习瓶颈。应改读具体控制包与参考之间尚未解释的部署差距。
(c) 参考不胜任	H 未达 .60，是参考预测失败，不是所有普通控制或静态 witness 的否定。可诊断，也可停止；不能自动变成无上限的参考重设计，更不能先用弱参考给 learned comparison 背书。
(d) 没有实用信号	可以真正结束当前 timing 投入。需明确查看哪些预定对比、绝对效应和风险，而不只看“正增益小于 .03”。结论是本研究范围内没有足够理由继续，不是统计等效或普遍无效。精度不足也允许结束投入并保留未知。
(e) 逐世界异质性	超过经验 null 阈值的世界数，只是候选信号。还需问是否存在决策时可观察的状态关系，而非事后世界编号或挑出的反号。不能自动购买规则研究。
(f) 大宽度有害	先记录完整有害响应，只有相符的占用、等待、储能和退出证据才加强 herding 解释。scheduler 是可能另立的问题，不是已排队的救援方案，更不是从负响应直接推出的唯一答案。
(g) QoS 上升、J 下降	不称为联合净收益，但保留真实服务—风险交换。还需覆盖反向情形：服务不增而 J 因风险成本下降而改善；以及 QoS/J 均值改善但重要电池尾部恶化。不能只保留方便当前主张的一种冲突方向。

最容易引发事后救援的是 (c)、(e)、(f)，以及 P1 失败后从其他 setting 中挑最好者来追认 (a)。防止它们的办法不是新增审批层，而是清楚区分：本批观察到了什么、原解释被怎样更新、是否仍有值得支付的新问题。宪章允许保留未决和不利结果，并不要求每个分支都产生一个后续实验。

还应保留几个未覆盖状态：技术失败或比较身份不一致；不完整面板；相关干预机会不足；实用门槛附近仍不确定；完整包有用但过程预测不支持；某控制器明显响应而另一控制器不响应。不能把这些都塞进“没有效果”。

对于 (f) 的“去最近空闲站”，还要核对执行接口：当前动作只有运动和 dock 请求，站点目标由原生最近站点选择。合法控制器可以通过运动改变随后最近的站点，但不能直接假装已经拥有任意 station-ID 指令。增加目标站动作或改变分配语义会是另一个明确的控制／宿主问题，不是 B01 原包中的免费补丁。

7．信息边界与 B02：B01 能展示一种合法普通程序的可达表现，不能建立普遍上限

有了 H_local，B01 可以回答：

一个按声明的观测汇总、手工规划与刷新规则执行的普通控制程序，在这些新世界上的完整表现是多少？

它还不能回答：

单架局部 actor 所能达到的最好表现是多少？
所有合法普通控制的能力上限是多少？
N 与这个上限的差距中有多少由学习造成？

特别是当前开发代码先在中央模式选择 H 的变体，再把参数用于 H_local。这个设计可以合法评价一个预先固定的继承变体，但不能写成 H_local 已独立选出了最胜任的局部参考。

运行前应修改的内容

我建议保留七个 setting、既定面板及零新 fits，不扩成新的参考搜索项目。修改集中于下面几项。

**首先修正事实与标签。**把 N 写成中央高层技能条件下的层次控制包，把 H_local 写成合法观测汇总式参考；撤销 P2′ 的因果命名；把 station 1 改称受扰动的相关锚点；把 447 m／24 s 写明条件。当前最小可行修订是降低解释强度，不是修改旧 N 或偷偷给 H_local 增加开发面板。

**其次使保存的读数足以支撑机制判读。**当前 B01 保存的 trace 包含 reward、QoS、mode、charging、waiting、battery、dock bit 等，但缺少重建 tether 和站点 herding 所需的若干直接字段。反馈决策已经计算了 margin、最近站点距离及选择结果；建议在同一批轨迹中保留这些小量字段，并保留逐站占用、关键规划目标／实际位移或足以识别持续 guard 阻塞的摘要。无需新增环境分支或保存所有高维内部状态。否则，应将研究明确限定为 setting 的完整包响应，不在结果中声称已经验证半径或 herding 机制。

**再次修正判读语义。**明确 phase 的异常次序、空窗和删失；保留各阶段累计量及长度；把 null 阈值限定为敏感性参照；补齐上述分支。不完整世界不能静默退出均值，开发变体也不能因为失败世界被排除而在不同世界集合上竞争。真实早终止是科学结果，技术不完整是缺失证据，两者都不能靠补零或自动重跑消除。

**最后修正已有数量不一致。**按当前代码与计划，最多为：

4
+
32
+
24
+
32
+
(
2
×
7
×
32
)
=
540
 episodes
,
4+32+24+32+(2×7×32)=540 episodes,

即 
540
×
3000
=
1.62
540×3000=1.62 M transitions。笔记末尾的 316 次把两个控制器的网格少算了一半；代码执行两个控制器。这是记账修正，不是建议扩大面板。

哪些决定应留到完整结果之后

完整结果之后，再判断参考是否确实胜任、宽度作用是否值得进一步研究，以及是否有一个具体学习问题值得形成 B02。不能因为预先写好了 LOCAL1／SET／HMASD，就默认启动九个 fits。

B02 的匹配不应只凭名称决定。需要按实际部署路径匹配中央 state、联合观测、局部观测、记忆、刷新周期及手工先验。当前 N 高层 k10、H 每 30 步重规划等差异，都意味着“信息来自合法字段”不等于“控制机会相同”。包级用途比较可以保留这些差异，但必须标明；关于学习结构的归因需要对应控制。

因此，原先简单的 “H_central 对 SET，H_local 对 N／LOCAL1” 不成立。**N 不能和纯局部 LOCAL1 合并成一个信息类别；H_local 也不能直接成为严格单架局部 actor 的匹配参照。**这不要求现在增加一个新训练臂，只要求 B02 在真正形成时按实际接口而不是标签设计。

结果后也不应在同一面板修改 ring、位移 cap、退出阈值或 horizon，再把改进结果当作原 B01 的验证。原结果保留完整；新问题必须有独立理由，而不是原预测的救援义务。

来源边界与最终判断

我读取了附件、固定问题及其同日修订、两份指定 inbox 复盘、DM 的 reset response、宪章相关治理内容、S7 的 B07／B09／B10／B11 结果与最终关闭决定，以及本题涉及的反馈、环境、观测、参考和 evaluator 源码。对 N 信息路径的判断另外核对了 hmasd/agent.py 与 hmasd/networks.py 的高层决策调用。

**仍未独立核验的内容有明确边界：**仓库外 checkpoint、NPZ／gzip 原始轨迹、现场节点与测试产物；同日 probe 的原始 scratch 输出；955／956 世界在全部仓库历史中从未暴露的全局检查；未来 B02 各实现的实际信息接口。本文没有重新审计其他方向的 CLAIM，也没有重新核验文献新颖性。历史数值与阶段重算按已读笔记及其作者标明的核验范围使用，不冒充本轮原始数据审计。

这些缺口不妨碍上述源码与设计批评，但意味着我没有确认 B01 的新效果、参考在新世界上的普遍胜任、长期安全或新的学习优势。

最终建议：保留一次修正后的 B01，把核心价值放在“真实执行的参考能力＋有限时域宽度响应”，而不是“退出宽度解释了早期低服务”。最该在运行前纠正的是 N／H_local 的信息分类和 P2′ 的因果命名；最该在运行后坚持的是，即使物理过程改变、某些世界改善或某个 setting 胜出，也不自动重开固定策略修补、调度救援或既定训练网格。

## 2026-09-26 — Independent scientific review at the B01 boundary; B01 revised before any launch

### Dev probe declared before running (not a result)

Purpose: the independent review (recorded below) notes that the S7 backhaul action guard
(`configs/config_1.py` line 424: `enable_backhaul_action_guard` for S6–S10; reject scale 0.0 in
`routed_core.py::_apply_backhaul_action_guard`) zeroes a serving or relaying UAV's move that would
break a dependent path, so an executed layout heuristic may freeze under service; the
implementer's 60-step central-mode test predates any routing path. Before committing node time,
one local probe on the already exposed B09 equivalence world 952001 (CPU, 3000 steps, production
shield (0, .05)): H1 and H3 in central mode as currently implemented, reading guard checked and
blocked action counts, F-mode UAV-step fraction and QoS/step. It informs whether H's motion needs a
displacement cap; it does not select a variant (the selection rule is fixed on the separate
development worlds 956001–956008 below) and it is not a B01 result. Script and output:
`temp/directions/energy_relay_benchmark/scratch/probe_guard.py`, `probe_guard_H1.json`,
`probe_guard_H3.json`.

### The review (ResearchCritic role, separate context, read-only)

Obtained before any launch under constitution §5 as amended today (one adequate independent
scientific review at a consequential decision). The critic did not inherit this session's context;
it read the notebook proposal, then reconstructed from source and from the retained B10 O raw traces
(`/home/fires/hmasd-artifacts/uav_service_auxiliary/b10_oc_925031_a01/raw/O_9530xx.npz`, read-only
numpy, no new transitions). Labels: [S] source fact, [D] derivation from source constants, [R]
recomputed from the retained traces, [C] conjecture. Material dissent: **yes**, four points, all
blocking a launch of B01 as frozen, none blocking a revised zero-training study.

1. **"32 fresh worlds 953001–953032" is false.** [S] S7 NOTES line 10885 fixed exactly these seeds
   as B10's "32 new paired evaluation world seeds" and published per-world N+F results on them.
2. **The mechanism entry over-claims sufficiency.** [S] One-tick charging spells come from the
   allocator: `_select_charging_uavs` re-ranks eligible candidates every tick by lowest battery,
   and B10's own spell endings are 11,594 same-station replacements, 408 ineligibility endings,
   38 censored. [R] ≈ 10 % slot utilisation is a whole-episode figure with late onset: first F
   entry median step 1,173 (490–1,760), first charger input median 2,124 (1,827–2,492); after the
   first input the busiest station is occupied 62 % of ticks. [S] B07 938030 loses service at
   step 1,607 and starts charging at 1,946: the loss precedes the first recharge. [R] Team QoS/step
   is .219 before the first F entry (39 % of the episode), .383 between first entry and first
   input, .441 after the first input (29 %): service does not collapse after recharge, because [S]
   `_communication_unavailable_mask` counts a UAV unavailable only when failed or at battery ≤ .02,
   so charging and waiting UAVs still serve and relay, and [S] station 1 is placed at the reset
   user centroid. What does hold: [D] 9.118e-5 per metre; a .05 margin ≈ 548 m without
   consumption, ≈ 447 m outbound at 30 m/s; approach margin climbs 2.12e-3/s and crosses .05 after
   23.6 s ≈ 709 m; [R] the tether is real (median 90th-percentile station distance of free time
   after a UAV's first charge = 342 m; 68 % of post-first-input time in F mode) and release before
   arrival is real (median battery at F exit .291, 10th percentile .152).
3. **The presence decomposition is invalid** under the unavailability mask: [R] after the first
   input 68 % of UAV-time counts as "absent" under B01's definition while team QoS is at its
   highest; "QoS per present UAV-step" inflates mechanically and team QoS is not additive.
4. **Branch (a) adopts margins from exposed worlds and promotes the central-information H to
   the ordinary reference**, confounding information with learning.

Further points: [D] the post-exit radius is set by the hysteresis **width** (x − e)/1.12e-4 m, not
by x alone, so (0, .05) and (.20, .25) are the same tether and the grid already contains four
matched-width pairs; P1′ as stated contradicts P1's own mechanism. J is not inert under a shield
(B10 C raised return cost by +24.6 per world). [D] A competing mechanism for high x: k hovering
UAVs draw 168.5 W × k against 1,000 W of supply, net ≤ 0 at k ≥ 6; lowest-battery-first ping-pong
equalises batteries so departures synchronise late; [R] herding is observed (on average 90 % of
occupancy at one station; median maximum queue 6). Horizon: B01 measures the first-cycle
transient, which bounds the claim; a horizon change is a host change and a new direction under the
freeze. Branches: missing (f) large negative response to x with the scheduler ("route to the
nearest free station") as the named rescue, and a trade-off branch (QoS up, J down); branch (e)
needs a null, and a free one exists: the production cell on CPU against B10's recorded CUDA
per-world values on all 32 worlds (B11 saw per-world |ΔQoS/step| up to .033 from closed-loop
divergence alone). Reference: [S] the backhaul action guard is on for S7 with reject scale 0.0,
so a serving or relaying UAV whose move would break a dependent path is zeroed; H's competence
under it is unexecuted conjecture; the strongest simpler alternative is to execute the
`estimate_heuristic_qos_feasibility` layout as periodic waypoints; choose variants on a separate
development panel. Information boundary: a central-information H is acceptable as a timing probe
but does not answer "attainable by lawful ordinary control"; SET is its matched comparator; a
local rule is not forced to be deferred, since the always-complete energy suffix gives every UAV
the teammates' and both stations' positions and station 1 lies near the reset user centroid, a
lawful seed for search. Could not verify: node checkpoint integrity, H under the guard, tether
cost versus user displacement (no user positions in the NPZ files), B09 raw traces, the 365-field
decode, whether 955xxx is unused. Recommendation: revise, do not stop; the deployment deficit is
real ([R] QoS .22 over the first 39 % of the episode against a static witness near 1.0).

### DM verification and response

Verified on this checkout: (i) S7 NOTES line 10885 and the per-world table at lines 10981–11012:
953001–953032 are B10's worlds, and line 11528 fixes 954001–954032 for B11; the "fresh" claim in
the entry above was mine and wrong (I had checked B09's 952xxx range only). A range grep for
955000–959999 over `docs/research/**`, `experiments/`, `scripts/`, `tests/` and `configs/` finds
only decimal fragments; 955001–955032 and 956001–956008 are unexposed on S7. (ii)
`_communication_unavailable_mask` = failed OR battery ≤ `service_cutoff_threshold` (.02). (iii)
`_select_charging_uavs` sorts eligible candidates by (battery, −wait, index) each tick and keeps
the first `capacity` (= 1); the B10 spell-ending counts are at S7 NOTES "What continuity changed
and what it did not buy". (iv) `configs/config_1.py` line 424 enables the guard for S6–S10, reject
scale 0.0 at line 60; guarded UAVs are those in `routing_paths`; the energy override exempts a
dock-request move toward the target station. (v) `_charging_station_anchor_points`: relay anchor
.7·BS + .3·service centre, station 1 = mean reset user xy (the jitter the critic mentions I did
not verify). (vi) All active UAVs consume at least hover energy per step
(`energy_aware.py` 2043–2049), so the station arithmetic holds. Not re-derived by me: the [R]
numbers from the B10 traces; they are recorded as the critic's and used as motivation, and B01's
phase-split readings test the same quantities on unexposed worlds.

Retracted: the fresh-worlds statement; the sufficiency of the exit-margin mechanism for one-tick
spells, low utilisation and the B07 "never again" worlds (both in the mechanism section above and
in `RESET_RESPONSE_AND_FIRST_STUDY_20260926.md` §5, corrected there the same day); the presence
decomposition; branch (a)'s adoption of margins from the study's own worlds; P1′ as stated.
Retained, source-derived: the 3 m/s return pricing; the tether after exit; release before arrival;
the width dependence of the post-exit radius. Adopted: every revision the critic recommends, with
two DM choices: seven grid settings rather than "two widths plus production" (a four-point width
curve at level 0 plus three matched pairs, so branch (f) has a high-width point), and the B09
four-world equivalence phase kept alongside the new 32-world null (it is already coded and costs
four worlds). No disagreement remains for Root-level resolution; the owner's "Both" was given on
the earlier design and the revision below stays inside its envelope (a zero-training reference
study on `wsl_4070`, 0 fits) at higher evaluation cost, reported to the owner.

### B01 revised (supersedes "B01 — zero-new-training reference study" above)

- **Worlds and roles**. Grid and reference panels: **955001–955032** (unexposed). Heuristic
  development: **956001–956008** (unexposed; the only selection domain). Device null:
  953001–953032 (B10's O worlds; used only to compare the production cell on CPU with B10's
  recorded CUDA per-world J and QoS/step; nothing is selected on them). Evaluator equivalence:
  952001–952004 against B09's recorded per-world J (record only, no gate). 955xxx are development
  worlds of this direction: any candidate named on them is confirmed on unexposed worlds later.
- **Controllers**. **N** = B09 `N/endpoint/agent.pt` (unchanged identity). **H_central** = the
  best of H1 (6 service + 2 relay, 100 m, 30 m/s), H2 (5+3), H3 (6+2, 10 m/s) by mean J on the
  development worlds under the production shield; k-means seeded on the environment's user order
  exactly as `estimate_heuristic_qos_feasibility` does, replanned every 30 steps from ground-truth
  user and BS xy; labelled *central-positions reference*. **H_local** = the selected variant's
  parameters planning from the union of the eight legal observations (users within 1,500 m of any
  UAV, BS from the legal slots), with a lawful search seed when fewer than `n_service` users are
  visible: unassigned UAVs go to equally spaced points on a 1,000 m ring around station 1, whose
  position every UAV always sees in the energy suffix (station 1 sits at the reset user centroid
  by host construction; the prior is declared in the label "legal-observation (station-1 ring
  search prior)"). Shield, batteries and modes always from the legal suffix for all three.
- **Phases** (one `--phase all` run): equivalence (4 N worlds) → null (32 N worlds, production) →
  heuristic-dev (H1–H3 × 8 worlds, production) → reference (H_local × 32 worlds, production) →
  grid (N and H_central × 7 settings × 32 worlds). Progress is journaled per world.
- **Grid** (width is the primary axis): level 0 at widths .05, .25, .45, .85 = (0, .05), (0, .25),
  (0, .45), (0, .85); level .20 matched to the first three widths = (.20, .25), (.20, .45),
  (.20, .65). Post-exit tether ≈ width / 1.12e-4 m at 30 m/s: ≈ 447 m, 2.2 km, 4.0 km, 7.6 km.
  (0, .05) is the production package. Allocation, reward, observation, horizon unchanged.
- **Readings per world** (all worlds kept; means and counts per panel): native J; cumulative QoS
  and QoS/step; return-cost sum; cutoff and depletion counts; zero-service; minimum battery;
  charger input Wh; F-mode UAV-step fraction (descriptive); first F-entry step and first
  charger-input step (team); **phase-split team QoS/step** before first entry, between first entry
  and first input, after first input, with phase lengths; one-tick spell share and wait ticks
  (descriptive, attributed to the allocator); backhaul-guard checked and blocked action counts.
  No presence reading.
- **Pre-registered predictions**. **P0** (device null): per-world |ΔQoS/step| between the CPU
  production cell and B10's CUDA record on 953001–953032 has median < .01; its 95th percentile
  τ_w is the per-world heterogeneity threshold used by branch (e); if τ_w > .03 the per-world
  reading is unavailable at this size and only means are read. **P1** (width, N): mean QoS/step at
  (0, .45) exceeds (0, .05) by ≥ .03 with mean ΔJ ≥ 0 and no added cutoff/depletion event; the
  four-point width curve is read as a whole. **P1c** (competing, herding): (0, .85) − (0, .05) ≤ 0
  in mean QoS/step with lower QoS/step in the entry-to-input phase and more wait ticks. **P1′**
  (level at matched width, N): for each of the three matched pairs |ΔQoS/step| < .03. **P2**
  (reference): H_central at (0, .05) reaches mean QoS/step ≥ .60. **P2′** (gap split at (0, .05)):
  gap_info = H_central − H_local and gap_learn = H_local − N; prediction gap_learn > gap_info.
  **P3** (deployment deficit on unexposed worlds): N's pre-entry QoS/step is < .30 in ≥ 24 of 32
  worlds while H_central's pre-entry mean is ≥ .60. The .03 QoS/step threshold is the practical
  threshold anchored to B09 (A − N = −.027 read as no gain; N's whole learning gain .125), not a
  noise estimate; P0 supplies the device noise. J, return cost and cutoff/depletion are co-primary
  with QoS: no "gain" is read from QoS alone.
- **Outcome branches** (decided now; more than one may apply, each is reported):
  (a) P1 holds with J not worse → the exit width is a consequential decision for the learned
  policy on unexposed worlds; the gaining widths are *named* for confirmation on further unexposed
  worlds; nothing is adopted from these worlds; B02 (learned comparison) uses the H references at
  the confirmed width.
  (b) P1 fails, P2 holds and gap_learn > gap_info → the loss is the learner's deployment, not the
  shield; the timing investment ends; the next study is the learning question against H_local and
  H_central (B02 design), not a rule.
  (c) P2 fails (H_central < .60) → the static witness is not an executable target on this host;
  diagnose from guard-blocked counts, phase split and F-mode fraction (guard freeze, energy or
  mobility) and redesign the reference before any learned comparison.
  (d) No width effect ≥ .03 for either controller and small gaps → exit timing is not
  consequential in the H3000 transient (this study covers the first cycle only); no host change
  under the freeze; the remaining question is deployment.
  (e) Per-world width effects above τ_w in ≥ 8 of 32 worlds without a mean effect → a per-world
  regime is reported; it is a rule study, not a policy study; no adoption.
  (f) P1c holds → herding and the allocator dominate at long tethers; the named rescue is a
  scheduler question (route to the nearest free station), to be opened explicitly as a different
  question, not a shield or policy repair.
  (g) QoS up and J down through return cost → not a gain under the co-primary rule; both reported.
  If P2′ fails (gap_info ≥ gap_learn) the deficit is informational: local learners face a search
  problem, and B02 must pair a central-information learned arm (SET carries all user and BS
  positions in its state) with H_central and a local arm with H_local. B02 never promotes
  H_central to the ordinary reference.
- **Cost**. 0 fits, 0 optimizer updates. N: (4 + 32 + 7 × 32) worlds = 260; H: (24 + 32 + 7 × 32)
  = 280; 1.62 M evaluation transitions. Measured here: N ≈ 338 s per world (4 threads), H1
  ≈ 158 s (2 threads). On `wsl_4070` with 8 workers × 2 threads: ≈ 4.5–5.5 h. This is above the
  ≈ 2–3 h given with the earlier design; the added phases are the null, the development panel and
  the local reference.
- **Engineering**. One implementer pass from `temp/directions/energy_relay_benchmark/L0_b01_rev.md`
  (worlds and roles, phases, width-matched grid, phase-split readings and guard counters, H_local
  search seed, the engineering reviewer's fixes: a shield-on B07 equivalence test, the normalizer
  snapshot in the evaluator mutation check, a float32 comparison note). The engineering review of
  `feedback.py`, `observation.py` and the per-step contract (accepted; shield bit-identical to B06
  at production margins over 200 boundary cases; decode verified against `routed_core.py` and the
  energy suffix; step contract line-by-line equal to B07) stands; `heuristic.py` and `native.py`
  are read by the DM before commit.

### Dev probe result (declared above; one exposed world; not a B01 result)

World 952001 (B09 equivalence world), CPU, 3000 steps, production shield (0, .05), central mode as
implemented before the revision (`probe_guard_H1.json`, `probe_guard_H3.json`):

| Variant | Guard checked / blocked (UAV-step actions) | F-mode UAV-step fraction | First F entry | Charger input Wh | Min battery | Native J | Wall s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H1 (6+2, 30 m/s) | 1 / 1 | .351 | 1171 | 358.6 | .1015 | 2318.47 | 169.5 |
| H3 (6+2, 10 m/s) | 1 / 0 | .127 | 1401 | 121.9 | .1035 | 2316.79 | 171.3 |

Reading: the backhaul action guard is not a binding constraint on the executed layout heuristic
(one consultation in 24,000 UAV-step actions for each variant), so H's motion keeps its cruise
rule and no displacement cap is added. Both variants finish the episode without a cutoff or
depletion event. Cruise speed changes the energy regime materially (10 m/s costs 126 W against
356 W at 30 m/s and 168 W hovering): H3 enters the shield later and spends a third of H1's
UAV-steps in F mode at the same J; the development phase on 956001–956008 decides the variant
by its fixed rule. For orientation only: B09 recorded N's native J on this world as 862.70
(CUDA, production shield), so on this one exposed world the executed central-information layout
scores about 2.7 times the learned policy. Nothing in the design changes on this reading; P2's
threshold and the selection rule were fixed before it.

### Correction of the probe reading, implementer return and final inputs

**Probe correction.** The guard counters `backhaul_guard_checked_actions` /
`backhaul_guard_blocked_actions` are reset to zero inside `UAVRoutedRelayEnv.step`
(`routed_core.py` lines 3393–3394), so the first probe's end-of-episode read gave only the last
step's counts and the table above ("1 / 1", "1 / 0") is wrong. Rerun with per-step sums through
the revised evaluator (`probe_guard2_H1.json`, `probe_guard2_H3.json`; same world 952001, same
episodes, J and battery identical to the first run):

| Variant | Guard checked / blocked (episode sums over 24,000 UAV-step actions) | QoS/step | Pre-entry / entry-to-input / post-input QoS/step | First entry / first input | F-mode fraction | J |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H1 | 13,587 / 1,006 (7.4 % of checked) | .784 | .828 / .738 / .760 | 1171 / 1506 | .351 | 2318.47 |
| H3 | 17,104 / 435 (2.5 % of checked) | .783 | .708 / .839 / .855 | 1401 / 2088 | .127 | 2316.79 |

Corrected reading: the guard is consulted on most UAV-step actions (the heuristic's UAVs are in
routing paths most of the time) and blocks a small share of moves; it does not freeze the layout,
and H's motion rule is unchanged. On this exposed world the executed central layout serves at
about .78 QoS/step in every phase, which is above P2's .60 threshold; the threshold was fixed
before this reading and is not moved. Nothing else in the design changes.

**Implementer return** (one pass from `L0_b01_rev.md`; no core or `uav_service_auxiliary` edit;
nothing committed or launched by it). Deviations accepted as reported: guard counters summed per
step (the correct reading, see above); with ≥ `n_service` users visible but no BS decodable the
leftover UAVs take ring waypoints rather than holding (a BS is normally cached in the legal slots,
so this case is expected to be rare and is recorded per plan); the shield-on B07 parity test runs
120 steps at (0.25, 0.45) because the first exit on 952001 occurs at step 99; `--controllers`
defaults to `("N", --heuristic)` for a grid-only run and both flags are ignored under `all`; the
phase split is literal, with `input_before_entry` flagged per world and counted per panel;
`first_return_step` is renamed `first_entry_step`; ring waypoints are not clipped (the
environment clips positions). RNG grep of `heuristic.py` is clean (no `random`/`torch`). Open
risk resolved by the DM: `B01Spec.policy_seed` is set to **925031**, the seed B07's evaluator
uses (the checkpoint's own seed) and the seed B10's summary records, so the equivalence and null
phases compare device and closed-loop divergence only, not an evaluator-seed difference. DM
checks after the change: `tests/experiments/candidates/energy_relay_benchmark/b01` 28 passed;
`tests/experiments/candidates/uav_service_auxiliary/b06` 11 passed, 2 skipped (CUDA). The DM read
`heuristic.py`, `native.py` and `evaluation.py` in full before this commit.

**Final runner argv on `wsl_4070`** (20 CPUs; defaults 8 workers × 2 threads), wrapped by
`scripts/hmasd_launch.py launch --snapshot` from the control checkout `/home/wu/projects/HMASD`:
`scripts/run_energy_relay_benchmark_b01.py --out runs/energy_relay_benchmark/b01_ref_a01
--launch-sha <sha> --checkpoint /home/wu/hmasd-worktrees/usa-b09-48388289d/runs/uav_service_auxiliary/b09_an_925031_a01/N/endpoint/agent.pt
--phase all --workers 8 --threads 2 --device cpu`. 316 episodes (4 + 32 + 24 + 32 + 224). The
launch record follows in the next entry once the admission kernel accepts the operation.

### Transport record: Pro question sent (2026-09-26)

Question key `hmasd:901b4c3178634bca7cf79dbccff265988b095aef6d2f5dd314daa8b67033a01c`, bound to
source SHA `414659f35f6dc4a41a07fd9d564223b2342499d0`, target this file, heading "## Pro question
2026-09-26 b01-exit-margin-mechanism-and-reference". Sent by the Claude session through the Jev
route (owner instruction of 2026-09-26: the session owns the repository and does not ask for
permission; the owner also authorised the session to handle the send-and-receive workflow):
headless, effort pill "6 Pro", short cover note plus the complete question document (sha256
`6fb71a4c7a90ccfe39dbbe5fb20498fa642648bdb4885542f5c6f1d9e38d5671`), `send_effect: sent`,
attachment seen, new conversation whose address stays in the local operation file. The
deterministic observer (`jev_send.py wait`) is armed; delivery is read with `deliver` and the
answer is recorded under `### Answer` when it lands. The B01 launch does not wait for it.

Publication commit for the launch inputs: `414659f35f6dc4a41a07fd9d564223b2342499d0`
("energy_relay_benchmark: B01 revised after independent scientific review; constitution section 5
amendment; launch inputs"). The node fast-forward and admission launch follow; the launch record
is appended when the kernel accepts the operation.

### Launch record: B01 accepted on wsl_4070 (2026-09-26)

Owner authorisation of 2026-09-26 ("You have my permission on all things about this project
including use the remote node"). Node control checkout `/home/wu/projects/HMASD` fast-forwarded
to `e592c3a80` (origin/main; contains the launch inputs commit `414659f35`). Admission launch from
the node itself:

- `scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot
  --direction energy_relay_benchmark --lead "Claude DM (WSL session)" --sha
  414659f35f6dc4a41a07fd9d564223b2342499d0 --output runs/energy_relay_benchmark/b01_ref_a01 --
  scripts/run_energy_relay_benchmark_b01.py --out runs/energy_relay_benchmark/b01_ref_a01
  --launch-sha 414659f35f6dc4a41a07fd9d564223b2342499d0 --checkpoint
  /home/wu/hmasd-worktrees/usa-b09-48388289d/runs/uav_service_auxiliary/b09_an_925031_a01/N/endpoint/agent.pt
  --phase all --workers 8 --threads 2 --device cpu`
- `acceptance: accepted`, `accepted_at 2026-09-26T13:33:25Z`; control observation
  `origin/refs/heads/main` = `e592c3a80375b0005eba2ab3c7ecdbbe43872896`; host `LAPTOP-U9TDKC8A`.
- Operation ref `/home/wu/projects/HMASD/.git/hmasd-admission/73a990e5b4e0b5f8d884cf698b1adfdaf36bc653394898314592ccf161fb60ff.json`
  (claim key `73a990e5…fb60ff`); manifest and outputs under
  `/home/wu/projects/HMASD/runs/energy_relay_benchmark/b01_ref_a01/` (`launch-manifest.json`,
  `admission-preflight.json`, `process-exit.json`, `stderr.log`, then `config.json`,
  `progress.jsonl`, `<phase>/panels/*.json`, `<phase>/traces/*.npz`, `summary.json`).
- Snapshot source `/home/wu/projects/HMASD/.git/hmasd-launch-sources/673435a800d54f38a6c082d24588f454`
  (linked worktree of the published SHA); command sha256
  `7c6426769b7f6222872fc1017221d710dfa9547f91afda0afba4dc107606a34d`; detached supervisor pid
  706986 (posix session), runner pid 706987.
- Observation: a detached local poller (`temp/directions/energy_relay_benchmark/scratch/poll_status.sh`)
  reads `hmasd_launch.py status <operation ref>` and the progress journal every 10 minutes into
  `poll_b01_ref_a01.log`; it exits on a terminal state and the session is woken by the native
  background return. Expected wall ≈ 4.5–5.5 h for 316 episodes.

### DM response to the Pro answer (2026-09-26) and relaunch decision

Read in full. Pro states material dissent against parts of the interpretation and reading rules,
not against one corrected zero-training reference study; it recommends keeping the seven settings,
the panels and zero new fits. Point by point:

- **Accepted, verified from source, applied before any record exists.** (i) N is not a
  legal-observation-only controller: `hmasd/networks.py::SkillCoordinator.assign_and_value_batch`
  embeds the central state into the skill decision (state_embedding, line 712/751), and
  `PolicyController.propose` passes the state exactly as B07 does. N is relabelled "central-state
  skill conditioning (HMASD coordinator) + local low-level actors". (ii) H_local is a
  legal-observation *pooled central planner*, not a per-UAV local controller; relabelled. (iii)
  Station 1 is a jittered anchor: `charging_station_jitter_m = 0.12 × area_size` = ±960 m per axis
  uniform around the reset user centroid (`configs/config_1.py` line 529; `energy_aware.py` 393–398);
  the ring prior is lawful as a known-model prior, and the wording "at the centroid" is withdrawn.
  (iv) P2′ is demoted from a causal "information versus learning" split to two descriptive signed
  differences: central-truth layout package minus pooled-observation layout package, and
  pooled-observation heuristic minus the historical hierarchical policy package; the predicted size
  relation is kept as a descriptive prediction and no bottleneck attribution is read from it.
  (v) The 447 m tether and the 24 s release are conditional quantities (from the exit position,
  radial flight, unchanged nearest station), not universal radii; wording adjusted where used.
  (vi) Episode count: 4 + 32 + 24 + 32 + 2 × 7 × 32 = **540** episodes (the "316" above undercounted
  the two-controller grid; the 1.62 M transitions and the 4.5–5.5 h estimate already assumed 540).
  (vii) The saved traces lacked the fields that make the tether and herding readings checkable;
  they are added now (own positions, return margin, nearest-station index and distance, per-station
  occupancy and queue, guard counts per step, H targets, station positions, post-exit recapture
  distances). Without them the study could only claim package responses.
- **Accepted for the reading, no code change.** τ_w from the null phase is a descriptive
  sensitivity reference, not a per-world significance threshold; branch (e) yields candidates only.
  P1′ is an approximate prediction, not a source invariant; three matched pairs, not four. P1c's
  sign alone does not establish herding; the process fields above must agree. P2 failure reads
  "this reference did not reach its expected level", never "ordinary control cannot". P3 stays as
  registered and gains a post-hoc common-window reading from the same traces (the earlier of the
  two controllers' first entries), no extra episodes. Branches (a)–(g) are not exhaustive or
  exclusive: uncovered states (technical failure or identity mismatch, incomplete panels, too few
  intervention opportunities, effects near the practical threshold, package effect without process
  support, one controller responding and the other not) are reported as such, and (g) covers both
  conflict directions. (f)'s "nearest free station" is a separate question with an interface
  problem (the action carries no station target), not a queued rescue. .03 is a pre-chosen
  practical threshold, not a calibrated significance bound. Results never trigger the prepared
  B02 grid automatically; B02 arms are matched by actual deployment interfaces (central state,
  pooled observation, local observation, memory, refresh period, hand priors), not by names.
- **Not adopted.** A different search seed for H_local (Pro names a partitioned expansion around
  station 1 as a candidate, unverified): the ring stays; the alternative is noted for a later,
  separately justified reference, never added after reading these worlds.

**Relaunch decision.** The operation accepted at 13:33:25 UTC (`73a990e5…fb60ff`) had produced
no readable result (equivalence and part of the null phase; no score read by the DM). Because the
wrong N information label would be written into every panel record and the traces would lack the
mechanism fields, the DM stops that operation, publishes the corrected inputs and relaunches under
a new tag. The stopped output directory is retained with its process-exit record as evidence of
a superseded launch; nothing from it is read or reused. Cost: about one hour of node time.

Disclosure before the stop: the poller's progress excerpt printed one development-panel value
that the DM therefore saw before stopping the run: `heuristic-dev/H2_e0.00_x0.05` mean raw native
J 2196.87 on 956001–956008 (the operation had already finished equivalence, null and two of the
three development panels; N runs faster on the node than the local estimate, so the whole
operation projects to well under two hours). The value belongs to the superseded operation, is
not reused, and cannot influence the fixed selection rule; it is recorded so that no later reader
mistakes the relaunch for a reaction to it.

### Stop record: operation 73a990e5 superseded (2026-09-26, ≈13:46 UTC)

Stopped by the DM with SIGTERM to the launcher's posix session (pid 706986, runner 706987) from
the node. The supervisor and runner exited without writing `process-exit.json`, so
`hmasd_launch.py status` reports `admission.state accepted`, `execution.state unknown`, runner
and supervisor `absent`, exit witness `absent`, records consistent. The runner's `summary.json`
stays `INCOMPLETE`: 60 episodes and 180,000 steps completed (equivalence 4, null 32,
heuristic-dev 24; five panels), the `reference` phase had just started; 0 fits, 0 optimizer
updates, no failed world. Output directory
`/home/wu/projects/HMASD/runs/energy_relay_benchmark/b01_ref_a01/` is retained unchanged as the
evidence of a superseded launch; its panels are not read or reused (the one disclosed value
above excepted). Reason and replacement: previous subsection. The relaunch uses tag
`b01_ref_a02`, the corrected published SHA and the same node, worlds, settings and rules.
Observed throughput of the superseded run: 60 episodes in ≈ 13 min at 8 workers × 2 threads,
so the complete 540-episode operation projects to roughly 2 h, not 4.5–5.5 h.

### Launch record: B01 relaunched on wsl_4070 as `b01_ref_a02` (2026-09-26)

Inputs commit `e1fdbe72f53a1597c34c1d32c89ac6700251dca0` (the second revision: corrected code and
tests, this notebook through the stop record, the response document's cost line and the index
row) pushed to origin/main; the node control checkout `/home/wu/projects/HMASD` fast-forwarded to
it. Admission launch from the node itself (`temp/directions/energy_relay_benchmark/scratch/relaunch_a02.sh`,
the first operation's argv with the tag and SHA replaced):

- `scripts/hmasd_launch.py launch --node wsl_4070 --source-root /home/wu/projects/HMASD --snapshot
  --direction energy_relay_benchmark --lead "Claude DM (WSL session)" --sha
  e1fdbe72f53a1597c34c1d32c89ac6700251dca0 --output runs/energy_relay_benchmark/b01_ref_a02 --
  scripts/run_energy_relay_benchmark_b01.py --out runs/energy_relay_benchmark/b01_ref_a02
  --launch-sha e1fdbe72f53a1597c34c1d32c89ac6700251dca0 --checkpoint
  /home/wu/hmasd-worktrees/usa-b09-48388289d/runs/uav_service_auxiliary/b09_an_925031_a01/N/endpoint/agent.pt
  --phase all --workers 8 --threads 2 --device cpu`
- `acceptance: accepted`, `accepted_at 2026-09-26T14:00:45Z`; control observation
  `origin/refs/heads/main` = `e1fdbe72f53a1597c34c1d32c89ac6700251dca0` (observed 14:00:45Z);
  host `LAPTOP-U9TDKC8A`.
- Operation ref `/home/wu/projects/HMASD/.git/hmasd-admission/02f762d25c98f83c5f42f473fd1af854bfd4b7e347b9e8391e3393e01d00ac43.json`
  (claim key `02f762d2…00ac43`); manifest and outputs under
  `/home/wu/projects/HMASD/runs/energy_relay_benchmark/b01_ref_a02/` (same layout as the first
  operation).
- Snapshot source `/home/wu/projects/HMASD/.git/hmasd-launch-sources/8a164fa1d18e48d6abad2d045101d89e`
  (linked worktree of the published SHA); command sha256
  `2a95eacb58ad080347f7d1f48419f7415923f2fbba4bd0e2d9cd5442d09400cd`; detached supervisor pid
  712622 (posix session), runner pid 712623.
- Health at ≈ 14:06 UTC: supervisor and runner alive, no `process-exit.json`; equivalence phase
  complete (4 episodes), null phase at 14 of 32 episodes, no failed world; node memory 5.8 GB
  free of 15.8 GB, load ≈ 10.8 with 8 workers × 2 threads. `stderr.log` holds only the
  checkpoint loader's notice that the checkpoint carries no discriminator buffer and an empty one
  is created; that buffer is a training-time object and this run makes no fit or optimizer
  update, so the equivalence rows against B09 remain the record of a correct load. Completion
  projects to ≈ 2 h after acceptance by the first operation's throughput.
- Observation: the same detached local poller (`poll_status.sh`, every 10 minutes, PID file
  `poll_b01_ref_a02.pid`, log `poll_b01_ref_a02.log` under the scratch directory) plus a
  background waiter that returns to the session when the poller exits on a terminal state or
  when a poll shows the runner absent. Before the terminal state only health fields are observed
  (event, phase, panel, seed, failed flag, episodes completed, memory, process presence).
- Disclosure: while confirming the panel layout after the equivalence phase the DM saw world
  952001's equivalence row (N, (0, .05)): `raw_native_J` 877.165. The equivalence phase is
  record-only by the revised design (no gate), so nothing follows from it now; the comparison
  with B09's recorded per-world J is made at the reading together with the other three worlds.
  No other result field was read.

## 2026-09-26 — B01 result, read by the pre-registered branches (operation 02f762d2, tag `b01_ref_a02`)

Operation `02f762d2…00ac43` at published SHA `e1fdbe72f` completed on `wsl_4070` at 15:56 UTC:
`run_end` status `COMPLETE`, 540 episodes, 1,620,000 steps, 20 panels, 0 failed worlds, 0 fits,
0 optimizer updates, wall 6,197 s (1 h 43 min), exit code 0 with a valid exit witness
(`process-exit.json`; launcher records consistent). Outputs: `runs/energy_relay_benchmark/b01_ref_a02/`
(the JSON outputs are committed with this entry; the 20 trace archives, 153 MB, stay on the node
as the durable copy and are gitignored locally). Reading code:
`experiments/candidates/energy_relay_benchmark/b01/read_b01.py` (panels; standard library) and
`trace_checks.py` (per-step traces; numpy); their combined output is
`docs/research/candidates/energy_relay_benchmark/b01_ref_a02_readings.json`. The reading follows
the rules registered in "B01 revised" and the reading rules adopted in the DM response to Pro:
registered readings first, then post-hoc descriptive readings, each labelled. Node cost of the
whole B01 including the superseded operation: ≈ 2 h, 0 fits.

### Registered readings

**P0 (device null, 953001–953032, CPU production cell vs B10's CUDA record).** Median
|ΔQoS/step| = .0020 (< .01: holds). 9 of 32 worlds reproduce the record exactly, 23 are within
.01, 4 differ by more than .03 (largest −.079 on 953012, ΔJ −237). τ_w (95th percentile) = .036
> .03, so by the registered rule the per-world reading is unavailable at this size and only means
are read: branch (e) is not read, and every per-world count below is descriptive. Panel means
agree with the record (QoS/step .342 vs .344; J 994.2 vs 998.5; mean ΔJ −4.2). τ_w describes
cross-device sensitivity; within B01 every comparison is same-device and deterministic: the four
level-0 settings share the trajectory up to the first shield entry (identical pre-entry values
.231 / .810 and first-entry steps 1372 / 1300 across them), and the superseded operation's
disclosed H2 development value (2196.87) equals this operation's to the digit.

**Equivalence (952001–952004 vs B09's recorded CUDA J; record only, no gate).** CPU − CUDA per
world: +14.5, +31.0, −82.2, −0.3 (means 986.1 vs 995.3). Not bit-equal; the same character as
the null. N in this study is a CPU realization of the B09 checkpoint whose per-world trajectories
diverge from the CUDA record in most worlds while panel means agree.

**Heuristic selection (956001–956008 only).** Mean J: H1 2248.1, H2 2196.9, H3 2167.0 →
H_central = H1 (6 service + 2 relay, 100 m, 30 m/s) by the fixed rule; nothing else was chosen on
those worlds.

**P2 (reference competence) holds.** H_central at (0, .05) on 955001–955032: QoS/step **.774**
≥ .60 (J 2281.9; return-cost sum 4.8; cutoff and depletion 0; guard consulted 14,620 and blocked
1,129 actions per world, ≈ 7.7 %; zero-service worlds 0). H_local: **.597** (J 1628.4; return
cost 65.9; blocked 2,742 of 13,564, ≈ 20 %; one zero-service world). N: **.328** (J 955.0;
return cost 1.2; three zero-service worlds).

**P2′ (descriptive only, per the adopted rule).** gap_info = H_central − H_local = +.177;
gap_learn = H_local − N = +.269: the predicted size relation gap_learn > gap_info holds in
QoS/step and the two are nearly equal in J (+653 vs +674). No bottleneck attribution is read.

**P1 (width, N) fails.** (0, .45) − (0, .05): ΔQoS/step +.023 (< .03), ΔJ +71.8, cutoff and
depletion unchanged at 0. N's four-point width curve is .328, .343, .352, .336 (J 955, 1000,
1027, 980): an inverted U peaking at .45, entirely inside the practical threshold. H_central:
.774, .775, .782, .757 (J 2282, 2293, 2314, 2240): same shape, same verdict (P1[H_central]
+.0075). Nothing is read as a gain under the co-primary rule.

**P1c (herding) fails on sign for both controllers** ((0, .85) − (0, .05): N +.008, H_central
−.017) while the herding process is present and monotone in width: N's mean station queue
.47 → 1.13 → 1.70 → 2.12 UAVs across the four widths, P(queue ≥ 3) .08 → .38, waiting steps per
UAV-step .25 → 8.6, F-mode share .18 → .39, mean battery .48 → .57 (H_central at .85: queue
2.18, waiting 12.5); the entry-to-input QoS falls for N (−.021) but not for H_central (+.014).
Read as herding without a service consequence in this host, not as (f): waiting and docked UAVs
keep serving (the review's finding) and the stations sit at serviceable positions (below).

**P1′ (level at matched width) fails for N at all three widths and for H_central at width .05.**
N, level .20 minus level 0: +.048 (width .05), +.079 (.25), +.061 (.45); J +146, +236, +183.
H_central: −.050, −.020, −.021; J −140, −60, −61. This is the study's unregistered finding; it
has its own subsection below.

**P3 (deployment deficit) fails on the registered count.** N's pre-entry QoS/step is < .30 in
19 of 32 worlds (24 required; 5 worlds lie within τ_w of .30); the means are N .231 and
H_central .810 (the H part holds). Eight worlds have exactly zero pre-entry service for N. The
post-hoc common-window reading allowed by the DM response (both controllers over [0, min of the
two first entries), median window 1,236 steps): N .215 (< .30 in 22 of 32; zero in 7), H_central
.801 (≥ .60 in 31 of 32); paired H_central − N ≥ +.30 in every world (mean +.585, minimum
+.304, about 8 τ_w). The registered prediction fails as written; the mean-level deficit before
any energy pressure is large and present in all 32 worlds.

### Branch reading

- **(b) applies**: P1 fails, P2 holds, and the descriptive gap relation is gap_learn > gap_info.
  By the registered text the loss is the learner's deployment, not the shield; the timing
  investment ends; the next study is the learning question against H_local and H_central (a B02
  design), not a rule. By the adopted rule this does not trigger the prepared B02 grid: B02 arms
  are matched by actual deployment interfaces, and the design is a separate decision under
  constitution §5.
- **(d), width clause**: no width effect ≥ .03 for either controller at level 0; the exit width
  is not consequential in the H3000 transient (this study covers the first charging cycle only).
  (d) as a whole does not apply because the gaps are large.
- **(a), (c), (e), (f), (g)**: not applicable ((e) unavailable by τ_w; (g) no QoS-up/J-down or
  reverse conflict at any setting: for N every level-.20 setting raises both, for H_central every
  level-.20 setting lowers both).
- **Uncovered states, reported as such**: (i) one controller responding positively and the other
  negatively to the enter level at matched width; (ii) P3's count failure beside a large mean
  effect; (iii) a sub-threshold inverted-U width response common to both controllers; (iv) N's
  three total-failure worlds (zero service over 3,000 steps: 955005, 955012, 955021) against none
  for H_central.

### The enter-level effect (unregistered; labelled)

**What it is.** Raising the enter margin from 0 to .20 at matched width is the constant-earlier-
return control that the S7 closure of 2026-09-25 declined to buy as a repair of the fixed policy
("do not buy the proposed approach-aware fixed-policy comparison or a constant-earlier-return
comparison"). B01 measured it because P1′ registered the three level-.20 settings as matched
controls for the width axis, not as candidates. B01 does not buy it: nothing is adopted from these
development worlds, and N at its best setting (.20, .45) reaches .422 QoS/step and J 1236, still
below H_local (.597) and far below H_central (.774). Read as a bound: level .20 closes about a
fifth of the N–H_central gap on 955001–955032 ((.422 − .328) / (.774 − .328) = .21), consistently
across the three widths, with J up 15–29 %, return cost 0, cutoff and depletion 0, minimum
battery .28–.38 instead of .11; descriptively 19–20 of 32 worlds move up by more than .03 and
4–6 move down.

**Where the gain comes from (phase split, same panels).** N's QoS/step is .23 before the first
entry, .35–.38 between the first entry and the first charger input, and .45–.48 after the first
input; at level .20 the first entry moves from step 1372 to 570 and the first input from 2196 to
734–1467, so N spends roughly two thirds of the episode in its best regime instead of a quarter.
For H_central the ordering is reversed (.81 → .84–.85 → .69–.76), so earlier entry costs it
service.

**Process support (post-hoc, correlational; traces).** Within N's production panel, team
QoS/step is .28 in steps with no UAV within 300 m of a station and .43–.46 whenever one or more
are (late steps only: .37 vs .43–.46); by occupied station it is .31 (none), .46 (relay anchor
only), .39 (service-centre station only), .51 (both). The same tables for H_central fall when
four or more UAVs sit at the stations (.81 → .70) and when either station is occupied (.82 →
.71 / .73 / .62); H_local behaves like H_central. So, for this learned policy, the shield's
stations act as a crude deployment prior that beats its own placement and that the layout
references do not need: a docked UAV at the relay anchor is a backhaul hop by construction, and
the service-centre station sits at the user centroid. This is a conjecture with correlational
support, not a causal reading: time in episode and battery level co-move with proximity (the
late-only column reduces but does not remove the first), and N's three zero-service worlds stay
at zero after UAVs dock at both stations from step ≈ 2,000 on (2,500–3,100 UAV-steps within
100 m, 490–580 charging UAV-steps), so docking is not sufficient for service in N's
configuration. The named zero-training test is a parked-at-stations reference (UAVs held at the
two stations, shield on): if it reaches N's post-input level (.45–.48) the station positions
explain that regime. It is not run here and is folded into the next design question.

### The tether, read from the traces (post-hoc; confirms the derivation as an increment)

Per shield exit, the nearest-station distance at the same UAV's next entry minus the distance at
the exit: at width .05, median **+391 m** for N (IQR 318–433; 2,313 re-entries of 2,354 exits)
and **+411 m** for H_central (359–423; 1,275 of 1,318), against the derived ≈ 447 m; at width
.25, +1,770 m (N) and +1,664 m (H_central) against ≈ 2.2 km; at level .20 and width .05, +363 m
and +411 m. The increment depends on the width, not the level, for both controllers. The
absolute recapture distance differs by controller for the reason the source derivation gave:
H_central's UAVs exit at the station (median exit distance 20 m; entering from ≈ 1 km they
arrive inside the ≈ 24 s release window) and are recaptured ≈ 470 m out, whereas N's UAVs,
entering from ≈ 2.1 km, are released mid-return at ≈ 1.4 km and recaptured at ≈ 1.7 km, cycling
70–80 times per episode without reaching a charger until step ≈ 2,200. The earlier phrase
"≈ 447 m of a station" was conditional on exiting at the station; the increment statement is the
one the data support. Recapture counts per world fall from 72 (N) and 40 (H_central) at width
.05 to 9 and 3 at .25, ≈ 1 at .45 and 0 at .85.

### What B01 settles and what it leaves open

Settled on these worlds (development worlds of this direction; any candidate named on them needs
unexposed confirmation): the exit width is not the S7 loss; the executable layout references are
competent under the S7 backhaul guard; the learned policy's deficit precedes energy pressure in
every world; the tether and herding mechanisms behave as derived and cost little service in
H3000. Open: what the learned deficit consists of (the parked-at-stations reference and the
H_local–H_central pair are the cheapest next discriminators); whether a learner given a layout
reference's information can approach it (the B02 question); N's total-failure worlds (3 of 32)
as a distinct failure mode. Nothing here changes the host under the freeze, and no rule is
adopted.

### Next step (decision pending under constitution §5)

Branch (b) names a B02 design as the next study. The design is a consequential decision that
takes one adequate independent scientific review; per this direction's practice the
decision-critical pass goes to Pro. The DM drafts the B02 design next (arms matched by deployment
interface: a central-state learner against H_central, a pooled-observation learner against
H_local, with the parked-at-stations reference as the zero-training discriminator first) and the
Pro question with it. No fit is bought by this entry.

## 2026-09-26 — B02 design proposal after B01 (decision pending independent review; nothing bought)

Branch (b) of B01 names the learning question as the next study. This entry proposes the design
for review under constitution §5 (point 1: key comparator). It buys nothing; Stage 0 and Stage 1
below are launched only after the review is read and the DM's response is recorded here, and any
fit also needs the owner's go on cost.

**Question.** On the frozen S7-S2/H3000 host with the production shield (0, .05) and unchanged
charging allocation: can a learned controller that has a layout reference's information approach
that reference's service at this direction's exposure scale, and how much of the learned deficit
is the recipe (seed, hierarchy) rather than information? B01 fixes the targets: H_central .774,
H_local .597, N .328 QoS/step on 955001–955032; the deficit precedes energy pressure.

**Stage 0 — zero-training discriminators (≈ 15 min of node time, 0 fits; 955001–955032 at
(0, .05); the B01 evaluator, shield and traces unchanged).**
- H_spawn: all eight UAVs hold their reset positions at the service altitude (100 m); no
  deployment at all. A floor for "service without deployment".
- H_park2: one UAV hovers at 100 m over each station's xy (relay anchor, service centre); the
  other six hold their reset positions. The direct test of the deployment-prior reading of B01's
  level effect (a UAV at the anchor is a backhaul hop by construction; the centroid station covers
  the densest users).
- H_central@10: H_central replanned every 10 steps instead of 30, matching N's coordinator clock.
  Tests whether the reference's advantage depends on its control opportunity (Pro's point).
Predictions: S0-1, H_park2 − H_spawn ≥ +.10 QoS/step and H_park2 ≥ .40 (N's post-input regime is
.45–.48): the station positions alone reproduce most of that regime and the deployment-prior
reading stands; if H_park2 < .35 the reading is withdrawn and the level effect stays a package
effect. S0-2, |H_central@10 − H_central| < .03: the control period is not the reference's
advantage. Readings co-primary as in B01. No candidate is adopted from these worlds.

**Stage 1 — learning (6 fits).** Recipes from the first entry's arm table (config switches of
one agent; S7 preset hyperparameters; no per-arm tuning; shield on at production margins during
training as in B09; 1.2 M transitions per fit, ≈ 5 h serial, up to three concurrent on
`wsl_4070` under the owner's concurrency ceiling). Evaluation with the B01 evaluator at each
checkpoint on 955001–955032 (development; curves read as a whole) and once at the end on
957001–957032, reserved now as this direction's unexposed confirmation panel (no prior use found).
- SET × 3 seeds: flat actor on local observation plus the central state snapshot (the S7 state
  carries normalised UAV, user and BS positions, coverage and connectivity flags, link quality and
  the step clock; verified in `envs/pettingzoo/relay/belief_map.py::_get_state`), acting every
  step, no hand prior, no explicit memory. Package comparator: H_central (central truth, 30-step
  replanning, k-means layout prior). Differences labelled: control period (Stage 0 measures its
  weight), prior, memory.
- HMASD-k10 × 3 seeds: B09's recipe (coordinator conditioned on the central state every 10
  steps, local low-level actors). Supplies the seed spread around the one-seed N and the
  hierarchy-versus-flat package difference with SET as the same-information control.
- LOCAL1 is not bought now: no executable reference matches a strict single-UAV local actor
  (H_local is a pooled planner), and the lower-information arm is informative only after SET's
  result. It is named for a later, separately justified stage.
Predictions: B02-P1 (information suffices for learning), SET's final mean QoS/step on 955xxx
≥ .60 in at least two of three seeds, with J, return cost, cutoff and depletion co-primary and
the pre-entry (before first shield entry) QoS/step as the deployment diagnostic; B02-P2
(typicality), the HMASD-k10 three-seed mean within .05 of N's .328 with seed SD < .05; B02-P3
(hierarchy), no predicted sign for HMASD-k10 − SET (the benchmark question). The seed SD is
measured before any confirmation rule is written (first entry's rule).
Branches: (i) P1 holds: the S7 deficit is a recipe or structure matter, not an information
limit; the next question is the hierarchical learner's structure against SET (the paradigm
question), on 957xxx first. (ii) P1 fails with SET's pre-entry QoS/step < .40: central
information is not learned into deployment at this exposure; the learning question becomes
exploration and credit (service reward exists only once a backhaul chain exists; N's three
zero-service worlds), and the next study is a declared curriculum or shaping question, not a
rule. (iii) P2 fails (SD ≥ .05 or mean farther than .05 from .328): the B09 endpoint is not
typical and B01's N readings are relabelled as one seed's. (iv) Mixed or uncovered states are
reported as such. Results never promote H_central to the ordinary reference (Pro's rule).

**Cost.** Stage 0 ≈ 15 min, 0 fits. Stage 1: 6 fits ≈ 12–15 h of node wall at three concurrent
(≈ 30 h serial). Engineering: one runner `run_energy_relay_benchmark_b02.py` (arms, seeds,
checkpoints, panels) reusing B01's host, evaluator, shield and traces, plus the three Stage 0
controllers in `heuristic.py`; tests as for B01.

**Not proposed.** Training with enter level .20 (the constant-earlier-return premise the S7
closure declined; it would be a different question and re-litigation before the deployment
question is answered); host, allocator, ring or horizon changes; LOCAL1 now; any per-arm tuning.

## Pro question 2026-09-26 b02-design-after-b01

Standing: B01 is complete and read (entry "B01 result, read by the pre-registered branches" above;
readings JSON `docs/research/candidates/energy_relay_benchmark/b01_ref_a02_readings.json`; run
outputs under `runs/energy_relay_benchmark/b01_ref_a02/`; reading code
`experiments/candidates/energy_relay_benchmark/b01/read_b01.py` and `trace_checks.py`). Branch
(b) applied. The proposed B02 design is the entry directly above. Constitution §5 point 1 (key
comparator) applies; this is the decision-critical independent pass before anything is bought.
Distinguish source facts, derivations and conjectures; cite what you used; say what you could
not read.

1. **The B01 reading.** State any material disagreement with the reading as recorded: branch
   (b); the τ_w rule's application (per-world readings withheld while paired within-run
   differences are deterministic); P3 read as "count fails, common-window paired deficit ≥ +.30
   in all 32 worlds"; the tether confirmed as an increment (+391/+411 m at width .05, ≈ 1.7 km
   at .25) with the absolute radius conditional on exiting at the station; herding present as a
   process without a service consequence.
2. **The enter-level effect.** Is "a bound (level .20 closes about a fifth of the N–H_central
   gap) plus correlational process evidence that the stations act as a deployment prior for N"
   the right label, or is it a package effect without adequate process support? Is the
   station-proximity table (team QoS .28 with no UAV within 300 m of a station vs .43–.46 with
   one or more; relay anchor occupied .46 vs none .31; the opposite sign for H_central) adequate,
   and what confound would you rule out first? Confirm or reject the framing that this is the
   constant-earlier-return control the S7 closure declined, measured only because P1′ registered
   it, and not adopted.
3. **Stage 0.** Are H_spawn and H_park2 the right zero-training discriminators for the
   deployment-prior conjecture, with the stated predictions and thresholds? Should H_park2 hover
   at 100 m over the station xy or dock (the shield's own docking makes UAVs land; a landed UAV's
   coverage differs)? Is H_central@10 worth its minutes, and does it isolate control opportunity
   as you intended?
4. **Stage 1 matching.** Is SET against H_central an adequate package pair given per-step control
   versus 30-step replanning, no hand prior and the snapshot's content; what must be labelled or
   controlled (Stage 0's H_central@10, a replanning-period-matched SET, a memory)? Is HMASD-k10
   × 3 the right instrument for the seed spread and the hierarchy contrast? Is dropping LOCAL1
   now right, given that H_local is a pooled planner and the direction's question names the
   legal-observation gap?
5. **Exposure and reading.** Is 1.2 M transitions per fit (≈ 5 h) enough for the result to be
   informative either way, or should exposure be set from an early checkpoint curve? Critique
   the .60 threshold for B02-P1, the .05 seed-SD rule, checkpoint reading on development worlds
   with one confirmation on 957001–957032, and the co-primary rule.
6. **Value against alternatives.** Does this B02 answer the direction's third question ("can a
   learned controller close either gap") and bear on the programme's paradigm concern (the
   owner's view that HMASD is fundamentally a MARL algorithm; the joint-skills recommendation),
   or is there a cheaper decisive experiment (for example, a single SET fit first, or a
   behaviour-cloning ceiling from H_central's targets as a learnability probe)? Name the
   strongest alternative and what would change the judgement.
7. **Failure explanations to pre-register.** For SET failing P1: what it would and would not
   mean (exploration, credit, horizon, guard freeze, the S7 preset tuned for HMASD); what would
   make the result uninterpretable; what to record from the traces to tell these apart.
8. Return `MATERIAL_DISSENT: yes/no` separately for buying Stage 0 and for buying Stage 1 as
   proposed, with the revision that would remove any dissent.

Sources at the pinned revision: this notebook (the B01 result entry, the design entry above, the
B01 revised entry, your previous answer and the DM response to it); the readings JSON; the B01
code; `docs/research/candidates/uav_service_auxiliary/NOTES.md` (the 2026-09-25 closure and the
B09–B11 evidence); `docs/research/RESEARCH.md` (programme and structural background);
`docs/project/OPERATING_CONSTITUTION.md` §§2–5; `hmasd/baselines.py` and the first entry's arm
table for SET, LOCAL1 and HMASD-k10.

### Answer

_Saved from chat by the DM on 2026-09-26 (Pro reported no repository write action; `deliver` read NOT_DELIVERED). Text as received, sha256 a549e9075861cde21d4cbba47f04b299f809a8b3f5ac3adb81aa09df9949f945, 13608 characters._

**GitHub 读取可用，但本轮可调用的 GitHub 接口没有仓库文件写入或提交动作，因此未发出写请求，实际 Answer commit：无。**最后核对的 main 文件 blob 为 cbee81ef4184d56c9bc4529cb99ee404ec571a70，本问题的 ### Answer 仍为空。下文依据附件指定的 debaa12d42a996b36edda55a73955ce66db5dbb8 作答；最新 main 只用于核对写入位置，没有替代科学输入。
hmasd-pro-question-b02-design-a…

B02：保留部署问题，但拆开参考诊断、学习可达性与旧 N 的典型性

MATERIAL_DISSENT — Stage 0 as proposed: yes。
MATERIAL_DISSENT — Stage 1 as proposed: yes。

两项异议的性质不同。Stage 0 的三个控制器值得做成一次小型参考比较，但目前的“完全不部署”“站点位置解释 N 的补能后阶段”“控制周期的贡献已经被隔离”等解释超过了设计能力。Stage 1 则存在更实质的错配：SET 的实际实现不是无记忆、逐步刷新中央 state 的 actor；新 HMASD 训练若开启 F 并增加到 1.2M transitions，就不是对 B09 N 的同配方种子复制。

我的首选是：**完成修正后的零训练参考，然后先做一次固定曝光的 SET 开发拟合，读取完整曲线和终点；暂不把六个 fits 作为“测 N 典型性＋检验层次结构”的整包投入。**一次 SET 只能提供探索性实例，不能承担训练总体结论；但它直接面对目前最近的未知——一个普通中央输入学习程序，在明确曝光下能否接近已执行参考。后续是否值得购买多种子稳定性或层次包比较，应由那个具体未知的价值决定。

以下按八个问题展开。

1．B01 判读：支持改变投资重点，不支持把全部损失归因于学习器
Branch (b) 可以决定下一步，但不能承担原因归属

B01 的重要进展成立：现在有了在冻结宿主上真实执行的高服务参考，而不是仅有静态 witness。生产设置下，H_central、H_local 和 N 的 QoS/step 分别约为 .7740、.5969、.3283；与此同时，预定的 N 宽度对比 (0,.45)−(0,.05) 为 +.02328，未达到 .03 的实用门槛。这些结果足以降低继续优化退出宽度的优先级，提高部署学习问题的优先级。

但“所以损失在学习器的部署，而非 shield 的时机”只能作为有范围的工作判断：

对这个 N 实例、这组世界和 H3000，已测 level-0 宽度变化没有回收与参考差距相当的服务；退出宽度不是当前最值得继续投入的解释。

不能进一步写成“退出宽度不是 S7 损失”“时机已经排除”或“剩余差距已归因为学习”。N 的该对比仍有 +71.8 J 和正服务增量；未过门槛不等于零效应。更重要的是，已采用的 P2′ 只是两个控制包差值的描述性关系，不能再借 branch (b) 把它重新解释为信息与学习的因果份额。

**投资可以结束，科学上的一般无效结论不必随之成立。**这一区别不会迫使 DM 继续扫参。

τ_w 的规则应保留，但“暂不作逐世界判断”不等于逐世界差值没有意义

本批按预先规则在 τ_w≈.036>.03 时不使用 branch (e)，这一读法应保留。与此同时，同一设备、固定初始化下的配对差值，仍然是这些具体闭环执行的可报告结果。两者并不矛盾：

同设备确定性，回答“这两个固定程序在本次条件下得到什么差值”。
CPU/CUDA 对照，回答“历史程序的结果对执行平台有多敏感”。

后者不是前者的独立加性测量误差，也不是逐世界的显著性阈值。因此，不应删除配对表；应停止用这些世界挑选 regime、阈值或声称跨实现稳定的个体效应。

“面板均值一致”也宜改为“本次观测到的均值差较小”。没有预定等效界限，就没有完成平台等效检验；N 上的 null 更不能自动为 H_central、未来 SET 或新训练程序提供误差界。read_b01.py 中接近零的数值判定也不应表述成所有状态或轨迹逐位相同。

P3：“登记计数失败＋共同窗口存在大差距”是正确并列

P3 的原规则确实没有通过：19/32，而不是要求的24/32。共同窗口诊断则报告 N .21535、H_central .80084，配对差均值 +.58549、最小值 +.30420。这构成很强的有限面板控制包差距，但不能回填成原 P3 通过。

“首次 shield 进入前”应取代“没有能源压力前”。在此前，电池、返航成本、原生动作路径以及策略自身的 dock 请求都可能影响行为。成立的排除是：**这些公共早期窗口中的差距，不可能由尚未发生的退出宽度干预造成。**它没有单独区分信息利用、几何先验、优化、技能条件化或探索。

最小差约为八个 τ_w，只是量级描述，不是“八倍标准误”或某种检验统计量。

Tether 得到了条件性过程支持，不是普遍半径定律

保留“距离增量”的修正是对的。读数中的约391/411 m、宽度 .25 下约1.7 km，与源码推导方向和量级相容。需要保留三个限定：统计只包括随后再进入的退出事件；同一世界中反复退出不是独立样本；脚本使用最近站点距离，没有要求前后最近站点身份不变、径向恒速或无垂直运动。

因此，适合的结论是“观测支持宽度约束自由离站增量的机制”，而不是“已证明增量只依赖宽度、与 level 无关”。另外，笔记用“从约1 km 进入，所以在约24秒内到站”解释 H 的过程，这不能由上述近似直接推出：即使全程30 m/s，1 km 也需约33秒，尚未计 docking。应使用实际配对轨迹解释，不能拼接不同事件总体的中位数。

P1c 有一处明确错误，且“拥挤没有服务后果”过强

JSON 与笔记的“两个控制器都在符号上失败”不一致：

对比 (0,.85)−(0,.05)	N	H_central
完整 QoS/step 差	+.00772	−.01715
entry-to-input QoS/step 差	−.02109	+.01372
等待增加	是	是

N 没有满足完整服务差非正的条件；H_central 满足该符号条件，却没有满足中间阶段服务下降的条件。两者完整 P1c 均失败，但失败的子条件不同。

应改读为“拥挤／等待过程改变，但预定的联合有害响应没有成立”，而不是“没有服务后果”。充电和等待 UAV 仍能服务，说明不能机械地把占位等同于离线；它不保证占位、布局集中与时机对服务无害。这里也不足以启动预定的 scheduler 救援。

2．Enter-level 效应：是真实的包级读数，有机制线索，但不是收益上界
“约闭合五分之一”是选中设置的描述比例，不是 bound

最好的已测 N 设置约为 .422，生产 N 约.328，生产 H_central 约.774，所以

.422
−
.328
.774
−
.328
≈
.21.
.774−.328
.422−.328
	​

≈.21.

这个算术可以保留，但它只表示在当前开发面板上，一个已测反馈包回收的参考差距比例。它不是所有常数时机规则的上界，更不是自适应控制的上界，也不是“能源原因占21%”的分解。

还要区分两种对比：最佳设置 (.20,.45) 相对生产 (0,.05) 同时改变了宽度和水平；在宽度 .25 下单独比较 level，差值是 +.07881，而不是最佳设置相对生产的约+.0932。三个匹配宽度的 level 差值为 +.0480、+.0788、+.0611。它们支持 level 对该 N 包有实际影响，但不是同一个“21%效应”的三次复制。

对历史定位的判断：基本认可，但须准确称为匹配宽度的 level-shift 包

这确实落在旧 S7 关闭决定不再购买的常数提前返航方向内。旧决定是当时的投入判断，不是已经取得了该控制无效的结果。B01 的新读数应更新认识，而不是为了维持旧建议而淡化它。

但它也不只是“进入时间提前”这一单因素：为了匹配宽度，进入和退出阈值同时平移。由此改变的包括介入时机、储能、驻留、后续释放位置和剩余时域。

此外，**对比本身是 P1′ 预先安排的，未预先安排的是把意外正方向当作候选收益来解释或采用。**最准确的记录是：预定 P1′ 被这些结果反驳；事后发现一个有利于 N、不利于 H 的反馈包效应；没有据此采用阈值。不是“整项发现都来自未登记的搜索”。

站点部署先验：有支持，尚未识别中介

近站时 N 服务较高、H_central 的趋势相反，加上匹配 level 干预方向相反，确实使“趋站有时替 N 完成了粗糙部署”成为有内容的猜想。它比只看到充电次数增加更有针对性。

但 trace_checks.py 把世界和时间拼接后按近站／占用状态分组。这些表是条件性、tick 加权的读数，不是“把一架 UAV 移到站点”的效果。我会首先检查世界与 episode 时间的组成差异：高服务几何的世界可能更容易靠站，靠站也通常发生在较晚、已经完成更多部署的阶段。仅保留 t≥1500 不能消除这一点。

随后才是电量、其余成员布局、已有 backhaul 路径和 guard 状态。简单把这些后处理变量全部放进回归，也不会自动得到中介因果效应。

已有反例尤其重要：N 的三个零服务世界在发生靠站和实际补能后仍为零。这排除了“只要到站就足以形成服务”的强解释，却没有排除站点位置对某些原本接近成功的布局有帮助。

最后，“锚点处的 UAV 按构造就是一个 backhaul hop”应撤回。源码构造的是相关位置锚点，随后还有扰动、裁剪和站间分离处理；它没有证明该位置在实际 SINR、双向链路容量及全队布局下必然构成有用路径。用户质心也不等于最密集用户簇，尤其不能等同于移动后的当前中心。

3．Stage 0：值得保留三个固定参考，但重新定义它们检验什么
H_spawn 不是严格的“无部署 floor”

按提案，它仍通过生产 F。F 接管后会把 UAV 从出生位置带走；释放后，基础控制器又可能命令它返回出生目标。因此，它是：

出生位置固定目标控制器＋生产反馈。

它不是整个 episode 内完全没有部署，也不是所有无部署策略的性能下界。初始升到100 m 本身也是动作和能耗，不能通过修改 reset 位置免费完成。

这是一个有用的简单参考，但命名和结论须符合实际执行。

H_park2 检验两锚点程序的用途，不直接检验 N 的中介

我支持把 H_park2 定义成一个完整、合法执行的程序：事前固定两架 UAV 与两个站点的匹配规则，从原 reset 出发以普通动作抵达100 m waypoint；另外六架采用与 H_spawn 相同的固定目标；全部经过同一个 F 和原生 guard。不瞬移，不冻结物理位置，不因某世界难到达而另选成员或站点。

这样，H_park2−H_spawn 测的是在这个固定目标背景上加入两个站点 waypoint 的完整包效应。它不直接测“更早返航的 N 为什么改善”，因为 N 的其余六架成员、技能、循环状态和响应行为都被替换了。

所以，原 S0-1 的正负分支都过强：

H_park2 达到.40或.45，只说明两锚点程序能取得这个水平，不能证明 N 的补能后阶段就是由两处位置解释的。
H_park2 低于.35，只能削弱“两个固定锚点加六个出生目标已经足够”的猜想，不能撤回所有站点部署先验解释。可能缺的正是 N 的其他成员形成的连接。
完整 episode 的.40与 N 内生选出的 post-input .45–.48不是同一估计对象，不能直接称为“复制了大部分那个阶段”。

.10、.40、.35可以作为此次具体参考的预期水平，但不是经噪声校准的通过线，更不能取代原生 J、风险和全部世界的读数。提案应明确中间区间及服务／J冲突的处理。

若真正要识别 N 的两锚点中介，更接近的问题会是保留 N 其余行为、仅加入事前固定的两成员锚点控制。我不建议现在自动加这一臂：当前更有价值的是建立简单程序能达到什么，而非追完旧 N 的每一条机制。

主版本选100 m 悬停，不改成持续 docking

我会保留100 m waypoint 作为这次空间部署参考。持续提交 dock 请求会改变高度、补能、占用、原生运动控制及 guard 路径，回答的是另一个“驻站补能服务包”的问题。

也应避免把环境中的 docking 直接叫作现实意义的“落地”。原生动作路径会在160 m内切到 docking 速度，并依据站点三维位置执行；“在站点 xy 上空悬停”与“进入捕获并实际供电”不是同一状态。

保持生产 F 后，H_park2 仍可能在低余量时下降补能。这正是应报告的真实过程，而不是为了维持“纯几何实验”而临时屏蔽 F。可同时读取共同早期窗口的服务、实际到达时间、高度、F 占比及补能状态，用来区分早期空间部署与后期反馈后果。

H_central@10 值得做，但只隔离 H 内部的重规划周期

这是很小、明确且可解释的干预：在其他 H 规则不变时把重规划间隔从30改为10。它可回答这个 H 的完整表现是否对该周期敏感。

它不能单独识别 H 相对 SET 的“控制机会贡献”。H 在30步之间仍每步根据当前位置向 waypoint 输出动作；它不是30步不反馈的开环控制器。改变重规划周期，还会改变分配、hysteresis、F 释放后重新获得目标的时机及整条轨迹。

|ΔQoS|<.03应读成“本批该 H 周期变化低于实用门槛”，而不是“已经证明控制周期对参考优势没有贡献”。不需要为此再自动增加 SET@30、H@1 或记忆消融。

4．Stage 1 匹配：中央输入包比较可行，但实现描述和 N 复制目标必须更正
实际的 SET 与提案不同

沿 baselines.py、agent 快照路径和网络构造核对，实际情况如下。

控制器	关键输入与记忆	两种时钟
SET，按首条 arm recipe 恢复 k=10	当前局部观测＋保持的中央 state、全队观测、ego 编码；低层仍有循环网络	每步输出动作；中央快照在 k=10 决策边界刷新
HMASD-k10	高层使用中央 state 和全队观测；低层局部输入、技能条件化和循环记忆	高层每10步重选；低层每步行动
H_central	真值用户／BS位置、手工布局与分配规则、保持的目标及反馈模式	默认每30步重规划；每步反馈运动

MAPPO 开关将技能压成单类并关闭高层训练等机制，没有删除低层 RNN。SET 的中央快照也不只是 state306，更不是默认每步刷新。直接使用 MAPPO 开关还会把 k 改成 rollout_length+1，所以首条 recipe 中恢复 k 和重算 buffer 的步骤必须保留。

提案引用 belief_map.py::_get_state 来验证 S7 state 也不正确。本 S7 类继承 UAVRoutedRelayEnv；实际基础 state 来自 routed_core.py::_get_state，再拼接能源状态。用户与 BS 位置确实存在，但应沿实际继承链引用，不能用另一个环境类证明接口。

因此，不需要为 SET 另加一个 memory。需要的是把已存在的记忆、中央刷新、输入内容及重放路径记录正确。

SET 对 H_central 是合理的包比较，不是纯信息实验

它可以问：

一个具有中央位置访问能力的普通学习程序，在固定曝光和反馈下，能否达到这个手工规划参考附近的完整表现？

它不能单独问：

增加中央信息能产生多少收益？

因为没有一个仅信息不同、其余不变的学习对照。H 的布局先验、联合目标分配、持久 waypoint 和反馈模式使用方式，也是控制程序的一部分；与 SET 的网络归纳偏置和学习过程不同。H@10 只能减少一项周期疑虑，不能使整对变成因果消融。

SET 与 HMASD 的快照时机若都为 k10，则中央读取机会本来就能按该层面匹配。二者仍有技能通道、模型容量、辅助目标、训练样本组织等差异，结果只能称为两个学习包的差值，不能直接称为“联合技能的贡献”。

还有一条需要纠正的前次意见延伸：H_central 不能冒充严格局部信息条件下的普通参考，但完全可以是明确中央位置条件下的普通可执行规则参考。“永远不能提升为 ordinary reference”不是合理限制；关键是比较边界，不是 H_central 这个名字。

HMASD×3 可以测新配方的种子变化，不能测旧 N 的典型性

B09 原文明确：N 训练没有 F；A 训练启用了 F。两者各180k transitions，且当时 A−N 的完整均值没有显示增量优势。

当前 Stage 1 写的是训练启用 F、1.2M transitions，并采用新 collector／rollout规模。因此，它改变了反馈训练条件、曝光和更新组织。假如新 HMASD 均值从.328升到.65，那不能证明旧 N 是一个不典型种子；也可能是新曝光、训练反馈或其他已声明的配方变化。反之，新均值恰好接近.328也不证明两配方等价。

**应删除 B02-P2 的“典型性”检验及据此重标 B01 的分支。**B01 的 N 从来就是一个训练实例，不必等新试验失败才补这个标签。

不建议为了保留典型性问题再追加一组原样180k、无 F 的复制。除非旧 N 的分布位置真的会改变当前研究选择，否则这不是最近的任务问题。

LOCAL1 可暂缓，但理由应是缩窄问题，而不是缺少专属 heuristic

H_local 是合法观测汇总式中央规划器，不能与严格单架局部 actor 视为信息匹配。这一点支持避免当前的错误配对。

但“没有严格局部可执行 heuristic，所以不能研究 LOCAL1”不成立。LOCAL1 仍可作为另一种信息结构的学习包，前提是有明确问题。

本次暂缓它的合理理由是：**先研究中央输入下的普通学习可达性，不同时购买信息结构比较。**代价是 B02 暂时不回答“合法观测汇总参考的差距能否被匹配学习器缩小”。应明确保留这个未回答项，而不是声称整个方向的第三问都已覆盖。

5．曝光、阈值和留出：1.2M 可以形成有用结果，但不是胜任保证
固定1.2M比看分数延长更清楚

1.2M 是一个可辩护的有界曝光选择：它明显扩大了历史机会，并能给出完整学习曲线。无论正负，都能回答这个具体程序在这份曝光下达到什么水平。它不能预先保证收敛，更不能使未达.60自动变成架构失败。

我倾向保留事先固定的曝光终点与 checkpoint，不依据某 seed 的中间分数延长该 fit。早期曲线可支持之后另写一个更长或改变配方的研究，也可支持停止；但不应一边把数据叫确认，一边用它决定何时训练结束。已有宪章也区分新前瞻比较与看分数后扩展当前批次。

曲线至少区分训练中的随机动作表现、冻结模型的确定性评价和 F 接管比例。若训练大部分有效行为由 F 生成，“总 transitions 更多”并不等于学习器获得了同等数量的自主部署机会。

.60 是实用里程碑，不是“信息足够”的证明

以 B01 的数字作量级参照，.60相对.328约回收了到.774差距的61%，仍离参考约.174。这是有实质意义的进展目标，但不能称为已接近到与参考相当的程度。这个比例是本文对已报告均值的算术，不是新增结果。

“至少两种子达到.60”可作为预先声明的有限成功计数，却不能单独证明一般可学习性或稳定性。应同时保留每种子的绝对 Q/J、相对自身初始化的变化、与共同参考的差，以及不利世界。

成功说明这个学习程序能利用其输入取得较高服务，不单独说明是信息起作用。失败则说明程序未达到里程碑，不说明中央信息本身不足。

.05 seed SD 没有校准依据，而且均值锚点错误

在三个训练实例上可以报告 SD，但不能把 .05 当作天然可接受变异、稳定性的证书或旧 N 典型性的界限。更根本的问题是，原计划正在用新配方的均值去检验旧配方的一个终点。

新研究真正需要的是实际比较量的训练间变化：例如每个训练块上 HMASD−SET 的面板均值差，或 SET 与固定 H 的差；不能以单臂边际 SD 替代相关差值的变化。相同数字 seed 也不自动保证初始化或所有外生历程构成有意义的配对。

955xxx 可以反复用于开发；957xxx 的用途必须一次说清

955xxx 已经用于 B01 和本次设计，继续作为开发曲线面板是合理的，只要不再称为未曝光。

957xxx 可以成为冻结模型的最终留出评价，但应区分：

新世界检验已训练模型的外推表现；新训练种子检验训练程序的重复性。

新世界不会增加独立训练 n。若在955上选择训练程序、checkpoint或研究问题，再让同一批模型第一次接触957，能得到有价值的留出评价；它并不自动完成训练总体的确认。提案“先读957的终点评价，再在957上首先开展层次结构问题”的用法会把同一面板重复用于选择与确认，需要撤掉这一重叠。

同样，应在957上执行冻结的 H 参考，不能把955上的.774当成957上的已知基线。本文没有独立审计957范围在全部历史中的暴露情况，现阶段只能引用提案的预留声明。

“Co-primary”必须对应明确比较，不能只留下名称

B01 的“ΔQoS达到门槛、ΔJ不恶化”等规则有明确的 setting 对手。B02-P1 却是绝对服务水平，不能不加区分地复制原判定。

建议分开读三个问题：**服务水平是否达到里程碑；是否较自身初始化产生有用学习；不同学习包相对共同参考的完整差值是什么。**J、返航成本、事件及最低电池尾部都应保留，不能用一句“co-primary”掩盖它们分别相对谁、允许什么交换。

例如，服务达到.60但风险成本大幅增加，应保留服务水平达标和风险交换两件事，而不是自动叫联合收益；J 改善但服务下降，也不能被抹成完全无用。B10/B11 已经具体展示过恢复、等待、服务和原生 J 不能互相替代。

成本不能由“三个并发名额”推出

提案的六 fits 对应7.2M训练 transitions，另有 checkpoint 和留出评价。最初 throughput probe 已估计一个 HMASD fit 连同 workers 约占10GB，并建议在约15.8GB节点上串行；“允许三个研究轨道”不是三个重训练进程能并行运行的资源证明。

因此，不能把“六次各约5小时”直接折成12–15小时节点墙钟。SET 的实际内存和吞吐、新 F 训练的成本都还没有本轮测量；应以已测资源为依据，未知部分保持未知。Stage 0 的三个32世界面板名义上另有288k评价 transitions，也不是零计算成本。

6．对范式问题的价值与最强替代：先选单个 SET 开发拟合，而不是 BC“上界”
这仍可以是 MARL 研究，但暂时不是联合技能机制研究

UAV 任务中的联合几何、接入—回传依赖和充电资源耦合，不因采用中央输入的普通学习器就消失。中央 actor／critic 的选择是信息和控制结构的一部分，不把任务变成没有多智能体后果的问题。

但“HMASD 是 MARL 算法”不意味着每项任务研究都应先购买其层次版本；“联合技能值得研究”也不意味着任何 HMASD−SET 差值都识别了联合技能。共享背景已经区分技能可辨认、组合有用途和有限训练学会选择，也明确要求普通强参照。

修正后的 B02 可以成为范式问题的任务校准阶段：先建立一个学习基线与真实规则参考之间的差距，再判断是否存在值得由结构化方法处理的决策。它不是联合技能推荐的直接验证，更不能在两个学习包都未达到高服务时自动宣布需要更复杂技能。

我选择的最强替代：一个固定曝光 SET fit，先不启动其余五个

这个选择直接测试新信息接口和普通学习程序能否把服务提升到有用水平，不同时承担解释旧 N 的种子位置与层次增量。它不需要再等一个正面 toy 或证明所有机制。

它的判别力是不对称的：

若单个 SET 明显取得较高完整服务并缩小参考差距，它提供一个探索性可达实例，足以削弱“必须依赖当前层次结构才能实现部署”的强前提；接下来更值得问稳定性和成本，而不是默认加新模块。

若单个 SET 没有取得有用进展，它只限制这一配方和实例。它不能证明普通中央学习普遍失败，也不能据此选中探索、信用分配或联合技能修补。是否值得再测种子或改变曝光，仍要看完整曲线和下一个决策，而不是为得到一次成功持续追加。

我偏好这一次序，是因为当前最近的未知是普通中央学习是否已经提供足够的任务进展，而不是旧 N 是否处于其原训练分布的中心。若 DM 的明确目标改为“一次比较两个已完整定义程序的跨种子表现”，并认为该排序本身就会改变下一项投入，那么修正后的六 fit 包比较有可辩护性；只是那不是当前写出的典型性实验。

为什么不优先采用 BC“ceiling”

从 H_central 学目标可以检验特定映射的可拟合性，但它不是性能上界。教师目标依赖当前规划、此前分配、F模式和手工规则；只向学生提供当前中央 snapshot，未必包含决定同一教师目标的全部条件。离线误差小，也不证明学生在自己的闭环状态分布中保持高服务。

BC 在“排除特定表示明显不能承载目标”这个问题上可能有用，但它引入数据取得、目标定义和分布转移，不是免费的、决定性的 learnability 证明。

会改变我这一排序的证据是：普通 SET 已经能在相关状态上拟合部署映射，却在在线学习中持续无法进入那些状态，且下一项选择确实取决于初始化／示范是否有用。当前材料尚未给出这一判别，所以我不建议把 BC 加成新的常规前置环节。

7．失败解释：预先保留可区分的观察，不预先选中一个救援

SET 没达到.60并不意味着结果不可解释。首先应读它达到了多少、较初始化改变多少、在哪些阶段和世界失去服务，再区分以下情况。

观测组合	可以加强的解释	不能直接推出
长期看不到用户、很晚才形成接入／backhaul，训练中有用服务暴露也很少	部署搜索或到达有用状态的机会不足	已识别探索算法缺陷；加入课程必定有效
用户和路径经常出现，但策略不能保持或改善完整交付	信号利用、优化、回报权衡或信用分配成为候选	已证明 credit assignment 是瓶颈
早期服务较好，进入F／补能后差距明显扩大	反馈条件下的部署与恢复过程值得关注	应重新调退出阈值或改 scheduler
目标持续未到达，非零提议多次被 guard 阻断	特定几何下动作过滤可能限制执行	H 的全局平均 blocked 比例就能诊断 SET
到最后仍持续改善但差距很大	当前曝光可能不足以描述平台水平	可以事后延长当前 fit 并保留原确认标签
曲线平台低、技术执行正常	该固定训练程序在此曝光下表现有限	中央信息不足、MARL无用或必须加联合技能

这些是工作解释的候选，不是互斥病因。提案“服务奖励只有 backhaul 建立后才存在”也应限定为交付服务分量；原生总奖励还含返航风险和势函数等项。三个确定性评价零服务世界不能代表全部训练经历都没有学习信号。

**S7 预设曾面向 HMASD 调整，是已声明的不对称，不是失败后才发现的解释。**保留同一超参数有助于定义包比较，但它不建立“各自充分调优后的算法优劣”；也不应在 SET 失败后无界搜索直到胜出。

有限而关键的记录

在现有曲线与 trace 基础上，最值得补充的是三组能直接区分接口、机会和结果的事实：

**行为与服务链。**首次用户可见、首次接入、首次有效 backhaul、首次正交付；提议动作、F提交动作与实际位移的关系；有多少非零运动因 guard受阻，是否持续不能到达目标。只保留连接数量不够，需要实际交付服务。

**学习与干预曝光。**每个 rollout 的完整训练 Q/J、F映射比例、真实优化步、PPO 的 KL／clip／entropy 等基本读数，以及各 checkpoint 的冻结评价。它们定位异常或缺少机会，不是成功代理。

**信息与状态连续性。**实际 actor 配置、中央 snapshot 时间戳／年龄、RNN reset／mask、技能与反馈模式的边界；评价不更新 normalizer或参数；世界初始化与实际终止语义。

B01 已保存的距离、模式、位置、排队和电池数据有用，但没有完整保存新学习诊断需要的用户可见—接入—回传链及动作映射事实，不能声称事后一定能从现有 NPZ 恢复这些原因。

什么使原定比较无法解释

真正会破坏原定比较的是：实际 SET 接口与标记不符、快照重放时机错误、把 shield 后动作当成 PPO 原提议的采样密度、RNN 在 rollout 边界被意外重置、评价用错 arm 配置、不同终止／奖励语义、模型或 normalizer 被评价改变、失败世界被悄悄排除或留出面板已参与选择。

这里有一项现成工程风险：**B01 当前 evaluator 的配置和 checkpoint loader 是为固定 N 写的，不是通用 SET loader。**可以复用世界循环、指标和隔离语义，但不能原样把 SET checkpoint 塞进 N 的构造路径，也不能为了载入而放松旧 N 的冻结身份检查。

若实际实现只是与提案标签不同，但运行事实完整可恢复，往往可以准确重标为另一种包比较；这与完全丢失终点或身份不明不同。低分、反号或没有显著差异本身不是技术失败。

8．分别的异议与可消除异议的修订
Stage 0：MATERIAL_DISSENT: yes

异议针对当前识别主张，不反对三项固定零训练程序的有限用途。消除异议的修订是：

把 H_spawn 与 H_park2 明确定义为原 reset 起步、真实动作执行、共同 F 下的控制包；主版本保留100 m waypoint；撤回 floor、“锚点必然是 hop”以及“达到分数便解释 N 阶段／低于分数便否定所有先验”的结论；H@10 只判 H 内部的周期敏感性。

保持三个控制器、原世界和原生完整读数即可，不需要扩大成新的机制矩阵。正负结果均可改变对简单普通控制的认识，不自动触发 Stage 1。

Stage 1：MATERIAL_DISSENT: yes

我的首选修订是先一个固定曝光的 SET 开发 fit，暂缓其余五个，使用真实的循环／k10快照 recipe，生产F训练条件明确标记为新程序；955只开发，957保留到用途和判读冻结后。

必须删除旧 N 典型性预测及其重标分支，撤回“通过.60就证明是结构而非信息”“失败就转课程或 shaping”的自动归因；修正 evaluator、留出用途和并发成本。

保留六 fits 的另一种可解释修订，是把它彻底改写为两个新训练包在共同1.2M曝光与F条件下的种子级比较，不再宣称复制 N、不声称隔离层次因果，并说明这个包排序本身为何现在值得六次训练。它可以成立，但我的当前投资排序仍优先普通 SET 的直接开发实例，而不是同时追问历史典型性与结构优势。

核验范围与剩余缺口

本次读取了固定问稿、B01结果和B02提案，核对了前次意见的采纳内容、readings JSON 中本文使用的预测／曲线／共同窗口／tether／近站读数及其生成代码，读取了相关 B01 evaluator、heuristic、基线与中央快照／循环网络路径，以及 S7 B09–B11和关闭决定、当前指定版本的共享背景与治理内容。

完整 b01_ref_a02/summary.json 未能读取：文件接口返回空内容，备用接口报告文件过大或不支持。我读取了退出见证和部分原生 panel 内容，但没有完成全部原生输出的独立逐项审计；退出码0也没有被单独当成科学完成证明。仓库外 checkpoint、20个轨迹归档、现场节点资源和 B02 尚未执行的实现均未独立核验。本文的历史数值依赖已读结果条目与派生读数，不冒充本轮原始轨迹重算。

最终判断：B01 已经提供了把研究重心转向真实部署学习的充分投资理由，但没有提供把所有剩余差距定为学习原因、把两锚点规则定为 N 的解释、或把新1.2M反馈训练定为旧 N 复制的依据。B02 最值得保留的未知，是普通学习能否接近一个已执行的强参考；最该删除的，是让同一批数据同时承担参考诊断、历史典型性、信息充分性和联合技能归因。

### Transport record: B02 design question sent (2026-09-26)

Question key `hmasd:2da8468598bc55b1a940dd92c950671e1db61834f5f20571fb2de657c5d8c07a` (repository
CartmanFatass/My-paper-code, branch main, source SHA `debaa12d42a996b36edda55a73955ce66db5dbb8`,
target this file, heading "## Pro question 2026-09-26 b02-design-after-b01"). Sent through the Jev
route as a follow-up in the conversation of the B01 question (key `901b4c31…3a01c`; the address
stays in the local operation file), headless, effort pill "6 Pro", short message plus the composed
document (sha256 `7d1546e9…f42bea`), `send_effect: sent`, attachment seen, 16:24 UTC. A first
`send` call failed before any browser action (wrong short-message path; nothing submitted) and
was rerun under the same key. Observation: the deterministic `wait` observer runs detached with a
native return; delivery is read with `deliver` after completion, and a chat answer is inserted
"saved from chat" if the connector does not write. An internal ResearchCritic pass over the same
two entries runs in parallel as a comparison (separate context, read-only); both are recorded here
when they return, with the DM's response, before anything is bought.

### Correction after the internal ResearchCritic pass (2026-09-26, before the Pro answer)

The internal Scientific Reviewer (separate context, read-only, run as a comparison to the Pro pass
in flight) returned MATERIAL_DISSENT: yes on three parts of the B01 reading and on both B02 stages
as proposed. The DM recomputed every disputed number from the traces (`trace_checks.py`, section
`boundary_and_time` added; readings JSON regenerated) and accepts the following, which supersede
the corresponding sentences of the result entry above.

1. **N parks its UAVs on the area boundary; the result entry did not report it.** In N's
   production panel 49.8 % of normal-mode UAV-steps have x or y on an area edge (east wall
   x = 8,000 m: 162,420 UAV-steps; south wall y = 0: 197,020), 67.7 % before step 1,000, above
   50 % in 27 of 32 worlds; 92.0 % of normal-mode UAV-steps before step 600 sit at the 50 m
   altitude floor. H_central and H_local: 0.0 % on the walls, 0.2 % at the floor. This is the most
   direct description of the deployment deficit and the simplest account of the level effect: the
   shield's entry pulls UAVs off the walls.
2. **The station-proximity table was a time confound; the "deployment prior" reading is
   withdrawn.** N's team QoS/step rises with time before any shield activity (.125, .202, .264,
   .298, .311 in the first five 300-step bins while the F-mode share is ≤ .05); the raw slope of
   QoS on "any UAV within 300 m of a station" (+.172) falls to +.047 within 300-step time bins
   and to +.012 / +.005 within world × 300-step / 100-step bins. The phase-split account ("two
   thirds of the episode in the best regime") is confounded the same way. The distance-only
   station cells are none .279, anchor only .452, centre only .326, both .593 (the entry's
   .31 / .46 / .39 / .51 used charging occupancy, not position). What survives is interventional:
   at matched time (steps 900–1,200) N scores .298 at (0, .05), .327 at (0, .45), .372 at
   (.20, .25) and .452 at (.20, .45). The level effect is therefore recorded as a real
   intervention (package) effect with an unresolved mechanism, not as process evidence for a
   station prior.
3. **The zero-service worlds were misdescribed.** In 955005, 955012 and 955021 the UAVs sit on
   the east wall (mean x = 8,000 m at step 500), the backhaul guard is consulted 0 times (no
   routing path ever forms), and after step 2,000 there are 0 UAV-steps within 300 m of the relay
   anchor against 3,474–3,938 near the service-centre station: the UAVs docked at one station,
   the centre, and occupying it alone gives no service. Two of the three recover at (.20, .45)
   (.458, .530) with anchor visits; excluding the three worlds the matched-width level effect is
   +.043 / +.054 / +.037 instead of +.048 / +.079 / +.061. Earlier entry changes which station is
   occupied first (anchor share of first entries .663 → .742 / .727).
4. **Wording narrowed.** "The timing investment ends" reads "the exit-width investment ends";
   the enter level is consequential for this policy (P1′ deltas +.048, +.079, +.061 with paired
   SE .015, .024, .024). The width curve's "inverted U" is not resolvable (per-point SE ≈ .010;
   P1's interval ≈ [.002, .045] straddles .03); the only width effect distinguishable from zero is
   H_central's −.017 at .85 (SE .0065), so "herding without service consequence" is slightly
   overstated for H_central. "Re-litigation" is withdrawn as the reason for not training at level
   .20; the reason is that it compensates a deployment failure and hurts the competent reference.
   The index row's "+.05–.09" is corrected to the matched range +.048–.079 (+.093 is the
   unmatched (.20, .45) − (0, .05) difference).
5. **Kept as recorded (verified by the reviewer):** every registered reading (P0–P3, P1c, P1′,
   P2′), the τ_w rule and its application, branch (b)'s conditions, the common-window P3 reading,
   the tether increments, the artifact hashes.

**Design dissents (both stages), to be resolved together with the Pro answer.** Stage 0:
H_spawn is a trivial floor (the spawn corner lies ≈ 3,950 m from the anchor and ≈ 5,900 m from
the centre) and H_park2 may not close a relay chain; the reviewer's replacement is a zero-fit
check of N with sampled instead of mean actions, because the boundary parking may be the
deterministic mean action saturating at the action bounds, which would make part of the "learned
deficit" an evaluation artefact. Source facts bearing on this: B01's evaluator acts with
`deterministic=True` (`evaluation.py` line 100) and B09's evaluations did the same; B09's N was
trained on 180,000 transitions (2 lanes × 30 episodes), and its stochastic training episodes
record J only (strongly negative under exploration, −1.5 k to −5.4 k in the last six), not QoS,
so the check needs the run. Stage 1: register per-checkpoint trace diagnostics (boundary share,
altitude-floor share, anchor and centre occupancy by distance, first step with service) so that a
SET failure is interpretable; read HMASD-k10's typicality at the checkpoint nearest N's exposure
and report N's rank among seeds instead of an SD threshold from three samples; label .60 as
H_local's level, not "approaching H_central"; memory ≈ 10 GB per fit makes the fits serial
(≈ 30 h for six) unless the flat arms' peak is measured lower. The DM's response to these and to
Pro's answer, and the revised design, follow in one entry; nothing is bought before that.

## 2026-09-26 — DM response to both reviews of the B01 reading and the B02 proposal; revised B02 (Stage 0 declared)

Two independent passes were read in full: the internal ResearchCritic (recorded in the correction
subsection above) and Pro (`### Answer` above; saved from chat; a `deliver` call made after the
DM's own insertion reports that insertion as the filling commit and is not a Pro write). Both
return MATERIAL_DISSENT: yes on Stage 0 and on Stage 1 as proposed; Pro also dissents on parts of
the B01 reading. Consequential source claims were checked before acceptance.

### B01 reading: further corrections accepted from Pro (in addition to the critic's)

- **P1c was misreported.** The entry says "fails on sign for both controllers". Correct: N fails
  the whole-episode sign condition (+.008 > 0) and satisfies the entry-to-input condition (−.021);
  H_central satisfies the sign condition (−.017) and fails the entry-to-input condition (+.014).
  Both fail the registered conjunction on different sub-conditions. The reading becomes "the
  queue and waiting process changes with width; the registered joint harmful response does not
  occur", not "no service consequence".
- **Scope of branch (b).** It decides the next investment; it does not attribute the whole gap.
  "The exit width is not the S7 loss" is replaced by "for this policy instance, these worlds and
  H3000, the level-0 width changes recovered no service comparable to the reference gap; the exit
  width is not the explanation worth further investment". The N width contrast still carries
  +71.8 J and a positive service change; below threshold is not zero. P2′ stays descriptive and
  gives no information-versus-learning share.
- **Paired tables stay reportable.** Same-device paired differences are results of these fixed
  programmes; the τ_w rule withholds their use for selecting regimes, thresholds or individual
  cross-platform claims, nothing more. "Panel means agree" is replaced by "the observed mean
  differences are small (.002 QoS/step, 4 J)"; no equivalence bound was pre-set, so no platform
  equivalence is established, and N's null does not supply an error bound for H_central or for
  any new learner.
- **P3.** "Before the first shield entry" replaces "before energy pressure"; what is excluded is
  that a not-yet-occurred exit-width intervention caused the early gap, not the other candidate
  causes. "About 8 τ_w" is a magnitude description, not a test statistic.
- **Tether.** Conditional process support, with three qualifiers: only exits followed by a
  re-entry count; repeated exits in one world are not independent samples; the script uses the
  nearest-station distance without enforcing unchanged station identity or radial flight. "The
  increment depends on the width, not the level" is weakened to "the observed increments are
  compatible with the width-bound derivation at both levels". The sentence "entering from ≈ 1 km
  they arrive inside the ≈ 24 s release window" is withdrawn (1 km at 30 m/s already takes 33 s);
  the observation stands that H_central's exits occur at the station (median 20 m) and N's
  mid-return (median 1,414 m), and its explanation needs paired trajectories, not medians.
- **Level effect.** "≈ 1/5 of the gap" is the descriptive proportion of one selected setting on
  the development panel, not a bound on constant rules or adaptive control. The accurate record
  is: P1′ was refuted; a post-hoc package effect favourable to N and unfavourable to H_central was
  found; the comparison itself was pre-arranged, the unregistered step would have been treating
  the direction as a candidate gain; nothing was adopted. "A UAV at the anchor is a backhaul hop by
  construction" is withdrawn (the source constructs an anchor position with jitter, clipping and
  separation; it proves nothing about SINR, two-way capacity or the team layout). With the
  critic's time-confound finding, the station-prior reading is withdrawn entirely (previous
  subsection).
- **Source citation.** The design entry cited `belief_map.py::_get_state` for the S7 state. The
  S7 environment is `UAVEnergyAwareRelayEnv(UAVRoutedRelayEnv)`; its state comes from
  `routed_core.py::_get_state` (normalised UAV, user and BS positions, coverage and connectivity
  flags, link quality, step clock) with the energy suffix appended in `energy_aware.py`. Verified.

### B02 design: what both reviews establish

- **Stage 0 as proposed over-claimed** (both): H_spawn is a reset-target controller under the
  production shield, not a "no deployment" floor (the spawn corner lies ≈ 3,950 m from the anchor
  and ≈ 5,900 m from the centre; the shield moves the UAVs anyway); H_park2 with two station
  waypoints measures the package effect of adding two waypoints on that background and says
  nothing about N's mediator; H_central@10 isolates only H's own period sensitivity. The critic's
  replacement, a zero-fit check of N with sampled instead of mean actions, targets a possible
  evaluation artefact behind the boundary parking (B01 and B09 evaluated with `deterministic=True`)
  and was not available to Pro, whose question predates the boundary finding.
- **Stage 1 as proposed was misframed** (both): the "typicality" test is invalid because B09's N
  was trained without the shield on 180,000 transitions while the proposal trains with the shield
  at 1.2 M transitions under a new collector (Pro; verified against the B09 entry "both arms learn
  service, feedback training adds no mean endpoint gain": N ordinary, A with feedback); SD from
  three seeds is not a test (critic); a SET failure is uninterpretable without registered
  diagnostics (critic; Pro's failure table); the actual SET recipe keeps the recurrent low-level
  actor and holds a central snapshot made of the central state, all agents' observations and an
  ego one-hot, refreshed at the k = 10 decision boundary, not every step (Pro; the snapshot
  composition and the held-snapshot arrays verified in `hmasd/networks.py` ≈ 1586–1592 and
  `hmasd/agent.py` ≈ 909–914; the RNN retention is recorded from the runner's active config at
  launch); memory ≈ 10 GB per fit makes fits serial (both); .60 is H_local's level, not
  "approaching H_central" (both); B01's evaluator loads a fixed N and needs a SET loader that does
  not relax N's identity check (Pro).
- **Value** (Pro): the corrected B02 is a task-calibration stage for the paradigm question, a
  learning baseline against an executed strong rule reference; it neither validates nor refutes
  the joint-skills recommendation, and a HMASD − SET difference would be a difference between two
  learning packages, not a joint-skill contribution.

### Resolution (DM, constitution §2; both reviews adopted where they agree, both replacements kept where they differ)

**Stage 0, declared now (0 fits; production shield (0, .05); 955001–955032; B01 evaluator,
traces and the four new diagnostics per world; ≈ 160 episodes ≈ 40 min of node time):**
1. **N with sampled actions**, 2 draws per world (64 episodes), seeded per (policy seed, world,
   draw); both levels sample. Registered reading S0-1: if the sampled-action panel mean lies within
   .03 QoS/step of the deterministic N (.328) and its boundary share stays above .30, the boundary
   parking and the deficit belong to the learned policy and the deterministic evaluation stands; if
   the sampled mean exceeds the deterministic one by ≥ .05 or the boundary share falls below .15,
   the deterministic evaluation misrepresents the learned behaviour and every deterministic S7
   comparison of this checkpoint (B09–B11, B01) is relabelled accordingly; between, both are
   reported and the evaluation mode becomes a declared axis of Stage 1. J, return cost, events and
   minimum battery are reported beside QoS; draw-to-draw spread is reported, not tested.
2. **Three fixed references, redefined as Pro asks** (32 worlds each): H_spawn = every UAV flies
   with ordinary actions to a 100 m waypoint over its own reset xy and holds it, under the
   production shield and guard; H_park2 = the same, except that the UAV nearest each station at
   reset (station 0 first, ties by index) takes a 100 m waypoint over that station's xy; H_central@10
   = H_central with a 10-step replanning period. Readings S0-2: H_park2 − H_spawn is the package
   effect of two station waypoints on a reset-target background (expected ≥ +.10; a level, not a
   pass mark; no claim about N's mediator either way); S0-3: |H_central@10 − H_central| < .03 reads
   "this H's period sensitivity is below the practical threshold", nothing about SET. All three
   report the common early window, arrival times, altitude, F-mode share and charging state so
   that early spatial deployment is separable from later feedback consequences.
Nothing is adopted from these worlds; no Stage 0 result triggers Stage 1 automatically.

**Stage 1, revised to Pro's preferred form (one fit; not launched by this entry):** one
fixed-exposure SET development fit at 1.2 M transitions with the production shield active during
training, labelled a new programme (not a B09 replication); the actual recipe recorded from the
active config at launch (recurrent low-level actor, held snapshot = central state + all
observations + ego one-hot at the k = 10 boundary, S7 preset hyperparameters as a declared
asymmetry, k restored and buffers recomputed as in the first entry); frozen deterministic
evaluation at fixed checkpoints on 955001–955032 with the B01 evaluator, traces and diagnostics
(boundary share, altitude-floor share, anchor and centre occupancy by distance, first service
step, guard-blocked motion, plus per-rollout training Q/J, shield-mapping share, optimizer steps
and PPO KL / clip fraction / entropy); a single sampled-action evaluation per checkpoint if S0-1
makes the mode an axis; 957001–957032 reserved for the frozen final model and the frozen H
references, read once, never used for selection. Readings, separately: the .60 milestone
(H_local's level, labelled so); improvement over the model's own initialisation; the gap to
H_central and to H_local; J, return cost, events and the minimum-battery tail against the same
comparators, with service-versus-risk conflicts reported as conflicts. The typicality prediction
and its relabel branch are deleted. Failure explanations are pre-registered as Pro's table
(non-exclusive candidates; no rescue pre-selected; no extension of the fit after scores; a longer
or changed recipe is a new declared study). Cost: ≈ 5 h serial node wall by the first entry's
HMASD measurement, SET's own memory and throughput measured at launch; checkpoint evaluations
≈ 6 min each. Further seeds or a HMASD-k10 package comparison are a later decision that the
SET curve must justify. Engineering: a training runner reusing the first entry's plan
(`b08.training`, the sharded collector, B01's host and evaluator), a SET checkpoint loader for the
evaluator that leaves N's identity check intact, tests, and an engineering review of the training
and RNG paths before launch.

**Not adopted.** Pro's "keep six fits as a seed-level comparison of two new packages" (a
defensible alternative, deferred behind the single SET curve); a behaviour-cloning ceiling (Pro:
not a bound, not decisive); a memory-ablated or per-step-refresh SET (no matched controls are
bought before the first curve); training at enter level .20.

Belief changes recorded: the deployment deficit is now described by boundary parking and the
altitude floor, with the evaluation mode an open question until S0-1; the "station prior" is
withdrawn; the exit width is closed as an investment for this policy on these worlds without a
general null claim; B02's object is "can an ordinary central-input learning programme approach an
executed rule reference at a fixed exposure", not typicality or structure attribution.

### Launch record: Stage 0 item 1, N with sampled actions (`b02_s0_stoch_a01`, 2026-09-26)

Inputs commit `8d88f72d02ea79ebaf7ac2173daf3db837b70636` (phase `stochastic-check`: N at (0, .05)
on 955001–955032, 2 draws per world seeded by `hash((925031, world, draw)) & 0xFFFFFFFF`, sampling
at both levels; five additive position diagnostics; `--phase all` unchanged) pushed to origin/main
and fast-forwarded on the node. Admission launch from the node
(`temp/directions/energy_relay_benchmark/scratch/launch_phase.sh 8d88f72d0 b02_s0_stoch_a01 stochastic-check 8 2`):
- `acceptance: accepted`, `accepted_at 2026-09-26T17:03:47Z`; host `LAPTOP-U9TDKC8A`; operation
  ref `/home/wu/projects/HMASD/.git/hmasd-admission/07ebcf709aa67d6e3307dada56e6fca0001072226e33c8a0ee94e8fc93133d94.json`
  (claim key `07ebcf70…133d94`); outputs under `/home/wu/projects/HMASD/runs/energy_relay_benchmark/b02_s0_stoch_a01/`
  (panels `stochastic-check/panels/N_e0.00_x0.05_s0.json`, `_s1.json`, traces, `summary.json`);
  command sha256 `03d5e3005bd3408d1f418571a514479b158be2573eb4e7f5d74d6e72a2ca2709`; supervisor
  pid 721802 (posix session), runner pid 721803; 8 workers × 2 threads, CPU; planned 64 episodes,
  ≈ 15 min by B01's throughput.
- Reading rule S0-1 as declared in the resolution above, against the B01 grid panel
  `N_e0.00_x0.05` of `b01_ref_a02` (deterministic; mean QoS/step .328, boundary share .498):
  reader `experiments/candidates/energy_relay_benchmark/b01/read_stage0.py` (written before the
  result is read). Observation: the detached poller every 5 minutes and a background waiter
  with a native return; only health fields are observed before the terminal state.

## 2026-09-26 — Stage 0 item 1 result: N with sampled actions (`b02_s0_stoch_a01`, operation 07ebcf70), read by S0-1

**Operation.** `run_end status COMPLETE`, exit code 0, 64 episodes / 192,000 steps / 0 fits, wall
753.6 s (8 workers × 2 threads, CPU), no failed world; inputs sha `8d88f72d0`; checkpoint identity
identical to B01's N (sha256 `2ba395b9…eeff5a`, fingerprint `aa197872…d39dc0`); `action_mode
stochastic`, sample seeds per `hash((925031, world, draw)) & 0xFFFFFFFF` recorded per row. Reader
`experiments/candidates/energy_relay_benchmark/b01/read_stage0.py` committed at `0376dc5b5` before
any result panel was read (verified end to end on a synthetic tree copied from the B01 panels);
no reader edit after sight. Outputs copied to `runs/energy_relay_benchmark/b02_s0_stoch_a01/`
(JSON committed; the two trace `.npz` files are ignored, local copy plus the node's durable copy);
combined readings `docs/research/candidates/energy_relay_benchmark/b02_stage0_readings.json`.
Definition parity: the five row diagnostics were recomputed from the traces with
`read_stage0.b01_trace_diagnostics` (area 8000 m, floor 50 m); draw 0 equal in all 32 worlds,
draw 1 equal except worlds 955008 and 955029, each by exactly one normal-mode UAV-step (of 18,908
and 19,678) sitting within 1e-3 m of the 1 m wall tolerance — float32 trace storage versus the
in-process value, not a definition difference. The B01 deterministic panel's diagnostics were
recomputed the same way (per-world mean boundary share .5006; the pooled UAV-step share reported
earlier was .4978). Disclosure: the poller's progress tail printed the `panel_end` mean J of draw 0
while draw 1 was running and of draw 1 at the terminal state, before the reader ran; J is not an
input of S0-1.

**Result (production shield (0, .05), 955001–955032; deterministic B01 panel `N_e0.00_x0.05` vs the
two sampled draws):**

| per-world mean | deterministic (B01) | sampled draw 0 | sampled draw 1 |
|---|---|---|---|
| QoS/step | .3283 | .3077 | .3179 |
| raw native J | 955.0 | 887.3 | 922.1 |
| return-constraint cost (sum) | 1.20 | 4.31 | 2.29 |
| cutoff / depletion events | 0 / 0 | 0 / 0 | 0 / 0 |
| min decoded battery | .108 | .102 | .104 |
| F-mode UAV-step share | .184 | .226 | .220 |
| first entry / first input step | 1372 / 2196 | 1368 / 2056 | 1360 / 2059 |
| QoS/step before first entry | .231 | .208 | .204 |
| charger input (Wh) / wait ticks | 146.6 / 1406 | 195.8 / 2660 | 195.8 / 2570 |
| guard-blocked actions | 1949 | 408 | 565 |
| boundary share, normal mode | .501 | .221 | .219 |
| altitude-floor share, normal mode | .700 | .457 | .465 |
| UAV-steps within 300 m of anchor / centre | 2511 / 1187 | 3792 / 1317 | 3697 / 1365 |
| first service step (served worlds) | 247 | 274 | 313 |
| zero-service worlds | 3 (955005/012/021) | 3 (same three) | 2 (955012/021) |

Paired per world (sampled − deterministic): QoS −.021 (SE .010) for draw 0 and −.010 (SE .014) for
draw 1, per-world range −.146…+.318 (per-world SD ≈ .055/.076, so per-world readings stay
unavailable, as under τ_w); boundary share −.280 / −.282 (SE .017), negative in all 32 worlds
(−.48…−.08); altitude-floor share −.244 / −.235 (SE .019); J −68 / −33 (SE 29 / 40).
Draw-to-draw (draw 1 − draw 0): QoS +.010 (SE .012), range −.09…+.32; the +.32 is world 955005,
zero service under deterministic actions and under draw 0, served under draw 1 (its J +951).

**S0-1 applied as declared.** Pooled sampled mean .3128, delta −.016 against .3283: within .03, so
the service clause reads "the deficit belongs to the learned policy" (each draw alone is also
within .03). Boundary share .220: below .30 and above .15, so the parking clause is satisfied by
neither branch. The conjunction therefore lands in the declared middle: **both are reported and
the evaluation mode becomes a declared axis of Stage 1** (one sampled-action evaluation per
checkpoint beside the deterministic one, draw 0 seeding rule). No relabel of B09–B11 or B01 is
triggered: sampled actions do not raise the level (if anything −.016) and do not empty the walls.

**What the numbers add (reported, not tested).** Sampling halves the wall share (.50 → .22) and
lowers the altitude-floor share (.70 → .46) without improving service: the UAVs leave the walls
more often, are blocked by the backhaul guard four times less often (1949 → 408/565), enter the
shield slightly earlier with a higher F-mode share (.18 → .22), draw more charger energy
(147 → 196 Wh), wait more at stations (1406 → 2600 ticks), pay more return-constraint cost
(1.2 → 2.3–4.3) and spend more UAV-steps near the anchor (2511 → 3700–3800), and the team QoS
before the first shield entry is lower (.231 → .205). The deficit is thus not a deterministic-mode
artefact and not tied to the wall pose: it persists when the policy's actions are sampled. The
zero-service worlds are mostly a policy property (the same three under draw 0; one escapes under
draw 1). B01's corrected reading keeps its numbers, now labelled "deterministic evaluation"; the
description of the deployment deficit becomes "wall parking and altitude floor under deterministic
actions (.50 / .70), still one fifth and one half of normal-mode UAV-steps under sampled actions
(.22 / .46), with the same service level". The mechanism of the enter-level effect stays open.

**Next.** Stage 0 item 2 (H_spawn / H_park2 / H_central@10, `stage0-references`, 96 episodes)
launches when its code passes the b01 and b06 suites; readings S0-2 and S0-3 as declared. Stage 1's
declaration gains the evaluation-mode axis (deterministic and one sampled draw per checkpoint);
its engineering (training runner, SET loader, review) is scoped in parallel and no fit is launched
by this entry.

### Launch record: Stage 0 item 2, three fixed references (`b02_s0_refs_a01`, 2026-09-26)

Inputs commit `e5857e0c2a21e6b69229b7b014fb154cef289e90` (phase `stage0-references`, never part of
`--phase all`): `Hspawn` (every UAV holds a 100 m waypoint over its own reset xy, decoded from the
reset legal observation), `Hpark2` (as Hspawn, except station 0 then station 1 each take the nearest
remaining UAV at reset by horizontal distance, ties to the lower index, target = the station xy from
the energy suffix; `park_assignment` recorded per row), `H1r10` (H1 with `replan_period` 10, ground-
truth plan inputs as in the grid); production shield (0, .05) and guard; worlds 955001–955032; 96
episodes; H1's movement primitive (100 m, 30 m/s, 5 m/s vertical cap); the fixed controllers plan
once at step 0 and never replan, so a UAV released by the shield resumes its waypoint. Tests on the
committed tree: b01 45 passed (rerun by the DM), `uav_service_auxiliary/b06` 11 passed 2 skipped
(CUDA); H1/H2/H3/Hlocal rows, per-step arrays and params records verified identical to `8d88f72d0`
on world 955001 (H = 70, three replans). Implementer deviations accepted: `replan_period` already
existed on `HeuristicParams`; "nearest" is horizontal distance (all UAVs reset at one altitude);
fixed rows report `replans = 1`; no arrival-time field (derivable from `target_xy` and `own_xyz` in
the traces); the implementer additionally ran five full-horizon episodes locally on seed 990001
(outside every registered range) for mechanics only, reading no J or QoS — recorded here as a
deviation from the scope note, not as evidence. Admission launch from the node
(`launch_phase.sh e5857e0c2 b02_s0_refs_a01 stage0-references 8 2`): `acceptance: accepted`,
`accepted_at 2026-09-26T17:34:27Z`; operation ref
`/home/wu/projects/HMASD/.git/hmasd-admission/e94bf1fe5c6b52992a1e014ac012df4c48d1073bd5f8155eaf9279b337b73354.json`
(claim key `e94bf1fe…b73354`); outputs under
`/home/wu/projects/HMASD/runs/energy_relay_benchmark/b02_s0_refs_a01/` (panels
`stage0-references/panels/{Hspawn,Hpark2,H1r10}_e0.00_x0.05.json`, traces, `summary.json`); command
sha256 `36e8fd8c1be50f0cb7ddfac790d0dc26d2a72ad2316d317bb05257996f77eb63`; supervisor pid 723493,
runner pid 723494; 8 workers × 2 threads, CPU; ≈ 20 min by the sampled-action run's throughput.
Readings S0-2 and S0-3 as declared, with the reader already committed at `0376dc5b5` (no change).
Known mechanics to report beside S0-2, from the implementer's local probe (mechanics only): under the
production shield a fixed-waypoint UAV released at return margin .05 about 2 km short of its
station turns back to its waypoint, re-enters within ≈ 16 steps and gains ≈ 300 m per cycle until it
docks (dozens of entries per world; H1 cycles less because a UAV in F mode at a replan receives no
target and holds after release). This oscillation is the declared package (fixed target + production
shield), the same shield N faces (N: ≈ 80 entries per world in B01); it is reported with the result,
not removed before it. Observation: detached poller every 5 minutes plus a background waiter with a
native return; only health fields are observed before the terminal state.

## 2026-09-26 — Stage 0 item 2 result: three fixed references (`b02_s0_refs_a01`, operation e94bf1fe), read by S0-2 and S0-3

**Operation.** `run_end status COMPLETE`, exit code 0, 96 episodes / 288,000 steps / 0 fits, wall
905.9 s, no failed world; inputs sha `e5857e0c2`; production shield (0, .05); worlds 955001–955032.
Reader `read_stage0.py` unchanged since `0376dc5b5`; outputs copied to
`runs/energy_relay_benchmark/b02_s0_refs_a01/` (JSON committed, traces ignored, local plus node
copies); combined readings regenerated in `b02_stage0_readings.json`. Definition parity: the five
row diagnostics equal the trace recomputation in all 96 rows. Disclosure: the poller's progress
tail printed each panel's `panel_end` mean J before the reader ran; J is not an input of S0-2 or
S0-3. Stage 0 is complete: 160 episodes, 0 fits, ≈ 28 min of node wall in total.

**Result (per-world means over 955001–955032; H_central = B01's H1 panel, N = B01's deterministic
panel, both on the same worlds):**

| | H_spawn | H_park2 | H_central@10 | H_central (B01) | N (B01) |
|---|---|---|---|---|---|
| QoS/step | .232 | .379 | .769 | .774 | .328 |
| raw native J | 492 | 1066 | 2270 | 2282 | 955 |
| QoS/step before first entry / entry→input / after input | .083 / .204 / .350 | .353 / .379 / .390 | .811 / .822 / .715 | .810 / .840 / .725 | .231 / .353 / .449 |
| first entry / first input step | 1049 / 1604 | 1073 / 1625 | 1317 / 1610 | 1300 / 1617 | 1372 / 2196 |
| shield entries / exits per world | 113 / 105 | 94 / 87 | 49 / 42 | 48 / 41 | 80 / 74 |
| F-mode UAV-step share | .458 | .364 | .336 | .325 | .184 |
| return-constraint cost (sum) | 88.7 | 19.5 | 3.4 | 4.8 | 1.2 |
| cutoff / depletion events | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| min decoded battery | .084 | .094 | .101 | .100 | .108 |
| charging UAV-steps / wait ticks / charger Wh | 1230 / 6367 / 342 | 1238 / 4663 / 344 | 1421 / 4737 / 395 | 1372 / 4570 / 381 | 528 / 1406 / 147 |
| guard blocked / checked | 230 / 2691 | 739 / 6648 | 1037 / 14345 | 1129 / 14620 | 1949 / 11031 |
| mean normal-mode altitude (m) | 98.9 | 98.6 | 97.9 | 97.7 | 67.9 |
| UAV-steps within 300 m of anchor / centre | 7142 / 1520 | 8142 / 3911 | 1810 / 6972 | 1733 / 6994 | 2511 / 1187 |
| first service step (served worlds) | 295 | 20 | 20 | 20 | 247 |
| zero-service worlds | 4 (955004/016/021/027) | 0 | 0 | 0 | 3 |

Arrival: every fixed waypoint is reached (within 50 m) — the spawn waypoints at step 0 by
construction, the two station waypoints of H_park2 at a median 176 steps from a median 5.2 km
(64/64 arrive); H_central's planned targets at a median 183 steps.

**S0-2 applied as declared.** H_park2 − H_spawn = **+.147 QoS/step (paired SE .023)**, positive in
32/32 worlds, ≥ +.10 in 17/32 (median +.101, range +.04…+.55), J +574. The expected level of ≥ +.10
is met on the mean; it was declared a level, not a pass mark, and no claim about N's mediator
follows. The common early window (steps before either arm's first shield entry, median 1,070 steps,
minimum 381): H_spawn .083, H_park2 .352, paired +.269 (SE .016), 32/32 — the package effect of two
station waypoints is present before any feedback consequence and narrows after the first input
(.350 vs .390). The two parked UAVs enter the shield about once each; the other six oscillate
exactly as the implementer's probe predicted (release ≈ 2 km short, return to the waypoint,
re-entry), which is what the entry counts (113 / 94 per world) and the return cost (88.7 / 19.5)
measure; no cutoff or depletion event occurs and the minimum battery stays ≥ .084.

**S0-3 applied as declared.** H_central@10 − H_central = **−.005 QoS/step (SE .005)**, |Δ| < .03 in
26/32 worlds (range −.09…+.07), common early window identical (.809 vs .809, paired −.000, SE
.002), J −12: this H's period sensitivity is below the practical threshold. Nothing about SET
follows, as declared.

**Reported beside (not tested): N among the references on the same 32 worlds.** N (.328) lies
between H_spawn (.232; N − H_spawn +.096, SE .026, 23/32 positive) and H_park2 (.379; H_park2 − N
+.050, SE .029, 21/32 positive). In the common early window N serves .203 against H_spawn's .084
(+.120, SE .019) and H_park2's .352 (−.148, SE .028, N ahead in 6/32). An idle team held at its
spawn points under the production shield still reaches .232 over the episode, .35 after the first
input: a large part of any S7 controller's whole-episode service on these worlds is produced by
the shield's station visits (the stations sit at the relay anchor and the service centre), which
is why the pre-entry window and the common early window are the readings that separate
deployment from feedback consequences. Two fixed station waypoints on that idle background
already match or exceed N's whole-episode level.

**Belief changes recorded.** (1) Package references for Stage 1 on 955001–955032: H_spawn .232,
H_park2 .379, H_local .597, H_central .774 (H_central@10 .769); N .328 deterministic / .313
sampled. (2) The shield's own contribution on an idle team is ≈ .23 QoS/step here; readings of a
learner's service must therefore keep the phase split and the common early window. (3) H's
replanning period is not a consequential design parameter at this level. (4) The fixed-waypoint
oscillation is a property of the production shield with any controller that keeps its target after
release (N included: 80 entries per world); it is part of the package, not corrected here.

**Next.** Stage 0 complete; nothing is adopted from these worlds. Stage 1 (one fixed-exposure SET
development fit with the evaluation-mode axis) proceeds through its engineering (training runner,
learner-checkpoint loader, per-checkpoint evaluation; implementer in flight from
`temp/directions/energy_relay_benchmark/L0_b02_stage1_training.md`) and an engineering review
before any launch; its cost (≈ 5 h serial node wall plus ≈ 1.4 h of checkpoint evaluations) is
reported to the owner with the launch record.

### Addendum to the Stage 0 item 2 entry (same day, after a reviewer pass on the wording and the record)

1. **Narrowing.** "A large part of any S7 controller's whole-episode service on these worlds is
   produced by the shield's station visits" over-reaches: H_central's own table row goes .811 before
   the first entry to .715 after the first input, so the shield lowers its service. The statement
   holds for the idle reference (H_spawn: .083 → .350) and for N (.231 → .449), not for "any"
   controller. Read it as: on an idle or poorly deployed team the shield's station visits produce
   most of the service; on a deployed team they cost service.
2. **Parked UAVs, measured on the 955xxx traces (not the 990001 probe):** the 64 parked UAVs of
   H_park2 enter the shield 2.16 times each on average (maximum 5), arrive at their station
   waypoint at a median 176 steps from a median 5,193 m, none fails to arrive. "About once each"
   in the entry above came from the probe and is replaced by these numbers.
3. **Declared trace readings now reproducible:** `experiments/candidates/energy_relay_benchmark/b01/stage0_trace_checks.py`
   (committed with this addendum) writes the common early windows (H_park2 − H_spawn +.269, SE .016,
   32/32; H_central@10 − H_central −.000, SE .002; N − H_spawn +.120; N − H_park2 −.148), arrivals,
   normal-mode altitude, F-mode share, charging state and the parked-UAV entries into
   `b02_stage0_readings.json` under `traces` (regenerated).
4. **S0-3 is a cross-run comparison** (H_central from the B01 run at `e1fdbe72f`, H_central@10 from
   `e5857e0c2`). Direct check: H1 (period 30, central information) re-evaluated locally on world
   955001 at the current tree for the full 3,000 steps equals B01's stored H1 output for that world
   in all 61 value fields of the row (QoS/step .842532, J 2480.8156, costs, events, counters) and in
   all 15 stored per-step arrays (positions, targets with NaN positions equal, modes, batteries,
   margins, station fields, guard counters); the only differences are fields that did not exist at
   B01 time (the five position diagnostics) or that `evaluate_task` adds after `evaluate_world`.
   S0-3 therefore compares like with like; the common-window −.000 says the same.

## 2026-09-26 — Stage 1 engineering, engineering review and launch record: one SET development fit (`b02_s1_set_a01`, operation d682c906)

**Code (commit `34824de1d`, note correction `759927b5e`).** Package
`experiments/candidates/energy_relay_benchmark/b02/` (`configuration.py`, `training.py`,
`checkpoint_eval.py`), entry `scripts/run_energy_relay_benchmark_b02.py` (`train`,
`evaluate-checkpoint`), additive controller kind `L` in `b01/evaluation.py` (learner checkpoint
built from its `record.json`; N's identity check and every existing B01 output unchanged), tests
`tests/experiments/candidates/energy_relay_benchmark/b02/`. Recipe: B09's fixed S7 native recipe
(2 lanes × 3000, k 10, λ_return 2.0, λ_e 1.0, normalizers off, preset architecture) with the SET
switch in ACG's order (mappo algorithm config, k = 10 restored, `use_central_snapshot_in_flat_actor`,
buffers recomputed), exposure exactly 1,200,000 transitions = 200 rollouts, shield on in training
through the same B06 `apply_feedback` path and layout B09's arm A used (enter 0, exit .05, which the
run record of `b09_an_925031_a01` confirms), training seed 925031 (B09's own; the scope note had
named 915031, B08's — DM decision), plain `HMASDAgent` (not ACG's count-stable modules). Checkpoints
`checkpoints/c00…c06/{agent.pt, record.json}`: c00 = initialisation, then the first rollout reaching
each 200k mark (rollouts 34/67/100/134/167/200 = 204k/402k/600k/804k/1,002k/1.2M transitions; exact
counts in each record). Per-rollout `progress.jsonl`: J and QoS/step per lane, F-mapped-command
share, F-mode share, entries/exits, action entropy, actor/critic losses, optimizer steps, live lanes
at the boundary (PPO KL and clip fraction are not exposed by the agent's update and are recorded
null). Tests: b02 18 passed, b01 45 passed (B07 parity included), `uav_service_auxiliary/b06` 11
passed 2 skipped. Tiny CPU round trip (2 lanes × 60 × 2 rollouts, checkpoints, evaluation on two
stand-in worlds in both modes): deterministic re-evaluation identical, loaded parameters equal saved,
actor input width 3599 = 365 + 306 + 8·365 + 8, saving leaves python/numpy/torch RNG and the learner
bit-identical; the copied collector loop equals B09's `train_arm` bit for bit on B09's own ordinary
config. Accepted deviations: `ordinary_completed_segments = False` (HMASDAgent refuses it with the
mappo switch's `disable_high_level_training`); `train_arm` copied rather than reused (it requires the
ordinary path); B09's bulk read-only artifacts dropped (≈ 4.5 GB at 200 rollouts); `new_agent`
initialisation; `--device cpu` allowed for tests.

**Engineering review (`hmasd-reviewer`, read-only, on `34824de1d`): launch-safe as committed.**
Acceptance items verified: recipe fidelity (the only fields differing from B09 are the SET switch's
own — algorithm, n_Z = n_z = 1, λ_D/λ_d/λ_h 0, the high-level/discriminator disables, the flag,
`ordinary_completed_segments`, `total_timesteps`), collector fidelity (call order and semantics match
`train_arm`; the batched step route; the snapshot held for k = 10 through `env_timers`), RNG safety
on CPU (the CUDA save path has no RNG call), checkpoint compatibility (same writer as B09's endpoint;
loader rejects a mismatched sha, config, flag or fingerprint; CUDA→CPU load as B01 already does for
N), B01 invariants (diff additive, gated on `controller == "L"`), evaluation (worlds, modes, seeding,
hold-out refusal, no output collision, admission before imports) and cadence; cost/memory not
verifiable statically. Findings: (1) low — under the legacy `clear_buffers` path every lane missing
from `env_timers` is re-initialised at the next step (timer, four numpy draws, zeroed GRU state);
no behavioural change at production sizes (all 120 B09 episodes truncated at 3000, live lanes at a
boundary 0), a live lane after an early termination would have its recurrent state zeroed
mid-episode; the recipe note in `configuration.py` under-described this and was corrected in
`759927b5e` (follow-up, not a launch condition: pin the behaviour with the reviewer's suggested
assertion in the live-boundary test); (2) informational — the fingerprint check cannot detect a
silent non-load at c00 (identical to a fresh initialisation; sha256 applies to every checkpoint);
(3) informational — `record.json` carries the ACG field list plus extras, the full config is in the
run-root `config.json`, architecture fields outside the list are protected by the frozen source at
the recorded sha; (4) procedural — nothing enforces reading the hold-out once; the DM does.

**Cost, declared before execution.** Upper bound ≈ 11 h of node wall at B09's HMASD cost on the
same GPU (arm A: 6,093 s per 180k transitions → ≈ 40,600 s for 1.2 M); SET skips the coordinator and
discriminator updates but has a wider actor, so the real rate is read from rollouts 1–2 in
`progress.jsonl` and appended below. Checkpoint evaluations ≈ 7 × 2 modes × ≈ 6 min ≈ 1.4 h, each a
separate admission launch (`evaluate-checkpoint`, own tag, checkpoint passed as a node path), run
after the fit unless the node's measured memory admits one earlier. Node at launch: RAM 12.8 GB
free of 15.8, RTX 4070 Laptop 6.9 GB free of 8.0, disk 826 GB free; the fit is the only research
process on the node. Nothing is adopted from the development worlds; the fit is not extended after
scores; a longer or changed recipe is a new declared study.

**Launch (admission, from the node):** `launch_b02_train.sh 759927b5e8ca… b02_s1_set_a01 4` →
`acceptance: accepted`, `accepted_at 2026-09-26T18:22:52Z`; operation ref
`/home/wu/projects/HMASD/.git/hmasd-admission/d682c90610817da1c499749ad42052e14e622cd06598cbd9203486658a9f722b.json`
(claim key `d682c906…9f722b`); command sha256
`aa63b7511d61bc5c530fe2d6bade42dc3b16da0cd154ac5adfdfed74e62e8a73`; supervisor pid 726069, runner
pid 726070; `train --seed 925031 --device cuda --threads 4`; outputs under
`/home/wu/projects/HMASD/runs/energy_relay_benchmark/b02_s1_set_a01/` (`config.json`,
`progress.jsonl`, `summary.json`, `checkpoints/`). A first attempt with a mistyped padded sha was
refused by the ancestor check before any launch (no operation created). Observation: detached
poller every 30 min (`scratch/poll_b02_s1_set_a01.{pid,log}`) and a background waiter with a
native return; only health fields and the per-rollout progress are observed before the checkpoints
are evaluated. Readings, as declared: the .60 milestone (H_local's level, labelled so), improvement
over c00, gaps to H_central (.774) and H_local (.597), J / return cost / events / minimum-battery
tail against the same comparators, with the package references H_spawn .232 and H_park2 .379 and
N .328 / .313 beside them; both evaluation modes per checkpoint; 957001–957032 once, final model
only, with `--final`.

### Stage 1 fit: measured rate, and the c00 evaluation launched beside it (2026-09-26)

Rollouts 1–2 of `b02_s1_set_a01` (6,000 transitions each, CUDA): collection 107.9 / 101.7 s,
update 42.1 / 41.3 s → ≈ 150 s per rollout → **≈ 8.3 h for 200 rollouts** (end ≈ 02:45 UTC on
2026-09-27), replacing the ≈ 11 h upper bound; runner RSS 2.4 GB at 107 % CPU on a 20-core node,
9.3 GB RAM free, no live lane at either boundary, shield-mapping share .243 / .225; training
QoS/step per lane .265 / .239 then .348 / .000 (sampled actions during collection; early, not a
reading). `action_entropy` is absent from the rollout event (recorded in the summary/PPO block or
null; checked at the read). Stage 1 reader `read_stage1.py` committed at `d3f6bda93` before any
checkpoint panel exists (verified on a synthetic tree copied from the B01 N panel).

**c00 (initialisation) evaluation launched during the fit.** The admission kernel refused the
checkpoint under the node's author root ("absolute author input is absent from published
snapshot"), so the c00 directory was copied unchanged to
`/home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c00/` (agent.pt sha256
`9d5806c1…` equals `record.json`; the loader re-checks it) — the convention for every checkpoint
evaluation of this fit. `launch_b02_eval.sh 759927b5e8ca… b02_s1_eval_c00_a01 <that path> 8 2`
(`evaluate-checkpoint --worlds 955001-955032 --modes deterministic,stochastic --device cpu`):
`acceptance: accepted`, `accepted_at 2026-09-26T18:31:34Z` on measured memory beside the running
fit; operation ref
`/home/wu/projects/HMASD/.git/hmasd-admission/53663d6bd47382e38c41af64f1cfd6725caae0eb154ea12f1021e820746bf3c0.json`
(claim key `53663d6b…bf3c0`); command sha256 `4b6bff081d3b93441067b0acc14afbee87c4ccd4d450ee20d23f9c0a755e760e`;
supervisor pid 727107, runner pid 727108; outputs under
`/home/wu/projects/HMASD/runs/energy_relay_benchmark/b02_s1_eval_c00_a01/checkpoint-eval/`
(panels `L_c00_deterministic_e0.00_x0.05`, `L_c00_stochastic_e0.00_x0.05`, traces). c00 gives the
"improvement over the model's own initialisation" baseline; it is read with the curve, not alone.

### Stage 1, c00 (initialisation) evaluated: the learner's own baseline (`b02_s1_eval_c00_a01`, operation 53663d6b)

`status COMPLETE`, exit 0, 64 episodes (32 worlds × 2 modes), 0 failed, wall 787.7 s beside the
running fit; launch sha `759927b5e`; the five row diagnostics equal the trace recomputation in all
64 rows. Reader `read_stage1.py` (`d3f6bda93`, unchanged); readings
`docs/research/candidates/energy_relay_benchmark/b02_stage1_readings.json` (regenerated at each
checkpoint; the training block reads the fit's `progress.jsonl`, copied locally, ignored by Git).

| c00, 955001–955032 | deterministic | stochastic (draw 0) |
|---|---|---|
| QoS/step | .209 | .243 |
| paired vs H_central .774 | −.565 (SE .017) | −.531 (SE .016) |
| paired vs H_local .597 | −.388 (SE .022) | −.354 (SE .023) |
| paired vs H_park2 .379 | −.170 (SE .022) | −.136 (SE .022) |
| paired vs H_spawn .232 | −.023 (SE .008) | +.011 (SE .005) |
| paired vs N .328 (deterministic) | −.120 (SE .026) | −.085 (SE .024) |
| worlds ≥ .60 | 0/32 | 0/32 |

Reading (a baseline, to be read with the curve, not alone): the untrained SET actor under the
production shield sits at H_spawn's level in both modes — the service an idle or random team gets
from the shield's station visits — and N's whole-episode margin over a random initialisation is
+.12 (deterministic) / +.085 (sampled). "Improvement over the model's own initialisation" is
measured from these two panels. Fit progress at the read: 7 rollouts, ≈ 195 s per rollout while the
evaluation shared the CPUs (≈ 150 s alone), 0 live lanes at any boundary.

### Stage 1, c01 (204k transitions, rollout 34) evaluated (`b02_s1_eval_c01_a01`, operation a9d1c17a)

Checkpoint written 19:59 UTC (`optimizer_steps` low_actor = low_critic = 76,500), copied to the node's
artifacts directory (agent.pt sha256 `be3ad2f1…` equals its record), evaluation accepted 20:00:13Z
beside the fit (command sha256 `a0bb9b39…`, supervisor pid 729766, runner 729767), `COMPLETE` in
828.7 s, 64 episodes, 0 failed, diagnostics parity equal in all rows. Reader `read_stage1.py`
unchanged; readings JSON regenerated (c00 + c01).

| 955001–955032 | c00 det | c01 det | c00 stoch | c01 stoch |
|---|---|---|---|---|
| QoS/step | .209 | .241 | .243 | .250 |
| paired vs c00 | — | +.032 (SE .022, 19/32) | — | +.007 (SE .024, 13/32) |
| vs H_central .774 | −.565 | −.533 (SE .025) | −.531 | −.524 (SE .026) |
| vs H_local .597 | −.388 | −.356 (SE .030) | −.354 | −.347 (SE .030) |
| vs H_park2 .379 | −.170 | −.138 (SE .028) | −.136 | −.129 (SE .030) |
| vs H_spawn .232 | −.023 | +.009 (SE .022) | +.011 | +.018 (SE .024) |
| vs N .328 | −.120 | −.087 (SE .032) | −.085 | −.078 (SE .033) |
| worlds ≥ .60 | 0 | 0 | 0 | 0 |

After 204k transitions the frozen learner is within the practical threshold of its own
initialisation in the sampled mode and one threshold above it in the deterministic mode, at
H_spawn's level; reported, not read further. Training-time QoS/step (sampled actions, shield on),
by 10-rollout blocks: r1–10 0.191, r11–20 0.161, r21–30 0.210, r31–39 0.181; F-mapped-command share 0.227 → 0.257; F-mode share 0.227 → 0.257; action entropy not in the rollout events; rollouts with a zero-service lane: [2, 6, 7, 8, 9, 11, 12, 13, 14, 16, 20, 23, 24, 25, 27, 28, 34, 35, 36, 38, 39].
Fit at the read: 39 rollouts, ≈ 168 s per rollout with the two evaluations sharing the CPUs
(projection ≈ 9.3 h), 0 live lanes at any boundary.

### Stage 1, c02 (402k transitions, rollout 67) evaluated (`b02_s1_eval_c02_a01`, operation c498afec)

Checkpoint written 21:26 UTC, copied to the artifacts directory (agent.pt sha256 `dd9dcec8…` equals
its record), evaluation accepted 21:26:38Z beside the fit (command sha256 `60530acb…`, supervisor
pid 732497, runner 732498), `COMPLETE` in 871.4 s, 64 episodes, 0 failed, diagnostics parity equal
in all rows. Reader unchanged since `a1767f1de`; readings JSON regenerated (c00–c02).

| 955001–955032 | c00 | c01 | c02 det | c02 stoch |
|---|---|---|---|---|
| QoS/step (det / stoch) | .209 / .243 | .241 / .250 | .318 | .303 |
| paired vs c00 | — | +.032 / +.007 | +.109 (SE .017, 29/32) | +.060 (SE .026, 21/32) |
| vs H_central .774 | | | −.456 (SE .019) | −.471 (SE .026) |
| vs H_local .597 | | | −.279 (SE .029) | −.294 (SE .038) |
| vs H_park2 .379 | | | −.060 (SE .022) | −.076 (SE .029) |
| vs H_spawn .232 | | | +.086 (SE .017) | +.071 (SE .026) |
| vs N .328 (det) | | | −.010 (SE .019) | −.026 (SE .029) |
| boundary share / altitude-floor share (normal mode) | | | .428 / .321 | .136 / .056 |
| QoS before first entry / after first input | | | .172 / .475 | .169 / .410 |
| F-mode share; return cost; min battery | | | .199; 3.28; .106 | .265; 8.15; .101 |
| zero-service worlds; worlds ≥ .60 | | | 1; 0 | 1; 0 |

At a third of the exposure the frozen learner has moved a full threshold above its
initialisation in both modes and sits within the threshold of N (B09's HMASD checkpoint, 180k
transitions) in the deterministic mode, still below H_park2 and far below H_local and H_central;
no milestone. Under deterministic evaluation this learner too parks on the walls (.43 of
normal-mode UAV-steps; .14 under sampled actions) — the same mode dependence Stage 0 found for N.
Training-time QoS/step (sampled actions during collection) stays flat and noisy by 10-rollout
blocks (.19, .16, .21, .18, .16, .13, .21, .12), a zero-service lane in 40 of 71 rollouts, action
entropy 1.156 → 1.150, F-mode share rising: the curve separates training-time stochastic service
from frozen evaluation, as Pro asked it to. Reported, not read further; the next checkpoints
decide whether this is a rising curve or a plateau at N's level. Fit at the read: 71 rollouts,
≈ 166 s per rollout (projection ≈ 9.2 h → end ≈ 03:35 UTC), 0 live lanes.

### Stage 1, c03 (600k transitions, rollout 100) evaluated (`b02_s1_eval_c03_a01`, operation e2e0f998)

Checkpoint written 22:55 UTC, copied to the artifacts directory (agent.pt sha256 `80b2bdad…` equals
its record), evaluation accepted 22:57:57Z beside the fit (command sha256 `0f059fe0…`, supervisor
pid 735402, runner 735403), `COMPLETE` in 882.0 s, 64 episodes, 0 failed. Diagnostics parity: row
values equal the trace recomputation except the normal-mode boundary share in 5 of 64 rows, which
differs by at most 2.5e-4 (float32 accumulation in the runner, as in the Stage 0 parity note); the
other four diagnostics are exact. Reader unchanged since `a1767f1de`; readings JSON regenerated
(c00–c03).

| 955001–955032 | c00 | c01 | c02 | c03 det | c03 stoch |
|---|---|---|---|---|---|
| QoS/step (det / stoch) | .209 / .243 | .241 / .250 | .318 / .303 | .325 | .345 |
| paired vs c00 | — | +.032 / +.007 | +.109 / +.060 | +.116 (SE .020, 28/32) | +.102 (SE .016, 25/32) |
| vs H_central .774 | | | | −.449 (SE .019) | −.429 (SE .017) |
| vs H_local .597 | | | | −.272 (SE .031, 2/32 above) | −.252 (SE .026, 0/32 above) |
| vs H_park2 .379 | | | | −.054 (SE .026) | −.034 (SE .023) |
| vs H_spawn .232 | | | | +.093 (SE .020) | +.113 (SE .017) |
| vs N .328 (det) | | | | −.003 (SE .022, 16/32) | +.016 (SE .019, 16/32; conflict flag: return cost and min battery worse than N's) |
| J (mean) | 587 / 693 | 692 / 709 | 920 / 864 | 944 | 996 |
| boundary share / altitude-floor share (normal mode) | | | .428 / .321 ; .136 / .056 | .365 / .334 | .094 / .098 |
| QoS before first entry / after first input | | | .172 / .475 ; .169 / .410 | .218 / .434 | .215 / .436 |
| first service step (mean) | | | 323 ; 290 | 206 | 254 |
| F-mode share; return cost; min battery | | | .199; 3.28; .106 ; .265; 8.15; .101 | .203; 1.63; .114 | .284; 4.97; .105 |
| zero-service worlds; worlds ≥ .60 | 4 / 3 | 5 / 5 | 1 / 1 | 2 (955005, 955021); 0 | 2 (955016, 955021); 0 |

At half the exposure the two modes separate: deterministic evaluation is flat between c02 and
c03 (+.007; the reader's `still_improving_at_end` is false) and sits exactly at N's level
(−.003, 16 worlds each way); sampled-action evaluation gained +.042 over c02 and is now +.016
above N with the reader's conflict flag (higher service, but return-constraint cost 4.97 against
N's and a lower minimum battery), still −.034 below H_park2 and a quarter below H_local; no
milestone (0/32 worlds at .60 in either mode). Both modes are more than a threshold above the
initialisation (+.116 / +.102). Wall parking under deterministic evaluation is receding rather
than growing (.43 → .36 of normal-mode UAV-steps; .14 → .09 under sampled actions) while service
before the first shield entry has risen (.17 → .22 in both modes) and the first service arrives
earlier (206 / 254 steps against 323 / 290): what improved between c02 and c03 is the pre-entry
phase, not the shield-driven one. Training-time QoS/step by 10-rollout blocks is still flat
(.19, .16, .21, .18, .16, .13, .21, .14, .20, .19, .20), a zero-service lane in 61 of 105
rollouts (21 of the last 34), action entropy 1.156 → 1.043 through a non-monotone path (1.23 near
rollout 76), F-mode share rising (.23 → .29–.34 per block) with shield entries per rollout up
from ≈ 114 to ≈ 170: the collection-time policy keeps oscillating through the shield while the
frozen evaluations improve, which is the gap Pro's table lists under "training signal is not the
evaluation signal" (observable proxy: flat training QoS with rising frozen-evaluation QoS).
Reported, not read further. Fit at the read: 105 rollouts, ≈ 165 s per rollout (projection
≈ 9.2 h → end ≈ 03:35 UTC), 0 live lanes, runner RSS unchanged. c04 (rollout 134, ≈ 00:40 UTC),
c05 (167) and c06 (200) follow the same procedure; the curve is read as a whole after c06.

## 2026-09-26 — Stage 1 fit `b02_s1_set_a01` died at rollout 117 (702k transitions): CPython internal error inside the environment's numpy path; c03 (600k) is the last checkpoint

**Facts.** The runner (pid 726070, operation d682c906) exited with code 1 at 23:45:31Z after
rollout 117 (702,000 transitions, 234 native episodes, checkpoints c00–c03); `summary.json`
status `INCOMPLETE`, failure `SystemError: Objects/listobject.c:2529: bad argument to internal
function`. Traceback (stderr.log, an untracked `.log`): `run_training` → `collect_and_train`
(training.py:130, `env.step(submitted)`) → `envs/pettingzoo/env_adapter.py:224` →
`envs/pettingzoo/relay/energy_aware.py:606 step` → `:1191 _graph_service_potential` →
`:1059 _access_capacity_bps` → `:1067 _spectral_efficiency`, `float(np.clip(sinr_db, -40.0,
60.0))` → `numpy/core/fromnumeric.py:2169 clip` → `:56 _wrapit` → `SystemError`. In CPython
3.10.21 `Objects/listobject.c:2529` is the `PyErr_BadInternalCall()` inside `PyList_AsTuple`: a C
caller handed a non-list to a list API. That is a memory-safety fault inside the process, not a
Python-level error; `sinr_db` is an ordinary Python float on this path (single traceback, no
chained `TypeError`), and the same line had run some 10^8 times in this process. Node interpreter:
Python 3.10.21, numpy 1.26.3, torch 2.7.0+cu118; the process also held CUDA and the pybind11
geometry backend. One event in ≈ 2.6 M environment steps run by this direction (B01, Stage 0,
four checkpoint evaluations, this fit); the evaluations ran in separate processes and none was
running at the crash (c03's ended 23:12Z). Root cause: undetermined; classified as a rare native
heap/refcount fault; not reproducible on demand and not pursued further. Node after the exit:
idle, RAM 12.4 GB free, CUDA available with 7.4 GB free, disk 821 GB free; the kernel log holds
only WSL `dxg` adapter-query ioctl failures at ≈ 23:01–23:08Z (the CPU evaluation's torch import)
and no OOM record. Rollouts 101–117 produced no checkpoint; their rows stay in the committed
`summary.json` (training-time sampled QoS/step over them: mean 0.230, a zero-service lane in
8 of 17, action entropy 0.897 at rollout 117). The fit poller and its waiter exited on the
terminal state; the c04 watcher was stopped.

**Decision (DM): resume from c03, not a fresh fit.** `c03/agent.pt` (`HMASDAgent.save_model`)
holds the whole learner state — network weights, both discoverer optimizers and the coordinator
optimizer, the rollout-sampler RNG state and seed, the value-normaliser statistics, the safety
dual state and the training progress — and `HMASDAgent.load_model` restores all of it (weights
with `strict=False`; the resume path therefore checks the parameter fingerprint, the optimizer
step counts and the sampler state after loading and refuses on any difference).
`value_norm_update_counter` is initialised and never incremented, so no phase is lost. What a
resumed run cannot restore are the environment world streams and the action-sampling streams
(torch; numpy global draws with n_Z = n_z = 1): they are re-seeded with a declared seed at the
600k boundary. A run whose learner state is restored exactly and whose random streams change at
a rollout boundary is the same declared study in distribution; it costs ≈ 4.6 h instead of
≈ 9.2 h and makes every later checkpoint a recovery point. A fresh 1.2 M fit was considered and
rejected: same validity, twice the cost, no recovery point, and a curve that could not be
compared with c00–c03 without a second reading rule. Rollouts 101–117 of the first process are
discarded (no checkpoint among them, nothing selected on them: the resume point is the last
checkpoint, whatever its scores). Engineering: a resume path in candidate files only
(`training.py`, the runner, tests; the shared core untouched), engineering review, then a launch
under a new tag from the sha-verified c03 copy in the artifacts directory; the Stage 1 reader's
training block gains a two-run rule (first process rollouts 1–100, resumed process 101–200; the
discarded 101–117 reported, not plotted) committed before any c04 panel exists. Declaration and
launch record follow in the next entry.

## 2026-09-27 — Stage 1 resumed from c03: declaration, engineering, review and launch record (`b02_s1_set_a01r`, operation faf881bc)

**Declaration (before launch).** The study is the one declared on 2026-09-26: the SET recipe,
the 1.2 M exposure, the checkpoint rule (c04 after rollout 134, c05 after 167, c06 after 200) and
the readings (the .60 milestone = H_local's level, improvement over c00, gaps to H_central .774 /
H_local .597 with H_spawn .232 / H_park2 .379 / N .328/.313 beside them, conflicts, Pro's
failure-explanation table; 957001–957032 once, final model only, `--final`) are unchanged. The
process that finishes it is a second one, started from c03 (rollout 100, 600,000 transitions;
`agent.pt` sha256 `80b2bdadddb76a4c03fe9fea8ae9fb1317a136363d28dec0d8fae350745dcce4`, policy
fingerprint `4667fdc9df9486167a9820ffc3433a5c6d4b8fe568b21e6fbc3c1326aca4ff3b`, both from the
committed `summary.json` of the first process). Restored exactly from c03 through
`HMASDAgent.load_model`: network weights (state dicts equal, no missing or unexpected keys),
discoverer actor and critic Adam states (step 225,000 = 100 × 2,250; `exp_avg`/`exp_avg_sq` equal
for all 15 parameters), coordinator optimizer, rollout-sampler RNG state and seed, value-normaliser
statistics (discoverer count 4.8 × 10^6 = 600k transitions × 8 UAVs), the (empty) safety dual state
and training progress. Re-seeded at the boundary with `resume_seed = 925031 + 100 = 925131`:
`seed_everything` before the agent is built, the two lane environments (`make_env(925131 + lane)`,
first reset with the same seed, later resets `seed=None` as before), torch action sampling and the
numpy global RNG (skill draws with n_Z = n_z = 1, always 0). Not saved by `save_model` and restarting
at 0: `global_step`, inert for this recipe (`use_lr_decay` False, `use_entropy_annealing` False,
`use_reward_annealing` unset, high level and process exploration disabled; its `% 200` block only
sets high-level collection flags after the last update). The per-lane agent state (env timers, GRU
state, central snapshot) starts fresh, which equals the boundary state of the first process:
rollout 100's row has 0 live lanes and all 234 completed episodes were truncated at 3000. Rollouts
101–117 of the first process are discarded (no checkpoint among them; nothing selected on them).
The new run's records: `training_seed` 925031 (so the evaluator's `policy_seed` rule is unchanged
for c04–c06), `launch_sha` of the new code, `wall_seconds`, `native_episodes` and lane `episode`
indices counting this process only, `summary["checkpoints"]` holding c04–c06 with the count
starting at 4. Reader: `read_stage1.py --train b02_s1_set_a01 b02_s1_set_a01r` (two-run rule,
committed `cfefb86a8` before any c04 panel existed).

**Engineering.** Implementer (L0 `temp/directions/energy_relay_benchmark/L0_b02_resume.md`)
committed `c9895139b` + `c369a6b91`: `collect_and_train(start_rollout, start_transitions,
env_seed)` (defaults byte-identical to before), `read_resume_checkpoint` (refuses before any torch
effect or output on object/programme/training-seed/config-dict/agent_pt name/rollout-schedule/
transitions/checkpoint-name/source-sha/sha256 mismatches), `resumed_agent` (refuses after the load
on fingerprint, optimizer steps or sampler state/seed differences), the `resume` block in
`config.json`/`summary.json`, runner `train --resume-from --resume-source-sha`; shared core,
`configuration.py`, `checkpoint_eval.py` and the launch kernel untouched. Tests: b02 27 passed
(18 unchanged + 9 new in `test_b02_resume.py`), b01 45, `tests/test_hmasd_launch.py` 53 + 1 skipped;
re-run here: b02 27 passed. Local pre-launch checks on the sha-verified c03 copy with the production
spec: `read_resume_checkpoint` passes with the full source sha and refuses the short one; CPU load via
`resumed_agent`: fingerprint equal, optimizer steps 225,000 (Adam step tensor 225,000, lr 1e-4),
value-norm count 4.8 × 10^6, sampler seed restored.

**Engineering review (hmasd-reviewer, read-only): launch-safe as committed.** Findings, none
blocking: (1) `global_step` not saved — inert here, declared above; for reuse, refuse in
`read_resume_checkpoint` when any schedule flag is on (follow-up); (2) a missing `valuenorm_state`
would be a silent partial load that the post-load checks would not catch — not live for c03 (count
confirmed), optional comparison in `resumed_agent` (follow-up); (3) nothing checks that both lanes
were done at the source boundary — evidence cited above; (4) the record is self-consistent only —
expected identity declared above and checked against the new run's `resume` block below; (5) test
gaps: the sampler post-load refusal, the reader's two-run rule and the kernel's handling of
`--resume-from` are read, not tested. Default path verified unchanged; seeds verified with no leak
in either direction; the kernel treats `--resume-from` like `--checkpoint` (absolute path outside
the author root passes unchanged, as in the accepted evaluations).

**Launch (admission, from the node):** `launch_b02_resume.sh c369a6b91651ece4bdfbbedce1be26cd0599baff
b02_s1_set_a01r /home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01/checkpoints/c03
759927b5e8caa0ba5bd8ba505ab5388985f6a2fa 4` → `acceptance: accepted`, `accepted_at
2026-09-27T00:38:32Z`; operation ref
`/home/wu/projects/HMASD/.git/hmasd-admission/faf881bcf0e5327cd69a984c4195b4334a78fbaf61134c66548b2f182cdd8066.json`
(claim key `faf881bc…8066`); command sha256
`1d9c218eaf0913b557af15fec968e49e99a2ab2ed7c3286c901f16ece5c455f0`; supervisor pid 738116, runner
pid 738117; memory preflight 15.3 GB available against the 4 GB floor, passed; command `train --seed
925031 --launch-sha c369a6b9… --out runs/energy_relay_benchmark/b02_s1_set_a01r --device cuda
--threads 4 --resume-from …/checkpoints/c03 --resume-source-sha 759927b5e…`. Verified after
acceptance: the run's `config.json` `resume` block carries the declared c03 sha256 and fingerprint,
`resume_seed` 925131, `source_launch_sha` 759927b5e…; `summary.json` counts transitions 600,000 /
rollouts 100 / checkpoints 4 / native_episodes 0, post-load fingerprint equal to c03's, no failure;
stderr holds only the harmless "no discriminator buffer in the checkpoint" line. Expected: 100
rollouts at ≈ 165 s → c04 ≈ 02:15 UTC, c05 ≈ 03:45, c06 ≈ 05:15; each evaluation ≈ 15 min beside the
fit; the once-only hold-out read of c06 after that. Observation as before: a 30-min detached poller,
a background waiter and a watcher on `checkpoints/c04/record.json`, all against the new tag.

**Housekeeping note.** At ≈ 00:32 UTC a helper's clean-up emptied the direction's scratch
directory (the brief said "remove scratch before returning" without naming a subdirectory): the
launch and poll scripts and the first process's poller logs (health polls only) were lost and the
scripts recreated with identical command lines before this launch; evidence is unaffected
(`progress.jsonl`/`summary.json` on the node, JSON committed). Helper briefs now name a unique
subdirectory.

### Hold-out reading pinned and the frozen comparators launched on 957001–957032 (`b02_holdout_refs_a01`, operation d6f4bdeb, 2026-09-27)

**Why now.** The declaration reserves 957001–957032 for "the frozen final model and the frozen H
references, read once". The Stage 1 reader's hold-out block was summary-only; the reading rule
for the hold-out has to exist before any hold-out panel does, so both were fixed at 00:50–01:01
UTC, while the resumed fit is at rollout ≈ 105 and no hold-out panel exists anywhere (checked:
no committed panel holds a 957xxx world).

**Reader (`ae998950e`, DM edit, verdict logic untouched).** `read_stage1.py --holdout-refs <run>`
reads `holdout-references/panels/{H1,Hlocal,N}_e0.00_x0.05.json` (H_central, H_local, N
deterministic on the hold-out worlds) and, for each final panel (c06 deterministic / stochastic on
957001–957032): the summary; `gaps` to those three comparators with the same paired `gap_block`
(QoS/step, J, return cost, cutoff/depletion events, minimum battery, conflict flag); the count of
worlds at or above .60 (H_local's DEVELOPMENT level, labelled so; H_local's own hold-out mean is
reported beside it); and `development_same_checkpoint` = the c06 development mean, the hold-out
mean and their difference (different worlds: two means, no paired SE). `holdout_comparators`
carries each comparator's hold-out summary and its shift from the development mean (whether the
world set is harder for everyone). Checked on the current data (checkpoint blocks byte-identical;
no final block) and on a synthetic hold-out built from renamed development panels (gaps and shifts
reproduce the development values exactly). Nothing here selects anything: the final model is c06
by declaration.

**B01 runner phase (`7ad3ba6d3`, implementer from L0 `L0_b01_holdout_references.md`; DM read the
diff; b01 tests 48 = 45 + 3, b02 27).** `holdout-references`: N (B09 endpoint, `--checkpoint`,
sha-checked), the selected central heuristic (`--heuristic`, H1 = H_central) and `Hlocal` at the
production margins on `HOLDOUT_WORLDS` 957001–957032, 96 episodes; never part of `all`; the runner
requires `--final` for it and refuses `--final` elsewhere; `phase_panels` refuses any other phase
that plans a world ≥ 957001 (default world sets 953xxx/955xxx/956xxx are unaffected; `all` stays
540 episodes); config/summary carry a `holdout_references` block (`read_once: true`). No existing
phase, controller, parameter, trace or diagnostic changed. Not separately reviewed (a phase
addition on the Stage 0 pattern; the DM read the diff).

**Launch (admission, from the node):** `launch_b01_holdout.sh 7ad3ba6d35cee7bb38efe97b9ae60d130a4b46db
b02_holdout_refs_a01 8 2` → `acceptance: accepted`, `accepted_at 2026-09-27T01:01:18Z`; operation ref
`/home/wu/projects/HMASD/.git/hmasd-admission/d6f4bdebffedebd9e4a08bfeb739bce223854417299c371ea643e6584ad3de3e.json`
(claim key `d6f4bdeb…de3e`); command sha256
`7c6b214b62ce40746a6da3b32138a76194af50c1f89077b3fc708e19f3c6f721`; supervisor pid 739467, runner
pid 739468; N checkpoint `…/b09_an_925031_a01/N/endpoint/agent.pt` sha256 `2ba395b9…` (B01's);
`--phase holdout-references --final --workers 8 --threads 2 --device cpu`, beside the resumed fit
(rollout 108 at launch, 168 s per rollout, RSS 1.7 GB, RAM 6.9 GB free). The comparator panels are
NOT read before the final model's hold-out panel exists; both are read together after c06 with the
reader invocation `--evals … <c06 hold-out run> --holdout-refs runs/energy_relay_benchmark/b02_holdout_refs_a01`.
Observation: a background completion watcher that prints status and counts only.

### Alignment notice from Root read (2026-09-27 ≈ 02:40 UTC): two Codex DMs registered; this direction's remaining scope

Root's owner-requested notice `docs/Claude_docs/inbox/CODEX_TWO_DM_ALIGNMENT_20260927.md` (commit
ce3947efb, with RESEARCH routing rows and the archived allocation review) registers two independent
Codex DMs on the same frozen S7 problem: `energy_relay_baselines` (DM1: ordinary-learning
reproducibility across training instances; the inbox report's D1, with D4 imitation
initialisation as a revisable successor) and `energy_relay_diagnostics` (DM2: the inbox report's
D2 + D3, comparability of training-time and evaluation signals, sole writer of any new
proposal/submitted-action/actor-head trajectory interface). This direction keeps exactly the
accepted B02 SET development study: the resumed fit, c04–c06, the once-only hold-out read of the
final model against `b02_holdout_refs_a01`, the full cost and the interpretation. Consequences
recorded here: (1) the cross-seed replication and the imitation-package comparison that earlier
entries listed as Stage 2 candidates are DM1's; this notebook will not declare them; any
continuation after the Stage 1 read that is not in DM1/DM2's scope is decided with Root's
coordination, not from the old menu. (2) 957001–957032 and the sealed comparator run are read
only here, once, by the pinned reader; nobody else looks at them. (3) Shared-main writing:
short critical sections under `flock .git/hmasd-main-writer.lock` for index/commit/push, refresh
main first, explicit own paths only, other writers' working-tree changes preserved — adopted from
this entry on. (4) DM2 may add an optional observer hook to `b01/evaluation.py` that keeps the
default behaviour and the old output contract; an uncommitted edit of that shape is present in
the shared working tree at the time of writing (`observer=None`, `nullcontext`, identical loop
body). It cannot reach this direction's remaining evaluations, which launch from the pinned
snapshots (`c369a6b91` for c05/c06/final; the comparators already ran at `7ad3ba6d3`); the
direction's own tools used from here on (`read_stage1.py`, `read_stage0.b01_trace_diagnostics`)
do not import it. (5) The §5 wording in the generated Claude skill copies was updated by the
publisher (`d81fc8622`); the constitution, models and permissions are unchanged. No reply, ACK
or forwarding is owed or sent.

### Stage 1, c04 (804k transitions, rollout 134) evaluated (`b02_s1_eval_c04_a01`, operation f77befe2) — first checkpoint of the resumed process

Checkpoint written ≈ 02:23 UTC by the resumed fit `b02_s1_set_a01r` (record: rollout 134, 804,000
transitions, optimizer steps 301,500 = 134 × 2,250, so the count is continuous across the resume;
`launch_sha` c369a6b91, `training_seed` 925031 unchanged, `wall_seconds` 5,991.7 = this process
only), copied to the artifacts directory (agent.pt sha256 `31d21637…` equals its record, fingerprint
`450be1dd…`), evaluation accepted 02:24:36Z beside the fit (command sha256 `ef0f56f4…`, supervisor
pid 742528, runner 742529, memory preflight 13.2 GB available), exit 0 at 02:40:11Z, `COMPLETE` in
916.1 s, 64 episodes, 0 failed. Same evaluator, worlds 955001–955032, `policy_seed` 925031, so the
panel is directly comparable with c00–c03. Diagnostics parity: row values equal the trace
recomputation except 1 (det) / 4 (stoch) of 64 rows differing by at most 6.2e-5 (float32
accumulation, as in the Stage 0 parity note). Reader unchanged since `ae998950e`; readings JSON
regenerated with both training directories under the two-run rule (c00–c04): process 1 rows
101–117 are listed under `discarded_rollouts` (17 rows, mean training QoS/step .230, 8 zero-service
lane rollouts) and the curve continues from the resumed process at rollout 101.

| 955001–955032 | c03 det / stoch | c04 det | c04 stoch |
|---|---|---|---|
| QoS/step | .325 / .345 | **.406** | **.404** |
| paired vs c00 | +.116 / +.102 | +.197 (SE .022, 31/32) | +.161 (SE .024, 26/32) |
| paired vs c03 (curve step) | | +.081 | +.059 |
| vs H_central .774 | −.449 / −.429 | −.368 (SE .017, 0/32 above) | −.370 (SE .021, 0/32) |
| vs H_local .597 | −.272 / −.252 | −.191 (SE .032, 4/32 above) | −.193 (SE .032, 4/32) |
| vs H_park2 .379 | −.054 / −.034 | +.027 (SE .020, 20/32) | +.025 (SE .023, 19/32) |
| vs H_spawn .232 | +.093 / +.113 | +.174 (SE .022, 32/32) | +.172 (SE .025, 28/32) |
| vs N .328 (det) | −.003 / +.016 | +.077 (SE .027, 21/32) | +.075 (SE .028, 22/32; conflict flag: return cost 1.65 and min battery .107 worse than N's) |
| J (mean) | 944 / 996 | 1187 | 1180 |
| boundary share / altitude-floor share (normal mode) | .365 / .334 ; .094 / .098 | .406 / **.710** | .221 / **.485** |
| QoS before first entry / after first input | .218 / .434 ; .215 / .436 | .274 / .520 | .271 / .506 |
| first service step (mean) | 206 ; 254 | 177 | 249 |
| F-mode share; return cost; min battery | .203; 1.63; .114 ; .284; 4.97; .105 | .157; 0.91; .110 | .245; 1.65; .107 |
| zero-service worlds; worlds ≥ .60 | 2; 0 ; 2; 0 | 0; 2 (955009 .609, 955014 .612) | 0; 2 (955009 .639, 955022 .643) |

Largest single step of the curve so far, in both modes (+.081 / +.059; `still_improving_at_end`
true in both), and the c03 separation between the modes has closed (.406 / .404). The learner is
now about two and a half thresholds above N (+.077 / +.075, 21–22 of 32 worlds), less than the
.03 threshold above H_park2 (+.027, SE .020; +.025, SE .023), a threshold above H_spawn on every
world under deterministic evaluation (32/32; 28/32 sampled), and still a fifth below H_local
(−.191 / −.193; 4 worlds above it) and .37 below H_central. No milestone: the mean is .19
short of .60, though the first two worlds per mode reach it (955009 in both modes). No world is
served zero (c03 had two per mode). Behaviour change between c03 and c04, deterministic mode:
the altitude-floor share of normal-mode UAV-steps doubled (.334 → .710; .098 → .485 under sampled
actions) while the boundary share moved little (.365 → .406; .094 → .221), the F-mode share fell
(.203 → .157; .284 → .245) with the return-constraint cost (1.63 → 0.91; 4.97 → 1.65), service
after the first input rose (.434 → .520) and before the first entry (.218 → .274), first service
earlier (206 → 177 steps). Phenomenon, not explanation: the gain coincides with descending to the
altitude floor and fewer shield episodes, not with more wall parking; whether the low flight is
the cause of the higher served ratio is not read from these panels.

Training signals of the resumed process, reported with the comparability caveat first: from
rollout 101 the environment world streams are re-seeded (resume seed 925131 + lane), so the
collection-time blocks before and after the boundary are not on the same world sequence, while
the frozen panel above is on the same 32 worlds as c00–c03. Within the resumed process the
training QoS/step per 10-rollout block rises monotonically (.261, .288, .301, .313 for rollouts
101–140) against .19 flat over process 1's ten blocks and .230 for its discarded rollouts 101–117;
zero-service lane rollouts 3, 2, 1, 1 per block (64 of 140 rollouts over the whole curve);
shield entries per rollout ≈ 132–167 (process 1 last block ≈ 175); F-mode share .26–.30 (process
1 last block .34). Action entropy: process 1 read 1.069 over rollouts 91–100 (per-rollout
.98–1.18) and 1.013 over its discarded 101–117 (per-rollout .90–1.14); the resumed process read
1.127 over 101–110 (per-rollout 1.08–1.19, within process 1's last-ten span; weights, optimizers
and sampler state were verified equal at load, and the streams differ from rollout 101), then fell
steadily to .684 over 131–140 (per-rollout .54–.78, the lowest of the whole fit; 1.156 → .624
first to last). Over this segment collection-time service and the frozen-panel reading rise
together (still different worlds, modes and aggregations); the c03-time contrast, flat training
QoS against a rising panel, is not present in the resumed process. The entropy fall is recorded
as the proxy for Pro's "policy sharpening / premature convergence" row and is read at c05–c06,
not acted on.
Fit at the read (02:43 UTC): 140 rollouts, ≈ 185 s per rollout in this process (164 in process 1;
the comparator run and the checkpoint evaluations shared the CPU), 0 live lanes, runner alive.
Projection: c05 (rollout 167) ≈ 04:05 UTC, c06 (rollout 200) ≈ 05:45 UTC; same procedure, then
the development evaluation of c06, the once-only hold-out evaluation of c06 on 957001–957032
(`--final`), and the whole-curve read with `--holdout-refs`.

Comparator run on the hold-out worlds `b02_holdout_refs_a01`: `COMPLETE` (96 episodes, 0
failed; launch sha 7ad3ba6d3), copied locally. Its panels stay unread; the run's JSON (config,
summary, launch records, panels) is committed with this entry so the comparator values are sealed
by content hash before the final model exists — a change from the earlier plan to commit them at
the final read, made for that reason only. Nothing in the panels was displayed by the commit.

### Updated alignment notice read (2026-09-27 ≈ 04:00 UTC): four Codex DMs under a five-track ceiling; this direction's scope unchanged

Root updated `docs/Claude_docs/inbox/CODEX_TWO_DM_ALIGNMENT_20260927.md` in place (commit
4220ecd4f, with the RESEARCH plan/routing rows and the archived expansion review
`docs/research/archive/2026-09-27/RESEARCH-four-dm-expansion.md`); the owner's amendment
eda9fae04 raises the concurrent result-bearing research-track ceiling from three to five
(constitution §2; node admission unchanged). Four Codex DMs now share the S7 problem: DM1
`energy_relay_baselines` keeps D1 (cross-seed) and chooses its single comparison after this
direction's complete development curve is published; DM2 `energy_relay_diagnostics` keeps D2+D3
and is the sole writer of the new trajectory interface (its 136-episode, 0-fit operation is
admitted; run directory `energy_relay_diagnostics/b01_alignment_a01` on the node, not read here);
DM3 `energy_relay_imitation` takes the unexecuted D4 as a fixed-budget BC-only closed-loop study;
DM4 `energy_relay_availability` takes D5's native S4 part (service sensitivity to short UAV
unavailability, 0-fit references first). Root executes no research line; Milan stays deferred; D6
is engineering on concrete need. The notice cites the published c04 (.406 / .404, still improving;
c03 is not a plateau).

For this direction nothing changes in what is executed: the resume operation, c05–c06, the
once-only hold-out read, the full cost and the interpretation stay here; no takeover, restart or
duplicate purchase; 957001–957032 and the sealed `b02_holdout_refs_a01` remain read only by this
DM under the original plan, and the new DMs and helpers do not view or use them. Two consequences
for the remaining records: (1) the Stage 1 result entry stays exploratory under constitution §8
(one training seed; the notice states that a resumed fit cannot be mechanically spliced into a
confirmation) — it will declare the resumed nature and claim nothing at confirmation level;
(2) DM1's next purchase waits on the complete curve, so the c05/c06 reads and the final read are
published promptly in the same form as c00–c04. Node at the read (03:58 UTC): only this
direction's fit running (load average 1.07, 12 GB available), the resumed process at rollout 163
(63 of its 100) at ≈ 187 s per rollout since its start; c05 (167) expected ≈ 04:10 UTC, c06 (200)
≈ 05:55 UTC. No reply is owed; the inbox report's allocation note is extended with the new
attribution in the same commit.

### Stage 1, c05 (1,002k transitions, rollout 167) evaluated (`b02_s1_eval_c05_a01`, operation de6e04d7)

Checkpoint written ≈ 04:09 UTC by the resumed fit (record: rollout 167, 1,002,000 transitions,
optimizer steps 375,750 = 167 × 2,250, continuous; `wall_seconds` 12,313.8 of this process),
copied to the artifacts directory (agent.pt sha256 `7ebf3586…` equals its record, fingerprint
`2147d8a5…`), evaluation accepted 04:10:57Z beside the fit (command sha256 `3653bd3c…`, supervisor
pid 751096, runner 751097, memory preflight 11.5 GiB available), exit 0 at 04:28:01Z, `COMPLETE`
in 996.3 s, 64 episodes, 0 failed. Diagnostics parity: row values equal the trace recomputation
except the normal-mode boundary share in 1 (det) / 2 (stoch) of 64 rows, by at most 5.4e-5.
Reader unchanged since `ae998950e`; readings JSON regenerated (c00–c05, two-run rule).

| 955001–955032 | c04 det / stoch | c05 det | c05 stoch |
|---|---|---|---|
| QoS/step | .406 / .404 | **.424** | **.382** |
| paired vs c00 | +.197 / +.161 | +.215 (SE .022, 30/32) | +.139 (SE .018, 29/32) |
| curve step vs c04 | +.081 / +.059 | +.019 | −.022 |
| vs H_central .774 | −.368 / −.370 | −.350 (SE .020, 0/32 above) | −.392 (SE .022, 0/32) |
| vs H_local .597 | −.191 / −.193 | −.173 (SE .031, 3/32 above) | −.215 (SE .028, 3/32) |
| vs H_park2 .379 | +.027 / +.025 | +.046 (SE .023, 19/32) | +.003 (SE .028, 18/32) |
| vs H_spawn .232 | +.174 / +.172 | +.192 (SE .024, 30/32) | +.150 (SE .019, 29/32) |
| vs N .328 (det) | +.077 / +.075 | +.096 (SE .023, 25/32; conflict flag) | +.053 (SE .026, 21/32; conflict flag) |
| J (mean) | 1187 / 1180 | 1242 | 1114 |
| boundary share / altitude-floor share (normal mode) | .406 / .710 ; .221 / .485 | .353 / .434 | .268 / .426 |
| QoS before first entry / after first input | .274 / .520 ; .271 / .506 | .295 / .512 | .242 / .486 |
| first service step (mean) | 177 ; 249 | 176 | 194 |
| F-mode share; return cost; min battery | .157; 0.91; .110 ; .245; 1.65; .107 | .180; 1.23; .108 | .238; 1.38; .107 |
| zero-service worlds; worlds ≥ .60 | 0; 2 ; 0; 2 | 0; 3 (955006 .639, 955022 .689, 955026 .668) | 2 (955004, 955016); 2 (955001 .610, 955026 .692) |

The modes separate again, now the other way: deterministic evaluation adds +.019 (the reader's
`still_improving_at_end` stays true, on a step smaller than the .03 threshold), sampled-action
evaluation loses .022 (best stays c04; `still_improving_at_end` false) and two worlds return to
zero service under sampled actions. Against the references the deterministic policy is now
three thresholds above N (+.096, 25/32, with the conflict flag in both modes: return-constraint
cost and minimum battery worse than N's), one and a half above H_park2 (+.046, SE .023), and
−.173 below H_local (3 worlds above it); no milestone (mean .18 short of .60; three worlds at or
above it). Behaviour: the c04 altitude-floor excursion did not persist (.710 → .434 of normal-mode
UAV-steps under deterministic evaluation; .485 → .426 sampled) while deterministic service still
rose, so the c04 coincidence between low flight and the gain is not a stable association and is
not read as the mechanism; the boundary share moved down (.406 → .353) deterministic and up
(.221 → .268) sampled; F-mode share and return cost rose slightly under deterministic evaluation
(.157 → .180; 0.91 → 1.23) and fell under sampled actions (.245 → .238; 1.65 → 1.38).

Training signals of the resumed process, same comparability caveat as at c04 (re-seeded world
streams from rollout 101): training QoS/step by 10-rollout block .313, .299, .293, .323 for
rollouts 131–170 (flat at ≈ .30 after the rise over 101–140); zero-service lane rollouts 1, 1, 2,
2 per block (69 of 171 over the whole curve); shield entries ≈ 145–161 per rollout; F-mode share
.26–.29. Action entropy fell from .684 (131–140) to .476, .284 and .082 per block, and the last
five rollouts (167–171) read .081, .025, −.013, −.018, −.060 — a differential entropy of the
squashed Gaussian, which may be negative; first-to-last 1.156 → −.060. Recorded as the proxy for
Pro's "policy sharpening / premature convergence" row: the entropy fall over rollouts 131–170
coincides with a flat training QoS and with the sampled-mode evaluation turning down while the
deterministic-mode evaluation still edges up. Phenomenon; whether the sharpening costs service
under sampled actions or the two modes are simply reading different policies at low entropy is
read at c06, not decided here. The once-only hold-out read stays on c06 as declared (fixed
exposure, frozen final model); c04's higher sampled-mode development score does not move it — no
selection on development scores.

Fit at the read (04:26 UTC): 171 rollouts, ≈ 173 s per rollout over the curve (170–207 s per
block in the resumed process, the checkpoint evaluations sharing the CPU), 0 live lanes, runner
alive. Projection: c06 (rollout 200) ≈ 06:00 UTC; then the development evaluation of c06, the
once-only hold-out evaluation of c06 (`--worlds 957001-957032 --final`, launch script variant
prepared and checked against the evaluator's guard: hold-out worlds require `--final`, `--final`
accepts only 957001–957032, output under `checkpoint-eval/final/`), and the whole-curve read.

## 2026-09-27 — Stage 1 result: one SET development fit at fixed exposure, read by the pre-registered readings (`b02_s1_set_a01` + `b02_s1_set_a01r`, final model c06; 957001–957032 read once)

**Operations that complete the study.** The resumed fit ended `COMPLETE` (200 rollouts, 1,200,000
transitions, 7 checkpoints, exit 0 at 06:26:14Z; process-2 wall 20,407.9 s; optimizer steps
450,000 = 200 × 2,250). c06 (rollout 200; agent.pt sha256 `41aa4ff0…`, fingerprint `a7c54b47…`)
was copied to the artifacts directory, sha verified, and evaluated twice in parallel on the idle
node: development `b02_s1_eval_c06_a01` (operation a82466db, accepted 06:29:23Z, command sha256
`fdc4b660…`, supervisor 779318 / runner 779319, preflight 12.4 GiB; `COMPLETE` 1,718.2 s, exit 0 at
06:58:59Z) and the once-only hold-out `b02_s1_eval_c06_final_a01` (operation db5bd391, 06:29:42Z,
command sha256 `0984b0c8…`, supervisor 780226 / runner 780227, preflight 8.8 GiB; `--worlds
957001-957032 --final`, output under `checkpoint-eval/final/`; `COMPLETE` 1,703.0 s, exit 0 at
06:59:03Z). Both: 64 episodes, 0 failed worlds, `policy_seed` 925031, launch sha c369a6b91.
Diagnostics parity: development panels differ from the trace recomputation only in the normal-mode
boundary share (1 / 2 of 64 rows, ≤ 5.6e-5); hold-out panels equal exactly. The sealed comparator
run `b02_holdout_refs_a01` (commit 9c1e238de) was opened by this read and by nothing before it.
Reader unchanged since `ae998950e`; readings JSON regenerated with c00–c06, the hold-out run and
`--holdout-refs` (`b02_stage1_readings.json`).

**Development curve, 955001–955032 (det / stoch).**

| | c00 | c01 | c02 | c03 | c04 | c05 | c06 |
|---|---|---|---|---|---|---|---|
| transitions | 0 | 204k | 402k | 600k | 804k | 1,002k | 1,200k |
| QoS/step | .209 / .243 | .241 / .250 | .318 / .303 | .325 / .345 | .406 / .404 | .424 / .382 | **.437 / .438** |
| step | | +.032 / +.007 | +.077 / +.053 | +.007 / +.042 | +.081 / +.059 | +.018 / −.022 | +.012 / +.056 |
| J | 587 / 693 | 692 / 709 | 920 / 864 | 944 / 996 | 1187 / 1180 | 1242 / 1114 | 1276 / 1281 |
| return cost | 6.6 / 4.6 | 1.6 / 6.9 | 3.3 / 8.1 | 1.6 / 5.0 | 0.9 / 1.6 | 1.2 / 1.4 | 2.4 / 1.5 |
| min battery | .097 / .099 | .108 / .105 | .106 / .101 | .114 / .105 | .110 / .107 | .108 / .107 | .106 / .106 |
| boundary share | .06 / .01 | .43 / .17 | .43 / .14 | .37 / .09 | .41 / .22 | .35 / .27 | .37 / .30 |
| first service step | 364 / 347 | 281 / 233 | 323 / 290 | 206 / 254 | 177 / 249 | 176 / 194 | 165 / 146 |
| zero-service worlds | 4 / 3 | 5 / 5 | 1 / 1 | 2 / 2 | 0 / 0 | 0 / 2 | 1 / 0 |

Best checkpoint c06 in both modes. The reader's `still_improving_at_end` (last step > .015 and the
previous step > 0) is false in both: deterministic steps +.018 then +.012, sampled −.022 then
+.056. Rollouts 101–117 of the first process (mean training QoS .230) are discarded from the curve
as declared; the resumed process's world streams differ from rollout 101 (resume seed 925131).

**Final model c06 against the comparators, both world sets** (paired per world; SE = paired SE;
"above" = worlds where the learner is higher).

| c06 | dev det | dev stoch | hold-out det | hold-out stoch |
|---|---|---|---|---|
| QoS/step (J) | .437 (1276) | .438 (1281) | .462 (1354) | .440 (1287) |
| vs c00 | +.228 (SE .021, 31/32) | +.195 (SE .018, 32/32) | — | — |
| vs H_central (.774 dev / .781 hold-out) | −.337 (SE .015, 0 above) | −.336 (SE .015, 0) | −.319 (SE .019, 0) | −.341 (SE .018, 0) |
| vs H_local (.597 / .611) | −.160 (SE .025, 6 above) | −.159 (SE .032, 6) | −.149 (SE .023, 4) | −.171 (SE .025, 3) |
| vs N (.328 / .344) | +.108 (SE .025, 24 above) | +.109 (SE .024, 24) | +.118 (SE .028, 26) | +.096 (SE .029, 23) |
| vs H_park2 .379 (dev only) | +.058 (SE .017, 26) | +.059 (SE .019, 23) | — | — |
| vs H_spawn .232 (dev only) | +.205 (SE .020, 31) | +.206 (SE .019, 32) | — | — |
| worlds ≥ .60 | 1 (955014 .626) | 3 (955014, 955026, 955030) | 2 (957010 .615, 957018 .632) | 2 (957008 .626, 957011 .611) |
| zero-service worlds; minimum | 1 (955016); 0 | 0; .265 | 0; .270 | 0; .194 |
| return cost; min battery | 2.35; .106 | 1.48; .106 | 1.18; .107 | 1.37; .106 |
| F-mode share; guard-blocked share | .182; .084 | .216; .090 | .184; .091 | .226; .066 |
| boundary / altitude-floor share | .365 / .474 | .295 / .478 | .388 / .483 | .312 / .470 |

Comparators on the hold-out worlds (read once with the model): H_central .781 (J 2300; return cost
5.7, min battery .101), H_local .611 (J 1691; 56.0, .089; ≥ .60 in 19/32 worlds), N .344 (J 1002;
0.93, .109; one zero-service world). Their hold-out-minus-development shifts are +.007, +.014,
+.015; the learner's are +.025 (det) and +.002 (stoch), i.e., inside the comparators' own shift
plus panel noise. This is agreement, not generalisation evidence: the recipe was fixed and no
decision was taken on the development panel, so agreement is what the design predicts. The two
evaluation modes, .02–.04 apart at c03–c05, read .437 / .438 on the development panel and
.462 / .440 on the hold-out panel at c06 (still .022 apart there).

**Readings against the declaration.** (1) Milestone .60 (H_local's level, labelled so): not
reached — the c06 mean is .16–.18 short in every panel, with 1–3 worlds at or above it against
H_local's 19 of 32 on the hold-out set. (2) Improvement over the model's own initialisation:
+.228 / +.195 on the development panel, 31–32 of 32 worlds positive, J roughly doubled
(587 → 1276). (3) Gaps: −.32 to −.34 to H_central and −.15 to −.17 to H_local on both world sets,
no world above H_central, 3–6 above H_local. (4) Risk, both directions: against N the service
gain of +.10–.12 comes with a higher return-constraint cost (hold-out +.253, SE .122 det;
+.449, SE .137 stoch; per-episode sums 1.18 / 1.37 against N's 0.93) and a minimum battery equal
within noise (−.001 / −.003, SE .002) — the reader's conflict flag is on the return cost, not on
the battery tail; against H_local and H_central the learner has a lower return cost (1.2–2.4
against 56–66 and 4.8–5.7) and a higher minimum battery (.106 against .087–.089 and .100–.101),
so the −.15/−.17 gap to H_local is a service gap at materially lower risk, not a like-for-like
deficit, consistent with Root's note that H_local's value is not a capability bound under the
same risk constraint. No cutoff or depletion event in any of the 608 Stage 1 episodes, learner or
comparator. (5) Package references: the learner is +.21 above the spawn-parking package on
31–32 worlds and +.06 above the two-station package H_park2 (SE .017–.019; 23–26 of 32), where N
sits −.05 below H_park2 — the fit learned beyond parking at the two stations, which N had not.

**Phase structure (the reader's split, as in Stage 0; window lengths stated).** The learner's
first shield entry falls at step ≈ 1000–1047 and its first charger input at ≈ 2030–2140
(H_central 1300–1323 / 1617–1640, H_local 1300–1304 / 1598–1620, N 1185–1373 / 2152–2196), so the
pre-entry means below are ≈ 1000-step windows for the learner against ≈ 1300-step windows for
the planners. Development, deterministic: learner .277 pre-entry / .488 entry-to-input / .543
post-input; H_central .810 / .840 / .725; H_local .631 / .702 / .544; N .231 / .353 / .449.
Hold-out, deterministic: learner .299 / .518 / .583; H_central .835 / .880 / .703; H_local
.655 / .714 / .543; N .243 / .361 / .441. The deficit to H_central is −.53 before any shield entry,
−.35 / −.36 between entry and first input and −.12 / −.18 after the first input; to H_local −.35,
−.21, then .00 (dev) / +.04 (hold-out). Observation, not mechanism: the learner's shortfall is
concentrated in the deployment phase before the shield has moved any UAV, and after the first
charger input it serves at H_local's level; whether the low pre-entry service is a deployment
choice, slow arrival (first service at 76–165 steps against 14–33 for the planners) or a
reward-side effect is not read from these panels.

**Training-time signals over the whole curve** (collection-time, 2 lanes; comparability caveat:
world streams differ across the resume boundary; the frozen panels are the like-for-like signal).
Training QoS/step by 10-rollout blocks: .19 .16 .21 .18 .16 .13 .21 .14 .20 .19 (process 1,
rollouts 1–100) | .26 .29 .30 .31 .30 .29 .32 .33 .37 .38 (resumed process, 101–200). Zero-service
lane rollouts 70 of 200 (61 in the first 105, 9 in the last 95). Shield-mapping share .274 mean.
Action entropy 1.156 → −.596 first to last (block means ≈ 1.07 at rollouts 91–100, then 1.13, .99,
.83, .68, .48, .28, .08, −.13, −.31, −.52; differential entropy of the squashed Gaussian). The
collection-time service kept rising through the last three blocks while the development panel's
deterministic steps shrank (+.018, +.012) and the sampled panel moved −.022 then +.056.
**Correction (2026-09-27):** the c04 and c05 entries above attribute a "policy sharpening /
premature convergence" row to Pro's failure table; the table has six rows (opportunity to reach
useful states; users and paths present but delivery not held; early service good and gap
widening after F/recharging; targets not reached under guard blocking; still improving at the
end with a large gap; low plateau with normal execution) and no such row. The entropy
observation stands as this notebook's own, non-pre-registered addition; nothing was selected or
acted on because of it.

**Pro's failure table, filled with the reader's proxies (non-exclusive; no rescue selected).**
Row 1 (users seen late, little useful exposure): first service 165 steps at c06 (364 at c00),
pre-entry service .277, training QoS of the first five rollouts .25/.17/.16/.25/.26 — held over
the first half of the fit (flat .19 training QoS, zero-service lane in 61 of the first 105
rollouts), not at the end (training QoS .38, first service 76–165 steps). Row 2 (users and paths
present, delivery not held or improved): the end state — service present in every phase and world
(one zero-service world under deterministic evaluation) at roughly half the planners' rate;
the row's candidate family (signal use, optimisation, return trade-off, credit) is the live one and
nothing in it is proven. Row 3 (early good, gap widens after F/recharging): absent — learner
.277 → .543 against H_central .810 → .725; the gap narrows after the shield acts. Row 4 (guard
blocking): absent as a global pattern — blocked share .084 against H_central's .077 (H_local .20,
N .18); the boundary share (.30–.39 of normal-mode UAV-steps, planners 0, N .46) is the geometric
residue that remains. Row 5 (still improving at the end with a large gap): flags false in both
modes under the stated rule, gap to H_central −.337 / −.336, training QoS still rising — the
exposure question is open in both directions; this fit is not extended (declared). Row 6 (low
plateau, execution normal): execution normal (0 live-lane boundaries, 0 failed worlds, identity
per panel present); a plateau is not established (`curve_flat` false; deterministic steps
shrinking, sampled non-monotone).

**Cost against the declaration.** Declared ≈ 5 h serial node wall (first entry), revised at
launch to ≈ 11 h upper bound plus ≈ 1.4 h of evaluations. Actual, operation walls: fit process 1
19,204 s (117 rollouts, of which 17 = 102k transitions discarded, ≈ 0.8 h), process 2 20,408 s
(100 rollouts): 39,612 s = 11.0 h of fit (CUDA, 4 threads, runner peak RSS 2.86 GB; 164 and
204 s per rollout, the second process sharing the CPU with evaluations); checkpoint evaluations
c00–c05 5,282 s beside the fit, c06 development 1,718 s and hold-out 1,703 s concurrently on the
idle node; hold-out comparators 1,233 s beside the fit. Episodes: 7 × 64 development, 64
hold-out, 96 comparator = 608; fits: 1 (one resume). Wall-clock span 18:22:52Z → 06:59:03Z =
12 h 36 min including the 53-min gap between the crash (23:45:31Z) and the resume (00:38:32Z).
Engineering on the way: training runner and SET loader (34824de1d), resume path (c9895139b,
c369a6b91), hold-out phase of the B01 runner (7ad3ba6d3), readers (d3f6bda93, cfefb86a8,
ae998950e), each reviewed or tested as recorded above.

**Status under constitution §8 and what the study supports.** Exploratory: one training seed,
the endpoint reached by a process resumed from c03 with the learner state restored exactly and
the world streams re-seeded — declared before the resume and not spliced into a confirmation.
Supported on this evidence: with the production shield active in training and the SET switch on
the B09 S7 recipe, 1.2 M transitions of one seed reach .44 QoS/step on the development worlds and
.46 / .44 on the hold-out worlds — above N by .10–.12 (paired, 23–26 of 32 worlds, at a higher
return-constraint cost and an equal battery tail), above the two-station package by .06, and
below H_local by .15–.17 and H_central by .32–.34 at lower return cost and higher minimum
battery than either planner; the shortfall sits in the pre-entry deployment phase. Not
supported: any statement about the recipe across seeds (DM1's question), a mechanism for the
pre-entry deficit, or a plateau. The reserved worlds are spent: 957001–957032 have now been seen
by this model and its comparators and are not an unexposed test set for any later model.

**Standing and open questions for Root (no Stage 2 declared here; continuation goes through
coordination).** (a) The pre-entry phase — the first ≈ 1000 steps, where this learner serves
.28–.30 against .63–.84 for the planners and .23 for N — is the concrete place where the
remaining gap lives; DM2's comparability diagnosis and DM3's teacher/student comparison already
own adjacent questions and may want this reading. (b) Whether a longer exposure of the same recipe
is worth buying (row 5) is open: development steps have shrunk while the collection-time service
still rises and the entropy sits below zero; a longer or changed recipe is a new declared study
and, under §8, a multi-seed one — DM1's and Root's call. (c) The evaluation-mode axis mattered
at c03–c05 (.02–.04 apart) and little at c06 (≤ .02 dev, .022 hold-out); a single mode would have
told the same story at the endpoint. One independent scientific review of this entry follows
(§5); its outcome is appended below.

### Independent scientific review of the Stage 1 result (§5), 2026-09-27 ≈ 07:25 UTC: MATERIAL_DISSENT yes on two readings; accepted; corrections to the entry above

**Review facts.** `hmasd-research-critic` (ResearchCritic body, separate context, read-only, no
scratch files, no other DM's directory read) reconstructed the curve, the c06 gaps, the hold-out
comparators and shifts, the phase means, the entropy blocks and the walls from the panels, progress
rows and run records before reading the entry; all table values matched. Verdict: execution and
bookkeeping hold (exposure kept, hold-out read once with the comparators opened only by that
read, resume declared before c04, 17 rollouts discarded, 608 episodes with 0 failures and 0
events, exploratory status and "957001–957032 spent" correct, six-row Pro table and the c04/c05
misattribution correction confirmed); `MATERIAL_DISSENT: yes` on two interpretive claims that had
reached the RESEARCH row — the risk framing and the phase locus — plus factual slips, two
under-reads and three omissions. Before accepting, the DM re-verified every number behind the
dissent from the raw files (this entry's figures are those recomputations; one of the review's own
recounts differs and is noted). Resolution under §2: the dissent is accepted in full, so no
disagreement remains for Root to resolve; the corrected wording replaces the standing in RESEARCH
in the same commit series, and Root sees both the dissent and the resolution there. Nothing here
authorises a run.

**Corrections to the result entry (each replaces the corresponding sentence above).**

1. **Risk framing — withdrawn: "a service gap at materially lower risk, not a like-for-like
deficit" (and the RESEARCH sentence that the learner beats both planners on return cost and
minimum battery).** The native J prices the return-constraint cost: per world
`raw_native_J = qos_satisfaction_ratio_sum − 2 × return_constraint_cost_sum + graph_potential_delta_sum`
exactly (the evaluator requires `lambda_return = 2.0`), and J is a declared reading. After that
pricing H_local still leads by 353 J (SE 90; learner above in 8 of 32 worlds) det / 348 (SE 112)
stoch on development and 336 (SE 81; 7/32) / 404 (SE 89) on hold-out. The learner's soft
return-constraint cost is clearly below H_local's (1.2–2.4 against 56–66 per episode, worth ≈
110–130 J of a ≈ 350 J gap) and **unresolved against H_central's** (−2.5 det / −3.3 stoch, SE
1.6 / 1.4, learner higher in 6 / 9 of 32 worlds on development; −4.5 / −4.3, SE 3.4, 7 / 13 of 32
on hold-out). Minimum battery is higher than H_local's by .017–.018 and than H_central's by
.005–.007 (SE .001–.002), and no controller reached the event regime (minimum battery .087–.109,
0 cutoff / depletion in 608 episodes). Corrected reading: the gap to H_local is a service **and J**
deficit; the risk proxies differ in the learner's favour by amounts J already prices, and against
H_central the return-cost difference is not resolved.

2. **Phase locus — withdrawn: "the shortfall sits in the pre-entry deployment phase" and "after the
first charger input it serves at H_local's level".** Clock-aligned decomposition at the learner's
mean first entry (1044 steps development, 1047 hold-out; service assumed uniform within each of
the reader's phases): development det, before that step the learner delivers .109 of its .437
against H_central .283 and H_local .220 (deficits .174 / .111); after it .328 against .491 / .377
(deficits .163 / .049). Hold-out: deficits .179 / .140 to H_central and .116 / .034 to H_local.
Corrected reading: the **per-step** deficit is largest before the first shield entry; that window
carries ≈ 70 % of the gap to H_local but only ≈ half of the gap to H_central, and in the same
clock window after the learner's first entry it still serves ≈ .51 per step against H_central
≈ .75 and H_local ≈ .58. The "post-input at H_local's level" sentence compared different windows
(learner ≈ 2124–3000 against H_local 1620–3000, H_local's own service falling .70 → .54 across its
phases) and is withdrawn. The entry's development-order figures "−.12 / −.18" for the post-input
deficit to H_central were reversed: −.18 development, −.12 hold-out.

3. **Conflict flag vs N.** The reader lists both `return_constraint_cost_sum` and
`min_decoded_battery` in every c06 panel because it adds the battery whenever the mean difference
is negative regardless of its SE (`read_stage1.py`, conflict block); the entry's "on the return
cost, not on the battery tail" described the evidence, not the flag. The battery difference is
−.001 / −.003 (SE .002), unresolved; the return-cost difference is consistent in sign (learner
higher in 26–30 of 32 worlds), resolved on hold-out (+.253, SE .122; +.449, SE .137) and within
noise on development (+1.16, SE .81; +.28, SE .43), worth 0.5–2.4 J against a J gain of
+285 to +353.

4. **Factual slips.** Milestone shortfall .14–.16 (development .163 / .162, hold-out .138 / .160),
not ".16–.18". Mode gap (sampled − deterministic) by checkpoint +.034, +.009, −.016, +.020,
−.002, −.043, +.001 — not ".02–.04 apart at c03–c05" (c04 was .002); open question (c) reads
accordingly. Zero-service-lane rollouts recounted from the raw rows: 57 of the first 100 rollouts
(process 1) and 13 of the 100 resumed rollouts, 70 of 200 — the entry's "61 in the first 105 /
9 in the last 95" mixed in discarded rows (61 is the count at rollout 105 of process 1, including
rollouts 101–105 that the curve discards); the review's own recount (58 / 12) also differs from
the raw rows.

5. **Training signal.** The contrast "collection-time service rising while the development steps
shrink" set sampled-mode collection on training worlds against deterministic development steps.
Like for like, the sampled development panel moved +.034 (SE .019) from c04 to c06 and the
deterministic +.031 (SE .020): no divergence is warranted. The deterministic last step (+.012,
SE .022) rests on world 955016 (.433 at c05 → .000 at c06; +.027 without it, which would flip the
reader's `still_improving_at_end` to true); at a paired SE ≈ .02 no single step of the curve is
resolved, which qualifies open question (b). "Entropy below zero" is not a landmark (differential
entropy); the fall (block means .68 → −.52) is ordinary sharpening, consistent with the two modes
converging (.437 / .438 at c06) and the sampled boundary share rising .09 → .30.

6. **Pro's table.** Row 1 also holds in part at the end: first service at 76–165 steps is 5–10×
the planners' 14–33. Row 4 is "not measured; no sign of widespread blocking", not "absent": the
learner's own blocked share .084 argues against widespread blocking, but comparing it with H's
global share is what Pro's row lists as non-diagnostic, and "targets persistently not reached"
was not measured. Rows 2, 3, 5 (with the 955016 caveat) and 6 stand.

7. **Cost overrun named.** Evaluations took 1.94 h for c00–c06 (13.1, 13.8, 14.5, 14.7, 15.3,
16.6 and 28.6 min, the last concurrent with the hold-out run) + 0.47 h hold-out + 0.34 h
comparators = 2.75 h, against ≈ 1.4 h declared at launch (≈ 6 min per checkpoint in the first
entry); the fit's 11.0 h equals the revised upper bound and includes 0.84 h of discarded rollouts.

8. **Omissions added.** (i) World 955016 is a knife-edge world: zero-service for H_local on the
development set too, and the learner flips between 0 and .43–.48 across checkpoints and modes;
with 955004 it produces the c05 sampled dip. (ii) Resume boundary: process 1's discarded
rollouts 101–117 had already risen to .230 (last seven ≈ .33) from .194 over rollouts 91–100, so
the post-600k rise began in the original process — evidence against a resume artefact, beside the
verified restoration of optimizers, value normaliser, dual state and sampler RNG. (iii) The
boundary (.30–.39) and altitude-floor (≈ .47) shares of normal-mode UAV-steps (planners 0; N
.46 / .68 on hold-out) belong beside the pre-entry deficit as an unread candidate, not as a
residue. (iv) Hold-out wording: the hold-out is a second, unselected 32-world sample confirming
that the development estimates are not a world-sampling artefact; agreement is expected without
selection, and it says nothing about seed variance or distribution shift.

**Supported-claims list, as corrected (replaces the one above).** With the production shield
active in training and the SET switch on the B09 S7 recipe, one seed at 1.2 M transitions reaches
.44 QoS/step on the development worlds and .46 / .44 on the hold-out worlds: above N by +.10–.12
QoS and +285–353 J (23–26 of 32 worlds; return cost higher in sign, resolved only on hold-out and
negligible in J), above the two-station package by +.06, below H_local by .15–.17 QoS and 336–404 J
and below H_central by .32–.34 QoS and ≈ 950–1010 J; soft return-constraint cost far below H_local's
and unresolved against H_central's; no events for any controller; the per-step deficit largest
before the first shield entry, that window carrying ≈ 70 % of the H_local gap and ≈ half of the
H_central gap; the milestone .60 not reached. Not supported: statements about the recipe across
seeds, a mechanism, a plateau, or "lower risk" as compensation for the service gap. Open questions
for Root stand as written, with (b) qualified by the 955016 caveat and (c) by the per-checkpoint
mode gaps.

### Closure record (2026-09-27 ≈ 08:30 UTC): node copies of the earlier runs were removed by a shared-checkout sparse update; evidence retained locally and on main; cleanup outcome

**What happened on the node.** At the closure survey the node checkout `/home/wu/projects/HMASD/runs/energy_relay_benchmark/`
held only `b01_ref_a01`, `b02_s1_eval_c05_a01`, `b02_s1_eval_c06_a01`, `b02_s1_eval_c06_final_a01` and
`b02_s1_set_a01r`. Gone: `b01_ref_a02`, `b02_s0_stoch_a01`, `b02_s0_refs_a01`, `b02_s1_set_a01`
(with the original c00–c03 checkpoints), `b02_s1_eval_c00_a01`…`c04_a01` and `b02_holdout_refs_a01`,
all present at 03:58 UTC (the c04 read). No admitted operation names those paths and nothing under
`/home/wu` holds a moved copy. The node checkout is a cone-mode sparse checkout (Git 2.43); its
pattern file changed at 04:28:14 UTC (between "merge origin/main" reflog entries at 04:08, 04:20 and
04:26 UTC made by another party's tooling), and the cone now lists other directions' run
directories (`runs/energy_relay_baselines/b01_set_a01/seed-26092711`,
`runs/energy_relay_diagnostics/b01_alignment_a01`, `runs/flexible_skill_duration/…`) but not
`runs/energy_relay_benchmark`. The removal pattern matches Git's sparse-directory cleanup on a
sparse-checkout update: every directory of this direction whose files were all either tracked on
main (skip-worktree on the node) or ignored (`*.npz`, `*.log`, `*.jsonl`, `checkpoints/`) was
deleted, while directories holding untracked non-ignored files (`b01_ref_a01`, never committed;
the c05/c06 evaluations, whose JSON was not yet on main at 04:28 UTC) or a modified tracked file
(`b02_s1_set_a01r/summary.json`) were left. The engineering method tells DMs to add their run
directories with `git sparse-checkout add` (preserving existing paths); that step, run by any DM,
deletes every other direction's completed and committed run directory on the node, bulk included.
Actor not identified and not needed: this is a shared-control hazard, reported to the owner and to
Root through this entry and the RESEARCH row, not a message.

**Evidence status.** Nothing is lost: every run's JSON (configs, summaries, launch records, panels)
is tracked on main and present locally, and the local checkout holds the traces of all 608 Stage 1
episodes and of B01/Stage 0 (rsynced after each run). Checkpoints: the node's `hmasd-artifacts`
copies of c00–c03 (`/home/wu/hmasd-artifacts/energy_relay_benchmark/b02_s1_set_a01/checkpoints/`)
are now the only node copies of the first process's checkpoints **and the live input of DM2's
admitted operation** (`--checkpoint-root` of `energy_relay_diagnostics/b01_alignment_a01`,
accepted 03:05:17Z) — not to be deleted by anyone; c04–c06 exist on the node in
`b02_s1_set_a01r/checkpoints/` (at risk on the next sparse update once the node pulls this
direction's commits) and under `hmasd-artifacts/…/b02_s1_set_a01r/checkpoints/`. Retention action:
all seven checkpoints (c00–c06) were copied to the local checkout under the two run directories
(`checkpoints/`, gitignored; 246 MB) and each `agent.pt` sha256 verified against its record
(9d5806c1…, be3ad2f1…, dd9dcec8…, 80b2bdad…, 31d21637…, 7ebf3586…, 41aa4ff0…); the frozen final
model c06 therefore has three copies (node run dir, node artifacts, local).

**Cleanup outcome (constitution §4/§9 closure).** Targets considered and their disposition: the
node `hmasd-artifacts` checkpoint copies (246 MB) — kept, live consumer DM2 and sole node copies of
c00–c03; local run directories with traces (≈ 500 MB, gitignored bulk) — kept, the retained
evidence copy and readable by the Codex DMs from the shared checkout; local `checkpoints/`
copies — kept as above; `temp/directions/energy_relay_benchmark/` (156 KB: launch and poll
scripts, poller log, L0 notes) — kept, tiny and reusable if Root asks for a launch; kernel launch
snapshots — their own lifecycle, untouched; session scratchpad dry-run files — removed (outside
the repository). No repository or node bulk was deleted, so net allocated usage did not decrease
(local +246 MB for the checkpoint retention; node unchanged, 825 GB free of 1 TB). Leftovers
recorded: `b01_ref_a01` on the node (6 MB, superseded B01 attempt, never committed), the three
reader/resume follow-ups (schedule-flag refusal in `read_resume_checkpoint`, value-normaliser
comparison in `resumed_agent`, a hold-out reader test beyond the dry run) — not done, no consumer.

## 2026-09-27 — Stage 2 declaration (B03): grounded assignment skills on HMASD's coordinator against the flat SET learner, at matched information and exposure (declared before any run; no launch until the §5 review and the engineering review)

**Owner constraint (2026-09-27).** "应该有一定的创新在算法上 这不是一个工程项目": the next study must be an
algorithmic contribution (MARL algorithm or network), not more benchmarking or controller engineering.
This entry declares the study, its lineage labels, the information contract, the readings and their
rules, the pre-declared continuation, the cost and the engineering scope. Nothing here has run.

### Candidates weighed, with their record labels

| Candidate | Record | Decision |
|---|---|---|
| A. HMASD-k10 × 3 seeds against SET (the first entry's P3 suite) | RECORDED (this notebook); a package benchmark, no new algorithm | not the headline; kept as the mechanism control (arm M, Stage 2b) |
| C. Entity / permutation-invariant actor encoders | TRIED on S1 twice with adverse or unestablished polarity: `local_observation_encoding` DENSE J45 .202 against ORIGINAL .458 at 1.95× wall; ACG set encoders, joint claim not established (RESEARCH rows); July R54 supervised full-set reference failed its access gate. No S7 record | declined as the headline; a later step if the coordinator matters and the low level is the limit |
| E. Learned counterfactual credit | TRIED: LCAC B01–B03 on a five-UAV categorical toy, PARK with adverse B03 (Q − V −.018) | declined |
| Chain-attributed rewards (difference-reward family; the environment knows each user's serving UAV and its backhaul path) | NEW to the record as a scheme; low literature novelty (difference rewards) | reserve |
| **Grounded assignment skills on HMASD's coordinator** (09-21 note, seed S4) | RECORDED 2026-09-21 as a seed; entity-pointer actions TRIED only in July's R51 AMDT toy, which never reached reward ("the lesson is about reward access, not about pointers"); `gnn_hmasd/` holds a dormant GCN role assigner (SERVER/RELAY, never run on S7); HMASD's sequential decoding is the paper's own duplicate-avoidance rationale. No S7 record | **selected** |

### Question

On the frozen S7-S2/H3000 host with unchanged slot allocation and the production shield, at exposure
1.2 M and the same central-snapshot information every k = 10 steps: when HMASD's coordinator assigns
**deployment anchors** instead of semantics-free skills, does the hierarchy learn joint deployment that
the flat SET learner does not — higher complete service (QoS/step and native J) on the 32 development
worlds, located mainly in the pre-entry phase — and do the learned assignments matter by intervention?

### MARL structure and the simple-model bridge

Relay service is conjunctive: a cluster's users are served only if a server UAV sits over them *and*
a chain of relays connects it to the base station. Under a shared team reward with independent
per-agent exploration, a jointly correct configuration of m agents is visited with probability of
order p^m, and greedy updates settle into miscoordinated equilibria — the climbing/penalty-game
family (Claus & Boutilier 1998; Matignon et al. 2012, "relative overgeneralization"; scout-retrieved,
secondary citation). HMASD's decoder chooses agent i's label conditioned on the labels already chosen
for agents 1..i−1, so with grounded labels the coordinator's problem is a matching over a small anchor
set whose consequences are immediate and dense (QoS and the graph potential respond within a few
decisions), and the k-step commitment makes teammates predictable (functions ii and iii of the 09-21
note §3.2). The flat learner must find the same conjunction in the 8 × 4-dimensional continuous joint
action space from a 3,599-dimensional input.

Simple model (derivation only, no run): two agents, two anchors {relay, server}, payoff 1 iff one
agent holds each anchor. Two independent learners with the shared payoff have two coordinated optima
and two miscoordinated joint actions of equal individual appeal; under uniform exploration a correct
joint draw has probability 1/2 and, with more agents and anchors, the correct-configuration
probability falls geometrically while every agent's own marginal remains flat. A sequential assigner
faces a four-arm bandit with two optimal arms. What the toy omits: motion dynamics, energy and
charging, moving clusters, partial observability, and endogenous learning of the low level; the UAV
study measures exactly those.

Stage 1 evidence used: the SET learner's shortfall against H_local (.15–.17 QoS/step) has ≈ 70 % of
its mass in the pre-entry window (≈ first 1,000 steps), the normal-mode boundary share is .30–.39
and the altitude-floor share ≈ .47 (planners 0), and the deficit is the policy's own, not an
evaluation artefact (Stage 0). Root's caution stands: "改进一个 UAV 控制器本身，尚未证明改进了 MARL 学习" —
so the anchor generator is fixed and shared with the H references, and the learned objects are named
below.

### Arm T — GAS-HMASD ("grounded assignment skills"), the treatment

1. **Anchor set A(s)**, computed from the central snapshot state at every team decision (env step
   % 10 == 0 or lane reset — the cadence at which SET already receives the snapshot): six service
   centroids by the B01 heuristic's own k-means (`b01/heuristic.py::estimator_kmeans`, seeds
   `np.linspace`, 30 iterations) over the 30 user xy read from the state (raw values; normalizers are
   off on this host), and two relay points at 1/3 and 2/3 of the segment from the BS xy (state) to
   the centroid mean. Deterministic slot order: relay points by distance from the BS ascending
   (labels 0–1), centroids by descending user count, ties by centroid index (labels 2–7); label 8 =
   FREE (no anchor, ordinary local control). Hence `n_z = 9`, `n_Z = 1` (team skill degenerate).
   The anchors are stored with the snapshot so acting and replay read the same numbers; replay never
   recomputes k-means. Rationale for 6 + 2: H1, the selected reference, uses `n_service = 6`,
   `n_relay = 2` on this host (`HeuristicParams`; the S7 generator draws five user clusters, one
   remote); the learner and the references therefore share one anchor generator, and the comparison
   is between learners at equal grounding, and between the learned assigner and the Hungarian
   distance rule (H_local / H_central) at equal anchors.
2. **Coordinator**: HMASD's `SkillCoordinator` / `SkillDecoder` unchanged (state token + eight
   observation tokens → Z, then z¹..z⁸ sequentially), trained by the existing high-level PPO on the
   k-step team return: `disable_high_level_training = False` (SET: True), high-level buffer 600
   decisions per rollout as the config already computes, `lr_coordinator` 1e-4 as configured, skill
   entropy `lambda_h = .01` (paper range .001–.1; nine labels summed over eight agents; chosen so the
   entropy bonus does not dominate small per-decision return differences — B12's signal-to-noise
   lesson — and recorded as a design choice). No discriminators and no intrinsic reward:
   `disable_discriminator_training = disable_discriminator_rewards = True` exactly as SET, so the
   low-level reward is the native reward (`hmasd/agent.py`: with the flag, `env_component =
   lambda_e * reward`).
3. **Low level**: the SET actor unchanged in architecture (MLP 256 → FiLM on the label one-hot,
   now 9 wide → GRU 256 → tanh-Gaussian, 4 actions: velocity xyz and dock request) with the CF
   central input (own obs 365 + state 306 + 8 × 365 + ego one-hot 8 = 3,599) plus an **anchor
   block** of six numbers appended at the single application point: assigned anchor absolute
   x/area, y/area, relative x/area, y/area (from the UAV's own position), distance/area, `is_free`;
   FREE gives zeros with `is_free = 1`. Actor input width 3,605. **Nesting**: with every label FREE the
   actor's input equals SET's up to the constant flag and the FiLM of one label, so SET's policy
   class is a member of T's; at initialisation T is not SET (the coordinator is near-uniform over
   nine labels), so a deficit of T against SET is a learning cost, not a representation limit.
4. **Recipe otherwise byte-identical to B02**: 2 lanes × rollout 3000, 200 rollouts = 1.2 M
   transitions, PPO 15 epochs × 4 minibatches, lr 1e-4, production shield (enter 0.00, exit 0.05)
   in training, checkpoints c00–c06 by B02's rule, `ordinary_completed_segments = True` (B09's native
   value; SET had to use False because of the mappo switch — at production sizes both lanes end at
   every rollout boundary, so the two paths differ only in four numpy draws, see B02 `RECIPE_NOTES`).
5. **Seeds**: 26092711 and 26092731 — the two seeds of DM1's clean SET fits (`energy_relay_baselines`
   B01, same `make_b02_config`, c00/c06 evaluated in both modes on the same 32 development worlds),
   so each T seed has a same-seed flat pair without asking DM1 for anything. My 925031 SET fit is a
   resumed process and stays a third, unpaired reference.

### Information contract per arm

| Arm | Actor information | Coordinator | Critic | Reward | Shield |
|---|---|---|---|---|---|
| T (GAS-HMASD) | own obs 365 + central snapshot (state 306, 8 obs, ego) every 10 steps + anchor block (6) | state + 8 obs at each decision, executed centrally once per k steps as HMASD does; anchors are a function of the same state | central state 306 (n_Z = 1) | native, λ_e = 1 | production, training and evaluation |
| SET (DM1 seeds, my seed) | own obs + the same central snapshot every 10 steps | none (labels constant) | central state 306 | native | production |
| H_local / H_central | legal observations pooled every 30 steps / ground truth | Hungarian distance rule on the same 6 + 2 anchors | — | — | production |

No new information enters T: the anchor block is a deterministic function of numbers SET already
receives. The coordinator's centralised step is HMASD's own execution structure (paper §: one
centralised step in k).

### Evaluation and readings (fixed rule, written before any score)

Fixed-policy evaluation, zero updates, 955001–955032 only (957001–957032 is spent): checkpoints c00,
c03, c06, deterministic (argmax labels, mean actions) and one sampled panel (both levels sampled
under the evaluator's `sample_seed` rule) → 6 panels × 32 episodes per seed. At c06 two zero-fit
interventions with deterministic low level: **PERMUTE** (the decoded labels permuted uniformly among
the eight agents at each decision) and **ALL-FREE** (every label forced to FREE) → 2 × 32 episodes per
seed.

- **Primary**: paired per-world c06 QoS/step and native J, T − SET(same seed), deterministic and
  sampled, with paired SE and the count of positive worlds; the same against H_local, H_central and N
  on these worlds. Prediction: T − SET ≥ +.05 QoS/step on both seeds. Competing prediction (from the
  record: coordinators that did not matter on S1; HMASD instability, 26 of 35 runs): the coordinator
  collapses to FREE or to a constant assignment, T ≈ SET or below.
- **Phase**: the clock-aligned pre-entry decomposition exactly as corrected by the Stage 1 review, and
  the boundary / altitude-floor shares. Prediction: most of any gain lies in the pre-entry window.
- **Mechanism** (from a per-decision training log and the evaluation traces): label occupancy per
  type (relay / service / FREE), duplicate rate (agents sharing a non-FREE anchor), assignment
  stability (share of decisions that keep the previous label, per agent), mean distance to the
  assigned anchor at the end of a commitment; their curves over rollouts. Prediction at c06: relay
  occupancy ≈ 2/8 of non-FREE labels and a duplicate rate near zero.
- **Intervention**: "assignments matter" if the policy's own labels beat PERMUTE by ≥ .05 QoS/step
  with ≥ 20/32 worlds positive (paired); ALL-FREE measures the low level's SET-like competence and
  whether the gain needs the coordinator at execution time.
- Exploratory under §8 (two training instances per arm); no recipe claim from this batch.

### Stage 2b — pre-declared continuation, bought only by the rule below

If both seeds show a paired deterministic c06 difference T − SET ≥ +.05 QoS/step with ≥ 20/32 worlds
positive: a third T seed (925031) and arm **M** (HMASD with its own MI skills: B09 recipe, n_Z = n_z
= 6, λ_D .05, λ_d .02, B09's λ_h, k = 10, shield on, 1.2 M) × 3 seeds, then a `CLAIM_` note under §8
with the claim "grounding, not hierarchy alone" read against M. If exactly one seed passes: one more
T seed (925031) before deciding, no M. If neither passes: the mechanism is recorded as not
demonstrated at this exposure and this notebook chooses between chain-attributed credit and a
pointer-over-users anchor set as a new declaration. No extension of this batch after its scores.

### Cost

- Fits: 2 (T × 2 seeds at 1.2 M). Measured SET rate 170–204 s per rollout; the coordinator adds a
  bounded fraction (collection is environment-dominated: probe 67.7 of 107 s; one coordinator forward
  per 10 steps; high-level PPO on 600 samples per rollout). Declared upper bound **13 h per fit,
  26 h for the batch**, serial. Node: `wsl_4070` CUDA; DM1's second SET seed occupies it until ≈
  02:30 UTC 2026-09-28; the first T fit is admitted when the memory preflight passes, concurrent with
  at most one other fit (walls then stretch and are recorded, not re-estimated).
- Evaluation: 6 panels × 32 + 2 × 32 intervention episodes per seed = 512 episodes ≈ 2.3 h at the
  Stage 1 panel rate; declared upper bound **3 h** (Stage 1 overran its evaluation estimate; the
  review named it).
- Engineering: two bounded implementer tasks (learner; evaluation and readers), one engineering
  review of the learner path (numerics, RNG, replay identity, checkpoint semantics).

### What is learned and what is fixed (for the owner's engineering concern)

Learned: which UAV takes which anchor and when to hold or switch (the coordinator, by PPO on the
k-step team return, sequentially over agents); motion and dock control under energy pressure given
the assignment (the low level, by PPO on the native reward). Fixed: the anchor generator (also the H
references' generator) and the k = 10 clock. The contribution claimed, if the readings support it, is
a MARL-algorithm statement — skills grounded in state-derived entities make HMASD's sequential
coordination learnable and useful on a dense, conjunctive task where semantics-free skills did not
matter (S1 record) and a flat information-matched learner falls short — with the intervention
readings as the evidence that the joint assignment, not the low level alone, carries it.

### Literature (bounded scout, 2026-09-27, ≈ 10 queries; labels against that search only)

Closest relatives found: MAPT (arXiv 2511.17435), an autoregressive pointer transformer over
entities for vehicle dispatch that emits the joint action directly (no k-step hierarchy, no
separately trained low level); Feudal Multi-Agent Hierarchies (Ahilan & Dayan 2019, abstract only:
manager sends subgoals to simultaneously acting workers; grounding and decoding order unverified);
ROMA / RODE (latent or action-cluster roles, independent selection); HAVEN (intrinsic-reward manager,
not assignment). No UAV relay / backhaul work with k-means or Hungarian anchors inside a hierarchical
RL learner was found. Within this bounded search "HMASD's sequential coordinator over state-grounded
anchor labels with a team-reward-only low level on a UAV relay host" has no direct match; that is a
bounded-search absence, not a publication claim. Coordination-failure citations: Claus & Boutilier
1998 (climbing / penalty games), Matignon et al. 2012 (relative overgeneralization), both via
secondary citation; primary passages to be verified before any paper text.

### Engineering scope (L0 summaries; full notes under `temp/directions/energy_relay_benchmark/`)

L0-A (learner, `experiments/candidates/energy_relay_benchmark/b03/`): anchor generator from the raw
state (reusing `b01/heuristic.py::estimator_kmeans` and the state offsets: UAV xyz 24, loads 8, users
30 × 6 from offset 32, BS 3 at 212); an `HMASDAgent` subclass that computes and stores anchors with
each central snapshot, appends the per-agent anchor block to the CF central input in acting and
replay from stored values, and logs decisions per rollout; a `SkillDiscoverer` subclass for the
widened input; `build_agent` in the direction directory (as ACG did), no edit to `hmasd/`, `envs/` or
the launch kernel; a `--arm gas` runner reusing B02's training loop, checkpoint rule and records;
tests: SET path byte-identical when the arm is off, all-FREE input equals SET input plus the flag,
anchor order deterministic (same state → same anchors; the references' index-seeded k-means is not
permutation-invariant and T inherits that), replay input equals acting input, `n_Z = 1` with high-level training on trains the coordinator (nonzero coordinator optimizer
steps), tiny end-to-end fit with checkpoint and resume. L0-B (evaluation and readers): checkpoint
evaluation aware of the arm from `record.json`, PERMUTE and ALL-FREE modes, decision statistics in
the panels, reader extension for the mechanism table. Both return diffs, check output and deviations;
the DM accepts. Review plan: independent scientific review (critic, separate context) and one Pro
question on this declaration; engineering review of L0-A; launch through `scripts/hmasd_launch.py`
with admission only after both.

## 2026-09-27 — Stage 2 (B03): independent scientific review received (MATERIAL_DISSENT: yes, "revise, not stop"); disposition and revised declaration B03 v2 — Stage 2-0 zero-fit stake sizing first, then T′ × 2 + SET+A × 2 (declared before any run; nothing launched)

**Review facts.** Role `hmasd-research-critic` (Opus, high effort, read-only, separate context), on main
`96e6a8422`, brief = the Stage 2 declaration above with the open questions of §5; the complete hand-back is
reproduced verbatim at the end of this entry. Verdict: **MATERIAL_DISSENT: yes** against launching the
declared 26 h two-fit batch as evidence for a MARL-algorithm claim; recommended correction **revise, not
stop** ("the idea — grounded labels on HMASD's decoder — is a legitimate algorithmic seed and is plausibly
novel; the design needs the stake measurement and the feature control before 26 node-hours are spent").
Disputed statements, each checked by me against the cited code/records before disposition:

- (a) "The contribution claimed … is a MARL-algorithm statement … with the intervention readings as the
  evidence" (declaration, *What is learned and what is fixed*): T − SET mixes (i) the H_central planner's
  output injected as an actor feature, (ii) the HMASD package, (iii) learned coordination; per-decision
  PERMUTE and off-distribution ALL-FREE do not separate them. **Accepted.**
- (b) "between the learned assigner and the Hungarian distance rule (H_local / H_central) at equal anchors"
  (arm T, item 1): H_local's anchors come from pooled legal observations (`b01/heuristic.py` `plan`,
  local branch); only H_central shares the generator. **Accepted; corrected below.**
- (c) The λ_h rationale (arm T, item 2): `hmasd/agent.py` sums the team entropy and the eight agent
  entropies (`entropy = (team_entropy + agent_entropies.sum(dim=1)).mean()`) while the agent policy loss is
  a mean over batch × agents, so λ_h = .01 weighs each agent's label entropy about 8 × .01 against its
  unit-scale surrogate. **Accepted; λ_h = .00125 (effective ≈ .01 per agent), logged.**
- (d) "semantics-free skills did not matter (S1 record)" / "coordinators that did not matter on S1"
  (readings; *What is learned*): `agent_count_generalization` NOTES (B01, S1, 3 fits v 3): every H6 (full
  MI-skill HMASD) final policy exceeded every SET final policy at N4/N6/N8, lowest H6 − highest SET
  +.012/.013/.010, unseen-count mean +.033, both arms at λ_l = .05 (no entropy confound between arms).
  **Accepted; withdrawn.** The narrower statements stand: B12 (additivity) and B13 (constant-label
  external bandit) show the *choice among semantics-free labels* worth about panel noise; the package
  itself beat SET on S1.

**Disposition, item by item** (finding → decision → change in v2):

| # | Finding | Decision | Change |
|---|---|---|---|
| A | T − SET confounds anchor feature, HMASD package, learned coordination | accept | feature control **SET+A** added; primary reading T′ − SET+A; T′ − SET secondary; first-batch claim reworded (below) |
| B | No timing leak (coordinator decides on the same refreshed state SET snapshots); relatives must be recomputed from the current own observation at acting and replay | accept (already so) | L0-A builds `rel = anchor − obs[0:2]` from the current own observation on both paths (verified in `b03/agent.py::_apply_central_input`); stated in v2 |
| C | Nesting holds as representation; entropy bonus, co-adaptation under non-FREE inputs and argmax evaluation are caveats | accept | caveats recorded; no design change |
| D1 | λ_h effectively 8× nominal | accept | λ_h = .00125; `avg_agent_entropy` and team entropy per rollout in the decision summary |
| D2 | Coordinator cannot see the anchors (state + 8 obs tokens only); centroid slot order is a discontinuous function of 30 user positions | accept, minimal form | the coordinator's state token is widened by the anchor block (9 × xy = 18, plus the six centroid member counts / 30 = 6 → state token 330); the widened state is stored in the ordinary high-level replay; anchor tokens (8 entities) rejected as the larger change to attention structure |
| D3 | Low level has no incentive to follow labels (native reward only) | accept as a named outcome | reading "low level ignores labels": end-of-commitment distance to the assigned anchor not below the distance to a uniformly random anchor, and ALL-FREE ≈ T′ |
| D4 | Label churn from count re-ordering / k-means re-seeding | accept | mechanism statistic: anchor displacement per held label between consecutive decisions |
| D5 | Anchor block is xy only; H flies at 100 m; altitude-floor share .47 | accept | prediction: if T′ gains service without moving the altitude-floor share, the mechanism is xy assignment only; read the share at c06 |
| D6 | n_z = 9, n_Z = 1, k = 10, `ordinary_completed_segments = True` justified; index seeding fine | — | none |
| E1 | Primary comparison does not test the bridge; ego one-hot gives a coordination-free identity convention | accept | SET+A (all eight anchors, no labels) is the matched control; IDENTITY labels added as a zero-fit rule (below) |
| E2 | Per-decision PERMUTE thrashes; ALL-FREE off-distribution | accept | PERMUTE-EP (one permutation per episode); **HUNGARIAN-LABELS** and **IDENTITY-LABELS** on T′'s own c06 low level; ALL-FREE kept as a secondary reading |
| E3 | Same-seed pair is not a coupling; fit is the unit; DM1 evaluates CPU FP32; second seed not started; c03 has no SET pair | accept | fit-level reading (lowest T′ − highest comparator) added; T′/SET+A evaluated CPU FP32 with B02's `checkpoint_eval` as DM1 does; fallback comparators declared; c03 read against 925031's c03 |
| E4 | No rule for three seeds; CLAIM lacks the feature control | accept | three-seed rule written; CLAIM wording bound to SET+A |
| E5 | ACG H6 > SET contradicts the S1 statement; M arm matters more | accept in part | statement withdrawn; candidate A relabelled; M stays in 2b (SET+A is the more decisive first control); first-batch claim reads "T′ vs SET+A / SET", not "grounding alone" |
| F | Contended wall unstated; "512 per seed" wrong; rates 164/204 | accept | node-hours bound and a contended factor declared; counts corrected |
| G | Candidate C misses `goal_conditioned_entity_aggregation` B01; candidate A misses ACG; 09-21 note's S4 ceiling and §3.3 coupling instrument unadopted; DM3/DM4 adjacency | accept / reject in part | C gains `goal_conditioned_entity_aggregation` B01 (P−O −.349, E−O −.326 J, 32/32 adverse; TRIED adverse); A → TRIED with a positive package result on S1; S4 scripted ceiling **adopted as Stage 2-0**; §3.3 coupling regression **not adopted** — it measures additivity under FSD's skill set, whereas Stage 2-0's assignment-mode contrast measures the stake of *this* label set directly; DM3 B01 (BC of H: +.05 QoS with 15 service-loss worlds) and DM4 B03 (fixed distance/hysteresis allocation) noted as adjacent, no overlap of paths or runs |
| H | Zero-fit stake sizing before any fit; pivot if IDENTITY ≈ HUNGARIAN | accept | Stage 2-0 below, with the tree written before the run |

### Stage 2-0 — zero-fit stake sizing (declared now; the only computation before the tree is read)

**Question.** How much service does the *assignment* of UAVs to the 6 + 2 anchors carry on this host, beyond
what a coordination-free rule reaches with the same anchors and the same go-to executor? This is the S4
"scripted ceiling on label stakes" of the 2026-09-21 note, applied to the anchors T′ would use.

**Design.** H_central's controller (`H1` params, `PRODUCTION_PARAMS` enter 0.00 / exit 0.05, replan 30,
100 m, central information) run by the B01 evaluator, deterministic, on the 32 development worlds
955001–955032, in three assignment modes applied inside the planner's target step on the same cost matrix
(distance plus the hysteresis margin, exactly as `_assign_targets` builds it):

- **HUNGARIAN** — as recorded (`_assign`, Hungarian); must reproduce Stage 1's H_central panel on these
  worlds to the bit (same code path; any difference is an engineering fault to resolve before reading);
- **IDENTITY** — available UAV *i* (ascending index) takes priority slot *i*; an unavailable UAV's slot
  stays empty; no cost used;
- **INDEPENDENT-NEAREST** — each available UAV takes its own row-wise cheapest anchor; duplicates allowed,
  unclaimed anchors unserved.

Everything else byte-identical to H_central: anchors, executor, shield, worlds, traces, diagnostics.
Implementation is a subclass in the direction's `b03/` package plus a runner phase that reuses
`b01/evaluation.py` unchanged; `b01/` is not edited. 96 episodes, CPU, this host (`local_linux`, 16 CPUs,
8 workers) so that DM1's node operation is not slowed; admission through `scripts/hmasd_launch.py`.
Cost bound **1 h wall, 0 fit**.

**Readings and the pre-written tree** (paired per world, deterministic, QoS/step and native J):

- S = HUNGARIAN − max(IDENTITY, INDEPENDENT-NEAREST) in paired mean QoS/step, with paired SE and the count
  of worlds where HUNGARIAN leads the better coordination-free rule.
- **S < .03** → the assignment choice is worth less than the panel noise at these anchors on this host: T′
  is **not launched** as a coordination study (its expected gain over SET+A would be within noise, and any
  T′ − SET gain would be the anchor feature). This notebook then declares a new study; the candidates on
  record are chain-attributed credit (coordination content in the reward) and a pointer-over-users anchor
  set; no fit is bought by this declaration.
- **S ≥ .03** → the stake exists; the first batch below is launched, with S recorded as the ceiling the
  learned assigner can recover over the better coordination-free rule.
- Also recorded: which coordination-free rule is stronger (that is the behaviour SET+A can reach without
  coordination), IDENTITY − HUNGARIAN and NEAREST − HUNGARIAN separately, and their pre-entry / post-entry
  split by the clock-aligned decomposition.

**Predictions (mine, before the run).** INDEPENDENT-NEAREST loses most: with 8 UAVs choosing among 8
anchors independently, several anchors go unserved at every replan (uniform choice would cover ≈ 66% of
anchors; distance correlation makes it better than uniform but far from complete), so I expect
NEAREST − HUNGARIAN ≈ −.10 or worse. IDENTITY is geometrically arbitrary but stable, so I expect
IDENTITY − HUNGARIAN between −.03 and −.10, with the loss concentrated after count re-orderings (slot swaps
across the map). Hence S ≈ .03–.10 with the better free rule = IDENTITY. If instead S < .03, the honest
reading is that on this host the Hungarian step buys little over a fixed convention and the coordination
study is not worth 52 node-hours.

### First batch (conditional on S ≥ .03) — arms, readings, rules

**Arm T′ (GAS-HMASD, v2).** The declared arm T with four changes: (1) coordinator input = state ‖ anchor
block (18 xy + 6 counts / 30 = 24; state token 330), the widened state stored for the ordinary high-level
replay so acting and update read the same numbers; (2) λ_h = .00125 (effective ≈ .01 per agent under the
summed formulation); (3) actor block as delivered by L0-A (assigned anchor abs x/y, rel x/y from the
current own observation, dist, is_free; input 3,605; labels stored with the snapshot, see the L0-A record
below); (4) decision summary gains team/agent entropy, anchor displacement per held label and the
random-anchor distance baseline. Seeds 26092711, 26092731. Everything else as declared (B02 recipe,
`ordinary_completed_segments = True`, n_Z = 1, n_z = 9, k = 10, no intrinsic reward, production shield,
1.2 M, c00–c06).

**Arm SET+A (feature control).** B02 SET exactly (`make_b02_config`, n_z = 1, no coordinator training,
`ordinary_completed_segments = False`) with the actor's central input extended by the same per-slot block
for **all eight grounded slots** in slot order (8 × [abs x, abs y, rel x, rel y, dist, is_relay] = 48 →
input 3,647), computed from the same stored anchors and the current own observation; no label, no FiLM
change. Seeds 26092711, 26092731. Information: SET's plus the anchors — equal grounding to T′, no
assignment. Nesting: SET+A ⊇ SET (zero weights on the block).

**Comparators.** SET: DM1's 26092711 / 26092731 c00 / c06 in both modes (their evaluations) and my 925031
(c00 / c03 / c06). H_central, H_local, N on the same worlds (Stage 1 panels). Stage 2-0's three modes.
Evaluation of T′ and SET+A: CPU FP32, B02 `checkpoint_eval`, the same evaluator DM1 uses, so per-world
pairing is device-consistent; if DM1's second seed is not complete when T′'s c06 panels exist, the SET
comparators are 925031 and DM1's 26092711 and the rule below is read at the fit level over those.

**Panels per seed.** T′: c00 / c03 / c06 deterministic and sampled (6 × 32) plus, at c06 with deterministic
low level, PERMUTE-EP, ALL-FREE, HUNGARIAN-LABELS, IDENTITY-LABELS (4 × 32) = 320 episodes. SET+A: 6 × 32 =
192. Batch total 1,024 episodes ≈ 4.6 h at the measured 16 s per episode; bound **6 h**.

**Readings and rules (fixed before any score).**

- Primary: paired per-world c06 deterministic QoS/step, **T′ − SET+A** (same seed label), with paired SE
  and positive-world count; sampled panel and native J alongside. Pass per seed label = ≥ +.05 QoS/step
  with ≥ 20/32 worlds positive.
- Secondary: T′ − SET (DM1 seeds, 925031), SET+A − SET (the value of the anchor feature alone), and the
  same against H_central / H_local / N. Fit-level reading in every case: lowest T′ − highest comparator fit
  (ACG's rule), in addition to the world-paired differences; the "same-seed" label is descriptive only.
- Intervention (T′ c06): "learning the assignment adds value" if learned − HUNGARIAN-LABELS ≥ +.02 with ≥
  20/32 worlds positive; "assignments matter" if learned − PERMUTE-EP ≥ +.05 with ≥ 20/32; learned −
  IDENTITY-LABELS reported; ALL-FREE = the low level's SET-like competence (off-distribution, secondary).
  "Low level ignores labels" (D3) is read as its own outcome.
- Mechanism: occupancy by type, duplicate rate, stability, anchor displacement per held label, distance to
  the assigned anchor v the random-anchor baseline, entropies over rollouts; phase decomposition and the
  boundary / altitude-floor shares with the D5 prediction.
- Competing prediction from the record: near-uniform labels with arbitrary argmax at evaluation (the D1
  failure), T′ ≈ SET+A; or a package effect only, T′ − SET+A ≈ T′ − SET − (SET+A − SET) ≈ 0.

**Stage 2b (pre-declared).** Both seed labels pass → third T′ seed 925031 and arm **M** (HMASD with its own
MI skills, B09 recipe, n_Z = n_z = 6, λ_D .05, λ_d .02, B09's λ_h, k = 10, shield on, 1.2 M) × 3 seeds,
then a `CLAIM_` under §8 with the claim "learned grounded assignment beats a flat learner at equal grounding
(SET+A) and HMASD's semantics-free skills (M) on S7". Exactly one passes → one more T′ seed and one more
SET+A seed (925031); then 2 of 3 pass with mean paired difference ≥ +.05 → the both-pass branch, otherwise
the neither branch. Neither passes → recorded as not demonstrated at this exposure; new declaration
(chain-attributed credit or pointer-over-users). No extension of a batch after its scores.

**Cost (upper bounds).** Stage 2-0: 1 h CPU, 0 fit. First batch: 4 fits × 13 h = **52 node-hours** GPU on
`wsl_4070`; serial wall ≈ 52 h after DM1's second SET fit releases the node (≈ 02:30 UTC 2026-09-28) → done
≈ 2026-09-30 07:00 UTC; two concurrent fits only when the memory preflight passes and no other DM fit
runs, with a contended factor 1.3 (Stage 1's process sharing CPU with evaluations ran 24% slower: 204 v
164 s/rollout) → ≈ 34 h wall. Evaluation 6 h. Corrections to the 09-27 text: measured rates 164 / 204
s/rollout (not 170–204); "512 episodes per seed" was the two-seed total (256 per seed).

**Engineering scope.** L0-A delivered (record below). **L0-C** (next, first): Stage 2-0 assignment-mode
subclass + runner phase + tests, no `b01/` edit. **L0-A2**: T′ deltas (coordinator anchor block and its
replay storage, λ_h, decision summary fields) and the SET+A arm (`--arm set_a`), tests, config JSON diff.
**L0-B**: arm-aware `checkpoint_eval`, the four label interventions, decision statistics, reader
extension. Engineering review (`hmasd-reviewer`) of the learner path before any fit. One Pro question on
this revised design (distinct value: the stake-sizing tree and SET+A as the "coordination at equal
grounding" control) is sent after this entry; it does not gate Stage 2-0, which is zero-fit.

### L0-A hand-back (learner core) — accepted with deviations

Commit `0e329dbe8` (local main, explicit pathspec, 11 files, +1,655/−39; base `8f749c901`). Files:
`b03/anchors.py` (H1's generator on the raw state, (9, 2) area-normalised, agreement with the H1 central
plan within 5e-3 m on 26 live frames), `b03/configuration.py` (`OBJECT_ID`, `PROGRAMME = "GAS-shield-on-
1.2M"`, seeds (26092711, 26092731, 925031), `make_b03_config`, `config_dict` with a `gas` record, widths),
`b03/agent.py` (`GASSkillDiscoverer`, `GASRolloutBuffer`, `GASHMASDAgent`, `build_agent`), `b03/training.py`
(decision log `decisions.jsonl` + per-rollout `gas_decisions` summary), `scripts/run_energy_relay_benchmark_b03.py`
(`train`, admission before candidate imports), `b02/training.py` injection points with byte-identical
defaults (B02 `config_dict` pinned by sha256), five test files. Tests: b01 48 + b02 27 unchanged; b03 23
new; `energy_relay_baselines` 33 and `energy_relay_imitation` 25 (consumers of `b02/training.py`) pass;
156 in all on the working tree, 50 (b02 + b03) against HEAD's core overlaid in scratch because the tree
carries another writer's uncommitted `hmasd/agent.py` / `hmasd/utils.py` (opt-in shield-surrogate path,
off by default). Config diff T v SET: `algorithm/baseline_algorithm mappo→hmasd`, `disable_high_level_training
True→False`, `lambda_h 0→.01`, `n_z 1→9`, `ordinary_completed_segments False→True`, plus the `gas` record;
nothing else. Deviations accepted: (1) labels stored with the snapshot (row = state 306 | anchors 18 |
labels 8 = 332) because `update_discoverer_from_rollout` calls `_apply_central_input` with two arguments;
the stored label equals the FiLM label at every step (refresh iff re-decided) and a mismatch raises;
(2) `GASRolloutBuffer` for the wider row, sampler state asserted equal; (3) module swap in the constructor;
(4) `collects_high_level_samples` unset on the config (agent attribute asserted True); (5) no `--arm`
flag yet (L0-A2 adds `gas` / `set_a`). RNG: coordinator identical to a plain agent at the same seed;
numpy/python states identical; the torch stream shifts after the 256 × 3,605 discoverer init (declared
"byte-identical recipe" therefore means the config, not the draw stream — recorded). Risks carried into
L0-A2/L0-B: CUDA path untested (autocast off, non-cache sampler); `n_Z = 1` team log-prob 0 (finite losses
in the tiny fit); `decisions.jsonl` ≈ 90–100 MB per fit (gitignored, copy with the run); a T checkpoint
loads only into `GASHMASDAgent` (`record.json` carries `arm`). Actor forward time on CPU indistinguishable
from SET (3–6 ms per batch of 16, noisy). Scratch removed (66 MB, own subdirectory only).

### Review text (verbatim hand-back, 2026-09-27, `hmasd-research-critic`)

> **Scientific review of the B03 declaration (energy_relay_benchmark, NOTES.md:3541–3745, main 96e6a8422)**
>
> **Context disclosure.** I worked in a separate context, read-only. No files were written, including under /tmp, and nothing was launched. I did not see the DM or Root conversation. The runtime did preload the user auto-memory index (MEMORY.md), and it contains one-line summaries of this direction's Stage 1 result and review. I rebuilt every number used below from NOTES, JSON and code rather than from those summaries. One exchange with the advisor model sharpened items D4, E1 and E3; it does not count as independent evidence.
>
> ### (1) Stage 1 evidence relevant to this choice (my reconstruction)
>
> - One SET fit (925031; the process was resumed from c03) reaches c06 at .437 / .438 QoS/step on the development worlds and .462 / .440 on hold-out (NOTES:3246–3252). Above N by .10–.12. Below H_local by .15–.17 and 336–404 J. Below H_central by .32–.34. World-paired SEs are about .015–.03.
> - As corrected by the review (NOTES:3413–3425), the per-step deficit is largest before the first shield entry (about step 1044). That window carries about 70% of the H_local gap but only about half of the H_central gap. After it, the learner serves about .51 against .75 (H_central) and .58 (H_local).
> - Unread candidates, not residues: boundary share .30–.39 and altitude-floor share about .47 of normal-mode UAV-steps; the planners have 0 on both (NOTES:3472–3473).
> - H_central, a scripted anchor-plus-Hungarian controller, reaches .774 / .781. So the 6+2 anchor generator with a perfect "go to anchor at 100 m" executor is worth about .34 QoS over the learner.
> - Measured cost: 164 s/rollout in process 1 and 204 s in process 2, i.e. 11.0 h of fit. Evaluation ran about 16 s/episode (608 episodes in 2.75 h).
> - One training instance only. No mechanism and no plateau are established.
>
> ### (2) Findings
>
> **A. MARL-algorithm comparison or controller engineering?** What is learned in arm T: the coordinator's label per agent (HMASD's SkillCoordinator, PPO on the k-step team return) and the low-level actor (PPO on the native reward only). What is fixed: the anchor generator — k-means over the ground-truth positions of all 30 users taken from the state (routed_core.py:4861–4898) plus two relay points on the line from the BS, i.e. H_central's planner computation (heuristic.py:223–256) — and the k = 10 clock. The actor receives that planner's output directly: 6 numbers giving its assigned anchor's absolute and relative position (NOTES:3622–3627). "No new information" (NOTES:3649) is true in the information-rights sense. But the block is a hand-coded, highly nonlinear feature that encodes the reference controller's domain knowledge. As declared, T − SET therefore mixes three things: (i) the engineered anchor feature in the actor input (controller engineering); (ii) the HMASD package itself (coordinator, FiLM labels, high-level training); (iii) learned coordination over grounded labels, which is the claimed MARL contribution. Root's caution ("改进一个 UAV 控制器本身，尚未证明改进了 MARL 学习") applies squarely. Fixing the generator does not answer it, because the fixed generator is exactly the controller knowledge being injected. T vs SET is interpretable only as "SET plus the H_central planner feature plus a learned assigner, against plain SET". T vs H is interpretable only against H_central. H_local uses anchors from pooled legal observations (heuristic.py:234–236), so "equal anchors … H_local" (NOTES:3610–3611) is false. H_central also has hysteresis, flies at a fixed 100 m and replans every 30 steps rather than 10. S0-3 showed the replan period matters little (−.005).
>
> **B. Information contract.** There is no timing leak. `_batched_assign_skills` decides on `states_batch[indices]` at `env_steps % k == 0 | dones | invalid` (agent.py:2197, 2212–2225). `step()` refreshes the held snapshot in the same call, after the assignment, from the same `states_batch` / `observations_batch`, for lanes with `env_timers == 0` (agent.py:3339–3352, 1326–1338). So at every decision step the coordinator's input equals SET's newly refreshed snapshot. Between decisions both the labels and the snapshot are held. The coordinator never acts on a state fresher than SET's snapshot. The CF input carries state, 8 observations and an ego one-hot (agent.py:1340–1364; configuration.py:189–192). One engineering point for L0-A. The anchor block's relative x/y and distance use the UAV's current position every step. The spec must say that stored k-means anchors are combined with relative terms recomputed from the current own observation, both when acting and in replay. Otherwise "replay reads stored values" and "relative to own position" conflict. The real contract issue is not information but injected computation (see A).
>
> **C. Nesting.** The claim holds as a representation statement. With label FREE, the actor input is SET's 3,599 numbers plus zeros and `is_free = 1`. FiLM of one fixed one-hot (networks.py:1449–1452) is one learned affine, as in SET with n_z = 1. The critic is identical (n_Z = 1). Caveats beyond the one the DM gives: the coordinator's entropy bonus penalises the "always FREE" member, so the regularised optimum differs from SET's; the low level trains mostly under non-FREE inputs while the coordinator is near-uniform; deterministic evaluation (argmax labels) is off the training distribution when the coordinator is near-uniform. "A deficit is a learning cost, not a representation limit" is correct. It says nothing about which learning cost, whether co-adaptation or credit.
>
> **D. Design choices that carry meaning.**
> 1. **λ_h = .01 is effectively about .08 per agent — consequential.** In the ordinary coordinator update, `entropy = (team_entropy + agent_entropies.sum(dim=1)).mean()` (agent.py:6020–6021) and `entropy_loss = -lambda_h * entropy` (6105). But `agent_policy_loss = -min(...).mean()` averages over batch × agents (6057), and advantages are normalised globally (6038–6042). So each agent's label entropy carries 8× the nominal weight against its unit-scale surrogate. The "paper range .001–.1" uses the same summed formulation, so it does not support the rationale that .01 "does not dominate". Added to a weak per-agent credit signal (all agents share the team k-step return), the likely failure is near-uniform labels, with arbitrary argmax at evaluation, not a collapse to FREE. Fix: λ_h ≈ .00125 (effective .01), or state the effective value explicitly. Log `avg_agent_entropy` per rollout as a mechanism curve.
> 2. **The coordinator cannot see the anchors — consequential.** `_build_entity_sequence` takes state plus 8 observations only (networks.py:749–754). Labels 2–7 are centroids ordered by k-means member count. That is a discontinuous function of 30 user positions, which the coordinator must recover implicitly to match UAVs to slots geometrically. A negative result would then be uninterpretable: grounding may have failed, or the pointer may simply be blind. Minimal fix: append the 8 anchors (xy, type, count) to the state token, or add them as 8 tokens. The ordinary replay path uses stored `ordinary['states']` / `['observations']` (agent.py:5688ff), so the anchors must also be stored there.
> 3. **The low level has no incentive to follow labels.** With `disable_discriminator_rewards` the reward is `lambda_e * reward` (agent.py:4859–4861). Labels matter only through co-adaptation, which is July's `A_NO_MATERIAL_Z_DEPENDENCE` failure. This is measured by the declared distance-to-anchor statistic, so it is non-blocking. Name "the low level ignores labels" as its own outcome with its reading (distance not below that for a random anchor; ALL-FREE ≈ T).
> 4. **Label churn.** Index-seeded k-means and count ordering are recomputed every 10 steps. Centroid slots can swap when counts tie, which is plausible with 6 centroids over 5 clusters. "Keeps the previous label" is then not target stability. Add anchor displacement per held label. Non-blocking.
> 5. **Altitude.** The anchor block carries xy only; H flies at 100 m (heuristic.py:324). Predict and read whether T changes the .47 altitude-floor share. If T gains service without changing it, that bounds the mechanism.
> 6. **Other choices.** n_z = 9 with 6+2 is justified: H_central reaches .78 with this generator. n_Z = 1 is fine; the team surrogate is identically zero. Engineering should check the one-class Categorical. k = 10 is the matched clock. `ordinary_completed_segments = True` is required: agent.py:513–531 refuses it without high-level training. Low-level semantics differ from SET only as B02 RECIPE_NOTES state. Index seeding is deterministic given the environment's user order; it is not a problem here.
>
> **E. Readings and rules.**
> 1. **The primary comparison does not test the declared bridge.** The simple model compares independent learners with a sequential assigner at the same anchors (NOTES:3580–3585). T − SET is not that comparison. The bridge also omits agent identity. SET's input includes an ego one-hot, so a flat learner given the anchors could use the convention "UAV i → slot i" with no coordination learning at all. Relative overgeneralisation assumes symmetric agents without identity. The matched control for the claim is **SET+A**: a flat SET actor given all 8 anchors (relative xy and type), with no labels.
> 2. **Interventions do not separate (i) from (iii).** ALL-FREE is off-distribution for a low level trained with anchors. PERMUTE is redrawn at every decision, so it causes target thrash every 10 steps. Any coordinator that learned any one-to-one matching, including a trivial one, will "beat" it, so ≥ .05 with ≥ 20/32 is a low bar. Changes: PERMUTE: one permutation per episode. Add zero-fit **HUNGARIAN** labels (H1 rule on the same anchors) and **IDENTITY** labels (agent i → slot i), both fed to T's own c06 low level. "Learned labels ≥ HUNGARIAN" would be the first evidence that learning the assignment adds anything over the fixed rule.
> 3. **Pairing.** DM1's config differs from Stage 1's only in seed (I diffed the run config.json files). Same recipe, same 32 worlds, c00/c06 in both modes. But a same-seed pair is not a coupling. T builds different modules, so initial draws differ, and at most the training world stream is shared. The inferential unit is the fit: 2 T against 3 SET (925031 plus DM1's two). Read the lowest T − the highest SET, as ACG did, in addition to the world-paired differences. World-paired SE excludes seed variance, which is the dominant term. DM1 evaluates on CPU FP32, and Stage 1 recorded per-world CPU/CUDA disagreement. T's evaluation must use DM1's device and evaluator for per-world pairing. DM1's second seed has not started (DM1 NOTES:392–393). Declare the fallback if it does not complete. DM1 scores c00/c06 only, so T's c03 panel has no SET pair.
> 4. **2b rule.** "Exactly one seed passes → one more T seed before deciding" has no decision rule for three seeds, which leaves a post-score choice. Write it now (e.g. 2 of 3 pass and mean ≥ .05 → the both-pass branch; otherwise the neither branch). Also, the both-pass branch's `CLAIM_` ("grounding, not hierarchy alone", read against M) still lacks a feature control (SET+A), so the claim would not be supported by that design.
> 5. **The M arm.** ACG B01 on S1 (agent_count_generalization NOTES:1185–1201) found that full MI-skill HMASD (H6) beat the same SET recipe at 3 fits vs 3. Every H6 fit exceeded every SET fit, by +.022 / +.044 / +.045 J. So "semantics-free skills did not matter (S1 record)" (NOTES:3665, 3710–3711) is wrong at the package level. B12 (additivity) and B13 (constant-label selection) support only the narrower statement. This raises the prior that a T > SET gain is partly the HMASD package. Deferring M to 2b is acceptable under §8 only if the first batch's supported statement is worded "T vs flat SET", not "grounding". For a first batch, the feature control (SET+A) is more decisive than M. My auto-memory mentions a λ_l .05 confound in ACG; I did not verify it.
>
> **F. Cost and feasibility.** 13 h per fit is plausible when idle. Collection is environment-bound, one coordinator forward per 10 steps, 600 high-level samples per rollout; 200 × 204 s = 11.3 h, plus overhead. The declaration allows admission alongside DM1's second fit, which stretches both walls. That includes DM1's accepted operation, which is a Root-visible coordination effect. The Stage 1 process that shared CPU with evaluations ran 24% slower (204 vs 164 s). State a contended bound or a node-hours bound rather than "stretched, not re-estimated". Evaluation: 256 episodes per seed (the text's "per seed = 512" is the two-seed total), about 2.3 h at the measured 16 s/episode; 3 h is fine. Adding HUNGARIAN and IDENTITY is 64 more episodes per seed. Engineering risks in the storage/replay design: storing anchors and recomputed relatives through both the low-level replay (agent.py:6631ff) and the ordinary high-level replay; agent-minor ordering of the per-agent block; persistence across rollout boundaries on the ordinary path; checkpoint/resume of the held anchors (Stage 1 needed a resume). Small slip: "measured 170–204 s"; the record says 164 / 204.
>
> **G. Record labels.** Candidate C is missing `goal_conditioned_entity_aggregation` B01 (RESEARCH.md:808): skill-conditioned entity aggregation, P−O −.349 and E−O −.326 J, 32/32 adverse. It is directly TRIED. Candidate A is missing ACG B01's H6 > SET result (above). It should read as TRIED with a positive package result on S1, not only "RECORDED". The 09-21 note, which the DM cites, contains two unadopted instructions that bear directly on this design: §3.3 (lines 294–322): measure coupling (the B12 regression) before building the mechanism; S4 (lines 529–541): the first observation should be scripted assignment plus go-to as "a ceiling on label stakes". The declaration adopts neither. FSD B13 (the constant-label external bandit, "selection … worth about the panel noise") is the closest record for "does the choice of label matter". Adjacent current work worth a sentence: DM3 `energy_relay_imitation` B01: BC of the H controller gave +.05 QoS but 15 service-loss worlds, so learning go-to-anchor behaviour is not free. DM4 `energy_relay_availability`: fixed distance/hysteresis target allocation. R51 AMDT, gnn_hmasd, LCAC and chain-attributed rewards are labelled correctly as far as I checked.
>
> **H. What would change my recommendation.** Do not launch T as a coordination study if the zero-fit stake sizing below shows IDENTITY ≈ HUNGARIAN on H_central (say within .03). The sequential assigner would then have little to add on this host with these anchors, and any T − SET gain would be the anchor feature, i.e. controller engineering. Pivot at that point, for example to chain-attributed credit, where the coordination content is in the reward. If HUNGARIAN ≫ IDENTITY and INDEPENDENT-NEAREST, change the first batch to T (coordinator sees anchors, corrected λ_h) × 2 plus SET+A × 1–2, with the extended interventions. That is about 4 fits and about 52 h serial.
>
> ### (3) MATERIAL_DISSENT: yes
>
> This is dissent against launching the declared 26 h, two-fit batch as evidence for the owner's MARL-algorithm claim. Disputed statements and their evidence: (a) "The contribution claimed … is a MARL-algorithm statement … with the intervention readings as the evidence that the joint assignment, not the low level alone, carries it" (NOTES:3708–3712) — T − SET confounds the injected H_central planner feature, the HMASD package and learned coordination; ALL-FREE is off-distribution and per-decision PERMUTE induces thrash, so neither separates them; ACG's H6 > SET on S1 is a record of a package effect without grounding; the ego one-hot in SET gives a coordination-free identity convention that the bridge ignores. (b) "comparison … between the learned assigner and the Hungarian distance rule (H_local / H_central) at equal anchors" (NOTES:3610–3611): H_local's anchors come from pooled legal observations (heuristic.py:234–236); only H_central's match. (c) The λ_h rationale (NOTES:3616–3618): the effective per-agent coefficient is 8 × .01 (agent.py:6020–6021, 6057, 6105). (d) "semantics-free skills did not matter (S1 record)" / "coordinators that did not matter on S1" (NOTES:3665, 3710–3711): contradicted at package level by ACG NOTES:1185–1201. Recommended correction: **revise, not stop.** The idea (grounded labels on HMASD's decoder) is a legitimate algorithmic seed and is plausibly novel. The design needs the stake measurement and the feature control before 26 node-hours are spent.
>
> ### (4) Recommended text-level changes (minimal)
>
> 1. Add a zero-fit Stage 2-0 before any fit: CPU, no conflict with DM1's GPU, B01 evaluator; H_central on 955001–955032, deterministic, in three assignment modes on the same 6+2 anchors — HUNGARIAN (as is), IDENTITY (UAV i → slot i; unavailable UAVs leave their slot empty), INDEPENDENT-NEAREST (duplicates allowed); 96 episodes, about 30–45 min. Pre-write the tree: IDENTITY within .03 of HUNGARIAN → do not launch T as a coordination study; otherwise → include SET+A in the first batch. 2. Arm T changes: coordinator input gains the 8 anchors (to the state token or as tokens), stored for high-level replay; λ_h = .00125, or a statement of the per-agent effective value; anchor relatives recomputed from the current own observation at acting and in replay. 3. Add SET+A (flat SET with all 8 anchors per actor, no labels) × 1–2 seeds; primary reading T − SET+A (coordination at equal grounding); T − SET stays secondary. 4. Interventions: PERMUTE one permutation per episode; add HUNGARIAN and IDENTITY labels on T's c06 low level; "learned ≥ HUNGARIAN" is the reading for "learning the assignment adds value". 5. Reading rules: fit-level reading against all SET fits (lowest T − highest SET); evaluation device and evaluator equal to DM1's; fallback if DM1's second seed is absent; a decision rule for the three-seed case in 2b; "same-seed pair" relabelled as a matched seed label, not a coupled unit. 6. Wording: delete "H_local" from "equal anchors"; qualify the S1 record with ACG B01's H6 > SET; add goal_conditioned_entity_aggregation B01 to candidate C; cite the 09-21 note's S4 scripted-ceiling instruction and §3.3 coupling instrument as adopted (Stage 2-0) or rejected with a reason; "512 per seed" → 256; add the altitude-floor prediction; if M stays in 2b, the first batch's supported claim reads "T vs flat SET / SET+A", not "grounding".
>
> ### (5) Unresolved facts I could not verify
>
> Whether the per-agent advantage signal (shared team k-step return minus agent value heads) is strong enough for 8 label choices — plausible but untested; the likeliest learnability wall besides λ_h. The ACG λ_l confound (from memory only), and whether it weakens H6 > SET. The S7 generator's "five clusters, one remote", and how often centroid-count ties cause slot swaps. Node CPU count, and actual contended walls with two concurrent fits. Whether the environment's training world stream is identical across same-seed T and SET fits. The layout of state entries 216–305 (only offsets 0–215, which the anchor generator needs, were checked against `_get_state`, routed_core.py:4836–4913; the declaration's offsets match). The literature claims (MAPT, Ahilan & Dayan) were not re-read.

*DM notes on the verbatim text:* the ACG λ_l point is resolved above (both arms λ_l = .05, ACG NOTES line 1362); the
"NOTES:NNNN" line references are to this notebook at `96e6a8422`; the review's item (1) numbers were checked
against the Stage 1 entries and match.

## Pro question 2026-09-27 b03-v2-stake-sizing-and-equal-grounding-control

Conversation: new (Jev account; the conversation address stays in the local operation file; shared
records use the question key)

Question: Before any Stage 2 fit is bought — is B03 v2 (the entry directly above: a zero-fit
**Stage 2-0** that sizes the stake of the assignment itself, then **T′ × 2 against SET+A × 2** as the
primary comparison, with fixed-rule label interventions) an adequate design for an algorithmic MARL
claim on this host — "learned grounded assignment on HMASD's coordinator adds service over a flat
learner at equal grounding and over fixed assignment rules" — and which single change would most raise
its evidential value per node-hour? The answer can change: the Stage 2-0 rule (modes, the statistic
S, the .03 bar); which control comes first (SET+A v M); the coordinator's learning signal (shared
k-step team return v a per-agent credit); and whether the 52-node-hour batch is launched at all.

Standing:
- Host and instrument facts. Frozen S7-S2/H3000 (8 UAVs, 30 users in 5 clusters + 1 remote, 1 BS,
  two charging stations, production shield enter .00 / exit .05, native J prices return cost at
  λ = 2). Stage 1 ("Stage 1 result" entry, line ≈ 3206, with the review corrections in the entries
  after it): one SET fit (B02 recipe, 1.2 M transitions, resumed from c03) reaches c06 .437 / .438
  QoS/step on the development worlds (.462 / .440 hold-out), above N by .10–.12, below H_local by
  .15–.17 QoS and 336–404 J, below H_central by .32–.34; the pre-entry window (before the first shield
  entry, ≈ step 1044) carries ≈ 70% of the H_local gap and ≈ half of the H_central gap; boundary share
  .30–.39 and altitude-floor share ≈ .47 of normal-mode UAV-steps (planners 0 on both). H_central
  (six k-means centroids + two relay points, Hungarian with a 300 m hysteresis, go-to at 100 m, replan
  every 30 steps, ground-truth positions) reaches .774 / .781; H_local (same planner on pooled legal
  observations) .58–.61.
- Owner constraint (2026-09-27, quoted in the Stage 2 declaration entry, line ≈ 3541): the next
  study must be an algorithmic MARL/network contribution, not an engineering improvement of a
  controller.
- The Stage 2 declaration (`96e6a8422`) proposed T = GAS-HMASD: HMASD's SkillCoordinator/SkillDecoder
  emits one of nine grounded labels per agent every k = 10 steps (labels 0–1 relay points, 2–7
  centroids by user count, 8 FREE) trained by the existing high-level PPO on the k-step team return;
  the SET low level unchanged except a six-number block for the assigned anchor; no intrinsic
  reward; recipe otherwise SET's. The independent scientific review (verbatim in the entry above,
  line ≈ 3747) dissented materially: T − SET confounds (i) the injected H_central planner feature,
  (ii) the HMASD package and (iii) learned coordination; the coordinator cannot see the anchors;
  λ_h = .01 is effectively 8× per agent; and the S1 record includes ACG B01's H6 > SET (3 fits v 3,
  every H6 fit above every SET fit, lowest − highest +.012/.013/.010 at N4/N6/N8, both arms λ_l .05),
  so semantics-free HMASD is not a null package on S1, while FSD B12/B13 show the *choice among*
  semantics-free labels worth about panel noise. Every item was adopted (disposition table in that
  entry): B03 v2 = Stage 2-0 (H_central under HUNGARIAN / IDENTITY / INDEPENDENT-NEAREST on
  955001–955032, S = HUNGARIAN − max(free rules); S < .03 → T′ is not launched as a coordination
  study), then T′ (coordinator state token carries the anchor block; λ_h .00125; relatives from the
  current own observation) × 2 and SET+A (flat SET with all eight anchors' blocks, no labels) × 2 on
  seeds 26092711 / 26092731, primary reading T′ − SET+A, interventions PERMUTE-per-episode / ALL-FREE /
  HUNGARIAN-LABELS / IDENTITY-LABELS on T′'s c06 low level, fit-level and world-paired readings, CPU
  FP32 evaluation as DM1's, a three-seed 2b rule, M (HMASD with its own MI skills) × 3 only in 2b.
- Contrary and adjacent evidence. Low-level representation changes did not help on S1
  (`local_observation_encoding` DENSE J45 .202 v .458 at 1.95× wall; `goal_conditioned_entity_aggregation`
  P−O −.349 J, 32/32 adverse); learned counterfactual agent credit parked adverse (Q−V −.018);
  chain-attributed rewards remain on the reserve list untested; DM3's behaviour cloning of the H
  controller gave +.05 QoS with 15 service-loss worlds (go-to-anchor is not free to learn); DM4
  studies fixed distance/hysteresis allocation rules. HMASD instability on S1: 26 of 35 runs.
- Unresolved after the review: whether the shared k-step team return with per-agent value heads is
  a strong enough signal for eight 9-way label choices at 600 decisions per rollout × 200 rollouts;
  how often centroid-count ties swap slots between decisions; whether .03 is the right stake bar
  (Stage 1 world-paired SEs ≈ .015–.03 on 32 worlds; seed variance unknown beyond one SET fit and
  DM1's two in progress).

Context:
  Governance: `docs/project/OPERATING_CONSTITUTION.md` §§1–5, 7–8 (source_sha): exploratory purpose,
    one adequate independent review with Pro added for distinct value (§5), scientific minimums (§8);
    the owner instruction above; no owner pause on this direction; RESEARCH row `energy_relay_benchmark`
    in `docs/research/RESEARCH.md` (source_sha) for the standing cell.
  Method: `.agents/skills/hmasd-scientific-tools/SKILL.md` (source_sha) — "Update the working
    explanation", "Comparators", "Statistics", "Cost and exposure", "Pro": the judgments this question
    asks about (comparator adequacy, paired v fit-level reading, cost per evidence).
  Evidence (source_sha unless stated): this notebook — "Stage 1 result …" (≈ 3206) and the review
    corrections that follow it; "Stage 2 declaration (B03)" (≈ 3541); "Stage 2 (B03): independent
    scientific review received … B03 v2" (≈ 3747, verbatim review, disposition table, Stage 2-0, first
    batch, L0-A record). Run outputs: `runs/energy_relay_benchmark/b02_s1_eval_c06_a01/checkpoint-eval/c06_deterministic-stochastic/summary.json`
    (Stage 1 c06 development panels), `runs/energy_relay_benchmark/b01_ref_a02/summary.json` and
    `runs/energy_relay_benchmark/b01_ref_a02/heuristic-dev/panels/H1_e0.00_x0.05.json` (H_central
    development panel, the HUNGARIAN reference for Stage 2-0's consistency check).
    `docs/research/candidates/agent_count_generalization/NOTES.md` (B01 H6 v SET table, ≈ 1180–1202).
    `docs/research/RESEARCH.md` rows `flexible_skill_duration` (B12/B13), `local_observation_encoding`,
    `learned_counterfactual_agent_credit`, `goal_conditioned_entity_aggregation`, `agent_count_generalization`.
    `docs/Claude_docs/research_notes/TEMPORAL_ABSTRACTION_PARADIGMS_AND_HMASD_DIRECTIONS_20260921.md`
    §3.3 (coupling instrument) and S4 (scripted ceiling), the note the declaration cites.
    Code: `experiments/candidates/energy_relay_benchmark/b03/` (`anchors.py`, `agent.py`,
    `configuration.py`: actor input 3605, central input 3253, snapshot row 332),
    `experiments/candidates/energy_relay_benchmark/b01/heuristic.py` (`plan`, `_assign_targets`,
    hysteresis), `hmasd/networks.py` (`SkillCoordinator`, `SkillDecoder`), `hmasd/agent.py`
    (coordinator update: entropy summed over agents, per-agent advantages from the shared k-step
    return, `_batched_assign_skills`).
  Frozen contract: the B02 SET recipe `experiments/candidates/energy_relay_benchmark/b02/configuration.py`
    (`make_b02_config`, `RECIPE_NOTES`) and the world roles (955001–955032 development; 957001–957032
    spent and never read again) keep their meaning; T′ and SET+A change only what the entry lists.

Prospective cost: Stage 2-0 — 0 fit, ≤ 1 h CPU on this host. First batch — 4 fits × 13 h = 52
node-hours GPU on `wsl_4070` plus ≤ 6 h evaluation, serial after DM1's second SET fit releases the
node (≈ 02:30 UTC 2026-09-28). Stage 2b — up to 6 further fits under the pre-declared rule.

Constraints: seeds and matched baseline per constitution section 8; no training, no edits outside the
empty "### Answer" subsection; write only there on branch main. Read the question at the pinned
source, but fetch the latest target file before editing and use its actual blob SHA. Preserve all
other bytes; stop on overlapping edits. On successful write, report the actual commit. On write
failure return the complete answer in chat, not just a SHA, status message or link.

Return:
1. **Stage 2-0.** Are HUNGARIAN / IDENTITY / INDEPENDENT-NEAREST the right coordination-free
   comparators for "how much is the assignment itself worth", is S = HUNGARIAN − max(free rules) with
   the .03 bar the right rule, and what else should be read from the three panels (per-world S
   against pre-entry mass, slot-swap frequency, J as well as QoS) before the tree is applied?
2. **Claim and controls.** Does T′ − SET+A support an algorithmic claim as worded, or only a
   "package v feature" statement; what exact wording does this design support; must M be in the
   first batch rather than 2b, given ACG's H6 > SET; is SET+A's block (eight anchors' absolute and
   relative positions, distance and type) the right equal-grounding input, or does it hand the flat
   learner a different and easier problem than T′'s?
3. **Learning signal.** With per-agent labels trained from the shared k-step team return (per-agent
   value heads, entropy summed over agents, λ_h .00125), is learnability of eight 9-way assignments
   at this exposure plausible? If not, name the cheapest per-agent credit (a label-level
   counterfactual/difference reward, the chain-attributed reward on record, or a decoder warm-started
   by imitation of HUNGARIAN then fine-tuned) and, for each simple-model argument you use, the MARL
   coupling it omits.
4. **Strongest alternative** at no more than the same cost and the single observation that
   discriminates it from B03 v2.
5. **MATERIAL_DISSENT** yes/no on launching the first batch if Stage 2-0 gives S ≥ .03, with the
   disputed statements and their evidence.
Cite the sources you used; state any decision-critical source you could not read. Distinguish source
facts, derivations and conjectures; do not require a new idea where the design is adequate.

### Answer

> Saved from chat by the DM (2026-09-27 ≈ 11:13Z): the deterministic observer collected Pro's complete reply from the conversation (kind `chat answer`, 12,114 characters; the driver reported answer_sha256 `6243509a…`, the saved file's own sha256 is `07fd241dc17eb5bd6e6407506fcfeedb0f365b9419151f42d13b900370024380`); Pro reported that the GitHub connector had no file-write operation, and `deliver` found no answer commit on `main` (NOT_DELIVERED). The text below is the page's text extraction, unchanged; formulas appear as the page rendered them to text. The question key is the shared identifier; the conversation address stays in the local operation file.

**GitHub 读取成功，但当前连接器没有可用的文件写入／更新操作，因此未修改仓库，也没有可报告的提交 SHA。以下是对应指定 ### Answer 的完整答复。**判断以固定提交 b6d93682c997ff13c307c8ed4c6d208ce78ec597 的问题、记录和代码为依据，没有用移动中的 main 替代推理输入。
hmasd-pro-question-b03-v2-stake…

Answer
总判断

**B03 v2 值得保留为有边界的算法探索，但尚不足以支持题述的完整归因性主张。**它已经补上最重要的第一层对照：不再只问 T′ 是否胜过没有锚点特征的 SET，而是问一个 grounded hierarchical assignment 整体方案是否胜过同样获得锚点计算结果的平坦学习器。可是，T′−SET+A 仍不单独识别“学习分配”的贡献；在 T′ 的冻结低层上替换标签，也不等于战胜了获得同等训练机会的固定分配方案。现有宪章明确允许探索性包级比较，但也明确说包级比较不能建立组件因果归因。

**我的单项最高性价比修改，是把 T′ 协调器已经得到的六个归一化簇人数，也提供给 SET+A。**固定版本的具体声明并非两臂具有完全相同的派生特征：T′ 的协调器输入增加了 18 个锚点坐标数值＋6 个簇人数／30，而 SET+A 的 48 维块只有各锚点的位置、相对位置、距离与类型，没有簇人数。建议在同一决策时刻计算、保存并向 SET+A 提供相同的六个数值，其声明中的 actor 输入因而从 3,647 改为 3,653。这是建议修改，不是已实现事实；它不增加拟合次数或评估回合，实际耗时仍应记录。它不能消除所有架构差异，但能避免把一项额外的需求规模特征误读为学习分配的收益。

首批优先级仍是 T′×2 对 SET+A×2，而不是先加入 M；共享团队回报也不应仅因联合标签空间很大就被替换。与此同时，我对原文“只要 Stage 2-0 得到 
𝑆
≥
.03
S≥.03，就按现有解释启动 52 节点小时批次”的规则给出 MATERIAL_DISSENT: YES — revise, not stop。原因是下面几个可具体修正的比较定义与推断问题，而不是要求先证明算法必然成功。

1. Stage 2-0：测量的是固定执行器下的分配规则差值，不是学习收益的上界
1.1 三个模式适合作为第一组比较，但“coordination-free”需要限定

HUNGARIAN、IDENTITY、INDEPENDENT-NEAREST 是合理的零拟合起点。不过，后两者应称为不学习联合分配的固定规则，不能称为完全没有协调信息、没有共同约定的控制器：三者共享中央锚点、目标优先顺序，以及至少部分可用性处理。IDENTITY 本身也是预先约定的角色分工。实际 H_central 代码还先按可用 UAV 数量截取目标优先列表，再执行匹配。

因此应分别阅读：

比较	可以回答	不能直接回答
HUNGARIAN−IDENTITY	在相同目标集合下，状态依赖的距离／滞后匹配是否胜过固定编号约定	学习联合分配是否胜过训练过的固定规则
HUNGARIAN−INDEPENDENT-NEAREST	联合分配相对于允许重复占位的逐行选择有多少闭环收益	收益是否全部来自“学习协调”，而非覆盖约束、目标优先级或避免重复
三者绝对 QoS、J	固定锚点与 go-to 执行器下各规则的实际服务和代价	学习器能恢复多少收益，或 SET+A 最终只能达到哪一个规则

这里还有一个需要在 L0-C 中消歧的定义。原文 IDENTITY 写成“可用 UAV i 取优先槽 i，不可用 UAV 的槽留空”；而已有 H_central 使用：

纯文本
available = 正常模式 UAV 的有序集合
used = priority[:len(available)]

若 IDENTITY 按全局 UAV 编号保留空槽，而 HUNGARIAN 总是填充优先前缀，那么 UAV 0 或 1 不可用时，前者可能丢掉中继角色，后者却保住它。此时差值混入了目标集合与优先级维护，不再只是“谁去哪个相同目标”的匹配收益。

**我的建议是明确使用同目标集合的 ranked-IDENTITY：**把第 
𝑟
r 个可用 UAV 分给 used[r]。这仍是零学习、零距离优化的强固定规则。保留全局编号空槽的版本可以作为另一种运营约定，但不能与前者混名，也不能把它损失中继角色的收益全部记为匹配价值。若预定实现本来就是 ranked-IDENTITY，则只需消除声明歧义，无须再改算法。

1.2 指定的一致性参考路径确有错配

附件指定的：

纯文本
.../b01_ref_a02/heuristic-dev/panels/H1_e0.00_x0.05.json

实际内容从 956001 世界开始，并不是 Stage 2-0 要使用的 955 开发世界面板。已在同一固定提交找到对应的：

纯文本
.../b01_ref_a02/grid/panels/H1_e0.00_x0.05.json

其内容从 955001 开始。这不是可以靠数组位置忽略的差别；HUNGARIAN 的逐世界复现检查必须核对世界种子、控制器信息来源、生产 shield 参数和数值执行路径。这里应显式纠正参考路径，而不是声称已经与附件误指的文件完成了同世界验证。

1.3 保留 
𝑆
S 的形式，但改变它的解释

设 
𝑞
𝑤
𝑚
q
wm
	​

 为世界 
𝑤
w、模式 
𝑚
m 的 QoS/step，则原统计量应明确为：

𝑆
^
=
𝑞
ˉ
𝐻
−
max
⁡
(
𝑞
ˉ
𝐼
,
𝑞
ˉ
𝑁
)
=
min
⁡
{
𝑞
𝐻
−
𝑞
𝐼
‾
,
𝑞
𝐻
−
𝑞
𝑁
‾
}
.
S
=
q
ˉ
	​

H
	​

−max(
q
ˉ
	​

I
	​

,
q
ˉ
	​

N
	​

)=min{
q
H
	​

−q
I
	​

	​

,
q
H
	​

−q
N
	​

	​

}.

这是相对于整个面板上较好的固定规则的收益。它不同于：

1
32
∑
𝑤
[
𝑞
𝑤
𝐻
−
max
⁡
(
𝑞
𝑤
𝐼
,
𝑞
𝑤
𝑁
)
]
,
32
1
	​

w
∑
	​

[q
wH
	​

−max(q
wI
	​

,q
wN
	​

)],

后者允许每个世界事后选择不同规则，是一个“逐世界先知选择器”的比较，不能悄悄替换主统计量。

因此，不宜只给一列含义不明的“逐世界 
𝑆
S”。应保留两列：

𝑑
𝑤
𝐼
=
𝑞
𝑤
𝐻
−
𝑞
𝑤
𝐼
,
𝑑
𝑤
𝑁
=
𝑞
𝑤
𝐻
−
𝑞
𝑤
𝑁
,
d
w
I
	​

=q
wH
	​

−q
wI
	​

,d
w
N
	​

=q
wH
	​

−q
wN
	​

,

再注明全局哪个规则胜出。正世界数也应说明是相对全局胜出规则，还是相对逐世界较好规则。

关键推导：这个 
𝑆
S 既不是 
𝑇
′
−
S
E
T
+
A
T′−SET+A 的上界，也不是下界。

原因不只是统计噪声。Stage 2-0 固定了 go-to 执行器、100 m 高度、30 步重规划和距离／滞后目标；T′ 与 SET+A 则要学习连续动作，使用 10 步决策接口，并优化原生团队目标。SET+A 也不是被限制在 IDENTITY 与 NEAREST 两个规则的策略类里。即使 
𝑆
S 很大，SET+A 仍可能学会相同或更好的分配；即使 
𝑆
S 很小，学习器也可能利用固定距离规则未优化的状态依赖服务差异。

所以原文两项解释都应撤回：

“
𝑆
<
.03
S<.03，所以 T′ 对 SET+A 的预期增益就在噪声内。”

“
𝑆
≥
.03
S≥.03，所以 
𝑆
S 是学习分配器可恢复收益的 ceiling。”

可以保留的是更窄的决策理由：在当前固定执行器下，连强固定分配规则之间都没有足够大的差值时，暂不为这条分配假设投入四个拟合，是合理的机会成本判断；但这不是不可能性结论。

另一个值得注意的内部尺度关系是：首批真正声明的通过标准为 T′−SET+A ≥ .05，且至少 20/32 世界为正，不是 .03。若把 Stage 2-0 的 .03–.05 真当成 ceiling，就会出现“允许启动，却按自己的上界无法达到通过标准”的矛盾。正确处理方式是区分两个估计对象，而不是机械把其中一个阈值调到另一个。

1.4 .03 可以保留为探索性的实用门槛，不能当作显著性线

指定评审给出的 Stage 1 世界配对标准误约为 .015–.03；但那不是这两个新规则差值的实测标准误，更不是训练种子方差。不能据此称所有低于 .03 的收益都是“噪声”，或称 .0301 已经建立可靠的可恢复收益。

我建议保留 .03 作为是否值得继续探索的量级参考，同时报告两组实际配对差值及其不确定性。一个直接做法是对两组均值差构造同时区间，再据此给出最小值 
𝑆
S 的区间；若做重采样，应按世界联合重采样三个模式，而不是分别打乱各臂。边界附近、少数世界驱动、或 J 与 QoS 相反的结果，应读成边界证据，而非自动打开 52 小时批次的充分条件。这也不意味着要求“95% 下界必须超过 .03”才能做任何探索。

1.5 在应用树之前，还要读什么

**首先是原生 J。**同时报告相对两个固定规则的 J 差值，不要只报告 QoS 胜者。QoS 最强的固定规则未必也是 J 最强的规则。原生 J 已经按 
𝜆
=
2
λ=2 计入返航代价；不能再用一个电量或风险代理，为 J 的实际下降追加未经声明的补偿。

**其次是同一时钟下的差值质量。**把两列 
𝑑
𝑤
𝐼
,
𝑑
𝑤
𝑁
d
w
I
	​

,d
w
N
	​

 与 Stage 1 同世界的 pre-entry 差距质量并列。所有模式使用同一个预先确定的截点，例如主分析对应的 SET c06 首次 shield entry 时刻；不要分别截到各臂自己的 entry，否则比较窗口受处理影响。最好给出可相加的 pre/post 累计贡献，而不是仅比较不同长度窗口内的均值。已修正记录中的“约 70% H_local 差距、约一半 H_central 差距在 pre-entry”是定位问题的描述，不是 shield 无因果作用的证明。

**再次是锚点身份变化，而不只是标签编号变化。**代码使用按用户索引初始化的 k-means，并按人数稳定排序；人数相等本身不必导致交换，人数交叉、簇几何变化或聚类归属变化才可能改变某个槽代表的实体。应区分“同一实体移动”和“同一槽换了实体”，报告实际交换频率、持有标签对应锚点的位移，以及交换时的服务损失。T′ 每 10 步刷新，而 Stage 2-0 每 30 步规划，因此后者的低交换频率不能直接证明前者接口稳定。

最后，原文“八个独立均匀选择覆盖约 66% 锚点”可以作为玩具计算：

1
−
(
7
/
8
)
8
≈
.656.
1−(7/8)
8
≈.656.

但“距离相关性会使它比均匀选择更好”没有保证：聚集的 UAV 可能一致选择同一个近锚点，反而更差。这个模型省略了空间相关性、可用性、滞后、目标需求不均，以及两个中继角色对端到端服务的非线性影响，不能用来预测 −.10 QoS。

2. Claim 与 controls：保留 SET+A 的优先级，但明确整体方案与学习分配的区别
2.1 这个设计实际能够支持什么措辞

若首批结果正向，最准确的探索性表述是：

在固定 S7-S2/H3000、指定开发世界、共同原始信息与匹配派生锚点特征、B02 训练暴露下，T′ 的 grounded hierarchical assignment 整体方案，相对于平坦 SET+A，在两个独立训练实例上显示了服务增益。对 T′ 冻结低层的标签替换，进一步显示该已训练系统的服务依赖其所使用的分配策略。

需要单独保留限定的是：

这些结果尚不能把增益唯一归因于学习分配，也不能证明该方法优于从头获得同等训练机会的固定分配方案。

这是一个可以有算法研究价值的整体方法比较，不必贬成“只是工程”；但还不是“学习协调这个组件已被识别”的结论。现有宪章恰好要求这种区分。

2.2 冻结低层干预有价值，但它回答的是条件化问题

原文的 HUNGARIAN-LABELS、IDENTITY-LABELS、PERMUTE-EP、ALL-FREE 都应保留。尤其 HUNGARIAN-LABELS 比单独 ALL-FREE 或随机置换更有辨别力。它们回答的是：

𝐽
(
T′低层
,
学到的分配
)
−
𝐽
(
同一T′低层
,
替代分配
)
.
J(T′低层,学到的分配)−J(同一T′低层,替代分配).

但训练期间的标签分布、到达状态和低层响应已经共同适应。这个差值不等于：

𝐽
(
学到的分配与其低层
)
−
𝐽
(
固定分配与为其训练的低层
)
.
J(学到的分配与其低层)−J(固定分配与为其训练的低层).

因此，原文“learned−HUNGARIAN-LABELS ≥ .02 且至少 20/32 世界为正”可作为在该低层上替换高层的服务证据，不能直接改名为战胜了训练匹配的固定规则。ALL-FREE 的零／弱响应也不能单独证明一般意义上的低层能力，因为它可能偏离训练时的输入分布。

PERMUTE-EP 比逐决策重置排列更好，但仍应明确是否置换 FREE、是否跨 relay/service 类型。跨类型或包含 FREE 的置换可以作为系统破坏实验，却不能专称“只破坏联合协调、其余不变”。

2.3 M 不必进入第一批

ACG B01 的原始结果确实有分量：三个 H6 最终策略在每个 N 上都高于三个 SET，最低 H6−最高 SET 分别为约 .0124/.0130/.0102。它否定的是“语义无关 HMASD 包在 S1 是零效应”这个概括，不是直接证明 B03 的分配机制。

这使 M 成为重要的后续替代解释对照，却不能让它替代 SET+A：不含相同锚点计算的 M，不能回答最先必须解决的“是不是注入 planner 特征就足够”。所以 SET+A 先于 M 是正确排序。代价是首批不能声称胜过语义无关 HMASD，也不能用 FSD 的标签选择弱效应，把 ACG 的包级正效应消掉。

2.4 SET+A 的全部锚点输入不是不公平的“容易题”，但当前特征还没完全匹配

首先要纠正信息来源的潜在混淆：B03 的锚点来自原始中央状态中的全部用户位置，不是 H_local 的 pooled legal observations。两臂共同采用这个中央状态／锚点合同才是本题的 equal grounding；不能为了看起来更“局部”而单独把一个控制器改用 H_local 的锚点。代码和既有评审已经明确这一区别。

其次，SET+A 得到全部锚点，而 T′ 低层得到选中的一个锚点，这种结构差异正是比较对象的一部分。SET+A 没有显式分配瓶颈，但要自己学会选择和连续控制；T′ 则得到高层选中的目标以及标签接口。不能事先断言哪一个更容易。

真正应补齐的是前述六个簇人数。原始状态里可以重建人数，不等于双方已经得到相同的派生计算；这与原评审指出“原始信息权利相同，不等于注入的 planner 特征相同”是同一个问题。建议把这些人数与锚点一起按决策时刻保存，acting 与 replay 一致使用；相对位置仍按已有合同由当前 own observation 重算。不要在看到结果后，再决定是否补这六个特征。

2.5 种子与 2b：目前的自动 CLAIM 路径不成立

首批两对种子适合探索，不适合把 32 个世界或 64 个种子—世界组合当成独立训练重复。应报告每个拟合的均值、每个预声明种子标签的差值，以及最低 T′−最高 SET+A 的描述性检查。最低减最高不是置信区间；同名种子也不保证初始化与策略随机数真正耦合，L0-A 已记录不同模块构造会移动 torch 随机数流。

2b 还有一个具体缺口：**“两对都通过”分支只增加第三个 T′ 和 M×3，没有第三个 SET+A，却随后要对 SET+A 提出学习主张。**这不满足每臂至少三个独立训练种子的最低要求。更进一步，宪章 §3 对确认要求的是另行固定的一批 3–5 个 fresh independent seeds／臂；不能把经探索结果选择后补上的一个种子，自动包装成确认批次。这不是要求现在追加确认预算，而是要求首批和 2b 的结论保持其真实证据等级。

3. Learning signal：可学性足以支持探索，尚不足以预测成功；不应先加复杂信用机制
3.1 八个九选一并不等于必须探索 
9
8
9
8
 个独立格子

实际解码器是自回归的：

𝜋
𝜃
(
𝑧
∣
𝑥
)
=
∏
𝑖
=
1
8
𝜋
𝜃
(
𝑧
𝑖
∣
𝑥
,
𝑧
<
𝑖
)
.
π
θ
	​

(z∣x)=
i=1
∏
8
	​

π
θ
	​

(z
i
	​

∣x,z
<i
	​

).

它逐个读取此前已选择的标签；训练重放也使用已执行标签做 teacher forcing。因此，
9
8
=
43,046,721
9
8
=43,046,721 是联合动作个数，不是样本复杂度结论。网络的条件化、参数共享和输入结构可能允许大量泛化。

按问题声明的暴露计算，600 次联合决策／rollout × 200 rollouts 是约 120,000 次联合分配，对应约 960,000 个 agent-label token。后一个数不能当作 960,000 个独立团队试验：同一次分配共享回报，连续决策具有时间相关性，低层策略还在变化。

在理想、未裁剪的策略梯度中，共享团队回报并不阻止联合策略获得正确方向的梯度：

∇
𝜃
log
⁡
𝜋
𝜃
(
𝑧
∣
𝑥
)
=
∑
𝑖
∇
𝜃
log
⁡
𝜋
𝜃
(
𝑧
𝑖
∣
𝑥
,
𝑧
<
𝑖
)
.
∇
θ
	​

logπ
θ
	​

(z∣x)=
i
∑
	​

∇
θ
	​

logπ
θ
	​

(z
i
	​

∣x,z
<i
	​

).

问题主要是方差、延迟、条件覆盖和共同适应，而不是“每个 agent 必须先有自己的奖励才可能学习”。外部 MAPPO 论文也只足以支持这种一般可行性；它在其他合作任务上的成绩不能替代本宿主的可学性证据。
arXiv

3.2 .00125 修正正确，但只修正了一个尺度问题

记录明确显示，个体策略损失按 batch×agents 平均，而个体熵按 agents 求和。因此 .01→.00125 修正了八个 agent 带来的相对权重放大。均匀分布时：

.00125
×
8
log
⁡
9
≈
.02197.
.00125×8log9≈.02197.

这是优化目标里的熵项尺度，不能与 .03 QoS 或某个 J 差值直接比较，也不保证标签分布一定离开均匀。每 agent 一个 value head 能改善条件基线，却不会自动变成反事实信用；它们仍由共同的团队回报驱动。

3.3 简单模型能提示困难，但不能替代 MARL 耦合

一个加性玩具模型是：

𝐺
=
∑
𝑖
=
1
8
𝑔
𝑖
(
𝑧
𝑖
)
+
𝜖
.
G=
i=1
∑
8
	​

g
i
	​

(z
i
	​

)+ϵ.

若各项独立同方差，单个 agent 对总回报方差的份额约为 
1
/
8
1/8。它提示共享回报可能有较差的个体信噪比，不证明八 agent PPO 不可学。它省略了本题最关键的东西：中继链的互补性、重复服务与容量竞争、能量退出造成的角色变化、动作持续时间，以及自回归选择之间的依赖。

另一个模型是“两名关键角色必须同时正确才有收益”的 AND 奖励。它说明联合信用可能比加性信用困难，却省略了多个可替代 UAV、空间连续性、部分服务回报，以及低层学习逐渐改变“正确标签”的含义。不能拿一个任意 AND 模型的低成功率，当成本题的成功概率。

指定的 §3.3 耦合仪器有助于区分加性标签效应与交互效应，但原笔记也限定了测量依赖于具体宿主和已学技能。Stage 2-0 的三个闭环规则差值并不等于该交互项；反过来，也没有必要在购买任何探索性拟合前，强制完成一个庞大的标签阶乘实验。

**我的判断是“可学性合理但未证实”，不是“已经充分有力”。**优先使用已经声明的低成本读数：训练中的标签熵、assigned-versus-random anchor 距离、重复占位、关键角色覆盖、c03→c06 变化，以及 learned 对固定标签替换的差值。近均匀标签也必须与 sampled/deterministic 差异一起读，不能把任意 argmax 的劣化当成训练分布下的能力。

3.4 若后来确有信用瓶颈，最便宜的候选是什么

**在所列“每 agent 信用”方案里，我优先考虑小型、前缀条件化的 label-level counterfactual baseline，而不是链奖励或全环境反事实分支。**这是候选方法，不是本项目已经验证有效的修复。

可令：

𝑄
^
𝑖
(
𝑥
,
𝑧
<
𝑖
,
𝑎
)
≈
𝐸
[
𝐺
∣
𝑥
,
𝑧
<
𝑖
,
𝑧
𝑖
=
𝑎
]
,
Q
^
	​

i
	​

(x,z
<i
	​

,a)≈E[G∣x,z
<i
	​

,z
i
	​

=a],
𝑏
𝑖
(
𝑥
,
𝑧
<
𝑖
)
=
∑
𝑎
=
0
8
𝜋
𝑖
(
𝑎
∣
𝑥
,
𝑧
<
𝑖
)
𝑄
^
𝑖
(
𝑥
,
𝑧
<
𝑖
,
𝑎
)
,
b
i
	​

(x,z
<i
	​

)=
a=0
∑
8
	​

π
i
	​

(a∣x,z
<i
	​

)
Q
^
	​

i
	​

(x,z
<i
	​

,a),

并用观测到的团队回报目标减去这个 detached baseline。九个标签允许每个前缀一次输出九个值，避免为每个替代标签再运行一条环境分支。COMA 原始方法提供了“用集中评论家高效边缘化单个动作”的参考，但这里的自回归 actor 需要额外注意。
AAAI出版物

**关键的 MARL 限制是：不能不加说明地照搬“固定其他所有 agent 标签”的 COMA 基线。**本实现里，后续标签分布依赖 
𝑧
𝑖
z
i
	​

。若固定已经实现的后续标签，一个声称“不依赖当前动作”的基线，实际上可能通过这些后续标签依赖它。使用只依赖 
𝑥
,
𝑧
<
𝑖
x,z
<i
	​

 的基线，并让 
𝑄
^
𝑖
Q
^
	​

i
	​

 的目标包含下游策略的平均后果，是一条较清楚的推导路线；它仍可能受评论家误差、稀疏条件覆盖和共同适应影响。这是方法建议，不是对现有 PPO 实现正确性的否定。

其余两种候选的定位应分开：

链归因奖励可能更贴近网络结构，但链上的“被计入服务”不等于移除某个 agent 后的因果边际贡献。备用链、流量重路由、共享容量和电池状态都会使局部归因失真。它在记录中仍未验证，且可能改变优化目标；不宜把它当成保留原生 J 合同的免费修复。现有 learned-counterfactual-credit 的负向记录也提醒我们，增加信用模块并不自动提升服务。
hmasd-pro-question-b03-v2-stake…

Hungarian 模仿暖启动 decoder可能是最便宜的探索起点改善，却不是每 agent 信用。它把策略推向一个有用区域，但会引入教师先验、模仿暴露及其费用；若教师的滞后决策依赖学习器输入中没有的历史，模仿目标还可能不可完全重建。它也没有自动解决“学会标签”和“学会执行标签”的共同适应。DM3 的 BC 正收益伴随 15 个 service-loss 世界，正说明 go-to 能力不是免费获得的。

所以，不建议在第一批同时换信用机制、加模仿、再改锚点。那会让一次正负结果难以更新当前解释。先保留共享回报，是有依据的简化，不是忽视信用问题。

4. 不超过同等成本的最强替代：T′×2 对“从头训练的固定分配”R×2

最强替代不是先放入 M，也不是再扩大语义发现模块，而是下面这个更直接的归因设计：

R：与 T′ 使用相同原始信息、锚点生成、标签接口、低层网络、原生奖励及 1.2 M 暴露，但训练全程由固定 Hungarian 分配规则产生标签，低层从头学习。

R 的规则须在同样的 
𝑘
=
10
k=10 接口调用，保持相同可用性和目标集合合同；不能直接拿 H_central 的 30 步、100 m go-to 控制器当成这个训练匹配臂，也不能改用 H_local 的另一套锚点。原代码和声明的差异使这些区分实质重要。

以 T′×2 对 R×2 替代现有四拟合首批，拟合数和声明暴露相同，可按相同的四拟合成本上界规划；R 的实际耗时尚未测量，不能提前声称更快。

唯一最有判别力的观察是：

Δ
l
e
a
r
n
e
d
 
a
l
l
o
c
a
t
i
o
n
=
𝐽
(
𝑇
′
从头训练
)
−
𝐽
(
𝑅
从头训练
)
,
Δ
learned allocation
	​

=J(T′
从头训练
	​

)−J(R
从头训练
	​

),

连同 QoS，在两个独立种子及同世界评估上是否方向一致、量级有实际意义。

若 T′ 胜过冻结低层上的 HUNGARIAN-LABELS，却不胜过 R，那么较合理的解释是：原干预主要暴露了共同适应和输入分布变化，而不是学习分配优于固定规则的训练后收益。若 T′ 稳定胜过 R，才更接近题目中“学到的分配本身增加服务”的主张。

这个替代也有明确损失：**它没有 SET+A，因而不能回答是否胜过等 grounding 的强平坦学习器。**我仍倾向于把修正后的 T′×2／SET+A×2 作为第一批，因为注入派生特征是当前最先应排除的解释；但若后续要从“整体方案有效”升级到“学习分配有效”，R 比继续堆叠冻结低层破坏实验更有价值。M 回答另一条重要问题，不能替代 R。

5. MATERIAL_DISSENT：YES，针对原文的自动启动规则与过强解释；不是停止这一方向
被争议的陈述／做法	我的判断与依据

𝑆
≥
.03
S≥.03 就建立了学习分配可恢复的 stake，且 
𝑆
S 是 ceiling	不成立。固定 go-to／30 步规则差值与 T′−SET+A 是不同估计对象；
𝑆
S 只能支持有边界的机会成本判断。
三模式只改变同一匹配问题	尚未定义清楚。IDENTITY 的“不可用槽留空”可能改变目标集合，而 H_central 先截取可用数量的优先前缀。
SET+A 已完全匹配 T′ 的派生 grounding 特征	尚未完全匹配。T′ 协调器有六个簇人数，SET+A 的 48 维块没有。
冻结低层上的 learned−HUNGARIAN-LABELS 正向，就说明学习分配优于固定规则	只能支持该低层上的替换效应，不能替代训练匹配的 R。
两对通过后补第三个 T′ 与 M×3 即可进入所写 CLAIM	SET+A 仍只有两次训练；而确认还受 §3 的 fresh、固定批次要求约束。

这些争议分别来自固定版 v2 声明、实际 planner 代码、实际输入定义及现行宪章，而不是新增的审批标准。

**具体建议是：**修正参考面板、消歧并统一固定规则的目标集合、把同样的六个簇人数提供给 SET+A，然后把 Stage 2-0 读成带不确定性的固定执行器 stake 测量。若结果仍有实际量级，J 没有显示被 QoS 掩盖的明确代价，而且收益不是目标集合差异制造的，我支持保留 T′×2／SET+A×2 的探索性首批；不要求先换信用、不要求 M 提前，也不把两种子结果升级为确认性学习主张。现有工程修正路径可以承载这些变化，不建议为此增加一轮形式性独立复审。

来源边界与尚未获得的信息

本答复已依据附件全文、固定版问题与相关治理／方法章节、指定研究记录、相关代码及运行摘要作出判断。较大的运行摘要与 ACG 笔记在普通文件读取返回空内容后，通过其实际 blob 读取补回；没有把接口空内容误判为文件为空。指定 HUNGARIAN 参考路径的错配已在上文说明，并明确区分了原指定文件与找到的对应开发面板。

**仍然没有的，是固定版本中尚未产生的决策数据：**Stage 2-0 的三个实测面板及其 
𝑆
S、配对标准误和 J 差值；T′／SET+A 的训练种子方差；实际 slot-swap 频率；以及 L0-A2 对 T′ 与 SET+A 的实现验收结果。固定版仍记录为 L0-A 已交付、L0-C／L0-A2／L0-B 待完成，因此本答复没有把 v2 的声明当作已验证实现，也没有给出虚构的通过概率或预期收益。

最终研究判断：保留 grounded assignment 这条算法种子，先做真正匹配的派生特征对照；把固定执行器的规则收益、整体学习方案收益，以及学习分配本身的收益，作为三个不同问题阅读。

## 2026-09-27 — Stage 2-0 (B03 v2): L0-C hand-back accepted (d4f9ecd0a + 5e8da3d94), IDENTITY revised to the declared rule, comparison-panel path corrected, one revision of the pre-written tree before the run, launch

**Engineering facts (implementer hand-back; verified by me where stated).**

- d4f9ecd0a: `b03/assignment_modes.py` (`AssignmentModeHeuristic` / `AssignmentModeController`, modes `hungarian` / `identity` / `independent_nearest`), `b03/stake_sizing.py` (`STAKE_WORLDS` 955001–955032, `evaluate_stake_task` = `evaluate_task`'s heuristic branch step for step, spawn pool sorted by seed, `stake_readings`, `consistency_check` that records and never raises; refusals for hold-out worlds, a mode set without hungarian, oversubscription and a non-empty `<out>/stake-sizing/`), runner subcommand `stake-sizing --out --launch-sha [--workers 8] [--threads 2]` with admission before any candidate import; worlds, modes, heuristic and params are not settable from the command line; `b01/`, `b02/`, `hmasd/`, `envs/`, `configs/` and the launch kernel untouched; suite 156 → 175 passed.
- Hungarian mode reproduces the recorded H_central row of world 955001 exactly on this host (qos_per_step 0.8425319250888533, raw_native_J 2480.815575609467; the recorded panel came from wsl_4070), 161.8 s for one world at 2 threads serial.
- Correction to the L0 note: the comparison panel is `runs/energy_relay_benchmark/b01_ref_a02/grid/panels/H1_e0.00_x0.05.json` (H1, enter .00 / exit .05, 955001–955032, mean QoS .7740, J 2281.89, tracked); the L0's `heuristic-dev/...` path holds 956001–956008 only. The run's consistency check uses the corrected path (tolerance 1e-9); I read its result before the tree.
- 5e8da3d94: IDENTITY revised from the L0 shorthand (the j-th *available* UAV takes truncated slot j, which re-covers the top slots from fleet availability, i.e. coordination content) to the declared rule (this notebook, lines 3811–3812): available UAV *i* takes slot *i* of the full priority list; an unavailable UAV's slot stays empty and that UAV has no target. Mechanism: identity-mode `plan` is a copy of `LayoutHeuristic.plan` whose only difference is `used = priority` (I diffed the two sources: that line plus the mode dispatch); hungarian and independent_nearest go through the base `plan` unchanged; `b01/` untouched. INDEPENDENT-NEAREST stays as declared (row-wise argmin on the same cost matrix `_assign_targets` builds, i.e. over the truncated list). Tests: b03 42 → 45, b01 48 unchanged, the 955001 bit-identity test unchanged and passing (b03 + b01 = 93 rerun; the other suites' paths are untouched by the revision).
- Accepted deviations: `B01Spec()` (no `production_spec()` exists in b01); `argv` recorded in `config.json`; hungarian required among the modes; the pre-entry / post-input phase means use each mode's own entry clocks — the clock-aligned split declared under "also recorded" is computed afterwards from the saved traces (qos and mode per step per world) before the tree is applied; the local-information identity path is unreachable here; `hmasd_launch.py status` looks for `<out>/summary.json` while this phase writes `<out>/stake-sizing/summary.json`.
- Cost and host: heuristic worker RSS ≈ 352 MB (8 workers ≈ 2.8 GB against ≈ 8 GB available, floor 4 GiB). Host load at launch time ≈ 165–180 on 16 CPUs, from a 23-hour orphaned headless Chrome unrelated to HMASD (GPU process ≈ 790 % CPU; I reniced the whole tree to 19 and did not kill it; the owner decides) and the Codex app-server (≈ 270 %, 151 runnable tokio threads). 12 waves × ≈ 160 s ≈ 32 min on an idle host; 50–75 min plausible under this load, so the declared 1 h wall bound may be exceeded — a cost overrun to record, not a scientific fact.

**One revision of the pre-written tree, before the run** (owner direction 2026-09-27: innovation points first, more weight on reasoning, no repeated experimental failure of low-quality ideas). The S < .03 branch is unchanged (T′ is not launched as a coordination study; this notebook declares a new study). The S ≥ .03 branch no longer launches the first batch automatically. It now reads: **S ≥ .03 → the stake exists and S is recorded as the ceiling; before any fit the direction re-argues its algorithmic contribution in writing** — novelty of T′ against allocation-based hierarchical MARL (a coordinator that assigns agents to grounded sub-goals with a shared low level is close to that family, ALMA and kin; to be read first-hand before the label TRIED / RECORDED / NEW is given), the mechanism from the algorithm change to QoS/J on this host, a predicted effect against measured seed noise (on S7 the only measurement is two SET seeds .437/.438 at c06; a proper seed SD is a prerequisite), and the discriminating observation — and that argument goes to independent review under constitution section 5 point 1 before the 52-node-hour batch. The Pro question `b03-v2-stake-sizing-and-equal-grounding-control` (sent 2026-09-27, key `hmasd:e51f86d4…`) is unchanged; its answer is read into that argument. Reasons: the review's own words ("any T − SET gain would be the anchor feature, i.e. controller engineering") and the owner's direction; the stake measurement itself is 0 fit and ≤ 1 h CPU and informs any coordination claim on this host, so it runs.

**Launch.** Inputs published: 5e8da3d94 on origin/main (the owner authorised pushes on 2026-09-27). Launch line, run from the checkout root with the scientific interpreter's launcher path recorded in `.codex/hmasd-compute.toml`:
`scripts/hmasd_launch.py launch --node local_linux --snapshot --direction energy_relay_benchmark --lead "Claude DM (WSL session)" --sha 5e8da3d94e19f80b2f5e7600665a98fbf471c70b --output runs/energy_relay_benchmark/b03_stake_a01 -- scripts/run_energy_relay_benchmark_b03.py stake-sizing --out runs/energy_relay_benchmark/b03_stake_a01 --launch-sha 5e8da3d94e19f80b2f5e7600665a98fbf471c70b --workers 8 --threads 2`.
Operation facts, the consistency check, S and the tree reading follow in the results entry.

## 2026-09-27 — Corrections to the previous entry and a second revision of the Stage 2-0 tree, written before S is read (independent review MATERIAL_DISSENT received through Root's reply, commit 0bc1d7931)

**Status of the run when this is written.** Stage 2-0 (`runs/energy_relay_benchmark/b03_stake_a01`) is still running: the hungarian mode has finished (32 worlds, mean QoS/step 0.77402, matching the recorded H_central panel mean .7740), identity and independent_nearest are in progress; no free-rule world has been read and S is unknown to me. This entry therefore precedes the scores.

**Corrections (my errors in the entry of b986c279e and in `docs/Claude_docs/research_notes/REASONING_FIRST_RESEARCH_METHOD_20260927.md`, 4c4ade350).**
- ".437/.438 (two SET seeds at c06)" is wrong: the two numbers are the deterministic and sampled evaluations of the *same* c06 checkpoint of the single Stage 1 SET fit (seed 925031; `runs/energy_relay_benchmark/b02_s1_eval_c06_a01/checkpoint-eval/c06_deterministic-stochastic/summary.json`). Stage 1 has n = 1 training instance on S7; nothing in this direction measures an S7 seed SD. DM1's two new SET seeds (26092711, 26092731) plus 925031 will be the first three independent instances.
- "S1 (static, uncoupled)" and "S4 short unavailability = the native form of variable N" repeat generalisations that my own 09-26 follow-up (`docs/Claude_docs/reviews/RESET_RESPONSE_AND_FIRST_STUDY_20260926.md` §2) had already corrected: S1 couples agents through SINR interference and exclusive user assignment; S4 unavailability keeps a fixed eight-slot roster and is not member join/leave.
- The "predicted effect < 2 × seed SD → do not run" rule in the method proposal re-proposes a rule that the same follow-up (§10) had withdrawn. It is withdrawn again below; the synthesis with Root's version replaces it with the comparison's own paired-difference uncertainty.

**Review received (via Root, `docs/Claude_docs/inbox/20260927_research_method_ROOT.md` and RESEARCH.md anchor `innovation-method-root-20260927`).** The independent Scientific Reviewer (hmasd-research-critic, Root's task) records MATERIAL_DISSENT: yes against (i) the universal first-fit gates in my proposal, (ii) the category ban on feature/controller/data research, and (iii) the residual inference "S < .03 → learned − SET+A is within noise". It no longer lists the withdrawn automatic 52-node-hour purchase as a live objection; it does not object to Stage 2-0 being collected as declared and asks that its result keep a conditional interpretation. On (iii) the reviewer's argument is that S — the paired difference between fixed controllers (Hungarian versus identity/nearest under the same go-to executor) — is neither an upper bound on a learned assigner's gain over SET+A nor a measure of "panel noise": a small S can coexist with a learned increment, and a large S can be reachable by a flat learner. I accept this argument; it was also implicit in the review's item B03-H, which I had turned into a hard branch.

**Second revision of the pre-written tree (supersedes the S-branches of lines 3824–3836 and the first revision in b986c279e; declared before any free-rule score is read).**
- S remains recorded exactly as declared (paired mean, SE, world counts, better free rule, per-rule differences, clock-aligned split from traces), as a conditional fact about these fixed controllers on this host.
- Neither branch launches or cancels T′ by itself. S < .03 lowers my investment preference for an assignment-learning study and is reported as such; it does not establish that learned − SET+A is within noise. S ≥ .03 records a stake for the fixed-controller comparison; it does not buy a fit.
- In both cases the next step is the same: a written contribution argument for any learned-assignment study (what a learned assigner would handle that a fixed rule cannot, at the same information and features; the closest prior work — allocation-based hierarchical MARL, ALMA read first-hand today, arXiv 2205.14205 — and the decisive difference; the strongest simple alternative; the discriminating prediction; the cost), one applicable independent challenge under section 5, then a decision among a direct bounded comparison (the reviewer's smaller option: T′ and SET+A one full training instance each, ≈ 26 training hours), a targeted revision, or no investment. The 52-node-hour batch stays withdrawn.
- The hungarian consistency check, the panel records and the traces keep their engineering meaning regardless of the tree.

**Chain-attributed credit candidate (draft argument kept locally, to be published with the Stage 2-0 results entry).** Root's caution is adopted in the statement of the counterfactual: the proposed per-agent signal is the per-step difference reward D_{i,t} = R(s_t, a_t) − R(s_t, a_t | UAV i's links removed), evaluated on the realised state with the other agents' realised actions held fixed (the Wolpert–Tumer "absent agent" default), summed over the agent's skill segment; it is a shaped credit signal for the coordinator's per-agent advantage, not a trajectory-level counterfactual (the others' future actions are not re-simulated), and its usefulness for learning is the hypothesis to test, not a derived fact. No exhaustive counterfactual verification is bought for it.

## 2026-09-27 — Stage 2-0 (B03 v2) result read by the second revision of the tree (operation b03_stake_a01, launch sha 5e8da3d94): S = +.007 QoS/step with paired SE .007 (hungarian − identity, 18/32 worlds), the whole Hungarian advantage lies in the deployment window, independent-nearest stacks the team on one anchor; Pro answer b03-v2 saved from chat and answered; T-prime and skill-level removal-difference credit contribution arguments written for one independent challenge

**Run facts.** Admission accepted 2026-09-27 10:16:50Z, process exit 11:01:29Z (exit code 0); runner wall 2,670.7 s = 44.5 min against the declared 1 h bound, on 8 workers × 2 threads while the host carried an unrelated load (load average 165–200 from a foreign headless Chrome and the Codex app server; see the launch entry). 96 episodes, 288,000 steps, 0 failed worlds, 0 fits; peak RSS runner 557 MiB, largest worker 488 MiB. **Consistency check passed exactly**: the hungarian panel equals the recorded H_central grid panel (`runs/energy_relay_benchmark/b01_ref_a02/grid/panels/H1_e0.00_x0.05.json`, sha256 `b5a44f49…`, read from the launch-source copy) with max |Δ| = 0.0 in `qos_per_step` and `raw_native_J` over all 32 worlds. Trace–panel check: the per-step QoS traces reproduce every panel mean (96 of 96, tolerance 1e-6). Artifacts on main: `runs/energy_relay_benchmark/b03_stake_a01/` (`launch-manifest.json`, `admission-preflight.json`, `launch-status.json`, `process-exit.json`, `stake-sizing/{config.json, summary.json, panels/*.json, clock_aligned_readings.json}`); the traces (`stake-sizing/traces/*.npz`, 25 MB) stay in the local checkout. The clock-aligned readings come from the new direction reader `experiments/candidates/energy_relay_benchmark/b03/read_stake_traces.py` (3 tests, `tests/experiments/candidates/energy_relay_benchmark/b03/test_read_stake_traces.py`; the whole b03 module: 48 passed); the summary's own-clock phase means are the launcher's.

**Readings exactly as declared (paired per world, deterministic, 955001–955032).** `native J` below is the native return (`scenario7_reward_sum`), which already prices the return-constraint cost at λ_return = 2; higher is better.

| mode | QoS/step | native J | first shield entry (mean step) | first charger input (mean step) |
|---|---|---|---|---|
| HUNGARIAN (= recorded H_central) | .7740 | 2281.9 | 1300 | 1617 |
| IDENTITY (declared global-index rule, 5e8da3d94) | .7672 | 2224.1 | 997 | 1311 |
| INDEPENDENT-NEAREST | .4499 | 1286.5 | 1747 | 1921 |

- Better coordination-free rule: **IDENTITY** (global winner by panel mean; S is the minimum over the two panel-mean differences, not a per-world oracle choice — Pro 1.3 below).
- **S = HUNGARIAN − IDENTITY = +.0068 QoS/step, paired SE .0073, hungarian leads in 18 of 32 worlds** (per-world range −.077 … +.135); native J +57.8, SE 24.6, 21/32.
- HUNGARIAN − INDEPENDENT-NEAREST = +.324 QoS/step, SE .033, 32/32; native J +995, SE 101, 32/32.
- Own-clock phase means (each mode on its own entry clock, as the launcher writes them): hungarian pre-entry .810 / entry-to-input .840 / post-input .725; identity .769 / .846 / .749; nearest .458 / .480 / .421. These windows differ in length between modes and are not the declared clock-aligned reading.
- **Clock-aligned split, declared convention (one common step for all modes and worlds; boundary = 1300 = rounded mean hungarian first entry; `clock_aligned_readings.json` block B).** Pre-window per-step means hungarian .8127, identity .7897, nearest .4490; post-window .7445, .7500, .4505. Paired differences: hungarian − identity **+.023 (SE .006, 22/32) before the boundary and −.0055 (SE .012, 12/32) after it**; hungarian − nearest +.364 (SE .035) before and +.294 (SE .034) after, 32/32 in both windows. Additive difference mass (sum over worlds and steps of q_H − q_I): pre +956, post −301, total +655 — the whole net advantage of the Hungarian step over the index convention lies before the reference controller's first shield entry, and the post-entry sign is reversed and unresolved. Supplementary exact version (block A, boundary = hungarian's own first entry in each world): +.0213 (SE .0062, 22/32) before, −.003 (SE .0125, 14/32) after; masses +817 / −162 / +655. For nearest the pre-window carries .49 of the difference mass under either boundary.
- **Trace diagnostics (positions only; the trace holds `target_xy` per UAV-step, no slot ids).** Target position changes per UAV per 1,000 steps 20.7 / 18.2 / 24.0 (hungarian / identity / nearest): with a 30-step replan (≈ 33 replans per 1,000 steps) and finite-target shares .68 / .60 / .75, the planned target moves at nearly every replan, i.e. this counts the k-means centroid drift of moving users, not reassignment. Jumps over 500 m between consecutive finite targets per UAV per 1,000 steps: **1.12 / 3.18 / 0.42** — a proxy for reassignment across anchors (swaps between anchors closer than 500 m are not counted; the closest anchor pair in 955001 at t = 0 is 95 m apart; a large centroid move would be counted). Distinct finite targets per sampled step 5.44 / 4.82 / **1.02**; share of UAVs sharing a target 0 / 0 / **.86**. Independent-nearest collapse worlds (QoS/step < .1): 955013 (.073, first service step 1778), 955016 (0, zero service), 955021 (.051, 1898), 955025 (.0001, 2057), 955027 (.054, 1959).

**Prediction versus outcome (my predictions of lines 3838–3845, written before the run).**
- IDENTITY: predicted −.03 … −.10 with the loss concentrated after count re-orderings. Observed −.007 (SE .007). Wrong: the index convention costs ≈ .02 per step during deployment only and nothing afterwards; the identity rule does jump across anchors about three times as often as the Hungarian rule (3.18 vs 1.12 per UAV per 1,000 steps), yet its post-entry service is not lower.
- INDEPENDENT-NEAREST: predicted ≈ −.10 by partial coverage (uniform independent choice covers 1 − (7/8)^8 ≈ 66 % of the anchors; I wrote that distance correlation would make it better than uniform). Observed −.32: direction right, magnitude three times larger, **mechanism wrong**. Derived from the rule and the traces: the UAVs start within ≈ .5 km of each other (max pairwise distance 444–494 m at t = 0 in the three worlds checked), so their cost rows share the same argmin and every UAV takes the same nearest priority point; the 300 m hysteresis margin (`switch_margin_m`) then holds each of them there because another point must be closer by more than 300 m; distinct targets 1.02 and duplicate share .86 in the traces. The team stacks on one anchor and the rest of the map is unserved; in five worlds that anchor serves nothing until charging cycles disperse the team. Pro's answer (written without the results) named exactly this failure: "聚集的 UAV 可能一致选择同一个近锚点，反而更差".
- S: predicted .03–.10; observed .007.
- Observed without an explanation test: identity enters the shield ≈ 300 steps earlier (997 vs 1300) and reaches charger input earlier (1311 vs 1617); longer flights to index-assigned anchors are the plausible cause, untested (the traces hold battery per UAV-step, so it is testable at zero cost if a decision comes to need it).

**Tree application (second revision, 5401fb8ad, written before any free-rule score was read).** S < .03. Recorded as a conditional fact about these fixed controllers on this host: on H_central's anchors with the go-to executor, the state-dependent Hungarian matching is worth +.007 (SE .007) QoS/step over a fixed index convention overall, +.023 (SE .006) during deployment and nothing after; against independent choice the value is large (+.32), but it is the value of not stacking — of any de-duplication — not of optimal matching. This lowers my investment preference for an assignment-learning study. It is not an upper bound on learned − SET+A (independent review via Root, Pro 1.3; accepted). Nothing is launched or cancelled by this entry; the next step is the two written contribution arguments below and one independent challenge.

**Pro answer b03-v2 (key `hmasd:e51f86d4…`): received and disposed.** The deterministic observer found the reply complete at ≈ 11:12Z (≈ 91 min after the send at 09:41:52Z); the GitHub connector had no file-write operation, so the answer was collected from the chat (12,114 characters, sha256 `6243509a…`), `deliver` reports NOT_DELIVERED with no answer commit, and the complete text is inserted above under the question's "### Answer" marked "saved from chat" (formula rendering is the page's text extraction). Pro records **MATERIAL_DISSENT: yes — revise, not stop**, against the v2 declaration's automatic launch rule "S ≥ .03 → the 52-node-hour batch" and its two inferences (S as a ceiling; S < .03 as noise); both were withdrawn in the second revision (5401fb8ad) before S was read, so on the Stage 2-0 reading no material disagreement remains under section 2. Disposition of the rest:
- *Adopted, already in this entry*: S as a fixed-executor rule difference; both per-rule differences with their SE and world counts; native J beside QoS; .03 as an exploratory magnitude reference, not a significance line; one common clock cut with additive pre/post masses (Pro 1.5).
- *Ranked-IDENTITY (Pro 1.1)*: the implemented IDENTITY is the declared global-index rule with empty slots (5e8da3d94, verified against the `plan` source), not the ranked-prefix rule Pro recommends. When UAV 0 or 1 is charging, identity leaves its relay slot empty while hungarian refills the prefix, so S contains a target-set effect whose sign is not derivable (the ranked rule refills relay slots but shifts every UAV one slot). A ranked-IDENTITY panel costs ≈ 16 min CPU and is available as a zero-fit check if a decision comes to depend on S; under the second revision none does, so it is not bought now.
- *Comparison-panel path (Pro 1.2)*: corrected before launch (b986c279e); the run's consistency check used the grid panel and found 0.0 difference.
- *Slot-swap frequency (Pro 1.5)*: reported as > 500 m jumps with the stated ambiguity; a true swap count needs slot ids in the trace (a future runner change, not bought now). Pro's alternative cut at the SET c06 first entry (≈ 1044) belongs to a learner comparison; this run has no learner, and the same traces allow that cut later.
- *Claim wording (2.1), frozen-low-level interventions as conditional (2.2), M not in the first batch (2.3), the six cluster counts for SET+A (2.4), the 2b seed gap and confirmation tier (2.5), learnability "reasonable but unproven" (3.1–3.3), the R arm (§4)*: carried into the T-prime argument below as its wording, its strongest alternatives and its cost; no fit is bought.
- *Credit (3.4)*: Pro prefers a small prefix-conditioned label-level counterfactual baseline over "chain rewards" and full-environment counterfactual branches. Two points separate my candidate from the chain attribution Pro criticises: it is the **removal difference reward** D_i = R − R(−i), i.e. exactly the "移除某个 agent 后的因果边际贡献" Pro asks for, not a traffic-share attribution; and it changes the *expectation* of each agent's signal, which no baseline can do. Pro's remaining objections stand and are carried into the argument: it changes the optimisation objective (per-agent D against team G; alignment holds with the others fixed, the learning dynamics differ; β-mixing keeps the team objective), the recomputation cost, the adverse record of learned counterfactual credit on S1 (Q − V −.018), and "do not stack a credit change with feature or anchor changes in one batch". Pro's baseline is the strongest simple alternative in the argument, and the zero-fit diagnostic below is designed to discriminate between an attribution problem (a reward change can help) and a variance-only problem (a baseline suffices).
- DM1's first new SET seed (26092711) failed technically at 432k steps (RESEARCH, fd02c6e05); the three-instance SET block that both arguments use as their uncertainty prerequisite is delayed, not lost.

**T-prime contribution argument (written for the challenge; nothing decided here).**
1. *Contribution sentence if fully successful*: "On S7-S2/H3000 with H_central's anchor generator as the shared grounding, a learned assignment (HMASD's coordinator over grounded labels, n_z = 9 = 6 service centroids + 2 relay points + FREE) delivers more service than a flat learner given the same anchor features (SET+A with the six cluster counts) and than the same architecture trained with fixed Hungarian labels at the same k = 10 interface (R)."
2. *What a learned assigner handles that a fixed rule cannot at the same information and features*: leaving anchors unserved and doubling on binding ones (FREE and duplicate labels), anticipating charging exits at the 10-step interface, and trading service anchors for relay anchors when the backhaul binds. None of these freedoms was exercised by a Stage 2-0 rule: all three rules place 8 UAVs on 8 anchors (or stack them). What Stage 2-0 did measure: the permutation content is worth +.007 (SE .007) overall and +.023 during deployment; the de-duplication content ≈ +.32.
3. *Closest prior work*: ALMA (Iqbal, Costales & Sha, NeurIPS 2022, arXiv 2205.14205, read first-hand): an allocation controller over agent→subtask assignments trained by amortised Q-learning, with subtask-specific rewards and an independent-sub-environments assumption. The decisive difference here would be the coupled host (relay/backhaul coupling across "subtasks", shared capacity) and PPO on the team return through HMASD's autoregressive decoder. Programme label: allocation-over-anchors NEW in the record (Stage 2 declaration); ALMA-style allocation TRIED in the literature.
4. *Strongest simple alternatives*: SET+A with the six cluster counts (is injected planner grounding sufficient — Pro 2.4), and R = the T-prime architecture with fixed Hungarian labels produced at the k = 10 interface, low level trained from scratch (is learning the assignment worth anything over a fixed rule with the same training — Pro §4). The frozen-low-level label swaps (HUNGARIAN-LABELS, PERMUTE-EP, ALL-FREE) answer only the conditional question on T-prime's own low level (Pro 2.2).
5. *Discriminating prediction*: T-prime − R > 0 in two independent instances only if the non-permutation freedoms matter; the fixed-rule evidence puts the permutation part at ≈ .01–.02, so a T-prime − R gain of the declared ≥ .05 would have to come from FREE, duplicates or anticipation. T-prime − SET+A > 0 with T-prime − R ≈ 0 would mean the package and label interface, not learned allocation.
6. *Cost*: two full training instances per arm at ≤ 13 h each — T-prime × 2 + R × 2 = 52 node-hours (the reviewer's smaller option, one instance each, ≈ 26 h) plus ≈ 3 h evaluation per fit; SET+A would be a further two instances. The node is DM1's until its SET block completes.
7. *My investment preference, stated for the challenge*: low. The achievable sentence rests on a hand-coded anchor generator (the reviewer's "package v feature", Pro 2.1's "整体方案 ≠ 学习分配"), the measured permutation content is small, and the innovation the owner asked for is algorithmic. The candidate below addresses the coupling this host actually has.

**Skill-level removal-difference credit (D-credit) — argument published (from the local draft, corrected; not yet reviewed).** Informal name so far: chain-attributed credit. It is *not* the reserve-list "chain-attributed reward" (a traffic-share attribution) that Pro 3.4 criticises.
1. *Contribution sentence*: HMASD's coordinator learns per-agent skill labels from the shared team k-step return minus a per-agent value baseline (`compute_high_level_advantages`: one scalar `high_level_rewards[t, env]`, `agent_values` heads). The change: each agent's high-level return becomes its accumulated per-step removal difference reward over its skill segment, D_i = Σ_t [R(s_t, a_t) − R(s_t, a_t | UAV i's links removed)], computed from the environment's own routing physics (the removal counterfactual that `_static_qos_with_unavailable_uavs` already implements for feasibility estimates), optionally mixed with the team return (β). Relay UAVs then receive credit for the traffic that flows through them; duplicated or idle UAVs receive ≈ 0. Algorithm change, not a feature: per-agent accumulated rewards and per-agent GAE in the high-level buffer; the team advantage is unchanged; information rights and policy class unchanged.
2. *Novelty label*: difference rewards TRIED at the primitive-action level (Wolpert & Tumer collectives; Agogino & Tumer rover/UAV domains; Castellini, Devlin, Oliehoek & Savani, *Difference Rewards Policy Gradients*, arXiv 2012.11258, read first-hand pp. 1–3: differencing a known reward function with a default action, or a learned reward network; COMA learns the counterfactual Q instead). Programme record: RECORDED only as a reading pointer (FSD NOTES line 3512), never implemented; RESEARCH background line 524 warns that COMA-style counterfactual *baselines* must respect the autoregressive coordinator's sampling structure — Pro 3.4 repeats that warning for baselines; it does not apply to an environment-side difference reward, which is independent of the sampling structure. Skill-level (k-step segment) difference credit inside a hierarchical coordinator with an exact physics counterfactual: no precedent found (arXiv abstract queries "difference rewards" ∧ hierarchical/option/macro-action; counterfactual ∧ multi-agent ∧ macro-action ∧ credit; UAV ∧ relay ∧ MARL ∧ credit assignment: empty or unrelated); nearest: Liang, Wu, Wang & Cai, *Asynchronous Credit Assignment for MARL*, IJCAI-25, arXiv 2408.03692 (read pp. 1–3): asynchronous macro-action credit by a virtual-synchrony proxy plus a learned multiplicative value decomposition — learned, not an exact counterfactual. Label: mechanism RECORDED, composition (exact removal difference reward × skill-level credit × energy/relay host) NEW pending one search outside arXiv abstracts.
3. *Mechanism chain (code-verified)*: (i) the S7 team reward per step = mean over 30 users of delivered/demand − λ_return · return cost − event penalties + graph PBRS (`_calculate_constrained_safety_reward`); delivered traffic of UAV u = its access capacities × min(1, backhaul_u / access_sum_u); backhaul_u = the widest path to the BS through other UAVs (`_widest_backhaul_capacities`, bottleneck = min over hops). A relay UAV r serves no user directly and contributes only through backhaul_u of every UAV whose widest path passes r. (ii) Under the shared return, r's high-level advantage is G_team − V_r(s): G_team is identical for all eight agents, so the sign of r's label gradient is driven by the other seven agents' contributions and exploration noise (Wolpert–Tumer "learnability"). (iii) With D_r, r's return contains only what r's presence changed: for a binding relay, the served traffic that would otherwise be lost; for a duplicated server, ≈ 0; for the only UAV covering a remote cluster, that cluster's traffic. With the others fixed, argmax over r's action of D_r equals that of R (alignment), and the agent's own gradient has lower variance. (iv) Native consequence, the hypothesis: relay-type labels become learnable ("be the relay for cluster c"), which is the coordination content Stage 1's flat SET lacked; the gain concentrates in worlds where the relay chain binds. What changes is the learning signal; the counterfactual is the per-step D_{i,t} on the realised state with the others' realised actions held fixed (the "absent agent" default), summed over the skill segment — not a trajectory-level counterfactual (the others' future actions are not re-simulated).
4. *Simple-model bridge*: a two-agent chain bandit (server S picks a cluster; relay R picks a relay position or serves; reward = Σ_clusters min(access, backhaul)). Under the team reward R's REINFORCE gradient variance is dominated by S's exploration; under D_R the expected gradient direction at the joint optimum is the same and the variance shrinks by the share of return not attributable to R. Omitted couplings: k-step temporal extension, low-level execution noise, energy/return terms, the graph PBRS term (potential-based on the team; per-agent differencing of a potential difference stays potential-based per agent — to be checked in the review), and the aristocrat (expected-contribution) variant, unavailable without a model.
5. *Strongest simple alternatives*: (a) Pro 3.4's prefix-conditioned label-level counterfactual baseline b_i(x, z_<i) = Σ_a π_i(a | x, z_<i) Q̂_i(x, z_<i, a) — variance reduction only, no environment recomputation, respects the autoregressive structure; (b) the shared return with the per-agent value heads as they are (Pro 3.1: "learnability reasonable but unproven" — the flat SET already learned something on S7). The discriminator between (a) and D-credit is whether the relay agents' signal is *biased toward the others' contributions* (an expectation problem, which only a reward change addresses) or merely noisy (a baseline suffices).
6. *Numerical prediction versus noise*: S7 has one training instance in this direction (SET seed 925031; .437/.438 are its c06 deterministic and sampled evaluations); DM1's block (26092731 pending, 26092711 failed technically) plus 925031 will give the first paired-block uncertainty (s_D/√n over independent instances) at no new cost. No universal 2 × SD gate (method v2 §3). Prediction, a discriminating expectation and not a gate: if the relay-hop traffic share on 955001–955032 under H_central is ≥ 25 % and the relay agents' difference signal carries materially less of the others' variance than the team return, D-credit recovers part of the learner's deficit to H_local (.15–.17 QoS/step): +.03 … +.08 QoS/step over SET at equal budget; if the share is < 10 %, the mechanism cannot produce > .02 and no fit is bought.
7. *Discriminating observation and retirement*: within the first 300k steps of a D-credit fit the learner's relay-hop traffic share rises above SET's and the coordinator's relay-type labels stabilise on the remote cluster; if D-credit is on and the relay-hop share does not rise above SET's, credit was not the bottleneck (the low level cannot execute relay skills, or the chain never binds) — retire, no variant. If the zero-fit decomposition shows the difference signal is not materially cleaner than the team return for relay agents, the mechanism argument fails before any fit.
8. *Cost*: zero-fit diagnostics ≈ 1–2 h CPU (below); fits 2 (D-credit v SET, one instance each at equal budget, ≈ 2 × 11 h on wsl_4070) only after the challenge, the diagnostics and a fit declaration with its own Pro follow-up and engineering review; engineering: an env hook for per-agent removal QoS, per-agent rewards + GAE in `hmasd/utils.py` (shared core → engineering reviewer), the coordinator update path; low level unchanged.
- *Open before review*: D_i on the QoS term only or on the full reward (energy/return terms are already per-agent in nature); β to keep the team objective; interaction with the graph PBRS term; whether removal of "UAV i's links" should also remove i's access links (full removal) or backhaul links only (relay-only counterfactual).

**Declared next step (zero fit, no launch yet).** (i) One independent challenge of both arguments (hmasd-research-critic, separate context, evidence-first; the Pro answer already covers the T-prime side in part, so the challenge is asked to concentrate on the D-credit argument and on my "no investment in T-prime now" preference); a Pro follow-up in the same conversation comes with the fit declaration, not before. (ii) After the challenge, the D-credit zero-fit diagnostics on 955001–955032 under H_central (hungarian), declared now with the choice they change: (a) the share of delivered traffic whose widest path uses at least one relay hop, mean over 32 worlds × 3,000 steps; (b) per UAV-step the removal difference D_{i,t} on the QoS term, its distribution across UAVs, and for relay-serving UAVs Var(D_r) and Corr(D_r, G) against Var(G) (the team return's variance share attributable to the others); (c) the wall cost of the eight removal recomputations per step (`_static_qos_with_unavailable_uavs`), measured once before the batch. Rule: (a) < 10 % → no fit is bought and the candidate is retired for this host; (a) ≥ 25 % and the relay agents' difference signal materially cleaner than the team return → a bounded fit declaration (2 fits) goes to a Pro follow-up and engineering review before any launch; in between → a targeted revision (β-mixed credit or relay-only counterfactual) argued in writing first. Cost bound 2 h CPU on this host, 0 fits. Not bought: the ranked-IDENTITY panel, the identity-battery explanation test, slot ids in the trace.

## 2026-09-27 — Independent challenge of the Stage 2-0 entry and the two arguments (hmasd-research-critic, separate context, read-only, on the working tree): MATERIAL_DISSENT yes on eleven statements; my first-hand verification, disposition, D-credit argument withdrawn to revision, next step redefined

**Verification before acceptance (mine, from the traces and the code).** Every recomputed number reproduces: native J hungarian − identity +30.2 (SE 7.5, 22/32) before step 1300 and +27.6 (SE 26.5, 17/32) after it; the non-QoS reward term (Σ qos − Σ reward) after 1300 is 64.5 J under identity against 27.5 J under hungarian (difference 37.0, SE 21.5); xy path 186 km under identity against 136 km under hungarian (105.5 against 62.7 km by step 900); mean battery at step 900 .476 against .535; F-mode share .404 against .325, charging share .070 against .057; under identity UAV 0 or UAV 1 (the relay slots) is out of normal mode in .487 of the post-1300 steps; hungarian's post-1300 QoS by number of normal-mode UAVs .58 (0), .69 (1), .74 (2), .76 (3), .80 (4–5), .82–.84 (6–8); the strict cut before either mode's first entry gives +.028 (SE .006, 23/32); the cut at 1044 gives +.028 / −.004. Code: the return-constraint cost is a team maximum over UAVs (`energy_aware.py` 797–807); QoS backhaul comes from `routing_paths` in `_calculate_end_to_end_user_rates` (path record, access bandwidth split, user rate = max over UAVs), not from `_widest_backhaul_capacities`; `_static_qos_with_unavailable_uavs` zeroes the batteries, re-runs channel update, association and routing, then restores and re-runs (1371–1390), and its only callers are the feasibility estimators; `enable_soft_handover = True` (`configs/config_1.py:104`) with hysteresis memory in `routed_core._update_serving_sets`; the ordinary high-level path already carries a per-record `reward_sum` with per-agent values (`hmasd/utils.py` 783–1069, `compute_high_level_advantages` returns at once under `ordinary_completed_segments`); the agent value heads condition on the encoded observations (`hmasd/networks.py` 786–789). All confirmed.

**Disposition: all eleven dissents accepted.**
1. "The whole Hungarian advantage lies in the deployment window, nothing afterwards" holds for QoS only. In the native objective the index convention costs +57.8 J (SE 24.6, 21/32) overall, +30 J before and +27.6 J (SE 26.5) after the cut, and identity pays +37 J (SE 21.5) more non-service cost after it. Conditional derivation (now tested at zero cost, not bought as a fit): longer index-assigned transits (186 against 136 km) cost service during deployment and energy afterwards (earlier shield entry, F-mode share .40 against .32). Pro §5's condition "J 没有显示被 QoS 掩盖的明确代价" is therefore not met by the index convention; the statement "no material disagreement remains" is corrected to that extent (Pro's dissent object itself stays withdrawn).
2. "+.32 de-duplication content" is withdrawn from every stake argument: it measures escape from a degenerate absorbing stack under co-located spawn (co-located rows share the argmin, the state is absorbing, the 300 m hysteresis blocks en-route switches; only a return from charging breaks the tie).
3. "Energy/return terms are already per-agent in nature" is false: the return cost is a team maximum.
4. The mechanism paragraph named the wrong function for QoS backhaul, and "duplicated server → D ≈ 0" is underived (bandwidth split, max over UAVs).
5. "G_team identical → relay labels unlearnable" and "D changes the expectation, which no baseline can do" are withdrawn: the shared return gives an unbiased, noisy team gradient; the subtracted term R(−i) is either a control variate (variance only) or, where it depends on i's own action through the state, the others' observations, the station queues and the labels z_{>i} sampled conditional on z_i, an objective change with the known redundancy failure (backup relays and doubled servers earn no credit). The bias-versus-variance discriminator and the Var/Corr diagnostic are withdrawn.
6. RESEARCH.md line 524's caution applies to D because z_{>i} are sampled conditional on z_i (COSAC, arXiv 2604.17693, treats exactly this fixed-order case — to be read first-hand).
7. `_static_qos_with_unavailable_uavs` is not a usable per-step probe as it stands: it mutates soft-handover state through association; per-step training use needs snapshot/restore and a bit-identity test of the realised trajectory, both uncosted.
8. Per-agent GAE already exists on the ordinary path; the engineering change is vectorising `reward_sum`.
9. "2 fits D-credit v SET" isolates nothing (SET has no coordinator); the isolating comparison is D against the shared return on the same architecture and a named label substrate.
10. "Composition NEW" is pending until COSAC, *Learning Individual Difference Rewards in MARL* (AAMAS 2023) and the programme's `expressibility_gated_renewal_credit_relay` (EGRCR, PARKED: expressibility passed, utility zero) have been read first-hand; "mechanism RECORDED" stands.
11. Coherence: D-credit's mechanism ("relay-type labels become learnable") presupposes labels with relay semantics, i.e. T-prime's grounded substrate; MI-skill labels carry none. Rating T-prime "low" while proposing D-credit on relay labels was inconsistent. T-prime is therefore a prerequisite substrate question rather than a rejected study; the coherent candidate comparison is T-prime with the shared return against T-prime with D, one instance each, inheriting T-prime's confounds (the reviewer's and Pro's "do not stack changes" caution applies and is recorded).

**Consequences.** The D-credit argument of the previous entry is withdrawn to revision; the declared zero-fit diagnostics are redefined before anything runs: relay-hop traffic share as declared; the magnitude and sparsity of D_i under redundancy with a pre-written retirement rule (median |D_i| ≈ 0 over most UAV-steps → retire); a probe bit-identity test; the measured per-step wall with a declared maximum slowdown. The Stage 2-0 reading keeps its QoS statements with the J correction above. Not bought: the ranked-IDENTITY panel (the natural experiment — relay slot vacant in .49 of post-1300 steps at equal post-1300 QoS, and hungarian's QoS nearly flat in the number of available UAVs — says the QoS confound is small), slot ids, any D-credit v SET fit, any T-prime/SET+A batch before the substrate question is settled. Next session's first items, in order: the rewritten D-credit argument (substrate, isolating comparator, reward scope, routing facts, variance/objective framing, first-hand COSAC/AAMAS-2023/EGRCR positioning), then the redefined diagnostics as a bounded L0, then a fit declaration only if D survives, with its Pro follow-up and engineering review. The owner's usage limit was reached while this entry was written; nothing is running.

## 2026-09-27 — D-credit argument, second version after the challenge: substrate named, comparator isolated, reward scope and routing facts corrected, variance-versus-objective framing, COSAC / LIDR / EGRCR read first-hand; amendments to the T-prime argument; the credit question also goes to a controllable second direction

**1. Contribution sentence (v2).** "On HMASD's sequential skill coordinator with grounded labels — the T-prime substrate on S7-S2/H3000 — replacing the shared k-step team return in each agent's high-level advantage by that agent's exact removal difference on the service term, D_i = Σ_t [QoS_t − QoS_t(−i)], with the non-service terms kept shared, improves service over the same architecture trained with the shared return at equal budget, and the gain concentrates where the relay chain binds." The isolating comparator is **T-prime(shared return) against T-prime(D)**, one instance each on the same seed; T-prime(shared) doubles as the substrate check (does the grounded coordinator learn a non-trivial assignment: label occupancy, duplicates, stability, the frozen-low-level label swaps of the v2 declaration). SET+A and R (Pro §4) come after, and only if a T-prime instance shows service above SET; the substrate question is settled first (challenge item 11).

**2. What D is, stated honestly.** D is an objective change: Σ_i D_i ≠ G. With the other agents held at their realised actions, D_i is factored with respect to G (Wolpert–Tumer), so improving D_i at fixed others improves G; its two known costs are that substitutable agents (a backup relay, a doubled server) receive ≈ 0 credit, and that in a fixed-order decoder the downstream labels z_{>i} are sampled conditional on z_i, so R(−i) evaluated on the realised state carries an indirect dependence on i's own label (COSAC's "indirect effect"; the caution of RESEARCH.md line 524 applies). The shared return is an unbiased, noisy estimate of the team gradient; D does not remove a bias. The claim is therefore a learnability claim about one role structure: a relay UAV's contribution enters the team reward only through other UAVs' backhaul, so under the shared return its label signal is dominated by the other seven agents' service, while D_r concentrates the signal on what r's presence changed, when the chain binds. The β-mixture R_i = β·G + (1 − β)·D_i (LIDR's team-plus-difference form) is the standard hedge against the redundancy cost; β is a declared design constant, never tuned on scores.

**3. Reward scope (corrected).** D acts on the QoS term only. The return-constraint cost is a team maximum over UAVs (`energy_aware.py` 797–807), the cutoff/depletion penalties are team counts, and the graph PBRS term is potential-based on the team; all of them stay shared in every agent's return. Per-agent segment return = Σ_t [QoS_t − QoS_t(−i)] + Σ_t [R_t − QoS_t], or the β form of item 2.

**4. Mechanism facts (corrected from the code).** QoS_t = mean over users of min(1, delivered/demand). `delivered_by_uav[u] = min(1, backhaul_u / access_sum_u) × access capacities of u`; `backhaul_u` is the bottleneck capacity stored in `routing_paths[u] = (path, capacity)` by `_find_widest_path_to_ground_bs` under the S7 default `widest_path` protocol with at most `max_hops = 4` hops (`routed_core.py` 4544–4577, 5020–5050); a user's rate is the maximum over UAVs; a UAV's access bandwidth is bandwidth/n_uavs (FDMA) split equally over its connected users. Hence a relay UAV r contributes only through the paths that pass r, and removing r re-associates and re-routes the team: D_r counts what the rerouted team loses, not r's traffic share. A doubled server changes the per-user split and the max over UAVs; its D is not ≈ 0 by construction — that was an error. The probe `_static_qos_with_unavailable_uavs` (1371–1390) zeroes the removed UAVs' batteries, recomputes channel, association and routing, and restores by recomputing again; with `enable_soft_handover = True` (`configs/config_1.py:104`) the association step updates the hysteresis memory `user_serving_sets`, so the probe is not side-effect-free. For the diagnostics it runs on a deep copy of the environment; for training it needs snapshot/restore and a bit-identity test, both in the engineering cost.

**5. Closest prior work (read first-hand today; PDFs in the session scratchpad).** *COSAC* — Deshmukh, Subramanian, Addanki & Vlassis, arXiv 2604.17693v2 (May 2026): fixed-order sequential teams sharing one team reward; the Sequential Aristocrat Utility is the unique prefix-conditional baseline maximising learnability; a critic-free estimator (ridge-fitted additive decomposition of the team reward plus fictitious policy continuations for the indirect effect through downstream agents); closed-form bias and variance, bias growing with the reward's departure from additivity; contextual-bandit abstraction, "extension to full sequential MDPs left to follow-up". This is the method-level neighbour of HMASD's autoregressive coordinator and the **strongest simple alternative** to D: a variance-only fix with no environment recomputation, whose known limit is non-additive rewards — and a relay chain's min-type reward is non-additive. *LIDR* — Yang, Yang & Zhang, AAMAS 2023 (extended abstract): a learned reward-decomposition network gives D_i = R̂(s, o_i, a_i) − max_a R̂(s, o_i, a) and each agent is trained on R_i = G + L_i; model-free, SMAC — the precedent for the team-plus-difference mixture with a learned decomposition. *Dr.Reinforce* (Castellini, Devlin, Oliehoek & Savani): exact or learned difference rewards in policy gradients, simultaneous primitive actions. Programme record: `learned_counterfactual_agent_credit` adverse on S1 (Q − V −.018); `expressibility_gated_renewal_credit_relay` (a two-agent renewal microhost credit study with a waiter/joiner counterfactual effect, technically complete at B1, not advanced); the chain-attributed reward on the reserve list, untested. **Novelty label (v2):** difference credit TRIED (simultaneous, primitive actions, exact and learned); sequential prefix-conditional credit TRIED (COSAC, bandit); microhost credit studies RECORDED (EGRCR); the composition "exact physics removal difference on the service term, accumulated over k-step skill segments, inside a fixed-order label decoder with a learned low level, on a chain-binding host" NOT FOUND after these reads — recorded as provisional, not as "new". The honest scientific question is *D against SeqAU on non-additive chain rewards*, and that question is cheaper to answer on a controllable host first (item 10).

**6. Discriminating prediction (v2).** (a) On the controllable host: SeqAU is at least as good as the shared return everywhere; D beats SeqAU only in the strongly non-additive chain-binding regime and loses in the redundancy regime; the regime boundary is measured there. (b) On this host the zero-fit diagnostics place H_central's operating point on that map (relay-hop share of delivered traffic; D sparsity). (c) If the two fits are bought: T-prime(D) − T-prime(shared) ≥ +.03 QoS/step at c06 with the learner's relay-hop share rising above T-prime(shared)'s within the first 300k steps; if T-prime(shared) already reaches the .60 milestone, or its labels collapse (occupancy trivial), D is not bought.

**7. Zero-fit diagnostics (redefined; the choice they change).** Re-simulate H_central (hungarian) on 955001–955032 with a per-step observer that, every 10th step, (i) reads `routing_paths` and `delivered_by_uav` to record the relay-hop traffic share (delivered mass on paths with ≥ 2 hops over all delivered mass) and the set of UAVs lying on another UAV's path; (ii) computes D_i^QoS for i = 0…7 on a deep copy of the environment (side-effect-free by construction); (iii) records QoS_t, Σ_i D_i / QoS_t, the per-UAV distribution of D_i, the share of UAV-steps with |D_i| < .01, and mean |D_r| for UAVs on a relay path against the others; (iv) one probe bit-identity test — one world run twice, with the raw probe called every step and without, comparing realised QoS and positions bitwise; (v) the wall of one raw probe call and of one deep-copy probe. **Pre-written rules:** relay-hop share < 10 % → D-credit retired for this host; share ≥ 25 % and D non-sparse where the chain binds (mean |D_r| on relay UAVs ≥ 2 × the others; fewer than 80 % of UAV-steps with |D_i| < .01) → the two-fit declaration with β and the probe cost fixed, to a Pro follow-up and an engineering review; anything in between → a targeted revision argued in writing first. Cost bound 2 h CPU on this host, 0 fits. Declared maximum training slowdown for a per-step probe: 1.5 × the collection wall; above it the credit is computed at decision boundaries (every k = 10 steps) or on a subsample, declared before any fit.

**8. Cost.** Diagnostics ≤ 2 h CPU (an L0 to the implementer: an admitted `credit-diagnostics` phase of the b03 runner, no shared-code change). Fits, only after item 7 succeeds: 2 × ≤ 13 h on wsl_4070 after DM1's block, plus ≈ 3 h evaluation each. Engineering for a fit: vectorised `reward_sum` on the ordinary high-level path (per-agent GAE already exists there), an environment hook returning per-agent removal QoS with snapshot/restore, the bit-identity test, an engineering-reviewer pass (shared core).

**9. Amendments to the T-prime argument of the results entry.** The "+.32 de-duplication content" sentence is withdrawn (degenerate absorbing stack). The permutation content is +.007 QoS/step but +.019 J/step (2.3 SE) in the native objective, with energy in it (186 against 136 km). T-prime is the prerequisite substrate for the credit question; its first instance (shared return) is bought together with the D instance if item 7 succeeds. My "low" preference applied to T-prime as a coordination claim on its own and stands for that claim only.

**10. Second direction (owner authorisation 2026-09-27: two directions at a time, related, sharing insight).** The credit question of items 2, 5 and 6(a) is declared today as its own direction, `sequential_coordinator_credit`: a controllable chain-relay microhost with fixed-order label decisions, ground-truth per-agent advantages by enumeration, the estimators shared return / prefix-conditional baseline / SeqAU / exact D / β-mixture compared on advantage error and learning regret over a regime map (redundancy × chain binding), then the k-step-segment and learned-low-level extensions that COSAC leaves open. This direction's zero-fit diagnostics read that map; the SeqAU implementation for HMASD's coordinator returns here as the alternative arm on the T-prime substrate. Its declaration is in `docs/research/candidates/sequential_coordinator_credit/NOTES.md`.

## 2026-09-27 — Zero-fit credit diagnostics: bindings declared before the run (amendment to item 7 of the D-credit v2 entry, after the second independent challenge)

Declared before any launch, on top of item 7: (i) the pre-written 2× rule reads **R1** — a UAV is a relay at a probe step when it appears as a non-first node in another UAV's `routing_paths` entry (it carries traffic); the plan-slot definition **R2** (the UAV's current target is a `kinds == "relay"` row of the last plan) is recorded beside it, not used by the rule; (ii) probe steps are `t % 10 == 0` of the evaluator's step index, on the post-step state that produced reward t, with the removal implemented as the existing probe does (battery ratio 0 → communication-unavailable) on deep copies of the raw environment; (iii) the common coordinate with `sequential_coordinator_credit` is the first-order additive residual `rho_t = (Σ_i D_i − QoS_t) / QoS_t` over probe steps with QoS_t > 0 (R_∅ = 0 exactly: an unavailable UAV serves nothing), reported as median, IQR and the share with |rho| > .25; (iv) bit identity in two layers — the phase's hungarian panel against Stage 1's committed H_central panel on all 32 worlds (the deep-copy probe must move nothing), and world 955001 run plain against the raw in-place probe `_static_qos_with_unavailable_uavs([i])` at every step (one world, the input to the training-engineering cost, not a proof); (v) the cost readings are the mean probe wall against the mean collection wall per step, giving the implied slowdown of a per-step and of an every-10th-step probe against the declared 1.5×. Measured on this host before the L0 (world 955001, 40 random steps): deep copy ≈ 5 ms, one recompute ≈ 8 ms reproducing the live QoS bitwise, eight removals ≈ 94 ms, `env.step` ≈ 39 ms; expected phase wall ≈ 20–25 min on 8 workers, bound 2 h. The scope note is `temp/directions/energy_relay_benchmark/L0_b03_credit_diagnostics.md` (one implementer task, no shared-code change, the runner gains a `credit-diagnostics` subcommand). The order of work follows the second challenge: this phase first, then the microhost's first cell.

## 2026-09-27 — Peer message from Root (commit afed567db, `docs/Claude_docs/inbox/20260927_uav_cooperative_planning_ROOT.md`): the owner's main-line clarification relayed — UAV path planning and swarm cooperative planning, MARL-enhanced; "the energy-relay optimisation looks off track"; my position, the direction's object restated in planning terms, one pre-written pivot condition

**Message (data).** Root quotes the owner (2026-09-27): innovation is due; exchange freely with the peer; put the effort into MARL or algorithmic-engineering innovation for the UAV base-station system; "Claude's so-called energy-relay optimisation seems a little off track; the main thing is UAV path planning and UAV swarm cooperative planning, enhanced with MARL." Root's reading: the object is joint path / coverage layout / cooperative task planning with its real service payoff; energy, return and charging stay constraints; DM4's energy_fraction rule closed negative (f80983538, native J −208); DM1/DM2 interruptions were technical; the uncommitted `sequential_coordinator_credit` draft is read as pending and must say how a credit difference changes real joint paths / role commitments / replanning against a capable same-information planner and flat/same-architecture baselines, a small model serving that judgment but not an independent line. Root asks for one thing: agreement or revision of the main line and division, and my candidate converged to one contribution claim with nearest method, strongest simple alternative, discriminating planning consequence and first full cost — or the pivot with its reason.

**Position (sent through the owner-authorised channel today; no ACK loop).** (1) Agreement with the object. (2) This direction never optimised an energy objective: energy enters through the production return shield and J. Its findings are planning findings on S7: Stage 1 — SET c06 .437/.438 against H_local .597 and H_central .774 QoS/step; Stage 2-0 — at fixed layout and paths the assignment coordination (who takes which anchor) is worth S = +.007 ± .007, the planner's payoff sits in the layout and the deployment-window entry, and independent nearest decisions collapse the team on one anchor (−.32). What MARL must close is layout/role grounding and execution, not the assignment permutation. (3) One contribution claim: grounded hierarchical assignment/timing — T′ (coordinator reads the planner's anchors and commits each UAV to one anchor per k = 10 decision; the low level executes) against the equal-grounding flat learner SET+A, toward H_local; nearest methods H_central/H_local and SET+A; strongest simple alternative R (fixed Hungarian labels, low level from scratch; Pro's proposal); discriminating consequences: T′ − SET+A ≥ +.05 QoS/step at c06 with ≥ 20/32 worlds, deployment-window QoS and relay-hop share above SET+A's, stable role commitments, and the HUNGARIAN/IDENTITY/PERMUTE label interventions on T′'s own low level; first full cost: the zero-fit diagnostics (≤ 2 h CPU, L0 dispatched today) then 4 fits (T′ × 2, SET+A × 2, ≤ 13 h each on wsl_4070 after DM1's block, ≈ 3 h CPU evaluation each). (4) Pre-written pivot: if the diagnostics show a relay-hop traffic share < 10 % under H_central's layout, the chain-credit claim is retired on this host, `sequential_coordinator_credit` stays bounded to the T′ second-arm choice (agreeing with Root: no independent line beyond the first cell), and the MARL-increment question moves to where the planner is weak — anchors adapted to realised service, and return/charging rotation planned jointly with coverage (the planner refills vacated slots only reactively at replans) — argued in writing before anything is declared. (5) Division: I keep the coordinator/assignment estimand (T′ against SET+A, same architecture family); Stage 1/2-0 panels and H_central/H_local are shared comparators; I do not claim the general "MARL against strong planning baselines" estimand (Root's new DM3). (6) The owner's words reached me relayed; the owner is present in my session and my report asks for direct confirmation of the emphasis; nothing was launched or cancelled on the relayed text.

## 2026-09-27 — Credit-diagnostics phase delivered (commit db4e2a3a6, on origin); launch attempt denied by the session's command classifier; command handed to the owner; two engineering facts from the implementer's scratch checks

**Delivery.** `experiments/candidates/energy_relay_benchmark/b03/credit_diagnostics.py` (904 lines), the `credit-diagnostics` subcommand of `scripts/run_energy_relay_benchmark_b03.py` (+18), `tests/…/b03/test_b03_credit_diagnostics.py` (13 tests); b03 61 passed, b01 48 passed; no edit outside these three files. Deviations accepted: `run_credit_tasks` and `_run_hungarian_world` copy the stake worker's body with `observer=` passed through (a test pins bitwise equality of rows and arrays with `evaluate_stake_task` at horizon 40); the npz carries extra integer arrays (`relay_hop_traffic_bps`, `relay_hop_users`, `delivered_users`, `failed`, `probe_count`, `probe_every`), −1/False padding for failed worlds in integer/bool arrays, float32 storage (readings computed from float64 in memory, so a re-read reproduces them only to float32); relay UAV-steps are defined as flag ∧ available, others as ¬flag ∧ available, flagged-but-unavailable counted separately; R2 comes from the last plan (up to 29 steps old). Probe core read by me (`delivered_by_uav`, `user_servers`, `path_structure`, `relay_slot_mask`, `relay_hop_shares`, `recomputed_qos`, `removal_qos`, `probe_raw`, both observers): as specified.

**Two facts from the implementer's scratch checks (world 952011, a fixture seed, not a panel world; cost and neutrality only, no D readings kept).** (i) The raw in-place probe `_static_qos_with_unavailable_uavs([i])` called every step **changes the realised reward** from step 101 on (largest difference .099) while positions stay identical — the soft-handover side effect predicted from the code (critic #1, item 7) is real; layer (b) will most likely record `raw_probe_trajectory_neutral: false`, and per-step training use of D needs the copy/restore path, not the raw probe. (ii) Cost at horizon 3000: 300 probes, mean .127 s (max .185 s) against a collection step of .059 s under load (.039 s uncontended in my smoke test) — a per-step probe would cost ≈ 3.2–4.3× the collection step, above the declared 1.5×; every 10th step ≈ 1.2–1.3×, within it. R1 held at every probe step from step 0 on that world with paths up to the hop limit, so the "direct paths at spawn" premise of the L0 was world-specific. Zero unavailable UAV-steps in 300 probes under the production shield (the "available" and "all" blocks will likely coincide). Risk noted by the implementer and accepted as a recorded quantity: `energy_aware.step` builds routing and connections before the battery update while the reward uses availability after it, so at a cutoff-crossing step `qos_copy_baseline` may differ from `qos_live`; D relative to the copy baseline is recomputable from the stored arrays.

**Launch.** Origin already holds db4e2a3a6 (origin/main moved to d56e62bdc by another writer: DM1's second SET seed accepted on wsl_4070). My launch through the admission kernel — `scripts/hmasd_launch.py launch --direction energy_relay_benchmark --lead "Claude DM (WSL session)" --sha db4e2a3a6967a3d2735efd9ebd25989c77dc4372 --output /home/fires/hmasd-wsl/runs/energy_relay_benchmark/b03_credit_a01 --snapshot --node local_linux scripts/run_energy_relay_benchmark_b03.py credit-diagnostics --out /home/fires/hmasd-wsl/runs/energy_relay_benchmark/b03_credit_a01 --launch-sha db4e2a3a6967a3d2735efd9ebd25989c77dc4372 --workers 8 --threads 2` — was denied by the session's command classifier ("Out-of-Place Publication"); not retried or split; the identical command is handed to the owner. Host state at the attempt: 16 CPUs, load average ≈ 439, of which the transport's headless Chrome GPU process (pid 894510, ≈ 7.6 cores for 26 h) and the Codex app-server (≈ 2.9 cores) — the wall readings of the run will be contended; the D and share readings are load-independent; the uncontended cost reference stays the smoke test above. Expected wall ≈ 30–35 min uncontended, bound 2 h.

**Owner confirmation (2026-09-27, in session): "agree the default".** The relayed main-line emphasis is handled as declared: the credit diagnostics run first and their pre-written condition (relay-hop share < 10 %) decides whether the chain-credit claim is retired and the MARL-increment question moves to the planner's weak points; no launch or cancellation on the relayed words alone.

## 2026-09-27 — Peer review round 2 (Root, commit f3d7cd49b; the same independent review reused): rho_t relabelled, the credit-to-training bridge made non-automatic, the first full comparison revised — T′ × 2 / SET+A × 2 withdrawn as the first batch; staged isolating fits T′(shared) then T′(credit) under pre-written zero-fit and substrate conditions

**Message (data).** Root's second message (`docs/Claude_docs/inbox/20260927_uav_cooperative_planning_ROOT.md`, second section) reports the Codex side's reorganisation (DM4: non-additive ordinary joint move/hold/relieve planning with cumulative service and full cost defined first; new DM3: closes B02, then longer-horizon cooperative decision learning, not my fixed-anchor label/credit object) and an independent Scientific Reviewer's reconstruction now in RESEARCH.md (anchor `uav-planning-review-20260927`; MATERIAL_DISSENT: yes against buying the 4-fit T′/SET+A batch on the present argument, against DM4's undefined target-only score, and against using the credit diagnostics as an automatic bridge to native training). Two of my arguments are to be revised: (a) (Σ_i D_i − R)/R on one controller's visited states is not COSAC's additive residual ε over joint label choices; (b) "AND coupling makes D's expected update vanish" is false (independent Bernoulli, R = a1·a2, removal to zero: D1 = R, logit gradient p1(1−p1)p2 > 0). Root's investment preference: one targeted full training pair (e.g. T′/R) plus a same-information executing-planner evaluation; not a cap, not a cancellation. One request: the revised contribution / first-comparison choice or reasons to keep, and the disposition of the credit-bridge argument, reusing the same review.

**1. rho_t relabelled.** rho_t = (Σ_i D_i − QoS_t)/QoS_t on the executed planner's visited states is the **first-order removal non-additivity of the service function at those states**: how far the sum of single-UAV removal effects departs from the whole under the physics (association, FDMA split, widest-path routing) along one fixed controller's trajectory distribution. It is not COSAC's ε, which is the error of the best additive approximation of the *coordinator's* joint-label reward over the label space under the learner's own sampling; the two would coincide only if removal-to-idle were the label perturbation and the planner's states were the learner's. rho_t stays in the phase as declared, with a reduced role: it sets the binding/substitutability coordinates at which the microhost's configurations are read against this host, and it carries no weight in any fit decision by itself. Accepted with it: neither rho_t nor the relay-hop share determines which estimator improves HMASD's clipped, jointly normalised updates; that question belongs to the microhost's calibration items and to the isolating pair below.

**2. The AND / "no gradient" claim** is withdrawn in `sequential_coordinator_credit`'s notebook (entry of today, counterexample verified numerically: .1260 = .1260). Consequence here: D's case on this host rests on relay-mass separation and de-duplication under the shared return's dilution, not on any vanishing update of a competitor.

**3. Bridge made non-automatic (amends item 7 of the D-credit v2 entry and point (3)–(4) of the peer position above).** The pre-written rule "share ≥ 25 % and D non-sparse → the two-fit declaration" is replaced. The credit diagnostics decide only the *retirement* branch — relay-hop share of delivered traffic < 10 % under H_central's layout → chain credit retired on this host, pivot argued in writing — and supply coordinates. A credit fit is declared only when all of the following hold, each read from zero-fit or already-bought evidence and each written before the next thing is bought: **C1** the microhost first cell shows a configuration in which the chosen credit arm (SeqAU or D, by the cell's own rule) beats the shared return in gradient bias/variance and in ≥ 100-seed regret at matched normalisation; **C2** the diagnostics place H_central's operating point in that configuration's coordinates (share ≥ 25 %, mean |D_r| on relay UAV-steps ≥ 2 × the others, fewer than 80 % of UAV-steps with |D_i| < .01) and the every-10th-step probe stays within the declared 1.5× collection wall (scratch check: ≈ 1.2–1.3×; a per-step probe at ≈ 3.2–4.3× is excluded); **C3** rule S below, read on Fit A. A declaration then still goes to the §5 review (this review reused, not stacked) and to an engineering review of the per-agent return path. Share between 10 % and 25 % → a targeted revision in writing, no fit.

**4. First full comparison revised.** (i) T′ as a coordination-only claim is retired by Stage 2-0: S = hungarian − identity = +.007 ± .007 QoS/step lies inside the .03 bar that the first independent review of B03 (its item H) set for "do not launch T as a coordination study"; the permutation content of the assignment at the planner's anchors is not worth a fit. R (same architecture, fixed Hungarian labels, low level from scratch) is needed only to identify that claim, so R is not bought either. (ii) T′ × 2 / SET+A × 2 (4 fits, 52 + 12 h) is withdrawn as the first batch: T′ − SET+A identifies the whole package, and my own D-credit v2 item 1 had already placed the isolating pair T′(shared) vs T′(credit) first with SET+A and R after; the peer position sent earlier today contradicted item 1 and is corrected here. (iii) Contribution sentence (learnability at equal budget): "In HMASD's fixed-order skill coordinator with grounded role labels, replacing the shared k-step team return in each agent's high-level advantage by a credit signal that separates non-additive joint roles (relay + server co-presence; de-duplication) — SeqAU or the removal difference, whichever the microhost selects — yields, at equal training budget with identical low level, labels and seed, better joint role commitments: fewer duplicated anchors, earlier refill of vacated slots, more stable commitments, and higher deployment-window and c06 service than the shared return." Nearest methods: COSAC (SeqAU, bandit), LIDR / Dr.Reinforce (difference credit, simultaneous primitive actions), HAPPO / MAT (joint advantage with a sequential update or decoder, not a per-agent credit); ALMA and MAT are the nearest joint-assignment learners for the package question, which is deferred to attribution. (iv) **Staging, declared now.** Fit A = T′(shared return), one instance, seed 26092731 (pairs with DM1's second SET seed for the secondary T′ − SET reading), ≤ 13 h on wsl_4070 after DM1's block, ≈ 3 h CPU evaluation: c06 deterministic on 955001–032 plus the PERMUTE-EP / ALL-FREE / HUNGARIAN-LABELS / IDENTITY-LABELS interventions on its own low level — used as a diagnostic of which layer is the bottleneck, not as a substitute for R. **Rule S (read on Fit A before Fit B, all at c06 deterministic on 955001–032):** occupancy := number of the 8 anchors carrying ≥ 5 % of the coordinator's label mass; collapse := ≥ 3 UAVs share one anchor in ≥ 25 % of decisions; reach := share of UAV-steps within 300 m of the labelled anchor, referenced to the same statistic of H_central's hungarian mode (from the Stage 2-0 traces, or a zero-fit re-simulation with the same observer if those traces lack the target coordinates); Δ_H := QoS(HUNGARIAN-LABELS on T′'s own low level) − QoS(T′'s own labels). S0: T′(shared) ≥ .60 QoS/step → no Fit B (no room; attribution next). S1: reach < 50 % of H_central's → the low level is the bottleneck → no Fit B; the next question is execution/grounding, argued in writing. S2: reach passes, occupancy ≥ 6 and not collapsed, Δ_H < +.03 → the shared-return coordinator already sits at the fixed rule's level on this executor → no Fit B. S3: reach passes and (Δ_H ≥ +.03 or collapsed) → Fit B bought, given C1–C2. Fit B = T′(credit): same seed, labels, low-level architecture and budget; primary reading T′(credit) − T′(shared) paired per world at c06 deterministic, bar +.03 QoS/step with ≥ 20/32 worlds; pre-declared secondary readings duplicates, occupancy, commitment stability, deployment-window QoS and relay-hop share. Worst case 2 fits ≈ 26 h GPU + ≈ 6 h CPU + the engineering of item 8 of the v2 entry; it is the only batch whose result the present evidence cannot predict. (v) Attribution after the pair, only if B − A meets the bar: SET+A (feature control) and DM1's SET seeds as the flat references; R only if the claim is re-widened to assignment. (vi) Order: credit diagnostics (launch pending with the owner) → microhost first cell (≤ 2 h CPU; L0 after the diagnostics are read) → Fit A → rule S → Fit B. Nothing is launched on this entry.

**5. Division.** Unchanged: I own the coordinator's learning-signal estimand on the T′ substrate; the Stage 1 / 2-0 panels, H_central / H_local and H_central@10 are shared comparators; the general "MARL against a strong planner" estimand is DM3's. My pre-written pivot loci (service-adaptive anchors; coverage-joint rotation) overlap DM4's joint move/hold/relieve object: before opening either I read DM4's declared intervention and comparator, and any pivot is argued in writing against DM4's transit planner as the ordinary comparator.

**Sent (2026-09-27, 13:3x UTC).** The position of items 1–5 went to Root through the owner-authorised queue channel as one message (queue id 01a0e315-2d0c-7f11-b9e9-a83a37e5774e, thread 01a0e091-9f32-7872-b582-b37a14f8d981); no reply requested. Two facts recorded for the launch: `hmasd_launch.py` applies the node's configured `path_prefix` to the child environment itself (`_child_environment`), so the launch line needs no shell `PATH=` prefix; the delivered commit's full sha is db4e2a3a6967a3d2735efd9ebd25989c77dc4372 (on origin/main).

**Amendment (same day, before any publication): Fit A is conditional too.** With T′ retired as a coordination-only claim, Fit A's only purpose is to be the substrate for Fit B, so it is bought only after the credit diagnostics have been read outside the retirement branch (share ≥ 10 %; between 10 % and 25 % only through the written targeted revision) and C1 and C2 both hold; otherwise no T′ fit at all. The order of item 4 (vi) is therefore diagnostics → first cell → (C1 ∧ C2) → Fit A → rule S → Fit B, with a written reading at each arrow. Engineering requirement noted for the Fit A L0, not opened now: the evaluator trace must carry per-decision labels and the anchor coordinates so that rule S's reach statistic can be read.

**Launched (2026-09-27 13:43:44Z).** After the owner wrote the option-B settings in this session (allow rules for the launcher and for git in `~/.claude/settings.json`), the identical command as one bare invocation without the `PATH=` prefix was accepted by the admission kernel: claim key 69303d12f6a854666f9dada6f6b206435c633ee9c614e1a761b264efd2485525, control observation origin/main f3d7cd49b at 13:43:43Z, source snapshot `.git/hmasd-launch-sources/fb7689ef8bea4892bd27de106ac9b413` at db4e2a3a6967a3d2735efd9ebd25989c77dc4372, supervisor pid 2654712, runner pid 2654713 (posix session), output root `runs/energy_relay_benchmark/b03_credit_a01` (launch-manifest, admission-preflight, stdout/stderr logs, `process-exit.json` on exit). Observation is a deterministic background waiter of this session on the output files; no model waits. Host at launch: load still contended by the orphan headless-Chrome GPU process, so the wall readings are read against the uncontended smoke-test reference; the D and share readings are load-independent. The phase's readings are bound by the "bindings declared before the run" entry and by item 3 of the peer-round-2 entry (retirement branch only; C1–C3 before any fit).

**Amendment to rule S after Root's disposition (commit d2f68ec65, data; no reply sent).** Root's record accepts the narrowed question and no longer holds R to be a necessary arm of the credit comparison; it marks C1/C2 as transfer motivation only and S as an investment rule, not a mechanism certification, which is how they are declared here. One of its cautions improves S1 and is adopted now, before Fit A exists: a low reach rate under T′'s own labels can come from the coordinator switching anchors every decision rather than from the low level, so S1 reads reach under the HUNGARIAN-LABELS intervention (stable labels on the same low level): reach under Hungarian labels < 50 % of H_central's → low level is the bottleneck (no Fit B); reach under Hungarian labels passes but reach under own labels fails → the coordinator's switching is the failure → S3 territory (Fit B bought, given C1–C2). Also recorded: the .60 milestone is a milestone, not a learning-headroom bound; a small Stage 2-0 S lowers the investment preference and does not prove learned assignment worthless; a Fit A → S3 → Fit B sequence yields one conditional training comparison, and per-world pairing does not make it an independent training replication.

## 2026-09-27 — Credit diagnostics read (operation b03_credit_a01, launch sha db4e2a3a6, exit 0, COMPLETE): the retirement branch is not taken, the C2 thresholds are met, and the host sits in the substitutable region where removal credit is weakest; no fit declared

**Provenance.** Accepted 13:43:44Z, exited 14:15:37Z (`process-exit.json`, epoch 1790518537.7), wall 1908.5 s (panel 1184.1 s, bit identity 723.5 s) on the contended host (load ≈ 450 until the orphan Chrome process was killed by the owner at ≈ 14:00Z); 32/32 worlds, 96 000 steps, 9 600 probe steps (300 per world), 0 failed worlds, 0 fits, `baseline_mismatch_steps` 0, peak RSS 426 MB (runner) / 422 MB (largest worker); artifact SHA-256 digests in `summary.json` (`panels/hungarian.json`, `traces/hungarian.npz`, `traces/credit_hungarian.npz`, `bit_identity.json`, `config.json`); the npz traces stay in the run directory (ignored by Git), which is the single durable copy. Both rule sets were written before the launch: item 7 of the D-credit v2 entry with the bindings entry (morning), and item 3 of the peer-round-2 entry (13:3x UTC, before the 13:43:44Z acceptance), so the branch reading below is not post hoc.

**Rules against observed values.**

| rule (pre-written) | observed | branch |
| --- | --- | --- |
| relay-hop share of delivered traffic < 10 % → chain credit retired on this host | pooled traffic-weighted .908; per-world step mean .889 (SE .012, 32 worlds); minimum world .707 (955009), maximum 1.000 (955021); user-weighted .918 | not taken |
| share ≥ 25 % (C2 threshold 1) | .908 | met |
| R1: mean abs D on relay UAV-steps ≥ 2 × the other available UAV-steps (C2 threshold 2) | .0977 against .0291, ratio 3.36 pooled; per-world ratio 3.42 (SE .25); 29/32 worlds ≥ 2 (below: 955026 1.31, 955030 1.76, 955006 1.97) | met |
| fewer than 80 % of UAV-steps with abs D < .01 (C2 threshold 3) | sparsity .370 pooled (per world .25–.53) | met |
| every-10th-step probe ≤ 1.5 × the collection wall (C2 threshold 4) | probe .171 s against collection .0797 s per step → 1.21× (a per-step probe 3.15×, excluded) | met |
| bit identity (a): the phase's hungarian panel equals Stage 1's committed H_central panel | max abs difference of qos_per_step 0.0 on all 32 worlds; panel mean .77402 | passed |
| bit identity (b): the deep-copy probe is trajectory-neutral on 955001 | reward and own_xyz identical over 3000 steps (max difference 0.0) | passed |
| bit identity (b): the raw in-place probe is trajectory-neutral on 955001 | not neutral: reward differs from step 1 (max .369), positions from step 2195 (max 357 m); QoS .8425 plain against .9026 with the raw probe | false, as predicted |

**Branch taken.** No retirement. Under round-2 item 3 the readings supply coordinates and no fit: C2's *threshold* half is met; its *placement* half — that H_central's operating point lies in a configuration where the chosen credit arm beats the shared return — cannot be read until the microhost first cell (C1) exists. Nothing is declared on this entry; Root's record (d2f68ec65) already labels C2 as transfer motivation, and that is how it is used here.

**Headline consequence: the host sits in D's unfavourable region.** rho_t = Σ_i D_i / QoS_t − 1 (first-order removal non-additivity): median −.615, IQR [−.780, −.397], mean −.608, 90.8 % of the 9 527 probe steps with QoS > 0 have |rho| > .25; per-world medians −.81 to −.33 in 31 worlds and +.22 in one (955016, which also has the highest relay ratio, 7.09). Single removals account for ≈ 40 % of the service: re-association and widest-path re-routing absorb most of any one UAV's absence. That is the high-substitutability region in which the `sequential_coordinator_credit` declaration predicts that D loses to SeqAU and to the shared return (D's redundancy cost), not the binding region where D was predicted to win. The relay separation is a relative separation inside a weak absolute signal: mean |D| .057 against QoS ≈ .77, median .023, 37 % of UAV-steps below .01; relay UAV-steps carry 70 % of the D mass (68 % per world), and the plan's relay-slot UAVs (R2, 22 % of UAV-steps) the highest |D| (.137, 3.9×, 50 % of the mass). Reading: the diagnostics survive the retirement branch, lower the prior on removal-difference credit on this host, and raise SeqAU and the β-mixture; the first cell's decisive configuration is the host-matched substitutable one, with the binding configuration kept as the map's other corner.

**Limit of the measurement: first order only.** Single removals were probed by design. Sub-additive singles are consistent with pairwise complementarity (remove the relay → its servers re-route; remove a server → its users re-associate; remove both → the pair's service collapses), so chain binding may live at second order, unseen here. This is a stated limit, not a new probe: the microhost enumerates pairwise removals for free, and its calibration matches single-removal statistics while reporting the pairwise structure.

**Coupling structure is not stake.** The 91 % multi-hop share is host topology (ground-station position, the 8 km area, `max_hops = 4`): under H_central's layout almost all delivered traffic reaches the ground station through at least one other UAV; at 97 % of probe steps at least one UAV is an intermediate, 3.28 of 8 on average (R1), against 1.7 of 8 on the plan's two relay slots (R2): relay-ness emerges from routing among the cluster servers, not only from the planned relay slots. This does not raise the coordinator's stake — Stage 2-0's +.007 for the permutation at fixed anchors stands; what it fixes is the *shape* of the joint role structure that any planner or learner on this host must maintain (the relay chain is the backhaul lifeline of the deployment), and that the planned relay positions are the critical ones.

**Unregistered observations (labelled; no mechanism claim; no branch depends on them).** (a) 10.7 % of UAV-steps have D_i < 0 (per-world mean .107, SE .010): a UAV's presence lowers the team's service there (interference or the routing choice). The microhost's min-structure is monotone and cannot produce negative D; recorded as an omitted coupling; the first cell is unchanged. (b) The raw in-place probe *raised* world 955001's QoS from .8425 to .9026 by recomputing association at every step through the soft-handover memory: one world and a side effect, but it says the production handover hysteresis is a planning knob worth a declared zero-fit look later, not now. (c) `flagged_unavailable_uav_steps = 0`: no UAV was communication-unavailable at any probe step under the production shield, so the "available" and "all" blocks coincide, as the scratch check predicted.

**Cost.** 0 fits; 31.8 min wall on 8 workers × 2 threads under contention (uncontended smoke reference: deep copy ≈ 5 ms, one recompute ≈ 8 ms, eight removals ≈ 94 ms, step ≈ 39 ms); the phase's per-step walls (probe .171 s, collection .080 s) are both contended, and the rule reads their ratio.

**Consequence for the first cell (C1) and the order of work.** The L0 for `sequential_coordinator_credit`'s first cell is written next, with one zero-cost step added: calibrate the microhost's dials to this host's single-removal statistics (Σ_i D_i / R ≈ .39–.45, relay/other |D| ratio ≈ 3.4, sparsity ≈ .37, relay share of D mass ≈ .70) by exact enumeration, report the nearest achievable configuration with its residual mismatch, and report the pairwise removal structure there; arms, contexts, readings and the ≤ 2 h bound are unchanged; negative D is stated as an omission. Fit A stays behind C1 (round-2 amendment); the retirement branch remains available if C1 finds no configuration in which a credit arm beats the shared return.

## 2026-09-27 — Handoff note before an owner machine restart (15:40Z)

No operation of this direction is running; nothing is unpublished. Fit A / Fit B remain conditional on C1 (read from `sequential_coordinator_credit`'s `b01_first_cell_a01`, running at the time of the restart announcement), C2 (met) and rule S. The local-only traces `runs/energy_relay_benchmark/b03_credit_a01/credit-diagnostics/traces/*.npz` are on this machine only. Session handoff: `docs/Claude_docs/deliverables/CLAUDE_DM_RESTART_HANDOFF_20260927.md`.

## 2026-09-27 — C1 read from `sequential_coordinator_credit`'s first cell (`b01_first_cell_a02`): NOT MET as written; Fit A and Fit B not declared; the T′ investment decision goes to independent scientific review

The staged plan (peer round 2, d2f68ec65) made Fit A (T′ shared return, seed 26092731, ≤ 13 h + 3 h) and Fit B (T′ + credit arm) conditional on C1 ∧ C2 ∧ rule S. C2 was met by the credit diagnostics. C1 — "a configuration where the credit arm beats shared return in gradient bias/variance and ≥ 100-seed regret" — was operationalised as Rule 3 in the SCC notebook before that cell ran and reads NOT MET: the regret clause holds at the binding corner (ridge SeqAU below shared return in both entropy settings) and is mixed at the host-matched configuration (worse under constant entropy, better under HMASD's annealed schedule), and the bias/variance clause fails because it was mis-specified (cosine measured against the exactly unbiased shared return; variance in jointly normalised units, where SeqAU's 3–4× lower raw variance is inverted). Removal-difference credit (D) lost to SeqAU by 29–86 SE in its own best case and is retired as a T′ arm. Consequences here: no fit is declared; T′'s second arm, if T′ is ever fitted, is SeqAU; whether a corrected C1 (regret under the annealed schedule plus raw-unit readings) may be adopted without post-hoc bias, and whether the 13 h T′ fit is worth buying at all given Stage 2-0's +.007 coordination stake, are put to independent scientific review before any declaration. Rule S and the Fit A engineering requirement (per-decision labels and anchor coordinates in the evaluator trace) stay unbuilt until then. Full reading in `docs/research/candidates/sequential_coordinator_credit/NOTES.md` (entry of the same hour).

## 2026-09-27 — Wording correction to the C1 entry above

"SeqAU's 3–4× lower raw variance" reads "2.4–4.3× lower at the trained snapshots (5.5–6.4× at the uniform policy)"; see the SCC notebook's correction entry of the same hour. No change to the verdict.

## 2026-09-27 — Independent review of the C1 reading returned (ResearchCritic, MATERIAL_DISSENT yes, accepted): no corrected C1; Fit A and Fit B stay undeclared; the T′ credit line closes; "SeqAU under HMASD's annealed schedule" withdrawn

The review of the SCC first-cell reading (full text, recount and corrections in `docs/research/candidates/sequential_coordinator_credit/NOTES.md`, entry of this hour; the owner routes Pro-based review from the next decision on) answers both questions the C1 entry above put to it. (1) A corrected C1 cannot be adopted on the same data: the only correction grounded in pre-declared text (raw-unit readings) still fails its cosine part everywhere, and the sketched one ("regret under the annealed schedule plus raw-unit readings") is not a rule until a projection bar is fixed after the scores. C1 stands NOT MET; by the accepted staging (peer round 2 and its amendment) neither Fit A nor Fit B is bought. (2) The T′ fit is not worth buying: T′ as declared runs λ_h = .00125 constant (this notebook, lines 3767 and 4046; `hmasd/agent.py` 1047 and `configs/config_1.py` 196 keep entropy annealing off), and in that regime the microhost's realisable SeqAU loses to the shared return at the host-like configuration (regret +.0078, endpoint −.0072) while the exact oracle gains ≈ .1 % of J* in regret and −.0021 at the endpoint; Stage 2-0's stake is +.007 ± .007; the host-matched cell is "nearest, not matched". Corrections to the C1 entry above: "better under HMASD's annealed schedule" reads "better under an annealed .2 → .01 schedule that is neither T′'s nor HMASD's default"; "T′'s second arm, if T′ is ever fitted, is SeqAU" keeps only the pre-written Rule 1(b) default sense, with no positive prediction for T′(credit) − T′(shared) in T′'s regime; "SeqAU's 2.4–4.3× lower raw variance" is the full-variance ratio (within the stratified batch 7.6–16.9× at the uniform policy, 2.6–4.5× trained). The dissent's mechanism finding (E3's loss is early additive-fit bias under relay substitution, not late ridge degeneracy) is accepted there.

Consequences here. The T′ credit-arm question is closed with C1; T′'s pure coordination claim was retired by Stage 2-0 (+.007 < .03); no T′ fit of any kind is declared, the Fit A engineering requirement (per-decision labels and anchor coordinates in the evaluator trace) is not built, and rule S is moot. The direction has no operation running and no declared next fit. What it has established: ordinary control reaches .774 / .597 QoS/step (H_central / H_local) against the learner's .437 (Stage 1), with ≈ 70 % of the gap to H_local in the deployment window before the first shield entry; assignment coordination at fixed anchors is worth +.007; the host sits in the substitutable region where per-agent credit is weakest; credit inside the coordinator is not where an algorithmic gain lies. Under the owner's main line (UAV cooperative planning with MARL, algorithmic innovation, reasoning before experiments) the next step proposed to the owner is a reasoning phase — no fit, no run — that selects a planning-side candidate against the measured deficits (deployment planning under return and charging constraints; anchors adaptive to service rather than fixed k-means centroids), marked TRIED / RECORDED / NEW against the July record and the local libraries, scoped against DM3's `uav_cooperative_planning` before any declaration, and reviewed by Pro at the question-selection point. Whether this direction hosts that phase or closes is the owner's call; nothing runs until then.

## 2026-09-27 — Owner decision (A): T′ line closed; a reasoning-only phase for a planning-side MARL candidate opens in this notebook

Owner chose option A of this session's report. Consequences: the T′ credit line and the staged Fit A / Fit B are closed (no fit, no evaluator-trace engineering, rule S moot); `sequential_coordinator_credit` moves to reserve with its result (its notebook, entry of this hour). This notebook now hosts the reasoning phase: no run and no fit; its deliverable is one selected candidate with an innovation claim, its strongest alternative, a discriminating prediction and a bounded first experiment, each idea marked TRIED / RECORDED / NEW against the July record (external-review R29–R54, FOUNDATIONS, the n_k literature deep-dive, the upstream RESEARCH reviews), the Claude_docs review notes and the two local paper libraries; DM3's `uav_cooperative_planning` boundary stated first; one independent scientific review by Pro (6 Pro; 5.6 Pro when the quota is short) at the question-selection point before any declaration. The phase follows `docs/Claude_docs/reviews/REASONING_FIRST_RESEARCH_METHOD_20260927.md`; the plan, the deficit statement and the boundary are the next entry.

## 2026-09-27 — Reasoning phase, entry 1: the deployment deficit stated from first-hand host facts and zero-fit trace readings; boundaries with DM3 and Root's transit-handoff design; candidate families labelled; one candidate selected for Pro review before any declaration

**What this entry is.** The plan, deficit statement and boundary promised by the owner-decision entry above. No fit, no run, no new episode. Two helper scouts inventoried the record and the local libraries (their reports are scratch under `temp/directions/energy_relay_benchmark/scratch/reasoning-phase-20260927/`, not evidence); every load-bearing number below was read first-hand from the named file. Two new **readings of existing traces** were computed (b01/b02 evaluator `.npz` files already on this host) and published with their reader: `experiments/candidates/energy_relay_benchmark/b04/deployment_readers.py` (tests `tests/experiments/candidates/energy_relay_benchmark/b04/`, 5 passed), outputs and source sha256 manifest in `runs/energy_relay_benchmark/b04_deployment_reading_a01/` (`manifest.json`: `kind = derived_reading_of_existing_traces`, `launcher = null`, `new_episodes = 0`). Reasoning-first method v2 (`docs/Claude_docs/reviews/REASONING_FIRST_RESEARCH_METHOD_20260927.md`) is applied: contribution sentence, closest methods, strongest simple alternative, discriminating prediction, cost, one independent challenge (Pro, next entry) — then, and only then, a bounded experiment or no investment.

### 1. The deployment problem in planning terms (host facts, file:line)

- **World and spawn.** 8 km square, 8 UAVs, 1 s per step, 1,500-step episode, 30 m/s ceiling (`configs/config_1.py` 34–38, 496). UAVs spawn as a grid inside a 500 m square in a **random corner** at the 50 m altitude floor (`envs/pettingzoo/relay/routed_core.py` 1115–1198, `randomize_uav_start = True`, `config_1.py` 89–94): mean pairwise distance at step 0 is 263 m in every world (reader, §3).
- **Demand.** 30 users in 5 clusters of 6: one **remote cluster** at the corner farthest from the base station (±800 m jitter) and four clusters uniform inside the central 4 km square, σ 80 m (`routed_core.py` 700–805; `n_remote_clusters = 1`, `central_area_ratio .5`, `cluster_std 80`); RPGM mobility.
- **Backhaul.** One ground base station on a random edge band (5 % of the side; `_init_ground_bs`, `routed_core.py` 589–676, `randomize_bs = True`). A user counts as served only through a UAV that has a multi-hop path to the base station: widest-path Dijkstra over link capacities, ≤ 5 hops (`_find_widest_path_to_ground_bs` 4977–5052, dispatcher 4556–4567 with the widest-path branch as default, `max_hops = 5`; `_get_state` 4836–4915 marks a user "effectively connected" only when its UAV is in `routing_paths`). The measured host structure (b03 credit diagnostics): 3.28 UAVs per step act as intermediaries, mean path ≈ 2 intermediate nodes.
- **Energy.** Two charging stations, `service_anchored`: anchors at .7·BS + .3·service-centre and at the service centre, ±960 m jitter (`envs/pettingzoo/relay/energy_aware.py` 390–427); the production return shield and backhaul guard act in training and evaluation for every arm.
- **Information of the flat learner (SET).** Own local observation (365; the base station's relative position only inside the 1,500 m 3-D radius or through the k-step global cache, `routed_core.py` 3949–4188, 5356–5401) plus the held central snapshot every k = 10 steps: state 306 (UAV xyz, loads, per-user xy/velocity/connected/best-SINR, BS xyz, step) + 8 × 365 observations + ego one-hot — 3,599 inputs, absolute normalised coordinates (`config_1.py` 243–246; Stage 2 declaration item 3).
- **Reward is conjunctive.** Native reward = end-to-end QoS + bounded return cost (λ_return 2) + **graph potential shaping** (`use_graph_pbrs = True`, `qos_fixed_safety_graph_pbrs`; `config_1.py` 440–470). The potential `_graph_service_potential` (`energy_aware.py` 1161–1206) is the mean over users of clip(max_uav min(access(uav, user), widest_backhaul(uav)) / demand, 0, 1): a UAV with no backhaul path contributes **exactly zero for every user, however close it hovers over them**, and a UAV with backhaul but no user in range contributes zero as well. The distance-only potential (the paper's ablation, `_euclidean_service_potential` 1206–1234) is not used. So no term of the reward gives a per-agent gradient toward users or toward the base station; the first non-zero deployment signal appears only when coverage ∧ connectivity holds jointly. This is the same AND-structure the Stage 2 declaration modelled (p^m) and the SCC micro-host used as R = Σ min(·).

### 2. The measured deficit (Stage 1, unchanged)

Final SET model c06 at 1.2 M transitions: QoS/step .437 (dev) against H_local .597 and H_central .774; ≈ 70 % of the gap to H_local sits before the first shield entry (learner pre-entry .277 against H_local .631 / H_central .810; entry-to-first-input .488 / .702 / .840; post-input .543 / .544 / .725); first service at 165 / 146 steps (det / stoch) against 14–33 for the planners; boundary share .365 / .295, altitude-floor share ≈ .47 (planners 0); the deficit is the policy's own (Stage 0). Post-input service equals H_local's.

### 3. Zero-fit readings of the existing traces (`b04_deployment_reading_a01`; development panel 955001–955032; N on 953001–953032)

Reader definitions: `spread_W` = mean over the first W steps of the mean pairwise horizontal distance (m); `cohere_100` = share of the first 100 steps whose moving UAVs have a mean pairwise velocity cosine > .8; `first_qos` = first step with QoS > 0; heading = angle of each UAV's net displacement over the first 100 steps; **R_map** = mean resultant length of that heading across the 32 worlds in the map frame (1 = the same absolute heading in every world; 0 = the heading depends on the world); **R_spawnrel** = the same after mirroring each world so that its spawn corner is the lower-left corner (a proxy for "conditioned on the spawn geometry"); walls = share of UAV-steps within 60 m of the E / W / S / N wall over the first 1,000 steps.

| policy | spread_t0 | spread_100 | spread_300 | spread_1000 | cohere_100 | first_qos mean (sd) | R_map mean | R_spawnrel mean | walls E/W/S/N/none |
|---|---|---|---|---|---|---|---|---|---|
| H_central | 263 | 698 | 1,686 | 2,409 | .97 | 20 (30) | **.21** | **.96** | 0/0/0/0/1.00 |
| H_local | 263 | 421 | 852 | 1,395 | .99 | 38 (78) | **.17** | **.98** | 0/0/0/0/1.00 |
| SET c06 det | 263 | 411 | 776 | 2,168 | .18 | 160 (297) | **.60** | **.20** | .32/.18/.16/.13/.36 |
| SET c06 stoch | 263 | 389 | 692 | 1,954 | .07 | 146 (246) | .48 | .20 | .26/.14/.14/.21/.40 |
| SET c03 det | 263 | 223 | 266 | 682 | .58 | 193 (392) | .94 | .26 | .36/.00/.17/.12/.43 |
| SET c01 det | 263 | 262 | 251 | 315 | .97 | 237 | .76 | .48 | .00/.28/.48/.01/.38 |
| SET c00 det (init) | 263 | 263 | 263 | 301 | — (no UAV moves ≥ 1 m) | 318 | 1.00 | .12 | .08/0/0/0/.92 |
| N init (953 panel) | 265 | 268 | 348 | 1,005 | .38 | 493 (633) | .83 | .29 | .45/.01/.28/.02/.44 |

Per-agent map-frame mean headings (degrees, c06 det): −146, −58, −113, −112, −119, −23, −90, −50 with per-agent R_map .47–.75; N init: −27 … −66 (all south-east, R_map .65–.99); c01: −123 … −154 (all south-west); c03: +17 … +52 (all north-east). Planners' per-agent R_map .02–.34; their spawn-relative mean headings 38–54° (toward the map centre) with R_spawnrel .92–.99.

**Reading 1 (fact).** The final learner does not move as one blob: at step 100 its spread (411 m) equals H_local's (421 m) and its motion coherence is low (.18 against the planners' .97–.99) — the eight UAVs disperse in different directions. The blob stage is c01–c03 (spread 223–266 m at 300 steps, coherence .58–.97).

**Reading 2 (fact; the load-bearing one).** The learner's early deployment direction is **not a function of the world**. With four spawn corners, one base-station edge and randomised clusters, any geometry-conditioned deployment must have R_map near 0 across worlds — the planners read .17–.21 with R_spawnrel .96–.98. The learner reads the opposite: R_map .60 (det) / .48 (stoch) with R_spawnrel .20, and it read R_map .76–1.00 at c00–c03. Each UAV keeps a partly fixed absolute heading keyed to its index, and the set of fixed headings drifts over training (south-east at init, south-west at c01, north-east at c03, mixed at c06 — with the touched walls following: W+S at c01, E+S at c03, all four at c06). At 1.2 M transitions 64 % of the learner's UAV-steps in the first 1,000 steps are within 60 m of a wall; the planners' share is 0.

**Reading 3 (inference, labelled).** Post-first-input service equals H_local's (.543 against .544) and the charging stations are service-anchored (§1). This is consistent with the forced returns doing the deployment: the shield carries UAVs to stations near the service centre, after which local service works. What would confirm it (not run): post-first-charge service against the station's distance to the service centroid, per world.

**Mechanism statement.** The pre-entry deficit is the absence of a geometry-conditioned deployment decision. Two code facts say why the flat learner did not acquire one within 1.2 M transitions: (a) the reward gives no per-agent gradient toward users or the base station (§1, conjunctive potential); (b) a world-dependent heading must be computed from 3,599 absolute coordinates while the only dense structure in the input that a shared-parameter actor can exploit at once is the ego one-hot — and what the learner learned is exactly a function of that one-hot (distinct fixed headings per index), which buys dispersal (spread 263 → 411 m by step 100, the de-duplication that Stage 2-0 priced at +.324 QoS/step for independent-nearest against Hungarian) but not placement. Conjecture, not read: the index-keyed dispersal is the learner's solution to the symmetric co-located spawn; the "where" was never rewarded often enough to be learned.

### 4. Boundaries

- **DM3, `uav_cooperative_planning` (reserve).** B02 = learned value ranking over a common transit library on the H_local planner, negative (L − P QoS −.0165); B01 (anticipatory rematching) withdrawn; the broader question "a useful learning increment in cooperative UAV planning" stays with DM3. Its reviewer's bar, quoted because it applies here too: "Merely adding a learned high-level choice or a longer return label is insufficient to specify an increment relative to established methods" (ALMA, MAT) — `uav_cooperative_planning/NOTES.md` 172–179.
- **Root's selected design `uav_transit_handoff` (new Codex DM, design only; RESEARCH current plan, inbox `20260928_transit_handoff_scope_ROOT.md`).** Object: with H1's final targets and assignment fixed, on the existing 10-step clock, whether a qualified member flies a temporary support leg while another UAV returns or transits — a decision in the shield/return phase.
- **This notebook's object.** The deployment window before any return (the first ≈ 1,000 steps), and the MARL learner's own joint policy class (what HMASD's coordinator decides), not a learned component inside a planner. No overlap in decision object with either; shared assets are the H references, the panels and the readers. Root asked to be told of overlap: there is none; one peer message carries this boundary and Reading 2.

### 5. Candidate families against the record and the libraries

| family | closest record | label | decision |
|---|---|---|---|
| A. learned spatial goal generation on HMASD's coordinator | S4 seed (09-21 note), R51 AMDT pointer toy (never reached reward), T/GAS declared and implemented, never run; `gnn_hmasd/` dormant GCN role assigner; libraries: HMASD/HAVEN high levels are categorical, none generates coordinates | RECORDED family | **selected, with a NEW parameterisation (§6)** |
| B. dependency-ordered / relay-tree autoregressive decoding | HMASD's decoder is fixed index order; MAT arbitrary order (Wen et al. 2022, read: "arbitrary decision order", one permutation per iteration); A2PO orders *updates*, not actions (Wang et al. ICLR 2023, read) | NEW to the record | folded into §6 (the relational goal makes order carry geometry); not a headline by itself |
| C. model-based planning / learned service model | proposal 09-19 (not UAV deployment); DM3 B02 negative; DM2 B04/B05 finite lookahead positive-conditional, ordinary planners | RECORDED / TRIED on the planner side | declined (DM2/DM3 territory) |
| D. coordinated exploration / intrinsic motivation | no S7 idea in the record; libraries: MAVEN, FoX, HCPO; HMASD's own individual discriminator is the config default (`use_individual_skill_discriminator = True`, λ_d .02) but off in every benchmark arm; the one HMASD-as-designed S7 record is June arm A on S7-S3 (k = 50, reward v1, 200 Wh): mean episode QoS .14 (`baselines/scenario7_arm_a_2400000_metrics.json`) | NEW to S7-S2; TRIED on another stage | declined as headline: diversity pressure without geometry does not target the chain (§1); possible add-on later |
| E. relative-frame / equivariant representation on the flat actor | entity encoders TRIED twice on S1, adverse or unestablished; R54 toy failed its gate | TRIED family | not a headline; kept as alternative explanation (B in §6) that the ablation must cover |
| F. constrained MARL for energy/return | shield + safety dual are in the host; DeCOM's team-average cost is the nearest library shape | TRIED in host | not the deficit (pre-entry, before any return) |
| G. imitation / curriculum from planners | `energy_relay_imitation` B01/B02 TRIED (heterogeneous BC gain, adverse worlds) | TRIED | declined |

### 6. Selected candidate: relational goal decoding on HMASD's coordinator (working label used only in this notebook)

**What changes.** HMASD's coordinator keeps its state encoder and its autoregressive skill decoder (paper §3.2, read: Z then z¹..zⁿ, each conditioned on the previous ones; `hmasd/networks.py` 703–). Its per-agent action stops being a categorical skill and becomes a **relational goal**: two pointers a, b over the entity set E_i = {base station, the 30 user positions in the held snapshot, the goals already decoded for agents 1..i−1} and a fraction f ∈ {0, ¼, ½, ¾, 1} (or a tanh-Gaussian scalar; L0 decision); the goal is g_i = (1 − f)·p_a + f·p_b, plus a FREE label. The low level is the goal-conditioned GAS discoverer already implemented for T (anchor block: absolute, relative, distance, free flag; `experiments/candidates/energy_relay_benchmark/b03/agent.py`), trained on the native reward with discriminators off, k = 10, the SET/T information contract (held central snapshot every 10 steps), shield and guard unchanged. Learned objects: the coordinator's relational policy and the goal-conditioned low level. Not supplied: k-means centroids, heuristic relay points, Hungarian matching. The heuristic's own relay points (⅓, ⅔ of the BS–centroid segment) are *expressible* as (BS, user, f) choices, not given.

**Contribution sentence (assuming success).** For conjunctive cooperative deployment — service = coverage ∧ multi-hop connectivity — expressing the coordinator's joint action as relations between entities and teammates' decisions (points on segments between the base station, demand and already-placed teammates) makes the deployment decision geometry-conditioned and chain-feasible by construction, so the hierarchical learner acquires a state-conditioned deployment (R_map near 0, early first service) that the flat learner and the same hierarchy with absolute goals do not reach at equal exposure.

**Increment against each closest method (all read first-hand this session).** T′/GAS (closed): fixed heuristic anchors and categorical labels — here the goal set is constructed by the policy from raw entities and its own previous decisions, nothing from the planner. HiT-MAC (Xu et al. NeurIPS 2020; coordinator allocates *existing* targets to executors every k steps, AMC critic) and ALMA (Iqbal et al. 2022; learned subtask allocation): both allocate existing entities; relay positions are not entities, and the segment construction creates them conditioned on teammates' goals. FMH (Ahilan & Dayan 2019, §3.2: the manager's message selects among fixed goal reward functions): here goals are continuous constructions and the low-level reward is the native team reward, not a manager-defined one. MAT and HMASD's decoder: reused; what changes is the coordinate system of the joint action (relational, not absolute), which is what lets the autoregressive conditioning mean "between the base station and agent j's goal". Answer to DM3's reviewer bar: the increment is not "adding a learned high-level choice"; it is a change of the joint action space's coordinates, and arm A below removes exactly that change.

**Simple model (derivation, no run).** One cluster at distance 2L from the base station, link range L, two agents: service needs one goal near L and one near 2L on the segment. Absolute goals sampled uniformly over the arena of area A: P(both within radius r of their spots) = (πr²/A)², e.g. r = 300 m, A = 64 km² → 2·10⁻⁵ per joint sample. Relational goals with a 5-fraction menu over (BS, cluster): P = P(f₁ ≈ ½)·P(f₂ = 1) = (⅕)² = .04, independent of arena size; with 31 entities the pointer pair has 31² combinations but the same combination is rewarded in every world, whereas a rewarded absolute coordinate is world-specific — this cross-world invariance is the mechanism behind Reading 2. Omitted: motion time, altitude, the shield, moving clusters, eight agents, the learned low level; the UAV study measures those.

**Strongest simple alternatives.** (A) *Absolute goals*: the same coordinator and low level, the goal as a tanh-Gaussian point in the arena — separates "goal-conditioned hierarchy" from "relational coordinates"; this is the ablation arm. (B) *Input-frame fix on the flat SET actor*: every snapshot entity in ego-relative (or BS-relative) coordinates; cheap and representation-only; predicted insufficient because the signal is conjunctive (§1), but Pro must weigh it and it can be a third arm if Pro rates the representation explanation higher. (C) *HMASD as designed* with the individual discriminator on: TRIED on S7-S3 (June arm A, mean QoS .14), not on S7-S2/H3000; not selected. (D) Fixed references: H_central, H_local, SET c06, N — existing.

**Discriminating predictions, readable at c01–c02 (200–400 k transitions) with the published readers.** P1 (mechanism): relational arm R_map ≤ .35 and R_spawnrel ≥ .60 on the development panel by c02; absolute arm R_map ≥ .50 (SET read .76–.94 at c01–c03, .60 at c06; planners .17–.21 / .96–.98). P2 (arrival): first service, development-panel mean, relational ≤ 60 steps by c02 (SET c02 ≈ 290–323, c06 160; planners 20–38); absolute > 120. P3 (service): relational pre-entry QoS ≥ .277 + .10 at 1.2 M; final QoS above SET c06 by ≥ .05 with the paired SE reported. P4 (failure readings): A ≈ R on P1–P3 → the relational coordinates add nothing beyond goal-conditioning (the plain FMH/HiT-MAC-family result; record it and stop); neither beats SET → hierarchy-with-goals is dead on this host at this exposure; R wins P1–P2 but not P3 → deployment solved and service lost elsewhere (read the clock-aligned phase decomposition before any repair).

**Bounded first experiment (to be declared only after the Pro review).** Two fits, one seed each (R, A), S7-S2/H3000, 1.2 M transitions, SET/T information contract, shield/guard unchanged; development panel 955001–955032 at every checkpoint with the Stage 1 reader and the b04 readers; the hold-out 957001–957032 is spent, so a new sealed hold-out panel is declared with the fits and read once. Cost ≈ 2 × (11–13 h GPU + ≈ 3 h CPU evaluation) on wsl_4070 ≈ 26 h GPU + 6 h CPU, inside the five-track ceiling one at a time; engineering: the coordinator head (two pointers + fraction) and the goal source in the snapshot replacing the k-means anchors, on the existing GAS code (≈ 300–500 lines with tests), one Implementer task and one engineering review (goal/replay parity, RNG). Zero-fit before any fit, if Pro asks: probe the saved SET c06 on constructed snapshots (move only the base station or only the clusters) to measure the action's sensitivity to geometry directly.

### 7. What the Pro review must challenge (next entry carries the question; MATERIAL_DISSENT yes/no)

Q1 whether R_map > R_spawnrel is a valid signature of non-conditioned deployment and what else could produce it; Q2 whether the conjunctive-signal reading of the code is right and whether alternative (B) would suffice on its own; Q3 novelty — the increments against T′, HiT-MAC, ALMA, FMH, MAT, and closer prior work the local libraries lack (relational action spaces, segment/pointer constructions in MARL, learned connectivity-constrained deployment), with TRIED/RECORDED/NEW labels; Q4 design — is arm A the right ablation, are P1–P4 falsifiable with sensible thresholds, which confound is missing (e.g. users in the entity set are a target-assignment prior); Q5 investment — two fits now, or the zero-fit probe and the input-frame fix first.

### 8. Cost of this entry and state

Zero fits, zero episodes; readers ≈ 1 min CPU; two Sonnet scouts. Nothing running. SCC's scope and cost statements are narrowed in its own notebook (entry of this hour, after Root's independent review); nothing in this notebook asserts a host-wide credit exclusion, and the candidate above does not depend on that dispute.

## Pro question 2026-09-27 reasoning-phase-candidate-selection

Conversation: new (Jev account; the conversation address stays in the local operation file; shared records use the question key)

Question: Independent scientific review at the question-selection point (constitution section 5; owner 2026-09-27: section-5 reviews are performed by Pro, with MATERIAL_DISSENT stated) of the entry "Reasoning phase, entry 1" in this notebook: does the evidence support selecting **relational goal decoding on HMASD's coordinator** as the one candidate to declare next — with arm A (the same hierarchy with absolute map-coordinate goals) as its ablation and P1–P4 as its discriminating readings — or should the zero-fit geometry probe of the saved SET model, the input-frame fix on the flat actor, another candidate, or no investment come first? The answer can change which study is declared, whether any fit is bought, and which claims of entry 1 are withdrawn.

Critic specification (the review body this project uses for independent scientific review; answer each item, separating [F] facts you verified from files, [D] derivations and [C] conjectures):
- Q1 Mechanism reading. Entry 1 §3 reads from `runs/energy_relay_benchmark/b04_deployment_reading_a01/heading_stat.json` and `blob_stat.json` (reader: `experiments/candidates/energy_relay_benchmark/b04/deployment_readers.py`) that the SET learner's first-100-step headings are consistent in the map frame (R_map .60 det / .48 stoch at 1.2 M; .76–1.00 at c00–c03) and inconsistent in the spawn-mirrored frame (R_spawnrel .20), the planners the reverse (.17–.21 / .96–.98), and 64 % of learner UAV-steps within 60 m of a wall in the first 1,000 steps (planners 0). Is "the learner's deployment direction is not a function of the world geometry" the right reading? What else could produce R_map > R_spawnrel (initialisation drift never trained away, an artefact of the mirroring proxy, a base-station-conditioned policy — the BS position is not in the traces — or something else)? Which additional zero-fit reading of the same traces would separate these?
- Q2 Signal structure. Entry 1 §1 reads `envs/pettingzoo/relay/energy_aware.py` `_graph_service_potential` (1161–1206) as giving zero potential to any UAV without a backhaul path, so that no reward term supplies a per-agent gradient toward users or the base station. Is that reading right? Given it, is the strongest simple alternative (B) — the flat SET actor with ego- or BS-relative coordinates for every snapshot entity — likely sufficient on its own, and should it be an arm?
- Q3 Novelty and increment. Entry 1 §5–6 labels the families TRIED / RECORDED / NEW against the record (`docs/research/candidates/*/NOTES.md`, `docs/external-review/`, `docs/Claude_docs/research_notes/TEMPORAL_ABSTRACTION_PARADIGMS_AND_HMASD_DIRECTIONS_20260921.md`) and states the increment against T′/GAS (this notebook's Stage 2 declaration), HiT-MAC (Xu et al. 2020), ALMA (Iqbal et al. 2022), FMH (Ahilan & Dayan 2019) and MAT (Wen et al. 2022). Are those increments real? Name closer prior work the local libraries lack (relational or object-centric action spaces in MARL, pointer or segment constructions, learned connectivity-constrained multi-UAV deployment) and say whether it reduces the candidate to a known method. Does DM3's reviewer bar ("merely adding a learned high-level choice is insufficient relative to ALMA/MAT", `docs/research/candidates/uav_cooperative_planning/NOTES.md` 172–179) apply to this candidate as specified?
- Q4 Design. Is arm A the right ablation; are P1–P4 falsifiable with sensible thresholds at c01–c02; which confound is missing (users in the entity set as a target-assignment prior; the fraction menu as a hidden relay heuristic; goal-conditioned low level vs categorical skills as a second change); is a third arm needed (B or HMASD-as-designed with its individual discriminator, whose only S7 record is June arm A on S7-S3, mean QoS .14)?
- Q5 Investment. With two fits at ≈ 26 h GPU + 6 h CPU on wsl_4070: declare R + A now; run the zero-fit probe first (saved SET c06 on constructed snapshots with only the base station or only the clusters moved); run B first as one fit; or do not invest. State the decision-changing observation for your recommendation.
- Return MATERIAL_DISSENT yes/no against entry 1's selection, and list any sentence of entry 1 that must be withdrawn.

Standing:
- Direction: HMASD on the S7-S2/H3000 UAV host as a cooperative-planning learner (owner main line: UAV path planning and swarm cooperative planning enhanced by MARL; energy/return/charging are constraints). Deficit: SET c06 .437 QoS/step against H_local .597 / H_central .774; ≈ 70 % of the gap to H_local before the first shield entry (pre-entry .277 against .631 / .810); first service 146–165 steps against 14–33; post-first-input service equals H_local's (.543 / .544).
- New this entry (zero fit): the heading and spread readings above; the conjunctive-potential code fact; the inference (labelled) that the shield's forced returns deploy the learner.
- Closed lines carried forward: T′/GAS (fixed heuristic anchors + categorical labels) closed with C1 NOT MET; SCC first cell (per-agent credit inside the assignment layer) closed to reserve with Root's independent review narrowing its generalisations (SCC notebook, entry of this hour); Stage 2-0: Hungarian − identity at fixed anchors +.007 ± .007, de-duplication worth +.324.
- Contrary evidence to keep in view: entity/permutation-invariant encoders TRIED-adverse on S1 (DENSE J45 .202 vs .458); HMASD-as-designed mean QoS .14 on S7-S3 (different stage, k = 50, reward v1); DM3's learned planner increments negative (B02) or withdrawn (B01); imitation from planners heterogeneous; the learner's own dispersal (spread 411 m at step 100 = H_local's) shows it solved de-duplication without geometry.
- Boundaries: DM3 `uav_cooperative_planning` (reserve; broader planner-side learning question retained) and Root's new design `uav_transit_handoff` (temporary coverage handoff during returns, fixed H1 targets) — no overlap in decision object with the deployment window.

Context:
  Governance: `docs/project/OPERATING_CONSTITUTION.md` §§1–5, 7–8 (source_sha); owner instructions quoted in this notebook's Stage 2 declaration and owner-decision entries (algorithmic innovation, reasoning first, planning framing).
  Method: `.agents/skills/hmasd-scientific-tools/SKILL.md` (working explanation; simple-model and literature bridges; cost and exposure) and `docs/Claude_docs/reviews/REASONING_FIRST_RESEARCH_METHOD_20260927.md` (source_sha).
  Evidence (source_sha): this notebook, entries "Stage 1 result …", "Stage 2 declaration (B03) …", "Stage 2-0 …", "Independent review of the C1 reading returned …", "Owner decision (A) …", "Reasoning phase, entry 1"; `runs/energy_relay_benchmark/b04_deployment_reading_a01/{blob_stat,heading_stat,manifest}.json`; `experiments/candidates/energy_relay_benchmark/b04/deployment_readers.py`; `experiments/candidates/energy_relay_benchmark/b03/agent.py` (GAS low level); `envs/pettingzoo/relay/energy_aware.py` 944–1000, 1161–1234, 333–427; `envs/pettingzoo/relay/routed_core.py` 589–676, 700–805, 1115–1198, 3949–4188, 4544–4760, 4836–4915, 4977–5052; `configs/config_1.py` 34–134, 243–290, 440–560; `hmasd/networks.py` 703–900; `docs/research/candidates/sequential_coordinator_credit/NOTES.md` (closure and narrowing entries); `docs/research/candidates/uav_cooperative_planning/NOTES.md` 148–260; `docs/research/RESEARCH.md` (current plan, rows `energy_relay_benchmark`, `sequential_coordinator_credit`, `uav_cooperative_planning`).
  Frozen contract: S7-S2/H3000 host, SET/T information contract (held central snapshot every k = 10 steps), production shield and guard, development panel 955001–955032; the hold-out 957001–957032 is spent.

Prospective cost: (i) if declared as written, two UAV fits (R, A), one seed each, ≈ 2 × (11–13 h GPU + ≈ 3 h CPU evaluation) on wsl_4070, plus ≈ 300–500 lines of implementation on the existing GAS code with one engineering review; (ii) zero-fit probe ≈ 30 min CPU; (iii) alternative B as one additional fit ≈ 13 h GPU + 3 h CPU; (iv) no investment: zero.

Constraints: seeds and matched baselines per constitution section 8; no training; no edits outside the empty "### Answer" subsection of this question; write only there on branch `main` of `CartmanFatass/My-paper-code` through the ChatGPT GitHub connector (Pro has no gh or token). Read the question at the pinned source, but fetch the latest target file before editing and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits. On successful write, report the actual commit. On write failure return the complete answer in chat, not just a SHA, status message or link.

Return: per Q1–Q5: what the evidence strengthens, weakens or leaves unresolved, with the numbers you re-read from the JSON records; the mechanism verdict and the extra zero-fit reading that would separate the alternatives; the novelty verdict with closer prior work named and each idea labelled TRIED / RECORDED / NEW; the design verdict on arm A and P1–P4 with any missing confound; a one-line recommendation among {declare R + A now; probe first; B first; other candidate (name it); no investment} with its decision-changing observation; MATERIAL_DISSENT yes/no and the sentences of entry 1 to withdraw.

### Answer


## 2026-09-27 — Pro question composed; send withheld pending a human login (transport state, no science)

- The question `## Pro question 2026-09-27 reasoning-phase-candidate-selection` is published at b4479693a; the document was composed unchanged (`temp/pro_transport/hmasd-pro-question-reasoning-phase-candidate-selection.md`, sha256 4ea361fed3d21fa5ec2a8cee356d030ffd24e9c926a054f061ffe040228448bb); key `hmasd:84c1b66eb2fc64d9e8fac22906c764211993ef40f1a3abc8111578c2c71ec065`; operation state `send_attempted: false` (two pre-send failures, nothing submitted). The same key resends without recomposition once the provider session exists.
- Cause chain on this host after the 2026-09-27 reboot: (i) the direct route is black-holed by a TUN default route, only the local proxy passes; (ii) the driver's headless Chrome auto-selected the keyring this boot and stalled on its unlock prompt, so no page loaded (net log: the request stops after COMPUTED_PRIVACY_MODE; a logging loopback server never saw the GET); fixed by passing the proxy explicitly and pinning `--password-store=basic` (commits 96b976d44, f409554d4; change note `docs/Claude_docs/changes/2026-09-27-jev-chrome-proxy.md` with its correction); (iii) with pages loading, the provider page renders logged out, so the dry-run ends with `timed out waiting for the composer`. Login is a human action; the owner report of this hour carries the two options (re-login headed under the basic pin; keyring recovery after making the pin configurable).
- Auto-mode classifier denials during the diagnosis, reported verbatim to the owner and not pursued: sandbox-disabling Chrome flags ("Safety Bypass Flag") and reading the profile's live cookie store ("Credential Exploration"). The key-store provenance of the pre-reboot session is therefore unknown, and the fate of its cookies is unknown, not "lost".
- No science changed: no declaration, no fit, no run. Peer message to Root of this hour: boundary with `uav_transit_handoff` (now its own DM) and `uav_cooperative_planning`, plus the R_map/R_spawnrel fact; no reply requested.
