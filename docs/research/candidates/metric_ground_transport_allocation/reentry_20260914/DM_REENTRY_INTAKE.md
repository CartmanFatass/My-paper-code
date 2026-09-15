# MGTAP 重入 intake 与实际 CONTINUE 决定

## 当前决定与来源

**DM 选择 CONTINUE：恢复 MGTAP 方向内实现工作，接续 LCAC 释放的唯一预留；首个研究对象为 MGTAP-LR-SELECTION-B01。** 不再等待 Portfolio、Root 或 Clerk
作科学批准，不创建第四方向或替代 DM，也不恢复旧冻结 invocation。

当前直接输入是用户“算了 继续吧 同步clerk最新状态即可”、Clerk 随后的明确
CONTINUE/PARK 回执请求，以及用户交付的[两份 Portfolio 答复正文](PORTFOLIO_USER_COPY.md)。
全文已逐段读取。其来源是用户复制件，不冒称浏览器/API 导出或不可变 provider 消息；
[来源记录](SOURCE_RECEIPT.json)保留原附件身份、字节数和换行归一化。
旧 AGENTS 指令已被用户撤销，本决定不将它们恢复为当前控制依据。

DM 复读了最新 PARK、B02 intake、完整实际结果 review（固定交付
47699fcad5714bbe8cfca43abef78c89a3887b62 的122行）及本人的 review intake，
核对现有 COND/DENSE factory、early256 runner 和共享 learner。
科学方法重用 evidence spec §§11.8–11.10、FOUNDATIONS §§2–4、6 与
04_EMPIRICAL 的当前相关阅读：信息公平不等于有限学习等效；
配置选择和最终评估需区分，独立单位不能由世界数或候选数伪造。

## 对 Portfolio 的实质回应

采纳它提出的“COND 是否值得作为可选研发分支保留”的实现选择，但将问题细化为：
**双方获得相同、明确的有限标量学习率选择机会后，所选 COND 程序能否在一个
新的原生配对上提供有开发价值的局部收益？**

这不是再取一次固定学习率 early256 符号。现有原生 learner 的 Adam 学习率为
3e-4；本次同时让两臂在包含该原值的三点集合中按各自验证 J 选择，再从新初始化
训练一个独立 holdout 配对。不能根据 COND−DENSE 差值选择或削弱 DENSE，
不能用选择面板报告新主结论。具体协议见[新卡](../MGTAP_LR_SELECTION_B01_SCIENCE_CARD_20260914.md)。

原 PARK 对“不变采样的边际开发价值不足”的理由仍合理。本次改变的是投入对象：
旧 toy 的学习设置敏感性提供了这个方向内问题的具体线索，原生调优后的比较尚未测得。
toy 不是原生失败原因的证据，三点学习率选择也不是所有 B 必须通过的资格考试。
我认为该有限选择程序比单纯再补一个不变点更可能改变是否继续维护 COND
作为活跃可选分支的判断；这仍是未量化的开发价值判断，不是新的阳性发现。

最强备选仍是继续 PARK：early256 的 +0.01513、−0.05684 J 与 equal512 的
+0.00576、−0.02247、+0.02448 J 均保留，REL/TOP/不等曝光的不利观察各自保留，
不合并为同一主量。该新对象需要8个拟合而非一个不变配对的2个拟合，
一个选择 master 也会使配置选择不稳定；没有证据证明它具有最高 Portfolio 价值。
我接受这项有限额外工作以直接检验所选程序，不把空槽本身当科学理由。

## 第一项具体工作及当前执行事实

首个研究对象为 MGTAP-LR-SELECTION-B01；仅协议实现和测试已完成，不宣称原生 runner 已验收或实验已运行。

已在本 DM authoring checkout 实现独立的
[protocol.py](../../../../../experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01/protocol.py)：
固定选择/holdout 地址、双方各自择优和精确平局规则、完整面板约束、
最终主量与配置绑定，以及从真实配置计算的[计划工作量](PLANNED_EXPOSURE.json)。
对应纯合成[测试](../../../../../tests/experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01/test_protocol.py)
不导入环境或模型；准确验收结果见[工程记录](ENGINEERING.md)。

这是实际方向内实现工作，不止资料阅读或重入意向；因此 DM 的生命周期决定已经是
CONTINUE，应将同一预留转换为 MGTAP 实际占槽。main registry 由 Clerk 集成，
本 DM 不直接修改 main。此事件只使 MGTAP 占位+1、同请求预留−1，
不得覆盖其他方向较新的生命周期；最初的2→3是当时快照，不是强制总数。
后续已观察到 Clerk 应用本方向占位，同时 FOLR 已 PARK，见
[容量与运输路由补记](CAPACITY_AND_TRANSPORT_UPDATE.md)。不增加第四方向。

当前没有新原生拟合、评估、实验进程、Monitor 或 Transport。
新 B 的完整 runner、针对改变行为的独立审查、实际节点准入和启动尚未完成，
不能把协议测试当成原生技术验收或 B 结果。
下一动作由本 DM 直接完成新 runner 和绑定验收，再按对象推进；不等第二次科学派发。

## 保留边界

DENSE 仍是当前通用默认。即使新 holdout 超过 MEI，也只支持在这个有限用途下
继续发展所选 COND 分支，不自动升级共享默认、宣布总体稳定优越或推出几何机制。
inside/adverse 结果保留其实际含义，DM 据完整记录决定修改或 PARK，
不为获取正 seed 自动加跑。两次旧 C 的结构不可识别结论与旧坐标 family 均不改写。

