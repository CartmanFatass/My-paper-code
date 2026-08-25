裁决
ACCEPT_R47_NSOPM_G0_LAUNCH_EXACT
	​


R46 的有效分支保持为：

VALID_FAIL_R46_HMRV_SUBSTRATE.

其可复用结论仍然是：均衡自然支持和 action-conditioned outcome information 可以同时存在，但注册的 learned Q/DR 路径未必能把这些信息恢复为稳定的、跨 agent/context 改变符号的时序价值。 R46 退休的是精确的 HMRV dynamics、三 block estimand、六维 context、6→32 Q/sham estimator 和 M2/M3 read 的组合，而不是一般异步 lifetime。唯一后继仍是 R47-NSOPM-G0。

R47 的唯一因果边固定为：

自然 task-blind 过程支持→稳定、持续、正交的过程模态→数值技能对不同模态的持续因果占据
	​


本轮无 actor、high policy、critic 或 intrinsic optimizer update；不读取外部 reward；不进入 S7、open roster 或 variable-N。这与当前仓库的计划边界一致。

1. Source policy 与自然数据日程
1.1 唯一 source checkpoint

使用 R31–R33 共同采用的冻结 R30 checkpoint：

logs/r30_alice_bob_paired_64k_20260714_163908/
runs/adaptive_keep_set/seed30031/
standalone_process_core_final.pt

启动时必须验证：

checkpoint_total_steps = 64000
checkpoint_update      = 50
scenario               = alice_bob_asymmetric_cycles
high_controller        = r30_fixed_clock_ar_edit
n_agents               = 2
n_skills               = 4
skill_interval         = 10
episode_length         = 80
obs_dim                 = 12
state_dim               = 19
action_dim              = 2 continuous

R31 的权威结果 JSON 明确登记了该 checkpoint、步数、环境和 R30 controller。

配置基类为：

ha_ctse_process.config_alice_bob_asymmetric.Config

保留其：

四技能 codebook；

alice_bob_asymmetric_cycles；

strict recurrent HMASD-style low actor；

64 维 low recurrent state；

continuous 2D action；

task shaping、semantic reward 和 R31 reward 全部关闭。

checkpoint 使用 strict R30 resume 语义加载，load_optimizers=False。compact、bridge、high actor/value、low actor/critic 和 ValueNorm 都从 checkpoint 恢复；任何 required key 缺失或架构不匹配均为 M0 invalid。

所有模块随后：

eval()
requires_grad_(False)

自然 rollout 仍然使用 stochastic policy：

high R30 KEEP/SET sampling: stochastic
low continuous action:     stochastic tanh-Gaussian

低层 actor 继续只读取：

(o
i,t
	​

,z
i,t
	​

),

team code 不进入 primitive actor。仓库默认 strict low architecture 和该瓶颈分别由配置及算法原则固定。

1.2 64 个自然 reset groups

对：

g=0,…,63

分别执行一个完整 80-step episode。

固定种子规则：

reset_seed(g)  = 47041 + g
policy_seed(g) = 47041 + g

每组开始前同时设置：

random
numpy
torch CPU
torch CUDA
environment reset seed

然后：

agent.reset_env_state(0)；

环境 reset(seed=47041+g)；

在 t=0,10,…,70 正常执行冻结 R30 high check；

每个 primitive step 调用 stochastic low actor；

recurrent actor/critic hidden 在整个 episode 内连续传播；

只在 episode reset 时归零，不因 high check 或 skill SET 归零。

仓库的 low actor执行路径会读取当前 hidden，产生并写回新的 actor/critic hidden；环境 reset 才重置这些状态。

实际环境 reward 的返回槽位必须被丢弃。为了让现有 R30 clock/buffer 正常推进，只向 record_environment_step 传入字面常数 0.0。该值不作为训练或统计目标；formal evidence schema 中不得出现环境 reward 数组。

因此：

external_reward_reads=0
	​


但环境内部因接触、收集和 task clocks 引起的真实状态转移仍正常发生。

1.3 每组八个自然窗口

每个 source episode 有八个完整 check blocks。每组只选四个 check indices，并为两个 focal agents 各创建一个窗口：

g 为偶数: check indices {0,2,4,6}
g 为奇数: check indices {1,3,5,7}

因此每组：

4 checks×2 agents=8 windows.

每个窗口从自然 high check 已经执行完、但第一个 low action 尚未执行的状态开始，包含：

11 position frames→10 transition views.

总数为：

64×8=512.

该 parity schedule使每个 check index在 fit 和 held-out halves 中均衡出现。

固定分割：

spectral fit groups       0..31
  fit half A              0..15
  fit half B             16..31

