# HMASD control-plane migration reference

Updated: 2026-08-29

This document is the migration reference for moving the current HMASD workflow to a fresh Codex
Desktop installation, a clean repository clone, or a new root task without losing control-plane
meaning. It is intentionally operational and redundant. It lists the files that define the current
control plane, the files that only mirror or test it, the files that must not be revived as current
authority, and the safe procedure for integrating native Codex worktrees back to `main`.

The current workflow is native-Codex-first. HMASD trusts Codex Desktop tasks, worktrees, thread
history, and configured subagent profiles for task identity and execution routing. The repository
does not rebuild identity, authentication, receipts, retry ledgers, registries, routers, or
schedulers. Repository files define meanings, role boundaries, paths, Effects, durable evidence,
milestones, and tests.

## Migration invariants

1. There is no compatibility path for retired control layers.
2. Current authority is read from `AGENTS.md`, `docs/project/WORKFLOW_PROTOCOL.md`, and the active
   HMASD session skills.
3. Historical workflow files, old task IDs, old prompt packs, old registries, old runtime ledgers,
   and old workflow scripts are provenance only unless the current authority explicitly names them.
4. Native Codex task history is the live conversation record. Do not reconstruct it from repository
   JSON, runtime caches, or archived task summaries.
5. A browser tab is only a local view of a provider conversation. The durable remote object is the
   provider conversation URL or ID.
6. Browser prompt and response hashes are local file evidence only when produced by
   `scripts/hmasd_file_fingerprint.py` or equivalent tool output at the point of use. They are not
   task identity, routing, receipt, approval, or lifecycle authority.
7. Transport failure never implies Portfolio lifecycle action, EM scientific polarity, or CM
   engineering acceptance.
8. Only `CANCELLED` from a received `[CONTROL] Action: CANCEL` can cancel an assignment.
9. `WAITING` retains the same assignment and must name a concrete reentry condition.
10. Shared Git integration is serialized by Root. Direction science, Portfolio authority, and shared
    control changes are not merged by a direction owner.

## Current authority files

These files are active control-plane authority. A migrating Root must read them before acting.

| File | Role in migration |
| --- | --- |
| `AGENTS.md` | Universal semantic kernel injected into every HMASD task. Defines shared field meanings, role boundaries, task configuration, subagent naming, Effect boundaries, and workspace/Git rules. |
| `docs/project/WORKFLOW_PROTOCOL.md` | Sole cross-task transport authority. Defines top-level message flow, Portfolio/EM/CM/BROWSER dispatch, handoff, pause/cancel behavior, milestone snapshots, transport states, and Git writer transfer. |
| `.agents/skills/hmasd-root-task/SKILL.md` | Root local method: user control, shared-core changes, task conflicts, protocol questions, cross-direction Git integration, and reviewed workflow-design implementation. |
| `.agents/skills/hmasd-portfolio-task/SKILL.md` | Portfolio local method: investment, lifecycle, capacity, fusion/separation, allocation-loop behavior, and scientific comparison. |
| `.agents/skills/hmasd-em-task/SKILL.md` | EM local method: scientific question freezing, material cycle, research leaves, Browser consultation, CM handoff, synthesis, and direction authority. |
| `.agents/skills/hmasd-cm-task/SKILL.md` | CM local method: engineering contract, code mapping, implementation, experiment/operator handoff, verification, and Git closure. |
| `.agents/skills/hmasd-browser-conversation/SKILL.md` | Browser Transport local method: long-lived provider-browser service, assignment multiplexing, semantic page observation, send/observe/archive flow, and tab cleanup. |
| `.agents/skills/hmasd-browser-conversation/agents/openai.yaml` | Skill activation policy for Browser Transport. |

Only these five HMASD session skills are role-local top-level methods. A top-level participant uses
its one skill and does not load another top-level role method merely to understand topology. Shared
terms that multiple roles need belong in `AGENTS.md` or `WORKFLOW_PROTOCOL.md`, not inside every
role skill.

## Custom subagent role files

The files below define leaf methods only. They are not top-level session methods and they do not
perform Portfolio, EM, CM, Browser, or Root decisions.

