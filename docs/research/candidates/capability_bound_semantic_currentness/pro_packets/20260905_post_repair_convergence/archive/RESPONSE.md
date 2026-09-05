**选择继续：开展一个独立的新直接回报 B，以新训练 seed 21203 做 STRUCT 对同信息 RAW 的一次配对比较。现在不优先补齐旧十五表发布，也不暂停这项最小比较；这属于既有机制下缩小主张的延续，不是机制 recast。**

理由是，源码确实提供了不经过旧历史重建和十五表发布器的真实 host → 循环 PPO → 逐 episode 原生回报路径。它能回答一个尚未得到可信主测量的较小问题，而不必承担旧三 seed、四臂、motif 和机制解释的全部证据义务。**但这只是对下一项有界投入的选择，不是新实现已通过运行验收，更不是共享 host 已正确的证明。** 新提案尚无已接受的 diff 或运行事实。

## 一、为什么选择新比较，而不是继续旧发布修复

### 旧修复已经结束，不能改写为性能结果

已结束的修复留下了 A174/D429 的源码变更、通过的原 smoke 和十九项 focused 检查，却没有完整正式发布。第一次正式调用发生 SIGSEGV、退出 139；唯一一次同源复现发生另一种 `TypeError`、退出 1，没有重现原段错误。两个根因均未确定。两次终止库存都记录了 428 个文件，但发布目录、`summary.json` 和表文件路径均为空。**缺的是主测量，不是已经观测到零收益。**

旧 assignment 明确要求保留三 seed、四臂、十五表、完整 RAW 能力输入和全部读回，而且不选择新 learner 或 successor。因而，新 B 不能被记录为旧修复继续、旧 B1 通过或 r05 隔离解除。新规范允许另选较小对象，但没有追溯改变这些历史事实。

### 减掉的是不再服务于主张的实验义务，而不只是优化其实现

旧 `b1_metrics_rehydrate.py` 会按固定旧 seed 重建完整训练和评估面板；旧 `b1_metrics_production.py::_assemble_and_publish_b1_metrics` 随后依赖十二个正式 replay 输出、训练组装、共享 truth/support、十五表物化和多轮读回。它不是一个给当前模型和 tape 就返回回报的简便接口。

因此，本次应先缩小科学问题：只比较两个实际训练策略在固定随机评估面板上的原生回报，不再要求通过这一比较解释语义特异性、motif 响应或 PI/DERANGED 排除。相应地，旧全历史 reconstruction、全 support census、逐位策略记录和完整十五表不再是新主张的默认依赖。**这不是宣布它们对原 B1 无用，而是不让原 B1 的解释范围决定新 B 的全部成本。** 当前已应用的 §11.8 正是按主张和实际风险限定这些义务。

### 最强反证有科学和工程两部分

**科学反证**是 RAW 的信息包含关系，而不是当前缺少更多诊断。历史 exact factorial 中，RAW 与结构化最优逐行相等；LR01 保留为有效的 `UNRESOLVED`，没有建立稳健的结构化优势，也不能反向改写为所有情况下 RAW 都优越。新 B 的合理问题只能是：在这个表示、优化器和有限训练预算下，结构化 currentness 是否使学习出的行为更好。它不能检验“RAW 缺少必要信息”。

**工程反证**是两次失败触及新路径仍需使用的公共依赖。原段错误栈经过 `addressing.canonical_json/audit_digest → host._finish`；后一次错误发生在 `EpisodeTape` 的 canonical token 重打包，最终到 `token.py:251` 的 `int(value)`。直接路径仍要经过这些组件，所以不能说“绕过发布器便绕过了故障”。另一方面，现有日志也没有证明新直接路径必然失败，或证明错误唯一属于 host、解释器、资源或修复补丁。合理处理是对新主路径做一次针对性验证，而不是先重开历史根因穷尽调查。

## 二、新 B 的最小完整科学目标

采用提案中的两个学习臂、一个新 seed 和固定终点。其主要量定义为：

