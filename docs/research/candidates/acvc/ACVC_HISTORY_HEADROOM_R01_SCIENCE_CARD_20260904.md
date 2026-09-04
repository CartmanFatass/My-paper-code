# ACVC history headroom R01 — science card

- Direction: **acvc**
- Object id: **ACVC-A-RECON-HISTORY-HEADROOM-R01**
- Evidence class: **A/RECON**, sequential follow-up
- Frozen: **2026-09-04T12:11:10Z**, before implementation or calculation
- Decision authority: **PRO_FINAL / RECAST_HEADROOM_FIRST**
- Decision intake:
  [ACVC_B2C_CONVERGENCE_DECISION_INTAKE_20260904.md](ACVC_B2C_CONVERGENCE_DECISION_INTAKE_20260904.md)
- Verbatim Pro archive:
  [external/2026-09-04-acvc-b2c-convergence-01/RESPONSE.md](external/2026-09-04-acvc-b2c-convergence-01/RESPONSE.md)

## 1. Question and finite claim ceiling

On the unchanged twelve-opportunity R01 host, does the optimal finite-horizon policy using only the
receiver's frozen online information obtain at least 0.25 more exact expected native return per
episode than unchanged DET-CF, while remaining inside the existing R01 harm-compatibility envelope
and changing a legal action on positive-probability reachable histories?

The maximum positive claim is that this finite host contains materially actionable
history-conditioned native-return headroom for a competent receiver-online policy. The maximum
negative claim closes or bounds only the uncertain/delayed R01 host family at the registered
thresholds. No branch establishes that a prior learner can approximate the policy, identifies an
optimizer or representation defect, or supports general history value, stable multi-seed value,
variable N, variable k, UAV or simulator transfer, sender compromise, cryptographic security,
safety certification, flight, deployment, or general MARL value. Portfolio lifecycle, priority,
capacity, registration, ownership, fusion, and investment remain outside this object.

This is a finite policy-opportunity measurement, not a learner-effect experiment. It has no C-style
consumption state, held-out transfer split, oracle-retuning programme, checkpoint contract, or
confirmatory seed burden.

## 2. Unchanged host, roles, information, and consequences

One receiver owns twelve serial service opportunities. One authenticated, exactly bound frame is
available at each opportunity. The episode sender regime R is fixed:

- CALIBRATED with probability 1/2;
- UNINFORMATIVE with probability 1/2.

For each opportunity independently, issuance unsafe truth x is Bernoulli 3/25, displayed confidence
q is uniform on {7/10, 9/10}, and integer age a is uniform on {0, 1, 2}. Under CALIBRATED, verdict
bit b matches x with probability q. Under UNINFORMATIVE, b matches x with probability 1/2. After
issuance, current unsafe truth y obeys

    P(y=1 | x,a) = 1/2 + (x - 1/2) (4/5)^a.

The receiver observes only the current b, q, a, opportunity index, all earlier observed frame
fields, its own earlier actions, and truth revealed by an earlier EXECUTE or PROBE. It never
observes R, x, y before a revealing action, future outcomes, another policy's path, or truth after
VETO.

The legal compound actions and immediate rewards are unchanged:

| action | current safe y=0 | current unsafe y=1 | observation |
| --- | ---: | ---: | --- |
| EXECUTE | +1 | -4 | reveals y |
| PROBE | +2/5 | -3/5 | reveals y, then executes iff safe |
| VETO | 0 | 0 | does not reveal y |

The episode ends after opportunity twelve. Gamma is 1 and native return is the undiscounted reward
sum. Actions do not alter later latent draws.

Trace:

| link | frozen meaning |
| --- | --- |
| environment event | An episode-fixed sender regime generates a confidence-labelled issuance verdict; current unsafe state may change during age delay. |
| entity and role ownership | One receiver owns all twelve actions; the sender only emits the authenticated, exactly bound frame. |
| available information | Current frame, confidence, age, opportunity index, prior frames, own actions, and truth revealed by prior EXECUTE/PROBE; no truth after VETO. |
| action and credit path | A legal action produces its frozen reward and possibly truth; undiscounted episode return is the credit quantity. |
| learner exposure | None: no parameters, gradients, optimizer, training episodes, checkpoints, or model selection. |
| native consequence | Episode return, unsafe direct execution, probe expenditure, vetoed safe service, and clean-opportunity loss. |

