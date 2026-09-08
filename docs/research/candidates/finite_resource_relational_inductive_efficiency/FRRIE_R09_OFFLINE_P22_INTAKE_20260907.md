# FRRIE original R09 offline P22 intake — 2026-09-07

**`R09_INVALID_INCOMPLETE`: no valid third-root comparison.** The sole allocated
offline chain completed package setup and passed both admissions, then the original
program raised `TypeError: 'Field' object is not iterable` during training-input
construction. Whole-chain wall was 61.54 s. Native evaluation work was reached, but
no primary, return curves or exact optimizer counters survived. The later debugger
`NameError` messages and supervisor exit 0 do not change this reading. No retry follows.

## 1. Assignment, evidence checked and rule applied

Current authority is [P22](../../portfolio/handoffs/2026-09-07-p22-frrie-offline-r09-execution.md)
at `ba4d4fe0609633591a423b1bc7bdbdda10451068`, allocating one complete chain from the
[P21 handoff §§1–4](FRRIE_R09_OFFLINE_RUNTIME_P21_HANDOFF_20260907.md) at
`a3bcd75123825fa34c833db5104aced33d268009`. P22 supersedes P21's preparation-only
allocation for this exact invocation. The current Portfolio command supplies that
authority; its older A03 row and historical card header are provenance, not a veto
or another allocation. No lifecycle or priority is changed here.

DM checked the [R09 card](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md), particularly
work/rule, prediction, runtime amendment and fixed debugger requirements; the
[CM E0](FRRIE_R09_OFFLINE_P22_RESULT_EVIDENCE_20260907.md) and
[companion JSON](FRRIE_R09_OFFLINE_P22_RESULT_EVIDENCE_20260907.json) at
`dd6fd9bdac3d806842a0622372e87befb7096212`; retained full task log, first traceback,
admissions, runtime metadata, process-time record and noncache output inventory.
The necessary source range was `b01_contact_r02/experiment.py:153–242`, establishing
what precedes the failing call. CM's source/command/input comparisons and native
collection are reused; no remote collection, build, test or execution was repeated.

Applied evidence spec §§2–4, 5.2, 6.1–6.2 and 11.4/11.8, especially §11.8.7:
an independently trustworthy setup fact survives, while the missing primary cannot
support its dependent performance claim. This does not require a unique root cause
before the incomplete attempt can be classified. DIRECTION's accepted R06–R08 and
A03 sections, the current Portfolio row and owner surfaces were read. The mechanism
and comparator are unchanged; their existing grounding is reused, with no new
literature or mechanism claim inferred from this technical exception.

First matching card row, **verbatim**:

| branch | rule and bounded reading |
| --- | --- |
| `R09_INVALID_INCOMPLETE` | Common integrity fails; actual seed/root/label/LR binding differs from this card; fresh actual-node admission is missing or below 4 GiB; nonzero planned learner/update/evaluation work or exposure/curves are missing; information/work/raw initialization pairing fails; actual initial projection disagrees with direct clipping; contact history is misreported; or projection changes optimizer moments. Quarantine, no result. Zero initial clipping itself is valid. |

Required completed work, N15 primary, full N9 curves and actual exposure/contact
evidence are absent. DM applies this first row; **the runner published no branch
label**. It is not a no-contact, within-MEI, adverse or favored result. Optional
resource or debugger telemetry alone would not invalidate this non-resource B;
the missing learner-dependent measurements do. B has no consumption state.

## 2. Direct facts, inferred work and cost

Accepted handle `frrie-r09-system312-offline-p21-43eec21e` ran on `hmasd-wsl-node`,
PID 2761895, from 2026-09-08 04:39:08Z to 04:40:09Z. The exact scientific/preflight
source remains `43eec21e9584c83e5e8d940402d7e4570b454e59`; remote cwd is
`/home/wu/hmasd-worktrees/frrie-r09-system312-offline-p21-43eec21e`. Its output root is
`temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_system312_offline_p21`.
The `learner/` directory exists and is empty. Setup log, runtime metadata and learner
admission remain, together with the separately retained setup admission and native binary.

CM checked 62 source/input paths against the bound bytes, and the accepted command
is the published 3,419-byte payload with digest
`f5e04fc2e3d0c0d0fb0e702914173a4e7a48d51321ef6c5ec416dc2ad8cb6b28`.
The 528-byte fixed stdin matches
`00631d27830cfb14b002aa0268d5ccc5d3b40a72a7a8f7d44a3c4ce295a7da65`.
These are scoped currentness/identity facts, not complete runtime equivalence.
Root's terminal observation and the retained log agree. After post-mortem `q`, the
debugger reports restart, stops at module line 1 and reaches EOF; no second
continuation or scientific traversal is evidenced. Collection initiated none.

