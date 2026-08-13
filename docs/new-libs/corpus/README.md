# MARL source corpus for LLM use

This directory is the navigable, page-traceable access layer for the 27 books
and papers retained under `docs/new-libs/papers/`. It is designed for two modes:

- **Route first:** use a navigator or claim index to find the right source and
  the right evidentiary boundary.
- **Read deeply:** open a paper overview, then follow its claim or section link
  to page-aligned chunks and finally to the source PDF when layout matters.

The original PDFs and [`LIBRARY_INDEX.md`](../LIBRARY_INDEX.md) remain the
authority. Corpus summaries are curator-authored access aids, not substitutes
for source text or proof.

## Best entry point by question

| Question | Start here |
|---|---|
| What does the corpus contain? | [`catalog.json`](catalog.json) or [`qa/COVERAGE.md`](qa/COVERAGE.md) |
| Which paper addresses my topic? | [`NAV_BY_TOPIC.md`](NAV_BY_TOPIC.md) |
| Which algorithms or learning methods are represented? | [`NAV_BY_METHOD.md`](NAV_BY_METHOD.md) |
| Which statements are theorems, experiments, surveys, or proposals? | [`NAV_BY_THEOREM_AND_EVIDENCE.md`](NAV_BY_THEOREM_AND_EVIDENCE.md) |
| What supports variable `N`, variable `k`, communication, or optimization? | [`NAV_BY_HMASD_AXIS.md`](NAV_BY_HMASD_AXIS.md) |
| What should I read, and in what order? | [`READING_PATHS.md`](READING_PATHS.md) |
| What does a term mean across subfields? | [`GLOSSARY.md`](GLOSSARY.md) |
| Search chunks programmatically | [`search_index.jsonl`](search_index.jsonl) |
| Search claims, assumptions, and boundaries | [`claim_index.jsonl`](claim_index.jsonl) |
| Run compact local retrieval | [`LLM_USAGE.md`](LLM_USAGE.md) |
| Check extraction limitations | [`qa/EXTRACTION_WARNINGS.md`](qa/EXTRACTION_WARNINGS.md) and [`qa/VISUAL_QA.md`](qa/VISUAL_QA.md) |

## Per-paper layout

Each `papers/<ID>/` directory contains:

- `metadata.json`: bibliographic identity, topics, methods, evidence types,
  HMASD axes, source path, and content fingerprint;
- `overview.md`: a compact research-oriented reading guide with PDF-page
  anchors;
- `structure.json`: section/page map;
- `claims.jsonl`: source claims, source scope, curator boundaries, and
  prospective HMASD connections kept as distinct record types;
- `chunks.jsonl`: the searchable metadata for page-aligned chunks; and
- `chunks/<ID>-C####.md`: source-language extracted text with explicit
  `[PDF page N]` markers and extraction warnings.

Use the overview for orientation. Use claim rows for precise retrieval. Use
chunks only when the actual surrounding source text is needed.

## Retrieval contract for an LLM

1. Identify the intended object: theorem, algorithm, empirical result,
   information structure, limitation, or project connection.
2. Filter `claim_index.jsonl` by `topics`, `hmasd_axes`, `evidence_type`, and
   `claim_kind`.
3. Read the linked overview and related chunk IDs.
4. Preserve the claim's `conditions` and `limits` in any synthesis.
5. If a chunk carries a layout/equation/table warning, inspect the cited source
   PDF pages before using exact notation or values.
6. Cite the source paper and PDF page, not this corpus as if it were the paper.

Recommended distinction:

- `source_claim`: what the work asserts or establishes;
- `source_scope`: the model, protocol, or population actually studied;
- `curator_boundary`: a bounded warning against a stronger inference; and
- `curator_connection`: a prospective HMASD use, not evidence that the use
  already works.

## Machine-readable indexes

All JSONL files contain one UTF-8 JSON object per line and use globally unique,
stable IDs.

- `catalog.jsonl`: one paper per row.
- `search_index.jsonl`: one page-aligned chunk per row; full text stays in the
  linked Markdown chunk.
- `claim_index.jsonl`: one claim/scope/boundary/connection per row.
- `navigation_facets.json`: normalized paper-ID groupings by topic, method,
  evidence type, and HMASD axis.

The deterministic builder and validator is
[`tools/build_corpus_indexes.py`](tools/build_corpus_indexes.py). It rejects
missing papers, malformed JSONL, duplicate IDs, bad links, invalid or overlapping
page spans, source page-count mismatches, and chunks without page markers.

## Known interpretation traps

- Parameter count independent of `N` is not learned held-out-`N`
  generalization.
- Mean-field and graphon rates apply to their stated model classes and
  assumptions; rates for uncontrolled particle systems are not policy-return
  guarantees.
- Separate experiments at several roster sizes are not necessarily one frozen
  policy crossing roster sizes.
- A determinant-of-covariance entropy bound for one message distribution is not
  conditional novelty or duplicate detection.
- A latent fixed for an episode, a communication delay, and a two-timescale
  optimizer are not variable skill period `k`.
- A conceptual position paper supplies mechanism inspiration, not empirical or
  theorem-level validation.

## Maintenance and copyright boundary

See [`../LLM_CORPUS_SPEC.md`](../LLM_CORPUS_SPEC.md) for the full schema and QA
rules. This local derivative is for research retrieval over user-supplied source
files. The source PDFs are not copied into the corpus, and the extracted chunks
must not be published as a replacement for the works. Licensing restrictions
recorded in the library index continue to apply.
