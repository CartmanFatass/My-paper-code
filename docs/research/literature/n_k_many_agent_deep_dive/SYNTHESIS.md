# Cross-Paper Synthesis

## 核心结论

有明确的 many-agent 研究，但 **many-agent scalability 不等于运行时 variable `N`**。本轮八篇中：

- Sable、ExpoComm、Safe-M3-UCRL 直接研究大规模群体；
- InforMARL、ExpoComm、IARO 展示某种跨团队规模复用或相对模式一致性；
- ACE 展示测试时机器人丢失；
- 没有一篇完整实现 episode 内 leave、join、rejoin、survivor hidden continuity 和 on-policy roster semantics；
- ACAC 是 per-agent 异步 `T_i` / SMDP credit 最直接的参考，但 roster 固定。

因此，HMASD 不能选一篇作为完整 successor。最有价值的路线是组合四个彼此独立的最小机制，并严格分阶段验证。

## 证据矩阵

`✓` 表示论文与代码有直接支持；`△` 表示只支持相邻问题或需要关键改造；`—` 表示没有支持。

| ID | many-agent 规模 | 跨固定配置 `N` | episode 内变 `N` | 每智能体不同 `T_i` | 对 HMASD 的角色 |
|---|---:|---:|---:|---:|---|
| P01 ACE | 小规模 | △ 共享策略/掉队测试 | △ 仅 mask/丢失压力，固定容量 | △ 执行异步，return 不正确 | 事件执行壳 + dropout diagnostic |
| P02 ACAC | 小规模 | — | — | ✓ `gamma^Delta t` + 宏事件 GAE | 变 `k` 的主实现参考 |
| P03 InforMARL | 中等 | ✓ 3/7/10 等配置 | — | — | 变 `N` 表示层主参考 |
| P04 Sable | ✓ 1,000+ | △ 每个配置重建固定序列 | — | — | coordinator 容量/显存基线 |
| P05 ExpoComm | ✓ 20–100 | ✓ 重建指数图后迁移 | — | — | bounded sparse topology 候选 |
| P06 Safe-M3-UCRL | ✓ 无限总体模型 | △ mean-field 极限 | — | — | population-field / safety null |
| P07 CT-MARL | 最多 6 | — | — | △ 全员共享随机 `Delta t` | duration-aware 语义 diagnostic |
| P08 IARO | 小规模 | △ 3→4 相对模式可视化 | — | —（全队同步 option） | 同步失败模式 + 相对场特征 |

## 精筛排序

### 对解绑 `N` 的启发

1. **InforMARL**：共享 GNN + active-set 聚合最适合作为 `full_set_reference` 和局部场骨架。
2. **ACE**：提供真实的测试时掉队场景，但数据结构仍固定；适合定义 survivor robustness 测试，不适合直接复用 roster 实现。
3. **ExpoComm**：提供随 `N` 可重建、边数有界的小直径候选拓扑；必须补 live-roster 重建和断连修复。
4. **Field-Slot + Safe-M3-UCRL 对照**：population summary 可扩展，但 pure mean-field 会丢失绝对人数和关键个体，反向支持 slot mass、`log(1+N)` 与 exact residual。
5. **Sable**：只在 coordinator 容量成为瓶颈后作为对照，不回答 open roster。

### 对解绑 `k / T_i` 的启发

1. **ACAC**：真实微时间的 `gamma` 与宏事件次数的 `lambda` 分离，是最接近 HMASD SMDP contract 的实现。
2. **ACE**：每智能体 readiness 和周期奖励累积可复用为事件执行壳，但 return 必须重写。
3. **CT-MARL**：证明 duration 必须进入价值语义和压力测试；共享 `Delta t`、HJB/VGI 不迁移。
4. **IARO**：全员投票和共同终止是有用的负面对照，说明共享 barrier 会让不同技能周期重新耦合。

## 最小可组合架构

下面是从论文中得到的机制组合，不是已批准实现：

```text
active roster / member events
  -> active-only generic tokens
  -> sparse local graph (InforMARL)
  -> fixed-M population slots + mass + log(1+N) (Field-Slot)
  -> bounded critical exact residual (live sparse graph / ExpoComm candidate source)
  -> fixed-length deterministic slot coordinator
  -> per-agent action decoder and survivor recurrent state

shared base check clock k0
  -> per-agent readiness / realized duration T_i (ACE execution idea)
  -> agent-centric valid event histories (ACAC)
  -> duration-correct reward, bootstrap and GAE (ACAC)
```

