1. Frozen task contract

Disposition：冻结 BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS_G0 的代码就绪合同。
实现包名固定为：

NONCALENDAR_HETEROGENEOUS_TRACKING_G0

本轮不重新选择研究路线；H、C、S、D 四个对象及“停止 Generic-SHORT supplied-executor F1 线”的处置已经确定。本答复只补齐实现所需的状态、动力学、信息、预算和数值门。

1.1 基本空间
episode horizon H = 80 physical steps
maximum lifecycle capacity = 6
primitive action count = 3
actor observation width = 15
critic common-field width = 8

Primitive action是物理推力，不是技能、角色或supplied executor：

action 0 -> thrust -1
action 1 -> thrust  0
action 2 -> thrust +1

每个opaque lifecycle i 的环境状态为：

s
i
	​

=(status
i
	​

,membership_epoch
i
	​

,x
i
	​

,u
i
prev
	​

,r
i
act
	​

,g
i
	​

,d
i
	​

,c
i
	​

,n
i
active
	​

)

其中：

status ∈ {NOT_JOINED, ACTIVE, TEMPORARILY_ABSENT, TERMINAL}；

x
i
	​

∈{−2,−1,0,1,2} 是本地受控物理状态；

u
i
prev
	​

∈{−1,0,1} 是上一primitive thrust；

r
i
act
	​

∈{0,…,16} 是当前相同primitive action的连续active-step run length，超过16截断；

g
i
	​

∈{−2,+2} 是当前在线需求的reference target；

d
i
	​

 是当前target segment尚余的active steps，只属于environment ledger和H/S solver，不进入C/D actor或critic；

c
i
	​

∈{0,1,2} 是连续位于当前target的active-step streak，封顶2；

n
i
active
	​

 是生命周期累计active steps。

1.2 Primitive transition

在physical step t，对每个active lifecycle采取 u
i,t
	​

∈{−1,0,1}：

x
i,t+1
	​

=clip(x
i,t
	​

+u
i,t
	​

,−2,2).

当步tracking quality为：

q
i,t
	​

=1−
4
∣x
i,t+1
	​

−g
i,t
	​

∣
	​

∈{0,0.25,0.5,0.75,1}.

Streak更新为：

c
i,t+1
	​

