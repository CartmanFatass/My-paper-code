# 控制面独立审查与修复记录

本次审查响应所有者要求：重审控制面 skill、文档和 subagents，增加 Astra/max
独立审阅，并清除历史操作说明造成的冲突。本文是审查证据，不是工作流入口。

## 范围与审阅方式

执行者在独立 worktree `HMASD-root-transport-routing` 修复；独立审阅者为
`control_plane_independent_audit`，模型 `gpt-6-astra`、推理强度 `max`。
审阅者只读检查，不实施修改、不操作 Pro、不派生子代理；首次审阅与修复复查分开。

检查范围包括 AGENTS.md、Codex 配置和全部 9 个原生角色、6 个 HMASD skill 入口及
相关参考文档、Root/Monitor/通信/GitHub 协作指引、Owner 介入面以及跨运行时边界。
首次审阅基线为 main `373d18720` 和先行修复 `ff4373d1e`；下列位置描述该基线的问题。
没有改动科学卡片、实验预算、比较器、既有 Pro 请求正文或响应、角色模型或权限。

## 独立审阅确认的问题与处理

| 编号 | 问题及影响 | 修复 |
| --- | --- | --- |
| 1 · P1 | PROJECT_MAP 指向的 SIBLING_COMMUNICATION 仍要求独立 Luna/low Monitor，并称 Root 无心跳，与当前 Root 配置冲突。 | 通信入口只保留当前原生消息、app 寻址与 Root 接管；旧追踪器说明和实测记录完整移入 archive。 |
| 2 · P2 | 正式 GitHub 指引加载流程草案，包含已完成的试点、恢复测试和再次实施任务，并把科学职责写作 Root/DM。 | 现行顺序及部分成功处理收敛到 GITHUB_RESEARCH_COLLABORATION；草案归档，作者和 intake 明确为 Portfolio/DM。 |
| 3 · P2 | 附件参考仍称附件为默认模式、要求渐进迁移及逐请求心跳；生成说明混淆本地回执与科学 intake。 | 用简短的 attachment-delivery 替换整份旧参考；沿用当前 Root 和共享心跳；生成器分别说明本地完成与 DM/Portfolio intake。 |
| 4 · P2 | validate_request 缺省进入 legacy，允许缺失来源、父任务和执行者；bind CLI 有同类默认值。 | 新请求验证与绑定 CLI 要求当前显式节点和路由；低层历史状态读取及归档兼容保留。 |
| 5 · P2 | Owner skill、DM、AGENTS 与 README 表格仍要求创建 P3/P4 项，但 CLI 已返回 skipped、不生成文件。 | 全部入口统一 P1/P2；普通决定、预测、技术事实、简报保存在 card/intake/audit，不另建审核项。 |
| 6 · P2 | 外包技能把独立审查也纳入固定 Terra 实施契约，UI 仍宣传“指定会话”。 | 触发范围限于外包实施；独立审查遵循所有者指定模型/职责；UI 改为原生 Terra 实施代理。 |
| 7 · P2 | Semantic Implementer 要求每次语义修改都测量成本定律，超出 scope spec 的按任务要求范围。 | 成本与资源测量仅在冻结任务要求时实施，保留所要求的测量与科学约束。 |
| 8 · P2 | Root 指引要求 app 消息不带模型覆盖，Author 又要求 Pro 派工显式 Luna/xhigh。 | 明确普通证据/接管/回执不覆盖模型；新 Pro 派工使用 Author 已生成的配置。 |
| 9 · P3 | conversation_policy 和 AGENTS 仍描述一次性 cutover/创建新会话。 | 当前模式描述为串行复用；保留原记录的完整会话排除政策，明确观测清单不穷尽排除范围。 |
| 10 · P3 | 从 skill 拆出的附件参考含 references/references 路径及失效的科学工具路径。 | 替换参考并修正入口链接；检查当前 Markdown 本地链接。 |

补充修正：Reviewer 和 tests/AGENTS 按声明的执行节点/拓扑判断可达风险；测试规则
对齐已有 scope spec，不因启动边界重复 smoke；AGENTS 的 Claude 附录转向当前 CLAUDE
规则，保留 Claude 自己的模型、容量与操作路径。控制面测试明确使用已安装的 Python
3.11+（tomllib），科学测试仍使用原科学环境。

Owner/Portfolio skill 不再把一次 CBSC/N3 实施事项称为“最新指令”，而直接引用当前
AGENTS §4.7 的授权范围与 CLI trace 程序。新请求的回执就绪摘要也与实际 outbox 一致：
执行者等于父任务时为本地完成。实际 outbox 行为未改变。

## 验证及限制

- Transport、Author、绑定、外包相关测试：128 passed；包括缺失/legacy 节点拒绝、
  不写 registry 的 CLI 拒绝、GitHub 绑定后正文不变、Root 直执行/普通派工和本地回执。
- Owner 控制台测试：19 passed。现有文案测试原来强制 skill 提及停用 kind 并要求 DM
  重复 CLI 指令，已改为检查维护中的 kind 和技能引用；CLI 的 P1/P2 分类逻辑未改。
- 修改的 5 个 skill 通过 quick_validate；14 个 Codex TOML 成功解析；25 个当前
  Markdown 文件的本地链接检查未发现断链。
- 对照 `ff4373d1e`，9 个角色的 model、reasoning effort、sandbox 和 approval 字段一致。
- 归档的两份文档与原 Git 内容一致（仅按仓库换行规则比较）；已接受科学材料未修改。
- 本次检查不发送新 Pro 请求、不运行科学实验、不证明模型此后绝不会偏离指引。
  历史 schema/兼容函数保留用于读取既有证据，不再作为新请求的默认入口。

初始扩大检查发现的 1 项失败是 Owner 文案测试要求停用 kind；修正后 19 项通过。
Windows 默认编码使通用 skill 检查器最初无法读取中文，使用现有 Python 的 UTF-8
模式后通过，没有修改检查器或安装依赖。

## 历史记录位置

- [原通信与 tracker 记录](../../archive/control-plane/20260904_SIBLING_COMMUNICATION.md)
- [原 GitHub 试点与迁移草案](../../archive/control-plane/20260905_GITHUB_PRO_COLLABORATION_WORKFLOW_DRAFT.md)

现行工作流不加载这两份归档。保留时间、旧标识、已接受请求和冻结科学例外作为证据，
与要求代理再次执行旧流程不同。

## 独立复查结论

同一 Astra/max 独立审阅者复查相对 `ff4373d1e` 的完整改动及新增文件，返回：
“No material findings remain in the current diff”。确认当前路由、共享心跳、本地回执、
P1/P2 指引一致，会话排除范围保留，未发现未经授权的科学、模型、推理强度或权限变更。
审阅者独立核对两份归档与原主工作区字节相同，检查了验证器、绑定、生成器和回归测试，
确认历史状态 helper 保留。其复查为只读，未重复测试套件，未操作线上服务。
