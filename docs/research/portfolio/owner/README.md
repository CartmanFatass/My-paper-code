# Owner surfaces（所有者介入面）

这个目录是自动研究循环与所有者之间唯一的异步接口。循环只追加、从不等待；所有者只在需要时填一个
`owner` 单元格，循环在下一个干净边界执行。控制决定：
`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`；规则文本在
`AGENTS.md` §4.5 和证据规范 §11.7。

## 所有者每天怎么用（约 15 分钟）

1. 打开今天的 `digest/<YYYY-MM-DD>.md`。只有需要你看的行会出现在这里：新卡片、被标记的账本行、
   新简报、等待批准的 Portfolio 提案。
2. 不同意的行，在 `owner` 单元格里写一句指令（例如 `PARK`、`reject: 不是 MARL 结构`、
   `use option (b)`）。空着表示同意。
3. 有空时在 `PREDICTIONS.md` 里填几句预测。没填也不影响发射。
4. 每周读 `briefs/` 下头部方向的简报，处理 digest 里累积的 `portfolio` 行。

## Surfaces and row schemas (agents write these)

### `digest/<YYYY-MM-DD>.md`

Append-only, created by the first agent that writes a row that day. Header:

```markdown
# Owner digest — <YYYY-MM-DD>

Rows are appended by DMs and Root. The owner replies in the `owner` cell; a filled cell is an
instruction applied at the next clean boundary.

| time | direction | kind | summary | path | owner |
| --- | --- | --- | --- | --- | --- |
```

`kind` is one of:

- `new-card`: summary = the card's one-sentence claim and its binding MARL structure.
- `close-call`, `critic-dissent`, `second-recast`, `portfolio`: summary = the ledger row's chosen
  option and why it was flagged; path = the ledger row's evidence path.
- `brief`: summary = the brief's 结果一句话; path = the brief.
- `prediction-open`: summary = the ladder whose prediction cell is still empty; path =
  `PREDICTIONS.md`.

### `PREDICTIONS.md`

One row per ladder, appended when the ladder's first card is frozen. Launch never waits.

### `briefs/<direction>/<YYYY-MM-DD>_<object>.md`

One page in Chinese, under 600 characters, six fixed headings:

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

## What the loop reads back

At every clean boundary the DM and Root read the `owner` column of the audit ledger, the `owner`
cells of every digest file, and the owner cells of `PREDICTIONS.md`. A filled cell is an owner
instruction and overrides the delegated decision it points at. Nothing here changes a frozen
scientific object or a live run's comparator, budget, RNG or claim meaning.
