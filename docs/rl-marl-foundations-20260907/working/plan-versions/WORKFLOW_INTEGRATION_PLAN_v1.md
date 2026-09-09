# RL/MARL 基础知识接入 HMASD 控制面的详细修改计划

版本：v1，2026-09-08。状态：供独立 Astra/max reviewer 评审；尚未实施控制面修改。本计划的通过只代表方案可供执行，不代表科学对象、代码或实验已获验收。

## 1. 目标与已确定的边界

让负责科学判断的代理在提出问题、设计对象、选择比较、解释结果和写 Pro 问题时，能够稳定到达已有 RL/MARL 基础知识，并据此改进判断。知识正文保持独立；现有经验规范只加入短的使用条款；扩展已有 hmasd-scientific-tools，不新建一个职责重叠的通用研究方法 skill。

“稳定”在此指有明确的角色入口、明确的文件和章节路径、可访问的固定版本以及可检查的实际使用行为。skill 的 description 是发现提示，不是保证每次自动读取的运行时事件钩子。本方案不新增调度器、读取守卫、打卡日志、阅读通过状态或实验准入条件。

本次用户要求为“给出详细修改计划，并交给独立 reviewer Astra/max，注意阅读整个控制面文件来设计和评估”。因此本次交付是计划、阅读覆盖和独立评审，不包含实施、运行科学实验、发出 Pro 请求或改动正在执行的研究对象。

保留以下语义：

- 当前 owner 指示、AGENTS、现行规范、各方向卡和冻结对象各自的适用范围；知识材料不获得决策权限。
- Root 执行、Portfolio 科学比较和计划、DM 对象判断、独立 Transport 传输的现有分工；角色模型和 effort、工作集计数和远程运行规则不变。
- §11.8/§11.9 的比例原则：基础知识不能变成先证明、先找正结果、先穷举、先做完整因果解释或先满足固定种子数的普遍门槛；A/B 不以 Pro 轮次为启动条件。
- 已冻结问题、奖励、信息集合、比较器、估计量、预算、RNG、输入 SHA 和结果历史不因本计划被重新解释。
- FOUNDATIONS §7 及若干 topic-notes 中的“当前研究选择”只属于这次讨论的研究设想，不能变成所有 HMASD 方向的 return-only 排序、MAPPO 强制基线或新的全局问题定义。
- grilling 仅用于用户明确要求的交互质询；科学知识读取不得自动调用 grilling，也不得因此暂停无人值守对象判断。

## 2. 阅读依据与现状诊断

设计者已逐文件全文读完 149 个文件，共 1,458,227 字节。范围包含根与区域 AGENTS/CLAUDE、完整 .codex 配置与角色、完整 .claude 设置/角色/skills、完整 .agents skills/引用/脚本/third_party、docs/project 清单中全部当前和历史文件、完整经验规范、Portfolio 和 Research Map、owner 表面及六项直接相关决定、九份基础文档、五个相关测试文件。长文件按连续片段读至结尾，截断处已补读。

逐文件版本和边界见 working/CONTROL_PLANE_READING.md。起始 HEAD 为 2cd77f3754d7e6d94f064cb384b66f214b8b932b；2026-09-08 06:41 UTC 复核 HEAD 为 60b7101c8c447252a2438ffca3371a867bbdb0f3，149 个文件的内容摘要未变。这是工作区实际字节的阅读记录，不声称所有文件均已提交或是原子 Git 快照。独立 reviewer 的实际阅读范围另记于评审原文。

发现的直接问题：

