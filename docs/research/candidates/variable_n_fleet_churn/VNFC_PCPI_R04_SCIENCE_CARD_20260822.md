# VNFC physical-command presentation-invariance science card

Owner: Portfolio-owned `direction:variable_n_fleet_churn_b4` EM  
Definition object: `VNFC-PHYSICAL-COMMAND-PRESENTATION-INVARIANCE-DEFINITION`  
Science revision: `VNFC-PCPI-SCIENCE-20260822-04`  
Treatment: `PCPI-INV-MAPR`  
Containing comparator: `PCPI-FREE-PRESENTATION`  
Authority: definition-only; no source, CM, coordinate materialization, model,
training, evaluation, lease, compute or activity

## Bounded question and purpose

The question is:

> In a fresh finite family of physically legal post-loss two-zone UAV states at
> `N={3,5,7}`, can one shared MAPR-compatible association and decoder path
> commute exactly with every presentation permutation at internal row,
> association-row and final physical-command surfaces while retaining
> nondegenerate teacher-command, state-action and row-association sensitivity?
> If not, can the strictly containing free-presentation family produce a
> competent, sensitive and exactly physical-command-invariant solution under
> matched information, tensor shapes, optimization and work, or should the
> current MAPR association/decoder route be deleted for this target before any
> new value panel?

This is an architecture-selection prerequisite. It asks no task-return,
post-churn recovery-value, robustness, safety or deployment question. Exact
presentation commutation plus action capability can make one decoder eligible
for a later direct-value object; it cannot itself establish value.

## Provenance isolation

The object has three noninterchangeable provenance classes:

| Class | Permitted content |
| --- | --- |
| `PUBLIC_TARGET_LAW` | Only the target-constitutive two-zone UAV records, graph, legal token grammar, flight/radio/energy/acquisition facts and raw public observation fields immutably incorporated by `VNFC_UAV_BOUNDED_POST_CHURN_RECOVERY_PUBLIC_PHYSICAL_LAW_BINDING.md`. |
| `MOTIVATING_CLOSED_RESULT` | Only the fact that the completed r09 package was invalid under its consistent-relabel control. This fact motivates the new question and supplies no row, threshold, estimate, parameter or claim. |
| `NEW_PCPI_DESIGN` | Every state coordinate, acceptance predicate, presentation permutation, model, teacher, training law, gate, branch and claim in this card. |

No r09 state, failed relabel row, public trace, score row, action, seed, master,
coordinate, checkpoint, optimizer, model byte, threshold, estimate or branch
may enter this object. No old VNFC row may be relabeled as a PCPI fixture. The
r03 Pro review informs only this prospective definition; no provider answer is
a state, label, threshold, gate, result or claim. Revisions r01, r02 and r03
remain immutable, mathematically unclosed, activity-free and permanently no-
resend. A future implementation must use a fresh namespace rooted at
`VNFC-PCPI-SCIENCE-20260822-04` and prove that no predecessor points into an old
VNFC result tree.

## Physical records, stable transport keys and public features

For one static post-loss state, let the active physical UAV key set be

```text
K={kappa_1,...,kappa_N},  N in {3,5,7}.
```

Each `kappa` is an immutable, unique 256-bit transport key assigned before any
presentation permutation. It identifies one physical UAV record only for:

1. transporting a row through a permutation;
2. reassembling row-indexed outputs into physical-key space;
3. establishing one canonical reduction order; and
4. breaking an exact deterministic score tie.

The key is never a model feature, loss input, learned embedding, attention
input, teacher feature, support label or endpoint. No prefix, integer rank,
hash bit or ordering statistic derived from the key enters a model tensor.

The independently frozen agent row has width 38 in this exact coordinate order:

```text
1-2    flight-class one-hot;
3      radio capacity;
4-18   node-or-directed-edge one-hot in the incorporated public table order;
19     remaining directed-edge time;
20     energy;
21-25  current-token one-hot [NULL,EXEC_failed,RELAY_failed,
                              EXEC_intact,RELAY_intact];
26     acquisition elapsed;
27-30  legal-token bits in failure-relative token order;
31-34  token ETAs in that same order;
35-38  safe-return energy margins in that same order.
```

Each labeled zone row has width 15 in this exact order:

```text
1      demand scalar;
2-3    obstruction one-hot [CLEAR,BLOCKED];
4-6    executor-state one-hot [VACANT,COMMITTED_OR_ACQUIRING,ACQUIRED];
7-9    relay-state one-hot [VACANT,COMMITTED_OR_ACQUIRING,ACQUIRED];
10     executor acquisition elapsed;
11     relay acquisition elapsed;
12     current delivered rate;
13     clearance remaining;
14     cumulative post-event zone demand;
15     cumulative post-event delivered zone data.
```

The global vector has width 4 in this exact order:

```text
1      post-event physical time;
2      roster scalar N/7;
3-4    failed-zone one-hot [ZONE1,ZONE2].
```

All model-visible entries are binary64. One-hot values and legal bits are exact
positive `0.0` or `1.0`. For a finite raw scalar `x`, define `clip(x,a,b)` as
`min(max(x,a),b)` and then perform the stated single division; both the clip
and division use binary64 round-to-nearest, ties-to-even, with no fused
contraction. Normalize exactly as follows:

```text
radio capacity and current delivered rate  clip(x,0,2)/2
remaining directed-edge time               clip(x,0,40)/40
energy                                      clip(x,0,160)/160
agent/zone acquisition elapsed              clip(x,0,6)/6
token ETA and safe-return margin            clip(x,0,140)/140
post-event physical time                    clip(x,0,120)/120
clearance remaining                         clip(x,0,20)/20
zone demand                                 x/2
cumulative zone demand and delivery         clip(x,0,240)/240
roster scalar                               N/7
```

There are no missing model values. At a node, remaining edge time is raw zero.
For an illegal or physically unavailable token, ETA uses raw `140`, safe-return
margin uses raw `0`, and its legal bit is zero. A vacant executor/relay has raw
acquisition elapsed and delivered rate zero. A missing clearance object has raw
clearance remaining zero. Every cumulative field is derived from the simulated
public state and is therefore present. Any nonfinite raw value, out-of-domain
demand, or non-one-hot categorical state makes the state structurally invalid;
negative zero is canonicalized to positive zero. No running normalization,
learned calibration, alternate divisor, coordinate permutation, identity, key,
presentation slot, padding position, old score, old result or `N`-specific
policy head exists.

