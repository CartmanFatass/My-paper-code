裁决
CONFIRM VALID_FAIL_R45_SDRA_IDENTIFIABILITY
	​

M2 CLARIFICATION = VALID AND PRE-REGISTERED
	​

RETIRE ALICE--BOB K=50 AS A NATURAL-SUPPORT ASYNC-TIMING SUBSTRATE
	​


唯一下一条因果路线为：

R46-HMRV-G0： Heterogeneous Maintenance Renewal-Value Gate
	​


即先建立一个具有原生异质续期需求、均衡自然动作支持、无策略训练、无 reward shaping 的固定 N=2 时间机制显微镜。R46 通过前，不允许训练新的 renewal actor，不允许 joint co-adaptation，也不进入 S7、open roster 或 variable-N。

1. Validity verdict
1.1 R45 的有效科学分支就是 VALID_FAIL

正式结果满足：

M0=PASS,M1=FAIL,M2=PASS,M3=FAIL.

运行严格完成了注册合同：

160,000 environment steps；

100 outer updates；

3,200 environment-check rows；

3,184 个普通 check；

6,368 个 focal-agent rows；

4 个 critic 各 195 optimizer steps，共 780 步；

source optimizer 和 renewal-actor optimizer 都是 0 步。

收集得到的 KEEP/RENEW 数量为：

i=0
i=1
	​

KEEP
149
146
	​

RENEW
3035
3038
	​

	​


每行保存了 148 维 context、实际二元动作、精确 source propensity 和 next-50 discounted external return。source probability error 小于 10
−6
，binary replay error 为 0，working-prefix mismatch 为 0。

注册分支明确规定：

M0 有效且 M1,M2,M3 任一失败⇒VALID_FAIL_R45_SDRA_IDENTIFIABILITY,

没有 UNDERPOWERED、追加数据或 actor-training 分支。

因此，M1 overlap 失败本身就是有效的科学否决条件，不能被改判为 implementation invalid，也不能通过继续收集数据挽救。

1.2 Collection、propensity 与 clock 没有改变分支的缺陷

普通 check 的 context 和 propensity 是在原始 canonical autoregressive prefix 上重新构造的：

使用冻结 source encoder 和 decoder；

对 focal agent 计算零 residual 的 source-exact binary KEEP/RENEW distribution；

teacher-force 实际存储的 renewal action；

直接存储该 distribution 的 P(RENEW)；

将对应 50-step external block return写入 focal row。

在每个 focal token 后，working roster 与 age 按实际 action 更新，再生成后序 agent 的 context，因此 agent 1 的 estimand正确条件化于 agent 0 已应用的动作。

source MAT、low actor、low critic、q
D
	​

、q
d
	​

 和 renewal actor全部被冻结；runner 的 train() 只清理 buffers并增加 collection counter，不执行任何策略 optimizer。

正式 JSON 进一步确认：

source modules、optimizers、ValueNorm 全部 exact zero drift；

renewal actor zero drift；

source optimizer steps 全为 0；

2,888 次 auto-reset 没有产生 high action、roster/team/age violation；

source zero/final deterministic traces完全相同。

没有发现会改变分支的 reset、freeze、checkpoint 或 evaluation defect。

1.3 Cross-fitting 与 critic comparator 有效

固定 folds 为：

fold A train: env ranks 0–7
fold A held out: env ranks 8–15

fold B train: env ranks 8–15
fold B held out: env ranks 0–7

每个 held-out row只由未见过该 environment rank 的 critic评分；normalization也只使用对应 training fold。

true-Q 与 sham：

使用相同 148 -> 32 GELU -> 2 架构；

从完全相同的初始化复制；

使用相同 minibatch schedules；

使用相同 optimizer、epochs 和 step 数。

true-Q 用实际动作选择：

y
^
	​

true
	​

=q
b
	​

(c),

而 sham 不读取实际动作，只输出 exact behavior-propensity mixture：

y
^
	​

sham
	​

=(1−e(c))q
K
	​

(c)+e(c)q
R
	​

(c).

所以 sham 确实是 action-blind comparator，而不是容量更小的 context baseline。

DR score、IPW weights 和 cluster bootstrap 也按注册公式实现。

未发现 cross-fit leakage、实际动作泄入 sham、propensity/action 错配或 bootstrap 分组错误。

2. M2 clarification verdict
ACCEPT
	​


令：

R=
WMSE
true
	​

WMSE
sham
	​

	​

