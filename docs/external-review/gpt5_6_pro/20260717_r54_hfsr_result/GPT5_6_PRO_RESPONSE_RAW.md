明确裁决
CONFIRM_NO_ACCESS_R54_FULL_SET_REFERENCE
	​

RETIRE_THE_EXACT_R54_HFSR_CONTRACT
	​

SELECT R55-ABRP-G0
	​


其中：

ABRP： Anonymous Bipartite Relational Pointer
	​


R54 是一次实现有效，但 uncompressed full-set prerequisite 本身无访问的实验。它不能支持关于 field-slot 压缩损失的结论；hybrid_m8_l2 必须继续隔离。

唯一下一条因果边为：

	​

删除全局 member-set attention、slots 和 residual selector
+直接建模 focal-member / candidate-entity 关系
+保留 capacity-feasible autoregressive support
→fixed-N ordinary task access
→shared variable-N learning.
	​

	​


这不是给现有系统再增加一个模块，而是用一个更小、更直接的关系策略替换 R54 的全局表示瓶颈。

一、M0 validity verdict
M0 VALID
	​


未发现会改变正式分支的 generator、oracle、模型、padding、permutation、replay、训练或 checkpoint 缺陷。

1. 首次 invalid run 的修复合法

第一次正式运行只暴露 masked padding 的浮点误差：

1.67×10
−6
>10
−6
.

修复仅在发现 masked tokens 时先将 active tokens compact，再执行 context 线性代数，避免加入 masked junk 后改变 GEMM 宽度和浮点归约顺序。它没有改变训练数据、loss、参数量、更新数、模型可见信息或科学阈值。修复后的新运行得到：

full padding error      0
hybrid padding error    0
full permutation error  8.34e-7
hybrid permutation      7.75e-7
replay errors           0
checkpoint errors       0
collisions              0

因此首次 invalid attempt 不产生科学结果；修复后的 retry 是权威运行。

2. Generator 和 oracle 符合注册语义

Generator 确实建立了：

两个对称的 member modes；

一个 critical task；

恰好一个具备 critical capability 的 member；

critical capability 在 mean-alias twins 中移动；

capacity-one Hungarian matching；

capability-infeasible edge 的 1,000 cost；

正的唯一性 margin。

正式 JSON 中：

critical qualification errors   0
mean-alias population error     0
minimum unique margin           1.346e-4
collision count                 0
3. 两个 arms 是注册的 capacity-matched pair

两个模型：

均为 49,576 参数；

从逐位相同参数开始；

接收同一 minibatch；

使用同一 external member order；

teacher-force 同一 oracle prefix；

各执行 600 optimizer steps、38,400 case exposures；

均训练同一个 slot module及其辅助 loss。

Full-set arm真实使用全部 member embeddings作为context tokens；hybrid arm使用八个slots和两个exact residuals。随后两者使用同一个AR query和task pointer。

需要记录一个不改变分支的审计弱点：runner 中 paired_prefix_mismatch_count 比较的是同一 tensor 与自身，而 paired_batch_mismatch_count 没有独立增量逻辑。不过两个arms确实在同一循环中直接接收同一个 batch 和 inputs，因此真实配对性质成立；缺陷只在冗余audit counter，而不在数据路径。

4. 正式分支实现正确

Runner 明确规定：

M0 fail           -> INVALID_R54_HFSR_WIRING
M0 pass/M1 fail   -> NO_ACCESS_R54_FULL_SET_REFERENCE
M0/M1 pass,
M2 fail           -> VALID_FAIL_R54_HYBRID_REPRESENTATION
M0/M1/M2 pass     -> PASS_R54_HYBRID_REPRESENTATION

所以当前 NO_ACCESS_R54_FULL_SET_REFERENCE 是注册合同的正确终端分支，不需要第三次运行。

二、最强可复用因果结论
1. “看到了完整 active set”不等于“能够利用完整 active set”

Full-set reference拥有全部 member tokens，但其held-out表现随 N 快速退化：

N	Token accuracy	Critical accuracy	Exact roster
8	0.9021	0.6934	0.6328
16	0.7939	0.4570	0.1367
32	0.4999	0.2207	0
64	0.2762	0.1152	0

