# HMASD Low-Intrusion Drift Containment, Resource-Grounded Execution, and File-Anchored Dispatch Implementation Plan

> **For agentic workers:** Execute this plan task-by-task in an isolated worktree. Use the repository-native `hmasd-agile-research-development` procedure for implementation, debugging, testing, review, and completion evidence. Do not preload the full control-plane design into ordinary implementation children. Only Operational Root may create Git commits, merge branches, change project-wide requirements, or alter activation state.

**Goal:** Replace high-frequency prompt-based drift prevention with a low-intrusion, repository-owned system that confines inevitable local semantic drift at assignment, intake, authority, and promotion boundaries; routes scope-local incidents to the smallest capable recovery owner; binds every nontrivial code assignment to exact files and a `PROJECT_MAP`-level architectural position; preserves parallel execution and the C++ backend without inventing a fixed worker count; requires CPU/memory resource preflight before experiment launch; and rejects unmeasured or implausible performance claims before they can stop work.

**Architecture:** Normal turns, tool calls, child starts/stops, and native auto-compaction must receive no control-plane prompting and must not create extra model turns. Long-term continuity comes from the existing `PROJECT_MAP.md`, partitioned `CURRENT_WORK.md`, a new machine-readable project requirement registry, file-backed assignment and result artifacts, milestone-maintained direction/technical state, deterministic incident-scope routing, measured resource preflights and experiment manifests, and owner-authorized promotion. A code assignment is executable only when it names the exact files or discovery roots and explains their role in the stable route, state ownership, dependency direction, and direct consumer described by `PROJECT_MAP.md`; professional-sounding abstractions alone are not scope. The App Server supervisor remains a low-frequency transport/liveness service and reports only bootstrap readiness, material incidents, explicit status queries, and shutdown.

**Tech Stack:** Python 3.10/3.11 stdlib (`dataclasses`, `enum`, `json`, `pathlib`, `re`, `tomllib` with `tomli` fallback, `argparse`, `sqlite3`, `os`, `ctypes` where needed), Markdown with embedded TOML metadata, Windows PowerShell 5.1 resource probes (`Get-CimInstance`), existing `tools/hmasd_control_plane/`, existing `tools/codex_supervisor/`, existing native subagents, pytest. No Agents SDK, Codex SDK, external workflow engine, automatic approval, automatic scientific/technical/Portfolio disposition, or high-frequency behavioral Hooks.

**Spec:** This plan implements and reconciles:
- `CONTROL_PLANE_RUNTIME_AND_SEMANTIC_DRIFT_AUDIT_20260821.md`;
- `docs/project/PROJECT_MAP.md`;
- `docs/project/CURRENT_WORK.md`;
- `docs/project/CONTEXT_PRECEDENCE.md`;
- `docs/project/CONTEXT_PROMOTION_POLICY.md`;
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`;
- `docs/project/ALGORITHM_PRINCIPLES.md`;
- root `AGENTS.md`;
- `.agents/roles/ROOT.md`;
- `.agents/roles/CODE_PROJECT_MANAGER.md`;
- `.agents/roles/IMPLEMENTER.md`;
- `.agents/roles/EXPERIMENT_OPERATOR.md`;
- `.agents/roles/WORKFLOW_RECOVERY_MANAGER.md`.

## Global Constraints

1. Semantic drift is expected and is not itself a control-plane incident.
2. Local reasoning, summaries, child prose, compacted context, automatic Memory, runtime status, and provider wording remain non-authoritative until the correct owner explicitly intakes or promotes them.
3. Do not use high-frequency Hooks to remind agents not to drift.
4. Normal turns, tool calls, child starts/stops, assistant Stop events, and auto-compaction must add:
   - zero control-plane prompts;
   - zero forced model turns;
   - zero workflow-wide audits;
   - zero automatic workflow/task creation.
5. Codex native auto-compaction remains the sole automatic compaction mechanism.
6. Do not install `Stop`, `PreToolUse`, `SubagentStart`, `SubagentStop`, `SessionStart`, `PreCompact`, or `PostCompact` as behavioral control-plane Hooks.
7. Existing hook code and historical ledgers may remain as evidence, but they are not the active runtime path.
8. `docs/project/PROJECT_MAP.md` remains the sole stable codemap. Do not create `CODEMAP.md`.
9. `docs/project/CURRENT_WORK.md` remains a pointer index, not a monolithic state document.
10. Assignment and result artifacts are repository-owned, human-readable, and file-backed.
11. Do not require a heavy JSON envelope for every ordinary child return.
12. Strict typed packets remain required only at cross-owner, state-mutating, provider, or promotion boundaries.
13. A child return is scope-local evidence, never a command to its parent.
14. The words `blocked`, `failed`, `terminal`, `pause`, `retire`, `cannot proceed`, and similar terms have no control effect without an exact object, exact affected action, remaining authorized work, recovery owner, and escalation condition.
15. No exact-operation incident may automatically become a Root-session incident, direction disposition, Portfolio decision, or user-authority request.
16. User escalation is permitted only for an explicitly classified `E5_USER_AUTHORITY_REQUIRED` object.
17. Project-wide constraints require registered provenance.
18. A new hard constraint in a normative artifact must reference:
   - an active requirement ID;
   - an assignment-local constraint marker; or
   - an owner-frozen scientific contract.
19. No fixed direction-count portfolio cap is authorized.
20. No project-wide default or hard upper limit for experiment worker/environment count is authorized.
21. Distinguish:
   - portfolio direction count;
   - assignment-selected experiment worker/environment count;
   - neighbor-count ceiling;
   - evidence candidate-count ceiling.
22. Experiment-critical, result-bearing execution uses parallel execution and the C++ backend wherever a semantics-preserving registered backend exists.
23. Before every experiment launch, CM records a current CPU/memory resource preflight and selects the concurrency for the exact host, route, backend, and experiment. The selected width is assignment/run-specific, not a project default.
24. Per-worker Python/Torch threads remain 1 where the current registered CPU contract requires it.
25. Serial/Python reference execution is allowed only when explicitly marked `DEBUG_REFERENCE` or `REFERENCE_ORACLE` and `result_bearing=false`.
26. A result-bearing run may not silently fall back from C++ to Python or from parallel to serial.
27. A missing semantics-preserving C++ or parallel path is implementation work for CM, not a scientific reason to terminate a direction.
28. Every nontrivial code assignment must name:
   - exact existing files or explicit new file paths;
   - exact symbols or a bounded discovery root;
   - an exact `PROJECT_MAP.md` heading/route;
   - the architectural role of those files;
   - the direct consumer or downstream effect;
   - the state owner and non-target surfaces.
29. Terms such as `pipeline`, `backend`, `orchestrator`, `core`, `adapter`, `manager`, `runtime`, `layer`, and `flow` do not establish scope unless grounded by the fields in constraint 28.
30. A discovery assignment may start without exact target files only when it is read-only, names bounded search roots and a `PROJECT_MAP` anchor, and must return an exact surface map before implementation is authorized.
31. Performance or duration claims that affect routing must be measured or transparently extrapolated from measured samples.
32. A speculative runtime estimate has no authority to pause a direction, stop a Root run, request user authorization, or create a Portfolio decision.
33. An implausible toy runtime is first classified as an implementation/performance anomaly and routed to CM.
34. `EVIDENCE_COMPLEXITY_POLICY.md` wall-clock values are review thresholds, not scientific stops.
35. File-byte SHA-256 is never a semantic-validity, owner-authority, or internal-handoff gate.
36. Internal repository handoffs use repository-relative paths, object/revision identity, owner, and Git commit when needed.
37. Hashes may be used only for a named transport-integrity threat model or deterministic test evidence.
38. The supervisor owns transport, delivery, wake, effect journaling, incidents, and recovery—not semantic interpretation.
39. Supervisor heartbeats and unchanged health remain outside model context.
40. Supervisor model-visible reporting is limited to:
   - bootstrap readiness;
   - material runtime incident;
   - explicit status request;
   - explicit manual wake result;
   - shutdown.
41. Native `wait_agent`, explicit semantic events, and explicit supervisor operations provide liveness. No Stop Hook provides liveness.
42. Direction scientific state is updated at scientific milestones, not per turn or per child.
43. Technical state is updated at technical milestones, not per process reading or tool call.
44. Do not add a per-task semantic-drift questionnaire or require implementers to self-certify that they did not drift.
45. Acceptance evidence is source diff, deterministic tests, state/receipt evidence, runtime observation, and owner disposition—not an agent’s self-description.
46. Only Operational Root stages, commits, pushes, merges, or edits project-wide requirement authority.
47. Current interpreter:
   `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
48. PowerShell scripts must run under Windows PowerShell 5.1.
49. Tests use explicit `--basetemp`.
50. Stop at the first failed hard gate.

---

# Part I — Controlling Intent and Supersession

## 1.1 Superseded plan

The prior artifacts:

```text
2026-08-21-hmasd-root-runtime-bootstrap-and-scoped-active-hooks.md
2026-08-22-hmasd-low-intrusion-drift-containment-and-execution-standards.md
```

must be marked `SUPERSEDED`, not executed as the current plan. The second file
introduced an unauthorized default worker width and did not sufficiently bind
code dispatch to exact files and the stable `PROJECT_MAP` abstraction.

Reasons:

```text
- it retained a Hook-centered architecture;
- it overused event claims and behavioral admission;
- it included per-task semantic-drift questionnaires;
- it proposed custom compaction/reanchor Hooks despite stable native compaction;
- it would increase context pollution and normal-workflow interference.
```

Do not delete the historical file. Add a clear supersession header and point to this plan.

## 1.2 Correct control objective

```text
Local semantic drift is inevitable.
Shared state drift must not happen automatically.
```

The system controls:

```text
assignment scope
incident blast radius
owner transitions
requirement provenance
result intake
cross-owner delivery
canonical promotion
experiment execution conformance
```

It does not continuously prompt the model to remain aligned.

## 1.3 Normal workflow budget

| Event | Control-plane prompt | Forced extra model turn | Semantic state mutation |
|---|---:|---:|---:|
| Ordinary user/assistant turn | 0 | 0 | 0 |
| Tool call | 0 | 0 | 0 |
| Assistant Stop | 0 | 0 | 0 |
| Child start | 0 | 0 | 0 |
| Ordinary child return | 0 | 0 | 0 |
| Native auto-compaction | 0 | 0 | 0 |
| Root runtime bootstrap | one explicit receipt | 0 | explicit |
| Material runtime incident | one explicit receipt | parent decides | explicit |
| Cross-owner packet | one typed packet | 0 | owner intake required |

