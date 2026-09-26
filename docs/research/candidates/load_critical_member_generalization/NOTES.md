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

#### 结论：保留五格，但把它读成固定策略的服务转换，而非负载适应或纯人数识别

我的建议是采用题内**已经修正的五格零新训练设计**，保留 N6/c10 锚点及全部不利结果。它能回答一个有用的窄问题：对于最终复用的两条 B03 clip-train 策略，各自既定的几何轨迹在不同每机连接上限下，产生多少额外服务，以及这种服务转换是否改变 H6−SET 的原生收益差。它不能识别“技能学会了负载适应”，也不能在“容量机制”和“人数机制”之间作排他性裁决。**现在不选择可选的两 fits。** 本答复是科学建议，不是运行接受、预算授予或新的审批要求。[题内修正与范围][S0]、[治理 §§3、5、8][S1]

最强的简单解释不是“SET 没有表示容量”，而是：**两种完整学习包形成了不同的冻结几何与 SINR 资格分布；相同的原生分配器按每机上限截断这些分布，再通过已连接用户的质量组成产生不同 J。** 这个解释足以兼容正、零、负的容量交互；即使预写的正向预测命中，它也仍然成立。五格的价值是定量定位这条服务转换链，而不是把它从几何中分离成一个新学得的机制。

#### 1. 本次证据基点及其边界

我读取了指定 `a37eed21e69adf3c6e159a7c255fd8603c1a95db` 下的本题与前文、RESEARCH 的当前授权/本方向行和主题 1–4、6、constitution 指定章节、科学方法指定章节、工程方法的 Checks and review、plan-6，以及原人数方向的 B02 完成记录和 B02/B03 投入决定。原生环境读取同一 revision；策略接口、配置、模型和评估/恢复路径另按指定的 `dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c` 读取，没有拿移动分支替换推理输入。[共享背景][S2]、[科学方法][S3]、[工程方法][S4]、[起始提案][S5]

B02 的大文件通过 contents 接口最初返回空内容，随后通过其 Git blob `baef10dba20bf5fe99441471be0253ccfddaa3ef` 成功读取；我读了相关 aggregate、component 记录及 counts，不把空返回或完成收据当成科学结果。summary 中的 clipped-deployment H6−SET J 为 N4 **+.029915413**、N6 **+.041645180**、N8 **+.054739264**；计数为 0 fits、288,000 evaluation team steps、576 episodes、0 training steps/updates/optimizer calls。完成记录保留 4/18 个不利 policy×N 均值和 86/288 个不利配对世界，并报告全部 288 对位置轨迹在第一动作后分叉。[B02 summary][S7]、[完整 B02 读数][S6]

因此，B02 削弱的是“这些旧策略的优势必须依赖越界确定性部署”，并未消除既往训练曝光、熵激励和有限优化的解释。这里的分量核对也不能移用：B02 改变动作和轨迹，高度项可以变化；本题同 N 改 c 的恒等轨迹对照中，高度不应变化。两种干预不能混为一谈。[S6]

B03 在指定材料中仍是**外部待交付资产和待完成的科学阅读**，不是已知的 bounded-training 结果。后文条件于其既定的 H6/SET × raw/clip 训练、共同 clipped deterministic 部署合同；原始 Gaussian 样本、样本 log-probability 和原始 entropy 合同保持不变。最后复用的两个 clip-train/final45 检查点各是一份训练实例，不因新增世界变成重复学习证据。[B03 前瞻合同][S6]、[本题资产依赖][S0]

#### 2. 隐藏容量为什么不产生同 N 的在线适应

已读原生代码把 c 用于连接分配，而非位置转移、SINR 或用户运动。局部观测是自己的位置、按 SINR 排序的最多 20 个用户和 10 个 peer 槽、时间；CountAdapter 的 133 维 state 是位置、roster 位、用户位置与时间。c、实际连接和服务 reward 均不在这些输入中。冻结评估的 `target.step` 接收 state、observation、时钟和结束标记，没有把上一步 reward 或服务 info 送回策略。[原生观测/转移][S9]、[CountAdapter][S10]、[冻结评估][S13]、[B02 评估入口][S14]

固定同 N、物理初态、检查点、normalizer、runtime RNG 和全部记忆状态后，可逐步归纳：相同策略输入产生相同动作；相同动作产生相同下一几何；几何决定相同 SINR、观测和 state；固定时长终止也相同。因此下一步仍相同。这包括 H6 的技能/计时器及 SET 的 held snapshot 在 k=10 边界的刷新。GRU 能记住合法历史，但这里的合法历史没有提供辨认 c 的通道。两包可以响应几何，却不能在这组对照中响应实际隐藏 c。[S9][S11][S12][S14]

这也不等于“人数不可观测”：roster/count 和合法团队快照仍携带 N 信息，不能为追求某种不变性而删掉。相同源信息和刷新时钟也不意味着表示、压缩、带宽、辅助目标或计算相同；H6−SET 仍是完整包比较。[S2][S11][S12]

实际面板仍应直接检查上述恒等性，而非只引用推导。出现首次分叉，应先定位 reset、缓存、dtype、隐藏状态、配置、RNG 或意外反馈的合同差异；不能将它命名为“发现了在线负载适应”。工程验证与科学收益是两件事，当前咨询没有运行任何生产策略评估或原生 fixture。[S0][S4]

#### 3. 唯一资格化简成立，但容量不能跨 UAV 自由调拨

对一个用户，令 UAV i 的接收线性功率为 p_i，噪声为 η。代码在 `use_fdma=False` 时采用

\[
\mathrm{SINR}_i=\frac{p_i}{\eta+\sum_{j\ne i}p_j},\qquad \eta>0.
\]

S1 将资格门槛设为 0 dB，即线性 SINR ≥1；父类的 −80 dBm 噪声对应严格正的线性值。干扰项包含其他所有 UAV 的信号，不随其是否满载或是否连接用户关闭。假设 i、j 同时合格，记其余信号之和为 r≥0，则

\[
p_i\ge p_j+r+\eta,\qquad p_j\ge p_i+r+\eta,
\]

相加要求 0≥2(r+η)>0，矛盾。因此是**每用户至多一个合格 UAV**，并非每用户必有合格 UAV。该结论来自本机用户链路公式，不是平均场近似。[S8][S9]

令某一步 e_i 为 UAV i 在完整 50 个用户中达到原生门槛的人数。两条分配路径都按 SINR 稳定降序处理合格链路，并检查每机上限及用户唯一连接。在资格集合互不相交时，用户争抢消失；各机服务自己的最高 SINR 前 min(e_i,c) 人，故

\[
E=\sum_i e_i\le50,\quad
S(c)=\sum_i\min(e_i,c),\quad
T(c)=\sum_i(e_i-c)_+,\quad S(c)=E-T(c).
\]

其中 50−E 是 SINR 不合格人数，T 是合格但未服务人数。于是

\[
S(c)\le\min(E,Nc)\le\min(50,Nc).
\]

上界不保证取到：一机排满、另一机闲置时，闲置名额并不能服务只有前一机合格的用户。可报告 `min(E,K)−S(c)` 描述“假想可汇集名额”与实际局部分配的差，但它不是合法改派能收回的服务、可达策略 headroom 或原生最优值。既定几何/资格下，换一个更聪明的派单器也不能凭空创造另一条合格链路；同时不能据此声称原生贪婪规则最大化了含平均质量项的完整 J。[S8][S9]

