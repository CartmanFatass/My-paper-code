1. Evidence validity and delta

PASS_CLEAN_CARRIER_DIRECT_ACCESS 在其注册合同内有效。

该结果同时满足实现有效性、carrier calibration 和 direct-access 三层条件：320,000 个环境 transition、1,000 个 optimizer step、1,280,000 个 active row 和 4,000 个独立训练 ledger 均精确；token/joint likelihood、value、recurrent hidden 和 primitive-prefix replay error 全为零；模型与 optimizer checkpoint 恢复误差为零；skill、高层策略和 intrinsic 路径计数均为零。Constructive control 的 P/S/U=1/1/1，uniform random 的正 utility 比例为 1、均值约 0.3242。最终 direct deterministic P/S/U=1/0.998210/0.999105、stochastic U=0.986654，deterministic final-minus-zero utility CI95 为 [0.498535,0.499105,0.499593]，清晰越过全部注册 access gate。

Clean carrier 的新增内容确实是旁路的 lifecycle-owned actuator trace：任务、observation、reward、membership schedule 和 direct learner仍是 Generic-SHORT；actuator_position/velocity 不进入 actor、critic、reward、GAE 或 PPO。新 JOIN 将状态置零；只有 active member 的状态被推进；temporary absence 期间状态冻结；REJOIN 恢复冻结值；环境 snapshot 包含并严格恢复全部 process state。测试还逐步比较 clean 与原 Generic-SHORT 的 actor observation 和 reward，确认二者相同。

但这里存在一个重要 claim ceiling：

v
t+1
	​

=0.75v
t
	​

+0.25F(a
t
	​

),F(a
t
	​

)∈{−1,0,1},

所以

F(a
t
	​

)=4v
t+1
	​

−3v
t
	​

.

三种 force 与三个 primitive action 一一对应；给定初始 process state，完整 velocity 序列精确恢复完整 action tape，position 又是 velocity 的确定性积分并带固定 clipping。因此该 channel 虽然连续、task-neutral、生命周期所有权正确，却不包含超出 start state 与 primitive-action tape 的独立过程随机变量。

由此得到三项结论：

Clean actuator channel可用于验证 action consequence、leave/rejoin persistence、snapshot ownership 和 process-window实现。

它不能直接支持 I(z; clean_process)、posterior accuracy 或 posterior-minus-context score 型 intrinsic semantics；在当前确定性动力学下，这些量只是 action information 的重编码。

只有先条件化于完整 action tape 与 start state 后仍存在非零、可重复的 physical residual，才可能讨论独立 process semantics；本实现的该 residual 理论上为零。单独再运行一次 action-equivalence科学实验没有新的识别价值，等式本身已经由冻结代码决定。

Clean positive因此解析了基础设施候选 A：episode 内 membership churn、active masks、survivor recurrence和旁路 clean process state可以与一个成功的普通 learner共存。它同时表明 Iteration-5 no-access不是由“动态 roster runtime 本身”或“仅仅存在物理process channel”必然造成。

它不改变以下结论：

精确 Iteration-5 spatial carrier仍永久退休；

精确 Iteration-5 C1 posterior/reward/view仍有效失败；

spatial failure仍未在 observation、dynamics、zero-step bias、policy information和optimization之间进一步分解；

“spatial carrier在数学上不可能学习”不受支持；

hierarchy、learned skills、intrinsic causality、variable skill lifetime、transfer和UAV价值均未建立。

Iteration-5中同预算C3的 short floor和learning-gain gate失败，而其C1 action/process effect上界低于1/12；clean run不能把这些负结果改写为参数不足，也不能用新的carrier替换旧结果。

还有两个工程边界必须保留。第一，当前direct actor是一个很强的access instrument：它读取active-member embedding总和、log(1+N)和同一primitive frontier中更早action的计数，并非严格local-only executor。第二，当前direct checkpoint保存model、optimizer、更新计数、下一ledger ID和Torch RNG，但不包含正在运行的environment、per-lifecycle hidden table或pending membership transaction；clean环境snapshot round-trip与训练checkpoint有效性是两个分别通过的合同，不等于任意mid-segment联合live resume。

2. Weighted two-to-four-candidate portfolio

