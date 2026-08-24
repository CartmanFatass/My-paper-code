# CM migration preparation: minimum viable external execution kernel

```text
document_kind=CM_AUTHORED_CONTROL_PLANE_MIGRATION_PREPARATION
marker=HMASD_MINIMUM_VIABLE_CONTROL_PLANE_DESELFHOSTING_CM_MIGRATION_PREPARATION_20260824
assignment=HMASD-MVCP-DESELFHOSTING-PREPARATION-20260824-01
scope=shared:minimal_control_plane_deselfhosting
author_role=CODE_PROJECT_MANAGER
request=docs/session/PORTFOLIO_TO_ROOT_MINIMUM_VIABLE_CONTROL_PLANE_DESELFHOSTING_MIGRATION_PREPARATION_20260824.md
disposition=MIGRATION_PREPARATION_READY_WITH_EXPLICIT_PRE_CUTOVER_BLOCKERS
activity=READ_ONLY_DISCOVERY|DESIGN_AND_COST_ONLY
implementation_or_runtime_change=false
```

## Technical disposition

The requested target is feasible, but removal is not safe today. The current
repository-local control plane is one mutually coupled implementation, not four
independently removable packages. It can be replaced by one external,
non-self-governing kernel exposing exactly three synchronous authorization
boundaries: `G1_INTENT_EFFECT`, `G2_COMMIT_EXECUTION_IDENTITY`, and
`G3_RESULT_PROMOTION`.

The later cutover must be deletion-first and atomic. It must not dual-run the
old permission system, retain import shims, or make legacy tests a production
gate. The immediate blockers are:

1. the external kernel has not been implemented, installed, or version-bound;
2. `.codex/config.toml` still launches two repository-local MCP servers;
3. `experiments/candidates/renewal_indexed_score_plasticity/durable_b3_r03_launcher.py`
   directly imports `tools.hmasd_control_plane.long_effect`;
4. current Codex processes may have already loaded the old MCP servers and
   therefore require one later authorized application/MCP restart at cutover;
5. the question-relevant UCOPE S1 object must reach its next safe atomic
   frontier before its supporting old runtime is removed; and
6. current project-facing role/policy text still makes heartbeat, canary,
   actor/packet, and lifecycle machinery appear authoritative.

These facts require completion or rewrite before cutover; none justifies a
compatibility layer. SGSP's current read-only conformance return and RCLE's
existing scheduled event are preserved as described under Grandfathering.

## One external bootstrap/runtime root

Use this exact root on the current host:

```text
C:\Users\fires\AppData\Local\HMASD\execution-kernel
```

It is outside `C:\Projects\HMASD`, is not governed by HMASD `AGENTS.md`, and
must not read HMASD actor maps, role files, queue state, promotion state, source
registry, or its own tests when deciding a production request.

```text
execution-kernel\
  bootstrap\
    hmasd-kernel.exe                 # stable, minimal version selector
    current.json                     # atomic {version,digest} pointer
  versions\v1\
    hmasd-kernel.exe                 # versioned production executable
    schemas\                         # G1/G2/G3 wire schemas
    acceptance\                      # ordinary external CI/replay fixtures
  runtime\
    kernel.sqlite3                   # durable intent/operation/promotion ledger
    locks\                            # resource/output/foreground-owner locks
    operations\                      # immutable run records and event journals
  snapshots\                         # cutover/rollback snapshots
  legacy-archive\20260824\           # relocated old source/tests/scripts only
```

Only `bootstrap`, the selected `versions\v1` executable/schemas, and `runtime`
are on the production path. `legacy-archive` and `acceptance` are not imported
or consulted by production admission. The bootstrap validates the selected
executable digest and starts it; it contains no policy other than fail-closed
selection of one installed version.

## Exact relocation and disposition manifest

The source-controlled inventory below was measured from current bytes. A later
cutover must assert the listed source-file count before moving and must stop if
the set has drifted. The recursive mappings include every file under each
named directory; generated caches are excluded.

