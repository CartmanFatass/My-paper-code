# reference_libraries

Stdlib-only tools that build and search a lightweight LLM index over the My-lib paper corpus
(`/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/**/*.pdf`, arXiv preprints of
title-screened RL/MARL papers from ICLR/ICML/NeurIPS 2023–2025). The index lives outside this
repository, in the ignored directory `/mnt/c/Projects/My-lib/.local-llm-index/`.

**Hints locate papers; they are not evidence. A miss says nothing beyond this corpus.** Open and
read the PDF before relying on anything a hint says.

## Full-text reading notes in the original libraries

The owner-requested 2026-09-29 reading work is stored in each original library, separately
from these first-two-page hints. Luna screened the sources; Astra Max readers retained
source versions, hashes, physical PDF pages, actual reading coverage and limitations.

- My-lib: `/mnt/c/Projects/My-lib/.local-llm-index/deep-reading-index.jsonl` and
  `DEEP_READING_INDEX.md`; per-paper notes are in the adjacent `deep-readings/` directory.
- Inst-sci: `/home/fires/projects/Inst-sci/papers/MyLib/llm-index/deep-reading-index.jsonl` and
  `DEEP_READING_INDEX.md`; notes are in `../metadata/deep-readings/`.

Search the deep-reading JSONL with `rg` for mechanisms, keywords or paper IDs, then read the
referenced note and load-bearing primary passages. The existing CLI below still searches
the shallow locator index; it does not silently incorporate these notes. A missing prior
reading record is not proof that nobody read the paper. Completed, partial prior readings,
supplementary-source checks and deferred selections remain distinguished; no novelty verdict
or automatic research restart follows from these reference notes.

## Search

```bash
python3 tools/reference_libraries/search_mylib.py UAV multi-agent          # AND of case-insensitive substrings
python3 tools/reference_libraries/search_mylib.py hierarchical skill --min-relevance 2
python3 tools/reference_libraries/search_mylib.py --topic credit-assignment --topic MARL --json
```

Each hit prints `id | venue-year | title | pdf path | [rel N] one-line hint`. Terms match the
title, the (often truncated) arXiv abstract, ids, venue and every hint field. `rg` over
`hints.jsonl`, `INDEX_BY_TOPIC.md` or `INDEX_BY_RELEVANCE.md` works as well.

## Build

```bash
B=tools/reference_libraries/build_mylib_llm_index.py
python3 $B catalog                   # catalog.jsonl + titles.tsv (pdfinfo only; no model calls)
python3 $B hints --limit 20          # smoke run; --dry-run prints the first prompt and the call count
python3 $B hints                     # all missing hints, 6 workers, resumable
python3 $B hints --ids <id> --ids <id>   # retry specific papers
python3 $B navigate                  # hints.jsonl, INDEX_BY_TOPIC.md, INDEX_BY_RELEVANCE.md, README.md
python3 $B all                       # the three steps in order
```

`all --dry-run` on an empty output directory stops at the hints step, because the catalog dry run
writes nothing; dry-run `catalog` and `hints` separately.

- One headless call per paper: `timeout -k 10 120 omp -p --model gemini-3.8-flash --thinking medium
  --no-tools --no-session ... --system-prompt <index-hint instructions> --mode json --cwd <scratch> <prompt>`.
  The assistant text and `usage.cost.total` come from the assistant `message_end` NDJSON event.
  `--omp-cwd` defaults to the energy_relay_benchmark scratch directory (omp refuses to start in `~`).
- Model input: title, venue/year, arXiv abstract and `pdftotext -f 1 -l 2` text truncated to 6,000
  characters. The output is validated against a strict schema (fixed topic and setting vocabularies,
  word caps); a failed validation is retried once with the errors appended, then written as
  `hints/<id>.error.json`.
- Resumable: a paper with `hints/<id>.json` is never called again; papers with only an error file
  are retried on the next run. Stale error files are left in place; an ok file takes precedence.
- `--cost-cap-usd` (default 25) applies to the cumulative cost recorded in `build_log.jsonl`
  across runs; the run also stops after `--max-consecutive-infra-errors` (default 5) timeouts,
  auth, rate-limit or exit failures in a row. In-flight calls finish and are logged.
- The prompt version (sha256 prefix of the prompt templates and vocabularies) is stored in each
  hint and in the index README; changing the prompt does not invalidate existing hints.

## Ids

`id` is the proceedings `official_id` prefixed with `<venue>-<year>-` when it does not already
carry it (NeurIPS/ICLR hash ids are reused across venues). The unprefixed value is kept as
`official_id`. The one PDF with no acquisition record is `loose-<arxiv id>`.

## Tests

```bash
scientific=$(python3 -c 'from tools.research_support.interpreters import scientific_interpreter; print(scientific_interpreter())')
"$scientific" -m pytest -q tests/tools/reference_libraries/
```