这个化简要以实际运行域为条件：记录 FDMA 开关、门槛、噪声和数值有效性，使用原生 `>=` 判定，核对每用户合格数、实际连接数以及 S(c) 恒等式；边界案例不能用另加 epsilon 静默改写资格。若发生多重资格、非有限值或分配不一致，保留原生结果并撤回依赖化简的诊断，先查原因。不能把公式用于 FDMA、负门槛或另有按活动链路改变干扰的后继宿主，也不能假定两个数值后端普遍逐位相等。[S4][S9]

e_i 必须在全体用户上计算，不能用 20 个可见槽的长度代替。满载率也应与溢出量分开：e_i=c 可以满载但没有未服务用户，e_i>c 才有截断。占用率、发生截断的 UAV-step 比例、遗漏用户量分别保留分母；roster 位和全 1 动作掩码都不是真实局部有效位。[S9][S10]

#### 4. 修正后的交互代数正确；正号并不表示更能处理过载

记 a∈{H6,SET}，同 N 的低/高每机上限为 c_l、c_h。逐步新增服务数为

\[
m_a=\sum_i\bigl[\min(e_{a,i},c_h)-\min(e_{a,i},c_l)\bigr]\ge0.
\]

它也等于 `Σ_{r=c_l}^{c_h−1} #{i:e_{a,i}>r}`：容量响应取决于资格人数分布在这些局部门槛上的尾部，不由 K 或 U/K 单独决定。令 b_a 为对步骤和配对世界平均的 m_a；Q、P 分别为原生质量和高度惩罚的对应平均，则

\[
\Delta J_a=\frac{0.7}{50}b_a+0.3\Delta Q_a,\qquad
D_N=\frac{0.7}{50}(b_{H6}-b_{SET})+0.3(\Delta Q_{H6}-\Delta Q_{SET}).
\]

这里每臂的 ΔP_a=0，所以高度在 D_N 中严格消去；它仍进入包水平差、跨 N 比较和新策略之间的比较。J 应按 `N×scalar_return/500` 恢复，并与逐步原生分量的平均核对，不把 connected-user 加权的汇总比值冒充原生逐步质量平均。[S8][S13]

质量组成使覆盖与 J 不必同向。某步旧连接数为 s>0，新增 m 人的平均归一化质量为 q_new，则

\[
\Delta Q=\frac{m}{s+m}(q_{new}-Q_{old}).
\]

s=0 时另按原生零连接约定 Q_old=0 计算。新增者在各自 UAV 内排得更后，不保证其质量低于**全队**原已连接用户的平均；故全队 ΔQ 的符号也不预定。不能将“容量放松”直接写成 J 必增，更不能写成 H6 的相对增益必增。

题内两个逻辑反例的计数正确：U8/N2、等质量等高度时，H=(4,4) 与 SET=(8,0)，c2→4 的服务差为 2→4；改 H=(2,2)，差为 2→0。它们只否定必然相对正号，不充当满足真实无线几何的实证。[S0]

因此窄 conjecture 要分别读：两臂 T 是否下降、H6 是否多恢复用户，以及 H6 的 J 增量是否也更大，而且 N4、N8 均保留符号。只有中间量成功而 D_N≤0，不能称原生预测命中。即使两处 D_N>0，也可能说明 H6 的现有几何**更依赖额外名额**；判断过载条件下哪个包更好用，仍要读低容量水平上的绝对 J、覆盖和 G，而不是用斜率代替水平。

#### 5. 局部容量分区与剩余 N 差异：用记账分解，不制造纯效应

把 E、T 按相同步骤/世界权重平均，定义

\[
A_N=E_{H6,N}-E_{SET,N},\qquad
B_{N,K}=T_{H6,N}(K/N)-T_{SET,N}(K/N).
\]

则覆盖部分的包差为 `(A_N−B_{N,K})/50`，完整分解为

\[
G(N,K)=\frac{0.7}{50}(A_N-B_{N,K})
+0.3(Q_{H6,N,K}-Q_{SET,N,K})
-(P_{H6,N}-P_{SET,N}).
\]

所以 `G(8,K)−G(4,K)` 可准确拆成资格总量差的变化、局部截断差的变化、质量组成差及高度差。这能说明剩余差异记在哪个原生后果上，却不是统计控制了中介之后的“纯 N 因果效应”。e_i 和几何本来就随 N、策略及干扰共同变化；配对初始用户并未冻结这些内生量。

现有五格可作三种互补读取，无须加格：同 N 改 c 是主容量干预；同 K 比 N4/N8 显示仍混有每机 c、分区、密度、干扰和几何的残差；已有的 **c10 下 N4/N6/N8** 则固定每机名额，但不固定总容量或联合物理条件。三者均不单独识别抽象人数不变性。N4 的 c10→20 与 N8 的 c5→10 虽同为 ΔK=40，也不是同一个局部门槛区间的响应；不能将 D8−D4 当成普适的容量导数。N6 只有 c10，五格本身没有 D6。[S0][S5]

普通 SET 应继续作主参照。题内 Deep Sets/MIPI/M3FC/均值场摘录提供的是有范围的方法桥梁，不提供本 UAV 的数量迁移保证、删除人数信息的理由或新增 attention 的证据。这里沿用题内所给段落的边界；官方 M3FC、Set Transformer 摘要也不替代全文、表格或附录的独立核验。[题内文献桥][S0]

#### 6. 最小有用观察与结果分支

保留预定的 `2 policies × 5 cells × 16 worlds × 500 steps = 80,000 evaluation team steps`、160 episodes、0 fits/训练转移/updates/optimizer calls。采用已经给出的独立用户/UAV SeedSequence 流及八机前缀；实际用户位置跨 N 相同、同 N 各容量和两包起点相同，不能只比较 seed 号码。物理位置保持 float64，网络/动作按冻结 FP32 合同；episode 重置全部记忆、技能、timer、held snapshot，冻结参数和 normalizer。[S0][S10][S14]

在这些已经计划的轨迹上，最有用的小增量是把**每步实际连接与由完整 SINR/资格得到的 S(c)、T(c)、质量选择相互核对**，并将两臂的容量响应及 D_N 展开成前述分量；不需要先购买新训练、能力输入或一个架构搜索。保留首次/最大 action、observation、state、geometry 差异和 k=10 边界证据。不要为省调用而未经核验便用一条容量轨迹替代整个已声明面板；解析重计是辅助读取，不自动减少所承诺的恒等性检查或改变 80k 计数。

| 实际观察 | 加强、削弱或仍未解决的判断 |
| --- | --- |
| 两种 N 都是 H6 多恢复用户且 D_N>0 | 加强这些固定实例的边际服务预测；仍完全兼容不同几何/资格集中及 H6 更依赖 slack，不证明学得的负载机制。 |
| 两臂都明显恢复用户，G 基本稳定 | 容量影响绝对服务，但未解释相对差距如何变化；不能说“容量没有作用”。 |
| H6 多恢复用户，J 增量却不更大 | 中间预测成功、原生相对预测失败，检查质量组成；不能用高度抵消来救同 N 的解释。 |
| 两个 N 符号相反，或同 K 残差明显 | 保留门槛尾部、局部分区、干扰与几何交互；没有集合编码失败或纯人数机制的归因。 |
| 两臂在低容量下也几乎没有 T | 削弱这些已观察轨迹上的容量截断瓶颈；不排除其他学习几何下出现截断，也不把平坦结果称为策略等价。 |

