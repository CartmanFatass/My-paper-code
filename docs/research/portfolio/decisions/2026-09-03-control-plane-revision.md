# Control-plane revision after the §11 calibration

Date: 2026-09-03

Decision: `FINAL / OWNER_DIRECT / ROOT_INTEGRATED` (merged as `824b499aa`; the earlier draft/merge
status is closed)

> **Current-status overlay (2026-09-04).** This record remains evidence of the 2026-09-03
> revision. Its fixed receipt route, two-direction capacity, and unratified Portfolio audit-window
> behavior are superseded. Current routing is one on-demand Transport operator per handoff with one
> receipt to the handoff author's declared `parent_thread_id`; new operators use Luna/high;
> repository research capacity has no fixed cap; and a
> Portfolio proposal never takes effect before owner ratification. See root `AGENTS.md` and
> `2026-09-04-dm-max-and-unbounded-research-capacity.md`.

## Provenance

- Request: owner, in session `session_015hGLzLCuJLFFtZTboKg2bd` ("请帮我审阅一下" the Codex
  control plane; "使用ask的方式和我对齐修改方案")
- Evidence: `docs/Claude_docs/reviews/CODEX_CONTROL_PLANE_REVIEW_20260903.md` (§3 stale
  clauses, §5 recommendations, §9–10 the owner's intent for the Pro nodes)
- Owner answers recorded 2026-09-03 18:15 PDT through eight aligned questions

## Decisions

| # | Question | Owner's answer |
| --- | --- | --- |
| 1 | Which decisions go to the Pro nodes when Codex runs unattended | Direction-tier final decisions and Portfolio-tier proposals; object-tier decisions are taken locally by the DM under the delegation policy and recorded |
| 2 | Loop behaviour on a Pro blocker | Object tier: provisional local decision, reversible actions only, labelled `PRO_BLOCKED / LOCAL_PROVISIONAL`; direction and portfolio tiers: the direction parks, Root drives another |
| 3 | Roster | 16 → 9: EM folded into DM as the loop driver; `em`, `research-innovator`, `research-principles-analyst`, `research-scout`, `workflow-designer`, `design-reviewer`, `general-leaf` retired to Git history |
| 4 | CM performance-readiness gate | Replaced by two recorded lines: per-arm cost projection before any sweep (cap per arm), offline exercise of the post-learner path and an end-to-end profile that reaches it before a fresh attempt |
| 5 | `AGENTS.md` | Rewritten runtime-neutral with Codex and Claude Code appendices; Claude drafts, owner reviews and merges |
| 6 | The 2026-09-03 09:57 uncommitted control-plane edits | Committed (`ac5cd664e`) against the then-current return-session contract; this historical routing is superseded by the creator-session route in the overlay above |
| 7 | Housekeeping | All four: empty authority directories removed, `.codex/runtime/` removed, third-party skills moved to `.agents/third_party/` (`502896633`), the `hmasd_operator_result` citation dropped from the CM definition |
| 8 | Confirmations | The routine-implementer swap to Luna/max is intentional; `docs/project/ALGORITHM_PRINCIPLES.md` is background, no longer required reading |

Deviation from 7: `scripts/hmasd_operator_result.py` itself is kept, because `scripts/hmasd_run.py`
imports it for the `promote` path and `tests/hmasd_run_test.py` depends on it; only the CM
definition's citation is removed.

Clarifications that shaped the answers (review §9–10): the Pro nodes exist so that the Codex side
runs unattended with the owner intervening from the records; Pro performs better than the local
models and runs on an independent quota, so a Pro round is not a cost to minimise. The owner
nevertheless keeps object-tier decisions local for latency. Direction Pro decisions are final for
their node; Portfolio Pro responses are proposals that the owner ratifies.

## Effect on the Portfolio

At the time, no lifecycle, priority or owner change was made and the branch replaced the earlier
`UNBOUNDED` capacity with two numeric caps. The owner reversed that capacity choice on 2026-09-04;
the current `PORTFOLIO.md` and `AGENTS.md` again impose no fixed repository research-capacity cap.
