# HMASD agent model/cost routing v1

```text
document_kind=owner_independent_model_cost_runbook
scope=shared:agent-model-cost-routing
cp0_root_model=populate_from_cost_script_before_cp1
cp0_root_effort=populate_from_cost_script_before_cp1
steady_root=gpt-5.6-luna/high
root_integration_recovery=gpt-5.6-terra/high
novel_governance=gpt-5.6-sol/high
routine_implementer=hmasd-implementer-terra|gpt-5.6-terra/high
semantics_critical_implementer=hmasd-implementer|gpt-5.6-sol/high
runtime_records=runtime/codex-semantic-mvp/agent-model-cost-routing
```

## Purpose and invariants

This runbook applies the shared steady/surge routing policy and measures two
prospective cost canaries without duplicating work. It is owner-independent:
the current authorized Root or CM can follow it, and no named session is made
the permanent owner. It is not a workflow state machine, readiness chain,
approval ledger, or scientific gate.

Model choice allocates capability only. It does not change authority, topology,
write scope, scientific meaning, technical acceptance, user contact, Git
authority, or evidence requirements. Root alone performs Git integration.
Existing active agents are never migrated mid-turn; every route assignment or
promotion applies only to a future task or turn. EM remains Sol-max, CM remains
Sol-high, and mechanical and Experiment Operator work remains Luna. Reviewer
and Verifier remain optional and risk-driven, never a routine triple chain.

Use only the existing task classes `simple_mechanical`, `ordinary_task`, and
`high_difficulty`. Their selection and promotion triggers are defined in
`.agents/roles/ROOT.md`; the Terra-versus-Sol implementation boundary and
non-overlapping review rules are defined in
`.agents/roles/CODE_PROJECT_MANAGER.md`. No model fallback is automatic,
including when a model is unavailable. Record the unavailable route and leave
the new work unstarted for its assigning owner. The exact Project Scout
capacity fallback in `AGENTS.md` is the only exception.

## Runtime-only evidence records

All measurement artifacts live beneath the already ignored directory
`runtime/codex-semantic-mvp/agent-model-cost-routing/`. They are noncanonical,
deletable runtime evidence and must not be treated as project or workflow state.
Raw `state_5.sqlite` and rollout JSONL files remain read-only.

Use these files:

- `quality.jsonl`: one final owner-recorded object per canary task;
- `join-manifest.json`: the explicit experiment, arm, task-class, and thread-ID
  cohort lists used for cost joins, plus exclusions and their reasons;
- `historical-summary.json`: the script-backed eligible historical snapshot;
- `canary-<experiment>-<task_class>-compare.json`: script-backed comparisons.

The join manifest is a plain audit object, not a controller. Its minimum shape
is:

```json
{
  "schema_version": 1,
  "cp0_root_thread_id": "<exact-current-root-thread-id>",
  "cp0_root_model": "<exact-cost-script-output-model>",
  "cp0_root_effort": "<exact-cost-script-output-reasoning_effort>",
  "historical_cost_exclusions": [
    {"thread_id": "<thread_id>", "reason": "<exact_parser_or_unit_reason>"}
  ],
  "filters": {
    "<snapshot-name>": {
      "kept_thread_ids": ["<thread_id>"],
      "deletions": [{"thread_id": "<thread_id>", "reason": "<exact_reason>"}]
    }
  },
  "experiments": {
    "A": {
      "ordinary_task": {
        "control": ["<thread_id>"],
        "experimental": ["<thread_id>"]
      }
    }
  }
}
```

Experiment B and any other eligible exact task-class stratum use the same
explicit list shape. Every row deleted from a runtime filtered SQLite snapshot
must appear under that snapshot's `filters` entry with its exact reason.

Optional metadata in a quality row may include `schema_version`, `canary_id`,
`thread_id`, `arm`, `recorded_at`, and `exclusion_reason`. Quality decisions use
only these explicitly owner-recorded fields:

```json
{
  "task_class": "ordinary_task",
  "model": "gpt-5.6-terra",
  "reasoning_effort": "high",
  "first_pass_accepted": true,
  "material_defect_count": {"critical": 0, "high": 0, "medium": 0, "low": 0},
  "rework_turns": 0,
  "rollback_used": false,
  "unauthorized_scope_or_semantic_escape": false,
  "complete_outcome": true,
  "accepting_owner": "<explicit-authorized-owner>"
}
```

