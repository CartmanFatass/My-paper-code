# Superseded B04 next-investment plan, 2026-09-23

Retired from [RESEARCH at main cfb058e5974d0f71304631659a6c8a0742f49abf](https://github.com/CartmanFatass/My-paper-code/blob/cfb058e5974d0f71304631659a6c8a0742f49abf/docs/research/RESEARCH.md) after the complete advice was verified and read, the DM fixed exactly one new N/R training pair, and B05 N was natively admitted. These are only the owned standing and affected plan excerpts; current controls and other directions are unchanged.

## Previous standing

| `uav_service_auxiliary` | 在 S7 完整共同学习中，怎样把服务改善转成包含返航风险的净收益？ | exploring | Codex DM (independent session) | 直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。**B04 N/R完整验收**，source914fc4843，训练返航成本系数2/4、评价均2，同初始化与首轮事实。最终32世界N/R原生J −496.301830/+53.091698，R−N **+549.393528**，QoS +.108482684、成本 −.129009370，22胜10负，最差相对损失−899.031058；平均/P10最低电池改善，R仍12个负J及6个零服务世界。同一最终策略在开发8世界却J −218.433452、QoS降低、成本更高，6/8受损；不抹去面板反号或提升为默认系数。2fits/360k train/192k eval，286.676430 runner min；全部轨迹、两层GAE与检查点核验，0运行/未收旧结果。B03两块辅助收益反号及MSE反证继续保留，旧配方关闭。下一聚焦选择为新N/R训练对的复现，或旧策略更宽世界评价；0后继fit，非确认。[完整B04与所有世界](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)；[下一投资问题](../../candidates/uav_service_auxiliary/NOTES.md#pro-question-2026-09-23-b04-risk-gain-next-discriminator)；[B03完整证据](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)。 |

## Previous plan

| **DM3：服务收益与风险控制** | 真实风险重加权在B04最终世界提高服务与原生J，但同一策略在开发世界反向，不能把有限正收益当通用改进。 | **B04完整验收**：最终R−N J +549.393528、成本 −.129009370，22/32 J更高；开发update30 J −218.433452且成本更高。2fits/360k train/192k eval、286.676430 runner min，无运行或待收旧结果。下一判断比较新独立N/R训练对（候选2fits/552k总交互）与固定策略新64世界（候选0fits/192k eval）的信息价值；聚焦Pro建议可改变选择，尚未启动后继。保留所有负尾部、低绝对服务与每臂n=1；不扫系数、选checkpoint或自动确认。[完整结果](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)；[聚焦问题](../../candidates/uav_service_auxiliary/NOTES.md#pro-question-2026-09-23-b04-risk-gain-next-discriminator)；[退役运行计划](../../archive/2026-09-23/RESEARCH-uav-service-b04-complete.md)。 |

## Previous runtime statement

B03 完整证据保留；DM3 的B04两臂已完整收取、独立核验和配对判读，原生操作全部结束；当前聚焦正最终/负开发读数后的下一投资，[完整证据与判断](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)。

## Previous progress phrase

DM3 已完整读取B04并聚焦复现与世界敏感性的下一投入。

## Previous compute statement

DM3 的B04两fits已完整验收，360k train/192k eval、286.676430 runner min，无当前训练或已选后继；

## Previous evidence entry

[S7 B04完整风险干预](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-complete-native-final-gain-with-contrary-development-worlds)、
