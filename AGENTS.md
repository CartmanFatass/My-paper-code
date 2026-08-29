# HMASD native Codex workflow

HMASD trusts the task/session plane visible in Codex Desktop. The repository constrains meanings,
roles, paths, Effects, milestones, scientific evidence, and experiment results. It does not rebuild
task identity, authentication, message receipts, retry ledgers, registries, routers, or schedulers.

## Authority and reading boundaries

- This file is the universal semantic kernel injected into every HMASD task.
- `docs/project/WORKFLOW_PROTOCOL.md` is the sole cross-task transport authority.
- `.agents/roles/<ROLE>.md` owns only that role's method. A participant reads its own role document;
  it does not load another role's method merely to understand the topology.
- The four session skills are only entry pointers: `hmasd-root-task`, `hmasd-portfolio-task`,
  `hmasd-em-task`, and `hmasd-cm-task`.
- Direction science lives in `docs/research/candidates/<direction>/DIRECTION.md` and its cited
  evidence. Current cross-direction investment lives in `docs/research/portfolio/PORTFOLIO.md`.
- Native task history is the live conversation record. EM and CM each keep one current milestone
  snapshot only when losing it would cause costly repetition or alter a material judgment.

Historical workflow documents, prompts, fixtures, tasks, or scripts that conflict with these
authorities are not active input. There is no compatibility path for retired control versions.

## Shared field semantics

This section is the only human-readable glossary for shared top-level, transport, and leaf result
fields and exhaustive values. Schemas and tests may mirror values mechanically but do not define
their meaning.

Fields belong to distinct namespaces and cannot be inferred from one another. `Outcome:` describes
only whether the current inbound `[WORK]` was completed; it never states whether science was
positive, implementation succeeded, a provider request completed, or a direction should continue.

| Owner | Fixed fields and exhaustive values |
| --- | --- |
| Any top-level task | `Outcome: DONE | WAITING | FAILED | CANCELLED` |
| Root | `Root status: IN_PROGRESS | CHANGED | UNCHANGED | BLOCKED`; `Integration status: IN_PROGRESS | INTEGRATED | NOT_INTEGRATED | NOT_APPLICABLE` |
| Portfolio | `Portfolio action: NONE | ACTIVATE | CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF`; `Capacity action: KEEP | SET <n>` |
| EM | `Scientific status: IN_PROGRESS | SYNTHESIZED | NO_MATERIAL_INSIGHT | NOT_REACHED`; `Decision impact: <text or NONE>`; `Recommendation: NONE | CONTINUE | NARROW | PARK | CLOSE | FUSE | SPINOFF`; `Pro Innovator: <transport state>`; `Pro Convergence: <transport state>` |
| CM | `Engineering status: IN_PROGRESS | IMPLEMENTED | UNCHANGED | BLOCKED | NOT_REACHED`; `Observation status: IN_PROGRESS | OBSERVED | NOT_OBSERVED | NOT_REQUIRED`; `Verification status: IN_PROGRESS | SATISFIED | UNSATISFIED | NOT_RUN`; `Commit: <git commit or NONE>` |

Top-level outcome meanings are exhaustive:

- `DONE`: the assignment acceptance was answered, including a negative or null scientific result.
- `WAITING`: the same assignment is still held and has a concrete reentry condition.
- `FAILED`: the assignment ended without satisfying its acceptance.
- `CANCELLED`: only a received `[CONTROL] Action: CANCEL` can produce this value, after committed
  Effects reach an observable safe terminal fact.

Role-owned field values are equally independent:

- Root `IN_PROGRESS` means the shared assignment is still advancing; `CHANGED` means its requested
  shared artifact or contract materially changed; `UNCHANGED` means acceptance was answered without
  such a change; `BLOCKED` means Root cannot satisfy the shared acceptance. Integration
  `IN_PROGRESS` is still underway, `INTEGRATED` is present in the intended Git target,
  `NOT_INTEGRATED` is absent from that target, and `NOT_APPLICABLE` means no Git integration was
  required.
- Portfolio `NONE` makes no lifecycle decision; `ACTIVATE` starts active investment; `CONTINUE`
  retains the current scope; `NARROW` retains only a smaller stated scope; `PARK` retains the
  direction without active investment; `CLOSE` ends investment in that direction; `FUSE` merges its
  surviving question into another direction; `SPINOFF` creates a distinct direction. `KEEP` leaves
  the advancing-capacity limit unchanged; `SET <n>` replaces it with the stated nonnegative limit.
- EM `IN_PROGRESS` means the scientific acceptance is still being pursued; `SYNTHESIZED` means the
  frozen question was answered at a bounded claim ceiling; `NO_MATERIAL_INSIGHT` means the scientific
  acceptance was completed but produced no decision-changing insight; `NOT_REACHED` means no valid
  scientific synthesis was reached. `Decision impact` states the supported change to the investment
  question, or `NONE`. An EM recommendation uses the Portfolio action meanings above as advice only;
  it never performs the action.
