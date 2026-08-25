# Dual-epoch authenticated-receipt survival B1 science card

Owner: `direction:dual-epoch-authenticated-receipt-survival` Explorer Manager  
Candidate: `CAND-DUAL-EPOCH-AUTHENTICATED-RECEIPT-SURVIVAL`  
Treatment identity: `DEARS-B1-DUAL-VERIFIER-v1`

This is a prospective construct-first experiment. It does not ask whether a suitable
host already exists in the repository.

## Question

In the matched one-decision host below, can a small fixed-budget policy learn from a
fail-closed verifier output `(live, content)` to choose `USE_0`, `USE_1`, or `RESET`
with high probability in every authentication/owner-lineage/skill-lease-lineage
cell, including on held-out opaque handles, epoch values, and lease-handoff time
offsets? Does that verifier summary confer a finite-data generalization advantage
over an exactly capacity-matched generic GRU given the raw relational history?

`live` means that the receipt is authentic and authorized, its owner lineage still
connects the write version to the current owner version, and its skill/lease lineage
still connects the write lease to the current live lease without a coverage gap.
The verifier exposes the written bit only when all three facts hold. The question is
about sufficiency and finite-budget learnability of that abstraction in this host,
not about whether dual lineage is necessary in arbitrary systems.

## Host and unique correct action

One episode contains five history events followed by exactly one decision. The
visible decision snapshot is the same in every member of a matched superblock:

- final owner name `owner`, one-member visible roster `actor`, skill name
  `apply_bit`, decision clock `0`, physical observation `0`, previous reward `0`,
  history-event count `5`, and action support `{USE_0, USE_1, RESET}`;
- the final current owner version, final current skill/lease version, and final
  visible lease interval are also held fixed within the superblock;
- no arm label, semantic-cell label, correct action, forge subtype, lineage-survival
  bit, or break locus appears in the visible snapshot.

The five chronological events are one receipt write, two owner updates, and two
skill/lease updates. The four updates use each of the six orderings that preserve
the within-owner and within-skill order. The receipt carries a displayed bit
`b in {0,1}` and anchors an owner `(handle:u32, epoch:u32)` and a skill/lease
`(handle:u32, lease_epoch:u32)`. All handles and epochs are opaque nonzero values.

Let:

- `A=1` iff the receipt tag is intact and its issuer is authorized;
- `O=1` iff the two owner-update `from` tuples make an unbroken exact chain from
  the receipt's owner anchor to the final owner version;
- `L=1` iff the two skill/lease-update `from` tuples make an unbroken exact chain
  from the receipt's skill/lease anchor, neither renewal leaves a positive coverage
  gap, and the final lease covers decision time `0`.

An unmatched `from` tuple or a positive coverage gap kills that lineage permanently;
a later update cannot resurrect receipt authority. All update records themselves
are host-trusted. Define `live = A & O & L`. The unique correct action and immediate
terminal reward are:

| Condition | Correct action | Reward |
|---|---|---:|
| `live=1, b=0` | `USE_0` | `+1` |
| `live=1, b=1` | `USE_1` | `+1` |
| `live=0` | `RESET` | `+1` |
| any other action | not correct | `-1` |

Training is supervised from this unique action label; no current reward is an input.
This experiment therefore tests representation and held-out relational
generalization, not exploration, temporal credit assignment, or learning from
return.

## Exact lineage and forgery interventions

The receipt anchor, both update `to` tuples, final current tuples, event count,
event ordering, final snapshot, and nuisance draw are paired within a superblock.
Only the following science-bearing fields change between its variants:

- Owner survival: for `O=1`, both owner `from` tuples match the current chain tip.
  For `O=0`, exactly one prespecified edge uses a fresh unrelated `from` tuple; the
  following edge still ends at the paired final owner version. Edge 1 and edge 2
  breaks are balanced.
- Skill/lease survival: for `L=1`, both `from` tuples match and both lease intervals
  overlap. For `L=0`, either one prespecified edge uses an unrelated `from` tuple
  with timely intervals, or all tuples match but one prespecified edge has
  `new_valid_from - previous_valid_until = +m`. Reference-break versus gap-break
  and edge 1 versus edge 2 are balanced. A timely designated edge instead uses
  offset `-m`. Historical expiry changes never alter the paired final clock or
  final visible interval.
