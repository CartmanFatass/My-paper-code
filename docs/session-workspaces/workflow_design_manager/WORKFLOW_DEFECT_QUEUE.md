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
| 1 | FIRST_BINDING_BOOTSTRAP_DEADLOCK | independent_research_explorer | `f4b12303ad3a4b6fdd2f43445ade0b881c52d835` | CLOSED | Replaced the deadlock with one strict provider-parameterized lifecycle: ChatGPT first binding captures the conversation created by the single raw-question send; Gemini uses the same interface on its bound page; local identity never enters `RAW_QUESTION`. Agentify pinned to `e9f636740bf94d7db260c8817554904cdcb68870`; focused and contract tests passed. |
| 2 | GENERAL_PLAN_FIRST_AND_RECON | direct_user | `all_nontrivial_agent_tasks` | CLOSED | Added one universal bounded-reconnaissance and frozen-plan discipline in `AGENTS.md`, with WDM reuse of its existing confirmed plan instead of a second artifact or gate. Invalidated assumptions stop and revise only the affected branch. |
