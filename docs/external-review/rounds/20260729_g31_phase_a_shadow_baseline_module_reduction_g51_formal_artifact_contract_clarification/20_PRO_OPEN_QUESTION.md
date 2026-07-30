# G51 formal-artifact contract clarification

## CURRENT_REVIEW_ASSIGNMENT

The exact submitted fence identifies this round, its stage commit and the
allow-list in `01_SHARED_SOURCE_MANIFEST.md`. Read only this question and
those listed paths from the pushed stage commit.

The Code Project Manager reported this exact frozen conflict at the aligned
G51 implementation. The clarification that led to the current formal
interface admits any of four schema-valid outcomes: `INVALID`,
`COUPLING`, `EXACT_REMOVABILITY`, or `NUMERICALLY_UNRESOLVED`. At the same
time, it lists `reference_final.pt`, `reduced_final.pt` and
`parallel_proof/two_process_equivalence.json` as required preflight artifacts
for every outcome. The aligned G51 implementation intentionally emits the
two final checkpoints and two-process artifact only for
`EXACT_REMOVABILITY`; adverse outcomes serialize an empty checkpoint inventory
and readiness returns before creating two-process evidence.

Requiring the full listed inventory would silently admit only the favorable
exact-removability branch. Inventing placeholder or terminal adverse
checkpoint payloads would change the aligned G51 artifact semantics.

## Required disposition

Return exactly one terminal token as the first line:

`G51_FORMAL_ARTIFACT_CONTRACT=OUTCOME_CONDITIONAL`

`G51_FORMAL_ARTIFACT_CONTRACT=ADVERSE_CHECKPOINT_SCHEMA_REQUIRED`

`G51_FORMAL_ARTIFACT_CONTRACT=SCIENTIFIC_AMBIGUITY`

If and only if the token is `OUTCOME_CONDITIONAL`, state the exact
outcome-to-artifact inventory and the fail-closed admission rule for each of
the four outcomes, including whether the adverse branches omit the final
checkpoint and two-process artifacts.

If and only if the token is `ADVERSE_CHECKPOINT_SCHEMA_REQUIRED`, freeze the
exact non-placeholder payload and validator schema for each adverse outcome;
do not ask Code PM to invent one.

Do not redesign G51, choose a scientific result, run compute, modify code,
or request user permission. Do not return a second disposition token.
