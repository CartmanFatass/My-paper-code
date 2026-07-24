# Timing–credit identifiability derivation (G20, broadened)

Date: 2026-07-24

```text
assignment=TIMING_CREDIT_IDENTIFIABILITY_G20_DERIVATION
scheduled_by=external_pro_untied_k_bootstrap_round_section_9
outcome_mapping=pre_registered_by_external_pro
inputs=frozen_G18_first_action_intervention_pair_only
implementation_referenced=ha_ctse_process/delayed_battery_roster_g18.py
gate_referenced=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
compute=zero
formal=false
iteration_consumed=false
```

This note executes the single evidence action Pro scheduled in the untied-k
bootstrap round: a zero-compute derivation deciding whether changing only the
boundary schedule alters the information available to distinguish the
constructive rotating-member allocation from the equal-immediate-service
counterfactual. The interpretation of each possible outcome was pre-registered
by Pro; this note derives which branch obtains and adds no new scientific
authority of its own.

## The frozen pair, exactly

From the registered implementation and its passed information gate. Slot keys
follow the identity ledger; `p0, p1` are persistent, `r0, r1` rotating.

- At `t=0`: demand `1.0`, actives `{p0, p1, r0, r1}`, all batteries `1.0`.
  Natural (constructive) action: `r0` effort `1.0`, all others `0`.
  Intervened (counterfactual) action: `p0` effort `1.0`, all others `0`.
- Both serve exactly `1.0` of demand `1.0`: immediate reward is equal
  (`immediate_service_equal=true`).
- The action difference `Delta_a = a_nat - a_int` is `+1.0` effort on `r0`,
  `-1.0` effort on `p0`, `0` elsewhere. Its sum over the active set is zero.
- Both arms then run the same deterministic constructive continuation. The
  continuation contributes no policy probability to either arm.
- Battery at `t=1` differs only on `{p0, r0}` (`next_persistent_battery_delta
  = 0.25`). Rotating batteries re-synchronize during the charging absence
  because the charge cap `1.0` saturates in both arms before rejoin at `t=10`.
- The realized reward traces are identical at every step except `t=9`, where
  the intervened arm's persistent batteries exhaust one effort-unit early:
  per-step utility `1.0` natural versus `0.5` intervened
  (`intervened_future_service_deficit=0.5`; episode utility `1.0` versus
  `0.9583333333 = 1 - 0.5/12`).

So the pair is: identical likelihood support everywhere except one step-0
action, identical reward everywhere except one scalar difference
`delta = 0.5` realized at `t=9`, nine steps after the decision.

## Three credit schemes at estimand level

Per Pro's scheduled comparison. In all three, the policy gradient estimator is
`sum_t sum_i grad log pi(a_it | o_it) * A_hat_it` and the schemes differ only
in how `A_hat_it` is formed.

- **S1 — fixed synchronous segmentation, shared team advantage.** One global
  boundary schedule with period `k`; every active member at `t` receives the
  same scalar `A_hat_t`, built from the shared team reward stream over the
  shared segment plus a declared bootstrap.
- **S2 — per-agent untied segmentation, same shared advantage.** Each member
  `i` has its own boundary schedule; `A_hat_it` integrates the *same shared
  team reward stream* (plus member-local bootstrap) over member `i`'s own
  realized segment. Only window placement varies by member.
- **S3 — agent-sensitive / active-set-centered redistribution advantage.**
  `A_hat_it` contains a member-resolved term built from the allocation itself
  — a counterfactual/marginal contrast or a projection of credit onto the
  anonymous active-set-centered action subspace — in addition to any shared
  common-mode term.

## Lemma 1 — segmentation does not enter the pair's likelihood

Both arms share the deterministic constructive continuation, so for any
segmentation whatsoever the log-likelihood difference between the two
trajectories is exactly

```text
log p(tau_nat) - log p(tau_int) = log pi(a_nat,0 | o_0) - log pi(a_int,0 | o_0)
```

A boundary schedule refactors the product of per-segment factors but the
product itself is invariant; no new probability term appears or disappears
when `k` becomes `k_i`. Segmentation can therefore act only through the credit
weights, never through the information carried by the likelihood.