这套组合必须保留以下边界：

- roster 层：稳定成员键、join 初始化、leave terminal/bootstrap、rejoin 是新实体还是续接实体；
- 表示层：只聚合 active tokens，置换/填充等价，slot mass 与绝对 `N` 可见，关键成员不会被平均掉；
- collector：每个 agent 的事件 owner、行为 log-prob、value snapshot、`T_i` 和 reward interval 一致；
- SMDP：`R_e = sum_r gamma^r reward_(t+r)`，bootstrap 为 `gamma^T_i V(s_next)`；
- PPO：只对真实决策事件形成 ratio，mask 不制造伪事件，detach/gradient 边界与 behavior policy 一致；
- 复杂度：邻域候选本身必须稀疏，不能先形成全 `N^2` pair score 再 Top-L。

## 与 Field-Slot 候选的具体关系

| Field-Slot 部件 | 最相关论文 | 可借鉴点 | 必须新增的 HMASD 约束 |
|---|---|---|---|
| `full_set_reference` | InforMARL | 局部 TransformerConv、固定维 pooling | active-only dynamic roster |
| global slots | Safe-M3-UCRL、IARO | population field、相对 dispersion | 多槽、mass、`log(1+N)`，不加 intrinsic reward |
| local field | InforMARL | 物理/感知稀疏图 | 有界邻居生成成本 |
| critical residual | ExpoComm | 有界、小直径候选拓扑 | 关键性判据、掉队连通修复 |
| slot coordinator | Sable | 固定长度序列的容量效率 | 只在固定 `M` 后比较，不展平 `T*N` |
| variable time | ACAC、ACE | event history、readiness、SMDP GAE | 每 agent `T_i` 与 PPO owner contract |

IARO 的单 Fermat center 不能替代多槽：多模态团队可能围绕一个中心发生 aliasing。其 feature-wise spreadness 更适合作为 slot diagnostics，而不是奖励或新技能系统。

## 推荐因果顺序

按照一个问题一条因果边，且不在首轮同时激活 `N` 与 `k`：

1. **N-representation gate**：沿 Field-Slot README，用 constructive oracle 比较 InforMARL 式 `full_set_reference` 与 `hybrid_field_slot`；只回答表示充分性、稀有成员、反协调和复杂度。
2. **N-learning gate**：表示门通过后，在固定 `N` 下比较两种表示的外部回报可学习性；避免把 open-roster 和优化 transport 混在一起。
3. **N-roster gate**：仅加入外生 episode 内 leave/join/rejoin，检查 survivor hidden continuity、成员 event mask 和策略输出连续性。
4. **k-semantics gate**：另在固定 `N` 下，用可解析短轨迹验证 ACAC 式 duration-correct return/GAE。
5. **k-robustness gate**：给定外生不同 `T_i`，测试 seen/unseen duration；此时仍不学习 termination。
6. **joint gate**：只有两条线各自通过后，才组合 dynamic roster 与异质 `T_i`；充电离场、任务规模变化和掉队才成为联合压力情景。

## 本轮不建议吸收

- ACE 当前标准一步 return 和固定 `num_agents` buffer；
- ACAC 固定 `n_agent` centralized shell；
- Sable 的 `T*N` 固定顺序展平；
- ExpoComm 的永久循环 ID、同步 one-peer 时钟和默认辅助目标；
- Safe-M3-UCRL 的无限同质 representative-agent 假设与整套 model-based safe optimizer；
- CT-MARL 的 PINN/HJB/VGI 整栈；
- IARO 的全员 joint option、共同终止和 eigenvector intrinsic reward。

## 最终判断

本轮最值得实际读代码并保留的四条线是：**ACAC、InforMARL、ACE、ExpoComm**。Sable 和 CT-MARL 代码保留为容量/时间语义对照。Safe-M3-UCRL 与 IARO 的论文已足以划定边界，当前不值得把完整代码引入本地研究面。

该判断只完成候选精筛，不改变当前项目路线，也不授权实现或实验。
