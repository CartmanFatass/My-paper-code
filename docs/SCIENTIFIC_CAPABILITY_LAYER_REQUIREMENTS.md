# HMASD 科研能力与仪器层需求

状态：需求基线，尚未授权任何具体 skill、依赖安装或工具调用。

本文件定义 HMASD 第三层“能力与仪器层”需要提供什么，不定义 Codex task
拓扑、跨 session 路由、Workflow-Clerk 状态转换或新的批准机制。系统分层背景见
`docs/DISTRIBUTED_RESEARCH_COGNITION_WORKING_NOTES.md`。

## 1. 目标

第三层应让 EM、CM 和它们的 bounded leaf 能够使用专业工具取得独立、可复现的
观测，减少研究判断仅依赖模型内部推理的问题。

能力调用遵循以下关系：

```text
EM/CM 冻结问题、输入与判断标准
    -> leaf 使用最小充分仪器取得观测
    -> 产生可复现 evidence artifact
    -> EM/CM 解释证据并更新各自长期认知对象
```

工具及其 skill 提供方法、接口和防错知识。工具输出不是 scientific authority，
skill 也不得创建 task、调度 participant、改变方向 lifecycle 或增加审批 gate。

## 2. 环境需求

建立独立、版本锁定的科研工具环境；暂定名称为 `hmasd-science-tools`。最终 Python
和包版本由实际依赖求解决定，不要求兼容当前 `hmasd-amd-cpu` 环境的旧版本。

环境必须满足：

- 不静默升级或修改 HMASD 主运行环境；
- 记录 Python、包版本、平台和必要的外部可执行程序；
- 提供可重复创建的 lock/manifest；
- 工具调用使用明确解释器或入口，不依赖调用者当前激活的环境；
- GPU、PufferLib、PyG extension 等强平台耦合组件发生冲突时允许使用独立 adapter
  环境，不为了单一环境形式改变科学或数值语义；
- skill 不自行安装依赖。缺少能力时报告 capability unavailable，由所属 CM 决定
  是否实现或配置；
- 网络检索、付费 provider 和其他 external effect 仍遵守项目已有的外部操作边界。

## 3. 需要保留的能力

以下上游材料的方法主体符合需求，只需进行轻量 HMASD 边界和环境适配：

| 上游素材 | HMASD 保留能力 | 主要使用者 |
| --- | --- | --- |
| `scientific-critical-thinking` | claim ceiling、反证、替代解释、validity threats、决定性缺失证据 | EM / Research Critic |
| `paper-lookup` | 有界检索、确定性分页、去重、identifier/locator 和检索 provenance | EM / Research Scout |
| `networkx` | 科研图结构、拓扑、连通性、路径和方向重叠分析 | EM/CM 的 bounded leaf |

必要边界：删除临床 GRADE 等不适用层级；检索不强制多库；NetworkX 不用于工作流
状态、task registry、Portfolio 自动评分或方向 authority。

## 4. 需要实质适配的能力

| 上游素材 | 目标能力 | HMASD/MARL 适配重点 |
| --- | --- | --- |
| `experimental-design` | MARL 实验设计 | seed/config/map 作为独立重复，CRN、paired design、预算、停止条件；区分 correctness、performance、scientific evidence |
| `statistical-analysis` | MARL 结果推断 | 层级依赖、seed-level estimand、effect size、bootstrap/hierarchical interval、failed runs、multiplicity 和 sensitivity |
| `scientific-visualization` | 科学诊断与结果图 | 冻结 source data、transform、单位、missing/censored、estimator 和 uncertainty；图形审计不替代科学判断 |
| `stable-baselines3` | 单智能体 reference/differential probe | termination/truncation、VecEnv、normalization、checkpoint 和最小 baseline；不作为 MARL 主基座 |
| `torch-geometric` | 图学习机制 probe | node/edge schema、方向、self-loop、时间轴、batch 轴和 dense reference differential test |
| `pufferlib` | MARL 环境与性能 probe | env contract、agent-slot/batch shape、deterministic trace、fixed-work vectorization、seed separation 和 checkpoint provenance；框架本体保持可选 |