The failure-relative public token order is fixed:

```text
[EXEC_failed, RELAY_failed, EXEC_intact, RELAY_intact].
```

The legal decoder assigns one remaining legal active key or null to each
unfixed token, removes a selected key from later choices, and sends every
unselected free key to base. Fixed en-route commitments are preserved. The
physical command is a partial injective map from the four named tokens to
physical keys plus the sorted set of keys commanded to base.

## Exact group action

A presentation is a bijection

```text
p:{1,...,N}->K
```

from presentation slots to physical keys. For `sigma in S_N`, define

```text
(sigma.p)(j)=p(sigma^{-1}(j)).
```

The action applies identically to every row-indexed object:

- raw agent records and legal masks;
- per-row hidden states at every shared-encoder layer;
- candidate-token association rows;
- row-indexed conditional distributions; and
- presented-slot command occupants.

Zone rows, global state and the four named physical tokens are not permuted.
If `d` is a presented-slot command, then

```text
(sigma.d)(token)=sigma(d(token))
```

for every nonnull selected slot. The inverse physical map is

```text
Phi_p(d)(token)=p(d(token)).
```

Therefore `Phi_(sigma.p)(sigma.d)=Phi_p(d)` by construction.

For an intended invariant path with row-hidden tensor `H`, pooled set state
`u`, association score rows `A` and presented command `D`, the exact
commutation laws are:

```text
H(sigma.X) = sigma.H(X)
u(sigma.X) = u(X)
A(sigma.X) = sigma.A(X)
D(sigma.X) = sigma.D(X)
Phi_(sigma.p)(D(sigma.X)) = Phi_p(D(X)).
```

No approximate tolerance is permitted for these equalities.

## Exact physical-command serialization and equality

The evaluation serializer emits, in order, four token-occupant fields in the
fixed failure-relative token order, one base-list field, one fixed-commitment-
list field, and one terminal byte `0x0A`.

Each token-occupant field is exactly 33 bytes:

```text
0x00 followed by 32 zero bytes                         for null;
0x01 followed by the complete 32-byte transport key   for an occupant.
```

The type byte makes null disjoint from every possible 256-bit key. The base-
list field is one unsigned 8-bit count `b`, followed by `b` complete 32-byte
keys in ascending byte order. The fixed-commitment-list field is one unsigned
8-bit count `c`, followed by `c` tuples in ascending key order. Each tuple is:

```text
complete 32-byte key;
one unsigned 8-bit destination code;
one unsigned 16-bit big-endian remaining-route-seconds value.
```

Destination codes are exactly `0=B`, `1=R1`, `2=S1`, `3=R2`, `4=S2`. Counts
must fit unsigned 8-bit and remaining-route seconds must fit unsigned 16-bit;
otherwise the state is structurally invalid. No optional field, padding,
locale, whitespace, hexadecimal text or alternative destination code exists.
Diagnostic binary64 fields are not part of command bytes.

Two physical commands are equal exactly when these complete canonical byte
strings are bitwise equal. No float tolerance, set-without-occupant comparison,
command utility equality, semantic equivalence or post-hoc normalization is
allowed.

The canonical internal-reduction order is ascending complete stable key. It is
used only after each row has been encoded independently. Because the key is not
an input value, this order removes presentation-dependent floating-point
reduction order without adding identity information to the learned function.

## Treatment: PCPI-INV-MAPR

`PCPI-INV-MAPR` is one shared MAPR-compatible masked autoregressive controller.

- Shared agent encoder: `38 -> 64 -> 64`, SiLU.
- Shared zone encoder: `15 -> 32 -> 32`, SiLU, applied separately with shared
  bytes to the labeled `ZONE1` row and then the labeled `ZONE2` row.
- Global encoder: `4 -> 16 -> 16`, SiLU.
- Roster summary: elementwise mean and maximum of the 64-dimensional agent
  encodings. The mean is accumulated in ascending stable-key order and rounded
  once after division by `N`; maximum uses canonical binary64 comparison.
- Token table: four shared 16-dimensional rows keyed only by the fixed
  failure-relative token roles.
- The 208-dimensional state summary is exactly
  `concat(agent_mean[0:64],agent_max[0:64],zone1_encoding[0:32],`
  `zone2_encoding[0:32],global_encoding[0:16])` in that order.
- The candidate-scorer input is exactly
  `concat(candidate_hidden[0:64],state_summary[0:208],token_row[0:16],`
  `presentation_control[0:16])` in that order and enters
  `304 -> 128 -> 64 -> 1`, SiLU.
- Null uses one shared learned 64-dimensional null feature and
  `concat(pbar_N,0_8)` as its presentation-control input.
- Prefix dependence is limited to legal masking and removal of already selected
  candidates. No selected-prefix feature enters the base scorer.

No mean/max swap, zone swap, interleaving, feature permutation or alternate
learned concatenation is permitted. The null candidate occupies the same first
64 scorer positions through its registered all-zero learned null feature.

Both arms allocate the same trainable presentation matrix `P in R^{7x8}`.
For active slots, in slot-index order, define

```text
pbar_N=(1/N)*sum_{j=1}^N P_j
r_j=P_j-pbar_N
c_j(alpha)=concat(pbar_N,alpha*r_j)
c_null=concat(pbar_N,0_8).
```

The treatment fixes `alpha=0`. Every active row therefore receives the same
`concat(pbar_N,0_8)`, while all seven rows of `P`, their active mean and every
residual are still evaluated, stored and optimized under the common law.

For every active physical row, both arms evaluate and record one real pre-mask
score for each of the four named tokens. Illegal scores never enter a softmax,
loss or command but remain diagnostic row entries. Each token also has one null
score. Thus one state-presentation executes exactly `4N+4=4(N+1)` logical
scorer calls in either arm before masks and injective removal are applied.
Deterministic evaluation chooses the greatest legal score; an exact tie uses
ascending stable physical key, with null after all tied physical keys. The
presented command is inverse-mapped to physical-key space before any equality
or capability result is computed.

