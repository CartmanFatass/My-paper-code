# Open "Jev-like" decision models for HMASD: what is already known, what is left to test, and what the Claude side should do (2026-10-02)

Provenance: Claude Code cloud session `session_013LQX44wuT3dfQfhb79KwZB`, branch `claude/inspiring-ritchie-2kj46g`
off `main` at `a1d58a5d` (2026-10-02 UTC). Non-direction deliverable under `docs/Claude_docs/`
(CLAUDE.md). It is evidence for the owner, not a science card, a contract, a declaration or a
decision record. **Zero fits, zero native steps, zero model forwards, zero downloads.** The only new
computation is deterministic arithmetic on per-world results already committed under `runs/`.

Status boundaries respected: the Claude session is paused by the owner (quota, 2026-09-30,
RESEARCH.md routing row); a status question or an owner remark does not lift a pause, so nothing
is declared or launched here. The long-term "generalised open / learnable decision assistance"
question belongs to the Codex DM `/root/dm_typed_joint_skill` (direction
`typed_joint_skill_decision`, owner assignment 2026-10-01 PDT); this note reads its published
evidence for a concrete need and does not take over, duplicate or message it.

**一句话结论（中文）**：仓库已经用 6 个 fit 把"冻结 Laya 表示 + 评分头"和同数据数值评分器在耦合中继宿主上
完整比较过，两者在新世界都输给一条固定构造规则，而普通静态规则已拿走该菜单 98–99% 的机会；本笔记用零成本算术
进一步证明，在仓库现有的每一个"学习/预测辅助 vs 普通参照"面板上，哪怕一个完美的逐世界"该不该用辅助"门控，
相对普通参照的增益也不超过参照的约 1.5%（多数 ≤ .01）。因此 Jev 类方法里真正还没测、且赌注未知的只剩两件：
逐决策的信息价值预测（radio 宿主）和 S7 B10 新面板上的逐世界门控包络；前者属于 Codex 长期问题的范围，
后者先用零 fit 读数判断是否值得买。Laya 作为模型不是杠杆；它的方法论里可迁移的是输出契约、后果标签训练和
选择性升级，这三者对 HMASD 协调器的瓶颈（有限曝光下学不到规划器的几何部署能力）都不是对症的。

---

## 1. What "Jev-like" means, in the terms this project can use

- **Jev** (TypeSafe AI, closed API): a "System One" model that takes a block of state plus typed
  questions and returns schema-constrained, calibrated decisions in one pass, 70–500 ms, no text
  generation. Not reproducible locally; the owner proposal already excludes it as a dependency.
- **Open relatives** (all read via the owner proposal §13 at `docs/research/candidates/typed_joint_skill_decision/OWNER_PROPOSAL_20261001.md`
  and the Codex DM's pinned audit): **Laya** (ModernBERT-large, 421,293,830 parameters, Apache-2.0;
  `choice` / `score` / `noul` primitives; every option capped at 48 tokens; trained with
  proper-scoring-rule RL so reported probabilities are rewarded for honesty; fine-tunable with a
  differentiable soft cross-entropy on option labels), **this-that-model-1.0** (~2B, MIT),
  **LAVOIR** (adds an amortised value-of-information head: "which missing field is worth asking
  for"; weights CC BY-NC 4.0), **Chinese-Jev** (training pipeline; domain weights not public at
  reading time), `lookski/openjev` (constrained answer-token logits over an ordinary causal LM).
  Three critique papers in the same list: calibration is not as advertised (R6), the head follows
  the option *name* rather than its definition (R7), and the evidence base is early (R8).
- **What "fine-tune your own decision model to your area" means mechanically:** serialise a state
  and a small typed option set into text, encode once, score the options, train the scorer (or the
  encoder) on labels that say which option was better. That is exactly what the Codex DM did in
  B01 as arm L-F, next to a numeric encoder N trained on the same labels.

The methodology has three separable ingredients, and they should be judged separately:

