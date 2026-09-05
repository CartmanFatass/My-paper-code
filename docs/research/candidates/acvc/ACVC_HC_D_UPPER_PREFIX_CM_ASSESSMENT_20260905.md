# ACVC four-opportunity upper: CM engineering assessment

Assignment: `ACVC_HC_D_EXACT_UPPER_REENTRY_ASSESSMENT_20260905.md` at pushed
`8b6ddad4c`. This is an engineering assessment, with no ACVC value or branch calculation.

## Contract and ownership

Implement a generic exact rational forward expectation and one independent synthetic cost
invocation. Acceptance requires information containment and the aggregate-harm inequality,
the full declared arithmetic envelope, a conforming diff, and measured cost within the
prospective projection. Preserve the original twelve opportunities, legal information,
action ordering, prior, consequence law and accepted nonnegative dual multipliers. The
synthetic command uses none of their numerical probability/reward/penalty/budget values.
There is no learner, RNG seed, optimizer, checkpoint, scientific selection or exposure.
No lower policy, new constrained optimum, full DP, B4 value or threshold comparison is assigned.

Owned paths are the `history_upper_prefix_assessment_r03` candidate and mirrored test
directories, `scripts/run_acvc_history_upper_prefix_cost_r03.py`, this record, and the
ignored `temp/directions/acvc/exp/history_upper_prefix_assessment_r03_20260905/` outputs.
The isolated checkout is `C:/Projects/HMASD-worktrees/cm-acvc-upper-cost-20260905`, branch
`codex/cm-acvc-upper-cost-20260905`. Initial worktree status was clean; the saved owner
checkout is not modified. Engineering scope section 4 additions: none.

## Derivation checked against the original law

Write the expected episode harm numerators as U and L. Original aggregate rate constraints
give U <= 12 b_u and L <= 12 b_l, because action-independent per-opportunity truth
probabilities determine the denominators. For any admitted policy and nonnegative multipliers,

`E[sum g] = E[sum(g-lambda_u*u-lambda_l*l)] + lambda_u*U + lambda_l*L`

is at most its penalized expectation plus `12*(lambda_u*b_u+lambda_l*b_l)`.
The accepted pair `lambda_u=38/235, lambda_l=0` is retained without optimization for any
future science card. No constrained primal optimum or equality of certificates is claimed.

A relaxed policy can simulate every legal policy by maintaining its legal internal history,
ignoring revealed outcomes following its simulated VETO actions and ignoring the extra regime
information at opportunities 5–12. Private randomization remains possible in the relaxed
class. The first four decisions observe the current frame and every completed past atom,
but never current truth. Thus no current-truth action maximum occurs inside the formula.

Original opportunities are conditionally independent given regime, and actions change no
later latent draws. Full past-outcome reveal makes future relaxed observations independent
of the chosen action. There is no exploration advantage left to trade against present
penalized reward, so maximization separates at each history/current-frame cell. The current
truth is integrated inside each regime's conditional score before the action maximum.

`m_r(h)=(1/2)*product f_r(e)` already contains the prior and the joint probability of h
and r. Therefore the prefix cell is `max_a sum_r m_r(h)*P(c|r)*s[r,c,a]`, without another
prior factor or division by history probability. A posterior-normalized implementation may
divide by the total cell mass and multiply it back outside the maximum; nonnegative mass
makes that identity exact. Summing all histories at each of depths 0,1,2,3 counts four
opportunities once each. Once regime is revealed, the remaining eight expectations have
weights `(1/2)*P(c|r)` regardless of earlier history. Hence the tail factor is eight and
the aggregate-harm constant is twelve, not four or eight.

This establishes a dominating Lagrange bound, not that it improves the old certificate.
Any later scientific calculation would take the minimum with the accepted R02 upper and
requires a separate DM card. Nothing here changes HC-D or admits a learner.

## Prospective execution

One deterministic full synthetic envelope; no sweep. Counts: 14,425 prefix histories,
519,300 three-action scores (two regime terms each), 72 tail scores, 14,424 two-mass
expansions, and exact normalization and aggregation. Synthetic numerical inputs are
512-bit rationals independent of scientific source tables and result JSON. Objective and
action values are discarded; publication contains only cost and static counts.

Configured node: `wsl_4070`, SSH `hmasd-wsl-node`, Python
`/home/wu/.venvs/hmasd/bin/python`. One CPU process/thread with portable exact integer/Fraction
semantics. Source is committed and pushed before remote worktree preparation. The existing
`agent-task` runs the actual-node `admit-memory --out .../admission.json` and runner joined
by `&&`. Both physical and effective free memory must be at least 4 GiB. The cost calculation
checks finite blocks against 40 seconds and 0.75 GiB; stop means no later scientific launch.
The projected future bounds are `3*wall <=120s` and `2*peak_RSS <=1.5GiB`.

No scientific output is computed on either host. The small synthetic publication test runs
on committed remote bytes. Its first local attempt failed before arithmetic because the
prescribed Python lacks psutil; the scoped runner now uses Linux resource on the assigned node.
The exact arithmetic remains portable; Windows runner RSS support is not implemented. Stop after returning derivation, scope, and cost evidence
to the DM; process observation transfers to the shared tracker after acceptance.

The independent Reviewer agreed with the derivation and counts. Also, max of a regime
mixture is no larger than the mixture of regime maxima. Normalized history sums therefore
make B4 no greater than the old fixed-dual upper analytically; a later minimum must not hide
an arithmetic defect. This is an inequality check, with no scientific numeric evaluation.
