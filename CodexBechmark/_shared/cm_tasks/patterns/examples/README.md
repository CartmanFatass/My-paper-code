# RL spec 的三个微例子

这些代码是可读、可执行的局部参考，不是完整 learner，也不是 HMASD 生产 API。
版本条件与任务差异必须写在交接中。仅 L3 获得相应例子；主持者不得将整个库暴露给低档候选。

| 文件 | 演示的明确约定 | 不能据此推断 |
| --- | --- | --- |
| [masked_reduction.py](masked_reduction.py) | agent 项求和后按完整 row 平均，held row 仍在分母 | 所有 actor loss 都应这样平均 |
| [transition_masks.py](transition_masks.py) | 持续任务的外部截断可 bootstrap，但当前 episode 的 trace 到此断开 | 任务本身 finite horizon 也需要 bootstrap |
| [evaluation_streams.py](evaluation_streams.py) | 显式分开的 NumPy generator 不互相消费状态 | 已隔离 Torch/native/环境、模型状态或统计独立性 |

focused checks 位于 [_host/check_examples.py](../../_host/check_examples.py)，检查这些例子
承诺的边界和可区分错误的反例；不是 benchmark 隐藏验收全集，也不证明学习效果。
检查不运行训练、不连远程、不写科研证据。

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -B C:/Projects/CodexBechmark/_shared/cm_tasks/_host/check_examples.py
```

例子只在已声明的 NumPy/Torch 本地环境检查。正式题包必须记录自己的依赖版本；这里不做
版本升级，也不承诺跨版本逐位相同。两个官方概念来源：
[Gymnasium 时间限制](https://gymnasium.farama.org/tutorials/gymnasium_basics/handling_time_limits/)、
[NumPy Generator](https://numpy.org/doc/stable/reference/random/generator.html)。
