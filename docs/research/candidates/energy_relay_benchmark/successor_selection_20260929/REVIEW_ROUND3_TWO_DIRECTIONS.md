# Independent scientific review: `MEMO_ROUND3_TWO_DIRECTIONS.md` (D1 `anchored_joint_target_refinement_s7s2`, D2 `coupled_host_joint_skills_stage1`)

hmasd-research-critic, separate context, read-only. Checkout main at c8795018d.

**Context disclosure.**
- I am a fresh subagent. I did not inherit the DM, Root or Oracle conversations.
- The assignment carried the brief's one-paragraph summary of D1 and D2. I read the round-3 brief, the round-2 review, the round-2 Pro answer and the scenario-2 / base-env code before the memo. I read the memo before the D1 code checks.
- Host facts were recomputed in memory with the environment's own functions. I used `/home/fires/.venvs/hmasd-linux-cpu/bin/python -c` with `PYTHONDONTWRITEBYTECODE=1`. Nothing was persisted, and there were zero fits and no node use.
- The layouts in those checks were built by me: k-means on users, and one relay placed on the BS→farthest-centroid line. There were 32 seeded worlds (reset seeds 1000–1031). These layouts are a proxy for the memo's planner gate, not the gate itself.
- `search_mylib.py` was run read-only.
- No file was written anywhere.

Tags: [V] read or recomputed first-hand; [I] inferred from [V]; [C] conjecture.

---

## Verdict in brief

**D2: revise, then retain.** It is the better of the two, and it is cheap. The host really does reward relaying. But the host's reward, as the memo would run it, has two defects that make three of the four predictions unreadable:
- a clip at 1.0 that binds in most relay-capable worlds;
- a normaliser that depends on where the UAVs currently are, which rewards moving an idle UAV away from the BS.

In addition, one declared constructor argument is silently overwritten.

**D1: revise the declaration. I recommend against it as the default.**
- Its modal outcomes restate a closure the owner already chose.
- [DECIDE-1] omits that the owner declined this exact option on 2026-09-28.
- The actor lacks the anchor it is offsetting.

**MATERIAL_DISSENT: yes**, on both purchases as declared. The resolving changes are listed at the end.

---

## 1. Host and code facts, recomputed

### (a) Channel constants and forced-relay reach

- **Which noise value applies.** −80 dBm applies to `scenario2.UAVCooperativeNetworkEnv`. [V]
  - `MultiUAVEnv.__init__` hard-codes `self.noise_power = -80` (`envs/pettingzoo/uav_env.py:120`).
  - `scenario2.py` has no noise argument (constructor 18–42).
  - `configs/config_1.py:83` (−94) reaches only the relay family: `routed_core.py:155, 258`.
  - The only construction sites of scenario 2 are the legacy `experiments/launchers/main.py:406` and tests. The current training launcher has no scenario-2 branch (`train_multiproc_config_1.py:4109–4163` handles base / belief_map / progress / energy / r39).
  - Printed after construction with the memo's arguments: `noise -80`, `bs_tx 23`, `tx 23`, `chan free_space`, BS `[2500, 2500, 30]`.
- **Do the 2.39 / 3.87 km reaches survive?** Yes, as single-user DERIVATION, but **only under `channel_model="free_space"`**. That is the constructor default (`scenario2.py:26`; `main.py:74`), and the memo never pins it. [V]
  - Under `urban`, the path loss is 128.1 + 37.6·log10(d/km) (`uav_env.py:782–783`). At −80 dBm that caps UAV links near 180 m.
  - `scenario2.py` 619, 640, 653 and 755 hard-code free-space loss for backhaul capacity and the throughput normaliser whatever the channel model is. Any other model would be internally inconsistent.
- **The single-user geometry understates the relay need.** [V]
  - At 23 dBm the BS link reaches only ≈ 1,194 m.
  - With UAVs at k-means-6 user centroids on the 5 km arena, only **.27** of UAVs have a routing path (32 worlds).
  - So most clusters, not "1–2 of 5", need a relay or a BS-ward compromise position.

### (b) Other host facts

