> Historical PARK knowledge record. Portfolio prospectively reopened ACVC with CONTINUE on 2026-09-14; see the current DIRECTION.md and ACVC_CLUSTER_DEPLOYMENT_B03_SCIENCE_CARD_20260914.md. The dated rationale, failed families and retained assets below remain evidence, not the current lifecycle or dispatch route.
# ACVC · 可逆 PARK 知识交接

2026-09-14 UTC（本地2026-09-13）。DM 在完整独立科学复核后作出生命周期决定；不是 Pro 批准，也不是因传输故障而放弃。详见[最终复核回应与决定](ACVC_CLUSTER_DEPLOYMENT_B02_INTAKE_20260913.md#complete-scientific-review-and-dm-decision--2026-09-14-utc)。

本次替代 DM 已在 Portfolio 选择 ACVC 填补 DISH 空槽后完成[新的重开评估](ACVC_REENTRY_INTAKE_20260914.md)，仍选可逆 PARK。再次独立训练有真实价值，但本次接受训练间差异未充分解决，保留有限开发参考；不是沿用旧决定作为审批，也不是证明重复无用。未建立 B03、未追加实验或 Send。Clerk 负责将此次实质决定整合后释放科学槽位，并在本轮发布完成后安全归档；重新选其他方向属于现行空槽流程。

新 DM 已重新核验下述本地保留包的 420438 字节与 SHA-256 一致。唯一模型包仍须在任何工作树回收前被保全；不得因 `temp/` 路径或任务归档而删除。

## 为什么现在停

DM 决定：ACVC 可逆 PARK，保留已复核的有限用途证据，不立即开展第三次相同的聚集场景训练。

另一次独立训练确实可能发现固定回退失利，也可能增加复现观察；不需要先有新用户、机制或代码缺陷。现在选择接受训练间差异尚未充分解决，只保留已观察终点的开发参考，不把它升级为新策略的默认选择。继续相同实验有价值，但本轮不选择增加这项投入；与再做一次直接重复的取舍接近，已标记供用户异步查看。永久 CLOSE 则过强。这不是“两次就够”的普遍规则、资源耗尽或全部研究问题已解决。

## 学到了什么

- 聚集场景 K/B02 的两个独立终点分别出现固定回退优于原动作及各自停留的均值收益。B02 两项增量为0.1046/0.0607 J，但有4/64、11/64个世界更差；简单停留自身也提高0.0439 J。[K结果](ACVC_CLUSTER_DEPLOYMENT_B01_RESULT_EVIDENCE_20260912.md)、[B02结果](ACVC_CLUSTER_DEPLOYMENT_B02_RESULT_EVIDENCE_20260913.md)。
- 均匀场景 C01 的五个完整训练—评估单位支持其预先指定工作模型下的有限结论，不与聚集结果合并。[C01 intake](ACVC_FRESH_DENSE_PACKAGE_C01_INTAKE_20260911.md)。
- 学习门控未胜过最强固定参照；训练时直接使用固定回退的两次比较均为 DOWN。负结果不因部署收益而消失。[方向记录](DIRECTION.md)、[训练使用结果](ACVC_FIXED_F_TRAINING_USE_B02_INTAKE_20260912.md)。
- 比较的是完整执行包。各自触发、轨迹和循环记忆不同，不能据此独立归因于回退或历史机制；不能推广成稳定优势、调优后余量、跨任务效果或正式 UAV 结论。64个评估世界不是64次独立训练。

## 复核纠正

[完整科学 review](pro_packets/20260913_cluster_b02_scientific_review/archive/RESPONSE.md)未发现结果失效问题。DM 接受两项修正：后续只有继续主张同一个双对照包结论时才沿用 C/停留，其他问题重新论证比较器；不再以“第三次不能证明稳定性或修复缺陷”作为停止的充分理由。固定结果、原失败与不利样本全部保留。

## 可复用资产与边界

- 实际算法与学习入口：[Binding](../../../../experiments/candidates/acvc/native_link_loss_b01/binding.py)、[learner](../../../../experiments/candidates/acvc/native_link_loss_b01/learner.py)、[B02 runner](../../../../scripts/run_acvc_cluster_deployment_b02.py)。复用科学版本以原卡/执行记录的固定源码为准，不把移动分支当作旧实验。
- [B02原始汇总](evidence/cluster_deployment_b02_20260913/summary.json)、全部行检查、原日志与其他19项文本保存在结果记录指向的 Git 版本。完整复核交付提交为`80be57f9e95818666f336e5fe89791875dc63425`，原文11819字节，不改写。
- 唯一本地模型/原始包保留于`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/cluster_deployment_b02_20260913/native_output.tar.gz`；420438字节，SHA-256`be32ec3b31643d310fbdba780feb7d64f964cbe4df1fdc8b10a58b521b0849c0`。checkpoint 的已验证摘要为`23cde1b6ffe6cce1f7482bfc54ff73d2a95f277aedc750263c6882675af7e34b`。[保存与清理回执](evidence/cluster_deployment_b02_20260913/CLEANUP_RECEIPT.json)。重用该策略不产生独立训练重复。
- 原科学调用完整墙时164.53秒；完整历史、文档和服务成本仍有未汇总部分，不声称预算全部合规或未知开销为零。已完成的四处远端资源已按回执清理，本地保留包不可随工作树回收丢失。

## 未决问题与重开条件

训练间变动、何时固定回退会输、完整包中各因素的贡献及改变任务后的有效性仍未确定。DM 或用户实际选择更广的重复性/用途问题时，可用有限独立重复继续研究；也可因明确的任务/比较器变化或影响结论的完整性问题重开。不要求先有阳性结果、外部客户或机制证明，不自动追加实验。归档后重开应与 Clerk 协调实际槽位，防止重复方向任务。

## 当前生产者与恢复入口

无运行实验、待生成 review、科学后继或未完成 Transport。原 review 一次发送、完整响应及配对消息均已保存；本地 helper 额外要求原任务没有要求的 TASK 链接，形成的纯元数据冲突已用 Root 接受、Clerk 发布的主线`ff955721b`修复。原 Transport 对同一记录完成 ARCHIVED、COMPLETE/SENT 和所属标签页关闭；旧冲突与失败记录保留，其他标签页未改。DM 将本次提交主动交给 Clerk，Clerk 在本轮结束后安全归档任务。恢复入口是最终 intake、原 HANDOFF、完整响应及P2条目`20260913-acvc-004`，不能以新请求重置历史。
