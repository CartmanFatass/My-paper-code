# 切到 WSL agent environment 前要改的 Codex 配置

2026-09-10。适用范围：把 Codex 桌面版的 agent environment 从 Windows native 改为
Windows Subsystem for Linux。桌面应用本身继续留在 Windows。

本文只谈配置。每一条的依据是 Codex 官方配置文档（引文见附录 A），每一条的现状值是本机
实测（附录 B）。没有改动仓库任何受控文件。

---

## 0. 结论

切换后会有五处配置失效。其中第一处**静默失效**，不报错，只是本仓库的七个 agent 定义、
`multi_agent_v2`、40 线程上限和 agentify MCP 全部不再生效。

落地方式不是直接改 `config.toml`，那个文件由应用生成并持续重写。文档给的机制是
profile 覆盖层。第 3 节给出可以直接写的文件内容。

有两处我改不了，需要 owner 决定，见第 4 节。

---

## 1. 五处失效点

| 配置项 | 现状值 | WSL 下的问题 | 改成 |
| --- | --- | --- | --- |
| `[projects.*]` 信任条目 | 51 条，全部为小写盘符路径，POSIX 键 0 条 | 项目路径变为 `/mnt/c/Projects/HMASD`，匹配不上，项目未信任，项目级 `.codex/config.toml` 整份不加载 | 补一条 POSIX 键 |
| `[mcp_servers.node_repl]` | command 为 `node_repl.exe`，env 含 `node.exe` 路径与命名管道 | Linux 侧无法启动 | `enabled = false` |
| `[mcp_servers.agentify-desktop]` | `command = "node"`，args 为 `C:\Projects\agentify-desktop\...` | Linux 的 node 拿到 Windows 路径 | command 指向 Windows 的 `node.exe`（见 4.1） |
| `notify` | `...\codex-computer-use.exe` | 可执行文件不存在 | `notify = []` |
| `[marketplaces.*] source` | 两条 `\\?\C:\Users\...` | `\\?\` 是 Win32 扩展长度前缀，Linux 无此语义；Linux 侧也没有对应目录 | 无干净改法（见 4.2） |

`[windows] sandbox = "elevated"` 在 WSL 下不生效，但也不冲突，不用动。

### 1.1 信任条目：唯一静默失效的一条

配置参考对 `projects.<path>.trust_level` 的说明是
"Untrusted projects skip project-scoped `.codex/` layers"，进阶配置页写得更全：

> For security, Codex loads project `.codex/` layers only when you trust the project.
> If the project is untrusted, Codex ignores project `.codex/` layers, including
> `.codex/config.toml`, project-local hooks, and project-local rules.

MCP 页面对项目级 MCP server 重复了同一条限制：**trusted projects only**。

本机 51 条信任条目的写法是小写化的 Windows 路径，例如：

```toml
[projects.'c:\projects\my-lib']
trust_level = "trusted"
```

WSL 模式下同一个项目的路径是 `/mnt/c/Projects/HMASD`。链条是：
**路径形式变了 → 匹配不到信任条目 → 项目未信任 → 项目级配置整份不加载。**

对本仓库，失效的是 `C:\Projects\HMASD\.codex\config.toml` 里的全部内容：
七个 `[agents.HMASD*]` 定义、`[features] multi_agent_v2`、
`[agents] max_concurrent_threads_per_session = 40`、`[agents] interrupt_message`，
以及 `[mcp_servers.agentify-desktop]`。

**文档没有说明跨 Windows 与 POSIX 两种路径形式时键如何归一化。**
所以补条目是必须的准备，切换后还要按第 5 节确认它确实生效了。

### 1.2 node_repl

这个 MCP server 的每一处都是 Windows 专用：

```toml
[mcp_servers.node_repl]
command = 'C:\Users\fires\AppData\Local\OpenAI\Codex\runtimes\cua_node\<hash>\bin\node_repl.exe'

