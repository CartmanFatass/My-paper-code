1. 中文路线简报

本轮构建并验证：

event-held learned commitment

目标：

在匿名动态成员、JOIN/LEAVE/REJOIN、异步成员生命周期下，判断一个由事件创建、事件保持、事件更新的 learned commitment state 是否提供 ordinary recurrent MARL 无法替代的时间抽象能力。

下一步不是增加 reward、skill classifier 或 hierarchy stack，而是冻结一个单独机制：

commitment representation 改变；

external reward、PPO credit、primitive action contract 保持不变。

ordinary recurrent MARL 是匹配 comparator，用于判断 commitment 是否超过普通 recurrent memory，而不是研究准入条件。

结果解释：

commitment 无优势 → temporal abstraction 降权；

commitment 有稳定 external value → 支持 event-held abstraction；

仅容量优势 → 归因回 representation；

benchmark 无法识别 → 停止该 source。

2. Correction verdict

接受修正要求。

此前 z_i^c 虽然被描述为 event-held，但仍存在三个问题：

commitment 更新过程未冻结；

create/keep/renew/terminate action support 不完整；

segment boundary detach 改变了 credit horizon。

因此此前方案无法区分：

event-held commitment；

extra recurrent capacity；

changed temporal credit。

本轮保留：

EVENT_HELD_COMMITMENT

但重新冻结完整 event contract。

同时保持：

external reward；

PPO/GAE credit；

anonymous membership；

survivor continuity；

ordinary recurrent comparator。

禁止加入第二 treatment。

3. Causal estimand and strongest explanation
Primary causal estimand

比较：

ΔU=U
commit
	​

−U
ordinary
	​


其中：

ordinary：

π
D
	​

(a
i
	​

∣o
i
	​

,h
i
	​

)

commitment：

π
C
	​

