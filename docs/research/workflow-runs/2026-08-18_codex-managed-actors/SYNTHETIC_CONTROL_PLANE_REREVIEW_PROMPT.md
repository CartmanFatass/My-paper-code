# Rereview Prompt: HMASD Codex Supervisor Synthetic Control Plane

Copy everything below the line to another model that can read
`origin/aggressive`. This prompt is for a **synthetic code/architecture
review**. It is not Phase 1, Stage 3, or Stage 4 acceptance. It does not
authorize live App Server work.

```text
document_kind=synthetic_control_plane_rereview_prompt
supersedes=SYNTHETIC_CONTROL_PLANE_REVIEW_PROMPT.md
prior_reviewed_commit=0520df87ee2dd1dd70c1bdade34889980c4c7a44
prior_reviewed_range=12236b26583c7e389fe4cc5026e0437760d34b3e..0520df87ee2dd1dd70c1bdade34889980c4c7a44
```

The prior rereview of `0520df87` returned `REVISION_REQUIRED`. This
prompt reviews the corrective commit that claims to close those defects.

---

## Assignment

Review the HMASD Codex App Server supervisor on branch `aggressive` at
commit `19a80529fa9b0ff7327d704cef92fe2fd065ae2e`.

Repository: the HMASD git remote the operator pointed you at.
Branch: `aggressive`.
Review range:

```text
0520df87ee2dd1dd70c1bdade34889980c4c7a44..19a80529fa9b0ff7327d704cef92fe2fd065ae2e
```

Parent of this corrective slice:

```text
0520df87  fix: close synthetic supervisor review defects
```

This is operational control-plane infrastructure, not a research
direction and not Portfolio work.

## Prior rereview that this commit must close

`0520df87` was a substantial improvement but remained `REVISION_REQUIRED`
for four High defects and several Medium leftovers:

1. activation could promote a stale verification ACK over a newer
   semantic tuple
2. persisted `SUBMITTING` remained sendable; thread attach was not in
   the same durable apply as the mutation intent
3. server-request fail-safe ended when the `turn/start` RPC response
   arrived, not for the generated turn's lifetime
4. `ACTIVE` wake batches were never completed during restart
   reconciliation and could occupy the only open-batch slot forever

Also required from that review:

- automatic wake submit must require lease generation
- command evidence must be the exact `item/completed` raw record
- packet send must revalidate semantic eligibility
- source resolution during `SUBMITTING`/`ACTIVE` must not cancel a
  message that later reconciliation needs
- omit inferred `thread/start.sandbox` and `turn/start.sandboxPolicy`
- reject mailbox ACK/intake when command/wake ordering cannot be proven
- do not rewrite the historical handoff; supersede it

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
```

## What this corrective slice claims

Inspect whether the code actually establishes these invariants:

```text
activation currentness
  current snapshot tuple
  == verification intent expected tuple
  == command expected tuple
  == reanchor receipt tuple
  for (checkpoint_id, state_version, epoch_id, epoch_revision)
  verified_* columns come from the receipt, not a later fetch
  UPDATE ... WHERE binding_state = 'VERIFICATION_REQUIRED'

SUBMITTING is reconciliation-only
  public submit / submit_batch accept PREPARED only
  atomically claim PREPARED → SUBMITTING in the same invocation
  do not reload a persisted SUBMITTING row and send again
  thread/start and thread/resume stay open until attach
  mark mutation APPLIED in the same SQLite transaction as attach

session-lifetime server-request watcher
  one watcher per App Server client, not one consumer per RPC
  watcher remains active after turn/start response
  on server request: persist, map to turn/batch, INCIDENT, terminate

ACTIVE wake recovery
  completed/interrupted/failed turn closes the batch
  still-running turn stays ACTIVE
  missing turn becomes a reviewable incident, not COMPLETED
  a recovered completed batch unblocks the next wake

automatic wake fencing
  submit_batch requires lease_generation
  revoked / non-ACTIVE binding cannot submit

