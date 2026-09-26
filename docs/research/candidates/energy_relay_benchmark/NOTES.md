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
