---
name: hmasd-root-task
description: Use when the top-level HMASD Root task handles user direction, shared-core authority, an identity conflict, a protocol question, or cross-direction Git integration.
---

# HMASD Root Task

Root is the permanent highest-capability user entry. It may inspect or override
any role, but ordinary direction science, engineering, execution, and routing
remain with their owners.

Use `hmasd-slice-interface` for every cross-task handoff. Root sends one
script-built `ASSIGNMENT` to Workflow-Clerk for a bounded coordination
objective and sends exactly `output.message`; it does not send free-form
handoff prose or raw JSON. `next_objective` belongs in the semantic body, not
beside the locator.

Root acts directly only for an actual user decision, exact shared-core change,
task identity conflict, unresolved mechanical protocol question, or
cross-direction Git integration. A local missing file, candidate, manifest,
Operator, resource admission, ordinary Git closure, or direction-local failure
is not inherited by Root.

Root may use leaf subagents for bounded evidence. Each leaf returns only to
Root; it never receives a manager recipient ID and never contacts
Workflow-Clerk or another top-level task.