| 当前入口 | 现状 | 本方案处理 |
| --- | --- | --- |
| AGENTS“Scientific tool use”及科学角色 Tool adoption | 触发主要是检索、计数、分析、性能和适配器；“我要设计一个对象/解释这个结果”未明确进入基础知识路径 | 给科学判断增加明确触发，并由角色短指针落实 |
| hmasd-scientific-tools | 已有工具路径与比例边界，适合作为共享入口，但没有科学基础阅读模式 | 在现有 skill 增加模式和一份短路由参考 |
| MARL_EMPIRICAL_EVIDENCE_SPEC | §11.8/§11.9 已约束方法和问题复杂度；§1 仍把 ALGORITHM_PRINCIPLES 表述成被细化的合同 | 增加知识使用条款，移除这条失效的当前权威关系 |
| ALGORITHM_PRINCIPLES | AGENTS 已定义为历史背景，文件开头却仍自称 durable scientific contract | 只加当前历史状态说明，保留历史正文和证据路径 |
| Pro 作者和 renderer | 正文要求适用经验规范，但 reference_files 由调用方提供，且只允许读取所列文件；规范和基础材料可能没有入清单 | 显式列入方法来源；解决科学输入版本与知识版本不同的情况 |
| 现有测试 | 能覆盖作者/父任务/Transport 路由、固定 TASK 字节、历史绑定等；没有证明科学问题会实际触发知识读取 | 保留原回归，补最小行为验证与负例 |

其他历史漂移已区分，不借本计划全面治理：旧 Root 兼任 Transport、heartbeat/tracker、早期 M0/positive-first、旧全链工程门槛、Claude 历史容量和 owner 处理文字等。只修复本次新增读取路径直接会重新激活的错误入口；其余作为评审观察留存。IMPLEMENTATION_PLAN、UAV_G0_READINESS 等已有历史状态标识的文件无需重复修改。

## 3. 接入路径与触发范围

本地科学判断：

用户/当前 assignment → AGENTS 和科学角色明确触发 → hmasd-scientific-tools 的 scientific-reading 模式 → 经验规范 §11.8、§11.9、§11.10 → FOUNDATIONS §1–§6 → 与问题有关的 topic-note/原始来源段落 → 当前卡或 intake 中的实际判断。

Pro 科学判断：

DM/Portfolio 完成上述本地判断 → Pro 作者列出固定版本的规范、基础和必要专题 → renderer 将明确路径及版本写入 TASK 的读取清单 → Transport 原样执行 → Pro 在所列范围阅读并给出节点决定 → 原 DM/Portfolio 按现有流程 intake。

知识文件没有“反向要求”代理调用另一个 skill 或运行命令的权力。当前卡/spec 决定要求；知识说明概念与假设；来源记录说明证据可达程度。不能通过知识文档链接递归扩张任务。

| 任务情形 | 是否进入 scientific-reading | 阅读深度和输出 |
| --- | --- | --- |
| DM 新机制/新卡、比较器或估计量选择、结果 intake、recast 问题 | 是 | 先读规范相关条款和基础摘要，按概念进入专题；在现有卡/intake 中写影响判断的假设或证据 |
| Portfolio 跨方向比较、投资或科学 Pro 问题 | 是 | 读取比较所需概念及证据约束；保留原 headroom/MEI/生命周期规则 |
| 独立 scientific critic | 是 | 针对受审主张、信息条件和推断强度读取，不展开成全方向审计 |
| CM/reviewer 遇到奖励、信息泄漏、终止语义、异步决策、训练/评估单位等科学语义问题 | 条件触发 | 只读受影响概念；不能借此自行重选科学对象 |
| CM 常规代码修复、例行 verifier、operator、Transport、Root 计数/推送/收据 | 否 | 沿用原工具和执行流程；没有基础知识预加载 |
| 用户明确要求 grilling | 按其专用 skill | 仍是用户质询；不成为无人值守研究的必经路径 |

已经在同一任务读过且相关内容未变时复用上下文；只有新概念、新规范版本、冲突或实际缺口时补读。不要求每个 turn 重读。

## 4. 逐文件修改

### 4.1 保持基础正文独立，明确知识和会话选择的范围

