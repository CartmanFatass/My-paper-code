# RCLE fresh1000 S22 intake — 2026-09-10

**Decision:** retain the incomplete attempt and accept only independently intact W1
and completed-block facts. The selected seed22 W100/W1 comparison is unavailable;
S21 remains the only complete same1000 training pair. No scientific retry was launched.

Evidence: [E0](RCLE_B03_FRESH1000_S22_RESULT_EVIDENCE_20260910.md),
[machine readback](RCLE_B03_FRESH1000_S22_RESULT_SUMMARY_20260910.json),
[frozen card](RCLE_B03_FRESH1000_S22_SCIENCE_CARD_20260910.md),
[execution/diagnostic repair](RCLE_B03_FRESH1000_S22_EXECUTION_20260910.md),
[Chinese brief](../../portfolio/owner/briefs/roster_consistent_latent_exploration/2026-09-10_RCLE_B03_FRESH1000_S22.md).
Runnable evidence source9a11fb084a16f293c27f3bd1fe8275dc19bd1a47; frozen cardd09667fcc.
Later reporting-only repairce189071a9487de36c7e1347508f1dcf0ed3f432 was not executed scientifically.

## 1. What I checked and the rule applied

I read the Monitor terminal evidence, reconciled the same remote supervisor and copied
the actual run/supervisor roots. All19 present files match their remote hashes; source,
preflight and relevant dependencies match the launch SHA. I read both complete summary
records and all1,983 completed curves, checked their JSONL counterparts, the actual
initial tensors and W1 final tensors, all4,096 available evaluation rows, admissions
and complete process timings. No complete-pair assertion was accepted from a status code.

Applied verbatim from card §4: **“Damaged training, information or primary”** →
**“Report failure/counts and only intact narrower facts; no algorithmic polarity.”**
The absent W100 endpoint and reference make the intended result incomplete. I did not
apply the other eight branches using proxy training curves, an earlier checkpoint,
old reference rows or an assumed zero effect. Evidence-spec §11.8.7 limits the dependent
claim while preserving independently trustworthy facts. No A/B consumption state arises.

## 2. What stopped, and what the evidence cannot locate

The sequence ended exit2 after644s. W1 completed1,000 nonzero updates. W100 returned
TECHNICAL_STOP after983 recorded nonzero blocks, carrying:

```text
TypeError: unsupported operand type(s) for *: 'range_iterator' and 'int'
```

Both actual-node admissions passed; neither the arm nor sequence cap was reached.
The wrapper's stop-on-failure behavior prevented reference execution. W100 has only
initial parameters, its partial summary and completed-block log; no final tensor,
held-out evaluation or paired primary exists.

The caught-exception handler discarded the traceback. The direct evidence therefore
establishes the exception message and missing outputs, not the failing multiplication's
file, line, operands' provenance or root cause. The independent bounded review found
no concrete learner/native defect from these bytes. It confirmed the diagnostic gap
and the possible unrecorded-block boundary without executing a reproduction.
Memory corruption, ctypes lifetime, seed dependence and equivalence to old signal11
remain unsupported explanations. Old quarantines are neither lifted nor retroactively
extended to S21 solely from this failure.

I corrected the diagnostic omission prospectively: `traceback.print_exc()` now writes
the caught stack to the existing stderr. One supplied pure-Python failure verifies
traceback file/function/message and unchanged TECHNICAL_STOP/zero counts. It deliberately
uses the same exception text to test reporting; **it does not reproduce the actual
learner failure**. Sourcece189071a contains only that two-line runtime addition and its
test/record. It cannot recover this lost stack or establish that a future run will finish.

## 3. Preserved observations and inference ceiling

Both produced initial vectors are identical within the pair, finite FP64 with26,161
scalars, and differ from S21 in25,440 components. W1's complete state/readback supports
its narrow measurement: primary U.7056294759→.7016723633, gain+.0039571126, below MEI.05.
Both primary paths have small gains; conditional scenario interval[.0021288,.0057854]
describes those fitted-policy evaluations. All2,048 W1 endpoint recovery scores are40.
Primary Y improves slightly and F decreases; the full eight-cell values remain in E0/data.

W100's recorded training curve contains a substantial late reduction in training U
and increase in training Y. Its final recorded block982 has U.3649349/Y.6265951,
compared with first-block.7085026/.2936442. This keeps the positive training signal
visible, alongside the native completion failure. Training distributions, changing
policies and an unavailable final checkpoint prevent using it as the frozen held-out
contrast or as proof that S21's effect replicated.

