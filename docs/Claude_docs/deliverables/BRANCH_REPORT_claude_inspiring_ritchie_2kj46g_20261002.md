# Branch report: `claude/inspiring-ritchie-2kj46g` (2026-10-02)

Provenance: Claude Code cloud session `session_013LQX44wuT3dfQfhb79KwZB`, 2026-10-02 UTC. Branch cut
from `main` at `a1d58a5d`; four commits (`bc116366`, `433d724e`, `ec7b8b16`, and the commit carrying
this report and the Codex prompt), all under `docs/Claude_docs/`. `origin/main` moved to `ab2c2326`
(42 commits, all dated 2026-10-01) while the branch was being written; a test merge of the branch onto
that `main` (`git merge-tree`) has no conflicts. Non-direction deliverables (CLAUDE.md): evidence and
design advice for the owner, not a science card, a contract, a declaration or a decision record.

Status boundaries respected throughout: the Claude session is paused by the owner (quota, 2026-09-30,
RESEARCH.md routing row); no project host, node, direction, fit or launcher was touched; no peer
message was sent (the `codex queue` channel runs only from the WSL checkout, not from this cloud
container); the only computation was deterministic arithmetic on committed per-world files and a
standard-library toy environment run inside the container.

**一句话（中文）**：本分支交付三件非方向性产物：(1) 开源 Jev 类决策模型用于 HMASD 的评估笔记（Root 已按 owner
要求逐字导入 main `8bc5f9c9`，并记录了有范围的异议；其中建议 1+5 已变成 Codex 的 B04 学习曲线合同，建议 3
"稀疏窗口"被保留为未定价候选）；(2) 把建议 3 定价成可执行比较的场景设计 S2-W（四个学习臂、四个零 fit 参照、
预声明判读带、首轮 ≈ 7.6 CPU-h）；(3) 一个 stdlib 玩具环境及读数：针尖难度下所有臂停在随机地板；放宽一档后
所有臂都能学，判别器权重 ×4 的层次臂最早激活且 5/5 种子，计数探索晚约 750 回合到同一水平，默认权重的层次臂
不优于 flat，无判别器的层次臂最差。两条教训已写回设计。未触碰任何宿主、节点、方向或 fit；Claude 暂停不变。

---

## 1. What was asked and what was delivered

| Owner request (chat, 2026-10-02) | Deliverable | Commit |
| --- | --- | --- |
| "The decision model Jev gives me some inspiration … Jev-like open-source models let you fine-tune a decision model for a specific area … I started a DM on Codex to find how to use this kind of model or methodology to enhance my hierarchical RL algorithm" | `research_notes/OPEN_DECISION_MODELS_FOR_HMASD_20261002.md`: what the repository already measured, three separable ingredients of the methodology, zero-cost "oracle deferral envelopes" on every existing assisted-versus-ordinary panel, a mapping onto HMASD's interfaces, four [DECIDE] items with defaults | `bc116366` |
| "btw do you know tibo the reset guy? don't search" | Answered in chat from memory, no search, nothing in the repository | — |
| "Any further idea about my research project" | Six ranked ideas in chat. The owner forwarded them to the Codex Root, which archived the text verbatim on `main` (`docs/research/archive/2026-10-01/RESEARCH-learning-curve-and-cost-aware-successors.md`) | — |
| "Can you re-design a suitable scenario for this sparse reward UAV-BS communication and a related toy-env to check my idea at lower cost" | `environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md` (scenario S2-W) and `toy_studies/sparse_window_relay/` (`swr_toy.py`, `README.md`, `RESULTS.md`, two results files) | `433d724e`, `ec7b8b16` |
| "write a report on that branch. And give a prompt for codex to utilize your work" | This report and `deliverables/CODEX_PROMPT_SPARSE_WINDOW_RELAY_20261002.md` | this commit |

## 2. Deliverable 1: the decision-model note, and how `main` has already used it

