# GPT-5.6 Pro R30 Algorithm And Code Review Entry

Repository: `CartmanFatass/My-paper-code` (private)

Branch: `aggressive`

Target code/design commit: `f62baf626f6f37903b3929c4732952f95d2bc2ab`

## Preferred GitHub-Connector Route

Ask GPT-5.6 Pro to open this file from the private repository, then read in this
order:

1. `QUESTION.md` in this directory;
2. `RESEARCH_BACKGROUND.md` and `CODE_MAP.md` in this directory;
3. `docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`;
4. the exact code paths named in `CODE_MAP.md` at the target commit;
5. `memory/ALGORITHM_PRINCIPLES.md` only for disputed research constraints.

The code at the target commit is intentionally **pre-R30**. GPT must review the
accepted R30 design against the existing duration/expired-segment
implementation and identify the minimal correct implementation boundary.

## ZIP Fallback

If the GitHub connector cannot read the private `aggressive` branch, upload:

`HMASD_R30_ALGORITHM_CODE_REVIEW_20260714.zip`

The ZIP contains the same question, background, design, research constraints,
and relevant source files. No checksum is required; Git is the version source.

Return GPT's answer verbatim. Codex will archive the raw response before
interpreting it.
