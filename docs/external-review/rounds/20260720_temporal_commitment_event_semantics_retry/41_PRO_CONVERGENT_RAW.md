1. 中文路线简报

本轮目标是推进更强 MARL 任务：在匿名动态成员、JOIN/LEAVE/REJOIN、survivor continuity 与异步个体生命周期下，验证显式 temporal commitment 是否比普通 recurrent hidden state 提供不可约能力。

下一步只构建一个机制：

event-held learned commitment

即策略学习一个在事件之间保持不变的 commitment state，并由显式事件决定 create / keep / renew / terminate。

ordinary recurrent MARL 保留为严格匹配 comparator，用于判断 commitment 是否超过普通记忆能力，而不是作为研究准入门槛。

结果解释：

若 event-held commitment 无优势：说明普通 recurrent explanation 更充分；

若其在容量匹配和 held-out lifetime 条件下有效：支持 temporal abstraction；

若 benchmark 无法识别：停止该 benchmark；

不通过调参、扩大模型或修改 reward 挽救失败路线。

本轮不重新选择 portfolio，仅完成已经选择的 LEARNED_COMMITMENT_REPRESENTATION_G0 合同。

2. Correction verdict

接受前序修正要求。

此前：

z
t+1
c
	​

=f(z
t
c
	​

,o
t
	​

,h
t
	​

)

每个 physical step 更新。

该定义实际上只是：

auxiliary recurrent memory；

而不是：

event-held commitment；

realized individual lifetime；

commitment segment。

因此无法支持：

commitment duration claim；

variable lifetime claim；

natural-use metric。

Selected disposition

选择：

EVENT_HELD_COMMITMENT

拒绝：

AUXILIARY_RECURRENT_REPRESENTATION；

STOP_SOURCE。

理由：

该 source 的科学目标就是区分：

ordinary recurrent memory

vs

explicit temporal commitment。

若退化为 recurrent augmentation，则无法回答最终 mission。

3. Causal claim and strongest ordinary explanation
Causal claim

引入一个：

z
i
c
	​


作为事件持有 commitment state。

它由：

create；

keep；

renew；

terminate；

事件驱动。

在两个 commitment event 之间：

z
i,t+1
c
	​

=z
i,t
c
	​


保持不变。

目标：

验证：

event-held commitment 是否产生 ordinary recurrent policy 无法替代的自然异步生命周期行为。

Strongest ordinary explanation

最强简单解释：

commitment 只是增加一个低频 recurrent memory channel，所有收益来自容量提升。

因此必须证明：

不是：

参数更多；

hidden 更大；

memory 增加。

而是：

event boundary；

segment semantics；

explicit persistence；

产生不可约价值。

4. Commitment algorithm contract
Commitment state

每个 lifecycle：

z
i
c
	​

∈{−1,0,+1}
K

其中：

K=8

每个维度：

离散 ternary commitment component。

Segment ownership

定义：

一个 commitment segment：

S
i
k
	​

=[t
create
	​

,t
terminate
	​

)

期间：

z
i
c
	​


固定。

Event semantics
Create

发生：

Genuine JOIN

初始化：

z
i
c
	​

=0

然后立即产生：

SET(z
i
c
	​

)

一次commitment decision。

Hold

普通 physical step：

z
t+1
c
	​

=z
t
c
	​


无梯度更新。

Keep

在 commitment opportunity event：

policy 可以选择：

KEEP

保持：

z
new
	​

=z
old
	​

Renew

policy 可以选择：

RENEW(z
′
)

替换：

z
new
	​

=z
′

结束旧 segment，开启新 segment。

Terminate

发生：

terminal leave；

episode termination。

删除：

z
i
c
	​

5. Clocks and ordering
Physical clock

每环境 primitive step：

推进：

state；

reward；

action。

Membership clock

事件：

JOIN；

LEAVE；

REJOIN。

Commitment clock

只在：

commitment opportunity

推进。

Segment clock

只记录：

Δ
i
	​


两个 commitment event 之间 active duration。

Ordering
同一步 JOIN

顺序：

membership update；

create lifecycle；

initialize z
c
=0；

commitment opportunity；

choose initial commitment；

primitive action。

Temporary LEAVE

顺序：

完成当前 primitive transition；

snapshot lifecycle；

close learning segment；

freeze commitment；

remove active mask。

REJOIN

顺序：

restore lifecycle；

restore commitment；

increment epoch；

open new execution segment。

Episode termination

顺序：

close commitment segments；

final reward；

checkpoint。

6. Actor, critic and probability contract
Actor

Baseline：

π(a
i
	​

∣o
i
	​

,h
i
	​

)

Commitment：

π(a
i
	​

,e
i
	​

∣o
i
	​

,h
i
	​

,z
i
c
	​

)

其中：

e
i
	​

∈{KEEP,RENEW(z
′
)}
Action factorization

事件时：

