# HMASD 控制面与 MARL 研究流程迁移计划

日期：2026-09-16  
用途：交给 Codex 执行的迁移任务书；不是新的常驻控制文档。  
基准：仓库 `CartmanFatass/My-paper-code` 的暂停快照；`main 941ed56a0`、`codex/fsd b034cb0d9`、`codex/acvc 66abf52ca`。短 SHA 仅为定位线索，执行前解析实际完整 SHA、当前远端分支和本地 worktree。不得回退后来已提交的工作。

> 目标：短 AGENTS、职责明确的原生角色配置、自包含且按任务加载的 skill、唯一维护的现行规则，以及不自动扩大研究投入的实验批次流程。
>
> 当所有者明确把本计划交给 Codex 并要求开始迁移时，授权的是本计划列明的控制面重构、流程修正和有界工程验证；不等于恢复科研、批准新实验、调用 Portfolio、发送 Pro 请求或更改冻结对象。

## 1. 交付目标与保护边界

### 1.1 本轮必须完成

完成当前规则归属清点、AGENTS 瘦身、角色配置去重、方法 skill 内化、Codex/Claude 加载适配、现行入口清理、研究流程修正、离线测试与原生加载验证、独立审查、提交集成和交接。

验收关注实际行为，而不是文件数量：角色开始关键动作前已获得必要规则；普通任务不用沿多个索引拼装义务；不相关科学规范不提前加载；旧工作流不能从另一个入口重新生效。

### 1.2 本轮明确不做

不恢复 CM/Implementer 或换名的实现代理链；不新增 router agent、调度服务、数据库、权限 DSL、守护进程、自动重试、lease/heartbeat 或整套文档平台；不新增每次实验必须通过的通用验证器；不为了重构换 MARL 框架、重写 PPO/collector/buffer、改 reward、seed、dtype、checkpoint 或训练预算。

不启动 FSD stage 0，不实现 CF 学习器，不发任何真实 Pro/Portfolio 请求，不开启 ACVC 后继对象，不加入或自动补入研究方向。CF 实现与实验恢复留给明确恢复后的方向任务。

不得把本计划提及的研究建议直接写成已经完成的 Portfolio 生命周期决定。ACVC 的 PARK 建议、候选加入、预算数字仍由所有者在相应审阅中决定。

### 1.3 原样保护

冻结 card、接受后的 TASK/HANDOFF、Pro 原回答、原始训练输出、历史标签、已消费额度和对象限定例外保持其原始含义。不得事后重命名证据等级、重算成功标准、回填从未测量的资源或删除阴性结果。

现行安全边界保持：pause 优先、批准集合限制、准确输入版本、每次实际启动的新鲜资源准入、不确定外部接受状态的同请求核对、保护其他写入者和无历史改写。

## 2. 目标结构：四种内容，四种职责

| 载体 | 唯一职责 | 应移出的内容 |
|---|---|---|
| 根 `AGENTS.md` 与必要的目录级 AGENTS | 所有相关会话必须知道的短约束、目录特有工程规则、明确任务入口 | 研究手册、完整角色流程、历史 override、实验状态快照、多层索引 |
| `.codex/agents/*.toml` | 该角色每次执行都需要的职责、权限边界、返回形式及关键 skill 触发 | 多角色共用的大段方法、全套文献、其他角色的操作手册 |
| `.agents/skills/*/SKILL.md` | 可直接执行的任务方法；正文足以完成正常流程 | 只有跳转的空壳、历史审批正文、当前进程/机器快照 |
| card、summary、approved set、handoff、历史 spec | 分别保存对象契约、观察、授权状态、交接和历史依据 | 重新抄写整套通用治理规则 |

保留必要的直接证据引用；消除“为了找到下一条规则而先读索引”的依赖。规则、对象数据和解释性文献不是同一种东西。

### 2.1 AGENTS.md 的具体范围

正文直接写清项目目的、Root/DM 基本分工、所有者 pause、只推进 approved set、并发上限不是填满目标、不自动申请 Portfolio、不因状态询问恢复研究、冻结语义和证据保护、共享 Git 与不确定外部效果的底线。

根会话承担 Root 协调时显式使用 `hmasd-loop-dispatch`；不能假设普通主会话已加载某个 subagent TOML。只有研究调度需要读 approved set；格式修改、只读审查、机械收集不先读整个 Portfolio。

不加入全技能目录、全部角色表、历史日期块和长命令手册。仅保留少量真正直接的入口指令。目录级 AGENTS 只写该目录独有的工程约定，不复制 Portfolio/统计规则。

检查真实启动目录和原生发现行为；不能假设根目录启动后，只要编辑一个子目录文件，该目录 AGENTS 就一定自动进入上下文。必要的目录规范在具体代码任务中直接读取。

### 2.2 角色配置分工

