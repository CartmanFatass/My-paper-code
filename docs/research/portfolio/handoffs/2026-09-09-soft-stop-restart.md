# Soft stop and restart handoff — 2026-09-09

Owner instruction: “采取柔和的停止模式 不要打断工作 但是各方向结束当前正在进行的工作后就写handoff 我们为重启做准备”.

Status: **DRAINING; restart not authorized**. No cancellation or process interruption was sent. Complete the work already in progress, its focused acceptance, evidence collection and scientific intake; publish the direction handoff and stop. Do not execute a next arm/seed/object, new scientific retry, successor engineering assignment or new Pro Send. A selected next step is recorded as held, not dispatched. Existing runtime limits remain binding. This is an execution pause, not a direction lifecycle or scientific disposition.

## Current closeout owners

| Direction | Current owner and work allowed to finish | Handoff state |
| --- | --- | --- |
| MGTAP | `/root/cm_mgtap_p72_repair`: source repair/acceptance and independent review. Then `/root/dm_mgtap_p51_geometry_question`: closure intake only. Designated checkout `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`, `codex/mgtap`. Prior writer completed at `5ce038e4aa6130be48b9cd17095470c6bde65d39`; native CM now sole writer. No scientific launch allocated. | CM completed source db34b6c14 and technical handoff c2cca317b, clean/no live process. Root forwarded closure intake to original DM; direction handoff pending. Main source integration remains pending shared-UCOPE reconciliation. |
| FSD | `/root/dm_fsd_p47_resume`, existing CM: P72 D0 and I are reported terminal exit 0; collect/validate exact pair, all-outcome intake. | DM confirmed drain boundary; handoff pending. |
| UCOPE | `/root/dm_ucope_p47_resume`, existing CM: renewal B03/7501 complete exit0, 390.73s, handle `ucope-uav-renewal-b03-7501-p72-20260908`; no live successor. | **STOPPED**. [Direction handoff](../../candidates/ucope/UCOPE_RESTART_HANDOFF_20260909.md), branch23e221769; seven-commit P72 chain integrated main9868dc355. Valid DOWN, T-G -0.0309471106; no remaining scientific budget or selected fourth pair. |
| VSPC1 | `/root/dm_vspc1_p49_value_question`, existing CM: finish current B08/8401 source/check batch; collect only an already accepted invocation. Do not start an unaccepted invocation. | Requested; acceptance/terminal state and handoff pending. |
| CRTO | `/root/dm_crto_p68_reentry`: finish P72 archived-response intake, response `9c8b4b74205e3fe6191e92106aa5b262f868272a`. No successor engineering or Send. | **STOPPED**. [Direction handoff](../../candidates/commitment_residual_triggered_options/CRTO_RESTART_HANDOFF_20260909.md), branch531263fdc; response/intake/handoff integrated main63550cd83. No live process or next B. |

Other directions were already returned/idle and receive no new research assignment. Their recorded intakes, unresolved restrictions and budgets remain unchanged; see EXPERIMENT_TRACKING.md and the existing root log.

## Independent services

Transport `01a07e52-f085-76a0-886a-4127f490421f` was told to finish only already accepted observation/reconciliation/archival/receipts, then hand off and remain idle; no new Send. Relay `01a08456-2cf3-7f02-8595-42d84ba41a4c` continues only final closeout deliveries with existing deduplication, preserving its receipt log. No new automation or scheduler was created.

## Restart inputs

Each direction handoff must retain exact branch/checkout/commit and dirty-path facts, accepted source/card/intake/evidence, any still-live supervisor handle/node/output/current observer, consumed and remaining budget, unresolved gaps, and the next unexecuted step explicitly held for owner restart. Root integrates accepted closeout bytes and records any unresolved integration conflict. Do not infer completion from a queued message or resume from an old ready route.

Main `3e3357c85` carries the owner-requested subagent approval correction: all nine roles explicit `approval_policy = "never"`; execution roles full-access defaults; read-only role boundaries retained. Existing agents received continuity instructions; no hot reload or model/budget change was claimed. Bring these committed configuration inputs into direction checkouts at their next clean input boundary without altering accepted launch bindings.
