# GPT-5.6 Pro raw response: R34-BHMD result review

- Source model: ChatGPT `Pro` (GPT-5.6 Pro conversation)
- Date: 2026-07-15
- Conversation: `HMASD Algorithm Consultation`
- Submitted question: `GPT5_6_PRO_QUESTION.md`
- Extraction: visible response text from the in-app browser; equation layout is
  flattened, but no controller interpretation is inserted below.

---

1. 裁决

R34-BHMD：VALID SCIENTIFIC FAIL，永久退休

我没有发现任何改变注册 estimand、数据分布、cluster assignment、recurrent
replay、gradient scope、intervention evaluation 或 bootstrap interpretation
的具体实现缺陷。因此：

FAIL_M1_RETIRE_R34_BHMD

成立。

R34 不应：

- 改 K；
- 换 descriptor；
- 换 clustering；
- 增加 epoch；
- 扩大 recurrent/FiLM scope；
- 调 learning rate；
- 扩 seed；
- 改 fidelity/SNR threshold；
- 把 hindsight label 转成 reward / critic target / classifier。

问题文件已经明确要求：只有发现改变注册数据分布、聚类、recurrent
likelihood、gradient、intervention 或 bootstrap 的 defect，才允许拒绝该失败
结论。

2. R34 validity audit

2.1 M0 合法

R34 的核心合同：

natural focal trajectory -> balanced hindsight mode -> full recurrent
distillation -> forced reproduction

实现没有破坏该链路。

关键修正已经正确：

- 使用 focal-only displacement sequence；
- train-only normalization；
- train-only balanced clustering；
- Hungarian 只用于旧 skill ID 命名；
- high R30 KEEP/SET 冻结。

数据：

- 32 个 stochastic 80-step episodes；
- 24 train / 8 heldout；
- 384 train block-agent rows；
- 每个 mode 96 rows；
- descriptor shape [20]。

训练：

- frozen source；
- real_modes；
- episode_sequence_sham。

real/sham：

- 48 个 agent-episode；
- zero hidden state replay；
- 10 epochs；
- 60 Adam calls；
- lr 3e-4；
- clip 0.5。

梯度限制：

{actor_film, actor_rnn, actor_act.action_out.fc_mean}

其余冻结。

M0 全部 PASS：

- exact counts；
- train-only fitting；
- balanced modes；
- no-self sham；
- matched streams；
- finite optimizer；
- zero forbidden drift。

source recurrent replay 最大误差：

2.861 x 10^-6 < 10^-5.

因此不能归因于实现。

3. R34 失败的真实含义

3.1 Real > sham，但不代表 codebook creation

结果：

nearest prototype fidelity：

| | fidelity |
| --- | ---: |
| source | 0.5098 |
| real | 0.5752 |
| sham | 0.1836 |

real-sham：

+0.3916

CI：

[0.3613, 0.4277]

非常明显。

但是 source anchor：

real - source = 0.0654

要求：

>= 0.15

失败。

3.2 更关键的是 SNR 下降

persistent forced-mode SNR：

source = 1.7608

real = 1.5235

sham = 0.1591

real 虽然超过 sham：

+1.3726

但：

real - source = -0.2962

CI：

[-0.3518, -0.2165]

这说明：

BHMD 学会了“按照 hindsight 标签解释行为”，但没有创造比原 policy 更强的
skill-conditioned persistent separation。

换句话说：

label consistency != skill controllability

3.3 geometry diagnosis

当前 evidence 支持：

已存在：

source policy 已经具有 latent-conditioned behavior geometry：

z -> persistent trajectory separation

因为：

SNR_source = 1.76

但是：

prototype geometry 和 controllable skill geometry 不一致。

原因：

旧 skill trajectory manifold 可能不是四个清晰 cluster 的并集。更可能是：

M_z = overlapping continuous manifold

其中：

- skill boundary 模糊；
- temporal phase 连续变化；
- 同一个 skill 覆盖多个 behavior mode；
- hindsight clustering 强行离散化。

因此 BHMD 做的是：

trajectory -> cluster -> clone

它优化的是：

p(a | o, z_cluster)

而不是：

z -> controllable causal mode

最终导致：

fidelity up；source SNR down。

4. 可复用因果结论

R29-R34 形成一个清晰约束：

不能通过重新解释旧 skill 标签来创造 skill semantics。

具体：

R29

action density：z -> action 存在。

但：action separation !=> persistent effect

R31

observational effect：z -> trajectory 存在。

但：association !=> intervention

R32

individual effect gradient：存在小 causal shift。

但：small shift !=> new codebook

R33

joint roster selector：不能从旧 skill 中制造 interaction primitive。

R34