The arm and thread metadata select an explicit cohort; they are not quality
proxies. Never infer quality from prose, test results, thread names, model
telemetry, or cost telemetry. Exclude a task that lacks an explicit authorized
quality owner and owner-recorded quality row. Join cost output to quality only
through the manifest's explicit `thread_id` lists. Never calculate cost,
tokens, duration, or their ratios outside the cost script.

Each severity count includes only a material defect that the accepting owner
explicitly attributes to the routed task outcome. This makes an experimental
arm's nonzero critical count the required attribution record without inventing
another quality field.

## CP0 historical baseline

Before CP1 activation, take one observational snapshot from the long local
Codex history. Group mechanically eligible completed units by exact model +
reasoning effort + role. This cost-only distribution does not require a quality
row. A task-class or quality comparison, however, includes only tasks with an
explicit authorized quality row supplying one of the three exact `task_class`
values. If no such rows exist, report zero eligible quality/task-class baseline;
never label historical tasks retrospectively or infer class or quality.
Historical tasks and configurations differ, so this baseline describes cost,
tokens, and duration only; it cannot support causal quality claims or substitute
for the prospective canaries.

The naive full-project command has been directly observed to fail closed with
`TOKEN_COUNTER_REGRESSED`, initially at thread
`019fec57-cea2-7f31-8595-8e9ca929b0dd`. The observed parser-failure exclusions
are currently:

- `TOKEN_COUNTER_REGRESSED`: `019fec57-cea2-7f31-8595-8e9ca929b0dd`,
  `019ff336-ddf4-7751-b1da-99757fddbf64`,
  `019ff34d-2d42-7883-b199-eabff2997320`,
  `019ff3c6-6728-7240-b7ab-628445f0ed44`,
  `019ff3dc-1bf0-7ad1-bffe-a53f1dea603d`,
  `019ff451-bed9-7953-8477-41b93393c4c6`,
  `019ff4b6-cf12-72c3-a5ae-26f5f529ddf2`,
  `019ff50e-5b7d-7f62-9073-54482042061b`, and
  `019ffa76-2b1f-7f50-bed0-bab4788f5369`;
- malformed `total_tokens`: `01a009fa-30eb-7de2-8c8d-4e93e4419070`.

This list is observed evidence, not an exhaustive hardcoded allow/deny list.
Before filtering, seed `historical_cost_exclusions` in the join manifest with
every ID above and its stated reason.
If the script reports another malformed or token-counter-regression cohort,
preserve its exact thread ID and reason in `join-manifest.json`, rebuild the
runtime snapshot from the raw database, delete that exact row from the copy,
and rerun. Do not manually reconstruct counters or partially salvage a rejected
thread.

The script excludes incomplete units and mixed-configuration task units; a
completed turn from a persistent or mixed-history thread is eligible only as
the exact per-turn model/effort unit reported by the script. Malformed units and
token-counter-regression cohorts are removed from the runtime copy and logged.
`UNPRICED` units remain eligible for token and duration reporting and are
excluded only from USD ratios. Tasks without explicit authorized quality rows
remain eligible for the historical cost-only role/model/effort distribution,
but are excluded from every task-class and quality comparison. The script
output is the sole cost/token/duration fact source.

Use these exact script-backed PowerShell patterns. The first command is only a
fail-closed diagnostic; do not treat a partial/empty redirect as a baseline.

```powershell
$Python = 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe'
$CostScript = 'C:/Users/fires/.agents/skills/codex-task-cost-analysis/scripts/codex_task_cost_analysis.py'
$RuntimeDir = 'C:/Projects/HMASD/runtime/codex-semantic-mvp/agent-model-cost-routing'
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
& $Python $CostScript summary --project 'C:/Projects/HMASD' --unit both --cost-scope self --format json
```

Do not rerun historical `summary` with explicit `--thread-id` values: that
selection recursively includes descendants. Instead, keep the raw database and
rollouts read-only, use the required HMASD Python interpreter and stdlib
`sqlite3` to make a runtime snapshot, and delete from that copy only the exact
manifest-listed parser-failure rows. The snapshot and deletion commands perform
no cost, token, or duration arithmetic. Rebuild from raw after every changed
exclusion list; never edit an earlier filtered copy in place.
Before every `$SnapshotCode` call, delete only that command's exact named
runtime snapshot with `-LiteralPath` beneath the fixed `$RuntimeDir`, then
recreate it. Never pass `$RawStateDb` to `Remove-Item` or otherwise modify the
raw database.

