# HA-CTSE Current Work

Updated: 2026-07-21

## Ownership

- Workspace: `C:\project\HMASD`
- Branch: `aggressive`
- Scientific authority: the user. Route selection, adoption, threshold changes
  and experiment authorization are theirs.
- Implementation and documentation: Claude Code session. It owns code
  correctness, focused evidence, Git integration and the maintenance of
  `docs/project/`.
- External review: the user's GPT-5.6 Pro, dispatched by the user directly.
- The Codex role graph in `AGENTS.md` and `.agents/skills/` is retained as
  historical workflow. It is not the operating contract for this session and is
  not modified here.

## Execution Flow

Work is executed through bounded subagents under a single orchestrator.

- Orchestrator: writes the frozen plan, dispatches, integrates the result,
  reruns the focused suite itself, commits and maintains `docs/project/`. A
  subagent's own claim that tests pass is never accepted as evidence.
- Implementer: one bounded task against a frozen plan, receiving the plan, the
  exact file scope, the acceptance criteria and the execution-environment
  facts. It receives no research context and holds no Git authority.
- Reviewer: a separate read-only spawn with fresh context that audits the diff
  against the plan and returns findings without editing. A review pass is
  mandatory before committing any change touching protected semantics, meaning
  probability factorization, gradients and detach boundaries, RNG stream
  ownership, replay, lifecycle clocks, credit assignment, masks and checkpoint
  meaning.
- Mechanical work such as inventories, search sweeps, log scraping and
  packaging is delegated to a low-cost tier and never touches algorithm
  semantics.

One writer holds a given file set at a time. Concurrent mutating tasks on the
same scope are not dispatched.

Handoff note: the prior Codex controller task
`019f5c78-0c91-7612-adb4-c1fcfe4484c8` left the
`EVENT_HELD_COMMITMENT_LINK_G0` implementation complete but uncommitted. It was
verified and committed under the ownership above.

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

External implementation review is dispatched by the user to GPT-5.6 Pro. The
package is
`docs/external-review/gpt5_6_pro/20260721_event_held_commitment_link_g0_code_review/`,
pinned to implementation commit `ce0d0ec` and pushed at `38da9ae`. It follows
the older flat convention rather than a `rounds/` divergent round, because the
`rounds/` contract cites `OPEN_REVIEW_PRINCIPLES.md` and produces scientific
divergence rather than an implementation audit. It requests one verdict of
`APPROVE`, `MODIFY` or `REJECT` against the frozen plan.

The returned reply is archived verbatim as `RESPONSE_RAW.md` in that directory
and the accepted outcome as `DISPOSITION.md`. Formal training remains a
separate later authorization and is blocked until the verdict is resolved.

## Open Contract Questions

One unresolved question stands against the result contract, raised before any
result was observed and therefore not a post-hoc threshold rescue. It is
recorded here because `ALGORITHM_PRINCIPLES.md` is reserved for generalized
rules and this is specific to the active source.

`ALGORITHM_PRINCIPLES.md` 2.3 requires that a long-lived skill arise from
learned behavior under the declared clock contract. The lifetime gate
`LCB(CV(T))>0.25` appears to be satisfied by construction. `Delta` is sampled
uniformly from `{4,8,12}` and the policy selects only `KEEP`/`RENEW`, so a
segment lifetime is a Geometric-count sum of `Delta` draws with
`Var(Delta)/E[Delta]^2 = (32/3)/64`. That yields `CV(T)=0.408` under always-
`RENEW` and `0.764` under a balanced policy, so every policy including an
untrained one clears `0.25`. The lifetime-bin condition appears similarly
satisfiable.

Two related observations. The natural-use gates are non-degeneracy checks,
since the support is binary and `P_KEEP+P_RENEW=1`, so a uniform random event
head clears both; principle 2.2 holds that usage statistics are not evidence of
a useful skill. The intervention gate measures logit-perturbation magnitude
rather than behavioral consequence, so a large `W_z` applied to an
uninformative `z` clears it.

The primary estimand `G` is unaffected and remains mechanism-matched. The
question is whether the behavioral battery discriminates the
`COMMITMENT_SUPPORTED` and `REPRESENTATION_ONLY` branches at all. One candidate
replacement conditions on the `KEEP`-chain length, which is purely
policy-determined, instead of realized lifetime, which is dominated by the
`Delta` draw. This is referred to the user and GPT-5.6 Pro; no threshold is
changed here.

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

INACTIVE. The inherited grant authorized five evidence-bearing iterations
driven by the Codex loop of Open-Pro divergence, internal convergence,
adoption, implementation, review, run, analysis and terminal disposition. That
loop is not operating, so the iteration budget is not being consumed and is
retained only as the user's standing intent.

Under current ownership each mutating step is authorized by the user directly.
Nothing runs formal training, changes a registered threshold, selects a
successor route or creates a terminal disposition without that explicit
authorization. The prohibitions on concurrent mutating research routes and on
locally invented successor routes still hold.

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
- `docs/project/IMPLEMENTATION_PLAN.md` — current frozen executable design, or
  explicit `NONE` when no implementation is authorized.
- `docs/project/ExpRecord.md` — formal experiment history and dispositions. It
  carries no `EVENT_HELD_COMMITMENT_LINK_G0` row, correctly, because no formal
  experiment has been authorized or run.
- `docs/external-review/gpt5_6_pro/20260721_event_held_commitment_link_g0_code_review/`
  — active implementation review package awaiting `RESPONSE_RAW.md`.
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
