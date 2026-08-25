# 裁决

[
\boxed{\texttt{CONFIRM_R51_AMDT_625_STEP_CONTRACT}}
]

不替换 R51 的环境、模型、奖励、阈值或科学路线。

指定材料已经把 `R51-AMDT-G0` 全部科学设计冻结，唯一未决项是：在 320K transitions、每个 (N) 64K transitions、16 个环境、32-step rollout 和 `PPO epochs=1` 的条件下，optimizer-step 数被误写为 3,125。

算术唯一一致的解释是：

[
16\times32=512
]

个 transitions/N-specific batch，

[
64,000/512=125
]

个 batches/N，

[
125\times5=625
]

个 N-specific batches/arm。每个 batch 只执行一次 full-batch PPO update，因此 shared policy 共 625 步；每个 specialist 125 步，五个 specialists 合计也是 625 步。3,125 步只有在每批数据重复优化五次，或者将总数据量增至 1.6M transitions/arm 时才能成立；两者都会改变已接受的因果 exposure。

指定提交中尚无 R51 环境实现或 R51 结果 JSON 可审阅；这不是证据遗漏。仓库明确规定，在本次算术澄清完成前不得实现 AMDT、登记正式实验或启动运行。

---

# 修正后的 launch-exact exposure 表

| 项目                               |                                              冻结值 |
| -------------------------------- | -----------------------------------------------: |
| Team sizes                       |                                    ({2,3,4,5,6}) |
| Arms                             | `shared_variable_N`, `fixed_N_specialist_family` |
| Environments                     |                                       16 per arm |
| Episode / rollout                |                                          32 / 32 |
| Transitions per N-specific batch |                                              512 |
| Balanced cycles                  |                                              125 |
| N-specific batches per cycle     |                                                5 |
| N-specific batches per N         |                                              125 |
| N-specific batches total per arm |                                              625 |
| Episodes per N per arm           |                                            2,000 |
| Episodes total per arm           |                                           10,000 |
| Transitions per N per arm        |                                           64,000 |
| Transitions total per arm        |                                          320,000 |
| Agent-token decisions per arm    |                                        1,280,000 |
| PPO epochs                       |                                                1 |
| Data reuse                       |                                           1 pass |
| Shared optimizer steps           |                                              625 |
| Specialist steps per model       |                                              125 |
| Specialist aggregate steps       |                                              625 |
| Zero-step evaluation             |                               128 episodes/N/arm |
| Exact-final evaluation           |                               128 episodes/N/arm |
| Evaluation total                 |                      640 episodes/arm/checkpoint |
| Expected wall-clock envelope     |                         unchanged: 15–25 minutes |

这里应把此前含混的 `outer updates=625` 精确定义为：

```text
125 balanced cycles
× 5 sequential N-specific rollout/update units
= 625 N-specific outer updates
```

每个 N-specific update 执行：

1. 为 shared arm 和对应 specialist arm生成配对的 16 个 32-step episodes；
2. 使用同一 reset schedule、agent/entity permutations、external AR order 和 categorical random streams；
3. 分别计算一次 PPO loss；
4. shared model执行一次 optimizer step；
5. 当前 (N) 的 specialist执行一次 optimizer step；
6. 该批数据不再复用。

五个 (N) 在每个 balanced cycle 中的处理顺序由已注册的固定 RNG 决定，并在两臂中一致。五个 N buckets 可以顺序执行；两臂也可通过预生成并重放随机账本顺序执行，所以并发环境数不必超过 16。该解释正是 tracked clarification 推荐的 125-cycle、625-step合同。

---

# 唯一需要修改的 M0 条款

原始 M0 中这一项：

```text
exact 320K transitions/arm,
64K/N,
3,125 optimizer steps/arm
```

替换为：

```text
exact 320K transitions/arm
exact 64K transitions/N/arm
exact 125 N-specific batches/N/arm
exact 625 N-specific batches/arm
exact 125 balanced cycles
exact 625 shared optimizer steps
exact 125 optimizer steps for each specialist
exact 625 aggregate specialist optimizer steps
exact PPO epochs = 1
no minibatch-induced extra optimizer steps
no repeated optimization of a collected batch
```

