1. 用户路线简报

当前目标不是证明普通 recurrent MARL 失败，而是在匿名动态成员、异步成员生命周期和变量 commitment duration 下，验证显式 temporal commitment 是否提供 ordinary recurrent policy 无法替代的能力。

本轮冻结一个最小时间机制实验：

保留现有 ordinary recurrent controller 作为匹配 baseline；

只改变一个因素：加入 policy-learned commitment representation；

保持 external reward、membership lifecycle、execution authority 和 credit contract 不变。

原因是此前 G0 已证明：

任务结构可达；

calendar/static null 不足；

shared renewal 存在压力；

但 ordinary controller 未完全访问。

因此下一步不是继续救援 G0/D0，而是直接判断 temporal commitment 是否具有不可约价值。

结果解释：

若 commitment 无增益：temporal abstraction 降权，回归更简单 recurrent explanation；

若 commitment 在匹配 direct baseline 下有效：支持继续研究 lifetime abstraction；

若 benchmark 无法识别该能力：停止该 benchmark；

所有结果均不得通过调 seed、预算、模型、reward 或 threshold 救援。

2. Correction verdict

接受当前 source：

TEMPORAL_COMMITMENT_CREDIT_LOCALIZATION_SOURCE

但完成时必须修正前一版本的双因素混合问题。

此前提出：

commitment representation；

credit localization；

同时变化，会破坏因果归因。

本轮冻结：

Primary treatment

policy-learned commitment representation

并保持：

ordinary external credit；

PPO；

return；

advantage；

action interface；

全部不变。

即：

Only change=policy representation

不改变：

credit estimator

这满足：

不同时改变 policy representation 和 temporal credit。

3. Mission-forward selected source
Selected source
LEARNED_COMMITMENT_REPRESENTATION_G0
Causal claim

加入一个 policy-learned commitment state 后：

是否能够让 agent 学习：

持续行为；

异步 commitment；

个体生命周期差异；

并在：

held-out membership；

held-out lifetime；

中产生 external task improvement。

Strongest ordinary explanation

最强简单解释：

recurrent hidden state 已经可以编码所有持续信息，commitment vector 只是额外参数容量。

因此成功必须证明：

不是：

参数增加；

memory 增加；

reward shaping；

而是：

一个显式、可干预、持续的 commitment variable 提供不可约 temporal abstraction。

Retained candidates

保持：

D — ordinary recurrent explanation

高权重。

R — representation limitation

中高权重。

T — temporal abstraction

当前目标。

C — credit limitation

合并进入后续诊断，不作为 primary branch。

原因：

本轮不改变 credit，因此无法声称 credit causality。

4. Algorithm and replacement boundary
Treatment

新增：

Commitment State

每个 active lifecycle：

z
i
c
	​

Type

连续 bounded commitment vector：

z
i
c
	​

∈[−1,1]
8
Semantics

它不是：

skill label；

role；

duration label；

task state。

它表示：

policy internal commitment memory。

Create
Genuine JOIN

初始化：

z
i
c
	​

=0
Keep

普通 physical steps：

z
i,t+1
c
	​

=f
θ
	​

(z
i,t
c
	​

,o
i
	​

,h
i
	​

)
Terminate
Terminal LEAVE

删除：

z
i
c
	​

Temporary LEAVE

冻结：

(z
i
c
	​

,h
i
	​

)
REJOIN

恢复：

(z
i
c
	​

,h
i
	​

)
Retain

保留：

primitive action;

recurrent policy;

PPO；

external reward；

anonymous membership；

survivor continuity。

Replace

替换：

当前：

h
i
	​

→action

变为：

(h
i
	​

,z
i
c
	​

)→action
Delete

无。

Forbidden additions

禁止：

skill classifier；

posterior；

intrinsic reward；

duration catalogue；

hazard；

role；

team latent。

5. Matched comparator and evidence contract
Baseline
D0 Ordinary recurrent MARL

保持：

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
Treatment
Commitment model
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
Information contract

两者完全一致：

允许：

当前 observation；

membership event；

local state；

recurrent hidden。

禁止：

