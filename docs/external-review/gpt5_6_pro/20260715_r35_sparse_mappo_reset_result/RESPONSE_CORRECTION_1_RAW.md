1. VALID_NO_ACCESS_R35_UNRESOLVED

接受当前纠偏。

R35 Sparse MAPPO Reset 的实现与实验合同有效，但结果不能用于判断：

MAPPO 是否优于 R30；

R30 skill abstraction 是否有价值；

hierarchy 是否必要；

skill 是否失败。

原因是 access floor 在比较前失败。

实际结果：

Constant-code recurrent MAPPO

320,000 train steps

250 low updates

64 stochastic evaluation episodes

cycle success mean = 0

collection episodes = 0

joint coverage mean = 0.015

zero-cycle fraction = 1

Reward-pure trained R30

320,000 train steps

250 low updates

64 stochastic evaluation episodes

cycle success mean = 0

collection episodes = 0

joint coverage mean = 0.013625

zero-cycle fraction = 1

paired evaluation:

collection in either arm = 0/64

而注册最低要求：

10/64

因此：

R35 cannot answer MAPPO vs R30

这不是 implementation failure：

!= INVALID

而是：

VALID_NO_ACCESS_R35_UNRESOLVED

2. R35 结论边界

可复用结论

唯一可靠结论：

在当前 Alice-Bob sparse setting、当前 checkpoint 初始化和训练预算下，无 skill recurrent MAPPO 与 reward-pure R30 都没有进入可评估 task-access 区域。

也就是：

optimization -> access

这一步尚未成立。

禁止结论

不能推出：

不可以说：

MAPPO 胜过 R30；

R30 胜过 MAPPO；

skill abstraction 无价值；

hierarchy 无价值；

KEEP/SET 失败；

HA-CTSE 失败；

sparse exploration 已解决。

因为：

P(access) = 0

时：

P(task success | access)

无法估计。

3. R29-R35 closure 保持

维持：

RETIRE

R29 action separation !=> stable skill

R31 trajectory association !=> causal persistence

R32 individual effect gradient !=> codebook formation

R33 selector !=> primitive creation

R34 trajectory relabel !=> stronger skill

同时：

OCSF retired；

CBF retired；

TMPF invalid。

不重新进入：

skill latent；

classifier；

effect reward；

roster score；

mode clustering；

scheduler/hazard。

4. 唯一下一路线：R36-AEM

Access-first Exploration via Memoryless State Novelty

这是一个非 skill、非 hierarchy、非 latent 方向。

核心因果边：

state visitation novelty -> reachable region expansion -> sparse reward access

它不回答：

“如何形成 skill”。

它先回答：

当前 agent 是否连任务相关状态空间都无法进入？

5. R36 algorithm semantics

5.1 State input

定义：

x_t = [p_1^x, p_1^y, p_2^x, p_2^y]

normalized position view。

禁止：

target；

button；

collection；

reward；

contact；

phase；

skill；

latent。

5.2 Occupancy memory

建立固定 state hash：

h(x_t)

例如：

5^4 joint position bins。

维护：

N(h)

访问计数。

5.3 Exploration bonus

定义：

r_t^novel = 1 / (N(h(x_t)) + 1)

总 reward：

r_t = r_t^env + beta r_t^novel

其中：

beta 固定；

不 sweep；

不调优。

5.4 Policy

普通 MAPPO：

Actor：

pi(a_i | o_i)

Critic：

V(s)

目标：

L = L_PPO + c_v L_V - c_H H

唯一 reward：

r_t

包含：

sparse external reward；

state novelty bonus。

5.5 Gradient boundary

更新：

Actor pi_theta(a_i | o_i)

Critic V_phi(s)

冻结：

R30 high controller；

KEEP/SET；

skill head；

all latent；

all classifier；

all effect module。

5.6 R30 角色

R30 不参与训练。

仅作为历史 reference。

原因：

当前需要先回答：

Can a non-skill policy access the task?

如果 access 都无法恢复，继续讨论 skill 没有因果基础。

6. 最小 Alice-Bob abandonment gate

Arms

Arm A

R36-AEM:

MAPPO + r_novel

Arm B

Constant-code MAPPO:

即 R35 reset baseline。

初始化

两臂：

同 checkpoint；

同 network size；

同 random seed；

同 optimizer。

Budget

每 arm：

seed:

37031

envs:

16

rollout:

500

PPO updates:

250

epochs:

15

minibatch:

32

optimizer:

Adam

lr:

3e-4

evaluation:

64 stochastic episodes

M0 validity

必须：

同 environment；

同 transition exposure；

同 PPO update 数；

同 evaluation seeds；

novelty 只读取 position view；

no task field；

no skill input；

no hierarchy input。

失败：

INVALID

只修实现。

Metrics

M1 Access floor

primary：

collection episodes：

要求：

>=10/64

M2 Task access

cycle completion：

要求：

cycle_success > 0

M3 Coverage

固定：

625 joint position cells。

要求：

Coverage_AEM >= 1.5 Coverage_MAPPO

M4 Stability

zero-cycle fraction：

要求：

<0.9

Bootstrap:

cluster = episode；

10000 bootstrap；

no threshold modification。

7. 结果分支

PASS_R36_ACCESS

条件：

全部通过。

结论：

当前主要瓶颈是 state access，而不是 skill abstraction。

下一步才重新讨论：

hierarchy；

temporal abstraction；

skill。

FAIL_R36_ACCESS

结论：

当前问题不是 skill，而是基础 sparse access failure。

停止：

skill discovery；

hierarchy search；

intrinsic mechanism search。

INVALID

只修：

implementation；

environment；

training wiring。

不改变算法。

8. 最终裁决

R35 = VALID_NO_ACCESS_UNRESOLVED

不是 MAPPO 胜利，也不是 R30 失败。

当前研究顺序必须改变：

access -> learning -> coordination -> hierarchy

唯一下一条可证伪路线：

R36-AEM: non-skill access-first state novelty exploration

在 access 被证明之前，不重新进入 skill formation。
