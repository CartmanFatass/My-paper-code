# Codex 原生 sibling 通信

## Current route — OWNER_DIRECT 2026-09-06

The native tracker is retired. DM/CM -> independent Luna/low app task -> research Root -> native DM/CM. See `.codex/hmasd-monitor.toml` and `docs/project/EXPERIMENT_MONITOR.md`. Native subagents can dispatch directly to app tasks (owner confirmed). Root heartbeat is removed; the monitor owns its heartbeat. Current assigned live/unknown handles: none. Historical handles and capability restrictions below are preserved evidence, not current assignments or routing rules.

## Historical record

验证日期：2026-09-04。适用范围：本项目当前 Codex Desktop 原生 multi-agent 任务树。

## 23:41Z 恢复后的实际能力

新 Root `01a06ec7-fd64-7281-9bc1-fc42ed53a2ca` 已成功按名字创建实际 custom role
`hmasd-experiment-tracker`：`/root/tracker_tl_experiments`，配置 Terra/low。
tracker 报告原生 `send_message` 和 `followup_task` 已暴露；它与
`/root/dm_amx_fsd_continue` 使用 `tracker-resume-fsd-20260904-01` 完成直接双向 ACK，
两端分别确认收件，Root 没有转发。角色发现和双向收件均已验证。
本轮尚未把 tracker 的 idle wake 单独记为实测；旧 DM 间的 idle wake 证据仍见下表。
所有者将该专用角色指定为默认实验追踪及通知节点；具体当前工作树和恢复约定见
[恢复记录](../research/portfolio/decisions/2026-09-04-resume-with-default-tracker.md)。
下文关于旧 runtime unknown agent_type 和临时 Luna 缺少 outbound 工具的文字保留为历史，
不代表新 Terra tracker 的当前状态。

**可以直接通信。** 同一个 Root 下的 DM、tracker，以及嵌套的 CM，可以通过原生
`collaboration` 工具联系任务树中的其他 agent。接收方用 canonical agent name 寻址，
不需要 Root 转发。这里的 sibling 是同树 agent 之间的关系，没有一个另外叫 `sibling`
的工具，也不使用 Codex 侧边栏任务的消息接口。

## 实测依据

以下是两端分别报告的实际原生调用及收件结果，不是仅凭配置推断：

| 验证 | 发送方 → 接收方 | 观察到的结果 |
| --- | --- | --- |
| 运行中直接收发 | `/root/dm_amx_fsd_resume` → `/root/dm_amx_crto_resume` → FSD | FSD 用 `collaboration.send_message` 发出 `sibling-doc-20260904-fsd-crto-01`；CRTO 收到并用同一工具直接 ACK；FSD 确认收到。两次调用均被接受。 |
| 休眠 agent 唤醒 | CRTO → 已完成当前 turn 的 FSD → CRTO | CRTO 用 `collaboration.followup_task` 发送 `sibling-wake-20260904-crto-fsd-02`；FSD 被唤醒，用 `send_message` 直接 ACK；CRTO 确认收到。 |

两端均为本任务树既有的 `hmasd-direction-manager` custom agents。Root 只提出验证任务，
没有转发测试消息或 ACK；验证没有操作实验、改变科学状态或编辑证据文件。

## 调用方式

原生工具在 assistant 的顶层工具命名空间中调用。不要放进 `functions.exec`，也不要写成
`tools.collaboration.*`。`ALL_TOOLS` 列的是该编排工具内可调用的方法，本来就不包含原生
`collaboration`；在那里搜不到不代表原生工具不存在。

| 工具 | 用途 | 对休眠 agent 的影响 |
| --- | --- | --- |
| `collaboration.send_message` | 给现有 agent 发送观察、ACK 或补充信息 | 不触发新的 turn。 |
| `collaboration.followup_task` | 分派需要继续执行的任务，包括实验完成后的 intake | 接收方 idle 时触发 turn；运行中则投递补充任务。 |
| `collaboration.list_agents` | 查看当前任务树的 canonical name 和状态 | 只读；不反复轮询。 |
| `collaboration.wait_agent` | 等待任务树消息或完成通知 | 返回哪些 agent 有更新；不是实验进程 supervisor。 |

使用已发现的完整路径。例如，tracker 向另一个 Root 子节点 DM 发消息时，目标是
`/root/dm_amx_fsd_resume`。在 tracker 内写 `dm_amx_fsd_resume` 可能按 tracker 自己的
相对路径解析。嵌套 CM 也应使用对方的完整路径。不要把 app 的 UUID task ID、agent 的
显示昵称、SSH PID 或远端 `agent-task` 名当成 canonical name。

给正在工作的 DM 发观察，顶层调用 `collaboration.send_message`，参数示例：

```json
{
  "target": "/root/dm_amx_fsd_resume",
  "message": "已观察到你委托的同一 task 终止，退出码为 0；具体时间、结果路径和日志见跟踪表。请安排 CM 核对后 intake。"
}
```

需要唤醒 idle tracker 接管已接受的进程，顶层调用 `collaboration.followup_task`：

