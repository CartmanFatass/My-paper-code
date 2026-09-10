# 控制面 C1–C5 修复独立验收

**结论：通过，限本次修复批次。C1–C5 均已闭合，没有新的源码或计划范围阻断项。** 知识接入计划本身尚未实施，研究暂停仍有效；本结论不授权科学调用、Pro Send 或存量任务恢复。

审核者：复用原独立 Astra/max。基线为 `9e592e9ab5cce669866e988c5032e5b3a7782116`。修复前六场景从原审核基线 `c463c03766f88cfc7c37d978bf9583cabfe52e3c` 的 Git 对象读取；验收针对父级提供的当前工作区差异。审核范围为六个已跟踪修改文件、新归档 helper、新聚焦测试及 [修复记录](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/CONTROL_PLANE_FIXES_20260908.md)，未全量复读控制面。

## 同一组六场景

下表除运输状态自身约束外，都以该动作原已获授权为前提；实际 PAUSED 始终优先。

| 场景 | 修复前实际条款 | 当前结果 |
| --- | --- | --- |
| 已发布 CALLER_READY | producer 要交 Sonnet；consumer 却因 false dispatch 判作无 payload 停止。 | 通过。Claude agent 接受已发布 caller-direct 的精确 prompt/binding；false 仅取消 Codex singleton 派发。 |
| TASK_NOT_PUBLISHED | producer/consumer 均要求先发布并 bind，不能 Send。 | 通过。拒绝行为保留；缺 payload/binding、错误状态也先返回 hub。 |
| owner 只问状态 | hub 的 owner-present 分支要求等待回复，与委托持续冲突。 | 通过。明确普通问题/状态请求不接管对象；既有暂停指令仍控制。 |
| owner 显式接管对象 | 未给选择时等待适当；已有选择不应再确认。 | 通过。遵从已给选择，只在选择缺失时暂停依赖工作。 |
| PRO_BLOCKED 暂定对象 | reversible 限制适用，但未区分特殊暂定标签和普通委托。 | 通过。明确 PRO_BLOCKED / LOCAL_PROVISIONAL、仅可逆、待重试/审计置首及归档决定在干净边界替代。 |
| 普通已授权预算消费 | 全局 reversible-only 可误拒绝声明预算内的正常研究动作。 | 通过。允许原授权及预算内执行，特殊暂定限制不再泛化；没有新增调用或放松冻结对象。 |

对应当前入口：[Claude Transport agent](C:/Projects/HMASD/.claude/agents/hmasd-pro-transport.md:17)、[Claude hub](C:/Projects/HMASD/.claude/skills/hmasd-research-hub/SKILL.md:78)。Codex singleton 请求明确交回 hub 正确路由，Claude operator 不接管该请求。

## C1–C5 关闭依据

| 发现 | 独立验收事实 |
| --- | --- |
| C1 | 上述已发布/未发布/错误路由分支现在一致；Claude skill 仍生成 CALLER_DIRECT/CALLER_READY，未修改 renderer 或请求正文。 |
| C2 | [归档 helper](C:/Projects/HMASD/.agents/skills/hmasd-chatgpt-pro-transport/scripts/archive_delivered_claude_request.py) 已进入本批待提交源码集合；两个 Claude 调用均转向新路径。它仅依赖同目录 tracked transport_contract 和标准库，不再依赖 ignored session 实现。独立比较确认从 CHAIN 开始的全部运行正文与原 temp helper 一致。 |
| C3 | 对象委托、显式接管、特殊暂定与普通预算消费已分开；普通选择留 intake/audit，P1/P2 与 skipped 处理清楚。Claude 容量、模型、运行分工和逐文件写入边界未改。 |
| C4 | [experiments/AGENTS.md](C:/Projects/HMASD/experiments/AGENTS.md:23) 改为比例适当的聚焦检查与复用，30% 是审查提示；2,000/600 行预算和命名冻结例外保留。 |
| C5 | [owner README](C:/Projects/HMASD/docs/research/portfolio/owner/README.md:147) 指向跨日期 pending CLI；日期文档只承担原文引用，mark-answered 在应用后执行，与现有实现一致。 |

计划仅改两处范围说明：区分活跃 Claude 缺陷、现行 runtime 例外和历史资料；将 source/parent/operator 描述限定为 Codex 原生路由，并保留 Claude CALLER_DIRECT/hub/Sonnet 映射。R1–R4、逐引用 SHA 设计、暂停和科学冻结边界未改变。

## 验证及交付边界

独立执行了运行正文比较、两个新增 Python 文件的无落盘语法编译、目标差异 whitespace 检查及旧 helper 调用引用检查。运行正文 SHA-256 为 `0bc443f4e55a92c3438f2a0300f3c7b2efa77760ee818edee159a2d0adb6bce5`；新 helper 文件 SHA-256 为 `4184d5766ccaf39d41863a000ebdc34d253793db459d6806e7058ed63cca10c7`。

已全文检查 [新测试](C:/Projects/HMASD/tests/skills/test_claude_archive_delivery.py)。fixture 只复制 helper 与 contract 到独立源码目录，覆盖成功归档/方向镜像/会话及消息身份、幂等重入、错误请求/摘要/不确定状态拒绝且 registry 字节不变。父级提供的结果为：修复前因缺少源码 4 failed；修复后 4 passed；现有 caller/singleton 作者子集 13 passed；两个 Claude skill quick_validate 通过。本次独立验收检查了这些测试的实际覆盖，没有重复运行测试或操作真实 registry。

父级仍负责显式路径提交并推送，包括新增 helper、测试和两份本批记录；当前验收不把尚未提交的文件称作已发布源码。测试 scratch 的清理被执行工具策略拒绝，三个自有目录保留并已在修复记录中列明；不影响源码接受，也不宣称清理已完成。本审核未尝试删除父级目录、未改源文件、未提交。

补核：计划第 3 行与 §6 第 1 步准确区分已完成的 v3 计划审核、C1–C5 修复验收和尚未实施的知识接入；两处状态更新不改变上述审查结论或验证事实。
