# G1 Project Manager code-side reconciliation

semantic_author=project_manager
artifact_scope=reviewer_visible_code_side
scientific_authority=external_pro
repair_owner=project_manager

assignment_id=G1_CODE_SIDE_RECONCILIATION_AND_REALIZATION
pm_source_commit=719ccf133936711d002bee965c3433a73979d755
external_pro_raw_sha256=1ba6bdd5a8f776c1840462037a6303d587d9dc7777bf064ef2d360d36bc2781f
adoption_authority=external_pro_raw_only
formal_compute_status=unauthorized

## Code-side disposition

`PROTECTED_SOURCE_CONTRACT_INCOMPLETE`

The exact external-Pro raw selects an independent Option A temporal-duty
source and freezes important source semantics, but it does not uniquely define
the complete environment, learning objective, evaluation distribution, or
evidence exposure needed for an executable G1 implementation. Filling those
fields with Project Manager defaults would select scientific objects that the
raw did not select.

This is not a rejection of the selected source and not an implementation
failure. It is a fail-closed code-side reconciliation at the boundary between
scientific definition and executable realization.

## Scientific object frozen by the exact raw

The following content is executable authority once the remaining fields are
specified:

- G1 is `ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1`, an independent source; the
  exact G0 pair remains permanently closed as `NO_ACCESS_THIS_BENCHMARK`.
- The source uses Option A: a clean-infrastructure temporal-duty task.
- OR/DUM/EHC remain the three arms. DUM and EHC retain matched capacity and
  exposure; only EHC adds
  `primitive_logits = base_logits + W_z(m*z)`.
- Primary `G = U_EHC - U_DUM` remains unchanged.
- Primitive actions are `{-1, 0, +1}`.
- Each lifecycle owns physical state, hidden duty, active duty age,
  accumulated duty performance, and recurrent state. The policy receives no
  identity.
- Hidden duty is in `{-1,+1}` and active duration is in `{6,10,14,18}`. A
  short cue reveals the duty; after it expires, duty, future duration, and
  future membership are hidden.
- Lifecycle success requires at least `0.75` correct active actions and correct
  duty behavior on the final two active steps.
- JOIN, temporary LEAVE, REJOIN, and terminal LEAVE preserve anonymous
  lifecycle ownership. Temporary absence freezes recurrent, commitment,
  segment-clock, and duty state; REJOIN restores them.
- Cue time, duty mode, duration, and membership shocks are independent, so a
  calendar scheduler or primitive-reactive policy cannot recover the hidden
  duty after cue removal.
- First-match order is operational invalidity, source non-identifiability,
  access, underpowered access, then mechanism/battery interpretation.
- Access passes at `LCB95(max_a U_a) >= 0.80`; equality passes. A source-wide
  `UCB95(max_a U_a) < 0.80` yields `NO_ACCESS_THIS_G1_SOURCE`.
- Mechanism support requires `LCB95(G) > 0.10`; `UCB95(G) <= 0.10` is the
  matched accessible-scope failure condition.
- The K-bin, `I_TV`, natural KEEP/RENEW, held-out transport, ordinary recurrent
  reduction, and mutually exclusive result meanings remain post-access only.
  The existing frozen battery predicates, confidence construction, and numeric
  thresholds carry forward unchanged.

## Protected fields not frozen by the exact raw

