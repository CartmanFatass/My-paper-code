裁决
CONFIRM_REGISTERED_NO_ACCESS_R53_RCMA_SPECIALISTS
	​


但其科学解释必须收窄为：

VALID_FAIL_R53_CAUSAL_LEARNING_GAIN
	​


而不是笼统的“specialists 无法访问任务”。

更准确地说：

	​

R53 action support 与 PPO/replay：有效；
fixed-N 和 shared final-policy competence：已建立；
相对随机初始化的预注册 causal learning gain：失败；
shared-versus-specialist cross-N transport：未识别。
	​

	​


精确 R53 实验合同按预注册分支永久退休，不重跑、不改阈值、不改初始化、不增加预算。唯一下一条可证伪路线为：

R54-HFSR-G0： Hybrid Field-Slot Representation Sufficiency
	​


它只测试：

完整 active-set 信息→固定 M 个场槽与 L 个精确残差成员→保留多峰、稀有关键成员和反协调决策信息.
	​

一、审阅包完整性说明

入口列出的：

docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/
GPT5_6_PRO_R53_FEASIBILITY_RESPONSE_RAW.md

在指定提交中不存在，精确路径返回 Not Found。

这是一个非分支性的文档指针缺陷。被接受的 feasibility correction 已完整登记在 R52 disposition：加入容量为 N 的匿名 idle entity、保留 productive queue 单位容量、总 action support 改为 N+2、模型参数量仍为 24,737，并使三个 M0 调度对所有 N 可执行。

实现代码、正式结果 JSON 和 M0 审计也都实际执行了这一修正。因此该缺失文件应在归档时补齐或修正链接，但不能据此把 R53 改判为 implementation-invalid，也不能触发重跑。

二、R53 implementation-validity audit
1. Environment 与 action contract 正确

实现严格使用：

P
N
	​

=⌊N/2⌋,B
N
	​

=N+1−P
N
	​

,
Q
N
	​

=P
N
	​

+B
N
	​

=N+1,

并加入一个 idle entity，所以完整 action support 为：

K
N
	​

=N+2.

Persistent queues 每个偶数 step 到达一个 work unit，burst waves 位于 t=3,9，burst deadline 为 3。Idle 不产生 arrival、service、completion、expiration 或 reward。

环境逐 step 验证：

每个 productive queue 最多被一名 agent 选择；

idle 最多被 N 名 agents 选择；

service 在 deadline decrement 前执行；

expired burst work 无法事后完成；

所有非终局 reward 为零；

终局 reward 严格等于

U=
F
P
	​

F
B
	​

	​

.

Constructive、persistent-only 和 burst-only 三个调度实际进入 M0，并分别要求：

(F
P
	​

,F
B
	​

,U)=(1,1,1), (1,0,0), (0,1,0).

正式结果中这些 M0 条目全部为真。

2. Residual-capacity autoregression 正确

每个 primitive step 开始时：

c
q
	​

=1

用于 productive queues，而：

c
idle
	​

=N.

每处理一个 AR token，选中 entity 的 planned count 立即增加；后序 token 根据真实 residual capacity 重新建立 dynamic mask。Sampling、teacher-forced replay 与 deterministic greedy decoding使用同一 support。

策略还正确处理了：

entity presentation permutation；

external agent order；

focal previous-action relation；

prefix counts；

idle normalized residual capacity；

masked logits；

canonical action恢复。

3. PPO replay 与 recurrent flow 正确

Collector保存了：

self/entity features
entity masks
agent/entity orders
focal previous actions
hidden reset masks
sampling uniforms
sampled pointers
prefix counts
residual capacities
dynamic masks
old log-probabilities
old values
rewards
next recurrent hidden

Replay 从 episode 初始零 hidden 开始，逐 step teacher-force同一 pointer序列，重建同一 prefix、capacity、mask、previous relation和hidden。

GAE、token-averaged PPO、value loss和entropy均真实执行；所有相关模块获得非零有限梯度。

正式结果中：

sample/replay logp error           0
prefix replay error                0
residual-capacity replay error     0
dynamic-mask replay error          0
previous-relation replay error     0
hidden replay error                0
masked probability mass            0
checkpoint reload error            0

并且全部 M0 checks 为真。

4. Exposure 与 comparator 正确

