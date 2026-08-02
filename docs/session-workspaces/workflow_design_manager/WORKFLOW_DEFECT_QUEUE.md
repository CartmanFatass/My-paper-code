# Workflow incident log

```text
owner=workflow_design_manager
ordering=chronological
scheduler=false
global_blocker=false
report_authority=advisory_only
hash_identity=forbidden
```

Append each typed `WORKFLOW_DEFECT_REPORT` here for history. WDM independently
reproduces shared-contract defects, but this file never schedules work or blocks
unrelated local recovery. A material policy/authority change moves to a
user-confirmed plan. Retryable tool failure remains a checklist item, not a new
mechanism or terminal state.

| received_order | report_id | source_role | observed_contract | status | disposition |
|---:|---|---|---|---|---|
| 1 | FIRST_BINDING_BOOTSTRAP_DEADLOCK | independent_research_explorer | `f4b12303ad3a4b6fdd2f43445ade0b881c52d835` | CLOSED | Replaced the deadlock with one strict provider-parameterized lifecycle: ChatGPT first binding captures the conversation created by the single raw-question send; Gemini uses the same interface on its bound page; local identity never enters `RAW_QUESTION`. Agentify pinned to `e9f636740bf94d7db260c8817554904cdcb68870`; focused and contract tests passed. |
| 2 | GENERAL_PLAN_FIRST_AND_RECON | direct_user | `all_nontrivial_agent_tasks` | CLOSED | Added one universal bounded-reconnaissance and frozen-plan discipline in `AGENTS.md`, with WDM reuse of its existing confirmed plan instead of a second artifact or gate. Invalidated assumptions stop and revise only the affected branch. |
| 3 | WINDOWS_UNICODE_POST_WRITE_FALSE_FAILURE | independent_research_explorer | `f9de596e819fe44d1ef2285f610eda95aeca8714` | CLOSED | Configured wrapper stdout/stderr for UTF-8 before command dispatch; a command-level cp1252 simulation proved that a Chinese source/output path is written and reported successfully. No provision replay or transport action. |
| 4 | ACTIVATED_TAB_EXISTING_BINDING_ADOPTION | code_project_manager | `hmasd-agentify-pro-transport` | CLOSED | Added explicit adoption of one unique exact URL/provider tab keyed only `default`/empty; Agentify re-keys it after durable binding/idempotency validation and before the unchanged strict send path. Creation/adoption flags are mutually exclusive. No page creation, navigation, durable conversation rebinding or new terminal. |
| 5 | CREATED_TAB_READINESS_RACE | independent_research_explorer | `bd6eb3a3417553713eb5ddfccd6a748c06329642` | CLOSED | After the one contract-allowed tab creation/reopen, the wrapper calls Agentify's existing 30-second `ensure-ready` on the returned exact tab before the unchanged inventory/status proof. No wrapper polling, state, alternate transport or second creation was added. |
| 6 | FIRST_BINDING_POST_SEND_CANONICAL_IDENTITY_RACE | independent_research_explorer | `bd6eb3a3417553713eb5ddfccd6a748c06329642` | CLOSED | First binding now waits through provisional `WEB:` identity until the same user message appears under the canonical conversation. An already-created durable operation is observed through its full deadline without a second send; the existing provisional binding is updated only from that same operation's canonical completion. Agentify `79c5b421e4fb5ac817c273311090b74d5d2c1306` and focused tests passed. |
| 7 | PUBLIC_QUERY_RETURNED_STALE_ASSISTANT | agentify_transport_operator | `e246112b576e9db8d685f7400aabbe30aee4064e` | CLOSED | Generic query completion accepted the pre-send registration reply. Agentify now records the assistant count before send and accepts only a later assistant node; no wrapper, hash, state machine or extra transport path was added. Agentify `98c8adfb2ae2354f8746114c8a98d41017688741`; 32 focused tests passed. |
| 8 | WORKSPACE_TICKET_BORN_DIRTY_OUTSIDE_ALLOW_LIST | code_project_manager | `a433a391a213340fc707ac1cb0e4fc1898740cc3` | CLOSED | Reproduced as a Windows long-path status false positive: plain Git marked 11 tracked paths modified while command-local `core.longpaths=true` reported the ticket clean. Extended the existing command-local rule to ticket verification and ticketed implementer Git inspection; the original clean ticket then verified with `changed_paths=[]`. No cleanup, reprovision or new gate. |
| 9 | AGENTIFY_STABLE_KEY_ACTIVE_QUERY_BATCH_AMPLIFICATION | independent_research_explorer | `IR_BATCH:IR-LOCAL-CANDIDATE-VALIDATION-2026-08-02-V1:CONSTRUCTIVE:V1` | CLOSED | The first timed-out query left the shared key active in `waiting_for_ready`; the unconditional continue rule amplified one failure into 15 `tab_busy` errors. The user confirmed the minimal repair: one post-error status read distinguishes idle from active; an active key receives no later sends, while other keys may continue, and any item error makes the batch `ERROR`. No resend, monitor or recovery state was added. |
| 10 | AGENTIFY_DUPLICATE_SEND_AND_PAYLOAD_POLLUTION | direct_user | `IR_BATCH:IR-LOCAL-CANDIDATE-VALIDATION-2026-08-02-V1:CONSTRUCTIVE:V4` | CLOSED | The Operator copied shell command output around question files into the reviewer prompt and treated transient/incomplete responses as terminal before sending later items. Agentify `a4dbdfa` reads one explicit `promptPath` directly and rejects transient `thinking` placeholders as completion; the ordered batch stops before any later send when the current item is not naturally complete. Agentify 36 focused tests plus the HMASD review, research-workflow and harness contracts passed. No hash, wrapper, ledger or new terminal state. |
| 11 | AGENTIFY_PINNED_TAB_BYPASSED_BY_FRESH_KEY | direct_user | `hmasd-agentify-transport-smoke` | CLOSED | The smoke assignment invented a fresh key although Agentify exposed the persistent `default` tab as `protectedTab=true`. The normal contract now requires the manifest key to resolve to the existing pinned protected provider tab before send; Agentify's existing `expectedModel` selector remains the only model-selection implementation. No new page, selector wrapper, state or terminal was added. |
