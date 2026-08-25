# VNFC-B3 External Pro v3 submission forensic correction

Owner: `direction:variable-n-fleet-churn` Explorer Manager  
Treatment: `VNFC-B3-SCALABLE-REWARD-SOURCE-CUT-v1`  
Revision: `SP-RDA-MATH-CLOSURE-20260812-03`  
Final transport state: `NATURAL_COMPLETION_VERIFIED_REVISION_REQUIRED`  

## Owner conclusion

The repaired-runtime ChatGPT External Pro mathematical-closure request crossed
the provider send boundary exactly once. The registered transport child's
subsequent `UNSENT` summary was false on that fact. Later same-operation,
observation-only recovery naturally verified the response with literal
`VERDICT: REVISION_REQUIRED`. The complete raw response is now durably archived
in requester-local `results.json`; the request must never be sent again.

This correction changes no scientific definition, comparator, estimand, gate,
or claim ceiling in v3. It corrects only the transport/intake record. The current
`results.json` and both earlier error archives are preserved unchanged.

## Frozen request identity

- Requester:
  `temp/sessions/agentify_transport_operator/independent_research_explorer/variable_n_fleet_churn_b3_math_closure_v3`
- Existing conversation:
  `https://chatgpt.com/c/6a7c399a-8834-83e8-8f3d-ef967d06589d`
- Provider/model: `chatgpt` / visible `Pro`
- Frozen question digest:
  `d9c8a3fc0cbefbc284e2149c696c9d0e201e4d5e4037593a140820f6cd2507f3`
- Stable key: `vnfc_b3_math_closure_v3_final`
- Idempotency key: `vnfc_b3_math_closure_v3_final-001`
- Operation ID: `7626c227-870a-4290-b407-4bf8cdf8c550`
- Provider user-message ID:
  `87f7a729-87d2-41d7-82bc-78a8e9c1f6e1`

## Durable strict-operation evidence

The persisted strict-operation record in
`C:/Users/fires/.agentify-desktop/review-transport.json` contains:

| Field | Value |
|---|---|
| status | `BLOCKED` |
| terminal state | `SUBMITTED_UNVERIFIED` |
| send count | `1` |
| send-action count | `1` |
| click count | `1` |
| failure stage | `send_occurred_or_uncertain` |
| prepared | `2026-08-12T07:47:49.3160000-07:00` |
| send action | `2026-08-12T07:55:56.3660000-07:00` |
| submitted | `2026-08-12T07:55:56.9660000-07:00` |
| final update | `2026-08-12T08:07:45.5090000-07:00` |
| error | `Session with given id not found.` |

The four baseline message IDs were
`d98ddb5b-bca7-4bc8-aa4b-a6beff897d2b`,
`0df936e0-daa8-496a-8038-6f4f04849cfd`,
`cb66f2eb-51ee-4ff5-9747-cffb8d64cf87`, and
`e1ce69dd-830f-46e9-b5e6-2a88dcf19523`.

The strict controller persists `sendActionCount=1` in its send-action callback
and then persists `sendCount=1`, the exact conversation identity, visible model
evidence, and `userMessageId` in its submission callback. Its failure handler
classifies any later observation/session exception with those receipts as
`SUBMITTED_UNVERIFIED` at `send_occurred_or_uncertain`. The recorded sequence is
therefore preparation -> one send action -> durable submission -> failed response
observation. It is not a pre-send stall.

## Superseded child statement

The preserved terminal archive
`temp/sessions/agentify_transport_operator/independent_research_explorer/variable_n_fleet_churn_b3_math_closure_v3/results.json`
states that no provider user turn committed. That statement conflicts with the
strict-operation record above and is superseded on send-boundary facts. It remains
preserved so the audit trail shows why the original owner intake was corrected.

The earlier archives `results_prior_error.json` and
`results_registry-mismatch-recovery.json` concern genuinely pre-submission
attempts. Their facts are unchanged and they do not negate or duplicate the later
committed operation.

## Only permitted recovery

No fresh operation or provider send is allowed. After Root relays a new
Agentify-idle confirmation following shared session repair, transport may reopen
only the exact saved conversation and invoke the same strict request with:

