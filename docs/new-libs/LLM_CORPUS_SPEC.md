# LLM corpus specification for `docs/new-libs`

## Purpose

Transform the 27 locally retained MARL books and papers into a navigable,
page-traceable corpus for LLM retrieval and research synthesis. The corpus is a
derived access layer. The source PDFs and `LIBRARY_INDEX.md` remain authoritative
for bibliographic identity and source content.

## Non-negotiable fidelity rules

1. Every extracted passage has a stable paper ID and PDF-page span.
2. Source text, author claims, and curator inference are never merged. A claim
   record uses exactly one of `source_claim`, `source_scope`,
   `curator_boundary`, or `curator_connection`.
3. Do not silently repair equations, symbols, tables, references, or reading
   order. Mark unreliable extraction as `equation_text_unreliable`,
   `table_text_unreliable`, `multi_column_order_uncertain`, or
   `scan_or_font_issue` and route the reader to the source page.
4. Preserve material section headings, theorem/proposition/lemma labels,
   figure/table numbers, footnotes when extractable, sample sizes, experimental
   regimes, and stated assumptions.
5. A paper's abstract or conclusion is evidence of what its authors claim, not
   independent proof. Overviews must describe the evidence type.
6. Do not turn separate fixed-`N` experiments into held-out-`N` generalization,
   graphon/mean-field approximation into a generic learned-policy guarantee, or
   fixed episodes/delays into variable skill period `k`.
7. No project result or other HMASD direction is evidence for a paper. HMASD
   links are explicitly labeled prospective curator connections.

## Stable directory layout

```text
docs/new-libs/corpus/
  README.md
  catalog.json
  catalog.jsonl
  search_index.jsonl
  claim_index.jsonl
  NAV_BY_TOPIC.md
  NAV_BY_METHOD.md
  NAV_BY_THEOREM_AND_EVIDENCE.md
  NAV_BY_HMASD_AXIS.md
  READING_PATHS.md
  GLOSSARY.md
  qa/
    COVERAGE.md
    EXTRACTION_WARNINGS.md
    VISUAL_QA.md
  papers/
    <ID>/
      metadata.json
      overview.md
      structure.json
      claims.jsonl
      chunks.jsonl
      chunks/
        <ID>-C0001.md
        ...
  _partials/
    agent_a_catalog.jsonl
    agent_a_search.jsonl
    agent_a_claims.jsonl
    agent_a_topics.json
    agent_a_qa.md
    agent_b_catalog.jsonl
    agent_b_search.jsonl
    agent_b_claims.jsonl
    agent_b_topics.json
    agent_b_qa.md
```

Subagents own only their assigned `papers/<ID>/` directories and their named
`_partials/agent_*` files. Root owns every merged/global navigator.

## Per-paper metadata

`metadata.json` contains:

- `paper_id`, `citation_key`, `title`, `authors`, `year`, `venue`, `version`;
- `source_pdf` as a repository-relative path;
- `pdf_pages`, `text_extractable_pages`, `warning_pages`;
- `doi`, `arxiv`, and source URLs only when already verified in the library;
- `primary_topics`, `method_families`, `problem_classes`, `evidence_types`;
- `hmasd_axes` drawn from `variable_N`, `variable_k`, `communication`,
  `credit`, `optimization`, `planning`, or `foundations`;
- `corpus_paths`, `chunk_count`, and a stable `content_fingerprint` of the
  source PDF for local change detection.

## Per-paper overview

`overview.md` is concise but substantive and uses these headings:

1. `Identity and scope`
2. `Problem formulation`
3. `Actual contribution`
4. `Core objects and equations`
5. `Algorithms or mechanism primitives`
6. `Assumptions and information structure`
7. `Theorems and guarantees`
8. `Experiments and evaluation protocol`
9. `Failure boundaries and non-claims`
10. `HMASD prospective connections`
11. `Recommended reading route`
12. `Source-page anchors`

The overview may paraphrase. It does not contain long verbatim reproduction.
Every substantive row includes a PDF-page locator.

## Page-aligned chunks

- Use PDF pages, not inferred printed page numbers, as the stable locator.
- Target 1,200-3,000 extracted words per chunk and no more than six PDF pages.
- Prefer section boundaries; never combine noncontiguous pages.
- Put a `[PDF page N]` marker before each page's extracted text.
- Preserve the source language and basic paragraph structure.
- Each chunk begins with YAML keys:

```yaml
chunk_id: P14-C0001
paper_id: P14
source_pdf: docs/new-libs/papers/P14_....pdf
pdf_pages: [1, 2, 3]
section_path: [Introduction]
content_types: [abstract, motivation]
extraction_warnings: []
```

`chunks.jsonl` and the global `search_index.jsonl` store one metadata record per
chunk with `chunk_id`, `paper_id`, `path`, `pdf_pages`, `section_path`,
`content_types`, `keywords`, `summary`, `word_count`, and warnings. The search
index does not duplicate full chunk text.

## Claim index

Each `claims.jsonl` row contains:

- `claim_id`, `paper_id`, `claim_kind`, `statement`, `pdf_pages`;
- `section`, `evidence_type`, `conditions`, `limits`;
- `topics`, `hmasd_axes`, and `related_chunk_ids`.

Formal results must retain their theorem/proposition label and assumptions.
Empirical rows retain task, roster size, train/test protocol, sample size when
reported, comparator, metric, and whether one frozen policy crosses `N` or `k`.
Absence/boundary rows are bounded to the inspected work.

## Global navigation

Root merges both partials and creates:

- topic routes (`mean field`, `graphon`, `information bottleneck`,
  `Dec-POMDP`, `potential games`, `variational inequalities`, `exploration`,
  `sample complexity`, `optimal transport`);
- method routes (Q-learning, policy gradient/NPG, PPO/TRPO, model-based,
  mirror/extragradient, latent-variable, communication compression);
- theorem/evidence routes separating formal guarantees, empirical support,
  conceptual proposals, textbooks, and recent unreviewed preprints;
- HMASD routes for variable `N`, variable `k`, information/communication,
  learning dynamics, and UAV-transfer ingredients;
- reading paths from foundations to specialized papers, with prerequisites and
  explicit “do not infer” boundaries.

Every navigation link points to an overview, claim row, or chunk path. No bare
paper title without a destination.

## Extraction and visual QA

- Use `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` and `pypdf` for
  deterministic page extraction.
- Use `pdfinfo` for page-count reconciliation.
- Render at least one representative content page per paper with `pdftoppm`;
  prioritize a theorem/equation/table or dense two-column page. Inspect that
  page against extracted order and record the result in the agent QA partial.
- Temporary renders belong under `tmp/pdfs/new_libs_corpus/`; final navigation
  never links to those PNGs.
- The merged acceptance requires 27/27 PDFs, no duplicate paper IDs or chunk
  IDs, valid JSON/JSONL, existing links, monotonically ordered nonoverlapping
  chunk spans, and explicit warnings for unreadable material.

## Copyright and research-use boundary

This is a local research-access derivative of user-supplied files. Overviews and
claim maps are preferred for normal LLM use. Page chunks remain local, preserve
source identity, and are not a redistributable replacement for the books or
papers. Do not commit or publish the source PDFs unless the user separately
authorizes that action and licensing permits it.
