# 裁决

[
\boxed{\texttt{VALID_FAIL_R40_ACCESS}\ \text{维持}}
]

[
\boxed{\texttt{MODIFY R41}}
]

唯一保留的路线是：

[
\boxed{
\begin{aligned}
&\text{固定官方 HMASD 源码与官方 Alice_and_Bob 环境}\
&\rightarrow
\text{完整复现标准 fixed-}k\text{ HMASD 正锚点}\
&\rightarrow
\text{仅在复现 PASS 后，进行同基底 native-categorical R30 比较}
\end{aligned}
}
]

这里的修改不是改变路线方向，而是把“根据论文重建环境并使用当前仓库的 native HMASD”改为：

> **直接固定并运行官方 HMASD 实现；当前仓库只提供外部封装、审计计数和结果导出，不重新解释算法或环境。**

---

# 一、R40 validity verdict

没有发现会改变 `VALID_FAIL_R40_ACCESS` 的实现或估计器缺陷。

R40 的结果 JSON 明确记录：

* M0 通过；
* 200,000 个环境步；
* 500 个 outer updates；
* 2,500 个 low optimizer steps；
* low replay 最大误差 (2.384\times10^{-7})；
* high optimizer steps 为 0；
* MAPPO 平均回报 (-52.3922)；
* uniform random 为 (-52.5873)；
* paired difference 为 (0.1950)，95% 区间为 ([-1.4484,1.9034])；
* 四个评估块均未超过预注册的 (-35) 门槛。

分析器逐项检查了：

* exact manifest；
* PettingZoo 版本；
* final checkpoint；
* 500 行连续 update；
* 2,500 次 low optimizer exposure；
* actor/critic 均收到非零梯度；
* recurrent likelihood replay 不超过 (10^{-6})；
* high、process、R28、R29、R31、team/prototype discriminator 等禁止路径全部为零；
* 256 个固定 reset episodes；
* paired bootstrap 使用同一批 reset seeds。

状态分支也完全遵守预注册规则：M0 通过但 M1 或 M2 未通过，结论必须是 `VALID_FAIL_R40_ACCESS`，而不是 `INVALID` 或自动增加训练量。

因此，下列替代意见都**不是** invalidation：

* 换成 continuous actions；
* 增大 horizon；
* 使用另一个 PPO 学习率；
* 增加环境步或种子；
* 改 return floor；
* 更换 simple_spread 版本。

它们只会定义新的实验，而不是修复当前实验。

R40 的严格可复用结论是：

[
\boxed{
\text{在冻结的 PettingZoo simple_spread-v3、Discrete(5)、}
200K\text{ recurrent MAPPO 合同下，}
\text{学习器没有建立优于随机策略的可靠 cooperative access。}
}
]

它不证明 MAPPO 或 simple_spread 一般不可学习，更不证明 HMASD、R30 或可变技能寿命无效。

---

# 二、R35–R40 的跨轮次因果结论

## 已验证的机制事实

1. **R27：低层条件控制容量存在。**
   持续强制 (z_i) 可以造成持久行为和局部环境 effect；缺口不是低层 actor 完全看不见技能。

2. **R30：固定检查、KEEP/SET、working-roster replay 的时间结构已实现。**
   但其效果比较没有完成，不能把“实现存在”当成“异步 lifetime 有效”。

3. **R39：joint policy capacity、reward timing 和 prefix replay 已关闭。**
   high-32 policy 在 exact supervision 下的最差正确-roster mass 为 `0.999487`；自然采样中正确 roster 的 block return 和标准化 actor weight 都明显高于错误 roster。模型可表达、奖励方向正确、stored-prefix replay 也正确。

4. **R40：standalone recurrent MAPPO 的基本优化通路有效执行。**
   actor、critic、GAE、sequence replay 和 optimizer exposure 都真实存在；失败不能解释成“训练根本没发生”。

## 已关闭的 instrumentation failure

R39 的早期运行曾发现：

