# Workflow defect queue

```text
owner=workflow_design_manager
ordering=receipt_order_fifo
states=QUEUED|ACTIVE|CLOSED
active_limit=1
report_authority=advisory_only
hash_identity=forbidden
```

Archive each typed `WORKFLOW_DEFECT_REPORT` here before evaluation. One item is
`ACTIVE`; later reports stay `QUEUED`. WDM independently reproduces the defect
and either restores the accepted stable contract, closes it as not a defect, or
moves a material policy/authority change to a user-confirmed plan. Retryable
tool failure remains a checklist item, not a new mechanism or terminal state.

| received_order | report_id | source_role | observed_contract | status | disposition |
|---:|---|---|---|---|---|
