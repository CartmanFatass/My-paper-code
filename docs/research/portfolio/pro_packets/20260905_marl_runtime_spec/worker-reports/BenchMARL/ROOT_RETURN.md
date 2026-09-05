# BenchMARL 返回 Root

查证版本为 `https://github.com/facebookresearch/BenchMARL.git` 固定提交
`65d649d80e0bdcbdbe2c5d6a3f02dbfed8f0bec1`（1.5.2）。官方发布页将 1.5.2 指向
`65d649d`、配套 TorchRL 0.11；许可证为 MIT。固定树没有上游 `AGENTS.md`，新增文件
均是本地导航 overlay，源码未改。

真实运行链是 `run.py`/Hydra → `Experiment._setup` → Task 环境/specs → Algorithm 的
policy/loss/buffer → `SyncDataCollector` 或 rollout → collection loop → `process_batch`、
optimizer → evaluation/logger/checkpoint。固定 commit permalink 在 [CORE_EVIDENCE.md](CORE_EVIDENCE.md)。

并行含义分层：VMAS 将 `num_envs` 传给向量环境；PettingZoo 的 `parallel=True` 是多智能体
API 模式；SMACv2、MeltingPot、MAgent 不使用 `num_envs`，未向量化环境由
`SerialEnv`/`ParallelEnv` 按 `parallel_collection` 包装；Hydra 多运行调度又是另一层。
`SyncDataCollector` 是同步 collector，源码无自有异步队列或预取器。

TensorDict 的 group/spec 是语义边界。非 RNN batch 入 buffer 前 `reshape(-1)`；RNN 保留
序列，长度按 `ceil(collected_frames_per_batch / n_envs_per_worker)` 推导。MAPPO 扩展
group done/reward 算 GAE；QMIX 对终止做 `any(-2)`、reward 做 `mean(-2)`。这些是算法
工作量和估计器语义，不能为提速任意重排。

设备路径为：环境/collector 用 `sampling_device`，模型/loss 用 `train_device`，off-policy
tensor buffer 用 `buffer_device`；batch 先到训练设备，再到 storage，sample 又回训练设备。
disk memmap 分支实际传 train device。`.item()` 可能造成 GPU→CPU 同步；评估、渲染、
JSON/video、checkpoint serialization 都应计入墙钟，除非协议排除。

仓库没有 C++/CUDA 自定义源或构建扩展；TorchRL、PyTorch、PyG 和 simulator 的 native
kernel 属于外部依赖。LSTM/GRU 仅在配置开启时 `torch.compile`，默认关闭；本次没有实测
speedup、FPS、profile 或训练结果。CUDA VMAS speedup 是文档预期，不是经验结论。toy
超 45 分钟、UAV 超 12 小时是工程查证触发器，不能类比承诺为 BenchMARL 性能。比较需
匹配 frames、模型、环境、seed、optimizer/minibatch、评估、日志、checkpoint 和争用，
并区分算法工作量与实现吞吐。

新增导航清单和上游保留方式见 [AGENTS_INDEX.json](AGENTS_INDEX.json)；原文备份在
`agents-overlays/`。未安装依赖、未运行训练/基准、未修改或提交上游。
