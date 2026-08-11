# Direction-scoped owner control plane: fresh-Root handoff

```text
document_kind=root_restart_handoff
handoff_revision=1
handoff_parent_commit=89303a03f4ec0b9718bc5ecca2aeb8abcab8505f
canonical_branch=aggressive
created_at=2026-08-11
next_actor=fresh_root
research_execution=false
science_state_changed=false
```

## Conclusion and restart objective

The direction-scoped research/code control plane is integrated and verified.
This invocation intentionally stopped before choosing or executing a real
research direction. A fresh Root should reload canonical state, perform the
small registration/scope smoke described below, select one currently available
direction from compact research continuity, and then run one bounded complete
`EM -> CM -> Experiment Operator -> publication -> reverse intake -> external
review` flow.

This file is the restart interface. Do not reconstruct this task from the old
thread, background descendants, retained worktrees, rollout history or temp
test artifacts.

## Integrated control-plane meaning

- Root owns macro/portfolio scientific comparison, ordering, pause/continue,
  dependency choices and complete-map/cross-direction acceptance. Root does not
  execute direction research and does not acquire CM technical acceptance.
- EM is direction-scoped only: `research_scope_key=direction:<id>`. There is no
  portfolio EM. One EM owns only that direction's decomposition, research
  synthesis, project-validation intake and reverse-intake delta.
- CM is scoped only as `code_scope_key=direction:<id>` or
  `code_scope_key=shared:<component>`. There is no `integration:<group>`,
  Convergence CM or `shared:all` lane.
- A direction/shared CM's technical acceptance is final for its slice. Root
  mechanically integrates accepted candidates and runs union Tests/Static. A
  technical semantic conflict returns to the exact owning CM(s), or to a
  temporary named shared CM when one shared component is the real owner.
- One writable L1 assignment receives one Root-managed worktree. Its exact,
  disjoint L2 writers share that worktree and never own Git/helper/receipt
  lifecycle. A separate candidate/release lifecycle requires a separate L1.
- Root-facing labels are `WM_<purpose>`, `EM_<direction>` and
  `CM_<purpose_or_direction>`. Root-to-L1 uses caller action
  `fork_turns=1`; registered L2 briefs use the profile/Role-prescribed context
  boundary, normally explicit `fork_turns=none`.
- Native payload is authoritative when no assignment-file locator is supplied.
  Leaves may read their mandatory Role/Skill immediate references, but must not
  search for or reconstruct a nonexistent assignment file.

Formal or project-canonical scientific claims remain at the user/External Pro
boundary. None of the changes above promotes an ordinary experiment result to
that status.

## Git and verification evidence

Canonical main was fast-forwarded from `901c3b9a` through these integrated
commits:

- `46fe10c6` - direction-scoped EM/CM control plane and contracts;
- `5efa1fc2` - pointer-only project-operation owner records;
- `89303a03` - cross-candidate contract alignment and case-sensitive
  `record_kind` dispatch.

The handoff commit is the commit containing this file; discover it after reload
with `git log -1 --format=%H -- docs/project/migration-validation/2026-08-11_direction_scoped_owner_restart_handoff.md`.

Tests completed before this handoff:

- WDM slice evidence: 131 relevant pytest tests and four PowerShell contracts
  passed after the sole integrated Reviewer findings were closed.
- Root cross-candidate union evidence: 91 pytest tests passed; CPM, research
  workflow, workflow delegation and profile benchmark PS1 contracts all passed.
- Agent harness passed with 21 profiles, 22 Roles and 9 Skills.
- 22 TOML files and two JSON files parsed; `git diff --check` passed.
- `codex --strict-config doctor --summary` reported 17 ok, 0 warn and 0 fail.

No real research, solver, training, result-bearing runtime, result publication
or external review was started by this control-plane task.

## Lifecycle state

The Root integration worktree receipt is `RELEASED`:

- `temp/sessions/root/managed-worktrees/root_direction_scoped_union_f1.json`

The three original cherry-picked candidate commits were uniquely unprotected,
so the helper correctly refused direct release. Their checkouts were removed
with assignment-scoped recovery refs and receipts are
`RETAINED_FOR_RECOVERY`:

- `temp/sessions/workflow_design_manager/managed-worktrees/wm_direction_scoped_owners_f1.json`
- `temp/sessions/code_project_manager/managed-worktrees/cm_shared_project_operations_index_f1.json`
- `temp/sessions/workflow_design_manager/managed-worktrees/wm_direction_union_contract_repair_f1.json`

Recovery refs:

- `refs/hmasd/root-managed-recovery/wm_direction_scoped_owners_f1`
- `refs/hmasd/root-managed-recovery/cm_shared_project_operations_index_f1`
- `refs/hmasd/root-managed-recovery/wm_direction_union_contract_repair_f1`

