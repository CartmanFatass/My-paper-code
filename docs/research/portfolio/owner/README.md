# Owner surfaces（所有者介入面）

这个目录是自动研究循环与所有者之间唯一的异步接口。循环只写条目、从不等待；所有者在批改台上批改，
批改结果生成 `reviews/<日期>.md`，循环在下一个干净边界读取并执行。控制决定：
`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`；规则文本在
`AGENTS.md` §4.5 和证据规范 §11.7。批改台：`python tools/owner_console/server.py`，然后打开
`http://127.0.0.1:8765/`。

## 当前维护范围

仅维护 P1/P2 批改项。普通委托决定、预测、技术项和简报保存在科学记录中，
不另建、补写或催审 P3/P4 批改项。已有文件和回复保留，待批计数只含 P1/P2。
`item.py add` 对 P3/P4 返回成功并输出 `skipped`，不创建文件、不分配 ID；审计直接引用
card/intake。`seed-ledger` 停止批量补建旧条目。既有 owner 指令仍须读取并执行。
科学卡片、预测记录、结果证据、intake、中文结果简报和必要审计照常保留；不再为这些
普通记录另建批改任务。真实的新卡、close-call、重大异议、方向决定和 Portfolio 提案
按原 P1/P2 分类处理，不为绕过限制而升级普通条目。
决定：[2026-09-05-owner-review-p2-cutoff.md](../decisions/2026-09-05-owner-review-p2-cutoff.md)。

## ★ 重要改动与当前权责

DM 负责创新、实验、工程修复、证据解释和报告，在当前方向范围内自主推进普通研究。
方向 Pro Convergence 负责独立 review；DM 回应意见。Portfolio 按
`docs/project/PORTFOLIO_DECISION_PROTOCOL.md` 总览全局，最终解释并决定方向级
CONTINUE/RECAST/PARK/CLOSE/重开。完整合规决定由 DM 执行，不等待 Root 或用户逐项批准；
普通实验不逐项提交 Portfolio。DM 的建议或待回复状态不能写为已 PARK、已关闭或已释放席位。

Clerk 已退役。平行 DM 按 `PEER_DM_COORDINATION.md` 直接协调并记录交接，实际空槽按当前
三个占用加预留席位的目标处理，已有请求和预留不得重复创建。Web Portfolio 必须收到固定版本的
完整相关上下文并说明实际访问情况。历史 PRO_FINAL 与批改项保留出处；星标便于用户异步介入。

对已执行的 Portfolio 决定，记录真实来源和应用状态，例如：

```powershell
python tools/owner_console/item.py trace <id> --authority "PRO_FINAL / OWNER_DELEGATED" --source <portfolio-response.md> --record <dm-intake.md> --state applied --summary "实际变化与影响" --auto-applied <option-key>
```

共享治理改动记录真实 OWNER_DIRECT 来源。planned/applied/blocked 描述实际应用状态；不能把待建议项
写成已经执行。用户的新明确指令仍在对应干净边界生效，不追溯改写已有结果或自动创建重跑。

## 所有者每天怎么用（约 15 分钟）

1. 打开批改台的收件箱，查看新卡片、方向决定、重大异议、close-call、二次重铸和 Portfolio 提案。
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
fields and writes an ID/file for P1/P2; P3/P4 returns `skipped` with neither. `tests/tools/owner_console/` pins the schema, and the
skill `.agents/skills/hmasd-owner-item/SKILL.md` names every insertion point with the exact
command. The DM definition and the Portfolio skill reference that skill.

| Moment in the loop | kind |
| --- | --- |
| a direction- or portfolio-tier decision is recorded | `decision` with explicit tier and packet (executed option in `auto_applied`) |
| a science card is frozen | `new-card` |
| a critic's material dissent is overruled | `critic-dissent` |
| a recommendation and its runner-up were not clearly separated | `close-call` |
| DM records a second `RECAST` | `second-recast` |
| Portfolio records a proposal or a DM returns a direction recommendation | `portfolio` |

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
`critic-dissent`, `close-call`, direction- and portfolio-tier `decision` items.

```json
{
  "id": "20260905-fsd-003",
  "created": "2026-09-05T03:12:00Z",
  "direction": "flexible_skill_duration",
  "tier": "object | direction | portfolio",
  "kind": "decision | new-card | critic-dissent | close-call | second-recast | portfolio",
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
| `decision` | direction/portfolio options, one marked `recommended`; `auto_applied` = the one executed | the owner's selected option applies at the next clean boundary |
| `new-card` | `accept`, `reject`, `revise` | reject or revise carries the reason in the comment; launch is not blocked meanwhile |
| `critic-dissent`, `close-call` | the DM's options plus the critic's position as one option | as `decision` |
| `second-recast` | `continue-low-priority`, `park` | park is a Portfolio record; continue keeps lowest sequencing priority |
| `portfolio` | `keep`, `refuse`, `amend` | keep acknowledges the formed Pro disposition; refuse/amend overrides at the next clean boundary, preserving executed effects and history |

Created items can be cited by their ledger row. Ordinary audit records cite the card/intake;
a `skipped` result supplies no item path.

## Decision packet (P1/P2 items)

An item requiring a P1/P2 review packet (`portfolio`, `second-recast`, `critic-dissent`, `close-call`,
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
pane when a P1/P2 strip is expanded. Ordinary object-tier decisions stay in their intake/audit.

## Review document (the loop reads this)

`reviews/<YYYY-MM-DD>.md` is regenerated by the console from every reply answered that day. One
section per item with `owner:` (the chosen option), `comment:`, and one `instruction:` line. At
every clean boundary the DM and Root query `python tools/owner_console/item.py reviews` for all
unapplied instructions across dates, apply each instruction that differs from what already ran,
and use `mark-answered` after application. The dated review file supplies the original instruction
and review-line citation for the ledger; its date does not limit the pending query. `agree` means
seen; nothing changes.

```markdown
## 20260905-fsd-003 · flexible_skill_duration · decision · E3 之后的下一 rung
- recommended: (a) · auto-applied: (a) · **owner: (b) E4：随机时长事件**
- comment: 先看 E4。
- instruction: apply (b) at the next clean boundary; supersede the delegated (a)
```

## Briefs

One page in Chinese, under 600 characters, six fixed headings, written by the DM at every
valid-result intake beside and linked from the English intake document:

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