| 角色 | 直接内联的常驻职责 | 明确禁止 |
|---|---|---|
| Root（主会话） | 集成、实际共享依赖、批准集合内顺序、收到变化事件后的动作 | 代替 DM 反复解释结果、自动补位、制造审批往返 |
| DM | 一方向内科学、直接实现、修复、技术验收、科学 intake、授权范围内连续执行 | 自行改变集合/生命周期/冻结实验；恢复 CM/Implementer 链 |
| Reviewer | 独立审阅实际变更路径，给出事实、可达失败和影响 | 修改被审查代码、增加无关科学门槛、以审查代替所有者决定 |
| Operator | 精确输入、一次有界启动、接收事实、交给现有 monitor、终态收集 | 自行补 seed、重跑、扩大矩阵、改设备或端点 |
| Monitor | 观察已有 handle，报告变化和终态，按既有协议等待 | 启动、重试、读数裁决、无变化时制造工作 |
| Transport | 已授权请求的单次发送、原请求核对、归档、返回真实事实 | 科学裁决、不确定时另发请求、跨请求清理 |
| Scout / Verifier / Critic | 保留现有可选、有界专业任务 | 强制前置、层层子代理、重复整项研究 |

关键底线可以在相关角色中短句重申；完整方法只能有一个手工维护来源。既有模型、推理等级、沙箱、工具和审批策略不因本轮文字压缩擅自调整。

### 2.3 Skill 的收敛方案

优先保留既有名字，避免大规模更名和调用修复；核心工作流默认七个 skill，不因 spec 小节数量扩张。

| Skill | 迁移后的职责 |
|---|---|
| `hmasd-loop-dispatch` | Root 协调、批准集合与 pause、事件触发、边界刷新、交接动作 |
| `hmasd-scientific-tools` | 完整研究方法：问题/主张、探索与确认、比较器、暴露、统计解释、结果 intake；现有工具为辅助 |
| `hmasd-research-engineering`（新增） | DM 与 Reviewer 共用的 L0、风险比例、科学语义检查、代码/测试范围、技术验收 |
| `hmasd-pro-research-prompt-author` | 已选定问题的固定输入、TASK 编写、发布绑定与返回处理；不承担发送细节或投资决定 |
| `hmasd-chatgpt-pro-transport` | 发送/观察/恢复/归档的完整正常方法；配置保留不可遗漏的边界 |
| `hmasd-portfolio-task` | 所有者触发时的 dossier、建议与决定 intake；没有循环自动触发 |
| `hmasd-owner-item` | 所需 owner brief/item 的机械发布；不自行决定每个事件都要一份记录 |

`SKILL.md` 必须包含触发与不触发条件、最低输入、正常步骤、应返回结果、越界处理。不规定所有任务必须读所有模式。

核心规则要直接落入正文。例如研究方法 skill 应直接说明：独立训练实例是学习性能推断单位；episodes/checkpoints 不增加训练 n；MEI 与不确定性分开；按冻结规则读数；缺失配对不填零；包装收益不自动归因单一机制。

允许一级、目的明确的附属读取，例如“只有文献检索时读取 local-literature”；禁止正常执行要经历 skill → 索引 → spec → 新索引 → 规则。特殊故障/API 长表、理论推导和示例可放 references，历史例外不塞回通用正文。

### 2.4 大小与加载预算

以下是维护目标，不是科学启动门槛；超出应解释内容归属，不通过截断或压缩可读性解决。

| 表面 | 初始目标 |
|---|---|
| 根 AGENTS | 4–6 KiB；超过 8 KiB 触发人工审查 |
| 单个目录 AGENTS | 通常 0.5–1.5 KiB |
| 单个角色 developer instructions | 通常 1–3 KiB |
| 常用 SKILL 正文 | 通常 2–6 KiB；确有必要可超出 |
| 核心工作流 skill 数量 | 默认七个；增加需说明不可合并的任务边界 |

测量固定加载字节、可见 skill 目录预算、角色正文、按任务实际读取内容和必经跳转数；未知 token 数明确未知。不要设置虚假的 token 改善百分比。

不得调低 `project_doc_max_bytes` 来掩盖膨胀。核查用户级/组织级配置、`CODEX_HOME`、override、fallback、项目信任、会话启动参数、目录级规则和已安装同名 skill。全局/组织配置不是本轮可擅自修改的仓库文件。

## 3. 现行规则的唯一维护与旧 spec 退场

### 3.1 归属迁移

| 原来源 | 新的主要维护位置 |
|---|---|
| `MARL_EMPIRICAL_EVIDENCE_SPEC.md` 中当前通用研究规则 | `hmasd-scientific-tools/SKILL.md` |
| `ENGINEERING_SCOPE_SPEC.md`、`MARL_RUNTIME_ENGINEERING_SPEC.md` 的通用工程要求 | `hmasd-research-engineering/SKILL.md`；机器值仍在配置 |
| `ROOT_OPERATIONS.md` 的分工与路由 | Root loop skill 与相关角色配置，各管自己的流程 |
| `SIBLING_COMMUNICATION.md`、`EXPERIMENT_MONITOR.md` 的常用方法 | 对应角色配置及专有 skill；较长 API/特殊恢复留一跳 reference |
| 科学双轴方案中的通用推断原则 | 研究方法 skill；具体投资顺序仍属于 Portfolio 数据/决定 |
| workload、pause、进程状态、当前 head | 当前 task/handoff/summary，不放进常驻指令 |