| Code | File | Configured role |
| --- | --- | --- |
| `gl` | `.agents/roles/GENERAL_LEAF.md` | Generic Luna/xhigh bounded chore leaf for downloads, extraction, formatting, fixture generation, and low-context non-mainline tasks. |
| `cs` | `.agents/roles/CM_SCOUT.md` | Read-only unfamiliar-code surface map for CM. |
| `ri` | `.agents/roles/RESEARCH_INNOVATOR.md` | Research mechanism ideation inside an EM-frozen scope. |
| `rp` | `.agents/roles/RESEARCH_PRINCIPLES_ANALYST.md` | Research principle and conceptual-defect analysis inside an EM-frozen scope. |
| `rs` | `.agents/roles/RESEARCH_SCOUT.md` | Research evidence lookup, source grounding, and factual research-side scouting. |
| `rc` | `.agents/roles/RESEARCH_CRITIC.md` | Adversarial scientific critique inside an EM-frozen scope. |
| `im` | `.agents/roles/IMPLEMENTER.md` | Nontrivial assigned implementation observation for CM-owned technical work. |
| `rt` | `.agents/roles/ROUTINE_IMPLEMENTER.md` | Routine implementation or mechanical code/test edits for CM-owned work. |
| `rv` | `.agents/roles/REVIEWER.md` | Independent code/protocol/scientific-boundary review for CM or Root-owned implementation. |
| `vf` | `.agents/roles/VERIFIER.md` | Focused runtime or artifact verification. |
| `op` | `.agents/roles/EXPERIMENT_OPERATOR.md` | One exact result-bearing command launch and process observation. |
| `wd` | `.agents/roles/WORKFLOW_DESIGNER.md` | Workflow/control-plane design proposal leaf. Root must delegate future workflow design here. |
| `dr` | `.agents/roles/DESIGN_REVIEWER.md` | One design review of a frozen `wd` proposal. |

A leaf returns only its local field and evidence to the spawning parent. It does not emit top-level
`[RESULT]` owner fields, make lifecycle decisions, mutate capacity, push Git, launch unassigned
Effects, or broaden scope. Read-only leaves remain read-only. Implementer leaves write only assigned
paths. Verifier leaves write only their assigned proof root under `temp/`.

## Codex configuration files

These files bind repository-side role names to native Codex subagent profiles.

| File | Migration use |
| --- | --- |
| `.codex/config.toml` | Global HMASD Codex settings, `multi_agent_v2`, `max_depth`, `max_threads`, and `[agents.*]` profile registrations. |
| `.codex/agents/hmasd-general-leaf.toml` | `gl` profile. |
| `.codex/agents/hmasd-cm-scout.toml` | `cs` profile. |
| `.codex/agents/hmasd-research-innovator.toml` | `ri` profile. |
| `.codex/agents/hmasd-research-principles-analyst.toml` | `rp` profile. |
| `.codex/agents/hmasd-research-scout.toml` | `rs` profile. |
| `.codex/agents/hmasd-research-critic.toml` | `rc` profile. |
| `.codex/agents/hmasd-implementer.toml` | `im` profile. |
| `.codex/agents/hmasd-routine-implementer.toml` | `rt` profile. |
| `.codex/agents/hmasd-reviewer.toml` | `rv` profile. |
| `.codex/agents/hmasd-verifier.toml` | `vf` profile. |
| `.codex/agents/hmasd-experiment-operator.toml` | `op` profile. |
| `.codex/agents/hmasd-workflow-designer.toml` | `wd` profile. |
| `.codex/agents/hmasd-design-reviewer.toml` | `dr` profile. |

Top-level task model configuration is not encoded as a repository router. It is a native task
creation rule:

| Top-level role | Model | Reasoning |
| --- | --- | --- |
| Portfolio | `gpt-5.6-sol` | `max` |
| EM | `gpt-5.6-sol` | `max` |
| CM | `gpt-5.6-sol` | `high` |
| Browser Transport | `gpt-5.6-luna` | `xhigh` |
| Root | User-selected | User-selected |

Direct-leaf task names use the short display convention
`<code>_<model>_<effort>_<task>`, for example `rv_s_xh_plan`, `gl_l_xh_pdf`,
`wd_l_xh_design`, or `dr_l_mx_review`. This is a display convention only. It is not identity,
receipt, routing, permission, or scientific evidence.

