# FSD B03 implementation technical acceptance — 2026-09-08

P47 implementation-only work in `C:/Projects/HMASD-worktrees/codex-fsd`,
`codex/fsd`, started clean at `a4f01bdd36f53ae5c80b3d20d2cc69850376fd14`.
Its declared source matches the specification's `a74ed196f8c7b7dbabd1492d5aa077366be65f40`.
The DM's concurrent card authority edit is outside this source commit.
Contract: [CM spec §§2–5](FSD_NATIVE_RENEWAL_LEARNING_B03_CM_SPEC_20260908.md),
[card §§2–7](FSD_NATIVE_RENEWAL_LEARNING_B03_SCIENCE_CARD_20260908.md).

## Delivered source

- Shared B01 runner: explicit default-C selector threaded only into summary,
  construction, pair assembly and CLI. B03 selects authentic E3 D0 k5/caps5;
  returned numeric +inf overrides reach the unchanged independent E2 evaluator.
  Only the two positive-infinity cost snapshot values use E0's JSON helper.
- Thin B03 entry fixes 770403/770404, B03 object/card and D0 comparator. B01/B02
  keep C/H/G, their masters and companion option. Invalid CLI inputs fail before
  output/model creation. No module globals are mutated by the wrapper.
- Pair assembly checks exact expected H/D0 clock/cost/derived buffer differences
  and equality of every remaining stored config field; legacy config equality
  remains exact. B03 reports H−D0, G−H and G−D0 full/post, primary sample SD and
  unchanged conditional SE/MEI arithmetic. G−H accounting residual is retained.
  Pair `status` concerns H/D0; B03 `card_status` also requires the G reference.
  Missing G returns incomplete card/exit1 while preserving the primary; missing
  D0 prevents pair polarity while preserving the completed H endpoint.
- D0 deadline/cap1200, H900 and G60 give panel2160; old objects retain1860.
  No collector, mask, finite check, evaluator, update or publication algorithm
  was changed. No engineering-scope §4 machinery was added (card §7: none).

## Focused acceptance evidence

Exact command, cwd as above:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/flexible_skill_duration/test/b03_p47_20260908 tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py
```

Result: **40 passed**, pytest98.96s, measured complete process119.5993081s,
within the300s directory budget. Warnings: existing disabled cacheprovider config
and matplotlib/pyparsing deprecations. No dependency installation or interpreter
change. Autouse forbidden constructors prevent real HMASDAgent/RelayCorridorHost
construction. The suite's first24 cases/assertions remain the exact original
file prefix;16 added cases cover the changed boundaries.

Real E3 selection and corridor config builder are exercised with fake models and
adapters. Production16/32-lane,H400 configs establish H buffers160/320 and D0
1280/2560, batches128, numeric infinite learner/evaluator costs, seed consumers,
four threads, own weights/normalizers/optimizers and preserved Python/NumPy/Torch
RNG. Evaluation scoring for this config check uses a ten-step fake host only.
Separate ten-step fake B03 main G/D0/H checks exercise native sampled masks
(distinct from public/periodic masks), current actions, original step_data,
native FP64 rewards, terminal storage/reset, full endpoint publication and pair
assembly. Config-drift/old-identity rejection, inclusive MEI branches, direct
reference arithmetic, readable nonfinite failures, companion dependencies and
fake-clock final publication boundaries are covered. Old three-step cases remain.

A source AST comparison against the starting commit confirms these ten functions
are unchanged: applied_mask, collect_training, evaluate, final_evaluation,
paired_statistics, completed_arm, require_finite, check_deadline, write_summary,
publish. `git diff --check` passes. Shared runner479 lines; wrapper16 lines;
source diff49 additions/21 deletions plus16-line wrapper, test272 additions/zero
deletions, below600-runner/2000-new-non-test-line limits.

## Independent review

Fresh configured `hmasd-reviewer`:
`/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47/rv_ah_fsd_b03_p47`.
Review completed independently over the actual source diff and focused coverage:
**no material finding; no repair requested**. It confirmed numeric D0 construction
through the evaluator, preserved action/storage/RNG behavior, seven permitted
configuration differences with all other fields compared, primary/reference
arithmetic and complete cap mapping. Reviewer independently verified the original
test prefix and used the reported40-case evidence without a redundant rerun.
No prohibited scope machinery or budget breach was found. CM accepts this
technical implementation; no empirical or scientific-readiness conclusion follows.

## Future invocation and remaining boundary

No empirical launch, model, host, production root, resource receipt, detached cwd,
launch script or handle was created. Fake tests establish wiring/conformance,
not learning performance, real D0 finite runtime behavior or completion in cap.

Per-arm cost projection: reuse the card §6 and existing
[FSD B03 exposure/cost record](FSD_NATIVE_RENEWAL_LEARNING_B03_EXPOSURE_AND_COST_20260908.json).
The historical D0 scale1051.6405s is a projection, not this implementation's
measurement. Future G60/D01200/H900 caps sum2160s; no new profiling/pilot or cap
change. Post-learner path coverage: fake main publication/readback and companion
assembly exercise this changed path, including missing-reference/primary branches.

Future logical argv (source acceptance only; DM/Root binds the actual SHA/root):

```text
python scripts/run_fsd_native_renewal_learning_b03.py --policy G --seed 770403 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/G
python scripts/run_fsd_native_renewal_learning_b03.py --policy D0 --seed 770403 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/D0
python scripts/run_fsd_native_renewal_learning_b03.py --policy H --seed 770403 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/H --d0-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/D0/summary.json --g-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/G/summary.json
```

Root integrates the accepted commit; DM owns binding/readiness and the P47
selected panel route. The later runtime command retains remote-first placement,
adjacent admission and complete outer command timeouts60/1200/900, including
admission/import/construction/learning/evaluation/pair/publication. Cooperative
clocks do not interrupt a single update. No automatic successor is authorized.