- **`ground_bs_tx_power` pass-through:** real (`scenario2.py:41, 101` → `uav_env.py:147`). [V]
- **Static users, edge clipping, no N pin:** confirmed. [V]
  - Users move nowhere in `uav_env.step` (264–350).
  - Edge clipping is at `uav_env.py:532`.
  - With 50 users, `n_clusters = min(5, 50//10+1) = 5` (`:516–517`).
  - No validator touches scenario 2.
- **New fact: `max_connections=15` is dead.** [V] `scenario2.py:75` sets it, then `super().__init__` overwrites it with the hard-coded `self.max_connections = 10` (`uav_env.py:122`). The printed value is 10. The same happens to `min_sinr` (overwritten with 3, the same value, so harmless).
  - Consequence: 6 UAVs × 10 slots = 60 for 50 users in 5 clusters of 10. One UAV per cluster is saturated, and exactly one UAV is spare for relaying before coverage must be traded.
- **Reward composition (`scenario2.py:769–838`)** is `clip((coverage + T)/2, 0, 1)`. [V]
  - Coverage counts users connected to any UAV, with or without backhaul.
  - T is the sum of routed UAVs' front-end capacity divided by `_compute_realistic_max_throughput()` (`:733–767`).
  - That denominator is recomputed every step from **every** UAV's current direct distance to the BS, whether or not the link exists.
  - Recomputed in memory (32 worlds, 5 km, 23 dBm):

| Layout | Mean normalised reward | Clip binds |
|---|---|---|
| k-means-6 (no relay) | .722 | 4/32 |
| k-means-5 + 1 relay | .864–.908 (two k-means inits) | 17–20/32 |
| All UAVs at the BS | .164 | — |

  - Paired relay − k-means-6: **+.142 (SE .030, 25/32 worlds positive)**.
  - Moving the spare, idle UAV from the BS to the far corner raises T by **+.108** and the normalised reward by +.027, while coverage *falls* (.891 → .856). That is a service-free reward channel.
  - At 6 km: relay − k-means-6 = +.157 (SE .034); the clip binds 7/32.
  - At the default 1 km / 30 dBm: relay − k-means-6 = −.033 (SE .011), i.e. no coupling, as the memo says.
- **Per-step cost.** [V]
  - The reward is computed twice per step: `uav_env.step` (~301) calls the scenario-2 override on stale routing before `scenario2.step` recomputes it.
  - The O(N²) SINR pairs plus BFS are negligible: measured **.00075 s/step** at N6/M50 with random actions, single thread. That is ≈ 4.5 min of environment time per 360k-step fit, so the memo's ×1.3–2 environment multiplier is unnecessary. Fits are learner-dominated.

### (c) D1 facts

- **`H1r10` is H1 at a 10-step replan** (`b01/evaluation.py:191–196`). `switch_margin_m` 300 m is the default (`b01/heuristic.py:77`). [V]
- **The S7 state carries H's replan inputs**, so the memo's open L0 check closes in its favour and its fallback is unnecessary. [V]
  - User xy is in the state (`routed_core.py:480–496`, `4836–4870`), and `energy_aware.py:2302` appends to that base state.
  - The dimensions add up: 24 + 180 + 3 + 8 + 1 + 72 + 14 + 4 = 306.
- **Gap the memo misses.** [I] The actor must also receive **H's assigned target_i**.
  - H's Hungarian-with-hysteresis output depends on planner memory (`targets_xy`, `heuristic.py:282–294`) that is not in the state.
  - "obs + central snapshot" therefore cannot reconstruct the anchor that δ is added to.
  - Supplying target_i is a better use of already-lawful information, not an added resource.
- **SET recipe and the "10× smaller batch".** [V]
  - The SET recipe is `apply_algorithm_config(config, "mappo")`, k = 10 restored, central snapshot (`b02/configuration.py:125–133`).
  - `calculate_and_set_buffer_sizes` derives the minibatch from `num_envs × rollout_length / num_mini_batch` (`config_1.py:750–757`; `num_mini_batch` 4 at :215; `ppo_epochs` 15 at :156).
  - The claim is one possible wrapper choice, not a consequence of the recipe. A 600-row macro buffer against a computed 1,500-row minibatch (12,000 agent rows) is an unspecified L0 point.
  - [I] Either way the real sample budget is 200 × 600 = 120k macro team decisions, each reused 15×. This leaves O − H unbiased, because the comparator is a planner, but it makes "SET recipe" nominal. Declare the minibatch rule before the fit.

