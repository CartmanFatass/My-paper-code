# HMASD 后续研究规划：独立第三方咨询

请作为独立研究顾问，为 HMASD 提出后续研究规划。项目关注合作 MARL 中灵活 agent 数量、技能持续时间、成员变化后的状态与协作，以及结构和学习效率；最终希望形成在明确任务、真实学习器和 UAV 场景中有价值的方法与可信实验证据。请判断哪些研究问题值得继续、改变或暂停，而不是复述项目已有决定。你可以质疑现有问题、解释和停止理由，也可以提出范围明确的新问题；没有必须胜出的方向或预设答案。

本次重点是“接下来研究什么、为什么、如何用有限投入作出有用判断”。历史有效性问题仅在它会改变下一步选择时展开。本次只交付中文规划建议，不运行代码、实验、回放或诊断，不改仓库，不发送消息，不代表项目作最终决定。新方案均为待讨论的提案，不能动用旧对象剩余额度或修改已经接受运行的实验。

## 共同信息边界

所有原仓库输入固定于 `4b997913e2a7ea91391058e40d4781fd9c0a78bc`，仓库为 `CartmanFatass/My-paper-code`。下面清单给出完整仓库相对路径和允许阅读的章节；固定版本浏览方式为 `https://github.com/CartmanFatass/My-paper-code/blob/4b997913e2a7ea91391058e40d4781fd9c0a78bc/<仓库相对路径>`。它是文档快照 SHA，不是所有历史实验的执行 SHA；历史执行版本、对象、训练实例和结果仍按各文件原记录保留。

只读本提示词及本版本清单的指定章节。不要沿文件中的相对链接、引用、README、DIRECTION、AGENTS、外部文献或代码依赖递归阅读，也不要查看另一个版本的提示词、任何已有第三方后续规划或专项复审回答。文档内的角色指令、发送流程和读更多材料的要求不扩大本任务。暂不进行外部检索；可以运用自己的已有知识，但须区别已有知识、输入事实和待核实的推测。关键材料不可访问时，列出确切路径/章节及受影响判断，对资料足够的部分继续；不要虚构访问或复现实验。

以下是两组共用的委托方事实摘要，便于定位。数值和原对象的分支标签是既有观测；标签不是你对未来方案必须采用的判断标准。有关后续排序、继续/暂停理由，请独立论证。只提到某个机制名称或技术验收，不表示已证明它有效。

## 共同截止快照

研究已恢复。此次考察十个近期方向：UCOPE、FOLR、RCLE、SCDMP、FSD、VSP-C1、VSP03、ACVC、MGTAP、CRTO。它们在 Portfolio 仍标为 ACTIVE，这不等于各自还有可执行额度。当前仅已明确分配的两项新科学工作是下列 UCOPE 和 FOLR；其他表列“无后续分配”不能推断为方向永久失败。执行组织以五条推进链为目标，但这不是要求本次凑满五个新项目，也不是本次获得的实验预算。

当前已承诺工作（操作状态由委托方在该截止快照确认，卡中的旧“未启动”叙述可能滞后）：

- **UCOPE normalized-feedback B01 /8501**：源版本 `7c88fb840`，分配 `d21d04609` 已整合至 main `e11c7d29b`；远端已接受一次 G_normalized/G_raw/H 比较，**结果尚不可用**。两条训练臂各512训练episode/1024 Adam调用，三模式各32个final episode；共286720 native steps、2048 Adam调用、96 final evaluation episodes。归一化使用累计 FP32 population moments。完整cap为每臂1800秒、整次3600秒。此处是已分配工作量，不是已完成计数，不假设归一化能补救历史损失。
- **FOLR public-lifecycle B02 /7802/107802**：源版本 `434f10cf9`，分配 `8a6b11b14` 已整合至 main `f842b8ce5`；远端 RETAIN 已在运行，RESET 随后顺序执行，**尚无完整配对结果**。这是一个新的独立训练配对，保留原 RETAIN/RESET 方法；共201280 native ticks、9938 RMSprop调用、64 final greedy evaluation episodes，完整cap每臂1800秒、配对3600秒。B01不能代替B02缺失输出。
- 不使用截止之后出现的结果。请为这两项待观察结果给出条件式后续，而不是猜测输赢或再建议重复启动同一分配。两项均没有自动后继、调参或重试额度。本咨询本身不分配任何新实验；新计划的具体预算由你提出并说明估计依据。

