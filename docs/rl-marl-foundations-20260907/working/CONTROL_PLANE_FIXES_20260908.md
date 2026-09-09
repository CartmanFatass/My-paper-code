# 独立审核发现修复（2026-09-08）

授权：用户要求完成修复并通过独立审阅。基线 9e592e9ab；范围为独立报告 C1–C5 及计划两处 runtime 澄清。知识接入计划本身尚未实施，研究保持暂停。

## 修复与检查

| 发现 | 修复 | 验证 |
| --- | --- | --- |
| C1 | Claude agent 接受已发布 CALLER_READY；false 只表示不派发 Codex singleton；未发布仍停止，singleton 请求交回 hub 正确路由 | 现有作者 caller/singleton 子集 13 passed；独立六场景复核 |
| C2 | 将原归档 helper 纳入 .agents/skills/hmasd-chatgpt-pro-transport/scripts，更新两个 Claude 入口，使用同目录 contract 导入 | 新隔离测试修复前因源码缺失 4 failed；修复后 4 passed：干净源复制、完整归档/方向镜像/固定会话、幂等重入、错误请求/摘要与不确定状态拒绝且 registry 不变 |
| C3 | 普通对象委托持续；仅显式接管且缺选择时暂停依赖工作；PRO_BLOCKED 可逆限制与普通预算消费分开，owner item 沿既有 P1/P2/skipped | 同一独立审核者固定六场景基线后复核；Claude 配额、写权限、模型和运行分工未改 |
| C4 | 区域入口改为比例适当的检查与复用；30%为review signal，保留行数预算与冻结例外 | 对照 scope §3/§5、evidence §11.8.6/§11.8.8 与 tests/AGENTS |
| C5 | owner README 指向跨日期 pending CLI，原日期文件用于引用 | 与现有 item.py/server.py 和此前跨日期回归一致；本次不改实现 |

归档 helper 从 CHAIN 定义起的全部运行代码与原临时实现逐字一致，只调整文件说明与同目录导入；不删除原临时文件，不迁移 registry、不重写请求。新用例只接触自身 fixture，未调用真实 registry 或外部服务。两个修改的 Claude skill 均通过 quick_validate（hub 用 Python UTF-8 模式读取）。

计划仅澄清现行 Claude 特有限制与历史材料的区别，以及 Codex 原生路由不覆盖 Claude CALLER_DIRECT。原独立报告保持原文；修复复核另见 INDEPENDENT_REVIEW_CONTROL_PLANE_FIXES.md（复核完成后为准）。

没有运行科学实验、Pro Send、远端运行或恢复存量任务；短控制面测试在本地 Python 3.11 执行。测试 scratch 清理被执行工具策略拒绝（blocked by policy）；已核实三个目录均在本任务 temp/tests 下且不是链接，现保留 claude-archive-red-20260908、claude-archive-green-20260908、claude-routing-20260908，不声明已清理。
