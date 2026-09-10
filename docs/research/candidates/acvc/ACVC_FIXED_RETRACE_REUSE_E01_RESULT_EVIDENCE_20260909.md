# ACVC fixed retrace reuse E01 — result evidence

Date: 2026-09-09. **Valid complete B/EXPLORE under the named §11.4.1 exception.**
The single allocated six-panel comparison completed. All four primary contrasts and both
secondary contrasts are **UP**. This is a preliminary fixed execution-package result
conditional on two selected retained trained bases; there were no new fits.

## 1. Frozen definition and received implementation

The [science card](ACVC_FIXED_RETRACE_REUSE_E01_SCIENCE_CARD_20260909.md) §§0,2–6 was
allocated at `7199ddc1a9173cd45c5734bb3991fbebf27d8428`, after Root's explicit allocation
`26f8b1abdf90d5cb34baf9eb7f14d138e5874901`. The complete Pro plan and its exact card/spec
application remain in the separate [Convergence intake](ACVC_FIXED_RETRACE_REUSE_E01_CONVERGENCE_INTAKE_20260909.md).
Neither the named exception nor this result reopens the stopped T/G selector.

CM published source **`6b269374d98886bce120ccde9bd6879ddc32882b`**, launch record
`11c17e04ccea6a3dbb0f0faa3ba8d2c2c154eaa1`, collection `9dd1cfcbb` and full supervisor
log `f7f47620f`. I checked the changed collector/stream/reducer/runner, focused-test
coverage and CM record against the card. Dwell uses its own unchanged Binding predicate,
zero velocity on its mask and its actual sent command as the next recurrent input. F retains
actual-displacement retrace. Ordered stochastic base proposals run on every step. Appending
dwell's stream index preserves old arm indexes. The six-panel runner constructs no gate,
critic or optimizer, retains all rows and reports each base separately.

CM's one focused synthetic check passed, covering commands, recurrence feedback, streams,
per-base reduction and publication. Independent semantic reviewer `review_acvc_link_loss`
found no remaining material issue; Root independently accepted that source/check/review
evidence. No native smoke, profile, broad repeat, retry or extra panel was performed.
Binding and the shared native/base sources were unchanged. Engineering-scope §4 additions:
none; 251 inserted lines across the six source/record/test files, including a 110-line runner,
remain below the applicable source/runner budgets. The passing test is conformance evidence,
not evidence of native value. E01 test scratch was removed; the historical P78 cleanup blocker
is separate and is not silently declared resolved.

## 2. Rule applied verbatim and all outcomes

> **UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**, retaining the sign.

The four primary contrasts are F-C and F-dwell for each base. Dwell-C is secondary.
Each contrast has 64 paired joint episodes; conditional SE is sample SD/sqrt(64).
Every native row retains S, J=S/256, base, rule, episode and reset seed. No return is
filtered by opportunity counts and no cross-base aggregate is the primary.

| Retained base | C mean J | F mean J | Dwell mean J |
|---|---:|---:|---:|
| DENSE/8201 | 0.1765850150 | 0.2842835951 | 0.2153539833 |
| DENSE/8202 | 0.1837095479 | 0.2716257515 | 0.2141804550 |

| Base | Contrast | Mean ΔJ | Mean ΔS | Conditional SE(J) | Adverse pairs /64 | Rule |
|---|---|---:|---:|---:|---:|---|
| 8201 | F-C | +0.1076985801 | +27.5708365049 | 0.0066070154 | 1 | UP |
| 8201 | F-dwell | +0.0689296118 | +17.6459806273 | 0.0071954850 | 7 | UP |
| 8201 | dwell-C | +0.0387689683 | +9.9248558776 | 0.0065200519 | 14 | UP |
| 8202 | F-C | +0.0879162035 | +22.5065481047 | 0.0079107102 | 7 | UP |
| 8202 | F-dwell | +0.0574452965 | +14.7059958962 | 0.0086159352 | 11 | UP |
| 8202 | dwell-C | +0.0304709071 | +7.8005522086 | 0.0073302998 | 21 | UP |

The [384 rows](fixed_retrace_reuse_e01_20260909/episodes.jsonl) and
[full summary with paired vectors](fixed_retrace_reuse_e01_20260909/summary.json) are retained.
CM independently recomputed the reductions from rows. DM's
[compact analysis](ACVC_FIXED_RETRACE_REUSE_E01_DM_ANALYSIS_20260909.json) reads those
accepted vectors to count adverse outcomes and score the original predictions. No extra
evaluation or resampling was run.

## 3. Actual exposure and information boundary

Machine-generated exposure: **retained_base_fits=2; new_fits=0; training_episodes=0;
training_team_steps=0; optimizer_updates=0; parameter_displacement_during_evaluation=0;
fixed_panels=6; scored_evaluation_episodes=384; team_steps=98304;
base_agent_forwards=491520; base_loads=6; environment_constructors=6;
unscored_constructor_resets=6; gate_constructions=0; critic_constructions=0.**
All six loaded bases had measured zero displacement after loading. Recurrent-state updates
and sampled proposals are not parameter learning. The arithmetic 2×3×64×256×5 accounts for
the base forwards; 13,107,200 is the declared coordinate-pair upper count, not measured work.
Each retained fit's historical 512 training episodes/131072 steps remains old provenance.