* interleaved environments 的 return 被错误跨流计算；
* 注册的多个 PPO epochs 没有真正执行；
* clipped Normal 的 likelihood 与执行动作不一致；
* direct-state lane 的 manifest 被配置规范化改写。

这些均被判为 `INVALID` 后在不改变科学阈值的条件下修复；后续有效失败不能再归因于这些已修复问题。

## 仍未关闭的优化与容量问题

目前尚未证明：

[
\text{自然 skill semantics}
\rightarrow
\text{可学习 joint composition}
\rightarrow
\text{稳定 cooperative access}.
]

尤其是：

[
\boxed{
\text{policy 可表达正确 joint roster}
+
\text{正确 roster 获得正确 reward}
\not\Rightarrow
\text{当前 sampled on-policy learner 能学会它}
}
]

这既可能涉及高层 credit variance，也可能涉及当前自定义 substrate 的访问结构。但经过 R35–R40 后，继续换一个方便的 toy 已无法区分这两者。

## 可复用的负结论

[
\boxed{
\begin{aligned}
&\text{扩大状态覆盖}\not\Rightarrow\text{任务访问};\
&\text{暴露任务身份}\not\Rightarrow\text{可靠协调};\
&\text{固定 primitive}\not\Rightarrow\text{高层可学习};\
&\text{exact policy capacity}\not\Rightarrow\text{sampled joint credit 可学习};\
&\text{公开 benchmark}\not\Rightarrow\text{当前 learner 自动得到正锚点}.
\end{aligned}
}
]

因此，R35–R40 的 custom-substrate search loop 应当关闭，而不是继续寻找第六个“看起来应该容易”的环境。仓库的跨轮次复盘也已将官方 HMASD Alice_and_Bob 识别为唯一具有同算法族已发表正证据、但仍需精确复现的候选。

---

# 三、为什么是 `MODIFY R41`，而不是直接 `ACCEPT`

路线方向正确，但“exact reproduction”必须修改为**源码级权威固定**。

官方仓库明确把其 `HMASD/` 子目录称为 HMASD 的官方实现，并给出了 Alice_and_Bob 的正式训练入口。

当前私有仓库不能被当成“unchanged paper HMASD”：

* `config_r39_native_hmasd_toy.py` 使用的是 `two_timescale_role_free_actions`；
* 连续二维动作；
* (k=5)；
* 四个固定 axis primitives；
* (q_D/q_d) 训练和 reward 全部关闭。
* 当前 native trainer 的 scenario router 也没有官方 Alice_and_Bob 入口，而是 base、belief、progress、energy 和自定义 role-free toy。
* 当前 `hmasd/networks.py` 包含仓库后续加入的 agent-specific query、独立 value heads、数值裁剪和 stored-prefix 修正；这些可能是合理修复，但已经不再是未经修改的官方 source implementation。

因此，R41 应修改为：

```text
官方 VOMASD/HMASD commit ff05a1f2...
+ 官方 Alice_and_Bob0
+ 官方 train_alice_and_bob.sh
+ 只读审计/结果导出 wrapper
```

禁止先把官方任务“移植”到当前 trainer 再声称完成复现。移植本身会同时引入环境 adapter、buffer、概率、critic、归一化和更新顺序差异。

---

# 四、R41 exact reproduction boundary

## 4.1 权威源码

唯一执行权威：

```text
repository: LucasCJYSDL/VOMASD
subtree:    HMASD/
commit:     ff05a1f2bebd1ed8c1a49afc424bac8905eb4de3
```

官方源文件保持内容哈希不变。允许的新增内容只能位于其外部：

* launch wrapper；
* optimizer/update counters；
* pre-update likelihood audit；
* zero-step/final evaluator；
* final result JSON；
* source/runtime manifest。

兼容性补丁若必须修改官方 source 文件，则先判 `INVALID`；只有证明固定输入上的环境 transition、action log-probability、reward 和梯度完全等价后，才能作为纯兼容修复。

官方依赖文件包括 `gym==0.12.4` 等旧版本依赖，因此应使用隔离环境并完整记录 Python、PyTorch、CUDA、GPU 和所有包版本。官方 requirements 未固定 PyTorch 版本，这一不确定性必须出现在 manifest 中，不能被隐去。

