# coupled_host_joint_skills_stage1 — NOTES (append-only)

Direction owner: Claude DM (WSL session, `/home/fires/hmasd-wsl`, main). Selected in round 3 of the Claude successor selection (owner via Root de03d1c39; Oracle memo, critic review and Pro §5 answer under `docs/research/candidates/energy_relay_benchmark/successor_selection_20260929/` and the 2026-09-29 entries of that notebook); owner decision "2" = [DECIDE-2] accepted (6136bc2c9). Type: **a capability/instrument study of existing learners on a new, explicitly contracted cheap coupled relay host, with a separately priced, low-prior, non-automatic SCC re-entry cell. Not a new MARL-algorithm contribution.**

## 2026-09-29 — b01 declaration: Stage-1 joint skills on a cheap coupled relay host (cells 0–1; cell 2 conditional and separately declared)

### Question
On a UAV relay host whose coupling is first proven by ordinary planners (best relay-capable placement minus best re-optimised no-relay placement at the same information ≥ a declared practical threshold), do the existing learners — HMASD (D-route, fixed k = 10) and the matched-information flat learner SET — reach a useful fraction of the ordinary planner's backhauled service at S1-class CPU cost (three training seeds each), and does HMASD's coordinator learn a non-additive label→outcome map (the B12 interaction reader) — i.e. complementary "who relays, who serves" roles — beyond what the flat learner achieves? The answer decides whether future skill-duration (untied K) and agent-count (untied N) algorithm work in the Claude line is built on HMASD's coordinator or on flat/anchored forms, and whether the explicit SCC re-entry cell (SeqAU credit in the coordinator) is worth buying.

### Decision object, comparator, type
- Decision object: (i) the learner package the Claude line develops further on coupled hosts (HMASD coordinator vs flat SET vs neither at this budget); (ii) whether cell 2 (SeqAU) is bought. Who acts: the Claude DM for (i)/(ii); the owner only if a positive changes the K/N programme.
- Comparators for the decision: for learner competence, the closed-loop ordinary planner P_relay (package reuse; the strongest ordinary alternative with the same information, executor and travel time); for the hierarchy's value, the matched-information flat learner SET (attribution with the narrower interpretation "package difference at equal exposure and update count", not component attribution).
- Type: capability/instrument. No algorithm-contribution claim is made in cells 0–1.

