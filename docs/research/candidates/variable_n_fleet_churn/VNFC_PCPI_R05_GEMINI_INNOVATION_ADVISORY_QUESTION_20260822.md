# VNFC PCPI revision-05 independent Gemini innovation advisory

Act as an independent divergent scientific innovator. Treat the prospective
object `VNFC-PCPI-SCIENCE-20260822-05` as result-blind. You are not given any
other reviewer's answer, disposition or reasoning. Do not seek agreement,
mathematical closure, implementation approval or a portfolio decision. Seek
mechanisms, concrete counterexamples, shortcut explanations, overlooked
regimes, target-realistic controls and a toy-to-UAV bridge.

## Frozen prospective object

The target is a finite two-zone post-loss UAV command problem with one shared
policy across roster sizes. Sixteen replicate roles each contain 36 fresh base
states:

```text
N in {3,5,7}
failed zone in {1,2}
support class in {ETA,RADIO,COUPLED}
copy in {0,1}.
```

The 576 states are constructed before learning from one bounded,
counter-addressed, treatment-blind generator. For each coordinate, the
generator samples `N+1` records from eight public records `UAV1,...,UAV8`,
simulates a 120-second legal demand/obstruction/command prehistory, removes the
acquired executor of the specified failed zone at `t=0`, and retains the first
of attempts `0,...,65535` meeting frozen public support/tie/flip/swap
predicates. Prehistory commands are enumerated by public-tag bytes, not by
transport-key order. Exhaustion and structural invalidity have a separate
pretraining terminal form; no model output can select or top up a state.

Each active physical record has a state-local 256-bit stable transport key.
The key is excluded from learned inputs and teacher features. Within one state
it only transports rows through presentation permutations, inverse-maps
outputs to physical records, defines canonical reduction/presentation order,
resolves genuine exact ties and supplies the complete physical-command byte
identity. A retained treatment-blind map `PUBLIC_TAG_s(key)=UAVj` is used only
for fixture registration and cross-state choice diversity.

For the four fixed failure-relative tokens

```text
[EXEC_failed, RELAY_failed, EXEC_intact, RELAY_intact],
```

cross-state diversity uses an exact `CHOICE_SIGNATURE`: `0x00` for an unfixed
null, `0x01 || ASCII("UAVj")` for an unfixed assignment to public record
`UAVj`, and `0x02` when an en-route commitment already fixes the token. It
contains no base list, transport key, fixed occupant, route time, presentation
slot or failed-zone label. Full stable-key command bytes, not this signature,
govern every within-state equality and commutation test.

The treatment `PCPI-INV-MAPR` and comparator
`PCPI-FREE-PRESENTATION` share all observations, encoders, parameters,
initial homologous bytes, masks, token order, optimizer and logical work. A
shared agent encoder is pooled by elementwise mean and maximum; absolute
`ZONE1`, `ZONE2` and global encodings complete the state summary. Both arms
allocate the same learned presentation matrix `P in R^(7x8)` and compute

```text
pbar_N=(1/N)*sum_j P_j
r_j=P_j-pbar_N
c_j(alpha)=concat(pbar_N,alpha*r_j).
```

The invariant treatment fixes `alpha=0`; the free comparator fixes `alpha=1`.
The free family literally contains the invariant family by copying all
homologous bytes and zeroing exactly the eight first-layer residual-input
columns. Both score every active candidate and null for each token before legal
masking and injective removal.

The deterministic capability teacher chooses by ETA, safe-return margin and
radio capacity, with the stable key only as its final exact-tie coordinate. In
each `(replicate,N,failed-zone)` block it must make nondegenerate public-record
executor/relay and injective second-choice decisions; at each `(replicate,N)`
it must emit at least four public-record `CHOICE_SIGNATURE` values. Learned
competence uses the same public-choice diversity plus exact full-command
teacher matching.

Only `N={3,5}` enters 256 fixed full-batch supervised AdamW updates; `N=7`
and all final presentation rows remain untouched until final evaluation. Final
evaluation enumerates every `N!` presentation for every state. It checks exact
physical-command bytes, invariant-arm internal/matched-prefix commutation, and
free-arm output commutation. FEATURE-FLIP exchanges registered ETA/radio
features and requires state-action change. Post-scorer ROW-SWAP exchanges two
complete pre-mask score rows while preserving each recipient's public row and
mask and requires association-sensitive command change. Every sensitivity
qualification is separate at each `N` and support class.

