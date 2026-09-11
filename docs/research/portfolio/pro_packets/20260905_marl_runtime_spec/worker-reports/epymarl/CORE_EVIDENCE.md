# EPyMARL performance core evidence

查证对象是本地只读 clone `C:/Projects/ref-lib/epymarl`，上游为
`https://github.com/uoe-agents/epymarl.git`，固定提交
`cbc38c09588064eab978501d0f12c2cf58fa7fc2`。`git rev-parse HEAD`、`origin/main` 和固定
GitHub tree 均指向该 SHA。本文所有行号均由该 checkout 的 `Get-Content`/`rg -n` 复核，
不是从当前上游分支推测。固定源码链接统一使用
`https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/`。

## 身份、来源和许可

官方上游仓库将自身描述为 EPyMARL（Extended Python MARL），是 PyMARL 的扩展，并明确列出
Gymnasium、PettingZoo、VMAS、SMACv2、SMAClite、额外算法及无参数共享选项：
[官方仓库 README](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/README.md#L1-L10)。
固定提交的官方树在
[GitHub pinned tree](https://github.com/uoe-agents/epymarl/tree/cbc38c09588064eab978501d0f12c2cf58fa7fc2)。
本地 `LICENSE:2-4` 标明 Apache License 2.0；`NOTICE:1-35` 保留相对原 PyMARL 的修改/新增
文件清单。没有修改、安装依赖、训练或 benchmark；这里是源码查证，不是加速实测。

关键源码的固定 SHA permalink 索引如下；正文中的短路径与行号均指向这些链接：

| 源码路径 | 关键行 | 固定 SHA permalink |
| --- | --- | --- |
| `src/main.py` | 35-44, 90-109 | [main.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/main.py#L35-L109) |
| `src/run.py` | 98-147, 198-267 | [run.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/run.py#L98-L267) |
| `src/runners/parallel_runner.py` | 19-47, 127-195, 288-336 | [parallel_runner.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/runners/parallel_runner.py#L19-L336) |
| `src/runners/episode_runner.py` | 10-29, 68-125 | [episode_runner.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/runners/episode_runner.py#L10-L125) |
| `src/envs/__init__.py`, `multiagentenv.py` | 31-60, 53-61 | [env registry](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/envs/__init__.py#L31-L60) |
| `src/envs/gymma.py` | 73-138 | [gymma.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/envs/gymma.py#L73-L138) |
| `src/envs/wrappers.py`, `pz_wrapper.py`, `vmas_wrapper.py` | 34-40, 16-64, 14-28 | [PettingZoo wrapper](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/envs/pz_wrapper.py#L16-L64) |
| `src/envs/smac_wrapper.py`, `smacv2_wrapper.py` | 6-16, 24-34 | [SMAC wrapper](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/envs/smac_wrapper.py#L6-L16) |
| `src/components/episode_buffer.py` | 30-113, 208-242 | [episode_buffer.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/components/episode_buffer.py#L30-L242) |
| `src/components/transforms.py` | 12-22 | [transforms.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/components/transforms.py#L12-L22) |
| `src/controllers/basic_controller.py`, `non_shared_controller.py` | 19-78, 17-76 | [shared MAC](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/controllers/basic_controller.py#L19-L78) |
| `src/modules/agents/rnn_agent.py`, `rnn_ns_agent.py` | 12-36 | [shared RNN](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/modules/agents/rnn_agent.py#L12-L31) |
| `src/learners/q_learner.py`, `ppo_learner.py` | 51-201, 41-235 | [Q learner](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/learners/q_learner.py#L51-L201) |
| `src/utils/logging.py` | 85-129 | [logging.py](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/utils/logging.py#L85-L129) |
| `src/config/default.yaml`, `src/config/algs/mappo.yaml`, `iql.yaml` | 4-20, 6-10, 9-14 | [default config](https://github.com/uoe-agents/epymarl/blob/cbc38c09588064eab978501d0f12c2cf58fa7fc2/src/config/default.yaml#L4-L20) |

代表性短片段（仅保留能证明边界的必要行）：

```python
# parallel_runner.py:127-153 — action device/IPC boundary
actions = self.mac.select_actions(...)
cpu_actions = actions.to("cpu").numpy()
parent_conn.send(("step", cpu_actions[action_idx]))

# episode_buffer.py:102-113 — Python data becomes a tensor on batch.device
if type(v) == list:
    v = th.tensor(np.array(v), dtype=dtype, device=self.device)
target[k][_slices] = v.view_as(target[k][_slices])

# basic_controller.py:26-40 — full B forward, then B×A×U view
agent_inputs = self._build_inputs(ep_batch, t)
agent_outs, self.hidden_states = self.agent(agent_inputs, self.hidden_states)
return agent_outs.view(ep_batch.batch_size, self.n_agents, -1)
```

## 端到端调用链

```text
src/main.py:35-44, 90-109
  -> src/run.py:98-147  runner + EpisodeBatch/ReplayBuffer + MAC + learner
  -> src/run.py:198-214  rollout -> replay insert/sample -> device move -> learner.train
  -> src/run.py:215-267  periodic eval/logging/checkpoint/close
```

主入口在 `main.py:35-44` 设置 NumPy/PyTorch/env seed；`main.py:90-109` 还固定
`torch.set_num_threads(1)` 并合并 default、environment、algorithm 配置。
`run.py:98-147` 先创建 runner、从环境读取 `n_agents/n_actions/state_shape`，建立 scheme/group，
再创建 replay buffer、MAC 和 learner。训练循环每次只处理一个完整 episode：
`run.py:198-214` 调 `runner.run(False)`，插入 replay，满足容量后采样、按已填充时间截断、把
sample 移到 `args.device`，然后调用一次 `learner.train`。

默认配置将 runner 设为 `episode`、`batch_size_run=1`（`src/config/default.yaml:4-10`）；
MAPPO 配置切到 `parallel`、`batch_size_run=10`、`batch_size=10`
（`src/config/algs/mappo.yaml:6-10`）。IQL 仍使用 serial `episode` runner
（`src/config/algs/iql.yaml:9-14`）。这表明 runner 并行度是算法/配置选择，不是所有实验共享
的固定属性。

## Runner、环境进程和 IPC

`ParallelRunner` 在 `parallel_runner.py:19-47` 为每个 `batch_size_run` 创建一对
`multiprocessing.Pipe`，启动一个 daemon `Process`，把环境构造函数 cloudpickle 后交给
worker；每个副本的 seed 增加环境索引（`parallel_runner.py:31-42`）。reset 先向所有
worker 发送命令，再按连接顺序逐个 `recv`（`parallel_runner.py:89-104`）。

每个时间步，MAC 在父进程产生动作，动作被显式转成 CPU NumPy 后逐环境发送
（`parallel_runner.py:127-153`）；随后父进程按 `enumerate(self.parent_conns)` 顺序接收活跃
worker 的响应（`parallel_runner.py:165-195`）。这提供跨环境的并发执行，但父进程在每个
时间步形成同步屏障，并且先等待低索引连接；源码没有 `multiprocessing.connection.wait`
或响应就绪集合，因此这是潜在的 head-of-line blocking（观察到的调度结构，未实测比例）。

worker 在 `parallel_runner.py:288-336` 串行接收命令；`step` 调环境 `step`，立即调用
`get_state/get_avail_actions/get_obs`，再通过 Pipe 发送包含下一状态、可行动作、观察、奖励、
终止标志和 info 的 Python dict（`parallel_runner.py:293-313`）。reset、get_stats、render、
save_replay 也都是独立的命令/往返。

父端在发送动作后才重算 `envs_not_terminated`（`parallel_runner.py:145-160`），而接收响应
时才更新 `terminated`（`parallel_runner.py:170-190`）；刚结束的环境可能在下一次
`select_actions` 仍出现在旧的 active list 中。更大的影响来自 MAC：`BasicMAC.select_actions`
只在 selector 阶段使用 `bs`（`basic_controller.py:19-24`），`forward` 仍按整个
`ep_batch.batch_size` 构建输入和推理（`basic_controller.py:26-40`）。因此不等长 episode
时，已终止环境可能继续承担完整 batch 的前向计算；这是逐行代码推断，没有运行时测量。

`EpisodeRunner` 是直接环境调用的 serial 基线：构造时断言 `batch_size==1`
（`episode_runner.py:10-29`），循环中逐步读取状态、选动作、直接调用 `env.step`
（`episode_runner.py:68-110`），最后补上末状态和动作（`episode_runner.py:112-125`）。
它适合 IQL/QMIX/VDN 等配置中的单环境路径；不能据此把不同任务或不同 episode 长度的
wall-time 直接互比。

## 环境适配层

环境注册在 `src/envs/__init__.py:31-60`；SMAC/SMACv2 动态注册以避免同时注册造成的
依赖冲突。统一接口由 `MultiAgentEnv.get_env_info` 生成 state/obs/action/agent 数和
episode limit（`multiagentenv.py:53-61`）。

Gymnasium 适配器对每次 step 把动作转为 Python `int`，调用底层环境，逐 agent pad 观察，
并把 iterable reward 聚合成 sum/mean 或保留 individual reward
（`gymma.py:73-99`）；state 是把所有观察 `np.concatenate` 后转为 float32
（`gymma.py:101-120`），可行动作每次都通过 Python list 构造（`gymma.py:122-138`）。
`FlattenObservation` 对每个 agent 调 `spaces.flatten`（`wrappers.py:34-40`）。这些是
每步 CPU/Python 工作，具体代价取决于外部环境。

PettingZoo 包装器使用一个 `parallel_env`，把 tuple 动作改为 agent-name dict，再把 dict
结果压回 tuple/list，并在 done 时处理空观察/奖励（`pz_wrapper.py:16-29, 40-64`）。VMAS
包装器显式传 `num_envs=1`（`vmas_wrapper.py:14-28`），所以外层 ParallelRunner 的
每环境进程不能被解释为 VMAS 内层向量化；SMAC/SMACv2 包装器则每步直接委托底层环境
（`smac_wrapper.py:6-16`、`smacv2_wrapper.py:24-34`）。没有根据适配器名字推断 GPU
或内部并行。

## Batch、MAC 和 agent 维度

`run.py:108-126` 的基础 scheme 是：

| 字段 | EpisodeBatch 形状（逻辑） | 备注 |
| --- | --- | --- |
| `state` | `B x T x S` | 全局状态 |
| `obs` | `B x T x A x O` | `agents` group |
| `actions` | `B x T x A x 1` | `long` |
| `avail_actions` | `B x T x A x U` | `int` mask |
| `terminated` | `B x T x 1` | `uint8` |
| `reward` | `B x T x 1` 或 `B x T x A` | common/general-sum |

`EpisodeBatch._setup_data` 按 scheme/group 分配 transition tensor 为
`(batch_size, max_seq_length, *shape)`，episode-constant 字段则没有时间维
（`episode_buffer.py:30-75`）；`filled` mask 自动添加在 `episode_buffer.py:51-54`。
`update` 对 Python list 先 `np.array` 再在 batch device 上建立 tensor，并执行 view/赋值和
预处理（`episode_buffer.py:87-113`）。动作的 one-hot 是一次 scatter 到新 tensor
（`transforms.py:12-22`）。

replay 是环形、按 episode 存储；跨尾部插入时递归切片
（`episode_buffer.py:208-230`），采样是无 replacement 的 uniform NumPy 选择
（`episode_buffer.py:232-242`）。`EpisodeBatch.to` 遍历所有 transition/episode 字段
逐个搬到目标 device（`episode_buffer.py:80-85`）；训练循环在 sample 截断后仅在 device
不同时调用它（`run.py:203-213`）。

共享 MAC 的输入构造把 obs、可选的上一动作 one-hot、agent id 拼接，并 reshape 为
`(B*A, features)`（`basic_controller.py:63-78`）；agent 输出再 view 回 `(B,A,U)`
（`basic_controller.py:26-40`）。RNN agent 对 `(B*A, features)` 用一个共享的
`GRUCell/Linear`，hidden reshape 为 `(-1, hidden_dim)`（`rnn_agent.py:12-31`）。

无参数共享 MAC 的外层 batch 形状仍相同（`non_shared_controller.py:61-76`），但
`RNNNSAgent` 对每个 agent 做 Python `for`，分别调用自己的 `RNNAgent`，再拼回 Q/policy
输出（`rnn_ns_agent.py:13-36`）。因此 no-sharing 路径的 agent 维循环是明确的串行点，是否
被矩阵库抵消取决于规模和硬件，源码没有给出加速数据。

## Learner 的时间展开和 GPU 边界

代表性的 `QLearner.train` 先读 reward/action/termination/filled，并按 termination 更新
mask（`q_learner.py:51-70`）；随后 live MAC 和 target MAC 各自沿完整 `max_seq_length`
逐时间步 forward（`q_learner.py:71-104`），可选 mixer，再计算 1-step target、masked
TD loss，反向和 optimizer step（`q_learner.py:106-144`）。每个训练步还执行 hard/soft
target update（`q_learner.py:146-156, 178-194`）。

`PPOLearner.train` 先沿时间展开 old policy；对每个 `epochs` 再沿时间展开当前 policy，
并在每轮调用 sequential critic（`ppo_learner.py:41-121`）。critic 的 n-step return
又有 `t_start x step` 的 Python 嵌套循环（`ppo_learner.py:162-235`）。MAPPO 默认
`epochs=4`（`mappo.yaml:22-31`），所以 policy/critic 计算随 epoch 重复；这属于算法
定义的计算，不应通过删减 epoch 或其他科学要求来宣称提速。

`run.py:27` 选择 `cuda`/`cpu`，`run.py:146-147` 调 learner 的 `cuda()`；Q learner
的 `cuda()` 会把 live/target MAC 和 mixer 移到 GPU（`q_learner.py:196-201`）。但默认
`buffer_cpu_only=True`（`default.yaml:18-20`），replay 在 CPU；训练 sample 再由
`run.py:210-211` 搬到 `args.device`。

Parallel rollout 的动作明确执行 `actions.to("cpu").numpy()`
（`parallel_runner.py:127-138`），再经过 Pipe 序列化；如果 action 位于 CUDA，这个
device-to-host/Numpy 边界是潜在同步点。环境返回的 list 经 `EpisodeBatch.update` 在其
目标 device 建 tensor（`episode_buffer.py:102-106`）。源码能证明这些边界存在，不能证明
具体同步等待、带宽或 wall-time；本调查没有执行 GPU/CPU profiler。另一个可能的开销是
rollout 路径的 `forward` 没有包在 `torch.no_grad()`/`inference_mode()` 中
（`parallel_runner.py:120-137`、`basic_controller.py:26-40`、`rnn_agent.py:23-31`）。
按 PyTorch 默认 autograd 语义，这可能为每个 episode 的 recurrent hidden 链创建图；这是
语义推断，未测显存或速度。

## Eval、logging 和其他串行点

每次 Parallel rollout 完成后父端都会发送并接收每个环境的 `get_stats`
（`parallel_runner.py:213-223`），即使当前没有触发 `_log`；接收的 `env_stats` 在随后
统计聚合中未使用，源码上形成一次额外 IPC 往返。`_log` 用 NumPy 计算 return mean/std，
按 agent 循环并调用 logger（`parallel_runner.py:255-285`）。

训练主循环按 `test_interval` 运行一组 `runner.run(test_mode=True)`
（`run.py:215-231`），所以评估会消耗同一 rollout/IPC/MAC 路径；checkpoint 还会调用
learner/MAC 保存并可复制到 W&B（`run.py:233-257`）。Logger 每次 `log_stat` 先累积
本地 stats；TensorBoard 立即写，W&B 按 timestep 聚合，Sacred 则逐指标调用
`log_scalar`（`utils/logging.py:85-109`）。`print_recent_stats` 还会做窗口均值/`.item()`
（`logging.py:111-129`）。主运行默认启用 Sacred setup（`run.py:63-70`）；这些外部日志
的实际代价取决于后端设置，未测量。

## 可用于工程调查的性能假设及边界

源码支持的可检验假设是：每环境 Pipe/进程及其 pickle、父端按连接顺序的同步 recv、
inactive env 的 full-batch MAC forward、no-sharing 的 agent Python loop、每步 adapter
list/padding/concat、CUDA action 的 host boundary、rollout 未禁用 autograd、learner 的
时间步/epoch 循环和频繁 eval/logging。它们是 observations 或明确标出的 inference；本
报告没有声称任何已实现加速。

`toy45min` 与 `UAV12h` 仅作为工程调查时的时间阈值。不同任务、环境后端、agent 数、episode
长度、dtype、GPU 和评估频率不能据此直接比速；不能为了过阈值而缩短 episode、减少 agent、
改变 comparator、精度、RNG 或其他科学要求。任何后续改动必须固定源字节、记录配置并用
同任务同信息基线实测。

## 查证/完整性结果

- `git -C C:/Projects/ref-lib/epymarl rev-parse HEAD` = pinned SHA；`git status --short`
  只显示本地新增导航 overlay，未显示任何 `src` 修改。
- 已用 `rg --files` 确认所有报告引用的源码路径存在；逐个按文件行数检查报告中的行号范围。
- 固定 SHA 的 GitHub blob 链接与本地文件路径一一对应；官方 GitHub README/固定树用于身份
  查证，源码结论以本地固定 clone 为准。
- 未安装依赖、未训练、未 benchmark、未启动 env；因此没有 wall-time、吞吐、显存或
  peak-RSS 实测结果。
