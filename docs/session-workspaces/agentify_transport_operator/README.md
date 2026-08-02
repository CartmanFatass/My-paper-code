# Agentify Transport Operator workspace

Requesters send `AGENTIFY_REVIEW_REQUEST`; the task returns
`AGENTIFY_REVIEW_RESULT`. Raw responses use
`temp/sessions/agentify_transport_operator/<request_id>/response.md`; requesters
name the exact provider and `stable_key` and own archival and interpretation.
The task loads `hmasd-agentify-transport`; no science or project state is stored
here.