held-out anchor groups   32..63
  nuisance train         32..47
  nuisance evaluation    48..63

任何 window 跨 episode terminal、reset 或缺少第 11 个 position frame时，都不能进入统计；在当前固定 80-step 环境中，正式 run 若未得到恰好 512 个完整窗口，则判 M0 invalid。现有 R31 window contract同样只接受真实 check 后的完整 W-transition window，并在 terminal/update boundary 前未完成时 fail closed。

2. 精确七维 task-blind process view

令：

p
ˉ
	​

i,t
	​

=
world_size
p
i,t
	​

	​

=
8
p
i,t
	​

	​

.

环境已经提供只含 normalized positions 的 intrinsic_effect_view()；active target、button、contact、clock、collection state 和 reward-derived fields 均不暴露。

对 focal agent i，定义 teammate-relative vectors：

r
ij,t
	​

=
p
ˉ
	​

j,t
	​

−
p
ˉ
	​

i,t
	​

,j

=i.

相对均值：

μ
i,t
rel
	​

=
N−1
1
	​

j

=i
∑
	​

r
ij,t
	​

.

相对 covariance 使用 population normalization：

Σ
i,t
rel
	​

=
N−1
1
	​

j

=i
∑
	​

(r
ij,t
	​

−μ
i,t
rel
	​

)(r
ij,t
	​

−μ
i,t
rel
	​

)
⊤
.

不使用 unbiased 1/(N−2) normalization。

当前：

N=2,

所以 teammate-relative point set恰好为 singleton：

{r
i,1−i,t
	​

}.

因此：

μ
i,t
rel
	​

=r
i,1−i,t
	​

,Σ
i,t
rel
	​

=0
2×2
	​

.

七维 transition view 的顺序固定为：

v
i,t
int
	​

=
	​

Δ
p
ˉ
	​

i,x
	​

Δ
p
ˉ
	​

i,y
	​

Δμ
i,x
rel
	​

Δμ
i,y
rel
	​

ΔΣ
i,xx
rel
	​

ΔΣ
i,xy
rel
	​

ΔΣ
i,yy
rel
	​

	​

	​

	​


其中：

Δ
p
ˉ
	​

i,t
	​

=
p
ˉ
	​

i,t+1
	​

−
p
ˉ
	​

i,t
	​

,
Δμ
i,t
rel
	​

=μ
i,t+1
rel
	​

−μ
i,t
rel
	​

,
ΔΣ
i,t
rel
	​

=Σ
i,t+1
rel
	​

−Σ
i,t
rel
	​

.

vech ordering固定为：

[xx, xy, yy]

所以在当前 N=2 gate 中，最后三个字段应数值为零。它们保留在 tensor 中，是为了保持未来跨 team-size 的字段语义；不能用其他点、虚拟 agent 或环境对象填充 covariance。

M0 要求：

view shape                    [512,10,7]
max_abs(view[...,4:7])       <= 1e-7

该 view 不读取：

primitive action
skill label
skill age
agent ID
external reward
task object/identity
button/target/contact
task phase/clock
success predicate
critic-only state
3. 四模态 spectral estimator
3.1 Train-only 标准化与初始中心化

在 primary fit groups 0..31 的全部 transition rows上计算 population mean/std：

μ
v
	​

=E
fit
	​

[v],
s
j
	​

=
E
fit
	​

[(v
j
	​

−μ
v,j
	​

)
2
]
	​

.

若：

s
j
	​

<10
−6
,

则固定：

s
j
	​

=1.

不删除该字段。

对每个 window：

v
~
t
	​

=(v
t
	​

−μ
v
	​

)⊘s,
u
t
	​

=
v
~
t
	​

−
v
~
0
	​

,t=0,…,9.

因此 u
0
	​

=0。

Fit half A、fit half B和 primary fit各自只用自己的 training groups拟合 (μ
v
	​

,s)。held-out anchor只做评分和 alignment。

3.2 35 维固定 feature map

固定：

χ(u)=[u
0
	​

,…,u
6
	​

,{u
a
	​

u
b
	​

}
0≤a≤b≤6
	​

]∈R
35
.

Quadratic ordering为：

u0*u0, u0*u1, ..., u0*u6,
u1*u1, u1*u2, ..., u1*u6,
...
u6*u6

不使用
2
	​

 off-diagonal scaling。

3.3 Lagged pair estimators

对：

Λ={1,5},

定义：

P
ℓ
	​

={(χ
w,t
	​

,χ
w,t+ℓ
	​

):t=0,…,9−ℓ}.

将两个 lag 的 source sides合并计算：

x
ˉ
=
M
1
	​