$$
d_e=R_{\mathrm{STRUCT},48,e}-R_{\mathrm{RAW},48,e},
\qquad
\widehat{\Delta}_{48}=\frac{1}{32}\sum_{e=0}^{31}d_e .
$$

这里两臂使用同一组 `EVAL_STOCHASTIC` episode 身份和公共历史；四个 checkpoint 重用这组固定评估根。**“随机评估 episode”指随机生成的环境，不是把现有 greedy 评估改成随机动作评估。** 0、12、24 的读数保留为学习曲线，不参与最好 checkpoint 选择。

| 必须保留                                                                                                       | 新 B 不再默认承担                                  |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 既有两 receiver、单 controller、24 opportunities、152 transitions 的动态 host；原事件、动作和 settlement 规则                  | 换成廉价合成标签或其他 host；也不新增多学习 agent、伙伴共适应任务      |
| 两臂完整相同的公共 primitive history；STRUCT 和 RAW 各自既有 adapter；不向 policy 输入 evaluator truth、validity、oracle 或奖励派生特征 | 用删减观察的 RAW 作为弱对照；全隐藏状态或全 support 发布         |
| 同一 FP32 循环网络、初始化、PPO 参数、训练动作随机地址、完整 episode BPTT、更新量和评估曝光                                                  | PI、DERANGED 两个学习臂及其对应机制归因                   |
| seed 21203，从新模型和新 Adam 状态开始；每臂 48 次 rollout、768 次实际 Adam 更新                                                | 旧 checkpoint 继续训练、旧数据冒充独立训练、旧三个 seed 的全历史重建 |
| 四个 checkpoint 各 32 个 stochastic episode；终点逐 episode 配对 native return                                       | 32 个 motif episode、twin 效应、AUC 选型、旧七类机制解释   |
| 每个评估 episode 的身份、24 个动作和回报；实际训练工作、配置、状态与主要输出读回                                                             | 旧十五表格式、旧 replay worker、逐位中间张量和通用极严容差        |

这些保留项与删减项分别对应提案的直接回报目标和旧 metrics-only 规范的较宽解释目标。

奖励尤其不能在简化时被改写。既有 active 请求下，合法 `SERVE` 为 \(1\)，无效 `SERVE` 为 \(-0.30\)，`REFRESH` 是决策时 \(-0.40\) 加延迟 settlement 的 \(1\)，`SAFE_FALLBACK` 为 \(0.20\)；inactive 请求下分别为 \(-0.10,-0.40,0\)。新 B 继续使用这些原生后果，而不是仅计成功次数、只取 decision reward，或把 refresh 的延迟收入漏掉。

**包含空假设**是：RAW 已有完整公共历史，能够从信息上重建 STRUCT 提供的关系量，有限预算下的实际 RAW 学习可能匹配或超过 STRUCT。信息包含不等于已证明该 RAW 网络在 768 步内学会了规则；这正是需要实际比较的部分。RAW 的四字节 adapter 是既有 generic FIFO，不应改成空输入或零 adapter。

保留同 tape 的 `ALWAYS_REFRESH`、`ALWAYS_SAFE` 回报及 RAW 动作分布作为低成本能力背景，但**不恢复旧“80% easy-OPEN + 全 support + 全表”的判定门槛**。RAW 若实际训练但表现很弱，应保留测得的差异并注明对照受限；不能据此声称击败了充分合格的强对照，也不应把所有直接回报事实一并抹掉。

## 三、源码支持的调用路径，以及不能假定存在的接口

下列源码均位于 `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/`。实际可复用的是函数级路径，不是旧 B0/B1 整体 runner：

