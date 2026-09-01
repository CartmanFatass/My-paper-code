# FRRIE B01 between-arm action-probability TV clarification intake

## Authority and outcome

This note reconciles the complete second round of the persistent
`em:finite_resource_relational_inductive_efficiency:innovator` decision node. It resolves only the
previously ambiguous post-contact action-probability total variation between `PHY_TRUST` and
`EDGE_FLEX` inside `FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901`.

- `FINAL_INNOVATOR_DECISION=CLARIFY_BETWEEN_ARM_TV`
- `DECISION_FORMED=true`
- `BLOCKER=NONE`
- `SELECTED_HISTORY_ANCHOR=SYMMETRIC`
- `MEASUREMENT_ROLE=MANDATORY_DESCRIPTIVE_NON_GATE`

The response was naturally completed and archived under request
`frrie-em-innovator-b01-action-tv-clarification-20260901-02`. Its response SHA-256 is
`89cb70649b58c70cd0735c86091d95288691e6e17bcd7da4e2e3d581e9571cee`.

## Question and inputs

The exact question was whether the between-arm TV should use each arm's different natural input,
one arm's shared input, or a symmetric shared-input construction, and how to freeze its coordinates,
raw rows, reducer, contact availability, and scientific role without changing any other B01 term.
Pro read the eight manifest-listed paths at pinned GitHub ref
`f198cedf8b0bb2c06b6e79ed3415e08b6e197477`, including the direction record, evidence standard,
old reusable freeze, and direct arm/training/evaluator definitions.

## Direct decision observation

### Symmetric two-anchor object

At each existing evaluation predecision coordinate, construct two common-input comparisons:

1. `PHY_TRUST` anchor: use the natural factual PHY full-roster observation, public roles, legal
   masks, and incoming hidden state; evaluate both checkpoint policies on those identical inputs.
2. `EDGE_FLEX` anchor: use the natural factual EDGE inputs and again evaluate both policies on the
   identical inputs.

The reported per-coordinate value is the equal-weight average of the two anchor-specific TVs. This
rejects the confounded quantity that compares `PHY` on `(O_PHY,H_PHY)` directly with `EDGE` on
`(O_EDGE,H_EDGE)`. The selected object instead compares policy mappings while holding the complete
actor input fixed within each anchor, then avoids privileging either arm's visited-state occupancy.

For `SEMANTIC_COLUMN_ROTATE`, each anchor is that arm's natural factual rollout under the existing
intervention. Both checkpoint policies receive the same already-rotated policy-facing input. No
second rotation is applied, and intact and rotated vectors are never compared across arms.

### Coordinates and canonical row order

The raw coordinate is

`(seed_block, checkpoint_update, roster, intervention, episode, slot, entity, anchor_arm)`.

The clarification gives the diagnostic serialization order as:

1. existing B01 seed order;
2. checkpoint `0,32,64,128,256,512`;
3. roster `9,15,6,21`;
4. intervention `INTACT,SEMANTIC_COLUMN_ROTATE`;
5. episode `0..255`;
6. slot `0..11`;
7. entity `0..N-1`;
8. anchor `PHY_TRUST,EDGE_FLEX`;
9. action `SCAN,UPLINK,LISTEN_WEST,LISTEN_EAST,FORWARD_BASE,HOLD`.

This roster ordering is only the new diagnostic's serialization order. The same Pro response
explicitly keeps every other B01 term unchanged, so it does not reorder the already frozen B01
primitive-panel roster order `(6,9,15,21)`.

The complete actor inputs at an anchor are the full `FP32[N,22]` observation tensor, public role
vector, full legal-mask tensor, and incoming `FP32[N,64]` hidden tensor. An entity row alone is
insufficient because the shared policy graph constructs relational summaries from the roster.

### One-step and side-effect boundary

