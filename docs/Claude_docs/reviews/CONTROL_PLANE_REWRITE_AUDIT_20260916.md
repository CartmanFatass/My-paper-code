# Claude 控制面重写：前后对比审计

日期：2026-09-16（America/Los_Angeles）。作者：ChatGPT Pro，通过 GitHub connector 读取与提交。一次性审阅记录，不是新的 operating authority、审批表或周期性 audit ledger。

## 结论、范围与版本

**本次重写不是行为等价的文字压缩。** 多项变化是 owner 有意选择的简化；部分工程保护曾被删短，随后已恢复；局部入口、生成链、Transport 消费接口和运行中会话采纳之间仍有冲突或验证缺口。不能仅凭 publisher drift 为零认定迁移正确，也不应因此恢复整套旧治理。

本提交仅移除工程数字配额、修复 Constitution 的两条相对链接，并加入[控制面总览](../../project/CONTROL_PLANE_MAP.md)。其余发现与最小修复候选列在下文，未自动实施。没有恢复研究、调整方向／runtime 分工、改变 frozen fits、删除旧文件或修改实验实现。

| 比较点 | 固定 commit | 含义 |
| --- | --- | --- |
| B：重写前 | `3196d2fc353dae5090c20517177aa15adaa52ec0` | Claude 此次 Constitution 采纳／共享方法重写之前；更早的 Codex task-skill migration 已在其中 |
| 采纳 | `5f57b4e5074e330360e6ca63f8d37bd8baff7903` | Constitution、入口切换、RESEARCH 与 clerk 退役 |
| R：共享方法重写 | `169c104494e6d2bb7cf5a16e366aa1d329303d7f` | skills、角色正文与 publisher 适配重写 |
| 工程恢复／Implementer | `4141a456827f233039a794b28066a975d73c8cac` | owner 要求保留适当工程保护，并加入两边 Implementer |
| H：本次审计快照 | `b24c4c8be1387b3f0963c8ce9229581a82001acd` | 根入口再次压缩后的状态；本报告的“当前”均指 H，而非可漂移的 main |

[B→H compare][compare] 涉及 8 commits、61 changed paths。审计逐项核对 authority、局部 AGENTS、共享 skills、DM/Implementer/Reviewer/Monitor/Operator/Transport、配置、publisher／测试与状态入口。生成文件按 source→adapter→output 核对；旧 helper 做存在性／可达性盘点，并非每个旧 helper 都逐行重新审查。实验代码目录和 scripts 的实现未在这个区间改动；这说明 diff 范围，不证明既有实现正确。

外部 Agentify 实现、用户级配置、Windows/WSL 本机状态和已启动会话未访问。以下“影响高”是静态失效路径的影响判断，**不是声称已经发生线上事故**。

## 哪些保留、哪些有意改变、哪些已经恢复

| 项目 | 前后结果 |
| --- | --- |
| owner pause；status/migration 不恢复研究 | 保留。当前 RESEARCH 仍明确暂停；本次审计也不解除。[入口][H:root]、[状态][H:research] |
| DM 端到端责任、Root 不逐步 ACK、独立方向不做 sibling barrier | 主要分工保留；共享 main 写入边界另见 A06。[B loop][B:loop]、[H loop][H:loop] |
| exact source、节点 fresh preflight、detached run、unknown≠terminal、防重复启动、收集验证后清理 | 保留；compute 配置未在该区间改变。[H engineering][H:engineering]、[Operator][H:operator]、[compute][H:compute] |
| core／科学语义／numerics／RNG／replay／checkpoint／外部效果的独立 review | R 与 H 都保留，不能误报为“只剩 core 文件审查”。[R engineering][R:engineering]、[Reviewer][H:reviewer] |
| declared-artifact staging、可选 telemetry 与主要测量的区别、local fallback | R 中删短或遗漏；H 有明确恢复段落，不再是当前缺失。[B engineering][B:engineering]、[B science][B:science]、[R engineering][R:engineering]、[H engineering][H:engineering] |
| quarantine、复现诊断 | H 明确写入；恢复日志称从早期标准恢复。本审计不把日志所称的每条旧规范都当成已在 B engineering 中逐字核实。[恢复日志][H:restore]、[H engineering][H:engineering] |
| 独立训练单位、匹配信息、调参暴露、坏结果、non-significance≠equivalence | 保留。seed 数量不构成精度认证。[B science][B:science]、[H science][H:science] |
| APPROVED_SET、lanes、C consumption、每周窗口、cards/intakes、Pro finality | Constitution 有意用 per-idea fits、三种记录、Pro adviser 替代；不作为“遗漏”要求恢复。[Constitution][H:constitution]、[重写记录][H:rewrite] |
| 三 DM soft ceiling／Claude session 单方向、Implementer | 是后续 owner 选择；本次不改回此前 Pro 草案的全局两个方向设计。[Constitution][H:constitution]、[恢复记录][H:restore] |
| clerk 删除与旧 helper 退役 | clerk 已删；若干 helper 删除仍 pending。保留 frozen 科学例外与退役旧流程不是同一个动作。[重写记录][H:rewrite] |

