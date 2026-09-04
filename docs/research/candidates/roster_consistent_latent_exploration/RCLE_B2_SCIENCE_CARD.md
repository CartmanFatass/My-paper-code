# Roster-Consistent Latent Exploration B2 science card

```text
direction=roster_consistent_latent_exploration
candidate=RCLE-B2
revision=RCLE-B2-SCIENCE-20260814-02
scientific_object=VALIDITY_ONLY_SEMANTIC_SPECIFICITY_CONTROL
owner=EM_roster_consistent_latent_exploration
science_revision_frozen=true
scientific_activity_started=false
mathematical_closure=CHATGPT_EXTERNAL_PRO_CLOSED_EXACT_V2_EM_INTAKE_COMPLETE
construction_authorization=ROOT_STAGE_AUTHORIZED_NAMED_SAME_DIRECTION_CM
compute_authorization=ROOT_DIRECTION_SCOPED_LEASE_REQUIRED
```

## Conclusion first

RCLE-B2 is the one prospective discriminator authorized by the complete
revision-04 result and its same-conversation Pro convergence. It asks whether
the rotation-identity content of RCLE's actor-facing semantic score contributes
beyond an equally scaled actor-facing signal that rewards validity alone.

The experiment is a fresh, paired, two-arm run. The `RCLE` arm preserves the
exact revision-04 treatment. The new `VALIDITY-ONLY` arm preserves the same
common latent, host, actor, initialization, posterior training and work,
samples, updates, optimizer, auxiliary coefficient, evaluation law, and
finite-toy boundary, but replaces the actor auxiliary by

```text
B_VALID = V
```

`B_VALID` itself directly reads only `V`; it contains no paired `(Z,K*)`,
hidden-lock, posterior, or semantic-score content. The complete actor
coefficient still contains the shared `K*`-dependent task reward and shared
`(N,Z)` baseline defined below. Its maximum positive auxiliary value is one,
matching RCLE's maximum positive auxiliary value. The sole primary contrast is
fresh paired held-out-`N=12` campaign value, `RCLE - VALIDITY-ONLY`.

This is a family-ending assay. A complete valid result retains the narrowed
semantic-diversification formulation only if RCLE has material value over
`VALIDITY-ONLY`, every seed has a unique four-rotation anchor bijection, the
full registered anchored-fidelity family passes, and both common/persistent
latent cuts pass. Every other complete valid outcome ends the current
formulation. There is no coefficient, posterior-capacity, latent-alphabet,
threshold, seed-selection, extra-seed, checkpoint, horizon, or repeated-tuning
rescue. An invalid or incomplete panel is not a scientific outcome and returns
to CM for unchanged-science completion.

Even a retained result supports only the exact RCLE package over this validity-
only package on the accepted-roster finite toy. It does not establish
optimizer-independent semantic causality and does not activate a second
surface, continuous-control experiment, simulator, UAV, or flight claim.

## Five-line science card

- **Question.** Does RCLE's paired latent/rotation identity score contribute
  material held-out roster value beyond the generic validity pressure in an
  equally scaled actor-facing `V` signal?
- **Treatment.** Fresh-from-initialization revision-04 `RCLE`, with
  `B_RCLE = V[1 + log q(Z|K*)/log 4]` and the exact frozen revision-04 learning
  and evaluation law.
- **Comparator.** `VALIDITY-ONLY`, identical wherever meanings match, but with
  `B_VALID=V`; this additional auxiliary directly uses only validity, while the
  complete coefficient retains the same task reward and `(N,Z)` baseline as
  RCLE.
- **Observable.** The sole primary contrast is paired frozen `N=12` four-probe
  campaign value. Retention additionally requires the RCLE-only split-sample
  four-rotation codebook, all 12 anchored-fidelity bounds, and both revision-04
  functional-cut bounds.
- **Strongest alternative and ceiling.** The arms still differ in realized
  score sign, variance, gradient alignment, clipping, and Adam trajectory, so a
  positive identifies the exact package contrast only, not semantic identity
  as an optimizer-independent cause.

## 1. Provenance, frozen predecessor, and isolation

