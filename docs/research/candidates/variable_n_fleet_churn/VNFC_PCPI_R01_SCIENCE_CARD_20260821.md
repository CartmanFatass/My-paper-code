# VNFC physical-command presentation-invariance science card

Owner: Portfolio-owned `direction:variable_n_fleet_churn_b4` EM  
Definition object: `VNFC-PHYSICAL-COMMAND-PRESENTATION-INVARIANCE-DEFINITION`  
Science revision: `VNFC-PCPI-SCIENCE-20260821-01`  
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
coordinate, checkpoint, optimizer, model byte, threshold, estimate, branch or
provider response may enter this object. No old VNFC row may be relabeled as a
PCPI fixture. A future implementation must use a fresh namespace rooted at
`VNFC-PCPI-SCIENCE-20260821-01` and prove that no predecessor points into an old
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
- Candidate scorer: candidate hidden, 208-dimensional state summary,
  16-dimensional token row and 8-dimensional presentation-control vector enter
  `296 -> 128 -> 64 -> 1`, SiLU.
- Null uses one shared learned null feature and the same state/token law.
- Prefix dependence is limited to legal masking and removal of already selected
  candidates. No selected-prefix feature enters the base scorer.

Both arms allocate the same presentation matrix `P in R^{7x8}`. For active
slots define, in slot-index order,

```text
pbar_N=(1/N)*sum_{j=1}^N P_j
r_j=P_j-pbar_N
q_j(alpha)=pbar_N+alpha*r_j.
```

The treatment fixes `alpha=0`, so every active row receives exactly `pbar_N`.
All seven rows of `P`, their mean and every residual are still evaluated and
stored. Thus the treatment cannot observe presentation slot while retaining
the exact same tensor shapes and arithmetic seams as the comparator.

The model produces a score for every legal candidate and null at each token.
Deterministic evaluation chooses the greatest score; an exact score tie uses
ascending stable physical key, with null after all tied physical keys. The
selected presented-slot command is inverse-mapped to physical-key space before
any equality or capability result is computed.

## Strictly containing comparator: PCPI-FREE-PRESENTATION

`PCPI-FREE-PRESENTATION` is the identical network with fixed `alpha=1`. Each
candidate therefore receives its current presentation-slot vector `P_j`.

The comparator strictly contains the treatment:

- for every invariant-arm parameter vector, setting every active `P_j` to the
  same `pbar_N` makes every residual zero and reproduces every treatment score,
  conditional distribution and command;
- strictness is witnessed by two nonidentical slot rows and one nonzero scorer
  coefficient on `r_j`, which can reverse the odds of the same two physical
  candidates when their presentation slots are exchanged.

Both arms have identical public information, row/zone/global tensors, stable-
key plumbing, legal masks, token order, network widths, parameter storage,
initial parameter bytes, optimizer, number of scorer calls, reduction calls,
forward/backward calls and checkpoint rule. Both compute `pbar`, every residual
and `q_j`; only the prospectively fixed scalar `alpha` differs. The comparator
has broader functional freedom only by lifting the equality constraint that is
the scientific axis under test. No extra observation, hidden state, parameter
tensor, communication, training row or optimization opportunity is added.

## Fresh finite target-bound state family

There are sixteen paired replicate roles `PCPI-REP-00` through
`PCPI-REP-15`. Future machine integer seeds remain unbound. Each replicate has
36 distinct base physical states:

```text
N in {3,5,7}
failed zone in {1,2}
support class in {ETA, RADIO, COUPLED}
copy in {0,1}.
```

For each coordinate, scan candidate attempt `a=0,...,65535` in ascending order
under the fresh counter address

```text
VNFC-PCPI-SCIENCE-20260821-01/
replicate/N/failed-zone/support-class/copy/attempt/field/draw.
```

One candidate state is produced by the public target law from a fresh active
roster, legal post-loss route/token state, energy state, failed-zone label and
obstruction state. Accept the first state satisfying the following
treatment-blind physical predicates; exhaustion is package invalidity.

Common predicates:

1. all active transport keys are unique and every public row is finite;
2. at least two legal complete physical commands exist;
3. every selected route is reserve-safe and every fixed commitment is legal;
4. the teacher command below is unique after the registered stable-key tie law;
5. at least two free physical candidates are legal for one claim-bearing token;
6. no model, score, learned action, r09 row or endpoint enters acceptance.

Support-class predicates:

- `ETA`: at least two failed-executor candidates have different ETAs; the
  minimum-ETA candidate differs from the maximum-radio candidate.
- `RADIO`: the failed-zone relay is required; at least two legal relay
  candidates differ in radio capacity; the maximum-radio candidate differs
  from the minimum-ETA candidate.
- `COUPLED`: at least two unfixed tokens share at least three legal candidates;
  one candidate is first under the teacher order for both tokens, so injective
  removal changes the second-token winner.

For `copy=0`, the decisive teacher tuple is feature-unique. For `copy=1`, one
registered decisive candidate pair has bitwise-identical complete model-visible
38-dimensional rows and legal masks at the decision, and is resolved only by
the stable-key tie law. Because the key is excluded from model features, a
shared scorer must produce a tie and the physical-key decoder must resolve it
consistently.

No accepted state is shared across replicates or sizes. Training and evaluation
addresses are disjoint. For every accepted base state, evaluation enumerates
all `N!` presentations in lexicographic permutation order. The exact evaluation
family per replicate is therefore:

```text
12*3! + 12*5! + 12*7! = 61,992 state-presentations.
```

Across sixteen replicates it is 991,872 state-presentations per arm. No
presentation is sampled, omitted, topped up or selected by a model result.

## Physical capability teacher

