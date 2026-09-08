# FRRIE A04 scientific intake — 2026-09-07

**Valid A/RECON: `A04_T0_PATH_COMPLETED`.** The single alternative-stack setup/T0 chain
completed six phases / 384 tape constructions in 16 s, with retained same-update A03 digests.
This is one input-path completion, with no learner or native-return observation. The A04 DM
prediction was correct. The old corruption cause, full learner-stack behavior and R09 release
remain unresolved. The next source/runtime decision below is prepared only.

Assignment: **P13-FRRIE-A04-INTAKE-01**, [P13 handoff](../../portfolio/handoffs/2026-09-07-p13-runtime-restore-and-next-questions.md)
at main `088e5d989`. No experiment, installation, probe, tape regeneration, source edit,
R09 authorization or causal diagnosis was performed in this intake.

## 1. What was checked and the rule applied

Read the [A04 card §§1–4](FRRIE_R09_A04_ALTERNATIVE_STACK_SCIENCE_CARD_20260907.md),
[preparation intake §§3–5](FRRIE_R09_A04_PREPARATION_INTAKE_20260907.md),
[result evidence / CM technical acceptance](FRRIE_R09_A04_RESULT_EVIDENCE_20260907.md) at
`b2a71951858be31a16d36aa72a3e3e8f6178c954`, its main integration
`b024bca3df46082e51f72904ad60b7d2b0bd150c`, and the
[P12 execution record](FRRIE_R09_A04_P12_EXECUTION_RECORD_20260907.md). The latter supplies
P12's sole complete-chain allocation; the earlier preparation-only header retained on main
is not a second or current allocation. The card's §3 reading rule is unchanged between the
technical-acceptance branch and current main. No newer scientific A04 intake was found.

Applied evidence spec §§3–4, 5.1, 6.1 and 11.4, 11.7–11.9, especially §11.8.7's dependency
boundary. Checked the current Portfolio row and P13 instructions, DIRECTION's R06–R08 and
A03 conclusions, and only the frozen R09 card/source sections needed for the next decision.
DIRECTION's historical waiting language does not override P12/P13; its mechanism results
are unchanged. No new mechanism or comparator is selected, so existing card grounding is
reused; no new literature search or causal attribution is needed.

Card §3, first matching branch, **verbatim**:

> `A04_T0_PATH_COMPLETED` — Exit 0, all six 64-tape phases completed, no exception, no torch/tracer, and retained same-update digests agree within this run and with the available A03 phases. This one alternative-stack T0 path completed; recommend an explicitly scoped next path decision. No automatic full R09 attempt.

The preceding ordered branches do not match: source/host/interpreter/admission and the sole
T0 allocation were met; setup reached tape work; there is no recorded original exception or
fatal signal; three repetitions finished before the cap; all six phase digests match their
same-update A03 references. Missing whole-chain resource telemetry does not overturn this
non-resource observation. This intake accepts the scientific reading independently of CM's
technical acceptance; successful execution is not mechanism value.

## 2. Direct observation, counts and receipts

Sole accepted handle: `frrie-a04-system312-p11-d6844bb25f6f`, on `wsl_4070` /
`LAPTOP-U9TDKC8A`; exact source `d6844bb25f6f1030aa7123467935861dcc719450`, detached cwd
`/home/wu/hmasd-worktrees/frrie-a04-d6844bb25f6f`. The retained
[launch receipt](a04_system312_20260907/launch_receipt.txt),
[supervisor runner](a04_system312_20260907/runner.sh) and
[task log](a04_system312_20260907/task.log) bind the complete chain. Start/exit are
2026-09-07 21:38:13Z / 21:38:29Z, exit 0. The status-query elapsed time is not runtime.

The log records one dedicated system CPython 3.12.3 venv and one NumPy 1.26.3 installation.
[Summary](a04_system312_20260907/summary.json) reports CPython 3.12.3 / GCC 13.3.0,
`/home/wu/.venvs/hmasd-frrie-system312-a04-20260907/bin/python`, and imported NumPy 1.26.3.
[WHEEL metadata](a04_system312_20260907/numpy_WHEEL.txt) identifies the cp312 manylinux
x86_64 binary. The configured node and prior inventory supply the WSL2/Ubuntu host facts.
The command preserved root ending 0003, label `FRRIE-B09-CONTACT-BLOCK-003`, T0, repeat 3,
update labels 1 and 2, roster order `(9,15)*32`, horizon 12, addressed RNG and FP32/int64.
The four compute-thread environment variables are 1; `-X faulthandler` is retained.

