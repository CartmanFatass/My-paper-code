# Owner console design (2026-09-04, revision 2)

Alignment draft, written by Claude Code (Fable 5.1) at the owner's request. Revision 2 follows the
owner's clarification at 07:36 PDT: the console's content is **updated by the Codex side**; the
owner **grades** each item (a choice among options with a marked recommendation, plus a free
comment); the graded items are **exported as a markdown document that Codex reads**. Nothing is
built yet. Markers: **[DECIDE]** owner's call; **[ASK]** default the author takes unless told.

## 0. The shape

```
Codex loop (DM / Root)                 Owner console (localhost)              Codex loop
  writes one item file per thing  --->  renders items as grading cards  --->  reads the review md
  that needs the owner's eye            owner picks an option + comments       at every clean boundary
  (options, recommendation,             console exports answered items         and applies replies
   evidence links, auto-applied?)       to reviews/<date>.md + commits
```

Three facts fix the design:

1. **The item is the unit.** Everything the owner grades is one item with the same fields: a
   delegated decision that was auto-applied, a new card, a prediction request, a brief, a critic
   dissent, a second recast, a Portfolio proposal. One card layout serves all of them.
2. **Codex writes items, never HTML.** Items are small structured files the DM writes at the
   moment it makes the decision, next to the ledger row. The console only renders.
3. **The owner's output is markdown.** The console keeps its own reply state, but the artifact the
   loop reads is `docs/research/portfolio/owner/reviews/<YYYY-MM-DD>.md`, regenerated from the
   replies on every save and committed by pathspec. Codex reads that file, not the console.

## 1. The item format (what Codex writes)

One file per item, `docs/research/portfolio/owner/inbox/<YYYY-MM-DD>/<id>.json`. JSON because the
DM writes it programmatically and the console parses it without a markdown-table parser; the
human-readable mirror is the ledger row and the review md. **[ASK]** JSON rather than a markdown
file with YAML front matter; either works, JSON is less fragile.

```json
{
  "id": "20260905-fsd-003",
  "created": "2026-09-05T03:12:00Z",
  "direction": "flexible_skill_duration",
  "tier": "object",
  "kind": "decision",
  "title": "E3 之后的下一 rung",
  "context": "≤200 字 markdown：在决定什么，为什么是现在，DM 看到了什么",
  "options": [
    {"key": "a", "label": "E2b：把 c=0.25 迁移到 scenario 1", "consequence": "…"},
    {"key": "b", "label": "E4：随机时长事件", "consequence": "…"}
  ],
  "recommended": "a",
  "dm_reason": "一句话",
  "auto_applied": "a",
  "evidence": ["docs/research/candidates/flexible_skill_duration/FSD_E3_..._INTAKE_20260905.md"],
  "ledger_row": "docs/research/portfolio/audit/2026-09-05.md#L14",
  "brief": "docs/research/portfolio/owner/briefs/flexible_skill_duration/2026-09-05_E3.md",
  "status": "open"
}
```

`kind` values and what the options mean for each:

| kind | options | typical owner reply |
| --- | --- | --- |
| `decision` | the DM's options; `auto_applied` names the one already executed under delegation | agree (empty), or another key = override at the next clean boundary |
| `new-card` | `accept` / `reject` / `revise` | reject with the reason, or a revise comment |
| `prediction` | the two or three competing mechanisms | pick the winner; comment carries magnitude or `unclear` |
| `brief` | `reading-agreed` / `reading-disputed` | dispute with the comment |
| `critic-dissent`, `close-call` | the DM's options, plus the critic's position as one option | as decision |
| `second-recast` | `continue-low-priority` / `park` | park or continue |
| `portfolio` | `ratify` / `refuse` / `amend` | ratify, or amend with the comment |

Predictions and briefs become items too, so `PREDICTIONS.md` and the digest table are replaced by
the inbox: one machine surface, one human artifact. The ledger stays as the audit record and gains
the item id in its evidence path. **[DECIDE]** replace the two markdown surfaces created this
morning with the inbox, or keep them in parallel (double writing for the DM; not recommended).

## 2. The review document (what Codex reads)

`docs/research/portfolio/owner/reviews/<YYYY-MM-DD>.md`, regenerated on every save from the
replies, sections in item order. Only answered items appear; "agree" replies appear as one line so
the loop can see the item was seen.

```markdown
# Owner review — 2026-09-05

## 20260905-fsd-003 · flexible_skill_duration · decision · E3 之后的下一 rung
- recommended: (a) · auto-applied: (a) · **owner: (b)**
- comment: 先看 E4，scenario 1 的迁移等 E4 有结果一起做。
- instruction: apply (b) at the next clean boundary; supersede the delegated (a).

## 20260905-vnfc-001 · variable_n_fleet_churn · prediction · R02 K1024 headroom
- owner: (a) headroom bracket resolves above 5 % · comment: 差距我猜在 8–12 %。

## 20260905-cbsc-002 · capability_bound_semantic_currentness · new-card · …
- owner: agree
```