.

原始文字：

LCB
95
	​

(R)>0

对任何有限正 MSE 几乎恒成立，无法检验 true-Q 是否优于 sham。

执行合同改为：

LCB
95
	​

(R−1)>0,

等价于：

LCB
95
	​

(R)>1.

因为减去常数 1 与 bootstrap quantile 平移严格交换。这才对应“sham error 显著大于 true-Q error”的原始科学意图。

该修改不是结果后的 threshold rescue：

tracked question 在运行前已经指出 literal threshold 的非判别性；

用户在 launch 前明确批准；

ExpRecord、PowerShell runner、result contract 和 analyzer 都在训练前记录了 ratio - 1 版本。

analyzer 对每个 cluster-bootstrap replicate先计算 sham_boot / true_boot，再减 1，最后要求 lower bound >0。

因此这是对一个数学歧义的预结果澄清，不是后验放宽。

3. 可复用的因果结论

必须严格区分五个对象。

对象	R45 建立的结论
action-conditioned predictive information	存在，而且很强
natural causal support / positivity	不足
common-mode renewal value	模型估计几乎全部为正，但因 overlap 失败不能作稳定因果结论
agent-specific timing value	没有证据
task service	冻结 source 的服务能力完整保留
3.1 Action-conditioned prediction 确实有增量信息

Held-out weighted MSE 为：

WMSE
true
	​

=0.038299,
WMSE
sham
	​

=0.376669.

bootstrap ratio-gain 为：

WMSE
true
	​

WMSE
sham
	​

	​

−1=8.8350,

其 95% 区间：

[3.3623, 18.4246].

按 predicted 
Δ
^
 排序后，top-minus-bottom held-out DR score 为：

0.52794,

95% 区间：

[0.40826, 0.70587].

所以 actual KEEP/RENEW action含有 context-only propensity mixture 无法解释的 outcome information；critic完全断路或只拟合 context 不能解释 R45。

3.2 但这不是可靠的 causal-support PASS

Overlap 明确失败：

ESS
0,K
	​

=33.59,ESS
1,K
	​

=3.30,

低于注册的 64。

最大单 environment normalized weight share 为：

0.1475,0.6156,

超过 0.10；agent 1 的 RENEW group 也达到 0.1353。

因此 M2 只支持：

A
t
	​

 对 held-out outcome prediction 有信息
	​


不能支持：

Q
^
	​

(c,R)−
Q
^
	​

(c,K) 已在完整 natural support 上稳定识别
	​


尤其是 agent 1 的 KEEP contrast 主要由极少数高权重 environment clusters承载。继续收集更多相同 policy 数据、clipping propensity 或扩大 critic会改变已注册的 positivity问题，而不是修复 implementation。

3.3 估计结果是 common-mode positive，而非异质 timing value

整体 predicted delta 为：

E[
Δ
^
]≈0.799.

两个 agent 的 bottom-quartile DR score 都没有变成负值：

ψ
0
bottom
	​

:[0.4753, 0.5779],
ψ
1
bottom
	​

:[0.0495, 0.5403].

对应 top quartile 则显著为正。

同一个 check 中两个 agent 的 predicted sign 几乎从不不同：

P[sign(
Δ
^
0
	​

)

=sign(
Δ
^
1
	​

)]=0.000314,

95% 区间：

[0, 0.000942].

这远低于注册的 point floor 0.20 和 lower-bound floor 0.10。

准确表述应当是：

R45 没有在 Alice–Bob natural source support 中找到可用于“一个 agent KEEP、另一个 agent RENEW”的稳定 sign-changing value evidence。

由于 M1 失败，不能进一步宣称真实 causal effect 必然全为正；但可以确定当前数据与模型没有给出异步 timing 所需的反向证据。

3.4 Service 没有被测试性机制改变

R45 没有更新任何 policy。冻结 source 的 zero/final：

win/key0/key1=0.93/1.00/0.93,

完整 high/low traces exact。

因此服务结果只证明：

collection 与 critic fitting 没有污染 R41B source
	​


不证明 SDRA 改善或保持了一个经过训练的 renewal policy，因为本轮根本没有 actor update。

4. Retirement boundary
4.1 确认退休的对象

永久退休：

	​

Alice–Bob K=50
+冻结 R41B source policy
+自然 source-exact KEEP/RENEW support
+SDRA action-Q/DR identification
+异步 renewal actor 的后续训练
	​

	​


以及下列 rescue：