## 发现与最小修复候选

### A01 · 影响高 · 局部入口仍重新引入旧规则

[docs/AGENTS][H:docs] 开头仍要求每 object 的 pilot note/card、summary/result、intake，以 DIRECTION 为科学入口；末段仍要求链接 card/intake。中段虽然改成 RESEARCH 索引，整份文件却未与 Constitution §4 的新工作记录体系对齐。这是局部迁移不完整，不是单纯保留历史档案。

[experiments/AGENTS][H:experiments] 和 [scripts/AGENTS][H:scripts] 仍指定 `temp/directions/<id>/exp/`，新 science/engineering 则指定 `runs/`。旧冻结 runner 使用原位置合理，但当前文字没有清晰划分新工作与冻结对象。

**推断的后果：** 读取 nearest AGENTS 的 agent 可能重新生产 card/intake 或写入消费者未读的输出位置。Constitution 优先级缓解冲突，却仍要求每个 agent 临场解释。

**候选：** 只改局部入口的新工作默认，保留冻结例外与历史路径，不批量转抄／搬迁结果。本次只移除了 tests/AGENTS、envs/AGENTS 的工程配额措辞；上述记录／输出冲突未改。

### A02 · 影响高 · Portfolio 生产者与 Transport 消费者不匹配

[Portfolio 步骤 2–3][H:portfolio] 将 review 和 `### Answer` 放在 `RESEARCH.md`，然后调用共享 Transport；[Transport 步骤 5][H:transport] 和 [role][H:transport-role] 却只验收 `NOTES.md`。旧方法使用 workflow-node/scope 指定交付目标，不是这个固定路径。[B Portfolio][B:portfolio]

**推断的后果：** Pro 正确写回 RESEARCH，也可能被报告为 connector write failed，并走错误 fallback。

**候选：** 现有 assignment 携带目标 repository path、branch、question heading/source revision、answer heading；消费者按目标验收。用 NOTES 和 RESEARCH 两条文件 fixture 验证，不恢复 packet／registry。本次未改 Transport。

### A03 · 影响高 · 完整答案与当前问题的配对保护被削弱

[B Transport][B:transport] 明确区分短聊天 receipt 与完整 GitHub answer，要求取得完整答案来源／commit、核对当前问题，保留冲突候选，并处理 GitHub 已交付而页面配对失效的情况。

[H Transport][H:transport] 主要检查新 commit 的 `### Answer`，失败时保存页面文本；[H question][H:question] 同时要求 Pro 在聊天只回复 commit sha。新 commit 或一个非空 heading 本身不足以证明答案属于本轮问题、内容完整或没有并发覆盖；页面 fallback 也可能只有一行 receipt。

**候选：** 读取实际 answer commit 中指定问题的完整 subsection，核对身份、完整正文与越界修改；写回不确定时先找实际提交。只有 receipt 就如实报告，不当作答案。无需恢复 PRO_FINAL、完整旧 ledger 或新增审稿轮次。没有证据表明这里已发生错配事故。

