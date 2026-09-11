# Mava 返回 Root

我按固定 checkout `C:\Projects\ref-lib\Mava`、SHA
`83f7f0d19d6fdbe07264bb226a64baf8a0b17514` 完成只读源码扫描；本地包版本是 `0.2.0`。
官方身份由 [instadeepai/Mava 固定树](https://github.com/instadeepai/Mava/tree/83f7f0d19d6fdbe07264bb226a64baf8a0b17514)
和 [固定 commit](https://github.com/instadeepai/Mava/commit/83f7f0d19d6fdbe07264bb226a64baf8a0b17514)
核对。没有安装依赖、训练、benchmark 或运行时 probe；`CORE_EVIDENCE.md` 保留主要源码行号、短片段和固定 SHA 链接。

当前 Anakin 链路是 `pmap(device) → vmap(update_batch) → lax.scan(time/update)`：FF-IPPO
在 `_env_step` 内对 `num_envs` vmap 环境步进，rollout、GAE、PPO epoch 和 minibatch 都在
scan；`pmean` 先聚合 batch 再聚合 device。初始化为每个 `D × UB × NE` 生成 reset key，
并把 state 变成 `(device, update_batch, num_envs, ...)`。默认 Anakin 是每设备 16 个环境，
FF-IPPO 的 update batch 是 2、rollout 是 128。runner 的步速分母明确包含设备、update、
rollout、update batch 和环境数。RNN 版本还保存 hidden state，并把 recurrent chunk 作为
时间序列 minibatch；不能把 feed-forward 布局套到它上面。

Sebulba 是另一条路径：Gym `AsyncVectorEnv` 在 actor 线程里保持 CPU，jitted actor 把观测
搬到 actor device、把 action 取回 CPU，再执行环境步。Pipeline 将列表堆叠为
`(num_envs, rollout_length, ...)`，通过有界 queue 施加 backpressure，再按
`learner_devices` 的 `NamedSharding` 交给 `jax.jit(shard_map(...))` learner。默认每 actor
线程 32 环境、每 executor 两线程、queue size 5；当前代码明确要求本地设备等于全局设备，
并声明不支持 multihost。learner 每次更新后等待参数 ready，再经 `ParamsSource` 发给 actor。
因此 CPU env、host/device transfer、queue 等待、learner shard_map 和评估必须分开计时。

环境语义有几个必须保留的边界：Observation 首轴是 agents，随后才增加 vector env 轴；
JaxMARL wrapper 用 dict batchify 并在 reset/step split JAX key；Jumanji wrapper 可把团队
奖励重复到 agent 轴。Gym adapter 以 `StepType.LAST` 表示 terminated 或 truncated，但
discount 只由 terminated 计算，截断仍可 bootstrap；AutoReset 把 terminal observation 放到
`real_next_obs`。其 docstring 警告不要 vmap AutoReset wrapper，而当前 Anakin runner 仍调用
`jax.vmap(env.step)`，这是待复现的当前实现事实，不能自行改成旧架构。

离策略方面，Anakin REC-IQL 使用 Flashbax trajectory buffer，存 terminal、truncation 和
`real_next_obs`，采样是 `(B,T,...)`，随后交换成 RNN 需要的 `(T,B,...)`。FF-ISAC 使用
Flashbax item buffer，先以 random explore 填充，再 scan acting 和 replay epochs。Sebulba
REC-IQL 为每个 actor 保持 CPU buffer，把采样合并后放到 learner sharding，并通过
`SampleToInsertRatio` 或 `BlockingRatioLimiter` 维护 replay ratio；这些不是可省略的性能
装饰。

JAX timer 在 learner/eval 前后配合 `jax.block_until_ready`，但没有 warm-up 排除，因此首
次编译会进入代码报告的 SPS。Sebulba 额外用 `time.monotonic()` 记录 get params、action、
env step、queue put/get、learning 和 per-eval 时间。Logger 区分 ACT/TRAIN/EVAL/ABSOLUTE/MISC；
TRAIN 只取均值，JSON 只写评估类的 episode return、win rate 和 SPS，Neptune 在 Anakin async、
Sebulba sync。README 的 45 场景/6 suite/10 seed 是上游历史 benchmark 描述，不是本次测量，
所以报告不宣称 speedup。

新增导航覆盖只放在 Mava 根及真实相关的 systems、utils、wrappers、networks、configs、
examples/test 子目录；每个文件的原文备份在 `reports/Mava/agents-overlays/`，上游源码没有
修改，`AGENTS_INDEX.json` 列出路径和 SHA。Apache 2.0 的简短授权依据是 LICENSE 66–71
行的 perpetual/worldwide/non-exclusive/no-charge/royalty-free/irrevocable copyright grant。
`toy45min` 与 `UAV12h` 仍是待规范化调查阈值；没有证据证明当前默认或任何不改语义的配置
能够达到它们。