---

## 4.2 官方环境合同

官方环境不是当前仓库的任何 Alice–Bob 变体。

精确合同是：

* 两个 agent；
* `Discrete(5)`：

  * 0/1/2/3 为四个方向；
  * 4 未进入任何移动分支，等价于 no-op；
* 内部数组尺寸 `10×10`；
* 最外圈为墙，因此可行走内部区域为 `8×8`；
* 两个按钮/keys 位于顶部内侧角；
* 两个 diamonds/goals 位于底部内侧角；
* 两个 agent 从内部 64 个格子中无放回随机初始化；
* episode limit 为 100。

这里解释了论文和代码表面的尺寸差异：论文称其为“被墙包围的 (8\times8) grid world”，官方实现用 (10\times10) 数组存储外墙和内部 (8\times8) 活动区。不能把论文中的“8×8”重新实现成总数组 8×8，否则会得到 6×6 活动区。([NIPS 会议论文][1])

局部 observation 必须是：

[
o_i=
[
\text{自身周围 }3\times3\text{ occupancy},
\text{自身二维绝对位置}
]
\in\mathbb R^{11}.
]

代码虽然计算了 teammate、button 和 goal 的相对距离，但最终没有把它们拼入 observation。全局 state 是整个 (10\times10) occupancy 展平后的 100 维向量。

reward 与 termination 必须保持：

[
r_t=
\begin{cases}
1,&\text{两个 diamonds 均被收集};\
0,&\text{否则}.
\end{cases}
]

一个 diamond 只有在同色 button 正被任一 agent 占据时才能被另一个或同一个 agent 激活；两个 goal 均完成时共享奖励 1 并立即终止，否则在第 100 步超时终止。

不允许添加：

* distance reward；
* 单个 key/diamond reward；
* contact reward；
* time penalty；
* role label；
* task phase；
* current target identity；
* curriculum；
* alternative reset distribution。

---

## 4.3 标准 fixed-(k) HMASD

联合高层策略保持：

[
\pi_h(Z,z_1,z_2\mid s,o)
========================

\pi_h(Z\mid s,o)
\pi_h(z_1\mid s,o,Z)
\pi_h(z_2\mid s,o,Z,z_1).
]

每 (k=50) 步重新采样：

[
Z\in{0,1},\qquad
z_i\in{0,1,2,3}.
]

低层 actor 保持：

[
\pi_l(a_i\mid o_i,z_i),
]

集中式 low critic 保持：

[
V_l(s,Z).
]

论文明确规定 high coordinator 每 (k) 步先选 team skill，再顺序分配 individual skills；低层 actor 只读取局部 observation 与 individual skill，critic 读取 global state 与 team skill。([NIPS 会议论文][1])

high reward 是固定 50 步内的外部回报和：

[
r_\tau^h
========

\sum_{p=0}^{49}r_{\tau k+p}^{env}.
]

low reward 必须精确为：

[
r_{i,t}^{l}
===========

\lambda_e r_t^{env}
+
\lambda_D\log q_D(Z\mid s_{t+1})
+
\lambda_d\log q_d(z_i\mid o_{i,t+1},Z),
]

其中 Alice_and_Bob 的系数为：

[
\lambda_e=0,\qquad
\lambda_D=0.1,\qquad
\lambda_d=0.2.
]

这意味着在该官方 case study 中，外部奖励训练 high coordinator，但**不直接进入 low reward**；低层技能完全通过原始 (q_D/q_d) pressure 形成。该看似反直觉的设置是论文和官方脚本的真实合同，不能“修正”为 (\lambda_e>0)。([NIPS 会议论文][1])

两个 discriminator 均按官方 categorical cross-entropy 训练：

[
-\log q_D(Z\mid s)
------------------

\sum_i\log q_d(z_i\mid o_i,Z).
]

官方 runner 每步计算这两个 intrinsic component，并用上述权重形成 low rollout reward。 ([NIPS 会议论文][1])

