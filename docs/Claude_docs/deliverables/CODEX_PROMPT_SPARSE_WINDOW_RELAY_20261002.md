# Prompt for Codex: use the sparse-window relay design and toy from the Claude branch (2026-10-02)

Written by the Claude Code cloud session `session_013LQX44wuT3dfQfhb79KwZB` at the owner's request
("give a prompt for codex to utilize your work"). Non-direction deliverable under `docs/Claude_docs/`.
The prompt grants nothing: it is an owner-forwarded input that Root evaluates under the constitution.

**给 owner 的使用说明（中文）**：把下面 BEGIN/END 标记之间的正文原样贴给当前 Root 线程（RESEARCH.md
`#session-routing` 表中的「完成Root交接并继续任务」，此刻 `01a0f779-ace2-74e1-85ad-e0997b61d505`），或贴给你
新建的独立 Codex DM（按 AGENTS.md 显式传 `model: "gpt-6-astra"`、`thinking: "max"`，并核对首轮实际模型）。
分支文件尚未合并到 main：要么先在 WSL 检出合并 `claude/inspiring-ritchie-2kj46g`，要么让 Codex 按正文第 2
条直接从远端分支读取。正文请求的是一个有理由的投资决定（买或不买，以及为什么），不是一次购买；买与不买都
不改变 Claude 会话的暂停。

---

<!-- BEGIN PROMPT -->

[HMASD owner request] Evaluate, and if worth it execute, the sparse-window relay comparison that the Claude peer designed and checked in a toy

You are acting under `docs/project/OPERATING_CONSTITUTION.md` (sections 2, 3, 5 and 8 apply here). This
message forwards a Claude-side deliverable. It is evidence and a design, not an instruction to buy fits:
the cross-question investment decision stays with Root, the contract with the DM you assign, and
nothing here resumes the Claude session or changes its pause, FSD/PPC, G33 or Milan scope.

**1. Where this comes from.** On 2026-10-02 you kept "sparse-window learning" (the Claude peer's
suggestion 3) as a substantive prospective candidate and did not buy it, with the reasons recorded in
RESEARCH.md `#three-dm-decision-assistance-20261001` and in
`docs/research/archive/2026-10-01/RESEARCH-learning-curve-and-cost-aware-successors.md`: not a priced
executable comparison; the existing registered-service metric F is per-user, per-window contact rather
than a single joint event; a lawful ordinary planner must get the same information and channel; a matched
HMASD-versus-flat comparison must pay both sides with at least two matched new learning instances; the
training, optimiser and run price were not closed. The peer has since written a priced specification
and checked its premise in a toy. Read those two things and decide.

**2. Read, in this order** (paths are on branch `claude/inspiring-ritchie-2kj46g`, commits `433d724e`,
`ec7b8b16` and the branch report commit; on `main` if the owner has merged. To read without merging:
`git fetch origin claude/inspiring-ritchie-2kj46g` then
`git show origin/claude/inspiring-ritchie-2kj46g:<path>`):

- `docs/Claude_docs/deliverables/BRANCH_REPORT_claude_inspiring_ritchie_2kj46g_20261002.md` — the
  summary, including section 3's table of how the design answers each condition you recorded.
- `docs/Claude_docs/environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md` — scenario
  S2-W: question, what changes on the coupled relay host and what does not, arms, references, worlds,
  exposure, pre-declared reading rule, order of work, price.
- `docs/Claude_docs/toy_studies/sparse_window_relay/RESULTS.md` — the toy's readings (`swr_toy.py`,
  `README.md`, `results_raccess1.json`, `results_raccess2.json` sit next to it).
- Assets the design reuses, read-only: `experiments/candidates/coupled_host_joint_skills_stage1/`
  (`host.py` for `CoupledRelayHost` and `HOST_CONTRACT_KWARGS`, `planner.py::search_placement`,
  `menus.py`, `runner.py`; Claude-owned, direction state reserve),
  `experiments/candidates/uav_registered_service/b01/{history.py,metrics.py,scheduler.py}` (registered
  windows, F metric, 400-byte map), `hmasd/agent.py` (intrinsic reward batch), `hmasd/networks.py`
  (`assign_and_value_batch`), `configs/config_1.py` (`lambda_D`, `lambda_d`,
  `disable_discriminator_rewards`), and the b03 cell record in
  `docs/research/candidates/coupled_host_joint_skills_stage1/NOTES.md` (360k native steps = 1.79 CPU-h
  on `local_linux`, the exposure the design prices from).

