# Variable-k relevance rejection fixture — not a real round

This directory exists so `tests/review_round_contract_test.ps1` can prove the
round preflight refuses a question that carries no `## Variable-k relevance`
section (user ruling 2026-08-01: every Pro access must first answer the
standing check of `docs/project/RESEARCH_GOAL.md` — what does this round let
us say about variable k). It is not science, was never sent, and must keep
NOT carrying that section. Its allow-list below is deliberately valid so this
fixture violates exactly one guard.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
