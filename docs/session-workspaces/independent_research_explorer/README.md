# Independent Research Explorer workspace

```text
owner_role=independent_research_explorer
owner_task_source=research_scheduler
owner_mode=direction|portfolio
startup_identity=role|owner_assignment|canonical_inputs
durable_workspace=docs/session-workspaces/independent_research_explorer/
temporary_workspace=temp/sessions/independent_research_explorer/
shared_surface_owner=false
public_current_work_partition_authority=none
continuity_entry=local_research/RESEARCH_CONTINUITY.md
```

This tracked directory holds compact research plans and WDM reload receipts. It
grants no workflow-design authority and contains no
candidate content, scientific state, runtime evidence, Pro archive, formal
project state or another session's context. Temporary research material stays
under the paired ignored workspace. Mature-candidate exchange copies use only
the ignored sender-owned `temp/handoffs/explorer_to_code_manager/` path defined
by `docs/project/handoffs/README.md` and require no Git operation.

An Explorer owner task is identified by its role, exact Scheduler assignment
and canonical inputs. The Explorer alone owns the lightweight continuity entry at
`local_research/RESEARCH_CONTINUITY.md`; it records only active campaign or
artifact paths, the last completed phase barrier, any unfinished assignment or
review, the next scientific action and the current authorized source boundary.

Authority and path ownership come from the Explorer role charter and
`docs/project/SESSION_WORKSPACE_CONTRACT.md`; this README does not duplicate or
expand them.
