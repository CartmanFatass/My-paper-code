# OMP Autonomous Multi-Direction Research Workflow Implementation Plan

## Metadata

- Status: implemented; amended 2026-08-25 for Root-owned Portfolio control and
  a two-level subagent tree.
- Original date: 2026-08-24.
- Owning concept:
  `docs/plans/2026-08-24-omp-autonomous-multidirection-research-concept.md`.
- Root, EM, and CM continuous Advisors are disabled; only Implementer leaves
  opt in, while deep-tree review uses explicit frozen checkpoint bundles.
- Target integration branch: `omp/workflow`.

## 1. Outcome and acceptance boundary

The implementation is complete when one resumed Root OMP session can:

1. reconcile durable portfolio and direction state directly in Root;
2. maintain an uncapped evidence-backed active queue while bounding execution by resources;
3. revive bounded EM and CM logical sessions instead of polling;
4. execute scientific research, engineering, local CPU runs, external review,
   Git integration, recovery, and compact reporting through a two-level
   subagent topology;
5. preserve one authoritative source for every scientific, workflow, run,
   external-send, and Git fact;
6. expose a read-only local Dashboard without making it a control surface; and
7. stop only at IDLE, COMPLETE, an explicit user boundary, or an exhausted safe
   recovery route.

The implementation must not introduce DVC, MLflow, Prefect, Airflow, Temporal,
Dagster, a workflow database, event sourcing, a recurring primary-agent model
poller, a HMASD OMP extension, tracked raw run directories, Advisor approval
authority, or Dashboard write controls.

The current headless Advisor implementation is a provisional baseline:

```text
.omp/advisors/*
scripts/run_hmasd_advisor.py
tests/run_hmasd_advisor_test.py
```

Phase 1 replaces it cleanly with `.omp/WATCHDOG.md` and native per-agent-type
Advisor configuration. The three profile documents, dispatcher, and tests are
deleted in the same boundary; no duplicate headless-review mechanism remains.

## 2. Resolved design clarifications

These decisions resolve ambiguities in the concept before implementation.

1. `docs/research/portfolio/workflow/registry.json` is the sole authority for a
   direction's lifecycle. There is no separate stored `active` boolean;
   `lifecycle == "ACTIVE"` is the active flag.
2. `PORTFOLIO.md` owns the persistent scientific goal. `registry.json` stores
   only its path and SHA-256, never a duplicate goal body.
3. `DIRECTION.md` owns direction science. Research and engineering JSON may
   point to a heading and its SHA, but never copy the claim or conclusion.
4. Concrete OMP handles, PIDs, absolute worktree paths, and local tab mappings
   are machine-local under ignored `.omp/runtime/` or `temp/`; tracked state
   stores logical references only.
5. OMP has native `autoResume`, but no generic persistent-goal engine and no
   post-compaction hook. Root recovers its goal from `PORTFOLIO.md` and directly
   reconciles cross-direction lifecycle; Root, EM, and CM perform prompt-driven
   reconciliation on startup, resume, or a detected compaction boundary.
6. All task agents are non-blocking. EM and CM are the only project
   spawn-capable managers; specialists are leaves. A missing reviewer, test,
   Dashboard, or Advisor result is an evidence gap, not a permission failure.
7. The project uses the existing sibling worktree container
   `/home/fires/hmasd-worktrees/`, not a worktree directory under repository
   `temp/`.
8. The Agentify ledger remains the sole authority for external submission.
   HMASD stores operation references and exact archives but never reconstructs
   or writes send state.
9. User-global model metadata belongs only in `~/.omp/agent/models.yml`; no
   project `.omp/models.yml` is created.
10. Bundled `scout`, `reviewer`, `sonic`, `designer`, and
    `security-reviewer` are disabled. Repository investigation uses
    `hmasd-project-scout`, code investigation uses `hmasd-code-scout`, and
    scientific investigation uses `hmasd-research-scout`.

## 3. Current-to-target clean cutover

| Current baseline | Target | Cutover rule |
| --- | --- | --- |
| Depth-3 Root → Portfolio → EM path | depth 2 | Merge Portfolio behavior into Root before lowering recursion. |
| `hmasd-portfolio` | removed | Root directly owns ranking, lifecycle, resources, and EM/CM dispatch. |
| `hmasd-independent-research-explorer` | `hmasd-em` | Rename file and every spawn/caller; no alias. |
| `hmasd-code-project-manager` | `hmasd-cm` | Rename file and every spawn/caller; no alias. |
| `hmasd-explorer-agentify-transport` | `hmasd-external-pro-transport` | Rename cleanly; no compatibility definition. |
| `hmasd-cpm-agentify-transport` | removed | Delete after all callers use research transports. |
| Reviewer `xhigh` | Reviewer `high` | Per-task effort may explicitly raise it. |
| Eight Skills | seven Skills | Merge Portfolio control into Root and delete the duplicate Skill. |
| Continuous Advisors | Implementer-only | Keep Root and managers off; use frozen checkpoint review for deep-tree evidence. |
| Provisional worktree helpers | one direction helper | Reuse safe path and Git primitives; remove replaced entry points. |
| Partial run wrappers | one observed-run contract | Preserve useful worker and atomic-write code. |
| Historical research maps | portfolio/direction authorities | Migrate facts once; retain old files only as provenance. |
| Agentify on `/mnt/c` | native WSL sibling | Copy, verify, install, then update `.omp/mcp.json`. |
| No Dashboard | read-only local service | Add after state schemas stabilize. |

No old agent name, route, re-export, compatibility file, or dual state writer
survives the cutover. Git history is the migration archive.

## 4. Target file layout

```text
.omp/
├── AGENTS.md
├── RULES.md
├── config.yml
├── lsp.json
├── mcp.json
├── WATCHDOG.md                      # active Implementer-only Advisor contract
├── agents/                          # exactly 17 hmasd-* definitions
├── skills/
│   ├── hmasd-root-control/SKILL.md  # includes Portfolio control
│   ├── hmasd-em-direction-cycle/SKILL.md
│   ├── hmasd-cm-engineering-cycle/SKILL.md
│   ├── hmasd-result-run/SKILL.md
│   ├── hmasd-scientific-external-review/SKILL.md
│   ├── hmasd-workflow-recovery/SKILL.md
│   └── hmasd-git-integration/SKILL.md
└── runtime/                          # ignored, reconstructible
    ├── agents.json
    └── worktrees.json

scripts/
├── schemas/
│   ├── hmasd_portfolio_registry.schema.json
│   ├── hmasd_research_state.schema.json
│   ├── hmasd_engineering_state.schema.json
│   ├── hmasd_external_review_index.schema.json
│   ├── hmasd_run_manifest.schema.json
│   ├── hmasd_accepted_result.schema.json
│   ├── hmasd_external_archive.schema.json
│   ├── hmasd_agent_result.schema.json
│   ├── hmasd_runtime_agents.schema.json
│   └── hmasd_runtime_worktrees.schema.json
├── hmasd_state.py
├── hmasd_worktree.py
├── hmasd_resource_preflight.py
├── hmasd_run.py
├── hmasd_external_review.py
├── hmasd_dashboard.py
└── dashboard/
    ├── index.html
    ├── app.js
    └── style.css

docs/research/
├── portfolio/
│   ├── PORTFOLIO.md
│   └── workflow/registry.json
└── candidates/<direction-id>/
    ├── DIRECTION.md
    ├── workflow/
    │   ├── research/state.json
    │   ├── engineering/state.json
    │   └── external-review/index.json
    └── results/
        ├── <result-id>.md
        └── <result-id>.json

docs/external-review/directions/<direction-id>/<round-id>/
├── GEMINI_DIVERGENT_PROMPT.md
├── PRO_DIVERGENT_PROMPT.md
├── PRO_CONVERGENCE_PROMPT.md
├── gemini/NATURAL_COMPLETION_ARCHIVE.json
├── gemini/HANDOFF.md
├── pro-divergent/NATURAL_COMPLETION_ARCHIVE.json
├── pro-divergent/HANDOFF.md
├── pro-convergence/NATURAL_COMPLETION_ARCHIVE.json
└── pro-convergence/HANDOFF.md

temp/directions/<direction-id>/exp/<run-id>/
├── manifest.json
├── runner-spec.json
├── stdout.log
├── stderr.log
├── exit-code.txt
├── checkpoints/
├── metrics/
└── artifacts/
```

Before creating tracked Markdown, update `.gitignore` with explicit parent/file
negations for `.omp/WATCHDOG.md`, `.omp/RULES.md`,
`.omp/skills/*/SKILL.md`, `docs/research/portfolio/**`, and
`docs/external-review/directions/**`. Keep `/.omp/runtime/**` and `/temp/**`
ignored, preserving only `temp/README.md`. Add a focused check using Git's
ignore-query surface for every target path; file existence alone is insufficient.

