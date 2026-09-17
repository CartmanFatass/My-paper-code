# Claude 修改前与迁移后控制面对比

一次性 owner-requested 审计，作者 Codex。不是新规则、批准记录或研究恢复指令。

## 固定版本与结论

- 修改前：`70654c8d9cc7852f41fe74c7f920f04af2409764`，2026-09-16 03:56 PDT。
- 当前源码快照：`0d1579cd3f4f0dbc3f46401f6a2acdd644203019`。
- 旧 Pro 审计基点 `3196d2fc3` 已包含 Claude 首批退役角色文件清理和 Constitution 草案；本次向前扩展一个提交，覆盖该变化。
- 后续版本包含 owner 采纳、Pro 修订和 Codex 迁移修复，不能全部归因于 Claude。

结论：这是治理与工作方式的实质简化，不是行为等价压缩。此前的大多数源码接口遗漏已补回；仍有一个明确的会话更换接口冲突、一个恢复能力收窄点，以及遗留工具、入口提示、运行时采纳等未闭合项。没有依据声称已发生错发、丢失结果或线上事故，也不能用 publisher 零漂移证明全系统正确。

本次对比限定的控制面路径共 60 个 changed paths：根与就近入口、共享 skills、两侧 roles/config、publisher、对应控制面测试。另读 Constitution、RESEARCH、先前审计与迁移记录。对照本机 Agentify 实现时只读源码，没有 Send、浏览器操作、训练或真实句柄接管。

## 主要变化

| 方面 | 修改前 | 当前 | 性质与影响 |
| --- | --- | --- | --- |
| 权威与索引 | 根入口组织权限，APPROVED_SET 是当前执行表；lane、证据等级、执行状态分别维护 | Constitution 是唯一治理文本，RESEARCH 是唯一当前索引 | 有意减少多份权威和状态同步 |
| 方向与并发 | 批准对象内推进；Claude hub 最多两个方向；禁止自动补位 | Codex Root 协调最多三个 DM 的软上限；Claude session 一次一个方向；TRDL 是 reserve | owner 后续选择，不是丢掉并发保护；不要求占满位置 |
| 实现 | CM/Implementer 新任务暂停，DM 直接实现 | 恢复有边界的 Implementer：Codex Sol/high、Claude Opus/high 请求；DM 接受结果 | 主动恢复委派；实现者不做科学决策、不启动训练、不再派生 |
| 研究预算 | 七日窗口：EXPLORE 四 fits，CONFIRM 一个 card-sized object；无自动下个窗口 | 每 idea 最多六 fits（含各 arm、调参），确认每 arm 三至五个新独立种子；无固定周额度 | 更快换想法；同一失败 idea 不可改名重置，不能看结果后扩批 |
| 日常自主权 | 对象完成不授权 successor；方向决策通过固定 Pro 节点 | active 方向内新 idea 可前瞻记录后用默认额度；reserve 可先做无实证准备 | 有意提高 DM 自主性；方向集合及超额仍归 owner |
| 科学记录 | card/pilot、summary、intake，加 DIRECTION、handoff、tracking、owner items 等 | NOTES、runs、确认前 CLAIM，加一张 RESEARCH 表 | 有意退役旧文书；冻结 FSD B01 仍按原卡、原 seeds、原判读与输出约定 |
| Pro 权限 | 符合约束的绑定答案是其节点最终决策；存在 finality 与节点路由 | Pro 是建议者，DM 记录采纳/修改/拒绝；Portfolio 仍只由 owner 触发、owner 决定 | 最重要的权限变化之一；不应作为遗漏恢复 PRO_FINAL |
| 科学底线 | 强调独立训练单位、匹配信息、选择暴露、坏结果及不确定性 | 这些保留；Constitution 明确学习效果主张至少三独立 seeds/arm；单 seed 留在探索 | 保留关键推断边界；数量本身仍不保证精度 |
| 工程配额 | 行数、runner 大小、orchestration 比例、测试时间等固定数字 | 改为复杂度、风险、充分检查与实际成本；不设工程数字配额 | owner 明确要求的删除；fits、seed 与实际内存底线未随之删除 |
| 运行与证据 | exact source、fresh actual-node admission、detached run、不可盲重试、收集后清理 | 保留，并恢复 declared artifacts、quarantine、复现诊断、local fallback 和性能计量限定 | 核心安全语义未整体丢失；compute 配置与执行脚本实现未在区间修改 |
| 写入与发布 | Root/main、Claude hub 自集成之间曾有冲突；publisher 不报额外文件 | 共享 integrator 明确；Pro 只写 answer subsection；Monitor/Implementer 返回事实；publisher 检出孤儿与模糊适配锚点 | 迁移修补；生成一致性与运行中会话生效仍是两件事 |