| Base | Rule | Eligible opportunities | Executed intervention | Distinguishable commands |
|---|---|---:|---:|---:|
| 8201 | F | 8123 | 8123 retraces | 8123 |
| 8201 | dwell | 5587 | 5587 dwells | 5587 |
| 8202 | F | 7775 | 7775 retraces | 7775 |
| 8202 | dwell | 5771 | 5771 dwells | 5771 |

C bypasses Binding, so its zero opportunity counters mean **unmeasured by that path**, not
absence of link loss. Its unconditional proposals still execute on all steps. F/dwell counts
are on their own trajectories, not matched events or intervention doses. Their differing
counts are consequences of the compared packages, not eligibility exclusions or a causal test.

The native host remains five fixed UAVs, 50 users, 256 primitive steps, CPU FP32 and Torch
intra/inter-op threads 1. Private recurrence and actual-command feedback are intact. The
preceding observation may supply a saturated-list anchor; the loss cue excludes a currently
saturated/empty list and requires the accepted unique anchor/away-dot conditions. No entity
membership, reward, privileged input, optimizer or partner-learning change was introduced.

## 4. Receipts, complete cost and accounting correction

Execution node: `wsl_4070` / `hmasd-wsl-node`; source cwd
`/home/wu/hmasd-worktrees/acvc-fixed-retrace-reuse-e01-20260909`; accepted handle
`acvc-fixed-retrace-reuse-e01-20260909`. The native output was
`temp/directions/acvc/exp/fixed_retrace_reuse_e01_20260909` under that exact-source checkout.
Both staged checkpoints matched their frozen digests, as recorded in the
[technical collection](ACVC_FIXED_RETRACE_REUSE_E01_TECHNICAL_COLLECTION_20260909.json).
The original CM owns collection and scoped closeout; Root owns closeout acceptance.
Root has now accepted that closeout: all 2,338 archive members were verified before the
named execution cwd, supervisor directory and staged-input directory were removed; disk,
worktree registry and PID absence were confirmed. Source recovery ref
`refs/recovery/acvc-fixed-retrace-reuse-e01-20260909` and original checkpoint assets remain.
The preservation report is
`C:/Projects/HMASD/temp/recovery/acvc-e01-closeout-20260909/recovery-acvc-fixed-retrace-reuse-e01-20260909.tar.gz.preservation.json`;
the local/remote archive SHA256 is
`7054ec5061bdcc8a042546c5edd1589ad3b5544f253a57dba7a25dae3cbb5a8a`.
No evidence was deleted before verified preservation, and no DM scientific invocation or
index action was part of that CM/Root closeout.

Fresh actual-node [admission](fixed_retrace_reuse_e01_20260909/e01_admission.json) at
23:00:59.794760Z passed with physical and effective available memory **15,217,790,976 bytes**,
above 4 GiB. Monitor adoption was confirmed at 23:01:38.7534034Z; terminal exit 0 was
observed at 23:02:51.3907047Z for actual exit 23:02:19Z. CM then collected the same handle;
no concurrent CM polling or another launch occurred. [Supervisor log](fixed_retrace_reuse_e01_20260909/task.log)
and [actual-exit process timing](fixed_retrace_reuse_e01_20260909/e01_process_time.txt) are preserved.

The precise timed scientific process is **79.46 s wall**, **79.35 s CPU** (79.17 user +0.18
system) and **415800 KiB peak RSS**. It includes imports, six loads/constructors, evaluations,
publication and actual exit, but the memory preflight precedes `/usr/bin/time`. CM confirmed
this scope after my intake query; no extra execution was needed. Its initial **86.81 s** bill
therefore omitted preflight/startup and is superseded here, not overwritten in the raw record.
The whole supervisor task reports **80 s** at whole-second precision. Conservatively charge
**81 s** for that whole task, including preflight/startup and rounding.

Supporting work is **8.35 s**: focused acceptance 4.35 s (measured 4.3434695), CM collection
and publication 3.00 s (measured collection 2.4465633), and DM summary analysis/publication
1.00 s (measured command 0.0747992). **Final complete charged work is 89.35 s**, below 180 s;
support is below 30 s. Unused allowances are **90.65 s complete /21.65 s support**, not
permission for another invocation. The single serial task's critical path and summed task
wall both use the same reported 80 s; the conservative charge is 81 s, not six renewed caps.
Human authoring/review/Git/transport work is outside machine invocation wall. Supporting CPU
and scratch high-water remain unmeasured; admission and peak RSS do not establish a runtime
memory-floor trace or CPU affinity. No scientific/engineering cap was breached.

## 5. Bounded reading and handoff

F is the strongest attained fixed package on both of these selected bases. Dwell's own UP
gains show that withholding an away proposal is useful here, but its lower mean leaves an
additional observed F-package margin. This comparison does not isolate retrace causality,
history necessity, matched cues, optimality, learned-selector value or transfer. The adverse
episodes, selected old fits and absent tuned upper/baseline headroom remain explicit.

The [scientific intake](ACVC_FIXED_RETRACE_REUSE_E01_INTAKE_20260909.md) records predictions,
the object-tier acceptance and the unselected next discriminator. This B object is complete;
A/B objects have no consumption state. The one invocation allocation is spent. No successor,
retry, additional panel, T/G reopening, direction lifecycle change or Portfolio action follows.