- Authentication: a genuine receipt has `tag_ok=1` and `issuer_allowed=1`.
  `PAYLOAD_FLIP_BAD_TAG` has an altered displayed payload and `tag_ok=0` with the
  designated issuer. `FOREIGN_ISSUER` has a structurally valid tag under an
  unapproved issuer, so `tag_ok=1` and `issuer_allowed=0`. Both forged modes must
  produce `live=0` and bottom content, regardless of the two lineage facts.
- Content: `b=0` and `b=1` are crossed with every other semantic fact. For a bad-tag
  forge, `b` means the displayed post-alteration bit.

Authentication is a host oracle over these two primitive checks. The experiment
does not model cryptographic strength. Malformed, ambiguous, missing, duplicate, or
multi-receipt input is outside B1; the verifier is nevertheless fail-closed for such
input and returns `(0, bottom)`.

The verifier applies this order: parse exactly one receipt; require `tag_ok` and an
authorized issuer; require the exact two-edge owner chain; require the exact
two-edge skill/lease chain, nonpositive handoff gaps, and final coverage; then and
only then return `(1,b)`. Every earlier rejection returns `(0,bottom)`.

## Semantic cells and matched panel

Every superblock crosses all 16 core cells `(A,O,L,b)`. Analysis refines those into
90 cells:

- authentication detail: `GENUINE`, `PAYLOAD_FLIP_BAD_TAG`, or `FOREIGN_ISSUER`;
- owner detail: `SURVIVES`, `BREAK_EDGE_1`, or `BREAK_EDGE_2`;
- skill/lease detail: `SURVIVES`, `REFERENCE_BREAK_EDGE_1`,
  `REFERENCE_BREAK_EDGE_2`, `GAP_EDGE_1`, or `GAP_EDGE_2`;
- displayed content: zero or one.

For each seed and arm, every reported refined cell averages all of its held-out
examples before the minimum over cells is taken. Also report the four matched
action flips, restricted to genuine receipts where appropriate: changing only
owner survival, only skill/lease survival, only authentication, or only `b` while
both lineages survive.

Opaque values are sampled without replacement from the full nonzero `u32` domain.
Train, validation, and test pools are disjoint for every owner handle, skill handle,
owner epoch, and lease epoch, including unrelated predecessor tuples. Rejection
sampling, rather than disjoint numeric ranges or prefixes, enforces the split, so a
split can not be inferred from a value range.

The designated lease-handoff magnitude is also held out:

| Split | timely offsets | gap offsets |
|---|---|---|
| train | `{-12,-8,-4}` | `{+4,+8,+12}` |
| diagnostic validation | `{-10,-6}` | `{+6,+10}` |
| held-out test | `{-11,-9,-7,-5,-3,-1}` | `{+1,+3,+5,+7,+9,+11}` |

All times are signed integer ticks relative to decision time zero. Receipt write and
four update times are strictly increasing and precede zero. Each renewal begins at
its update time; the predecessor expiry is chosen to realize the designated
handoff offset. The other renewal has fixed overlap `-2`. The final lease always
covers zero. Event position, absolute timestamp, nonce, displayed tag material,
opaque values, and unused subtype selectors are counterbalanced or independently
randomized and never correlate with a semantic bit.

## Treatment, comparators, and information ceilings

All learned arms get the same final visible constants and differ only in the named
extra channel:

| Arm | Extra information | Worst-cell information ceiling |
|---|---|---:|
| `GRU-DUAL` (treatment) | verifier `(live,b)` or `(0,bottom)` | `1` |
| `GRU-SNAPSHOT` | none | `1/3` |
| `GRU-UNBOUND` | authenticated/authorized receipt bit `A` and displayed `b`, but no owner or skill/lease survival | `1/2` |
| `GRU-VALIDITY` | `live`, but no content | `1/2` |
| `GRU-ORACLE` | ground-truth `A,O,L,b`, but not the correct action | `1` |
| `GRU-RAW` | full raw relational tokens and primitive `tag_ok`/`issuer_allowed`, but no derived `O`, `L`, or `live` | `1` |

The ceilings are maximin observation bounds, not expected learned scores.
`GRU-SNAPSHOT` must distribute probability over three different correct actions
that share one observation, so its best possible minimum is `1/3`.
`GRU-UNBOUND` cannot distinguish `USE_b` from `RESET` among genuine same-`b`
lineage twins, and `GRU-VALIDITY` cannot distinguish `USE_0` from `USE_1` among
live twins, so each is bounded by `1/2`. The raw history contains all required
relations and therefore has information ceiling one; whether this finite GRU learns
them on new symbols and offsets is empirical.

