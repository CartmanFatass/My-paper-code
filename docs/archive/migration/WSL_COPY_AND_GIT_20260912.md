# WSL 正式工作区、复制边界与 Git 收尾（2026-09-12）

日常工作继续使用原 **HMASD** Desktop 项目。其正常项目接口已读回
`/home/fires/projects/HMASD`，项目 ID 为 `177ab8d8-53ae-448c-9a9e-aaa2fecd2498`。
项目“1”曾用于验证 Linux 入口，没有必要切换过去。旧任务的 cwd 是独立字段；
续用时明确给出对应 native 工作树，并检查实际 `pwd` 和 Git 根目录。
当前迁移任务的既有记录仍是 `/mnt/c/projects/hmasd`，其变更面板可能继续查看旧副本；
本次所有提交均通过明确的 native cwd 执行。原 HMASD 项目中新开的任务使用已切换的
Linux 项目入口；不需要项目“1”，也不为改变面板而直接改写任务数据库。

## 正式布局

- `/home/fires/projects/HMASD`：`main`，跟踪 `origin/main`。
- `/home/fires/projects/HMASD-worktrees/`：17 个有分支的方向/Transport 工作树，
  各自保持原有分支名和对应 `origin/<branch>`；Git 元数据归属 native main。
- 两个 `app-4b9d/HMASD`、`app-c587/HMASD` detached checkout 保留固定 SHA，
  作为原有快照，不将其切成 main 或普通 authoring 分支。
- `/mnt/c/Projects/HMASD` 及 Windows 原工作树保留作回退来源；迁移后新增日常工作
  写入 native 工作区。原 Windows main 保持 `64561c64f47fed8a86b39ccf27601db25d4d77df`。

## 复制完整性的准确表述

已验证复制的资产清单包含 193,856 个文件、28,651,427,301 字节；源 refs 和维护中的
工作树已保全。可重建的 Python/pytest 缓存按原迁移记录排除，Git 链接重建，运行环境
按 Linux 包重建，因此本来就不是将 Windows 系统环境逐字节照搬。

OWNER_DIRECT 2026-09-12：用户说明这些历史临时目录是 pytest 遗留的 ACL 权限残留，
也是迁移离开 Windows 的原因。按该说明，这批受限历史临时内容列为迁移排除项，
保留 Windows 原状；不再阻塞 native main/worktree 的正式使用。

保留的实际读取事实如下；排除并不表示已经读取或复制：

- 797 个源端历史临时目录仍拒绝枚举，native 目标不存在对应目录。pytest 遗留性质
  来自用户说明；工具没有核验其内部内容，也不声称它们是空目录。
- 一个 2,218,087 字节的文件仍拒绝读取，目标未复制：
  `temp/directions/ucope/recon/ucope-scout-r01-b1-odd-support-audit-20260901-01/odd-support-audit.json`。

WSL 与 Windows 原生读取均返回拒绝访问，当前 Windows 进程也没有备份读取特权。
源 Windows 权限和内容保持原样，本次不修复这些旧 ACL、不将其权限问题带入 Linux。
按上述排除范围，正式项目迁移可以收尾；这不等于整个 Windows 目录逐字节镜像，
也不会将 Git 忽略的历史目录自动上传到远端。

## 大量行数变化的原因与处置

原有 24 份跟踪日志在 Windows 工作目录使用 CRLF，而 Git 已保存 LF。普通 diff 因此
显示约 181 万行增加及 181 万行删除；逐文件核对确认没有内容变化。

native 仓库本地 Git 配置现为 `core.autocrlf=input`，没有修改全局 Git 设置。
对这 24 个明确路径刷新索引后，规范化 blob 与 HEAD 完全一致；磁盘上总计
59,236,866 字节保持原 SHA-256，日志没有被批量重写，也没有产生日志内容提交。
可用 `git config --local --unset core.autocrlf` 恢复本次本地设置。

本次提交保全源 Windows 已有的 ACVC 交接产物，并清理审计合并冲突标记：
17 个产物通过 Git 读取规则生成的 blob 与已发布 `14288810c` 的对应 blob 逐项一致；
审计只去掉三行冲突标记，保留 FOLR 和 ACVC 双方原始记录。此次是交接内容保全，
没有代替 DM 补做科学 intake、更新科学结论或恢复研究。

精确文件、哈希、原冲突备份、权限复查及最终提交/推送回执位于：
`/home/fires/migration-records/hmasd-wsl-20260912/astra-desktop-repair/copy-completeness-followup/`。