1. docs/rl-marl-foundations-20260907/README.md：在开头说明这是共享知识入口与来源目录，不是新规范；列明 FOUNDATIONS §1–§6 是基础概念，§7 是本次讨论的选择记录。保留现有文件路径和证据链接。
2. docs/rl-marl-foundations-20260907/FOUNDATIONS.md：增加用途/权威说明；把 §7 标题和首段明确为“本次讨论的研究设想与待落实选择”，注明不覆盖现有方向卡、不等于全局 owner 决定。§1–§6 不夹入工作流命令，不把教材简化结论改写成普遍定理。
3. topic-notes/02_MARL.md、03_HIERARCHY_ASYNC.md、04_EMPIRICAL.md：仅给包含“当前研究选择”的段落添加同样的局部范围提示，避免 Pro 按专题阅读时丢掉 FOUNDATIONS 的范围信息。
4. sources/READING_MAP.md、topic-notes/01_RL.md 和两份既有 working 证据：原则上不改。保持原文版本、可访问性和检索缺口记录；没有新读取就不扩大“已读原文”的宣称。

不迁移日期目录、不复制第二份正文、不建立新的科学卡。以后知识增补沿用这一入口，当前科学决定仍回到各 DIRECTION/card。

### 4.2 在经验规范增加短使用条款，修复直接权威歧义

文件：docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md。

- §1 Purpose：将“本规范细化 ALGORITHM_PRINCIPLES”一类当前合同关系改为“本规范给出当前经验研究证据标准；ALGORITHM_PRINCIPLES 保留为历史背景”。不改现有证据级别及适用例外。
- 在现有 §11.9 后新增 §11.10“Foundational knowledge in scientific judgment”，不插入或重编号旧条款。建议英文正文：

“Before designing or interpreting a scientific object, use the scientific-reading mode of hmasd-scientific-tools to identify the relevant RL/MARL concepts, assumptions and inferential limits. Reuse material already read when current, and read only the topic and primary-source passages needed for the actual question. The shared foundations are explanatory references; the current owner instructions, this specification and the applicable card determine requirements. Record a material assumption or source in the existing card/intake when it affects a decision. Foundational knowledge creates no additional experiment, proof, positive-result, seed-count, Pro-consultation or approval prerequisite. Preserve sections 11.8–11.9, frozen scientific meaning and historical evidence. Session-specific choices in the knowledge notes do not apply to other directions.”

文件：docs/project/ALGORITHM_PRINCIPLES.md。

在开头增加简短、日期明确的 HISTORICAL_BACKGROUND / NON-OPERATIVE 状态说明，链接当前 AGENTS 与经验规范。保留正文作为当时的科学背景；不删除、不移动、不逐条重写其历史规则。本次只修复其被新路径当作现行规范的风险。

### 4.3 扩展现有 scientific-tools，不创建平行 skill

文件：.agents/skills/hmasd-scientific-tools/SKILL.md。

- frontmatter description 增加正向触发：提出或设计 RL/MARL 科学对象、选择比较/估计量、解释结果、评审科学主张。
- 正文增加 scientific-reading 入口，链接 references/scientific-reading.md；现有检索、计数、run-summary、性能和适配器模式保持原语义。
- 明确机械执行不触发阅读；科学阅读不自动调用 grilling，不要求所有原文、所有工具或所有专题。
- 在本文件已有“谁解释工具结果”的句子中，按当前角色改为 DM/Portfolio/适当 Pro 节点；避免把 Root 的执行身份重新写成科学选择者。这是本入口的局部一致性修正。

新增：.agents/skills/hmasd-scientific-tools/references/scientific-reading.md。

内容限于使用路由，不复制知识正文：

| 问题 | 先读摘要 | 按需专题 |
| --- | --- | --- |
| 回报、状态/观测、策略、终止/截断 | FOUNDATIONS §1–§2 | topic-notes/01_RL.md |
| 多智能体信息、CTDE、非平稳性、比较器公平性 | §3–§4 | 02_MARL.md |
| option、异步事件、持续时间、层级信用 | §5 | 03_HIERARCHY_ASYNC.md |
| 独立训练单位、评估不确定性、选择偏差、估计量 | §6 | 04_EMPIRICAL.md |

