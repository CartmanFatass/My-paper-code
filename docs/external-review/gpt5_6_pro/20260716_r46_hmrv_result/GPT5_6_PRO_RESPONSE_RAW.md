裁决
CONFIRM VALID_FAIL_R46_HMRV_SUBSTRATE
	​

CONFIRM NO-RESCUE RETIREMENT OF THE EXACT R46 LINE
	​


同时必须收窄其科学表述：

R46 证明的是 learned Q/DR sign transport 失败，不是 HMRV 转移动力学本身不存在异质 renewal value。
	​


唯一下一条路线为：

R47-NSOPM-G0： Natural-Support Orthogonal Process Modes
	​


即停止继续修改 timing-only external-return credit，回到更上游的固定 N 因果边：

自然 task-blind 过程支持→稳定持续的过程模态→skill-conditioned causal mode occupancy
	​


本轮不训练 renewal actor，不注入 intrinsic reward，不进入 S7、open roster 或 variable-N。

一、R46 validity audit
1. Transition、reward 与三段 outcome 正确

实现严格使用：

u
i,τ
	​

={
h
i,τ
	​

/4,
0,
	​

b
i,τ
	​

=KEEP,
b
i,τ
	​

=RENEW,
	​

h
i,τ+1
	​

={
max(0,h
i,τ
	​

−d
i
	​

),
4,
	​

KEEP,
RENEW,
	​

r
τ
env
	​

=min(1,u
0,τ
	​

+u
1,τ
	​

).

每个 block reward 被重复到五个 primitive steps，三段 outcome 使用连续十五步折扣：

G
τ
(3)
	​

=
r=0
∑
14
	​

0.99
r
r
τk
0
	​

+r
env
	​

,k
0
	​

=5,

没有在 block 边界重新开始折扣。

Analyzer 从保存的 action、health 和 degradation 独立重建 service、post-health、reward 与三段 outcome；任一不一致都会进入 M0 invalid reasons。

2. Context 与 autoregressive prefix 正确

六维 context 精确为：

c
i
	​

=[h
i
	​

/4,h
−i
	​

/4,d
i
	​

/2,d
−i
	​

/2,prefix_valid,b
<i
	​

].

Agent 0 使用 [0,0] sentinel；agent 1 使用 [1, actual_b0]。代码在生成 agent 1 行以前读取 agent 0 的实际 action，没有把未执行的预测动作写入 prefix。

Analyzer 又从原始 action tensor 重建全部六个字段，并要求逐元素完全一致。

3. 行为概率与 overlap 正确

行为策略是固定、独立的：

μ(b
0
	​

,b
1
	​

)=Bernoulli(0.5)Bernoulli(0.5).

保存的 propensity 严格等于 0.5，action replay mismatch 为 0。四个 agent/action group 的 ESS 为 4708–4892，最大 persistent-environment weight share 为 0.0656–0.0679，均通过预注册 M1。

因此 R45 的 positivity failure 在 R46 中确实被消除。

4. Critic、fold 与 RNG 合同正确

每个 fold 的 true-Q 和 action-blind sham：

使用相同 6 -> 32 GELU -> 2 架构；

从同一个 base model 深拷贝；

使用相同 normalization；

使用相同十五个 shuffle schedules；

使用相同 Adam 参数；

各执行 570 optimizer steps。

Fold A/B 的 model seeds、shuffle seeds 和环境分区均与 launch-exact clarification 一致。

True-Q 只通过实际 action 对应的 head预测 outcome；sham 只能输出：

y
^
	​

sham
	​

=0.5q
K
	​

(c)+0.5q
R
	​

(c),

不能读取实际 action。

5. Bootstrap 与 M3 正确

科学 interval 的 cluster 是独立 episode：

cluster_id=env_rank×100+episode_index.

同一 episode 内六个 usable checks 和两个 focal rows被共同重采样。

Pooled discordance 与两个有序角色 strata：

(d0,d1) = (1,2)
(d0,d1) = (2,1)

均使用同一 episode-cluster bootstrap；两个 strata 各自要求 lower bound >0.10。

6. Branch 正确

正式结果为：

M0=PASS,M1=PASS,M2=PASS,M3=FAIL.

True/sham weighted MSE 为：

10.6079/10.9186,

ratio-gain 区间为：

[0.02669,0.03189],

top-minus-bottom DR 区间为：

[2.5504,3.0374].

但 agent 0 的 top-quartile DR interval 仍完全为负；pooled 和两个 role-stratum predicted-sign discordance 都精确为零。

Analyzer 的分支实现为：

M0 fail                  -> INVALID_R46_HMRV_WIRING
M0-M3 all pass           -> PASS_R46_HMRV_IDENTIFIABILITY
M0 valid, any M1-M3 fail -> VALID_FAIL_R46_HMRV_SUBSTRATE

与预注册合同一致。

未发现能够改变科学分支的 M0 defect。

二、必须修改的因果表述

正式 branch 有效，但当前 disposition 中这句话过强：

“exact heterogeneous-maintenance dynamics did not produce sign heterogeneity.”

M3 实际检验的是：

sign[
Q
^
	​

i
	​

(c,RENEW)−
Q
^
	​

i
	​

(c,KEEP)],

即学习得到的 critic contrast，而不是已知有限状态动力学的 exact contrast。

基于注册代码的转移、奖励、Bernoulli-0.5 后续策略和三段 outcome，我对有限状态过程进行了直接枚举。结果是：

P
oracle
	​

[signΔ
0
	​


=signΔ
1
	​

]=0.5675

在两个有序角色分层中分别约为：

0.544,0.591.

一个实际出现在注册自然 schedule 中的例子是：

h=(0,2),d=(1,2),b
0
	​

=RENEW,

其 exact contrasts 为：

Δ
0
	​

≈+2.336,Δ
1
	​

≈−0.939.

这些数值是对仓库中已注册有限状态公式的直接枚举，不是新实验。转移、reward 和三段折扣定义见实现。

因此可复用结论必须写成：

	​

均衡自然支持存在;
actual action 对 outcome prediction 有增量信息;
但注册的 6→32 true-Q/DR pipeline
没有把这种信息恢复为正确、稳定的 sign heterogeneity。
	​

	​


而不能写成：

HMRV transition kernel 本身没有异质 timing demand.

这不改变正式 branch，因为 M3 从一开始就由 learned 
Δ
^
 定义；但它严格限制了结果能够支持的科学 claim。

三、四个对象必须分开
对象	R46 能支持的结论
Balanced natural support	已建立；propensity、ESS 和 cluster concentration 全部健康
Action-conditioned predictability	已建立，但增益较小；true-Q 相对 sham 的误差优势约 2.9%
Persistent sign heterogeneity transport	失败；learned 
Δ
^
 没有恢复同时正负 signs
Actor learnability	完全未测试；R46 没有 policy module，policy optimizer steps 为 0

R46 还没有测试：

renewal actor 能否利用一个正确 contrast；

skill semantics 与 renewal timing 能否共同适应；

task-blind intrinsic loop；

sparse exploration；

S7 transfer；

open roster；

variable team number。

R46 明确不存在 policy、low、skill 或 intrinsic module，所有相应 optimizer exposure 都为零。

四、退休边界
确认永久关闭

按预注册分支，以下完整实验线永久关闭：

	​

exact HMRV transition/reward
+三 block external-return estimand
+六维 context
+6→32 true-Q/action-blind sham
+当前 M2/M3 read
	​

	​


不得通过以下方式重开：

改 degradation rate；

改 maintenance cost；

改 reward saturation；

改 horizon 或 k
0
	​

；

增加数据或 seed；

扩大 critic；

更换 optimizer；

propensity clipping；

修改 M2/M3 threshold；

在该 substrate 上训练 renewal actor。

这是对精确实验线的 no-rescue retirement，而不是对所有异步 lifetime 的否定。

五、唯一下一条因果边：R47-NSOPM-G0
选择理由

R42–R46 一直在问：

“外部任务价值能否教会 KEEP/RENEW？”

但当前项目更上游、仍未闭合的问题是：

z
i
	​

→自然、持续、可区分的行为过程
	​


项目原则本来就规定，async temporal comparison 只有在 skill mechanism 已经工作后才有解释力；reward-off observational 与 causal gate 必须先于 reward-on 和 async ablation。

因此 timing-only substrate search 到 R46 为止。唯一下一步回到：

skill semantic formation
	​


而不是继续制造第三个 maintenance environment 或第五个 renewal critic。

六、R47-NSOPM 的精确对象
1. Task-blind process view

复用现有固定 N=2 movement/process microscope，只读取：

v
i,t
int
	​

=
	​

Δp
i,t
	​

Δμ
i,t
rel
	​

ΔvechΣ
i,t
rel
	​

	​

	​

∈R
7
.

禁止输入：

primitive action
external reward
task identity/object/goal
distance/contact/progress/phase/success
agent ID
skill age or duration
critic-only state
communication-specific fields

低层不变量继续保持：

a
i,t
	​

∼π
l
	​

(a
i
	​

∣o
i,t
	​

,z
i
	​

).

项目本身也要求 compact/team context 不得绕过 skill bottleneck进入低层 actor。

2. 自然过程模态

固定：

K=4,W=k
0
	​

=10,Λ={1,5}.

对窗口内标准化且初始中心化的 u
t
	​

，使用无参数特征：

χ(u)=[u,vech(uu
⊤
)]∈R
35
.

仅用 natural on-policy windows 估计 lagged covariance 和 whitened operator，取四个主过程模态：

m
q,t
	​

=f
q
	​

(u
t
	​

).

模态按冻结 natural anchor bank 的特征值顺序编号；禁止根据 forced-z 结果事后重新命名技能。

3. Persistent occupancy score
E
q
	​

(w)=
W
1
	​

t
∑
	​

m
q,t
2
	​

,
C
q
	​

(w)=
2
1
	​

[corr
1
	​

(m
q
	​

)+corr
5
	​

(m
q
	​

)],
X
q
	​

(w)=
∑
r
	​

E
r
	​

(w)+ϵ
E
q
	​

(w)
	​

.

候选的 skill-indexed score 为：

S(w,z)=C
z
	​

(w)X
z
	​

(w)−
K
1
	​

q
∑
	​

C
q
	​

(w)X
q
	​

(w)
	​


本轮只计算，不进入 reward，不更新 actor。

它不同于退休路线：

不预测旧 z；

不使用 action likelihood；

不从 forced branches 训练 scorer；

不直接最大化 intervention effect；

不聚类并生成 hindsight labels；

不拟合 roster score；

不读取外部 reward。

七、最小 abandonment gate
固定合同
experiment                 R47-NSOPM-G0
execution                  local CUDA
seed                       47041
bootstrap seed             62047
agents                     2
skills                     4
global check / window      k0=W=10
causal horizon             H=40
natural reset groups       64
natural windows/group      8 (4 per agent)
natural windows total      512
fit groups                 0..31
held-out groups            32..63
temporal nulls             256 within-window time permutations
causal contexts            64
branches/context           4 skills x 2 stochastic replicas
causal branch steps        20,480
policy/high/critic updates 0
intrinsic reward           0
external reward read       0

Forced branches只用于 causal audit；不得进入 normalization、mode fitting、anchor alignment 或 nuisance fitting。

M0：实现有效性

必须同时满足：

process view严格为注册的 7 维字段；

mode fitting 看不到 z、action、reward、agent ID、age和任务字段；

natural fit/held-out 按 reset group完全分离；

forced data不进入自然 mode basis；

四模态 covariance、whitening、eigenvectors和 scores全部有限；

同一冻结 basis 对所有 skill branches评分；

incomplete window和 OOD window不得进入统计；

所有 policy、critic、high和 intrinsic optimizer steps严格为 0。

失败：

INVALID_R47_NSOPM_WIRING

只修具体 wiring defect并原合同重跑。

M1：自然过程模态存在

必须全部满足：

四个非平凡 eigenvalues 均超过 256 个 temporal null 的第 95 百分位；

两个独立 fit halves在 held-out anchor上的 Hungarian 对齐后：

q
min
	​

∣corr(f
q
A
	​

,f
q
B
	​

)∣≥0.70;

lag 1 和 lag 5 的 real-minus-null coherence，其 reset-cluster bootstrap 95% lower bound 均 >0；

仅用 initial context、agent、age和 action variance 的 audit-only nuisance regression满足：

R
nuisance
2
	​

<0.10.

M1 failure意味着 natural support中没有稳定、shortcut-resistant的四维过程 basis。

M2：技能能持续占据不同模态

在每个 matched natural context 对每个 z 执行两个随机 replica。

定义：

g
q
H
	​

=C
q
H
	​

X
q
H
	​

,
D
H,z
	​

=E
	​

g
z
H
	​

−
K−1
1
	​

q

=z
∑
	​

g
q
H
	​

	​

.

技能间/同技能随机性比：

ρ
H
	​

=
within-skill replica distance+ϵ
between-skill squared distance
	​

.

必须全部满足：

H10 与 H40-late 的 natural-support-valid branch比例均 ≥0.80；

bootstrap lower bounds：

D
10
	​

>0,D
40,late
	​

>0;

四个 skill 的 D
40,z
	​

 点估计全部 >0；

bootstrap lower bounds：

ρ
10
	​

>1,ρ
40,late
	​

>1;

persistence ratio：

D
10
	​

+ϵ
D
40,late
	​

	​

≥0.50.
分支
PASS_R47_NSOPM_IDENTIFIABILITY

要求：

M0∧M1∧M2.

允许的唯一下一步：

probe_only
versus
real_reward

两臂计算并更新完全相同的自然 mode basis；唯一差异是 detached endpoint S(w,z) 是否进入 low GAE。高层 return继续 external-only。

VALID_FAIL_R47_NSOPM

M0有效但 M1 或 M2 任一失败。

永久退休：

该 7 维 view；

二阶 feature map；

lag {1,5}；

四模态 score；

相应 reward-on pair。

禁止通过改 window、lag、mode count、neural encoder、kernel、seed、数据量或 threshold救援。

八、继续关闭的路线

继续永久关闭：

R42 incumbent-logit residual；

R43 full-stack true-renewal continuation；

R44 frozen-source next-check renewal credit；

R45 Alice–Bob natural-support SDRA；

R46 exact HMRV dynamics/estimand/gate；

action-density/action-information reward；

old-z classifier与 q
d
	​

/q
D
	​

 revival；

direct IFEPG；

roster complementarity fitting；

hindsight clustering/distillation；

task-specific novelty、distance、contact、progress或potential shaping；

duration-category action；

immediate S7 promotion；

open-roster implementation；

variable-N implementation。

当前工作边界也明确要求，固定-N temporal/semantic gate闭合前不得进入 open-roster 或 variable-team 实现。

最强反对意见

最强反对意见是：

spectral process modes 可能只是运动学主方向，而不是有任务价值的 skill semantics。
	​


这是正确的。即便 R47 PASS，也只能证明：

自然支持中存在稳定模态+数值 skill 能因果、持续地占据不同模态.

它不能证明：

模态有合作价值；

sparse exploration 改善；

S7 usefulness；

variable lifetime 优于 fixed lifetime。

这不改变路线，因为 R47正是 promotion ladder中的 reward-off 上游 gate。任务价值必须由后续 mechanism-matched reward pair和最终 external-task advantage检验，而不能被写进当前 intrinsic 定义。

最终单一决定
	​

R46 = VALID_FAIL;
未发现 branch-changing M0 defect;
exact R46 line 按合同永久关闭，不救援;
但科学表述收窄为 learned sign-transport failure，
不能宣称转移动力学本身无异质 value;
timing-only substrate search 到此停止;
唯一下一边 = R47-NSOPM-G0;
先证明 task-blind persistent skill-process semantics，
再允许任何 intrinsic reward 或 async efficacy 实验。
	​

	​

