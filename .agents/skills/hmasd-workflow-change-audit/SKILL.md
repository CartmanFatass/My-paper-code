---
name: hmasd-workflow-change-audit
description: Use only in the task-scoped Workflow Design Manager L1 after plan confirmation to implement, verify, accept and route one centralized HMASD control-plane proposal.
---

# HMASD Workflow Change Audit

## Contract boundary

```text
activation_trigger=confirmed_workflow_plan_execution_or_verification
startup_preload=false
```

Workflow Design Manager is the sole workflow design, modification and semantic
acceptance authority. Root owns physical application, lifecycle, Git and final
reload. This Skill grants no science, code, code-acceptance, runtime or
project-state authority. CPM, Explorer and other sessions report exact
requirements or defects through Root; they do not edit or accept control-plane
surfaces.

The Session Workspace Contract is the single mechanics source for workspace,
managed worktrees, lifecycle receipts, progress meanings, review, convergence,
Root closure and Git boundaries. This Skill adds only the post-confirm route,
focused checks, bounded recovery and acceptance consequences below. Use it for
router, role, Skill, profile, hook, registry, stable workflow contract,
workflow script or focused workflow-test changes; operational state, review
instances, run artifacts, scientific ledgers and implementation code are
outside this procedure.

User confirmation remains mandatory before mutation. Every mutation is carried
out by a registered Workflow Implementer L2 on its exact assigned paths; WDM
never writes. The normal registered Auditor, Implementer and Reviewer types and
the native-default exception remain unchanged. Children return only to WDM;
Root remains the sole user, cross-owner, physical and lifecycle actor.

## Routing, validation and review

Planning first consults `docs/project/CONTROL_PLANE_DOCUMENT_ROUTES.md`. A clear
row names the defining source, direct consumers and focused tests. A missing,
ambiguous, conflicting or authority-crossing row routes to the bounded
registered Auditor rather than repository rediscovery or guessing.

Classify risk by semantic consequence, not file count. `high` means authority,
topology, cross-owner or shared-contract impact and requires the Auditor.
`bounded_contract` means a stable cross-file contract within one owner; a clear
route may skip the Auditor when WDM records its rationale.
`low_causal_repair` means wording, a recognizer or one bounded assertion family
that preserves accepted meaning; WDM may skip the Auditor with rationale even
when tightly coupled files exceed one. This is a routing choice, not a gate or
second acceptance owner. The canonical keys are
`workflow_change_risk_tiers` and `workflow_route_table_policy` in the Session
contract.

The normal validation layers remain exactly three: writers run `slice_local`
checks on owned paths and the smallest affected contracts; after all writes
freeze, WDM runs exactly one `integration_cross_slice` suite; and Root alone
runs `runtime_fresh_smoke_after_root_integration_reload` after integration and
canonical reload. Writers never run the whole suite. Once all consumed
producer, consumer and test bytes are frozen, run one focused causal-family
check before package acceptance. Reuse that result only while those bytes stay
unchanged. Setup failures are repaired and rerun at the same layer; product
failures repair the causal contract or implementation.
The canonical timing pointer is
`workflow_causal_check_timing=when_all_consumed_bytes_are_frozen_before_package_acceptance`.

WDM publishes the five Session-defined status observations
`DISPATCHED`, `WRITES_COMPLETE`, `TESTS_COMPLETE`, `REVIEW_READY` and
`TERMINAL`. Each named observation is emitted at most once. Adjacent relevant
observations may share one outcome-first report carrying evidence and the next
actor; there is no requirement for five separate messages. The names and
meanings remain status-only, non-scheduling and non-accepting, and
`TERMINAL` only says that WDM returned its terminal conclusion to Root. The
canonical local consequence is
`workflow_progress_event_emission=each_relevant_event_at_most_once|adjacent_observations_may_share_one_report`.

A singleton package is one writable WDM L1 assignment's exact final frozen
bytes, including its disjoint Implementers in the shared L1 worktree, reviewed
together. After routed checks and exactly one advisory Reviewer, WDM may
semantically accept that package and return it to Root; no fresh convergence
WDM or worktree is needed solely for singleton integration. True
multi-candidate convergence occurs only when Root combines two or more
independently reviewed WDM candidates or when the actual union differs from
every reviewed package. In that case a fresh WDM reviews the actual union,
uses exactly one advisory Reviewer and owns union acceptance. The canonical
keys are `workflow_singleton_package`, `workflow_singleton_acceptance` and
`workflow_multi_candidate_convergence_trigger`.