The loop's side (already in `AGENTS.md` §4.5 in spirit; wording to be updated): at every clean
boundary the DM and Root read today's and yesterday's `reviews/*.md`, apply any reply that differs
from the auto-applied option, mark the item `answered`, and cite the review line in the ledger.

## 3. The console

**Layout.** Left: a direction rail with pending counts and lifecycle colour. Centre: the grading
queue, one card per item, newest first, filterable by kind and direction; keyboard `j/k` to move,
`a/b/c` to pick, `Enter` to open the comment. Right: the evidence pane, rendering the linked
markdown (card, intake, brief) inside the page so the owner never leaves it.

**A card.** Title, direction chip, tier chip, `auto-applied` badge when the decision already ran,
the context paragraph, the option list with the recommended one marked ★ and the auto-applied one
marked ✓, a comment box, and two buttons: 同意 (records agree) and 提交 (records the choice and
comment). Both write the reply, regenerate the review md, and commit.

**Overview tab.** The PORTFOLIO table with usage columns, per-direction item history (a strip of
answered/open dots by day), and the last ten briefs. Read-only. **[ASK]** a small result timeline
per direction (valid results by date with verdict labels) if the intake documents carry a
machine-readable verdict line; otherwise deferred.

**Export.** Besides the daily review md, a button "导出选中项" writes
`reviews/<date>_<slug>.md` for a hand-picked set (for a Pro packet, for example).