迁移必须完整读完相关现行规范后再提炼，不得只根据本计划、之前的摘录或 §11 摘要删除其他仍有效约束。现有源代码/runner/测试预算与具名例外不自动消失。

### 3.2 结构迁移与语义改动分开记录

每个迁移项标为三种之一：`MOVE_UNCHANGED`（原义搬迁）、`REMOVE_SUPERSEDED`（已被明确替代的旧规则）、`CHANGE_PROSPECTIVE`（本计划明确提出的未来规则改动）。标签只用于本次迁移记录，不新建运行时协议。

所有者采纳计划后，在一份有日期的决定/变更记录里明确新承载位置、切换范围、下节列出的语义修正以及冻结兼容性。该记录是审计证据，不要求每个任务读取它。

旧 spec 保留历史正文与已发布 SHA；可以在当前版本增加“历史绑定用、非日常加载”的短说明，但不得破坏原版的固定 SHA 读取。冻结对象若未显式写出所有引用版本，在迁移清点时解析并记录当时实际适用来源；不要让后来移动的链接改写原卡。

不长期维持“旧 spec 是现行权威，skill 是另一份手工摘要，执行时两边都要读”。人类版手册若保留，只做派生阅读材料或历史解释。

未被本计划覆盖的实质冲突列出旧文、新文、后果和最小待决问题；仅暂停依赖该问题的切换，不借重构自行改变科学约束，也不阻塞无关的结构迁移。

## 4. Codex、Claude 与外部 Pro 的加载适配

### 4.1 Codex

AGENTS 由原生机制构建指令链；自定义 agent TOML 是所生成会话的配置层；skill 通常先发现元数据，选用后读正文。`skills.config` 是启用/禁用配置，不是强制正文预加载。

角色的重要方法通过明确任务触发绑定。例如 DM 开始新科学设计或 intake 时使用研究方法 skill；开始代码变更时使用工程 skill；Root 做研究协调时使用 loop skill。不要写成“必须先读所有 skill”。

验证实际客户端支持的字段、原生 agent 名称和注册方式。项目中已有配置若仍兼容，不为了追随文档示例而改接口或模型。不要跨运行时发明 `skills`、`imports`、`required_skills` 等字段。

### 4.2 Claude

`CLAUDE.md` 保持短小，只导入共享 AGENTS 和必要的 Claude 运行时差异。共享方法以 `.agents/skills` 的正文作为唯一手工维护来源。

复用仓库已有同步方法；若没有，采用小型、确定性的发布时复制/格式适配，把完整共享方法提供给 Claude 的原生技能入口，标清生成来源，禁止手改派生正文。不能只做一层“去读另一个 skill”的空壳。Windows 符号链接仅在真实 checkout、Git 和两个运行时均验证后采用，不当作默认前提。

角色职责同样只维护一份可确定的共同语义，Claude 特有工具/模型字段保留其原生值。不凭字符串替换把 Codex 权限映射成 Claude 权限。

Claude 的确有原生 subagent skill 预加载机制，但只在所安装版本验证后使用，并只加载该角色任务必需的方法；不能把它当作 Codex 同名字段存在的证据。

适配工具限于开发时的复制/格式校验，不引入模板引擎、常驻同步服务或新治理注册表。不能实现或验证一端时，只报告该端未验收，不声称双端完成。

### 4.3 外部 Pro

Pro 不继承本地 skill 或子代理配置。新 TASK 必须直接附上适用的简短约束，或绑定具体 skill 正文/段落的固定 Git SHA，并说明它们是本请求采用的方法。它不能靠递归查本地索引理解义务。

针对 `render_packet.py` 等现有工具仅修复必要输入映射并离线检查；迁移不发送真实请求。已接受和接受状态不确定的请求不重新渲染、不换绑定、不重发。

### 4.4 旧会话切换

磁盘修改不等于旧会话已切换。切换完成后，在新会话/原生刷新后的角色中验证加载；不能把旧 DM/Transport 的长历史直接继续当作新规则测试。

如果发现实际仍有请求、进程或未完成写入，先保留原 handle 与责任人，不终止或重发来制造干净状态。只对不涉及现有外部效果的部分继续迁移。

## 5. 必须同时落地的研究流程修正

本节是明确的未来流程变更，不是文件搬家；所有者采纳本计划后按此写入现行角色和 skill。冻结对象依其原卡保持不变。

### 5.1 拆开授权、流程、证据和执行状态

在已有文档中分别表达：是否 approved；方向 lane；对象 evidence class/claim ceiling；当前 execution state。不要增加四套独立注册表。

批准集合决定能否安排研究投入；lane 决定默认流程；证据等级决定能声称什么；execution state 描述现实。`ACTIVE` 不代表获批，`CONFIRM` 不代表效果已成立，`CLOSE` lane 不等于已获得 Portfolio 的方向 PARK/CLOSED 决定。