## Strictly containing comparator: PCPI-FREE-PRESENTATION

`PCPI-FREE-PRESENTATION` is the identical stored network with fixed
`alpha=1`. Candidate `j` receives
`concat(pbar_N,P_j-pbar_N)`; null receives the same `c_null` as treatment.

The comparator literally contains the treatment at every `N in {3,5,7}`.
For any invariant-arm parameter vector, the embedding into the free family:

1. copies every encoder, pool, token, null, hidden-scorer, output and
   nonresidual first-layer parameter;
2. copies the complete `P` tensor; and
3. sets exactly the eight first-layer scorer columns multiplying the residual
   half of `c_j` to zero.

Because the invariant residual input is identically zero, this embedding
reproduces every invariant score, masked conditional distribution and physical
command for every roster, presentation, mask and prefix. Strictness is
witnessed by two unequal slot residuals and one nonzero residual-input column
that reverses the odds of the same two physical candidates when their slots are
exchanged.

Both arms have identical public information, row/zone/global tensors, stable-key
plumbing, legal masks, token order, network widths, parameter storage,
initial homologous bytes, optimizer, `4(N+1)` scorer calls, reduction calls,
forward/backward calls and checkpoint law. Both compute `pbar_N`, every
residual and the full 16-vector input; only the frozen scalar `alpha` differs.
The comparator adds functional freedom only through the residual channel and
adds no observation, hidden state, parameter tensor, communication, training
row or optimization opportunity.

## Fresh finite target-bound state family

There are sixteen paired replicate roles `PCPI-REP-00` through
`PCPI-REP-15`. The complete object uses no future machine seed. Its single
256-bit counter master is bound now, before any proposal or diagnostic, by

```text
M=SHA256(UTF8("VNFC-PCPI-SCIENCE-20260822-04/MASTER/V1")),
```

where the quoted ASCII characters are encoded as UTF-8 without BOM or terminal
newline. This deterministic r03-specific realization is immutable, is copied
into either terminal atomic manifest, and is never selected, redrawn or
replaced. No proposal, acceptance count, key, parameter, gradient, model
output, predecessor result or preliminary diagnostic may be observed before
this binding. Each replicate has exactly 36 accepted base physical states:

```text
N in {3,5,7}
failed zone in {1,2}
support class in {ETA,RADIO,COUPLED}
copy in {0,1}.
```

### Counter primitives

For a complete UTF-8 address `A`, define

```text
R64(A)=uint64_BE(SHA256(M || 0x00 || UTF8(A))[0:8]).
```

For integer `m>=1`, let `L_m=2^64-(2^64 mod m)`. Define
`UNIFORM_INDEX(m,A)` by scanning exactly the suffixes
`A/reject/q`, `q=0,...,65535`, in increasing order, taking the first
`R64(A/reject/q)<L_m`, and returning `R64(A/reject/q) mod m`. If none qualifies,
return `COUNTER_EXHAUSTION`; do not extend the scan or substitute another
address/master. This is the sole finite index law. It is the registered
rejection mapping on the fixed SHA-derived counter tape, not a theorem that
SHA-256 words are probabilistically independent or uniform. All claims are
conditional on this exact counter model and master. A physical transport key
is the complete 256 bits

```text
SHA256(M || 0x01 || UTF8(A/key/latent-record)).
```

No draw-order state is shared between addresses. Every field, transition and
command selection below has a literal suffix, so construction order cannot
change a candidate. Any `COUNTER_EXHAUSTION` during state proposal, transition,
presentation selection or static registration terminates construction into the
static-invalid manifest defined below; it is not an attempt miss and there is
no fallback draw.

Boundary address tags are exactly
`T_NEG120,T_NEG100,T_NEG80,T_NEG60,T_NEG40,T_NEG20,T_ZERO`; zone tags are
exactly `ZONE1,ZONE2`; latent-record tags are exactly `UAV1,...,UAV8` in the
public table order.

### Proposal-only public-tag command order

Random prehistory-command selection uses a proposal-only byte string that is
disjoint from the stable-key evaluation serializer. It emits four token-
occupant fields in fixed token order, one base-list field, one fixed-
commitment-list field and terminal `0x0A`.

Each proposal occupant is exactly five bytes: `0x00` plus four zero bytes for
null, or `0x01` plus the four ASCII bytes of one public tag `UAV1` through
`UAV8`. The base list is one unsigned 8-bit count followed by its four-byte
public tags in ascending ASCII order. The fixed-commitment list is one unsigned
8-bit count followed by tuples in ascending public-tag order; each tuple is the
four-byte tag, the exact unsigned 8-bit destination code registered by the
evaluation serializer, and unsigned 16-bit big-endian remaining-route seconds.
The same count/range invalidity rules apply.

This proposal-only string is used solely to order legal commands for counter
unranking. It is never a model/teacher feature, presentation/reduction order,
evaluation tie, endpoint or reported command identity. Stable transport keys
retain exactly their four registered row-transport, inverse-reassembly,
canonical-reduction and exact-tie roles and never affect proposal ordering.

### Exact attempt-to-state proposal law

For coordinate
`(replicate,N,failed-zone,support-class,copy,attempt)`, with
`attempt=0,...,65535`, use the fresh root

```text
VNFC-PCPI-SCIENCE-20260822-04/
replicate/N/failed-zone/support-class/copy/attempt.
```

The attempt maps to one candidate as follows.

1. Enumerate all `(N+1)`-subsets of the eight public physical UAV records in
   lexicographic latent-record order. Select one with
   `UNIFORM_INDEX(C(8,N+1),root/roster)`. The enclosing failed-zone coordinate
   is fixed, not drawn.
2. Assign each sampled physical record its root-addressed 256-bit stable key,
   substituting its exact `UAV1,...,UAV8` tag for `latent-record`. Any collision
   among sampled keys makes the entire attempt a miss; there is no nested key
   redraw.
