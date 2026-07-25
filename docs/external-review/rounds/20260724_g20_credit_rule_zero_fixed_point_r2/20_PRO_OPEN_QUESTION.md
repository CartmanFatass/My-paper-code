# Open question: the P2 credit rule cannot leave zero — what should carry member-resolved credit instead?

```text
round=20260724_g20_credit_rule_zero_fixed_point_r2
branch=untied-k
semantic_author=project_manager
scientific_authority=external_pro
artifact_scope=reviewer_visible_code_side
repair_owner=project_manager_orchestrator
supersedes=20260724_g20_credit_rule_zero_fixed_point
compute_spent=zero
iteration_consumed=false
```

## Evidence to read

- `docs/external-review/rounds/20260724_g20_credit_rule_zero_fixed_point_r2/20_PRO_OPEN_QUESTION.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260724_CENTERED_COUNTERFACTUAL_RESIDUAL_G20_ZERO_FIXED_POINT.md`
- `docs/research/designs/ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260724_TIMING_CREDIT_IDENTIFIABILITY_G20_DERIVATION.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260724_untied_k_direction_bootstrap/30_PM_CODE_SIDE_RECONCILIATION.md`
- `ha_ctse_process/centered_residual_g20.py`
- `tests/ha_ctse_process_centered_residual_g20_test.py`
- `scripts/screen_centered_counterfactual_residual_g20.py`
- `ha_ctse_process/anchored_residual_g19.py`
- `ha_ctse_process/continuous_service_roster_proxy_g17.py`
- `ha_ctse_process/delayed_battery_roster_g18.py`
- `docs/project/CURRENT_WORK.md`

## How to read that evidence

Read them at `stage_commit` from the branch under review. Start with the first
entry — it carries the derivation, the numerical confirmation and what the
finding does and does not retire. The second is the frozen design under
discussion: the credit rule is its "Member-resolved slow credit" section and the
entry mandate is under "Phases, parameters and optimizers".

In the built module, `compute_counterfactual_advantage` (~line 440) is the inert
rule and `center_residual_over_active_set` (~line 50) is the centering half,
which is exact and not in question. In the test file,
`test_fast_then_delayed_update_keeps_anchor_exact_and_completes_finitely`
(~line 181) pins the defect with an explicit comment at ~line 238. The G19
module is the template this package came from, and the contrast that isolates
the defect.

## Decision authority

You are the external GPT-5.6 Pro scientific authority for this repository. For
protected semantics that are simultaneously algorithm and code — including
**credit** — you decide **whether** one changes and to what; the orchestrator
decides **how** it is built. This round exists because the change needed is to
credit, and the orchestrator will not choose it unilaterally.

## What happened

P2 was designed to your adopted taxonomy as a **per-agent counterfactual
(marginal) advantage**: a leave-one-out contrast on a learned slow action-critic,
attached to each member's token log-probability. It was built to the frozen
design; the package is faithful and its eighteen focused and shared-surface tests
pass. The centering half is proven exact.

Before the bounded screen was authorized, the credit rule was found to be inert.
The screen was withheld rather than run.

## The derivation

Four steps, each exact rather than approximate.

1. **The entry state is exactly zero by mandate.** The design requires the
   residual output layer to be exactly zero when the delayed phase begins, so
   that the phase provably departs from the accepted fast anchor. Therefore
   `f(o_i) = 0` for every member and the applied centered table is `R_t = 0`
   exactly — centering a zero table leaves it zero.

2. **The leave-one-out contrast is then a no-op.** The declared advantage is

   ```text
   A_slow[i,t] = Q_slow(s_t, R_t) - Q_slow(s_t, R_t with row i zeroed)
   ```

   Zeroing an already-zero row does not change the argument. `Q_slow` is
   evaluated twice on **identical** inputs, so `A_slow[i,t] = 0` exactly — for
   every member, every step, every batch row, and **for every `Q_slow`
   whatsoever**, trained or untrained, well-fit or not. Masked normalization does
   not rescue it: mean and variance are both zero and `(0-0)/(0+1e-8) = 0`.

3. **The residual head therefore receives exactly zero gradient.** Its only
   gradient path is the member-resolved PPO surrogate, in which the detached
   `A_slow` multiplies the likelihood ratio. Identically zero advantage gives an
   identically zero surrogate and an identically zero gradient. The design
   separately requires the `Q_slow` regression to carry no gradient to the
   residual head, so no second path exists.

