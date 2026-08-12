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

If a Project Scout call returns an explicit model quota, rate-limit, traffic,
capacity, or model-unavailable failure, do not retry Spark. The invoking Root,
Code Manager, or Explorer Manager immediately reissues the same one narrow
read-only factual question as a native child with exactly
`agent_type=default`, `model=gpt-5.6-luna`, `reasoning_effort=medium`, and
`fork_turns=1`. This is a transport-capacity fallback only: preserve the exact
scope and factual-output boundary, do not add scientific/technical judgment,
and do not use it for Research Scout, Code Scout, Critic, Innovator, Reviewer,
Verifier, or other professional roles.