本次允许 (q_D/q_d) 的范围非常窄：

> 它们只是冻结的论文算法组成部分，用于建立 source anchor；这不是对 R24、R31 或旧 (q_D/q_d) 改造路线的重新开放。

---

## 4.4 初始化、网络与优化曝光

官方脚本固定：

* seeds `1..5`；
* 32 rollout environments；
* episode length 100；
* declared `num_env_steps=3,000,000`；
* (k=50)；
* (n_Z=2,n_z=4)；
* hidden size 64；
* learning rate (5\times10^{-4})；
* high/low PPO epochs 15；
* discriminator epochs 15；
* one minibatch；
* ValueNorm；
* GAE (\lambda=0.95)；
* (\gamma=0.99)；
* high entropy coefficient 0.1；
* low entropy coefficient 0.01；
* 100 evaluation episodes。

官方 runner 使用：

[
\left\lfloor
\frac{3,000,000}{100\cdot32}
\right\rfloor
=============

937
]

个 outer updates，所以每个 seed 的实际训练 exposure 是：

[
937\cdot100\cdot32
==================

2,998,400
]

个环境 transition，而不是通过额外 partial rollout 补足整 3M。官方 runner 的 outer-loop 计算就是整数除法。

每个 seed 的 optimizer exposure 必须精确为：

| 优化器                             | optimizer steps |
| ------------------------------- | --------------: |
| high MAT policy/value optimizer |          14,055 |
| low actor optimizer             |          14,055 |
| low critic optimizer            |          14,055 |
| team discriminator (q_D)        |          14,055 |
| individual discriminator (q_d)  |          14,055 |

因为每个 outer update 对每个路径执行 15 epochs × 1 minibatch。官方 high trainer、low trainer 和 discriminator trainer都明确按该循环更新。

每个 seed 共计 70,275 次 `optimizer.step()`；五个 seed 共计 351,375 次。必须分别报告这些计数，不能只报告 nominal environment steps。

每个 seed 从独立 fresh random initialization 开始。官方 shell 不加载 `model_dir`，训练脚本按 seed 设置 Python、NumPy、Torch 和 CUDA RNG。

---

## 4.5 Checkpoint 与 evaluation

不得使用：

* 当前私有仓库 checkpoint；
* R39 checkpoint；
* historical S7 checkpoint；
* exact-supervision checkpoint；
* best checkpoint；
* early stop。

必须保存官方 runner 的 exact final checkpoint，包括：

* high policy；
* low actor；
* low critic；
* low ValueNorm；
* team discriminator；
* individual discriminator；
* optimizer states；
* runtime manifest。

官方 runner 本来就在最后一个 outer update 保存模型；现有 save path 包含 high policy、low actor/critic/ValueNorm 和 discriminator。

科学决策使用 exact final checkpoint 的 100-episode deterministic evaluation：

* one eval thread；
* high skill deterministic；
* low action deterministic；
* win rate；
* key0 rate；
* key1 rate；
* average episode steps。

这些是官方 evaluator 的原生语义。

---

# 五、最小 abandonment gate

## `R41-OFFICIAL-HMASD-ALICE-BOB-ANCHOR`

这不是一条 five-arm sweep，而是**一个五 seed 的单一官方复现合同**。官方论文报告五 seed 的均值和方差，官方 launch script 也明确执行 seeds 1–5；单个 seed 的失败不足以形成有效 abandonment，特别是论文自己承认 HMASD 存在较高运行方差。([NIPS 会议论文][1])

因此，最小有效科学运行是：

```text
official source commit  ff05a1f2...
training seeds          1,2,3,4,5
rollout envs            32 per seed
episode length          100
actual env steps        2,998,400 per seed
outer updates           937 per seed
high PPO steps          14,055 per seed
low actor steps         14,055 per seed
low critic steps        14,055 per seed
q_D steps               14,055 per seed
q_d steps               14,055 per seed
final eval              100 deterministic episodes per seed
```

## Comparator

唯一 comparator 是：

[
\boxed{\text{同 seed、同网络的 zero-step official HMASD checkpoint}}
]