继续收集相同 source policy 数据；

增加 seed；

扩 critic；

propensity clipping；

forced KEEP/RENEW；

simulator clone；

修改 overlap 或 sign thresholds；

在该 substrate 上继续训练 renewal actor。

这与预注册分支及正式 disposition一致。

更精确的 substrate 结论是：

Alice–Bob 仍是 fixed-k HMASD positive skill/cooperation anchor，
	​


但：

它不再是当前项目的正 asynchronous-timing substrate。
	​

4.2 仍未测试

R45 不退休：

joint skill-and-renewal co-adaptation；

具有真实异质时序需求的其他环境；

一般 asynchronous skill learning；

process-level intrinsic semantics；

sparse exploration；

S7 假设；

open roster；

variable team number。

R41B 只证明官方 fixed-k HMASD 能在 Alice–Bob 获得 access。

R42 证明直接 skill-logit residual 会损害服务且未形成充分 temporal decoupling。

R43 证明 true-renewal factorization、clock 和 replay 可以实现，但其 treatment 因 fixed continuation anchor丢失而不可解释。

R44 排除了 source forgetting 与 actor disconnect，却仍没有 deterministic temporal transport。

R45 又表明 Alice–Bob natural support 缺少可识别的异质 renewal signs。以上证据仍没有直接测试自然 skill semantics、joint co-adaptation 或新 substrate。

5. 唯一下一条因果边
R46-HMRV-G0：Heterogeneous Maintenance Renewal-Value Gate

选择：

	​

原生异质 process degradation
→均衡自然 KEEP/RENEW support
→action-specific delayed renewal value
→同一 check 内稳定的正负 value signs
	​

	​


这是一个新 substrate 的 reward-off positive-control gate。

不选择 joint co-adaptation，原因是目前没有一个已经验证会产生异质 timing value 的 substrate；此时同时学习 skill semantics、low executor 与 renewal，只会重新混合 substrate failure 与 algorithm failure。

不选择另一个 Alice–Bob critic，因为 R45 已按绑定分支退休该 natural-support line。

不进入 S7，因为当前门槛只需要最低成本地确认：

当任务确实需要不同 lifetime 时，项目的自然数据与 value read 能否看到它。
	​

6. R46 的精确算法与 substrate 合同
6.1 环境：两智能体异质维护过程

固定：

N=2,k
0
	​

=5,H=40.

每个 agent 维护一个通用 service process，健康度为：

h
i,τ
	​

∈{0,1,2,3,4}.

每个 episode 开始：

h
1,0
	​

=h
2,0
	​

=4.

两个 degradation rates 为：

{d
1
	​

,d
2
	​

}={1,2},

并按 episode index确定性交换给两个 agent，使每个 agent在 evaluation 集中各承担一半 fast/slow process；persistent agent ID不进入模型。

每个 global check 选择：

b
i,τ
	​

∈{KEEP,RENEW}.

若 KEEP，本 block 的 service output 和下一健康度为：

u
i,τ
	​

=
4
h
i,τ
	​

	​

,
h
i,τ+1
	​

=max(0,h
i,τ
	​

−d
i
	​

).

若 RENEW，当前 block 进入维护：

u
i,τ
	​

=0,
h
i,τ+1
	​

=4.

唯一共享外部奖励为：

r
t
env
	​

=min(1,u
1,τ
	​

+u
2,τ
	​

),t∈[τk
0
	​

,(τ+1)k
0
	​

).
	​


奖励不读取 KEEP/RENEW token本身，不奖励 lifetime，不奖励异步性，也没有 distance、progress、contact 或 potential term。异步需求来自环境动力学：

健康 agent 继续服务；

低健康 agent 维护以恢复未来能力；

两者同时维护会使 team service归零；

degradation rate不同，最合适的维护时刻自然不同。

因此这是环境的 native service objective，不是给 renewal policy 添加 shaping。

6.2 Policy factorization

本 gate 不训练 actor。自然行为策略固定为：

μ(b
τ
	​

∣x
τ
	​

)=
i=1
∏
2
	​

Bernoulli(b
i,τ
	​

;0.5).
	​


canonical 顺序仍为 1→2，但第二个 factor也是 0.5，不依赖第一动作。

没有 forced action：每次 KEEP 和 RENEW 都通过同一个显式 stochastic policy采样，并拥有精确 propensity 0.5。

没有 low policy、skill label或 duration action。本轮只验证 renewal timing substrate；不能产生 skill-semantics claim。