### A04 · 影响高 · 退役面仍接在活动配置与生成链上

[transport 配置][H:transport-config] 仍 `status="active"`，含 `registry_path`、verified-binding 和 retired-id 策略；新 Transport 仍读取其中的 provider policy。旧 binding、native_transport、transport_contract、validate_request、materialize_packet、archive helpers，以及 prompt 的 render_packet 和旧 delivery/state refs 仍在 shared skill 目录。重写日志明确记载删除受阻、pending，而非完成。[重写记录][H:rewrite]

[publisher][H:publisher] 递归复制目录中的文件，没有 retired 筛选。`--check` 只遍历预期输出，也不检测额外孤儿文件。这个孤儿盲点在 [B publisher][B:publisher] 已存在；本次退役增加了其影响，不能全部算作新代码引入。

**实际定点验证：** 原 publisher 的隔离 fixture 中，新增孤儿生成文件后 check 仍返回空；标作 retired 的源 helper 仍出现在 generated outputs。sentinel 未执行，没有操作用户机上的 registry。

**候选：** 分离当前 provider settings 与旧 registry 元数据；明确每个旧 helper 是仍需保留的 recovery 工具还是退役材料，再对齐发布输入。孤儿检查可作为开发检查，不自动删除，不变成研究启动门禁；不绕过先前的删除限制。

### A05 · 影响高 · 源发布不等于在途会话采纳

[B loop][B:loop] 明确说明磁盘修改不会更新旧会话，要求向受影响原 DM 发送 revision/application boundary，记录实际 adoption/conflict。H loop 已没有对应边界。[H loop][H:loop]

publication tests 测生成一致性而非原生加载；现存 migration publication 记录的 source 是更早的 `38cc9264...`，不能证明 H 已进入所有原会话。[测试][H:tests]、[旧 publication][H:publication]

**结论：** H 在途采纳状态未验证，不是已证明失败。候选是在现有交接／报告中说明受影响会话实际采用的版本和适用边界；不重发 accepted run/Send，不新增全局 ACK 或采纳 registry。

### A06 · 影响高 · main／RESEARCH／NOTES 写入权仍有歧义

[根入口][H:root] 与 [loop][H:loop] 说 Root owns main/index；[生成 Claude hub][H:hub] 却要求 session 自行集成 main 并更新 RESEARCH。这是 publisher 的明确适配，不是偶然手改生成副本。[publisher][H:publisher]

Pro 写回 notebook、Monitor 可写 NOTES 或 assigned path、DM 持有方向 writer，可以产生交接竞争。Constitution 已要求协调 notebook writer，但各组件的归还边界尚未对齐。[Monitor][H:monitor] 另有 Implementer 的“push if the DM said so”与根入口每个 commit 立即 push 的差异。[Implementer][H:implementer]

**候选：** 在当前 assignment 中统一实际 checkout/owned paths、共享 writer 和交还方式；返回事实不自动授予共享文件写入权。main 的集成责任需尊重 owner runtime 设计，不由 map 决定，也不引入 lease service。未观测到实际 Git 数据丢失。

### A07 · 中等影响 · 封闭角色列表与实际注册不一致

Constitution／根入口禁止其他 role，但 [Codex config][H:config] 和 [DM][H:dm] 仍保留 Scout、Verifier、ResearchCritic、Operator 等 optional leaves，Claude 也有对应注册。Operator 又是 Claude 唯一结果启动者，不能因列表未解释它就直接删除。

**候选：** 澄清这些名字是已有角色的受限方法调用，还是需 owner 保留的独立 role，再同步注册与文案。本审计和 map 只指出差异，不擅自增删角色。

### A08 · 中等影响 · Monitor 的恢复细节删短

[B Monitor][B:monitor] 要求 local handle 有稳定进程身份与可访问 terminal witness，观察者交接须先 same-handle reconciliation 再 replacement adoption。[H Monitor][H:monitor] 仍保留 supplied handles、首次 adoption、unknown≠terminal、稳定 event 与 notice reconciliation，但上述具体条件不再明确。