`RULE-DUAL` is a nonlearned reference: return `RESET` on `(0,bottom)`, otherwise
return `USE_b`. It must have worst-cell correctness one. It is also the strongest
alternative to any learning claim: the verifier has already computed the difficult
conjunction and a deterministic three-case decoder is sufficient.

## Common token schema and exactly matched learner capacity

Every learned arm receives six fixed-width tokens: receipt, four updates, and
decision for `GRU-RAW`; five `MASK` tokens and one decision token for summary arms.
Each token is a fixed, nonlearned 192-bit/binary feature vector with:

- a token-kind one-hot code;
- two `(handle:u32, epoch:u32)` slots, used as receipt anchors, update
  `from`/`to` tuples, or final current tuples according to token kind;
- three signed 16-bit time fields (`event_time`, `valid_from`, `valid_until`);
- presence, displayed-content, `tag_ok`, `issuer_allowed`, `live`, and bottom flags;
- zero padding. Integers are represented bitwise, not as normalized scalar IDs.

Disallowed fields are zero and have zero presence bits. `GRU-RAW` gets no composite
lineage or live bit. Summary arms get no raw receipt or update tuple. This schema,
the masking transform, and the semantic label must be emitted in the result contract
so information leakage is testable.

Each learned arm uses exactly one GRU layer with input size 192, hidden size 48,
zero initial state, no dropout, no attention, and a `48 -> 3` affine action head.
There are exactly 34,995 trainable parameters and no learned input embedding. Thus
`GRU-RAW` is capacity-matched to every summary arm rather than receiving a larger
model. Every arm is initialized independently from the same paired model seed and
trains its own weights; no parameter, gradient, label prediction, or hidden state
crosses arms or examples.

Use multiclass cross-entropy, AdamW (`lr=0.001`, betas `(0.9,0.999)`,
`eps=1e-8`, weight decay `1e-4`), batch size 256, gradient-norm clip 1.0, and exactly
20 shuffled epochs. The final epoch-20 checkpoint is evaluated with temperature-one
softmax. There is no early stopping, checkpoint selection, restart, hyperparameter
tuning, or augmentation. Validation is reporting-only.

## Seeds, exact counts, and caps

Base seeds are `[13,29,43,59,73,89,103,127,149,181]`. Counter-keyed namespaces
separate world/template generation, opaque values, tags/nonces, minibatch order,
and model initialization. Arms share the paired generated examples and label order.

A superblock contains the 16 core semantic variants. Its nuisance schedule is the
Cartesian product of six legal update interleavings, two forge modes, two owner
break loci, two skill/lease break modes, two skill/lease break loci, and the split's
handoff magnitudes. Train adds two independent repetitions.

| Split | Superblocks per seed | Examples per arm and seed | Use |
|---|---:|---:|---|
| train | `576` | `9,216` | 20 fixed epochs |
| validation | `192` | `3,072` | diagnostic only |
| held-out test | `576` | `9,216` | sole conclusion panel |

Across six learned arms and ten seeds, training is exactly 11,059,200 example-passes;
validation plus test is 737,280 passes. The registered run is capped at one CPU
worker, 12,000,000 total learned example-passes, 60 minutes wall time, and 2 GiB
peak RSS. A cap breach or incomplete paired panel yields no scientific conclusion
and returns to CM as unchanged-science engineering work. There is no reduced-budget
scientific run; ordinary generator, verifier, masking, ceiling, count, and rule
checks precede the registered train/evaluate/analyze flow.

## Primary observable and prespecified support statements

For seed `s`, arm `a`, and refined held-out semantic cell `c`, let

`q[s,a,c] = mean_x pi_a(correct_action(c) | x)`.

The primary seed-level observable is

`W[s,a] = min_c q[s,a,c]`

over all 90 refined cells. Report every `q`, every `W`, mean `W` over ten seeds,
two-sided 95% Student-t intervals over seed-level values, and paired seed-level
intervals for `GRU-DUAL` minus each comparator. Also report worst-cell greedy
top-one accuracy, the four matched action-flip accuracies, action probabilities by
forge subtype and break subtype, all split/domain overlap checks, and declared and
actual counts/caps.

The following statements are separate rather than one omnibus pass label:

- Learned verifier sufficiency is supported when the 95% lower bound for
  `W[GRU-DUAL]` is above `0.90` and the paired 95% lower bound for
  `W[GRU-DUAL] - W[GRU-ORACLE]` is above `-0.05`.
