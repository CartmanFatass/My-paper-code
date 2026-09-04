# Synthetic Acceptance

## Boundary checks

- `tests/hmasd_control_plane`: 79 passed.
- Requirements registry validates and renders deterministically.
- E1 routes to `WORKFLOW_RECOVERY_MANAGER` with no user question.
- Toy multi-day measured runtime routes as `E2_ASSIGNMENT_RECOVERY` to CM.
- Current host CPU/memory preflight and matching C++/parallel manifest validate.
- Constraint lint is report-clean for the repository boundary set.
- `.codex/config.toml` has `features.hooks=false` and no hook tables; semantic
  MCP remains enabled independently.

## Seeded artifacts

- Routine code assignment/result: `assignments/ASSIGNMENT_constraint_lint.md`.
- R2 execution assignment, resource snapshot and manifest:
  `assignments/ASSIGNMENT_native_execution_preflight.md` and `resources/`.
- Synthetic E1 result: `results/RESULT_asg_constraint_lint_seed_E1.md`.

The final mixed acceptance suite completed with `698 passed, 66 skipped` in 99.51s.
The skipped cases are historical hook-activation evidence; the active semantic
MCP, context lifecycle, supervisor, and low-intrusion suites are green.
