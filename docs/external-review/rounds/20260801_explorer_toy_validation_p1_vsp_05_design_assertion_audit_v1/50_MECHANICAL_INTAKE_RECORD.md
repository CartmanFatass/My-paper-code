# Mechanical intake: VSP-05 design audit

```text
workflow_id=EXPLORER-TOY-VALIDATION-2026-07-31-P1
candidate_id=CAND-VSP-05
review_round=20260801_explorer_toy_validation_p1_vsp_05_design_assertion_audit_v1
assignment_identity=round=20260801_explorer_toy_validation_p1_vsp_05_design_assertion_audit_v1|question=docs/external-review/rounds/20260801_explorer_toy_validation_p1_vsp_05_design_assertion_audit_v1/20_PRO_OPEN_QUESTION.md
agentify_source_commit=3a69613a4363091014733123e3f0cea82c5b76e5
hmasd_workflow_commit=d4dba504860e1492b95bda3c7d9d55aba4d467f5
package_commit=59def3c
operation_id=9ae0426e-5ea2-450a-9155-4c56191ec29d
conversation_id=6a6cd2d9-321c-83e8-a046-7062de12c4b7
conversation_url=https://chatgpt.com/c/6a6cd2d9-321c-83e8-a046-7062de12c4b7
model=Pro
transport_backend=agentify
status=COMPLETE
terminal_state=NATURAL_COMPLETION_VERIFIED
send_count=1
send_action_count=1
click_count=1
clicked_controls=[]
assistant_message_id=f4a2e405-44a3-4cf2-912c-73faeaabc56f
user_message_id=656ad706-729b-4bfa-acf2-9dd8b413d351
snapshot_count=2
snapshot_gap_ms=3083
answer_now=false
continue=false
retry=false
stop=false
compute_authorized=false
scientific_iteration_cost=zero
```

## Exact result

```text
response=ADVISORY_REFINEMENT_REQUIRED_WITH_ONE_EXACT_GAP
exact_gap=The pre-code Stage-A gate is not frozen: its 23 trace-family labels and separate M01â€“M16 attribution cases are not reconciled into one exact finite trace matrix specifying per row the initial FSM, ledger and epoch state, observation and event order, expected gate/residual/handoff actions and counts, terminal state, and fixed H and K required for an implementable O(H*K) audit.
raw_archive=docs/external-review/rounds/20260801_explorer_toy_validation_p1_vsp_05_design_assertion_audit_v1/21_PRO_OPEN_RAW.md
raw_bytes=438
raw_sha256=d60498097d0e2ecf94c491c2d58a9ecfe93423dd07215c705cab7407b98e8d89
```

The candidate remains active for one exact-gap refinement only. VAP and VSP-02
remain frozen and archived; no comparison, code, compute or project-state
action is authorized by this intake.

```text
next_boundary=EXPLORER_VSP05_EXACT_REFINEMENT_PACKET
```
