# HMASD Session Envelope Protocol v1

本协议只约束跨 Codex session 的 HMASD 语义。Codex 原生负责 task 身份、历史、
create、send、read、wait 和同 task 继续；本协议不复制这些能力。

## 唯一 transport artifact

跨 session 的固定信息由 scripts/hmasd_session_envelope.py 生成，写入已 gitignore
的 .codex/runtime/session-envelopes/<direction-id>/。

当前 session skill 层只有 `hmasd-root-task`、`hmasd-workflow-clerk-task`、
`hmasd-portfolio-task`、`hmasd-em-task`、`hmasd-cm-task`、
`hmasd-slice-interface` 和 `hmasd-operations-manual`。它们让对应 top-level task 在
相关工作开始时自动加载自己的切面；它们不新增协议状态。Root/Portfolio/EM/CM
使用 slice interface，Clerk 使用 operations manual 独占 topology/routing。

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

receiver 将 Codex delegation 的 exact input 交给 `read-message`。非 exact locator
的自然语言、raw JSON、附带说明的 locator 与 leaf report 均为 `NON_ENVELOPE`，
不触发路由。用户直接对话仍是用户输入。

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

`send_message_to_thread` 只由 top-level sender 调用，并且参数只能使用 CLI 的
`output.recipient_thread_id` 与 `output.message`。所有 leaf return only to the
spawning parent；leaf 不持有跨 session recipient，也不直接联系 Clerk。

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

Only two ASSIGNMENT edges are valid: `Root -> Workflow-Clerk` for an exact
coordination request, and `Workflow-Clerk -> Root/Portfolio/EM/CM` for one
bounded responsibility slice. Portfolio, EM, and CM never create an ASSIGNMENT
for another participant. They return a decision to Clerk; Clerk performs the
next native send.

This route restriction applies to newly generated assignments. A legacy v1
participant-to-participant assignment already in flight may be read and return
to its original sender exactly once so existing work is not stranded; neither
side may create another legacy edge from it. The original sender forwards that
same legacy RETURN locator once to the single observed Workflow-Clerk task
without wrapping it in another assignment. Clerk reads it as transition-only
input and resumes the normal topology with a new Clerk-generated assignment.

1. participant 在 final 前使用 Codex 原生 send_message_to_thread，把 script 输出的
   固定 locator 消息发送给 envelope recipient_thread_id。
2. Clerk 收到 RETURN 后，先 read，再向下一责任 session 创建 ASSIGNMENT，或向
   用户发送 terminal summary。
3. participant 已停止但 Clerk 未收到匹配 RETURN 时，Clerk 继续同一个 Codex
   task，并重用原 assignment locator；不得创建重复 manager。
4. envelope 文件存在不等于消息已发送。Codex task history 中可见的原生消息才是
   hop 已交接的事实。
5. Clerk 在 ingress 后和 final 前各运行一次纯 `liveness` 投影。第二次是 bounded
   drain：同一 active turn 中新注入的 locator 必须在结束前处理；若 task 已停止且
   无 RETURN，程序只重投同一 assignment locator。
6. `liveness` 输入只含 native task `id/name/status`、recipient history 中实际可见的
   每方向唯一 outstanding current locator，以及 native owner 的 exact
   pause/heartbeat/experiment 观察。ASSIGNMENT 在 correlated RETURN 可见后清除；
   RETURN 在 next ASSIGNMENT 或 terminal/user summary 可见后清除。它不扫描
   envelope 目录来猜 delivery，也不按文件 mtime 猜当前事件；assignment 的
   `context_refs` 与 RETURN `reply_to` 是因果关联。

## Direction liveness invariant

每个 selected direction 在任一时刻按以下优先级分类，命中第一项后停止：

1. registry lifecycle 为 `CLOSED`：正式结束且没有 next slice；
2. registry lifecycle 为 `PARKED`、exact material question 已送达 Root/user，且
   reactivation condition 是该用户答案：正式暂停；
3. 资源等待，retry assignment 与唯一 heartbeat 位于同一 owner，成功后 heartbeat
   自动取消；
4. owner session 持有 current assignment，next event 是 correlated RETURN。

不满足上述任一项的 idle 是 transport/workflow defect。Clerk 必须重投 existing
locator 或按已验证 RETURN 发送下一 assignment；不能用 PARKED、local DONE 或裸
BLOCKED 掩盖。未持有当前切面的其他 manager idle 不构成缺陷。

## Portfolio routing contract

Portfolio 是低频的跨方向选择、优先级、资源投入与 lifecycle 决策者，不是普通
EM/CM 调度者。Clerk 使用单一 transport `direction_id=portfolio` 唤醒一次全局
判断；该相关 ID 不限制 Portfolio 的研究范围。Portfolio 可在同一 wake 比较多个
方向、打开新方向，并用 `portfolio-return` 生成一个
`PORTFOLIO_RETURN.actions[]`；Portfolio 不创建 task，不向 Root、EM 或 CM 发送
ASSIGNMENT，也不等待这些角色。

