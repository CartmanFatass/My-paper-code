1. Evidence-validity disposition

接受注册结果：NO_ACCESS_BENCHMARK_ORDINARY_CONTROL。

该结果不是 INVALID，也不是 benchmark structural failure。实现有效：

implementation_valid=true；

全部 22 个 M0 checks 通过；

causal arms 各完成 320,000 transitions、1,000 optimizer steps、4,000 training episodes；

H/S 均为零 optimizer、零 skill/high/intrinsic/posterior/new critic；

evaluation、checkpoint、replay 均有效。

因此应保留：

NO_ACCESS_BENCHMARK_ORDINARY_CONTROL

而不是改写成“algorithm failure”。

H/C/S/D 分别识别什么
H — constrained hindsight authority

已识别：结构可达。

H 的结果：

tracking = 0.7961

completion = 1.0

utility = 0.8923

说明：

在相同 membership、需求、primitive action support 和合法控制权限下，该任务存在高质量轨迹。

因此：

task dynamics 不是不可完成；

action support 不是不足；

membership lifecycle contract 不是阻断因素。

但 H 不证明：

causal policy 可以获得该信息；

learned temporal abstraction 存在；

hierarchy 必要。

C — calendar/static null

已识别：calendar-only 不能解决该任务。

C held-out deterministic：

tracking = 0.5；

completion = 0.4328；

utility = 0.4636。

它提供了一个强 null：

如果没有当前 demand/error 信息，仅依靠时间、roster phase、memory 和 static pre-positioning，无法达到任务要求。

但 C 失败不能证明：

hierarchy 必要；

skill lifetime 是唯一解决方案；

direct recurrence 不够。

S — shared renewal restriction

已识别：heterogeneous timing pressure 存在。

S：

tracking = 0.6809；

completion = 0.7070；

utility = 0.6932。

H-S：

tracking LCB = 0.1109；

completion LCB = 0.2859；

utility LCB = 0.1963。

因此：

统一 renewal clock 限制确实损害能力。

但不能升级为：

learned heterogeneous lifetime 已存在；

skill abstraction 已被证明；

hierarchy 比 direct 更优。

D — ordinary recurrent access

未通过。

D：

IID deterministic：

utility = 0.6262

Held-out deterministic：

utility = 0.6163

Held-out stochastic：

utility = 0.4815

注册 gate 失败：

held-out deterministic utility 不足；

final-minus-zero utility LCB = 0.1014，不达到要求；

D-C utility LCB = 0.1321，不达到要求。

所以当前唯一正确结论：

该 benchmark 通过了 structural identifiability，但没有建立 ordinary causal access。

2. Divergent factual adjudication
Claim 1：C 证明 scheduler failure

结论：部分支持，但表述需要收窄。

Repository fact：

C 被设计为 demand/error information null；

C utility 约 0.46。

合理 inference：

单纯 calendar/static recurrence 不足。

不支持：

“scheduler 本身失败”；

“需要 hierarchy scheduler”。

原因：

C 的失败可能来自：

信息不足；

observation design；

ordinary policy learning；

benchmark online demand access。

Claim 2：H>S 证明 heterogeneous skill lifetime

结论：错误升级。

Repository fact：

H>S：

U
H
	​

−U
S
	​


存在显著差异。

Inference：

共享 renewal clock存在限制。

Unsupported:

“learned heterogeneous skill lifetime 已证明”。

原因：

H 是 hindsight authority。

S 是 artificial shared renewal restriction。

二者比较的是：

full temporal authority
vs
restricted renewal authority

不是：

learned skill lifetime
vs
no skill lifetime

根据项目原则：

长生命周期必须来自 learned behavior under declared clock contract，而不是duration catalogue或外部约束。

Claim 3：D 已有 ordinary access

拒绝。

D 有部分控制能力：

utility > C；

参数变化有效；

replay/checkpoint有效。

但：

ordinary access gate 未通过。

因此：

正确表述：

D learns partial causal control but not sufficient ordinary access.

Claim 4：threefold scaling 是下一来源

拒绝。

三倍规模扩展不能解决当前未识别问题。

