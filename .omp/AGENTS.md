# HMASD native OMP workflow

This repository uses one user-facing Root OMP session and a bounded,
non-blocking two-level task tree. Roles divide context and capability; they
never grant or deny ordinary authorized reversible work. The exact active
project inventory is the 17 `hmasd-*` definitions under `.omp/agents/`.

## Authority and startup

- `.omp/RULES.md` contains the only sticky hard boundaries. Skills and agent
  contracts contain bounded-cycle details.
- Root is authoritative for user scope, cross-direction Portfolio ranking and
  lifecycle, direct EM/CM dispatch, recovery, worktree allocation, external
  archive validation, Git integration, and final delivery. `PORTFOLIO.md`
  remains Root's durable scientific goal and lifecycle-reason authority; the
  registry remains the lifecycle/dependency authority.
- At `START_OR_RESUME`, Root loads `hmasd-root-control` and
  `hmasd-git-integration`, reads `PORTFOLIO.md`, and reconciles registry,
  direction states, runtime mappings, Hub jobs, worktrees, run manifests,
  Agentify references, and Git before dispatch.
- Root repeats that prompt-driven reconciliation after resume or a detected
  compaction boundary. It uses the persisted goal reference, not a generic
  persistent-goal engine or a post-compaction hook.
- `autoResume` is enabled and Root's continuous Advisor is disabled in
  `.omp/config.yml`. `task.agentAdvisor` contains only the two Implementer
  leaves, enabling engineering advice for `hmasd-implementer` and
  `hmasd-implementer-terra`. Every other project role runs without a
  continuous Advisor.
- Root stops only at `IDLE`, `COMPLETE`, an explicit user decision boundary, or
  an exhausted safe recovery route. It never runs a recurring primary-agent
  model poller.

## Project agents and delegation

- Use only the exact project role names in `.omp/agents/`; do not invent aliases,
  compatibility names, or generated per-direction definitions.
- `hmasd-em` and `hmasd-cm` are the only project spawn-capable managers. All
  other project roles are non-blocking leaves; there is no Portfolio agent.
- Root directly invokes EM and CM managers and may directly invoke every project
  leaf.
- The bundled `task` agent is Root-only and may be used only when no project
  role fits. The bundled `librarian` is available to Root, EM, and CM. Only Root
  may dispatch `hmasd-workflow-recovery-manager`; managers do not spawn it.
- Bundled agents disabled in config cannot be used as substitutes for explicit
  project roles. Repository investigation uses `hmasd-project-scout`, code
  investigation uses `hmasd-code-scout`, and scientific investigation uses
  `hmasd-research-scout`.
- Every task agent is non-blocking and asynchronous. Specialists are leaves;
  missing reviewer, test, Dashboard, or Advisor output is an evidence gap, not
  a permission failure.
- Use `task` with `maxRecursionDepth: 2` only for a valid declared spawn edge.
  Root → EM/CM → specialist is the maximum path.
- Task-item `effort` overrides role frontmatter when enabled and coarse `hi`
  selects the model's highest supported tier, which is `max` for GPT-5.6.
  Therefore `task.enableEffort` remains disabled: every project role uses the
  audited `thinking-level` in its `.omp/agents/<role>.md`. Do not pass per-task
  effort hints or silently raise a low/medium/high operational role to `max`.


## Hub lifecycle

- Use Hub lifecycle commands for long-running processes: `hub start` launches,
  `hub logs` observes, and `hub wait` waits for readiness or terminal
  completion. Do not substitute a polling loop.
- The Experiment Operator owns exactly one result-bearing command from
  `hub start` through terminal return and records its observed manifest.
- A parked EM or CM session is revived by a parent Hub message carrying only
  material transitions. File changes, process exits, or Hub completion wake
  bounded reassessment; they do not create successor sessions automatically.
- Cross-task callers invoke documented CLIs and declared role names, never
  private helper functions or duplicate state writers.