同时列出：规范 §11.8–§11.10 入口、材料范围、复用已读信息、何时到 READING_MAP 或现有 local-literature 路由查原始来源、来源不可访问时如何准确记录缺口。原文检索只为具体不确定性服务，不设置“读完教材再研究”的顺序。

现有 references/local-literature.md 只需在入口注明基础概念先经 scientific-reading 定位，具体文献疑问继续走现有检索路径；若原文本身已无歧义则无需编辑。adapters.md 和 summarize_runs.py 无需修改。

### 4.4 把触发落实到实际角色，保持跨运行时一致

文件及修改锚点：

| 文件 | 锚点/修改 |
| --- | --- |
| AGENTS.md | Scientific tool use：在已有五类工具触发外加入科学对象设计/解释/比较/评审，明确进入同一 scientific-tools 的 reading 模式；不复制知识或改职责表 |
| .codex/agents/hmasd-direction-manager.toml | Tool adoption：在机制/卡/比较/intake/Pro 问题等科学判断前使用 reading 模式；继续“当前 assignment 与相关章节优先” |
| .agents/skills/hmasd-portfolio-task/SKILL.md | Core/科学比较与 Pro 问题入口：同一短指针；纯 Root 命令排队和收据不触发 |
| .codex/agents/hmasd-research-critic.toml | Tool adoption：按当前受审主张进入 reading 模式 |
| .codex/agents/hmasd-cm.toml、hmasd-reviewer.toml | Tool adoption：仅在本任务涉及科学语义时进入 |
| .claude/skills/hmasd-research-hub/SKILL.md | 科学判断入口增加相同共享路径；不改现有 runtime 的调度容量和 delegation 机制 |
| .claude/agents/hmasd-research-critic.md | 同 Codex critic 的科学触发 |
| .claude/agents/hmasd-cm.md、hmasd-reviewer.md | 同 Codex 的条件触发 |

根 CLAUDE.md 和六个区域 CLAUDE/AGENTS 已通过根入口继承；除非实现时发现该入口确实被遮蔽，否则无需添加重复正文。普通 implementer/scout/verifier/operator、Transport 与 Grok 机械执行角色不增加强制知识阅读；发现越出其工程任务的科学选择时仍按现有规则返回 CM/DM。

以上角色只添加短指针；路由细节以 scientific-reading.md 一处为准。配置中的 model、reasoning effort、权限、工具列表、并发限制、发送与回执规则均不改。

### 4.5 让 Pro 真正能读到固定版本的方法来源

这是方案中风险最高、需 reviewer 独立判断的部分。

当前 renderer 把所有 reference_files 固定到顶层 commit_or_ref，并禁止读取未列出的文件。只在正文里写“请遵守 spec”或“读 FOUNDATIONS”不够：该版本可能不存在这些文件，或者文件不在 allowlist。也不能为放入新知识而偷偷更新冻结科学输入 SHA。

建议方案：

A. 作者显式列出方法来源。修改 .agents/skills/hmasd-pro-research-prompt-author/SKILL.md 的 scientific question/burden 部分：新科学请求须在已有 reference_files 清单中明确列入经验规范、FOUNDATIONS，以及本问题确需的专题或原始来源。purpose 写具体章节和用途，provenance 写版本和知识材料的范围。不得在列表外递归读取链接，也不得将 FOUNDATIONS §7 当作适用于其他方向的决定。

B. 对作者的 reference_files 项增加一个可选 commit_sha 字段；省略时继续使用顶层 commit_or_ref。只接受完整不可变的 Git SHA，不接受分支名、latest 或隐式当前 HEAD。这样科学 card/evidence 仍用原冻结顶层 SHA，较新的规范/知识文件可以显式使用另一已发布 SHA。不引入 method registry 或第二套 Transport 协议，也不改变顶层科学输入的含义。

示意输入：