3. At `t=-120`, place every sampled UAV at base, fully charged, uncommitted
   and unacquired. Draw each zone's initial demand state with
   `UNIFORM_INDEX(2,root/initial/demand/ZONEz)`, mapping index 0 to demand 1
   and index 1 to demand 2. Draw obstruction at
   `UNIFORM_INDEX(2,root/initial/obstruction/ZONEz)`, mapping index 0 to
   `CLEAR` and index 1 to `BLOCKED`.
4. At boundaries `t=-120,-100,-80,-60,-40,-20`, apply the exact incorporated
   public physical law. At every boundary after `-120`, advance demand using
   `UNIFORM_INDEX(10,root/transition/demand/ZONEz/T_TAG)`: in state 1,
   indices 0--7 stay at 1
   and 8--9 move to 2; in state 2, indices 0--2 move to 1 and 3--9 stay at 2.
   Advance obstruction with
   `UNIFORM_INDEX(5,root/transition/obstruction/ZONEz/T_TAG)`: in `CLEAR`,
   indices 0--3 stay
   `CLEAR` and 4 moves to `BLOCKED`; in `BLOCKED`, indices 0--1 move to
   `CLEAR` and 2--4 stay `BLOCKED`.
5. After the boundary transition, canonically enumerate every legal complete
   physical command conditional on fixed en-route commitments, ordered by the
   proposal-only public-tag bytes defined above. Select command
   `UNIFORM_INDEX(command_count,root/prehistory/T_TAG/command)` and simulate
   the public one-second physics for the next twenty seconds. No legal command
   or any nonfinite/invalid public transition makes the attempt a miss.
6. At `t=0`, advance both demand and obstruction chains once by the same exact
   rules using boundary tag `T_ZERO`, then require the specified failed zone to
   have an acquired executor. Remove that exact executor from the controllable
   roster, install the public 20-second clearance object, and serialize the
   resulting pre-action state. Absence of such an executor makes the attempt a
   miss.
7. Derive every route/token/acquisition field, energy, ETA, legal mask,
   safe-return margin, demand, obstruction, delivered-service field, cumulative
   zone/global field, fixed commitment and clearance value from that simulated
   physical state. No public field is independently redrawn after simulation.
8. Apply the treatment-blind common, support, copy and registered-pair predicates
   below. Retain the first qualifying attempt. If attempt 65535 does not
   qualify, trigger the static-invalid manifest form below; no scientific
   disposition exists until that manifest is complete.

Common predicates are:

1. all active keys are unique and every public row is finite;
2. at least two legal complete physical commands exist;
3. every fixed commitment and every selected route is legal and reserve-safe;
4. the teacher command is unique after the stable-key tie law;
5. at least two free physical candidates are legal for one claim-bearing token;
6. the exact canonical presentation and all required pairs below exist; and
7. no model, score, learned action, old VNFC row or endpoint enters proposal or
   acceptance.

The support witness is selected lexicographically from the fixed physical-token
order and ascending public latent-record tags `UAV1,...,UAV8`, independently
of stable-key values and model output. Candidate tuples are enumerated by their
ordered public tags; any teacher tie inside one already selected tuple is then
resolved by the separately registered stable-key tie law:

- `ETA`: two legal failed-executor candidates have different ETAs, and the
  minimum-ETA candidate differs from the maximum-radio candidate.
- `RADIO`: the failed-zone relay is physically required; two legal relay
  candidates differ in radio capacity, and the maximum-radio candidate differs
  from the minimum-ETA candidate.
- `COUPLED`: the first fixed-token-order pair of unfixed tokens and first
  ascending three-public-tag set are jointly legal; the teacher's first
  candidate is common to both tokens, so injective removal changes the second-
  token winner.

### Canonical presentation and registered pairs

The canonical presentation `p_can` maps slot `j` to the active physical key
with the `j`-th smallest complete 256-bit value.

Every accepted state separately registers:

1. `support_witness`, the lexicographically first witness above, used only for
   treatment-blind state-family classification;
2. for `copy=1`, `tie_pair=(token,kappa_a,kappa_b)`, the first fixed-token-
   order/ascending-public-tag pair that is legal at the same teacher prefix, has
   bitwise-identical complete 38-dimensional visible rows and legal masks, has
   identical non-key teacher tuples, and is resolved only by stable-key order;
   this pair is used only for the tie fixture;
3. for `copy=0`, no `tie_pair`, and every teacher-selected winner must be
   unique before the stable-key coordinate at its actual prefix;
4. `flip_pair=(token,kappa_a,kappa_b)`, the first fixed-token-order and
   ascending-public-tag pair for which both keys are legal at that prefix and
   the exact FEATURE-FLIP defined below changes the complete teacher physical
   command; and
5. `swap_pair=flip_pair`, fixed before any model result.

Absence of a required support witness, `copy=1` tie pair or flip/swap pair is
an attempt miss. The tie pair and flip pair need not be the same.
Public tags are used only for treatment-blind proposal/fixture registration and
never enter a learned tensor, teacher score, endpoint, presentation order or
reported command identity. Stable keys remain confined to row transport,
inverse physical reassembly, canonical reduction/presentation and genuine
exact tie resolution.

For each accepted base state, final evaluation enumerates all `N!`
presentations in lexicographic permutation order. The exact family per replicate
is

```text
12*3! + 12*5! + 12*7! = 61,992 state-presentations,
```

or 991,872 per arm across sixteen replicates. The accepted `N={3,5}` base
physical states are both the fitting states and the base states used in final
exhaustive presentation evaluation. Fitting presentations and final evaluation
presentations use disjoint counter namespaces; no separate `N={3,5}` physical
evaluation states are implied. `N=7` physical states and all final presentation
rows are constructed/frozen but receive no model evaluation until final
evaluation. No state or presentation is sampled, omitted, topped up or selected
by a model result.

## Physical capability teacher

The teacher receives only the same public state plus stable-key tie plumbing. It
processes the fixed token order and, for every unfixed token, chooses the
remaining legal candidate with the smallest token-specific tuple:

```text
executor: (ETA,-safe_return_margin,-radio_capacity,stable_key)
relay:    (-radio_capacity,ETA,-safe_return_margin,stable_key).
```

