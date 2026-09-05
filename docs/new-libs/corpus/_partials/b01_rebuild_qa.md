# B01 rebuild QA note

Rebuild date: 2026-09-02. Source: `C:\Users\fires\Downloads\marl-book.pdf` copied to
`docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf`.

## PDF identity

- sha256: `4eec7be5bcabaf912846ddd295925c35d46502d92fcd9f7ba3311656fd2e9091`
  (matches the value given in the task; recorded as `metadata.json.content_fingerprint`).
- Build: pdfTeX, dated 2026-03-24 (newer build of the same edition as the previously
  indexed 2025-06-18 build; fingerprint of that older build was `sha256:50f0dc03...`,
  now superseded).
- Page count: 395 (via `pymupdf`; unchanged from the previous index).
- Outline (`doc.get_toc()`): 194 entries, confirmed. Levels actually span **1-4**, not
  "1-3" as stated in the task brief — see "Outline anomalies" below.

## Extraction

- Extracted with `pymupdf` `page.get_text("text")`, one call per page, 1-395.
- Total extracted words: **141,469**.
- Extractable pages (>=40 words, no replacement chars/font garbage): **376**.
- Warning pages (metadata.json `warning_pages`, 19 total, all `<40 words`):
  `1, 3, 4, 5, 6, 9, 18, 19, 24, 25, 29, 47, 71, 143, 189, 211, 333, 365, 391`.
  All 19 were individually inspected and are genuine near-blank pages (front-matter
  half-title/blank versos, and blank pages at the back of the Summary-of-Notation and
  List-of-Figures fronts, plus blank chapter-end/part-divider versos) — not extraction
  failures. None contain replacement characters (`n_repl == 0` on every page) or
  `(cid:N)` glyph-mapping garbage (`n_cid == 0` on every page) anywhere in the document.
- No pages were classified as "mostly figures": pages with embedded raster images
  (19 pages, up to 9 images on one page) all also carry 250+ words of caption/body
  text, so none qualify as figure-dominant.

### Real (subtler) extraction risk found: big-operator glyph substitution

This PDF build extracts prose and pseudocode very cleanly (see visual QA below), but on
pages with displayed/numbered equations, the large summation (Σ) and product (Π)
operator glyphs are extracted as ordinary Latin letters that still look like plausible
text — e.g. on PDF page 226, the softmax denominator prints as
`P a'∈A el(s,a';ϕ)` where the book actually shows `Σ_{a'∈A} e^{l(s,a';ϕ)}`, and on PDF
page 56/60/93 the same pattern surfaces as `X a∈A ...` / `Y τ=0 ...` for Σ/Π elsewhere.
This is not caught by replacement-character or `(cid:N)` heuristics because the output
is well-formed ASCII/Unicode that merely means something different than the glyph
originally drawn. Detected via: any page containing a numbered-equation line
(`\(\d+\.\d+\)` at end of line) — 134 of 395 pages match. Every chunk touching such a
page carries `extraction_warnings: [equation_text_unreliable]` (50 of 85 chunks).
No `table_text_unreliable` tag was needed: the book has zero pages containing the
literal word "Table" (confirmed by full-text scan) — the one candidate table-like
element (the RL↔game-theory "dictionary" on PDF page 87) is delivered as an
unextracted Figure (3.5), correctly absent from the extracted text rather than
garbled.

## Structure (`structure.json`)

194 outline entries mapped 1:1 to `S001`-`S194`, `pdf_pages` computed as
`[start, page-before-next-same-or-higher-level entry]`, last entry clamped to 395.

Two structural facts worth flagging rather than silently fixing:

1. **Level depth is 1-4, not 1-3.** Because Part I / Part II wrap the numbered chapters
   one level deeper, e.g. `2 Reinforcement Learning` is level 2 and `2.1 General
   Definition` is level 3, `3.4.1 Belief States and Filtering` is level 4. Front-matter
   items, unwrapped Chapter 1, Appendix A, References, and Index sit at level 1.
2. **Appendix A / References / Index nest under Part II in the raw outline.** Their
   TOC level (2) is identical to Part II's chapters' level, so the stack-based
   parent/child reconstruction (faithful to the PDF's own bookmark nesting, not an
   artifact of our script) places them as Part II's siblings/children rather than as
   independent back-matter. This is the source PDF's actual outline tree, not a bug
   introduced here, and it is why the chapter/appendix/references/index table below
   still resolves correctly (chunking used `family_key`, not raw nesting depth).
