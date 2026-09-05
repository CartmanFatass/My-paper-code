# Owner surfaces（所有者介入面）

这个目录是自动研究循环与所有者之间唯一的异步接口。循环只写条目、从不等待；所有者在批改台上批改，
批改结果生成 `reviews/<日期>.md`，循环在下一个干净边界读取并执行。控制决定：
`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`；规则文本在
`AGENTS.md` §4.5 和证据规范 §11.7。批改台：`python tools/owner_console/server.py`，然后打开
`http://127.0.0.1:8765/`。

## 当前维护范围（OWNER_DIRECT，2026-09-05）

所有者指令：「我们停止维护P2级别以下的问题 P3P4问题太多 我也审核不过来」。
此项覆盖下文及旧 insertion-point 规则中的 P3/P4 独立条目要求。
仅维护 P1/P2 批改项；P3 普通委托决定/预测、P4 技术项/简报停止新建、补写、催审，
历史项退出收件箱及待批计数，保留原文件和回复，不伪记为已审核。
`item.py add` 对 P3/P4 返回成功并输出 `skipped`，不创建文件、不分配 ID；审计直接引用
card/intake。`seed-ledger` 停止批量补建旧条目。既有 owner 指令仍须读取并执行。
科学卡片、预测记录、结果证据、intake、中文结果简报和必要审计照常保留；不再为这些
普通记录另建批改任务。真实的新卡、close-call、重大异议、方向决定和 Portfolio 提案
按原 P1/P2 分类处理，不为绕过限制而升级普通条目。
决定：[2026-09-05-owner-review-p2-cutoff.md](../decisions/2026-09-05-owner-review-p2-cutoff.md)。

## ★ 重要改动与 6 Pro 执行委托（当前边界）

完整裁决的执行委托及此前批准归因纠正见 [本次明确指令](../decisions/2026-09-05-pro6-delegation-and-starred-trace.md)。
方向/Portfolio 层级及重大异议、close-call、second-recast 新项自动星标；重要治理改动用既有 P1 项。
「★ 重要改动」显示全部历史星标项，包含已答项。星标不代表 owner 逐项批准。

执行时通过 CLI 追加记录，保留原回复与 status，不伪写 owner ratify：

```
python tools/owner_console/item.py trace <id> --authority "PRO_FINAL / OWNER_DELEGATED" --source <archived-response.md> --record <application-intake.md> --state applied --summary "实际变化与影响" --auto-applied <option-key>
```

`--state planned|applied|blocked`；仅已执行可填 `--auto-applied`。`--authority OWNER_DIRECT` 仅用于有明确 owner 指令的事项。application record 列出变化前后、修改文件和提交定位；`execution_history` 逐条追加时间、来源、状态与记录链接。`--correction` 用于保留原回复并明确纠正其授权归因，不冒充新回复。新 owner 回复仍按原流程生效。此记录不新增运行关卡。

## 所有者每天怎么用（约 15 分钟）

1. 打开批改台的收件箱。只有需要你看的条目会出现：已按委托执行的决定、新卡片、预测请求、简报、
   批评者异议、二次重铸、等待批准的 Portfolio 提案。
2. 每张卡片：看一眼推荐项（★）和已执行项（✓），同意就按 `g`；不同意就选另一项并写一句原因，
   `Ctrl+Enter` 提交。每次提交都会写入 reply 文件、重生成当天的 `reviews/<日期>.md` 并按 pathspec
   commit。推送由你手动按。
3. 右侧面板可以直接读证据文档、简报和账本行，不用离开页面。
4. 需要把一批批改交给 Pro 或 Codex 时，用"导出选中"生成一份单独的 md。

## Layout

```
owner/
  README.md              this file (schemas for agents; routine for the owner)
  inbox/<YYYY-MM-DD>/<id>.json         items written by the DM or Root
  inbox/<YYYY-MM-DD>/<id>.reply.json   the owner's reply, written by the console
  reviews/<YYYY-MM-DD>.md              regenerated from replies; THE FILE THE LOOP READS
  reviews/<YYYY-MM-DD>_<slug>.md       hand-picked exports
  briefs/<direction>/<YYYY-MM-DD>_<object>.md   one-page Chinese brief per valid result
```

## How the loop writes items (the stable contract)

Agents never write item JSON by hand. They call `tools/owner_console/item.py`, which validates the
fields, assigns the id and writes the file; `tests/tools/owner_console/` pins the schema, and the
skill `.agents/skills/hmasd-owner-item/SKILL.md` names every insertion point with the exact
command. The DM definition and the Portfolio skill reference that skill.

| Moment in the loop | kind |
| --- | --- |
| an object-tier decision is recorded in the audit ledger | `decision` (executed option in `auto_applied`) |
| a science card is frozen | `new-card` |
| a ladder's first card is frozen | `prediction` |
| a valid result is taken in and its brief written | `brief` |
| a critic's material dissent is overruled | `critic-dissent` |
| a recommendation and its runner-up were not clearly separated | `close-call` |
| Convergence returns a second `RECAST` | `second-recast` |
| Root records a Portfolio proposal or a DM returns a direction recommendation | `portfolio` |

```
python tools/owner_console/item.py add --direction <id> --kind <kind> --title "…" [--context "…"] \
  --option a "…" --option b "…" --recommended a [--auto-applied a] [--evidence <path>] …
python tools/owner_console/item.py reviews              # at every clean boundary
python tools/owner_console/item.py mark-answered <id>   # after applying an instruction
```

## Item schema (what `item.py add` writes)

