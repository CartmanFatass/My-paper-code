# VQFP implementation threshold

Status: `NO_STANDALONE_CODE`

## Decision

VQFP transfers exact control definitions only into FRRIE. Historical VQFP/SGSP packages remain
provenance and cannot become direct imports or runtime dependencies. Existing proofs establish exact
measure, LR, oracle, and reassociation totality, not FRRIE-native control value.

## FRRIE-owned surface

```text
experiments/candidates/finite_resource_relational_inductive_efficiency/
  contracts/vqfp_controls.py
  fixtures/vqfp_controls_v1.json

tests/experiments/candidates/finite_resource_relational_inductive_efficiency/
  test_vqfp_controls.py
  test_dependency_firewall.py
```

Use exact `Fraction` arithmetic, `Q=120`, deterministic physical-coordinate tie keys, and
complete-only fixtures. Imports from historical `vqfp_vnpa_r03` or SGSP packages and native loaders
are forbidden.

## Exact controls

For even `N`, let `P(i)=(i+N/2) mod N` and `lambda_i=v_{P(i)}`. Preserve endpoint cells, `m_i`,
`d_i`, coordinates, tie keys, coefficients, tapes, and RNG.

\[
w_i^T=v_iB_i,\qquad w_i^{T-P}=\lambda_iB_i,
\]

\[
w_i^{MASS}=m_i=v_id_i,\qquad w_i^{MASS-P}=\lambda_i d_i.
\]

`MASS-P` is not `m_{P(i)}`. For a higher-better native return:

\[
D_{assoc}=(J_T-J_{T-P})-(J_{MASS}-J_{MASS-P}).
\]

FRRIE's relational `SEMANTIC_COLUMN_ROTATE` is a different intervention and cannot substitute for
this physical-measure cut. On uniform fields, `T=MASS` and `T-P=MASS-P`, hence `D_assoc=0`; retain
this exact absorption witness.

Focused tests cover LR legality/ties, command conservation, half-cycle involution and derangement,
measure-multiset preservation, exact MASS-P formula, unchanged endpoint inputs, DID ordering,
uniform-field absorption, and the dependency firewall.

## Unique blocker

`FRRIE_ACTION_SEAM_ABSENT`: VQFP emits integer allocation vectors with `sum(n)=120`; the current
FRRIE source host executes sequential role-masked categorical actions. No lossless `ActionCodec` or
equivalent native seam exists.

Closure requires a fresh FRRIE-owned seam proving for every admissible command:

```text
decode(encode(n)) == n
```

together with injectivity, legal native actions, preserved entity/order/tape/RNG/work semantics, and
equality between allocation and native endpoint values. Until then, marginal heap and reassociation
DID remain output-disconnected fixtures and cannot satisfy native competence or support a result
claim.

After closure, the exact marginal heap is mandatory whenever the prospective resource law admits
it. Only a frozen resource boundary that genuinely excludes it can support amortized allocation
efficiency.

## Operation and claim ceiling

Any continuation of the retained provider operation is same-operation observation only; it cannot
authorize send, retry, replacement, enumeration, or CM work. Its terminal fact is lifecycle
provenance, not an implementation unlock.

The current claim ceiling is exact control conformance. Even later native evidence can support only
finite-resource allocation-control value on frozen FRRIE cells, never standalone VQFP, learned
Voronoi necessity, arbitrary geometry, churn, UAV, safety, or deployment.

## Evidence

- `DIRECTION.md`
- `VQFP_PROOF_SIZED_ASSOCIATION_GATE_R01_SCIENCE_CARD_20260829.md`
- `VQFP_FERL_ANALYTIC_CONTAINMENT_R03_G_FIRST_PAPER_THEOREM_RETURN_20260823.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/IMPLEMENTATION_THRESHOLD.md`
