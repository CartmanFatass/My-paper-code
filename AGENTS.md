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

Transport states are shared facts for both Pro and engineering transport:

- `PENDING`: no send-capable call occurred.
- `ZERO_SEND_FAILED`: the provider definitely received no request and no operation was created.
- `COMMITMENT_UNKNOWN`: whether the provider received the request cannot be proved.
- `SENT_WAITING`: the exact request was sent and natural generation is still in progress.
- `COMPLETE`: the provider-visible request matches the frozen prompt and the naturally completed
  full response is archived.
- `SENT_INPUT_MISMATCH`: a send is confirmed but the provider-visible request differs from the
  frozen prompt.
- `SENT_UNREADABLE`: a send is confirmed but the full response cannot yet be archived.
- `WAIVED`: the user waived that exact operation before any send-capable call.

Any unknown or sent state is observe-only and never resends. A mismatch is terminal for that
operation and supplies no scientific, engineering, Portfolio, or lifecycle conclusion. When a Pro
stage is required for EM acceptance, mismatch makes the current EM `[WORK]` `FAILED`, never
`CANCELLED`; EM still returns every EM field using its actually reached scientific state and
`Recommendation: NONE`. Engineering transport mismatch fails the CM assignment only when that
consultation was required for its acceptance. Transport failure cannot imply `PARK`, `CLOSE`, or any
other Portfolio action.

Leaf observations are also separate namespaces:

| Alias | Custom subagent | Own final field |
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

## Caller matrix and task configuration

| Caller | Allowed direct leaves | Work retained by the manager |
| --- | --- | --- |
| Root | `gl`, `rv` | user intent, shared-core contract, workflow repair, task conflict, cross-direction Git integration |
| Portfolio | `gl` | quality floor, lifecycle, priority, capacity, fusion/separation, dispatch and join |
| EM | `gl`, `rs`, `ri`, `rp`, `rc`, `pt` | scientific scope, evidence synthesis, claim ceiling, discriminator, Pro prompt authorship, direction authority |
| CM | `gl`, `cs`, `im`, `rt`, `rv`, `vf`, `op`, `et` | engineering contract, implementer selection, integration, validation interpretation, technical acceptance and Git closure |

Root sends bounded shared engineering to a dedicated top-level `CM/shared`; it does not borrow a
direction CM or call engineering leaves directly. EM never calls engineering leaves. CM never calls
research leaves. Portfolio never calls either specialist family. Leaves return only to their
spawning parent, never delegate, and never contact another participant.

New top-level tasks use explicit native configuration:

| Role | Model | Thinking |
| --- | --- | --- |
| Portfolio | `gpt-5.6-sol` | `max` |
| EM | `gpt-5.6-sol` | `max` |
| CM | `gpt-5.6-sol` | `high` |
| Root | user-selected | user-selected |

Direct-leaf `spawn_agent.task_name` uses `<alias>_<model>_<effort>_<task>`. The model code is
`l | t | s`; effort is `l | m | h | xh | mx | u`; task is `[a-z0-9_]+`. Codes must match the actual
selected profile. Examples: `rv_s_xh_plan`, `gl_l_xh_pdf`, `pt_l_m_pro`. This is a short display
name only and is never an identity, receipt, or route.

## Universal leaf and Effect boundaries

Every leaf receives a self-contained natural-language task model: intended outcome, why it matters,
concrete objects and relations, protected semantics, exact owned paths and Effects, local judgment,
completion evidence, and stop condition. IDs, paths, commits, fields, and commands are factual
anchors after meaning. Use `fork_turns=1`; inherited context is background, not the assignment.

Every leaf returns conclusion-first, followed only by its own field, direct evidence, paths, and
limitations. It does not commit, push, create a worktree, launch an unassigned Effect, or broaden
scope. A read-only specialist remains read-only. An implementer writes only its assigned paths. A
Verifier writes only its assigned proof root under `temp/`. The Experiment Operator launches one
exact command once and retains the same process observation through terminal fact.

The number of leaves follows independent information gaps, not a quota. Multiple answers from the
same model or source are search coverage, not independent scientific evidence. Weakly coupled
downloads, extraction, formatting, fixtures, and chores should go to `gl`; a specialist is selected
only for its own method.

One owner-frozen request to one provider sends at most once. Once commitment is unknown or a send is
confirmed, changing the WORK, leaf, label, key, conversation, or task does not make the same request
a fresh Effect; only same-operation non-sending observation is allowed. A new send requires either
strict proof that the provider received nothing or a materially different owner-authored question.
This is judged from native history and the prompt itself, not from a local ledger. Tool-local stable
keys or content hashes required by the strict transport implementation stay inside that tool
operation; they do not become HMASD workflow identity or durable control state.

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

For one direction, only one top-level participant is a Git-visible writer at a time. Before EM hands
Git-visible work to CM it commits its owned paths and becomes read-only. The CM branch fast-forwards
to that exact commit, changes and commits only its owned paths, then returns the known commit/diff.
EM fast-forwards to the exact CM commit before writer ownership returns. A non-fast-forward stops
the current participant and is reported to its requester; no cherry-pick, rebase, or history rewrite
is used. Shared Git mutations are serialized and unrelated changes are preserved.

Direction source is under `experiments/candidates/`, tests under
`tests/experiments/candidates/`, durable science under `docs/research/candidates/<direction>/`, and
raw run artifacts under `temp/directions/<direction>/{exp,test}/`. A Git-visible top-level handoff
must commit the referenced changes. A same-repository native-worktree handoff does not require push;
push is required only for user-requested remote sync, cross-host delivery, or formal delivery.

Shared C++ backend, neural-network base, or cross-direction core changes require prior user notice
of exact paths, goal, non-goals, and semantic effect. Use native Windows Git/Python; prefer
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Tracked paths use repository-relative POSIX
syntax and durable text follows `.gitattributes` LF policy.
