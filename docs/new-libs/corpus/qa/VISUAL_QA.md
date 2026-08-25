# Visual extraction QA

At least one representative content page from every source PDF was rendered
with the bundled Poppler `pdftoppm` executable and inspected against `pypdf`
extraction. This is a routing audit: it checks reading order, equations, tables,
figures, fonts, and labels well enough to decide when an LLM must return to the
source page. It does not certify that spatial mathematics can be reconstructed
from linear text.

Detailed per-paper observations:

- [Agent A QA - B02, B03, P01, P02, P04, P05, P13, P17, P18, P19, P21](../_partials/agent_a_qa.md)
- [Agent B QA - B01, P03, P06-P12, P14-P16, P20, P22, P24, P25](../_partials/agent_b_qa.md)

## Coverage

- 27/27 PDFs visually sampled.
- `pypdf` and `pdfinfo` page counts reconciled for every source.
- Dense theorem/equation/algorithm/table or two-column pages were preferred over
  title pages.
- Page-aligned chunks retain all pages, including blank/decorative pages, with
  warnings rather than silent omission.

## Important source-specific cautions

- **P19:** the legacy PDF loses Symbol/Arial mathematical glyphs in Poppler
  rendering. Use theorem prose and the original source file; extracted formula
  constants are not authoritative.
- **P18:** all six pages are dense two-column text. Column sequence is explicitly
  marked uncertain.
- **B02 and P17:** some pages contain NUL/font-extraction artifacts. They remain
  warned and page-traceable instead of being silently rewritten.
- **B01:** the source records a restriction against AI-system training. This
  local corpus is a retrieval/access derivative, not training data and not a
  redistributable replacement for the book.
- **P07:** the source is a 2026 arXiv v1 preprint. Visual fidelity does not change
  its provisional evidence status.

## Warning semantics

- `equation_text_unreliable`: display math, matrices, fractions, subscripts, or
  symbols lost spatial fidelity; inspect the PDF for exact notation.
- `table_text_unreliable`: cell geometry or row/column association is not safe
  in linear text; inspect the table.
- `multi_column_order_uncertain`: extraction may interleave columns/captions;
  inspect the rendered/source page for sequence.
- `scan_or_font_issue`: missing glyphs, NULs, decorative pages, or legacy-font
  behavior may make text incomplete.

These flags are deliberately conservative. A warning does not mean the entire
page is unusable; it prevents an LLM from silently treating layout-dependent
text as exact.