## 已闭合的旧审计项

以原 [Pro 审计](CONTROL_PLANE_REWRITE_AUDIT_20260916.md) 的 A01–A12 为参照，不把旧快照结论冒充当前状态：

| 旧编号 | 当前核对结果 |
| --- | --- |
| A01 | docs/experiments/scripts 的新记录与 runs 默认路径已对齐；冻结路径例外明确 |
| A02–A03 | 方向/Portfolio/Transport 共用 repository、branch、source_sha、target_path、两级 heading；读取完整答案，核对实际 commit、范围、并发覆盖及 fallback；不是只收 SHA |
| A04 | 已补孤儿检测，registry 标为旧恢复兼容；物理退役仍未完成，见下 |
| A05 | 已恢复 revision/application-boundary 交接文字；真实在途采纳仍未验证 |
| A06 | main/RESEARCH、NOTES、Pro subsection 与 leaf 的写入责任已对齐；授权提交立即 push |
| A07 | Constitution 已解释既有 Operator/Scout/Verifier/Critic 是有边界的方法，不是新增决策者 |
| A08 | Monitor 稳定身份、terminal witness、same-handle reconciliation、replacement adoption 已恢复 |
| A09 | 已区分合法新 idea 与旧批次加额，并说明 reserve 的无实证准备 |
| A10 | 冻结原卡入口、完整性能成本和 transfer/theorem 主张限定已补回 |
| A11 | Constitution 相对链接已修复 |
| A12 | 已明确不能从文字推定 Claude effective effort/隔离；实际设置仍未证明 |

另已核对上次迁移修复的 Claude Tracker/Transport 原生描述，以及 Transport 的 wait_response 白名单。它们不再保持此前的 NOTES-only/直接写笔记/不能等待的组合。

## 当前剩余问题，按实际影响排序

### 1. 会话更换缺少独立 generation key：明确接口冲突

当前 [Transport](../../../.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md) 第 21 行指定 `stableKey = <subject key>`，方向通常保持不变；[Constitution](../../project/OPERATING_CONSTITUTION.md) §5 却明确允许上下文过旧时更换会话。

本机 `C:/Projects/agentify-desktop/review-transport.mjs` 第 337–340 行：同一 stableKey 已存在 binding 时，firstBinding 或不同会话 URL/ID 会触发 `review_binding_mismatch`。不是换一个 idempotencyKey 就能解决。该源码还会在已观察到新会话用户消息后持久化 binding（480–491）。

修改前 `references/agentify.md` 的 Binding generations 明确区分方向身份与具体会话 generation，并要求新 generation 使用不同 key。现在整段被删除，但下层工具的不可变 binding 语义未消失。

影响：已有一次成功绑定后，按当前方法为同方向换会话会在发送前被拒绝。这里是源码可达失效路径，没有实际发消息复现。最小修复候选：assignment/现有 NOTES header 保存实际会话 key，新会话使用独立 key，旧 accepted/uncertain 操作保留原 key；不恢复旧全局 registry，不借换 key 重发旧问题。

### 2. 无发送恢复调用被一并禁用：能力收窄，需要精化

当前 Transport 第 31 行和两份直接链接的参考文档禁止 sendAttempted=true 后再次调用 review_query。修改前允许相同 immutable args、已有操作、verifyExisting=true 的观察与归档恢复。

本机 Agentify MCP schema 明确区分 false 可发送、true 只观察；`review-transport.mjs` 第 329–335 行要求已有完全相同操作，第 500–526 行只在 !sendAttempted 时进入发送分支，第 527 行以后保留用户消息配对和响应归档恢复。

现方法的 wait_response/read_page 仍能观察和取正文，GitHub 成功交付仍可独立验收，因此不能说所有恢复都坏了。但它失去了上述原生配对/归档恢复通道。上次迁移为关闭手动重复 Send，也把参考文档同步为绝对禁止；本次跨到工具实现后确认，应区分“再次发送”和“同一操作只观察”。修复候选只允许已确认 sendAttempted=true、严格匹配原操作的恢复；unknown 不可直接推定安全。