The teacher receives only the same public state plus stable-key tie plumbing.
It processes the fixed token order and, for every unfixed token, chooses the
remaining legal candidate with the smallest token-specific tuple:

```text
executor: (ETA, -safe_return_margin, -radio_capacity, stable_key)
relay:    (-radio_capacity, ETA, -safe_return_margin, stable_key).
```

Null follows every legal physical candidate and is chosen only when no legal
candidate exists. A selected key is removed from later choices; all remaining
free keys go to base. The teacher is deterministic, legal, physical-key based
and exactly presentation invariant. It is a capability label only, not a value
baseline, optimal controller or task-return claim.

The teacher must itself pass all group actions and produce, for each `N`, at
least four distinct physical command serializations, at least two distinct
failed-executor occupants and at least one injective second-choice change in
each failed zone. Failure is state-family invalidity, not a model result.

## Frozen finite-budget supervised fit

Only `N={3,5}` states enter fitting; `N=7` is untouched until final evaluation.
Within each replicate and arm:

- 256 fixed full-batch updates, no early stop or checkpoint selection;
- each update contains the 24 training base states exactly once;
- each state is presented under one fresh counter-keyed uniform permutation,
  common across arms and disjoint across updates;
- teacher forcing uses the exact teacher prefix and sums the four masked
  categorical cross-entropies, with a skipped fixed token contributing zero;
- one AdamW step follows the full batch: learning rate `3e-4`, betas
  `(0.9,0.999)`, epsilon `1e-8`, weight decay `1e-4` on rank-two-or-higher
  weights, and global gradient-norm cap `0.5`;
- no reward, critic, RL rollout, data augmentation beyond the registered
  presentation, learning-rate schedule, checkpoint sweep, tolerance or
  auxiliary loss exists; and
- only update 256 is conclusion-bearing.

All homologous parameter bytes, including the complete `P` tensor, are
bitwise identical across paired arms before fitting. Hidden matrices use fresh
counter-keyed orthogonal initialization with SiLU gain `sqrt(2)`; output layers
use gain `0.01`; biases are zero; `P` uses a fresh zero-mean row-wise
orthogonal draw with gain `0.1`. Arm action and minibatch namespaces are
disjoint, but training state presentations are paired. No old checkpoint or
optimizer state is imported.

## Final observables and interventions

For each final checkpoint, replicate, base state and presentation, record:

1. raw presentation map and inverse physical map;
2. every per-row hidden tensor after inverse mapping;
3. pooled mean/max state bits;
4. every four-token score row and masked conditional distribution after inverse
   mapping;
5. presented and physical command serialization;
6. legality, fixed-commitment and stable-key tie receipts; and
7. teacher command and exact match bit.

Three nondegeneracy observables are frozen.

### Teacher competence and action diversity

A replicate-arm is competent when, on the stable-key canonical presentation:

- it matches the complete teacher physical command in at least 10 of 12 base
  states separately at each `N`;
- it matches at least 3 of 4 states in each support class at each `N`;
- it emits at least four distinct physical command serializations at each `N`;
  and
- it selects at least two distinct failed-executor physical keys and one
  nonnull relay key across each failed-zone block.

The package-level competence gate requires at least 14 of 16 replicates for an
arm. These are exact finite counts, not estimates.

### State-action sensitivity

Each accepted state registers the decisive legal pair from its support
predicate. `FEATURE-FLIP` exchanges only that pair's token-specific ETA and
radio ordering fields while preserving keys, masks, all other rows and the
teacher's legality. The teacher command must change. A replicate-arm is
state-sensitive when its physical command changes on at least 4 of 12 flips at
each `N` and in every support class at least once. Package-level sensitivity
requires at least 14 of 16 replicates.

### Association-row sensitivity

`ROW-SWAP` begins after the ordinary scorer on the same state. It exchanges the
complete four-token score rows of the registered legal pair, preserves the row
multiset, public physical records, masks, null scores, decoder and all other
rows, then inverse-maps the command. Every accepted state is an opportunity. A
replicate-arm is association-sensitive when the physical command changes on at
least 4 of 12 row swaps at each `N` and in every support class at least once.
Package-level sensitivity requires at least 14 of 16 replicates.

These gates prevent a constant command, null-only controller, presentation-
blind but association-dead scorer, or nonacting decoder from passing.

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

`FREE_POSITION_ACTIVE` compares the final comparator with its own exact
position-projected clone obtained by setting `alpha=0` without changing any
other byte. In one canonical state, activity means maximum token-level total-
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

1. **INVALID_STATIC_FAMILY.** Any public-law, state acceptance, fresh-namespace,
   key uniqueness/exclusion, permutation enumeration, teacher invariance,
   legality, containment, serialization, inverse-map, trace, atomicity or
   observability failure invalidates the object. Report no architecture claim.
2. **NONIDENTIFIED_CAPABILITY_SUPPORT.** If the teacher does not satisfy the
   frozen diversity/support predicates, or neither arm reaches package-level
   state-action and association-row sensitivity, the family cannot distinguish
   commutation from a degenerate command path.
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

> In the exact finite two-zone post-loss state family, under the frozen
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
   zero r09 predecessors;
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

This revision authorizes no construction or empirical work. It first requires:

1. mathematical/causal closure in the existing same-VNFC ChatGPT External-Pro
   conversation;
2. an independently frozen External-Gemini innovation response, kept mutually
   blind from Pro; and
3. same-direction EM intake of both.

Only after Pro `CLOSED` and EM intake may Portfolio decide whether to ask
Operational Root for a same-direction CM static bindability, observability,
containment and full-cost assessment. Neither provider may review code,
technical acceptance, runtime, hashes, leases or portfolio priority.
