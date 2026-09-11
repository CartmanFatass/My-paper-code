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
information at opportunities 5-12. Private randomization remains possible in the relaxed
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
expansions, and exact normalization and aggregation. The generator starts with independent 512-bit raw rational operands, independent of scientific
source tables and result JSON. Its normalization enlarges the actual input bit widths; this
material discrepancy is measured and dispositioned below. Objective and
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

## Recorded implementation and independent review

Source commit: `782f696588c075d7aa22f3608ebf98bf4d1490f4`, pushed before remote preparation.
The semantic Implementer wrote the generic arithmetic and the independent Reviewer checked
its complete diff. CM inspected the final source and accepted the algebra, not the cost
feasibility. Source lines: arithmetic 79, runner 44, tests 78; 123 non-test lines. No section 4
addition. The reviewer's conservative nonblank orchestration accounting is:

- arithmetic lines 1-3,16,21,33,52,54,67,78: 10;
- runner lines 1-6,8-11,14-21,23-25,27-29,32-40,43-44: 35;
- test imports lines 1-6,8-10,58: 10.

Thus 55/201 = 27.36% of the code-plus-test diff, excluding this document. Source-only is
45/123 = 36.59%, disclosed separately. The literal specification denominator is the diff;
substantive tests exercise independent hand algebra, prior/horizon factors, normalization,
resource callback behavior and publication, with no padding.

Four rule tests passed on final committed remote source (0.04 s). The publication test first
encountered a missing pytest base-directory parent before arithmetic, then passed alone (0.03 s)
after creating that parent. The earlier Windows psutil failure was also before arithmetic.
No full-envelope local execution or second full cost occurred. Remote pytest emitted an existing
unknown cache_dir configuration warning. The five checks establish generic arithmetic and toy
publication behavior, not ACVC input construction or scientific conformance.

## Unique cost invocation and evidence

Task: `acvc_upper_prefix_cost_782f6965_01`, accepted once on `wsl_4070`.
Cwd: `/home/wu/hmasd-worktrees/acvc-upper-prefix-cost-782f6965`, detached at the source SHA.
The exact accepted supervisor command was:

```sh
/usr/local/bin/agent-task run acvc_upper_prefix_cost_782f6965_01 "cd /home/wu/hmasd-worktrees/acvc-upper-prefix-cost-782f6965 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/acvc/exp/history_upper_prefix_assessment_r03_20260905/attempt01/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_acvc_history_upper_prefix_cost_r03.py --out temp/directions/acvc/exp/history_upper_prefix_assessment_r03_20260905/attempt01"
```

Fresh memory admission at `2026-09-05T09:33:56.392392Z` passed: physical and effective available
memory each 12,382,183,424 bytes, above 4 GiB. Tracker `/root/tracker_tl_experiments` adopted
this exact handle and directly reported its terminal state to CM and DM: FAILED, exit 2,
PID 1651933, tmux inactive. The program deliberately published `cost_cap_reached` at the
finite history boundary. Calculation wall: **40.232610791994375 seconds**. Peak RSS:
**18,841,600 bytes**. Threefold wall is 120.697832375983125 seconds; twofold peak is
37,683,200 bytes. Time projection failed; memory projection passed. Finite-block checks
permit the observed 0.2326 s overshoot before return. Static counts in the summary describe
the required full envelope; they are not completed-operation counts after this early stop.

Authoritative remote outputs are below the cwd at
`temp/directions/acvc/exp/history_upper_prefix_assessment_r03_20260905/attempt01/`:
`admission.json` and `summary.json`. Supervisor log:
`/home/wu/.agent-tasks/acvc_upper_prefix_cost_782f6965_01/task.log`.
CM copied these three files into the corresponding ignored local attempt root. They retain
all published data; no synthetic objective or selected actions are emitted.

Remote preparation first used a non-login shell and stalled during Git fetch; CM terminated
that owned fetch/helper and used the configured `zsh -lic`, after which fetch and exact checkout
succeeded. Remote Git also reported an existing automatic-repack missing-parent warning;
checkout and the focused tests succeeded. No shared Git maintenance or scientific process
was repaired, reset, deleted or duplicated.

## Material input-envelope finding and final boundary

DM raised the normalized-input-size concern immediately after unique process acceptance.
The accepted process was preserved to its existing cap. On DM's explicit instruction CM ran
one short input-only reproduction on the same source SHA: call `synthetic_inputs()` and print
minimum/maximum numerator and denominator bit lengths of atoms and context marginals. It
never called `prefix_bound` or loaded ACVC coefficients.

| Inputs passed to generic arithmetic | Numerator bits | Denominator bits |
| --- | ---: | ---: |
| Normalized atoms | 12,215-12,248 | 12,221-12,252 |
| Context marginals | 12,215-12,248 | 12,219-12,251 |

Source `arithmetic.py` lines 19-20 adds 24 independently denominated raw fractions before
normalization. Raw operands are 512-bit before reduction; normalized inputs demonstrably
are not the intended <=512-bit envelope. The reviewer corrected its initial description of
this as conservative stress: an enlarged input workload is not a calibrated substitute for
the prescribed envelope. This is a material assessment limitation, not evidence that the
exact prefix formula, ACVC re-entry or all implementations are infeasible.

**Engineering conclusion:** derivation and generic implementation exist and were independently
reviewed. This particular enlarged-denominator synthetic construction failed the time
projection. The intended normalized 512-bit cost feasibility remains **UNMEASURED / UNRESOLVED**;
the complete assigned feasibility assessment is therefore not accepted as successful. There
is no B4 value, threshold comparison, new HC branch, learner launch or scientific polarity.
No second cost invocation or outcome-informed repair is assigned. DM must resolve the synthetic
input representation prospectively before a separately authorized measurement; an actual ACVC
value calculation still requires its separate science card. CM stops at this recorded boundary.