| Quantity read by this question | Observed value |
| --- | --- |
| Completed repetitions / phases | 3 / 6; each phase has 64 tapes |
| Update-1 constructions | 192; digest `0f0fb392c59dcfdbaa475ae8becca03323751d0a849ee6f39c9a8c9d68057b5f` |
| Update-2 constructions | 192; digest `7e155dc5452d9303688d0a807b190ab0050db723078a7f890e1ee6b5f71a4f16` |
| Content comparison | Each digest agrees in all three repetitions and with the available retained A03 phase |
| Exception / torch-at-start / torch-in-modules / tracer | null / false / false / false |
| Complete setup-to-publication wall | 16 s, supervisor one-second resolution; cap 300 s plus at most 5 s kill grace |
| Summed phase wall | 10.297323798 s; excludes digest work and is not whole-chain wall |
| T0 peak RSS | 46,542,848 bytes (44.3867 MiB) |

For the primary measurement I read the raw phase/flag fields and the retained
[A03 T0 summary](a03_tape_isolation_20260906/t0/summary.json), then used local stdlib Python
to sum phase counts/times and compare same-update digests. This corroborates the relevant
[CM collection checks](a04_system312_20260907/collection_checks.json); no workload or
collection command was rerun. The existing command identity check is reused, not rebuilt.

The [fresh admission](a04_system312_20260907/a04_system312_admission.json) at
21:38:19.414305Z passed with physical/effective available memory both 15,664,181,248 bytes
(14.5884 GiB), above 4 GiB. It is retained in the log and summary. The recorded command puts
that admission immediately before T0. Publication is directly evidenced by the successfully
written/parsed summary and its six nested phases; separate tape files were not required.

Computed work: `1 arm × 3 repetitions × 2 update labels × 2 rosters × 32 episodes = 384`
constructions, covering **128 distinct addressed inputs repeated three times**. The selected
unit is the **single accepted invocation**, not 384 independent samples or three training
seeds. Dominant uplink-array work is `3×2×32×12×(9²+15²) = 705024` addressed entries, plus
other fields and origin schedules. No statistical interval over these repetitions is justified.

**Exposure: 0 learner updates; 0 optimizer steps; 0 native transitions; 0 native evaluations;
0 model initializations.** `training_update` names input labels only; `--eval-episodes 256`
created no evaluation tapes in T0. This P13 intake adds zero result-bearing exposure.

Setup-process peak RSS, scratch use and aggregate CPU seconds were not measured. Those
quantities are `resources_unmeasured`; T0 RSS is measured. Single-chain critical path and summed
invocation wall are both 16 s. No whole-stack resource-health or speedup claim follows.
Engineering-scope §4: none needed or added; zero code changes and no observed §5 budget breach.

## 3. Bounded scientific reading and prediction check

The card's categorical MEI—six completed phases with preserved content—was reached. A04
therefore changes the preparation intake's unknown NumPy acquisition/import and T0 completion
facts to observed success on this exact alternative stack. It does not measure return-scale
headroom; a tuned same-information host baseline/upper-reference pair remains absent.

Strongest support is direct completed input work beyond A03 T0's two retained phases, with
matching content. Strongest contrary evidence is the retained A03 T0 failure without torch
or tracing on the same physical host. A04 changes both Python version/build and NumPy binary
ABI, lacks a concurrent old-stack control, and observes only two update-address sets. It
neither identifies the old causal agent nor excludes a source defect, intermittent failure
or failure elsewhere in this or the original stack. Historical quarantine and the A03
`A03_CORRUPTION_WITHOUT_TORCH` reading are not rewritten.

The original scientific path remains distinct: fixed-role partial observations → beta-weighted
partner aggregation → native scan/uplink/radio actions → delivery/balance/waste reward →
RSCF/Adam learning under the two projection boxes. A04 stops at exogenous-input construction
and never traverses those action, credit or learning links. It supplies no new evidence about
that mechanism, agent-count transfer, churn, safety or UAV validation.

The strongest existing learning support remains R06 root-1 N15 tight-minus-wide
`+0.005548293532`; the contradiction to assuming recurrence is R07 root-2 N15
`-0.001948094523`, within the ±0.005 MEI. R08's same-root chart-cut attenuation
`+0.000010174094` does not remove the root-1 gap and is not another independent path.
Generic projection/optimizer geometry and path-specific co-adaptation remain live alternatives.
None of these historical results is pooled with A04 or reclassified.

Prediction: A04's recorded low-confidence `A04_T0_PATH_COMPLETED` prediction is **correct**
for this one invocation; the competing tape-failure outcome did not occur. No reliability
probability was predicted or learned. The older A03 DM prediction remains wrong; R09's native-
return prediction remains unscored. Owner prediction: **not taken (unattended)**.

