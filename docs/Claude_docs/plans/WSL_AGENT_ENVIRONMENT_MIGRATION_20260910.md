# Codex agent environment 迁移 WSL：实测评估与推进顺序

2026-09-10，Claude Code（Opus 5）只读咨询任务。本文没有修改仓库任何受控文件，没有改动
`.codex/`、`.agents/`、`AGENTS.md`，没有运行任何 result-bearing 实验，没有消耗任何科学对象。
所有性能数字都在本机（主机名 `Jacob`）实测，命令见附录 A。

---

## 0. 结论

三句话：

1. **上次崩溃是上游缺陷，不是配置错误。** 当时的桌面版没有随包发出 Linux 版 `codex`
   二进制，或者投放了过期的缓存。当前安装的 26.903.8094.0 已经带了 9 月 5 日的 Linux 二进制，
   这一类原因消失了。
2. **性能账上，全 Linux 终局确实比现状便宜，而且不是只便宜一点。** 进程创建快 33 倍，
   解释器启动快 4.4 倍，同侧逐文件读取快 3.8 倍。跨环境调用 Agentify 的代价是每次 38–81 ms，
   在任何合理的调用频率下都可以忽略。
3. **真正的阻塞项不是成本，是 Codex 桌面版 WSL 模式当前的可靠性，以及
   `.codex/hmasd-compute.toml` 里写死的控制面节点声明。** 前者要靠受控冒烟验证，
   后者需要 owner 批准才能改。

推荐顺序：先做完全可逆的准备和试验，WSL 模式通过冒烟集之后再迁项目。不要先搬项目。

---

## 1. 本文回答什么，不回答什么

回答：

- 上次崩溃的归因，以及当前版本是否仍然会崩。
- 把 agent 换到 WSL、把项目搬到 ext4，各自的实测代价与收益。
- 安全的切换步骤与回滚杠杆。
- 推进顺序，以及每一步的可逆性。

不回答：

- 26.903.8094.0 是否修好了 8 月底那批 WSL 功能缺陷。上游没有发布说明可查，只能靠冒烟验证。
- Linux 侧 pytest 与 torch 导入的实测耗时。本机 WSL 里没有本项目的 Python 环境，
  没有可比的测量对象，本文不给这两个数字。
- Defender 排除目录能挽回多少。读取排除列表需要管理员权限，本次没有提权。

---

## 2. 上次崩溃的归因

症状属于 Codex Windows 应用 WSL 模式的一个已知缺陷族，上游至今有多条记录（附录 C）。
按时间可以分成两代：

**第一代，启动即失败。** 应用的相对路径投放步骤去 `app\resources\codex` 取 Linux 二进制，
而 MSIX 包里只有 `codex.exe`，于是报 `Unable to locate the Codex CLI binary`。
对应 issue #28103、#30094、#28212，影响 26.609.4994.0 一线版本。

**第二代，能启动但功能坏。** 26.820 / 26.825 上新建会话失败于
`AbsolutePathBuf deserialized without a base path`（#40786），
切到 WSL 后项目增删失效（#41290），
所有线程失败于 `invalid transport in mcp_servers.codex_app`（#40732）。

本机 `~/.codex/bin/wsl/4f759bc6b64517c4/codex` 的时间戳是 8 月 28 日，与
`.codex-global-state.json` 的同期备份对得上，所以你那次尝试大概率落在第二代窗口里。

当前状态与那时不同的地方：

| 项目 | 当时 | 现在 |
| --- | --- | --- |
| 桌面应用版本 | 26.820 一线 | 26.903.8094.0 |
| 包内 Linux 二进制 | 缺失或过期 | 存在，`app\resources\codex`，9 月 5 日 |
| WSL 内 Codex CLI | 未确认 | 已装，`/home/fires/.local/bin/codex`，0.154.0 |
| 缓存的 WSL 二进制 | 即为问题本身 | 8 月 28 日，**比包内的旧，应当清掉让其重新投放** |

---

## 3. 本机实测