(a
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

目标：

证明：

z
i
c
	​


作为事件持有状态，产生：

natural persistence；

heterogeneous lifetime；

external task improvement。

Strongest ordinary explanation

最强反解释：

commitment 只是增加一个额外 hidden memory channel，本质仍是 recurrent capacity。

因此必须控制：

参数量；

optimizer exposure；

observation；

reward；

communication。

4. Commitment state and event process
Commitment state

定义：

z
i
c
	​

∈[−1,1]
8

连续向量。

原因：

避免人为离散 skill catalogue。

Segment

定义：

第 k 个 commitment segment：

S
i
k
	​

=[τ
k
	​

,τ
k+1
	​

)

期间：

z
i
c
	​

(t)=z
i
c
	​

(τ
k
	​

)

严格冻结。

Event clock

只有 commitment event 才修改：

z
i
c
	​

Event action support

事件策略：

e
i
	​

∈{KEEP,RENEW(z
′
),TERMINATE}

其中：

z
′
∈[−1,1]
8
JOIN

顺序：

membership creates lifecycle；

recurrent hidden = 0；

commitment state：

z
i
c
	​

=0

forced initial commitment opportunity；

policy 选择：

RENEW(z
′
)
KEEP

保持：

z
t+1
c
	​

=z
t
c
	​


segment duration 增加。

RENEW

结束旧 segment：

S
i
k
	​


创建：

S
i
k+1
	​


更新：

z
i
c
	​

←z
′
TERMINATE

删除：

z
i
c
	​


只允许：

terminal leave；

episode termination。

5. Opportunity scheduling

为了避免第二 mechanism：

commitment opportunity 使用已有 exogenous membership/event clock。

定义：

每个 active lifecycle：

Δ
i
opp
	​

∼Uniform{4,8,12}

由 environment ledger 提供。

policy 不决定 opportunity 时间。

因此：

commitment 内容是 learned；

commitment 时间仍 external。

6. Clock ordering
Physical clock

每一步：

primitive action；

environment transition；

reward accumulation。

Membership clock

优先于 commitment：

JOIN

membership

→ commitment create

→ primitive execution。

Temporary LEAVE

顺序：

完成当前 primitive；

close segment ledger；

freeze：

(h
i
	​

,z
i
c
	​

)

remove active mask。

REJOIN

顺序：

restore lifecycle；

restore：

(h
i
	​

,z
i
c
	​

)

increment epoch；

wait next commitment opportunity。

Terminal LEAVE

顺序：

final primitive；

close segment；

final reward credit；

delete lifecycle。

7. Actor, critic and probability contract
Actor

primitive:

π
a
	​

(a
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

event:

π
e
	​

(e
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
Critic

centralized critic：

V(o
team
	​

,h,z
c
)

允许：

active anonymous aggregation。

禁止：

identity；

role；

future lifetime。

Sampling order

commitment event：

sample event action；

update commitment；

primitive rollout。

physical step：

primitive action；

transition。

Probability factorization

单 lifecycle：

π(e
i
	​

∣C
i
	​

)
t
∏
	​

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

Replay 必须保存：

event old logprob；

primitive old logprob；

masks；

commitment state；

segment id；

lifecycle id。

8. Credit contract

保持 unchanged。

Primitive return
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

Event return

不新增：

R
event

原因：

否则同时改变：

representation；

credit。

Advantage

保持：

GAE(γ,λ)
Gradient

event head：

score function：

∇logπ
e
	​

(e)A

primitive：

∇logπ
a
	​

(a)A
Detach

segment boundary：

不 detach credit。

只 detach：

environment state。

原因：

保持 PPO credit contract。

9. Capacity matched comparator
Baseline

ordinary recurrent：

π
D
	​

(a∣o,h)
Commitment model
π
C
	​

(e,a∣o,h,z
c
)
Capacity control

总参数：

∣Params
C
	​

−Params
D
	​

∣<1%

方式：

减少 recurrent hidden width。

Representation-only control

新增：

Dummy commitment control

加入同样维度：

z
dummy

但：

z
dummy
=0

始终固定。

作用：

区分：

commitment representation；

extra input/capacity。

10. Frozen experiment contract
Environment

保持：

noncalendar heterogeneous tracking G0。

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
heldout 99058

bootstrap 108058
Evaluation

每 arm：

IID deterministic 256
IID stochastic 256

heldout deterministic 256
heldout stochastic 256
11. Natural use and lifetime metrics
Natural commitment usage

统计：

P(KEEP)

和：

P(RENEW)

要求：

KEEP>0.2
RENEW>0.1
Lifetime diversity

定义：

T
i
	​


commitment active duration。

要求：

CV(T)>0.25

并：

至少两个 duration bins：

>10%
Intervention

固定：

observation；

hidden；

environment。

替换：

z
1
c
	​

,z
2
c
	​


要求：

TV(π
a
	​

(z
1
	​

),π
a
	​

(z
2
	​

))>0.1
12. Quantitative outcome branches
INVALID

条件：

replay；

checkpoint；

probability；

lifecycle；

RNG。

失败。

处理：

工程修复。

ORDINARY_CAPACITY_SUPPORTED

条件：

commitment:

无 external gain；

dummy control 同等。

更新：

D ↑；

T ↓。

解释：

capacity/recurrent 足够。

REPRESENTATION_ONLY

条件：

commitment gain：

消失于 dummy control。

更新：

T ↓。

COMMITMENT_SUPPORTED

条件：

同时：

external gain：

LCB(ΔU)>0.10

natural usage 达标；

lifetime diversity 达标；

intervention 达标。

更新：

T ↑。

允许进入 integration review。

NO_ACCESS

条件：

baseline 与 commitment 都无法达到：

U≥0.78

处理：

该 benchmark 不证明 temporal abstraction。

BENCHMARK_NON_IDENTIFIABLE

条件：

无法区分：

commitment；

recurrent；

capacity。

停止。

13. Replacement ledger
Retain

membership runtime；

survivor continuity；

ordinary recurrent baseline；

external reward；

PPO/GAE。

Add

新增：

commitment state table；

commitment event head；

commitment ledger。

Replace

替换：

π(a∣o,h)

为：

π(e,a∣o,h,z
c
)
Delete

无。

14. Prohibited changes and parked ideas

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
Credit modification

重新激活：

只有 commitment 已证明存在，而 assignment credit 成为瓶颈。

Factorized executor

重新激活：

commitment 成功，但 low executor interference 出现。

Applied-prefix cooperation

重新激活：

出现真实 multi-owner coordination conflict。

Continuous marks

重新激活：

event-held commitment 成功后，需要连续 composition。

Final disposition

选择：

EVENT_HELD_COMMITMENT_CODE_READY
	​


本轮冻结：

唯一 causal change：

event-held learned commitment representation

保持：

external reward + PPO credit + ordinary comparator

该 source 只回答：

显式事件持有 commitment 是否提供 ordinary recurrent memory 无法替代的 temporal abstraction。

不回答：

完整 hierarchy；

HMASD 复现；

UAV 泛化；

communication；

team latent。