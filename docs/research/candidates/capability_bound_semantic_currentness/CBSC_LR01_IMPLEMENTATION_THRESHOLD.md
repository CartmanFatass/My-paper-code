# CBSC-LR01 finite-resource learnability threshold

Status: `RESULT_BLIND_CONTRACT_FROZEN_NOT_IMPLEMENTED`

`CBSC-LR01` is a new prospective object. It neither reopens nor changes
`CBSC-EXACT-FACTORIAL-V1`, its accepted result, costs, actions, or interpretation. The existing
`IMPLEMENTATION_THRESHOLD.md` and exact artifact remain immutable evidence.

## Direct observations and inference boundary

Direct observations are:

- the accepted exact artifact has 48 scientific cells, 128 nuisance worlds per cell, unique native
  actions, minimum selected-action margin `3/8`, and exact rowwise equality between CBSC and the
  same-primitive unrestricted RAW optimum;
- the existing CBSC package has no trainable learner, optimizer, checkpoint, selection, or learned
  result path;
- its current `controller_view` includes target-proximal derived predicates and transparent
  structural identifiers, so it is not the RAW feature tensor for this learned object; and
- EOCIV B2's content-separating encoder caused a much larger payload-conditioned action-kernel
  response than raw bytes but did not produce a stable positive correct-versus-swapped or
  correct-versus-neutral native-return contrast.

The prospective inference is narrower than the exact result. Exact containment does not preclude a
finite-budget advantage for one named training procedure, but it precludes representation necessity
or oracle superiority. The EOCIV observation makes native regret, not representation response, the
endpoint. Because the exact CBSC rule is already known, a structured-versus-RAW result alone cannot
separate semantic alignment from task-aligned compilation or conditioning; the deranged structured
arm and capability-specific interaction are therefore conclusion-bearing controls.

## Question and non-goals

At the fixed resource ladder below, does a lossless typed CBSC codec reduce held-out native regret
relative to both a competent dense RAW parameterization and an equal-work deranged semantic codec?

This is a full-information offline action-value assay. Each context is reset and executed once under
each of `SERVE`, `REFRESH`, and `SAFE_FALLBACK`; the three observed exact terminal returns form its
Q-vector. It does not test partial-feedback bandit exploration, on-policy data acquisition, credit
assignment, proactive probing, recurrence, communication, coordination, or partner co-adaptation.

There are always two physical receivers. Carrier objects and presentation slots are not agents.
There is no join, leave, rejoin, replacement, censoring, survivor-state transfer, or variable
lifetime. `SERVE` and `SAFE_FALLBACK` terminate at primitive `t=0`; `REFRESH` terminates at `t=1`.
Credit is the exact undiscounted ledger sum with `gamma=1`, no bootstrap and no reward
normalization.

## Canonical 112-bit primitive tensor

The sole pre-codec tensor is 112 bits, serialized least-significant bit first. Thirteen unsigned
eight-bit fields occupy offsets `0, 8, ..., 96` in this exact order:

| Offset | Field |
| ---: | --- |
| `0` | `physical_receiver` |
| `8` | `owner_predecessor` |
| `16` | `owner_current` |
| `24` | `body_epoch` |
| `32` | `current_epoch` |
| `40` | `associated_carrier_issued_to` |
| `48` | `execution_carrier_issued_to` |
| `56` | `body_addressed_receiver` |
| `64` | `payload_source_receiver` |
| `72` | `carrier_nonce` |
| `80` | `body_nonce` |
| `88` | `presentation_slot` |
| `96` | `public_phase` |

The final flags are:

| Bit | Field |
| ---: | --- |
| `104` | `focal_need_active` |
| `105` | `access_binding_gated` |
| `106` | `body_native_neutral` |
| `107` | `body_content_bit` |
| `108` | `focal_need_bit` |
| `109` | `public_z0` |
| `110` | `public_z1` |
| `111` | `presentation_flip` |

Scientific cells use codes `o,s,b,a in {0,1}` and `p in {0,1,2}` for, respectively,
`LIVE/BROKEN`, `PERSIST/REFRESH`, `AUTHENTIC/REASSOCIATED`, `OPEN/GATED`, and
`CORRECT/SWAPPED/NEUTRAL`. Their canonical index, with payload fastest, is

