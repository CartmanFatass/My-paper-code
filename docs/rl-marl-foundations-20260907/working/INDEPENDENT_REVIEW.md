# 科研基础接入控制面计划：独立评审记录

评审任务：科研基础接入控制面计划独立评审；模型 gpt-6-astra，reasoning effort max。评审任务 ID：01a07faa-0744-7d83-8e6b-cef4e6fe91bc。

以下保留独立 reviewer 回传的原文。v1 的精确受审正文见 [v1 版本](plan-versions/WORKFLOW_INTEGRATION_PLAN_v1.md)，SHA 与报告对应；主计划可能已更新为修订版。复核报告另节追加，不能把下面 v1 的“需修改”改写成通过。本次仅为计划审查，控制面尚未实施。

## v1 正式评审原文

正式独立评审原文

受审对象：[WORKFLOW_INTEGRATION_PLAN.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/WORKFLOW_INTEGRATION_PLAN.md)，v1，2026-09-08，242 行、27,569 字节，SHA-256 `609E5118C511108C9498ADECB607975D7843653DE068C779B1CE29008268002C`。我完整读取了现成源文件，并确认最终路径与源文件字节相同。

整体判定：**需修改**。复用 scientific-tools、规范只规定使用方式、角色按科学语义触发的主干成立；§4.5 的可选逐引用 SHA 也值得保留。以下四项应写入修订计划后交回复核。它们都可在本任务范围内解决，不要求新 skill、新 Transport 协议、额外科学实验或 Pro 审批。

**R1 — P1，阻断：Pro 被新规范要求调用一个未交付的本地 skill。**

锚点：计划 §4.2 第 82 行、§4.5A 第 139 行；拟修改 [MARL_EMPIRICAL_EVIDENCE_SPEC.md](C:/Projects/HMASD/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) §11.10；现有 [render_packet.py](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py:677) 的读取范围限制。

失败场景：作者完整按 v1 执行，清单包含 spec、FOUNDATIONS 和必要专题。Pro 读到新 §11.10 的“use the scientific-reading mode of hmasd-scientific-tools”，却没有获得该 SKILL 或 scientific-reading.md 的读取权限，也没有本地技能运行环境。它只能越出清单、忽略规范要求或报告缺口。逐引用 SHA 解决文件版本问题，不能解决这个入口断点。

最小修正：把 §11.10 写成两条等价使用路径：本地科学角色通过 skill 定位阅读；Pro 按固定 TASK 中列明的规范章节、基础和专题直接阅读。TASK 明确采纳所列版本的适用规范及有限科学阅读要求；其他仓库内容仍不能扩张权限。不要为此把整套本地技能、工具命令和调度流程装入 Pro 清单。验收增加“仅能访问清单所列文件”的 Pro 消费者阅读场景，确认没有必要的未列依赖；这个检查可以离线完成，不发真实 Pro 测试请求。

**R2 — P2，阻断：知识与当前选择的分离尚未完整落实，§6 也含会话选择。**

锚点：计划 §4.1 第 68–73 行和 §3 第 45 行；[FOUNDATIONS.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/FOUNDATIONS.md:63) 第 63 行及 §7；[04_EMPIRICAL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md:37)。

失败场景：新路由把 FOUNDATIONS §1–§6 定义为可供所有方向使用的一般知识，但 §6 第 63 行明确含“本次讨论采用的研究判断”。§4.1 主要给 §7 和专题加局部标签，遗漏这个一般知识区域中的选择。另将 §7 继续留在知识正文，只改成“研究设想与待落实选择”，也没有给出此前已同意的“当前选择进入适用任务记录”的承接位置。

最小修正：用本次已有任务记录或一份明确命名的会话选择记录承接 §7、§6 的会话策略句及专题对应内容；知识正文保留必要的范围提示和链接，无需创建研究方向或科学卡。记录中区分“用户已明确选择”“机制假设”“具体实现尚未冻结”：例如当前 return 排名偏好已经明确，MAPPO 具体版本仍未冻结。当前选择不外推至其他方向，也不被一并降格为尚未表达的偏好。增加只读取 §6/实证专题的反例，检查不会把本次投入策略当成全局准则。