- CM engineering `IN_PROGRESS` means the engineering acceptance is still being pursued;
  `IMPLEMENTED` means the requested change is present; `UNCHANGED` means acceptance was answered
  without a code/configuration change; `BLOCKED` means the engineering acceptance was not satisfied;
  `NOT_REACHED` means engineering work did not reach a valid candidate. Observation `IN_PROGRESS`
  is still being acquired, `OBSERVED` is the requested valid observation, `NOT_OBSERVED` means no
  valid observation was obtained, and `NOT_REQUIRED` means none was requested. Verification
  `IN_PROGRESS` is still running, `SATISFIED` supports engineering acceptance, `UNSATISFIED` does not,
  and `NOT_RUN` means no verification ran. `Commit` is the exact Git commit containing the returned
  Git-visible work, or `NONE` when no such commit exists.

EM/CM milestone snapshots use a separate shared state:

- `WORKING`: the same inbound WORK is actively advancing.
- `WAITING_REENTRY`: the same WORK remains live and names one concrete reentry condition.
- `TERMINAL_GAP`: the current WORK ended before the role's final milestone and no live Effect
  remains.
- `COMPLETE`: the current WORK reached the role's final milestone and no live Effect remains.

`WAITING_REENTRY → WORKING` resumes the same WORK. A terminal snapshot can become nonterminal only
when native history supplies a successor WORK that opens a fresh research cycle or engineering
scope; a terminal snapshot never reopens the old cycle or scope.

While a requested leaf or top-level callee is still running, a provider operation is unresolved, or
a launched process lacks a terminal witness, the owner retains the same WORK and continues native
wait or same-operation observation. If progress genuinely requires a later external reentry, it may
yield `Outcome: WAITING` with that same assignment and a concrete condition. A wait timeout, stale
status, clipped/unreadable response, or lost process observation is not completion and cannot
produce `DONE`, `FAILED`, or `CANCELLED` or release the target. `PAUSE` also retains the same WORK;
`CANCELLED` remains unavailable until every committed Effect has a safe terminal fact.

Transport states are shared facts for both Pro and engineering transport. Each value describes one
strict send operation inside one provider conversation. A browser tab is only a replaceable view of
that conversation; neither tab nor operation is an EM material cycle or a top-level WORK.

- `PENDING`: no send-capable call occurred.
- `ZERO_SEND_FAILED`: the provider definitely received no request and created or advanced no
  provider conversation for this operation.
- `COMMITMENT_UNKNOWN`: whether the provider received the request cannot be proved.
- `SENT_WAITING`: the exact request was sent and natural generation is still in progress.
- `COMPLETE`: the provider-visible request matches the frozen prompt and the naturally completed
  full response is archived.
- `SENT_INPUT_MISMATCH`: a send is confirmed but the provider-visible request differs from the
  frozen prompt.
- `SENT_MODEL_MISMATCH`: a send is confirmed but the provider-visible model differs from the exact
  owner-required visible model.
- `SENT_UNREADABLE`: a send is confirmed but the full response cannot yet be archived.
- `CONVERSATION_LOST`: after same-account direct reopening and bounded non-sending recovery, the
  provider positively reports that the exact conversation no longer exists or is permanently
  unavailable. The old operation is isolated and any late old-conversation content is quarantined.
- `WAIVED`: the user waived that exact operation before any send-capable call.

`COMMITMENT_UNKNOWN`, `SENT_WAITING`, and `SENT_UNREADABLE` retain the same operation and provider
conversation; observation may move to another tab but cannot send. `ZERO_SEND_FAILED` permits one
bounded repair followed by a fresh strict operation because no provider injection occurred.

`SENT_INPUT_MISMATCH`, `SENT_MODEL_MISMATCH`, and `CONVERSATION_LOST` isolate the old operation and
conversation and supply no scientific, engineering, Portfolio, or lifecycle conclusion. When the
same frozen request is still required, its owner may start at most one automatic replacement in a
new provider conversation while retaining the same top-level WORK and, for EM, the same material
cycle. The current Pro-stage snapshot records only whether that single replacement was used; it is
not an attempt ledger. Native history retains the underlying isolation fact. The same prompt is
never injected twice into one
provider conversation, and late content from an isolated conversation is never evidence for its
replacement. If a concrete user decision or waiver can still satisfy the assignment, the owner
retains `WAITING` for that exact reentry. If a required consultation has exhausted this replacement
boundary, no live Effect remains, and no waiver applies, the current assignment ends `FAILED` with
the owner's actually reached role fields and no lifecycle recommendation; it never becomes
`CANCELLED`. Transport failure cannot imply `PARK`, `CLOSE`, or any other Portfolio action.

