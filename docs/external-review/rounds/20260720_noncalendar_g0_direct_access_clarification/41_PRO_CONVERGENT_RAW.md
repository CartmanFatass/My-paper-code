1. Correction verdict

接受修正：上一轮提出的 evaluation-only D1 readout audit 不成立，应撤销。

原因：

当前 D 已经观察到此前建议新增的两个字段：

active mean (g_i-x_i)/4

target_changed

因此“同 checkpoint 加入这些字段”不会改变 actor-visible information，而只是重新读取已有输入。

若真正改变 observation width，则需要：

新 actor；

新 checkpoint；

新训练；

新 optimizer exposure。

因此不能称为 evaluation-only audit。

保留此前结论：

H 已证明结构可达；

C 已证明 calendar/static null 不足；

S 已证明 shared renewal 存在压力；

D 当前仍是 NO_ACCESS_BENCHMARK_ORDINARY_CONTROL；

不允许通过 budget、model、seed、threshold、reward 或同 G0 重跑救援 D。

2. One selected source or stop

选择：

D0_D1_CAUSAL_OBSERVATION_REFACTOR_G0

这是一个新的 bounded training source，不是 evaluation audit。

原因：

当前最大未解决问题：

NO_ACCESS
D
	​

=?

无法区分：

observation contract不足；

recurrent representation不足；

credit/optimization不足；

temporal abstraction必要。

上一轮 D1 readout 无法区分，因为输入已经存在。

新的 source 改变一个真正的 causal variable：

将当前需求误差信息从 aggregate/focal mixed observation 中拆分为 explicit causal local observation，而不是增加信息。

目标：

验证 D 失败是否来自信息组织方式，而不是信息缺失。

该 source 能区分：

D：representation/access问题；

R：recurrent/data-flow问题；

T：真正需要 temporal abstraction。

3. Exact treatment and causal reason
Single changed variable

唯一变化：

local observation factorization
D0（现有）

保留当前15维 observation：

global active means；

focal x
i
	​

；

focal g
i
	​

；

normalized error；

target_changed；

previous action；

action run length。

D1 treatment

删除 aggregate demand/error fields，只保留：

local:
x_i/2
g_i/2
(g_i-x_i)/4
target_changed
previous thrust
action run length

plus:
anonymous active-set size
anonymous pooled embedding

新增：

explicit local demand-transition encoding

定义：

e
i
	​

=(x
i
	​

/2,g
i
	​

/2,(g
i
	​

−x
i
	​

)/4,Δg
i
	​

)

其中：

Δg
i
	​

=g
i,t
	​

−g
i,t−1
	​


范围：

[−4,4]

归一化：

Δg
i
	​

/4∈[−1,1]
Why this separates candidates

它区分：

R — recurrent representation limitation

如果 D1 提升：

D 上升；

T 降低。

说明：

当前问题是 observation/data-flow，而不是 temporal abstraction。

T — genuine temporal abstraction

如果 D1 无提升：

但未来 commitment abstraction 成功：

说明：

普通 recurrent access不足，temporal abstraction可能必要。

B — benchmark/access limitation

如果 D1仍失败：

说明不是字段组织问题，而是benchmark access仍不足。

Replacement ledger

保留：

DirectPrimitiveARPolicy；

primitive action space；

recurrent state；

PPO；

external reward；

anonymous membership；

active masks。

删除：

当前D observation schema。

新增：

D1 observation encoder。

不增加：

skill；

high controller；

intrinsic；

posterior；

graph；

latent。

4. Executable data and learning flow
Actor-visible inputs

D0:

current observation
+
recurrent hidden
+
active-set context
+
earlier action prefix

D1:

new local demand-factorized observation
+
same recurrent hidden
+
same active-set context
+
same earlier action prefix
Recurrent state

保持：

GRU hidden width = 32

不重置：

JOIN;

REJOIN;

survivor.

保持：

temporary leave freeze；

terminal delete。

Action distribution

保持：

primitive AR:

π(a
i
	​

∣o
i
	​

,h
i
	​

,prefix)

动作：

{-1,0,+1}

不引入：

skill；

option；

KEEP/SET。

Reward / credit

完全保持：

terminal utility：

r
79
	​

=U

中间：

r
t
	​

=0

不改变：

GAE；

PPO；

discount；

credit。

Rollout data

新增存储：

delta_target_local

删除：

无。

保存：

observation；

action；

hidden；

prefix；

reward；

RNG。

Optimizer path

发生训练。

不是 evaluation。

两臂：

D0；

D1。

共同：

initialization；

optimizer；

exposure。

Checkpoint initialization

两个 arm：

