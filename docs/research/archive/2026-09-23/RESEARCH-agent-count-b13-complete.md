退役日期：2026-09-23。DM1 的 B13 四策略共同回放已完整验收；此页保存被替代的计划与运行快照，不再维护。
来源：已发布 main `13f5adf00a7fe37fdf71069dcdaa20cde7fb5d81` 的 RESEARCH.md。
仅退役 DM1 已完成计划，其他方向和 owner 控制不变；当前判断见 ../../RESEARCH.md。

## 原方向状态

| `agent_count_generalization` | 固定 k、回合内固定 roster 时，HMASD 对未见团队数量 N 的服务能力和泛化代价是什么？ | exploring | Codex DM (independent session) | 直接 DM：task `01a0c6ef-cdd4-7113-b2d9-20487e35171b`，host `local`；checkout `/home/fires/.codex/worktrees/7fef/hmasd-wsl`，branch `codex/agent-count-generalization`。B12已完整验收：2fits/720k train/64k eval，30文件逐字节核验、四面板原生轨迹独立重算、实际共同初始化与90更新检查通过。N8 T8−T6 J −.042106854、服务−1.1256875人/步（J4正/28负）；N6 J −.064500572、服务−2.41025（J1正/31负）。两N全部世界高度罚更高；最差N8服务−6.828，最差N6−6.794，同时保留N8四个和N6一个J有利世界。B11的N8 +.019681931 J/+3.0195服务与此块反号，同实际评价世界使换面板解释不成立；不池化隐藏不一致，不作训练原因归因。复用既有Pro的反号分支，结束当前目标N训练配方追加，0第三块/确认；B12两臂均已收取验收。sum command181.734382min，重叠admission→last exit107.501981min。完整Pro答复已同key核验并保存，采纳B13四个原始final45策略的共同回放：B03/B07 H6对B11/B12 T6，N8主用途与N6后果，0新fits/128k eval。首个准入尝试因稀疏快照缺少已提交历史文件而在读取前退出；9文件完整核验保存，0 fits/0评价。a02稀疏读取修复已独立复核、21项检查通过；source01fc89e5d已在4070原生准入运行，观察器接管同一操作，0已验收B13科学结果。八面板协议不变；先重现SET再读H6。[a02原生运行](../../candidates/agent_count_generalization/NOTES.md#b13-a02-admitted-under-the-unchanged-ordinary-control-protocol)；[原失败与修复L0](../../candidates/agent_count_generalization/NOTES.md#b13-admitted-attempt-failed-before-exposure-l0-for-sparse-evidence-loading)。保留全部2×2差值及其代数依赖，不作为四次独立证据或普通基线认证。B04–B06反号与B07/B08/B10边界保留。[完整B12与判断](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b12-complete-target-condition-benefit-reverses-on-fixed-development-panels)；[完整咨询与采纳](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--pro-advice-adopted-fixed-b13-ordinary-control-comparison)。 |

## 原 B13 计划

| **DM1：泛化与训练条件** | B12在同世界反转B11的N8 J/服务收益，高度代价再次出现；更强普通T6必须进入后续包比较。 | **B13固定：0新fits，128k eval。** 完整Pro同key核验后保存全文，采纳四个原始final45策略在N8/N6各32世界的共同回放，保留B03/B07两份H6及B11/B12两份T6。先复现SET逐世界读数/原生初值与服务轨迹，再读H6剩余J/服务用途、N6后果及损失世界。两份H6对两份SET的差值共享四个策略，不能当作交互实验或四次独立复现。首个准入尝试在历史文件读取前失败，0评价；a02技术修复与独立审阅已完成，source01fc89e5d原生运行且自动观察已接管，0已验收科学结果。固定比较不扩量，不自动追加新学习。[B12结果](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--b12-complete-target-condition-benefit-reverses-on-fixed-development-panels)；[完整咨询、采纳与L0](../../candidates/agent_count_generalization/NOTES.md#2026-09-23--pro-advice-adopted-fixed-b13-ordinary-control-comparison)。 |

**DM1 的关键读法。** B11/B12各一个共同初始化区组，评价物理初值保持相同；四个实际训练策略
不是64个独立训练重复。T6/T8各2.16M/2.88M agent rows和101250/135000次actor与critic优化，
等团队步不等于等曝光或纯N作用。B12的原生J/服务双重反号按旧咨询覆盖分支降低当前配方优先级，
不抹去B11正结果。固定B13保留两份普通T6及两份H6，不按较弱对照或较好H6挑结果，
不把旧策略再评价叫作新训练复现；四者训练日程、目标与工作量的差异仍须保留。
B12已完成计划与运行快照已[退役保存](RESEARCH-agent-count-b12-complete.md)。