原始 raw response 中把 320K、64K/N、2,000 episodes/N、625 outer updates和 `PPO epochs=1` 与 `3,125/625/3,125` optimizer counts同时登记，正是需要修正的唯一内部矛盾。

---

# 全部其他合同保持不变

## 环境合同不变

唯一环境仍是 **Anonymous Maintenance–Dispatch Task**：

* (N\in{2,3,4,5,6})，episode 内 membership 固定；
* (P_N=\lfloor N/2\rfloor) 个 persistent stations；
* (D_N=N-P_N) 个 concurrent dispatch jobs；
* 32-step episode；
* 三个短期 job waves；
* station 是长时责任，job 是短时责任；
* one-hop assignment transition；
* 只有 episode 最后一步的完整成功产生共享奖励 1；
* 无中间奖励、进度奖励、角色奖励、team-size reward、shaping 或 intrinsic reward。

## 模型与概率合同不变

仍采用原注册的小型 N-independent set-pointer recurrent actor-critic：

```text
member encoder: 6 -> 32 -> 32
entity encoder: 7 -> 32 -> 32
GRU hidden: 32
query MLP: 128 -> 64 -> 32
entity key: 33 -> 32
critic: pooled state -> 64 -> 1
parameter count < 35K
```

继续使用：

* anonymous homogeneous shared parameters；
* 外生 active-agent AR order；
* active-entity pointer action；
* applied-prefix planned-assignment counts；
* 无 persistent agent ID、slot embedding、learned order或角色标签；
* teacher-forced replay误差 (\le10^{-6})；
* 无 (K^N) 枚举；
* 无 mandatory agent-agent (N\times N) tensor。

## PPO 与 credit 合同不变

继续使用：

[
L_{\pi,t}
=========

-\frac1N
\sum_i
\min!\left[
\rho_{i,t}A_t,,
\operatorname{clip}(\rho_{i,t},0.8,1.2)A_t
\right],
]

以及：

```text
gamma               0.99
GAE lambda           0.95
learning rate        3e-4
PPO epochs           1
entropy coefficient  0.01
value coefficient    0.5
gradient clip        0.5
```

每个 (N) 的 advantages 分开标准化；大团队不能仅凭 token 更多获得更高 loss 权重。唯一训练信号仍是终局环境回报。

## Seeds、evaluation 与 aggregation 不变

```text
model/init seed          51051
training reset seed      61051
order/action RNG seed    71051
evaluation reset seed    81051
bootstrap seed           91051
```

继续执行 zero-step 与 exact-final 的每 (N) 128 个 deterministic episodes；shared 与 specialist使用相同 reset、agent order和entity presentation streams。Macro 结果仍先在每个 (N) 内计算，再对五个 (N) 等权平均，不按 agent tokens 或 (N) 加权。

15–25 分钟保留为非科学性的运行规划范围；实际时间应记录到结果 JSON，但不参与 PASS/FAIL。

---

# 原始科学门槛保持不变

## M1：specialist ordinary-policy access

仍要求对每个 (N)：

[
S_N^{spec}\ge0.60,
]

同时：

[
\bar S^{spec}\ge0.70.
]

每个 (N) 的 final-minus-zero paired bootstrap必须满足：

[
\operatorname{LCB}*{95}
\left[
S*{N,\mathrm{final}}^{spec}
---------------------------

S_{N,\mathrm{zero}}^{spec}
\right]>0.20.
]

每个 (N) 的四个连续32-episode blocks中，至少三个必须达到：

[
S_{N,\mathrm{block}}^{spec}\ge0.50.
]

这些门槛没有隐含“每批必须优化五次”的要求。它们评价的是在冻结数据和优化合同下是否形成环境访问；目前没有任何 R51 结果能证明需要重复使用同一批数据。

## M2：shared cross-(N) learning

仍要求：

[
S_N^{shared}\ge0.50
\quad\forall N,
]

[
\bar S^{shared}\ge0.65,
]

[
\min_N
\frac{S_N^{shared}}
{S_N^{spec}+10^{-8}}
\ge0.75,
]

[
\frac{\bar S^{shared}}
{\bar S^{spec}+10^{-8}}
\ge0.85,
]

[
\operatorname{LCB}_{95}
\left[
\frac15\sum_N
(S_N^{shared}-S_N^{spec})
\right]>-0.10,
]

以及：