**State.** Replies live in `inbox/<date>/<id>.reply.json` next to the item (in the repository, so
the state is recoverable and the review md is derivable). Read marks and UI preferences live in
`%LOCALAPPDATA%\hmasd-owner-console\`.

**Write-back.** On every save: write the reply file, regenerate the day's review md, then
`git add -- <paths>` and `git commit -- <paths>` with `owner: review <date> (<n> items)` and
`scope: none`. Push is a button. **[DECIDE]** commit-on-save with manual push (recommended), or
file-only.

**Runtime.** Python standard library server on `127.0.0.1:8765` plus one `index.html` (vanilla
JS, inline CSS, no CDN, Chinese UI). Runs on the system Python 3.11 or either conda env with no
installs. Location `tools/owner_console/` with unit tests for item parsing, reply writing and the
review renderer under `tests/tools/owner_console/`. **[DECIDE]** `CLAUDE.md` line 58 gains the
owner-side carve-out.

## 4. Who builds and maintains what

- **Claude (this session)**: the console, its tests, the item and review schemas as a one-page
  `docs/research/portfolio/owner/README.md` rewrite, and the wording changes in `AGENTS.md` §4.5
  and the DM definition so the DM writes items instead of digest rows.
- **Codex loop**: writes items from its next task onward; reads reviews at clean boundaries. It may
  also maintain the console later; the code has no dependency on Claude tooling. **[ASK]** the
  owner's phrase "由 Codex 端更新" is read as "the content is updated by Codex"; if it also means
  "the code is maintained by Codex", the hand-off is the README plus the tests.

## 5. Phases

1. Inbox with grading cards, evidence pane, review export, commit. Items of kind `decision`,
   `new-card`, `prediction`, `brief`.
2. Overview tab, `portfolio` and `second-recast` kinds, selected-items export, keyboard flow polish.
3. Runs view (local `temp/directions` roots; remote `agent-task list` over the SSH alias,
   read-only), optional Windows toast for `portfolio` items.

## 6. Decisions (taken with the owner, 2026-09-04 07:45 PDT)

1. Inbox items replace the digest table and `PREDICTIONS.md`. Done.
2. Commit-on-save by pathspec, manual push button. Done.
3. `tools/owner_console/` with the `CLAUDE.md` carve-out. Done.
4. Content by Codex, console by Claude; Codex may maintain the code later. Done.

## 7. Built in this session (phase 1, plus part of phase 2)

- `tools/owner_console/server.py`: item loading, reply writing, review rendering, selected-items
  export, portfolio table, briefs and reviews listing, safe document reading, git commit by
  pathspec, push, and two subcommands: `seed-ledger <date>` (one-off: every ledger row of that day
  becomes an auto-applied `decision` item, so the owner can review today's delegated decisions
  immediately) and `render-review <date>`.
- `tools/owner_console/index.html`: direction rail with pending counts, grading queue with kind
  filters, cards with ★ recommended / ✓ executed marks, comment box, 同意 and 提交, keyboard flow
  (`j/k`, `a`–`e`, `g`, `Enter`, `Ctrl+Enter`), evidence pane rendering repository markdown,
  组合 tab (PORTFOLIO table, read-only), 简报 tab, 评审文档 tab, 导出选中, 推送. Light and dark.
- `tests/tools/owner_console/test_owner_console.py`: table parsing with escaped pipes, reply
  round trip and review text, ledger seeding, path-escape refusal, portfolio parse, export.
- `docs/research/portfolio/owner/README.md` rewritten as the schema page; `PREDICTIONS.md`
  removed; `AGENTS.md` §4.5, the DM definition, the Portfolio skill and `CLAUDE.md` updated.
- Seeded: the 2026-09-04 ledger rows as items, so the console has real content on first open.

Not built: runs view, Windows toast, the per-direction result timeline (phase 3).

## 8. Revision 3 (08:10 PDT): the loop's write contract, the board page, the redesign

Owner feedback: explain how Codex updates the console and where the update node sits, guarantee
it with a skill or document; the page was cluttered, wanted a separate page for active directions
with priority ordering, and a redesign.

**Write contract.** The loop no longer writes item JSON by hand. `tools/owner_console/item.py add`
validates fields, assigns the id and writes the file; `item.py reviews` prints the owner's
unapplied instructions; `item.py mark-answered` closes them. The insertion points are pinned in a
new Codex skill, `.agents/skills/hmasd-owner-item/SKILL.md` (one row per moment in the loop with
the kind and the exact command), referenced from the DM definition and the Portfolio skill.
Stability is enforced by `tests/tools/owner_console/`: schema validation, id numbering, the CLI
round trip, and a contract test that the skill names every kind and every command and that the DM
definition references the skill.

**Insertion points.** Ledger row written → `decision` (same step, one command); card frozen →
`new-card`, plus `prediction` for a ladder's first card; valid result taken in → `brief`; critic
overruled → `critic-dissent`; recommendation and runner-up not separated → `close-call`; second
Convergence `RECAST` → `second-recast`; Root records a Portfolio proposal → `portfolio`. Read point:
every clean boundary, `item.py reviews`, apply, `mark-answered`.

**Board page (活跃方向).** A separate page: one row per direction, ACTIVE first, sorted by
priority then first-investment-wave rank then open items (other sorts: open count, recent
activity); columns wave rank, code and id, priority, open items with P1 count, last item age,
snapshot age, the Portfolio reason (two-line clamp, click to expand), links to `DIRECTION.md`, the
latest brief and the direction's inbox. PARKED rows sit below a divider. New endpoint `/api/active`.

**Priority in the inbox.** Items carry a grading priority computed server-side: P1 `portfolio`,
`second-recast`; P2 `new-card`, `critic-dissent`, `close-call`, direction-tier decisions; P3
delegated decisions and predictions; P4 briefs and `technical` decisions. The inbox groups by
these buckets and sorts by direction priority inside each.

**Redesign.** Metaphor: the flight-progress-strip bay of an air-traffic desk, which fits both the
grading task (rule quickly, in priority order) and the multi-UAV subject. Each item is one strip
with a coloured holder for its priority bucket; the selected strip unfolds into the grading form;
the rail filters by priority, kind and direction. Type: Bahnschrift SemiCondensed (the DIN family
of airport signage, shipped with Windows) for labels and codes, Segoe UI and Microsoft YaHei UI
for body, Cascadia Mono for ids and times; no web fonts, works offline. Palette: cool board grey
with white strips, deep teal for actions, vermilion/amber/steel/slate holders for P1–P4, green,
amber and slate dots for HIGH/MEDIUM/LOW directions; dark scheme follows the OS. Motion is limited
to the strip unfold and respects reduced-motion. Keyboard: `j/k`, `x`, `a`–`e`, `g`, `Enter`,
`Ctrl+Enter`, `]` for the evidence pane, which is closed by default so the bay has the width.

Verified visually afterwards through the Chrome DevTools plugin (inbox, expanded strip, board);
two defects found and fixed (option-key overlap, seeded titles and timestamps).

## 9. Revision 4 (08:35 PDT): the decision packet

Owner feedback: "这些较为高级的决策选项应该提供非常详细的上下文才可以，以如今的颗粒度我实际上无法做出
决策." The first real P1 item from Codex confirmed it: a 90-word context and a link to a
37 KB Pro response whose own sections (PORTFOLIO_EFFECTS, RATIFICATION_CHANGES, EVIDENCE,
UNCERTAINTY, OWNER_RATIFICATION_TEXT) never reached the card.

Contract change: any item the owner must rule on (`portfolio`, `second-recast`, `critic-dissent`,
`close-call`, `new-card`, and any direction- or portfolio-tier item) must carry a `packet`, in
Chinese, with `question`, `changes_if_approved` (target / from / to), `if_refused`, `evidence_for`
(path + quote + why), `evidence_against`, `uncertainty`, `cost` (compute, owner time,
reversibility, what waits on this), `verdict_text` verbatim, and `source`; every option needs a
non-empty `consequence`. `item.py add` refuses the item otherwise (`--packet <file.json>`). The
console renders the packet as sections above the options, opens `source` in the evidence pane
when a P1/P2 strip is clicked open, marks an incomplete item 上下文不足 with the missing fields
listed, and offers 要求补充决策包, which files a `needs-context` reply whose review instruction
tells the loop to re-file the item with a complete packet. Object-tier `decision` items are
exempt: the owner reviews them after the fact. Skill, README and tests (14) updated.
