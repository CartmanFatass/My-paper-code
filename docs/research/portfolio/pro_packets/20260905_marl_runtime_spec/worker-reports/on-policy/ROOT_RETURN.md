# 给 Root 与 `workflow_lxh_marl_runtime_spec` 的回传

我在 `C:/Projects/ref-lib/on-policy` 的固定提交 `de66d7a4b23fac2513f56f96f73b3f5cb96695ac` 上完成源码调查。GitHub 官方主页确认这是 `marlbenchmark/on-policy` 的 MAPPO 官方实现；提交页为 <https://github.com/marlbenchmark/on-policy/commit/de66d7a4b23fac2513f56f96f73b3f5cb96695ac>，许可证为 MIT。所有结论限定这个 SHA；本次没有安装依赖、训练、benchmark、启动外部环境或测硬件时间。

核心调用链是 `scripts/train/{train_smac,train_mpe}.py` 初始化环境、seed 和 device，按 `share_policy` 选择 `runner/shared` 或 `runner/separated`，随后 `Runner(config).run()`。SMAC/MPE runner 对每个 episode 先执行 `T=episode_length` 次 `collect → envs.step → insert`，然后一次 `compute`（bootstrap/GAE）和一次 `train`；episode 数为 `floor(num_env_steps/(T·R))`，`R=n_rollout_threads`。训练、保存、日志和评估都在 runner 中调度。SMAC/MPE 的 interval 按 episode 下标判断，默认 eval interval=25 且 episode 0 即评估；Football shared runner 改按 `total_num_steps % interval`，同名参数不能跨环境解释成相同单位。

Shared 结构只创建一套 actor、critic、trainer 和 `SharedReplayBuffer`。buffer 的原始形状为 `obs/share_obs:[T+1,R,A,...]`、RNN state 同样带 agent 轴、value/return `[T+1,R,A,1]`、action/reward `[T,R,A,...]`。每个收集时刻把 `[R,A,...]` 的 NumPy 数组拼成 `[R·A,...]`，一次 `policy.get_actions` 同时完成所有 agent 的 actor/critic 推理，再 split 回 `[R,A,...]`；T 仍是 runner 的顺序循环，因此并行语义是 agent×环境样本的单步 batch，不是时间维并行。feed-forward batch 为 `R·T·A`。RMAPPО 的 recurrent generator 用 `C=floor(R·T·A/L)` 个长度 L chunk，单个 minibatch flatten 后为 `L·floor(C/B)` 条样本；整数除法意味着未整除尾部可能未被 sampler 使用，应在未来规范中固定整除关系或明确丢弃策略。

Separated 结构为每个 agent 创建独立 policy、trainer 和 `SeparatedReplayBuffer`，每份 buffer 只有 `[T+1,R,...]`。收集时 Python for-loop 逐 agent 调一次 `[R,...]` policy，最后 transpose 成 `[R,A,...]`；训练也逐 agent 串行。除 PPO 本身外，`separated/base_runner.train` 在每个 agent 更新前后各对完整 rollout buffer 重新 `actor.evaluate_actions`，并维护 `factor`。Separated buffer 会把 factor 作为第 13 项 sample 产出，而 `R_MAPPO.ppo_update` 对 13 项 sample 用 `_` 丢弃；因此对 RMAPPО/MAPPO，这套旧/新 logprob 与 factor 路径是源码可见的额外工作，是否成为主要瓶颈需要计时确认，不能直接写成已证明的优化收益。

环境向量化在 `envs/env_wrappers.py`：`R=1` 用 Dummy，`R>1` 用 `multiprocessing.Process`+Pipe 的 Subproc。`step_async` 先向所有 worker 发 action，`step_wait` 再依序 `recv` 并 `np.stack`；worker 内完成 env step，done 后自动 reset 并返回 reset observation。由此可确认 worker 间可并行推进，但主线程每步等待所有 remote，最慢环境形成 barrier，Pipe 序列化、复制和 stack 也在热路径。SMAC wrapper 每个 worker 内调用 pysc2 `run_config.start()` 并持有一个 `_sc2_proc.controller`；底层是否再派生游戏进程由 pysc2 决定，未作外部测量。Dummy 路径则在主进程顺序执行所有 env。

GPU 路径的 buffer 仍是 NumPy。`check` 对 NumPy 调 `torch.from_numpy`，actor/critic forward 随即 `.to(dtype=float32, device)`；收集输出通过 `detach().cpu().numpy()` 回写 buffer。PPO minibatch 又从 NumPy reshape/stack 后搬到 device。源码看不到 pinned memory、`non_blocking` 或 device-resident buffer；因此 CPU↔GPU 往返和同步是潜在开销。RNN 收集时一次只推进一个时间步；recurrent training 把 flatten 输入恢复成 `(T,N,feature)`，按 zero mask 边界分段调用 GRU。时间递推和 mask 分段的 Python 循环构成潜在序列瓶颈。

给 runtime 规范的直接约束是：把 `R,T,A,L,B` 写入每次运行的可复核配置；明确 shared 的单步 `[R·A]` 与 separated 的 A 次 `[R]` 语义；把 environment barrier、host/device 往返、separated 额外重算、RNN chunk 整除性列为 profiling 项，而不是未经实测的速度承诺。代表脚本 SMAC 是 `R=8,T=400,B=1,ppo_epoch=15`，MPE 是 `R=128,T=25,B=1,ppo_epoch=10`；这些只支持静态 batch 算术。toy45min/UAV12h 只能作为工程调查触发，不能跨任务保证时长或降低科学证据要求。

适用边界：固定树没有 `runner/separated/football_runner.py` 和 `runner/separated/hanabi_runner_forward.py`；`train_smac.py` 的 `SMAC` 分支还引用了树中不存在的 `onpolicy.envs.starcraft2.SMAC`。所以 shared/separated 对照应先限定 SMAC/MPE 的实际实现，Football/Hanabi 与 SMAC 别名必须单独核验。