+M
5
	​

1
	​

ℓ∈{1,5}
∑
	​

(x,y)∈P
ℓ
	​

∑
	​

x,

target sides同理得到
y
ˉ
	​

。

Population covariances为：

C
00
	​

=
M
1
	​

+M
5
	​

1
	​

ℓ
∑
	​

(x,y)∈P
ℓ
	​

∑
	​

(x−
x
ˉ
)(x−
x
ˉ
)
⊤
,
C
11
	​

=
M
1
	​

+M
5
	​

1
	​

ℓ
∑
	​

(x,y)∈P
ℓ
	​

∑
	​

(y−
y
ˉ
	​

)(y−
y
ˉ
	​

)
⊤
.

每个 lag 的 cross-covariance为：

C
01
(ℓ)
	​

=
M
ℓ
	​

1
	​

(x,y)∈P
ℓ
	​

∑
	​

(x−
x
ˉ
)(y−
y
ˉ
	​

)
⊤
.

不跨 window 构造 temporal pair。

3.4 Whitening、rank floor 与 operator

对 C
00
	​

 和 C
11
	​

 分别做对称 eigendecomposition。

保留 eigenvalues：

λ>τ
C
	​

,

其中：

τ
C
	​

=max(10
−8
,10
−6
λ
max
	​

).

Whitening ridge固定为：

ϵ
C
	​

=10
−4
.

例如：

W
0
	​

=U
0,+
	​

diag[(λ
0,+
	​

+10
−4
)
−1/2
]U
0,+
⊤
	​

,

W
1
	​

 同理。

定义非对称 lag operators：

T
ℓ
	​

=W
0
	​

C
01
(ℓ)
	​

W
1
	​

.

不对 T
ℓ
	​

 做

(T
ℓ
	​

+T
ℓ
⊤
	​

)/2

之类的 reversible symmetrization。

使用 left-singular Gram：

G=
2
1
	​

(T
1
	​

T
1
⊤
	​

+T
5
	​

T
5
⊤
	​

)
	​


所以 G 本身天然为 symmetric positive semidefinite。

对 G eigendecompose：

Gq
q
	​

=ν
q
	​

q
q
	​

,ν
0
	​

≥ν
1
	​

≥⋯.

Nontrivial eigenvalue floor固定为：

τ
G
	​

=max(10
−10
,10
−6
ν
0
	​

).

少于四个 ν
q
	​

>τ
G
	​

 是有效的 M1 scientific FAIL，不是 wiring invalid。

3.5 Mode ordering 与 sign

Primary basis由 groups 0..31 拟合。

Mode IDs固定为 primary G 的 descending eigenvalue rank：

mode 0 = largest eigenvalue
mode 1 = second
mode 2 = third
mode 3 = fourth

若 eigenvalue完全相等，保留 eigensolver返回的原始 index作为稳定 tie-break。

每个 eigenvector的 sign规则：

找到 ∣q
q,j
	​

∣ 最大的最小 feature index j；

若 q
q,j
	​

<0，将整个 q
q
	​

 乘以 −1。

最终 mode activation为：

m
q,t
	​

=q
q
⊤
	​

W
0
	​

(χ(u
t
	​

)−
x
ˉ
)
	​


不允许用 natural skill label或 forced-z outcome重新排列、重命名或翻转 primary modes。

4. Temporal null、稳定性与 nuisance audit
4.1 256 个 temporal nulls

固定：

temporal_null_seed = 57041
null_replicates    = 256

先按真实数据计算每个 window 的 u
0:9
	​

。对每个 null replicate和每个 window：

独立采样一个长度 10 的 uniform random permutation；

identity permutation 被拒绝并重采样；

同一个 permutation应用于全部七个 coordinates；

只在 window 内重排，不交换 window、agent或reset group；

不重新计算 initial centering。

这样每个 window 的 u 和 χ(u) multiset完全不变，只有 temporal order 被破坏。

每个 null replicate在 permuted fit bank上重新估计：

C00, C11, C01(1), C01(5), whitening, G, eigenvalues

Rank-q eigenvalue threshold为：

ν
q
null95
	​

=Q
0.95
	​

{ν
q
null,r
	​

}
r=1
256
	​

.

M1 要求：

ν
q
	​

>τ
G
	​

∧ν
q
	​

>ν
q
null95
	​

,q=0,…,3.

这是本合同中使用 temporal-null 95th percentile 的唯一位置。

4.2 Held-out temporal coherence

对一个 window 和 mode q，固定：

c
q,ℓ
	​

(w)=
∑
t=0
9−ℓ
	​

m
q,t
2
	​

∑
t=0
9−ℓ
	​

