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
- `autoResume` is enabled. Root's continuous Advisor uses the dedicated
  local-project simplicity route in `.omp/WATCHDOG.md`; `task.agentAdvisor`
  retains separate engineering mappings only for `hmasd-implementer` and
  `hmasd-implementer-terra`. EM, CM, Clerk, Transport, research leaves, and
  every other project role run without a continuous Advisor.
- Root stops only at `IDLE`, `COMPLETE`, an explicit user decision boundary, or
  an exhausted safe recovery route. It never runs a recurring primary-agent
  model poller.

## Project agents and delegation

- Use only the exact project role names in `.omp/agents/`; do not invent aliases,
  compatibility names, or generated per-direction definitions.
- `hmasd-em` and `hmasd-cm` are the only project spawn-capable managers. All
  other project roles are non-blocking leaves or services. `hmasd-clerk`
  implements the one stable logical `Clerk` service: Root assigns it one
  concise frozen mechanical job at a time through task or Hub, then the same
  identity may idle, park, and revive for the next sequential job. Clerk
  cannot spawn, schedule, interpret, choose a successor, or gain science,
  technical, Portfolio, lifecycle, actor, or writer authority. Root executes
  Portfolio work directly; it never creates an intermediate Portfolio agent.
- Root directly invokes EM and CM managers. Direction-scoped science always
  goes to the responsible EM; Root never bypasses that EM by invoking a
  scientific leaf. Root may invoke a project leaf directly only for
  Root-owned work that the leaf contract fits, including the bounded
  cross-direction Portfolio analyses below. There are no workflow-designer or
  design-reviewer project roles.
- Decompose by a coarse vertical outcome, not by consecutive reading, planning,
  implementation, review, and test-writing steps over the same files. One leaf
  owns a bounded engineering slice from investigation through code and focused
  test edits; its parent performs integration review and verification.
  Parallel children require genuinely disjoint repositories, directions,
  owned paths plus semantic interfaces, or role-required independent
  scientific evidence. A separate engineering Reviewer is exceptional: use it
  only when independence on a frozen high-risk candidate is itself required
  evidence, never as a routine second reader of the implementer's context.
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


## OMP communication, analytical dispatch, and Portfolio semantics

- Every cross-role dispatch uses an OMP `task` or Hub carrier with identity,
  generation, and assignment fields plus meaning-complete sections for
  objective/decision relevance; authorities, inputs, and evidence boundary;
  scope, protected non-goals, and preserved semantics; requested role work;
  authorized Effects; acceptance/stop; and return route, durable references,
  and reentry. Results use the common v2 result envelope and role payload.
- If an assignment crosses a material internal boundary before its terminal
  product—for example investigation to implementation, specialist fan-out, a
  newly evidenced blocker, or an exact long-running command start—the owner
  sends Root one concise Hub progress note with **Problem**, **Now**,
  **Evidence**, and **Next**. At most one note is sent per unchanged phase.
  It is an observation, not a result, acceptance, authority, successor edge, or
  state write. Timer heartbeats and per-tool narration are prohibited; Root
  surfaces the transition in its next visible main-transcript note.
- The common v2 result carrier requires `next_actions` as an array and has no
  singular `next_action` alias. Every closed item contains `action_id`, `kind`,
  `owner` (including `CLERK`), `input_refs`, strict `dependencies`,
  `authorized_effect_ref`, and `stop_or_reentry_ref`; all fields are present,
  and an empty array means no successor. Independent simultaneous obligations
  are separate items and array order creates no dependency.
- `dependencies` is strict one-of: either an accepted producer
  `(logical_identity, generation, assignment_id)` plus exact `result_sha256`,
  required status, required payload kind, and required `{path, sha256}` refs;
  or an immutable authority `{path, sha256}` plus exact revision/checkpoint.
  Generic input refs, file or packet presence, job completion, direction,
  salience, timing, and later Git state never satisfy an edge.
- `NodeKey=(logical_identity,generation,assignment_id)` has at most one terminal
  product. Delivery identity is distinct from `NodeKey+result_sha256`, and job
  settlement is not acceptance. Every manager reentry uses a new assignment
  ID. Every Clerk assignment uses a new sequential `job_id` while the logical
  identity remains exactly `Clerk`; compatible scope keeps the same service
  session and material scope change requires a replacement assignment.
