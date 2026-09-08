# FRRIE A05 P27 scientific intake — 2026-09-07

**Decision: `A05_INCONCLUSIVE`.** The one allocated chain ended in a segmentation
fault after 42.71s without a retained Python traceback, state capture or learner
publication. This is a bounded A/RECON termination observation, not a completed
target-state measurement. The P27 allocation is finished; no additional invocation
is released. P22 remains `R09_INVALID_INCOMPLETE` and the R09 learning question is
unanswered.

## 1. What was checked and the rule applied

Authority is P27 at `a10e37e5161ae444f24db08844c621738ddbad7d` and the
[A05 card](FRRIE_R09_FIRST_EXCEPTION_A05_SCIENCE_CARD_20260907.md) §§1–7, bound at
`c77ab7ce8e9a256985052c4c43ae69d618f4b224`. CM's
[E0 and adjacent JSON](FRRIE_R09_FIRST_EXCEPTION_A05_RESULT_EVIDENCE_20260907.md)
are committed through `25c04d9a08b23f067f2edf11100204c26347774f`, following
`073ec7b70`. Scientific source is original
`43eec21e9584c83e5e8d940402d7e4570b454e59`; diagnostic helper/input are
`30643b7359b35c6e9d5751147d0999bc629a966d`; the exact Root handoff is
`137ed1fda47662f4eb51fa9d70f41a6a3675d2a2`.
The [evidence specification](../../specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) §11.8
controls the bounded claim and proportional checks; missing optional telemetry
does not replace the required primary observation.

DM read the complete E0/JSON against the card, the actual supervisor log and
exit/status/time receipts, source/staged-byte readback and output inventory.
The log directly reports `Segmentation fault (core dumped)` for Python PID 2765962.
Root observed the same handle terminal, supervisor PID 2765954, with tmux inactive.
This establishes more than the earlier exit139 notice alone; it still supplies no
crash location or causal writer.

The accepted command file has 1187 bytes and SHA256
`2976134a5690041fea083bef024aff1e28c92225c4d42479ccca38599893976d`, matching
card §7. CM decoded the supervisor literal and checked the staged helper/input;
DM read that evidence and independently checked the retained command binding.
Remote source is original 43ee with no tracked changes; the untracked native
library is a 24488-byte build artifact. Its existence and identity do not establish
which native calls ran or caused the failure.

DM used stdlib analysis to match admission/time values to E0, calculate resource
units, verify that the output contains only `learner_admission.json` and an empty
`learner/`, and check the absence of a traceback, target TypeError and
`A05_SUMMARY_WRITTEN` marker. Actual update/episode/slot fields remain null.
CM's ten-file raw checks and remote collection were not repeated. The parent
readback is retained as
`temp/directions/finite_resource_relational_inductive_efficiency/exp/a05_collection_p27/dm_intake_checks.json`.

Apply card §3's first matching rule, verbatim:

> Failed admission, different first exception, missing state/publication, timeout or hard failure prevents the preceding readings. Record the exact boundary and every trustworthy partial fact; stop without retry, clearance or scientific polarity.

No source/input/cap breach or second traversal was observed to trigger the earlier
nonconforming row. Both target-state rows require a target exception and complete
state capture, neither retained here. Hard failure excludes normal completion.
Thus **`A05_INCONCLUSIVE`** is the applicable row. This is DM's application of the
frozen rule, rather than acceptance of the CM label alone. Absence of a recorded
Python exception establishes neither recurrence nor nonrecurrence of P22's error.

## 2. Counts, cost and observation ceiling

| Quantity | Actual retained fact |
| --- | --- |
| Node / handle | `hmasd-wsl-node` / `frrie-a05-first-exception-p27-43eec21e` |
| Start / terminal UTC | 2026-09-08T06:24:06Z / 2026-09-08T06:24:48Z |
| Accepted logical invocations / remaining P27 allowance | 1 / 0 |
| Complete process wall / summed invocation wall | 42.71s / 42.71s |
| Complete cap | TERM115s plus at most5s grace,120s maximum |
| Peak RSS | 873284KiB =894242816 bytes =0.832828522GiB |
| Fresh physical/effective memory admission | Passed at06:24:06.215770Z;15650717696 bytes available against4294967296-byte floor |
| Completed target-state captures | 0 |
| Actual updates, Adam/backward calls, episodes, tapes and native slots | Unknown; not zero by inference |
| Valid new learning results / independent-root evidence | 0 / 0 |
| New result-bearing invocations during collection/intake | 0 |