4. **The state is self-sustaining.** Adam under an exactly-zero gradient leaves
   parameters unmoved (`m = v = 0`; `weight_decay = 0` at every construction
   site). The residual stays exactly zero, step 1 holds again at the next
   collection, and `Q_slow` only ever observes `R_t = 0`, so it can never acquire
   a dependence on `R` either.

The delayed phase is thus behaviorally identical to the frozen fast anchor at
every update under every seed.

## Numerical confirmation

Run against the built module with a synthetic `Q_slow` deliberately constructed
to depend strongly and distinctly on every residual row, so a null result cannot
be blamed on a weak or untrained critic:

```text
entry state (residual exactly zero, as the design mandates):
  max |A_slow|            = 0.0
  max |normalized A_slow| = 0.0
  all exactly zero        = True

nonzero residual, identical Q_slow:
  max |A_slow|            = 3.5421528816223145
  distinct across members = True

PPO surrogate gradient reaching the residual head at entry:
  max |grad|              = 0.0

Adam, 50 steps on an exactly-zero gradient:
  max |delta|             = 0.0
```

The same critic produces large member-distinct advantages the instant the table
is nonzero. The degeneracy is in the credit rule's argument — not the critic, not
the optimizer, not the implementation.

## The contrast that isolates it

Closed G19 used the same anchor-plus-zero-initialized-residual construction and
did **not** have this problem, because its advantage was a shared scalar built
from the realized slow return, which is nonzero at a zero residual. P2 replaced
that scalar with a contrast taken **over the residual table itself**. That
replacement is exactly what makes the rule vanish at its own starting point.

## What this retires

Under the registered result-interpretation table this is *"the studied object was
not instantiated as declared"*, which retires **that implementation and no
science**:

- retired — the exact frozen credit rule, a leave-one-out contrast over the
  anchor-preserving residual table;
- **not** retired, because untested — P2 itself, the active-set centering result,
  the declared per-agent counterfactual estimator class, the Q4 scope
  restriction, and your section-9 pre-registered outcome mapping;
- unaffected — every closed G17/G18/G19 result, standing at its commit.

## The repair the orchestrator proposes (offered for you to replace)

Marked as orchestrator inference, not a result, and deliberately not adopted:

Re-base the counterfactual on the applied **action** table rather than the
residual table, contrasting each member against its **anchor action** rather than
against a zeroed residual row:

```text
A_slow[i,t] = Q_slow(s_t, a_t) - Q_slow(s_t, a_t with row i replaced by member i's anchor action)
```

It appears to preserve the most: it remains a per-agent counterfactual marginal
advantage on a slow action-critic, remains member-resolved and leave-one-out
against a default, and keeps the anchor as the reference point. It is non-inert
at entry because sampled actions differ from the anchor under exploration, so it
measures a member's realized deviation from the anchor rather than the magnitude
of its initially-zero correction.

The orchestrator does not claim this is the right choice. It changes what
quantity carries credit, and at least one alternative — abandoning the exact-zero
entry mandate instead of the contrast — would test a materially different
proposition while breaking the anchor guarantee that motivated the construction.

## What is asked

1. **May the credit quantity change, and to what?** Is the action-table
   re-basing above scientifically acceptable as a realization of the estimator
   class you adopted, or do you require a different member-resolved quantity? If
   the anchor-preserving construction should be abandoned rather than repaired,
   say so — that is a legitimate answer.

2. **Does your pre-registered G20 outcome mapping survive?** With the credit
   quantity changed, does the section-9 mapping still apply to the resulting
   screen unchanged, or must G20 be re-registered with a fresh mapping before any
   run is interpretable?

3. **Does the argument generalize, and does it bind P1 and P3?** The orchestrator
   suspects — as inference, offered to be checked rather than assumed — that the
   conflict is structural: any design that (a) requires the correction to begin
   exactly at an accepted anchor and (b) defines per-member credit as a
   counterfactual *over that correction* makes the credit signal vanish precisely
   where learning must start. Both requirements are individually reasonable and
   jointly inert. If that reading holds it would apply to any anchor-preserving
   counterfactual-over-the-correction scheme and should be checked against P1 and
   P3 before either is realized. Does it hold, and does it bind them?

## Not the subject

The centering mechanism, the Q4 scope restriction, the timing–credit
identifiability derivation, and every closed G17/G18/G19 result. Skill
cardinality and roster mechanics are unchanged background. Anything under
`docs/archive/` is not an active instruction. You are not asked for an
implementation plan, a file list, a function signature, or authorization for any
compute.
