# MARLlib / RLlib 集成核心证据

- 查证日期：2026-09-05
- 固定仓库：`C:/Projects/ref-lib/MARLlib`
- 固定 commit：`80e9973a430271a93c781d7422133acb1198f84b`
- 上游身份：[MARLlib 固定 commit（GitHub 官方页面）](https://github.com/Replicable-MARL/MARLlib/commit/80e9973a430271a93c781d7422133acb1198f84b)
- 报告性质：只读源码取证；没有安装依赖、运行训练、启动 Ray、运行补丁链接或测量吞吐/内存/序列化。
- 许可证：仓库 `LICENSE` 与 `setup.py#L18-L31` 声明 MIT。这里只保留必要短片段和行号，未大段复制代码。

## 1. 证据边界与标签

本次固定树的 Git 工作树在查证时为 clean，库内原来没有任何上游 `AGENTS.md`。新增的 `AGENTS.md` 只是本地导航 overlay，完整文本备份在 `C:/Projects/ref-lib/reports/MARLlib/agents-overlays/`。一次早期相对路径误写曾落到共享 HMASD 工作区，Root 已在报告前精确恢复 tracked 文件并隔离误写文件；这不改变本库固定 commit 或下文源码行号。

证据标签如下：

- **O（observed）**：直接由固定 commit 的 MARLlib 源码或配置看到。
- **D（dependency declaration）**：由依赖清单、import 或本地补丁的目标路径声明；不等于已验证的运行时行为。
- **I（inference）**：根据 O/D 推断的性能机制或限制，必须结合实际运行测量才能量化。
- **U（untested）**：本次没有安装/运行/测量，不能形成性能或兼容性结论。

最重要的边界是：本地只检查了 MARLlib 自带的 `marllib/patch/rllib/` 文件副本，没有检出或读取独立 Ray/RLlib 源码。官方 Ray 的 [ray-1.8.0/rllib 目录身份页](https://github.com/ray-project/ray/tree/ray-1.8.0/rllib)只用于核验项目/路径身份；不能把它当成本次已核验的 RLlib 实现。因此，采样器、RolloutWorker、SampleBatch 内部字段协议、Tune worker 调度、对象存储和跨进程传输的具体行为均标为 D/I/U，除非 MARLlib 自己的代码明确写出。

固定依赖清单位于 [`requirements.txt#L1-L16`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/requirements.txt#L1-L16)：`ray==1.8.0`、`ray[tune]==1.8.0`、`ray[rllib]==1.8.0`、`torch==1.9.0`、`gym==0.20.0`、PettingZoo 1.12.0、NumPy 1.20.3。它证明了目标 API 世代和兼容性意图（D），不证明当前机器具备这些版本或运行成功。

## 2. 端到端调用链（代码事实与边界）

静态调用链可写成：

`marl.make_env` → `register_env` + 驱动端环境实例 →（D/U：Ray/RLlib 注册与采样）→ `MultiAgentEnv.reset/step` 返回逐 agent 字典 →（D/U：RLlib 采样器形成 `SampleBatch`/`MultiAgentBatch`）→ `run_il`/`run_cc` 的 policy mapping 与 postprocessing → Tune script 注册 custom model → custom Policy/Trainer learner 或 `episode_execution_plan` →（D/U：权重回传、worker 调度与 checkpoint）。

入口 [`marllib/marl/__init__.py#L23-L32`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/__init__.py#L23-L32) 直接 import `MultiAgentEnv`、`register_env`、环境/模型注册表。`make_env` 在 [`#L72-L153`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/__init__.py#L72-L153) 读取 YAML，检查 registry，把名称拼成 `env_map`，以 lambda 调用 `ENV_REGISTRY` 或 `COOP_ENV_REGISTRY` 注册，并在 driver 立即实例化相同 wrapper。这个“注册后由 RLlib/Tune 何时、在哪个进程实例化”是依赖行为，MARLlib 未在本地给出 RolloutWorker 实现。

### 环境 wrapper

| 代码位置 | O：固定树能直接看到的行为 | I/D：性能含义与限制 |
|---|---|---|
| [`base_env/mpe.py#L94-L135`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/envs/base_env/mpe.py#L94-L135) | `RLlibMPE` 通过 Supersuit pad observation/action，再包 `ParallelPettingZooEnv`；观测包装为 `{"obs": ...}`，step 返回每个活动 agent 的 obs/reward 与 `{"__all__": d["__all__"]}`。`#L145-L153` 返回空间、agent 数、episode limit 和 mapping info。 | padding 与嵌套字典会改变每步 payload；逐 agent 字典使 payload 至少按活动 agent 数复制。实际 Python/Ray 序列化字节数、worker 位置和吞吐未测（I/U）。PettingZoo/RLlib 转换细节是 D/U。 |
| [`base_env/smac.py#L40-L115`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/envs/base_env/smac.py#L40-L115) | `GymDict` 含 `obs`、`state`、`action_mask`；reset/step 对每个 agent 都放入同一个全局 state，step 将单个 SMAC reward 复制给每个 agent，终止为 `{"__all__": terminated}`。 | 全局 state 与 action mask 被逐 agent重复携带（O），因此 I：采样 batch 和跨进程 payload 的 state 部分随 agent 数增长；没有实测占用或传输成本。 |
| [`base_env/mamujoco.py#L93-L153`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/envs/base_env/mamujoco.py#L93-L153) | 每个 agent 返回 `obs` + 同一 `state`；step 先按 key 排序动作，再 `np.array`、normalize，随后为每个 agent 写 reward/obs，返回 `__all__`。 | 排序、数组重建、归一化和 state 复制是本地可见的 CPU/内存工作（O）；其比例和跨进程代价未测（U）。 |
| [`global_reward_env/mpe_fcoop.py#L35-L48`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/envs/global_reward_env/mpe_fcoop.py#L35-L48) | 合作 wrapper 汇总所有 `r[key]`，再把 `reward/self.num_agents` 发给每个活动 agent。 | reward 聚合和复制是 O；它没有提供通信/采样性能证据，不能把 cooperative reward 逻辑解释成共享 policy 或集中式 learner。 |

`base_env/__init__.py` 和 `global_reward_env/__init__.py` 用 try/except 导入环境，把缺少依赖保存为字符串错误（O；见各自 `#L23-L39` 附近）。这说明“能否 import 某环境”受外部依赖影响，但本次没有安装或验证任何环境。

## 3. policy mapping、shared policy 与联合 Q grouping

IL 的 [`run_il.py#L70-L118`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_il.py#L70-L118) 和 CC 的 [`run_cc.py#L95-L146`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_cc.py#L95-L146) 都实现 `all/group/individual`：

- `agent_level_batch_update=True` 时共享名是 `default_policy`，否则是 `shared_policy`（`run_il.py#L77-L84`；CC 对应 `#L102-L110`）。
- `all` 需要 `all_agents_one_policy`，mapping lambda 恒返回共享名；`group` 按 `team_prefix` 创建 policy，lambda 使用 agent ID 的前缀（IL `#L86-L103`）；`individual` 按 `agent_name_ls.index(agent_id)` 映射到每 agent policy（`#L105-L115`）。
- run config 将 policies、mapping fn、`num_workers`、`num_gpus`、`num_gpus_per_worker`、framework 和 `simple_optimizer=False` 交给 Tune/RLlib（IL [`#L124-L136`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_il.py#L124-L136)；CC [`#L165-L178`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_cc.py#L165-L178)）。
- HAPPO/HATRPO 会在 CC runner 中强制 individual mapping（[`run_cc.py#L148-L159`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_cc.py#L148-L159)），这是 O。
- 对 qmix/vdn/iql，VD runner 不构造 policies/mapping，而是把全部 agent 通过 `with_agent_groups` 成为一个 `group_all_` 联合环境；joint Q 不支持 individual，代码见 [`run_vd.py#L89-L132`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_vd.py#L89-L132)。这改变了后续 batch 的形状和 learner 边界，不能与普通 shared policy batch 直接作速度比较。

O 只证明 mapping 函数、policy 集合和 config 字段被构造。mapping 函数在何处被调用、同一 policy 的样本是否如何拼接、RolloutWorker 如何广播 policy 权重，均是 D/U；本地未读取 RLlib 的 `policy_mapping_fn` 或 worker 源码。

## 4. MultiAgentBatch、跨 agent postprocessing 与额外拷贝

集中式 critic 的 [`centralized_critic.py#L48-L124`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/utils/centralized_critic.py#L48-L124) 直接要求 `other_agent_batches`（`#L77-L84`），对每个 opponent 用 `align_batch`，构造 state，再 `np.stack` opponent actions（`#L88-L104`），最后调用 central VF 并写回 `VF_PREDS`。初始化尚未 ready 时则在 `#L126-L141` 建零 state/action。GAE/advantage 计算最终调用 imported `compute_advantages`（`#L143-L162`）。这形成了：

`SampleBatch(own agent)` + `other_agent_batches` → 对齐/堆叠 state、opponent actions → central value → RLlib-style advantage。

`other_agent_batches.values()` 的前 `n_agents-1` 个元素在 `#L78-L80` 被当作 opponents，随后又按 key 查找（`#L93-L100`）。这是固定代码的顺序假设；是否由 RLlib 保证 key 顺序、不同 agent episode 长度如何产生这些批次，本次未验证（O + U limitation）。

Q mixing 的 [`mixing_Q.py#L48-L58`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/utils/mixing_Q.py#L48-L58) 发现长度不等时截断较长 batch，或重复较短 batch 的末尾切片补齐。`before_learn_on_batch` 在 [`#L146-L226`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/utils/mixing_Q.py#L146-L226) 对每 policy `copy.deepcopy`、padding、计算 Q/target Q，再 `np.stack`；`#L228-L260` 为每 policy 构造并写入 `opponent_q` 和 `next_opponent_q`。因此 O 可见的 CPU/内存机制包括：

1. policy batch 的深拷贝；
2. RNN padding 后的数组；
3. 所有 agent Q 的 stack，以及为每个当前 agent 删除自身后的 opponent 数组；
4. 不等长 batch 的截断/末尾重复。

I：这些步骤会引入至少 O(agent 数 × batch) 的中间数组和额外 copy/stack，长度对齐还可能使用重复数据；常数、峰值 RSS 和 wall time 未测，不能报告为实测开销或准确复杂度。

## 5. RNN batch、序列 padding 与多设备 policy

MARLlib 的本地 patch 文件说明了它想接入哪一代 RLlib 逻辑，但不证明 patch 已激活。`rnn_sequencing.py` 的 docstring 说时间维度在最后一刻添加、postprocessing 动态 padding，并明确写出“zero inputs”对 loss 无显著影响的假设（[`#L23-L34`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/rnn_sequencing.py#L23-L34)）。`pad_batch_to_sequences_of_same_size` 在 [`#L53-L125`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/rnn_sequencing.py#L53-L125) 处理 state、seq lens、batch divisibility；`chop_into_sequences` 在 [`#L216-L344`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/rnn_sequencing.py#L216-L344) 按 episode/agent/unroll 及 max length 切段并零填充；带 burn-in 的 timeslice 在 [`#L347-L465`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/rnn_sequencing.py#L347-L465)。

模型端 `BaseRNN` 将 flat 输入变成 `[B,T,...]` 后调用 GRU/LSTM，再 flatten 回去（[`models/zoo/rnn/base_rnn.py#L112-L179`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/models/zoo/rnn/base_rnn.py#L112-L179)）。IPPO 将 `train_batch_size = batch_episode * episode_limit`，令 `model.max_seq_len=episode_limit`，并把 SGD minibatch 放大到不小于 episode limit（[`algos/scripts/ippo.py#L52-L99`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/scripts/ippo.py#L52-L99)）。VD/Q 脚本同样设置 `max_seq_len=episode_limit`，并把 buffer、train batch、target update、learning starts 按 episode limit 换算（[`vdn_qmix_iql.py#L78-L106`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/scripts/vdn_qmix_iql.py#L78-L106)）。

本地 Torch policy snapshot 的 device 选择见 [`torch_policy.py#L153-L220`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/torch_policy.py#L153-L220)：worker 0 使用 `num_gpus`，远程 worker 使用 `num_gpus_per_worker`；CPU/fake GPU 会保存一个或多个 model tower，真实 GPU 会 deep-copy model 到各 device。加载 batch 时 CPU shortcut 直接 padding 并保存一个 batch；多 device 路径先按设备 timeslice、每片 padding、再搬到设备（[`#L540-L591`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/torch_policy.py#L540-L591)）。学习时 shared policy 有单独的 batch slicing，多个 tower 先同步权重，再平均梯度（[`#L600-L685`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/torch_policy.py#L600-L685)）。多设备梯度路径用线程，分布式 world size 时还可 `all_reduce`（[`#L983-L1100`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/policy/torch_policy.py#L983-L1100)）。

性能含义是 I/U：padding waste、timeslice copy、model deep-copy、device transfer、tower weight copy、thread/allreduce latency 都是潜在成本；本次没有 Ray/torch runtime，无法确认这些 snapshot 是否与安装版本一致，也没有任何序列长度分布或 GPU 测量。patch 的激活边界由 [`marllib/patch/add_patch.py#L32-L83`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/add_patch.py#L32-L83) 与 [`#L95-L106`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/add_patch.py#L95-L106) 明确：脚本会把本地 replay/preprocessor/RNN/Torch policy 文件链接到已安装 Ray 路径。本次没有运行脚本，因此不能声称当前 Ray 使用了这些补丁。

## 6. learner、execution plan 与 replay buffer

IL/CC 使用旧版 RLlib Policy/Trainer 扩展。`core/IL/ppo.py#L23-L45` 从 RLlib PPO policy/trainer 派生 IPPO；`core/CC/mappo.py#L40-L92` 将 central critic postprocess/loss 与 `ppo_surrogate_loss` 组合，再用 `PPOTrainer.with_updates` 构造 MAPPO trainer。这里可观察到的 learner 入口是 Policy loss/Trainer（O），不是一个本地新式 Learner API；RLlib 实际训练循环仍是 D/U。

联合 Q 路径的 [`core/VD/iql_vdn_qmix.py#L49-L168`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/core/VD/iql_vdn_qmix.py#L49-L168) 明确计算 `[B,T,n_agents]` 形状、可用动作 mask、Double Q 选项、mixer target 和 masked L2 loss；`learn_on_batch` 在 [`#L321-L423`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/core/VD/iql_vdn_qmix.py#L321-L423) 解包 grouped observation、构造 sequence mask、按 agent 组织数据、可选 reward standardize、反传并更新 optimizer；`JointQTrainer` 在 [`#L534-L539`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/core/VD/iql_vdn_qmix.py#L534-L539) 绑定旧版 `GenericOffPolicyTrainer` 与自定义 execution plan。

execution plan [`episode_execution_plan.py#L35-L82`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/utils/episode_execution_plan.py#L35-L82) 的调用链是：

`ParallelRollouts(mode="bulk_sync")` → `StoreToReplayBuffer` → `Replay` → `before_learn_on_batch` → `TrainOneStep` → `UpdateTargetNetwork`，

然后通过 `Concurrently(mode="round_robin", round_robin_weights=[1,1])` 交替收集和训练。此处是 MARLlib 自己明确的老式 execution graph（O）；`ParallelRollouts`、`TrainOneStep` 如何跨 worker 传输则依赖 RLlib/Ray（D/U）。

`EpisodeBasedReplayBuffer` 继承 patched/local replay，并把 `replay_batch_size` 重设为 episode 数；`add_batch` 复制 batch 后按 policy 保存完整 sample batch，不做普通 timestep slicing（[`episode_replay_buffer.py#L23-L70`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/utils/episode_replay_buffer.py#L23-L70)）。这是保留整 episode 的 O；capacity 的最终单位、跨 shard 行为仍依赖继承实现。

patched `LocalReplayBuffer` 文档称 Ray actor 单线程并可用多个 replay actor 扩展（[`replay_buffer.py#L386-L391`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/execution/replay_buffer.py#L386-L391)）。构造时将 `learning_starts`/capacity 除以 shard 数，并在 sequence length > 1 时把 replay batch 转成 sequence 数（`#L448-L465`）；按 policy 创建 `PrioritizedReplayBuffer`（`#L476-L480`）。`add_batch` 先 `batch.copy()` 以避免 pin plasma memory，再在 lockstep 或 independent 模式按 timestep/带 burn-in 的 sequence 切片（[`#L502-L538`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/execution/replay_buffer.py#L502-L538)）；replay 在 independent 模式对每个 policy 分别 sample 并返回 `MultiAgentBatch`（`#L540-L561`）。容量告警使用 item size 与 `psutil.virtual_memory().total`，超过总内存则 raise、超过 20% 则 warning（[`#L54-L70`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/patch/rllib/execution/replay_buffer.py#L54-L70)）。

这里能形成的性能判断仍为 I：batch copy、sequence padding、per-policy sampling、priority updates 和 actor/object-store 交互会产生额外 CPU/内存/传输成本；没有实际 replay size、RSS、Ray object store 或 wall-time 观测。`ReplayActor = ray.remote(num_cpus=0)(LocalReplayBuffer)`（`#L597`）是 O/D 的 actor 声明，不能单独证明实际跨进程部署、并发度或序列化耗时。

## 7. 资源配置与跨进程成本

默认 Ray 配置 [`marllib/marl/ray/ray.yaml#L23-L40`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/ray/ray.yaml#L23-L40) 为 `local_mode: True`、`num_workers: 1`、`num_gpus: 1`、每 worker CPU 1、每 worker GPU 0，并使用 Torch；这只是默认 YAML。IL runner 在 [`run_il.py#L36-L47`](https://github.com/Replicable-MARL/MARLlib/blob/80e9973a430271a93c781d7422133acb1198f84b/marllib/marl/algos/run_il.py#L36-L47) 调 `ray.init(local_mode=..., num_gpus=...)`；CC/VD 有同样入口。worker 数和 worker 资源随后进入 Tune config，而不是由这行 `ray.init` 独立证明。

资源机制的可观察部分：

- O：local mode、worker/driver GPU 配额、CPU 配额、Tune `num_workers` 字段、torch policy 的 device/tower 分支。
- D：Ray 是否创建独立 worker、对象 store 是否发生跨进程拷贝、注册环境是否在 worker 重建。
- I：关闭 `local_mode`、增加 worker 或使用 GPU 可能把 wrapper 输出、SampleBatch、policy 权重和 replay batch 放入进程/对象存储路径，带来 serialization/copy/通信开销；这不是本次测量。
- U：当前机器的 Ray/torch 版本、可用 GPU、peak RSS、object store、worker wall time、batch throughput 和 learner utilization 均未读取。

没有把任何 toy（>45 min）或 UAV（>12 h）工程核验时间转化为科学门槛，也没有跨任务速度比较；工程查证时间不能放宽科学要求。

## 8. 结论矩阵

| 主题 | 固定树 O | 只能 D/I/U 的部分 | 本次状态 |
|---|---|---|---|
| 环境协议 | dict-per-agent、nested `obs/state/action_mask`、`__all__`、合作 reward 代码 | RLlib sampler 如何收集/拼接、真实序列化 | O；runtime U |
| policy mapping | all/group/individual、shared/default 名称、HAPPO 强制 individual | mapping invocation、policy sample batching、权重广播 | O；D/U |
| MultiAgentBatch | local postprocess 读取 `other_agent_batches`、align、stack、deepcopy | RLlib batch schema 与 worker 生成方式 | O；D/U |
| RNN | 本地 snapshot 的 pad/chop/timeslice、model max seq、multi-device load/gradient | snapshot 是否已链接到安装 Ray、zero padding 的实际 loss 影响 | O；activation/loss U |
| learner | PPO/A2C wrapper、central VF、JointQ loss/optimizer、旧 execution graph | RLlib Trainer 内部 orchestration 与 learner scheduling | O；D/U |
| replay | per-policy buffer、copy、sequence/burn-in、capacity warning、Ray actor 声明 | actor 数、object store、真实 capacity/RSS/wall time | O；I/U |
| resources | YAML 与 runner 传递的 worker/GPU 字段 | 实际进程/设备分配、serialization cost | O；D/U |
| 性能比较 | 没有数值结果 | 所有吞吐、内存、延迟、速度结论 | 未测，禁止宣称 |

后续若要把这些机制升级为可比较性能证据，必须先锁定相同 MARLlib commit、Ray/RLlib 与环境依赖、agent 数/episode limit、policy mapping、sequence length、worker/GPU、seed 和采样/learner budget，再记录 peak RSS、batch/step wall time、跨进程序列化或 object-store 指标。此报告没有替代任何科学卡、实验资源 preflight 或结果证据要求。
