# Engineering constraints, control-plane audit and map — 2026-09-16

Owner request: remove numerical engineering constraints; compare the control plane before Claude's recent rewrite with its current state; maintain a compact descriptive map.

Base: `b24c4c8be1387b3f0963c8ce9229581a82001acd`. Audit starts at `3196d2fc353dae5090c20517177aa15adaa52ec0`. Author: ChatGPT Pro (GitHub connector). This change neither resumes research nor changes the owner-selected runtime split.

| Surface | Change |
| --- | --- |
| Constitution; AGENTS/CLAUDE; shared engineering; Codex DM/Implementer; tests/AGENTS; envs/AGENTS | Remove arbitrary code-size, orchestration-share, test-time/count, runner-count, fixed L0-line and entry-byte/proposal-format quotas. Preserve substantive correctness, review and resource-safety checks. |
| Claude Implementer metadata and affected generated engineering/hub/Implementer bodies | Adjust maintained description and regenerate with the unchanged publisher. Models, tools and Codex effort/approval/sandbox settings unchanged. |
| Constitution links | Correct two relative evidence links after the move to docs/project; evidence targets unchanged. |
| `docs/project/CONTROL_PLANE_MAP.md` | Authority/source/generation/runtime/roles/state/execution/transport/retirement navigation. Optional pointer in AGENTS, not another rulebook or preload. |
| `docs/Claude_docs/reviews/CONTROL_PLANE_REWRITE_AUDIT_20260916.md` | One-off pinned-version audit; distinguishes intentional changes, restored protections, unresolved conflicts and unverified live state. Other findings are not silently implemented. |

Validation: source and publisher blob hashes checked; original affected generated outputs reproduced in a reduced fixture, then regenerated after edits. Targeted quota-removal, execution-section and native-metadata checks passed. Publisher orphan detection and retired-helper copying limitations reproduced with non-executed sentinels. This is not a full-repository drift/test run or independent second-agent review; no actual Windows/WSL/Agentify/session validation was performed.

Scientific fits/seeds, runtime concurrency choices, pause, real memory floor, exact-source/handle safeguards and frozen experimental contracts are unchanged. No training, Send, worktree deletion or historical rewrite occurred. Remaining fixes are proposals in the audit, not adopted new rules.
