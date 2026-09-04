# ACVC history headroom certificate R02 — science card

- Direction: **acvc**
- Object id: **ACVC-A-RECON-HISTORY-HEADROOM-CERTIFICATE-R02**
- Evidence class: **A/RECON**, sequential follow-up
- Result family: **HC-X/A/B/C/D**
- Frozen: **2026-09-04T13:25:18Z**, before implementation, project-cost admission, or calculation
- Launch status: **FROZEN / NOT LAUNCHED / awaiting Root REMOTE_FIRST activation**
- Decision authority: **PRO_FINAL / RECAST_CERTIFIED_BOUND**
- Decision intake:
  [ACVC_HEADROOM_CERTIFICATE_R02_CONVERGENCE_DECISION_INTAKE_20260904.md](ACVC_HEADROOM_CERTIFICATE_R02_CONVERGENCE_DECISION_INTAKE_20260904.md)
- Verbatim Pro archive:
  [external/2026-09-04-acvc-headroom-engineering-dissent-convergence-02/RESPONSE.md](external/2026-09-04-acvc-headroom-engineering-dissent-convergence-02/RESPONSE.md)

## 1. Question and finite claim ceiling

On the unchanged twelve-opportunity uncertain/delayed R01 host and inside the unchanged R01 harm
envelope:

1. can one prospectively fixed, legal, receiver-online history policy establish at least 1/4 exact
   expected native-return headroom over unchanged DET-CF; or
2. can an exact harm-constrained regime-oracle certificate prove that no legal receiver-history
   policy can reach 1/4 headroom?

This object does not seek the exact optimal receiver-history value unless equal lower and upper
certificates incidentally pin it.

The maximum positive claim is that the fixed legal lower policy establishes materially actionable,
harm-compatible history-conditioned native-return headroom on this finite host. The maximum
negative claim is that the exact upper certificate places every legal harm-compatible
receiver-history policy below the registered 1/4 threshold on this host. An open interval is
explicitly unresolved.

No branch establishes that ACVC-HISTORY-GATE, RAW-GRU, or another learner can approximate the
policy; identifies representation, optimization, objective, or credit failure; establishes full
optimal horizon-twelve value when the interval remains open; or supports stable seed performance,
sample efficiency, arbitrary history value, variable N, variable k, UAV or simulator transfer,
sender compromise, cryptographic security, safety certification, flight, deployment, or general
MARL value. Portfolio lifecycle, priority, capacity, registration, ownership, fusion, and
investment remain outside this object.

This is an exact threshold-certificate object, not a learner experiment. It has no C-style
consumption state, held-out split, confirmatory seed burden, checkpoint, model selection, or
oracle-retuning obligation.

The live explanations are fixed before calculation:

1. receiver-visible history has at least 1/4 harm-compatible native-return value, but the two R01
   learners were driven by shared objective, credit, or optimization effects into blanket probing;
2. DET-CF is within less than 1/4 of every legal receiver-history policy satisfying the unchanged
   harm envelope; or
3. material native-return history value exists only outside that consequence envelope.

HC-A supports the first explanation at the registered threshold, HC-C supports the second, HC-B
supports the third, and HC-D leaves the first two unresolved. HC-X supports none of them.

## 2. Unchanged host, roles, information, and native consequences

One receiver owns twelve serial service opportunities. One authenticated, exactly bound frame is
available at each opportunity. The episode sender regime R is fixed:

- CALIBRATED with probability 1/2;
- UNINFORMATIVE with probability 1/2.

At each opportunity independently, issuance unsafe truth x is Bernoulli 3/25, displayed confidence
q is uniform on {7/10, 9/10}, and integer age d is uniform on {0, 1, 2}. Under CALIBRATED, verdict
bit b matches x with probability q. Under UNINFORMATIVE, b matches x with probability 1/2. After
issuance, current unsafe truth y obeys

$$
P(y=1\mid x,d)=\frac12+\left(x-\frac12\right)\left(\frac45\right)^d.
$$

For regime r in {C,U}, retain the exact R01 likelihoods

$$
P(b\mid x,q,C)=
\begin{cases}
q,&b=x,\\
1-q,&b\ne x,
\end{cases}
\qquad
P(b\mid x,q,U)=\frac12,
$$

$$
L_r(b,y\mid q,d)
=\sum_xP(x)P(b\mid x,q,r)P(y\mid x,d),
$$

and

$$
M_r(b\mid q)=\sum_yL_r(b,y\mid q,d).
$$