## Lemma 2 — schedules only rescale one shared scalar contrast

Fix any member `i` and any boundary schedule sigma (global or per-agent). The
credit that scheme S1 or S2 attaches to member `i`'s step-0 action is a window
functional `W_sigma_i` of the shared scalar reward stream (with bootstrap
pass-through of post-window rewards through a learned shared value). The
estimator's expected preference between the two arms is carried by the
member-wise contrasts

```text
c_i(sigma) = W_sigma_i(r(tau_nat)) - W_sigma_i(r(tau_int))
           = w_sigma_i(9) * delta,        w_sigma_i(9) in [0, 1]
```

because `r(tau_nat) - r(tau_int)` is supported on the single step `t=9`.
`w_sigma_i(9)` is the (discount- and bootstrap-weighted) coverage of `t=9` by
member `i`'s step-0 credit window. Consequences:

1. Every reachable estimator in the S1/S2 family is a member-wise
   **nonnegative rescaling** of one and the same scalar contrast `delta`.
2. No schedule produces member-*signed* or member-*resolved* credit: the
   opposite-signed correction the pair demands (`r0` up, `p0` down) enters
   only through the score functions, which are schedule-independent
   (Lemma 1) and already condition on battery and the rotation flag.
3. The maximal element of the family — full coverage `w_i(9) = 1` for all
   members — is realized by a *fixed synchronous* schedule with an undiscounted
   window (or bootstrap) reaching `t=9`. Untying can only remove or shrink
   per-member coverage relative to it, never add a contrast fixed scheduling
   lacks.
4. `c_i = 0` for every member exactly when the step-0 credit window and its
   bootstrap exclude `t=9`; `gamma = 0` is the extreme case. This reproduces
   CE-GAMMA0-FUTURE-BLIND on the registered pair without any appeal to
   representation.

## Theorem — answer to the central proposition

**No.** Changing only the boundary schedule does not alter the information
available to distinguish the constructive rotating-member allocation from the
equal-immediate-service counterfactual. The pair's likelihood difference is
schedule-invariant (Lemma 1), and the S1-to-S2 move changes only nonnegative
member-wise scalings of a single shared scalar contrast whose maximum is
already reachable with a fixed synchronous schedule (Lemma 2). Per-agent
untying is resegmentation of the same insufficient signal.

Under Pro's pre-registered outcome mapping, this selects the exclusion branch:

```text
branch=NO_SCHEDULE_INFORMATION_CHANGE
pre_registered_consequence=k_to_k_i_alone_formally_excluded_as_impasse_solution
```

What *does* change the estimand is S3: a member-resolved term — a
counterfactual swap contrast or centered-subspace projection — makes the
credit itself carry the opposite-signed structure `(+ on r0, - on p0)` that no
window functional of a shared scalar can express. That is the exact return
term separating S3 from S1/S2, as Pro's mapping asked the derivation to name
in the affirmative case for schedules; here it is available only by changing
the credit factorization, not the clock.

## Broadened G20 question 1 — the delayed direction is centered

`Delta_a` has active-set sum zero and is supported on active members, so the
registered constructive-minus-counterfactual action difference lies exactly in
the anonymous active-set-centered subspace. It is anonymous in the required
sense: the direction is determined by observable per-member fields (rotation
announcement, battery), not by slot identity.

```text
q1_registered_delayed_direction_in_centered_subspace=true
```

## Broadened G20 question 2 — the fast aggregate is preserved

At `t=0` no member is battery-clipped (each active member can execute up to
`4.0` effort-units; requests are at most `1.0`) and both endpoint allocations
lie inside the effort support. Realized service depends on the allocation only
through its active-set sum wherever no battery or support clip binds, so a
centered action change preserves realized immediate service exactly on the
registered pair — both arms serve `1.0` of `1.0`. The fast common mode remains
representable because the centered residual adds no mean component and the
registered source's delayed-optimal allocation requires none: the constructive
controller serves current demand fully at every pre-spike step.

Scope: preservation is exact only while the centered path crosses no battery
or action-support clip. That caveat is what question 4 instantiates.