The original root 3/128-update/two-arm schedule was configured, not measured as
complete. Its maxima in card §4 are exposure limits, not A05 execution counts.
Historical P22 conditional lower bounds cannot be assigned to A05. This A object's
independent unit is the one diagnostic invocation; repeating the same root in a
failed attempt does not add an independent learner seed.

Mark `resources_unmeasured` for aggregate CPU, scratch, cgroup headroom and per-arm
times; study/control-plane elapsed is also unmeasured. Admission and peak RSS do
not prove uninterrupted headroom or aggregate concurrent memory use. Missing
optional telemetry is not the reason for the inconclusive result: the required
state/publication is absent.

CM found no existing core or fatal-stack artifact inside this handle's owned cwd,
output or supervisor paths. The shell's core-dump notice does not establish a
retained readable core there; system-managed locations elsewhere were not assessed.
There was no debugger analysis or broad host search. This limit remains explicit.

Engineering acceptance covered the bounded helper's output and pdb termination
using two inert children and a focused missing-attribute correction check. It did
not test the original learner's complete publication pipeline or certify its
runtime. The added helper remains 284 lines plus the 2-line input, with 200 test lines
separate; only the card-named optional exception-state observation was added.
No scope-spec §5 breach is evidenced. The campaign's completed-three-batch CM
comparison exclusion remains unchanged.

## 3. Scientific interpretation and prediction

The categorical MEI—one complete target-state capture distinguishing malformed
from apparently ordinary structure—was **not met**. No address, field-table,
generator or execute state was captured. The hard failure does not decide whether
such state was ordinary or malformed, where it changed, or whether Python, native
code, a library, the debugger or the host is responsible. A missing traceback is
not a source-supported repair instruction.

The strongest support for the bounded reading is the same-handle terminal log,
matched source/command and empty publication inventory. The strongest limitation
is the complete absence of the requested live state and execution counters. The
inert success supports the recipe's checked paths; this real hard failure prevents
extending that support to the original runtime.

DM predicted `A05_TARGET_MALFORMED_STATE` with low confidence. Under the frozen
prediction rule, **unscored: failed state collection**. A process signal without a
recorded first Python exception is not a scored different-exception outcome.
Owner prediction: **not taken (unattended)**; main reviews were empty at intake.

The learning record remains [R06–R08 in DIRECTION](DIRECTION.md): root 1 N15
tight-minus-wide return `+0.005548293532` is conditional positive support; root 2
`-0.001948094523` contradicts assuming material recurrence. R08 reuses root 1 and
its `+0.000010174094` chart-cut attenuation does not remove the known gap or add
independent-root evidence. R09 MEI 0.005 and the absent tuned same-information host
headroom record are unchanged. No stable-superiority, mechanism, transfer, UAV or
C-BENCH claim follows. A05 has no consumption state, and no family/lifecycle
disposition is made. DIRECTION requires no mechanism-level update.

## 4. Decisions this intake produces

**1. Current object — technical.** Options: (a) record the frozen inconclusive
reading, preserve all evidence and stop P27; (b) infer a target-state result or
runtime cause from exit139; (c) extend/retry the allocation. Recommend/select
**(a)**. **Owner-delegated decision (unattended,2026-09-03 instruction): (a).**
The stop is applied. It is not a direction PARK or an R09 negative; the original
P22 invalid reading and all prior exposure remain intact.

**2. Next discriminator — direction-local object advice.** Options: (a) seek one
bounded first-fatal-callpath observation; (b) repeat the same post-mortem-only
recipe or a blind full B; (c) rewrite source without a supported correction.
Recommend/select **(a) as the next-task recommendation only**.
**Owner-delegated decision (unattended,2026-09-03 instruction): (a).** No new card,
diagnostic bytes, scientific invocation or budget is frozen/released by this intake.
Root returns the task need to Portfolio under P27's named return route; priority,
capacity, lifecycle and allocation remain outside this decision.