```powershell
$RawStateDb = 'C:/Users/fires/.codex/state_5.sqlite'
$ManifestPath = "$RuntimeDir/join-manifest.json"
$HistoricalStateDb = "$RuntimeDir/historical-filtered-state.sqlite"
$SnapshotCode = @'
import sqlite3, sys
source = sqlite3.connect("file:" + sys.argv[1].replace("\\", "/") + "?mode=ro", uri=True)
target = sqlite3.connect(sys.argv[2])
source.backup(target)
target.close()
source.close()
'@
if (Test-Path -LiteralPath $HistoricalStateDb) {
    Remove-Item -LiteralPath $HistoricalStateDb -Force
}
& $Python -c $SnapshotCode $RawStateDb $HistoricalStateDb

$DeleteManifestExclusionsCode = @'
import json, sqlite3, sys
database, manifest_path = sys.argv[1:3]
with open(manifest_path, encoding="utf-8") as stream:
    manifest = json.load(stream)
deletions = manifest["historical_cost_exclusions"]
thread_ids = [item["thread_id"] for item in deletions]
connection = sqlite3.connect(database)
present = {row[0] for row in connection.execute("SELECT id FROM threads")}
missing = sorted(set(thread_ids) - present)
if missing:
    raise SystemExit("manifest exclusion IDs absent from snapshot: " + ",".join(missing))
connection.executemany("DELETE FROM threads WHERE id = ?", ((item,) for item in thread_ids))
connection.commit()
connection.close()
manifest.setdefault("filters", {})["historical_cost"] = {
    "kept_thread_ids": sorted(present - set(thread_ids)),
    "deletions": deletions,
}
with open(manifest_path, "w", encoding="utf-8") as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2)
'@
& $Python -c $DeleteManifestExclusionsCode $HistoricalStateDb $ManifestPath

& $Python $CostScript summary --state-db $HistoricalStateDb --project 'C:/Projects/HMASD' --role unlabeled_root --role hmasd-implementer --role hmasd-implementer-terra --unit both --cost-scope self --format json | Set-Content -Encoding utf8 "$RuntimeDir/historical-summary.json"
```

The lack of a quality row does not remove a mechanically eligible unit from
that cost-only summary. For an exact CP0 Root observation or an exact
role/task-class snapshot, create a fresh runtime snapshot and keep only the
explicit owner-recorded IDs. The following filter records every removed row in
the join manifest; its deletion is selection only and performs no telemetry
arithmetic.

```powershell
$KeepOnlyCode = @'
import json, sqlite3, sys
database, manifest_path, snapshot_name, reason, *keep_ids = sys.argv[1:]
keep = set(keep_ids)
connection = sqlite3.connect(database)
all_ids = {row[0] for row in connection.execute("SELECT id FROM threads")}
missing = sorted(keep - all_ids)
if missing:
    raise SystemExit("explicit keep IDs absent from snapshot: " + ",".join(missing))
deleted = sorted(all_ids - keep)
connection.executemany("DELETE FROM threads WHERE id = ?", ((item,) for item in deleted))
connection.commit()
connection.close()
with open(manifest_path, encoding="utf-8") as stream:
    manifest = json.load(stream)
manifest.setdefault("filters", {})[snapshot_name] = {
    "kept_thread_ids": sorted(keep),
    "deletions": [{"thread_id": item, "reason": reason} for item in deleted],
}
with open(manifest_path, "w", encoding="utf-8") as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2)
'@

$Cp0RootThreadId = '<exact-current-root-thread-id>'
$Cp0RootStateDb = "$RuntimeDir/cp0-root-filtered-state.sqlite"
if (Test-Path -LiteralPath $Cp0RootStateDb) {
    Remove-Item -LiteralPath $Cp0RootStateDb -Force
}
& $Python -c $SnapshotCode $RawStateDb $Cp0RootStateDb
& $Python -c $KeepOnlyCode $Cp0RootStateDb $ManifestPath 'cp0_current_root' 'not_cp0_current_root_thread' $Cp0RootThreadId
$Cp0StartLocal = '<pre-CP1-observation-window-start>'
$Cp0EndLocal = '<pre-CP1-observation-window-end-exclusive>'
& $Python $CostScript summary --state-db $Cp0RootStateDb --project 'C:/Projects/HMASD' --unit both --cost-scope self --start-local $Cp0StartLocal --end-local $Cp0EndLocal --format json --label cp0_current_root | Set-Content -Encoding utf8 "$RuntimeDir/cp0-root-observation.json"
```

