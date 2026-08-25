1. Design verdict
MODIFY_TESTBED_DRAFT
	​


理由：“动态 roster＋长期连续职责＋短期响应职责”的核心结构可以形成自然的并发重分工机会，但当前草案尚不能可靠地区分普通策略访问、技能瓶颈、F1 applied-prefix 价值和外生机会时钟限制；必须用一个有限、冻结的修正版合同闭合这些混淆。

本裁决不授权实现、训练或环境接入。

2. Causal graph and hypothesis audit
2.1 已建立的证据事实

当前 F0/F1 运行时已经机械实现并验证了 lifecycle ownership、JOIN/temporary LEAVE/terminal LEAVE/REJOIN、survivor continuity、active-only packing、token replay、物理时间折扣、严格 checkpoint resume，以及 F1 能够在手工构造的 common-support 情形下改变后序 token 的相对 logits。

F0 与 F1 的参数图、critic、low actor、credit、collector、随机顺序和机会时钟合同相同。唯一差异是：

F0:
F1:
	​

g(C
t
(0)
	​

),
g(C
t
(j−1)
	​

).
	​


也就是后序 token 的 learned scores 是否读取已应用的 working commitment set。

当前证据仍完全是手工 deterministic transaction trace。真实环境训练路径仍 fail-closed；测试明确要求在 collector 构造前抛出“deterministic transaction trace”边界。因此，当前代码不是一个已经可训练的 F0/F1 算法结果。

历史访问证据具有三种不同失败模式：

R51：没有一个正终局回报 carrier；

R52：stochastic return carrier 充分，但 specialists 的 deterministic joint mode 坍缩；

R53：最终策略能力达到 U=1，但随机初始化已经较强，注册的 zero-to-final learning-gain 门槛失败；

R54：即使读取完整 active set，full-set supervised reference 仍随 N 快速失效。

因此不能再使用单一“specialist prerequisite”或单一终局成功率解释所有失败。

R41B 仍证明原始 HMASD 在固定 N=2 Alice–Bob 上具有真实访问，但它没有动态 roster，也不能直接验证本轮 F0/F1。

2.2 推断与假设重排

四个假设不应被视为同一层级的并列候选。正确的因果顺序是：

task access→skill execution→{H0 versus H1}→conditional H3 diagnosis
	​

H0 — shared-context sufficiency

当前地位：主零假设，优先级最高。

F0 已拥有：

完整动态 lifecycle；

active-set sum/count；

owner-local recurrence；
-当前 commitment roster；

task/member observation；

duration-correct credit。

F1 只有在并发 frontier 的先前编辑会改变后序成员的最佳相对技能排序时，才有不可约价值。其余情况下 F1 按代数约化为 F0。

H1 — irreducible applied-prefix coordination

当前地位：可测试但尚无行为证据。

现有 positive control只证明参数路径存在，不能证明：

自然 rollout 会使用该路径；

路径会减少冗余角色；

路径会改善外部任务；

路径会形成有用 lifetime。

因此 H1 需要同时满足：

common-support distribution change+directionally useful composition change+task gain over F0.

只有第一项的手工 wiring 已建立。

H2 — skill-semantic / low-control bottleneck

当前地位：强上游竞争解释，不能作为普通 FAIL 后的事后借口。

新的 event low actor从随机初始化训练；当前实现只证明：

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

)

路径可运行和重放，没有证明不同 z
i
	​

 会自然形成不同持续职责。此前项目已经反复观察到 forced conditional capacity 不等于 natural skill formation。因此 direct ordinary policy 成功、F0/F1 失败时，H2 是首要解释之一，而不能直接归因于 prefix 或 timing。

H3 — exogenous-opportunity timing bottleneck

当前地位：降级为条件性诊断，不能独立发动 learned timing。

只有当以下证据已成立时，H3 才进入解释：

ordinary policy 能访问任务；

F0/F1 至少一方形成持续可执行技能；

F1 真实学到方向正确的 common-support prefix response；

失败显著集中在机会时钟无法在 deadline 前提供足够编辑机会的波次。

仅观察任务失败不能授权 learned hazard、point process 或 duration head。

