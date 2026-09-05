# CBSC-OMRC-B01 drain receipt — 2026-09-04

- Direction: `capability_bound_semantic_currentness`
- Current object: `CBSC-OMRC-B01` (`B/EXPLORE`)
- Direction branch: `codex/cbsc/defect8-20260904`
- Clean pushed boundary: `be2cc5ad67eb31c40c9c49107d1113140c648209`
- Last result-bearing task: `cbsc-b1-r06-a138b01534-01`, terminal technical failure
- Next result attempt: `b1_scout_r07`, **not launched**
- Scientific object consumed: **false**
- Scientific result/polarity: **none**

## Current authority and drain action

Root transmitted the owner's 2026-09-04 instruction to drain the current wave after work already
in flight, without interrupting the direction: finish the existing venv-interpreter repair/review,
create no new task, and do not launch r07. That direct owner instruction supersedes the future-launch
part of the earlier unattended option while the pause is in force. It changes scheduling only; it
does not change CBSC lifecycle, priority, fusion, card meaning, evidence polarity or the result rule.

At receipt of the instruction, no r07 `agent-task` existed. The CM had already submitted four
non-result exact-SHA verification tasks for the active repair; those were allowed to drain and no
later task was created. No CM, reviewer, operator, learner or result invocation was added after the
instruction.

## Engineering boundary completed before pause

The preserved r06 failure was reproduced directly over exact commit
`a138b01534f41f88d1045179fadc464aefa79e9e` and its recorded request. The B1 launcher had resolved
the configured venv symlink to the underlying UV base interpreter, dropping the venv's NumPy and
Torch packages. The child stopped at import, before model construction. The immutable incident
records zero completed arm-seeds, null scientific claim/branch, and
`scientific_object_consumed=false`.

CM repaired only the B1 subprocess interpreter identity. Admission construction/validation,
ordinary worker launch, assess-run, policy replay launch and replay receipt validation now retain
`Path(os.path.abspath(sys.executable))` rather than resolving symlinks. The bound path, executable
byte hash and exact command remain mutually consistent. No `PYTHONPATH` or environment fallback was
added. B0, learner, FP32, RNG, host, arms, seeds, budgets, checkpoints, admission floors, telemetry,
result rule and scientific fields are unchanged.

The accepted CM source is exact commit `5a1b1b7feae9f67063ba0a5dd1d66085684a0d4b`:

- final diff from its base: four files, `+10/-8`;
- runtime: six in-place substitutions, `+6/-6`, with no orchestration growth;
- tests: `+4/-2`; runner: zero lines; `scope: none`;
- local focused profile: `12 passed, 1 deselected` in `64.38` seconds; the deselected pre-existing
  test hard-codes the primary checkout path and also fails on the unmodified base in an isolated
  worktree;
- independent reviewer: PASS, no material finding;
- exact remote worker module entry: task `cbsc_b1_worker_help_5a1b1b7fe_05`, exit `0`;
- exact remote policy-replay module entry: task `cbsc_b1_policy_help_5a1b1b7fe_06`, exit `0`;
- exact remote focused profile: task `cbsc_b1_focused_5a1b1b7fe_07`, `17 passed` in `39.58`
  seconds, exit `0`;
- exact remote readiness: task `cbsc_b1_readiness_5a1b1b7fe_08`,
  `COMMIT_CONFORMANT / B1_FORMAL_READY / start_authorized=true`, exit `0`.

The two CM commits were integrated without modification into this direction branch. A Git surface
comparison between `5a1b1b7feae9f67063ba0a5dd1d66085684a0d4b` and the clean pushed boundary above is empty for
all declared CBSC authority, source, runner and test paths. No new remote check was created for the
integration commit because the owner had already ordered the drain.

## Quiescence receipt

- `cbsc-b1-r06-a138b01534-01`: terminal `failed`, exit `6`; preserved incident only.
- All four pre-instruction `5a1b1b7fe` verification tasks: terminal `finished`, exit `0`.
- Prospective `cbsc-b1-r07-be2cc5ad6-01`: `not_found`.
- No r07 output root, admission receipt, RNG master, model, optimizer, checkpoint, evaluation or
  summary exists.
- Direction worktree is clean; local HEAD and upstream are identical.
- Owner-console reviews returned no separate file-based instruction to apply.

## Bounded reading and resume point

Direct observation establishes that the interpreter portability defect is technically repaired and
that the exact repaired source passes module-entry, focused and readiness checks on the configured
Linux node. It does not establish CBSC mechanism value. The strongest contrary engineering fact is
the quarantined r06 import failure; it is fully explained by the old launcher and remains valuable
provenance, not scientific evidence.

The frozen B1 question and claim ceiling remain unchanged. Headroom remains
`HC-M / CANDIDATE_ASSETS_MISMATCHED`, with null terms and gap; it is non-gating and carries no
polarity. `DIRECTION.md` and `PORTFOLIO.md` are therefore not changed.

If the owner later releases the pause, resume from this repository boundary: first read owner
reviews and compare the declared CBSC source surface with then-current authority; then use one new
exact pushed SHA, one new detached remote worktree, the fixed B0/archive inputs, a no-duplicate
task/root check, exact readiness, and fresh node-local `admit-memory && runner` for a create-only
`b1_scout_r07`. Do not resume r06 or reuse any prior receipt. Until that instruction, no work is
scheduled.
