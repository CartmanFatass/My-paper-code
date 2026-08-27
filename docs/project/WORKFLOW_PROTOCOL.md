# HMASD Session Envelope Protocol v1

本协议只约束跨 Codex session 的 HMASD 语义。Codex 原生负责 task 身份、历史、
create、send、read、wait 和同 task 继续；本协议不复制这些能力。

## 唯一 transport artifact

跨 session 的固定信息由 scripts/hmasd_session_envelope.py 生成，写入已 gitignore
的 .codex/runtime/session-envelopes/<direction-id>/。

每个 envelope 固定包含：

- schema_version
- message_id
- direction_id
- sender.identity 与 sender.thread_id
- recipient.identity 与 recipient.thread_id
- kind
- reply_to
- body

上述 header 由 script 生成或从原 assignment 复制。LLM 不填写或改写 header，只
提供 body JSON。

## Assignment body

ASSIGNMENT body 的字段固定为：

- objective：当前局部切面的目标；
- context_refs：接收 session 需要读取的 repository-relative 路径；
- owned_paths：本切面允许写入的路径或目录前缀；
- constraints：局部约束；
- done_when：完成与交接条件。

Clerk 调用：

    python scripts/hmasd_session_envelope.py assignment +      --repo <repo> +      --direction-id <direction> +      --sender-identity Workflow-Clerk +      --sender-thread-id <clerk-thread> +      --recipient-identity EM/<direction>/g<generation> +      --recipient-thread-id <participant-thread> +      --body <assignment-body.json>

script 生成 UUID message_id、固定 header、canonical runtime 文件，并输出：

- locator；
- recipient_thread_id；
- 固定消息 HMASD_SESSION_ENVELOPE_V1 <locator>。

Clerk 只把该固定 locator 消息通过 Codex 原生 send 发送给目标 task。

## Return body

RETURN body 的字段固定为：

- status
- summary
- changed_paths
- artifact_refs
- next_objective
- failure

status 只能是 DONE、REQUEST_EM、REQUEST_CM、REQUEST_PORTFOLIO、
REQUEST_USER 或 FAILED。FAILED 必须给出 project、direction、feature 或 effect
范围的 failure。REQUEST_* 必须给出 next_objective。

participant 调用：

    python scripts/hmasd_session_envelope.py return +      --repo <repo> +      --assignment <assignment-locator> +      --body <return-body.json>

script 自动：

1. 读取并校验 assignment；
2. 复制 direction_id；
3. 翻转 sender 与 recipient identity/thread_id；
4. 将 reply_to 绑定到 assignment message_id；
5. 生成确定性的 <assignment-message-id>:return；
6. 检查 changed_paths 位于 assignment owned_paths；
7. 写入唯一 return envelope，并输出 Clerk thread ID 与固定 locator 消息。

相同 assignment 与相同 return body 重复调用时复用同一 return 文件；内容不同时
返回冲突，不创建第二份。

## Read

任何 receiver 调用：

    python scripts/hmasd_session_envelope.py read +      --repo <repo> +      --envelope <locator>

read 校验 envelope；RETURN 还会读取 paired ASSIGNMENT，检查 direction、
reply_to、反向 endpoints 与 changed_paths。输出包含完整 envelope、locator、
recipient_thread_id 和固定 locator 消息。

## Session completion contract

1. participant 在 final 前使用 Codex 原生 send_message_to_thread，把 script 输出的
   固定 locator 消息发送给 envelope recipient_thread_id。
2. Clerk 收到 RETURN 后，先 read，再向下一责任 session 创建 ASSIGNMENT，或向
   用户发送 terminal summary。
3. participant 已停止但 Clerk 未收到匹配 RETURN 时，Clerk 继续同一个 Codex
   task，并重用原 assignment locator；不得创建重复 manager。
4. envelope 文件存在不等于消息已发送。Codex task history 中可见的原生消息才是
   hop 已交接的事实。

## Portfolio routing contract

Portfolio 对一个仍在投资范围内的方向必须选择下一责任角色，不能把“当前切面
完成”或“实现尚不存在”自动解释为方向终止：

1. 科学对象、可证伪判据、比较对象或证据解释仍缺失：向同方向 EM 发送下一
   ASSIGNMENT。
2. 科学对象与判据已经接受，但 source、test、CLI、instrumentation、batching 或
   运行入口缺失：向同方向 CM 发送实现 ASSIGNMENT。
3. 工程入口和实验定义均已准备：向同方向 CM 发送实验准备 ASSIGNMENT；CM 决定
   是否创建唯一 Experiment Operator。
4. 需要跨方向排序、资源投入或继续/停止判断：Portfolio 自己形成决定，然后仍须
   发送下一 ASSIGNMENT 或 terminal RETURN。

只有明确的科学否决、资源否决、用户决定，或已经证明该方向没有任何可执行的
科研/工程切面时，Portfolio 才能 PARK/CLOSE。缺少现成实现、测试或 CLI 本身必须
路由给 CM，不能作为 PARK 理由。

## Clerk semantic routing and topology

Workflow-Clerk 的完整运行说明是
`.codex/prompts/hmasd-workflow-clerk.md`。它只使用标准 RETURN status 与 failure
scope 路由，不能从方向 prose 推导全局状态。每次处理新事件先由 Codex task
list/read 获取当前 Portfolio、EM、CM 的 exact task ID/generation/status，形成仅存在
于当前 turn 的 topology snapshot；不得写入第二 registry 或 task cache。

多个正交方向 ready 时，Clerk 必须先生成并发送全部独立 assignment，再执行第一
次 wait。某方向的 wait、memory refusal、REQUEST_USER 或 feature failure 不得延迟
其他方向的 ready send。跨方向汇总只能发给 Root/user，不能作为 participant 的
assignment。

## Memory-admission fallback

`hmasd_run.py prepare` 在创建 reserved output root 前执行资源评估。若
`memory_safe=false`，它返回 exit 6、输出完整评估且保持 root 不存在；下一 heartbeat
可安全重试同一冻结命令。为兼容旧调用，它只会机械回收以下精确 partial shape：

- 没有 `manifest.json`、stdout/stderr、checkpoint 或 artifact 内容；
- 只有 `preflight.json` 与空的 `artifacts/`、`checkpoints/`、`metrics/`；
- preflight 的 direction/run 匹配且 `memory_safe=false`。

任何额外文件、非空目录、symlink 或 identity mismatch 都拒绝回收。Clerk 对每个
direction/run_id 只允许一个 Codex heartbeat；heartbeat 必须绑定 retry assignment，
不能修改 estimate、parameters、command 或 code SHA，不能创建 Operator。manifest
进入 `PREPARED` 后先发送 correlated RETURN，再删除该 heartbeat。正式执行仍通过
普通 CM→唯一 Operator 流程。

## 明确非职责

hmasd_session_envelope.py 不得创建、命名、等待、恢复或关闭 Codex task，不解析
raw rollout，不选择下一角色，不维护 task lifecycle、retry FSM、权限 gate 或第二
registry，也不使用 hash/receipt 重复证明 Codex 消息存在。

实验命令与进程事实仍由 hmasd_run.py 负责；Git 与 durable authority 仍使用各自
现有工具。session envelope 不取代这些领域边界。
