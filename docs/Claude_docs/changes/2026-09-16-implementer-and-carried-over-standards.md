# Implementer role and carried-over engineering standards — Claude hub, 2026-09-16 18:32 PDT

Owner instruction 18:32 PDT: both runtimes use an Implementer role for context pressure and
cost (Claude: Opus; Codex: Sol; both high effort), and the rewrite must carry over the earlier
engineering standards where appropriate. The owner's instruction is recorded as an amendment of
`docs/project/OPERATING_CONSTITUTION.md` (sections 2 and 6).

## Audit: what the 18:05 rewrite of `hmasd-research-engineering` had dropped

| Earlier standard | Status after 18:05 | Now |
| --- | --- | --- |
| Never-build list (workers, pools, schedulers, retries, leases, guards, validators, registries, shims) | kept, shortened | kept, restored in full with the `scope:` rule |
| Size budgets 2,000 new non-test lines per attempt, 600 per runner; orchestration 30 percent as a review signal | dropped | restored as review signals |
| Research-directory tests under five minutes; no repeated smoke per launch | dropped | restored |
| Stage only committed source and declared artifacts at their digest; currentness by declared bytes, not commit id | dropped | restored |
| Telemetry rule (missing wall/RSS/scratch marks `resources_unmeasured`; only a resource claim is annulled; missing learner instrumentation quarantines) | dropped | restored |
| Quarantine of incomplete attempts; fresh outcome-blind attempt at a new sha; failure grants no fits | partly (failure is not a negative) | restored in full |
| Diagnosis by reproduction (direct facts now, root cause provisional, repair when the next claim depends) | dropped | restored |
| Local fallback boundary (portability established first, no remote process, fresh local admission; routing changes no dtype/device/RNG/comparator) | dropped | restored |
| RSS scope and CPU accounting, no standing profiler, no automatic GPU/JIT/language migration | kept | kept |
| Memory preflight 4 GiB on the executing node, `preflight && runner` under agent-task, detached exact-sha worktree | kept | kept |
| Independent review triggers (core, semantics, numerics, RNG, replay, checkpoint identity, external effects, launch and Pro tooling) | kept | kept |
| Summary carries learner movement relative to initialisation (the old exposure line) | dropped | restored as a runner requirement |
| Historical per-object exceptions (DISH A05, CBSC B1, VNFC E01, ACVC/RCLE retained policy) | dropped | not restored: those directions are archived; the exceptions stay in their own documents |
| Generic wall thresholds (2700/43200 s versus 5400/64800 s) | dropped | not restored: the owner has not resolved the conflict and neither value was a gate |
| The 100-line exception and object-specific A/D line caps | dropped | not restored: tied to archived objects |

`hmasd-scientific-tools` kept comparators, MARL information, statistics, cost and exposure
accounting, baseline reuse and the tools section; it dropped evidence classes, C consumption,
MEI verdicts, cards, intake and the seven-day windows, all replaced by constitution sections 3,
4 and 8.

## Changes

| Time (PDT) | Surface | Change | Trace |
| --- | --- | --- | --- |
| 18:40 | `docs/project/OPERATING_CONSTITUTION.md` | Amendment line in the header; Implementer bullet in section 2; carried-over standards paragraph in section 6. | this commit |
| 18:40 | `.codex/agents/hmasd-implementer.toml`, `.codex/config.toml` | New Sol/high Implementer role (was a suspended stub deleted at 17:18); registered as `HMASDImplementer`. | this commit |
| 18:40 | `.claude/agents/hmasd-implementer.md` | New Opus Implementer role; body generated from the Codex role by the publisher (`ROLE_MAP` entry added). High effort is stated in the description; the agent frontmatter has no effort field. | this commit |
| 18:40 | `.codex/agents/hmasd-direction-manager.toml`, `tools/publish_claude_control.py` | DM hands bounded code tasks to the Implementer from five L0 lines and accepts the diff; the Claude replacement table maps `HMASDImplementer` to `hmasd-implementer`. | this commit |
| 18:40 | `.agents/skills/hmasd-research-engineering/SKILL.md` | New "L0 and the Implementer" section; new "Carried-over engineering standards" section per the audit above. | this commit |
| 18:40 | `AGENTS.md`, `CLAUDE.md`, `.agents/skills/hmasd-loop-dispatch/SKILL.md` | Implementer named in the role lists; AGENTS points to the carried-over standards. | this commit |
| 18:40 | `.claude/skills/**`, `.claude/agents/*.md` | Regenerated; drift 0; publication tests passed. | this commit |