---

# Part II — Repository-Owned Artifact Spine

```text
AGENTS / exact Roles
        ↓
PROJECT_MAP
        ↓
CURRENT_WORK
        ↓
PROJECT_REQUIREMENTS
        ↓
Assignment artifact
        ↓
Scope-local result artifact
        ↓
Parent/owner intake
        ↓
Direction or technical milestone update
        ↓
Authorized promotion / next assignment
```

## 2.1 Stable files

```text
docs/project/PROJECT_MAP.md
    stable code and control-plane navigation

docs/project/CURRENT_WORK.md
    active-work pointers only

docs/project/PROJECT_REQUIREMENTS.toml
    machine-readable active requirements, defaults, nonrequirements,
    supersessions and provenance

docs/project/PROJECT_REQUIREMENTS.md
    generated human-readable projection

docs/project/CODE_STRICTNESS_POLICY.md
    repository-area strictness profiles

docs/project/INCIDENT_SCOPE_AND_RECOVERY_POLICY.md
    E0–E5 blast-radius and routing policy

docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md
    file-backed dispatch, exact code-surface grounding, result and intake contract

docs/project/EXPERIMENT_EXECUTION_POLICY.md
    backend, parallelism, manifests, runtime plausibility and deviation policy

docs/project/EXECUTION_BACKEND_REGISTRY.toml
    route/backend capability registry
```

## 2.2 Assignment artifact

A nontrivial long-running assignment contains one exact file. The default
template is:

```markdown
# Assignment: <human title>

```toml hmasd-assignment
schema_version = 2
assignment_id = "asg_<stable-id>"
assignment_mode = "DISCOVERY|IMPLEMENTATION|REVIEW|OPERATION"
semantic_owner = "OPERATIONAL_ROOT|PORTFOLIO|EM:<direction>|CM:<scope>"
executor_role = "hmasd-implementer"
return_to = "CM:<scope>"
strictness_profile = "R2_EXPERIMENT_EXECUTION"
evidence_class = "B"
result_bearing = true
runtime_profile = "TOY_EXPLORATORY"
requirement_ids = ["UR-EXEC-001", "UR-EXEC-002", "UR-RESOURCE-001", "UR-PERF-001"]
nonrequirement_ids = [
  "NR-DIRECTION-CAP-001",
  "NR-WORKER-LIMIT-001",
  "NR-HASH-HANDOFF-001"
]
recovery_owner = "CM:<scope>"
result_path = "docs/.../RESULT_<id>.md"

project_map_anchor = "Standalone process-core route"
architecture_role = "ENTRYPOINT|RUNNER|STATE_OWNER|ADAPTER|NATIVE_BOUNDARY|OUTPUT_OWNER|CONTROL_PLANE|REFERENCE_ORACLE"
affected_files = [
  "ha_ctse_process/standalone_train_runner.py",
  "ha_ctse_process/collectors.py"
]
create_files = []
affected_symbols = ["run_training", "CollectorPool"]
search_roots = []
direct_consumers = [
  "ha_ctse_process/train.py",
  "ha_ctse_process/standalone_agent.py"
]
upstream_inputs = ["ha_ctse_process/config.py"]
state_owner = "standalone_train_runner"
non_target_surfaces = [
  "environment physics",
  "scientific treatment",
  "Portfolio state"
]
```

## Outcome

State one observable behavior and at least one direct consumer.

Invalid:

```text
optimize the experiment pipeline
```

Valid:

```text
the standalone training runner creates the CM-selected parallel collector pool,
and StandaloneProcessAgent receives the same ordered rollout-batch contract
```

## Exact code surface

- Existing files that may change.
- Explicit new paths that may be created.
- Exact symbols/interfaces where known.
- For `DISCOVERY`, bounded read-only search roots instead of guessed files.

## PROJECT_MAP-level abstraction

State all of:

```text
PROJECT_MAP heading/route:
architectural role:
upstream input:
direct consumer/downstream effect:
state owner:
stable dependency direction:
native boundary or none:
default/isolated/reference/legacy route status:
```

A professional-sounding noun is not a code surface. `pipeline`, `backend`,
`orchestrator`, `core`, `adapter`, `manager`, `runtime`, `layer`, and `flow`
must be resolved to exact files plus the abstraction fields above.

## Established facts

- <only facts the owner is willing to freeze for this assignment>

## Canonical references

- `docs/project/PROJECT_MAP.md#<exact-heading>`
- `<repository-relative owner artifact>`

## Allowed actions

- <bounded actions>

## Prohibited actions

- <scope or authority exclusions>

## Local completion boundary

<what ends this assignment>

## Escalation boundary

<exact E3/E4/E5 conditions>
```

Forked conversation context is background only. The file is the assignment.

### Discovery exception

A `DISCOVERY` assignment may omit `affected_files` only when:

```text
write authority = none
search_roots are exact and bounded
project_map_anchor is exact
the result must identify files, symbols, owners, consumers and dependency edges
implementation is not authorized in the same assignment
```

The discovery result becomes the input to a later implementation assignment.

## 2.3 Ordinary result artifact

```markdown
# Result: <assignment_id>

```toml hmasd-result
schema_version = 2
assignment_id = "asg_<stable-id>"
result_kind = "COMPLETED|PARTIAL|LOCAL_BOUNDARY|INCIDENT|SURFACE_MAP"
author_role = "hmasd-implementer"
owner_return = "CM:<scope>"
project_map_anchor = "Standalone process-core route"
files_observed = ["ha_ctse_process/standalone_train_runner.py"]
files_changed = ["ha_ctse_process/standalone_train_runner.py"]
symbols_changed = ["run_training"]
direct_consumer_checked = "ha_ctse_process/standalone_agent.py"
```

## Conclusion

<one direct conclusion tied to the declared consumer>

## Observed facts

- <exact file/symbol/object and observation>

## Evidence

- `<path:line>`
- `<command and factual result>`

## Changes

- `<path and symbol>`

## Architecture effect

State whether the `PROJECT_MAP` abstraction remains unchanged. If a stable
lineage role, route, state owner, dependency direction, or native boundary
changes, CM must update `PROJECT_MAP.md` in the same code commit.

## Interpretation

- <scope-local inference, clearly separated from observation>

## Remaining unknowns

- <unknown>

## Remaining authorized work

- <work that can still continue>
```

## 2.4 Abstraction-grounding rule

A code assignment or result is invalid when it contains only abstract labels
without exact repository grounding.

Rejected examples:

```text
improve the backend
repair the orchestration layer
optimize the experiment pipeline
make the core more scalable
fix the manager flow
```

Accepted form:

```text
file/symbol
+ PROJECT_MAP route/heading
+ architecture role
+ state owner
+ upstream input
+ direct consumer
+ non-target surfaces
```

This is a scope-quality rule, not a requirement to create another codemap.

## 2.5 Impact envelope

Required only when the result asserts a limitation, incident, inability to
continue an exact action, or need for a higher owner.

```markdown
## Impact envelope

```toml hmasd-impact
schema_version = 1
incident_level = "E1_EXACT_OPERATION_INCIDENT"
observed_object_kind = "agentify_operation"
observed_object_id = "op_183"
affected_actions = ["resend_exact_operation"]
unaffected_actions = [
  "inspect_existing_provider_state",
  "continue_local_analysis",
  "repair_transport_adapter"
]
does_not_imply = [
  "root_session_stopped",
  "direction_paused",
  "portfolio_retirement",
  "user_authority_required"
]
recovery_owner = "WORKFLOW_RECOVERY_MANAGER"
escalate_to = "OPERATIONAL_ROOT"
escalate_when = ["new_provider_identity_required"]
```
```

A generic word such as `blocked` without this envelope becomes
`UNSCOPED_CLAIM` and has no routing effect.

---

# Part III — Incident Scope and Recovery Model

## 3.1 Levels

| Level | Name | Meaning | Default owner | Maximum automatic propagation |
|---|---|---|---|---|
| `E0` | `OBSERVATION` | Fact/anomaly without action fence | current executor | none |
| `E1` | `EXACT_OPERATION_INCIDENT` | One exact request/process/file/tab/command cannot continue | Operator/transport/leaf | exact operation |
| `E2` | `ASSIGNMENT_RECOVERY` | Current assignment implementation or workflow needs recovery | CM/Workflow Recovery Manager | assignment/component |
| `E3` | `DOMAIN_OWNER_DECISION` | Technical contract or scientific definition may need change | CM or EM | one owner scope |
| `E4` | `CROSS_OWNER_DECISION` | Shared resource, cross-owner or Portfolio coordination | Root or Portfolio | cross-owner |
| `E5` | `USER_AUTHORITY_REQUIRED` | Existing owners lack authority | user | user decision |

## 3.2 Prohibited jumps

```text
E0 → E5: forbidden without new evidence
E1 → E5: forbidden without failed E2/E3/E4 route and exact authority gap
E2 → direction pause/retirement: forbidden
technical E3 → scientific disposition: forbidden
resource E4 → scientific termination: forbidden
provider E1 → user request: forbidden unless credentials/new external identity
```

## 3.3 Recovery ladder

```text
exact local repair
→ semantics-preserving alternate implementation
→ Workflow Recovery Manager
→ CM or EM owner decision
→ Root/Portfolio cross-owner decision
→ user authority
```

A lower step is skipped only when the exact missing authority makes it
impossible.

## 3.4 Canonical examples

### Agentify operation anomaly

```text
level=E1
affected=exact operation identity
no_resend=exact operation only
remaining=local work and distinct future owner-authorized operation
recovery_owner=transport/recovery owner
user_required=false
```

### Implausible experiment runtime

```text
level=E2
class=PERFORMANCE_IMPLEMENTATION_ANOMALY
affected=current implementation/launcher
remaining=profile, optimize, verify backend/parallel path
recovery_owner=CM
direction_disposition=none
```

### Missing scientific definition

```text
level=E3
owner=EM
CM continues unrelated engineering
user_required=false unless EM identifies a P0 choice
```

---

# Part IV — Project Requirement Registry

## 4.1 Registry schema

Canonical file:

```text
docs/project/PROJECT_REQUIREMENTS.toml
```

Schema:

```toml
schema_version = 1