### 3. 旧 helper 尚在活动发布输入：已知未完成项

`tools/publish_claude_control.py` 第 51–66 行仍递归复制 shared skills 的全部非 bytecode 文件。旧 `native_transport.py`、binding/validation/archive/materialize/render_packet 脚本，旧 state-schema、provider-context-replacement 等仍在 shared 与 generated 树。旧 state-schema 仍定义共享 registry/lease；native_transport 仍消费 TASK/HANDOFF。

新 SKILL 没有要求调用这些旧 helper，`.codex/hmasd-transport.toml` 也已标为 legacy-only，所以不是“当前默认仍强制 registry”。但它们仍可被发现，并被 publisher 当成预期输出；零漂移不能证明完成退役。最小后续工作是先核对旧 accepted/uncertain 操作依赖，再从当前分发输入移出不再需要的内容，保留来源和恢复通道。未经核对不删除 registry 或旧任务状态。

### 4. 技能菜单默认提示遗漏 Portfolio：低风险入口漂移

`.agents/skills/hmasd-chatgpt-pro-transport/agents/openai.yaml:4` 仍写“one committed NOTES.md question in the direction's Pro conversation”；其 Claude 复制品同样如此。正文和角色已支持 RESEARCH/Portfolio。走菜单默认提示时可能重新带入方向/NOTES-only 假设；正文能纠正，故不等同 A02 主调用链仍坏。可仅改维护源默认提示并重新发布。

### 5. 运行中会话及原生设置：仍是验证缺口

当前加载约定已修复，但没有新证据证明旧 Claude/DM 会话采用当前 revision。Claude Implementer frontmatter 是 model: opus，high 在描述；Reviewer 有 Bash，项目 settings 为空 deny。这既不证明 effort 错误，也不证明与 Codex read-only sandbox 等价。旧运行时加载回执属于更早版本，不能搬作本快照的证明。应在真实 session 安全边界观察，不重启 accepted run、不重发 Pro、不创建全局 ACK 表。

### 6. 开销落地仍待观察，另有一条新增文书要求

Constitution §9 已要求新月度分子/分母，但 RESEARCH 的月度表只有旧的 33 docs-touching/run-summary 参考行；没有当前治理提交/唯一结果摘要的实际计数或 owner-hour。当天采纳后的过渡待办不等于逾期违规，但当前无法验证“简化已降低开销”。

CLAUDE.md 第 34–35 行新增“every control-plane change gets a row in ... changes/<date>-<slug>.md”；修改前只指定非方向交付目录，没有逐控制变更留记录的要求。这是新增的固定文书义务，与 Constitution §7 不增加过程文档的方向有张力，不能把它算作精简。候选是保留需要的实质变更说明，避免把每次修改都强制变成独立文书；这只是审计建议，本次不改规则。

## 保留项与验证范围

Owner pause、独立高风险 review、真实节点物理及有效可用内存保护、精确来源与 artifacts、无盲目重复外部效果、原结果与 adverse outcomes、匹配 actor/critic 信息、训练单位与选择暴露均仍有明确来源。不能因为删掉旧 gate/ledger/PRO_FINAL 就断言这些保护消失。

本次实际运行 publisher --check：`drift: 0`。读取已有 21 项定向测试及迁移结果；没有无改动重复跑同一测试。测试覆盖生成、孤儿、header、锚点、目标字段和关键文字；没有覆盖“同方向会话替换→真实 Agentify binding”，这解释了为什么通过 21 项检查仍会漏掉问题 1。研究实现与 `.codex/hmasd-compute.toml` 在本区间无 diff；scripts/envs/experiments 范围内变化仅为 AGENTS 入口。这不认证既有科学实现。

没有进行真实 provider Send、native effort/权限验证、WSL launch、旧运行句柄交接或旧 helper 依赖清理。本报告只记录证据和最小修复候选，不修改控制面源码、不恢复研究、不改变历史科研结论。

后续 owner 澄清：旧流程复杂度不适合当前研究项目，要求实际完成迁移。本文是上述固定快照的审计，
不构成继续保留这些手续的理由。随后已采用问题级工具 key、恢复不发送的同操作查询、移除旧 helper／
references／owner-item 与对应测试、对齐菜单提示并取消逐修改文书要求；真实 Agentify 模块的无外部发送
测试通过。实施事实见[原迁移记录](../changes/2026-09-16-control-plane-alignment.md)的 owner clarification 段落。