## Root mechanics and bounded fallback

Root turn closure, bounded waits, mailbox delivery, accepted-path recording,
integration, canonical reload, runtime smoke and release-or-retain actions
are defined by `docs/project/SESSION_WORKSPACE_CONTRACT.md`. WDM returns its
candidate or accepted-package conclusion through the current Root boundary and
does not promise a commit, push, lifecycle receipt or external cleanup.

The normal path is direct orchestration with one bounded local recovery. A
recoverable tool or transport failure is diagnosed and continued or parked
without blocking unrelated work. Stop and return to Root for material plan
drift, a same-file collision, an unavailable required profile or a missing user
decision. Root may finalize unfinished work only when genuinely blocked on new
user authority or a decision, or when the user explicitly replaces or cancels
the work; blocked actions and unfinished work are reported. No scheduler,
queue, ledger, ticket, hash/fingerprint admission, polling loop, recovery state
machine or new global gate is introduced.
Dispatch read-only Auditor/Scout concurrently with already-freezable
implementation slices; run exact disjoint Implementers parallel-first; serialize
only actual information dependencies or same-file writers.

Mechanism budgets constrain only irreversible/high-cost actions and new
recovery branches. If a failure means only “try again,” use the smallest direct
diagnostic or one-line runtime checklist. A new mechanism must identify the
old text/mechanism it deletes, its terminal condition and recurring cost, and
must be justified by focused contract evidence and qualitative maintainability.
One incident does not create a permanent rule; require two independent
recurrences. Never use a hash, digest, byte count or fingerprint as workflow
admission, routing, handoff, recovery or acceptance evidence. Git revisions are
source locators only.

## Workflow change loop

1. **Inspect.** Read the routed control-plane paths, declare the exact owned
   path set, preserve unrelated work and identify the smallest normal-path
   probe. Do not mutate before confirmation.
2. **Delete or edit.** Remove superseded rules before adding text. WDM routes
   exact non-overlapping paths to registered Implementers; it does not write,
   stage or use Git. The Session contract supplies worktree and lifecycle
   mechanics.
3. **Focused check.** Writers run their `slice_local` checks. After all
   producer, consumer and test bytes freeze, run the focused causal-family
   check once, then WDM runs the single `integration_cross_slice` suite. Run
   the structural harness, stale-term search and `git diff --check` when they
   are the smallest affected contract. Exactly one advisory Reviewer follows
   the frozen evidence; the Reviewer is read-only and cannot accept or create
   a second pass.
4. **Return and reload.** Inspect exact changed paths and begin the result in
   ordinary language: name the package or union, why it matters, the direct
   consequence checked, residual uncertainty and the next actor. Append only
   the relevant candidate/acceptance packet, commands and evidence. Root then
   performs its separately authorized integration and reload actions.

The configured hooks remain empty and disabled. No Hook Stop route is part of
this workflow. Tool/OS sandboxing and exact assignment paths remain the
authoritative write boundary.

## Harness

Run with the registered interpreter:

```powershell
& '<hmasd_python_interpreter>' `
  .agents/skills/hmasd-workflow-change-audit/scripts/check_hmasd_agent_harness.py `
  --repo .
```

The harness checks structure and retired terms only; it cannot decide semantic
sufficiency or acceptance. Add `--active-path` and `--forbid` only for a
change-specific stale reference.

## Acceptance

For a singleton package, WDM's acceptance report opens in ordinary language
with the concrete package impact, child results and direct checks considered,
why the package is ready, what consequence was checked, what remains uncertain
and which actor acts next. It may then append exact paths, commands, statuses
and evidence. Accept only when the routed impact is closed, child packets are
reconciled, focused and structural checks pass, stale references are explained,
exact changed paths are inspected and exactly one advisory Reviewer has
reported. WDM may semantically accept this singleton package and return it to
Root; this does not claim Root integration or a multi-candidate union.

Only the true multi-candidate path receives a fresh convergence WDM after Root
integrates the exact candidate union. That WDM reviews the actual union with
one advisory Reviewer, resolves any actionable finding in its one pass, owns
union semantic acceptance and returns exact paths, verification and the reload
boundary to Root. Reviewer advice, a slice package, Root integration or a
commit alone never implies union acceptance. Root decides whether a separately
authorized candidate commit is needed.
