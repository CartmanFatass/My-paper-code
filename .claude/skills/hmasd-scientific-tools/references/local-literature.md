# Local literature for DM decisions

OWNER_DIRECT 2026-09-06: use the existing libraries when a concrete research question
needs evidence. This is question-driven retrieval, not a new mandatory reading list.

## When to retrieve

Retrieve when designing or recasting a mechanism, selecting a comparator, examining
an unexpected result, or assessing related-work overlap. State the question first.
Reuse relevant evidence already checked in the current NOTES.md unless the question,
source version or required coverage changed. Ordinary engineering implementation does not trigger
a fresh search. Historical research and every cited paper are not startup reading.

## Existing entry points

Check these stores, the July record and external-review rounds before calling an idea new.
Do not partition questions by library name. Counts and access may change; inspect the actual
index and authoritative integrity metadata rather than assuming that old counts are current.
The following paths are on the WSL authoring host, not relative to a worktree or compute node.
On another host use its configured equivalent and state any concrete coverage/access gap.

- `docs/new-libs/` (this repository): 27 verified foundations works (MARL foundations, Dec-POMDP,
  mean-field, potential games, VI dynamics). Entry `docs/new-libs/LIBRARY_INDEX.md`; machine indexes
  under `docs/new-libs/corpus/` (`catalog.jsonl`, `claim_index.jsonl`, `NAV_BY_*.md`,
  `tools/search_corpus.py`).
- Inst-sci formal library `/home/fires/projects/Inst-sci/papers/MyLib/` (WSL host): 190 MARL papers as
  `pdf/<id>.pdf` + structured `json/<id>.json` + `assets/`. `metadata/integrity.json` is authoritative
  for counts. Retrieval order per `llm-index/INSTRUCTIONS.md`:
  `llm-index/catalog.v2.jsonl` (title, abstract, algorithm_names, method_family, marl_setting,
  benchmarks, keywords) or `titles.tsv` with `rg` → `json/<id>.json` → the PDF only for verification.
  Owner-requested full-text reading notes are in `metadata/deep-readings/<id>.json`, indexed by
  `llm-index/deep-reading-index.jsonl` and `DEEP_READING_INDEX.md`; inspect actual coverage,
  source versions/pages and DIRECT versus INFERENCE, not just a completion label.
- My-lib corpus `/mnt/c/Projects/My-lib/` (Windows `C:\Projects\My-lib`; its tracked project is a
  read-only mechanism sidecar with its own `AGENTS.md` — do not edit it from here): Phase-0
  title-screened RL/MARL arXiv preprints of ICLR/ICML/NeurIPS 2023–2025 main tracks, 1,519 PDFs under
  `.local-formal-capture/corpus/papers/<venue-year>/<official_id>/arxiv-<id>.pdf` (arXiv copies, not
  camera-ready). Official rosters `.local-formal-capture/rosters/<venue-year>.json`; title/abstract
  records `.local-formal-capture/.local-acquisition/downloads/four-year-arxiv-matches.json`. The
  project's own SQLite indexes (`.local-index`, `.local-page-index`, `.local-semantic-index`) hold 2
  mechanism rows and no pages: not corpus coverage. The LLM index (rebuildable, git-ignored)
  lives in `.local-llm-index/`: `catalog.jsonl` / `titles.tsv` (one row per PDF), `hints.jsonl` and
  `hints/<id>.json` (Gemini 3.8 Flash, medium thinking: problem, method, key mechanism, keywords,
  MARL setting, topics, relevance 0–3 to hierarchical MARL / UAV cooperative planning, one-line
  hint), `INDEX_BY_TOPIC.md`, `INDEX_BY_RELEVANCE.md`, `README.md` (model, prompt version, build
  date, counts, cost). Search: `python3 tools/reference_libraries/search_mylib.py <term> [<term>…]`
  from this checkout; rebuild with `tools/reference_libraries/build_mylib_llm_index.py`. Hints locate
  papers; they are not evidence and carry no novelty verdict. Owner-requested Astra Max reading
  notes live separately in `.local-llm-index/deep-readings/<id>.json`, with prior-reading evidence,
  actual coverage and source hashes in `deep-reading-index.jsonl` / `DEEP_READING_INDEX.md`.

A missing local path is an access gap, not an empty scientific literature. Do not install a new
index/service or download pipeline as a prerequisite to ordinary research. This retrieval method
does not itself require the Inst-sci acquisition skill or authorise acquisition.

## Evidence and handoff

Indexes, title/abstract tags and mechanism matches identify candidates; they do not
establish novelty, fair comparison or a scientific result. Confirm material claims
in the source, retaining assumptions, setting, limits and page/section references.
Distinguish the paper's finding from the DM's inference about HMASD. A local miss means
no match in the searched snapshot, not absence of prior work. Extend to official
external sources for a specific gap or freshness need, rather than forcing local coverage.

Record the paper identity/version, source JSON/PDF path and page/section, bounded claim,
and which current choice it informs in the existing NOTES.md entry or claim note. An implementation delegate receives only
the relevant algorithm, equation or passage needed for its deliverable, with a precise
pointer or excerpt if the source is inaccessible. Do not attach the whole paper set,
repeat the research history, or create a separate literature report by default.
