# RISP prospective population-law decision audit

```text
direction_id=renewal_indexed_score_plasticity
candidate_law=PC3-IID-REFERENCE
candidate_law_status=MATHEMATICALLY_COMPLETE_NOT_ADOPTED
scientific_activity=DERIVATION_AND_LOCAL_LITERATURE_AUDIT
result_bearing_experiment_executed=false
census_executed=false
implementation_recommendation=NO_IMPLEMENTATION
```

## Conclusion

A witness-independent, finite, exactly normalized population law can be written down. That fact
does **not** resolve the RISP blocker. The smallest convenient candidate, `PC3-IID-REFERENCE`, is an
off-policy reference occupancy whose stopping, duration, action, opportunity, regret denominator,
and materiality choices are all prospective conventions. No current target, source, or local
literature evidence selects those conventions. Changing any of them changes both the coarsened
Bayes controllers and the reported prevalence/regret.

Therefore this candidate is audited below but is not adopted as conclusion-bearing RISP authority.
Do not ask CM to implement or enumerate it. The completed four-history ECR result remains an exact
existence theorem/control; it does not supply a standalone learned-successor investment case.

## Question and non-goals

The two questions are separate:

1. Can one define a complete normalized law over public renewal histories without selecting or
   weighting the four registered ECR witnesses?
2. Would the resulting exact census answer a target-grounded question capable of changing the
   standalone RISP investment decision?

The answers are respectively **yes** and **no** for the candidate below. This audit does not inspect
the complete ECR artifact, rerun ECR, enumerate a new census, introduce learning, or change the
direction or Portfolio authorities.

## Inputs: inherited facts versus prospective assumptions

The following are inherited from current ECR authority:

- sectors/actions `LEFT < CENTER < RIGHT` and that deterministic tie order;
- uniform initial hidden-sector belief;
- duration support \(\mathcal K=\{4,8,12\}\);
- \(P_k=J/3+(15/16)^k(I-J/3)\);
- ACK probability \(4/5\) on completion-sector match and \(1/5\) otherwise;
- motion, ACK, update, and next-action event order;
- the next-hold value
  \[
  Q(a\mid b,k)=k[-3/5+(6/5)(bP_k)(a)];
  \]
- the exact full, duration-erased, and last-ACK information projections; and
- deterministic primitive clocks and next-hold credit.

Current authority does not inherit a stopping/count law, duration-string law, behavior occupancy,
decision-opportunity law, next-duration law, variable-duration regret denominator, or numeric
materiality rule. The choices below are therefore candidate assumptions, not recovered facts.

## A complete candidate law: `PC3-IID-REFERENCE`

This candidate has exactly three completed renewals: \(N=3\) almost surely. It samples the single
terminal decision opportunity after the third ACK/update. Equivalently, the stopping hazard is zero
before that opportunity and one immediately after the third completed event. There is no censoring,
survival selection, replacement, or incomplete hold.

Independently sample

\[
K_1,K_2,K_3,K_4\overset{iid}{\sim}\operatorname{Unif}(\mathcal K),
\qquad
A_1,A_2,A_3\overset{iid}{\sim}\operatorname{Unif}(\mathcal A),
\]

where \(K_4=K_{\mathrm{next}}\) is visible at the terminal decision. The uniform action law is a
prospective promotion of the old full-support reachability reference into a behavior population; it
is not a learned or natural-policy law.

Let \(X_0\sim\operatorname{Unif}(\mathcal A)\). For \(i=1,2,3\), draw
\(X_i\sim P_{K_i}(X_{i-1},\cdot)\), followed by ACK \(Y_i\) under the inherited match/mismatch law
\(\ell(Y_i\mid A_i,X_i)\). The full atom has exact probability

\[
\mu(k_{1:4},a_{1:3},x_{0:3},y_{1:3})
=3^{-8}\prod_{i=1}^{3}
P_{k_i}(x_{i-1},x_i)\ell(y_i\mid a_i,x_i).
\]

The public-history mass is obtained by summing this expression over \(x_{0:3}\). Every atom is a
positive rational. Exact normalization follows because the four duration factors, three action
factors, and initial-state factor each sum to one, every row of every \(P_k\) sums to one, and
\(\sum_y\ell(y\mid a,x)=1\). Hence summing \(\mu\) over the entire augmented sample space is exactly
one. The public census contains

