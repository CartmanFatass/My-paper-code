# EOCIV-B1 real valve-learning code/science index

This package is the candidate-local B-level exploratory treatment
`EOCIV-B1-REAL-VALVE-LEARNING-SIGNAL`. It is a real environment algorithm
path: a recurrent stochastic actor/critic is trained on ordinary external team
reward, a detached ridge-logistic valve is fit from paired real/native-neutral
receipts, and four paired arms are evaluated through the existing sibling
environment and actuation runner.

It does **not** license or execute the registered C-level outcome experiment.
`capability_gate.REGISTERED_OUTCOME_EXPERIMENT["licensed"]` remains `False`.
Mechanical zero/negative signal, actor insensitivity, one-sided valve support,
training instability, or learned/control equivalence are B-level diagnostics;
they are not promotion, retirement, deployment, or whole-direction pause
decisions.

## Stable entry points

- Algorithm/trainer/evaluator:
  `experiments/candidates/eociv_lite/real_valve_learning.py`
- Existing runner with optional same-surface policy and control-decision seams;
  both retain the Stage-0 defaults when unused:
  `experiments/candidates/eociv_lite/actuation_runtime.py`
- CLI: `scripts/run_eociv_b1_real_valve_learning.py --mode smoke|full`
- Focused tests:
  `tests/experiments/candidates/eociv_lite/test_real_valve_learning.py`
- Parent-run result (created only after the registered full run):
  `docs/research/candidates/eociv_lite/REAL_VALVE_LEARNING_RESULT.json`

## Frozen experiment contract

The full mode uses actor seeds 86031/86032/86033, all three registered training
profiles, 32 actor episodes per seed/profile, 12 receipt roots (9 fit and 3
calibration), and 16 four-arm evaluation roots. The environment maximum is
72,576 transitions. The actor uses only ordinary external reward. The valve
sees only identity-free endpoint capability roles, active/incoming counts,
endpoint spell-age bins, and the two registered zero constants. Its threshold
is 0.25 and invalid or unsupported input hard-opens.

The primary descriptive statistic is the equal-block mean of
`(Y_LS - Y_LR) - (Y_CS - Y_CR)`, where each `Y` is mean external team reward
over steps 12 through 47. Raw per-root arm reward traces and block effects are
emitted so this aggregate can be recomputed. No scientific interpretation is
made by the implementation.

## Registered B run

The fixed full run completed as
`eociv_b1_real_valve_learning_288ebdaf_r3` at clean source revision
`288ebdafe6226c49868a5a645d8c3cf42b3aee4e`; the candidate code revision is
`2d2c7a891d490a172f94e9d172f56064afa5f229`. Two earlier operator launches
performed zero candidate compute and created no run root: the first exposed a
Windows path-encoding defect in the temporary assignment, and the second
exposed a missing repository-root import/bootstrap plus a stale run-id binding.
Those launcher repairs occurred before the successful run; the algorithm,
host, features, threshold, seeds, sample construction, optimizer settings and
budget did not change.

The successful run made 72,576 real environment transitions and policy calls,
288 actor/critic updates, 384 detached-valve updates, 288 training episodes,
648 receipt-clone episodes and 576 four-arm evaluation episodes. All three
actor seeds had two-sided fit support; all nine seed/profile controls executed
their exact target close counts; fallback count was zero; LR/CR validation
passed. Across 144 blocks, the recomputable primary was
`tau_B1=-7.465733177634326e-06`, mechanically classified
`VALID_NEGATIVE_SIGNAL`. Frozen-actor payload sensitivity remained small
(approximately `2.78e-05` to `1.14e-04` after training), so weak actor use of
the payload is the strongest mechanical alternate explanation for the tiny
contrast. This is a non-discriminating/negative B diagnostic, not a direction
pause, superiority claim or registered C result.

Public recomputation evidence is
`docs/research/candidates/eociv_lite/REAL_VALVE_LEARNING_RESULT.json`. It keeps
all per-seed/profile/root arm outcomes, receipt labels, training trajectories,
routes, support diagnostics and block effects. The full 48-step reward traces
remain in the Code Manager runtime root
`logs/eociv_b1_real_valve_learning_288ebdaf_r3/raw_result.json`.

Technical acceptance evidence:

- all EOCIV candidate tests: `95 passed in 25.31s`;
- two corrected real smoke runs: byte-identical, 4,752 transitions, 3
  actor/critic updates, 128 valve updates, 24 evaluation episodes, and executed
  CS close count `8 == 8` target;
- integrated review found that the first CS implementation counted but did not
  execute its exact-rate schedule; the accepted repair added a default-safe
  control-decision seam and counts actual boundary routes;
- registered phases: `TRAIN:0`, `EVALUATE:0`, `ANALYZE:0`, validation `PASSED`,
  analysis `MECHANICAL_ANALYSIS_COMPLETE`.