m
q,t+ℓ
2
	​

	​

+10
−8
∑
t=0
9−ℓ
	​

m
q,t
	​

m
q,t+ℓ
	​

	​

.

不做额外的 window-local mean subtraction。

Lag-level window statistic：

c
ℓ
	​

(w)=
4
1
	​

q=0
∑
3
	​

c
q,ℓ
	​

(w).

对 held-out window，使用同一 frozen primary basis，并对其 mode sequence执行上述 256 个 temporal permutations。Null comparator是：

c
ˉ
ℓ
null
	​

(w)=
256
1
	​

r
∑
	​

c
ℓ
null,r
	​

(w),

不是 null 95th percentile。

对每个 held-out reset group先平均其八个 windows，再按 reset group做 10,000 次 bootstrap。M1 要求：

LCB
95
	​

E[c
1
	​

−
c
ˉ
1
null
	​

]>0,
LCB
95
	​

E[c
5
	​

−
c
ˉ
5
null
	​

]>0.
4.3 Fit-half stability 与 frozen anchor

分别在：

half A = groups 0..15
half B = groups 16..31

拟合两个独立 basis。

在 held-out groups 32..63 上，分别计算：

primary activations
half-A activations
half-B activations

并按固定 window/time flatten order形成 Pearson correlation matrices。

对 A→primary 与 B→primary 分别执行 exhaustive 4! one-to-one assignment，目标为最大化 absolute-correlation sum；相同分数时选择 lexicographically smallest permutation。随后使 matched correlation相对 primary为正。

稳定性统计为：

s
q
	​

=corr(m
q
A, aligned
	​

,m
q
B, aligned
	​

).

M1 要求：

q
min
	​

s
q
	​

≥0.70.

Primary mode IDs仍由 primary eigenvalue rank决定；alignment只重排两个 half bases。

4.4 Audit-only nuisance regression

Mode fitting及 alignment永远看不到 nuisance fields。Nuisance audit只在 held-out natural windows上执行。

每个 window的 target是：

y
w
	​

=[g
0
	​

(w),g
1
	​

(w),g
2
	​

(w),g
3
	​

(w)],

其中：

E
q
	​

(w)=
10
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

(w)+10
−8
E
q
	​

(w)
	​

,
C
q
	​

(w)=
2
1
	​

[c
q,1
	​

(w)+c
q,5
	​

(w)],
g
q
	​

(w)=C
q
	​

(w)X
q
	​

(w).

Nuisance feature固定为十维：

x
w
nuis
	​

=
	​

p
ˉ
	​

i,x
start
	​

p
ˉ
	​

i,y
start
	​

p
ˉ
	​

−i,x
start
	​

p
ˉ
	​

−i,y
start
	​

1[i=1]
min(age
i
start
	​

,80)/80
Var(a
i,x
	​

)
Var(a
i,y
	​

)
Var(a
−i,x
	​

)
Var(a
−i,y
	​

)
	​

	​

.

Action variances使用该 natural window中十个真实执行动作、population normalization ddof=0。不输入 action means、action sequence或 skill labels。

固定 nuisance split：

train groups 32..47
test groups  48..63

模型为 analytic multi-output ridge：

feature standardization: nuisance-train only
intercept:                yes, unregularized
ridge lambda:             1e-3

报告四个 per-mode test R
q
2
	​

 和一个 pooled multivariate R
2
。若某一 target的 test SST为零，则该 target R
2
=0。

Gate statistic为：

R
max
2
	​

=max(R
pooled
2
	​

,R
0
2
	​

,…,R
3
2
	​

).

M1 要求：

R
max
2
	​

<0.10
	​

.
5. Forced-skill causal branches
5.1 64 个 matched natural contexts

每个自然 reset group贡献一个 context。

对 group g：

focal(g)=gmod2,
check(g)=⌊
2
g
	​

⌋mod4.

所以 context来自：

check index 0,1,2,3
primitive time 0,10,20,30

每个 check/focal组合恰好出现八次。所有 branch最多运行至 primitive time 70，因此不会碰到 episode-80 truncation。

Snapshot时点固定为：

natural R30 high check及 working-roster commit已经完成，但该 block第一个 low action尚未执行。

Snapshot必须包含：

complete environment probe snapshot, including RNG
current observation and centralized state
active skill roster
active mask
skill ages
team code
steps_to_check
episode step/id
low actor recurrent hidden
low critic recurrent hidden
Python/NumPy/Torch/CUDA RNG state

环境现有 probe API能够完整保存和恢复位置、task state、counters及 environment RNG。task fields只用于恢复同一模拟器状态，不能进入 view、mode或score。