```text
cell = ((((o * 2 + s) * 2 + b) * 2 + a) * 3 + p).
```

For nuisance slot `q in {0,...,15}`, define:

```text
r    = q & 1
pres = (q >> 1) & 1
old0 = (q >> 2) & 1
old1 = (q >> 3) & 1
z0   = ((q >> 1) XOR (q >> 2)) & 1
z1   = ((q >> 1) XOR (q >> 3)) & 1.
```

The sole uint8/sentinel law is:

```text
physical_receiver = r
owner_predecessor = 16 + 2 * ((q >> 2) & 1)
owner_current = owner_predecessor                    if LIVE
                owner_predecessor + 1                if BROKEN
body_epoch = 32 + 2 * ((q >> 3) & 1)
current_epoch = body_epoch                           if PERSIST
                body_epoch + 1                       if REFRESH
associated_carrier_issued_to = r                     if AUTHENTIC
                                 1-r                  if REASSOCIATED
execution_carrier_issued_to = r                      if OPEN
                              associated_carrier_issued_to if GATED
body_addressed_receiver = execution_carrier_issued_to
payload_source_receiver = 255                        if NEUTRAL
                          execution_carrier_issued_to if CORRECT
                          1-execution_carrier_issued_to if SWAPPED
body_content_bit = 0                                 if NEUTRAL
                   old[payload_source_receiver] XOR z[payload_source_receiver] otherwise
focal_need_bit = (old[r] if PERSIST else 1-old[r]) XOR z[r]
presentation_slot = 128 + (r XOR pres)
public_phase = 144 + ((z0 << 1) | z1).
```

Here `old[0]=old0`, `old[1]=old1`, `z[0]=z0`, and `z[1]=z1`; the source-indexed expression is never
evaluated for sentinel `255`. Flags 104--111 are the Boolean values named in the table, with
`focal_need_active=(p != NEUTRAL)`, `access_binding_gated=(a == GATED)`,
`body_native_neutral=(p == NEUTRAL)`, and `presentation_flip=pres`.

For panel block index `block` and slot `q`, nonces are:

```text
carrier_nonce = 64 + ((q + block) mod 16)
body_nonce    = 96 + ((q + block + shift) mod 16)

shift MAIN/TRAIN       = 3
shift MAIN/EVAL        = 11
shift COMPETENCE/TRAIN = 5
shift COMPETENCE/EVAL  = 13.
```

The schema rejects every noncanonical value. The tensor contains no arm or payload-role label;
world, nuisance, body, or carrier ID; derived equality, match, correctness, permission, or
optimal-action predicate; authorization outcome; reward; action value; future content; result
field; or post-action state. Scientific cell identity determines the environment population but is
not appended to the learner tensor. Every tensor field is available before the action. All three
arms receive exactly this tensor and therefore the same primitive sigma-field.

## Three lossless 49-XOR codecs

One shear operation is `target_bit ^= source_bit`. Codec output width remains 112 bits. Inversion
applies the same shear list in reverse order. Every implementation and artifact records the literal
ordered pair list and proves exact inversion on every legal MAIN and COMPETENCE input.

For `STRUCTURED_CBSC`, for every `b in {0,...,7}`, apply these six pairs in the displayed group
order, followed by the flag pair:

```text
(16+b,  8+b)
(32+b, 24+b)
(40+b,    b)
(48+b,    b)
(56+b,    b)
(64+b,    b)
(107, 108)
```

This is `6 * 8 + 1 = 49` shears. It exposes only local typed relations; it does not compile the
final permission/correctness conjunction or an action.

For `STRUCTURED_SHAM`, use:

```text
(16+b, 24+b)
(32+b,    b)
(40+b,  8+b)
(48+b, 24+b)
(56+b,  8+b)
(64+b, 24+b)
(107, 109)
```

again for every `b in {0,...,7}` and then the flag pair. This is the frozen no-fixed-point
field-to-role derangement. It has the same graph, width, operation count, byte movement, and active
learner downstream as `STRUCTURED_CBSC`.

