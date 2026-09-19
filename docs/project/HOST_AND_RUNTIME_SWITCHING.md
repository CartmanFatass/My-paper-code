# 主机与运行时切换协议

操作说明，不是新的权威：与 [OPERATING_CONSTITUTION.md](OPERATING_CONSTITUTION.md) 冲突时以宪法为准。
本协议不新增任何记录类型，只使用宪法第 4 节已有的三样记录（`NOTES.md`、`runs/<direction>/<tag>/`、
`CLAIM_<slug>.md`）和 `docs/research/RESEARCH.md`。切换本身不恢复研究，也不解除 owner 的暂停。

owner 要求（2026-09-18）：`main` 必须支持在 Claude 与 Codex 之间、在 Windows 与 WSL 两台主机之间随时切换，
研究进度始终同步，两台主机只在控制面适配上不同。

## 1. 为什么能切换

| 事实 | 位置 |
|---|---|
| 研究权威只有一处：`origin` 的 `refs/heads/main`。启动器把本机 `RESEARCH.md` 的暂停、方向状态、Lead 与已发布版本比较，不一致就拒绝 | `.codex/hmasd-compute.toml` `[control_source]`，`scripts/hmasd_launch.py` |
| 同一份 `main` 服务两台主机：控制面节点按 `--node` → `HMASD_CONTROL_PLANE_NODE` → `[control_plane_by_platform]` → `control_plane_node` 的顺序选出 | `.codex/hmasd-compute.toml` |
| 两个运行时读同一套方法：`.agents/skills` 是维护源，`.claude/**` 由 `tools/publish_claude_control.py` 生成 | [CONTROL_PLANE_MAP.md](CONTROL_PLANE_MAP.md) |
| 结果节点相同：两台主机都经 ssh 使用 `wsl_4070` | `.codex/hmasd-compute.toml` |
| Pro 通道相同：两台主机驱动同一个 Windows agentify 应用，注册在各主机、各运行时的用户级配置里 | `.agents/skills/hmasd-chatgpt-pro-transport/references/agentify.md` |

每台主机只保留自己的 checkout（Windows `C:/Projects/HMASD`，WSL `/home/fires/hmasd-wsl`）。不跨 `/mnt/c` 或
`\\wsl$` 使用对方的 checkout、index 或解释器。

## 2. git 带不走的东西

切换前必须自己处理，因为它们不随 `main` 同步：

- **进程句柄与 claim。** 启动器的 claim 库按 git 公共目录存放，两个克隆互不可见；本机启动的进程只有本机能观察。
  远端 `wsl_4070` 上的运行两台主机都能经 ssh 观察，前提是 `NOTES.md` 里记了 operation ref。
- **被忽略的产物。** `temp/`、`logs/`、`*.csv`、`*.log`、`*.pt` 不进 git；要留给对方看的表格发布为 `.json`，
  结论写进 `NOTES.md`。
- **运行时私有记忆。** Claude 记忆与 Codex memories 各主机、各运行时独立，不能承载研究状态；
  研究状态只写进上面三样记录。
- **逐位数值。** 相同版本的 numpy/torch 在 Windows 与 Linux 上仍有 1–2 ULP 差异。带字节一致性守卫的测试
  按主机各有基线（例：`tests/fixtures/flexible_skill_duration_d2/fingerprint_off{,.linux}.json`）；
  一个主机上的本地检查不能逐位预言另一台主机或 `wsl_4070` 的数值。科学比较始终在同一节点、同一批次内进行。

## 3. 切出（离开当前主机或运行时之前）

1. **没有在途的本机运行。** 本机启动的运行已到终态并已收集；远端运行可以在途，但其 operation ref、节点、
   预期结束时间已写入该方向的 `NOTES.md`。不确定的启动或 Send 先按同一请求对账，绝不盲目重发。
2. **记录落盘。** 当前想法、读数、下一步写入 `NOTES.md`（追加）；`RESEARCH.md` 的该方向一行反映真实状态。
   不另写 handoff 文件：`NOTES.md` 的最后一节就是交接。
3. **提交并发布。** 用显式 pathspec 提交，推送方向分支；要让对方看到的内容必须进入 `main`
   （由在任 Codex Root 集成；没有在任 Root 或有明确移交时，Claude 从自己的 checkout 集成）。