### (d) Is `hmasd/ha_ctse.py` a live consumer?

No. [V]
- Last commit 2026-06-25 (a33974d86), before R30 (2026-07-14). It still carries `duration_head` (:336, 431).
- `use_horizon_window = False` (`config_1.py:253`; launcher presets `train_multiproc_config_1.py:362, 445`).
- It is absent from `RESEARCH.md`, and outside `hmasd/agent.py` only `tests/ha_ctse_test.py` imports it.
- The C3 row's "its keep/drop consumer exists" is therefore not supported. Pro's first A′ gap (a named follow-on implementation on the same host and contract that must choose AR or constant prefix) stays open.
- The prefix-usage reader is descriptive only.

### (e) Cost anchors

- **Verified:**
  - S7 SET rates .02736 / .03401 / .03006 s per transition (`successor_selection_20260928/REVIEW.md:37`).
  - FSD D128 at 2,160,000 team steps per 6 fits, i.e. 360k per fit (FSD NOTES 576, 729). D128 wall 5,554–10,047 s; D1280 9,885 s; peak RSS 1.9 / 2.75 GiB.
  - CF mean 6,776 s (494).
  - ACG serial H6 69.7–98.8 min, SET 53.6–89.0 min (`agent_count_generalization/NOTES.md:1244–1250`).
- **R's query cost is underpriced.** [V] → [I]
  - The record is 41.79 min *wall* for 24 episodes, 1.3765 worker-CPU hours, and R 68.7 % above G per world (`RESEARCH.md:873, 1023`). Wall divided by episodes ignores parallelism.
  - Assuming H ≈ G cost: R ≈ 4.7 worker-CPU min per 3000-step episode at replan 30. With the query-dependent part tripled at replan 10, that is ≈ 8–9 min.
  - 64 episodes (dev + hold-out) ≈ **6–10 worker-CPU hours**, not 4–6.
- **Resume is the expected case, not a 5–10 % reserve.** [V] Both 1.2M SET-family S7 fits died at rollout 117 / 113 and were resumed from c03:
  - `energy_relay_benchmark/NOTES.md:2830`;
  - `:6778` (`b05_canonical_frame_a01` died at rollout 113; `…a01r` resumed from c03).
- **Scenario 2 CPU:** the environment is negligible (above). The S1 learner anchors apply directly.

---

## 2. D1

### Identity contract

Substantively complete for deterministic c00:
- zero mean head;
- everything in H unchanged;
- δ = 0 never rewrites H;
- per-action equality within a tolerance, checked on the dev panel at 0 fits.

The memo states that stochastic c00 has no identity guarantee, and it excludes post-score adjustment. [V against NOTES 6938–6944]

Two fixes:
- **Calibrate on worlds off the reading panel.** Calibrating the log-std init against the stochastic c00 *dev* panel uses the reading panel for tuning. Use the fact / calibration seeds instead (the b02 spec has `fact_seeds`).
- **Add target_i to the actor input** (1c).

### Is R a legitimate secondary comparator?

Yes, if it is re-run under the O contract and its old panel is never reused. It is the strongest ordinary destination correction. It is used as a comparator, not re-skinned as the object.

Its record says "不默认替换或称安全" and notes reserve tails (`RESEARCH.md:1023`). Row 1's "adopt R-type ordinary correction" is therefore Root's investment, not the Claude line's.

### Pro's conditions and [DECIDE-1]

Pro's condition (as adopted, NOTES 7150): "O only as an owner-chosen exploratory package under the zero-residual identity contract, its modal outcome … conceded before purchase". D1 meets the contract and concedes the modal outcome. It still needs the owner.

**[DECIDE-1] is not stated honestly enough.** On 2026-09-28 the owner was offered exactly this, as option C ("conceded, not recommended", NOTES 7160), and chose A: "Option C (exploratory O fit) is not selected" (NOTES 7180).
- Circumstances changed: A is now shelved pending data. So re-offering C is legitimate.
- But [DECIDE-1] must say that it asks the owner to revisit that choice.
- It must not suggest that "选两个不重叠的方向推进" may already be the concession.

### Which outcome row is modal, and what changes

