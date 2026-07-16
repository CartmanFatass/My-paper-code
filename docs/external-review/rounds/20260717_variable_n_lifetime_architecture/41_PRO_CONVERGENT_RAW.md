1. Convergent verdict
ACCEPT_WITH_CORRECTIONS

窄理由： Codex 综合正确地把“活动成员承诺集合 + 事件 ledger + duration-correct credit”识别为共同正确性骨架，也正确地将真正的算法分歧缩减为：

给定同一匿名 active-set context 后，成员编辑是否仍需 prefix-conditioned 联合分布
	​


但还需要三项收敛修正：

F2 不应继续作为独立架构名保存。 它的条件独立技能选择部分就是强化后的 ordinary-MARL reduction；其 learned hazard 部分应并入 deferred point-process family。

首版表示不应预装 sparse graph、fixed slots、critical residual 或 Hybrid Field-Slot。 R54 只提供了对一个具体 full-set 模型和一个固定槽压缩的负证据，不能证明另一套复杂表示栈是默认答案。

现在不应直接授权训练或新 testbed。 R53 的 Git-visible 结果证明 replay 检查和最终能力存在，但保留包没有最终权重与逐决策 context，不能执行所提议的 alternate-prefix 零训练重分析。

证据事实

R41B 证明 fixed-N、fixed-clock 的原始 HMASD 在 Alice–Bob 上可学习：最终 win 0.89、key0/key1 0.97/0.92，并通过精确 replay。

R42 的具体 incumbent-roster renewal 既损害服务，又几乎保持同步：treatment-minus-fixed win CI 为 [-0.17,-0.03]，discordance 0.10，full-sync SET 0.90。

R45/R46 都显示“动作相关价值信息可以存在”，但没有形成所需的同一检查时刻异号续期结构；这削弱的是已测试的 renewal-credit 假设，不证明异步架构普遍不可能。

R47/R48 分别否决了一个 task-blind spectral process view 和 skill-boundary hidden reset；都没有测试 episode-internal roster。

R50–R53 没有识别 shared-variable-N 相对 specialist 的因果收益。R50 的 specialist prerequisite 失败，而 shared 数值较强；R51/R52 的 specialist access 失败；R53 多数最终能力指标通过，但注册的学习增益/零基线前提失败，因此 shared transport 被隔离而非否定。

R49 只证明匿名、置换/填充不变的 roster 表示可以与 applied prefix、精确 replay 共存；没有学习证据。

当前三个竞争性因果假设
假设	核心主张	当前证据状态
F0 — active-set scheduled ordinary MARL	生命周期路由、active-set encoder、per-member opportunities 和 γ
Δ
 credit 已足够；给定共享 context 后，成员编辑近似条件独立	强零假设，未被击败
F1 — exchangeable event-frontier editor	并发 commitment edits 存在不可约 later-on-earlier 条件依赖；working-roster prefix 承载真实合作信息	最合理的 leading family，但未识别
F
time
	​

 — learned event-time / point process	固定或外生 opportunity 本身是瓶颈，必须学习 survival/termination intensity	缺乏直接证据，保持 deferred

因此现在既不能停止全部 skill-based 路线，也不能把 F1 当成已经获证的算法。最诚实的状态是：

F0 与 F1 尚未区分；event-time learning 更下游。
	​

2. Claim adjudication
1. “匿名动态 roster 与 autoregression 根本冲突，除非 learned pointer 采样顺序”
REJECT

匿名集合并不禁止 autoregression。可以在每次 event frontier 上外生采样一个均匀随机排列：

q(σ∣F
t
	​

)=
∣F
t
	​

∣!
1
	​

,

记录该排列，并在 PPO replay 时 teacher-force 同一排列。q 与参数无关，在行为概率审计中可显式保留，在 PPO ratio 中精确抵消。learned pointer 只是可选机制，不是概率正确性的必要条件。R49 已经证明匿名 active-set 表示、applied prefix 和精确 replay 在接口层可以共存。

真正风险是：

order-induced semantic leakage；

