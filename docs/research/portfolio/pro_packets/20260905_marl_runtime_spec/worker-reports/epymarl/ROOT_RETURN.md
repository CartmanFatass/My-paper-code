# Root return — EPyMARL fixed-SHA performance scout

对象是 `C:/Projects/ref-lib/epymarl` 的固定 SHA
`cbc38c09588064eab978501d0f12c2cf58fa7fc2`，官方身份由
[uoe-agents/epymarl README](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/README.md#L1-L10)
和 [pinned tree](https://github.com/uoe-agents/epymarl/tree/cbc38c09588064eab978501d0f12c2cf58fa7fc2)
核验；许可是 Apache-2.0，`NOTICE` 已保留。

主链为 `main.py:35-44` seed/config → `run.py:98-147` 建 runner、scheme、ReplayBuffer、
MAC、learner → `run.py:198-214` rollout/insert/sample/device/learn →
`run.py:215-267` eval/log/checkpoint。`ParallelRunner` 为每个环境创建 daemon process 和
`Pipe`（`parallel_runner.py:19-47`），父端逐环境发送 CPU NumPy action，并按连接顺序
逐个 `recv`（`127-195`）；worker 每步再读取 state/avail/obs 并发送 Python dict
（`288-313`）。因此环境可并发，但父端每步同步屏障和按序接收会形成串行/HOL 限制。
`EpisodeRunner` 明确断言 `batch_size==1`（`episode_runner.py:10-29`），是 serial 基线。

性能核心：`BasicMAC.select_actions` 的 `bs` 只给 selector，`forward` 仍处理完整 B
（`basic_controller.py:19-40`）；不等长 episode 下 inactive env 仍可能前向。no-sharing
路径的 `RNNNSAgent` 按 agent Python 循环（`rnn_ns_agent.py:13-36`）。Gymma 每步 int 转换、
padding、concat 和 Python action list（`gymma.py:73-138`）；VMAS wrapper 内部固定
`num_envs=1`（`vmas_wrapper.py:14-28`）。

Batch 是 `B×T×A` agent 布局：scheme 在 `run.py:108-126`，存储在
`episode_buffer.py:30-75`；列表更新会在 batch device 建 tensor（`87-113`），replay 是
uniform ring buffer（`208-242`）。默认 buffer CPU、sample 时整批搬 device
（`default.yaml:18-20; run.py:203-213`）。CUDA rollout action 的 `.to("cpu").numpy()`
（`parallel_runner.py:127-138`）是潜在 host sync；rollout forward 没有显式 no-grad，按
PyTorch 语义可能建 recurrent autograd 图。这些均为源码观察/推断，未做 profiler。

QLearner 对 live/target MAC 沿完整 T 循环（`q_learner.py:71-104`），再 loss/optimizer/
target update（`120-156`）；PPO 每 epoch 重复 policy/critic 时间循环，n-step return
另有嵌套循环（`ppo_learner.py:41-121, 162-235`），MAPPO 默认 4 epochs。每次 rollout
都 `get_stats` IPC（`parallel_runner.py:213-223`）；eval、Sacred/TB/W&B logging 形成
额外串行路径（`run.py:215-231; logging.py:85-129`）。

报告、六个本地导航 overlay 及对应备份在 `reports/epymarl/`；没有改 source、上游
`AGENTS`、commit/push、依赖安装或运行。`toy45min`/`UAV12h` 仅是工程调查阈值，不能声称
不同任务可直接比速，也不能删减科学要求来提速。