- **Modal: row 3 (near-H) or row 4 (exploration damage).** Two same-host learned-over-planner packages already read null or negative: [V]
  - `uav_joint_transition`: L chose the default D at all 800 clocks (`RESEARCH.md:1020`);
  - `uav_cooperative_planning`: L − P = −.016 [−.027, −.006] on H_central@10's information (`RESEARCH.md:1031`).
- **Rows 3 and 4 restate the standing state.** Pro's N plus the owner's A-over-C choice already closed this direction's S7-S2 learner line (NOTES 7129, 7150, 7180).
- **Row 1 moves only Root's asset.**
- **Only row 2 changes a real judgment:** the first learned gain over a competent planner on a coupled UAV host in the record, which would be a real headline. Its prior is low, but not negligible: R measured +.027 of destination-space headroom (J interval crosses zero), and destinations are the one object the two precedents did not learn.

### Other gaps

- **Independent-offset reader.** It needs eight single-agent deterministic panels per checkpoint: 8 × 32 × 3000 = 768k steps, ≈ 2 h at the memo's .009 s/step [C]. It is unpriced. Its summed-marginal SE grows about √8. [I] As declared it will likely be unreadable at 32 worlds, so it is descriptive only.
- **Type.** The memo's table labels D1 "algorithm", while §2 concedes "no algorithmic novelty". It is an exploratory learned-planning package comparison (RECORDED residual family), and it must be presented that way.

---

## 3. D2

### (a) Planner gate and the 6 km branch

- Comparing a relay-capable planner with the re-optimised no-relay member of the same search is the right *form* under constraint D.
- **P1 is near-certain, not ≈ 55 %.** A crude one-relay layout already beats k-means-6 by +.142 (25/32). [V proxy]
  - So the gate certifies coupling; it is not the binding uncertainty.
  - The single pre-declared 6 km branch is legitimate (one branch, declared, with a stop), not a search for a positive result. It is also moot on this axis. At 6 km the clip binds less (7/32).
- **"The same search" must actually be a search.** The memo's `LayoutHeuristic` with n_relay ∈ {0, 1, 2} on a BS→far-cluster line is a weak comparator here, because most clusters lack backhaul (1a).
  - Static users make a real placement optimiser cheap: ≈ 1 ms per evaluation, thousands of candidates per world.
  - The no-relay member is the same optimiser with UAV–UAV links disallowed.
- **The planner port is more than "central mode with the relay line changed".** `LayoutHeuristic.act` consumes the S7 observation layout, 4-D actions and shield modes (`heuristic.py:304–333`). Scenario 2 uses 3-D velocity actions scaled by `max_speed` 30 (`uav_env.py:280–291`) and has no shield.

### (b) FSD reopening, SCC re-entry, or a new decision object?

- **Not an FSD reopening.** [V] The condition speaks of "this host" (S1) and duration mechanisms (FSD NOTES 4134–4139; the second form at 4249). D2 is fixed k = 10 on a different host and changes no FSD row.
- **Cell 2 is SCC's recorded re-entry form**, a coordinator fit with a credit arm. Root's narrowing permits it under lessons (a)–(f) (SCC NOTES 384–390). [DECIDE-2] should name it as such.
- **Cell 2's prior from SCC's own record is low.** [V] → [I]
  - The arms differed "in learning speed, not in the end point" (SCC 161).
  - Exact SeqAU bought ≤ .1 % of J* at the corner, and the realisable ridge SeqAU lost under relay substitution (380).
  - A forced relay among homogeneous UAVs, where any member can relay, is the substitutable regime. The memo's claim that "a host with forced relays is that regime's realisation" (the binding, non-substitutable regime) is not supported.
- **Cell 1 is a new decision object:** coordinator competence on a cheap coupled host. It inherits `complementary_skill_learning`'s question family.

### (c) Matched-information flat arm and recipe choice

- **SET is a defensible competent flat baseline.** It uses the central snapshot at the coordinator's cadence and is ≈ H6 on S1-class hosts (ACG B16/B17). It is not FSD's CF.
- **"The competent flat baseline on this host" in FSD's text refers to S1.** SET on scenario 2 is a new-host reference.
- **Mixing recipes needs a declared matching table.** HMASD in FSD's D-route with SET from ACG (`configuration.py:45–60`, `policy_interruption_mode="off"`), ported into the FSD runner, needs a table covering lanes, horizon, hidden sizes, PPO epochs, coordinator batch, information and exposure.
- **D-route d2 is defensible** because the B12 collector's caps require it (`hmasd/agent.py:491–504`).
- **D128 is defensible:** no detectable difference from D1280 (FSD 713–745) and cheaper.