某些 lifecycle key 总是更早进入 prefix；

顺序方差；

把外部路由 key 偷偷变成永久 policy slot。

这些是 compatibility 和统计风险，不是数学不可能。

2. “ACAC 是该目标的 definitive SMDP-credit solution”
MODIFY

ACAC 是目前最强的 duration-credit 参考，因为它明确区分：

γ
Δt

的物理时间折扣与按宏事件次数推进的 λ trace，并使用 agent-centric event histories。

但它不是完整解：

roster 在启动时固定；

不定义 JOIN/LEAVE/REJOIN；

不定义 survivor state；

不定义 learned event-time survival likelihood；

不保留 HMASD skill/cooperative assignment 语义。

正确裁决是：

吸收 ACAC 的时间/trace 语义，不吸收其 fixed-roster 外壳。
	​

3. “IARO 证明同步会摧毁 heterogeneous-lifetime utility”
REJECT

IARO 的全员投票、同步执行、共同终止和统一 hard stop 与 per-member T
i
	​

 目标相反，因此是有价值的设计警告和同步反例。但其论文没有做本项目所需的因果比较，不能证明所有 barrier coordination 都会降低异质寿命效用。

它支持的窄结论是：

不要让最慢成员或全员共识重新成为默认 renewal barrier。
	​


不是普遍不可能性定理。

4. “Hybrid Field-Slot 是当前默认 representation”
REJECT

R54 中 full-set reference 已随 N 严重退化：

exact-roster success：约 0.633 at N=8；

0.137 at N=16；

0 at N=32,64。

固定 8 slots + 2 residuals 的 hybrid 没有解决 critical-member inclusion 或 held-out-N 问题。

但这也不证明所有 global attention 或压缩都无效。正确起点是最小 permutation-compatible encoder；只有出现明确的 aliasing 或 scaling 证据后，才增加 graph、slot 或 exact residual。

5. “event ownership、active-set exchangeability 和 duration-correct credit 是正确性基础设施，而非不可约算法创新”
ACCEPT

这三者必须同时用于 F0 和 F1：

lifecycle table；

active-only packing；

opaque routing key；

exact mask/order/prefix replay；

γ
Δ
 return；

macro-event λ boundary。

若只给 F1 使用这些，而让 ordinary baseline 使用错误的同步 buffer 或 dummy-agent credit，就会把工程正确性误报为算法收益。Codex 对这一点的综合是正确的。

F1 相对 F0 唯一可能不可约的算法内容是：

learned prefix-conditioned joint edit distribution.
	​

6. “保留的 R53 artifacts 支持 no-training prefix audit”
REJECT

R53 结果 JSON 记录了：

dynamic mask replay；

prefix replay；

previous-relation replay；

sample log-prob replay；

均为精确，但这只是实验时的结果证据。

Git-visible 保留包没有最终模型权重，也没有逐决策 observation、hidden、legal support、working prefix 等 context，无法重算：

π
θ
	​

(⋅∣s,p)vsπ
θ
	​

(⋅∣s,p
′
).

因此该分析至少需要重新生成策略与决策 ledger，不能称为零训练现有重分析。

7. “identity-free recorded random event-frontier order 可定义 exact teacher-forced autoregression，而无需永久 slots”
ACCEPT

条件是：

order 在当前 event frontier 上均匀采样；

order RNG 外生且与 policy 参数无关；

opaque lifecycle key 只用于 collector 找回成员 state；

order 与 sampled mask、pre-prefix、post-prefix 一起存储；

replay 使用完全相同的 frontier、order 与 working roster；

在任意成员重标号下，联合分布同步重标号。

完整增广行为概率是：

p
θ
	​

(σ,E
t
	​

∣C
t
	​

)=
m!
1
	​

j=1
∏
m
	​

π
θ
	​

(e
σ
j
	​

	​

∣C
t
(j−1)
	​

,F
t
	​

,σ
j
	​

).

PPO ratio 中 1/m! 精确消去。无需 learned pointer，也无需 permanent member slot。