- A manager terminal semantic product names `semantic_product_ref` and
  `persistence_status=PREPARED`; unobserved durable, candidate, and integrated
  SHAs remain null. Pending Clerk work does not make the manager's scientific
  or technical semantic product incomplete. Same-direction EM-to-CM waits for
  the exact accepted EM `integrated_sha`, and CM-to-EM result interpretation
  waits for the exact accepted CM `integrated_sha`; explicitly independent
  semantic, Transport, Portfolio, or Clerk obligations may proceed.
- Root supplies each Clerk job as one concise frozen task/Hub assignment with
  its exact actor or writer, canonical targets, inputs, allowed paths,
  authorized effects, competing refusal outcomes, stop, and return route.
  Clerk runs one active job, returns direct observations, then idles or parks.
  It never persists another authorization graph or operation draft, and Root
  never splits one coherent chore into primitive jobs.
- Literal Codex `[WORK]`, `[RESULT]`, and `[BROWSER WORK]` headings are semantic
  source material only. They are not OMP routing authority, identity, receipts,
  or a substitute for the required meaning sections.
- An accountable manager dispatches an analytical leaf only for an unanswered
  information gap that can change that manager's own decision, is separable
  from manager synthesis, benefits from the leaf's method, source, code-map, or
  tool advantage, and can return an inspectable product. The assignment freezes
  the scope, protected semantics and Effects, positive/negative/null/ambiguous/
  failure branches, stop condition, and reentry; accepted evidence must not
  already answer the gap. Zero qualifying gaps dispatch zero leaves. One gap
  dispatches at most one fitting assignment at a time, while several genuinely
  separable gaps may fan out. Counts follow gaps, never a fixed leaf quota,
  wave size, utilization target, vote, majority, or quorum.
- Every analytical assignment carries a neutral packet containing the
  manager-owned variable; frozen question, claim, or contract; authoritative
  definitions and hashed references; facts, evidence, inference, speculation,
  and contradictions kept separate; exact gap and assigned lens; all outcome
  branches; non-goals; ownership and authorized Effects; required output; stop;
  and reentry. First-wave packets contain no favored answer, desired `PASS`,
  sibling conclusion, vote tally, allocation preference, or other result
  leakage. Different first-wave assignments may receive different
  mechanism-level lenses, but each remains blind to sibling results until it
  returns a substantive product or `NO_MATERIAL_INSIGHT`; authoritative
  constraints and known invalidating evidence are never hidden.
- The common analytical product records `assignment_id`, `gap_id`,
  `task_family`, the answered question, `MATERIAL_INSIGHT` or
  `NO_MATERIAL_INSIGHT`, and the concrete claim or product; exact
  source/artifact/observation references and locators; sources inspected and
  methods attempted; assumptions and applicability boundary; verified facts,
  external evidence, inference, speculation, and contradiction separately;
  a falsifier or counterexample and surviving alternatives; uncertainty,
  limitations, and the exact residual gap; the conditional consequence and
  decision relevance for the manager-owned variable; a recommendation; and
  the next discriminator, `DONE_REASON`, and reentry trigger. A leaf's
  recommendation is conditional analysis, never the manager's decision.
- `NO_MATERIAL_INSIGHT` is a successful, terminal, negative-complete
  analytical product: within the frozen scope no answer-changing insight
  follows. It states the sources inspected, methods attempted, why no material
  insight follows, and residual uncertainty. It is not `FAILED`, approval,
  negative scientific evidence, evidence of absence, or scientific rejection,
  and it causes no silent claim change or resampling. Reopen the same
  family/input only after a new mechanism, source, observation, premise, or
  corrected defect. A valid adverse or null scientific observation and a
  technical failure remain separate from `NO_MATERIAL_INSIGHT`.
- Analytical products travel in the role-specific payload of the unchanged
  common v2 result carrier. These rules add no scheduler, authority role,
  lifecycle state, result schema, or registry. Each manager consumes a
  terminal analytical product immediately, closes the answered gap, and fans
  out or refills only for an evidenced residual or newly exposed separable
  gap. It waits only for a live result on which the contemplated action
  actually depends, never for an all-terminal wave.
