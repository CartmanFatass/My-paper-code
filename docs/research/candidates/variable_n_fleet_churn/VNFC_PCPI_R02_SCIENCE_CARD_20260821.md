# VNFC physical-command presentation-invariance science card

Owner: Portfolio-owned `direction:variable_n_fleet_churn_b4` EM  
Definition object: `VNFC-PHYSICAL-COMMAND-PRESENTATION-INVARIANCE-DEFINITION`  
Science revision: `VNFC-PCPI-SCIENCE-20260821-02`  
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
r01 Pro review informs only this prospective definition; no provider answer is
a state, label, threshold, gate, result or claim. Revision r01 remains immutable,
mathematically unclosed, activity-free and permanently no-resend. A future
implementation must use a fresh namespace rooted at
`VNFC-PCPI-SCIENCE-20260821-02` and prove that no predecessor points into an old
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

The independently frozen agent row has the same public field meanings at every
`N` and presentation: flight-class one-hot (2), radio capacity (1),
node-or-directed-edge one-hot (15), remaining edge time (1), energy (1),
current-token one-hot including null (5), acquisition elapsed (1), four legal-
token bits (4), four exact token ETAs (4), and four safe-return energy margins
(4), for width 38. Two labeled zone rows have width 15 and the global vector
has width 4, using the public target meanings. All scalars use one frozen
binary64 normalization law. There is no identity, key, presentation slot,
padding position, old score, old result or `N`-specific policy head.

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

The physical command serializer emits, in fixed token order, either a null
sentinel or the complete 256-bit selected physical key, followed by the
ascending complete keys commanded to base and then the ascending complete keys
with fixed en-route destination and remaining-route time. All integers use
fixed-width big-endian encoding; binary64 fields, where present in diagnostic
traces, use canonical IEEE-754 bits. There is one terminal LF and no locale-
dependent text.

Two physical commands are equal exactly when these canonical byte strings are
bitwise equal. No float tolerance, set-without-occupant comparison, command
utility equality, semantic equivalence or post-hoc normalization is allowed.

The canonical internal-reduction order is ascending complete stable key. It is
used only after each row has been encoded independently. Because the key is not
an input value, this order removes presentation-dependent floating-point
reduction order without adding identity information to the learned function.

## Treatment: PCPI-INV-MAPR

`PCPI-INV-MAPR` is one shared MAPR-compatible masked autoregressive controller.

- Shared agent encoder: `38 -> 64 -> 64`, SiLU.
- Shared zone encoder: `15 -> 32 -> 32`, SiLU, with labeled-zone outputs
  concatenated.
- Global encoder: `4 -> 16 -> 16`, SiLU.
- Roster summary: elementwise mean and maximum of the 64-dimensional agent
  encodings. The mean is accumulated in ascending stable-key order and rounded
  once after division by `N`; maximum uses canonical binary64 comparison.
- Token table: four shared 16-dimensional rows keyed only by the fixed
  failure-relative token roles.
- Candidate scorer: candidate hidden (64), the 208-dimensional state summary,
  one 16-dimensional token row and the 16-dimensional presentation-control
  input enter `304 -> 128 -> 64 -> 1`, SiLU.
- Null uses one shared learned 64-dimensional null feature and
  `concat(pbar_N,0_8)` as its presentation-control input.
- Prefix dependence is limited to legal masking and removal of already selected
  candidates. No selected-prefix feature enters the base scorer.

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
`PCPI-REP-15`. Future machine integer seeds and the future 256-bit master
`M` remain unbound. Each replicate has exactly 36 accepted base physical
states:

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
`UNIFORM_INDEX(m,A)` by scanning rejection suffix
`A/reject/q`, `q=0,1,...`, taking the first `R64<L_m`, and returning
`R64 mod m`. This is the sole finite uniform-index law. A physical transport
key is the complete 256 bits

```text
SHA256(M || 0x01 || UTF8(A/key/latent-record)).
```

No draw-order state is shared between addresses. Every field, transition and
command selection below has a literal suffix, so construction order cannot
change a candidate.

