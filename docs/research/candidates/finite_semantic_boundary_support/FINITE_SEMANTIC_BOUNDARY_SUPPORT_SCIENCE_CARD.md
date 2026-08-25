# Finite semantic boundary support B1 science card

Owner: `direction:finite-semantic-boundary-support` Explorer Manager  
Candidate: `CAND-FSBS-ONE-BIT-CAPPED-TWO-RECORD`  
Treatment: `FSBS-B1-AUTHENTIC-ASSOCIATION-v1`

This is one new prospective, constructed-host question. VSP-04, SCOPE-1S,
ROSTER-SMF-BI, and VSP-C1 motivated the shared uncertainty but contribute no
evidence, thresholds, host instances, or acceptance to this candidate. Missing
source, host, or runner is construction cost owned by CM, not a scientific
reason to change or defer the question.

## Question, treatment, and semantic deletion

At a boundary that can open and serve only one of two sealed records, does a
valid one-bit carrier improve the value of the selected record when its bit is
authentically associated with the valuable record, relative to the same valid
carriers reassociated with worlds inside exactly matched finite strata? Can the
registered learner discover both legal choices and credit the association from
return?

- In `AUTHENTIC`, carrier semantic bit `z` equals the valuable physical record
  `t`.
- In `REASSOCIATED`, whole valid carriers are assigned from other worlds in the
  same `(split, issuer_class, route_mode, presentation, block)` stratum. Each
  four-world block has indices `0..3` and `t=(0,0,1,1)`. Recipient `j` receives
  whole carrier `pi(j)`, where `pi` is drawn uniformly before learning from
  `[(1,2,3,0),(1,3,0,2),(2,0,3,1),(3,0,1,2)]`. These are exactly the
  no-fixed-point permutations that make the comparator joint table contain
  each `(t,z')` pair once. Thus `z'` is balanced and conditionally
  uninformative, rather than a stable inverted code.
- Arms share the same latent worlds, target order, valid-carrier count, carrier
  marginals, authentication result, observation and action APIs, architecture,
  initialization, learner draws, action support, updates, work, costs, and
  resource caps. Only carrier-to-world association differs. No arm label or
  donor identity is observable.

The primary estimand is therefore the total effect of learning and acting with
authentic rather than deleted association. It is not a message-versus-silence,
capacity, authentication-presence, or extra-work comparison.

## Exact finite host and resource boundary

Each one-step episode has two private records, physical slots `0` and `1`, and
exactly one valuable target `t`. Fresh opaque record identities are never
learner features. Before the action, the learner observes only:

`(issuer_class i, route_mode r, surface_bit b, auth_ok=1, cap=1, legal_mask={0,1})`.

Here `i,r in {0,1}` are outcome-neutral public carrier/interface classes. A
finite host registry issues a token containing `(i,r,b,opaque_serial)` and
privately validates its provenance and integrity. Only the four fields above
and the Boolean validation result reach the learner; serials, registry state,
validation evidence, target, block, presentation, donor, and arm do not. This
models a valid finite carrier, not cryptographic security or issuer truth under
compromise.

For paired seed `s`, the presentation fixes two hidden label polarities
`kappa_s, lambda_s in {0,1}`:

- the visible bit is `b = z XOR kappa_s`;
- learner action `a` opens physical slot `j = a XOR lambda_s`;
- the authentic correct action is
  `a_star = b XOR kappa_s XOR lambda_s`.

The four `(kappa,lambda)` combinations occur twice across the eight seeds. This
counterbalances carrier polarity and action/slot polarity, including equal
numbers of visible copy and complement rules. Both arms of a seed use the same
presentation.

The only legal learner actions are `SELECT_0` and `SELECT_1`. Either action
opens and serves its selected record, consumes exactly one payload read and one
service slot, ends the episode, and reveals only that record's outcome. Gross
value is `4` for the target and `0` otherwise; a fixed service cost of `1`
gives return `Y=3` for the correct action and `Y=-1` for the other. The
unselected record is absent from feedback, replay, update inputs, and later
observations.

The enforced resource cap is `(payload_reads=1, service_slots=1)`. Either
one-record choice requires `(1,1)`; a complete two-record census requires
`(2,2)` and is rejected before either payload or outcome is exposed. Carrier
validation performs the same one registry lookup in both arms and is outside
the record cap. Every accepted episode therefore has identical work and cost;
the candidate-specific resource fact is the strict inequality
`R_selected=(1,1) <= R_max=(1,1) < R_all=(2,2)`.

Episodes reset all state. The learner has no recurrence, clock, block position,
or cross-episode observation. Episode order is independently shuffled within
each split using a paired world schedule. There is no partner, environment
adaptation, replay, normalization, or parameter sharing across arms.