统计先构造每个配对世界的 ΔJ_a、D_N 和分量，再报告全部有符号结果及均值。16 个世界是固定策略条件下的外生布局单位；同世界的两包、容量、N 共享设计，500 个步骤和 UAV 不是独立样本。需要世界不确定性时，应按完整 world block 保留这些关联，并说明对世界抽样的假设；任何区间都不覆盖只有每包一个训练实例的学习随机性。不能按 seed 接近配对训练，也不能将 160 episodes 或窄世界区间升级为学习总体优势。混合、负面及技术失败保留，不按结果追加世界或挑 checkpoint。[S3]

80k 是 team steps，不是单 UAV 决策数；0 fits 不代表零计算。CPU FP32/四 Torch 线程及优先节点沿现有合同，实际 import/加载、推理、模拟、诊断、资源占用和未测项如实记录；B02 的约 316.584 秒不是新面板的耗时承诺。[S0][S3][S7]

#### 7. 什么观察值得进一步学习，而不是只读完冻结服务转换

**值得买的新增判断是有限学习下的折中是否有用，不是 c 能否被当前 actor 察觉。** 例如，目标使用条件确实含有多种容量；冻结面板显示有实质原生后果的资格集中—截断—质量权衡，旧策略在某些目标条件下损失明显；一个新的共同训练目标有理由改变几何，使目标服务权衡更好。包排序跨容量改变是直观线索，但不是必要门槛；没有正 D_N 也可能有可修改的几何问题。反过来，仅有很大的 D_N、漂亮的 occupancy 图或“均衡训练听起来更稳健”，不足以说明两 fits 会改变任何使用或科学判断。[S2][S3]

对一个冻结且无容量反馈的策略 π，令 X 为其几何历史。在独立抽取、对策略不可见的容量分布 w(c) 下，X 的规律不依赖当回合 c，故

\[
\mathbb E_c[J(\pi,c)]
=\mathbb E_{X\sim P_\pi}\left[\frac1{500}\sum_t\sum_c w(c)R_c(X_t)\right].
\]

这只是期望的交换：混合容量对应沿同一几何规律使用容量平均后的 reward。它不等于把平均 c 代入 reward，因为 min 截断和连接质量比值非线性；也不等于分别对每个 c 找到最优策略后取平均。训练 reward 改变可以使参数更新和最终几何不同，故“隐藏容量”不使新训练无意义；但训练后仍不能在同一可观测历史上因真实 c 不同而条件化行动。均值目标也不会自动产生最坏情形保证。[S8][S9][S14]

若 DM 后来选择原提案的两 fits，能新增的比较是：**H6 与普通 SET 各自在共同 balanced-c 配方下完成 360k 训练后，哪个完整包在预写测试用途上提供更好的原生服务/代价折中。** 它不是 balanced 相对 fixed-c 的因果效应。每臂 N6、720 episodes，c∈{5,10,20} 各 240 个并事先打乱；训练动作映射和潜变量评分保持最终绑定的共同合同，不能顺便加入 capacity cue、tanh、熵调参或新表示。[S0][S5]

这个后继必须写清两个层次的预测。中间预测应是新训练改变了目标条件下的几何与资格尾部，使局部截断/质量取舍朝预写方向移动；仅 T 变小不够，因为让 E 一起塌缩也会减少 T。原生预测应是声明权重下的完整 J 有实用改善，且分别展示低容量、未见 N 和 N6 锚点的损失。若提出 H6 的额外复杂度值得付费，就预写 H6 相对 SET 的目标 J/代价预测；H6 胜出的叙事不是结果义务。中间量改善但完整 J 不改善、SET 吸收收益、只有开发峰值或目标条件损失不值得成本，均削弱继续这一配方的理由，而不是自动加训。[S3][S5]

**必须区分训练容量混合与五格测试目标。** 现有五格不是每个 N 都有 c5/c10/c20；特别是 N6 只有 c10。因此，它能够测 balanced-c 训练后的五格包价值，却不能直接声称测得 N6 上三种 c 的均衡混合回报或其最坏容量表现。可在后继选择时将目的限定为实际五格及其事先权重；若目的确为每个 N 的完整容量混合，则需明说相应评估覆盖/代价，不能给缺失格补成绩或暗中扩充当前面板。若完整 SINR 历史已保留、路径恒等与分配合同已验证，也可对同一冻结几何做缺失 c 的解析服务重计；这不增加训练/环境转移，却仍有计算成本，且必须标为条件反事实重计，不是新增独立世界或新学习证据。

原可选方案的已知成本应完整保留：**2 fits、720k training team steps，另 400k evaluation team steps**。其中开发 0/120k/240k 的五格×16 世界、两包共 240k eval；final360k 的五格×32 个独立新世界、两包共 160k eval。实际训练/世界 seed 尚未绑定，wall 也未知；这些都不是现在的已接受工作。每臂一个新训练实例只能作探索性包判断。要因果比较 fixed 与 balanced 训练，须另行前瞻匹配 H6/SET × fixed/balanced 四格；不能拿旧 B03 的跨 seed 结果补格，该四格也未被选择。[S0][S5]

如果冻结服务转换已足够支持目标条件下的部署选择，或者剩余解释没有一个能改变判断的可执行预测，就没有理由为维持路线而训练。B03 资产未就绪是实际依赖，不是失败结果；读完五格后因信息价值/机会成本而 reserve 或收束，也是有范围的投入判断，不是否定所有隐藏容量学习。反之，不需要证明可达最优、先跑阳性 toy 或先获得一般理论保证才能考虑一个真正有区别的有限学习问题。[S1][S3]

#### 8. 工程与关键成员后继仍保持原边界

当前 L0 的独立场景/诊断工作合理。S1 构造中父类先 reset、子类后设置 min_sinr/c，最终参数后的显式 reset 及共享物理位置安装后的 cache/channel/observation/state 刷新必须准确。旧 `make_envs` 未显式传 c，不能因改了一个外层配置字段就假定真实上限已变。另一方面，B02 的生产 loader 写死旧 B01 launch identity、六个旧 source policies 及其 summaries；只能复用严格恢复/冻结检查的方法，不能原样冒充 B03 资产装载器。后来依生产者不可变 summary 绑定 clip-train/final45 身份，是原合同的落实，不是要求重复生产或新增审批。[S8][S10][S14]

五格没有测试能力异质性。`[20,8,8,8,8,8]` 与 `[10,10,10,10,10,10]` 的同 K60 后继会引入容量向量和新的合法信息接口；若被选中，要同时处理两条分配路径、随机高能力成员的位置/槽位、匹配自身/可见 peer/中央快照能力信息，并以普通能力拼接或 FiLM SET 为主参照。固定槽位不是能力，某机在当前几何上影响大也不证明已学得关键成员泛化。本答复不选择该后继。[S0][S5]

