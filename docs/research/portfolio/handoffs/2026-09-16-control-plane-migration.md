# Control-plane migration handoff — 2026-09-16

## 当前结论

控制面迁移已集成发布，受限原生验收和独立审查完成；Root 接受本次共享控制实现。
Research pause（所有者 2026-09-15 22:23 PDT）仍有效；没有启动训练、CF 实现或真实
Pro/Portfolio 请求。临时目录清理受自动审批拒绝而保留，不宣称清理完成。

main 控制源码：`38cc9264fae4e770f7a71ce0e3810baa0454c16e`（主体
`50ad5e9bc192dce4828af2a3565b031ebbee731d` + Windows 换行修复），两提交均已推送 main
与迁移分支。本页及发布证据是其后的文档回执，未再改控制逻辑。
FSD：控制同步 `ca57dfe7565ffd479c0d01e56ca96d30ba596ac1`，补齐原有主分支批准表及
两份 owner 决定 `2f57045c95c7525e8c881a04955d035d1a726e0d`；已核对 origin/codex/fsd。
完整路径和来源见[发布回执](../../../project/CONTROL_PLANE_MIGRATION_PUBLICATION_20260916.json)。

下一明确动作：Root 仅在允许安全删除后清理本次 scratch/worktree；研究保持暂停，
不因交接完成继续科研。未来科研恢复须由所有者明确触发，随后原 DM 从下述冻结入口继续。

## 实际落地与验收

七个 shared task skills 为现行方法唯一维护源；AGENTS/角色已瘦身，Claude 副本由
`tools/publish_claude_control.py` 生成并提供原生适配。计划 §5 的前瞻流程修正已经落地。
详见[迁移决定与来源映射](../decisions/2026-09-16-control-plane-migration.md)，其中直达
BASELINE、CHECKS、NATIVE 证据，不需要逐份回读旧 handoff。

AGENTS 55,161→5,485 bytes，CLAUDE 16,258→1,753 bytes。七个 skill 格式有效，publisher
零漂移；202 项既有检查通过，修复后两轮聚焦检查 82/95 项通过（相互重叠）。Codex root、
DM、Operator、Transport 和 Claude hub、Reviewer、Operator 的实际本地读取/行为轨迹已核验。
完整系统注入不可见部分、远端运行时和旧常驻会话不在已验收声明内。

发布后实际 Windows checkout 曾出现 CRLF/LF 漂移，已用文本复制的 LF 归一化修复，
独立 Reviewer 在 main 重现四处差异并核对只有换行变化；新增回归检查 3 项通过。
main 与 FSD publisher 最终均为零漂移。发布后的新 Codex main 会话和新 Claude FSD 会话
真实读取新方法并正确保留 pause/无补位/n=1 限制；这不代表旧会话已经刷新。

## 保留与待决

FSD 当前冻结对象仍为 `FSD_MATCHED_INFORMATION_BASELINE_B01`，card/handoff/request/archive
和批准表成员原样。FSD 分支原本没有批准表与两份 owner 决定，本次从 main 原样补齐，
Git blob 与主分支相等，未产生新批准或成员变更；恢复入口是
[matched-information handoff](../../candidates/flexible_skill_duration/HANDOFF_2026-09-16_matched_information_baseline.md)。
未来明确恢复后才由原 DM 实施 CF、检查和独立审查，再由 Operator 启动 stage 0。
ACVC closing memo 仅排队，未作新生命周期决定，未发送 Portfolio。

运行进程 / Pro / agent / 浏览器：迁移自身未启动研究 producer；原 registry 的 FSD/ACVC
归档事实已读取，但远端进程、浏览器与旧 agent 状态未全面实时核验，不能报“全部为零”。
旧未决 Send 状态保留，恢复只能接原 request。其他会话的既有修改已在基线提交内，未回退。
FSD 另同步了基线 `e9399305d58bdd7e5f9518e12cf43e9abd199ee3` 已接受的
`.claude/settings.json` 与 Transport `bind_conversation.py` 的 direction_id 补齐；Claude
共享控制编辑禁令移除沿用基线既有决定。Codex 角色模型、推理和 sandbox 配置保持相等。

旧通用 wall 参考阈值冲突、七日预算起算/扣账规则待所有者以后在相关预算边界澄清；不为
迁移猜造额度，也不影响已冻结对象原义。旧会话需实际刷新或新建加载，磁盘更新不等于接管。

自动审批审查两次拒绝递归清理本次 scratch（虽已核对路径）；没有绕过。迁移临时目录和
worktree 保留，Root 在可获准安全清理时收尾；不删除诊断或独有证据。

## 回退

已知良好基线 main `e9399305d58bdd7e5f9518e12cf43e9abd199ee3`。如需回退，以新提交撤销
本次迁移提交组，保留科学证据；Git 回退不代表撤销任何外部效果。
