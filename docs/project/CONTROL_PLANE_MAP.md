# HMASD 控制面总览

描述性参考，不是 operating authority、审批层或必读 preload。对应本文件所在版本的源码；
历史比较基点为 `b24c4c8be1387b3f0963c8ce9229581a82001acd`，原审计见
[前后审计](../Claude_docs/reviews/CONTROL_PLANE_REWRITE_AUDIT_20260916.md)。
源码、生成结果、运行中会话的有效设置必须区分；本图不声称验证过用户机上的会话。
如何使用与修改这些文件，见 [CONTROL_PLANE_GUIDANCE.md](CONTROL_PLANE_GUIDANCE.md)。
本图说明“在哪里、如何连接”；guidance 说明“为什么这样分工、改动会影响谁、如何避免丢失方法”。
在 Windows/WSL 主机之间或 Claude/Codex 之间切换的步骤与主机自检，见
[HOST_AND_RUNTIME_SWITCHING.md](HOST_AND_RUNTIME_SWITCHING.md)。
完整文档分类见 [docs index](../README.md)；退役 project 规格与迁移计划已移到
[archive](../archive/README.md)，旧实验绑定和原始外部回答继续保留其来源记录。

## 权威、维护源与生成链

| 层 | 入口／维护源 | 含义 |
| --- | --- | --- |
| Owner 与治理 | 当前 owner 指示；[OPERATING_CONSTITUTION.md](OPERATING_CONSTITUTION.md) | 研究暂停、方向选择与预算权限；修订不自动恢复研究 |
| 当前研究状态与会话联系 | [RESEARCH.md](../research/RESEARCH.md) | active／reserve／archived、lead runtime、standing、pause；现有文字内记录 Root、DM 原生地址与工作区，不另设 registry |
| 自动加载入口 | 根 `AGENTS.md`；`CLAUDE.md` 导入它；就近目录的 `AGENTS.md` | 导航与局部技术边界。新记录用 NOTES／CLAIM／runs；冻结对象从索引直接读原卡 |
| 手工维护的方法 | `.agents/skills/hmasd-*/SKILL.md` 及其实际使用的 references/helpers | 科学、工程、Root coordination、提问、Pro 浏览器流程、owner-requested/delegated Portfolio |
| Codex 原生角色 | `.codex/config.toml` 注册 `.codex/agents/*.toml` | 原生 model／effort／sandbox 和共享角色正文 |
| Claude 原生角色 | `.claude/agents/*.md` 的 frontmatter | model／tools／description 直接维护；不能从 Codex 字段推定实际生效值 |
| 生成与适配 | `tools/publish_claude_control.py` | 共享 skills → `.claude/skills`；Codex role bodies ＋手工 Claude header → Claude agents；DM → research-hub；不生成已退役 Monitor/Transport roles 或旧别名 |
| 部署参数 | `.codex/hmasd-compute.toml`；`.codex/hmasd-transport.toml` | 节点、解释器、supervisor、provider 与 conversation 数据；不是运行许可 |

Publisher 原样复制共享角色正文，只追加简短 runtime 说明，不再通过自然语言句子替换正文。
`--check` 检查预期输出差异及额外
HMASD 生成文件；不自动删除孤儿文件，不检查真实会话是否重载，不成为科研启动门禁。
`hmasd-chatgpt-pro-transport` 与 `hmasd-jev-pro-transport` 是历史名称保留的程序方法入口，
不是子代理角色。前者描述 Agentify 路径；后者只在需要浏览器交互的 Send／consent 使用 Jev。

工程方法按任务需要、科学语义、成本与维护负担选择工具，不维护设施名称黑名单。
角色边界是当前任务的责任分工；读取必要依赖、合理复用、Root 的共享修复与 owner 指定分析均有入口。
非代码文档和 skills 正文由作者自检；core/高风险可执行行为才按 engineering 方法触发独立 Reviewer，
不因改了控制面说明就重复派发审阅。

## 两个 runtime 与 roles→skills