[[requirements]]
id = "UR-EXEC-001"
kind = "USER_REQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["experiment.result_bearing", "code.performance_critical"]
summary = "Use a semantics-preserving C++ backend for experiment-critical result-bearing execution."
source_ref = "user:2026-08-22"
enforced_at = ["assignment", "technical_acceptance", "experiment_manifest"]
does_not_imply = ["rewrite_every_tool_in_cpp", "change_frozen_science"]
deviation_policy = "CM_MEASURED_DEVIATION_ROOT_VISIBLE"

[[requirements]]
id = "UR-EXEC-002"
kind = "USER_REQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["experiment.result_bearing"]
summary = "Use parallel execution for result-bearing experiment execution; select the worker/environment count from a current CPU/memory resource preflight for the exact host and route. No fixed width is implied."
source_ref = "user:2026-08-22"
enforced_at = ["assignment", "experiment_manifest", "operator_dispatch"]
does_not_imply = ["fixed_worker_count", "worker_count_cap", "portfolio_direction_cap", "neighbor_count_ceiling"]
deviation_policy = "CM_MEASURED_DEVIATION_ROOT_VISIBLE"

[[requirements]]
id = "UR-RESOURCE-001"
kind = "USER_REQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "CODE_PROJECT_MANAGER"
scope = ["experiment.prelaunch", "experiment.resource_selection"]
summary = "Before experiment launch, inspect current CPU and memory resources and record the CM-selected concurrency for the exact host, backend and route."
source_ref = "user:2026-08-22"
enforced_at = ["resource_preflight", "experiment_manifest", "operator_dispatch"]
does_not_imply = ["fixed_worker_default", "fixed_worker_cap", "scientific_stop"]
deviation_policy = "NONE"

[[requirements]]
id = "UR-PERF-001"
kind = "USER_REQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "CODE_PROJECT_MANAGER"
scope = ["performance_estimate", "experiment_runtime"]
summary = "A runtime claim that affects routing must be measured or transparently extrapolated from measured evidence."
source_ref = "user:2026-08-22"
enforced_at = ["result", "technical_acceptance", "resource_escalation"]
does_not_imply = ["hard_wall_clock_stop"]
deviation_policy = "NONE"

[[requirements]]
id = "UR-RECOVERY-001"
kind = "USER_REQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["subagent_incident", "workflow_recovery"]
summary = "Route scope-local problems to the smallest recovery owner before requesting user authority."
source_ref = "user:2026-08-22"
enforced_at = ["impact_envelope", "root_intake"]
does_not_imply = ["hide_real_user_decisions"]
deviation_policy = "NONE"

[[requirements]]
id = "NR-DIRECTION-CAP-001"
kind = "NONREQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "PORTFOLIO"
scope = ["portfolio"]
summary = "No fixed direction-count cap is authorized."
source_ref = "user:2026-08-22"
enforced_at = ["portfolio_plan", "constraint_lint"]
does_not_imply = ["unlimited_compute", "no_priority_judgment"]
deviation_policy = "USER_ONLY"

[[requirements]]
id = "NR-WORKER-LIMIT-001"
kind = "NONREQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["experiment.worker_count", "experiment.parallelism"]
summary = "No project-wide default or hard upper limit for worker/environment count is authorized; every launch width is selected from the current resource preflight."
source_ref = "user:2026-08-22"
enforced_at = ["assignment", "resource_preflight", "experiment_manifest", "constraint_lint"]
does_not_imply = ["serial_execution", "unbounded_resource_use", "ignore_host_capacity"]
deviation_policy = "USER_ONLY"

[[requirements]]
id = "NR-HASH-HANDOFF-001"
kind = "NONREQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["internal_handoff", "repository_artifact"]
summary = "Internal repository file handoffs do not require SHA-256 and hashes never establish semantic validity or owner authority."
source_ref = "user:2026-08-22"
enforced_at = ["assignment", "handoff", "constraint_lint"]
does_not_imply = ["transport_integrity_checks_for_untrusted_bytes"]
deviation_policy = "NAMED_THREAT_MODEL"

[[requirements]]
id = "NR-HIGH_FREQUENCY_HOOKS-001"
kind = "NONREQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["control_plane"]
summary = "Do not use high-frequency lifecycle Hooks as semantic-drift prompts or workflow-wide audit triggers."
source_ref = "user:2026-08-22"
enforced_at = ["config", "control_plane_review"]
does_not_imply = ["remove_explicit_supervisor"]
deviation_policy = "USER_ONLY"

[[requirements]]
id = "NR-COMPACTION-HOOKS-001"
kind = "NONREQUIREMENT"
status = "ACTIVE"
authority = "P0_USER"
owner = "OPERATIONAL_ROOT"
scope = ["compaction"]
summary = "Native auto-compaction remains untouched; no custom compaction Hook, automatic checkpoint, or automatic reanchor is required."
source_ref = "user:2026-08-22"
enforced_at = ["config", "control_plane_review"]
does_not_imply = ["delete_explicit_recovery_tools"]
deviation_policy = "USER_ONLY"
```

## 4.2 Registry rules

- IDs are unique and immutable.
- An active requirement cannot be silently edited; meaning changes create a
  new ID and `supersedes`.
- `NONREQUIREMENT` entries prevent historical or model-invented constraints
  from reappearing.
- Assignment files cite IDs; they do not duplicate the registry body.
- Role documents contain compact pointers and scope-specific operational rules,
  not full registry copies.
- `PROJECT_REQUIREMENTS.md` is generated; do not edit it manually.

---

# Part V — Code Strictness Profiles

Scientific evidence class `A/B/C` and code strictness profile are independent.

## `R0_NAVIGATION_AND_MECHANICAL`

Examples:

```text
PROJECT_MAP pointer
generated index
format conversion
bounded file move
non-authoritative report rendering
```

Rules:

```text
smallest edit
one focused check
no reviewer chain
no performance manifest
no scientific gate
```

## `R1_ROUTINE_ENGINEERING`

Examples:

```text
ordinary bug fix
CLI parameter
encoding
test fixture
local adapter
```

Rules:

```text
assignment-local design judgment
focused tests
CM intake
no automatic Root/user escalation
```

## `R2_EXPERIMENT_EXECUTION`

Examples:

```text
environment stepping
rollout collector
learner update path
runner/launcher
native backend
parallel worker orchestration
checkpoint/manifest/output
```

Rules:

```text
execution manifest required
parallel/C++ requirements enforced
microbenchmark required before cost conclusion
no silent backend fallback
real production command exercised
```

## `R3_PROTECTED_SCIENTIFIC_SEMANTICS`

Examples:

```text
reward/intrinsic signal
probability support/factorization
gradient/detach boundary
clock/lifecycle ownership
RNG streams
replay
credit assignment
checkpoint meaning
treatment/comparator/observable
```

Rules:

```text
EM-owned scientific object
CM implementation conformance
science-bearing ambiguity returns to EM
result-bearing changes require exact revision control
```

## `R4_CONTROL_PLANE_AND_AUTHORITY`

Examples:

```text
actor identity
workflow open/close
owner admission
promotion
operator resolution
App Server effect durability
cross-owner packet ACL
```

Rules:

```text
deterministic transitions
negative tests
idempotency
independent focused review
no raw prose authority
```

The strictness profile must prevent two opposite errors:

```text
a toy file edit must not inherit formal control-plane ceremony;
a state/authority mutation must not be treated as routine prose.
```

---

# Part VI — Experiment Execution and Plausibility

## 6.1 Backend registry

Canonical file:

```text
docs/project/EXECUTION_BACKEND_REGISTRY.toml
```

Example:

```toml
schema_version = 1

[[routes]]
route_id = "continuous_roster_native"
entrypoint = "envs.continuous_roster"
cpp_backend = "AVAILABLE"
parallel_execution = "AVAILABLE"
semantic_equivalence = "REGISTERED"
reference_python_path = true

[[routes]]
route_id = "standalone_process_default"
entrypoint = "python -m ha_ctse_process.train"
cpp_backend = "NOT_WIRED"
parallel_execution = "AVAILABLE"
semantic_equivalence = "UNASSESSED"
reference_python_path = true
owner = "CODE_PROJECT_MANAGER"
next_action = "wire or register a semantics-preserving native path before a result-bearing run that cites UR-EXEC-001"
```

Do not falsely claim every environment already uses C++. Missing wiring is
explicit engineering work.

## 6.2 Resource preflight

Every experiment launch uses a current, host-specific resource preflight. It
records facts and the CM decision; it does not impose a project-wide worker
default or cap.

```toml
schema_version = 1
preflight_id = "resource_<id>"
assignment_id = "asg_<id>"
captured_at = "<UTC>"
host_identity = "<machine/process identity>"
route_id = "continuous_roster_native"
backend = "cpp"

[cpu]
physical_cores = 0
logical_processors = 0
load_percent = 0.0

[memory]
total_gib = 0.0
available_gib = 0.0

[selection]
selected_worker_count = 0
threads_per_worker = 1
parallel = true
selection_rationale = "<CM explanation based on the observed host and route>"
cm_owner = "CM:<scope>"

[optional_probe]
sample_worker_count = 0
peak_rss_gib = 0.0
shared_memory_note = ""
```

Rules:

```text
- selected_worker_count is a positive run-specific decision;
- no number is supplied by project convention;
- CPU and memory observations must be current at launch;
- a value above logical processors is allowed only with an explicit CM rationale;
- memory selection must explain how the observed available memory supports the run;
- the Operator checks presence/identity, not the engineering wisdom of the choice;
- a changed host or materially changed available memory requires a new preflight.
```

## 6.3 Experiment manifest

```toml
schema_version = 2
manifest_id = "exp_manifest_<id>"
assignment_id = "asg_<id>"
direction_id = "<direction>"
treatment_id = "<treatment>"
evidence_class = "B"
strictness_profile = "R2_EXPERIMENT_EXECUTION"
runtime_profile = "TOY_EXPLORATORY"
result_bearing = true
requirement_ids = [
  "UR-EXEC-001",
  "UR-EXEC-002",
  "UR-RESOURCE-001",
  "UR-PERF-001"
]
nonrequirement_ids = ["NR-WORKER-LIMIT-001", "NR-DIRECTION-CAP-001"]
resource_preflight_ref = "docs/.../RESOURCE_PREFLIGHT.toml"

[code_surface]
project_map_anchor = "Standalone process-core route"
entrypoint = "ha_ctse_process/train.py"
runner = "ha_ctse_process/standalone_train_runner.py"
environment_factory = "ha_ctse_process/env_factory.py"
native_boundary = "envs/continuous_roster/cpp_backend.py"
direct_consumer = "ha_ctse_process/standalone_agent.py"

