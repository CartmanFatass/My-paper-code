# HMASD OMP control-plane protocol

This document is the human-readable map of the active HMASD control plane. OMP
sessions, `task`, Hub, the state CLI, and Git remain the execution substrate;
this protocol defines how role-owned meanings move across that substrate. It
does not introduce a second scheduler, message bus, or authority layer.

## Authority and layered state

Authority is deliberately split rather than inferred from process status:

- The user fixes the scientific goal, the considered direction set, capacity,
  and any explicit decision boundary.
- Root is the single user-facing coordinator. Root executes the Portfolio
  subflow itself; there is no Portfolio agent or intermediate Portfolio
  session. `docs/research/portfolio/PORTFOLIO.md` records current
  cross-direction scientific judgment, while the registry records lifecycle
  and dependencies through expected-revision/CAS writes.
- `EM-<direction>` owns direction science and the material research cycle.
  `CM-<direction>` owns an accepted engineering contract, implementation,
  observation, and technical verification. Neither role performs Portfolio
  actions.
- `BrowserTransport` is one Root-mediated logical service implemented by agent
  type `hmasd-browser-transport`. Agentify remains the external-operation
  ledger; the service never becomes scientific, lifecycle, or engineering
  authority.
- OMP task and Hub state is live execution evidence. Root reconciles it with
  `.omp/runtime/agents.json`, `.omp/runtime/worktrees.json`, durable role state,
  run manifests, external-operation references, and Git. A runtime status never
  silently changes Portfolio lifecycle or role-owned conclusions.

Durable direction content is layered under
`docs/research/candidates/<direction-id>/`. Scientific authority is
`DIRECTION.md`. EM writes `<cycle-id>-scope-freeze.md`, material
`<cycle-id>-local-route-<route-id>.md`, `<cycle-id>-synthesis.md`, conditional
`<cycle-id>-terminal-gap.md`, and `<cycle-id>-handoff.md` under `evidence/`;
owner-authored `<cycle-id>-innovator-prompt.md`,
`<cycle-id>-convergence-prompt.md`, and
`<cycle-id>-convergence-disposition.md` under `external/`; and the current
durable CM request at `workflow/research/engineering-request.md`. CM writes
`<cycle-id>-contract.md`, `<cycle-id>-implementation.md`, conditional
`<cycle-id>-review.md`, `<cycle-id>-verification.md`, and
`<cycle-id>-result.md` under `workflow/engineering/`. Each reference is a
repository-relative path plus SHA-256, and each artifact is required only when
its named phase is reached. Raw runs, generated logs, concrete process handles,
tab mappings, and worktree paths remain outside durable scientific authority.

## Root Portfolio subflow

At every Portfolio decision boundary, Root states a compact decision frame:

1. the user decision and fixed considered set, including authorized capacity;
2. live investments and already-committed Effects that constrain allocation;
3. the scientific evidence boundary, exclusions, uncertainty, and claim ceiling;
4. the strongest counterfactual allocation and why the proposed allocation is
   preferable on leverage, independence, cost, reversibility, and stop rule;
5. the next observation that could change allocation, its owner, and how each
   outcome changes an action.

Root compares every direction in that fixed set and adopts exactly one explicit
action per direction: `NONE`, `ACTIVATE`, `CONTINUE`, `NARROW`, `PARK`,
`CLOSE`, `FUSE`, or `SPINOFF`. An EM recommendation is evidence for this
comparison, not an adopted Portfolio action. Transport state, CM status, run
status, task liveness, and Git state are likewise facts at their own boundaries;
they cannot be promoted into science or lifecycle decisions.

Portfolio allocation is active, not an all-terminal join. Root consumes each
terminal EM, CM, Transport, or Run fact as soon as it arrives, routes its
role-owned consequence, recomputes live advancing work, and adopts any
Portfolio action supported by current comparative evidence. When advancing
work is below authorized capacity and control is not `PAUSED`, Root screens the
strongest authorized candidates and dispatches the best admissible successor
or replacement to an exact available EM without waiting for every other leg.
Unused capacity requires an explicit comparison against the strongest candidate
and an exact reentry condition. `PAUSE` retains the current work and permits
safe observation of already-committed Effects, but blocks active refill, fresh
dispatch, provider sends, experiment launches, and every other new Effect until
`RESUME`.

