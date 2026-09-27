# 独立通用外部等待器

这是单独发布的 POSIX 工具，不替换 `hmasd_wait.py`，不修改现有 AGENTS、skills、
角色或运行配置，也不迁移已接受任务。参照 owner 指定的
`/home/fires/codex/MySkills/Fix_wait`；控制器初版直接采用其 `assets/codex_wait.py`
（SHA-256 `99c81a56fdf4fbf57e36768518db01e407ee0aef9cde03abcd720c43ceaed555`）。
独立审查后在新副本加固：尚未执行 drain 时，即使 event IDs 为空也拒绝 rearm，
防止清除 queued／未知投递的 wake 后对同一事件重复通知。检查点通知待处理期间，
仍持续只读观察运行中的任务并保存晚到的终态事实。原 Fix_wait 未改。
旧入口仍负责已接入它的操作。本工具只有在真实等待已经获授权、且适配器能只读判断
条件时才启动；发布工具本身不启动科研或向其他会话发消息。

## 运行逻辑

1. `start` 为当前 `CODEX_THREAD_ID` 注册稳定、不复用的任务 ID 和只读探针。
2. 脱离模型回合的脚本最多并行执行 8 个有界探针；没有变化就留在脚本内等待。
3. 条件完成、失败、阻塞或观察窗口到期时，先持久化事件，再用
   `codex queue --thread <原会话> --message <通知>` 唤醒当前会话。
4. 一次只保留一个待处理 wake；多个事件合并，未知投递不自动重发。检查点过期后，
   仍按探针间隔和每次超时继续观察运行中的任务，直至显式 stop 或全部任务不再运行。
5. 会话收到 `[fix-wait <wake-id>]` 后执行 `drain`，读取全部事件和相关产物；
   再用返回的 generation、wake ID 和全部 event ID 执行 `rearm`。
6. `rearm` 确认消费并续等同一批仍运行的任务；不会重启终态任务。读取后晚到的事件
   留给下一次通知，不能猜测未读 ID。

这沿用 Fix_wait 的控制逻辑。检查点不是“完整任务已完成”；一个 Git 文件发布变化
也不代表生产者的整个研究已完成。业务判定在适配器内，控制器只观察、记录和通知。
外部构建、远端任务、文件发布、Pro 等均可通过各自适配器输出相同 JSON 接入，
不在控制器内加入业务启动、重试、浏览器操作或科学解释。

## 环境、窗口与状态

POSIX、Python 3.10+、同账户且支持 `queue` 的 Codex CLI，以及当前 `CODEX_THREAD_ID`。
本次本机检查为 Codex CLI 0.157.1、Python 3.11.16；采用已配置解释器
`/home/fires/.venvs/hmasd-linux-science-tools/bin/python`，不安装新依赖。
独立控制器运行时仅用标准库，测试需要 pytest。

默认状态目录 `~/.local/state/codex-wait/<thread-uuid>/`。同一会话在本工具中只使用
一个目录；若使用 `--state-dir`，每条命令传相同目录。状态、日志、请求不提交 Git。
不要对同一操作同时启动本工具和旧 waiter，也不要通过多个目录绕过 8 项容量或通知去重。
旧 waiter 的状态格式不同；本工具会拒绝它，不自动导入或覆盖。

保留本项目现有 agent wait 配置 25／25／60 分钟，不写 `.codex/config.toml`。
这些原生 agent wait 参数与脚本窗口分别生效。脚本默认 `--window 1500`（25 分钟），
为 queue 留出至多 25 秒；窗口结束产生一次检查点，待确认期间仍保存晚到的终态事件，
实际工作不受这个窗口限制。
它提供了及时续接与维持会话上下文的机会，不能保证服务端缓存保留期限、通知送达或
宿主消费时间。`queued` 只表示 CLI 成功入队，不证明模型实际唤醒或缓存命中；
后台进程仍在运行也不证明模型已读。

探针默认每 30 秒执行一次（上限 300 秒）；支持长轮询的外部接口可以直接等待变化，
在 stdout 返回状态后即进入 queue 流程。短探针的通知延迟受声明间隔及实际查询耗时
限制，不是等待整点再唤醒模型。轮询间隔、探针超时和会话窗口是三个不同参数。

## 通用探针合同

stdout 只输出一个 JSON 对象；诊断日志写 stderr。探针须可重复、无副作用、有界，
可以用 argv 数组显式调用 SSH。控制器不能证明任意命令只读，调用者必须核对命令。

| `state` | 处理 |
| --- | --- |
| `running` | 静默继续观察 |
| `complete` | 保存 COMPLETE，停止该条件的探测，等待读取产物 |
| `failed` | 保存 FAILED，不重启或重提实际任务 |
| `blocked` | 保存 BLOCKED，原因解决后显式选择恢复 |
| `unknown` | 有界退避重试；连续三次为阻塞，不推断实际任务失败 |