**候选：** 在现有方法保留稳定身份与替换观察者的语义，不复活 tracking/handoff 文档。不能误报为“全部 adoption 保护都没了”；本审计未访问用户机 handles。

### A09 · 中等影响 · 自主探索带有旧 no-successor 歧义

Constitution 允许普通 ideas 与额度内工作不等待 owner；[DM][H:dm] 又说完成 idea/batch 不授予 successor/retry/new host/extra fits。[Root loop][H:loop] 要求 reserve 的 NOTES 已有 worthwhile idea 才启动 DM，同时 Root 不做方向科学。

可以合理读作“完成本身不自动加额度”，也可能被读成“下一项合法新 idea 必须重新获批”；reserve 由谁准备 idea 也不清晰。**这是歧义，不是已复现死锁。** 候选是区分新 idea 自主提出与同一失败 idea 重命名／批次自动加 fits，并说明准备责任，而非增加逐 idea 审批。

### A10 · 中等影响 · 冻结例外入口与非等级性科研／性能限定变弱

[RESEARCH][H:research] 明确保留 FSD B01 原卡替代新 claim note，并给原 handoff；DM 却只列当前 NOTES/CLAIM/owned code。恢复冻结对象时不能漏读原卡，也不该因此要求全局历史 preload。

[B engineering][B:engineering] 更明确解释完整成本阶段、cold/warm、CPU accounting、内部 native/BLAS teams，以及 parallel wall 与实际占用的差别；H 主要保留 wall/RSS/horizon。[恢复日志][H:restore] 所说“CPU accounting kept”不能替代当前正文欠缺的说明。[B science][B:science] 的 held-out transfer 范围与 simulator 不证明物理部署安全等限定，也随证据等级内容一起删短。

**候选：** 冻结对象按索引直接读原卡；做性能或 transfer 主张时链接相应测量限定。不要恢复 C-ladder、统一精度门槛或所有探索必须先做全面诊断。

### A11 · 导航缺陷 · Constitution 移动后相对链接失效（本次修复）

[H Constitution][H:constitution] 从 plans 移到 `docs/project/`，仍保留两条 `../../research/candidates/...`，解析到仓库根 `research/`。本次改为 `../research/candidates/...`，目标仍是同一 FSD 冻结卡和 FOLR evidence，未改变科学内容。

### A12 · 验证边界 · runtime 元数据不能互相推定

[Codex Implementer][H:implementer] 有原生 high-effort 字段；[Claude Implementer][H:claude-implementer] 只有 Opus model，high effort 在 description，恢复日志也承认没有 effort field。这里是配置证明缺口，不是证实实际 effort 错误。

[Codex Reviewer][H:reviewer] 是 read-only sandbox；[Claude Reviewer][H:claude-reviewer] 的只读文字与 Bash tools 并存。[Claude settings][H:settings] 空 deny 既不能证明没有全局限制，也不能证明等效隔离。publisher 保留手工 frontmatter，“只改共享正文”不足以覆盖全部 Claude 元数据变化。

候选是在真实 runtime 查看有效模型／effort／权限／版本；本审计未执行，也不建议变成每次研究的新增固定门禁。

## 本次修改、验证与未完成边界

移除代码行数、runner 行数、orchestration 比例、测试时长／固定次数、L0 行数、入口字节数及提议句数配额。替代为按复杂度和风险提供充分检查，报告实际成本与覆盖缺口。修改同步到 shared source、Codex role、Claude 手工描述及受影响 generated bodies，并处理 tests/AGENTS、envs/AGENTS；不修改历史规格的原始数值。

保留 fits/seeds、owner runtime soft ceiling、pause、独立 review 触发、exact inputs、坏结果、真实内存检查、防重复外部效果与 FSD frozen contract。engineering 改为引用 admit-memory 的实际检查，不修改 script/config 中 4 GiB 底线。

已完成的定点验证：相关源文件与原 publisher 的 Git blob SHA 校验；在隔离的受影响输入 fixture 中重现三个原 generated outputs 的 fetched SHA，并生成修改后的副本；Codex 原生元数据、Claude model/tools 不变；受影响 role/skill 数字配额扫描；执行段除内存引用措辞外不变；孤儿输出和 retired-copy 行为复现。不是把自查称作独立审阅。