## State and schema files

These files support milestone snapshots and run/result validation. They are mirrors and validators,
not a replacement for native task history.

| File | Meaning |
| --- | --- |
| `scripts/hmasd_state.py` | Strict helper for current EM/CM milestone snapshots. It validates fields, transition rules, path boundaries, and atomic writes. |
| `scripts/schemas/hmasd_research_state.schema.json` | EM/research milestone snapshot schema. |
| `scripts/schemas/hmasd_engineering_state.schema.json` | CM/engineering milestone snapshot schema. |
| `scripts/schemas/hmasd_run_manifest.schema.json` | Local result command/run manifest schema. |
| `scripts/schemas/hmasd_operator_result_v1.schema.json` | Experiment Operator result schema. |
| `scripts/schemas/hmasd_accepted_result.schema.json` | Accepted-result contract schema used by current tests and tools. |

EM and CM keep one current milestone snapshot only when losing it would cause costly repetition or
alter a material judgment. Snapshot states are `WORKING`, `WAITING_REENTRY`, `TERMINAL_GAP`, and
`COMPLETE`. A snapshot is not an event log, retry ledger, identity document, receipt, or lifecycle
authority.

## Browser and fingerprint files

These files are control-plane-relevant because the Browser Transport depends on exact local file
evidence and visible page semantics.

| File | Meaning |
| --- | --- |
| `scripts/hmasd_file_fingerprint.py` | Required helper for prompt/response fingerprinting at point of use. Use it for UTF-8 validation, line-ending-sensitive size/hash reporting, and avoiding LLM-computed hashes. |
| `tests/hmasd_file_fingerprint_test.py` | Contract tests for the fingerprint helper. |
| `tests/hmasd_browser_conversation_contract_test.py` | Static contract tests for Browser Transport vocabulary, states, send boundaries, archive rules, and tab/conversation distinction. |
| `.agents/skills/hmasd-browser-conversation/SKILL.md` | Browser Transport method. Listed again here because it is the operational Browser authority. |

Browser Transport must use visible page facts first. The composer-adjacent actionable `Pro` product
control is HMASD's user-authorized Pro model evidence. Account/profile `Pro` labels are excluded.
Clicking or inspecting a local tab is not the same as creating a provider request. Closing a tab
after a terminal fact is normal cleanup and does not delete or stop the provider conversation.

## Execution and operator files

These files are engineering/runtime support, not workflow identity.

| File | Meaning |
| --- | --- |
| `scripts/hmasd_run.py` | Local result-command launcher and manifest writer. Admission/resource semantics are engineering contracts, not Portfolio science. |
| `scripts/hmasd_resource_preflight.py` | Resource preflight estimation. It does not by itself prove runtime memory behavior. |
| `scripts/hmasd_operator_result.py` | Operator result validation and formatting. |
| `scripts/hmasd_workspace_boundary_guard.py` | Workspace path boundary guard used by local tools. |
| `scripts/hmasd_platform.py` | Platform helper. |
| `scripts/hmasd-resource-preflight.ps1` | PowerShell resource-preflight helper. |
| `scripts/invoke_hmasd_hook.ps1` | Local hook invocation helper. |
| `scripts/new_hmasd_worktree.ps1` | Worktree creation helper. It is not a persistent worktree registry. |
| `tests/hmasd_run_test.py` | Launcher tests. |
| `tests/hmasd_resource_preflight_test.py` | Resource preflight tests. |
| `tests/hmasd_operator_result_test.py` | Operator result tests. |
| `tests/experiment_launcher_paths_test.py` | Launcher/path integration tests. |

Local run manifests, checkpoints, stdout/stderr, and result artifacts are scientific or engineering
evidence. Their hashes are reproducibility/bit-identity facts only; they are not task identity,
transport receipts, approvals, or lifecycle actions.

## Scientific capability files

These files expose the current observation-only scientific tooling layer. They are not a transport
release mechanism and they do not create automatic routing.

