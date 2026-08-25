1. Verdict
VALID_FAIL_M1_RETIRE_R36_AEM

R36-AEM 结果有效，必须退休精确的 R36 direct joint-position novelty access bonus。

不存在改变 estimand 的实现缺陷。

审计结论：

bonus 注入路径正确；

per-environment count reset 正确；

low-GAE-only 路径正确；

control isolation 正确；

sparse-only evaluation 正确；

coverage metric 正确；

bootstrap/branch order 正确。

R36 不是“弱探索结果”，而是一个有效的负结果：

undirected visitation expansion != sparse task access

2. R36 结果建立什么，不能建立什么
已建立

R36 测试的因果边：

joint-position novelty -> broader visitation -> sparse access

结果：

visitation 成功

AEM：

Coverage=0.063900

Control：

Coverage=0.016575

ratio：

3.855204

paired difference：

0.047325

CI：

[0.045400,0.049175]

说明：

r_novel 确实改变了行为分布。

但是：

access 完全失败

AEM：

cycle=0
collection=0/64

paired collection：

0

要求：

10/64

因此：

coverage !=> access

不能建立

禁止解释：

AEM 不如 task reward；

MAPPO 不行；

R30 不行；

hierarchy 没价值；

sparse exploration 已失败。

原因：

R36 只证明：

state breadth

不是：

task-relevant coordinated occupancy

3. Alice-Bob information contract 审计
结论：

当前 Alice-Bob access gate 存在隐藏 identity bottleneck。

不是实现 bug。

但是作为 access benchmark：

当前 actor observation contract 不适合作为算法比较入口

当前 actor observation

包含：

own position；

other agent relative position；

button offsets；

target offsets。

但是不包含：

active button identity；

active target identity；

task clocks；

contacts；

collection state；

reward progress。

关键问题

环境：

button 每 40 steps变化；

target 每 10 steps变化；

active identity 随机初始化。

central critic：

拥有：

active one-hot；

clocks。

actor：

没有。

因此：

第一阶段：

actor无法知道：

(button,target)

是否对应当前任务。

这意味着：

任务需要：

hidden identity inference

而不是单纯：

exploration

另外一个问题

coverage 使用：

5^4 position bins。

单 bin：

8/5=1.6

而 contact radius：

0.70

所以：

进入同一个 cell !=> 接触成功。

因此：

coverage 是合法 diagnostic，但不是 access proxy。

4. 唯一路线：Observation Substrate Repair

接受入口提出的 substrate repair。

不是算法贡献。

这是 benchmark validity repair。

R37：Actor-Visible Task Identity Access Gate

不是 skill。

不是 intrinsic reward。

不是 exploration algorithm。

目标：

验证：

当前 sparse task 是否因 actor information bottleneck 不可达

5. R37 algorithm semantics
Actor observation 修改

只增加当前任务必要 identity：

新增：

o_i' = [o_i, onehot(active_button), onehot(active_target)]

不增加：

reward；

progress；

contact；

future state；

oracle action；

distance shaping。

保留

环境 reward：

r_t = r_collection

不变。

Actor

MAPPO：

pi(a_i | o_i')

Critic

保持：

V(s)

当前 centralized critic。

Gradient

更新：

actor；

critic。

冻结：

skill；

high controller；

KEEP/SET；

all intrinsic modules。

R30 角色

继续：

Diagnostic only

不训练。

原因：

先证明：

task access exists

再讨论 hierarchy。

6. 最小 Alice-Bob decision gate
Arms
Arm A

Observation-repaired recurrent MAPPO。

Arm B

Original constant-code recurrent MAPPO。

注意：

不是 R36。

不是 novelty。

初始化

两臂：

同：

zero-step initialization；

seed；

network size；

optimizer。

Budget

保持 R35/R36 access 规模：

seed:
38031

envs:
16

rollout:
80

steps:
320000

low updates:
250

PPO epochs:
5

sequence length:
10

batch:
64

evaluation:
64 stochastic episodes

M0 validity

必须：

reward 完全一致；

无 shaping；

无 intrinsic reward；

唯一区别：

actor observation 增加 identity。

critic input unchanged；

recurrent state contract一致；

PPO exposure一致。

失败：

INVALID。

M1 Access floor

必须：

collection episodes：

>=10/64

cycle success：

>=0.05

paired collection indicator：

CI_lower >0

M2 Task performance

collection reward：

要求：

R_repair >0

并且：

cycle completion：

>0

M3 Stability

zero-cycle fraction：

要求：

<0.9

Bootstrap

unit：

episode。

10000 bootstrap。

Result branches
PASS_R37_ACCESS

结论：

Alice-Bob 在修复 actor information contract 后成为有效 sparse access benchmark。

只支持：

observation repair -> access

不支持：

算法提升；

skill提升；

hierarchy提升。

下一步才允许比较：

MAPPO；

R30；

HA-CTSE。

FAIL_R37_ACCESS

结论：

即使 actor 获得必要任务 identity，当前 sparse task 仍无法形成 access。

下一步：

停止在该 benchmark 上做算法比较。

INVALID

只修：

observation wiring；

experiment contract。

不改变算法。

7. 最终结论

R36 的核心发现：

Undirected exploration is not the missing causal carrier.

它已经被有效关闭。

当前更上游的问题：

Can the decentralized actor even observe enough information to solve the task?

因此唯一下一步：

R37: Observation Substrate Repair

顺序恢复：

information validity -> access -> learning -> coordination -> hierarchy

在 access contract 没有成立之前，不重新打开 skill、hierarchy 或 intrinsic mechanism。
