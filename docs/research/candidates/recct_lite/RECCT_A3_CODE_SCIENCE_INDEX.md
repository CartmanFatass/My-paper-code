# RECCT-A3 common one-port update-bank noninterference: code-science index

Candidate: `CAND-VAP-RECCT-LITE@factorized-one-port-policy-value-revision-v10`

Treatment: `RECCT-A3-COMMON-ONE-PORT-UPDATE-BANK-NONINTERFERENCE`

Status: prospective result-bearing implementation. The implementation worker
ran only the unregistered direction-local technical fixture and focused tests.
No registered audit, result branch, publication, readiness, technical
acceptance, B2, C, Pro, promotion, retirement, or scientific conclusion is
claimed here.

## Accepted callable and separately sealed source boundary

`common_one_port_update_bank_noninterference.py` imports the accepted RECCT-A1
`DirectedEdgeMaskedUpdate` directly. `A1Binding` freezes the accepted A1 source
and result commits, passing branch, raw-output binding, port-payload schema and
learner mint provenance. `_authenticated_orientation_binding` is a narrow
owner-authenticated adapter: the owning learner verifies its registry and
opaque LR/RL handle objects, but A3 never requests, deserializes, or exposes A1
private capsule bytes.

The proposal/confirmation data gap is represented by
`SealedCreditSource`. Registered execution may construct it only from a
pre-existing Git-blob-bound immutable DTO with an explicit source record,
commit, path, blob and byte SHA-256. No eligible public DTO currently exists;
DTO paths under `local_research` are rejected before reading. The registered
runner therefore returns
`A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE` before pair
construction or any shadow call unless CPM supplies one. Synthetic rows exist
only in the separately named technical fixture.

At source sealing, the Git-bound outer DTO exposes only a base64-encoded opaque
content blob plus its byte digest, declared count and ordered-key digest. The
registered loader decodes base64 bytes but never JSON-decodes or constructs
prediction/reward rows. Those opaque bytes are bound to proposal epochs
`[0,2,4,6]`, confirmation halves `A=[1,5]`, `B=[3,7]`, lineage and the owning
A1 capsule digest. Pair selection receives only a presealed opaque manifest
with content/lineage/order digests and count; it neither traverses nor rehashes
observation contents. Manifest-access, content-open and content-decode counters
are separate. Only after `PAIR_FROZEN` may the credit binder open the selected
source, rederive its byte digest, JSON-decode prediction/reward floats and
validate the exact ordered A/B by `00/10/01/11` rows. The selection receipt and
`PAIR_FROZEN` activity evidence record zero content decodes before that point.

`bind_credit_tensor` computes every `q` as the arithmetic mean negative BCE of
four detached predictions against the already observed four-step binary team
rewards. It then applies the exact frozen LR/RL difference order and records
all eight q values, all eight C values, source digest, formula order, and exact
quarter weights. Missing, duplicate, misordered, unbound, or nonfinite source
data fails closed with no imputation or replacement.

## Four-cell bank and componentwise evidence

The audit unconditionally calls only the accepted A1 one-port masks:

```text
stored:     PLUS/LR(10), PLUS/RL(01), MINUS/LR(10), MINUS/RL(01)
recomputed: MINUS/RL(01), MINUS/LR(10), PLUS/RL(01), PLUS/LR(10)
```

Each call restores a fresh clone of its member's sealed learner and complete
Adam state. Within each orientation, LR and RL have the same bit-identical
pretreatment receipt. Every call has one distinct authenticated opaque handle,
one active port, an independent one-use A1 RNG clone, unchanged site counters,
and no `00`, `11`, commit, live update, policy, environment, trainer, or
evaluation call.

The role-instance table binds public `LEFT/RIGHT` roles to the learner's
authenticated A1 handle source/receiver records. PLUS must bind LR=`LEFT->RIGHT`
and MINUS must bind LR=`RIGHT->LEFT`; swapping both orientations, roles and
handles together is rejected before a shadow call.

