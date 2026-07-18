1. Evidence audit
已建立事实（Stage B / Stage C）

Stage B 只证明动态 roster 控制问题本身可学习，不证明 skill hierarchy 必要。

Stage B anonymous recurrent primitive-action controller 已经学习动态团队任务：

deterministic P/S/U=1/0.998210/0.999105

stochastic U=0.986654
这说明环境、动态成员变化、匿名执行约束不是不可解问题。

因此：

“动态 N 导致所有方法失败”不成立。

“必须需要 skill abstraction 才能解决动态团队”尚未成立。

Stage C 建立的是 skill-execution bottleneck，而不是确定原因。

Stage C F0/F1：

实现有效；

paired contract 有效；

两 arm 完成 320,000 transitions；

最终均为 P/S/U=0/1/0.5；

F1-F0 utility CI95 = [0,0,0]。

同时：

F1 不是完全没有 skill signal：

working vs initial prefix TV CI95:
[0.047562,0.050023,0.052577]

directional composition shift 为正；

forced audit rho=0.070304。

但：

两个 arm 都没有 executable naturally used skills。

所以 Stage C 支持：

当前 skill bottleneck 没有形成“可执行、可复用行为语义”。

不支持：

skill selector 有 bug；

lifetime clock 一定错误；

intrinsic 一定错误；

hierarchy 一定错误。

Original HMASD 能证明什么

Original HMASD 仍然提供正向 anchor：

skill-conditioned low controller；

environment-agnostic q_d/q_D mutual information reward。

但是：

HMASD 是固定 N；

没有解决 dynamic membership；

没有解决 asynchronous lifetime。

因此不能直接迁移 HMASD reward。

已退休路线边界

不能重新包装：

R29 direct action-information reward；

R31-CFEI observational/forced-effect reward；

R32-IFEPG direct individual-effect policy gradient；

R33 intervention-scored roster complementarity。

它们可以作为失败证据，但不能作为未完成版本继续调参。

2. Causal portfolio

以下不是排序后的路线，而是四个竞争解释。

H2-A：缺失真正 environment-agnostic skill semantic pressure
Mechanism

当前：

z_i
 |
pi_low(a|o,z)
 |
external reward

缺少：

z_i -> predictable reusable behavior

因此：

high-level 可以改变 label occupancy；

low-level 不需要让不同 z 产生稳定行为；

skill 退化为 latent index。

替代结构：

保留：

discrete skill;

low-level conditioned execution;

HMASD 信息语义。

替换：

原固定 segment MI；

改成 variable-membership / mixed-age compatible behavioral predictability。

核心思想：

skill 的 intrinsic target 不是：

“完成任务”

而是：

“这个 z 是否持续对应一种可识别行为过程”。

Predicted observable

如果正确：

同一 z 跨：

agent;

lifetime age;

roster change

仍保持行为 signature。

出现：

skill-conditioned action distribution separation；

long segment predictability。

Strongest contradiction

如果 Stage B primitive policy 已经能解决任务，而任何 skill pressure 都无法提升：

说明：

skill abstraction 在该 substrate 没有必要。

Confidence

中等偏高。

原因：

Stage C 已经直接暴露：

“skill exists statistically but is not executable”。

H2-B：skill representation 存在，但 credit alignment 错误
Mechanism

问题不是 skill discovery，而是：

skill effect
      |
      ?
terminal reward

之间 credit path 太长。

当前 high assignment：

看最终 external reward；

不知道哪个 skill contribution 有用。

但 R31/R33 已经排除：

简单 effect reward；

complementarity score。

所以新方向不能是：

“计算 skill contribution”。

而应该是：

替换 credit representation。

例如：

让 high-level 学习：

skill transition -> future option value

而不是：

skill -> immediate effect
Predicted observable

如果正确：

skill forced audit 已存在差异；

但 natural selection 不稳定。

加入更合适 credit 后：

occupancy 变稳定；

execution success 上升。

Strongest contradiction

如果 low-level 本身没有形成 skill behavior：

任何 credit 都无法选择不存在的东西。

Confidence

中等。

H2-C：fixed skill interface 本身错误
Mechanism

当前：

π
l
	​

(a
i
	​

∣o
i
	​

,z
i
	​

)

假设：

skill 是 agent-local latent。

但 dynamic team:

agent 加入；

agent 离开；

skill age 不同步。

可能需要：

skill-conditioned execution context。

不是：

o_i,z_i

而是：

o_i,
z_i,
local temporal context

但限制：

不能添加：

identity；

roster slot；

global team latent；

scheduler。

因此是替换接口，而不是增加第二 controller。

Predicted observable

如果正确：

当前 skill signature：

存在，但无法 transfer。

新的 interface：

应该提高：

cross-agent skill reuse；

mixed-age consistency。

Strongest contradiction

如果简单 π(a|o,z) 已经足够：

那么增加 context 只是复杂化。

Confidence

中低。

H2-D：hierarchy 在该 substrate 不必要
Mechanism

Ordinary MARL 解释：

Stage B 已经解决：

dynamic N；

anonymous agents。

Stage C failure 只是说明：

toy substrate 没有可识别 reusable skills。

那么：

skill hierarchy 是错误归因。