- A finite-budget abstraction advantage over raw recurrence is supported only when
  the paired 95% lower bound for `W[GRU-DUAL] - W[GRU-RAW]` is above `0.10`.
- `GRU-RAW` within `0.05` of `GRU-DUAL`, or a paired interval spanning that band,
  supports no abstraction-advantage claim even if both are excellent.
- Any snapshot score above `1/3 + 1e-6` or unbound/validity score above
  `1/2 + 1e-6` contradicts the frozen information partition and indicates leakage,
  incorrect matching, masking, or analysis. It is not evidence of a better policy.
- `RULE-DUAL` must equal one on every generated example. `GRU-ORACLE` with a 95%
  lower bound at or below `0.90` prevents attributing a raw-history shortfall solely
  to representation, because the common learner or budget did not reliably learn
  even the explicit semantic factors.

## Scientific activity start and interpretation

Question-relevant scientific activity begins only when the frozen final checkpoint
from all six learned arms has evaluated the same first complete held-out superblock
and emitted its three action probabilities, unique correct label, refined cell,
receipt-authentication facts, lineage facts, and split-membership facts. Training
logs, a fixed-rule check, unit tests, serialization, a partial semantic panel, or an
unpaired arm are not question-relevant output.

Interpret complete output as follows:

- High `GRU-DUAL`, exact `RULE-DUAL`, and low `GRU-RAW` support a finite-budget
  held-out-symbol/time abstraction advantage for the verifier in this host.
- High `GRU-DUAL` and high `GRU-RAW` show that both the summary and generic raw
  recurrence suffice here; they do not show that the verifier abstraction is
  necessary or empirically superior.
- High `GRU-DUAL` with failure restricted to forged cells does not support
  fail-closed authenticated use. Failure restricted to either owner-break or
  skill/lease-break cells supports no dual-lineage claim; report the surviving axis
  only as a descriptive result.
- Low learned `GRU-DUAL` with exact `RULE-DUAL` shows that the summary is
  deterministically sufficient but was not learned under the frozen optimizer and
  budget. It does not refute the verifier semantics.
- A ceiling violation, wrong rule action, split overlap, missing semantic cell, or
  inconsistent label makes the run non-identifying and returns to CM for
  unchanged-science repair. Output before the activity-start criterion is likewise
  engineering provenance, not a negative treatment result.

The strongest alternative explanation for learned success is direct label decoding:
`(0,bottom)`, `(1,0)`, and `(1,1)` already form a lossless three-symbol action code.
The experiment can establish that this fail-closed code survives the held-out panel
and is easier than raw relational parsing for the frozen learner; it cannot establish
autonomous lineage reasoning or a need for learning.

## Claim ceiling and CM construction request

Any supported claim is limited to this constructed one-receipt, two-edge-per-lineage,
one-decision, binary-content host; trusted update records; host-oracle tag and issuer
checks; the two named forgery modes; the fixed supervised GRU; the exact matched
panel, seeds, and finite budget; and held-out values drawn from the stated domains.
It does not establish cryptographic security, real provenance, production benefit,
open-ended or concurrent histories, multiple writers or receipts, revocation races,
arbitrary lineage depth, online reinforcement learning, causal discovery, semantic
necessity of two epochs, or superiority over `RULE-DUAL`. A gap over `GRU-RAW`
applies only to this architecture, data volume, and shift panel, not to generic
sequence models.

CM should construct an isolated generator and matched host, fail-closed verifier,
the six learned arms and `RULE-DUAL`, the registered train/evaluate/analyze runner,
and ordinary deterministic contract tests from this card. The retained result must
contain the per-seed/per-cell action probabilities, primary and paired intervals,
information-ceiling checks, matched flips, split-disjointness facts, declared and
actual counts/caps, material anomalies, and whether the activity-start fact occurred.
Suggested fresh implementation namespace is `experiments/candidates/dual_epoch_receipt_survival/`
with tests under the corresponding candidate test namespace and retained result
`docs/research/candidates/dual_epoch_receipt_survival/DEARS_B1_RESULT.json`;
equivalent isolated paths do not change the science. Missing host, verifier, runner,
adapter, or analyzer is CM construction work and never a scientific rejection.

No pre-result Pro request is warranted: the strongest alternative, leakage tests,
information ceilings, interpretation boundary, and next discriminator are already
fixed. A completed loop may use its one result-convergence scientific review.
