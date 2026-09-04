# 文献目录与读取边界

本目录只建立索引，不复制论文。当前审阅使用两个用户指定的文献根。

## 1. HMASD `docs/new-libs`

绝对路径：`C:/Projects/HMASD/docs/new-libs`

这是 27 个 verified works 的 committed、page-traceable corpus。推荐入口：

1. `docs/new-libs/LIBRARY_INDEX.md`：版本、来源、边界与本地 PDF 历史说明；
2. `docs/new-libs/corpus/NAV_BY_HMASD_AXIS.md`：variable `N`、variable `k`、communication、
   optimization 等轴；
3. `docs/new-libs/corpus/claim_index.jsonl`：typed claims、conditions、limits、PDF pages；
4. `docs/new-libs/corpus/papers/<ID>/overview.md`；
5. `docs/new-libs/corpus/papers/<ID>/claims.jsonl` 与 `chunks.jsonl`。

`docs/new-libs/README.md` 历史上记录 27 个约 49 MiB 的 local-only PDF，但本快照实际
`docs/new-libs/papers/*.pdf` 数量为 **0**。因此 GitHub/当前工作区可用的是 committed corpus、
overview、claims、chunks、BibTeX 和 source links；不要声称原 PDF 当前可读。遇到 equation/table
warning 时应通过 `LIBRARY_INDEX.md` 的官方链接另行核对。

检索命令：

```powershell
$env:PYTHONIOENCODING='utf-8'
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  docs/new-libs/corpus/tools/search_corpus.py `
  'query' --kind claims --limit 20 --json
```

`source_claim/source_scope` 可作为来源陈述；`curator_connection` 只是 HMASD construction idea；
`curator_boundary` 只限定本次已核对 source 的非结论，不能证明全球文献空白。

## 2. InstSci 正式 MyLib

绝对路径：`C:/Projects/Inst-sci/papers/MyLib`

`metadata/integrity.json` 在本快照记录：

- PDF：190 / 190；
- structured JSON：190 / 190；
- metadata records：190 / 190；
- missing JSON：0；
- Metadata v2：validated，190 records；
- official exact-title matches：184；
- quality grade A/B：184 / 6；
- DOI coverage：126 / 190。

模型读取顺序：

1. `metadata/integrity.json`；
2. `llm-index/catalog.v2.jsonl` 做标题/摘要/算法/keyword recall；
3. `metadata/v2/papers.v2.jsonl` 检查质量与逐字段 provenance；
4. `json/<paper-id>.json` 核对方法、公式、实验、局限和页面元素；
5. 必要时才读 `pdf/<paper-id>.pdf`。

Metadata v2 的 `research` 字段主要是摘要级语义，不等于全文验证。实质性判断必须记录
paper ID、JSON/PDF path 和证据层。InstSci 正式库位于 HMASD 仓库之外，GitHub connector
看不到；本机模型可按绝对路径读取。

## 3. Cross-cutting empirical methodology

HMASD 的 empirical evidence spec 还显式引用以下公开来源，当前两套本地目录未必收录全文：

- MADDPG — arXiv `1706.02275`；
- QMIX — PMLR v80；
- MAPPO — arXiv `2103.01955`；
- Henderson et al., *Deep Reinforcement Learning That Matters*；
- Agarwal et al., *Deep RL at the Edge of the Statistical Precipice*；
- Gorsane et al., cooperative MARL evaluation protocol, NeurIPS 2022。

它们支持 bounded empirical reporting 与 uncertainty discipline，不要求所有早期 MARL 方向先
获得一般 convergence theorem。

## 4. SCDMP legacy physics references

以下四篇曾被 SCDMP science cards 直接引用，但不在当前 InstSci 190-paper catalog 中：

- Sreenath & Kumar, RSS 2013, *Dynamics, Control and Planning for Cooperative Manipulation of
  Payloads Suspended by Cables from Multiple Quadrotor Robots* —
  `https://www.roboticsproceedings.org/rss09/p11.pdf`；
- Han et al., IEEE Access 2022 — DOI `10.1109/ACCESS.2022.3222031`；
- Liang et al., Aerospace Science and Technology 2021 — DOI `10.1016/j.ast.2021.107139`；
- Omran et al., Automatica 2016 — DOI `10.1016/j.automatica.2016.02.013`。

这些来源只支持 broad payload dynamics、failure/control 与 sample-and-hold ingredients；它们不
验证 HMASD 的具体 event map、action catalogue、系数或 learned result。

## 5. 审阅可见性

| Source | GitHub connector | 本机模型 | 内容层级 |
| --- | --- | --- | --- |
| `docs/new-libs` committed corpus | 可见 | 可见 | curated index + page-aligned chunks |
| `docs/new-libs/papers` | 当前无文件 | 当前无文件 | historical local PDFs absent |
| InstSci Metadata/JSON/PDF | 不可见 | 可见 | 190-paper formal local library |
| 本包 | 可见 | 可见 | 路由、摘要和精选映射 |