6.3 时间与 reset

每 5 primitive steps 一个 check；

每个 episode 8 个 checks；

episode固定在 40 步结束；

没有 episode 内 auto-reset；

没有 arrival-triggered checks；

没有 hidden membership event；

maintenance state只在 block末更新；

最后两个 checks不进入 3-block value estimand，但仍按行为策略执行。

6.4 Information boundary

对 focal agent i，只使用：

c
i
	​

=[
4
h
i
	​

	​

,
4
h
−i
	​

	​

,
2
d
i
	​

	​

,
2
d
−i
	​

	​

,prefix-valid,b
<i
	​

]∈R
6
.

这是一种 self/other、permutation-compatible representation，不含：

agent ID；

task object；

success flag；

reward history；

future health；

oracle maintenance label；

external reward。

外部 reward 只作为离线 outcome target。

6.5 Credit estimand

维护在当前 block产生 opportunity cost，却影响后续健康，因此最小完整 estimand覆盖三个 blocks：

G
τ
(3)
	​

=
r=0
∑
3k
0
	​

−1
	​

γ
r
r
τk
0
	​

+r
env
	​

.
	​


只使用拥有完整三 block future 的前六个 checks。

定义：

Q
i
μ
	​

(c,b)=E
μ
	​

[G
τ
(3)
	​

∣C
i
	​

=c,B
i
	​

=b].

使用与 R45 相同、已验证的 cross-fitted DR 公式，但在全新 substrate 数据上计算：

ψ
i
	​

=
Q
^
	​

i
	​

(c,R)−
Q
^
	​

i
	​

(c,K)+
0.5
1[b=R]
	​

(G−
Q
^
	​

i
	​

(c,R))−
0.5
1[b=K]
	​

(G−
Q
^
	​

i
	​

(c,K)).

本轮仍不把它注入 reward 或 actor。

6.6 Updated 与 frozen 参数

没有 checkpoint 从 R41B、R43、R44 或 R45 迁移。

冻结或不存在：

renewal actor
skill actor
low actor
team latent
discriminator
intrinsic model

只训练四个 critic：

fold-A true-Q
fold-A action-blind sham
fold-B true-Q
fold-B action-blind sham

每个模型：

6 -> 32 GELU -> 2

true-Q 与 sham 使用完全一致的初始化、optimizer、schedule 和 exposure。sham仍输出 propensity mixture，不读取实际 action。

7. 最小 abandonment gate
7.1 固定执行合同
experiment                   R46-HMRV-G0
execution target             local CUDA
cloud execution              prohibited for G0
environment seed             46041
behavior-action seed         46041
agents                       2
health levels                0..4
degradation rates            {1,2}, episode-balanced permutation
episode / rollout            40 / 40
global check                 k0 = 5
rollout environments         16
outer updates                100
environment steps            64,000
usable 3-block checks         9,600
usable focal rows             19,200
policy optimizer steps        0
intrinsic optimizer steps     0
cross-fit folds               env 0–7 / 8–15
critic architecture           6 -> 32 -> 2
critic epochs                 15
minibatch                     256, drop_last=False
optimizer steps/model         570
total critic steps            2,280
evaluation                    100 paired stochastic episodes
evaluation action RNG         fixed and replayable
bootstrap repetitions         10,000
bootstrap seed                62046

每个 fold 有 9,600 training rows：

⌈
256
9600
	​

⌉×15=570

次 optimizer steps/model。

7.2 M0：wiring 与 substrate validity

必须全部满足：

health、degradation、KEEP/RENEW transition逐 row符合注册公式；

reward严格等于 min(1,u
1
	​

+u
2
	​

)；

reward代码不读取 renewal token，只读取执行后的 service output；

action propensity逐 row严格为 0.5；

action replay error为 0；

恰好 64,000 steps、100 updates、19,200 usable factor rows；

policy、low、intrinsic optimizer steps全部为 0；

四个 critic各 570 steps，共 2,280；

folds无 environment overlap；

true/sham初始化、架构、normalization和schedule一致；

gradients、predictions、weights和 DR scores全部有限；

context只含注册的 6 个通用字段；

100-episode pre/post critic-fit action、state和reward traces逐项完全相同；

结果中同时观察到至少一个零 reward block和一个满 service block，排除常数任务。

失败：

INVALID_R46_HMRV_WIRING

唯一动作是修复明确的 transition、reward、split、likelihood或critic错误，并原合同重跑。

