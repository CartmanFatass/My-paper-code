# WSL 项目配置验收（2026-09-12）

本记录覆盖 main、17 个有分支工作树和 2 个保留的 detached 快照。研究继续暂停。
当前配置文件专项清单共 346 项，范围为项目配置、测试/构建入口及新环境记录；
排除 temp/logs/runtime 历史记录、文档、冻结 CodexBechmark 夹具和依赖缓存目录。
专项范围内未发现 `.env` / `.env.*` 文件。更广的全部文本路径扫描见
`WSL_PATHS_20260912.md`，包含上述历史文本和隐藏文件。

| 配置 | 处置及验证 |
| --- | --- |
| `.codex/config.toml` | 18 个维护中的 checkout 使用 `/mnt/c/Program Files/nodejs/node.exe` 启动 Windows Agentify；Windows 模块参数保留。实际 `codex mcp get agentify-desktop --json` 在每个 checkout 读回此入口。 |
| `.codex/agents/*.toml` | 相对 `config_file` 均解析到各自工作树内；保留各分支既有角色、模型与推理设置。20 个 checkout 的 `codex features list` 均成功。 |
| `.codex/hmasd-compute.toml` | 控制端继续用 `local_linux` / `hmasd-control`；新增显式 `local_linux_cpu`。远端默认 `wsl_4070`、Windows 回退节点及实验约束不变。 |
| `configs/scientific-capabilities-v1.toml` | 两项已启用能力改用独立 Linux 分析环境及本工作树内的 manifest；18 个 checkout 的 `doctor --id networkx` 均通过。其他能力状态保留。 |
| `pytest.ini`、`tests/AGENTS.md`、`CLAUDE.md` | 测试入口使用明确环境与本次调用的独立临时目录；原 pytest 发现规则和禁用 cache 设置不变。 |
| `.claude/settings.json` | 现有规则使用相对路径，保留原内容。 |
| Git 项目配置 | 未发现 `core.worktree`、`core.hooksPath`、`core.sshCommand` 或 include 路径覆盖；所有工作树的 Git 元数据已指向 native main。 |
| Git 换行读取 | 收尾时在 native 仓库本地设置 `core.autocrlf=input`，24 份日志的 Git blob 与磁盘字节均未改变，纯 CRLF/LF diff 已清除；见 `WSL_COPY_AND_GIT_20260912.md`。 |
| `environments/`、`requirements/` | 新 Linux 环境有独立版本清单和重建命令；旧 Windows/GPU 导出及 win-64 conda lock 保留其原始用途。 |

18 个维护中的 checkout 共解析 243 份 `.codex` 与能力目录 TOML，均成功；所有新入口
及其 manifest 均存在。能力目录现有测试为 2 passed，Linux CPU 原生 loader 的现有
编译加载测试为 2 passed。版本、编译器及平台边界见 `environments/README.md`。

## 保留项

- `configs/execution_kernel_v1.json` 固定了外部 Windows CLI 的源码哈希和 ledger。
  当前 scripts/tools/tests/控制指令中未找到调用方；保留绑定与 ledger，不启动其中的
  authority commands，也不把该历史绑定改成未经验证的 Linux 服务。
- `.codex/hmasd-monitor.toml` 的 `primary_checkout` 已改为 native main；
  `monitor_checkout` 仍记录旧任务 cwd。项目根目录修改不会重绑该任务。
- 四个较旧的方向分支仍有 `.codex/hmasd-portfolio.toml`，记录已退役的 native
  Portfolio 端点；当前 main 的 Portfolio 使用 Pro 节点。保留历史 ID/cwd，不激活旧端点。
- 两个 detached 快照保留原 SHA 和字节，实际 CLI 仍读回其历史 `node` 入口；它们是
  固定版本快照，不能作为已适配 WSL 的日常工作入口。

## 用户配置层与验收方法

当前 Desktop 任务实际使用 `CODEX_HOME=/mnt/c2/Users/fires/.codex`，其用户配置已存在
native main 的 trusted 记录。本次未修改用户配置，也未合并独立的
`/home/fires/.codex/config.toml`。在其他终端启动 Codex 时，应先确认实际配置目录和 cwd。

一次隔离 SQLite 的 app-server 配置读取探针在 initialize 阶段 30 秒超时，进程已终止，
未获得 `config/read` 响应，也未使用生产 SQLite。有效入口改用实际 CLI 的只读
`mcp get` / `features list` 验证；本记录不声称取得完整的 app-server 配置层回执。

专项清单、逐工作树 CLI 读回、保留项与验收记录：
`/home/fires/migration-records/hmasd-wsl-20260912/astra-desktop-repair/environment-audit/`。