| 环节   | 实际接口及新调用方必须处理的事项                                                                                                                                   |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| 构造环境 | `DynamicHost.build_stochastic(split, episode_id)` **直接返回 `EpisodeTape`**，不是字典，也不是 `(tape, metadata)`。训练按更新 \(u\) 使用 episode ID `8*u .. 8*u+7`。     |
| 构造观察 | `build_observations` 返回 `(Tensor, AdapterWorkReceipt)`；`_project_panel` 返回堆叠观察及工作记录。前 136 通道来自公共 token，后 32 通道来自对应 adapter。                        |
| 训练采样 | `_rollout_from_panel` 返回 `(EpisodeRollout, evidence_dict, uniform_digest)`；其 reward tensor 同时填入 decision 与 settlement 行。                           |
| 实际优化 | `RecurrentPPOTrainer.train_rollout` 返回 `tuple[PPOLossRecord, ...]`，每次执行 16 个 Adam 步并更新工作计数；它检查连续的训练 episode ID，不能反复训练同一个 `0..7` 面板冒充 48 个 rollout。 |
| 评估动作 | `_evaluate_heldout` 返回“动作记录列表、状态检查记录”，**不返回回报**。动作记录中的 `decision_actions` 是名称字符串。                                                                  |
| 计分   | 先用 `Action[name]` 转换名称，再把同一 `EpisodeTape` 和 24 个动作交给 `evaluate_episode`。后者返回字典；`record["return"]` 包含分子、分母和浮点展示值，不是直接返回一个标量。                        |

这些返回类型和计分路径可在 `host.py::build_stochastic`、`engine.py` 的上述 helpers、`ppo.py::train_rollout` 与 `evaluator.py::evaluate_episode` 中直接核对。把评估 helper 的字符串动作未经转换传入 evaluator，不是已经可工作的集成。

还有两项明确兼容性边界。

第一，`build_b0_panel` 固定要求 B0 namespace 和 seed 21001，不能拿它构造新 B 的面板。第二，`addressing.py` 的合法 namespace 只有 B0/B1/B2，因此应按提案使用 **`B1_RUN` 作为随机地址空间，seed 为 21203**，而把新科学对象和输出目录标在外层。`checkpoint.py` 同样保留旧 substrate 的 `object_id` 和严格 payload 字段；不能向现有 checkpoint payload 随意加新字段，或改内部对象身份后仍声称兼容。新对象、旧随机 namespace 与 checkpoint 的对应关系写入外层结果元数据即可，不必改变 RNG 字节或 checkpoint 格式。

新调用方仍会支付现有 helper 的必要工作，例如 `_finish` 的打包和地址摘要、`_project_panel` 的重复投影检查，以及 PPO 的实际梯度和参数记录。因此，我确认的是**依赖范围可以缩小**，不是确认这些路径已经没有额外开销，更不是确认存在一个已实现的“跳过旧 metrics”开关。

### 交给 CM 的最小完整目标

完成一个薄的新调用模块、一个薄 runner 和一次针对性集成验证，直接形成上述配对测量；不建设新框架，不改 host、adapter、PPO 或奖励语义，不接入旧十五表生产事务。主要结果应在实际评估时生成、保存并读回，而不是训练结束后依靠旧历史重建去恢复它。提案已明确允许这种尚待实现的目标，尚未接受其源码。

**唯一新增的 focused 验证应贯通改变的主路径。** 两臂都覆盖真实 host 构造、公共输入投影、合法动作、一次符合既有八 episode 批大小的真实 PPO 更新、动作名称转换、chosen-action 原生 decision/settlement 求和，以及结果写入与读回。复用相关未改路径已有的检查；核对更新计数及参数确实发生变化，而不以合成 checkpoint 计数替代实际优化。验证使用与正式 21203 观察分开的工程 fixture，其实际 learner/评估曝光单列，不算独立科学训练样本，也不另外设立“曝光证明实验”。

这次检查不要求得到正收益、不要求覆盖所有 support signature、不要求复现旧 SIGSEGV，也不要求跨平台 bit 相等。**若共享 token/addressing/host 在这条路径上再出现问题，就返回该具体依赖和受影响主测量；不能用更多 seed 掩盖，也不能自动扩大成 host 或解释器重写。**

## 四、预算、成本未知和结束边界

正式比较的工作量为：