3. Final architecture contract
Leading family
F1 — Exchangeable Exogenous-Opportunity Event-Frontier Commitment Editor
Ordinary-MARL reduction baseline
F0 — Active-Set Scheduled Recurrent MARL

两者必须共享全部 lifecycle、encoder、credit、low actor、reward 和 collector 基础设施；唯一干预是：

F0:
prefix-independent learned logits
+ prefix-dependent deterministic legality mask if needed

F1:
prefix-conditioned learned logits
+ the same legality mask
3.1 Active member and commitment state

Collector 维护：

L[κ
i
	​

]=(h
i
	​

,z
i
	​

,τ
i
	​

,status
i
	​

),

其中：

κ
i
	​

：opaque lifecycle key，只用于路由；

h
i
	​

：成员 recurrent state；

z
i
	​

：当前 individual skill；

τ
i
	​

：累计的活跃执行时间；

status：active、temporarily absent 或 terminal。

Policy 看不到 κ
i
	​

。Policy-visible member token 为：

u
i
	​

=[x
i
	​

,emb(z
i
	​

),log(1+τ
i
	​

),b
i
new
	​

,b
i
rejoin
	​

],

其中 x
i
	​

 是正常 decentralized/member-relational policy feature。不存在 permanent agent-ID、slot-ID 或 lifecycle-key embedding。

首版 active-set context 使用：

g(C
t
	​

)=[
i∈A
t
	​

∑
	​

ϕ(u
i
	​

),log(1+∣A
t
	​

∣)].

这是 DeepSets-style sum/count encoder：

permutation compatible；

active-only；

不绑定 N
max
	​

；

不预装 graph、slots、critical residual 或 team latent。

它不是“DeepSets 已被证明充分”；它只是最小、可归约的初始合同。

3.2 JOIN、LEAVE 和 REJOIN

Genuine JOIN

collector 创建新 κ；

h=0；

z 未定义；

τ=0；

新成员立即进入 event frontier；

action support 只有 {SET(z):z∈[K]}。

Temporary LEAVE

外生事件，无 actor log-prob；

当前 member event trace 在 leave 时形成 critic-only truncation；

h,z,τ 被冻结保存；

inactive 期间 τ 不增加；

survivor 成员的 hidden、skill 和 age 不变。

REJOIN

相同 κ 恢复保存的 h,z,τ；

rejoin 本身是外生结构事件；

同时创建一次 policy opportunity，支持 KEEP 或 SET；

policy 不看到 κ，只看到恢复后的成员 token 与 rejoin 标志。

Terminal LEAVE

关闭该成员的 open event trace；

bootstrap 为零；

删除 lifecycle state。

这一区分必须由环境/collector 的外生 lifecycle contract 指定，不能由 policy 猜测未来是否会回来。

3.3 Event-time ownership

首版选择：

Exogenous policy opportunities

事件时间由 collector/environment 的 task-agnostic readiness schedule 产生并完整记录。Policy 不学习何时触发事件，因此：

silent physical steps没有 survival log-prob；

JOIN/LEAVE/REJOIN 没有 policy log-prob；

policy 只拥有 opportunity 上的 skill commitment action。

这避免在同一首版架构中同时引入：

learned survival；

termination hazard；

integrated intensity；

competing risks；

censoring likelihood。

Heterogeneous lifetime 由不同成员在不同 opportunities 上连续 KEEP 或 SET 产生，而不是 duration action product。

3.4 Event action support

对已有 incumbent skill z
i
	​

：

E
i
	​

(z
i
	​

)={KEEP}∪{SET(z):z

=z
i
	​

}.

若共有 K skills，support 大小仍是 K，不是 K+1 或 K×D。

对 genuine JOIN：

E
i
join
	​

={SET(z):z∈[K]}.

使用一个 combined categorical action。没有独立 duration head，也没有未登记的 post-sampling repair。

3.5 Concurrent edits and exact probability

外部 membership events先应用，得到 pre-policy active set。令本次有 policy opportunity 的成员集合为 F
t
	​