原因：

当前缺口不是：

compute不足；

capacity不足；

sample不足。

当前问题是：

ordinary causal access 是否建立，以及 temporal abstraction 是否真正必要。

扩大规模会混入：

optimization；

capacity；

benchmark difficulty。

不是最小信息源。

Claim 5：direct action factorization ≠ temporal abstraction

部分接受。

Repository fact：

D 使用：

active-set embedding；

primitive autoregressive prefix；

recurrent state。

这意味着：

D 已经拥有：

temporal memory；

sequential coordination；

primitive-level factorization。

因此：

“D 失败说明需要 temporal abstraction”

不成立。

更准确：

当前 D 的 primitive-time recurrence 未达到足够 access，但不能区分 representation、optimization、credit 或 action factorization。

Claim 6：当前证据支持 hierarchy

拒绝。

当前支持：

variable lifetime pressure 存在；

shared renewal 有限制；

ordinary access 未建立。

不支持：

high policy；

skill;

hierarchy；

intrinsic reward；

option discovery。

项目原则明确：

skill claim需要：

intervention-sensitive executable behavior；

persistent effects；

beyond stochastic noise；

natural use；

external contribution。

目前没有满足。

3. Weighted causal portfolio

保留五个 live candidates：

D — ordinary recurrent representation/access
Weight: High
Supporting evidence

clean carrier 上 direct access 已成功；

当前 benchmark 失败不是因为 membership runtime；

D 在本 benchmark 有明显学习，但未过 access gate。

Explanation

D 认为：

主要问题仍可能是 observation / representation / optimization，而非需要显式 hierarchy。

Strongest contradiction

如果：

D 在更合适 observation contract 下仍失败；

但 temporal abstraction model 成功；

D 降权。

Retirement condition

需要：

information-matched temporal abstraction；

held-out advantage；

external value。

B — benchmark/access construction problem
Weight: High

当前最强解释之一。

Supporting evidence

H：

utility 0.892。

D：

utility 0.616。

差距说明：

authority存在，但causal access不足。

Possible causes

observation insufficient；

task too hard for ordinary access；

demand process设计仍有hidden difficulty。

Strong contradiction

如果 D 在同信息合同下通过，则 B 降权。

R — recurrent representation/data-flow limitation
Weight: Medium
Explanation

失败可能来自：

recurrent state insufficient；

demand representation不足；

active-set compression不足；

learning signal不足。

Supporting evidence

D 有参数更新：

parameter drift:

0.14995

说明不是dead network。

但没有达到access。

Retirement

如果：

更强但信息匹配的direct baseline仍失败；

temporal model成功；

R下降。

C — terminal credit / optimization limitation
Weight: Medium-low

当前 external reward 是：

terminal only；

sparse。

可能存在：

PPO credit propagation问题；

long-horizon optimization困难。

Supporting evidence

D：

final-minus-zero LCB:

0.1014

说明学习存在，但不足。

Strong contradiction

若更换credit estimator即可让D通过，则C上升。

T — genuine temporal abstraction
Weight: Medium-low

不是退休。

Supporting evidence

S失败：

shared renewal损害性能。

Contradiction

S失败也可能来自：

action update frequency；

restricted control authority。

不是skill necessity。

Retirement condition

若：

D通过；

fixed renewal与adaptive recurrence等价；

T下降。

4. Ordinary-access prerequisite and final capability boundary
Decision

必须先解决 ordinary access，再比较 direct vs commitment.

原因：

当前：

H  PASS
C  FAIL as null
S  shows pressure
D  NO_ACCESS

因此任何：

hierarchy；

skill；

lifetime controller；

都会混入：

benchmark access failure

而不是算法价值。

Before learned variable-membership + lifetime claim is identifiable

必须同时证明：

1. Ordinary access

存在：

D
access
	​


满足：

IID；

held-out；

stochastic；

learning gain。

当前失败。

2. Lifetime pressure

必须证明：

不是calendar：

C fail；

不是shared renewal：

S fail；

而且：

direct recurrence不能简单解决。

3. Temporal abstraction

需要：

learned temporal object:

naturally used；