| Ingredient | What it is | Does HMASD already have it? |
| --- | --- | --- |
| (i) Typed output contract | choose one option from a declared, masked set; probabilities per option | Yes: `hmasd/networks.py::assign_and_value_batch` encodes once, picks team skill Z, then each z_i conditioned on Z and the prefix (n_Z = n_z = 6, `configs/config_1.py`). |
| (ii) Consequence-labelled supervised training with a proper scoring rule | labels come from branch roll-outs of each option; soft-CE on the value-derived preference | Tested as a proxy several times (section 2). |
| (iii) Calibration, selective escalation, value of information | act on the model only when it is confident; otherwise defer to a planner; predict the value of asking for a missing report | Not tested as such; bounded at zero cost in section 3. |

## 2. What the repository already measured (read from published `main`)

| Study (owner, cost) | Learned or assisted arm vs. ordinary reference | Outcome on fresh worlds |
| --- | --- | --- |
| `typed_joint_skill_decision` B01 (Codex; 6 fits, 4,808,000 native steps, 2.017 CPU-h + 9.1 min GPU, 7.66 GiB peak) | N (numeric scorer) and L-F (frozen Laya encoder + two frozen head layers + adapted 1.05M-parameter scorer) choose 1 of 8 complete layouts; static coverage rule and fixed construction as references; coupled relay host, H500 | Complete C_bh: fixed .628/.625/.628, static .713/.700/.707, N final .615/.599/.606, L-F final .591/.617/.601, full planner .784/.769/.766. N reaches training regret ≈ .0006 but test regret ≈ .10; L-F fits training weakly; reversing option display order changes L-F's choice in 239/384 worlds. Online: N 29 ms, static 33 ms, L-F 318 ms per decision (Laya call 282 ms, cold load 3.8 s). Independent critic: stop both exact recipes, MATERIAL_DISSENT no. |
| `coupled_host_joint_skills_stage1` b02c (Claude; 1.33 CPU-h) | six-slot typed choice + fixed executor, PPO | sampled C̄_bh .4288 vs random-slot floor .4274; no de-duplication learned. |
| same host, ten single-seed fits (Claude; ≈ 42.4 CPU-h) | HMASD D-route (k = 10), flat SET, bounded heads, λ_l = 0 | all at learning floors (.21–.43); planner references .73–.81. |
| `coupled_host_planner_distillation` b01 (Claude; .95 CPU-h) | supervised student of the same-information planner, one DAgger round | S .4004 vs teacher T_M .7587 (0/32 worlds positive); train loss low, dev error 3.7× train, and the student's own trajectories leave the labelled distribution. |
| `uav_parent_adaptation` B05 (Codex; 4 fits) | CAL/CONT heads fitted to complete native action-consequence labels | CONT−S J −.005135 / −.005498, intervals cross zero. |
| `coupled_host_replan_timing` R1-lite (Claude; 0 fit) | four re-plan rules | hindsight envelope `mean(max(KEEP, cold, warm, seeded) − cold)` = +.0161 dev / +.0152 hold-out. |
| same family, b05 sighting (Claude; .19 CPU-h) | privileged full-map grant at call 100 | D_100 − L +.040; per-world envelope max(L, D_100) − L +.046; max(B0, L, D_100) − B0 +.049. |
| `uav_radio_uncertainty` B01 (Codex; 0 fit) | U32 (joint RF uncertainty package) vs P | payload-J +.00753 [+.00406, +.01100], 26/32 positive; mean age and maximum gap worse. |
| `uav_radio_information_cost` B02 (Codex; 0 fit, 3,269 CPU-s) | U32_FULL (paid central information) vs P_PRIOR | payload-J −.00975 [−.01524, −.00426], 6/32 positive. |
| `uav_fleet_transmission` B09 (Codex; 0 fit, 288,000 native steps) | S7 planner with lawful service prediction F, hold H, ordinary C | F − H total J +65.97 (17/32 positive) but F − C −454.28 (6/32 positive). |

The pattern is consistent across owners, hosts and interfaces: learners and learned assistants fit
their training exposure and then lose to a competent ordinary program on fresh worlds, at every
exposure the sizing rules allow (≈ 1–3 CPU-h, 64–256 training worlds). The shared background
(RESEARCH.md topic 4) already records this as "trainability, new-world decision quality and
complete-package usefulness are different things".

