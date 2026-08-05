# Claude Orchestrator Workflow (HMASD full takeover)

```text
document_kind=claude_orchestrator_workflow
assignment=CLAUDE_HMASD_FULL_TAKEOVER_20260805
authority_note=adds_no_authority_over_AGENTS.md; AGENTS.md remains the sole project authority/routing contract
scope=claude_native_workflow_for_lanes_subagents_models_transport; not a copy of the Codex session workflow
```

The Codex workflow is session-topology-based (persistent role sessions,
cross-session messages). Claude Code works differently: one persistent
orchestrator session, stateless one-shot subagents, native browser tools,
file artifacts. This document fixes the **logical mapping** — the Codex
workflow's invariants are preserved; its session mechanics are not imitated.

## Logical mapping (Codex concept → Claude mechanism)

| Codex workflow concept | Claude-native mechanism | Preserved invariant |
|---|---|---|
| Persistent Explorer session | Explorer lane of the orchestrator session | Science decisions have one accountable owner; longitudinal state lives in `local_research/RESEARCH_CONTINUITY.md` |
| Persistent Code Manager session | CM lane of the orchestrator session | Implementation/acceptance separated from science freezing; every artifact states its lane |
| `send_message_to_thread` between sessions | File artifacts (`temp/handoffs/`, `local_research/`) read across lane phases | Auditable handoff content; no informal semantic relay |
| Registered native child (`.codex/agents/*.toml` + role charter) | Self-contained `.claude/agents/*.md` subagent (stateless, single-shot, full contract inline) | Exact-assignment-only; fail closed on missing identity/path/authority/completion |
| Same-session self-review before acceptance | `hmasd-reviewer` subagent in a clean context | Review independence (stronger: reviewer never saw implementation reasoning) |
| Agentify Transport Operator session | Orchestrator drives the browser directly (claude-in-chrome) | Verbatim raw-response archive, byte-compared; transport facts + conversation URLs recorded; transport errors are never scientific results |
| External Pro review boundary | Unchanged — GitHub connector on exact pushed commits, fresh clean conversation per audit | Pro is never simulated; final scientific acceptance is Pro's alone |

Subagents do NOT load `.agents/roles/*.md` or `.codex/` files — those are
Codex session charters. Each `.claude/agents/*.md` profile carries its own
complete contract (outcome/observation/action/judgment/recovery/completion)
consistent with AGENTS.md authority boundaries.

## Lanes

- **Explorer lane** (orchestrator): scientific propositions, dispositions,
  frozen treatment/revision briefs, experiment contracts, External Pro
  question authoring, verbatim archive and scientific intake, portfolio and
  continuity (`local_research/RESEARCH_CONTINUITY.md`, five fields).
- **Code Manager lane** (orchestrator): implementation, focused tests, runs,
  independent-review dispatch, technical acceptance, isolated commits,
  pushes to the dedicated branch only.
- **External Pro**: constructive advice before a freeze; independent
  CODE_SCIENCE_ALIGNMENT_AUDIT after technical acceptance and an exact
  pushed public revision.

## Subagent and model mapping

| Work | Subagent | Model / effort |
|---|---|---|
| Bounded, well-specified implementation unit | `hmasd-implementer` | opus / high |
| Independent engineering review (clean context, pre-acceptance) | `hmasd-reviewer` | opus / xhigh |
| Read-only object-existence / semantics reconnaissance | `hmasd-scout` | sonnet / medium |
| Read-only mechanical verification (inventory, byte-compare, counts, summaries) | `hmasd-mechanic` | haiku / low |
| Science decisions, freezes, intake, technical acceptance, commits | orchestrator, never delegated | session model |

Per-call `model` overrides remain allowed for one-off calibration; profile
frontmatter is the default. Subagent output is advisory input to the lane
owner; acceptance decisions stay in the orchestrator.

## Per-candidate loop

1. Explorer lane freezes the treatment/revision brief (file artifact under
   `temp/handoffs/` or `local_research/`).
2. CM lane implements against the frozen brief; focused proof-sized tests;
   deterministic CLI/evidence-index binding. Long runs go to background
   Bash; lanes continue meanwhile.
3. `hmasd-reviewer` performs an independent engineering review; findings
   are resolved before acceptance.
4. Configuration check (shared control-plane diff vs base must be empty),
   isolated commit(s), push the dedicated branch only.
5. Explorer lane authors the Pro question; orchestrator performs browser
   transport; verbatim archive (byte-compared); bounded intake JSON;
   disposition drives close or a narrowed loop.
6. Update `local_research/RESEARCH_CONTINUITY.md` after every completed item.

## External Pro session separation

- Pro reads exact pushed commits via GitHub connector; questions carry the
  frozen contract plus commit/source/test/evidence locators, not pasted code.
- Constructive sessions may be reused only for true follow-ups on the same
  candidate.
- Every CODE_SCIENCE_ALIGNMENT_AUDIT uses a fresh clean conversation that
  has never given constructive advice on that candidate.
- Conversation URLs of both session kinds are recorded in transport facts
  and intake JSON so independence lineage is auditable.

## Control-plane boundaries

- Shared/Codex control plane is hard read-only: `AGENTS.md`, `.agents/`,
  `.codex/`, `docs/project/`, `scripts/hmasd_workspace_ticket.py`,
  `scripts/hmasd_workspace_boundary_guard.py`. Diff vs base must be empty
  at every commit and at final handback. Known reconciliation item for WDM:
  AGENTS.md still describes `.claude/agents/` as thin entry profiles; per
  the 2026-08-05 user amendment they are now self-contained Claude-native
  contracts. AGENTS.md is not edited from this branch.
- Claude control plane (`CLAUDE.md` pointer, `.claude/`) is maintained by
  the Claude orchestrator per that amendment, always in dedicated
  configuration commits, never mixed with candidate science commits, and
  enumerated item-by-item in `FINAL_HANDBACK.md` for a separate user merge
  decision.
- Tracked changes go only to the dedicated takeover branch; no direct push,
  merge, rebase or cherry-pick to `aggressive`.