### 3.1 文件系统轴

合成基准，3000 个小文本文件，四种组合，冷热状态一致（均为创建后首次遍历再读取）：

| 操作 | 项目在 NTFS，从 Windows | 项目在 NTFS，从 WSL | 项目在 ext4，从 WSL | 项目在 ext4，从 Windows |
| --- | --- | --- | --- | --- |
| `find -type f`（枚举 3000） | 122 ms | 32 ms | 6 ms | 97 ms |
| `cat *.txt`（打开并读 3000） | 454 ms | 21458 ms | 119 ms | 49688 ms |

读法：

- **目录枚举在任何组合下都不是问题。** 跨界的元数据枚举甚至比本地 Windows 还快。
- **致命的是逐文件打开。** 跨界时 WSL 读 NTFS 慢 47 倍，Windows 读 ext4 慢 417 倍。
- **同侧比较，ext4 加 Linux 比 NTFS 加 Windows 快 3.8 倍**（119 ms 对 454 ms）。
  这一项是纯粹的迁移收益，与跨不跨界无关。

真实仓库上的对照，10628 个跟踪文件：

| `git status --porcelain` | 耗时 |
| --- | --- |
| Windows 侧 git | 76–105 ms |
| WSL 侧 git 走 `/mnt/c`，冷 | 113656 ms |
| WSL 侧 git 走 `/mnt/c`，热第一次 | 109925 ms |
| WSL 侧 git 走 `/mnt/c`，热第二次 | 82609 ms |

热缓存基本没用，因为 9p 上每次 `open` 都要往返。这条数字说明一件事：
**把 agent 放进 WSL 而项目留在 `/mnt/c`，是四种配置里唯一不可用的那一种。**

### 3.2 进程与解释器轴

这一轴是我先前漏掉的，也是这个仓库真正的重复成本所在。

| 操作 | Windows | WSL（ext4） | 倍数 |
| --- | --- | --- | --- |
| 进程创建，`git --version` × 50，PowerShell 原生 | 33.3 ms/次 | 1 ms/次 | 33× |
| 进程创建，`git --version` × 50，Git Bash | 35 ms/次 | 1 ms/次 | 35× |
| 进程创建，`cmd.exe /c exit` × 50（系统小程序，下限参考） | 13.3 ms/次 | — | — |
| Python 解释器启动，`-c pass` × 10 | 61 ms/次 | 14 ms/次 | 4.4× |
| `import torch` | 3348 ms | 未测量 | — |

33 倍这个数不是 Git Bash 的 fork 模拟造成的，PowerShell 原生调用也是 33.3 ms。
`cmd.exe` 的 13.3 ms 可以当作本机 Windows 进程创建的下限，其余是二进制体积、
`git.exe` 这层 shim、以及实时防护对每次映像加载的检查。Defender 实时保护当前是开启的。

### 3.3 跨环境调用轴

从 WSL 调用 Windows 可执行文件的单次代价：

| 调用 | 单次耗时 |
| --- | --- |
| `cmd.exe /c exit` × 10 | 38 ms |
| Codex 运行时自带的 `node.exe --version` × 3 | 81 ms |

**这条数字支持不迁移 Agentify 的判断。** Agentify Desktop 是低频调用，一次 Pro 往返也就
几次进程调用。按每天 20 次跨界调用、每次 81 ms 计，全天累计 1.6 秒。

作为对照，下一节里一次 pytest 收集是 37 秒。**一次测试收集的代价约等于 23 天的
Agentify 跨界开销。** 把 Agentify 当作迁移的阻塞点是量级上的误判，先前那个判断收回。

### 3.4 真实仓库上的锚点

| 项目 | 值 |
| --- | --- |
| `pytest -q --collect-only tests/experiments/candidates/` | 37175 ms，收集 6131 个测试，22 个收集错误 |
| 工作树体积 | 27565 MB |
| `.git` 体积 | 1330 MB |
| 跟踪文件数 | 10628 |