正式合同精确达到：

100 balanced cycles
500 N-specific batches/arm
128,000 transitions/arm
25,600 transitions/N/arm
512,000 agent-token decisions/arm
500 shared optimizer steps
100 optimizer steps/specialist
500 aggregate specialist steps
PPO epochs = 1
collected-batch reuse = 0

Shared 与相应 specialist 使用同一个 episode ledger、arrival schedule、entity order、agent order和sampling uniforms。

5. Branch code与结果完全一致

代码中 M1 要求每个 specialist 不仅达到绝对 final task floors，还必须满足：

LCB
95
	​

[U
final
det
	​

−U
zero
det
	​

]>0.15.

M2 同样要求 shared macro：

LCB
95
	​

[
U
ˉ
final
det
	​

−
U
ˉ
zero
det
	​

]>0.20.

终端分支顺序明确为：

M0 fail          -> INVALID_R53_RCMA_WIRING
M0 pass/M1 fail  -> NO_ACCESS_R53_RCMA_SPECIALISTS
M0/M1 pass,
M2 fail          -> VALID_FAIL_R53_SHARED_VARIABLE_N
all pass         -> PASS_R53_RCMA_VARIABLE_N

未发现任何能够改变正式分支的 environment、mask、probability、PPO、checkpoint、evaluation 或统计缺陷。

三、四个科学对象必须分开
对象	R53 结论
Action-support correctness	PASS
Final-policy competence	PASS
Causal learning gain over initialization	FAIL
Shared-versus-specialist cross-N transport	UNIDENTIFIED
1. Action-support correctness：PASS

R53 建立了以下机械事实：

heterogeneous residual capacity→无重复 productive assignment 的可重放联合策略.
	​


Productive capacity、idle slack、dynamic mask和AR prefix都严格成立。所有 final deterministic policies也能通过该support执行最优joint mode。

但 R53 没有设置一个无RCMA、其他条件相同的matched arm。因此不能声称：

RCMA 因果地造成了学习改善.

它证明的是RCMA-compatible policy可执行、可训练、可replay，而非RCMA相对unmasked support的因果优势。

2. Final-policy competence：PASS

五个fixed-N specialists的final stochastic utility分别约为：

0.9218, 0.9604, 0.9488, 0.9627, 0.9720.

更强的是，对所有：

N∈{2,3,4,5,6},

specialist和shared的final deterministic结果均为：

F
P
	​

=F
B
	​

=U=1.

所有block stability、绝对utility、persistent/burst floors以及stochastic-to-deterministic transport gates都通过。

因此不能说specialists“没有task access”或“不能形成greedy joint mode”。

3. Causal learning gain：FAIL

正式失败只来自zero-to-final增益：

N=5 specialist LCB：

0.1139<0.15;

N=6 specialist LCB：

0.1193<0.15;

shared macro LCB：

0.1746<0.20.

这说明随机初始化的deterministic policy在该强约束support下已经具有很高utility，剩余可提升空间被明显压缩。Final达到1并不能使预注册的final-minus-zero门自动通过。

因此精确结论是：

R53没有建立“大于注册幅度的训练因果增益”。
	​


不是：

R53没有建立任务能力.
4. Shared-versus-specialist transport：未识别

描述性地看：

shared与全部specialists都达到deterministic U=1；

within-N ratios通过；

macro ratio通过；

paired shared-minus-specialist noninferiority通过。

但是：

M1 prerequisite按预注册合同失败；

两类模型都处于performance ceiling；

shared单模型接受500次更新，每个specialist只接受100次，虽然aggregate specialist exposure为500；

没有可见的final performance gap用于识别cross-N transfer。

所以不能声称：

shared cross-N learning成功,

也不能声称：

shared cross-N learning失败.

Shared结果可保留为描述性能力证据，但不能升级为variable-N learning claim。

四、可复用因果结论

R53最有价值的结论是：

final competence

⇒causal learning gain.
	​


更完整地：

	​

硬 feasibility support 可以同时：
排除无效joint actions；
让随机初始化本身获得较高任务效用；
因此final optimality不能单独证明PPO学习贡献。
	​

	​


同时：

shared 与 specialists 在 ceiling 上相等

⇒cross-N transfer已被识别.
	​


