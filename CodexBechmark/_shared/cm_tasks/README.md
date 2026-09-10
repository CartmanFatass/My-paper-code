# CM 测试共用材料

版本 `cm-pair-v1`：可运行实现和离线校准已完成，尚无候选模型比较结果。
主线是 spec 颗粒度、交接详细度和常见范例复用；使用同一顶层 CM 连续完成两题。

完整执行、自动化边界与数据统计见 [操作与统计文档](OPERATING_GUIDE.md)，
入口速查见 [一句话启动](QUICKSTART.md)。两个并列场景：

- [直接实现](../../cm_direct_review/README.md)：当前 HMASD 的 Astra/medium CM + Astra/high 独立 reviewer 基线。
- [委派与复用](../../cm_delegation_granularity/README.md)：用户选择 CM/implementer/reviewer 组合，比较 L0–L3 和 fresh/reuse；默认模型仅作起始建议。

每轮从五个经典任务中抽一题，再从三个非范例中抽一题；默认两题预估难度不同。
seed 与题库字节冻结。任务依据当前 HMASD 代码边界重新构造，都是明确标注的 synthetic
小型修复，不能称为历史 bug 的原样回放或完整生产任务。难度尚未经验校准。

| 材料 | 用途 |
| --- | --- |
| [OPERATING_GUIDE.md](OPERATING_GUIDE.md) | 两项测试全过程、逐项自动化、报告判读、跨轮统计与异常处理 |
| [QUICKSTART.md](QUICKSTART.md) | 独立 session 入口、默认值、自动报告和维护命令 |
| [SPEC_DESIGN.md](SPEC_DESIGN.md) | 比较问题、分组与复用成本 |
| [DESIGN.md](DESIGN.md) | 当前两题协议、角色、质量和冻结边界 |
| [HANDOFF_LEVELS.md](HANDOFF_LEVELS.md) | L0–L3 的累积信息 |
| [patterns/](patterns/README.md) | 五类可复用模式与三个可执行局部例子 |
| [MEASUREMENT.md](MEASUREMENT.md) | 真实会话、全链条成本与测量局限 |
| [_host/IMPLEMENTATION.md](_host/IMPLEMENTATION.md) | 维护者实现、离线检查和剩余实测范围 |
| [_host/EPISODES.md](_host/EPISODES.md) | 两题抽样和固定事件；主持材料 |
| [_host/MATRIX.json](_host/MATRIX.json) | 可选择配置；不自动批量启动 |
| [_host/task_bank/README.md](_host/task_bank/README.md) | 题库、来源、难度与离线校准；主持材料 |
| [_host/census/CENSUS.md](_host/census/CENSUS.md) | 先前历史筛选，不是当前模型比较结果 |

被测 CM 只读本轮分发的材料；维护者阅读过隐藏答案的 session 不能作为候选。
公共库首次制作成本仍为 unmeasured，不能据此声称净节省或回本。