[execution]
route_id = "continuous_roster_native"
backend = "cpp"
parallel = true
worker_count = 0  # exact CM-selected value copied from the preflight
worker_count_source = "RESOURCE_PREFLIGHT"
threads_per_worker = 1
silent_fallback_allowed = false
deviation_ref = ""

[measurement]
warmup_steps = 100
sample_steps = 500
sample_wall_seconds = 5.0
estimated_target_steps = 50000
estimate_ref = "docs/.../RUNTIME_ESTIMATE.json"
```

Manifest validation requires `worker_count` to equal the selected value in the
named preflight. It does not compare the count to a global constant.

## 6.4 Runtime profiles

These values are engineering review triggers, not scientific stops.

| Profile | Typical object | Review trigger | Implementation-anomaly trigger |
|---|---|---:|---:|
| `TOY_SMOKE` | ≤5,000 simple env steps or import/step/update smoke | >120 s | >600 s |
| `TOY_EXPLORATORY` | small real learner/eval, normally ≤100k transitions | >1,200 s | >3,600 s |
| `PROOF_SIZED_MULTI_SEED` | bounded multi-seed evidence | assignment-specific; default >2 h | >4 h without measured dominant cost |
| `FORMAL_ITERATION` | conclusion-bearing train/eval/analyze | >8 cumulative h review | no universal automatic stop |

For `TOY_SMOKE` or `TOY_EXPLORATORY`:

```text
a projected 500-step duration above 10 minutes
→ PERFORMANCE_IMPLEMENTATION_ANOMALY

a projected 500-step duration measured in days
→ PERFORMANCE_IMPLEMENTATION_ANOMALY with high confidence
```

It is not a resource-cost disposition.

## 6.5 Required measurement

Before a runtime estimate affects scheduling:

```text
warm up the exact route
measure at least max(500 environment steps, 5 seconds)
record transitions, updates and evaluations separately
record backend, workers, thread count and build mode
compute throughput and estimate with the shown formula
capture a profiler when the estimate crosses anomaly threshold
```

Allowed bases:

```text
MEASURED
EXTRAPOLATED_FROM_MEASURED
SPECULATIVE
```

`SPECULATIVE` has no state/routing effect.

## 6.6 Performance anomaly recovery

Check, in order:

```text
unexpected sleep/wait
debug/instrumented build
serial fallback
Python fallback
C++ extension build every run
worker count actually active
thread oversubscription
environment reset/step bottleneck
IPC/serialization
per-step disk/log writes
accidental nested rollout/search
model update cadence
evaluation loop explosion
```

The recovery owner is CM, optionally using the Workflow Recovery Manager.

---

# Part VII — Low-Frequency Runtime and No-Hook Policy

## 7.1 Active configuration target

```text
behavioral_hooks=0
native_auto_compaction=unchanged
semantic_mcp=explicit/on-demand
supervisor=explicit Root-run command
automatic_wake=false
scheduler_serve=false
```

## 7.2 Explicit supervisor commands

Use or extend existing supervisor CLI through PowerShell wrappers:

```text
scripts/hmasd-root-supervisor-start.ps1
scripts/hmasd-root-supervisor-status.ps1
scripts/hmasd-root-supervisor-stop.ps1
```

Start uses:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  -m tools.codex_supervisor `
  --repo-root <repo> `
  --runtime-home <external-runtime> `
  serve
```

The wrapper owns process identity and readiness detection. It prints exactly one
bounded receipt:

```text
HMASD_SUPERVISOR_READY_V1
```

or:

```text
HMASD_SUPERVISOR_INCIDENT_V1
```

No periodic model message is emitted.

## 7.3 Reporting

Model-visible:

```text
READY once
INCIDENT once per material incident identity
STATUS only on explicit request
STOPPED once
```

External ledger only:

```text
heartbeat
unchanged health
PID/RSS
thread counts
stale connection counts
```

## 7.4 Liveness

```text
ordinary child
→ native wait_agent

explicit semantic bridge
→ content-free event
→ explicit await

manual supervisor mailbox
→ scheduler once only when operator requests it
```

No assistant Stop event drives continuation.

---

# Part VIII — New and Modified File Map

## Create

```text
docs/project/LOW_INTRUSION_CONTROL_PLANE.md
docs/project/PROJECT_REQUIREMENTS.toml
docs/project/PROJECT_REQUIREMENTS.md
docs/project/CODE_STRICTNESS_POLICY.md
docs/project/INCIDENT_SCOPE_AND_RECOVERY_POLICY.md
docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md
docs/project/EXPERIMENT_EXECUTION_POLICY.md
docs/project/EXECUTION_BACKEND_REGISTRY.toml

docs/project/templates/ASSIGNMENT_TEMPLATE.md
docs/project/templates/RESULT_TEMPLATE.md
docs/project/templates/IMPACT_ENVELOPE_TEMPLATE.md
docs/project/templates/EXPERIMENT_MANIFEST_TEMPLATE.toml
docs/project/templates/RESOURCE_PREFLIGHT_TEMPLATE.toml
docs/project/templates/DIRECTION_STATE_TEMPLATE.md
docs/project/templates/TECHNICAL_STATE_TEMPLATE.md

tools/hmasd_control_plane/requirements_registry.py
tools/hmasd_control_plane/artifact_protocol.py
tools/hmasd_control_plane/incident_scope.py
tools/hmasd_control_plane/intake_router.py
tools/hmasd_control_plane/constraint_lint.py
tools/hmasd_control_plane/experiment_manifest.py
tools/hmasd_control_plane/resource_preflight.py
tools/hmasd_control_plane/runtime_plausibility.py

scripts/hmasd-requirements.ps1
scripts/hmasd-validate-assignment.ps1
scripts/hmasd-validate-result.ps1
scripts/hmasd-route-incident.ps1
scripts/hmasd-constraint-lint.ps1
scripts/hmasd-resource-preflight.ps1
scripts/hmasd-validate-experiment-manifest.ps1
scripts/hmasd-runtime-plausibility.ps1
scripts/hmasd-root-supervisor-start.ps1
scripts/hmasd-root-supervisor-status.ps1
scripts/hmasd-root-supervisor-stop.ps1

tests/hmasd_control_plane/test_requirements_registry.py
tests/hmasd_control_plane/test_artifact_protocol.py
tests/hmasd_control_plane/test_incident_scope.py
tests/hmasd_control_plane/test_intake_router.py
tests/hmasd_control_plane/test_constraint_lint.py
tests/hmasd_control_plane/test_experiment_manifest.py
tests/hmasd_control_plane/test_resource_preflight.py
tests/hmasd_control_plane/test_runtime_plausibility.py
tests/hmasd_control_plane/test_low_intrusion_runtime.py
```

## Modify

```text
AGENTS.md                                 # compact pointers only
.agents/roles/ROOT.md
.agents/roles/CODE_PROJECT_MANAGER.md
.agents/roles/IMPLEMENTER.md
.agents/roles/EXPERIMENT_OPERATOR.md
.agents/roles/WORKFLOW_RECOVERY_MANAGER.md
.agents/skills/hmasd-agile-research-development/SKILL.md

docs/project/PROJECT_MAP.md
docs/project/CURRENT_WORK.md
docs/project/CONTEXT_SOURCE_REGISTRY.toml
docs/project/AGENT_CONTEXT.md

.codex/config.toml
.codex/hooks.json                         # legacy surface, explicit disabled note
scripts/codex-semantic-mvp-enable.ps1    # disable behavioral activation target
tools/codex_semantic_mvp/hook_entry.py   # mark dormant; no active config path
tools/hmasd_control_plane/doctor.py
tools/codex_supervisor/doctor.py
```

Do not create a second codemap.

---

# Task 0: Freeze the Current Baseline and Supersede the Hook-Centered Plan

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/BASELINE.md`
- Modify: prior plan header only

- [ ] Create an isolated worktree:

```powershell
git fetch origin
git worktree add `
  C:\Projects\HMASD-low-intrusion-control-plane `
  -b codex-low-intrusion-control-plane-v1 `
  origin/aggressive
```

- [ ] Record:

```powershell
Set-Location C:\Projects\HMASD-low-intrusion-control-plane
git status --short
git rev-parse HEAD
git log -10 --oneline
```

- [ ] Locate the exact audit file. If it is not already repository-backed, copy
  the user-supplied bytes without editing into:

```text
docs/research/workflow-runs/2026-08-21_control-plane-runtime-audit/
CONTROL_PLANE_RUNTIME_AND_SEMANTIC_DRIFT_AUDIT_20260821.md
```

- [ ] Record current:
  - Hook config and effective mode;
  - semantic MCP schema/status;
  - supervisor runtime presence;
  - `PROJECT_MAP`, `CURRENT_WORK`, Role and Skill pointers;
  - active directions and assignments;
  - current C++/parallel routes;
  - strings that imply a direction cap;
  - internal SHA handoff requirements;
  - runtime/cost stop language.

- [ ] Search:

```powershell
git grep -n -E "16 directions|16-direction|direction cap|maximum.*direction|最多.*方向"
git grep -n -E "SHA-?256|sha256|hash.*required|required.*hash"
git grep -n -E "30 days|wall.?clock|one.?attempt|no.?retry|recommend.*park"
git grep -n -E "PreToolUse|SubagentStart|SubagentStop|PreCompact|PostCompact|Stop" -- .codex tools/codex_semantic_mvp
```

- [ ] Add this header to the old plan:

```text
STATUS=SUPERSEDED
SUPERSEDED_BY=docs/superpowers/plans/2026-08-22-hmasd-low-intrusion-drift-containment-resource-grounded-execution-v2.md
DO_NOT_EXECUTE=true
REASON=Hook-centered design conflicts with the user-authorized low-intrusion artifact/promotion-boundary architecture.
```

- [ ] Commit:

```powershell
git add docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/BASELINE.md docs/superpowers/plans/2026-08-21-hmasd-root-runtime-bootstrap-and-scoped-active-hooks.md
git commit -m "docs: freeze low-intrusion control-plane baseline"
```

**Hard gate:** Do not modify behavior before the baseline and supersession are committed.

---

# Task 1: Write the Low-Intrusion Control-Plane Contract

**Files:**
- Create: `docs/project/LOW_INTRUSION_CONTROL_PLANE.md`
- Modify: `AGENTS.md` with one compact pointer

- [ ] Write the contract from Parts I–III and VII.

- [ ] State literally:

```text
Semantic drift is inevitable.
The control objective is drift containment at promotion/authority boundaries.
Normal turns and auto-compaction receive zero control-plane prompts.
Subagent feedback is evidence, not a parent command.
Supervisor owns liveness, not semantic interpretation.
```

- [ ] Include the normal-operation budget table.

- [ ] Include the explicit prohibition on behavioral Hooks.

- [ ] Include the E0–E5 model and prohibited jumps.

- [ ] Include the repository artifact spine.

- [ ] Add only a short AGENTS pointer:

```text
Low-intrusion drift containment, requirements, incident scope, assignment and
execution policy: docs/project/LOW_INTRUSION_CONTROL_PLANE.md and linked project
policies. These do not change Role ownership.
```

- [ ] Review the contract once against the user’s messages and the audit.

- [ ] Commit:

```powershell
git add docs/project/LOW_INTRUSION_CONTROL_PLANE.md AGENTS.md
git commit -m "docs: define low-intrusion drift containment"
```

---

# Task 2: Add the Requirement Registry

**Files:**
- Create: `docs/project/PROJECT_REQUIREMENTS.toml`
- Create: `tools/hmasd_control_plane/requirements_registry.py`
- Test: `tests/hmasd_control_plane/test_requirements_registry.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class Requirement:
    id: str
    kind: str
    status: str
    authority: str
    owner: str
    scope: tuple[str, ...]
    summary: str
    source_ref: str
    enforced_at: tuple[str, ...]
    does_not_imply: tuple[str, ...]
    deviation_policy: str
    supersedes: str | None