最后明确未读/未测范围：未直接读取节点上的 B02 二进制 checkpoints/NPZ traces，未独立重做 DM 的全部逐轨迹审计；没有 B03 完成结果和两个最终检查点的可用身份可供核验；没有访问本地 MyLib 全文或重审其经验附录/证明；未运行本方向新代码。B02 的相关结构化字段、完成记录和指定代码足以支持以上有条件的设计与代数判断，但不支持宣布 B03 成功、面板已经通过轨迹恒等检查，或新学习已获收益。

[S0]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/docs/research/candidates/load_critical_member_generalization/NOTES.md#pro-question-2026-09-22-five-cell-identifiability-and-next-learning
[S1]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/docs/project/OPERATING_CONSTITUTION.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/docs/research/RESEARCH.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/.agents/skills/hmasd-scientific-tools/SKILL.md
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/.agents/skills/hmasd-research-engineering/SKILL.md
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/docs/research/designs/LITERATURE_RESEARCH_PLAN_20260922.md#plan-6
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/docs/research/candidates/agent_count_generalization/NOTES.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/runs/agent_count_generalization/s1_action_law_b02_probe/summary.json
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/envs/pettingzoo/scenario1.py
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/a37eed21e69adf3c6e159a7c255fd8603c1a95db/envs/pettingzoo/uav_env.py
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c/experiments/candidates/agent_count_generalization/adapter.py
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c/experiments/candidates/agent_count_generalization/configuration.py
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c/experiments/candidates/agent_count_generalization/models.py
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c/experiments/candidates/agent_count_generalization/runner.py
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/dd25f34a09ba8d0f8a62c5aacb36d9aaa56dcf0c/experiments/candidates/agent_count_generalization/action_law_b02/probe.py

MATERIAL_DISSENT: no — 以题内已采纳的唯一资格、相对符号和高度抵消修正为前提，我支持保留五格作为固定策略的服务转换研究；它不承担纯 N、在线容量适应或技能机制归因。后继五格测试用途须与完整 balanced-c 混合目标分开，B03 身份仍待真实发布；这些限制不推翻当前零 fit 设计，也不构成选择任何新增 fits。

## 2026-09-22 — Complete Pro reading, adoption and scene acceptance

Question key: `hmasd:b41fa3c38e2ef995c6c7ab013e401d103ba1f76d2efa6337333b8e9381f5ec7a`.
One Send was accepted after a confirmed pre-send composer timeout; the same key and unchanged
text were used, with no duplicate accepted Send. The deterministic observer collected COMPLETE.
The chat text was a receipt, not the answer. `deliver` verified answer commit
`04f402b8174dd1ea2e0d63f538ecfed1c099ac50`: only this file changed, only the previously empty
Answer was filled, and the question and all other bytes were preserved. The DM read the full
12,349-character answer above. The owned observation tab was closed; no operation tab remained.
The terminal wake was consumed/rearmed with its returned identifiers; no worker or question was
restarted. Private conversation/account facts remain outside Git.

The DM adopts the corrected **five-cell, zero-new-fit** study. The advice strengthens the
interpretation as conversion of fixed learned geometry/eligibility into service. It leaves the
directional H6 marginal-service conjecture testable but unsupported by any new result. The
strongest alternative remains ordinary per-UAV capacity truncation plus connected-user quality
composition; even positive D does not isolate a skill or online load-adaptation mechanism.
No optional two-fit balanced-capacity batch, heterogeneous-capability interface, extra cell,
checkpoint choice or confirmation is selected.

Additional reading commitments from Pro are adopted:

- The five cells do not span c5/10/20 at every N: N6 has c10 only. A later mixture-learning
  objective would need its own declared test distribution and weights; these are not the same
  endpoint. Missing-cell recounts from frozen SINR traces are possible only as a separately
  stated analysis; none is selected here.
- Read full-50-user eligibility E and per-UAV truncation T separately from the 20 visible user
  slots. A full UAV with e_i=c has no capacity truncation. Report both overflowing UAV-steps
  and missed eligible users with their own denominators.
- Read time-averaged native connected-user quality, including its native zero-service value;
  do not replace it by a connected-user-weighted pooled average. Newly served users can lower
  an individual UAV's quality while raising the team's current mean. For s>0, the composition
  change is m/(s+m) times (q_new-Q_old), with the s=0 case read directly.
- Retain all 80,000 steps, including repeated-capacity trajectory checks. Report per-world
  paired components and adverse outcomes, not worlds as independent training replications.
  Decompose matched-K residuals into eligibility, truncation, quality and height without a
  causal mediation or pure-N claim. D8-D4 compares different local-capacity intervals.

The Pro explicitly did not audit unavailable B03 binaries, our new implementation or all local
paper appendices. Its source-based algebra/design advice is sufficient for this narrow choice;
production identities, engineering review and the original DM's completed B03 reading remain
real prerequisites for evaluation, not inferred Pro approvals.

The DM accepts the four-file scene implementation from `matched_worlds` after reading its diff
and the independent `matched_world_review` report. The focused 9 tests passed (implementer
1.87 s; reviewer 1.04 s); compilation and whitespace checks passed. Native reward, allocation,
observation and motion code were unchanged. Coverage includes exact streams/N-prefix, repeated
reset, fixed-action capacity invariance, caps/diagnostics, reward decomposition, read-only
diagnostics and domain refusal. The checks do not yet establish actor/GRU/held-snapshot or
checkpoint/evaluator invariance. Synthetic zero-noise/threshold-tie cases were inspected rather
than separately tested. No result-bearing operation, fit or training update occurred.

### L0 — Source-bound frozen-policy evaluator, before production asset binding

The published first-fit B03 manifest now supplies its exact producer source,
`89486d32ea569728f39d6e21b53f8a7c8854e74c`, and the checkpoint/completed-summary schema is
readable. This prospectively extends the earlier primitives-only L0: implement and test the
source-complete evaluator now, while **final policy identity binding and execution remain
deferred** until the original DM publishes and reads B03. No final checkpoint digest is
available or invented. A missing/incomplete committed summary must refuse before evaluation.

The DM may restore the seven unchanged upstream source files needed for reuse:
`experiments/candidates/agent_count_generalization/{__init__,adapter,configuration,models,runner}.py`
and `action_law_b02/{__init__,probe}.py`, byte-for-byte from that B03 source. This recovers
dependencies in this isolated checkout, not the producer's training runner or unmerged history.
The shared `hmasd/agent.py` difference from B03 is only equivalent recurrent training-mask
spelling/comments (`dones_for_masks.size(0)` versus `masks_for_eval.shape[0]`); the mask shape and
values are the same and the frozen inference path is unaffected. No shared core edit is needed.

One bounded Implementer owns new `load_probe/probe.py`, the explicit entry
`scripts/run_load_critical_member_probe_b01.py`, and matching `load_probe/test_probe.py`.
It may minimally extend the new package initializers; scenes changes require a concrete defect.
DM owns this notebook, upstream dependency recovery, acceptance and RESEARCH. Preserve others'
work, edit no shared learner/environment/launcher or producer record, launch nothing and spawn
no children. Read experiments/scripts/tests AGENTS. Stop on a needed core semantic change.

Deliver the fixed five-cell comparison and summary/trace contract already declared above:

1. Strictly load only H6/clip/942201 and SET/clip/943201 B03 final45. Bind the two completed
   source summaries to this evaluator's committed Git inputs and identical working bytes;
   external checkpoint storage cannot attest its own digest. Check exact producer SHA, tag,
   arm, seed, clip training/deployment, completion, 360k train/stored transitions, 45 updates,
   96k evaluation steps and complete published final N4/6/8 configs. Verify exactly one
   checkpoint45 entry, size/digest, payload schema/keys/rollout/config and strict module plus
   normalizer restoration. Reconstruct each N-specific source config without behavioral
   drift. Production CLI has no fixture or arbitrary-policy bypass.
2. Native-admission guard before scientific effects; fixed CPU FP32/four Torch threads,
   16 worlds, 500 steps, both policies/all five cells. Fresh or fully reset episode runtimes
   preserve source configuration and k10 information clocks. Use stream 3 addressed
   `[260922,6,world_id,3,N]` for runtime randomness, shared across capacities and arms.
   Preserve source num_envs=16 in configuration; sequential single-world inference may use
   one active row if tested through the actual agent path. Count only actual environment
   transitions. Do not silently exchange the full repeated-capacity evaluation for recounting.
3. Execute a separately owned coordinate-clipped deterministic action. Preserve raw actions
   and log probabilities; retain observations, encoded state, float64 geometry, runtime-state
   fingerprints and native service/SINR traces with documented pre/post-transition indexing.
   Assert same-policy/same-N paired capacities have exactly equal actions, observations,
   state, geometry and relevant recurrent/skill/snapshot state through k10 boundaries.
   Hash tensor/array values canonically, not storage addresses. Height must cancel.
4. Record model/normalizer digests before/after, zero optimizer/training/update counts,
   checkpoint digest stability, and diagnostic RNG noninterference. Full-50-user e_i,
   occupancy/full/overflow, unserved eligible/ineligible, visibility truncation, connected
   quality sums/means and native coverage/height/J stay analyst outputs, never actor inputs.
   Record the conditional unique-eligibility/S(c) domain and actual equality; a violation
   quarantines its dependent interpretation. Do not adjust SINR thresholds or tolerances.
5. Summary retains each arm/cell/world, all component means, G, D_N, each arm's absolute
   capacity effect, matched-K cross-N residual and same-c10 secondary contrast. Pair by world;
   show all world differences and descriptive spread/adverse counts, without a training-level
   significance claim or automatic selection. Assert component decompositions on paired data.
   Atomic summary plus checksummed traces retain partial exact counts after technical failure.
   Count each successful environment step immediately, before fallible diagnostics; retain
   completed episodes and partial current work. Never overwrite an existing attempt root.
   Report elapsed time and process peak RSS with scope and honest missing telemetry.

Tests use small synthetic source fixtures only under pytest-owned scratch. Cover actual H6
and SET inference across k10 (at least 12 steps), N4/6/8, same-world/capacity equality and
capacity-dependent service, strict source/payload/digest/config rejection, no learning or
normalizer movement, native-admission-first refusal, complete and injected-failure counts,
output/decomposition correctness and fixture/production separation. These are technical checks,
not policy-performance evidence. Reuse accepted scene tests; independent Reviewer examines the
new checkpoint/runtime/evaluation/entry code before DM acceptance. The production plan remains
0 fits / 80k eval; no operation is accepted by this implementation task.

## 2026-09-22 — Frozen evaluator accepted; production assets remain unavailable

The DM accepts `load_probe/probe.py`, `scripts/run_load_critical_member_probe_b01.py`, its
focused tests and the minimal package initializer change after reading the implementation,
check outputs and independent `matched_world_review` re-review. The seven recovered producer
dependency files remain byte-identical to source `89486d32ea569728f39d6e21b53f8a7c8854e74c`.
No shared learner/environment/launcher was changed. The production entry has no fixture or
arbitrary-policy option and refuses missing, incomplete or mismatched committed source evidence.

The initial review found two material defects before any result launch: the multi-world loop
would have reset the first bound physical world under different runtime seeds, and failure
accounting would have omitted earlier completed worlds or misreported a completed native
episode. Both were repaired and independently re-reviewed. Each world now gets its own bound
native scene; user and UAV float64 geometry is retained in traces. Completion counters follow
actual world/terminal boundaries, independently of diagnostic success, and the failed active
cell retains its failure state. The DM also required comparison with the producer's final
model/normalizer digest, source-compatible pre-import BLAS/OpenMP settings of 1 with four
Torch threads, and untruncated domain-failure reasons. These are correctness repairs, not
scientific observations or evidence against the capacity conjecture.

Current focused suite: **23 passed**, implementer 6.19 s, independent reviewer 5.52 s. The DM
then narrowed temporary-fixture Git operations to explicit paths and reran the suite:
**23 passed in 5.90 s**. Compilation and whitespace checks passed; pytest scratch was cleaned.
Per full suite invocation, evaluator fixtures execute **167 native evaluation transitions**:
120 through actual H6/SET paths over all ten package/cell episodes at horizon 12; 40 over a
second, two-world/all-cell geometry check; and 7 in three injected-failure cases. Source/config,
module/digest, admission-order, overwrite and reduction checks are included. These are small
synthetic untrained checkpoints, not B03 policy results. The tests cover k10, distinct/matched
worlds, same-N capacity trajectory/runtime equality, zero optimizer/model/normalizer movement,
native service differences and partial outputs. Existing singleton `torch.std()` warnings are
debug-log statistics only; their values do not enter logits, actions or recurrent state.

Limits remain explicit: production B03 binaries, the full 500-step horizon, full-size network
execution and destination-node performance have not been validated by these fixtures. Keeping
source num_envs=16 with one active inference row preserves the tested policy path and clocks;
it does not claim bitwise equivalence to the producer's sixteen-row batched numerical execution.
No result has been generated, no training fit or optimizer update has been spent here, and the
proposed **0-fit / 80,000-step / 160-episode** panel has not been admitted.

At the publication refresh, main `9a1c88298` contains the producer's complete H6/raw reading
and the start of SET/clip. The published completed raw summary confirms the expected final
schema/counts and producer SHA; it is not an eligible policy for our clip-only panel. SET/clip
is still an incomplete published training snapshot and H6/clip is not yet published as started.
This is a reading of committed dependency evidence, not inspection of another DM's live process.
It supplies no completed pair or four-cell B03 conclusion and changes no scientific prediction.

**Re-entry condition:** consume the original DM's published completed B03 reading and fixed
next-action contract, then bind both clip/final45 summaries and binary identities into this
direction's committed source, verify available checkpoint bytes, and admit the already specified
full panel on a suitable configured node. Do not substitute the completed raw checkpoint, an
intermediate endpoint, a duplicate training producer or an extra capacity-training batch.
There is no accepted result handle or open Pro question for this direction to observe now.
No App message, new monitoring loop or new fit is created to bridge the external asset wait.


## 2026-09-23 — Owner-assigned direct DM continuation and original B03 asset binding