Null follows every legal physical candidate and is chosen only when no legal
candidate exists. A selected key is removed from later choices; all remaining
free keys go to base. The teacher is deterministic, legal, physical-key based
and exactly presentation invariant. It is a capability label only, not a value
baseline, optimal controller or task-return claim.

For replicate `r`, size `N` and failed zone `z`, define

```text
B_(r,N,z) = the six accepted states from
            support class {ETA,RADIO,COUPLED} x copy {0,1}.
```

Structural teacher validity requires legal commands, exact presentation
invariance, the registered stable-key semantics, a unique complete command
after ties, a valid state proposal/acceptance record and every required
support/tie/flip/swap registration. Any structural failure is
an exact trigger for the static-invalid manifest; it becomes
`INVALID_STATIC_FAMILY` only when that create-once form is complete.

After a structurally valid 576-state family exists, teacher diversity is
evaluated separately in every `B_(r,N,z)`. Each such block must contain at
least two distinct failed-executor physical occupants, at least one nonnull relay
occupant and at least one injective second-choice change. At each `(r,N)`, the
teacher must additionally emit at least four distinct physical command
serializations. Failure of these exact diversity counts is
`NONIDENTIFIED_CAPABILITY_SUPPORT`, not static invalidity.

### Complete pretraining counter frontier

Before any forward pass, model output, gradient or optimizer step, execute and
freeze the complete result-blind counter frontier in this exact order:

1. construct the state family in lexicographic
   `(replicate,N,failed-zone,support-class,copy)` order, with replicate
   `PCPI-REP-00` through `PCPI-REP-15`, `N:3<5<7`, failed zone `1<2`, support
   `ETA<RADIO<COUPLED`, copy `0<1`, and attempts `0..65535`; retain every
   accepted state and complete bounded attempt ledger;
2. for every training presentation, evaluate and freeze
   `UNIFORM_INDEX(N!,fit/replicate/update/state/presentation)` in order
   `(replicate,update,N,failed-zone,support-class,copy)`, with update
   `1..256` and the remaining fields ordered as above; the resulting index is
   shared by both arms; and
3. materialize and freeze all homologous initial parameter bytes in
   `(replicate,tensor-name)` order, using the bounded Stiefel/orientation law
   below for every rank-two tensor and exact positive-zero bytes for biases and
   the null feature.

Tensor names are these exact ASCII strings, sorted lexicographically by their
UTF-8 bytes whenever an order is required:

```text
agent.fc1.bias
agent.fc1.weight
agent.fc2.bias
agent.fc2.weight
global.fc1.bias
global.fc1.weight
global.fc2.bias
global.fc2.weight
null_feature
presentation_matrix
scorer.fc1.bias
scorer.fc1.weight
scorer.fc2.bias
scorer.fc2.weight
scorer.out.bias
scorer.out.weight
token_table
zone.fc1.bias
zone.fc1.weight
zone.fc2.bias
zone.fc2.weight
```

Any state-family, presentation-index, Stiefel-attempt or orientation
`COUNTER_EXHAUSTION`, or any `INITIALIZATION_EXHAUSTION`, stops this frontier
before model activity and triggers only the static-invalid manifest. No later
counter address may be evaluated during fitting. If and only if the complete
frontier succeeds, the full-PCPI path reads the frozen states, presentation
indices and initial bytes. This preflight is a constitutive scientific
construction step, not a UI/runtime canary, implementation benchmark or model
probe.

## Frozen finite-budget supervised fit

Only `N={3,5}` states enter fitting; `N=7` is untouched until final
evaluation. Within each replicate and arm:

- 256 fixed full-batch updates, with no early stop or checkpoint selection;
- each update contains the same 24 accepted training base states exactly once;
- each state uses the lexicographic presentation at its already frozen
  pretraining-frontier index, paired across arms; update/address namespaces are
  disjoint even if the same permutation value recurs, and final evaluation is
  exhaustive rather than sampled;
- teacher forcing uses the exact teacher prefix and the unique full-batch
  objective below;
- one AdamW step follows the full batch: learning rate `3e-4`, betas
  `(0.9,0.999)`, epsilon `1e-8`, weight decay `1e-4` under the exact scope
  and recurrence below, and global gradient-norm cap `0.5`;
- no reward, critic, RL rollout, augmentation beyond the registered
  presentation, schedule, checkpoint sweep, tolerance or auxiliary loss exists;
  and
- only update 256 is conclusion-bearing.

### Exact supervised update loss and reduction

For training state `s` and token `r` in fixed failure-relative token order,
let `CE_(s,r)` be the negative natural logarithm of the teacher-forced
candidate probability under the exact teacher prefix. A fixed/skipped token has
`CE_(s,r)=+0.0`. For one state and one update define

```text
ell_s    = sum_(r=1)^4 CE_(s,r)
L_update = (1/24) * sum_(s=1)^24 ell_s.
```

Every accepted state has equal weight; the loss is not renormalized by its
number of unfixed tokens. The 24 states are reduced in this exact lexicographic
order:

```text
N:             3 < 5;
failed zone:   1 < 2;
support class: ETA < RADIO < COUPLED;
copy:          0 < 1.
```

Within a token softmax, logits/exponentials are accumulated in ascending
complete stable-key order followed by null. Within a state, token losses are
added in the fixed token order; state losses are then added in the order above;
the total is divided once by binary64 `24.0`. `exp` and `log` mean the correctly
rounded real elementary functions to binary64 round-to-nearest, ties-to-even.
All additions, subtraction of the softmax reference, divisions and
multiplications use that mode and no fused contraction. One AdamW step is
computed from this single mean loss. No sum reduction, token-count reduction,
state weighting, label smoothing, temperature change, framework-default
reduction or alternate accumulation order is permitted.

### Exact Stiefel/Haar initialization

For every affine weight matrix `W` of logical shape
`n_out x n_in`, scan exactly `stiefel_attempt=0,...,65535`. At each attempt,
draw a counter-keyed row-major matrix of registered standard-normal entries. An
entry is the correctly rounded binary64
`Phi^{-1}((R64+0.5)/2^64)` at its literal
`tensor/stiefel_attempt/row/column` address. This is a deterministic mapping of
the fixed counter tape; no probabilistic independence theorem is claimed.

