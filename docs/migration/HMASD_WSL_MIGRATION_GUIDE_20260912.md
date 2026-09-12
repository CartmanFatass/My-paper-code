# HMASD 正式迁移说明（2026-09-12）

本次仅迁移基础设施，不恢复已暂停的研究，不新增实验或 Pro 请求。完整执行约束见同目录 HMASD_WSL_MIGRATION_SPEC_20260912.md。

日常继续使用原 HMASD 项目；native main 与方向工作树已是正式工作区。
复制尚存的源端权限缺口及大行数 diff 的换行原因见 `WSL_COPY_AND_GIT_20260912.md`。

## 目标布局

| 内容 | 迁移后位置/行为 |
| --- | --- |
| 主仓库 | /home/fires/projects/HMASD |
| 当前方向工作树 | /home/fires/projects/HMASD-worktrees 下，保持各自分支、提交及未提交内容 |
| 实验产物和历史运行记录 | 主仓库 temp/ 保持相对结构及文件原始内容 |
| 本机控制端 Python | /home/fires/.venvs/hmasd-control，依赖由验收记录给出 |
| 本机 CPU / 分析 Python | `/home/fires/.venvs/hmasd-linux-cpu` / `/home/fires/.venvs/hmasd-linux-science-tools`，见 `environments/README.md` |
| Desktop/Agentify | 继续运行在 Windows，Agent 已在 WSL |
| 远端实验节点 | 继续使用现有 hmasd-wsl-node / wsl_4070，/home/wu 路径不改变 |
| Windows 原仓库及工作树 | 保留，作为明确的回退来源；切换后不再双边同时日常写入 |

## 执行责任（用户最新指令）

四个 Luna 任务已全部取消。后续由当前迁移任务的 Root 亲自执行、核对和收尾；不唤醒研究 Root。

Windows 原项目及工作树保持原样。之前的 WSL 候选仓库和工作树已整体重命名封存在 `/home/fires/migration-backups/hmasd-before-root-redo-20260912T020931/`，随后重新创建目标。此备份保全的是取消时的候选状态，不代表迁移开始前曾有完整 WSL 备份，也不证明所有 Windows 文件已复制。

## 数据保全规则

1. 以实际 Git 祖先关系核对版本，不凭提交时间判断；保留两边独有提交与修改。
2. 区分源仓库的 CRLF/LF 展示差异与真正编辑，禁止批量换行符提交。
3. temp 并非可删除缓存；完整复制，不使用 rsync --delete。目标冲突内容先备份。
4. 保留个人笔记、记忆、被忽略的研究日志、运行 receipt；可重建 Python 缓存的排除必须记录。
5. Windows Git 工作树路径需转换和重建链接，不对 Linux 显示 prunable 的记录直接执行清理。
6. 不修改历史实验卡、固定请求、哈希、原始命令、研究结果或既有任务 ID。

## 验收顺序

- 数据阶段：提交与 refs 对齐；真实修改保留；工作树登记有效；证据文件校验，列出明确例外。
- 配置阶段：本机路径与 Linux 工具匹配；项目及七个 agent 的 TOML 能加载；依赖、短控制端检查、SSH 和 Windows 桥接边界有记录。
- 入口阶段：Desktop 项目及旧任务实际 cwd 切换到已验证的目标。复制文件并不自动改变任务 cwd。
- 若入口切换必须关闭 Desktop，则先完成备份、切换工具及其测试，再把关闭/重启作为最后一步交给用户执行，明确尚未完成的项目，不在线改写会话数据库。

## 当前使用与回退

用开始菜单 `Codex - WSL Repair` 启动已验证的可回滚适配器（安装包
`26.908.4834.0`）。原 HMASD 项目的主目录已正常保存为
`/home/fires/projects/HMASD`；原项目 ID、附加 remote-test 根目录及任务历史保留。
项目“1”曾用于入口验证，不是后续工作的必需项目。
本次没有直接写入生产 SQLite、global-state 或历史会话文件。

已有任务的 cwd 不随项目根目录自动更新。旧任务恢复时须明确指定已分配的 native
checkout，并检查实际 `pwd` 与 `git rev-parse --show-toplevel`；本次没有批量唤醒任务。
main 和各方向工作树的环境入口及检查范围见 `WSL_PATHS_20260912.md`。

CPU 和分析环境分别按 Windows 实际包版本重建，依赖检查和主要导入通过；Linux
C++ loader 的两个现有检查通过。解释器和包版本、明确省略项、编译器/BLAS 平台
边界及重建命令见 `environments/README.md`。远端节点和 Windows 专用工具继续沿用
原环境；安装完成不恢复研究或改写任何冻结实验条件。

完整退出后通过原官方快捷方式启动，可停用路径适配器。后续官方升级需重新核验。
若需要回到 Windows 项目，先保全 Linux 新增提交、修改和证据，再通过正常项目界面
选择已保留的 Windows 副本；不要用旧数据库覆盖新任务历史，也不要双边同时日常写入。
迁移记录中的旧 staging/数据库修补脚本不是当前切换方法。

## 故障与扫描记录

原缺陷是 Windows Desktop 传入盘符或 UNC 项目路径，而 Linux 后端按 POSIX 绝对
路径解析；仅改变文件选择器里的 UNC 拼写不足以修复。当前适配器只在项目
create/import/update 请求边界转换路径，真实创建和更新均已验证。

全部 20 个 native checkout 已扫描 Windows 路径残留，18 个有分支的 checkout 修复
当前入口；两个 detached 固定 SHA 快照、历史证据与主机专属科学实现保留。
完整路径清单、逐文件备份、提交/推送、环境与 Desktop 读回证据位于
`/home/fires/migration-records/hmasd-wsl-20260912/astra-desktop-repair/`。

WSL Agent 访问 `/mnt/c` 上的仓库仍有跨文件系统开销；日常代码和工作树现位于 Linux
文件系统。模型生成速度和远端实验计算速度不因此直接改变。