| Missing field | Why code cannot choose it | Minimum exact scientific content required |
| --- | --- | --- |
| Physical state and transition | The raw names `x_i` and calls the action local control, but gives no dynamics or relationship between `x_i`, action correctness, duty accumulation, and termination. Different choices make memory necessary, optional, or irrelevant. | State coordinates, reset values, transition equations, action-to-state mapping, bounds, and termination/failure rules. |
| Actor and critic observation | The raw states cue visibility, post-cue hiding, anonymity, and no identity, but gives no tensor fields, cue duration/encoding, actor/critic asymmetry, global critic inputs, or legal history. These choices determine information access and leakage. | Exact actor and critic observable fields at every lifecycle phase, cue encoding and length, masks, global context, and history boundary. |
| External reward and utility | The raw defines a lifecycle success predicate but never defines per-step reward, terminal episode utility `U`, lifecycle aggregation, normalization, or failure penalties. PPO gradients and both access and G depend on them. | Reward at every transition, episode utility formula/range, lifecycle weighting, normalization, and terminal/failure treatment. |
| Train and held-out distributions | The duration support is specified, but sampling probabilities, cue-time law, JOIN/LEAVE/REJOIN/terminal schedule, roster process, episode horizon, and held-out duration/schedule/roster supports are not. The raw requires unseen held-out transport but does not define it. | Numeric training and held-out distributions, horizon, roster limits, membership-event laws, duration split, cue-time law, and episode pairing. |
| G1 source identifiability and frozen-battery mapping | The raw names `NON_IDENTIFIABLE`, sufficient heterogeneous K support, intervention, natural KEEP/RENEW, and held-out transport, but supplies no G1-specific support quotas, eligible selection strata, held-out admission rule, or mapping from the new task outcome to the existing battery inputs. The frozen battery itself is not open for correction. | Exact G1 identifiability quotas/floors, eligible selection strata, held-out admission, and task-specific consequence observables that feed the unchanged battery predicates, confidence construction, and numeric thresholds. |
| Conclusion-bearing exposure and RNG | The raw gives no update/interaction budget, paired replicate count, evaluation episodes/cells, PPO exposure, bootstrap repetitions/unit, seed values, or task/event/action RNG namespace. These determine uncertainty and formal claim scope. | Exact budget, paired replicates, evaluation grid, PPO passes/exposure, bootstrap contract, new seed list, and RNG ownership/coupling. |

## Why existing values cannot fill the gaps

The accepted clean carrier reuses Generic-SHORT observations, terminal utility,
fixed membership ledger, and a task-neutral actuator trace. Persistent
commitment is decorative in that task. Inheriting those values would not
instantiate the raw's hidden temporal duty.

The G0 implementation and runner hard-code a different noncalendar tracking
environment, 15-dimensional observation, horizon, utility, `0.78` access
floor, support quotas, budget, seeds, checkpoint kind, schemas, and result
labels. Reusing any of those unselected source values would modify or rescue
the permanently closed G0 pair. The raw explicitly sets a new `0.80` access
criterion for G1 but does not authorize the remaining G0 contract.

Mechanical intake records exact transport and raw integrity only. Its
`Transport quality: COMPLETE` field is not semantic completeness and cannot
fill a missing scientific field.

## Safe engineering realization once the source is complete

The Project Manager can then implement an independently named active line:

1. a new G1 ledger/environment defining hidden duty, cue lifecycle, temporary
   absence, task state, reward/utility, train/held-out generators, snapshot,
   and RNG ownership;
2. a new G1 OR/DUM/EHC adapter that reuses verified anonymous lifecycle and
   event-held commitment mechanics without changing G0 modules or schemas;
3. a new G1 runner/analyzer with independent checkpoint and artifact schemas,
   first-match `0.80` access before the frozen mechanism battery, and strict
   formal/nonformal separation;
4. focused RED/GREEN tests for source dynamics, cue hiding, lifecycle freeze,
   observation leakage, reward reconstruction, distribution closure,
   access/identifiability precedence, RNG/replay/checkpoint integrity, and
   tamper rejection; and
5. one bounded CPU/one-thread nonformal shared-core exercise followed by an
   independent code-side review.

Implementation-only choices such as module boundaries, tensor packing,
vectorization, schema layout, API naming, fail-closed validators, and test
decomposition remain PM-owned after the scientific values above are frozen.

## Bounded recovery completed

1. Audited every executable field against the exact raw. Result: the six
   protected groups above are absent or only qualitatively constrained.
2. Mapped clean-source, anonymous lifecycle, G0 EHC, runner, analyzer, schema,
   and test interfaces. Result: only lifecycle mechanics, primitive support,
   and selected EHC mechanics are safely reusable.
3. Tested whether a parameterized skeleton could defer the missing values.
   Result: those parameters directly determine the estimand and formal result,
   so an executable default would be a local scientific selection.
4. Rechecked mechanical intake authority. Result: it proves exact-text
   transport only and expressly supplies no semantic interpretation.

recovery_attempts=4
recovery_exhausted=true

## Exact resume condition

External Pro must append one focused answer that supplies the six exact field
groups in the table, or explicitly labels a field implementation-only and
explains why it cannot change the estimand. The answer must preserve the frozen
G1 content above, carry the existing battery unchanged, and must not alter or
rescue G0. Controller may then archive that exact raw and redispatch Project
Manager; Controller must not fill or paraphrase the missing values.

No production code, implementation plan, design contract, formal run, monitor,
or conclusion-bearing artifact is admissible before that boundary.

iterations_remaining=4
