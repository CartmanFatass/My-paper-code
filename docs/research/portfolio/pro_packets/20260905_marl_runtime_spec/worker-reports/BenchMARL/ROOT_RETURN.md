# BenchMARL 返回 Root

我查证的版本是 `https://github.com/facebookresearch/BenchMARL.git` 的固定提交
`65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1`（1.5.2）。官方 1.5.2 发布页把该版本指向
`65d649d`，并说明配套 TorchRL 0.11；仓库和源码均标注 MIT。固定树没有上游
`AGENTS.md`，因此新增文件均为本地导航 overlay，并保留源码不变。

真实运行链是 `run.py`/Hydra → `Experiment._setup` → Task 环境与 specs → Algorithm 的
policy/loss/replay buffer → `SyncDataCollector` 或直接 rollout → collection loop → 每个
group 的 `process_batch`、buffer 与 optimizer → evaluation/logger/checkpoint。关键证据和固定
commit permalink 见 [CORE_EVIDENCE.md](CORE_EVIDENCE.md)。

批处理要分清四层：VMAS 把 `num_envs` 传给原生向量环境；PettingZoo 的 `parallel=True` 是
多智能体 API 模式，并不等于多环境；SMACv2、MeltingPot、MAgent 在适配器中不使用
`num_envs`，未向量化环境由 `SerialEnv`/`ParallelEnv` 根据 `parallel_collection` 包装；
Hydra 的多运行调度又是另一层。`SyncDataCollector` 选择的是同步 collector，源码没有自有
异步队列或预取器。

TensorDict 的 group/spec 约束是真实语义边界。非 RNN batch 在入 buffer 前 `reshape(-1)`；
RNN 保留序列，sequence length 按 `ceil(collected_frames_per_batch / n_envs_per_worker)`
推导。MAPPO 在 `process_batch` 扩展 group done/reward 并算 GAE；QMIX 将 group 终止做
`any(-2)`、reward 做 `mean(-2)`。这些是算法工作量和估计器语义，不能为提速任意重排。

设备路径是显式的：环境和 collector 用 `sampling_device`，模型/loss 用 `train_device`，
off-policy tensor buffer 用 `buffer_device`，采集 batch 先到训练设备，再到 storage，sample
又回训练设备；disk memmap 分支传给 storage 的实际 device 是 train device。`.item()` 日志
可能产生 GPU 到 CPU 同步；评估、渲染、JSON/video、checkpoint serialization 均计入墙钟，
除非协议明确排除。

仓库没有 C++/CUDA 自定义源或构建扩展；TorchRL、PyTorch、可选 PyG 和 simulator 的 native
kernel 属于外部依赖。LSTM/GRU 仅在配置开启时 `torch.compile`，固定 YAML 默认关闭；没有
本次实测 speedup、FPS、profile 或训练结果。文档关于 CUDA VMAS 的 speedup 是设计预期，
不是证据。toy 超 45 分钟、UAV 超 12 小时应作为目标系统工程查证触发器，不能类比承诺为
BenchMARL 性能。比较时必须匹配 frames、模型、环境、seed、optimizer/minibatch、评估、
日志、checkpoint 和 launcher 争用。

新增导航文件清单及备份见 [AGENTS_INDEX.json](AGENTS_INDEX.json)；原文备份在
`agents-overlays/`。未安装依赖、未运行训练/基准、未修改或提交上游。

