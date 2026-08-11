# HMASD Role Router

```text
document_kind=role_router
all_workspace_agents_auto_load_this_file=true
root=current_cli_task
topology=root|optional_domain_manager|optional_specialist_leaf
max_subagent_depth=2
```

A fresh CLI invocation starts as Root. Root reads the current user request,
this router, and `.agents/roles/ROOT.md`. Every other agent reads this router,
its exact assignment, registered Profile, and named Role; it does not load the
Root Role or unrelated owner procedure.

## Role pointers

| Identity | Profile | Role |
|---|---|---|
| Root | current CLI task | `.agents/roles/ROOT.md` |
| Code Manager | `.codex/agents/hmasd-code-project-manager.toml` | `.agents/roles/CODE_PROJECT_MANAGER.md` |
| Explorer Manager | `.codex/agents/hmasd-independent-research-explorer.toml` | `.agents/roles/INDEPENDENT_RESEARCH_EXPLORER.md` |
| Project Scout | `.codex/agents/hmasd-project-scout.toml` | `.agents/roles/PROJECT_SCOUT.md` |
| Registered specialist | exact entry in `.codex/config.toml` | Role named by its Profile |

Root may directly invoke every registered subagent. A specialist called by
Root is a non-spawning depth-1 leaf; the same specialist may be a depth-2 leaf
under Code Manager or Explorer Manager. Direct dispatch changes only caller
and return route, never domain acceptance authority.

Root alone contacts the user, relays across owners, performs final Git actions,
and writes shared canonical state. Children remain inside their exact
assignment and Role, do not contact the user or siblings, do not spawn unless
their manager Role explicitly allows it, and never stage, commit, or push.

For every project Python command, invoke
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` directly. Do not use bare
`python`, `py`, or `conda run` unless the assignment explicitly requires a
different interpreter.

## Shared Project Scout route

`hmasd-project-scout` is the common read-only Spark lookup utility. Root, Code
Manager, or Explorer Manager may invoke it with `fork_turns=1`. Give one Scout
exactly one narrow factual question. Split independent owners, routes, files,
or evidence families into multiple separate Scout calls and run independent
calls in parallel. Scout output is factual evidence only, never design,
implementation, scientific judgment, technical judgment, review, or acceptance.
