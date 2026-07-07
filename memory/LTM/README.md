# Long-Term Memory Archive

Purpose: store full historical records so root `memory/` can stay compact.

Use root memory for current work:

- `memory/CURRENT_WORK.md`: first-read current state and next actions.
- `memory/ALGORITHM_PRINCIPLES.md`: active research contract.
- `memory/IMPLEMENTATION_PLAN.md`: active staged plan.
- `memory/ExpRecord.md`: compact current experiment dashboard.

Use this folder for long-term records:

- `PROJECT_HISTORY_20260707_full_import.md`: imported full historical
  state before LTM compaction.
- `EXPERIMENT_RECORD_20260707_full_import.md`: imported full experiment ledger
  before compaction.
- `CROSS_VALIDATION_20260707_full_import.md`: imported full cross-validation
  ledger before compaction.
- `EXPERIMENT_ARCHIVE.md`: append-only experiment conclusions and handoff
  summaries maintained by LongTimeMemoryManager from ExpManager factual records.
- `external_reviews/INBOX.md`: template-preserving paste area for external
  model dialogue.
- `external_reviews/DIALOGUE_ARCHIVE.md`: newest-first detailed Claude /
  GPT-5.5 Pro / Gemini dialogue archive.
- `external_reviews/INDEX.md`: newest-first lightweight review-round index.

## Update Rule

When an experiment is completed, invalidated, superseded, or materially
reinterpreted, ExpManager records the factual experiment state and handoff.
LongTimeMemoryManager decides whether and how to update
`memory/LTM/EXPERIMENT_ARCHIVE.md`.

When the active research direction changes, LongTimeMemoryManager updates
`memory/CURRENT_WORK.md`, then appends any historical narrative that would make
the current file bulky to an appropriate file in this folder.

ExternalReviewManager manages `external_reviews/` files and produces handoffs.
LongTimeMemoryManager decides whether external review content changes current
memory, principles, plans, experiments, or archives.