The exact predecessor is
`RCLE-B1-SCIENCE-20260813-04`, defined in
`docs/research/candidates/roster_consistent_latent_exploration/RCLE_B1_SCIENCE_CARD.md`.
Its complete result and same-conversation Pro convergence are recorded in
`RCLE_B1_R04_COMPLETE_RESULT_INTAKE.md` and
`RCLE_B1_R04_EXTERNAL_PRO_RESULT_CONVERGENCE_INTAKE.md` in the same directory.
Those records motivate this one comparator and its family-ending outcome law;
they contribute no stochastic object or observation to B2.

Revision 04 is complete and immutable. B2 must not rerun, resume, extend,
reanalyze, select from, or initialize from any revision-04 seed, roster,
latent, action uniform, model, posterior, baseline, checkpoint, anchor,
evaluation campaign, cut, or result coordinate. Source patterns may be adapted
by CM, but B2 owns a new exact revision namespace and the fresh seed list in
Section 6. No other direction's hypothesis, data, threshold, implementation,
or provider answer enters this object.

The motivating source claims and their limits remain exactly those in revision
04 Section 1. They motivate a persistent common latent and parameter sharing;
they provide no B2 efficacy evidence.

The existing RCLE Pro conversation returned `REVISION_REQUIRED` for B2
revision 01 with exactly two defects: it distinguished an identity-free
auxiliary imprecisely from the full shared actor coefficient, and it did not
partition invalid/conformance failures from valid scientific retention-gate
failures literally enough. Revision 02 incorporates only those two prospective
repairs. It changes no arm, DGP, stochastic coordinate, seed, coefficient,
threshold, count, inference model, family-ending rule, or claim ceiling.

## 2. Exact accepted-roster host and information boundary

B2 preserves the revision-04 host without change. Training sizes are
`N in {4,8}`, equally weighted by episodes and optimizer updates. Every learned
object is frozen before evaluation at `N in {4,8,12}`, so `N=12` remains held
out from training.

For each campaign or training block, draw

\[
\Xi\sim\operatorname{Uniform}[0.3,0.7],
\qquad
X_i\mid\Xi=\xi\stackrel{\rm iid}{\sim}
\operatorname{Beta}(8\xi,8(1-\xi)).
\]

Retain the sampled `Xi` while rejection-resampling only `X_1:N`. Compute

\[
\mu_N=N^{-1}\sum_iX_i
\]

once on the accepted canonical roster, and define

\[
B_i=\begin{cases}
0,&X_i<\mu_N/2,\\
1,&\mu_N/2\le X_i<\mu_N,\\
2,&\mu_N\le X_i<(1+\mu_N)/2,\\
3,&X_i\ge(1+\mu_N)/2.
\end{cases}
\]

Accept exactly when no bin contains more than half the roster. More than 4,096
candidate draws for one retained `Xi` makes the run incomplete; it never
redraws `Xi` or weakens acceptance. Independently permute storage rows after
acceptance while carrying the cached `mu_N` and bins; row order is never an
input.

At the two decisions, agent `i` receives only `X_i`, public normalized mean
`mu_N`, phase, the episode-common `Z in {0,1,2,3}`, and its own first action at
phase two. It receives no `N`, raw sum, identity, slot, rank, roster tensor,
padding or mask count, other agent data, bin, rotation, validity, winning
rotation, hidden lock, reward, posterior state, seed, or arm label. The actor is
decentralized and factorized conditional on the public mean and common latent.
Centralized training may compute team outcomes and the joint policy score.

Each agent chooses two binary actions, giving

\[
R_i=2A_i^1+A_i^2,\qquad D_i=(R_i-B_i)\bmod4,
\qquad F_k=N^{-1}\sum_i\mathbf1[D_i=k].
\]

Define `V=1[max_k F_k >= 3/4]`. The winning rotation `K*` is unique whenever
`V=1`; invalid episodes have no winning symbol, no tie repair, and no posterior
input. The semantic outcome is `K*` when valid and `bottom` otherwise.

