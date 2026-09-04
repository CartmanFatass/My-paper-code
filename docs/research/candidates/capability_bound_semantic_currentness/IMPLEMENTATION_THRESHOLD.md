# CBSC implementation threshold

Status: `EXACT_RESULT_COMPLETE`

This threshold defined the specification-conformant implementation. The sole registered enumeration
completed on 2026-08-30 and is recorded in `CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md`; it must
not be rerun. Any learned comparison is a separate prospective object and Root retains Portfolio
lifecycle responsibility.

## Scientific object

Test whether independently varied OWNER continuity, semantic refresh, binding-gated capability, and
receiver-addressed payload content change the unique net-optimal `SERVE / REFRESH /
SAFE_FALLBACK` action.

RAW is a conformance ceiling: CBSC must match the unrestricted same-primitive raw-history optimum on
every world. A positive CBSC-minus-RAW residual is an invalid information/work mismatch. The maximum
positive claim is exact one-opportunity protocol value of current receiver-addressed content plus a
current execution capability under the frozen cost law. No representation, learning, security,
proactive-acquisition, MARL, variable-population/lifetime, UAV, safety, or deployment claim follows.

## Exact factorial host

Each matched superblock crosses:

```text
OWNER    {LIVE, BROKEN}
SEMANTIC {PERSIST, REFRESH}
BINDING  {AUTHENTIC, WHOLE_CARRIER_REASSOCIATED}
ACCESS   {OPEN, BINDING_GATED}
PAYLOAD  {RECEIVER_CORRECT, SWAPPED, NATIVE_NEUTRAL}
```

There are 48 scientific cells. Each cell has 128 exact nuisance twins over receiver, old/current
bits, donor bit, public `z_0/z_1`, and presentation permutation: 6,144 worlds per controller arm.
Reassociation deranges intact whole carriers within pretreatment strata and never edits fields.
Strata exclude emitted index, authorization result, action, and reward. Physical receiver keys carry
truth; slots are nuisance. There is no membership change or censoring.

Order:

1. Commit focal need, physical receiver, old content, and phase law.
2. Issue immutable correct, swapped, and neutral bodies and whole carriers.
3. Independently commit OWNER predecessor status and semantic epoch. `PERSIST` keeps current content;
   `REFRESH` publicly marks epoch mismatch while new content stays hidden until refresh.
4. Commit the access law.
5. At primitive `t=0`, choose once; authorization is not leaked beforehand.
6. `SERVE`/fallback terminate at `t=0`; `REFRESH` consumes the opportunity, reveals current content,
   and completes correct service at `t=1`.

No passive reveal, wait, second refresh, or proactive diagnostic probe exists.

## Arms and information parity

- `CBSC_RULE`: reads primitive receipt/body/OWNER/semantic/binding/public protocol facts.
- `RAW_EXACT_OPTIMUM`: identical primitives, unrestricted exact finite computation.
- `OWNER_BLIND_OPTIMUM`: retains content/capability but masks predecessor history and optimizes the
  frozen uniform LIVE/BROKEN mixture.
- `PREDICTIVE_INDEX_CAPABILITY_NULL`: same receiver/address/epoch information, bytes, validation,
  lookup and timing, but no nonfungible content-bound authorization.
- `RESET_EXACT`: removes cached content and uses the same single reactive refresh.
- `HARD_OPEN`: diagnostic cached-body use without currentness/address conditioning.

No factorial label is visible. Every arm executes the padded read, history scan, and authorization
lookup. The index is pathwise equivalent in OPEN; its inability to execute in GATED is the stipulated
capability treatment, not an information advantage.

## Exact costs and endpoints

Use `Fraction` arithmetic. Freeze common validation/read `1/8`, retained service `1/8`, refresh scan
`1/4`, refresh delay `1/4`, new-content ingestion `1/8`, gross correct service `+1`, wrong service
`-1`, unauthorized attempt `-1/2`, and safe fallback `0`.

