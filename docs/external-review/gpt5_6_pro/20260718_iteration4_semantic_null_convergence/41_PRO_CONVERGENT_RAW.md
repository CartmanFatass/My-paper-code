材料读取边界：GitHub 插件在指定提交上能确认 ref/hmasd.tar 的 blob 标识，但当前接口未展开该二进制归档；因此下文不虚构 tar 内部的逐文件结论。HMASD 源锚判断依据同一提交中保留的 hmasd 实现与官方 NeurIPS 论文。其余入口列出的 Markdown、结果 JSON、实现与测试均按提交 2e2175c169c50edee21f7fd6df11acc0d9f3d026 阅读。

1. Validity and causal update
对 A_NO_MATERIAL_Z_DEPENDENCE 的裁决

确认该结果有效，但必须把名称解释为“低于预注册实质性阈值的等价性结论”，而不是数学上的严格独立或零效应。

M0 足够强：F0/F1 都通过了严格模型恢复、父实验及提交绑定、原注册随机评估逐 episode 一致、forced effects 一致、自然技能计数一致、模型参数/梯度/module mode 不变、全局 RNG 不变、来源张量不变等检查；每个 arm 有 128 个唯一 forced source 和 10,240 个唯一 natural row。因而这不是错误 checkpoint、重放漂移、重新采样、模型变异或来源混淆造成的假阴性。

F1 在 reference fold 唯一选出的最强 pair 是技能 1–2。在 inference fold：

同一 observation、同一 actor_hidden_before 下，仅替换 z，primitive-action TV CI 为 [0.046582, 0.051259]；

从同一 snapshot 强制技能后运行 12 个 active steps，process-effect CI 为 [0.027817, 0.069094]；

两者的上界都低于冻结的 delta=1/12≈0.083333，其他技能对也全部如此。

结果分派实现先检查“所有 action 与 forced-effect 上界是否都低于 delta”，满足时直接返回 A，之后才检查稀疏 stability strata 的 support；测试也冻结了这一 A–F 优先级。因此后续某些 age/rejoin strata 的 support_ok=false 不能把已成立的上游实质性 null 改写成 underpowered。

自然 segment 的技能标签虽可被满准确率分类，但这不构成反证。其自然过程 decision margin 仍约为 [0.06148, 0.06423]，低于 delta；“能识别一个很小但稳定的分布差异”和“该标签能实质性控制可执行行为”是两个不同命题。这里恰好证明了自然分类可以放大微弱模式，却不能替代 intervention materiality。

该结果明确排除了什么

它排除了：

当前 Stage C checkpoint 中的离散标签已经形成实质性 executable semantics。 当前 z 不是完全 inert，但其 action 与 12-step process control 都在冻结阈值以下。

继续对这些 checkpoint 做 context、自然分类、credit 或 assignment 读取可以发现一个隐藏的实质性技能对象。 上游对象不存在，后续读取不能创造它。

C2 可以仅通过把已有 event/age/rejoin context 接到当前标签上来“解锁”其语义。 同一输入 intervention 与随后 12-step rollout 已覆盖当前 recurrent contract；问题首先是 z 控制强度不足，而不是已经存在的强技能只缺一个读出变量。

conditional SMDP credit 可以立即激活。 Credit 不能选择一个尚未达到实质性、持续性和自然执行要求的对象。

高自然标签分类率可以作为 semantic pass。

现行计划和研究状态也明确把该结果记录为：加强 C3；只加强 C1 的“缺失 semantic-creation mechanism”诊断；削弱 C2；保持 credit 关闭；禁止继续补 episode、合并 strata、改阈值或把自然分类提升为成功。

它没有排除什么

它没有排除：

一个训练时真正向 low executor 提供语义创建压力的全新 C1 replacement；

一个显著改变 skill-to-recurrent-dynamics 路径的执行器替换，但那将是新的 actor-conditioning 假设，而不是当前 C2 的“小 event-context 添加”；

hierarchy 在跨 roster、跨 lifetime、迁移、长期 commitment 或样本效率上的潜在价值；

原 HMASD 中个体 posterior-to-intrinsic-reward 功能的动态 roster 版本；

新算法在其他 training seeds 上的表现。

结果的正式 claim ceiling 本身也只涵盖当前 checkpoint、当前 testbed、action dependence、12-step persistence、stratified stability 与 natural overlap，不涵盖 environment-independent semantics、transfer、cooperation、hierarchy superiority、commitment advantage、credit success 或 seed robustness。