For `RAW_FLEX`, enumerate the 13 token-field offsets `0, 8, ..., 96` in order. Within each field,
enumerate the disjoint pairs `(offset+1,offset+0)`, `(offset+3,offset+2)`,
`(offset+5,offset+4)`, `(offset+7,offset+6)`, then take the first 49 pairs. This canonical
within-field Gray-like schedule is independent of semantic roles and results. It is not an adverse
random mixing.

RAW is unrestricted only within the frozen dense parameterization below. “Unrestricted” does not
quantify over every learning algorithm: such a meta-learner could run the structured codec itself,
making a universal structured-over-RAW claim incoherent.

## Common learner and optimization

Every arm uses the same fully dense FP32 ReLU Q-network:

```text
112 -> 160 -> 128 -> 32 -> 16 -> 3
```

It has exactly 43,395 active, output-connected trainable scalars and 43,056 dense forward
multiply-accumulates per context, before common activations and bias additions. Dead, frozen,
gradient-disconnected, or no-op padding cannot establish parameter or useful-work parity.

Within a paired block, parameter bytes are identical across arms. The final head is zero at update
zero, so the three policies and returns are identical and noncompetent before learning. There is no
dropout, recurrence, auxiliary head, auxiliary loss, semantic target, action mask, or arm-specific
normalization.

The three output coordinates and greedy first-maximum tie order are exactly
`(SERVE, REFRESH, SAFE_FALLBACK)`, matching the accepted exact action order. MAIN uses that order for
every finite tie. Update zero is intentionally common, tied, and noncompetent.

Optimization is FP32 Adam with `lr=1e-3`, `betas=(0.9,0.999)`, `eps=1e-8`, zero weight decay,
and global gradient-norm cap `1`. One update consumes 96 contexts and minimizes the arithmetic mean
MSE over the complete `96 x 3` Q-target matrix. There is no discount, bootstrap, target network,
return normalization, or result-dependent stopping.

## RAW capacity witness

Before any learning result, deterministically compile a sparse certificate inside the common
43,395-scalar architecture:

1. the first hidden layer prepares exact inversion of RAW's 49 disjoint shears and carries the
   oracle-relevant sources and flags;
2. the second hidden layer uses two-ReLU absolute-bit mismatches;
3. the third layer aggregates the six uint8 equalities, content equality, and carried need,
   gated-access, and neutral flags;
4. the fourth layer forms the open-serve, gated-serve, fallback, and active-need clauses; and
5. the output layer emits exact `0/1` one-hot logits for `SERVE`, `REFRESH`, and
   `SAFE_FALLBACK`.

The generated witness must have the unique oracle argmax and exact one-hot logits on every legal
MAIN and COMPETENCE TRAIN/EVAL context, stay within the same width and MAC ceiling, and contain no
unreachable required path. Its weights are a capacity certificate only: they may never initialize,
tune, select, or otherwise inform a learned arm. If the stated width/depth cannot realize this
construction, the object stops before learning for scientific recast; extra width or an approximate
“universal approximator” argument cannot silently replace the witness.

## Population, support, RNG, and exposure

The finite target population is uniform over the accepted 48 scientific cells and the registered
16 nuisance slots per split. Addresses are exactly:

```text
(CBSC-LR01,
 MAIN|COMPETENCE,
 block,
 TRAIN|EVAL,
 scientific_cell[0..47],
 nuisance_slot[0..15])
```

Each MAIN block contains 768 TRAIN contexts and a disjoint 768-context EVAL census. Each context's
three reset executions share every exogenous fact except the action. TRAIN and EVAL have the same
token-value support and complete receiver/presentation twins. Their fixed within-support identity
pairing is the exact nonce/shift law above: EVAL changes the body-to-carrier nonce pairing by eight
without creating an OOV value. The remaining nuisance construction and batch permutation are
counter-addressed, arm-independent, and fixed before execution.

MAIN block IDs are `CBSC-LR01-MAIN-B00` through `CBSC-LR01-MAIN-B23`; COMPETENCE block IDs are
`CBSC-LR01-COMP-B00` through `CBSC-LR01-COMP-B03`. An address is a canonical ASCII JSON array with
`ensure_ascii=true`, comma/colon separators, and no NaN. Its digest is SHA-256 and its counter value
is the first eight digest bytes interpreted as an unsigned big-endian integer. These digests are
counter-addressed RNG/order material only, never authenticity, admission, or scientific identity
evidence.

