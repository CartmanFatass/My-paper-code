# 明确裁决

[
\boxed{\texttt{CONFIRM_NO_ACCESS_R51_AMDT_SPECIALISTS}}
]

[
\boxed{\texttt{RETIRE_THE_EXACT_R51_AMDT_CONTRACT}}
]

R51 是一次**实现有效、但 ordinary-policy access 失败**的实验。五个 fixed-(N) specialists 都未建立正回报访问，因此 shared-variable-(N) 结果必须继续隔离，不能用于支持或否定跨规模参数共享。

唯一下一条可证伪路线为：

[
\boxed{
\textbf{R52-ARFA-G0：
Anonymous Reliability–Fulfillment Allocation}
}
]

其唯一因果边是：

[
\boxed{
\begin{aligned}
&\text{随 }N\text{ 扩展的匿名资源分配任务}\
&+\text{终局、分级、非可加的原生任务效用}\
&+\text{可辨识的 focal stay/switch 关系}\
&\rightarrow
\text{fixed-}N\text{ specialists 获得普通外部回报载体}\
&\rightarrow
\text{检验一套共享策略能否跨 }N\text{ 学习。}
\end{aligned}
}
]

---

# 一、R51 有效性审计

## 1. 曝光量、概率账本和优化路径全部有效

正式结果精确达到：

```text
balanced cycles                    125
N-specific batches/arm             625
transitions/arm                 320,000
transitions/N/arm                64,000
agent-token decisions/arm     1,280,000
shared optimizer steps             625
specialist steps/model              125
specialist aggregate                625
PPO epochs                             1
collected-batch reuse                  0
```

同时：

```text
sample/replay max error               0
prefix replay max error               0
masked probability mass               0
```

全部 M0 检查为真，包括 paired ledgers、状态形状与 (N) 无关、exact-final checkpoint reload、梯度支持、参数漂移、终局 reward 检查和 evaluation 数量。

所以失败不能归因于：

* 625-step exposure 没有实际执行；
* PPO 没有更新；
* recurrent replay错误；
* AR prefix没有重建；
* 无效 entity获得了概率质量；
* shared 与 specialist没有配对；
* checkpoint保存或重新加载错误；
* 模型没有收到梯度。

## 2. 环境 transition 与二元终局奖励符合注册合同

实现中，agent 只有在继续选择当前非 depot entity 时才提供服务。Station 被服务时恢复到 health 4，否则 health 每步下降；job 被服务后完成，deadline到零则设置 failure。所有中间 reward 为零，只有最后一步满足“没有任何 failure 且全部 jobs完成”时才返回 1。

结果文件也确认：

```text
reward_only_terminal             true
reward_matches_success_predicate true
no_invalid_action                true
intermediate_reward_terms        0
shaping_reward_terms             0
intrinsic_reward_terms           0
```

因此不存在隐藏的 progress、job completion、station occupancy或 team-size reward。

## 3. PPO credit 与 recurrent flow有效

轨迹完整保存 observation、entity mask、agent/entity order、pointer action、prefix count、old log-probability、value、reward和 recurrent reset mask。Replay 从 episode初始零 hidden 开始，逐 primitive step teacher-force相同的 pointer和外生顺序。GAE使用 (\gamma=0.99,\lambda=0.95)，episode末不 bootstrap；token PPO loss按 active-agent维度平均。

所以没有证据支持以下 invalidation：

[
\text{“终局 reward 没有传播到较早动作”}
]

或：

[
\text{“recurrent likelihood 与执行轨迹不一致”。}
]

## 4. Specialist 整个训练过程从未观察到正 task return

完整 CSV 有 625 个训练 batch；从第一批到最后一批：

```text
shared_success     = 0
specialist_success = 0
```

始终成立。

因此五个 specialist 的 on-policy buffers 中，从未出现一个正 terminal reward episode。最终每个 (N) 的 specialist：

[
S_N^{spec}=0,
\qquad N\in{2,3,4,5,6}.
]

所有 final-minus-zero区间和四个连续 evaluation blocks也都是零。