组合权重更新

当前排序应更新为：

C3 显著领先。 Stage B 直接策略解决任务，而 Stage C hierarchy 和当前标签没有实质性执行对象。

C1 作为“缺失创建压力”的解释相对上升，但具体 C1 算法仍未经支持。 这是 diagnosis weight 上升，不是某个 discriminator 方案已经被验证。

C2 降为 parked/dormant。 没有具体证据显示失败局限于 join、rejoin、age 或 event boundary。

SMDP credit 关闭。 只有新的训练机制先建立 material、persistent、natural semantics 后，才可能重新进入组合。

这与提交中的当前 portfolio 边界一致。

2. Competing architecture judgment
C3 — 当前经验领先者和强制 ordinary-MARL null

C3 不是一个弱的“flat MLP”基线。Stage B 直接策略没有 skills、high actions 或 intrinsic reward，但具有：

每 lifecycle recurrent state；

active-set sum/count context；

primitive-time autoregressive action ordering；

later agents 可看到 earlier primitive-action counts；

centralized active-set critic；

exact replay 与 schema-3 checkpoint。

源码明确排除了 skill、高层动作和 intrinsic reward，同时 primitive actor 每一步根据 active-set context、自己的 recurrent state 以及本步已执行动作前缀做决策。

该策略在注册预算下达到 deterministic P/S/U=1/0.998210/0.999105、stochastic U=0.986654。所以对任何 hierarchy 的最强直接反对是：

recurrent direct policy 已经能以 primitive-time coordination bandwidth 内化“持续者/反应者”的行为结构；显式 z、KEEP/SET 和 semantic objective 可能只是把普通 recurrent representation 外显化，而没有增加可迁移能力。

C3 尚未证明 hierarchy 在最终目标上永远无用。它没有测试技能冻结后复用、跨任务重组、比 primitive recurrence 更长的 commitment、样本效率优势或规模变化下的 representation compression。因此它是经验第一和强制 null，不是最终普遍结论。

C1 — 唯一值得序列化的当前 hierarchical implementation hypothesis

Stage C 的 low actor 已经有明确的 z 参数路径：MLPBase(o) 后由 one-hot skill 生成 FiLM 参数，再进入 recurrent layer 和 action head。Iteration 4 检出的微小 TV 也证明该路径并非断线。与此同时，Stage C 的 intrinsic reward/count 均为零，low policy 只接受 sparse terminal external reward。最简因果解释因此不是“再加 context”，而是当前路径从未被要求把不同 z 训练成实质性行为过程。

C1 的最强 ordinary-MARL objection 是：

一个 posterior/contrastive objective 很容易创建任意 action modes，但这些 modes 可能与合作任务无关；C3 可以在内部学习同样的行为分解而不承担离散 label、selector 和非平稳 intrinsic reward 的成本。

原 HMASD 论文自己也显示了这一风险：其 q_d/q_D intrinsic rewards 促进可区分状态/观测访问，但作者同时观察到许多被发现的 diverse skills 不贡献任务 reward。其 ablation 支持 intrinsic pressure 在原固定 N 设置中的作用，却不证明这种目标单独导致成功或能原样迁移。
NeurIPS 论文集
+1

因此，C3 仍排第一，而 C1 是下一次执行的最佳候选。这不是自相矛盾：选择 C1 是因为它对当前未解决因果不确定性的预期信息增益最高，而不是因为它已有最多成功证据。

C2 与 credit

C2 当前不应作为 implementation candidate。Iteration 4 没有发现“整体上 material、只在 event strata 中不稳定”的模式，而是发现所有 pair 的基础 intervention effect 就低于 materiality floor。若未来要把 skill conditioning 改成 skill-indexed recurrent dynamics、hypernetwork 或在 SET 时改变 hidden transition，那已经是新的 executor-capacity replacement，不能冒充本轮的“minimal event context”。

SMDP credit 同样不应保留为当前实现分支。只有 C1 先产生稳定、自然使用的技能，但 external-only high selector仍不能选对，credit 才重新变为可识别假设。此前 disposition 对这两者的边界已经明确。

3. Minimal semantic-creation design, if authorized

证据支持一个可辩护的最小 C1 设计。我建议将其冻结为描述性的 “C1 条件过程残差语义”，而不是恢复原 q_d/q_D 或创建一组新模块菜单。

3.1 Retain / delete / replace / add

Retain

schema-3 variable-roster lifecycle runtime；