One campaign fixes one accepted roster and an independently sampled hidden
lock `H` uniform on four values. It contains exactly four frozen-parameter
probes, one for each common `Z`, in a fresh random order with independent
action uniforms. There is no update, recurrence, belief, reward input, or state
carry between probes. Probe reward and campaign value are

\[
R=V\mathbf1[K^\star=H],\qquad C=\max_{p=1,\ldots,4}R_p.
\]

Training crosses each accepted roster with all four locks and all four common
latents before one update, with parameters fixed within the block.

## 3. Shared actor, posterior, and work

Both arms use one parameter-shared float64 stochastic actor with exact input

```text
[X_i, mu_N, X_i-mu_N,
 phase_1, phase_2,
 previous_action_available,
 signed_previous_action_or_zero,
 one_hot_latent_0..3]
```

and exact network

```text
Linear(11,32) -> tanh -> Linear(32,32) -> tanh -> Linear(32,2)
```

The temperature-one binary categorical law is sampled in training and frozen
evaluation. There are 1,506 actor scalars and no critic, recurrent state,
per-`N` head, normalization state, greedy evaluation, or checkpoint selection.

Both arms also own a disjoint `4 x 4` posterior-logit table `q_phi(z|K*)`.
Invalid episodes use the fixed posterior `1/4`, create no symbol, and do not
update the table. Both arms compute route entropy, validity, rotations, the
true-label posterior loss, the RCLE semantic score, and all diagnostics. The
comparator's computed semantic score is detached diagnostic work and never
enters its actor target or gradient.

Within each paired seed, corresponding actor tensors and posterior tensors
start byte-identically. All affine actor weights use Xavier-uniform
initialization with tanh gain, all actor biases are zero, and all posterior
logits are zero. Each arm owns its own actor, posterior, Adam states, and
baselines after initialization.

## 4. Treatment and validity-only comparator

### 4.1 `RCLE`

All agents receive the same uniform episode-persistent `Z`. On a valid episode,
define

\[
s_\phi(z,k)=1+\frac{\log q_\phi(z\mid k)}{\log4},\qquad
B_{\rm RCLE}=V s_\phi(Z,K^\star).
\]

Invalid episodes have `B_RCLE=0`. The posterior value used in the actor target
is from the pre-update posterior and is stopped. This is exactly revision-04
RCLE.

### 4.2 `VALIDITY-ONLY`

This arm receives the same episode-common `Z` and has the same actor input,
posterior, posterior update, task reward, samples, batching, parameters,
computed diagnostics, and work. Its actor auxiliary is exactly

\[
B_{\rm VALID}=V.
\]

`B_VALID` is one on every valid episode and zero otherwise. It has no `K*` or
hidden-lock identity, `Z` identity, posterior probability, or semantic-score
content: it directly reads only `V`. It lies in `[0,1]`, matching RCLE's maximum
positive auxiliary contribution of one under the same coefficient `beta=0.10`.

The complete stopped actor coefficient is nevertheless

\[
R+0.10 B_{\rm VALID}-c_{N,Z},
\]

where the shared task reward remains `R=V 1[K*=H]` and the shared
action-independent baseline remains indexed by the causal pre-action pair
`(N,Z)`. Those paths are identical in RCLE and `VALIDITY-ONLY`; they are not
removed or relabeled. Accordingly, B2 isolates replacement of the additional
generic-validity auxiliary by the exact posterior-shaped semantic auxiliary.
It does not compare RCLE with a complete actor coefficient free of `K*` or `Z`,
and "no identity content" means no direct paired `(Z,K*)` or posterior-semantic
information in `B_VALID`.

The comparator does not match RCLE's negative tail, posterior-confidence
weighting, realized variance, gradient direction, clipping incidence, or Adam
trajectory; those remain in the claim ceiling.

The comparator is not `COMMON-Z`: it deliberately supplies generic
actor-facing validity pressure. It is not a learned critic, reward shaping by
the hidden lock, an anti-information objective, a shuffled label, or a private-
latent arm.

## 5. Exact learning law

