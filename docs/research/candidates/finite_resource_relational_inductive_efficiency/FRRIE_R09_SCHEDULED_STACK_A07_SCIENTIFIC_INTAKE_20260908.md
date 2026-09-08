# FRRIE A07 / P35–P37 scientific intake — 2026-09-08

**`A07_FATAL_CALLPATH_CAPTURED`: a valid narrower A/RECON path observation.**
The corrected execution ended with a fatal segmentation-fault report and exit139
after62.86s. Its current-thread Python stack reaches RNG address validation through
training-input generation. No scheduled-report header was retained. The scheduled
MEI was not met; no native-return comparison, completed-work count or crash cause
is established. P35/P37's sole scientific allowance has ended.

## 1. Evidence checked and rule applied

DM read the complete [CM E0](FRRIE_R09_SCHEDULED_STACK_A07_RESULT_EVIDENCE_20260908.md)
and [JSON](FRRIE_R09_SCHEDULED_STACK_A07_RESULT_EVIDENCE_20260908.json) at
`1d2bdbe02251f06f8bef132bb818d1cac1d98ecd`, integrated by Root as492f775f0,
against the [A07 card §§1–4,6–7](FRRIE_R09_SCHEDULED_STACK_A07_SCIENCE_CARD_20260908.md)
bound at `81b58964e1c266a7a120dbfde851464489342e4e`. The original1287-byte
payload remains at66cd6cd6522d1bde426046907c31d5eb488e4b43; the corrected
transport handoff remains atf9a785b6caf898ca120778812150de53a4991049.
[P35](../../portfolio/handoffs/2026-09-08-p35-frrie-scheduled-stack.md) and
[P37](../../portfolio/handoffs/2026-09-08-p37-frrie-a07-command-transport.md)
authorize this intake and stop. Evidence-spec §§3–4,5.1,11.8.1,11.8.6–7 govern
the claim and proportionate acceptance.

Read the retained corrected log/runner, time receipt, admission, remote source/
input/output readback and the two focused source excerpts. DM's local stdlib
check matched the primary log, time, admission and command bytes to E0, parsed
the16 frames and24 extension names, reconciled both timestamps and exit/status,
and checked RSS units and the complete cap. The original Git blob also confirms
`rng.py:133` is the `validate` definition boundary. Reused CM's collection and
technical checks; no remote command, target import, fixture or execution was
repeated. Receipt: `temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_collection_p37/dm_intake_checks.json`.

The card's applicable rule, verbatim:

> No usable scheduled-path reading applies, but a readable fatal stack locates the original process's caller context. Preserve the signal and path as a narrower observation, without relabelling it a scheduled sample or clearing any prior attempt.

No evidenced source/input/runtime/schedule/cap deviation makes the preceding
`A07_NONCONFORMING` row match. The unchanged command is not proof of successful
timer arming: that event and its timestamp remain unobserved. No attributable
`Timeout (...)!` scheduled header occurs, so `A07_SCHEDULED_PATH_CAPTURED` does
not apply. The explicit fatal header and readable original caller chain satisfy
the next row. Later Python-exception, normal-completion and inconclusive rows do
not replace this retained narrower observation. The missing primary scheduled
measurement limits its dependent claim, as §11.8.7 requires.

## 2. All outcomes, counts and receipts

| Attempt | Direct terminal evidence | Scientific exposure |
| --- | --- | --- |
| Original P35 wrapper, `frrie-a07-scheduled-stack-p35-43eec21e` | Start/end08:19:37Z; reported0 whole seconds; exit127, runner line10 backslash-command-not-found. Actual runner contains no preflight, GNU-time, Python or diagnostic payload. | Zero original preflight/scientific/arming/learner execution, established from runner/log control flow. This was not a scientific A07 sample. |
| Corrected P37, `frrie-a07-scheduled-stack-p37-43eec21e` | Supervisor PID2768577; Python PID2768586;08:36:02Z–08:37:05Z; exit139/failed;62.86s GNU time,63s reported supervisor duration. | One scientific invocation. Actual completed updates, episodes, tapes, optimizer calls and native slots are unknown. |
| CM collection / DM intake | Read existing bytes only. | Zero scientific invocations, imports, fixtures, rearms or samples. |

The failed wrapper's six original supervisor files remain preserved by the
[P37 handoff](FRRIE_R09_SCHEDULED_STACK_A07_P37_TRANSPORT_HANDOFF_20260908.md)
and local `exp/a07_transport_p37/failed_supervisor/` receipt. DM reread its
log/runner without modifying them. The corrected supervisor has its own log,
runner and terminal identity. Its unchanged payload intentionally used the
previously unused P35 scientific cwd/output and P35 `process-time.txt` path.
That time file measures P37, not the failed wrapper. There are two supervisor
attempts and one scientific invocation; no scientific budget was reset.

