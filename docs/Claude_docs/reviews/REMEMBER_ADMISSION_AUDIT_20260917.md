# Remember 自动记忆入口复核（供 Claude 修复）

日期：2026-09-17（America/Los_Angeles）。Owner 要求单独报告；本次不修改 Remember、Claude 用户设置或记忆文件。研究暂停保持有效。本报告是一次性审计证据，不是新的治理入口。

## 结论与边界

**Medium：自动注入路径可将过期的操作指令带回 HMASD 会话。** 机制置信度 0.97；实际导致违规行为的证据不足。不能据此声称插件未经用户授权、模型已恢复研究，或 Haiku 与 Codex 两种总结器都实际运行过。

当前唯一治理来源是 `docs/project/OPERATING_CONSTITUTION.md`；当前研究状态为 `docs/research/RESEARCH.md`。Remember 的内容不能改变 owner pause、方向 lead 或 Git 规则。

## 已核实证据

以下行号来自审计时文件，修复前应重读当前内容；插件升级可能改变行号。

| 边界 | 文件与证据 |
| --- | --- |
| 启用 | `C:/Users/fires/.claude/settings.json:18`：`remember@claude-plugins-official=true`。 |
| 实际版本 | `C:/Users/fires/.claude/plugins/installed_plugins.json:88`：用户级安装，版本 `0.33.0`。 |
| 冲突 handoff | `C:/Projects/HMASD/.remember/remember.md:10`：要求继续旧 D2 Phase 3；`:17`：推送拒绝时使用 `rebase --autostash`。与当前 `AGENTS.md:48` 未经明确授权不得 stash 的规则冲突。 |
| 过期状态 | `C:/Projects/HMASD/.remember/recent.md:7` 与 `.remember/tmp/start-context.cache:18`：仍称宪章 work in progress。宪章已被 owner 采用。 |
| 单独 handoff 注入 | 插件 `scripts/session-start-hook.sh:1694` 输出 handoff；`:1689` 有重复交付/陈旧提示，但仍注入正文。autostash 不在 start-context.cache 中不代表不会注入。 |
| 缓存注入 | 同脚本 `:1862` 加载 start-context 缓存；`:1981` 将内容包装为 SessionStart `additionalContext`。 |
| 实际运行 | `C:/Projects/HMASD/.remember/logs/memory-2026-09-17.log:1` 显示本项目 SessionStart hook；`:4–7` 显示 consolidation；`:30` 的 provider 为 claude。 |
| 后台模型路由 | 插件 `pipeline/haiku.py:951` 起根据宿主选择总结器；Codex 是支持路径，不是本次已证实的 HMASD 使用事实。fallback 也不是无条件执行第二模型。 |

插件根目录：`C:/Users/fires/.claude/plugins/cache/claude-plugins-official/remember/0.33.0/`。

## Claude 侧最小修复建议

1. 先确认当前插件版本及实际运行配置，识别自动 SessionStart、压缩后重新注入和后台整合入口。不要运行 hook 来“检查”，因为 hook 本身会写记忆并可能调用总结器。
2. 在 HMASD 范围禁用或收窄自动 handoff/治理状态注入；优先使用插件支持的项目级设置。不要凭空添加未知配置项，也不要未经检查影响其他项目。
3. 保留旧记忆作为历史证据，替换活动 handoff 中的继续执行与 Git 操作指令，并使缓存失效。只删缓存不修源内容会在下一次生成时复现。
4. 若继续保留自动记忆，治理状态只指向宪章与 RESEARCH.md，不复制可过期的 pause/lead/允许操作结论。用户纠正应高于模型摘要；旧 handoff 不得自动获得恢复研究权限。
5. 在无外部副作用的夹具中验证：旧 handoff 不重新激活、重新压缩不恢复冲突内容、插件未产生意外的模型 fallback、无研究启动。单纯更新磁盘配置不等于活会话已采纳。

## 验收与尚未确认事项

- 本次仅静态读取源码、配置、日志、记忆；没有执行 Remember hook 或总结器。
- 没有证据证明过期 handoff 已造成真实 stash、研究恢复或结果污染。
- 历史 archive 的日期标签和旧研究摘要本身不是违规指令；重点是自动注入的可执行 Next/Context 内容。
- HMASD 控制发布 `drift: 0` 只覆盖项目生成文件，不覆盖用户插件、活会话状态或有效权限。
- 修复后请报告实际变更路径、缓存处理方式、验证结果和仍未确认的运行时采纳状态；不需要创建新的常设治理记录。
