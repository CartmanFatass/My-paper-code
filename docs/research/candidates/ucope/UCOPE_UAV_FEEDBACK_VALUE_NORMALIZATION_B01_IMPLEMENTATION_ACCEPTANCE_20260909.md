# Feedback value normalization B01 implementation acceptance

**Delivered: technically accepted implementation, zero scientific invocations.**
Source **7c88fb8405c75339e9634b78f1ef6de770f24e31** is committed and pushed on
`codex/ucope` in `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`,
starting clean at `658c02ce5b7acd2062ab89708917ffb1ba35b356`.
Root's later concrete implementation assignment superseded only the preparation
code restriction; it allocated no result-bearing execution. The frozen
[card sections2–7](UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_SCIENCE_CARD_20260909.md)
and [preparation intake section4](UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_PREPARATION_INTAKE_20260909.md)
remain unchanged, as do item013 and governance.

## Delivered source and protected boundary

The new `experiments/candidates/ucope/uav_feedback_value_normalization_b01/`
contains the 203-line study, 44-line moments helper and one-line package file.
The thin runner `scripts/run_ucope_uav_feedback_value_normalization_b01.py` is
33 lines; mapped tests add169 lines. Total new non-test source281 lines,
450 total additions, zero deletions. Engineering scope section4 additions:
**none**, per card section7. CM inspected the complete diff.

Both no-head copies are made from the common initialization before training.
The driver explicitly selects agent_compound/entropy0 and sampled execution;
G_raw passes `value_moments=None` to the existing collector and learner.
G_normalized uses the local frozen-reference cumulative FP32 arithmetic, with
one merge before four fixed-target epochs. Checkpoints serialize n/updates and
cloned FP32 mean/M2; summary reports derived scale and raw/normalized units.
Evaluation records unchanged parameter exposure and moments. Current shared
Linear/Tanh/GRU networks have no running-stat buffers; evaluation accesses no
optimizer or moments update. All three paired outputs retain episode IDs,
conditional SE and signs, explicit normalized-minus-raw primary, MEI boundary
reading and honest missing-outcome completeness. Partial native-call counts
would remain visible after an exception.

[Protected source identity](../../../../temp/directions/ucope/analysis/feedback-value-normalization-implementation-20260909/source-identity.json)
records all four shared study/learner/policy/environment blobs matching
`52bf50a089d3389d9fada0b531e4f4e56e83f9b8`. No shared runtime, other selector,
adapter/core or VSPC1 file changed. The helper copies the arithmetic from
`7c80750ea7493af2d70d28fe2072e517b6f45e97` without a cross-direction import.
Comparator identity here is a checked source fact, not a new runtime guard.

## Focused acceptance and independent review

One affected synthetic suite was run locally with the scientific interpreter:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/ucope/test/feedback-value-normalization-implementation-20260909 tests/experiments/candidates/ucope/uav_feedback_value_normalization_b01
```

[Initial raw receipt](../../../../temp/directions/ucope/analysis/feedback-value-normalization-implementation-20260909/focused.log):
12 passed, one test expectation failed, pytest3.47s/outer4.76s. The sole failure
compared the prescribed `sqrt(FP32(1e-8))` against literal `FP32(1e-4)`, which
round differently. Corrected only that expectation to the frozen arithmetic;
runtime source was unchanged. The same test was rerun with the distinct
`feedback-value-normalization-floor-correction-20260909` basetemp and its exact
node `test_normalization.py::test_population_moments_reference_order_floor_and_detachment`:
[correction receipt](../../../../temp/directions/ucope/analysis/feedback-value-normalization-implementation-20260909/floor-correction.log),
one passed, pytest1.64s/outer2.56s. All13 current cases thus have passing
evidence; cumulative pytest5.11s/outer7.32s, below300s. The existing disabled
cache provider's `cache_dir` warning is unrelated. No repeated full suite.

Checks exercise detached population moments/merge order/floor/checkpoint copy;
the actual shared collector's decoded raw baseline; raw stored advantages
before the once-per-rollout merge; fixed targets and value loss through four
actual synthetic epochs; no-head/private-stream/reset wiring; synthetic
learning/checkpoint/evaluation nonmutation/publication; native-unit reward_sum
division; three signed contrasts, MEI boundaries and missing-output dependency;
and a partial collection exception. CLI8501 was a stub with no workload or
8501 RNG creation; actual synthetic fixtures use9001. No native smoke, real
training/evaluation, scientific diagnostic/profiling or scientific root exists.

Independent reviewer **rv_ah_ucope_b02_credit** inspected exact source7c88fb840,
the shared hooks, tests and both raw receipts: **no material finding**. Review
confirmed units/detachment/order, fixed epochs, reference arithmetic, private
pairing, raw comparator, frozen evaluation, checkpoint outputs and partial
primary behavior. It performed no duplicate suite or scientific invocation.
CM dispositions: accept the implementation; no remaining semantic correction.

The relevant baseline/critic passage in the RL topic note and evidence
section11.10 at `d89be7656d367ca10f75ca1185797081b5d722fa` inform the acceptance:
detachment excludes an extra critic-loss derivative through the current actor
surrogate, while joint clipping and future baselines remain possible effects.
Normalization is neither output-preserving PopArt nor proof of native benefit.
The synthetic result establishes execution semantics, not scientific truth.

## Cost, publication coverage and remaining ownership

**Per-arm cost projection:** prospective normalized work remains131072 training
steps/1024Adam/8192 final steps/256 scalar merges plus normalization/decoding;
raw has the same training/final policy work plus8192 H steps and publication.
Card section5's1800s complete-arm/3600s whole limits remain. Native walls and
scalar overhead are unmeasured; P85's331.58s is a different-work reference.
No performance probe or launch occurred. Future serial critical path and summed
invocation wall coincide; aggregate CPU is unmeasured.

**Post-learner path coverage:** the actual synthetic driver exercised both fits,
final checkpoints, frozen moments evaluation and the complete three-outcome
publication, plus partial-result dependency. Native reward/observation and
shared PPO coverage are reused. Actual8501 output and native affordability
remain unmeasured; Root alone allocates any later execution.

**Cleanup limitation:** after resolving the exact completed invocation directory,
automatic approval review rejected this command before execution as
**blocked by policy**:

```powershell
Remove-Item -LiteralPath 'C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/test/feedback-value-normalization-implementation-20260909' -Recurse -Force
```

[Blocker record](../../../../temp/directions/ucope/analysis/feedback-value-normalization-implementation-20260909/cleanup-blocker.txt).
That scratch remains **CM-owned**; no retry or alternate bypass followed.
The correction test created no scratch directory, and absence was checked.
Prior P85 rejected scratch remains untouched. This is an engineering cleanup
limitation without scientific polarity. DM retains acceptance; Root owns
integration and any later allocation. Shared authoring checkout remains in use.
