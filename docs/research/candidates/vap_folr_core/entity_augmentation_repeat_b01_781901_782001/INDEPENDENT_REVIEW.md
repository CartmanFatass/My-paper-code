# Independent Astra/high review

Native child /root/dm_folr_resume_20260914/review_a_high_folr_persistence_b01
reviewed source78437b89f901f0a3ef1828f768039ea41e7d29a3 against
ef3605be4f67935062d72d459173552f8872b68b in the maintained authoring checkout.
Full native return follows; it is source review, not a new empirical observation.

> 已独立审查 `78437b89f901f0a3ef1828f768039ea41e7d29a3`，基线为 `ef3605be4f67935062d72d459173552f8872b68b`。**未发现材料性缺陷。**
>
> 覆盖结论：
>
> - 原 factory 将 A 路由到默认 **persistent** AugmentedActor，G 保持原 Generic/head；未误接 Z。既有模型、环境、collector、learner 和统计依赖与已审来源一致。
> - 每次调用独立构造 actor、targets、optimizer、replay；兼容模块与外部 RNG 对齐，不冒称完整网络相同。
> - 四个 wrappers 的块、训练/评估种子及 arm 正确。完整流程保留 **5000/4969/128**，A 完成评估后才读取自己的 G。
> - object/block/seed/source/exposure 检查阻止旧 G、错块、异源或不完整端点形成假 primary；无效 G 保留 A 的独立事实。
> - `study_result` 要求固定顺序 `[1,2]`、共同来源，保留两个差值；严格 ±1 边界和混合模式符合卡片，描述均值不改变分类。
> - 未新增无卡依据的禁用工程设施。新增非测试源码 **340 行**（含 wrappers 48 行），runner **210 行**；测试 **191 行**，均在预算内。算得总计 **410240 ticks / 19876 updates**，其余位置计数与卡一致。
>
> 限制：此次为只读源码及测试覆盖审查，未执行 suite、native smoke 或 fit；远端 focused suite 的实测结果尚未提供。单次 runner 只发布本臂及本块结果，完整 study 汇总仍需 DM 收集四端点后调用 `study_result` 并保留输出；缺失块不得生成 study polarity。实际资源、线程和科学端点仍待执行证据。技术验收归 DM。

DM accepts this independent coverage. The separately executed focused suite's
one failure is a test-fixture duplicate keyword, not a reached production defect;
its repair changes no scientific source, wrapper or card. Technical acceptance
will follow the affected fixture checks. At full collection DM will call the
published study_result on all four endpoints, independently read back both
differences, and preserve incomplete block facts without inventing study polarity.