Owner requested this session to advance one direction and create one Astra/max independent
DM after reclaiming abandoned worktrees. This session directly adopts the existing
`load_critical_member_generalization` responsibility: task
`01a0cd93-9107-7701-a7e5-84fb071ea8f7`, host `local`, authoring checkout
`/home/fires/.codex/worktrees/load-capacity-sept23/hmasd-wsl`, branch
`codex/load-capacity-sept23`. The former task is archived, not running, and its authoring
checkout no longer exists. Native task history and the complete published notebook agree:
its Pro answer was fully collected/adopted, evaluator accepted, and no load-evaluation
operation was admitted. There is no accepted load worker or uncertain Send to restart.
Original identities and earlier entries remain historical evidence. Claude FSD/G33 remain
paused/frozen; the original count DM retains its work and checkout.

Read the complete existing question, Pro answer, adoption and evaluator acceptance. The
same five cells, world streams, 500-step horizon, 16 worlds, two fixed policies, native
component interpretation and **0 fits / 80,000 evaluation team steps / 160 episodes** remain
selected. This is the original fixed-policy service-conversion question, not an online
capacity-adaptation, pure-N, skill-mechanism or new-training claim. The prior complete Pro
advice still covers this unchanged choice; no repeat consultation or optional training is
selected. Same-N capacity trajectories must agree; height cancels in the interaction, and
coverage/quality composition may give either relative sign.

Current published main at continuation is d2daabdf1689209c87d856a2f97b50115ba57f1c. Relevant shared topics 3 and 6 now
include the original producer's complete B03 reading and the later entropy/initial-policy
counterevidence. B03's common clip-trained endpoint H6-minus-SET J is
+.064857891 / +.095823637 / +.161067197 for N4/6/8, unseen mean +.112962544.
That bounded single-block package advantage does not certify a sufficiently tuned ordinary
baseline or a skill mechanism. Later B04/B05 opposite entropy responses and B08's initial
policy rival constrain attribution but do not change the original B03 checkpoint contract.
We deliberately retain that preselected pair, rather than replace it after seeing B07/B08.
The next useful observation remains the complete capacity response and its eligibility,
local truncation and quality decomposition, including adverse/flat results.

The producer has now published both exact completed clip summaries, each with 360k stored
training steps, 45 updates and 96k evaluation steps. Required checkpoint45 identities are:

- H6 `s1_action_law_b03_h6_clip_s942201`: 23,073,626 bytes,
  `98d908e4c9d1c33e59707b7da288b0c019f293eced1a99a461f020d1ae069343`.
- SET `s1_action_law_b03_set_clip_s943201`: 20,968,771 bytes,
  `03f4f070e30b34fb61cd45820f1579ebde185c9417468689bd0c2e7ef60c0a3b`.

These are declared identities, not yet a statement that this task verified the binary bytes.
They come from producer source `89486d32ea569728f39d6e21b53f8a7c8854e74c` and remain
recoverable on the configured wsl_4070 node. Bind the original published summary bytes to
committed evaluator inputs and verify those two binaries before original-panel admission.

### L0 — Restore accepted evaluator and bind published original assets

Own only the direction evaluator/entry/tests, the seven byte-identical producer inference
dependencies named in the prior L0, and the two source-summary input paths. Restore accepted
code from `7524026cebe8d9af7461f670db3edb3098e979c2` / its published direction branch;
no learner, environment, metric, sampling, horizon or policy change is selected. The shared
`hmasd`, `envs`, `configs`, launch and admission paths are byte-unchanged between that accepted
revision and current main. Reuse the existing independent review and 23 technical checks;
verify restored bytes and production binary/config bindings. Any real executable defect
requires a separate documented repair and independent review before use. Stage/publish exact
inputs, then use the original five-cell entry with native admission on wsl_4070 and arm the
current session's deterministic observer. Do not duplicate training or consume another DM's
operation. No result exists at this entry.


### 2026-09-23 — Exact production inputs restored and verified

The seven accepted evaluator/entry/test files were restored byte-identically from
`7524026cebe8d9af7461f670db3edb3098e979c2`; the seven inference dependencies were restored
byte-identically from producer SHA `89486d32ea569728f39d6e21b53f8a7c8854e74c`.
No scientific executable byte was changed. The two full final summaries are copied exactly
from published count-direction commit `e9a106f6841a765d474afb6dc41e5dd508ddcae0` and verified against
the identical completed summaries already published in current main. Their SHA-256 values are
H6 `55a994c81f49a9b97b52efa4ddaea82579e1068ea3a7ddbd11c8b7645bf88921` and
SET `2621fc884d2d6a9ea909ee4f483b4df1c2d9d6f8767826ef730b952a360422e3`.

Read-only inspection on configured host `LAPTOP-U9TDKC8A` independently verified both
complete summary hashes and the previously declared checkpoint45 sizes/digests at
`/home/wu/hmasd-worktrees/agent-count-action-law-20260922-b03/runs/agent_count_generalization/`.
This closes the old binary-availability dependency without creating a new producer.
The original asset files remain unchanged. Preserve the accepted 23-check engineering
coverage and its full-size/full-horizon limits; production payload/config verification will run inside
the admitted evaluator, before any fixed-panel environment or policy effects. No source, summary,
checkpoint, cell or exposure substitution is selected.


### 2026-09-23 — Original B01 admitted; current-session observation adopted

The original five-cell contract is now accepted. The exact restored source is published
as `c770220d3abc4e32a9e80347dea87bdea88080e8`; source remains fixed on the configured
executing node. [Native manifest](../../../../runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/launch-manifest.json) and
[actual-node admission](../../../../runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/admission-preflight.json) retain the
operation identity, interpreter, source, native process identities and invocation.
No new fit, supplementary panel, source-policy substitution or relaunch was introduced.

Both original completed-summary/binary/payload/config bindings passed inside the admitted
evaluator before policy/environment effects. The collected [progress summary](../../../../runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/summary.json)
is an in-flight snapshot: 16,000 evaluation team steps,
32 episodes and 2 of 10 policy-by-cell evaluations complete,
0 fits/train steps/updates/optimizer calls, no reported failure. The fixed target remains
80,000 steps and 160 episodes. This snapshot is not a complete five-cell result or a new
scientific conclusion. Full trajectories, capacity-invariance checks and all adverse worlds
will be collected and read at the original endpoint.

The current task's deterministic observer has adopted this same accepted operation: first
read reports consistent native records and both runner/supervisor running, generation 1,
30-second read-only probes and a 1,500-second observation window. It wakes only this assigning
session on terminal/error/checkpoint. A checkpoint means read/rearm, not new execution.
The independent complementary-skill DM has its own task and operation; this direction
requires no cross-task reporting loop or further owner approval.


## 2026-09-23 — B01 complete: useful package levels, mixed capacity response, route closure

### Scientific acceptance and recoverable evidence

Read the terminal native observation and [OS exit witness](../../../../runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/process-exit.json),
then collected and SHA-256 checked **all 181 files, 246,723,301 bytes** against the
original node. The [complete summary](../../../../runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/summary.json) has SHA-256
`f727a4ee005c1893e0041ea8dd8f2f1160d98a47f2014d396b75b8a0e5cb7bf8`.
Source remains `c770220d3abc4e32a9e80347dea87bdea88080e8`; producer/checkpoint identities
are exactly those bound before admission. Every planned cell, world and 500-step episode
completed: **0 fits, 80,000 evaluation team steps, 160 episodes, 0 training steps/updates/
optimizer calls**. Exit zero alone was not acceptance.

