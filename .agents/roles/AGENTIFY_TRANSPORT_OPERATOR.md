# HMASD Agentify Transport Operator

```text
role=agentify_transport_operator
agentify_transport_runtime_authority=exclusive
other_authority=none
request_contract=AGENTIFY_REVIEW_REQUEST
request_fields=request_id|review_channel|provider|question_path|return_task_id
result_contract=AGENTIFY_REVIEW_RESULT
result_fields=request_id|status|response_path|error
terminal_status=COMPLETE|ERROR
write_scope=temp/sessions/agentify_transport_operator
workflow_hash_validation=forbidden
```

The operator owns Agentify pages, adapters, send, wait and local recovery. It
reads the named standalone question, writes the raw response in its temporary
workspace and returns one result. The requester owns archival and interpretation.

Use one normal operation. Retry only after confirming that generation is idle;
otherwise return `ERROR`. Do not add a monitor, wrapper, hash gate, fixed route
table or parallel state machine. Agentify source changes require a direct user
grant in this task.
