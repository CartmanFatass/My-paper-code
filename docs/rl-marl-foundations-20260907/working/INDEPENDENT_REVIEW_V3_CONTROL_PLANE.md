# v3 知识接入与当前控制面独立审核

审核日期：2026-09-09 UTC（本地 2026-09-08）。审核者：独立 Astra/max。工作区：C:/Projects/HMASD。审核起点与结束复核均为 `c463c03766f88cfc7c37d978bf9583cabfe52e3c`，main 跟踪 origin/main；179 个候选路径的 SHA-256 在阅读前后完全一致。

**结论：v3 的知识接入、职责适配和逐引用固定版本设计可实施；v2 的 R1–R4 在当前 v3 文本中仍然闭合，没有新的实质计划阻断项。当前整个控制面仍有四项 P2 实际缺陷和一项 P3 维护文档漂移，不能宣称全控制面无缺陷。** v3 第 41 行把现行 Claude 入口笼统归为“历史漂移”的表述需要澄清。以下缺陷分别定位、分别修复；不把它们合成新的研究启动门槛，也不要求为知识接入重做历史实验或发 Pro。

本次只创建本报告与 [V3_CONTROL_PLANE_READING.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/V3_CONTROL_PLANE_READING.md)。没有修改现有计划、规范、角色、代码或运行状态，没有提交、运行实验、Send、派发启用命令或新增代理。父级验收并负责提交。现有未跟踪基础知识文件和 PDF 均保留。

## 1. 实际依据与阅读边界