One JSON file per item at `inbox/<YYYY-MM-DD>/<id>.json`, written at the moment the decision is
made or the card is frozen, next to the ledger row. `id` is `<YYYYMMDD>-<script prefix>-<nnn>`
(prefixes in `docs/research/RESEARCH_MAP.md`; Root uses `root`). The console assigns a grading
priority from `kind` and `tier`: P1 `portfolio`, `second-recast`; P2 `new-card`,
`critic-dissent`, `close-call`, direction-tier decisions; P3 delegated decisions and predictions;
P4 briefs and decisions whose `ledger_kind` is `technical`.

```json
{
  "id": "20260905-fsd-003",
  "created": "2026-09-05T03:12:00Z",
  "direction": "flexible_skill_duration",
  "tier": "object | direction | portfolio",
  "kind": "decision | new-card | prediction | brief | critic-dissent | close-call | second-recast | portfolio",
  "title": "one line",
  "context": "<= 200 words of markdown: what is being decided, why now, what the DM saw",
  "options": [
    {"key": "a", "label": "…", "consequence": "one line, optional"},
    {"key": "b", "label": "…", "consequence": "…"}
  ],
  "recommended": "a",
  "auto_applied": "a",
  "dm_reason": "one sentence",
  "evidence": ["docs/research/candidates/<direction>/<card or intake>.md"],
  "ledger_row": "docs/research/portfolio/audit/2026-09-05.md#L14",
  "brief": "docs/research/portfolio/owner/briefs/<direction>/2026-09-05_<object>.md",
  "status": "open"
}
```

Fields other than `id`, `direction`, `kind`, `title`, `options` are optional. `auto_applied` names
the option already executed under the standing delegation; omit it when nothing has run yet.
Options per kind:

| kind | options the DM writes | what a reply means |
| --- | --- | --- |
| `decision` | the object-tier options, one marked `recommended`; `auto_applied` = the one executed | `agree` or the same key: delegated decision stands; another key: override at the next clean boundary |
| `new-card` | `accept`, `reject`, `revise` | reject or revise carries the reason in the comment; launch is not blocked meanwhile |
| `prediction` | the competing mechanisms (two or three) | the owner's prediction; scored at intake; comment carries magnitude or `unclear` |
| `brief` | `reading-agreed`, `reading-disputed` | dispute with the comment |
| `critic-dissent`, `close-call` | the DM's options plus the critic's position as one option | as `decision` |
| `second-recast` | `continue-low-priority`, `park` | park is a Portfolio record; continue keeps lowest sequencing priority |
| `portfolio` | `ratify`, `refuse`, `amend` | ratification or refusal of a Portfolio proposal; amend with the comment |

Every item is also one ledger row (audit record) whose evidence path names the item file.

## Decision packet (P1/P2 items)

An item the owner must rule on (`portfolio`, `second-recast`, `critic-dissent`, `close-call`,
`new-card`, and any direction- or portfolio-tier item) carries a `packet` object, written in
Chinese, and every option has a non-empty `consequence`. `item.py add --packet <file.json>`
refuses the item otherwise; the console shows an incomplete one as 上下文不足 and the owner's
reply `needs-context` sends it back to be re-filed. Fields:

| field | content |
| --- | --- |
| `question` | one sentence: what the owner is deciding |
| `changes_if_approved` | list of `{target, from, to}` (what changes where), or the string `none` |
| `if_refused` | what the loop does instead, what stays unchanged |
| `evidence_for` | list of `{path, quote (≤2 sentences), why}` supporting the recommendation |
| `evidence_against` | same shape, the strongest cautionary evidence (may be empty) |
| `uncertainty` | list of open points or revisit triggers |
| `cost` | `{compute, owner_time, reversibility: reversible\|costly\|irreversible, waits_on_this}` |
| `verdict_text` | the Pro verdict or DM recommendation, verbatim |
| `source` | the Pro response, intake or card the packet was drawn from |

The console renders the packet as sections above the options and opens `source` in the evidence
pane when a P1/P2 strip is expanded. An object-tier `decision` needs no packet: the owner reviews
it after the fact, and the context paragraph plus the intake link suffice.

## Review document (the loop reads this)

`reviews/<YYYY-MM-DD>.md` is regenerated by the console from every reply answered that day. One
section per item with `owner:` (the chosen option), `comment:`, and one `instruction:` line. At
every clean boundary the DM and Root read today's and yesterday's review files, apply each
`instruction` that differs from what already ran, mark the item's `status` as `answered` in the
item file, and cite the review line in the ledger. `agree` means seen; nothing changes.

```markdown
## 20260905-fsd-003 · flexible_skill_duration · decision · E3 之后的下一 rung
- recommended: (a) · auto-applied: (a) · **owner: (b) E4：随机时长事件**
- comment: 先看 E4。
- instruction: apply (b) at the next clean boundary; supersede the delegated (a)
```

## Briefs

One page in Chinese, under 600 characters, six fixed headings, written by the DM at every
valid-result intake beside the English intake document, and referenced from a `brief` item:

```markdown
# <direction> · <object> · <date>
## 问题
## 机制与比较器
## 结果一句话
## 预测核对
## 排除了什么
## 下一步与需要你做的
```

Plain language, no commit sha, no field names; the English intake document carries those.

## Guarantees

The loop never waits for a reply. A missing console changes nothing: the owner can write a
`.reply.json` by hand and run `python tools/owner_console/server.py render-review <date>`. Nothing
here changes a frozen scientific object or a live run's comparator, budget, RNG or claim meaning.