def load_requirements(path: Path) -> dict[str, Requirement]
def validate_registry(requirements: Mapping[str, Requirement]) -> list[str]
def require_active(requirements: Mapping[str, Requirement], ids: Iterable[str]) -> tuple[Requirement, ...]
```

- [ ] Write failing tests for:
  - duplicate ID;
  - unknown kind;
  - missing P0 source;
  - conflicting active requirements;
  - invalid supersession;
  - missing `does_not_imply`;
  - active `NONREQUIREMENT`.

- [ ] Implement `tomllib` / `tomli` fallback.

- [ ] Seed the exact entries from Part IV.

- [ ] Add:

```text
UR-EXEC-001
UR-EXEC-002
UR-RESOURCE-001
UR-PERF-001
UR-RECOVERY-001
NR-DIRECTION-CAP-001
NR-WORKER-LIMIT-001
NR-HASH-HANDOFF-001
NR-HIGH_FREQUENCY_HOOKS-001
NR-COMPACTION-HOOKS-001
```

- [ ] Run:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest `
  tests/hmasd_control_plane/test_requirements_registry.py -q `
  --basetemp=C:/Projects/HMASD-low-intrusion-control-plane/.tmp_requirements
```

- [ ] Commit:

```powershell
git add docs/project/PROJECT_REQUIREMENTS.toml tools/hmasd_control_plane/requirements_registry.py tests/hmasd_control_plane/test_requirements_registry.py
git commit -m "feat: add project requirement registry"
```

---

# Task 3: Generate the Human Requirement View

**Files:**
- Modify: `requirements_registry.py`
- Create: `docs/project/PROJECT_REQUIREMENTS.md`
- Create: `scripts/hmasd-requirements.ps1`
- Extend registry tests

**Interface:**

```python
def render_requirements_markdown(requirements: Mapping[str, Requirement]) -> str
```

- [ ] Deterministically group:

```text
ACTIVE USER REQUIREMENTS
ACTIVE PROJECT INVARIANTS
ACTIVE DEFAULTS
ACTIVE NONREQUIREMENTS
SUPERSEDED
```

- [ ] The generated file warns:

```text
Generated from PROJECT_REQUIREMENTS.toml. Do not edit manually.
```

- [ ] Second generation must be byte-identical.

- [ ] Script commands:

```text
validate
render
show --id <id>
```

- [ ] PowerShell uses explicit Python.

- [ ] Commit:

```powershell
git add tools/hmasd_control_plane/requirements_registry.py docs/project/PROJECT_REQUIREMENTS.md scripts/hmasd-requirements.ps1 tests/hmasd_control_plane/test_requirements_registry.py
git commit -m "feat: render project requirements"
```

---

# Task 4: Define Code Strictness Profiles

**Files:**
- Create: `docs/project/CODE_STRICTNESS_POLICY.md`
- Modify: `PROJECT_REQUIREMENTS.toml` if a profile requirement is needed
- Add policy tests

- [ ] Define `R0`–`R4` exactly as Part V.

- [ ] Define the interaction with evidence classes `A/B/C`.

- [ ] Explicitly reject:

```text
toy exploration inheriting conclusion-bearing C ceremony
control-plane authority edits treated as routine prose
```

- [ ] Define review requirements:
  - R0: no independent reviewer required;
  - R1: focused tests;
  - R2: manifest + benchmark + CM acceptance;
  - R3: EM/CM owner boundaries and exact revision;
  - R4: negative tests + focused independent review.

- [ ] Add a validator enum in `artifact_protocol.py` in Task 7; for now write
  document tests that required profile names exist.

- [ ] Commit:

```powershell
git add docs/project/CODE_STRICTNESS_POLICY.md tests/hmasd_control_plane
git commit -m "docs: define code strictness profiles"
```

---

# Task 5: Define Incident Scope and Recovery Policy

**Files:**
- Create: `docs/project/INCIDENT_SCOPE_AND_RECOVERY_POLICY.md`
- Create: `tools/hmasd_control_plane/incident_scope.py`
- Test: `tests/hmasd_control_plane/test_incident_scope.py`

**Interfaces:**

```python
class IncidentLevel(str, Enum):
    E0_OBSERVATION = "E0_OBSERVATION"
    E1_EXACT_OPERATION_INCIDENT = "E1_EXACT_OPERATION_INCIDENT"
    E2_ASSIGNMENT_RECOVERY = "E2_ASSIGNMENT_RECOVERY"
    E3_DOMAIN_OWNER_DECISION = "E3_DOMAIN_OWNER_DECISION"
    E4_CROSS_OWNER_DECISION = "E4_CROSS_OWNER_DECISION"
    E5_USER_AUTHORITY_REQUIRED = "E5_USER_AUTHORITY_REQUIRED"

@dataclass(frozen=True)
class ImpactEnvelope:
    level: IncidentLevel
    observed_object_kind: str
    observed_object_id: str
    affected_actions: tuple[str, ...]
    unaffected_actions: tuple[str, ...]
    does_not_imply: tuple[str, ...]
    recovery_owner: str
    escalate_to: str
    escalate_when: tuple[str, ...]

def validate_impact(envelope: ImpactEnvelope) -> list[str]
def default_route(envelope: ImpactEnvelope) -> str
def may_escalate(envelope: ImpactEnvelope, target_level: IncidentLevel) -> bool
```

- [ ] Encode prohibited jumps.

- [ ] Add canonical cases:
  - Agentify operation E1;
  - runtime estimate E2;
  - scientific ambiguity E3;
  - lease conflict E4;
  - user goal/credentials E5.

- [ ] Tests prove:
  - E1 cannot request user;
  - E2 cannot pause direction;
  - technical E3 cannot create scientific disposition;
  - E5 requires a concrete user question;
  - `does_not_imply` cannot be empty for boundary reports.

- [ ] Commit:

```powershell
git add docs/project/INCIDENT_SCOPE_AND_RECOVERY_POLICY.md tools/hmasd_control_plane/incident_scope.py tests/hmasd_control_plane/test_incident_scope.py
git commit -m "feat: classify incident blast radius and recovery"
```

---

# Task 6: Add Assignment, Result and Impact Templates

**Files:**
- Create the three Markdown templates
- Create: `docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md`

- [ ] Copy the exact metadata schemas from Part II, including
  `assignment_mode`, exact code-surface fields and `PROJECT_MAP` grounding.

- [ ] Add a dedicated “abstraction grounding” section:
  - abstract nouns do not establish scope;
  - implementation/review assignments name exact files and symbols;
  - discovery assignments are read-only and name bounded search roots;
  - every code assignment names an exact `PROJECT_MAP` heading/route,
    architecture role, state owner, upstream input, direct consumer and
    non-target surfaces.

- [ ] State:
  - ordinary success does not need an impact envelope;
  - limitation/incident feedback does;
  - cross-owner state-bearing traffic still uses typed packets;
  - assignment file is authoritative over forked context;
  - result is scope-local until intake.

- [ ] Add examples:
  - simple code repair;
  - Agentify operation anomaly;
  - performance anomaly;
  - scientific ambiguity.

- [ ] Do not add per-task meta checklists.

- [ ] Commit:

```powershell
git add docs/project/ASSIGNMENT_AND_INTAKE_PROTOCOL.md docs/project/templates
git commit -m "docs: define file-backed assignment and intake protocol"
```

---

# Task 7: Implement Assignment and Result Validation

**Files:**
- Create: `tools/hmasd_control_plane/artifact_protocol.py`
- Create: `scripts/hmasd-validate-assignment.ps1`
- Create: `scripts/hmasd-validate-result.ps1`
- Test: `tests/hmasd_control_plane/test_artifact_protocol.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class AssignmentArtifact:
    assignment_id: str
    assignment_mode: str
    semantic_owner: str
    executor_role: str
    return_to: str
    strictness_profile: str
    evidence_class: str
    result_bearing: bool
    runtime_profile: str | None
    requirement_ids: tuple[str, ...]
    nonrequirement_ids: tuple[str, ...]
    recovery_owner: str
    result_path: str
    project_map_anchor: str
    architecture_role: str
    affected_files: tuple[str, ...]
    create_files: tuple[str, ...]
    affected_symbols: tuple[str, ...]
    search_roots: tuple[str, ...]
    direct_consumers: tuple[str, ...]
    upstream_inputs: tuple[str, ...]
    state_owner: str
    non_target_surfaces: tuple[str, ...]

@dataclass(frozen=True)
class ResultArtifact:
    assignment_id: str
    result_kind: str
    author_role: str
    owner_return: str
    project_map_anchor: str
    files_observed: tuple[str, ...]
    files_changed: tuple[str, ...]
    symbols_changed: tuple[str, ...]
    direct_consumer_checked: str
    impact: ImpactEnvelope | None

def parse_assignment(path: Path) -> AssignmentArtifact
def parse_result(path: Path) -> ResultArtifact
def validate_assignment(assignment: AssignmentArtifact, registry: Mapping[str, Requirement]) -> list[str]
def validate_result(result: ResultArtifact, assignment: AssignmentArtifact) -> list[str]
```