37 秒里一个测试都还没跑。这是进程创建、解释器启动、数千次模块导入、
每次导入的文件打开、以及实时防护逐次检查的复合结果，全部落在 3.1 和 3.2 两条慢轴上。
这才是这个仓库最大的重复性开销。

27.5 GB 的工作树里只有 1.3 GB 是版本历史，其余绝大部分是 `temp/` 下历次测试与实验
没有清理的残留（WSL 侧遍历时在其中撞到数百个权限拒绝的目录）。
所以"搬迁要拷 27 GB"是个伪成本，一次 `git clone` 加一次 checkout 就够。

---

## 4. 核心开销在哪：对先前判断的修正

我最初把问题框成"跨文件系统访问"，据此得出"搬过去只是把债换一侧背"。
把进程轴测出来之后，这个框架不成立。按量级重排，这个仓库的重复开销是：

1. **Python 与 pytest 的启动和导入，叠加 NTFS 逐文件打开与实时防护。**
   单次数十秒量级。这是最大的一项，而且每轮开发都要付。
2. **进程创建，33 ms 一次。** 一个 agent 会话几百到上千次调用，累计数十秒。
3. **跨界调用 Windows GUI 程序，38–81 ms 一次。** 低频，可忽略。
4. **agent 与项目分处两侧时的 9p 逐文件访问，47 至 417 倍。**
   这一项不是"必然要付的债"，而是一个配置错误的后果，只在你把两者拆开时才出现。

第 1 项和第 2 项不会因为"把 agent 换到 WSL 但项目留在 C 盘"而改善，只会因为
第 4 项而急剧恶化。它们只在**项目和解释器都在 ext4 上**时才消失。

所以你的原话是对的：`/mnt/c` 是永久债务，而复制粘贴只是短期开销。
我先前把 Agentify 列为搬不动的那一层，是把一个每天 1.6 秒的项当成了阻塞点。

---

## 5. 四种配置的账

| 配置 | agent 侧 | 项目位置 | 评价 |
| --- | --- | --- | --- |
| A 现状 | Windows 原生 | NTFS | 零跨界，但持续付第 1、2 项慢轴。可用，是当前基线。 |
| B 半迁 | WSL | NTFS（`/mnt/c`） | **不可用。** `git status` 82 秒。不要进入这个状态。 |
| C 全迁 | WSL | ext4 | 性能最优。第 1、2 项慢轴消失，只剩低频跨界调用。 |
| D 反向半迁 | Windows 原生 | ext4（`\\wsl.localhost`） | 最差。Windows 读 ext4 是 417 倍，比 B 还糟。 |

值得注意的是 B 和 D 都是"做了一半"的产物。从 A 到 C 的路径上，如果先切 agent 再搬项目，
中间会经过 B；如果先搬项目再切 agent，中间会经过 D。
**所以切换顺序必须是：先在一个一次性项目上验证 WSL 模式可用，再同时完成 agent 与项目的切换。**

---

## 6. 真正的阻塞项

不是性能，是下面三条。

### 6.1 Codex 桌面版 WSL 模式的可靠性

8 月底那批功能缺陷（#40786、#41290、#40732）在 26.903 上是否修复，没有公开依据。
必须自己冒烟。冒烟集见 7.2。

### 6.2 Codex home 分叉

WSL 模式下 app-server 读的是 `/home/fires/.codex/config.toml`，不是 Windows 那份（#22759）。
本机这两份差别很大：

| 键 | Windows `%USERPROFILE%\.codex` | WSL `/home/fires/.codex` |
| --- | --- | --- |
| `model` | `gpt-5.6-sol` | `gpt-6-astra` |
| `approval_policy` | `never` | 项目级 `on-request` |
| `sandbox_mode` | `danger-full-access` | 项目级 `workspace-write` |
| `[agents]` | 未设 | `max_concurrent_threads_per_session = 40`，`max_depth = 2` |
| 本项目 trust 条目 | 有（`c:\projects\hmasd`） | 无 |
| 插件 | 全套 bundled 与 primary-runtime | 无 |
| `mcp_servers` | `node_repl`、`agentify-desktop`，均为 Windows 路径 | 无 |