**R3 — P2，阻断：缩减 renderer 方法段的保留范围还不可审。**

锚点：计划 §4.5C 第 159 行、§5.2；[render_packet.py](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/scripts/render_packet.py:698) 第 698–755 行。

核对结果：第 703–712 行主要对应 spec §11.9 的问题价值和工作量；第 714–720 行对应 §11.8.2/.3/.6；第 722–748 行对应 §11.9 的 search-before-learning、复杂度和规范冲突处理。这些可以通过明确采纳已列版本的规范来承接。但第 750–755 行的原始来源、工具事实与推断分离、不得声称执行不可用工具、不得强加工具清单/框架迁移等要求，并非逐项完整写在 §11.8/§11.9 中。现有相关测试也没有为这一整段科学行为提供充分回归证据。

失败场景：实现者按“都能落到 §11.8/§11.9”压缩正文，比例原则仍在，工具证据边界却消失；或者规范只被列作不受信任的参考，TASK 没有明确采纳其约束。v1 尚未给出替代短段，无法确认这种变化不会发生。

最小修正有两种：本批保留现有方法段，仅补明确的规范版本/章节和基础阅读入口；或在修订计划中给出实际替代短段及简短保留映射，对未由规范承接的工具证据要求保留一两句明确提醒。若同批缩减，行为验收至少保留一个“有限/零 learner 的昂贵前置搜索”场景，观察是否仍质疑不必要的 search-before-learning，并准确区分已知成本和未知成本。无需新增成本实验或完整映射台账。

**R4 — P2，阻断：发布后的实际启用路径不够具体，现有会话不能假定自动热更新。**

锚点：计划 §6 第 206–211 行、§5.2 第 194 行；拟修改的 [.codex 角色](C:/Projects/HMASD/.codex/agents/hmasd-direction-manager.toml) 与 [Claude hub](C:/Projects/HMASD/.claude/skills/hmasd-research-hub/SKILL.md)。

失败场景：第一批已发布新的 spec/角色入口，第二批作者和 renderer 仍未完成，当前科学作者就进入新要求；或者既有 DM/hub 已加载旧角色、读过旧 skill，编辑磁盘文件后继续沿用旧上下文。其他方向 checkout 也可能仍持有旧 renderer；它当前会在 validate 的 clean_refs 中丢弃未识别的 commit_sha（第 418–424 行）。因此“下一次干净边界进入新路径”需要具体交付动作，不能只作为预期。

最小修正：先发布独立知识文件，再把新规范/角色入口与兼容的作者、renderer 一起启用，或在两批间明确新 Pro 作者路径尚未启用。按既有 clean-boundary 输入同步规则，将所需已提交控制面版本带入实际 authoring checkout。由既有下一条科学 assignment/return 路由携带一次明确的读取指针，说明已读旧版本应补读哪一段；不要新建广播角色、调度器或重启所有会话。增加一个“已经读过旧 skill 的存量会话”场景，检查自然工作边界上的实际补读。以上属于发布与输入交付，不是实验审批或 A/B 启动门槛。

**关于 §4.5 逐引用 SHA 的独立结论：建议保留，按下列最小合同收口。**

当前作者结构没有可直接替代它的固定外部文件 URL 通道：discussion_urls 只接受本仓库 Issue/PR URL（renderer 第 426–432 行），不是任意另一个提交的文件来源。让方法资料与冻结科学证据分别固定版本，有实际必要；移动顶层科学 SHA 不符合本任务边界。

未发现 Transport 程序或注册表把顶层 commit_or_ref 用作“全部参考文件唯一提交”的机器校验键。其同名 reference_files 是附件文件及摘要的表，不是作者的仓库引用列表；TASK/PROMPT 全文字节与现有绑定已经能保全每项固定版本。因此本改动不需要触及 validate_request.py、materialize_packet.py、bind_conversation.py 或 Transport 状态机。