| 工作量                  |     每臂 |        两臂合计 |
| -------------------- | -----: | ----------: |
| 训练 episode 执行        |    384 |         768 |
| 训练 transitions       | 58,368 |     116,736 |
| 训练决策                 |  9,216 |      18,432 |
| Rollout 更新           |     48 |          96 |
| 实际 Adam 步            |    768 |       1,536 |
| 评估 episode 执行        |    128 |         256 |
| 评估 transitions       | 19,456 |      38,912 |
| 训练与评估 transitions 总计 | 77,824 | **155,648** |

这里 128 次评估执行来自四个 checkpoint 各 32 个 episode，**不是 128 个独立训练样本，也不是四套互不相关的评估世界**。两臂合在一起仍只有一个配对训练 seed。上述计数与零新曝光成本文件、提案和实际 PPO 批大小一致。

选择的正式投入上限为**每臂完整调用 600 秒，最多两次臂调用**。启动、host 构造、48 个 rollout/update、四次评估、checkpoint/结果写入、必要读回和结束宽限都在其中；配对汇总也不能通过移出计时另获额度。两次臂调用 wall 之和至多 1,200 秒，但这不是含准备和测试在内的 study 总耗时预测。

旧 **333.27086 秒**来自三段训练的最大合计约 296.92813 秒，加最大 replay 约 36.34273 秒；它不覆盖完整旧共享发布，更没有测量新直接路径。新路径的完整成本应写为

$$
T_{\rm arm}
=T_{\rm startup}
+\sum_{u=1}^{48}T_{\rm rollout/update,u}
+\sum_{c\in\{0,12,24,48\}}T_{\rm eval32,c}
+T_{\rm publication/readback/finish}.
$$

其完整系数目前未知。可以明确数出减少的臂、seed、motif 评估和历史重建义务，**不能把这些计数下降换算成已测 wall 节省、C++/GPU 加速或并行倍数**。既有 B0 的十六步参数位移只支持 optimizer 能移动参数，不预测 768 步的收益或线性收敛。

工程范围采用普通预算：新增非测试源码不超过 2,000 行、runner 不超过 600 行，30% 编排占比只作必要性审查信号。旧 A174/D429 不续期，旧测试账不清零。按当前记录，focused/offline 已用 **124.49/300 秒**，剩余 **175.51 秒**；新检查应按实际共享目录账安排，本文不增加测试配额。若必要覆盖在余额内无法完成，CM 应返回缺哪项覆盖和具体预算差额，而不是删掉必要检查、重新命名目录清账或申请泛化豁免。

未来实际调用仍遵守四项 B 条件和逐调用资源准入。配置的优先节点是 `wsl_4070`，解释器为 `/home/wu/.venvs/hmasd/bin/python`；本对象使用 CPU FP32、单科研进程和一条 Torch 计算线程，不因节点有 GPU 而改变执行设计。配置记录不能替代当次物理及有效可用内存均至少 4 GiB 的实际检查，也不能替代精确源码的正常集成与运行验收。

**本项投入结束于完整结果 intake，或具体主路径故障、完整调用超限、必要依赖/预算缺口。** 不自动重试，不追加训练，不恢复旧第四次正式发布。终点任一臂的主要回报缺失、配对身份不成立或回报计算失真，就不能形成该配对性能结论；只缺非主张必需的资源诊断，则保留有独立依据的主测量并限制资源措辞。

## 五、MEI、结果含义和有限后续

采用提案的 **每 episode 0.25 原生回报**作为本对象的 MEI。它约为 24 单位理论 episode 最大回报的 1.04%，理由是用一个小而非纯符号性的原生收益，判断是否值得购买独立训练重复。它**不是已测 headroom 的比例，不是显著性门槛，也不是从旧收益反推得到的通过阈值**；当前匹配的 tuned-generic headroom 仍缺失。

若终点差异超过 0.25，且实际训练、信息、配对和计分可信，可优先建议保持同一比较，再投入一到两个新的独立训练 seed。应同时报告全部 32 个配对差异、两个臂的绝对回报、固定基线背景和四点曲线；不能只展示均值或最好 episode。它支持的是一次有意义的局部信号，而不是稳定优越或语义特异性。