Predicted observable

如果正确：

继续寻找 skill mechanism：

不会产生：

stable executable skill；

generalization gain。

Strongest contradiction

如果未来发现：

skill-based policy 在 unseen N/lifetime 明显优于 primitive policy，

则 hierarchy 假设重新成立。

Confidence

中等。

3. Replacement ledger per candidate
Candidate	Retain	Delete	Replace	Add
H2-A	skill bottleneck, decentralized low policy	current MI formulation	fixed HMASD q semantics	variable-age behavioral predictability
H2-B	hierarchical assignment	terminal-only skill credit	effect credit estimator	future-value skill credit
H2-C	latent skill concept	strict o,z interface	low execution conditioning	minimal temporal context
H2-D	dynamic anonymous controller	hierarchy assumption	skill abstraction	stronger evidence substrate

拒绝：

“skill + graph”

“skill + field”

“skill + scheduler”

“skill + team latent”

作为模块堆叠。

4. Intrinsic-reward boundary

Original q_d/q_D 可以部分保留，但必须重新定义边界。

允许：

skill-conditioned behavior predictability；

skill mutual information；

environment-agnostic temporal consistency。

不允许：

task state；

role label；

progress；

contact/success predicate；

external reward。

变量 membership 下：

不能定义：

“skill 对团队任务贡献多少”。

因为那已经是 task semantic。

可以定义：

“skill 是否保持自身行为 identity”。

mixed-age segments：

需要：

skill semantics 对 segment age invariant。

即：

p(behavior | z, age)

应保持可预测。

5. Probability, credit and lifetime audit

共同要求：

Policy factors

必须明确：

π_request
π_high
π_low

三者不能混淆。

Gradient boundary

必须保持：

low policy 不被 intrinsic selector gradient 偷渡控制；

high policy 不直接优化 external disguised intrinsic。

Clock

需要同时记录：

physical time:

environment step

和：

event time:

skill transition event
Mask

必须：

active agent only；

survivor recurrent continuity；

leave agent state termination。

这些属于最终 invariant。

Segment ownership

必须明确：

skill segment：

谁产生；

谁负责 credit；

谁更新。

不能出现：

多人共享 segment 但无人负责。

Checkpoint

必须保存：

policy parameters；

recurrent state；

skill assignment state；

lifetime clock；

event ledger。

6. Ordinary-MARL objections
Against H2-A

普通 MARL：

“primitive recurrent policy 已经足够。”

反驳条件：

必须展示：

skill policy 在：

unseen roster；

longer lifetime；

transfer

超过 primitive。

Against H2-B

普通 MARL：

“credit 问题只是 PPO optimization。”

反驳：

需要证明：

skill behavior 已存在，只是选择失败。

Against H2-C

普通 MARL：

“增加 context 只是增加容量。”

反驳：

必须证明：

同容量 primitive 不具备相同行为压缩能力。

Against H2-D

普通 MARL：

这是最强解释。

目前不能排除。

7. Retired-line exclusion
R29

不是：

“换一个 action information”。

原因：

direct action information reward 已退休。

R31-CFEI

不是：

“更好的 forced effect”。

原因：

forced effect 只能证明存在差异，不能产生 reusable skill。

R32-IFEPG

不是：

“重新设计 individual effect gradient”。

R33

不是：

“更复杂 complementarity”。

Scheduler-only

排除：

scheduler 只能决定：

什么时候换。

不能产生：

为什么这个 skill 有意义。

Task-shaped

排除：

任何：

role；

progress；

success；

contact

都违反 intrinsic boundary。

8. Serialized evidence graph

不是实验路线，而是信息获取顺序。

Evidence 1：skill existence test

问题：

H2-A/B/C 是否建立在真实 skill behavior 存在？

观察：

z-conditioned behavior clustering；

cross-agent transfer；

cross-age stability。

更新：

如果不存在 → H2-D 权重增加。

如果存在 → H2-A/B/C 保留。

Evidence 2：credit identifiability test

问题：

已有 skill 是否只是无法被 high-level 利用？

观察：

固定 skill executor：

测试 assignment learning。

更新：

成功 → H2-B。

失败 → H2-A/C。

Evidence 3：interface ablation

问题：

限制是否来自：

π(a∣o,z)

观察：

最小 context replacement。

更新：

大幅改善 → H2-C。

无改善 → H2-D。

9. Portfolio stop and integration conditions
H2-A retire

如果：

证明不存在稳定 skill semantics。

H2-B retire

如果：

skill 已不存在。

H2-C retire

如果：

最小 interface replacement 无收益。

H2-D retire

如果：

skill policy 在 transfer/generalization 上显著优于 primitive。

Integration condition

只有当：

skill semantics 被证明存在；

skill execution 可复现；

dynamic N/lifetime transfer 有优势；

才允许进入 integration。

Portfolio stop condition

停止条件：

不是某一个 candidate fail。

而是：

H2-A/B/C 均无法建立 executable skill；

primitive MARL 已达到全部目标；

dynamic testbed 无法区分 hierarchy value。

当前 Stage C 的结论应保持：

已确认 skill bottleneck；尚未确认 bottleneck 的算法原因。下一步应减少不确定性，而不是继续增加模块。