Required net values are authorized current service `3/4`, successful refresh `1/8`, safe fallback
`-1/4`, unauthorized attempt `-3/4`, and wrong direct service `-5/4`; RESET refresh is `1/4`. In a
neutral opportunity, fallback must be uniquely optimal. Endpoints are first action, exact terminal
team return, and reconciled gross-plus-cost ledger. Freeze material margin `delta=1/4`.

Acceptance requires CBSC/RAW rowwise identity, currentness and correct/swapped action/value
contrasts, zero binding effect in OPEN, a positive declared capability difference-in-differences in
the gated usable cell, positive OWNER-information and retained-content value, and neutral payload
never opening direct service.

## Determinism and publication

Scientific factors are exhaustive; scientific RNG, transitions, optimizer updates, seeds, and
checkpoints are zero. Opaque nuisance IDs use counter-addressed `CBSC-F0-V1`; controller/intervention
fields never enter paired exogenous addresses. Global Python, NumPy, and Torch RNG are forbidden.
Canonical row sorting makes traversal/worker order byte-invariant. Publication is atomic,
create-only, and rejects partial or pre-existing output.

## New implementation surface

```text
experiments/candidates/capability_bound_semantic_currentness/
  __init__.py
  schema.py
  registered.py
  rng.py
  factorial.py
  policies.py
  artifact.py
  run.py
  schemas/cbsc_host_spec_v1.schema.json
  schemas/cbsc_exact_factorial_result_v1.schema.json

tests/experiments/candidates/capability_bound_semantic_currentness/
  test_schema_and_factorial.py
  test_policies_and_equivalence.py
  test_clock_cost_payload.py
  test_rng_and_order.py
  test_artifact_and_cli.py
```

Public API:

```python
registered_spec() -> RegisteredSpec
validate_registered_spec(spec) -> SpecAudit
enumerate_worlds(spec) -> tuple[World, ...]
controller_view(world, policy) -> ObservationKey
solve_policy(worlds, policy) -> ExactPolicy
evaluate_registered(spec) -> CompleteResult
validate_complete_result(result) -> None
write_complete_result(manifest_path, result) -> Path
```

JSON rationals are `[numerator, denominator]`. The complete result records identities, manifests,
support/pairing counts, action-value vectors, decisions, cost ledgers, exact contrasts, invariant
audits, and interpretation boundary. Historical DEARS/FSBS/EOCIV packages are references only and
must not be imported.

## CLI and focused checks

Non-result inspection:

```text
python -m experiments.candidates.capability_bound_semantic_currentness.run configuration
```

Future sole result shape, not authorized here:

```text
python -m experiments.candidates.capability_bound_semantic_currentness.run registered \
  --manifest temp/directions/capability_bound_semantic_currentness/exp/<run-id>/manifest.json
```

Expose no seed, arm subset, payoff override, threshold, smoke/full, retry, resume, or checkpoint
flags. Focused tests establish exact cell/world counts, no-fixed-point reassociation, access truth,
no pre-action leakage, RAW containment, OPEN equivalence, exact cost reconciliation, action twins,
unique optima, order-invariant serialization, no global RNG, and atomic complete-only output. The
`configuration` path emits zero question-relevant values and tests must not call the registered
enumerator.

## Result branches and stop

Branches are `VALID_NARROW_PROTOCOL_VALUE`, `INDEX_ABSORBS`, `RAW_MISMATCH_OR_TIE`,
`NO_CAPABILITY_EDGE`, `NO_CONTENT_EDGE`, and `INVALID`. Preserve the first failing witness. Do not
rerun, retune, change costs/margins, or enter learning after the exact enumeration. A positive gate
permits only a separately frozen learnability question.

## Evidence

- `DIRECTION.md`
- `docs/research/portfolio/decisions/2026-08-30-fifteen-direction-consolidation.md`
- `docs/research/legacy/directions/dual_epoch_receipt_survival/DIRECTION.md`
- `docs/research/legacy/directions/finite_semantic_boundary_support/DIRECTION.md`
- `docs/research/candidates/eociv_lite/DIRECTION.md`
