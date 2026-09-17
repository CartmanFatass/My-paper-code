# Claude 修改前与迁移后控制面对比

一次性 owner-requested 审计，作者 Codex。不是新规则、批准记录或研究恢复指令。

**审计重点更正：下列原报告主要检查手续与工具迁移，不能证明科学、工程方法完整迁移。请先读本文末尾的「科学 spec、工程 spec 与 skills 的内容保留复核」。该复核固定到 `7d30691bc87d7de441c0f27b666a237aef4c247a`，结论是：底线保留，但有实质方法内容未被当前 skills 完整承接。原报告保留为此前快照，不把其已修复的接口问题冒充当前问题。**

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

## 科学 spec、工程 spec 与 skills 的内容保留复核

### 对比对象与判定口径

本节回应 owner 的更正：检查工作流简化时有没有丢掉研究方法，而非再次审核手续。
旧基线为 `70654c8d9cc7852f41fe74c7f920f04af2409764`，当前为
`7d30691bc87d7de441c0f27b666a237aef4c247a`。旧 skill 引文均指该基线的同名文件，
可用 `git show <基线>:<路径>` 复核；当前链接指本次快照的路径及节名。
区间还包含 owner 修订、Pro 建议及 Codex 修复，不能把所有差异都归为 Claude 一人造成。

逐节对照的来源：

- 旧科学 skill 与 [MARL_EMPIRICAL_EVIDENCE_SPEC](../../research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md)，尤其 §§5、11.1–11.11。
- 旧工程 skill 与 [ENGINEERING_SCOPE_SPEC](../../project/ENGINEERING_SCOPE_SPEC.md) §§2–7、[MARL_RUNTIME_ENGINEERING_SPEC](../../project/MARL_RUNTIME_ENGINEERING_SPEC.md) General requirements §§1–8、[ENGINEERING_ADDITIONS](../../project/ENGINEERING_ADDITIONS.md)。对象附款只检查保留方式，不推广成新工作要求。
- 旧/current 科学、工程、Pro author、Portfolio、Root dispatch、Transport skills，已删除 owner-item 的内容；当前 Constitution、DM/Reviewer/Critic 角色和科学 references、分析脚本、foundation 阅读入口。
- Claude 的 [shared-methods rewrite](../changes/2026-09-16-shared-methods-rewrite.md) 与 [carried-over standards](../changes/2026-09-16-implementer-and-carried-over-standards.md) 改动记录。

**“未承接”指旧的可用方法不再出现在当前日常 skill/角色入口中；不是说历史文件被抹掉，也不是证明已经发生错误实验。**
旧 spec 被明确标为历史资料，因此“旧 spec 仍在磁盘”不能作为完成迁移的证据。
泛称“检查语义”“报告不确定性”只能算部分覆盖，不能替代原来具体的判断方法。
当前 foundation 仍能补充部分概念；其按需阅读入口也不等于所有相关方法已在日常 skill 中承接。

### 科学内容：六组实质差异

