# FSD B02 P42 technical acceptance

Delivered the fixed B02 training770303/evaluation770304 entry point by explicit
inputs to the reviewed B01 implementation. B01 callable/CLI defaults remain
770203/770204 with their original object/card. No production model, host, learner,
scientific output root, admission, launch binding, probe or execution occurred.

Contract: [P42](../../portfolio/handoffs/2026-09-08-p42-fsd-b02-seed-implementation.md),
[B02 CM spec §§2–5](FSD_NATIVE_RENEWAL_LEARNING_B02_CM_SPEC_20260908.md),
[card §§3–5](FSD_NATIVE_RENEWAL_LEARNING_B02_SCIENCE_CARD_20260908.md).
DM reconciled inputs and released the existing `codex/fsd` checkout at clean,
pushed `d78ce48af84d24ba74c1245572c7bec62abf4254`. Complete starting code remains
`ab6426ef6ca0267d7b5ca7c833401d6348ab07fb`; affected B01 source/test bytes at entry
match reviewed `b3f86bb28879db239b07291c39d93a1c494abe50`. No fourth comparison
is enrolled; P42 records enrollment exhausted. No other writer's work changed.

## Source and preserved behavior

- [B01 shared runner](../../../../scripts/run_fsd_native_renewal_learning_b01.py):
  only `base_summary`, `build_learner`, `final_evaluation`, `main` changed.
  Keyword defaults retain B01. Main threads the accepted CLI training seed into
  metadata, Python/NumPy/Torch seeds, training-adapter master and learner-config
  seed. The supplied evaluation master reaches G and the independent evaluator;
  the evaluator also receives the training seed for its config, inside the
  unchanged RNG-preservation context.
- [B02 wrapper](../../../../scripts/run_fsd_native_renewal_learning_b02.py):
  16 lines, one shared-main delegation with fixed770303/770304/B02 object/card,
  and the ordinary exit-code guard. No global rebinding, new CLI flags or copied
  runner body. Wrong fixed CLI seed fails before output/model construction.
- Existing pair identity checks retain their dependency behavior: an old B01 C
  cannot supply B02's pair; an old or mismatched-master G leaves a valid fresh
  pair's reference incomplete. No cross-pair estimator or B01 result rewriting.

An AST comparison against the starting source confirmed every top-level element
outside the four owned functions unchanged. Collector/storage/native reward,
mask/credit/reset, evaluator internals, optimizer exposure, pairing arithmetic,
finite/deadline and durable publication functions are preserved. Shared runner
is451 lines; wrapper16; each is below600. No scope§4 machinery is added and new
non-test source is below2000 lines. Source diff whitespace checks passed.

## Focused acceptance evidence

The [existing synthetic suite](../../../../tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py)
retains all18 accepted cases and assertions. AST comparison confirmed every
original test function and assertion remains. Six additional parameterized cases
cover the new actual seed consumers, evaluator config/master with RNG/module/
ValueNorm isolation, complete fake B02 entry-point panel, subsequent B01 defaults,
unsupported CLI seeds before output creation, and cross-pair identity failures.
The existing fake Agent/Adapter are reused; real model/host construction remains
forbidden. The actual E2 constructor/sync path runs only through patched fakes.

From `C:/Projects/HMASD-worktrees/codex-fsd`:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/b02-seed-threading tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py
```

**24 passed**, pytest3.58s; complete test-process wall **4.6721191s**, measured
around the process, below300s. This was the single suite invocation for P42.
Raw output: `temp/directions/flexible_skill_duration/test/b02-seed-threading-check.txt`.
Warnings are the existing disabled-cache configuration and Pyparsing deprecations.

The reused independent `fsd_integration_review` examined the changed source,
consumer map and focused assertions without execution: **no material findings**.
It confirmed both new keys reach their actual consumers, no residual global
binding, intact B01 defaults and unchanged protected semantics; no scope/budget
breach. These facts establish engineering conformance, not a B02 learning result
or real runtime feasibility. No scientific exposure or extra production check
is inferred from the fake suite.

## Future CLI and remaining owner

The next separately allocated panel must bind an accepted implementation SHA
containing this change. These are syntax only; the prospective root does not
exist and no commands/scripts/admission/handles were prepared for execution:

```text
python scripts/run_fsd_native_renewal_learning_b02.py --policy G --seed 770303 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/G
python scripts/run_fsd_native_renewal_learning_b02.py --policy C --seed 770303 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/C
python scripts/run_fsd_native_renewal_learning_b02.py --policy H --seed 770303 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/H --c-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/C/summary.json --g-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b02_770303/G/summary.json
```

No implementation issue remains. Root integrates accepted code and returns to
the same DM for readiness and a separately issued runtime allocation. Prospective
G60/C900/H900s admission-inclusive caps and all original counts/stop rules remain
unallocated by coding acceptance. The existing B01 measured costs and publication
coverage are reused; no new projection calibration or scientific follow-up was
selected here. B01/B02 scientific reporting remains separate per-training-pair
rows under the card, with no pooled estimator.