Portfolio 对一个仍在投资范围内的方向必须在 RETURN 中选择下一责任类型，不能把
“当前切面完成”或“实现尚不存在”自动解释为方向终止：

1. 科学对象、可证伪判据、比较对象或证据解释仍缺失：返回 `REQUEST_EM`。
2. 科学对象与判据已经接受，但 source、test、CLI、instrumentation、batching 或
   运行入口缺失：返回 `REQUEST_CM`。
3. 工程入口和实验定义均已准备：返回 `REQUEST_CM` 及精确实验准备目标；CM 决定
   是否创建唯一 Experiment Operator。
4. 需要用户材料决定：返回 `REQUEST_USER`。只有 durable lifecycle 已明确变为
   `CLOSED` 且无下一切面时才返回 terminal `DONE`。

Clerk 在发送任何下一 ASSIGNMENT 前先原子校验完整 actions 列表，再在同一事件
turn 展开所有独立 ready action。每个 action 只携带自己的 direction ID、refs、
lifecycle、status 与 next objective；Clerk 不重做 Portfolio 比较。Portfolio 的决定
与 Clerk 的 transport 动作必须保持为两个不同责任。
新 global Portfolio assignment 不能使用普通 `return`；CLI 在文件创建前拒绝该
绕行，Portfolio 必须修正完整 actions body 并重新运行 `portfolio-return`。切换前
明确要求旧格式的 direction-specific Portfolio assignment 才可用普通 `return`；
其中 `REQUEST_PORTFOLIO` 仍被拒绝。

新 global wake 的 action/lifecycle 对固定为：`ACTIVE` + `REQUEST_EM` 或
`REQUEST_CM`，或 `ACTIVE` + scoped `FAILED`；`PARKED` + `REQUEST_USER`；
`CLOSED` + `DONE`。一个失败 action 不删除其他 ready actions。CLI 在创建与读取
时把每个 action lifecycle 与当前 Portfolio registry 匹配，body-only terminal
声明不能路由。普通 `return` 仅用于完成已经在途、明确要求旧格式的 Portfolio
assignment。

只有明确的科学否决、资源否决、用户决定，或已经证明该方向没有任何可执行的
科研/工程切面时，Portfolio 才能 PARK/CLOSE。缺少现成实现、测试或 CLI 本身必须
路由给 CM，不能作为 PARK 理由。

## Clerk semantic routing and topology

Workflow-Clerk 的完整运行说明是
`.codex/prompts/hmasd-workflow-clerk.md`。它只使用标准 RETURN status 与 failure
scope 路由，不能从方向 prose 推导全局状态。每次处理新事件先由 Codex task
list/read 获取当前 Portfolio、EM、CM 的 exact task ID/generation/status，形成仅存在
于当前 turn 的 topology snapshot；不得写入第二 registry 或 task cache。

Clerk 同时维持现有 `scripts/hmasd_dashboard.py` 在
`http://127.0.0.1:8765` 可用。Dashboard 每次请求只读 Portfolio registry 与方向
state，并在独立 Clerk tab 显示 ignored `.codex/runtime/clerk-liveness.json`；它不写
authority、不路由工作，陈旧 task projection 必须显示为陈旧，且服务故障不改变
任何方向 liveness。

多个正交方向 ready 时，Clerk 必须在本 turn 生成并发送全部独立 assignment，然后
在 final 前用新鲜 native task/history observations 再运行一次
`hmasd_session_envelope.py liveness` 并执行
所有 machine-emitted action。普通事件 turn 不调用 wait；新的原生消息通常会再次
唤醒 Clerk，而 active turn 内合并到达的消息由这次 bounded drain 回收。
某方向的 memory refusal、REQUEST_USER 或 feature failure 不得延迟其他
方向的 ready send。跨方向汇总只能发给 Root/user，不能作为 participant 的
assignment。

Clerk 在考虑 Root 前使用唯一责任案例映射：方向科研语义与 Pro external review
归现有 EM，其中 Pro 由 `hmasd-explorer-agentify-transport` 调用 GPT-5.6 Pro；方向
实现、依赖、路径、Git、candidate、dossier、manifest、prepare 与 Operator 归现有
CM；跨方向 priority/investment/lifecycle 归 Portfolio。缺少代码、依赖、candidate、
manifest、activity release 或 future Operator identity 都不是 Root 切面。Root 只接收
真实用户材料选择、user-owned irreversible Effect、shared-core 语义修改、task
identity conflict，或无法由协议机械解释的矛盾；最后一种只上报事实，不把方向切面
转交 Root。