- Root may dispatch a Portfolio analytical leaf only for a Portfolio-owned
  cross-direction gap in one of four categories: (1) a **shared-assumption
  audit** identifying the dependency, affected directions and layer,
  necessity, common-mode failure path, and independent discriminator; (2) a
  **complement/substitute analysis** returning `COMPLEMENT`, `SUBSTITUTE`,
  `ORTHOGONAL`, `CONDITIONAL`, or `UNKNOWN` with mechanism, conditions,
  evidence, sequencing implication, distinguishing scientific and information
  value, engineering reuse, and common risk; (3) an **option-value analysis**
  identifying the branch opened, preserved, or closed, reversible enabling
  action, exercise/abandon/expiry trigger, information gained, irreversibility,
  dependencies, and bounded cost/time without invented probability or rank; or
  (4) a **cross-direction risk analysis** identifying the mechanism, exposed
  directions, propagation, trigger, blast radius, relatively independent
  check, and reversible mitigation/tradeoff. These leaves return only
  conditional relationships. They never rank directions, allocate resources,
  change lifecycle, write direction state, adjudicate direction science, or
  gain Portfolio or direction authority; Root synthesizes cited mechanisms and
  dependencies, not leaf counts.
- Root's Portfolio subflow adopts one explicit action for every direction in the
  user-fixed considered set. Root projects the runnable graph afresh at each
  material wake, snapshots and drains the finite queued-delivery set, validates
  and causally consumes each accepted/refused result digest once, routes every
  consequence, then dispatches the maximal admissible independent set. It uses
  separate Portfolio, OMP semaphore, BrowserTransport, Experiment Operator, Git
  target, worktree lease, and state-path CAS capacity classes; saturation of one
  does not suppress available work in another.
- Root actively refills authorized Portfolio capacity when not `PAUSED`; it does
  not wait for an all-terminal join or a salient/first child. Per-item partial
  batch registration is reconciled and only items proven not started remain
  runnable; a batch is never retried wholesale. `PAUSE` admits no fresh task or
  Effect, including Clerk, CAS, Git, send, Run, refill, or manager revival. It
  may validate deliveries and non-sendingly observe only an already-committed
  Effect through its existing owner; with none it returns `PAUSED/IDLE`.
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
  `hub logs` observes, and a legal broad coordination `hub wait` races material
  job/message events. Never narrow wait to a slow child or substitute a polling
  loop. Timeout or a useless all-running snapshot is not a new wake.
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
- At `START_OR_RESUME`, each material fan-out/result, verification or
  integration boundary, and immediately before a legal wait or user boundary,
  emit concise human-readable text in the main transcript. Use short
  **Problem**, **Now**, **Evidence**, and **Next** fields, omitting unchanged
  fields. Tool intents, Todo cards, Dashboard state, Hub events, and task result
  cards are not substitutes. Do not expose hidden reasoning.
- The same visible note includes the proof required by R12 in
  `hmasd-root-control`: Portfolio authorized/live/free capacity; OMP
  running/queued limits; queued delivery IDs; unconsumed and consumed result
  keys/digests; runnable and inflight NodeKeys; exact blocked
  dependency/resource edges; current target-mutating operation ID/lock key;
  Run, Transport, worktree, and external refs; and Dashboard status
  (`NOT_CONFIGURED` is valid and non-gating). It is derived evidence, never
  state.
- Material checkpoints are event-driven, not timer-driven: completed research
  or engineering rounds, accepted-result promotion, terminal-run evidence
  promotion, external prompt/archive readiness, Portfolio lifecycle changes,
  and schema cutovers.
- Progress narration is event-driven, not a timer heartbeat or polling loop.
  Users may press `Alt+A` to inspect OMP Agent Hub for live per-agent tool
  activity and open a subagent transcript with `Enter`; this complements but
  does not replace Root's main-transcript explanation.
- EM and CM own semantic authoring in their exact provisioned worktree until
  terminal handoff. They freeze concise mechanical intent for state,
  candidate, or integration work and then become non-writing. Root assigns
  that complete bounded job to the stable `Clerk` under the declared actor
  `em:<direction>` or `cm:<direction>`. The manager resumes writing only after
  terminal Clerk observation and a new Root assignment.
- Root authors Root/shared, cross-direction Portfolio, schema/control-plane,
  and external-archive semantics. For its own non-overlapping tracked paths,
  Root may run the local quick check, stage the exact allowlist, and create one
  local checkpoint directly; this routine reversible path needs no Clerk.
  Remote push still requires an immediate fetch/compare and one known-outcome
  attempt. Direction-owned candidate integration, state CAS, and bounded
  mechanical work explicitly assigned to Clerk remain with that service.
  Clerk never changes actor, writer, allowlist, lifecycle, acceptance, or
  successor and never rebases, retries, or resolves a conflict. Git targets
  stay inside `omp/*`; every candidate must be one direct child of its declared
  source base and must change exactly its declared allowed paths.