The scientific-reading basis is unchanged FOUNDATIONS §6/04_EMPIRICAL at
e51bdf299c5638ab76d7ecd48d27acbcbacdf2f7: actual independent training and the declared
endpoint determine the evidence unit. A partial second fit or more rows from it does
not create a second paired endpoint. `summarize_runs.py` therefore receives one
completed W1 endpoint only, without `--paired`; its output explicitly has n1 and no
paired differences. No n2 W100/W1 mean or confidence interval is computed.

This changes the available evidence, not the accepted mechanism. S21's local native
benefit, reference gap and saturated recovery remain; H_A1 is still unidentified.
Old200-update results stay separate. The whole normalized joint learning law, shared
features, plans, baselines, visitation and partner co-adaptation remain alternative
explanations for S21's benefit. No new causal/novelty/comparator claim warrants a new
literature search merely to classify a caught runtime error.

## 4. Predictions and owner instructions

| Prospective S22 prediction | Intake score |
| --- | --- |
| Delta_U≥.05 | Not scoreable: W100 final primary is absent. |
| W100 G_U≥.05 | Not scoreable: W100 final evaluation is absent. |
| Majority tau40 for each learned arm | W1 component supported2048/2048; the complete prediction is not scoreable without W100. |

An exception is not a refuted algorithmic prediction. Owner prediction: **not taken**;
live-main reviews were[] at terminal intake. Earlier S21 prediction scores remain as
recorded. No new Pro prediction or owner answer is invented. No material critic dissent,
second recast, direction decision or new card arises from the technical classification;
ordinary facts and choices remain here and in the audit ledger.

## 5. Exposure, cost and conformance

Recorded new exposure is126,912 training plus4,096 evaluation episodes: **131,008 episodes,
8,384,512 primitive ticks and1,983 backward calls**, all recorded steps nonzero. Up to
one additional interrupted block—64 episodes/4096 ticks/one backward or step—may be
unrecorded. The count is bounded, not reconstructed from the error message. Twelve
models contain two started fits and ten untrained helpers. No scientific call occurred
during collection, tensor readback or the supplied exception-reporting test.

W1333.18s and W100310.74s sum643.92s; whole sequence644.00s is charged once. Conservative
complete charge **894.00/1500s** includes full100s prelaunch and150s postlaunch support
charges, including failed source packaging, diagnostics/checks and closeout. They are
conservative charges, not precise utilization measurements. The same1000 two-attempt
window now has1891.01s and one complete paired result. Full-history calendar/CPU costs
remain unmeasured. No source/runner/test or per-invocation/complete cap breach occurred.

The required fatal-stack capture existed, but it did not cover this caught exception;
that diagnostic limitation is explicit. The original source correctly retained completed
blocks and stopped the sequence. Missing terminal training/primary facts make the
requested comparison incomplete even though stopping and preservation conformed. Test
success and the prospective traceback patch are engineering facts, not mechanism value.

## 6. Decisions this intake produces

**Object/technical acceptance.** Options: (a) retain the incomplete attempt and accept
only intact W1/completed-block observations; (b) infer a W100 effect from its training
curve or treat failure as negative; (c) discard all observations. Recommend and select(a)
under the exact damaged-primary rule. Owner-delegated decision (unattended, 2026-09-03
instruction): (a). The result is neither a complete paired B nor a direction-level negative.

**Technical repair.** Options: (a) emit ordinary exception traceback on existing stderr;
(b) keep the diagnostic omission; (c) add a framework or unallocated reproduction.
Recommend and select(a), already implemented/tested in ce189071a. Owner-delegated
decision (unattended, 2026-09-03 instruction): (a). This has zero scientific exposure and
does not authorize a learner retry or claim the multiplication defect was repaired.

**Retry and next scientific discriminator.** The frozen allocation explicitly permits
one sequence and no retry/resume/replacement. It is ended. Neither its unused time nor
the logging patch authorizes another run. A and B may be repeated under a separately
selected object allocation; that possibility does not convert this failed attempt into
an accepted retry budget or allow silently resuming unavailable W100 state.

Options for the next object are (a) separately select one traceback-equipped W100
invocation from fresh initialization at the same seed22/1000 endpoint, retaining the
verified W1 control and running its same-seed reference only if W100 completes;
(b) defer this comparison while preserving the narrow result; (c) run an unchanged
blind retry or replace seed22. Recommend(a) over(b), because it can either locate the
failure or finish the still-informative native comparison while reusing an intact control.
Reject(c): no new run has been selected and changing seeds is not a diagnosis.

