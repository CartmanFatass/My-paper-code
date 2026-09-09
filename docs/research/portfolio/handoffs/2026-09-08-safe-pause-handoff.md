# HMASD 安全暂停 handoff — 2026-09-08

## 目的与边界

本 handoff 根据 owner 的最新指令建立“安全暂停”边界。当前已接受的方向任务只完成各自已经授权的收尾；到达清洁边界后停止自动研究循环。暂停期间不新增 Portfolio replacement，不发起新的 Pro Send，不创建新的研究方向，不改变冻结卡片、比较器、预算、RNG、设备或证据含义。

“完成各自部分”指：DM/CM 完成当前已选对象的实现、检查、一次既定执行（若该对象已有授权）、技术 collection、科学 intake、Chinese brief、audit/owner 记录和提交。它不包括为填补空位而选择 successor、重复实验或扩展预算。

## 当前必须排空的三个方向链

| 方向 | 当前状态 | DM 的最后一步 | 清洁边界 |
| --- | --- | --- | --- |
| `ucope` | P61 B04/7201 已完成一次远程 pair；技术 collection 已通过并已集成 `cc64a7b84`，科学 intake 已集成 `31e0fda31`。T−G = −0.003948225944122139（SE 0.010191826216031805），G−H = +0.0238187196536019（SE 0.011454243503509544），T−H = +0.019870493709479763（SE 0.014677398371169156）；286,720 team steps、2,048 Adam、96 eval、277.51 s 全部可追溯。 | `/root/dm_ucope_p47_resume` 已完成 P61 all-outcome intake，保留预测评分、限制、brief、audit 和 no-successor 结论，提交 `43f4cc2c14a3b6662d138ad4b3b7b9a26f9e0227` 并返回 Root。 | intake 已集成、原始证据与 receipts 保留；无 live handle、无后续运行。 |
| `vsp_03` | P65 deadline correction 已由 CM 接受（source `b5d605bf4f39b5ab18f01c98e04dc07e53764354`，evidence `c2c092894`，DM binding `671619257`）；P64 唯一 seed6 B04 已执行一次并在准入前 exit2，科学曝光为零；DM intake 已集成 `40a2506db`。 | `/root/dm_vsp03_p54_reentry` 完成 failure collection/intake，提交 `380c50499da32affe4b3350387f45f858c88edbb` 并返回 Root。 | 单次 B04、collection 与 intake 已完成；无 live handle、无 retry、无新增 seed/T。 |
| `vsp_c1` | P66 已由 Portfolio 发布（`3c32c8f51`）；master8202 的一次提交已 exit127 于脚本路径错误，科学曝光为零；DM intake 已集成 `437b2801d`。 | `/root/dm_vspc1_p49_value_question` 完成 failure collection/intake，提交 `49e759d9151b912f974f9916d52cd42f0539c7ce` 并返回 Root。 | P66、collection 与 intake 已完成；无 live handle、无 retry、无 third normalized pair、extra H/eval、tuning 或 successor。 |

P66 依赖的 accepted UCOPE environment files（`experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` 与 `__init__.py`）必须随 exact launch source 保留；不要用无关 main 变更替换。

## 已结束或保留为依赖的方向

DISH P62 已作 `PRO_FINAL` narrow stops/no successor；FRRIE P63 仍是 permitted observation method 缺口；SCDMP P58 是无 confirmed Send 的 terminal blocker；RCLE 仍缺 exact-request external acceptance；FSD、MGTAP、VSP02 和其它已 intaken 路由没有当前 successor。它们全部保留原始证据，不重发、不重跑、不以“第五个空位”为理由绕过限制。

## Root 执行顺序

1. 逐项接收并集成 DM/CM 的已提交 commit，只按显式路径 add/commit/push；不触碰预先存在的未跟踪 PDF 和 `docs/rl-marl-foundations-20260907/`。
2. 对 VSP03 和 P66，只有在对应 DM 的 exact source/cwd/payload/handle handoff 已接受后，才在同一次 invocation 前执行 `admit-memory`，并按现有远程 wrapper/launch 文件提交一次。
3. 每个 terminal result 立即沿原 route 用 `followup_task` 送同一 CM collection，再送同一 DM intake；不把 technical PASS 当作 scientific conclusion。
4. 每个方向完成 intake 后更新 `docs/research/portfolio/EXPERIMENT_TRACKING.md` 和当日 root log，保留 handles、raw outputs、admission、source SHA、collection、intake 和 cleanup 证据。
5. 三个方向都到达上述清洁边界后，设置本 handoff 为 `PAUSED`：没有 live accepted handle、没有未完成的 DM/CM 收尾、没有新的 Portfolio command。之后仅在 owner 明确恢复时继续；不要创建 heartbeat、scheduler 或 replacement task。

## 恢复所需最小事实

恢复时从本 handoff、`EXPERIMENT_TRACKING.md`、当日 root log、各方向 card/intake 和 exact commit 读取状态。恢复不得从旧 agent 名称或历史 handoff 推断新任务；每个新对象必须有新的明确 Portfolio/owner 指令和对应证据记录。

状态：`PAUSED`（2026-09-09T00:27Z；UCOPE P61、VSP03 P64/P65、VSPC1 P66 三条当前链均已完成 intake 并集成；无 live accepted handle、无未完成 DM/CM 收尾、无新的 Portfolio command。证据与原始 receipts 保留，待 owner 明确恢复后再继续。）