Leaf observations are also separate namespaces:

| HMASD task-name code | Configured custom subagent | Own final field |
| --- | --- | --- |
| `gl` | `hmasd-general-leaf` | `Chore status: COMPLETE | PARTIAL | UNAVAILABLE` |
| `cs` | `hmasd-cm-scout` | `Surface status: MAPPED | PARTIAL | UNAVAILABLE` |
| `ri` | `hmasd-research-innovator` | `Innovation status: CANDIDATE | NO_SURVIVING_CANDIDATE | INCOMPLETE` |
| `rp` | `hmasd-research-principles-analyst` | `Principles status: DEFECTS | NO_MATERIAL_DEFECT | INCOMPLETE` |
| `rs` | `hmasd-research-scout` | `Evidence status: FOUND | CONFLICTED | NOT_FOUND | UNAVAILABLE` |
| `rc` | `hmasd-research-critic` | `Critique status: OBJECTIONS | NO_MATERIAL_OBJECTION | INCOMPLETE` |
| `pt` | `hmasd-explorer-agentify-transport` | `Pro transport state: <transport state>` |
| `im` | `hmasd-implementer` | `Implementation observation: IMPLEMENTED | PARTIAL | BLOCKED` |
| `rt` | `hmasd-routine-implementer` | `Routine implementation observation: IMPLEMENTED | PARTIAL | BLOCKED` |
| `rv` | `hmasd-reviewer` | `Review status: FINDINGS | NO_FINDINGS | INCOMPLETE` |
| `vf` | `hmasd-verifier` | `Verification observation: OBSERVED | NOT_OBSERVED | UNAVAILABLE` |
| `op` | `hmasd-experiment-operator` | `Run observation: TERMINAL | LAUNCH_FAILED | OBSERVATION_LOST` |
| `et` | `hmasd-cpm-agentify-transport` | `Engineering transport state: <transport state>` |

A leaf result is evidence for its parent. It cannot substitute for the parent's judgment or emit a
top-level `[RESULT]` field.

Leaf value meanings are local to that observation:

- `gl`: `COMPLETE` met the chore acceptance, `PARTIAL` returned a bounded usable subset, and
  `UNAVAILABLE` could not produce one. `cs`: `MAPPED` answered the frozen surface question,
  `PARTIAL` mapped only a stated subset, and `UNAVAILABLE` could not establish a trustworthy map.
- `ri`: `CANDIDATE` returns at least one surviving mechanism candidate,
  `NO_SURVIVING_CANDIDATE` returns none after the assigned search, and `INCOMPLETE` could not finish
  that judgment. `rp`: `DEFECTS` found material principle defects, `NO_MATERIAL_DEFECT` found none in
  scope, and `INCOMPLETE` could not finish. `rs`: `FOUND` found decision-relevant evidence,
  `CONFLICTED` found unresolved primary-source conflict, `NOT_FOUND` found none within the completed
  search, and `UNAVAILABLE` could not perform the search. `rc`: `OBJECTIONS` found surviving material
  objections, `NO_MATERIAL_OBJECTION` found none in scope, and `INCOMPLETE` could not finish.
- `im` and `rt`: `IMPLEMENTED` produced the assigned implementation observation, `PARTIAL` produced
  only a stated subset, and `BLOCKED` could not satisfy it. `rv`: `FINDINGS` reports at least one
  verified material defect, `NO_FINDINGS` reports none in scope, and `INCOMPLETE` lacks a premise
  required for judgment. `vf`: `OBSERVED` obtained the frozen runtime fact, `NOT_OBSERVED` did not,
  and `UNAVAILABLE` could not run the probe.
- `op`: `TERMINAL` retains the exact process through a terminal witness, `LAUNCH_FAILED` proves no
  process was launched, and `OBSERVATION_LOST` means the launched process lacks a terminal witness.
  `pt` and `et` use exactly the shared transport-state meanings above.

## Caller matrix and task configuration

| Caller | Allowed direct leaves | Work retained by the manager |
| --- | --- | --- |
| Root | `gl`, `rv` | user intent, shared-core contract, workflow repair, task conflict, cross-direction Git integration |
| Portfolio | `gl` | quality floor, lifecycle, priority, capacity, fusion/separation, dispatch and join |
| EM | `gl`, `rs`, `ri`, `rp`, `rc`, `pt` | scientific scope, evidence synthesis, claim ceiling, discriminator, Pro prompt authorship, direction authority |
| CM | `gl`, `cs`, `im`, `rt`, `rv`, `vf`, `op`, `et` | engineering contract, implementer selection, integration, validation interpretation, technical acceptance and Git closure |

