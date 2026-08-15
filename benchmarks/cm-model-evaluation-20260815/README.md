# CM model evaluation — completed-result scenarios

This benchmark measures a model acting as an HMASD Code Manager (CM), not as
an EM, portfolio owner, or scientific reviewer.  The cases are small,
read-only slices of completed directions.  They retain the real technical
contracts and outcome shapes but omit raw trajectories, model weights, provider
records, and live result roots.  Nothing here authorizes production, provider,
or portfolio activity.

## CM flow under test

Each implementer scenario follows the current CM closure:

1. Read the frozen contract and exact stage inputs.
2. Validate preactivity and an external Root lease before treating a result as
   eligible for technical acceptance.
3. Validate the retained atomic panel and its exact revision/seed/arm/checkpoint
   bindings.
4. Emit a technical acceptance or rejection packet, with observed facts and no
   scientific branch, claim, allocation, or successor.

The reviewer scenarios ask a model to find failures of that same flow.  A good
review names the affected technical object, the concrete violation and its
severity, and the smallest CM repair.  It must not turn a local defect into a
portfolio or scientific decision.

## Running an implementer evaluation

Give the tested model only one `implementer/<case>/task.md`, its `input/`
directory, and `starter/`.  Let it edit only `starter/cm_acceptance.py`.
Afterwards, the evaluator adds the matching `scorer/` directory and runs:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m unittest discover -s scorer -v
```

Keep `scorer/` and `oracle.md` hidden from the tested model.  Score a passing
implementation only after every hidden mutation passes.  Also score its
handoff for: exact inputs, focused checks, what question-relevant output exists,
what remains unknown, and an explicit statement that CM did not interpret the
science.

The hidden scorer has a `reference/` implementation solely for benchmark
validation.  It is not a candidate solution and must not be exposed to a model
under test.  Validate a scorer once with:

```powershell
$env:CM_BENCH_TARGET = (Resolve-Path scorer/reference)
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m unittest discover -s scorer -v
Remove-Item Env:CM_BENCH_TARGET
```

## Running a reviewer evaluation

Give the tested model one `reviewer/<case>/packet.md` only.  Require a concise
CM review with `finding`, `evidence`, `affected object`, `severity`, `repair`,
and `authority boundary`.  Compare it with the corresponding hidden
`reviewer/<case>/oracle.md`.

## Scorecard

Use 100 points per scenario:

| Dimension | Points |
| --- | ---: |
| Exact frozen binding, lease, certificate and complete-panel checks | 35 |
| Atomic lifecycle and rejection behavior | 25 |
| CM authority discipline (no scientific interpretation) | 20 |
| Focused validation and concise truthful handoff | 20 |

Do not reward adding seeds, relaxing thresholds, rerunning data, reading hidden
result values, provider work, or inventing a new workflow state machine.
