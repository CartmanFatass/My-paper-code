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

## Skill mapping (Codex procedural Skills → Claude workflow)

| Codex Skill | Status | Claude-native mapping |
|---|---|---|
| `hmasd-agile-research-development` | **Adopted as engineering contract** | Its invariants are session-agnostic and bind the CM lane directly: proof-sized tests with the oracle preference order (exact hand-checkable case → structural/metamorphic invariant → differential vs small reference → boundary/fail-closed → seeded band last); a focused test must reject one plausible wrong implementation; small-change shape (≤3 new tracked files, ≤500 new active lines per mechanism, refactors net-negative, files >1200 lines never grow); successor deletes predecessor in the same commit; no versioned scientific filenames; no hash handoffs; complexity gates (evidence search ≤ O(H*K_search), K_search≤16, ≤16*H hypothetical transitions, no nested rollout/tree/MCTS, 20-min nonformal wall-clock cap). Session-bound mechanics are remapped: the registered `hmasd-verifier` child → the Skill-owned `hmasd_execution_readiness.py` script stays the sole executor of phase argv (orchestrator or `hmasd-mechanic` merely invokes run/finalize and consumes the receipt); the Codex Stop-hook and nine-iteration Pro grant loop → not applicable under the user-directed takeover grant; transport routing → next row. |
| `hmasd-agentify-transport` | **Remapped; artifact contract preserved** | The dedicated transport session is replaced by the orchestrator driving the provider page directly with Chrome tools. Preserved invariants: one batch file (`provider`, ordered `question_paths`) is the only prompt source; the sent payload is exactly the UTF-8 question file content, no local metadata; one ordered results envelope with `question_path`/`status`/`response`/`conversation_url`/`error` per row, completed rows preserved on later failure; raw responses archived verbatim and byte-compared; clean conversation for independent reviews, reuse only for a true follow-up; never interrupt an active generation, never duplicate a possibly-submitted question, never send a placeholder or press Continue/Retry/Stop; a transport error is a transport fact, never a scientific result. |
| `hmasd-explorer-project-validation` | **Absorbed into the per-candidate loop** | Explorer→CM briefs remain self-contained file artifacts under `temp/handoffs/explorer_to_code_manager/` (loop step 1); CM executes the named treatment without substitution; a genuinely scientific choice returns to the Explorer lane as a concrete question; after technical acceptance the exact commit plus public GitHub locators are pushed; the audit question asks Pro to reconstruct the realized proposition, strongest hidden assumption/alternate explanation and evidence discriminating power — never a pre-filled findings checklist; `formal=false`, no `CURRENT_WORK.md` mutation. |
| `hmasd-independent-research-exploration`, `hmasd-independent-research-pro-review` | **Excepted (user decision)** | Explorer is not procedurally mapped: the local core is deliberately shrunk to longitudinal state, freeze decisions and verbatim archive + intake; scientific content work leans on External Pro dual sessions (constructive vs audit). The review-item file conventions (`20_RAW_QUESTION.md` / `40_RAW_RESPONSE.md` / `60_ALIGNMENT_INTAKE.json` under one item root) are retained for archive compatibility. |
| `hmasd-collaborative-workflow-design`, `hmasd-workflow-change-audit` | **Out of scope** | WDM-exclusive control-plane procedures. The Claude orchestrator records workflow defects/reconciliation items for WDM and never executes these Skills or edits their surfaces. |

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
