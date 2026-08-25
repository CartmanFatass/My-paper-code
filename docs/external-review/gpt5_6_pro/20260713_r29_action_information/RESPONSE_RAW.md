## 1. **Verdict: MODIFY R29**

Retain the R29 density-ratio family, uniform codebook prior, old-policy recomputation, detachment, coefficient `0.05`, clip `0.05`, and low-level-only PPO placement. Replace the independent per-action ratio with **one fixed-skill recurrent action-sequence ratio on the final 10 steps of each complete natural skill lifetime**.

The decisive reason is temporal, not support-related. At a fixed recurrent state, the present ratio is a valid interventional action-information statistic. But in training it can be increased through state-local Gaussian mean, variance, or tanh-saturation coding without requiring one skill to remain behaviorally identifiable through its recurrent lifetime. GAE accumulates pointwise rewards, but it does not change that pointwise denominator into a persistent-skill comparison.

R27’s discriminating evidence was specifically that a label held through the recurrent executor continued to control late actions relative to a 10-step pulse. The next reward should therefore make **one candidate skill explain a late action block after being recurrently active throughout the natural segment**. That is the smallest change that follows the positive R27 result rather than merely amplifying R29-G0’s instantaneous statistic. ([R27 design](sandbox:/mnt/data/hmasd_r29_review/docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md), lines 27–39, 243–255, and 387–406; [research background](sandbox:/mnt/data/hmasd_r29_review/RESEARCH_BACKGROUND.md), lines 254–266.)

I would not reject action information as a target family. I would reject running the current **pointwise** form unchanged as the decisive reward experiment.

---

## 2. **Objective derivation and failure analysis**

### 2.1 What the current ratio means at a fixed recurrent context

Let

[
x=(o,h),\qquad
p_z(a\mid x)=\pi_{\bar\theta}(a\mid o,h,z),
]

where (\bar\theta) is the frozen collection policy for the current rollout, and let

[
u(z)=\frac1K,\qquad
m_u(a\mid x)=\frac1K\sum_{j=1}^K p_j(a\mid x).
]

The R29 reward is

[
r_u(x,z,a)
==========

\log p_z(a\mid x)-\log m_u(a\mid x).
]

If, at this fixed (x), the source skill is sampled uniformly and then the action is sampled from that skill policy,

[
Z\sim u,\qquad A\sim p_Z(\cdot\mid x),
]

then

[
\begin{aligned}
J_u(x)
&=
\mathbb E_{Z\sim u,A\sim p_Z}
\left[r_u(x,Z,A)\right]\
&=
\frac1K\sum_{z=1}^K
D_{\mathrm{KL}}!\left(p_z(\cdot\mid x),\middle|,m_u(\cdot\mid x)\right)\
&=
I_u(Z;A\mid X=x).
\end{aligned}
]

Thus it is the generalized Jensen–Shannon divergence among the (K) action policies at (x), with

[
0\le J_u(x)\le \log K.
]

For (K=4), the upper bound is (\log4\approx1.386) nats.

The tanh treatment is correct. Every candidate scores the same squashed action, so the candidate-independent sum of tanh-Jacobian terms cancels in the log ratio. The actual-skill squashed likelihood can still be used for parity with PPO’s stored old log probability. ([R29 evaluator](sandbox:/mnt/data/hmasd_r29_review/ha_ctse_process/r29_action_information.py), lines 115–162; [online reward](sandbox:/mnt/data/hmasd_r29_review/ha_ctse_process/r29_action_information_reward.py), lines 73–180.)

### 2.2 Why the online expectation is not generally that uniform-prior mutual information

Natural rollouts do not normally sample (z) uniformly conditional on the visited recurrent context. Write the natural joint occupancy as

[
\Pr(X=x,Z=z)=d(x)\rho_z(x),
]

where

[
\rho_z(x)=\Pr(Z=z\mid X=x).
]

Define the natural action marginal at (x),

[
m_\rho(a\mid x)=\sum_z\rho_z(x)p_z(a\mid x).
]

The expectation of the actual online R29 score is then

[
\begin{aligned}
\mathcal J_{\mathrm{nat},u}
&=
\mathbb E_{d(x)\rho_z(x)p_z(a\mid x)}
\left[\log\frac{p_z(a\mid x)}{m_u(a\mid x)}\right]\
&=
I_{\mathrm{nat}}(Z;A\mid X)
+
\mathbb E_{X\sim d}
D_{\mathrm{KL}}!\left(
m_\rho(\cdot\mid X),\middle|,m_u(\cdot\mid X)
\right).
\end{aligned}
]