## Pre-learning public-path support gate

No learner is initialized until one registered gate uses the same
`reset -> observe -> boundary_request -> outcome` path as training. For each of
the 16 `(i,r,kappa,lambda)` strata and both semantic arms, the gate instantiates
one four-world block with `t=(0,0,1,1)` and the arm's exact carrier rule. On
clones of all 128 arm-worlds it must:

1. force `SELECT_0` and `SELECT_1`, show that both are accepted, and record
   exactly `(1,1)` resource use for each;
2. show returns `3` and `-1` on the two counterfactual choices of every world,
   with exact nonzero contrast `4` and at least one carrier-conditioned optimal
   action change;
3. submit the well-formed two-record census request through the same boundary
   path and observe pre-read resource denial with required `(2,2)`, cap `(1,1)`,
   and no payload or outcome;
4. show that every carrier validates, learner-visible field domains and
   marginals match across arms, `AUTHENTIC` decodes to `t`, and every one of
   the four allowed `REASSOCIATED` permutations gives one instance of each
   `(t,z')` pair; and
5. show that target, unread content, serial, donor, presentation, arm, block
   position, validation internals, and future outcome have no learner path.

This is exactly 256 accepted one-record requests (two choices per arm-world)
and 128 denied two-record census requests, or 384 public boundary requests.
The gate learner state is nonexistent and all gate worlds are discarded. A
failed or incomplete gate stops before learning and means that this constructed
question was not instantiated; it is not evidence that authentic association
has no value.

Question-relevant scientific activity begins when the real registered flow has
retained this complete support/resource gate. The learning comparison begins
only with the first complete paired learner-selected transition after the gate.
A process launch, unit check, partial gate, or unpaired arm is not
question-relevant activity. A learning conclusion additionally requires paired
frozen evaluations from both arms.

## Learner and exploration-versus-credit localization

The learner is an eight-parameter linear contextual bandit. For
`x=(1, 2b-1, 2i-1, 2r-1)`, action values are `Q_a=w_a^T x`, with both four-entry
weight vectors initialized to zero. After chosen action `a` and return `Y`, the
only update is

`w_a <- w_a + (0.05/4) * (Y-Q_a) * x`.

There is no discount, bootstrap target, replay, regularization, or update for
the unchosen action. Native training is epsilon-greedy; epsilon decreases
linearly from `0.40` at update zero to `0.05` at update 384. Ties and exploration
use the paired learner draw for that episode coordinate. Frozen evaluation is
greedy with a seed-fixed paired tie rank and performs no updates.

The training cross cells are `(i,r)={(0,0),(0,1),(1,0)}`. Cell `(1,1)` is never
presented to an initialized learner and is a secondary held-out crossed-cell
test only. Every cell contains both targets and both carrier-bit marginals, so
reassociation is performed within each cell rather than borrowing support from
the held-out cell.

Let the exposure quota be `q=16`. Native training contains 32 balanced
four-world blocks per training cross cell: 384 decisions total, 64
presentations of each of the six `(i,r,b)` states. Log completed-feedback counts
`N_free(i,r,b,a)`, their minimum, first passage to `q`, conditional action
entropy, returns, updates, and signed action-value margins. Only learner-chosen
actions count as native exploration.

At update 384, clone each arm once into two prespecified equal-work branches:

- `NATURAL` receives 16 more balanced blocks per training cross cell, 192
  learner-selected decisions at epsilon `0.05`.
- `COVERAGE` receives the same 192 latent worlds and updates but externally
  follows one frozen paired coordinate-level action schedule. Within every
  training `(i,r)` cell, each of the eight `(t,z',a)` triples occurs exactly
  eight times across the 16 blocks; those same coordinate actions are applied
  to the paired `AUTHENTIC` worlds. Consequently each arm has exactly `q`
  completed transitions in each of its 12 `(i,r,b,a)` cells. In `AUTHENTIC`,
  the correct action cell contains 16 returns of `3` and the incorrect action
  cell 16 returns of `-1`. In `REASSOCIATED`, every visible-bit/action cell has
  eight of each return, exact mean `1`, and exact action gap `0`. Forced actions
  are tagged and never counted as exploration.

The coverage branch is a diagnostic intervention, not a retry or selected
checkpoint. Its deterministic feedback must reproduce the signed return
contrast in every action cell. Both terminal clones are frozen and evaluated.

Localization uses the following plain-language rules:

- If native minimum coverage is below `q`, coverage reaches `q`, and authentic
  carrier value improves specifically in `COVERAGE` relative to equal-work
  `NATURAL`, insufficient action exploration contributed to the native result.
