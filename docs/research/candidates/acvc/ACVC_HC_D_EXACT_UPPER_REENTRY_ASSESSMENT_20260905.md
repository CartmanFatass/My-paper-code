# ACVC HC-D re-entry — bounded exact-upper feasibility assessment

Recorded: 2026-09-05T09:23:00Z. Evidence class: A/RECON engineering assessment.
This document selects a finite implementation and cost assessment; it is not a frozen scientific
result card and does not authorize an ACVC value calculation or a learner.

Final boundary, 2026-09-05: the one full synthetic cost reached its time cap with reproduced
12,221-12,252-bit normalized denominators. The prescribed normalized 512-bit input cost remains
unmeasured. See `ACVC_HC_D_EXACT_UPPER_REENTRY_INTAKE_20260905.md`; no actual ACVC calculation
or second full cost was launched in this assignment.

## Authority and reviewed evidence

The owner's September 5 reply to `20260904-acvc-009` chose `continue-low-priority`.
Root applied that reply in
`docs/research/portfolio/decisions/2026-09-05-apply-owner-console-reviews.md` at
`d5a6a2568b2d5424d1b0d694cb1cf704b859056d`: ACVC is ACTIVE/MEDIUM, second-recast lowest
sequencing. The reply does not replace the valid HC-D rule or admit a learner. The owner review
is at `docs/research/portfolio/owner/reviews/2026-09-05.md`, line 19. `item.py reviews --json`
returned no unapplied instruction at this boundary because Root already applied the reply.

I read the current Portfolio row, DIRECTION, the complete archived Convergence02 response, its
decision intake, R02 science card, R02 scientific intake and result evidence, and the accepted
R02 result's exact coefficient/dual fields. The surviving authority is `PRO_FINAL /
RECAST_CERTIFIED_BOUND`, specifically its HC-D exact re-entry clause:

> a prospectively resource-admitted tighter exact upper certificate below `1/4`.

The alternative is a prospectively resource-admitted stronger legal same-information lower
witness clearing `1/4`, inside both unchanged harm limits, with a visible action witness and
positive forced-DET-CF native advantage. Neither condition is claimed to have been satisfied here.

## What the current evidence does and does not establish

R02 remains the one valid `HC-D / CERTIFICATE_INTERVAL_UNRESOLVED` observation:

- `J_D = 2088/625`;
- `Delta_L = 124861/5625000 = 0.022197511111...`;
- `Delta_U = 1098083/3671875 = 0.299052391489...`.

The positive legal lower witness is harm-compatible and changes actions because of legal history,
but its gain is only about 8.9% of the fixed `1/4` threshold. Both prior learners lost to DET-CF.
The extra-information upper remains above the threshold; it is not a legal comparator and is not
the missing tuned same-information headroom census pair. No contrary evidence is removed.

The stronger-lower route currently lacks a concrete fixed policy with a reason to expect a more
than elevenfold increase over the accepted lower gain while retaining both harm constraints and
cheap exact evaluation. Merely increasing the number of posterior updates is a policy-family
extension, not evidence that this requirement can be met. I do not select it for implementation.

The tighter-upper route has one concrete finite proposal. The accepted upper gives away the
episode regime before the first action. A different certificate-only relaxation can withhold that
regime during four early opportunities while still giving at least as much information as every
legal receiver policy. Its exact value can be bounded by a forward sum, without optimizing a
full horizon-12 policy tree.

## Candidate upper: four-opportunity information prefix

This proposal preserves the twelve-opportunity host, its prior, frame/outcome law, three actions,
native reward, DET-CF, `1/4`, harm envelope, exact rational arithmetic and tie order.

For certificate purposes only, the relaxed receiver at opportunities 1–4 observes the complete
sequence of all earlier `(current frame, current truth)` atoms, even when a legal receiver's
earlier action would have been VETO. It observes the current frame but not the current truth.
It is not told the regime. From opportunity 5 onward the analytic relaxation additionally knows
the regime. This is extra information in a bound, never a deployable policy, treatment, or
reinterpretation of truth-after-VETO for a legal policy.

Each opportunity has 24 complete observed atoms `(b,q,d,y)`. Let `f_r(e)` be the exact
conditional probability of atom `e` given regime `r`, reconstructed from the unchanged R01 law.
For a length-`n` complete history `h`, define the unnormalised regime masses

`m_r(h) = (1/2) product_{e in h} f_r(e)`.

Let the unchanged native reward and two harm-numerator coefficients be `g_a(p)`, `u_a(p)` and
`l_a(p)`. Retain the already accepted R02 nonnegative dual multipliers, with no search or tuning:

`lambda_u = 38/235`, `lambda_l = 0`.

The per-opportunity harm numerator limits are unchanged:
`b_u = (U_D + 1/50) P(Y=1)` and `b_l = (L_D + 1/20) P(Y=0)`.
Write `s_{r,c,a} = g_a(p_{r,c}) - lambda_u u_a(p_{r,c}) - lambda_l l_a(p_{r,c})`.
The candidate bound is

```text
B4 = 12 (lambda_u b_u + lambda_l b_l)
   + sum_{n=0..3} sum_{h: |h|=n} sum_c
         max_a sum_r m_r(h) P(c | r) s_{r,c,a}
   + 8 sum_{r,c} (1/2) P(c | r) max_a s_{r,c,a}.