anonymous active-only execution；

genuine join、temporary leave、rejoin、terminal leave；

survivor recurrent continuity；

discrete individual skill z_i；

exogenous opportunity 与 combined categorical KEEP/SET；

当前 pi_low(a_i|o_i,z_i) 的 FiLM–RNN actor；

low physical-time PPO；

high owner-event gamma^Delta credit；

exact action masks、stored old log-probabilities、policy-version boundaries 和 fail-closed checkpoints。

Delete

下一候选中的 F1 applied-working-prefix treatment。Stage C 已证明 prefix distribution change 没有 task transport，而 semantic object 尚不存在；在第一次 C1 比较中保留它只会增加不可归因复杂度。

任何 team latent、q_D、team discriminator、learned timing、scheduler、graph/field/slot stack。

用自然标签分类率作为训练成功判据。

Replace

以 F0 initial-summary event selector + semantic low executor 取代 Stage C 的“F1 selector + external-only low learning”。

高层仍负责 variable membership 下的 KEEP/SET 和 realized lifetime，但本次 semantic treatment 不改变其 objective。

Add

只增加一个 process posterior module、一个冻结的 rollout scorer copy，以及每 lifecycle 的短 process-window ledger。它是缺失 semantic objective 的替换物，不是与 F1、q_D、event context 和新 credit 同时堆叠。

3.2 Semantic random variables and objective

对 focal lifecycle i 的 window w 定义：

Z
i,w
	​

∈{1,…,K}

为 window 内不变的当前 skill。

C
i,w
	​

=(o
t
0
	​

i
	​

,h
t
0
	​

i
	​

)

为 window 开始前的 local observation 和 low actor hidden state，二者都从 policy path detach。

X
i,w
	​

=[onehot(a
t
i
	​

),Norm(o
t
i
	​

)−Norm(o
t
0
	​

i
	​

)]
t∈w
	​


为最多 12 个连续 active transitions 的局部行为过程。它不含 centralized state、reward、return、role、success、contact、lifecycle key、membership epoch、age 或 duration scalar。M
i,w
	​

 是 padding/valid mask，只用于 sequence aggregation 和 nuisance conditioning。

使用一个共享参数的 posterior：

c=E
c
	​

(C,M),p=E
p
	​

(X,M)
q
ϕ
	​

(z∣X,C,M)=softmax(W(c+p))

并使用相同 decoder 和 context tower、把 process embedding 置零得到 capacity-matched context/length baseline：

b
ϕ
	​

(z∣C,M)=softmax(Wc).

Estimator loss 为：

L
process
	​

=−Elogq
ϕ
	​

(Z∣X,C,M)−Elogb
ϕ
	​

(Z∣C,M).

训练 minibatch 在 skill 与有效 window length 上平衡。这样 mask、短/长 window、selection context 或 start hidden 中可预测的 label occupancy 会同时被 b
ϕ
	​

 吸收；只有加入行为过程后增加的 label evidence 才能产生 semantic score。

冻结 scorer 参数 
ϕ
ˉ
	​

 在一个 rollout 内不变，定义：

s
i,w
	​

=clip(
logK
logq
ϕ
ˉ
	​

	​

(Z
i,w
	​

∣X
i,w
	​

,C
i,w
	​

,M
i,w
	​

)−logb
ϕ
ˉ
	​

	​

(Z
i,w
	​

∣C
i,w
	​

,M
i,w
	​

)
	​

,−1,1).

对 window 中每个 active transition 分配：

r
i,t
int
	​

=β
∣w∣
s
i,w
	​

	​

,t∈w,

其中 β 是计划中一次冻结的单一常数，不是 sweep 参数。除以 ∣w∣ 后，一个 window 的总 intrinsic credit 不随其长度增加；age、duration 或“活得更久”不会成为 reward target。

Low reward 为：

r
i,t
low
	​

=r
t
env
	​

+r
i,t
int
	​

.

High event policy 仍只接收注册的 external SMDP return：

R
i,n
H
	​

=
r=0
∑
Δ
i,n
	​

−1
	​

γ
r
r
t
i,n
	​

+r
env
	​

.

因此 semantic reward 不会奖励 KEEP、不训练 lifetime selector，也不会伪装成 high-level credit。

3.3 Exact data and segment ownership

当前 low ledger 已保存 lifecycle/epoch/policy version、physical time、local observation、skill、primitive action、old log-probability、actor hidden before、critic hidden 和 exact critic sources，足以在不读取新任务字段的情况下构造上述过程窗口。

