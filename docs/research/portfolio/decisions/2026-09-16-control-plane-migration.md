# Control-plane migration — OWNER_DIRECT 2026-09-16

Authority: the owner's instruction to execute the supplied
[migration plan](../../../project/CONTROL_PLANE_MIGRATION_PLAN_20260916.md).
This is shared-control engineering, not a Portfolio decision or research resumption.
Research remains paused under the owner's 2026-09-15 22:23 PDT instruction.

## Assignment and baseline (L0 / M0)

Root owns AGENTS/roles, seven task methods, runtime publication and current views.
Goal: remove repeated rule loading and implement plan §5 prospectively while preserving
frozen scientific meaning. No training, CF implementation, Pro/Portfolio Send, new
runtime scheduler/service, approved membership or ACVC lifecycle change is in scope.
Acceptance: protected-byte/source checks, focused helper tests, actual native loading
and bounded behavioral probes, independent shared-control review, publication and handoff.
Rollback uses new reverting commits; it cannot erase external effects.

Actual main baseline was `e9399305d58bdd7e5f9518e12cf43e9abd199ee3`, not the plan's
older `941ed56a0` hint. FSD was `b034cb0d9eb1ef2031d33dde1c60441242adc138` and ACVC
`66abf52ca0a8323ebd9df936bbef165cb831da6c`; these heads matched origin during inventory.
The previously foreign Transport/wait edits were already committed in main; no dirty
foreign paths were swept into this assignment. Isolated implementation checkout:
`C:/Projects/HMASD-worktrees/control-plane-migration-20260916`, branch
`codex/control-plane-migration-20260916`. Baseline file sizes/hashes are in
[BASELINE](../../../project/CONTROL_PLANE_MIGRATION_BASELINE_20260916.json).

## Unique rule ownership (M1–M3)

Paths below are relative to repository root. Each row identifies the maintained method;
old spec bodies remain historical, with a retirement header and original Git versions.
This mapping is migration evidence, not another mandatory loading index.