若差异很小、反向或 RAW 明显受限，保留其原意。尤其不能把负差异仅因落在 MEI 内就从报告中消失。一次具体、可判别的预算或对照限制可以成为另一个 B 的理由，但没有“未转正就继续增加预算”的默认后续。后续独立 seed 的所有结果和失败均保留，不要求每个 seed 都改善，也不因增加评估 episode 就把训练样本量记大。

本次最终选择只包含第一对训练；后续一到两个 seed 是有限建议，不是已经选择的额外调用。无论结果如何，新 B 都不证明 PI/DERANGED 已被排除、跨 seed 统计效应、变量 agent 数、伙伴共适应、MARL 协调或 UAV 迁移，也不恢复旧 B1 的解释权限。Portfolio 的生命周期和优先级不在本次改变范围。

## 实际读取范围与仍未验证的事实

本轮通过连接的 GitHub，在固定版本 **`7a8c985c75f418a63e18af92e13ada10d3ad37a5`** 读取了清单中全部 **33 条路径**的相关内容，没有列明路径的访问缺口。为明确读取边界，以下以：

* `D/` 表示 `docs/research/candidates/capability_bound_semantic_currentness/`；
* `S/` 表示 `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/`。

| 路径组             | 实际读取                                                                                                                                                                                                                                                                                                    |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 根与规范，共 5 条      | `AGENTS.md`，重点 §§1–8；`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`，包括 §§4、5.2、11.4、11.8；`docs/project/ENGINEERING_SCOPE_SPEC.md`，包括预算与 CBSC 附款；`docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md`，一般要求 §§1–7 及 §8 开头；`.codex/hmasd-compute.toml` 全文                                                |
| Portfolio，共 3 条 | `docs/research/portfolio/PORTFOLIO.md` 当前概览及 CBSC 行；`docs/research/portfolio/pro_packets/20260905_exploration_calibration/archive/RESPONSE.md` 全文，截断处续读；`docs/research/portfolio/decisions/2026-09-05-exploration-rigor-spec-application.md` 全文                                                         |
| 方向记录，共 6 条      | `D/DIRECTION.md`；`D/CBSC_OMRC_B01_APPROVED_REPAIR_INTAKE_20260905.md`；`D/CBSC_OMRC_B01_APPROVED_REPAIR_CM_RESULT_20260905.md`；`D/CBSC_OMRC_B01_R06_LAUNCH_READINESS_INTAKE_20260904.md`；`D/CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md`；`D/CBSC_OMRC_B01_APPROVED_REPAIR_ASSIGNMENT_20260905.md`，均全文 |
| 原始终止证据，共 4 条    | `D/approved_repair_20260905/profile02-task.log`、`repro03-task.log`、`profile02-inventory.json`、`repro03-inventory.json`，均全文                                                                                                                                                                              |
| 本轮提案，共 2 条      | `D/pro_packets/20260905_post_repair_convergence/EVIDENCE_AND_OPTIONS.md`、`EXPOSURE_AND_COST.json`，均全文                                                                                                                                                                                                   |
| 源码，共 13 条       | `S/addressing.py`、`host.py`、`tapes.py`、`adapters.py`、`contract.py`、`model.py`、`ppo.py`、`evaluator.py`、`checkpoint.py`、`b1_metrics_rehydrate.py` 全文；`S/token.py` 第 1–325 行；`S/engine.py` 第 1–510 行；`S/b1_metrics_production.py` 第 1–190 行及第 1560 行至文件末尾                                                  |

未展开清单外的传递依赖，也未执行仓库代码、训练、optimizer、profiling 或仓库修改。仍未知的是两次历史故障的根因、新调用方的实际集成正确性、新完整路径能否在 600 秒内完成，以及 seed 21203 的原生性能。**这些未知限制运行接受和结果主张，但现有证据已足以选择上述最小、有界、同机制的新比较。**
