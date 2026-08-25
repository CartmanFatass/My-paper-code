# 1. R38 validity verdict

## `VALID_FAIL_R38_CTS_ACCESS`

R38 CTS access gate失败有效，不存在改变 estimand 的 M0 缺陷。

我审计了：

* registered access contract；
* retry2 result；
* learner configuration；
* reward boundary；
* random comparator；
* evaluation branch。

结论：

[
\boxed{
\text{R38 failed as an access substrate, not as an implementation}
}
]

---

## M0 validity

R38 retry2：

* fresh neutral zero-step checkpoint；
* 320,000 environment steps；
* 16 environments；
* rollout 200；
* 100 outer/low updates；
* CUDA；
* zero high updates；
* zero process updates；
* zero intrinsic path。

M0：

* high rows = 0；
* process rows = 0；
* intrinsic field = 0；
* reward semantics valid；
* terminal semantics valid；
* paired reset order exact。

因此不能改判：

[
INVALID
]

---

## M1 access failure

MAPPO：

[
short=0/256
]

[
long=2/256
]

[
full=0/256
]

[
reward=0
]

random：

[
short=0/256
]

[
long=0/256
]

[
full=0/256
]

[
reward=0
]

paired：

[
full=[0,0,0]
]

因此：

[
\boxed{
\text{ordinary recurrent MAPPO cannot establish CTS access floor}
}
]

---

# 2. Reusable causal conclusion

R35-R38 的共同结论：

[
\boxed{
\text{当前自建 sparse toy access program 不能作为 HA-CTSE 算法比较基准}
}
]

---

## R35

constant-code MAPPO 与 reward-pure R30：

[
access=0
]

说明：

不是 skill/lifetime 的直接失败。

---

## R36

joint-position novelty：

coverage：

[
3.855204\times
]

但：

[
access=0
]

说明：

[
\text{undirected visitation}
\neq
\text{task access}
]

---

## R37

actor-visible identity：

产生：

[
10/64
]

collection。

masked：

[
0
]

说明：

hidden identity 是真实 bottleneck。

但：

cycle success：

[
0.01953125
]

低于：

[
0.05
]

可靠性门槛。

---

## R38

CTS 去除了：

* Alice-Bob 特殊 identity；
* observation ambiguity；
* intrinsic；
* hierarchy；
* skill。

仍：

[
full=0
]

因此：

最终结论：

[
\boxed{
\text{问题不是某个 skill mechanism，而是 custom sparse substrate 没有建立可信 access anchor}
}
]

---

# 3. Retire or retain custom sparse-toy access program

## RETIRE

退休：

[
\boxed{
\text{custom sparse-toy access program}
}
]

包括：

* Alice-Bob；
* CTS；
* R36 access novelty；
* R37 identity repair；
* 继续局部修补 toy。

原因：

继续修补会把：

[
benchmark\ design
]

变成：

[
algorithm\ tuning
]

---

# 4. Exactly one selected route

## Route A — Return to S7-S1

选择：

[
\boxed{A}
]

---

原因：

当前真正目标：

[
HMASD/HA\text{-}CTSE
]

不是：

开发一个更好的 sparse toy。

S7-S1 已经提供：

[
\text{positive access anchor}
]

历史结果：

约：

[
0.8M
]

steps 达到：

[
coverage\approx0.9639
]

因此：

S7 是已有 substrate。

---

# 5. Why other routes are rejected

## Route B：Public benchmark

拒绝。

原因：

它提供 external baseline，但引入：

* 新环境；
* 新任务语义；
* 新 integration uncertainty。

当前缺失不是 benchmark 数量，而是：

[
\text{与 HMASD 目标一致的正向 substrate}
]

---

## Route C：R27 forced-capacity

拒绝。

R27：

证明：

[
forced\ skill
\rightarrow
conditional\ behavior
]

存在。

但 R29-R34 已关闭：

* action density；
* observational effect；
* IFEPG；
* roster fitting；
* hindsight relabel。

继续找新的 skill diagnostic 会重复：

[
capacity
\not\Rightarrow
transport
]

---

# 6. One falsifiable causal edge

## R39-S7 Access Calibration

唯一 causal edge：

[
\boxed{
\text{ordinary recurrent MAPPO on native S7}
\rightarrow
\text{positive cooperative service access}
}
]

不是：

[
skill
\rightarrow
success
]

也不是：

[
hierarchy
\rightarrow
performance
]

---

# 7. Lowest valid comparator/baseline level

最低 baseline：

## Native S7 recurrent MAPPO

条件：

* no skill；
* no high policy；
* no intrinsic；
* no lifetime；
* no scheduler。

---

Actor：

[
\pi(a_i|o_i)
]

---

Critic：

centralized：

[
V(s)
]

---

Reward：

S7 原生 reward。

---

# 8. Smallest evidence-bearing implementation and experiment

## Environment

使用：

[
S7-S1
]

native environment。

禁止修改：

* observation；
* reward；
* termination；
* dynamics。

---

## Arm

单 arm：

```text
Native recurrent MAPPO
```

---

## Budget

固定：

```text
seed:
40031

num_envs:
16

steps:
800000

rollout:
200

updates:
250

epochs:
5

sequence_length:
20
```

---

## Evaluation

64 stochastic episodes。

指标：

### Service access

使用 S7 native service metric。

### Success

使用原 S7 service completion。

---

## Bootstrap

10000：

unit：

episode。

seed：

60031。

---

# 9. Exact abandonment gate and prohibited rescue changes

## M0 validity

必须：

* S7 untouched；
* reward untouched；
* observation untouched；
* no skill；
* no intrinsic；
* no hierarchy。

失败：

## INVALID

唯一动作：

修 implementation wiring。

---

## M1 access floor

ordinary MAPPO：

要求：

service metric：

[
\ge0.5
]

---

## M2 repeatability

64 episodes：

至少：

[
10
]

episodes：

service > 0。

bootstrap：

95% CI lower > 0。

---

## PASS

条件：

M0-M2 全通过。

唯一下一动作：

注册：

[
fixed/shared-k
]

vs

[
per-agent-lifetime
]

gate。

---

## VALID_FAIL_ACCESS

M0通过但 M1/M2失败。

唯一动作：

停止继续 HA-CTSE algorithm comparison。

---

## 禁止 rescue

禁止：

* 继续 CTS；
* 新 sparse toy；
* intrinsic；
* skill；
* latent；
* scheduler；
* reward shaping；
* threshold lowering；
* seed expansion。

---

# 10. Strongest objection

## Objection

S7 更复杂，失败可能来自 integration，而不是 substrate。

---

## 是否改变决定？

不改变。

原因：

当前最大风险：

[
\text{继续制造不可校准 toy}
]

而不是：

[
\text{S7复杂}
]

S7 的价值：

不是简单 benchmark。

而是：

[
\text{existing positive HMASD substrate}
]

它允许重新回答：

[
\text{HA-CTSE temporal abstraction 是否有效}
]

而不是继续回答：

[
\text{如何让人工设计 sparse task 可学习}
]

---

# Final decision

[
\boxed{
R38=VALID_FAIL_CTS_ACCESS
}
]

[
\boxed{
\text{Retire custom sparse-toy access program}
}
]

唯一路线：

[
\boxed{
R39:
\text{Native S7-S1 recurrent MAPPO access calibration}
}
]

研究顺序：

[
\boxed{
\text{positive substrate}
\rightarrow
\text{ordinary access}
\rightarrow
\text{temporal abstraction}
\rightarrow
\text{HA-CTSE}
}
]