Macro exact-roster success只有：

0.19238.

五项M1检查全部失败。

因此：

uncompressed information availability

⇒supervised decision access.
	​


Full-set reference仍然可能因以下任一对象失败：

focal-to-member attention的归纳偏置；

task pointer的间接条件化；
-长AR序列上的误差累积；

token-mean imitation objective；

slot auxiliary loss对共享member encoder的影响；

600-step优化合同；

toy本身的combinatorial难度。

R54没有识别这些解释中的唯一根因。

2. 一个critical decision在loss中的权重随 N 稀释

注册pointer loss为全部AR tokens的平均：

L
pointer
	​

=−
N
1
	​

i=1
∑
N
	​

logπ(a
i
⋆
	​

).

每个case只有一个critical task，因此critical decision在pointer objective中的直接权重为：

O(1/N).

与此同时，critical assignment一旦不可行，就会触发1,000级cost penalty。这个“训练权重随 N 降低、评估代价极高”的结构与observed critical accuracy下降一致。

这是一项结构诊断，不是已验证的唯一失败原因；不能通过给critical token重新加权来救援R54。

3. Hybrid compression loss完全未被识别

由于M1 prerequisite失败，不能用以下任何现象评价field slots：

hybrid与full macro exact ratio约0.977；

hybrid在 N=8 略高于full；

critical residual inclusion只有约0.101；

slots effective count约7.4；

hybrid的absolute regret和critical accuracy很差。

这些均是audit-only。

尤其是：

full exact
hybrid exact
	​

≈0.98

没有科学含义，因为分母reference本身未达到access。

正确结论是：

field-slot compression quality = UNIDENTIFIED.
	​


不是：

field slots失败

也不是：

field slots通过.
三、精确退休边界

永久退休以下完整组合：

	​

R54 multimodal capacitated-assignment generator
+rare-critical / mean-alias construction
+49,576-param focal-to-full-set cross-attention reference
+同一模型中的slot reconstruction与mass-KL辅助目标
+hybrid M=8,L=2 candidate
+reconstruction-error residual selection
+600-update、38,400-exposure监督合同
+M0/M1/M2 threshold gate.
	​

	​


禁止通过以下方式重开：

增加training cases或updates；
-扩大hidden width；
-修改loss weights；
-给critical token加权；
-更换optimizer或learning rate；
-换seed；
-修改decoder；
-放宽M1门槛；
-调整 M 或 L；
-更换residual salience score；
-用best checkpoint；
-将N64移出评估；
-根据hybrid audit数值重新解释M2。

该边界与注册分支及provisional disposition一致。

但R54不退休：

anonymous active-set接口；

R49已经证明的permutation、mask、padding和replay语义；
-一般deterministic set representations；
-一般exact critical-member protection；
-variable-N MARL；
-event-owned SMDP credit；
-dynamic membership或variable time作为未来独立问题。

四、ARES-SMDP与文献原则的重新裁决
保留：研究顺序与概率边界

ARES-SMDP仍可保留为一种研究排序和数据合同：

variable-N ordinary learning先于dynamic membership；

dynamic membership先于heterogeneous T
i
	​

；

deterministic representations不拥有policy log-probability；

只有真实sampled ready-member actions进入PPO ratio；

future event credit必须使用agent-owned history与 γ
T
i
	​

。

这些原则不依赖R54成功。文献审阅也明确指出，没有一篇论文完整解决join/rejoin、survivor history和per-agent T
i
	​

，因此串行验证仍然必要。

保留：anonymous shared relational processing

InforMARL最有价值的原则不是“必须用full-set GNN”，而是：

同一共享关系函数作用于任意数量的匿名nodes/edges.
	​


其active-set batching、共享图运算和pooling仍是合理启发。

下一路线只吸收其中的shared relation function，不吸收full-set global attention。

暂停/不支持：field-slot architecture

以下机制当前没有上游授权：

fixed-M population slots；
-slot mass作为协调表示；
-reconstruction-error top-L residual；
-slot coordinator；
-full-set attention作为其prerequisite reference。