- If native coverage reaches `q` and action-return contrasts are resolved but
  the authentic arm does not acquire positive correct-action value margins or
  beat reassociation, the limitation is downstream carrier credit/use for this
  learner and budget.
- If forced coverage resolves the contrasts but authentic value margins remain
  wrong, credit/update failed; if margins are correct but frozen choices are
  wrong, action extraction failed.
- If native coverage is low and forced exposure still yields no carrier-aligned
  policy, exploration and credit/use cannot be separated. Neither result makes
  the carrier itself valueless.

## Evaluation, strongest alternative, and interpretation

For each terminal clone, evaluation has 16 balanced four-world blocks in each
of all four `(i,r)` cells. The first three cells form the in-support result;
`(1,1)` is reported separately. For each seed, arm, branch, and domain report:

- correct-record rate and `V=4*correct_rate-1`;
- paired authentic-minus-reassociated value `tau`;
- the carrier value above the best bit-blind balanced policy, whose exact value
  is `1`;
- `Q(x,a_star)-Q(x,1-a_star)` and frozen bit-flip action sensitivity;
- native/forced cell counts, first-passage times, entropy, and update counts;
- exact resource/work totals and any anomaly.

Seeds, not episodes, are independent units. Report all eight paired seed
effects. Directional evidence for useful learned authentic association requires
all eight in-support `NATURAL` effects to be positive, their mean return gap to
be at least `1.0` (a correct-choice gap of `0.25`), and authentic mean return to
be at least `2.2`. The forced branch is interpreted separately by the
localization rules and cannot replace the natural result. A crossed-cell effect
supports only transfer to the exact held-out `(1,1)` cell and is never required
for the in-support claim.

The strongest alternative is a stable nonsemantic codebook: carrier serial,
tag, issuer, record position, timing, block order, arm mechanics, or a
copy-versus-complement optimization bias could predict the target. The frozen
feature list, private validation, fresh identities, within-cell target balance,
memoryless learner, hidden shuffled order, paired work, and four presentation
polarities close those paths prospectively.

Two frozen-policy negative controls remain decisive:

- `MASKED`: replace `b` with an independently balanced bit inside every
  `(i,r,t)` evaluation stratum while preserving validation, API, work, and
  carrier marginals. Both learned arms must then have exact balanced value `1`
  and exact gap `0`. Any retained treatment advantage is a semantic-only
  falsifier and identifies an unclosed side channel.
- `RELABEL`: report effects separately for visible copy and complement
  presentations. A benefit confined to copy presentation or reversed by label
  polarity supports optimization geometry rather than carrier association.

A positive in-support result after these controls supports only that, on this
exact finite host, authentic bit-to-target association causally improves the
learned one-record boundary decision over conditionally exchangeable
reassociation at matched resources. It demonstrates acquisition of a binary
cue-action rule, not semantic understanding. A forced-only result supports
creditability after supplied coverage and identifies native exploration as a
limitation under the stated rule. A null result says only that this learner and
budget did not separate the arms. No outcome establishes necessity of learning,
cryptographic security, provenance truth under compromise, production
prevalence, predecessor-host facts, open-support generalization, scaling,
multi-agent coordination, or deployment value.

## Seeds, budget, and CM-buildable request

Paired base seeds are `[11,23,37,53,71,89,107,127]`. In that order,
`(kappa,lambda)` is `[(0,0),(0,1),(1,0),(1,1)]` repeated twice. World order,
donor permutation, learner choice, and evaluation tie ranks use separate
counter-keyed namespaces; the two semantic arms share the corresponding world
and learner draws but never parameters or transitions.

Per arm and seed there are 384 native decisions, 192 decisions in each of two
continuation clones, 256 ordinary frozen evaluations per clone, and 256 masked
evaluations per clone: 1,792 one-step transitions. Across two arms and eight
seeds the registered learning/evaluation total is 28,672 transitions. With the
384 fixed pre-learning boundary requests, the registered full has exactly
29,056 host interactions. Cap the single registered full at 32,000 host
transitions, one CPU worker, five wall minutes, and 1 GiB peak memory. There is
one final checkpoint per branch, no validation-based choice, tuning, sweep,
early stop, retry, or reduced scientific run. A cap breach or incomplete paired
output is inconclusive, not a negative carrier result.

CM should construct an isolated host, finite carrier registry and balanced
donor allocator, learner, registered full runner, analyzer, and ordinary
contract tests from this card. The retained scientific result should contain
the full support/resource gate, declared and actual counts, per-seed per-branch
metrics, exploration and credit localization fields, ordinary/masked/relabel
controls, the held-out crossed cell, resource/work equality, material
anomalies, and whether the activity criterion and paired frozen evaluation were
reached. Equivalent isolated file paths do not change the scientific identity.
No pre-result Pro request is needed.
