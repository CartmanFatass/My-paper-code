# 2026-09-18 — WSL 主机的 Pro 通道迁移到 Jev Ultrafast

Owner 指示(Claude 会话,WSL 主机):用本机的 Jev Ultrafast 完成 Pro 发送,浏览器是本机的
Chrome for Testing,登录的是 owner 的第二个 ChatGPT 账号(额度原因);有头、无头各测一次,确认后
写技能,默认无头;transport 整体外包给 Jev,模型请求优先原生 TypeSafe key;该账号的会话地址等
私人信息只留在本地,不进入任何被推送的文件。

## 改动

| 文件 | 内容 |
| --- | --- |
| `tools/pro_transport/jev_send.py` | 新增。`chrome start/stop/status`、`send`、`wait`。Jev 自己完成输入和发送;驱动只提供提交原文、在发送点击前落盘 `send_attempted`、在 effort 或文本不符时拒绝那一次点击,之后只读观察 |
| `.codex/hmasd-transport.toml` | 新增 `[jev]`:Jev 根目录、Chrome、profile、CDP 地址、默认无头、effort 标签 `6 Pro`、状态目录 |
| `.agents/skills/hmasd-jev-pro-transport/SKILL.md` | 新技能;`.claude/skills/` 下的同名文件由 `tools/publish_claude_control.py` 生成 |
| `AGENTS.md`、`docs/project/HOST_AND_RUNTIME_SWITCHING.md` | 各加一句:WSL 主机用新技能;Windows 主机仍用 Agentify |

没有修改 Jev 仓库,没有向任何解释器安装东西;Jev 的凭证留在它自己被忽略的 `.env` 里。

## 测试(2026-09-18 23:35–23:41 PDT)

| 模式 | Jev 步骤 | 结果 |
| --- | --- | --- |
| 有头 | TYPE_TEXT 输入框 → CLICK 发送提示词 | 已发送,完整读回约定的应答行 |
| 无头 | 同上 | 已发送,完整读回约定的应答行;同 key 再次 `send` 不发送 |

两条测试会话的地址只在本机状态目录的操作文件里。

## 途中发现并已处理的事实

- Jev 的本地补丁在有网关 key 时总走 Vercel 网关,被限流(HTTP 429)。驱动在有原生 key 时不把
  网关 key 传入进程。
- effort 控件是滑块(5 档,最高档显示 `6 Pro`),不在 Jev 的动作空间内。驱动用方向键设到最高档,
  以观察到的标签为准。
- 新会话先显示不可重开的临时地址;驱动等到稳定地址才记录,`wait` 可用 `--conversation-url` 补记。
- ChatGPT 会在新会话页恢复本地草稿;Jev 的填充是全选后插入,会覆盖它。发送点击前的文本相等检查
  拦下过一次"草稿未被替换就去点发送",之后在目标里告诉 Jev 框里是过期草稿。
- 无头模式用正常 UA 启动,未遇到登录或人机验证。

## 未覆盖

长篇多段问题、GitHub connector 写回、Pro 长时间生成期间的等待,都还没有在这条通道上跑过;
第一次真实问题发送时按技能的恢复条款处理。

## 2026-09-19 补充:真实长问题,改为"短消息 + 文档"

第一次真实问题(FSD notebook 的 `Pro question 2026-09-19 b01-after-stage0-next-step`,约 2900 字符)
整段输入后点击发送没有提交:草稿原样留在新会话页,没有新会话。按 owner 的建议改为上传文档。