Clerk 构造 EM assignment 时必须把 `.codex/prompts/hmasd-em.md` 放入 context refs；
构造 CM assignment 时必须同样引用 `.codex/prompts/hmasd-cm.md`；构造 Portfolio
assignment 时引用 `.codex/prompts/hmasd-portfolio.md`。三个 prompt 是各 manager 的
role-internal orchestration 入口。Clerk does not choose or sequence their leaves。
slice 可以冻结路径、Effect 并禁止当前 result-bearing command，但不能 blanket-ban
subagent 而删除 EM/CM 的 direct-leaf 接口。静态 CM slice 可以明确“不需要
Operator”，但不能把这一点扩展成后续 eligible execution slice 的全局禁令。

## Participant Git completion

`C:/Projects/HMASD` 是 shared checkout 且永久保持 `main`（permanent `main`）。任何 manager 都不得在
这里运行 `git switch` 或 `git checkout`。只有 assignment 明确绑定一个 separate
worktree 时才允许使用方向分支；否则 workspace mode 是 shared `main`，owner 在不
改变分支的前提下提交 exact owned paths。

修改 tracked direction-owned source、test 或 durable authority 的 top-level 责任
session 必须在发送 RETURN 前自行完成 Git 收尾；leaf helper 不 commit/push，也不把
Git 收尾转交 Root：

1. 仅 stage assignment `owned_paths` 内由本切面产生的 exact paths，不得带入其他
   session 的 staged/dirty 文件；
2. shared checkout 在 `main` 上 commit/push；显式 separate worktree 才在其 exact
   assignment branch 上 commit/push；
3. RETURN summary 明确报告 `branch`、完整 commit SHA、remote/ref 与 push 结果；无
   Git-visible 改动时明确报告 `Git: no changes`；
4. commit/push 失败使用 direction/feature/effect scoped failure。push commitment
   unknown 时只 observe remote，不盲目重发；
5. 使用 worktree 的责任 session 必须在 branch 已 push 后回收 exact clean worktree，
   或在 RETURN 中明确报告 retained worktree、branch、HEAD 和不能回收的原因。不得
   无说明遗留 dirty worktree。

共享 main 可以同时包含其他方向的 unstaged 修改；这不是跳过本方向 Git 收尾的
理由。worktree 仍是显式例外而非默认流程。

Direction-owned candidate 和 manifest preparation 属于同方向 CM 的普通工程切面。
其中 static prelaunch dossier 是 CM artifact、不得调用 run CLI；runtime prepare
由 CM 调用 `hmasd_run.py prepare` 并持有资源 heartbeat；payload/result execution
只由唯一 Operator 执行。Root 不是 manifest
preparation 的正常 owner；只有 shared-core、明确 user-owned decision/effect、task
identity conflict、cross-direction Git integration，或无法机械解释的 protocol
question 才路由 Root；protocol question 只上报事实，不把方向工作转给 Root。历史 authority
中旧的 runtime actor 名称不改变材料决定，但由当前协议重新映射实际 actor。

## Memory-admission fallback

`hmasd_run.py prepare` 在创建 reserved output root 前执行资源评估。若
`memory_safe=false`，它返回 exit 6、输出完整评估且保持 root 不存在；下一 heartbeat
可安全重试同一冻结命令。为兼容旧调用，它只会机械回收以下精确 partial shape：

- 没有 `manifest.json`、stdout/stderr、checkpoint 或 artifact 内容；
- 只有 `preflight.json` 与空的 `artifacts/`、`checkpoints/`、`metrics/`；
- preflight 的 direction/run 匹配且 `memory_safe=false`。

任何额外文件、非空目录、symlink 或 identity mismatch 都拒绝回收。Clerk 对每个
direction/run_id 只允许一个 Codex heartbeat；heartbeat 必须建立在 retry
assignment 的 exact recipient task 上。prepare/memory admission 默认由同方向 CM
负责，不能把 timer 建在 Root 或 Clerk 上，除非 exact assignment 明确把该责任交给
它们。heartbeat 不能修改 estimate、parameters、command 或 code SHA，不能创建
Operator。manifest 进入 `PREPARED` 后先发送 correlated RETURN，再删除该
heartbeat。正式执行仍通过普通 CM→唯一 Operator 流程。

## 明确非职责

hmasd_session_envelope.py 不得创建、命名、等待、恢复或关闭 Codex task，不解析
raw rollout，不选择下一角色，不维护 task lifecycle、retry FSM、权限 gate 或第二
registry，也不使用 hash/receipt 重复证明 Codex 消息存在。

实验命令与进程事实仍由 hmasd_run.py 负责；Git 与 durable authority 仍使用各自
现有工具。session envelope 不取代这些领域边界。

一个已在方向 authority 内、memory-safe、无新 external commitment/shared-core
语义变更且预计不超过 7200 秒的本地 PREPARED result command 不需要仅因“是真实
科学执行”再次请求用户批准；Clerk 直接路由同方向 CM，由 CM 创建唯一 Operator。
`REQUEST_USER` 只用于 authority 确实保留给用户的材料选择、超过 7200 秒的 exact
command，或另一个明确的 user-owned Effect。缺少尚未创建的 future Operator identity
不是阻塞或批准理由。