```text
q2_fast_aggregate_preserved_on_registered_source=true
q2_scope=exact_only_while_no_battery_or_support_clip_binds
```

## Broadened G20 question 3 — what shared scalar credit can orient

With full window coverage, the S1 estimator's expected update does prefer the
natural joint action: the shared contrast `delta` multiplies the summed score
difference, and the score functions are member-differentiated through their
observations. So the orientation information for the centered subspace
**exists in expectation** under shared scalar credit. What shared scalar
credit cannot do is *isolate* it: the same scalar simultaneously credits the
common-mode component and every other concurrent fluctuation, so the centered
redistribution signal competes inside one channel with the fast aggregate
signal and all exogenous variance. The closed evidence is consistent with this
split: the G18 formal failure and the G19 no-access outcome occurred on the
interference/preservation side (shared-channel actor gradients overwrote or
starved the fast mapping), not because the pair contrast was absent from the
estimator. That consistency reading is Project Manager inference offered as
explanation, marked as such; the derivational content is the
exists-but-not-isolated split itself.

```text
q3_shared_scalar_orientation=present_in_expectation_not_member_resolved_not_isolated
```

## Broadened G20 question 4 — CE-CENTER-COMMON-MODE

A counterexample class in the same rule family (linear service, `min(demand,
supply)` cap, battery-limited effort, charge cap) where centering deletes the
required delayed action:

Two persistent members only, battery `1.0` each (`8` effort-units total).
`t=0`: demand `4.0`. `t=1..4`: demand `2.0` per step (`8` units — exactly the
total battery). Serving now yields utility `1/4` per unit; serving the later
steps yields `1/2` per unit and is capacity-bound. Myopic full effort at `t=0`
(both members at `1.0`) earns `0.5` and leaves `6` units, for episode utility
sum `0.5 + 3.0 = 3.5`; spending nothing at `t=0` yields `0 + 4.0 = 4.0`. The
optimal deviation from myopic is a pure **common-mode reduction** — both
members symmetric, both spike-critical, no redistribution available — so a
residual confined to the active-set-centered subspace above an aggregate
demand-matching fast controller cannot express it.

This is a construction sketch, not a new source. It establishes that the
centering proposition is scoped: valid for sources whose delayed-optimal
allocation preserves the immediate aggregate (the registered G18 source is
one, because pre-leave rotating effort is repaid in full by the saturating
charge cap), and refutable where delayed value requires changing total current
effort. Any future centered-residual evidence contract must declare this scope
and keep the counterexample class outside its claim.

```text
q4_centering_counterexample=exists_common_mode_reduction_required_class
q4_registered_source_inside_valid_scope=true
```

## Pre-registered dispositions that now obtain

These follow Pro's reactivation conditions applied to the derived branch; none
of them is a new scientific decision.

- **P1 / untied period:** no decision-local information or credit difference
  attributable to asynchronous event ownership was identified — the schedule
  family only rescales one shared contrast. P1 remains ineligible for an
  implementation proposal on this gate. Its independent gate (a frozen
  heterogeneous-tempo source with a positive registered `I_period`
  interaction) remains open and untouched.
- **P2 / G20 centered residual:** the derivation shows the registered delayed
  direction lies in the centered subspace (Q1) and the required fast common
  mode remains representable on the registered source (Q2). P2 is now
  **eligible for an implementation proposal**, scoped by Q4.
- **P3 / slow allocation authority:** dormant; the centered residual is not
  shown inexpressive on the registered source — the opposite is derived.
- **P4 / flat recurrent reduction:** unchanged; mandatory alongside any
  P1/P3 behavioral evidence per the adopted disposition.
- **Sampled team `Z`:** untouched by this derivation.

## Next boundary

The next Project Manager action is the P2 implementation proposal: an
executable design for an active-set-centered delayed residual whose slow
credit is member-resolved (S3 class), preserving the accepted G17 fast
controller, with a bounded nonformal screen and zero iteration cost until a
formal contract is frozen. The design must declare the S3 estimator variant,
the Q4 scope limitation, and the fail-closed source controls, and may not
reopen any closed G18/G19 candidate.