Each arm and seed receives exactly 2,000 optimizer updates. One update uses one
accepted roster at each training size, all four hidden locks, and four probes
per lock: 16 episodes at `N=4` and 16 at `N=8`. The arms share addressed
rosters, locks, probe orders, common latents, initial tensors, and action
uniforms wherever their meanings match. Arm divergence never shifts another
address.

For episode `e`, let `log P_e` be the sum of the two selected-action log
probabilities over all agents. For both arms define

\[
T_e=R_e+0.10 B_e,
\]

using the arm's exact `B_e` from Section 4. One complete block minimizes

\[
L_{\rm actor}=-\frac12\sum_{n\in\{4,8\}}\frac1{16}
\sum_{e:N_e=n}\operatorname{sg}(T_e-c_{n,z_e})\log P_e.
\]

There is no extra `1/N` on the joint policy score. Each arm owns
action-independent EMA baseline buckets indexed by causal pre-action `(N,Z)`,
initialized to zero. Immediately after the actor step, each populated bucket is
updated from the same block's four lock episodes by

\[
c_{n,z}\leftarrow0.95c_{n,z}+0.05\,\operatorname{mean}(T_e).
\]

Targets and baselines are stopped. Actor Adam uses learning rate `1e-3`, betas
`(0.9,0.999)`, epsilon `1e-8`, no weight decay, global norm clip `1.0`, and one
step per complete 32-episode block.

After the actor step, each arm updates its own posterior once using the
pre-update table that scored that block:

\[
L_q=-\frac12\sum_{n\in\{4,8\}}\frac1{16}
\sum_{e:N_e=n}V_e\log q_\phi(Z_e\mid K_e^\star).
\]

There is no renormalization by the number of valid episodes. Posterior Adam
uses learning rate `1e-2`, the same betas and epsilon, no weight decay, global
norm clip `1.0`, and one step per complete block. Actor update precedes
posterior update; the baseline update occurs after the actor step and before
the next block. There is no replay, validation tuning, early stop, curriculum,
sweep, or selected checkpoint. The only evaluable checkpoint is immediately
after update 2,000.

## 6. Fresh stochastic coordinates and activity boundary

The paired algorithm seeds are prospectively fixed as

```text
[2371,2473,2591,2683,2791,2903,3011,3121,3251,3371,3491,3613]
```

They do not overlap revision 04. The revision string and a versioned B2 address
schema form a new RNG root. Separately addressed PCG64 namespaces cover `Xi`,
roster proposals, row permutation, hidden lock, common latent, probe order,
both action phases, initialization, optimizer/evaluation coordinates, and both
functional cuts. Rejection, arm divergence, or a different action never shifts
another matched address. No revision-04 random value, checkpoint, baseline,
posterior, anchor, or evaluation object may initialize or populate B2.

Question-relevant scientific activity begins at the earliest materialization
or inspection of any registered B2 stochastic roster proposal, accepted
roster, latent, action, training, posterior-training, calibration, validation,
ordinary-evaluation, or cut object, or at the first actor or posterior update,
whichever occurs first. Deterministic source parsing, algebra on hand-specified
nonrandom fixtures, and static shape or information-boundary checks remain
preactivity. Discarding a stochastic object does not restore preactivity.

No partial seed value, aggregate, checkpoint outcome, map, or cut result may be
interpreted, exposed for selection, or used to alter the frozen object. Seed
packets may be installed atomically for resumability, but scientific analysis
requires the complete 12-seed panel.

## 7. Evaluation and registered diagnostics

Every final actor and posterior is frozen. Each seed and arm receives 2,048
fresh campaigns at each `N in {4,8,12}`, exactly 512 per hidden lock. Every
campaign uses all four common latents once. There are no updates, selected
latents, greedy decoding, evaluation-based checkpoint choice, or adaptation.

For each seed, arm, and size, report revision-04 campaign value, per-probe
return, validity, winning agreement, distinct valid rotations, hidden-lock
discovery, permitted-input action sensitivity, route and relative-rotation
histograms, invalid/tie counts, host rejection draws, retained-`Xi` summaries,
posterior diagnostics, exact work counts, and anomalies. Common-latent semantic
diagnostics are explicitly arm-scoped. Only RCLE diagnostics enter the
codebook, fidelity, posterior-restriction, and cut gates.