This is a **recommendation only**, as requested by Root's terminal assignment. Execute
preservation, the small reporting repair and closure of this allocation; do not launch(a).
Owner-delegated decision (unattended, 2026-09-03 instruction): publish recommendation(a),
with zero additional scientific execution. The original DM owns any next explicit card,
budget and decision under standing delegation, independently of sibling directions;
Root receives this exact boundary for acceptance and continuation, not a batch gate.

For that prospective same-law completion, known factors are1 fit×1000×64 training
episodes +2×8×256 endpoint/reference episodes: **68,096 episodes/4,358,144 ticks/1,000
backward calls;6 models,1 fit,5 helpers**. Prior complete same-shape W100355.01s and
reference2.70s give a357.71s planning observation, not a guarantee. It would need its
own declared complete support/600s arm/30s reference limits, new source and exact retained
control bytes. Its two attempts would still represent one seed22 training unit in an
eventual paired comparison; the failed prefix, costs and outcome-informed recovery
selection must stay visible. No direction/Portfolio disposition or Pro Send is selected.

## 7. Preservation, risks and next owner

All raw outputs, including the partial W100 summary/curves/initial tensor, complete W1
initial/final tensors/panels and supervisor bytes remain locally under the named roots.
The source-only stage retains both malformed and corrected bundles. The exact completed
remote cwd, supervisor and stage are the cleanup inventory; source/evidence must be
archived and compared against originals before any removal. The final preservation
receipt will append its digests and direct disk/registry checks here.

Unresolved risks: lost actual exception stack; unlocated cause that may recur; bounded
unknown within-block execution; absent W100 endpoint/reference; historical unknown failed
prefix and unmeasured full-history costs. The prospective traceback fix narrows only the
future diagnostic gap. It supplies no guarantee against a repeat or a broader native defect.

Root owns main integration and acceptance of this return/retention. This original DM
owns any separately selected next object; no extra fit has been accepted. A technical
failure and a pending new allocation change neither lifecycle nor scientific polarity.

## Verified preservation before remote removal

The exact execution checkout (excluding only its Git pointer), supervisor and source-only
stage were archived before removal. Remote `tar -d` comparison against all original
archived members passed; PID3095314 was absent and supervisor state was terminal exit2.
The archive contains **2355 regular members**, **11549691 bytes**, SHA256
`023d847fe1a2665ebf9788b13ead873a6d106ad2b144156860fa4a44eef9a885`. Local transfer hash matches; all19 accepted
output/supervisor members and both original/corrected source bundles match their retained
bytes. `members.json` SHA256 is `02d6c1c5455ec3eba927e9f3b9db90c4a3968fa23aa4e48b7a64d02a7b533ab5`.

Remote archive: `/home/wu/hmasd-recovery/rcle-b03-fresh1000-s22-20260910/remote.tar.gz`.
Local archive: `temp/directions/roster_consistent_latent_exploration/closeout/b03-fresh1000-s22-20260910/remote.tar.gz`.
Recovery ref `refs/recovery/rcle-b03-fresh1000-s22-20260910` preserves source9a11fb084.
Preservation/transfer5.393398699990939s and member verification0.43075230000249576s count
inside the same150s postlaunch support charge. No scientific evidence was discarded,
no new learner invoked, and historical/native-cache/shared-authoring paths are outside
the cleanup inventory. Final removal facts will be appended after result publication.

## Final scoped closeout

After publication `b70520eba7edff0a9900f0c6f97ce227f4a4fd9d`, the exact completed remote
execution checkout was unregistered and removed; the matching supervisor and source-only
stage were removed after the verified archive/source-ref preservation above. Removal
returned0 in0.3662557000061497s. All three paths are absent on disk, PID3095314 is absent,
and a direct exact-line check of `git worktree list --porcelain` confirms the execution
checkout is absent from the registry (additional0.42907800000102725s). The archive digest
and source recovery ref still match. `closeout/b03-fresh1000-s22-20260910/removal.json`
and `REPORT.md` retain the exact inventory/results.

Local raw W1/partial W100 evidence, the verified local and remote archives, historical
evidence, native cache and shared authoring checkout remain. All closeout work is inside
the conservative894.00s complete charge. This terminal assignment is complete; Root
integrates/accepts the return. The next scientific object remains an explicit separate
DM selection under standing authority; no scientific retry or replacement was launched.