因此：

ARES-SMDP保留为控制面与实验顺序，HFSR representation branch关闭。
	​


Sable、ExpoComm、mean field和稀疏GNN不得作为R54后自动替代物。文献disposition本身也禁止在第一阶段同时堆叠这些机制。

ACE的membership shell和ACAC的duration-correct credit继续延期；本轮不实现。

五、唯一下一条路线：R55-ABRP-G0
Anonymous Bipartite Relational Pointer

R54使用的决策路径为：

x
i
	​

→Attention(x
i
	​

,{x
j
	​

}
j=1
N
	​

)→query→y
k
	​

.

但注册oracle cost本身主要是member–task pairwise关系：

C
ik
	​

=C(x
i
	​

,y
k
	​

).

R55直接删除中间的global member context：

ℓ
ik
	​

=f
θ
	​

(x
i
	​

, y
k
	​

, c
k
res
	​

, log(1+N)).
	​


联合动作仍通过capacity-masked autoregression形成：

π(a
t
	​

∣s
t
	​

)=
j=1
∏
N
	​

π(a
σ(j),t
	​

∣x
σ(j),t
	​

,{y
k
	​

},c
t
(j−1)
	​

).

这测试：

一个不编码“其他成员集合”的共享edge policy，是否可以仅通过当前focal–entity关系和applied capacity prefix完成可变规模协调。

六、唯一新toy：Anonymous Typed Backlog Matching
1. Team size与类型
N∈{4,8,12,16},C=4.

每个episode内membership稳定。

Reset时：

每个capability type恰有 N/4 个agents；

每个requirement type恰有 N/4 个productive queues；

agent keys和queue keys独立随机排列；

keys只进入ledger，不进入network。

Capabilities和requirements是可观察资源属性，不是persistent agent ID或人为角色。

2. 时间与workload

固定：

H=8.

每个primitive step开始时，每个productive queue增加一个work unit：

b
q,t
pre
	​

=b
q,t−1
post
	​

+1.

因此每episode总到达量为：

HN=8N.

增加team size会同时增加：

agents；

productive queues；

work arrivals；

joint AR sequence length。

这是task-dynamic variable-N，不是仅改变padding长度。

3. Action support

动作entities：

N productive queues+1 anonymous idle.

Capacity：

c
q
	​

=1for productive queues,
c
idle
	​

=N.

按外生agent order进行AR sampling。一个productive queue被前序agent选择后，对后序agents立即mask。

Capability mismatch不被mask；策略必须学习它。不得输入预计算的is_compatible或oracle assignment。

4. Service transition

若agent i 选择productive queue q，且：

cap
i
	​

=req
q
	​


并且：

b
q,t
pre
	​

>0,

则：

b
q,t
post
	​

=b
q,t
pre
	​

−1.

否则不服务。

Idle无状态或reward效果。

由于每个step每queue增加1，而每queue每step最多服务1，一次遗漏不能在未来完全补回；其work会一直保留到episode末。

5. 唯一外部奖励

所有中间steps：

r
t
	​

=0,t<7.

Terminal utility：

U=1−
8N
∑
q
	​

b
q,7
post
	​

	​

.
	​


它正好是整个episode按时提供的work fraction。

没有：

per-step service reward；
-capability bonus；
-progress shaping；
-duplicate penalty；
-team-size reward；
-role reward；
-intrinsic reward。

6. M0 schedules
Matched schedule

每个step将每个agent匹配到一个不同的same-capability queue：

U=1.
Cyclic-mismatch schedule

所有type-c agents选择不同的type-(c+1)mod4 queues：

U=0.
All-idle schedule

所有agents选择idle：

U=0.
七、R55模型：用edge scorer替换set representation
Actor-visible member：4维
capability one-hot[4]
Actor-visible entity：6维
is_productive
requirement one-hot[4]
backlog / 8

Idle为全零。

Edge input：12维
member capability[4]
entity fields[6]
normalized residual capacity
log(1+N) / log(17)

Actor：