Within every `N=4` hidden-lock stratum, campaign indices `0..255` are the anchor
half and `256..511` the scoring half. The split is fixed by fresh B2 counter
index before outcomes and consumes no extra episode. For each RCLE seed and
latent, the anchor half chooses

\[
m_{s,z}=\arg\max_k\widehat P_{s,\rm anchor}
(K^\star=k,V=1\mid Z=z,N=4).
\]

A fixed numeric order resolves a tie for descriptive reporting, but any tied
row fails the gate. The four chosen rotations must be a bijection in every
seed. Neither `N=8` nor `N=12` selects or realigns the map.

For every seed, latent, and size, define

\[
U_{s,z,N}=\widehat P_s
(V=1,K^\star=m_{s,z}\mid Z=z,N).
\]

At `N=4`, use only the scoring half; at `N=8,12`, use all campaigns. The 12
registered `(z,N)` across-seed lower bounds preserve revision 04 exactly: a
Bonferroni familywise one-sided 95% family, hence each marginal Student-`t`
bound is `99.583333%` with 11 degrees of freedom, and every lower bound must
exceed `0.70`.

The two revision-04 frozen-checkpoint RCLE-only interventions are preserved:

1. `PRIVATE-LATENT-CUT` replaces trained RCLE's common latent by iid agent
   latents while preserving each one-agent marginal.
2. `TEMPORAL-LATENT-CUT` keeps the first-decision common latent and supplies a
   new common latent at the second decision.

Both cuts use the same fresh accepted rosters, hidden locks, probe indices, and
action uniforms as intact RCLE at all three sizes, changing only the named
latent intervention, exactly as revision 04 did. Only their `N=12` paired
campaign-value losses are inferential gates. They diagnose functional
dependence, not natural mediation.

The scripted roster-adaptive codebook `R_i=(B_i+Z) mod 4` must retain campaign
value one at every size; scripted coherent collapse `R_i=B_i` must retain
expected campaign value one quarter. Before learner activity the deterministic
host certificate must also establish both actions and phases, all locks and
rotations, exact row-permutation invariance, forbidden-input exclusion, and a
nonempty hand-specified accepted panel at every size.

## 8. Sole primary contrast and retention predicates

Seeds, not campaigns, are the independent units. Define the only primary
contrast

\[
\Delta_s=C_{{\rm RCLE},s,N=12}
-C_{{\rm VALIDITY},s,N=12}.
\]

Under the same independent Normal seed-effect model as revision 04, use
one-sided Student-`t` bounds with 11 degrees of freedom. Because there is one
and only one registered primary contrast, its familywise one-sided level is
95% without a three-contrast Bonferroni division. Define:

```text
POS_VALIDITY    iff the one-sided 95% lower bound for Delta exceeds 0.10
NO_MAT_VALIDITY iff the one-sided 95% upper bound for Delta is below 0.05
UNRES_VALIDITY  otherwise
```

No cross-arm or secondary value contrast exists.

Define `UNIQUE_FOUR_ROTATION_BIJECTION_OK` iff every RCLE seed's four `N=4`
anchor rows have unique empirical maxima and the resulting map is a bijection.

Define `FULL_ANCHORED_FIDELITY_OK` iff all 12 registered `(z,N)` lower bounds
in Section 7 exceed `0.70`.

Define `CODEBOOK_SUPPORTED` iff both of those predicates are true.

Define `CUTS_OK` iff the one-sided 95% lower bound across seeds for RCLE intact
minus `PRIVATE-LATENT-CUT` at `N=12` exceeds `0.10` and the corresponding lower
bound for RCLE intact minus `TEMPORAL-LATENT-CUT` exceeds `0.05`.

Define `POSTERIOR_RESTRICTION_OK` iff every RCLE posterior probability and
score is finite, `q` receives `K*` only for `V=1`, invalid episodes have fixed
`q(.|bottom)=1/4`, and invalid episodes provide neither a symbol nor an update.