same zero-step checkpoint。

禁止：

pretrained D；

best checkpoint。

Evaluation path

保持：

IID；

held-out；

deterministic；

stochastic。

5. Comparator, estimand and frozen contract
Comparator
D0

existing ordinary recurrent controller。

D1

same controller with observation factorization replacement。

Information authority

两者相同：

允许：

current target；

current local state；

active-set anonymous aggregation；

previous action；

recurrence。

禁止：

future duration；

future demand；

future membership；

reward history；

identity；

role。

Parameter accounting

保持：

hidden width: 32
parameter count:
within ±1%

如果参数变化超过1%，增加dummy parameters补齐。

Optimizer

保持：

Adam
lr=3e-4
gamma=0.99
GAE lambda=0.95
PPO epochs=4
gradient clip=0.5
Budget

每 arm：

16 environments
80 horizon
250 updates
320000 transitions
1000 optimizer steps
4000 episodes
Seeds

保持：

model initialization 58058
training ledger 68058
order 78058
action 88058

IID eval 98058
held-out eval 99058

bootstrap 108058
Held-out distribution

保持：

training durations:
{5,9,13}

held-out:
{5,7,9}

保持：

anonymous JOIN；

temporary leave；

REJOIN；

terminal leave。

Metrics

Primary:

ΔU=U
D1
	​

−U
D0
	​


Bootstrap：

10000 paired bootstrap
cluster=base_id
PASS thresholds

D1 must satisfy:

Held-out deterministic:

tracking >= 0.72
completion >= 0.85
utility >= 0.78

Learning gain:

LCB
95
	​

(U
D1
	​

−U
D0
	​

)>0.10

Additionally：

D1 must improve D0:

LCB
95
	​

(U
D1
	​

−U
D0
	​

)>0.10
6. Mutually exclusive result branches
INVALID_D1_OBSERVATION_CONTRACT

触发：

replay mismatch；

mask错误；

checkpoint错误；

information leakage。

处理：

只修工程。

D1_PASS_OBSERVATION_ACCESS

条件：

M0 pass；

D1 held-out utility通过；

improvement LCB > 0.10。

更新：

R 大幅下降；

D 上升；

T 降低。

结论：

当前失败主要来自 observation/data-flow。

D1_NO_GAIN

条件：

M0 pass；

D1不超过D0。

更新：

R下降；

B上升；

T保持。

说明：

不是简单 observation factorization。

D1_FAIL_WITH_VALID_ACCESS

条件：

D1仍失败；

H/C/S保持。

更新：

ordinary access仍未建立；

不进入 hierarchy；

不增加skill。

STOP

如果：

D0；

D1；

均无法建立ordinary access：

停止当前benchmark algorithm line。

不允许：

加大模型；

加seed；

加budget；

加intrinsic。

7. Minimal implementation boundary and prohibitions
Reuse

复用：

ha_ctse_process/dynamic_roster_direct.py
ha_ctse_process/variable_roster_event.py
scripts/run_clean_process_direct_access.py

保持：

PPO；

replay；

checkpoint；

lifecycle。

Add

新增：

ha_ctse_process/
    noncalendar_direct_observation_refactor.py

scripts/
    run_noncalendar_direct_observation_refactor.py

tests/
    test_noncalendar_direct_observation_refactor.py
Replace

替换：

DirectPrimitiveARPolicy observation encoder

不替换：

actor；

critic；

optimizer。

Delete

无。

Forbidden

禁止：

G0 rerun；

threshold修改；

reward修改；

seed增加；

budget增加；

model scaling；

skill；

intrinsic；

posterior；

graph；

communication；

latent；

hazard；

new critic。

8. Unselected ideas and stop conditions
Existing D read-only decomposition

Park。

原因：

当前需要训练性因果证据。

重新激活条件：

已有stored trace能直接区分representation failure。

Larger direct model

Park。

原因：

会混入capacity。

重新激活：

D1证明observation足够但capacity不足。

Direct vs commitment prototype

Park。

原因：

D access尚未建立。

重新激活：

D或D1通过。

Factorized executor B

Park。

原因：

没有证明shared executor是瓶颈。

重新激活：

temporal abstraction成立后。

Temporal abstraction T

保留。

但当前不是下一步。

重新激活：

D1失败且更强direct access仍失败。

Stop condition

如果：

D0失败；

D1失败；

两者均在严格信息合同下无access；

则停止该benchmark，不进入hierarchy。

最终integration仍要求：

learned skill；

natural execution；

intervention evidence；

heterogeneous lifetime value；

held-out external advantage；

matched direct comparison。

当前尚未满足。