12 -> 64 GELU -> 32 GELU -> 1
Centralized critic：13维输入
mean active-member capability[4]
mean active-entity fields[6]
t / 8
total backlog / (8N)
log(1+N) / log(17)

Critic：

13 -> 64 GELU -> 1

Exact trainable parameter count：

3,906
	​

.

Actor最后一层weight和bias均zero-init，使初始action distribution在有效support内中性；shared和所有specialists逐位相同。

明确不存在：

member encoder；
-member pooling；
-member-member attention；
-GNN；
-slots；
-exact residual selector；
-recurrent hidden；
-agent ID；
-slot embedding。

每步计算：

O(N(N+1))=O(NK)

个member–entity edges，但不产生member–member N×N tensor。

八、arms、预算与优化
Arms
shared_variable_N_ABRP
fixed_N_ABRP_specialist_family

四个specialists分别训练：

N=4,8,12,16.
Exposure
balanced cycles                 100
N-specific batches/cycle       4
episodes/batch                  32
episode / rollout              8 / 8

transitions/N/arm              25,600
transitions/arm               102,400
agent-token decisions/arm   1,024,000

shared optimizer steps           100
specialist steps/model           100
specialist aggregate             400
PPO epochs                         1
collected-batch reuse              0

每个cycle：

收集四个 N 的paired shared/specialist batches；

每个specialist在自己的batch上更新一次；

shared分别计算四个N-specific losses和advantages；

将四个loss等权平均；

shared执行一次optimizer step。

因此shared和每个specialist的per-model optimizer steps相同；shared利用全部四个规模的数据，这是所测试的共享机制。

PPO
gamma               0.99
GAE lambda           0.95
learning rate        3e-4
PPO epochs           1
clip                  0.2
entropy coefficient  0.01
value coefficient    0.5
gradient clip        0.5

Advantages按 N 独立标准化；token loss在active N 维度平均。

Seeds
model/init          55055
training ledger     65055
orders/actions      75055
evaluation ledger   85055
bootstrap           95055
Evaluation

Zero-step与exact-final分别执行：

256 stochastic episodes/N/arm
256 deterministic episodes/N/arm

Shared和对应specialist使用同一：

capability/requirement permutation；
-agent order；
-entity order；
-sampling uniform；
-arrival ledger。

Bootstrap 10,000次，cluster为同一 N 下的paired episode。Macro先在每个 N 内重采样，再对四个 N 等权平均。

九、最小 abandonment gate
M0：implementation validity

必须全部满足：

每个 N 恰有 N/4 agents和queues属于每个capability type；

每step每productive queue恰好到达一单位work；

matched、cyclic-mismatch、all-idle schedules产生 1,0,0；

只有最后一步reward可非零；

terminal reward严格等于完成work fraction；

capability mismatch不进入mask；

productive capacity为1，idle capacity为 N；

sample/replay logp、capacity、prefix和mask误差：

≤10
−6
;

masked probability mass为0；

simultaneous member/entity permutation和junk-padding误差：

≤10
−6
;

actor中不存在member-set encoder、pool、attention、GNN、slot或residual路径；

member-member tensor count为0；

exact parameter count为3,906，state-dict shapes与 N 无关；

shared和specialists初始参数逐位相同；

zero-step shared/specialist traces逐项相同；

exact 102,400 transitions/arm、25,600/N及100 shared/100-per-specialist steps；

PPO epoch1，无data reuse；

所有gradients、losses、parameters有限且相关模块产生drift；

exact-final checkpoint reload error为0。

失败：

INVALID_R55_ABRP_WIRING

唯一动作：只修明确的transition、edge-input、capacity、mask、replay、pairing、count或checkpoint defect，并原合同重跑。

M1：fixed-N ordinary access

对每个 N 必须同时满足：

Initial ceiling
U
ˉ
N,zero
spec,det
	​

≤0.40.
Final performance
U
ˉ
N
spec,det
	​

≥0.90,
U
ˉ
N
spec,stoch
	​

≥0.80.

每个capability type的final deterministic fulfillment：

c
min
	​

F
N,c
spec,det
	​

≥0.85.
Mode transport
UCB
95
	​