| 改动 | 内容 |
| --- | --- |
| `send --attach <document>` | 完整消息作为文档,经输入框自带的上传控件(CDP `DOM.setFileInputFiles`)附上;短消息写明文档名和 SHA-256。发送点击前核对短消息逐字相等且附件在输入框里;发送后核对会话里有短消息和附件名 |
| `reconcile --key` | 只读。仅当没有记录到稳定会话地址、且提交的原文仍作为未发送草稿留在新会话页时,才释放该 key,且只释放一次 |
| 每步告知 Jev 输入框状态 | Jev 看不到要输入的文本,无法判断框里是否已是它;驱动在每次决策前说明"已完整在框里"或"仍是旧草稿"。此前 Jev 因此连续重复输入而不去点发送 |
| 清空恢复的草稿 | 很长的旧草稿会把输入框撑出视口,Jev 正确地拒绝点不中的目标;驱动先全选删除 |
| `wait --prompt-file` | 以"提交的短消息包含在用户消息里"核对会话,并记录 `attachment_seen` |

结果:同一问题 key 在 `reconcile` 释放后,以短消息 + 文档的形式无头发送成功,会话里核对到短消息和附件。

## 2026-09-19 补充:连接器授权交给 Jev

Owner 指示:GitHub connector 的授权提示由 Jev 以"始终允许"统一处理;单独授权的只有 GitHub
connector,出于工程协作的必要。

- `[jev]` 新增 `approval_policy = "always_allow"`、`approval_connectors = ["GitHub"]`。
- `wait` 看到授权提示时由 Jev 找到并点击按钮;驱动只放行"提示文字点名了列出的连接器、且按钮
  文字恰为'始终允许'/'Always allow'"的那一次点击,并记入本地操作文件的 `approvals`。其他连接器
  或其他授权仍返回 `NEEDS_HUMAN`,不点击。
- 结果:授权后 Pro 读取了仓库固定版本的全部指定来源,并通过连接器把完整回答写回方向分支的
  `### Answer` 小节(单个提交,父提交为问题的 source_sha,只有新增行),聊天里只留带提交 SHA 的
  回执。技能已写明:`COMPLETE` 的短回执不是答案,要接着读交付。

至此这条通道覆盖了:无头发送、长问题(短消息 + 文档)、长时间等待、连接器读与写回。

## 2026-09-19 补充:流程优化与修复

Owner 指示"优化修复一下这个流程"。针对第一次真实问题暴露出的问题:

| 问题 | 修复 |
| --- | --- |
| 发送前的失败每次都上传一份文档,账号文件库里留下重复副本 | 先让 Jev 输入,输入框与短消息相等后才上传 |
| 上传后 Jev 连点输入框六七次才去点发送,有一次因此被 Jev 自己判为 blocked | 原因:文件处理期间发送按钮被禁用,禁用控件不在 Jev 的元素表里。驱动等按钮连续四次采样可用后才问 Jev;并在目标里写明"只剩点发送"。复测:两步到达发送按钮 |
| 等待用 120 秒短调用反复开标签页,空转 80 分钟没发现页面在等人 | `wait` 默认一次 3600 秒的长调用,保持一个标签页,只在状态变化时输出;授权提示按上一节处理 |
| 聊天里的短回执被当成答案 | `wait` 标出 `kind: receipt` 和回执里的提交;新命令 `deliver` 在仓库里找到填写该问题 `### Answer` 的提交并核对:只有一个、只动目标文件、问题和其余字节不变、原小节为空。不满足则 `CONFLICT` 或 `NOT_DELIVERED` |
| 手工拼短消息、手算 key、每次用 sed 遮会话地址 | 新命令 `compose`、`key`;输出默认把会话地址显示为"recorded locally",`--show-url` 才打印 |
| 改动发送路径后只能靠真发一条来验证 | `send --dry-run`:做完全部步骤和核对,只是不点发送,不消耗 Pro 请求;`HMASD_JEV_DEBUG=1` 打印 Jev 每步看到和选择的内容 |

离线测试 `tests/skills/test_jev_transport.py`(控制面解释器):key、地址遮蔽、`compose`、
`answer_block`、`deliver` 的交付/冲突判定(临时 git 仓库)。`deliver` 对真实问题复核为
`DELIVERED`(提交 `18e1543d8`,答案 20946 字符)。