{
  "commit_or_ref": "<原科学输入完整SHA>",
  "reference_files": [
    {"path": "<当前卡路径>", "purpose": "<当前冻结对象相关节>", "provenance": "<冻结事实>"},
    {"path": "docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md", "commit_sha": "<已发布方法来源完整SHA>", "purpose": "§11.8–§11.10 的现行适用条款", "provenance": "方法约束；不改写冻结对象"},
    {"path": "docs/rl-marl-foundations-20260907/FOUNDATIONS.md", "commit_sha": "<同一已发布方法来源完整SHA>", "purpose": "§1–§6 的相关概念；§7 仅为原讨论记录", "provenance": "解释性材料，无独立决策权"}
  ]
}

C. 修改 render_packet.py：

- validate() 保留并校验可选 commit_sha；路径仍按现有规则去重，不利用同一路径的多个版本规避歧义检查。没有这个字段的输入仍可规范化和渲染。
- render() 在每个列表项打印实际生效的完整版本；将“所有文件只能取顶层版本”的绝对措辞改成“每个列出路径只能使用其列出的固定版本，省略覆盖的项继承顶层科学输入版本”。PROMPT_BODY、Evidence to read 和由其生成的 TASK 需同步，不能一处允许另一处禁止。
- 不自动猜版本、不从移动分支读取、不因方法版本较新而重写任何科学项。作者在渲染前确认方法来源在远端该 SHA 可读；知识文件仍未发布时先完成独立可用工作，不伪称已提供给 Pro。
- 方法段保留简短关键提醒，把完整规范约束指向明确列出的规范版本与章节；避免继续维护一大段与 spec 独立演化的复制品。缩减旧摘要前逐条核对语义都能落到现行 §11.8/§11.9，不能顺便删除有效约束。
- 既有顶层 SHA、source/parent/operator、binding、delivery base、response path、模型和发送语义不变。Transport 只处理固定任务字节，不解释方法、选择来源或替作者补清单。

D. 相应更新 references/github-connector-contract.md、references/github-delivery.md 以及 references/attachment-delivery.md 中“全部来源共用一个 SHA”的措辞，仅限其确实与 C 冲突的段落。附件兼容路径也必须能表达相同清单；不恢复已退役发送方式。

E. 明确缺口语义：当前必要规范或决定所需证据不可达，按既有节点流程说明精确缺口；某份解释性基础材料不可达，只能声明该知识上下文未读取，并由科学作者判断是否影响当前结论，不自动宣布整个方向或实验不可进行。此接入不是 A/B 的新增启动门槛。

此设计的 reviewer 重点：是否可仅在作者与 renderer 层完成，是否有其他现行合同把顶层 SHA 定义为全部输入唯一版本；若有，必须在评审中明确兼容修正及最小受影响文件，不能把隐藏的单版本假设留给实施者。若独立评审认为扩展逐引用版本的风险不划算，可提出同等保留冻结科学输入且可访问新方法来源的替代方案；不能通过“升级科学 SHA”掩盖冲突。

## 5. 验证与验收

验证分开回答“路径是否正确”和“代理是否真的使用了知识”。当前计划阶段不执行这些验证、不发测试 Pro 请求，也不启动训练。实施时先利用已有检查，再补确有信息价值的用例。

### 5.1 静态与确定性检查

- 用现有 YAML/TOML/Markdown/skill 检查方式确认 frontmatter、角色配置和链接有效。新科学入口均指向同一个 reading 模式；不把所有角色无条件引入。
- 检查新增知识用语中没有自动 grilling、固定种子门槛、先正结果/先证明/先完整机制的要求；这只是辅助检查，不能作为行为正确的唯一证据。
- renderer 用例：旧输入缺省继承顶层版本；新方法项可固定到另一个完整 SHA；无效/移动版本拒绝；路径/版本按对应项打印；原科学 SHA、交付 base、绑定和角色不被改写。
- 在现有 tests/skills/hmasd_pro_research_prompt_author_test.py 中增加上述有关用例；保留原来的 Codex singleton 和 CALLER_DIRECT 覆盖，不改其模型或路由断言。
- 在既有 tests/skills/hmasd_pro_conversation_binding_test.py、hmasd_chatgpt_pro_transport_test.py 中使用现有固定 TASK/历史绑定/不确定 Send 保护用例；若输入扩展不触及它们，不凭空增加新的 Transport 状态机。
- tests/skills/test_scientific_tools.py 继续保证没有由匹配标签自动推断 paired-seed 设计；本次不改 run summary 计算代码。