`CellLedger` retains orientation/port/mask/handle, capsule/batch/roster/config
and RNG lineage; complete named learner and Adam state before and after; the
full ordered dense A1 gradient receipt; computed global norm; explicitly
disabled clipping with coefficient one; optimizer hyperparameters; complete
parameter delta; and capsule digest before/after. The accepted A1 interface
normalizes its finite fixture gradient receipt to named dense tensors; A3 does
not infer parameter-coordinate edge ownership from those tensors.

Each stored cell must equal only its own recomputation under A1's complete
transition predicate. LR and RL are deliberately not compared for equality.
After all four equalities, unchanged original digests, common ancestry and RNG
isolation pass, `HiddenImmutableBank` seals the four potential cells behind a
private mapping and exposes only a digest plus outer-harness pointer resolution.
Every attempted shadow has a retained started/completed/indeterminate event.
Post-call failures retain all completed call ledgers, partial equalities,
selector/sentinel evidence and observed optimizer activity. Result counts are
always rederived from these records; a zeroed post-call failure cannot validate.

## Selector firewall and sentinel manifest

Each selector has one argument: a view with only the two ordered four-entry C
vectors and the prospectively fixed shared tie value `LR`.

- `SIGNED_DIRECTED` compares signed arithmetic means.
- `SIGN_DESTROYED` compares arithmetic means of component magnitudes.
- `BALANCED_DIRECTION_BLIND` reads only the tie value.

Selectors return only `LR` or `RL`. They never receive orientation labels,
support/reliability, gradients, norms, clipping, Adam state, update norms, bank
objects/digests, outcomes, or instance/seed/slot/capsule/source identities.
`AccessTrapSelectorView` raises on any undeclared attribute. The outer harness
adds the sealed bank digest and resolves the selected cell only after the
selector returns.

The six committed orientation-by-selector records are followed by the exact
12-case by three-selector pure sentinel manifest (36 calls). It checks the
base case, global sign inversion, mixed component sign flips, candidate swap,
both-score ties under both bits, signed-only ties under both bits,
absolute-only ties under both bits, and two access-trap variants. A second
reverse-order invocation verifies all six pointers and selected cell digests
without changing the six committed records or bank.

## Traceability

| claim_id | code path and symbol | observable invariant | focused evidence |
|---|---|---|---|
| RECCT_A3_PROSPECTIVE | `::CreditSourceLineage`; `::CreditSourceManifest`; `::SealedCreditSource`; `::select_first_structural_pair` | registered source requires immutable Git DTO lineage; loader retains base64-decoded content as digest-bound opaque bytes; selection sees only presealed manifests and leaves content-open/decode counters zero through `PAIR_FROZEN` | `test_technical_preflight_selects_structurally_before_opening_credit`; `test_credit_fixture_rejects_misordered_or_unbound_source`; `test_registered_runner_without_existing_source_dto_fails_provenance_pre_shadow` |
| RECCT_A3_A1_BINDING | `::A1Binding`; `::_authenticated_orientation_binding` | accepted A1 source/result/version/schema/mint, role-instance table and opposite opaque handle source/receiver records authenticate; coordinated role swaps reject | `test_mutated_a1_binding_and_involution_fail_before_shadow_calls` |
| RECCT_A3_CREDIT | `::CreditObservation`; `::bind_credit_tensor`; `::_negative_bce` | exact detached negative-BCE q values, frozen LR/RL formulas/order, finite quarter-weight entries | `test_exact_common_bank_fixture_preserves_every_frozen_cap_and_boundary`; `test_credit_fixture_rejects_misordered_or_unbound_source` |
| RECCT_A3_BANK | `::PotentialCell`; `::CellLedger`; `::HiddenImmutableBank`; `::run_common_bank_audit` | exact four stored plus four reverse recomputations; own-cell bitwise equality; common ancestry/RNG isolation; original/bank immutability; no 00/11/live update | `test_exact_common_bank_fixture_preserves_every_frozen_cap_and_boundary`; `test_mutated_recomputation_is_rejected_by_componentwise_bank_gate` |
| RECCT_A3_FIREWALL | `::SelectorView`; `::AccessTrapSelectorView`; `::_invoke_selector` | selector input contains only C/tie; balanced reads tie only; outer harness binds bank after pointer return | `test_selector_interface_is_narrow_and_forbidden_access_fails_closed` |
| RECCT_A3_SENTINELS | `::SENTINEL_CASES`; `::run_sentinel_manifest` | exact 12 cases x 3 calls, formula/tie/swap/sign invariants and fail-closed access proxies | `test_sentinel_manifest_has_exact_formula_ties_swaps_and_sign_invariance` |
| RECCT_A3_SCHEMA | `::A3Result`; `::_derive_counts`; `::validate_a3_result`; `::BRANCH_PRECEDENCE` | exact identity/branch; counts rederive from retained partial/full activity, call, equality, selector and sentinel evidence | `test_result_validator_rejects_identity_count_and_evidence_mutations`; `test_midstream_call_failure_retains_partial_activity_and_ledgers` |
| RECCT_A3_RUNNER | `scripts/run_recct_a3_common_one_port_update_bank_noninterference.py` | help is inert; technical fixture makes zero claim-bearing calls; registered path requires `--source-dto` or selects provenance failure before shadows; output is create-only | `test_registered_runner_without_existing_source_dto_fails_provenance_pre_shadow`; runner help/technical proof below |