5.2 Intervention boundary

对每个 context、每个：

z∈{0,1,2,3},

和两个 replicas执行 40 步 branch。

每个 branch恢复完全相同的 snapshot，然后：

只把 focal agent 的 actor-visible active_skill改为 z；

不伪造一个 high SET action；

不改变 focal age；

teammate skill、age、team code和 active mask保持 snapshot值；

focal 与 teammate skill均在 40 步内保持不变；

不调用 high controller；

不打开或更新 high buffer；

low actor/critic recurrent states从 snapshot连续传播；

teammate继续由 frozen stochastic low policy响应观察，不使用 action tape；

environment reward返回值被丢弃；

branch不能训练或更新任何参数。

这与既有 R31–R33 的 causal-audit边界一致：forced windows只用于审计，不用于 posterior/scorer训练；R31正式结果也记录了 forced_windows_used_for_posterior_training=0。

5.3 Replica 与 common random numbers

固定：

seed
branch
	​

(c,r)=67041+2c+r,

其中：

c = context index 0..63
r = replica index 0 or 1

在同一个 (c,r) 内，四个 skills使用完全相同的：

Python RNG
NumPy RNG
Torch CPU RNG
Torch CUDA RNG
environment snapshot/RNG

因此四个 skill branches使用 common random numbers。

Replica 0 与 replica 1 使用不同 seed，因而是独立 policy-noise replicas。

每个 skill branch保持相同的 stochastic sampling-call count与两 agent batch order。

总步数：

64×4×2×40=20480.

如果任一 branch在 40 步以前 terminal、truncate或reset，则该 context的全部八个 branches标为 invalid；formal M0要求：

early_branch_reset_contexts = 0

不能跨 reset拼接 H40 trajectory。

6. Support/OOD、H10/H40 与 M2 aggregation
6.1 Natural-support distance

使用 primary fit的：

x
ˉ
,W
0
	​

.

对任何 10-transition window的每个 point定义：

d
t
2
	​

=∥W
0
	​

(χ(u
t
	​

)−
x
ˉ
)∥
2
2
	​

.

Support threshold来自 held-out natural groups 32..63 的全部 point distances：

d
95
2
	​

=Q
0.95
	​

{d
t
2
	​

}
heldout
	​

,

使用线性 quantile interpolation。

一个 branch window support-valid，当且仅当：

#{t:d
t
2
	​

≤d
95
2
	​

}≥9.

Horizon windows固定为：

H10       transitions 0..9
H40-late  transitions 30..39

每个 10-step horizon window独立执行标准化、初始中心化和 χ 构造。

对 horizon H，一个 context只有在：

4 skills × 2 replicas = 8 windows

全部 support-valid时才是 complete-support context。

注册的 “support-valid branch ratio” 定义为：

64×8
8×#{complete-support contexts}
	​

=
64
#{complete-support contexts}
	​

.

因此不会通过选择性删除某一个 skill 的 OOD branch产生偏差。

M2 要求 H10 与 H40-late 均：

support ratio≥0.80.
6.2 Score

对每个 branch/horizon：

g
c,z,r,q
H
	​

=C
c,z,r,q
H
	​

X
c,z,r,q
H
	​

.

同时计算后续候选 intrinsic：

S(w,z)=g
z
	​

(w)−
4
1
	​

q=0
∑
3
	​

g
q
	​

(w)
	​


但在 G0 中：

S is detached
S is logged only
S is never written to rollout reward
6.3 Assigned-mode contrast

先对 replicas平均：

g
ˉ
	​

c,z,q
H
	​

=
2
1
	​

r=0
∑
1
	​

g
c,z,r,q
H
	​

.

Context/skill contrast：

d
c,z
H
	​

=
g
ˉ
	​

c,z,z
H
	​

−
3
1
	​

q

=z
∑
	​

g
ˉ
	​

c,z,q
H
	​

.

Skill-specific mean：

D
H,z
	​

=E
c
	​

[d
c,z
H
	​

],

pooled mean：

D
H
	​

=
4
1
	​

z
∑
	​

D
H,z
	​

.

Mode ID z 是 frozen spectral rank；不得根据 forced结果做 permutation alignment。

M2 要求：

LCB
95
	​

(D
10
	​

)>0,
LCB
95
	​

(D
40,late
	​

)>0,

以及：

D
40,late,z
	​

>0∀z.

后者只要求四个 point estimates均正，不新增 per-skill CI门槛。

6.4 Between/within causal SNR

对 context c：

B
c
H
	​

=
K(K−1)
2
	​

z<z
′
∑
	​

	​

g
ˉ
	​

c,z
H
	​