The receiver observes only the current b, q, d, opportunity index, earlier observed frame fields,
its own earlier actions, and truth revealed by an earlier EXECUTE or PROBE. It never observes R,
x, y before a revealing action, future outcomes, another policy path, or truth after VETO.

The legal actions and immediate native rewards remain:

| action | current safe y=0 | current unsafe y=1 | observation |
| --- | ---: | ---: | --- |
| EXECUTE | +1 | -4 | reveals y |
| PROBE | +2/5 | -3/5 | reveals y, then executes iff safe |
| VETO | 0 | 0 | does not reveal y |

The episode ends after opportunity twelve. Gamma is 1 and native return is the exact undiscounted
reward sum. Actions do not alter later latent draws. Exact ties are resolved EXECUTE, then PROBE,
then VETO.

Trace:

| link | frozen meaning |
| --- | --- |
| environment event | An episode-fixed sender regime produces a confidence-labelled verdict; current unsafe truth may change during age delay. |
| entity and role ownership | One receiver owns all twelve actions; the sender only emits an authenticated, exactly bound frame. |
| legal treatment information | Current frame, opportunity index, first-opportunity receiver action, and legally revealed first truth; no hidden regime, issuance truth, unrevealed current truth, future outcome, another policy path, or truth after VETO. |
| upper-certificate information | The analytic relaxation additionally knows regime only to upper-bound the legal class; it is never an implementable arm or comparator. |
| action and credit path | EXECUTE, PROBE, or VETO produces the unchanged immediate reward and legal reveal; native episode return is the exact undiscounted sum. |
| learner exposure | None: no parameters, gradients, optimizer, training episodes, checkpoints, or selection. |
| native consequence | Return, unsafe direct execution, probe expenditure, vetoed safe service, and clean-opportunity loss. |

There is no population change, entity/slot ambiguity, join/leave/rejoin, replacement,
semi-Markov discounting, censoring, optimizer exposure, or partner co-adaptation.

## 3. Legal lower certificate: HIST-1UPDATE-CF

HIST-1UPDATE-CF is a prospectively fixed, deliberately restricted, non-optimal receiver-online
history policy.

### Opportunity 1

1. Observe the legal current context

   $$
   c_1=(b_1,q_1,d_1).
   $$

2. Take exactly the action selected by unchanged DET-CF.
3. Form one exact anchor posterior

   $$
   \pi_1=P(R=\mathrm{CALIBRATED}\mid h_1),
   $$

   where h_1 contains c_1, the receiver's action, and y_1 only when that action legally reveals
   truth.
4. If the action is EXECUTE or PROBE, update with the corresponding exact L_C and L_U likelihood.
   If it is VETO, update only with M_C and M_U; no truth is inserted.

With prior 1/2, the two exact cases are therefore

$$
\pi_1=
\frac{L_C(b_1,y_1\mid q_1,d_1)}
{L_C(b_1,y_1\mid q_1,d_1)+L_U(b_1,y_1\mid q_1,d_1)}
$$

after a revealing action, and

$$
\pi_1=
\frac{M_C(b_1\mid q_1)}
{M_C(b_1\mid q_1)+M_U(b_1\mid q_1)}
$$

after VETO.

### Opportunities 2–12

For each current context c_t=(b_t,q_t,d_t):

1. use the frozen anchor \pi_1 as the regime prior;
2. update it transiently using only the current frame,

   $$
   \widetilde\pi_t=
   \frac{\pi_1M_C(b_t\mid q_t)}
   {\pi_1M_C(b_t\mid q_t)+(1-\pi_1)M_U(b_t\mid q_t)};
   $$

3. calculate the exact current unsafe probability

   $$
   p_t=P(y_t=1\mid \pi_1,c_t)
   =
   \frac{\pi_1L_C(b_t,1\mid q_t,d_t)
   +(1-\pi_1)L_U(b_t,1\mid q_t,d_t)}
   {\pi_1M_C(b_t\mid q_t)+(1-\pi_1)M_U(b_t\mid q_t)};
   $$

4. choose the immediate exact Bayes action maximizing

   $$
   G_E(p_t)=1-5p_t,\qquad
   G_P(p_t)=\frac25-p_t,\qquad
   G_V(p_t)=0
   $$

   with the frozen tie order; and
5. discard every later posterior change after that action. The anchor \pi_1 remains fixed through
   opportunity twelve.