**What it says.** The repository already contains the direct test of "fine-tune an open Jev-like model on
this domain": `typed_joint_skill_decision` B01 compared a frozen Laya encoder with an adapted scorer (L-F)
against a numeric scorer (N) trained on the same consequence labels, six fits, and both lost to a fixed
construction rule on fresh worlds (complete C_bh: L-F −.1035 and N −.0997 against the static rule on 384
test worlds; L-F's choice flips in 239/384 worlds when the option order is reversed; online cost 318 ms
against 33 ms). The methodology has three separable ingredients: a typed output contract (HMASD's
coordinator already has it), consequence-labelled supervised training (tested by proxy four times, all
below the ordinary planner), and calibrated selective escalation / value of information (untested). The
note bounds the untested ingredient at zero cost with the per-world oracle deferral envelope, the mean
of max(0, assisted − ordinary): +.0001 and +.0002 C_bh on the B01 menu, +.0089 and +.0021 payload-J on the
two radio panels, +32.5 J (≈ 1.5% of the reference) on S7 B09. The conclusion: on every existing panel a
perfect "use the assistant here or not" gate is worth about 1–2% of the ordinary reference, so selective
escalation is not where the missing value is; the large gaps are planner-over-static (+.067) and
planners-over-learners (.73–.81 against .21–.43) on the coupled host, and the planner's own search cost.
Four [DECIDE] items with executing defaults: no Claude action while paused; forwarding is the owner's
choice; if the session resumes, the candidate with a distinct estimand is the gate value on S7 B10's
fresh panel, with a pre-written band (declare a gate study only if max(C, H_A, F_A) − C ≥ 3% of C's mean J
with at least 8 of 32 gaining worlds); Laya full fine-tuning not bought.

**What `main` did with it (read from `origin/main` at `ab2c2326`).**

- The owner asked Root to import the note; Root copied it byte-for-byte from `bc116366` to `main` in
  `8bc5f9c9` (20,141 bytes, SHA256 `e1da1d8d…`), preserving its status and conclusions without rewriting
  them. The branch copy and the `main` copy are identical.
- Root read the note, the six chat ideas, two result critics and a temporary Oracle answer, and recorded
  its cross-question disposition (RESEARCH.md anchor `three-dm-decision-assistance-20261001`; archive
  above). Ideas 1 and 5 (an exposure curve on a wider raw layout) became the `typed_joint_skill_decision`
  B04 contract: a nested 1k/4k/16k world bank, two initialisations × three sizes = six fits, independently
  selected (`30e8b917`, MATERIAL_DISSENT: no), under implementation with no producer yet.
- Root recorded a **scoped disagreement** with the note, without rewriting it: the per-world envelope over
  fixed complete policies "applies only to those policies, worlds and metrics, not online switching or the
  family of assistants". The Oracle's answer carries MATERIAL_DISSENT: yes against using the note's
  envelope as a repository-wide gating bound, its train–test gap as a unique bottleneck diagnosis, or an
  uncorrected price as investment grounds. The note's arithmetic is kept as "limited gating arithmetic
  worth retaining". The report accepts the scope correction as stated: the envelopes bound the fixed
  policies on the panels they were computed on, nothing more.