Two disposable external pytest roots remain because the command runner blocked
the attempted recursive deletion even after exact-path validation:

- `C:\Projects\ht\dsu_20260811_1245` - 158 files, about 255 KB;
- `C:\Projects\ht\dsu_final_20260811_1311` - 158 files, about 255 KB.

They are not canonical state and do not block restart. Never broaden cleanup to
`C:\Projects\ht`; remove only these exact resolved targets through an
authorized exact cleanup path, or retain them as harmless disposable evidence.

Pre-existing untracked user paths in the main checkout were preserved and are
not part of this handoff or its commit. A fresh Root must inspect `git status`
and continue to leave unrelated paths untouched.

## Fresh-Root startup sequence

1. Read `AGENTS.md`, this handoff, and the smallest relevant pointers in
   `docs/project/L1_STARTUP_CONTEXT.md` and
   `docs/project/SESSION_WORKSPACE_CONTRACT.md`. Do not preload owner corpora.
2. Confirm the canonical branch contains this handoff and that tracked status
   is clean. Run a fresh registration/scope smoke for exact registered WM, EM
   and CM types using `fork_turns=1`. Use valid keys such as
   `direction:smoke-a` and `shared:smoke-component`; prove no default
   substitution, no portfolio EM, no Convergence CM, no L3 and no write/runtime
   action. This smoke is recognition/context evidence, not research.
3. Load `local_research/RESEARCH_CONTINUITY.md`, then follow only its exact lazy
   pointers to the current Direction Action Map and the smallest direction
   records needed for macro comparison. Root selects one genuinely available,
   bounded direction. Reconfirm dependencies and current state rather than
   relying on this handoff's historical examples.
4. Prefer a direction that needs no package installation, has closed scientific
   predecessors, has an inexpensive bounded technical test, and has no live
   path/resource conflict. Do not reactivate a parked or dependency-blocked
   direction merely to exercise the topology.
5. Dispatch `EM_<direction>` with
   `research_scope_key=direction:<direction>` and `fork_turns=1`. The EM must
   use the direction research and project-validation Skills, perform actual
   direction-local research, and return a self-contained outbound proposal to
   Root. It must not compare sibling directions or modify the complete map.
6. If code/runtime work is justified, Root provisions one writable L1 worktree
   and dispatches `CM_<direction>` with the matching
   `code_scope_key=direction:<direction>`. Its disjoint L2 writers share that
   worktree. CM performs scope-local review/readiness and returns final slice
   technical acceptance; Root records and mechanically integrates accepted
   paths, then runs union Tests/Static.
7. Only after candidate readiness and a fresh resource observation, dispatch
   exactly one bounded registered Experiment Operator. Preserve one-full/no
   retry semantics, isolated roots/checkpoints/RNG and exact receipt validation.
   Do not install missing dependencies or silently select another treatment.
8. Root publishes only accepted result bytes, routes the exact direction-local
   reverse brief to the same EM, and receives one bounded scientific intake.
   Root then updates macro/complete-map state only from that accepted direction
   delta; EM never receives or accepts the full map.
9. Run the authorized external review through the registered Agentify transport
   and External Pro boundary. Preserve the raw external response and the
   direction owner's semantic intake separately; tool recognition is not proof
   that a review was sent or answered.
10. Commit accepted tracked artifacts, record/release-or-retain every exact
    receipt, dispose or report exact temp residue, and report Tests, Static and
    Semantic evidence separately.

## Completion evidence for the next task

The requested live-flow test is complete only when all of the following exist:

- one real available direction chosen from freshly loaded compact state;
- one direction-local EM scientific conclusion and Root-relayed CM brief;
- one CM-accepted code/config candidate in a direction worktree;
- candidate-bound readiness evidence when triggered;
- one bounded Experiment Operator receipt and validated raw result;
- one accepted tracked/public result publication;
- one exact reverse intake by the same direction EM;
- one actually completed external review with preserved raw response and
  bounded semantic intake;
- canonical commits plus terminal worktree/receipt disposition;
- a final report that distinguishes Tests, Static checks and Semantic review.

## Workflow-efficiency follow-up (not a restart blocker)

This migration was slower than its edits because cross-candidate assertions ran
late, first-failure authorization exposed stale prose serially, and a two-file
test-only repair still paid the full Auditor/Implementer/Reviewer cost. Preserve
WDM's workflow semantic authority, but a future user-confirmed workflow change
should make risk tiers operational: full review for authority/topology/shared
contracts, lighter bounded review for cross-file contracts, and one causal
batch plus direct evidence for low-risk test recognizers. Run cross-candidate
contract tests as soon as writer bytes freeze, before separate slice acceptance
when possible. Do not redesign WDM as part of the live direction-flow test
unless the user explicitly asks for that separate workflow change.