Corrected raw root: `temp/directions/finite_resource_relational_inductive_efficiency/exp/a07_collection_p37/`.
Its4004-byte `supervisor/task.log` has SHA256
`d2c0ce26cbb717029cf1e46734bd4178c402bd20d3c9d055c9a305eac7e761ca`.
The87-byte time receipt has SHA256
`d743a9b41fc7a921f8a507991550c28dbb0b3bf4063eecda25edd0e6e7fd3e54`.
E0 JSON preserves the full raw inventory and frame/extension arrays; remote
originals remain at the named accepted handle and scientific cwd.

The corrected source is original `43eec21e9584c83e5e8d940402d7e4570b454e59`,
with no tracked modifications; generated `_native/` is untracked. The script
readback is1287 bytes, SHA256
`8ed56ed4489b0d211355f74a1e91a07f9ae8ac1efc43cecf77c824a5fc56e51c`.
The30643b7359b35c6e9d5751147d0999bc629a966d helper/stdin digests are unchanged.
The pinned P22 system312 environment, root3, original schedule and one60s
`repeat=False, exit=False` argument remain the accepted invocation bindings.
Their identity does not establish internal scientific-state integrity.

Fresh admission at08:36:02.233145Z passed physical/effective availability:
15636484096 bytes (14.562610626GiB) against4294967296 bytes (4GiB).
GNU-time peak RSS is874680KiB =895672320 bytes (0.834159851GiB).
Cgroup headroom, aggregate CPU, scratch and complete descendant-memory coverage
remain unmeasured. Admission is an entry measurement, not sustained headroom.
The only published output file is504-byte `learner_admission.json`; `learner/`
is empty and no summary/A05 state exists. Absence is not zero completed work.

Both recorded durations are below TERM115s plus5s grace =120s. The measured
scientific invocation-wall sum is62.86s; control-plane elapsed is not measured
by it. A06's118.40s and A05's42.71s have no comparable completed-work denominator
and establish no throughput change. The current source/configuration ceilings
remain one chain×two arms×128 updates,8192 training/512 evaluation tapes,
16384 factual training episodes,256 Adam/backward calls and1316864 native slots.
Per-arm nominal LR exposure≤0.384 or7.68 initialization half-ranges is configured
exposure, not measured movement. No previous conditional count transfers here.

Engineering acceptance is limited to exact transport, preserved source/input
bindings, retained report and terminal facts. It does not accept a working
scheduled-report or learner-publication path. The card named one bounded
watchdog/report plus the existing fatal/exception facilities under scope §4;
no new source, framework or §5 budget breach is evidenced. Static tests and the
old inert capture fixture are not mechanism evidence.

## 3. Scientific interpretation and prediction

The fatal report labels current thread `0x0000717491b39080`. Read from outer
scientific callers toward the reported top, its path is `execute:242` →
`production_training_inputs:246` / tuple generator:247 →
`generate_episode_tape:369` → `uniform_float32:273` → `block:251` →
`canonical_bytes:204` → `validate:133`. The lower pdb/bdb/runpy frames are the
execution harness. No capture-helper or traceback-processing frame appears in
this retained chain. This locates an original training-input caller at a fatal
event, rather than an active exception-capture helper.

`validate:133` is a method definition boundary, not an identified faulting
expression or native instruction. The record contains no live `update`,
`number`, tape index, address fields, optimizer state or causal writer. It does
not prove a source defect in validation/serialization, exclude earlier native
effects, or identify Python, NumPy, Torch or the host as the cause. The separate
thread `0x00007173b9bff6c0` has `<no Python frame>`; its role is unknown. Do not
assign it to the watchdog, a worker or the fault. The24 listed extensions are
presence facts only. No explicit truncation marker appears, but native frames,
memory state and complete thread coverage are not certified.

**Scheduled MEI: not met.** Strongest support for the narrower positive path
reading is the fatal header plus the16 source-identifiable current-thread
frames. Strongest contradiction to the intended timed observation is absence
of any scheduled header followed by fatal termination. Proximity of62.86s to
the configured60s delay does not establish an emission time, successful arming
or watchdog causation. The shell's `(core dumped)` text supplies no retained
core location; CM/DM did not search for or open a core.

**Prediction check:** the scheduled-report forecast was not borne out: only a
fatal record was retained. Its original-program-location component is supported
by that narrower fatal path. The card's “earlier fatal” timing qualifier is
**unscored**, because neither arming time nor a scheduled emission time was
recorded; do not claim the fault preceded the60s deadline. This is not a scored
successful scheduled capture or a rewrite of the frozen prediction. Owner
prediction: **not taken (unattended)**; current main reviews were empty.

Reuse the verified facility distinction in [A06 intake §4](FRRIE_R09_FATAL_CALLPATH_A06_SCIENTIFIC_INTAKE_20260908.md)
and the source/RNG/native-interface grounding in [P23](FRRIE_R09_TRAINING_INPUT_P23_ASSESSMENT_20260907.md).
No new mechanism or comparator claim requires another literature search. The
new evidence changes the next observation question from a missing Python
caller to missing native fault context; it does not justify bypassing address
validation or `asdict`, and it leaves P23's source-correction absence bounded.

