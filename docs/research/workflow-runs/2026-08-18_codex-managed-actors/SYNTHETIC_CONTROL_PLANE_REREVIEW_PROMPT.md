# Rereview Prompt: HMASD Codex Supervisor Synthetic Control Plane

Copy everything below the line to another model that can read
`origin/aggressive`. This prompt is for a **synthetic code/architecture
review**. It is not Phase 1, Stage 3, or Stage 4 acceptance. It does not
authorize live App Server work.

```text
document_kind=synthetic_control_plane_rereview_prompt
supersedes=SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md
prior_reviewed_commit=883eb028c3cbdadf99159869ea722e8a4a6a5f6d
prior_reviewed_range=19a80529fa9b0ff7327d704cef92fe2fd065ae2e..883eb028c3cbdadf99159869ea722e8a4a6a5f6d
```

The prior rereview of `883eb028` returned `REVISION_REQUIRED`. This
prompt reviews the corrective commit that claims to close those defects.

---

## Assignment

Review the HMASD Codex App Server supervisor on branch `aggressive` at
commit `f7a5304560e52b2b78faadb6d6de4049a5b9a5f9`.

Repository: the HMASD git remote the operator pointed you at.
Branch: `aggressive`.
Review range:

```text
883eb028c3cbdadf99159869ea722e8a4a6a5f6d..f7a5304560e52b2b78faadb6d6de4049a5b9a5f9
```

Parent of this corrective slice:

```text
883eb028  fix: make incident terminal and recover prepared siblings
```

`d13760d8` only pinned the previous rereview prompt; treat it as
documentation, not a science-bearing change.

This is operational control-plane infrastructure, not a research
direction and not Portfolio work.

## Prior rereview that this commit must close

`883eb028` closed the previous High set (managed completion guard,
mutation-aware attach rollback, unresolved-incident begin fence,
PREPARED sibling recovery, source-resolution flag, one queue consumer
design, timestamp-only reject, VALIDATED+receipt reconcile, exact
item/completed lookup). It remained `REVISION_REQUIRED` for three High
defects and three Medium leftovers:

1. `INCIDENT` was only enforced at some call sites, not at every
   state-holding API: `BindingStore.activate()`, no-intent
   `attach_thread()`, `MutationIntentStore.set_state()` /
   `mark_submitted()`, `WakeRecovery` unconditional writes, and
   `mark_related_incidents()` omitting `OBSERVED`
2. automatic `thread/resume` after a successful response could be
   submitted again on the next scheduler iteration because
   `SUBMITTED` was not an open/unresolved state
3. `ManagedAppServerSession` was not established before the first
   `reconcile_threads()` or CLI `snapshot`, so the process-lifetime
   server-request fail-safe did not cover those paths

Also required from that review:

- missing command receipt must become a durable `INCIDENT`, not only a
  runtime error; reanchor reconcile must compare the full normalized
  currentness tuple
- mailbox ACK/intake ordering must use the turn's **first** transport
  sequence, not `last_event_seq`
- final wake `turn/start` fence must re-check semantic actor
  eligibility and matching kind/scope; on failure suspend, cancel the
  unsubmitted batch, and return messages to `ELIGIBLE`

## Read these first

```text
AGENTS.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/CAPABILITY_BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/PHASE_1_LIVE_AND_REVIEW_DEFERRED.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/PROTOCOL_EVIDENCE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/STAGE_3_CAPABILITY_BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/STAGE_4_CAPABILITY_BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/QUOTA_BLOCKED_HANDOFF.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/SESSION_CONTINUE_HANDOFF.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md
```

Then inspect only this surface:

```text
tools/codex_supervisor/
tests/codex_supervisor/
scripts/codex-app-server-observer-*.ps1
scripts/codex-managed-actor-*.ps1
scripts/codex-mailbox-*.ps1
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/
docs/research/workflow-runs/2026-08-18_codex-managed-actors/
```

Do not review or comment on unrelated dirty or historical trees
(`ha_ctse_process`, `hmasd`, `envs`, research candidates, experiment
runs). They are out of scope.