## Bounded implementation proof and reserved execution

The fixed audit has `K_search=0`, no rollout or hypothetical environment
transition, two sealed capsules, four stored calls, four reverse
recomputations, six selector commitments, six order checks and 36 pure
sentinel calls. It is constant finite evidence below the project ceiling.

Implementation-worker focused proof:

```text
11 passed in 4.79s
```

The mutation cases reject a changed A1 source identity, foreign opaque handle,
misordered/unbound credit fixture, altered recomputation, forbidden selector
field, result identity, activity count and missing sentinel ledger.
It also checks coordinated role swaps and retains four completed ledgers plus
the fifth indeterminate attempt after an injected midstream failure. The runner
rejects an occupied output before building the claim fixture and, without a
source DTO, emits the exact provenance branch with zero shadows.

Technical-only runner proof used separately named technical members, capsules,
frame, learner generations and initialization seeds; it returned two distinct
technical capsule digests, the first canonical key, zero prohibited selection
reads, zero credit opens and zero claim-bearing calls. Focused tests likewise
used only that disjoint technical pair, never `build_registered_pair`.
`py_compile` and `--help` passed. The implementation worker did not supply
`--output`; therefore the registered A3 pair was never constructed by a test or
audit and no public result was created.

Reserved CPM command shape if an eligible pre-existing immutable DTO is later
available:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_recct_a3_common_one_port_update_bank_noninterference.py --output <new-isolated-result-path> --source-dto <existing-git-bound-dto>
```

Even a future passing branch certifies only finite construction and
noninterference for this one selected pair. It supplies no signed-credit
validity, policy value, learning, natural incidence, LR/RL equality,
generalization, B1 repair, automatic B2 license, C or Pro claim.

## A3 prospective provenance-failure publication (source 3267ba1ab60785540de0cf2a74a4315c12045a53)

The registered publication records branch `A3_PROSPECTIVE_PAIR_CAPSULE_OR_CREDIT_PROVENANCE_FAILURE`.
The first failure was no pre-existing immutable registered credit-source DTO.
Exactly one named audit was observed; pair/capsule/shadow/optimizer/cell/
selector/sentinel/runtime/retry/open counts are all zero, and no synthetic
credit was created. Source readiness is `r3`; the operator is `ERROR` solely
because this branch does not evaluate. The raw result is byte-identical to
the authoritative source log at
`recct_a3_common_one_port_update_bank_noninterference_3267ba1a_r1/raw_result.json`.

Nonclaims: this branch provides no construction, noninterference, signed-credit
validity, policy-value, learning, natural-incidence, LR/RL-equality,
generalization, B1-repair, C, or Pro claim. It is not a B2 license; B2 is
forbidden from being inferred or authorized from this provenance failure.
