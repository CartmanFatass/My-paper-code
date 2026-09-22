# Joint duration and skill learning

## 2026-09-21 — Owner-selected independent study

Owner requested four concurrent directions, with the assigning task itself owning one and
three newly created independent DM tasks. This task owns this direction end to end.
After initialization the DMs do not communicate with one another. Evidence publication and
shared-background use follow the existing constitution; no Root acknowledgment is needed.
Owner's compute order: prefer configured remote WSL `wsl_4070`, then local computation only
with a recorded availability, resource or suitability reason. Preserve accepted handles and
use actual-node admission; four research tasks do not imply four simultaneous heavy fits.

### Question and inherited explanation

Can additional duration choices improve native Scenario1 service under finite learning,
and does an ordinary autoregressive duration distribution improve on a fully informed
factored duration distribution? All arms jointly learn high-level skills and low-level control.
This is the previously proposed new comparison, now selected by the owner's instruction.
It does not reopen Claude's paused `flexible_skill_duration` task, take over its notebook,
or continue the stopped high-level-label-credit/threshold/renewal rescue package.

The [published background at 455837f60](https://github.com/CartmanFatass/My-paper-code/blob/455837f60127cc31fbc5d802e19dfd79d0a2bfec/docs/research/RESEARCH.md)
sections 3–6 changes the design: use a competent fixed-clock arm, give both duration arms
the same lawful commitments/history/team latent/current joint skills, preserve closed-loop
primitive control, and compare native return and actual cost. Expressivity inclusion does
not guarantee strict improvement, and action-space size is not a sample-complexity ratio.
The [complete programme advice and decision](../../archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-whole-project-evidence-led-research-plan)
and [concept formation](../../archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation)
cover this initial question; the DM must check applicability before reusing advice for a bound design.

FSD B13/B14 did not reverse the stopped package's judgment. B12's particular label-count
regression is not a bound on new joint skill learning. UCOPE's local suffix effects did not
establish useful complete return. These raise the cost of speculative rescue and are retained
as contrary evidence, not reset by the new directory. Sources: [FSD notebook](../flexible_skill_duration/NOTES.md)
and the [current UCOPE standing](../../RESEARCH.md#archived-investment-only-not-scientifically-disproved).

### First comparison and discriminating observations

- Same Scenario1 task and full HMASD: fixed k; informed factored durations; ordinary AR
  durations after the same joint skill-selection family. One difference between variable
  arms is conditioning on earlier sampled durations in the same eligible-member event.
- Share duration menu, cap, lawful information, ordinary commitment/history critic and
  update principles. Factored policies may coordinate deterministically and through latent
  variables. Single-member events provide no extra within-event joint sampling relation.
- Read full native J, prespecified learning-curve positions, native service components,
  actual decisions/updates, joint-event exposure, effective durations and compute. Low-level
  chunk length, nominal clock and cap truncation must not be silently conflated.
- An AR gain only over factored, while both lose to fixed k, does not justify extra
  complexity. Useful variable arms without a reliable AR increment favor the simpler arm.
  Duration correlation, entropy or local credit changes alone do not establish service gain.

### Initial work and scope

Map the active S1 training/evaluation path and existing duration sampling, replay and credit
semantics; then bind a minimal runnable comparison, scientific cost and meaningful endpoint.
Do not add a new encoder, predictive auxiliary, clock curriculum, new reward or fictional
fault/backhaul mechanism. Existing code/evidence is reusable; another active DM's new result
or module is not a dependency. Shared correctness repairs, when necessary, apply to all arms.

The DM owns this notebook, `experiments/candidates/joint_duration_skill_learning/`, its tests
and `runs/joint_duration_skill_learning/`; shared executable edits need existing independent
review. Declare exact arms, seeds, horizon, evaluation and planned fits before any result run.
Initialization starts **0 fits**, accepts no experiment or Pro Send, and is not an empirical
result. Continue through design, implementation, evidence reading and a supported next
investment/stop judgment using the existing methods; no automatic rescue sequence.

## 2026-09-21 — Direct DM initialization and the first implementation distinction

This task `01a0c348-428c-7f01-bd8b-121d69543032`, host `local`, now owns only this direction.
Its isolated authoring checkout is `/home/fires/.codex/worktrees/joint-duration-learning/hmasd-wsl`,
branch `codex/joint-duration-learning-20260921`. The three other independent DM tasks have
their own recorded addresses and workspaces; initialization is complete and no further
cross-DM communication or monitoring is planned. Current runtime context for all four DMs
was read and verified as `gpt-6-astra` / `max` after correcting the three new tasks' initial
default medium setting. No experiment or Pro operation was restarted to change effort.

Refreshed published main `c91af2e5a` and read the unchanged relevant shared background and
the complete programme Pro Answer. The full-joint-learning question, fixed/factored/AR
comparison, strong-information requirement and outcome branches remain applicable; this
advice is reused for the question, not treated as a validated executable design. FSD's
03:43/03:52 B14 interpretation and rest entry were read directly: the proposed reversal
did not occur, the old label-credit route stopped, and no accepted FSD operation is inherited.

Read-only source inspection found a substantive implementation distinction. The existing
duration head is in `hmasd/ha_ctse.py` and requires the horizon/process/discrete-lifetime
path. The original full-HMASD S1 recipes use `SkillCoordinator` with those switches off;
`hmasd/baselines.py::_enable_ha_ctse` also changes the discovery/process objective. Therefore
turning on that family is not the promised single duration-parameterization intervention.
The HA-CTSE AR skill/editor path also emits duration logits in parallel, so its AR name
does not implement conditional duration sampling. The next binding must preserve the full
HMASD actor/discovery path and explicitly add the missing duration context/sampling and
matching reevaluation. A bounded Scout is checking the separate non-HA D2 scheduling path
before selecting the smallest implementation. This is a code fact, not a performance result.

The configured remote responded as `LAPTOP-U9TDKC8A`; the read-only observation showed
about 14 GiB available RAM and current canonical research control at `c91af2e5a`.
Use `wsl_4070` first for result computation and acquire fresh actual-node admission at launch.
No scientific run, new Pro Send or fit has yet been accepted; started fits remain 0.

## 2026-09-21 — D2 scheduling map and the decision needing advice

The bounded D2 follow-up resolves the distinction left open above. D1280/D0 is not simply
the ordinary off collector: `run_flexible_skill_duration_e0.py::_make_config("D0", ...)`
uses D2 with both logit-gap costs infinite, individual/team caps 10, age feature off; the
1280 variant changes coordinator batch size. `HMASDAgent::_batched_assign_skills_d2`
checks primitive-step ages, resamples the team at its cap and forces all members then;
between team decisions it can resample a subset. `SkillCoordinator::assign_partial_batch`
decodes kept members first and eligible members next in canonical order, forcing held tokens.
`evaluate_training_batch_ordered` replays that order and the stored eligibility masks.

Unlike the HA-CTSE lifetime path, D2 already maintains separate open agent and team credit
segments. Resampling, terminal closure and rollout flush have explicit elapsed-step semantics;
rewards are discounted inside a segment and the next value by gamma to its elapsed steps.
`update()` still performs original low-level/discoverer and discriminator learning. These
are reusable implementation assets, not evidence that a new duration head is useful.

The material open choice is how to add the common commitment context and the post-skill
duration policy without introducing an action-dependent baseline or miscrediting an AR
factor's influence on later sampled durations. Existing programme advice covers the three
learning packages but does not bind that actual loss/critic choice. A focused Pro consultation
will resolve this scientific design boundary before committing an implementation/batch.

## Pro question 2026-09-21 duration-sampling-and-credit

Conversation: new (WSL/Jev; private address remains in local operation state).

### Question

Choose the smallest scientifically sound full-HMASD comparison of fixed k, informed
factored durations and ordinary autoregressive durations on the existing Scenario1 path.
The immediate decision is the **common decision state, critic and policy-gradient target**
for a duration sampler added after joint skill selection. Is extending the existing D2
agent/team segment path adequate, or should the three arms share a different ordinary
event-based return/critic construction? Explain a concrete recommended construction and
the consequential alternative; do not invent another research direction or rescue module.

This direction is now explicitly selected in the owner's four-task assignment. Each DM
works independently after initialization. This task owns the new jointly trained duration
comparison; it does not restart Claude/FSD, its old credit rescue, or G33. Current model is
Astra max; result computation prefers remote WSL `wsl_4070`, then local only for a recorded
availability/resource/suitability reason. Advice is not an empirical result or approval.

### Standing and inherited evidence

The complete programme Answer/Decision in the dated RESEARCH archive already recommends
fixed/informed-factored/ordinary-AR duration learning and says to retain ordinary methods
when they absorb the gain. It does not validate a pre-existing duration implementation.
Background sections 3–6 establish that legal common context and a team latent can already
coordinate factored outputs; deterministic coordination is not exclusive to AR. When one
member is eligible there is no extra within-event cross-member sampling relation. More
duration choices do not guarantee better finite learning or imply a sample-complexity ratio.

FSD B13/B14 left the old high-level-label-credit package stopped. B14's primary checkpoint
effects were about +.019, +.016, -.019; they did not reverse the predeclared investment
judgment. B12's label-count regression is not a bound on new state-conditional joint skill
learning. UCOPE's real local suffix effects did not establish useful complete return.
No new positive result overturns those findings. All new arms here must jointly learn
skills and primitive control, and compete with a competent newly trained fixed-clock arm.

### Concrete current implementation facts

- The S1 reference uses 6 UAVs and 50 users, primitive closed-loop actor actions and the
  original hierarchy/discovery pipeline. D0 has k=10, both D2 logit-gap costs infinite and
  both individual/team caps 10; D1280 selects coordinator batch size 1280. It is not HA-CTSE.
- D2 has held team/joint skills, agent/team ages, partial resampling masks and stored decode
  order. Kept skill tokens precede eligible tokens; the same ordered law is reevaluated.
- D2 stores separate agent segments and a team segment. It accumulates discounted primitive
  rewards, closes at relevant resampling/terminal/rollout events and uses gamma^elapsed in
  bootstrap/GAE. Original actor and discriminator learning continues.
- The only current duration head is in HA-CTSE. Enabling that family also changes discovery
  and process objectives. Its AR label applies to skill/edit sampling; durations are emitted
  in parallel, without preceding sampled durations or held remaining-time context. Simply
  toggling it does not implement the requested comparison.
- Config k is also used for low-level recurrent training chunks. Execution duration must
  have its own state and must not silently change the low-level training chunk length.

### Proposed bounded design, open to material correction

Start with one fresh implementation of the full D2 learning family shared by all three arms,
preserving primitive actor/discovery training. At a team event sample the team latent and
all skills; at a member event hold the team latent and noneligible skills, sample eligible
skills using the same ordinary ordered coordinator. Only after the whole current joint
skill vector is defined do the eligible members sample durations.

Both duration arms receive identical lawful current central/joint observations already used
by the high-level policy, team latent, current joint skills, eligibility, held commitment
ages/deadlines and time to the common team cap. No new privileged observation or predictive
module is introduced. The factored arm samples durations independently conditional on that
full common context; AR additionally sees earlier sampled durations in canonical eligible
order. Store the actual order, eligibility, context and sampled choices for PPO reevaluation.

A concrete starting option is team cap 10, fixed arm k=10, and durations in primitive units
1..10, masked to the remaining time before the team cap. This keeps a fixed-10 policy
reachable, avoids duplicate nominal choices that all clip to the same actual duration and
isolates optional shorter individual commitments. It is explicitly **not** a test of every
longer-than-10 duration scheme. If that restriction makes the question poor value, explain
the specific alternative and its cost; do not infer opportunity from label counts or add
artificial synchronization/faults to favor AR.

The unresolved loss/critic alternatives are:

1. Extend D2's separate agent/team segments and common commitment-aware value inputs; train
   a duration factor using the corresponding legitimate return target and baseline. A
   duration prefix is available before that factor but later sampled durations depend on
   it. Identify precisely which sampled skills/latent/durations may enter each skill or
   duration baseline, and whether existing segment bootstraps need a different state.
2. Use one ordinary event-level team-return target and pre-action commitment/history value
   shared across arms for all actually sampled factors, with discounting to the next event.
   Explain what is lost/gained versus per-member closure, including irregular sampling,
   clipped PPO surrogates, event frequency and finite-learning variance.

Do not assume a COMA marginalization holding later AR durations fixed remains a legitimate
baseline; do not require a new causal-credit method. A simple lawful baseline is preferable
to a new module. Distinguish faithful sampling/replay, a useful approximate PPO objective,
and any stronger unbiased-policy-gradient claim. A package result need not identify the
cause as correlated exploration; marginal duration, optimization, capacity and occupancy
differences remain alternative explanations.

### Prospective cost and discriminating reading

This consultation and implementation inspection start 0 fits. The proposed first exploration
is 3 new training instances, one per arm, at 360,000 primitive team transitions each
(1,080,000 total training transitions), remote WSL preferred. This is a costed design option,
not an accepted batch or confirmation. The DM will bind seeds, evaluation population and
curve positions, exact horizon/config, compute and stopping before launch after reading advice.
There is no architecture grid, frozen-label prerequisite or requirement for a positive toy.
Ordinary correctness tests do not establish performance.

Read full native J, actual S1 service components, prespecified curve/endpoints and actual
data/update/compute cost. Log joint-event exposure and executed commitments to check whether
the proposed difference exists in use. AR beating only factored but losing to fixed does
not justify complexity; both variable arms beating fixed without useful AR increment favors
the simpler arm. Proxy-only changes weaken the proposal's native-use explanation. One seed
per arm is exploratory, not stable superiority, equivalence or a paper-grade claim.

### Context and source precedence

All paths below resolve at source_sha supplied in the actual message. Read only the named
relevant sections; no recursive archive preload is requested.

- Current governance: `docs/project/OPERATING_CONSTITUTION.md` sections 1–5 and 8. Owner
  explicitly selected this new study; old FSD/Claude remains paused and G33 remains frozen.
- Current methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Explore / Comparators /
  Update the working explanation / Cost and exposure; `.agents/skills/hmasd-research-engineering/SKILL.md`,
  Core versus experimental / Checks and review. They are methods under the constitution.
- Shared background: `docs/research/RESEARCH.md`, topics 3–6 and the duration row of the
  current plan. These are revisable scientific judgments, not a requirement to agree.
- Existing advice: `docs/research/archive/2026-09-21/RESEARCH.md`, the duration subsection
  of the complete whole-project Answer/Decision and the complete MARL-concept Answer/Decision.
- Direct adverse evidence: `docs/research/candidates/flexible_skill_duration/NOTES.md`,
  2026-09-21 03:43/03:52 B14 reading and rest, plus its scoped B13/02:51 prior interpretation.
  Do not reinterpret the old claim endpoints or reuse old weights as new training replication.
- Code: `scripts/run_flexible_skill_duration_e0.py::_make_config`,
  `scripts/run_fsd_uav_individual_renewal_b01.py::make_config`;
  `hmasd/agent.py::_batched_assign_skills_d2`, `_d2_store_transition`,
  `_d2_flush_open_segments`, `update_coordinator_d2`, `update_discoverer_from_rollout`;
  `hmasd/networks.py::SkillCoordinator.assign_partial_batch`, `evaluate_training_batch_ordered`;
  `hmasd/utils.py::RolloutBuffer._compute_d2_high_level_advantages` and D2 storage/sampler;
  `hmasd/ha_ctse.py::HorizonSkillEditor` only for the identified existing-head mismatch.
  Function names are locators, not a claim that each implementation is correct.

### Requested answer and writing constraints

Recommend the least invasive useful comparison and give explicit conditioning/return/credit
semantics. Name the strongest material objection and the smallest observation or correctness
check that can discriminate it, including a native outcome rather than only duration
statistics. State which prior judgments are strengthened, weakened or unresolved, costs and
remaining uncertainty, and `MATERIAL_DISSENT: yes/no` for this proposed design. Do not turn
uncertainty into an invented probability, global impossibility or a new approval gate.

No training or edits outside the following empty `### Answer` subsection in this unique
question. Target branch: `codex/joint-duration-learning-20260921`. Read pinned sources for
reasoning, but fetch the latest target file and its actual blob SHA before writing. Preserve
all other bytes and stop on overlapping edits. Return the actual answer commit if written;
if writeback is unavailable, return the complete answer in chat, not only a receipt or link.

### Answer

#### 一、建议：保留三臂，选择共同事件回报，不把旧 D2 损失直接接上时长头

**建议采用题面的第 2 种构造：复用 D2 的部分重选、持有状态和顺序技能解码，三臂共同使用事件级团队回报、采样前的承诺条件价值函数，以及只作用于真实采样因子的普通 PPO surrogate。** 原有团队/个体技能、闭环 primitive actor、低层 PPO 和判别器继续共同学习；不启用 HA-CTSE，不增加前缀 Q 网络、反事实信用、预测目标或课程。固定臂也使用这一共同高层学习实现，而不是拿历史 D1280 checkpoint 充当对照。[代码调度与更新][agent] [顺序采样与重放][networks] [现行研究背景][background]

这不是说“各成员自己的片段天然错误”。第 1 种构造在**累计真实团队奖励、使用适当续接状态、只减合法 baseline**时可以成立；但它不是“已有 gamma^elapsed，所以直接给 duration 复制 agent advantage”这么简单。对于本次先生成全部技能、再生成时长的联合动作，共同事件构造更容易明确每个因子究竟在优化哪个未来量，也减少了不同结束时刻、不同 value head 和不同分母叠加的歧义。代价是改变共同高层 target/sampler，增加事件级价值学习工作；它不保证更低方差或更好成绩。

**MATERIAL_DISSENT: no。** 对题面已经限定的固定/充分知情分解/普通 AR 三臂、cap=10 和一次有成本边界的探索，没有实质异议。上述选择是在题面明确开放的两个方案中选择第 2 个，不是对未实现代码的认证。对“HA-CTSE 的 AR 开关就是本比较”“旧 D2 的片段与损失完全不改即可保证正确”这两种更强表述，我明确不认可。

我保留 cap=10 的第一问：**同一团队十步更新制度内，允许成员提前重选是否值得，以及 AR 是否比充分知情分解输出多带来有限学习价值。** 它不是长于十步的时间抽象研究，也不是联合策略普遍优越性的检验。题面已经承认这个范围，因此现在不扩菜单、改团队时钟或增加第四臂。[固定问题][question] [既有完整概念答复与 Decision][concept]

#### 二、源码真正支持什么，以及哪些不是现成能力

配置核对支持所述起点：E0 的 D0 设置 `k=10`、D2 两项 logit-gap cost 为无穷、个体/team cap 均为 10、`age_feature="off"`；renewal runner 的 `make_config` 接在这个配置上，允许显式设置 coordinator batch size，并使用六团队/六个体标签。不能把另一个 arm 的成本、开关或旧运行的配置标签自动搬来。[E0 `_make_config`][e0] [renewal `make_config`][renewal]

D2 已经保存采样 mask 和解码顺序，保持成员在前、待重选成员在后；teacher-forced replay 可以复用。其 agent/team 表分别累计**同一真实团队 reward**，在相应边界结算；低层仍逐 primitive step 训练。需要区分三件事：[D2 实现][agent] [buffer 与 GAE][utils]

* 当前 value 输入是 state/joint observations 的编码，没有显式 held skills、承诺剩余时间和 cap 相位。这并不使它作为当前动作无关 baseline 自动有偏；它使“该 value 已经充分表示新持续策略的续接条件”没有依据。
* 当前 GAE 的 gamma 按实际 elapsed 指数折扣，但 lambda 每个相应片段乘一次。`update_coordinator_d2` 调用高层优势函数时没有显式传 `gae_lambda`，后者默认值为 .95。新实现应绑定实际使用值，而不是仅抄配置名。[GAE 调用与实现][agent] [GAE helper][utils]
* 当前团队 policy loss 与成员 policy loss 分别除以各自有效行数；entropy 又按事件行累计成员项。增加一个“duration 平均 loss”会继续引入相对缩放。它不是自动等于联合 log-prob 梯度。原 `config.k` 同时控制低层 recurrent chunk，执行 deadline 必须独立存储。[高低层更新][agent]

`HorizonSkillEditor` 的 `_duration_outputs` 对整个 hidden 张量一次生成各成员 duration 分布；AR 循环更新的是技能/edit context，没有把已经采到的时长传给下一时长因子。其 `_features` 也不是这里要求的完整承诺与时长前缀接口。因此这里只能复用普通 categorical/mask 的写法，不能把那个完整编辑器切换进来，声称保持了原 HMASD。[HA-CTSE 相关方法][ha]

#### 三、把采样前状态、技能后状态和事件时间分开保存

以 primitive 时间计，令 \(t_j\) 是 episode 开始或至少一个成员/团队有权重选的事件，\(S_j\) 是本次待重选成员集合。\(H_j^-\) 表示**本次任何随机选择之前**的合法历史与已知承诺；它包含现有高层有权取得的 state/joint observations、原 held team/individual skills、年龄或绝对 deadline、到团队 cap 的时间，以及 eligibility/团队到期标志。有限 episode 所需的时间位置也必须来自既有合法计时。不要把未来实际终止时刻、未来 observation 或 simulator 隐藏变量放进来。

具体首实现可用原高层编码，加技能/承诺特征的普通投影形成 \(c_j^-\)，训练一个团队 value；不额外造关系模型或前缀 critic。**\(c_j^-\) 是 \(H_j^-\) 的表示，不因为加了 age 就获得充分状态证明。** 低层 GRU 的历史可能影响后续行为；已有合法历史摘要可以共同使用，但没有保存、没有重放的历史不能被声称已经输入。使用有限状态摘要作 bootstrap，是下面近似 actor–critic 的剩余误差来源。

团队到期时先按共同规则重开十步团队窗口，采样团队 latent，再重选所有成员技能；仅个体到期时保持团队 latent 和其他成员的技能/承诺，按 D2 顺序重选 eligible 技能。**全部当前技能确定后**，记

\[
C_j=(c_j^-,Z_j,\mathbf z_j,\text{本次合法时长支持集}),
\]

再采样新时长。这里 \(Z_j,\mathbf z_j\) 是本次生成或继续持有的实际值，不是旧值的别名。两种可变策略为

\[
\begin{aligned}
\pi_{\mathrm{fact}}(A_j\mid H_j^-)
 &=p_{\mathrm{skill}}(Z_j,\mathbf z_{S_j}\mid H_j^-)
   \prod_{i\in S_j}q_i(d_i\mid C_j),\\
\pi_{\mathrm{AR}}(A_j\mid H_j^-)
 &=p_{\mathrm{skill}}(Z_j,\mathbf z_{S_j}\mid H_j^-)
   \prod_{\ell=1}^{|S_j|}q_{i_\ell}(d_{i_\ell}\mid C_j,d_{i_{<\ell}}).
\end{aligned}
\]

\(p_{\mathrm{skill}}\) 中未重选的 team/skill 项是确定的持有操作，不是需要学习的随机因子；两臂的“相同技能机制”指方法、信息和更新规则相同，不指训练后参数相同。顺序 \((i_1,\ldots)\) 使用 canonical eligible order，重放原样保留，不在 epoch 中重新排列或重新采样前缀。分解臂可以通过共同条件和原团队 latent 形成**边缘相关与确定性协调**；它只是给定 \(C_j\) 后不再依赖本事件其他新时长。[既有概念范围][concept]

设本次生效的团队 deadline 为 \(D_j^Z\)，则 \(R_j^{\mathrm{cap}}=D_j^Z-t_j\)，合法时长是 \(1,\ldots,R_j^{\mathrm{cap}}\)。团队刷新事件的这个剩余量为 10，而不是刷新前的 0。先 mask 后采样，选择 \(d_i\) 就设置 deadline 为 \(t_j+d_i\)；不把十个名义类别采完再 clip 成若干同一动作。\(d_i=1\) 意味着执行一个 primitive transition 后才到期，不能形成零时间重选循环。剩余量为 1 时 duration 因子退化，log-prob/entropy 为零。

固定臂总在团队窗口起点持有十步，duration 是确定规则，无 duration policy loss。强制所有可变臂选十步时应退化到同一固定执行制度；这是执行语义检查，不是说有限 softmax 参数必然实现精确点质量，也不是要求新 critic 与历史 checkpoint 数值相同。未重选成员只保留旧 deadline，不产生新的 duration score。相同标签再次选中仍可开始新的承诺，不能用“标签没有变”删掉这次真实动作。

#### 四、推荐的共同事件目标：下一事件不是任何一个人的名义时长

下一事件 \(t_{j+1}\) 是当前执行中的最早合法重选时刻，或任务结束边界。令 \(\Delta_j=t_{j+1}-t_j\)，实际团队段回报为

\[
\mathcal R_j=\sum_{u=0}^{\Delta_j-1}\gamma^u r_{t_j+u}^{\mathrm{native}}.
\]

**\(\Delta_j\) 通常不等于正在训练的某个 \(d_i\)。** 例如一名成员新选 8 步，另一名保留的承诺还剩 2 步，下一事件就是 2 步以后；前者仍持有 6 步。此时的续接价值必须看见这个承诺，不能假装全队都可重新行动。底层在这两步内仍每步读取 observation 并行动，duration 不等于开环 primitive action。

共同 TD residual 与 GAE 可写为

\[
\delta_j=\mathcal R_j+\gamma^{\Delta_j}b_j V_{\bar\phi}(c_{j+1}^-)
                        -V_{\bar\phi}(c_j^-),
\qquad
\widehat A_j=\delta_j+\gamma^{\Delta_j}\Lambda(\Delta_j)m_j\widehat A_{j+1}.
\]

这里 \(b_j\) 表示任务是否真的还会继续，\(m_j\) 表示是否存在同一 episode 内可接上的已采集后继事件；二者不是一个含混的 `done`。actor 使用冻结、停止求导的优势；value 拟合停止求导的 \(\widehat A_j+V_{\bar\phi}(c_j^-)\)。不要在 PPO epoch 中用已经更新的参数重新决定旧动作的结束时间或重算旧行为概率。

**建议把 trace 的时间单位也共同固定。** 以固定十步参考的实际高层 lambda 值 \(\lambda_{10}\) 为锚，采用

\[
\Lambda(\Delta)=\lambda_{10}^{\Delta/10}.
\]

这样固定十步时恢复 \(\lambda_{10}\)，把一个十步区间分成若干事件不会仅因事件变多而额外缩短 trace 的物理时间尺度。这是本答复建议的普通估计设置，不是已有 D2 事实，也不保证有限 lambda 下估计与事件切分完全无关。保留固定“每事件 lambda”同样是合法的近似选择，但那会使短时长改变实际 trace 衰减，应明确作为学习包的一部分；不要把它误称为相同物理信用窗口。GAE 的一般价值是偏差/方差折中，而非无条件无偏。[源码 lambda 语义][utils] [GAE 作者摘要][gae]

**结尾处理必须具体。** 原生有限 episode 的目标结束时 bootstrap 为零，即使环境 API 把该结束标成 `truncated`；人工 rollout 截断、但任务本应继续时，应在真实 final observation 和仍在执行的承诺上 bootstrap，不接 reset 后的新 episode。不能机械地把所有 truncation 都当成终局，也不能机械地全部 bootstrap。已有 runner 把 terminated/truncated 合并，实际新绑定必须按所选任务目标解释，而不是只看字段名。[现有 runner][renewal]

若 rollout 在非决策时刻结束，该点只是结算边界：用“继续当前承诺”的状态价值，eligibility 可为空，不虚构一次技能/时长采样。对齐原有 episode/rollout 与 cap 可以减少这类情况，但不能以方便为由改变声明训练量；若保留中段截断，就必须训练/验证这个继续状态的 value 语义。用下一次尚未发生的重选 value 替它，或跨参数更新拼接旧行为概率，均不是合法替代。

同一 \(\widehat A_j\) 作用于该事件**实际采到的**团队、技能与时长因子。团队 latent 虽只在 team event 采样，它仍通过 \(V\) 和后续 GAE 获得跨成员事件的后果；没有必要到下一个 team event 才让它拥有长远信用。共享团队 return 不等于宣称所有成员贡献相等：各 score 对各自条件概率的导数不同。

#### 五、为什么各自闭合的 D2 方案也能成立，以及我为什么不首先选它

令 \(\tau_i\) 是从本次动作开始到成员 \(i\) 下次真实重选/任务结束的间隔。一个合格的成员因子回报可以是

\[
Y_{j,i}=\sum_{u=0}^{\tau_i-1}\gamma^u r_{t_j+u}^{\mathrm{native}}
       +\gamma^{\tau_i}b_{j,i}V^\pi(H_{t_j+\tau_i}^-).
\]

这段期间其他成员可以多次更新；奖励仍是团队奖励，续接仍是**完整未来**。在条件充分、续接 value 正确的理想情形，停止时刻分解并不会丢掉当前动作对后续的影响，成员/团队不同边界都可以估计同一个 reward-to-go。原 D2 已经跨自己的片段做 GAE，不能把它描述成“信用硬截断在十步内”。[D2 结算与递推][agent] [buffer 递推][utils] [FSD 更正与收束][fsd]

危险在于错误的 \(V\) 语义。例如 AR 先采 \(d_1\)，再依赖它采 \(d_2\)；成员 1 在 2 步后重选时，成员 2 可能还持有此前受 \(d_1\) 影响的长承诺。只累计成员 1 两步内奖励、把未来置零，或者用忽略成员 2 承诺的头当作已正确的续接，都会遗漏或近似掉这条后果。**未来 state 中包含当前动作留下的承诺是必要且合法的；在当前因子的 baseline 中减掉自身选择则是另一回事。**

各自闭合的优点是复用现有表、较少短事件 bootstrap、不同成员可获得不同长短的经验回报，可能减轻某些估计负担。其代价是要同时绑定 team/agent/duration 的边界价值、尾部状态、mask、trace 时间单位和因子权重；一次事件的各 loss 可能使用不同近似噪声。理论上可正确，不等于现有每个 head 已实现这一点。

共同事件则统一一套团队 Bellman 语义，适合本次的完整联合动作，也使 held commitments 在每次事件都显式进入续接。损失是更多短间隔价值估计、同一优势带来的共同噪声、以及丢掉潜在的成员专用 baseline 方差收益。**没有一般方差优劣定理。** 在同一个完整 return 上取不同合法 baseline，或用精确 value 在不同停止时刻分解，和有限网络/有限 lambda 下的实际训练，是不同问题。首轮选择共同事件，是减少必须解释的接口与估计对象，不是预先判断它会赢；不另加一臂比较这两个 critic。

#### 六、每个因子可以减什么 baseline：按真实采样次序判断

把本事件随机因子顺次记作 \(a_\ell\)，其采样前信息为 \(\mathcal F_{\ell-1}\)。在通常的可微、固定条件支持下，

\[
\mathbb E[\nabla_\theta\log p_\theta(a_\ell\mid\mathcal F_{\ell-1})
                 \mid\mathcal F_{\ell-1}]=0.
\]

因此任何可积的 \(b_\ell(\mathcal F_{\ell-1})\) 都能在**未裁剪的当前策略 score 项**中消去期望；共享网络参数不破坏这个条件恒等式，actor loss 必须停止通过 baseline/advantage 求导。下面是本题的具体允许范围；它是概率条件判断，不是给每一项再建一个 head 的建议。[既有概念 Decision 的解析核对][concept]

| 被训练的因子 | 可以用于本因子 baseline 的已知量 | 不能不加论证直接放入的量 |
| --- | --- | --- |
| 新 team latent | 事件前合法历史、旧承诺、已知 eligibility/cap | 本次新 team latent、新技能、新时长 |
| 第几个新 skill | 上述量；已经确定的 team latent；所有 kept skills；前面已采的新 skills | 自身新 skill、后采的新 skills，以及随后采的任何新 durations |
| 分解 duration \(d_i\) | 完整当前 team/joint skills、旧 held commitments、合法时钟与历史 | 自身新 duration、由新 durations 决定的下一事件间隔 |
| AR duration \(d_{i_\ell}\) | 分解臂允许量，加本次前面的新 duration prefix | 自身与后面的新 durations、包含其后果的下一事件间隔 |

分解时长给定完整共同条件后独立，因此在严格满足该独立条件时，其他成员的新 duration 还可以构成该 duration 因子的动作无关 baseline 信息；不能把这个特例搬到 AR，也不能搬回其上游 skill 因子。首实现**不利用这个额外技巧**：统一减 \(V(c_j^-)\)，它对所有因子合法、最容易核对。技能后、时长前的条件 value 可能更好，但不值得在本次先变成额外信用模块。

为何不能照搬“固定其他动作”的 COMA 写法？沿用概念 Decision 已核对的两因子反例：\(a_1\sim\mathrm{Bernoulli}(p)\)，\(p=\sigma(\theta)\)，\(P(a_2=1\mid a_1)=1/4+a_1/2\)，回报 \(Q=a_2\)。于是

\[
J=\tfrac14+\tfrac p2,\qquad \nabla_\theta J=\tfrac12p(1-p)>0.
\]

若固定已经采到的 \(a_2\)，对 \(a_1\) 求边际作 baseline，则该 baseline 就是 \(a_2\)，优势恒零，恰好抹掉 \(a_1\) 对后采动作的全部价值。完整支持、baseline stop-gradient 都救不了这个统计依赖错误。正确的条件 Q 必须对**依当前选择生成的后缀分布**取期望；本次直接用真实完整回报及其普通 bootstrap，不建这个反事实模型。这个解析例子是正确性参照，不是 S1 有时长收益的证据。[反例与适用边界][concept]

#### 七、PPO 具体怎么接，以及三层“正确”不能混称

**采样/重放层。** 对每次真实采样保存 pre-event context、完整技能后 context、合法 duration mask、团队/成员采样 mask、两种解码顺序、实际 tokens 和每因子 old log-prob；后继结算再保存 actual elapsed、reward、结束/截断类型及续接承诺。重放必须使用旧动作形成的前缀，不重采样后缀。保持操作的 log-prob/entropy/actor 梯度为零；不能给每个 primitive step 重复写入同一次 duration 的 policy 项。[现有可复用重放][networks] [D2 sampler][utils]

还应注意“输入相同”也包括归一化与循环状态。若开启 running normalization，在一个行为数据批次内冻结相应变换、保存实际变换后的输入，或用等价可重放方案；相同网络参数及相同 train/eval、随机层语义应能复现 old log-prob。若选定配置关闭归一化，identity 即可，不必新增修复。源码的 D2 决策子集统计更新和 update 时再应用统计的路径需要据实际配置核对，**这里未运行数值检查，不能宣布已发现新失败**。若未来高层 value/actor 使用 recurrent history，随机打散事件不能替代合法序列重放。[相关采集与更新路径][agent]

**首选优化层。** 为尽量复用原 D2，我建议每因子 clipped ratio、同一事件优势，对实际因子求和，而不是再堆一个各自平均的 duration loss。对一个含 \(T\) 个 primitive team transitions 的 rollout，可把高层 actor surrogate 明确写为

\[
L_{\rm actor}=\frac1T\sum_j\sum_{\ell\in\mathcal A_j}
 \min\left(\rho_{j\ell}\widehat A_j,
  \operatorname{clip}(\rho_{j\ell},1-\epsilon,1+\epsilon)\widehat A_j\right),
\qquad
\rho_{j\ell}=\exp(\log p_\theta(a_{j\ell}\mid\mathcal F_{j\ell-1})
                       -\log p_{\rm old}(a_{j\ell}\mid\mathcal F_{j\ell-1})).
\]

\(\mathcal A_j\) 只含本事件真实随机因子。用共同固定交互分母，是为了不让“团队平均 + 成员平均 + 时长平均”暗中改变相对 credit 权重；不是要额外按 \(d_i\) 或 \(\Delta_j\) 乘奖励。均匀抽事件 minibatch 时，要用该 rollout 的事件数与 \(T\) 转换为同一目标的估计，不在每个可变长度 batch 中另定义目标。全局数值尺度、value/entropy 系数、优化器和优势处理三臂共同绑定；若做优势标准化，按同一事件总体估计，不因某事件有更多 duration factors 就重复计入其统计量。

这是建议的**普通近似 PPO**，不宣称它就是联合动作的 clipped PPO。事件联合 ratio 是所有实际因子 ratio 的乘积；逐因子 clip 不等于对该乘积 clip，也不保证联合 KL/trust region。选择联合 ratio 是一个不同的普通优化选择，但本轮不需要再加比较臂；当前选择以复用原更新形态为理由，须报告实际 KL/clip 饱和和优化暴露，而不是借 PPO 名称取得单调改进保证。[当前分项 PPO][agent] [PPO 作者摘要][ppo]

entropy 也只统计本次真实采样项，按共同规则缩放；它是优化正则，不是偷偷加入任务切换费。AR 在旧前缀上计算条件 entropy 的常用 surrogate，不应被宣称为精确的新策略联合熵梯度。原低层/判别器目标及更新安排保留，duration 改变了它们实际见到的技能驻留分布；不额外做占用平衡或新内在奖励。[低层路径][agent] [占用解释边界][concept]

**无偏策略梯度层。** 对固定行为参数下的完整回报，令 \(G_j\) 是从 \(t_j\) 起折扣的真实 reward-to-go。对从 episode 起点定义的 \(J_\gamma=\mathbb E\sum_t\gamma^t r_t\)，其高层参数 score 形式包含

\[
\mathbb E\sum_j\gamma^{t_j}\sum_{\ell\in\mathcal A_j}
 \nabla_\theta\log p_\theta(a_{j\ell}\mid\mathcal F_{j\ell-1})
 \bigl(G_j-b_{j\ell}\bigr).
\]

这要求正确采样测度、合法 baseline 和完整回报或满足相应条件的估计。上面推荐的首实现保留常用 PPO 的未额外乘 episode 起点 \(\gamma^{t_j}\) 的 surrogate；**gamma^elapsed 正确，并不使它自动成为上述目标的无偏梯度**。近似 value、有限 lambda、多 epoch 旧数据、clipping、样本优势标准化又分别带来近似。若后来选择显式起点折扣权重，那是应共同绑定的优化语义变化，不能只加给 AR。

此外，这个公式只描述高层 native-reward 部分；完整 HMASD 还共同更新低层与 discovery，并非一个已经证明对单一 native J 精确求梯度的算法。native evaluator 仍报告原来的完整 J，不改成“每次高层决策的平均奖励”。**我建议的是一套可忠实实现、可评价的近似学习包，不是一个新的无偏信用定理。**

#### 八、最强异议与最小可区分观察

**最强科学异议不是 AR 能否写出来，而是这个 cap=10 的实际任务是否值得新增时长自由度。** 每十步团队刷新可能截短有用配合，充分知情的分解头和原 latent 已能学确定性的错峰；AR 还增加串行条件化、优化和估计负担。它可能只是更短的边缘 duration、更多高层更新、不同容量或技能占用在起作用，而不是所谓相关探索。这些替代解释在方法包获益时仍然存在。[背景与原概念范围][background] [concept]

不过共同 cap 也意味着完整非终止窗口起点会有全员重选，并非新臂必然没有联合事件。应记录 **\(|S_j|\ge2\) 且至少两个成员各有多个合法 duration 的事件**，与所有 eligible 计数分开；\(R^{\mathrm{cap}}=1\) 时人数多也没有 duration 关系可学。记录声明/实际驻留、同标签重选、cap/终局结束、技能占用和真正服务变化，不靠总相关系数判断条件依赖被利用。增加事件数不是增加独立训练重复。

最小正确性检查可以与本次实现一起完成，不形成一套新的科学准入程序：

| 检查 | 它真正区分什么 |
| --- | --- |
| 很小的可枚举两成员时长分布，检查 mask、概率和为 1、teacher-forced old/new log-prob 一致、held 项无梯度 | “写了 AR 代码”与“实际采样/训练同一个分布” |
| 固定回报序列上检查 \(d=1\)、\(d=R^{\mathrm{cap}}\)、别人先到期、episode 结束与人工 cutoff；lambda=1 时事件分段回报应与 primitive reward-to-go telescoping 一致 | deadline/off-by-one、遗漏/重复奖励、错误 bootstrap，而不是性能 |
| 上述有后缀依赖的两因子解析例子，比较完整期望的导数与未裁剪 score；同时检查强制十步时的固定执行退化 | 当前因子的后缀影响是否被 target/baseline 错误抹掉；不是要求 toy 产生正收益 |

共同事件方案最值得防范的实现异议，是“长时长动作的效果发生在别人的第一次到期以后，却被 next-event target 丢掉”。第二、三项检查必须覆盖这一情况：早期事件的 reward 可以为零，后果通过真实后续回报或正确 continuation 到达早期 score。检查通过仍不证明有限网络在 S1 上能学好 continuation。

**区分科学异议的最小原生观察就是已提出的三臂完整学习，而不是再购买一个 frozen-label 阳性前置实验。** 在相同声明交互量、固定终点与少量预写曲线位置，读取完整 native J 及实际 S1 coverage/quality/原生代价分量；沿用真实字段含义，不能把名为 energy 的旧代价项升级成 S7 电池/返航结论。训练采样与评价的 greedy/stochastic 规则事先固定，各臂一致，不能见分后换规则来解释“探索有用”。[实际 runner 的评价口径][renewal]

AR 优于分解且优于固定，才支持在该范围继续保留联合学习包；一条曲线或一个 seed 只提供探索理由。两种可变方式均胜固定、没有值得保留的 AR 增量时，优先简单分解，不从低精度小差值宣称等价。AR 只胜分解却输固定，不推广复杂度。只有相关性、entropy、critic loss 或局部服务代理变化而完整 J 不改善，削弱当前转化解释；没有有用增量且没有新的可区分理由，就结束这套配方，不自动扩菜单或加种子。

cap=10 的阴性不能排除更长时间抽象。若以后所问确实是长于十步的配合，必须另行声明共同团队更新规则、能够实际执行长承诺的支持集及相应固定参照；仅把菜单改为 1..20 后仍在十步 cap 截断，不会回答它。那是重新购买不同问题，不是本次为保护 AR 添加的救援或当前必做成本。

#### 九、历史判断、成本和未解决部分

**历史负证据保留，而且采用更正后的版本。** B13 的预声明 P1 成立、P2–P4 失败；02:51 对早先过宽的“选择价值上界”“coordinator 没贡献”表述作了收窄。B14 主比较三块约 +.019、+.016、−.019，记录均值 +.005，未达到当时预先规定的反转条件；第二组旧 BANDIT 权重上有 +.047 的条件收益，不能抹去，但也没有挽救先前完整方案。03:52 的休止决定仍成立。这不是“所有高层信用无效”，更不是对重新共同学习的 duration 系统的实验结果。[B13/02:51 与 B14/03:52 原始笔记][fsd]

因此，加强的是：真实联合学习、充分知情的普通参照、完整团队后果和实际成本需要一起比较；削弱的是：标签计数、局部信用或更大动作空间能直接推导收益，和“现成 head 名称等于可用实现”；仍未解决的是：S1 十步制度内有没有值得利用的时序机会、分解参照是否已吸收它、共同 critic 的实际误差及各臂的计算代价。B12 不给新策略类的价值上界；UCOPE 的局部后果按本题与共享背景的原边界继承，本轮未重放其原始数据。[background] [concept]

本次为阅读、解析与写答复，**0 新 fits、0 rollouts、0 科学评估**。题面首探索仍是每臂一个新训练实例，每个 360,000 primitive team transitions，共 **3 fits / 1,080,000 training team transitions**；评价另计。它不是已经接受的批次，更不构成训练总体优势、等价或论文级确认。新种子、面板、曲线位置、精确配置、共同损失尺度与停止条件由 DM 在运行前绑定；现行宪章的后续确认要求不被一个单种子结果替代，也不因此现在自动追加确认。[question] [constitution] [methods] [engineering]

相同 primitive 交互量不等于相同代价。短时长会增加有效高层事件、可训练因子、minibatch 和优化调用；AR 多出顺序 duration 条件化，而判别器/低层仍有逐步学习成本。应记录实际训练/评价交互、coordinator 与低层更新、参数及推理工作、运行时间和内存，并保持低层 chunk=10 与新 duration deadline 解耦；不强行配平所有决策数来删除时间自由度本身，也不把额外计算藏成免费探索。使用 `wsl_4070` 优先的 owner 顺序；本轮没有检查节点当前可用性，不提供新实现墙钟报价或完成期限。[question] [agent] [methods]

**阅读范围与信息缺口。** 推理输入固定为 `012b2ade2e2c836d272979516d6c89cd4c49a121`：已读题目全文、指定宪章/两项 skill 的相关部分、共享背景 3–6 与 duration 当前计划行、完整 MARL-concept Answer/Decision、whole-project Answer/Decision 的 duration 部分、直接 FSD B13/02:51 与 B14/03:43、03:52，以及题列配置、D2 调度/结算/更新、ordered replay、D2 buffer/sampler/GAE、低层更新和 HA duration 不匹配方法。没有仍未读取、却被本答复当作已核实的关键 Context 来源。

没有重算历史 raw arrays、重放二进制 checkpoint、运行新正确性测试或验证新 duration implementation。外部补充只核对 PPO/GAE 作者摘要，用于 surrogate 与偏差/方差定位；没有据此声称完成全文优先权审查。文中的事件目标、baseline 条件、lambda 时间单位和 loss 选择是本答复的推导/设计建议，不是已有代码或已发生效果。普通状态摘要的充分性、有限训练方差、三臂真正跑通后的效果与成本仍待实际实现观察。当前资料足以选择这个有界比较，不足以保证它有原生收益。

最终落点是：**保留 cap=10 的三臂完整学习；共同采用承诺条件的事件团队回报；明确因子采样次序与 PPO 近似边界；用原生结果决定保留、简化或停止。** 这不重启旧 FSD/Claude，不改 G33，不产生新审批要求，也不把普通自回归命名为新信用算法。

[question]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/docs/research/candidates/joint_duration_skill_learning/NOTES.md#pro-question-2026-09-21-duration-sampling-and-credit
[constitution]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/docs/project/OPERATING_CONSTITUTION.md
[methods]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/.agents/skills/hmasd-scientific-tools/SKILL.md
[engineering]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/.agents/skills/hmasd-research-engineering/SKILL.md
[background]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/docs/research/RESEARCH.md
[concept]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/docs/research/archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-marl-concept-formation
[fsd]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/docs/research/candidates/flexible_skill_duration/NOTES.md
[e0]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/scripts/run_flexible_skill_duration_e0.py#L239-L263
[renewal]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/scripts/run_fsd_uav_individual_renewal_b01.py
[agent]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/hmasd/agent.py
[networks]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/hmasd/networks.py#L1029-L1229
[utils]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/hmasd/utils.py
[ha]: https://github.com/CartmanFatass/My-paper-code/blob/012b2ade2e2c836d272979516d6c89cd4c49a121/hmasd/ha_ctse.py
[ppo]: https://arxiv.org/abs/1707.06347v2
[gae]: https://arxiv.org/abs/1506.02438v6

### DM reading and decision — 2026-09-21

The same accepted Pro operation completed. `deliver` verified commit
`2876bf029b441b2d6ce1d3beaeb091e12e44107e`: one target file, previously empty Answer filled,
question and all other bytes unchanged. Read the entire 16,799-character Answer, not just the
chat receipt. The driver closed its owned observation tab; no resend or new conversation.
The completed wait event was consumed with its original generation/wake/event identities.

Adopt option 2: a common pre-sampling commitment-conditioned team value and event-level
native team return, reused for all actually sampled high-level factors. Preserve original
low-level/discriminator learning. This narrows the unimplemented credit choice; it does not
strengthen any empirical duration claim. The Answer's distinction between legal baselines,
faithful replay and approximate factorwise PPO is adopted. No action-dependent COMA baseline,
new prefix value head, predictor, HA-CTSE or occupation reward is added. Conditional AR gains
would still be package effects, not identified correlated-exploration effects.

Fresh published main `63e87d81b87caa4bad0332fa0dbfdc633e939f63` retains the relevant background
3–6, owner authorization and our lead. Its changes since initialization affect another
direction's own standing only. The shared background therefore continues to require the
informed factored reference, actual service/cost reading and the old FSD stopping boundary.
No other DM's unpublished module or result is a dependency.

Binding choices within the advice: terminal-aligned native S1 episodes and rollouts, 500
primitive steps each, 16 training lanes, 45 rollouts = 360,000 team transitions per arm.
This retains the existing native episode length and lane count. The first implementation
rejects a nonterminal rollout cutoff instead of pretending an unsupported continuation
value is valid. Unit-level return checks can still exercise a supplied cutoff bootstrap;
the result runner only uses complete episodes. Low-level recurrent chunks remain 10.

The common high-level policy sees original lawful state/joint observations plus pre-event
held team/member labels (with explicit invalid-at-reset representation), commitment age and
remaining primitive steps, eligibility, team cap phase and episode position. The common
critic uses only this pre-event representation, not newly sampled labels or durations.
There is no new learned history summary or claim of state sufficiency. After all skills
are known, both duration heads additionally see actual current joint labels; AR alone gets
the earlier eligible durations of this event in canonical order. Factored prefix inputs
are zero, with otherwise the same head shape; fixed has no duration score.

Bind gamma to the native config, lambda_10=.95 and event trace multiplier
lambda_10**(elapsed/10). Sum per-factor clipped surrogates and entropy over true sampled
factors, with event-minibatch scaling to the rollout primitive transition count. Normalize
advantages once over the event population, not over duplicated factors. Use common native
optimizer/loss coefficients, 15 PPO epochs and coordinator batch size 1280. Preserve native
value normalization with correctly frozen collection values and explicitly verified replay;
native observation/state normalization is disabled. Neither per-factor clipping nor this
common scaling is claimed to implement exact joint PPO or an unbiased discounted gradient.

### L0 — event-duration learning adapter and first native runner

Deliver one direction-local implementation of the above joint-duration family. No shared
learner/runner/environment edits are initially necessary. Owned source paths are
`experiments/candidates/joint_duration_skill_learning/` and matching tests under
`tests/experiments/candidates/joint_duration_skill_learning/`. Reuse `HMASDAgent` primitive
collection, discoverer, discriminator, `SkillCoordinator` ordered skill decoder and native S1
environment. Override the necessary duration scheduling, high-level event storage and PPO
update in a local subclass; do not fork the whole training framework or toggle HA-CTSE.

The bounded Implementer owns `learning.py` and `test_learning.py`: common coordinator/context,
deadline sampler/replay, event returns and agent adapter. Expose `DurationAgent(config,
log_dir=..., device=...)` with `config.duration_mode` in `fixed/factored/ar`, ordinary
`step/store_transition_batch/update/clear_buffers/reset_env_state` APIs, and
`get_duration_metrics()` for JSON-compatible cumulative/last-update facts. All duration
parameters belong under `skill_coordinator` so existing parameter, optimizer and evaluation
sync helpers include them. The DM owns `runner.py`, runner tests, NOTES, Git index and
publication. The Implementer makes no scientific changes, result launches or Pro sends.
Parallel writers must preserve each other's paths and not stage or commit the other's work.

Invariants: duration support is masked before sampling to 1..remaining team window; team
refresh resets that support to 10; d=1 executes one physical step; held members keep their
deadline; same-label renewal is a real event; stored skill/duration tokens and orders are
teacher-forced; forced factors have zero score/entropy; pre-event value excludes new actions;
all primitive rewards appear exactly once in each event chain; terminal means the native
finite task ended; no reset state supplies terminal bootstrap. Align complete rollouts and
reject unsupported mid-episode clearing/cutoffs. Preserve original low-level/discriminator
parameter updates and objectives. Any necessary common correctness repair is disclosed and
tested separately from a scientific improvement.

Checks: enumerable two-member masked duration law/replay and held gradients; duration-prefix
dependence versus factored invariance; deadline edges/kept commitments/fixed-10 degeneration;
event reward and lambda=1 telescoping, including delayed consequences after someone else's
earlier event; analytical score-gradient suffix-dependence example; actual collector-storage-
update traversal and native short complete-episode smoke for all arms. Check CPU/CUDA on the
preferred remote when available. Small local syntax checks are development work; no local
result computation is selected. Obtain independent executable review before a result launch.
Stop dependent work for a real semantics mismatch, preserve any accepted handles, and repair
within this design; no speculative scientific additions or automatic retry are authorized.

### B01 prospective exploration — declared before implementation/results

Arms, in execution order: `fixed`, `factored`, `ar`. Training seeds respectively
2026092201, 2026092202, 2026092203; each is one fresh jointly learned instance, no checkpoint
warm start or seed matching claim. Planned cost **3 fits**, 360,000 training team transitions
each, 1,080,000 total. Primary reading is deterministic native S1 J at the fixed final
360,000-transition checkpoint, with curves at initialization, 120,000 and 240,000.
All four evaluations use the same predeclared 32 environment seeds 740000..740031, 500 steps
each (64,000 evaluation team transitions per arm, separately counted). No best-checkpoint
selection, score-dependent extension or replacement seed. Evaluation preserves all learner
RNG streams, including CUDA; evaluator parameters and normalizers are synchronized only at
these four points and do not train.

J retains the native runner definition 6 * mean episode team return / 500. Retain per-world
native coverage/quality/energy fields with their S1 meanings, all curves, actual low/high/
discriminator optimizer counts and parameter movement. Also save eligible/joint nondegenerate
event counts, nominal/executed durations, same-label renewals, cap/terminal boundaries, skill
occupancy, replay error, clip/KL and parameter counts; no proxy replaces J. Report actual
training/evaluation interactions, wall/CPU/RSS and remote occupancy, with unmeasured resource
facts labeled honestly. Remote `wsl_4070` is preferred; fresh actual-node admission and a
published exact source are required for each accepted result attempt. Initially run one fit
at a time; independent research tasks do not reserve the whole GPU or bypass memory checks.

This is an exploratory package comparison. AR must be useful against fixed and informed
factored to justify retaining its added complexity; useful variable methods without a
convincing AR increment favor the simpler method. A one-instance ranking is not stable
superiority or equivalence. If no useful native increment and no concrete differentiating
follow-up remain, stop this bounded recipe; do not automatically enlarge the menu, change
host/reward, add modules or purchase more seeds. Started fits remain **0** at this entry.

### Common recurrent correctness repair — before B01

The inherited shared-background B11 warning applies to the actual low-level update hot path:
`update_discoverer_from_rollout` uses `1-done[t]` for actor/critic entry masks, although storage
and GAE correctly interpret done[t] as ending the transition out of row t. At our terminal
row 499 this resets the RNN before evaluating the last action/value. The already correct
`SkillDiscoverer.evaluate_sequence` helper is bypassed by this optimized path.

Expand the DM's L0 only for the known shared repair in `hmasd/agent.py`: row-0 entry mask is
one, later entry mask is `1-done[t-1]`, for both actor and critic. Reuse the storage→sampler→
actual-update-dispatch regression from B's published `74fe267aa166299d93a03566e5f0ab149ff2b12d`
as `tests/hmasd/test_discoverer_entry_masks.py`. This is the same known repair, not a newly
discovered performance intervention. It applies to every B01 arm, is reviewed with the full
adapter, and is not retroactively applied to historical FSD measurements or another task's
accepted run. No other low-level loss, recurrence or reset semantics change.

The independent engineering Reviewer found no material issue in this same common repair.
On preferred `wsl_4070`, committed source `d34eb73f7` passed the reused storage-to-update
regression and existing recurrent sequence tests: **9 passed in 2.31 s**. This is correctness
evidence, 0 new fits. Remote Git needs its configured login network shell; the stalled owned
nonlogin Git fetch/checkout was reconciled and cancelled before preparing the isolated sparse
checkout. No scientific process was started, stopped or retried, and no local compute fallback
was used. Full duration-adapter integration and its independent review remain pending.

### B01 implementation accepted for execution — 2026-09-21

Implementation `c40441c1cc3a4336b03e21509de06e9ebdbe4fca` passed all **23** direction tests
on preferred `wsl_4070` in 29.50 s, with no skips. This includes actual S1 collection,
high/low/discriminator updates, fresh deterministic evaluation and checkpoint writing for
fixed, factored and AR on both CPU and CUDA; these are short correctness fixtures, not
performance evidence or result fits. The earlier 9 shared recurrent tests also passed.
All warnings were 14 existing Matplotlib/Pyparsing deprecations.

The independent Reviewer inspected the full path and the repaired failure-exposure logging:
consumed evaluation interactions and completed training episodes survive later failures;
nonfinite displacement cannot poison the failure summary. Their final diagnostic finding was
that fixed duration had been counted as a nondegenerate duration choice. Code
`cc8d87eef5fb9994f386713453923da93dc64b18` now counts only actual eligible variable factors
with support greater than one. The two changed assertions each passed remotely (fixed
evaluation: 2.95 s; AR collector/update: 4.52 s). The Reviewer found no remaining material
issue, and the DM accepts this terminal-aligned implementation for the declared B01.
Checkpoint resume, nonterminal production cutoffs and scientific benefit are not established.

Execution binding: preferred remote `wsl_4070`, isolated source checkout
`/home/wu/hmasd-worktrees/joint-duration-learning`, configured Python, device **CUDA**,
Torch/OMP/MKL/OpenBLAS threads **4**. The native sequence batch size **32** is explicit and
unchanged; 15 epochs and coordinator batch 1280 remain fixed. No device fallback, optimizer
retuning or added fit is selected. During correctness work the remote node reported
6,448 MiB free GPU memory and 9,320,000 kB available host memory; these are observations,
not reservations. Native admission rechecks actual-node memory and published pause/lead
before the first fresh `fixed` fit (seed 2026092201). Keep the remote source unchanged while
an admitted process uses it. Started result fits remain **0** at this prelaunch entry.

### Pre-training admission refusal and integration repair — 2026-09-21

The first supervisor submission `duration-b01-fixed-s2026092201` ended with exit 4 at
2026-09-22 03:54:22 UTC: the kernel's static contract requires a literal direction string,
whereas the runner passed the same string through `DIRECTION`. This was before claim
persistence, output-directory creation and scientific spawn; the declared output path was
confirmed absent. **0 result fits started**. Preserve the supervisor log at
`/home/wu/.agent-tasks/duration-b01-fixed-s2026092201/task.log`; no accepted worker was retried.

`e05566f9f4e2517632b31bca29f710c4e60ef2c8` uses the required literal and adds a test against
the actual kernel guard, extending the earlier mocked runtime-boundary tests. All three
focused remote guard/admission/SHA tests passed in 1.75 s. The independent Reviewer verified
the tiny change and the pre-claim refusal boundary; the DM accepts the fix. No learner,
seed, exposure or fit-plan change. Use normal admission of the corrected published source,
with a distinct supervisor submission name to preserve the refused submission's evidence.

### B01 fixed fit accepted — 2026-09-21

Native admission accepted the first `fixed` fit at **2026-09-22 03:58:11 UTC** on
`wsl_4070`, source `d6719caad42a469f881bdff1d7049af15be7a380`, seed 2026092201, CUDA,
360,000 planned training transitions. Supervisor submission:
`duration-b01-fixed-s2026092201-guardfix`. The runner and detached supervisor identities
were both observed running, with consistent records, at 03:59:17 UTC. Acceptance is not
scientific completion; no primary result has been read.

Runner-written records, copied without modification from the executing node:
[native manifest](../../../../runs/joint_duration_skill_learning/b01_fixed_s2026092201/launch-manifest.json)
and [actual-node preflight](../../../../runs/joint_duration_skill_learning/b01_fixed_s2026092201/admission-preflight.json).
Use the manifest's original `operation_ref`, source and output paths for read-only observation
and reconciliation; local copies do not establish local process identity. Preflight measured
9,080,238,080 available host bytes against the 4 GiB floor. Published control was main
`3f28120bfebc2a73cca3a1442d1eefc23c5fcba1`; expected lead and lifted pause matched.

Actual accepted result attempts are now **1 of the 3 predeclared fits**. Factored and AR
remain unstarted and will follow sequentially, preserving their seeds and exposure. The
deterministic waiter observes this exact operation; never restart it on missing observation.
The full output, exit witness and all scientific measurements must still be collected and
read at completion. The portable distinction between a member's selected duration and the
actual common event interval is being incorporated into the shared Research background;
it is correctness/design knowledge, not a performance claim.

### B01 fixed technical failure and bounded numerical diagnosis — 2026-09-21

The accepted fixed attempt exited 1 at 2026-09-22 04:02:08 UTC. Its original operation has a
valid exit witness and consistent identities. All ten output files were collected and their
SHA-256 values matched the executing node, including the 22,814,948-byte initial checkpoint.
The runner recorded 24,000 collected/stored training transitions, 48 training episodes,
16,000 initialization-evaluation transitions, and two completed updates. Optimizer calls:
coordinator 30; low actor/critic 4,500 each; team/individual discriminator 30/120.
Scientific-process wall time was 238.612 s; user/system CPU 217.170/22.299 s; process peak RSS
1,906,964 KiB. This remains one started fit and a **technical failure**, not a scientific
negative. Only initialization was evaluated; no declared learned-policy endpoint exists.

The third pre-update audit rejected max absolute log-probability difference **2.86698341e-5**
against its 2e-5 threshold, before any third optimizer update. Prior audit maxima were
1.40667e-5 and 1.19209e-5. The independent Reviewer found no static sampling/replay semantic
mismatch: fixed uses no duration factors or held-member choices; ValueNorm affects values,
not audited logits. A concrete numerical hypothesis is regrouping: collection uses 16 lanes,
whereas audit evaluates 800 events together, with float32 unnormalized native embeddings.
This is not yet proof of harmless rounding. Failing events and weights were not persisted;
the initial checkpoint cannot establish the exact third-rollout cause retrospectively.

The failure weakens confidence in the original audit's production calibration and leaves the
scientific comparison unresolved. Factored/AR are not started into the same unresolved path.
Consume the completed waiter event without resuming that failed operation. No scientific
retry is selected at this entry.

L0 continuation: a zero-update numerical fixture on preferred WSL, using frozen native-sized
coordinator weights and native reset states. Compare identical recorded inputs/tokens in
their original 16-lane groups and merged 800-event batches, including grad-enabled replay;
measure actual backend settings, first intermediate divergence and probability consequences.
Do not fit a policy, alter reward, consult endpoint scores, overwrite old log-probabilities,
change policy train/eval mode, or relax a threshold merely to exceed the observed failure.
An evidence-supported repair may distinguish collection-group identity from finite-precision
regrouping, preserve failure inputs for future diagnosis, and receive independent numerical
review. Any later replacement fit requires a separate prospective DM decision and retains
this failed attempt in total cost, under constitution section 3.

### Frozen replay result and numerical repair scope — 2026-09-21

Committed zero-update fixture `e027de225` passed 3 remote CUDA cases in 24.91 s: each arm
used 50 native reset batches of 16 (800 events), with unchanged weights, zero optimizer
calls and zero physical transitions. Original 16-row replay error was **0** for all arms.
Regrouped 800-row max absolute log-probability error was **2.074241638e-5** for fixed and
**1.442432404e-5** for factored/AR; relative probability errors were 2.074263102e-5 and
1.442422035e-5. Thus a frozen fixed policy can exceed the original 2e-5 check solely when
regrouped. Grad-enabled and no-grad merged replay were identical in this fixture. The
first measured difference was in float32 entity embedding (max .000732421875), then encoder
(fixed .000117778778) and team logits (9.11951e-6). Independent float64 16-vs-32 traversal
gave identical entity embeddings, encoder differences at most 8.18e-14 and team logits at
most 2.39e-15. Actual runtime: torch 2.7.0+cu118, float32 matmul precision highest, matmul
TF32 false, cuDNN TF32 true, flash/memory-efficient/math attention enabled.

This establishes a numerical false-positive mechanism for the original audit. It supports,
but does not prove, the diagnosis of the unrecoverable third-rollout event. The scientific
question and prior Pro advice remain applicable; routine numerical repair does not require
a new scientific consultation or turn this run into a performance observation.

Repair L0: retain the **2e-5** absolute factor-log-probability check when replaying the exact
collection grouping, reconstructed from stored rollout start_step and environment order.
Separately measure merged training-batch drift and refuse nonfinite factors or maximum
relative factor-probability change above **0.001** before the first update. This explicit
probability-scale diagnostic bound is 0.5% of the fixed PPO clip radius .2, not a universal
float32 bound or a claim of identical gradients. Record both errors and their thresholds.
Keep old probabilities, sampling law, actual optimizer batch 1280, epochs, precision,
train/eval modes, seeds, objective and exposure unchanged. Never replace stored old scores
with freshly computed ones. Persist event records, frozen coordinator weights, configuration
and numerical/backend facts when either check fails, for reproducible diagnosis rather than
checkpoint resume. Tests must reject wrong tokens/old scores/nonfinite values and an oversized
regrouping perturbation, while accepting the observed pure regrouping case. Keep all native
CPU/CUDA integration checks. Independent numerical review precedes any new result attempt.

One additional output-only repair is included: a freshly constructed evaluator previously
reported coordinator displacement against its own random initialization, rather than the
training instance's initialization. Copy the learner's frozen reference into the evaluator;
the initialization panel must report zero displacement. Historical learner displacement
and training/evaluation actions are unaffected. Preserve the old output as written.

### Replay repair accepted and corrected fixed attempt selected — 2026-09-21

Source `20121b2ba13c739854fbe94aebbe9303e4332490` passed the complete direction suite
on preferred `wsl_4070`: **37 passed**, no skips, 14 existing dependency-deprecation warnings,
76.02 s. This includes native fixed/factored/AR learning and evaluation on CPU and CUDA,
corruption rejection, failure artifact round-trip/hash/source checks, and preserving the
primary error when diagnostic capture fails. Local compilation and diff checks passed.
The independent numerical Reviewer found no material reachable defect in this exact diff;
that review was static, while the remote runtime evidence was read directly by the DM.

Five zero-update native-sized CUDA probes passed. Original collection-group replay error
was zero in every case, including reversed record order. Each asynchronous factored/AR case
contained 568 events in 50 groups, with 488 partial-eligibility events and group sizes from
4 to 16 (not every intermediate size occurred). Maximum merged relative factor-probability
drift was 2.074263102e-5 for fixed, 1.442422035e-5 for all-reset factored/AR, and
1.168257859e-5 for asynchronous factored/AR. The frozen probes changed no parameters,
optimizer counts or RNG state. These checks establish implementation behavior on the tested
inputs, not gradient equivalence, a universal numerical bound or policy performance.

DM decision under constitution section 3: accept this bounded diagnostic repair and select
**one fresh corrected fixed attempt**, tag `b01_fixed_r1_s2026092201`, before the original
unstarted factored and AR arms. Its seed remains 2026092201; use the original 16 lanes,
500-step episodes, 45 rollouts, 360,000 training transitions, four fixed evaluation panels
and 32 evaluation worlds per panel, native reward, model/optimizer settings and CUDA node.
Cold initialization only; do not load or resume the failed attempt. The original output,
native claim and 24,000 consumed training transitions remain preserved as a technical failure.

Prospective total cost is now **4 result attempts**: 1 failed original fixed, this corrected
fixed, and the original factored/AR instances at seeds 2026092202/2026092203. Until native
admission, actual started attempts remain 1. This explicit engineering-based decision is not
an automatic worker restart, a seed replacement, a score-conditioned extension or evidence
of a scientific negative. No further technical repeat is pre-authorized by this entry; any
new failure is collected with its diagnostic snapshot and receives a fresh DM judgment.
The question, comparator and scientific premises are unchanged, so prior accepted Pro advice
is reused. The next useful observation remains the predeclared learned-policy comparison.

### Corrected fixed attempt natively accepted — 2026-09-21

The prospectively selected corrected attempt was accepted at 2026-09-22 04:31:33 UTC.
Its [native manifest](../../../../runs/joint_duration_skill_learning/b01_fixed_r1_s2026092201/launch-manifest.json)
binds the exact published inputs, invocation, executing checkout, output and original
operation reference. A subsequent read-only native status found both recorded process
identities running and consistent. The [fresh node preflight](../../../../runs/joint_duration_skill_learning/b01_fixed_r1_s2026092201/admission-preflight.json)
measured 11,539,693,568 available host bytes against the 4 GiB floor. Both collected admission
files were SHA-256 matched to the node. The canonical pause and lead checks passed.

Actual started result attempts are now **2 of the 4 prospectively declared attempts**:
one retained technical failure and the running corrected fixed instance. Factored/AR remain
unstarted. Hold the executing source checkout unchanged while this accepted process is live.
The deterministic waiter observes its original operation reference; a checkpoint or missing
observation does not authorize a restart. Full outputs, resource costs and scientific
measurements remain to be collected and read before any comparison or subsequent arm launch.

### B01 corrected fixed result accepted; factored continuation — 2026-09-21

The corrected fixed instance exited 0 at 2026-09-22 05:44:24 UTC with a valid native exit
witness and consistent process identities. All **12 files**, including all four binary
checkpoints, were collected without changing the remote output and SHA-256 matched to the
executing node. The checkpoints also match the hashes/bytes in the runner's
[complete summary](../../../../runs/joint_duration_skill_learning/b01_fixed_r1_s2026092201/summary.json).
The full 45-row training JSONL equals the embedded training rows; all recorded numeric
measurements are finite. The DM accepts the declared fixed instance as a completed result.

Exposure matches the plan: **360,000** training/stored team transitions, 720 episodes,
45 updates; **64,000** evaluation transitions and 128 episodes across exactly the four
declared panels, each using worlds 740000..740031 for 500 steps. All evaluation optimizers
remain at zero; one cold training start and zero checkpoint loads. Optimizer calls:
coordinator 675; low actor/critic 101,250 each; team/individual discriminator 675/2,700.
Every parameter group moved: relative initialization displacement high .065122, low actor
1.157766, low critic .499444, team discriminator .079253, individual discriminator .131905.
All per-world scores satisfy native J = 6 * episode team return / 500.

| Training team transitions | Mean native J | Coverage component | SINR-quality component | Native height penalty |
| --- | --- | --- | --- | --- |
| 0 | .21165105 | .31567500 | .08710144 | .03545188 |
| 120,000 | .48310947 | .61143375 | .19353737 | .00295537 |
| 240,000 | .50583558 | .64317250 | .20303362 | .00529526 |
| 360,000 (declared primary) | **.49670730** | .65604500 | .18252755 | .01728247 |

These are the same 32 evaluation worlds for one learned instance, not 32 independent
training runs. Keep the declared final checkpoint: the 240k score is not substituted for
it. S1's `energy_penalty` is .1 times normalized average height, not measured joules or
physical battery consumption. From 240k to 360k, coverage rises while quality falls and
this penalty grows; the complete native objective falls by .00912828. Neither coverage
alone nor the best observed checkpoint replaces the primary endpoint.

Fixed execution matches its intended clock: all 216,000 training member durations declared
and executed at 10; 36,000 common events; 40,214 same-label renewals; 35,280 cap and 720
terminal boundaries; zero nondegenerate joint duration events. Across all 45 updates the
original-group replay maximum remains **0**, while merged relative factor-probability drift
peaks at .000188928869, below the prospective .001 bound. This supports the repaired audit
on this actual learning trajectory; it does not prove the exact lost original failure or
general numerical equivalence. Stderr contains 45 inherited missing-raw-state bootstrap
warnings. The direction override deliberately omits that raw-state path, requires all lanes
terminal and all events closed, and computes terminal event returns itself; the inherited
fallback bootstrap is not used by the override. No executable change follows from this log.

Scientific-process wall time **4,340.447 s (72.341 min)**; user/system CPU
3,938.399/434.102 s; process peak RSS 1,935,400 KiB (1.846 GiB), with reaped-child peak
414,684 KiB reported separately. Continuous node/GPU occupancy was not measured; the
admission and prelaunch resource observations are not reservations or peak occupancy.
Including the original failed instance, actual result cost so far is **2 attempts**, with
384,000 consumed training transitions and 80,000 evaluation transitions. Preserve both.

Working update: evidence now strengthens that this complete fixed-clock HMASD recipe can
learn native S1 service and provide the declared comparison instance, rather than only
passing short implementation fixtures. It does not establish a tuned optimum or remaining
achievable headroom. The variable-duration opportunity, extra exploration burden and any AR
increment remain untouched; prior FSD adverse evidence is unchanged. The late fixed decline
also leaves finite-learning variability relevant and reinforces using the full native endpoint.
No new cross-direction scientific conclusion is forced from this single baseline trajectory.

Next action is the already declared **factored** instance, seed **2026092202**, tag
`b01_factored_s2026092202`, followed by the original AR instance. Retain source
`472af353ed44d9da8529179c4f32b2ce030d7b56` and all bound settings except the declared arm/seed;
no code, reward, exposure, evaluation, optimizer, horizon or checkpoint-selection change.
Use fresh native admission on preferred WSL, with no warm start or replacement seed.
This completes the original discriminating comparison, adds no new planned fit, and reuses
the accepted Pro advice. Planned total remains **4 attempts including the technical failure**;
actual starts remain 2 until the next arm is natively accepted.

### B01 factored instance natively accepted — 2026-09-21

The original factored arm was accepted at 2026-09-22 05:53:38 UTC. Its
[native manifest](../../../../runs/joint_duration_skill_learning/b01_factored_s2026092202/launch-manifest.json)
binds the unchanged published execution source and original operation reference. Native
status subsequently found the runner and supervisor running with consistent identities.
The [fresh actual-node preflight](../../../../runs/joint_duration_skill_learning/b01_factored_s2026092202/admission-preflight.json)
measured 10,483,630,080 available host bytes against the 4 GiB floor, with published pause
and lead checks passed. Both admission files were copied and SHA-256 matched to the node.

Actual started result attempts are now **3 of the 4 planned attempts**: the retained
technical failure, the completed fixed instance and this running factored instance. AR is
unstarted. The deterministic waiter observes the accepted factored handle, preserving the
live source checkout and the declared 360k endpoint. No cross-arm or duration-benefit
conclusion is available until the remaining predeclared evidence is read.

### B01 factored result accepted; original AR comparison remains — 2026-09-22

The factored instance exited 0 at 2026-09-22 08:03:43 UTC with a valid native exit witness
and consistent identities. All **12 output files**, including four checkpoints, were copied
and byte/SHA-256 matched to the node; checkpoint hashes also match the
[complete summary](../../../../runs/joint_duration_skill_learning/b01_factored_s2026092202/summary.json).
The full 45-row training JSONL matches the embedded rows; all recorded numeric measurements
are finite. Configuration differs from the accepted fixed instance only in the declared
duration mode and training seed. The DM accepts the factored instance as a completed result.

The original exposure was fulfilled: 360,000 training/stored transitions, 720 episodes,
45 updates, 64,000 evaluation transitions and 128 evaluation episodes. Every declared panel
uses the same 32 worlds 740000..740031 for 500 steps, with zero evaluator optimizer calls.
One cold training start, zero checkpoint loads, and all learner parameter groups moved.
Low actor/critic and team/individual discriminator calls are the same as fixed:
101,250/101,250 and 675/2,700. Coordinator calls are **3,375 versus fixed's 675**: the same
15 epochs and batch size 1280 process 5,561–6,008 events per rollout rather than 800.
The summary and each row match this actual event/minibatch cadence; no update budget was
silently held equal or retuned. Original-group replay error is zero throughout, with merged
relative factor-probability drift at most .000567955081, below the declared .001 limit.
Stderr is byte-identical to the fixed run's 45 inherited bootstrap warnings; its already
verified terminal-override interpretation is unchanged.

| Training team transitions | Fixed mean J | Factored mean J | Factored minus fixed |
| --- | --- | --- | --- |
| 0 | .21165105 | .31067571 | +.09902466 |
| 120,000 | .48310947 | .48363505 | +.00052558 |
| 240,000 | .50583558 | .42644395 | -.07939163 |
| 360,000 (declared primary) | **.49670730** | **.46107574** | **-.03563156** |

These are one independently initialized training instance per arm with distinct predeclared
seeds, evaluated on common worlds. The initial difference is substantial: neither within-run
learning gains nor 32 nested evaluation worlds identify a duration treatment effect or
training-population ranking. Keep the final checkpoint and complete curves. At that endpoint,
factored coverage is .63813375 versus .65604500, quality .16001597 versus .18252755, and
the native height penalty .03362268 versus .01728247. All three terms contribute to the
observed J deficit (weighted contributions -.01253788, -.00675347 and -.01634022).
The height penalty retains its S1 proxy meaning, not physical energy consumption.

The additional choices were active. Training produced **259,855** common events (7.218x
fixed), 629,078 member duration selections (2.912x), 119,755 joint nondegenerate events,
116,105 same-label renewals and unchanged 35,280 cap/720 terminal boundaries. Mean declared
and executed member duration is 3.433596, while mean common-event elapsed time is 1.385388;
these are different quantities. All selected durations 1..10 appeared. At the final
deterministic panel mean member duration is 2.989537, with 7,433 common events and 5,610
joint nondegenerate events. Counts include forced cap-edge choices where applicable; the
duration-1 histogram alone is not evidence of a learned short-duration collapse.

Scientific-process wall time is **7,633.369 s (127.223 min)**, 1.75866x the observed fixed
wall time, with user/system CPU 6,946.937/861.786 s and peak RSS 1,951,028 KiB (1.861 GiB).
Reaped-child peak 414,868 KiB is separate. Shared-node occupancy was not continuously
measured, so the wall ratio is an actual package cost observation, not an isolated hardware
benchmark. With the retained technical failure, actual total is **3 attempts**, 744,000
training transitions and 144,000 evaluation transitions. No fit or failed cost is dropped.

Working update: this result strengthens actual activation and added event/optimization cost,
and weakens the return/cost promise of this ordinary factored recipe at the declared exposure.
It does not identify exploration pressure as the cause, falsify expressivity inclusion,
establish a stable population ranking, or decide the remaining AR comparison. In particular,
substantial joint nondegenerate exposure leaves the original AR-versus-informed-factored
sampling question testable; event frequency alone is not evidence of attainable service gain.
The inherited shared-background distinction between finite learning and representation now
also has an executed cost example: equal primitive steps and PPO epochs need not mean equal
event counts, coordinator updates or computation. Publish that bounded lesson with these
sources; preserve the adverse return observation and its one-instance limit.

Continue the original **AR** arm, seed **2026092203**, tag `b01_ar_s2026092203`, with the same
published execution source `472af353ed44d9da8529179c4f32b2ce030d7b56`, unchanged 360k exposure,
four fixed panels, optimizer settings and preferred WSL CUDA execution. Its role remains to
test whether ordinary within-event joint duration sampling yields a useful package against
both fixed and informed factored. Beating only factored while losing to fixed does not
justify AR complexity under the prewritten reading. This is completion of the declared
comparison, not a new rescue, renewed fit allocation, replacement seed or score-conditioned
extension. Prior accepted Pro advice applies unchanged. Planned total remains **4 attempts**
including the original technical failure; actual starts remain 3 before AR admission.
