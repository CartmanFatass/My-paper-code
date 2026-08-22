# HMASD Control-Plane Observability V1 Acceptance

```text
record_date=2026-08-20
schema=HMASD_CONTROL_PLANE_OBSERVABILITY_ACCEPTANCE_V1
implementation_status=ACCEPTED
rollout_status=SHADOW_MCP_ACTIVE
operational_exception=PREEXISTING_SGSP_PRODUCTION_ADVANCED_BEFORE_ROOT_SAFE_STOP
```

## Accepted surface

- Semantic MCP exposes only `ANY_REPORT`, `ALL_REQUIRED_RETURNED`,
  `OPEN_OBLIGATION_CHANGED`, and `WORKFLOW_QUIESCENT`; `state_version` and
  `await_cursor` are independent.
- Explicit paused-only `workflow-reconcile` supports read-only dry-run,
  version/cursor compare-and-swap, idempotent rollover receipts, and preserves
  reports, events, and intakes without manufacturing Root intake.
- Hooks run in `ShadowMcp`: they write audit/probe records only, create no
  semantic workflow/task/obligation, inject no continuation context, and never
  block Stop or SubagentStop. Stale cached `--mode active` invocations fail
  neutral or downgrade to shadow according to the exact live configuration.
- `tools.hmasd_control_plane` provides read-only `doctor` and `incidents`
  commands across semantic SQLite, supervisor SQLite, Agentify ledger,
  research-event JSONL, and long-effect run roots.
- `HMASD_LONG_EFFECT_V1` uses one synchronous owner and exactly
  `experiment.json`, `owner.json`, `stdout.log`, `stderr.log`, and
  `terminal.json`. It has no detach, Windows Job, READY/CANCELLED race,
  heartbeat, retry, or automatic recovery mechanism.
- RISP retains its exact lease/certificate/source/frontier validation while
  delegating generic process ownership and records to the shared long-effect
  implementation.
- Agentify rejects an empty continuation baseline before composer replacement
  and Send at both controller and transport admission. The guarded record has
  `failureStage=before_composer_write`, `noClickProven=true`, and zero send
  counters. First binding with an empty baseline remains legal.

## Legacy semantic rollover

The following workflows were reconciled individually while hooks were disabled
and the pause sentinel was present:

| Workflow | Receipt |
| --- | --- |
| `wf_361f389de473431a88e1b7dd217929a5` | `receipt_6b7b79549cf04fdebdb30f2c2be6d1bc` |
| `wf_b4cce2894f5a4e26997a8057bf29dcd2` | `receipt_a3c977a65be744a9a9a5da2ba12c2528` |
| `wf_c53770d4e5f84bf7977258ed02be29d9` | `receipt_df8e247557e54cbbae969a3cc10e26f8` |
| failed pre-repair canary `wf_0efc209f05ae4acdb4ff5cf9368127ee` | `receipt_383881f94b774e0f8e267c9ceb7ee04b` |

Final semantic counters are seven workflows, zero active workflows, zero open
tasks, zero open obligations, 111 preserved reports, and 1,418 preserved
events. A live legal `ANY_REPORT` wait at cursor 1,418 returned
`TIMEOUT_NO_DISPOSITION` and did not change the cursor.

## Validation

| Scope | Result |
| --- | --- |
| Semantic MCP/hooks/reconcile/activation | `240 passed` under final live ShadowMcp |
| Doctor, incident index, and long-effect | `42 passed` |
| RISP shared long-effect adapter | `11 passed` |
| Agentify targeted empty-baseline guard | all targeted controller/transport/HTTP cases passed |
| Agentify affected full suite | 158 passed; four pre-existing environment/fixture failures remained outside the guard change |
| Shadow hook canary | one audit row added; semantic DB counters unchanged; no blocking decision |
| 90-second long-effect canary | one child, exit 0, five complete records, zero duplicate child, zero partial record |
| RestorePause drill | disable restored `hooks=false` plus sentinel; re-enable reproduced ShadowMcp |

The first Root semantic rerun used an unnecessarily long `--basetemp` and hit
the Windows PowerShell 5.1 path limit in one activation fixture. The complete
suite was rerun with a short unique `C:\hf_*` base and passed 240/240.

## Final live state

```text
hooks=Shadow
MCP=enabled
semantic_pause_sentinel=not_active
automatic_wake=false
scheduler_serve=false
Stage5=false
provider_sends_by_this_rollout=0
automatic_retries=0
matching_scientific_processes_at_acceptance=0
```

The final read-only snapshots are runtime-only and disposable:

- `runtime/hmasd-control-plane/doctor-final-20260820.json`
- `runtime/hmasd-control-plane/incidents-final-20260820.json`

Doctor reports zero semantic delivery debt, zero missing long-effect terminals,
zero partial long-effect envelopes, and one complete long-effect run.

## Acceptance thresholds

| Threshold | Observed |
| --- | --- |
| `unknown_await_condition_failures=0` | PASS |
| `legacy_open_obligations=0` | PASS |
| `legacy_open_tasks=0` | PASS |
| `agentify_empty_baseline_send_actions=0` | PASS |
| `long_effect_duplicate_children=0` | PASS |
| `partial_immutable_records=0` | PASS |
| `shadow_blocking_decisions=0` | PASS |
| `automatic_retries=0` | PASS |
| `provider_sends=0` | PASS for this rollout |
| `rollback_failures=0` | PASS |
| `scientific_state_changes=0` | LITERAL WINDOW EXCEPTION: pre-existing SGSP seed workers advanced before Root discovered them; Root then fenced new scheduling and closed a result-blind safe boundary. No control-plane canary caused scientific activity. |

The SGSP exception is retained, not deleted or reinterpreted: 19 complete
blinded seed packets, four disjoint non-evaluable frontiers, one unmaterialized
seed, no analysis, and zero active seed/wrapper/scheduler processes. It is an
operational authority exception, not a scientific result or portfolio change.

## Known limitations and fences

- The optional external supervisor database is absent at
  `%LOCALAPPDATA%\HMASD\codex-supervisor\state.sqlite3`; doctor therefore
  reports overall `UNAVAILABLE` without creating it.
- Seventeen historical Agentify operations have explicit ambiguous-submission
  markers and remain indexed as observe-only incidents. Their prompt/response
  content is not read.
- `RCLE-CPC-R04-PRO-RESULT-CONVERGENCE-20260820-01` remains permanently
  observe-only/no-resend. Reload and baseline validation did not mutate its
  ledger or archive and performed no provider send.
- Four unrelated Agentify full-suite failures remain: two stale fixture
  expectations and two Windows symlink-permission mappings. Targeted baseline
  guard coverage passes.
- True wake of an ended Codex task is not provided. Scheduler serve, automatic
  wake, Stage 5, Agents SDK, and automatic retry remain disabled and require a
  future separate authorization.
- Host loss leaves `owner.json` without `terminal.json`; doctor reports that
  fact but never restarts the command. Recovery always uses a fresh run root
  and the domain runner's own atomic frontier.

## Git integration

- HMASD base implementation commit: `f53e2d0c add observable control-plane v1`.
- The semantic fail-safe/test-isolation and this acceptance record are in the
  follow-up HMASD commit containing this file.
- Agentify guard commit: `449252a fix: reject empty continuation baselines` on
  `codex/hmasd-strict-review-transport`.
- No push was performed; publication requires explicit later authorization.

Future control-plane repairs use the fixed loop:
`incident -> minimal reproduction -> minimal repair -> focused test -> harmless
live canary -> acceptance`. Doctor and incident snapshots remain runtime state,
never canonical scientific state.

## Native-child semantic wait bridge follow-up — 2026-08-20

The V1.1 follow-up adds an explicit, opt-in bridge for a native EM/CM child that
Root wants to await through the semantic event cursor. Root first registers the
child with `native_child_register`; the returned content-free signal command is
included in that exact child assignment. The child emits exactly one
`COMPLETED` or `ANOMALY` signal immediately before its ordinary native return.
The signal only creates `NATIVE_CHILD_REPORT_AVAILABLE`; it contains no result
text and does not imply a scientific disposition. Root then uses
`workflow_wait_plan` and, only for `WAIT_SEMANTIC_EVENT`, calls
`workflow_await_event` with the returned `await_cursor`; the formal result still
comes from `collaboration.wait_agent`.

Validation:

```text
tests/codex_semantic_mvp/test_native_wait_bridge.py
tests/codex_semantic_mvp/test_long_wait.py
tests/codex_semantic_mvp/test_mcp_tools.py
tests/hmasd_control_plane/test_stdio_servers.py
result=37 passed
python= C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
basetemp= C:/Projects/HMASD/.pytest-basetemp-native-bridge-20260820-02
```

The bridge is not automatic wake, scheduler serve, retry, or task resurrection.
Unbridged children continue to use native `collaboration.wait_agent`; cancelled
semantic workflows reject bridge registration/signals. No live semantic DB,
scientific runner, provider operation, lease or result was changed by this
follow-up. The bridge is therefore eligible for new EM/CM assignments only;
already-running children retain their existing native wait route.
