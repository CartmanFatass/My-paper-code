# VSP05-A4 blind portable-locator DTO retained-field admission — code/science index

This package implements the frozen zero-runtime treatment
`VSP05-A4-BLIND-PORTABLE-LOCATOR-DTO-RETAINED-FIELD-ADMISSION-AUDIT`.
It answers only whether the immutable accepted A1 bytes are portably locatable,
self-described, and structurally sufficient for a possible separately
authorized semantic audit. It never reads a retained-row scalar, emits a row
sample or presence vector, infers meaning from producer code, reconstructs a
field, runs an environment, or selects a scientific successor.

The input identity is the exact repository-relative POSIX locator
`logs/vsp05_a1_truth_reachability_1a09bccf_r1/raw_result.json`, opaque SHA-256
`d4ba7e00ae65c4f0cfd6f84b37c300e9e580868c42bd3c3f02eff20b0b3a3f2e`,
and row-container cardinality 15,971. The accepted source and publication
commits are `1a09bccf9bd64c756865531bc55a871afa286dd3` and
`9f3c57f809a0c0ee11868e025adbeea762832a46`.

## Blind source and parsing boundary

`resolve_portable_locator` requires an absolute caller-supplied verified
checkout/worktree root. It admits only the byte-for-byte registered POSIX
locator, resolves it once, and verifies that the resolved regular file remains
beneath the resolved root. Absolute locators, traversal, backslashes,
normalization variants, alternates, cwd substitution, missing paths, and
symlink escape fail closed. The environment-specific root and resolved
absolute file path are never serialized as scientific identity.

`_opaque_sha256` makes one binary hash pass. Only after the expected digest
matches does `scan_structural_schema` reopen the same resolved file for one
streaming UTF-8 structural pass. `_JsonReader.scalar_type` consumes row string,
number, boolean, and null lexemes without constructing their values.
`_StructuralScanner` materializes only JSON keys and the exact embedded schema
declaration. Its aggregate manifest contains paths, JSON type envelopes,
nullable observation, and total presence counts; it contains no row-local
presence vector or example.

## Authenticated self-description protocol

Meaning can enter only through the top-level immutable object
`vsp05_a4_retained_field_self_description`, which is authenticated by the
already-matched artifact digest. The object has the exact envelope:

```text
schema_kind = VSP05_A4_RETAINED_FIELD_SELF_DESCRIPTION
schema_version = 1
row_container = /real_frontier_rows
slots = exact frozen group and slot roster
closed_handoff_allowlist = {closed: true, members: [...]}
```

Each slot and each explicitly enumerated allowlist member has exactly one
binding. `direct_field` declares one exact JSON pointer. The also-admissible
`subject_indexed_field` declares one path template containing `{subject}`, a
literal nonempty unique subject-key roster, and one literal subject role. Both
forms declare non-null JSON types and nullability. Names, aliases, defaults,
code, neighboring rows, or data values never supply or repair a binding.

Missing, malformed, incomplete, or multi-path declarations remain unbound and
naturally select branch 3. Branch 4 is reachable only after every frozen slot
and the closed allowlist have one authenticated unambiguous declaration, but
the streamed row envelopes show missing presence, incompatible type,
incompatible nullability, or missing declared subject-indexed structure.

## Claim-to-code map

| Protected assertion | Implementation symbols | Observable invariant | Focused evidence |
|---|---|---|---|
| Caller root is not identity; only the exact contained POSIX locator is admissible | `_portable_parts`, `resolve_portable_locator` | Absolute, traversal, normalization, alternate, cwd, and symlink-escape paths fail before hashing; result carries no absolute path | locator parameterization, relative-root, and symlink-escape tests |
| Opaque identity precedes structure | `_opaque_sha256`, `run_admission_audit` | Hash mismatch performs zero structural passes; parse/cardinality failures select branch 2 | hash/parse/cardinality test |
| Row values remain blind | `_JsonReader.scalar_type`, `_discard_number`, `_StructuralScanner._row_value` | Scalars are consumed without construction; result counters and attestations remain zero; sentinel scalars never appear in output | sufficient and incomplete synthetic-fixture tests |
| DTO meaning comes only from immutable self-description | `bind_self_description`, `_binding_paths`, `_declared_envelope` | Missing or ambiguous binding selects branch 3; no name-based inference or repair exists | missing/ambiguous DTO test |
| Authenticated retention failures are distinct from binding failures | `_presence_receipt`, `bind_self_description` | Only an exact fully bound DTO can select branch 4 for absent/incompatible retained envelopes | partial-presence test |
| Direct and explicit subject-indexed structures are admissible | `_binding_paths` | One direct pointer or one explicit template/domain/role binds; no guessed subject key is read from row values | subject-indexed fixture test |
| Five-branch precedence and caps are protected | `_caps_violated`, `_select_branch`, `validate_result` | Scope, source, binding, retention, sufficient order is recomputed; stale branch and protected receipts fail validation | cap/precedence tamper test |
| Production publication cannot inherit fixture identity or an unrun/fabricated stage | `validate_result`, `_validate_component_result`, `write_result_once` | Public validation has no caller-supplied cardinality; exact registered digest/cardinality and one registered audit are unconditional; locator/hash/parser/row counters remain stage-coherent; all protected attestations remain false | component/unrun/reviewer-fabrication rejection and protected-attestation tests |
| Publication is one-shot and claim-bounded | `_install_result_once`, `write_result_once`, `main` | Production validation precedes canonical atomic installation without overwrite, and the result carries no scientific disposition or successor | component installer, production rejection, and runner-help tests |

