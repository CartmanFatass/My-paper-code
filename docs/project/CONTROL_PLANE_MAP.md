# HMASD 控制面总览

描述性参考，不是 operating authority、审批层或必读 preload。对应本文件所在版本的源码；
历史比较基点为 `b24c4c8be1387b3f0963c8ce9229581a82001acd`，原审计见
[前后审计](../Claude_docs/reviews/CONTROL_PLANE_REWRITE_AUDIT_20260916.md)。
源码、生成结果、运行中会话的有效设置必须区分；本图不声称验证过用户机上的会话。
如何使用与修改这些文件，见 [CONTROL_PLANE_GUIDANCE.md](CONTROL_PLANE_GUIDANCE.md)。
本图说明“在哪里、如何连接”；guidance 说明“为什么这样分工、改动会影响谁、如何避免丢失方法”。
完整文档分类见 [docs index](../README.md)；退役 project 规格与迁移计划已移到
[archive](../archive/README.md)，旧实验绑定和原始外部回答继续保留其来源记录。

## 权威、维护源与生成链

| 层 | 入口／维护源 | 含义 |
| --- | --- | --- |
| Owner 与治理 | 当前 owner 指示；[OPERATING_CONSTITUTION.md](OPERATING_CONSTITUTION.md) | 研究暂停、方向选择与预算权限；修订不自动恢复研究 |
| 当前研究状态 | [RESEARCH.md](../research/RESEARCH.md) | active／reserve／archived、lead runtime、standing、pause；不是另一本规则书 |
| 自动加载入口 | 根 `AGENTS.md`；`CLAUDE.md` 导入它；就近目录的 `AGENTS.md` | 导航与局部技术边界。新记录用 NOTES／CLAIM／runs；冻结对象从索引直接读原卡 |
| 手工维护的方法 | `.agents/skills/hmasd-*/SKILL.md` 及其实际使用的 references/helpers | 科学、工程、Root coordination、提问、Transport、owner-triggered Portfolio |
| Codex 原生角色 | `.codex/config.toml` 注册 `.codex/agents/*.toml` | 原生 model／effort／sandbox 和共享角色正文 |
| Claude 原生角色 | `.claude/agents/*.md` 的 frontmatter | model／tools／description 直接维护；不能从 Codex 字段推定实际生效值 |
| 生成与适配 | `tools/publish_claude_control.py` | 共享 skills → `.claude/skills`；Codex role bodies ＋手工 Claude header → Claude agents；DM → research-hub，Transport →别名 skill |
| 部署参数 | `.codex/hmasd-compute.toml`；`.codex/hmasd-transport.toml` | 节点、解释器、supervisor、provider 与 conversation 数据；不是运行许可 |

Publisher 原样复制共享角色正文，只追加简短 runtime 说明，不再通过自然语言句子替换正文。
`--check` 检查预期输出差异及额外
HMASD 生成文件；不自动删除孤儿文件，不检查真实会话是否重载，不成为科研启动门禁。
`.claude/skills/hmasd-pro-transport` 是同一 Transport 方法的生成别名，不是第二套协议。

工程方法按任务需要、科学语义、成本与维护负担选择工具，不维护设施名称黑名单。
角色边界是当前任务的责任分工；读取必要依赖、合理复用、Root 的共享修复与 owner 指定分析均有入口。
非代码文档和 skills 正文由作者自检；core/高风险可执行行为才按 engineering 方法触发独立 Reviewer，
不因改了控制面说明就重复派发审阅。

## 两个 runtime 与 roles→skills

