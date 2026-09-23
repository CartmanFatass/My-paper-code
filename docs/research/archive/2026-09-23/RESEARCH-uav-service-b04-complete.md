# Superseded B04 service-risk running plan, 2026-09-23

Retired from [RESEARCH at main b512311aff062034799414338bf69f1043a710d6](https://github.com/CartmanFatass/My-paper-code/blob/b512311aff062034799414338bf69f1043a710d6/docs/research/RESEARCH.md) after both B04 operations and the complete paired reading were accepted. Only the owned standing and affected running-plan excerpts are retired here; links are rebased. Current controls, ownership and the completed frozen experiment remain unchanged.

## Previous standing

| `uav_service_auxiliary` | 在 S7 完整共同学习中，怎样把服务改善转成包含返航风险的净收益？ | exploring | Codex DM (independent session) | 文献第 1 项；直接 DM task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`，host `local`，`gpt-6-astra` / `max`；checkout `/home/fires/.codex/worktrees/d319/hmasd-wsl`，branch `codex/uav-service-predictive-control`。固定 B03 D/S/G×两块六 fits、两次共同端点回放全部完整验收，source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`。两块最终 S−D J **+24.585407 / −16.825601**，G−D **+117.896434 / −24.945921**，S−G **−93.311027 / +8.120320**；收益均未复现，G服务增加但成本取舍转坏，保留负尾部。共同回放中G首块两类MSE最高、第二块最低，均不能代替原生用途。按已覆盖该分支的完整Pro建议关闭当前配方，0追加/确认，无旧操作待收。B04固定N/R两臂，训练成本系数2/4、评价均为2。N已完整验收：1 fit/180k train/96k eval/134.635283 runner min；最终32世界原生J -496.301830，QoS .158025、返航成本 .239923，20/32原生J为负；无充电/切断/耗尽事件。全部原始轨迹、37个记录中的文件hash、两层优势和检查点已独立核验；开发update30 J +50.842834与最终世界不同，不作额外退化解释。固定R已在同一源914fc4843/seed914021上原生准入运行，仍待完整结果与逐世界配对，不改变系数、端点或曝光。[N完整验收](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-n-fully-accepted-fixed-r-remains-the-next-fit)；[R原生运行](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-fixed-r-admitted-on-the-same-source)。方向与lead不变。B03六fits共769.038846 runner min，零更新共同回放另1.693106 min。[完整结果与判断](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)；[G2验收](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-block-g-accepted-and-fixed-common-replay-bound)。 |

## Previous plan

| **DM3：服务收益与风险控制** | G 的服务提升在 S7 两块都出现，返航约束成本改善没有复现；下一问题是怎样把服务转成完整用途。 | **B04已固定并开始**：原生N与训练时额外扣除 `2×真实返航约束成本` 的R，共同新种子914021；两层原生回报/优势均变化，原生评价系数仍为2。每臂180k，**2 fits / 360k train / 192k eval上限**；开发937001–8在0/10/20/30，最终938001–32只读更新30。N已完整收取与独立验算：最终J -496.301830、QoS .158025、成本 .239923，20/32原生J为负，134.635283 runner min。R已按同一源和固定合同原生准入，保持句柄观察；等待完整R后读取配对。看原生J、QoS、返航成本、电量低尾与逐世界损失；不选最佳checkpoint或调系数。原分项critic只保留为有理由时的替代。[N验收与固定R运行](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-fixed-r-admitted-on-the-same-source)。 |

## Previous runtime statement

B03 完整证据保留；DM3 的固定B04 N已完整验收并保留负尾部，R已在同一源上原生准入运行；[当前句柄与读取范围](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b04-fixed-r-admitted-on-the-same-source)。

## Previous progress phrase

DM3 收取固定风险干预比较。

## Previous compute statement

DM3 的2 fits已固定，N已验收、R已原生准入；

## Previous evidence entry

[S7 完整六格](../../candidates/uav_service_auxiliary/NOTES.md#2026-09-23--b03-second-common-replay-accepted-and-current-recipe-closed)、
