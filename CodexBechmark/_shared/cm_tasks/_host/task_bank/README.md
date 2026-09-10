# Host-only bounded task bank

Eight synthetic repairs: five classic tasks, three non-examples. Each installation
contains only its own `cm_<task_id>/` package: three source modules, `__init__.py`,
`public.py`, and `TASK.md`. Only the two implementation modules listed by
`owned_paths` may be repaired; `api.py` supplies the caller. A repair can change one
or both owned files. Reference material and hidden assertions are never installed.
The host/runner owns selection of exactly one classic and one non-example.

Difficulty is an **ex-ante estimate**, not calibrated empirical difficulty:

| Task | Kind | Estimate |
| --- | --- | --- |
| masked_credit | classic | medium |
| timeout_bootstrap | classic | hard |
| evaluation_stream | classic | medium |
| publish_count | classic | easy |
| replay_snapshot | classic | medium |
| fixed_slot_credit | non_example | easy |
| finite_horizon | non_example | medium |
| paired_tape | non_example | hard |

`TASKS` includes a specific difficulty rationale, brief, owned paths, public argv,
source revision and provenance for each task. Its brief and installed `TASK.md`
contain the same scientific assumptions and acceptance facts for every spec level.
They are a task statement, not a pre-authored CM delegation handoff or solution.
The host must present the task brief at all levels and run the public command from
the candidate workspace with the scientific interpreter. No production HMASD
training or evaluation is invoked.

## APIs and commands

The package imports with stdlib only. `install(workspace: Path, task_id: str)`
writes only one task. `apply_reference(workspace, task_id)` is calibration-only
and changes only owned paths. `grade(workspace, task_id, interpreter=None)` returns
`{'passed': bool, 'checks': [...]}`. Its default interpreter is `sys.executable`;
pass the configured scientific interpreter when the host uses system Python.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B CodexBechmark/_shared/cm_tasks/_host/task_bank/grade.py --workspace ABS_WORKSPACE --task masked_credit ABS_OUTPUT.json
```

The positional output path is optional; JSON is always printed to stdout. When
provided, its output parent must exist. The CLI exits 0 for pass and 1 for a failed behavioral
check. `--python PATH` overrides the worker interpreter. Grading launches one
isolated `-I -B` subprocess with a 30-second limit and runs host assertions against
candidate source directly, never candidate `public.py`. It reports stdout/stderr
for diagnosis. These assertions are not a security sandbox for adversarial Python;
file ownership and malicious grading bypass remain the independent reviewer's
responsibility. Additional fixtures test documented cases, not extra requirements.

Calibration is bounded to baseline, reference and one plausible wrong patch per
task, plus public baseline/reference checks and a two-install isolation check:

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B CodexBechmark/_shared/cm_tasks/_host/task_bank/calibrate.py --scratch-parent C:/Projects/HMASD/temp/tests --out CodexBechmark/_shared/cm_tasks/_host/task_bank/CALIBRATION.json
```

The script creates a unique `temp/tests/cm-bank-*` directory, retains its diagnostic
summary, then removes only its own scratch in `finally`. No `.git` is created in
candidate packages. Calibration demonstrates these known defects and mutants are
distinguished; it does not establish benchmark discrimination between models or
spec strategies, exhaustive correctness, or a performance improvement. Hidden
checks are deliberately small and deterministic; no timing performance threshold
or training outcome is tested.

## Provenance and semantic limits

The inspected current source revision is
`1385b56b6a0761d4064dcafbce0c66c590ecc5a2`. Paths and relevant boundaries:

- `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`,
  `clipped_policy_loss`: mask/reduction; `ucope/paired_training.py`: detached
  rollout-derived actor advantage. The tasks remove PPO, optimizers and environments
  and replace these with explicitly declared actor objectives.
- `experiments/candidates/vap_folr_core/public_lifecycle_b01/collection.py`,
  `collect`/`sample`: observation lifetime, terminal rows and stacked replay. The
  benchmark adds a synthetic mutable observation buffer and timeout wrapper. Its
  timeout semantics are **not** claimed to be those of the source environment.
- `experiments/candidates/ucope/crossed_evaluation.py`: paired support concept.
  The benchmark uses invented seeded tensor/action and weather fixtures; the real
  crossed-support mathematics and policies are not copied.
- `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_metrics_artifact.py`:
  separate producer/publication boundary. The benchmark substitutes a deterministic
  score producer and three-field JSON output; no historical publishing failure is
  reproduced.

Before candidate runs, `masked_credit` was aligned with the current UCOPE reduction
and `patterns/examples/masked_reduction.py`: sum active agent terms, then average
over all time rows, including all-held rows (denominator T). `fixed_slot_credit`
intentionally uses denominator T*agents. The pre-freeze alignment changed the common
brief, reference, public fixture, independent hidden oracle and wrong-patch fixture;
its targeted calibration is recorded in `CALIBRATION.json` alongside the retained
original calibration. The original masked-credit record describes the superseded
active-count contract and is not evidence for the final reduction.

These tasks are **synthetic reconstitutions inspired by current project code**,
not verbatim extraction or recovered prebug commits. Every defect and simplified
contract is benchmark-authored. The three non-examples intentionally counter unqualified
reuse of agent-sum/row-mean normalization, external-timeout bootstrapping, and per-arm
independent exogenous evaluation streams. Scientific reading used Foundations
§§1–2 and the RL topic's return/gradient sections to make these assumptions explicit;
it supplies no research claim or experiment authorization.