### Host contract (direction-owned subclass; no shared-env edit; fixed before cell 0, identical for every arm including any cell 2)
Base class `envs/pettingzoo/scenario2.py::UAVCooperativeNetworkEnv` (constructor 18–42) via a direction-owned subclass `CoupledRelayHost` under `experiments/candidates/coupled_host_joint_skills_stage1/host.py`, constructed only by the direction's factory:
- `n_uavs = 6`, `n_users = 50`, `area_size = 5000` m, `user_distribution = "cluster"` (`uav_env.py` 516–532: five centres uniform in the arena, std 500 m, clipped), `n_ground_bs = 1` (centre), `ground_bs_tx_power = 23` dBm (pass-through `scenario2.py` 41 → `uav_env.py` 147), `channel_model = "free_space"` **pinned** (the backhaul/normaliser paths hard-code free-space loss, `scenario2.py` 596–667, 733–767), `max_hops = 3`, `use_fdma = True`, `max_steps = 500`, `height_range = (50, 150)`, `max_speed = 30` m/s (actions are normalised 3-D velocities, `uav_env.py` 280–291), `max_observed_uavs = 6`, `max_observed_users = 20`, `time_step = 1.0`. Base-env constants that apply and cannot be changed by arguments: `tx_power` 23 dBm, `noise_power` −80 dBm, `min_sinr` 3 dB, carrier 2 GHz, bandwidth 20 MHz (`uav_env.py` 117–121). `max_connections`: the base class overwrites the constructor value with 10 (`uav_env.py` 122); the subclass **declares 10** and asserts it after construction (no silent value).
- Static users (no motion in `uav_env.step`, 264–350). Global state = UAV xyz + user xy + step (`uav_env.py` 150); the BS is a fixed constant absent from the state; scenario-2 observations add BS-connection and hop fields (`scenario2.py` 117–118).
- **Reward (training and reading, one contract):** `r_t = ½ · (C_bh,t + S_t / D)` with `C_bh,t` = fraction of users connected to a UAV that has a backhaul path to the BS at step t (backhauled coverage; access coverage without a path counts zero), `S_t` = the existing "front-end capacity of UAVs with a backhaul path" quantity (`scenario2.py` 786–806; named exactly so — it is not end-to-end bottlenecked Mbps), and `D = n_uavs · B · log2(1 + 10^3)` (the base class's per-UAV front-end ceiling at 30 dB SINR, `scenario2.py` 745–746; a constant ≈ 1.196 Gbps, therefore independent of UAV positions). **No clip.** The per-agent reward stays the team scalar divided by n_uavs (`scenario2.py` 289–290); every reading and threshold below is on the **team per-step scale** `r_t`. The original reward's defects this removes are recorded in the selection notebook (state-dependent denominator that an idle UAV lowers by moving away from the BS; clip at 1.0 binding in relay-capable worlds). Access coverage, the original normalised reward and `avg_hops` are logged as diagnostics only.
- Deterministic world generation from a world seed (reset seed): dev worlds 1000–1031, hold-out worlds 2000–2031, training worlds drawn from the training seed's stream. Initial UAV positions per the base class reset (recorded per world).

### Cells
**Cell 0 — zero fits, `local_linux`.**
- (a) Ordinary placement planner `search_placement(world, allow_a2a)`: a same-information (ground-truth user and BS positions, the env's own connection/routing/reward functions as the static evaluator) local search over the six UAV positions — initial candidates from k-means service centroids (k ∈ {4, 5, 6}) with relays on BS→centroid lines, then coordinate descent with a 100 m step and a fixed evaluation budget of 3,000 evaluations per world; `P_relay` = best with UAV–UAV links allowed; `P_flat` = the same search, same budget, same fleet and caps, with UAV–UAV links disabled in the evaluator (never "optimise relay then delete"). Static-gate reading on the 32 dev worlds: `G = mean(P_relay − P_flat)` on the contract reward and `G_C = mean(C_bh,relay − C_bh,flat)` in backhauled coverage. **Gate: G ≥ .05.** If it fails at 5 km, one pre-declared re-parameterisation (`area_size = 6000`) is allowed; a second failure stops the direction at 0 fits with the result "no cheap coupled parameterisation of scenario 2 under the current channel" (an informative negative about the host, not about learning).
- (b) Closed-loop ordinary references on dev and hold-out: `P_relay` and `P_flat` executed from each world's common initial positions with straight-line flight at `max_speed` (travel time counted, 500 steps), plus stationary and uniform-random floors. These, not the static gate, are the competence references for the learners.
- (c) 20k-team-step timing probe of both learners on `local_linux` (environment and update time, peak RSS; a short training run, recorded as such); the probe fixes the concurrency (2–3) for cell 1.
- (d) Contract check: the subclass reward equals the formula above on 100 random states (unit test); `max_connections == 10` asserted; free_space asserted.
**Cell 1 — six fits, `local_linux` CPU, one runner with an arm switch (adapted from `experiments/candidates/agent_count_generalization/runner.py` + a scenario-2 adapter in place of `adapter.make_envs`).**
- HMASD arm `H`: the ACG `H6` recipe (`agent_count_generalization/configuration.py` 32–63: `apply_algorithm_config(config, "hmasd")`, k = 10, n_Z = n_z = 6, hidden 256, 8 heads, 2 layers, PPO epochs 15, sequence batch 32, coordinator batch 1280, 16 lanes × 500 steps × 45 rollouts = 360k team steps) with `policy_interruption_mode = "d2"` (the D-route; required by the B12 collector's `d2_k_max/d2_k_Z` caps, `hmasd/agent.py` 491–504) — declared as a recipe difference from ACG's `"off"`. Seeds 931201, 931307, 931413.
- Flat arm `SET`: the ACG `SET` recipe (`apply_algorithm_config(config, "mappo")`, k = 10 restored, `use_central_snapshot_in_flat_actor = True`, same lanes/horizon/rollouts/epochs/hidden). Seeds 932201, 932307, 932413. Exposure and update counts matched by construction; the matching table (lanes, horizon, hidden sizes, epochs, batch sizes, information, exposure) is printed by the runner and recorded before the first fit.
- Panels (deterministic actions) at rollouts 0, 15, 30, 45 on the 32 dev worlds; final rollout-45 panel on the 32 hold-out worlds, deterministic and sampled. Readers per panel: `r` (team per-step, mean over the 500 steps and final-100-step mean), `C_bh` (mean and final), far-cluster backhaul share (users in the cluster whose centre is farthest from the BS that are backhauled), `S` in Mbps, relay-hop usage, relay-position share by agent index, label entropy (H only).
- **B12 interaction reader** on each H rollout-45 checkpoint: 16 collection rollouts × 16 lanes × 500 steps on the training-world law; a pre-specified interaction model — count regression of the per-step team reward on per-label counts (additive terms), pairwise label-count products and a relay-pair term (label pairs whose members hold relay positions), with 1,000-permutation calibration (labels permuted within lane and step block to respect within-world dependence) and a team-label placebo; read correlationally (no causal "learned cooperation" claim). Extension of `scripts/run_fsd_commitment_visibility_b12.py` (FSD-specific arguments generalised; the FSD script itself untouched).
- Descriptive zero-fit readers on the H checkpoints: prefix-usage (z_<i sensitivity: distribution shift of z_i under supported prefix interventions with the state, Z and hidden state fixed; agent 0 as the structural negative control) and teammate-conditioning of goals — usage checks, never screens.
**Cell 2 — conditional, not bought here.** Only if P2 ∧ P3 ∧ P4 hold: SeqAU (prefix-conditional sequential advantage, SCC's recorded re-entry form, `sequential_coordinator_credit/NOTES.md` 384–390 lessons a–f) in `update_coordinator` versus the shared return, three fits paired to cell 1's H seeds and worlds, same contract. Declared separately with its own §5 review, cost and readers; COSAC's contextual-bandit/sequential-execution setting means this is a tested rewrite, not the paper's instance. Prior low (SCC: speed not endpoint; realisable ridge SeqAU lost under relay substitution — homogeneous UAVs are the substitutable regime).

### Predictions (falsifiable; odds are the DM's, conceded before purchase)
- P1 (gate): `G ≥ .05` at 5 km — likely (≈ 70 %); the critic's proxy (+.14 under the original reward and a weak layout) is evidence for the direction of the sign, not for the contract value.
- P2 (competence): on the hold-out closed-loop panel, each learner's `L_2,s = C_bh,learner,s − C_bh,P_flat − ½ G_C ≥ 0` for ≥ 2 of 3 seeds, with far-cluster backhaul share > 0 — H ≈ 40 % | P1, SET ≈ 45 % | P1. (Reported as instance differences; "2 of 3" is a pre-declared reading rule, not a significance criterion.)
- P3 (roles): the interaction terms exceed the permutation 95th percentile for ≥ 2 of 3 H seeds — ≈ 35 % | P2(H).
- P4 (hierarchy value): `r_H − r_SET ≥ +.03` on the team per-step contract scale (hold-out, deterministic) for ≥ 2 of 3 paired seeds — ≈ 30 % | P2.
- Modal outcome conceded: P1 holds; one or both learners below P2, or an additive map (P3 fails); cell 2 never bought.

### Outcome rows → belief / investment (Pro's table, adopted)
| Outcome | Belief changed | Investment changed; not implied |
|---|---|---|
| Gate fails at 5 km and at the one 6 km fallback | this host/budget does not establish the relay opportunity | stop D2 at 0 fits; the coupled-host question moves to S7-S1 on CUDA or waits; no "MARL useless" |
| Gap exists; neither learner reaches P2 | existing packages do not realise the reachable opportunity at 360k | instrument failure; no retrain, reward change, credit cell or seed addition |
| SET reaches P2, H does not (or H < SET by ≥ .03) | the flat learner suffices; the hierarchy shows no value for its complexity here | prefer SET for coupled-host follow-ups; coordinator-based K/N line deprioritised; no cell 2 |
| H reaches P2, P3 readable, P4 unresolved | a readable joint-behaviour instrument exists; no hierarchy superiority | keep the instrument; invest only on a named use |
| H reaches P2, P4 positive, P3 unsupported | the package may be useful; the claimed role mechanism is not established | package choice; no non-substitutable-role claim; no SCC evidence |
| P2 ∧ P3 ∧ P4 | a strong hierarchical instance on this host and budget | retain HMASD; re-evaluate the explicit SCC re-entry (cell 2 declaration); no automatic credit gain implied |
| Technical/metering failure | no scientific result | pre-declared technical stop; no seed swap hides a failure |

### Cost (separate quantities; never one "total hours")
- Cell 0: planner search + P_flat + gate script 8–12 h; host subclass, factory, contract tests 4–6 h; runner adaptation (arms H/SET, scenario-2 adapter, matching table) 6–10 h; interaction-reader extension 4–6 h; timing probe ≤ 30 min CPU; gate evaluation 3 configurations × 64 worlds (minutes); engineering review of the subclass/reward and the runner arm switch 2–4 h. Engineering cap for cell 0: **40 h**; stop and report if exceeded.
- Cell 1: 6 × 360k = 2.16 M team training steps; projected from the S1 anchors (ACG serial H6 70–99 min, SET 54–89 min at N6/H500; the environment adds ≈ .75 ms/step ≈ 4.5 min per fit) ≈ 1.2–2.0 h (H) and .9–1.5 h (SET) per fit → ≈ 7–11 process-hours, ≈ 4–7 h wall at 2–3 concurrent; peak RSS ≈ 2.75 GiB per fit against ≈ 9 GB free (B07's 14 GB kill at 4 concurrent is the risk). Panels: 4 dev + 1 hold-out (two modes) per fit ≈ 6 × 32 × 500 = 96k steps per fit, .58 M for six; B12 reader 128k per H checkpoint, .38 M for three; descriptive readers minutes. CPU cap for cell 1: **20 process-hours** (measured `resource.getrusage` per fit, as in `uav_restoration_readiness/b01`); a fit exceeding 2× its probe projection is stopped and reported.
- Cell 2 (if declared): 3 × 360k more, SeqAU implementation 8–12 h plus engineering review 2–4 h (shared coordinator update); its own panels.
- Cumulative in this line before this declaration: 0 fits; one Oracle memo, one critic review, one Pro review, DM reading (round 3).

### Stop rules and no-tuning
No change to the reward contract, denominator, planner search budget, seeds, lanes, horizon, rollouts or thresholds after any learner score is seen; the 6 km fallback is decided at cell 0 before any fit. No second fit per seed, no extension after scores, no repair of a failed arm. A technical failure of one fit is recorded; the arm's remaining seeds complete; no replacement seed.

### Independence and inheritance
Distinct by decision object and comparator from Codex Q1 (`uav_persistent_service`: reassignment before F, energy, H12000) and Q2 (`uav_message_content`: scalar slot, RR channel); from `uav_joint_transition`, `uav_radio_placement` (R is not used here), `uav_cooperative_planning`; inherits without reset: `complementary_skill_learning` (B01: positive local pairing does not recover P service; B06 bank-advantage reversal), `agent_count_generalization` (LOCAL1 ≈ HMASD at equal exposure; SET competent on S1), FSD B12/B13/B14 (S1 labels additive; I1 adverse), SCC (D loses to SeqAU on the microhost; realisable credit adverse under substitution), FLAT .4510. FSD is not reopened (S1, duration mechanisms); SCC is re-entered only by cell 2. Scenario 2 has no prior research record (grep of RESEARCH and all NOTES). Sources: Pro answer 2026-09-29 §§1–2, 6; critic review §§1, 3; Oracle memo §2 D2; paradigm note §3.3/§3.6.

### Bounded implementer tasks (L0 scope notes to follow; Opus/high; each returns diff, tests, deviations)
T1 host subclass + factory + contract tests (reward formula, max_connections, free_space, world seeds). T2 placement search planner with `allow_a2a` switch, `P_relay/P_flat`, static gate script and closed-loop executor (straight-line flight), floors. T3 runner: ACG runner adapted (arms H with `d2`, SET), scenario-2 adapter, matching table, panels/readers, timing probe, per-fit CPU metering, `require_admission(__file__, direction="coupled_host_joint_skills_stage1")`. T4 B12 interaction-reader extension with synthetic additive-vs-interacting tests. (T5 SeqAU only after a cell 2 declaration.)

### Gates before any launch
This declaration receives one §5 review (Pro) as a declaration; cell 0 launches only after that review is read and its material dissent (if any) resolved in this notebook; cell 1 launches only after the gate reading and the timing probe are recorded here. Launcher: `scripts/hmasd_launch.py` on `local_linux`, published source on main, RESEARCH Active row state `exploring`, lead `Claude DM (WSL session)`.

### Send record (2026-09-29 06:32 UTC): SCOPE message to Root
`codex queue --thread 01a0e560-4333-7b03-8ff3-759a4add1d9a` (current Root per RESEARCH session routing): Queued message 01a0ebdd-1a24-76f2-944a-d434deca732c for thread 01a0e560-4333-7b03-8ff3-759a4add1d9a.; one send, no reply requested. Content: selection complete at 1d765aa3e, D2 declared with type/comparators/cost, second slot unresolved (D1′ candidate), no overlap with Codex Q1/Q2, no node use. Text at `temp/directions/coupled_host_joint_skills_stage1/scratch/scope-20260929/scope_to_root.txt`.

## Pro question 2026-09-29 b01-declaration-review
Source: this notebook at the pinned commit given in the send record; read the b01 declaration above in full, the round-3 records (`docs/research/candidates/energy_relay_benchmark/successor_selection_20260929/{BRIEF_ROUND3_TWO_DIRECTIONS,MEMO_ROUND3_TWO_DIRECTIONS,REVIEW_ROUND3_TWO_DIRECTIONS}.md`), your own answer under `## Pro question 2026-09-29 round3-two-directions` and the DM disposition and owner decision entries in `docs/research/candidates/energy_relay_benchmark/NOTES.md` (2026-09-29), the D1′ candidate entry there, and the code the declaration cites (`envs/pettingzoo/scenario2.py`, `envs/pettingzoo/uav_env.py`, `experiments/candidates/agent_count_generalization/{configuration,runner,adapter}.py`, `hmasd/agent.py` 478–510, `scripts/run_fsd_commitment_visibility_b12.py`).
Context: this is the review of a declaration as a declaration (your 2026-09-29 answer: "解决异议需要一份收口后的声明，而不是再增添同题评审循环"). Owner "2" accepted [DECIDE-2]; [DECIDE-1] not exercised. Cell 0 launches only after this review is read; cell 1 only after the gate and timing probe are recorded. Withdrawn premises remain excluded.
Constraints: seeds and matched baseline per constitution section 8; single-instance wording; no training, no edits outside the empty "### Answer" subsection; write only there on branch main. Read the question at the pinned source, but fetch the latest target file before editing and use its actual blob SHA. Preserve all other bytes; stop on overlapping edits. On successful write, report the actual commit. On write failure return the complete answer in chat, not just a SHA, status message or link.
Return: (1) Is the host contract closed and legitimate — reward ½(C_bh + S/D) with the constant D = n_uavs·B·log2(1001), no clip, backhauled coverage as both training term and primary reading, `S` named "front-end capacity with a path", `max_connections` 10 asserted, free_space pinned — and does any remaining state-dependent channel or exploit survive (recompute from `scenario2.py` 733–835 and the subclass description)? Is the constant-D scale sensible (state the expected range of S/D) or should the throughput term be re-weighted before cell 0? (2) Is the placement-search gate (k-means seeds, coordinate descent, 3,000 evaluations, P_flat = same search with A2A disabled) a fair coupling proof, and are the closed-loop references (straight-line flight from common initial positions) the right competence comparators; what would you change in the search budget or the gate threshold? (3) Are the recipes defensible: ACG H6 with `d2` (recipe difference from ACG's "off") vs ACG SET; coordinator batch 1280; 360k steps; are the matching table items sufficient; do you foresee an S1-contract check in the ACG configuration (`state_dim != 133 or obs_dim != 104`) that the adaptation must lift, and any other adaptation hazard (adapter, action space, observation layout of scenario 2)? (4) Predictions P1–P4 and the outcome rows: falsifiable, readable at three seeds on the contract scale, and does each row change the stated investment; is the "2 of 3" reading rule stated honestly; is the modal outcome conceded correctly? (5) The B12 interaction reader as declared (count regression with pairwise and relay-pair terms, permutation within lane and step block, team-label placebo): identifiable and read correlationally, or does it need a different pre-specification? (6) Cost caps (40 engineering hours cell 0; 20 CPU process-hours cell 1) and the concurrency/memory risk; is anything unpriced? (7) D1′ as written in energy_relay_benchmark NOTES: is it an independent question with a real decision object and a fair ordinary correction, and what must change before it can be declared; should it wait for D2's gate as proposed? (8) MATERIAL_DISSENT: yes/no, with the specific change that resolves it; [DECIDE] items only where genuinely the owner's.

### Answer

#### Pro 声明评审：保留 D2，修正可执行合同后再启动

**结论：MATERIAL_DISSENT = yes，但异议已经收窄到可直接修订的声明条件，不再是是否允许选择 D2 的异议。** 固定分母、取消 clip、训练与主要读数统一为回传覆盖、真正重新优化的禁 A2A 对照、能力／仪器定位，以及非自动、单独计价的 SCC 后续问题，都是实质修订。我支持保留它们。现稿仍不能直接作为计时训练和六个正式 fit 的完整执行合同，主要缺口是 P2 的参照定义、P3 的识别／校准、若干确定会阻断 ACG 适配的代码条件，以及成本单位与停止规则。

**材料与边界。** 本评审以发送记录固定的 `cf62cef7b45ace34419bc475837f185cbf5a8592` 为研究来源，完整阅读了 b01 声明、round-3 的 BRIEF／MEMO／REVIEW、前轮 Pro Answer、2026-09-29 的 DM disposition、owner “2”及 D1′ 条目；核对了点名代码的实际奖励、路由、观测、训练和 B12 收集／统计路径，并补读直接依赖 `agent_count_generalization/models.py`、`env_adapter.py` 和宪章 §8。下文的数值是代码公式重算，不是新环境面板、planner gate、计时探针或训练结果。本次没有运行训练，没有把前轮 proxy 当作复现，也没有重做整个历史／文献库查重。尚缺的是待实现合同的验收与运行数据，不是本次所需文本来源。文末列出固定版本的来源定位，正文用短码引用。

Owner “2”已经接受 [DECIDE-2]；[DECIDE-1]没有行使，D1 的 S7-S2 探索没有被购买。D1′仍是候选，不是已宣告批次。这些不需要再表决一次。[N：06:26 UTC owner decision 与紧随其后的 D1′ 条目]

#### 1. 宿主：奖励变更合法，旧分母通道已关闭，但不能宣称所有激励都服务单调

令 A_i 为按原生关联规则分配给 UAV i 的用户集合，p_i 表示 i 有合法 BS 路径，γ_i 为 A_i 中最差用户的 SINR（dB）。实际声明对应：

`C_bh = (1/50) Σ_i p_i |A_i|`

`S = Σ_{i:p_i=1, |A_i|>0} B log2(1 + 10^(γ_i/10))`

`D = 6 × 20,000,000 × log2(1001) = 1,196,067,151.0603 bit/s`

`r = 0.5(C_bh + S/D)`。

原生贪心关联保证一个用户最多归给一个 UAV，所以这里没有重复覆盖计数。旧奖励的分母会计入全部 UAV 的位置相关直达 BS 容量，包括闲置／无路径 UAV；新 D 不含这些位置。**在 C_bh 和 S 不变的条件下，单纯把闲置 UAV 移远，不再提高 r。** 取消 clip 也消除了该处的饱和平台。统一 C_bh 为训练项与主要读数、把 S 准确命名为“有路径的前端容量和”、声明并断言 max_connections=10，均应接受。free_space 与理想 FDMA 也应该继续明确钉住。[E2：701–835；E0：117–122、945–979]

但有三个不能省略的限定。

**第一，30 dB 是参考尺度，不是前端容量上界。** E2:745–746 是旧 normaliser 使用的参考容量；实际 `_compute_uav_frontend_capacity` 没有把 SINR 截到 30 dB。按此处自由空间、23 dBm、−80 dBm、最低高度 50 m，最近地面用户的 SINR 可达约 30.5582 dB。因此无 clip 后不能写严格的 `S/D≤1` 或 `r≤1`。在所声明常数及合法高度下，一个安全的解析上界是 `S/D≤1.01859`、`r≤1.00930`；这是上界，不是正常世界的预期成绩。另外，带宽是构造参数，不是“不能通过参数改变”的常量；应写“本方向显式固定 B=20 MHz”，而不是陈述错误的 API 事实。[E2：18–42、701–767；E0：21–46、117–122、773–783、895–930]

**第二，仍存在舍弃弱用户／改变关联来抬高容量项的激励。** 一个 UAV 的整个前端容量由其最差用户决定。若一次移动或无回传 UAV 的抢关联使一个弱用户失去回传服务，却让原服务 UAV 的最差 SINR 从 3 dB 变为 20 dB，其他项不变，则 `ΔC_bh=−.02`、`Δ(S/D)≈+.08487`，从而 `Δr≈+.03244`。这是按代码公式给出的条件算术例子，不是我已经在本次世界面板上观察到的事件。它说明：**P4 的 +.03 可能由覆盖下降、容量项上升构成，不能自动叫作服务覆盖改善。** 原关联只按 SINR 和连接数上限贪心分配，不先排除无 BS 路径的 UAV，故关联竞争本身也必须记录。[E2：701–732、786–806；E0：945–979]

这不同于旧分母的“指标全不变却涨分”：现在发生了声明中的容量—覆盖取舍。不过，它仍足以否定“修复后不存在其他可利用激励”或“奖励提高必然覆盖提高”。我的建议不是临时扩充成完整网络流量模拟，而是保留当前抽象，记录覆盖损失与关联转移，并在 package 的采用读数中显式检查主要覆盖量，见第 4 节。

**第三，有路径不等于有端到端交付能力。** 当前 S 不调用 `_compute_effective_throughput` 的瓶颈路径，没有共享 BS／中继流量守恒约束；刚越过 SINR 阈值的路径和宽裕路径都能打开相同的前端容量计入资格。纯中继、兼任服务／中继、用户争用和路由替代都可能存在，但“需要一条路径”不证明中继角色不可替代。可以在这个路由—覆盖抽象上做能力研究，不能外推为真实交付 Mbps 或 SCC 的非替代性保证。[E2：596–732、786–806；R3-R、N：前轮 Pro §§1–2]

**S/D 的量级与权重。** 写成 `T=S/D=(1/6)Σ_{活跃且有路径的i} q_i`，其中 `q_i=log2(1+10^(γ_i/10))/log2(1001)`。对一个活跃服务 UAV，连接阈值附近 q≈.1588；最差用户三维距离约 300、500、1000 m 时，q 分别约 .5043、.3641、.1949。于是：

| 条件示例：最差用户三维距离 | 4 架实际服务且有路径时 T | 5 架实际服务且有路径时 T |
|---|---:|---:|
| 300 m | .3362 | .4202 |
| 500 m | .2427 | .3034 |
| 1000 m | .1299 | .1624 |
| 约 1194 m，连接阈值附近 | .1059 | .1323 |

这些是条件尺度示例；中继也可能同时服务，不能先验把活跃服务架数固定成 4 或 5。**规划用的合理量级是“有用布局常可在约 .1–.4，四五架服务且最差距离在 300–1000 m 时约 .13–.42”；实际分布均值尚未测得，随机／断网状态可以为零，紧密近距离布局可以更高。** 不能把这个范围写成已验证的宿主统计。[E0、E2；本答复公式计算]

我的选择是：**保留 D 和两个 1/2，不在 cell 0 前无依据地放大吞吐项。** 此时覆盖通常占较大份额，但吞吐绝非数值消失；放大它反而强化上述舍弃弱用户的动机。先固定合同并分项报告。若研究目的改成吞吐优先，当然可另定权重，但那是另一份预先声明的目标与阈值，不能看过 gate／learner 后校准。

宿主还需要几个明确的验收点，而不只是 100 个随机状态的等式测试：

- **路由跳数语义。** 当前 BFS 在 `len(path)>=max_hops` 时才停止扩展，且先检查直达 BS；参数 3 可以允许 3 条 A2A 链路再接 1 条地面链路，即总计 4 条链路。原观测又用节点数 `len(path)` 归一化，直达路径的长度为 2；它不是 `avg_hops` 使用的 `len(path)−1`。最小改动是保留原生路由行为、准确声明参数语义，并用真实链路数／是否有路径做诊断。若要改成总链路数最多 3，必须在 direction-owned subclass 内于 gate 前固定，不能默默混用两种宿主。[E2：221–255、365–449、807–823]
- **新鲜状态与一致性。** `scenario2.step` 先经过父类 step，再更新 A2A／BS 路由并重新算 reward。静态 evaluator 直接改坐标时，也必须依次失效缓存、重算 SINR／关联、重算开关后的路由、再取新奖励。断开／接通 BS、A2A 开关、终止步、空服务 UAV、连接数达到 10 和上述弱用户边界，都要有定向测试；旧 reward 的诊断不得覆盖新训练 reward。[E2：267–309；E0：264–350、773–982]
- 明确 `use_shadowing=False`、B、原生动作约束和观测布局；6 km fallback 若继承生成器，用户散布标准差也变为 600 m。原生成器的 cluster_centers 是局部变量，far-cluster 读数需保存同一次生成的中心与归属，不能重新抽样或把 k-means 中心冒充原生成中心。[E0：516–532]

#### 2. Placement gate：对照形式正确，但只能证明给定搜索器／预算下的实用机会

真正禁 A2A、保留整个舰队并重新优化 P_flat，是正确的普通对照。静态 placement 与共同初态下的 500 步部署分开，也是正确修订。但是“best”应读作 **best found**；相同求值次数不自动保证两个非凸搜索同样接近最优，不能称作全局耦合证明。[D：Cells；R3-R、N：前轮 placement 讨论]

**我保留每臂每世界 3,000 次的主预算，不建议立即翻倍，也不建议看完正负后加预算。** 应把这个预算实际分配规则写死：初始候选也计数，固定 k-means 随机流、重启数、坐标顺序、tie-break 和停止条件；两臂使用同一候选生成原则。建议在 3,000 内预分配粗搜与精修，例如 2,400 次粗搜、600 次 25 m 的末段精修，并把高度候选明确为 50／100／150 m；只有一个 100 m 的三维步长可能根本没有对中间高度起点做有效高度搜索。

P_flat 的起点不能只有远端用户簇中心：要包含向 BS 收缩的直达服务候选，否则“没有 relay seed”可能变成“没有可行 flat seed”。最好把找到的 P_flat 布局也作为 P_relay 的一个 incumbent，计入原预算；在相同关联与奖励下，增加可用路由不应使这个同一布局的得分降低。记录两臂在 1k／2k／3k 求值处的 incumbent 和各起点贡献，检查结果是否由明显未收敛或单一起点灾难主导。若这些检查暴露搜索不足，应写“本预算未建立机会／搜索读数不充分”，而不是“整个 Scenario 2 没有耦合”。预算之外的追加搜索不在本次建议中自动获准。

**门槛建议：保留静态 dev reward gap `G≥.05`，并增加与本问题一致的闭环 dev 覆盖机会条件 `G_C,dev,cl≥.05`。** 后者是建议的前瞻性实用下限，即平均约 2.5 个用户的服务差，不是统计显著性界，也不是从未运行的面板估出来的门槛。理由是当前研究购买的是可实现的回传覆盖能力：一个只有吞吐差、没有有意义闭环覆盖差的 gate，不足以支撑“关闭一半覆盖差距”的 P2。静态 G_C 仍报告，但不拿来代替闭环值。如果 DM 选择另一个有理由的正覆盖下限，应在任何 gate／probe 结果前固定，不以过门为目标回调。

5 km 不满足预先固定的机会条件时，保留唯一一次 6 km fallback；后者失败便停止这一合同／预算下的 D2。不得外推为任意便宜参数化皆不存在，也不得自动启动 S7-S1。host 选择只看 dev；hold-out reference 只在所选宿主生成并封存，不参与 fallback 或调参。

**闭环参照是合适的能力下限，但不是已证明最强的普通闭环规划器。** 静态最优目标再直线飞行，优化的不是完整 500 步平均回报。应称“预定预算的 placement-plus-executor 参照”，保留全程成绩与最终阶段成绩，明确目标到 UAV 的分配规则，避免任意编号导致额外行程。它可以很好地回答 learner 是否达到了普通部署能力；不能仅因 learner 超过它就排除所有普通路径规划。

还有一个直接的公平性问题：原生 `Box([-1,1]^3)` 的 action 逐坐标乘 30，没有速度向量的 L2 归一化。合法对角动作可有 30√2 的水平速度。**不能让普通参照按 L2 速度≤30 飞，而 learner 按原生逐轴上限飞。** 最小改动是两者都保留原生 Box／逐轴规则，普通直线 executor 按同一可行域缩放，临近目标不越过；若改成 L2 限速，则所有臂一起在 host 合同中改。不要只修 planner。[E0：173–176、280–291；EA：动作转换]

#### 3. H6+d2、SET、1280 与 360k：配方可以保留，适配远不止换 make_envs

**H6+d2 对 SET 是可辩护的 existing-package 比较，不是 ACG H6 的原样复现，也不是 duration-interruption 实验。** 保留 coordinator batch 1280、16×500×45=360k 团队环境步和每臂三个预定种子；没有代码依据要求先追加 D128 臂或加长训练。固定十步 cadence 时，每 rollout 有 `16×(500/10)=800` 个团队 commitment、4,800 个 agent commitment 行。1280 是所声明批量上限，不意味着凭空得到 1280 条独立团队样本；实际采样／优化计数要输出。B12 的收集检查也明确要求团队行数不超过 coordinator_batch_size，因此 800≤1280 与其协议相容。[AC；B12：391–450、851–908、1060–1078]

d2 的理由要说准。`hmasd/agent.py:478–510` 的 off 分支同样设置 `d2_k_max` 和 `d2_k_Z`，所以不能说 off 没有这两个属性。真正的限制是 B12 的 `commitment_cap` 显式要求 `d2_enabled`，并检查两项 interruption cost 为无穷、age feature 为 off，随后从 D2 segment／cause 数据收集。因此“为复用这个收集协议选择 d2”成立，“只有 d2 才存在 cap 属性”不成立。应把 `skill_cap_k_max=team_cap_k_Z=10`、两项 cost=∞、age_feature=off 以及 HA-CTSE 路径关闭逐一固定，验收只有 reset／team_cap 两种原因且六个 agent 同步更新。SET 仍按其 off＋held central snapshot 的十步信息时钟运行。[HA：478–510；B12：327–345、851–908]

**确定存在的适配阻塞如下，不是风险猜测。**

| 位置 | 固定代码的行为 | 本方向必须做的处理 |
|---|---|---|
| AC `make_config` 末尾 | `state_dim !=133 or obs_dim !=104` 即报错 | 用明确的新 adapter 契约替换，不是删掉所有验证 |
| AM `build_agent` | 拒绝任何非 off 模式；再次检查 133／104 | direction-owned H 构造允许经验证的固定-cap d2；保持 SET 的正确路径 |
| AM `StateSetEncoder` | 按 8×3 UAV 位置、8 个 validity bit、100 用户坐标和时间解析 133 维 | 不能把原生 119 维硬塞进去，也不能仅改一个数字让切片错位 |
| AM `SetActorBase` | 强制 obs=104，hidden=256 时强制 concat=721 | 原生本配置 obs=90；保留现有编码方式时 concat 应为 693，相关线性层和断言一起改变 |
| AA 工厂和 AR 内部 imports | 仍创建 S1 uniform 环境；训练与 evaluator 分别引用 ACG 工厂 | 两条路径、admission direction、seed 规则、测试 N 和面板都要实际切换 |
| AR `native_components` | 验证 `.7 coverage+.3 quality−energy`，并要求 S1 奖励键 | 改为逐步验证 `N×adapter_scalar=.5(C_bh+S/D)`；不借用旧 key 的错误语义 |
| AR checkpoint／B12 loader | ACG 保存 `modules`／normalizers；B12 构造旧 FSD 对象并调用其 load_model、旧 seed／reference 验证 | 新 reader 必须走新工厂及严格 checkpoint 加载，不能只替换 FSD CLI 参数 |

[E0、E2、AC、AA、AR、AM；B12：910–1055]

**维度和语义应直接写进匹配表。** 原生 state 为 `6×3+50×2+1=119`；本配置 observation 为 `3+20×3+6×4+1+1+1=90`。其索引布局是 own `[0:3]`、users `[3:63]`、other-UAV slots `[63:87]`、time `[87]`、BS connection `[88]`、legacy hop `[89]`。用户三元组的末项、UAV 四元组的末项，实际都是归一化 SINR，而不是部分注释所称的距离。空槽、排序及 hop 的歧义不能靠改 shape 掩盖。[E0：150–155、383–501；E2：117–134、221–255]

最小风险的复用方案是保留 ACG 的**有缩放、8 槽／validity 的 133 维 adapter state**，明确它只是同一原生 119 维信息的编码，换成本场景 90 维原生 observation，并相应适配 AM；不是给 flat 多加世界信息。若改为新的 119 维 encoder 也可以，但要声明架构改动、重新绑定优化器，并验证所有替换模块真正更新。不能为了绕过 d2／维度断言而退回一个失去 StateSetEncoder／SET actor 的不同 baseline。尤其不要在 `use_statenorm=False` 下，误将原来缩放到单位尺度的输入换成数千米的裸坐标。[AA、AM]

EA 返回的是各 agent 奖励的平均值，原生每个 agent 已拿到 r/N，因此 scalar 仍是 r/N，不是 r。读数恢复团队尺度时只能乘一次 N。原生动作还是连续三维速度，不是目的地 offset，也不是离散角色动作；核对采样动作的合法范围和 requested／executed action，保留真实 terminal successor 在 reset 前存储的现有正确顺序。[EA：185–315；AR：训练与 evaluation 循环]

当前匹配表是骨架，**不充分**。还应逐项输出：准确观测／state 编码和 snapshot 时点，reward 单位及 H 的辅助目标权重，gamma／GAE、value norm、观测／state norm、learning rates／schedule、PPO clipping／梯度裁剪、批量单位与实际 optimizer calls、网络参数量与信息入口、episode reset／bootstrap 规则、评估时冻结的参数和 normalizers、CPU dtype／线程数、训练／环境／评估 RNG 的分工，以及 final-45 不择优 checkpoint 的规则。H 的 coordinator 和 discriminator 有梯度步而 SET 没有，因此“equal update count”只能指已明确定义的外层 rollout／共同 low-level 更新日程；不能说全部优化计算匹配。三组 seed 应固定按声明顺序配对，公开两臂不同训练 seed 不等于共享了相同训练世界／初始化。[AC、AR、AM、C §8]

#### 4. P1–P4 与结果用途：修正参照、联合实例及“不显著”的文字

P1 的 .70、P2 的 .40／.45、P3 的 .35、P4 的 .30 可以保留为 DM 的主观预期，不是测得概率。旧奖励＋弱布局的 +.14 不能标定新 G；这些条件概率也不足以直接算出 cell 2 的联合概率。[D；R3-R；N]

**P2 必须改成同一 hold-out、同一闭环、同一全程平均量。** 当前 G_C 只在 cell 0(a) 定义成 static dev gap，P2 却直接把它带进 hold-out closed-loop 式子。应分别命名，并定义：

`G_C,ho,cl = mean_w[C̄_bh(P_relay,w) − C̄_bh(P_flat,w)]`

`L2(a,s) = mean_w[C̄_bh(a,s,w) − C̄_bh(P_flat,w)] − 0.5 G_C,ho,cl`。

这里每个 C̄ 都是同一 500 步的均值，a 为 H 或 SET，w 为相同 32 个 hold-out 世界。最终 100 步与最终时刻留作已命名的次要读数。若 hold-out 闭环覆盖 gap 非正或明显不足以支撑“机会”解释，应报告机会没有转移／P2 此项不可解释，不能让负 gap 自动制造“有能力”。不再逐世界除以 gap，也不用 static-dev 数替代。

far-cluster share>0 是一个很弱的存在性条件：最远簇也可能可直达，微小的早期用户时间亦可能满足它。保留它作已声明描述，并同时报告该簇通过 A2A 路径获得的用户时间、全程与末段覆盖；它本身不能证明 relay necessity 或已学会角色分工。其中心及用户归属必须来自原始生成记录，而非看完轨迹后重新选簇。[D；E0：516–532]

**P4 的 +.03 可保留，但只表示新团队奖励尺度上的 package 差。** 在容量项不变时它等于 +.06 覆盖，不是三个百分点覆盖。鉴于第 1 节的反例，建议把“优先保留 H 作为覆盖能力 package”的读法加上同一配对实例 `ΔC_bh(H−SET)≥0` 的点估计检查；这不是统计非劣性证明。若奖励赢而主要覆盖下降，应单列“容量—覆盖取舍”，不能悄悄归入覆盖更好的层级 package。

“2 of 3 是预先读法，不是显著性”这句话已经诚实，应保留。还要报告全部三个 L2／paired Δr／ΔC、失败状态及世界条件不确定性，不把 32 世界、256 lane-episodes 或 128k 步冒充独立训练次数。三个公平独立符号中至少两个为正的概率就是 1/2；三种子满足宪章最低数，不保证分辨 .03。不同 checkpoint 不能挑最好，sampled 模式不能在 deterministic 不利时替换主终点。[C §8；AC、AR]

**购买 cell 2 的联合条件还必须说明是不是同一实例。** 例如 P2 在 seeds 1、2 通过，P3 在 2、3 通过，P4 在 1、3 通过，则各项都是 2/3，却没有一个 seed 同时通过全部三项。我的建议是：需要**同一组至少两个 H／SET 配对 block**满足 P2(H)、有效 P3、P4 及上述覆盖检查，才称为支持 SCC re-entry 的强实例；通过后仍只进入单独声明，不自动运行 SeqAU。

结果表方向正确，但应按以下优先顺序解释，避免重叠或缺行：

| 结果 | 应改变的投资 |
|---|---|
| 技术、合同、计量失败 | 该部分不产生科学结论；保留失败；依预算停止，不换 seed |
| 两个预定宿主的机会 gate 都失败 | 停止这份 D2 合同／搜索预算；不是“MARL 无用”或自动获准转跑 S7 |
| 有机会，但 H、SET 都未达到 P2 | 当前训练预算的能力仪器失败；不续训、不改 reward、不买 credit |
| SET 达到 P2，H 未达到；或两者有能力且 SET 明确更好 | 优先 SET；不能仅因 SET 比同样无能的 H 好一点就称“flat suffices” |
| H 达到 P2，但 package 差未分辨，无论 P3 为正还是未分辨 | 最多保留这一仪器及已明示用途；没有自动追加 fit 的理由 |
| H 有有用的 package 增量，但有效 P3 不支持所测交互 | 可以保留 package；不能宣称已证实联合角色，更不能据此购买 credit |
| 同一组至少两个实例满足完整联合条件 | 保留 H，重新评价单独计价的 cell 2；不是 credit 增益的保证 |

因此各行确实可以改变“保留谁／停止什么／是否购买下一项”，不必每行都启动新实验。**Modal outcome“cell 2 不被购买”是合理的低先验让步；但“P3 失败即 additive map”不正确，应改成“所测交互不获支持或不可分辨”。** 有限统计量失败不证明所有技能可加。问题开头的“non-additive map，即 who relays/who serves，且 beyond SET”也应收窄：P3 读 H checkpoint 的特定关联结构，P4 读 package 差；两者并不自动识别这种机制优于 SET。[D；C §8]

#### 5. B12：需要新的、真正写出的统计预规格，不能只泛化 FSD 参数

现稿“count regression＋pairwise＋relay-pair＋lane/step-block permutation”还没有给出可识别的完整模型。旧 B12 主要检验 label spread，cap=500 时另加 `Σ n_z²` 同质性项；它不是现在所需的一般 pair-interaction 检验。旧脚本还默认四个 cap、旧种子、旧 FSD 权重与 reference，照搬会改变 128k 的暴露量甚至根本读不到新模型。[B12：1–65、391–850、910–1135]

我的建议是预先固定下面这套最小可解释读法，而不是事后挑显著项。

**观测单位与响应。** 只读训练时的 cap=10，最终 checkpoint，冻结所有参数／normalizers，零 optimizer step；每个十步 commitment 对应一个全队 label vector 和该段的团队每步平均 r。每个 H 的 128k 步成为 12,800 个 commitment，名义上最多 256 个 lane-episode cluster；若世界重复，按真实 world ID 合并 cluster。记录动作前 state、时点、labels、路径／角色、执行动作和对应 reward 时间对齐。不能把十个相同 label vector 的逐步行当成十次独立指派。[B12：327–345、391–481、851–908、1066–1185]

**模型与 rank。** 旧 count-additive 模型可以保留作描述。主检验的 reduced model 至少包含预先指定的动作前 state／时间控制和 agent-index-specific 的单标签加性项；否则“同一个标签放在不同位置的 agent 上效果不同”就会被错误挤进联合项。full model 再加入事先指定的 label-count 二次基与 relay-service／relay-pair 项。固定 N 时 `Σn_z=6`；若平方与所有交叉项都纳入，又有 `Σ_{z'}n_z n_z'=6n_z` 等关系。必须选择独立对比基并检查实际支持下的 rank／条件数，而不是用伪逆得到系数便宣称已识别。不能在已经包含完整 pair 基后，再把同质性项当成独立机制。稀有组合、label collapse 或 relay 变量无变化时，读作不可识别，不是交互为零。[B12：483–613、621–783；数学关系由固定计数直接推出]

**relay 定义不能偷看响应。** “某 label 的成员占据 relay positions”需指明：实际中继是他人通往 BS 路径的内部 UAV 节点，不是凡出现在自己路径里就算 relay；服务与中继可兼任。主模型用 commitment 开始前的角色／图结构作条件，且给 reduced model 相应角色主效应。段结束后才形成的 relay 角色是行动结果的一部分，可单独描述，但不能作为已经控制好的前置变量来证明 labels 造成协作。聚合 counts 更不能独自识别“谁”的因果角色。

**校准的零假设必须是“在加性基线之外没有增量”，而不是“labels 与回报完全无关”。** 原始 label permutation 会破坏已有的加性效应和状态选择关系；在 lane 和 step block 内打乱，并不自动修复这个问题。逐步 shuffle 会破坏十步 commitment；若 block 本身只有一个 commitment，则根本没有可置换对象；若跨多个 commitment，又需处理状态与历史变化。仅按位置分组的旧 B12 permutation 不能直接改名为已保证交换性的角色检验。[B12：613–683]

一个具体可采用的替代方案是：按完整 world／episode 分组做固定交叉验证，以 full 相对 reduced 的 held-out MSE 减少为单一 omnibus 统计量；在 reduced null 下保留其拟合值，对完整 episode 的残差向量施加同一个 wild-cluster multiplier，重新拟合并以 1,000 次 null draws 校准。要求观察到的 held-out 改善为正且超过预定 95% 分位。预先固定控制变量、folds、正则化（如使用）、乘子、seed、基函数和 rank 失败处置，交互族一次联合检验，不逐项捞最显著者。**这是有模型及 cluster 假设的近似校准，不是精确随机指派试验，更不是因果证明。** 若仍坚持 label permutation，应明确所保留的加性／状态条件、交换单位及为何可交换，不能只写“respect within-world dependence”。

**team-label placebo 不能机械移植。** 旧 B12 的“team label 不直接输入低层 actor”不足以保证在新 checkpoint 的观测数据里它与回报独立：它可能代理 state，或经 individual-label law 与行动关联。其回归为正不能自动使整个 P3 无效；为零也不证明无混杂。保留它作为条件诊断，并加一个已知零效应的结构检查：固定 individual labels、state、hidden state，只改变不进入当前低层动作路径的 team-label 输入，应不改变执行动作；或者预先生成与轨迹独立的伪标签作统计校准。必须验证所用新网络确实满足这个结构前提，而不是沿用旧注释。[B12：210–241；HA、AM 的本方向构造]

T4 的 synthetic tests 应覆盖“强加性＋状态相关标签＋episode 内相关”而不仅仅 iid 零效应，也要有已知 pair interaction 的正例、缺支持／rank 失败例及奖励缩放检查。新 reader 保留旧 B12 的冻结权重、禁止 optimizer step、faithful-load、segment geometry、reward tape 和 RNG 恢复保护，但不继承其旧宿主 reference、四-cap 暴露或“placebo 一过即作废”的未经验证假设。

最后，**最终权重上有条件关联，不等于证明该结构是训练新学到的，也不等于它导致了 P4 的增益。** 本次可把措辞收窄为“有能力的 checkpoint 上存在预指定的非加性预测结构”。若要再证明 acquisition 或 causal coordination，须另列 c00／受控 label 干预等对照及成本；本评审不自动购买这些新增读数。P3 的重写和计算报价必须在 fit 前完成；没有有效 P3，就没有基于 P3 的 cell 2 购买。

#### 6. 成本：上限可以保留，但目前不是同一种“小时”，也不是完整报价

40 工程小时作为硬停止上限是合理的；现列工程项目合计 24–38 h，含 engineering review，余量很小。上面的 models 迁移、terminal／cache 验收与统计重写都在真实工作量内，不能因为分给 implementer 就不计工程成本。原 4–6 h 的 reader-extension 项不应被当成已经验证的报价。[D：Cost；AC、AM、B12]

**计时探针不是 zero fits。** 声明一面写 cell 0 zero fits，一面明确说 probe 是 short training run。应改成“零正式科学 fits 的 gate／合同检查，随后两臂各一次已记录的技术训练探针”。明确 20k 是每臂还是合计；我的工程建议是每臂 3 个完整 8k rollout，即 24k、合计 48k，以免为精确 20k 新造半个 rollout 的更新路径。它们不是六个正式 fit 的独立结果，也不用于选配方，但确实消耗训练步和 CPU，不能记成零。gate／fallback 与合同冻结先于 probe，probe 之后只使用事先允许的 timing／RSS 信息作资源准入，不用 learner 分数改研究参数。该建议的额外步数仍须落在已有 probe／工程上限内，不是新增无限技术尝试额度。[D：Cells、Stop rules；AR：完整 rollout 更新]

**process wall-hours 与 `getrusage` CPU-hours 不同。** ACG runner 同时记录墙钟和 user＋system CPU，且设 `torch_threads=4`。一个运行一小时的多线程进程可能消耗多于一 CPU 小时。因而 7–11 累计进程墙钟小时不能直接证明能落在“20 个 getrusage CPU 小时”内；并发只能改变总历时，不能把累计 CPU 自动除以并发数。probe 必须测两臂各自的 wall／CPU 比、收集／更新／评估时间和峰值内存，再按同一单位做六 fit 的准入预算。[AR：1–25、run_fit、resources]

当前 b01 的最低 cell-1 暴露量应按新面板重算，而不是沿用前轮的旧面板报价：

| 项目 | 团队环境步／求值量 |
|---|---:|
| 六个正式 fit | 2,160,000 团队训练步 |
| 每 fit 四个 dev 加最终 hold-out 两模式 | 576,000 评估步 |
| 三个 H 的单-cap B12 收集 | 384,000 评估／收集步 |
| 上述小计 | **3,120,000 步**，还没有 permutation／bootstrap 回归成本 |
| 技术 probe | 单独列明；按本建议为 48,000 训练步，不混成 0 |

门槛的“3 configurations×64 worlds”也不是 placement-search 求值账。单个 arena 的 dev 搜索是 `2×32×3000=192,000` 次静态求值；两个 arena 的 dev 最多 384,000，加所选 arena 的 hold-out reference 搜索 192,000，可达 576,000 次。另计完整轨迹的 planner／stationary／random panels、k-means、缓存重算、prefix reader、checkpoint 读写及失败成本。纯 evaluator 足够快时这些仍可能是分钟级，但目前没有本实现的实测，不能把“分钟”当作已闭合报价。

20 CPU 小时若保留为 cell-1 总 cap，就应涵盖六 fit、所有规定面板、独立启动的 B12 收集和 1,000 次统计重拟合；不能只对训练进程调用 getrusage，遗漏独立 reader／worker。声明中的“单 fit 超过 2×投影停止”“一个 fit 失败后剩余 seeds 完成”与总 cap 需明确优先级：**总 cap 优先；预算不足就保留未完成／不可作三种子结论，不能为凑齐三个而超支，也不能悄悄减读数。** ACG checkpoint 明确不是 optimizer 恢复合同，故恢复／重启不能假装免费。[AR：save_checkpoint、resources；D：Stop rules]

**并发建议从两个进程开始，不预先承诺三个。** 按声明的 2.75 GiB／fit 和约 9 GB 余量作规划，三个已约 8.25 GiB≈8.86 GB，几乎没有系统、评估副本和峰值波动余量；这不是本次对节点可用内存的新测量。AR evaluation 会在 learner 仍存活时构造另一个 agent，必须测这个重叠峰值及 PPO 更新峰值。只有实际节点准入和安全余量支持时才升到三个，同时核对 CPU 线程、BLAS、其他工作和 scratch。历史 B07 kill 只能提醒风险，不能给出新配置必然安全的概率。[D：Cost；AR：evaluate_panel]

#### 7. D1′：已是独立问题，但普通修正合同与总边际成本还不够完整

**是，现有 D1′ 比前轮已经明显进步。** 它的决策对象是“计划修正采用 learned 还是 ordinary”，主要比较 learned correction 对同锚点的普通 correction，次要比较 anchor；D2 决定的是现有 learner package 能否形成有用仪器。接受近似可加但有用的 learned gain，且不要求 `joint > sum of independent offsets` 才采用，也正确。共享宿主不是自动重复问题；共享同一失败点则必须继续承认。[N：D1′ candidate]

但在宣布三 fit 前至少补齐以下合同。

**普通 correction 的相同可行域必须是真的相同。** 明确每个十步 offset 是相对原 assigned anchor 还是累积到上次 target；300 m 是 XY 圆盘，不应让 ordinary 改高度、learner 却只能改 XY，或一方累积漂移而另一方每次被限制在原锚点附近。两者同一信息、target assignment、边界裁剪、executor 与动作范数；ordinary 保留零修正 incumbent，使用有实际竞争力的多方向／较细步长，而不是故意只做一个很粗的 sweep。300 evaluations 应定义为哪些原始模型调用；“一次 sweep”不足以复现实验。

同样要承认目标差异：learner 优化完整部署回报，而只看最终静态 reward 的普通 sweep 未必是最强的短程部署修正。至少明确它是“300-evaluation static local correction”这一有界对照，或在相同原始求值预算内加入考虑行程时间的候选评价；不能以一个静态、可能已经被 anchor 局部最优化的 sweep，直接代表所有普通在线修正。D2 gate 有 relay gap 也不保证 D1′ 还有值得购买的 correction headroom。cell 0 的搜索轨迹和闭环参照可帮助判断是否还有独立、可改变选择的问题，而不是因为第二槽空着就必须训练。

**身份检查及宏时间合同。** assigned target 要在动作发生前缓存，并对 actor／critic 可用；重放不能重新运行一个改变内部状态的 planner 来补 target。确定性零均值 offset 必须在完整执行链逐动作等于 anchor，包括 target assignment、裁剪、停靠和终止；随机 c00 不会因均值为零就自动等于 anchor。360k 应继续指原生团队步，等于每 fit 36k 个十步宏决策；16 lanes／500 步的 rollout 只有 800 个团队宏决策，不能继承按 8,000 原生步生成的宏 minibatch。若保持原逐步折扣目标，宏奖励应为 `Σ_{j=0}^9 γ^j r_{t+j}`、边界折扣 γ^10，并明确 GAE 时间单位。[N：D1′ 与前轮 Pro 的宏时间分析；AR]

**结果行还需补洞。** learned≈ordinary 不能由“不显著”直接定义；需预先固定实用区间及未分辨分支。learned>ordinary 但二者都低于 anchor，不能保留 learned 当作规划改善。最好让 ordinary 的合格基线包含 anchor／零修正保护，并同时报告 learned−ordinary 与 learned−anchor。保留“加性 gain 也值得采用”，但继续使用主要覆盖检查、全部三 seed、固定配对／终点，不把 2/3 写成总体优越性证明；未来第二宿主仍是新投资，不自动获准。

**边际报价漏了反复求 anchor 的成本。** `64×50×300=960,000` 是一套普通修正面板的静态求值数；多个模式／dev checkpoint 是否重用，必须说明。如果每个新训练世界都用 3,000 次搜索生成 P_relay anchor，那么三 fit 的 `3×360k/500=2160` 个训练 episode 还需要 **6.48 million 次 anchor 求值**，不包含在 D2 的 64 个 reference 世界里。若有缓存，列明缓存命中所对应的确切世界；不能把训练世界重复使用悄悄当作免费缓存。在线 300-evaluation correction 是否也在学习训练循环中运行，要单列，不能把每次十步的成本都隐藏在“调用 anchor”里。宏策略的实际训练调用／更新次数不同于 SET 原生逐步 actor，所以 3–5 process-hours 仍只是待测投影。12–20 工程小时之外的 review 2–4 h、全部面板、接口验收、CPU／wall／内存和失败成本，也需闭合。[N：D1′；本答复工作量重算]

**应等待 D2 的 cell 0 gate 与实际普通部署读数，但不必等待 D2 六个 learner fit 成功。** 等的是它依赖的宿主合同、ordinary capability 和计算报价，不是借用一个未来 HMASD positive。若 gate 失败，不能自动改名迁移继续买 D1′；若通过且上面合同闭合，再形成自己的声明及适用的独立科学评审。当前仍标 RECORDED／未宣告／未购买，这个状态是正确的。

#### 8. MATERIAL_DISSENT 与能一次解决它的修改

**MATERIAL_DISSENT：yes。** 异议不是反对常数 D、不是要求做成真实通信模拟器、不是再次否决 D2 的能力／仪器类型，也不是默认重开 D1。它针对“现稿已经足以直接启动声明中的技术训练和正式六 fit，并据 P3 决定 SCC 投资”的说法。

解决方式是一份由 DM 记录的收口修订，不是另一轮同题选题循环：

1. **宿主／执行语义固定。** D 改称 30 dB 参考尺度；准确写出原生 hop、速度、B 和 fallback 用户分布；接受并报告容量—覆盖取舍。完成 fresh-routing／cache／reward-unit 定向测试及 AC／AM／AR 的 direction-owned 适配验收，随后才做训练 probe。
2. **机会与终点统一。** 保留 3,000 主预算和 reward gate .05，固定一个有意义的闭环 dev 覆盖机会下限；P2 改用同一 hold-out closed-loop gap，P4 同报并检查主要覆盖量；结果行按技术／机会／能力／package／机制分层，cell 2 要求同一组至少两个配对实例满足联合条件。
3. **P3 成为可执行统计规格。** 固定 commitment 数据、独立对比基／rank 规则、状态／角色时点、单一增量统计量、保留加性 null 的 cluster 校准、placebo 的真实含义和 synthetic 验收；删去“不支持交互即证明 additive”“非加性即因果 who-relays／优于 SET”的等号。若做不到有效读数，就不能用这一项购买 cell 2。
4. **资源账与停止优先级闭合。** 技术训练不记零；分开累计 wall 与 CPU，把所有正式面板、reader 和统计计算计入 20 CPU 小时 cap，完成六 fit 的准入投影；默认两个并发，第三个以真实重叠峰值与节点余量决定；总 cap 优先于补齐种子。

这些修改保留了 D2 的研究选择与主要预算，不要求先运行新的调参批次。T1–T2 的无训练工程可按用户已述范围继续，但执行 gate 要用修订后固定合同；probe／cell 1 不应越过尚未解决的物质条件。D1′ 的独立声明缺口不应反过来无限拖住已闭合的 D2，也不能借 D2 的已接受状态被默认为购买。

**本轮没有新增必须交 owner 的 [DECIDE] 项。** [DECIDE-2]已经接受；[DECIDE-1]没有被行使。参数／统计规格／adapter／资源计量的闭合属于 DM 的科学与工程责任。只有另行重访 D1、改变 owner 的既有暂停／资源约束，或按声明真正改变 K/N programme 时，才提交对应的新 owner 选择。通过上述修改后，应进入既定的实现验收与有界观察，而不是再以“还需要一轮意见”替代结果。

#### 写回检查发现的并发追加记录：与固定快照分开处理

准备写入时重新读取 main，发现目标文件已追加“T1 + T2 implementation received”，当前 blob 为 `66cc1866ded6cc5f28c4209b94b0a805e3e8f43e`；Answer 仍为空，没有重叠编辑。该追加全文在写回时保留。**本答复的主体仍是固定提交的声明评审；没有据此冒称已读完这批新增实现代码、复跑了其 53 项测试或独立复测 smoke。** 仅依据追加记录的文字，补充以下执行边界。

其 range-aware relay chains、top-3 multi-start 和 plateau tie-break 方案，与本答复第 2 节所要求的可行起点／搜索充分性方向相容；3,000 必须仍是两臂各自跨全部起点的总预算，而不是每个起点 3,000。smoke 与候选分数不能替代完整 gate。记录已经披露 dev 1000–1002 的候选分数被查看，因此后续搜索器修订不能再称从未看过任何 dev 结果的全盲设计。继续保留开发披露，固定修订后的完整面板与规则，不换掉这三个世界，也不将“预先声明”回填到这次调试之前。不能借这些候选分数改写旧 P1 预期。

**追加记录将 P_flat 的主要闭环执行明确设为 A2A on。这个比较可以成立，但不能继续与真正禁 A2A 的 P_flat 共用一个无后缀名称。** 应区分 `P_flat^off`（禁 A2A 规划且禁 A2A 执行）、`P_flat^on`（禁 A2A 所得布局，在完整宿主执行，允许偶然中继）和 `P_relay^on`。我建议能力 P2 与其闭环覆盖机会条件使用同宿主的 `P_relay^on−P_flat^on`，这是更强的普通部署参照；第 4 节公式中的闭环 P_flat 明确取 on。静态物理耦合 gate 仍使用真正 off 的对照，闭环 off 读数另列并保留。前一个差距是普通布局／部署差，不能冒称禁用物理 A2A 的效果；若 on 对照消除了覆盖差距，P2 的“关闭 gap”问题就不再成立，不能拿 off 的较大 gap 顶替。

追加记录报告 host step 约 1.84 ms、约 11 min／360k 环境步，不是固定声明的旧 .75 ms／4.5 min 估计。它尚未由本评审独立复测，但已足以要求用两臂 probe 重报成本；也不能把完整 host-step 时间不加区分地当成 S1 learner 时间之外的增量。其“最差用户距 500 m 时 S/D≈.06”是**单架活跃服务 UAV 的贡献**：本答复算得 `.36409/6≈.06068`，四五架这样的 UAV 总贡献约 `.2427–.3034`。不能把单架贡献误读为全队必然只有 .06，进而据此放大吞吐权重。

#### 固定来源定位

除上节显式标明的写回并发记录外，以下均指 `CartmanFatass/My-paper-code` 的 `cf62cef7b45ace34419bc475837f185cbf5a8592`；代码数字为该版本文件行号，文档以原 heading／章节定位。

- **D**：`docs/research/candidates/coupled_host_joint_skills_stage1/NOTES.md`，b01 declaration、Predictions、Outcome rows、Cost、Stop rules、Pro question。
- **R3-B／R3-M／R3-R**：`docs/research/candidates/energy_relay_benchmark/successor_selection_20260929/` 下 `BRIEF_ROUND3_TWO_DIRECTIONS.md`、`MEMO_ROUND3_TWO_DIRECTIONS.md`、`REVIEW_ROUND3_TWO_DIRECTIONS.md`。
- **N**：`docs/research/candidates/energy_relay_benchmark/NOTES.md`，`Pro question 2026-09-29 round3-two-directions` 的 Answer、06:11 UTC DM disposition、06:26 UTC owner “2”、紧随其后的 D1′ candidate entry。
- **C**：`docs/project/OPERATING_CONSTITUTION.md` §8，五项 scientific minimums。
- **E2／E0／EA**：`envs/pettingzoo/scenario2.py`；`envs/pettingzoo/uav_env.py`；`envs/pettingzoo/env_adapter.py`。
- **AC／AA／AR／AM**：`experiments/candidates/agent_count_generalization/` 下 `configuration.py`、`adapter.py`、`runner.py`、`models.py`。
- **HA**：`hmasd/agent.py:478–510`。
- **B12**：`scripts/run_fsd_commitment_visibility_b12.py`，尤其 `commitment_cap`、`commitment_frame`、`design_matrix`／`fit_centred`／`label_regression`、`permutation_calibration`、`response_block`、`check_cap_geometry`、`_run`／`cap_reading`。旧脚本的科学用途与断言不能未经验证移植为新宿主结论。


### Send record (2026-09-29): Pro question `b01-declaration-review` sent
Question key `hmasd:0740cd163091672591ac4de9c339d0f76c04990d1e9e44f61a8d808da79bd5ca` (source sha cf62cef7b, question heading above); attachment `hmasd-pro-question-b01-declaration-review.md` (4,000 bytes); Jev transport, ChatGPT 6 Pro (effort pill verified), new conversation (address stays in the local operation file); dry run reached the send button with effort, text and attachment verified, then sent at 2026-09-28T23:33:34-0700 (`send_effect: sent`, attachment seen). Passive observation by the transport's `wait`; the answer is recorded verbatim under `### Answer` when it arrives. Cell 0 waits for this review; bounded implementer tasks T1–T2 (host subclass, placement planner) proceed in parallel as zero-fit engineering whose contract the review may still adjust. Nothing running on any node; 0 fits.

### 2026-09-29 — T1 + T2 implementation received (implementer, Opus/high); accepted with one open planner defect (T2b) and a disclosure
**Delivered (committed here):** `experiments/candidates/coupled_host_joint_skills_stage1/{host.py, planner.py, run_gate.py}` and tests (`tests/experiments/candidates/coupled_host_joint_skills_stage1/{test_coupled_relay_host.py, test_planner.py}`); 53 tests pass (21.75 s). DM read personally: the reward override (`r = ½(C_bh + S/D)`, S by the base `_compute_uav_frontend_capacity` under the `i in routing_paths` condition, D constant at construction, no clip; the original normalised reward kept as a diagnostic by calling the parent), the A2A switch (`a2a_enabled` set before the base constructor, UAV–UAV adjacency cleared after the base update; observations unaffected), and the budgeted single-start coordinate descent. Deviations accepted: test file renamed (collection collision), `require_admission` inside `main()` as in the readiness runner (AST check passes), `--smoke-no-admission` refused on panel worlds or outside `temp/`, min-makespan target assignment in the closed-loop executor, far-cluster membership from the generator's index layout with a replay check, extra diagnostic keys.
**Planner defect (T2b, design fix owed by the DM before cell 0):** all links (UAV–user, UAV–UAV, UAV–BS) are 23 dBm free-space at 2 GHz with a 3 dB threshold → ≈ 1.19 km 3-D range; a midpoint relay on a BS→centroid line links both ways only if the centroid is within ≈ 2.38 km of the BS, so for far clusters every k-means candidate scores exactly 0 and single-UAV ±100/50 m moves cannot leave the zero plateau (smoke on non-panel worlds 9001/9002: all candidates 0; on 9001 P_relay .046 < stationary floor .080). A gate failure with this search would be a search artefact, not a host fact. Fix declared: range-aware candidate generation (relay chains along BS→centroid lines with spacing ≤ 1.1 km, as many relays as the distance needs; enumeration of served-cluster subsets under the six-UAV budget), multi-start descent from the top-3 candidates, and a plateau tie-break (distance to the nearest routed node) — same budget, same rules for P_relay and P_flat (P_flat's generator has no chains and only direct-range service positions). Budget unchanged at 3,000 evaluations (≈ .57 ms each; ≈ 7 s per world projected).
**Disclosure:** while debugging, the implementer statically evaluated the three k-means candidates (A2A on, no descent, no P_flat) on dev worlds 1000–1002 (k=4/5/6: .259/.137/.103; 0/.123/.124; .447/.126/.339). These are three of the 32 gate worlds, candidate scores only, under the pre-fix generator; recorded so the gate reading is not presented as blind. No learner has seen any world.
**Hazards carried to T3 (runner):** host step ≈ 1.84 ms (≈ 11 min of environment time per 360k fit, not 4.5); obs_dim 90 / state_dim 119 (ACG's S1 guard 133/104 must be lifted; state is raw metres plus step fraction, no BS/link/routing fields); the env does not clip actions (√3·30 m/s diagonal) — the runner clips; `reset()` without a seed advances the world stream — training episodes use explicit recorded seeds; the hop feature cannot tell "unrouted" from "one relay" (2/3 direct, 1.0 otherwise); observed neighbours come from `uav_sinr_matrix`, not `uav_connections`; BFS with `max_hops = 3` allows up to three relays; terminations True at step 500 with truncations False (bootstrapping choice declared in T3); `sinr_matrix`/`uav_positions` are mutated in place (copy before storing); the throughput term is small in practice (S/D ≈ .06 for a UAV whose worst user is 500 m away), so the contract reward is dominated by C_bh — Pro was asked whether to re-weight before cell 0; no change until its answer.
**P_flat closed-loop reference:** executes in the host environment with A2A on (the environment the learners act in; incidental relays may form) — this is the "all-serve layout" reference; the A2A-off closed-loop reading is added as a diagnostic in T2b.

## 2026-09-29 07:15 UTC — T2b accepted: placement-search plateau fix (zero fits; smoke on non-panel worlds only)

**Delivered (committed here):** `planner.py`, `run_gate.py`, `tests/.../test_planner.py`; 83 tests pass (22.3 s; same pytest command as the T1/T2 entry). Implementer (Opus/high) built the range-aware generator, multi-start descent, plateau tie-break, action clip and the flat parked-candidate family; the DM added the final two search rules directly and read the whole diff.

**Search as accepted (replaces the T2 rule; the declared budget 3,000 and the gate threshold are unchanged):**
- Link ranges derived from the host constants (free space, 2 GHz, 23 dBm, −80 dBm, 3 dB): 3-D link range 1,193.7 m; direct BS reach at the 100 m service height 1,191.6 m horizontal (`planner.link_ranges`). Relay spacing 1,100 m (constant `RELAY_SPACING_M`; the DM's "3,400 m needs 2 relays" example was wrong: ceil((3,400 − 1,191.6)/1,100) = 3, tested at boundary fixtures derived from the constants).
- Candidates, all evaluated statically before descent: (1) the three plain k-means layouts (k = 4, 5, 6; the T2 midpoint rule, kept as a family); (2) relay family: for each k = 5, 4, 6 solution, every served-centre subset whose need (one service UAV at the centre plus `ceil(max(0, d − R_direct)/1,100)` relays on the BS→centre line, first leg ≤ R_direct, no relay sharing) fits six UAVs; a centre needing more relays than the router can chain (`max_hops` = 3) is excluded with a recorded reason, never scored zero silently; (3) flat family: every centre served by one UAV parked at min(d, R_direct − 1 m) along its BS→centre line, same subset enumeration, no relays. Leftover UAVs go to the largest unserved cluster (relay: its centre; flat: its parked point), else above the BS. **The relay search evaluates families (1)+(2)+(3) with A2A on; the flat search evaluates (1)+(3) with A2A off**, so the flat search's candidate set is contained in the relay search's and the static gate cannot go negative through candidate coverage alone (DM rule, after the implementer's two-sided artefact analysis: the v1 flat family had 3–6 candidates against 49–63 and overstated G ≈ .26; the v2 parked family alone left the relay search without the parked layouts). Duplicate layouts (the k = 5 and k = 6 solutions share centres) are removed before ranking, so the three starts are distinct.
- Multi-start coordinate descent from the top-3 candidates (contract reward, ties by index), the remaining budget split equally; per start the T2 axis moves 100 m → 50 m; accept a strict reward improvement or, at equal reward, a strict decrease of the plateau potential (sum over unrouted UAVs of the distance to the nearest node they could route through: the BS, plus routed UAVs when A2A is on). Best start returned; histories record `descent` and `plateau` moves separately. Converged starts do not pass unused budget on.
- Closed-loop executor clips the normalised action to the unit ball (the env does not clip; tested: per-step displacement ≤ 30 m). `run_gate.py` records five references with labels: `closed_loop_relay`, `closed_loop_flat_a2a_on` (the competence reference, host env), `closed_loop_flat_a2a_off_diagnostic` (diagnostic only), `stationary_floor`, `random_floor`; link ranges, candidate counts per family, duplicates removed, excluded centres and the best start per world.

**Smoke (non-panel worlds 9001–9003, budget 3,000, `--smoke-no-admission`, output `temp/directions/coupled_host_joint_skills_stage1/scratch/smoke_dm_t2b_v3/`; descriptive, not the gate):**

| reading | value over 3 worlds |
|---|---|
| static G = P_relay − P_flat | mean .166, SD .023 (min .141, max .188) |
| static G_C (backhauled coverage) | mean .313 (min .26, max .34) |
| P_relay / P_flat static contract reward | .600 / .434 |
| closed-loop final-100 contract reward, relay / flat (A2A on) | .600 / .434 |
| closed-loop final C_bh, relay / flat (A2A on) | .82 / .51 |
| far-cluster backhauled share at the end, relay | 1.00 on all three |
| candidates, relay / flat search | 157–170 / 111 (1–2 duplicates removed) |
| evaluations used, relay / flat (of 3,000) | 775–836 / 615–687, every start converged |
| cost | ≈ 5.9 s wall ≈ CPU per world, 18.4 CPU s total, peak RSS 50 MB → the 64-world gate is minutes |

The relay best start was a relay-family subset layout on all three worlds; the same G as the parked-family-only run (v2), i.e. adding the flat layouts to the relay search changed nothing on these worlds. The v1 value (G ≈ .26) is withdrawn as a search artefact.

**Remaining search effects (recorded, not fixed):** single-UAV axis moves cannot shift a relay chain as a unit; heights fixed at 100 m (same for both searches); converged starts' unused budget is not redistributed; the relay generator's leftover rule can park UAVs at an unreachable centre. All bias G downward or are symmetric; none can make a zero gate look like a host fact on a world where some centre lies beyond direct reach. A genuine zero is a compact world with every centre inside R_direct.

**Standing:** the Pro §5 declaration review is still unread (two `wait` observations ended in the transport's "browser recovery budget exhausted": send confirmed with the attachment seen, no login/challenge state, Chrome and CDP alive, the conversation bound three times before each loss; a third observation is armed — observation only, never a resend). No cell-0 launch, no fit, no change to the reward contract or the budget before that answer is dispositioned. Zero fits.

## 2026-09-29 07:40 UTC — DM disposition of the Pro §5 declaration review (`b01-declaration-review`): MATERIAL_DISSENT accepted and closed by this revision

**Record facts.** The owner inserted Pro's review document under `### Answer` (805abef99, "Record pinned-source b01 declaration review in Answer only"; pinned source cf62cef7b, blob 66cc1866d re-read by Pro before writing). The transport's third `wait` later captured the chat-form text of the same review (15,623 chars, sha256 `c56947f2…`, receipt commits 164c05f22/cf62cef7b; "chat answer", math rendered as expanded fragments); it stays in the local operation scratch. A copy into the direction docs was denied by the auto-mode classifier (sensitive-source provenance) and is not pursued; the owner may place it if wanted. Two earlier `wait` observations had ended in "browser recovery budget exhausted" with the send confirmed; no resend occurred. The DM read the inserted body in full and verified its code claims directly: free-space SINR at the 50 m minimum height for a user directly below is 30.5582 dB (q = 1.01859), so `S/D ≤ 1.0186`, `r ≤ 1.0093` and D is a **reference scale, not a bound**; `use_central_snapshot_in_flat_actor` is native (`hmasd/networks.py` 1586) but ACG's SET actor and StateSetEncoder live in `agent_count_generalization/models.py` (obs 104 / concat 721 / state 133 asserted; `build_agent` refuses any non-`off` interruption mode, 199–205); `HOST_CONTRACT_KWARGS` already pins `bandwidth = 20e6`, `channel_model`, `max_hops = 3`; `use_shadowing` is the base default False and not yet pinned; the BFS stops expanding at `len(path) >= max_hops` so a path may hold up to three relays (four links), as `planner.max_routable_relays` states.

**Verdict adopted: keep D2, keep the reward contract (D and the two halves), keep the 3,000-evaluation budget, the static gate `G ≥ .05` and the six-fit comparison intent; close the declaration on the four points before any training.** Pro's "current draft is not yet an executable contract for the probe and the six formal fits" is accepted. Pro's ranking of the remaining issues (P2 mixes static and closed-loop scales; P3/B12 has no closed statistical spec; the ACG adaptation omits the actual model implementation; cost mixes elapsed process-hours with cumulative CPU-hours) is accepted as written. Item by item:

1. **Host and execution semantics (declaration amended).**
   - D is the 30 dB *reference* scale; no clip; the bound above replaces "S/D ≤ 1". B = 20 MHz is a constructor parameter fixed explicitly by this direction (already asserted); `use_shadowing = False` is added to the contract kwargs and asserted (T3 host edit). Hop semantics: `max_hops = 3` permits up to three relays / four links; diagnostics report actual link counts and path existence, not the legacy normalised hop feature.
   - The **capacity–coverage trade-off is accepted and reported, not removed**: a move that drops one weak backhauled user (ΔC_bh = −.02) while lifting a serving UAV's worst SINR from 3 to 20 dB gives Δ(S/D) ≈ +.085, Δr ≈ +.032 (Pro's arithmetic on the code formula; a conditional example, not an observed event). Consequence: every panel reports C_bh and S separately, per-step association changes and backhaul-loss events are logged, and P4 carries a coverage check (item 4). No re-weighting of the throughput term before cell 0 (Pro concurs; the DM's earlier "S/D ≈ .06" was the contribution of **one** active serving UAV (.364/6), the fleet's is ≈ .24–.30 with four or five such UAVs — DM error corrected).
   - **Action feasibility is made identical for every actor**: the host subclass clips each UAV's normalised action to the unit 3-ball inside its own `step` (direction-owned override; clip events counted in `info`), so learners and the placement-plus-executor references fly under one rule (L2 speed ≤ 30 m/s). The planner's executor clip stays (now redundant, identical). Pro's alternative (native per-axis box for all) is not taken: the L2 rule is the physically meaningful one and is applied uniformly.
   - Fresh-state acceptance tests are added (T1b, inside T3): coordinate change → cache invalidation → SINR/association → routing under the A2A switch → reward, in that order; BS disconnect/reconnect; A2A off on every graph update including closed-loop execution (already exercised by the A2A-off closed-loop diagnostic); terminal step; UAV with no users; `max_connections` reached; the weak-user boundary example; the original reward stays a diagnostic. Far-cluster membership continues to come from the generator's own index layout with a replay check (T1); the panel row stores the generated centres. 6 km fallback: the generator's user spread scales to 600 m (std = area/10) — recorded.
2. **Opportunity gate and references (declaration amended; all before any dev gate result).** Names: `P_relay^on` (relay layout, host env), `P_flat^on` (A2A-off-planned layout executed in the host env; **the competence reference**), `P_flat^off` (planned and executed with A2A off; diagnostic only). Static gate unchanged: `G = P_relay − P_flat^off(static) ≥ .05` on dev, one 6 km fallback. **Added prospective condition:** closed-loop dev coverage opportunity `G_C,dev,cl = mean_w[C̄_bh(P_relay^on, w) − C̄_bh(P_flat^on, w)] ≥ .05` (500-step means over the 32 dev worlds; ≈ 2.5 users of service difference; a practical floor, not a power claim). If the static gate passes and this fails: "static relay opportunity exists, the coverage-capability comparison is not established" — no learner fit, no blame on learners. Static G_C is still reported. Search rules fixed now (T2b + this entry): 3,000 evaluations per arm per world **total** across candidates and all starts; the flat search's found layout is evaluated with A2A on as one extra incumbent of the relay search (one evaluation inside the budget) so `G ≥ 0` holds by construction; descent adds ±z moves (50 m, clipped to [50, 150] m) and a final 25 m stage (100 → 50 → 25 m); per-start incumbents at 1k/2k/3k cumulative evaluations are recorded; results are read as **best found**, never as global optima. Hold-out references are generated only on the arena chosen from dev and then sealed. The references are named "budgeted placement-plus-executor references" (min-makespan assignment, straight flight, hold); they bound ordinary deployment competence, they do not exhaust ordinary path planning. Disclosure kept: candidate scores on dev worlds 1000–1002 were seen in the T2 smoke before the T2b revision; the panels are not changed and no pre-declaration is back-dated.
3. **Recipes and adaptation (declaration amended).** The learner packages are ACG's actual implementations, not a plain-agent stand-in: a direction-owned copy of ACG `models.py` keeps the StateSetEncoder over the scaled 8-slot/validity 133-dim adapter state (six valid slots; the same native 119-dim information, positions scaled, no extra world information) and the SET actor adapted to obs 90 (concat 693; all asserted widths and linear layers changed together); a direction-owned `build_agent` admits the fixed-cap `d2` for H (`skill_cap_k_max = team_cap_k_Z = 10`, both interruption costs ∞, age feature off, HA-CTSE off; acceptance: only reset/team_cap causes, six agents synchronised) and the native `off` path for SET; all replaced modules must update (ACG's motion checks). Readers load checkpoints strictly through the same factory. The d2 rationale is corrected: `off` also sets the cap attributes; d2 is chosen because B12's collection protocol requires `d2_enabled`. Reward identity per step: `N × adapter scalar = ½(C_bh + S/D)`. Observation layout recorded in the matching table (own [0:3], users [3:63] with normalised SINR as the third entry, UAV slots [63:87] with normalised SINR fourth, time [87], BS connection [88], legacy hop [89]). Terminal treatment stays ACG's for both arms (`last_values` zeros, `dones` True at step 500) — no new recipe difference; the runner reports how the update consumes it. Seeds are paired in declared order (931201↔932201, 931307↔932307, 931413↔932413) and **paired arms share the training-world sequence by construction** (world seed a function of the seed's last three digits, lane and episode; never a panel world). The matching table is extended to Pro's list (encodings and snapshot timing, reward units and H auxiliary weights, γ/GAE, value/obs/state norms, learning rates and schedules, PPO clipping and gradient norm, batch units and actual optimizer calls, parameter counts and information entry points, reset/bootstrap rule, frozen evaluation, CPU dtype/threads, RNG roles, final-45 no-selection rule); "equal update count" means the outer rollout and low-level update schedule only.
4. **Predictions and outcome rows (declaration amended).** P1 unchanged. **P2:** `G_C,ho,cl = mean_w[C̄_bh(P_relay^on, w) − C̄_bh(P_flat^on, w)]` and `L2(a, s) = mean_w[C̄_bh(a, s, w) − C̄_bh(P_flat^on, w)] − ½ G_C,ho,cl ≥ 0`, all 500-step means on the same 32 hold-out worlds, deterministic actions; final-100 and final-step values are named secondary readings; if `G_C,ho,cl < .05` the opportunity did not transfer and P2 is unreadable. Far-cluster share > 0 stays descriptive, reported with that cluster's A2A-path user-time. **P4:** `r_H − r_SET ≥ +.03` on the contract scale **and** paired `ΔC_bh(H − SET) ≥ 0` (point check, no non-inferiority claim); a reward win with lower primary coverage is listed as "capacity–coverage trade-off", not as a better coverage package. **Cell 2 condition:** the same ≥ 2 paired seed blocks satisfy P2(H), a valid P3, P4 and the coverage check. Report all three L2, paired Δr and ΔC_bh per block; no checkpoint selection; sampled mode never replaces the deterministic endpoint. Outcome rows re-layered (technical → opportunity → capability → package → mechanism) as Pro's table; "P3 fails ⇒ additive" is replaced by "the tested interaction is unsupported or unresolvable"; the modal outcome reads "P1 holds; one or both learners below P2, or the interaction unresolved; cell 2 not bought". Odds stay the DM's subjective expectations.
5. **P3 becomes an executable statistical pre-specification (T4, priced and accepted before any fit; without it there is no P3-based cell 2 purchase).** Unit = the ten-step commitment on the final H checkpoint (cap 10, frozen weights and normalisers, zero optimizer steps): 12,800 commitments per checkpoint (128k steps) in ≤ 256 lane-episodes, clustered by true world id; response = the segment's mean team r; records: pre-commitment state, time, label vector, pre-commitment roles and paths, executed actions, time-aligned rewards. Reduced model: pre-specified pre-commitment state/time controls + agent-index-specific single-label additive terms. Full model: + a label-count quadratic basis on independent contrasts (Σ n_z = 6 fixed) + relay-service / relay-pair terms with **pre-commitment** roles (relay = interior node of another UAV's BS path at segment start). Rank/condition checks on the actual support; failure = "unreadable", never "interaction zero". One omnibus statistic: held-out MSE reduction of full over reduced under fixed world/episode-grouped cross-validation; calibration = wild-cluster multiplier bootstrap of whole-episode residual vectors under the reduced-model fit, 1,000 draws; pass if the observed improvement is positive and above the 95th percentile. Placebo: the team-label regression stays a conditional diagnostic plus a structural zero check (with individual labels, state and hidden state fixed, a team-label input change must not change the executed action; verified on the new networks, not assumed). Synthetic acceptance: strong-additive + state-dependent labels + within-episode correlation null; a known pair interaction positive; rank failure; reward scaling. Wording of a positive: "pre-specified non-additive predictive structure on a competent checkpoint" — no acquisition or causal-coordination claim. Cost of T4 is priced in its L0 note.
6. **Cost accounting and stop priority (declaration amended).** The timing probe is **not zero fits**: cell 0 = zero formal scientific fits plus two recorded technical training probes (3 full rollouts per arm = 24k team steps each, 48k total, run after the gate/fallback decision and contract freeze; only timing/RSS used, never learner scores). Wall and `getrusage` CPU are metered separately per process; the **20 CPU-hour cap covers the six fits, all declared panels, the B12 collections and the 1,000 refits** (readers metered too); priority: total cap > completing seeds — an unfinished arm stays unreadable rather than over-spending or silently dropping readers; ACG checkpoints are not a resume contract. Concurrency starts at **two** fits; a third only after the probe measures the overlap peak (learner alive while the evaluation agent is built; PPO update peak) and the node's actual headroom. Exposure: 2.16 M training + .576 M evaluation + .384 M B12 collection = 3.12 M team steps plus the 48k probe; gate: up to 576k static evaluations (two arenas dev + hold-out) — at the measured ≈ 5.9 s per world (search + five references) the 64-world evaluation of one arena is ≈ 6–7 min, so "minutes" now rests on a measurement. Engineering cap 40 h stands; the models migration, fresh-state tests and the statistics rewrite are counted inside it; the DM reports consumed hours at the end of cell 0.
7. **D1′:** stays RECORDED / not declared / not bought. Declare only after D2's cell-0 gate, the ordinary deployment readings and the timing probe — not after a learner positive. Contract gaps to close first (Pro §7, accepted verbatim into the D1′ candidate's to-do): identical feasible set for the ordinary correction (offset reference frame, XY disc, height, accumulation, clipping, executor, action norm; zero-correction incumbent; competitive multi-direction fine steps), the exact meaning of "300 evaluations", the macro-time contract (36k macro decisions per fit; 800 per rollout; γ^10 boundary), identity checks of the deterministic zero offset against the anchor, the anchor cost (6.48 M evaluations for 2,160 training episodes at 3,000 each unless cached — cache hits must name their worlds), and outcome rows with a practical band and an unresolved branch. A D2 gate failure does not migrate into D1′.

**Owner items:** none new; [DECIDE-2] stands accepted, [DECIDE-1] stands unexercised.

**Next §5 point:** the revised declaration, the cell-0 readings (gate, `G_C,dev,cl`, references, probe timing) and the T3/T4 acceptances go to one independent review before cell 1; no further selection round. Until then: T3 (runner, models adaptation, host clip and `use_shadowing` pin, fresh-state tests, per-step trade-off logging) and T4 (B12 pre-spec reader) are engineering with zero formal fits; then the cell-0 gate launch through `scripts/hmasd_launch.py` on `local_linux`. Zero fits.

**Time correction (2026-09-29 07:19 UTC):** the disposition entry above is stamped 07:40 UTC in error; it was written at 07:17 UTC (`date -u` at the append).

## 2026-09-29 07:45 UTC — T2c accepted: gate revisions of the disposition (item 2) implemented; numbers provisional until the host action clip lands

**Delivered (committed here):** `planner.py`, `run_gate.py`, `test_planner.py`; 97 tests pass (83 + 14). DM read the diff. As declared: descent moves ±x/±y at stage steps 100 → 50 → 25 m plus ±z by 50 m at every stage (heights clipped to 50–150 m); the flat search runs first and its found layout is evaluated with A2A on as the relay search's extra candidate (`flat_result_incumbent`, inside the budget, eligible as a start); incumbents snapshotted at cumulative evaluations 1,000/2,000/3,000 (overall and per start); reference names `P_relay^on` / `P_flat^on` / `P_flat^off`; `G_C_dev_cl` (closed-loop 500-step mean C_bh, relay minus flat-on) with the declared threshold .05 beside the static gate threshold; per-reference association-change counts and backhaul-loss events per step. **Property test added and passing:** on 400 random layouts (5 non-panel worlds) A2A on vs off leaves the user association identical, routes a superset, and never lowers C_bh, S or r (A2A strictly raised C_bh in 94 of 400) — the premise behind "flat candidates inside the relay search ⇒ G ≥ 0" holds on this host.

**Smoke (9001–9003, budget 3,000, committed `host.py` before the T3 action clip — provisional):** G .155 ± .026; static G_C .313 ± .046; **G_C_dev_cl .263 ± .058** (min .195); every start converged at the 25 m stage after 900–1,200 evaluations, so the budget did not bind and the 2k/3k snapshots equal the finals; the flat incumbent scored exactly its A2A-off value on all three worlds (never a top-3 start); ≈ 3 s wall ≈ CPU per world, peak RSS 51 MB.

**Host facts surfaced:** (i) with height free, **every UAV in both searches descends to the 50 m floor** — nothing in the contract prices height, lower is closer to ground users (better SINR) and the BS gap shrinks; symmetric across the two searches, so the gate is unaffected, and the learners have the same option; recorded as a property of this host, not corrected. (ii) The declared 3,000 budget is not binding for this search at 5 km; it stays as declared (no reduction after seeing results). The gate re-smoke after the T3 host clip is the DM's, before any dev launch. Zero fits.

**Time correction (2026-09-29 07:26 UTC):** the T2c entry above is stamped 07:45 UTC in error; it was appended at 07:26 UTC. Headings are now taken from `date -u` at the append.

## 2026-09-29 07:55 UTC — T3 accepted: cell-1 runner package, host action clip, fresh-state tests; gate re-smoke after the clip

**Delivered (committed here):** `host.py` (contract adds `use_shadowing = False` asserted; `step` clips every UAV's normalised action to the unit 3-ball before the parent step and counts clip events; caller arrays never mutated), `adapter.py` (`ContractCountAdapter`: ACG's scaled 8-slot/validity 133-dim state over the host, six valid slots, obs 90 untouched; `reset(seed=None)` refused; per-step identity `6 × scalar = contract_reward = ½(C_bh + S/D)` on the host's own keys; training-world rule `300000 + (seed % 1000)·100 + lane + episode·10000`, never a panel world, shared by paired seeds), `configuration.py` (ACG FitSpec; H = `d2` with `skill_cap_k_max = team_cap_k_Z = 10`, both interruption costs ∞, age feature off; SET = `off` + central snapshot; matching table with Pro's full list incl. the observation/state layouts and the d2 per-step cost asymmetry), `models.py` (direction-owned copy of ACG's: StateSetEncoder unchanged, SET actor at obs 90 → concat 693, `build_agent` admits the fixed-cap d2 for H and `off` for SET, `assert_route` on every build; θ₀ of the d2 displacement metric recaptured after module substitution), `runner.py` (ACG loop; explicit per-episode world seeds; d2 acceptance per rollout: no gap/team-gap/cap causes, decisions = team decisions with six agents sampled, one per 10 steps; terminal facts recorded per rollout; dev panels at 0/15/30/45, hold-out deterministic + sampled at 45, 32 worlds as two 16-lane chunks; readers per world incl. far-cluster A2A-path user-time, relay-position share by agent, association changes, UAV/user backhaul-loss events, clip events, label entropies; `--probe` = 3 full rollouts + one timed panel-sized run without scores; `resource.getrusage` + `/proc` RSS incl. the evaluation-overlap peak; `require_admission` once inside `main()`), tests (+11 host fresh-state tests, 15 runner tests; file renamed by the DM to `test_contract_runner.py` to avoid the basename collision with ACG's `test_runner.py`). Direction suite: **129 passed** (94 s). ACG suite unchanged (216 passed, 1 skipped, 8 errors in `fresh_world_deployment_b17` for a checkpoint absent from this checkout — pre-existing, not touched). DM read the host diff, adapter, configuration, models diff and the runner in full. DM change: the probe's timed panel-sized run uses non-panel worlds 9000–9031 (never the declared panels).

**Facts established by the implementer and accepted:** `validate_config` accepts d2 with rollout 500 / k 10 (requires `interruption_delta = 1`, costs ≥ 0, `1 ≤ k_max ≤ k_Z ≤ episode_length`, `rollout_length % episode_length = 0`); `hmasd/agent.py` 491–505 sets the same cap attributes in `off` mode, so d2 is chosen only because B12's collection needs `d2_enabled`; `use_central_snapshot_in_flat_actor` is refused together with d2 (agent.py 507–516), hence SET on `off`. **Terminal treatment (both arms, ACG rule):** `compute_advantages` multiplies `last_values` by (1 − done), so δ₄₉₉ = r − V; in d2 every open segment closes with `terminal = True` on the done step and the coordinator bootstrap from `last_state` is discarded (utils 1560–1570); SET skips `update_coordinator` and stores no high-level rows. No new recipe difference. **SET concat width 693** (2·128 + 1 + 2·90 + 256). Smoke (2 lanes, hidden 32, 500 steps): env ≈ 1.1–1.2 ms/step; H policy ≈ 3.1 ms/step of which ≈ 2.35 ms is d2's per-step teacher-forced coordinator forward (`evaluate_held_batch`, run every non-reset step even with infinite costs) — SET pays none of it; the probe measures this at full width.

**Hazards recorded:** the unit-ball clip binds on ≈ 80 % of UAV-steps at initialisation (PPO stores the unclipped action and log-probability; the host executes the clipped one — same for both arms; early panels read accordingly); the declared H time estimate (from ACG's `off` route) omits the d2 per-step cost; checkpoints are evaluation weights only (`config` stores ∞ as "inf"); the panel readers import `planner.cluster_layout` (one far-cluster rule shared with the gate).

**Gate re-smoke with the host clip (9001–9003, budget 3,000, `smoke_dm_t3_v4`):** G .155 ± .026 (min .126), static G_C .313 ± .046, **G_C_dev_cl .263 ± .059 (min .196)** — identical to the T2c values (the executor was already unit-ball clipped); random floor .097 (was .096–.10 range), ≈ 6.5 s wall per world (node loaded). The T2c smoke numbers are no longer provisional. Zero fits.

## 2026-09-29 08:02 UTC — Cell 0 dev gate READ: both declared conditions pass at 5 km (P1 holds); hold-out references and technical probes launched

**Launch:** `scripts/hmasd_launch.py launch --direction coupled_host_joint_skills_stage1 --lead "Claude DM (WSL session)" --sha f589523191c670e215e3d719fc4f2cd01492c301 --output runs/coupled_host_joint_skills_stage1/b01_gate_dev_a01 --node local_linux --snapshot -- experiments/candidates/coupled_host_joint_skills_stage1/run_gate.py --worlds 1000-1031 --area-size 5000 --budget 3000 --out runs/coupled_host_joint_skills_stage1/b01_gate_dev_a01` (snapshot mode because the shared working tree held another writer's untracked file under `experiments/`; the gate reads no `runs/` inputs). Accepted 07:58:25 UTC, exited 0 at 08:00:33 UTC; 128.8 CPU s, peak RSS 91 MB, ≈ 4.0 s per world. Committed here: `summary.json` and the launcher's admission/manifest/status/exit records; `worlds/` (11 MB of candidate lists and descent histories) stays in the run directory as the durable copy (not committed; logs are ignored by `.gitattributes`/`.gitignore`).

**Reading (rule fixed before the numbers: pass = static G ≥ .05 AND G_C,dev,cl ≥ .05, both as 32-world means):**

| reading (32 dev worlds, 5 km, budget 3,000) | mean | SD | min | max |
|---|---|---|---|---|
| static G = P_relay − P_flat^off | **.106** | .054 | .030 | .282 |
| static G_C (backhauled coverage) | .190 | .111 | .020 | .500 |
| **G_C,dev,cl** = closed-loop 500-step C̄_bh, P_relay^on − P_flat^on | **.152** | .094 | −.010 | .403 |
| P_relay static r / C_bh | .610 / .876 | .045 / .095 | | |
| P_flat^off static r / C_bh | .504 / .686 | .074 / .140 | | |
| closed-loop r (all 500 / final 100): P_relay^on | .561 / .610 | | | |
| closed-loop r (all / final 100): P_flat^on | .480 / .504 | | | |
| closed-loop r: P_flat^off (diag.) / stationary / random | .471 / .115 / .117 | | | |
| closed-loop C̄_bh (all): P_relay^on / P_flat^on / floors | .810 / .658 / ≈ .18 | | | |
| far-cluster backhauled share at the end: P_relay^on / P_flat^on | .891 / .300 | | | |
| evaluations used, relay / flat (of 3,000) | 1,143 / 869 | | 896 / 519 | 1,537 / 1,239 |

**Both conditions pass** (P1 held; the DM's prior was ≈ 70 %). Every search converged at the 25 m stage; the budget never bound. Spread is real: on 5 of 32 worlds one condition is below .05 (1005, 1006, 1014, 1026, 1031), and on world 1031 the closed-loop coverage gap is −.010 — the relay layout's deployment does not pay on every world; the opportunity is a mean effect of ≈ 7.6 users' service (.152 × 50) with world-to-world SD ≈ 4.7 users. No fallback is used (the 6 km fallback exists only for a failed 5 km gate). Cost so far in this line: 0 fits; ≈ 2 CPU-min for the gate.

**Decided by this read (nothing else changes):** (1) hold-out references at 5 km (`--worlds 2000-2031`, same command, tag `b01_gate_holdout_a01`) — generated now and **sealed**: they are P2's comparators, recorded without interpretation until the hold-out panels are read; (2) the two technical probes through the launcher (`runner.py --probe`, arm H seed 931201 and arm SET seed 932201, 3 full rollouts = 24k team steps each plus one timed panel-sized run on non-panel worlds 9000–9031; not zero fits; timing/RSS only, no learner score is used for any research parameter); (3) the six formal fits wait for T4's acceptance and the probe projection against the 20 CPU-hour cap.

## 2026-09-29 08:31 UTC — Hold-out references sealed; technical probes read: the declared 20 CPU-hour cap is mis-priced by 2–5× (DM error); [DECIDE-3] on where and whether to buy the six fits

**Hold-out references** (`b01_gate_holdout_a01`, worlds 2000–2031, 5 km, budget 3,000; accepted 08:03 UTC, exited 0; 252 CPU s; summary and launch records committed a745bc786, `worlds/` 11 MB in the run directory): generated from the dev decision only and **sealed** — the DM has not read its G, G_C or reference values and will not until the hold-out panels are read.

**Technical probes** (`b01_probe_H_a01` H seed 931201; `b01_probe_SET_a01` SET seed 932201; 3 full rollouts = 24k team steps each + one timed 32-world panel-sized run on non-panel worlds 9000–9031; both exited 0; records committed a745bc786; `training.jsonl` is git-ignored and stays in the run directory). Node load during the probes: 17–23 on 16 cores from the owner's other projects (node tests, playwright, the Codex app), plus the hold-out gate and both probes together. **Not zero fits: 48k technical training steps consumed.**

| probe (local_linux, CPU float32, torch_threads 4, loaded node) | H (d2) | SET (off) |
|---|---|---|
| wall per rollout: collection / update / total | 80.6 / 346.7 / 427.5 s | 44.3 / 259.6 / 303.9 s |
| CPU per rollout | 1,397.7 s | 989.7 s |
| ms per team step: env / policy / store / update | 2.29 / 6.57 / 1.15 / 43.3 | 2.39 / 2.92 / 0.14 / 32.5 |
| CPU ÷ wall (training) | 3.27 | 3.26 |
| timed panel run (32 worlds): wall / CPU | 119 / 338 s | 85 / 175 s |
| **projection per fit (45 rollouts + declared panels): wall / CPU** | **5.5 h / 18.0 CPU-h** | **3.9 h / 12.7 CPU-h** |
| peak RSS (VmHWM = ru_maxrss) | 2,216 MiB | 879 MiB |
| d2 acceptance | causes reset 16 / team_cap 784 = 800 decisions, no gap/cap; six agents synchronised | — (0 high-level rows) |
| terminal facts | dones all True at step 500 only; all last d2 rows terminal; 0 open segments | same low-level facts |
| action clip events per rollout (of 48,000 UAV-steps) | 38.7k–39.8k | 38.5k–40.0k |

**Contention adjustment (declared as an estimate, not a measurement):** the single-threaded host step went from 1.1–1.2 ms (T3 smoke, load ≈ 10) to 2.3–2.4 ms in the probes (load 17–23); that ≈ 2× is contention and SMT inflation of CPU seconds, not recipe. Contention-adjusted: ≈ 9 CPU-h (H) and ≈ 6.4 CPU-h (SET) per fit, six fits ≈ 46 CPU-h; nominal six fits ≈ 92 CPU-h (+ ≈ 1 CPU-h for three B12 collections + the refits). **Either row exceeds the declared 20 CPU-hour cap by more than 2×, so the conclusion does not depend on the adjustment.** Two concurrent fits fit the memory (≈ 3.1 GB H+SET, ≈ 4.4 GB H+H against ≈ 9 GB free; the evaluation-overlap record showed no extra peak at the target build, and VmHWM equals ru_maxrss).

**DM error, recorded:** the declaration's cell-1 cost ("7–11 process-hours", cap 20 CPU-h) was projected from ACG's 62–99-minute fits, which ran on `wsl_4070` (CPU float32, torch_threads 4); the cap was a wsl_4070 number applied to `local_linux`. Here the update phase alone is 81–85 % of a rollout's wall (347 s H / 260 s SET) against ≈ 85–130 s for a whole rollout on that node; the gap is mostly hardware and load, d2's collection cost (80 vs 44 s per rollout) is a secondary term. Pro's warning that the cost was not a verified quotation was right.

**Disclosure:** reading the probe records the DM saw the training team-reward means of the three probe rollouts per arm (H .122/.074/.107; SET .100/.085/.083, 16-lane means). No parameter, seed, threshold, cap reasoning or reader uses them; they are not learner results (3 rollouts, sampled actions, the fit restarts from scratch).

**[DECIDE-3] (owner; a resource choice reserved to the owner by the disposition's item 8; it does not block, because the six fits also wait for T4's acceptance):**
- **A (recommended): run the six fits on `wsl_4070`, CPU float32, torch_threads 4 — the node ACG's anchors come from; recipe unchanged, only the execution node.** Projection from the anchors × the d2 collection factor: H ≈ 1.2–2 h, SET ≈ 1–1.5 h wall per fit, ≈ 25–35 CPU-h for six at two concurrent (≈ 5–8 h wall); the cap is re-declared to **35 CPU-h** for fits + panels + B12 collections + refits. Needs one CONTROL message to Root for node time, the SPARSE-CONE rule on the node checkout (rsync every run at once), and the declared node amended before launch.
- **B: stay on `local_linux`**, cap re-declared to 100 CPU-h nominal, two concurrent, ≈ 15 h wall on the owner's working machine under its current load.
- **C: stop at zero formal fits on cost** — the relay opportunity is established (gate), the learner instrument stays unpriced; recorded under the pre-declared technical/metering row as a cost stop, no scientific claim.
- Not offered: two seeds (breaks §8 and the "2 of 3" rule) or fewer epochs/rollouts/lanes/threads (tuning after a probe that exposed learner scores; the stop rules forbid it).
Default if no owner word arrives by the time T4 is accepted: A (the DM sends the CONTROL message and launches pair by pair, 931201/932201 first). Cumulative cost in this line: 0 formal fits; 48k technical training steps; ≈ 2.2 CPU-h (gate 129 s + hold-out 252 s + probes 7,681 s).

## 2026-09-29 09:00 UTC — T4 accepted: P3 interaction reader (collector + reader), with the T4b support rule; 148 tests; ≈ 1 CPU-h per checkpoint collection

**Files (committed with this entry):** `experiments/candidates/coupled_host_joint_skills_stage1/collect_commitments.py` (commitment collector: 16 rollouts × 16 lanes × 50 ten-step commitments = 12,800 rows per H checkpoint; at each commitment start it records `env.snapshot()` after `agent.step` and before `env.step`, i.e. the pre-commitment state, the six team labels, routed/relay/serving roles and the relay-relation matrix; response = mean team r of the ten executed steps), `interaction_reader.py` (the pre-specified P3 reading), `tests/…/test_interaction_reader.py` (19 tests). Direction suite: **148 passed** (fresh basetemp `scratch/dm_t4b_suite_01`, 204 s). Implementer (Opus/high) from `L0_b01_T4_scope.md` plus the DM's T4b message; the DM read the support/readability/decision code and the collector's snapshot point personally.

**Reading (as implemented, verbatim strings written into every reading JSON):**
- Reduced model R = intercept, time, c_bh_t0, sd_t0, relay/routed/serving per UAV, agent-specific label one-hots (label 0 = reference); full model F = R + the SUPPORTED columns of the 72-column added block (15 label-count products `n_z*n_w` (z < w; squares are spanned by R), 36 ordered relay-service `rs_zto w`, 21 relay-pair `rp_z_w`).
- Support rule (DM, T4b, fixed on the design, never the response): "an added column is SUPPORTED iff its non-zero rows >= max(8, ceil(0.01 * rows)) (128 at 12,800 rows) AND its non-zero episodes >= 8; F = R + the supported columns of the 72-column block; unsupported columns are listed under missing_support.unsupported with their facts and are never treated as zero effects". "Episode" = one (lane, episode) pair = one independent 500-step trajectory in its own world (256 per checkpoint table); the same unit is the CV group and the bootstrap cluster.
- Readability: "READABLE iff (a) at least 10 of the 15 label-count-product columns are supported, (b) the rank increment of R + supported columns over R equals the number of supported columns (otherwise the spanned ones are listed and the reading is unreadable), and (c) all K folds are non-empty; the secondary products-only reading applies the same rule to R + the supported product columns".
- Statistic: Δ = mean over 8 grouped folds (fold = sha256("lane{l}:episode{e}") % 8) of held-out MSE_R − MSE_F; 1,000 wild-cluster Rademacher draws (one sign per episode, `default_rng(20260929 + b)`), null y* = fitted_R + e·w; pass = Δ > 0 and Δ > q95 of the null Δ*; computed by the exact linear-algebra equivalent of refitting (Gram route, checked against direct refits at rtol 1e-7). Primary decision = full supported block (`decision`); pre-declared secondary = the 15 products alone (`decision_products_only`); placebo = team-label one-hots (diagnostic only, not a veto). Wording: supported / unsupported / unreadable.
- Design consequence accepted: one spanned column among the supported ones makes the primary reading unreadable (listed by declared-order Gram-Schmidt); the products-only secondary is the pre-declared fallback for that case, and both are reported whenever either is readable.

**Synthetic calibration (40 seeds × 1,000 draws, 12,800-row tables from the T4 generator):**

| case | primary pass | products-only pass | notes |
|---|---|---|---|
| additive null | 0/40 (Δ > q95 in 0/40) | 1/40 (Δ > q95 in 3/40) | placebo 3/40; unsupported columns per table 1–20 |
| label-count product positive (+.03 when labels 1 and 2 are both held, 47 % of rows) | 40/40 | 40/40 | |
| relay-service positive (+.03 on ≈ 4 % of rows; information only) | 33/40 (Δ > q95 39/40) | 3/40 | expected: the effect is outside the product block |

No synthetic table was unreadable. CLI smoke on a synthetic table: 58/72 added columns supported (the 14 unsupported are mostly `rs_1*`/`rp_1*` and `rp_5_5`), rank increment 58/58, products 15/15, condition numbers R 9.2 / F 24.7 / products-only 22.8; 2.5 s, 192 MB. Structural fact (T4, unchanged): the team label does not reach H's actor (max |Δaction| over label swaps = 0.0; control 0.0167), so any P3 signal is about which joint contract was chosen, not about label-conditioned execution. Known limits: R's state terms are assumed correctly specified; R's condition number reads inf if every UAV is always routed (then the routed columns drop as zero-variance).

**Cost:** collection ≈ 1.0 CPU-h per H checkpoint on the contended local host (16 rollouts, no update); reader ≈ 3 s. Three checkpoints ≈ 3 CPU-h, inside the cap. Zero formal fits so far.

**Prior (recorded before any collection):** P3 primary supported on ≥ 2 of 3 H checkpoints ≈ 35 %; the products-only secondary alone supported ≈ 25 %. Both are reported; only the primary is the P3 reading.

## 2026-09-29 09:01 UTC — [DECIDE-3] default A executed (no owner word by T4 acceptance): the six fits move to `wsl_4070`; cap re-declared 35 CPU-h; launch mechanics and the CONTROL message

**Decision record.** No owner message on [DECIDE-3] arrived between its posting (08:31 UTC) and T4's acceptance (68e441f3e); the recorded default applies: **A**. Amended before any launch, nothing else in the declaration changes:
- Execution node for cell 1: `wsl_4070` (CPU float32, `torch_threads 4`, 45 rollouts, area 5,000 m, the declared dev/hold-out panels inside the runner, seeds H 931201/931307/931413, SET 932201/932307/932413 paired by position). The node's torch is 2.7.0+cu118 on Intel versus +cpu on AMD locally: numbers are not bit-identical to the local probes, and the whole batch (all six fits, their panels and the B12 collections) runs on the one node so every paired comparison is same-host. The probes stay as the cost anchors of record.
- Cost cap for cell 1: **35 CPU-h** (fits + panels + B12 collections + reader refits), replacing the mis-priced 20 CPU-h; two fits concurrent, launched pair by pair in seed order (931201/932201 first; the next pair when a pair has exited); each fit's CPU seconds come from its `process-exit.json`/summary. Stop rules unchanged: one fit per seed, no second seed, no extension after scores, no tuning.
- Node state observed at 16:58 UTC before launch: load 0.00 (no fit running), 14.9 GB available of 15.8 GB, 20 cores, 814 GB free; H peak RSS 2.2 GiB + SET 0.9 GiB ≪ the 4 GiB result floor's headroom. The node control checkout (`/home/wu/projects/HMASD`, HEAD c562b8fa9) carries a foreign local edit of `docs/research/RESEARCH.md` and two foreign bundles: the launches therefore only **fetch** the published head and the launch SHA (never pull/merge/checkout) and run from the launcher's locked snapshot worktree; the sparse cone already contains `experiments/` and `docs/research/`, so no `sparse-checkout add` is issued (SPARSE-CONE rule). Every run directory is rsynced to this checkout immediately at exit; checkpoints get a durable node copy under `/home/wu/hmasd-artifacts/coupled_host_joint_skills_stage1/<tag>/` before any node-side use.
- Launch entry: `experiments/candidates/coupled_host_joint_skills_stage1/launch_b01_fits.sh <sha> <arm> <seed>` (committed with this entry; issued from this host; tags `b01_fit_<arm>_<seed>_a01`; runner argv identical to the probes minus `--probe`). Launch SHA = the commit that carries this entry and the script (recorded in each run's launch record).

**CONTROL message to Root (one message, the owner-authorised channel, sent after the push of this entry; no reply owed):**

> [HMASD peer] CONTROL — Claude DM `coupled_host_joint_skills_stage1`: node time on `wsl_4070`. From now, six CPU fits two at a time (torch_threads 4 each, ≈ 8 cores, peak RSS ≈ 3.1 GiB per pair), ≈ 25–35 CPU-h in total, projected 5–8 h wall; outputs under `runs/coupled_host_joint_skills_stage1/b01_fit_{H,SET}_<seed>_a01` in the node checkout, rsynced off at exit; no `sparse-checkout` change, no pull/merge on the node checkout (its local RESEARCH.md edit is untouched), launches via `scripts/hmasd_launch.py --snapshot` at a pushed sha. If Root needs the node for a shared control, say so in the inbox and I stop after the running pair.

**Cost accounting at this point:** 0 formal fits; technical: 48k probe steps, gate/hold-out/probe ≈ 0.6 CPU-h, T4 synthetic calibration ≈ minutes. The next entries are the launch records (accepted / refused with the kernel's reason) for pair 1.

## 2026-09-29 09:07 UTC — Pair 1 launch on `wsl_4070` REFUSED by admission (node checkout state, a shared control); CONTROL message 2 to Root; pair 1 waits

**Correction to the previous entry:** the node state was observed at **08:58 UTC**, not 16:58 UTC (the node's `uptime` prints its local clock, UTC+8; DM error, the third clock mis-stamp of this line).

**Refusal (09:02 UTC, from this host via `launch_b01_fits.sh c3e3bf10d… H 931201`):** `hmasd launch refused: direction 'coupled_host_joint_skills_stage1' must appear exactly once in the Active table`. Nothing was created on the node (no claim, no run directory, no worktree by the launcher). CONTROL message 1 (node time) had been queued at 09:02 UTC (`01a0ec66-68fd-7542-ade6-3ffc9502410f`).

**Root cause (read, not guessed):** `scripts/hmasd_launch.py` (`_require_local_policy`, identical at the node's HEAD and on main, last changed 6ad4efd5f) parses the Active table of the canonical control checkout's **working-tree** `docs/research/RESEARCH.md` first, then the published head's, and requires the same state. The node's canonical checkout `/home/wu/projects/HMASD` is at c562b8fa9 (2026-09-28 00:47 PDT, before this direction's row existed) and carries uncommitted foreign edits to `docs/research/RESEARCH.md` (working blob 0df3b7f0f; equal to no main version in the last 80; the author preserved copies under `/home/wu/hmasd-artifacts/node-local-modified-20260928/`) and to two `runs/energy_relay_baselines/b01_set_a01/seed-*/launch-status.json`. Both the HEAD and the working copy have zero rows for this direction; the published head (c3e3bf10d, fetched on the node, blob verified) has exactly one. A fast-forward would overwrite the foreign edits, so it is not mine to run (no stash/reset/checkout of others' files). A detached worktree at c3e3bf10d (`/home/wu/hmasd-worktrees/coupled-b01-20260929`, contains the row and the runner) does not help: the launcher resolves the control root to the common canonical checkout regardless of `--source-root`. The worktree stays until closure (harmless, removed then).

**Action:** CONTROL message 2 to Root (queued 09:2x UTC, `01a0ec6a-5a8d-7a30-8c87-6936b74a28e2`): the facts above, the concrete need (Root reconciles the local edits and fast-forwards the node checkout to main, then leaves one inbox line), and that pair 1 launches on that line. Owner alternative if Root cannot act soon: [DECIDE-3] B (six fits on `local_linux`, ≈ 100 CPU-h) or C; the DM does not switch on its own. Inbox waiter re-armed. **State: 0 formal fits; A chosen and mechanically blocked on a shared control; T4 accepted.**

Data received, no action: Root's inbox file `20260929_workflow_retrospective_ROOT.md` (commit 366903212 by the other writer in this checkout, carried by this push): owner-adopted workflow refinements from the Pro retrospective; applies at the next boundary; no reply owed.

## 2026-09-29 09:21 UTC — Root reconciled the node checkout; pair 1 ACCEPTED on `wsl_4070` (H 931201, SET 932201); 2 formal fits running

**Root's inbox line** (`docs/Claude_docs/inbox/20260929_wsl4070_control_sync_ROOT.md`, commit 5c6997722, 09:19 PDT-stamped 02:19): Root fast-forwarded `/home/wu/projects/HMASD` c562b8fa9 → 89acc114f under the shared writer and admission locks; the launcher's read-only policy check passed at 09:16:23 UTC for this direction/lead; the superseded node-local index was retained verbatim under `hmasd-artifacts/node-local-modified-20260928/` (sha256 02e31846…); no sparse/reset/stash/claim change; Root launched nothing. Verified from here at 09:19 UTC: node HEAD 89acc114f, the direction row present once, load 0.00, 14.9 GB available. Data, no reply owed.

**Launches (from this host, `launch_b01_fits.sh`, launch sha c3e3bf10d — runner unchanged since; the launcher reads the published head's control state):**

| fit | accepted (UTC) | claim | supervisor / runner pid | preflight |
|---|---|---|---|---|
| `b01_fit_H_931201_a01` (H, d2) | 09:20:01 | e3a59ba26d5c… | 978289 / 978290 | available 14.58 GB, floor pass, no failure reasons |
| `b01_fit_SET_932201_a01` (SET, off) | 09:20:3x | 506e2d534b3a… | 978909 / 978910 | (record on the node; rsynced at exit) |

At 09:20:32 UTC the H runner had passed the admitted boundary, written config/matching table (15 differing config fields between arms, as in the probes) and started evaluation 0 (dev, deterministic); RSS 777 MB, 340 % CPU, node load 2.0. Output roots `/home/wu/projects/HMASD/runs/coupled_host_joint_skills_stage1/<tag>`; observation = detached poll of `process-exit.json` from this host, rsync of each run directory to this checkout at exit (then durable checkpoint copies under `/home/wu/hmasd-artifacts/coupled_host_joint_skills_stage1/<tag>/`). Next pair (931307/932307) after this pair exits. **2 formal fits running, 0 read; cap 35 CPU-h.**

## 2026-09-29 11:15 UTC — Pair 1 complete and read (ordinary readings only; the P2/P4 rule applies at batch end); pair 2 accepted (H 931307, SET 932307)

**Pair 1 exit (both `status complete`, exit 0, 45 rollouts = 360k team steps, 45 updates, all declared panels written; rsynced to this checkout at exit; checkpoints c00/c15/c30/c45 copied to `/home/wu/hmasd-artifacts/coupled_host_joint_skills_stage1/<tag>/` with the summary's sha256s):**

| fit | wall | CPU | peak RSS | last rollout wall / update | d2 / terminal facts |
|---|---|---|---|---|---|
| `b01_fit_H_931201_a01` (exited 10:54:06 UTC) | 5,442 s = 1.51 h | 21,796 s = **6.05 CPU-h** | 2.56 GB | 132.5 s / 101.8 s | 800 team rows, 16 terminal, 0 open segments; dones all true at 500 only |
| `b01_fit_SET_932201_a01` (exited 10:29:38 UTC) | 3,991 s = 1.11 h | 15,697 s = **4.36 CPU-h** | 1.11 GB | 85.6 s / 71.6 s | 0 high-level rows (off) |

Cost: pair 1 = 10.4 CPU-h on the idle node, 2.9× cheaper per fit than the contended local probes projected and inside option A's 25–35 CPU-h projection; three pairs ≈ 31 CPU-h + B12 collections (≈ 1–3 CPU-h on the node) ≈ 32–34 CPU-h against the 35 CPU-h cap — tight; a third-pair overrun would be reported, never trimmed.

**Ordinary readings, pair 1, closed-loop 500-step means over the declared panels (32 worlds each), against the sealed hold-out references** (P_relay^on C̄_bh .780 / r .553; P_flat^on .639 / .459; stationary floor .171 / .110; random .172 / .113; G_C,ho,cl = .141):

| panel | H r / C̄_bh | SET r / C̄_bh | paired Δ (H − SET) r / C̄_bh |
|---|---|---|---|
| dev det. c00 (init) | .117 / .183 | .121 / .190 | −.004 / −.007 |
| dev det. c15 | .135 / .205 | .046 / .071 | +.089 / +.134 |
| dev det. c30 | .215 / .311 | .074 / .116 | +.141 / +.195 |
| dev det. c45 | .162 / .244 | .123 / .190 | +.039 / +.054 |
| **hold-out det. c45 (P2/P4 panel)** | **.155 / .235** | **.142 / .219** | **+.014 / +.016** |
| hold-out sampled c45 | .146 / .216 | .151 / .235 | −.005 / −.019 |

Facts, not the reading: (i) both arms end ≈ .05–.06 C̄_bh above the stationary floor and ≈ .40 below P_flat^on; the pair-1 P2 quantity L2(H) = .235 − .639 − ½·.141 = **−.475** (SET −.491) — far from the ≥ 0 competence line; (ii) H's paired advantage on the P4 panel is +.014 r (rule needs ≥ +.03 on ≥ 2 of 3 pairs) with ΔC̄_bh +.016 ≥ 0; (iii) H's dev curve is non-monotone (c30 .311 → c45 .244) and SET's collapses at c15/c30 (final-100 C̄_bh .000 / .014) before recovering; (iv) association changes per step rise from .003 (init) to ≈ .8 in both arms, with 150–175 user backhaul-loss events and ≈ 2,800 action clips per 500-step episode — the learned policies churn; (v) H's relay-position share per UAV on hold-out is .09–.17 (diffuse), the far-cluster backhauled share .123 (H) vs .074 (SET) det. hold-out, both far under P_relay^on's .891 dev. Parameter motion: H coordinator relative L2 .068 (1,350 optimizer calls' worth over 675 steps), discoverer actor 1.15; SET coordinator 0 (as designed). No parameter, seed or recipe changes; the six-fit batch continues as declared. What this pair changes: the prior on P2(H) drops from the declared value toward the S7 pattern ("learner not competent on a host where the ordinary planner is"), and the cell-2 contingency is now unlikely; nothing is decided until the three pairs are read by the fixed rule.

**Pair 2 launches (same script, launch sha c3e3bf10d; node HEAD e9faa4ad4 after Root's sync; node load before launch 0.43):**

| fit | accepted (UTC) | claim | supervisor / runner pid |
|---|---|---|---|
| `b01_fit_H_931307_a01` | 11:12:57 | 06c3c015f6d2… | 988195 / 988196 |
| `b01_fit_SET_932307_a01` | 11:13:34 | d84f699678dd… | 988757 / 988758 |

Watcher armed for pair 2; pair 3 (931413/932413) follows its exit. **Cumulative: 2 fits complete (10.4 CPU-h), 2 running, 0 batch readings.**

## 2026-09-29 12:56 UTC — Pair 2 complete and read; pair 3 accepted (H 931413, SET 932413); 4 of 6 fits done, 20.4 CPU-h

**Pair 2 exit (both `complete`, exit 0; rsynced at exit; c00/c15/c30/c45 copied to `hmasd-artifacts/coupled_host_joint_skills_stage1/<tag>/`, sha256s as in each summary):**

| fit | exited (UTC) | wall | CPU | peak RSS | d2 / terminal facts |
|---|---|---|---|---|---|
| `b01_fit_H_931307_a01` | 12:41 | 5,069 s = 1.41 h | 20,358 s = **5.66 CPU-h** | 2.55 GB | 800 team rows, 16 terminal, 0 open segments |
| `b01_fit_SET_932307_a01` | 12:22 | 3,952 s = 1.10 h | 15,545 s = **4.32 CPU-h** | 1.12 GB | 0 high-level rows |

**Ordinary readings, pair 2 (same panels and sealed references as pair 1):**

| panel | H r / C̄_bh | SET r / C̄_bh | paired Δ (H − SET) r / C̄_bh |
|---|---|---|---|
| dev det. c00 | .119 / .185 | .115 / .178 | +.004 / +.007 |
| dev det. c15 | .075 / .114 | .105 / .147 | −.030 / −.033 |
| dev det. c30 | .144 / .220 | .167 / .234 | −.023 / −.014 |
| dev det. c45 | .152 / .221 | .142 / .211 | +.010 / +.010 |
| **hold-out det. c45 (P2/P4 panel)** | **.143 / .211** | **.152 / .225** | **−.009 / −.014** |
| hold-out sampled c45 | .171 / .257 | .168 / .252 | +.003 / +.005 |

Facts: L2(H, pair 2) = .211 − .639 − .0705 = **−.499** (SET −.485); H loses the paired P4 panel on this pair (pairs so far: +.014, −.009 — the "≥ +.03 on ≥ 2 of 3" rule can no longer be met by cell 1: P4 is already decided NOT MET on the pre-declared rule, formally recorded at batch end). The same churn signature as pair 1: association changes/step ≈ .7–.9, 130–200 user backhaul-loss events and ≈ 2,900 action clips per episode at c45 in both arms; far-cluster backhauled share .046 (H) / .049 (SET) det. hold-out. H's relay-position share per UAV stays diffuse. Parameter motion H coordinator .071, discoverer actor 1.17 (SET 1.17) — the actors move as much in both arms; the coordinator barely moves. No changes to anything declared; pair 3 runs to complete the batch as declared (the batch cost is inside the cap and the third pair still prices P2's "2 of 3" and the P3 instrument on three H seeds).

**Pair 3 launches (same script and launch sha; node load before launch 0.00 — Root's Codex operations exited before 11:12 UTC):**

| fit | accepted (UTC) | claim | supervisor / runner pid |
|---|---|---|---|
| `b01_fit_H_931413_a01` | 12:55:03 | 9877e262c1c6… | 991746 / 991747 |
| `b01_fit_SET_932413_a01` | 12:55:43 | 5b3ea1ead905… | 992290 / 992291 |

Watcher armed. After pair 3: B12 collections on the node (`collect_commitments.py` on H c15/c30/c45 from the artifacts copies, three H fits × 3 checkpoints ≈ 9 collections; cost re-priced from the first one before the rest), the reader, then the batch reading by the fixed rules. **Cumulative: 4 fits complete = 20.4 CPU-h; 2 running; projected batch ≈ 30.5 CPU-h + collections.**

**2026-09-29 12:57 UTC — correction and B12 start.** The previous entry's "H c15/c30/c45 ≈ 9 collections" misstated the declared P3 unit: one table per H fit from its final checkpoint c45 (P3 = supported on ≥ 2 of 3 H seeds), i.e. three collections. The first collection (H 931201, c45, sha256 0a74c705…) is launched now, in parallel with pair 3 (node has spare cores; collections are inside the 35 CPU-h cap and do not depend on pair 3); its measured cost prices the other two before they are launched. Launch entry `launch_b01_collect.sh <sha> <fit tag> <seed> [c-index]` (committed here), launch sha c3e3bf10d (the collector is unchanged since 68e441f3e). Argument fact: the checkpoint is passed relative to the checkout (`runs/<fit>/checkpoint_45.pt`); the snapshot launcher leaves relative arguments untouched and the collector resolves them against the checkout that holds `runs/` and records the digest.

## 2026-09-29 13:20 UTC — P3 collection 1 and reading 1 (H 931201, c45): reading UNSUPPORTED by the pre-specified rule; collection 2 and reading 1 launched

**Collection 1** (`b01_p3_collect_H_931201_a01_c45`, accepted 12:58:13 UTC, claim 8f6270599d09…, pids 992858/992859; exit 0 at ≈ 13:06 UTC; rsynced; `commitments.npz` is git-ignored — durable copies: the node run directory and this checkout): checkpoint `runs/…/b01_fit_H_931201_a01/checkpoint_45.pt` sha256 0a74c705… (matches the fit summary; tensors bitwise equal after load, normalisers equal, config equal, route d2/k 10/costs ∞/age off), 16 rollouts × 16 lanes, episodes 46–61 (worlds 7801xx…, never a panel world), 128,000 team steps, **12,800 commitments = 256 lane-episodes × 50**, zero optimizer steps, digest equal. Structural zero check: max |Δaction| = 0.0 (deterministic and sampled) over 200 rows × 5 other team labels; control (agent 0's individual label) 4.45. Cost: **472 s wall, 1,661 CPU s = 0.46 CPU-h**, peak RSS 0.76 GB; 3.66 ms per team step (policy 2.34, env 1.29). Clip events 763,893 of 768,000 UAV-steps (99 %).

**Reading 1** (`b01_p3_read_H_931201_a01_c45`, accepted 13:18:58 UTC, claim 155f4a240650…, pids 994471/994472, exit 0; table sha256 d5f4f26e…; 1,000 draws, seed base 20260929; 2.5 s):

| item | value |
|---|---|
| readability | READABLE: 66 of 72 added columns supported (all 15 products); the 6 unsupported are the diagonal `rp_z_z` (58–123 non-zero rows, below the 128 floor); rank increment 66/66; folds non-empty; placebo readable |
| primary Δ (MSE_R − MSE_F, 8 folds) | **−4.20e−6** (per fold: +2e−6, +1.1e−5, −1.4e−5, −1.1e−5, −1.7e−5, −9e−6, −9e−6, +1.4e−5); direct refit −4.20e−6 |
| null q95 / fraction of null below Δ | −6.29e−6 / .997 |
| **primary decision** | **unsupported** (rule: Δ > 0 AND Δ > q95; the first clause fails) |
| products-only Δ / q95 / fraction below | −8.53e−7 / −3.99e−7 / .823 → **unsupported** |
| placebo (team-label one-hots) | Δ −2.8e−7, q95 +1.3e−7, not passed (as it should) |
| scale | fold MSE_R ≈ 7.4e−4 – 1.24e−3; residual SD of R .032; \|Δ\| ≈ .4 % of MSE_R |

Fact recorded without reinterpretation: the observed Δ sits above 99.7 % of the additive-null draws (the null distribution of Δ is centred near −1e−5 because 66 noise columns cost held-out MSE), i.e. the added block predicts slightly better than 66 spurious columns would, yet still worse than R alone; the pre-specified rule requires an outright held-out improvement and reads **unsupported**. On the synthetic additive null, Δ > q95 occurred in 0/40 tables, so this position is unusual under the null; it is one H seed, and no rule is changed by it. The reading is also on an incompetent checkpoint (pair-1 L2(H) −.475), which the disposition anticipated: P3 is conditioned on P2(H) for the roles claim.

**Launches:** collection 2 (`b01_p3_collect_H_931307_a01_c45`, checkpoint sha256 1132a5dc…, accepted 13:18:26 UTC, claim 3709c2366b66…, pids 993989/993990); reading launch entry `launch_b01_read.sh <sha> <collection tag>` (5259ed8c4). Collection 3 and readings 2–3 follow pair 3's H fit. Cost so far: 4 fits 20.4 CPU-h + collection 0.46 + reading ≈ 0; pair 3 running.

## 2026-09-29 13:41 UTC — P3 collection 2 and reading 2 (H 931307, c45): UNSUPPORTED again; two of three H seeds read, P3 can no longer reach "≥ 2 of 3"

**Collection 2** (`b01_p3_collect_H_931307_a01_c45`, accepted 13:18:26 UTC, exit 0 ≈ 13:27 UTC, rsynced): checkpoint sha256 1132a5dc… (matches the fit summary; faithful load), 12,800 commitments (256 lane-episodes × 50), zero optimizer steps; structural zero check 0.0 / 0.0 (control 3.39); **493 s wall, 1,695 CPU s = 0.47 CPU-h**, peak RSS 0.76 GB; clip events 763,604 of 768,000.

**Reading 2** (`b01_p3_read_H_931307_a01_c45`, accepted 13:40:34 UTC, claim 11b265610431…, pids 996202/996203, exit 0; table sha256 1b737791…):

| item | value |
|---|---|
| readability | READABLE: 67 of 72 supported (all 15 products; unsupported = `rp_0_0`…`rp_4_4`, 83–118 non-zero rows); rank increment 67/67; placebo readable |
| primary Δ / q95 / fraction of null below | **−4.54e−6** / −5.39e−6 / .990 → **unsupported** (Δ < 0) |
| per-fold Δ | −1.0e−5, +5e−6, −7e−6, −9e−6, +5e−6, −5e−6, −4e−6, −1.1e−5 (MSE_R .00095–.00132; residual SD .033) |
| products-only Δ / q95 / fraction below | −4.39e−7 / −4.33e−7 / .948 → **unsupported** |
| placebo | Δ −6.6e−7, q95 +1.5e−7, not passed |

Same pattern as reading 1 (Δ < 0 in both, both above q95 of the additive null at .997/.990). With two of three H seeds unsupported, the P3 rule "supported on ≥ 2 of 3 H seeds" cannot be met; the third seed's reading is still produced for the record (its cost is ≈ 0.5 CPU-h + seconds) and the batch reading is written once pair 3 exits. Cumulative cost: 4 fits 20.4 CPU-h + 2 collections 0.93 CPU-h; pair 3 at rollouts 21/29 at 13:40 UTC (slower while the collections shared the node).

## 2026-09-29 14:43 UTC — Pair 3 complete and read; six fits done (31.0 CPU-h); collection 3 launched; batch reading follows reading 3

**Pair 3 exit (both `complete`, exit 0; rsynced; c00–c45 copied to the artifacts directory):**

| fit | exited (UTC) | wall | CPU | peak RSS |
|---|---|---|---|---|
| `b01_fit_H_931413_a01` | 14:36 | 5,285 s = 1.47 h | 21,379 s = **5.94 CPU-h** | 2.56 GB |
| `b01_fit_SET_932413_a01` | 14:16 | 4,165 s = 1.16 h | 16,387 s = **4.55 CPU-h** | 1.14 GB |

d2/terminal facts as in pairs 1–2 (800 team rows, 16 terminal, 0 open segments; SET 0 high-level rows). Parameter motion H coordinator .068, actors 1.12/1.18.

**Ordinary readings, pair 3:**

| panel | H r / C̄_bh | SET r / C̄_bh | paired Δ (H − SET) r / C̄_bh |
|---|---|---|---|
| dev det. c00 | .129 / .200 | .115 / .180 | +.014 / +.020 |
| dev det. c15 | .086 / .134 | .053 / .081 | +.033 / +.053 |
| dev det. c30 | .157 / .237 | .112 / .171 | +.045 / +.066 |
| dev det. c45 | .147 / .228 | .112 / .173 | +.035 / +.055 |
| **hold-out det. c45 (P2/P4 panel)** | **.142 / .215** | **.086 / .132** | **+.056 / +.083** |
| hold-out sampled c45 | .144 / .213 | .131 / .195 | +.013 / +.018 |

Facts: SET 932413 ends **below the stationary floor** on the deterministic hold-out (C̄_bh .132 vs floor .171; its final-100 .097) — a collapsed flat policy, so this pair's H advantage is SET's failure, not H's competence (H .215 ≈ pairs 1–2); L2(H, pair 3) = .215 − .639 − .0705 = **−.495**. Same churn signature (association changes .84/step, ≈ 2,900 clips per episode).

**Collection 3** (`b01_p3_collect_H_931413_a01_c45`, checkpoint sha256 fe819d46…, accepted 14:43:17 UTC, claim cd78abb65f9f…, pids 1002431/1002432). Reading 3 follows; then the batch reading by the fixed rules. **Cumulative: 6 fits = 31.0 CPU-h; collections 0.93 + 1 running; cap 35 CPU-h holds.**

## 2026-09-29 15:09 UTC — b01 BATCH READING (final, by the pre-declared rules): P1 MET; P2, P3, P4 NOT MET; cell 2 not bought; cost 33 CPU-h of 35; closure and round-boundary statement

**Reading 3** (`b01_p3_read_H_931413_a01_c45`, accepted 15:04:42 UTC, claim 668ec20f10cd…, pids 1007295/1007296, exit 0; table sha256 e5270bb1…, collection 3 = 262 s / 958 CPU s = 0.27 CPU-h, 12,800 rows, structural zero check 0.0 / 0.0, control 5.22): READABLE (65/72 supported, all 15 products; unsupported = six `rp_z_z` + `rp_0_1`); primary Δ **−8.31e−6**, q95 −5.71e−6, fraction of null below .573 → **unsupported**; products-only Δ −2.16e−6, q95 −3.13e−7, fraction .007 → **unsupported**; placebo Δ +3.1e−9, q95 +9.3e−8, not passed.

**Formal readings (the declaration's rules as revised by the disposition of 54a51a9df; all six fits, three collections and three readings complete; nothing tuned, one fit per seed, no extension):**

| item | rule | result | verdict |
|---|---|---|---|
| P1 coupling (cell 0) | G ≥ .05 and G_C,dev,cl ≥ .05 on 32 dev worlds | G .106 (hold-out .121), G_C,dev,cl .152 (hold-out .141) | **MET** |
| P2 competence (hold-out, closed loop) | L2(a) = C̄_bh(a) − C̄_bh(P_flat^on) − ½ G_C,ho,cl ≥ 0 on ≥ 2 of 3 seeds | L2(H) −.475 / −.499 / −.495; L2(SET) −.491 / −.485 / −.578 | **NOT MET** (both arms, 0 of 3) |
| P4 hierarchy | paired r_H − r_SET ≥ +.03 AND ΔC̄_bh ≥ 0 on ≥ 2 of 3 pairs | Δr +.014 / −.009 / +.056; ΔC̄_bh +.016 / −.014 / +.083 | **NOT MET** (1 of 3; pair 3's margin is SET 932413's collapse below the floor) |
| P3 roles | primary reading supported on ≥ 2 of 3 H seeds | 0 of 3 (Δ −4.2e−6 / −4.5e−6 / −8.3e−6; null positions .997 / .990 / .573; products-only 0 of 3) | **NOT MET**, and read on incompetent checkpoints (P3 was conditioned on P2(H)): uninformative about roles |
| cell 2 (SeqAU) | only if P2 ∧ P3 ∧ P4 | — | **not bought** |

Facts that carry over (not readings): on every fit the hold-out C̄_bh sits at .21–.24 (SET 932413 .13, below the stationary floor .171) against P_flat^on .639 and P_relay^on .780; ≈ 2,850 of 3,000 UAV-steps per episode are unit-ball clipped in every arm while PPO stores the unclipped action; association changes ≈ .7–.9 per step; 1.4–2.6 of six UAVs routed per step; far-cluster backhauled share .03–.12; H's coordinator relative L2 .068–.071 versus actors ≈ 1.15 in both arms; SET's actor receives the full 133-dim state (all user and UAV positions) at execution time and fails identically, so execution-time information is not the cause (source: `configuration.py` information entry points, `models.py` SetActorBase). The precise statement is: incompetence under the per-step continuous velocity interface with the AND-coupled team reward (a far server earns nothing without its relay and vice versa), at 360k steps, for both packages.

**Round-boundary statement (858e8cff5).** Changed: the cheap coupled relay host is an established opportunity with a sealed same-information ordinary reference (P_relay^on on 64 worlds, ≈ 4 s per world); the existing HMASD-d2 and flat SET packages are not a learner substrate on it at this interface and exposure; the coordinator-based Stage-2 line (untied K / N) has no competent instance to build on. Unchanged: every S7 verdict, FSD's reopening condition, SCC's closure, T3's pause, the D1′ candidate (still RECORDED, now with a zero-fit headroom gate as its first act). Uninformative: P3 (read on incompetent checkpoints; the instrument itself calibrated and works), cell 2 never bought. Cost of this batch: 6 formal fits **31.0 CPU-h** (H 6.05 / 5.66 / 5.94; SET 4.36 / 4.32 / 4.55), 3 collections 1.20 CPU-h, 3 readings ≈ 0.01, technical probes 48k steps ≈ 0.7 CPU-h (local), gate + hold-out ≈ 0.1 → **≈ 33.0 CPU-h against the re-declared 35 CPU-h cap**; engineering inside the 40 h cap.

**Closure.** Records: every run's summary/config/launch/exit/panel/reading JSON is committed (`runs/coupled_host_joint_skills_stage1/b01_*`); checkpoints (c00–c45 of all six fits) and the three commitment tables stay on `wsl_4070` (run directories 592 MB, durable copies under `/home/wu/hmasd-artifacts/coupled_host_joint_skills_stage1/` 504 MB, sha256s in each summary) plus one local copy of the tables (git-ignored). Scratch removed: `temp/directions/coupled_host_joint_skills_stage1/scratch/{implementer-t1t2,implementer-t2c,implementer-t3,implementer-t4,smoke_dm_t2b_v3,smoke_dm_t3_v4}` (7,912 KB → 128 KB; the L0 scope notes and the Pro transport operation directory remain); the unused detached node worktree `/home/wu/hmasd-worktrees/coupled-b01-20260929` removed (766 MB freed on the node); no other leftovers. Net allocated disk decreased on both hosts; the direction's temp tree is 132 KB.

**What follows (owner-approved workflow sizing, 2026-09-29):** question ownership continues on this host. The Oracle's decision memo for the next two questions is copied in the next entry; it goes through one critic pass (separate context) and the round-boundary Pro synthesis, then the two declarations. No new fit on this recipe.

## 2026-09-29 15:11 UTC — Oracle decision memo (Fable 5.1, max effort, read-only) for the next two questions; copied verbatim, owned by the DM; critic pass and round-boundary Pro synthesis follow

### Oracle decision memo — next two Claude questions after `coupled_host_joint_skills_stage1` b01 (2026-09-29)

Read-only; nothing written or launched. Sources: D2 NOTES (all 645 lines), the D2 code (`host.py`, `planner.py`, `adapter.py`, `configuration.py`, `models.py`, `runner.py`, `run_gate.py`), the six fit run directories and both sealed gate runs (read with the scientific venv, numbers below are my recomputation), RESEARCH.md (background §§5, 7, 8; Active/Reserve tables; current plan; session routing), the D1′ candidate entry (`energy_relay_benchmark/NOTES.md` 8721), the round-3 memo/critic/Pro records, `uav_transit_handoff` (design, literature check, final disposition), `uav_cooperative_planning` B02, SCC lessons, Root's two inbox files of today, the three libraries (MyLib `catalog.v2.jsonl` term scans; My-lib `search_mylib.py` hits with PARCO pp. 1–2 read; new-libs index), MAT abstract (arXiv 2205.14953), `hmasd/networks.py` 800–850 and 1650–1665, `hmasd/agent.py` 1992–1996 / 3253–3275, CLAUDE.md "Owner-approved workflow sizing (2026-09-29)". Claims are numbered so the DM can cite them; each load-bearing one is tagged SOURCE FACT / DERIVATION / CONJECTURE.

#### 1. The question as I understood it

Select the Claude DM's next two concurrent research questions on the owner's main line (UAV path planning / swarm cooperative planning with MARL), after D2's six-fit batch returned a negative learner result, under the 2026-09-29 workflow sizing: cheapest refuting run first; instruments only after the conditioning result holds; existing competent assets over new hosts; fits priced well under 10 CPU-h per study; bounded corrections from competent frozen policies over from-scratch fits; Pro at the round boundary; ideas labelled TRIED/RECORDED/NEW; no diagnosis successor; no re-skinned triggers/baselines/probes presented as new.

#### 2. What D2 established, what it did not, and the consequential question

**One-paragraph reading.** The coupled relay host is real and cheap: relaying is worth ≈ 7 users of service on both panels (G_C,cl .152 dev / .141 hold-out; P_relay^on C̄_bh .810/.780 vs P_flat^on .658/.639; floors ≈ .17), and the same-information placement planner reaches it in ≈ 4 s per world. Both existing packages, HMASD-d2 (k = 10) and matched flat SET, are far below the competence line on every pair (hold-out C̄_bh .21–.24, SET 932413 .13 below the stationary floor; L2(H) ≈ −.48 to −.50), with one signature: saturated full-speed actions (≈ 2,850 of 3,000 UAV-steps clipped per episode), association churn (.7–.9 changes per step), only 1.4–2.6 of six UAVs routed per step, far-cluster service .03–.12, and below-stationary service on 9–17 of 32 hold-out worlds. HMASD's coordinator barely moved (relative L2 .068–.071) while both arms' actors moved ≈ 1.15; P4 is NOT MET by the pre-declared rule (Δr +.014/−.009/+.056), P3 is unsupported on two of three H seeds (the third reading cannot change "≥ 2 of 3"), so "who relays, who serves" was never testable. What D2 did **not** establish: whether the failure is the per-step continuous velocity interface, the AND-coupled sparse team reward (a far serving UAV earns nothing without a relay and vice versa), exposure (360k), or optimisation — and it did establish, from source, that execution-time information is **not** the cause for SET (claim 2.4). The consequential question that follows is not "why did it fail" but **"is there any cheap competent learner substrate on this coupled host at all, and at which decision interface — because the owner's Stage-2 programme (untied K / untied N on HMASD's coordinator) has nothing to stand on until one exists."**

Numbered claims behind that paragraph:

2.1 SOURCE FACT (NOTES 399–421, 425, 530; my recomputation of `runs/…/b01_gate_{dev,holdout}_a01/worlds/*.json`): static G .106/.121; G_C,cl .152/.141 (dev minimum −.010, hold-out minimum −.087; 3/7 worlds below .05); P_relay^on C̄_bh .810/.780, final-100 .876/.846; P_flat^on .658/.639; stationary .179/.171; random .181/.172.

2.2 SOURCE FACT (NOTES 541, 572, 643; my recomputation of the six `panel_45_holdout_deterministic.json`): hold-out C̄_bh H .235/.211/.215, SET .219/.225/.132; routed UAVs per step 1.4–2.6 of 6; links per routed UAV 1.3–1.6 (mostly direct); far-cluster backhauled share .03–.12; worlds below the world's own stationary floor 12/12/9 (H) and 9/12/17 (SET); worlds above P_flat^on: 0 for every fit; dev curves non-monotone in every fit (e.g. H 931201 .183 → .205 → .311 → .244; SET 932201 .190 → .071 → .116 → .190).

2.3 SOURCE FACT (NOTES 395, 587): the host executes the unit-ball-clipped action while PPO stores the unclipped action and log-probability; ≈ 95–99 % of UAV-steps are clipped. This is a known continuous-control pathology (the policy mean is pushed outward with no execution consequence); it is a confound of every per-step-velocity arm and disappears at a target-level interface. I did not re-verify the storage path in `hmasd/agent.py`; the NOTES statement is the source.

2.4 SOURCE FACT (`configuration.py` 246–251 `information_entry_points`; `models.py` `SetActorBase.forward`, which slices the 133-dim state from the actor input and feeds `state_encoder`; `STATE_LAYOUT` 144–151 puts all 50 user xy in [32:132) and six UAV xyz in [0:24)): **SET's actor had ground-truth user and UAV positions at execution time and still ended at C̄_bh ≈ .22.** The explanation "the actors cannot see the far clusters" is refuted for SET; H's actor sees only the 90-dim local observation plus labels, but H is no worse than SET. The failure is therefore located in the per-step continuous interface under an AND-coupled team reward, not in execution-time information.

2.5 DERIVATION (host reward structure, `host.py` 138–177; game reading): C_bh counts a user only if its serving UAV is routed; a relay contributes nothing unless a far server depends on it; a far server contributes nothing without the relay. Every far cluster on both panels lies 1.6–3.5 km from the BS, beyond the 1.19 km direct reach (`planner.link_ranges`), so every world's opportunity is a chain of 1–3 relays. With shared-parameter per-step Gaussian exploration this is a team stag hunt: "hover near the BS and serve the near users" (hare, ≈ the flat layout) is reachable by unilateral improvement; a chain (stag) pays only when ≥ 2 UAVs commit to distant complementary positions for ≥ 80 steps. The single-agent prototype (one controller placing all six UAVs — i.e. the planner) omits exactly this coupling: symmetric agents must break symmetry to fill distinct chain slots and must commit jointly. HMASD's device for correlated commitment (team latent Z) does not reach the actors in this implementation (SOURCE FACT: NOTES 474, max |Δaction| over team-label swaps = 0.0); only the autoregressive per-agent labels z_i | Z, z_<i do (SOURCE FACT: `hmasd/networks.py` 826–845).

2.6 SOURCE FACT (my recomputation of the gate records): the planner's descent adds .054 r (dev) / .058 (hold-out) over the best evaluated candidate (max .115) and converges at the 25 m stage in every world; the best candidate alone already beats P_flat's final layout by +.052/+.063 static on 28/32 worlds. Closed-loop travel costs the planner .066 C̄_bh on both panels (final-100 minus all-500), arrival at ≈ 80 steps (max 123), max travel 2.4–3.5 km.

2.7 SOURCE FACT (NOTES 525–528, 558–559, 627–628): on idle `wsl_4070` a 360k-step fit costs SET 4.32–4.55 CPU-h and H 5.66–6.05 CPU-h; the PPO update is 84 % (SET) / 77 % (H) of a rollout's wall at 8,000 team rows per rollout; the gate is ≈ 4 s per world.

2.8 SOURCE FACT (grep of `uav_env.py`, `scenario2.py`, `scenario1.py`): there is no user-mobility switch. Any dynamic variant of this host is a new host in the owner's sense.

**Round-boundary line the DM owes before the new declarations (858e8cff5):** changed — the coupled host is an established cheap opportunity (ordinary reference P_relay^on sealed on 64 worlds); both existing packages are not a substrate on it at this interface and exposure; the coordinator-based K/N line has no instance to build on. Unchanged — every S7 verdict, FSD's reopening condition, SCC's closure, T3's pause. Uninformative — P3 (read on incompetent checkpoints), cell 2 never bought. Cost — 6 formal fits 31.0 CPU-h, 3 collections ≈ 1.4 CPU-h, 48k probe steps, gate/hold-out ≈ 0.1 CPU-h, engineering inside the 40 h cap.

#### 3. Candidate questions (all on the main line; labels against the July record, the RESEARCH rows and the three stores)

##### C1 — D1′ as declared: learned bounded offset around P_relay^on's assigned target vs a qualified ordinary correction (the DM's own sharpening, critiqued)

- Decision object: learned vs ordinary planning correction on this host; comparator = the planner plus a 300-evaluation static correction, secondary the anchor itself. Asset reused: planner, executor, sealed references.
- Critique. (a) Headroom is bounded by construction on a static world with a same-information planner: the static residual beyond the converged 25 m descent is unknown but the descent already captured .054 (2.6); the travel term .066 is mostly chain-formation time that a 300 m disk (exactly one 10-step segment at 30 m/s) cannot shorten, and the residual frame cannot express staged deployment ("serve near users while the chain forms"). Expected total headroom ≤ .02–.04 C̄_bh — inside the within-arm seed range seen in D2 (H .211–.235, SET .132–.225). CONJECTURE, with 2.6 as its basis. (b) The DM's "discrete choice among the planner's candidate placements" as a *team-level* choice is a ≈ 175-arm bandit over a known deterministic evaluator whose argmax the planner already takes; it has no MARL content and an unbeatable comparator — not worth a fit. Its *per-agent* form is C3 below. (c) What host change would create headroom: user mobility, unknown user positions for the planner too, link stochasticity, energy or member loss — each is a new host (2.8) and none is bought now.
- Cheapest refuting run (zero fits, < 1 CPU-h on `local_linux`): H_static = P_relay at a 10× budget (30,000 evaluations, 6 starts, 10 m final stage) minus P_relay at 3,000 on the 32 dev worlds; H_corr = closed-loop C̄_bh of "anchor + one 300-evaluation ±25 m/±z sweep every 10 steps" minus the anchor's closed-loop on dev; the travel term is already known (.066). Kill: H_static ≤ .02 (C̄_bh-equivalent) AND H_corr ≤ .01 → the learned residual has < .03 of headroom beyond the ordinary correction → D1′ not bought, recorded as a justified no-run. Prior that it is killed: ≈ 80 %.
- If not killed: the residual arm is the owner-preferred "bounded correction from a competent frozen policy" and slots into Q-A below as a third arm with its own declaration line (identity check c00 ≡ anchor per action, anchors cached by world seed — Pro's 6.48 M-evaluation objection applies verbatim, cost ≈ .8 CPU-h for a shared 720-world set).
- Label: RECORDED (Pro round-1 O; critic's competing question; `uav_transit_handoff` residual-in-logits designed and declined; July R42–R44 residual at another level per the round-3 memo). Not NEW.
- Overlap: none (Root's inbox of today excludes D1′ from Codex assignment).

##### C2 — Target-level substrate: the same packages with an absolute destination action executed by the go-to controller ("where to go", free targets)

- Decision object: does any existing package become a competent coupled-host learner when the decision is the planner's kind of decision (an absolute 3-D destination held by the executor until re-chosen, one decision per UAV per 10 host steps) instead of a per-step velocity? Package reuse, not attribution. Assets: the executor (`closed_loop_execute` action rule), the adapter, the runner, sealed references, both learner packages unchanged except the action contract.
- Interface fork (deliberate): an *absolute destination* held by the executor is a different object from the critic's "300 m disk = velocity at a coarser clock" objection to W′; the learner emits what the planner emits. Targets must persist across boundaries, so the actor keeps its recurrent path; k = 1 in macro units (= 10 host steps) is a declared recipe difference (BPTT/GRU chunk in macro units), not a tuning.
- Ordinary comparators with the same addition: P_relay^on (package-reuse comparator, the sealed reference), P_flat^on (.639: the "all-direct" band boundary — what a learner reaches if it finds service but never chains), stationary, and a zero-fit random-target floor (uniform destination every 10 steps under the same executor).
- Label: RECORDED — waypoint/target learner W/W′ (energy_relay_benchmark NOTES 6737–6739, Pro "not bought" on S7-S2 for six co-varied changes and a modal partial recovery); `uav_cooperative_planning` B02 (learned values over a common transit library, L−P −.016 QoS, one fit); `uav_joint_transition` (L chose the default at all 800 clocks). Not NEW. Its justification now is not novelty but decision exposure: on a host with a *proven* opportunity and a *proven* per-step failure, one target-level fit is the cheapest run that can refute "existing packages are usable as a Stage-2 substrate at all".
- Cheapest refuting run: one SET-T fit (≈ 1.1–1.8 CPU-h, DERIVATION: rows per rollout fall 8,000 → 800, the update was 84 % of wall, env cost unchanged; the 3-rollout probe prices it), then H-T seed 1; kill if both hold-out c45 C̄_bh ≤ stationary + .10 (≈ .27, the D2 level).
- Overlap: none with Root's live objects (G0 S7-S1 availability; N5/S1 local history; B05 retained-control in reserve).

##### C3 — Slot allocation with a planner menu: does the autoregressive coordinator learn "who relays, who serves" when execution is competent?

- Decision object: with the planner's six-slot layout of the world as a menu (service:c / relay:c:m / above_bs positions with role tags) and the go-to executor, each UAV chooses a slot every 10 host steps. Compare HMASD's coordinator (labels z_i sampled sequentially conditioned on Z and z_<i — the joint sampling device) against matched flat SET (independent per-agent categorical choices from the same central state) and against ordinary allocation rules. This is the roles question D2 declared and could not test, now with competent execution and the AND structure explicit in the menu.
- Game structure: a 6-agent assignment game with complementarities (a relay slot is worth nothing without its server and vice versa) under simultaneous moves; the MARL coupling a single-agent prototype omits is *conflict* (two UAVs choosing one slot wastes a UAV) and symmetry breaking with shared parameters. Distinct prediction: sequential sampling (H) should show fewer conflicts than independent sampling (SET) at matched exposure, especially early (c15). Neighbours read: PARCO (My-lib `neurips-2025-f404c0259def290306159047b0b52584/arxiv-2409.03811.pdf`, pp. 1–2 read: "priority-based conflict handlers to resolve decision conflicts via learned priorities" in parallel autoregressive multi-agent construction); MAT (arXiv 2205.14953 abstract fetched: joint policy search as sequential decision-making with a monotonic-improvement claim); HMASD's own coordinator (`networks.py` 826–845). MAVEN: only the new-libs curator line ("mutual-information objective for episode-persistent joint modes"); its PDF is not in `docs/new-libs/papers/` — cite as index text only.
- Ordinary comparators with the same addition (all get the menu): M = min-makespan permutation (= P_relay^on, the upper reference; beating it on its own slots is impossible by construction), N = nearest-unclaimed slot in fixed index order (a decentralised sequential protocol — the strong ordinary rule a learned allocation must match), random-slot (floor, with conflicts and churn), sticky-random (random at t = 0 then hold; separates commitment from allocation).
- Honest framing (say it before the critic does): adoption value is nil — the planner's assignment is already optimal; the contribution is empirical understanding of the coordinator as an allocator, and the exposure is an investment decision: build Stage 2 on the coordinator or on flat/anchored forms. That is the constructive successor of D2's P3, not a diagnosis of D2.
- Label: RECORDED family (`uav_transit_handoff` joint selector over fixed controllers, declined; cooperative_planning B02; SCC stake: Hungarian vs fixed +.007, de-duplication +.32 on S7). The specific comparison "sequential-label coordinator vs independent flat sampling on a complementarity assignment with competent execution" is not in the record as run; that is a new comparison instance, not algorithmic novelty. Not NEW.
- Cheapest refuting run: pair 1 (H-slot, SET-slot; ≈ 2.5–3.5 CPU-h derived, probe-priced); kill if both ≤ random-slot + .10.
- Cost item Pro raised for D1′ applies here: menus for training worlds. Fix the training-world set (720 worlds) shared across all six fits (declared recipe difference from D2's seed-specific worlds; seeds then differ only in initialisation and sampling), cache menus by world seed: 720 × 4 s ≈ .8 CPU-h once; panels use the sealed dev/hold-out layouts (0 cost). Full search everywhere (candidate-stage menus would make the hold-out comparison against sealed P_relay^on incomparable).
- Overlap: none.

##### C4 — Clipped-action policy-gradient repair for D2's arms (single-agent inspiration: CAPG-style log-probability of the executed action)

Rejected as a direction: it is a recipe repair after scores on the same arms (constitution §3 forbids the rename-and-retry), single-agent in content, and the owner rejected diagnosis successors. Carried as a confound note (2.3) that the target interface removes; a future per-step-velocity arm on any host should declare its treatment prospectively.

##### C5 — Imitation/curriculum from the planner, then RL

TRIED (`energy_relay_imitation` B01/B02 on S7: partial mean gain, adverse worlds; round-3 memo C15 not selected). Rejected.

##### C6 — A dynamic coupled host (user mobility, member loss) to create planner headroom

Rejected now: no mobility flag exists (2.8) → a new host; the owner buys a new host only when the question cannot be asked otherwise, and the substrate question can be asked on the existing one first. Member-loss questions overlap Root's `uav_availability_recovery`.

##### C7 — Untied-K / untied-N on this host

Premature: no competent instance; both are Stage 2 by the owner's own two-stage framing. Not selected; they are what a positive C2/C3 buys.

#### 4. Recommendation: two concurrent questions, one shared engineering step

**Zero-fit first actions (day 1 morning, both questions):**

4.1 One implementer task T-W (Opus/high, ≈ 8–12 h): a macro-step mode in `adapter.py` (`ContractCountAdapter` variant) that takes one action per UAV per 10 host steps, runs the executor's action rule inside the wrapper for 10 host steps (unit-ball clip unchanged), returns the mean contract r and the boundary state/obs, and feeds `WorldTracker` every *host* step so the sealed P2 readers stay comparable; three action contracts — `target` (absolute xyz in the arena/height box), `slot` (categorical over the six menu positions; the menu appended to the observation for both arms, 6 × 3 scaled floats + role tag; `R_Actor` supports `Discrete` natively, `networks.py` 1663–1664, `agent.py` 1993/3271), `offset` (D1′, only if its gate passes); floors (random-target, random-slot, sticky-random, nearest-unclaimed); menu cache by world seed; runner macro mode (the `(lanes, 6, 3)` action assertion, `d2 decision_steps*10 == steps`, `validate_config` k ≤ episode_length and rollout % episode, k = 1 in macro units, 800 team decisions per rollout as before). The B12/P3 collector assumes cap = 10 host steps and is **not** touched now (owner rule 1: instruments after the conditioning result).

4.2 D1′ headroom gate (C1) on `local_linux`, < 1 CPU-h, read by the rule in C1 before any fit.

4.3 Four 3-rollout probes (SET-T, H-T, SET-slot, H-slot) on `wsl_4070` ≈ 0.3–0.5 CPU-h total: they price the batches (owner rule 6); no learner score is used.

**Q-A — `coupled_host_target_substrate` (C2).** Arms SET-T and H-T (paired seeds 932201/931201, 932307/931307, 932413/931413; shared training worlds; 360k host steps = 36k macro decisions per fit, 16 lanes × 50 macro steps × 45 rollouts, panels as D2). Declared batch: six fits, launched pair by pair, pair 1 first as the refuting unit; pre-declared kill: if both pair-1 arms end ≤ stationary + .10 on the hold-out deterministic c45 panel, the batch ends under the nonactivation row (a stop, not a go rule; not extension after scores). Cost: DERIVATION ≈ 1.1–1.8 CPU-h per fit → ≈ 7–10 CPU-h for six; if the probe projects more than 10 CPU-h for six, declare SET-T ×3 as the batch and H-T ×3 as a separately declared later batch. Readers: the D2 panel readers plus two zero-cost counters (fraction of decisions with |target − position| > 300 m, i.e. velocity-like use of the interface; target-change rate per episode). Endpoint bands on hold-out C̄_bh (c45, deterministic, "2 of 3" reading rule, all three reported):
- Band 0 ≤ .27 (nonactivation): the incompetence is not the velocity interface; existing packages do not learn on this host at this exposure at either interface → stop learner fits on this host; Stage 2 is not built on either package (a justified stop). Prior SET-T 25 %.
- Band 1 (.27, .64): direct service without chains — the "hare" → the failure is joint chain commitment, not execution; the substrate exists at the target level and the Stage-2 algorithm question becomes correlated commitment (reconnect Z to the actors; menu scaffolding per Q-B; MAVEN-type latent). Prior 45 %.
- Band 2 [.64, .71): flat-competent (≥ P_flat^on) → SET-T/H-T are a usable substrate; buy the P3 reader in macro units on H-T checkpoints then. Prior 22 %.
- Band 3 ≥ .71 (the D2 P2 line, L2 ≥ 0): a competent coupled instrument; roles testable; cell-2 (SeqAU) re-evaluated only under D2's joint condition. Prior 8 %.
- Hierarchy value: paired H-T − SET-T ≥ +.03 r AND ΔC̄_bh ≥ 0 on ≥ 2 of 3 (the D2 P4 rule) — prior 15 %; otherwise no hierarchy claim.
Wording of any positive: "a target-level package reaches band k on this host"; no algorithmic novelty, no causal claim about the interface (six things change together: cadence, PPO horizon, samples per update, executor profile, action support, clip confound).

**Q-B — `coupled_host_slot_allocation` (C3).** Arms H-slot and SET-slot (same pairing and exposure as Q-A; shared 720-world training set; menus cached ≈ .8 CPU-h once). Declared batch six fits, pair 1 first; kill if both ≤ random-slot + .10. Cost ≈ 7–10 CPU-h derived, probe-priced, same fallback rule as Q-A. Comparators M, N, random-slot, sticky-random (zero fits, minutes). Readers: C̄_bh, far-cluster share, arrival step, plus zero-cost per-decision counters already implied by the interface (slot conflicts per decision, slot switches per episode) — reported descriptively; no MI/label→slot instrument until an arm activates. Outcome rows (hold-out c45, "2 of 3"):
- Row 0: both ≤ random-slot + .10 → even a six-way allocation is not learned at this exposure → the learners' failure is optimisation at any interface; coordinator line has no substrate here. Prior 20 %.
- Row 1: SET-slot ≥ N − .02, H-slot < N − .02 → flat suffices; the coordinator does not learn allocation with competent execution → Stage 2 on flat/anchored forms; coordinator-based K/N deprioritised. Prior 30 %.
- Row 2: both ≥ N − .02, |H − SET| ≤ .02 → no allocation value of the hierarchy; conflict counters descriptive. Prior 30 %.
- Row 3: H-slot − SET-slot ≥ +.03 C̄_bh on ≥ 2 of 3 with lower conflict rate → the sequential coordinator has measurable allocation value → retain HMASD's coordinator as the Stage-2 substrate; roles become testable (P3 reader in macro units bought then). Prior 15 %.
- Any arm > M + .01 → reader/menu fault check before any reading (a learner cannot beat the planner's own slots). 5 % other/technical.

4.4 Why these two together: they bracket the coupling. Q-A asks whether the packages can *discover* chains from free targets; Q-B asks whether they can *allocate* chains when the menu supplies them. Band 1 in Q-A together with row 2/3 in Q-B says the algorithmic target for Stage 2 is joint commitment/correlated exploration, not execution and not information — a belief change with a concrete investment behind it. Row 0 in both closes the coupled-host learner line at the package level, cheaply and honestly.

4.5 Node and cadence: up to four concurrent fits on `wsl_4070` (torch_threads 4 each = 16 of 20 cores; RSS ≈ 2 × 2.5 + 2 × 1.1 GB against 14.9 GB available at the last check) is feasible; one CONTROL message to Root for node time; SPARSE-CONE/rsync rule as in D2. Wall: each pair ≈ 30–40 min derived; both batches fit in one day with the engineering step in the morning.

4.6 Review path: the wrapper is a new action contract, not a new host or metric, so no pre-declaration Pro review is owed (owner rule 3); one critic pass (separate context) on both declarations under §5 item 1; Pro at this round boundary for synthesis/next-question selection with this memo, the D2 batch reading and the critic's dissent as inputs.

#### 5. Alternatives rejected and why

C1 as a fit before its zero-fit gate (headroom bounded, 2.6); the team-level candidate chooser (bandit with an unbeatable comparator); C4 (recipe repair, single-agent); C5 (TRIED); C6 (new host; overlaps Root's availability question); C7 (no substrate yet); re-running D2's H/SET with more steps or a second seed (extension after scores); an S7-S1 coupled instrument on CUDA (the round-3 next-best; loses on cost and on the same interface hazard); TRDL replication (no decision object today).

#### 6. Risks and what I would refuse to do

6.1 Refuse: any tuning after scores; one fit per seed; no second seed; no extension; no CAPG repair of D2's arms; no host change to manufacture headroom; no novelty claim for the target or slot interface; no instrument (conflict/MI/P3 macro collector) before an arm activates; no "go" rule after a favourable pair-1 score (only the declared kill).
6.2 Risk: 800 rows per rollout is a small PPO batch; if curves are still rising at c45 that is an exposure outcome to record, not a reason to extend.
6.3 Risk: k = 1 in macro units changes BPTT/GRU chunking for both arms and H's d2 clock semantics; declare as recipe differences, verify the d2 acceptance counts (800 decisions per rollout) in the probe.
6.4 Risk: the target interface can be used as a velocity interface (targets > 300 m away are straight-line commands); the zero-cost counter above reports it; the W′ objection is then a reading, not a design flaw.
6.5 Risk: the slot menu is planner output — the same ground-truth information SET's actor already receives (2.4), processed by an ordinary planner; every comparator gets the same menu; acquisition cost stated (4 s/world). Not privileged.
6.6 Risk: two directions on one host — separate declarations, separate stop rules and cost caps; the shared wrapper is engineering, not scientific overlap.

#### 7. Evidence I could not find, and disagreements with the session's framing

7.1 Not found: a measured cost for any macro-step fit (derivation only; the probe prices it); MAVEN's PDF locally; the seed SD on this host (D2's within-arm hold-out ranges .02–.09 are the only guide — a .03 rule sits inside them, which is why the bands are .10 wide and the P4-style ±.03 is kept only as the pre-declared paired rule); a direct verification of the unclipped-log-probability storage in `hmasd/agent.py` (NOTES is the source); the third P3 reading (pending; cannot change "≥ 2 of 3").
7.2 Disagreement (i): "learner incompetent on continuous low-level execution" is too coarse — the precise statement is incompetence under the per-step velocity interface with an AND-coupled reward, with execution-time information ruled out for SET (2.4).
7.3 Disagreement (ii): "the coordinator barely moves" is true but not the cause — SET has no coordinator and fails identically; do not build a coordinator-repair question on it.
7.4 Disagreement (iii): the D1′ sharpening's "comparator = the planner itself" is right, but on this static host the planner is near-unbeatable with the same information; the correct first act is the zero-fit headroom gate (C1), and the per-agent slot form (C3), not the team-level candidate choice, is the version with MARL content.
7.5 Disagreement (iv): none of the recommended questions is NEW; the owner's rejection of re-skinned ideas is met by labelling them RECORDED and justifying them by decision exposure and cost, not by novelty. If the owner requires a NEW idea for a slot, the honest answer is that the record contains none that is cheap, on-line and runnable on an existing competent asset today; the correlated-commitment question that Q-A band 1 would open is the first place a genuinely new algorithmic contribution could be attempted.

## 2026-09-29 15:36 UTC — Critic review of the Oracle memo (ResearchCritic, Opus/high, separate context): MATERIAL_DISSENT on Q-A as written, ACCEPTED; correction to the 15:09 batch-reading "precise statement"; revised order of purchase (cheapest refuting fit first)

**DM verification before disposition (from the committed records, not the critic's text).** `training.jsonl` `losses.action_entropy` at rollouts 1 / 23 / 45: H 931201 4.33 / 6.14 / 7.66, H 931307 4.33 / 6.13 / 7.56, H 931413 4.34 / 6.25 / 7.74, SET 932201 4.33 / 6.29 / 8.00 (SET 932307/932413 in the same class); c45 hold-out deterministic panel (H 931201) `action_clip_events` 2,848.5 of 3,000 UAV-steps per episode; per-rollout training C̄_bh mean first → last: .19 → .21, .10 → .26, .13 → .14, .16 → .19 (SET 932307 .07 → .28, SET 932413 .13 → .12) against the .18 random floor. `config.json` of every fit carries no `continuous_action_distribution` key; `hmasd/networks.py` 1626 and `hmasd/r_mappo_utils.py` 220 default to `gaussian` = `DiagGaussian` (state-independent log-std, no clamp), while `TanhDiagGaussian` (r_mappo_utils 112–165, clamp from `args`) exists and S7's `configs/config_1.py` 464–467 selects it with init −1 / clamp [−5, 0]. One trap found in the DM's own read: the `Args` wrapper in networks.py 1629–1638 defaults the log-std bounds to init 0 / min −20 / max 2, so selecting the head alone would **not** give the [−5, 0] clamp — all four keys must be set and must land in the run's config.json. Verified: the critic's load-bearing facts hold.

**Correction to the 15:09 entry (batch reading).** The sentence "The precise statement is: incompetence under the per-step continuous velocity interface with the AND-coupled team reward …" overstates what is known and is withdrawn. Established: both packages ended far below the no-relay "hare" level (P_flat^on .639) with training C̄_bh never leaving the random floor; action entropy grew monotonically to ≈ 7.6–8.0 (σ ≈ 3.1–3.9 per axis under λ_l = .05 with an unclamped state-independent log-std) and ≈ 95 % of deterministic c45 actions lie outside the feasible unit ball. NOT established: the attribution to the per-step velocity interface or to the AND-coupled reward. The simplest alternative — the unbounded head plus the entropy bonus under this recipe (RECORDED: ACG B03–B05 action law / λ_l, S7 `tanh_gaussian` head) — fits the below-hare level, which the stag-hunt account (memo 2.5 / 7.2) does not. The SET execution-time information fact (2.4) stands. The round-boundary statement is amended accordingly: "not a learner substrate on it at this interface and exposure" → "not a learner substrate under this recipe (unbounded Gaussian head, λ_l .05, per-step velocity interface, 360k steps)". The RESEARCH row is corrected in the same commit.

**Disposition (every critic item; nothing kept against the critic, so no residual goes to the owner or an independent review):**
- R1 ACCEPT — every Q-A arm declares the head prospectively: `continuous_action_distribution = tanh_gaussian`, logstd init −1.0, clamp [−5.0, 0.0] (the S7 values), λ_l .05 unchanged so the head is the sole change from D2's SET recipe; two zero-cost readers: per-rollout log-std / σ trajectory and the fraction of decisions at or within one σ of the box bound. Configuration exposure of the four keys assigned to T-W (in flight; per-step default bit-identical).
- R2 ACCEPT — band 0 rewritten as "no substrate at this interface, head and exposure"; every interface-attribution phrase struck from the bands. The recommended matched per-step control **SET-V-b** is bought and is the **first** fit of the round (owner-approved sizing rule 1: cheapest refuting run first): D2's SET recipe with the bounded head only, per-step velocity interface (the owner's path-planning interface), one seed, ≈ 4.3–4.6 CPU-h on `wsl_4070`, no macro adapter needed. Readings: activates → D2's failure was the action distribution, not the interface; the per-step interface stays a viable Stage-2 substrate and the target wrapper is unnecessary for Q-A. Does not activate → SET-T-b next. It is a new question with its own kill rule, not a repair of D2 (D2's four readings stay frozen; constitution §3).
- R3 ACCEPT — the c00 deterministic floor and the all-at-BS static bound (≈ .20; BS at the arena centre) are reported beside the random-target floor; the declaration states where normalised 0 maps.
- R4 ACCEPT — H-T at k = 1 macro tests a label→target factorisation at a shared clock, not temporally extended skills; H arms only after a SET arm clears band 0; d2 acceptance at k_max = k_Z = 1 verified in the probe before any H-T declaration.
- R5–R10 ACCEPT (Q-B) — mechanism (conflicts, switches) read on training and sampled rollouts, contrast stated as learnability not representation; zero-cost coordinator-activation reader (`parameter_motion` already logged, label entropy and distinct labels per decision at c15/c45); "> M + .01 → fault" struck, replaced by a reported reading with a menu check only above M + .066; a held random-permutation floor added; row thresholds widened to the ≥ .05 class with the conflict rate co-primary; memo 6.5 corrected (the menu is new information for H's actor relative to D2, not privileged relative to Q-B's comparators); the thin Stage-2 link on a static host is stated.
- D1′ gate ACCEPT WITH REVISIONS — one scale (closed-loop C̄_bh via integer backhauled-user counts), correction bounded to D1′'s own feasible set (300 m xy disc, |dz| ≤ 50 m), exact arithmetic in the kill rule (assigned to T-G as an addendum; its first hand-back had exactly the critic's two defects: sweep on r while the rule reads C_bh, unbounded drift up to 372 m). The gate runs once on `local_linux` (≈ 0.10 CPU-h measured on two worlds) as a recorded cheap check; "not bought" is the expected reading and it does not gate Q-A.
- Cost ACCEPT — H-T re-priced from probes under the planned concurrency (D2 saw ≈ 2× under contention); the memo's > 10 CPU-h fallback applies.
- Labels ACCEPT — C4 carries RECORDED; W/W′ objection (six co-varied changes) transfers to Q-A and is carried in the declaration.
- Critic conjecture not adopted as fact: that S1's competence despite entropy growth came from S1's reward shape.

**Revised order of purchase (all RECORDED).** (1) SET-V-b, one seed, first. (2) SET-T-b (needs T-W), one seed. (3) H-T / H-V conditional on a SET arm clearing band 0. Q-B (slot allocation) independent of Q-A, after T-W and its probes. Declarations follow the round-boundary Pro synthesis within a bounded window (inputs: memo, batch reading, this review); under sizing rule 4 the SET-V-b declaration carries an executing default.

### Critic review (verbatim, ResearchCritic hand-back 2026-09-29)

## Independent scientific review: Oracle memo for the next two questions after `coupled_host_joint_skills_stage1` b01 (ResearchCritic, 2026-09-29)

**Disclosures.**
- **Context contamination.** The assignment text summarised the memo's proposals (Q-A/Q-B/D1′, bands, kill rules) before I had looked at any evidence, so this was not a blind reconstruction. I did not inherit any DM or Root conversation. I reconstructed from NOTES lines 1–668, the run JSON and source, and only then opened the memo.
- **Hold-out data.** I read the user positions of the hold-out worlds (`runs/coupled_host_joint_skills_stage1/b01_gate_holdout_a01/worlds/*.json`) to compute one static bound. The batch is closed and its hold-out references have already been read, so no seal is broken, but I am stating it.
- **Scope.** Read-only. I wrote nothing and ran nothing except read-only analysis of existing JSON with the scientific venv.

### A. My provisional reading of b01, formed before reading the memo

The six `training.jsonl` files show the same pattern in every fit, H and SET alike:
- **Action entropy** rises monotonically from 4.33 to 7.56–8.34 at rollout 45. The log-std is a single state-independent parameter per axis (`hmasd/r_mappo_utils.py` 73–107, no clamp), so σ goes from 1 to about 3.1–3.9 per axis. The driver is λ_l = .05 on the Gaussian entropy (`hmasd/agent.py` 6860–6868).
- **Clip fraction** goes from .80 to .995. The host clips to the unit ball (`host.py` 104–127).
- **Training backhauled coverage (C_bh) stays at the random-floor level for all 360k steps.** Per-rollout means range .08–.29 against a random floor of .18. The training team reward shows no trend in any fit (for example H 931201: .122 → .143; SET 932413: .089 → .079).
- **Deterministic c45 panels clip 2,783–2,926 of 3,000 UAV-steps.** The c00 panels clip 0. So the policy mean itself ends up outside the feasible ball about 95% of the time: the deterministic policy flies at full speed and never holds a position.
- **Both learners end far below the "hare" level.** Hold-out C̄_bh is .21–.24 against P_flat^on at .639. P_flat^on needs no relay: a UAV within about 1.19 km of the BS routes directly.

My reading is that neither package learned anything useful. The behaviour policy is noise-dominated and saturated, so it cannot hold the kind of position that even the no-relay layout requires.

This is the strongest simpler alternative to the NOTES and memo explanation ("per-step velocity interface under an AND-coupled reward"). I label it RECORDED, not NEW:
- On S1, ACG saw the same entropy growth (7.3–9.0 in `s1_count_b01_*` and `s1_action_law_b03_*`) and studied the action law and λ_l = 0 in B03–B05, where the packages were still competent.
- On S7, the native `tanh_gaussian` head (`configs/config_1.py` 464–467) was used and the learners were still incompetent.

So I do **not** claim the entropy/clip effect is *the* cause. Its effect depends on the host. It is a confound that carries over to any continuous-action arm under this recipe, and it is the only explanation I found that fits the below-hare level.

### B. Findings

**F1. Source facts 2.1–2.8.** Seven are verified as stated and one only by grep; 2.3 and 2.5 are correct as facts but carry wrong inferences.
- **2.1 verified.** G is .106 / .121 and G_C,cl is .152 / .141. Minima are −.010 / −.087. Worlds below .05: 3 of 32 (dev) and 7 of 32 (hold-out); that is the memo's "3/7".
- **2.2 verified.** Hold-out C̄_bh and the counts of worlds below the stationary floor (12/12/9 and 9/12/17) are correct. Worlds above P_flat^on: 0 in every fit.
- **2.3: the fact is correct; the inference is false.**
  - The fact: DiagGaussian samples the unclipped action and its log-prob, the host clips inside its own `step`, and the runner asserts the stored actions are unchanged (`runner.py` 676–697).
  - The inference: "disappears at a target-level interface" does not follow. Memo 4.1 specifies the target only as "absolute xyz in the arena/height box" and says nothing about the output head or λ_l. With the same DiagGaussian, λ_l = .05 and clip-to-box, the same mechanism pushes targets to the box boundaries, and σ of about 3.5 in normalised units makes sampled targets essentially the arena edges.
  - The memo also missed the entropy trajectory, which I think is the more important half of the confound.
- **2.4 verified.** `models.py` `SetActorBase.forward` (144–158) slices the 133-dim state out of the actor input, and `configuration.py` `information_entry_points` agrees. Minor: that string says H's actor receives "team and agent labels", but the T4 structural check (NOTES 474, 587) shows the team label has zero effect on the action.
- **2.5: the structure is correct; the explanation is contradicted by the data.** In `host.py` 138–177 a user counts only if its serving UAV is in `routing_paths`, so AND-coupling holds for far clusters. But the stag-hunt account predicts that learners reach the hare (about .64) and fail only on relay chains. The observed .21–.24 is far below the hare, so the derivation does not explain the level actually reached. The NOTES "precise statement" and memo 7.2 both rest on it.
- **2.6 verified by recomputation from the gate `worlds/*.json`.** Descent gain is .054 (dev) / .058 (hold-out), with max .115 on dev (.102 on hold-out). The best candidate beats P_flat by .052 / .063, on 28 of 32 worlds on both panels. Travel cost is .066 on both panels. Arrival averages 83 / 79 steps, with maxima 116 / 123.
- **2.7** matches NOTES.
- **2.8** is consistent: I grepped for mobility terms and found nothing. That is grep-level only.
- The autoregressive z_i | Z, z_<i sampling at `networks.py` 824–845 is verified.

**F2. The consequential question is right in kind but mis-specified.** "Is there any cheap competent substrate on this host" is the right successor. As designed, though, Q-A varies the interface while leaving the most likely confound in place, and it contains no arm at the owner's main-line interface: per-step velocity is the path-planning interface.

The memo also rejects C4 as "a recipe repair after scores" while accepting an interface change after scores. Both are prospective changes after scores. Constitution §3 forbids repairing the failed arm to rescue D2's claim; it does not forbid declaring a new question. A bounded head can therefore sit inside the substrate question without becoming a diagnosis successor.

The better question, stated concretely: **does an existing package with a bounded action head become a competent learner on this host, at the per-step velocity interface or only at the target interface?**
- Arms: SET-V-b (the per-step interface with the native `tanh_gaussian`, logstd clamped to [−5, 0]; one seed, about 4.3 CPU-h from D2's SET cost) and SET-T-b (the target interface with the same head; about 1–1.5 CPU-h).
- H arms only after a SET arm activates.
- Comparators: P_flat^on (.639, the hare line), P_relay^on, stationary, random, and the c00 floor from F3.
- Distinct predictions:
  - SET-V-b activates: D2's failure was the action distribution, not the interface. The per-step path-planning interface stays a viable Stage-2 substrate, and the target wrapper is unnecessary.
  - Only SET-T-b activates: holding or temporal abstraction matters given a bounded head. The memo's interface reading becomes supported.
  - Neither activates: an honest "no substrate at this exposure".
- What tempers the prior: S7 used tanh and was still incompetent.

**F3. Q-A readability.**
1. **Band 0 is the problem.** Its consequence ("the incompetence is not the velocity interface … stop learner fits on this host; Stage 2 not built on either package") is a causal, programme-level stop. It contradicts the memo's own disclaimer at line 96 ("no causal claim about the interface"), and it would be read from an observation that the 2.3 confound shapes if the head is unbounded.
2. **Floors.** If normalised 0 maps to the arena centre, the initial deterministic mean (gain .01) sends all six UAVs to the BS, which `host.py` puts at the centre. My static bound for all six hovering over the BS is about .20 C̄_bh (dev .206, hold-out .195; 6 of 32 worlds reach ≥ .27). The band-0 line of .27 is therefore only about .07 above what an untrained target policy may deliver. Measure the c00 deterministic floor and the all-at-BS floor and report both.
3. **H-T at k = 1 in macro units.** The low-level "skill" becomes a single action, so the hierarchy is a label→target factorisation at a shared clock rather than temporally extended skills. The discriminator intrinsic terms, which are 2–3× the environment term per step in D2 (team-discriminator −.042 and individual −.017 against env +.02 to +.03), see one-step segments. "Packages unchanged except the action contract" is therefore not credible for H. I did not verify d2's edge semantics at k_max = k_Z = 1; I only know the `validate_config` constraints from NOTES 393.
4. **Effective horizon.** γ = .99 per macro step means the effective horizon becomes about 1,000 host steps. The memo's list of six co-varied changes covers this under "PPO horizon"; fine.
5. The memo's 300 m counter for velocity-like use of the target interface is good; keep it.

**F4. Q-B.**
1. **The contrast is learnability, not representation.** SET's actor has the ego one-hot plus the full state (plus the menu), so independent per-agent argmax can represent any deterministic conflict-free permutation. The "sequential vs independent sampling" contrast can only show up in exploration and sampled behaviour, so conflicts must be read on training rollouts and the sampled panel. The deterministic panel is the outcome only.
2. **Coordinator nonactivation.** In D2 the coordinator moved a relative L2 of only .068–.071 over 675 optimizer calls at lr 1e-4. A row 1 or row 2 null in Q-B would be confounded by finite optimisation of the coordinator. A zero-cost coordinator reader is needed so that a null reads as "coordinator nonactivated" versus "active but useless": parameter motion, label entropy, and distinct labels per team decision at c45.
3. **M is not an upper bound.** Min-makespan minimises the maximum travel distance, not 500-step C̄_bh, and re-choosing slots every 10 steps can reorder deployment (relays first, for example). A learner can legitimately exceed M by up to about the .066 travel term. The rule "> M + .01 → fault" is wrong.
4. **Ordinary comparators.** N (nearest-unclaimed) is an appropriate strong, simple decentralised rule. SCC's record says de-duplication (+.324) dominates assignment optimality (+.007), so add a **held random permutation** floor (conflict-free, no travel optimisation). That separates de-duplication value from travel value.
5. **Row thresholds.** The ±.02 thresholds sit inside the observed within-arm seed spread of .02–.09.
6. **Memo 6.5 needs correcting.** The menu contains no information beyond SET's actor input, though it hands SET the planner's search result. It is **new information for H's actor** relative to D2 (90-dim local observation only). It is not privileged relative to Q-B's own comparators.
7. **Framing is honest.** Adoption value is nil, and the study is about understanding and investment. The link to Stage 2 (untied K/N) is thin on a static host: holding a slot is trivially "forever". Say so.

**F5. D1′ gate: well-posed only weakly; not material.**
- The budget never bound (1,143 of 3,000 evaluations on average, every start converged at 25 m). A 10× budget therefore measures only the extra starts and the 10 m stage, so H_static ≤ .02 is nearly assured by construction; the memo's 80% prior reflects that.
- The kill rule mixes scales: static r at the final layout against closed-loop 500-step C̄_bh.
- The ±25 m sweep has no feasible set bounded to D1′'s 300 m offset disc (Pro §7 asked for an identical feasible set).
- The structural argument alone (static world, same-information planner, a 300 m offset cannot shorten chain formation) already justifies a recorded no-run.

**F6. Cost.**
- **SET-T: 1.1–1.8 CPU-h is plausible.** Low-level rows fall from 8,000 to 800 per rollout, the update was 84% of wall, and host steps (panels included) are unchanged. My estimate is about 0.8–1.5 CPU-h.
- **H-T is probably underpriced.** D2's H−SET update gap of about 30 s per rollout on the node is coordinator and discriminator work, and the coordinator's row count (800 decisions per rollout) does not shrink at macro level. My derivation is 2–3 CPU-h per H-T fit, so six-fit Q-A is about 9–13.5 CPU-h. That probably triggers the memo's own ">10 CPU-h" fallback, which handles it.
- Both batches plus menus (0.8) and probes land at about 20–28 CPU-h, inside the 35 CPU-h class but not "well under 10" per study.
- Four concurrent fits (16 threads on 20 cores) will inflate metered CPU-seconds; D2 saw about 2× under contention locally. Price from the probes taken under the planned concurrency.

**F7. Labels.**
- W/W′ (energy_relay_benchmark NOTES 6737–6739): RECORDED is correct. Note that W was a 300 m disc target and Q-A uses an absolute destination; the earlier critic's six-co-varied-changes objection transfers.
- cooperative_planning B02, uav_transit_handoff (residual declined, MATERIAL_DISSENT no, lines 398–449), and SCC (+.007 / +.324 at line 386): cited correctly.
- C4 should also carry the label RECORDED (ACG B03/B04/B05 action law and entropy; S7 tanh). No label is wrong; C4's rejection reasoning is (F2).

### C. Verdicts and required revisions

**Q-A (`coupled_host_target_substrate`): MATERIAL DISSENT as written. It becomes ACCEPT WITH REVISIONS once R1–R4 are made.**
- **R1.** Declare the target output head and entropy term prospectively: native `tanh_gaussian` with the logstd clamp, or a discrete target set. Add two zero-cost readers: the per-rollout logstd/σ trajectory, and the fraction of target decisions at or within one normalised σ of the box bound.
- **R2.** Rewrite band 0 as "no substrate at this interface, head and exposure" and strike every interface-attribution phrase from the bands. Required: R2. Recommended in addition: the matched per-step control SET-V-b (same bounded head, one seed, about 4.3 CPU-h), tied to the per-step path-planning interface. Without it, no reading may say anything about "the velocity interface".
- **R3.** Report the c00 deterministic floor and the all-at-BS static bound (about .20) beside the random-target floor; state where normalised 0 maps.
- **R4.** Narrow the H-T wording: at k = 1 macro it tests a label→target factorisation, not temporally extended skills. The P4-style hierarchy claim is limited to that. Verify d2 acceptance at k_max = k_Z = 1 in the probe.
- **Order.** SET-T-b (and SET-V-b if bought) first. H-T only after a SET arm clears band 0.

**Q-B (`coupled_host_slot_allocation`): ACCEPT WITH REVISIONS.**
- **R5.** Read the mechanism (conflicts, switches) on training and sampled rollouts, and state that the contrast is learnability, not representation.
- **R6.** Add a zero-cost coordinator-activation reader: parameter motion, label entropy, and distinct labels per decision at c15/c45.
- **R7.** Strike "> M + .01 → fault" and replace it with a reported reading plus a menu check only above M + .066.
- **R8.** Add a held random-permutation floor.
- **R9.** Widen the row thresholds to at least the .05–.10 class, or make the conflict rate co-primary.
- **R10.** Correct 6.5 (new information for H's actor relative to D2) and state the thin link to Stage 2.

**D1′ gate: ACCEPT WITH REVISIONS (not material).** Use one scale (C̄_bh, closed loop). Bound the correction to D1′'s own feasible set, or record D1′ as a justified no-run on the structural argument and skip the gate.

**Round-boundary statement.** It should add that training never left the random floor, that σ grew to about 3.5 in all six fits, and that the "AND-coupled velocity interface" explanation is not established. The DM's "precise statement" in the b01 batch-reading entry overstates what is known.

**Unverified by me.** d2 semantics at k = 1; the split of H's update time between coordinator and discriminators; 2.8 beyond grep; H-T/SET-T wall (derivation only); whether the S1 competence despite entropy growth came from S1's reward shape (conjecture).

MATERIAL_DISSENT: yes. It is about Q-A's six-fit purchase and its band-0 stop consequence as written. The target head and entropy term are undeclared, so the 2.3 confound carries over. The evidence is all six `training.jsonl` files (entropy 4.33 → 7.6–8.3, clip fraction → .995, training C_bh at the random floor) and deterministic c45 clipping of about 95%. Separately, the memo's stag-hunt explanation is contradicted by learners ending far below the no-relay (hare) level of .639. None of this is dissent against Q-B or the D1′ gate.