，大小 m。

均匀采样并存储：

σ
t
	​

∼Uniform(Perm(F
t
	​

)).
F1
p
θ
	​

(E
t
	​

,σ
t
	​

∣C
t
	​

)=
m!
1
	​

j=1
∏
m
	​

π
θ
	​

(e
σ
j
	​

	​

∣u
σ
j
	​

	​

,h
σ
j
	​

	​

,g(C
t
j−1
	​

),M
t
j−1
	​

).

每个 token 执行后立刻更新 working commitment set：

C
t
j
	​

=apply(C
t
j−1
	​

,e
σ
j
	​

	​

).

后续 token 看到已经应用的 skill edit、当前 age 与仍未处理成员的 incumbent skill。

F0

F0 使用相同：

frontier；

random order；

action support；

hard legality mask；

event ledger。

但在共同合法 support 上，learned logits 不读取 applied prefix：

ℓ
i
F0
	​

=f
θ
	​

(u
i
	​

,h
i
	​

,g(C
t
0
	​

)).

若容量或互斥约束需要顺序化，working prefix 只改变确定性合法 mask，不改变 common-support learned scores。

3.6 Replay ledger

每个 policy token必须存储：

lifecycle key，仅用于 routing；

event time；

frontier membership；

sampled σ；

token position；

pre-event active set digest；

pre-token working commitment set；

exact legal mask；

sampled combined action；

post-token working set；

old token log-prob；

old value；

recurrent state snapshot；

event owner；

physical elapsed time；

terminal、temporary-leave 或 policy-truncation boundary。

Replay teacher-forces同一 order、action、mask 与 applied prefix。禁止：

重采样 order；

重算不同 mask；

用当前 roster 代替 collection roster；

post-sampling conflict repair；

把 opaque key 输入网络。

3.7 Reward, return and macro trace

外部 reward 保持环境原生形式；本轮不增加 intrinsic 或 shaping。

对成员 i 的第 n 个 policy-owned event：

Δ
i,n
	​

=t
i,n+1
	​

−t
i,n
	​

,
R
i,n
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

若下一边界非 terminal：

bootstrap=γ
Δ
i,n
	​

V
i
	​

(C
t
i,n+1
	​

	​

).

若 terminal leave：

bootstrap=0.

λ 只在该成员的下一次 policy-owned event 上推进，不因：

silent primitive step；

其他成员的 event；

外生 membership event；

而虚构一次宏决策。ACAC 支持这种“物理时间控制 γ、成员事件深度控制 λ”的窄语义，但其 fixed-roster 外壳不迁移。

Temporary leave 在 leave 点做 critic-only truncation；不创建 actor ratio，不把 inactive reward 强行归给暂停成员。

并发 frontier 中，每个 token 使用其 event owner 的 advantage。token loss 按实际 frontier token 数求平均，避免梯度规模随 m 增长。

3.8 Recurrent-state boundary

active survivor：primitive low RNN 连续；

KEEP：不重置 hidden；

SET：更新 skill，hidden 连续；

temporary leave：冻结 hidden；

rejoin：恢复 hidden；

genuine new member：hidden 清零；

terminal leave：丢弃；

rollout/PPO policy-version boundary：open trace 用旧 critic bootstrap 截断，但 simulator/lifecycle state可继续；不得跨 policy version 复用旧 actor row。

3.9 HMASD functions retained and removed

Retain

skill-conditioned low policy：

π
l
	​

(a
i
	​

∣o
i
	​

,z
i
	​

);

persistent individual skill commitment；

later-on-earlier assignment function；

applied working-roster semantics；

task-blind skill-semantic requirement；

centralized cooperative value context。

Deliberately remove from the default architecture

separately sampled global team latent Z/g；

team-latent bridge；

team-code log-probability；

default team discriminator q
D
	​

；

team-code-conditioned classifier reward；

discrete duration head；

full-team shared renewal barrier。

项目已有证据表明一个后加的 sampled team intent 可以在 assignment 上近乎 inert，因此不能仅凭“HMASD 曾使用 team Z”就把新 team latent 当作必要模块。