两条推论：

- 切过去之后 agent 的模型、审批策略、沙箱模式会**静默变成另一套**。必须在切换前
  把 WSL 侧的 `config.toml` 按意图对齐，不要指望 UI 里的设置生效。
- **不要用 `CODEX_HOME=/mnt/c/Users/fires/.codex` 去共用 Windows 那份。**
  Windows 配置里的 `mcp_servers.node_repl`、`mcp_servers.agentify-desktop` 的 command
  和 `notify` 都是 Windows 路径与 `.exe`，在 Linux 侧加载会直接出配置错误，
  这正是 #40732 那一类症状。要共用就必须先把这些条目拆成平台相关的两份。

`agentify-desktop` 这一条是可以留在 Windows 侧、由 WSL 通过 interop 调用的，
但 MCP 的 command 必须改写成 interop 形式，不能照抄 `command = "node"`。

### 6.3 治理声明

`.codex/hmasd-compute.toml` 目前写死：

```toml
control_plane_node = "local_windows"

[nodes.local_windows]
project_root = "C:/Projects/HMASD"
python = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"

[invariants]
control_plane_moves_remote = false
local_receipt_admits_remote = false
remote_receipt_admits_local = false
```

迁移会让 `project_root` 和 `python` 两个字段失真，也会让 AGENTS.md §7 的资源准入收据
换了语义：WSL 里测到的是 WSL 虚拟机的内存预算，不是 Windows 物理内存，而收据只对本节点有效。

`.codex/**` 属于 Codex 控制面，Claude 会话按 CLAUDE.md 不得编辑。
**迁移前需要 owner 明确批准这个文件的修改，并决定 WSL 侧算作 `local_windows` 的更新
还是一个新节点。** 这一条不是性能问题，但它在流程上先于迁移。

另外两条附带事实：

- 本机 WSL **不是** `hmasd-wsl-node`。后者是 192.168.1.12、用户 `wu`、
  主机 `LAPTOP-U9TDKC8A` 的另一台笔记本，带 RTX 4070，走 SSH。本机 WSL 没有 GPU。
- 那台节点上已经有一份 ext4 原生检出（`/home/wu/projects/HMASD`）和 Linux venv
  （Python 3.10.21，torch 2.7.0+cu118）。**它可以当作本机 Linux 环境的配方来源**，
  但 CUDA 那部分在本机 WSL 上用不上，本机需要的是 CPU 版。

---

## 7. 推进顺序

### 7.1 立刻可做，完全可逆，且不依赖迁移决定

这三件事在 A 配置下就能拿到收益，做完再谈迁移。

1. **清理 `temp/`。** 按 AGENTS.md §6，测试 scratch 由创建它的调用负责删除。
   目前它占了 27.5 GB 工作树的绝大部分，直接拖慢每一次 `git status` 和每一次目录遍历。
   注意不要删除仍在运行的调用的 scratch，也不要碰科学证据。
2. **给 Defender 加排除。** 候选：`C:\Projects\HMASD`、
   `C:\Users\fires\.conda\envs\hmasd-amd-cpu`、以及 `python.exe`、`git.exe`、
   `node.exe` 三个进程排除。实时保护当前开启，排除列表需要管理员权限才能查看和修改。
   做完之后重测 3.2 和 3.4 的数字，用实测决定值不值。