- Every writer uses an exact path allowlist. `git add -A` is forbidden.
  Unrelated user changes remain unstaged; mixed ownership in one path is a
  conflict. Runtime maps, raw runs, generated logs, secrets, and unverified
  source are never checkpoint content.
- Before pushing, the owning writer fetches and compares the remote tip. An
  unknown push outcome is reconciled by fetching before any retry; it is never
  blindly pushed again or merged into a later checkpoint.
- Routine reversible local work uses
  `python3 scripts/hmasd_local_check.py --repo <repo> --base <base> --scope <owned-root>`
  by default. It validates the cheap core state, changed direction state,
  changed Python syntax, whitespace, and only directly mapped focused tests.
  Add a behavioral smoke or focused contract check only when the changed
  behavior needs evidence the quick check does not provide.
- Agents skip formatters, linters, project-wide tests, and unrelated
  validation unless their exact assignment says otherwise. Root runs the
  unified/project-wide suite once for a shared control-plane integration or
  final delivery, never after each routine local operation or direction
  checkpoint. Quick-check output is evidence, not authority, and never replaces
  the remote-push, provider, result-command, destructive-path, secret,
  scientific, numerical, RNG, checkpoint, or bit-identity boundaries.

## Native Advisor boundary

`.omp/WATCHDOG.md` is the single role-aware continuous Advisor contract. Root
uses its local-project simplicity route; the two Implementers use the separate
engineering route. Advisors inspect transcript deltas read-only and
non-gating. They never approve, reject, block, authorize, mutate, run tests,
dispatch agents, or become a state authority. The configured matrix, not an
invocation profile or a job-ID mutation, selects the model.
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
- Long-lived JSON mutations use the public `scripts/hmasd_state.py` interface,
  its schema, complete desired input bytes, revision, expected-revision CAS,
  and exit-code contract. The authority owner freezes the desired document;
  an assigned Clerk state job invokes that public interface directly and never
  edits the bytes or wraps the call in another protocol artifact.
- Root alone owns shared-authority and recovery semantics. EM and CM own exact
  direction/kind semantic candidates. None performs target Git; each hands
  Root one concise frozen integration intent. The stable Clerk service executes
  an admitted candidate integration under the original actor. All other
  children never commit or push.
- Agentify remains the sole external submission ledger. The configured MCP
  command runs `C:\Projects\agentify-desktop` with Windows `node.exe` from its
  WSL mount, so Agentify opens the user's configured, visible Windows Chrome
  profile. Do not replace it with a Linux browser or Linux Node runtime unless
  the user changes this runtime choice.
- `BrowserTransport` is the singleton logical service, implemented by agent type
  `hmasd-browser-transport`, for both `chatgpt` and `gemini`. EM and CM freeze
  the exact prompt and request references; Root forwards that request to the
  singleton and routes its receipt back to the requester. No role, state, or
  approval step gates an exact request.
- BrowserTransport follows one line: validate the exact target, operation,
  idempotency key, fingerprint, model, and response path; insert the prompt;
  persist `send_attempted`; perform one hit-tested native Send; observe the
  provider message IDs; archive the response. Failures before `send_attempted`
  retry directly. Once `send_attempted` is true, the operation only observes
  and never sends again. BrowserTransport does not interpret scientific or
  engineering meaning.

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

## On-demand P1 research tools

The following repository skills are optional, on-demand research tools; they
are not agent-profile/config autoloads or default manager dependencies:

- `hmasd-paper-lookup` normalizes bounded scholarly records and makes separately
  authorized named-endpoint retrieval requests.
- `hmasd-hypothesis-mechanisms` generates or validates bounded mechanism cards.
- `hmasd-experimental-design-tools` generates or validates frozen randomized or
  full-factorial experimental schedules.
- `hmasd-scientific-writing-validation` checks local scientific-writing
  metadata records for declared structural consistency.
- `hmasd-symbolic-counterexample-tools` performs bounded symbolic algebra checks
  or encoded counterexample searches.
- `hmasd-scientific-compute-contracts` performs bounded property falsification
  or explicit numerical-artifact comparison.

Activate one only for its exact assigned research or verification gap and its
own frozen input contract. Loading a skill grants no authority or Effect,
including network, provider, experiment, state, Git, lifecycle, or external
Effects; any such action requires its separate existing authorization.