Root sends bounded shared engineering to a dedicated top-level `CM/shared`; it does not borrow a
direction CM or call engineering leaves directly. EM never calls engineering leaves. CM never calls
research leaves. Portfolio never calls either specialist family. Leaves normally return only to
their spawning parent and never contact another top-level participant.

A role-local fact check is the sole depth-2 exception. A judgment leaf may spawn only the Scout or
Verifier types named by its own role method, only for one material factual premise that can change
its conclusion. The child receives a frozen factual question and returns observation, not judgment;
the fact-check child cannot delegate. If that observation conflicts with the assignment, cited
authority, owner-supplied constraint, or the judgment leaf's provisional conclusion, the leaf sends
one concise native `conflict packet` to its spawning parent: the conflicting propositions, direct
evidence, authority boundary, and what conclusion would change. It retains its assignment until the
parent replies with the converged premise. Without that reply it returns its own incomplete/partial
value, never a guessed finding. This uses native parent/child history; no receipt, conflict ledger,
router, or new shared state is created.

New top-level tasks use explicit native configuration:

| Role | Model | Thinking |
| --- | --- | --- |
| Portfolio | `gpt-5.6-sol` | `max` |
| EM | `gpt-5.6-sol` | `max` |
| CM | `gpt-5.6-sol` | `high` |
| Root | user-selected | user-selected |

Codex has no native alias field for these codes. They are only an HMASD display-name convention;
the configured native agent identifiers remain the `[agents.*]` entries in `.codex/config.toml` and
the `hmasd-*` profile names above. Direct-leaf `spawn_agent.task_name` uses
`<code>_<model>_<effort>_<task>`. The model code is
`l | t | s`; effort is `l | m | h | xh | mx | u`; task is `[a-z0-9_]+`. Codes must match the actual
selected profile. Examples: `rv_s_xh_plan`, `gl_l_xh_pdf`, `pt_l_m_pro`. This is a short display
name only and is never an identity, receipt, or route.

## Universal leaf and Effect boundaries

Every leaf receives a self-contained natural-language task model: intended outcome, why it matters,
concrete objects and relations, protected semantics, owner-known domain and runtime facts, exact
owned paths and Effects, local judgment, completion evidence, and stop condition. IDs, paths,
commits, fields, and commands are factual anchors after meaning. Use `fork_turns=1`; inherited
context is background, not the assignment.

Every leaf returns conclusion-first, followed only by its own field, direct evidence, paths, and
limitations. It does not commit, push, create a worktree, launch an unassigned Effect, or broaden
scope. A read-only specialist remains read-only. An implementer writes only its assigned paths. A
Verifier writes only its assigned proof root under `temp/`. The Experiment Operator launches one
exact command once and retains the same process observation through terminal fact.

The number of leaves follows independent information gaps, not a quota. Multiple answers from the
same model or source are search coverage, not independent scientific evidence. Weakly coupled
downloads, extraction, formatting, fixtures, and chores should go to `gl`; a specialist is selected
only for its own method.

One strict operation sends at most once, and one frozen prompt is never injected twice into the same
provider conversation. A fresh operation is permitted only after strict zero-send proof, for a
materially different owner-authored question, or for the one new-conversation replacement defined
above. Changing the WORK, leaf, label, key, tab, or task is never sufficient. This is judged from
native history and the provider conversation, not from a local workflow ledger. Tool-local stable
keys or content hashes stay inside that tool operation; they do not become HMASD identity or
durable control state.

Unsafe memory plans must be reduced, batched, or sharded. A local result command expected to exceed
7200 seconds requires one performance-reasonableness review and user approval bound to the exact
command. Scientific, numerical, RNG, checkpoint, bit-identity, and external-Effect semantics never
change silently. Tools and verification produce evidence; they do not create a new approval layer.

## Workspace and Git

`C:/Projects/HMASD` is Root's primary `main` checkout; never run `git switch` or `git checkout` in
it. Portfolio, EM, and CM are created from the saved HMASD project using Codex native
`environment: worktree`, with an exact existing branch only when a specific baseline is required.
No direction directory must be saved as a separate Desktop project, and no local worktree mapping
or registry is created.

For one direction, only one top-level participant is a Git-visible writer at a time. Exact
top-level writer transfer and handoff behavior is defined only by
`docs/project/WORKFLOW_PROTOCOL.md`; shared Git mutations remain serialized and unrelated changes
are preserved.

Direction source is under `experiments/candidates/`, tests under
`tests/experiments/candidates/`, durable science under `docs/research/candidates/<direction>/`, and
raw run artifacts under `temp/directions/<direction>/{exp,test}/`.

Shared C++ backend, neural-network base, or cross-direction core changes require prior user notice
of exact paths, goal, non-goals, and semantic effect. Use native Windows Git/Python; prefer
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Tracked paths use repository-relative POSIX
syntax and durable text follows `.gitattributes` LF policy.