- [ ] Parse exact fenced TOML blocks:

```text
toml hmasd-assignment
toml hmasd-result
toml hmasd-impact
```

- [ ] Do not parse arbitrary prose as control metadata.

- [ ] Validation:
  - assignment ID matches;
  - known Role;
  - known strictness/evidence/runtime profile;
  - `project_map_anchor` matches an exact heading in `PROJECT_MAP.md`;
  - implementation/review assignments have exact files;
  - discovery assignments have bounded search roots, no writes and a
    `SURFACE_MAP` result;
  - affected existing files and direct consumers exist;
  - new paths are explicit and repository-relative;
  - architecture role/state owner/non-target surfaces are nonempty;
  - outcome names an observable behavior and a direct consumer;
  - abstract labels without repository grounding are rejected;
  - requirement IDs active;
  - result-bearing R2 has runtime profile;
  - incident/local boundary has impact envelope;
  - owner route matches;
  - repository-relative result path;
  - no `../`.

- [ ] Scripts print JSON and exit nonzero on errors.

- [ ] Commit:

```powershell
git add tools/hmasd_control_plane/artifact_protocol.py scripts/hmasd-validate-*.ps1 tests/hmasd_control_plane/test_artifact_protocol.py
git commit -m "feat: validate file-anchored assignment and result artifacts"
```

---

# Task 8: Implement Root/Parent Intake Routing

**Files:**
- Create: `tools/hmasd_control_plane/intake_router.py`
- Create: `scripts/hmasd-route-incident.ps1`
- Test: `tests/hmasd_control_plane/test_intake_router.py`

**Interface:**

```python
@dataclass(frozen=True)
class IntakeDecision:
    incident_level: str
    route_to: str
    root_action: str
    user_question: str | None
    continuation_allowed: bool
    disposition_created: bool

def route_result(
    assignment: AssignmentArtifact,
    result: ResultArtifact,
    registry: Mapping[str, Requirement],
) -> IntakeDecision
```

- [ ] E0:
  ```text
  NO_DECISION
  ```
- [ ] E1:
  ```text
  route exact operator/transport/recovery owner
  root/session continuation allowed
  user_question=None
  ```
- [ ] E2:
  ```text
  CM or Workflow Recovery Manager
  ```
- [ ] E3:
  ```text
  exact CM or EM
  ```
- [ ] E4:
  ```text
  Root or Portfolio
  ```
- [ ] E5:
  ```text
  user question required
  ```

- [ ] Reject a result that claims:
  ```text
  E1 + root_session_stopped
  E2 + direction_retired
  E3 technical + scientific_disposition
  ```

- [ ] Add the toy-runtime and Agentify examples.

- [ ] Commit:

```powershell
git add tools/hmasd_control_plane/intake_router.py scripts/hmasd-route-incident.ps1 tests/hmasd_control_plane/test_intake_router.py
git commit -m "feat: route child incidents without global escalation"
```

---

# Task 9: Update Root, CM, Implementer, Operator and Recovery Roles

**Files:**
- Modify the five Role charters
- Modify project-native Skill

## Root

Add compact rules:

```text
classify only when a result changes routing
E1/E2 do not reach user by default
generic blocked wording is UNSCOPED_CLAIM
use assignment/result artifact pointers
apply requirement IDs
```

## CM

Add:

```text
UR-EXEC-001 / UR-EXEC-002 / UR-PERF-001
performance anomaly before resource conclusion
manifest ownership
no silent Python/serial fallback
missing C++/parallel path is implementation
```

## Implementer

Add:

```text
read exact assignment artifact
do not repeat entire project requirements
return impact envelope only for limitation/incident
do not return generic blocked
```

## Operator

Add:

```text
validate experiment manifest mechanically
return E1 exact-command incident on manifest/launch mismatch
never request user
never interpret runtime cost
```

## Workflow Recovery Manager

Add:

```text
receive E1/E2 bundle
repair one root cause
do not expand blast radius
return recovered or exact next E-level
```

## Skill

Add the new tools as optional boundary procedures. Do not make every ordinary
task invoke all validators.

- [ ] Keep Role additions compact; point to policies instead of copying them.

- [ ] Tests assert each Role has the required pointer and does not duplicate the
  full registry.

- [ ] Commit:

```powershell
git add .agents/roles .agents/skills/hmasd-agile-research-development/SKILL.md tests/hmasd_control_plane
git commit -m "docs: align agent roles with scoped recovery and requirements"
```

---

# Task 10: Add Execution Backend Registry

**Files:**
- Create: `docs/project/EXECUTION_BACKEND_REGISTRY.toml`
- Create: `docs/project/EXPERIMENT_EXECUTION_POLICY.md`
- Test backend registry parsing

- [ ] Inventory actual routes from `PROJECT_MAP.md`.

- [ ] For each active result-bearing route record:
  - entrypoint;
  - Python reference;
  - C++ status;
  - parallel status;
  - equivalence status;
  - owner;
  - verification reference.

- [ ] Do not claim default standalone C++ wiring when it does not exist.

- [ ] Classify missing wiring as CM implementation work.

- [ ] Add the resource-preflight, runtime-profile and measurement rules from
  Part VI.

- [ ] State explicitly:
  - no default worker count;
  - no project-wide worker cap;
  - every launch width is CM-selected from current CPU/memory evidence;
  - a number appearing in evidence-search or neighbor policies does not become
    a worker count.

- [ ] Commit:

```powershell
git add docs/project/EXECUTION_BACKEND_REGISTRY.toml docs/project/EXPERIMENT_EXECUTION_POLICY.md tests/hmasd_control_plane
git commit -m "docs: register experiment execution backends"
```

---

# Task 11: Implement Resource Preflight and Experiment Manifest Validation

**Files:**
- Create: `docs/project/templates/RESOURCE_PREFLIGHT_TEMPLATE.toml`
- Create: `docs/project/templates/EXPERIMENT_MANIFEST_TEMPLATE.toml`
- Create: `tools/hmasd_control_plane/resource_preflight.py`
- Create: `tools/hmasd_control_plane/experiment_manifest.py`
- Create: `scripts/hmasd-resource-preflight.ps1`
- Create: `scripts/hmasd-validate-experiment-manifest.ps1`
- Test: `tests/hmasd_control_plane/test_resource_preflight.py`
- Test: `tests/hmasd_control_plane/test_experiment_manifest.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ResourceSnapshot:
    preflight_id: str
    assignment_id: str
    captured_at: str
    host_identity: str
    route_id: str
    backend: str
    physical_cores: int
    logical_processors: int
    cpu_load_percent: float
    total_memory_gib: float
    available_memory_gib: float
    selected_worker_count: int
    threads_per_worker: int
    parallel: bool
    selection_rationale: str
    cm_owner: str

@dataclass(frozen=True)
class ExperimentManifest:
    manifest_id: str
    assignment_id: str
    evidence_class: str
    strictness_profile: str
    runtime_profile: str
    result_bearing: bool
    requirement_ids: tuple[str, ...]
    nonrequirement_ids: tuple[str, ...]
    resource_preflight_ref: str
    project_map_anchor: str
    entrypoint: str
    runner: str
    environment_factory: str
    native_boundary: str
    direct_consumer: str
    route_id: str
    backend: str
    parallel: bool
    worker_count: int
    worker_count_source: str
    threads_per_worker: int
    silent_fallback_allowed: bool
    deviation_ref: str | None

def load_resource_preflight(path: Path) -> ResourceSnapshot
def validate_resource_preflight(snapshot: ResourceSnapshot) -> list[str]
def load_manifest(path: Path) -> ExperimentManifest
def validate_manifest(
    manifest: ExperimentManifest,
    preflight: ResourceSnapshot,
    requirements: Mapping[str, Requirement],
    backend_registry: Mapping[str, object],
    project_map: Path,
) -> list[str]
```

- [ ] `hmasd-resource-preflight.ps1` uses PowerShell 5.1:
  - `Get-CimInstance Win32_Processor`;
  - `Get-CimInstance Win32_OperatingSystem`;
  - records physical cores, logical processors, load, total memory and available
    memory;
  - accepts CM-selected worker count and rationale;
  - writes deterministic TOML or JSON;
  - does not invent a count.

- [ ] Resource validation requires:
  - current timestamp;
  - exact host identity;
  - positive selected worker count;
  - measured CPU and memory fields;
  - nonempty CM rationale;
  - no project-default field;
  - one thread per worker where the assignment cites the CPU contract.

- [ ] A selected count above logical processors is a warning unless the CM
  rationale explicitly names oversubscription/IO behavior; it is not rejected
  by a universal cap.

- [ ] Manifest validation requires:
  - R2 for result-bearing runs;
  - exact requirement and nonrequirement IDs;
  - exact `PROJECT_MAP` anchor and code-surface paths;
  - `resource_preflight_ref`;
  - manifest worker count exactly equals the preflight selection;
  - `worker_count_source=RESOURCE_PREFLIGHT`;
  - parallel true;
  - no silent fallback;
  - C++ when route is registered available/equivalent.

- [ ] Debug/reference:
  - may use Python/serial;
  - must be `result_bearing=false`;
  - cannot be used for conclusion-bearing output.

- [ ] Missing native path:
  - returns `E2_ASSIGNMENT_RECOVERY`;
  - never recommends direction stop.

- [ ] Required tests:

```text
test_resource_preflight_has_no_default_worker_count
test_resource_preflight_records_cpu_and_memory
test_manifest_worker_count_matches_preflight
test_manifest_rejects_magic_worker_default
test_manifest_requires_project_map_anchor_and_exact_files
test_result_bearing_available_route_requires_cpp_and_parallel
test_debug_reference_may_be_serial_python
```

- [ ] Commit:

```powershell
git add docs/project/templates/RESOURCE_PREFLIGHT_TEMPLATE.toml docs/project/templates/EXPERIMENT_MANIFEST_TEMPLATE.toml tools/hmasd_control_plane/resource_preflight.py tools/hmasd_control_plane/experiment_manifest.py scripts/hmasd-resource-preflight.ps1 scripts/hmasd-validate-experiment-manifest.ps1 tests/hmasd_control_plane/test_resource_preflight.py tests/hmasd_control_plane/test_experiment_manifest.py
git commit -m "feat: ground experiment concurrency in host resources"
```

---

# Task 12: Implement Runtime Plausibility Evaluation