[mcp_servers.node_repl.env]
NODE_REPL_NODE_PATH        = 'C:\...\node.exe'
NODE_REPL_NODE_MODULE_DIRS = 'C:\...\node_modules'
NODE_REPL_TRUSTED_SERVICES = '{"browser":"C:/Users/fires/.codex/plugins/cache/..."}'
SKY_CUA_NATIVE_PIPE_DIRECTORY = '\\.\pipe\codex-computer-use-<uuid>'
CODEX_CLI_PATH             = 'C:\...\Codex\bin\<hash>\codex.exe'
```

命名管道 `\\.\pipe\...` 尤其没有 Linux 对应物。配置参考给了正式的关闭方式，
`mcp_servers.<id>.enabled`，说明是 "Disable an MCP server without removing its configuration"。

关于 `CODEX_CLI_PATH`：它**不在配置参考里**，在本机只是传给这一个 MCP server 的环境变量，
不是全局的 CLI 定位器。关掉 `node_repl` 之后它不再被使用。

### 1.3 notify

配置参考的定义是 `array<string>`，"Command invoked for notifications; receives a JSON
payload from Codex"。本机的值指向一个 `.exe`。

同一份文档说明项目级配置会忽略 `notify` 并在启动时打印警告，所以它只在用户级或 profile 生效，
可以在 profile 里置空。

---

## 2. 为什么不能直接改 `config.toml`

这些路径是应用自己生成并持续重写的，不是手写的。本次会话内实测：
`config.toml` 在 22:01:55 被重写过一次，其中 `runtimes\cua_node\<hash>` 的哈希
与两小时前那次读取不同。直接改会被覆盖。

文档给出的分环境机制是 profile。层叠顺序由低到高：

1. 用户级 `~/.codex/config.toml`
2. profile 覆盖层 `~/.codex/<profile-name>.config.toml`
3. 项目级 `.codex/config.toml`，自工作目录向上逐层加载
4. CLI 覆盖

> Profiles let you save named configuration layers and switch between them from the CLI.

两点注意：

- profile 不随 agent environment 自动切换。`profile` 是一个配置键，选中后全局生效，
  所以改 agent environment 时要同时改它。
- **项目级优先于 profile。** 所以项目 `.codex/config.toml` 里的条目覆盖不掉，
  只能改那个文件本身，见 4.1。

本机目前没有任何 profile 文件。

---

## 3. 可以直接写的 profile

新建 `C:\Users\fires\.codex\wsl.config.toml`：

```toml
# 切到 WSL agent environment 时，在 config.toml 里设 profile = "wsl"

# 1. 让 WSL 形式的项目路径被信任，否则项目级 .codex/config.toml 整份不加载
[projects."/mnt/c/Projects/HMASD"]
trust_level = "trusted"

# 2. 关掉只能在 Windows 启动的 MCP server
[mcp_servers.node_repl]
enabled = false

# 3. 通知命令在 Linux 侧不存在
notify = []
```

然后在 `config.toml` 里设 `profile = "wsl"`，切回 Windows 时删掉这一行。

文档没有说明 profile 覆盖一个表时是整表替换还是逐键合并。
如果是整表替换，第 2 项写成 `[mcp_servers.node_repl] enabled = false` 会丢掉
原有的 `command` 等键——但既然目的就是关掉它，这不影响结果。
第 1 项是新增条目，不涉及合并。

---

## 4. 两处需要 owner 决定

### 4.1 `agentify-desktop` 必须改在项目级配置里

按第 2 节的层叠顺序，项目级优先于 profile，所以这一条覆盖不掉。
`C:\Projects\HMASD\.codex\config.toml` 现在是：

```toml
[mcp_servers.agentify-desktop]
command = "node"
args = ['C:\Projects\agentify-desktop\bin\agentify-desktop.mjs', "mcp"]
```

Windows 下 `node` 从 PATH 解析到 `C:\Program Files\nodejs\node.exe`。
WSL 下 `node` 解析到 Linux 的 node，拿到 Windows 路径参数会失败。

要让它在 WSL 下工作，必须经 interop 调 Windows 的 node，参数保持 Windows 形式：

```toml
[mcp_servers.agentify-desktop]
command = "/mnt/c/Program Files/nodejs/node.exe"
args = ['C:\Projects\agentify-desktop\bin\agentify-desktop.mjs', "mcp"]
```

两个问题需要 owner 定：

- 这个文件属于 Codex 控制面，按 CLAUDE.md Claude 会话不得编辑。
- 这样改之后它在 Windows 模式下就不对了。要两边都能用，
  得把这一条从项目级挪到两个 profile 里，或者接受切换时手工改。

同名条目在用户级 `config.toml` 里也有一份（第 330 行起），内容相同，同样的问题。

### 4.2 `marketplaces` 没有干净解

配置参考里 `marketplaces.<name>` 只有四个键：`source_type`、`source`、`ref`、
`sparse_paths`。**没有 `enabled`。**

`source` 的说明是 "Use an absolute path for a local source"。本机两条：

```toml
[marketplaces.openai-bundled]
source = '\\?\C:\Users\fires\.codex\.tmp\bundled-marketplaces\openai-bundled'