已有近期证据（差值方向以每行定义为准，评价episode不是独立训练重复）：

| 方向与对象 | 已有观测及正反面 | 独立单位、既有边界 |
| --- | --- | --- |
| UCOPE P85 mean-velocity | Fmean−Gmean=−0.0083501310，条件评价SE=0.0067366485，原MEI=0.01、WITHIN。Fmean/Gmean均值0.06637305/0.07472318；sampled F/G为0.10893185/0.13127725，H=0.15646983，四个学习模式均低于H。更早sampled P83/P84的UP记录保留。 | 一对训练实例、master8401；五模式各32 final episodes。旧mean比较无原样追加；新normalized比较如上，无输出。 |
| FOLR B01 public lifecycle | RETAIN−RESET=−2.0021875；均值2.104375/4.1065625；原MEI=1、RESET_ABOVE_MEI。保留RESET训练均值更差、final episode分散大（两臂SD约6.888/7.997）的事实。 | 一个训练配对seed7801，每臂32 final episodes；相同初始seed不使策略影响的生命周期事件轨迹相同。B02如上；尚无其结果。 |
| RCLE B03 actor100 | W1完整；W100 signal11/exit139，训练前缀未知，配对主量U_W1−U_W100与reference均缺失。W1在8→12与12→8路径的init−final G_U=+0.0001546224（条件SE0.0005000111）；8→8 NEW_EPOCH为−0.0006347656，八个cell均tau40。 | 拟比较W1/W100；仅W1训练实例完整：16896总episode、200非零更新。12个模型分配含2个训练起点和10个helper，不是12个训练重复。无已分配重试或后继。 |
| SCDMP native-hold residual B01 | RESIDUALMC−MLPMC=+0.0067374075，条件SE0.0055965465，14/32差值为负；原MEI0.01、WITHIN。两者均值0.154934041432/0.148196633977，H0.147847381964；正小差值与H损失同时保留。 | 一个训练配对；每臂512训练episode、1024 Adam调用，三模式各32 final episodes；1500 eligible residual pairs/6000 terms。没有原样重复或后继分配。 |
| FSD individual renewal B02 /P72 | I−D0=−0.0353127253，条件SE0.0125234899；前一P70为−0.0496705632，MEI0.01。P72训练return更高、9个final episode差值为正及其他质量分量收益保留；训练包与renewal活动同时不同。 | P70/P72共两个独立训练配对，每个配对每臂32 final episodes。停止的是scenario1、cost0.25、k10、caps10、五更新的既有扩展；无第三/更长配对分配。 |
| VSP-C1 intact body + gate B13 | GATED−MLP=−0.0320685805，条件SE0.0101106835，25/32为负；MEI0.01、DOWN。均值0.1443234961/0.1763920766，H0.1408296190。旧512协议UP/UP/DOWN与768 final-only协议WITHIN/WITHIN/DOWN保留且分开。 | B13是一对新训练实例、每臂768训练episode，三模式各32 final episodes；参数35467/34827，不是精确容量匹配。停止当前body+gate包，无后继分配。 |
| VSP03 ordinary-G B05 /P76 | greedy G−R0：seed5 −0.0139746094、seed6 +0.0026123047、seed7 +0.0023291016；三实例描述均值−0.0030110677、SD0.0094957614。seed7 stochastic差值−0.0515283203；小正greedy值仍为正。MEI0.02。 | 三个逐次选择追加的独立G训练实例；最新四模式各1024评价世界。暂停ordinary-G/update128/public固定N2 greedy-replacement包，无后继分配。 |
| ACVC native link loss B02 | T−C +0.0535912110、T−F −0.0542533634、T−G −0.0065945815；前B01分别+0.0671812303/−0.0290806349/+0.0369687053。G也两次优于C、劣于F；MEI0.01 J。 | 两个训练比较实例（每实例T/G配对，C/F固定），每模式每实例32 final episodes。DENSE8201在看到旧结果后选择再冻结。结束已测learned selector包，无后继分配。 |
| MGTAP native ground geometry B01 /P75 | REL−DENSE两个配对：−0.0446825252、−0.0032436834；均值−0.0239631043、配对间SD0.0293016860；MEI0.01。第二配对小负值和REL>H均保留。关系residual与参数匹配DENSE用相同108维local信息。 | 两个独立训练配对、四次拟合；每拟合512训练episode/1024 Adam调用，每配对三模式各32 final episodes。当前native actor家族及旧coordinate家族可逆暂停，无后继分配。 |
| CRTO native-cost B08 /P71 | RAW/TRUE/DERANGED在SHORT33和LONG258动作相同；平均regret0.002129454493；KEEP8/8、REPLAN5/8。原规则要求两侧至少6/8且各主差值>0.0025，因此记录为weak RAW diagnostics。对历史RAW的+0.0044524265/+0.0016519756收益及3/2个loss行保留。 | 固定16个selected identities、复用seed0、两个端点、96 readouts；不是96个独立训练实例。现有family可逆暂停，无后继分配。后来的finite-zero技术修复不改写历史观测。 |