| 工作 | Codex | Claude | 方法／记录归属 |
| --- | --- | --- | --- |
| 方向推进 | Root 协调 DM children，保留 owner 指定 soft ceiling | session 本身是单方向 DM | loop-dispatch／research-hub；direction lead 拥有 NOTES |
| 实现 | DM 直接实现，或按需 Sol/high Implementer | session 直接实现，或按需 Opus/high Implementer | research-engineering；原生 Claude effort 未实测，不能从描述证明 |
| Review／事实 | Reviewer，既有 Scout／Verifier／ResearchCritic | 对应原生 leaves | engineering／scientific-tools；是受限方法，不是额外决策者 |
| 启动 | DM 直接启动或按需 Operator | session 直接启动或按需 Operator | engineering execution；精确来源、fresh preflight、accepted handle |
| 观察 | DM 直接观察或按需 ExperimentMonitor | session 直接观察或按需 bounded tracker | 委派者返回事实；解释与记录仍由 DM 负责 |
| Pro | 有工具时直接执行，或按需 Transport | session 自行 Agentify，或 Sonnet Transport | 同一 transport 方法；目标由问题作者指定 |
| 共享 Git 写入 | 协调中的 Root 集成 main／RESEARCH | 向共享 integrator 返回已接受提交；无 Root 或明确交接后才自行集成 | 使用自己的 checkout，确认实际 writer，不跨 runtime 共用 index |

DM 可在已选 active 方向内提出并前瞻记录新 idea，使用既定 per-idea fits；不是批次结束自动加额。
已选 reserve 可先由指定 DM 做无实证的准备，再由 Root 按现有 reserve 权限更新状态。
Monitor／Implementer 的任务分配不自动授予 NOTES／RESEARCH 写入权。Pro 只接管目标 answer subsection；
写入是否成功不确定时先核对实际 commit，再归还 writer，不建立 lease 或 ACK 服务。

## 状态、记录与两条执行路径

**新研究记录：** `docs/research/candidates/<direction>/NOTES.md`、确认前的 `CLAIM_<slug>.md`、
`runs/<direction>/<tag>/`。远端输出用可恢复位置关联；`temp/` 是 scratch，不是唯一证据仓库。
旧 FSD B01 按 RESEARCH 的原卡／原输出约定恢复，不转抄、不重新设计、不重跑已有 accepted 工作。

**执行路径：** owner pause／方向状态／idea allowance → DM 的明确代码任务 → 实现及必要 review →
提交并发布精确输入 → 按新实验需要选择配置中的本地/远端节点 → 同一 wrapper 内 preflight 成功后 runner →
accepted handle → 直接观察或委派时确认 adoption → terminal facts → DM 收集、核对并判读。
失联／timeout 不等于终止。local handle 要稳定进程身份与可访问 terminal witness；替换观察者先核对同一
handle，再完成新观察者 adoption。节点安全底线、declared artifacts、scope 和冻结科学合约未取消。
本地路径（Windows 与 `local_linux`）见 [local execution](../../.agents/skills/hmasd-research-engineering/references/local-execution.md)；
远端使用配置的 agent-task。新实验选机与已有进程恢复是两件事。分支/worktree 按隔离需要选择，
在完成工作、外部交付或运行前 push，不要求逐提交 scope 尾注或月度治理计数。

**Transport 路径：** 方向问题写 NOTES，owner-triggered Portfolio 写 RESEARCH → 发布问题 → assignment
携带 repository、branch、source_sha、target_path、question_heading、answer_heading、subject key、conversation →
专用非保护 tab／provider preflight → 固定操作的 Send → 同一问题的 observation → 完整 answer commit／完整正文
fallback → 原作者读取并记录采纳意见。目标不是固定 NOTES。核对 pinned question、实际 diff、完整 subsection 和
目标 branch；SHA／短聊天 receipt 不算答案。未知发送状态只核对，不重复 Send。

**Pro 的阅读上下文：** [共享选读说明](../../.agents/skills/hmasd-pro-research-prompt-author/references/pro-reading-context.md)
由问题作者按用途展开到原问题 Context：current governance/methods、standing/evidence、独立版本的 frozen contract。
实际发送消息包含阅读要求与来源优先关系；Transport 不自行选科学材料、不删掉这些说明。
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

已运行会话在安全边界通过现有返回路径报告实际采用的 revision／冲突；源码发布不能替代这个事实。
Windows／WSL／Agentify、用户级配置、Claude effective effort／权限隔离仍需原生观察。
这些是未验证边界，不是“已发生事故”，也不是每次 fit 前新增的一组检查。

维护本图只随实际入口、来源、路由或退休状态变化更新相关行；不逐次实验登记，不增加周期报告或签字。
