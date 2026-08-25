1. Decision
EVENT_HELD_COMMITMENT_CODE_READY_FINAL

保留 EVENT_HELD_COMMITMENT source。

本轮不重新打开 portfolio，不重新评估 G0/D0/D1，不把 ordinary-controller access 作为 prerequisite。当前任务是将 event-held commitment 冻结为一个可实现、可回放、可统计判定的单一 causal treatment。

2. Causal estimand and simpler explanation
Primary causal claim

比较：

Δ
U
	​

=U
EHC
	​

−U
OR
	​


其中：

OR：ordinary recurrent controller；

EHC：event-held commitment controller。

目标：

证明：

一个由事件创建、事件保持、事件更新的 learned commitment state，能够产生 ordinary recurrent hidden state 无法解释的 temporal organization。

Strongest simpler explanation

最强反解释：

EHC 只是增加参数、额外 memory channel 或 action head。

因此必须通过：

ordinary baseline；

literal capacity matched control；

dummy representation control；

区分：

普通容量；

recurrent representation；

真正 event-held commitment。

3. State machine and clocks
3.1 Clocks

四层 clock：

Physical clock

每一步：

t→t+1

负责：

primitive transition；

environment reward。

Membership clock

事件：

JOIN；

temporary LEAVE；

REJOIN；

terminal LEAVE。

Commitment opportunity clock

每个 active lifecycle：

τ
i
k
	​


由 environment RNG 产生：

Δ
i
k
	​

∼Uniform{4,8,12}

下一机会：

τ
i
k+1
	​

=τ
i
k
	​

+Δ
i
k
	​


policy 不控制机会时间。

Commitment segment clock

segment:

S
i
k
	​

=[τ
i
k
	​

,τ
i
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
i
k
	​

)

固定。

3.2 Event ordering
普通 physical step

顺序：

读取当前 commitment；

primitive actor sampling；

environment transition；

reward；

recurrent update。

Commitment opportunity

顺序：

physical transition 完成；

判断 opportunity；

event policy 输入：

post-step observation；

recurrent state；

current commitment；

sample event action；

更新 commitment；

开启新 segment。

primitive actor 下一步使用新 commitment。

JOIN

顺序：

environment creates lifecycle；

hidden=0；

commitment:

z
c
=0

immediate CREATE event；

sample initial commitment。

Temporary LEAVE

顺序：

完成当前 primitive；

close current segment ledger；

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

restore:

(h
i
	​

,z
i
c
	​

)

increment epoch；

next opportunity继续。

Terminal LEAVE

顺序：

close segment；

final reward credit；

delete lifecycle state。

4. Commitment representation
State
z
i
c
	​

∈[−1,1]
8

连续 commitment vector。

Semantics

不是：

skill label；

role；

duration label。

是：

policy-controlled temporal commitment state。

Event actions

完整 support：

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
Terminate resolution

TERMINATE 不作为 learned action。

原因：

否则引入第二 survival mechanism。

因此：

TERMINATE

仅由：

terminal LEAVE；

episode termination；

触发。

event policy:

{KEEP,RENEW(z
′
)}
5. Probability law
Event factor

Categorical:

p(e∣c)

其中：

e∈{KEEP,RENEW}
Renew mark

RENEW 时：

base:

ϵ∼Uniform(−1,1)
8

policy outputs：

μ∈R
8
σ∈[0.1,1]
8

sample：

y=μ+σϵ

transform：

z
′
=tanh(y)

density：

logp(z
′
)=logp(y)−
j
∑
	​

log(1−tanh(y
j
	​

)
2
)

保存：

y

z
′

log density。

Joint factorization

事件：

π
e
	​

(e∣o,h,z)

renew：

π
m
	​

(z
′
∣e=RENEW,o,h,z)

primitive：

π
a
	​

(a∣o,h,z)

joint:

π=π
e
	​

π
m
	​

π
a
	​

6. Actor / critic architecture
Ordinary baseline

Actor:

obs 15
 ↓
MLP 15-64-64
 ↓
GRU 64
 ↓
action head 64-32-3

参数：

约：

P
OR
	​

=18435
Dummy control

输入增加：

z
dummy
∈R
8

恒：

0

保持同 architecture。

EHC

Actor:

primitive:

obs + zc
 ↓
MLP
 ↓
GRU
 ↓
primitive head

event:

obs + hidden + zc
 ↓
event head

renew:

hidden
 ↓
mu,sigma
Capacity matching

通过减少 EHC hidden：

保证：

∣P
EHC
	​

−P
OR
	​

∣<1%

dummy、EHC、ordinary 三者 optimizer exposure 完全一致。

7. Execution and replay contract
Rollout ledger

保存：