**Files:**
- Create: `tools/hmasd_control_plane/runtime_plausibility.py`
- Create: `scripts/hmasd-runtime-plausibility.ps1`
- Test: `tests/hmasd_control_plane/test_runtime_plausibility.py`

**Interfaces:**

```python
class EstimateBasis(str, Enum):
    MEASURED = "MEASURED"
    EXTRAPOLATED_FROM_MEASURED = "EXTRAPOLATED_FROM_MEASURED"
    SPECULATIVE = "SPECULATIVE"

class RuntimeDisposition(str, Enum):
    PLAUSIBLE = "PLAUSIBLE"
    OPTIMIZATION_REVIEW = "OPTIMIZATION_REVIEW"
    PERFORMANCE_IMPLEMENTATION_ANOMALY = "PERFORMANCE_IMPLEMENTATION_ANOMALY"
    RESOURCE_LIMIT_CANDIDATE = "RESOURCE_LIMIT_CANDIDATE"
    UNVALIDATED_ESTIMATE = "UNVALIDATED_ESTIMATE"

@dataclass(frozen=True)
class RuntimeSample:
    runtime_profile: str
    basis: EstimateBasis
    environment_steps: int
    optimizer_updates: int
    evaluations: int
    wall_seconds: float
    backend: str
    parallel: bool
    worker_count: int
    threads_per_worker: int
    target_steps: int

@dataclass(frozen=True)
class RuntimeAssessment:
    disposition: RuntimeDisposition
    steps_per_second: float | None
    estimated_seconds: float | None
    incident_level: str
    route_to: str
    user_authority_required: bool
    checks: tuple[str, ...]

def assess_runtime(sample: RuntimeSample) -> RuntimeAssessment
```

- [ ] `SPECULATIVE` returns `UNVALIDATED_ESTIMATE`, E0, no routing effect.

- [ ] Measured estimate uses:

```python
steps_per_second = environment_steps / wall_seconds
estimated_seconds = target_steps / steps_per_second
```

- [ ] `TOY_SMOKE`, 500 steps, 30 days returns:
  ```text
  PERFORMANCE_IMPLEMENTATION_ANOMALY
  level=E2
  route=CM
  user_authority_required=false
  ```

- [ ] A formal 9-hour run returns optimization/resource review, not scientific
  termination.

- [ ] Output includes the profiler checklist.

- [ ] Script accepts JSON/TOML and emits JSON.

- [ ] Commit:

```powershell
git add tools/hmasd_control_plane/runtime_plausibility.py scripts/hmasd-runtime-plausibility.ps1 tests/hmasd_control_plane/test_runtime_plausibility.py
git commit -m "feat: reject unmeasured and implausible runtime conclusions"
```

---

# Task 13: Calibrate Initial Runtime Baselines

**Files:**
- Create: `docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/RUNTIME_BASELINE.md`
- Create benchmark result JSON files under the workflow-run directory
- Do not modify scientific treatments

- [ ] Select:
  - one simple toy environment;
  - one real learner update route;
  - one parallel C++ route;
  - one Python reference route.

- [ ] Before each run:
  - execute the CPU/memory resource preflight;
  - let CM select the worker/environment count for the observed host and route;
  - record the selection and rationale;
  - do not reuse a magic project-default width.

- [ ] For each run:
  - warmup 100 steps;
  - sample at least 500 steps or 5 seconds;
  - use the preflight-selected parallel width;
  - use one thread per worker where required;
  - record build mode, backend and preflight ID;
  - record steps, updates, evaluations and wall time.

- [ ] Do not launch formal training.

- [ ] Use results to check, not silently rewrite, initial profile thresholds.

- [ ] Any threshold change:
  - edits `EXPERIMENT_EXECUTION_POLICY.md`;
  - records reason;
  - does not become a scientific stop.

- [ ] Commit benchmark evidence and any justified policy adjustment.

---

# Task 14: Add Constraint Lint

**Files:**
- Create: `tools/hmasd_control_plane/constraint_lint.py`
- Create: `scripts/hmasd-constraint-lint.ps1`
- Test: `tests/hmasd_control_plane/test_constraint_lint.py`

**Scope:**

Run only at:

```text
Role change
AGENTS change
project policy change
plan freeze
stage acceptance
merge
```

Do not run per turn or per ordinary task.

**Rules:**

Scan normative Markdown/TOML for candidate hard constraints:

```text
must
never
only
maximum
minimum
limit
cap
one attempt
no retry
required hash
fixed direction count
```

A candidate is valid when the same paragraph/block contains:

```text
[REQ:<id>]
assignment_local=true
science_contract=<path/revision>
```

- [ ] Flag:
  - any fixed direction-count cap;
  - any global/default/fixed worker count or worker cap;
  - internal handoff SHA requirement;
  - one-attempt/no-retry global rule;
  - hard wall-clock scientific stop;
  - unregistered fixed reviewer chain.

- [ ] Do not flag:
  - an assignment/run-specific `worker_count=<n>` that cites
    `resource_preflight_ref` and `NR-WORKER-LIMIT-001`;
  - `neighbor_count_ceiling=16` or evidence candidate ceilings in the existing
    scientific scaling policy;
  - owner-frozen science card values.

- [ ] First rollout is report-only.

- [ ] After false-positive review, make it fail the boundary CI/script on new
  unregistered constraints.

- [ ] Commit:

```powershell
git add tools/hmasd_control_plane/constraint_lint.py scripts/hmasd-constraint-lint.ps1 tests/hmasd_control_plane/test_constraint_lint.py
git commit -m "feat: lint unregistered project constraints"
```

---

# Task 15: Update Stable Navigation and Current Work

**Files:**
- Modify:
  - `PROJECT_MAP.md`
  - `CURRENT_WORK.md`
  - `CONTEXT_SOURCE_REGISTRY.toml`
  - `AGENT_CONTEXT.md`

- [ ] Add new stable control-plane surfaces to `PROJECT_MAP.md`.

- [ ] Add pointer records, not copied content, to `CURRENT_WORK.md`.

- [ ] Register all new policies/templates in the source registry with correct
  owner and precedence.

- [ ] In `AGENT_CONTEXT.md`:
  - point to execution policy when assigned;
  - state no per-file hash handoff;
  - retain direct interpreter and one-thread-per-worker contract where
    applicable;
  - state that worker/environment count has no project default or cap and is
    selected from a current CPU/memory preflight;
  - distinguish worker count, direction count, neighbor ceilings and evidence
    candidate ceilings.

- [ ] Confirm no `CODEMAP.md`.

- [ ] Commit:

```powershell
git add docs/project
git commit -m "docs: map low-intrusion control-plane artifacts"
```

---

# Task 16: Disable Behavioral Hooks and Preserve Native Compaction

**Files:**
- Modify:
  - `.codex/config.toml`
  - `.codex/hooks.json`
  - activation script/state handling
  - hook documentation/tests

- [ ] Set:

```toml
[features]
hooks = false
```

- [ ] Remove the live semantic Hook block from `.codex/config.toml`.

- [ ] `.codex/hooks.json` states:

```text
disabled by user-authorized low-intrusion control-plane policy
```

- [ ] Do not install:
  - Stop;
  - PreToolUse;
  - SubagentStart;
  - SubagentStop;
  - SessionStart;
  - PreCompact;
  - PostCompact.

- [ ] Preserve `hook_entry.py` and historical tests as dormant evidence only,
  or move active-only tests under an explicit historical/legacy test module.

- [ ] Activation state records:

```text
mode=disabled_low_intrusion
desired_mode=disabled_low_intrusion
reason=NR-HIGH_FREQUENCY_HOOKS-001|NR-COMPACTION-HOOKS-001
```

- [ ] Native auto-compaction receives no custom checkpoint/reanchor.

- [ ] Tests parse config and prove zero hook tables.

- [ ] Tests prove semantic MCP remains independently usable.

- [ ] Commit:

```powershell
git add .codex tools/codex_semantic_mvp scripts tests/codex_semantic_mvp
git commit -m "fix: remove behavioral hooks from normal workflow"
```

---

# Task 17: Add Low-Frequency Explicit Supervisor Control

**Files:**
- Create three supervisor PowerShell wrappers
- Modify doctor/status where necessary
- Test: `tests/hmasd_control_plane/test_low_intrusion_runtime.py`

- [ ] `start`:
  - explicit operator invocation;
  - external runtime path;
  - starts observer `serve`;
  - writes process identity;
  - prints one READY/INCIDENT receipt;
  - no managed turn;
  - no wake.

- [ ] `status`:
  - explicit query;
  - reads doctor and process identity;
  - no model call.

- [ ] `stop`:
  - explicit;
  - terminates exact process;
  - prints STOPPED receipt.

- [ ] Heartbeat remains external.

- [ ] Do not auto-start from Hook, child return, compaction or assistant Stop.

- [ ] Tests use fake App Server and do not consume model usage.

- [ ] Commit:

```powershell
git add scripts/hmasd-root-supervisor-*.ps1 tools/codex_supervisor tools/hmasd_control_plane tests/hmasd_control_plane/test_low_intrusion_runtime.py
git commit -m "feat: add explicit low-frequency supervisor lifecycle"
```

---

# Task 18: Confirm Liveness Without Stop Hooks

**Files:**
- Modify:
  - Root Role;
  - Workflow Recovery Role;
  - project-native Skill;
  - existing semantic bridge docs/tests.

- [ ] Ordinary child:
  ```text
  collaboration.wait_agent
  ```

- [ ] Explicit bridged child:
  ```text
  native_child_register
  content-free event
  explicit workflow wait
  full result through wait_agent
  ```

- [ ] Supervisor:
  ```text
  manual mailbox/status/wake only when explicitly invoked
  ```

- [ ] No unchanged-state or heartbeat messages.

- [ ] Add tests/document checks proving Stop Hook absent and wait path intact.

- [ ] Commit:

```powershell
git add .agents docs tools tests
git commit -m "docs: preserve liveness without turn-level hooks"
```

---

# Task 19: Add Direction and Technical Milestone Templates

**Files:**
- Create:
  - `DIRECTION_STATE_TEMPLATE.md`
  - `TECHNICAL_STATE_TEMPLATE.md`
- Modify assignment protocol

## Direction state sections

```text
current question
mechanism hypothesis
established observations
strongest alternative
claim ceiling
current comparator/discriminator
external review state
next high-information action
revisit/exit conditions
```

Update only on:

```text
science freeze
external review
valid result intake
mechanism/alternative/claim change
next discriminator change
stage end/long interruption
```