Clean substrate A退出算法组合，作为已解析的基础设施保留。当前相对证据权重为：

D — Hierarchy-null active-set direct recurrence

权重：高，当前经验领先者；不是最终定论。

机制与最终能力。 一个共享primitive-time recurrent actor直接处理active roster；持续行为、响应行为和leave/rejoin记忆均由hidden state实现。最终系统仍可支持匿名JOIN/LEAVE/REJOIN，但“skill lifetime”只是内部状态持续性，而不是显式、可干预、可复用的skill object。

因果estimand。

Δ
D
	​

=U
verified hierarchy, heldout
	​

−U
information-matched direct, heldout
	​

,

主要读取未见membership schedule、未见active-lifetime distribution和sample efficiency，而不是训练内utility或label可解码性。

替换账本。 保留typed membership spine、active-only masking、survivor recurrence、centralized training critic和terminal external reward；删除high policy、skill latent、KEEP/SET、semantic learner和event-policy likelihood；以primitive autoregressive recurrence替换两级policy；不增加新模块。

最强ordinary-MARL reduction。 D自身就是该reduction。B或C若只增加参数容量、latent维度或行为可解释性，而没有held-out外部优势，则归约为普通recurrent representation。

最强反证。 一个具有material、persistent、natural、nuisance-resistant learned semantics的hierarchy，在actor-visible information、communication、参数量、environment exposure和optimizer exposure匹配时，于未见roster/lifetime上提供material external-utility或sample-efficiency优势。

分离观察。 B/C可以形成稳定process modes，但matched direct仍noninferior，会直接支持D而非“技能存在即有价值”。

权重依据。 Generic-SHORT和clean carrier都被同一类direct policy近乎完美访问，而Stage C、Iteration 4和Iteration 5均未形成material naturally executable skills。其限制是当前任务不要求显式temporal abstraction，且direct access actor拥有active-set和primitive-prefix coordination bandwidth。

E — Executable-skill assignment / event-credit bottleneck

权重：中。

机制与最终能力。 即使一个low executor已经拥有persistent/reactive primitives，当前F0 high policy、owner-event return、固定opportunity interface或其联合optimization仍可能无法自然选择正确组合和KEEP lifetimes。E首先是因果解释，不是一个待盲加的新critic。

它若最终解决，可解锁：JOIN时分配初始commitment；temporary leave后维持survivor commitments；REJOIN恢复skill并重新决策；不同成员通过KEEP形成不同active-time lifetimes；高层只利用external task return完成自然assignment。

因果estimand。

Δ
E
	​

=U
learned high + supplied executor
	​

−U
frozen high + same executor
	​

,

同时要求routing oracle在同一opportunity ledger上可解，并验证exact high likelihood、event value、owner-event return、gradient和checkpoint。

替换账本。 在诊断中保留F0 high/event policy、event critic、external opportunities、KEEP/SET、owner-specific gamma^\Delta return和terminal reward；删除learned low、low optimizer以及所有intrinsic；暂时以固定supplied primitive executor替换low path；不增加credit module。

最强ordinary-MARL reduction。 Direct policy完全绕过assignment和event credit。即使supplied hierarchy访问任务，也不能据此削弱D，因为primitive是手工提供的。

最强反证。 现有high/event path在supplied executor上可靠越过access gate并显著优于其冻结初态；这会将主要不确定性推回B的skill creation/executor。

分离观察。 Oracle与direct均通过、learned high失败，同时high replay、return和gradient有效，会区分E与B：此时先更换low executor没有识别力。

权重依据。 当前clean run没有运行high policy；而历史fixed-primitive positive control、direct-state、更多high exposure和block-return诊断均未建立high access。那些运行并非同carrier或同event runtime，因此只能给予E中等而非决定性权重。

B — Factorized discrete process executor

权重：中低；high path通过后才具有直接可识别性。

机制与最终能力。 保留三个opaque categorical skills和KEEP/SET，但以三个互斥、低秩、总容量受控的recurrent/action adapters替换“shared actor + FiLM是唯一skill separation”。每个lifecycle一次只执行一个adapter；不同时加入posterior、simplex、graph或learned timing。目标是让z真正选择不同的闭环状态转移，而非仅给共享网络添加弱条件。

因果estimand。

Δ
B
	​

