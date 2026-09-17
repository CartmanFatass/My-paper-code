# HMASD 控制面总览

描述性参考，不是 operating authority、审批层或必读 preload。对应本文件所在版本的源码；
历史比较基点为 `b24c4c8be1387b3f0963c8ce9229581a82001acd`，原审计见
[前后审计](../Claude_docs/reviews/CONTROL_PLANE_REWRITE_AUDIT_20260916.md)。
源码、生成结果、运行中会话的有效设置必须区分；本图不声称验证过用户机上的会话。

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

Publisher 自身包含行为适配，必须和 source→output 一起审阅。`--check` 检查预期输出差异及额外
HMASD 生成文件；不自动删除孤儿文件，不检查真实会话是否重载，不成为科研启动门禁。
`.claude/skills/hmasd-pro-transport` 是同一 Transport 方法的生成别名，不是第二套协议。

## 两个 runtime 与 roles→skills

| 工作 | Codex | Claude | 方法／记录归属 |
| --- | --- | --- | --- |
| 方向推进 | Root 协调 DM children，保留 owner 指定 soft ceiling | session 本身是单方向 DM | loop-dispatch／research-hub；direction lead 拥有 NOTES |
| 实现 | Sol/high Implementer；DM 验收 | Opus/high 为请求设置；session 验收 | research-engineering；原生 Claude effort 未实测，不能从描述证明 |
| Review／事实 | Reviewer，既有 Scout／Verifier／ResearchCritic | 对应原生 leaves | engineering／scientific-tools；是受限方法，不是额外决策者 |
| 启动 | DM 或 Operator | 只有 experiment-operator | engineering execution；精确来源、fresh preflight、accepted handle |
| 观察 | 可复用 ExperimentMonitor，事实直接回 DM | session 派发 bounded tracker window，原生返回 | 不解释科学、不发起重试；状态由 DM 记入现有 run entry |
| Pro | Transport child | session 自行 Agentify，或 Sonnet Transport | 同一 transport 方法；目标由 assignment 指定 |
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
提交并发布精确输入 → compute config 中的执行节点 → `admit-memory && runner` 同一 supervised command →
accepted handle → Monitor／tracker 的实际 adoption → terminal facts → DM 收集、核对并判读。
失联／timeout 不等于终止。local handle 要稳定进程身份与可访问 terminal witness；替换观察者先核对同一
handle，再完成新观察者 adoption。节点安全底线、declared artifacts、scope 和冻结科学合约未取消。

**Transport 路径：** 方向问题写 NOTES，owner-triggered Portfolio 写 RESEARCH → 发布问题 → assignment
携带 repository、branch、source_sha、target_path、question_heading、answer_heading、subject key、conversation →
专用非保护 tab／provider preflight → 固定操作的 Send → 同一问题的 observation → 完整 answer commit／完整正文
fallback → 原作者读取并记录采纳意见。目标不是固定 NOTES。核对 pinned question、实际 diff、完整 subsection 和
目标 branch；SHA／短聊天 receipt 不算答案。未知发送状态只核对，不重复 Send。

## 历史、退役与尚未验证的边界

PORTFOLIO、APPROVED_SET、dossiers、旧 cards／intakes／handoffs／ledger／packets 与旧治理规格是历史材料；
冻结对象中直接绑定的事实和科学约定仍保留。Grok／Sonnet clerk 已退役，不因旧引用重新注册。

**仍存在的遗留工具不可当作当前默认：** 两个 Pro skills 目录下的旧 renderer、registry／binding／archive helpers、
旧 state／delivery references，及 `hmasd-owner-item` 的退役 notice。当前新工作流程不调用这些工具；但文件仍在，
当前 publisher 的递归复制也仍会包含它们。孤儿检测的修复不等于退休工作完成。
在确认没有 accepted／uncertain legacy 操作依赖后，才把这些工具及对应测试按原字节迁出活动树；
保留 Git 来源与恢复说明，不移除用户本地 registry、进程状态、科学结果或未知 worktree。

已运行会话在安全边界通过现有返回路径报告实际采用的 revision／冲突；源码发布不能替代这个事实。
Windows／WSL／Agentify、用户级配置、Claude effective effort／权限隔离仍需原生观察。
这些是未验证边界，不是“已发生事故”，也不是每次 fit 前新增的一组检查。

维护本图只随实际入口、来源、路由或退休状态变化更新相关行；不逐次实验登记，不增加周期报告或签字。