每个 seed 的 zero-step 与 final checkpoint 使用相同的 100 个环境 reset 流和同一 deterministic evaluator。

不重新训练 MAPPO、MAT 或 MASER；那会把一个 source-anchor gate 扩大成新的 benchmark suite。论文中的 baseline 曲线只作为历史参考。

## M0：实现有效性

必须全部满足：

1. 官方 subtree 文件内容与固定 SHA 一致；
2. 环境 shape 精确为：

   * agents 2；
   * obs 11；
   * state 100；
   * actions 5；
   * horizon 100；
3. 所有 paper/script 参数精确一致；
4. seeds 恰好为 1–5；
5. 每个 seed 恰好 937 outer updates 和上述 optimizer counts；
6. high、low、(q_D)、(q_d) 均有有限非零梯度；
7. (\lambda_e=0,\lambda_D=0.1,\lambda_d=0.2)；
8. high reward 只包含环境奖励；
9. 无 shaping、无额外 intrinsic、无 current-repo process path；
10. zero-step 和 final 都使用 exact deterministic official evaluator；
11. final checkpoint 完整、有限、非 best-selected；
12. 只读 replay audit 在首次优化前满足：
    [
    \max|\log p_{\rm replay}-\log p_{\rm stored}|\le10^{-6}.
    ]

任一失败：

```text
INVALID_R41_HMASD_ALICE_BOB_REPRODUCTION
```

唯一下一动作是修复被明确定位的源码同步、wrapper、计数、checkpoint 或 evaluator 缺陷，然后原样重跑。不得改变科学门槛。

## M1：绝对正锚点

令 (W_s^F) 为 seed (s) 的 final 100-episode win rate。

要求：

[
\frac{1}{5}\sum_{s=1}^{5}W_s^F\ge0.80,
]

并且预注册 warm-start seed：

[
W_1^F\ge0.80.
]

Seed 1 被事先指定，是为了避免结果出来后从五个 seed 中挑选最佳 checkpoint。

## M2：学习效应与重复性

要求同时满足：

[
#{s:W_s^F\ge0.70}\ge3,
]

以及以 seed 为 cluster、10,000 次 bootstrap、固定 seed `61041` 计算：

[
\operatorname{LCB}_{95}
\left[
\overline{W^F-W^0}
\right]

> 0.50,
> ]

其中 (W_s^0) 是同 seed zero-step comparator 的 win rate。

这些门槛是为“存在强而可重复的 fixed-(k) positive anchor”预注册的保守门槛，不声称是从论文图中精确读取的 final ordinate。论文只给出了曲线和五 seed 均值/方差，没有给 Alice_and_Bob 的最终数值表。([NIPS 会议论文][1])

## 分支

### `PASS_R41_HMASD_ALICE_BOB_REPRODUCTION`

条件：

[
M0\land M1\land M2.
]

允许结论：

> 官方 fixed-(k) HMASD 在官方 Alice_and_Bob 源码和官方训练合同下形成了可靠正锚点。

唯一下一动作：

> 冻结 seed-1 final checkpoint、完整 manifest 和 evaluator，然后注册同 checkpoint 的 fixed-refresh versus native-categorical KEEP/SET 比较。

### `VALID_FAIL_R41_HMASD_ALICE_BOB_REPRODUCTION`

条件：

[
M0\land\neg(M1\land M2).
]

允许结论：

> 当前可执行官方源码/运行时组合没有重现该 paper-task 正锚点。

唯一下一动作：

> 永久退休 R41 paper-task 路线及其 PASS-only R30 treatment，完成 source-reproduction failure review。

明确禁止：

* 增加第六个 seed；
* 增加 steps；
* 使用 best checkpoint；
* 调 (k,n_Z,n_z,\lambda_D,\lambda_d)；
* 改 reward 或 observation；
* 更换地图大小；
* 以“可能是随机性”为理由反复运行到成功。

不存在 `UNDERPOWERED`、`MIXED` 或自动 rescue 分支。

---

# 六、PASS-only native-categorical R30 边界

