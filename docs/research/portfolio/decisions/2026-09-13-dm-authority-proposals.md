# DM 方向研究管理员扩权建议汇总 — 2026-09-13

状态：`PROPOSAL_ONLY`。本文件汇总四个当前 ACTIVE DM 的独立建议，不改变现有科学权限、预算、生命周期或 Portfolio 决策边界。

## 当前请求审计

- **FOLR**：Portfolio F 已完整 intake；Generic64 已 admission/launch，Monitor 在途。技术验收后由 FOLR DM 直接执行已批准的 BANK128。没有待批准 Portfolio 请求。
- **ACVC**：最近 next-use 请求已 ARCHIVED/intake；没有开放请求、实验或外部依赖。DM 已记录空白等待审计，不重复提交条件性问题。
- **MGTAP**：post-8231 R 已 ARCHIVED/intake；没有开放请求或已批准的后续 pair。当前只保留具体开发后果出现后的 proper-node 入口。
- **RCLE**：greedy-anchored Convergence 已 ARCHIVED/intake；正在准备单一 finite-investment 问题，尚未发布/发送。若获批，实验执行仍由 DM 负责。

常规实验不进入 Portfolio 审批队列。只要 accepted card、Pro decision 或 finite grant 已固定对象、输入、比较器和 cap，DM 直接完成 admission、launch、monitor、collection 和 intake。Portfolio 只处理新的 investment、capacity、lifecycle、fusion/separation、registration 或 vacancy replacement。

## 四个独立建议

| DM | 建议文件 | 当前针对的瓶颈 |
| --- | --- | --- |
| FOLR | [FOLR_DM_AUTHORITY_PROPOSAL_V1_20260913.md](../../candidates/vap_folr_core/FOLR_DM_AUTHORITY_PROPOSAL_V1_20260913.md) | 已批准 Generic→BANK 链不再逐步请求；DM 负责 admission、Monitor、技术验收和下一已批准对象 |
| ACVC | [idle audit 与 authority proposal](../../candidates/acvc/pro_packets/20260913_reference_next_use_convergence/INTAKE.md) | ACTIVE-idle 不等于待审批；无新输入时复用 no-addition 判断并等待真实事件 |
| MGTAP | [MGTAP_DM_AUTHORITY_PROPOSAL_V1_20260913.md](../../candidates/metric_ground_transport_allocation/MGTAP_DM_AUTHORITY_PROPOSAL_V1_20260913.md) | 已接受任务包内的对象实验、工程和 intake 由 DM 闭环；新的总额度/容量仍走 proper node |
| RCLE | [RCLE_DM_AUTONOMY_PROPOSAL_V1_20260913.md](../../candidates/roster_consistent_latent_exploration/RCLE_DM_AUTONOMY_PROPOSAL_V1_20260913.md) | 一次性 finite-investment 选择与获批后的整包执行分离，避免为每个步骤重复购买/审批 |

四份建议的共同最小规则是：复用当前 card/intake/ledger；在完成、实质冲突或 ACTIVE-idle 时向 parent 主动回报一次；无变化时保持原生等待；只有改变科学含义、预算、容量或生命周期时才提交 proper-node 请求。

## 后续处理

Root 暂不把 `PROPOSAL_ONLY` 自动提升为新的 Portfolio 决策。现有 `AGENTS.md`、`ROOT_OPERATIONS.md` 和 `hmasd-loop-dispatch` 中的 DM 自主执行标准继续生效；若需要统一改写治理条文，应由 owner/proper node 形成明确的 specification decision 后再落地。