2.3 区分假设所需的最小证据
观测结果	更新
Direct ordinary policy也失败	testbed ordinary access失败；H0–H3均不解释，退休环境
Direct成功，F0/F1技能探针失败	强化H2；F1 prefix问题尚未被测试
Direct成功，F0成功，F1无prefix/task增益	强化H0；退休H1，停在F0
Direct和技能基底成功，F1有prefix effect但无任务收益	H1未成立；检查冗余方向与条件性H3
F1有方向正确prefix response、减少冗余并超过F0	强化H1
上述均成立，但失败集中在时钟不可达波次	条件性强化H3；仍不授权learned timing
3. Launch-exact environment contract

修正版仍使用一个 Anonymous Dynamic Dual-Duty 非空间环境，但需冻结以下合同。

3.1 时间与 roster
episode horizon H = 80
initial active N   = 4

t = 0:
  4 genuine JOIN

t = 20:
  2 of the original members TEMPORARY_LEAVE

t = 40:
  those 2 members REJOIN
  + 2 new genuine JOIN
  active N = 6

t = 60:
  2 active members TERMINAL_LEAVE
  active N = 4

临时离开者和终局离开者由 membership RNG 独立、均匀采样；未来成员事件不进入 observation。Task RNG、membership RNG、opportunity RNG、frontier-order RNG 相互独立。

Policy-facing presentation 每个 primitive step 随机置换；lifecycle key 和 membership epoch 仅用于路由。

3.2 Primitive actions
a
i
	​

∈{IDLE,PERSIST,SHORT_A,SHORT_B}.

动作没有 hard role mask。重复服务合法，但不能获得额外工作量。

3.3 Persistent duty

环境维护：

persistent_owner
persistent_units

每一步：

若当前 owner 仍 active 且选择 PERSIST：

persistent_units←persistent_units+1.

否则，若至少一名 active member 选择 PERSIST，通过预生成、policy-independent 的 service-order ledger 选择一个新 owner；该 handoff step 不增加 units。

无人选择时 owner 置空。

owner 离开 roster 时立即置空。

其他同时选择 PERSIST 的成员是冗余服务。

终局：

P=min(1,
64
persistent_units
	​

).

这使长期由同一 lifecycle 维持 PERSIST 自然优于频繁交接，但不直接奖励 KEEP 或 skill age。

3.4 Short reactive waves

共有八个 waves。

candidate windows:
{0},
{9,10},
{24,25},
{32,33},
{40},
{49,50},
{64,65},
{72,73}

每个双元素窗口独立均匀选择一个 arrival time。八个 wave types 是：

4 × A
4 × B

的随机排列。

Wave 到达时，在 post-membership active roster 上定义：

R
w
	​

=N
w
	​

−1

个需要完成的短期 work units。

每个 lifecycle 在该 wave 中最多贡献一个 unit。贡献要求它连续两个 primitive steps执行与 wave type相符的动作：

SHORT_A或SHORT_B.
deadline = 4 primitive steps

切换动作、离开 roster 或 wave 更换会清零未完成的 local streak。多名成员可以并发贡献；同一 lifecycle 的额外重复不增加 units。

终局：

S=
∑
w
	​

R
w
	​

完成的short units
	​

.

因此 workload 随 episode 内 N
t
	​

 真正变化，而不是只改变 tensor 长度。

3.5 唯一外部奖励

所有中间 steps：

r
t
ext
	​

=0.

仅在 t=79：

r
79
ext
	​

=U=
2
1
	​

(P+S).
	​


这是新的 terminal task utility，不是 potential difference、中间 progress reward、skill reward、role reward 或 intrinsic reward。

结果必须同时报告 P 和 S，避免只优化一项即可通过。

3.6 Observation

每个 active member获得同一个18维匿名局部/公共向量：

t / 80
log(1 + N_t) / log(7)
persistent_units / 64
persistent_owner_exists
wave_active
wave_type_A
wave_type_B
wave_deadline / 4
short_units_remaining / max(1, wave_required)
completed_short_fraction
self_is_persistent_owner
self_short_streak / 2
self_already_contributed_to_wave
self_active_time_since_join / 80
previous_action_one_hot[4]

F0/F1 high token在此基础上按现有runtime加入：

skill embedding
log age
genuine_join
rejoin

Low actor只读取：

(o
i
	​

,z
i
	​

).

Direct ordinary policy读取同一个18维 observation，但没有skill、KEEP/SET或生命周期key。

Centralized critics可以读取：

全部 active member 的上述通用关系字段；
-当前 P/S task state；

boundary kind；

active count；

但不能读取未来membership或未来wave schedule。

4. Learnability and access attribution
4.1 单一证据源中的三个 arms