So the online expectation equals natural conditional action information **plus a prior/mixture mismatch term**. It is not the natural conditional mutual information unless (\rho_z(x)=1/K).

This does not mean frequency imbalance alone fabricates a signal: if all (p_z) are identical, both terms remain zero. It means that once the action laws differ, the natural weighting and the uniform denominator optimize a different quantity from natural (I(Z;A\mid X)).

The observed normalized label entropy near (0.998) only establishes that the global marginal (P(Z)) is close to uniform. It does not establish that (P(Z\mid o,h)) is uniform. Because skills persist and influence observations and recurrent histories, (P(Z\mid o,h)) can be concentrated even when the aggregate histogram is balanced. The R29-G0 results therefore validate the uniform **interventional codebook channel**, not a learned-usage mutual information. ([R29 aggregate](sandbox:/mnt/data/hmasd_r29_review/logs/r29_action_information_20260713_230631/r29_action_information_aggregate.json), lines 25–58, 73–106, and 121–154.)

Replacing (u(z)) with the global learned frequency (P(Z=z)) would not solve this. It would merely replace (m_u) with (m_{P(Z)}), while the correct natural conditional marginal is based on (\rho(z\mid x)). Estimating that posterior would require another classifier or density model and would re-open the shortcut line that R26 and the earlier process-posterior work already constrained.

For the next run, the uniform mixture should therefore be retained and explicitly interpreted as a **desired equiprobable skill-code intervention prior**, not as the learned skill marginal.

### 2.3 Skill-dependent visitation and recurrent-state semantics

Holding (x=(o,h)) fixed is an important strength: the score cannot earn reward merely because a classifier can read the skill from the observation. Nevertheless, natural occupancy still determines which (x)'s receive weight.