[marketplaces.openai-primary-runtime]
source = '\\?\C:\Users\fires\.cache\codex-runtimes\codex-primary-runtime\plugins\openai-primary-runtime'
```

`\\?\` 是合法的 Windows 绝对路径前缀，在 Linux 侧不是；改成 `/mnt/c/...` 也无意义，
因为那两个目录里是 Windows 侧的插件副本。

这一条只能在切换后观察：它是致命错误，还是仅仅一条启动告警、相关插件不可用。

---

## 5. 切换后要验证的四项

| 检查 | 判据 | 对应本文 |
| --- | --- | --- |
| 项目是否仍为 trusted | 项目级键生效，例如 `[agents.HMASD*]` 仍可见 | 1.1 |
| 启动是否有配置告警 | 无 Windows 路径相关告警 | 1.2、1.3 |
| marketplaces 的表现 | 致命还是告警 | 4.2 |
| `windows_wsl_setup_acknowledged` | 切换过程中是否出现该引导，事后该键是否写入 | 附录 B |

任一项失败的回滚方式：从托盘完全退出应用，把 `%USERPROFILE%\.codex\config.toml` 里
`[desktop] runCodexInWindowsSubsystemForLinux` 改回 `false`，删掉 `profile = "wsl"`，
再启动。应用运行期间改会被覆盖。

---

## 附录 A 文档依据

全部引自 Codex 官方文档。

**配置目录**（Windows 应用页）：

> The Windows app uses the same Codex home directory as native Codex on Windows:
> `%USERPROFILE%\.codex`.

> If you also run the Codex CLI inside WSL, the CLI uses the Linux home directory by default,
> so it doesn't automatically share configuration, cached auth, or session history with the
> Windows app.

这一条说明切换 agent environment 不改变 app 的配置目录，因此第 1 节的问题确实会被
Linux 侧的 app-server 读到。`/home/<user>/.codex` 是另外安装的 WSL CLI 的家目录，与本文无关。

**信任与项目级层**（进阶配置页、配置参考、MCP 页）：

> For security, Codex loads project `.codex/` layers only when you trust the project.
> If the project is untrusted, Codex ignores project `.codex/` layers, including
> `.codex/config.toml`, project-local hooks, and project-local rules.

> `projects.<path>.trust_level`：Mark a project or worktree as trusted or untrusted
> (`"trusted"` | `"untrusted"`). Untrusted projects skip project-scoped `.codex/` layers.

> you can also scope MCP servers to a project with `.codex/config.toml` (trusted projects only)

**层叠顺序与 profile**（进阶配置页）：

> Profiles let you save named configuration layers and switch between them from the CLI.

profile 文件位于 `$CODEX_HOME/<profile-name>.config.toml`，用 `--profile <name>` 选中；
顺序为用户级、profile、项目级、CLI 覆盖。

**键定义**（配置参考）：

> `mcp_servers.<id>.enabled` (boolean)：Disable an MCP server without removing its configuration.

> `notify` (array<string>)：Command invoked for notifications; receives a JSON payload from Codex.

> `marketplaces.<name>.source` (string)：Git repository location or local marketplace root
> directory. Use an absolute path for a local source.

> `windows.sandbox`：`unelevated | elevated`，原生 Windows 沙箱模式。

> `windows_wsl_setup_acknowledged` (boolean)：记录 Windows 侧针对 WSL 配置的 onboarding 确认。

项目级配置忽略的键包括 `notify`，遇到时在启动打印警告。

## 附录 B 本机配置快照（2026-09-10 实测）

| 项 | 值 |
| --- | --- |
| 桌面应用 | `OpenAI.Codex` 26.903.8094.0 |
| 用户级配置 | `C:\Users\fires\.codex\config.toml`，990 行，22:01:55 被应用重写过 |
| `[projects.*]` | 51 条，全部盘符键，POSIX 键 0 条 |
| 非 `[projects.*]` 的 Windows 绝对路径 | 7 处：`notify`、两条 marketplace `source`、`node_repl` 的 command 与三个 env 值 |
| profile 文件 | 无 |
| `profile` 键 | 未设 |
| `windows_wsl_setup_acknowledged` | `config.toml` 与 `.codex-global-state.json` 中均不存在 |
| `[windows]` | `sandbox = "elevated"` |
| `[desktop]` | `runCodexInWindowsSubsystemForLinux = false`，`integratedTerminalShell = "gitBash"` |
| 项目级配置 | `C:\Projects\HMASD\.codex\config.toml`，含七个 agent 定义与 `mcp_servers.agentify-desktop` |
| Windows node | `C:\Program Files\nodejs\node.exe` |
| WSL | Ubuntu-24.04，WSL2；WSL1 自 Codex 0.115 起不支持 |
| WSL 内 Codex CLI | `/home/fires/.local/bin/codex`，0.154.0，应用不会自动安装它 |

复现这份快照：

```powershell
# 信任条目的形式与数量
Select-String -Path C:\Users\fires\.codex\config.toml -Pattern '^\[projects\.' | Measure-Object
# Windows 绝对路径（排除 projects 表）
Select-String -Path C:\Users\fires\.codex\config.toml -Pattern '[A-Za-z]:\\|\\\\\?\\|\.exe'
# 文档化的 WSL onboarding 键
Select-String -Path C:\Users\fires\.codex\config.toml -Pattern 'windows_wsl_setup_acknowledged'
```