窗口必须满足：

单一 lifecycle；

单一 skill；

单一 policy version；

只包含 active execution；

非重叠，最多 12 active steps；

每个 low transition 只属于一个 window。

边界规则：

KEEP： 当前 window 继续。

SET： 旧 window 关闭，新 skill 开新 window；现有 low hidden 不重置。

其他成员 join/leave/event： survivor 的 window 不关闭。

temporary leave： 当前 partial window 关闭；skill 和 low hidden 按现有 runtime 冻结；absence 不计入长度。

rejoin： 以恢复的 skill 和 low hidden 开新 window，不把 inactive gap 输入 posterior。

terminal leave / episode terminal： 关闭 partial window。

PPO update boundary： 关闭所有当前 window；任何 estimator、reward 或 actor row 都不得跨 policy version。

当前 runtime 已经按 lifecycle、membership epoch 和 policy version 关闭 low chunk，并在 temporary、terminal 和 rollout truncation 上建立独立 bootstrap/trace 边界；新 semantic ledger 应复用而非重写这些所有权规则。

3.4 Tensor flow, recurrence and gradients

数据流为：

active local rows
  -> detached (start observation, start low hidden)
  -> detached local action/observation process window
  -> online process posterior φ
  -> frozen rollout scorer φ_bar
  -> detached scalar window score
  -> length-normalized low intrinsic rewards
  -> existing low PPO / low critic

梯度边界：

L_process 只更新 online process posterior。

Observation、action、low hidden 和 z 在 estimator update 中全部 detached；posterior CE 不反向训练 actor、high selector 或 skill embedding。

使用 frozen 
ϕ
ˉ
	​

 计算的 reward 再次 detached。

Low actor 只能通过其已记录 primitive-action log-probability和 low PPO advantage 接收 semantic gradient。

High selector、event critic 和 KEEP/SET logits 不接收 intrinsic advantage。

一轮 low PPO 与 posterior update 完成后，才把 online ϕ hard-copy 到下一 rollout 的 
ϕ
ˉ
	​

。

Posterior 数据每次 PPO update 后清空，不跨 policy version replay。

这保留了现有 low actor 的 skill-FiLM→RNN 路径，而不是同时更换执行器容量。当前 actor 确实由 local observation base、skill one-hot FiLM、RNN 和 action head组成。

3.5 Probability, clocks, masks and checkpoints

Probability。 Process posterior 不采样环境动作，因此不增加 behavior-policy probability factor。High probability 仍是当前 exact combined categorical KEEP/SET；low probability 仍是 primitive-action probability。Membership events、exogenous opportunities、semantic-window closure 和 posterior outputs都没有 actor ratio。

Clocks。

High：owner-specific event clock 和 gamma^Delta。

Low：physical primitive clock。

Semantic：只在 focal lifecycle active 时推进的 active-step counter。

Inactive leave time、其他成员 event 数和 wall-clock age 不进入 score。

Masks。 Posterior只消费 active rows。Padding mask同时进入 process posterior 和 context baseline，防止 mask/length 单独解决标签。Routing keys、member IDs 和 roster slots不得进入 tensor。

Checkpoint。 Schema 必须新增并严格恢复：

online process posterior；

frozen rollout scorer；

posterior optimizer；

posterior normalizer；

posterior sampler RNG；

每 lifecycle open semantic window；

window start context、skill、policy version 和 valid mask。

其余现有模型、optimizers、normalizers、lifecycle table、opportunity/order/action RNG、open traces、pending membership transaction、collector/environment snapshot仍必须完整恢复；缺项为 hard load error，而不是重新初始化。现有 checkpoint contract 已对这些 runtime 状态采用 fail-closed 语义。

3.6 Retired-line and HMASD boundary

该设计不是：

R29： 不直接最大化单步 I(z;a
t
	​

∣o
t
	​

)，也不直接正则化不同 skill 的 action logits；目标是 context/length-residual 的多步局部过程 posterior。

R31-CFEI： forced branches只用于最终审计，不产生训练 reward。

R32-IFEPG： 不通过 individual effect 对动作做直接微分；actor只接受 detached reward 的普通 PPO gradient。

R33-IRSC： 不计算 roster complementarity、intervention contribution 或 team composition reward。

task shaping： posterior 不读取 reward、return、role、success、contact 或额外 task diagnostic。

原 HMASD 中保留的是两项功能：