The first-true result map can invalidate the static family, find capability
support nonidentified, retain the invariant decoder, select only the broader
free family, delete both current MAPR association/decoder paths, find finite-
budget optimization nonidentified or return a mixed nonidentification. A
positive result could support only exact finite-family presentation
commutation plus registered capability/sensitivity. It cannot establish task
return, post-loss recovery benefit, robustness, arbitrary `N`, repeated churn,
general invariance, a unique mechanism, distributed execution, safety,
deployment or flight value.

## Divergent innovation questions

Return one science-only advisory addressing all of the following:

1. Give the strongest concrete mechanism-level counterexample in which exact
   internal and physical-command presentation commutation holds but the policy
   still fails useful variable-roster coordination after a UAV loss.
2. Stress-test canonical stable-key reduction, inverse physical reassembly and
   deterministic key ties. What centralized identity or synchronization
   shortcut could survive the stated feature exclusion, and what smallest
   target-realistic alternative would expose it?
3. Stress-test `PUBLIC_TAG_s` and `CHOICE_SIGNATURE`. Can public-record
   diversity still reward a repeated behavioral template, roster composition
   artifact or fixed-token pattern rather than meaningful decoder diversity?
   Give one prospective diversity observable or control that would discriminate
   the shortcut without retrospectively changing r05.
4. Give the strongest treatment-blind generator or teacher-selection
   counterexample: a way that first-qualifying legal prehistories and frozen
   ETA/radio support predicates could concentrate on easy or artificial
   coordination states despite model-independent acceptance.
5. Challenge the invariant-in-free containment and matched finite optimization
   opportunity. Identify any mechanism by which residual-zero embedding,
   copied initialization, canonical reductions or AdamW geometry could still
   make the comparison scientifically misleading without violating literal
   function-class containment.
6. Show how FEATURE-FLIP or post-scorer ROW-SWAP could pass through a shortcut
   that is neither useful state capability nor meaningful record-association.
   Propose the cheapest prospective intervention that distinguishes it.
7. Identify the most important variable-`N` failure missed by a static
   post-loss state family with exhaustive presentation permutations—for
   example in-episode joins/leaves, delayed membership knowledge, distributed
   key disagreement, communication loss or reassignment hysteresis—and state
   exactly why permutation commutation is insufficient there.
8. Give one credible target-UAV scenario in which a common decoder across
   roster sizes matters operationally. Map roster change, observations,
   commands, coordination failure, physical benefit and the decisive missing
   direct-value endpoint. Name the smallest future simulator experiment that
   would test this bridge without claiming flight or safety.
9. Propose one genuinely different mechanism family that addresses the same
   post-loss variable-roster problem—such as decentralized role negotiation,
   graph matching, auction/market assignment, communication-equivariant set
   control or another concrete alternative—and name the single discriminator
   that most sharply separates it from PCPI.
10. End with a `DELETE / RETAIN / ADD` ledger for mechanisms and controls, plus
    the one highest-information prospective discriminator before any expensive
    direct-value panel.

Treat every proposed change or experiment as advisory only. Do not review code,
tests, repository state, runtime, cost, provider mechanics, another direction
or portfolio priority. Do not authorize construction, training, evaluation,
compute, deployment or flight.

Conclude with exactly these labeled fields:

```text
MECHANISM_HYPOTHESIS=<one concise causal mechanism>
STRONGEST_COUNTEREXAMPLE=<one concise counterexample>
STRONGEST_SHORTCUT=<one concise shortcut>
TARGET_UAV_BRIDGE=<one concise target-to-endpoint bridge>
DELETE=<mechanisms or controls to remove, or NONE>
RETAIN=<mechanisms or controls to preserve>
ADD=<prospective mechanisms or controls to consider, or NONE>
HIGHEST_INFORMATION_NEXT_DISCRIMINATOR=<one prospective discriminator>
MAXIMUM_DEFENSIBLE_ADVISORY_CLAIM=<one bounded claim>
```