The pre-CP1 Root observation must contain exactly one eligible completed-turn
model/effort group. Copy those exact script-output strings, without inference,
to `cp0_root_model` and `cp0_root_effort` in `join-manifest.json`. If the window
has zero or multiple groups, refine the prospective CP0 observation window and
rerun before CP1; do not choose a comparator from thread metadata or prose.

For each task class with explicit authorized quality rows, use a fresh snapshot
and the same keep-only filter, then label the script output as
`<role>/<task_class>` so the grouping retains both. Every kept ID must have that
exact owner-recorded role and task class. When the list is empty, record zero
eligible quality/task-class baseline and do not run or invent a cohort.

```powershell
$Role = 'hmasd-implementer'
$TaskClass = 'ordinary_task'
$EligibleTaskClassThreadIds = @('<owner-recorded-thread-id-1>', '<owner-recorded-thread-id-2>')
$TaskClassStateDb = "$RuntimeDir/historical-$Role-$TaskClass-filtered-state.sqlite"
if (Test-Path -LiteralPath $TaskClassStateDb) {
    Remove-Item -LiteralPath $TaskClassStateDb -Force
}
& $Python -c $SnapshotCode $RawStateDb $TaskClassStateDb
& $Python -c $KeepOnlyCode $TaskClassStateDb $ManifestPath "historical-${Role}_${TaskClass}" "not_in_explicit_owner_recorded_${Role}/${TaskClass}_cohort" @EligibleTaskClassThreadIds
& $Python $CostScript summary --state-db $TaskClassStateDb --project 'C:/Projects/HMASD' --role $Role --unit both --cost-scope self --format json --label "$Role/$TaskClass" | Set-Content -Encoding utf8 "$RuntimeDir/historical-$Role-$TaskClass-summary.json"
```

## Prospective matched canaries

Prospective quality records begin only after the applicable checkpoint is
activated: experiment A after CP1 and experiment B after CP2. Each populated
experiment/task-class stratum has its own sample boundary: at least 10 eligible
tasks with balanced arms and at least 5 eligible tasks in each arm, and a cap
of 20 prospectively assigned canary tasks in that stratum. Do not duplicate a
task. Before dispatch, record its exact task class and assign the next arm by
alternating within that task-class stratum; where more than one stratum is
eligible, rotate strata without combining their samples. Never choose an arm
after seeing its outcome.

Before a populated stratum has 10 eligible tasks and at least 5 in each arm,
report only its eligible, excluded, and assigned counts by arm plus any
hard-safety event; do not issue an economic or quality conclusion. At the
20-assigned-task per-stratum cap, a stratum with fewer than 10 eligible total or
fewer than 5 eligible in either arm is non-passing. No undersized or failing
stratum may support activation or be hidden by pooling with another stratum.

For experiment A, control is the exact CP0 current-Root comparator recorded as
`<join-manifest.cp0_root_model>/<join-manifest.cp0_root_effort>` from
`cp0-root-observation.json`, and experimental is steady Operational Root
`gpt-5.6-luna/high`. The control must not be hardcoded before that script-backed
observation. For experiment B, control is
`hmasd-implementer`/`gpt-5.6-sol/high`, and experimental is
`hmasd-implementer-terra`/`gpt-5.6-terra/high`. Experiment A admits future
steady Root tasks classified `simple_mechanical` or `ordinary_task` that do not
trigger Terra integration/recovery or Sol novel-governance promotion.
Experiment B admits future `ordinary_task` implementation packages that satisfy
the routine frozen-semantics boundary. A semantics-critical package is not
randomized and always takes the Sol route.