The one-update restriction is the prospective treatment definition. It adds no information, never
uses hidden regime, never observes unrevealed truth, and changes no action or reward semantics. The
exact calculation integrates at most 24 receiver-visible anchor histories and 48 latent
first-opportunity atoms. There is no simulation, sampled trajectory, posterior grid, tolerance, or
result-dependent policy selection.

## 4. Strongest competent same-information comparator: unchanged DET-CF

DET-CF remains byte-semantically unchanged from R01. It holds regime prior at 1/2, uses only
current verdict, confidence, and age, knows the exact population law, and discards earlier history
by policy definition.

For issuance accuracy

$$
a_q=\frac{q+1/2}{2},
$$

and prior p_0=3/25, it computes

$$
P(x=1\mid b=1,q)
=\frac{p_0a_q}{p_0a_q+(1-p_0)(1-a_q)},
$$

$$
P(x=1\mid b=0,q)
=\frac{p_0(1-a_q)}
{p_0(1-a_q)+(1-p_0)a_q}.
$$

It advances the issuance posterior through age,

$$
p_{\mathrm{current}}
=\frac12+\left(p_{\mathrm{issue}}-\frac12\right)\left(\frac45\right)^d,
$$

then maximizes the same three immediate exact rewards with the same tie order. The calculation
must derive exact J_D from the host law. The sampled R01 evaluation mean is provenance only and
cannot substitute for this exact value.

## 5. Exact upper relaxation: REGIME-ORACLE-ENVELOPE

REGIME-ORACLE-ENVELOPE is not a deployable treatment or comparator. It is an extra-information
relaxation used only to upper-bound every legal receiver-history policy inside the frozen
consequence envelope.

Let:

- r in {C,U} be the episode regime;
- c=(b,q,d) be one of twelve current visible contexts;
- A in {E,P,V};
- w_{r,c}=P(R=r,C=c);
- p_{r,c}=P(Y=1\mid R=r,C=c); and
- z_{r,c,A} be the joint per-opportunity probability mass assigned to action A.

Define exact native-reward coefficients

$$
g_E(p)=1-5p,\qquad
g_P(p)=\frac25-p,\qquad
g_V(p)=0.
$$

Define unsafe-execution numerator coefficients

$$
u_E(p)=p,\qquad u_P(p)=u_V(p)=0,
$$

and clean-loss numerator coefficients

$$
\ell_E(p)=0,\qquad
\ell_P(p)=\frac35(1-p),\qquad
\ell_V(p)=1-p.
$$

Let U_D and L_D be the exact DET-CF unsafe-execution and clean-loss rates. Let
P_U=P(Y=1) and P_S=P(Y=0). Solve exactly

$$
\max_z\sum_{r,c,A}z_{r,c,A}g_A(p_{r,c})
$$

subject to

$$
\sum_Az_{r,c,A}=w_{r,c}
\quad\text{for every }(r,c),
$$

$$
z_{r,c,A}\ge0,
$$

$$
\sum_{r,c,A}z_{r,c,A}u_A(p_{r,c})
\le\left(U_D+\frac1{50}\right)P_U,
$$

and

$$
\sum_{r,c,A}z_{r,c,A}\ell_A(p_{r,c})
\le\left(L_D+\frac1{20}\right)P_S.
$$

Let the exact optimum be j_U per opportunity and define

$$
J_U=12j_U.
$$

Conditional on R=r, current opportunities are independent of receiver history, and actions do not
alter later draws. Any legal time-dependent stochastic history policy therefore induces an average
action distribution conditional on (r,c), with expected native return and both harm numerators
represented by a feasible z when the policy satisfies the envelope. The relaxation additionally
reveals R, so it contains every legal compatible receiver-history policy. Therefore

$$
J_H^*\le J_U
$$

for the best legal compatible history policy J_H^*. The calculation must emit exact rational
primal and dual certificates with equal objectives. DET-CF must induce a feasible point, making
J_U\ge J_D an integrity check.

## 6. Exact observables and estimands

Calculate and publish exact rational values, each with numerator, denominator, and decimal
rendering, for

$$
J_D=E[J_{\mathrm{DET-CF}}],
$$

$$
J_L=E[J_{\mathrm{HIST\text{-}1UPDATE\text{-}CF}}],
$$

$$
J_U=12j_U,
$$

and

$$
\Delta_L=J_L-J_D,\qquad
\Delta_U=J_U-J_D.
$$

Also publish:

1. exact action rates and regime-stratified return for DET-CF and HIST-1UPDATE-CF;
2. exact unsafe-execution and clean-loss rates for both legal policies;
3. lower-policy action-disagreement mass against DET-CF and expected disagreement count per
   episode;
4. the lexicographically first positive-mass pair of receiver-visible first-opportunity histories
   that, with identical later current context, produces different lower-policy actions, or an
   exact no-witness certificate;
5. for every positive-mass lower-policy disagreement state, exact forced-DET-CF native Q advantage

   $$
   Q_L(s,A_L)-Q_L(s,A_D)
   $$

   under the lower policy's frozen continuation;
6. the probability-weighted aggregate of those advantages;
7. every exact probability-normalization check;
8. the complete upper-program coefficient table;
9. exact primal feasibility, dual feasibility, complementary slackness, and equal primal/dual
   objective;
10. static work counts, exact launch SHA and argv, wall time, peak-RSS status, and fresh
    memory-admission receipt.

Because the lower policy intentionally ignores outcomes after opportunity one, its continuation is
unchanged by a later current action. The forced-DET-CF Q difference is therefore an exact
native-reward comparison, not a predictive score.

## 7. Ordered result rule

Apply this rule only after one complete exact calculation and in the following order.

### HC-X / NO_OBSERVATION — integrity branch

Any of the following yields no scientific branch:

- illegal information enters HIST-1UPDATE-CF;
- truth is inserted after VETO;
- the oracle relaxation is reported as a legal treatment;
- any host probability, action, reward, comparator, threshold, or harm definition differs from
  R01;
- arithmetic is inexact, or a posterior grid, tolerance pruning, sampling, or approximate LP
  solution is used;
- any return, action, harm, witness, forced-DET-CF, normalization, or certificate field is missing;
- primal or dual infeasibility;
- unequal exact primal and dual objectives;
- J_U<J_D;
- HIST-1UPDATE-CF is harm-compatible but J_L>J_U;
- failed prospective project-cost admission;
- failed fresh memory admission;
- wall time above 120 seconds or peak RSS above 1.5 GiB.

**Mapping:** quarantine the attempt. Permit only outcome-blind repair at a new SHA. Admit no
learner, infer no HR branch, and assign no scientific polarity.

### HC-A / MATERIAL_COMPATIBLE_HEADROOM_WITNESS

All conditions must hold:

- \Delta_L\ge1/4;
- HIST-1UPDATE-CF satisfies both frozen harm limits;
- action-disagreement mass is positive;
- a positive-mass visible-history action witness exists; and
- aggregate forced-DET-CF native advantage is positive.

**Mapping:** establish material compatible history-conditioned headroom on the unchanged host.
Admit, but do not automatically launch, one new B/EXPLORE learner-competence object. That object
must use HIST-1UPDATE-CF as a competent reachable reference, retain DET-CF, and distinguish
policy-approximation failure from exposure. Do not reopen R01 or claim full-DP optimality.

### HC-C / MATERIAL_COMPATIBLE_HEADROOM_CERTIFIED_IMPOSSIBLE

Condition:

$$
\Delta_U<\frac14.
$$

This branch takes precedence over an incompatible lower-policy gain.

**Mapping:** no legal history policy satisfying the frozen consequence envelope can clear the
material threshold. Close the uncertain/delayed R01 host family as a learner-investment target and
park ACVC at the direction-local boundary. Retain exact binding only as a primitive/control.

**Re-entry:** a new independently motivated host must prospectively specify a competent
same-information history policy expected to change a legal action and clear 1/4 native-return
headroom over its strongest competent fixed null. The current threshold and envelope may not be
tuned to this result.

### HC-B / MATERIAL_NATIVE_WITNESS_OUTSIDE_ENVELOPE

All conditions must hold:

- \Delta_U\ge1/4;
- \Delta_L\ge1/4;
- positive action disagreement, visible-history witness, and forced-DET-CF advantage exist; and
- HIST-1UPDATE-CF violates at least one frozen harm limit.

**Mapping:** a legal history policy has material native-return value, but this witness is outside
the admitted consequence envelope. Admit no learner. Park pending an independently justified
prospective objective or harm envelope.

### HC-D / CERTIFICATE_INTERVAL_UNRESOLVED

Every other complete result, including

$$
\Delta_L<\frac14\le\Delta_U,
$$

or failure of the lower policy to produce a visible-history action witness while the upper
certificate does not rule out material headroom.