=U
factorized
	​

−U
capacity-matched shared
	​

,

之后才读取same-snapshot action control、自然skill usage、跨JOIN/REJOIN/age strata稳定性以及未见membership/lifetime上的外部utility。

替换账本。 保留K=3、F0 high/event path、opportunities、owner-event return、shared observation trunk和decentralized low execution；删除Iteration-5 posterior reward；替换low recurrent transition/action conditioning；增加三个互斥、总容量匹配的adapter，不增加第二controller。

最强ordinary-MARL reduction。 三个adapter可能只是把一个网络拆成三份。容量匹配direct/shared actor若学到相同行为，B没有独立贡献。

最强反证。 Adapters有非零gradient和drift，但没有material自然执行差异；差异只存在于参数/logits或action tape；shared arm等价；或B在held-out条件下仍不优于direct。

分离观察。 Supplied-executor high path先通过，而factorized显著优于capacity-matched shared，会支持“shared-executor interference”；若high path本身失败，B不能被解释。

权重依据。 现有共享executor的z作用在多轮审计中均小，但没有任何证据表明参数分隔是缺失原因。

C — Three-basis simplex process command

权重：低，parked。

机制与最终能力。

w
i
	​

∈Δ
2
,c
i
	​

=
k=1
∑
3
	​

w
ik
	​

b
k
	​

.

三个共享basis不变；KEEP保持当前command，SET(w)更新command；lifetime仍由连续active KEEP产生。它替换hard one-hot interface，而不是堆在B上；不增加duration head、hazard或team latent。

因果estimand。

Δ
C
	​

=G
simplex
	​

−G
one-hot
	​

,

其中G必须是non-vertex command在held-out roster/lifetime上的可控性和外部价值，而不是actuator classifier accuracy。

替换账本。 保留三个basis、active lifecycle、opportunity、low recurrence和external reward；删除categorical embedding及categorical SET head；增加完整continuous transformed density、实际sample、Jacobian和command checkpoint state。

最强ordinary-MARL reduction。 Simplex latent可能只是普通recurrent hidden的冗余连续输入。

最强反证。 Command长期落在vertices；non-vertex只混合primitive-action probabilities；B或D可复现全部行为；没有额外held-out utility。

分离观察。 在one-hot executor和high path均已有效时，non-vertex command仍产生不可由B复现的、负载相关且外部有用的过程插值，才支持C独立存在。

权重依据。 当前没有证据表明离散性是瓶颈；clean channel又不能独立验证continuous semantics。

3. Semantic, intrinsic and reward boundary

当前clean carrier上不存在可接受的process-semantic intrinsic signal。

原因不是字段名不够“通用”，而是actuator trajectory在给定start state后由action tape完全决定。将

logq
ϕ
	​

(z∣x
1:L
actuator
	​

)

或其相对context posterior的差值加入low reward，在数学上仍是通过确定性编码恢复primitive-action information，属于R29的重命名。换posterior、窗口、encoder或系数不改变这一事实。

本轮的准入边界如下：

对象	处置
Clean actuator position/velocity	Audit-only：lifecycle ownership、action consequence、snapshot、leave/rejoin检查
Primitive action tape	可用于behavior replay和action-conditioned null；不得作为semantic positive view或intrinsic target
Forced skill/action/process branches	Audit-only；不得训练posterior、构造reward或形成policy gradient
Posterior accuracy、MI、effect ratio、between/within score	Audit-only；不得替代intervention materiality或external task value
Identity、role、lifecycle key、epoch、roster slot	Routing/stale-row用途之外均禁止进入policy或semantic estimator
Progress、success、contact、phase、owner、wave target、task state	可按注册合同进入普通task observation或external evaluator；不得进入intrinsic semantics
External return	可作为external task objective训练direct/high/low policy；不得改名为intrinsic或semantic evidence
Duration/age	可用于credit和nuisance stratification；不得因更长lifetime而放大semantic reward

更一般地说，未来只有以下对象才可能成为admissible semantic signal：

I(z
i
	​

;X
i,1:L
local physical
	​

∣o
i,0
	​

,h
i,0
	​

,a
i,0:L−1
	​

,M
i
	​

,L),

