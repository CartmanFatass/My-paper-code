# 后续研究规划双提示词：文件与使用说明

两份中文prompt已写好，可分别交给两个互不共享上下文的第三方会话。增强版加入研究/代码规范和RL/MARL基础知识；对照版只提供共同事实。两版的研究目标、十方向事实、当前已承诺工作、历史成本窗口、问题和输出要求相同。

- [增强版：PROMPT_WITH_SPECS_AND_FOUNDATIONS.md](C:/Projects/HMASD/docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/PROMPT_WITH_SPECS_AND_FOUNDATIONS.md)
- [对照版：PROMPT_WITHOUT_SPECS_AND_FOUNDATIONS.md](C:/Projects/HMASD/docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/PROMPT_WITHOUT_SPECS_AND_FOUNDATIONS.md)

只发送所选prompt和其规定的材料，不把本README、另一个prompt、旧复审prompt或旧回答发给第三方。两份prompt自身均包含完整事实材料清单，增强版另外包含完整附加清单，无需说“同上”或向第三方补转另一版本。

## 固定版本和使用

共同源快照是main `4b997913e2a7ea91391058e40d4781fd9c0a78bc`。本目录是基于该快照新撰写的提示词，不能在这个历史SHA下寻找本目录的新文件。下方20项原始材料全部按这个SHA读取；不使用移动的main，也不混用后来结果。文档版本不替代各历史实验本身记录的执行版本。

增强版读取“共同事实材料”12项和“仅增强版”8项；对照版读取前12项。每项仅提供表内指定章节。直接访问仓库时，用prompt中的固定SHA路径；手工打包时，应从固定SHA导出对应章节，保留原路径和章节名称，不上传整个仓库、整套复审归档或无关章节。磁盘上的绝对路径供定位，文件以后可能更新，因此不能用后来的磁盘内容替换冻结版本。

尽量保持两次咨询的第三方模型/版本、推理设置、检索条件、输出额度和提问时机一致，使用新会话且不互相展示答案。两组都不进行外部检索；若需要补齐不可访问的事实文件，应以相同固定版本、相同范围同时补给两组。若增强组缺少某份规范或知识材料，记录实际缺失，不能把未读全的结果称为完整增强条件。推荐比较问题选择、反证保留、设计的区分能力、投入依据和不确定性，而非以是否同意Root/Pro或引用规范数量来判优。

这是“显式提供规范+知识”这一组合干预；不能凭这两次咨询分别识别规范与知识各自的效果，也不能从单次回答推断模型能力的稳定差异。

## 共同事实材料：两版都读

下方本地路径均真实存在；允许章节同两份prompt。共同输入刻意不用DIRECTION、PORTFOLIO全文、复审EVIDENCE_INDEX或完整Convergence回应，防止其中的现行方法要求或后续排序成为隐含答案。