command evidence
  raw.method == item/completed
  raw.item_id present
  payload item id/type match
  snapshot.item_id == raw.item_id
  no fallback lookup for command ingestion

semantic eligibility
  packet send calls require_eligible on source and target
  released actor suspends the managed binding

source resolve vs in-flight wake
  PREPARED batch may cancel
  SUBMITTING / SUBMISSION_UNCERTAIN / ACTIVE retain the attempt
  record source_resolved_after_submission instead of CANCELLED

mailbox ordering
  use event/raw sequence, not optional timestamps
  if ordering cannot be proven, reject ACK/intake
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
   `SUBMITTING` as part of this answer, not only `SUBMISSION_UNCERTAIN`.
9. Can mailbox prose, lexical names such as `FAILED.md`, or raw child
   text become a routing key, ACL input, or semantic state transition?
10. Can EM/CM/Leaf receive automatic wake delivery in this stage?
11. Can a packet send bypass the Root↔Portfolio ACL or self-declare the
    source actor? Also: can a released semantic actor still send?
12. Can a revoked or non-ACTIVE binding receive a wake? Include direct
    `submit_batch` without a lease generation.
13. Can a PREPARED wake batch after restart be resent, or are messages
    correctly returned to ELIGIBLE?
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

Corrective-slice checks:

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
    turn/batch marked `INCIDENT`?
25. After restart, is a completed `ACTIVE` batch closed, a still-running
    one left `ACTIVE`, and a missing turn made an incident?
26. Is there one session-level watcher, or can concurrent RPC wrappers
    consume the wrong server request?

## Required synthetic tests

These names must exist and must actually prove the claim, not only
assert that a row was stored:

```text
test_activation_rejects_checkpoint_changed_after_ack
test_activation_rejects_state_version_changed_after_ack
test_activation_rejects_epoch_changed_after_ack
test_verified_checkpoint_is_exactly_the_acknowledged_checkpoint

test_managed_turn_submit_rejects_persisted_submitting
test_wake_submit_rejects_persisted_submitting
test_thread_start_response_attach_is_one_durable_apply
test_thread_resume_response_attach_is_one_durable_apply

test_server_request_after_turn_start_response_terminates
test_server_request_during_active_wake_marks_batch_incident
test_one_session_level_watcher_handles_concurrent_rpc_responses

test_active_batch_completed_during_restart_is_reconciled
test_active_batch_still_running_remains_active
test_active_batch_missing_turn_becomes_incident
test_active_batch_recovery_unblocks_next_wake

test_automatic_submit_requires_lease_generation
test_binding_revoked_after_batch_prepare_prevents_submission

test_command_evidence_requires_exact_item_completed_method
test_command_evidence_requires_exact_item_id

test_released_semantic_actor_cannot_send_managed_packet

test_source_resolution_during_submitting_batch_preserves_reconciliation

test_mailbox_command_with_unknown_ordering_is_rejected
```

Local operator evidence, not a substitute for your reading:

```text
tests/codex_supervisor  167 passed
--basetemp=C:/Projects/HMASD/.tmp_review_0818d
```

Treat that count as **UNOBSERVED** unless you independently run or see
CI. GitHub status checks are not required for this review.

## Required output shape

```text
review_kind=synthetic_control_plane_rereview
reviewed_commit=19a80529fa9b0ff7327d704cef92fe2fd065ae2e
reviewed_range=0520df87ee2dd1dd70c1bdade34889980c4c7a44..19a80529fa9b0ff7327d704cef92fe2fd065ae2e
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
- **Answers** — numbered 1–26 with evidence.
- **Not reviewed** — live transport, quota, and any file outside the
  listed surface.
- **Does not decide** — Phase 1 / Stage 3 / Stage 4 acceptance, Portfolio
  investment, or whether to run a live canary.

If you cannot see a file, say `UNOBSERVED` for that point. Do not invent
protocol fields, acceptance files, or live results.