The same cutover updates `temp/README.md` to the Linux sibling worktree helper,
`.omp/AGENTS.md` to registry/Portfolio authority, and
`docs/external-review/README.md` to the direction/round layout. Existing
`docs/external-review/rounds/` and historical agent-name mentions remain
provenance and are never parsed as active workflow instructions.

## 5. Authority and writer matrix

| Fact | Sole authority | Writer |
| --- | --- | --- |
| Portfolio goal, ranking, synthesis, direction relationships | `PORTFOLIO.md` | Portfolio |
| Direction lifecycle and dependencies | `registry.json` | Portfolio |
| Direction question, mechanisms, evidence interpretation | `DIRECTION.md` | EM |
| Research actionability and active research references | `research/state.json` | EM |
| Engineering scope and integration progress | `engineering/state.json` | CM |
| External round pointers and archive references | `external-review/index.json` | EM after transport return |
| Exact tracked external archive bytes | Agentify archive validated into tracked path | Root through `hmasd_external_review.py` |
| Scientific external handoff | provider `HANDOFF.md` | EM through Artifact Writer |
| One local command's observed state | local `manifest.json` | its single Experiment Operator process |
| Accepted conclusion and small metrics | result Markdown/JSON pair | EM through Artifact Writer |
| Browser submission and commitment state | Agentify Schema-v2 ledger | Agentify only |
| OMP session/job handles | `.omp/runtime/agents.json` | Root reconciliation code |
| Absolute worktree paths | `.omp/runtime/worktrees.json` | Root worktree helper |
| Candidate and integration commits | Git | Root on `omp/workflow` |
| UI presentation | derived Dashboard snapshot | no authoritative writer |

A helper's `writer` field is provenance, not authentication. Single-writer
ownership is enforced by agent contracts, assignment-owned paths, optimistic
revision checks, and integration review—not by pretending local JSON is a
security boundary.

## 6. Common data conventions

All tracked and long-lived local JSON follows these rules:

- UTF-8, newline-terminated, two-space indentation, sorted keys;
- `schema_version` is integer `1` initially;
- `revision` starts at `1` and increments exactly once per successful replace;
- timestamps are UTC RFC 3339 with `Z`;
- SHA-256 values are lowercase 64-character hexadecimal strings;
- tracked paths are repository-relative POSIX paths without `..`, symlinks, or
  absolute prefixes;
- direction IDs match `[a-z0-9][a-z0-9_-]{1,63}` so existing stable
  underscore IDs remain unchanged; new IDs prefer kebab-case;
- logical manager identities are `Root`, `EM-<direction>`, or
  `CM-<direction>`;
- OMP job names are stable CamelCase without punctuation;
- optional values are explicit `null`; absent required keys are invalid;
- unknown top-level keys fail validation;
- unknown newer `schema_version` fails read-only with no rewrite;
- migrations are registered one-way functions `N -> N+1`; no downgrade exists;
- writes use same-directory temporary files, file `fsync`, `os.replace`, and
  parent-directory `fsync`;
- a write requires `expected_revision`; mismatches return a conflict and leave
  the file unchanged.

Exit codes for workflow helpers are uniform:

```text
0  success
2  invalid input or schema
3  unsupported schema version
4  stale expected revision or base SHA
5  writer/path ownership refusal
6  observed conflict or unsafe resource plan
7  external commitment unknown; no resend
8  user decision required
1  other directly observed failure
```

## 7. Exact state schemas

The JSON Schema files under `scripts/schemas/` are the durable machine
contracts. Python validators implement only these ten schemas with standard
library code; no general workflow framework or schema service is added.

Agentify's immutable natural-completion archive is a foreign schema exception:
HMASD validates its native `schema` discriminator and never adds
`schema_version`, `revision`, or writer fields to the raw archive.

### 7.1 Portfolio registry

```json
{
  "schema_version": 1,
  "revision": 1,
  "updated_at": "2026-08-24T00:00:00Z",
  "writer": "Portfolio",
  "workflow_version": "hmasd-autonomous-v1",
  "goal": {
    "path": "docs/research/portfolio/PORTFOLIO.md",
    "sha256": "<sha256>"
  },
  "directions": [
    {
      "id": "example-direction",
      "abbreviation": "EXD",
      "path": "docs/research/candidates/example-direction",
      "lifecycle": "REGISTERED",
      "dependencies": [],
      "lifecycle_decision_ref": {
        "path": "docs/research/portfolio/PORTFOLIO.md",
        "heading": "Direction example-direction",
        "sha256": "<sha256>"
      },
      "reactivation_condition_ref": null,
      "agent": {
        "logical_identity": "EM-example-direction",
        "job_name": "EMExampleDirection",
        "generation": 1,
        "runtime_ref": null
      },
      "research_state_path": "docs/research/candidates/example-direction/workflow/research/state.json",
      "engineering_state_path": "docs/research/candidates/example-direction/workflow/engineering/state.json",
      "external_review_index_path": "docs/research/candidates/example-direction/workflow/external-review/index.json"
    }
  ]
}
```

Validation:

- `lifecycle` is `REGISTERED | ACTIVE | CLOSED`; generic `PARKED` is rejected;
- `ACTIVE` includes runnable and queued work and has no fixed count cap;
- direction IDs, abbreviations, paths, logical identities, and job names are
  unique;
- dependencies refer to registered IDs and form an acyclic graph;
- lifecycle decisions, inheritance, merge relationships, scientific rank,
  reason, conclusion, and reactivation prose are prohibited; the registry
  points to their authoritative `PORTFOLIO.md` section instead;

### 7.2 Research state

```json
{
  "schema_version": 2,
  "revision": 1,
  "updated_at": "2026-08-24T00:00:00Z",
  "writer": "EM-example-direction",
  "direction_id": "example-direction",
  "registry_revision_seen": 1,
  "phase": "SCOPING",
  "actionable": true,
  "blockers": [],
  "waiting_on": [],
  "direction_ref": {
    "path": "docs/research/candidates/example-direction/DIRECTION.md",
    "sha256": "<sha256>"
  },
  "question_sha256": "<sha256>",
  "evidence_set_sha256": "<sha256>",
  "active_round_id": null,
  "active_agents": [],
  "engineering_request": null,
  "last_checkpoint_sha": null,
  "next_action": {
    "kind": "DISPATCH_RESEARCH",
    "owner": "EM",
    "input_refs": []
  }
}
```

`phase` is:

```text
SCOPING | DIVERGENT_REVIEW | LOCAL_RESEARCH | SYNTHESIS |
CONVERGENCE | ENGINEERING_REQUESTED | WAITING | IDLE | COMPLETE
```

`blockers[]` contains `{code, observed_refs[], resume_condition_ref}`. Scientific
interpretation and open-work prose remain in `DIRECTION.md`; operational
blockers may reference manifests, logs, state, or Git evidence.
`waiting_on[]` contains `{kind, ref, expected_terminal_states[]}`.
`active_agents[]` contains logical identity, generation, assignment ID, and a
nullable runtime reference; it never stores a session transcript.
`engineering_request` contains only scope and acceptance references into
`DIRECTION.md`, never rewritten scientific text. `next_action.owner` is one of
`ROOT | EM | CM | TRANSPORT | EXPERIMENT_OPERATOR | USER` and makes the
cross-role handoff deterministic.

### 7.3 Engineering state

```json
{
  "schema_version": 2,
  "revision": 1,
  "updated_at": "2026-08-24T00:00:00Z",
  "writer": "CM-example-direction",
  "direction_id": "example-direction",
  "phase": "SCOPING",
  "actionable": true,
  "blockers": [],
  "waiting_on": [],
  "scope_ref": {
    "path": "docs/research/candidates/example-direction/DIRECTION.md",
    "sha256": "<sha256>",
    "heading": "Engineering request"
  },
  "base_sha": "<git-sha>",
  "worktree_ref": null,
  "candidate_sha": null,
  "changed_paths": [],
  "verification_refs": [],
  "run_refs": [],
  "integration": {
    "target_branch": "omp/workflow",
    "target_sha_seen": "<git-sha>",
    "integrated_sha": null
  },
  "active_agents": [],
  "last_checkpoint_sha": null,
  "next_action": {
    "kind": "SCOUT_CODE",
    "owner": "CM",
    "input_refs": []
  }
}
```

`phase` is:

```text
UNREQUESTED | SCOPING | IMPLEMENTING | VERIFYING | RUN_READY |
RUNNING | INTEGRATING | WAITING | COMPLETE | FAILED
```

Tracked state stores no absolute worktree path or PID. A candidate can enter
`INTEGRATING` only after focused verification evidence exists. Review is
optional and advisory.

### 7.4 External-review index

