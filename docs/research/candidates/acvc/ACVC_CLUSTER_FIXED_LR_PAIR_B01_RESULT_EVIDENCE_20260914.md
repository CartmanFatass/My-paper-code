# ACVC_CLUSTER_FIXED_LR_PAIR_B01 — E0 result evidence

## Object, original bytes and rule

Class **B/EXPLORE**; one prospectively matched programme identity master27931/eval37931, two fresh C-only recipes (low1e-4, reference3e-4), no iid-training-population claim. Source `2bbaa99ad9cc717d89e47a1f24d9acd76dce4f97`; exact commands `f3cba57c88bcde9c8bd8a37ed4b8410f4f875bcd`. [Card](ACVC_CLUSTER_FIXED_LR_PAIR_B01_SCIENCE_CARD_20260914.md), [machine facts](ACVC_CLUSTER_FIXED_LR_PAIR_B01_PROSPECTIVE_FACTS_20260914.json), [complete recorded-data analysis](evidence/cluster_fixed_lr_pair_b01_20260914/INTAKE_ANALYSIS.json).

Rule applied verbatim: **strictly greater than +.01 J is UP; strictly less than −.01 J is DOWN; inclusive [−.01,+.01] is WITHIN; missing or invalid required measurements give INCOMPLETE for their dependent contrast.** Both original fits and all six final panels are complete. WITHIN is not equivalence; no confidence-interval or significance gate was applied. J=S/256 from complete native team reward.

## Full final panel

| Recipe | Package | Mean J | Mean S | World min J | World max J |
|---|---|---:|---:|---:|---:|
| low | C | 0.20068241765190753 | 51.374698918888328 | 0.044678943818140457 | 0.37969101592218379 |
| low | F | 0.31733687247860587 | 81.238239354523103 | 0.089292882522906958 | 0.53968339147481281 |
| low | dwell | 0.25068396735243303 | 64.175095642222857 | 0.065972772053684361 | 0.39964088568336836 |
| reference | C | 0.32921597892941801 | 84.27929060593101 | 0.11501581677631535 | 0.51164244950211446 |
| reference | F | 0.36692059909191432 | 93.931673367530067 | 0.13826558259811514 | 0.53616052213567766 |
| reference | dwell | 0.33440984893592984 | 85.60892132759804 | 0.07445259248848396 | 0.52136590425761131 |

The designated low C−reference C contrast is **−.1285335612775105 J, DOWN**. Its conditional SE is .011137008194285232 J; 59/64 world differences are negative and5 positive, range−.3730060045102702 to+.04755205995114148. This is one matched recipe block, not a recipe-population interval.

| Comparison | Mean difference J | Conditional SE J | Negative / positive / zero | Min J | Max J | Reading |
|---|---:|---:|---|---:|---:|---|
| low_C-reference_C | -0.12853356127751051 | 0.011137008194285232 | 59/5/0 | -0.37300600451027022 | 0.047552059951141479 | DOWN |
| low_F-reference_F | -0.049583726613308517 | 0.0089650510048318345 | 48/16/0 | -0.24107445129313909 | 0.098607458658424102 | DESCRIPTIVE |
| low_dwell-reference_dwell | -0.083725881583496795 | 0.0095635292939266012 | 56/8/0 | -0.28092052955949531 | 0.083510507386820754 | DESCRIPTIVE |
| low: F-C | 0.11665445482669831 | 0.01058683363038718 | 6/58/0 | -0.077510145585770407 | 0.2807765121096597 | UP |
| low: F-dwell | 0.066652905126172807 | 0.010230990747700543 | 12/52/0 | -0.16355284736656367 | 0.27924491895970532 | UP |
| low: dwell-C | 0.050001549700525519 | 0.010470156868647412 | 18/46/0 | -0.13054168059125171 | 0.26350486857698546 | DESCRIPTIVE |
| reference: F-C | 0.037704620162496337 | 0.0082647506378577072 | 16/48/0 | -0.13436005611203941 | 0.20899639158312627 | UP |
| reference: F-dwell | 0.032510750155984522 | 0.0082580429344839366 | 16/48/0 | -0.12733811826976932 | 0.24955961587095765 | UP |
| reference: dwell-C | 0.0051938700065118143 | 0.0072409090670419781 | 32/32/0 | -0.12515055975512923 | 0.1533425043404813 | DESCRIPTIVE |

All five prespecified point-rule readings are reported: low C−reference C DOWN; both recipes' F−C and F−dwell UP. Supporting comparisons are explicitly descriptive. Direct64-world difference vectors, their sample SD/sqrt64, all signs and episode IDs are in the analysis; no independent-SE addition, cross-panel pooling or favorable-endpoint selection was used. Each package has private state/history; common reset worlds do not make its trajectory or trigger dose identical.

## Exposure and technical acceptance

Each original has4096 train +192 evaluation episodes (4288 scored rows), 2048 rollouts,8192 ordered Adam/backward/update records, one snapshot after rollout2047/update8192, three subsequent private actor loads and four environment constructors. Per original:1048576 training+49152 evaluation=1097728 team ticks,20971520 replayed actor-agent steps and4194304 critic update rows. Pair totals:2 fits,8192 train+384 eval,8576 scored rows,2195456 ticks,16384 Adam,41943040 replayed actor-agent steps,8388608 critic rows,2 snapshots/6 loads. No midpoint, third fit, retry or extra scientific probe.

Both original summaries, all episode/update rows and actual source/configuration match the card. All parsed loss, reward and gradient fields are finite; row IDs, reset identities, recipe/rate tags, counts and direct primary publication agree. Runtime summaries record CPU/float32/intraop1/interop1, actor34902+critic34177=69079 parameters, expected final checkpoints, actual optimizer group rates1e-4 and3e-4 and empty limits. Both actor and critic move under real learning; low/reference actor displacements2.413120985031128/8.544625282287598 are descriptive, not mechanistic causality or a rate-displacement bound. No models were loaded or native trajectories rerun during collection/analysis.

