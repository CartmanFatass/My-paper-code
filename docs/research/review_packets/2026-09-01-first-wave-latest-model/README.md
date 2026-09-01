# HMASD 第一投资波：最新模型独立审阅包

本包用于独立审阅当前五个 `ACTIVE/HIGH` 方向：FRRIE、VNFC、CBSC、SCDMP、UCOPE。
它整理科学动因、最强替代解释、现有证据、真正难点、下一判别对象，以及两套曾使用的
本地文献源。它不替代各方向的 persistent Pro 决策，也不直接改变 Portfolio lifecycle。

## 快照与优先级

- 仓库快照：`b4d738537c2a3e098e141770ecf716d51321c3b3`，当时与 `origin/main` 一致。
- 当前工作树仍包含 CBSC、FRRIE 与控制面未提交 WIP；不得把 GitHub 版本误当成完整本地状态。
- 当前状态以
  [`FIRST_INVESTMENT_WAVE_USAGE_SAFE_STOP_HANDOFF_20260901.md`](../../portfolio/FIRST_INVESTMENT_WAVE_USAGE_SAFE_STOP_HANDOFF_20260901.md)
  的 `1% pre-stop delta` 和其后的 UCOPE retained-audit 记录为最晚事实。
- `DIRECTION.md` 解释方向科学对象；若与上述 handoff 的更晚工程事实冲突，以 handoff 为准，
  但 handoff 不拥有 lifecycle 修改权。

## 建议读取顺序

1. [`REVIEW_PROMPT.md`](REVIEW_PROMPT.md)：可直接交给新模型的任务正文。
2. [`DIRECTIONS.md`](DIRECTIONS.md)：五方向动因、难点、当前证据与审阅问题。
3. [`SOURCE_MANIFEST.json`](SOURCE_MANIFEST.json)：机器可读的权威路径与可见性边界。
4. [`literature/README.md`](literature/README.md)：两套文献库的实际状态和取证顺序。
5. [`literature/DIRECTION_MAP.md`](literature/DIRECTION_MAP.md)：文献到方向的人工映射。
6. [`literature/selected_references.jsonl`](literature/selected_references.jsonl)：便于模型检索的精选条目。

## 证据解释规则

- 用最小足够证据类回答问题。当前五方向主要是 `A/RECON` 或 `B/EXPLORE`；不要要求一般
  MARL 收敛定理才允许 toy/benchmark 学习实验。
- 工程失败没有科学极性。有效负结果只更新最小对象，不自动关闭整个方向。
- 文献提供动因、机制、控制或反例边界，不替代 HMASD 的直接实验。
- `docs/new-libs/corpus` 的 `curator_connection` 是项目假设，不是来源论文结论。
- InstSci 的 Metadata v2/摘要只用于召回；方法、公式、实验和局限应回到结构化 JSON，必要时核对 PDF。

## 本包不包含

- 不复制 PDF、结构化全文或外部浏览器状态。
- 不包含 ChatGPT Pro transport 请求，也没有发送任何新审阅。
- 不为五方向预先选择 `CONTINUE/PARK/CLOSE/RECAST`；审阅模型必须从证据给出理由。