7.3 M1：natural overlap

对每个 agent、每个 action：

ESS
i,b
	​

≥64,

并要求：

e
max
	​

∑
e
′
	​

w
e
′
,i,b
	​

w
e,i,b
	​

	​

≤0.10.

因为 propensity固定为 0.5，不允许 clipping、补样本或修改行为 policy。

7.4 M2：action-conditioned informativeness

保持 R45 已澄清的同一判据：

LCB
95
	​

[
WMSE
true
	​

WMSE
sham
	​

	​

−1]>0,

且：

LCB
95
	​

[
ψ
ˉ
	​

top
	​

−
ψ
ˉ
	​

bottom
	​

]>0.
7.5 M3：异质 timing value

对两个 focal identities分别要求：

LCB
95
	​

[
ψ
ˉ
	​

i,top25%
	​

]>0,
UCB
95
	​

[
ψ
ˉ
	​

i,bottom25%
	​

]<0.

同一个 check 中：

P[sign(
Δ
^
1
	​

)

=sign(
Δ
^
2
	​

)]≥0.20,

且：

LCB
95
	​

>0.10.

由于 fast/slow degradation assignment按 episode平衡交换，还必须在两个 role assignments中分别满足：

LCB
95
	​

[P(sign discordance)]>0.10.

这防止模型只把固定 agent index当成“总是先维护”的 shortcut。

7.6 互斥分支
PASS_R46_HMRV_IDENTIFIABILITY

要求：

M0∧M1∧M2∧M3.

允许结论仅为：

在无 skill learning、无 shaping、均衡自然动作支持下，HMRV substrate确实包含可识别的 agent/context-specific renewal timing value。

唯一后续动作：

在完全相同的 HMRV substrate 上注册一次 per-agent renewal actor versus shared-sync control。

仍不进入 S7、joint skill learning、open roster 或 variable-N。

VALID_FAIL_R46_HMRV_SUBSTRATE

M0有效，但 M1、M2 或 M3任一失败。

永久退休：

该 HMRV 动力学；

该三 block estimand；

该环境作为异步 timing positive control。

禁止通过：

修改 degradation rates；

修改 maintenance cost；

修改 horizon；

增加 steps或seed；

扩 critic；

clipping；
-降低 sign thresholds；

进行救援。

唯一后续动作是完成 substrate failure review；在选择另一个全新 causal object 前，不训练 temporal actor。

不存在 UNDERPOWERED 或自动 cloud extension。

8. Prohibitions 与最强反对意见

继续禁止：

R42 residual重命名或扩容；

R43/R44 continuation；

Alice–Bob追加数据；

R45 propensity clipping或 critic expansion；

forced renewal；

simulator clone；

actor entropy/temperature rescue；

task-specific intrinsic reward；

distance、contact、phase、success或目标字段；

duration-category action；
-立即进入 S7；

open-roster implementation；

variable-N implementation。

这符合项目的 promotion ladder：reward-off observational/causal gate必须先于 reward-on actor更新，且上游失败阻塞下游 claim。

最强反对意见
HMRV 是人为构造的 maintenance positive control，其动力学明确包含异质时序需求。
	​


因此即使 R46 PASS，也不能证明：

自然 cooperative roles 会出现；

learned skills具有 semantics；

joint co-adaptation会成功；

S7存在相同 renewal structure；

open roster或 variable team有效。

它只能证明：

当环境真正包含异质 renewal demand 时，自然支持与 value estimator 能否识别该 demand。
	​


这个反对意见不改变决策。R35–R40 和 R45 的共同教训正是：在没有正 substrate 的情况下继续修改算法，会把 substrate absence、access failure和credit failure混为一谈。R46被限定为固定 primitives、零 actor更新、零 intrinsic的最低层正控制，不是新的 benchmark performance claim。

最终单一决定
	​

R45 = VALID_FAIL;
M2 ratio-gain澄清合法且为预结果登记;
M2证明 action-conditioned prediction，
但 M1 不支持稳定 causal contrast；
M3没有发现 agent/context-specific sign heterogeneity；
永久退休 Alice–Bob K=50 natural-support async-timing substrate；
唯一下一边 = R46-HMRV-G0；
先在无 shaping、无 actor更新、均衡 support 的
异质维护 substrate上证明 sign-changing renewal value；
有效失败即永久退休该 substrate，不调参、不扩数据、
不进入 S7、open roster 或 variable team。
	​

	​

