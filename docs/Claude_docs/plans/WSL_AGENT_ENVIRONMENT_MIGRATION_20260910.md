# Codex agent environment 迁移 WSL：实测评估与推进顺序

2026-09-10，Claude Code（Opus 5）咨询任务。没有改动仓库任何受控文件，没有改动
`.codex/`、`.agents/`、`AGENTS.md`，没有运行任何 result-bearing 实验，没有消耗任何科学对象。
仓库之外执行过一次可逆操作：7.1 第 3 项的 WSL 二进制缓存改名。
所有性能数字都在本机（主机名 `Jacob`）实测，命令见附录 A。更正见第 10 节。

---

## 0. 结论

三句话：

1. **切换前有一份按官方配置文档推出的准备清单，不做完就会出问题。** 最关键的一条是
   信任条目：本机 51 条全部以 Windows 盘符为键，WSL 下项目路径变成 `/mnt/c/...`，
   匹配不上；而文档规定未信任的项目不加载任何项目级 `.codex/` 层。结果是本仓库的
   七个 agent 定义和 agentify MCP **静默失效**。完整清单见 6.3。
   上次崩溃的具体成因未定，初版归给上游缺陷是从 issue 反推的，已收回（见第 10 节）。
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

**这一节初版给出的是一个从上游 issue 反推的单一归因，证据不足，已收回。**
现在分成"本机可查的事实"和"外部可参考的同期缺陷"两部分，不再给单一结论。

### 2.1 本机可查的：配置里的路径冲突

