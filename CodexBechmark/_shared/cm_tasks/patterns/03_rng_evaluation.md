# 模式 03：seed、评估隔离和必要状态

适用：新 seed/arm 参数连接、评估与训练隔离，以及任务确实要求的 checkpoint 状态修复。
没有 checkpoint/resume 需求时不增加恢复框架。参考 DISH seed101、UCOPE/RCLE 后续 seed 接线。

## 五项交接的本次差异

1. 目标：`<新参数/评估调用>` 应影响哪些实际计算；哪些既有路径必须保持。
2. 路径：`<CLI → Config → 初始化/采样/重置 → metadata>`；只列需改边界。
3. 语义：已有 seed/address law、初始化/训练/评估流归属、reporting label 与随机地址的关系。
4. 验收：新值实际到达计算；旧默认保持；插入评估不消耗本题训练流或改变训练状态。
5. 边界：不为方便另创命名空间、更换 RNG、改 device/dtype 或多启动一次实验。

## L1 增量

精确指出真值来自哪个 Config 字段、哪些函数已有显式 RNG 参数、输出字段复用方式。
actor 的 train/eval 模式、RNN state、normalization 统计和环境状态分别确认；`no_grad`
不等于这些状态全隔离。若 checkpoint 是本题范围，引用必需 payload，不自动要求全状态快照。

## L2 增量

画出本题实际参数透传顺序；把“展示标签”和“随机流 key”分开说明。每个采样点用已有
指定流，初始化与 evaluation 不借用训练流。清楚写出评估开始前/后谁持有可变状态。
只承诺本题需要的复现范围；不默认跨库版本、跨平台或不同 reduction 路径逐位相等。

## L3 增量

[evaluation_streams.py](examples/evaluation_streams.py) 展示 NumPy 两个显式 Generator 的
消费隔离，train/eval seed 由调用者按任务既有规则提供。它不生成 HMASD seed namespace，
不覆盖 Torch、环境或 native RNG，不证明不同 seed 的统计独立，也不保证 checkpoint 恢复。
正式代码优先使用项目已有工厂，而非把微例子的 RNG 选择复制替换进去。

依据：[NumPy Generator](https://numpy.org/doc/stable/reference/random/generator.html)；
已有 UCOPE `study.py` 与 RCLE `make_rng` 是不同方案，不能统一成同一个模板默认值。