**Mapping:** admit no learner and park at an engineering/scientific dependency boundary.

**Exact re-entry:** supply either:

- a prospectively resource-admitted legal same-information policy whose exact compatible lower
  bound clears 1/4 with an action witness and positive forced-DET-CF advantage; or
- a prospectively resource-admitted tighter exact upper certificate below 1/4.

A predictive regime statistic, posterior-separation result, approximate policy evaluation, extra
learner budget, or cap increase does not satisfy this condition.

No threshold or mapping may be rewritten after calculation. A technical failure, failed
admission, or incomplete attempt produces HC-X only and cannot acquire scientific polarity.

## 8. Predictions on record

- **DM:** HC-D / CERTIFICATE_INTERVAL_UNRESOLVED. The one-update legal witness is likely too
  restricted to clear 1/4, while revealing the episode regime is likely to leave the compatible
  upper relaxation above 1/4. This forecast is recorded before implementation, project-cost
  admission, or any scientific calculation.
- **Owner:** not taken (unattended).

## 9. Exposure line

This object has no learner:

- trainable parameter count: **0**;
- initialization L2/RMS and initialization scale: **N/A**;
- parameter displacement L2/RMS: **0 / 0**;
- displacement-to-initialization ratio: **N/A**;
- gradient-bearing updates: **0**;
- optimizer transitions, training episodes, checkpoints, and selection exposure: **0**.

The analytic oracle is a certificate computation, not a learner or deployable policy.

## 10. Prospective project-cost admission and result budget

### Static work law

The legal lower certificate has:

- 12 first-opportunity current contexts;
- at most 24 receiver-visible anchor histories and 48 latent first-step atoms;
- 12 later current contexts;
- 3 action values per anchor/context; and
- at most 864 later exact action-score evaluations plus aggregation.

The upper certificate has:

- 24 (R,c) cells;
- 72 action variables;
- 24 normalization equalities; and
- 2 harm inequalities.

The two-constraint exact dual contains at most 72 action-pair tie lines. Its complete
nonnegative-quadrant candidate arrangement has at most

$$
1+2(72)+\binom{72}{2}=2701
$$

candidate points. Evaluating three adjusted actions in all 24 cells at every candidate requires at
most

$$
2701\times24\times3=194{,}472
$$

exact rational action-score evaluations, followed by exact primal recovery and certificate
verification.

### Result-blind project-cost command

Before any scientific output root exists, a non-result project-cost command must:

1. execute the complete lower and upper computational path on a deterministic synthetic 24-cell,
   three-action, two-constraint table;
2. use 512-bit rational numerators and denominators and the full 2,701-candidate envelope;
3. contain no ACVC probabilities, rewards, DET-CF values, scientific thresholds, or branch
   calculation;
4. report only total wall time, peak RSS, and static operation counts; and
5. discard every synthetic objective and action selection.

Admission requires

$$
3\times\text{measured wall time}\le120\text{ seconds},
$$

and

$$
2\times\text{measured peak RSS}\le1.5\text{ GiB}.
$$

Admission failure launches no scientific calculation, creates no scientific root, and produces no
branch. Without assigning HC-D as an observed result, the direction remains at the exact re-entry
dependency that HC-D specifies.

### Result invocation

- Seeds: none.
- Sweep: none; no per-arm sweep cost law applies.
- Invocations: exactly one deterministic result-bearing invocation.
- Runtime: one CPU process and one computational thread.
- Arithmetic: exact rational only.
- Cap: 120-second hard wall and 1.5-GiB peak RSS.
- Fresh memory admission: immediately before the result invocation run
  python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>, requiring physical and
  effective available memory both at least 4 GiB.
- Hard-stop checks occur at deterministic candidate-block boundaries, not only after the complete
  calculation.
- Output: exactly one summary.json containing every card-required field and receipt.
- No validation split, checkpoint, resume, retry, result-informed rerun, seed panel, tolerance,
  grid, or outcome-dependent extension.
- Missing ordinary resource telemetry leaves an otherwise complete non-resource claim marked
  resources_unmeasured under repository policy; a measured cap breach remains HC-X.

Any added lower-policy family, horizon, threshold, prior, confidence, age, reward, tolerance,
grid, or harm envelope is a new scientific object.

## 11. Stop rule

Stop successfully only after:

1. project-cost admission passed prospectively;
2. fresh 4-GiB memory admission passed for the result invocation;
3. DET-CF, HIST-1UPDATE-CF, and REGIME-ORACLE-ENVELOPE completed in exact arithmetic;
4. every primary value, action and harm rate, witness/no-witness field, forced-DET-CF advantage,
   normalization check, LP coefficient, exact primal/dual certificate, work count, launch fact,
   and resource field is present;
5. exact primal and dual objectives agree and all integrity inequalities pass; and
6. the frozen ordered HC rule maps the complete result once.

Stop as HC-X on any integrity or admission condition. Do not salvage, resume, or interpret a
partial calculation. An outcome-blind repair at a new SHA is a fresh A/RECON attempt and requires
new admission.

## 12. Protected semantics and CM objective

CM must implement the smallest isolated research path that preserves:

- every unchanged R01 host probability, role, information boundary, action, reward, tie order,
  threshold, harm definition, and no-truth-after-VETO rule;
- exact HIST-1UPDATE-CF opportunity-one anchoring and deliberate refusal to update that anchor
  later;
- unchanged DET-CF and its exact host-law value;
- the 24-cell regime-oracle relaxation as certificate-only extra information;
- exact LP coefficients, feasible set, primal/dual certificate, complementary slackness, and
  dominance interpretation;
- every observable, exact rational representation, branch condition, precedence, and mapping;
- the synthetic result-blind cost path and its multipliers;
- one deterministic one-process/one-thread result invocation, fresh 4-GiB admission, hard cap
  checks, 120-second / 1.5-GiB limits, exact launch SHA and argv, one summary, and the repository
  resources_unmeasured rule; and
- no writes outside the named research, runner, test, scratch, and later evidence paths.

Owned paths are:

- experiments/candidates/acvc/history_headroom_certificate_r02/;
- scripts/run_acvc_history_headroom_certificate_r02.py, with the runner below 600 lines;
- tests/experiments/candidates/acvc/history_headroom_certificate_r02/;
- temp/directions/acvc/exp/history_headroom_certificate_r02_20260904/; and
- this object's later result evidence and intake after DM interpretation.

R01 code, cards, results, and the DO_NOT_INTEGRATE diagnostic branch are read-only. Core MARL code
is outside scope.

Technical success means only that the exact carded calculation and publication path conform and
complete. It cannot establish a scientific branch, history value, learner competence, or any
Portfolio action; the DM alone applies the frozen rule to accepted output.

Required tests are focused exact-likelihood, legal-information, lower-policy anchoring,
no-truth-after-VETO, DET-CF parity, harm normalization, upper-certificate primal/dual,
forced-action, witness, and branch-rule tests, plus one under-60-second end-to-end synthetic or
reduced-work publication-path smoke. Tests cannot substitute for project-cost admission or the
result invocation.

## 13. Engineering-scope contract

**This object needs none of the default-prohibited machinery in
docs/project/ENGINEERING_SCOPE_SPEC.md section 4.**

It adds no multi-process or distributed execution, queue or scheduler, checkpoint/resume/retry,
lease/heartbeat, tamper evidence, hash chain, byte manifest, provenance/currentness guard, incident
tree, schema framework, registry, compatibility shim, worker system, repeated smoke loop, or
telemetry beyond wall time, peak RSS, and the card-required static counts.

Research code remains below 2,000 new non-test lines, the runner below 600 lines, orchestration
below 30 percent of the diff, and the direction test directory below its normative budget. Any
section-5 budget breach is returned as a named engineering breach and is not accepted as the price
of a result.

## 14. REMOTE_FIRST launch boundary

Freezing and pushing this card does not activate implementation or a result invocation. No CM or
experiment task is launched until Root explicitly marks the node active.

After activation, portable result-bearing work must:

1. bind the exact pushed implementation SHA;
2. use a detached remote worktree;
3. use one remote agent task for the fresh admit-memory command and the runner;
4. keep the result process detached from the directing agent; and
5. preserve every existing local process.

This execution boundary does not alter the science, budget, admission rule, branch mapping, or
evidence class.

## 15. Non-goals

Do not rerun or change B1, uncertain/delayed R01, or the blocked full-DP R01; add a learner; tune
an optimizer; alter the host, horizon, consequence envelope, threshold, or tie order; treat the
oracle as a legal treatment; substitute sampled or approximate evaluation; use a posterior grid
or tolerance; expose hidden regime to the legal lower policy; infer truth after VETO; weaken
DET-CF; introduce a policy sweep or C-time obligation; modify core MARL code; or infer a Portfolio
decision.
