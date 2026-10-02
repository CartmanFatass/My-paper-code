# Sparse-window relay service: a scenario for HMASD under sparse reward, and a toy to check it first (2026-10-02)

Provenance: Claude Code cloud session `session_013LQX44wuT3dfQfhb79KwZB`, branch `claude/inspiring-ritchie-2kj46g`.
Non-direction deliverable under `docs/Claude_docs/` (design advice, not a science card, a contract or a
declaration). The Claude session is paused (owner, 2026-09-30); nothing here is launched on a project
host, no direction is declared and no fit of the project learner is run. The toy in
`docs/Claude_docs/toy_studies/sparse_window_relay/` is standard-library Python run inside this cloud
container with fixed seeds; its readings are in that directory's `RESULTS.md`.

**一句话（中文）**：把"注册用户的周期服务窗口"（`uav_registered_service` 已有）和"只能靠中继链到达的远簇"
（耦合中继宿主已有）组合成一个只在"联合中继链在窗口内被建成并保持"时才付奖励的稀疏任务；这才是 HMASD 的
技能发现机制（判别器内在奖励）被设计出来要解决的探索问题，而项目此前只在稠密几何覆盖上试过它，那里静态规划器
按构造就赢。先用一个毫秒级的 stdlib 玩具环境检验"多样性内在奖励是否提高稀疏奖励的命中率"及其与计数探索、
纯层次结构的区别，再决定是否在真实宿主上花 CPU 小时。

---

## 1. Why this scenario, and what question it asks

HMASD's team and individual skill discriminators pay the policy for making skills distinguishable from
the states they visit. That is an exploration device for sparse-reward cooperative tasks. In this
repository the learner has only been exposed to dense, geometric coverage objectives on the coupled
relay host, where a static-score planner wins by construction and every learner sat at a floor (ten
single-seed fits, about 42 CPU-hours; slot choice b02c at the random floor; distillation at .40 against
a .76 teacher; typed scorers in `typed_joint_skill_decision` B01 below a fixed construction). None of
those results tests the mechanism on the kind of task it was built for.

The repository already holds the two ingredients of a sparse, compositional objective:

- registered users with periodic windows and the user-window hit metric F (`uav_registered_service`:
  64-tick windows in H256, a 400-byte registered map, lawful model-history scheduling O);
- a relay-coupled host where far users are reachable only through a chain of UAVs
  (`coupled_host_joint_skills_stage1`'s `CoupledRelayHost`: six UAVs, 5 km, one centre base station,
  max 3 hops; the coupling condition "allow relay minus no-A2A re-optimisation ≥ .05" held at 5 km).

**Question.** On a UAV-BS service task whose reward is paid only when a joint relay configuration to a
far cluster is formed and held inside a service window, does HMASD's skill discovery reach the sparse
reward more reliably than flat PPO at the same interface and exposure, and more reliably than the same
hierarchy with its discriminator rewards disabled? The ordinary scheduler that knows the schedule is the
ceiling reference; beating it is not the question (a capability question, as the project's B00 stance
states). Three competing explanations are controlled by arms, not by argument: any exploration bonus
would do it (count-based arm); hierarchy and commitment alone do it (no-discriminator arm); the reward
is reachable by chance at this exposure (random and sticky floors).

## 2. Scenario S2-W on the coupled relay host (specification)

Only the objective, the user layout and the schedule features change. Host constants, team size,
decision clock, executor interface and learner configuration stay as in the existing cells, so that the
comparison with the ten dense-reward fits is as clean as a changed objective allows.