`APPROVED_SET.md` 保持执行授权的唯一现行表。其他 Portfolio 表是视图；方向 DIRECTION 记录科学状态与当前对象；原始结果来自 summary/native outputs。不得为清理冲突而批量重判历史生命周期。

### 5.2 批准集合、结束与生命周期

调度先检查 pause，再检查 approved set、当前对象权限和可用资源。只有属于集合且具有已授权工作、没有暂停限制的任务才进入执行。空闲容量不构成新任务理由。

对象完成首先产生结果与 intake，不自动进入下一对象、不自动 CLOSE 方向、不自动换 host、不默认使用下一周额度。可继续完成已经明确授权的依赖步骤；准备建议不等于执行建议。

若按现行授权正式进入 CLOSE lane，落实已有“退出可执行集合、排队 closing memo”的规则，而不创建新的生命周期决定。普通 object completion 或一次不利结果不能冒充 lane CLOSE。

Portfolio review 只由所有者触发。预算不足、关闭建议和候选加入可以准备并排队，不由循环自行发起请求。approved set 中未获批的 parked backups 不自动拉入。

### 5.3 EXPLORE：批次自治，不逐 pilot 审批

算法 pilot 的证据等级统一为 B/EXPLORE，`PILOT` 是探索性标记；A/RECON 只报告工程/测量事实，不能用 A 标签发布算法效应。历史标签不重写。

已批准方向、已接受机制家族、现有额度内的 pilot 由 DM 本地选择，无逐 pilot Pro。涉及真正方向级新家族/机制选择时，批次层面最多一次有针对性的 Innovator/Convergence 问题；不是每批无条件增加一次咨询。

可以先提出三到五个候选，再按能区分的解释和成本剪枝；最终执行必须计入实际 fits。四 fit 额度可以容纳两个两臂单 seed pilot，不是四个任意臂数 pilot。

pilot 保留简短问题/对照、真实学习与测量、signed effect、n、暴露、关键失败和下一步；没有正式 MEI 成功判决。没有正结果仍可支持有具体理由的有界后续；正结果也不赋予无限追加。

轻量化优先减少仪式、无关臂和不必要的评估，不默认把训练缩短到不足以观察学习；不得增加“必须先证明可学习或算出 oracle”的新前置实验。

### 5.4 CONFIRM：冻结解释，普通结果无需再投票

CONFIRM lane 表示采用确认性流程，不自动把 B 升为 C。未来开发性、边界明确的对象可保留 B；承担结论性固定总体比较的对象使用 C-BENCH。不能因为写了冻结卡就自动获得更强主张，也不能因已有 `B + CONFIRM` 标签就改写历史。

普通确认对象一次 card-freeze Pro，覆盖正/小/负、宽区间、边界值、缺失和无效情形。结果落在规则内由 DM 直接 intake；只有改变比较含义的未覆盖事件、实质异议或已明示的返回要求才走例外审阅。宽区间、负号或未达到旧分数不是自动例外。

A/B 不因进入 CONFIRM lane 获得额外 consumption 状态；具名对象仍按自身停止边界结束。C 的原有消费语义保留。

### 5.5 统计修正

删除“MEI 足够大即可代替独立训练重复”的替代条款。MEI 表示值得关心的差异；训练波动和目标精度决定重复设计。一个训练实例不能估计训练总体不确定性；更多 episodes/checkpoints、bootstrap 或扩大 MEI 都不能补出独立训练 n。两个 seed 也不是充分性的保证。

学习性能确认应安排与主张匹配的独立训练实例；若现实只剩一个可用实例，只报告该条件性观察和不完整状态，不伪造总体结论。对便宜探索不强设统一五/十 seed 门槛。

调参与最终评价分离到主张需要的程度；选择暴露单独列出；配对由共同外生设计和真实独立单位支持，不由 seed 数字相同推定。区间说明模型和小样本限制；不把小点估计当等效，不把宽区间当零效应，不把五个正号当充分证据。

没有预定追加规则，不看结果补 seed、换 checkpoint、增加终点、丢掉不利块或运行到显著。缺失配对不填零、不默认为随机缺失；保留可信窄事实及限制。

### 5.6 MARL comparator 与共享 baseline

研究方法 skill 直接要求说明 actor/critic 信息权限、刷新频率、通信/表示差异、动作约束、reward/termination、normalization、recurrent reset、训练预算、调参权和评估选择。

区分局部 actor 的 MAPPO、中央输入 CF、固定时钟/中断消融和特权上参照。相同外生信息不等于相同带宽、表示、优化难度或 matched compute；完整方法收益不是单一机制的因果证明。

复用既有 `docs/research/baselines/<host>/`、`experiments/baselines/<host>/`。baseline package 至少包含可重跑配置/版本、信息与任务条件、训练及选择暴露、逐 seed 曲线、结果和适用范围。复用不匹配时说明差异，不偷偷当公平对照。