\[
3\cdot(3\cdot2\cdot3)^3=17{,}496
\]

histories, including all three choices of visible \(K_4\), with no witness row or twin given special
weight.

Primitive clocks are deterministic: \(T_0=0\),
\(T_i=\sum_{j=1}^{i}K_j\), and the evaluated credit interval is
\([T_3,T_3+K_4]\). The observational unit is one terminal renewal opportunity per generated
history, not a uniformly sampled primitive-time instant and not a stationary Palm population.

## Competent coarsened nulls

For public history \(h\), let \(b_h=P(X_3\mid h)\). The inherited views are

\[
V_E(h)=((A_i,Y_i)_{i=1}^{3},K_3,N=3,K_4)
\]

for `FULL_BAYES_K_ERASED`, and

\[
V_L(h)=(A_3,Y_3,K_3,N=3,T_3,K_4)
\]

for `LAST_ACK_BAYES`. For \(C\in\{E,L\}\), the strongest competent same-information null is
defined under this candidate population, not copied from the equal-weight witness census:

\[
b_C(v)=
\frac{\sum_{h:V_C(h)=v}\mu(h)b_h}
     {\sum_{h:V_C(h)=v}\mu(h)}
=P(X_3\mid V_C=v).
\]

All denominators are positive on the support. Since \(K_4\) is present in both views and \(Q\) is
linear in belief, maximizing \(Q(a\mid b_C(v),K_4)\) is the Bayes-optimal action at that information
level. `LAST_ACK_G` is not a competent matched-information null for this question.

## Exact census estimands, regret units, and ties

Let \(a_F(h)\) and \(a_C(h)\) maximize the appropriate exact \(Q\) values using the printed tie
order, and define

\[
g_C(h)=Q(a_F(h)\mid b_h,K_4)-Q(a_C(h)\mid b_h,K_4)\ge0.
\]

An exact census would map the normalized law to:

\[
p_C^a=\sum_h\mu(h)\mathbf1[a_F(h)\ne a_C(h)],
\qquad
p_C^+=\sum_h\mu(h)\mathbf1[g_C(h)>0],
\]

the equal-opportunity, per-hold normalized regret

\[
R_C^{\mathrm{opp}}=\sum_h\mu(h)\frac{g_C(h)}{K_4},
\]

and the semi-Markov physical-time rate

\[
R_C^{\mathrm{time}}
=\frac{\sum_h\mu(h)g_C(h)}{\sum_h\mu(h)K_4}
=\frac{\sum_h\mu(h)g_C(h)}{8}.
\]

These two regrets are not generally equal even though \(K_4\) is marginally uniform. A conditional
severity diagnostic is

\[
S_C=E_\mu[g_C(H)/K_4\mid g_C(H)>0]
\]

when \(p_C^+>0\). All histories, including ties, remain in the common denominator. The census must
separately report full and null tie mass and the zero-regret action-difference mass
\(p_C^a-p_C^+\). Printed-order action differences created only by a tie therefore cannot masquerade
as native value.

One numerically complete screening convention could declare comparator \(C\) material only when

\[
p_C^+\ge1/100,\qquad
R_C^{\mathrm{time}}\ge1/1000,\qquad
S_C\ge1/20,
\]

with equality passing, and otherwise distinguish `SUBMATERIAL` (positive regret but a missed floor),
`TIE_ONLY` (action difference but zero regret), and `EXACT_NULL`. The two comparators would be
classified separately because their views are not nested: the erased view retains the full ordered
action/ACK sequence but not total time, while the last-ACK view retains total time but not the older
sequence.

These exact numbers are presented only to demonstrate that a complete branch can be specified. They
are not inherited, literature-derived, cost-calibrated, or accepted for a result. Freezing them would
convert a convenient convention into apparent scientific authority.

## Direct observations and literature boundary

The accepted ECR result proves that earlier public outcomes and completed-duration order can change
a unique exact action and native value on the frozen four-history support. It does not provide a law
over how often those histories or their information views occur.

The formal InstSci library was audited at its current `190 PDF / 190 JSON / 190 Metadata v2` integrity
baseline. It contains no direct renewal/Palm, opportunity-sampling, stationary holding-time
weighting, or renewal-reward source. The useful local sources constrain interpretation but do not
select the candidate law:

- `MARL-0621`, *HMARL-CBF – Hierarchical Multi-Agent Reinforcement Learning with Control Barrier
  Functions for Safety-Critical Autonomous Systems* (NeurIPS 2025; no DOI recorded), distinguishes
  variable-duration SMDP actions, accumulated reward over \(k\) steps, and termination-defined
  decision epochs. Evidence:
  `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0621.json` and
  `C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0621.pdf`.
- `MARL-0449`, *Agent-Centric Actor-Critic for Asynchronous Multi-Agent Reinforcement Learning*
  (ICML 2025; no DOI recorded), distinguishes elapsed micro-time from macro-action decision count
  under variable action durations. Evidence:
  `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json` and
  `C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0449.pdf`.
- `MARL-0061`, *AgentMixer: Multi-Agent Correlated Policy Factorization* (AAAI 2025,
  DOI `10.1609/aaai.v39i17.34048`), defines a coarsened policy by conditional averaging under a
  **policy-induced occupancy** and gives a mechanism by which that averaging need not preserve the
  fine-information action. Evidence:
  `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0061.json` and
  `C:/Projects/Inst-sci/papers/MyLib/pdf/MARL-0061.pdf`.
- `VS-0002`, *Continuous-Time Value Iteration for Multi-Agent Reinforcement Learning* (ICLR 2026;
  no DOI or official URL recorded), treats variable decision gaps in physical-time value. Evidence:
  `C:/Projects/Inst-sci/papers/MyLib/json/VS-0002.json` and
  `C:/Projects/Inst-sci/papers/MyLib/pdf/VS-0002.pdf`.

These sources support keeping event, time, and occupancy measures explicit. None supplies RISP's
stopping distribution, behavior occupancy, duration law, opportunity weighting, regret unit, or
materiality floors.

## Limitations and strongest contradiction

`PC3-IID-REFERENCE` fails the decision-relevance test for four independent reasons:

1. Uniform actions are an off-policy excitation law. Actions affect ACK information, so changing to
   a Bayes, learned, or deployed behavior changes the public-history occupancy and the conditional
   Bayes nulls themselves.
2. Fixed count three, IID-uniform durations, a terminal-opportunity sample, and uniform next duration
   are convenience choices. Current evidence is compatible with many different normalized laws that
   give different answers.
3. The registered duration-order witness has four completed events. A nonmaterial three-event census
   could not adjudicate the already-established four-event phenomenon. Expanding to all histories
   through count four or eight removes this depth objection but not the arbitrary-occupancy problem.
4. Event-opportunity regret and physical-time regret are distinct. Reporting both is honest, but it
   does not identify which one is the target utility. The proposed numeric floors are likewise not
   tied to a deployment cost, learning budget, or Portfolio utility.

The candidate is therefore easy to enumerate but scientifically non-independent. Technical success
would establish only exact arithmetic under a law chosen for convenience.

## Judgment impact and next observation

The answer to the CM implementation question is **no**. A normalized law is necessary but not
sufficient; this candidate does not cross the independent decision-value threshold. Standalone RISP
should not be reactivated for a prevalence census or learned successor on this basis. Root may close
the standalone label while retaining ECR noncommutation as a theorem/control input for another
direction such as SCDMP, with no polarity transfer.

The recommendation would change only if one of the following arrives before enumeration:

- an independently target-grounded generative law that fixes stopping, durations, behavior,
  opportunity sampling, next duration, and physical utility for an intended benchmark/deployment;
  or
- a law-robust theorem over a prospectively justified class of such populations whose lower bound
  crosses an independently cost-calibrated materiality threshold.

A generic renewal/Palm citation alone would explain how measures differ; it would not choose the
project's numerical law. Until a target law or robust class exists, the cheapest next observation is
the existence of that authority, not a census under a convenient reference occupancy.

## HMASD evidence paths

- `AGENTS.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/research/portfolio/PORTFOLIO.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/DIRECTION.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/IMPLEMENTATION_THRESHOLD.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/RISP_ECR_R01_RESULT_INTAKE.md`
- `docs/research/candidates/renewal_indexed_score_plasticity/RISP_PREVALENCE_CENSUS_R01_BLOCKER_INTAKE_20260830.md`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/exact_probability.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/reference_host.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/reachable_twins.py`
- `experiments/candidates/renewal_indexed_score_plasticity/event_conditioned_bayes_r01/controllers.py`
