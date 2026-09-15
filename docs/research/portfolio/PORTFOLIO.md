# 科研 Portfolio 报告

> OWNER_OPERATIONAL_PAUSE 2026-09-15：所有者要求各 DM 完成已接受任务后安全暂停。四条链均已完成当前对象、保全证据并停止；生命周期和席位未改变。统一恢复入口见 [handoff](handoffs/2026-09-15-owner-operational-pause.md)。

当前工作集为 **4 个占用方向、0 个预留、0 个空缺**。ACVC、FOLR 与 TRDL 延续各自链；所有者于 2026-09-14 直接恢复 FSD 为第四条并行链，不挤占前三个方向，也不等待 Portfolio 重复准入。四个方向均由原生 Astra/max DM 管理完整生命周期。实时执行细节见[实验跟踪](EXPERIMENT_TRACKING.md)。

| 方向 | 当前科学位置 | 当前 producer / 下一事件 |
| --- | --- | --- |
| acvc | [ACTIVE/MEDIUM/recasts2](../candidates/acvc/DIRECTION.md)。private C/M 单block完成，F−M +.02343965 J；限于一个训练block、22/64 adverse worlds，缺tuned headroom。em:acvc:convergence PRO_FINAL：再做一个不变的 C/M block（A，k=1）。 | **Claude hub 驱动**；0 producer；b02 wrapper 已备（`7bd04236d`）；Portfolio 13:19Z 授予一个 block（G，`decisions/2026-09-15-acvc-one-block-replication-grant.md`）；C fit 13:26Z 启动，M 随后；交接 `HANDOFF_2026-09-15_post_cm_decision.md` |
| vap_folr_core | [ACTIVE/MEDIUM](../candidates/vap_folr_core/DIRECTION.md)。两块fresh A−G为 −5.830625/−.109921875，均未重现旧A正优势；保持MIXED_BLOCK_PATTERN。 | **Operationally paused**；0 learner/Monitor/Transport。恢复从 `HANDOFF_20260915_AUGMENTATION_REPEAT_OWNER_PAUSE.md` 继续，next discriminator刻意未选。 |
| tail_return_distributional_learning | [ACTIVE/MEDIUM/recasts0](../candidates/tail_return_distributional_learning/DIRECTION.md)。B02独立pair lower-tail Q−S −.00241972 J（INSIDE_MEI）；B01正结果独立保留。 | **Operationally paused**；0 fit/provider/child。恢复从 `TRDL_OWNER_PAUSE_HANDOFF_20260914.md` 继续；B02结果Pro review未启动。 |
| flexible_skill_duration | [ACTIVE/HIGH](../candidates/flexible_skill_duration/DIRECTION.md)。8/8 factorial originals完成；主均值+.02910478 J但两block符号混合、n=2区间很宽。Portfolio S 决策（baseline × interruption B01，FLAT/D1280/I1280 × 4 blocks）已应用。 | **Claude hub 驱动**：D1280/I1280 八个 fit 于 2026-09-15 11:52Z 在 hmasd-wsl-node 运行（`dc4dbdfcd`）；Portfolio 12:55Z 确认 FLAT k=10（`decisions/2026-09-15-fsd-flat-k-correction.md`），首个 FLAT fit 13:02Z 启动，其余按槽位释放依次启动；交接 `HANDOFF_2026-09-15_baseline_interruption.md` |

## 当前协作边界

- DM 自主完成方向科学、实现、检查、审查、Transport、Monitor、结果 intake 和已授权延续；Root 不对这些步骤逐项审批。
- Direction Convergence 处理方向内科学收敛；`portfolio:cross_direction` 处理投资、优先级、生命周期、容量、融合/分离和注册。只有完整 Portfolio 决定或所有者直接指令才能 PARK/CLOSE 整个方向。
- Root 处理 DM 原生事件、共享依赖、主分支集成和当前记录。Root 使用事件驱动的 `wait_agent`，不以短轮询或 ACK 作为推进门槛。
- vacancy 请求 `2026-09-14-mgtap-park-vacancy-replacement-01` 已完整归档并应用：选择 TRDL，占用第三席；Root Transport 已结束。新的 vacancy 只有在未来正式 Portfolio/owner lifecycle 处置释放席位时才产生。

## 已 PARK / 未占用方向

| 方向 | 当前登记 |
| --- | --- |
| metric_ground_transport_allocation | [Portfolio 可逆 PARKED/MEDIUM](../candidates/metric_ground_transport_allocation/PARK.md)；DENSE default、optional COND、8252/8214 正证据、8253 与8254反证全部保留；0新拟合、无RECAST/CLOSE，已释放1席。 |
| roster_consistent_latent_exploration | [Portfolio 可逆 PARK](../candidates/roster_consistent_latent_exploration/PARK.md)；B10/B12 固定先验、B11 缺失、E01 面板、B13 结果和恢复条件均保全。 |
| degraded_incumbent_shadow_handover | [PARK](../candidates/degraded_incumbent_shadow_handover/PARK.md)；保留 B09、REPLACE/BYPASS 边界和历史证据。 |
| ucope | [PARK](../candidates/ucope/PARK.md)；保留 reactive renewal 结果、反证和重新研究条件。 |
| learned_counterfactual_agent_credit | [PARK](../candidates/learned_counterfactual_agent_credit/PARK.md)；保留 B03 负结果及基线/学习证据。 |

历史 pause 文件、旧分配和结束的对象仍是证据，但不作为当前 dispatch 路由或生命周期状态。新的判断从各 DM 的最新 `DIRECTION.md`、intake、固定 Pro packet 和本报告读取。运行时长参考值不自动触发停止、上报、PARK 或额外授权。