| File | Meaning |
| --- | --- |
| `configs/scientific-capabilities-v1.toml` | Current capability catalog. |
| `configs/execution_kernel_v1.json` | Execution-kernel configuration used by current tooling/tests. |
| `scripts/hmasd_science_capabilities.py` | Observation-only CLI for listing/showing/doctoring capabilities and validating evidence. |
| `tests/hmasd_science_capabilities_test.py` | Capability catalog/CLI tests. |
| `tests/hmasd_role_capability_contract_test.py` | Role/capability contract tests. |
| `tests/hmasd_science_environment_test.py` | Science environment smoke/manifest tests. |

The capability CLI must not run experiments, create tasks, install environments, mutate lifecycle,
route work, or score Portfolio decisions.

## Workflow and configuration tests

The following tests are the primary workflow/control checks for migration. They do not replace
reading the authorities.

| File | What it guards |
| --- | --- |
| `tests/codex_config_contract_test.py` | Subagent profile registration, model/reasoning expectations, discovery constraints. |
| `tests/hmasd_native_workflow_contract_test.py` | Native workflow vocabulary, Portfolio/EM/CM/BROWSER boundaries, lifecycle mirror checks, retired-control absence, and key file content. |
| `tests/hmasd_state_contract_test.py` | State helper and schema behavior. |
| `tests/hmasd_browser_conversation_contract_test.py` | Browser Transport and provider-conversation behavior. |
| `tests/hmasd_file_fingerprint_test.py` | Fingerprint helper behavior. |
| `tests/hmasd_role_capability_contract_test.py` | Role/capability boundary checks. |
| `tests/hmasd_science_capabilities_test.py` | Capability catalog and CLI checks. |

Recommended focused migration verification:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest `
  tests/codex_config_contract_test.py `
  tests/hmasd_native_workflow_contract_test.py `
  tests/hmasd_state_contract_test.py `
  tests/hmasd_browser_conversation_contract_test.py `
  tests/hmasd_file_fingerprint_test.py `
  tests/hmasd_role_capability_contract_test.py `
  tests/hmasd_science_capabilities_test.py
```

When integrating direction evidence, add the direction's own focused tests if the patch changes
experiment code, schemas, scripts, or executable evidence. Pure documentation handoff integration
does not require the full experiment suite unless it touches executable paths.

## Research authority and direction files

These files are not control-plane authority, but the workflow depends on them for scientific and
investment context.

| File or pattern | Meaning |
| --- | --- |
| `docs/research/portfolio/PORTFOLIO.md` | Current cross-direction investment authority. |
| `docs/research/portfolio/decisions/*.md` | Portfolio decision rationale and allocation-loop history. |
| `docs/research/portfolio/legacy/*.md` | Historical/provenance-only Portfolio consolidation records. Not current authority unless cited by `PORTFOLIO.md`. |
| `docs/research/candidates/<direction>/DIRECTION.md` | Direction-local scientific authority and current evidence map. |
| `docs/research/candidates/<direction>/*.md` | Direction-local durable evidence, Pro prompt/response archives, terminal gaps, handoffs, and EM/CM outputs. |
| `docs/research/candidates/<direction>/workflow/research/state.json` | Current EM milestone snapshot if present and valid. |
| `docs/research/candidates/<direction>/workflow/engineering/state.json` | Current CM milestone snapshot if present and valid. |
| `experiments/candidates/<direction>/` | Direction source and runnable experiment code. |
| `tests/experiments/candidates/<direction>/` | Direction-specific tests. |
| `temp/directions/<direction>/` | Raw run artifacts. Usually untracked and not a migration authority. |

Do not import invalid stale `state.json` snapshots from old worktrees. If a direction worktree has
valid science/evidence documents plus an invalid or retired snapshot, integrate the durable evidence
and leave the state snapshot out unless the owner explicitly returns a current-protocol valid state.

## Project reference files with workflow relevance

These files are not the primary workflow protocol, but they can affect technical interpretation,
runtime staging, or migration context.