- Start the optional Dashboard through Hub under the stable process name
  `hmasd-dashboard`: `python3 scripts/hmasd_dashboard.py serve --root <repo>
  --port <port>`. Reuse an already-ready process; readiness requires both the
  service banner and its `127.0.0.1` TCP port. Stopping it never stops workflow.
- At each material checkpoint, print a compact terminal summary containing the
  registry revision, logical manager/job generations, run terminal states,
  external round references, worktree references, exact blockers, and the
  Dashboard URL when running. The summary is derived evidence, never state.
- Material checkpoints are event-driven, not timer-driven: completed research
  or engineering rounds, accepted-result promotion, terminal-run evidence
  promotion, external prompt/archive readiness, Portfolio lifecycle changes,
  and schema migrations. Before a dependent dispatch or any Root stop, Root
  commits the checkpoint and attempts its push to `omp/workflow`; no completed
  checkpoint may cross a Root wake-cycle boundary uncommitted.
- Root stages only validated Root-owned authority paths and assignment-owned
  paths named by settled envelopes. `git add -A` is forbidden for automatic
  checkpoints. Unrelated user changes remain unstaged; mixed ownership in one
  path is a conflict. Runtime maps, raw runs, generated logs, secrets, and
  unverified source are never checkpoint content.
- Before pushing, Root fetches and compares the remote tip. An unknown push
  outcome is reconciled by fetching before any retry; it is never blindly
  pushed again or merged into a later checkpoint.
- Agents skip formatters, linters, project-wide tests, and unrelated
  validation unless their exact assignment says otherwise. Root performs
  unified validation after integration.

## Native Advisor boundary

`.omp/WATCHDOG.md` is the single role-aware continuous Advisor contract.
Advisors inspect transcript deltas read-only and non-gating. They never approve,
reject, block, authorize, mutate, run tests, dispatch agents, or become a state
authority. The configured matrix, not an invocation profile or a job-ID
mutation, selects the model.
- Hub steering may be absent from an Advisor transcript. Implementer
  assignments are therefore scope-frozen after spawn: a material change to
  goals, non-goals, owned paths, authorization, or interfaces cancels that leaf
  and dispatches a replacement with the complete assignment. Ordinary EM/CM
  managers have no Advisor and may accept compatible Hub updates in place.
  Without complete scope context, an Advisor may request reconciliation but
  cannot issue a blocker.

## Root-managed paths and state

- Use repository-relative POSIX tracked references without `..`, symlinks, or
  absolute prefixes. Concrete handles, PIDs, absolute worktree paths, and
  local tab mappings stay under ignored `.omp/runtime/` or `temp/`.
- All long-lived JSON goes through `scripts/hmasd_state.py` and its schema,
  revision, expected-revision CAS, and exit-code contract.
- Root alone applies a verified single candidate to `omp/workflow`. Children
  preserve user changes and never commit or push unless their exact assignment
  says so.
- Agentify remains the sole external submission ledger. The configured MCP
  command runs `C:\Projects\agentify-desktop` with Windows `node.exe` from its
  WSL mount, so Agentify opens the user's configured, visible Windows Chrome
  profile. Do not replace it with a Linux browser or Linux Node runtime unless
  the user changes this runtime choice.
- Unknown commitment never resends; Root validates exact returned archive bytes
  without rewriting the foreign archive schema. After restart, Root recovers an
  exact operation only through `verifyExisting`/`agentify_review_observe`.
- Pro and Gemini transports share the strict `agentify_review_query` ledger tool
  but bind it respectively to `provider: chatgpt` and `provider: gemini`;
  cross-provider submission and generic send/browser/write/shell paths remain
  forbidden.

## Direction workspace

Direction work uses `temp/directions/<direction-id>/exp/` and `test/` for
disposable output, with durable definitions and accepted result pairs under
`docs/research/candidates/<direction-id>/`. Raw runs, generated manifests,
profiles, checkpoints, and captured logs remain ignored. A Dashboard is a
read-only derived view and never an authority or control surface.
