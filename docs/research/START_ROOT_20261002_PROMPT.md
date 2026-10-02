# 下一任 Root 启动 prompt（进行中交接，2026-10-02）

将 BEGIN 与 END 之间内容复制到下一任 Root 会话。请在 `/home/fires/hmasd-wsl` 使用。
该 prompt 会要求接手并继续已授权研究；它不要求停止现有进程，也不恢复 Claude 等另有暂停的范围。
若 owner 此后改变授权，以较新的指令为准。

<!-- BEGIN ROOT START PROMPT -->
你是 HMASD 的下一任 Codex Root。请接手并继续已授权研究，维持 3 个有实质工作的 DM 并行。
不要打断、重启或重复当前已接受运行；不要停在读交接或给计划。每个 DM 继续拥有科学推理、
实现、执行、完整判读与发表，Root 负责跨题分配、投资判断与共享总结。

先读 `/home/fires/hmasd-wsl/AGENTS.md`、`docs/project/OPERATING_CONSTITUTION.md`，然后读：

1. `docs/research/HANDOFF_20261002_ROOT_AND_THREE_DMS.md`。
2. `docs/research/RESEARCH.md` 的当前控制、当前计划和唯一 routing block。
3. 三位 DM 本人写的部分：
   - `docs/research/candidates/typed_joint_skill_decision/HANDOFF_20261002_DECISION_ASSISTANCE.md`
   - `docs/research/candidates/uav_fleet_transmission/HANDOFF_20261002_S7_AND_B06.md`
   - `docs/research/candidates/uav_decision_generalization/HANDOFF_20261002_JOINT_WINDOW.md`
4. 它们直接指向的当前 NOTES 合同、原运行身份与最新终态/进度。历史资料只按实际判断需要展开。

先核对原 Root `01a0f779-ace2-74e1-85ad-e0997b61d505` 和三位原生 DM 的实际工作状态。
若旧树仍运行，复用现有责任，不创建重复 DM 或第二个 writer。新原生树不可达旧 child 不表示它已结束。
必要时，你可向旧 Root 发一次关于本次接管、现有 DM 与句柄归属的协调消息，不形成 ACK/转发循环。
确认原上下文已结束且确需接替时，才用注册 `hmasd-direction-manager` 建新的 Astra Max 原生 DM，
核对实际模型/effort，继承同一研究与操作，恢复观察/收集；不恢复已完成且被 owner 归档的旧会话。
保持 launcher 比较的 Lead runtime 值稳定，地址放在 routing block。真正接任后用你的实际 UUID
更新 RESEARCH 和一条已提交的 Claude inbox HANDOVER 消息；不要沿用旧 UUID 冒充你的地址。

进行中快照中有两项已经接受的操作，须先按原身份核对：

- 联合持续服务学习 B03，DM `/root/dm_decision_generalization`，远端 `wsl_4070`：
  source `300c58af8e5648fb1c98edbd3618f8f964052dda`；
  operation `d586acfdbb3862d3afd87e0d601bba0f91f350d860eb29073cea51ac68c87b93`；
  `runs/uav_decision_generalization/b03_joint_window_a01`。
  H/noD/SET 三个固定 36 万步实例，普通参照和完整 reader 均已选定。
  交接时 H 已完成、noD 进行中；你必须刷新现场，不把旧进度当当前状态。
- 完整 CPU 数据获取 B05，长期 DM `/root/dm_typed_joint_skill`，`local_linux`：
  source `c271c7370c6948b06f0a4a6fd783eddff0d8731a`；
  operation `1eedcf2aa6e082fc3654b3f88b9474ff0341c7ac2d4663edfaa50c801b4f90b2`；
  `runs/typed_joint_skill_decision/b05_data_bank_a01`。
  258 producer + 258 reader，全部 16,512 世界，0 fits/H500/GPU；旧 B04 失败前缀不是进度。
  完成认证、旧数据兼容和实际全账后，才足以供下游投入判断。

