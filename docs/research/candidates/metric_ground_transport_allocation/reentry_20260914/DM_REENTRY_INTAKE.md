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