- unchanged stable key and idempotency key;
- unchanged prompt bytes/digest, conversation URL/ID, visible Pro requirement,
  and timeout;
- `verifyExisting=true`;
- the persisted user-message ID as the response-observation anchor.

That branch is observation-only: it requires the existing operation and message
ID and is intentionally denied send, input, and response-control capabilities.
The disposable tab closes only after the observation call returns and its terminal
archive is durable. Any inability to observe returns as an observation error; it
never authorizes resend.

## Scientific and production consequence

The exact v3 composite received `REVISION_REQUIRED` and is superseded by
prospective revision `SP-RDA-MATH-CLOSURE-20260812-04`. Full scientific intake
is recorded in `VNFC_B3_V3_EXTERNAL_PRO_DECISION_INTAKE.md`. V3 cannot be relayed
to CM or resent. V4 remains production-held pending a same-conversation literal
`CLOSED` plus owner intake and renewed CM conformance/technical acceptance.

## Observation-only recovery attempt 1

Root later relayed a fresh idle runtime and authorized one exact
`verifyExisting=true` call. The unchanged strict request entered the
`review_query` route, then returned `review_conversation_identity_mismatch` after
116 ms at live identity validation. It did not reach `observing_existing`; no
response identity, assistant message, raw response, or verdict was returned.

This call was capability-bounded and performed no send, input, control, retry,
new operation, or provider turn. The durable operation therefore remains
`SUBMITTED_UNVERIFIED` with the same one-send receipt and provider user-message
ID. The observation error is archived at:

`temp/sessions/agentify_transport_operator/independent_research_explorer/variable_n_fleet_churn_b3_math_closure_v3/results.json`

The child terminal that falsely called the submitted request unsent is now
preserved as `results_client_stall.json`; the two earlier pre-submission error
archives remain preserved. Both disposable tabs associated with the failed
observation/reconciliation were closed after terminal diagnosis, and the final
runtime contained only the protected default tab with zero active/inflight work.

No additional observation call is authorized by this record. A later recovery,
if Root authorizes one after repairing live DOM identity reconciliation, must
remain observation-only on this same operation and message ID. Resend is never
permitted.

## Observation-only recovery attempt 2

Following a repair of the fresh-target identity race, Root authorized one new
same-operation `verifyExisting=true` call on an idle runtime. The strict observer
advanced past the former conversation-identity mismatch, then returned
`review_user_message_identity_unreadable` after 3.557 seconds while looking for
the persisted provider user-message ID.

No structured message list, user or assistant content, DOM snapshot, response
identity, or diagnostic metadata accompanied the predicate. It is therefore
indeterminate whether the conversation content rendered without readable IDs or
failed to load. No response or literal verdict can be claimed from this terminal.

No send-capable action occurred. The call performed no send, input, response
control, retry, new operation, or new provider turn. The current error is archived
as `results.json`, and the prior observation error is preserved as
`results_identity_race_recovery.json`. Generated tabs were closed after terminal
diagnosis; the runtime returned to protected-default-only and idle. The durable
exact-one submission receipt remains authoritative and v3 remains
`SUBMITTED_UNVERIFIED`.

## Final observation-only natural completion

After a strict unique full-prompt content-rebind repair, Root authorized one last
same-operation observation-only recovery. It verified the exact existing user
turn and completed naturally with assistant message
`f81d8302-3907-4adc-a379-c2c02c358ae3`, response digest
`f268d9aee000c8cc08d7fa4304a60931a5cf538c064349051f94ed9504838563`,
and literal `VERDICT: REVISION_REQUIRED`. All response controls were inactive and
unused. Both disposable tabs closed and Agentify returned default-only and idle.

The complete 23,218-character raw response is in the `response` field of
`temp/sessions/agentify_transport_operator/independent_research_explorer/variable_n_fleet_churn_b3_math_closure_v3/results.json`, and its UTF-8 digest matches
the receipt. `results_metadata_only.json` preserves the earlier metadata-only
archive. Earlier statements in this document that no response or verdict had
been observed are historical and superseded by this terminal.