这不是略低于 access floor，而是完全没有 task-return carrier。

---

# 二、结果的可复用因果结论

R51 支持：

[
\boxed{
\begin{aligned}
&\text{正确的可变-}N\text{ set-pointer接口}\
&+\text{严格配对的sampling/replay}\
&+\text{真实梯度和完整参数更新}\
&+\text{任务确实随 }N\text{ 扩展}\
&\not\Rightarrow
\text{full-conjunction terminal reward具有普通策略访问。}
\end{aligned}
}
]

具体地：

> 在注册的 AMDT dynamics、32-step horizon、reset distribution和“所有 station 均存活且所有 jobs 全完成”的唯一二元终局奖励下，320K transitions没有生成一次正回报轨迹，因此 PPO没有用于学习任务成功的外部回报载体。

R51 **不支持**以下结论：

* variable-(N) parameter sharing失败；
* shared model容量不足；
* set/pointer架构无效；
* fixed-(N) specialists若获得有效 reward carrier仍无法学习；
* open-roster总体方向无效。

Shared arm必须隔离。注册分支本身也规定，M1失败时状态为 `NO_ACCESS_R51_AMDT_SPECIALISTS`，而不是 shared-variable-(N) failure。

---

# 三、一个不会改变 verdict、但必须吸收的设计缺陷

R51 actor没有显式观察 focal agent与候选 entity之间的“当前所在位置”关系。

Self vector只描述当前 entity的属性；公共 entity set描述各entity的health、work、deadline和全队assignment count，但没有对每个 focal-agent/entity pair提供：

```text
is_current_entity_for_focal
```

Pointer key只读取entity embedding和planned-assignment count。当前采样的pointer也没有显式作为下一步GRU输入写回。

当多个 stations或jobs具有相同状态时，匿名agent可能无法辨认“选择哪一个entity才是在原地继续服务”。

这不把R51改判为`INVALID`，因为：

1. 该信息合同是预注册R51 estimand的一部分；
2. M1就是用来否决整个环境—观察—策略访问合同的；
3. 即使 (N=2) 只有一个station和一个job，也没有任何训练成功。

因此绑定解释应为：

[
\boxed{
\text{R51完整环境/信息/奖励合同不可访问，}
}
]

而不是只归因于某一个单独因素。

---

# 四、R51 精确退休边界

永久退休：

```text
R51 AMDT transition kernel
32-step horizon
wave/reset distribution
absorbing global failure bit
terminal all-stations-survive AND all-jobs-complete binary reward
R51 self/entity observation contract
R51 specialist/shared access thresholds as applied to this exact task
```

明确禁止通过以下变化重新运行R51：

* 320K增加为更大预算；
* PPO epochs由1改为5；
* 增加seed；
  -扩大模型；
  -降低M1阈值；
  -增加station/job中间奖励；
  -加入intrinsic reward；
  -选择best checkpoint；
  -只添加 `is_current_entity` 后仍称为R51修复。

下一实验必须具有新的编号、任务目标、observation contract和terminal branches。

---

# 五、唯一下一条路线：R52-ARFA-G0

## 1. 任务定位

**Anonymous Reliability–Fulfillment Allocation** 是一个新的variable-(N) Markov game，而不是对R51结果的重判。

它保留R51已经验证有效的部分：

* (N\in{2,3,4,5,6})；
* anonymous homogeneous agents；
* workload随 (N) 增长；
* persistent stations与short jobs；
* set/pointer AR policy；
* shared versus fixed-(N) specialists；
* terminal-only external reward；
* 320K transitions和625-step合同。

它改变两个新的因果对象：

1. 二元full-conjunction terminal objective改为终局分级的max–min service objective；
2. pointer score加入匿名、task-generic的focal-current-entity关系。

---

# 六、R52 完整 Markov game

## 1. Team size与workload

[
N\sim\operatorname{Uniform}{2,3,4,5,6},
]

episode内membership固定。

[
P_N=\left\lfloor\frac N2\right\rfloor,
\qquad
D_N=N-P_N.
]

