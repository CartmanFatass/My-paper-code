# HMASD Workflow Improvement Notebook

This is an optional engineering notebook for improving how Codex tasks,
experiments, monitors, external reviewers, Git, and project-control documents
interact. It is not part of the active control plane, is not a default read,
and does not trigger a Skill or authorize an action.

Current instructions remain owned by `AGENTS.md`, the applicable project Skill,
and the five files under `docs/project/`. When an improvement is accepted, its
enforceable rule belongs in that owning source; this notebook retains only the
problem, rationale, and pointer.

Read this file only when the user explicitly requests a workflow review, a
repeated operational failure suggests a process defect, or the controller is
designing a replacement workflow.

## Accepted Improvements

| Date | Problem | Root cause | Accepted correction | Owning source |
| --- | --- | --- | --- | --- |
| 2026-07-19 | A monitor task ended with `MONITOR_ACTIVE` and never delivered the later terminal state. | A Codex task cannot remain a background waiter after its final answer; the prompt treated conversational availability as process persistence. | One registered heartbeat wakes one persistent Luna Medium monitor task for bounded ticks. | `.agents/skills/hmasd-experiment/references/experiment-protocol.md` |
| 2026-07-19 | Repeated monitor attempts created ambiguous ownership of cadence and terminal cleanup. | Initial binding and runtime automation management were not separated. | The controller owns initial binding only; the monitor owns ETA-based cadence and terminal pause. | `.agents/skills/hmasd-experiment/SKILL.md` and `references/monitor-task.json` |
| 2026-07-19 | Cross-task delivery risked model/thinking drift. | A live value was treated as permission to rewrite a stored route expectation. | Normal research uses the user-frozen `gpt-5.6-sol` / `ultra` controller route. A mismatch blocks delivery; only explicit user direction changes the frozen route. | `.agents/skills/hmasd-task-router/SKILL.md` |
| 2026-07-19 | Monitor displayed 100% training with ETA zero while the experiment remained `running`. | Per-arm training counters ended before final evaluation and aggregation, while the parent status exposed only launch and terminal states. | Display `FINALIZATION_PENDING`; do not infer experiment terminal from training counters. | `.agents/skills/hmasd-experiment/references/experiment-protocol.md` |

## Open Improvement Backlog

### Runner phase observability

The parent runner should atomically update `runner_status.txt` at meaningful
boundaries such as `training`, `final_evaluation`, `semantic_audit`, `analysis`,
and `terminal`. Its `updated` field should change at each boundary. This would
remove the need for Monitor to infer finalization from child counters.

### Arm terminal observability

An arm reaching its full training budget should stop publishing
`state=running, phase=training`. It should publish a truthful next phase or a
contained arm terminal result. The parent remains the only scientific terminal
authority.

### Orphan monitor-process cleanup

Replacing a monitoring transport should include a bounded check for processes
owned by the removed transport. Stop only an exactly identified obsolete
monitor process; never touch the experiment parent or workers.

### Runtime self-management evidence

For each future Monitor workflow change, one bounded smoke should demonstrate
that the registered monitor can update the existing heartbeat, preserve its
target/model route, pause it, and send one terminal relay. Do not add recurring
workflow tests after this capability is established.

## Entry Template

```markdown
### YYYY-MM-DD — Short problem name

- Symptom:
- Direct evidence:
- Root cause:
- Accepted correction or open option:
- Owning source if accepted:
- Evidence that closes the item:
```
