# MARLlib 查证回传（Root）

固定来源是 `C:/Projects/ref-lib/MARLlib` 的 `80e9973a430271a93c781d7422133acb1198f84b`。官方身份由 [MARLlib commit 页面](https://github.com/Replicable-MARL/MARLlib/commit/80e9973a430271a93c781d7422133acb1198f84b) 与 [Ray 1.8.0 RLlib 目录](https://github.com/ray-project/ray/tree/ray-1.8.0/rllib)核验。报告只读 MARLlib 自身代码；没有检出 RLlib 源码、安装依赖、运行训练或测量吞吐、RSS、对象存储和序列化。完整行号、短片段、SHA permalink、标签和限制见 `CORE_EVIDENCE.md`。

实际调用链为：`marl.make_env` 读取 YAML，检查 `ENV_REGISTRY/COOP_ENV_REGISTRY`，调用 Ray `register_env` 并在 driver 实例化 wrapper；随后依赖 RLlib 的采样器形成 agent/policy batch，再进入 MARLlib 的 Tune script、postprocessing 和旧版 Policy/Trainer。环境 wrapper 的事实是逐 agent 字典和 `{"__all__": done}`。MPE 先用 Supersuit pad 观测/动作；SMAC 在每个 agent 的 Dict 中重复全局 `state` 和 action mask；MuJoCo 为每个 agent 重建归一化后的 obs/state；合作 wrapper 先求 reward 总和再除以 agent 数。SMAC/MuJoCo 的全局字段复制是明确的 payload 放大机制，但没有实测字节数。

IL/CC runner 支持 all/group/individual mapping。共享名随 `agent_level_batch_update` 在 `default_policy/shared_policy` 间切换，group 用 agent ID 前缀，individual 用 agent 列表索引；HAPPO/HATRPO 在 CC runner 强制 individual。QMix/VDN/IQL 走另一条路径，把全部 agent 以 `with_agent_groups` 组成 `group_all_`，随后 policy/mapping 设为 None。两条路径的 batch 形状和 learner 边界不同，不能直接拿普通 shared policy 的速度与联合 Q 比。

集中式 critic 读取 `other_agent_batches`，调用 `align_batch` 后堆叠 state 和 opponent actions，再算 central VF 和 GAE。Q mixing 对每个 policy batch 做 deep copy、padding、Q/target Q 计算和 `np.stack`，并写回 `opponent_q`；长度不足时会重复末尾 slice，长度过长时截断。这里可推断额外的 O(agent 数×batch) 中间数组、copy/stack 与可能的 padding/重复数据；不能把它报告成已测 wall time。central critic 还按 `other_agent_batches.values()` 前 `n_agents-1` 项取 opponent，顺序保证没有在本地 RLlib 源码中核验，应作为工程风险记录。

RNN 路径设置 `max_seq_len=episode_limit`。仓库内的 patch snapshot 会按 episode/agent/unroll 切序列、零填充、支持 burn-in overlap；Torch policy 多设备时做 batch timeslice、padding、device transfer、model tower deep-copy、权重同步和梯度平均，多 GPU 用线程，分布式 world size 可 all-reduce。patch 只有执行 `marllib/patch/add_patch.py` 才链接进已安装 Ray；本次没有运行，所以不能声称当前环境使用这些 patch。zero padding 对 loss 的中性是假设，不是本次验证结果。

learner 是旧版 Policy/Trainer 组合：IL/CC 包装 PPO/A2C policy/loss；Joint Q 自己实现 `[B,T,n_agents]` loss、动作 mask、mixer、optimizer 和 `learn_on_batch`。其 execution plan 是 bulk-sync rollouts → store replay → replay → `before_learn_on_batch` → TrainOneStep → target update，并以 1:1 round-robin 交替。Episode replay 保存完整 episode；patched LocalReplayBuffer 先复制 batch，按 policy 与 sequence/burn-in 切片，返回 MultiAgentBatch，并声明 Ray actor。copy、padding、每 policy sampling、priority update 和 actor/object-store 交互都是潜在成本，实际 replay capacity、RSS 和传输未测。

默认资源配置是 `local_mode=True`、1 worker、driver 1 GPU、每 worker 1 CPU/0 GPU；runner 明确把 worker 数/GPU 字段送入 Tune，但没有在对应 `run_config` 字典中显式写 `num_cpus_per_worker`，是否由更上层 merge 保留未运行时核验。local_mode、资源字段和 device 分支是 O；worker 是否独立进程、环境是否重建、SampleBatch 如何经对象存储、权重如何广播都是 RLlib/Ray D/U。依赖清单锁定 Ray/RLlib 1.8.0、Torch 1.9.0、Gym 0.20.0 等旧版本，兼容性没有在本机验证。

已新增 32 个真实关键目录的本地 `AGENTS.md` 导航，并将每个全文备份到 `reports/MARLlib/agents-overlays/`；索引是 `AGENTS_INDEX.json`。新增内容仅导航与报告，MARLlib 源文件未改。早期相对路径误写落到 HMASD 共享工作区，Root 已恢复原 tracked `AGENTS.md`/ `tests/AGENTS.md` 并隔离误写物；这项操作写入了报告局限，但没有删除证据或改历史。

建议把本报告作为“工程集成机制与未测成本”输入：若要形成科学性能证据，另行锁定相同 commit、依赖、agent 数、episode limit、mapping、序列长度、worker/GPU、seed 和 budget，并按统一协议采集 step/batch wall time、peak RSS、序列化/object-store 指标。toy 超过 45 分钟或 UAV 超过 12 小时的工程查证不能放宽科学要求，也不能支持跨任务速度比较。MARLlib 以 MIT 授权发布，报告保留许可证信息且没有大片复制代码。