## Terminal precedence and result boundary

The result recomputes exactly one first branch in this order:

1. `A4_BLINDNESS_OR_SCOPE_VIOLATION`
2. `A4_IMMUTABLE_SOURCE_OR_PORTABLE_LOCATOR_INVALID`
3. `A4_DTO_SEMANTIC_BINDING_UNAVAILABLE`
4. `A4_REQUIRED_RETENTION_INCOMPLETE`
5. `A4_BLIND_ADMISSION_SUFFICIENT`

Every result carries expected and observed portable-source binding, parser and
cardinality status, the per-slot source pointer or null, binding basis,
declared type/nullability, aggregate presence evidence, closed-allowlist
manifest, all hard-cap counters, blindness/no-reconstruction attestations,
accepted commits, public result/index locators, an Operator-receipt placeholder,
the strongest alternative, and residual uncertainty. It emits no semantic row
scalar, scientific count, example, label table, witness, or learner inference.

The thin entry point is
`scripts/run_vsp05_a4_blind_portable_locator_dto_retained_field_admission.py`:

```text
python scripts/run_vsp05_a4_blind_portable_locator_dto_retained_field_admission.py \
  --checkout-root <caller-verified-absolute-root> \
  --output <new-a4-result.json>
```

There is no input/locator override on the registered CLI, no fallback search,
and no overwrite. Even branch 5 establishes only structural addressability;
it does not authorize a semantic audit, learner, C treatment, External Pro,
promotion, retirement, or reopening of another route.

`_validate_component_result` exists only for synthetic opaque proof fixtures and
requires an explicit fixture row bound. It is not a publication validator.
The public `validate_result` and `write_result_once` always use the frozen
15,971-row bound and registered digest, require
`registered_admission_audits=1`, reject an unrun base envelope, and enforce
coherent locator/hash/parser/row stages. They also require both
`source_reopened_after_structural_pass` and
`environment_specific_absolute_identity_emitted` (along with every other
protected boolean blindness/reconstruction attestation) to remain false, while
the paired semantic/sample/code/fallback counters remain zero. The writer never
reads its validation bound from the artifact being published.

A completed opaque pass whose observed digest equals the frozen expected digest
must advance to exactly one structural pass. A branch-2 artifact claiming hash
success while retaining `parser_status=not_started`, zero structural passes,
and zero row envelopes is therefore rejected before installation. An observed
digest mismatch remains the legitimate branch-2 early-stop case: it performs
no structural pass and retains the not-started parser stage.

## Implementation-time evidence boundary

Implementation verification uses only synthetic opaque component fixtures.
It does not invoke the registered audit or perform a structural pass over the
real accepted A1 artifact. The evidence action has `H=0`, `K_search=0`, zero
hypothetical transitions, and no experiment-pool or formal-compute activity.

## Registered publication — VSP05-A4

- Source commit: `ec12cc37f91629a19b05e9a14c0f723fe68b6b20`; terminal branch: `A4_DTO_SEMANTIC_BINDING_UNAVAILABLE`.
- Public result: `VSP05_A4_BLIND_PORTABLE_LOCATOR_DTO_RETAINED_FIELD_ADMISSION_RESULT.json` (byte-for-byte raw audit publication; SHA-256 `313373A2C58BD66DB4F7E3E072FFB3B4AC3A9DFED9341CBDC53E9F7F929555A`).
- Audit evidence: one locator/hash/schema pass, 15,971 row-schema envelopes, semantic values/code reads/samples/runtime/retry/fallback all zero; no semantic audit, learner, successor, promotion, retirement, B/C/Pro authorization.
- Source readiness: `.git/worktrees/vsp05_a4_source_readiness_clean_candidate_20260810/hmasd/execution-readiness/ec12cc37f91629a19b05e9a14c0f723fe68b6b20/vsp05_a4_source_readiness_r1.json`.
- Operator receipt: `temp/sessions/code_project_manager/vsp05_a4_operator_receipt.json` (`ERROR` solely because offline phases are `N/A`; no runtime was attempted).