| Current HMASD path | Source files | Current lines | Exact destination/disposition |
|---|---:|---:|---|
| `tools/codex_semantic_mvp/**` | 22 | 8,216 | move to `execution-kernel\legacy-archive\20260824\src\tools\codex_semantic_mvp\**`; delete HMASD directory |
| `tools/codex_context_lifecycle/**` | 14 | 2,224 | move to `...\src\tools\codex_context_lifecycle\**`; delete HMASD directory |
| `tools/codex_supervisor/**` | 47 | 9,908 | move to `...\src\tools\codex_supervisor\**`; delete HMASD directory |
| `tools/hmasd_control_plane/**` | 16 | 3,010 | move to `...\src\tools\hmasd_control_plane\**`; delete HMASD directory |
| `tests/codex_semantic_mvp/**` | 32 | 6,679 | move to `...\tests\codex_semantic_mvp\**`; delete HMASD directory |
| `tests/codex_context_lifecycle/**` | 21 | 2,257 | move to `...\tests\codex_context_lifecycle\**`; delete HMASD directory |
| `tests/codex_supervisor/**` | 80 | 10,506 | move to `...\tests\codex_supervisor\**`; delete HMASD directory |

The request omitted `tests/hmasd_control_plane/**`, but 15 current Python test
files directly import the package being removed. They must move to
`execution-kernel\legacy-archive\20260824\tests\hmasd_control_plane\` and be
deleted from HMASD in the same cutover:

```text
test_artifact_protocol.py
test_cli.py
test_constraint_lint.py
test_diagnostics.py
test_experiment_manifest.py
test_incident_scope.py
test_intake_router.py
test_long_effect.py
test_low_intrusion_runtime.py
test_mcp_runtime.py
test_mcp_server.py
test_requirements_registry.py
test_resource_preflight.py
test_runtime_plausibility.py
test_stdio_servers.py
```

Move these 32 exact scripts to
`execution-kernel\legacy-archive\20260824\scripts\` and delete the HMASD
copies:

```text
scripts/codex-app-server-observer-canary.ps1
scripts/codex-app-server-observer-doctor.ps1
scripts/codex-app-server-observer-schema.ps1
scripts/codex-app-server-observer-serve.ps1
scripts/codex-app-server-observer-snapshot.ps1
scripts/codex-app-server-observer-test.ps1
scripts/codex-context-lifecycle-doctor.ps1
scripts/codex-context-lifecycle-gc.ps1
scripts/codex-context-lifecycle-index-decisions.ps1
scripts/codex-context-lifecycle-test.ps1
scripts/codex-mailbox-doctor.ps1
scripts/codex-mailbox-list.ps1
scripts/codex-mailbox-once.ps1
scripts/codex-mailbox-send-canary.ps1
scripts/codex-mailbox-serve.ps1
scripts/codex-mailbox-test.ps1
scripts/codex-managed-actor-adopt.ps1
scripts/codex-managed-actor-create.ps1
scripts/codex-managed-actor-doctor.ps1
scripts/codex-managed-actor-suspend.ps1
scripts/codex-managed-actor-test.ps1
scripts/codex-managed-actor-turn.ps1
scripts/codex-semantic-mvp-disable.ps1
scripts/codex-semantic-mvp-doctor.ps1
scripts/codex-semantic-mvp-enable.ps1
scripts/codex-semantic-mvp-test.ps1
scripts/codex-semantic-topology-probe.ps1
scripts/codex-supervisor-durability-doctor.ps1
scripts/codex-supervisor-durability-test.ps1
scripts/hmasd-root-supervisor-start.ps1
scripts/hmasd-root-supervisor-status.ps1
scripts/hmasd-root-supervisor-stop.ps1
```

### Coupled import graph

The packages must be archived together because current imports cross their
nominal boundaries:

| Importer | Imported old package/surface |
|---|---|
| `tools/codex_semantic_mvp/mcp_server.py` | `tools.codex_context_lifecycle.authority`; `tools.hmasd_control_plane.mcp_runtime` |
| `tools/codex_context_lifecycle/**` | semantic actor models, epochs, semantic commits, models, store, and DB |
| `tools/codex_supervisor/managed_packet_send.py` | semantic packet refs |
| `tools/codex_supervisor/semantic_scanner.py` | semantic models |
| `tools/codex_supervisor/semantic_bridge.py` | semantic actor models, checkpoints, epochs, and store |
| `tools/hmasd_control_plane/mcp_server.py` | context-lifecycle `default_repo_root` |
| `tests/codex_context_lifecycle/test_mcp_authority.py` | `tools.hmasd_control_plane.mcp_server` |
| `experiments/candidates/renewal_indexed_score_plasticity/durable_b3_r03_launcher.py` | `tools.hmasd_control_plane.long_effect` |

The new kernel must be a clean implementation of G1/G2/G3 and must import none
of these archived packages. The RISP launcher must call the new G2/run-record
API directly after its current operation reaches a safe frontier. No module
alias, forwarding package, import hook, or copied validator is permitted.

### Delete, rewrite, keep

Delete from active HMASD authority at cutover:

```text
.codex/semantic-actors.toml
.codex/hooks.semantic-mvp.active.json
.codex/hooks.semantic-mvp.shadow.json
.codex/app-server-observer.toml
runtime/codex-semantic-mvp/**
runtime/hmasd-control-plane/**
```

The runtime directories are snapshotted first; they are not imported into the
new production ledger. Existing operation provenance is closed or
grandfathered explicitly rather than inferred from old rows. Historical
documents that mention the old system remain immutable provenance and are not
auto-loaded.

Rewrite atomically:

```text
.codex/config.toml
AGENTS.md
.agents/roles/ROOT.md
.agents/roles/CODE_PROJECT_MANAGER.md
.agents/roles/EXPERIMENT_OPERATOR.md
docs/project/PROJECT_MAP.md
docs/project/CURRENT_WORK.md
docs/project/CONTEXT_SOURCE_REGISTRY.toml
docs/project/LOW_INTRUSION_CONTROL_PLANE.md
docs/project/EXPERIMENT_EXECUTION_POLICY.md
experiments/candidates/renewal_indexed_score_plasticity/durable_b3_r03_launcher.py
```

`CONTEXT_SOURCE_REGISTRY.toml` currently has no direct entry for any of the four
implementation or test directories, so there is no such entry to delete.
However, the `low-intrusion-control-plane` and
`p0-hidden-limit-control-plane-correction` entries currently keep superseded
multi-gate policy active; at cutover they must become non-auto-loaded historical
provenance or be removed from the current registry. The source registry remains
project data and never becomes kernel authority.

Delete these seven old wrapper entry points rather than redirecting them:

```text
scripts/hmasd-validate-assignment.ps1
scripts/hmasd-route-incident.ps1
scripts/hmasd-requirements.ps1
scripts/hmasd-constraint-lint.ps1
scripts/hmasd-runtime-plausibility.ps1
scripts/hmasd-validate-experiment-manifest.ps1
scripts/hmasd-validate-result.ps1
```

The project-specific schema logic still needed at G2/G3 is re-expressed as
data schemas or validators called by the external kernel, not as repository
permission commands. Retain ordinary HMASD source, research, experiment data,
the three wire schemas, immutable historical artifacts, and experiment-specific
validators that check only concrete G2/G3 facts.

The exact new HMASD-owned data/validation destinations for that later tranche
are:

```text
configs/control_kernel/v1/intent.schema.json
configs/control_kernel/v1/runspec.schema.json
configs/control_kernel/v1/result-promotion.schema.json
tools/hmasd_experiment_validation/g2_manifest.py
tools/hmasd_experiment_validation/g3_result.py
```

The two Python validators are newly extracted, project-specific fact checkers;
they do not import an archived package, consult actor/role/queue state, or
authorize an effect. Their content-addressed output is evidence consumed
inside G2 or G3. The external kernel still independently enforces all hard
identity, at-most-once, conflict, no-resend, and promotion invariants.

## Deleted old entry points

All of the following cease to be production entry points in one cutover:

- MCP server `python -m tools.codex_semantic_mvp.mcp_server` and the
  `hmasd_orchestrator` registration. Its enabled tools are
  `runtime_health`, `workflow_current`, `workflow_wait_plan`, `workflow_open`,
  `task_register`, `task_bind`, `native_child_register`, `workflow_state`,
  `report_get`, `root_record_intake`, `obligation_open`,
  `obligation_resolve`, `responsibility_handoff_open`,
  `responsibility_handoff_accept`, `responsibility_scheduled_record`,
  `responsibility_idle_complete_record`,
  `responsibility_local_boundary_record`, `responsibility_orphan_detect`,
  `responsibility_orphan_assign`, `provider_transaction_classify`,
  `provider_recovery_resend_authorize`, `workflow_await_event`,
  `workflow_await_global_event`, `workflow_close`, `actor_context_current`,
  `plan_epoch_open`, `plan_epoch_current`, `plan_epoch_revise`,
  `plan_epoch_close`, `semantic_commit_write`, `semantic_commit_current`,
  `context_checkpoint_materialize`, `context_checkpoint_current`,
  `context_reanchor_ack`, `packet_register`, `packet_ack`,
  `context_promotion_propose`, `context_promotion_resolve`,
  `context_promotion_mark_applied`, `context_promotion_list`,
  `plan_epoch_rollover_prepare`, `plan_epoch_rollover_confirm`,
  `plan_epoch_rollover_apply`, `plan_epoch_rollover_current`, and
  `working_set_refs`.
- MCP server `python -m tools.hmasd_control_plane.mcp_server` and the
  `hmasd_observability` registration, including `control_plane_health`,
  `control_plane_doctor`, `control_plane_incidents`, `long_effect_observe`, and
  `mcp_instance_list`.
- Hook entry `python -m tools.codex_semantic_mvp.hook_entry --mode
  active|shadow`, doctor, trust-hooks, and topology probe entry points.
- Semantic CLI `python -m tools.codex_semantic_mvp.cli` commands
  `runtime-health`, `workflow-open`, `workflow-state`, `events-after`,
  `workflow-close`, `workflow-reconcile`, and `native-child-signal`.
- Context CLI `python -m tools.codex_context_lifecycle.cli` commands `doctor`,
  `sources`, `decisions-index`, `working-set`, `promotion-list`,
  `rollover-show`, and `gc`.
- Supervisor CLI `python -m tools.codex_supervisor` commands `doctor`,
  `schema`, `snapshot`, `serve`, `canary`, `timeline`, `managed
  list|show|create|adopt|verify|activate|turn|suspend|revoke`, `mailbox
  list|show|send-operator|dead-letter`, `scheduler once|status|serve`, and
  `wake show`, plus `tools.codex_supervisor.schema_capture`.
- Control-plane CLIs `python -m tools.hmasd_control_plane` (`doctor`,
  `incidents`, `long-effect run|observe`) and
  `python -m tools.hmasd_control_plane.boundary_cli` (`requirements`,
  `assignment`, `result`, `incident`, `preflight`, `manifest`, `runtime`,
  `lint`).
- The 32 named PowerShell entry points and seven extra wrappers in the
  relocation manifest.

There is no forwarding alias for any deleted name.

## Thin HMASD connector

The later `.codex/config.toml` replacement is one optional MCP connector:

```toml
[mcp_servers.hmasd_kernel]
command = "C:\\Users\\fires\\AppData\\Local\\HMASD\\execution-kernel\\bootstrap\\hmasd-kernel.exe"
args = [
  "serve-mcp",
  "--project-root", "C:\\Projects\\HMASD",
  "--runtime-root", "C:\\Users\\fires\\AppData\\Local\\HMASD\\execution-kernel\\runtime"
]
startup_timeout_sec = 15
tool_timeout_sec = 1800
enabled = true
required = false
enabled_tools = [
  "kernel_health",
  "operation_get",
  "intent_commit",
  "execution_commit",
  "run_event_append",
  "result_promote"
]
```

`kernel_health`, `operation_get`, and `run_event_append` are read/observation
surfaces and are not additional authorities. `run_event_append` can record a
fact under an existing G2 owner token but cannot create, alter, retry, resume,
or promote an operation. Only `intent_commit`, `execution_commit`, and
`result_promote` are synchronous authorization boundaries.

If the executable is absent or stopped, Codex startup and ordinary HMASD
read/edit/build/diagnosis/tests remain usable because the connector is not
required. A call that needs a new G2 effect fails with:

```json
{
  "action": "execution_commit",
  "protected_invariant": "G2 durable at-most-once execution identity",
  "observed_fact": "external kernel unavailable",
  "required_fact": "installed selected kernel responding at configured root",
  "override_class": "NONE_FOR_EFFECTFUL_OPERATION",
  "next_action": "restore the configured external kernel, then retry the same operation_id"
}
```

## G1/G2/G3 schema and API

All records use canonical UTF-8 JSON, sorted keys, integer timestamps in UTC,
SHA-256 content digests, and schema/version tags. Unknown fields are rejected.
The SQLite ledger uses one transaction per boundary and unique constraints on
the IDs and namespaces below.

### G1 — `intent_commit(Intent) -> IntentReceipt`

Required `Intent` fields:

```text
schema="hmasd.kernel.intent.v1"
intent_id                         # globally unique durable idempotency key
issued_at_utc
expires_at_utc|null
authority_ref                     # exact user decision/artifact reference
project_root="C:\Projects\HMASD"
scope                             # exact object/direction/component
effect_class                      # EXPERIMENT|PROVIDER|DESTRUCTIVE|PAID_EXTERNAL
operation_kind
budget={currency_limit,compute_limit,attempt_limit}
effect_constraints={allowed_targets,forbidden_actions}
intent_digest
```

Constraints: the authority reference must be durable and in scope; destructive,
external, and paid flags must be explicit; budget cannot be widened downstream;
same `intent_id` plus same digest is idempotent, while a changed digest is an
actionable conflict. The receipt contains `intent_id`, `intent_digest`,
`committed_at_utc`, and remaining budget. Actor, role, session, packet,
dashboard, model, or thinking identity is neither input nor permission.

### G2 — `execution_commit(RunSpec) -> ExecutionReceipt`

Required `RunSpec` fields:

```text
schema="hmasd.kernel.runspec.v1"
operation_id                      # globally unique at-most-once id
intent_id
intent_digest
manifest_ref
manifest_digest                   # immutable science/config manifest
science_identity
configuration_digest
rng_identity={algorithm,seed,stream_order}
command={argv,cwd,environment_allowlist}
foreground_owner_id               # exact one Operator/process owner
output_namespace
checkpoint_identity
frontier_identity
resume_policy                     # SAME_OPERATION_SAME_FRONTIER_ONLY
result_blind=true
resource_claims=[{resource_id,mode,quantity,conflict_domain}]
provider_transaction|null={provider,conversation_id,request_digest,attempt_ordinal,commit_unknown_policy="NO_RESEND"}
runspec_digest
```

One transaction verifies the G1 scope/budget, immutable manifest digest,
operation ID, exact foreground owner, output/checkpoint/frontier namespace,
result blindness, real resource conflicts, and provider no-resend identity,
then inserts the operation and claims all unique resources/namespaces. The
receipt is either `OPERATOR_READY` or an actionable refusal with the exact
action, invariant, observed fact, required fact, override class, and executable
next action. Same operation ID plus identical digest returns the original
receipt without launching or overwriting; any changed digest is rejected.

Ordinary tests, generic SANCheck, heartbeat, canary, Goal, dashboard, review,
provider opinion, archive shape, and duration estimate can be evidence embedded
in the manifest. They do not veto G2 unless they prove a concrete required
field false or a hard invariant violated.

### G3 — `result_promote(ResultPromotion) -> PromotionReceipt`

Required fields:

```text
schema="hmasd.kernel.result-promotion.v1"
promotion_id
operation_id
runspec_digest
manifest_digest
run_record_ref
run_record_digest
result_refs=[{path,digest,complete}]
checkpoint_identity
frontier_identity
provenance_chain=[{kind,ref,digest}]
claim_boundary_ref
claim_boundary_digest
completion={terminal=true,partial=false,mixed_revision=false}
promotion_target                  # interpretation|portfolio_use|publication
promotion_digest
```

G3 reads the immutable G2 record and accepts only a terminal, complete,
single-revision result whose hashes, output namespace, checkpoint/frontier,
and provenance chain match it. Partial, mixed-revision, missing, or mutated
output is rejected. Replaying an identical `promotion_id` is idempotent; a
changed digest conflicts. G3 checks integrity and claim-boundary presence but
does not interpret science or select Portfolio action.

## Atomic cutover order

1. **Freeze the cutover candidate.** Finish the external v1 executable,
   schemas, and replay fixture outside HMASD. Record its executable/schema
   digests. Do not connect it yet.
2. **Reach grandfathering frontiers.** Let UCOPE S1 reach its next safe atomic
   frontier. Preserve SGSP's read-only return and RCLE's scheduled event. Stop
   admitting new effects under the old system; this is a short cutover freeze,
   not a second permission service.
3. **Resolve direct consumers.** Rewrite the RISP launcher to the external
   G2/run-record API and resolve any new production import found by the final
   search. Do not add shims.
4. **Take one rollback snapshot.** Capture the exact bytes and hashes listed in
   the next section while old processes are stopped from accepting new work.
5. **Apply one filesystem/config transaction.** Move the eight source/test
   families and 32 scripts to the external legacy archive; delete the seven
   wrappers, actor map, hook templates, observer config, and old runtime paths;
   rewrite the project-facing contracts and maps; replace both old MCP
   registrations with the one external connector. Use staged paths followed by
   atomic renames on each volume. No old and new admission process runs
   simultaneously.
6. **Perform the single authorized MCP/App restart.** This is the first point
   the new connector can become live. Existing in-memory old servers must not
   survive it.
7. **Run the one acceptance replay.** Keep new real effects frozen. If the
   replay fails, use rollback because no new G2 record has been committed.
8. **Open G2.** After replay success and a zero-hit production import search,
   allow the first real new effect through the external kernel. After any new
   G2 commit, rollback to the old permission system is forbidden; repair the
   selected external version or atomically select a corrected external version
   while preserving the same operation IDs.

## Rollback snapshot and switch

Create exactly:

```text
C:\Users\fires\AppData\Local\HMASD\execution-kernel\snapshots\cutover-20260824-01\
```

The snapshot manifest contains SHA-256, size, and last-write time for:

- every file in the eight relocation families, the 32 scripts, and seven
  additional wrappers;
- `.codex/config.toml`, `.codex/semantic-actors.toml`, all three hook JSON
  files, and `.codex/app-server-observer.toml`;
- `AGENTS.md`, the three rewritten role files, `PROJECT_MAP.md`,
  `CURRENT_WORK.md`, `CONTEXT_SOURCE_REGISTRY.toml`,
  `LOW_INTRUSION_CONTROL_PLANE.md`, and `EXPERIMENT_EXECUTION_POLICY.md`;
- the RISP launcher and any production imports found by final search;
- a quiesced copy of `runtime/codex-semantic-mvp/**`,
  `runtime/hmasd-control-plane/**`, and existing external
  `C:\Users\fires\AppData\Local\HMASD\codex-supervisor\**`; and
- the pre-cutover and candidate `bootstrap\current.json` bytes plus the
  selected external executable/schema digests.

Rollback is permitted only while the post-cutover G2-commit counter is zero.
It restores the snapshot as one filesystem/config transaction, restores the
old external version pointer, and performs one restart. It never runs both
systems. Once a new G2 operation exists, use an atomic `current.json` version
switch to a fixed external kernel; do not reactivate repository-local gates.

## Grandfathering logic

- **UCOPE S1:** preserve the current science manifest, operation identity,
  foreground owner, output/checkpoint/frontier identity, and no-resend facts.
  It continues under its existing mechanism only through the next safe atomic
  frontier. Do not restart, rebind, assign G1/G2 retroactively, or inspect
  result/partial data. At the frontier, close its old runtime record into the
  rollback/provenance archive; any later new effect uses a new G1/G2 record.
- **SGSP:** the current CM conformance return is read-only and proceeds under
  its current owner without kernel dependency. Any later effectful action
  consumes a G1 decision and a new G2 identity; the existing return is not
  reinterpreted as permission.
- **RCLE:** retain the existing scheduled event, owner, time, and watched
  object unchanged. No intermediate polling or rescheduling is introduced.
  When it becomes actionable, ordinary read/diagnostic work remains available
  even if the kernel is stopped; only a new effectful operation needs G1/G2.
- **Other existing active operations:** apply the UCOPE rule. Completed or
  quiescent historical records remain immutable provenance and are never
  imported as live authority. No actor/session row is reclassified.

## One end-to-end acceptance replay

The external v1 package must contain this fixture:

```text
C:\Users\fires\AppData\Local\HMASD\execution-kernel\versions\v1\acceptance\authorized-idle-migration-launch-20260824.json
```

After cutover, with real effects still frozen, run exactly one command:

```powershell
& 'C:\Users\fires\AppData\Local\HMASD\execution-kernel\bootstrap\hmasd-kernel.exe' acceptance replay --fixture 'C:\Users\fires\AppData\Local\HMASD\execution-kernel\versions\v1\acceptance\authorized-idle-migration-launch-20260824.json' --scratch-root 'C:\Users\fires\AppData\Local\HMASD\execution-kernel\runtime\acceptance\cutover-20260824-01' --project-root 'C:\Projects\HMASD'
```

The one replay is successful only if it proves all eight later-cutover targets
in one isolated trace:

1. with the kernel child deliberately stopped, a fixture repo read/edit/build
   and ordinary test complete, while a synthetic new G2 call fails with the
   actionable unavailable-kernel response;
2. one G1 Intent persists once and is consumed directly, without actor,
   session, packet, queue, model, or review authorization;
3. one valid frozen RunSpec reaches `OPERATOR_READY`, and the fixture Operator
   performs the earliest legal isolated effect exactly once;
4. resume with the same operation/checkpoint identity returns the original
   receipt and does not duplicate work or overwrite output;
5. a second fixture RunSpec colliding on output/resource identity is rejected
   with the six required actionable-refusal fields, while missing heartbeat,
   canary, dashboard, and old-test evidence does not veto the valid run;
6. partial and mixed-revision fixture results fail G3, while the complete
   provenance-bound result is promoted once;
7. a repository search reports zero production references to retired packages,
   tests, hook templates, actor mapping, old MCP names, or deleted launchers;
   and
8. the authorized-idle incident path reaches the earliest safe action without
   permission ping-pong.

The replay produces one immutable JSON receipt with phase assertions, kernel
and schema digests, fixture digest, and `real_external_effect=false`. Legacy
test suites are not invoked and cannot approve cutover.

## Bounded future implementation cost

This estimate is for a separately authorized implementation and cutover, not
work performed in this preparation stage.

| Tranche | Engineer-days |
|---|---:|
| External bootstrap, signed/versioned selection, durable SQLite ledger | 3–4 |
| G1/G2/G3 schemas, transactions, refusals, CLI/MCP surface | 4–6 |
| HMASD connector/contracts, direct-consumer rewrite, deletion manifest | 2–3 |
| Acceptance replay, snapshot tooling, cutover rehearsal | 2–3 |
| Atomic production cutover and observation window | 1 |
| **Total** | **12–17 engineer-days** |

Expected elapsed time is 2–3 calendar weeks for one engineer, including one
rehearsal. The production cutover window is bounded to 2–4 hours. Snapshot
rollback, if no new G2 operation has committed, is bounded to 30–60 minutes.
The current legacy inventory is 232 files in the seven requested source/test
families plus 32 named scripts. The 15 additional control-plane tests and seven
wrappers are explicit scope additions required only to eliminate direct old
imports and entry points.

## Protected invariants and terminal boundary

```text
boundary_kind=ENGINEERING_BOUNDARY
continuity_state=IDLE_COMPLETE
active_worker=NONE_EXPECTED_FOR_PREPARATION_STAGE
continuity_owner=NONE_WITHIN_CM_PREPARATION_SCOPE
next_event=PORTFOLIO_OR_USER_DECISION_ON_SEPARATE_IMPLEMENTATION_TRANCHE
affected_scope=shared:minimal_control_plane_deselfhosting
affected_actions=future_external_kernel_implementation|file_move_delete|connector_cutover|restart|acceptance_replay
unaffected_scopes=UCOPE_S1_ACTIVE_SCIENCE_AND_IDENTITY|SGSP_CURRENT_READ_ONLY_CONFORMANCE_RETURN|RCLE_EXISTING_SCHEDULED_EVENT|all_science_allocation_provider_lease_coordinate_result_partial_git_deployment_flight_state
evidence_ref=docs/session/HMASD_MINIMUM_VIABLE_CONTROL_PLANE_DESELFHOSTING_CM_MIGRATION_PREPARATION_20260824.md
no_current_science_or_run_change=true
no_duplicate_effect=true
no_result_or_partial_access=true
no_provider_send=true
no_git_action=true
```

This CM stage is complete. Implementation, deletion, restart, replay execution,
and cutover remain unperformed and require a separate exact authorization.