每个episode有：

* (P_N) 个persistent reliability stations；
* 每个wave有 (D_N) 个short fulfillment jobs；
* 一个depot；
* active entity count：

[
E_N=N+1.
]

随着 (N) 增加，agent数、station数、job数和AR sequence length同时增加。任务不是增加空闲成员，也不是复制多个独立二人任务。

## 2. 时间结构

```text
episode horizon       32
wave starts           {4,12,20}
job deadline          6
station health range  0..4
```

episode始终固定32步结束，无early termination。

## 3. Action和switching

每个agent选择一个当前有效entity pointer。

若：

[
a_{i,t}=\ell_{i,t}\ne\texttt{DEPOT},
]

本步提供服务。

若：

[
a_{i,t}\ne\ell_{i,t},
]

本步只移动，不服务，并在step末更新location。

重复分配不会直接受到奖励惩罚，但会浪费有限team capacity。

## 4. Station dynamics

[
h_{p,t+1}=
\begin{cases}
4,&p\text{被至少一名agent服务};\
\max(0,h_{p,t}-1),&\text{否则}.
\end{cases}
]

与R51不同，health达到0不再设置永久global-failure bit。以后重新服务仍可恢复station。

累计可靠度：

[
A_{p,t+1}
=========

A_{p,t}
+
\frac{h_{p,t+1}}4.
]

最终weakest-station reliability：

[
\boxed{
M=
\min_p
\frac{A_{p,32}}{32}
}
\in[0,1].
]

## 5. Job dynamics

每个job初始work为1。

在deadline内被至少一名agent服务时：

[
work_j\leftarrow0
]

并计为按时完成。

若deadline到零仍未完成，job标记为expired；以后不能再被补做并计入完成数。

最终fulfillment：