这不是三条并行研究路线，而是一个分层归因实验。

direct_active_set_primitive_AR

最强 ordinary-MARL task-access instrument：

每个 primitive step对全部active members运行一次记录顺序的primitive-action autoregression；

使用同一个active-set sum/count；

later primitive tokens看到已应用的primitive-action count prefix；

recurrent shared policy；

无skill、无high editor、无KEEP/SET。

它只回答任务是否能被强普通策略访问。

F0_initial_set

完整event runtime、skill bottleneck和exogenous opportunity schedule；高层所有token都读取：

g(C
(0)
).
F1_working_prefix

与F0逐参数、逐模块、逐随机账本匹配，只把decoder summary改为：

g(C
(j−1)
).

F0是机制匹配零假设；direct policy才是最强ordinary task-access反对者。问题文件原map中把F0称为ordinary reduction是合理的，但不能把它误称为不含skill bottleneck的最强普通策略。

4.2 testbed access 前置读数

同一结果包必须在训练前完成两个无学习审计：

Constructive controller

使用routing-only oracle完成职责分配，要求在256个固定ledgers上：

P
ˉ
,
S
ˉ
,
U
ˉ
≥0.90.

它只证明环境可完成。

Uniform random primitive policy

要求：

P(U>0)≥0.80,

并且：

0.10≤
U
ˉ
≤0.45.

这同时排除：

R51式零carrier；

R53式初始化/feasibility ceiling。

若任一失败，退休该testbed，不启动对F0/F1的解释。

5. F0/F1 causal isolation

必须保持当前已验证的单一 intervention：

F0:
  decoder summary = initial commitment set

F1:
  decoder summary = applied working commitment set

以下全部严格相同：

module graph和参数量；

initial weights；

low actor/critic；

event critic；

lifecycle store；
-机会 gaps；

frontier orders；

membership/task ledgers；
-外部reward；

high/low PPO；

normalizers；

optimizer exposures；

checkpoint与evaluation。

现有代码确实是在每个token应用动作、更新member embedding和working summary之后，再为F1后序token选择working summary；F0继续选择initial summary。

5.1 Common-support prefix read

只分析：

frontier size ≥2；

token position j>0；

episode-start全join frontier之外的自然post-shock/frontier事件。

对每个F1 token，使用相同owner hidden、member embedding和legal mask，计算：

π
work
	​

=π(⋅∣C
(j−1)
),
π
initial
	​

=π(⋅∣C
(0)
).

主统计：

D
prefix
	​

=TV(π
work
	​

,π
initial
	​

).

F0的对应值应为数值零。Hard-mask-only变化、common additive shift或raw Jacobian不计入F1证据，这与现有代数约化合同一致。

6. Metrics and outcome branches
6.1 M0 — implementation and substrate validity

必须全部满足：

typed membership事件、两快照transaction和active sets完全符合注册schedule；

event train_loop不再停留在deterministic-trace fail-closed状态；

F0/F1 state-dict keys、shapes、parameter count、initial values完全相同；

sample/replay high logp、low logp、value、hidden、order、mask和working-prefix误差：

≤10
−6
;

duration return与owner-local GAE直接重算误差：

≤10
−6
;

schema-3 live resume逐项相等；

routing keys不进入model tensors；

exact environment counts、membership counts、wave counts；

constructive/random access审计通过；
-所有相关梯度、参数和normalizer有限；

exact-final checkpoint，无best selection。

失败：

INVALID_DYNAMIC_TESTBED_WIRING

只允许修明确实现缺陷，不修改任务、预算或阈值。

6.2 Direct ordinary access

每个final deterministic evaluation必须满足：

U
ˉ
direct
	​

≥0.75,
P
ˉ
direct
	​

,
S
ˉ
direct
	​

≥0.70,
LCB
95
	​

[U
final
	​

−U
zero
	​

]>0.20,
U
ˉ
direct
stoch
	​

≥0.70,
UCB
95
	​

[U
stoch
−U
det
]<0.15.

四个连续64-episode deterministic blocks中至少三个：

U
ˉ
block
	​

≥0.70.

失败：

RETIRE_TESTBED_NO_ORDINARY_ACCESS

退休精确环境；不解释F0/F1。

6.3 Skill execution read

在每个F0/F1 final model上，从128个自然held-out snapshots执行：

3 skills
× 2 common-random-number replicas
× 12 primitive steps