```json
{
  "schema_version": 1,
  "revision": 1,
  "updated_at": "2026-08-24T00:00:00Z",
  "writer": "EM-example-direction",
  "direction_id": "example-direction",
  "workflow_version": "hmasd-external-review-v1",
  "rounds": [
    {
      "round_id": "<deterministic-id>",
      "question_sha256": "<sha256>",
      "evidence_set_sha256": "<sha256>",
      "status": "DIVERGENT_PENDING",
      "prompt_refs": {
        "gemini_divergent": {"path": "<path>", "sha256": "<sha256>"},
        "pro_divergent": {"path": "<path>", "sha256": "<sha256>"},
        "pro_convergence": null
      },
      "providers": {
        "gemini_divergent": null,
        "pro_divergent": null,
        "pro_convergence": null
      },
      "local_synthesis_ref": null,
      "created_at": "2026-08-24T00:00:00Z",
      "completed_at": null
    }
  ]
}
```

The round ID is the first 20 hex characters of:

```text
sha256(direction_id + "\n" + question_sha256 + "\n" +
       evidence_set_sha256 + "\n" + workflow_version)
```

Round status is:

```text
DIVERGENT_PENDING | DIVERGENT_RUNNING | LOCAL_RESEARCH |
SYNTHESIS_READY | CONVERGENCE_RUNNING | COMPLETE | BLOCKED
```

A provider result contains only `operation_id`, `idempotency_key`,
`session_ref`, `terminal_state`, archive/handoff paths and SHAs, and completion
time. It never stores `sendCount`, commitment, or reconstructed ledger state.
Only EM replaces the index after receiving transport results.

### 7.5 Local run manifest

```json
{
  "schema_version": 1,
  "revision": 1,
  "writer": "Operator-example-run",
  "run_id": "example-run",
  "direction_id": "example-direction",
  "assignment_id": "run-example",
  "operator_identity": "Operator-example-run",
  "status": "PREPARED",
  "command": ["python3", "train.py", "--seed", "7"],
  "command_sha256": "<sha256-of-NUL-delimited-argv>",
  "cwd": "/home/fires/hmasd-worktrees/example",
  "parameters": {"seed": 7},
  "code_sha": "<git-sha>",
  "environment": {
    "python": "3.x",
    "platform": "linux",
    "hostname": "<host>",
    "captured_variables": {}
  },
  "estimate": {
    "wall_seconds": 1200,
    "basis": "benchmark-ref-or-explicit-rationale",
    "peak_memory_gib": 4.0
  },
  "resources": {
    "preflight_ref": "preflight.json",
    "workers": 4,
    "threads_per_worker": 1,
    "memory_safe": true
  },
  "process": {
    "execution_token": null,
    "pid": null,
    "process_group_id": null,
    "linux_boot_id": null,
    "proc_start_ticks": null,
    "started_at": null,
    "ended_at": null,
    "exit_code": null,
    "terminal_reason": null
  },
  "outputs": {
    "stdout": "stdout.log",
    "stderr": "stderr.log",
    "checkpoints": "checkpoints",
    "metrics": "metrics",
    "artifacts": "artifacts"
  },
  "observed_metrics": {},
  "created_at": "2026-08-24T00:00:00Z",
  "updated_at": "2026-08-24T00:00:00Z"
}
```

Status transitions are:

```text
PREPARED -> RUNNING -> SUCCEEDED | FAILED | CANCELLED | UNKNOWN
```

The process that changes `PREPARED` to `RUNNING` is the sole writer while its
PID identity remains live. A live manifest with the same `command_sha256`, code
SHA, and direction refuses a duplicate launch. After proving that PID identity
dead, Root recovery may atomically change `RUNNING` to `UNKNOWN` with the
observed recovery evidence; it never relaunches implicitly.

`captured_variables` is an explicit reproducibility allowlist. Names matching
secret/token/key/password/credential patterns are rejected; values are stored
only when declared non-secret, otherwise only a SHA-256 is recorded. The
Dashboard never exposes this field.

### 7.6 Accepted result

```json
{
  "schema_version": 1,
  "revision": 1,
  "updated_at": "2026-08-24T00:00:00Z",
  "writer": "EM-example-direction",
  "result_id": "example-result",
  "direction_id": "example-direction",
  "conclusion_path": "docs/research/candidates/example-direction/results/example-result.md",
  "source_run": {
    "run_id": "example-run",
    "manifest_path": "temp/directions/example-direction/exp/example-run/manifest.json",
    "manifest_sha256": "<sha256>",
    "code_sha": "<git-sha>",
    "parameters": {"seed": 7},
    "parameters_sha256": "<sha256>"
  },
  "metrics": {
    "return_mean": {
      "value": 1.25,
      "unit": "score",
      "split": "evaluation",
      "aggregation": "mean",
      "sample_count": 100
    }
  },
  "promoted_at": "2026-08-24T00:00:00Z",
  "promoted_by": "EM-example-direction"
}
```

The JSON retains the relevant reproducibility parameters even if the local run
directory is later removed. It remains small and contains no raw tensors,
checkpoints, full logs, or copied scientific prose.

### 7.7 External natural-completion archive

HMASD validates Agentify's
`agentify_review_natural_completion_archive_v1` without rewriting it. Required
fields are:

```text
schema, operationId, idempotencyKey, stableKey, provider, model,
conversationUrl, conversationId, terminalState, sendCount, sendActionCount,
userMessageId, assistantMessageId, responseSha256, responseText, completedAt
```

Acceptance requires terminal natural completion, `sendCount <= 1`,
`sendActionCount <= 1`, exact response SHA, and a matching operation reference
from Agentify. Commitment-unknown state is not converted into an archive and is
never resent.

### 7.8 Common agent result envelope

```json
{
  "schema_version": 1,
  "role": "hmasd-em",
  "logical_identity": "EM-example-direction",
  "generation": 1,
  "assignment_id": "research-round-1",
  "status": "COMPLETED",
  "materiality": "DIRECTION",
  "summary": "<concise observed outcome>",
  "changed_paths": [],
  "state_refs": [],
  "artifact_refs": [],
  "checkpoint_sha": null,
  "decision_requests": [],
  "next_action": null,
  "payload": {
    "kind": "em",
    "direction_id": "example-direction"
  }
}
```

`status` is `COMPLETED | PARTIAL | BLOCKED | FAILED` and `materiality` is
`NONE | LOCAL | DIRECTION | PORTFOLIO | USER`. `decision_requests[]` is allowed
only for the user boundaries in `.omp/RULES.md`.

Payload discriminators and required additions:

| `kind` | Required payload fields |
| --- | --- |
| `portfolio` | `direction_actions[]`, `portfolio_ref`, `registry_revision` |
| `em` | `direction_id`, `question_sha256`, `evidence_set_sha256`, `conclusion_refs[]`, nullable `engineering_request_ref` |
| `cm` | `direction_id`, `scope_ref`, `base_sha`, nullable `candidate_sha`, `verification_refs[]`, nullable `integrated_sha` |
| `implementation` | `changed_paths[]`, `preserved_invariants[]`, `lsp_evidence_refs[]` |
| `review` | `findings[]`, `evidence_refs[]`; no approval field |
| `verification` | `checks[]`, `behavioral_evidence_refs[]`, `benchmark_refs[]` |
| `run` | `run_id`, `manifest_ref`, `terminal_status`, nullable `exit_code` |
| `transport` | `provider`, `mode`, `round_id`, `operation_ref`, nullable `archive_ref`, nullable `handoff_ref` |
| `artifact` | `paths[]`, `sha256_by_path` |
| `recovery` | `failure_class`, `observed_refs[]`, `attempts[]`, `outcome`, nullable `resume_condition` |

Ordinary `event_id` is forbidden. Agentify operation IDs remain untouched.

### 7.9 Ignored runtime registries

`.omp/runtime/agents.json` and `.omp/runtime/worktrees.json` use the common
version/revision/writer conventions even though they are reconstructible and
ignored. The agent registry contains only logical identity, agent type,
generation, parent identity, session/job/runtime refs, lifecycle state, and
last-seen time. The worktree registry contains only worktree ref, direction,
kind, assignment, canonical absolute path, branch, base/candidate/integrated
SHAs, lifecycle state, and receipt path. Root is the single writer.

Both runtime schemas are accepted by `hmasd_state.py`, use the same transient
`fcntl` lock/CAS path, and can be rebuilt from Hub/session artifacts and Git.
Deleting them while an owned process is live is prohibited; their absence at
startup triggers reconstruction, not a blocker.

## 8. OMP configuration and model policy

Target `.omp/config.yml`:

```yaml
modelRoles:
  advisor: opencode-go/glm-5.3:high

advisor:
  enabled: false

autoResume: true

async:
  enabled: true

launch:
  enabled: true

task:
  maxConcurrency: 32
  maxRecursionDepth: 2
  enableEffort: true
  enableLsp: true
  agentAdvisor:
    hmasd-implementer: opencode-go/glm-5.3:high
    hmasd-implementer-terra: opencode-go/glm-5.3:high
  disabledAgents:
    - scout
    - reviewer
    - sonic
    - designer
    - security-reviewer
```

Root's Advisor subsystem is disabled. OMP task subagents default to no Advisor,
and the only two `task.agentAdvisor` entries opt in the Implementer leaves.
Root, EM, and CM remain off because their complete descendant and Hub context
is not available to a continuous Advisor.

`.omp/WATCHDOG.md` routes strictly by primary role:

```text
Root, hmasd-em, hmasd-cm     -> no Advisor
hmasd-implementer,
hmasd-implementer-terra      -> engineering
all other roles              -> no Advisor
```

Implementers are scope-frozen leaves. A material assignment change cancels and
replaces the leaf rather than relying on unseen Hub steering. Deep-tree
assessment uses an explicit checkpoint Reviewer or Research Critic with
complete frozen envelopes and artifact references. Advice remains read-only and
non-gating.

`task` and `librarian` remain available. Bundled `task` is Root-only and used
only when no project role fits. All project agent frontmatter uses
`blocking: false` or omits the field, whose default is non-blocking.

Create user-global `~/.omp/agent/models.yml` with `contextWindow: 372000` for
the seven currently installed OpenAI-Codex models:

```yaml
providers:
  openai-codex:
    modelOverrides:
      gpt-5.3-codex-spark: {contextWindow: 372000}
      gpt-5.4: {contextWindow: 372000}
      gpt-5.4-mini: {contextWindow: 372000}
      gpt-5.5: {contextWindow: 372000}
      gpt-5.6-luna: {contextWindow: 372000}
      gpt-5.6-sol: {contextWindow: 372000}
      gpt-5.6-terra: {contextWindow: 372000}
```

Before writing user-global files, merge with existing provider entries rather
than replacing unrelated configuration. Verify every selector with `omp models
openai-codex`. New catalog models are not silently added; installation of a new
model requires updating this list deliberately.

If `~/.omp/agent/RULES.md` exists, resolve its collision before relying on the
project `.omp/RULES.md`, because both discover as `RULES`. Do not delete
unrelated user-global rules without explicit user authorization.

## 9. Agent frontmatter and tool contracts

All 17 project definitions declare concrete model selectors, thinking level,
`blocking: false`, exact `spawns`, and `autoloadSkills` where applicable.

| Agent | Model / effort | Direct tools | Spawns | Autoload Skills |
| --- | --- | --- | --- | --- |
| `hmasd-em` | Sol max | read/write/edit/grep/glob/task/hub | research specialists, artifact writer, code scout, both transports, librarian | em-direction-cycle, scientific-external-review |
| `hmasd-cm` | Sol high | read/write/edit/grep/glob/bash/task/hub | engineering specialists, experiment operator, research scout, librarian | cm-engineering-cycle, result-run, git-integration |
| `hmasd-project-scout` | Luna medium | read/grep/glob | none | none |
| `hmasd-code-scout` | Luna medium | read/grep/glob | none | none |
| `hmasd-implementer` | Sol high | read/write/edit/grep/glob/bash/lsp | none | git-integration |
| `hmasd-implementer-terra` | Terra high | read/write/edit/grep/glob/bash/lsp | none | git-integration |
| `hmasd-reviewer` | Sol high | read/grep/glob | none | none |
| `hmasd-verifier` | Luna high | read/grep/glob/bash | none | none |
| `hmasd-experiment-operator` | Luna low | read/grep/glob/bash/hub | none | result-run |
| `hmasd-workflow-recovery-manager` | Terra high | read/write/edit/grep/glob/bash/hub | none; Root-only caller | workflow-recovery |
| `hmasd-external-pro-transport` | Luna medium | read/grep/glob plus allowlisted Agentify MCP review tools | none | scientific-external-review |
| `hmasd-external-gemini-transport` | Luna high | read/grep/glob plus allowlisted Agentify MCP review tools | none | scientific-external-review |
| `hmasd-research-scout` | Sol high | read/grep/glob/web_search | none | none |
| `hmasd-research-innovator` | Sol max | read/grep/glob/web_search | none | none |
| `hmasd-research-critic` | Sol max | read/grep/glob/web_search | none | none |
| `hmasd-research-principles-analyst` | Sol max | read/grep/glob/web_search | none | none |
| `hmasd-research-artifact-writer` | Luna medium | read/write/edit/grep/glob | none | none |

Project/code scouts, Reviewer, Verifier, research Scout/Innovator/Critic/
Principles Analyst all declare `read-summarize: false`; their evidence reads
must remain verbatim across the rename. Other roles keep the native default.

Only Implementers receive LSP. Reviewer receives a frozen diff/evidence bundle
from CM and never runs Git or tests. Verifier runs the exact assigned check but
never edits source. Transports receive only the exact Agentify MCP tools exposed
by the migrated server; they never receive direct browser, write, or shell
access.

Root loads `hmasd-root-control` and `hmasd-git-integration` through mandatory
instructions in `.omp/AGENTS.md`, because Root is the main session rather than a
project task-agent definition.

## 10. Skill contracts

Every `SKILL.md` contains `name`, `description`, purpose, inputs, bounded cycle,
state writes, returned result envelope, failure handling, and deletion
condition.

### `hmasd-root-control`

- Reconcile `PORTFOLIO.md`, registry, all direction states, `.omp/runtime`, Hub
  jobs, worktrees, runs, Agentify references, and Git before dispatch.
- Rank current and recently active directions. Activate every scientifically
  qualified runnable or exact queued next action; zero remains a valid IDLE
  result and execution concurrency remains resource-bounded.
- Create, register, activate, return-to-registered, merge, close, and reactivate
  with reasons written only to `PORTFOLIO.md`, then replace registry state by
  CAS using authority writer `Portfolio`. `PARKED` is not a Portfolio
  lifecycle.
- Route science to EM, implementation to CM, external review to Transport,
  exact commands to an Experiment Operator resource queue, integration and
  lifecycle to Root, and genuine decisions to the user. Persist
  `next_action.owner`; never end a material wake with an ownerless handoff.
- Start or revive EM and CM sessions directly. Inject only material transitions
  and keep Root → EM/CM → specialist as the maximum path.
- Stop at IDLE, COMPLETE, a rules-defined user decision, or exhausted recovery.
- Never continuously poll; use Hub completion, process exit, file change, or one
  bounded reassessment.

### `hmasd-em-direction-cycle`

- Read registry, `DIRECTION.md`, research state, and current external index.
- Dispatch two specialists by default, up to four when the exact question
  justifies it.
- Separate facts, external evidence, inference, and speculation.
- Run divergent review, local research, synthesis, and convergence in order.
- Request engineering through a durable reference; never spawn CM directly.
- Update only EM-owned files and return a material result envelope.

### `hmasd-cm-engineering-cycle`

- Freeze scope and acceptance references from `DIRECTION.md`.
- Map files/interfaces before decomposing work.
- Dispatch two specialists by default and at most six with disjoint ownership
  and contracts.
- Require Implementer LSP references before exported-symbol edits and LSP rename
  for cross-file renames.
- Obtain focused verification; review is optional and advisory.
- Integrate only through the Root-owned Git helper.
- Return scientific ambiguity to Root/EM without reinterpretation.

### `hmasd-result-run`

- Require exact argv, cwd, code SHA, parameters, output paths, duration estimate,
  memory estimate, and scientific activity predicate.
- Run memory preflight before approval logic.
- At `> 7200` estimated seconds, attempt `hmasd-reviewer` performance review
  from frozen evidence; the running engineering Advisor may supplement but
  never replace that attempt. Reviewer unavailability is recorded as an evidence
  gap and remains fail-open for asking the user.
- Return exit code `8` with a frozen decision request binding direction/run ID,
  argv, code SHA, parameters, estimates, and evidence SHAs. Approval resumes
  exactly that request and dispatches one Operator; rejection cancels the run
  request or returns engineering state to exact `WAITING`. It never creates an
  ambiguous Portfolio lifecycle. Advisor/reviewer output is never the approval
  token.
- At `<= 7200`, one Operator uses Hub to own one `hmasd_run.py execute` process.
- Inspect duplicate manifests and PID identity before launch.
- Never start a successor or reinterpret metrics.

### `hmasd-scientific-external-review`

- Freeze question/evidence SHAs and deterministic round ID.
- Dispatch mutually blind Gemini and Pro divergent prompts in parallel.
- Require local EM synthesis before authoring Pro convergence prompt.
- Route sends through Agentify only; monitor with 1–3 transports and disjoint
  lists.