已通过只读任务工具读取 [确定无人机实验场景](codex://threads/01a07e71-4afd-7b20-a5ac-d776cd7b2da5) 的最近 16 个任务回合，提取其中实际用户消息与最终答复；没有将大量历史工具输出或空语音回合推定为新增授权，也没有声称读完该任务全部历史。有关接入方式、独立知识文件、复用 scientific-tools、当前 return 比较偏好、MAPPO 方向及未冻结实现的上下文可访问，没有为这些事实留下待用户补充的缺口。

文件覆盖为 **179 个候选路径中的 172 个全文阅读**，包含根和六个区域入口、全部当前 .codex/.claude/.agents 文件、直接脚本与合同、现行科学和工程规范、Root/Portfolio/owner 入口及实现、基础知识稿、相关现有测试。另 7 个历史计划、实验长档或旧清单只核对状态/入口/元数据，明确不计作全文。逐文件范围和字节版本见阅读记录。全量目录核对与引用搜索用于确定范围，全文结论来自实际分段阅读，而不是关键词命中。

必要只读事实包括 Git 状态/HEAD、当前 owner 待应用指令查询（`python -B tools/owner_console/item.py reviews --json` 返回 `[]`）、必需 Claude helper 的存在/跟踪/忽略状态、源码前后摘要。现有测试全文已读，本次没有重跑单元测试或构造新测试。本文的失败场景来自具体指令与实现的相接关系，不声称已触发真实浏览器失败。

## 2. v3 计划审核

### R1–R4 保持情况

| 原发现 | v3 实际处理 | 独立结论 |
| --- | --- | --- |
| R1：Pro 被要求使用未交付的本地 skill | §3、§4.2 的 §11.10 草案、§4.5 将本地 skill 定位和 Pro 固定 TASK 直接读取分开；清单外依赖与权限扩张被排除。 | 方案层面闭合。 |
| R2：一般知识混入当前会话选择 | §4.1 明确 SESSION_CHOICES 承接原 §7、§6 的策略句、§5 的机制设想与专题选择，并区分已选偏好、机制假设、未冻结实现；FOUNDATIONS 原 §7 留导航。 | 方案层面闭合；实施前文件尚未分离是预期状态。 |
| R3：renderer 方法段缩减会丢失约束 | §4.5C 完整保留当前 renderer 698–755 行方法段，本批不压缩；新增固定规范的明确采纳，同时澄清两处绝对排除措辞。 | 方案层面闭合；原始来源/工具事实/推断与比例约束不会依赖一个未给出的替代摘要。 |
| R4：新旧作者和存量上下文无法一致启用 | §6 先发布独立知识，再一致启用规范、角色、作者、renderer 和合同；同步实际 authoring checkout，通过自然 assignment/return 给存量角色一次具体补读指针，Root 自身也补读。 | 方案层面闭合；没有热更新假设、广播服务、全会话重启或 Portfolio ACK。 |

### 当前职责和固定版本

Root 现已承担 Portfolio 科学比较与执行；当前 [ROOT_OPERATIONS.md](C:/Projects/HMASD/docs/project/ROOT_OPERATIONS.md)、portfolio-task、loop-dispatch、DM/CM、EXPERIMENT_MONITOR 和 SIBLING_COMMUNICATION 的维护入口相互可达。v3 正确给 Root 的科学动作增加读取入口，同时不让计数、推送、转交收据等机械动作预加载科学知识。CM/Reviewer 只在奖励、信息、终止、训练单位等科学语义问题上条件触发；科学判断仍由实际科学负责人解释。

可选逐引用 `commit_sha` 适合当前作者模型。现有 renderer 没有可直接替代的任意跨提交文件 URL 输入；其科学引用当前继承顶层 `commit_or_ref`。v3 把完整 SHA 校验放进共同 validate、固定每项有效映射、保持路径去重、同时覆盖 GitHub 与附件正文，并保持科学卡/证据原映射。这避免为新知识移动旧科学输入 SHA。新方法 SHA 在一致启用提交发布后选择，避免未来自身 SHA 的循环依赖；HANDOFF 不再复制独立引用总表，Transport 状态机不需要扩张。

当前 [安全暂停 handoff](C:/Projects/HMASD/docs/research/portfolio/handoffs/2026-09-08-safe-pause-handoff.md:35)、PORTFOLIO 与 EXPERIMENT_TRACKING 的暂停边界一致。v3 保留该边界及已接受、发送不确定、已封存和既有 READY 请求的字节/绑定，不因知识更新生成新科学对象或重发。既有三批 CM 模型比较已有完成记录，v3 不重启它。角色 model/effort、权限、工具清单、已冻结比较器、奖励、信息集合、RNG、预算、设备和证据含义均不在拟改范围。

## 3. 当前控制面实际缺陷

### C1 — P2：Claude 正常生成的 CALLER_READY 被自己的 Transport 前置条件拒绝

**位置：** [.claude/agents/hmasd-pro-transport.md:17](C:/Projects/HMASD/.claude/agents/hmasd-pro-transport.md:17)（17–19、32–34 行）；[Claude Transport skill:46](C:/Projects/HMASD/.claude/skills/hmasd-pro-transport/SKILL.md:46)（46–66 行）；[render_packet.py:591](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py:591)。

Claude skill 正确要求 `execution_mode=CALLER_DIRECT`，bind 后明确得到 `CALLER_READY`。renderer 对这条已发布路径设置 `dispatch_required=false`，含义是不需要向 Codex singleton 派发。下游 Claude agent 却只接收 `READY_TO_DISPATCH`，并明确把 `dispatch_required=false` 与 `TASK_NOT_PUBLISHED` 一起判作“no payload: stop”。

**失败场景：** hub 按当前 skill 完整 render、发布、bind 一个已授权请求，然后交 Sonnet 执行。Sonnet 严格遵守自己第一个前置条件，会在任何 Send 前拒绝这个合法请求。现有作者测试亦明确断言 direct 路径的 `CALLER_READY/false`（作者测试 160–203 行），说明这里不是 renderer 偶然返回错误状态。

**最小修正：** 只对齐 Claude agent 的输入/前置条件：未发布 TASK 仍停止；有已发布精确 payload 的 CALLER_READY 走已授权 Claude Transport 路径，false 只取消 Codex 应用派发。保留一次 Send、精确请求、provider 检查和暂停约束，不改为 REUSE_SINGLETON，也不改科学正文。

**验证：** 用现有 renderer 的 direct/non-direct 输出对照入口解释，确认未发布、已发布 CALLER_READY、普通 singleton 三种状态分清即可；不需要真实 Pro 测试请求。

### C2 — P2：Claude 必需的归档实现只存在 ignored temp 路径，无法从仓库恢复

**位置：** [Claude Transport agent:143](C:/Projects/HMASD/.claude/agents/hmasd-pro-transport.md:143)（143–160 行）；[Claude Transport skill:110](C:/Projects/HMASD/.claude/skills/hmasd-pro-transport/SKILL.md:110)；[archive_delivered_claude_request.py](C:/Projects/HMASD/temp/sessions/hmasd-chatgpt-pro-transport/archive_delivered_claude_request.py)。

这两处现行入口把 `temp/sessions/hmasd-chatgpt-pro-transport/archive_delivered_claude_request.py` 指定为 Phase 2 结束时的必需步骤。脚本在本机确实存在且已全文阅读；`git ls-files -- <该路径>` 无输出，`git check-ignore -v` 显示命中 .gitignore 第 50 行 `/temp/**`。它是读取固定归档并推进 shared registry 的运行源码，不是可有可无的临时证据。

**失败场景：** 新 checkout、恢复环境或清理该临时目录后，tracked Claude 指令仍要求调用一个仓库不能提供的脚本。归档状态不能按指定步骤推进到 ARCHIVED；现有 bind 的后续请求仍会遇到 BINDING_BUSY。不能以当前机器恰有该文件证明仓库可恢复。

**最小修正：** 将这份已使用的实现纳入一个可跟踪的现有源码位置，并更新两处调用和它的仓库根定位；保留 request/字节/归档检查、validated transitions 与幂等行为。既有 registry、原始证据和历史请求无需迁移或重写，也无需增加第二套归档系统。

**验证：** 验证 tracked 来源可在干净源码树中找到、两个入口一致；必要时以调用自有 temp fixture 验证已有归档路径，不访问真实 registry 或发送请求。

### C3 — P2：Claude hub 把普通对象委托重新变成“owner 出现就等回复”，并错误限制为可逆动作

**位置：** [Claude hub skill:76](C:/Projects/HMASD/.claude/skills/hmasd-research-hub/SKILL.md:76)（76–84 行）；对照 [AGENTS.md:55](C:/Projects/HMASD/AGENTS.md:55)、AGENTS §3–4，以及 [当前 DM:96](C:/Projects/HMASD/.codex/agents/hmasd-direction-manager.toml:96)。

hub 仍写 owner present 时把选项放在最终消息里、收到回复后才继续；owner absent 时普通对象决策全部限于 reversible actions，并为每次普通 decision 写 owner item。当前通用 owner calibration 已明确：状态/问题不等于接管对象，既有对象委托持续；可逆限制只适用于 PRO_BLOCKED / LOCAL_PROVISIONAL；普通授权研究可以消费已声明调用预算，普通对象选择留在 intake/audit，P1/P2 才进入独立 owner item。

**失败场景：** owner 只问一句状态，hub 就停止一个仍受 standing delegation 覆盖的下一 rung，等待已经不需要的确认；或者在 owner 离线时把已授权预算消费误认为不允许的“不可逆动作”。这些条款位于会在会话开始加载的活跃 skill，不能按历史资料忽略。

**最小修正：** 只把普通对象决策段对齐当前委托/显式接管/PRO_BLOCKED 区别，owner item 用既有 P1/P2 规则并处理 CLI 的 skipped 返回。**保留** Claude 的两个方向配额、不可再嵌套代理、Grok/Sonnet 分工及 [CLAUDE.md:82](C:/Projects/HMASD/CLAUDE.md:82) 的逐文件写入边界。不要借此把 Codex 的五方向目标或权限套到 Claude；Claude 特有治理文件权限也不能从 §4.7 泛化解除。

**验证：** 对照“owner 仅问状态”“owner 显式接管本对象”“PRO_BLOCKED 暂定选择”“普通已授权调用”四种输入检查决策说明。无需新 owner 状态机或每次确认流程。

### C4 — P2：experiments/ 最近层入口仍将 30% 作为硬预算，并保留旧的统一 smoke 要求

**位置：** [experiments/AGENTS.md:23](C:/Projects/HMASD/experiments/AGENTS.md:23)（23–27 行）；对照 [ENGINEERING_SCOPE_SPEC.md:41](C:/Projects/HMASD/docs/project/ENGINEERING_SCOPE_SPEC.md:41)、[证据规范 §11.8.6](C:/Projects/HMASD/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md:503) 和 [§11.8.8](C:/Projects/HMASD/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md:523)、[tests/AGENTS.md:52](C:/Projects/HMASD/tests/AGENTS.md:52)。

该入口仍把“one smoke test under 60 s plus rule tests”和“orchestration under 30% of a diff”列为 attempt 必须满足的要求。现行维护规范要求按改变的行为/主要输出做比例适当的聚焦检查、未改变路径复用现有证据；30% 明确只是 review signal，不能自动退回、成为预算上限或科学有效性测试。

**失败场景：** 对一个普通 B 的必要 I/O 和参数处理超过 30% 的小修复，CM/Reviewer 遵循最近层入口硬退回；或已有合适的聚焦检查时仍补跑一个独立 smoke。这正是 v3 §4.4 所说需要按实际遮蔽情况处理的区域入口，当前遮蔽已存在。

**最小修正：** 把这几行改为现行规范的短指针及同义摘要；30% 保留为审查提示，检查按对象实际分支规则和改变范围执行。保留 2,000/600 行及现有测试/资源预算、冻结对象附款和科学语义，不引入新计数或验证体系。

**验证：** 以普通 research 变更与 VNFC E01 等命名冻结例外分别做条款对照；确认一般入口不会新增门槛，也不会解除特定已冻结要求。文档定点修复不需要运行实验。

### C5 — P3：owner README 仍要求只读今天和昨天，与已修复的跨日期待应用实现不一致

**位置：** [owner/README.md:147](C:/Projects/HMASD/docs/research/portfolio/owner/README.md:147)（147–153 行）；[item.py:63](C:/Projects/HMASD/tools/owner_console/item.py:63)；[server.py:220](C:/Projects/HMASD/tools/owner_console/server.py:220)。

README 仍指示每个干净边界只读今日/昨日 reviews。当前 CLI 调用 pending_instructions，后者使用 `load_items(root, days=None)`；DM/owner-item 入口已采用所有未应用指令，现有测试 134–155 行也覆盖 30 天前的 item/reply。

**失败场景：** 一个从 AGENTS/README 恢复流程的执行者依旧只按两个日期窗口读文件，会漏掉长暂停前尚未应用的 override。当前只读查询返回空列表，未发现本次已有 owner 指令实际漏应用，所以不报告运行事故或升级严重度。

**最小修正与验证：** README 指向现有 `item.py reviews` 的跨日期 pending 结果，日期 review 文件用于原文引用；保留 mark-answered 与 audit 回链。确认说明与现有实现/测试一致，无需新字段或再造队列。

## 4. 历史漂移与非阻断说明

- v3 第 41 行应拆开“现行 runtime 例外”和“历史非执行材料”：Claude 两方向容量是 [CLAUDE.md:110](C:/Projects/HMASD/CLAUDE.md:110) 的现行 owner 边界；C1–C3 是活跃入口问题。v3 第 51 行的新请求 source/parent/operator 说明也宜加“Codex 原生路由”限定，避免读者把它套到被第 137/199 行明确保留的 Claude CALLER_DIRECT。现有“不改路由/保留 CALLER_DIRECT”约束已足以限定实现，因此这是范围澄清，不是增加一套路由的理由。
- ALGORITHM_PRINCIPLES 自称 durable contract、指向旧 EM/ExpRecord；当前 AGENTS 已将其降为历史背景，v3 明确只加历史状态说明并修复 evidence spec 的旧引用关系。此处已有合适方案，不要求重写历史正文。
- IMPLEMENTATION_PLAN 与 UAV_G0_READINESS 已显式标为历史非执行/对象局部记录；旧 ExpRecord、Explorer、UAV 性能记录、旧分支清理/Transport 迁移收据中的 Root/Portfolio/heartbeat/lease 语言属于当时事件或冻结对象上下文。当前维护源和暂停 handoff 已接管，不把旧收据当作下一条动作。
- CPP production policy 的旧 P0/全链效率/原生优先段、hmasd_run 的旧 OMP/长运行合同需要留在实际被冻结采用它们的对象范围。当前 scripts/AGENTS 明确 hmasd_run 只用于冻结卡指定的 wrapper；不能从读取这段兼容代码推出今天所有 B 的额外门槛。本次没有无理由扩读全部历史科学卡，也没有因此建议删除旧实现。
- 未发现新增角色、常驻 scheduler、方法 registry 或统一知识“通过状态”的必要性。v3 已有正例/负例、实际读取轨迹、存量上下文与两种正文的验收设计；这些是后续实施应交付的证据，本次没有把文本存在算作行为已经稳定。

## 5. 接受范围与后续工作

可以按 v3 主干实施知识接入，并定点澄清其历史/runtime 范围说明；当前控制面 C1–C4 应由后续被授权的控制面修复工作处理，C5 同步修正文档即可。它们不是 v3 才引入的代码回归，也不构成让全部独立研究或所有维护工作等待的新门槛。当前 owner 暂停继续有效。

本结论只接受**计划可实施性与上述静态/只读事实**。后续实现仍按 v3 既定范围验证逐引用映射、发布后固定来源可读性、角色实际读取与旧上下文补读。真实 Pro 读取只在下一条本来就获授权的请求中观察；“未观察”应保留，不用额外 Send 结清。

本次没有验证 Agentify/ChatGPT 实际 UI、当前远端 supervisor/资源准入运行、所有其他存量会话是否已加载最新文本、全部历史 registry/请求或所有方向的科学有效性。没有将这类未运行事实列为通过，也不把它们自动列成缺陷。详细覆盖与七项非全文范围见伴随阅读记录。