At this clean boundary `item.py reviews --json` on current main returned `[]`; the relevant
FRRIE audit owner cells are empty. No owner instruction or prediction reply was available to
apply/score/mark answered. Open historical owner items are not owner replies. No new P1/P2
item is warranted: this is ordinary result intake and preparation, without a new card,
direction decision, material dissent, close call, second recast or Portfolio disposition.

## 4. Decisions this intake produces

1. **Object-tier technical intake.** Options: (a) accept the single T0 completion at A/RECON;
   (b) withhold that observation pending evidence from the full learner stack. Recommend/select
   (a): the retained inputs and primary measurement satisfy the actual ordered rule; (b) would
   impose a different claim's burden. **Owner-delegated decision (unattended, 2026-09-03
   instruction): (a).** This adds no R09 permission or A/B consumption state.
2. **Object-tier next-path preparation only.** Options: (a) prepare an explicit alternative-stack
   decision for the existing third-root real-learning comparison, using the originally accepted
   R09 source and preserving its work/meaning; (b) prepare another T0/T1 or multi-arm causal
   isolation panel; (c) yield with no concrete next learning-path choice. Recommend/select
   preparation of (a). It targets the unresolved native-return question and names the threatened
   dependencies below. Another unchanged T0 gives no learner observation, and a causal panel is
   unnecessary for a bounded B claim. **Owner-delegated decision (unattended, 2026-09-03
   instruction): (a), preparation only.** No substrate amendment, execution or new family is
   selected by this record. Portfolio receives a prospective option, not an automatic launch.

Owner flags: none; no close call, critic dissent, recast, lifecycle/priority change or UAV entry.
P13 is existing-result intake and preparation, excluded once from the temporary CM comparison:
no new coding assignment or historical-task replay is commissioned. A later necessary source
change must reach Root as one complete common spec before any five-arm/solo CM implementation.

## 5. Smallest next source/runtime decision, missing input and prospective return

**Prepared question:** should the existing third-root B be explicitly assigned one alternative-
stack setup-through-learning chain, using original source
`43eec21e9584c83e5e8d940402d7e4570b454e59`, instead of further input-only attribution work?
The recommended future option is that unchanged scientific comparison, conditional on an
explicit source/runtime amendment and its actual later allocation. The original A03-substrate
R09 stop remains in force; A04 supplies no answer to the old host/interpreter causal question.

The source binding matters. Read-only Git comparison from original R09 `43eec21e` to A04
`d6844bb2` shows **246 added lines in imported `b01/trainer.py`**. The R09 wrapper,
`b01_contact_r02` path, policy, training and native-adapter files checked in that same focused
diff are unchanged. This is a source-surface discrepancy, not an observed defect or an
explanation of any failure. T0 does not exercise the changed trainer. Do not silently launch
current HEAD as the original accepted R09 learner. Preferred prospective binding is the whole
original accepted commit; selecting the later trainer would require its own explicit acceptance.
No source was changed or reverted here.

The missing execution input is a **concrete CPython-3.12 learner dependency/setup route** for
that bound source. A04 acquired only NumPy and excluded torch. The retained project metadata
identifies torch 2.7.0+cu118 for cp310; it does not establish a cp312 artifact or importability.
The existing R09 entry calls evaluation-tape generation, native build/load, uniform evaluation,
paired model/optimizer creation, collection, updates and final publication. Its native path
uses the package's existing C++17 build and ctypes adapter. None of these learner/native stages
ran in A04. Their compatibility and complete-chain cost under the proposed stack are unmeasured.
No package version/variant, backend or altered dtype is silently substituted to fill the gap.

Implementation-relevant pointers, read-only at the bound R09 commit:
`scripts/run_frrie_b01_contact_r09.py`; `b01_contact_r02/experiment.py::execute`;
`b01/r128_smoke.py::_build_adapter`; `b01/trainer.py::PairedB01Trainer`;
`native_adapter.py::build_package_native_artifact` and `load_package_native_adapter`, all
under the FRRIE candidate directory except the script. Existing source already expresses the
third-root comparison; **no new code spec is needed or defensibly frozen from A04 alone**.
If a concrete compatibility defect later requires implementation, return that exact gap and
its bounded spec to Root first, not a generic stack-repair assignment.

The prospective command requested through Root is for Portfolio to allocate the next bounded
**source/runtime decision and necessary learner setup**, with the above original source,
system CPython 3.12.3 / NumPy 1.26.3 as the candidate stack, and an explicit compatible torch
artifact/version and native-build route to be named. The DM must record the runtime amendment
before any affected execution; a separate learner venv must not mutate the retained A04 or
shared project environments. If existing artifacts cannot supply a needed fact, return the
exact missing dependency; do not manufacture a probe or a causal prerequisite. Necessary
installation/import/build may be part of a later explicitly allocated complete learner chain,
not an added mandatory preliminary experiment. This paragraph allocates none of that work.