| Element | Specification | Source it reuses |
| --- | --- | --- |
| Host | `CoupledRelayHost` with `HOST_CONTRACT_KWARGS` unchanged: 6 UAVs, 50 users, 5 km, base station at the centre (scenario 2's single-BS rule), free space, 23 dBm, min SINR 3 dB, max connections 10, max hops 3, FDMA, H500, max speed 30 m/s, k = 10. | `experiments/candidates/coupled_host_joint_skills_stage1/host.py` |
| User layout (changed, declared) | One near cluster of 10 users around the base station (std 250 m) and four far clusters of 10 users centred near the four corners (about 750 m from each corner, std 250 m, per-world jitter ±150 m). World admission rule: a far cluster must not be servable by any single UAV with a direct base-station link; check with the host's own SINR calculation at world generation, regenerate failing worlds and report the count. | `envs/pettingzoo/uav_env.py` cluster generator, replaced by a fixed layout in the direction's host subclass |
| Registered map and schedule | All 40 far-cluster users are registered; their positions are given to every arm as the 400-byte map convention. The schedule is four windows of 125 ticks covering H500; one far cluster is open per window; the order is a permutation drawn from the world seed and known in advance to every arm. | `experiments/candidates/uav_registered_service/b01/history.py`, `metrics.py` (window bits, gaps) |
| Served condition | The open cluster is served at a tick when at least 8 of its 10 registered users are connected to a UAV that has a routing path to the base station (the C_bh condition restricted to the cluster). | `CoupledRelayHost._compute_reward` bookkeeping (`routing_paths`, `connections`) |
| Sparse reward | Window b pays +1 at the first tick at which the served condition has held for H_hold = 20 consecutive ticks inside the window; at most 4 per episode. Team reward per tick is the sparse term plus w_dense × the existing contract reward, w_dense ∈ {0, .01}; per-agent reward is the team scalar divided by 6, as in scenario 2. | new `_compute_reward` in the direction's host subclass |
| Travel feasibility | Base station to a corner cluster is about 2.5 km, 83 ticks at 30 m/s; plus the 20-tick hold this fits a 125-tick window, and the known schedule allows pre-positioning. Verified by the zero-fit floor stage: the known-window scheduler must satisfy at least 3.5 of 4 windows on the dev worlds, otherwise the window length is raised to 166 ticks (three windows). | zero-fit stage |
| Learner information | The standard observation and state vectors plus schedule features appended to both: open cluster one-hot (5), ticks remaining in the window (scaled), next cluster one-hot (5). Identical for every learned arm and for the scheduler. | `hmasd/agent.py` normalisation handles the extra dimensions |
| Learned arms | (1) HMASD defaults: n_Z = 6, n_z = 6, k = 10, λ_e = 1, λ_D = .05, λ_d = .02, entropy defaults. (1b) HMASD with the discriminator weights raised four-fold (λ_D = .2, λ_d = .08): in the toy the mechanism showed only at this weight in the sparse reward scale (section 3). (2) HMASD with `disable_discriminator_rewards = True` (hierarchy only). (3) Flat SET at the same interface and exposure (the b02/b03 recipe). (4) Optional: flat + count-based bonus on a coarse team configuration, only if the project learner gains that option without touching shared code paths used by other directions. | `configs/config_1.py`, existing cells |
| Zero-fit references | Random slot program; sticky-random (the project's I-style hold); near-camping planner (the frozen planner restricted to the near cluster, the decoy's attractor); O_W, the frozen planner given the schedule, re-planning at each decision for the current or next open cluster with the objective restricted to that cluster's users (pre-positioning). | `planner.py::search_placement`, `menus.py` |
| Worlds | 64 dev worlds for floors and training, 32 fresh hold-out worlds for the reading; common worlds across arms. | `scripts/hmasd_launch.py` admission, direction-owned seeds |

**Exposure and price.** One instance per learned arm at 360k native steps, the b03 exposure that cost
1.79 CPU-h on `local_linux`: four arms (1, 1b, 2, 3) ≈ 7.2 CPU-h, plus floors ≈ .1 CPU-h and the hold-out
evaluation ≈ .3 CPU-h. Under the 10 CPU-h sizing line for the first round. Seeds are added only after an
activation, never to rescue a floor-level instance.

**Pre-declared reading (to be written as a rule in the direction's NOTES before any fit).**

- Primary: windows satisfied per episode on the 32 hold-out worlds (0 to 4), paired across arms on
  common worlds, with per-world signs and descriptive intervals.
- Activation: an arm is active if its mean exceeds the sticky-random floor by at least 1.0 window and is
  at least .5 in absolute terms.
- Mechanism effect: HMASD minus HMASD-without-discriminators ≥ .5 window and at least three standard
  errors, with HMASD also above flat SET. If flat + count-bonus is run and matches HMASD, the effect is
  generic exploration, not skill discovery, and is reported as such.
- Ceiling: O_W, reported, not a bar.
- Also reported: first training episode with any reward; fraction of training episodes with any window;
  chain formations per far cluster; near-cluster occupancy in the w_dense = .01 variant (decoy capture);
  travel and contract reward as secondary consequences.
- Uninformative outcomes and their cost: three floor-level instances close this objective at this
  exposure on this host, with the toy ladder saying which rung (needle or wider access) the host sits on;
  no seeds, epochs or knobs are added to a floor-level instance.

**What each outcome changes.** HMASD active and above the no-discriminator arm: the first HMASD-specific
positive capability in this project, and the right host for a learning curve. Count-bonus matches it:
the project's contribution is a sparse-reward UAV benchmark, not the discriminator. Nothing active: the
objective is too sparse at affordable exposure; the toy rung results then say whether widening the
access range or the hold is the honest next step, and the near-camping and O_W references remain as the
competent ordinary capabilities.

## 3. The toy: SWR, a stdlib gridworld with the same structure

`docs/Claude_docs/toy_studies/sparse_window_relay/swr_toy.py` keeps the structure and drops the physics.

| Scenario element | Toy element |
| --- | --- |
| 5 km arena, base station at the centre | 11 × 11 grid, base station at (5, 5) |
| Four far corner clusters reachable only by relay chains, max 3 hops | Four corner sites; link range 2 cells, access range 1 cell, at most 3 UAV hops. A corner is served only when one UAV holds the single relay cell ((3, 3) for the (0, 0) corner) and another holds a cell adjacent to the corner; three-UAV chains also exist. |
| Four 125-tick windows in H500, one cluster open per window | Five 20-tick windows in T = 120 (sites 0, 1, 2, 3, 0), one site open per window |
| Served for 20 consecutive ticks pays +1 | Served for 5 consecutive ticks pays +1; at most 5 per episode |
| Decoy: w_dense × contract reward | Decoy: +.002 per UAV-tick within one cell of the base station (max 1.44 per episode, comparable to one window) |
| k = 10 decisions, frozen straight-line executor | K = 10 decisions, one-cell-per-tick executor toward a target cell (121 choices per UAV) |
| HMASD coordinator and skills, PPO | Tabular REINFORCE analogs: team skill Z (6) → per-UAV skill z_i (6) → shared target policy; tabular discriminators q(Z | coarse 3 × 3 configuration) and q(z_i | region_i, Z) with the project's λ_D = .05, λ_d = .02 |
| Flat SET | One tabular target policy per UAV conditioned on the open site |
| Count-based bonus arm | β / √n(coarse configuration), β = .1 |
| O_W | Known-window scheduler that sends the two nearest UAVs to the chain cells (ceiling 5/5) |
| Random, sticky, near-camping floors | random, sticky_random (hold w.p. .9), stay; plus region_random, a diagnostic that shows what regional concentration does to the hit rate |

Difficulty ladder (the project's design principle P1/P3: one knob, a curve rather than a bit): access
range 1 (one two-UAV chain per corner, the needle) and access range 2 (wider). Uniform random targets hit
a window in about 2% of episodes at access range 1 (300-episode check), so the reward is sparse but not
unreachable, and the ceiling is 5.

What the toy can say: whether discriminator rewards change the hit rate of a held joint configuration
under sparse reward relative to flat, count-bonus and hierarchy-only exploration, at which rung, and
whether the decoy captures each arm. What it cannot say: anything about radio physics, continuous
control, PPO, the Transformer coordinator or learned low-level skills. A toy positive licenses the
zero-fit floors on the real host; a toy negative at both rungs says the mechanism's exploration story
does not even hold in the abstraction, and the real-host fits should not be bought on that story.

Run: `python3 swr_toy.py --r-access 1 --out results_raccess1.json` (and `--r-access 2`); all seeds fixed;
about 5 ms per episode in CPython 3.11.

**What the toy found (full tables in the toy's `RESULTS.md`; 5,000 episodes, five seeds, five arms, two
decoy settings, two rungs, about 12 minutes per rung).** At the needle rung no arm left the random floor
in 5,000 episodes: the one-chain-per-corner geometry gives a 2% hit rate that REINFORCE over 121-way
policies cannot turn into credit, whatever the exploration device. At the wider rung every arm learns,
and the arms separate: the hierarchy with four-fold discriminator weights activates earliest and in all
five seeds (about 2.0 of 5 windows, the two windows of site 0), the count-bonus arm reaches the same
level later, flat PPO's analog is a little lower and more variable, the hierarchy at the project's default
weights is no better than flat, and the hierarchy without discriminators is the worst and least reliable
arm. Two lessons carry to the real host: the discriminator reward is an exploration device whose effect
depends on its weight relative to the sparse reward, so the default weights need a stronger companion arm
(arm 1b above); and the task's sparsity must be calibrated before any fit, because a needle that random
exploration hits in 2% of episodes is unlearnable at affordable exposure while one hit in 13% of episodes
is learnable by every arm.

## 4. Order of work on the real host, if the owner takes this up

1. Zero fit (≈ .1 CPU-h): implement the host subclass and the schedule features; run the four references
   on the 64 dev worlds. Room condition: O_W − sticky ≥ 2.0 windows and O_W ≥ 3.5; near-camping ≈ 0 windows
   with high contract reward (the decoy is real). Sparsity calibration (the toy's rung lesson): the random
   slot program must satisfy between 5% and 20% of windows; below 1% the needle is too narrow for
   affordable exposure, so loosen the served condition (6 of 10 users) or lengthen the hold before any fit;
   above 30% the objective is not sparse and the question is moot. If either condition fails, fix the
   geometry, the served condition or the window length before any fit.
2. One fit per learned arm at the b03 exposure, in the pure-sparse variant (w_dense = 0), read by the
   pre-declared rule. The decoy variant is bought only if at least one arm activates.
3. Seeds for the active arms only; then the exposure curve (the owner's idea 1) on this host.

Independent scientific review under constitution section 5 applies before step 2 as a new host and a new
metric; the toy and the floors supply its facts.

## 5. Cost summary

| Item | Price |
| --- | --- |
| Toy (both rungs, five seeds, five arms, two decoy settings) | minutes of CPython in this container, 0 node resources |
| Real-host zero-fit floors | ≈ .1 CPU-h, ≈ 4–6 engineering hours including the subclass and tests |
| First round of fits (three arms, one instance each) | ≈ 5.4 CPU-h + .3 CPU-h evaluation |
| Seeds and exposure curve | only after activation; priced then |