- Transport returns the immutable Agentify operation/archive reference to Root.
  Root alone invokes the archive helper to validate and create exact tracked
  bytes. EM then gives the rendered intake to Artifact Writer for the scientific
  handoff and updates its index.
- Never resend commitment-unknown operations.

### `hmasd-workflow-recovery`

- Classify the effect before acting: pure research, code/worktree, run, Git,
  external send, runtime mapping, or Dashboard.
- Inspect the authoritative source and record materially distinct attempts.
- Never replay an unknown run or external send.
- Reject late output against a newer checkpoint SHA.
- Return a precise resume condition or exhausted user blocker.

### `hmasd-git-integration`

- Resolve canonical paths and exact `omp/workflow` base SHA.
- Enforce assignment-owned paths and a single candidate commit.
- Refuse dirty worktrees, stale bases, conflicts, non-OMP target branches, and
  out-of-scope paths.
- Root alone applies a verified candidate to `omp/workflow`.
- Commit and push at material checkpoints; batch ordinary intermediate events.

## 11. `.omp/RULES.md` hard boundaries

The file contains only these always-applied rules:

1. A local result-bearing command estimated over 7200 seconds requires a
   performance-reasonableness review attempt and explicit user approval.
2. Any operation that affects a branch outside the OMP-owned `omp/*` namespace
   requires user approval. Temporary assignment branches may affect only their
   declared scope and may integrate only into `omp/workflow`.
3. An external submission must have an exact target and Agentify operation,
   idempotency, fingerprint, and commitment state; unknown commitment never
   resends.
4. Exactly one Experiment Operator owns one exact result-bearing command.
5. Destructive targets and assignment-owned paths must resolve canonically.
6. Secrets are never exposed in prompts, state, logs, Dashboard APIs, or Git.
7. Scientific, numerical, RNG, checkpoint, bit-identity, and external-effect
   semantics are not silently changed.
8. A role, test, review, Advisor, Dashboard, lease, hash, or historical document
   cannot grant or deny ordinary authorized reversible work.
9. Unsafe memory plans are refused mechanically and must be reduced, batched, or
   sharded; they are not sent for approval.

Everything else belongs in Skills or agent prompts, not sticky rules.

## 12. Helper interfaces

### 12.1 `scripts/hmasd_state.py`

```text
validate --kind <kind> --path <json>
initialize --kind <kind> --path <json> --writer <identity> --input <json>
replace --kind <kind> --path <json> --writer <identity>
        --expected-revision <n> --input <json>
migrate --kind <kind> --path <json> --writer <identity>
        --expected-revision <n> --to-version <n>
```

`initialize` validates and creates the target with `O_CREAT|O_EXCL`; an existing
path is never overwritten. `replace` accepts a complete next document, not a
generic JSON patch. Every replace or migration takes a short Linux `fcntl`
lock in ignored `.omp/runtime/locks/<path-sha>.lock`, rereads and validates the
current bytes/revision under that lock, writes a same-directory temporary file,
`fsync`s it, uses `os.replace`, and `fsync`s the parent directory. The lock is
transient mutual exclusion for one observed duplicate-writer race, not durable
authority or a lease.

Each operation validates path ownership, current revision, next revision,
writer identity, and schema before mutation. Migration writes a backup only
under ignored `temp/runtime/migrations/`, applies one registered step,
validates, and atomically replaces. Concurrent initialize/replace/migrate tests
must prove one winner and no lost update.

### 12.2 `scripts/hmasd_worktree.py`

```text
provision --repo <absolute> [--container <absolute>] --direction <id>
          --kind research|engineering --assignment <id> --base <full-sha>
inspect --worktree-ref <id>
record-candidate --worktree-ref <id> --candidate <full-sha>
prepare-integration --worktree-ref <id> --target omp/workflow
                    --allowed-path <path>...
apply --receipt <json> --actor root
release --worktree-ref <id> --actor root
        --ignored-artifacts refuse|discard|retain
retain --worktree-ref <id> --actor root --reason <text>
```

Reuse only canonical path, symlink, and Git-query primitives from
`hmasd_root_managed_worktree.py`; its detached-worktree lifecycle and receipt
format are replaced. The default container is
`<repo.parent>/<repo.name>-worktrees`; for this checkout it resolves to
`/home/fires/hmasd-worktrees`. Tests and isolated repositories pass an explicit
temporary `--container`. The worktree path is
`<container>/<direction>-<kind>-<assignment>` on the OMP-owned temporary branch
`omp/<direction>/<kind>/<assignment>`.

Provision holds an `fcntl` lock on a non-symlink lock file opened inside the
canonical container, records container/parent device+inode identities, refuses
an existing target, and revalidates every identity immediately before and after
`git worktree add`. All HMASD worktree mutations use this lock. A detected
namespace swap rolls back only the exact Git registration/path proven by the
operation token and fails safely. This protects concurrent cooperative project
operations; it does not claim security against a privileged process mutating
the filesystem outside HMASD.

Before `git worktree add`, Root atomically records `PROVISIONING` with intended
path, branch, base SHA, and operation token in `.omp/runtime/worktrees.json`.
Success advances it to `PROVISIONED`; recovery compares the journal with
`git worktree list --porcelain`, the target path, and branch ref. A kill between
Git mutation and registry update therefore yields a detectable orphan, never an
untracked second provision.

`record-candidate` requires one clean candidate commit directly descended from
the recorded base. `prepare-integration` requires exact target `omp/workflow`,
unchanged target/base SHA, assignment-owned changed paths, and a conflict-free
candidate. Verification references are recorded evidence, not permission; a
missing reference is visible in the receipt and cannot by itself revoke Root's
authority over reversible integration.

The receipt contains operation token, runtime-registry revision, all observed
SHAs, path results, conflict result, and verification evidence status. `apply`
takes the runtime lock, rereads target/receipt/registry, and refuses if any fact
changed between prepare and apply. Stale base, target advance, conflict, or
out-of-scope changes return to Root without automatic repair. Release deletes a
temporary branch only after proving it is integrated or explicitly disposable.

After callers migrate, delete `new_hmasd_worktree.py` and
`hmasd_root_managed_worktree.py`; do not keep wrappers. Update `temp/README.md`
from its retired Windows/PowerShell path to this Linux Python contract.


Release defaults to `refuse` when ignored-only artifacts exist. `discard` is
allowed only after status proves every residual path is ignored, inside the
assignment worktree, and non-authoritative; it records the discarded path list
before removal. `retain` transitions to `RETAINED_FOR_RECOVERY` and requires a
reason. Tracked, staged, or non-ignored untracked changes always refuse release.

### 12.3 `scripts/hmasd_resource_preflight.py`

Rename and extend the current hyphenated helper with two explicit modes:

```text
capture --out <host-snapshot.json>
assess-run --direction <id> --run-id <id>
           --workers <n> --threads-per-worker <n>
           --estimated-wall-seconds <n> --estimated-peak-gib <n>
           --basis <text-or-ref> --out <preflight.json>
```

`capture` is observation-only and needs no estimate. `assess-run` is exclusively
for result-bearing execution; missing or non-positive estimates return exit `6`.
Measure `/proc/cpuinfo`, `/proc/meminfo`, load average, and cgroup v2
`memory.max`/`memory.current` when present. Treat literal cgroup `max` as
unbounded and normalize all byte/KiB/GiB values before applying:

```text
effective_limit = min(MemTotal, finite_cgroup_memory_max if present)
cgroup_headroom = max(0, cgroup_memory_max - cgroup_memory_current)
effective_available = min(MemAvailable, cgroup_headroom if bounded)
reserve_gib = max(4.0, 0.20 * effective_limit)
usable_gib = max(0, effective_available - reserve_gib)
adjusted_peak_gib = 1.25 * estimated_peak_gib
memory_safe = adjusted_peak_gib <= usable_gib
```

`prepare` stores the preflight SHA. Immediately before child launch, `execute`
captures resources again and reruns the same assessment. A now-unsafe plan
becomes terminal `FAILED` with reason `MEMORY_REFUSED_BEFORE_START`, exit `6`,
and proof that no child PID was created. Worker count never triggers approval.
The 25% factor is replaced only after measured peak evidence establishes a
safer margin.

### 12.4 `scripts/hmasd_run.py`

```text
prepare --direction <id> --run-id <id> --assignment <id>
        --code-sha <sha> --parameters <json> --estimate <json>
        --output-root temp/directions/<id>/exp/<run-id> -- <argv...>
execute --manifest <absolute-manifest-path>
reconcile --manifest <absolute-manifest-path>
promote --manifest <path> --result-json <tracked-path>
        --result-markdown <tracked-path>
```

