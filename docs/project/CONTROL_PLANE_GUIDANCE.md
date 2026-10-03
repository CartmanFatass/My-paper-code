# HMASD 控制面维护说明

本页解释分工与维护取舍，不维护另一套运行规则，也不是每次任务的必读材料。
文件关系见 [MAP](CONTROL_PLANE_MAP.md)；权限见 [宪法](OPERATING_CONSTITUTION.md)，
当前安排见 [RESEARCH](../research/RESEARCH.md)，具体做法见对应 skill。

## 保留角色上下文，减少多处维护

角色正文必须独立说清身份、责任、自主范围、输入、交付、返回与异议路径。
暂停优先、同请求对账、DM 自行发表、Critic 独立上下文等决定首次行动的边界，
可以在相关入口短重复；完整方法只在负责该任务的 skill 中维护。
不要把 DM 缩成执行者，或把 Critic 缩成一句“请独立思考”。

| 改动内容 | 应当修改的源 |
| --- | --- |
| 权限或角色关系 | owner 对宪法的修订；其他说明跟随，不自行制造规则 |
| 某角色负责什么、向谁返回 | 对应角色正文；Root 的协调职责在 loop-dispatch |
| 具体科学判断方法 | scientific-tools；角色保留使用它的责任与触发条件 |
| 代码、发表、执行与存储步骤 | research-engineering；原生特殊步骤留在适配说明 |
| 当前人数、题目、地址或暂停 | RESEARCH；不要写进手册、角色或配置注释成为永久规则 |
| Claude 原生模型／工具 | Claude frontmatter；生成脚本不能覆盖它，Oracle 全文独立维护 |
| 文献检索 | scientific-tools 的 local-literature reference；入口保留库名和证据提醒 |

主会话不自动加载同名子角色。直接 DM 必须实际读取 DM 正文；注册或标题不能证明
模型、权限、技能或角色已生效。原生子 DM、独立 App 会话和 Claude peer 的联系路径不同，
不能合并成笼统的“向 Root 汇报”或“禁止通信”。Pro 不继承本地上下文：问题作者按
[pinned context 方法](../../.agents/skills/hmasd-pro-research-prompt-author/references/pro-reading-context.md)
提供具体来源、版本、支持与反对证据。

## 修改与核验

先检查来源和消费者，再缩写；具体任务只读取相关段落，不沿历史链接递归拼接当前义务。
沿用现有文件、记录与生成链。若某项迁移只把同一大段复制到另一本手册，并没有减少维护。
普通文档自检；执行行为变化按工程方法检查和审查。检查生成副本时用
`tools/publish_claude_control.py --check`，必要的源码配置检查用
`tools/inspect_codex_control.py`。两者都不证明 live runtime 已加载。

对角色／方法实质精简，检查典型情形下责任与行动是否保全：暂停中的状态询问、
独立 DM 发表、Critic 提出重大异议、接受状态不确定、原生子 DM 等待、跨主机接回句柄。
这是改动的开发检查，不增加科研每批检查、回执、审批或固定审查次数。
保留模型／权限／工具设置；不要为文字去重改变执行行为。

RESEARCH 维护判断与直接证据入口，NOTES 保存完整经过。只退役已完成复盘或实质被替代计划；
未决意见、有效约束、接受操作和未读结果仍能从当前页找到。普通编辑用 Git 历史。
启动器读取 RESEARCH 的唯一 Owner pause 标记、Active 表以及 direction/state/lead；
精简不能改变这些解析值。保留仍被消费的锚点和冻结引用，不用旧整页覆盖并发新结果。

## 历史与生效边界

此前迁移的设计与来源保留在 [原迁移计划](../archive/project/CONTROL_PLANE_MIGRATION_PLAN_20260916.md)、
[采用记录](../Claude_docs/changes/2026-09-16-constitution-adoption.md)和 Git 历史。
历史规则不因链接仍存在而恢复有效。新材料替代的是现行重复说明，原实验和评审保持原义。
运行会话在相关工作安全边界读取变化，不要求广播、采用回执或为重载重复 Send／实验。
发现某项来源不明的冲突就指出具体条款；不要通过删句子静默选择新的权限含义。
