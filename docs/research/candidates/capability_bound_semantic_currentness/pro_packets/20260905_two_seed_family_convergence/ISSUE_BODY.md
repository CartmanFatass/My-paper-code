这是 CBSC Direction Manager 对完整实测的综合与待决问题，不是 Pro 原文。

直接回报 B02 和另行选择的 B03 都已完整结束。两次独立运行中，RAW 与 STRUCT 的固定终点分别同时为 10.7125 和 10.5875；每组 32 个配对评价差值全部为零。每臂均完成 48 次 rollout 更新、768 次 Adam 更新，并产生非零且不同的参数变化。所有已训练的 greedy 检查点都选择固定 REFRESH，回报与同面板固定刷新参照相同。

第二次训练确实抽样过其他动作，但末批几乎只剩刷新。这既可能反映优化/探索限制，也可能反映简单策略在当前宿主的适用性；没有建立唯一原因、最优策略或总体等效。两组 seed 同时改变初始化、训练随机性及程序生成的评价世界，不能只归因于初始化。旧 B1/r05 结果界限及历史宿主错误保留。

下一问题：停止当前不变的 48 更新比较家族，还是选择一个有明确判别价值的新真实学习 B？DM 建议前者，范围限于当前比较，不改 CBSC 的 Portfolio 生命周期或优先级。一个具体次选是新配对运行增加到 192 更新、只评价 48 和 192 两个检查点；是否值得投入由本方向 Convergence 决定。没有自动第三组，也不把精确上界、全支持、历史重放或政策搜索放在学习之前。

四个正式完整调用合计 288.67 秒，另有一次 6.97 秒工程检查。新 192 更新方案仅有基于已有时段的成本推算，没有实测或启动。

固定证据：

- [B02 完整科学结果](https://github.com/CartmanFatass/My-paper-code/blob/ba45e444c1cbaa0f1d9b34e3e9cd01c3a457f993/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B02_RESULT_EVIDENCE_20260905.md)
- [B03 完整科学结果](https://github.com/CartmanFatass/My-paper-code/blob/ba45e444c1cbaa0f1d9b34e3e9cd01c3a457f993/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_RESULT_EVIDENCE_20260905.md)
- [B03 intake 与当前方向问题](https://github.com/CartmanFatass/My-paper-code/blob/ba45e444c1cbaa0f1d9b34e3e9cd01c3a457f993/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_INTAKE_20260905.md)
- [B03 原始完整输出及技术验收](https://github.com/CartmanFatass/My-paper-code/blob/ce1b3d84a604b5c12f17541dec2b303a059d2022/docs/research/candidates/capability_bound_semantic_currentness/CBSC_DIRECT_RETURN_B03_CM_RESULT_20260905.md)

新 Convergence 通过固定 TASK、专用输出分支和单一回复文件交付。DM 将直接读取完整原文并 intake；评论不构成额外审批队列。