| 编号与旧来源 | 当前实际承接 | 缺失的内容及影响 | 最小补法（建议，尚未应用） |
| --- | --- | --- | --- |
| S1：旧 scientific-tools「Design and lanes」的因果路径与动态成员分析 | **部分保留。** Explore 仍列 roster/duration/credit/information；comparators 仍区分 K、N、transfer、ad hoc；Critic 仍检查 causal path、co-adaptation、censoring | DM 的设计方法中不再明确追踪 environment event → entity ownership → information → action/credit → learning → native consequence；entity/slot、join/leave/rejoin、survivor state、primitive/opportunity time 的区分未承接。可能把槽位复用或存活者历史差异误认为 N-axis 机制效果；不能声称 co-adaptation/censoring 在全控制面消失 | 在 Explore 增加适用时的因果链与动态成员辨析提示，不要求每项实验填写新表 |
| S2：旧 scientific-tools 实际学习链；科学 spec §§5.2、11.4、11.8.6 | **部分保留。** 工程 skill 要求 summary 中的 learner movement；当前有 horizon、fits、curves、summary 和技术失败区分 | 环境、policy、learner/trainer、evaluator 是否真的贯通，以及 transition/update/evaluation 的实际非零计数不再明确列出。参数变化不独自证明 evaluator/采样完整，也不能把 recurrent state 变化算作参数学习 | 需要学习主张时在现有 summary 核对这些读数；固定策略评价如实写零更新及条件性结论，不恢复 B 类认证或通用“先证明可学习”实验 |
| S3：旧 scientific-tools 确认冻结与 selection；科学 spec §5.3 | **部分保留。** CLAIM 已有 arms、fresh seeds、horizon、endpoint/evaluation、selection/tuning、decision rule、uncertainty；禁止看分数扩批和改写原计划；foundation 解释 checkpoint 选择 | 任务总体、checkpoint 选择规则、停止规则，以及 development/tuning 与 final evaluation 的分离不再在当前确认方法中逐项明确。不能说预先约定完全丢失，但新作者可能遗漏选择协议。DM 对旧冻结卡的 stopping-rule 保护只覆盖旧对象 | 在原 CLAIM 方法的一句话中补明总体、选择/停止协议及调参与最终评价的分离，不新建卡或审批 |
| S4：旧 scientific-tools「Statistics and comparison」；科学 spec §§11.7、11.11 | **部分保留。** 独立训练单位、配对依据、per-seed、estimand、小样本、不显著≠等效、宽区间≠零均在 | “值得关心的效应大小”、训练结果变异、估计量不确定性三者的区分未承接；事先定义等效区域及区间精度的正面判据缺失。取消 MEI verdict 是流程简化，但不应连确认阶段如何判断效果有无实际意义一起删掉。旧 spec 的“不用 1/2 SD 机械判有效或等效”也没有替代说明 | 按主张说明实际有意义的差异；仅在声称等效时给出事先定义区域及区间判断，不恢复所有探索都要 MEI 通过的门槛 |
| S5：旧 scientific-tools 基线段；科学 spec §11.7 | **未明确承接。** 匹配信息与 baseline reuse 保留 | headroom 原来是“说明的 upper reference 减去调优后的同信息通用基线”，不是任意正 score gap；当前 skill 没有这个定义。它关系到 FSD 基线校准的解释，不能把 privileged upper 与弱基线之差直接当可实现改进空间 | 在 comparators 增加一句定义及适用限度；缺少 headroom 不阻止普通探索 |
| S6：旧 scientific-tools「Burden, work and intake」；科学 spec §11.9 | **部分保留。** fits/horizon、完整性能成本、最小真实学习比较、search 需要目的均保留 | 设计前数 arms×fits×steps、evaluation panels、epochs、嵌套 candidate/trajectory/solver calls，区分算法固有搜索与研究附加验证的具体方法消失。小 fits 数无法揭示 a^N、b^H、全子集或每候选 replanning；“bounded/beam”也不自动代表便宜 | 在 Cost 加短工作量提示，用配置计数与已有测量选足够小的问题；无需成本 ledger、额外 profiling fit 或精确复杂度证明 |

另有一项研究取向的压缩：科学 spec §§11.1–11.3 明确允许受理论启发的次优/启发式方案，
其理论结论应匹配实际实现，普通经验比较不以普遍 invariance/safety/convergence 证明为前提。
当前 Constitution 的快速探索、单种子探索，以及 science 的 theorem-assumption 限定保留了大方向，
所以这不是全面丢失；但“启发式本身是合法研究对象，不需要先证明最优”不再明确。
可与 S6 一起补一句正面方法说明，无需恢复 C-FORMAL 分类。

### 工程内容：四组实质差异