迁移只建立记录与复用方法，不为填满 baseline library 启动训练；不把 baseline 完备性或 headroom 变成所有 pilot 的新门槛。K 轴受控机制问题、N 轴共同训练 churn/train-N-test-N/ad hoc teamwork 的区分进入方法说明，不因此新开实验。

### 5.7 风险比例与执行链

DM 继续直接实现；L0 保持简短、可复用 card，不重新复制历史。高风险/shared core/numerics/RNG/checkpoint/result identity/external effects 由独立 reviewer 审查；薄绑定和文档修改采用自查及既有聚焦测试。

MARL 审查优先检查 collector → storage → recurrent replay → loss/update → evaluator 之间的科学语义，尤其信息泄漏、快照一致性、reset 和训练/评估隔离。

迁移中的共享控制面、Pro 发布和启动路径改动也属于高风险；在整体切换前做一次独立审查及必要修复，不对每段文字分别审议。评审本身不发真实 Pro，不启动实验。

现有 Operator/Monitor 处理执行事实，DM 负责技术验收与科学 intake。工程失败不等于科学阴性；观测丢失先接原 handle；源码修复不自动授权新尝试。

### 5.8 预算从对象计数补齐到实际工作量

保留现有 standing budget 和具名卡额度；本轮不杜撰新的 node-hour 数字。新增未来卡的描述与账目：fits、training team steps、evaluation team steps、更新/优化暴露、调参暴露、逐 fit wall、实际 batch elapsed、RSS、线程数及可获得的 CPU 时间。

区分计划/上限/实测，区分 `sum_fit_wall`、`batch_elapsed` 和 `aggregate_cpu`。不能把并发 fit 的时长之和叫作已测整节点占用，更不能承诺除以并发数就是完工时间。

下一次所有者预算审阅决定资源维度的具体额度；未知标 UNKNOWN/待分配，不从缺失推导无限预算。已批准对象不因新增记账字段失效，缺少可选资源遥测不使本来可信的科学结果作废。

核对既有七天窗口的起算规则和每个对象的额度归属。跨周未完成对象不得重置曝光或重复取得同一授权；失败尝试的实际工作量不消失，也不自动返还 retry 权。旧来源未定义的窗口/扣账规则须明确列为待决预算语义，不在迁移中猜造。对新未冻结对象，卡片必须说明计划工作量及其现有额度依据；发现真实资源短缺则报告并排队建议，不因“每周一个对象”推定任意规模都可执行。

复用已有 summary/执行记录，不增加独立账本数据库、持续 profiler 或历史补测。启动路径使用真实节点、解释器、device 和 fresh admission。CF RSS 未知时采用保守并发，从计划内首个 fit 更新估算；不另加 profiling fit。

并发 admission 若可能读到同一未扣减的空闲内存，优先让现有 Operator 串行完成“启动—确认接受”并重新检查容量；不能把多个同时通过的 preflight 当成资源已预留，也不为此建设新 scheduler/lease 系统。

### 5.9 记录与 dossier 修正

每对象三个核心记录：pilot note/card、summary、intake；原始输出与必要执行事实照常保留。可选 dependency/preservation/prediction 等小文件能并入现有记录就并入，不删唯一证据。

DIRECTION、root/direction handoff、tracking 在干净边界刷新；ledger 只记有实际替代项的选择；pilot 不无条件生成 owner item/brief。确认结果和生命周期/Portfolio 信息按现有轻量机制交付。

dossier 的事实列从当前来源读取或由小型已有工具生成，带 source commit/current object/updated-at；人工维护解释与投资建议。没有结构化源时直接核对，不能先建设大平台。

修正旧 FSD headroom 草稿、0.67 参照与新卡混用；分别列 ACVC wrapper 局部收益和完整方法比较，不把方向压成单一 signal 布尔值。历史实验结论原样保留，修改的是当前摘要的准确性。

## 6. FSD 冻结兼容性：本轮不得突破的检查单

当前唯一 approved direction 为 FSD；当前对象为 `FSD_MATCHED_INFORMATION_BASELINE_B01`。准确路径：

```text
docs/research/candidates/flexible_skill_duration/HANDOFF_2026-09-16_matched_information_baseline.md
docs/research/candidates/flexible_skill_duration/FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md
```

| 项目 | 保持不变 |
|---|---|
| 比较 | 站立 D1280 vs central-input flat CF；不是 interruption increment |
| 信息 | CF 按 k=10 更新 legal global state + joint observations snapshot，间隔保持；ego 与私有 GRU 按卡定义 |
| Stage 0 | λ={0.5,1,2} × 两个训练块，共六 CF fits；最高均值 J45，精确并列按 1、0.5、2 |
| Stage 1 | 五个全新块，每块 D1280 + 选定 λ 的 CF，共十 fits |
| 训练 | 每 fit 45×16×500=360,000 training team steps |
| 评估 | 九 panels、每 panel 32 worlds，唯一主终点 J45 |
| 读数 | 五个 G_b 的均值、卡内 df=4 区间、固定 MEI .05 J，重要性与不确定性标签分开 |
| 缺失/无效 | SELECTION_INCOMPLETE 不进入 stage 1；PRIMARY_INCOMPLETE_OR_INVALID 不自动补齐或重试 |
| 结论边界 | headroom_record: not established；不证明 hierarchy 必要性，不重判旧结果 |
| 预算 | 共十六 fits；约 183,500 秒是各 fit 计划 wall 之和，CF RSS 与实际速度未测；不是保证的节点完成时长 |

