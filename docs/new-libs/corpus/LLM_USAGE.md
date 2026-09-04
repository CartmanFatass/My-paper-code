# LLM retrieval recipes

## Minimal retrieval loop

1. Search paper/claim/chunk metadata rather than opening all source text.
2. Read the selected paper's `overview.md`.
3. Follow `related_chunk_ids` or the returned chunk path.
4. Preserve `conditions`, `limits`, and PDF page locators in the answer.
5. Inspect the original PDF page whenever an extraction warning affects the
   exact object being used.

For questions specifically about the B01 textbook, route through
`papers/B01/SECTION_INDEX.md` instead of step 2-3 above — it is that paper's
own outline-ordered, chunk-anchored entry point.

## Local search commands

From the repository root in PowerShell:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  docs/new-libs/corpus/tools/search_corpus.py `
  'held-out roster generalization' --kind claims --axis variable_N
```

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  docs/new-libs/corpus/tools/search_corpus.py `
  'mutual information communication' --paper P15 --limit 8
```

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  docs/new-libs/corpus/tools/search_corpus.py `
  'O(N^-1/2)' --kind claims --evidence theorem --json
```

An empty query is allowed when filters are sufficient:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  docs/new-libs/corpus/tools/search_corpus.py `
  --kind papers --topic graphon
```

For exact field-oriented inspection, use `rg` over JSONL:

```powershell
rg -n -i 'held-out|cross-N|variable_N' docs/new-libs/corpus/claim_index.jsonl
rg -n '"evidence_type".*theorem' docs/new-libs/corpus/claim_index.jsonl
rg -n '"paper_id": "P14"' docs/new-libs/corpus/search_index.jsonl
```

## Suggested LLM prompt contract

```text
Use docs/new-libs/corpus as a retrieval index, not as independent evidence.
First route through claim_index.jsonl or a navigator. For every substantive
statement, preserve the record's source paper, PDF pages, conditions, limits,
and evidence type. Read the linked page-aligned chunk for context. If that chunk
has an extraction warning affecting an equation/table/layout-dependent claim,
inspect the original source PDF page. Clearly label curator_connection as a
prospective project hypothesis and never report it as a paper result.
```

## Query patterns

### Find formal support

Search claims for the object plus `evidence_type=theorem`, then verify the
theorem label, assumptions, and controlled quantity. A convergence theorem for
a mean-field game, approximation of an uncontrolled particle system, and policy
return guarantee are different objects.

### Find a method implementation

Start with `NAV_BY_METHOD.md`, read `Algorithms or mechanism primitives` in the
overview, then retrieve chunks tagged `algorithm`, `pseudocode`, `objective`, or
`experiment`. Inspect exact equations in the PDF when the chunk warns that math
text is unreliable.

### Find an empirical comparator or benchmark

Filter claims for `experiment` or `benchmark`, preserving task, roster size,
train/test protocol, sample count, seeds/runs, metric, uncertainty presentation,
and comparator. Do not infer one-frozen-policy cross-size transfer unless the
protocol actually freezes that policy before the target size.

### Find limitations and non-claims

Search `claim_kind=curator_boundary` and `source_scope`. Boundaries say what the
checked source does not establish; they are not global literature-absence
claims unless explicitly scoped that way.

### Connect a paper to HMASD

Search `claim_kind=curator_connection` and the relevant `hmasd_axes`. Treat the
result as a proposed construction, control, or validation requirement. It does
not transfer evidence or authorize a project claim.

## Compact context assembly

For most questions, give an LLM:

- the relevant navigator subsection;
- 1-4 claim rows;
- the selected paper overview; and
- only the chunks linked by those claim rows.

This usually preserves the necessary assumptions and evidence type while
avoiding hundreds of irrelevant PDF pages. Add the original rendered/source
page only for layout-dependent details.