={
min(c
i,t
	​

+1,2),
0,
	​

x
i,t+1
	​

=g
i,t
	​

,
otherwise.
	​


Action-run更新为：

r
i,t+1
act
	​

={
min(r
i,t
act
	​

+1,16),
1,
	​

u
i,t
	​

=u
i,t
prev
	​

,
u
i,t
	​


=u
i,t
prev
	​

.
	​


随后：

active-step counter加一；

当前target segment remaining减一；

segment在该active step结束时，若 c
i,t+1
	​

=2，则该segment完成；

segment结束后，下一active step令target翻转：

g
i
new
	​

=−g
i
old
	​

;

新segment duration由已经ledgered、但对policy未来不可见的duration stream给出；

新segment开始时target_changed=1一step，streak重置为0。

这是一个离散、有限状态的closed-loop tracking process。Primitive action不是任务角色标签；同一推力的作用取决于当前位置、当前reference和此前连续控制。

1.3 在线需求过程

每个lifecycle拥有独立的active-time target segment stream。

Training及IID evaluation duration support：

{5, 9, 13}

Held-out duration support：

{5, 7, 9}

每连续三个segment是相应support的一次均匀随机排列；下一个三段block重新独立采样排列。初始target符号均匀采样于{−2,+2}，之后每个segment边界确定性翻转。

Duration、下一target边界和未来membership均不进入causal policy。Policy只在新segment实际开始时看到当前target和target_changed。

1.4 Sign-inversion配对

所有训练和评价episode按两两配对：

episode e:
  base_id = floor(e / 2)
  sign_parity = e mod 2

同一base pair共享：

membership；

duration排列；

presentation和AR order；

action uniforms；
-初始环境物理状态。

唯一差异是全部target符号相反：

g
i,t
(2b+1)
	​

=−g
i,t
(2b)
	​

.

这为C提供精确的信息-null，而不是依赖其训练是否充分。

1.5 Anonymous membership lifecycle

每个base ledger先均匀采样六个opaque routing keys的一次排列 ρ
b
	​

。Routing key和其排列rank从不进入网络。

Training及IID profile
t = 0:
  N0 ~ Uniform{3,4}
  rho[0:N0] genuine JOIN

t = 20:
  one uniformly selected initial lifecycle TEMPORARY_LEAVE

t = 40:
  same lifecycle REJOIN
  rho[N0] genuine JOIN

t = 60:
  one uniformly selected active lifecycle TERMINAL_LEAVE

Roster size为：

3 -> 2 -> 4 -> 3
or
4 -> 3 -> 5 -> 4
Held-out profile
t = 0:
  N0 ~ Uniform{2,5}
  rho[0:N0] genuine JOIN

t = 12:
  one uniformly selected initial lifecycle TEMPORARY_LEAVE

t = 36:
  same lifecycle REJOIN
  rho[N0] genuine JOIN

t = 68:
  one uniformly selected active lifecycle TERMINAL_LEAVE

Roster size为：

2 -> 1 -> 3 -> 2
or
5 -> 4 -> 6 -> 5

Lifecycle规则：

genuine JOIN：

epoch 0；

x=0；

previous thrust 0；

action-run 0；

recurrent state 0；

分配第一个target segment；

temporary LEAVE：

冻结 x,u
prev
,r
act
,g,d,c,n
active
 和recurrent state；

absence期间不推进target active-time；

不产生actor row或reward denominator；

REJOIN：

同一opaque lifecycle；

epoch加一；

恢复全部冻结状态；

terminal LEAVE：

当前未结束target segment被censor，不进入segment-completion denominator；

lifecycle物理与recurrent state在边界finalization后删除；

horizon结束时尚未完成的segment同样censor。

这些规则沿用已经验证的“JOIN零状态、temporary freeze、REJOIN恢复、terminal discard、survivor continuity”语义，而非重新发明membership所有权。

1.6 外部任务结果

定义：

A=
∑
t=0
79
	​

∣A
t
	​

∣
∑
t=0
79
	​

∑
i∈A
t
	​

	​

q
i,t
	​

	​


为active-member tracking quality。

定义：

B=
在terminal leave或horizon censor前实际结束的segments
完成且在结束时拥有两步target streak的segments
	​

.

每个formal episode必须至少有一个eligible ended segment，否则M0失败。

最终utility：

U=
AB
	​

.

Reward为：

r_t = 0                    for t = 0,...,78
r_79 = U

没有中间reward、shaping、switch reward、duration payment、role reward或intrinsic reward。

2. Why the task identifies heterogeneous lifetime
2.1 Member commitment lengths由在线状态决定

从 x=+2 到 g=−2 至多需要四个连续-1 thrust；到达后至少再保持一个active step，才能在segment结束时取得两步target streak。最短segment为5，因此causal reactive rule：

u
i,t
	​

=
⎩
⎨
⎧
	​

+1,
−1,
0,
	​

g
i,t
	​

>x
i,t
	​

,
g
i,t
	​

<x
i,t
	​

,
g
i,t
	​

=x
i,t
	​

	​


可以完成每个未censor segment，而不需要未来duration。

不同成员：

使用独立duration排列；

拥有不同initial target；

target clock按各自active time推进；

temporary absence只冻结该成员；

genuine JOIN在不同physical time开始新的active-time stream。

因此，相同physical time下，不同成员的下一target边界、所需thrust run和后续coast run通常不同。

作为M0中的task-identifiability检查，每个128个held-out base ledgers必须同时满足：

>= 20 physical steps:
  at least two active lifecycles have current-segment remaining
  active durations differing by >= 2

>= 3 lifecycle instances:
  each undergoes at least one completed target transition

未满足则是INVALID_BENCHMARK_IDENTIFIABILITY_G0，而不是通过learner或threshold补救。

2.2 S严格隔离shared-lifetime压力

S拥有完整未来信息，却只可在公共renewal times：

t ∈ {0,4,8,...,76}

为各active member更新其primitive command；其余步骤必须保持上一command。

Genuine JOIN和REJOIN允许该到达member立即选择一次初始command，但不会给所有survivors额外renewal。Temporary absence冻结command。

固定周期4并非人为拉长到超过模型记忆；4正好等于从−2到+2的process diameter。它是能够在一个shared segment中完成全状态迁移的最短整周期共同clock。S仍然失败时，原因是各成员的target边界无法同时与一个公共clock对齐，而不是单个action本身执行不够久。

2.3 Calendar/static策略存在精确上界

C看不到target、error或target-change fields，而且target不改变任何C-visible物理动力学。对sign-inversion pair，C获得相同observation、hidden start、order和action uniforms，因此产生相同primitive actions与x trajectory。

对于任意 x∈[−2,2]：

q(x,+2)+q(x,−2)=1.

所以每个inversion pair的tracking均值精确为：

2
A
+
+A
−
	​

=0.5.

同一action trajectory不可能在对应的正、负target segment末尾同时连续两步位于+2和−2，因此：

2
B
+
+B
−
	​

≤0.5.

由Cauchy–Schwarz：

2
A
+
B
+
	​

+
A
−
B
−
	​

	​

≤0.5.

因此C即使具有完整RNN容量、充分优化、absolute time、membership clock和persistent internal state，也不能仅凭calendar pre-positioning越过0.5 pair ceiling。这个null不依赖刻意削弱RNN，也不依赖C恰好未学会。项目原则要求通过信息与held-out行为区分普通memory和temporal abstraction，而不是人为制造RNN memory failure。

3. Exact H/C/S/D interfaces
3.1 C/D的15维active-member observation

字段0–7在同一环境的全部active rows上完全相同：

Index	字段	范围
0	t/80	[0,0.9875]
1	log(1+N
t
	​

)/log7	[0,1]
2	active mean x
i
	​

/2	[-1,1]
3	active mean g
i
	​

/2	[-1,1]
4	active mean (g
i
	​

−x
i
	​

)/4	[-1,1]
5	active mean (	g_i-x_i
6	active fraction with target_changed=1	[0,1]
7	active fraction with current JOIN或REJOIN	[0,1]

字段8–14是focal-local：

Index	字段	范围
8	x
i
	​

/2	[-1,1]
9	g
i
	​

/2	{-1,+1}
10	(g
i
	​

−x
i
	​

)/4	[-1,1]
11	target_changed	{0,1}
12	event code：JOIN +1，REJOIN -1，ordinary 0	{-1,0,+1}
13	previous thrust	{-1,0,+1}
14	min(r
i
act
	​

,16)/16	[0,1]

Neither arm receives target remaining duration.

3.2 H — constrained hindsight authority
causal status: non-causal ceiling
optimizer steps: 0
model parameters: 0

H读取完整episode ledger，包括未来target segment boundaries、membership和order，但：

只能对当步active members采取一个合法primitive action；

不得改变membership、target、duration、presentation、order或reward；

每个active member每个physical step可独立更新action；

inactive member没有action；

environment transition与C/D完全相同。

H使用有限状态exact Pareto DP。每个lifecycle DP state只需：

x ∈ {-2,-1,0,1,2}
target streak ∈ {0,1,2}

标签为：

integer tracking quarter-units
completed segment count

跨lifecycles卷积Pareto labels后，选择最大U的合法episode trajectory。不得分别拼接不同trajectory的最佳A与最佳B。

H只回答结构authority；它不是causal policy或算法baseline。

3.3 C — matched calendar/static recurrent null
causal status: causal learned policy
control frequency: every active member, every physical step

C在进入actor、critic、rollout storage与replay前，将以下字段精确置零：

common fields: 3,4,5,6
local fields:  9,10,11

其余字段和D完全相同。C保留：

absolute time；

roster size；

current physical x；

JOIN/REJOIN；

previous action及action run；

recurrent state；

active-set communication；

earlier-action prefix。

因此C是“任何利用time、membership phase、internal memory或固定pre-positioning的ordinary policy”null，而不是弱手写controller。

3.4 S — shared-renewal/fixed-lifetime hindsight ceiling
causal status: non-causal ceiling
optimizer steps: 0
model parameters: 0
shared renewal period: 4 physical steps

S读取与H相同的完整未来ledger，但合法action change仅允许于：

t mod 4 == 0
or
the focal lifecycle is a genuine JOIN/REJOIN at that step

所有其他active steps保持该member上一primitive command。

S可在一个shared renewal time为不同成员选择不同thrust；其限制是共同change time，不是共同action。它没有duration action、catalogue或learned scheduler。

3.5 D — ordinary causal recurrent access
causal status: causal learned policy
control frequency: every active member, every physical step

D读取完整的当前15维observation，但不读取未来target、duration、future membership、reward history或oracle plan。

C与D均使用已经通过clean-carrier access的ordinary primitive-AR结构：

shared member encoder；

active-member embedding sum；

log(1+N)；

每lifecycle GRU；

同一primitive frontier内earlier-action counts；

一个centralized team value。

每个physical step的active order由独立order RNG均匀采样、完整记录并teacher-force replay。Order只改变actor factorization；environment同时应用全部primitive actions。外部order不产生policy gradient，遵循既有identity-free recorded-order原则。

3.6 Recurrence和membership ownership

C/D：

genuine JOIN：hidden全零；

active lifecycle：hidden只在其actor token时更新；

temporary LEAVE：hidden冻结；

REJOIN：恢复同一hidden；

terminal LEAVE：hidden删除并永不再次进入active tensor；

unrelated survivor：hidden连续。

这些语义在现有direct和event实现中已有明确的freeze/restore基础；新task只替换环境状态和ledger。

3.7 全部arm禁止的信息

任何causal actor或critic均不得读取：

opaque lifecycle key、其排列rank或membership epoch；

sign-pair parity；

future target、future duration、duration remaining；

future membership；

future order/action uniform；

H/S action plan；

cumulative A,B,U 或terminal reward history；

task role、agent identity或named duty；

supplied skill、high token、KEEP/SET action；

intrinsic、posterior或effect statistic。

4. Frozen training and evaluation budget
4.1 C/D架构

C和D分别持有一个完全相同、初始state byte-equal的DirectPrimitiveARPolicy：

member encoder:
  15 -> 32 -> 32, Tanh/Tanh

active-set context:
  [sum of 32-D member embeddings, log(1+N)]
  33 -> 32, Tanh

per-lifecycle actor GRU:
  input = local embedding 32
        + set context 32
        + earlier-action counts 3
  input width 67
  hidden width 32

action head:
  [hidden 32, prefix counts 3]
  35 -> 32 -> 3, Tanh

team critic:
  [set sum/count 33, common fields 8]
  41 -> 32 -> 1, Tanh

总参数数：

14,980 per arm

不新增critic、attention、graph或communication module。此前clean carrier正是这一ordinary recurrent class取得了近乎完美access，因此该容量不是为制造失败而选的小模型。

4.2 PPO合同
optimizer                  Adam
learning rate              3e-4
gamma                      0.99
GAE lambda                 0.95
policy clip                0.20
value clip                 0.20
value coefficient          0.50
entropy coefficient        0.01
gradient clip              0.50
PPO passes/update          4
BPTT chunk length          20
minibatch                  all 16 env x all four 20-step chunks

BPTT 20大于training最大target duration 13；当前target每步可见于D。该合同没有通过截断关键因果信息制造ordinary-control failure。

4.3 Formal exposure

每arm：

parallel environments      16
episode/rollout horizon    80
outer updates              250
environment transitions    320,000
optimizer steps            1,000
training episodes          4,000

C和D总计：

640,000 environment transitions
2,000 optimizer steps

每个update依次：

在同一16个episode IDs上收集C和D，各包含8个sign-inversion pairs；

两臂均完成collection后；

分别进行四次PPO replay；

清空rollout；

进入下一组16个IDs。

不得让一个arm先更新后再为另一个arm生成同一update的数据。

4.4 Seeds
paired model initialization     58_058
training task/demand ledger     68_058
training presentation/order     78_058
training action uniforms        88_058

IID evaluation task ledger      98_058
held-out evaluation task ledger 99_058
evaluation presentation/order   79_058
evaluation action uniforms      89_058

bootstrap                       108_058

所有RNG使用：

NumPy PCG64(SeedSequence([...]))

训练episode IDs：

0..3999

每个profile的评价episode IDs：

0..255

同一sign pair基于同一个base_id生成除target sign以外的全部随机量。

4.5 Evaluation cells

对C和D分别运行：

Checkpoint	Profile	Deterministic	Stochastic
update 0	IID	256	256
update 0	held-out	256	256
update 250	IID	256	256
update 250	held-out	256	256

每arm共：

2,048 evaluation episodes

H与S只在同一256个held-out ledgers上各执行一次exact deterministic solve。

不选择best checkpoint，不读取中间update作科学判定。

4.6 Checkpoint

保存：

update_000.pt
latest.pt after every complete outer update
update_250.pt

Checkpoint必须包括：

arm mode calendar_masked | demand_visible；

model和optimizer；

completed update；

next training episode ID；
-全部seed/profile headers；

Torch CPU/CUDA RNG；

action/order RNG ownership；

observation-mask schema；

model shape和parameter count。

Resume仅允许在完整80-step episode/update边界；该G0没有open high/skill segment。缺字段、arm mismatch、seed mismatch、mask mismatch或counter mismatch均hard fail。

科学评价只加载update_000.pt与update_250.pt。Final reload后model和optimizer必须逐tensor一致。

5. Numerical estimands and thresholds
5.1 Confidence method

所有paired margins使用：

10,000 percentile-bootstrap resamples
bootstrap seed = 108_058
cluster = one base_id containing both sign-inverted episodes
cluster count = 128
CI = [2.5 percentile, paired mean, 97.5 percentile]

同一次resample保留：

两个sign mates；

C/D；

zero/final；

H/S；

的配对关系。

所有“LCB”均指上述CI的第一个元素，并使用严格不等式>。

5.2 Structural authority H

在held-out 256 episodes上必须同时满足：

A
ˉ
H
	​

≥0.780,
B
ˉ
H
	​

≥0.980,
U
ˉ
H
	​

≥0.880.

Exact solver还必须报告：

every action active-only
every target/membership ledger unchanged
5.3 Calendar/static null C

Final deterministic held-out必须满足：

A
ˉ
C
	​

≤0.550,
B
ˉ
C
	​

≤0.550,
U
ˉ
C
	​

≤0.550.

此外，每个sign pair必须满足：

C primitive action tape equality       exact
C recurrent hidden equality            max error <= 1e-6
C pair mean A                           |mean - 0.5| <= 1e-12
C pair mean B                           <= 0.5 + 1e-12
C pair mean U                           <= 0.5 + 1e-12
5.4 Shared-lifetime pressure S

S必须同时满足绝对非访问条件：

A
ˉ
S
	​

<0.750,
B
ˉ
S
	​

<0.800,
U
ˉ
S
	​

<0.750,

以及H-minus-S paired margins：

LCB
95
	​

(A
H
	​

−A
S
	​

)>0.080,
LCB
95
	​

(B
H
	​

−B
S
	​

)>0.200,
LCB
95
	​

(U
H
	​

−U
S
	​

)>0.150.

任何一项不满足，都不允许声称benchmark具有material heterogeneous-lifetime pressure。

5.5 Ordinary causal access D
IID final deterministic
A
ˉ
D
IID,det
	​

≥0.780,
B
ˉ
D
IID,det
	​

≥0.900,
U
ˉ
D
IID,det
	​

≥0.830.
Held-out final deterministic
A
ˉ
D
HO,det
	​

≥0.720,
B
ˉ
D
HO,det
	​

≥0.850,
U
ˉ
D
HO,det
	​

≥0.780.
Held-out final stochastic
A
ˉ
D
HO,stoch
	​

≥0.650,
B
ˉ
D
HO,stoch
	​

≥0.750,
U
ˉ
D
HO,stoch
	​

≥0.700.
Learning gain
LCB
95
	​

(U
D,250
HO,det
	​

−U
D,0
HO,det
	​

)>0.200.
5.6 D相对C的online-information margin

仅在D已经通过全部ordinary-access gates后读取：

LCB
95
	​

(A
D
HO,det
	​

−A
C
HO,det
	​

)>0.200,
LCB
95
	​

(B
D
HO,det
	​

−B
C
HO,det
	​

)>0.250,
LCB
95
	​

(U
D
HO,det
	​

−U
C
HO,det
	​

)>0.200.
5.7 完整PASS逻辑
PASS =
  H structural floors
  AND C absolute information-null ceilings
  AND S absolute failure
  AND all H-minus-S margins
  AND all D IID/held-out deterministic/stochastic floors
  AND D final-minus-zero margin
  AND all D-minus-C margins

没有UNDERPOWERED分支。

6. Validity and mutually exclusive result branches
6.1 M0 implementation validity

M0必须全部通过：

精确state、action、transition、A/B/U和terminal-only reward；

training/IID duration support精确为{5,9,13}；

held-out support精确为{5,7,9}；

membership counts、times和routing-key permutation精确；

sign pair除target符号外的ledger byte-equal；

C mask字段在collection、critic、storage和replay中精确为零；

C sign-pair observation、action、hidden和order一致；

D仅读取当前target，不读取duration remaining或未来ledger；

H/S solver只改变合法actions；

S只在t mod 4 == 0或focal JOIN/REJOIN时改变action；

tiny-horizon H/S DP与unpruned brute force outcome set完全一致；

每个held-out base ledger满足第2节的heterogeneity-support条件；

anonymous relabeling同步重标ledger、hidden和action rows后，joint distribution/reward不变；

genuine JOIN零hidden，temporary absence冻结，REJOIN恢复，terminal state删除；

C/D update-0 model byte-equal；

每arm精确320,000 transitions、1,000 optimizer steps和4,000 training episodes；

C/D active-row数与各自ledger之和精确且彼此相等；

token、joint、value、hidden和prefix replay error均<=1e-6；

finite losses、gradients和parameters；

D parameter drift >1e-8；

checkpoint model/optimizer/counter/RNG round-trip error为零；

H/S optimizer steps为零；

skill、高层、KEEP/SET、intrinsic、posterior和new-critic counts均为零；

evaluation IDs、sign pairs、uniforms及bootstrap headers精确；

result runner不选择或启动successor。

现有direct实现已经证明active-only sum/count、primitive AR prefix、recurrent replay和PPO可在这一shape/budget下精确工作；新实现不得以改写这些概率语义来通过M0。

6.2 Priority branches
1. INVALID_BENCHMARK_IDENTIFIABILITY_G0

触发：任一M0失败。

处置：

只修具体实现、solver、ledger、replay或checkpoint defect；

task、threshold、seed、budget、model和comparators不变；

K/D/R/B/P权重不更新。

2. REJECT_BENCHMARK_STRUCTURALLY_UNREACHABLE

触发：M0通过，但H任一绝对floor失败。

处置：

拒绝该benchmark；

不读取C、S或D科学结果；

不以reward shaping、更多authority、更多steps或oracle输入救援；

不在该task上实现temporal abstraction。

3. REJECT_BENCHMARK_CALENDAR_IDENTIFIABLE

在以下任一条件成立时触发：

C的held-out deterministic A,B,U 任一超过0.550；或

D已通过ordinary access，但D-minus-C三个LCB中任一未过注册margin。

处置：

支持benchmark-identifiability候选K；

D即使任务得分高，也只能算calendar/static access；

R、B和P均不可在该benchmark上解释；

拒绝该benchmark，不修改target distribution或C mask重新尝试。

4. REJECT_BENCHMARK_NO_HETEROGENEOUS_LIFETIME_PRESSURE

触发：

S的 A,B,U 任何一项不满足严格上界；或

H-minus-S三个LCB任何一项未过门。

处置：

该task可能需要online adaptation，但不需要material individual-lifetime freedom；

R下降；

B/P不进入；

D继续是ordinary solution；

不增大shared period、改变duration support或提高switch cost来制造gap。

5. NO_ACCESS_BENCHMARK_ORDINARY_CONTROL

触发：

H通过；

C信息-null通过；

S pressure通过；

但D的任何IID、held-out、stochastic或learning-gain gate失败。

处置：

不读取hierarchy、R、B或P含义；

不能断言D理论上不足，只能说该benchmark/model/budget没有建立ordinary access；

不扩大hidden、BPTT、budget、seed或加入intrinsic；

停止该benchmark的algorithm line。

6. PASS_BENCHMARK_IDENTIFIABILITY_AND_ORDINARY_ACCESS

触发：M0及第5节全部条件通过。

允许的唯一结论：

该独立benchmark在匿名dynamic membership下结构可达；calendar/static recurrence不能解决；固定shared renewal materially低于individual primitive authority；一个匹配的ordinary recurrent controller能从当前online demand访问IID和held-out任务。

Portfolio更新：

K在该benchmark上显著下降；

D保持mandatory high-weight null；

R首次成为可识别的后续algorithmic alternative；

B仍为低权重条件候选；

P继续park。

PASS只使一个未来、单独审阅的information-matched D-vs-R source具有资格，不自动授权它。

7. Minimal implementation boundary
7.1 精确复用

只复用下列已有能力：

ha_ctse_process/dynamic_roster_direct.py

DirectPrimitiveARPolicy

recurrent replay和PPO algebra

advantage、clip、entropy和gradient合同

state-dict比较工具；

ha_ctse_process/variable_roster_event.py

membership transaction datatypes；

epoch、JOIN/LEAVE/REJOIN语义；

active-only order和fail-closed checkpoint原则；

scripts/run_clean_process_direct_access.py

atomic result/status输出模式；

clean-process test中已经验证的temporary freeze、REJOIN resume、genuine JOIN zero和snapshot测试形式。

不得复用clean actuator作为task process或semantic signal；它仍是action-tape-determined audit state。

7.2 新增路径

只允许新增：

docs/research/designs/
  NONCALENDAR_HETEROGENEOUS_TRACKING_G0.md

ha_ctse_process/
  noncalendar_commitment_testbed.py

scripts/
  run_noncalendar_commitment_benchmark_g0.py

tests/
  ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py

以及由Code Implementation Manager按本合同更新：

docs/project/IMPLEMENTATION_PLAN.md
docs/project/ExpRecord.md

noncalendar_commitment_testbed.py同时拥有：

train/IID/held-out ledger；

environment；

C mask；

H/S exact DP；

tiny brute-force reference；

membership/heterogeneity/sign-pair audits。

不另建solver framework、environment package或representation library。

Runner唯一terminal结果：

<run-root>/result/
  noncalendar_heterogeneous_tracking_g0.json
7.3 替换与删除

删除文件：无。

科学上的替换是：

Generic-SHORT predictable supplied-executor evidence substrate
  ->
independent noncalendar physical tracking benchmark

不是修改或重启Generic-SHORT。

以下全部保持read-only：

dynamic_roster_testbed.py

dynamic_roster_clean_process_testbed.py

dynamic_roster_supplied_executor.py

dynamic_roster_opportunity_audit.py

原G0与opportunity-audit runner/results/checkpoints

Stage C / Iteration 4 / Iteration 5 artifacts

retired R29、R31–R33和Iteration-5 C1实现。

7.4 Boundary mismatch

若实现需要以下任一变化，应返回：

IMPLEMENTATION_BOUNDARY_MISMATCH

而不是扩大scope：

改DirectPrimitiveARPolicy的概率factorization；

新增critic或actor communication module；

改PPO/GAE；

改旧Generic-SHORT代码；

使用high、skill或event policy；

将future ledger输入causal arm；

不能在一个runner内完成H/C/S/D与单一terminal branch。

8. Prohibited changes and unresolved claims
8.1 Source open后禁止

不得修改：

horizon 80；

state range {-2,-1,0,1,2}；

action mapping；

tracking、completion或utility公式；

membership counts/times；

training duration support {5,9,13}；

held-out support {5,7,9}；

shared renewal period 4；

C mask indices；

model width、parameter count或BPTT；

environment count、updates、PPO passes或optimizer；

seeds、episode IDs、bootstrap或evaluation cells；

absolute floors或paired margins；

checkpoint选择；

train/held-out profile。

不得通过以下方式制造D失败或救援失败：

延长interval直到超过RNN memory；

缩小hidden；

截短BPTT；

在membership边界重置survivor hidden；

移除D当前target/error；

给C/D不同communication、control frequency或optimizer exposure；

增加seed、budget或best checkpoint。

不得加入：

F0/F1 training；

skill label、高层token、KEEP/SET actor；

supplied executor；

intrinsic reward或task shaping；

posterior、MI或effect objective；

graph、field、slot、attention、communication extension；

team latent；

learned hazard、termination或duration catalogue；

identity、role、progress、success或external reward input；

new critic或module stack。

有效negative不能通过改名或调参重开；这是项目的durable result-semantics要求。

8.2 即使PASS也不能推断

PASS不建立：

R优于D；

event abstraction有任务价值；

learned skills或skill semantics；

heterogeneous learned-skill lifetime；

applied-prefix P；

factorized executor B；

cooperation或team composition；

hierarchy superiority；

arbitrary-N scaling；

strict decentralized execution；

UAV transfer或integration资格。

该G0的per-member process在team reward中聚合，但没有需要later-on-earlier assignment的联合资源冲突。因此它只资格化dynamic membership、online adaptation和individual-lifetime pressure，不是合作性hierarchy benchmark。

H和S均为noncausal ceilings。D还使用active-set aggregate与primitive-prefix communication；任何后来完整算法比较仍须匹配这些信息和通信权限。

8.3 保持的组合权重与未选想法

在结果产生前，既有权重不变：

K  benchmark calendar-identifiability limitation   high
D  information-matched direct recurrence           high
R  persistent event abstraction                    medium
B  learned-executor bottleneck                      low, conditional
P  applied-prefix value                            parked

本轮不重新排序它们。

有价值但未选择的想法继续park：

Existing-checkpoint calendar reanalysis：只能进一步描述已停止的Generic-SHORT checkpoint，不能资格化新benchmark。

Information-matched D-vs-R matrix：只有本G0 PASS后才有识别力。

Actor-information-matched causal planner：需要先给出非启发式sufficient-information state；否则会退化为oracle tuning。

Factorized learned executor B：只有R先相对D显示held-out external value后才可测试。

Applied-prefix P：只有未来任务天然具有不可由pre-positioning解决的multi-owner same-frontier反协调时才重开。

Continuous marks：只有离散persistent abstraction已证明load-bearing而连续nonvertex control提供额外价值时才值得进入。

Learned hazard：继续关闭；它改变authority并要求完整survival/intensity/censoring概率。

精确Generic-SHORT supplied-executor F1线仍永久停止；本合同不修改其原INVALID G0或有效pre-positioning reduction。