1. Verdict
VALID_NO_ACCESS_R41A

R41A 是有效的 reduced-batch original HMASD source pilot failure。

没有发现能够改变结果解释的具体 defect：

wrapper contract：有效；

source execution path：有效；

reward flow：有效；

high/low PPO update：有效；

replay likelihood：有效；

evaluator：有效；

checkpoint semantics：有效；

exposure accounting：有效。

因此不能返回 INVALID。

2. Validity and learning-trace audit
M0 implementation validity

R41A 使用：

fresh extracted original HMASD source；

未迁移到当前 trainer；

原始 Alice-Bob environment；

原始 reward；

k=50；

nZ=2；

nz=4。

训练合同：

seed=1；

CUDA；

16 rollout environments；

episode length=100；

937 outer updates；

1,499,200 environment steps；

high/low/q_D/q_d 均完成 14,055 optimizer steps。

Replay：

error_high=0

error_low=0

error_global=0

因此：

M0=PASS

3. Result interpretation

最终：

win_final=0

并且：

final-zero=0

95% CI：

[0,0]

训练过程中：

peak win rate：

0.0125

key0/key1 peak：

0.4875/0.15

但平均：

0.03856/0.02473

更关键：

38 次 deterministic evaluation；

update 700–925 全部：

win=key0=key1=0

4. What R41A rules out

R41A 可以排除：

当前 reduced-batch original HMASD source contract 在该 exposure 下没有产生 Alice-Bob access

它排除：

“只是当前 HA-CTSE migration 破坏了 HMASD”；

“当前 trainer wrapper 导致失败”；

“R30 compatibility 层是唯一问题”。

因为执行的是原始 source tree。

5. What R41A does NOT rule out

不能推出：

HMASD 原论文结果错误；

HMASD 永远无法学习 Alice-Bob；

R30 KEEP/SET 无价值；

skill abstraction 无价值；

intrinsic mechanism 无价值。

原因：

该实验明确是：

reduced-batch pilot，不是 full reproduction。

它使用：

16 envs

而完整 source contract：

32 envs

约：

3M

environment transitions。

入口明确说明：

该 pilot 保留 optimizer update 数，但只有一半 env batch 和约一半 environment transitions，因此不是 full reproduction。

6. Unique next action

选择：

exact original 32-env, approximately 3M-step source reproduction for one access seed

不选择：

five-seed reproduction；

R30；

新 substrate；

intrinsic；

open roster。

理由：

当前唯一未关闭的关键问题：

failure 是 reduced exposure，还是 original HMASD 在当前 source 下无法 access

需要一次完整 source contract reproduction。

7. R41B exact reproduction contract
Source

必须：

fresh original HMASD source。

禁止：

current HA-CTSE trainer；

standalone R30；

wrapper migration。

Environment

保持：

Alice-Bob

原始环境。

禁止：

修改 reward；

修改 observation；

修改 horizon。

Agent/config

保持：

k=50

nZ=2

nz=4

原始 network。

Resources
Seed

唯一：

seed=1

先跑一个完整 access seed。

Environment count
32
Environment steps

约：

3,000,000
Episode
100
Optimizer exposure

恢复 original source：

包括：

high policy；

low actor；

low critic；

qD；

qd。

保持：

原 optimizer。

Evaluation

使用：

exact zero-step；

exact-final；

deterministic reset streams。

8. R41B gate
PASS_R41A_SOURCE_ACCESS

条件：

最终 deterministic evaluation：

win rate≥0.50

并且：

key0/key1：

满足 source registered threshold。

VALID_NO_ACCESS_R41A_FULL_SOURCE

条件：

M0 通过。

完整 32-env / 3M source contract 下：

win<0.50

或者：

final-zero CI 包含 0 且无 access。

9. Consequence
如果 PASS

才允许进入：

same source checkpoint→native categorical R30 KEEP/SET temporal gate

要求：

fixed-k full refresh：

vs

per-agent KEEP/SET

唯一变化：

renewal semantics

不能改变：

coordinator；

low actor；

discriminator；

reward；

environment。

如果 NO_ACCESS

唯一结论：

original HMASD access anchor is not reproduced under current source contract

下一动作：

停止：

R30 temporal decoupling；

HA-CTSE extension；

intrinsic redesign。

因为没有 positive anchor。

10. Explicit prohibited changes

禁止：

intrinsic reward 修改；

reward shaping；

environment 修改；

favorable checkpoint selection；

model size increase；

learning-rate tuning；

entropy tuning；

threshold relaxation；

R29-R40 retired route resurrection；

variable-N/open-roster；

new team latent；

new intrinsic classifier。

Final record
Verdict token
VALID_NO_ACCESS_R41A
Reusable causal conclusion
R41A proves that the original HMASD source does not obtain Alice-Bob access under reduced-batch pilot exposure, but it does not yet prove source-level impossibility.

Single next experiment
R41B: exact original 32-env ≈3M-step HMASD source reproduction, seed 1

Minimal abandonment gate

若完整 source reproduction：

win_final<0.50

则：

retire HMASD Alice-Bob as current positive anchor

Prohibited changes
No rescue by algorithm modification before source-anchor question is closed.

来源