```

The prospective tightened upper would be `min(J_U_R02, B4)`. No value of B4, revised interval,
or threshold comparison has been calculated for this assessment.

### Why the proposal can be an upper certificate

For every policy inside the original aggregate harm envelope, its native return is at most its
penalized return plus `12 (lambda_u b_u + lambda_l b_l)` because both multipliers are
nonnegative. Every legal receiver policy can be simulated in the relaxed information set by
ignoring extra revealed past outcomes and the later regime. Conditional on the episode regime,
future frame/outcome draws are independent of actions. Under the relaxed full-outcome reveal,
today's action therefore changes neither later observations nor later feasible decisions. The
maximum expected penalized sum separates into the exact pointwise action maxima above.

This argument requires CM to check the complete information-containment and aggregate-harm
algebra, including the prior factor, the absence of current-truth leakage, and the factor of 12.
An exact nonnegative Lagrange upper bound does not need to be the optimum of a new constrained
primal program. R02's equal primal/dual objectives remain historical evidence for its own bound;
we do not claim that B4 is a new constrained optimum. This new certificate construction is
explicitly separate from the completed R02 calculation.

## Bounded CM assignment

CM owns only one independently reviewable derivation and generic synthetic implementation/cost
assessment of the formula above. No actual host table, accepted R02 scientific JSON, ACVC primary
value, materiality comparison or HC branch may enter the executable cost command. The existing
R02 source is historical read-only evidence at `3831a66da19788f549e39faeb8a898221186252a`; it
is absent from this main-based worktree and must not be copied wholesale or made a new dependency.

Use a plain finite forward enumeration with these prospective structural maxima:

- prefix history counts `1, 24, 576, 13824`, total `14425`;
- 12 current contexts and 3 actions per prefix history, `519300` action scores;
- 2 regime-weighted terms per score;
- 24 regime/current-context tail cells and 3 actions, 72 tail scores;
- at most `24 + 576 + 13824 = 14424` history expansions, each updating two masses;
- depth fixed at three completed past atoms; no posterior grid, policy DP, alpha envelope,
  approximation, tolerance pruning, prefix sweep or adaptive increase.

The single synthetic command must traverse that full structural envelope with deterministic
512-bit rational input numerators/denominators. It must use the actual proposed generic arithmetic
path, include exact aggregation and normalisation work, discard synthetic objective/action values,
and report only wall time, peak RSS and the static counts. Synthetic probabilities, rewards,
penalties and budgets must be independent of ACVC's host and threshold. No output of this command
is an ACVC scientific result. A single small synthetic end-to-end smoke may exercise publication;
do not run the full envelope locally or repeatedly benchmark it.

Cost admission for any later result preserves the existing multipliers and caps:
`3 * measured cost wall <= 120 seconds`, `2 * measured peak RSS <= 1.5 GiB`.
The assessment command stops at 40 seconds of measured calculation time or 0.75 GiB measured peak
RSS, making a failed projection explicit without extending the scientific cap. Check at finite
history blocks. Missing ordinary resource telemetry is `resources_unmeasured`; it cannot support
a prospective resource projection, and is not evidence about history headroom.

Before the one full cost invocation, commit and push exact source. Use the configured remote
node, an exact-SHA detached worktree, one CPU process/thread, and the existing `agent-task`.
Join the actual-node fresh `admit-memory` command and cost runner with `&&`; both physical and
effective available memory must pass 4 GiB. Portable exact-integer/rational CPU semantics are
declared for the configured Linux and Windows hosts; the assigned route is remote-first. No
accepted process is duplicated or migrated. CM hands any accepted handle to this DM and the
shared `/root/tracker_tl_experiments`; the tracker directly observes the same handle.

Owned implementation paths:

- `experiments/candidates/acvc/history_upper_prefix_assessment_r03/`;
- `scripts/run_acvc_history_upper_prefix_cost_r03.py`;
- `tests/experiments/candidates/acvc/history_upper_prefix_assessment_r03/`;
- `temp/directions/acvc/exp/history_upper_prefix_assessment_r03_20260905/`;
- `docs/research/candidates/acvc/ACVC_HC_D_UPPER_PREFIX_CM_ASSESSMENT_20260905.md`.

There are zero learner parameters, parameter displacement, optimizer updates, training episodes,
checkpoints and selection exposure; initialization ratio is not applicable. There is no seed or
sweep. The future scientific bound must retain the finite-host A/RECON ceiling assigned by the
existing Pro node; this assessment itself establishes engineering feasibility only.

Engineering-scope section 4 additions: **none**. Use no new registry, validator, manifest, retry,
worker, scheduler, provenance guard, incident tree, telemetry beyond wall/RSS, compatibility layer
or core change. Under 2,000 non-test research lines, under 600 runner lines, orchestration under
30% of the diff, no padding. Stop and return a concrete breach or missing fact if the smallest
implementation cannot comply. CM may use the normal bounded native engineering method, but no
extra independent numerical exploration is assigned.

Technical success means a justified dominating bound formula, a conforming generic arithmetic
path and a passing prospective cost projection. It does not establish that the upper is below
`1/4`, satisfy the exact re-entry condition, change HC-D, admit a learner, change a family or
alter Portfolio lifecycle. On success, return to this DM for a separate result card before any
ACVC coefficient/value calculation. On failure, return the exact missing fact; no local
direction-level override is permitted.

## Decisions this assessment produces

Options:

- **(a)** commission only the fixed four-opportunity upper derivation and full-envelope synthetic
  cost assessment above;
- **(b)** commission a new lower-policy construction despite having no concrete compatible
  material-gain policy; or
- **(c)** return at the dependency now without assessing the finite upper construction.

Recommendation: **(a)**. The upper route has a closed information argument and an explicit finite
work count. It directly addresses an admitted re-entry discriminator without learner spending or
the prior full-DP expansion. Option (b) lacks a specified scientific object; (c) would discard the
one concrete reversible engineering assessment now available. These are not close alternatives.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This is object-tier
selection within the existing certified-bound family. The owner's prediction slot is not taken
(unattended). My engineering prediction is that the finite arithmetic can fit the unchanged cap;
no claim about whether B4 crosses `1/4` is made before a scientific card.

The owner's existing second-recast flag remains; this assessment is not another RECAST and makes
no lifecycle or priority decision. No Pro request is created in this bounded assignment.

## Root integration and audit handoff

Root owns the shared ledger and Portfolio; this DM edits neither. CLI-written owner item:
`docs/research/portfolio/owner/inbox/2026-09-05/20260905-acvc-001.json`.

Anchor: `acvc-hcd-reentry-assessment-20260905`.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T09:23:00Z | acvc | object | selection | (a) fixed four-opportunity exact-upper derivation and synthetic cost assessment; (b) unspecified stronger lower-policy construction; (c) return at dependency without assessment | (a) | yes | OWNER_DELEGATED | docs/research/portfolio/owner/inbox/2026-09-05/20260905-acvc-001.json | none | |

## References

- `ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_INTAKE_20260904.md`
- `ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_SCIENCE_CARD_20260904.md`
- `ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESULT_20260904.json`
- `ACVC_HISTORY_HEADROOM_CERTIFICATE_R02_RESULT_EVIDENCE_20260904.md`
- `ACVC_HEADROOM_CERTIFICATE_R02_CONVERGENCE_DECISION_INTAKE_20260904.md`
- `external/2026-09-04-acvc-headroom-engineering-dissent-convergence-02/RESPONSE.md`