### (d) Are P1–P4 falsifiable, with honest odds?

- **P1:** falsifiable; the odds are understated (above).
- **P2 tests nothing about relaying.**
  - ".8 × P_relay" ≈ .69–.73 on my proxy.
  - The no-relay k-means layout scores .722.
  - It must be restated against P_flat and on native service. For example: the learner closes ≥ ½ of (P_relay − P_flat) in backhauled coverage, with far-cluster backhaul.
- **P4 and cell 2 are compressed at the clip.** With the clip binding in 17–20/32 relay-capable worlds, P4's +.03 (HMASD − SET) and cell 2's SeqAU − shared read on a saturated scale.
- **Both learners can exploit the normaliser channel** (+.108 T for an idle UAV parked away from the BS). A "service" gain can then be a normaliser gain.
- **Cell 2's gating on P3 ∧ P4 is a legitimate pre-declared conditional purchase**, not a retry allowance. But under SCC's record its expected value is small.

### (e) Type label

- **What D2 is not:** a cooperative-planning algorithm direction in the owner's sense.
- **What D2 is:** a competence/instrument stage for existing learners on a new cheap coupled host, with an unlikely gated credit cell.
- **Its decision object is real but prospective.** It decides whether future K/N algorithm work is built on HMASD's coordinator or on flat/anchored forms. No K/N investment is waiting on it today (FSD reserve; ACG archived; VNFC reserve).
- **How to present it:** say exactly that. The memo's label is close. Drop "gated algorithm cell" as a selling point.
- **Strongest useful positive:** a cheap coupled UAV host with a large, measurable relay opportunity (+.14 on a crude proxy) at .75 ms per step. That is the first host in the record where three-seed learner comparisons on a coupled problem cost CPU hours, not CUDA days. [V]

---

## 4. Independence

- **D1 vs D2:** different host, learner family and decision object. [V]
- **Codex Q1 (`uav_persistent_service`):** O keeps the dock / return / F logic and runs H3000, not H12000. Offsets up to 300 m can shift a UAV's pre-return position, but that is not deadline-aware reassignment. Adjacency is minor. [I]
- **Codex Q2 (`uav_message_content`):** different host and object. Q2's B02 is now admitted: CPU FP32 on `wsl_4070` (8f83e8076). The node's GPU is free, and its CPU is contended by Q1/Q2 panels. [V]
- **`uav_joint_transition` / `uav_cooperative_planning`:** D1 learns destinations; they learned staging and joint move/wait ordering. Distinct objects, but they are D1's closest adverse precedents. [V]
- **`uav_radio_placement`:** R is D1's comparator, not its object. Reuse needs one SCOPE line to Root.
- **`complementary_skill_learning` / `agent_count_generalization`:** D2 inherits their question family and recipes. It does not duplicate them (S1 there; new host here).
- **FSD / SCC:** FSD is not reopened; SCC is re-entered by cell 2 (3b).

No collision with a Codex decision object.

---

## 5. Constructive-development method

### D1

- **What it develops:** H_central@10 (.769, a Claude-line ordinary positive) and R's measured destination headroom.
- **Prediction / stop / cost line:** stated. The prediction is c02 O − H ∈ [−.02, +.03] with mean |δ| < 100 m; the stop is no second seed unless row 2.
- **Same addition to the ordinary comparator:** yes (the same targets, executor and clock).
- **Missing:** the anchor input (target_i).

### D2