只作evaluation，不更新参数。

过程签名包括：

IDLE/PERSIST/SHORT_A/SHORT_B occupancy
persistent work
A/B short contribution

要求：

LCB
95
	​

(ρ
H4
	​

)>1,LCB
95
	​

(ρ
H12
	​

)>1,

其中 ρ 为between-skill / within-skill-replica比。

还要求：

至少两个skills在held-out contexts中形成TV距离 ≥0.20 的不同职责模式；

natural rollout中persistent-like与reactive-like模式各至少占10%的真实opportunities；

persistent-like spell与reactive-like spell的active-time中位数之比：

LCB
95
	​

>1.20.

这一区分“有不同标签”与“有持续可执行角色”。

6.4 F1 prefix evidence

要求至少：

10,000 post-initial later-token common-support rows

并满足：

LCB
95
	​

[ED
prefix
	​

]>0.03,
P[D
prefix
	​

>0.05]≥0.20.

基于在独立forced-probe split上冻结的skill-to-duty mapping，F1还必须使后序token的重复职责概率相对initial-summary counterfactual下降：

LCB
95
	​

[p
duplicate
initial
	​

−p
duplicate
work
	​

]>0.08.
6.5 F1 task value

H1成立需要：

U
ˉ
F1
det
	​

≥0.65,
P
ˉ
F1
	​

,
S
ˉ
F1
	​

≥0.60,
LCB
95
	​

[U
F1
	​

−U
F0
	​

]>0.05,

以及：

U
ˉ
direct
	​

+10
−8
U
ˉ
F1
	​

	​

≥0.85.

不能以prefix logits变化替代外部任务收益。

6.6 Timing diagnosis

对每个short wave，利用真实ledger计算：

在deadline前至少两步，已有多少active members持有当前reactive职责，或会获得下一次policy opportunity。

若少于该wave的 R
w
	​

，定义为timing-infeasible。

只有在skill和prefix门均通过时，以下模式才强化H3：

P(timing-infeasible waves)≥0.25,
completion
feasible
	​

≥0.80,
completion
infeasible
	​

≤0.40.

该读数不改变机会时钟，也不授权learned timing。

6.7 互斥科学分支
分支	条件	假设更新与动作
INVALID_DYNAMIC_TESTBED_WIRING	M0失败	修具体wiring；原合同重做
RETIRE_TESTBED_NO_ORDINARY_ACCESS	Direct access失败	环境无访问；H0–H3均不判，退休testbed
STOP_AT_DIRECT_H2_SKILL_BOTTLENECK	Direct通过；F0/F1 task低且skill execution失败	强化H2；F1 prefix未被测试；停止F1集成
STOP_AT_F0_SHARED_CONTEXT_SUFFICIENT	Direct通过；F0达到task floor并接近direct；F1无task增益或无prefix证据	强化H0；退休H1，采用F0作为当前解释
SUPPORT_F1_APPLIED_PREFIX_VALUE	Direct、skill、prefix和F1 task gain全部通过	强化H1；仅进入新设计审阅，不直接集成
TIMING_LIMITED_AFTER_PREFIX	Direct/skill/prefix通过，task gain未通过，且timing诊断满足	条件性强化H3；learned timing仍保持deferred
MIXED_STOP_AND_AUDIT	其余有效组合	不自动生成下一实验；冻结结果并做跨轮架构审计

这些分支使多个非PASS结果仍能改变假设组合，而不是把所有F0/F1读数都隔离掉。

7. Minimum evidence budget

唯一建议的高信息量证据源是上述一个三arm分层实验；不另开并行toy或额外specialist家族。

arms
  direct_active_set_primitive_AR
  F0_initial_set
  F1_working_prefix

environments / arm          16
episode / rollout           80 / 80
outer updates               250
primitive steps / arm       320,000
episodes / arm              4,000

PPO epochs                  4
optimizer steps/path        1,000
batch reuse                 exactly 4 registered passes
gamma                       0.99
GAE lambda                  0.95
clip                        0.20
entropy coefficient         0.01
value coefficient           0.5
gradient clip               0.5

zero/final evaluation
  stochastic episodes       256 / arm
  deterministic episodes    256 / arm

forced-skill audit
  snapshots                 128 / F0,F1
  skills                    3
  replicas                  2
  horizon                   12
  branch steps              9,216 / arm