Hidden weights are addressed by the canonical array
`[CBSC-LR01-INIT,panel,block,parameter,flat_index]` and initialized as

```text
(2 * ((u64 + 0.5) / 2^64) - 1) * sqrt(6 / (fan_in + fan_out)),
```

then cast once to FP32. Hidden biases, output weights, and output biases are exact zero. Within a
block the same bytes initialize all three arms. Batch order uses the sorted complete digests of the
canonical addresses `[CBSC-LR01-ORDER,panel,block,epoch,batch_id]`. No ambient Python, NumPy, Torch,
device, or worker RNG may influence initialization, ordering, training, evaluation, or the
finite-panel decision.

Any TRAIN/EVAL primitive-tuple overlap, missing twin, token-support difference, action-target
omission, arm-dependent context/target/minibatch order, global RNG use, or resampling is `INVALID`.
No context is censored. A block is one registered design point; rows, action replicas, cells, and
checkpoints do not create independent replicates. The 24 blocks are deterministic rather than an
iid, exchangeable, or randomized sample from an unobserved population.

The MAIN panel has 24 paired blocks, batch size 96, and checkpoints
`U={0,8,16,32,64}`. Training always reaches update 64. Checkpoints are all consumed by the frozen
estimand and never selected. All three arms have identical context exposure, three-action target
exposure, parameter initialization, forward/backward calls, optimizer updates/state, logical
FLOPs/bytes, checkpoint opportunities, evaluation calls, workers, and threads.

Four disjoint RAW-only COMPETENCE blocks use the same finite-context and learner law for exactly 512
updates, eight times the MAIN update budget. Their addresses, initialization, and tapes are disjoint
from MAIN. They cannot select hyperparameters, initialize MAIN, or contribute to the primary
estimate.

## Native endpoint and estimands

Evaluation is greedy and adaptation-free. Native regret for arm `h`, block `b`, checkpoint `u`, and
evaluation subset `C` is

```text
R_h,b,C(u) = mean_w in C [V_star(w) - V(w, selected_action_h,b,u(w))].
```

`V_star` is the accepted unique exact optimum and `V` is the exact undiscounted action ledger. Use
exact rational ledgers and float64 reductions; learned logits and training remain FP32.

For `u=(0,8,16,32,64)`, define normalized trapezoidal area under regret:

```text
A_h,b,C = (1/64) * sum_k ((u_k-u_(k-1))/2)
                         * (R_h,b,C(u_(k-1)) + R_h,b,C(u_k)).
```

Let `E` be the complete `48 * 16` held-out census. The first two paired coordinates, where positive
favors the structured arm, are:

```text
d_SR,b = A_RAW_FLEX,b,E       - A_STRUCTURED_CBSC,b,E
d_SS,b = A_STRUCTURED_SHAM,b,E - A_STRUCTURED_CBSC,b,E
```

For capability specificity, restrict to receiver-correct, `PERSIST` cells. `GATED` and `OPEN` each
contain the four OWNER-by-BINDING cells and 64 held-out contexts per block. Define:

```text
psi_b = (A_SHAM,b,GATED - A_STRUCT,b,GATED)
        - (A_SHAM,b,OPEN - A_STRUCT,b,OPEN).
```

This subtracts any generic content/currentness or conditioning benefit visible in OPEN, where the
accepted exact result gives binding zero action/value effect. The common material margin is
`delta=1/32`, exactly one twelfth of the accepted `3/8` minimum selected-action margin. A single
final-budget contrast cannot replace the registered AUC or support a sample-complexity-rate claim.

## Support, competence, and causal-use gates

Before main contrasts are readable:

1. every codec inverse, input exclusion, token support, logical-work, active-parameter, RNG,
   checkpoint, target-ledger, and complete-panel audit passes;
2. the RAW capacity witness passes every legal address;
3. update-zero logits, actions, and returns are arm-identical, noncompetent, and feature-independent;
4. every TRAIN context has all three exact action targets and every EVAL context has the unique
   accepted optimum;
5. RAW at update 512 has zero regret and a strict predicted maximum for the unique oracle action on
   all `48 * 16` COMPETENCE EVAL contexts in each of all four blocks.

