# HMASD native OMP workflow

This repository uses one user-facing Root OMP session and a bounded,
non-blocking two-level task tree. Roles divide context and capability; they
never grant or deny ordinary authorized reversible work. The authoritative
project inventory is the current `hmasd-*` definitions under `.omp/agents/`;
the target transport inventory contains the singleton
`hmasd-browser-transport`, not provider-specific transport agents.

## Authority and startup

- `.omp/RULES.md` contains the only sticky hard boundaries. Skills and agent
  contracts contain bounded-cycle details.
- Root is authoritative for user scope, the explicit cross-direction Portfolio
  subflow, lifecycle/capacity adoption, routing and runtime reconciliation,
  direct EM/CM dispatch, Root-mediated BrowserTransport serialization,
  recovery, worktree allocation, external archive validation, shared Git
  integration, and final delivery. There is no Portfolio agent.
  `PORTFOLIO.md` remains Root's durable scientific goal, allocation, and
  lifecycle-reason authority; the registry remains lifecycle/dependency
  authority.
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
  other project roles are non-blocking leaves or services. Root executes
  Portfolio work directly; it never creates an intermediate Portfolio agent.
- Root directly invokes EM and CM managers and may directly invoke every project
  leaf. There are no workflow-designer or design-reviewer project roles.
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
- Task items must omit `effort`; role frontmatter selects effort. Source-parity
  tiers: `hmasd-em`, `hmasd-research-critic`, `hmasd-research-innovator`, and
  `hmasd-research-principles-analyst` use `max`; `hmasd-browser-transport` and
  `hmasd-reviewer` use `xhigh`; `hmasd-cm` uses `high`; all other current roles
  remain at or below `high`. Session-init evidence remains the effective-effort
  authority.


## OMP communication and Portfolio semantics

- Every cross-role dispatch uses an OMP `task` or Hub carrier with identity,
  generation, and assignment fields plus meaning-complete sections for
  objective/decision relevance; authorities, inputs, and evidence boundary;
  scope, protected non-goals, and preserved semantics; requested role work;
  authorized Effects; acceptance/stop; and return route, durable references,
  and reentry. Results use the common v1 result envelope and role payload.
- Literal Codex `[WORK]`, `[RESULT]`, and `[BROWSER WORK]` headings are semantic
  source material only. They are not OMP routing authority, identity, receipts,
  or a substitute for the required meaning sections.
- Root's Portfolio subflow adopts one explicit action for every direction in the
  user-fixed considered set. It consumes each terminal EM, CM, Transport, or
  Run fact immediately and actively refills authorized capacity when not
  `PAUSED`; it does not wait for an all-terminal join. `PAUSE` retains current
  work and safe observation of committed Effects but blocks refill, fresh
  dispatch, sends, launches, and all other new Effects.
- Portfolio actions are `NONE`, `ACTIVATE`, `CONTINUE`, `NARROW`, `PARK`,
  `CLOSE`, `FUSE`, and `SPINOFF`. An EM recommendation is evidence, not an
  adopted Portfolio action. Engineering, transport, Run, runtime, and Git facts
  do not imply science or lifecycle.
- Registry lifecycle is exactly `REGISTERED`, `ACTIVE`, `PARKED`, or `CLOSED`.
  `ACTIVE` requires live scientific work or one exact operational reentry.
  `PARKED` has no live direction work, requires
  `reactivation_condition_ref`, and is not `CLOSED`.

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
  and schema migrations.
- Direction-scoped EM and CM cycles own their orthogonal Git checkpoint. Root
  provisions a dedicated assignment worktree; the manager stages only its exact
  assignment paths, creates one cycle-completion commit, applies it with actor
  `em:<direction>` or `cm:<direction>`, fetches, compares, and pushes
  `omp/workflow`. A stale base, dirty target, non-fast-forward, mixed ownership,
  or path/semantic conflict stops unchanged and is reported to Root. Managers
  never auto-resolve cross-direction or shared-authority conflicts.
- Root commits only Root/shared authorities, cross-direction Portfolio changes,
  schemas/control-plane changes, external archive promotion, and recovery
  integration. It does not recommit settled manager-owned paths or create a Git
  checkpoint for every manager transition.
- Every writer uses an exact path allowlist. `git add -A` is forbidden.
  Unrelated user changes remain unstaged; mixed ownership in one path is a
  conflict. Runtime maps, raw runs, generated logs, secrets, and unverified
  source are never checkpoint content.
- Before pushing, the owning writer fetches and compares the remote tip. An
  unknown push outcome is reconciled by fetching before any retry; it is never
  blindly pushed again or merged into a later checkpoint.
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
- Root alone owns shared-authority and recovery integration. An EM or CM may
  apply and push exactly one verified direction/kind-owned candidate from its
  provisioned worktree to `omp/workflow`; all other children never commit or
  push unless their exact assignment names a recovery effect.
- Agentify remains the sole external submission ledger. The configured MCP
  command runs `C:\Projects\agentify-desktop` with Windows `node.exe` from its
  WSL mount, so Agentify opens the user's configured, visible Windows Chrome
  profile. Do not replace it with a Linux browser or Linux Node runtime unless
  the user changes this runtime choice.
- `BrowserTransport` is the singleton logical service, implemented by agent type
  `hmasd-browser-transport`, for both `chatgpt` and `gemini`. EM and CM author
  frozen durable request references and return `next_action.owner=TRANSPORT` to
  Root; they never invoke a provider-specific transport directly. Root validates
  requester, provider, mode, exact operation, model, authorization, commitment,
  and response path, serializes the request through the singleton, validates
  returned archive bytes, and routes the transport fact to the exact requester.
- Unknown commitment never resends. BrowserTransport performs transport only:
  provider conversation, operation, tab, direction, OMP assignment, archive,
  scientific conclusion, engineering acceptance, and lifecycle are distinct
  objects and meanings.

## Direction workspace

Durable direction authority is layered under
`docs/research/candidates/<direction-id>/`: `DIRECTION.md`, accepted
cycle-scoped material in `evidence/`, exact external material in `external/`,
EM state and durable CM requests in `workflow/research/`, and contract-first CM
artifacts in `workflow/engineering/`. Role skills name the standard artifacts,
which are required only after their phase is reached. Disposable output stays
under `temp/directions/<direction-id>/exp/` and `test/`. Raw runs, generated
manifests, profiles, checkpoints, and captured logs remain ignored. A Dashboard
is a read-only derived view and never authority or control surface.
