# Assignment: Context foundation coherence review

```toml hmasd-assignment
schema_version = 2
assignment_id = "asg_context_foundation_review"
assignment_mode = "REVIEW"
semantic_owner = "OPERATIONAL_ROOT"
executor_role = "hmasd-reviewer"
return_to = "OPERATIONAL_ROOT"
strictness_profile = "R4_CONTROL_PLANE_AND_AUTHORITY"
evidence_class = "B"
result_bearing = false
runtime_profile = ""
requirement_ids = ["UR-RECOVERY-001"]
nonrequirement_ids = [
  "NR-HIGH_FREQUENCY_HOOKS-001",
  "NR-COMPACTION-HOOKS-001",
  "NR-HASH-HANDOFF-001"
]
recovery_owner = "OPERATIONAL_ROOT"
acceptance_outcome = ""
result_path = "docs/research/workflow-runs/2026-08-22_context-foundation-closure/results/RESULT_context_foundation_review.md"
project_map_anchor = "Repository context lifecycle"
architecture_role = "CONTROL_PLANE"
affected_files = []
create_files = []
affected_symbols = []
search_roots = [
  "tools/codex_context_lifecycle",
  "tools/hmasd_control_plane",
  "docs/project"
]
direct_consumers = [
  ".agents/roles/ROOT.md",
  ".agents/roles/CODE_PROJECT_MANAGER.md"
]
upstream_inputs = [
  "AGENTS.md",
  "docs/project/CONTEXT_SOURCE_REGISTRY.toml"
]
state_owner = "operational_root"
non_target_surfaces = [
  "scientific direction state",
  "technical acceptance",
  "Portfolio allocation",
  "App Server live runtime"
]
```

## Outcome

Operational Root receives one evidence-backed review of whether Stage 1
artifacts form a coherent repository-owned context foundation, with no runtime
or semantic disposition.

## Allowed actions

Read only the declared search roots and upstream inputs. Write only the declared
result artifact. Report exact evidence, actionable findings, and residual
limitations.

## Prohibited actions

Do not edit source, tests, policies, roles, scientific artifacts, technical
acceptance, Portfolio state, App Server runtime state, or Git. Do not contact
the user or spawn children. Do not create a semantic disposition.

## Local completion boundary

The declared result artifact contains a conclusion-first, evidence-backed
coherence review and is returned to Operational Root through the CM intake
route.
