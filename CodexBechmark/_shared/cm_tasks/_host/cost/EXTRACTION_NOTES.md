# 历史 CM 用量提取说明

本目录是筛选支持材料，不是新 benchmark 的模型比较结果。

选取 SQLite `agent_role=hmasd-cm`、HMASD cwd，且创建时间在
`[2026-09-06T07:00:00Z, 2026-09-10T01:00:00Z)` 的 27 个 CM 会话。
只读取已完成 turn，时间窗为洛杉矶 `2026-09-06 00:00` 到 `2026-09-09 18:00`。
明确 thread 列表与 census 队列一致；不是整个项目的成本。

调用现有 skill 的原脚本，未修改 SQLite、rollout、解析逻辑或价表：

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
C:/Users/fires/.agents/skills/codex-task-cost-analysis/scripts/codex_task_cost_analysis.py
summary --role hmasd-cm --unit turn --cost-scope self
--start-local 2026-09-06T00:00:00 --end-local 2026-09-09T18:00:00
--label current_cm --thread-id <明确的CM会话ID> [--format json]
```

16 个会话可由原脚本解析；11 个会话报 `TOKEN_COUNTER_REGRESSED`，没有修补计数器
或把缺失消耗当零。[extraction_status.json](extraction_status.json) 保存完整 27 条结果。
成功的原 JSON 分别保存，汇总仅包含这 16 个会话：
[HISTORICAL_COST.md](HISTORICAL_COST.md) 是原脚本 Markdown stdout 的完整原文，未改写。
这 16 个会话不构成随机缺失样本，不能外推到全体 CM。

汇总给出 111 个已完成 turn，另排除 3 个不完整 turn；均为 Astra/medium。
原脚本自带的 2026-07-26 价表没有 Astra，美元标为 UNPRICED。
记录中的原始汇总 tokens 由原脚本生成；不把它解释为真实账单、能力、质量、每个工程
目标的典型成本，亦不用于推算新测试预算。这里没有计入 reviewer/implementer 团队费用。

先前全项目调用也因一个更早历史会话的计数器回退而失败；随后按预定近期队列逐会话
提取，保留失败清单。队列没有为得到好看的费用而缩小；完整成本仍明确不可得。
后续正式测试使用独立根会话、真实完整终止记录和当时适用价格，参见
[MEASUREMENT.md](../../MEASUREMENT.md)。