这张表只是迁移保护核对，不替代原卡全部 seed、输入、隔离、停止和边界细节。

迁移期间不修改 CF 学习器。科研正式恢复后的首项工作仍是：原 DM 按 handoff 实现 CF → 聚焦测试 → 独立 reviewer → 提交推送 → Operator 按精确版本和 fresh admission 启动 stage 0。重构完成本身不触发这个序列。

## 7. 实施阶段与提交顺序

### M0：现场清点与基线捕获

Root 在真实 checkout 核对分支、完整 SHA、worktree、未提交变更、当前会话/handle/Pro binding 和 pause。给定 heads 是历史基线，不是假设当前 HEAD 相同。

枚举当前控制入口：根/目录 AGENTS 与 CLAUDE、`.codex`、`.agents/skills`、`.claude`、相关 spec/operations、native task 配置和现有渲染/分析脚本。记录实际字节与发现路径，检查全局/组织 override 与同名 skill；不导出密钥。

特别核对三处 foreign-edit pending 以及其他 stale vacancy 规则；不得通过 pathspec commit 把他人的同文件修改扫入。协调原写入者或隔离 worktree，不 stash/reset/force push，不假定迁移前没有活动进程。

产出：一份迁移记录中的基线、归属表、受保护对象和实际冲突；不创建长期索引。

### M1：确定现行规则正文与语义变更表

按第 3 节三种类型逐项映射；写清第 5 节未来修正、当前 FSD 兼容性和作用范围。在所有者明确交付迁移任务后，以真实授权来源记录，不伪造过去批准。

梳理尚需原样继承的工程范围/预算/具名例外。准备精简正文，不先大删原文，不移动冻结绑定。

### M2：先构建自包含方法，再切入口

重写研究方法 skill，新增共享工程 skill，收敛现有 loop/Portfolio/Pro/transport/owner-item 方法。优先复用已有 scripts 与 references，修复被迁移改变的相对路径。

这些修改先在隔离迁移分支完成，科研仍暂停；生产入口在新正文齐备前不切到半套规则。

### M3：瘦身 AGENTS、角色与跨运行时适配

精简根与目录 AGENTS、角色 TOML、CLAUDE 与 hub 配置；关键边界直接内联，方法显式触发。清掉活动入口的旧补位、Root replacement Transport、逐事件全量刷新和自动 Portfolio 等指令，不仅处理已列出的三个文件。

保留历史记录中的原话；禁止用全仓库字符串替换改写 archive/card/evidence。迁移分支内修复全部普通调用入口，避免新旧正文同时承担当前规则。

### M4：执行/记录接口的最小修复

离线验证 Pro TASK 方法来源、summary 资源描述、dossier 当前事实与 source 绑定、handoff 简化。复用已有代码；新增脚本只做必要的开发时适配/报告，不变成科研 launch gate。

核对 compute 配置与真实执行节点身份；允许既有授权内的只读状态探测，不进行新的训练/benchmark。没有访问能力时保留 `runtime_unverified`，不编写硬件事实。

### M5：静态、行为与原生加载验收

执行第 8 节测试。科学 fixture 为合成数据或既有副本；外部动作 stub/禁止，不能用真实 Send 或训练验证“不会发送/不会训练”。启动必要的受限测试会话，不恢复生产科研 loop。

独立 reviewer 审查迁移意图、旧适用来源、diff 与实际测试证据；Root 修复并接受。没有原生运行环境时完成可做的部分，明确 native 未验收，不以模型自报替代证据。

### M6：集成、切换、交接

使用现有 Git 集成策略把成组可回退提交进入 main，推送并读取远端确认；不改写历史。方向分支只集成所需的控制更新，不整支覆盖方向代码或证据。

标记旧 spec 为历史/解释入口，移除日常必须读取的旧索引链。在新会话确认新指令链和角色/skill 行为；切换事实进入 handoff。保持研究 pause，交付迁移结论、未验收项和下一恢复动作。

建议提交分组：规则归属与决定；skill 正文；AGENTS/角色/适配；接口与测试；验收和 handoff。每组可审查并按既有规则推送，不为凑提交数量制造微提交。

## 8. 验收：不是 grep 几个词就算成功

### 8.1 静态检查

检查实际生效的 TOML/skill metadata 能被所安装运行时解析；角色注册和名称一致；必要文件在精确版本存在；非历史必经跳转收敛；引用不会回到已退出日常加载的旧 spec；共享正文与派生副本无漂移；AGENTS/角色/skill 大小有前后对照。