future demand；

future lifetime；

identity；

role；

reward history；

oracle。

Capacity matching

Baseline 增加 dummy parameters：

保证：

∣Params
commit
	​

−Params
direct
	​

∣<1%

新增 commitment vector 的参数通过减少 actor hidden width补偿。

Environment

冻结：

horizon = 80；

membership distribution；

duration distribution；

external reward。

训练：

16 environments
320000 transitions
250 updates
1000 optimizer steps
4000 episodes
Seeds

保持：

model init 58058
ledger 68058
order 78058
action 88058

IID eval 98058
held-out eval 99058

bootstrap 108058
Evaluation

每 arm：

IID deterministic 256
IID stochastic 256
held-out deterministic 256
held-out stochastic 256
Metrics

Primary：

ΔU=U
commit
	​

−U
direct
	​


要求：

LCB
95
	​

(ΔU)>0.10

同时：

held-out：

U
commit
	​

≥0.78
Temporal-specific metrics

必须额外报告：

Commitment persistence

同一 z
c
 下：

行为稳定窗口长度。

Natural usage

不是 forced intervention。

要求：

自然 policy 使用。

Lifetime distribution

比较：

T
i
	​


是否产生自然异质分布。

6. Executable data and learning flow
Actor

Baseline:

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

Treatment:

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
Critic

保持：

V(o,h)

不读取：

commitment label；

future lifetime。

Reward

保持：

r
79
	​

=U

其他：

r
t
	​

=0
Advantage

保持：

A
t
	​

=GAE(r,V)

不改变。

Gradient path

commitment：

接收：

∇
θ
	​

L
PPO
	​


禁止：

commitment auxiliary loss；

mutual information loss；

classifier loss。

原因：

否则同时改变 objective。

Optimizer

两个 arm：

同 optimizer；

同 update count；

同 environment exposure。

7. Mutually exclusive outcomes
INVALID

条件：

checkpoint；

replay；

RNG；

lifecycle；

probability；

错误。

处理：

只修工程。

ORDINARY_SUFFICIENT

条件：

Direct baseline：

通过：

U≥0.78

并且 commitment：

无 material gain。

更新：

D ↑

T ↓

解释：

ordinary recurrence 足够。

COMMITMENT_SUPPORTED

条件：

commitment：

held-out external gain；

natural usage；

lifetime differentiation；

matched direct comparison。

更新：

T ↑

D 保留为 baseline。

允许进入下一 integration review。

但不能声称：

hierarchy superiority；

HMASD parity；

cooperation。

REPRESENTATION_ONLY

条件：

commitment 有提升，但：

gain 消失在 matched capacity control；

或只是参数增加。

更新：

T ↓

解释：

容量效果。

BENCHMARK_NOT_IDENTIFYING

条件：

无法区分：

recurrent memory；

commitment；

benchmark shortcut。

处理：

停止 benchmark。

8. Prohibitions and parked ideas
禁止

不得：

修改 G0；

rescue ordinary baseline；

改 reward；

改 threshold；

加 seed；

加 budget；

增大模型；

弱化 direct comparator。

不得加入：

intrinsic reward；

posterior；

skill labels；

role；

identity；

graph；

field；

latent；

hazard；

new critic。

Parked ideas
Temporal credit modification

保留，但不在本轮。

重新激活：

只有 commitment representation 已证明存在后，且 assignment/value mismatch 明确。

Factorized executor

保留。

重新激活：

commitment 有价值，但 executor interference 仍存在。

Applied-prefix cooperation

继续 park。

需要：

真实 multi-owner coordination conflict。

Continuous commitment marks

保留。

重新激活：

离散/低维 commitment 有效后，需要更强 generalization。

Stop condition

如果：

commitment model；

matched recurrent baseline；

natural lifetime evaluation；

无法产生不可约 external value，

则停止 temporal commitment 方向。

最终 integration 仍要求：

learned behavior；

natural execution；

intervention evidence；

heterogeneous lifetime value；

held-out external advantage；

matched direct comparison。

当前 source 只验证 temporal commitment，不自动授权完整 hierarchy。