pi_low(a_i|o_i,z_i) 的 individual skill-conditioned execution；

posterior 先通过监督 loss 学习，再以 detached log-posterior 型 intrinsic signal 训练 low policy。

原论文的 q_d(z_i|o_i,Z) 以局部 observation 和 team skill 预测 individual skill，并把 log q_d 加入 low-level reward；本设计把其单时刻、固定-N、team-conditioned 形式替换为 focal variable-length process posterior。
NeurIPS 论文集
+1

q_D 必须继续关闭。这里没有一个已经证明 actionable、roster-invariant 的 sampled team latent；恢复 q_D 只会产生一个无行为所有权的 team-looking classifier。仓库先前的 team-intent 证据已经显示 latent 可在 assignment 上近乎 inert，并明确禁止在 actionability gate 前启用 q_D reward。

4. One discriminating evidence source
单一序列化比较

建议一个一次性、三臂、同合同实验，不是一串小 gate：

C1-semantic-on： 上述 F0-shell + process-residual intrinsic objective。

C1-semantic-off： 完全相同的 F0 shell、posterior、posterior optimizer、采样和计算，但令 β=0。这是 strongest mechanism-matched comparator。

C3-direct： 注册 Stage B direct primitive-AR architecture，作为 mandatory ordinary-MARL comparator。

C1 两臂应 byte-equal 初始化，共享环境、任务 ledger、opportunity/order、action-uniform streams、网络宽度、high/low optimizer counts 和 evaluation。Estimator 使用独立冻结 RNG，semantic-off 必须在 policy/RNG/replay 上约化为无 semantic treatment 的 F0。

Minimum sufficient budget and placement

使用已经证明足以让 C3 学会任务、也足以让 Stage C 暴露失败的原注册 testbed 与 exposure：

16 environments；

horizon/rollout 80；

250 outer updates；

每臂 320,000 environment transitions；

PPO4；

hierarchical arms 各 1,000 high 和 1,000 low optimizer steps；

posterior 也固定为 1,000 update steps，semantic-on/off完全相同；

原注册 initialization、training ledger、event/order、action、evaluation 和 bootstrap seeds；

update 0 与 update 250 固定评价，不选 best checkpoint。

该预算已经被冻结为当前 learned-arm exposure；有效失败不得触发 budget、seed、threshold、reward 或 model rescue。

不应先移到 UAV、增加新 task 或引入 unseen schedule。当前最小问题是：这个机制能否在已知可学习的 variable-roster carrier 上创造 material executable semantics？

Metrics
A. Material executable semantics

复用 Iteration 4 的冻结审计：

reference fold 选择 maximum-energy unordered pair；

inference fold 上：

same-input action-TV LCB >1/12；

12-active-step forced process-effect LCB >1/12；

两个选中技能各占至少 10% natural active steps；

natural windows 与 forced centroids有正的 held-out overlap margin；

context/mask baseline 与 matched-shuffle residual LCB >0。

这里必须使用 LCB 超阈值，而不是仅仅“不再满足 UCB 低于阈值”。

B. Task relevance

复用现有 Stage C task-access 条件：

deterministic U≥0.60；

P≥0.55；

S≥0.55；

final-minus-zero utility LCB >0.10。

此外，semantic-on 相对 semantic-off 的 paired utility-gain LCB 应 >0.03。C3 的 deterministic/stochastic task result必须同时报告，但在这个 ceiling-saturated toy 上不要求 C1 超过 C3才能证明 semantic creation。现有 task thresholds 与 applied-treatment utility threshold来自冻结合同，不应事后修改。

C. Limited stability and corruption checks

只保留与具体失败模式直接相关的检查：

Context/length shortcut： 同结构 context+mask baseline 和 age/duration-matched shuffle。

R29 reduction： action-only posterior若已解释全部 residual，则该机制按 retired action-information reduction 失败。

Task leakage： reward、return、role、success/contact 和非 policy-visible diagnostics必须不在数据中；评价时对显式 task-progress coordinates 做 corruption，semantic materiality若消失则不得称 environment-agnostic。

Gradient leakage： high intrinsic count、high intrinsic advantage 和 posterior-to-high gradient必须严格为零。

Probability/state validity： exact low/high replay、mask equality、policy-version separation、checkpoint round-trip 和 finite updates。

这些是同一个实验的 M0/M1 检查，不是允许失败后继续追加的独立研究 gate。

Outcome-dependent portfolio updates