owner 的回忆是当时发现了路径冲突。本机配置支持这个方向：用户级配置里有 7 处
Windows 绝对路径（含两条 `\\?\` 扩展长度前缀和一条指向 `codex.exe` 的
`CODEX_CLI_PATH`），51 条项目信任条目全部以 Windows 盘符为键，项目级配置里还有一条
Windows 路径的 MCP 参数。完整清单见 6.3。按 6.2 的文档说法，app 在 WSL 模式下加载的
正是这份配置，所以这些条目会被 Linux 侧的 app-server 读到。

本文没有当时的崩溃日志，无法把崩溃与其中某一条对应起来。**具体是哪一条，以
owner 当时的观察为准。**

### 2.2 外部可参考的：同期的上游缺陷

同一时间窗口内上游确有多条相关记录（附录 C），按时间分成两代：

**第一代，启动即失败。** 应用的相对路径投放步骤去 `app\resources\codex` 取 Linux 二进制，
而 MSIX 包里只有 `codex.exe`，于是报 `Unable to locate the Codex CLI binary`。
对应 issue #28103、#30094、#28212，影响 26.609.4994.0 一线版本。

**第二代，能启动但功能坏。** 26.820 / 26.825 上新建会话失败于
`AbsolutePathBuf deserialized without a base path`（#40786），
切到 WSL 后项目增删失效（#41290），
所有线程失败于 `invalid transport in mcp_servers.codex_app`（#40732）。

本机 `~/.codex/bin/wsl/4f759bc6b64517c4/codex` 的时间戳是 8 月 28 日，与
`.codex-global-state.json` 的同期备份对得上，所以那次尝试在时间上落在第二代窗口内。
**时间吻合不等于成因。** 这些 issue 说明同期存在什么缺陷，不说明本机崩溃是哪一条造成的；
2.1 的配置路径冲突是同样成立的候选，且可以在本机直接查证。

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

### 3.5 工作树体积的构成

本节的数字来自对 `temp/` 顶层 1063 个条目的逐项扫描（脚本与判定规则见 7.1）。

| 构成 | 条目 | 体积 | 文件数 |
| --- | --- | --- | --- |
| `.git` | — | 1.30 GiB | — |
| `temp/` 中需要保留的部分 | 90 | 23.51 GiB | 146163 |
| `temp/` 中无引用且陈旧的 scratch | 973 | 1.02 GiB | 56482 |
| 其余源码与文档 | — | 约 1.1 GiB | 10628（跟踪） |

保留部分里 16.82 GiB 是 `temp/directions/`，即 AGENTS.md 约定的 scratch 根，
里面是各方向实验的运行根；5.25 GiB 是 `temp/cm-model-comparison/`。
**这两部分都被已提交的 intake 文档按路径直接引用为证据**，不是残留。

两个推论，都与迁移直接相关：

- **`temp/` 的绝大部分不是垃圾。** 真正可回收的只有 1.02 GiB，占体积 3.7%，
  但占文件数 28%。清理它的收益在文件数，不在空间。
- **这 23.5 GiB 证据不在 git 里**（`.gitignore` 第 50 行 `/temp/**`）。
  所以"迁移只要 `git clone` 1.3 GB"这个说法是错的，见 7.3 步骤 3。

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

不是性能，是下面四条。6.3 是其中唯一需要你动手改配置的一条。

### 6.1 Codex 桌面版 WSL 模式的可靠性

8 月底那批功能缺陷（#40786、#41290、#40732）在 26.903 上是否修复，没有公开依据。
必须自己冒烟。冒烟集见 7.2。

### 6.2 Codex home：文档怎么说，以及一条与之矛盾的缺陷报告

**官方文档的说法是明确的，且不带 agent environment 这个条件：**

> The Windows app uses the same Codex home directory as native Codex on Windows:
> `%USERPROFILE%\.codex`.

> If you also run the Codex CLI inside WSL, the CLI uses the Linux home directory by default,
> so it doesn't automatically share configuration, cached auth, or session history with the
> Windows app.

所以按文档，**切换 agent environment 不改变 app 的配置目录**。桌面应用始终用
`%USERPROFILE%\.codex`；`/home/fires/.codex` 是你另外装的 WSL Codex CLI 的家目录，
两者本来就是分开的两套东西，不是同一套配置的两个读取者。

本机的直接证据与文档一致：上次崩溃后，改回 Windows 侧 `config.toml` 里的
`[desktop] runCodexInWindowsSubsystemForLinux` 就恢复了启动。
如果 app 读的是 Linux 那份，这个杠杆不会起作用。

**唯一的反面材料是 issue #22759**，一位用户报告 WSL 模式下 app-server 实际读了
WSL 的 `~/.codex`，并列出了由此产生的配置漂移。它是一份**尚未修复的缺陷报告，
不是文档化的行为**。本文没有在本机验证过它，也无法在不切换到 WSL 模式的前提下验证。
处理方式：把它当作切换后要检查的一项，放进 7.2 的冒烟集，而不是当作既定事实来做准备。

下面这张表列的是两个**本来就独立**的家目录当前各自的内容，供对照，
**不表示切换后 app 会采用右列**：

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

- **按文档，切换本身不需要你去改 WSL 侧那份 `config.toml`。** 它属于 WSL CLI。
  真正要做的是切换后核对 agent 实际生效的模型与审批策略，确认与 Windows 侧一致；
  不一致就说明 #22759 在这个版本上仍然成立，按 8 节回滚。
- **文档给出的共用方案有一个本机特有的坑。** 文档建议让 WSL CLI 指向 Windows 家目录：
  `export CODEX_HOME=/mnt/c/Users/<windows-user>/.codex`。
  在本机不要这样做：Windows 配置里 `mcp_servers.node_repl`、`mcp_servers.agentify-desktop`
  的 command 和 `notify` 都是 Windows 路径与 `.exe`，被 Linux 侧的 CLI 加载会直接出配置
  错误，正是 #40732 那一类症状。要共用就必须先把这些条目拆成平台相关的两份。
  这条针对的是 CLI 的配置共用，与 app 切不切 WSL 无关。

顺带一条与迁移无关但值得知道的事实：如果将来确实要让 WSL 侧也能驱动 Agentify，
它可以留在 Windows 侧由 WSL 通过 interop 调用，但 MCP 的 command 必须改写成 interop
形式，不能照抄 `command = "node"`。按 3.3 的实测，这种调用每次 38–81 ms。

### 6.3 按官方配置文档推出的切换前清单

本节的每一条都来自 Codex 的配置文档，不是从 issue 反推的。

#### 6.3.1 最重要的一条：项目会变成未信任，于是项目级配置整份失效

文档对信任与项目级配置层的规定：

> For security, Codex loads project `.codex/` layers only when you trust the project.
> If the project is untrusted, Codex ignores project `.codex/` layers, including
> `.codex/config.toml`, project-local hooks, and project-local rules.

MCP 页面重复了同一条：项目级 MCP server 是 **trusted projects only**。

信任条目的键是路径。本机 51 条全部是小写化的 Windows 盘符路径，例如
`[projects.'c:\projects\my-lib']`，POSIX 键 0 条。而 WSL 模式下同一个项目的路径是
`/mnt/c/Projects/HMASD`。

于是链条是：**路径形式变了 → 匹配不到信任条目 → 项目未信任 → 项目级
`.codex/config.toml` 整份不加载**。对本仓库，这意味着七个 `[agents.HMASD*]` 定义、
`[features] multi_agent_v2`、`[agents] max_concurrent_threads_per_session = 40`
以及 `mcp_servers.agentify-desktop` 全部静默失效，而不是报错。

文档没有写跨 Windows/POSIX 两种路径形式时键如何归一化，所以这一条需要在 7.2 里实测确认。
准备动作是明确的：切换前为 `/mnt/c/Projects/HMASD` 补一条信任条目。

#### 6.3.2 用户级配置里的 Windows 专用路径

按 6.2，app 在两种 agent environment 下用的都是 `%USERPROFILE%\.codex`。
所以 WSL 模式下，Linux 侧的 app-server 加载的正是下面这份配置。

用户级 `%USERPROFILE%\.codex\config.toml`（990 行，2026-09-10 实测）：

| 位置 | 内容 | 在 Linux 侧的问题 |
| --- | --- | --- |
| `notify` | `C:\...\codex-computer-use.exe` | 可执行文件不存在 |
| `[marketplaces.openai-bundled] source` | `\\?\C:\Users\fires\.codex\.tmp\...` | `\\?\` 是 Win32 扩展长度前缀，Linux 无此语义 |
| `[marketplaces.openai-primary-runtime] source` | `\\?\C:\Users\fires\.cache\...` | 同上 |
| `[mcp_servers.node_repl] command` | `...\node_repl.exe` | 可执行文件不存在 |
| `[mcp_servers.node_repl.env] NODE_REPL_NODE_PATH` | `...\node.exe` | 同上 |
| `[mcp_servers.node_repl.env] NODE_REPL_TRUSTED_SERVICES` | 内嵌 `C:/Users/...` 服务路径 | 解析不到 |
| `[mcp_servers.node_repl.env] CODEX_CLI_PATH` | `C:\...\Codex\bin\<hash>\codex.exe` | **正是 #28086 警告的那个变量指向 Windows 二进制** |
| `[projects.*]` | 51 条，**全部**以 Windows 盘符为键，POSIX 键 0 条 | WSL 下项目路径是 `/mnt/c/...`，一条都匹配不上，等于全部未信任 |

项目级 `C:\Projects\HMASD\.codex\config.toml`：

| 位置 | 内容 | 在 Linux 侧的问题 |
| --- | --- | --- |
| `[mcp_servers.agentify-desktop] args` | `['C:\Projects\agentify-desktop\bin\agentify-desktop.mjs', "mcp"]` | node 拿到 Windows 路径，起不来 |

关于 `marketplaces.<name>.source`，配置参考的原话是
"Use an absolute path for a local source"。`\?\C:\...` 是合法的 Windows 绝对路径，
在 Linux 侧不是。`notify` 的定义是 "Command invoked for notifications"，
文档同时说明项目级配置会忽略 `notify` 并在启动时打印警告，所以它只在用户级生效。

`CODEX_CLI_PATH` **不在配置参考里**。本机它出现在 `[mcp_servers.node_repl.env]` 下，
只是传给那一个 MCP server 的环境变量，不是全局的 CLI 定位器。
初版把它当成 #28086 那个全局变量，范围说大了。

还有一条要知道的性质：**这些路径是应用自己生成并持续重写的**，不是你手写的。
本次会话内实测，`config.toml` 在 22:01:55 被重写过一次，其中
`runtimes\cua_node\<hash>` 的哈希与两小时前那次读取不同。所以清理之后要复查，
应用更新或重启可能把 Windows 路径写回来。

#### 6.3.3 文档给出的分环境配置机制：profile

配置文档描述的层叠顺序，由低到高：

1. 用户级 `~/.codex/config.toml`
2. profile 覆盖层 `~/.codex/<profile-name>.config.toml`，需 `--profile <name>` 选中
3. 项目级 `.codex/config.toml`，自工作目录向上逐层加载
4. CLI 覆盖

> Profiles let you save named configuration layers and switch between them from the CLI.

这是文档给出的"同一台机器上保留两套设置"的正式机制。本机**没有任何 profile 文件**。
需要注意它不随 agent environment 自动切换：`profile` 是一个配置键，选中后全局生效，
所以切换 agent environment 时要同时改这个键。

#### 6.3.4 一个未完成的文档化步骤

配置参考里有一个键 `windows_wsl_setup_acknowledged`，布尔值，
用途是记录 Windows 侧针对 WSL 配置的 onboarding 确认。

本机 `config.toml` 与 `.codex-global-state.json` 里**都没有这个键**。
也就是说这台机器从未走完（或从未记录）那一步确认。切换时留意应用是否弹出该引导，
并在事后确认这个键出现。

#### 6.3.5 文档建议与本机实测冲突的一处

Windows 应用文档对项目位置的建议是：

> prefer storing projects on your Windows filesystem and accessing them from WSL through
> `/mnt/<drive>/...`，"more reliable than opening projects directly from the WSL filesystem"

这正是第 5 节里的配置 B。文档是从**可靠性**角度说的（`\wsl$` 下 git 检测不到等问题），
而 3.1 的实测是从**性能**角度说的：本仓库在这个组合下 `git status` 要 82 秒。
两者不矛盾但指向相反的选择。对本仓库的规模，B 不可用；文档的建议适用于小仓库。
文档同时说明：WSL1 自 Codex 0.115 起不再支持，且应用**不会**在发行版里安装 Codex CLI，
需要自备（本机已有 0.154.0）。

### 6.4 治理声明

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

1. **清理 `temp/` 中陈旧的 scratch。** 按 AGENTS.md §6，测试 scratch 由创建它的调用负责删除。
   按 3.5 的构成，可回收的是 973 个条目、1.02 GiB、56482 个文件，
   收益是把工作树的文件数减掉约 28%，从而加快目录遍历与 `git status`，**不是回收空间**。

   判定规则，任一命中即保留：名字被 HEAD 上任何提交内容引用；三天内有改动
   （避开仍在写的会话）；属于 `directions/`、`sessions/`、`README.md` 三个约定根。
   另外单独摘出三个不删：`test.bundle` 与 `vsp02.bundle` 是 §6 的恢复归档
   （其提交当前仍可达，属冗余，但归属工作树回收流程），
   `backup-missing-originals-20260828.zip` 是 `.agents/skills/` 的原件备份。

   分类与删除脚本在会话 scratchpad 下（`classify_temp.py`、`purge_temp.py`），
   后者不带 `--apply` 为空跑，删除时会重新 stat 每棵树，三天内被动过的一律跳过。
   空跑结果：970 个候选、0.84 GiB、0 跳过、0 失败。**截至本文提交尚未执行。**
2. **给 Defender 加排除。** 候选：`C:\Projects\HMASD`、
   `C:\Users\fires\.conda\envs\hmasd-amd-cpu`、以及 `python.exe`、`git.exe`、
   `node.exe` 三个进程排除。实时保护当前开启，排除列表需要管理员权限才能查看和修改。
   进程排除收益更大但削弱面更广，建议先只加路径排除。
   做完之后重测 3.2 和 3.4 的数字，用实测决定值不值。
3. **清掉过期的 WSL 二进制缓存。** ~~把 `%USERPROFILE%\.codex\bin\wsl\4f759bc6b64517c4\`
   改名而不是删除~~ **已完成（2026-09-10）**：已改名为
   `4f759bc6b64517c4.stale-20260828`，337 MB，随时可改回。
   这让应用在切到 WSL 时从 9 月 5 日的包内资源重新投放。这一步是 7.2 的前置。

### 7.2 受控试验，不碰 HMASD

在一个一次性项目上验证 WSL 模式，目标是判定 6.1 是否仍然成立。

前置条件：

- WSL2 Ubuntu-24.04 已是默认发行版且在运行（已满足）。WSL1 在本机不被支持。
- WSL 内已有 Codex CLI 0.154.0（已满足）。
- **不要设置 `CODEX_CLI_PATH` 指向 Windows 的 `codex.exe`**，那会通过 interop 起一个
  半 Windows 半 Linux 的混合会话（#28086）。
- 按 6.2，**不需要**预先改 `/home/fires/.codex/config.toml`。那是 WSL CLI 的家目录，
  按文档与 app 无关。切换前先把它当天的 mtime 记下来，作为下面那项检查的基线。
- **按 6.3 做完四件事**，这是切换前真正需要动手的准备：
  1. 为 `/mnt/c/Projects/HMASD` 补一条信任条目（6.3.1）。不补，项目级
     `.codex/config.toml` 整份不加载，七个 agent 定义和 agentify MCP 静默失效。
  2. 处理用户级配置里的 Windows 专用路径（6.3.2），或按 6.3.3 用 profile 覆盖。
  3. 留意 `windows_wsl_setup_acknowledged` 引导（6.3.4）。
  4. 清完记录 `config.toml` 的 mtime，切换后复查，应用会重写它。

冒烟集，五项对应五个已知缺陷，任一失败即回滚：

| 动作 | 判据 | 对应缺陷 |
| --- | --- | --- |
| 新建会话 | 不报 `AbsolutePathBuf` | #40786 |
| 新建项目、删除项目 | 两者都生效 | #41290 |
| 任意线程跑一条 shell 命令 | 不报 `invalid transport` | #40732 |
| 改一个文件并 `git status` | 结果正确 | 常规 |
| 核对 agent 实际生效的模型与审批策略 | 与 Windows 侧一致，且 `/home/fires/.codex` 没有新写入 | #22759 |
| 在一次性项目里确认项目级 `.codex/config.toml` 仍被加载 | 项目显示为 trusted，项目级键生效 | 6.3.1 |
| 确认启动时没有配置警告 | 无 Windows 路径相关告警 | 6.3.2 |

切换方式：设置里改 Agent environment，**从托盘完全退出**，再启动。不是关窗口。

### 7.3 迁移，只有在 7.2 全绿之后

顺序很重要，目的是避开第 5 节的 B 和 D 两个中间态。

1. 拿到 owner 对 `.codex/hmasd-compute.toml` 的批准（6.4）。
2. 在 WSL 里建好本项目的 Linux Python 环境，配方参考 `hmasd-wsl-node`，但用 CPU 版 torch。
   在旧位置验证它能跑通目标测试子集。
3. **迁移代码与迁移证据是两件事，都要做。**
   - 代码走 `git clone`，约 1.3 GiB 历史加约 1.1 GiB 检出。
   - `temp/` 下约 23.5 GiB 的证据**不在 git 里**，但被已提交的 intake 文档按路径引用。
     只 clone 会让那些引用全部断掉。先做 7.1 的清理，再把剩下的 `temp/` 一并搬过去。
   - **不要逐文件跨 9p 拷贝。** 146163 个文件按 3.1 的速率会非常慢。
     正确做法是在 Windows 侧打成单个归档，再在 WSL 侧解开，让跨界只发生在一个大文件上。
   - 所以一次性搬迁的实际量级是约 25 GiB，不是 1.3 GiB。它仍然是一次性的，
     你的原判断不受影响，但预算要按 25 GiB 排。
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
- **上次崩溃的具体成因未确定。** 没有保留当时的崩溃日志，本文只能给出两类候选：
  本机配置里可查证的 Windows 路径冲突（2.1、6.3），以及同期的上游缺陷（2.2）。
  两者都没有被排除，也没有被证实。

---

## 10. 更正记录

本节按发现顺序记录，全部发生在 2026-09-10 当日。

### 更正一：`temp/` 的构成

初版把 `temp/` 的绝大部分描述为"历次测试与实验没有清理的
残留"，并据此写出"迁移只要 `git clone` 1.3 GB"。对 1063 个顶层条目逐项扫描后，
这两条都不成立，已改写 3.5、7.1 与 7.3。

错在哪：初版只看了 `temp/` 的总体积和顶层条目数，没有区分其中哪些被已提交内容引用。
实测是 23.51 GiB 需要保留（其中 16.82 GiB 是约定的 scratch 根 `temp/directions/`，
被 intake 文档按路径直接引用为证据），只有 1.02 GiB 是真正无引用的陈旧 scratch。

影响：清理的收益从"回收 26 GB 空间"改成"减少 28% 的文件数"；
迁移的一次性搬运量从 1.3 GiB 改成约 25 GiB，因为那 23.5 GiB 证据不在版本库里，
只 clone 会让已提交文档中的证据引用全部断掉。
结论方向未变，全 Linux 终局在性能上仍然更便宜，一次性成本仍然是一次性的。

### 更正二：Codex home 的归属

初版在 6.2 断言"WSL 模式下 app-server 读的是 `/home/fires/.codex`，切过去之后模型、
审批、沙箱会静默变成另一套"，并据此要求切换前先对齐那份配置。这是错的。

错在哪：把一份**尚未修复的缺陷报告**（#22759）当成了当前的既定行为，并且没有区分
两个不同的读取者，即 Windows 上的桌面 UI 进程与 agent 侧的 app-server。
更根本的是，官方文档里就写着 app 用 `%USERPROFILE%\.codex`、不带 agent environment
这个条件，我应该先引文档再引 issue。owner 提出的反证也是直接成立的：
既然改回 Windows 侧 `config.toml` 就能恢复启动，app 显然在读 Windows 那份。

已改写 6.2，把它降级为"文档说不会，有一份缺陷报告说会，切换后验证"，
并把验证挪进 7.2 的冒烟集；7.2 里"先对齐 WSL 侧配置"这条前置条件删除。

顺带记录一个方法上的错误：为验证此事我去看了 `/home/fires/.codex` 的写入活动，
但那是 owner 自己在 WSL 里装的 Codex CLI 的家目录，它的活动对 app-server 说明不了任何事。
用错了仪器。

### 更正三：崩溃归因

初版第 2 节从上游 issue 反推出单一归因，并在结论里写成"是上游缺陷，不是配置错误"。
证据不足。owner 的回忆是当时发现了路径冲突，而本机配置里确实有充分的素材：
用户级 7 处 Windows 绝对路径、51 条全部以盘符为键的项目条目、一条指向 `codex.exe` 的
`CODEX_CLI_PATH`，项目级还有一条 Windows 路径的 MCP 参数。

已把第 2 节拆成 2.1（本机可查的配置路径冲突）与 2.2（同期的上游缺陷），
不再给单一结论；新增 6.3 作为切换前的路径清单；结论第 1 条相应改写。

### 更正四：应该先读配置文档

前三次更正之后，owner 指出真正的问题是我既没读本机内容也没读 OpenAI 文档，
只在 GitHub issue 之间打转。据此重读了配置文档（配置参考、进阶配置、MCP、Windows 应用），
6.3 整节改写为从文档推出的清单，其中 6.3.1 的信任条目链条是之前完全没有发现的，
而它是本机切换后最可能出问题的一条，因为它**静默失效**而不是报错。

同时收窄了一处范围：`CODEX_CLI_PATH` 不在配置参考里，本机它只是
`[mcp_servers.node_repl.env]` 下传给单个 MCP server 的环境变量，
不是 #28086 说的那个全局 CLI 定位器。

四次更正的共同原因是同一个：从外部材料推断本机状态，而没有先读一手文档与本机配置。
正确的顺序是文档、本机配置、实测，最后才是 issue。

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
| 缓存的 WSL 二进制 | `~/.codex/bin/wsl/4f759bc6b64517c4/codex`，268 MB，8 月 28 日；已于本日改名为 `...4517c4.stale-20260828` |
| `temp/` 构成 | 1063 个顶层条目；保留 90 个 / 23.51 GiB / 146163 文件，可删 973 个 / 1.02 GiB / 56482 文件 |
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