| 用途 | 真实本地绝对路径 | 允许范围 |
| --- | --- | --- |
| UCOPE 历史 | [docs/research/candidates/ucope/UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_EVIDENCE_20260909.md](C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_EVIDENCE_20260909.md) | E0.1–E0.4；不读 E0.5 |
| FOLR 历史 | [docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_RESULT_EVIDENCE_20260909.md](C:/Projects/HMASD/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_RESULT_EVIDENCE_20260909.md) | Delivered primary and resource facts |
| RCLE | [docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_RESULT_EVIDENCE_20260909.md](C:/Projects/HMASD/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_RESULT_EVIDENCE_20260909.md) | Retained measurements and acceptance；Execution and complete costs |
| SCDMP | [docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.md](C:/Projects/HMASD/docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.md) | Observed primary and H；Counts, support and exposure；Execution and complete cost |
| FSD | [docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md](C:/Projects/HMASD/docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md) | §§1–5（结果、分量、两个训练实例、暴露和成本） |
| VSP-C1 | [docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B13_INTAKE_20260909.md](C:/Projects/HMASD/docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B13_INTAKE_20260909.md) | §4 Primary reading, native levels and uncertainty；§6 Prediction verification and measured cost |
| VSP03 | [docs/research/candidates/vsp_03/VSP03_B05_P76_INTAKE_20260909.md](C:/Projects/HMASD/docs/research/candidates/vsp_03/VSP03_B05_P76_INTAKE_20260909.md) | §§2–5（观测、native后果、三个训练实例、成本）；不读§§6–7 |
| ACVC | [docs/research/candidates/acvc/ACVC_NATIVE_LINK_LOSS_B02_INTAKE_20260909.md](C:/Projects/HMASD/docs/research/candidates/acvc/ACVC_NATIVE_LINK_LOSS_B02_INTAKE_20260909.md) | §§2–3，但§3只读至“The comparison does not…”所在段落末；不读以“For the unexpected T−G reversal”开头的知识引用段；另读§5成本 |
| MGTAP | [docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_INTAKE_20260909.md](C:/Projects/HMASD/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_INTAKE_20260909.md) | §§2–4、§6（问题、暴露、结果、成本）；不读后续决定 |
| CRTO | [docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_INTAKE_20260908.md](C:/Projects/HMASD/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_INTAKE_20260908.md) | §§2–4（原对象规则、结果、正负分量和完整成本）；不读§5后续决定 |
| UCOPE 当前已分配对象 | [docs/research/candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_SCIENCE_CARD_20260909.md](C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_SCIENCE_CARD_20260909.md) | §§2–6（方法、数值、单位、训练/评价、成本和终点）；不读§1权威/选择、§7工程要求 |
| FOLR 当前已分配对象 | [docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md](C:/Projects/HMASD/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md) | §§2–4（保留的方法、独立训练、终点、工作量和原有cap）；不读其余授权/工程段 |

当前UCOPE /8501、FOLR B02的“已接受/运行中”状态是Root在共同截止时提供的操作覆盖说明；仓库卡和部分跟踪文字仍可能写“尚未启动/handle pending”。这项覆盖只更正执行状态，不推断任何结果：UCOPE尚无科学输出可供本咨询使用，FOLR尚无完整配对输出。两份prompt明确保留它们的已承诺分配、原source和cap。

## 仅增强版：规范与知识

| 用途 | 真实本地绝对路径 | 允许范围 |
| --- | --- | --- |
| 研究规范 | [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](C:/Projects/HMASD/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) | §§2–7、§9、§11.1–11.10（含11.8各小节）；不读角色分工§8及外部来源§10 |
| 代码规范 | [docs/project/ENGINEERING_SCOPE_SPEC.md](C:/Projects/HMASD/docs/project/ENGINEERING_SCOPE_SPEC.md) | §§2–6；§5只读通用预算正文及Owner-ratified small reuse / net-deletion exception，不读CBSC/DISH/VNFC对象附款 |
| 运行与成本规范 | [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md](C:/Projects/HMASD/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md) | General requirements §§1–7；不读§8角色分工及VNFC唯一对象附款 |
| 基础总览 | [docs/rl-marl-foundations-20260907/FOUNDATIONS.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/FOUNDATIONS.md) | §§1–6；不读§7、SESSION_CHOICES或任何链接扩展 |
| RL | [docs/rl-marl-foundations-20260907/topic-notes/01_RL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/01_RL.md) | 任务和策略；数据与更新；策略梯度、baseline 和 critic；reward 变换的边界 |
| MARL | [docs/rl-marl-foundations-20260907/topic-notes/02_MARL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/02_MARL.md) | 模型分类首先说明目标和信息；CTDE 和参数共享各自改变什么；信用分配与非平稳性；MAPPO 为什么是一个具体而有用的起点（仅作算法例子） |
| 层次与异步 | [docs/rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/03_HIERARCHY_ASYNC.md) | 前五个概念章节：Option、持续回报、时间抽象、异步决策边界、时间尺度；不读“与本地研究资料的连接” |
| 实证 | [docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md](C:/Projects/HMASD/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md) | 全部五个概念章节；不追来源链接 |