4. **工作区干净。** `git status` 为空；没有未完成的 merge、rebase 或 cherry-pick；临时 worktree 已移除或已说明。
5. **Lead 如需变更**，在 `RESEARCH.md` 的 Lead runtime 单元格里改并发布到 `main`。一个方向任何时刻只有一个
   lead/writer（宪法第 2 节）；启动器的 `--lead` 必须与已发布的单元格逐字一致，所以不改单元格就换不了执行者。

## 4. 切入（在另一台主机或另一个运行时开始之前）

1. `git status` 干净，`git pull --ff-only origin main`。拉不动先查原因（未完成的 cherry-pick、本地分叉），
   不用 reset、stash 或强推解决。
2. 读 `docs/research/RESEARCH.md`：暂停状态、自己是不是该方向的 Lead。不是 Lead 就不写该方向的 `NOTES.md`。
3. 读该方向 `NOTES.md` 的最后一节；有在途运行就用其中的 operation ref 执行
   `<configured-python> scripts/hmasd_launch.py status <operation_ref>`，先确认再接手观察。claim 记在启动它的
   那个 checkout 里：远端运行经 ssh 在 `wsl_4070` 上查，本机运行只能回到原主机查。
4. 首次在这台主机上、或控制面刚改过时，跑一次第 5 节的自检。
5. 运行中的会话不会因为拉取而刷新：方法或角色变了就在安全边界重读，MCP 或角色注册变了就重启会话。

## 5. 主机自检

在仓库根目录执行；解释器路径见 [CLAUDE.md](../../CLAUDE.md) 的主机表。全部只读或只写 pytest 自管的 scratch。

| 检查 | Windows | WSL | 预期 |
|---|---|---|---|
| 控制面生成副本 | 控制面解释器 `tools/publish_claude_control.py --check` | 同左 | `drift: 0` |
| 启动器与控制面测试 | 科学解释器 `-m pytest -q tests/test_hmasd_launch.py`；控制面解释器 `-m pytest -q tests/skills` | 同左，且 `PATH` 前置 venv 的 `bin` | 全部通过 |
| 本机节点解析 | 科学解释器 `-c "from pathlib import Path; from scripts import hmasd_launch as L; c=L._load_config(Path('.codex/hmasd-compute.toml')); print(L._node_config(c, None)[0])"` | 同左 | `local_windows` / `local_linux` |
| 方向守卫（按所接手的方向选） | 例：`tests/flexible_skill_duration_d2_test.py` | 同左 | 全部通过 |
| 原生后端 | `tests/uav_cpp_backend_test.py` | 同左 | 通过；各主机各有少量平台跳过 |
| Pro 通道 | `codex mcp list`、`claude mcp list` | 同左 | `agentify-desktop` 在列；Codex 条目含 `tool_timeout_sec = 2700` |
| 结果节点 | `ssh -o BatchMode=yes hmasd-wsl-node hostname` | 同左 | `LAPTOP-U9TDKC8A` |

WSL 主机上传给 agentify 的路径参数必须是 Windows 能打开的写法：`prompt` 内联，`responsePath` 用
`wslpath -w` 的输出。

## 6. 当前状态（2026-09-18）

- WSL 主机：第 5 节各项已在 `main` 上实测通过。
- Windows 主机：checkout 仍在 `23d6dc41d`，**尚未拉取今天的 `main`，第 5 节尚未在 Windows 上执行**。
  拉取前先处理 `C:/Projects/HMASD/.git/sequencer` 里自 2026-09-15 停着的 cherry-pick（完成或中止，由 owner 定）。
  Windows 上未推送的 `codex/hmasd-clerk`、不在 origin 上的 tag 与 bundle 在任何 `worktree prune`/`gc` 之前先推送或打包。
- 已知与主机无关的 4 个陈旧测试失败在 `tests/production_backend_policy_test.py`
  （RIDGEGATE 注册表断言、RCLE 旧源码摘要），属于归档方向，未改动。

本节是状态快照；Windows 自检通过后由执行它的会话更新这一节。背景与逐项改动见
[2026-09-18 变更记录](../Claude_docs/changes/2026-09-18-wsl-second-host-enablement.md)。