需要在计划中说清以下实现与验收细节：

- 所有引用都产生确定的“仓库、路径、有效 SHA”映射；缺省继承顶层 SHA。对科学卡/证据核对这个有效映射，不能只断言顶层字段没变；本次迁接只给方法来源使用新版本，不静默覆盖科学项。
- 全 SHA 检查必须覆盖继承的顶层值及可选覆盖，并覆盖 github_delivery 与 archive_attachment。现有 validate() 第 369 行只检查非空，完整 SHA 检查只在 prepare_github_delivery() 第 508 行；仅校验新字段会让附件路径仍可继承 main 等移动版本。旧的合法全 SHA 输入继续兼容；历史已接受原件不重新调用作者来生成。
- TASK 和附件正文使用同一份有效来源映射，保留路径去重，明确拒绝空值/移动 ref。不让 HANDOFF 顶层字段成为第二份不一致的引用总表。
- 除计划已列的作者参考文件，还应在 [GITHUB_RESEARCH_COLLABORATION.md](C:/Projects/HMASD/docs/project/GITHUB_RESEARCH_COLLABORATION.md:17) 第 17–18、65、90 行简短澄清：顶层是默认科学输入版本，明确的方法引用可以另有固定 SHA。它们目前是单数表述，不是必须重写全部运输合同的依据；github-connector-contract.md 本来已用 full commit SHAs 复数，实际不冲突的文字可保持。
- 作者在发布前确认来源存在于远端，只证明发布和可解析性。[github-connector-contract.md](C:/Projects/HMASD/.agents/skills/hmasd-pro-research-prompt-author/references/github-connector-contract.md:3) 已明确，本地工具访问成功不能证明当前 Pro 会话能读到。真实 Pro 访问事实沿第一条本来就获授权的请求观察与归档；未观察前如实标为未验证，不增加测试 Send。

**非阻断建议与已确认无问题边界。**

§5.2 已区分结构测试和实际读取轨迹，也有机械负例、同信息比较、训练单位和其他方向指标反例，方向正确。建议在相同临时用例中补一个 Portfolio 科学比较入口和一个 critic 入口；无需为每个角色建设独立测试套件。对 Pro 构造成功、远端文件存在、当前 Pro 实际读取这三个证据层次分别命名。

§4.2 的历史地位澄清有明确依据，适合定点修改；不必重写 ALGORITHM_PRINCIPLES 的历史正文。保留 §11.8/§11.9、普通 B 比例原则、失败证据和冻结对象的设计明确。return-only 仅限本次任务，不撤销资源 admission/cap；循环 MAPPO 的方向与具体实现未冻结也已区分。

Codex Root/Portfolio/DM/独立 Transport 的路由，以及 Claude/Fable hub 的 Root+DM 身份、两方向容量、CALLER_DIRECT 和编辑边界，都应按计划保持。共享 skill 的科学解释责任建议称为“承担科学角色的 DM/Portfolio/相应 Pro；包括以 DM 身份工作的 Claude hub”，防止删除“Root”一词时误删 Claude hub 的科学职责。

计划保留已接受、发送不确定、已封存和 READY_TO_DISPATCH 请求的原件，没有批量重发/迁移；这部分正确。提交后立即推送、显式路径、复用 checkout、独立高风险工程 review、三批比较不重启，也符合当前规则。当前仅有计划审查授权，尚未实施；后续用户要求实施这份明确计划时，无需另加仓库内部 ACK 或 Pro 许可。

**阅读与版本证据。**

复用先前 178 个文件的全文预读。本轮完整阅读计划 242 行、修复后的覆盖记录 168 行；另将覆盖对照中发现的两项未在先前集合中的直接授权记录全文补齐：[owner-review-p2-cutoff](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-05-owner-review-p2-cutoff.md) 28 行、[pro6-delegation-and-starred-trace](C:/Projects/HMASD/docs/research/portfolio/decisions/2026-09-05-pro6-delegation-and-starred-trace.md) 79 行。这里明确补读事实，不把它们算作先前已经读过。

