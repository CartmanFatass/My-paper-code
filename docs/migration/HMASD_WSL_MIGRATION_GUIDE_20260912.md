# HMASD 正式迁移说明（2026-09-12）

本次仅迁移基础设施，不恢复已暂停的研究，不新增实验或 Pro 请求。完整执行约束见同目录 HMASD_WSL_MIGRATION_SPEC_20260912.md。

## 目标布局

| 内容 | 迁移后位置/行为 |
| --- | --- |
| 主仓库 | /home/fires/projects/HMASD |
| 当前方向工作树 | /home/fires/projects/HMASD-worktrees 下，保持各自分支、提交及未提交内容 |
| 实验产物和历史运行记录 | 主仓库 temp/ 保持相对结构及文件原始内容 |
| 本机控制端 Python | /home/fires/.venvs/hmasd-control，依赖由验收记录给出 |
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

## 回退

保留 Windows 副本和 Desktop 路径备份。需要回退时先保全迁移后新增的 Linux 提交、修改和证据，再在 Desktop 退出状态恢复明确的路径记录。已成功启用的 WSL Agent 开关无需因项目迁移而关闭。

## Desktop 入口尚未切换

Windows 文件选择器可以读取 `\\wsl.localhost\Ubuntu-24.04\home\fires\projects\HMASD`，但当前安装版创建项目时，Linux 后端拒绝该 UNC 路径，错误为 `AbsolutePathBuf deserialized without a base path`。Root 在隔离配置目录复现了 UNC 失败、原生 `/home/fires/projects/HMASD` 成功。仅换成另一种 UNC 写法不能视为修复。

尚未改写正在运行的 Desktop 项目、会话数据库或已有任务 cwd。原生 Linux 后端接受路径，不等于 Windows Desktop 全流程已验证；文件迁移与入口切换分别记账。迁移记录目录中的旧 staging 脚本不具备已验证的完整切换能力，不应当作可直接安装的修复运行。

WSL agent 访问 /mnt/c 上的仓库有跨文件系统开销，尤其是大量小文件和 Git 操作；把 agent 切到 WSL 不会自动把项目文件迁入 Linux 文件系统。模型生成速度和远端实验计算速度不因此直接改变。