π(e
i
	​

∣context)

physical step：

π(a
i
	​

∣o
i
	​

,h
i
	​

,z
i
c
	​

)
Sampling order

每个 commitment event：

sample event action；

update commitment；

execute following primitive actions。

Execution authority

commitment：

policy-owned。

membership：

environment-owned。

future demand：

不可见。

7. Reward and credit contract

保持：

External reward only
r
t
	​


不改变。

Return

仍：

R
t
	​

=
k
∑
	​

γ
k
r
t+k
	​

PPO / GAE

保持：

A
t
GAE
	​


禁止：

commitment reward；

lifetime reward；

duration bonus。

8. Gradient and optimizer contract
Gradient

Actor：

接收：

∇
θ
	​

L
PPO
	​


包括：

primitive action；

commitment decision。

Commitment state：

不通过：

MI；

classifier；

posterior。

Detach

segment boundary：

detach:

h
i
	​

,z
i
c
	​


避免跨 segment credit 泄漏。

Optimizer

两 arm：

recurrent baseline；

event commitment。

保持：

optimizer；

steps；

exposure。

9. Capacity-matched comparator
Baseline

ordinary recurrent：

π
D
	​

(a∣o,h)
Treatment

commitment：

π
C
	​

(a,e∣o,h,z
c
)
Capacity matching

总有效参数：

∣Params
C
	​

−Params
D
	​

∣<1%

方式：

减少 recurrent hidden width。

禁止：

直接扩大模型。

10. Frozen experiment contract
Environment

保持：

noncalendar heterogeneous tracking G0；

anonymous membership；

held-out lifetime distribution。

Training

每 arm：

16 environments
320000 transitions
250 updates
1000 optimizer steps
4000 episodes
Seeds

保持：

init 58058
ledger 68058
order 78058
action 88058

IID 98058
held-out 99058

bootstrap 108058
Evaluation

每 arm：

IID deterministic 256
IID stochastic 256

held-out deterministic 256
held-out stochastic 256
11. Metrics and thresholds
Primary estimand
ΔU=U
C
	​

−U
D
	​

External value

要求：

LCB
95
	​

(ΔU)>0.10
Commitment-specific criteria

必须同时满足：

Natural use

至少：

P(KEEP)>0.2

且：

P(RENEW)>0.1
Lifetime diversity

commitment segment duration：

满足：

CV(T)>0.25

并且：

至少两个 lifetime bins：

占比：

>10%
Intervention

固定：

同一：

observation；

hidden；

environment state；

替换 commitment：

必须产生：

TV(π(a∣z
1
	​

),π(a∣z
2
	​

))>0.1
12. Mutually exclusive branches
INVALID

触发：

replay；

checkpoint；

probability；

lifecycle；

RNG。

处理：

只修工程。

ORDINARY_CAPACITY_EXPLANATION_SUPPORTED

条件：

commitment 无 external gain。

更新：

D ↑；

T ↓。

解释：

普通 recurrent 足够。

COMMITMENT_SUPPORTED

条件：

同时：

external gain；

natural usage；

lifetime diversity；

intervention effect。

更新：

T ↑；

进入下一 integration review。

但不证明：

hierarchy superiority；

HMASD parity。

REPRESENTATION_ONLY

条件：

commitment gain 消失：

capacity matched 后；

或 dummy control 后。

更新：

T ↓。

NO_ACCESS

条件：

commitment 与 baseline 均失败。

解释：

benchmark/access 问题。

不进入 hierarchy。

BENCHMARK_NON_IDENTIFIABLE

条件：

无法区分：

recurrent；

commitment；

benchmark shortcut。

停止。

13. Replacement ledger
Retain

membership runtime；

anonymous lifecycle；

survivor continuity；

PPO；

external reward；

direct comparator。

Add

commitment state table；

commitment event ledger；

commitment action head。

Replace

替换：

primitive-only execution：

π(a∣o,h)

为：

π(e,a∣o,h,z
c
)
Delete

无。

14. Prohibitions and parked ideas

禁止：

intrinsic reward；

task shaping；

identity；

role；

skill classifier；

posterior；

duration catalogue；

hazard；

graph；

team latent；

new credit objective。

Parked
Temporal credit modification

重新激活：

只有 commitment 已证明存在，但 assignment/value mismatch 明确。

Factorized executor

重新激活：

commitment 有价值但执行器冲突。

Applied-prefix cooperation

重新激活：

真实 multi-owner coordination conflict。

Continuous commitment

重新激活：

离散 commitment 成功后需要更强泛化。

Final disposition

冻结：

EVENT_HELD_COMMITMENT
	​


唯一改变：

policy representation

保持：

external reward / PPO credit / action interface contract

该 source 的目标是回答：

显式事件持有 commitment 是否比普通 recurrent memory 提供真正 temporal abstraction。

不是证明普通 MARL 失败，也不是直接构建完整 hierarchy。