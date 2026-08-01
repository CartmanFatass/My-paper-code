---
name: hmasd-workflow-change-audit
description: Use in a persistent HMASD session after plan confirmation when changing that session's owned router, role, Skill, profile, stable workflow contract, or focused test surfaces.
---

# HMASD Workflow Change Audit

## Contract boundary

This is a shared persistent-session workflow-design procedure. It grants no
scientific, formal-compute, code-acceptance or runtime authority. The calling
session accepts only its exact owned workflow artifact. Workflow Design Manager
alone accepts shared control-plane surfaces.
Generic planning, ticket, TDD and review-stack Skills remain disabled.

Use this Skill when a mutation touches any of these coupled surfaces:

- `AGENTS.md` or `.agents/roles/*.md`;
- `.agents/skills/*/SKILL.md` or their reusable scripts;
- `.codex/config.toml` or `.codex/agents/*.toml`;
- stable workflow routing or contract documents; or
- tests that enforce those surfaces.

`docs/project/CURRENT_WORK.md`, its public partitions, runtime review instances,
run artifacts, reports and ledgers are operational state, not workflow-design
context. This workflow-design procedure never loads them merely to reconstruct
history. `docs/project/RESTART_HANDOFF.md`
also remains outside this procedure and is written only on explicit user request.

### Persistent-session contract

Any persistent-session invocation carries the exact
`session_owner_role`, `session_owner_id`, `owned_paths` and `session_workspace`
from `docs/project/SESSION_WORKSPACE_CONTRACT.md`. This Skill grants no authority; the caller
role and contract define the owned surfaces. Workflow Design Manager retains
shared-control-plane ownership. Shared workflow children use
`parent=assigning_persistent_session` and receive the four assignment identity
fields; they never accept the artifact.

Ordinary algorithm implementation stays on
`hmasd-agile-research-development`. A scientific authority or evidence change
first follows `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`.

## Shared design discipline

```text
workflow_auditor=hmasd-workflow-auditor_optional_impact_map_or_postchange_verify
workflow_implementer=hmasd-workflow-implementer_optional_exact_confirmed_slice
workflow_reviewer=hmasd-workflow-reviewer_risk_triggered_only
workflow_child_parent=assigning_persistent_session
workflow_child_assignment_fields=session_owner_role|session_owner_id|owned_paths|session_workspace
workflow_child_acceptance_authority=none
workflow_design_mechanical_guarantee_scope=irreversible_external_actions_only
workflow_design_retry_recoverable_failure_mechanism=forbidden
workflow_design_single_mechanism_line_budget=100
workflow_design_single_mechanism_terminal_state_budget=3
workflow_design_new_mechanism_requires_named_deletion=true
workflow_design_net_line_growth_default=negative_or_zero
workflow_design_incident_to_mechanism_promotion_threshold=2_recurrences
workflow_design_single_incident_response=root_cause_fix_plus_note_only
workflow_design_rule_single_source=one_defining_file_others_point
workflow_design_role_file_rule_duplication=forbidden
workflow_design_sha256_whitelist=archived_response_integrity_only
workflow_design_recovery_path_line_share=must_not_exceed_normal_path
```

Use the smallest mechanism that prevents the named error. A mechanical
invariant is justified only for an irreversible external action. A retryable
failure gets a direct diagnostic or checklist, not a new state machine. Every
new or expanded mechanism names the old mechanism or text it deletes; default
net line growth is zero or negative. One isolated incident receives a root-
cause repair and note. Promotion into a reusable mechanism requires two
independent recurrences.

Every new workflow step states the error prevented, terminal condition, total
packaging/wait/compute/repair cost and the larger avoided cost. Prefer a proof-
sized direct diagnostic when it cannot increase false-scientific-conclusion
risk. Do not add review because a reviewer exists, and never create a review of
the review.

Children reduce context and mechanical effort; they add no authority or
acceptance layer. Do not delegate user collaboration, plan selection,
authority or ownership decisions, ambiguous cross-surface semantics, conflict
resolution, final acceptance, Git integration or cross-task routing. Do not
create a child when dispatch and packet-review cost exceeds the direct edit.

## One continuous change loop

1. **Inventory.** Search the workflow design control plane for the changed identity,
   path, authority term and every retired name. Include router, roles, Skills,
   registry, profiles, stable workflow contracts and contract tests. Historical
   external-review evidence and scientific uses of words such as controller are
   evidence, not automatic repair targets.
