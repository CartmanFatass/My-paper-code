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
| 3 | WINDOWS_UNICODE_POST_WRITE_FALSE_FAILURE | independent_research_explorer | `f9de596e819fe44d1ef2285f610eda95aeca8714` | CLOSED | Configured wrapper stdout/stderr for UTF-8 before command dispatch; a command-level cp1252 simulation proved that a Chinese source/output path is written and reported successfully. No provision replay or transport action. |
| 4 | ACTIVATED_TAB_EXISTING_BINDING_ADOPTION | code_project_manager | `hmasd-agentify-pro-transport` | CLOSED | Added explicit adoption of one unique exact URL/provider tab keyed only `default`/empty; Agentify re-keys it after durable binding/idempotency validation and before the unchanged strict send path. Creation/adoption flags are mutually exclusive. No page creation, navigation, durable conversation rebinding or new terminal. |
| 5 | CREATED_TAB_READINESS_RACE | independent_research_explorer | `bd6eb3a3417553713eb5ddfccd6a748c06329642` | CLOSED | After the one contract-allowed tab creation/reopen, the wrapper calls Agentify's existing 30-second `ensure-ready` on the returned exact tab before the unchanged inventory/status proof. No wrapper polling, state, alternate transport or second creation was added. |
| 6 | FIRST_BINDING_POST_SEND_CANONICAL_IDENTITY_RACE | independent_research_explorer | `bd6eb3a3417553713eb5ddfccd6a748c06329642` | ACTIVE | FIFO evaluation started after item 5 closed. Exactly one first-binding send later gained a user-message receipt, but the operation captured temporary `WEB:` identity and the wrapper returned before the durable ledger settled. Resend and manual state edits remain forbidden. |