For each anchor, the anchor arm's factual vector may be reused or recomputed with direct equality.
The non-anchor policy is evaluated exactly once on the same inputs. Its output hidden state is
discarded. The shadow call samples no action, draws no RNG, and advances or changes no environment,
factual hidden state, action tape, reward, transition, learner exposure, optimizer, checkpoint,
adaptation record, evaluation trajectory, or B01 work account. No training-history shadows are
added; only the six existing evaluation checkpoints are in scope.

### Tight-contact binding and availability

For seed `s`, let `kappa_s` be the first update `k in 1..512` at which the stored FP32 bytes of the
post-Adam, preprojection PHY `beta` differ from the stored FP32 bytes after projection into
`[-0.15,0.15]`. Merely reaching a real boundary without changing an FP32 value is not contact.
Adam moments remain unprojected. If contact never occurs, `kappa_s=infinity`.

The diagnostic is available at checkpoint `u` exactly when `kappa_s <= u`. Therefore checkpoint
zero is always unavailable. Pre-contact values are unavailable rather than zero. If contact has not
occurred by update 512, all checkpoints are unavailable; the update-512 reason is
`NO_TIGHT_CONTACT_BY_512`, while earlier checkpoints use `PRE_TIGHT_CONTACT`.

Once `kappa_s <= u`, the diagnostic is required for every otherwise available roster/intervention
cell at that checkpoint. This availability rule adds no result branch.

### Legal support and exact TV

Each policy output is the complete six-action FP32 vector in canonical action order. Public role
defines the common legal mask:

- surveyor: `SCAN,UPLINK,HOLD`;
- relay: `LISTEN_WEST,LISTEN_EAST,FORWARD_BASE,HOLD`.

For both policies, all components must be finite and nonnegative, illegal probabilities must be
exactly zero, legal mass must sum to one within the existing FP32 tolerance, and every legal action
must retain the existing `0.04/m` floor. No renormalization is allowed.

For anchor `b`, entity `i`, and legal action set `A_r(i)`:

`TV_b = 0.5 * sum_{j in A_r(i)} abs(p_PHY|b[j] - p_EDGE|b[j])`.

Because illegal mass is exactly zero, the six-column expression is identical. The symmetric row is
`TV_sym = 0.5 * (TV_PHY_anchor + TV_EDGE_anchor)` and lies in `[0,1]`.

To derive a row, decode the stored FP32 probability bits exactly into binary64, take absolute
differences in canonical action order, reduce with binary64 `math.fsum`, and divide by two. No
scientific threshold attaches to this value.

### Raw schemas and direct validation

One available raw row is emitted for every `(s,u,N,c,e,t,i,b)`:

```text
FRRIE_B01_BETWEEN_ARM_TV_RAW_V1 {
  seed_block,
  checkpoint_update,
  roster,
  intervention,
  episode,
  slot,
  entity,
  role,
  anchor_arm,
  anchor_history_kind=NATURAL_FACTUAL_PREDECISION,
  tape_identity,
  first_tight_contact_update,
  available=true,
  legal_mask[6],
  phy_probability_bits_u32[6],
  edge_probability_bits_u32[6],
  tv_binary64
}
```

The two probability arrays are literal IEEE-754 binary32 bit patterns. Validation must decode them,
recheck finiteness, nonnegativity, exact illegal zeros, legal sum tolerance, legal floor, and the
direct TV formula. Stored `tv_binary64` is derived and must equal this recomputation; it is not an
independent source value. `tape_identity` binds the existing same-coordinate B01 addressed
evaluation tape. The natural trace and immutable checkpoint provide conformance evidence that both
actor calls used the same anchor input; the raw TV row need not duplicate the full observation and
hidden tensors.

An unavailable cell emits no fabricated decision rows and instead emits:

```text
FRRIE_B01_BETWEEN_ARM_TV_AVAILABILITY_V1 {
  seed_block,
  checkpoint_update,
  roster,
  intervention,
  first_tight_contact_update,
  available=false,
  availability_reason=PRE_TIGHT_CONTACT|NO_TIGHT_CONTACT_BY_512
}
```

### Reducers and inventory

