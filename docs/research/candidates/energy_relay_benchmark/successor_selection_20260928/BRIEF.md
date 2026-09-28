# Oracle brief — select the Claude session's next question on the owner's main line (2026-09-28)

Decision owner: the Claude DM (this session). You return a decision memo; the DM accepts, has it
reviewed (critic pass, then Pro under section 5), declares and launches. You are read-only. Do not
ssh to any node; do not run anything result-bearing; do not write outside
`temp/directions/energy_relay_benchmark/scratch/oracle-selection-20260928/` (write your memo there as
`MEMO.md`; if the harness refuses that name, `memo_oracle.md`).

## The decision

The owner's main line (their words, 2026-09-27, relayed by Root in
`docs/Claude_docs/inbox/20260927_uav_cooperative_planning_ROOT.md`, confirmed by the owner in person
today): "主要还是uav路径规划 uav集群的合作规划 使用marl增强 这些合作和规划" — UAV path planning and swarm
cooperative planning, enhanced with MARL; MARL algorithmic innovation or reusable planning-algorithm
engineering innovation both count; the owner called the Claude direction's "energy relay optimisation"
off track. Today the owner confirmed: after the running study `b05` closes, the Claude session's next
question is selected from this main line, with no further energy-relay diagnosis or attribution
continuation. Root's owner-approved refinement (858e8cff5, `.agents/skills/hmasd-loop-dispatch/SKILL.md`
and `hmasd-portfolio-task`): attention on consequential questions that could change a belief, an
ordinary reference or an investment; diagnosis/baseline attribution only when it changes such a
decision; at a boundary report what changed and what did not, with the cost.

Your task: recommend ONE question for the Claude session to own next (plus at most two alternatives,
ranked, with why they lost), in the form the method requires (`.agents/skills/hmasd-scientific-tools/SKILL.md`,
especially "Design the comparison and decision exposure"; and `.claude/agents/hmasd-oracle.md`).

## What the memo must contain

1. **Contribution claim** in planning terms: if fully successful, what planning capability does the
   UAV swarm gain (joint path / coverage layout / role commitment / replanning consequence), and
   what real service quantity on the actual host measures it (native J with λ = 2 return cost, QoS/step,
   delivered throughput — read the host facts, do not assume).
2. **Package reuse or component attribution?** Say which the question buys, and pick the comparator for
   that decision: the strongest applicable existing ordinary alternative (reuse) or the matched
   control with its narrower interpretation (attribution). Name the nearest existing methods and the
   strongest simpler alternative (same-information competent ordinary planner; flat / same-architecture
   learner). Locate the intervention in the mathematical, information and game structure and name
   the MARL coupling a single-agent or bandit prototype omits.
3. **Decision exposure**: for any conditional/learned choice, what eligibility, output→choice mapping,
   fallback and duration look like on the host; the requested-vs-executed readings that separate
   nonactivation, sparse exposure and active adverse intervention.
4. **Outcome table**: what each plausible outcome (clear positive, flat within the reading band, clear
   negative, technical failure) would change — which belief, reference or investment.
5. **Cost** in fits and wall on `wsl_4070` (facts: a B02 SET-recipe fit of 1.2 M transitions on CUDA
   ≈ 5.6 h; a 32-world × 2-mode CPU panel at 8 workers × 1 thread ≈ 14 min; the two recent CUDA
   training processes each died once at ≈ 5.5 h with a CPython-level heap fault — a resume contract
   exists, but budget the risk). The smallest complete experiment that changes a real judgment.
6. **Overlap check** against Root's DMs so the estimand is complementary, not contested:
   `docs/research/RESEARCH.md` standing table (lines ≈ 960–1015: `uav_persistent_service` ACTIVE —
   nearest-station return admission / dwell commitments / redeployment under central snapshots;
   `uav_cooperative_planning`, `uav_transit_handoff`, `uav_energy_coordination`, `uav_active_sensing`,
   `uav_radio_placement`, `uav_geometric_generalization`, `uav_roster_memory`, `uav_information_value`,
   `planning_policy_compression`, `controller_composition` … each with its closed/reserve verdict),
   the archived planning review
   `docs/research/archive/2026-09-27/RESEARCH-four-codex-root-handover.md#uav-planning-review-20260927`
   (independent Scientific Reviewer reconstruction with MATERIAL_DISSENT on the earlier 4-fit T′/SET+A
   argument, DM4's undefined target bonus and the credit-to-training bridge), and Root's 2026-09-28
   inbox scope notes (`docs/Claude_docs/inbox/20260928_*_ROOT.md`). Say explicitly which Root
   estimand your recommendation must not duplicate and how it is complementary.
7. **TRIED / RECORDED / NEW** for every idea you rely on, checked against: the July record
   (external-review rounds R29–R54, the n_k literature deep-dive, the upstream RESEARCH reviews and
   FOUNDATIONS — search `docs/research/` and `docs/Claude_docs/reviews/`), `docs/new-libs/LIBRARY_INDEX.md`
   (27 foundations PDFs) and the owner's MyLib catalogue
   `~/projects/Inst-sci/papers/MyLib/json` / `llm-index` (190 MARL PDFs). Read the load-bearing
   primary passages yourself (the PDFs are local); an author's abstract is not the evidence. The
   owner has rejected re-skinned triggers, baselines and probes as old ideas; mark honestly.
8. **What the Claude session already reasoned**: `docs/research/candidates/energy_relay_benchmark/NOTES.md`
   from the 2026-09-27 entry "Owner decision (A): T′ line closed; a reasoning-only phase for a
   planning-side MARL candidate opens" through the reasoning-phase entries that follow (≈ lines
   5259–5800: the deployment deficit stated from first-hand host facts, boundaries with DM3 and Root's
   transit-handoff design, candidates, and a composed Pro question), then b04 (geometry probe: the
   "row A" fixed-heading phenomenon; W-half vs E-half service) and b05 (canonical-frame training
   under the SW wrapper; c02–c04 dev snapshots track the unwrapped SET recipe; primary L at c06
   pending). Use what still holds; say what the b04/b05 evidence changes for a planning question
   and what it does not. Also `docs/Claude_docs/reviews/RESEARCH_PROGRAM_DIAGNOSIS_AND_RESET_20260926.md`
   and `RESET_RESPONSE_AND_FIRST_STUDY_20260926.md` (the three-layer verdict: host, instrument,
   workflow; "benchmark-first on S7"; LOCAL1 ≈ HMASD on S1).
9. **Host facts to trace yourself** (only the consequential premises): scenario S7-S2/H3000 energy-aware
   relay host `envs/pettingzoo/relay/energy_aware.py` (users, stations, return constraint λ = 2, the
   charging allocator, the shield), the B02 SET recipe `experiments/candidates/energy_relay_benchmark/b02/`
   (what the learner controls: proposals → shield → executed physical actions; k = 10 central snapshot),
   the b01 evaluation contract (`b01/evaluation.py`, dev 955001–032 / hold-out 957001–032), and the
   frozen policy interface a planning question would have to respect or explicitly change.

Constraints on the recommendation: one result-bearing study at a time; declare before running,
never extend after scores; a single training instance is a conditional exploratory observation, not
a confirmation, so the design must say what one fit can and cannot establish and whether a second
seed is part of the first declaration or a conditional follow-up; a justified "no new fit, ordinary
planner study first" is a valid recommendation if it changes a real decision — but the owner asked
for MARL-enhanced cooperative planning, so a zero-fit planner-only study needs to say what MARL
question it decides. Do not invent facts; label verified / inferred / conjecture; cite file:line for
every host or record fact you rely on. Length: as long as the decision needs, no longer.
