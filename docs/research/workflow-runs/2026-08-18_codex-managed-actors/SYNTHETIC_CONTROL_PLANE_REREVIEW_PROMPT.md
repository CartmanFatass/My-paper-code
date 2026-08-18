# Rereview Prompt: HMASD Codex Supervisor Synthetic Control Plane

Copy everything below the line to another model that can read
`origin/aggressive`. This prompt is for a **synthetic code/architecture
review**. It is not Phase 1, Stage 3, or Stage 4 acceptance. It does not
authorize live App Server work.

```text
document_kind=synthetic_control_plane_rereview_prompt
supersedes=SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md
prior_reviewed_commit=19a80529fa9b0ff7327d704cef92fe2fd065ae2e
prior_reviewed_range=0520df87ee2dd1dd70c1bdade34889980c4c7a44..19a80529fa9b0ff7327d704cef92fe2fd065ae2e
```

The prior rereview of `19a80529` returned `REVISION_REQUIRED`. This
prompt reviews the corrective commit that claims to close those defects.

---

## Assignment

Review the HMASD Codex App Server supervisor on branch `aggressive` at
commit `883eb028c3cbdadf99159869ea722e8a4a6a5f6d`.

Repository: the HMASD git remote the operator pointed you at.
Branch: `aggressive`.
Review range:

```text
19a80529fa9b0ff7327d704cef92fe2fd065ae2e..883eb028c3cbdadf99159869ea722e8a4a6a5f6d
```

Parent of this corrective slice:

```text
19a80529  fix: close remaining synthetic supervisor rereview defects
```

`2d7008f3` only pinned the previous rereview prompt; treat it as
documentation, not a science-bearing change.

This is operational control-plane infrastructure, not a research
direction and not Portfolio work.

## Prior rereview that this commit must close

`19a80529` closed the previous High set (activation currentness,
SUBMITTING non-resend, attach+APPLIED same tx, session-lifetime
watcher subject, ACTIVE wake recovery). It remained
`REVISION_REQUIRED` for two High defects and several Medium leftovers:

1. server-request `INCIDENT` was not a terminal state: completion,
   activation, attach, and `MutationIntentStore.begin()` could overwrite
   or re-open it
2. a PREPARED multi-message wake batch cancelled the whole batch when
   one source resolved, leaving valid siblings permanently `BATCHED`

Also required from that review:

- record `source_resolved_after_submission` for `SUBMISSION_UNCERTAIN`
  and `ACTIVE` messages, not only `SUBMITTING` / `BATCHED`
- one server-request consumer for the whole App Server client, including
  `ObserverService.serve()` / canary
- mailbox ACK/intake ordering must use event/raw sequence only; reject
  timestamp-only evidence
- duplicate ingest must reconcile `VALIDATED` + existing receipt to
  `APPLIED`; do not leave a crash window that permanently blocks
  activation
- `verify_and_activate()` must not pick a non-`item/completed
  agentMessage` raw row

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
INCIDENT is terminal without operator recovery
  record_completion allows only SUBMITTED / OBSERVED → COMPLETED
  complete_activation refuses INCIDENT
  attach_thread applies mutation only WHERE state='SUBMITTING'
    and rolls back the binding attach if rowcount != 1
  observe_completion allows only ACTIVE → COMPLETED
  MutationIntentStore.begin() refuses an unresolved INCIDENT
    for the same method+client_key
  operator resolve_incident is the only path that reopens the client key

PREPARED multi-message source resolution
  one invalid source cancels the PREPARED batch in one SQLite tx
  invalid messages → CANCELLED_SOURCE_RESOLVED
  still-valid siblings → ELIGIBLE, batched_at cleared
  cancelled batch contains no BATCHED messages

source_resolved_after_submission
  SUBMITTING / SUBMITTED / SUBMISSION_UNCERTAIN / ACTIVE
  retain the delivery attempt
  flag is recorded even when the message is already
    SUBMISSION_UNCERTAIN or DELIVERED_TO_TURN

one server-request consumer
  ObserverService._watch_server_requests does not
    client.server_requests.get()
  it waits on ManagedAppServerSession incident
  persist_server_request does not steal stdout transport_seq
    from ObserverService inbound recording

mailbox ordering
  last_event_seq or raw_message_seq only
  timestamp-only evidence is rejected

command crash reconciliation
  existing RECEIVED/VALIDATED + matching receipt
    → re-check tuple → APPLIED
  RECEIVED/VALIDATED + missing receipt
    → explicit incident, do not re-execute the semantic effect

verify_and_activate convenience lookup
  only exact item/completed agentMessage evidence
  never the latest raw row (usually turn/completed)
