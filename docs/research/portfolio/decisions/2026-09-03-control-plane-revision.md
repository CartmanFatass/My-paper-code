# Control-plane revision after the §11 calibration

Date: 2026-09-03

Decision: `FINAL / OWNER_DIRECT / ROOT_INTEGRATED` (draft on branch `control-plane-revision-20260903`, merge pending owner review)

## Provenance

- Request: owner, in session `session_015hGLzLCuJLFFtZTboKg2bd` ("请帮我审阅一下" the Codex
  control plane; "使用ask的方式和我对齐修改方案")
- Evidence: `docs/Claude_docs/reviews/CODEX_CONTROL_PLANE_REVIEW_20260903.md` (§3 stale
  clauses, §5 recommendations, §9–10 the owner's intent for the Pro nodes)
- Owner answers recorded 2026-09-03 18:15 PDT through eight aligned questions

## Decisions

| # | Question | Owner's answer |
| --- | --- | --- |
| 1 | Which decisions go to the Pro nodes when Codex runs unattended | Direction and Portfolio tiers only; object-tier decisions are taken locally by the DM under the delegation policy and recorded |
| 2 | Loop behaviour on a Pro blocker | Object tier: provisional local decision, reversible actions only, labelled `PRO_BLOCKED / LOCAL_PROVISIONAL`; direction and portfolio tiers: the direction parks, Root drives another |
| 3 | Roster | 16 → 9: EM folded into DM as the loop driver; `em`, `research-innovator`, `research-principles-analyst`, `research-scout`, `workflow-designer`, `design-reviewer`, `general-leaf` retired to Git history |
| 4 | CM performance-readiness gate | Replaced by two recorded lines: per-arm cost projection before any sweep (cap per arm), offline exercise of the post-learner path and an end-to-end profile that reaches it before a fresh attempt |
| 5 | `AGENTS.md` | Rewritten runtime-neutral with Codex and Claude Code appendices; Claude drafts, owner reviews and merges |
| 6 | The 2026-09-03 09:57 uncommitted control-plane edits | Committed (`ac5cd664e`), with the prompt-author receipt wording aligned to the fixed return session and the four transport tests rewritten to that contract |
| 7 | Housekeeping | All four: empty authority directories removed, `.codex/runtime/` removed, third-party skills moved to `.agents/third_party/` (`502896633`), the `hmasd_operator_result` citation dropped from the CM definition |
| 8 | Confirmations | The routine-implementer swap to Luna/max is intentional; `docs/project/ALGORITHM_PRINCIPLES.md` is background, no longer required reading |

Deviation from 7: `scripts/hmasd_operator_result.py` itself is kept, because `scripts/hmasd_run.py`
imports it for the `promote` path and `tests/hmasd_run_test.py` depends on it; only the CM
definition's citation is removed.

Clarifications that shaped the answers (review §9–10): the Pro nodes exist so that the Codex side
runs unattended with the owner intervening from the records; Pro performs better than the local
models and runs on an independent quota, so a Pro round is not a cost to minimise. The owner
nevertheless keeps object-tier decisions local for latency, with Pro at the two tiers the owner
audits.

## Effect on the Portfolio

No lifecycle, priority or owner change. `PORTFOLIO.md`'s `Investment capacity: UNBOUNDED` is to be
replaced by the two numbers in the new `AGENTS.md` §5 (two implementer sessions, two result-bearing
runs) when the branch merges.
