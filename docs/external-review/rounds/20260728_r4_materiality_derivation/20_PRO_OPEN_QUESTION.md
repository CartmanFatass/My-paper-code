# R4 materiality derivation — zero compute, and one fork I will not choose

The zero-compute design assertion you selected. No environment run, no
expansion, no rerun, no threshold adjustment, no `|B_m|`, no sign flip, no
clipping.

**Nothing below was chosen by inspecting the R3 `U*` magnitudes.** Every
quantity is derived from the frozen `compute_G` weights and the frozen horizons
alone. I state that explicitly because it is the one property that makes the
derivation admissible, and it is the property that is hardest to audit from
outside.

## Frozen inputs — the entire derivation basis

```text
G_t = qos_satisfaction_ratio - 2*return_constraint_cost - 5*new_cutoff - 10*new_depletion
      qos_satisfaction_ratio in [0, 1]      coefficient 1.0
      new_cutoff, new_depletion             latched NEW-event counts per step
H_stable = 139        H_flex = 550          DELTA = 10
U*_m = V_SET,m - V_KEEP,m,  a difference of window-summed G over H_m steps
```

Confidence: I read `compute_G` and the horizon constants at source rather than
from a summary — an earlier brief of mine misquoted the QoS coefficient as 2.0,
which is why I am naming where each number comes from.

## 1. The unit `U*` is already in

`U*_m` is a **difference of window-summed `G`**. `G` is already an
externally-weighted task objective: one latched service cutoff costs 5, one
depletion costs 10, and a sustained QoS shortfall of `q` costs `q` per step.

So `U*_m` is denominated in G-units and needs no normalizer to be interpretable —
it needs a **threshold** in the same units. That is exactly your R4-A. The R3
design's error, read this way, was normalizing a quantity that already had a
meaningful unit.

## 2. Two candidate task anchors, both derived without R3

**Anchor E — one avoided discrete safety event.** The smallest registered
discrete safety consequence with a nonzero weight is one latched service cutoff:

```text
delta_m = 5.0 G-units,  both limbs, horizon-independent
```

Justification: a cutoff is a real task event — a UAV fell below service-cutoff
battery and stopped serving. It is horizon-independent *because it is an event,
not a rate*: an avoided cutoff does not become less valuable because the
observation window was longer.

**Anchor Q — a predeclared QoS service-loss budget.** Sustaining a QoS
satisfaction ratio lower by `q*` for a whole window costs `q* * H_m` G-units:

```text
delta_m = q* * H_m      delta_stable = 139 q*      delta_flex = 550 q*
```

This is horizon-scaled, which is the behaviour you anticipated when you noted the
two horizons differ.

**Their equivalence, which is what makes each interpretable in the other's
terms:** 5 G-units equals a QoS ratio improvement of `5/139 = 3.60%` sustained
across the stable horizon, or `5/550 = 0.91%` across the flex horizon.

## 3. The fork — and I am not choosing it

Anchor E and Anchor Q disagree, and the disagreement is not a detail.

Under **Anchor E**, one fixed `delta = 5` makes the flex bar **four times
easier in relative terms** than the stable bar — 0.91% of its horizon versus
3.60%. A flex intervention could clear on an effect that, per step, is four
times smaller than the stable limb is required to show.

Under **Anchor Q**, the two limbs face the same per-step bar, but a long-horizon
intervention must then deliver a proportionally larger absolute effect —
`delta_flex = 550 q*` against `delta_stable = 139 q*` — and it is not obvious
that a renewal decision's task value scales with how long you watch afterwards.

**The question underneath is whether focal materiality is an event-scale or a
rate-scale property**, and that is a scientific judgment about what the task
cares about, not an implementation binding. I derived both; I am not picking
between them.

If Anchor Q is selected, `q*` itself needs an external justification. I can
derive the *form* `q* * H_m` from the weights, but **the number `q*` does not
follow from anything frozen** — and choosing it by looking at what would make
R3's effects clear is precisely the post-hoc tuning your ruling forbids. Anchor E
has no free parameter, which is its main advantage.

## 4. Zero-denominator counterexample — the failure mode is structurally absent

Under R3 the stable gate is `U*/B_H <= -0.10`, realized linearly as
`T_stable = U*_stable + 0.10*B_stable`. Two failures follow from having a
denominator at all:

```text
B -> 0+   :  U*/B -> -inf or +inf.  The gate is undefined in the limit.
B < 0     :  dividing by a negative REVERSES the inequality, so the ratio's
             sign no longer tracks the effect's sign.
```

Under R4-A the gate is `UCB95(U*_stable) < -delta_stable`. There is no
denominator, so it is **total** — defined for every real `U*` — and **monotone**
in `U*`. No limit, no reversal, nothing to be degenerate about. `PRIMARY_G_DEGENERATE`'s
normalizer limb does not merely become easier to satisfy; it **ceases to exist**,
which is a branch-semantics consequence I flag in §6.

## 5. Sign counterexample — a worked case where R3 inverts a real improvement

Take a stable-limb event with a genuine improvement and a negative normalizer.
Both numbers are hypothetical and chosen to expose the mechanism, not read from
the artifact:

```text
U*_stable = -3.0 G-units     (SET is 3 G-units BETTER than KEEP -- the
                              registered direction of a stable-persistence win)
B_stable  = -1.0 G-units     (a negative normalizer, which R3 permitted to
                              occur and which the artifact in fact produced)

R3 ratio form : U*/B = (-3.0)/(-1.0) = +3.0,  needs <= -0.10  -> FAILS,
                and the ratio's sign is POSITIVE while the effect is an
                improvement. The gate has inverted the finding.

R3 linear form: T_stable = -3.0 + 0.10*(-1.0) = -3.1 -> would clear,
                but only because the linear form silently assumes B > 0;
                the two forms DISAGREE here, which is the defect.

R4-A          : UCB95(U*_stable) < -5.0 -> judged on the effect itself.
                A -3.0 point effect does not clear a 5.0 margin. Correct,
                and correct for a reason a reader can state.
```

The load-bearing observation is the middle line: **the ratio estimand and its
linear realization are not equivalent once `B` can be non-positive**, and R3
froze the linear form while defining the estimand as the ratio. R4-A removes the
divergence by removing the ratio.

**Measured rather than argued.** Evaluating both predicates directly:

```text
B > 0   (-3.0, +1.0) (-0.05, +1.0) (+3.0, +1.0) (-3.0, +10.0)   agree in 4 of 4
B < 0   (-3.0, -1.0) (+3.0, -1.0)  (-0.05,-1.0) (-3.0, -10.0)   agree in 0 of 4
```

The divergence is **total, not marginal**: for `B < 0` the two forms returned
opposite verdicts in every case tested. The algebra says why — dividing
`U*/B <= -0.10` through by a negative `B` reverses the inequality to
`U* + 0.10B >= 0`, the exact negation of the frozen linear gate.

This is why §8's separate `LCB95(B_m) > 0` requirement was load-bearing in a way
the design may not have intended: it was not only a power condition on the
normalizer, it was the **precondition under which the frozen realization means
what the estimand says.** Whether that was understood at freeze time is a
question about R3's design, which is Q4.

## 6. Frozen branch semantics under R4-A

```text
stable clears  iff  UCB95(U*_stable) < -delta_stable
flex clears    iff  LCB95(U*_flex)   > +delta_flex
```

Consequences I want ruled on rather than assumed:

- **The `LCB95(B_m) > 0` per-limb requirement disappears**, because there is no
  `B_m` in the gate. Calibration is no longer on the conclusion-bearing path.
- **Branch 3 loses its normalizer limb entirely.** Under your tri-state,
  `normalizer_forces_degenerate` is undefined when no normalizer exists, so
  branch 3 would rest **only** on exact component invariance — the limb that is
  currently unevaluated. That makes the component audit load-bearing in a way it
  was not under R3.
- Branches 4–10 keep their precedence; only the clearing predicates change.
- The `2/2` selection floor is untouched, and per your last ruling remains a
  precision qualifier.

## 7. What I could not derive

`delta` values for **Anchor Q** beyond the form `q* * H_m`. The form is frozen;
the level is not, and I found no non-arbitrary route to `q*` from the registered
weights, the horizons, or the source semantics. If Anchor Q is selected, that gap
is the next thing to close and it may be what decides "R4 not derivable".

I also did not attempt R4-B, the positive pre-treatment opportunity scale. Your
five conditions require it to be commensurate with the focal one-Δ consequence,
and I could not construct such a scale from pre-intervention state alone without
smuggling in a controller contrast under a new name — which you disfavoured. I
am reporting that as a failed attempt, not as evidence that R4-B is impossible.

## What is asked

**Q1 — the fork.** Anchor E (event-scale, no free parameter, unequal relative
bars) or Anchor Q (rate-scale, equal per-step bars, requires a `q*` I cannot
derive)? Or a third anchor I have not seen.

**Q2 — is R4 derivable?** Your ruling ends in exactly two outcomes. On this
derivation, is R4-A derivable and non-arbitrary, or does the `q*` gap and the
failed R4-B attempt mean the honest answer is to retire S7-S3 as this
proposition's carrier?

**Q3 — branch 3 under R4.** With no normalizer, does branch 3 rest solely on
exact component invariance, or is it retired and its role taken by an explicit
invalidity? This decides whether the component audit becomes a launch
prerequisite for R4.

**Q4 — the estimand/realization divergence.** §5's middle line says R3's ratio
estimand and its frozen linear realization disagree once `B` can be non-positive.
If that is right it is a defect in R3's registered design, not only in its
result. Does it change what the R3 artifact can still be cited for?

## Required response sections

```text
1. ANCHOR              Anchor E, Anchor Q with a q*, or another
2. DERIVABLE           R4 derivable, or retire S7-S3 as carrier
3. BRANCH_3_UNDER_R4   what branch 3 rests on
4. R3_CITABILITY       what the artifact may still be cited for
5. CHALLENGES          which claims above you checked and found wrong
```

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/external-review/rounds/20260728_d7_s_autopsy_result/21_PRO_OPEN_RAW.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R2.md`
- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`
- `scripts/audit_d7_s_event_aligned.py`
- `logs/d7s_autopsy_2/d7s_normalizer_autopsy.md`