[U
N
spec,stoch
	​

−U
N
spec,det
	​

]<0.15.
Causal learning gain
LCB
95
	​

[U
N,final
spec,det
	​

−U
N,zero
spec,det
	​

]>0.40.

四个连续64-episode deterministic blocks中至少三个满足：

U
ˉ
N,block
spec,det
	​

≥0.85.

Equal-N macro：

U
ˉ
spec,det
≥0.92.

M0通过但M1失败：

NO_ACCESS_R55_ABRP_SPECIALISTS

绑定动作：

永久退休精确typed-backlog dynamics；

永久退休该raw-edge policy、3,906参数模型和100-cycle合同；

隔离shared结果；

不增加steps、seed、width、entropy、reward或threshold；

不恢复R54 slots/full-set reference。

M2：shared variable-N

Shared每个 N 必须满足：

U
ˉ
N
shared,det
	​

≥0.88,
U
ˉ
N
shared,stoch
	​

≥0.78,
c
min
	​

F
N,c
shared,det
	​

≥0.82,
UCB
95
	​

[U
N
shared,stoch
	​

−U
N
shared,det
	​

]<0.15.

Macro：

U
ˉ
shared,det
≥0.90.

相对specialists：

N
min
	​

U
ˉ
N
spec,det
	​

+10
−8
U
ˉ
N
shared,det
	​

	​

≥0.95,
U
ˉ
spec,det
+10
−8
U
ˉ
shared,det
	​

≥0.97.

Paired macro noninferiority：

LCB
95
	​

[
4
1
	​

N
∑
	​

(U
N
shared,det
	​

−U
N
spec,det
	​

)]>−0.04.

Shared zero-to-final gain：

LCB
95
	​

[
U
ˉ
final
shared,det
	​

−
U
ˉ
zero
shared,det
	​

]>0.40.

M0、M1通过但M2失败：

VALID_FAIL_R55_SHARED_VARIABLE_N

唯一动作：

永久退休精确shared ABRP contract，并停止当前variable-N learning line，进入一次只读架构失败审查。

PASS
PASS_R55_ABRP_VARIABLE_N

仅当：

M0∧M1∧M2.

允许结论仅为：

在pairwise-sufficient、capacity-coupled的匿名动态任务中，一个不读取其他成员集合的共享edge policy能够跨多个team sizes接近fixed-N specialists。

PASS后只允许：

冻结R55为ordinary variable-N baseline，并提交一次新的后续设计审阅。

本裁决不直接授权episode内join/leave、heterogeneous T
i
	​

、skills、intrinsic reward或UAV实现。

十、继续禁止

不得：

重跑或救援R54；

将hybrid audit解释为compression failure或success；

调整R54 M/L；

立即改用GNN、ISAB、mean field、ExpoComm或Sable；

在R55加入第三个表示arm；

使用precomputed capability compatibility mask；

使用agent ID、slot-specific head或learned agent order；

加入中间service reward或task shaping；

加入skills、KEEP/SET、variable lifetime或intrinsic reward；

同时测试dynamic membership或heterogeneous time；

进入S7/UAV；

通过增加数据、seed、network、PPO epochs、threshold修改或best checkpoint救援有效失败。

研究纪律明确要求下游机制在上游失败时停止，并将负结果作为约束，而非通过重命名或扩容重新运行。

最终单一决定
	​

R54 = CONFIRMED NO ACCESS;
最终retry的M0有效，不再运行R54；
full-set reference本身无法学习注册matching substrate；
因此field-slot compression loss完全未识别；
精确R54 toy/generator/model/loss/gate永久退休；
ARES-SMDP只保留为事件所有权、概率边界与串行研究原则；
fixed-M slots、reconstruction residual和full-set attention路径关闭；
唯一下一路线为R55-ABRP-G0：
用直接member–entity edge scoring替换全局set representation，
先由fixed-N specialists建立ordinary access，
再检验一个shared anonymous policy的cross-N transport；
任一有效M1或M2失败均永久退休精确路线，
不调参、不扩种子、不叠加文献模块。
	​

	​
