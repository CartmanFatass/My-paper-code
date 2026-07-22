# OMP HMASD Agent Migration Design

Date: 2026-07-22
Status: Approved by user

## Goal

Expose the four bounded HMASD code-agent roles currently defined under
`.codex/agents/` as native OMP task agents under `.omp/agents/`, while retaining
the Codex definitions for Research Project Manager use and explicitly allowing
the active controller to dispatch the OMP variants.

## Scope

Create native OMP definitions for:

- `hmasd-code-scout`
- `hmasd-implementer`
- `hmasd-verifier`
- `hmasd-reviewer`

Update `.gitignore` so `.omp/agents/*.md` is durable tracked tooling, update the
protected workflow boundary in `AGENTS.md`, and update the active status in
`docs/project/CURRENT_WORK.md`. Do not alter the existing
`.codex/agents/*.toml` files.

## Native OMP Mapping

Each OMP agent is a standalone Markdown file with YAML frontmatter and a prompt
body. The prompt body preserves the corresponding Codex role's scientific,
authority, isolation, performance, and output constraints. Codex-specific tool
language is translated to OMP terminology.

| Role | Model | Thinking | Tools |
| --- | --- | --- | --- |
| Code Scout | `openai-codex/gpt-5.6-luna` | `medium` | `read`, `grep`, `glob`, `lsp` |
| Implementer | `openai-codex/gpt-5.6-sol` | `high` | `read`, `grep`, `glob`, `lsp`, `edit`, `write`, `bash` |
| Verifier | `openai-codex/gpt-5.6-luna` | `high` | `read`, `grep`, `glob`, `bash` |
| Reviewer | `openai-codex/gpt-5.6-sol` | `xhigh` | `read`, `grep`, `glob`, `lsp`, `bash` |

No definition grants the `task` tool or child spawn authority. OMP may inject
`hub` as a coordination surface; each role prompt continues to prohibit contact
with persistent sessions unless its bounded assignment explicitly changes that
constraint.

The verifier has no `edit` or `write` tool. Its `bash` permission exists only to
run exact assigned checks and may write only to an explicitly assigned evidence
root. The reviewer may run only explicitly authorized, read-only commands.

## Controller Authority Boundary

`AGENTS.md` will distinguish two agent surfaces:

1. `.codex/agents/` remains the Research Project Manager's native temporary
   implementation surface.
2. `.omp/agents/` becomes a controller-dispatchable native OMP surface.

The controller may dispatch an OMP implementation agent only when:

- no Research Project Manager mutating write lease is active;
- the user has authorized the mutating step;
- the assignment freezes the design, file scope, preserved invariants, checks,
  and acceptance criteria;
- one writer owns a file set at a time; and
- the controller independently integrates and verifies the returned package.

Read-only scouts and reviewers remain bounded by their assigned files and
questions. Direct OMP dispatch does not grant scientific adoption, formal
experiment, Git integration, project-control, or persistent-role authority to a
subagent.

## Active Control Record

`docs/project/CURRENT_WORK.md` will record that the four native OMP agents are
available for controller dispatch under the new boundary, while the Codex
profiles remain available to the Manager. This is a workflow-only change and
does not resume research, implementation, or formal compute.

## Verification

After writing the definitions and control updates:

1. Spawn each custom OMP agent with a bounded no-modification smoke assignment.
2. Confirm runtime discovery resolves all four exact names.
3. Confirm each response identifies and follows its assigned role.
4. Confirm no smoke task modifies source, project control, or runtime evidence.
5. Inspect the integrated definitions for correct model, thinking level, tool
   allowlist, no-spawn behavior, and preserved authority constraints.

The existing Codex TOML files remain unchanged and serve as the semantic source
used to compare the migrated prompt bodies.