扫描 stale 字样需区分“历史记录/禁止旧行为”与“仍在命令执行旧行为”。不得要求全仓库彻底没有 vacancy 一词。

单次迁移的来源映射、字节检查和内容核验是开发验收，不引入运行时 hash-chain、provenance guard 或每-fit 内容校验。

### 8.2 行为测试矩阵

| 场景 | 应有行为 | 禁止行为 |
|---|---|---|
| 用户只要求状态或控制迁移 | 读取必要信息/迁移范围内工作 | 恢复科研、发 Portfolio、启动 fit |
| 集合为空或只有 FSD | 空闲即空闲，只推进明确授权 | 自动补入 parked direction |
| approved 对象有未完成授权步骤 | 原 DM 连续完成范围内步骤 | 每步重新审批或 Root 转发 |
| 覆盖内负结果/宽区间 | 按卡 intake 并保留 | 因不喜欢读数再发 Pro/补 seed |
| 单训练 seed + 大量 episodes | 条件性观察 | 伪造 training-population n/CI |
| 提高 MEI | 不增加独立训练信息 | 免除重复或声称确认 |
| stage 0 缺一个 fit | SELECTION_INCOMPLETE，无 stage 1 | 默认 λ=1、忽略缺失、自动替代 |
| 信息快照/replay/reset 修改 | 聚焦真实路径并独立审查 | 以 thin runner 为理由免审 |
| 仅文案或已审薄绑定 | 自查与必要既有测试 | 全量文献、所有 spec、Pro 仪式 |
| Send 接受状态不确定 | 原 request/handle 核对 | 新请求绕过、第二次真实 Send |
| 多个 fit 争用内存 | 按实际接受状态和新鲜容量调度 | 把并发 preflight 当成 reservation |
| 同文件有其他会话修改 | 协调或隔离并保留 | pathspec 扫入、stash/reset/强推 |
| 旧 dossier 与当前 card 不同 | 修正当前摘要及来源 | 重写历史 card/结果/决定 |
| 旧会话仍持旧规则 | 新会话/原生刷新并验证 | 用“磁盘已改”宣称切换完成 |

### 8.3 原生加载证据

至少覆盖根主会话、一个方向任务、Reviewer、Operator/Transport 的受限替身，以及实际仍使用的 Claude hub/角色。

记录启动目录、版本、有效配置来源、已加载指令文件/角色、真正读取的 skill 与 reference、是否出现意外旧入口，以及实际采取/未采取的工具动作。

使用可用的原生日志、session 记录和工具读取轨迹；模型复述规则仅作辅助。日志可能不暴露完整系统上下文，不据此声称读到不可见内容。无法观测的部分标明限制。

无统一“零次读取”要求：需要核查事实时允许直接读 card/证据/代码。要消除的是无意义的规则查找链，不是科学证据阅读。

### 8.4 完成定义

结构迁移与第 5 节修正均已落入实际当前入口；受保护对象未改义；独立审查关闭材料问题；静态与行为测试通过；声称已支持的运行时完成实际加载验证；远端提交可读；研究仍暂停；handoff 能让下一会话直接确定状态、范围和首个动作。

静态通过但 native 未验证，只能写“代码与静态检查完成，运行时切换未验收”；不能写迁移全部完成。

## 9. 回退和防止再次膨胀

回退采用成组、正常的新提交恢复已知控制版本，不 reset/rebase/force push。回退控制文件不撤回外部副作用、不改变冻结科研对象；若意外外部动作已发生，立即记录真实事实并停止依赖动作，不能通过删日志掩盖。

新的控制规则必须先决定唯一维护位置，再改正文。历史理由写变更记录，不往 AGENTS/角色里追加 dated override。发现现行入口冲突必须修正文，不长期要求模型自行裁决。

大小超标和额外跳转是代码审查提示，不是新运行时门槛。定期整理可随真实控制变更一起做，不新建自动 Portfolio/定时审查循环。

本计划及本次映射表在迁移结束后作为历史任务记录；不加入根 AGENTS 的固定必读集合。

## 10. 依据与版本核对

仓库依据均来自上述暂停快照；执行时对照真实当前状态，不能把旧快照当实时事实：