**3. The comparison in one paragraph.** `CoupledRelayHost` with every contract constant unchanged (6
UAVs, 50 users, 5 km, centre base station, max 3 hops, k = 10, H500). Changed and declared: one near
cluster of 10 users at the base station and four far clusters of 10 near the corners, with a world
admission rule that no far cluster is servable by one UAV with a direct base-station link; all 40 far
users registered; a known schedule of four 125-tick windows, one far cluster open per window; a window
pays +1 at the first tick at which at least 8 of the open cluster's 10 registered users have been
backhaul-connected for 20 consecutive ticks (at most 4 per episode); optional decoy w_dense = .01 on the
existing contract reward; schedule features (open cluster, ticks remaining, next cluster) appended
identically to every arm's observation and state. Learned arms at the same interface, worlds and
exposure (one instance each, 360k native steps): (1) HMASD defaults (λ_D = .05, λ_d = .02); (1b) HMASD
with λ_D = .2, λ_d = .08; (2) HMASD with `disable_discriminator_rewards = True`; (3) flat SET (the b02/b03
recipe); (4) optional flat + count bonus, only if it needs no shared-code change. Zero-fit references:
random slot program, sticky-random, near-camping planner, and O_W (the frozen planner given the schedule,
re-planning per decision for the current or next open cluster). 64 dev worlds, 32 fresh hold-out worlds.
Primary reading: windows satisfied per episode on the hold-out worlds, paired across arms. Bands written
before any fit: activation = arm ≥ sticky-random + 1.0 window and ≥ .5 absolute; mechanism = HMASD −
HMASD-without-discriminators ≥ .5 window and ≥ 3 SE with HMASD above flat SET; a count-bonus match is
reported as generic exploration. Price: four arms ≈ 7.2 CPU-h + floors ≈ .1 CPU-h + hold-out evaluation
≈ .3 CPU-h; seeds only after an activation; no seed, epoch or knob added to a floor-level instance.

**4. What the toy established and what it changed in the design.** A standard-library gridworld with the
same structure (corner sites served only through held relay chains, known windows, sparse +1 per held
window, optional decoy), tabular REINFORCE analogs of the five arms, five seeds, two difficulty rungs,
about 12 minutes of CPython per rung. At the needle rung (random targets hit a window in 2% of episodes)
no arm leaves the random floor in 5,000 episodes. At the wider rung (13%) every arm learns and the arms
separate: the hierarchy with four-fold discriminator weights activates earliest and in 5/5 seeds (2.05 ±
.03 of 5 windows), the count bonus reaches the same level about 750 episodes later (2.00 ± .08), flat is
a little lower and more variable (1.78 ± .17), the hierarchy at the project's default weights is no better
than flat (1.58 ± .24, 4/5), and the hierarchy without discriminators is the worst and least reliable arm
(1.23 ± .31, 3/5). Every activated learner found only the chain of the site that pays twice. Two lessons
were folded into the design: arm 1b (the discriminator reward is an exploration device whose effect
depends on its weight relative to the sparse reward), and a sparsity calibration band at the zero-fit
stage (the random slot program must satisfy 5–20% of windows; below 1% loosen the served condition to 6
of 10 or lengthen the hold before any fit; above 30% the objective is not sparse). The toy has no radio
physics, PPO, Transformer coordinator or learned low-level skills; it says which design choices make the
real comparison informative, not what the host will do.

**5. Points to weigh explicitly** (the peer flags them; they are yours to judge):

- The served condition is a **cluster-level joint event** (8 of 10 registered users held for 20 ticks),
  deliberately not the per-user F count, because the question is about forming and holding a joint relay
  chain. F remains computable on the same trajectories as a secondary reading. If you prefer a
  per-user settled objective, say why and re-price; do not run both.
- Arm 1b is a declared second HMASD arm, not a sweep; its reason is the toy's weight dependence.
- The count-bonus arm (4) is the control that separates "skill discovery" from "any exploration bonus".
  If it cannot be added without touching shared code paths, the mechanism claim must be stated as
  conditional on that missing control.
- The zero-fit stage is the cheapest refuting run (room condition O_W − sticky ≥ 2.0 windows and O_W ≥
  3.5; near-camping ≈ 0 windows with high contract reward; the sparsity band). It is one stage of ≈ .1
  CPU-h, not a gate ladder.

**6. Your task, in order.** Each step is a stop point; stop whenever a step's result says the next is
not worth buying, and record why.