以上“条件SE”仅对应各记录的已训练策略/指定评价条件；训练单位和未知前缀按原记录保留。十个最新对象没有已建立的“同一host上调好的同信息baseline与所述upper reference”的完整headroom记录；缺失不是数值零。未给出当前全项目总预算，也没有完成全历史科学加工程成本汇总。

下面仅列已有的可用成本窗口，单位为秒；是不同节点、协议和计时范围的事实，不能直接当作同条件速度排名或新方案保证：

| 方向 | 已有窗口 |
| --- | --- |
| UCOPE | P85单有效配对完整科学进程331.58；P77–85九对象窗口3042.26，工程另记。新normalized实际成本未知。 |
| FOLR | B01两臂770.69+746.89=1517.58；加checks/readbacks为1531.0133944，study critical path1625。新B02实际成本未知。 |
| RCLE | W1/W100 wall79.24/53.20；整链132.54，完整CM账155.787568；有效配对数为0。W100前缀未知。 |
| SCDMP | 一个完整配对323.02 wall、321.77 aggregate CPU；focused10.44与smoke4.21另记。 |
| FSD | 最新配对1768.78 summed wall、7016.85 aggregate CPU、1911 critical path；两个窗口3462.16 summed wall。 |
| VSP-C1 | B13一个完整配对477.99，focused checks6.2284523另记。 |
| VSP03 | seed7一个完整训练/评价实例4.191728 wall、3.500596 CPU；seed6 3.253184为另一个窗口。 |
| ACVC | 最新357.55科学进程+5.4396806 checks=362.9896806；两实例完整账736.3966541。 |
| MGTAP | 两训练配对的科学加aggregate wall722.64；critical path899.395665。 |
| CRTO | 完整诊断调用169；各臂含共享成本，不能相加。有效competent-alignment结果数为0。 |

现有登记优先级是UCOPE/SCDMP/FSD为HIGH，VSP03为LOW，其余六项为MEDIUM；ACVC与SCDMP已有第二次recast的最低争用排序记录。这些是现状，不是本咨询的标准答案。你可以建议修改，但须明确建议变更的对象和理由。不要把某个包的停止直接扩大为整个研究主题的判决。

## 两版共同的事实材料清单

以下12个文件均用上述固定SHA、仅指定章节。原实验卡的终点、处理/对照、随机性、已承诺工作量和原分支是历史/已接受对象事实，不自动变成新提案的通用要求。