最终工作区全文覆盖为 181 个独立路径、31,639 行、1,959,007 字节；临时源与目标的相同字节不重复计数。范围仍是根/六区域 AGENTS/CLAUDE、全部当前 .codex/.claude 控制文件、全部 .agents 技能及其直接支持、docs/project 全量当前与历史控制记录、经验规范/owner 表面/直接授权记录、三份研究状态入口、基础资料，以及此前逐项列出的运行/输入构造/owner-console 支持与针对性现有测试。正式阶段只复核有关代码段和发生变化的表面，没有重跑整套全文阅读。

修复后的 [CONTROL_PLANE_READING.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/CONTROL_PLANE_READING.md) SHA-256 为 `EEE348114CC69290CB7F243F4D6CE9975262F3C9AF1376E1DDFCEA3993A65E2F`。确有 149 个逐路径数据行，字节求和为 1,458,227，与声明一致；与我此前已读共同表面的摘要相符，PORTFOLIO 的后续变化另行识别。因此原“占位清单无法核查”的证据缺口已经修复，不再列为问题。该数据支持可追溯性；我没有用它替代自己的独立阅读。

正式评审开始 HEAD 为 `890ab614bda28291dbff79ea50910c3ab37c6986`，最终复核为 `e3b8d6aa9c551f4194d97e7f1ad91957689f9e75`。相对预读终点，PORTFOLIO 增加 P30/P31 入口，完整差异已补读；最终摘要 `839667A2F6A614255002E5F782ED812E1B9E0F198C9B8D7659BCE132F2B15B9E`。除覆盖记录修复、新计划及这些状态入口变化外，已读控制表面未变。

未递归审计全部历史方向卡、Pro 正文、实验输出、外部论文全文或 .claude/worktrees 的重复 checkout。这些边界未缩小本次控制指令及直接输入链的评审覆盖。行为验证、单元测试和真实 Pro 可达性本轮均未运行，属于后续实施的验证事项，不能标作已通过。

本轮正式评审已完成；等待 v2 和逐项处置后，在同一任务复核。没有修改文件、提交、运行测试/实验、发 Pro、操作 Transport、联系实际科学 Root/Portfolio 或再委派。

## v2 独立复核原文

精确受审正文：[v2 版本](plan-versions/WORKFLOW_INTEGRATION_PLAN_v2.md)。下面的通过结论限于这份计划；本次未实施控制面。

v2 独立复核原文

受审版本：[WORKFLOW_INTEGRATION_PLAN.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/WORKFLOW_INTEGRATION_PLAN.md)，v2，270 行、37,188 字节，SHA-256 `756B82B2C2F5F17D36D5ADAB1C8E2D40327DAE282E552EABB3DA98B7A365FF0D`。现成源文件、主计划与 [v2 归档](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/plan-versions/WORKFLOW_INTEGRATION_PLAN_v2.md) 的摘要一致。

**整体判定：通过，限计划层面。R1–R4 均已在实际 v2 文本中闭合，没有剩余阻断项，也没有需要再开一轮计划修订的新增事项。** 后续实施仍需用户提出实施要求，并完成计划已经列出的工程与行为验收；本结论不表示控制面已经修改或读取行为已经验证。

| 项目 | 复核结论 | 实际闭合依据 |
| --- | --- | --- |
| R1 / P1 | 已闭合 | §3、§4.2 第 85 行、§4.5A/C 明确本地角色通过 skill 定位，Pro 直接读取固定 TASK 所列规范与知识；不需要本地 skill 或清单外依赖。§5.2 增加受清单限制的离线消费者场景。 |
| R2 / P2 | 已闭合 | §4.1 第 68–76 行明确 SESSION_CHOICES 的承接范围，包含原 §7、§6 策略句、§5 当前机制设想和专题选择。区分用户已明确选择、机制假设与未冻结实现；知识正文只留范围及导航。§6/实证专题单独读取的反例已经加入。 |
| R3 / P2 | 已闭合 | §4.5C 第 163 行选择完整保留现有方法段，本批不压缩；第 164–165 行新增有限的规范采纳与直接阅读，并要求同步澄清正文和 manifest 的绝对排除措辞。工具证据与比例约束不再依赖尚未给出的摘要替代品。 |
| R4 / P2 | 已闭合 | §6 第 231–238 行将知识发布与一致启用分开，第二批同时启用规范、角色、作者、renderer 和合同。实际 checkout 同步、旧 renderer 不接收新字段、存量会话通过下一条自然 assignment/return 获得一次补读指针都有明确动作；没有广播服务、任务重启或等待 Portfolio ACK。 |

