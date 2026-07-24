# Centered counterfactual residual G20 — zero fixed point in the frozen credit rule

Date: 2026-07-24

```text
assignment=ACTIVE_SET_CENTERED_RESIDUAL_P2_IMPLEMENTATION
finding=FROZEN_G20_CREDIT_RULE_IS_INERT_AT_ITS_MANDATED_ENTRY_STATE
design_referenced=docs/research/designs/ACTIVE_SET_CENTERED_COUNTERFACTUAL_RESIDUAL_G20.md
implementation_referenced=ha_ctse_process/centered_residual_g20.py
surfaced_by=hmasd-implementer
established_by=project_manager_derivation_plus_numerical_confirmation
compute=zero
formal=false
iteration_consumed=false
screen_executed=false
```

The frozen G20 package was built to spec and its focused suite passes. Before
authorizing the bounded screen, the implementation lap surfaced — and this note
establishes — that the frozen credit rule has an exact fixed point at zero. The
declared object cannot be instantiated by the frozen screen. The screen is
therefore not run.

## The derivation

Four steps, each exact rather than approximate.

1. **The entry state is exactly zero by mandate.** The design requires the
   delayed phase to begin with the residual output layer exactly zero, so that
   the delayed phase provably departs from the accepted fast anchor. Hence the
   raw per-member outputs satisfy `f(o_i) = 0` for every member, and the
   applied centered table is `R_t = 0` exactly — centering a zero table leaves
   it zero.

2. **The leave-one-out contrast is then a no-op.** The declared advantage is
   `A_slow[i,t] = Q_slow(s_t, R_t) - Q_slow(s_t, R_t with row i zeroed)`.
   Zeroing an already-zero row does not change the argument, so `Q_slow` is
   evaluated twice on *identical* inputs and `A_slow[i,t] = 0` exactly, for
   every member, every step, every batch row — **for every `Q_slow`
   whatsoever**, trained or untrained. Masked normalization does not rescue
   it: mean and variance are both zero, and `(0 - 0)/(0 + 1e-8) = 0`.

3. **The residual head therefore receives exactly zero gradient.** Its only
   gradient path is the member-resolved PPO surrogate, in which the detached
   `A_slow` multiplies the likelihood ratio. With `A_slow` identically zero the
   surrogate is identically zero and so is its gradient. The `Q_slow`
   regression is required by the same design to carry no gradient to the
   residual head, so no second path exists.

4. **The state is self-sustaining.** Adam under an exactly-zero gradient leaves
   parameters unmoved (`m = v = 0`, and `weight_decay = 0` at every
   construction site). So the residual stays exactly zero, and step 1 holds
   again at the next collection. `Q_slow` meanwhile only ever observes `R_t = 0`
   and can never acquire a dependence on `R`.

The delayed phase is thus behaviorally identical to the frozen fast anchor, at
every update, under every seed.

## Numerical confirmation

Run against the built module with a synthetic `Q_slow` deliberately constructed
to depend strongly and distinctly on every residual row, so that a null result
cannot be blamed on a weak or untrained critic:

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

The same `Q_slow` yields large, member-distinct advantages the moment the table
is nonzero. The degeneracy is located in the credit rule's argument, not in the
critic, not in the optimizer, and not in the implementation.

## What the frozen screen would have reported

Deterministically `NONFORMAL_NO_DELAYED_ACCESS_CENTERED_RESIDUAL_G20`
(branch 3), on every seed. Branch 1 does not fire: centering,
zero-residual-equivalence, replay and gradient-ownership all hold — trivially,
because the residual is zero. Branch 2 does not fire: with a zero residual the
G17 behavior is exactly the accepted fast policy. Branch 3 then fires because
G18 gain over the frozen fast anchor is exactly `0.0`, below the `0.10`
threshold.

That reading would have been an artifact. It would have looked like evidence
against member-resolved delayed credit while testing nothing about it.

## What this retires, and what it does not

Per the registered result-interpretation table this is the row *"the studied
object was not instantiated as declared"*, which retires **that implementation
and no science**.

- Retired: the exact frozen G20 credit rule — a leave-one-out contrast taken
  over the anchor-preserving residual table itself.
- **Not** retired: the P2 candidate, the active-set centering result, the
  declared per-agent counterfactual estimator class, the Q4 scope restriction,
  or Pro's pre-registered G20 outcome mapping. None of these were tested.
- Not affected: every closed G17/G18/G19 result, all of which stand at their
  commits.

The centering half of the design is unaffected and is proven exact by the
focused suite. Only the credit half is inert.

## Generalization (Project Manager inference — not a result)

Marked as local inference under the constitution, offered because it may bear
on sibling candidates and should be checked rather than assumed:

The conflict looks structural rather than incidental. Any design that (a)
requires the correction to begin exactly at an accepted anchor, and (b) defines
per-member credit as a counterfactual *over that correction*, makes the credit
signal vanish precisely where learning must start. The two requirements are
individually reasonable and jointly inert. If that reading holds, it applies to
any anchor-preserving "counterfactual-over-the-correction" scheme and would be
worth checking against P1 and P3 before either is realized.

The repair direction that appears to preserve the most — re-basing the
counterfactual on the applied *action* table against each member's anchor
action, so the contrast measures a member's realized deviation from the anchor
rather than the size of its (initially zero) correction — is likewise inference.
It keeps the declared estimator class, stays member-resolved, and is non-inert
at entry because sampled actions differ from the anchor under exploration. It
is *not* adopted here: it changes what quantity carries credit, which is
protected, and alternatives exist that would test materially different
propositions.

## Disposition and next action

The bounded screen is withheld — not deferred for capacity, but withheld
because it cannot measure its declared object. No iteration is consumed and no
compute was spent.

The credit rule is protected semantics and its repair is a scientific choice,
so the next action is a bounded external review round carrying this derivation
and the proposed repair, to converge on: whether the action-table re-basing
preserves the declared estimator class and Pro's pre-registered G20 outcome
mapping or constitutes a separately registered candidate; whether the
pre-registered mapping survives unchanged; and whether the generalization above
bears on P1 and P3.