| Quantity | Retained observation or explicitly conditional inference |
| --- | --- |
| Dedicated setup | One system CPython 3.12.3 / GCC 13.3.0 venv; all 23 pinned distributions installed, including NumPy 1.26.3 / Torch 2.7.0+cu118 / Triton 3.3.0 |
| Setup admission | 04:39:08.370172Z; physical/effective each 15,640,940,544 B, above 4 GiB |
| Learner admission | 04:39:15.082287Z; physical/effective each 15,618,752,512 B, above 4 GiB; adjacent to original runner |
| Original exception | `TypeError: 'Field' object is not iterable`, system `dataclasses.py:1286`, from RNG-address `asdict(self)` during `production_training_inputs` |
| Secondary debugger errors | `obj`, `self` and `number` unavailable in the selected frames; no recovered failed-update or object value |
| Published scientific result | None; no summary, N15/N9 value, curve, checkpoint summary, contact or actual exposure |
| Work reached, source-flow lower bound | 512 evaluation tapes; two uniform and four learned checkpoint-0 cells; at least 1,536 evaluation episodes / 18,432 native evaluation slots |
| Training work | Exact failed update and optimizer/episode counts unknown; ordinary source flow permits failed update 1–128, completed paired updates 0–127 and Adam calls 0–254 |
| Whole-chain wall / supervisor duration | 61.54 s / 61 s at integer resolution; one accepted invocation |
| GNU-time peak RSS | 674,988 KiB = 691,187,712 B; not a simultaneous sum of worker RSS |

The work lower bound follows source call order, not recovered scientific counters:
evaluation tapes and uniform cells precede model initialization; both arms' N9/N15
checkpoint-0 evaluations precede any training-input call. The observed traceback
is at that later call. A retained native `.so` and this ordering support build/load
reachability. No numerical score survived, so these facts establish neither valid
native return nor comparator competence. Checkpoint 32 or 64 might have occurred;
the exact failed update is unavailable. Do not replace unknown optimizer work with zero.

Local stdlib calculations checked raw admissions/runtime against E0, exact rule text,
traceback ordering, output absence, `6×256×12=18,432` evaluation slots and RSS conversion.
The receipt is `temp/directions/finite_resource_relational_inductive_efficiency/exp/p22_offline_r09_collection_20260907/dm_intake_checks.json`.
The independent unit is the **one accepted attempt**. There is no selected endpoint
for run-level aggregation; evaluation episodes and checkpoints are not training seeds.

Planned exposure remains `2 arms ×128 updates ×64 factual episodes =16,384 episodes`,
256 Adam calls, 196,608 learner transitions, 1,261,568 training-native slots and
55,296 evaluation slots across 18 cells. The total is 1,316,864 native slots.
`128×0.003=0.384` and `0.384/0.05=7.68` describe planned nominal LR exposure only;
actual updates, contact and displacement are unknown. Collection/intake add **zero
result-bearing invocations**; P22 itself used its one allocated chain.

The complete wall includes setup, imports, build, reached work and termination.
It is below the original 14,400 s per-arm and 28,800 s complete caps; no timeout or
budget breach is recorded. Arm attribution, aggregate CPU and scratch remain
`resources_unmeasured`. Charge 61.54 s to this incomplete FRRIE attempt, adding no
valid-result denominator and no CBSC acquisition cost. It supplies no training-cost
rate or runtime speedup estimate. The existing source's formal-sized publication
coverage remains open; prior focused source acceptance is not erased or promoted
by this failure. Engineering-scope §4 additions: none; the card's existing fixed
pdb observation alone was reused. No new §5 source-budget breach occurred.

## 3. Bounded interpretation and prediction

The offline dedicated-runtime setup is now directly observed for FRRIE. The strongest
evidence against extending that fact to full readiness is this original-program failure
after native evaluation. A04's shorter T0 completion and shared CBSC imports remain
valid within their scopes. Neither predicted or established complete R09 execution.
This new-stack failure prevents attributing full-chain reliability solely to changing
away from the old uv build; it does not identify a common causal agent across attempts.
The live dataclass/iterator state, RNG address and failed update were not captured.
Source, native-memory and host/runtime explanations remain unclassified. Historical
quarantine and the old substrate's A03 stop are unchanged.