其中X必须含有不能由start state和action tape确定的局部physical consequence；输入合同须跨环境保持同一数学形式；不得读取task fields、reward、identity、role或future membership；必须由action-conditioned、length-matched、context-matched null确认增量。当前clean channel对这个条件互信息的可用residual为零。

若将来另有合法signal，其credit还必须：

只进入所属focal active segment的low objective；

不进入high/event return、KEEP/SET advantage或lifetime选择；

不按segment duration累计放大；

不跨temporary absence、membership epoch或policy version；

estimator loss与policy graph隔离，actor只能通过detached ordinary RL reward接收影响。

默认q_D或team-code reward仍关闭：当前runtime没有一个已经证明actionable、roster-invariant且拥有明确事件owner的team latent。原R41B仅证明完整fixed-N source path可学，不能倒推出某个discriminator的因果必要性。

4. Variable-membership, lifetime and checkpoint contract
Clean direct run已经证明的内容

运行中确实发生4→2→6→4的episode内membership变化，而不是跨episode固定N泛化。

只有active member产生primitive action并推进actuator state。

Temporary absence期间process state冻结，REJOIN恢复；genuine JOIN为零。

Direct hidden只在active row更新，因此temporary leaver的hidden在absence期间不演化。

Active mask、recorded primitive order、teacher-forced actions、earlier-action prefix和recurrent replay均精确。

Routing key未进入network；observation和reward与原Generic-SHORT一致。

Clean environment snapshot可完整恢复process和pending transaction边界。

PPO credit沿每个physical step推进；不存在high event或skill likelihood。

这些证据的边界是固定capacity MAX_LIFECYCLES=6下的匿名active masking，不是任意无界roster；direct actor还拥有active-set aggregate和primitive-prefix context，不是最终local-only execution证明。

未来hierarchy必须逐项建立的语义

Genuine JOIN

new opaque lifecycle
membership_epoch = 0
h_low = 0
h_high = 0
skill/command = undefined
active age = 0
immediate structural opportunity
legal high action = SET only

不得通过复用物理标签继承terminal或旧lifecycle状态。

Temporary LEAVE

在post-primitive、pre-removal snapshot读取旧critic bootstrap；

关闭owner event trace和low/semantic learning chunk，属于critic-only truncation；

没有leave actor likelihood；

冻结low/high recurrent state、skill/command、active age和剩余opportunity gap；

absence不推进active lifetime，不分配inactive reward；

所有survivor hidden、commitment、age和open trace连续。

REJOIN

恢复同一opaque lifecycle，但membership_epoch += 1；

恢复hidden、skill/command和active age；

获得新的policy opportunity；

从恢复状态开启新的high trace和learning chunk；

commitment可在active-time意义上继续，但数据/credit segment不得跨inactive gap或旧epoch拼接。

Terminal LEAVE

所有open trace零bootstrap关闭；

row finalization后删除policy-runtime hidden和skill/command状态；

之后相同物理标签必须创建新lifecycle；

不得产生terminal后actor row。

这些是现有event architecture的硬合同，而非clean direct run自动证明的事实。

Probability、masks和clocks

对未来B/C/E hierarchy，完整behavior probability只包含：

q(σ
t
	​

∣F
t
	​

)
j∈F
t
	​

∏
	​

π
H
	​

(e
i
j
	​

	​

∣C
t
j−1
	​

,m
j
	​

)
i∈A
t
	​

∏
	​

π
L
	​

(a
i
	​

∣o
i
	​

,h
i
	​

,z
i
	​

),

其中外部frontier order q、membership events和exogenous opportunities均与policy参数无关；它们可记录用于审计，但不产生policy gradient。Supplied deterministic executor的诊断中没有low policy likelihood，只有实际high commitment tokens具有actor ratio。

必须区分：

Physical time：环境primitive step与γ折扣；

Opportunity time：active member被允许KEEP/SET的外生事件；

Event depth：同一owner的真实policy events，决定λ递推；

Realized lifetime：同一commitment跨连续active KEEP累计的active execution time；

Learning segment：由SET、leave/rejoin、terminal和policy-version边界切分的可归属数据窗口。

Owner-event return为：

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
env
	​

(t
i,n
	​

+r),

非终止bootstrap为γ
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

)。其他成员的event、silent primitive step和external membership transaction不能制造该owner的actor ratio或增加其event-depth。