这也给后续研究一个明确约束：如果目标是审计可扩展表示，第一道门不应继续依赖一个被强action support显著简化、且随机初始化已高分的RL任务。应直接检验表示是否保存决策所需信息。

五、R53退休边界

永久退休以下完整实验组合：

	​

AMQA arrivals/deadlines/horizon
+ U=
F
P
	​

F
B
	​

	​

+anonymous idle-RCMA support
+24,737-parameter recurrent set-pointer
+128K/500-vs-100 exposure
+zero-to-final learning-gain thresholds
+specialist-prerequisite shared comparison.
	​

	​


禁止：

重跑R53；

改 0.15/0.20 增益门；

换初始化；

增加预算、epoch、seed或网络宽度；

使用best checkpoint；

使用temperature、beam search或joint MAP；

删除zero-step comparator；

改task reward或arrival schedule；

加intrinsic reward；

将shared final U=1 升级为variable-N PASS。

但不永久否定：

residual-capacity mask作为一般feasibility primitive；

R49已经通过的active-set/replay接口；

deterministic set/slot representation；

open roster；

heterogeneous event time；

variable-N MARL总体方向。

R53代码可以保留为工程参考，但不再承担算法效能或cross-N学习证据。

六、唯一下一路线：R54-HFSR-G0
Hybrid Field-Slot Representation Sufficiency
	​


该路线已经由独立文献审阅选择为唯一post-R53候选；其明确要求slots、masses与exact residuals是确定性表示，而不是MAT action或PPO factor。

唯一因果边
完整active-set决策信息→固定 M=8 slots+L=2 exact residuals→保留关键匿名分配决策.
	​


它不测试：

PPO credit；

external reward learning；

dynamic membership；

variable T
i
	​

；

skill、KEEP/SET；

intrinsic reward；

UAV任务。

七、R54最小 abandonment gate
1. Toy：Multimodal Capacitated Assignment

每个case包含：

N anonymous members+N capacity-one tasks.

Member为12维：

2D position
2D velocity
4 binary capabilities
energy
current load
availability
continuous observable tie-break

Task为10维：

2D position
4 required capabilities
demand
deadline
priority
continuous observable tie-break

数据必须同时包含：

两个或更多population modes；

one-member-per-task反协调约束；

一个critical task；

恰好一个拥有所需稀有能力的critical member；

unique feasible Hungarian oracle；

mean-alias twins：population coordinate-wise means相同，但critical capability位于不同成员，正确assignment必须改变。

Stable keys只进入ledger，不进入模型。

2. 两个arms
full_active_set_reference

每个focal member通过共享cross-attention读取完整active member set。

hybrid_m8_l2

固定：

M=8,L=2.

Slots：

α
im
	​

=softmax
m
	​

g
θ
	​

(ϕ
i
	​

),
F
m
	​

=
ϵ+∑
i
	​

α
im
	​

∑
i
	​

α
im
	​

ϕ
i
	​

	​

.

Residual score：

r
i
	​

=
	​

ϕ
i
	​

−
m
∑
	​

α
im
	​

F
m
	​

	​

2
2
	​

.

保留 r
i
	​

 最大的两个members。Top-L indices detach，但selected member embeddings不detach。Hybrid decision path只读取：

8 slots+2 exact residual members.

两个arms使用相同member/task encoders、pointer decoder、oracle prefixes、minibatches和slot auxiliary objectives。

3. Exact model budget

每个arm：

49,576 trainable parameters
	​

member encoder  12 -> 64 -> 64          4,992
task encoder    10 -> 64 -> 64          4,864
context Q/K/V/O 64 -> 64               16,640
slot assignment 64 -> 32 -> 8           2,344
AR query        192 -> 64 -> 64         16,512
task key        65 -> 64                 4,224
                                       ------
total                                  49,576

Full-set arm同样实例化和训练slot module，只是不使用compressed tokens作为decision context。

4. Data与训练
training N                   {8,16,32}
unique cases/N               1,024
total training cases         3,072

held-out N                   {8,16,32,64}
held-out cases/N             512
mean-alias cases/N           256

model seed                   64054
data seed                    54054
minibatch/order seed         74054
bootstrap seed               84054

optimizer                    Adam
learning rate                3e-4
updates                      600
batch size                   64
case exposures/arm           38,400
dropout                      0
checkpoint                   exact final
bootstrap                    10,000 paired case clusters