hindsight clustering：不能把连续行为 manifold 压缩成更好的 discrete skill
codebook。

最终约束：

Skill semantics must be created during skill formation, not assigned
afterwards.

5. 唯一 R35 路线

R35-OCSF

Online Controllable Skill Formation

在线可控技能形成

这是与 R34 结构不同的因果边：

z_i -> online exploratory process -> persistent controllable behavior -> skill
separation

区别：

R34：old trajectory -> label -> clone

R35：skill -> behavior -> discover useful skill

即恢复 HMASD discoverer 的真正功能，但不用旧 one-step discriminator reward。

6. R35 algorithm

6.1 核心思想

保持：

pi_l(a_i | o_i, z_i)

不变。

新增：

skill-conditioned online process contrast。

每个自然 rollout segment tau_i^z，长度 W=10，构造 process embedding：

phi(tau) = Encoder_psi(o[t:t+W], a[t:t+W])

限制：

输入：

- observation sequence；
- action sequence。

禁止：

- reward；
- task fields；
- old skill；
- agent ID；
- age；
- duration。

6.2 Online skill separation objective

训练一个 process critic：

q_psi(z | phi(tau))

但不直接作为 reward。

目标：

L_disc = -E[log q_psi(z | phi(tau))]

同时加入 shortcut null：

q_psi(z | phi(o))

和：

q_psi(z | duration)

作为诊断。

6.3 真正训练信号

采用 variational skill objective：

R_skill = log q_psi(z | phi(tau)) - log q_psi(z)

但只进入 low-level PPO：

A_t^low = GAE(r_env + lambda R_skill)

不进入：

- high PPO；
- KEEP/SET；
- task reward；
- critic high。

6.4 防止 R31/R34 重演

不是旧 z 分类。

skill label 来自当前 policy sampling：

z_t ~ pi_H

不是 frozen source。

不是 posthoc clustering。

没有 trajectory -> cluster 步骤。

不是 deterministic classifier reward。

process encoder 与 policy 同步训练。

7. 参数更新

允许 low actor pi_l 更新：

- actor FiLM；
- actor RNN；
- action mean。

允许 process discriminator q_psi 更新。

冻结：

- high KEEP head；
- high SET head；
- R30 clock；
- environment reward；
- OPT bridge；
- team latent；
- IMOD scheduler。

8. 与 R30 interaction

R30 保持 KEEP/SET 完全冻结。

R35 只改变 skill execution quality。

流程：

R30 chooses z_i

-> low actor executes

-> process discriminator measures whether z_i created a coherent process

-> low actor improves

不改变：

- check interval；
- lifetime；
- scheduler；
- roster。

9. 最小 abandonment gate

Budget

source: same frozen adaptive-R30 checkpoint

seed: 35031

episodes: 32 x 80 steps

split: 24 train / 8 heldout

segments: W = 10

training:

real: process objective ON

control: process objective OFF

updates: 40 low PPO updates

epochs: 15

lr: 3e-4

evaluation:

64 paired natural episodes

64 heldout forced segments

M0 validity

必须：

- 同一 rollout；
- 同一 z sampling；
- reward identical；
- only process intrinsic differs；
- high parameters drift < 10^-8；
- low update count identical；
- q optimizer identical；
- no task reward read into intrinsic。

M1 causal skill formation

Forced evaluation：同一 snapshot do(z)，比较 between B 与 within W。

要求：

median(B/W)_real >= 1.5

且：

CI_95(real - control) > 0.3

M2 natural skill usage

冻结 high R30。

测：

natural active skill: P(q(z | tau) = z)

要求：

real - control >= 0.15

且 joint coverage：

coverage_real / coverage_control >= 1.1

M3 shortcut rejection

必须：

duration-only classifier accuracy < 0.35

observation-only classifier 必须明显低于 full process classifier：

Acc(full) - Acc(obs) > 0.15

否则说明又学到了 shortcut。

失败分支

FAIL_M1

永久退休：online process discriminator 无法形成 controllable skill。

不得：换 encoder、换 reward scale、换 window。

FAIL_M2

结论：skill 可控但不能被 R30 使用。

禁止进入 team composition。

FAIL_M3

结论：skill semantics 仍来自 duration/context shortcut。

退休该 discriminator family。

10. 最终路线

R34 FAIL 不是因为 clustering 不够好、prototype 不够多、replay 不够长。

而是：

posthoc codebook construction cannot create causal skills

唯一下一条：

R35 Online Controllable Skill Formation

目标不是寻找更好的旧标签，而是恢复 HMASD 真正缺失的环节：

skill discovery -> persistent executable behavior -> skill differentiation

在 R35 gate 通过前，不进入正常训练，不宣称 cooperation、HMASD parity、S7
transfer 或任务收益。