2. **Classify.** Before editing, keep a task-local impact matrix with one row per
   discovered surface: `path | relation | action | evidence`. Every row is
   exactly one of `modify`, `add`, `delete`, `unchanged-valid` or
   `historical-exempt`. Declare the exact owned path set and preserve any
   pre-existing dirty changes outside the task.
   If any child uses an isolated worktree, create its identity and path scope
   with `scripts/hmasd_workspace_ticket.py`; pass only the ticket path, require
   child-side `resolve`, and run assigning-authority verification. Never transcribe a UUID-heavy
   worktree path into an assignment.
   For a multi-family change or broad path set, the assigning session may split read-only mapping
   across two or three registered `hmasd-workflow-auditor` children with
   disjoint surface families. Six paths is a useful dispatch heuristic, not an
   authorization or acceptance gate. The assigning session merges their evidence, decides every
   classification and owns the final path set.
3. **Probe.** Run the smallest existing contract that should expose the change.
   If it passes despite a known missing relation, add one negative regression
   for that relation rather than expanding a coverage suite.
4. **Implement.** Close the smallest active-line dependency set. After the user
   confirms the complete plan, the assigning session may assign one or two registered
   `hmasd-workflow-implementer` children exact nonoverlapping path slices and
   frozen plan clauses. Each child edits only its slice, uses no Git and returns
   one `WORKFLOW_CHANGE_PACKET`. The assigning session directly implements semantic junctions,
   resolves packet conflicts and integrates the result.
   A registered
   profile names exactly one existing role charter. Every profile is registered
   exactly once; every role and Skill is routed. Remove superseded live paths
   instead of keeping compatibility aliases. Use
   a separate exact Code Project Manager assignment with `hmasd-agile-research-development` for
   any algorithm source-code slice; a workflow-design assignment never edits
   algorithm source.
5. **Verify closure.** Run the bundled checker, the affected focused contract
   tests and targeted negative searches from the impact matrix. Inspect the
   actual diff path set and `git diff --check`. The checker is structural; it
   does not replace change-specific semantic checks.
   Registered `hmasd-workflow-auditor` children in `postchange_verify` mode may
   run disjoint named read-only checks and return `WORKFLOW_VERIFY_PACKET`s.
   The assigning session still reads the final diff, checks the decisive semantics and owns the
   acceptance decision.
   Assign one registered `hmasd-workflow-reviewer` only when the integrated
   change touches authority or file ownership, locked routing or model settings,
   Pro transport/recovery, compute admission, an action-performing script/hook,
   or unresolved cross-worker semantics. Its `WORKFLOW_REVIEW_PACKET` is
   advisory. Ordinary low-risk documentation edits need no reviewer, and there
   is no review of the review.
   Only when the user explicitly requests a workflow cost audit, assign one
   registered `hmasd-workflow-cost-reviewer` with `fork_turns=none`. Its return
   is optional evidence for the assigning session, never an automatic
   acceptance owner or recurring gate.
6. **Integrate.** Inspect the exact staged path set and
   `git diff --cached --check`, then commit and push only the assigning
   session's accepted owned paths. Preserve every unrelated staged, tracked and
   untracked path. The Git receipt is not a second acceptance owner.
7. **Reload smoke.** If router, registry or profiles changed, start a fresh
   Codex task before relying on discovery. Smoke every changed callable profile
   against its exact fail-closed boundary. Do not substitute a default child
   when a registered type is unavailable.

Run the structural checker with the Python interpreter registered in the
assignment. A missing interpreter is a smallest-boundary blocker; do not load a
runtime document to discover one:

```powershell
& '<registered-python>' .agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py --repo .
```

Add change-specific active files or retired terms when needed:

```powershell
& '<registered-python>' .agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py --repo . --active-path AGENTS.md --forbid hmasd-old-agent
```

## Acceptance and stop

The assigning session accepts only when the impact matrix is classified, structural closure passes,
focused contracts pass, targeted stale-reference searches are explained, the
exact changed path set and final diff are inspected by that session, every assigned
workflow-child packet is reconciled, and any user-requested workflow cost audit
has no unresolved finding. A fresh-task profile smoke may remain
an explicit post-restart condition when the current task cannot reload its own
router.

Stop for a missing authority decision, an ambiguous active-versus-historical
surface, same-file collision or unavailable required profile. Do not resolve a
scientific ambiguity or weaken the checker locally.