| 编号与旧来源 | 当前实际承接 | 缺失的内容及影响 | 最小补法（建议，尚未应用） |
| --- | --- | --- | --- |
| E1：旧 engineering「Runtime and bounded execution」；runtime spec §4 | **部分保留，关键细节缺失。** 当前允许进程内 batching、固定同步 native team，保留常规 RNG/mask/reset/replay 审查和内部线程成本披露 | 没有明确 batching 应保留 time/causal/autoregressive/recurrent 顺序，以及 sample/update frequency、replay ratio、policy freshness、reduction/tail；固定团队的私有可变状态/输出、参与者与生命周期边界、逻辑顺序合并错误也消失。可能“加速”时改变训练量、丢尾或引入共享状态竞争 | 在 Runtime notes 补适用的语义清单和固定团队实现边界；不增加 worker 框架、验证服务或审批 |
| E2：旧 engineering「Scope and checks」；runtime spec §7；Engineering Additions「Wasted compute」 | **未明确承接。** independent Reviewer、required measurements 和不得删科学工作仍在 | “独立数值 checker 不得直接复用候选答案证明一致”和“虽不被主分支读取、但属于承诺诊断的输出不能直接删”已消失。独立 Reviewer 是人员/上下文隔离，不等于 checker 的算法独立性 | 补两句到 Checks。可以重新设计未来实验的无用诊断，但不能把省略原约定输出说成等价优化 |
| E3：旧 engineering 数值段；scope spec §3.5；runtime spec §7；科学 spec §11.8.5 | **部分保留。** dtype/scale/intermediates、反对普遍 bit equality、独立种子统计方法均保留 | 三种复现（确定性数值回放、统计重复、算法/语义等价）的用途区分不再明确；gradients、conditioning、accumulation、动作/排序/指标后果的检查较旧版缩水。相近中间数值未必代表相同策略决策；输入 SHA 相同也不保证输出相同 | 在 Checks 用一小段区分主张所需复现，按实际数值与决策风险选择检查；不设统一 1e-12 或跨平台 bit equality |
| E4：旧 engineering runtime 段；runtime spec §§1、3、5；Engineering Additions「Device selection」 | **部分保留。** 完整 wall/CPU/RSS/cold-warm 计量、no automatic GPU/JIT、killed stays killed 已在 | 性能方法被压缩为禁止列表与计量：真实热点、重复构造/细粒度跨语言调用/pack-copy、采样/训练/buffer/output 的设备与传输同步分析未承接。普通 wall/watchdog 估计可前瞻调整、但不能改变科学 endpoint/exposure 或硬资源限的区分也消失。可能误把规划估计当硬停机，或把微基准优势推广成训练优势 | 补“按完整实际路径找热点和选设备”及“工程估计与科学终点不同”两段；不恢复旧秒数阈值、不做强制设备扫描、不让被杀运行复活 |

E1/E4 的计量内容不能误报为全丢：当前 scientific-tools「Cost and exposure」已经承接
import/build/init、rollout/learning/replay、evaluation/synchronization/publication/readback、
cold/warm、preparation/queue、sum fit walls/batch elapsed/node occupancy、children CPU 和 RSS scope。
问题是**计量覆盖仍在，如何设计和验证优化的具体方法不完整**。

Engineering Additions 中的历史倍速、单线程经验、特定 CUDA/width16 tolerance、
torch.compile 1.00x 和 clone 成本仍是条件性历史测量，不应复制为全局规则。
需要承接的是其适用范围与推理方法，不是把历史硬件经验设成当前约束。

### 其他 skills：两处方法传播缺口

**O1：Pro author 的方法传递断开。** 旧 skill「Method and evidence bindings」明确指出
Pro 不继承本地 skills/role TOML，问题须内联适用约束，或指明固定 SHA 的科学/工程方法节；
并交代 claim ceiling、strongest alternative、discriminator、dominant workload 与未知量。
当前 [Pro author](../../../.agents/skills/hmasd-pro-research-prompt-author/SKILL.md) 的 Standing
链接 notebook/runs/claim，Constraints 明确写出的科学内容只有 seeds 和 matched baseline；
Return 仍有预测/null/discriminator/fit cost，但没有要求带入其他适用方法。
**文件在仓库可读不等于 Pro 已收到阅读目标。** 这会让本地方法即使修好也不能可靠传给 adviser；
不能因此断言所有历史 Pro 答案已经错误。最小补法是在现有问题段落加相关方法的短摘录或固定版本链接，
只选与问题有关的节及必要原始证据，不恢复 TASK/HANDOFF、全历史预读或 PRO_FINAL。