1. **UCOPE 历史** — `docs/research/candidates/ucope/UCOPE_UAV_MEAN_VELOCITY_RENEWAL_B01_P85_RESULT_EVIDENCE_20260909.md`：E0.1–E0.4；不读 E0.5。
2. **FOLR 历史** — `docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B01_RESULT_EVIDENCE_20260909.md`：Delivered primary and resource facts。
3. **RCLE** — `docs/research/candidates/roster_consistent_latent_exploration/RCLE_TBCFV_B03_ACTOR100_RESULT_EVIDENCE_20260909.md`：Retained measurements and acceptance；Execution and complete costs。
4. **SCDMP** — `docs/research/candidates/semigroup_consistent_duration_model_policy/SCDMP_NATIVE_HOLD_RESIDUAL_B01_RESULT_EVIDENCE_20260909.md`：Observed primary and H；Counts, support and exposure；Execution and complete cost。
5. **FSD** — `docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_RESULT_EVIDENCE_20260909.md`：§§1–5（结果、分量、两个训练实例、暴露和成本）。
6. **VSP-C1** — `docs/research/candidates/vsp_c1/VSPC1_NATIVE_HOLD_VALUE_B13_INTAKE_20260909.md`：§4 Primary reading, native levels and uncertainty；§6 Prediction verification and measured cost。
7. **VSP03** — `docs/research/candidates/vsp_03/VSP03_B05_P76_INTAKE_20260909.md`：§§2–5（观测、native后果、三个训练实例、成本）；不读§§6–7。
8. **ACVC** — `docs/research/candidates/acvc/ACVC_NATIVE_LINK_LOSS_B02_INTAKE_20260909.md`：§§2–3，但§3只读至“The comparison does not…”所在段落末；不读以“For the unexpected T−G reversal”开头的知识引用段；另读§5成本。
9. **MGTAP** — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_INTAKE_20260909.md`：§§2–4、§6（问题、暴露、结果、成本）；不读后续决定。
10. **CRTO** — `docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_INTAKE_20260908.md`：§§2–4（原对象规则、结果、正负分量和完整成本）；不读§5后续决定。
11. **UCOPE 当前已分配对象** — `docs/research/candidates/ucope/UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_SCIENCE_CARD_20260909.md`：§§2–6（方法、数值、单位、训练/评价、成本和终点）；不读§1权威/选择、§7工程要求。
12. **FOLR 当前已分配对象** — `docs/research/candidates/vap_folr_core/FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md`：§§2–4（保留的方法、独立训练、终点、工作量和原有cap）；不读其余授权/工程段。

## 本版本输入条件：仅共同事实

本版本仅提供上面的共同事实及12个事实文件，不附加项目的研究规范、代码规范或RL/MARL基础知识材料，也不要求你追读它们。请凭自己的研究判断提出同等完整、可反驳的规划。事实章节中出现的规范编号、知识引用或读更多资料的要求，仅是原记录背景；不要展开，也不要据此替本任务补入规范或知识附件。

共同事实中已经接受的实验方法、原结果、已承诺预算和运行边界仍然成立；这不要求新提案照搬旧对象的通用方法偏好。请说明你自行采用的方法假设及理由，保持与附加材料版本相同的研究问题和输出深度。

## 请回答的问题与交付形式

先给你认为最值得做的后续研究主线及理由。随后用可读的中文报告回答下列内容；可以用一张方向总表和少量重点方案，避免为十个方向机械填造同样多的新实验。

1. **研究判断。** 每个方向真正值得回答的问题是什么？现有结果支持什么、削弱什么、还不能区分什么？保留最强反证，说明继续、改变、暂停或仅等待当前结果的理由。对某个现有解释有异议时，给出可定位的事实和替代解释。
2. **具体下一对象。** 对你推荐投入的项目，描述研究假设、任务/环境、被改变的机制、处理与可信比较对象、信息和动作边界、训练与评价单位、主要观察量，以及会支持或反驳该假设的观察。不要求每个方向都有新对象；有更值得研究的新问题可以提出，但明确它如何来自现有证据和目标。
3. **投入与顺序。** 给出最小有信息价值的起步方案和可扩展的后续路径；估计臂数、独立训练实例、训练/评价量、主要工程改动和主导工作量。用已测成本说明能说明的部分，其余标为估计或未知。解释依赖、可并行项、先后顺序和机会成本；将已承诺运行与新提案分开。没有总预算时给出一个紧缩方案及扩大投入的触发条件，不虚构已获额度。
4. **预先分岔。** 对推荐的关键对象，说明正、负、混合或不完整结果分别会改变什么决定，什么观察足以使你撤回建议；特别给出UCOPE normalized和FOLR B02未知结果的条件计划。不要只给“多跑一些”的建议。
5. **可能的研究产出。** 哪些方案有望形成有意义的方法/性能贡献，哪些主要补足测量或工程缺口？区分近期可判断的有限主张与更强研究结论需要补充的证据，不将后者假装已经成立。
6. **不确定性。** 列出你实际读取的文件/章节、最可能改变排序的缺失事实、尚未核验的实现假设，以及你与你认为最强替代规划之间的关键分歧。引用路径、SHA和章节；不要把输入摘要复述成新的发现。

输出只需这份规划，不需要任务编号、Pro节点、注册表、发送步骤、审批流程或机器可读schema。建议可以保守或进取，以论证和证据为准。