- If `n_out<=n_in`, perform canonical increasing-column Householder thin QR on
  the transpose and transpose the resulting `Q`, yielding orthonormal rows.
- If `n_out>n_in`, perform the same thin QR directly, yielding orthonormal
  columns.
- Each Householder diagonal is normalized positive; all arithmetic is IEEE-754
  binary64 round-to-nearest ties-to-even in row-major scalar order without
  fused contraction. Rank deficiency or a nonfinite reflector advances to the
  next registered attempt. The first finite full-rank result is retained. If
  attempt 65535 also fails, return `INITIALIZATION_EXHAUSTION`; do not extend,
  substitute or redraw. That exhaustion terminates construction into the
  static-invalid manifest and no model is trained.

After QR, draw one exact orientation sign from
`UNIFORM_INDEX(2,tensor/stiefel_attempt/orientation_sign)` for the retained
attempt, mapping 0 to `+1` and 1 to `-1`,
and multiply the complete `Q` by it. This is the registered orientation rule;
no probabilistic balance or independence claim is made for the fixed counter
tape. This counter-keyed QR construction, rather than an ideal continuous Haar
measure, is the single-valued Stiefel/Haar initialization law. Set `W=gQ`, with
correctly rounded `g=sqrt(2)` for hidden matrices and
`g=0.01` for policy-output matrices. Every affine bias is zero.

The four-by-sixteen token table uses the same bounded Stiefel-attempt law in
its literal token-table namespace with gain 1. The `7x8` presentation matrix
`P` uses the same bounded law in its literal presentation-matrix namespace with
gain `0.1`; the registered orientation sign does not add row centering. The
learned null-candidate feature is the all-zero 64-vector.

Within a paired replicate, each homologous tensor is drawn once from the
`(replicate,tensor-name)` namespace and its exact initial bytes are copied to
both arms; no second arm draw is consumed. AdamW decay applies to every
trainable tensor of rank at least two, including all affine matrices, `P` and
the token table. Decay is zero for biases and every rank-one vector, including
the null feature. Global clipping uses the Euclidean norm over all trainable
tensors. Arms have disjoint action/optimizer namespaces after their paired
initial bytes, while presentations remain paired.

### Exact binary64 AdamW recurrence

All optimizer scalars are the correctly rounded binary64 values of the written
decimal literals. Parameter tensors are traversed by the exact lexicographic
ASCII tensor-name order registered in the pretraining frontier; matrices use
row-major scalar order and vectors use increasing index order. Both moment
arrays start as positive binary64 zero for every scalar. No AMSGrad, fused
kernel, master-precision copy or framework-default recurrence exists.

For update `t=1,...,256`, compute the raw gradient `d_i` of the unique
`L_update` at the common pre-update parameter snapshot. Accumulate

```text
S_0 = +0.0
S_i = S_(i-1) + d_i*d_i
G   = sqrt(S_last)
```

in the registered scalar order, rounding after each multiplication and
addition. `sqrt` is the correctly rounded binary64 square root. If `G=0`, set
`clip=1`; otherwise set `clip=min(1,0.5/G)`. Then set `g_i=clip*d_i`, rounded
once, before any moment update.

Define bias-correction powers by repeated binary64 multiplication, not a
library power call:

```text
b1pow_0 = 1;  b1pow_t = b1pow_(t-1)*beta1
b2pow_0 = 1;  b2pow_t = b2pow_(t-1)*beta2.
```

For every scalar, simultaneously from its pre-update state, apply exactly:

```text
m_i,t     = beta1*m_i,t-1 + (1-beta1)*g_i
v_i,t     = beta2*v_i,t-1 + (1-beta2)*(g_i*g_i)
mhat_i,t  = m_i,t/(1-b1pow_t)
vhat_i,t  = v_i,t/(1-b2pow_t)
denom_i   = sqrt(vhat_i,t) + epsilon
step_i    = lr*(mhat_i,t/denom_i)
base_i    = theta_i,t-1*(1-lr*wd_i)
theta_i,t = base_i-step_i.
```

Every multiplication, addition, subtraction, division and square root above is
rounded to binary64 round-to-nearest, ties-to-even immediately in the written
left-to-right dependency order, without fused contraction. `wd_i=1e-4` for
the already registered rank-at-least-two decay scope and `wd_i=0` otherwise;
`lr=3e-4`, `beta1=0.9`, `beta2=0.999`, and `epsilon=1e-8`. Decoupled decay is
therefore applied to the old parameter before subtracting the adaptive step,
while moments see only the clipped loss gradient. Nonfinite raw gradients,
moments or parameters do not authorize a substituted recurrence, skipped
update or altered branch; the full manifest remains incomplete until unchanged-
science technical completion produces the exact finite trajectory.

### Exact logical work

Each training update uses 12 states at `N=3` and 12 at `N=5`, so it executes

```text
12*4*(3+1) + 12*4*(5+1) = 480
```

logical scorer calls. That is 122,880 calls per replicate-arm and 1,966,080 per
arm across sixteen replicates. There is one batched forward/backward and one
optimizer step per replicate-arm update: 8,192 optimizer steps across both arms
and all replicates.

Final exhaustive evaluation executes

```text
12*3!*4*(3+1) + 12*5!*4*(5+1) + 12*7!*4*(7+1)
= 1,971,072
```

logical scorer calls per replicate-arm, or 31,537,152 per arm. FEATURE-FLIP adds
864 calls per replicate-arm. The trained comparator's residual-zero projected
clone adds 864 calls per comparator replicate. ROW-SWAP reuses the recorded
pre-mask score vectors and adds no scorer call. These counts, tensor dimensions,
mask operations and reductions are identical across learned arms wherever the
same observable is evaluated; no hidden arm-specific work is permitted.

## Final observables and interventions

For each final checkpoint, replicate, base state and presentation, record:

1. raw presentation and inverse physical map;
2. every per-row hidden tensor after inverse mapping;
3. pooled mean/max state bits;
4. all four pre-mask token scores for every active physical row, every null
   score, each legal mask and every masked conditional distribution both on the
   ordinary deterministic decode and on every registered matched-prefix trace;
5. presented and physical command serialization;
6. support, tie, flip and swap registrations plus legality and tie receipts; and
7. teacher command and exact match bit.

### Teacher competence and learned-arm diversity

A replicate-arm is competent when, on `p_can`:

- it matches the complete teacher command in at least 10 of 12 base states
  separately at each `N`;
- it matches at least 3 of 4 states in each support class at each `N`;
- it emits at least four distinct physical commands at each `N`; and
- in every `B_(r,N,z)`, it selects at least two distinct failed-executor keys
  and at least one nonnull relay key.

Package-level competence requires at least 14 of 16 competent replicates for an
arm. The structurally valid teacher family and its separate blockwise diversity
gate are prerequisites defined above; teacher diversity failure is not learned-
arm incompetence.

### Exact FEATURE-FLIP state-action sensitivity

FEATURE-FLIP is evaluated only under `p_can`. For registered
`flip_pair=(token,kappa_a,kappa_b)`:

1. exchange only the ETA coordinate for that token between the two physical
   rows;
2. exchange their scalar radio-capacity coordinates;
3. preserve keys, masks, safe-return margins, every other row coordinate,
   zone/global records and physical-command plumbing; and
4. recompute the complete model and teacher from the modified public tensor.

Both candidates must remain teacher-legal under the frozen masks, and the
complete teacher command must change; this is part of candidate acceptance. A
replicate-arm is state-sensitive only when, for every `N` separately, its
physical command changes on at least 4 of 12 flips and changes on at least one
of the four states in each support class ETA, RADIO and COUPLED at that same
`N`.
Package-level sensitivity requires at least 14 of 16 replicates.

### Exact pre-mask ROW-SWAP association sensitivity

ROW-SWAP is evaluated only under `p_can` after the ordinary scorer. It
exchanges the complete four-token pre-mask score vectors of `swap_pair`,
retains each recipient's own public row and legal mask, leaves null scores and
all other rows unchanged, and then reruns the ordinary masked decoder and
inverse physical map. Illegal diagnostic scores remain excluded from softmax
and command.

Every accepted state is an opportunity. A replicate-arm is association-
sensitive only when, for every `N` separately, its physical command changes on
at least 4 of 12 swaps and changes on at least one of the four states in each
support class ETA, RADIO and COUPLED at that same `N`. Package-level
sensitivity requires at least 14 of 16 replicates satisfying the complete
per-size rule. These competence and intervention gates prevent a constant,
null-only, association-dead or nonacting path from passing.

## Exact commutation and comparator-activity gates

`INV_INTERNAL_COMMUTES` requires, for all sixteen final treatment checkpoints,
all 36 base states and all registered permutations:

- inverse-mapped per-row hidden tensors are bitwise equal to the canonical-
  presentation tensors;
- pooled state is bitwise equal;
- at each token, let the canonical deterministic treatment decode under
  `p_can` define one physical prefix. Under presentation `sigma.p_can`, force
  the exact `sigma`-transport of that same physical prefix. On those matched
  prefixes, inverse-mapped pre-mask score rows, legal supports and masked
  conditional probabilities are bitwise equal; and
- physical command bytes are bitwise equal.

The matched-prefix traces do not replace the ordinary decode. Separately run
the complete deterministic treatment decoder under every presentation to test
`D(sigma.X)=sigma.D(X)` and physical-command equality. One mismatch in either
surface makes this Boolean false. No replicate or state is dropped.

`FREE_OUTPUT_COMMUTES` requires only the final physical-command byte equality
for all sixteen comparator checkpoints, states and permutations. Its internal
row/score mismatches are recorded and cannot be called internal invariance.

`FREE_POSITION_ACTIVE` compares the trained comparator with its exact
residual-zero projected clone: keep every parameter byte fixed and evaluate the
same checkpoint with the residual half of every `c_j` set to zero
(`alpha=0`). For each canonical state, first run the trained `alpha=1`
comparator and record its complete deterministic physical prefix. At each token,
evaluate both the trained comparator and projected clone conditioned on that
identical recorded prefix, hence the same remaining-candidate legal support.
Compute total variation on that common support and take the maximum of the four
token-level distances. Separately run both complete deterministic decoders from
the initial state and compare their physical-command bytes. Activity in one
state requires maximum common-prefix total variation at least `0.05` and
different complete command bytes. The gate requires activity in at least one
state at every `N` for at least 8 of 16 replicates. This gate is relevant only
to a branch selecting the broader free family.

`OBSERVABLE` requires complete presentation maps, stable-key maps, internal
traces, score rows, commands, interventions and denominators. Missing or
ambiguous inverse mapping, duplicate key, hidden key-as-feature use, or an
unrecorded presentation prevents completion of the full PCPI manifest and
returns to unchanged-science technical completion; it is not a scientific
branch from partial data.

## Exhaustive first-true result map

The manifest forms defined below are mutually exclusive. A completed static-
invalid manifest has only branch 1. A completed full PCPI manifest applies
branches 2 through 7 in their listed first-true order:

1. **INVALID_STATIC_FAMILY.** Any public-law, exact proposal-generator,
   first-attempt acceptance, fresh-namespace, collision, state/pair registration,
   key uniqueness/exclusion, permutation enumeration, structural teacher
   legality/invariance/unique-command, containment, serialization, inverse-map,
   counter exhaustion or initialization exhaustion established before training
   completes the static-invalid manifest and invalidates the object. Report no
   architecture claim and train no model.
2. **NONIDENTIFIED_CAPABILITY_SUPPORT.** After a structurally valid 576-state
   family exists, if any teacher `B_(r,N,z)` diversity predicate fails, or
   neither arm reaches package-level state-action and association-row
   sensitivity, the family cannot distinguish commutation from a degenerate
   capability path.