Mid-segment fail-closed checkpoint

未来hierarchy不能依赖当前direct checkpoint schema。它必须在具有open owner trace、非零skill age、mixed active/temporarily-absent lifecycle和pending transaction的mid-segment边界，完整保存并恢复：

policy、critic、optimizer、normalizer；

lifecycle table与membership epochs；

low/high recurrent states；

active skill或simplex command及age；

opportunity RNG、frontier-order RNG、policy-action RNG；

open event traces和policy version；

current observation/state boundary；

active presentation、pending membership transaction及command-response state；

worker environment snapshot，包括clean process state；

environment RNG。

恢复后下一high action、primitive action、log probability、value、hidden、membership transition和环境后果必须一致；缺失任一状态须hard fail，不能reset-and-continue。

Decentralized execution

未来integration比较必须信息匹配。当前direct actor读取active-set aggregate与earlier-action counts；hierarchical low actor通常只读自身observation、hidden和skill/command。后续D-vs-hierarchy比较必须：

为两者提供相同可部署通信信息；或

将direct限制到与low actor相同的local information；或

明确将共享active-set通信作为两者共同、计费的系统能力。

否则“direct更优”可能只是centralized execution bandwidth的结果。

5. Literature principles and non-imports

可迁移的是约束，不是模块菜单：

ACAC：γ按真实微时间流逝、λ按owner event深度推进；agent-centric有效事件history。其固定n_agent runner、经验结构和critic shell不能直接迁移。

ACE：per-member readiness、异步执行壳和dropout pressure test有价值；其固定num_agents buffer与一步return缺少γ
T
i
	​

，不能作为open-roster/SMDP实现。

InforMARL：共享参数、active-set/permutation-safe representation和稀疏邻域原则；其runner仍固定agent/node count。只有测得当前sum/count信息不足后，graph才可能作为替换。

Sable：用于固定大N的吞吐和内存对照；固定T×N序列、n_agents相关mask和token phase不提供dynamic-roster ownership。

ExpoComm：有界、小直径candidate topology可作为未来复杂度原则；固定循环ID、同步one-peer clock和旧邻居message memory与roster churn冲突，默认辅助通信loss也不能顺带加入。

Safe-M3-UCRL：population field与mass/safety diagnostics有启发；无限同质representative-agent会抹去rare-critical member与绝对N，不能成为有限open-roster主体。

CT-MARL：真实duration必须进入value semantics；其共享Δt、固定N joint state和PINN/HJB/VGI整栈不迁移。

IARO：relative spreadness可作无奖励diagnostic；全员投票、共同执行、共同终止与heterogeneous T
i
	​

相反，eigenvector intrinsic和joint-option system不迁移。

收敛原则是：

active lifecycle ownership
+ exact physical/event-time credit
+ task-neutral且action-null-resistant的process evidence
+ information-matched direct recurrent null

而不是：

graph + retention + communication + mean field
+ team latent + option discovery + continuous-time model

注册综述也确认，没有一篇列出的论文同时提供episode内JOIN/LEAVE/REJOIN、survivor continuity和正确on-policy roster semantics。

6. Retired-line and rescue exclusion

以下关闭保持严格：

R29：direct action-information及其online reward家族。Clean actuator是action tape的确定性编码，不能以“process information”重开。

R31-CFEI：自然posterior/effect association不能替代forced intervention；effect statistic保持audit-only。

R32-IFEPG：不得用forced-effect advantage直接更新FiLM、adapter、action head或其他executor参数。

R33-IRSC：不得使用complete-roster effect enumeration、pair complementarity reward、pair sham或head-only intervention-score update。

Iteration-5 C1：精确conditional posterior、posterior-minus-context score、beta=0.05、12-step position-process reward组合已关闭；不得迁移到clean carrier。

历史R39 supplied-primitive、高context、高exposure和block-return路径也是固定结果，不能调参复活。下一节选择的supplied executor只是一项针对当前clean carrier与当前F0 event runtime的诊断positive control；它不会重跑R39、改变其预算或把手写primitive晋升为skill算法。

有效负结果后禁止：

增加或替换seed；

增加budget、updates、PPO epochs或model width；