bootstrap                   10,000 paired episode clusters
checkpoint                  exact final
best-checkpoint selection   prohibited

建议固定seeds：

model/init          57057
membership/task     67057
opportunity/order   77057
primitive action    87057
evaluation          97057
bootstrap          107057

F0/F1必须使用相同的：

membership ledger；

task waves；

service tie-breaks；

opportunity gaps；

frontier orders；

initial parameters；

optimizer exposure。

Direct arm共享membership/task ledgers，但不共享skill机会，因为它没有high event process。

8. Final-capability map and replacement ledger
8.1 修正后的capability map

问题文件中的“yes”需要区分架构可表达与已有科学证据。

Family	Dynamic roster	Heterogeneous lifetime	Skill bottleneck	Learned prefix	当前证据地位
Direct ordinary active-set	可支持	无显式claim	否	primitive-level可协调	尚未实现；仅task-access instrument
F0	runtime已支持	可表达但未证明自然使用	是	否	lifecycle/replay/credit wiring PASS
F1	runtime已支持	可表达但未证明自然使用	是	common-support参数路径存在	wiring PASS；learnability/usefulness未知
Learned point process	未实现	可能	可选	独立问题	deferred

特别需要删除以下推断：

exogenous gap差异⇒有用的learned lifetime heterogeneity.

随机机会时钟本身会制造不同spell长度；只有role-conditioned KEEP/SET和行为过程证据才能支持lifetime claim。

8.2 Replacement ledger
Retain

schema-3 LifecycleStore和typed membership transaction；

JOIN/temporary LEAVE/terminal LEAVE/REJOIN语义；

active-only sum/count reference；

uniform recorded frontier order；

exact F0/F1 selector；

owner-local γ
Δ
 return和GAE；

strict replay/resume/fail-closed边界；

low actor不变量：

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

).
Delete or keep retired

R51–R54全部精确环境、模型、threshold与rescue；

未执行的R55 numbered route；

fixed-N specialists作为episode-internal roster任务的普遍前置条件；

field slots、graphs、team latent、new discriminator；

learned event time；

hard role masks、identity tokens和reward-defined skill labels；

“toy PASS即可接入主控制器”的任何隐含规则。

R55已在architecture disposition中明确repurpose且不得执行。

Add only for this testbed

一个dynamic-roster environment/adapter；

一个direct primitive-action ordinary access instrument；

event-mode真实PPO integration；

一个同时归因task access、skill execution、prefix value和conditional timing的analyzer。

不新增：

intrinsic reward；

graph/attention/slot stack；

learned hazard；

team code；

testbed-specific辅助loss。

9. Strongest ordinary-MARL objection

最强反对意见是：

只要当前职责状态、self-owner关系和active-set信息可见，primitive-level普通AR策略就足以完成所有协调；F1的skill-prefix层可能是多余中间层。
	​


该反对意见有三部分：

Direct ordinary policy每个primitive step都能重新协调，而F0/F1只能在均值10步的外生机会时钟上编辑。

F0已看到initial active commitment set和成员局部状态；若成员状态本身足以决定职责，后序编辑不需要读取前序sampled edits。

F1最明显的优势发生在episode-start或membership shock的大frontier；若测试只依赖同质joiners打破对称，得到的只是人工anti-coordination演示，而非一般合作价值。

修正版设计通过以下方式正面接受该反对意见：

将direct primitive AR作为最强task-access instrument；

H1主统计排除episode-start全join frontier；

要求post-shock heterogeneous lifecycle contexts中的common-support response；

要求方向正确的冗余减少；

最终仍要求F1超过完全匹配F0的外部任务表现；

即使F1通过，也只授权后续设计审阅，不视为可集成或UAV证据。

最终决定
	​

MODIFY_TESTBED_DRAFT;
保留动态dual-duty与F0/F1唯一selector差异；
精确冻结owner-continuity persistent duty、
随 N
t
	​

 扩展的A/B short waves和terminal graded utility；
把direct primitive-AR policy加入同一分层证据源；
将H0/H1作为主比较，H2作为上游失败分支，
H3降级为skill/prefix均成立后的条件诊断；
只有common-support prefix response、方向正确的组合变化
和F1外部任务增益同时成立时才支持H1；
否则允许退休testbed、停在direct/F0、强化H2、
或进入mixed cross-round audit，而不是自动生成新算法。
	​

	​


本回复只提供审阅后的候选合同，不授权环境实现、训练或实验启动。