[DIRECTION](DIRECTION.md)'s R06–R08 learning evidence is unchanged: root1 N15
tight-minus-wide+0.005548293532 is conditional support; root2−0.001948094523
contradicts material recurrence. R08's root1 chart-cut attenuation
+0.000010174094 adds no independent-root evidence. R09 MEI0.005 and absent
tuned same-information host headroom remain unchanged. A05/A06 stay inconclusive,
P22 stays `R09_INVALID_INCOMPLETE`, and all historical quarantine remains.
A07 has no consumption state. No algorithm effect, reliability, C, family,
recast, UAV-entry, lifecycle or priority decision follows. No mechanism-level
update to DIRECTION is needed.

## 4. Decisions this intake produces

**1. Current object — technical.** Options: (a) accept the fatal-path fallback,
retain the scheduled miss and end P35/P37; (b) relabel the record as scheduled
from elapsed time; (c) infer a cause/completed-work count or repeat the task.
Recommend/select **(a)**. **Owner-delegated decision (unattended,2026-09-03 instruction): (a).**
This stop is applied. No relaunch, rearm, extra sample, cap reset, source repair
or new allocation remains in this task.

**2. Next discriminator — direction-local object advice.** Options: (a) return
a separately scoped native-fault-context task need; (b) repeat Python-only
capture or add scheduled samples; (c) patch the reported Python line or launch
another learning comparison without a justified route. Recommend/select **(a),
as a next-task recommendation only**. **Owner-delegated decision (unattended,2026-09-03 instruction): (a).**
Root passes this concrete need to Portfolio; DM does not allocate it or ask Root
to select the science.

**Exact missing observation:** native fault instruction/frame/module context
attributable to this original chain, sufficient to choose a bounded correction
or identify a credible alternative execution path. A Python method-entry line
does not provide it. A separately assigned task should reuse any already named
retained native crash material first; the current record names none. If absent,
the proposed alternative is one prospectively frozen native-fatal observation
of the same original43ee/system312/root3/full schedule, within a complete cap
no larger than120s. Freeze report bounds, execution/termination recipe, source,
inputs and fresh identity before an allocation. Reuse trustworthy same-host
debugger/containment facts where available; do not turn this into a separate
capability experiment, broad core search, setup campaign or causal panel.

Before recommending this diagnostic, compare a minimal real B: it could answer
performance on a credible execution path, but the present path has just lost
the primary comparison again. Repeating it unchanged adds learning exposure
without the newly missing native context. The proposed observation addresses
that specific dependency, not complete diagnosis of every prior cause; a later
B on an independently credible alternative need not solve unrelated history.
Even a native backtrace would locate a fault site, not automatically its causal
writer. No new source/runtime choice is justified or selected here.

Prospective algorithm work is still one chain×two arms×128 updates and the
section2 ceilings. Added observation would be one bounded native report, with
unknown overhead inside the same≤120s complete invocation, not additional arms,
seeds or a timing pilot. The62.86s is an observed failed-chain anchor, not a
duration forecast. Current new code/card/command/runtime allocation: zero.
Portfolio owns whether and when to commission this separate task.

Owner flags: **none**. Existing new-card P2
[20260908-frrie-002](../../portfolio/owner/inbox/2026-09-08/20260908-frrie-002.json)
remains; this ordinary intake/object-task advice creates no additional item.
The [Chinese brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-08_A07-scheduled-stack.md)
records the valid narrow result. No owner review or ledger override was present
for this direction at the clean-boundary check.

## 5. Clean boundary and audit rows

Authoring began clean at1d2bdbe02251f06f8bef132bb818d1cac1d98ecd in the reused
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`.
The accepted handle is terminal; CM collection is complete, with no further
diagnostic or implementation running locally. Commit/push only this intake,
the card's terminal status/record and Chinese brief. Root integrates them and
appends these rows. Shared Portfolio/audit paths are not edited by DM.

The existing A07 acceptance row08:09:35Z and P37 correction row08:29:26Z are
already present in main's September8 audit. The card §5 selection row07:57:59Z
is still absent at this intake; Root appends it once if still absent, preserving
its original text/time. A06's four rows are already integrated and need no replay.

```text
| 2026-09-08T08:51:09Z | finite_resource_relational_inductive_efficiency | object | technical | (a) fatal-path fallback and stop; (b) infer scheduled report from timing; (c) infer cause/counts or repeat | (a):A07_FATAL_CALLPATH_CAPTURED,one62.86s exit139 scientific invocation after zero-exposure P35 wrapper;scheduled MEI unmet;counts/cause unknown;P35/P37 allowance0 | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P35/P37 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_SCHEDULED_STACK_A07_SCIENTIFIC_INTAKE_20260908.md | none | |
| 2026-09-08T08:51:09Z | finite_resource_relational_inductive_efficiency | object | selection | (a) separately scoped native-fault-context task; (b) repeat/add Python samples; (c) unsupported patch/learning retry | (a):direction-local next-task recommendation viaRoot toPortfolio only;no new card/code/command/budget/invocation or cause claim | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P35/P37 return | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_SCHEDULED_STACK_A07_SCIENTIFIC_INTAKE_20260908.md#4-decisions-this-intake-produces | none | |
```

scope: none