§4.5C 的规范采纳与 untrusted-content 边界可以同时成立：约束来自固定 TASK 对明列版本的适用规范要求的明确采纳；教材、知识稿及其他仓库文字仍不能授予工具权限、扩大任务或读取清单。第 165 行明确要求两处既有绝对措辞一起澄清，避免一边采纳规范、一边又排除全部仓库条款。保留旧方法段也没有改变其原有 owner/spec 适用边界。实施时对两种生成正文作整体一致性检查即可，这已包含在计划验收中。

逐引用 SHA 的新增细节没有引入新的合同冲突。共同 validate 覆盖顶层继承值及覆盖值、同时覆盖两种交付模式；逐项核对科学来源的有效映射，保留旧合法全 SHA 输入；同一映射生成正文，HANDOFF 不维护第二份表。这解决了 v1 中附件路径和“只看顶层不变”的遗漏。源版本在第二批发布后选取，不要求代码预知自身未来 SHA；科学卡/证据的冻结映射保持，既有请求不重生成。Transport 的附件摘要表、绑定和状态机仍保持原用途，直接合同只作必要澄清。

§5.3 的验收边界诚实且适当：代码、离线构造、实际本地读取行为和远端来源可解析性完成后，可以验收这次控制面实施；当前 Pro 会话实际读取仍单独标作“未观察”，只随下一条本来就获授权的真实请求确认。它没有把离线消费者当成 Pro，也没有为结清观察项增加 Send、实验或 A/B 启动条件。§5.2 还明确初次触发用例不预先告诉被测角色答案文件，旧会话用例则测试实际启用交接；Portfolio、critic、Codex DM、Claude hub 与工程条件触发的覆盖也已补齐。

没有新增的计划层面非阻断修改要求。需要保留的执行事实边界已经在 v2 中写明：模型/effort、Claude hub 的 DM 职责及两方向容量、既有科学权限、资源约束、固定请求字节和不确定 Send 均不因接入改变；当前计划审查不派发任何启用命令。

本轮复用上一轮 181 路径的全文预读与边界，没有重新启动全量通读。完整读取了 v2、实际 [REVIEW_DISPOSITION.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/REVIEW_DISPOSITION.md)（24 行，SHA-256 `9833EF792361DB3312402CEAE52391123A8C168D238DF51F5D192E7A7F772F3B`），并检查计划差异和版本归档。v1 归档仍为 `609E5118C511108C9498ADECB607975D7843653DE068C779B1CE29008268002C`；新出现的 [INDEPENDENT_REVIEW.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/working/INDEPENDENT_REVIEW.md) 已核对包含我回传的 v1 完整原文，没有把“需修改”改写成通过。

已读控制表面摘要相对上轮未变，变化为计划/评审归档及 PORTFOLIO 的 P32/P33 状态入口；状态差异已完整补读，不将其当作本任务执行指令。最终复核 HEAD 为 `86ebee3f8b66fbeb4509294703387a7fbbc32eb3`。此前明确排除的全部历史科学卡、Pro 正文、运行输出、外部论文全文和重复 checkout 没有扩大为本轮阅读要求。

本轮没有修改文件、提交、执行单元测试或行为验证、运行实验、发 Pro、操作 Transport、联系实际科学 Root/Portfolio 或委派。真实 Pro 可达性仍未观察；上述尚未执行的验收没有被记成通过。本次计划复核已完成，可由原任务原样归档并在处置表记录 R1–R4 计划层面闭合。