非零退出、超时、损坏 JSON 也为 unknown。不要仅凭 PID 消失、文件存在或 exit 0
推断研究成功。探针的其他 JSON 字段作为证据落盘，不作为指令执行。

通用请求没有业务 `protocol` 字段：

```json
{
  "jobs": [{
    "id": "existing-operation-unique-id",
    "argv": ["/absolute/python", "/absolute/project/tools/check_existing_job.py", "operation-id", "--timeout", "{window_seconds}"],
    "cwd": "/absolute/project",
    "interval_seconds": 30,
    "probe_timeout_seconds": 20
  }]
}
```

`{window_seconds}` 替换为当前剩余探针预算，并为退出留余量。长轮询可声明较长
`probe_timeout_seconds`（上限 3600）；窗口到期前受剩余窗口约束，到期后每次探针
仍受这个独立超时约束。同 ID 的请求不能换
argv、cwd 或参数；相同任务重复注册是幂等操作，不能复活终态任务。

附带的通用适配器 `tools/codex_wait_probe.py` 有两种可实际接入的条件：

- `result-json --path <绝对路径> --expected-id <原操作ID> [--identity-key operation_id]`：
  读取生产者原子发布的通用状态文件，核对原操作身份。不存在为 running，身份冲突为
  blocked，半写或不支持的状态为 unknown。文件缺失本身不证明任务仍健康。
- `git-publication --repo <本地仓库> --remote origin --ref refs/heads/main --path <仓库相对文件>
  --baseline <完整提交ID> --timeout <秒>`：比较基线与远端已发布提交的该文件 blob；
  忽略未提交、未推送和无关文件变化，不读取文件内容。新增、删除也算发布变化。
  本地仓库须已有这些提交对象；缺失时报告 unknown，不执行 fetch、checkout 或其他写入。
  `complete` 只表示声明的文件变化条件已满足。若整个依赖尚未完成，以新的明确基线和
  新条件 ID 注册下一次观察；不是重新启动生产者。

## 完整命令与返回处理

以下路径和 ID 替换为真实值；也可用部署环境的 Python，而非本机示例路径。

```bash
wait_python=/home/fires/.venvs/hmasd-linux-science-tools/bin/python
"$wait_python" tools/codex_wait.py start --request /absolute/private/jobs.json --window 1500
"$wait_python" tools/codex_wait.py status
```

`arm` 是 `start` 的别名。注册后检查一次 status 和 daemon.log，确认首个探针实际工作；
注册成功不等于远端句柄已接入。若没有其他独立工作，结束模型当前轮次，由脚本等待。
status 仅用于诊断，不能代替 drain 的已读登记。收到通知后：

```bash
"$wait_python" tools/codex_wait.py drain
"$wait_python" tools/codex_wait.py rearm --generation <N> --wake-id <实际ID> --event-ids <全部已读事件ID> --window 1500
```

先处理全部已读事件再 rearm，完成的任务也需确认消费。只在明确解决阻塞原因后追加
`--resume-jobs <job-id> ...`，不会恢复其他阻塞任务或任何终态失败任务。

```bash
"$wait_python" tools/codex_wait.py stop
```

stop 取消的是该观察器拥有的探针进程组，实际工作不受影响；已经排队的消息不能撤销。
遵守 owner 最新暂停／停止要求，通知本身不授予恢复研究或跨会话发送权限。
停止后得到明确恢复指令，先 drain：有 wake 时按正常确认字段重接；没有 wake 和事件时，
仅使用返回的 generation 重接。`delivery_unknown`／`attempting` 先核对和手动 drain，
不盲目重发 queue。观察进程异常时核查旧进程已退出，再恢复原观察，保留未知投递证据。

## 验证范围

`tests/skills/test_codex_wait.py` 采用 Fix_wait 的回归用例，覆盖并行探针、合并通知、
去重消费、晚到事件、未知投递、阻塞恢复、停止取消、原操作身份和完整 CLI 往返。
`tests/skills/test_codex_wait_probe.py` 用临时 Git 仓库和结果文件检查实际适配器。
测试只使用假的 queue，不给真实会话发送测试消息；帮助可用和离线测试不等于真实
端到端自唤醒已验证。已授权的真实依赖可以正常接入，但不额外发送测试消息。

```bash
/home/fires/.venvs/hmasd-linux-science-tools/bin/python -m pytest -q tests/skills/test_codex_wait.py tests/skills/test_codex_wait_probe.py
```

本次发布前：两文件 **37 passed in 9.99 s**；独立工程审查获得
**36 passed, 1 deselected in 8.63 s**，并关闭未 drain 空确认和测试后台进程退出两项问题。
最后一项 CLI 退出等待修正后，定点复跑 **1 passed in 1.06 s**。
真实仓库的只读发布探针也已返回正确的未变化状态；未作真实 queue 自唤醒测试。
先前未发布、未运行的方向私有脚本及测试已撤回，两个目标分配空间从 12,288 B 降至 0 B。