observation；

hidden before；

commitment before；

event action；

renew latent y,z
′
；

event logprob；

primitive action；

primitive logprob；

masks；

lifecycle id；

segment id；

membership epoch；

RNG state。

Replay equality

要求：

所有 stored rows：

∣logπ
stored
	​

−logπ
recomputed
	​

∣<10
−6

包括：

event categorical；

renew density；

primitive action。

8. Credit contract
External reward unchanged

保持：

r
t
	​


不改变。

Return

普通 PPO:

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

Advantage

保持：

GAE(γ=0.99,λ=0.95)
Detach

禁止：

segment detach 改变 credit horizon。

因此：

hidden；

commitment；

均按普通 recurrent PPO graph 处理。

唯一 detach：

environment state。

如果实现改变 credit semantics，则该 source invalid。

9. Checkpoint contract

必须保存：

Model

actor；

critic；

event head；

renew head。

Optimizer

all optimizer states；

step counters。

Runtime

保存：

recurrent hidden；

commitment state；

opportunity countdown；

opportunity RNG；

membership table；

segment id；

lifecycle epoch；

masks；

collector cursor。

RNG

保存：

environment RNG；

membership RNG；

opportunity RNG；

action RNG。

Evaluation checkpoint

唯一：

update_250.pt
Resume equality

resume 后：

下一 rollout：

observation；

commitment；

action probability；

environment transition；

全部：

error<10
−6
10. Frozen experiment contract
Training

三 arms：

Ordinary

Dummy commitment

Event-held commitment

Environment

保持：

Noncalendar heterogeneous tracking G0。

Budget

每 arm：

16 env
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

IID eval 98058
heldout eval 99058

bootstrap 108058
Evaluation

每 arm：

IID deterministic 256
IID stochastic 256

heldout deterministic 256
heldout stochastic 256
11. Statistical contract
External value

Primary:

ΔU=U
EHC
	​

−U
OR
	​

Bootstrap

cluster:

base episode pair。

repetitions:

10000

CI:

percentile 95%。

Commitment metrics
Natural usage

Eligible:

所有完整 commitment segments。

要求：

P(KEEP)>0.2
P(RENEW)>0.1
Lifetime diversity

统计：

T
i
	​


要求：

CV(T)>0.25

且：

两个 duration bins：

>10%
Intervention

固定：

observation；

hidden；

environment。

替换：

z
1
	​

,z
2
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
12. Branch precedence

严格顺序：

1. INVALID_IMPLEMENTATION

条件：

replay error；

checkpoint mismatch；

probability mismatch；

lifecycle mismatch。

更新：

engineering repair only。

2. BENCHMARK_NON_IDENTIFIABLE

条件：

无法区分：

commitment；

capacity；

recurrence。

更新：

stop source。

3. ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED

条件：

Dummy ≈ EHC：

LCB(U
EHC
	​

−U
Dummy
	​

)≤0

或：

参数控制后优势消失。

更新：

temporal abstraction 降权。

4. REPRESENTATION_ONLY

条件：

EHC > ordinary，

但：

lifetime criteria fail；

intervention fail。

更新：

认为是 representation gain。

5. NO_ACCESS_THIS_BENCHMARK

条件：

ordinary、dummy、EHC 全未达到：

U≥0.78

更新：

只约束该 benchmark。

不得否定更强 MARL mission。

6. COMMITMENT_SUPPORTED

条件：

同时：

LCB(ΔU)>0.10

并：

natural use pass；

lifetime diversity pass；

intervention pass。

更新：

进入 integration review。

13. Replacement ledger
Retain

external reward；

PPO/GAE；

anonymous membership；

survivor continuity；

ordinary recurrent comparator。

Add

commitment state table；

event policy；

renew density head；

commitment ledger。

Replace

primitive-only policy：

π(a∣o,h)

替换为：

π(e,z
′
,a∣o,h,z
c
)
Delete

无。

14. Prohibited changes and handoff

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

communication module；

new credit objective。

Implementation handoff

有：

Implement EVENT_HELD_COMMITMENT_FINAL

包含：

event policy；

renew density；

commitment ledger；

replay tests；

checkpoint tests。

Experiment handoff

有：

Run EHC vs Ordinary vs Dummy
Final conclusion

该 source 当前达到：

EVENT_HELD_COMMITMENT_CODE_READY_FINAL
	​


唯一科学变量：

event-held commitment representation

保持：

external reward + PPO credit + ordinary comparator

因此最终可识别的问题是：

显式事件持有 commitment 是否比普通 recurrent hidden memory 提供不可约 temporal abstraction。

不是：

skill discovery；

hierarchy reconstruction；

intrinsic motivation；

HMASD reproduction。