[
\operatorname{LCB}*{95}
\left[
\bar S*{\mathrm{final}}^{shared}
--------------------------------

\bar S_{\mathrm{zero}}^{shared}
\right]>0.25.
]

不修改任何成功率、比率、置信区间或 noninferiority threshold。

---

# 可复用的因果结论

[
\boxed{
\text{environment-transition exposure}
\neq
\text{optimizer-step exposure}
}
]

在按 team size 分桶的 on-policy variable-(N) 实验中，若：

* 每个 bucket 包含 16 个32-step episodes；
* 每个 (N) 有64K transitions；
* PPO epoch为1；
* 每个 collected bucket只执行一次 full-batch update；

则：

[
\boxed{
125\text{ updates/N}
\quad\text{和}\quad
625\text{ total shared updates}
}
]

是数据合同直接决定的数量。

将同一批数据优化五次不是算术修复，而是新的优化机制：

[
\texttt{PPO epochs}=5.
]

因此它会混淆：

[
\text{跨-}N\text{共享能力}
]

与：

[
\text{额外数据复用带来的优化收益}.
]

R51 的因果对象是“一套匿名策略能否在相同总数据暴露下学习多个真实 team-size tasks”，所以必须保留一次数据使用和 625-step合同。

---

# 唯一下一条可证伪路线

[
\boxed{\texttt{R51-AMDT-G0}}
]

下一动作只有：

> 按上述625-step合同实现 AMDT、shared set-pointer policy、五个 capacity-matched specialists、完整 replay/mask账本和单次 paired正式运行。

不得在实现前增加 smoke-layer科学实验、额外环境、替代模型、额外 seed 或新的 access threshold。

---

# 最小 abandonment gate

## 1. 实现无效

```text
INVALID_R51_AMDT_WIRING
```

触发条件包括：

* transition或终局reward不符合合同；
* 出现中间reward、shaping或intrinsic；
* N schedule、transition或optimizer counts不精确；
* sample/replay误差 (>10^{-6})；
* member/entity mask、AR order或prefix错误；
* shared/specialist配对不一致；
* checkpoint不是 exact-final；
* 出现额外数据复用或 optimizer steps。

唯一动作：

> 只修复明确定位的实现缺陷，并按同一625-step合同重跑。

## 2. 环境无访问

[
M0\land\neg M1
]

产生：

```text
NO_ACCESS_R51_AMDT_SPECIALISTS
```

唯一动作：

> 永久退休 AMDT 的精确 dynamics、32-step horizon和reset contract，并隔离全部 shared结果。

禁止增加 steps、PPO epochs、seed、模型宽度、threshold或reward。

## 3. Shared variable-(N) 学习失败

[
M0\land M1\land\neg M2
]

产生：

```text
VALID_FAIL_R51_SHARED_VARIABLE_N
```

唯一动作：

> 永久退休该精确 shared set-pointer MAPPO contract，并停止当前 variable-(N) learning line，进入一次架构/优化失败审查。

不得把 `PPO epochs=1` 改成5作为结果后救援。

## 4. PASS

[
M0\land M1\land M2
]

产生：

```text
PASS_R51_AMDT_VARIABLE_N
```

唯一动作：

> 在同一个 AMDT、相同 ordinary policy和相同外部奖励上，注册一次 within-episode **exogenous** join/leave 与 membership-censoring gate。

仍不授权 skill latent、KEEP/SET、variable lifetime、intrinsic reward、S7/UAV transfer或论文 novelty。原始 raw response对这些结果分支和后续边界的规定保持不变。

---

# 最终决定

[
\boxed{
\begin{aligned}
&\texttt{CONFIRM_R51_AMDT_625_STEP_CONTRACT};\
&125\text{ balanced cycles};\
&625\text{ N-specific rollout/update units};\
&625\text{ shared optimizer steps};\
&125\text{ optimizer steps per specialist};\
&625\text{ aggregate specialist steps};\
&320K\text{ transitions/arm};\
&64K\text{ transitions/N/arm};\
&\texttt{PPO epochs}=1;\quad\text{no data reuse};\
&\text{环境、模型、奖励、seeds、evaluation、M0--M2阈值、}\
&\text{结果分支和no-rescue条款全部保持不变。}
\end{aligned}
}
]
