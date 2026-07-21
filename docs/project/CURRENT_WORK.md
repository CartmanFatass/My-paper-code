# HA-CTSE Current Work

Updated: 2026-07-21

## Controller Ownership

- Active controller: Codex root task `019f5c78-0c91-7612-adb4-c1fcfe4484c8`
- Controller status: ACTIVE
- Workspace: `C:\project\HMASD`
- Branch: `aggressive`
- Handoff state: NONE
- Codex role: project state, accepted scientific boundary, implementation and
  experiment authorization, evidence, Git, and user communication
- Scientific convergence source: registered Research Project Manager using
  tracked Open-Pro divergent evidence and project principles
- Code implementation source: Research Project Manager-managed temporary
  `$hmasd-implementer` and `$hmasd-reviewer` subagents; there is no persistent
  code-manager session

## Current Boundary

The independent `NONCALENDAR_HETEROGENEOUS_TRACKING_G0` benchmark qualification
is valid `NO_ACCESS_BENCHMARK_ORDINARY_CONTROL`. H establishes structural
reachability, C the current-demand/error information null, S the cost of one
shared four-step renewal restriction, and D partial causal learning without
ordinary access. It does not establish hierarchy, learned skills or learned
heterogeneous lifetime.

The prior external clarification selected
`D0_D1_CAUSAL_OBSERVATION_REFACTOR_G0`, but the controller retracted that route
before implementation or compute. It inverted the research objective by making
ordinary-controller access a prerequisite for developing the hierarchy,
skills and variable-lifetime mechanisms whose purpose is to build a stronger
MARL algorithm. That raw remains historical reviewer evidence; its route is not
active authority.

The Research Project Manager has now converged the unresolved proposal into
controller-adopted `EVENT_HELD_COMMITMENT_LINK_G0`. It isolates one treatment:
whether an event-held commitment reaches primitive action logits. Ordinary
recurrent `OR` is the full-algorithm comparator; `DUM` and `EHC` have identical
commitment state, capacity, event learning and optimizer exposure, while only
`EHC` enables the commitment-to-action link. The execution, probability,
replay, lifecycle, checkpoint, experiment and mutually exclusive result
contracts are frozen in the durable design. No formal experiment is authorized
until implementation and focused review complete.

## Implementation State

`EVENT_HELD_COMMITMENT_LINK_G0` is implemented and committed at `ce0d0ec`
("implement event-held commitment link G0 arms"), replacing the superseded
noncalendar H/C/S/D executable benchmark. Focused evidence was reproduced on
CUDA before the commit:

- 7/7 focused tests pass in 60s;
- `or_dum_no_op` true under matched weights, observations, orders and uniforms;
- added parameters 1608 per arm, base optimizer 15004, event optimizer 1584;
- DUM base zero-gradients `[1,1,1,1]` against EHC `[0,0,0,0]` at equal event
  steps, so `W_z` Adam exposure matches while its primitive effect stays zero;
- maximum replay error 4.77e-7 against the 1e-6 tolerance;
- checkpoint continuation exact on discrete, lifecycle and RNG state with all
  continuous, model and optimizer errors 0.0.

No formal training or registered evaluation has been launched.

## Next Action

External review of the committed diff is performed by the user's GPT 5.6 pro
reviewer against the frozen plan in `IMPLEMENTATION_PLAN.md`. Formal training
remains a separate later authorization.

## Measured Compute Cost

Registered `16 x 80` four-epoch update on the local RTX 4070: 8.61s for `OR`,
8.14s for `DUM`, 8.18s for `EHC`. Serial formal training over 250 updates,
three arms and five replicates is 8.65h, and the four evaluation cells add
roughly 1 to 1.5h, for about 10h continuous.

Throughput is Python-loop and kernel-launch bound rather than compute bound at
roughly 160 transitions/s for a 15k-parameter model, so the GPU stays nearly
idle. The 15 `(arm, replicate)` cells are independent and can be executed
concurrently before any formal launch is authorized.

## Local Execution Environment

Focused tests and the smoke fail closed without CUDA by design. The default
interpreter carries a CPU-only `torch 2.8.0+cpu`; use
`C:/Users/wu/.conda/envs/SB3/python.exe` (`torch 2.7.0+cu118`) directly.
`conda run -n SB3` raises `UnicodeDecodeError` from a non-UTF-8 `.pth` during
`site.py` and must not be used.

## Autonomous Boundary

- Status: IMPLEMENTATION_SOURCE_ADOPTED
- Authorized evidence-bearing iterations: five additional iterations from this
  corrected boundary
- Remaining iterations: five
- Permitted automatic action: for each iteration, obtain Open-Pro divergence,
  converge internally, adopt, implement, review, run, analyze and record one
  terminal disposition, then decrement the remaining count
- Stop condition: five terminal dispositions are accepted, committed and
  pushed; the Research Project Manager selects `STOP`; or a genuine
  contract/operational blocker requires user authority
- Forbidden: more than five iterations, concurrent mutating research routes,
  locally invented successor routes, or expansion beyond each accepted
  scientific boundary

## Durable Constraints

- Target capability: one shared algorithm with runtime-variable team membership
  and variable individual skill lifetime.
- Preserve the ordinary recurrent direct learner as the access null.
- Intrinsic reward remains environment-agnostic: no task field, identity, role,
  success predicate, progress measure, or external reward may enter it.
- R41B is the positive fixed-`N` source anchor. Retired mechanisms and old
  carriers are evidence, not executable dependencies.
- Do not rescue a valid failure by changing budget, seed, threshold, reward,
  model, task, skill count, or carrier under the same claim.
- Active-line development applies; no backward-compatibility or legacy path is
  required.

## Pointers

- `docs/project/ALGORITHM_PRINCIPLES.md` — durable scientific constraints.
- `.agents/skills/hmasd-project-manager/references/convergence-principles.md` —
  internal scientific-convergence guidance.
- `.agents/skills/hmasd-project-manager/references/engineering-principles.md` —
  implementation-management engineering constraints.
- `.agents/skills/hmasd-implementer/references/engineering-principles.md` and
  `.agents/skills/hmasd-reviewer/references/review-principles.md` — temporary
  subagent contracts.
- `docs/project/IMPLEMENTATION_PLAN.md` — Research Project Manager-owned current
  executable design or explicit `NONE`.
- `docs/project/ExpRecord.md` — formal experiment history and dispositions.
- `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md` — current adopted
  scientific and executable source.
- `docs/external-review/rounds/20260719_clean_process_access_portfolio/`
  — completed review evidence and accepted `50_DISPOSITION.md`.
- `docs/external-review/rounds/20260720_noncalendar_g0_no_access_portfolio/`
  — completed G0 no-access portfolio and accepted evidence boundary.
- `docs/external-review/rounds/20260720_noncalendar_g0_direct_access_clarification/`
  — immutable clarification raw plus retracted objective-inverting disposition.
- `docs/external-review/rounds/20260720_event_held_commitment_replay_statistical_finalization/`
  — final focused raw and controller non-adoption record; no code or experiment
  handoff.