Do not require live App Server. Do not ask for Codex quota. Do not treat
missing `LIVE_CANARY_REPORT.md` / `PHASE_1_ACCEPTANCE.md` /
`STAGE_3_ACCEPTANCE.md` / `STAGE_4_ACCEPTANCE.md` as a code defect; those
files are intentionally absent until quota restore.

## Known host facts (do not contradict)

```text
Codex CLI 0.147.0
wire is JSONL-lite: no outbound "jsonrpc":"2.0"
handshake: initialize request, then initialized notification
-32001 retry only for thread/list and thread/read
mutating methods are never automatically retried
unexpected server-initiated requests terminate the owned process
clientUserMessageId exists on local TurnStartParams; not in official docs
thread/loaded/list exists in official docs and local schema
ThreadStatus types: notLoaded | idle | systemError | active
thread/memoryMode/set does not exist on this host
activation uses OPERATOR_CONFIRMED_GLOBAL_DISABLED
identity is only threadId → binding_id → actor_context_id
user authorized synthetic Stage 3/4 before Phase 1 live acceptance
live canaries are deferred, not failed
thread/start.sandbox and turn/start.sandboxPolicy are implementation
  inferences, not local-schema observations, and must not be sent
CONTEXT_REANCHOR_ACK itself increments workflow state_version by one;
  current_state_version in {ack, ack+1} is the only allowed extra bump
```

## What this corrective slice claims

Inspect whether the code actually establishes these invariants:

```text
INCIDENT is terminal at every state-holding API
  BindingStore.activate() requires verification submission_state == COMPLETED
    and refuses INCIDENT
  public attach_thread requires mutation_intent_id
  attach_thread_for_tests still refuses an unresolved thread/start INCIDENT
  MutationIntentStore transitions are CAS:
    mark_submitted: SUBMITTING → SUBMITTED
    mark_submitted_unreconciled: SUBMITTING → SUBMITTED_UNRECONCILED
    mark_uncertain: SUBMITTING → SUBMISSION_UNCERTAIN
    mark_applied: SUBMITTING → APPLIED
    mark_applied_reconciled: SUBMITTED_UNRECONCILED → APPLIED
    any INCIDENT write with rowcount=0 raises terminal error
  mark_related_incidents includes OBSERVED managed turns
    and SUBMITTED / SUBMITTED_UNRECONCILED mutation intents
  WakeRecovery writes use expected_state; INCIDENT is kept
  CommandGateway refuses a non-empty effect when the turn intent
    or wake batch is INCIDENT

automatic thread/resume is not resent after a successful response
  SUBMITTING → SUBMITTED_UNRECONCILED → APPLIED only after IDLE_LOADED
  SUBMITTED_UNRECONCILED is an open state and blocks begin()
  the next scheduler iteration only reconciles the old intent
  UNKNOWN / IDLE_NOT_LOADED after a successful response do not start
    another thread/resume

process-lifetime server-request watcher
  ObserverService.start() creates the unique ManagedAppServerSession
    immediately after the client reader starts
  reconcile_threads, snapshot, serve, canary, and managed runtime
    reuse that session
  run_snapshot / serve convert a server request during the first
    thread/list into UNEXPECTED_SERVER_REQUEST and call stop()

missing command receipt is durable
  RECEIVED/VALIDATED + no receipt → CommandValidationState.INCIDENT
    plus rejection_reason; do not re-execute
  reanchor reconcile compares the full normalized currentness tuple;
    a present-and-different receipt field does not get skipped

mailbox ordering uses first transport evidence
  MIN(normalized raw_message_seq) or MIN(stdout raw_message_seq)
  last_event_seq is not used
  a command turn that started before the wake turn is rejected
    even if it completed later

wake submit fence re-checks semantic eligibility
  require_eligible(actor) and kind/scope still match binding
  failure suspends the binding, cancels PREPARED/SUBMITTING batch,
    and returns BATCHED messages to ELIGIBLE
```

## Questions the review must answer

Answer each with evidence (file + function / table / test name). Separate
**observed fact** from **inference**. Re-answer the original 1–31, then
the new slice questions.