[
\boxed{
J=
\frac{#\text{按时完成jobs}}
{3D_N}
}
\in[0,1].
]

## 6. 唯一外部奖励

所有中间steps：

[
r_t^{ext}=0,\qquad t<31.
]

最终：

[
\boxed{
r_{31}^{ext}=U=\min(M,J).
}
]

这不是中间 shaping：

* 不逐job发奖励；
* 不逐station发奖励；
* 不使用potential difference；
* 不奖励角色、停留、切换或team size；
* 不使用intrinsic reward。

它是新的终局任务目标：最大化长期可靠性与短期任务履约中的最弱项。

---

# 七、R52 information contract

## Self view：6维

```text
at_depot
current_entity_has_health
current_entity_has_work
current_entity_health / 4
current_entity_deadline / 6
served_on_previous_step
```

## Base entity view：8维

```text
is_depot
active
current_health / 4
cumulative_health_integral / 32
work_remaining
deadline_remaining / 6
ready_service_count / N
currently_assigned_count / N
```

## Focal relation：1维

每个focal agent对每个candidate entity附加：

```text
is_current_entity_for_focal
```

每个agent在active entity set中恰有一个值为1。

这是匿名关系，不是agent ID、slot ID或oracle role。它只使“stay versus switch”的动作语义可观察。

## Centralized critic fields：4维

```text
t / 32
wave index / 3
completed-job fraction
current weakest accumulated station reliability
```

---

# 八、模型、概率与PPO合同

复用R51的小型N-independent recurrent set-pointer结构，只修正输入宽度：

```text
member encoder  6 -> 32 -> 32
entity encoder  8 -> 32 -> 32
GRU hidden      32
query MLP       128 -> 64 -> 32
entity key      34 -> 32
critic          pooled state -> 64 -> 1
```

Exact参数量：

[
24,897<35,000.
]

每步仍有外生active-agent order：

[
\pi_\theta(\mathbf a_t\mid o_t)
===============================

\prod_{j=1}^{N}
\pi_\theta
\left(
a_{\sigma(j),t}
\mid
o_{\sigma(j),t},
a_{\sigma(<j),t}
\right).
]

前序actions通过planned entity counts进入prefix。Teacher-forced replay必须重建：

* member/entity orders；
* masks；
* pointers；
* focal-current relation；
* applied prefix；
* recurrent hidden。

复杂度仍为：

[
O(NE_Nd)=O(NK),
\qquad E_N=N+1,
]

不枚举 (K^N)，不构建mandatory agent-agent (N^2) tensor。

PPO保持：

```text
gamma               0.99
GAE lambda           0.95
learning rate        3e-4
PPO epochs           1
entropy coefficient  0.01
value coefficient    0.5
clip                  0.2
gradient clip        0.5
```

Token loss按active (N) 平均；advantages在每个N-specific batch内单独标准化。

---

# 九、唯一比较与launch-exact exposure

## Treatment

```text
shared_variable_N
```

一套参数训练所有五个team sizes。

## Comparator

```text
fixed_N_specialist_family
```

五个架构和初始化相同的specialists，各自只训练一个 (N)。

Shared与对应specialist逐batch共享：

* reset ledger；
* entity/member permutations；
* external AR order；
* categorical uniforms；
* transitions；
* optimizer exposure。

## 固定预算

```text
experiment                    R52-ARFA-G0
team sizes                    {2,3,4,5,6}
parallel environments         16
episode / rollout             32 / 32
balanced cycles               125
N-specific batches/cycle      5
N-specific batches/N          125
N-specific batches/arm        625
episodes/N/arm                2,000
transitions/N/arm             64,000
transitions/arm               320,000
agent-token decisions/arm     1,280,000
PPO epochs                    1
shared optimizer steps        625
specialist steps/model        125
specialist aggregate          625
zero-step evaluation          128 episodes/N/arm
final evaluation              128 episodes/N/arm
bootstrap repetitions         10,000
```

固定seeds：

```text
model/init        52052
training reset    62052
order/action      72052
evaluation reset  82052
bootstrap         92052
```

---

# 十、最小 abandonment gate

## M0：implementation validity

必须全部满足：

1. (P_N,D_N,E_N) 与注册公式一致；

2. station health与累计reliability transition正确；

3. job deadline、completion与expiry transition正确；

4. expired job以后不能增加completed count；

5. 所有中间reward严格为0；

6. 最终reward逐episode严格等于：

   [
   U=\min(M,J);
   ]

7. 一个注册constructive schedule对每个 (N) 产生：

   [
   M=J=U=1;
   ]

8. no-job schedule产生 (U=0)，partial schedule产生 (0<U<1)；

9. 每个focal agent恰有一个正确的 `is_current_entity=1`；

10. actor无ID、slot、role、skill、KEEP/SET、shaping或intrinsic字段；

11. shared/specialists初始参数逐位相同；

12. 精确达到320K transitions/arm、64K/N和625/125 optimizer counts；

13. PPO epoch为1，无batch reuse；

14. sample/replay与prefix误差：

[
\le10^{-6};
]

15. masked probability mass为0；
16. recurrent hidden只在episode边界清零；
17. 所有相关模块有有限非零gradient和parameter drift；
18. exact-final checkpoint reload error为0。

M0失败：

```text
INVALID_R52_ARFA_WIRING
```

唯一动作：只修明确的transition、reward、relation、mask、replay、count或checkpoint defect，并原合同重跑。

---

## M1：fixed-(N) specialist access

先要求每个 (N) 的specialist训练数据中：

[
P_{\mathrm{train}}(U>0)\ge0.10.
]

这是task-return carrier gate。

Exact-final每个 (N) 要求：

[
\bar U_N^{spec}\ge0.60,
]

[
\bar M_N^{spec}\ge0.65,
\qquad
\bar J_N^{spec}\ge0.65.
]

Equal-(N) macro：

[
\bar U^{spec}\ge0.70.
]

每个 (N) 的final-minus-zero paired bootstrap：

[
\operatorname{LCB}*{95}
[
U*{N,\mathrm{final}}^{spec}
---------------------------

U_{N,\mathrm{zero}}^{spec}
]

> 0.20.
> ]

每个 (N) 的四个连续32-episode blocks中，至少三个满足：

[
\bar U_{N,\mathrm{block}}^{spec}\ge0.50.
]

若M0通过而M1失败：

```text
NO_ACCESS_R52_ARFA_SPECIALISTS
```

唯一动作：

> 永久退休精确ARFA dynamics、terminal utility、observation relation和32-step合同；隔离shared结果。

禁止改变reward aggregation、预算、PPO epochs、seed、model或threshold进行救援。

---

## M2：shared cross-(N) learning

每个 (N) 要求：

[
\bar U_N^{shared}\ge0.50,
]

[
\bar M_N^{shared}\ge0.55,
\qquad
\bar J_N^{shared}\ge0.55.
]

Macro：

[
\bar U^{shared}\ge0.65.
]

Within-(N)与macro ratios：

[
\min_N
\frac{\bar U_N^{shared}}
{\bar U_N^{spec}+10^{-8}}
\ge0.75,
]

[
\frac{\bar U^{shared}}
{\bar U^{spec}+10^{-8}}
\ge0.85.
]

Paired equal-(N) macro noninferiority：

[
\operatorname{LCB}_{95}
\left[
\frac15
\sum_N
(U_N^{shared}-U_N^{spec})
\right]

> -0.10.
> ]

Shared final-minus-zero：

[
\operatorname{LCB}*{95}
[
\bar U*{\mathrm{final}}^{shared}
--------------------------------

\bar U_{\mathrm{zero}}^{shared}
]

> 0.25.
> ]

若M0、M1通过但M2失败：

```text
VALID_FAIL_R52_SHARED_VARIABLE_N
```

唯一动作：

> 永久退休精确shared ARFA set-pointer MAPPO合同，并停止当前variable-(N) learning line，进行一次架构/优化失败审查。

不允许扩大网络、增加epochs、修改任务或放宽阈值。

---

## PASS

```text
PASS_R52_ARFA_VARIABLE_N
```

仅当：

[
M0\land M1\land M2.
]

唯一下一动作：

> 在同一个ARFA、同一个ordinary policy和同一个terminal utility下，注册一次within-episode **exogenous join/leave 与 membership-censoring gate**。

仍不授权：

* skill latent；
* KEEP/SET；
* variable skill lifetime；
* intrinsic reward；
* unseen-(N) claim；
* S7/UAV transfer；
* paper novelty。

---

# 十一、最强反对意见

最强反对意见是：

[
\boxed{
U=\min(M,J)
\text{ 将R51的hard binary conjunction替换成了更易获得的连续终局效用。}
}
]

该反对意见成立。因此即使R52 PASS，也不能声称：

* 解决了full-conjunction sparse exploration；
* 重建了HMASD intrinsic exploration loop；
* R52优于R51；
* binary success会自然出现；
* UAV稀疏任务已可访问。

但它不改变路线选择，因为：

1. R52明确是一个新的任务目标，不是R51结果救援；
2. reward仍只在episode末出现；
3. 没有中间subtask bonus或potential shaping；
4. max–min reliability/fulfillment本身是合理的资源调度效用；
5. fixed-(N) specialists仍必须证明显著的zero-to-final学习；
6. shared结果仍受specialist access prerequisite约束。

---

# 最终单一决定

[
\boxed{
\begin{aligned}
&\texttt{R51 = CONFIRMED NO ACCESS};\
&\text{未发现改变分支的transition、reward、replay、PPO、}\
&\quad\text{checkpoint或evaluation defect};\
&\text{精确R51合同永久退休；shared结果继续隔离};\
&\text{唯一下一路线为R52-ARFA-G0};\
&\text{R52使用terminal }U=\min(M,J)\text{任务目标，}\
&\quad\text{并加入匿名focal-current-entity关系};\
&\text{specialists先建立ordinary-policy access，}\
&\quad\text{之后才解释shared cross-}N\text{结果};\
&\text{任何有效M1或M2失败均永久退休精确路线，}\
&\quad\text{不得通过budget、seed、epoch、model、reward或threshold救援。}
\end{aligned}
}
]
