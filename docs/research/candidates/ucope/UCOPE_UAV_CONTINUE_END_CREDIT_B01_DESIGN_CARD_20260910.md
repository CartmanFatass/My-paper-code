Claim under test: separate PPO credit for a renewal's velocity and end/continue choice, with a conditional suffix-return baseline, can improve final native return over trained fixed-short F at the same 2048-episode budget.
Binding MARL structure: (b) temporal abstraction or termination; five partially observed, co-adapting UAVs hold their own velocities for one or two primitive steps and receive a shared native service return.

# UCOPE continue/end credit B01 — design card, 2026-09-10

**DESIGN ONLY / proposed B/EXPLORE. Numerical allowance: zero.** This card
specifies one candidate for a later explicit allocation. It authorizes no
implementation, model load, test, probe, fit, evaluation or launch. The proposed
3300-second envelope below is new requested work, not released historical budget.

## 1. Question, authority and limits

Does learned-credit arm **L**, defined below, exceed a freshly trained **F**
at the final2048 endpoint by more than0.01J? The comparison tests the whole
changed learning package against the attained fixed-short alternative. It
does not identify why the old T lost or isolate any one change inside L.

Current authority is the [Portfolio allocation at main674f246a2](https://github.com/CartmanFatass/My-paper-code/blob/674f246a202eef1467b084fdd25e2eeb531c0b1e/docs/research/portfolio/decisions/2026-09-10-rolling-successor-allocation.md),
§2 UCOPE, and Root's design-only assignment. The immutable Portfolio response
is b4d71be60f789e97bf1f4c7130bb9995fc84f387, UCOPE section; its checked execution
mapping permits one concrete credit-comparison design with zero numerical work.

The existing own-expiry renewal family remains the scope. The decision time,
physical support{1,2}, legal actor information, native reward and host do not
change. Changing the learning law and selecting F as the new object's primary
comparator is object-tier design; it does not rewrite the old T−G primary or
open a new termination family. No Convergence question is required for this
candidate. A later change to decision time or information would need its own
scope assessment; it is not hidden in this proposal.

Preserve8701/8703 final T−G **−0.0433782967180869/+0.00019308516986599905**,
DOWN/WITHIN, and final T−F **−0.03097854039363236/−0.01107321367085382**.
T trails F beyond0.01 at all six panels of those two complete instances, while
8703 T−H is+0.062103492173288755. Heads moved. Training/evaluation variation,
optimization and co-adaptation remain alternatives to any credit explanation.
8702 stays incomplete with an unexplained crash; A01 is a repeated prefix,
neither a cure nor an independent performance sample.

## 2. Exact decision and legal information

At primitive tick t, agent i first updates its private64-unit recurrent state
from the current104-feature local observation, its last sent3-vector and its
remaining-hold counter/4: the existing108-feature actor input. State advances
on every tick, including held ticks. Other agents' hidden states, global critic
input, reward targets and the residual baseline never enter the acting policy.

If its own remaining counter is zero, it samples pre-tanh velocity u_i,t using
the existing private Gaussian stream and sets v_i,t=tanh(u_i,t). The existing
67→32→2 duration head then samples **END_AFTER_ONE** or **CONTINUE_ONE_MORE**
from [current private recurrent output, detached v_i,t]. These labels map to
physical holds1/2. This is a commitment made at renewal, before the first
environment step; it cannot look at the first reward/next observation and then
change its choice. L initially assigns half probability to each label.

Both labels send exactly v_i,t on the first step. At the next tick, END permits
a fresh velocity draw; CONTINUE keeps that stored velocity for the second step
and renews afterward. Held agents receive no new velocity or duration draw.
Timers, last velocity and recurrent history belong to the same fixed UAV slot
throughout its episode; none resets when that agent or a partner renews. Episode
reset starts fresh histories/timers. There is no join/leave/rejoin or roster change.

The source path is `learner.collect_episode` → `policy.sample` →
`HoldState.decide` → native `env.step(sent)` → `team_reward(info)` →
`HoldState.advance`. The environment receives velocities, not duration labels.
Thus a current duration draw first changes a possible action at t+1; its first
native reward r_t cannot depend on that draw given the already sampled velocity
and pre-decision situation. This is a source-grounded ordering assumption,
not an observed credit bug or a claim that later rewards are independent.

For example, a held second step may keep serving nearby users or prolong a poor
velocity while peers move. L can change the probability of taking that second
step; F cannot condition its half/half decision on this history/velocity. The
claimed value must appear in native J against F, not merely baseline prediction
or a changed duration histogram.

## 3. Changed credit law and collected data

Use the unchanged gamma-one native team rewards r_t and complete-episode returns
G_t=sum from k=t to255 of r_k. The global136→128→128→1 critic retains raw G_t
targets and the existing half-weighted MSE. No reward shaping, renewal penalty,
reward-rate conversion, option-length division or terminal bootstrap is added.

The current T compounds velocity and duration densities before PPO clipping.
L instead uses two separately clipped factors. Let S(r,A)=min(rA,
clip(r,0.8,1.2)A). With E=2 episodes/rollout and H=256:

- Velocity ratio rho_v=exp(new velocity logp − recorded old velocity logp).
  Preserve the existing detached standardized A_v=(G_t−V_old−batch mean)/sigma,
  where sigma=population std of all E×H raw G_t−V_old values +1e−8.
  L_v=−sum over episodes,t,agents of renewal_mask×S(rho_v,A_v)/(E×H).
- Duration ratio rho_d=exp(new duration logp − recorded old duration logp).
  Its observed target is the **suffix G_(t+1)=G_t−r_t**, so credit begins where
  the current end/continue choice can first change action. Define
  A_d=[G_(t+1)−V_old−delta_old(h_i,t,v_i,t)]/sigma, detached and fixed for all
  four epochs. Do not separately center, standardize or retune this advantage.
  L_d=−sum of credit_mask×S(rho_d,A_d)/(E×H), coefficient1.

`credit_mask = renewal_mask AND t<255`. The last-tick duration draw remains
part of the execution/RNG law and is counted, but neither possible label has
a visible future action, so that draw gets no duration-policy or residual
regression term. The final velocity still receives its actual r_255 credit.
A two-step hold starting at254 includes r_255 in its duration suffix. Censoring
creates no fictitious second step, termination reward or bootstrap. All held
rows remain in the **primitive-row E×H denominator**; there is no per-option
reward averaging or replicated likelihood for a held action.

The training-only residual baseline delta is a **67→32→1 tanh MLP,2209
parameters**, shared across the five agents, with its final layer initially zero. It takes the recorded
acting recurrent output and sampled tanh velocity, both detached. Its target
at each credit-mask row is detached G_(t+1)−V_old. Fit it by mean MSE over
those eligible rows, weight0.5. It cannot see the selected duration label,
post-action state, realized first reward or future trajectory as input;
those observations are targets only. V_old is the pre-decision global critic
value already collected; it contains no current own-duration choice. This
retains that baseline's global context while allowing a local action-dependent
correction for the conditional duration decision. A poor correction may hurt;
no reduced-variance claim is assumed.

Total L loss is L_v + L_d +0.5 global-value MSE +0.5 residual MSE, entropy0.
Use one existing Adam optimizer, lr3e−4, betas(.9,.999), eps1e−8,
weight_decay0, foreach/fused false, four full-rollout epochs, global gradient
clip0.5 over all trainable parameters. The added regression contributes only
to residual-baseline parameters, not actor features or the global critic.
Both policy terms differentiate through their own current replayed actor/GRU;
duration's sampled velocity remains detached as before. Chunk32 replay retains
the existing recorded detached chunk-start recurrent states and every primitive
observation; it does not reset or splice histories at renewals.

Store old velocity/duration logps separately, V_old, delta_old, renewal/credit
masks, actual reward and the detached acting67-feature baseline input alongside
the existing rollout. Compute G and suffix once after each complete episode.
Freeze old predictions and advantages before all four epochs. Recompute current
policy logps on the stored actions with recurrent replay; train the residual on
stored acting features. There is no second critic rollout, model-based target,
counterfactual environment branch, replay of past runs or update between holds.
The residual is unused in evaluation and adds no acting information.

One residual module and one optimizer belong to the continuous L fit; neither
is reinitialized at a rollout, chunk, renewal or evaluation boundary. The final
L checkpoint must retain actor, global critic and residual state plus actual
configuration/counts; F keeps its existing checkpoint meaning. Final native
evaluation uses only the actor/hold state, with fresh episode recurrence.

Separating PPO clips, changing the baseline and omitting the first insensitive
reward form **one learning package**. The unclipped duration score has zero
conditional expectation against an action-insensitive first reward under the
stated ordering, but clipping, estimated baselines and finite shared-parameter
updates prevent a blanket equivalence/unbiasedness or improvement claim.
Omitting one reward alone may have little effect over256 ticks. The native
L−F result, not this rationale, would decide whether the package merits more work.

## 4. Comparator, endpoint, unit and outcomes

F is freshly trained from the same initial velocity actor/global critic as L,
with the identical initialized2242-parameter duration head **entirely frozen**
at half{1,2}. Its existing source recipe is unchanged: own-expiry law, actor
information, private recurrence, raw G_t critic target, agent-compound PPO,
primitive-row denominator and Adam cadence. It has66311 trainable parameters;
L has70762 including its duration head and residual baseline. F's frozen head
brings its stored actor/critic parameter total to68553. Parameter/gradient
differences are part of the declared package; capacity causality is not claimed.

Reuse attained F's source at c40a4cd66 as the algorithmic reference, not a
historically selected fitted tensor. Both arms train2048 fresh episodes from
scratch; neither is screened or tuned. The proposed unit is **one fresh matched
training pair**, two fits, with common model initialization and exogenous train/
evaluation worlds but private L/F policy draws. Bind a new master only with a
later explicit allocation. Proposed mapping preserves b=100000×master:
common actor/critic b+11, common initial duration head b+12, L residual b+13,
train worlds b+10000+e(e0..2047), final worlds b+20000+e(e0..63), constructor
reset of world0; L train velocity/duration b+41/+42, F b+31/+32, final
L b+72000/+82000+e and F b+32000/+42000+e. No old weights, Adam or RNG state.

Only the final2048 checkpoint is evaluated,64 common worlds per arm, with
separate policy generators and no change to training RNG/weights. Preserve
J=sum_t sum(info['rewards_dict'].values())/256. Primary
**Delta_F=mean_e(J_L,e−J_F,e)**; retain all64 native values/differences,
world IDs, signs and conditional evaluation SE=sample_sd(differences)/sqrt64.
F's known host observation, action, information and native-reward baseline
match; training budget matches. The omitted interim panels reduce evaluation
exposure only. All raw training outcomes remain, without mandatory new plots.

G, H, old T and interim evaluations are not arms/panels in this proposal.
Consequently it supports no L−G, L−H, best-checkpoint, pure credit-component,
stable superiority or transfer claim. Old G/H findings remain historical.
No new oracle, upper-bound search or baseline qualification run is required.

**MEI: absolute0.01J**, retaining the host's declared useful-effect scale for
the added learning work. Headroom: no tuned same-information current-host
record; F is an attained legal alternative, not a known optimum. Recasts1.

| Unrounded final Delta_F | Proposed B reading and interpretation |
| --- | --- |
| >+0.01 | One favorable changed-package observation against F; consider a separately allocated independent follow-up, not stable superiority or a diagnosed repair. |
| −0.01≤Delta_F≤+0.01 | No demonstrated point gain at the chosen scale; not equivalence. Recommend ending unchanged L spending unless a new concrete question is selected. |
| <−0.01 | Adverse package evidence against F on this instance; recommend ending unchanged L spending. Do not close the family or invent a cause. |

All outcomes and incomplete attempts remain. A missing primary limits the
dependent comparison; no historical F is imputed and no replacement follows.
No result automatically grants another pair. Design-stage forecast
P(Delta_F>0.01)=0.25, reflecting persistent old T/F losses and the untested
credit rationale; retain this forecast if the unchanged design is later
selected, score by Brier, and record any prospective revision. Owner prediction
not taken (unattended). No forecast is a success condition or allocation.

## 5. Work and cost proposal — no numerical allowance released

One matched pair × two arms ×2048×256 = **1048576 train team steps**;
two arms ×64×256 = **32768 eval steps**, **1081344 total native steps**.
Each fit has1024 two-episode rollouts ×4 epochs =4096 Adam calls; total8192.
Acting/eval GRU rows total5406720; four-epoch replay rows total20971520.
Counts are static configuration arithmetic, not new measurements.

For each fit, training renewals span1310720..2621440 and final-eval renewals
40960..81920. L's non-censored duration-credit rows span1310720..2611200.
Existing duration-head dense forward MACs/row=2208; F forward rows are
6×train renewals +2×eval renewals. L needs2×train draws +4×credit rows
+2×eval draws. The added residual needs one old prediction plus four
regressions: **5×credit rows =6553600..13056000 forward rows**,2176 dense
forward MACs/row, plus its backward/Adam work. No enumeration, optimizer search,
nested candidate trajectories or extra learned comparator is hidden here.

Per-fit native workload is524288 training +16384 final-eval steps. Complete
cost must include initialization, collection, recurrent replay, all policy/
value/residual loss work, Adam, final evaluation and publication. Known same-host
CPU FP32/thread1 references:8703 T743.3080151620088s, F776.6612845610362s
(both2048 training with three192-episode-total panels);8701 T729.136335030s,
F708.723448782s. Those nested fit times are components of their recorded complete
outer costs, not new whole-run guarantees. The proposed F has128 fewer evaluations;
do not scale all historical wall by an environment-step ratio. L's added baseline
and separated backward/clip work have **unknown seconds**. No pilot is selected
to price that term, and no unchanged-triple timing is claimed as L's forecast.

Request, for explicit later selection: **L≤1800s complete fit; F≤1200s complete
fit; ≤3000s summed scientific work +≤300s all additional runtime support,
including source checks, preparation, Monitor work, collection, analysis,
publication and closeout; ≤3300s complete**. These unequal per-arm caps are
proposed finite spending limits informed by the attained F wall and L's additional
work, not measured projections, inherited5400s, or transferable savings.
Retain each whole-arm bill and the whole-study support bill; unknowns stay unknown.
Use one sequential L then F study if later allocated; failure stops the dependent
comparison, with no retry/fourth fit/automatic successor or migrated live process.

## 6. Future implementation boundary and scientific grounding

**Engineering Scope§4: none newly needed.** The2209-parameter residual is an
ordinary learner component, not a framework, extra simulator, service or oracle.
No implementation or check occurs now. If later allocated, the concise L0 task
is to add this one L/F route in the existing UCOPE checkout and retain F/old
routes; affected read-only entry points now are `policy.joint_terms`,
`learner.collect_episode`, `learner.update` and continuous-study/CLI publication.
Keep learner changes object-local or explicitly opt-in, preserving existing
callers' numerics/RNG/meaning. Source≤2000 new lines, runner≤600, proposed focused
synthetic checks≤15s inside support; no unchanged native smoke or historical replay.
Independent review must inspect the actual future factorization, baseline
information/detachment, masks, censoring and publication before technical acceptance.

Future execution would remain remote-first on hmasd-wsl-node, CPU FP32, one Torch
compute/interop thread, published exact bytes and fresh destination memory
admission adjacent to the invocation. A launch SHA, command, master and actual
handle do not exist for this design. Only an explicit later allocation can
release engineering/numerical work; no further Pro round is a universal B gate.

Scientific-reading use: Foundations§§5–6 and03_HIERARCHY_ASYNC distinguish
termination/hold, recurrent observation and optimizer clocks;04_EMPIRICAL
distinguishes one trained pair from64 evaluations. The resulting design keeps
primitive observation/reward continuity and compares complete learning packages.
It does not replace the native task by an option-level reward rate.

Question-driven local retrieval checked the formal190-record catalog, then
three actual source JSONs. UTE (VS-0005,p3 kid37,p4 kid84) supports action/extension
factorization and cautions that decomposed learning can still be suboptimal;
it does not establish this PPO change's benefit. ACAC (MARL-0449,p3 kids42/56)
supports agent-owned history/termination distinctions; its macro-observation,
attention-critic and modified-GAE method is not imported into this primitive
recurrent Monte Carlo learner. Asynchronous Credit Assignment (MARL-0530,p3
kids89–112) distinguishes continued from restarted actions; its virtual proxies
are not a required correction here. The [design intake](UCOPE_UAV_CONTINUE_END_CREDIT_B01_DESIGN_INTAKE_20260910.md)
records verified identities, coverage limits, concrete uses and recommendation.
No novelty or broad causal claim follows from these sources.

Design version recorded at **2026-09-10T23:47:43.011889+00:00**. This freezes the returned proposal only; no numerical master/source/command or spending authorization is created.