Define `SUPPORT_HEADROOM_INVARIANCE_OK` iff every deterministic host certificate
in Section 7 passes.

Define `COMPLETENESS_OK` iff both arms have all 12 exact seeds, 2,000 complete
training blocks, every ordinary campaign, every RCLE cut at all three sizes,
finite required outputs, one exact source revision and hyperparameter set, and
no evaluation adaptation, partial-result selection, or leakage.

Define `INVALID_OR_INCOMPLETE` iff any one of the following is true:

- any registered arm, seed, training block, ordinary campaign, or RCLE cut is
  missing;
- any required scientific output is nonfinite;
- the exact source revision, hyperparameter set, DGP, accepted-roster law,
  rejection rule, or fresh-coordinate prohibition is violated;
- any forbidden actor or posterior information path exists;
- `POSTERIOR_RESTRICTION_OK` is false;
- `SUPPORT_HEADROOM_INVARIANCE_OK` is false, including any failure of the
  deterministic host/oracle/headroom/action/lock/rotation/row-invariance/
  information-boundary/nonempty-support gate;
- an evaluation adaptation, checkpoint selection, leakage path, or partial-
  result selection occurs; or
- a resource terminal leaves the exact panel incomplete.

Define `VALID_COMPLETE = not INVALID_OR_INCOMPLETE`.

Define

```text
SCIENTIFIC_RETENTION_GATES_OK =
  UNIQUE_FOUR_ROTATION_BIJECTION_OK and
  FULL_ANCHORED_FIDELITY_OK and
  CUTS_OK
```

Finally define

```text
FAMILY_RETAINED =
  VALID_COMPLETE and
  POS_VALIDITY and
  SCIENTIFIC_RETENTION_GATES_OK
```

These are prospective finite-seed model-based bounds, not distribution-free
guarantees. A nonpassing lower bound is not affirmative evidence of a negative
effect. `UNRES_VALIDITY` is not equivalence or parity.

## 9. Completeness and resource ceiling

The exact registered counts are:

- 1,536,000 two-step training episodes: two arms, 12 seeds, two sizes, 2,000
  updates, and 16 episodes per size/update;
- 589,824 ordinary two-step evaluation episodes: two arms, 12 seeds, three
  sizes, 2,048 campaigns/size, and four probes/campaign; and
- 589,824 RCLE-only cut episodes: two cuts, 12 seeds, three sizes, 2,048
  campaigns/size, and four probes/campaign.

There are 48,000 actor and 48,000 posterior optimizer steps. The inherited
ceiling remains at most 8,000,000 two-step episodes including deterministic
gates and diagnostics, one CPU worker, at most 2 GiB peak memory, and 45 wall
minutes. This is a prospective ceiling, not a runtime claim or scientific stop.
A resource or engineering interruption with an incomplete panel returns to CM
for a semantics-preserving blinded continuation under Root's direction-scoped
lease; it does not select or end the formulation.

## 10. Exhaustive result-blind interpretation

Use `INVALID_OR_INCOMPLETE` and `VALID_COMPLETE` exactly as defined in Section
8. Define `ZERO_LEARNED_VALIDITY` iff `V=0` on every ordinary-evaluation probe
for both learned arms, all 12 seeds, and every `N in {4,8,12}`. Define
`ORACLE_HEADROOM_WITH_ZERO_LEARNED_VALIDITY` iff the scripted oracle passes and
`ZERO_LEARNED_VALIDITY` is true.

Apply this literal precedence:

0. `INVALID_OR_INCOMPLETE` supports no scientific comparison. CM repairs or
   completes the same frozen science. It does not end the formulation.
1. For a complete valid panel,
   `ORACLE_HEADROOM_WITH_ZERO_LEARNED_VALIDITY` means finite-budget learning is
   nonidentified. It is not evidence against representability or persistent
   latents generally, but it ends this current formulation without rescue.
2. If and only if `FAMILY_RETAINED=true`, retain the narrowed RCLE semantic-
   diversification formulation. Report the exact package advantage, unique
   codebook, fidelity family, and functional-cut predicates separately.
