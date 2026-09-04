# VQFP/FRRIE ActionCodec impossibility result intake — 2026-08-31

## Decision

- Baseline: `1bea5cc9b0780a8986fb66df65976de376eb57e6`
- Result: `EXACT_STRUCTURAL_IMPOSSIBILITY`
- Certificate: `VQFP_FRRIE_ONE_STEP_ACTION_CODEC_IMPOSSIBILITY_V1`
- Direction-local effect: recommend `CLOSE` standalone VQFP
- Portfolio authority: Root alone records lifecycle in `PORTFOLIO.md`

The explicit PARKED reactivation condition fails. No deterministic lossless one-decision
`ActionCodec` exists between the exact VQFP allocation domain and the current FRRIE role-masked
categorical action domain. This is a finite interface theorem, not scientific polarity, runtime
failure, or unavailable implementation.

Retain only FRRIE-owned output-disconnected LR, marginal-heap, `MARG0`, utility, MASS/MASS-P, and
reassociation control provenance. Historical VQFP results transfer no polarity.

## Finite certificate

VQFP fixes one decision per row and

```text
A_N = {n in nonnegative integers^N : sum_i n_i=120},  a_i=n_i/600.
```

VQFP rosters are `{4,6,8,12}`; FRRIE rosters are `{6,9,15,21}`, so `N=6` is the sole shared
registered roster. At one FRRIE step, four surveyors each have three legal actions and two relays
each have four. For every balanced stable entity order,

```text
|A_6| = C(125,5) = 234,531,275
|C_6| = 3^4 * 4^2 = 1,296
gap   = 234,529,979.
```

If `decode(encode(n))=n` for every allocation, `encode` is injective. The cardinalities forbid such
an injection. Every total encoder has a collision fiber of at least
`ceil(234,531,275/1,296)=180,966` allocations. Even the finite subset

```text
{(a,b,120-a-b,0,0,0) : a>=0, b>=0, a+b<=120}
```

has `C(122,2)=7,381` members, more than the entire native one-step codomain. VQFP rosters
`{4,8,12}` additionally have no roster-preserving FRRIE target.

## Strongest contradiction

An abstract communication code can rank allocations, write the rank in base `1,296`, and unrank
it. It needs three native symbols because

```text
1,296^2 < 234,531,275 <= 1,296^3.
```

That code is lossless data compression but not the required seam. It replaces one decision with
three host steps, advances state and observation chronology, consumes extra action/work and
tape/RNG coordinates, and executes SCAN/UPLINK/LISTEN/FORWARD/HOLD rather than applying all
`n_i/600` commands simultaneously. It therefore violates entity/order/tape/RNG/work and native
endpoint preservation. A twelve-step padding or a history/logit/tape side channel has the same
defect. For corresponding twelve-step action sequences, the original cardinality contradiction
also exponentiates to `|A_6|^12>|C_6|^12`.

The VQFP one-step `U/Z` endpoint and FRRIE terminal delivery/waste endpoint have different native
consequence maps. Pathwise endpoint equality is unreachable after the round-trip contradiction; no
native or stochastic run is needed.

## Engineering conformance

The isolated package at `experiments/candidates/vqfp_frrie_action_codec/` exports the hypothetical
`ActionCodec` protocol and exact preservation contract, but deliberately supplies no implementation.
It binds an actual balanced role tuple, simultaneous `a_i=n_i/600`, unchanged categorical meaning,
no extra inputs or steps, round trip, and pathwise endpoint equality. Its certificate recomputes all
counts and rejects tampering or nonshared rosters.

Focused tests at `tests/experiments/candidates/vqfp_frrie_action_codec/` cover source literals,
balanced entity-order permutations, physical commands, side-channel rejection, exact counts, the
three-symbol contrary capacity fact, and certificate tampering. No FRRIE file was changed for this
object. The isolated suite passed `12` tests; the isolated suite plus FRRIE's focused VQFP-control
tests passed `16`. No native, training, result, provider, or other external-effect command ran.

## Claim ceiling and next discriminator

The result proves only current-domain incompatibility at baseline `1bea5cc9`. It does not test VQFP
efficacy, FRRIE learning, arbitrary categorical hosts, or multi-step communication.

Reconsider only a prospectively frozen FRRIE action revision exposing a one-step allocation or
equivalent multidiscrete ABI with adequate cardinality, roster-preserving physical keys, an exact
inverse, unchanged tape/RNG/work, and a pathwise endpoint homomorphism for the retained controls.
That would be a new FRRIE revision or successor, not a reopening of standalone VQFP.

## Evidence

- `DIRECTION.md`
- `IMPLEMENTATION_THRESHOLD.md`
- `VQFP_PROOF_SIZED_ASSOCIATION_GATE_R01_SCIENCE_CARD_20260829.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/host.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/contracts/core.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/contracts/vqfp_controls.py`
- `experiments/candidates/vqfp_frrie_action_codec/`
- `tests/experiments/candidates/vqfp_frrie_action_codec/`