以下内容**现在不授权实现**。它只定义 R41 PASS 后的唯一比较。

## 6.1 Warm-start

两臂都加载：

```text
R41 seed-1 exact final checkpoint
```

包括：

* high policy/value；
* low actor/critic；
* ValueNorm；
* (q_D/q_d)；
* 所有对应 optimizer states。

新增的 incumbent/age adapter 在两臂中结构相同、权重严格为零、optimizer moments 为零，使迁移时 logits 和 values 与 fixed-(k) checkpoint 完全一致。

禁止：

* 只加载 actor；
* `strict=False` 模糊加载；
* 重新初始化 low policy；
* 从五个 seed 中事后选择最佳 checkpoint。

## 6.2 两臂

### Comparator：native full refresh

每 (k_0=50)：

* 原样采样 native team skill (Z)；
* 原样顺序采样两个 categorical (z_i)；
* 每个采样都记作 `SET`；
* 即使新 skill 等于 incumbent，也重置 age。

### Treatment：native categorical KEEP/SET

保持同一个 (K=4) categorical individual-skill distribution。

对 active agent：

[
e_i=
\begin{cases}
\texttt{KEEP},&\tilde z_i=z_i^{-};\
\texttt{SET}(\tilde z_i),&\tilde z_i\ne z_i^{-}.
\end{cases}
]

初始 assignment 没有 incumbent，因此所有 categorical samples 都解释为 `SET`。

联合概率仍是：

[
\pi(Z)
\prod_i
\pi(
\tilde z_i
\mid
s,o,Z,\tilde z_{<i},z_i^{-},age_i
).
]

执行 log-probability 为：

[
\log p(e_i)
===========

\log\pi(\tilde z_i).
]

所以：

* KEEP 没有额外 Bernoulli head；
* SET 没有二次 factorization；
* 每个 token 只有一个 categorical ratio；
* 迁移时可以保持原始 policy 分布严格不变。

后序 agent 必须看到已应用的 working roster：

* 前序 KEEP：prefix 中保留 incumbent；
* 前序 SET：prefix 中写入新 skill。

agent order 保持官方 canonical order并随 transition 保存；不引入 learned ordering。

## 6.3 Clock 与 lifetime

[
k_0=50
]

保持不变。两臂都只在 (t=0,50) 进行 high check。

Treatment 的实际 individual lifetime 是连续 incumbent draws 的游程：

[
T_i=50\times\text{连续 KEEP 块数}.
]

不增加：

* arrival-triggered check；
* asynchronous high clock；
* duration head；
* forced maximum lifetime；
* KEEP reward；
* switch penalty；
* lifetime entropy reward。

## 6.4 Reward 与梯度

native team skill (Z)、(q_D/q_d) 和原始 HMASD low reward全部保留且两臂一致：

[
r_{i,t}^{l}
===========

0.1\log q_D(Z\mid s_{t+1})
+
0.2\log q_d(z_i\mid o_{i,t+1},Z).
]

high return 仍只包含外部 binary team reward。

没有梯度穿过：

[
\text{hard KEEP/SET interpretation}.
]

学习路径是：

[
r^h
\rightarrow
\text{native high team/agent GAE}
\rightarrow
\log\pi(Z),\log\pi(\tilde z_i),
]

以及：

[
r^l
\rightarrow
\text{low MAPPO}
\rightarrow
\pi_l(a_i\mid o_i,z_i).
]

两臂都继续更新原始 (q_D/q_d)，但不得修改其目标、输入、权重或 optimizer exposure。

这一例外只为保持 source substrate mechanism-matched；它不重新授权在 HA-CTSE、S7 或其他环境中使用旧 (q_D/q_d) reward。

## 6.5 Checkpoint 与曝光

PASS 后的正式比较应使用同一个 seed-1 checkpoint，32 rollout envs，每臂再训练 320,000 个环境步：

[
\frac{320,000}{32\cdot100}=100
]

个 continuation outer updates。

两臂必须：