−
g
ˉ
	​

c,z
′
H
	​

	​

2
2
	​

.
W
c
H
	​

=
K
1
	​

z
∑
	​

2
1
	​

	​

g
c,z,0
H
	​

−g
c,z,1
H
	​

	​

2
2
	​

.

聚合：

ρ
H
	​

=
E
c
	​

[W
c
H
	​

]+10
−8
E
c
	​

[B
c
H
	​

]
	​

.

M2 要求：

LCB
95
	​

(ρ
10
	​

)>1,
LCB
95
	​

(ρ
40,late
	​

)>1.

Persistence point statistic：

D
10
	​

+10
−8
D
40,late
	​

	​

≥0.50.

该 ratio使用同时满足 H10 与 H40 support的 context intersection；若 intersection为空，则 M2失败。

6.5 Bootstrap

固定：

bootstrap repetitions = 10000
bootstrap seed        = 62047

M1 coherence：以 held-out reset group为 cluster；

M2：以 causal source reset group/context为 cluster；

同一个 context的四 skills、两个 replicas和四 mode coordinates始终共同重采样；

percentile interval为 [0.025,0.975]。

7. 实现边界与最小 abandonment gate
7.1 唯一允许的实现文件

核心实现只允许新增：

scripts/r47_nsopm.py
scripts/run_r47_nsopm_gate.py
scripts/analyze_r47_nsopm.py
scripts/run_r47_nsopm_local.ps1

禁止修改：

envs/pettingzoo/alice_bob_asymmetric_cycles.py
ha_ctse_process/train.py
ha_ctse_process/standalone_agent.py
ha_ctse_process/r31_effect_information.py
normal R30 trainer/controller
environment reward
low actor
checkpoint format

环境现有 normalized-position view和 probe snapshot API已足以实现 gate，因此不需要环境代码变化。

正常研究登记只更新：

memory/ExpRecord.md
memory/CURRENT_WORK.md
memory/IMPLEMENTATION_PLAN.md

不新增 algorithm module或 trainer integration。仓库当前也将 R47 定义为 standalone gate plus analyzer/runner，不允许修改环境、normal trainer、reward或 low actor。

7.2 唯一 focused dry run

正式 launch前允许一次非科学 dry run：

natural reset groups  2
natural windows       16
causal contexts       1
forced branches       8
branch steps          320
temporal nulls        2
optimizer steps       0

它只能检查：

checkpoint strict load；

natural window count和 [10,7] shape；

last-three covariance fields为零；

spectral tensors、whitening和 branch scores有限；

snapshot restore/replay一致；

parameter drift为零；

reward字段未写入 evidence。

它不计算或判断 M1/M2 thresholds，不产生正式 result status，完成后删除 transient output。

8. 互斥结果分支
INVALID_R47_NSOPM_WIRING

触发条件：任一 M0失败，包括：

source checkpoint/config不一致；

512 natural windows或20,480 branch steps不匹配；

process view字段/顺序错误；

task/action/reward/skill字段进入 mode fit；

fit/held-out leakage；

forced data进入 normalization、basis、alignment或 nuisance fit；

basis未冻结；

snapshot/recurrent/CRN contract错误；

非有限 spectral/score；

任意 optimizer step或parameter drift；

external reward被读取或保存。

唯一动作：

只修复定位到的 wiring defect，并原合同重跑。

PASS_R47_NSOPM_IDENTIFIABILITY

要求：

M0∧M1∧M2.

只允许结论：

natural task-blind support 中存在稳定、shortcut-resistant的四个过程模态，并且四个数值技能能够在 matched natural contexts中持续、因果地占据其冻结 spectral-rank mode。

唯一后续动作：

probe_only
versus
real_reward

两臂使用相同公式、自然 basis更新、collector和 low PPO；唯一差异是 detached endpoint S(w,z) 是否进入 low GAE。High KEEP/SET return继续 external-only。

VALID_FAIL_R47_NSOPM

条件：

M0∧¬(M1∧M2).

永久退休：

exact 7-D view
within-window standardization/initial-centering
35-D second-order feature map
lags {1,5}
whitened Gram estimator
four spectral-rank mode identities
S(w,z) score
corresponding reward-on pair

禁止通过以下方式救援：

改 W；

改 lag；

改 mode count；

使用 neural encoder或 kernel；

对 modes做 skill-label/forced-outcome post-hoc alignment；

改 checkpoint、seed、数据量、null数量或门槛；

加 task字段、action likelihood或 reward；

扩大 forced contexts或 replicas。

不存在 UNDERPOWERED、参数 sweep或自动追加数据分支。

保持永久关闭

以下路线不因 R47 clarification重新开放：