For a fixed anchor and `(s,u,N,c)`, average equally over `256 * 12 * N` factual predecisions. The
symmetric cell mean is the equal half-weight average of the two anchor means. At fixed `(u,N,c)`,
report each available seed, arithmetic mean, median, minimum, maximum, and the exact count and IDs of
seeds satisfying `kappa_s <= u`. If none has contacted, report `NO_POST_CONTACT_SEEDS`; never insert
zeros.

There is no pooling across checkpoints, rosters, or interventions and no maximum-over-checkpoints,
AUC, first-crossing, work-to-threshold, pooled train/held-out, or pooled intact/rotated quantity.
Early checkpoint summaries are conditional on the contacted-seed subset and are not a fixed-cohort
trajectory unless that subset is unchanged.

One available checkpoint contains
`2 anchors * 256 episodes * 12 slots * 2 interventions * sum(6,9,15,21) = 626,688`
raw rows per seed. An unavailable checkpoint has eight cell-level availability records. Because
`u=0` is necessarily pre-contact, the maximum when contact occurs by update 32 is `3,133,440` raw
rows per seed, `9,400,320` for the initial three seeds, and `15,667,200` for all five. These counts
support streaming or compressed exact-bit storage; they do not change scientific work accounting.

## Role, missingness, and claim exclusions

This metric is mandatory descriptive but non-gating. It is not one of the ordered 28, has no
threshold, and appears in no B01 branch or promotion rule.

- A pre-contact checkpoint is validly unavailable, not missing, zero, invalid, or a failed
  scientific predicate.
- No contact through update 512 leaves the diagnostic unavailable and does not replace the existing
  observed-path contact/equivalence interpretation.
- A finite positive value is reported descriptively.
- Exact zero is valid shared-anchor one-step policy-vector equality only; it does not establish
  parameter, trajectory, return, causal, or universal equality.
- A missing or nonfinite required post-contact row is
  `UNAVAILABLE_MEASUREMENT_DEFECT` for the affected diagnostic scope. It blocks only a claim about
  this metric's magnitude and creates no new `B01_INVALID`, result branch, threshold, or promotion
  consequence.
- Different inputs within an anchor, propagated non-anchor hidden state, a sampled shadow action, or
  an environment step is a different measurement and cannot be reported as this diagnostic.

The symmetric diagnostic remains conditional on the two arms' endogenous visited-state
distributions. The non-anchor policy can also receive an anchor-generated recurrent state outside
its natural recurrent-state manifold. It therefore measures one-step policy-map discrepancy on an
equal mixture of visited evaluation histories. It does not identify natural trajectory distance,
the causal contribution to return, the origin of divergence, propagated behavior, representation,
recurrence, optimizer history, semantic correctness, or a relational mechanism.

The ordered-28 `V_u(N)` remains the intact PHY policy versus its one-step rotated PHY shadow and is
not substituted, pooled, or satisfied by this between-arm metric. The study identity, population,
seeds, budget, checkpoints, panels, support, work, comparator competence, branches, promotion,
claim ceiling, adaptation record, and R01/R02 separation are unchanged.

## Judgment impact and implementation acceptance

The missing measurement anchor is now scientifically frozen. CM can implement it without choosing
a new estimand. Technical acceptance requires exact coordinate coverage after contact, explicit
pre-contact availability records, shared full-roster actor inputs within each anchor, zero side
effects, literal FP32 probability bits, direct recomputation of every row and reducer, and no use of
the metric in scientific branch selection. A defect in this sidecar measurement is repairable and
must not be converted into scientific polarity.

## Evidence paths

- `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/frrie-em-innovator-b01-action-tv-clarification-20260901-02/RESPONSE.md`
- `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/frrie-em-innovator-b01-action-tv-clarification-20260901-02/TRANSPORT_FACTS.json`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md`
- `docs/research/candidates/finite_resource_relational_inductive_efficiency/INFERENCE_AND_EXECUTION_FREEZE.md`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/constants.py`
- `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/contract.py`