Boundary address tags are exactly
`T_NEG120,T_NEG100,T_NEG80,T_NEG60,T_NEG40,T_NEG20,T_ZERO`; zone tags are
exactly `ZONE1,ZONE2`; latent-record tags are exactly `UAV1,...,UAV8` in the
public table order.

### Exact attempt-to-state proposal law

For coordinate
`(replicate,N,failed-zone,support-class,copy,attempt)`, with
`attempt=0,...,65535`, use the fresh root

```text
VNFC-PCPI-SCIENCE-20260821-02/
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
   `root/initial/obstruction/ZONEz`, mapping index 0 to `CLEAR` and index 1 to
   `BLOCKED`.
4. At boundaries `t=-120,-100,-80,-60,-40,-20`, apply the exact incorporated
   public physical law. At every boundary after `-120`, advance demand using
   an exact ten-cell draw at
   `root/transition/demand/ZONEz/T_TAG`: in state 1, indices 0--7 stay at 1
   and 8--9 move to 2; in state 2, indices 0--2 move to 1 and 3--9 stay at 2.
   Advance obstruction with a five-cell draw at
   `root/transition/obstruction/ZONEz/T_TAG`: in `CLEAR`, indices 0--3 stay
   `CLEAR` and 4 moves to `BLOCKED`; in `BLOCKED`, indices 0--1 move to
   `CLEAR` and 2--4 stay `BLOCKED`.
5. After the boundary transition, canonically enumerate every legal complete
   physical command conditional on fixed en-route commitments, ordered by the
   card's canonical physical-command bytes. Select command
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
   qualify, the complete object takes `INVALID_STATIC_FAMILY`.

Common predicates are:

1. all active keys are unique and every public row is finite;
2. at least two legal complete physical commands exist;
3. every fixed commitment and every selected route is legal and reserve-safe;
4. the teacher command is unique after the stable-key tie law;
5. at least two free physical candidates are legal for one claim-bearing token;
6. the exact canonical presentation and all required pairs below exist; and
7. no model, score, learned action, old VNFC row or endpoint enters proposal or
   acceptance.

The support witness is selected lexicographically from physical tokens and
ascending complete keys, independently of model output:

- `ETA`: two legal failed-executor candidates have different ETAs, and the
  minimum-ETA candidate differs from the maximum-radio candidate.
- `RADIO`: the failed-zone relay is physically required; two legal relay
  candidates differ in radio capacity, and the maximum-radio candidate differs
  from the minimum-ETA candidate.
- `COUPLED`: the first fixed-token-order pair of unfixed tokens and first
  ascending three-key set are jointly legal; the teacher's first candidate is
  common to both tokens, so injective removal changes the second-token winner.

### Canonical presentation and registered pairs

The canonical presentation `p_can` maps slot `j` to the active physical key
with the `j`-th smallest complete 256-bit value.

Every accepted state separately registers:

1. `support_witness`, the lexicographically first witness above, used only for
   treatment-blind state-family classification;
2. for `copy=1`, `tie_pair=(token,kappa_a,kappa_b)`, the first fixed-token-
   order/ascending-key pair that is legal at the same teacher prefix, has
   bitwise-identical complete 38-dimensional visible rows and legal masks, has
   identical non-key teacher tuples, and is resolved only by stable-key order;
   this pair is used only for the tie fixture;
3. for `copy=0`, no `tie_pair`, and every teacher-selected winner must be
   unique before the stable-key coordinate at its actual prefix;
4. `flip_pair=(token,kappa_a,kappa_b)`, the first fixed-token-order and
   ascending-key pair for which both keys are legal at that prefix and the exact
   FEATURE-FLIP defined below changes the complete teacher physical command; and
5. `swap_pair=flip_pair`, fixed before any model result.

Absence of a required support witness, `copy=1` tie pair or flip/swap pair is
an attempt miss. The tie pair and flip pair need not be the same.

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
rows remain untouched until final evaluation. No state or presentation is
sampled, omitted, topped up or selected by a model result.

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
`INVALID_STATIC_FAMILY`.

After a structurally valid 576-state family exists, teacher diversity is
evaluated separately in every `B_(r,N,z)`. Each such block must contain at
least two distinct failed-executor physical occupants, at least one nonnull relay
occupant and at least one injective second-choice change. At each `(r,N)`, the
teacher must additionally emit at least four distinct physical command
serializations. Failure of these exact diversity counts is
`NONIDENTIFIED_CAPABILITY_SUPPORT`, not static invalidity.

## Frozen finite-budget supervised fit

Only `N={3,5}` states enter fitting; `N=7` is untouched until final
evaluation. Within each replicate and arm:

- 256 fixed full-batch updates, with no early stop or checkpoint selection;
- each update contains the same 24 accepted training base states exactly once;
- each state uses the lexicographic presentation at index
  `UNIFORM_INDEX(N!,fit/replicate/update/state/presentation)`, paired across
  arms and disjoint across updates and final evaluation;
- teacher forcing uses the exact teacher prefix and sums four masked categorical
  cross-entropies, with a skipped fixed token contributing zero;
- one AdamW step follows the full batch: learning rate `3e-4`, betas
  `(0.9,0.999)`, epsilon `1e-8`, weight decay `1e-4` under the exact scope
  below, and global gradient-norm cap `0.5`;
- no reward, critic, RL rollout, augmentation beyond the registered
  presentation, schedule, checkpoint sweep, tolerance or auxiliary loss exists;
  and
- only update 256 is conclusion-bearing.

### Exact Stiefel/Haar initialization

For every affine weight matrix `W` of logical shape
`n_out x n_in`, draw a counter-keyed row-major matrix of iid standard-normal
entries. A standard normal is the correctly rounded binary64
`Phi^{-1}((R64+0.5)/2^64)` at its literal tensor/row/column address.

- If `n_out<=n_in`, perform canonical increasing-column Householder thin QR on
  the transpose and transpose the resulting `Q`, yielding orthonormal rows.
- If `n_out>n_in`, perform the same thin QR directly, yielding orthonormal
  columns.
- Each Householder diagonal is normalized positive; all arithmetic is IEEE-754
  binary64 round-to-nearest ties-to-even in row-major scalar order without
  fused contraction. Rank deficiency or a nonfinite reflector redraws the whole
  matrix under the next `stiefel_attempt` suffix.

After QR, draw one exact orientation sign from
`UNIFORM_INDEX(2,tensor/orientation_sign)`, mapping 0 to `+1` and 1 to `-1`,
and multiply the complete `Q` by it. This makes the finite registered draw
exactly centrally symmetric. This counter-keyed QR distribution, rather than
an ideal continuous Haar measure, is the single-valued Stiefel/Haar
initialization law. Set `W=gQ`, with correctly rounded `g=sqrt(2)` for hidden matrices and
`g=0.01` for policy-output matrices. Every affine bias is zero.

The four-by-sixteen token table is drawn on the four-row Stiefel manifold with
gain 1. The `7x8` presentation matrix `P` is drawn on the seven-row Stiefel
manifold with gain `0.1`; its exact central symmetry comes from the registered
orientation sign and does not add row centering. The learned null-candidate
feature is the all-zero 64-vector.

Within a paired replicate, each homologous tensor is drawn once from the
`(replicate,tensor-name)` namespace and its exact initial bytes are copied to
both arms; no second arm draw is consumed. AdamW decay applies to every
trainable tensor of rank at least two, including all affine matrices, `P` and
the token table. Decay is zero for biases and every rank-one vector, including
the null feature. Global clipping uses the Euclidean norm over all trainable
tensors. Arms have disjoint action/optimizer namespaces after their paired
initial bytes, while presentations remain paired.

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
   score, each legal mask and every masked conditional distribution;
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
replicate-arm is state-sensitive when its physical command changes on at least
4 of 12 flips at each `N` and at least once in every support class.
Package-level sensitivity requires at least 14 of 16 replicates.

### Exact pre-mask ROW-SWAP association sensitivity

ROW-SWAP is evaluated only under `p_can` after the ordinary scorer. It
exchanges the complete four-token pre-mask score vectors of `swap_pair`,
retains each recipient's own public row and legal mask, leaves null scores and
all other rows unchanged, and then reruns the ordinary masked decoder and
inverse physical map. Illegal diagnostic scores remain excluded from softmax
and command.

Every accepted state is an opportunity. A replicate-arm is association-
sensitive when the physical command changes on at least 4 of 12 swaps at each
`N` and at least once in every support class. Package-level sensitivity
requires at least 14 of 16 replicates. These competence and intervention gates
prevent a constant, null-only, association-dead or nonacting path from passing.

## Exact commutation and comparator-activity gates

`INV_INTERNAL_COMMUTES` requires, for all sixteen final treatment checkpoints,
all 36 base states and all registered permutations:

- inverse-mapped per-row hidden tensors are bitwise equal to the canonical-
  presentation tensors;
- pooled state is bitwise equal;
- inverse-mapped score rows and masked conditional probabilities are bitwise
  equal; and
- physical command bytes are bitwise equal.

One mismatch makes this Boolean false. No replicate or state is dropped.

`FREE_OUTPUT_COMMUTES` requires only the final physical-command byte equality
for all sixteen comparator checkpoints, states and permutations. Its internal
row/score mismatches are recorded and cannot be called internal invariance.

`FREE_POSITION_ACTIVE` compares the trained comparator with its exact
residual-zero projected clone: keep every parameter byte fixed and evaluate the
same checkpoint with the residual half of every `c_j` set to zero
(`alpha=0`). In one canonical state, activity means maximum token-level total-
variation distance at least `0.05` and a different physical command. The gate
requires activity in at least one state at every `N` for at least 8 of 16
replicates. This gate is relevant only to a branch selecting the broader free
family.

`OBSERVABLE` requires complete presentation maps, stable-key maps, internal
traces, score rows, commands, interventions and denominators. Missing or
ambiguous inverse mapping, duplicate key, hidden key-as-feature use, or an
unrecorded presentation makes the complete object invalid.

## Exhaustive first-true result map

Apply the following branches only after the complete atomic object, in order:

1. **INVALID_STATIC_FAMILY.** Any public-law, exact proposal-generator,
   first-attempt acceptance, fresh-namespace, collision, state/pair registration,
   key uniqueness/exclusion, permutation enumeration, structural teacher
   legality/invariance/unique-command, containment, serialization, inverse-map,
   trace, atomicity or observability failure invalidates the object. Report no
   architecture claim.
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

Question-relevant activity begins only when one create-once atomic manifest
contains:

1. all sixteen paired initial/final checkpoints and optimizer states for both
   arms;
2. all 576 accepted fresh base physical states, their acceptance attempts and
   zero r09 or r01 activity predecessors;
3. every training presentation and final exhaustive permutation row;
4. all per-row/internal/pool/score/conditional/command traces and physical
   inverse mappings;
5. every teacher, feature-flip and row-swap result;
6. complete competence, sensitivity, commutation, free-activity and branch
   reductions; and
7. this immutable card, future source/model/optimizer manifests and one fresh
   coordinate binding under the PCPI namespace.

Before that complete boundary, code, fixtures, partial states, checkpoints,
permutation rows, diagnostics and benchmarks are not scientific observations.
After it, no state, permutation, parameter role, gate, threshold or branch may
be added or changed. Definition, Pro/Gemini review and later CM static
feasibility/cost occur strictly before activity.

## Current definition boundary and requested reviews

This revision authorizes no construction or empirical work. It first requires
mathematical/causal closure in the existing same-VNFC ChatGPT External-Pro
conversation and same-direction EM intake.

An independent mutually blind External-Gemini innovation question is frozen but
held. Gemini cannot close the revision, and no Gemini response is required or
authorized by this card. Only after Pro `CLOSED` and EM intake may Portfolio
separately decide whether the blind Gemini advisory and a same-direction CM
static bindability, observability, containment and full-cost assessment are
worth authorizing. Neither provider may review code, technical acceptance,
runtime, hashes, leases or portfolio priority.