| File | Use |
| --- | --- |
| `docs/project/PROJECT_MAP.md` | Repository map. |
| `docs/project/ALGORITHM_PRINCIPLES.md` | Scientific/algorithm principle background. |
| `docs/project/EFFICIENCY_PRACTICES.md` | Engineering efficiency practices. |
| `docs/project/ENGINEERING_ADDITIONS.md` | Engineering additions and conventions. |
| `docs/project/EXECUTION_BACKEND_REGISTRY.toml` | Execution backend registry. |
| `docs/project/CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md` | Production policy for C++ batched environment. |
| `docs/project/UAV_G0_READINESS_PERFORMANCE_CONTRACT.md` | UAV G0 readiness/performance contract. |
| `docs/project/UAV_ENVIRONMENT_PERFORMANCE_AUDIT.md` | UAV environment performance audit. |
| `docs/project/CODEX_DESKTOP_PERMISSION_MODE_NOTE.md` | Note about current Codex Desktop permission-mode behavior. |
| `docs/project/SELF_CONTAINED_SKILL_BEHAVIORAL_VALIDATION_20260829.md` | Current skill behavior validation note. |
| `docs/project/templates/EXPERIMENT_MANIFEST_TEMPLATE.toml` | Experiment manifest template. |
| `docs/project/templates/RESOURCE_PREFLIGHT_TEMPLATE.toml` | Resource preflight template. |
| `temp/README.md` | Temporary-output and worktree location conventions. |

If any of these conflict with `AGENTS.md` or `WORKFLOW_PROTOCOL.md`, the conflict must be resolved
by updating or explicitly retiring the older wording. Do not let two versions of the control layer
coexist as equal authority.

## Historical and non-authority locations

These locations may contain useful provenance but are not current control-plane input.

| Location | Migration treatment |
| --- | --- |
| `docs/project/archive/**` | Historical project/control documents. Read only when provenance is explicitly needed. |
| `docs/archive/**` | Historical repository material. Not active workflow authority. |
| `docs/research/workflow/**` and `docs/research/workflow-runs/**` | Historical workflow notes/runs unless current protocol explicitly cites a specific artifact. |
| `.codex/runtime/**` | Ignored local runtime state. Do not use as durable authority or migrate. |
| `.scratch/**` | Ignored scratch files and old registry/clerk artifacts. Do not use as current authority. |
| Old `C:/Projects/HMASD-worktrees/*` control-plane or engineering branches | Treat as historical/in-flight unless Root explicitly integrates exact owned paths. Do not bulk merge. |
| Archived Codex tasks | Provenance only. Do not reuse as current Portfolio/EM/CM/Browser participants unless current protocol and user explicitly reappoint them. |

Current migration must not resurrect `Workflow-Clerk`, old registries, old controller scripts,
heartbeat monitors, receipt ledgers, envelope releases, or state schemas from retired control
versions.

## Top-level operating model

### Root

Root receives user control, owns shared-core changes, integrates Git, resolves task conflicts, and
implements approved control-plane changes. Root does not design workflow topology in the main
session. Future workflow-control designs are assigned to `wd` and reviewed exactly once by `dr`;
Root then implements only the approved design.

Root sends bounded shared engineering to a dedicated top-level `CM/shared`. Root does not borrow a
direction CM and does not call engineering leaves directly for shared implementation work.

### Portfolio

Portfolio owns cross-direction allocation. It compares scientific evidence, lifecycle state,
priority, capacity, fusion/separation, and refill decisions. It must distinguish allocated slots
from actual operational liveness. A retained `WAITING_REENTRY` direction can occupy capacity, but
Portfolio must not call it actively executing if no owner task is currently running.

Portfolio consumes terminal EM results immediately, makes independent lifecycle/refill decisions
from valid science, commits Portfolio authority before dispatch, and keeps capacity filled when
authorized. Transport and engineering failures are evidence-availability facts only unless they
also produce valid scientific evidence through the responsible owner.

### EM

EM owns direction science. It freezes a falsifiable scientific question, authors Pro prompts,
selects research leaves when needed, sends Browser work directly to Browser Transport, requests CM
only for executable observations, synthesizes evidence, updates direction authority, and returns a
recommendation to Portfolio.

EM recommendations do not perform Portfolio actions. `Recommendation: PARK` is advice. Portfolio
must independently adopt or reject it.

### CM

CM owns engineering. It maps unfamiliar code with `cs` when needed, uses implementer leaves for
bounded code work when appropriate, uses reviewer/verifier/operator for the correct engineering
facts, integrates assigned paths, and returns engineering/observation/verification status to its
caller.

