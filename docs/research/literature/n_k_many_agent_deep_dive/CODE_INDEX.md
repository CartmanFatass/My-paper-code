# Code Index and Inspection Status

代码于 2026-07-17 从论文给出的官方仓库检出。所有仓库均位于本目录的 `code/`，由主项目 `.gitignore` 排除；它们是只读研究快照，不是 vendored dependency。本轮没有安装依赖、执行训练或把外部代码并入 HMASD。

## 已下载代码

| ID | 本地目录 | 官方仓库 | 分支 / 快照 | 检出范围 | 保留原因 |
|---|---|---|---|---|---|
| P01 | [`code/P01_ACE_async_mappo`](code/P01_ACE_async_mappo) | [yang-xy20/async_mappo](https://github.com/yang-xy20/async_mappo) | `main` / `038058b` | shallow full checkout | per-agent readiness、异步 buffer、掉队测试 |
| P02 | [`code/P02_ACAC`](code/P02_ACAC) | [LGAI-Research/acac](https://github.com/LGAI-Research/acac) | `main` / `5ca6afb` | shallow full checkout | duration-correct macro GAE 与 agent-centric history |
| P03 | [`code/P03_InforMARL`](code/P03_InforMARL) | [nsidn98/InforMARL](https://github.com/nsidn98/InforMARL) | `main` / `7d3c42a` | shallow full checkout | variable-size GNN 与固定维 pooling |
| P04 | [`code/P04_Sable_Mava`](code/P04_Sable_Mava) | [instadeepai/Mava](https://github.com/instadeepai/Mava) | `develop` / `e1cc61d` | sparse checkout: Sable networks/system/config | many-agent retention 容量对照 |
| P05 | [`code/P05_ExpoComm`](code/P05_ExpoComm) | [LXXXXR/ExpoComm](https://github.com/LXXXXR/ExpoComm) | `master` / `25dc972` | shallow full checkout | 指数稀疏拓扑和 one-peer 调度 |
| P07 | [`code/P07_CTMARL`](code/P07_CTMARL) | [Wangxuefeng1024/Continuous-Time-Value-Iteration-for-Multi-Agent-Reinforcement-Learning](https://github.com/Wangxuefeng1024/Continuous-Time-Value-Iteration-for-Multi-Agent-Reinforcement-Learning) | `main` / `b3071ae` | shallow full checkout | `gamma^dt`、dt-conditioned policy 和不规则间隔对照 |

短 Git revision 仅用于标识本轮阅读快照，不是内容校验和。

## 关键实现定位

### P01 ACE

- `onpolicy/utils/util.py::AsynchControl`：每 `(env, agent)` 独立周期与 readiness；
- `onpolicy/runner/shared/gridworld_runner.py`：周期奖励累积和 active-agent 插入；
- `onpolicy/utils/shared_buffer.py`：per-agent `update_step`、异步 mask、return；
- `onpolicy/algorithms/utils/invariant.py`：team-size-invariant 关系编码；
- `onpolicy/algorithms/utils/mix.py`：仍显式依赖固定 `num_agents`。

结论：执行壳有启发；return 未保存 duration，buffer 仍固定形状，且异步 mask 赋值路径需先复核。

### P02 ACAC

- `acac/acac_marl/cores/acac/learner_acac.py`：宏事件抽取、joint advantage 与 ACAC update；
- `learner_acac_micro_gae.py` / `learner_acac_vanilla.py`：时间语义消融对照；
- `memory.py`：episode batch 与有效事件组织；
- `models.py`：agent history encoder 和 attention critic；
- `envs_runner.py`：固定 `n_agent` 异步宏动作 rollout。

结论：本轮最值得迁移语义的代码；只参考 `_squeeze_cen_exp`、`_get_gae` 一类事件/折扣逻辑，不能复制固定 roster 外壳。

### P03 InforMARL

- `onpolicy/algorithms/utils/gnn.py`：`TransformerConv`、节点 batch 与 pooling；
- `onpolicy/algorithms/graph_actor_critic.py`：actor focal aggregation 与 critic global aggregation；
- `onpolicy/utils/graph_buffer.py`：图观测存储；
- `onpolicy/runner/shared/base_runner.py`：按当前配置构造固定 agent/node 数。

结论：适合提取 active-set GNN 和 full-set reference；runner 不支持 episode 内 roster 变化。

### P04 Sable / Mava

- `mava/networks/retention.py`：parallel/recurrent/chunkwise retention；
- `mava/networks/sable_network.py`：Sable encoder/decoder；
- `mava/networks/utils/sable/`：固定 `n_agents` 的 mask、decay 与 reshape；
- `mava/systems/sable/`：learner/executor 系统。

结论：只保留为固定 `M` slot coordinator 的未来容量参考；当前 `T*N` 序列不具备动态 roster 语义。

### P05 ExpoComm

- `src/controllers/ExpoComm_controller.py::get_exp_neighbors`：指数偏移和 one-peer 邻居；
- `src/modules/agents/ExpoComm_agent.py`：消息记忆、聚合和辅助目标；
- `src/config/algs/`、`src/config/exp/`：不同团队规模的固定配置。

结论：可提取 bounded candidate topology；需替换固定循环 ID、同步 `t` 并增加 live-graph repair。

### P07 CT-MARL

- `algo/multi_main.py::compute_discounted_returns`：`reward*dt + gamma^dt*return`；
- `algo/multi_main.py`：全局随机 `delta_ts` rollout；
- `algo/vip/agent.py::choose_action`：所有 agent 共享 dt 并将其加入 policy input；
- `algo/vip/agent.py::target_vgi_training`：`gamma^dt` 的 VGI target；
- `algo/vip/network.py`：固定 `N` 联合状态的 value/dynamics/reward 网络。

结论：只提取 duration-aware invariant。源码中 return shape 与 target-list update 等接口存在可复核问题，不作为直接依赖。

## 未下载代码

| ID | 官方仓库 | 决策 |
|---|---|---|
| P06 Safe-M3-UCRL | [mjusup1501/safe-m3-ucrl](https://github.com/mjusup1501/safe-m3-ucrl) | 纯 mean-field / model-based safety 栈与当前 PPO、有限 open roster 不匹配；论文已足够完成边界判断 |
| P08 IARO | [raulsteleac/IARO](https://github.com/raulsteleac/IARO) | 全队同步 option contract 与 per-agent `T_i` 相反；相对表示启发无需引入整套 option discovery |

## 使用约束

若以后迁移任何片段，应重新在 HMASD 内独立实现并用当前 tensor shape、mask、gradient/detach、clock、SMDP、PPO ratio、checkpoint 与 collector contract 逐项证明。外部仓库的论文实验结果和原型可运行性不能替代这些证明。