The scientific mechanism still runs from fixed-role partial observations through
beta-weighted partner aggregation to native scan/uplink/radio actions and
delivery/balance/waste return, with RSCF/Adam exposure under tight versus containing
wide boxes. P22 supplies no retained learned-return contrast along that path. The
MEI remains 0.005 and tuned same-information host headroom remains absent.

Strongest existing learning support is R06 root-1 N15 `+0.005548293532`. R07 root-2
`−0.001948094523`, inside the MEI, contradicts assuming material recurrence. R08's
same-root chart-cut attenuation `+0.000010174094` did not remove the known gap and
adds no independent root. Generic projected-Adam/shrinkage, path-specific
co-adaptation and roster dependence remain. No scientific sign is pooled from P22,
and no superiority, equivalence, mechanism attribution, transfer or UAV claim follows.

The low-confidence R09 prediction `R09_N15_WITHIN_MEI`, conditional on contact and
N15 EDGE competence, remains **unscored**. This is an earlier nonidentifying branch,
not evidence for a zero gap. Owner prediction: **not taken (unattended)**.

## 4. Decisions this intake produces

1. **Object-tier technical decision.** Options: (a) classify this attempt as
   incomplete, preserving setup facts, conditional work bounds and unknown cause;
   (b) infer a no-contact, within-MEI or adverse root-3 result; (c) withhold the
   incomplete classification until all historical causes are explained.
   Recommend/select **(a)**. **Owner-delegated decision (unattended, 2026-09-03
   instruction): (a).** The card receives a current-boundary update only; its
   question, root, source, semantics, six branches, MEI and prediction are unchanged.
2. **Execution boundary under P22.** Apply the named stop and return the unresolved
   technical problem through Root to Portfolio. A retry, resume, source repair,
   diagnostic invocation, new seed or successor is not selected or allocated here.
   This is completion of the current execution command, not direction-level PARK,
   a recast, object consumption or a Portfolio disposition.

**Exact remaining task need:** training-input construction on the original chain
fails in `SemanticRNGAddress.canonical_bytes → asdict → dataclasses.fields`. The record lacks
the actual address/dataclass field-container state and update at failure, and does
not establish a source correction. Recommend a separately scoped, targeted failure
assessment/repair of this dependent path, using the retained traceback and source
first and returning a concrete correction or the exact bounded observation needed.
No broad historical-cause census, renewed package acquisition, import certificate
or blind full R09 repeat is justified by this intake. That next engineering or
result-bearing assignment requires its own scope and allocation; Root forwards
this need and does not select the research task.

The eventual scientific discriminator remains the same fixed third-root paired
native-return measurement with full N9, if a subsequent authorized route can
produce trustworthy training and primary measurements. This is not an assertion
that the current route is ready or that all old failures must first be explained.

## 5. Owner surface and integration

At this clean boundary `item.py reviews --json` on main returned `[]`; relevant
FRRIE ledger owner cells are empty. No instruction or prediction reply was available
to apply or mark answered. Owner flag: none. No new P1/P2 item is created for this
ordinary technical intake and scoped blocker return. The
[Chinese brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_P22-offline-r09-incomplete.md)
labels the attempt incomplete rather than a valid algorithm result.

CM collection was excluded from the temporary comparison because it contained no
coding and no new invocation; Root records that concrete exclusion once. Raw evidence
remains under the E0's collection root and original remote locations. This checkout
is the shared `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`;
CM returned clean at `dd6fd9bdac3d806842a0622372e87befb7096212`. DM changes only this
intake, the card's current-boundary wording and the brief. DIRECTION, scientific
source, shared Portfolio/audit and other writers' paths are preserved.

Root integrates the named E0 and this intake commit if absent, then appends this
row to `docs/research/portfolio/audit/2026-09-07.md`; it is not already appended here:

```text
| 2026-09-07T21:54:08-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) retain incomplete attempt plus bounded setup/work facts; (b) infer scientific sign/no-contact; (c) wait for complete historical cause | (a):R09_INVALID_INCOMPLETE,61.54s,original dataclasses TypeError;23-pin setup and admissions pass,at least1536 evaluation episodes by source flow,optimizer counts and primary unknown;no retry | yes | OWNER_DELEGATED (unattended,2026-09-03 instruction); P22 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_OFFLINE_P22_INTAKE_20260907.md | none | |
```

scope: none