3. Else if `POS_VALIDITY=true`, report a bounded positive package contrast
   without family retention and end the formulation. State exactly which
   scientific retention gate failed.
4. Else if `NO_MAT_VALIDITY=true`, report only the directional no-material
   conclusion below and end the formulation.
5. Else report `UNRES_VALIDITY` and end the formulation.

Within item 3, a failed scientific retention gate means only a failure of
`UNIQUE_FOUR_ROTATION_BIJECTION_OK`, `FULL_ANCHORED_FIDELITY_OK`, or `CUTS_OK`.
A posterior-restriction, support/headroom/invariance, information-path,
leakage, finite-output, source, DGP, coordinate, or completeness failure belongs
to item 0 and permits no positive package claim.

In particular:

- `POS_VALIDITY` with a failed scientific retention gate on an otherwise valid
  complete panel is only a bounded package effect and still ends the
  formulation. It supports no four-strategy, semantic-identity, common-
  coupling, or temporal-persistence mechanism claim.
- `NO_MAT_VALIDITY` permits only that the registered upper bound places the
  directional `RCLE - VALIDITY-ONLY` effect below `0.05` on this finite assay.
  RCLE therefore demonstrated no material directional advantage under the
  frozen criterion. This is not equivalence, and a substantially negative
  effect is compatible with the predicate.
- A negative `Delta` may be reported descriptively and still falls under the
  same family-ending rule; no superiority claim is needed to end the object.
- `UNRES_VALIDITY` is unresolved value and still ends the current formulation
  by the prospectively protected one-assay rule.
- A repeated non-bijective RCLE map ends the formulation even if the value
  contrast is positive.
- Failure of a fidelity or cut lower-bound threshold means only that the
  registered criterion was not established; it is not affirmative absence of
  held-out fidelity, common coupling, or temporal persistence.

After any complete valid non-retained result, do not alter the coefficient,
posterior capacity, latent alphabet, validity threshold, seed roster, seed
count, optimizer, work budget, checkpoint, training horizon, host, anchor,
evaluation rule, or inference threshold to rescue the current formulation.

## 11. Claim ceiling and next-decision boundary

The maximum retained-result language is:

> On the frozen accepted-roster relative-role toy, one shared stochastic policy
> trained at `N={4,8}` and evaluated without adaptation at `N=12` obtained a
> material four-probe hidden-lock advantage with the exact RCLE semantic-score
> package over the matched validity-only package, while its four latent values
> formed a unique `N=4`-anchored four-rotation codebook that met the registered
> fidelity and common/persistent-latent functional-cut criteria.

The strongest surviving explanation is posterior-confidence-weighted validity
shaping and optimizer geometry rather than rotation identity itself. RCLE's
posterior-dependent magnitude, negative tail, task-gradient covariance, seed
variance, clipping exposure, and Adam moments can create a useful curriculum or
favor symmetry-breaking basins. Thus the result does not establish rotation
identity as an optimizer-independent cause. It also does not establish
normalization necessity, exact mutual information, arbitrary or continuous
`N`, membership churn, variable `k`, continuous control, second-surface value,
simulator value, UAV value, or flight readiness.

After a complete technically accepted result, this EM performs the frozen
intake and returns the exact result to the existing RCLE ChatGPT External Pro
conversation for result convergence. No new provider identity is permitted.
If `FAMILY_RETAINED=true`, the only scientifically coherent prospective next
discriminator is a newly frozen gradient-geometry-matched nonsemantic control
that directly addresses the remaining optimizer alternative; it is not
authorized here. If the family is not retained, no successor inside the
current formulation is authorized or proposed. No B2 outcome activates a
second surface.

## 12. Current handoff

The exact composite `RCLE-B2-SCIENCE-20260814-02` is frozen and result-blind.
No B2 stochastic object has been materialized or inspected. The existing
dedicated RCLE ChatGPT External Pro conversation returned literal `CLOSED` with
zero science-bearing defects for this exact revision, and this EM accepted the
disposition without changing the composite. The named same-direction CM may now
construct it and, under Root's direction-scoped compute lease, carry it through
the complete frozen discriminator.