- **What it develops:**
  - B12 as a coupling reader (recorded in the paradigm note, `docs/Claude_docs/research_notes/TEMPORAL_ABSTRACTION_…20260921.md:75–79, 468–471`; the brief's `reviews/` path is wrong);
  - SCC's partial positive (learning speed only);
  - FLAT/SET competence as the comparator.
- **Prediction / stop / cost line:** stated.
- **Same information for the planner:** yes (ground-truth users; the BS is a fixed constant, absent from the state).

### Looking back: was any stop premature?

- The FSD and SCC stops were not premature on their own evidence.
- One cheap derivation was warranted and never run across three rounds: **the zero-fit S7-S2 planner comparison that constraint D requires**. That is H1 (6 service + 2 relay) against the re-optimised no-relay variant (`n_service=8`) at the same information, ≈ 15 min per panel.
- It would have settled the S7 coupling argument that consumed rounds 1–3. It should run whatever D1's fate.

### The memo's disagreements with the brief

- **(i) JDSL AR gap is not a positive:** agree. It is one instance per arm with different seeds, inside the S1 instance spread; it is a duration mode, not this link.
- **(ii) FLAT is evidence of flat competence:** agree. Its constructive use is as the comparator.
- **(iii) Two algorithm directions are not purchasable today:** agree. D1 is also not one (§2).

---

## 6. TRIED / RECORDED / NEW

The labels are store-bounded. The My-lib search for "residual" and "relay UAV" found no MARL residual-over-planner paper and no UAV-relay paper. The nearest hint, Residual-MPPI (ICLR 2025, `iclr-2025-83ce241ce40aef32225eb2833ca2363c`, single-agent), was not read. Residual Policy Learning (Silver et al. 2018, arXiv 1812.06298) is cited at `uav_transit_handoff/NOTES.md:228`. A miss is not novelty.

**D1: RECORDED.**
- Pro's round 1 labels it RECORDED.
- The residual family is RECORDED and was declined on S7: a residual-PPO design at `uav_transit_handoff/NOTES.md:161–175`, declined at 441, 449, 518, where the reviewer said "conditional residual correction with no independently grounded new mechanism".
- Learned-over-planner packages on this host were TRIED twice, with null / adverse results (RESEARCH 1020, 1031).
- The only untried part is the destination-offset instance.

**D2: RECORDED question family.**
- `complementary_skill_learning` (RESEARCH 1063).
- The paradigm note's stage 1 (as recommended to the owner, B12 as coupling measurement).
- SeqAU TRIED on the microhost (SCC).
- NEW only as a host instance: no research record on scenario 2 (grep of RESEARCH and all NOTES), and the coupled parameterisation.
- The memo's "B12-as-coupling-reader NEW" dates from 09-21 and is now recorded.

---

## 7. Cost completeness and the smallest change per direction

### D1

| Component | Estimate |
|---|---|
| Fit | 1.2M native transitions, 9.1–11.3 h CUDA |
| Expected resume (2/2 precedents) | ≈ +1 h CUDA plus launch/record overhead; the resume path now exists |
| Panels | ≈ 3.5 h node CPU, as the memo says |
| R under the contract | ≈ 6–10 worker-CPU h [I] |
| Independent-offset reader | ≈ 2 h per checkpoint read [C] |
| Engineering | 20–34 h, plus target-input wiring, plus review |
| Node | panels queue behind Q1's H12000 CPU panels and Q2's CPU fits |

**Smallest change that makes it worth its cell:**
- the honest [DECIDE-1];
- target_i as input;
- off-panel calibration;
- the minibatch rule declared;
- a statement that only row 2 changes any investment.

Then it is a legitimate owner-chosen exploratory fit. It is not a default.

### D2

- **Cell 1 CPU:** learner-dominated at S1 anchors. 3 × D128 at 1.5–2.8 h plus 3 × SET at 0.9–1.5 h ≈ 7–13 process-hours, not 10–26. At 2–3 concurrent on `local_linux` (≈ 9 GB free), ≈ 4–7 h wall.
- **Panels:** the memo's 1.06M + 384k evaluation steps stand. The environment part of those is minutes.
- **Engineering is underpriced.** It needs:
  - a direction-owned scenario-2 factory (the legacy launcher cannot pass `area_size` / BS power / `max_steps`);
  - a reward-treatment subclass or reader;
  - a search-based placement planner with the no-relay member;
  - the SET arm ported into the FSD runner with a matching table;
  - the interaction reader.

  That is ≈ 25–40 h for cells 0–1 [C], plus review.
- **Cell 2:** as the memo prices it; low expected value.
- **Resume risk:** no S7 heap-fault risk. The memory ceiling is the risk (B07's 14 GB kill).

**Smallest change that makes it worth its cells:** declare the reward treatment before cell 0. Either:
- a direction-owned subclass with a per-world fixed normaliser and no clip, used for both training and reading; or
- native service readers primary (backhauled coverage, backhauled Mbps), with the clip-binding share and the normaliser-channel diagnostic reported.

Also:
- pin `channel_model="free_space"`;
- drop `max_connections=15`, or honour it in the subclass;
- make P_relay / P_flat a real placement search;
- restate P2 against P_flat.

---

## 8. Ranking, [DECIDE] items, dissent

**Ranking: D2 (revised) > D1.**

Strongest alternative to D1 [C]: run the anchored refinement on D2's host, with three seeds on CPU, after D2's cell 0.
- Pros: it avoids Pro's S7-S2 dissent and the heap-fault recipe, and it gives replication.
- Cons: it depends on D2's host, so the two directions would share a failure point.

Named here as an option, not a demand.

**[DECIDE] items that are genuinely the owner's:**
- **[DECIDE-1]:** revisit the 2026-09-28 choice of A over C, now that A is shelved. That means one exploratory O fit on S7-S2, knowing its modal outcomes restate the standing closure. My recommendation is no as the default, yes only as the owner's explicit revisit.
- **[DECIDE-2]:** accept D2 as a competence/instrument stage (not an algorithm contribution) that includes an SCC re-entry cell.

Arena, reward treatment, planner search and seeds are scientific/engineering contract items, not owner items.

---

## MATERIAL_DISSENT: yes

Tied to two purchases.

### 1. D2's six CPU fits as declared

Direct evidence:
- `scenario2.py:733–767, 769–838` (the state-dependent normaliser and the clip);
- the in-memory recomputation:
  - the clip binds 17–20/32 relay-capable worlds;
  - the idle UAV moved to the corner gives +.108 T with less coverage;
  - P2's .8 × P_relay is met by the no-relay layout (.722);
  - the gate proxy is +.142, 25/32;
- `scenario2.py:75` vs `uav_env.py:122` (the dead `max_connections`);
- `uav_env.py:120` and `scenario2.py:619/640/653/755` (the unpinned channel model);
- SCC NOTES 161, 380 (cell 2's prior and regime).

**Resolving change:**
- pin `free_space`;
- drop or honour `max_connections`;
- declare the reward treatment before cell 0 (a fixed normaliser and no clip in a direction-owned subclass, or native backhauled-service readers primary with the clip share reported);
- make P_relay / P_flat a same-information placement search;
- restate P2 relative to P_flat;
- label D2 a competence/instrument stage;
- have [DECIDE-2] name cell 2 as SCC's re-entry with a low prior.

### 2. D1's one CUDA fit as presented

Direct evidence:
- NOTES 7160 and 7180 (the owner declined option C);
- NOTES 7129 and 7150 (Pro's N; no new S7-S2 fit);
- RESEARCH 1020 and 1031 (same-host learned-over-planner nulls);
- `heuristic.py:282–294` (the hysteresis memory is not in the state);
- NOTES 2830 and 6778 (both SET-family fits resumed);
- RESEARCH 873 and 1023 (R's cost).

**Resolving change:**
- [DECIDE-1] discloses the prior decline and frames the question as a revisit;
- the modal rows are stated as restating the standing closure, with only row 2 changing an investment;
- target_i is added to the actor input;
- the stochastic calibration moves to off-panel worlds;
- the minibatch rule is declared;
- R's cost is repriced at ≈ 6–10 worker-CPU h, and one resume is priced as expected;
- D1 is typed as an exploratory package, not an algorithm contribution.

Separately, and at zero fits: run the S7-S2 relay-capable vs re-optimised no-relay planner reading regardless of D1's outcome.

Paths: the review object is `/home/fires/hmasd-wsl/docs/research/candidates/energy_relay_benchmark/successor_selection_20260929/MEMO_ROUND3_TWO_DIRECTIONS.md`; the brief is `/home/fires/hmasd-wsl/docs/research/candidates/energy_relay_benchmark/successor_selection_20260929/BRIEF_CRITIC_ROUND3.md`. Key code: `/home/fires/hmasd-wsl/envs/pettingzoo/scenario2.py`, `/home/fires/hmasd-wsl/envs/pettingzoo/uav_env.py`, `/home/fires/hmasd-wsl/experiments/candidates/energy_relay_benchmark/b01/heuristic.py`, `/home/fires/hmasd-wsl/configs/config_1.py`.
