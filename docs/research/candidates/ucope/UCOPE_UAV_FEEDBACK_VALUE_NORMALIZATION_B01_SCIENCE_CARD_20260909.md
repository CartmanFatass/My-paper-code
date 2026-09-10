Claim under test: training-only cumulative scalar value-target normalization improves the legal feedback learner's sampled native team return over its raw-target version by more than 0.01 on one fresh matched learning instance.
Binding MARL structure: (c) multi-agent credit assignment; one team-return critic supplies detached advantages to five private recurrent actors whose co-adapting policies change the training distribution.

# UCOPE UAV feedback value normalization B01 — science card, 2026-09-09

## 1. Question, selection and authority

**UCOPE-UAV-FEEDBACK-VALUE-NORMALIZATION-B01**, selector
**feedback_value_normalization_b01**, **B/EXPLORE**, master **8501**.
Does one specified critic-target training change improve legal every-step
feedback at the existing native budget? Compare **G_normalized, G_raw and H**;
the primary is **G_normalized−G_raw**. This is outcome-informed comparator
development inside the accepted renewal family, **recasts: 1**. It does not
test renewal, mean execution, or paid information.

The [accepted Convergence intake §3](UCOPE_POST_MEAN_VELOCITY_B01_CONVERGENCE_INTAKE_20260909.md#3-selected-future-scope-implementation-is-not-allocated)
and full response at **18356085f60fab3bb0d9e092c50bfcc5005f907f** select this
question. The [special validity review §2.1/§4](../../portfolio/pro_packets/20260909_foundations_special_review/archive/RESPONSE.md)
retains it. Root's **2026-09-09 preparation assignment** authorizes this concrete
card and ordinary object choices only: **zero runtime implementation and zero
result-bearing invocation in this batch**. A later concrete Root assignment
controls implementation/execution; the following bounds are not a released run.

P85 remains COMPLETE/WITHIN, mean F−G **−0.008350131013904307** with all four
learned-mode hover losses and both mean−sampled losses. Those facts motivate
testing a different training intervention without identifying their cause.
P83/P84's sampled F−G UPs and every original primary/loss remain valid and
separate. No further mean-execution comparison is selected.

## 2. Learners and preserved native boundary

Both fitted arms use accepted UCOPE source **52bf50a089d3389d9fada0b531e4f4e56e83f9b8**:
private 108-input actor, Linear64/tanh/GRU64, Gaussian mean/log_std and
separate 136-input centralized MLP critic (128/128). Each fit has **32134
actor + 34177 critic = 66311 trainable parameters**; both have no duration
head. All five velocities are available every primitive step, including zero
and repetition. Each actor uses its own observation/history; the critic's
global predecision input never enters the actor.

Retain `make_real` and `actor_features/critic_features/team_reward` exactly:
five fixed UAVs, 50 users, area1000, height50–150, max speed30, time step1,
256 steps, uniform users/free-space channel, native default reward and action
scaling. Private feature layout still contains previous sent velocity and
remaining/4; remaining is zero for these stepwise policies. Per-agent GRU
state, previous command and episode state reset between episodes. No roster
change, sensor, fee, hold restriction, team barrier or information privilege.

Both train and evaluate **sampled** velocities:
`u=mu+exp(clamp(log_std,-5,2))*epsilon; action=tanh(u)`.
Keep agent-compound likelihood/clipping, all-primitive-row denominator,
two complete episodes per rollout, chunk32, four full-rollout PPO epochs,
gamma1/no terminal bootstrap, existing detached scalar advantage normalization,
Adam lr0.0003/betas(.9,.999)/eps1e-8/zero weight decay/amsgrad false/
foreach false/fused false, PPO clip0.2, value coefficient0.5,
joint actor/critic gradient clip0.5 and explicit entropy coefficient0.
No mean mode, initial/intermediate checkpoint evaluation or best-mode selection.

**G_raw** keeps `value_moments=None`, unscaled MC critic regression and the
current raw-unit baseline path. **H** remains untuned zero-velocity with no
learner, optimizer or action draws. Reuse these controls because observation,
legal action, information, objective and training budget match; H is not an
upper reference. No tuned matching host baseline/headroom package is established.

The effect path is **private history → owned velocity → actual movement,
service and subsequent free observations → team native reward →
critic training and later detached advantages/joint clipping → changed
feedback policies and partner co-adaptation → complete sampled native return**.
Normalization changes training coordinates; no causal credit, information
value or remedy is assumed.

## 3. Exact scalar moments and units

Select **cumulative population moments**, equal weight for each complete
team-time MC target, with no EMA, minibatch-only reset, pseudo-count or
per-agent duplication. There is one private moments object for G_normalized;
G_raw/H contribute nothing to it. State: integer **n=0, updates=0** and CPU
FP32 scalar tensors **m=0, M2=0**. Scale is **1 while n=0**, otherwise
**s=sqrt(max(M2/n, 1e-8))**, so the standard-deviation floor is **1e-4**.
Variance is population variance, not Bessel corrected.

For each two-episode rollout, form complete FP32
`R[e,t]=sum_{tau=t}^{255} sum_i native_reward[e,tau,i]`, without a bootstrap.
The environment reward and reported J are never normalized. Use this order:

1. Collection stores the critic baseline in raw units:
   **v_raw=m+s*V_normalized(x)** using moments fixed during that rollout.
   G_raw stores V_raw directly. At initialization m=0/s=1 gives matching
   decoded baselines for the matched critic initialization.
2. Form **A_raw=R−stored_v_raw**, then the existing
   **A=(A_raw−mean(A_raw))/(population_std(A_raw)+1e-8)**, detached once
   before all four epochs. Moments do not recompute or re-decode this stored baseline.
3. Merge the **512** detached targets once. For batch mean q and
   **B2=sum_j(R_j−q)^2**, when n=0 set m=q/M2=B2.
   Otherwise, with old n,m,M2, **delta=q−m**, **N=n+512**:
   **m_new=m+delta*512/N** and
   **M2_new=M2+B2+delta*delta*n*512/N**.
   Then n=N (512 on the first merge), updates+=1. Preserve this arithmetic
   order in CPU FP32; no autograd or optimizer state belongs to moments.
4. Fix the updated m,s across four epochs and regress
   **Y=(R−m)/s**, detached, using the unchanged mean squared critic loss.
   The loss is `policy_loss+0.5*value_loss`, with existing joint clipping
   and Adam. No output-layer/bias rescaling or optimizer compensation occurs
   when moments change; decoded future values can therefore change.

Each fit has separate parameters/optimizer/trajectories. The actor's current
surrogate does not receive a derivative through the detached advantage or
critic loss. Critic-target units can affect the shared gradient clip and future
baselines; neither improved critic loss nor nonzero gradients prove native value.
This is **not output-preserving PopArt or an equivalent raw-PPO rewrite**.

Final G_normalized state must be **n=131072, updates=256** after full training.
Freeze all parameters and moments during final evaluation; no evaluation
reward/observation updates them. The existing final checkpoint saves actor,
critic and configuration plus moments **n, updates, mean=m, M2** in their exact
FP32-representable values. The JSON summary also reports derived s and its units;
s is recomputed from n/M2, not independently fitted. G_raw records
`value_moments=null`. These are ordinary final-state outputs, not resume,
replay, provenance guards or new checkpoint-selection machinery.

The arithmetic reference is the existing
[ValueMoments at 7c80750ea7493af2d70d28fe2072e517b6f45e97](https://github.com/CartmanFatass/My-paper-code/blob/7c80750ea7493af2d70d28fe2072e517b6f45e97/experiments/candidates/vsp_c1/native_hold_value_b03/value_normalization.py),
blob **5bb58ac94fda961c4f9cd330e9ed96a15e60d50c**. It is a read-only source
example, not a cross-direction result or accepted new UCOPE implementation.
Use its small arithmetic locally; no cross-direction runtime dependency is needed.

## 4. Fresh pairing, exposure and selected work

Master **8501**, **b=850100000**. New common actor/critic initialization **b+11**;
deep-copy to both real fits before learning. Raw private training velocity/
unused duration generators use **b+21/b+22**; normalized uses **b+31/b+32**.
Continuous private velocity streams persist across that arm's training episodes.
No duration head or duration draw is present.

Common training resets **b+1000+e, e=0..511**. Common final resets
**b+2000+e, e=0..31** for all three outcomes. Raw final velocity generator is
fresh at **b+3000+e**; normalized at **b+5000+e**. The compatible unused duration
domains are b+4000+e and b+6000+e. Never share mutable generators across arms or
episodes. These fresh domains separate this learning instance from P85;
paired resets match exogenous starts, not actions, visitation or trajectories.

Serial scope: normalized training → final checkpoint → 32 sampled normalized
episodes; raw training → final checkpoint → 32 sampled raw episodes → 32 H episodes.
Each fit trains **512×256 = 131072** native steps, **256** two-episode rollouts,
**1024** Adam calls. The independent unit is **one new matched learning instance**;
two fits, 96 final episodes and five agents are not independent treatment replications.

[Machine-generated facts](UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_PROSPECTIVE_FACTS_20260909.json):
`prospective_matched_instances=1; fitted_arms=2; train_steps_per_arm=131072;
Adam_calls_per_arm=1024; trainable_parameters_per_arm=66311; lr=0.0003;
all_actor_critic_parameters_trainable; native_steps=286720;
final_eval_episodes=96; actual_new_scientific_exposure=0; current_invocation_allowance=0`.
Total **1024 training + 96 final episodes, 1120 explicit + 2 constructor resets**.
G_normalized alone merges 256 batches of 512 targets; no F-head work.

Dominant work is **2×512×256 training + 3×32×256 evaluation = 286720 steps**,
and **2×256×4 = 2048 Adam calls**. No nested candidates, search, solver, sweep,
ensemble or repeated checkpoint evaluator. The extra scalar arithmetic is
256 moments merges, 131072 target normalizations and 139264 value decodes.
Focused implementation verification is separate.

## 5. Cost, future node and execution boundary

Per **G_normalized**: startup/imports/common initialization + 131072
collection steps + 1024 Adam epochs + 8192 sampled evaluation steps +
256 moments merges(512 targets each) + target normalization/value decoding +
arm publication. Per **G_raw**: initialization + 131072 collection steps +
1024 Adam epochs + 8192 policy evaluation steps + **8192 H steps** +
complete publication and exit. All required initialization, training, evaluation
and publication belong to the same logical invocation.

Retain **1800 s per complete arm / 3600 s whole invocation through exit**.
Both future arm walls and the scalar overhead are **unknown**; known counts
do not establish affordability or require a timing pilot. P85's measured
331.58 s and nested F174.66877074097283/G-H140.52741507801693 s are
different-work references, not forecasts for this study. A concrete over-cap
problem returns the question and necessary work, not hidden phases or a higher cap.

If subsequently assigned, use configured remote_first **hmasd-wsl-node**,
CPU FP32/one Torch thread, committed/pushed exact source in a detached worktree
under agent-task. Host identity is not in the estimand. Fresh actual-node
canonical admission must show physical/effective memory ≥4 GiB and join
the exact runner with `&&` before scientific roots, RNGs or models. The original
assigned CM owns technical execution/observation and collection.
**This preparation launches nothing and creates no scientific run root.**

## 6. Primary, all-outcome reading and predictions

**J=sum_t sum(info['rewards_dict'].values())/256** over the complete episode;
do not use the adapter scalar that averages again. Primary
**Delta_N=mean_e[J_G_normalized(e)−J_G_raw(e)]** over 32 paired final resets.
Retain all **96 J values**, three means and the three signed paired vectors
(normalized−raw, normalized−H, raw−H), each with conditional evaluation SE
**sample_sd(differences)/sqrt(32)** and positive/negative/zero counts.
Primary depends on both learned outcomes; full completion includes H.
Missing output limits its dependent claim under §11.8.7; no invented H values.

**MEI absolute 0.01** is the existing native task-scale magnitude worth considering
another bounded comparator investment. It is not significance, equivalence or
a repository-wide cutoff. **Tuned same-information/upper-reference headroom absent**;
the ordinary G/H set is reused on matched information, action and budget.

| Complete unrounded primary | Reading and recommendation |
| --- | --- |
| Delta_N > +0.01 | UP: preliminary favorable normalized-feedback package evidence on this instance/budget; consider a separately justified independent follow-up. |
| −0.01 ≤ Delta_N ≤ +0.01 | WITHIN: no demonstrated point gain at the selected scale; prefer no unchanged normalization follow-up from this observation, without claiming equivalence. |
| Delta_N < −0.01 | DOWN: adverse normalized-feedback package evidence; retain the loss and decline unchanged continuation. |

Report distance to the boundaries. Both hover contrasts are coequal native
observations: an improvement over raw G while normalized G still loses to H
is a relative gain with an absolute deficit. Hover gains do not rescue an
adverse primary. No pooled historical F/G primary, best seed/checkpoint/mode,
training-population SD/interval or post-result retuning.

Prospective predictions: **P(Delta_N>0.01)=0.50;
P(mean(G_normalized−H)>0)=0.55; P(mean(G_raw−H)>0)=0.50**.
The concrete value-target path and verified MAPPO source support testing a
change; they supply no UAV success probability. These are modest DM forecasts
amid mixed raw-G/hover history, not confidence levels. Score each event by Brier
loss and retain all outcomes. Owner prediction **not taken (unattended)**.

The narrative is package-level throughout: above MEI gives one favorable
instance, inside shows no selected-scale point gain, and the opposite sign
counts against this particular normalization recipe. Better target fit cannot
replace native return. No normalization-cause, causal-credit, renewal-effect,
paid-information, stable superiority/harm, tuned-competence, transfer or
deployment claim follows. Every future single allocation ends at full intake;
no automatic second instance, retry, replacement master or extra evaluation.

## 7. Engineering scope and bounded acceptance

Engineering scope §4: **none**. Moment scalars and final state are the algorithm's
ordinary data, with existing counts/exposure/final checkpoint outputs.
No new telemetry, replay, guards, registry, scheduler or recovery machinery.
Future research source ≤2000 new lines, runner ≤600; one affected semantic/
primary-output suite **≤300 s**, with independent review of changed units,
training-only updates, pairing, frozen evaluation and result publication.
Reuse trustworthy unchanged environment, reward, actor-information and credit
checks. No scientific diagnostic or profiling invocation is included.

Implementation entry points and the five-item future CM handoff are in
[preparation intake §4](UCOPE_UAV_FEEDBACK_VALUE_NORMALIZATION_B01_PREPARATION_INTAKE_20260909.md#4-implementation-ready-handoff-for-a-later-cm-assignment).
Stop the future single allocation on failed admission, a complete-arm/invocation
cap, nonfinite learning or a concrete reward/information/units/training/primary
defect. Preserve completed narrower facts; missing optional resources alone
does not erase an intact primary. Stop this assignment now at the committed
card/intake/owner evidence. No runtime source or invocation is authorized here.