The next observation should locate the active Python call path at a fatal failure,
including whether it lies in original execution, traceback handling or capture.
It need not identify the causal writer or reconstruct the full address state.
An already-retained, readable fatal artifact could answer this without a new run;
an exhaustive crash-dump census is not a prerequisite. If fresh observation is
selected, changing the observation channel has decision value that an unchanged
PDB-only retry lacks. A blind real B has the same missing-location risk and the
larger full schedule as its work envelope.

The [CPython 3.12 documentation](https://docs.python.org/3.12/library/faulthandler.html)
documents startup `-X faulthandler` support for fatal signals including SIGSEGV,
with Python frame information sent to stderr. Its bounded record is at most 100
threads by 100 frames, with 500-character string limits; it does not expose address
locals or identify a causal writer. This verified documentary capability changes
the prospective observation choice. It is not a test of this pinned runtime and
does not promise that this failure will leave a readable trace. No mechanism,
comparator or related-work claim is being recast; P23's source assessment remains
the relevant local grounding, and no additional paper search substitutes for the
missing runtime state.

**Exact next task requested through Root:** scope preparation and, only under a
new explicit allocation, one A/RECON first-fatal-callpath observation. Reuse
original 43ee, the P22 system312 environment/pins, root 3 and original schedule;
the minimal prospective amendment is startup fatal-traceback reporting alongside
the accepted A05 post-mortem recipe. Use a fresh handle/output and a complete cap
no larger than 120s. Freeze its exact observation input and stop rule before any
launch. No source repair, package setup, broad causal panel, added learner seed,
fallback or automatic continuation is included.

Prospective dominant work is **at most 1 chain × 2 arms × 128 paired updates**,
with the original 512 evaluation/8192 training-tape and 18-cell schedule as linked
in card §4; actual learning exposure is unknown until observed. The same configured
maxima are 16384 factual episodes, 256 Adam/backward calls and 1316864 native slots.
Fatal-frame reporting is added bounded observation, not another learner arm.
The measured 42.71s is a known anchor, not a recurrence/completion forecast; the
prospective 120s includes all computation, reporting and termination. Existing
capture acceptance is reused; a new smoke or cost experiment is not requested.

Owner flags: **none**. No new P1/P2 item is warranted for this ordinary technical
intake/task recommendation; the existing new-card item is
[20260907-frrie-002](../../portfolio/owner/inbox/2026-09-07/20260907-frrie-002.json).
No owner instruction or prediction reply was inferred. The
[Chinese owner brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_A05-first-exception.md)
records the result without requiring owner action.

## 5. Clean boundary and audit rows

The run is terminal and the CM/DM authoring checkout remains the existing
`C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, branch `codex/frrie`.
All remote artifacts remain in place. This intake changes no original source,
historical input, P22 evidence, R09 decision rule or shared Portfolio document.
Root integrates the accepted evidence and this intake, appends these rows, and
returns the named next-task need to Portfolio. No fresh run is pending locally.

```text
| 2026-09-08T06:47:36Z | finite_resource_relational_inductive_efficiency | object | technical | (a) frozen inconclusive reading and stop; (b) infer target state/cause; (c) retry/extend | (a):A05_INCONCLUSIVE,one42.71s chain,exit139,required state absent,counts unknown;P27 allowance0 | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P27 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_SCIENTIFIC_INTAKE_20260907.md | none | |
| 2026-09-08T06:47:36Z | finite_resource_relational_inductive_efficiency | object | selection | (a) bounded first-fatal-callpath task; (b) unchanged post-mortem retry/blind B; (c) unsupported source rewrite | (a):direction-local task recommendation to Portfolio viaRoot only;no new card/input/budget/invocation released | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P27 return | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_FIRST_EXCEPTION_A05_SCIENTIFIC_INTAKE_20260907.md#4-decisions-this-intake-produces | none | |
```

scope: none
