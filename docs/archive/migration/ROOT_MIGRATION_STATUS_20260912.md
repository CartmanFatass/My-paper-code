# Root 亲自迁移记录（2026-09-12）

用户取消全部 Luna 任务后，由本迁移任务 Root 亲自重建并核对。研究保持暂停。整体迁移尚未完成：Desktop/旧任务入口没有切换，Windows 中无法读取的内容仍需保留原件。

## 已执行

- Windows 原项目和原工作树保持原样。
- 旧 WSL 仓库及工作树整体封存在 `/home/fires/migration-backups/hmasd-before-root-redo-20260912T020931/`，重新建立 `/home/fires/projects/HMASD` 和 19 个工作树。原始分支/提交一致，源工作树均无未提交改动；并未把各方向分支升级到主分支配置。
- Windows 的 154 个 Git 引用已通过完整 bundle 保全并逐项核对。目标同时保留原 Windows 和先前 WSL 的引用命名空间，Git 连接完整性检查通过。
- 从 Windows 原目录复制并逐文件哈希校验 193,856 个资产文件，共 28,651,427,301 字节。这是逐文件复制阶段的计数，不含其余由 Git checkout 生成的跟踪文件。目标冲突 0。工作树附属资产复制无错误。
- 根目录 `.git` 由 Git 重建；历史目录中的嵌套 Git 元数据、旧依赖环境仅按历史数据保留，未作为新的运行环境启用。明确排除可重建的 `__pycache__`、`.pytest_cache`、`*.pyc`、`*.pyo`。
- 主仓库的 12 个 TOML、控制端 Python 导入、owner console 帮助命令和既有远端 SSH 只读访问均通过。没有运行科学实验。本机控制 venv 不等于完整科学依赖环境。
- Desktop 状态数据库已用只读连接制作一致性备份，另保存配置快照；生产 Desktop 状态未修改。

## 未完成边界

- 去重后 797 个源目录及 1 个源文件读取失败。精确路径保存在外部 `ROOT_COPY_EXCEPTIONS.json`；原件没有删除，也没有修改 ACL。复制成功不能代替这些内容的保全确认。
- 当前 Desktop 的 UNC 项目创建错误仍存在，详见 `DESKTOP_WSL_PROJECT_FAILURE_20260912.md`。现有项目 ID、任务 ID、绑定和 cwd 未改写。原生后端接受 `/home` 路径不等于 Windows Desktop 完整入口已通过。
- Windows 原有审计改动和 24 个日志文件的原始字节被保留在目标工作区，没有作为迁移修改提交。源配置中的模型选择修复已在此前主仓库迁移提交中保留。

## 恢复与证据

完整逐文件清单、脚本、检查记录及 `ROOT_PERSONAL_MIGRATION_RECEIPT.json` 在 `/home/fires/migration-records/hmasd-wsl-20260912/`。Windows 全引用备份为其中 `windows-original-all-refs.bundle`；Desktop 快照位于 `root-desktop-backup/`。旧 WSL 封存副本保全取消时的实际状态，不声称它是迁移开始前的完整备份。

不删除 Windows 原件或封存副本。尚未经过 Desktop/旧任务实际入口验证，当前没有唯一可替代全部原件的已验收副本。后续由 Root 继续处理入口及读取例外，不重新委派 Luna，不唤醒研究任务。
