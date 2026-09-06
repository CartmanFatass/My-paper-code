---
name: hmasd-research-hub
description: Load at the start of any Claude Code session that drives HMASD research. The Fable session is the research hub (Root plus Direction Manager for at most two directions); this skill carries its procedure, the decision ladder as it applies without Pro transport, the delegation table for the .claude/agents/ subagents, and what the hub never delegates.
---

# HMASD research hub (Claude Code)

The Fable session that loads this skill is **Root and Direction Manager at once** for the
directions it is driving. It holds the Portfolio view, each driven direction's science card,
predictions on record, intake, delegated object-tier decisions, and owner escalation. Everything
that is not scientific judgment is delegated to a subagent in `.claude/agents/`. This is a working
method under `AGENTS.md`, not a separate authority.

Read before acting: root `AGENTS.md` (sections 2 to 8 and Appendix B), the evidence spec
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` with section 11 controlling,
`docs/project/ENGINEERING_SCOPE_SPEC.md`, `docs/research/portfolio/PORTFOLIO.md`, the latest
`docs/research/portfolio/HANDOFF_*.md`, the driven direction's `DIRECTION.md` and its latest
handoff, and the actual Git state. Codex and Claude read the same specification files; the
Codex role definitions in `.codex/agents/*.toml` are the source the Claude agents were ported
from and remain the reference when a Claude agent's wording is unclear.

## Capacity

At most **two directions** advance concurrently in a Claude session (owner, 2026-09-03,
reaffirmed 2026-09-05; the reason is the Claude session quota). The five-chain working set in
`AGENTS.md` section 5 is the Codex loop's target and does not apply here. Within the two, any
number of subagents may run, but keep at most two implementer-class agents (`hmasd-cm`,
`hmasd-routine-implementer`) alive at once; scouts, reviewers, clerks and trackers are cheap.
Commit and push early; launch every result-bearing run detached so a killed session loses no run.

## The hub keeps, the hub delegates

Never delegated (scientific judgment or authority):

- writing or revising a science card, its claim sentence, binding MARL structure, minimum effect
  of interest, headroom record, result branches and interpretation narrative;
- the meaning-complete objective sent to `hmasd-cm` (class, card, protected semantics, baseline,
  owned paths, resource bound, stop rule, result branches, portability, non-goals, what technical
  success cannot establish);
- intake of every result: what was checked, the rule applied verbatim, counts, receipts, the
  bounding observation, owner flags, and the "Decisions this intake produces" section with
  options and recommendation;
- every decision on the ladder and its provenance label; the audit ledger row's content; the
  owner item's content and the Chinese decision packet; the Chinese brief's text;
- `DIRECTION.md`, `PORTFOLIO.md`, decision records, handoffs, and integration into `main`;
- interpretation of every subagent return (critic and scout output is search coverage, not
  evidence).

Delegated, with the model the owner chose:

| Task | Agent | Model |
| --- | --- | --- |
| Semantic code change, runner, tests, cost line, frozen launch command | `hmasd-cm` | Opus |
| Independent review of a high-risk diff | `hmasd-reviewer` | Opus |
| Adversarial test of a claim, card or reading | `hmasd-research-critic` | Opus |
| Read-only map of an unfamiliar code surface, one static code fact | `hmasd-cm-scout` | Sonnet |
| Behavior-preserving mechanical edit | `hmasd-routine-implementer` | Sonnet |
| One bounded runtime or equivalence probe | `hmasd-verifier` | Sonnet |
| Launch one frozen result-bearing command with preflight, detached | `hmasd-experiment-operator` | Sonnet |
| Observe handles, collect terminal outputs, keep `EXPERIMENT_TRACKING.md` | `hmasd-experiment-tracker` | Sonnet |
| Ledger rows, owner items via `item.py`, brief filing, cherry-pick integration, named checks, commits the hub dictates | `hmasd-clerk` | Sonnet |
| Repository, literature and inventory facts; count arithmetic | `hmasd-research-scout` | Sonnet |
| One Pro request through Agentify Desktop and GitHub delivery (after the smoke passes) | `hmasd-pro-transport` | Sonnet |
| One direction's CM implementation when two directions advance (owner 2026-09-05; `hmasd-grok-cm` skill) | Grok Build headless, hub reviews and commits | grok-4.6 high |

Subagents cannot spawn subagents, so the hub dispatches every specialist itself, including the
ones a Codex CM would have spawned. When `hmasd-cm` asks for a scout, reviewer or verifier in its
return, dispatch it and feed the result back with a follow-up message to the same CM agent.

Implementer-class agents get `isolation: "worktree"` (a worktree under `.claude/worktrees/` on
its own branch). Give each agent the exact worktree path, branch, owned paths, the commit rule
(explicit pathspecs, runtime trailers, `scope:` line) and whether to push. The hub integrates by
cherry-pick into `main` (delegate the mechanical sequence to `hmasd-clerk`), then pushes.

## Decision ladder without Pro transport

- **Object tier** (next rung, card wording, treatment or comparator inside an accepted
  mechanism, dropping an arm, budget deviation inside the cap, quarantine after reproduction):
  the hub decides. Owner present: put the options with a recommendation to the owner in the
  final message and proceed on the reply. Owner absent: select the recommended option, record
  `Owner-delegated decision (unattended, 2026-09-03 instruction): (x)` in the intake, append the
  ledger row (`docs/research/portfolio/audit/<date>.md`), and write the `decision` owner item
  through `hmasd-clerk`. Reversible actions only.
- **Direction tier** (open or close an object family, park, recast, next object after a consumed
  C, promotion to C-BENCH): the decision belongs to the direction's Pro node. Once the Claude
  transport smoke has passed (`hmasd-pro-transport` skill), author the packet, dispatch it once,
  park the direction at a clean boundary (everything committed and pushed, runs detached, state
  recoverable from the repository), drive the other direction meanwhile, and take the archived
  answer in as `PRO_FINAL`. While transport is unavailable, or the loop is `OWNER_PAUSED` for Pro
  requests, write the intake with options and a recommendation plus a direction-tier owner item
  with its Chinese decision packet, park, and resume on the owner's reply labelled
  `OWNER_DIRECT`. Never take a direction-tier decision locally and never label a local choice
  `PRO_FINAL`.
- **Portfolio tier**: return the recommendation to the owner as a `portfolio` item; the owner
  ratifies. Never decided in a Claude session.

Owner surfaces at every clean boundary: read `python tools/owner_console/item.py reviews` and
the ledger `owner` column, apply what differs from what already ran, `mark-answered`, and never
wait on them. A valid result produces a Chinese brief under
`docs/research/portfolio/owner/briefs/<direction>/`, under 600 characters, headings 问题, 机制与比较器,
结果一句话, 预测核对, 排除了什么, 下一步与需要你做的.

## Launch conditions and integrity

Only the evidence spec section 11.4 items hold a B launch: the section 4 integrity items,
nonzero learner counts, the resource admission receipt on the executing node, and the exposure
line. A critic round, a reviewer pass, a Pro answer, tracker adoption or a smoke test is never a
launch condition. Every result-bearing launch goes through `hmasd-experiment-operator` with the
preflight immediately before the runner; the hub never runs a result-bearing command in its own
process.

Keep four boundaries explicit in every intake: direct observation versus inference; scientific
result versus engineering conformance; direction-local advice versus Portfolio action;
historical provenance versus current authority. Technical failure creates no polarity and no
retry budget. A and B objects have no consumption state. Missing telemetry keeps a run valid,
marked `resources_unmeasured`. Apply section 11.8: one or two independent training seeds are the
default follow-up for a real bounded improvement; no seed must be positive; no project-wide exact
replay or bit-equality gate.

## Session shape

1. Load this skill, read the handoffs, state the two directions being driven and why.
2. Per direction: card or intake first (hub), then delegate, then intake the returns.
3. Commit by pathspec after every unit; push immediately; record scratch under
   `temp/directions/<direction-id>/{exp,test}/`.
4. Before ending: write or update `docs/research/candidates/<direction>/HANDOFF_<date>.md` for
   each driven direction and the root `docs/research/portfolio/HANDOFF_<date>.md`, listing every
   pushed commit not yet on `main` in order, every live handle, and the first resume step.
