# Load and critical-member generalization

Direction: `load_critical_member_generalization`.
Direct DM: Codex task `01a0c9b0-bcc3-7643-8058-5e565402f558`, host `local`.
Authoring checkout: `/home/fires/.codex/worktrees/5899/hmasd-wsl`;
branch: `codex/load-critical-member-generalization`.
Pro conversation: new; Jev account identifiers remain in local operation state only.

## 2026-09-22 — Initialization, inherited evidence and proposed first observation

The owner selected literature-plan item 6. Initialization completed at published main
`e46deae6aae14dd54180bfabd982fd00840a14de`; that revision is the initial authoring base
and includes plan input `fe6e990cb161af5483d12da624e0184e75db3ffd` and B02 publication
`5113f4917`. This task owns this notebook, its own code/runs, and its RESEARCH entry.
There is no continuing App communication with the dispatcher or other DMs. Claude's FSD
pause and G33 freeze remain. No fit, evaluation operation or Pro Send is accepted at this entry.

The active dependency is the **assigned B03 work of the original `agent_count_generalization`
DM**, task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`. Its declared H6/SET × raw/clip training
comparison, records and operations remain exclusively its responsibility. We consume only
published evidence and eventually its two clip-trained final-45 checkpoints, after that DM's
complete reading and fixed subsequent action contract. At the published evidence revision
read here, B03 was in implementation/review; no completed B03 checkpoint record was available.
This is a real asset dependency, not authority to duplicate production, monitor its handles,
or substitute old raw-trained checkpoints. Independent scene/evaluator engineering can proceed.

### Evidence and working explanation

Read the original direction's complete B02 result at
[`cadea93515a2ff3fe4f5b43658d5adba2590b99c`](https://github.com/CartmanFatass/My-paper-code/blob/cadea93515a2ff3fe4f5b43658d5adba2590b99c/docs/research/candidates/agent_count_generalization/NOTES.md#2026-09-22--b02-complete-bounded-deployment-preserves-the-package-advantage),
now incorporated in main. Its evaluator source is `dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c`.
The 0-fit, 288k-step comparison reports that all 288 raw/clip policy-world position paths
diverge after the first action. H6−SET clipped-deployment J is +.029915413 / +.041645180 /
+.054739264 at N4/6/8. Both package means improve under clipping at all N, but 4/18
policy×N changes and 86/288 paired worlds are adverse. These are the same six old training
instances. They weaken the explanation that the H6 advantage requires executing unbounded
deterministic actions; they do not settle the historical training-exposure explanation.

B03's existing prospective scope fixes four 360k fits, H6 seed 942201 and SET seed 943201,
raw/clip training with common clipped deterministic deployment. Gaussian samples, raw-sample
PPO likelihood and entropy remain unchanged. This direction does not revise that comparison.
The eventual reused policies each represent one training instance; new evaluation worlds do
not make them a replicated learning comparison.

The relevant [shared background at initialization](https://github.com/CartmanFatass/My-paper-code/blob/e46deae6aae14dd54180bfabd982fd00840a14de/docs/research/RESEARCH.md)
changes this design concretely: topics 1–2 require native service consequences and an actual
information path for adaptation; topic 3 requires same-N comparisons, lawful inputs and no
skill attribution from package differences; topics 4 and 6 separate finite learning from
representation and separate evaluation worlds from training units. Accordingly, the first
question is **how capacity converts each fixed learned geometry into service**, not whether
an encoder has acquired general count invariance or whether hidden capacity is observed.

### Actual host and primary-source bridge

Native S1 has U=50 static uniform users, area 1000×1000, homogeneous integer connection cap c,
and fixed per-episode roster. It has no traffic queues, capability vector, persistent identity
input or true local valid-mask. Local observations have 104 entries: own position, 20 ranked
user slots, 10 peer slots and time. N4/6/8 does not exercise peer-slot overflow. CountAdapter's
central state is 133 entries (8×3 positions + 8 roster bits + 50×2 users + time); roster bits
are not local visibility masks. Capacity and connections are absent from actor/state inputs.

SET remains the ordinary shared mean/max/count encoder with GRU and a 10-step held central
snapshot, while H6 retains its k=10 hierarchy. Both receive the same lawful source information
at the declared clock; representation, compression, auxiliary objectives and computation differ.
No new attention, analytical labels, capacity cue, connection truth or local mask is introduced.

The following local primary passages were inspected, rather than treating the reading index
as primary evidence. JSON/PDFs are under `/mnt/c/Projects/Inst-sci/papers/MyLib/`; this records
the limited passages used here, not a new claim of reading every appendix.

- **M3FC, MARL-0438**, §2.1–2.2 p3, JSON `/kids/28,32,33,48,49`: minor policies use own
  state, major state and empirical distribution. It motivates separating a few influential
  members, but does not grant mean-field guarantees to our few locally observed UAVs.
  [Official paper](https://proceedings.mlr.press/v235/cui24a.html).
- **MIPI, MARL-0561**, §§3/4.1 pp4–5, `/kids/34,59,69,88`: conditional MI penalizes dependence
  on team information under that paper's information assumptions. This is a precedent for
  a question, not evidence that deleting N information would help here. The existing full
  reading also retains overcompression and replication sensitivity; those empirical appendices
  were not newly reread for this entry.
  [Official paper](https://papers.neurips.cc/paper_files/paper/2023/hash/0799492e7be38b66d10ead5e8809616d-Abstract-Conference.html).
- **Deep Sets, DMOD-CCA390C5FE**, pp2–3 `/kids/23,24,44,46,48,50`: shared element maps and
  pooling support keeping a competent ordinary set comparator. Permutation symmetry does
  not prove UAV count transfer. **Set Transformer, DMOD-F08EC1A407**, p5 Table 1,
  `/kids/97–102`: ordinary max pooling beats SAB+PMA on the known maximum target
  (MAE .1355 versus .2085); an attention upgrade is not selected merely from the paper name.
  [Set Transformer](https://proceedings.mlr.press/v97/lee19d.html).
- **Mean-field sampling, MARL-0637**, p3 Eq.1, `/kids/31,32`: local transitions are conditionally
  independent with a global agent. That is not the interfering UAV/visibility-truncation
  model. Previously recorded printed-proof concerns were not independently re-audited here
  and are unnecessary to this mismatch judgment.

### Proposed B01 five-cell evaluation — pending focused Pro reading and B03 assets

Reuse the two B03 **clip-train, final45** policies, with deterministic coordinate-clipped
execution. Keep reward, source configurations, information clocks, parameters and normalizers
frozen. Final checkpoint identities will be bound from the producer's immutable published
summaries before any evaluation admission; they are currently unavailable.

| N | c | K=Nc | nominal U/K |
| ---: | ---: | ---: | ---: |
| 4 | 10 | 40 | 1.25 |
| 4 | 20 | 80 | .625 |
| 8 | 5 | 40 | 1.25 |
| 8 | 10 | 80 | .625 |
| 6 | 10 | 60 | .833333… |

Each cell has 16 new worlds and 500 steps for each of the two policies: **0 new fits,
80,000 evaluation team steps, 160 episodes; zero training transitions, updates and optimizer
calls**. Retain every outcome. No checkpoint selection, score-dependent world expansion or
automatic training follows. Prefer wsl_4070, CPU FP32/four Torch threads matching the source
evaluation; actual admission/resources and command/loading/inference/simulation costs are
reported, not inferred from fit count.

World IDs are 0…15. Independent user/UAV streams are derived from
`numpy.random.SeedSequence([260922, 6, world_id, stream])`, stream 1 for users and 2 for UAVs;
one generated uint32 initializes a local `RandomState`. Generate all 50 uniform users and
eight UAV positions (x,y,z in native per-UAV draw order), then take the first N UAVs. Preserve
float64 physical positions. World content is identical across arms/capacities and users are
identical across N. This replaces the original N-dependent reset consumption order; equal
seed alone would not match users. Stream 3 additionally keyed by test N is reserved for
evaluation runtime initialization, shared across capacities/arms; it supplies no actor feature.
These addresses are distinct from the published B01/B02/B03 evaluation ranges.

Fully reset hidden states, skills, timers and held snapshots at each episode. With the same
N, actual initial positions, checkpoint, normalizers and runtime RNG, capacity changes should
leave deterministic actions, observations, state and geometry identical because neither c nor
service reward feeds that policy's observation history. Check the identity directly, including
across the k=10 boundary. A failure is a contract/implementation question before interpretation,
not evidence of online load adaptation. Capacity changes only connection/reward consequences.

Read native `J=N*scalar_return/500=.7*mean_coverage+.3*mean_quality−mean_height_penalty` within
each N. Let G(N,K)=J_H6−J_SET and D_N=G(N,80)−G(N,40). Show both arms' absolute capacity
changes and all components, then remaining G(8,K)−G(4,K). Matching total K does not identify
a pure count effect: it changes per-UAV c and capacity partition, interference, density and
policy geometry. Nominal U/K is not reachable demand, throughput or attainable headroom.

### Analytical corrections and discriminating predictions

Independent Critic `five_cell_critique` returned material dissent to the plan's implied
relative-sign and height-offset reasoning, while retaining the zero-fit study's information
value. The DM checked the relevant native source and adopts these corrections as premises
for the focused Pro question, without treating local criticism as a replacement for Pro.

1. **Height cancels in D_N.** Same-N trajectory identity makes each policy's height penalty
   exactly capacity-invariant. Quality can offset coverage gains in this interaction; height
   cannot. Height remains relevant to package levels and across-N comparisons.
2. **Total capacity is not freely transferable.** Current S1 defaults to `use_fdma=False`,
   `min_sinr=0 dB` and positive noise (`−80 dBm`). Each signal's denominator includes all
   other UAV signals. In exact arithmetic two UAV signals cannot each exceed the other plus
   positive noise, so at most one UAV qualifies per user. Conditional on this unchanged
   contract, if e_i is UAV i's eligible-user count, native assignment serves
   `S(c)=Σ_i min(e_i,c)`, choosing its highest-SINR users. Verify constants and numerical
   threshold cases in actual traces rather than silently imposing this formula.
3. **Capacity relaxation has no necessary relative sign.** Let b_a be the mean extra users
   served by arm a when capacity increases. Then
   `D_N=.7/50*(b_H6−b_SET)+.3*(Δquality_H6−Δquality_SET)` under verified trajectory identity.
   A positive value can mean greater H6 dependence on slack, not better overload handling.
   Quality averages over connected users, so serving extra low-quality users changes composition.

These follow from `envs/pettingzoo/scenario1.py` (constructor, reward and both assignment
paths) and `uav_env.py` (constructor, observation, SINR and greedy assignment), at the initial
main revision. A simple logical bridge illustrates the sign issue: N2/U8, equal quality and
height, disjoint eligible sets; H=(4,4), SET=(8,0) gives a served-count gap 2→4 when c2→4,
whereas H=(2,2), SET=(8,0) gives 2→0. This omits physical interference and learning and is not
UAV evidence; it shows why a generic capacity story does not entail a relative direction.

The plan's narrow conjecture remains testable: capacity relaxation reduces eligible-unserved
users and gives H6 greater additional coverage and J at both N. Its strongest simpler account
is different frozen geometry/eligibility concentration followed by capacity truncation and
quality composition. The conjecture is not a prerequisite positive screen for all future work.

| Observation | Bounded interpretation |
| --- | --- |
| H6 recovers more users and G grows at both N | Supports this marginal-service prediction for these policies; also consistent with more dependence on slack. |
| Both recover users similarly, G is stable | Capacity affects absolute service without explaining the relative gap. |
| H6 recovers more users but G does not improve | Intermediate prediction succeeds; native prediction fails, potentially through quality composition. |
| Opposite N signs or matched-K residuals | Retain geometry × local-capacity effects; no representation-failure attribution. |
| Little truncation in both arms | Weakens the capacity bottleneck on these observed paths, not its possible role under other learned geometry. |

Retain per-UAV e_i, connections, occupancy/full rates; SINR-eligible but unserved users;
SINR-ineligible users; quality/coverage/height; visible-user truncation with denominators;
and action/observation/state/geometry equality evidence. These are analyst diagnostics, not
policy inputs. Mixed or flat outcomes do not prove equivalence. Worlds characterize conditional
fixed-policy performance, not population learning superiority or a skill mechanism.

### Conditional subsequent investment, not an accepted batch

A useful residual geometry/service tradeoff under an intended capacity mixture could justify
learning a compromise. The plan's optional two-fit comparison is H6 versus SET, each N6,
360k steps, with 720 episodes balanced across c∈{5,10,20} (240 each, shuffled prospectively).
Its cost would be **2 fits, 720k training + 400k evaluation team steps**: development at
0/120k/240k on 16 worlds per five cells; final360k on 32 separate fresh worlds per cell.
It has not been selected; actual new training/world seeds would be fixed in a new entry.

Hidden c and reward-independent observation dynamics mean a fixed policy's expected mixture
return equals its return under the reward averaged over c along the same geometric law.
Training may learn a different compromise from changed rewards; it cannot condition its
behavior on an unobserved c or inherit a worst-case guarantee. Two fits compare packages
under that mixture only. Causally comparing balanced versus fixed training requires a new
matched H6/SET × fixed/balanced four-cell design, not a cross-seed splice with B03.

Heterogeneous capacities `[20,8,8,8,8,8]` versus `[10,10,10,10,10,10]` at N6/K60 remain a
separate possible successor requiring both allocation paths and lawful, matched capability
inputs. Randomize the high-capability member's position; a fixed slot is not capability.
Ordinary capability concatenation/FiLM SET would be a primary reference. No interface change,
heterogeneous fit, architecture search or confirmation is selected here. No decision-changing
prediction remaining is a reason to stop this route, without declaring the broad class impossible.

### L0 — Independent matched-world and capacity-diagnostic implementation

Before B03 assets and while awaiting advice, implement only the already justified engineering
primitives: `experiments/candidates/load_critical_member_generalization/load_probe/scenes.py`
and package initializers, plus matching tests in
`tests/experiments/candidates/load_critical_member_generalization/load_probe/`.
Deliver a native-S1 scene factory/reset using the declared independent streams and N-prefix,
and read-only service diagnostics including e_i and the conditional S(c) identity. Return a
native environment that can later be wrapped by the unchanged CountAdapter; do not duplicate
or alter that adapter, recover unrelated branch history, or construct a learner/runner yet.

All scene-specific c/threshold parameters must be final before the returned explicit reset;
after installing shared physical positions refresh channel/cache, observation and state in
native order. Preserve static-user/free-space dynamics, native reward/termination, 104-wide
local observation, no added input, no global RNG consumption and no core file edits.
Small native fixtures test actual caps; same user worlds/UAV prefixes across N; exact same-N
observations, states, SINR and action-driven trajectories across c; reward identity; separate
quality composition; 0-dB unique eligibility and S(c) including threshold/domain failure
reporting; deterministic repeated reset and the k=10/time boundary. Use modest fixed actions,
not production policies, and no result-bearing CLI. Tests own/clean scratch under temp.

One bounded Implementer may own only those paths; DM owns NOTES, acceptance and publication.
No fits, no scientific outputs, no Pro, no launch and no children. Stop on a required core
semantic change or missing source prerequisite. Independent Reviewer will examine the scene,
RNG and diagnostic code before its use by a result-bearing evaluator. Source-complete
checkpoint loader, frozen runtime and native-admission entry are a later L0 once advice and
published B03 identities are actually available; independent progress does not fabricate them.

## Pro question 2026-09-22 five-cell-identifiability-and-next-learning

Conversation: new (private Jev URL remains local).

**Question.** Before adopting the first study, does the proposed five-cell frozen-policy
capacity comparison provide a useful and correctly bounded distinction, and what observation
could justify further learning investment instead of reserve/closure? Please focus on the
actual hidden-capacity interface and strongest simpler explanation, not a broad architecture
survey. Test the corrected algebra and the narrow directional conjecture above. In particular,
does the unique-eligibility simplification hold under the native SINR/assignment contract,
and how should local capacity partition be separated from any residual N interpretation?

The prior direction's action-law Pro answer concerns B02/B03, not this capacity question.
B02 is complete, but **B03 is a pending external asset and scientific reading**, not a claimed
bounded-training result. Give advice conditional on the declared B03 clip-training contract;
do not invent its outcomes or require duplicating it. If its published result materially
changes the premises, that later decision will be read at the time.

The decision the answer can change is whether to adopt/revise this 0-fit panel and its
interpretation, and the conditions under which a hidden-capacity robust-learning comparison
would be worth selecting. Do not automatically select the optional two fits: explain what
new judgment H6/SET under balanced c could change, compared with simply reading frozen service
conversion. Those fits do not identify balanced-versus-fixed causality. Critical-member
heterogeneity would introduce a new interface and remains conditional.

**Standing and cost.** The preceding entry supplies actual published B02 evidence, adverse
outcomes, the competing explanations, proposed worlds, input permissions, analytical checks
and reading branches. The first study is 0 fits/80k evaluation steps, two old training units;
it is not zero compute. Optional new learning would be 2 fits/720k train+400k eval and remains
unselected. Engineering-only native fixtures may proceed independently of this scientific choice.

**Context and source precedence.** Paths below inherit the full `source_sha` in the send
message unless a different full revision is explicitly given. Read the selected sections,
not recursively every linked archive.

- Current owner authorization/ownership and background: `docs/research/RESEARCH.md`, active
  `load_critical_member_generalization` row, relevant topics 1–4 and 6; this notebook's entry.
  Owner has started this independent direction; Claude remains paused and G33 frozen.
- Governance: `docs/project/OPERATING_CONSTITUTION.md` §§1–5, 7–8 (DM choice, no fit allowance,
  Pro adviser, scientific minimums). Methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`
  “Update the working explanation”, “Comparators and MARL information”, “Statistics”,
  “Cost and exposure”, “Pro”; research-engineering “Checks and review” only for feasibility.