### 5.2 最小行为验证

用临时只读场景和工具读取轨迹评估，不保存为新生产台账。先跑一个当前配置的正例/负例基线，再对变更后的同类任务检查；发现具体失败后修正并重试该用例，不设无理由的重复轮数。

| 场景 | 应观察到的行为 | 应避免的行为 |
| --- | --- | --- |
| DM 面对局部观测下的 MARL 比较设计 | 到达 spec 与 FOUNDATIONS 的信息/比较章节；按需要进入专题，指出适用假设 | 只从标题复述；强迫全状态或完整因果证明 |
| DM 解释 seed/episode 混合统计的结果 | 区分训练独立单位与评估回合，限定结论并给比例适当的下一步 | 把匹配 seed 标签当自然配对；规定统一种子数量 |
| CM 修正终止与截断或异步持续时间语义 | 条件触发相关基础阅读，维护冻结卡语义 | 自行换奖励、比较器或扩展对象预算 |
| 普通格式修复/commit push/Transport receipt | 不进入科学阅读和 grilling | 读完整教材、向 owner 请求知识确认 |
| 另一方向使用其既有主指标和基线 | 知道 §7 只是本次讨论记录，继续使用该卡 | 套用本次讨论的 return-only 或 MAPPO 选择 |
| Pro 作者构造“旧科学 SHA + 新方法 SHA”的离线输入 | 列表中的路径均可在所列版本解析；科学输入保持原样；输出正文无单 SHA 自相矛盾 | 从 latest 补读、静默移动科学 SHA、声称已发出 Pro |

行为验收看实际读文件/使用证据，而非代理说“我已理解”。需要覆盖 Codex DM 与 Claude hub 两条科学入口，以及二者工程角色的条件触发；同一套用例可复用，避免重复建设。如果离线行为运行能力不可用，准确保留这个未验证项，不能用字符串匹配宣布稳定性已证明。

### 5.3 验收完成的定义

以下同时成立，才可把本实施称为完成：科学正例能够到达相关知识并影响判断；机械负例不被扩张；没有新的科学门槛或跨方向选择泄漏；新 Pro 清单的固定来源可访问且保留旧科学输入；存量已接受/发送不确定请求不被重写；相关现有检查通过，独立 reviewer 没有未解决的阻断项。

本方案不承诺“所有以后模型调用必然按指令执行”，也不用这种不可检验承诺替代实际验证证据。

## 6. 实施次序、并行与发布

1. 审核本计划：Astra/max reviewer 独立读完整控制面和方案，指出具体冲突、遗漏和可接受的最小改动；作者逐条处置并回交同一 reviewer 复核。当前阶段只归档计划/阅读覆盖/评审原文与处置表。
2. 用户后续要求实施时，使用已存在的共享控制面 checkout、一个编辑负责人和显式 owned paths。控制面计划不属于新研究方向，不开占位 direction 分支；保持其他 writer 的未提交内容。任何实际需要的 shared-index 协调只围绕具体 Git 操作。
3. 第一批：基础范围说明、spec 短条款/历史入口、scientific-tools reading 路由和各角色短指针作为一致变更提交，避免出现入口指向不存在的文件。受影响文档解析及本地行为验证可以在提交前短运行。
4. 提交后立即按仓库规则推送当前分支；确认新方法来源的固定 SHA 在配置远端已发布。不得因为要等待下一批而将已提交内容留在本地。
5. 第二批：Pro 作者/renderer/合同与有关测试一起完成。用第一批已发布的完整 SHA 构造离线读取清单示例；验证不通过则修复本工程批，不向真实 Pro 发送测试请求。
6. 高风险处是 Pro 输入版本和方法约束，因此保留独立工程 review。模型/effort 按当前角色配置；已完成的三批 CM_MODEL_COMPARISON 临时比较不重启、不把本方案当成新增比较批。
7. 接入只作用于新的知识判断和新的未发送请求。已接受请求、发送状态不确定请求、已封存 TASK/PROMPT/HANDOFF 及其固定 SHA 不重新生成、重发或改字节；其结果仍走原绑定归档/intake。存在的 READY_TO_DISPATCH 请求也保留原件，是否生成一个新请求须有原科学作者的具体任务理由，不能因本次措辞更新批量替换。
8. 已活跃本地会话在下一次本来需要科学判断的干净边界进入新路径；不为推广 skill 打断实验、重建所有任务或重设上下文。