## Technical state sections

```text
implementation contract
accepted source commit
execution route/backend/parallel state
test evidence
runtime baselines
technical risks
remaining work
technical acceptance
```

Update only on technical milestones.

- [ ] Do not create per-turn status logs.

- [ ] Active directions migrate on their next milestone, not by rewriting all
  historical directions.

- [ ] Commit templates and policy pointers.

---

# Task 20: Migrate Active Work and Seed Real Assignments

**Files:**
- Update current-work partition files
- Create assignment bundles for two active cases

- [ ] Select:
  1. one routine code assignment;
  2. one experiment/performance assignment.

- [ ] Create assignment files citing requirement IDs.

- [ ] Every seeded code assignment must include:
  - exact affected files or bounded discovery roots;
  - exact `PROJECT_MAP` heading/route;
  - architecture role;
  - state owner;
  - upstream inputs;
  - direct consumers;
  - non-target surfaces.

- [ ] Create matching result paths.

- [ ] For one assignment, simulate an Agentify E1 incident.

- [ ] For the performance assignment, include:
  - R2;
  - runtime profile;
  - CPU/memory resource preflight;
  - manifest;
  - CM-selected worker count with no default;
  - C++/parallel requirements;
  - exact code surface and `PROJECT_MAP` abstraction.

- [ ] Validate all artifacts with scripts.

- [ ] Update `CURRENT_WORK` pointers only.

- [ ] Do not migrate closed historical work.

- [ ] Commit:

```powershell
git add docs/project/current-work docs/research/workflow-runs
git commit -m "docs: seed low-intrusion assignments"
```

---

# Task 21: Synthetic Acceptance Suite

Run:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest `
  tests/hmasd_control_plane `
  tests/codex_semantic_mvp `
  tests/codex_context_lifecycle `
  tests/codex_supervisor `
  -q `
  --basetemp=C:/Projects/HMASD-low-intrusion-control-plane/.tmp_full
```

Required assertions:

```text
ordinary turn has zero behavioral Hook
native auto-compaction has zero custom Hook
ordinary child needs no typed repair turn
E1 never routes to user
E2 performance anomaly routes to CM
30-day/500-step estimate is implementation anomaly
no fixed direction cap is authorized
no default or project-wide worker/environment cap is authorized
experiment launch requires current CPU/memory preflight
manifest worker count equals the CM-selected preflight value
code assignments name exact files and a PROJECT_MAP-level abstraction
vague professional labels alone are rejected
result-bearing available route requires C++ and parallel
serial/Python debug cannot be result-bearing
internal handoff hash is not required
unknown hard constraint is linted
assignment/result identity is exact
cross-owner promotion remains owner-gated
supervisor reports only explicit events
```

Run PowerShell wrappers under 5.1.

Write:

```text
docs/research/workflow-runs/2026-08-22_low-intrusion-control-plane/SYNTHETIC_ACCEPTANCE.md
```

Record test output as operator evidence.

Request independent focused reviews for:

```text
A. requirements/nonrequirements and constraint lint
B. incident blast radius and user escalation
C. file/codemap assignment grounding
D. CPU/memory preflight, experiment manifest, C++/parallel and runtime plausibility
E. no-Hook/low-frequency runtime
```

Close all Critical/High findings.

---

# Task 22: Controlled Live Workflow Pilot

## Pilot A — ordinary workflow

Perform normal work:

```text
one short Root turn
one tool call
one ordinary child
one native auto-compaction if it occurs naturally
```

Verify:

```text
zero control-plane prompts
zero forced turns
zero workflow-wide audit
zero Hook processes
```

## Pilot B — file-backed assignment

Dispatch one bounded code task by assignment path only.

Verify:

```text
child reads exact assignment
result file matches assignment ID
no full project policy repeated
parent intake routes locally
```

## Pilot C — scope-local incident

Use a safe synthetic/real Agentify or local operation anomaly.

Verify:

```text
E1
exact operation fence
recovery owner assigned
Root continues
no user request
```

## Pilot D — runtime plausibility

Use a small toy benchmark.

Verify:

```text
current CPU/memory preflight
CM-selected run-specific worker count
no default/cap inferred
measured sample
manifest/code-surface conformance
parallel/C++ state visible
implausible estimate routes to CM
```

## Pilot E — explicit supervisor

Start/status/stop once.

Verify:

```text
one READY
no periodic context
one explicit STATUS
one STOPPED
automatic wake false
```

Write:

```text
LIVE_PILOT_REPORT.md
```

A naturally absent auto-compaction event is `UNOBSERVED`, not a defect.

---

# Task 23: Phase Acceptance and Merge Readiness

Create:

```text
ROLLOUT_ACCEPTANCE.md
```

Acceptance:

```text
behavioral hooks=0
ordinary workflow interference=0
native compaction untouched
assignment/result validators green
exact file/symbol and PROJECT_MAP grounding green
E0–E5 routing green
E1/E2 do not reach user
requirements registry canonical
no direction cap
CPU/memory preflight active
no worker-count default/cap
parallel/C++ manifest enforcement active
runtime estimate gate active
internal SHA handoff requirement absent
constraint lint clean
supervisor low-frequency receipt behavior observed
automatic wake=false
Stage 5 unauthorized
```

Run the full suite once more from a clean worktree.

Run:

```powershell
scripts/hmasd-constraint-lint.ps1
scripts/hmasd-requirements.ps1 validate
```

Require clean results.

Commit acceptance.

---

# Task 24: Merge and Rollback

## Merge

```powershell
git checkout aggressive
git pull --ff-only origin aggressive
git merge --no-ff codex-low-intrusion-control-plane-v1 `
  -m "merge: add low-intrusion drift containment and execution standards"
```

Resolve conflicts without restoring behavioral Hooks or deleting registered
requirements.

Rerun full tests, requirement validation and constraint lint.

Push:

```powershell
git push origin aggressive
```

Do not delete the source branch/worktree until the live pilot remains stable.

## Rollback

If the new artifact system causes an operational issue:

```text
do not restore high-frequency Hooks;
do not remove requirement history;
do not delete assignment/results;
disable only the failing validator or wrapper;
record an E2 recovery assignment;
continue ordinary work through native collaboration.
```

Rollback must preserve:

```text
PROJECT_REQUIREMENTS
incident history
assignment/result evidence
native auto-compaction
owner authority
```

---

# Part IX — Acceptance Matrix

| Property | Required evidence |
|---|---|
| Drift is local | ordinary prose cannot mutate owner/shared state |
| Low intrusion | zero behavioral Hooks; zero forced normal turns |
| Traceability | assignment/result/intake paths and IDs |
| Scoped incidents | E0–E5 tests and impact envelopes |
| Recovery autonomy | E1/E2 route below user |
| Requirement persistence | registry IDs and generated view |
| No hidden constraints | boundary constraint lint |
| No direction-count cap | active NONREQUIREMENT |
| Resource-grounded parallel norm | CPU/memory preflight + manifest validation |
| Stable C++ norm | backend registry + manifest validation |
| No worker-count default/cap | active NONREQUIREMENT + preflight-selected width |
| File-anchored dispatch | exact files/symbols + PROJECT_MAP abstraction validation |
| Runtime sanity | measured plausibility assessment |
| Toy anomaly handling | 500-step multi-day estimate → CM anomaly |
| No SHA ritual | internal handoff path/owner identity only |
| Low-frequency supervisor | explicit READY/INCIDENT/STATUS/STOPPED |
| Native compaction | no custom Hook or reanchor |
| Owner promotion | existing promotion policy unchanged |

---

# Part X — Explicit Non-Goals

This plan does not authorize:

```text
high-frequency Hooks
per-turn control prompts
per-task drift questionnaires
custom compaction Hooks
automatic reanchor
automatic approval
automatic work retry
automatic scientific acceptance
automatic technical acceptance
automatic Portfolio disposition
managed EM/CM App Server threads
scheduler serve
unattended overnight execution
Agents SDK
Codex SDK
external workflow engine
```

---

# Execution Handoff for Local Codex

Save this plan at:

```text
docs/superpowers/plans/2026-08-22-hmasd-low-intrusion-drift-containment-resource-grounded-execution-v2.md
```

Use this exact initial instruction:

```text
Read the complete plan:
docs/superpowers/plans/2026-08-22-hmasd-low-intrusion-drift-containment-resource-grounded-execution-v2.md

Read:
CONTROL_PLANE_RUNTIME_AND_SEMANTIC_DRIFT_AUDIT_20260821.md
AGENTS.md
.agents/roles/ROOT.md
.agents/roles/CODE_PROJECT_MANAGER.md
.agents/roles/IMPLEMENTER.md
.agents/roles/EXPERIMENT_OPERATOR.md
.agents/roles/WORKFLOW_RECOVERY_MANAGER.md
docs/project/PROJECT_MAP.md
docs/project/CURRENT_WORK.md
docs/project/CONTEXT_PRECEDENCE.md
docs/project/CONTEXT_PROMOTION_POLICY.md
docs/project/EVIDENCE_COMPLEXITY_POLICY.md
docs/project/ALGORITHM_PRINCIPLES.md

User intent is fixed:

- semantic drift is inevitable;
- do not use Hooks or repeated prompts to prevent it;
- normal workflow and native auto-compaction must remain untouched;
- contain drift at assignment, intake, owner and promotion boundaries;
- scope-local incidents must recover below the user whenever authority permits;
- no fixed direction-count cap is authorized;
- no project-wide default or hard upper limit for worker/environment count is
  authorized;
- result-bearing experiment paths require parallel execution and a
  semantics-preserving C++ backend where registered;
- every experiment launch requires a current CPU/memory resource preflight and
  the exact worker count selected by CM for that host and route;
- every nontrivial code assignment must name exact files or bounded discovery
  roots plus its PROJECT_MAP-level route, architecture role, state owner,
  upstream input and direct consumer;
- professional-sounding abstractions without this repository grounding are not
  valid dispatch scope;
- runtime/cost conclusions require measured evidence;
- an implausible toy runtime is an implementation anomaly, not a reason to end
  a research direction;
- internal repository handoffs do not require SHA-256;
- the supervisor is low-frequency transport/liveness infrastructure, not a
  semantic prompting system.

The previous Hook-centered Root-runtime plan is superseded and must not be
executed.

Execute Task 0 onward in order, test-first.
Use assignment-local context only.
Do not inject this whole plan into every child.
Only Operational Root may commit or merge.
Stop at the first hard-gate failure and report exact evidence.
```