```

## Questions the review must answer

Answer each with evidence (file + function / table / test name). Separate
**observed fact** from **inference**. Re-answer the original 1–20, then
the corrective-slice questions.

1. Can a model impersonate another actor by putting `actor_context_id`,
   `binding_id`, `thread_id`, `source_kind`, or `user_authority` in a
   command envelope or payload?
2. Can a thread name, preview, `agentRole`, or prose establish identity?
3. Can an adopted legacy thread create semantic authority?
4. Can an unverified Memory policy become ACTIVE?
5. Can Stage 3 start a turn without an explicit operator intent?
6. Can Stage 4 start more than one `turn/start` for one wake batch?
7. Can an active turn be steered automatically (`turn/steer`)?
8. Can an uncertain mutating submission be resent? Treat persisted
   `SUBMITTING` **and** unresolved `INCIDENT` as part of this answer.
9. Can mailbox prose, lexical names such as `FAILED.md`, or raw child
   text become a routing key, ACL input, or semantic state transition?
10. Can EM/CM/Leaf receive automatic wake delivery in this stage?
11. Can a packet send bypass the Root↔Portfolio ACL or self-declare the
    source actor? Also: can a released semantic actor still send?
12. Can a revoked or non-ACTIVE binding receive a wake? Include direct
    `submit_batch` without a lease generation.
13. Can a PREPARED wake batch after restart be resent, or are messages
    correctly returned to ELIGIBLE? Include the **source-resolution
    multi-message** path, not only ordinary restart.
14. Are DELIVERED messages preserved across restart? Also: is an
    `ACTIVE` batch reconciled so it cannot permanently block the next
    wake?
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

Corrective-slice checks from the previous rereview, still in force:

21. Can activation succeed when checkpoint, state_version, or epoch
    changed after the ACK, and is `verified_checkpoint_id` exactly the
    acknowledged checkpoint?
22. Can `ManagedTurns.submit` or `WakeScheduler.submit_batch` send a
    persisted `SUBMITTING` row?
23. If `thread/start` or `thread/resume` returns an id and the process
    exits before attach, can a later call create or resume a second
    thread?
24. If a server request arrives after a successful `turn/start` response
    and before `turn/completed`, is the session terminated and the
    turn/batch marked `INCIDENT`? **Also: can that INCIDENT later become
    COMPLETED / APPLIED / ACTIVE?**
25. After restart, is a completed `ACTIVE` batch closed, a still-running
    one left `ACTIVE`, and a missing turn made an incident?
26. Is there one session-level watcher for the whole client, including
    `ObserverService`, or can ObserverService still `get()` the queue?

New checks for this slice:

27. After a server-request `INCIDENT`, can `complete_activation`,
    `record_completion`, `attach_thread`, or `observe_completion`
    overwrite it?
28. After a thread/resume `INCIDENT`, can `begin()` create another
    mutation intent for the same client key without operator resolution?
29. If a PREPARED batch has two messages and one source resolves, is the
    valid sibling returned to `ELIGIBLE` and selectable again?
30. If a command receipt exists and the command row is still
    `VALIDATED`, does a later ingest reconcile it to `APPLIED` instead
    of returning `DUPLICATE` and leaving activation blocked?
31. Is timestamp-only turn ordering rejected for mailbox ACK/intake?

## Required synthetic tests

These names must exist and must actually prove the claim, not only
assert that a row was stored. Prior required names remain in force;
this slice adds:

```text
test_server_request_incident_cannot_be_completed_or_activated
test_thread_start_incident_cannot_be_overwritten_by_attach
test_thread_resume_incident_requires_operator_resolution
test_wake_incident_cannot_be_overwritten_by_completion

test_prepared_batch_source_resolution_returns_valid_siblings_to_eligible
test_cancelled_batch_contains_no_batched_messages

test_observer_and_managed_runtime_share_one_server_request_consumer
test_mailbox_command_rejects_timestamp_only_ordering
test_reanchor_receipt_crash_before_command_applied_is_reconciled
```

Prior required names from `19a80529` must still exist and still prove
their claims.

Local operator evidence, not a substitute for your reading:

```text
tests/codex_supervisor  177 passed
--basetemp=C:/Projects/HMASD/.tmp_review_final3
```

Treat that count as **UNOBSERVED** unless you independently run or see
CI. GitHub status checks are not required for this review.

## Required output shape

```text
review_kind=synthetic_control_plane_rereview
reviewed_commit=883eb028c3cbdadf99159869ea722e8a4a6a5f6d
reviewed_range=19a80529fa9b0ff7327d704cef92fe2fd065ae2e..883eb028c3cbdadf99159869ea722e8a4a6a5f6d
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
- **Answers** — numbered 1–31 with evidence.
- **Not reviewed** — live transport, quota, and any file outside the
  listed surface.
- **Does not decide** — Phase 1 / Stage 3 / Stage 4 acceptance, Portfolio
  investment, or whether to run a live canary.

If you cannot see a file, say `UNOBSERVED` for that point. Do not invent
protocol fields, acceptance files, or live results.
