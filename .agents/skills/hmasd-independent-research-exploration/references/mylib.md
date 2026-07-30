# MyLib JSON-only access contract

```text
default_mylib_root=C:/Projects/Inst-sci/papers/MyLib
content_contract=pdf+json+metadata+llm-index
write_authority=none
temp_search=forbidden
legacy_markdown_search=forbidden
counts_source=metadata/integrity.json
recall_source=llm-index/catalog.v2.jsonl
candidate_metadata=metadata/v2/papers.v2.jsonl
metadata_schema=metadata/v2/schema.v2.json
metadata_quality_report=metadata/v2/quality-report.v2.json
```

Before each research assignment, read these external authorities in order:

1. `C:/Projects/Inst-sci/AGENTS.md`
2. `C:/Projects/Inst-sci/papers/AGENTS.md`
3. `<MYLIB_ROOT>/llm-index/INSTRUCTIONS.md`
4. `<MYLIB_ROOT>/metadata/integrity.json`

Use `MYLIB_ROOT` when the library moves. The path above is only the default.
Never hard-code the observed counts or `missing_json_ids`.

## Retrieval sequence

1. Read integrity and fail closed unless `metadata_v2.status=validated` and its
   catalog, full JSONL, schema and quality-report paths are registered.
2. Recall candidates through the registered `catalog.v2.jsonl`. Do not fall
   back to the retired `catalog.jsonl` or any path under `papers/temp`.
3. Read each selected record from `papers.v2.jsonl`. Check `quality.grade`,
   `quality.warnings` and `provenance.field_evidence` before using it.
4. Read `json/<paper-id>.json`; extract `text`, `content` or `value` elements
   together with page, element, type and bbox context.
5. Use `assets/<paper-id>/` only when JSON coordinates bind the asset.
6. Open `pdf/<paper-id>.pdf` for original-text verification, equations,
   figure/table semantics, layout ambiguity or a missing JSON ID.

Catalog and full-record algorithm, setting, benchmark, contribution and related
research facets are Luna title/abstract-grounded analyses. They are discovery
metadata, not full-text verification.
Empty arrays and `unspecified` remain unknown and must not be completed from common knowledge.
Structured JSON is the
normal formal LLM content layer; PDF resolves fidelity-sensitive claims. If JSON
is missing, an exact official abstract with `evidence_url` may remain
`abstract_only` guidance, but details require PDF; record `json_missing=true`.
Never consult `papers/temp`, including archived Markdown.

Metadata v2 keeps `bibliographic` facts separate from model-assisted `research`
labels. Always carry the field evidence and quality warnings into the candidate
packet. A metadata field supports only its declared title/abstract-level scope;
method details, formulas, experimental values and limitations must be verified
in the underlying JSON/PDF.

## Probe commands

```powershell
$python = "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe"
$probe = ".agents/skills/hmasd-independent-research-exploration/scripts/mylib_research_probe.py"
$local = "./local_research"

& $python $probe --local-research-root $local status
& $python $probe --local-research-root $local search --query "changing membership" --limit 12
& $python $probe --local-research-root $local locate --paper-id MARL-0001
& $python $probe --local-research-root $local validate-pdf --paper-id MARL-0001
& $python $probe --local-research-root $local smoke --output "$local/mylib-smoke.json"
```

The probe is read-only toward MyLib. Its only write option is `--output`, and
that path must remain under the supplied `--local-research-root`.