* 相同 reset streams；
* 相同网络和参数量；
* 相同 optimizer exposure；
* 相同 low/discriminator训练；
* 相同 final 100-episode evaluator；
* 唯一差异为 incumbent categorical action是解释为 KEEP 还是 SET。

这一比较首先只能支持：

[
\text{native KEEP/SET 是否保持 task access、产生非退化 lifetime，并避免全同步刷新}.
]

它不能单独证明异步 lifetime 在一般任务上优于 fixed (k)。

R30 的高层外部回报、working-roster teacher forcing、单 token ratio、无 lifetime reward 等原则必须保持现有设计。

---

# 七、继续关闭的路线

以下路线在 R41 期间和之后仍保持关闭：

* R35 custom sparse Alice–Bob；
* R36 episodic joint-count novelty；
* R37 task-identity repair；
* R38 CTS；
* R39 role-free two-timescale toy；
* R40 simple_spread exact contract；
* 任何新的“方便 toy”或公共 benchmark 搜索；
* R29 action-density/action-information reward；
* R31 observational effect posterior；
* R32 IFEPG/direct effect gradient；
* R33 roster scorer；
* R34 hindsight clustering/distillation；
* task-specific novelty、distance、contact、coverage、progress 或 potential reward；
* NS-OPM 或任何其他新 intrinsic，在 source anchor 闭合前不得进入训练；
* sampled team latent 的 HA-CTSE revival；
* variable-(N)、set-roster、membership censoring 和 learned admission；
* S7 temporal comparison；
* duration head、KEEP reward、lifetime reward、switch penalty；
* 调参、扩种子、扩预算、改阈值或 best-checkpoint rescue。

Open-roster 仍是未来架构轴，但必须排在 fixed-(N) learned anchor 和同基底 R30 temporal gate 之后。

---

# 八、最强反对意见

最强反对意见是：

[
\boxed{
\text{Alice_and_Bob 可能只是一个为标准 HMASD 精确量身定制、}
\text{却不适合验证可变 lifetime 的正控制。}
}
]

原因包括：

* episode 只有 100 步；
* (k=50)，因此每个 episode 只有两次 high assignment；
* 恰好有两个 team skills，对应两颗 diamond；
* 恰好有四个 individual skills，对应两个 button 和两个 diamond；
* (\lambda_e=0)，low behavior 完全由原始 (q_D/q_d) pressure 驱动；
* 论文还明确指出 HMASD 对 skill interval 和 skill cardinality 较敏感。([NIPS 会议论文][1])

因此，即使 R41 PASS，也只能证明：

[
\text{官方机制能够在官方正任务上工作}.
]

它不能证明：

* R30 variable lifetime 有优势；
* 自然异步 roles 已出现；
* open-roster 会有效；
* S7 会成功；
* 当前项目的新 intrinsic 问题已经解决。

同样，因为 episode 只有两个 50-step blocks，后续 R30 最多只能产生 50/100 步 lifetime，并且任务可能天然偏好同步切换。一个有效的 R30 “无显著提升”结果不能直接推广为异步 lifetime 无用。

这个反对意见**不改变裁决**。经过 R35–R40 后，使用同算法族的官方正证据建立 source anchor，仍然比继续寻找新 substrate 更具因果辨识力。但它严格限制了 R41 PASS 和后续 R30 结果能够支持的 claim。

---

# 最终单一路线

[
\boxed{
\begin{aligned}
&\texttt{R40 = VALID_FAIL};\
&\texttt{Route = MODIFY R41};\
&\text{立即行动：固定官方 HMASD commit，执行五-seed官方 Alice_and_Bob复现};\
&\text{PASS：冻结 seed-1 final checkpoint，才允许同基底 native categorical R30};\
&\text{VALID FAIL：永久退休 paper-task 路线，不调参、不扩种子、不换阈值};\
&\text{INVALID：只修明确实现/同步缺陷，原合同重跑。}
\end{aligned}
}
]

[1]: https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf "https://papers.nips.cc/paper_files/paper/2023/file/c276c3303c0723c83a43b95a44a1fcbf-Paper-Conference.pdf"