Pre-dispatch exclusions are: an already-active agent; no explicit accepting
owner; missing exact task class; mixed model/effort configuration; external or
irreversible side effects that prevent a comparable rollback; a Root promotion
trigger for A; or a semantics-critical trigger for B. Post-dispatch eligibility
requires a complete task turn, a single recorded model/effort, a well-formed
cost-script cohort, and the explicit owner quality row. Preserve every later
exclusion and reason; never replace an excluded sample opportunistically in a
way that breaks prospective alternation. Safety-triggered rollbacks remain in
the quality set rather than being excluded.

Before comparison, validate arm identity for every otherwise eligible quality
row. In A, each control row's explicit `model` and `reasoning_effort` must equal
the manifest-recorded CP0 Root pair, and each experimental row must equal
`gpt-5.6-luna/high`. In B, each control row must equal
`gpt-5.6-sol/high`, and each experimental row must equal
`gpt-5.6-terra/high`. Then require the cost script to report exactly one
model/effort group per arm and require that group to match the same assigned
identity. Exclude any row or cohort mismatch with its explicit reason in the
join manifest. A mismatch cannot count toward the per-stratum sample minimum or
activation.

Build compare commands only from the manifest's explicit eligible thread IDs.
The same template must be run for `A/simple_mechanical` and
`A/ordinary_task` when those strata are populated, and for
`B/ordinary_task`. Run one comparison per experiment and exact task-class
stratum; combine neither costs nor ratios manually.

```powershell
$Experiment = 'A' # Set to 'A' or 'B'.
$TaskClass = 'ordinary_task' # Or 'simple_mechanical' for populated experiment A.
$ControlThreadIds = @('<exact-manifest-control-thread-id-1>', '<exact-manifest-control-thread-id-2>')
$ExperimentalThreadIds = @('<exact-manifest-experimental-thread-id-1>', '<exact-manifest-experimental-thread-id-2>')
$CompareArgs = @($CostScript, 'compare', '--unit', 'task', '--cost-scope', 'self', '--format', 'json', '--label-a', 'control', '--label-b', 'experimental')
foreach ($ThreadId in $ControlThreadIds) { $CompareArgs += @('--cohort-a', $ThreadId) }
foreach ($ThreadId in $ExperimentalThreadIds) { $CompareArgs += @('--cohort-b', $ThreadId) }
& $Python @CompareArgs | Set-Content -Encoding utf8 "$RuntimeDir/canary-$Experiment-$TaskClass-compare.json"
```

## Metrics, thresholds, and decision

At every sample, hard-roll back the affected experimental route prospectively
on either (1) any `unauthorized_scope_or_semantic_escape=true`, or (2) any
critical material defect attributable by the accepting owner to that
experimental route. Preserve the row and stop assigning new tasks to that
experimental arm. Do not migrate the active task or erase its evidence.

For each populated stratum, at 10 eligible tasks with at least 5 per arm, and
again before its 20-assigned-task cap if needed, compare the owner-recorded
quality fields and the cost script's mean and median self-cost, total tokens,
and duration. The experimental arm passes the quality boundary only if all of
the following hold:

- zero unauthorized scope/semantic escapes and zero critical defects;
- complete-outcome and first-pass-accepted rates are each no more than 10
  percentage points below control;
- total high-severity defects do not exceed control, mean medium defects are no
  more than 0.25 per task above control, and mean low defects are no more than
  0.50 per task above control;
- rollback-used rate is no more than 10 percentage points above control; and
- median rework turns are no more than 1 above control and mean rework turns
  are no more than 0.5 above control.

For priced groups, the economic boundary requires the script-generated median
self-cost ratio to be at most `0.85` and the experimental script-generated mean
self-cost to be strictly below control. For any `UNPRICED` group, make no USD
ratio or USD decision; instead require the script-generated median-token ratio
to be at most `0.85` and experimental mean total tokens to be strictly below
control. In either case, script-generated median-token and median-duration
ratios must each be at most `1.25`, while experimental mean tokens and mean
duration must each be no greater than control. Thus mean and median cost,
tokens, and duration are all compared without arithmetic outside the script.
These thresholds apply separately to A and B and to every reported task-class
stratum; do not hide a failing stratum in a pooled result.

