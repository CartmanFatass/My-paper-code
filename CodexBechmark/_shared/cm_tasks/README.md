# CM 测试共用材料

状态：设计与历史筛选；尚未冻结可运行代码题包，未启动候选模型比较。
维护基线：HMASD `0fae6912f20a8322376b6289fca3ead4ef2a56ac`，2026-09-09 PDT。

**主线是 spec 颗粒度、交接详细度与常见范例的复用**；模型比较用于验证其适用范围。
先读 [SPEC_DESIGN.md](SPEC_DESIGN.md)。本组材料服务两个并列场景：

- [cm_direct_review](../../cm_direct_review/README.md)：CM 直接实现，独立 reviewer；比较角色模型组合。
- [cm_delegation_granularity](../../cm_delegation_granularity/README.md)：保留 CM 和 reviewer，比较 implementer 模型与委派说明颗粒度。

主测试单位是一条**同一 CM 持续负责的工作流程**，包含连续代码问题、真实子代理交互、
验收、回执和杂务。单题冷启动用于诊断，不代替主测试。

| 材料 | 用途 |
| --- | --- |
| [SPEC_DESIGN.md](SPEC_DESIGN.md) | 主研究顺序、8 个 spec 策略、首次/复用成本与工作流产出 |
| [patterns/](patterns/README.md) | 五类可复用 spec 候选与三个可执行微例子 |
| [DESIGN.md](DESIGN.md) | 共同控制条件、连续上下文、质量判定与执行方式 |
| [HANDOFF_LEVELS.md](HANDOFF_LEVELS.md) | 累积式 L0–L3 委派策略与边界 |
| [MEASUREMENT.md](MEASUREMENT.md) | 全链条成本、失败、时间与历史提取局限 |
| [_host/census/CENSUS.md](_host/census/CENSUS.md) | Luna 初筛及逐会话溯源；主持材料 |
| [_host/EPISODES.md](_host/EPISODES.md) | 工作流程选材与投递次序；主持材料 |
| [_host/MATRIX.json](_host/MATRIX.json) | 计划比较的配置，不是已运行结果 |
| [_host/cost/EXTRACTION_NOTES.md](_host/cost/EXTRACTION_NOTES.md) | 历史用量提取的覆盖范围和失败清单 |

题包、两个场景各自的配置/运行记录保持分离；只共享版本固定的输入与验收标准。
实际测试仍安装到 `C:\Projects\CodexBechmark`，不在 HMASD 生产目录启动被测 CLI。
历史筛选中的 session 创建时 Git SHA 不是自动可用的题目起点；制作题包时需核对变更前源码。

本次交付不声称存在新的 CM runner。后续代码题包与机械投递器按 DESIGN 的接口制作，
不会让用户逐条粘贴事件。已有 root_delegation runner 与数据不受影响。
