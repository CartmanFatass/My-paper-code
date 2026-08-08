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