**未运行：** 完整仓库 publisher drift／完整测试套件、独立第二 agent review、Windows/WSL/Agentify 实际 smoke、原生会话采纳验证、科研训练。结论是源级审计与定点生成验证，不是全系统运行认证。

## 最小收敛顺序（建议，不是新授权）

先对齐局部入口与答案目标／完整答案消费，再处理退休文件和发布输入一致性，随后明确共享 writer 与在途会话切换。每项沿实际生产者→消费者验证，证据留在当前 PR／change/review。冻结／accepted 操作不重发、不换输入；历史科学证据保持可恢复。无需新增 governor、registry 或全量规则验证框架。

## 固定源链接

[compare]: https://github.com/CartmanFatass/My-paper-code/compare/3196d2fc353dae5090c20517177aa15adaa52ec0...b24c4c8be1387b3f0963c8ce9229581a82001acd
[H:constitution]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/docs/project/OPERATING_CONSTITUTION.md
[H:root]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/AGENTS.md
[H:claude]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/CLAUDE.md
[H:docs]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/docs/AGENTS.md
[H:experiments]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/experiments/AGENTS.md
[H:scripts]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/scripts/AGENTS.md
[H:config]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/config.toml
[H:settings]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.claude/settings.json
[H:compute]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/hmasd-compute.toml
[H:transport-config]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/hmasd-transport.toml
[H:publisher]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/tools/publish_claude_control.py
[H:tests]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/tests/skills/test_control_publication.py
[H:loop]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.agents/skills/hmasd-loop-dispatch/SKILL.md
[H:engineering]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.agents/skills/hmasd-research-engineering/SKILL.md
[H:science]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.agents/skills/hmasd-scientific-tools/SKILL.md
[H:question]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.agents/skills/hmasd-pro-research-prompt-author/SKILL.md
[H:portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.agents/skills/hmasd-portfolio-task/SKILL.md
[H:transport]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md
[H:dm]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/agents/hmasd-direction-manager.toml
[H:hub]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.claude/skills/hmasd-research-hub/SKILL.md
[H:implementer]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/agents/hmasd-implementer.toml
[H:claude-implementer]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.claude/agents/hmasd-implementer.md
[H:monitor]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/agents/hmasd-experiment-monitor.toml
[H:operator]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/agents/hmasd-experiment-operator.toml
[H:reviewer]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/agents/hmasd-reviewer.toml
[H:claude-reviewer]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.claude/agents/hmasd-reviewer.md
[H:transport-role]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/.codex/agents/hmasd-transport.toml
[H:research]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/docs/research/RESEARCH.md
[H:rewrite]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/docs/Claude_docs/changes/2026-09-16-shared-methods-rewrite.md
[H:restore]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/docs/Claude_docs/changes/2026-09-16-implementer-and-carried-over-standards.md
[H:publication]: https://github.com/CartmanFatass/My-paper-code/blob/b24c4c8be1387b3f0963c8ce9229581a82001acd/docs/project/CONTROL_PLANE_MIGRATION_PUBLICATION_20260916.json
[B:loop]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/.agents/skills/hmasd-loop-dispatch/SKILL.md
[B:engineering]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/.agents/skills/hmasd-research-engineering/SKILL.md
[B:science]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/.agents/skills/hmasd-scientific-tools/SKILL.md
[B:portfolio]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/.agents/skills/hmasd-portfolio-task/SKILL.md
[B:transport]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md
[B:monitor]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/.codex/agents/hmasd-experiment-monitor.toml
[B:publisher]: https://github.com/CartmanFatass/My-paper-code/blob/3196d2fc353dae5090c20517177aa15adaa52ec0/tools/publish_claude_control.py
[R:engineering]: https://github.com/CartmanFatass/My-paper-code/blob/169c104494e6d2bb7cf5a16e366aa1d329303d7f/.agents/skills/hmasd-research-engineering/SKILL.md
