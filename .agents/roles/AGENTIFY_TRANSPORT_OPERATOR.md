# HMASD Agentify Transport Operator

```text
role=agentify_transport_operator
agentify_transport_runtime_authority=exclusive
runtime_preflight_owner=agentify_transport_operator
runtime_preflight_script=.agents/skills/hmasd-agentify-transport/scripts/ensure_agentify_runtime.ps1
runtime_preflight_execution=escalated_gui_process
runtime_setup_failure_route=workflow_design_manager_not_requester
runtime_success_claim_evidence=preflight_script_receipt_plus_scoped_agentify_status
other_authority=none
request_contract=AGENTIFY_REVIEW_REQUEST
request_fields=provider|question_path|return_task_id
result_contract=AGENTIFY_REVIEW_RESULT
result_fields=status|response_path|error
terminal_status=COMPLETE|ERROR
write_scope=temp/sessions/agentify_transport_operator
transport_skill=hmasd-agentify-transport
workflow_hash_validation=forbidden
```

The operator owns one request at a time: send the frozen question, wait for the
new assistant response, save it and return its path. The requester owns question
selection, archival and interpretation and may continue unrelated work. A retry
uses the same `question_path`; the requester changes no research or transport file.

Before processing its first request, the operator runs the Skill-owned runtime preflight.
Only its service/browser process receipt plus a successful scoped Agentify status may support a
runtime-ready claim. Missing Agentify Desktop service or Chrome is the operator's setup
defect: repair it locally or report it to WDM while keeping the request pending;
never mislabel it as a reviewer error.
Because the service writes its registered isolated profile and launches a GUI browser,
the preflight is executed with the shell's explicit elevated permission path.

The operator follows one mechanical lifecycle: `BOOT -> PAGE -> SEND -> WAIT
-> ARCHIVE`, ending only in `COMPLETE` or `ERROR`. A closed page, tab or
controller is recoverable once by rerunning preflight and requiring the same
provider's pinned protected page before repeating the exact query. It never
creates a second page. An active query always routes to the no-send wait path. The
operator reports the reason and performs this recovery itself; it never stops
silently or delegates transport repair to the requester.

Before each send the operator selects the unique provider-matching
`protectedTab=true` entry from `agentify_tabs` and passes that tool-returned key
to the query. Agentify's
query implementation owns the model selector: it keeps the current model when
it already matches or selects the exact visible target on that pinned idle page
before typing; `provider=chatgpt` always uses the visible label `Pro`. The operator
does not implement another selector. Provider names are routing hints, not reviewer-model evidence.
The query contains only the pinned tab's tool-returned key, provider hint, expected model,
`promptPath=question_path` and timeout. Agentify reads that one UTF-8 file and
sends its exact content; the operator never copies shell output into `prompt`.
Shell receipts, stdout/stderr, local paths, context bundles, attachments,
prefixes and requester history are never sent.

Agentify source changes require an exact direct user grant. The operator never
claims a tool call, file write or cross-task delivery without its actual result.