这不是授权新的 intrinsic reward。已有 R29–R48 reward/classifier families 保持退休。保留的是“技能必须有行为语义”的功能要求，不是复活某个旧 scorer。

3.10 Computational cost

设：

N
t
	​

=∣A
t
	​

∣；

m
t
	​

=∣F
t
	​

∣；

hidden width 为 d；

skill 数为 K。

通过 sum encoder 和增量 subtract/add 更新：

time=O(N
t
	​

d+m
t
	​

(d+K)),
memory=O(N
t
	​

d).

没有固定 N
max
	​

 的 permanent policy slots，也不先形成 N
t
2
	​

 pair tensor。

3.11 Algebraic reduction boundary

若对所有合法 common support：

π
θ
	​

(e
σ
j
	​

	​

∣C
t
j−1
	​

)=π
θ
	​

(e
σ
j
	​

	​

∣C
t
0
	​

),

则 F1 的 learned distribution 退化为 F0。

若 prefix 只改变 hard mask，而共同 support 上 logits 不变，则 F1 只是可行性序列化基础设施，不能作为算法贡献。

F1 只有在下述行为成立时才有不可约内容：

Earlier applied edits materially change later common-support action distributions.
	​

4. Portfolio disposition
Final-capability map
Family	Episode-internal roster	Heterogeneous lifetime	Skill bottleneck	Joint learned coordination	Exact probability/credit	Status
F0 active-set scheduled MARL	✓	✓ via opportunities + KEEP/SET	可保留	条件独立；mask-only serialization	✓	必须保留的 ordinary baseline
F1 event-frontier editor	✓	✓	✓	prefix-conditioned AR over frontier	✓	唯一 leading research family
Point process	理论上 ✓	原生 ✓	可保留	可独立或 AR marks	需 survival/intensity/censoring	deferred，不进入首版
Replacement ledger
F0 — RETAIN AND STRENGTHEN

Replaces

fixed N
max
	​

 dummy-agent semantics；

synchronous fake high rows；

ordinary one-step credit。

Retains

shared recurrent actor/critic；

optional skill-conditioned low actor；

centralized training；

exact event ledger。

Adds

active-only packing；

lifecycle table；

survivor/rejoin continuity；

exogenous per-member opportunities；

duration-correct event return。

F0 吸收了绝大部分“正确架构基础设施”，防止把这些误报为 F1 的贡献。

F1 — RETAIN WITH CORRECTIONS AS LEADING FAMILY

Replaces

full-team synchronous refresh；

fixed roster slots；

full-roster decode when only a small frontier changes；

separate sampled team latent；

duration action product。

Retains

individual skill bottleneck；

applied-prefix HMASD cooperation function；

exact joint probability；

same lifecycle/credit spine as F0。

Adds

uniform identity-free event-frontier order；

learned common-support prefix dependence；

immediate working-commitment application。

F2 — MERGE; RETIRE AS A SEPARATE NAME

F2 的两部分应拆开：

条件独立 KEEP/SET mark policy → 已经是 F0；

learned termination hazard → 属于 deferred point-process family。

继续保存 F2 名称只会制造一个没有清晰边界的中间模块。

Deferred point-process family — DEFER

它只有在证据表明：

exogenous discrete opportunities themselves are the binding limitation

时才重新进入组合。

它将替换 opportunity clock，并新增：

log-survival；

termination intensity；

integrated hazard；

skill-mark probability；

censoring/competing-risk likelihood。

当前没有证据支持承担这一正确性与优化复杂度。

5. Evidence and R55 disposition
REPURPOSE

R55 原 fixed-membership、fixed-horizon toy 不应执行。它不同时暴露：

episode-internal join/leave/rejoin；

heterogeneous useful commitment durations。

其唯一有价值的问题：

later member 的 learned action distribution 是否在共同合法 support 上依赖 earlier applied edits？

应吸收到 F1 的不可约性定义，不再保留 R55 作为环境或编号实验。R55 原始状态本就只是 drafted/paused，且没有运行证据。