```json
{
  "target": "/root/tracker_lxh_experiments",
  "message": "请接管已接受的进程。DM、节点、task、SHA、cwd、日志、receipt 和观察时间见此 run record；只观察同一 handle，终止后直接提醒我。"
}
```

以上名字取自此次实测树；恢复到新 Root 时要重新读取 Portfolio/实际任务树中的名字。
工具接受发送和收件人实际 ACK 是两种事实，记录时应分开。ACK 用于确认观察责任已接管，
不成为实验 admission 条件。`followup_task` 的目标须为现有非 Root agent；给 Root 的恢复
请求可通过普通子 agent 回复报告，不创建额外侧边栏任务。

## 专用 experiment tracker

定义在 [hmasd-experiment-tracker.toml](../../.codex/agents/hmasd-experiment-tracker.toml)，
`name = "hmasd-experiment-tracker"`，固定 `gpt-5.6-terra` / `low`，并显式启用
`agents.enabled`。项目 config 保留相应 role 声明。Root 创建一个与 DMs 同层的实例，
公布其 canonical name、独立 worktree 和跟踪文档；各 DM 按需直接发派任务。

“持有进程”指持有可恢复的 supervisor/进程身份及观察责任。实验仍由原来的 detached
supervisor 执行，不依赖 tracker 的 turn 存活。tracker 记录、观察、提醒；CM/Operator
负责启动、收集、核对与修复；DM 负责科学 intake 和下一步决定。进程退出码 0 不等于
科学结果有效。

| 场景 | 接管事实 | 观察及终止确认 |
| --- | --- | --- |
| 远端 | 执行节点、SSH alias、接受的 `agent-task` 名、精确 SHA/cwd、远端日志/输出/receipt | 按 `.codex/hmasd-compute.toml` 读取该节点的 `agent-task status` 和有限 `logs`；以 supervisor 的状态/退出记录为据。SSH 会话退出不是实验退出。 |
| 本地 detached | 主机、supervisor 或 PID **及启动时间/命令身份**、SHA/cwd、绝对日志/输出/receipt、已有退出记录 | 查指定进程并有限读取日志；结合原启动方的退出证据。PID 消失或被复用不能推断成功。 |
| 本地工具 session | 启动方和确切可访问的 session、日志/退出见证 | 仅在该 runtime 实际允许访问时观察。单独传一个私有 session ID 不会转移工具访问权；否则由 CM 提供已有 detached/log/exit 见证或一次有界观察。 |

当前远端只读命令模式如下；`<accepted-name>` 必须换成已接受并记录的真实名字：

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task status <accepted-name>
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node /usr/local/bin/agent-task logs <accepted-name> 40
```

同一 `(node, accepted handle)` 的重复交接更新同一记录；换 observer 不重启实验。
失联记为未知，安静的日志不直接判定为 hang。短任务较早检查，健康长任务退避观察；
有意义的终止、失去观察或约定提醒只通知一次。现有 Root heartbeat 恢复同一 observer
与同一组 handles，不新增逐实验 heartbeat、daemon 或队列系统。本地接管不改变
remote-first 及卡片的 host/device 约定。

## 工具暴露与 custom role 的边界

此次 sibling 收发及 idle 唤醒已验证成功；**Luna tracker 的双向发送尚未验证**。
临时以 `agent_type=default`、显式 Luna/xhigh 启动的 tracker 能收到 DM 消息，但其两个
有界检查都报告顶层只有 `functions`、`mcp__cua_repl`，没有 `collaboration`。这是该实例
的实际工具暴露限制，不是“sibling 不可用”，也没有证明 Luna 或所有 custom agents
都不支持。它没有执行过原生发送调用，因此不能写成原生发送被拒绝。

相反，其 app task-message 尝试确实被拒绝：
`direct app-server input is not allowed for multi-agent v2 sub-agents`。
这个接口不是 sibling 通信接口；不通过 app-server、shell 或网络绕过拒绝。

新 role 文件已安装，但当前 Root 对 `hmasd-experiment-tracker` 的选择曾返回
`unknown agent_type`。不要把临时 default 实例登记成已成功加载的 custom role。加载角色
失败与原生发送工具缺失应分别记录；显式 `agents.enabled = true` 也不等于已通过收发
验证。后续支持该配置的 runtime 应按名字选择角色，先做一次直接 DM ACK，再更新能力
状态。在此之前保留有限进程观察和必要的 Root 恢复投递，实验不因此重复或失去 intake。

## 文档依据

[官方 Subagents 文档](https://learn.chatgpt.com/docs/agent-configuration/subagents)
说明 standalone TOML 的必填字段、`name` 寻址、模型/effort 配置和原生任务编排。
[官方 Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)
说明 `agents.enabled` 与 `agents.<name>.config_file`。这两页没有单独规定 sibling 发送
API；本说明的 canonical 寻址、发送与唤醒语义来自当前 runtime 暴露的原生工具契约，
并由上面的两端实测确认。公开文档未写明新角色在已运行 turn 中的即时重载保证，不能
用这次 `unknown agent_type` 单独推断具体加载原因。