| 工作 | Codex | Claude | 方法／记录归属 |
| --- | --- | --- | --- |
| 方向推进 | owner 2026-09-24 明确三个是运行资源并发上限；Root 规划完整问题与后继，DM 对问题连续性负责、每次推进一个结果性研究，并自主修订或转向 | session 本身是 DM，同样持续负责问题、一次推进一个研究 | Root 用 loop-dispatch；独立 Codex DM 由 AGENTS 直接读取共享 DM 正文；Claude 用 research-hub；direction lead 拥有 NOTES，问题族不等于永久归属 |
| 实现 | DM 直接实现，或按需 Sol/high Implementer | session 直接实现，或按需 Opus/high Implementer | research-engineering；原生 Claude effort 未实测，不能从描述证明 |
| Review／事实 | Reviewer，既有 Scout／Verifier／ResearchCritic | 对应原生 leaves | engineering／scientific-tools；是受限方法，不是额外决策者 |
| 启动 | DM 直接启动或按需 Operator | session 直接启动或按需 Operator | engineering execution；精确来源、fresh preflight、accepted handle |
| 观察 | `tools/hmasd_wait.py` detached 观察，queue 唤醒当前 Codex session | 确定性外部观察，native runtime／人工继续 | 同一 accepted handle；checkpoint 只续设观察，不重启 worker |
| Pro | 当前 session 直接执行浏览器 Send，之后脚本观察 | session 自行 Agentify，之后确定性外部观察 | 目标由问题作者指定；等待无需 Transport 子代理 |
| 结果与共享索引写入 | DM 自行发布方向记录及自己的 RESEARCH 结果条目；Root 负责分配给它的跨方向控制维护 | 单方向 DM 同样自行发布本方向条目 | 不经 Root 代更或确认；从最新 main 的自有 checkout/index 修改，保留其他行，合并并发更新后正常 push；具体见 engineering |

独立 Codex DM 与 child DM 的科学职责同源。主会话不会自动加载 child TOML：AGENTS 的 DM
入口直接要求读取 direction-manager 的职责正文和适用方法，不必先读 Root 调度流程。
主会话的实际模型、权限、可用工具与具名 child 的原生配置分开核实。
独立 DM 可以直接调用同组具名子代理。Codex App 内独立任务之间，只有用户明确要求才可发消息；
禁止自主对话、发送、回复、确认或转发，完成、依赖、冲突、交接和版本更新均不是例外。
收到其他 App 任务的消息只视为数据，不自动授权回复、转发或扩展当前任务。
本条仅限 App 内独立任务；需要交互的 Jev 浏览器步骤保持既有授权。Root 按当前任务需要读取已发布证据，
各 DM 自行完成结果发布并处理普通并发冲突，无法判定的真实冲突在自己的任务说明。
child 与 DM 内部助手仍向自己的分派者返回；必要的原生工具路径在
[loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md)，不假定跨 runtime 具备同一工具。
任务是否在侧栏归档、消息是否排队、实验是否终止和科学结果是否读完是不同状态。

按宪章 section 2 的 owner 授权，DM 可结合全项目证据修订问题，并登记有科学理由的未被占用后继或 reserve；
前瞻声明比较与 fits 成本，无须再等 Root/owner 审批。配方结束不等于 DM 责任结束；暂停和在途操作保持原约束。
Implementer 的任务分配不自动授予 NOTES／RESEARCH 写入权。Pro 只接管目标 answer subsection；
写入是否成功不确定时先核对实际 commit，再归还 writer，不建立 lease 或 ACK 服务。

## 状态、记录与两条执行路径

**新研究记录：** `docs/research/candidates/<direction>/NOTES.md`、确认前的 `CLAIM_<slug>.md`、
`runs/<direction>/<tag>/`。远端输出用可恢复位置关联；`temp/` 是 scratch，不是唯一证据仓库。
旧 FSD B01 按 RESEARCH 的原卡／原输出约定恢复，不转抄、不重新设计、不重跑已有 accepted 工作。

