# G51 formal-admission clarification

## CURRENT_REVIEW_ASSIGNMENT

The exact submitted fence identifies this round, its stage commit and the
allow-list in `01_SHARED_SOURCE_MANIFEST.md`. Read only this question and
those listed paths from the pushed stage commit.

The aligned G51 implementation is `ce6ed8659c480ca2779155b2871dc82b89fa0e95`,
aligned to `188b210975a0f243ae34318d658fbf943d1d63ab` at independent alignment
stage `aa756dcd06a2ea622c155f2983a89bb5d76e9d80`. Its index says that formal
admission is fail-closed because no formal authorization token or same-source
preflight interface is frozen. The standing user goal authorizes ten
automatic valid iterations, but it does not permit us to invent a token or
infer a preflight contract.

## Required disposition

Return exactly one terminal token as the first line:

`G51_FORMAL_EXECUTION_REQUIREMENT=REQUIRED`

`G51_FORMAL_EXECUTION_REQUIREMENT=NOT_REQUIRED`

`G51_FORMAL_EXECUTION_REQUIREMENT=SCIENTIFIC_AMBIGUITY`

If and only if the token is `REQUIRED`, provide the exact frozen formal
admission requirements needed to proceed, mechanically and without redesign:

1. the token field semantics and its binding to the aligned G51 source;
2. the same-source nonformal preflight evidence and artifact/schema contract;
3. the exact source, alignment, configuration, root and artifact identities
   that must be checked before formal dispatch.

If the token is `NOT_REQUIRED`, name the single in-scope action that should be
followed instead and state that no formal run is needed. Do not request code,
compute, a successor design, or a user permission question. Do not return a
second disposition token.