Selected next boundary
Architecture specification only, followed by implementation planning

现在不选择：

R53 reanalysis：必要 artifacts 不存在；

新 testbed：架构边界尚未完全闭合；

R55：不区分最终能力；

training：没有被授权。

两个会导致真实决策的 specification outcomes

Outcome A — F1 contract closes

若正式 specification 能同时证明：

no permanent identity；

exact augmented behavior probability；

exact teacher-forced replay；

external event ownership；

no unlogged resolver；

F0/F1 共享全部 correctness spine；

F1 存在明确的 common-support prefix-conditioned parameter path；

则下一动作是：

进入单一共享实现的 implementation planning；仍不自动授权训练。

Outcome B — F1 collapses or violates anonymity

若 specification 显示：

prefix 只能影响 hard mask；

learned logits 实际不读 applied prefix；

必须使用 semantic lifecycle IDs/permanent slots；

conflict resolver 不能进入 probability；

team latent 或多个表示栈成为不可避免依赖；

则：

\boxed{ \text{STOP_AT_ORDINARY_MARL_REDUCTION} }

并以 F0 作为当前最终架构解释，不再制造新的 AR toy gate。

6. Strongest ordinary-MARL objection

最小、最强的 ordinary baseline 是：

Active-Set Scheduled Recurrent MAPPO

它具备：

active-only ragged member tokens；

shared recurrent actor；

opaque lifecycle state table；

survivor/rejoin hidden continuity；

exogenous JOIN/LEAVE/opportunity events；

skill-conditioned low actor；

invariant sum/count context；

independent per-member KEEP/SET logits；

exact pre-sampling feasibility masks；

centralized active-set critic；

agent-centric γ
Δ
 return 和 macro-event GAE；

相同的 checkpoint、collector 和 replay ledger。

这已经覆盖动态 roster、不同 realized lifetime、技能执行和正确 credit。它与 F1 的差异不再是“是否支持异步/变量 N”；差异只剩：

F1 是否需要 learned later-on-earlier coupling。
	​


F1 必须展示的唯一不可约行为是：

在相同 active-set state、相同 focal member、相同合法 action support 下，仅改变 earlier applied edits，会稳定改变 later token 的 learned action ranking/logits，并且这种依赖带来超过 F0 mask-only serialization 的合作效用。

若做不到，F1 就只是把 ordinary MARL 串行化，复杂度和方差没有算法回报。

当前证据尚未证明这一行为。R41B 证明 HMASD 可工作，但没有做 AR-vs-independent 因果隔离；R53 又缺少重算 prefix dependence 的 artifacts。因此普通 MARL 反对意见目前仍然成立。

7. Authorized next action

唯一授权动作是创建并评审一份架构合同：

docs/research/designs/
VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md

该文档必须一次性冻结：

F0/F1 共享 active commitment schema；

JOIN/temporary-LEAVE/terminal-LEAVE/REJOIN 状态机；

exogenous opportunity ownership；

F0 与 F1 的完整概率方程；

uniform random frontier-order ledger；

exact mask/prefix teacher forcing；

per-member γ
Δ
 return 与 macro trace；

opaque-key permutation rule；

DeepSets sum/count 初始 encoder；

F1→F0 algebraic reduction theorem；

final-capability map；

replacement ledger；

fail-closed checkpoint/collector boundary；

能导致 “proceed to implementation planning” 或 “stop at F0” 的审阅条件。

该动作不授权：

训练；

新环境；

R55；

R53 artifact reconstruction；

intrinsic reward；

reward shaping；

team latent；

Hybrid Field-Slot；

sparse graph；

learned hazard；

hyperparameter search；

并行路线执行。

最终收敛状态是：

F1 remains the leading skill-based hypothesis, but F0 remains undefeated.
	​


当前最有信息量的动作不是再跑一个 gate，而是先证明 F1 在概率、匿名性和代数上确实是一种不同于 ordinary scheduled MARL 的架构。