F retrace counts are7046(low)/7629(reference); own-dwell interventions5036/5009. They arise from separately evolved package histories and are not matched intervention doses. Reference dwell−C is+.005193870006511814 J descriptively, with32 adverse/32 favorable worlds; this does not prove equivalence.

Prelaunch engineering:11 focused checks passed10.22s; independent Astra/high review found one offline partial-ingestion failure path. DM repaired it before either original,2 focused tests passed.29s, and the same Reviewer verified no residual material finding. The training/evaluation/launch bytes were unchanged by that repair. Details and the actual local-cleanup restriction are in [ENGINEERING](evidence/cluster_fixed_lr_pair_b01_20260914/ENGINEERING.md). No scientific-source deviation or §5 budget breach was found.

## Original costs, receipts and preservation

| Original | PID | Native wall s | User+system CPU s | Peak RSS KiB | Native/supervisor exit |
|---|---:|---:|---:|---:|---|
| low | 3701076 | 1189.08 | 1187.91 | 553692 | 0 / 0 |
| reference | 3701127 | 1192.29 | 1191.52 | 555540 | 0 / 0 |

Native whole-process wall sum **2381.37s**, aggregate user+system CPU **2379.43s**. Remote supervisor logs give common whole-second start2026-09-15T02:04:22Z, low terminal02:24:11Z and reference02:24:15Z:1193s rounded enclosing elapsed,1189/1193s per supervisor. Native timers include actual runner import/learning/evaluation/publication through exit; admission is adjacent outside GNU timing, and supervisor wall encloses its command. Per-original RSS peaks are not a measured simultaneous sum. Historical2461.16s was a coarse reference, not a hard cap or cost-law guarantee. No new numerical failed attempt exists, so these two originals are the complete numerical allocation cost; full support/provider/maintenance/agent/lifetime costs remain **UNKNOWN**.

Fresh adjacent physical/effective memory receipts both passed4GiB: low15629537280 bytes and reference15556071424 bytes; original cgroup fields are null as reported by the helper. [Execution](evidence/cluster_fixed_lr_pair_b01_20260914/EXECUTION.md), [acceptances](evidence/cluster_fixed_lr_pair_b01_20260914/ACCEPTANCE.json), [admission](evidence/cluster_fixed_lr_pair_b01_20260914/ADMISSION.json) and both preserved supervisor roots provide actual terminal evidence.

Monitor boundary: direct final terminal facts were received, but an adoption receipt was not. The child reconciled its earlier unsupported delivery/timestamp fields: adoption **unconfirmed**, actual query wall time unavailable, supervisor terminal times preserved, stable terminal events delivered through its native final, active_set[]. DM independently collected both terminal supervisor records. This is an observation-handover defect; it does not invalidate the independently recorded native measurements or establish real-time observer coverage. [Corrected monitor record](evidence/cluster_fixed_lr_pair_b01_20260914/MONITOR.json).

All28 original files (26 text,2 checkpoints) match remote/local SHA256 and byte lengths. Local retained archive `C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/cluster_fixed_lr_pair_b01_20260914/original_native.tar.gz`:2840872 bytes, SHA256 `c10b687a1652566f39b341cb3e278c872da3d5719eafd2e197fae3928f1fcbee`. Checkpoints each283253 bytes: low `7a9fe3078d20e0835a30063fcc9bd2d8e129469bd4033d9750dafba2d4ed5fdc`, reference `c371cf0341f2fe4370d1c0173aabe56effa85b80c8b6c63541b8f09bda460e59`. [Preservation](evidence/cluster_fixed_lr_pair_b01_20260914/PRESERVATION.json) and [manifest](evidence/cluster_fixed_lr_pair_b01_20260914/REMOTE_TERMINAL_MANIFEST.json) identify every original. Root confirmed retention; exact remote checkout, both inactive supervisor roots and owned staging were reclaimed, with disk and worktree-registration absence verified2026-09-15T02:52:59.786188Z in [CLEANUP.json](evidence/cluster_fixed_lr_pair_b01_20260914/CLEANUP.json). Shared authoring checkout, verified local originals/checkpoints and policy-denied local scratch remain intact.

## Bounded reading and prediction

At this fixed4096 exposure, the proposed low rate loses to reference on C and is lower on F and dwell descriptively. Retain3e-4 as the development reference; this is no stable ranking across programmes. Reference C attains.329215978929418 J and F still adds.03770462016249634 J over C and.03251075015598452 J over own-dwell. That directly supports optional-F usefulness on the higher attained reference endpoint in this pair; the usefulness is not restricted to its weaker low-rate C. It does not establish tuned headroom or compare old and new programmes as matched causal exposure changes. Reference F has16/64 adverse worlds against each control; their identities need not coincide.

Low-C forecast missed: UP/WITHIN/DOWN=.45/.35/.20, observedDOWN, Brier.965. Four F forecasts had modalUP and all observedUP; Brier lowF−C .14, lowF−dwell .245, referenceF−C .065, referenceF−dwell .14. Whole-pair completeness forecast.95 realized complete (binary Brier.0025). Owner prediction not taken (unattended); current reviews were checked at intake. Claim ceiling remains one B pair, no training-population uncertainty, causal rate/data diagnosis, safety, default promotion or formal transfer.

[Result figure](evidence/cluster_fixed_lr_pair_b01_20260914/RESULT_FIGURE.png) shows all six absolute panel means and all five prespecified contrasts; error bars are conditional SE, not training-population intervals.