来源、旧结果和模型不删除；已被政策拒绝删除的 scratch 不绕过。
成本与资源为新对象前瞻定义，旧378.77秒仅是已发生 native wall，
不是本次额度或完整研究成本。支持、模型服务、累计成本和 aggregate CPU 仍 UNKNOWN。

## Peer-DM role mapping and actual continuation boundary

At main control revision9a86963ed (transition c3baaa27b), this independent DM explicitly
read the complete live `.codex/agents/hmasd-direction-manager.toml` developer_instructions,
AGENTS.md and PEER_DM_COORDINATION.md. It then applied the newly published canonical
`hmasd-direction-management/SKILL.md` and completely read its `references/role.md`.
This loads full lifecycle, implementation/dependency, review-response, execution,
own-record/integration and direct peer/service responsibilities; an App title alone
is not role inheritance. The older Clerk-only integration wording above records its
earlier route and is superseded prospectively: Clerk is retired, main transaction
ownership is released, and this DM integrates accepted work under the short shared mutex.

Actual next work: the complete eight-fit runner and focused wiring tests are a bounded
Sol/medium Implementer batch while this DM authors independent scientific design review and
reconciles the assigned Clerk retirement handoff. No native launch has occurred. The draft
resource line is prospectively corrected from2GiB to the actual4GiB physical/effective
admission requirement; exposure, learner semantics and historical evidence are unchanged.

The separate bounded handoff owns only preservation of retiring Clerk's unresolved requests
and the one possible FOLR vacancy transaction, not authority over peers. Main9a86963ed reserves
the third slot for the original FOLR DM's explicit owner-requested scientific reconciliation.
Clerk reports a previously sent Portfolio request in conversation
6aa7836e-e4a0-83e8-985d-c633d94935b1. Exact Send provenance/full prompt and terminal answer
are being reconciled with the registered independent Transport; no new Send or replacement
application is authorized by that report. Current state is recorded only in the shared registry.
Tool/file/support recovery does not supply scientific polarity or a PARK reason.

The later OWNER Portfolio authority correction supersedes the earlier DM-final-lifecycle
wording prospectively. PORTFOLIO_DECISION_PROTOCOL.md and the updated direction/Portfolio
skills were read and applied: DM continues innovation, bounded experiments, engineering,
evidence interpretation and reports; Portfolio supplies final direction-level interpretation.
The already selected LR object continues without a new per-experiment permission request.
No unilateral new PARK, slot release or automatic replacement follows its eventual sign.
The pending direction-design review keeps its exact published input and is intaken under
current authority; its scientific question has not been duplicated or re-sent.

Clerk retirement is complete: full prior exchange preserved at552f0dce7904e35206b8e32f9180ab85aee822ad,
integrated on mainf92dc1619, shared preservation record40bc9a5a9, then actual App archive
confirmed and recorded atf1c5072d70639c6e0dec91d82bda03b696d08d72. The observed Clerk turn
was completed/idle with no remaining reported writer or producer. Main transaction
preserved the unrelated untracked tests/pelican_bicycle.html. Third-slot reservation
remains with FOLR's pending Portfolio interpretation. Full fixed old question/answer and
actual binding were delivered directly to FOLR and RCLE; they coordinate their own
new reports with Transport. MGTAP is not a standing coordinator.

## Completed implementation and scientific design review intake

The complete runner and focused tests are now delivered, with both engineering findings
corrected and independently rechecked. DM technical acceptance and the actual check
scope are in [ENGINEERING.md](ENGINEERING.md). No native invocation has yet occurred.

The full159-line independent design review atbf71e5287f830e6a36601d01553d2c74296e3137
was read, its immutable Git blob verified and reconciled into this branch. The
[substantive intake](../pro_packets/20260914_lr_selection_design_review/INTAKE.md)
answers the stronger PARK alternative and binds the review's three implementation
dependencies to the completed runner review. The exact earlier scientific question was
sent once, with no resend due to later Portfolio-authority wording.

DM retains the selected finite experiment: symmetric three-rate selection followed by
one genuinely fresh final pair asks a different useful development question from a third
unchanged draw. Its fourfold fit cost and noisy single-master selection remain real
counterarguments, not defects that review can erase. There is no assumed tuning gain,
native causal diagnosis, programme replication or population confirmation. Ordinary
implementation/execution proceeds; a later direction disposition goes to Portfolio with
the full signed evidence and strongest alternative, without unilateral PARK or slot release.

## Completed new empirical consequence

The selected programme has now completed all8fits at its exact published source.
Both own-score winners are1e-4; the fresh8252 pair gives+0.023704897713093642 J,
conditional paired-world SE0.004197354694630503,29positive/3adverse worlds. The frozen
MEI0.01 rule reads COND_ABOVE_MEI. Full-command wall658.02s; actual counts and original
20native/supervisor member bytes were collected/verified without additional science.
The [complete new intake](../MGTAP_LR_SELECTION_B01_INTAKE_20260914.md) updates the
optional-branch hypothesis, retains all old contrary evidence and compares a proposed
fixed-selected-LR recurrence with programme repetition and PARK. It does not claim
causal tuning benefit, stable ordering or automatic successor/default promotion.
Independent actual-results review and the resulting Portfolio report are the next
concrete work, not a return to Clerk or a new owner-approval gate.

FOLR's full Portfolio decision4776103de4f55beaee610c52506112651bfaed04 is CONTINUE/MEDIUM;
main5456aec117b9746f141d09292af2da1f803b8262 closes the possible FOLR vacancy with
three occupied/zero reserved or vacant. The bounded MGTAP retirement/vacancy handoff is
therefore complete; RCLE receives the released Portfolio conversation directly. No DISH
replacement is applied or requested by this DM.