`prepare` performs schema, path, branch, duration, and memory checks and writes
`PREPARED` manifest plus runner spec. `execute` takes the manifest's transient
state lock, atomically claims it with an unguessable execution token, and
performs the execute-time resource recheck before creating a child.

The child runs with `shell=False` and `start_new_session=True`. The manifest
records leader PID, process-group ID, Linux boot ID, `/proc/<pid>/stat` start
ticks, execution token, and command digest. Cancellation terminates the exact
process group, waits for group quiescence, then records terminal state.
Recovery matches boot ID/start ticks/command digest and inspects the whole group;
PID number alone is never identity.

The exact child exit code is stored in the manifest. The wrapper returns `0`
when it recorded a successful child, `1` when it safely recorded a nonzero or
signalled child, and the reserved helper exit codes only for wrapper/prestart
conditions. Child code `2`, `6`, or `8` is never confused with helper refusal.
Experiment Operator launches `execute` through Hub. `reconcile` observes only;
it never relaunches. `promote` copies no raw artifact and requires EM-authored
conclusion plus selected metric provenance.

Reuse only atomic JSON and subprocess/log primitives from
`hmasd_run_observed_command.py` and `run_python_worker.py`; their foreground
lifecycle and raw child-exit behavior are replaced. Delete both entry points
after all callers and tests migrate.

### 12.5 `scripts/hmasd_external_review.py`

```text
round-id --direction <id> --question-sha <sha> --evidence-sha <sha>
         --workflow-version <version>
validate-prompts --round-dir <path>
partition-monitors --sessions <json> --count 1|2|3
validate-archive --operation-ref <json> --archive <json>
render-handoff-input --archive <json> --out <ignored-json>
```

The helper is Root-only. It computes IDs, validates frozen files and exact
Agentify archives, partitions monitoring sessions by sorted stable session key
with round-robin assignment, imports exact archive bytes, and renders an ignored
handoff input. It never sends, monitors a browser directly, writes the Agentify
ledger, or performs scientific synthesis. Transport agents therefore need no
shell or write tools; Artifact Writer writes only the EM-authored handoff.

Archive creation uses `O_CREAT|O_EXCL`, complete-byte write, file and
parent-directory `fsync`, and same-SHA idempotent acceptance. Concurrent
creators yield one file; a different existing SHA is a conflict. Retire
`export_gemini_live_response.py` after
migrating only its transcript-extraction logic; its `--force` and direct
`write_text` behavior are not reused.

### 12.6 `scripts/hmasd_dashboard.py`

```text
serve --root <repo> --port <port>
snapshot --root <repo>
```

Use only the Python standard library. `--root` must resolve to the HMASD checkout
with `.omp/AGENTS.md`; the bind host is not caller-configurable and is always
literal `127.0.0.1`. `ThreadingHTTPServer` serves only three fixed static assets
and the allowlisted APIs below—never arbitrary root-relative files. A one-second
mtime/signature scan refreshes durable projections; local agent/PID/Git/external
runtime projections refresh every seven seconds. There is no database or
filesystem-watcher dependency.

HTTP contract:

```text
GET /                         fixed static index
GET /app.js                   fixed static JavaScript
GET /style.css                fixed static CSS
GET /api/health               service/version/read-only status
GET /api/snapshot             all five safe projections
GET /api/portfolio            portfolio/direction projection
GET /api/agents               logical/runtime projection
GET /api/runs                 local manifest projection
GET /api/external-reviews     round/archive projection
GET /api/worktrees            Git/worktree projection
POST|PUT|PATCH|DELETE *        405 Method Not Allowed
all other paths               404 Not Found
```

Every projection uses `{schema_version, generated_at, status, revision_refs,
data, warnings}` where status is `ok | missing | invalid | stale`. Snapshot reads
the registry revision before and after all dependent files and retries at most
three times. A still-changing registry returns HTTP 409 with no mixed-generation
data. Missing/malformed optional runtime sources return a section status rather
than failing unrelated sections. `snapshot` prints the identical deterministic
JSON; it returns `0` for a consistent projection, `2` for invalid root/schema,
and `4` for an unstable revision.

The service allowlists fields; it never returns secrets, raw Agentify ledger,
full transcripts, environment variables, raw external responses, or arbitrary
file contents. Agent Hub navigation is a logical identity, job name, and a short
`/agents` instruction because OMP exposes no stable browser deep-link contract.
Root starts/reuses it with Hub and readiness on both log banner and TCP port.

## 13. Manager lifecycle and reconciliation

### 13.1 Root cycle

```text
START_OR_RESUME
  -> READ_GOAL_AND_REGISTRY
  -> RECONCILE_RUNTIME_GIT_RUNS_AGENTIFY
  -> REVIVE_OR_CREATE_PORTFOLIO
  -> DISPATCH_ACTIONABLE_CM
  -> WAIT_FOR_NATIVE_EVENT
  -> APPLY_MATERIAL_RESULTS
  -> CHECKPOINT
  -> CONTINUE | USER_DECISION | IDLE | COMPLETE
```

Root does not wait by polling. It uses native task completion, Hub messages,
Hub-managed process exit, and bounded checks after file changes or external
completion. Todo tracks only the current bounded tick.

### 13.2 Portfolio cycle

```text
RECONCILE_REGISTRY
  -> MECHANICAL_ELIGIBILITY
  -> SCIENTIFIC_RANKING_IN_PORTFOLIO_MD
  -> SELECT_2_TO_8
  -> REVIVE_OR_CREATE_EM
  -> RECEIVE_MATERIAL_RESULTS
  -> UPDATE_PORTFOLIO_AND_REGISTRY
  -> BOUNDED_REASSESSMENT
  -> WAIT | IDLE
```

### 13.3 EM cycle

```text
RECONCILE_DIRECTION
  -> SCOPE_OR_REFRESH_QUESTION
  -> DIVERGENT_EXTERNAL_REVIEW
  -> LOCAL_SPECIALISTS
  -> LOCAL_SYNTHESIS
  -> PRO_CONVERGENCE
  -> ACCEPT_RESULT | REQUEST_ENGINEERING | CONTINUE_RESEARCH | WAIT
```

Gemini and Pro divergent prompts are mutually blind. Pro convergence receives
only the EM-authored local synthesis and declared repository evidence; no
divergent prompt, response, archive, or conversation context from either
provider is supplied or linked. EM may incorporate validated mechanisms into
its own synthesis without exposing raw provider material.

### 13.4 CM cycle

```text
RECONCILE_SCOPE
  -> PROVISION_WORKTREE
  -> SCOUT_AND_DECOMPOSE
  -> IMPLEMENT
  -> VERIFY
  -> OPTIONAL_REVIEW
  -> OPTIONAL_RESULT_RUN
  -> PREPARE_INTEGRATION
  -> ROOT_APPLY
  -> RETURN_TO_EM
```

### 13.5 Session generations

Reuse an EM/CM session when durable identity, owned scope, checkpoint, and
current generation match. Rotate only for incompatible direction redefinition,
state/context inconsistency, ownership mismatch, untrustworthy recovery, or
context-exhaustion risk. On resume or compaction boundary, compare:

```text
logical identity and generation
registry/state revision and checkpoint SHA
current parent and active children
pending next_action/waiting_on references
active external round and Agentify operation refs
active run IDs and terminal state
worktree ref, base SHA, and candidate SHA
```

Any mismatch prevents new effectful work until Root reconciles; read-only
research may continue when its frozen inputs remain valid.

## 14. External review and Agentify migration

This section is a cross-repository prerequisite contract, not authorization to
modify Agentify. Execute the WSL copy and Agentify-owned changes only as a
separately approved workstream. HMASD state/topology/run phases may proceed
without it, but Phase 5 external submission cannot cut over until the sibling
workstream passes its focused evidence.

### 14.1 Windows Agentify runtime and native fallback

The user-approved final runtime is `C:\Projects\agentify-desktop`, visible in
WSL at `/mnt/c/Projects/agentify-desktop`. OMP must launch it with Windows Node,
not WSL Node:

```text
/mnt/c/Program Files/nodejs/node.exe
  C:\Projects\agentify-desktop\bin\agentify-desktop.mjs mcp
```

Windows Node resolves `C:\Users\fires\.agentify-desktop`, starts the visible
Windows Agentify application, and uses its configured Windows Chrome profile.
Do not replace this path with Linux headless Chrome: the user must be able to
see and intervene in the provider browser.

The verified copy at `/home/fires/projects/agentify-desktop` remains an
optional fallback and development worktree. It is not the MCP default. Changes
needed by both runtimes must be deliberately synchronized; the Windows
configured state, ledger, Chrome profile, and user data are never copied into
the Linux tree.

### 14.2 Agentify-owned changes

Implement in the Agentify repository, not HMASD:

- a Linux headless runner that initializes `ChromeCdpBrowserBackend`,
  `TabManager`, and `startHttpApi` without Electron;