The registry lifecycle has four states:

- `REGISTERED`: known and eligible, without active investment.
- `ACTIVE`: a current executable scientific question with live work or one
  exact operational reentry; it may not be silently starved.
- `PARKED`: no live direction work, with a supporting scientific or
  opportunity-cost reason, evidence boundary, and required
  `reactivation_condition_ref`; it is not `CLOSED`.
- `CLOSED`: terminal investment disposition, reopened only by an explicit new
  Portfolio action on materially new grounds.

Lifecycle/action adoption is written coherently to Portfolio authority and the
registry through `scripts/hmasd_state.py` with expected revision before new
direction work is dispatched.

## Direction cycles and durable handoffs

An EM material cycle is one bounded scientific question with
`cycle_boundary` equal to `FRESH_MATERIAL_CYCLE`, `CONTINUATION`,
`CM_RESULT_INTERPRETATION`, `EVIDENCE_INTAKE`, or
`TERMINAL_GAP_DISPOSITION`. A fresh material cycle normally includes Pro
Innovator and Pro Convergence using the required visible Pro model unless the
user waives the exact unsent operation. Evidence intake, continuation, CM-result
interpretation, and terminal-gap disposition do not manufacture a fresh cycle
or external-operation budget. EM separates facts, external evidence,
inference, and speculation, preserves the claim ceiling, and sends engineering
needs to Root as durable request references.

CM is contract-first. It accepts an exact durable engineering request, freezes
scope, non-goals, interfaces, protected semantics, acceptance, owned paths, and
an evidence-role policy before implementation. It reports the independent axes
`engineering_status`, `observation_status`, and `verification_status` using the
values defined by the CM contract. Implementer, Reviewer, Verifier, and
Experiment Operator outputs retain their evidence roles; none is permission or
scientific judgment. CM returns the resulting durable reference to Root, which
routes it back to EM when scientific interpretation is required.

## OMP communication and BrowserTransport

Every cross-role dispatch uses an OMP `task` or Hub carrier and names the common
v1 identity/generation/assignment envelope. In addition, its natural-language
body contains these meaning sections:

- **Objective and decision relevance**
- **Authorities, inputs, and evidence boundary**
- **Scope, protected non-goals, and preserved semantics**
- **Requested role work and role-owned judgment**
- **Authorized Effects and ownership**
- **Acceptance evidence and stop condition**
- **Return route, durable references, and reentry**

Results use the common v1 result envelope and role-specific payload. Literal
Codex `[WORK]`, `[RESULT]`, or `[BROWSER WORK]` headings may be historical
semantic source material, but they are not OMP routing authority, identity, or
receipts.

EM and CM never send directly to provider-specific transport agents. They
create a frozen owner-authored request reference and return it to Root. Root
validates the route, provider (`chatgpt` or `gemini`), mode (`INNOVATOR`,
`CONVERGENCE`, `DIVERGENT`, `ENGINEERING`, or `MONITOR`), exact operation
identity, authorization, and current commitment state, then serializes the work
through the singleton `BrowserTransport`. Root returns the transport fact to
its exact requester without interpreting the content. Unknown commitment never
resends, and one provider conversation, operation, tab, direction, or OMP task
must never be conflated with another.

## Liveness, Git, and recovery

Root reuses compatible logical EM/CM sessions through OMP runtime maps and Hub.
Material transitions wake reconciliation; delayed output does not create a
poller or successor. One Experiment Operator owns one exact result-bearing
command through its terminal observation.

Git handoff is layered over `omp/workflow`. EM and CM write only their
provisioned research or engineering worktrees and checkpoint one exact
assignment-owned cycle candidate. The matching direction manager applies its
verified candidate only under the Git integration contract. Root owns shared
control-plane, cross-direction, external-archive, and recovery integration.
Exact path allowlists, canonical paths, clean state, exact base, fetch/compare,
and unchanged-on-refusal semantics apply; no role stages unrelated changes or
uses `git add -A`.

Observed inconsistency routes through the OMP
`hmasd-workflow-recovery-manager`, dispatched only by Root. Recovery reconciles
existing authorities and effects; it does not invent science, resend an unknown
external operation, replay an unknown run, bypass CAS, or turn a stale runtime
observation into a lifecycle decision.
