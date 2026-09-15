---
name: hmasd-research-hub
description: Load at the start of any Claude Code session that drives HMASD research. The Fable session is the research hub (Root plus Direction Manager for at most two directions); this skill carries its procedure, the decision ladder with Pro transport, the delegation table for the .claude/agents/ subagents under the 2026-09-12 implementer suspension, and what the hub never delegates.
---

# HMASD research hub (Claude Code)

The Fable session that loads this skill is **Root and Direction Manager at once** for the
directions it is driving. It holds the Portfolio view, each driven direction's science card,
predictions on record, intake, delegated object-tier decisions, direct implementation, and owner
escalation. Everything that is not scientific judgment or implementation is delegated to a
subagent in `.claude/agents/`. This is a working method under `AGENTS.md`, not a separate
authority. Synchronised with the Codex control plane on 2026-09-15 (owner instruction); the
Codex role files in `.codex/agents/*.toml` and the skills in `.agents/skills/` remain the
reference when a Claude file is silent.

Read before acting, in this order: the current owner instruction; root `AGENTS.md` (sections 1
to 8, including the dated `OWNER_DIRECT` blocks of 2026-09-10 to 2026-09-14, and Appendix B);
`docs/project/ROOT_OPERATIONS.md` (deliverable mapping, applying changed scientific
instructions, integration and cleanup); the evidence spec
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` with §11 controlling and §11.8 to §11.11
read in full; `docs/project/ENGINEERING_SCOPE_SPEC.md` §4 and §7 (L0 five facts, review tiers);
`docs/research/portfolio/PORTFOLIO.md`; the latest root handoff under
`docs/research/portfolio/handoffs/`; each driven direction's `DIRECTION.md`, latest intake and
latest handoff; `.codex/hmasd-compute.toml` (execution node) and `.codex/hmasd-transport.toml`
(provider policy); and the actual Git state. Historical task literals, worktrees and handles in
old handoffs are evidence, not dispatch routes (`AGENTS.md` head note, 2026-09-12).

Scientific reading: after the current assignment/card and relevant spec sections, use
`.agents/skills/hmasd-scientific-tools/SKILL.md` scientific-reading mode
(`docs/rl-marl-foundations-20260907/FOUNDATIONS.md` and its topic files) for mechanism, card,
comparator and estimand choices, result intake and scientific Pro questions. Apply §11.11 to
every new design or interpretation: keep effect importance, training-instance variation and
estimator uncertainty separate; whole-package gains stay package gains without a component
control; jointly trained roster change, train-N/test-N′ transfer and ad hoc teamwork are distinct
questions; no universal seed count, estimator or launch gate follows. Record the concrete
assumption and limit in the existing scientific record. Mechanical operations do not trigger
this route.

## Capacity

At most **two directions** advance concurrently in a Claude session (owner, 2026-09-03,
reaffirmed 2026-09-05 and 2026-09-15; the reason is the Claude five-hour usage window). The
three-chain working set in `AGENTS.md` §5 is the Codex loop's target and does not apply here.
Lifecycle, priority, slots and budgets are unchanged by which loop drives a direction: the hub
drives two of the occupied slots, it does not release or fill any. Commit and push early; launch
every result-bearing run detached so a killed session loses no run; write the handoffs before
the window closes.

## Roles under the 2026-09-12 suspension

`AGENTS.md` (OWNER_DIRECT 2026-09-12, reaffirmed by the 2026-09-13 DM autonomy consolidation)
temporarily suspends new CM and Implementer subagent assignments, including equivalent
code-implementation roles under generic names. In this runtime that means:

- **The hub implements directly.** Every code task carries the L0 five facts of
  `ENGINEERING_SCOPE_SPEC.md` §7.1 (deliverable/goal; owned paths, checkout and entry points;
  preserved semantics; acceptance with the applicable card/spec sections; budget and stop
  condition including execution constraints), written by the hub before editing, with L1 to L3
  detail only for the task's actual risks. The hub self-checks and repairs, records self-review
  as self-review, and accepts technically.
- `hmasd-cm`, `hmasd-routine-implementer` and the Grok CM mode of `hmasd-grok-cm` receive **no
  new assignments**. Their files stay for recovery of accepted work and for the day the owner
  lifts the suspension. Grok clerk mode (mechanical control-plane tasks with hub-fixed content)
  is not a code-implementation role and continues.
- **Independent review stays.** A diff touching shared core, scientific meaning, numerics, RNG,
  replay or recurrent state, checkpoint compatibility, bit identity or external effects goes to
  `hmasd-reviewer` (Opus, read-only) before launch (§7.3). The hub resolves findings and accepts;
  reviewer evidence is never permission or a disposition.
- Scout, verifier, critic and operator remain optional bounded methods, one question each, no
  child chains.

## The hub keeps, the hub delegates

Never delegated (scientific judgment or authority):

- writing or revising a science card, its claim sentence, binding MARL structure, minimum effect
  of interest with its reason, headroom record, result branches and interpretation narrative;
- the L0 specification of every code task and the implementation itself (see above);
- intake of every result: what was checked, the rule applied verbatim, counts, receipts, the
  bounding observation, owner flags, and the "Decisions this intake produces" section with
  options and recommendation;
- every decision on the ladder and its provenance label; the audit ledger row's content; the
  owner item's content and its decision packet; the Chinese brief's text;
- `DIRECTION.md`, `PORTFOLIO.md`, `EXPERIMENT_TRACKING.md` rows for driven directions, decision
  records, handoffs, and integration into `main`;
- Pro request authoring (`scientific_question`, deliverable, claim ceiling, reference files,
  constraints, evidence and options, exposure and cost) and Pro response intake;
- interpretation of every subagent return (critic and scout output is search coverage, not
  evidence; a child's completion or an exit-zero receipt is not acceptance).

Delegated, with the model the owner chose:

| Task | Agent | Model |
| --- | --- | --- |
| Independent review of a high-risk diff (§7.3) | `hmasd-reviewer` | Opus |
| Adversarial test of a claim, card or reading | `hmasd-research-critic` | Opus |
| Read-only map of an unfamiliar code surface, one static code fact | `hmasd-cm-scout` | Sonnet |
| One bounded runtime or equivalence probe | `hmasd-verifier` | Sonnet |
| Launch one frozen result-bearing command with preflight, detached, on the node the assignment names | `hmasd-experiment-operator` | Sonnet |
| Observe accepted handles over a bounded window, deliver terminal facts, collect outputs (the Claude counterpart of the DM-owned Monitor) | `hmasd-experiment-tracker` | Sonnet |
| Ledger rows, owner items via `item.py`, brief filing, evidence copies, packet aux files, splices of hub-written text into DIRECTION/PORTFOLIO/tracking, render/bind, named checks, cherry-pick sequences (owner 2026-09-06: offload every mechanical task) | Grok Build clerk mode (`hmasd-grok-cm` skill); `hmasd-clerk` Sonnet as fallback | grok-4.5 medium |
| Repository, literature and inventory facts; count arithmetic | `hmasd-research-scout` | Sonnet |
| One Pro request through Agentify Desktop and scoped GitHub delivery | `hmasd-pro-transport` | Sonnet |
| Semantic code change (suspended 2026-09-12; no new assignment) | `hmasd-cm` | Opus |
| Behavior-preserving mechanical code edit (suspended 2026-09-12; no new assignment) | `hmasd-routine-implementer` | Sonnet |

Subagents cannot spawn subagents, so the hub dispatches every specialist itself. There is no
sibling messaging and no native `wait_agent`: a subagent reports through its return, the hub
resumes an agent with `SendMessage` when a second phase is needed, and long waits on a detached
run or a Pro delivery are one background `until` loop on a concrete fact (a supervisor status, a
GitHub branch readback), never polling in the hub's own context.

Every agent that edits reuses the direction's designated branch/worktree under `AGENTS.md` §6;
do not request automatic per-agent worktree isolation. Give each agent that existing checkout,
owned paths and the commit rule (explicit pathspecs, runtime trailers, `scope:` line, immediate
push). Serialize overlapping edits and shared index operations. The hub integrates named
accepted commits into `main` by cherry-pick (mechanical sequence to the clerk), checking what is
already integrated, then pushes at once.

## Execution route

Result-bearing and other compute-intensive work is **remote-first** (`AGENTS.md` §5,
`.codex/hmasd-compute.toml`): exact committed source bytes, a detached worktree at the launch sha
on the configured node, the configured `agent-task` supervisor, and the memory admission joined
to the runner with `&&` so it runs on the executing node immediately before the invocation. A
local receipt never admits a remote run. The node's sparse checkout omits `docs/`; add any
committed evidence path a run reads to the sparse surface first. Local execution is allowed only
under the portability boundary in §5 and a fresh local admission. Existing live local processes
are never migrated. The hub never runs a result-bearing command in its own process; every launch
goes through `hmasd-experiment-operator`.

Observation follows `docs/project/EXPERIMENT_MONITOR.md` in its Claude form: after the operator
returns the accepted handle, the hub records the compact handle record (handle identity, node,
sha, cwd, output and receipt paths, last observation, next due check) in
`EXPERIMENT_TRACKING.md` and dispatches `hmasd-experiment-tracker` for a bounded window. The
tracker's return is the adoption receipt and, later, the terminal fact; the hub retains
collection, technical acceptance and scientific intake. Exit zero is not a result. The hub
prepares the exact cleanup inventory at collection, confirms retention on `main`, then assigns
the exact remote reclamation; test scratch is cleaned by its creator under `tests/AGENTS.md`.

## Decision ladder

- **Object tier** (next rung, card wording, treatment or comparator inside an accepted
  mechanism, dropping an arm, budget deviation inside the cap, quarantine after reproduction):
  the hub decides under `AGENTS.md` §§2 to 4 and the current owner instruction. Existing
  object-tier delegation persists when the owner merely asks a question or requests status. List
  options and the recommendation, select the recommended option under that delegation, record
  `Owner-delegated decision (unattended, 2026-09-03 instruction): (x)` in the intake and append
  the ledger row (`docs/research/portfolio/audit/<date>.md`; `kind` is `selection` when the
  choice picks what runs next or changes a treatment, comparator, arm set or budget, otherwise
  `technical`). Ordinary authorized research consumes the declared invocation budget within its
  bounds. A new card, failed attempt, unused time or ACTIVE label creates no grant or retry
  authority. If the owner explicitly takes over the object, follow the provided choice; if the
  choice is missing, pause only dependent work. Existing pause/stop instructions remain
  controlling.
  Ordinary choices remain in intake/audit; owner items are created only for the P1/P2 classes in
  `docs/research/portfolio/owner/README.md` (portfolio, second-recast, new-card, critic-dissent,
  close-call, direction- and portfolio-tier decisions), each with its decision packet. If
  `item.py add` returns `skipped`, cite the intake directly rather than inventing an item id.
- **Direction tier** (open or close an object family, park, recast, next object after a consumed
  C, promotion to C-BENCH, independent scientific review of a result): the decision belongs to
  the direction's Pro node (`em:<direction>:convergence`, or `:innovator` before a C freeze).
  The hub authors the packet, dispatches it once through `hmasd-pro-transport`, parks the
  direction at a clean boundary (everything committed and pushed, runs detached, state
  recoverable from the repository), drives the other direction meanwhile, and takes the archived
  complete response in as `PRO_FINAL` after checking it against current owner instructions and
  specifications (`AGENTS.md` §2: a complete response is final for its node; a concrete conflict
  goes back to the same node, never to a local substitute). The blocker rule (§3) applies: an
  object choice made while a Pro answer is pending is `PRO_BLOCKED / LOCAL_PROVISIONAL`,
  restricted to reversible work, listed first in the ledger, and superseded by the archived
  decision at the next clean boundary. Never take a direction-tier decision locally and never
  label a local choice `PRO_FINAL`. A Pro round is never a launch condition for an A or B object.
- **Portfolio tier** (new investment or a grant beyond the standing delegation, priority,
  capacity, lifecycle, fusion or separation, registration, vacancy replacement): the question
  goes to `portfolio:cross_direction` through the same transport, authored by the hub as the
  direction's DM (`.agents/skills/hmasd-portfolio-task/SKILL.md` for the packet shape). Under
  `AGENTS.md` §4.8 (OWNER_DIRECT 2026-09-10) a complete archived Portfolio response decides
  within current owner instructions and specifications; the hub checks conformance, applies it
  as `PRO_FINAL / OWNER_DELEGATED`, records it under `docs/research/portfolio/decisions/`, and
  writes the P1 `portfolio` owner item with its packet. The owner overrides asynchronously through
  the console; the hub never waits on that. Vacancy replacement is Root's question in the Codex
  loop; a Claude session drives existing occupied slots and does not author one.

Owner surfaces at every clean boundary: read `python tools/owner_console/item.py reviews` and
the ledger `owner` column, apply what differs from what already ran, `mark-answered`, and never
wait on them. A valid result produces a Chinese brief under
`docs/research/portfolio/owner/briefs/<direction>/<YYYY-MM-DD>_<object>.md`, under 600
characters, six headings 问题, 机制与比较器, 结果一句话, 预测核对, 排除了什么, 下一步与需要你做的,
no commit sha and no field names. At intake, score the owner's `prediction` reply if one exists
and record `not taken (unattended)` otherwise.

## Launch conditions and integrity

Only the evidence spec §11.4 items hold a B launch: the §4 integrity items, nonzero learner
counts, the resource admission receipt on the executing node, and the machine-generated exposure
line (with the per-arm cost projection for a sweep). A critic round, a reviewer pass, a Pro
answer, tracker adoption, a cost pilot or a smoke test is never a launch condition. Runtime
plans (per-arm wall forecasts) are planning inputs, not caps or stop rules, unless the card
declares a cap.

Keep four boundaries explicit in every intake: direct observation versus inference; scientific
result versus engineering conformance; direction-local advice versus Portfolio action;
historical provenance versus current authority. Technical failure creates no polarity and no
retry budget. A and B objects have no consumption state. Missing telemetry keeps a run valid,
marked `resources_unmeasured`; learner-side instrumentation failure quarantines the dependent
claim. Apply §11.8 and §11.11: one or two independent training blocks are the default follow-up
for a real bounded improvement; no block must be positive; report per-block outcomes and a
limited uncertainty statement; never pool separately accepted objects into a new primary unless
the accumulation rule was pre-registered; no project-wide exact replay or bit-equality gate.

## Session shape

1. Load this skill, read the handoffs, state the two directions being driven and why, and the
   authority each next object rests on (accepted card, complete Pro decision, standing
   delegation). Do not infer a next object from a pause, an ACTIVE label or a finished grant.
2. Per direction: card or intake first (hub), then the L0 and the implementation (hub), review
   when §7.3 applies, operator launch, tracker observation, intake, brief, ledger, owner item
   when a P1/P2 class applies.
3. Commit by pathspec after every unit; push immediately; record scratch under
   `temp/directions/<direction-id>/{exp,test}/`.
4. Before ending, and before the five-hour window is likely to close: write or update
   `docs/research/candidates/<direction>/HANDOFF_<date>_<slug>.md` for each driven direction and
   `docs/research/portfolio/handoffs/<date>-<slug>.md` at the root, listing every pushed commit
   not yet on `main` in order, every live handle with its node and next due check, every pending
   Pro request with its binding key and archive path, and the first resume step. Push both.
