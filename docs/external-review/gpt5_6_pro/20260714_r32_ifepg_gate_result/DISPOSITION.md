# Controller disposition

- Source model: GPT-5.6 Pro / ChatGPT web
- Date: 2026-07-14
- Related claim: R32 validity and the single post-R32 causal edge
- Disposition: **ACCEPT R32; MODIFY R33**

## Accepted

The R32 audit identifies no concrete M0 defect.  The registered
`FAIL_M1_RETIRE_R32_IFEPG` result is a valid scientific failure.  Direct
individual IFEPG and its learning-rate, update-count, effect, window, replica,
seed, parameter-scope, reward/value, and normal-trainer variants remain
retired.

The next causal level is complete-roster composition through the existing R30
autoregressive joint distribution.  The Alice--Bob gate keeps the proposed
16-roster intervention table, two stochastic replicas, pair-sham comparator,
exact joint-probability expectation, high-`skill_head`-only update, fixed
budget, natural transport read, and all prohibitions on low-policy, team-latent,
classifier, task-reward, and environment-shaping paths.

## Required estimator correction

The proposed raw contrast is not sufficient evidence of team complementarity.
Under the independent model

\[
E_1(a,b)=f_1(a)+u_1(b),\qquad E_2(a,b)=u_2(a)+f_2(b),
\]

its original role-swap score can be large even though there is no joint
interaction.  It can also score a one-sided orientation effect as a stable
role swap.

R33 therefore uses the same complete `4 x 4` table to remove both additive
roster-axis main effects separately for each agent and replica:

\[
\widetilde E_i^q(a,b)=E_i^q(a,b)
-\overline E_i^q(a,\cdot)
-\overline E_i^q(\cdot,b)
+\overline E_i^q(\cdot,\cdot).
\]

For each unordered pair, define

\[
\widetilde g_{ab}^q=\widetilde E_1^q(a,b)-\widetilde E_2^q(a,b),
\quad
h_{ab}^q=\tfrac12(\widetilde g_{ab}^q-\widetilde g_{ba}^q),
\quad
k_{ab}^q=\tfrac12(\widetilde g_{ab}^q+\widetilde g_{ba}^q),
\]

and the signed score

\[
\widetilde C_{ab}
=\tfrac14\left(
\langle h_{ab}^1,h_{ab}^2\rangle
-\langle k_{ab}^1,k_{ab}^2\rangle
\right).
\]

This is zero for additive independent skills and for a purely one-sided
orientation in expectation, positive for a stable antisymmetric role swap, and
negative for a stable same-direction orientation effect.  Replicas remain
independent and no ReLU is applied.  Within-context standardization leaves the
registered M1 scale interpretable in score standard deviations, so the
external thresholds and compute budget are retained.

## Required comparator correction

The raw sham mapping shares a skill in four of six mapped pairs and therefore
retains avoidable pair identity. R33 uses the fixed complementary-edge
derangement

```text
01 <-> 23
02 <-> 13
03 <-> 12
```

or source indices `[5,4,3,2,1,0]` in lexicographic pair order. It preserves
the complete signed score multiset, mean, and variance while removing both
skill identities from every mapped pair. It does not claim to preserve the
parameter-gradient norm.

## Required validity correction

The external M0 rule requiring both arms to move the skill head by more than
`1e-6` would classify an exact zero mathematical gradient as an implementation
failure and improperly authorize repair/retry.  M0 instead requires eight
finite optimizer calls, finite loss/gradient values, gradient scope restricted
to `high.skill_head`, and zero non-head drift.  Head drift and gradient norms
are recorded; a zero causal gradient is valid evidence and proceeds to M1,
where it retires the mechanism.

No normal-trainer integration, sparse-task training, seed expansion, new team
latent, `q_D`, team intrinsic reward, or classifier is authorized by this
disposition.