There is no population change, entity/slot ambiguity, join/leave/rejoin, replacement,
semi-Markov discounting, censoring, optimizer exposure, or partner co-adaptation.

## 3. Treatment: HIST-BAYES-DP

The treatment is the exact finite-horizon policy over the receiver belief

    pi = P(R = CALIBRATED | receiver-visible history),

with initial belief

    pi_0 = 1/2.

For regime r in {C,U}, define

    P(b | x,q,C) = q       when b=x, and 1-q otherwise,
    P(b | x,q,U) = 1/2,

    L_r(b,y | q,a)
      = sum_x P(x) P(b | x,q,r) P(y | x,a),

    M_r(b | q)
      = sum_y L_r(b,y | q,a).

M_r is independent of age after summing over y. On the current frame, update to

    pi_b
      = pi M_C(b|q)
        / [pi M_C(b|q) + (1-pi) M_U(b|q)].

The receiver-computable current-truth probability is

    P(y | pi,b,q,a)
      = [pi L_C(b,y|q,a) + (1-pi) L_U(b,y|q,a)]
        / [pi M_C(b|q) + (1-pi) M_U(b|q)].

When EXECUTE or PROBE reveals y, update to

    pi_{b,y}
      = pi L_C(b,y|q,a)
        / [pi L_C(b,y|q,a) + (1-pi) L_U(b,y|q,a)].

After VETO retain pi_b; no current or counterfactual truth is inserted.

For n opportunities remaining:

    V_0(pi) = 0,

    Q_E
      = sum_y P(y | pi,b,q,a)
        [u_E(y) + V_{n-1}(pi_{b,y})],

    Q_P
      = sum_y P(y | pi,b,q,a)
        [u_P(y) + V_{n-1}(pi_{b,y})],

    Q_V = V_{n-1}(pi_b),

    V_n(pi)
      = E_{q,a,b | pi} [max(Q_E,Q_P,Q_V)].

The expectation uses only the frozen uniform q and a laws and the receiver-computable mixture
probability of b. Choose the largest Q with the unchanged exact tie order EXECUTE, then PROBE, then
VETO.

Every probability, belief, reward, Q value, and aggregate must be calculated as an exact rational
number. The result emits numerator and denominator plus a decimal rendering. There is no posterior
grid, floating tolerance, approximate pruning, simulation, sampled trajectory, or result-dependent
state merge. Rational equality determines the tie order.

The implementation may memoize identical exact (n,pi) states and use algebraically equivalent
finite-support evaluation. It must produce the same complete reachable-state recursion and may not
alter scientific meaning for speed.

## 4. Strongest competent comparator: unchanged DET-CF

DET-CF remains byte-semantically identical to the R01 comparator. It knows the frozen population
law, marginalizes the two regimes at prior weight 1/2, uses only current verdict, confidence, and
age, and discards earlier history by policy definition.

For issuance accuracy

    a_q = (q + 1/2) / 2,

it computes the exact issuance posterior from prior p0=3/25 and b:

    P(x=1 | b=1,q)
      = p0 a_q / [p0 a_q + (1-p0)(1-a_q)],

    P(x=1 | b=0,q)
      = p0 (1-a_q) / [p0(1-a_q) + (1-p0)a_q].

It advances that posterior through age:

    p_current = 1/2 + (p_issue - 1/2) (4/5)^a,

then chooses the maximum exact immediate expected reward:

    EXECUTE: 1 - 5 p_current,
    PROBE:   2/5 - p_current,
    VETO:    0,

with tie order EXECUTE, PROBE, VETO.

AUTH-PROBE and ALWAYS-EXECUTE, ALWAYS-PROBE, and ALWAYS-VETO may be reproduced as reporting-only
integrity references. They cannot select or alter a branch.

## 5. Exact observables and estimand

Primary quantities are

    J_H = V_12(1/2),
    J_D = E[J_DET-CF],
    Delta_H = J_H - J_D.

Both policies are evaluated exactly under the same frozen population law. The result also reports:

1. treatment opportunity-disagreement mass

       D_action = (1/12) sum_t P(A_H != A_D at opportunity t)

   and the expected disagreement count per episode, both over treatment-reachable histories;
2. when it exists, the lexicographically first pair of positive-mass receiver-visible histories
   with identical current (t,b,q,a) but different treatment actions; each history includes only
   earlier frame fields, own actions, and legally revealed truths;