研究规范和工程规范是增强版的规划约束；知识材料是概念和论证辅助。规范中的发送、角色、工具或递归阅读要求不能改变本次仅咨询的范围。SESSION_CHOICES和完整基础包README没有列为输入；MAPPO专题中的算法例子不强制采用MAPPO。

## 作者实际核对来源与限制

起始HEAD与固定截止均为 `4b997913e2a7ea91391058e40d4781fd9c0a78bc`，新文件作者为本次Astra/high subagent。子代理交付时未提交；Root已阅读全文，并独立核对移除输入条件段后两版共同正文逐字符一致、20项材料存在于固定SHA，然后按三个明确文件路径提交推送。此次提示词任务未发送第三方、未建Pro handoff/registry、未运行科学或性能实验。

实际阅读/检索的主要来源：

- 用户提供的根AGENTS说明，以及 [docs/AGENTS.md](C:/Projects/HMASD/docs/AGENTS.md)；目标目录中没有更近的AGENTS。
- [hmasd-scientific-tools/SKILL.md](C:/Projects/HMASD/.agents/skills/hmasd-scientific-tools/SKILL.md) 及 [scientific-reading.md](C:/Projects/HMASD/.agents/skills/hmasd-scientific-tools/references/scientific-reading.md)，用于作者的定向阅读，不交给第三方。
- [PORTFOLIO.md](C:/Projects/HMASD/docs/research/portfolio/PORTFOLIO.md)：当前Lifecycle表、Research organization、相关已测成本窗口；只用其事实和既有边界，不复制后续排序提案。
- [20260909_foundations_special_review/EVIDENCE_INDEX.md](C:/Projects/HMASD/docs/research/portfolio/pro_packets/20260909_foundations_special_review/EVIDENCE_INDEX.md)：Bounded result and next-state matrix、Historical exposure and cost windows、原卡/结果/intake的章节定位。该索引在作者准备时用作事实导航，不作为第三方输入。
- [20260909_foundations_special_review/TASK.md](C:/Projects/HMASD/docs/research/portfolio/pro_packets/20260909_foundations_special_review/TASK.md)：查看原输入版本/路径和十方向范围，没有把其问题、方法段落或要求沿用为对照版输入；没有阅读或提供专项复审RESPONSE。
- 上述共同文件的目录/标题、结果数值匹配及相关结果段落；另核对了RCLE [final intake](C:/Projects/HMASD/docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_RESULT_INTAKE_20260909.md) §§2–3、SCDMP结果全文、ACVC intake §§2–3、CRTO intake §§2–3，以及UCOPE当前card的方法段。
- 当前分配事实来自 [UCOPE /8501 intake](C:/Projects/HMASD/docs/research/candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_8501_INTAKE_20260909.md) §§1–3和 [FOLR B02 intake](C:/Projects/HMASD/docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_INTAKE_20260909.md) §§1–2，实际运行状态另由Root补充；未将这些分配理由/预测作为第三方标准答案。
- 规范的相关标题及条款，重点为证据规范§11.1–11.10、工程scope通用要求及runtime General requirements；FOUNDATIONS §§1–6与四专题的章节定位。作者未声称读完全部历史卡、全部基础引用或审计历史执行源码。

两组都保留“原卡如何定义已执行/已接受对象”和必要的历史边界。这些卡、结果和intake本来就受项目规范和既有研究者知识影响，事实段也可能包含概念解释、历史分支或局部判断，不能做到完全没有规范影响。对照所移除的是显式的规范/基础知识材料及其采用要求，并不是改写历史或清空第三方已有知识。事实摘要由同一作者制作并完全共用，也会共享摘要选择的影响；这属于本次比较的限制。

轻量验收只核对文件存在于固定SHA、允许章节定位、两版共同正文一致及差异限于附加输入条件，不把此次准备声称为独立科学复审或运行复现。
