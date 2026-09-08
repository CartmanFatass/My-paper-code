# Independent Transport migration — 2026-09-07

Authority: the owner requested a separate Luna/high Pro Transport task, using the previous
singleton implementation, and explicitly required Root/subagent/cross-session return design.
The owner also requested a stable dispatch skill to prevent idle direction slots.

## Responsibilities and endpoint

Transport task: `01a07e52-f085-76a0-886a-4127f490421f`, title `HMASD Pro Transport`,
model `gpt-5.6-luna`, effort `high`, local saved HMASD project on main. Creation returned that
actual task ID; this is not a desired configuration awaiting task creation. Root remains
`01a07249-b095-7821-8ce2-e9c32ba85267` at its existing model/effort. Provider remains verified
6 Pro; no conversation-policy reset, scheduler or research invocation follows.

Root owns direction execution, experiment observation, integration and native forwarding.
Transport owns exact Pro Send/reconciliation/observation/archive and parent receipts. The
maintained route and wake/recovery procedure are in ROOT_OPERATIONS.md, "Independent Transport
and native return routing". Normal native routing is DM/CM → Root → Transport → Root → DM/CM;
an already-authorized child direct dispatch preserves Root as parent. Portfolio's own requests
keep Portfolio as parent. Every app message omits model/thinking; the endpoint setting is
recorded in handoff metadata, not copied into a message override.

## Existing implementation reused

The independent singleton configuration and Author dispatch procedure before `2a5cadd41`
supplied the prior implementation reference. Retain the current, improved provider bindings,
shared direction branches, exact archive/outbox helpers and no-scheduler behavior. Do not
restore the old fresh-conversation policy, old task ID or xhigh effort.

The renderer and new-request validator now bind the current independent high endpoint.
The existing `execution_thread_id` already supports a migrated executor independently of
immutable `operator_thread_id`. Receipt helpers already return to the explicit parent and
preserve attempted delivery evidence. No replacement registry or retry machinery is added.

## Cutover and exact recovery rules

1. Root released Pro browser ownership by app handover to the new task and stated it would
   continue research/comparison work without Pro browser operations. Transport confirmed the
   named VSP02/VSP03/UCOPE archive paths and zero in-app browser tabs. That check establishes
   browser release, not completeness of the entire registry or scientific intake.
2. Root's handover and subsequent return facts report VSP02/VSP03/UCOPE complete, and FSD
   final intake `c08e921d7`. The registry still contained stale pending/tab facts for FSD,
   UCOPE, VSP02/VSP03, DISH and VSPC1. Transport has an explicit, no-Send reconciliation task
   for these named rows; it resolves them against actual archives/receipts with Root, preserving
   contrary evidence. A registry label alone does not justify another Send or new observation.
3. For accepted/unknown unfinished work, compare the original HANDOFF at its fixed commit with
   the persisted request ID, prompt/TASK, provider/message identity, source and parent. Preserve
   that original HANDOFF and operator metadata. Record the new actual `execution_thread_id`
   and handover evidence only on unfinished records, then observe/reconcile the same request.
   Do not validate an accepted historical request as if it were a new high-endpoint request.
4. For an explicitly authorized but unsent legacy handoff, retain the original immutable input
   and create a request-scoped effective transport JSON beside the existing operational packet.
   Copy the original `transport_request` exactly, then change only `operator_thread_id` to the
   new endpoint, `operator_model` to `gpt-5.6-luna`, `operator_thinking` to `high`,
   `dispatch_mode` to `REUSE_SINGLETON`, and `operator_reuse_required` to `true`. Remove any
   old `owner_execution_instruction` that solely selects the obsolete CALLER_DIRECT executor.
   Compare every other field against the original, including source/parent, prompt/path,
   companion text, TASK URL/SHA, delivery branch/path and provider requirements. Record the
   original HANDOFF commit/path and this owner migration as the routing-override evidence.
   Pass that effective transport-request JSON directly to `validate_request.py` (not an outer
   envelope); use existing materialization with that validated object. Do not regenerate TASK,
   alter scientific content or infer an absent Send authorization. Root sends its exact
   operational file/reference to Transport once; app acceptance is not provider acceptance.
5. Completed LOCAL/SENT receipts and already-applied intakes remain completed history. Do not
   assign them a new executor and restage a receipt. Preserve every attempted/uncertain outbox;
   resolve uncertain delivery from authoritative state, never from elapsed time. A genuinely
   unfinished request completing under Transport sends to its unchanged parent, including Root
   for native authors, using the existing outbox key and single-attempt procedure.

## Checks and activation

The focused renderer/transport suite passes 118 tests, including a Root-authored high-endpoint
dispatch and native-author completion/blocker receipts under migrated execution ownership.
The latter preserve original operator/source/parent fields and cannot stage another receipt
after recorded delivery. Existing same-task and ambiguous-delivery tests remain in place.
Independent routing review identified and corrected a stale Root instruction and placed the
CM-comparison intercept before generic coding dispatch. New requests do not require a live
Pro probe to qualify migration; no extra scientific request is authorized for testing.

`hmasd-loop-dispatch` now defines Root's explicit next-action trigger at goal-turn entry,
commands, native/Transport returns and before blocking waits. It is a skill procedure, not a
claimed runtime event subscription. Actual dispatch/return evidence remains the operational
check; queued commands and completed agents cannot be counted as advancing directions.