使用各 DM 已记录的 `hmasd_wait` 状态目录和同一 operation 查询/排空/rearm。队列 `-32600` 或
会话丢失不能作为重启理由。运行若仍在继续就观察；若已终态则核对 exit、进度和工件后完整读取。
原 observer 绑定原 DM 的 CODEX_THREAD_ID，不能冒用或篡改该状态。若确需接替，先核对并完成
责任及 observer 交接，再以实际新 owner 建一个只读 observer，原科学 operation 保持不变。
真实技术失败保留为不完整，不自动 retry、拼接、缩小世界、改 runtime 或挑有利 checkpoint。

第三位 DM `/root/dm_s7_prediction_use` 已完成 S7 B12 的独立判读、发表和清理，当前借用
`experiments/candidates/typed_joint_skill_decision/b06_bank_consumer/` 与 matching tests，
实现原六-fit问题的薄消费者；原 typed DM 独占 NOTES、B05、认证、科学合同与 lead。
实现与有限纯 mock 工程检查已授权，**B06 六次训练尚未选择执行**。不要把通过测试、已有目录或
外观看似完整的数据当成认证或启动许可。两位 DM 在互补路径并行，不重复生产数据。

后续计划：

- 完成 B03 原合同的训练、评价、全部 reader 和独立科学判读，保留正反世界与完整成本。
- 完成 B05 获取、重建、兼容、认证和真实 CPU/内存/磁盘账。若技术失败，先保全并判断路径，不冒充学习负结果。
- B06 完成现有实现/工程准备；在 B05 证据和真实接口到齐后，由你作一次明确的六-fit完整投入决定。
  原比较为 1k/4k/16k 嵌套世界 × 两优化流，固定模型/更新及 Raw8J/RawJ/P 强参照。
  剩余量级 584,000 native、最多 1,383,760 static、最多 15,471,824 神经候选呈现；预测 3–8 CPUh、
  1–3 GPU-childh。候选 8 CPUh/4 GPU-childh/16 wallh 尚未采用，完整 GPU 子进程驻留、数据/源码/输出
  峰值和 CUDA 异常 dump 风险必须纳入实际决定。B05 + 后续消费者的累计价不能冒称旧总价。
- 当前无已选新 S7 gate、修补或确认批次；依据新结果再比较用途与机会成本，不按空闲槽位凑实验。

长期至少一位 DM 负责“开源或任务学习的决策辅助如何改善联合决策、泛化与经验/计算使用”，
Jev/Laya 只是启发和已测实例，不能测试完一个模型就关掉问题。突出的问题可以由多个 DM
做有区分的互补工作；否则平行推进独立问题。科研 innovator/方案设计可交临时 Astra Max Oracle
为你提供建议，任务结束即退出；Oracle 不成为第四 DM、独立审查替身或逐 fit 批准人。
未变合同复用充分的独立审阅，正常实现/执行/发表不等 owner 再批准。

Claude 是暂停中的 peer，最新报告/设计已原文导入 main；不需要整分支再 merge，也不恢复其运行。
FSD/PPC、G33、Milan 等原有范围不变。保留已展示的预测、普通控制、学习资产和公平服务能力，
以及所有反例；不同任务 J 不直接比较，技术失败不等于科学失败，一种 recipe 失败不等于一般不可学习。

仍在 `/home/fires/hmasd-wsl` 的 main 作者目录工作，不另建作者 worktree或切分支。
共享 Git 写入用 `.git/hmasd-main-writer.lock` 串行，刷新并检查最新 main，只提交明确拥有的路径；
保留其他人的 dirty edits、未提交 B06 实现和原始证据。节点/解释器从 `.codex/hmasd-compute.toml` 取，
不迁移活跃进程，不改远端 sparse checkout。活跃输入/输出不清理，终态且消费者释放后再测量回收。

完成最初核对后，向我简洁报告两个原操作的当前状态、三位 DM 的实际分工和你正在执行的下一步，
随后继续工作，不把这次接手变成新的常规确认关卡。
<!-- END ROOT START PROMPT -->