Read and independently checked all 160 saved NPZ traces, their recorded sizes/hashes, array
shapes/dtypes/finiteness, exact declared user streams and UAV prefixes, action clipping,
full-SINR eligibility, actual connections, `S=Σ min(e_i,c)=E−T`, quality composition,
scalar-to-native reward scaling and summary reductions. All 80,000 transitions passed;
no eligibility-identity quarantine occurred. All 64 same-policy/same-N paired worlds
were exactly equal in actions/log-probabilities, observations, encoded state, positions,
SINR and recurrent/skill-clock fingerprints across capacity, including refresh boundaries.
Height penalties were exactly equal. Model/normalizer and input checkpoint digests remained
unchanged in every cell. This is frozen-policy evidence, not new learning or online adaptation.

The 19 runner JSON files and two logs are published with this notebook. All 160 compressed
traces remain recoverable with the per-world path, byte count and SHA-256 in the summary, at
`hmasd-wsl-node:/home/wu/hmasd-worktrees/load-capacity-b01-20260923/runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/`
and the independently verified local copy
`/home/fires/.codex/worktrees/load-capacity-sept23/hmasd-wsl/runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923/`.
NPZ bytes are retained outside Git; neither copy nor its source/output worktree is reclaimed.
The terminal wake was consumed with its exact generation/wake/event IDs; observation is now
generation 2 with no remaining running job. No worker was restarted and no question resent.

### Absolute service and package comparison

J is native mean team reward, `N × scalar_return / 500`. Every mean below uses the same
16 declared paired worlds. The independent learning unit remains one original trained
instance per arm; there is no training-population confidence or mechanism attribution.

| N | c | K | H6 J | SET J | H6−SET J | Worst world gap | Negative J worlds | Extra H6 served users/step |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 4 | 10 | 40 | 0.539891827 | 0.481791206 | +0.058100620 | -0.027369480 | 1/16 | +2.916125 |
| 4 | 20 | 80 | 0.591848927 | 0.554125053 | +0.037723875 | -0.029597256 | 3/16 | +1.367125 |
| 8 | 5 | 40 | 0.362293715 | 0.214267842 | +0.148025873 | +0.013004914 | 0/16 | +8.281125 |
| 8 | 10 | 80 | 0.441925250 | 0.270417880 | +0.171507370 | +0.040798893 | 0/16 | +9.978875 |
| 6 | 10 | 60 | 0.532320598 | 0.430265127 | +0.102055471 | +0.013401407 | 0/16 | +5.628625 |

H6's mean J and coverage advantage survives all five declared conditions, while absolute
service remains condition-dependent. Preserve the four adverse J comparisons: N4/c10 world 1
(−.027369480); N4/c20 worlds 1, 3 and 13 (−.020677854, −.004430281, −.029597256).
Coverage alone is adverse in N4/c10 world 1; N4/c20 worlds 1, 3, 4, 13, 15; and N8/c5
world 7 (−.584 served users/step despite J +.013004914). A positive mean or J level does
not erase these different component outcomes. At common c10, both packages' absolute mean
J falls as N rises even though H6's relative gap grows.

### Capacity response: the two-N conjecture did not hold

| Arm | Same-N change | Extra served users/step | ΔJ | Δquality | Δheight | Negative ΔJ worlds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| H6 | N4, c10→20 | 4.112250 | +0.051957101 | -0.018714664 | 0 | 0/16 |
| H6 | N8, c5→10 | 6.248375 | +0.079631535 | -0.026152382 | 0 | 0/16 |
| SET | N4, c10→20 | 5.661250 | +0.072333846 | -0.023078846 | 0 | 0/16 |
| SET | N8, c5→10 | 4.550625 | +0.056150038 | -0.025195708 | 0 | 0/16 |

All 64 arm×world absolute capacity changes improve J and service count; each of the four
mean quality changes is negative. Capacity therefore has an actual favorable native effect
on these paths despite a quality-composition cost. It is not irrelevant.

The prewritten conjecture required H6 to recover more users **and** more J at both N.
At N4 it fails already at the intermediate quantity: H6 gains 1.549 fewer users/step than
SET. D4 is **−.020376745**, negative in 13/16 worlds (positive worlds 1, 6, 11), with
range [−.066633344, +.008873451]. Its weighted decomposition is
`−.021686000 coverage + .001309255 quality + 0 height`. Quality softens the adverse
relative response; it does not cause a successful intermediate prediction to fail.
At N8 H6 gains 1.69775 more users/step, and D8 is **+.023481498**, positive in all 16
worlds, range [+.000771698, +.049642616], decomposed as
`+.023768500 coverage − .000287002 quality + 0 height`.
This is the prospectively covered mixed-N branch, not a uniform overload advantage,
a universal capacity derivative or evidence that either actor senses hidden c.

### Eligibility, local truncation and matched-K residuals

E and T use all 50 users. Each table entry is a time/world mean count; a full UAV with
e_i=c need not truncate anyone. Overflow rates use UAV-steps, while missed-eligible rates
use eligible user-steps. Visible-user truncation has its own eligible-entry denominator.

| Arm | N | c | E eligible | T eligible but unserved | SINR-ineligible | Overflow UAV-step rate | Missed eligible-user rate | Visible eligible-entry truncation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H6 | 4 | 10 | 39.171875 | 4.138375 | 10.828125 | 0.405531 | 0.105647 | 0.000667 |
| H6 | 4 | 20 | 39.171875 | 0.026125 | 10.828125 | 0.001125 | 0.000667 | 0.000667 |
| H6 | 8 | 5 | 29.654000 | 6.645250 | 20.346000 | 0.310578 | 0.224093 | 0.000000 |
| H6 | 8 | 10 | 29.654000 | 0.396875 | 20.346000 | 0.022781 | 0.013384 | 0.000000 |
| H6 | 6 | 10 | 35.710625 | 0.855250 | 14.289375 | 0.054938 | 0.023949 | 0.000000 |
| SET | 4 | 10 | 37.858375 | 5.741000 | 12.141625 | 0.395062 | 0.151644 | 0.002107 |
| SET | 4 | 20 | 37.858375 | 0.079750 | 12.141625 | 0.008000 | 0.002107 | 0.002107 |
| SET | 8 | 5 | 20.001750 | 5.274125 | 29.998250 | 0.178813 | 0.263683 | 0.000075 |
| SET | 8 | 10 | 20.001750 | 0.723500 | 29.998250 | 0.036797 | 0.036172 | 0.000075 |
| SET | 6 | 10 | 30.673625 | 1.446875 | 19.326375 | 0.091771 | 0.047170 | 0.000000 |

At N4, H6 starts with less absolute truncation and has less service to recover over
c10→20; at N8/c5 it has more absolute truncation but a lower truncated fraction of its
larger eligible population. The added service depends on the tails of e_i at different
local cap intervals. This ordinary geometry/eligibility/truncation explanation survives;
no new representation defect or skill mechanism is required to explain the sign reversal.
At high capacity the remaining T is small compared with SINR-ineligible counts. Those
counts bound capacity-only relief along the observed geometry, not attainable learning
headroom, physical optimality or a limit on other policies.