CM never makes scientific lifecycle decisions. A technical failure can invalidate an observation
or implementation, but it does not park a direction.

### Browser Transport

Browser Transport is one long-lived Luna/xhigh task that receives direct `[BROWSER WORK]` from EM
or CM. It may manage multiple independent assignments, but every result returns only to the
assignment's `Return task`. It never contacts Portfolio and never interprets owner content.

The assignment tuple is:

```text
Return task + Direction + Owner stage + Transport assignment
```

This tuple keeps the owner route separate from provider conversation identity. A strict operation is
one send-capable attempt inside that assignment. A provider conversation is the remote ChatGPT/Gemini
conversation URL/ID. A browser tab is a replaceable local view.

## Browser send/observe/archive procedure

1. Read the exact `[BROWSER WORK]`.
2. Identify the `Return task`, direction, stage, frozen prompt path/content, response archive path,
   expected provider, expected product/model premise, and operation budget.
3. Use `scripts/hmasd_file_fingerprint.py --require-utf8` for local prompt evidence. Do not compute
   hashes mentally.
4. Open or reuse the provider page according to the assignment. Use visible page state, not hidden
   assumptions, as the main evidence.
5. Treat composer-adjacent actionable `Pro` as the user-authorized Pro product control. Exclude
   account/profile `Pro`.
6. Verify clean composer state before injecting. If a stale draft is present, preserve or clear it
   only under the owner-authorized provenance rule.
7. Inject the exact frozen prompt once.
8. Click Send at most once for that strict operation.
9. Wait for natural completion using visible page facts: generation controls, page responsiveness,
   provider conversation URL/ID, and stable response content. Do not use time alone as completion.
10. Archive the full response to the owner-supplied path.
11. Reread and fingerprint the archive with `scripts/hmasd_file_fingerprint.py --require-utf8`.
12. Return `[BROWSER RESULT]` to the exact `Return task`.
13. Close terminal tabs when the provider fact is captured. Closing a tab does not delete the
    remote conversation.

If the original tab is closed but the provider conversation URL exists, observation may reopen the
same conversation in a fresh tab without sending. Original-tab closure is not by itself a failure.

## Transport-state interpretation

Use the transport state vocabulary from `AGENTS.md`. The operational consequences are:

| State | Consequence |
| --- | --- |
| `PENDING` | No send-capable call occurred. |
| `ZERO_SEND_FAILED` | Provider definitely received no request for that operation. Page-local repair may proceed only within the owner acceptance and changed premise. |
| `COMMITMENT_UNKNOWN` | Do not resend. Observe the same operation/conversation if possible. |
| `SENT_WAITING` | Exact request was sent and generation is still in progress. Observe only. |
| `COMPLETE` | Prompt matches, model/product premise is satisfied, full natural response is archived. |
| `SENT_INPUT_MISMATCH` | Send occurred but provider-visible request differs. Isolate conversation; no science. |
| `SENT_MODEL_MISMATCH` | Send occurred under wrong model/product. Isolate conversation; no science. |
| `SENT_UNREADABLE` | Send occurred but full response cannot yet be archived. Observe only. |
| `CONVERSATION_LOST` | Provider positively reports permanent conversation loss after same-account reopening and bounded recovery. |
| `WAIVED` | User waived that exact operation before send-capable work. |

Do not convert `ZERO_SEND_FAILED` into direction failure. Do not convert `SENT_INPUT_MISMATCH` into
Portfolio action. Do not use a closed tab as proof that a provider conversation is gone.

## Git integration procedure

Use this procedure for every worktree-to-main integration.

1. Confirm `C:/Projects/HMASD` is on `main` and do not switch branches there.
2. Confirm `git status --short` is clean or contains only the files Root currently owns.
3. Identify the source worktree path, source commit, source owner, baseline commit, exact owned
   paths, and explicitly excluded paths.
4. Inspect the source diff path-by-path. Do not bulk merge a task branch unless the whole branch is
   known to be the desired main history.
5. For direction-local handoffs or evidence, integrate only the named
   `docs/research/candidates/<direction>/...` files unless the owner explicitly assigned code/test
   paths.