3. **清掉过期的 WSL 二进制缓存。** 把 `%USERPROFILE%\.codex\bin\wsl\4f759bc6b64517c4\`
   改名而不是删除，让应用从 9 月 5 日的包内资源重新投放。这一步也是 7.2 的前置。

### 7.2 受控试验，不碰 HMASD

在一个一次性项目上验证 WSL 模式，目标是判定 6.1 是否仍然成立。

前置条件：

- WSL2 Ubuntu-24.04 已是默认发行版且在运行（已满足）。WSL1 在本机不被支持。
- WSL 内已有 Codex CLI 0.154.0（已满足）。
- **不要设置 `CODEX_CLI_PATH` 指向 Windows 的 `codex.exe`**，那会通过 interop 起一个
  半 Windows 半 Linux 的混合会话（#28086）。
- 先按 6.2 把 `/home/fires/.codex/config.toml` 的模型、审批、沙箱、trust 条目对齐。

冒烟集，四项对应四个已知缺陷，任一失败即回滚：

| 动作 | 对应缺陷 |
| --- | --- |
| 新建会话 | #40786 |
| 新建项目、删除项目 | #41290 |
| 任意线程跑一条 shell 命令 | #40732 |
| 改一个文件并 `git status` | 常规 |

切换方式：设置里改 Agent environment，**从托盘完全退出**，再启动。不是关窗口。

### 7.3 迁移，只有在 7.2 全绿之后

顺序很重要，目的是避开第 5 节的 B 和 D 两个中间态。

1. 拿到 owner 对 `.codex/hmasd-compute.toml` 的批准（6.3）。
2. 在 WSL 里建好本项目的 Linux Python 环境，配方参考 `hmasd-wsl-node`，但用 CPU 版 torch。
   在旧位置验证它能跑通目标测试子集。
3. `git clone` 到 ext4，**不要拷贝工作树**。1.3 GB 而不是 27.5 GB。
4. 在新检出里跑一次 7.1 之后的 pytest 收集，与 37175 ms 对照，确认收益是真的。
5. 同一时间窗口内完成 agent 切换与项目切换，不要留下过夜的中间态。
6. 把 Windows 侧的旧检出保留一段时间作为回退，确认无引用后再按 AGENTS.md §6 的
   工作树回收流程处理，不要只是删目录。

迁移一并解决的两个老问题：

- **换行符分叉。** Windows 侧 git 的 `core.autocrlf` 是 `true`，WSL 侧未设置。
  现在两边操作同一个检出，WSL 侧 git 会把 5 个未被 `.gitattributes` 钉成 lf 的文件
  报成已修改（`.claude/` 下三个文件、`.gitattributes`、`.gitignore`），而 Windows 侧认为干净。
  全迁到 ext4 之后只有一侧的 git 接触工作树，这个问题自动消失。
  反过来说，**在半迁状态下必须先统一 `core.autocrlf`，否则会把整片 CRLF 写进索引。**
- **MAX_PATH。** ext4 上不存在。

---

## 8. 回滚

这个设置持久化在 `%USERPROFILE%\.codex\config.toml`：

```toml
[desktop]
runCodexInWindowsSubsystemForLinux = false
integratedTerminalShell = "gitBash"
```

应用起不来、进不了设置界面时的恢复路径：从托盘完全退出，手工把第一个键改回 `false`，
再启动。应用运行期间改会被覆盖。切换前请先备份两份 `config.toml` 和两份 `auth.json`。

注意 `integratedTerminalShell` 与 agent environment 是**两个独立设置**。
如果你只是想要一个 Linux shell 而不想动 agent，改这一个键就够，不承担本文其余任何风险。

---

## 9. 未测量项与本文限制

- Linux 侧的 pytest 收集耗时与 `import torch` 耗时未测量，本机 WSL 没有本项目的环境。
  第 7.3 步 4 就是为了补上这个数字再做判断。
- 26.903.8094.0 是否修复了 8 月底那批缺陷，无公开依据，只能靠 7.2 判定。
- Defender 排除的收益未测量，需要管理员权限。
- 3.1 的合成基准用的是 3000 个小文本文件，与真实仓库的文件大小分布不同。
  3.4 的 `git status` 与 pytest 收集是真实负载下的锚点，两者结论一致。
- 本次在 WSL 里对 `/mnt/c/Projects/HMASD` 跑过 `git status`（只读）。
  事后确认 Windows 侧工作树未发生改变，仍只有会话开始时的两个未跟踪文件。

---

## 附录 A 复现命令

文件系统轴，NTFS 侧（Git Bash）：

```bash
mkdir -p "$SCRATCH/f"; for i in $(seq 1 3000); do echo "line $i" > "$SCRATCH/f/file_$i.txt"; done
time find "$SCRATCH/f" -type f | wc -l
time cat "$SCRATCH/f"/*.txt | wc -l
```

同一组文件从 WSL 读，以及 ext4 基线：

```bash
wsl -e bash -c 'time find /mnt/c/<scratch>/f -type f | wc -l; time cat /mnt/c/<scratch>/f/*.txt | wc -l'
wsl -e bash -c 'mkdir -p /tmp/perf/f; for i in $(seq 1 3000); do echo "line $i" > /tmp/perf/f/file_$i.txt; done; time cat /tmp/perf/f/*.txt | wc -l'
```

ext4 从 Windows 读：

```bash
time cat '//wsl.localhost/Ubuntu-24.04/tmp/perf/f'/*.txt | wc -l
```

进程轴：

```powershell
$sw=[Diagnostics.Stopwatch]::StartNew(); for($i=0;$i -lt 50;$i++){ & git --version | Out-Null }; $sw.Stop(); $sw.ElapsedMilliseconds
```

```bash
wsl -e bash -c 'time (for i in $(seq 1 50); do git --version >/dev/null; done)'
```

跨界调用：

```bash
wsl -e bash -c 'time (for i in $(seq 1 10); do /mnt/c/Windows/System32/cmd.exe /c exit >/dev/null 2>&1; done)'
```

真实锚点：

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q --collect-only tests/experiments/candidates/
```

## 附录 B 本机环境快照（2026-09-10）

| 项 | 值 |
| --- | --- |
| 主机名 | `Jacob` |
| Codex 桌面版 | `OpenAI.Codex` 26.903.8094.0，MSIX |
| 包内 Linux 二进制 | `app\resources\codex`，258 MB，9 月 5 日 |
| 缓存的 WSL 二进制 | `~/.codex/bin/wsl/4f759bc6b64517c4/codex`，268 MB，8 月 28 日 |
| WSL | Ubuntu-24.04，WSL2，默认发行版，运行中；WSL1 不受支持 |
| WSL 用户 | `fires`，家目录 `/home/fires` |
| WSL 内 Codex CLI | `/home/fires/.local/bin/codex`，`codex-cli 0.154.0` |
| WSL 内 git | 2.43.0，`core.autocrlf` 未设置 |
| Windows git | `core.autocrlf = true` |
| Defender 实时保护 | 开启；排除列表需管理员权限查看 |
| `[desktop]` 当前值 | `runCodexInWindowsSubsystemForLinux = false`，`integratedTerminalShell = "gitBash"` |
| `[windows]` | `sandbox = "elevated"` |
| GPU 节点 | `hmasd-wsl-node`，192.168.1.12，用户 `wu`，主机 `LAPTOP-U9TDKC8A`，**另一台机器** |

## 附录 C 上游参考

- [ChatGPT desktop app for Windows](https://learn.chatgpt.com/docs/windows/windows-app)
- [#30094](https://github.com/openai/codex/issues/30094) 切到 WSL 后无法启动
- [#28086](https://github.com/openai/codex/issues/28086) 找不到随包二进制，`CODEX_CLI_PATH` 误用
- [#28103](https://github.com/openai/codex/issues/28103) MSIX 缺少 Linux 二进制
- [#28212](https://github.com/openai/codex/issues/28212) 请求安全恢复路径
- [#22759](https://github.com/openai/codex/issues/22759) WSL app-server 读 WSL 的 `~/.codex`
- [#40786](https://github.com/openai/codex/issues/40786) 新建会话 `AbsolutePathBuf` 失败
- [#41290](https://github.com/openai/codex/issues/41290) 切到 WSL 后项目增删失效
- [#40732](https://github.com/openai/codex/issues/40732) `invalid transport in mcp_servers.codex_app`