3. exact action rates and regime-stratified returns, with true regime used only after policy
   evaluation for reporting;
4. unsafe-execution rate, defined as expected unsafe EXECUTE count divided by expected unsafe
   opportunity count;
5. clean-opportunity loss, defined as expected sum of 1 minus opportunity reward over safe
   opportunities divided by expected safe opportunity count;
6. probability-mass normalization receipts and exact Bellman-state counts by horizon;
7. on disagreement states, the probability-weighted exact advantage

       Q_H(state, A_H) - Q_H(state, A_D),

   where both actions use the treatment's legal belief and the frozen continuation recursion; and
8. exact launch argv, launch SHA, elapsed wall time, peak RSS when measured, resource-measurement
   status, and fresh memory-admission receipt. Missing peak-RSS telemetry leaves an otherwise valid
   calculation marked resources_unmeasured; it does not create scientific polarity.

A regime-prediction score, posterior-calibration statistic, or belief separation without a legal
action or native-return difference is not positive evidence.

## 6. Ordered result rule

Apply this rule only after the single complete, information-conforming calculation and in the
following order.

### HR-X / NO_OBSERVATION — integrity branch

Any of the following produces no scientific branch:

- illegal access to regime or unrevealed truth;
- truth inserted after VETO;
- incomplete reachable-state recursion;
- missing probability mass, action-disagreement, harm, return, or native-consequence fields;
- nonfinite or inexact primary values;
- HIST-BAYES-DP scoring below DET-CF, because the treatment policy class can reproduce DET-CF;
- wall time above 120 seconds or peak RSS above 1.5 GiB; or
- failed fresh result-bearing memory admission.

Mapping: quarantine the attempt and allow only outcome-blind A/RECON repair at a new SHA. Admit no
learner and assign no scientific polarity.

### HR-A / MATERIAL_COMPATIBLE_HEADROOM

Conditions:

- Delta_H is at least 1/4;
- D_action is positive;
- treatment unsafe-execution rate is no more than 1/50 above DET-CF; and
- treatment clean-opportunity loss is no more than 1/20 above DET-CF.

Mapping: native history-conditioned headroom is established on this host. Admit, but do not
automatically launch, one new B/EXPLORE learner-competence object on the unchanged host. That object
must use HIST-BAYES-DP as its competence reference and distinguish approximation failure from
absence of opportunity. Do not revive or rerun R01.

### HR-B / MATERIAL_HEADROOM_ONLY_WITH_HARM_TRADEOFF

Conditions:

- Delta_H is at least 1/4;
- D_action is positive; and
- at least one R01 harm-compatibility limit fails.

Mapping: unconstrained native-return headroom exists, but not inside R01's admitted consequence
envelope. Do not launch a competence ladder. Park the algorithm line pending a prospectively
specified objective or consequence envelope that independently accepts the tradeoff; do not tune
the harm thresholds to the result.

### HR-C / SUBMATERIAL_HEADROOM

Conditions:

- Delta_H is at least 1/10 but below 1/4; and
- D_action is positive.

Mapping: history changes action and return, but not at the existing material scale. Close the R01
host family as a learner-investment target and park ACVC. Re-entry requires a new, independently
motivated host for which a competent same-information history policy is prospectively expected to
clear 1/4 against the strongest competent fixed rule.

### HR-D / NO_ACTIONABLE_HEADROOM

Conditions:

- Delta_H is at least zero but below 1/10; or
- D_action is zero.

Mapping: close the uncertain/delayed R01 host family and park ACVC at the direction-local
scientific boundary. Retain exact binding only as a primitive/control. Re-entry requires a
prospectively specified host where a competent receiver-online history policy both changes a legal
action and has at least 1/4 native-return headroom over the strongest competent fixed null.

No threshold or mapping may be rewritten after calculation. This A/RECON object has no consumption
state. Its result may change direction state only through the frozen mappings above; any Portfolio
consequence returns to Root.

## 7. Predictions on record

- **DM:** HR-A / MATERIAL_COMPATIBLE_HEADROOM. Twelve receiver-owned opportunities should provide
  enough revealed outcomes to separate calibrated from uninformative streams, and the exact
  dynamic policy should improve on a prior-marginal current-frame rule without needing more unsafe
  execution or clean loss than the frozen envelope permits.
