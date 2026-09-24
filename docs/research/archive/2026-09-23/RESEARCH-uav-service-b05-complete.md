# Retired B05 in-flight index excerpts

Retired 2026-09-23 PDT from published main `9c9a5d2c1c1fc482a7215734f6751613b81ddabc`.
Only the DM3 plan/standing and directly affected topic passage are superseded.
Current evidence and decisions are in RESEARCH.md and the append-only direction NOTES.

## Superseded shared topic passage

直接训练目标干预也需要按原目标读取完整用途。S7同初始化N/R的B04仅把真实返航成本的
训练系数2改为4，评价仍为2；首轮物理事实匹配、两层真实存储奖励/GAE与学习更新不同。
固定最终32世界的R−N原生J **+549.393528**，QoS **+.108482684**、成本 **−.129009370**，
支持这个有限实例中服务和风险可同时改善。22个J有利世界之外仍有10个损失，最差−899.031058；
R仍有12个负J和6个零服务世界。同一最终策略在开发8世界却J **−218.433452**、QoS更低、
成本更高；三个已训练开发时点都未出现平均优势。较高平均最低电池也不保证返航约束成本
更低，须保留位置/最差成员风险与低尾部。该面板反号不是额外训练变化，也未识别分布偏移
或优化机制；一个训练对不能支持稳定系数排序。原生评价无充电/切断/耗尽事件，R训练的一次
充电UAV-step不建立恢复能力。此结果保留直接风险学习的机会，不复活旧MSE辅助配方，
也不证明原系数普遍不足。[完整比较、全部世界与成本](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)。

## Superseded direction standing

| `uav_service_auxiliary` | 在 S7 完整共同学习中，怎样把服务改善转成包含返航风险的净收益？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。B04最终R−N J +549.393528与开发−218.433452的反号、全部负尾部及B03失败继续保留。完整咨询后固定B05仅一对新N/R，source3de3e3f71、seed914173、训练成本系数2/4、评价均2；2fits/360k train/192k eval上限。**N已完整验收**：46文件与远端hash一致、全部原始轨迹/两层GAE/检查点独立核验，1fit/180k train/96k eval、124.628160 runner min。最终32世界J **−232.025030**、QoS .216057847、成本 .180828987，14负J、1零QoS，最差J−1796.058763；开发30−0 J +149.725207、服务提高但成本+.035404663，晚期J仍回落。训练3充电UAV步、评价无充电/切断/耗尽，不能声称风险干预已兑现。固定R已在同一源/seed上原生准入运行，观察器已接管；1已验收/1运行，配对增量待完整R。保持两区组×两端点分别读取，不池化反号或自动追加。[N完整验收](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-n-fully-accepted-fixed-r-follows-unchanged)；[R原生运行](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)；[B05前瞻与分支](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-advice-adopted-b05-fixed-independent-training-recurrence)；[B04完整证据](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)。 |

## Superseded DM3 plan

| **DM3：服务收益与风险控制** | B04最终世界的服务/J/成本共同改善与开发世界损失并存；下一判断是该有限学习干预能否在新训练实例中复现。 | **B05固定：2fits/360k train/192k eval上限/552k总交互。** N已完整收取并独立核验，最终J−232.025030、14/32负J；开发自身学习J+149.725207但成本上升，不能由单臂判定风险加权用途。N实测1fit/276k总交互、124.628160 runner min；R已按同一source3de3e3f71/seed914173原生准入，保持原系数和已曝光面板，等待完整配对。分别读B04/B05×开发/最终四格的原生J、服务、真实成本及全部损失世界；净收益消失/反转默认结束此固定配方继续训练，持续面板反号只支持窄范围观察，不选择第三对、默认系数或确认。[N验收与固定R](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)；[前瞻分支](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-advice-adopted-b05-fixed-independent-training-recurrence)；[退役N运行计划](archive/2026-09-23/RESEARCH-uav-service-b05-n-accepted.md)。 |

## Superseded DM3 runtime

B03/B04完整证据保留；DM3的B05 N已完整收取、独立核验和判读。固定R在同一源/seed上原生运行，观察器已接管；1完成验收/1运行，尚无完整N/R配对结论。[N验收及R原生操作](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)。

## Superseded DM3 progress

DM3 的B05 N已完整验收并保留服务—风险取舍，原先固定的R已原生准入运行，等待完整配对。

## Superseded DM3 compute

DM3 的B04两fits已完整验收，360k train/192k eval、286.676430 runner min；B05固定2fits/360k train/192k eval，N已完整验收（180k train/96k eval、124.628160 runner min），R已在4070原生运行，当前1验收/1运行；

## Superseded B05 evidence entry

[S7 B05 N完整验收与固定R运行](candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b05-fixed-r-admitted-on-the-same-source)