3. **7 same-page adjacent short sections** initially produced `start > end` spans
   before clamping (each pair fits on one shared PDF page, e.g. `1.3.2 Competitive
   Play...` and `1.3.3 Autonomous Driving` both start on page 39): clamped to
   `end = max(end, start)`. Two of these pairs (`3.7`/`3.8` on p.87 and `4.2`/`4.3` on
   p.94) also produced duplicate page coverage across the corresponding chunking
   leaves, which was resolved by merging the two sections into one chunk (a physical
   page's text cannot be split between two sections).

## Chunking

- Leaf units built from the outline tree (chapter/Part own-intro pages folded forward
  into the first child subsection; x.y-level sections treated as the chunking grain
  regardless of x.y.z children, per spec).
- Long leaves (References, several long x.y sections) split into consecutive
  page-contiguous pieces respecting the 6-page cap and ~3000-word ceiling.
- Tiny adjacent leaves merged only when they share the same chapter/appendix/
  references/index "family" (never across a chapter boundary, so a chapter-ending
  "Summary" never absorbs the next chapter's opening section) and stay page-contiguous
  and within 6 pages / 3000 words.
- Result: **85 chunks**, `B01-C0001`-`B01-C0085`, covering pages 1-395 exactly once
  each (verified: no gaps, no duplicates, no >6-page chunk, all chunk_id/page spans
  monotone non-overlapping). 141,469 total words, matching the raw per-page sum.
- 26 of 85 chunks fall below the 1200-word soft target; all are natural document
  boundaries (chapter-end "Summary" sections, front-matter items, References/Index
  tail fragments) where merging would have crossed a chapter/family boundary or blown
  past the 6-page/3000-word caps — left as-is per spec priority (never combine
  noncontiguous/unrelated content just to hit the word target).

## Visual QA (3 pages, rendered via `pymupdf.get_pixmap` at 80/72 zoom — `pdftoppm` is
not present under `/mingw64/bin` or elsewhere on `PATH` in this environment, contrary
to the task brief; pymupdf rendering is the in-repo equivalent capability)

| Page | Chosen for | Result |
| --- | --- | --- |
| 226 | Dense equation page, Ch. 8 (softmax policy, policy-gradient-theorem intro) | Prose and equation numbers (8.7, 8.8) extract correctly and in order; **confirms** the Σ→"P" glyph-substitution issue described above (`π(a\|s;ϕ) = e^l(s,a;ϕ) / P_{a'∈A} e^l(s,a';ϕ)` should read `Σ_{a'∈A}`). Chunk B01-C0050 correctly carries `equation_text_unreliable`. |
| 230 | Algorithm pseudocode page, Ch. 8 (`Algorithm 13 REINFORCE`) | Extracted pseudocode is a verbatim, line-for-line match of the rendered box (all 8 steps, variable names, and the loss-function line). No warning needed beyond the page's own `equation_text_unreliable` (it also carries equations 8.17-8.22 below the box). |
| 392 | Two-column page (closest analogue to a table page — the book has **no** literal tables anywhere; confirmed by a full-text scan for "Table") — book Index | Reading order is correct: pymupdf extracts the **entire left column top-to-bottom, then the entire right column top-to-bottom** (standard/expected order for this layout), which is directly verifiable because index entries are alphabetical and the extracted sequence is alphabetically monotone across the column boundary (`...Bellman equation → best responses → bias-variance tradeoff → Boltzmann policy → bootstrapping → catastrophic forgetting...`). No `multi_column_order_uncertain` tag applied anywhere in the corpus; none was warranted. |

## Deviations from the literal task steps

1. `pdftoppm`/`pdftoppm`-equivalent from `/mingw64/bin` was not found in this shell's
   `PATH`; substituted `pymupdf.Page.get_pixmap()` at an equivalent 80 dpi render,
   which is the tool already in use for extraction and is explicitly permitted in the
   tool list.
2. Outline levels are 1-4 (task said 1-3); handled by using regex-derived dot-count on
   the `number` field for chunking granularity rather than the raw TOC `level`, so the
   deeper nesting did not distort chunk boundaries.
3. `structure.json` intentionally has **no synthetic entry for PDF pages 1-15**
   (cover/praise/copyright/dedication/contents) because the first real TOC entry
   ("Summary of Notation") starts at page 16 and the task specified "one entry per
   outline entry" (194, no additions). Those 15 pages are still fully covered by
   chunks (`B01-C0001`-`B01-C0003`, `section_path: ["Front matter (cover, title page,
   copyright, dedication, contents)"]`), just not by a `structure.json` row.
4. Chunk count is 85 (old index had 67) — expected per the task ("the count will
   differ, that is fine").

## Corpus tooling reused

`docs/new-libs/corpus/tools/build_corpus_indexes.py` (merge/validator, not an
extractor) and `search_corpus.py` (query CLI) already existed; neither performs PDF
extraction or chunk generation, so no reusable extraction/chunking script existed to
adapt. A standalone validator mirroring `build_corpus_indexes.py`'s per-paper checks
(page contiguity/monotonicity/coverage, `[PDF page N]` markers, duplicate IDs,
keyword-count band, fingerprint/page-count/chunk-count agreement) was run
against the rebuilt B01 files only (the full merge script requires all 27 papers'
source PDFs on disk, most of which are out of scope for this task) and passed with
zero errors.