intervention sensitive；

external value。

不能来自：

supplied primitive；

forced branch；

duration label。

4. Matched comparison

未来必须比较：

direct recurrent
vs
commitment abstraction

保持：

information；

communication；

capacity；

optimizer exposure。

否则不能声称hierarchy优势。

5. Selected next evidence source or stop
Selected source:
DIRECT_ACCESS_REPRESENTATION_LOCALIZATION_AUDIT

选择 evaluation-only，不立即训练新hierarchy。

Why

当前最大不确定：

不是：

“有没有skill？”

而是：

“为什么D没有通过ordinary access？”

需要先拆：

NO ACCESS=representation+credit+optimization+information
Source

读取当前D checkpoint：

不训练。

比较：

Arm D0

当前D。

Arm D1

同一checkpoint，仅增加一个最小causal observation component：

允许：

target_changed
+
normalized tracking error

但是：

禁止：

future duration；

future target；

reward；

identity。

原因：

当前field5/需求误差是online causal information。

为什么不是重新训练hierarchy

因为：

如果D本身不能访问任务：

任何hierarchy成功都无法解释。

为什么不是三倍scale

因为不能区分：

access；

capacity；

optimization。

6. Exact estimand, comparator and information contract
Estimand

核心：

Δ
D
	​

=U(D1)−U(D0)
Comparator
D0

当前D：

信息：

x；

current target；

membership；

recurrence；

active-set。

D1

增加：

e
i
	​

=(g
i
	​

−x
i
	​

)/4

和：

target_changed

仅作为当前事件信息。

Forbidden

禁止：

future duration；

reward history；

completion；

role；

identity；

lifetime label；

intrinsic。

Training

保持：

same model capacity；

same optimizer；

same budget；

same seeds。

唯一变化：

observation contract。

Outcome interpretation
D1 pass

说明：

当前D失败主要来自 observation access。

下一步：

重新评估temporal abstraction必要性。

D1 fail

说明：

问题更可能：

credit；

representation；

optimization。

不能直接进入hierarchy。

7. Mutually exclusive branches and portfolio updates
INVALID

M0/replay/checkpoint失败。

更新：

只修工程。

D1 PASS

结果：

B下降；

R下降；

D上升；

T下降。

解释：

ordinary controller即可。

D1 FAIL + stronger credit evidence

C上升。

D1 FAIL + temporal model succeeds

T上升。

H/S gap disappears under better D

T退休。

No candidate survives

停止该benchmark family。

8. Minimal boundary and prohibited changes
Minimal implementation

只允许：

新增：

analysis/readout_direct_access_localization.py

或：

scripts/run_direct_access_localization.py

复用：

D checkpoint；

evaluation ledger；

existing runner。

Prohibited

禁止：

重跑G0；

改budget；

改seed；

改threshold；

改reward；

改H/S/C定义；

增加skill；

intrinsic；

posterior；

graph；

communication；

latent；

hazard；

new critic；

weakening direct baseline。

项目原则要求：

有效negative不能通过参数搜索救援。

9. Valuable unselected ideas and integration conditions
Matched direct vs commitment prototype

Parked.

未来条件：

D必须先通过。

Factorized executor B

保留。

条件：

证明shared executor interference。

Persistent event abstraction R

保留。

需要：

held-out lifetime advantage；

direct matched comparison。

Calendar redesign

保留为benchmark方向。

如果未来发现：

D失败来自calendar leakage，则重新设计。

Applied-prefix P

继续park。

当前没有multi-owner conflict。

Integration gate

任何 hierarchy integration 必须满足：

ordinary direct access成立；

learned skill而非supplied primitive；

natural execution；

intervention evidence；

heterogeneous lifetime external value；

held-out roster/lifetime advantage；

matched direct comparison；

不依赖task shaping或intrinsic shortcut。

当前状态：

H  ✓
C  ✓
S  ✓
D  ✗
Skill semantics ✗
Hierarchy value ✗

因此：

下一步不是实现 hierarchy，而是定位 ordinary access 缺口。

本轮不授权代码、训练或compute，只选择最小信息增益证据源。