At a stratum's 10-eligible-task minimum, activation is decisive only when it has
at least 5 eligible tasks per arm and every safety, quality, identity, and
applicable economic threshold passes. A non-hard-safety threshold failure or a
result too close to call continues prospectively while preserving alternation,
but never beyond 20 assigned tasks in that stratum. At that cap, the stratum
passes only if it still has at least 10 eligible total, at least 5 eligible per
arm, exact arm identities, and every threshold passes. Otherwise that stratum
is non-passing and the route is prospectively reversed to its checkpoint
comparator. Full activation requires every populated stratum for that route to
pass separately. Reviewer or Verifier may be used only for a concrete
independent risk under the CM policy; the canary never creates automatic review
or re-review.

## CP0--CP4 integration and rollback boundaries

These checkpoints are integration and rollback boundaries, not runtime states,
approval gates, or a workflow lifecycle. Root alone performs each Git
integration or reversal; this runbook author performs none.

- **CP0 baseline.** Policy/test paths: `AGENTS.md`, `.agents/roles/ROOT.md`,
  `.agents/roles/CODE_PROJECT_MANAGER.md`,
  `docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md` (absent at the CP0
  boundary), `tests/hmasd_model_routing_test.py`, and
  `tests/hmasd_two_level_agent_topology_test.py`. Read-only inputs are
  `C:/Users/fires/.codex/state_5.sqlite` and their rollout JSONL paths. Before
  CP1, create only runtime filtered snapshots, script output, and the join
  manifest. Comparator routes are Root
  `<join-manifest.cp0_root_model>/<join-manifest.cp0_root_effort>` and the
  Sol-high implementer. Reversal: CP0 has no prior checkpoint and requires no
  source action; Root remains at the exact manifest-recorded Root comparator
  and Sol-high implementer. Runtime evidence may be deleted independently.
- **CP1 Root-only.** Policy/test paths: `AGENTS.md`, `.agents/roles/ROOT.md`,
  `docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md`,
  `tests/hmasd_model_routing_test.py`, and
  `tests/hmasd_two_level_agent_topology_test.py`;
  `.agents/roles/CODE_PROJECT_MANAGER.md` remains at CP0. Activate only
  prospective experiment A after the CP0 snapshot and manifest comparator are
  complete. Reversal: at the Root Git revert boundary, restore each named CP1
  policy/test path to its exact CP0 version, remove the runbook because it was absent
  at CP0, stop new Luna Root assignments, and route future Root work to the
  exact manifest-recorded CP0 model/effort. Retain runtime evidence and never
  migrate an active turn.
- **CP2 CM/leaf routing.** Integrated policy/test paths: `AGENTS.md`,
  `.agents/roles/ROOT.md`, `.agents/roles/CODE_PROJECT_MANAGER.md`,
  `docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md`,
  `tests/hmasd_model_routing_test.py`, and
  `tests/hmasd_two_level_agent_topology_test.py`. Activate prospective
  experiment B. Reversal: at the Root Git revert boundary, restore all six
  named paths to their exact CP1 versions, stop new Terra routine-implementer
  assignments, and route future implementation to
  `hmasd-implementer`/`gpt-5.6-sol/high`; do not migrate active agents.
- **CP3 review policy.** Integrated policy/test paths: `AGENTS.md`,
  `.agents/roles/ROOT.md`, `.agents/roles/CODE_PROJECT_MANAGER.md`,
  `docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md`,
  `tests/hmasd_model_routing_test.py`, and
  `tests/hmasd_two_level_agent_topology_test.py`. Reversal: at the Root Git
  revert boundary, restore all six named paths to their exact CP2 versions,
  removing the CP3 non-overlap additions only; model canaries and retained
  runtime evidence remain unchanged.
- **CP4 full activation.** Integrated policy/test paths: `AGENTS.md`,
  `.agents/roles/ROOT.md`, `.agents/roles/CODE_PROJECT_MANAGER.md`,
  `docs/project/HMASD_AGENT_MODEL_COST_OPTIMIZATION_V1.md`,
  `tests/hmasd_model_routing_test.py`, and
  `tests/hmasd_two_level_agent_topology_test.py`. Integrate only routes whose
  per-populated-stratum canary meets every full-activation threshold. Reversal: at the
  Root Git revert boundary, restore all six named paths to their exact CP3
  versions and route future work according to CP3; leaves active turns
  untouched. Further rollback proceeds one named checkpoint boundary at a time.
