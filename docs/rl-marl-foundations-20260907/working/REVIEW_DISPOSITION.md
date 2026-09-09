# 独立评审问题处置

本记录对应 v1 计划 SHA-256 609E5118C511108C9498ADECB607975D7843653DE068C779B1CE29008268002C 的正式独立评审，以及修订 v2 SHA-256 756B82B2C2F5F17D36D5ADAB1C8E2D40327DAE282E552EABB3DA98B7A365FF0D。这里只记录计划修订；没有实施控制面变化。最终独立复核结论以 INDEPENDENT_REVIEW.md 中对应版本原文为准。

| 项目 | v1 发现 | v2 处置与定位 |
| --- | --- | --- |
| R1 / P1 | Pro 被规范要求使用未交付的本地 reading skill | 接受。§3、§4.2、§4.5A/C 改为两条等价路径：本地用 skill 定位，Pro 直接读固定 TASK 明列文件。给出 TASK 显式采纳适用规范的实际短段，其他仓库内容不获授权。§5.2 增加仅能访问清单的离线消费者场景。 |
| R2 / P2 | 通用 §6 仍混有会话选择，§7 未进入独立任务记录 | 接受。§4.1 明确新增 SESSION_CHOICES.md，承接 §7、§6 策略句、§5 当前机制设想及专题选择；正文只留范围和链接。区分已明确选择、机制假设与未冻结实现，不降格已同意的 return 比较偏好。§5.2 增加只读 §6/04_EMPIRICAL 的反例。 |
| R3 / P2 | renderer 缩减方法段时可能丢掉工具证据约束 | 接受最小方案。§4.5C 本批完整保留现有方法段，只新增固定规范采纳与直接阅读，不进行精简。§5.2 仍验证有限/零 learner 的昂贵前置搜索场景及已知/未知成本。 |
| R4 / P2 | 两批发布存在半启用窗口；旧会话与旧 checkout 不会自动更新 | 接受。§6 第一批仅发布知识/会话记录；第二批把规范、skill、角色、作者、renderer/合同和测试一致启用。按既有 clean boundary 同步实际 authoring checkout；下一条科学 assignment/return 携带一次已发布版本与补读指针。补存量会话场景，不加调度器或全量重启。 |

逐引用 SHA 合同建议全部纳入 §4.5/§5：

- 校验每个“仓库、路径、有效 SHA”映射，科学项逐项保持冻结来源；不只比较顶层值。
- 共同 validate 同时检查继承顶层值和覆盖值，覆盖 github_delivery、archive_attachment；合法旧全 SHA 输入兼容，历史原件不重生成。
- 同一映射生成 TASK/附件正文，保留路径去重，HANDOFF 不另存一份总表。
- GITHUB_RESEARCH_COLLABORATION 的单数默认输入说明定点澄清；未冲突合同文字保留。
- 不改 Transport 程序、绑定或注册表；作者仓库引用表与 Transport 附件摘要表分别保持原用途。
- 明确区分离线构造/依赖自洽、远端发布可解析、当前 Pro 实际读取三层事实。第三层只随下一条本来就获授权的真实请求观察，当前未观察就不声称成功，不新增测试 Send 或实验启动门槛。
- 共用 skill 明确保留以 DM 身份工作的 Claude hub；行为材料复用并覆盖 Portfolio、critic。

其余历史职责/运输/正例门槛残留不借本计划全面治理；当前引用链上的 ALGORITHM_PRINCIPLES 历史状态与 spec §1 关系作定点修正。已有请求原件、冻结科学语义、模型/effort、角色权限、既有容量和实验规则保持。

v1 原文保存在 plan-versions/WORKFLOW_INTEGRATION_PLAN_v1.md；v2 原文保存在 plan-versions/WORKFLOW_INTEGRATION_PLAN_v2.md。