修改threshold、CI、window、skill count或adapter rank；

更改reward、task observation、task horizon或carrier；

给clean channel加noise、改damping/drive/force map以制造residual；

更换posterior容量、loss、temperature或normalizer；

加duration catalogue、SET(current)、age payment或lifetime reward；

加learned scheduler、termination hazard或event-time policy；

加identity、role、task progress、contact、success或phase；

加graph、communication、slot、team latent、q_D、new critic或module stack；

以best checkpoint、stochastic-only metric或post-hoc stratum合并救援。

任何需要上述改变的想法必须是新的独立因果问题，并且不能用于改写旧branch。

7. One selected next evidence source or explicit stop

选择：CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0——一次独立的supplied-executor high/event-path localization。

这是当前最高“causal information / registered change”的来源。

原因如下。

第一，clean-channel action-equivalence不需要成为新的科学运行。 由冻结递推式可直接推出action tape；独立E1预计只能报告数值精度零，且不会区分D、B、C或E。该等价性应作为新source的M0不变量，而不是消耗一个scientific iteration。

第二，直接运行B-versus-D会混杂两个未识别边。 B失败可能因为factorized executor无效，也可能因为现有high assignment/event credit无法利用即使完美的skills。必须先用supplied executable primitives隔离high path。

第三，Gemini提出的delayed direct-null不是最小改变。 增加temporal spacing会同时改变task、horizon上的信用传播和access margin，重新打开一个carrier qualification。Direct失败不能区分memory horizon、observation、optimization与任务校准；direct通过也不能判断B还是E。它只适合在executor与high path都已验证后，作为真正load-bearing的held-out lifetime压力条件，而不是下一步。

第四，supplied-executor source直接改变组合权重。

High通过：E下降，B成为可识别的下一机制；

Oracle通过而high失败：E上升，B/C应暂停；

Oracle失败：固定opportunity contract不能承担assignment判断；

初始high已足够：当前任务不load-bearing，停止在该carrier继续比较hierarchy。

这比再确认access或立刻训练新executor具有更高信息增益。Open divergent review也将该source定义为只训练现有high/event path、supplied low零参数、oracle字段不进入policy或advantage的diagnostic。

选择这一source不使B、C或D非法；也不授权其实现。

8. Selected-source contract and mutually exclusive branches
8.1 Scientific question

在已通过direct access的clean dynamic-roster carrier上，当三个完全可执行的primitive modes由外部供给时，现有F0 high/event policy、固定exogenous opportunities和owner-specific SMDP credit能否从external terminal reward学会有用的commitment assignment？

这只定位high path；不检验learned skill semantics。

8.2 Comparator

一个独立结果包含：

learned_high_supplied
现有F0 initial-summary high/event policy和event critic；正常训练high path。

frozen_high_supplied
与learned arm byte-equal的update-0 high policy，零actor/critic optimizer step；在相同256个evaluation ledgers上作为frozen comparator。

routing_only_oracle_supplied
使用task-aware oracle选择commitments，仅证明supplied executor与固定opportunity ledger可达；零学习。

Standing direct reference
已接受的clean direct result，仅作为access与utility上界参考，不重训、不作为primary paired arm。

Supplied executor固定为：

skill 0 -> always IDLE
skill 1 -> always PERSIST
skill 2 -> always SHORT

它没有参数、hidden、critic、optimizer、entropy、likelihood或intrinsic reward。它是task-specific positive-control instrument，不是候选最终skill library。

8.3 Frozen data and ledger boundary

Carrier、observation、reward、membership schedule和process dynamics：精确clean carrier，不修改。

Roster：4→2→6→4，horizon/rollout 80。

Training：16 environments，250 outer updates，320,000 transitions。

High PPO：4 passes，精确1,000 high/event optimizer steps。

Low/posterior/intrinsic optimizer steps：全部0。

Seeds：high initialization 57057；task ledger 67057；opportunity/frontier order 77057；policy action 87057；evaluation 97057；bootstrap 107057。

Evaluation：update 0与exact final，各256 deterministic及256 stochastic episodes；不选best checkpoint。

Reward：只有现有terminal external U=0.5(P+S)。

Selector：F0 initial-summary；不启用F1 applied-prefix treatment。