- Starting proposal: `docs/research/designs/LITERATURE_RESEARCH_PLAN_20260922.md#plan-6`;
  the corrections in this question take precedence over the original relative-sign/height
  interpretation. The plan is not an accepted batch or a new rulebook.
- Evidence: `docs/research/candidates/agent_count_generalization/NOTES.md`, headings
  “B02 complete: bounded deployment preserves the package advantage” and “Full Pro reading,
  B02 execution probe and B03 investment decision”; complete B02 summary is at
  `runs/agent_count_generalization/s1_action_law_b02_probe/summary.json` (read relevant aggregate,
  components and count fields rather than treating a receipt as a result).
- Native contract: `envs/pettingzoo/scenario1.py` constructor/reward/reference assignment and
  `envs/pettingzoo/uav_env.py` constructor/observations/SINR/greedy assignment at source_sha.
  Actual policy information/configuration remains at the separately published frozen revision
  `dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c`,
  `experiments/candidates/agent_count_generalization/{adapter,configuration,models,runner}.py`
  and `action_law_b02/probe.py`. These files are not assumed present on the new direction branch.
- Primary literature passages and official links are paraphrased above. Local MyLib paths are
  not remote-access claims. Use the supplied excerpts for their bounded bridge or inspect the
  official paper; state any consequential source you could not read.

**Return.** Give the strongest alternative, what this design can strengthen/weaken/leave
unresolved, material corrections and the smallest useful next observation. For any recommended
learning step, state its intermediate and native prediction and fit/non-fit cost, with honest
single-instance limits and unfavorable branches. No new idea or positive result is owed.
End with `MATERIAL_DISSENT: yes/no` and the material substance if yes. Do not grant approval,
launch experiments, expand owner selections or create a new record type.

**Answer-only writing.** Write only inside this question's empty `### Answer` subsection of
`docs/research/candidates/load_critical_member_generalization/NOTES.md` on branch
`codex/load-critical-member-generalization`. Read the question at the pinned source; fetch
the latest target file before editing and use its actual blob SHA. Preserve all other bytes,
including the question and prior records; stop on overlapping edits. Report the actual commit
on successful write. If GitHub writing is unavailable, return the complete answer in chat,
not a status, link or SHA alone. Keep private account/conversation facts out of Git.

### Answer
