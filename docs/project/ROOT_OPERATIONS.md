# Research execution responsibilities

Root owns research planning, cross-direction comparison, selection, parent acceptance and main
integration. DM owns direction science; CM owns technical delivery. Independent Transport owns
Pro browser work. Root uses the owner's selected model/effort. Scientific authority and budgets
remain in AGENTS.md; the current owner pause applies before any research work.

## Where each rule is maintained

| Rule | Maintained source |
| --- | --- |
| Scientific tiers, delegation, capacity, source publication, Git and resource bounds | AGENTS.md §§2–7 and the evidence specification |
| Ready-work ordering, return processing and waits | [hmasd-loop-dispatch](../../.agents/skills/hmasd-loop-dispatch/SKILL.md) |
| Cross-direction scientific comparison and Portfolio intake | [hmasd-portfolio-task](../../.agents/skills/hmasd-portfolio-task/SKILL.md) |
| Native/app addressing and handoff acceptance | [SIBLING_COMMUNICATION.md](SIBLING_COMMUNICATION.md) |
| Experiment observer, collection and transfer | [EXPERIMENT_MONITOR.md](EXPERIMENT_MONITOR.md) |
| Pro packet preparation | [hmasd-pro-research-prompt-author](../../.agents/skills/hmasd-pro-research-prompt-author/SKILL.md) |
| Pro identity, Send, archive and receipt state | [hmasd-chatgpt-pro-transport](../../.agents/skills/hmasd-chatgpt-pro-transport/SKILL.md) |

Skills and agent configurations keep role-specific choices and link to these procedures.
Change the maintained source and any affected entrypoint metadata together; do not copy its
step-by-step rules into every caller.

## Complete deliverables and their owners

| Owner | Deliverable |
| --- | --- |
| Root | Select ready direction work within authority, resolve Portfolio questions, accept actual delivery, integrate accepted commits on main and keep current state coherent. |
| DM | Card and prediction, direction-local decisions, CM assignment, scientific intake and authorized continuation. |
| CM | Accepted implementation and complete technical execution batch: committed inputs, staging, bounded launch, observation, collection and technical acceptance. |
| Existing Experiment Operator, when useful | One exact launch/observation/collection batch with accepted inputs; return direct process and artifact facts to its assigning parent. CM still accepts the result. |
| Independent Transport | Execute the exact authored Pro request and return its archived facts; Root intakes Portfolio responses or forwards direction responses to DM. |

CM executes short cohesive work itself. Delegate a complete independent mechanical batch to
an existing Operator when it saves work or enables useful parallelism. Do not add a mandatory
child, standing observer or chain of per-command helpers. Root delegates accepted work before
lengthy integration and does not relay each shell step. Root may execute a short bounded operation
when delegation costs more, or take over an explicitly handed-over handle. Keep one executor
and one observer for each accepted invocation, using EXPERIMENT_MONITOR.md for transfer.

Use AGENTS.md's five-item assignment and the existing direction branch/checkout. The parent
retains acceptance; a child's completion alone does not close the direction. A technical blocker
returns to the actual assigning parent with evidence; DM/CM handles in-scope repairs, Root
resolves cross-direction dependencies. Neither a repair nor a task handover adds experiment budget.

## Exact execution inputs

CM supplies the committed command/script and exact node, source, cwd, output, handle and bound.
The assigned executor uses those bytes rather than rebuilding a similar path or retyping nested
shell text. Verify the staged cwd and all declared execution inputs, including preflight helpers,
against the accepted source; preserve frozen input digests. A disagreement returns to the same
CM for correction before submission. For Windows-to-Linux staging, preserve literal variables
and LF bytes and syntax-check the staged wrapper without executing its scientific payload.
These checks do not authorize an extra invocation or test outside its assigned budget.

Supervisor acceptance, memory admission and scientific execution are separate facts. Reconcile
uncertain acceptance using the exact handle before correction. CM collects the actual failure;
wrapper failure does not imply scientific polarity or permission to retry.

## Current records and integration

Root maintains PORTFOLIO.md as the current lifecycle/priority, latest scientific intake and
readiness view; EXPERIMENT_TRACKING.md holds accepted handles, actual observers, terminal facts
and pending continuations. Link original run/intake evidence and keep older planning snapshots
in archives. A newly completed intake updates its affected current row; old costs retain explicit
as-of scope instead of masquerading as current-regime estimates. Required owner reviews follow
hmasd-owner-item at clean boundaries.

Root owns main's index and integrates accepted commits under AGENTS §6. CM publishes its required
source/evidence in its assigned direction checkout. Coordinate actual overlapping writers, not
routine idle checks. Root records only useful execution evidence in the existing root-log and
batches ready record edits at clean boundaries. Publication must not delay independently ready
work. Recovery/cleanup follows AGENTS §6: resolve live request targets before retiring branches,
update retained checkout locations and preserve unique evidence without merging unaccepted work.

The active task and assigned native tasks drive execution and observation. OWNER_DIRECT
2026-09-08 replaces the normal completion wake path with an independent Luna/low relay
under SIBLING_COMMUNICATION.md. Only actionable Root handoffs use it; nested native work
and Transport's already waking receipts keep their routes. After the relay test succeeds,
the previous 20-minute Root heartbeat is paused. No observer or scientific budget is added.
A pause or workflow edit does not resume scientific work. Preserve accepted external identities
and the observation handover authorized by the owner.