- 根 `AGENTS.md`、`CLAUDE.md`、`.codex/config.toml`、`.codex/agents/*.toml`、`.agents/skills/*/SKILL.md`。
- `docs/research/portfolio/decisions/2026-09-15-workflow-lanes.md`：lane、轻量记录、审查和预算。
- `docs/research/portfolio/decisions/2026-09-15-portfolio-control-and-approved-set.md`、`APPROVED_SET.md`：所有者触发、批准集合、无补位。
- `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §§4–5、11.4、11.7–11.11：证据负担、统计单位、比例原则。
- `docs/project/ENGINEERING_SCOPE_SPEC.md`、`MARL_RUNTIME_ENGINEERING_SPEC.md`：工程范围、源代码与测试预算、具名附款；完整迁移前必须通读相关现行条款。
- `docs/Claude_docs/changes/2026-09-15-portfolio-control.md`：foreign edits 与同步残留。
- `docs/research/portfolio/dossiers/2026-09-16_PORTFOLIO_DOSSIER.md`、`TWO_AXIS_RESEARCH_PROGRAMME_20260914.md`：当前摘要与研究准备方向。
- FSD 两份当前路径见第 6 节；ACVC 原 memo 为 `docs/research/candidates/acvc/ACVC_CLOSING_MEMO_20260916.md`。

2026-09-16 核对的官方加载资料（文档是机制依据，真实安装版本与加载日志才是本机验收证据）：

```text
https://developers.openai.com/codex/guides/agents-md
https://developers.openai.com/codex/skills
https://developers.openai.com/codex/subagents
https://developers.openai.com/codex/config-reference/
https://developers.openai.com/blog/eval-skills
https://code.claude.com/docs/en/memory
https://code.claude.com/docs/en/sub-agents
```

统计方法背景：Agarwal et al., Deep Reinforcement Learning at the Edge of the Statistical Precipice, 2021，强调有限训练重复下的不确定性报告；不作为统一 seed 配额或新启动门槛。

## 11. Handoff：开始迁移与迁移完成后的交接

### 11.1 交给 Codex 的启动指令

```text
任务：按 HMASD_CONTROL_PLANE_MIGRATION_PLAN_20260916.md 开始控制面迁移。

你是本次控制面迁移的 Root 实施负责人。完成 M0–M6：现场清点、唯一规则归属、
自包含 skill、AGENTS/角色瘦身、Codex/Claude/Pro 适配、计划第 5 节流程修正、
离线行为测试、原生加载验证、独立 reviewer、Git 集成与最终 handoff。

这是控制面工程授权，不是恢复科研：保持 owner pause；不启动训练，不实现 CF，
不发送真实 Pro/Portfolio 请求，不更改 approved set 成员，不作 ACVC 生命周期决定。
科研中的 frozen card、seed、预算、读数规则、历史结果与已接受请求保持原义。

基准线索为 main 941ed56a0、codex/fsd b034cb0d9、codex/acvc 66abf52ca。
先核对实际完整 SHA、worktree、远端、其他写入者、会话与外部 handle。
不得回退后来的提交，也不得扫入他人的未提交修改。

按计划区分原义搬迁、清除已废弃规则和前瞻流程修正；未覆盖的实质冲突列明后果，
只暂停依赖部分。不要另造索引体系、管理代理链、调度器或每次实验的通用验证门槛。

复用现有路径与工具。普通范围内工程步骤连续完成，不逐步骤问权限。
本次共享控制修改用独立 reviewer；没有真实运行时的部分明确未验收。
最后提交推送，在干净边界交接；迁移完成仍不自动恢复 FSD。
```

### 11.2 迁移 handoff 必须记录的事实

沿用项目现有 handoff 路径，当前摘要置顶；只保留下一会话继续工作需要的事实。建议完整结构如下，所有占位项都要换成真实核验结果，未核验不得填写“无”。

```markdown
# Control-plane migration handoff — <实际日期>

## 当前结论
- 迁移状态：<完成 / 部分完成；不得用静态通过代替 native 验收>
- research pause：<实际状态与来源>
- 当前源码/集成版本：<branch + 完整 SHA + 远端核验>
- 运行进程 / Pro 请求 / agent 或浏览器状态：<实际核验及时间；否则未核验>
- 下一个明确动作：<只写一个动作、执行者、现有授权与范围>

## 实际落地
<AGENTS、角色、skill、运行时适配和流程语义修正各自的完成情况；
记录唯一维护位置及提交，不重抄规则全文。>

## 验收与限制
<前后字节/任务加载范围、静态/行为测试、独立 reviewer、
Codex/Claude 的真实加载证据、未覆盖环境与未验收事项。>

## 保留与待决
<FSD 冻结兼容性；ACVC/Portfolio 未执行项；foreign edits 的真实处理；
具体阻塞、责任人、触发继续的事实。>

## 恢复入口
<下一会话直接读取的当前迁移记录、当前 task/card 与必要代码入口；
固定 SHA 用于已冻结对象，当前控制用切换后实际集成版本。>

## 回退
<已知良好控制版本、应以新提交撤回的迁移提交组；
真实外部效果另行核对，不通过 Git 回退假装撤销。>
```

### 11.3 后续科研交接的固定原则

Root handoff 只写跨方向变化、共享依赖、pause 与下一协调动作；direction handoff 只写当前科学对象、实现状态、精确执行输入、结果与下一有界动作。card/summary/批准集合仍是底层事实来源，handoff 不是第四份科学规范。

不在每次无变化等待后刷新；不靠“下次先读上一份 handoff，再读更早 handoff”恢复上下文。当前摘要必须直接给出足以继续的入口。

当前 FSD 的未来恢复入口仍是第 6 节的 matched-information handoff。正式恢复后先实现 CF、审查，再由 Operator 启动 stage 0；迁移结束的默认终点是“控制面完成交接，研究保持暂停”，而不是“顺手开始训练”。