Loss：

L=L
oracle pointer
	​

+0.1L
slot reconstruction
	​

+0.01L
slot mass KL
	​

.

没有environment reward、critic、PPO、low actor、skills、membership events或duration。

八、R54互斥分支
M0：implementation validity

必须全部满足：

unique feasible oracle和唯一critical member；

两arms逐项配对初始化、batch、order与prefix；

每arm精确49,576参数和600 steps；

slots、mass和residual selection完全确定性；

slot policy log-probability数量为0；

pointer teacher-forcing error：

≤10
−6
;

simultaneous member/task permutation error：

≤10
−6
;

junk-padding error：

≤10
−6
;

task collision严格为0；

hybrid token数始终为10；

hybrid路径没有member-member N×N tensor；

gradients、parameters与loss均有限；

exact-final checkpoint reload error为0。

失败：

INVALID_R54_HFSR_WIRING

唯一动作：只修明确的generator、oracle、equivariance、padding、replay、parameter-count或mask defect，原合同重跑。

M1：full-set prerequisite

对每个held-out N：

token accuracy≥0.98,
critical assignment accuracy≥0.99,
normalized oracle-cost regret≤0.01.

并要求：

macro exact-roster success≥0.60,
exact-roster success at N=64≥0.20.

失败：

NO_ACCESS_R54_FULL_SET_REFERENCE

唯一动作：永久退休精确toy、generator、model和gate；不得解释hybrid结果，不增加数据或网络。

M2：hybrid sufficiency

对每个held-out N：

token accuracy≥0.96,
critical assignment accuracy≥0.95,
normalized regret≤0.03.

同时要求：

UCB
95
	​

[regret
hybrid
	​

−regret
full
	​

]<0.02∀N,
exact
macro
full
	​

+10
−8
exact
macro
hybrid
	​

	​

≥0.80,
exact
N64
full
	​

+10
−8
exact
N64
hybrid
	​

	​

≥0.75,
P[critical member进入exact residual]≥0.90,
mean-alias critical-decision accuracy≥0.90,

以及slot effective count中位数：

medianexp[−
m
∑
	​

ν
m
	​

log(ν
m
	​

+10
−8
)]≥4.

失败：

VALID_FAIL_R54_HYBRID_REPRESENTATION

绑定 abandonment：

永久退休精确 M=8,L=2；

永久退休reconstruction-error residual selection；

不改 M,L、宽度、loss coefficients、数据、seed或阈值；

不自动换成ISAB、attention slots、graphon、mean field或更大的residual；

不进入dynamic membership或variable-time gate。

全部通过：

PASS_R54_HYBRID_REPRESENTATION

唯一下一动作：

注册固定membership、固定/common external clock下的 full_set_reference versus hybrid_field_slot ordinary-learning transport gate。

九、永久禁止的救援

以下均禁止：

任何R53重跑或结果重判；

把R53 final U=1改写为registered PASS；

删除final-minus-zero prerequisite；

改R53 threshold、seed、初始化、budget、model或evaluation；

在R54增加第三个parallel arm；

调整 M/L；

加pure mean-field、GNN、ExpoComm或Sable并行路线；

在R54加入reward、PPO、membership churn、variable T
i
	​

、skills或intrinsic；

直接进入S7/UAV；

根据R54结果事后修改generator、oracle、loss或threshold。

研究原则要求失败结果保留为约束，并且只有明确的INVALID才能在科学阈值不变时修复重跑。

最终单一决定
	​

R53 registered status remains
NO_ACCESS_R53_RCMA_SPECIALISTS;
没有branch-changing M0 defect；
“NO ACCESS”在科学表述上过宽，
精确失败对象是预注册的causal learning gain；
RCMA action support正确，所有final policies具备最优能力；
RCMA自身的学习因果贡献未被matched ablation识别；
shared-versus-specialist transport因ceiling和M1失败而未识别；
精确R53 task/comparator/gain-gate永久退休，不救援；
唯一下一条路线为R54-HFSR-G0；
先用监督式full-set prerequisite检验
M=8,L=2压缩是否保留关键决策信息；
R54 PASS前不进入ordinary RL、dynamic membership、
variable T
i
	​

、skills、intrinsic或UAV训练。
	​

	​