R42 incumbent-logit residual；

R43 full-stack true-renewal continuation；

R44 frozen-source next-check renewal credit；

R45 Alice–Bob natural-support SDRA；

R46 exact HMRV line；

old-z classifier及 q
d
	​

/q
D
	​

 reward revival；

action-density/action-information reward；

direct IFEPG；

roster complementarity fitting；

hindsight clustering/distillation；

duration-category action；

task-specific novelty、distance、contact、phase、progress或 potential shaping；

immediate S7；

open-roster；

variable-N。

项目的实验纪律要求 skill mechanism先通过 reward-off observational/causal gate，之后才能进入 reward-on和 async temporal ablation。

可直接登记到 memory/ExpRecord.md 的 launch contract
### EXP-20260716-r47-nsopm-g0

- Status: launch-ready.
- Verdict source:
  ACCEPT_R47_NSOPM_G0_LAUNCH_EXACT.
- Causal edge:
  natural task-blind process support
  -> stable orthogonal persistent modes
  -> skill-conditioned causal mode occupancy.
- Scope:
  reward-off fixed-N=2 gate only.
  No policy/high/critic/intrinsic update.
  External reward is discarded and never stored or used.
  No S7, open-roster, or variable-N claim.

- Source:
  checkpoint =
    logs/r30_alice_bob_paired_64k_20260714_163908/
    runs/adaptive_keep_set/seed30031/
    standalone_process_core_final.pt
  checkpoint_total_steps=64000; update=50.
  config=ha_ctse_process.config_alice_bob_asymmetric.Config.
  high_controller=r30_fixed_clock_ar_edit.
  N=2; K=4; k0=10; episode=80.
  obs/state/action=12/19/continuous-2.
  strict recurrent HMASD low actor, hidden=64.
  stochastic high and stochastic tanh-Gaussian low execution.
  load_optimizers=False; all parameters frozen/eval.

- Natural schedule:
  seed=47041.
  groups=64; group g reset/policy seed=47041+g.
  one independent 80-step episode/group.
  high checks at t=0,10,...,70.
  even g uses check indices {0,2,4,6};
  odd g uses {1,3,5,7}.
  4 checks x 2 agents = 8 windows/group.
  total windows=512, each [10,7].
  fit groups=0..31; half A=0..15; half B=16..31.
  heldout groups=32..63.
  nuisance train=32..47; nuisance test=48..63.
  actual environment reward is discarded; literal 0.0 advances R30 clock.

- Seven-dimensional view:
  pbar=p/world_size, world_size=8.
  r_ij=pbar_j-pbar_i.
  mu_rel=mean_{j!=i} r_ij.
  Sigma_rel=(1/(N-1))*sum(r_ij-mu)(r_ij-mu)^T.
  v=[Delta pbar_x,Delta pbar_y,
     Delta mu_x,Delta mu_y,
     Delta Sigma_xx,Delta Sigma_xy,Delta Sigma_yy].
  For N=2 the relative set is one point and Sigma_rel is exactly zero.
  covariance vech order=[xx,xy,yy].
  No action, z, age, ID, reward, task, clock, contact or critic field enters fit.

- Standardization/features:
  population mean/std from train groups only.
  std<1e-6 -> scale=1.
  u_t=((v_t-mu)/std)-((v_0-mu)/std).
  chi=[u0..u6,{u_a*u_b for 0<=a<=b<=6}] in fixed upper-triangular order.
  chi_dim=35.

- Spectral estimator:
  lags={1,5}; within-window pairs only.
  pooled source/target means and C00/C11 over both lags.
  lag-specific C01(l).
  covariance normalization=population.
  covariance rank floor=max(1e-8,1e-6*lambda_max).
  whitening ridge=1e-4.
  T_l=W0*C01(l)*W1; T_l is not symmetrized.
  G=0.5*(T1*T1^T+T5*T5^T).
  G rank floor=max(1e-10,1e-6*nu0).
  primary modes are the four descending G eigenvectors.
  sign: largest-absolute, lowest-index component must be positive.
  mode activation m_q=q_q^T W0(chi-xbar).
  No skill/forced-result mode alignment.

- Temporal null:
  null_seed=57041; replicates=256.
  independently permute each already-centered length-10 u sequence;
  same permutation for all seven coordinates; reject identity;
  never exchange windows/groups/agents.
  Refit the complete spectral estimator for every null.
  eigenvalue q uses rank-matched null 95th percentile.
  coherence null is the mean of 256 frozen-basis permuted coherences,
  not a null percentile.

