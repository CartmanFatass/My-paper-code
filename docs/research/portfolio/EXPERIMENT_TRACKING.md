# HMASD current execution tracking

Current workflow: event-driven Root and independent DM task rollout; research remains paused. See [workflow repair](decisions/2026-09-13-direction-management-workflow.md) and `.codex/hmasd-dm-sessions.toml`. On resume each DM resolves any unasked continuation/capacity/lifecycle decision; exhausted objects do not complete direction management.
Updated 2026-09-13. Windows control checkout: C:/Projects/HMASD; PowerShell.
Owner pause 2026-09-13：MGTAP、RCLE、ACVC、FOLR 均已在干净边界暂停；无运行中实验、Transport 或等待循环。50-minute Heartbeat 已暂停，恢复需 owner 明确指令。

Current direction details: [Portfolio](PORTFOLIO.md). Only current work appears here.

| Work | Actual owner/state | Next event |
| --- | --- | --- |
| ACPS | B02 complete INSIDE_MEI negative: −0.0051864274 J, 12 positive/20 adverse; Q recovery intaken. Portfolio PRO_FINAL applied reversible whole-direction PARKED/HIGH; SHARED/default and all evidence retained; old operation remains unsent record | No active work. Re-entry requires a changed operating/training-resource requirement or trustworthy relevant evidence/cost fact and a new Portfolio/owner decision |
| MGTAP | Portfolio B 与 conformance amendment 已完整 intake；唯一 master pair 完成：COND512 0.16574499572521276 J、DENSE768 0.19507936796417658 J、delta −0.02933437223896382 J（COND_ADVERSE），SE 0.009856726660478026、7/25 worlds；ACTIVE/MEDIUM | post-8231 R 已完整 intake；mean-COND eligibility 与 DENSE default 保留。OWNER_PAUSED，无在途外部依赖/新 pair；旧 UNCERTAIN_EFFECT 不阻挡已完成 intake 且绝不重发。恢复后 DM 复用 R 科学结论，解决未决方向接续/容量问题 |
| RCLE | B08 complete: D_g −0.533040365, D_n −0.370141602, G_U +0.048152669; post-B08 response applied reversible development HOLD; ACTIVE/MEDIUM | Greedy-anchored A 仅保留 epsilon .1 exact-greedy 候选；Portfolio B09 已完整 intake，seed29/256-update/four-panel 完成（native47.13s、exit0），G_U +.0512695、D_n +.1460205、D_g -.0317708；OWNER_PAUSED，两项 HOLD 保留；恢复后 DM 负责下一管理决定 |
| ACVC | Qualified train-C→deploy-F reference retained; F−C +0.124073 J and F−dwell +0.076741 J; ACTIVE/MEDIUM/recasts2 | Next-use/no-addition 已完整 intake，Transport ARCHIVED；无新 fit/K retry 或在途外部依赖。OWNER_PAUSED；恢复后核对科学 no-addition 是否覆盖容量/生命周期，未覆盖则由 DM 提出该未决管理选择 |
| FOLR | Portfolio F 已完整 intake；新 Generic64 完成/技术接受 e617175e（5000/4969/128、exit0、native2156.67s），随后固定 BANK128 一次 admission/提交 db935e57；同一 Monitor 回 ADOPTED+TERMINAL exit0/n128/duration3s，ACTIVE/MEDIUM | DM 已完成 BANK collection/combined scientific intake，结论为该固定用途中 Generic-only（BANK worse）；无运行中实验或新 Pro 请求。Generic→BANK 顺序和五 caps 保持，无 Root ACK/再审批、旧 Generic retry 或 transfer/renewal |
| CADC | Portfolio explicitly applies reversible PARKED/HIGH, retaining RR and B01 evidence | Direction-local documentary application only; no advancing research chain |
| FSD | U complete; limited optional I1280 and D0 default retained, no LONG/repeat U funded | No advancing research chain |

Working-set target: **4**; existing overlap drains without interruption or fifth-slot admission.
Occupied direction slots: **4** — MGTAP, RCLE, ACVC and FOLR, with their original DMs.
No scientific work is running: RCLE B09 and FOLR fixed allocations are fully intaken; ACVC/MGTAP have no external producer. Independent DM migration is the only current governance work; rollout state is in .codex/hmasd-dm-sessions.toml. Occupancy is not a claim of four advancing runs;
completion or idle state does not release an ACTIVE slot. CADC and ACPS are PARKED only through
their explicit Portfolio dispositions. See [current workflow](decisions/2026-09-13-direction-management-workflow.md).
One-time Portfolio discovery intake/registration/control-plane application overhead is attributed
to ACPS support only, unknown unless directly measured. MGTAP T and CADC exclude that shared item;
each direction still counts its own implementation-through-cleanup and later Root integration once.

## Request audit — 2026-09-13

RCLE 的 `2026-09-13-rcle-greedy-anchored-investment-01` 已完成 Portfolio intake 与 B09 执行（seed29/256/four-panel，exit0）；投资请求已闭环，当前 OWNER_PAUSED，不等待 ACK；恢复后由 DM 判断仍未解决的方向管理问题。

FOLR 的 Portfolio F 已归档/intake，没有开放投资审批；Generic64 已完整技术接受，DM 随即直接
执行已拨款 BANK128，Monitor 已回终态，combined intake 已完成，固定用途中 Generic-only（BANK worse）。ACVC 与 MGTAP 最近请求已完整 intake，没有新的未决
答复。各自保留的 no-addition 与 uncertain-effect 事实不会凭 timeout 变为新请求。

实验属于 DM object tier：只要 accepted card、Pro decision 或 finite grant 已固定对象、输入、
比较器和 cap，DM 直接完成 admission、launch、collection 与 acceptance，不再向 Portfolio
申请重复批准。Portfolio 只处理新的 investment、capacity、lifecycle、fusion/separation、
registration 或 vacancy replacement；没有具体科学后果时不创建高频咨询。

## Current routing

| Role | Task | Runtime |
| --- | --- | --- |
| Root | 01a095b7-850f-7401-ad4e-5e4320d285f1 | Windows main control |

Read .codex/hmasd-transport.toml for Agentify/provider configuration. Each DM creates/reuses
its native Transport, binds its exact ID in new handoffs, and receives archives directly. Root and DM use native
long waits; each DM resolves and records its own reusable native Luna/low monitor identity on
adoption. Experiment events return directly to DM. Root-action completions remain native.
Historical packet addresses are not new dispatch routes.
FOLR's300-second support value is an owner-clarified reference: recorded308.8422538 is not
by itself a hard stop. Native/scientific scope and remaining explicit complete-work limits persist.
Historical run roots, fixed SHAs and complete data remain in their scientific evidence records.