| Old source / subject | Current maintained owner | Treatment |
| --- | --- | --- |
| AGENTS scope, authority, pause, frozen meaning, Git | AGENTS.md | MOVE_UNCHANGED: original meaning compressed; REMOVE_SUPERSEDED: obsolete refill/CM instructions |
| Evidence spec §§4–5, 11; two-axis programme | .agents/skills/hmasd-scientific-tools/SKILL.md | MOVE_UNCHANGED: current methods; CHANGE_PROSPECTIVE: plan §5 statistics, lanes, comparator and exposure corrections |
| Engineering scope §§7.1–7.3; runtime engineering constraints/admission | .agents/skills/hmasd-research-engineering/SKILL.md | MOVE_UNCHANGED: L0, review risks, limits and execution; named frozen exceptions retain exact old sources |
| ROOT_OPERATIONS, SIBLING_COMMUNICATION, EXPERIMENT_MONITOR | .agents/skills/hmasd-loop-dispatch/SKILL.md and native role bodies | MOVE_UNCHANGED: coordination and bounded interfaces; REMOVE_SUPERSEDED: mandatory old manual loading |
| Portfolio task and scattered refill routes | .agents/skills/hmasd-portfolio-task/SKILL.md | MOVE_UNCHANGED: owner-triggered review; REMOVE_SUPERSEDED: vacancy dispatch |
| Pro authoring / GITHUB_RESEARCH_COLLABORATION | .agents/skills/hmasd-pro-research-prompt-author/SKILL.md | MOVE_UNCHANGED: full normal authoring and one-hop partial-success details; REMOVE_SUPERSEDED: old manual prerequisite |
| Transport normal effect/recovery/archive | .agents/skills/hmasd-chatgpt-pro-transport/SKILL.md | MOVE_UNCHANGED: same-request effects; rare unrecoverable-conversation appendix split |
| Owner item mechanics | .agents/skills/hmasd-owner-item/SKILL.md | MOVE_UNCHANGED: item tool/schema; REMOVE_SUPERSEDED: ordinary pilot ceremony |
| Codex roles and Claude duplicate policy | .codex/agents/*.toml plus tools/publish_claude_control.py | MOVE_UNCHANGED: short native roles; CHANGE_PROSPECTIVE: deterministic publication and explicit runtime adaptation under plan §4 |
| Current view entrypoints | PROJECT_MAP, PORTFOLIO, EXPERIMENT_TRACKING, current dossier | CHANGE_PROSPECTIVE: source/current-object presentation; REMOVE_SUPERSEDED: obsolete current routes; historical execution evidence retained |

Codex role model, effort, approval and sandbox metadata and parsed project config are
unchanged. Claude model/tools metadata remain native; Operator returns to hub, which
assigns its bounded Tracker. Claude Pro preserves CALLER_DIRECT and actual-session UUID5
metadata, native Sonnet routing and existing post-acceptance binding/archive helpers.
The publisher is a development command with read-only `--check`, never an experiment gate.
Generated complete trees contain executable helpers and references; edits belong in shared
sources/adapter, not generated bodies. Suspended implementer/CM roles remain closeout-only.

## Explicit prospective changes (M4)

Classification: CHANGE_PROSPECTIVE for each plan §5 correction below; no retroactive application.

Plan §5.1–5.2 separates approval, lane, evidence class and execution status; only the
approved set authorizes admission, completion does not grant a successor or next week's
budget, and CLOSE lane queues lifecycle material without making a new Portfolio verdict.
§5.3 uses B/EXPLORE with PILOT labeling, local bounded batch choices and actual fit counting;
A/RECON cannot report algorithmic effects. §5.4 freezes all interpretation branches and
permits ordinary covered results to be intaken without another Pro round. C consumption
semantics remain object-specific; CONFIRM alone promotes neither evidence nor consumption.
§5.5 removes large-MEI substitution for independent training repetitions and forbids
pseudo-replication or result-driven extra seeds. §5.6 spells out MARL information, cadence,
communication, replay/reset, selection/compute differences and reusable baseline contents.
§5.7 retains direct DM implementation and independent high-risk path review. §5.8 records
actual work/exposure, distinguishes fit wall sums from batch elapsed/CPU, and serializes
launch acceptance with fresh admission without inventing a reservation service. §5.9 keeps
three core scientific records, proportionate owner surfaces and source-grounded current views.

`render_packet.py` no longer gives Convergence blanket Portfolio PARK/CLOSE power.
FSD's current dossier describes D1280 versus central-input CF, 16 fits, J45, MEI .05 and
no established headroom; the old .67 reference does not define this card's threshold.
ACVC's wrapper results and package comparisons are separately stated, with no new verdict.

## Frozen bindings and compatibility

No candidate scientific file, accepted TASK/HANDOFF/REQUEST, archive, seed, result or
APPROVED_SET membership changed. The complete FSD card/handoff blobs and original method
snapshots are recorded in [CHECKS](../../../project/CONTROL_PLANE_MIGRATION_CHECKS_20260916.json).
That artifact also records every `REQUEST.reference_files` path at its actual explicit
commit, including the workflow/portfolio rules bound at
`999e838cf764928b11d484f2232fde24a43f949f`; request default source was
`b8c41ad27f85c9269a9e25adc4e9836af650061b`. The original question contained the rejected
headroom proposal; it remains intact and is not confused with the resulting matched-input card.
The FSD branch did not contain the lane decision file at its handoff commit; that absence
does not erase the explicit request-bound source. Old named appendix exceptions remain
readable at the baseline commit. No retrospective relabeling or budget recalculation occurred.

## Verification (M5)

Installed runtimes: Codex 0.154.0, Claude 2.1.273, Python 3.11, Node 24.18, Git 2.55.
No same-named global skill conflict was found. Global Codex stale disabled agile entry and
old hook paths were observed but not changed; no claim of global configuration cleanup.
Seven shared skills pass skill-creator quick validation. TOML/config preservation and
protected blobs pass; generated publication has zero drift.

- Existing authoring/science/native-transport/send-recovery tests: 202 passed in 7.34s.
- New publisher plus renderer focused pass after scope correction: 82 passed in 1.97s.
- Final adapter/publisher/Claude-archive/renderer pass: 95 passed in 4.14s.
  These overlap; they are not 379 distinct tests. The first run had fixture setup errors
  because `temp/tests` did not exist; after creating the scratch parent it passed.
- Actual fresh Codex root and native DM/Operator/Transport sessions read the new skills
  and performed bounded hypothetical probes. Claude hub, Reviewer and Operator probes
  used actual native startup and Read/Skill traces. Filtered action/session evidence is
  in [NATIVE](../../../project/CONTROL_PLANE_MIGRATION_NATIVE_20260916.json); original
  rollout paths are retained there. Child identity uses actual spawn IDs/log filenames,
  not the inherited parent session_meta present in forked logs.
- Behavioral coverage: pause/empty capacity; authorized continuity; covered negative or
  wide results; n=1 despite more episodes/large MEI; missing stage-0 fit; high-risk replay
  versus documentation; uncertain Send; concurrent admission; foreign writer preservation;
  current card versus old dossier; old sessions requiring real refresh.
- Reviewed native agent-issued calls contain local reading and probe collaboration only,
  no training, SSH launch, Agentify Send or scientific edits. CLI startup may contact its
  own plugin/model services; this is not a claim of zero network packets. Full injected
  system context is not exposed by all logs. Operator made one failed legacy role-path
  lookup before reading the correct native config; DM evidence reads included a historical
  cited card, not adoption of its superseded rules.

Independent reviewer `/root/review_ah_control_migration` inspected the shared control and
actual child tool traces. Findings repaired: Claude Operator/Tracker return path; renderer
lifecycle scope; complete C freeze fields; Claude routing/binding/model; Grok clerk fences;
obsolete GitHub prerequisite; native evidence child identities. Final adapter/identity
recheck found no remaining material implementation finding; final publication receipt
is recorded in the handoff after integration.

Root AGENTS shrank 55,161→5,485 bytes; CLAUDE 16,258→1,753 bytes. Full per-file and role-body
measurements are in CHECKS. Bytes are not token counts. Science/engineering/Transport
exceed the soft 6KB skill target to retain normal-path statistical, execution and effect
rules self-contained; generated Claude Transport/hub include explicit runtime adaptation.
Directory-specific core/test conventions remain where unique. No size becomes a launch gate.

## Deliberate limits and pending decisions

- Old generic wall review signals conflict: AGENTS 2700/43200s versus runtime spec
  5400/64800s. Numerical consolidation is pending owner resolution. Neither becomes a
  new launch/stop/result-validity gate; exact frozen object caps remain unchanged.
- Seven-day window origin and debit/refund semantics were not defined by the old source.
  Owner budget review must resolve them before a new allocation depends on them; unfinished
  work does not gain duplicate exposure and failure grants no retry. No resource cap invented.
- Remote hardware/process state was not established by this migration; a scout alias
  connectivity probe did not verify SSH routing. Live browser/legacy agent states were not
  exhaustively inspected. Registry archival facts are local evidence, not a process census.
- Existing long-lived sessions are not magically refreshed by disk edits. Only the new
  bounded native sessions above are verified. Next research owner must start/refresh from
  published controls and prove actual method loading after an explicit research-resume instruction.
- Automatic approval review rejected recursive scratch cleanup twice despite path checks;
  no bypass attempted. Migration scratch and worktree are retained pending permitted cleanup.
  No unique source/evidence was deleted. This is a cleanup limitation, not scientific work.

## Integration and rollback (M6)

Root publishes the reviewed migration branch, fast-forwards clean main and publishes only
needed current controls into the clean paused FSD checkout, preserving scientific files.
Exact source/remote receipts and final migration state belong in the
[handoff](../handoffs/2026-09-16-control-plane-migration.md). Other paused direction branches
are not claimed refreshed. Known-good control baseline is main `e9399305d58bdd7e5f9518e12cf43e9abd199ee3`.
Any rollback is a new reviewed reverting commit over migration commits, not reset/rewrite;
current evidence and any independently observed external effects must remain reconciled.