There is also a recurrent qualification. The stored (h_t) was produced by the actual preceding skill and observation history. Evaluating (z'\neq z_t) at the same (h_t) is a local intervention on the actor, not a naturally occupied ((h_t,z')) pair. This is not the R28 failure mode: there is no externally trained scorer or empirical support envelope that must transport to those states. But the valid claim remains “the actor’s action law changes under a local skill substitution at this natural context,” not “this is the likelihood of the counterfactual environmental trajectory under (z').”

### 2.4 What detachment does—and when it is exact

For fixed (x), uniform source sampling has a useful identity:

[
\nabla_\theta J_u(x)
====================

\mathbb E_{z\sim u,a\sim p_z}
\left[
r_u(x,z,a)\nabla_\theta\log p_z(a\mid x)
\right].
]

The direct derivatives of the numerator and mixture cancel after integrating over all uniformly weighted source policies. Therefore a detached R29 reward used as a score-function reward is not intrinsically wrong: under uniform source sampling and fixed contexts it gives the correct first-order gradient of the uniform JSD.

Under natural source weighting (\rho), however, define

[
F_{\rho,u}(x)
=============

\sum_z\rho_z
\int p_z(a)\log\frac{p_z(a)}{m_u(a)},da.
]

Its gradient contains

[
\nabla_\theta F_{\rho,u}
========================

\mathbb E_{\rho_zp_z}
\left[
r_u\nabla_\theta\log p_z
\right]
-------

\int m_\rho(a)\nabla_\theta\log m_u(a),da.
]

The detached PPO update retains the first term and omits the second. The omitted term vanishes when the source and mixture weights match, but not in general. Dependence of visitation, recurrent histories, and skill usage on the policy introduces further omitted direct derivatives. Consequently, the actual R29 update is best described as an **old-policy semi-gradient diversity regularizer**, not exact gradient ascent on either natural MI or uniform JSD over the natural trajectory distribution.

Detachment is still the correct operational boundary for PPO:

* the reward remains fixed throughout PPO epochs;
* no reward gradient leaks directly through the collection actor;
* no gradient reaches the high-level selector, skill lifetime, observations, actions, or counterfactual candidates;
* the low actor changes only through its PPO log-likelihood and shaped advantage;
* the low critic fits the shaped return.

The limitation is that unexecuted candidate skills do not receive their own direct update at that row. They affect only the detached scalar denominator; uniform coverage across naturally executed skills is what makes the JSD interpretation approximately relevant over time.

### 2.5 Likely pathologies

The current pointwise objective can increase through any mechanism that makes the four diagonal-Gaussian action laws easier to identify:

[
\log p_z(u)
===========

-\frac12\sum_d
\left[
\frac{(u_d-\mu_{z,d})^2}{\sigma_{z,d}^2}
+2\log\sigma_{z,d}
+\log 2\pi
\right].
]

That includes:

1. separating the means, potentially by pushing squashed actions toward different tanh-saturated regions;
2. giving skills different variances;
3. shrinking the active skill’s variance while making other candidates assign low likelihood to its samples;
4. implementing a statewise label code whose interpretation changes across contexts;
5. generating diversity unrelated to the environmental task.

The entropy bonus opposes some variance collapse, but there is no semantic or state-effect term in R29 itself.

The observed distribution reinforces this concern. At the final checkpoint, the mean score is only (0.019208) nats, while the 1st and 99th percentiles are approximately (-0.517) and (+0.511). After multiplying by `0.05`, the mean intrinsic increment is approximately (9.6\times10^{-4}), while those percentiles are about (\pm0.0256). Since clipping begins only when (|r_{\mathrm{AI}}|>1), those tails are not clipped. The scorer is real, but its per-row signed variability is much larger than its mean. ([R29 aggregate](sandbox:/mnt/data/hmasd_r29_review/logs/r29_action_information_20260713_230631/r29_action_information_aggregate.json), lines 25–30.)

Persistent natural (z_i) and GAE make the existing implementation less myopic than an isolated one-step auxiliary loss, because the same label receives reward repeatedly over 10–40 steps. But each time step still resets the mixture comparison. It never asks whether **one fixed counterfactual skill, propagated through the recurrent actor, explains a late action process**.

The most likely failure is therefore not absence of actor capacity. R27 already rules that out. Nor is pure variance collapse the leading hypothesis, because R27 found deterministic-action and local-trajectory effects under forced labels. The leading failure is:

> **R29 successfully amplifies skill-specific action coding—probably through means as well as variances—but the coding remains state-local or task-irrelevant and does not convert R26’s natural process-level negative into persistent natural behavior.**

---

## 3. **Exact recommended algorithm**

### R29-T10: recurrent terminal-block action information

Consider one agent’s complete natural skill segment (g), collected under (\bar\theta):

[
g=
\left(
z_g,,
h_{g,0},,
o_{g,0:L_g-1},,
a_{g,0:L_g-1}
\right),
]

where

[
L_g\in{10,20,30,40}.
]

Only naturally completed full lifetimes are scored. A segment truncated before its selected lifetime by episode termination or rollout truncation receives no intrinsic score.

Let the terminal window be

[
T_g={L_g-10,\ldots,L_g-1}.
]

For every candidate skill (k\in{1,\ldots,K}), begin from the segment’s stored collection-time pre-step hidden state:

[
\hat h^{(k)}*{g,0}=h*{g,0}.
]

Replay the **natural observation sequence** through the frozen recurrent actor while holding candidate (k) fixed for the entire segment:

[
\left(
y^{(k)}*{g,t},\hat h^{(k)}*{g,t+1}
\right)
=======

\operatorname{ActorRNN}*{\bar\theta}
\left(
\operatorname{FiLM}*{\bar\theta}
\big(f_{\bar\theta}(o_{g,t}),k\big),
\hat h^{(k)}_{g,t}
\right).
]

Use (y^{(k)}_{g,t}) to obtain the candidate tanh-Gaussian action density. Define the candidate terminal-block log likelihood

[
\ell_{g,k}
==========

\sum_{t\in T_g}
\log
\pi_{\bar\theta}
\left(
a_{g,t}
\mid
o_{g,t},\hat h^{(k)}_{g,t},k
\right).
]

The persistent action-information score is

[
R^{\mathrm{T10}}_g
==================

## \ell_{g,z_g}

\log
\left[
\frac1K\sum_{k=1}^K
\exp(\ell_{g,k})
\right].
]

Equivalently, the denominator is

[
\frac1K\sum_k
\prod_{t\in T_g}
\pi_{\bar\theta}
\left(
a_{g,t}\mid o_{g,t},\hat h^{(k)}_{g,t},k
\right),
]

not

[
\prod_{t\in T_g}
\left[
\frac1K\sum_k
\pi_{\bar\theta}(a_{g,t}\mid\cdots,k)
\right].
]

That distinction is load-bearing: a single candidate skill is held fixed across the recurrent path and the entire terminal action block.

At a fixed natural observation sequence and initial hidden state, define

[
P_k(A_{T_g}\mid O_g,h_{g,0})
============================

\exp(\ell_{g,k}).
]

Under a synthetic uniform source skill, the expected score is

[
\frac1K\sum_k
D_{\mathrm{KL}}
\left(
P_k
,\middle|,
\frac1K\sum_jP_j
\right)
=======

I_u(Z;A_{T_g}\mid O_g,h_{g,0}),
]

again bounded above by (\log K). It is action-sequence information conditional on a natural observation path, not state-transition MI.

Replaying the recurrent state is necessary. Merely summing current R29 row scores while repeatedly restoring the actual stored (h_t) would not be the likelihood of any single persistent recurrent candidate policy.

### Prior and marginal

Use exactly

[
u(k)=\frac14.
]

Do not substitute empirical rollout frequencies or the global learned skill histogram. Those quantities are not (P(Z\mid O_g,H_g)), and using them would neither remove skill-dependent visitation bias nor produce natural conditional MI. Uniform remains the declared intervention prior over the four executable codes.

### Reward scaling and placement

Keep the current coefficient and clip:

[
\widehat R_g
============

\operatorname{clip}
\left(
0.05,
\operatorname{stopgrad}
[R^{\mathrm{T10}}_g],
-0.05,
0.05
\right).
]

Add it once, at the final primitive step of the segment:

[
r^{\mathrm{low}}_{t,i}
======================

r^{\mathrm{env}}_{t,i}
+
\mathbf 1[(t,i)=\operatorname{end}(g)]
\widehat R_g.
]

Do not copy or divide the segment score across all segment steps. Treat it as a terminal low-level outcome and let the existing GAE recursion carry credit backward through the segment. This preserves a single bounded reward opportunity per natural lifetime and prevents the same sequence information from being counted (L_g) times.

The score itself must not use environment reward or any communication-specific field.

### Detach and PPO boundaries

All candidate recurrent replays, action distributions, likelihoods, mixture terms, and the final clipped reward are computed under (\bar\theta) with no gradient. The source-skill replay must reproduce PPO’s stored old squashed log likelihood on its rows; the existing `2e-5` tolerance remains appropriate.

Then:

* `probe_only` computes and logs (R_g^{\mathrm{T10}}), but leaves rollout rewards untouched.
* `real_reward` adds (\widehat R_g) only to the terminal primitive low-level reward.
* The modified low rewards enter the existing low-level GAE and low actor/critic PPO update.
* No intrinsic value enters high-level segment returns.
* No gradient reaches the high-level skill or duration policy.
* Collector behavior, environment execution, asynchronous renewals, skill lifetimes, team mechanisms, and the low actor interface (\pi_l(a_i\mid o_i,z_i)) remain unchanged.

This is one scoring change, not a new model family.

---

## 4. **One next experiment**

Run exactly two mechanism-matched arms:

[
\texttt{probe_only}
\quad\text{versus}\quad
\texttt{real_reward},
]

both using R29-T10. No sham arm and no separate engineering-smoke stage are needed. `probe_only` already matches all score computation and differs only in whether the detached scalar is added to low-level reward.

### Exposure and seeds

Start both arms from the same R25 arm0 final checkpoint at (1{,}000{,}000) environment steps.

Use three paired continuation seeds:

[
29031,\quad 29032,\quad 29033.
]

Within each seed pair, match initial policy state, environment seeds, collector settings, optimizer settings, and every non-R29 reward/configuration. Analyze paired seed differences rather than treating the six runs as independent.

Use:

* 16 vector environments;
* rollout length 500;
* 8,000 environment transitions per PPO update;
* 20 PPO updates;
* (160{,}000) additional environment steps per arm;
* the source low-PPO exposure, including 15 low PPO epochs.

Thus the endpoint is (1{,}160{,}000) environment steps. Ten updates or (80{,}000) steps are too weak as a negative decision for a clipped signal of this scale; (160{,}000) is still a mechanism test rather than a long-run performance comparison.

At the endpoint, collect 64 matched natural evaluation reset groups per arm and seed for action-information and frozen R26 analysis, plus the existing 20 deterministic task-evaluation episodes per seed. Use paired reset-cluster bootstrap intervals, 10,000 repetitions, with fixed bootstrap seed `29034`.

### Primary decision metrics

| Metric                         | Precommitted threshold                                                                                                                                                                                                                                                                                                                       |               |                                                                                                                                            |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Exact target movement**      | Let (\Delta_{\mathrm{T10}}) be pooled mean held-out (R_g^{\mathrm{T10}}) in `real_reward` minus `probe_only`. Require (\Delta_{\mathrm{T10}}\ge 0.05) nats and its paired reset-cluster 95% lower bound (>0). At least two of three seed-level differences must be positive, and no pooled skill-specific difference may be negative.        |               |                                                                                                                                            |
| **Natural process transfer**   | Run the unchanged frozen R26 natural-window analyzer as a diagnostic only. `real_reward` must pass its natural behavior gate in at least two of three seeds, while `probe_only` passes in at most one. The pooled real-minus-probe improvement in the R26 held-out full-minus-prior gain must be at least `0.05`, with 95% lower bound (>0). |               |                                                                                                                                            |
| **No skill or scale collapse** | Normalized natural skill-label entropy must remain at least `0.80`. The per-rollout mean-absolute intrinsic/environment reward ratio must remain at most `0.05`. Likelihood parity and all reward/value quantities must remain finite.                                                                                                       |               |                                                                                                                                            |
| **Task safety**                | In every paired seed, ((R_{\rm probe}-R_{\rm real})/\max(                                                                                                                                                                                                                                                                                    | R_{\rm probe} | ,10^{-8})\le0.10). The zero-service episode fraction may worsen by at most `0.10` absolute. These are safety gates, not intrinsic targets. |

The R26 analyzer is not added to training and is not a new reward classifier. It is the existing independent natural-process read needed to determine whether optimization of the exact score transported beyond policy-density coding.

Also report, without using it as another optimization target, the pairwise Gaussian symmetric-KL decomposition into mean and variance components on the terminal rows. This classifies a failure:

* full score rises almost entirely through the variance component: variance coding;
* deterministic means separate but R26 remains negative: task-irrelevant/state-local mean coding;
* both score and R26 move: natural process transfer.

### PASS/FAIL interpretation

**PASS** requires all four rows in the table. It means the reward changed the exact actor channel, that change transferred to the pre-existing natural process-level read, skills did not collapse, and the short continuation did not materially damage task behavior.

Otherwise classify the mechanism as **FAIL**, with the causal localization determined as follows:

* (\Delta_{\mathrm{T10}}) fails: the detached clipped reward did not produce a measurable actor-learning effect.
* (\Delta_{\mathrm{T10}}) passes but R26 transfer fails: the action-density objective produced only likelihood coding; this falsifies the bridge from action information to natural persistent skill behavior.
* Target and R26 pass but task safety fails: differentiation was learned but was not useful enough to coexist with external-task optimization; reject this target rather than beginning a coefficient sweep.
* Both arms pass R26 or the paired R26 difference misses its threshold: continuation training, not reward injection, explains the result.

---

## 5. **What the result would and would not support**

A PASS would support the narrow claim:

> Under natural on-policy visitation, a uniform-prior, fixed-skill recurrent terminal-action density ratio, added only as a small detached low-level completion reward, causally increases natural individual-skill process differentiation over a 160,000-step continuation without short-horizon task-safety regression.

It would also show that the R27 forced conditional capacity can be converted into natural learning pressure without a separately trained scorer or support envelope.

It would **not** establish:

* that the score is mutual information under the learned skill marginal;
* that alternate candidates represent full counterfactual environment trajectories;
* semantic task roles or general-purpose option meaning;
* complementary team assignment or team-level cooperation;
* improved high-level skill selection or duration choice;
* benefit from asynchronous rather than fixed/shared lifetimes;
* task improvement, HMASD parity, long-run stability, or cross-environment generalization;
* usefulness of team reward, (q_d/q_D), (q_A), DADS, or any retired scorer family.

A FAIL would not weaken R27’s capacity result. In particular, a target-score increase with no R26 transfer would give a clean new conclusion: **the recurrent actor can express skill-dependent behavior, but action-density identifiability—even when temporalized over the late native window—is not sufficient to make natural skills behaviorally meaningful.**