这些能力不得被合并成少数宽泛 skill。是否需要独立 skill，应在具体能力的失败基线、
可重复任务和工具接口明确之后逐项决定。

## 5. 当前不激活的能力

| 上游素材 | 当前决定 | 可保留内容 |
| --- | --- | --- |
| `literature-review` | 不作为常驻 skill | 正式系统综述时参考其筛选、检索记录和主题综合方法 |
| `research-lookup` | 不启用 | provider-neutral 的 query ledger、identifier 去重和 contradictory evidence |
| `scientific-writing` | 论文阶段前不启用 | claim-evidence locator 与数值/方法一致性检查 |

不引入强制三数据库、固定文献数量、PRISMA、AI 图片、投稿状态、作者审批、稿件
registry、provider router 或由启发式脚本生成的自动 verified/quality 标签。

## 6. 尚缺能力

当前上游集合没有完整覆盖以下需求：

- Mathematica、SymPy、SMT/solver 等符号数学与定理辅助验证；
- 数值高精度 reference、property/invariant 和 differential verification；
- 本地 MARL、RL、DL 开源仓库的实现定位与对照；
- profiler、内存峰值、批处理吞吐和扩展性测量；
- UAV 仿真与真实实验的 scenario、hardware、checkpoint 和 runtime provenance；
- 按“证据问题类型”检索能力的 capability catalog。

## 7. 最小 evidence 输出

不同工具可以产生不同 artifact，但每次有界仪器操作至少应保留：

- frozen objective/input；
- tool、version 和运行平台；
- exact invocation 或等价的可复现操作描述；
- seed、bounds、expected count/shape 等适用输入约束；
- artifact locator；
- core observation；
- assumptions、limitations 和失败信息；
- 对所属 scientific claim 或 engineering judgment 的影响。

这是第三层工具证据的共同内容，不是新的跨 session envelope、transport schema、
状态机或长期 raw-output 仓库。

## 8. 角色边界

- EM 冻结科学问题、discriminator、claim ceiling，并解释科学证据。
- CM 冻结可执行 contract、adapter、数值/批处理语义和工程证据。
- leaf 完成一次 bounded instrument operation，返回观测，不再 delegate。
- Portfolio 只请求和消费会改变投资决策的证据摘要，不直接操作工具。
- Workflow-Clerk 只转递既有 assignment/return，不解释工具内部语义。
- Experiment Operator 仍只运行 CM 冻结的 result-bearing command；普通检索、静态
  数学检查或分析 probe 不因属于第三层而自动变成 Operator 工作。

## 9. 验收标准

单项能力进入项目激活 skill/tool 集前必须证明：

1. 有一个真实 HMASD 问题需要该能力，且无能力基线暴露了明确缺口；
2. 适用问题、输入、输出、限制和角色解释责任清楚；
3. 使用独立环境可重复运行，并保留版本和 artifact provenance；
4. 至少一个真实或代表性案例证明工具观测能改变或约束具体判断；
5. 工具 pass 不被表述为 scientific acceptance 或 authority；
6. 不复制 workflow、Clerk、task、Git、批准或方向 lifecycle 规则；
7. 不自动安装依赖、不隐式执行外部操作、不把 raw provider 输出写入长期认知面；
8. skill 的触发范围经过独立行为测试，未表现为宽泛自动触发或上下文污染。

## 10. 已停用的早期实现

以下两个过早合并能力面的 skill 已从项目 `.agents/skills/` 移出，暂存于
`C:/Projects/skill_backup/`：

- `hmasd-marl-experiment-design`
- `hmasd-marl-result-analysis`

它们仅作为后续需求追溯素材，不是当前项目指令，也不得被 participant 自动加载。