3. **RETAIN_INVARIANT_DECODER.** If the invariant arm passes package-level
   competence, state sensitivity, association sensitivity and
   `INV_INTERNAL_COMMUTES`, retain `PCPI-INV-MAPR` as the sole current VNFC
   decoder eligible for a separately defined direct-value question. Report the
   free arm descriptively; it cannot displace a passing by-construction path.
4. **SELECT_FREE_PRESENTATION_FAMILY.** If the invariant arm does not qualify,
   but the free arm passes package-level competence, both sensitivity gates,
   `FREE_OUTPUT_COMMUTES` and `FREE_POSITION_ACTIVE`, select only the broader
   free family for a separately defined direct-value question. This means a
   trained solution inside the broader class realized physical output
   invariance; it does not claim that presentation dependence is useful.
5. **DELETE_CURRENT_MAPR_ASSOCIATION_DECODER.** If both arms pass competence and
   both sensitivity gates but neither produces exact physical-command
   commutation over the full registered permutation family, delete these two
   current association/decoder paths for this target. Do not delete all set
   policies or all variable-`N` recovery.
6. **NONIDENTIFIED_OPTIMIZATION.** If neither arm reaches package-level
   competence, make no commutation-family selection; finite-budget fitting is
   the strongest alternative.
7. **NONIDENTIFIED_MIXED.** Every remaining valid pattern—such as one capable
   but noncommuting arm with the other inactive, or a free output-invariant
   solution without registered position activity—is nonidentified for the
   requested selection.

No branch changes a checkpoint, update count, support threshold, state,
permutation, key, comparator or intervention after activity. No positive branch
automatically authorizes a value experiment.

## Strongest alternatives

Even `RETAIN_INVARIANT_DECODER` would remain compatible with:

- stable-key canonical reduction mechanically removing presentation order
  without demonstrating useful task semantics;
- finite-template imitation of a simple ETA/radio teacher;
- action changes caused by the deterministic key tie law rather than learned
  coordination; and
- a public stable transport key that is unavailable or costly in a distributed
  deployment.

`SELECT_FREE_PRESENTATION_FAMILY` would additionally remain compatible with
finite-budget optimization geometry: the broader arm may fit a physically
invariant solution more easily without showing that free presentation is
causally helpful. Failure of the free arm may reflect slot-residual
optimization, not a need for symmetry. No branch distinguishes those
alternatives without a later direct-value object.

## Maximum claim

The largest possible claim is:

> In the exact 576-state finite two-zone post-loss family, under the frozen
> supervised capability teacher, 256-update fit, sixteen paired parameter
> roles, training sizes `N={3,5}`, held-out size `N=7` and exhaustive registered
> presentation permutations, the selected decoder produced exactly invariant
> physical command bytes while meeting the registered teacher competence,
> state-action and association-row sensitivity requirements.

For `RETAIN_INVARIANT_DECODER`, internal row, pooled-state and association-row
commutation may additionally be claimed for the exact family. For
`SELECT_FREE_PRESENTATION_FAMILY`, only output commutation may be claimed.

No branch supports task return, recovery benefit, robustness, arbitrary `N`,
arbitrary composition, repeated churn, general permutation invariance outside
the finite family, unique mechanism, distributed execution, real-aircraft
transfer, safety, deployment or flight.

## Indivisible activity boundary

The object has exactly two mutually exclusive create-once terminal manifest
forms. Before either form is complete, code, fixtures, attempt rows, partial
states, initialization attempts, checkpoints, permutation rows, diagnostics
and benchmarks are not scientific observations and support no disposition.

### A. Static-invalid manifest

This form contains:

1. this immutable card, the already frozen master `M`, and one fresh future
   coordinate binding under the r03 namespace;
2. the complete bounded counter/attempt ledger through the first exhausted
   coordinate, counter exhaustion, structural failure or initialization
   exhaustion;
3. every preceding candidate miss and its exact treatment-blind predicate;
4. all key, proposal-order, teacher, pair-registration, containment,
   serialization, permutation and inverse-map receipts needed to establish the
   first failure, plus the complete bounded Stiefel ledger when initialization
   exhausts; and
5. proof that no predecessor result or model output entered construction and
   that no optimizer/training step occurred.

On create-once completion, its sole disposition is
`INVALID_STATIC_FAMILY`. No model is trained and no architecture-selection
claim exists. The manifest cannot be extended, converted into the full form or
replaced by changing a master, coordinate, attempt/counter cap, predicate,
state, initializer or namespace.

### B. Full PCPI manifest

This form is permitted only after all 576 accepted states, structural teacher
checks, containment/equality laws, exhaustive presentation registrations and
all sixteen paired initializations exist without a static-invalid trigger. It
contains:

1. all sixteen paired initial/final checkpoints and optimizer states for both
   arms;
2. all 576 accepted fresh base physical states, their bounded acceptance
   attempts and proof of zero r09, r01, r02 or r03 activity predecessors;
3. every training presentation and final exhaustive permutation row;
4. every ordinary-decode and matched-prefix per-row/internal/pool/score/legal-
   support/conditional/command trace and physical inverse mapping;
5. every teacher, FEATURE-FLIP and ROW-SWAP result;
6. complete competence, structural diversity, per-size sensitivity,
   commutation, free-activity and branch reductions; and
7. this immutable card, frozen `M`, future source/model/optimizer manifests and
   the one fresh coordinate binding under the r03 namespace.

Only branches 2 through 7 apply to this form. After create-once completion, no
state, permutation, parameter role, gate, threshold, prefix law, manifest form
or branch may be added or changed. It cannot be converted to the static-invalid
form. Definition, Pro review and any later separately authorized Gemini or CM
static-feasibility/cost work occur strictly before either activity form.

## Current definition boundary and requested reviews

This revision authorizes no construction or empirical work. It first requires
mathematical/causal closure in the existing same-VNFC ChatGPT External-Pro
conversation and same-direction EM intake.

No r04 Gemini question or operation is created or authorized. Gemini cannot
close the revision. Only after Pro `CLOSED` and EM intake may Portfolio
separately decide whether a new mutually blind Gemini advisory and a same-
direction CM static bindability, observability, containment and full-cost
assessment are worth authorizing. Neither provider may review code, technical
acceptance, runtime, hashes, leases or portfolio priority.