这些值沿用已注册F0/Stage-C exposure和task-access边界，而不是新调参。

8.4 Probability and checkpoint boundary

行为概率只有实际high combined categorical token：

existing lifecycle:
  {KEEP} ∪ {SET(z != incumbent)}

genuine JOIN:
  {SET(0), SET(1), SET(2)}

External membership、opportunity和uniform recorded order没有policy gradient；supplied primitive execution没有low likelihood。

M0必须验证：

exact legal mask与recorded frontier order；

high sampling/teacher-forced replay error <=1e-6；

event value replay <=1e-6；

owner-specific γ
Δ
 reward、bootstrap和GAE；

learned arm高层actor/critic具有精确1,000次有限、非零gradient exposure；

frozen high参数零drift；

high intrinsic application、low optimizer、posterior optimizer均为零；

lifecycle、epoch、skill、active age、opportunity gap和open trace所有权；

action-equivalence误差为数值精度零；

process channel不进入high input、value或reward；

一次固定mid-segment save/resume：包含open traces、非零ages、temporarily absent member、environment/process snapshot及全部RNG，并证明下一步概率、value、action、membership transaction和环境结果一致。

8.5 Primary reads

Oracle opportunity access

mean(P_oracle) >= 0.95
mean(S_oracle) >= 0.95
mean(U_oracle) >= 0.95

Oracle未达到该门时，不读取learned high。

Learned high access

沿用注册F0 task-sufficiency：

U_final_det >= 0.60
P_final_det >= 0.55
S_final_det >= 0.55
LCB95(U_final_det - U_frozen_det) > 0.10

同时完整报告stochastic结果和相对standing direct的utility gap，但二者不单独改变branch。

8.6 Diagnostic-only reads

natural skill shares；

KEEP/SET rates；

active-time lifetime distribution与censoring counts；

owner temporary leave后的persistent恢复时间；

JOIN、ordinary、REJOIN、survivor及active-age strata中的commitment分布；

high entropy、clip fraction、KL、critic error；

process/action exact equivalence；

oracle assignment trace；

supplied hierarchy与direct的descriptive gap。

这些读数均不能成为learned semantics、hierarchy superiority或integration证据。

8.7 Mutually exclusive priority branches
Branch	Trigger	Portfolio update
INVALID_SUPPLIED_HIGH_PATH	任一概率、mask、credit、count、gradient、checkpoint、RNG、lifecycle或clean-channel exclusion M0失败	只修具体实现；B/C/D/E权重不变
OPPORTUNITY_CONTRACT_NO_ACCESS	M0通过，但routing oracle未过0.95/0.95/0.95	当前固定opportunity interface不能承担assignment positive control；E未被识别；B/C暂停；D保留；不得增加learned scheduler
HIGH_ACCESSES_WITH_SUPPLIED_EXECUTOR	Oracle通过，learned final越过全部F0 task门，且final-minus-frozen LCB>0.10	E作为当前F0 high/event主要瓶颈下降；B成为最强未决hierarchical mechanism；C继续parked；D仍为mandatory null。不得将supplied modes称作skills
FROZEN_HIGH_SUFFICES_NO_LOAD_BEARING_HIGH_LEARNING	Oracle通过；update-0 frozen high已越过绝对P/S/U门；learned gain未越过0.10	当前task不能识别high learning；E不获支持；B/C不能在该carrier作任务价值比较；D局部加强；不自动创建delayed carrier
HIGH_NO_ACCESS_ORACLE_VALID	Oracle通过、frozen不已然充分，且learned high未满足完整access/gain门	E显著上升；B/C暂停；D局部加强但非最终结论。只能在新review中选择一个单一assignment或credit replacement，不能自动加critic/timing/reward

没有UNDERPOWERED、新增seed、延长budget或修改threshold分支。

8.8 Conditional later implications

只有HIGH_ACCESSES_WITH_SUPPLIED_EXECUTOR才使后续独立B-vs-shared-vs-D source具有识别力。

HIGH_NO_ACCESS_ORACLE_VALID不会授权B、C或新intrinsic；它只定位high/event path。

C只有在B的一次one-hot executor已可执行且high path通过后，才可能获得单变量simplex comparison。

Supplied positive control无论多成功，都不能削弱D；真正削弱D仍需learned semantics和held-out外部优势。