The common toggle base is `(LIVE,PERSIST,AUTHENTIC,GATED,CORRECT)`. The six pairs are fixed as
follows:

- neutral/active: the base versus its `NEUTRAL` payload twin;
- PERSIST/REFRESH: the base versus its `REFRESH` semantic twin;
- correct/swapped: the base versus its `SWAPPED` payload twin;
- OPEN/GATED: `(LIVE,PERSIST,REASSOCIATED,OPEN,CORRECT)` versus its `GATED` access twin;
- OWNER live/broken: the base versus its `BROKEN` OWNER twin; and
- AUTHENTIC/reassociated: the base versus its `REASSOCIATED` binding twin.

Receiver and presentation twins must preserve the oracle action and value. Failure of a definition,
support, parity, capacity, or RAW-competence gate is nonidentification or invalidity, never negative
CBSC evidence. Separately, the positive endpoint gate requires, in every one of the 24 MAIN blocks,
that `STRUCTURED_CBSC` at update 64 choose the greedy oracle action on at least 15 of 16 held-out
contexts on each side of every named pair and satisfy
`R_STRUCTURED,E(64) < R_common,E(0)`. Failure of this endpoint gate blocks only the positive branch;
it is not `INVALID` and does not hide the complete finite-panel result.

## Exact finite-panel decision and branch law

The 24 complete paired MAIN vectors `x_b=(d_SR,b,d_SS,b,psi_b)` are the whole registered decision
panel. They are deterministic counter-addressed design points, not iid draws, randomized treatment
assignments, or an exchangeable sample. Reproducibility does not create a sampling law. Therefore
this object has no bootstrap, randomization test, p-value, standard error, confidence interval,
coverage claim, seed-population mean, or unregistered-block extrapolation.

The exact decision statistics are

```text
D_SR_min  = min_b d_SR,b
D_SS_min  = min_b d_SS,b
PSI_min   = min_b psi_b
ABS_max_j = max_b abs(x_b,j)
D_SR_max  = max_b d_SR,b
D_SS_max  = max_b d_SS,b.
```

All 24 blocks must be present, finite, and paired; none may be omitted, replaced, resampled,
winsorized, retried, or reweighted. Every block and material outlier remains individually visible.

The finite bounds are exact. Per-world native regret is in `[0,11/8]`, hence every normalized AUC
on `E` is in `[0,11/8]` and `d_SR,b,d_SS,b` are in `[-11/8,11/8]`. On each receiver-correct,
PERSIST `OPEN` or `GATED` subset, regret and AUC are in `[0,1]`; each SHAM-minus-STRUCT advantage is
in `[-1,1]`, so `psi_b` is in `[-2,2]`.

For audit only, even a hypothetical iid law would not rescue the discarded 24-block bootstrap. A
one-sided Hoeffding bound with Bonferroni `alpha=0.05/3` would subtract

```text
(11/4) * sqrt(log(60)/48) = 0.8031640652  from d_SR and d_SS,
4       * sqrt(log(60)/48) = 1.1682386403 from psi.
```

Thus clearing `delta=1/32` would require observed means above approximately `0.8344140652` and
`1.1994886403`, respectively, before any additional assumptions. Those bounds do not apply here
because no iid law exists; they demonstrate why a model-free population claim at `n=24` is neither
licensed nor usefully powered.

The exact positive gate is attainable rather than oracle-impossible. In the correct/PERSIST GATED
subset, the common first-max update-zero policy has regret `21/32`; the matched OPEN regret is zero.
If STRUCT reaches zero regret at update 8 while SHAM remains at the common policy, trapezoidal AUC
leaves STRUCT only the first-interval triangle, giving
`psi=(15/16)*(21/32)=315/512 > 1/32`.

The first applicable branch is authoritative:

1. `INVALID`: information, codec, inverse, support, ledger, RNG, work, numerical, checkpoint,
   resource, completeness, or exact-panel audit fails, including any missing or replaced block.
2. `RAW_INCOMPETENT`: the constructive witness or any 512-update RAW competence block fails.
3. `NO_RESOLVABLE_HEADROOM`: all three arms attain zero regret on every held-out world at update 8.
4. `VALID_NARROW_CBSC_INDUCTIVE_BIAS`: all gates pass,
   `D_SR_min>1/32`, `D_SS_min>1/32`, and `PSI_min>1/32`, and the final structured endpoint gate
   passes.
