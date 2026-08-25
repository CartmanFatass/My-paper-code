Verdict
ACCEPT R40 SIMPLE_SPREAD ACCESS

R39 native-toy credit route应永久关闭；下一条唯一正向 substrate 路线接受：

official MPE simple_spread + ordinary recurrent MAPPO -> positive cooperative access

但必须明确：

R40 不是 skill experiment，不是 HMASD experiment，不是 intrinsic experiment。

它只回答：

是否存在一个公开、可复现、固定 N 的 cooperative MARL substrate，使普通策略先建立可信 access。

1. R39 native-toy failure 审计

Verdict

VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR

成立。

不存在 estimator 或 implementation defect。

M0 通过

R39 native toy contract：

algorithm:

hmasd_original

scenario:

two_timescale_role_free_actions

fixed：

N=2

n_Z=n_z=4

k_0=5

episode length:

40

rollout:

40

seed:

39041

num_envs:

16

total timesteps:

12800

outer updates:

20

实现检查：

20/20 outer updates；

60/60 high optimizer updates；

low updates = 0；

discriminator updates = 0；

intrinsic reward = external only；

replay max error:

4.76837158203125 x 10^-7

numerical repairs = 0。

因此不能解释为：

PPO bug；

replay bug；

high probability bug；

credit leakage；

intrinsic 干扰。

失败是科学失败

最终：

match=0.455078125

slow=0.46484375

fast=0.4453125

目标：

match>=0.70

slow>=0.65

fast>=0.65

因此：

native toy does not provide a positive HMASD credit substrate

2. R39 native-toy route 永久退休

必须关闭：

two_timescale_role_free_actions 作为 HMASD credit gate；

oracle credit；

counterfactual credit；

open-roster extension；

custom CTS/Alice-Bob 修补。

入口文件明确禁止：

another run or objective on two_timescale_role_free_actions, including oracle or counterfactual credit.

3. 可复用因果结论

R35-R39 的共同结论现在更清晰：

不是技能问题

因为：

R27 已证明：

z -> conditional behavior

存在。

不是 credit factorization 问题

R39 中：

factorization:

pi_H(Z|x) pi_1(z_1|x,Z) pi_2(z_2|x,Z,z_1)

保持。

并且：

earlier capacity：

minimum correct unordered roster mass=0.999487

通过。

当前真正缺口

没有可靠的正向 cooperative access substrate

在没有 substrate 时：

intrinsic；

skill discovery；

lifetime；

roster；

HMASD temporal mechanism

都无法公平评价。

4. 为什么选择 official MPE simple_spread

接受 R40。

理由：

它满足当前缺失的属性：

固定 N

避免：

variable team；

open roster；

membership credit。

当前 gate：

N=3

固定。

已知 cooperative access

simple_spread：

官方 MPE；

PettingZoo 支持；

MAPPO 社区已有实现；

dense cooperative reward；

可验证 ordinary policy baseline。

入口给出的路线：

official fixed-N MPE simple_spread -> ordinary recurrent MAPPO -> positive cooperative access

5. R40 唯一 causal edge

必须保持：

ordinary recurrent MAPPO -> positive cooperative access

禁止提前加入：

HMASD；

fixed-k；

skill；

intrinsic；

lifetime。

原因：

如果 baseline 都没有 access，则后续所有 skill claim 无法解释。

6. R40 实验合同

Environment

固定：

MPE simple_spread

版本：

PettingZoo 1.24.3

Agent number

固定：

N=3

不是 variable-N。

原因：

当前目标是 credit substrate，不是 roster scalability。

Local ratio

固定：

local_ratio=1.0

即：

完全 decentralized actor。

Action

MPE continuous action。

动作模式：

continuous vector action。

Horizon

固定：

H=25

Observation

Actor:

原生 local observation。

允许：

self velocity；

self position；

landmark relative positions；

teammate relative positions。

禁止：

global state；

reward；

success flag。

Critic

centralized MAPPO critic：

输入：

global state。

Policy

ordinary recurrent MAPPO：

Actor：

pi(a_i|o_i,h_i)

Critic：

V(s,h)

hidden size：

64

7. Training Budget

Seed

训练：

40041

Environment

num_envs=16

Rollout

25

Total steps

200000

计算：

16 x 25 x 500 = 200000

PPO

updates：

500

epochs：

5

sequence length：

25

minibatch：

64

learning rate：

3e-4

gamma：

0.99

GAE：

0.95

clip：

0.2

value coefficient：

0.5

entropy coefficient：

0.01

gradient clip：

0.5

8. Evaluation

Evaluation seeds：

40042,40043,40044,40045

每 seed：

64

总：

256

9. Metrics

只使用 native environment metrics。

Primary

合作覆盖/目标完成率：

success

Secondary

episode return：

R

不允许

派生：

intrinsic score；

skill metric；

role metric；

lifetime metric；

agent identity metric。

10. Null comparator

Random policy：

动作：

U(action)

同：

reset；

evaluation seeds。

paired evaluation。

11. Decision Gate

M0 INVALID

必须：

MPE version frozen；

N=3；

no skill；

no intrinsic；

no shaping；

actor local only；

critic centralized。

失败：

INVALID

下一动作：

修实现。

M1 Access

MAPPO：

要求：

平均 success：

>=0.30

并且：

MAPPO-random：

paired bootstrap:

CI_95,lower >0

M2 Repeatability

四个 evaluation seed：

至少：

3/4

seed：

success > 0。

Bootstrap

次数：

10000

unit：

paired episode。

seed：

60041

分支

PASS_R40_SIMPLE_SPREAD_ACCESS

条件：

M0-M2 全通过。

下一动作：

允许：

native fixed-k HMASD

在同一 simple_spread substrate 上测试。

仍禁止：

variable N；

open roster；

intrinsic；

lifetime。

VALID_FAIL_R40_ACCESS

条件：

M0通过，但 M1/M2失败。

结论：

ordinary cooperative access substrate 未建立。

下一动作：

停止在该 substrate 上进行 HMASD credit/lifetime 比较。

INVALID

条件：

M0失败。

下一动作：

修实现。

12. PASS 后允许什么

PASS 只授权：

simple_spread + native fixed-k HMASD

比较。

它不授权：

HMASD superiority；

skill discovery；

variable team number；

intrinsic reward；

per-agent lifetime。

最终裁决

ACCEPT R40 SIMPLE_SPREAD ACCESS

核心原因：

R39 已经证明：

custom toy credit substrate

不能作为研究基础。

下一步必须先建立：

公开、固定 N、普通 MARL 可访问的 cooperative substrate

然后才重新进入：

fixed-k -> per-agent lifetime -> HMASD/HA-CTSE

而不是继续在定制 toy 上调整 credit。