1. Can a model impersonate another actor by putting `actor_context_id`,
   `binding_id`, `thread_id`, `source_kind`, or `user_authority` in a
   command envelope or payload?
2. Can a thread name, preview, `agentRole`, or prose establish identity?
3. Can an adopted legacy thread create semantic authority?
4. Can an unverified Memory policy become ACTIVE?
5. Can Stage 3 start a turn without an explicit operator intent?
6. Can Stage 4 start more than one `turn/start` for one wake batch?
7. Can an active turn be steered automatically (`turn/steer`)?
8. Can an uncertain mutating submission be resent? Include persisted
   `SUBMITTING`, unresolved `INCIDENT`, and a successful but not-yet-
   loaded automatic `thread/resume`.
9. Can mailbox prose, lexical names such as `FAILED.md`, or raw child
   text become a routing key, ACL input, or semantic state transition?
10. Can EM/CM/Leaf receive automatic wake delivery in this stage?
11. Can a packet send bypass the Root↔Portfolio ACL or self-declare the
    source actor? Also: can a released semantic actor still send?
12. Can a revoked or non-ACTIVE binding receive a wake? Include direct
    `submit_batch` without a lease generation, and a semantic actor
    released after batch prepare but before `turn/start`.
13. Can a PREPARED wake batch after restart be resent, or are messages
    correctly returned to ELIGIBLE? Include the **source-resolution
    multi-message** path, not only ordinary restart.
14. Are DELIVERED messages preserved across restart? Also: is an
    `ACTIVE` batch reconciled so it cannot permanently block the next
    wake? Include concurrent watcher `INCIDENT` vs recovery writes.
15. Does `-32001` retry leak onto `thread/start`, `thread/resume`,
    `turn/start`, or `thread/loaded/list`?
16. Are forbidden event kinds (`BLOCKED`, `FAILED`, `SUCCESS`, `RETIRED`,
    `PAUSED`, `PARKED`, `RELEASED`) used as supervisor or mailbox states?
17. Does the supervisor write canonical repository artifacts, ADRs,
    science cards, or Portfolio decisions?
18. Is the runtime database kept outside the repo
    (`%LOCALAPPDATA%\HMASD\codex-supervisor`) with tests using `tmp_path`
    / repo `--basetemp` only?
19. Are protocol fields limited to the local 0.147.0 schema plus the
    recorded docs/schema distinctions in `PROTOCOL_EVIDENCE.md`?
    Confirm inferred sandbox fields are omitted, not still sent.
20. What is the strongest remaining synthetic defect, and what is only
    untestable until a live canary?

Prior corrective-slice checks, still in force:

21. Can activation succeed when checkpoint, state_version, or epoch
    changed after the ACK, and is `verified_checkpoint_id` exactly the
    acknowledged checkpoint?
22. Can `ManagedTurns.submit` or `WakeScheduler.submit_batch` send a
    persisted `SUBMITTING` row?
23. If `thread/start` or `thread/resume` returns an id and the process
    exits before attach, can a later call create or resume a second
    thread? Include no-intent `attach_thread()`.
24. If a server request arrives after a successful `turn/start` response
    and before `turn/completed`, is the session terminated and the
    turn/batch marked `INCIDENT`? **Also: can that INCIDENT later become
    COMPLETED / APPLIED / ACTIVE via activate, attach, mark_submitted,
    or recovery?**
25. After restart, is a completed `ACTIVE` batch closed, a still-running
    one left `ACTIVE`, and a missing turn made an incident?
26. Is there one session-level watcher for the whole client, including
    the first `reconcile_threads()` and CLI `snapshot`?
27. After a server-request `INCIDENT`, can `complete_activation`,
    `record_completion`, `attach_thread`, `BindingStore.activate()`,
    `observe_completion`, or `WakeRecovery` overwrite it?
28. After a thread/resume `INCIDENT`, can `begin()` create another
    mutation intent for the same client key without operator resolution?
    Can `mark_submitted()` overwrite that INCIDENT?