For that candidate, preserve the [R09 card](FRRIE_R09_THIRD_ROOT_SCIENCE_CARD_20260905.md)
sections “Third root fixed before any output”, “Treatment, comparator, activation and native
trace”, “Work, observable, effect margin and rule”, and “Predictions, exposure, cost, cap and
portability”: root/label 3, tight ±0.04 versus containing wide ±1.50, shared LR0.003,
CPU FP32/Torch1/native32, 128 paired updates, N15 primary/N9 fully reported, all four checkpoints,
uniform competence reference, original six-branch rule and MEI0.005. No seed screening,
checkpoint choice, smaller-work relabeling as R09, or cross-stack output-equality prerequisite.
A fresh alternative-stack invocation would be a new launch, not an exact retry of the old attempt.

Computed prospective work, **zero allocated/actual here**: two arms × one fixed root × 128
updates × 64 factual episodes, or 16,384 factual episodes / 196,608 factual transitions and
256 Adam steps. Counterfactual/suffix work is included in `2×128×4928 = 1,261,568` training
native slots. Evaluation is `2 arms×4 checkpoints×2 rosters×256 + 2×256 uniform = 4608`
episodes in 18 cells / 55,296 native slots; total native work is 1,316,864 slots. Input
construction is 8,192 training plus 512 evaluation tapes. Exposure arithmetic remains
`128×0.003/0.05 = 7.68` nominal LR exposure relative to initialization half-range, not a
parameter-motion bound. These are algorithm and required measurement work, with **zero
extra diagnostic/check runs** proposed. No policy/trajectory search is added.

For decision comparison, another unchanged A04 repeats 384 constructions for zero learning;
the existing T1 with the same repeat/update/evaluation arguments would construct
`3×(2×64+2×256)=1920` tapes, also with zero learning. Neither answers the third-root native-
return question. The original R09 card's R07 anchors are about 150.08/149.91 attributed seconds
per learned arm and 903 s supervisor wall; they are historical planning inputs, not system312
measurements. Original four-attributed-hour per-arm/eight-hour complete bounds are not extended;
any future setup, import, native build, learning, evaluation and publication belong to one
complete allocation. A04's 16 s cannot price that chain; new-stack time remains unknown.

Next scientific discriminator, if explicitly commissioned: final N15 tight-minus-wide native
return against the competent containing comparator after the complete real learner chain,
with all N9 and adverse results retained. A material positive, within-MEI or material adverse
result would respectively add a bounded third-path occurrence, leave recurrence unsupported
on that path, or show an opposite tradeoff under the existing rule. No mandatory all-positive
seed requirement or unique old-cause explanation is added.

## 6. Return, owner brief and audit handoff

Authoring checkout: `C:/Projects/HMASD-worktrees/dm-frrie-a01-resume-20260905`, `codex/frrie`,
starting clean at `b2a71951858be31a16d36aa72a3e3e8f6178c954`. All required accepted evidence
is present; current P13/owner instructions were read from committed main. Unrelated source
and other work were preserved. Only this intake and the
[Chinese brief](../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-07_A04-result.md)
are owned for edit/commit/push. No DIRECTION edit is needed because no mechanism-level science
changed. No live run, pending Pro Send or CM code dispatch is created by this return.

Root integrates those paths and returns the precise dependency/allocation request to Portfolio;
DM retains the explicit object-tier source/runtime decision and later scientific intake.
Root instructed this task to leave the shared audit file untouched and will append the following
exact rows at integration. The rows are supplied here, **not claimed already appended**:

```text
| 2026-09-07T15:05:51-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) accept A04 single T0 completion; (b) withhold pending full learner evidence | (a): A04_T0_PATH_COMPLETED,384 constructions/128 distinct inputs,16s,zero learner/native; no R09 release | yes | OWNER_DELEGATED (unattended, 2026-09-03 instruction); P13-FRRIE-A04-INTAKE-01 | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_A04_SCIENTIFIC_INTAKE_20260907.md | none | |
| 2026-09-07T15:05:51-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) prepare original-source alternative-stack third-root learning decision; (b) further tape/causal panel; (c) yield without concrete choice | (a) prepared only; original43eec21e source versus later trainer+246 lines; cp312 torch/native setup unverified; no amendment/code/setup/probe/learner allocated | yes | OWNER_DELEGATED (unattended, 2026-09-03 instruction); P13 preparation | docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R09_A04_SCIENTIFIC_INTAKE_20260907.md | none | |
```

scope: none