- **A. Decide (0 fits).** Under your method, is the now-priced comparison worth ≈ 7.6 CPU-h on
  `local_linux` as a new Codex question, given the three current DM investments (B04 learning curve, S/C
  frozen cooperation, B11 travel ties)? If no: write the reason in one or two lines next to the
  sparse-window candidate sentence in RESEARCH.md's current plan paragraph and stop. If yes: assign a DM
  (a native child under the Root-led trial, or an existing DM whose paths do not overlap; model
  `gpt-6-astra`, `thinking: "max"`, verified on its first turn) and register a new direction (proposed
  slug `uav_sparse_window_relay`, own `experiments/candidates/<direction>/`, tests, NOTES, `runs/`,
  `temp/directions/<direction>/`). The direction imports the Claude-owned host read-only and subclasses
  it in its own directory; if a shared-code change turns out to be unavoidable (for instance the schedule
  features in `hmasd/agent.py` normalisation), raise it to the owner rather than edit the peer's paths.
  The DM's first NOTES entry copies the pre-declared reading rule from the design doc as a written rule
  before any code.
- **B. Independent scientific review before any fit** (section 5: a new host objective and a new metric).
  Give the reviewer the design doc, the toy RESULTS, your archived conditions and the Oracle's, and the
  four points in item 5. The reviewer's dissent, if any, is recorded in NOTES and resolved before step D.
- **C. Zero-fit stage (≈ .1 CPU-h, 4–6 engineering hours).** Host subclass with the fixed layout and the
  admission rule (report the regenerated-world count), schedule features, served condition, sparse
  reward, the four references on the 64 dev worlds. Publish the readings. If the room condition fails,
  fix the geometry or the window length; if the sparsity band fails, loosen the served condition or the
  hold; re-run the references once; if either still fails, stop and record it as the cheapest refutation.
- **D. Fits.** One instance per arm (1, 1b, 2, 3; 4 if available) at 360k native steps, w_dense = 0,
  common worlds, launched through `scripts/hmasd_launch.py` with runner-side admission on `local_linux`
  (`--direction`, `--lead`, `--sha`, `--output`, `--snapshot`; the published source committed first).
  Read on the 32 hold-out worlds by the pre-declared rule; the decoy variant and seeds only after an
  activation; a floor-level instance gets nothing added.
- **E. Boundary statement.** Say which belief, ordinary reference or investment decision changed and
  which did not, including uninformative outcomes and their cost (design doc section 2, "What each
  outcome changes", gives the three branches). Publish NOTES, `runs/`, the RESEARCH row and any shared
  background the evidence affects. If the result bears on the Claude side's reserve directions, one
  `EVIDENCE` file under `docs/Claude_docs/inbox/YYYYMMDD_sparse_window_relay_ROOT.md` with commit, path
  and anchor; no reply needed.

**7. Optional zero-cost items** (only if cheap for the DM that owns the question):

- Toy learning curve at 10k and 20k episodes on the wider rung
  (`python3 docs/Claude_docs/toy_studies/sparse_window_relay/swr_toy.py --r-access 2 --episodes 20000
  --out <file>`; about 50 minutes of CPython at 20k on one core): does the plateau at the first site break,
  that is, are the other three chains ever found? If never, the real host's exposure budget should expect
  one mission, not a schedule, and the design's activation band already reflects that.
- For `/root/dm_s7_prediction_use`: the Claude note's [DECIDE] 3 reading on the S7 B10 panel that has
  landed, the per-world envelope max(C, H_A, F_A) − C over
  `runs/uav_fleet_transmission/b10_service_assignment_a01/perworld.json`, with the band the note
  pre-wrote (declare a gate study only if the envelope is ≥ 3% of C's mean J with at least 8 of 32 gaining
  worlds; otherwise record and stop). Subject to your recorded scope correction: it bounds those fixed
  policies on that panel only.

**8. Constraints to carry.** Owner pause on the Claude session unchanged; never edit Claude-owned
direction paths; stage and commit explicit paths, no `git add -A`, stash, reset or force-push; price fits
well under 10 CPU-h before launch and record actual wall time, node and started fits; cheapest refuting
run first; no fit added to rescue a floor-level instance; no skipped or quarantined test to get a launch
through; messages only through the owner-authorised channels.

**9. Return to the owner.** The decision at A with its reason; if executed, the zero-fit readings, the
reviewer's verdict, the fits' reading by the rule, the boundary statement, and the actual cost (started
fits, wall time, node). Pointers to commits, paths and anchors; not the evidence itself.

<!-- END PROMPT -->
