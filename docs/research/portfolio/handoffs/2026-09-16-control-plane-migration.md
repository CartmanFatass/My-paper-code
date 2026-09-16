# Control-plane migration handoff — 2026-09-16

## 当前结论

控制面实现与受限原生验收完成；独立审查材料问题已修复。当前处于提交集成阶段，
精确发布回执在本页下一次更新写入。Research pause（所有者 2026-09-15 22:23 PDT）
仍有效；没有启动训练、CF 实现或真实 Pro/Portfolio 请求。

下一明确动作：Root 按本次迁移授权提交推送已审查改动，集成干净 main，并将必要控制
同步到暂停中的 FSD checkout；完成发布核验后保持研究暂停。

## 实际落地与验收

七个 shared task skills 为现行方法唯一维护源；AGENTS/角色已瘦身，Claude 副本由
`tools/publish_claude_control.py` 生成并提供原生适配。计划 §5 的前瞻流程修正已经落地。
详见[迁移决定与来源映射](../decisions/2026-09-16-control-plane-migration.md)，其中直达
BASELINE、CHECKS、NATIVE 证据，不需要逐份回读旧 handoff。

AGENTS 55,161→5,485 bytes，CLAUDE 16,258→1,753 bytes。七个 skill 格式有效，publisher
零漂移；202 项既有检查通过，修复后两轮聚焦检查 82/95 项通过（相互重叠）。Codex root、
DM、Operator、Transport 和 Claude hub、Reviewer、Operator 的实际本地读取/行为轨迹已核验。
完整系统注入不可见部分、远端运行时和旧常驻会话不在已验收声明内。

## 保留与待决

FSD 当前冻结对象仍为 `FSD_MATCHED_INFORMATION_BASELINE_B01`，card/handoff/request/archive
和批准表成员原样；恢复入口是
[matched-information handoff](../../candidates/flexible_skill_duration/HANDOFF_2026-09-16_matched_information_baseline.md)。
未来明确恢复后才由原 DM 实施 CF、检查和独立审查，再由 Operator 启动 stage 0。
ACVC closing memo 仅排队，未作新生命周期决定，未发送 Portfolio。

运行进程 / Pro / agent / 浏览器：迁移自身未启动研究 producer；原 registry 的 FSD/ACVC
归档事实已读取，但远端进程、浏览器与旧 agent 状态未全面实时核验，不能报“全部为零”。
旧未决 Send 状态保留，恢复只能接原 request。其他会话的既有修改已在基线提交内，未回退。

旧通用 wall 参考阈值冲突、七日预算起算/扣账规则待所有者以后在相关预算边界澄清；不为
迁移猜造额度，也不影响已冻结对象原义。旧会话需实际刷新或新建加载，磁盘更新不等于接管。

自动审批审查两次拒绝递归清理本次 scratch（虽已核对路径）；没有绕过。迁移临时目录和
worktree 保留，Root 在可获准安全清理时收尾；不删除诊断或独有证据。

## 回退

已知良好基线 main `e9399305d58bdd7e5f9518e12cf43e9abd199ee3`。如需回退，以新提交撤销
本次迁移提交组，保留科学证据；Git 回退不代表撤销任何外部效果。