INVALID。
只修具体 wiring、replay、RNG、gradient leakage 或 checkpoint defect，保持科学合同不变。

Valid no-materiality：action/effect UCB 仍低于 1/12。
永久退休这一 exact C1 process-residual objective。C3成为当前 substrate 上唯一 active implementation；C2 与 credit继续关闭。不得调整 β、增加 seed、延长预算、改变 window 或降低 threshold。其他 C1 思路只有在出现独立新证据时才能重新进入 portfolio，失败本身不自动产生 successor。

Material forced effect，但只由 action-only、length、context 或 task-progress corruption解释。
按 prohibited shortcut/retired-line reduction 退休 exact C1。C3加强；C2和 credit不开放。

Material、稳定 forced semantics，但无 natural overlap。
说明 executor在强制时可表达模式，但当前 natural assignment/execution没有使用它。C1仍未通过 coherent algorithm test；credit继续关闭，因为不存在自然执行对象。只有当失败明确集中在 SET/rejoin 边界时，C2才可被重新提名。

Material、稳定且自然使用，但 task access或 semantic-on 对 semantic-off 的增益失败。
支持“C1能创建行为语义”，但同时支持“这些语义任意或与任务无关”。C3仍为经验领先者。Conditional SMDP credit可重新成为 portfolio hypothesis，因为此时首次存在可被选择的稳定对象；这仍不授权 credit 实现或 hierarchy integration。

Material、稳定、自然使用，并通过 task access及 semantic-on 对 semantic-off 增益。
C1上升为成功的 testbed-level hierarchical mechanism；C3仍是 mandatory null。C2进一步降权，credit无需作为当前解释。下一项证据应转向真正 load-bearing 的 transfer/commitment comparison，而不是继续优化本 toy。

Stop and integration boundary

一个有效 semantic null 或 shortcut fail，永久关闭本 exact C1实现。

一个 semantic-only pass但 task fail，不允许集成，只允许重新权衡 credit/alignment。

即使 semantic + task pass，也不允许直接集成 UAV 或声称 hierarchy superiority。

后续集成必须在 capacity、information、environment exposure 和 policy-update exposure匹配的直接 active-set controller上，展示 transfer、sample efficiency、unseen membership/lifetime 或 genuine long-horizon commitment中的 material advantage。

当前实验不能把“有技能”升级成“hierarchy有独特价值”。

5. Final recommendation
Ranked live portfolio

C3 — direct anonymous active-set control。
当前证据最强、经验领先、mandatory ordinary-MARL null。

C1 — conditional process-residual semantic creation。
当前最值得序列化的 hierarchical implementation hypothesis；选择依据是信息增益，而非已有成功权重。

C2 — minimal event-context execution。
Dormant/parked。当前结果没有 event-local instability 证据，不应参与下一实现。

Conditional SMDP credit。
Closed。只有 C1 先产生 material、persistent、natural semantics后才重新进入。

One next serialized implementation

建议序列化上述 C1 semantic-on / C1 semantic-off / C3-direct 单合同比较。不建议继续 checkpoint reanalysis，不建议恢复 q_D，也不建议先做 credit、event context、continuous latent、learned timing或参数 sweep。

Most important unresolved causal uncertainty

最重要的不确定性不是“现有标签有没有一点信息”，Iteration 4 已经回答了这一点。真正未决的是：

一个不读取 task semantics、对 context/length 做 residual、只通过 detached low-policy reward作用的 process posterior，能否把现有可表达但微弱的 z 路径训练成 material、持续且自然执行的行为模式；若能，这些模式是否比 direct recurrent control多提供任何任务相关价值。

Exact claim ceiling on a full pass

即使上述比较全部通过，最高只允许声称：

在该固定 generic-SHORT dynamic-roster testbed、该单一注册 training seed 与 320k exposure 下，条件过程残差的个体语义目标，相对于 architecture-matched semantic-off hierarchy，因果性地创建了至少两个达到预注册 materiality、持续 12 active steps、通过 nuisance controls且被自然使用的 skill-conditioned behavior modes，并恢复或改善了注册 task access。

仍不得声称：

environment-independent semantic success；

training-seed robustness；

cross-task或cross-domain transfer；

cooperative complementarity；

variable-lifetime superiority；

credit success；

q_D/team-skill reconstruction；

HMASD parity；

hierarchy优于 C3；

UAV-scale scientific value。

本结论仅为收敛审阅建议，不构成代码、训练、算力、晋级、退休或唯一研究路线的授权。