Let A_N=E_H6−E_SET and B_NK=T_H6−T_SET. The matched-K residual of package gaps is
`(.7/50)ΔA − (.7/50)ΔB + .3ΔQ − ΔP`, with Δ taken from N4 to N8.

| K | Eligibility contribution | Truncation contribution | Quality contribution | Height contribution | G(8,K)−G(4,K) | Negative worlds |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 40 | +.116742500 | −.041632500 | +.001940569 | +.012874683 | +.089925252 | 2/16 |
| 80 | +.116742500 | +.003822000 | +.000344313 | +.012874683 | +.133783496 | 0/16 |

K40's adverse residual worlds are 7 and 12. This is exact outcome accounting, not causal
mediation or a pure-N effect: c, local capacity partition, geometry and interference
change with N. Same-c10 gap differences are +.043954851 (N6−N4), +.069451899 (N8−N6)
and +.113406750 (N8−N4); these also do not isolate abstract count invariance. N6 has no
capacity pair, and this panel does not cover the full three-capacity mixture at each N.

### Working update, Pro reuse and decision

Strengthened: useful mean native service levels for this original H6 package on all five
conditions; the actual capacity-conversion chain and same-N trajectory invariance; the
need to retain eligibility and truncation separately. Weakened: the prewritten claim
that H6 extracts a larger marginal capacity benefit at both N. Untouched/unresolved:
training-population ranking, ordinary-baseline adequacy, skill causality, unseen online
capacity adaptation, heterogeneous capabilities and key-member generalization. No failed
intermediate prediction is rescued by a proxy improvement or by height in D_N.

Checked current published main `1e5a411630a2a603fcc8659886332ea5c208e437` at this decision. Shared topic 3's B03–B08
evidence matters: clipping alone did not selectively repair SET, entropy responses
reversed across training instances, and both packages actually learned useful service
despite an initial H6 advantage. These prevent attributing this fixed B03 pair's gap to
a skill mechanism, prescribing an initialization/entropy repair, or borrowing a causal
initialization share from another pair. No new result from another DM is assumed.

Reuse the **complete, delivered prior Pro answer** (answer commit
`04f402b8174dd1ea2e0d63f538ecfed1c099ac50`), specifically its sections 6–7: opposite
N signs retain local threshold/geometry effects, and a finished frozen-conversion study
may close when a further useful learning decision is not justified. Those conditions
remain applicable; this decision changes no question, comparator, endpoint or scope.
Bounded ResearchCritic `load_b01_interpretation_critic` independently challenged this
reading and the investment choice, with no material dissent. Its advice supports, but
does not replace, that already applicable Pro consultation and the DM's judgment.

**Decision: complete and close the current frozen service-conversion route; archive this
direction's present investment, preserving its positive and adverse evidence.** No further
fit, missing-cell recount, confirmation, Pro operation or result run is selected or pending.
The native pipeline is feasible now; the stop is scientific information value, not a
technical block, missing asset, resource refusal or request for owner approval.

The optional two balanced-c H6/SET fits would supply another package comparison without
identifying the benefit of changing the training capacity distribution. Merely observing
a capacity response does not identify a target mixture or a modifiable learning prediction
worth that cost. Heterogeneous capacities would change the information/interface question
and are not an automatic successor. If a concrete use distribution later motivates
learning a geometric compromise, a new prospective comparison could first test an unchanged
ordinary SET recipe under matched fixed versus mixture training, predicting both retained
eligibility/better truncation tradeoffs and improved target-weighted J. That is unselected,
not a queued reserve or an admission condition. This closure does not deny that such
learning or key-member questions can have value under a different grounded comparison.

### Actual cost and technical limits

The runner measured **354.661234 s command wall (5.911021 min)**, including its import/load/
init, inference, simulation, diagnostics and writes; the internal probe body was 352.870600 s.
Scientific-process CPU user/system were 1435.264696 / 1.895802 s with four Torch threads;
peak RUSAGE_SELF RSS was **784,072 KiB (765.695 MiB)**. Git/network preparation, collection,
DM reading and peak scratch were not covered by that wall/RSS measurement and are not zero.
The read-only local trace audit took 3.637053 s and added no environment steps or fits.

Both recorded stderr warnings concern `std()` on singleton logits in existing debug
statistics at `hmasd/networks.py:600,674`; source inspection shows that statistic is only
logged. The native actions/log-probabilities and all scientific numeric arrays audited
above were finite. The warnings remain in the published log; no source repair or rerun
was made. This is one pair of fixed learned policies on the declared simulator worlds,
not replicated learning, broad transfer, physical deployment evidence or a speed comparison.


## 2026-09-23 — Owner assigns scientific project management and continued research selection

The owner now asks this task to manage the project scientifically and asks DMs to review the
whole project after failures, propose broader useful work and continue with greater autonomy.
The prior B01 evidence and closure of the frozen capacity-conversion recipe remain intact.
That closure does not end this task's responsibility to choose the next valuable research.
All B01 operations and its Pro answer were already collected/read; no worker or Send is reopened.
The original source checkout and ignored raw trajectories remain preserved. This task now acts
as Root from the main-based project-management checkout recorded in RESEARCH.

B01's large N8 eligibility difference and small remaining truncation motivate a new learning
question; they do not establish learnable headroom. Count B08 says both packages learned useful
service, and B10 weakens continuous reassignment as a necessary explanation of the mean benefit
while preserving large local losses. The proposed next investment compares ordinary SET trained
at N6 and N8, rather than extending capacity-only diagnostics. It is a new prospective candidate,
not an accepted batch or a claimed repair; cost currently proposed is two 360k fits plus 64k final
evaluation steps. A whole-project Pro question weighs this against mixed-count training, S7
service/risk work and information from the ongoing complementary-skill comparison.

See [current project review](../../RESEARCH.md#portfolio-review-2026-09-23-scientific-management-and-next-learning-investment).
The current owner delegation permits choosing and continuing useful work after this advice,
without treating a recipe failure as the end of research or requesting another direction approval.


## 2026-09-25 — Owner-requested publication and source checkout retirement

The owner requested consolidation of useful results into main and retirement of unused
worktrees. B01 remains closed; this is evidence preservation, not another evaluation.
The load-capacity source checkout was archived through the Codex worktree lifecycle,
with its source commit `bc2134f4df523dcb68a52ea4085a3493f18b3d8f` and branch
`codex/load-capacity-sept23` retained. The dedicated runner, candidate implementation
and tests are being consolidated into main without changing their source blobs.

Before archival, all 160 ignored NPZ trajectories (244,283,369 bytes) were individually
matched by byte size and SHA-256 against the original executing-node copy at
`hmasd-wsl-node:/home/wu/hmasd-worktrees/load-capacity-b01-20260923/runs/load_critical_member_generalization/s1_load_critical_member_b01_20260923`.
The sorted local hash-list digest was
`d88c0f8576edaecad1c0e04879da198b1e6a461b766e9dcae7a5318d1a0bafad`.
The node copy remains the raw-data location; ignored trajectories are not part of the
Codex archive snapshot. Compact runner results and this notebook remain in main.
No live process depended on the retired checkout. No fit, Send, relaunch or scientific
claim change occurred during reclamation.