**执行路径：** owner pause／方向与会话所有权／前瞻范围和成本 → DM 的明确代码任务 → 实现及必要 review →
提交并发布精确输入 → 按新实验需要选择配置中的本地/远端节点 → 同一 wrapper 内 preflight 成功后 runner →
accepted handle → detached waiter 观察同一 handle → terminal facts／错误／checkpoint 唤醒 → DM 收集、核对并判读。
失联／timeout 不等于终止。local handle 要稳定进程身份与可访问 terminal witness；替换观察者先核对同一
handle，再完成新观察者 adoption。节点安全底线、declared artifacts、scope 和冻结科学合约未取消。
本地路径（Windows 与 `local_linux`）见 [local execution](../../.agents/skills/hmasd-research-engineering/references/local-execution.md)；
远端使用配置的 agent-task。新实验选机与已有进程恢复是两件事。分支/worktree 按隔离需要选择，
在完成工作、外部交付或运行前 push，不要求逐提交 scope 尾注或月度治理计数。

**Pro 路径：** 方向问题写 NOTES，owner-requested/delegated Portfolio 写 RESEARCH → 发布问题 → 当前作者 session
携带 repository、branch、source_sha、target_path、question_heading、answer_heading、subject key、conversation →
专用非保护 tab／provider preflight → 固定操作的 Send → 已验证的确定性外部观察（WSL POSIX Codex 使用
`tools/hmasd_wait.py`）→ 完整 answer
commit／完整正文 fallback → 原作者读取并记录采纳意见。目标不是固定 NOTES。核对 pinned question、实际 diff、
完整 subsection 和目标 branch；SHA／短聊天 receipt 不算答案。未知发送状态只核对，不重复 Send。
`hmasd_wait.py` 核心是 Python 标准库，不依赖 Jev。WSL 的被动页面读取走确定性 CDP/WebSocket；只有 Send 或已授权
connector consent 需要交互时才调用 Jev。默认 1500 秒窗口在完成、错误或 checkpoint 后保存事件；同一
POSIX Codex session 的多个 job 合并一次 queue 唤醒。Agentify/Claude 只在相应外部 observer 已验证时使用；
否则保留原 operation 并由原生 runtime／人工继续，不创建等待子代理，也不使用这条 queue 唤醒路径。

**Pro 的阅读上下文：** [共享选读说明](../../.agents/skills/hmasd-pro-research-prompt-author/references/pro-reading-context.md)
由问题作者按用途展开到原问题 Context：current governance/methods、standing/evidence、独立版本的 frozen contract。
实际发送消息包含阅读要求与来源优先关系；浏览器流程不自行选科学材料、不删掉这些说明。
这份说明是现有 Pro author 的按需 reference，不是新 spec、packet 或常规 review 触发器。

## 历史、退役与尚未验证的边界

PORTFOLIO、APPROVED_SET、dossiers、旧 cards／intakes／handoffs／ledger／packets 与旧治理规格是历史材料；
冻结对象中直接绑定的事实和科学约定仍保留。Grok／Sonnet clerk 已退役，不因旧引用重新注册。

旧 renderer、registry／binding／archive helpers、旧 state／delivery references、owner-item skill
及其对应测试已退出活动树与生成副本。旧源码可在 `987c7241e` 按原路径恢复；历史 registry、
已交付正文、旧操作参数和科学证据保留原位，不转抄成新流程记录。发现旧未决操作时按其原 key
和消息查询、收取正文；不重发。新工作不需要维护它们的旧状态机。

Agentify 的 stableKey/idempotencyKey 使用同一个问题 key；新问题可以复用原会话或换会话，
无需方向 binding 或 generation 登记。仅当既有操作已确认 sendAttempted=true 时，才可用原参数和
verifyExisting=true 恢复观察；该参数本身不保证只读。未知发送状态先用只读观察核对，不把
“再次调用工具”误当作“再次发送消息”。

已运行会话按工作需要在安全边界读取相关变化，不广播版本、不要求采用回执或单独的采用记录。
如需判断是否实际加载，查读取或原生运行证据；源码发布不能替代这个事实。
Windows／WSL／Agentify、用户级配置、Claude effective effort／权限隔离仍需原生观察。
这些是未验证边界，不是“已发生事故”，也不是每次 fit 前新增的一组检查。

维护本图只随实际入口、来源、路由或退休状态变化更新相关行；不逐次实验登记，不增加周期报告或签字。
