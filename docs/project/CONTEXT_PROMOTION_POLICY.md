# Context Promotion Policy

Promotion never happens automatically from raw prose, model summaries, semantic
hazard words, or compaction output.

A promotion requires a typed proposal, a validated semantic owner, an explicit
owner disposition, an actual canonical artifact write by the authorized writer,
and an applied receipt. The promotion subsystem never edits canonical files.

## Kinds

`EPHEMERAL`, `AUTHORITY_RULE`, `ROLE_CONTRACT`, `PROCEDURE`,
`REPOSITORY_NAVIGATION`, `SHARED_ARCHITECTURE_DECISION`, `SCIENTIFIC_ARTIFACT`,
`TECHNICAL_ARTIFACT`, `PORTFOLIO_ARTIFACT`, `CURRENT_WORK_POINTER`.

## Owner matrix

| Kind | Valid owner | Destination |
| --- | --- | --- |
| AUTHORITY_RULE | Operational Root | `AGENTS.md` or Role |
| ROLE_CONTRACT | exact Role owner | Role |
| PROCEDURE | procedure owner | Skill |
| REPOSITORY_NAVIGATION | CM for PROJECT_MAP, Root for CURRENT_WORK | existing map/index |
| SHARED_ARCHITECTURE_DECISION | Operational Root/user | ADR |
| SCIENTIFIC_ARTIFACT | same-direction EM | existing direction artifact |
| TECHNICAL_ARTIFACT | scoped CM | existing technical artifact |
| PORTFOLIO_ARTIFACT | dedicated Portfolio | portfolio adjudication |
| CURRENT_WORK_POINTER | current-work owner | partitioned current-work record |
| EPHEMERAL | current actor | no file |

## Lifecycle

`PROPOSED` → `OWNER_ACCEPTED` → `APPLIED`, or `PROPOSED` → `OWNER_REJECTED`.
A proposal may be `CARRIED_FORWARD` into the next epoch and then accepted or
rejected there.

Keep a note ephemeral when it is exploratory. Promote only when the owner is
writing a durable shared or owner-canonical artifact. Summaries cannot open
proposals.
