# Local literature for DM decisions

OWNER_DIRECT 2026-09-06: use the existing libraries when a concrete research question
needs evidence. This is question-driven retrieval, not a new mandatory reading list.

## When to retrieve

Retrieve when designing or recasting a mechanism, selecting a comparator, examining
an unexpected result, or assessing related-work overlap. State the question first.
Reuse relevant evidence already checked in the current card/intake unless the question,
source version or required coverage changed. Ordinary CM implementation does not trigger
a fresh search. Historical research and every cited paper are not startup reading.

## Existing entry points

- **My-lib — mechanism overlap and alternatives:** `C:/Projects/My-lib/README.md`
  documents the existing local CLI and mechanism/evidence records. Use its existing
  index and supported search interface. A CLI search uses the library's Innovation
  Brief and explicit collection selection; derive these from the current question,
  without asking DM or CM to rewrite the science card. Inspect relevant returned
  source pointers, conditions and differences. No new index, service or acquisition
  pipeline is needed for HMASD integration.
- **Inst-sci — paper methods and empirical evidence:** the formal library is
  `C:/Projects/Inst-sci/papers/MyLib/`; start with `llm-index/catalog.v2.jsonl`.
  Search title, algorithm, setting, benchmark or mechanism terms with bounded output.
  Read a candidate's full metadata record in `metadata/v2/papers.v2.jsonl` when
  needed, including quality warnings and field provenance. Read relevant pages or
  elements from `json/<paper-id>.json` for substantive claims; use the corresponding
  `pdf/<paper-id>.pdf` and assets when equations, tables, figures or extraction gaps
  need verification. Use `metadata/integrity.json` for asset-availability questions;
  do not rely on counts in old READMEs. Ignore `papers/temp` in ordinary retrieval.

These are local control-plane paths, not paths relative to a DM worktree or remote
execution node. If unavailable, report that concrete coverage/access gap and use an
available source; do not silently treat the library as empty. This reading workflow
does not require loading the Inst-sci download skill or performing downloads.

## Evidence and handoff

Indexes, title/abstract tags and mechanism matches identify candidates; they do not
establish novelty, fair comparison or a scientific result. Confirm material claims
in the source, retaining assumptions, setting, limits and page/section references.
Distinguish the paper's finding from the DM's inference about HMASD. A local miss means
no match in the searched snapshot, not absence of prior work. Extend to official
external sources for a specific gap or freshness need, rather than forcing local coverage.

Record the paper identity/version, source JSON/PDF path and page/section, bounded claim,
and which current choice it informs in the existing card or intake. CM receives only
the relevant algorithm, equation or passage needed for its deliverable, with a precise
pointer or excerpt if the source is inaccessible. Do not attach the whole paper set,
repeat the research history, or create a separate literature report by default.