9. Prohibited rescues, implementation boundary and integration gate
9.1 Result-open期间禁止的变化

不得修改：

clean carrier、task dynamics、observation、reward、horizon或membership ledger；

process damping、drive、step、force map或process fields；

opportunity schedule、frontier order或event return；

seed、budget、optimizer exposure、PPO pass、width、threshold或evaluation；

supplied primitive table；

F0改为F1；

skill count；

high context、critic capacity或advantage source；

low learner、posterior、intrinsic、graph、communication、team latent、new critic；

learned scheduler、hazard、duration action或age reward；

best-checkpoint选择或结果后stratum合并。

任何valid negative均关闭该精确source。

9.2 后续若获得单独实施授权，允许的精确文件边界

首个实现应限制为新增diagnostic surface：

新增 ha_ctse_process/supplied_executor_high_path.py

SUPPLIED_SKILL_TO_ACTION

SuppliedPrimitiveExecutor

routing_only_supplied_oracle

新增 scripts/run_clean_process_supplied_high_path.py

run_clean_process_supplied_high_path

单一terminal result result/clean_process_supplied_high_path.json

新增 tests/ha_ctse_process_supplied_high_path_test.py

supplied table/action parity

action-equivalence invariant

zero-low/zero-intrinsic checks

high replay与owner-return检查

lifecycle及mid-segment checkpoint round-trip

以下现有科学实现保持冻结并仅被调用：

ha_ctse_process/dynamic_roster_clean_process_testbed.py

CleanProcessDynamicRosterEnv

CleanProcessDynamicRosterEventEnv

audit_clean_process_contract

ha_ctse_process/dynamic_roster_testbed.py

ha_ctse_process/dynamic_roster_direct.py

scripts/run_clean_process_direct_access.py

scripts/run_dynamic_roster_stage_b.py

当前F0 event runtime、probability、owner-return和checkpoint实现

ha_ctse_process/process_semantics.py不得进入该source。

若supplied executor不能仅通过独立runner调用现有event API，而必须改变core event probability、credit、mask或checkpoint schema，控制器应返回IMPLEMENTATION_BOUNDARY_MISMATCH供重新审阅，而不是静默扩大write scope。

这些文件名和symbol只是未来可操作边界；本回答不授权创建、修改或执行它们。

9.3 Diagnostic-only和未授权事项

Diagnostic-only：

supplied primitive modes；

routing oracle；

action-equivalence check；

lifetime/skill-share/composition统计；

standing direct reference；

high-gradient、credit和checkpoint读数。

本轮未授权：

任何代码变更；

smoke、formal training或compute；

B factorized executor；

C simplex command；

新assignment/credit estimator；

intrinsic reward；

learned event timing；
-第三个carrier或delayed task；

UAV或主代码integration；

自动下一轮。

9.4 Later hierarchy integration gate

任何hierarchical candidate进入独立integration review前，必须联合满足：

同carrier ordinary direct access已通过；

Genuine JOIN、temporary LEAVE、REJOIN、terminal LEAVE与survivor continuity逐项实测；

Exact probability、mask、RNG、physical/event-time credit、replay及联合mid-segment checkpoint有效；

Skill semantics由learner形成，不是supplied primitive、task label或手写role；

Segment ownership唯一，不跨inactive gap、membership epoch或policy version；

Same-snapshot action control达到material门；

持续环境后果在相关active-time window达到material门；

跨lifecycle、JOIN/REJOIN、active-age、active-N和未见lifetime保持方向稳定；

Natural policy真实使用相同process regions；

Signal不由action tape、task progress、reward、identity、role、contact、phase或duration shortcut解释；

与information、communication、参数、environment exposure、optimizer exposure和checkpoint选择匹配的direct recurrent policy相比，在未见membership/lifetime条件上取得material external-utility或sample-efficiency优势；

优势来自一个明确替换，而非模块堆叠。

Labels、posterior accuracy、forced effects、supplied primitives及训练内部utility均不足以满足该门。

最终收敛建议：保留D/E/B/C，选择一次独立的CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0作为唯一下一证据源；action-equivalence作为其M0定理检查，delayed direct-null与B-vs-D均延后。该建议不构成任何实现或训练授权。