29. If a PREPARED batch has two messages and one source resolves, is the
    valid sibling returned to `ELIGIBLE` and selectable again?
30. If a command receipt exists and the command row is still
    `VALIDATED`, does a later ingest reconcile it to `APPLIED`? If the
    receipt is missing, is the command a durable `INCIDENT`?
31. Is timestamp-only turn ordering rejected? Does ordering use the
    turn's first sequence rather than `last_event_seq`?

New checks for this slice:

32. Does `BindingStore.activate()` itself refuse an `INCIDENT`
    verification intent, not only `ManagedRuntime.complete_activation()`?
33. Can `attach_thread` without `mutation_intent_id` bypass an unresolved
    `thread/start` INCIDENT?
34. After a successful `thread/resume` response that is not yet
    `IDLE_LOADED`, does a later scheduler iteration send another
    `thread/resume`?
35. Does `ObserverService.start()` establish the session watcher before
    the first `thread/list`? Does snapshot terminate on a server request
    during that list?
36. If a command turn started before the wake turn but completed after
    it, is mailbox ACK/intake rejected?
37. If the semantic actor is released after batch prepare and before
    `turn/start`, is the wake aborted, the binding suspended, and
    messages returned to `ELIGIBLE`?

## Required synthetic tests

These names must exist and must actually prove the claim, not only
assert that a row was stored. Prior required names remain in force;
this slice adds:

```text
test_binding_store_activate_rejects_incident_verification
test_attach_without_mutation_intent_cannot_bypass_incident
test_resume_response_then_incident_cannot_become_submitted
test_observed_turn_is_marked_incident_by_server_request
test_recovery_cannot_overwrite_incident_with_active
test_recovery_cannot_overwrite_incident_with_completed
test_command_from_incident_turn_has_no_control_effect

test_successful_resume_not_loaded_is_not_resubmitted
test_successful_resume_unknown_is_reconciled_not_restarted
test_resume_intent_becomes_applied_only_after_loaded_observation

test_server_request_during_initial_reconcile_terminates
test_server_request_during_snapshot_terminates
test_serve_establishes_session_watcher_before_thread_list

test_validated_command_without_receipt_becomes_durable_incident
test_reconciled_reanchor_receipt_requires_exact_normalized_tuple

test_mailbox_command_started_before_wake_but_completed_after_is_rejected

test_semantic_actor_released_after_batch_prepare_prevents_wake_submit
```

Prior required names from `883eb028` and `19a80529` must still exist and
still prove their claims.

Local operator evidence, not a substitute for your reading:

```text
tests/codex_supervisor  194 passed
--basetemp=C:/Projects/HMASD/.tmp_review_0818d
```

Treat that count as **UNOBSERVED** unless you independently run or see
CI. GitHub status checks are not required for this review.

## Required output shape

```text
review_kind=synthetic_control_plane_rereview
reviewed_commit=f7a5304560e52b2b78faadb6d6de4049a5b9a5f9
reviewed_range=883eb028c3cbdadf99159869ea722e8a4a6a5f6d..f7a5304560e52b2b78faadb6d6de4049a5b9a5f9
live_acceptance=absent
synthetic_disposition=CLOSED|REVISION_REQUIRED
```

Then:

- **Conclusion** — one paragraph: did this commit close the prior
  `REVISION_REQUIRED`, or what still prevents synthetic closure.
- **Findings** — each finding: severity (`Critical` / `High` /
  `Medium` / `Low` / `Note`), exact object, evidence, why it matters,
  smallest fix. Do not use `BLOCKED` / `FAILED` / `SUCCESS` as a routing
  status for this review.
- **Confirmed closures** — which prior High/Medium items are now
  actually closed in code, not only renamed.
- **Answers** — numbered 1–37 with evidence.
- **Not reviewed** — live transport, quota, and any file outside the
  listed surface.
- **Does not decide** — Phase 1 / Stage 3 / Stage 4 acceptance, Portfolio
  investment, or whether to run a live canary.

If you cannot see a file, say `UNOBSERVED` for that point. Do not invent
protocol fields, acceptance files, or live results.