所有实际提交仍使用显式路径、当前 runtime attribution trailers 与 scope 行，并立即推送；不使用 add -A、stash、reset、force-push 或历史重写。长的可移植检查按已提交精确版本走既有 remote-first；本改动的短文档/renderer检查留本地即可。总工作限于上述范围和必要兼容修正，不包含性能实验或新的科学调用预算。

## 7. 风险与退出方式

| 风险 | 处理与可观察证据 |
| --- | --- |
| skill 仅靠自然语言发现，科学判断漏读 | AGENTS+具体角色双入口；以实际读取轨迹验收 |
| 过度触发拖慢机械任务 | 角色条件和负例；复用已读上下文，知识文件无递归命令 |
| 规范被教材简化观点替代 | §11.10 明确层级、claim ceiling 和比例边界；保留来源限制 |
| 会话选择污染所有方向 | 正文与专题局部范围提示；其他方向场景的反例 |
| Pro 清单写了文件却版本不存在 | 作者确认已发布固定 SHA；离线逐路径解析；不猜 latest |
| 逐引用 SHA 与旧合同冲突 | reviewer 检查所有直接合同和 renderer 分支；顶层科学输入不变 |
| 缩减 renderer 方法摘要时漏掉有效约束 | 原段落逐条对照现行 spec 后再删；不以“去重”为名删科学要求 |
| 并发 writer 修改已读表面 | 实施前复核受影响文件摘要，只补读变化部分，显式协调重叠路径 |
| 旧 Pro 请求被重新解释或重复发送 | 无存量迁移；现有固定字节/历史绑定测试继续通过 |

如果实施后发现阅读模式导致误触发或科学要求扩张，用新的前向修正提交停用/修正受影响入口；保留知识、评审、结果和已发请求原件。renderer 的新可选字段若须停用，先保证现有含该字段的未发送输入仍有可解释的处理方式；不能简单删除支持让归档失去可读性。退出不删除证据、不回写历史、不重放科学运行。

## 8. 本次交付及 reviewer 核查要求

交付文件：

- WORKFLOW_INTEGRATION_PLAN.md：这份逐文件方案及最终修订状态。
- working/CONTROL_PLANE_READING.md：设计者实际全文阅读文件、版本摘要与范围。
- working/INDEPENDENT_REVIEW.md：Astra/max reviewer 原文、其实际阅读范围、受审计划版本与摘要；不把独立预读误称成通过。
- working/REVIEW_DISPOSITION.md：每项发现、修改/不改的理由、最终定位和 reviewer 复核结论。

请 reviewer 独立判断：整体分工/现有 skill 是否冲突；是否已覆盖真正的科学角色入口；spec 只约束使用而没有塞入知识正文；全控制面是否存在未被识别的相反规则；逐引用 SHA 是否值得及需要哪些最小兼容改动；存量请求与冻结对象是否安全；行为验收是否足以支持“稳定接入”而没有新增实验门槛。严重发现需给出文件/章节和具体失败场景；不能仅检查文本关键词。

当前实施授权、真实实验验收、Pro 最终科学决定与这份计划的工程评审是不同事项。后续若用户授权本计划实施，依既有授权直接推进，不额外要求仓库内部 ACK 或再次确认。
