# Review model

```text
status=IN_FORCE
decided=2026-07-25 by user
```

RL is theory plus experiment driven, so two things get external review:

1. **The scientific idea.**
2. **Implementation detail choices and key algorithms — confirmed with External
   Pro before implementing.**

Nothing else.

Point 2 is the one that pays. Every expensive failure here was a realization
choice that decided whether a result meant anything, and each was answerable
before the code existed — *"how exactly will this hold `h_j` fixed?"*, *"is this
null the same object as the statistic?"* **Move the question earlier; do not add
a gate after.**

## In force

- **Pre-send pass** — one cheap adversarial read of a question before it goes to
  Pro. Three for three on real catches.
- **Archetype casebook** — `.claude/skills/hmasd-contract-grill/SKILL.md`. The
  checklist for point 2.
- **Decision ledger** — `DECISION_LEDGER_TEMPLATE.md`, without certificates.

## Retired

Gates, certificates, validation tiers, blinded grading, finding-disposition
manifests. Records kept in `CONTRACT_GRILL_DESIGN.md` and
`PRO_FIRST_LOOP_PROPOSAL.md` so they are not re-proposed.

Pro ruled `CHANGES_REQUIRED` on the retired mechanism; that ruling is not
disputed, the mechanism was retired instead. Its substance survives in the
casebook.