- **Owner:** not taken (unattended).

## 8. Budget, stop rule, resource admission, and cost

- Seeds: none; the primary result is exact finite-support evaluation.
- Budget: every state reachable over all twelve opportunities from pi_0=1/2, integrating every
  frozen confidence, age, verdict, action-reveal, and truth branch.
- Invocations: exactly one deterministic result-bearing invocation.
- Runtime: one CPU process and one computational thread.
- Cap: 120 seconds wall time and 1.5 GiB peak RSS for the invocation.
- Admission: immediately before the result invocation, run the repository memory preflight and
  require both physical and effective available memory to be at least 4 GiB. Recheck for any new
  result invocation. No scientific output root is created before admission passes.
- Stop success only after both policies, every reachable Bellman state, exact normalization,
  primary values, disagreement mass and either the required witness or an exact no-witness
  certificate, harm and native-consequence metrics, resource status, launch SHA, and argv are
  emitted in one summary.
- Stop as HR-X on any integrity condition or cap. There is no resume, retry, checkpoint recovery,
  outcome-dependent extension, approximate grid, or result-informed rerun.

There is no sweep, so no per-arm sweep cost law is required. Any horizon, prior, confidence, age,
reward, posterior-grid, tolerance, or policy-family sweep is a new object and must prospectively
project each arm from its own runner cost law with the cap applied separately.

Learner exposure is N/A. Adding a learner creates a distinct B/EXPLORE object and must prospectively
record parameter count, initial L2/RMS, displacement L2/RMS and ratio, gradient-bearing updates,
transitions, episodes, updates, and model-selection exposure.

## 9. Protected semantics and CM objective

CM must implement the smallest isolated research path that exactly preserves:

- the twelve-opportunity host, rational population law, information boundary, action/reward order,
  and no-truth-after-VETO rule;
- the exact Bayes likelihoods, belief updates, finite-horizon recursion, tie order, and no
  approximation requirement;
- unchanged DET-CF, the exact estimand and normalization, the disagreement and witness semantics,
  harm metrics, ordered branch rule, and branch mappings;
- one deterministic invocation, no RNG, no learner, no selection, and no hidden oracle field;
- fresh 4 GiB admission, one-process/one-thread execution, 120-second wall cap, 1.5-GiB RSS cap,
  launch SHA/argv/resource receipts, the repository resources_unmeasured rule, and one complete
  summary; and
- no writes outside the named research, test, scratch, and evidence paths.

Expected owned paths are:

- experiments/candidates/acvc/history_headroom_r01/;
- scripts/run_acvc_history_headroom_r01.py, one runner below 600 lines;
- tests/experiments/candidates/acvc/history_headroom_r01/;
- temp/directions/acvc/exp/history_headroom_r01_20260904/; and
- this object's result evidence and intake after DM interpretation.

Technical success means only that the declared exact calculation and publication path ran and all
required measurements are complete. It cannot establish history value, select a scientific branch,
admit a learner, or decide Portfolio state. B1 and uncertain/delayed R01 code, cards, and results
are read-only.

## 10. Engineering-scope contract

**This object needs none of the default-prohibited machinery in
docs/project/ENGINEERING_SCOPE_SPEC.md section 4.**

It adds no multi-process or distributed execution, queue/scheduler, checkpoint/resume/retry,
lease/heartbeat, tamper evidence, provenance/currentness guard, incident tree, schema framework,
registry, compatibility shim, telemetry beyond wall time and peak RSS, or repeated smoke loop.
Research code stays below 2,000 new non-test lines, the runner below 600 lines, orchestration below
30 percent of the diff, and tests are one under-60-second end-to-end reduced-horizon smoke plus
exact-likelihood, information-boundary, recursion, comparator, metric, and result-rule tests. Any
section 5 budget breach is returned and recorded; it is not accepted as the price of a result.

## 11. Non-goals

Do not rerun or change B1 or R01, add a learner, tune the optimizer, alter the host or consequence
envelope, substitute a sampled estimate, introduce an approximate posterior grid, search a
tolerance, expose the hidden regime or unrevealed truth, infer truth after VETO, weaken DET-CF,
change the action tie order, add a parameter or policy sweep, introduce C-time obligations, modify
core MARL code, or infer a Portfolio decision.