## 3. Zero-cost readings made for this note

All numbers below are arithmetic on committed per-world files; nothing was re-run. The quantity is
the **oracle deferral envelope**: the mean per-world gain over the ordinary reference if a perfect
gate used the assisted arm only in the worlds where it is better. It bounds what *any* calibrated
"use the model here or not" rule, the untested ingredient (iii), could ever win on that panel.

### 3.1 The eight-plan menu host (`runs/typed_joint_skill_decision/b01_read_a01/per-world.csv`, 384 test worlds)

| Reading (complete C_bh) | Mean | Worlds +/−/= |
| --- | ---: | --- |
| N final − static | −.0997 | 9 / 280 / 95 |
| L-F final − static | −.1035 | 9 / 287 / 88 |
| static − menu best (static's own regret) | −.00101 | 0 / 43 / 341 |
| **oracle deferral envelope, max(0, N − static)** | **+.00010** | 9 / 0 / 375 |
| **oracle deferral envelope, max(0, L-F − static)** | **+.00020** | 9 / 0 / 375 |
| agreement-gated rule (use N only where N and L-F agree, else static) − static | −.0194 | 1 / 70 / 313 |
| full planner − static | +.0666 | 325 / 59 / 0 |
| menu best − fixed construction | +.0807 | 271 / 0 / 113 |

Two consequences. First, on the host where Laya was tested there was nothing left for a calibrated
or selective learner to win: a perfect gate adds two ten-thousandths of coverage, and the only
deployable confidence proxy available in the saved data (two independently trained learners
agreeing) does not predict correctness (agree: mean regret .083, exact-best 18/91; disagree: .106
and .111, exact-best 73/293 and 67/293). Second, the opportunity on that host sits outside the
menu: the full planner beats the static rule by +.067 in 325/384 worlds. The Codex DM's B02
(experience-assisted choice of which search branch to descend) is therefore pointed at the right
interface; the B01 negative is a "wrong host for the question" result more than a "wrong model" one.

### 3.2 Radio information hosts (`runs/uav_radio_uncertainty/b01_correlated_shadow_a01/result.json`, `runs/uav_radio_information_cost/b02_integrated_package_a01/result.json`, 32 paired worlds each)

| Panel (payload-J) | Assisted − ordinary | Oracle per-world gate envelope over ordinary |
| --- | ---: | ---: |
| U32 vs P | +.00753 (26/6) | +.00889 (26/32 worlds), i.e. a gate adds +.00136 over always-U32 |
| U32_FULL vs P_PRIOR | −.00975 (6/26) | +.00214 (6/32 worlds); a gate would turn the FULL purchase from a loss into +.002 over PRIOR at best |

### 3.3 S7 prediction planner (`runs/uav_fleet_transmission/b09_service_prediction_a01/perworld.json`, 32 worlds)

| Panel (total J; C mean 2156.3) | F − C | H − C | Oracle gate max(C, F) − C | max(C, H, F) − C |
| --- | ---: | ---: | ---: | ---: |
| B09 | −454.28 (6/26; max +358.19) | −520.25 (3/29) | **+32.48 (6/32 worlds), ≈ 1.5% of C** | +34.01 |
| cumulative QoS | −450.84 | −511.61 | +31.16 | +32.73 |

### 3.4 What the envelopes say together

| Host | Oracle gate envelope over the ordinary reference | Relative to the reference |
| --- | ---: | ---: |
| eight-plan menu (B01) | +.0001 / +.0002 C_bh | ≈ 0.03% |
| radio U32 / P | +.0089 payload-J (of which +.0014 is the gate) | small; most of it is "always U32" |
| radio FULL / PRIOR | +.0021 | < 1% |
| S7 F / C | +32.5 J | ≈ 1.5%, concentrated in 6 of 32 worlds |
| coupled-host sighting (already read by the Claude DM) | +.046 / +.049 C_bh | ≈ 6%, needs a privileged grant |
| re-plan timing (already read) | +.016 / +.015 C_bh | ≈ 2% |

On every panel in the repository, a perfect per-world "use the assistant or not" decision is worth
at most about 1–2% of the ordinary reference (6% only with privileged information). Calibrated
selective escalation, the one piece of the Jev methodology this project has not tried, therefore
has a small bounded stake on existing hosts; it is not where the missing value is. The large gaps
are elsewhere: planner over static on the menu (+.067), planners over every learner on the
coupled host (.73–.81 vs .21–.43), and the planner's own search cost (full `compute_menu` 822 ms
vs 33 ms for the static rule; B02's G already removes about 32% of search calls with no learning).

## 4. Mapping the three ingredients onto the HMASD algorithm

| Interface in HMASD | Ingredient | Evidence status | Assessment |
| --- | --- | --- | --- |
| Coordinator head (Z, z_i) replaced or initialised by a typed scorer | (i)+(ii) | Tested by proxy: B01 N/L-F, b02c slots, distillation b01 | The readout is not the bottleneck. A Laya-shaped head would add a text serialisation of numeric geometry, an option cap of 48 tokens, order sensitivity (239/384 flips) and ≈ 10× online cost, for no demonstrated representation gain over a numeric encoder at equal data. Not recommended. |
| Consequence-labelled pre-training of the coordinator from planner branches | (ii) | Tested: distillation .40 vs .76 at .95 CPU-h; parent B05 CAL/CONT; B01 N train-regret .0006 vs test .10 | Finite-exposure generalisation and compounding, not the training signal, are the identified rungs. More of the same exposure is what the project's record says not to buy; the structural question is the sibling A/R study (`uav_decision_generalization`, 6 fits, 384 new worlds), which is the right experiment for it. |
| Selective escalation: coordinator defers to the planner when uncertain | (iii) | Untested; bounded here | Oracle envelopes ≤ ~1.5% on all existing panels; a real gate would recover less and must predict the few gaining worlds in advance. Read first on any new panel (B10's C/H_A/F_A per-world outcomes when they land); declare a fit only if that envelope clears a pre-written band. |
| Value-of-information head: which lawful report to request before a decision | (iii) LAVOIR-style | Untested at the per-decision level; the per-world package envelopes are small (3.2) | This is the one ingredient whose per-decision stake is genuinely unmeasured and whose host exists (radio directions, with real sensing and communication costs, both signs observed). It sits inside the Codex long-term scope and inside Codex-owned radio directions; a Claude study would need a distinct estimand agreed by the owner. |
| Experience-guided search allocation (algorithm selection) | (ii) at a search boundary | B02 contract frozen, implementation accepted, admission pending the shared launcher repair | The best current use of "task-learned decision assistance"; one fit, 102,000 native steps, 64 fresh worlds, G/L/P with the paid incumbent protected. Nothing for the Claude side to add before it reads. |
| Skill termination / re-decision timing as a typed `continue / switch` decision | (i)+(iii) | FSD is owner-paused; re-plan envelopes +.015–.016; Δ_L = 0 for periodic re-plans | Low stake on the static coupled host; the dynamic host question remains open but is not licensed by any present result. |

Net for "enhance my hierarchical RL algorithm": the transferable parts of the Jev methodology are
the output contract (already present), the discipline of consequence labels with a separate
calibration split (already practised in the project's reading rules), and the idea that a learned
component should know when to hand over to an ordinary planner. None of them addresses the
bottleneck the evidence identifies, which is that at affordable exposure the learner does not
acquire the planner's geometric deployment competence on fresh worlds. A pretrained text decision
model does not supply that competence either; B01 is the direct test, and it was negative at the
cheapest coupling while the sibling study now tests the structural alternative.

## 5. What this changes, and what it does not

- Changed belief: "fine-tuning an open Jev-like model on this domain" is not an open question any
  more at the frozen-encoder level; what remains open is full fine-tuning, whose expected value is
  low given the modality mismatch and the sibling study, and whose honest form is a pretraining
  attribution (same-shape random initialisation vs. pretrained) that answers a method question of
  little consequence for UAV service.
- Changed belief: calibrated selective escalation cannot be where the value is on any existing
  panel; its oracle stake is ≤ ~1.5% of the ordinary reference.
- Unchanged: ordinary planners and static rules remain the competent references; the Codex B02
  search-assistance comparison is the right next purchase for "task-learned decision assistance";
  per-decision value of information is the one unmeasured stake with a concrete host.
- Cost of this note: 0 fits; arithmetic only. Uninformative outcomes: none.

## 6. [DECIDE] items for the owner, each with a default that executes

1. **Claude action on this theme now.** Default: none. The session stays paused; this note is the
   deliverable. No direction is declared, no run is launched, no peer message is sent (the
   `codex queue` channel runs only from the WSL checkout, not from this cloud container).
2. **Forwarding.** Default: the owner decides whether to point the Codex DM at this note (peer
   method: an `EVIDENCE` message carries a commit, path and anchor; the note is on branch
   `claude/inspiring-ritchie-2kj46g`, not on `main`, until the owner merges or asks for a `main`
   commit from the WSL session).
3. **If the owner later resumes the Claude session and wants it on this theme**, the candidate with
   a distinct estimand from the Codex DM's is *the gate value of an existing predictor*: read the
   per-world oracle envelope on S7 B10's fresh panel at zero fits; pre-write the band (for
   instance, declare a gate study only if max(C, H_A, F_A) − C ≥ 3% of C's mean J with at least
   8 of 32 gaining worlds); otherwise record the reading and stop. Default if not chosen: the
   Claude queue stays as published (`uav_restoration_readiness` waits on the Milan data).
4. **Laya full fine-tuning on serialised geometry.** Default: not bought. If the owner wants it
   regardless, price it as a pretraining-attribution comparison (L-T vs same-shape random
   initialisation vs the numeric N at matched labels) at no less than B01's bill (2.0 CPU-h,
   GPU reservation, ≈ 8 GiB peak) plus the sibling A/R result read first.

## 7. Sources

Repository (branch base `a1d58a5d`): `docs/research/RESEARCH.md` (`#resume-20261001`,
`#three-dm-decision-assistance-20261001`, `#typed-joint-skill-selection-20261001`, topics 3–4,
routing rows); `docs/research/candidates/typed_joint_skill_decision/{NOTES.md,OWNER_PROPOSAL_20261001.md}`
(B00 audit, `#b01-complete-reading`, `#b01-independent-result-review`, `#b02-search-branch-contract`,
B02 acceptance); `docs/research/candidates/uav_decision_generalization/NOTES.md`;
`docs/research/candidates/coupled_host_joint_skills_stage1/NOTES.md` (b02c, b03, b04, b05 reads,
CORRECTION, Pro `learner-locus-round-boundary`); `docs/research/candidates/coupled_host_planner_distillation/NOTES.md`
(b01 READ); `docs/research/HANDOFF_20261001_ROOT_AND_FOUR_DMS.md`; per-world files named in section 3;
`hmasd/networks.py` lines 795–855; `configs/config_1.py` lines 132–133.

External (read 2026-10-02; descriptions only, no weights downloaded):
[DigitalOcean, "What is Jev"](https://www.digitalocean.com/resources/articles/what-is-jev);
[DataCamp, "System One models: Jev"](https://www.datacamp.com/blog/system-one-models-jev);
[OpenRouter, typesafe/jev-1.13](https://openrouter.ai/typesafe/jev-1.13);
[Hugging Face, convaiinnovations/laya](https://huggingface.co/convaiinnovations/laya);
[Laya release note](https://aiweekly.co/alerts/laya-open-sources-a-33ms-multilingual-typed-decision-engine);
[eesel, "Laya AI"](https://www.eesel.ai/blog/laya-ai);
[Orca Router, "Laya decision model explained"](https://www.orcarouter.ai/blog/laya-decision-model-explained);
and the owner proposal's R1–R12 entries (Laya, this-that-model arXiv:2609.23886, LAVOIR arXiv:2609.30706,
Chinese-Jev arXiv:2609.36965, openjev, arXiv:2609.33843, arXiv:2609.26758, arXiv:2609.32160, MAT, PARCO, DAgger, Guo et al. 2017).
