# Stage 1 long-task assignment and intake pilot

## Observed facts

- Operational Root authored and validated
  `assignments/ASSIGNMENT_context_foundation_review.md` for one bounded,
  file-backed `hmasd-reviewer` review.
- The original validation exposed two implementation gaps: the registered
  reviewer role was not accepted, and a REVIEW assignment could not use
  bounded `search_roots` when `affected_files` was empty.
- CM repaired those gaps without weakening IMPLEMENTATION or OPERATION exact
  file requirements. The final focused cycle was
  `22 passed, 1 skipped`; the skip records the host's lack of Windows symlink
  creation privilege, while production containment still resolves and checks
  every configured root.
- The first reviewer child resolved the relative assignment path against the
  dirty main worktree. It did not read the candidate scope and wrote no result.
  A fresh reviewer then used the exact Stage 1 worktree as repository root.
- The fresh result at
  `results/RESULT_context_foundation_review.md` validates against the exact
  assignment with `valid=true`.

## Scope-local review conclusions

The reviewer found that the repository-owned context spine exists, but reported
two normal-path technical defects that must be reconciled before Stage 1 final
acceptance:

1. `sources_for_actor()` includes `ON_DEMAND` sources by default while a
   `ROLE_REQUIRED` P0 correction is excluded unless explicitly requested, which
   conflicts with the declared load policies.
2. `context_foundation_health()` can report `OK` while `CURRENT_WORK` metadata
   omits `control_plane_runtime` from `common_record_ids`, retains a stale
   `state_updated` value, and the health query omits the file-level ADR/source
   checks already performed by doctor.

The result does not establish App Server live/runtime behavior, scientific
validity, technical acceptance, Portfolio disposition, or a project-wide pause.

## Remaining authorized work

- CM may perform an unchanged-authority repair of source selection semantics,
  CURRENT_WORK metadata validation, and shared file-only health checks.
- CM must add focused regression tests and use an independent reviewer for the
  repaired load-policy and false-green health risks.
- Task 12 acceptance and external Pro review remain authorized after the repair
  and the complete Stage 1 suite are green.

## Operational Root decision

`root_decision_class=bounded_engineering_repair`.

The exact first-child path-resolution operation is closed and is not repeated.
It does not imply any broader review, direction, or stage prohibition. The fresh
review result is accepted as scope-local evidence, not as final technical
acceptance. Stage 1 continues through the smallest CM-owned repairs above; no
App Server live action or Stage 2 work is authorized yet.