- `mcp-lib.mjs::ensureDesktopRunning` selection of headless mode when
  `AGENTIFY_HEADLESS=1` or Electron/display is unavailable;
- `chrome-cdp-backend.mjs::listAvailableTargets` and
  `attachExistingTarget`;
- `tab-manager.mjs::adoptExistingTarget`;
- authenticated HTTP/MCP reconciliation endpoints and
  `agentify_reconcile_targets`;
- provider-specific submit tools and provider-independent
  `agentify_review_observe` monitoring.

Do not change `review-transport.mjs` ledger authority, Schema v2 IDs,
at-most-once counts, commitment-unknown isolation, or two-snapshot natural
completion semantics except to fix a proven bug with focused tests.

Focused Agentify checks:

```text
node --test tests/package-manifest.test.mjs tests/config.test.mjs
node --test tests/review-transport.test.mjs \
  tests/review-prepared-cancellation.test.mjs tests/state.test.mjs
node --test tests/mcp-server-names.test.mjs tests/mcp-lib.test.mjs \
  tests/http-api.test.mjs
node --test tests/chrome-cdp-backend.test.mjs tests/tab-manager.test.mjs
node --test tests/artifact-store.test.mjs tests/bundle-store.test.mjs
```

A real restart smoke must prove that an existing provider tab is listed,
adopted, bound to the original conversation/session, and observed without a new
send. No live submission is performed merely for migration verification.

### 14.3 Review sequence

```text
freeze question/evidence
  -> Gemini divergent + Pro divergent in parallel
  -> local EM validation and research
  -> direction/portfolio synthesis
  -> Pro convergence
  -> exact archives + scientific handoffs
```

Agentify defaults remain six inflight queries and twelve tabs. Work beyond those
limits runs in waves. Root assigns one to three monitor transports through the
deterministic partition helper. Duplicate observation is harmless; duplicate
submission is forbidden.

## 15. Git, checkpoint, and path policy

Root owns canonical `omp/workflow`. Automated work may create, commit, inspect,
and delete only the assignment branch
`omp/<direction>/<kind>/<assignment>` plus integrate it into `omp/workflow`.
Any operation affecting a branch outside `omp/*` returns exit `8` with the exact
branch and proposed effect.

Material checkpoints are:

- completed research or engineering round;
- accepted result promotion;
- terminal run evidence promotion;
- external prompt/archive readiness;
- direction lifecycle create/register/activate/return-to-registered/merge/close/reactivate; and
- schema migration, including cross-role routing owners.

The trigger is event-driven, never a timer or recurring model poller. Before a
dependent dispatch or Root stop, Root validates every changed path, stages only
Root-owned authority paths and assignment-owned paths named by settled
envelopes, commits the checkpoint locally, and attempts its push to
`omp/workflow`. Automatic checkpointing must never use `git add -A`. Unrelated
user changes remain unstaged; a path containing mixed ownership is a conflict.
Checkpoint content excludes ignored runtime state, raw runs, generated logs,
secrets, and unverified source.

Intermediate state updates may batch into the next checkpoint, but no completed
material checkpoint may cross a Root wake-cycle boundary uncommitted. Root
fetches before push and compares the remote SHA; an unknown push outcome is
reconciled before retry and never folded blindly into a later checkpoint.

## 16. Recovery matrix

| Failure | Inspect first | Safe action | Forbidden action |
| --- | --- | --- | --- |
| Pure research task failed | frozen inputs, transcript, checkpoint | new attempt with distinct assignment | treating old partial prose as accepted |
| Manager missing after resume | registry/state and Hub lineage | revive matching generation or reconstruct | creating duplicate live manager blindly |
| Partial code work | worktree, index, diff, candidate SHA | resume or retain for recovery | applying patch twice |
| Run says RUNNING | PID identity, exit file, logs, manifest | observe or mark UNKNOWN | relaunching same command blindly |
| Memory refusal | preflight and estimate | reduce/batch/shard | asking user to approve overcommit |
| Git conflict/stale base | target/base/candidate SHAs | return to Root for new integration plan | auto-resolving semantic conflict |
| Push outcome unknown | fetch remote tip | compare and resume | pushing again without comparison |
| External commitment unknown | Agentify ledger | verify existing/observe | resend |
| Late specialist output | accepted checkpoint SHA | archive as superseded evidence | overwrite newer state |
| Dashboard failure | service logs and health | restart or run without Dashboard | blocking workflow |

Workflow Recovery Manager receives one classified failure and a bounded attempt
budget of three materially distinct safe routes. Repeating the same command or
send with different wording is not a distinct route. Exhaustion returns a user
blocker containing observed facts, attempts, duplicate/effect risk, and exact
resume condition.

## 17. Phased implementation

Each phase follows RED -> GREEN -> focused pressure verification. Do not run the
full repository suite until the final integration phase.

### Phase 0: Freeze baseline and contracts

RED:

1. Add failing contract tests for target config, exactly 17 project agents,
   legacy names absent from active `.omp` definitions/callers, disabled bundled
   agents, depth 2, seven Skills, `.omp/RULES.md`, and `.omp/WATCHDOG.md`.
   Historical documents are provenance and excluded from the legacy-name ban.
2. Add schema fixtures for valid, unknown-version, extra-key, stale-revision,
   invalid-path, wrong-writer, foreign Agentify archive, and both runtime
   registries.
3. Add concurrent initialize/replace/migrate pressure cases and checksum proof
   for losing writers.
4. Add Git ignore-query failures for every new tracked Markdown/JSON contract.
5. Record current headless Advisor tests as migration baseline only.

GREEN:

1. Add the ten schema files and `hmasd_state.py` validator/atomic writer.
2. Update `.gitignore` before creating WATCHDOG, Rules, Skills, Portfolio, or
   external-review Markdown.
3. Keep all workflow features inactive until their state contracts pass.

Acceptance:

- no state file can be partially written;
- stale revision and unsupported version leave bytes unchanged;
- schemas contain no scientific prose fields outside Markdown references.

### Phase 1: OMP topology, Rules, and Skills

RED:

1. Assert the exact target agent names, models, effort, tools, spawn graph,
   non-blocking setting, and skill autoloads.
2. Assert bundled `scout`, `reviewer`, `sonic`, `designer`, and
   `security-reviewer` cannot dispatch.
3. Assert only Root can dispatch bundled `task` and Workflow Recovery Manager.

GREEN:

1. Create the seven Skills, `.omp/RULES.md`, and the active Implementer-only
   `.omp/WATCHDOG.md`.
2. Perform the agent clean rename/add/delete boundary, including removal of the
   Portfolio agent.
3. Disable Root and manager continuous Advisors; opt in only the two Implementer
   leaves and preserve frozen checkpoint review for deep-tree evidence.
4. Update `.omp/AGENTS.md`, recursion depth 2, concurrency, async/launch,
   autoResume, bundled disablement, and checkpoint-review policy.
5. Apply the user-global 372K model overrides without replacing unrelated
   settings.

Acceptance:

- live project-agent discovery lists exactly 17 `hmasd-*` roles;
- Root → EM/CM → project specialist reaches at most depth 2;
- every specialist is a leaf;
- a real dispatch uses `hmasd-project-scout`, not bundled `scout`;
- continuous Advisors run only on scope-frozen Implementer leaves and frozen
  checkpoint review remains available for deep-tree evidence;
- all newly authoritative Markdown paths are visible to Git.

### Phase 2: Portfolio and direction bootstrap

RED:

1. Test unique IDs/abbreviations/jobs, dependency cycles, lifecycle transitions,
   active-count bounds, and one-writer replacement.
2. Test manager startup/resume reconciliation against missing, stale, and
   inconsistent runtime mappings.

GREEN:

1. Preserve the exact existing underscore-bearing stable IDs from
   `RESEARCH_MAP.md`; create `PORTFOLIO.md` and registry from existing research
   sources without inventing conclusions.
2. Create each direction's `DIRECTION.md` and workflow JSON by citing existing
   source documents; historical maps remain provenance.
3. Update `.omp/AGENTS.md` so Root owns lifecycle through the registry while
   `RESEARCH_MAP.md` remains navigation/provenance.
4. Implement bounded Root and EM cycles in Skills/prompts.

Acceptance:

- registered and active directions have no hard count cap;
- active includes runnable work and exact dependency/resource queues;
- Root may enter IDLE with zero qualified directions;
- science routes to EM, code to CM, external critique to Transport, commands to
  Experiment Operators, and decisions to the user;
- return to `REGISTERED` or closure does not delete science;
- no primary model polls while IDLE.

### Phase 3: Git worktrees and CM engineering

RED:

1. In temporary Git repositories and explicit temporary containers, cover
   canonical path escape, initial and mid-provision symlink/container swap,
   target outside `omp/*`, dirty worktree, stale base, target advance between
   prepare/apply, extra commit, out-of-scope path, conflict, orphaned provision,
   branch retention/deletion, ignored-only artifact refuse/discard/retain,
   non-ignored residue refusal, missing verification evidence, and unknown apply
   outcome.
2. Verify a conflict-free candidate cannot apply if any receipt fact changed.

GREEN:

1. Implement `hmasd_worktree.py` from existing safe path/Git primitives while
   replacing the detached lifecycle and receipt protocol.
2. Implement CM/Implementer/Verifier result contracts and engineering state.
3. Migrate callers, update `temp/README.md`, and delete replaced worktree
   helpers.

Acceptance:

- clean candidate integrates once into `omp/workflow`;
- failure leaves target, temporary branch, and worktree recoverable;
- no branch outside `omp/*` changes.

### Phase 4: Resource preflight and observed runs

RED:

1. Cover observation-only capture, missing run estimates, cgroup-limited and
   literal-`max` memory, byte/KiB/GiB boundaries, reserve calculation,
   preflight-to-execute memory change, overcommit refusal, and the 7200-second
   boundary.
2. Cover duplicate claim races, crash after claim, PID reuse/start ticks,
   changed boot ID, orphaned child process group, signal termination, nonzero
   child codes including `2/6/8`, output symlink/escape, and dead leader with a
   live descendant.
3. Prove memory refusal occurs before approval logic and before child creation.
4. Prove an approved frozen `7201` request resumes exactly once while a changed
   request requires a new decision.

GREEN:

1. Rename/extend resource preflight.
2. Implement `hmasd_run.py`, manifest lifecycle, and Operator Skill.
3. Migrate useful worker tests and delete replaced entry points.

Acceptance:

- a short real subprocess produces a complete manifest and captured output;
- a synthetic overcommit and an execute-time memory regression never launch;
- `7200` seconds is automatic; `7201` requests a user decision after review
  attempt evidence and an exact approval resumes once;
- child exit values cannot collide with helper refusal codes;
- cancellation/recovery leaves no live process-group descendant;
- an interrupted RUNNING manifest is observed, never auto-replayed.

### Phase 5: Windows Agentify and external review

RED:

1. In a separately approved Agentify sibling-repository workstream, add failing
   headless startup and existing-target adoption tests.
2. In HMASD, test round identity, blind prompt separation, archive validation,
   monitor partitioning, same-SHA concurrent create, different-SHA conflict, and
   commitment-unknown no-send.
3. Use fake MCP/ledger fixtures; no live send in automated tests.

GREEN:

1. Complete the Agentify headless/reconciliation fallback and its focused tests.
2. Start the configured Windows Agentify with Windows Node, verify the reported
   browser user-data directory and Chrome product are Windows-owned, then set
   HMASD MCP to the exact Windows command.
3. Implement external-review helper, Skill, transport contracts, tracked
   archive, and handoff paths.
4. Update `docs/external-review/README.md`; mark the old `rounds/` layout as
   historical provenance and retire `export_gemini_live_response.py`.

Acceptance:

- provider submits remain provider-specific;
- any monitor can observe an assigned session without send capability;
- a restart adopts and observes an existing tab;
- exact raw SHA survives archive and handoff intake;
- commitment-unknown cannot produce a second send.

### Phase 6: Read-only Dashboard

RED:

1. Test all GET projections and deterministic CLI snapshots from isolated
   fixtures.
2. Test every mutating method returns 405 and changes no file bytes.
3. Test fixed-static-route allowlisting, path traversal, fixed loopback bind,
   secret/environment omission, malformed/missing/stale section status, and a
   registry revision change during aggregation.

GREEN:

1. Implement standard-library service and static UI.
2. Add Root Hub start/reuse instructions and terminal checkpoint summary.

Acceptance:

- service listens only on `127.0.0.1`;
- five views render from actual fixture state;
- browser-drive the actual Dashboard and inspect portfolio, agents, runs,
  external reviews, and worktrees;
- workflow continues when the Dashboard is stopped.

### Phase 7: Recovery, resume, and compaction pressure

RED:

1. Cover every recovery-matrix row, generation mismatch, late result,
   compaction reconciliation, missing runtime map, and exhausted route budget.
2. Prove repeated identical recovery is not counted as distinct.

GREEN:

1. Finalize recovery Skill/agent and Root startup sequence.
2. Add ignored runtime registry reconstruction.
3. Exercise native autoResume and prompt-driven post-compaction reconciliation.

Acceptance:

- a killed Root resumes the same trustworthy generation or rotates from durable
  state;
- no duplicate manager, run, Git effect, or external send is created;
- exhausted recovery reports one precise user-visible blocker.

### Phase 8: Integrated takeover

1. Run focused tests from Phases 0–7 once against the final code.
2. Run project LSP diagnostics on changed Python and agent/config files where
   supported.
3. Run one synthetic Root portfolio reconciliation with two fixture directions.
4. Exercise one depth-2 research dispatch, one parked/revived EM, one no-op CM
   integration in a temporary Git repository, one short observed run, one fake
   external-review completion, and the actual Dashboard.
5. Obtain an independent read-only final diff review using
   `hmasd-reviewer`, not the bundled reviewer.
6. Remove migration fixtures, obsolete agents/scripts, aliases, and temporary
   runtime data.
7. Commit and push the clean boundary to `omp/workflow`.
8. Resume Root from the committed durable state and verify it reaches IDLE
   without user acknowledgment or continuous polling.

## 18. Verification evidence matrix

| Claim | Direct evidence | Owner |
| --- | --- | --- |
| Topology and disablement are exact | discovery/config contract test plus live depth-2 project-scout dispatch | Root |
| Continuous advice is leaf-scoped safely | disabled Root/manager config, exact Implementer mapping check, and frozen checkpoint review contract | Root |
| State is atomic and single-writer | concurrent initialize/replace/migrate, kill-write, checksum, revision, lock, and parent-directory-fsync evidence | Verifier |
| Scientific facts are not duplicated | schema negative fixtures and path/field audit | hmasd-research-principles-analyst |
| Git applies only safe candidates | conflict/path/base tests plus target-advance, orphan provision, multi-commit, branch cleanup, and prepare/apply race | Verifier |
| Run executes at most once | concurrent claim, crash-after-claim, PID reuse/starttime, boot ID, group-orphan, output escape, and child-exit collision tests | Experiment Operator + Verifier |
| Memory overcommit cannot launch | cgroup `max`/unit boundaries, preflight refusal, execute-time TOCTOU recheck, and process-absence proof | Verifier |
| High-cost boundary is correct | 7200/7201 decision envelope, changed-request rejection, and exact approved continuation | Verifier |
| External send cannot duplicate | Agentify strict-ledger tests and commitment-unknown scenario | Agentify tests |
| Archive is exact | response bytes/SHA comparison plus concurrent same-SHA and different-SHA create-if-absent tests | Root with External Transport evidence |
| Dashboard is read-only and coherent | HTTP mutation matrix, static allowlist, revision-change 409, deterministic snapshot, byte checks, and browser smoke | Verifier |
| Resume does not duplicate work | killed-session recovery pressure scenario across manager, run, Git, and external refs | Root |

No test, reviewer, or evidence owner grants approval. Each item establishes or
limits a factual claim.

## 19. Rollback and deletion conditions

- Agent renames are rolled back only by reverting the entire topology commit;
  old aliases are never reintroduced.
- Tracked schema migration code is deleted after every tracked v1 file has been
  migrated and the oldest supported version advances.
- `.omp/runtime` may be deleted whenever no owned process is live; startup must
  reconstruct it.
- A direction worktree is released after integration and clean verification;
  dirty/conflicted worktrees are retained explicitly for recovery.
- Raw local run directories may be deleted after terminal evidence needed for
  accepted results is promoted; accepted provenance must remain meaningful.
- Dashboard may be removed if Agent Hub plus terminal summaries satisfy the five
  observability needs; its absence never blocks research.
- The four-slot advisory reserve is removed if measured OMP queue behavior shows
  it provides no recovery/control benefit.
- The 25% memory margin is replaced only by measured peak-memory evidence and a
  documented safer formula.
- HMASD external archive helpers are narrowed or removed if Agentify later
  exports the exact tracked contract directly; Agentify ledger authority remains.
- Historical concept/design documents remain provenance and are never parsed as
  runtime state.

## 20. Explicitly deferred

The following remain outside this implementation:

- SSH-managed local GPU runs;
- cloud execution;
- a central scheduler or workflow service;
- DVC/MLflow/Prefect package integration;
- a workflow database or event reducer;
- Dashboard mutation controls;
- automatic resolution of scientific conflicts;
- changes to branches outside the OMP-owned `omp/*` namespace without separate
  user approval.