- Stability/coherence:
  align half A and B independently to the primary basis on heldout activations;
  exhaustive 4! Hungarian-equivalent assignment, maximize absolute correlation,
  lexicographically smallest tie; flip signs toward primary.
  min corr(aligned A_q,aligned B_q)>=0.70.
  c_q,l=sum m_t*m_t+l /
        (sqrt(sum m_t^2 * sum m_t+l^2)+1e-8).
  c_l=mean_q c_q,l.
  reset-group bootstrap LCB95(real-nullmean)>0 for lags 1 and 5.

- Nuisance audit:
  target g_q=C_q*X_q.
  features=[
    focal start xy, teammate start xy,
    focal-agent indicator,
    min(focal age,80)/80,
    focal action var xy,
    teammate action var xy
  ].
  No action mean/sequence or skill label.
  multi-output ridge lambda=1e-3; intercept unregularized.
  train groups=32..47; test=48..63.
  max(pooled R2, four per-mode R2)<0.10.

- Forced audit:
  64 contexts, one/reset group.
  focal=g mod 2.
  check=floor(g/2) mod 4, i.e. t in {0,10,20,30}.
  snapshot immediately after natural high commit and before first low action.
  restore full simulator, obs/state, roster/ages/mask/team code,
  low actor/critic hidden and RNG state.
  override only focal actor-visible z; do not create a SET action.
  hold focal and teammate skills for H=40; suppress high checks.
  teammate remains stochastic policy-responsive; no action tape.
  replicas=2.
  CRN seed(context c,replica r)=67041+2*c+r,
  identical across four skills; replicas are independent.
  early reset/truncation invalidates all eight branches of that context.
  expected forced steps=64*4*2*40=20480.

- Support:
  d2=||W0*(chi-xbar)||^2.
  threshold=heldout-natural pointwise 95th percentile.
  a 10-step window is valid when at least 9/10 points are in support.
  H10=steps 0..9; H40-late=steps 30..39.
  a context is H-valid only when all 4 skills x 2 replicas are valid.
  support ratio=#H-valid contexts/64; require >=0.80 for both horizons.
  OOD/incomplete windows never enter D or rho.

- Scores:
  E_q=mean_t m_q,t^2.
  X_q=E_q/(sum_r E_r+1e-8).
  C_q=0.5*(c_q,1+c_q,5).
  g_q=C_q*X_q.
  S(w,z)=g_z-(1/4)*sum_q g_q; log only, no reward.
  replica mean gbar_c,z.
  d_c,z=gbar_c,z,z-(1/3)*sum_{q!=z}gbar_c,z,q.
  D_H,z=mean_c d_c,z; D_H=(1/4)*sum_z D_H,z.
  B_c=mean_{z<z'} ||gbar_c,z-gbar_c,z'||^2.
  W_c=(1/4)*sum_z 0.5*||g_c,z,0-g_c,z,1||^2.
  rho_H=mean B_c/(mean W_c+1e-8).

- Bootstrap:
  repetitions=10000; seed=62047.
  natural M1 cluster=reset group.
  causal M2 cluster=matched source context/reset group.
  All skills, replicas and mode coordinates remain in one cluster.

- M0:
  exact checkpoint/config/counts/view schema;
  512 complete natural windows;
  64 contexts and 20480 branch steps;
  fit/heldout separation;
  finite covariance/whitening/eigenvectors/scores;
  same frozen basis across every branch;
  no forced data in fit/alignment/nuisance;
  no reward field/read;
  all optimizer steps=0 and parameter drift=0;
  no early branch reset.

- M1:
  four nontrivial real eigenvalues exceed rank-matched temporal-null q95;
  min fit-half aligned correlation>=0.70;
  lag-1 and lag-5 real-minus-null coherence bootstrap LCB95>0;
  nuisance R2 maximum<0.10.

- M2:
  H10 and H40-late complete-context support ratio>=0.80;
  LCB95(D10)>0 and LCB95(D40-late)>0;
  all four D40-late,z point estimates>0;
  LCB95(rho10)>1 and LCB95(rho40-late)>1;
  D40-late/(D10+1e-8)>=0.50.

- Branches:
  INVALID_R47_NSOPM_WIRING:
    repair only the identified implementation defect and rerun unchanged.
  PASS_R47_NSOPM_IDENTIFIABILITY:
    authorize only probe_only versus real_reward with identical basis,
    collector and auxiliary updates; detached endpoint S enters low GAE only
    in real_reward; high return remains external-only.
  VALID_FAIL_R47_NSOPM:
    permanently retire this exact view, feature map, lags, four-mode basis,
    score and reward pair. No window/lag/mode/encoder/kernel/seed/data/
    threshold or post-hoc mode-label alignment rescue.
