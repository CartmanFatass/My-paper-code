VERDICT

PASS_FULL_WORKFLOW_SMOKE

VERIFIED_TRANSPORTS

Gemini：支持。 注册的 Antigravity 会话返回 TRANSPORT_OK，并列出实际读取的四个 allowlisted 本地文件；raw 同时声明未收到算法、实验或其他 reviewer 输出。

Open Pro：支持。 注册的 Pro 会话报告 pinned commit、问题文件及两个规定证据文件均可读取，并明确未收到 Gemini 输出或科学任务。

Direct callbacks：支持，但证据为间接闭环。 控制器记录两份结果均由各自注册 Exchange 返回，随后才生成 factual reconciliation 和当前 convergent handoff；这与 Exchange 只允许向注册 controller 发送一次 terminal callback 的合同一致。

Raw archival：支持。 两份 raw 均已成为当前提交中的独立文件；reconciliation 记录其自然完成且精确归档。Exchange 合同还要求 capture、回读和 exact-text equality，而 Gemini 脚本以 UTF-8 写入指定 raw 并默认拒绝覆盖。

Role isolation：支持。 两个 divergent raw 均作出明确隔离声明；Exchange role firewall 也禁止读取另一 reviewer 的输出、管理其他阶段或联系其他 Exchange。

REPAIR_ASSESSMENT

三项修复均针对已观察到的 transport blocker，且未改变科学范围：

Gemini permission：已处理。 两个 tracked launcher 均显式保留注册 conversation、plan mode 和 sandbox，同时加入已批准的 --dangerously-skip-permissions；问题、manifest 和输出路径仍限制在批准的 external-review roots。

Deferred-Pro waiting：已处理。 立即回答 被明确规定为正常等待状态，不得点击或误判为失败；后续检查由同一 heartbeat 完成。

Pinned-question validation：已处理。 完成条件只能从 assigned commit 上的问题文本导出，禁止使用旧工作树、会话记忆或其他 round 的字段。

这些修复只改变 permission、waiting-state 和validation transport 行为；review brief及各问题继续明确禁止算法、实现或实验判断。

REMAINING_OPERATIONAL_RISK

当前审阅材料没有单独保存 REVIEW_STAGE_COMPLETE 的工具回执、handoff_id 或 heartbeat 删除确认；direct-callback完成由控制器 reconciliation 和阶段推进间接证明。

--dangerously-skip-permissions 的文件隔离仍依赖 sandbox、manifest 内容及 reviewer 遵约，而不是 launcher 对manifest内每个读取路径实施机器级allowlist enforcement。该风险在本次smoke中未造成越界证据，但应继续视为权限面风险。

NEXT_ACTION

该workflow可用于下一次tracked scientific round。使用前应先按现有合同完成本convergent raw的精确归档、向注册controller发送唯一terminal callback，并由controller记录本轮transport-only disposition；无需重跑Gemini或Open-Pro smoke，也不得借此改变任何科学路线、模型或推理设置。