6. For Portfolio authority, integrate only `docs/research/portfolio/PORTFOLIO.md` and the named
   `docs/research/portfolio/decisions/...` or `legacy/...` files.
7. For shared tests, update only mechanical mirrors that conflict with current Portfolio authority.
8. Reject invalid stale `workflow/.../state.json` files unless the current owner emitted them under
   the current schema.
9. Reject retired control-layer files unless the user explicitly asks to archive them as history.
10. Verify blob equivalence for exact source-owned files when a source commit is named.
11. Run focused tests. For workflow-only changes, run the workflow/state/browser/fingerprint suite.
12. Commit Root integration on `main`.
13. Push `main`.
14. Only after the needed files are integrated and pushed, recycle local worktrees that are
    terminal, clean, and no longer needed by a live Codex task.

Never run `git reset --hard`, `git checkout --`, or branch switching in Root's main checkout unless
the user explicitly authorizes that exact destructive operation.

## Worktree recycling procedure

Worktree recycling is allowed only after integration or explicit exclusion is complete.

1. List worktrees with `git worktree list --porcelain`.
2. For each candidate, record path, branch or detached commit, and whether it belongs to an active
   native task.
3. Run `git -C <worktree> status --short`. Dirty worktrees are not removed unless the user explicitly
   accepts losing or relocating those files.
4. Confirm the path is under one of the intended worktree roots:
   `C:/Users/fires/.codex/worktrees/` or `C:/Projects/HMASD-worktrees/`.
5. Do not remove `C:/Projects/HMASD`.
6. Do not remove active EM/CM/Browser worktrees that are still needed for same-task reentry.
7. Use `git worktree remove <exact-path>` for clean terminal worktrees.
8. If Git refuses because the directory is dirty, stop and report the exact files.

Old physical worktrees under `C:/Projects/HMASD-worktrees/` are not automatically disposable. Many
belong to retired control-plane or historical engineering branches. They require a separate
owner/path audit before removal.

## Current migration snapshot

As of this reference update, the current Root main line has integrated recent direction/Portfolio
handoff evidence through these Root commits:

| Commit | Meaning |
| --- | --- |
| `01ab59cfa8f9dfb59d09b8a71155fde8e1acef6d` | Integrated DEARS semantic-currentness R02 terminal evidence. |
| `7555d2a03f39ce05007dc20dea51a14c2ed72881` | Integrated DEARS R02 pause handoff. |
| `893716a6e517f129d9ed1a04878284d407e8580c` | Integrated current direction worktree evidence from selected native direction worktrees, excluding invalid stale state snapshots and protected FSBS DIRECTION wording. |

Do not infer scientific decisions from these integration commits. They are Git preservation facts.
Portfolio authority in `docs/research/portfolio/PORTFOLIO.md` remains the place where lifecycle and
capacity decisions are recorded.

## Common migration failure modes

1. Treating Codex task status as workflow status. `active`, `idle`, `completed`, `archived`, and
   `notLoaded` are native process states only.
2. Treating `Outcome: DONE` as positive science. It only means the assignment acceptance was
   answered.
3. Treating an EM recommendation as Portfolio action.
4. Treating a Browser tab ID as a provider conversation ID.
5. Requiring the original tab for same-conversation observation.
6. Treating a local hash as authentication or receipt.
7. Computing hashes by LLM instead of `scripts/hmasd_file_fingerprint.py`.
8. Treating transport failure as scientific failure.
9. Treating a stale mechanical test assertion as current Portfolio authority.
10. Importing invalid old `state.json` snapshots because they came from a direction worktree.
11. Bulk-merging old worktree branches that contain retired control files.
12. Putting global topology into role-local skills until a role mistakes another role's field for
    its own.
13. Reopening retired `Workflow-Clerk`, registry, envelope, router, monitor, or receipt-ledger
    concepts.
14. Leaving Browser tabs open after terminal capture and exhausting local memory.
15. Describing retained `WAITING_REENTRY` capacity slots as actively executing when their owner
    tasks are idle.

The safe corrective pattern is simple: read the current authorities, preserve native task history,
integrate only exact owned paths, use scripts for mechanical file evidence, run focused tests, and
keep each role inside its semantic slice.