- Idea 3 (give HMASD's own mechanism a sparse-reward task) was **kept as a substantive prospective
  candidate and not bought**, with the reasons written down: "neither is an already priced executable
  comparison"; the existing registered-service metric F is per-user, per-window contact, not a single
  joint event; a lawful ordinary planner must get the same information and channel; a matched HMASD
  versus flat comparison must pay both sides; at least two matched new learning instances are needed; the
  training, optimiser and run price were not closed, "so this round does not buy it and does not require
  a string of zero-fit gates first".

Deliverables 2 and 3 are the answer to that last item: they turn idea 3 into a priced, executable
comparison and check its premise in an abstraction before any CPU-hour is spent.

## 3. Deliverable 2: scenario S2-W, a sparse-window relay service task on the coupled host

**Question.** On a UAV-BS service task whose reward is paid only when a joint relay configuration to a
far cluster is formed and held inside a service window, does HMASD's skill discovery reach the sparse
reward more reliably than flat PPO at the same interface and exposure, and more reliably than the same
hierarchy with its discriminator rewards disabled? The schedule-aware ordinary planner is the ceiling
reference, not a bar. Three competing explanations are controlled by arms: any exploration bonus would do
it (count-based arm); hierarchy and commitment alone do it (no-discriminator arm); the reward is reachable
by chance at this exposure (random and sticky floors).

**What changes against the existing coupled host, and what does not.** `CoupledRelayHost` keeps every
contract constant (6 UAVs, 50 users, 5 km, centre base station, max 3 hops, k = 10, H500, 30 m/s). Changed
and declared: the user layout (one near cluster of 10 at the base station, four far clusters of 10 near
the corners, with a world admission rule that no far cluster is servable by one UAV with a direct
base-station link); all 40 far users registered with the 400-byte map convention; a known schedule of
four 125-tick windows, one far cluster open per window, order drawn from the world seed; the served
condition (at least 8 of the open cluster's 10 registered users backhaul-connected); the reward (+1 per
window at the first tick the served condition has held for 20 consecutive ticks; at most 4 per episode;
plus w_dense × the existing contract reward with w_dense ∈ {0, .01} as the decoy variant); schedule
features appended identically to every arm's observation and state.

**Arms, references, worlds, exposure, price.**

| Item | Specification |
| --- | --- |
| Learned arms | (1) HMASD defaults (λ_D = .05, λ_d = .02); (1b) HMASD with four-fold discriminator weights (λ_D = .2, λ_d = .08); (2) HMASD with `disable_discriminator_rewards = True`; (3) flat SET at the same interface and exposure (the b02/b03 recipe); (4) optional flat + count bonus, only if it needs no shared-code change |
| Zero-fit references | random slot program; sticky-random; near-camping planner (the decoy's attractor); O_W, the frozen planner given the schedule, re-planning per decision for the current or next open cluster |
| Worlds | 64 dev worlds for floors and training; 32 fresh hold-out worlds for the reading; common across arms |
| Exposure | one instance per arm at 360k native steps, the b03 exposure that cost 1.79 CPU-h on `local_linux` |
| Price | four arms ≈ 7.2 CPU-h + floors ≈ .1 CPU-h + hold-out evaluation ≈ .3 CPU-h; seeds only after an activation |
| Primary reading | windows satisfied per episode on the hold-out worlds (0–4), paired across arms, per-world signs and descriptive intervals |
| Activation band | arm mean ≥ sticky-random + 1.0 window and ≥ .5 absolute |
| Mechanism band | HMASD − HMASD-without-discriminators ≥ .5 window and ≥ 3 SE, with HMASD above flat SET; if flat + count bonus matches HMASD, the effect is reported as generic exploration |
| Zero-fit room condition | O_W − sticky ≥ 2.0 windows and O_W ≥ 3.5; near-camping ≈ 0 windows with high contract reward |
| Sparsity calibration (from the toy) | the random slot program must satisfy 5–20% of windows; below 1% loosen the served condition (6 of 10) or lengthen the hold before any fit; above 30% the objective is not sparse |

**Order of work.** Zero-fit stage first (host subclass, schedule features, four references on the dev
worlds, room and sparsity conditions; ≈ .1 CPU-h and 4–6 engineering hours); independent scientific
review under constitution section 5 (new host objective and new metric); then one fit per arm in the
pure-sparse variant, read by the pre-declared rule; the decoy variant and seeds only after an activation.
Three floor-level instances close the objective at this exposure on this host; no seed, epoch or knob is
added to a floor-level instance.

**How S2-W meets the conditions Root and the Oracle recorded on `main`.**

| Recorded condition | S2-W |
| --- | --- |
| "Not an already priced executable comparison" | Priced: ≈ 7.6 CPU-h for the first round, with the exposure taken from a measured cell (b03) |
| "A matched HMASD-versus-flat comparison pays both sides"; "at least two matched new learning instances" | Four learned instances at the same interface, exposure and worlds |
| "A lawful ordinary planner gets the same information and channel" | Registered map and schedule features are identical for every arm and for O_W; no contact acknowledgement enters any actor |
| "The sparse-window metric is per-user, per-window completion rather than a single all-user event" | **Deliberate design choice, flagged for review:** S2-W pays on a cluster-level joint event (≥ 8 of 10 registered users backhauled for 20 consecutive ticks), because the question is about forming and holding a joint relay chain; the per-user window-hit count F stays available as a secondary reading on the same trajectories |
| "Does not require a string of zero-fit gates first" | One zero-fit stage (≈ .1 CPU-h) whose purpose is to refute the comparison cheaply (room and sparsity conditions), not a gate ladder |
| Oracle: "it can study exploration capability under sparse reward" | That is the stated question; the planner is a ceiling, not a bar |

## 4. Deliverable 3: the toy, and what it found

**Instrument.** `toy_studies/sparse_window_relay/swr_toy.py`, standard-library Python, every draw seeded,
about 5 ms per episode. An 11 × 11 grid with the base station at the centre, four corner sites served only
through a relay chain (link range 2, access range 1 or 2, at most 3 hops), six UAVs, decisions every 10
ticks, 120-tick episodes, five 20-tick windows (sites 0, 1, 2, 3, 0), +1 per window after 5 consecutive
served ticks (maximum 5 per episode), optional decoy of +.002 per UAV-tick next to the base station
(maximum 1.44 per episode). Arms: tabular REINFORCE analogs of flat PPO (`flat`), flat + count bonus
(`flat_count`), hierarchy without discriminators (`hier_nodisc`), hierarchy with tabular discriminator
rewards at the project's weights (`hier_disc`, λ_D = .05, λ_d = .02) and at four-fold weights
(`hier_disc_x4`). Zero-learning references: random, sticky-random, stay, region-random, and an
ordinary scheduler that knows the schedule and chain cells (`ordinary_window`, the ceiling). Five seeds,
5,000 episodes per instance, two difficulty rungs (access range 1 = the needle, one two-UAV chain per
corner; access range 2 = wider), decoy 0 and .002. Wall time 739 s and 737 s for the two rungs.

**References.** Needle rung: random targets .020 windows per episode (1.9% of episodes with any window),
sticky-random .005, stay .000, ordinary_window 5.000. Wider rung: random .131 (12.5%), sticky .033,
ordinary_window 5.000. With the decoy, `stay` earns 1.44 and sticky-random .84 with zero windows: the
decoy is real.

**Learners, pure sparse reward, final 500 training episodes (mean ± SE over five seeds).**

| rung | flat | flat_count | hier_nodisc | hier_disc | hier_disc_x4 |
| --- | ---: | ---: | ---: | ---: | ---: |
| needle | .016 ± .002 (0/5) | .017 ± .000 (0/5) | .020 ± .004 (0/5) | .022 ± .004 (0/5) | .033 ± .006 (0/5) |
| wider | 1.781 ± .167 (5/5) | 1.995 ± .082 (5/5) | 1.225 ± .307 (3/5) | 1.577 ± .238 (4/5) | **2.048 ± .029 (5/5)** |
| wider: first 250-episode bin with seed-mean ≥ 1.0 | 18 | 17 | 19 | 18 | **14** |

Contrasts at the wider rung (difference of seed means, SE from the two seed sets): hier_disc_x4 −
hier_nodisc +.82 (SE .31); hier_disc_x4 − flat +.27 (.17); hier_disc_x4 − flat_count +.05 (.09); hier_disc −
flat −.20 (.29); hier_disc − hier_nodisc +.35 (.39).

**Decoy variant, wider rung.** flat 1.783 ± .154 (5/5), flat_count 1.498 ± .261 (4/5), hier_nodisc 1.493 ±
.200 (4/5), hier_disc 1.249 ± .333 (2/5), hier_disc_x4 2.068 ± .136 (5/5). At the needle rung the hierarchy
arms learn the decoy (camp at the base station) while flat does not learn even that. Seed variance is
large; this is a direction, not an established effect.

**Per-site diagnostic** (recording-only field added after the main run; re-running single instances
reproduced the main run exactly): every activated instance earns almost all of its windows at site 0,
the site whose chain pays twice per episode (flat seed 2: 1.88 / .09 / .07 / .04 by site; hier_disc_x4
seed 1: 1.97 / .17 / .01 / .01). The plateau near two windows is the first mission learned; the other three
chains stay at the random rate.

**Reading.** At the needle rung the toy is uninformative about arm differences: a 2% random hit rate is
unlearnable by every analog at 5,000 episodes. At the wider rung the discriminator reward is an
exploration device, but only at a weight that is large relative to the sparse reward: at the project's
default weights the hierarchy is no better than flat, without discriminators it is the worst and least
reliable arm, and the count bonus reaches the same final level as the best discriminator arm about 750
episodes later. The mechanism's claim at this rung is earlier activation and lower seed variance, not a
unique capability.

**Limits.** No radio physics, continuous control, PPO, advantage estimation, Transformer coordinator or
learned low-level skills; intrinsic rewards computed once per decision on the end-of-segment
configuration; exact tabular discriminators; fixed schedule; five seeds give descriptive intervals. The
toy says which design choices make the real comparison informative; it does not predict the host's
outcome.

## 5. What changed and what did not (round-boundary statement)

- **Changed belief:** "fine-tune an open Jev-like model on this domain" is no longer an open question at
  the frozen-encoder level (B01 is the direct test); the untested ingredient, calibrated selective
  escalation, has a bounded stake of about 1–2% of the ordinary reference on every existing panel, with
  the scope correction recorded by Root: those bounds hold for the fixed policies and panels they were
  computed on.
- **Changed design:** the sparse-reward comparison now exists as a priced specification with arms,
  references, bands and worlds; idea 3 has moved from "prospective, unpriced" to "executable, awaiting
  Root's investment decision and a section-5 review".
- **Changed design, from the toy:** a real-host comparison must carry a stronger-weight HMASD arm (1b),
  and sparsity must be calibrated at the zero-fit stage (random slot program satisfying 5–20% of windows)
  before any fit is bought.
- **Unchanged:** ordinary planners and static rules remain the competent references; the count-based
  bonus remains a required control, because in the abstraction it reaches the best discriminator arm's
  level; the Claude session's queue and pause are unchanged; Codex's current investments (B04 learning
  curve, S/C frozen cooperation, B11 travel ties) are not affected.
- **Uninformative outcomes and their cost:** the needle rung of the toy (all arms at the floor, about 12
  minutes of CPython); the decoy comparisons (too variable at five seeds to rank arms). Total cost of the
  branch: 0 fits, 0 native steps, 0 node resources, about 25 minutes of CPython in this container.

## 6. Open items, each with a default that executes

1. **Merging the branch.** Default: the owner merges `claude/inspiring-ritchie-2kj46g` into `main` from the
   WSL checkout, or asks Root to import the files as it did for the note. The test merge is clean; the only
   overlapping file (the note) is identical on both sides.
2. **Handing the scenario to Codex.** Default: paste the prompt in
   `CODEX_PROMPT_SPARSE_WINDOW_RELAY_20261002.md` to the current Root thread; Root decides whether the
   now-priced comparison is bought, and assigns a DM if so. The prompt asks for a decision and a reason,
   not for a purchase.
3. **Claude session.** Default: stays paused; no direction is declared from this branch. If the owner
   resumes the session and assigns S2-W to it instead of Codex, the design doc is the pre-declaration
   source and the first act is the zero-fit stage.
4. **Zero-cost readings now computable on `main`.** The S7 B10 panel has landed
   (`runs/uav_fleet_transmission/b10_service_assignment_a01/perworld.json`), so the note's [DECIDE] 3
   envelope and its pre-written band can be read at zero fits by whoever owns the question; the toy's
   learning curve at 10k and 20k episodes (whether the three undiscovered chains are ever found) costs
   minutes of CPython. Neither was run here.

## 7. Files on the branch

| Path | Lines / bytes | Commit |
| --- | --- | --- |
| `docs/Claude_docs/research_notes/OPEN_DECISION_MODELS_FOR_HMASD_20261002.md` | 212 / 20,141 (identical copy on `main` at `8bc5f9c9`) | `bc116366` |
| `docs/Claude_docs/environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md` | 163 / 15,939 | `433d724e`, `ec7b8b16` (lessons folded in), this commit (price row corrected to four arms) |
| `docs/Claude_docs/toy_studies/sparse_window_relay/swr_toy.py` | 452 / 17,808 | `433d724e`, `ec7b8b16` (per-site field) |
| `docs/Claude_docs/toy_studies/sparse_window_relay/README.md` | 24 | `433d724e` |
| `docs/Claude_docs/toy_studies/sparse_window_relay/RESULTS.md` | 143 / 9,602 | `ec7b8b16` |
| `docs/Claude_docs/toy_studies/sparse_window_relay/results_raccess1.json`, `results_raccess2.json` | 2,025 lines each | `ec7b8b16` |
| `docs/Claude_docs/deliverables/BRANCH_REPORT_claude_inspiring_ritchie_2kj46g_20261002.md` (this file) | — | this commit |
| `docs/Claude_docs/deliverables/CODEX_PROMPT_SPARSE_WINDOW_RELAY_20261002.md` | — | this commit |
| `docs/Claude_docs/README.md` | index entries for the above | this commit |

Reproduce the toy from the checkout root:

```
python3 docs/Claude_docs/toy_studies/sparse_window_relay/swr_toy.py --r-access 1 --out results_raccess1.json
python3 docs/Claude_docs/toy_studies/sparse_window_relay/swr_toy.py --r-access 2 --out results_raccess2.json
```
