# HMASD experiment tracking

## Current observation and return state — OWNER_DIRECT 2026-09-08

This file is the compact operational snapshot. The previous tracker and procedure text is preserved in [EXPERIMENT_TRACKING_THROUGH_P45_20260908.md](../../archive/operations/EXPERIMENT_TRACKING_THROUGH_P45_20260908.md). Detailed receipts remain in [root-log/2026-09-08.md](root-log/2026-09-08.md). Root owns local integration and observation; independent Pro provider operations belong to Transport thread `01a07e52-f085-76a0-886a-4127f490421f`. No standalone heartbeat or retired tracker role is claimed here.

| Direction | Request or accepted handle | Current authoritative state | Current DM/CM route |
|---|---|---|---|
| `flexible_skill_duration` | P52 request `2026-09-08-fsd-post-b03-convergence-01`; Transport turn `01a08264-3712-74f0-ba81-6eaac17a92b6`; HANDOFF `52c30986d1af6b20ab0df4d2c0f1b68a68a90306` | Transport `ARCHIVED` after one provider Send; response SHA256 `0a630d11a37d5179d6df1149d02cf112bb529b32b7a761a393becdea35e83c47`; DM intake is active; no native run | `/root/dm_fsd_p47_resume` |
| `ucope` | 7001 `ucope-uav-motion-prefix-b02-7001-p47-20260908-cwd02`; 7002 `ucope-uav-motion-prefix-b02-7002-p47-20260908` | 7001 terminal exit 0 and technically accepted (`c838cfe2926e1b9d484e9cd73fd945a0464ff473`); 7002 supervisor accepted on `hmasd-wsl-node`, terminal facts pending; no score gating or third pair | `/root/dm_ucope_p47_resume/cm_am_ucope_b02_p47` collects 7002; `/root/dm_ucope_p47_resume` owns all-outcome intake |
| `vsp_c1` | `vspc1_hold_value_b01_8101_65c89368ab0f` | Terminal exit 0; collection accepted (`3ff962acbfabaaa26e2f07d9d38fc2d94a1c3141`) and integrated; scientific intake is the active next route | `/root/dm_vspc1_p49_value_question` |
| `degraded_incumbent_shadow_handover` | P53 request `2026-09-08-dish-p53-own-command-mean-convergence-01` | Transport `ARCHIVED` after one Send; response commit `ddb4c9ff20167837c99d146b2177c3e784066411`; DM intake is active; no local experiment | `/root/dm_dish_p53_native_proposal_question` |
| `metric_ground_transport_allocation` | P51 request `2026-09-08-mgtap-native-geometry-convergence-01` | Transport `ARCHIVED` after one Send; DM intake committed as `623905684a7daa6948c42724aeac0bc3a2b8cbe0`; decision parks the current allocation-coordinate family; no successor | No active DM/CM route |
| `finite_resource_relational_inductive_efficiency` | P47 repair and P41 method-gap routes | No live accepted handle; P47 narrow check was intaken, while P41 remains method-incomplete/tool-blocked; no retry or replacement launch | Existing FRRIE DM records the unresolved dependency |
| `capability_bound_semantic_currentness` | P47 repair route | No live accepted handle; narrow diagnostics were intaken, retained-prefix continuation was not launched after the CM restriction; no production repair | Existing CBSC DM records the remaining restriction boundary |
| `roster_consistent_latent_exploration` | P47 Transport recovery request `2026-09-06-rcle-post-a02-innovator-01` | Provider acceptance and complete matching response remain unproven; unresolved wait counts zero; no new Send | `/root/dm_rcle_p47_transport_recovery` |
| `vsp_02` | P19 convergence | Direction-tier stop is intaken; no runnable continuation, new seed or UAV allocation | No active DM/CM route |

A row is marked active only when a native turn, accepted handle, or accepted Pro generation is live now. Completed returns, undispatched intentions and unresolved idle Transport dependencies do not count as advancing work.

