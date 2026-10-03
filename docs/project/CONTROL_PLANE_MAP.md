# HMASD 控制面总览

描述性导航，不是权限来源或必读 preload。当前 owner 指示与
[宪法](OPERATING_CONSTITUTION.md)决定权限；当前分工和暂停见 [RESEARCH](../research/RESEARCH.md)。
源码一致、生成一致与实际会话加载是三件事。

## 权威、维护源与生成链

| 内容 | 唯一维护源／入口 | 消费者 |
| --- | --- | --- |
| 治理与角色关系 | OPERATING_CONSTITUTION.md | 入口、角色、方法按任务读取 |
| 当前背景、状态、计划、联系 | docs/research/RESEARCH.md | Root、DM、启动器；证据原文在 NOTES/CLAIM/runs |
| 会话入口 | AGENTS.md；CLAUDE.md 为原生适配 | 主会话；直接 DM 显式读取 DM 正文 |
| Root 方法 | .agents/skills/hmasd-loop-dispatch/SKILL.md | Root；实际职责交接时按需读取 |
| DM 职责／辅助角色 | .codex/agents/*.toml | Codex 注册角色；主会话读取职责不改变其模型／权限 |
| 科学／工程／协作／Pro 方法 | .agents/skills/hmasd-*/ | 对应任务；references 按具体需要读取 |
| Claude 生成正文 | tools/publish_claude_control.py | .claude/skills；共享角色 → .claude/agents；DM → research-hub |
| Claude 原生设置与 Oracle | .claude/agents 的 frontmatter；hmasd-oracle.md 全文 | 独立维护，不由 Codex 设置推断实际值 |
| Pi／OMP 入口 | AGENTS 的 Pi 段；.omp/APPEND_SYSTEM.md | 实际 native 工具和返回路径 |
| 节点／解释器／supervisor | .codex/hmasd-compute.toml | 工程、启动器与解释器查询工具 |
| Pro provider／部署参数 | .codex/hmasd-transport.toml | 适用的 Jev／Agentify 方法；配置不是 Send 权限 |

生成器复制完整共享正文并追加原生适配，不靠自然语言句子替换来迁移规则。
`--check` 检查差异和额外生成文件，不删除孤儿，不证明真实会话重载，也不是启动门禁。
两种 Pro transport 是程序方法，不是子代理角色；Transport、Monitor 和旧 clerks 不注册。

## 按需要进入

| 问题 | 直接入口 |
| --- | --- |
| Root 选题、派发、恢复子 DM | [loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md) |
| DM 自主范围、交付与异议 | [DM 正文](../../.codex/agents/hmasd-direction-manager.toml)；宪法 §2 |
| 假说、比较、完整判读与共享认识 | [scientific-tools](../../.agents/skills/hmasd-scientific-tools/SKILL.md) |
| 实现、检查、发表、准入、同句柄观察、清理 | [engineering](../../.agents/skills/hmasd-research-engineering/SKILL.md) |
| Claude–Root 对等联系与共享写入 | [peer-collaboration](../../.agents/skills/hmasd-peer-collaboration/SKILL.md) |
| Pro 的固定问题与完整答案 | [prompt-author](../../.agents/skills/hmasd-pro-research-prompt-author/SKILL.md)，再选 Jev／Agentify |
| 项目综合与计划退役 | [portfolio-task](../../.agents/skills/hmasd-portfolio-task/SKILL.md) |
| 主机／运行时真正交接 | [HOST_AND_RUNTIME_SWITCHING](HOST_AND_RUNTIME_SWITCHING.md) |
| 为什么如此划分、维护时怎样保留上下文 | [GUIDANCE](CONTROL_PLANE_GUIDANCE.md) |

历史规格、原始评审与冻结对象通过 [docs index](../README.md) 按需取证。
旧操作保留原 key、输入和证据，不因方法更新重发、重启或改绑。