5. `GENERIC_FACTORIZATION_OR_CONDITIONING`: `D_SR_min>1/32` but `D_SS_min<=1/32`.
6. `NO_CAPABILITY_SPECIFIC_ATTRIBUTION`: `D_SR_min>1/32` and `D_SS_min>1/32` but
   `PSI_min<=1/32`.
7. `PRACTICAL_EQUIVALENCE`: `ABS_max_j<=1/32` for all three coordinates.
8. `RAW_OR_SHAM_MATERIALLY_SUPERIOR`: `D_SR_max < -1/32` or `D_SS_max < -1/32`, so the relevant
   comparator beats STRUCT on every registered block.
9. `UNRESOLVED`: every other complete, valid panel, including failure of only the structured
   endpoint gate.

Invalidity, incompetence, resource exhaustion, or unresolved evidence supplies no lifecycle polarity.
A valid positive supports a later separately frozen online or natural-support discriminator.
`GENERIC_FACTORIZATION_OR_CONDITIONING` and `NO_CAPABILITY_SPECIFIC_ATTRIBUTION` deny the named
semantic-positive interpretation but do not turn a failed worst-block margin into equivalence. Practical
equivalence or valid RAW/SHAM material superiority supplies direction-local closure evidence at this
frozen ceiling while retaining the exact result. Root alone decides the Portfolio action. No result
may be rescued by changing a codec, seed, block, finite context set, target, optimizer, budget,
checkpoint, endpoint, margin, or decision law.

## Resource, publication, and forbidden paths

The complete bound is one CPU worker/thread, 30 wall minutes, 4 GiB peak memory, and 128 MiB durable
output. MAIN performs `24 * 3 * 64 = 4,608` Adam steps; COMPETENCE performs
`4 * 512 = 2,048`. A preflight that predicts or observes a bound violation stops before result
release. Runtime or engineering failure produces no scientific update and no automatic retry.

Implementation, if assigned, must use a separate learned package, manifest, checkpoint, result
schema, atomic complete-only writer, and CLI. It may reuse pure world construction and exact action
ledger semantics only through an explicitly audited adapter. It must not call, wrap, import as a
runner, or modify:

```text
experiments.candidates.capability_bound_semantic_currentness.run registered
enumerate_worlds(...)
evaluate_registered(...)
write_complete_result(...)
```

The accepted exact manifest is read-only provenance, never training data, a checkpoint, a model-
selection source, or an executable input. No exact-factorial schema, arm, artifact, or test may be
changed to host `CBSC-LR01`.

## Claim ceiling and evidence

The maximum positive claim is:

> On the frozen synthetic two-receiver one-opportunity 24-block panel, under the named full-Q
> supervision, codecs, dense network, Adam law, resource ladder, zero-selection rule, and paired
> exact finite-panel decision, the CBSC-aligned codec has lower finite-budget held-out native regret
> on every registered block than both the generic RAW codec and the equal-work semantic derangement,
> with a gated-specific residual.

It does not establish learned semantic discovery, necessity of the representation, superiority to
all RAW learners, asymptotic sample complexity, online exploration or credit, natural-frequency
value, proactive acquisition, security, authentication, MARL coordination, variable population or
lifetime, UAV transfer, safety, deployment, or general communication value.

Evidence:

- `DIRECTION.md`
- `IMPLEMENTATION_THRESHOLD.md`
- `CBSC_EXACT_FACTORIAL_RESULT_INTAKE_20260830.md`
- `experiments/candidates/capability_bound_semantic_currentness/factorial.py`
- `experiments/candidates/capability_bound_semantic_currentness/policies.py`
- `experiments/candidates/capability_bound_semantic_currentness/registered.py`
- `tests/experiments/candidates/capability_bound_semantic_currentness/`
- `docs/research/candidates/eociv_lite/PAYLOAD_CONTENT_LEARNABILITY_CODE_SCIENCE_INDEX.md`
- `docs/research/candidates/eociv_lite/PAYLOAD_CONTENT_LEARNABILITY_RESULT.json`