**O2：Portfolio/owner-item 的决策质量内容没有完整转移。** 旧 Portfolio 的比较维度包括
decision relevance、uncertainty、完整成本、substitutability、reversibility、headroom、MEI、
strongest contrary evidence；选项需说明 smallest useful investment、missing facts、revisit condition。
旧 owner-item 还让 owner 看支持与反对证据、代价和可逆性。
当前 [Portfolio](../../../.agents/skills/hmasd-portfolio-task/SKILL.md) 保留 options/consequences/reasons、
owner 决定、narrow negative≠方向否定、资源退出≠科学否定、fusion 匹配问题/estimand。
但“reasons”未明确承接上述比较维度。删掉 packet/owner-console 手续是有意简化，
不能据此把反证与最小下一步投资也丢掉。最小补法是在原 review section 中用普通文字说明
支持/反对证据、不确定性、完整代价、可替代性/可逆性及值得再次考虑的条件，仍只由 owner 触发。

Root dispatch 主要变动是权限、预算与协调，不能把这些改变算成科研知识丢失。
Transport 主要是交付方法，其先前修复也不等于完成上述科学内容迁移。
owner-item 的删除不应反转；它有用的决策信息可留在现有 Portfolio/NOTES 内。

### 确认保留的内容与应继续删除的手续

| 类别 | 本次核对结论 |
| --- | --- |
| 科学推断底线 | 独立 training runs；episodes/checkpoints 不扩充 n；配对有设计依据；不填缺失为零；保留失败与反向结果；报告 per-seed/estimand/selection；不显著不等于等效；按预写规则判读——均有明确当前文字 |
| 比较器 | actor/critic rights、信息 cadence/bandwidth/representation、communication/action/reward/termination/normalisation/reset、training/update/tuning/evaluation 权利以及 package/component 区分均保留 |
| 工程纪律 | core/experimental 区分、L0、保持 interfaces/RNG/checkpoints、core 不依赖实验代码、比例检查、高风险独立 review、exact inputs、declared artifacts、fresh admission、quarantine、复现诊断、local fallback、optional telemetry 与 primary measurements 区别均保留或已补回 |
| 文献与分析工具 | scientific-reading/local-literature 的 diff 仅是 card/intake → NOTES/claim 的记录路径用语；adapters.md 和 summarize_runs.py 在对比区间无变化。foundation/topic notes 入口保留。不能报告为知识库或统计脚本被删除 |
| 历史对象 | Constitution §10 明确保留 FSD B01 的原 fits/seeds/endpoint/reading/output contract；归档对象的独立例外仍在历史源中，不该泛化成新工作门槛 |
| 有意取消 | evidence-class/C-consumption 手续、旧 weekly windows、cards/intakes/ledgers/owner items、Pro 最终裁决与逐节点审批、固定行数/runner/test-time 配额、registry/packet/receipt 文书。均不建议恢复 |

### 对此前结论的更正与修复边界

Claude 两份变化记录对“comparators/statistics/cost kept”的说法，只在**保住部分主题与底线**的意义上成立。
它们没有证明全部方法已迁移。此前 Codex 的对比也把生成一致、工具接口与部分底线保留当成主要结论，
没有完成本节这种内容追踪，因此遗漏了 owner 真正关心的问题。

本次定位到 **6 组科学、4 组工程、2 组其他 skill 的实质缺口或承接不足**，另列研究取向的轻度压缩。
这些分组是审计组织方式，不是新的十二项合规关卡，也不表示十二项都完全消失。
优先补 S1/S2/S4、E1/E2/E3 与 O1，可分别避免机制混淆、假学习证据、统计误读、
优化改变算法、循环自证、错误复现要求及给 Pro 的方法遗漏；其余内容可在相同短段内一起承接。

适合当前 research project 的处理是：**把有用判断方法补进现有四个 skills，继续使用 NOTES、runs、CLAIM，
不恢复旧流程。** 本次只修改这份 owner 请求的对比报告，没有修改 Constitution/skills、增加研究任务、Send 或运行实验。
核验为旧/新源码与记录逐节对照、当前角色和阅读入口交叉检索；没有用 publisher drift 或通过的测试替代内容审计。
