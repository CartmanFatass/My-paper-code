Claim under test: an opening-duration policy conditioned on its owning UAV's just-sampled command improves complete sampled native team return over same-information primitive-step recurrent PPO at the fixed real training budget.
Binding MARL structure: (b) temporal abstraction or termination; five partially observed co-adapting UAVs choose one opening commitment of one or four primitive steps while retaining their private recurrent histories.

# UCOPE UAV motion prefix B04 — science card, 2026-09-08

## 1. Authority and bounded question

Object **UCOPE-UAV-MOTION-PREFIX-B04**, **B/EXPLORE**. [P61](../../portfolio/handoffs/2026-09-08-p61-ucope-post-b03-direction-choice.md)
and [Convergence at immutable 475f4452177a98e20fb4c0aedf31a89aee4d8912](https://github.com/CartmanFatass/My-paper-code/blob/475f4452177a98e20fb4c0aedf31a89aee4d8912/docs/research/candidates/ucope/pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md)
select exactly one action-conditioned opening comparison, master7201. The
[intake](UCOPE_POST_B03_CONVERGENCE_INTAKE_20260908.md) applies the direction-tier
CONTINUE and records its narrow margin over retaining no successor. The selected
question is performance of this package against legal ordinary feedback, not
attribution of old losses or the effect of conditioning alone.

Prior support: P21 mean+0.0152174206, preliminary UP with conditional uncertainty.
Prior contradiction: B02 mean−0.0267016551 with both T−H negative, P24's6902
native harm, then B03 T−G−0.010093085146628955 despite positive G−H+0.0475679623
and T−H+0.0374748772. B03's one pair and conditional SE0.0085061383 limit its
near-boundary DOWN. These objects remain distinct and are not pooled.

The current independent head samples velocity first but ignores that actual
command when choosing duration. This is a source fact, not a defect diagnosis.
Conditioning could make persistence depend usefully on the owned command, or
could add capacity without beating ordinary feedback. The verified UTE retrieval
in [P61 preparation §3](UCOPE_POST_B03_CONVERGENCE_PREPARATION_INTAKE_20260908.md)
motivates state-and-selected-action extension, with single-agent Q-learning
evidence only; no ensemble or search is adopted.

## 2. Preserved host, ownership, information and native path

Reuse [B03 card §2](UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md#2-preserved-host-information-action-and-credit)
and accepted code `70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44` for the existing
fixed-five-UAV task: 50 users, uniform1000m layout, altitude50–150m, existing
velocity scale30, 256 one-second steps, free-space channel, no shadowing/FDMA,
vectorized backend, unchanged observation limits and default native reward.
There is no sensing fee, count feature, membership change or replacement.

Each actor receives its complete own108-component input, including existing
local observation and own command/hold history. The separate critic keeps its
136-component predecision input. Global diagnostic state, other UAV commands
and future information never enter actors. Each UAV's own present sampled
normalized command is available for its duration choice within the same t0
decision; it is not a new environmental observation.

At t0, T chooses velocity and duration1 or4. A four-step choice repeats the
command through t3 and releases at t4; a one-step choice permits a fresh velocity
at t1. Every agent observes, updates recurrence and receives native reward on
every primitive step, including holds. All agents use ordinary feedback by t4.
No later duration choice, interruption or new clock is selected. G can choose
every legal velocity on every step, including zero or repeating a command, with
the same free local information. T/G have separate fitted policies, optimizers,
histories and on-policy trajectories. H is unchanged untuned zero-velocity control
on matched final reset identities, evaluated through G's environment.

Local history → owned sampled command → conditional duration → actual held or
feedback motion → position/channel/service and later free local observations →
private recurrence and legal action → complete native team reward → PPO credit
→ fitted native service is the tested route. Direct service, geometry, added
capacity, persistence and partner co-adaptation remain alternatives to any
information explanation. Larger movement or information diagnostics are not
substitute endpoints or evidence of competent action by themselves.

## 3. Selected architecture and true likelihood credit

Retain the shared108→64 encoder, GRU64, 3D Gaussian velocity head and learned
log_std. Replace only T's duration head with **Linear(67,32) → tanh → Linear(32,2)**.
Input is `[recurrent64, tanh(u)3]` from the actual owned sampled latent. Initialize
the added head on private substream **b+12**, b=100000×7201, using ordinary Linear
initialization; zero only its final layer weights/biases so opening probabilities
start uniform for every command. Preserve the common actor/critic initialization
at b+11 exactly between T/G and keep action sampling streams untouched. Do not
zero both layers. New T totals68553 parameters, G66311; the additional2112 over
old T belong to this package, not a capacity-matched conditioning experiment.

Sample velocity first and conditional duration second. Evaluate the new head
only on actual opening-duration rows. Its input is not the velocity mean, a
fresh draw, later observed displacement, another agent's command or a candidate
search. In behavior density and PPO recomputation, the true opening log density
is `log pi_v(v_i|h_i) + log pi_d(d_i|h_i,v_i)`. Retain the tanh-Gaussian Jacobian.
Recompute the condition from the **stored detached latent** and detach its tanh
value; recurrent features and duration parameters retain likelihood gradients.
No reparameterized gradient through a new conditioning action enters this update.

Both arms retain **agent-compound clipping**: one owner's eligible velocity and
opening-duration densities form one ratio; later ordinary rows contain velocity
only; held rows have no fresh action/credit. Sum eligible agent surrogate terms
then average all primitive rollout rows, including all-held rows. Old logp and
the normalized scalar advantages remain detached; do not divide by five or by
active count. Sparse opening credit is not compensated with extra samples.

Retain full undiscounted native returns-to-go `R_t=sum_{tau=t}^{255} sum_i r_i,tau`,
gamma1, no terminal bootstrap, unchanged predecision critic and scalar advantage
normalization, two complete episodes/rollout, recurrent chunk32, four full-rollout
epochs, Adam lr0.0003/betas(.9,.999)/eps1e-8/weight_decay0/amsgrad false/foreach
false/fused false, PPO clip.2, value coefficient.5 and global gradient clip.5.
Both arms keep explicit entropy coefficient0.0; stochastic sampling and trainable
variance stay active. Unnormalized training return and horizon-average final J
retain their distinct existing roles. Historical p21/p24/b02/b03 routes remain.

## 4. Independent unit, RNG and complete exposure

One fresh matched training pair: **master7201**, b=720100000. The preparation's
bounded current-UCOPE search over273 files found no earlier7201 use; this is not
a global RNG census. Common initialization b+11; T head-only initialization b+12;
training velocity b+21; training duration b+22; training resets b+1000+e for
e0..511; final T/G/H reset b+2000+e and private velocity/duration b+3000+e/b+4000+e
for e0..31. Common initialization and matched reset/stream laws do not imply
identical trajectories or action-draw consumption after T holds. Preserve that
law; no new draw alignment is selected.

Each learned arm: **512 complete256-step training episodes,131072 team steps,
256 two-episode rollouts and1024 Adam calls**. Only each final checkpoint is
evaluated, stochastically,32 complete episodes per T/G/H. No checkpoint/seed
selection on evaluation. Independent training **n=1 matched pair**; agents,
openings, rollout chunks and final episodes add no independent training units.

Dominant complete work is `2*512*256 + 3*32*256 = 286720` native team steps;
`2*256*4 = 2048` Adam calls;1120 episodes/explicit resets,2 constructor resets,
96 final episodes and1600 existing diagnostic frames. Only T has512 team
opening decisions/2560 owned training-duration samples. Named new-head forward
rows total15680:2560 sampling +2560 behavior-density +10240 recomputation +160
final sampling +160 final density. At2208 dense multiply-adds/row,34,621,440
forward multiply-adds, plus unmeasured backward/activation/Adam work. No added
environment/GRU forward, candidate, trajectory, replay, ensemble or learned arm.
[Computed facts](UCOPE_UAV_MOTION_PREFIX_B04_PREPARATION_FACTS_20260908.json)
give units and separate selected exposure from zero exposure at preparation.

Future output reports actual train/eval/Adam counts, lr, parameter counts,
initial/final norms and movement for common actor, critic, duration and total.
The new head's hidden and zero-initialized final layer are identifiable in the
existing exposure summary; zero-norm groups use absolute displacement, not an
epsilon-divided number presented as meaningful relative movement. These are
observations, not minimum-movement or all-heads-positive launch/result gates.

## 5. Primary, MEI, predictions and interpretation

`J_a(e) = sum_t sum(info['rewards_dict'].values()) / 256` uses the original
per-UAV native dictionary, not the adapter scalar that averages again.
Primary `Delta=mean_e(J_T(e)-J_G(e))` over32 paired final episodes of7201.
Preserve all96 J values, all signed episode differences, three arm means,
T−G, T−H and G−H. Each paired contrast has conditional evaluation SE
`sample_sd(differences)/sqrt(32)`. No training-population SD/interval is
estimable from one trained pair; no multi-pair aggregate or historical pooling.

**MEI: absolute0.01** in time-average native team return, retaining the one
percentage point task-scale investment rationale. The coverage component for
one additional continuously served user is.7/50=.014; this is not a guaranteed
total-reward change or measured headroom. There is no upper/tuned same-information
headroom record on this host. Reuse G/H because task, information, action and
budget match; G is the specified ordinary-feedback learner, H is untuned.

| Reading | Fixed rule and bounded recommendation |
| --- | --- |
| UP | Delta>.01: preliminary favorable package evidence on this task/fit; consider a separately justified bounded follow-up without allocating it automatically. |
| WITHIN | -.01<=Delta<=.01: no demonstrated point gain at the selected scale/budget; prefer no unchanged continuation, not stable equivalence. |
| DOWN | Delta<-.01: adverse native evidence for this package/task/budget; drop unchanged continuation from the default next choice, without a whole-family impossibility claim. |

Apply unrounded boundaries; retain distance to the MEI and conditional uncertainty.
A near-boundary label is not reliable population separation. G−H is assessed,
not assumed: a weak G limits improvement-over-competent-control wording without
erasing trustworthy T−G. Positive T−H never rescues negative T−G. No extra final
evaluation is allocated to resolve a small crossing.

Predictions recorded before B04 output: **WITHIN, probability.50**; **G−H
positive, probability.60**. Owner prediction: **not taken (unattended)**. Sparse
opening credit and the adverse history favor expecting no above-MEI package
gain; B03 supports a modest prediction of positive generic/hover contrast, not
certainty. Score both at intake; neither holds launch.

Above MEI would motivate discussing a new bounded replication; inside it would
favor no unchanged follow-up; opposite sign would strengthen adverse package
evidence. In all cases this allocation ends at intake. No second pair, stable
superiority/harm, conditioning/entropy/clipping causality, pure-information value,
transfer, deployment, C promotion or direction disposition follows. This is
outcome-informed exploratory selection, not independent confirmation of the
conditioning mechanism.

## 6. Cost, engineering scope and stopping boundary

Caps: **1800s per complete learned arm;3600s for the whole pair through
publication and exit**. T carries startup/common initialization; G carries H
and final publication. Cost per arm is initialization +131072 environment/actor
steps +1024 updates +8192 final steps +publication; G adds8192 H steps, T the
new head's actual opening/learning work. Prior B03 T143.6449222s/G139.3128413s/
whole283.51s are same-loop references, not measured B04 predictions. Incremental
seconds and aggregate CPU are unknown. No timing pilot or cap growth follows.

Use portable remote-first **CPU FP32, one Torch thread** on the configured node;
host identity is not the estimand. Accepted source is committed/pushed before
one detached exact-SHA invocation. Fresh actual-node admission must show both
physical and effective available memory≥4GiB before any scientific root/model.
Root launches and observes; the same CM collects/technically accepts; DM intakes
every outcome. Commit identity alone does not change the accepted source surface.

Stop at selected counts/caps, failed admission, nonfinite learning, or a concrete
defect affecting reward, information, action density, training, comparison or
primary measurement. Preserve partial endpoints/overruns. No retry, replacement
master, second pair, extra H completion/evaluation, post-result tuning or automatic
cap increase. A damaged primary limits dependent claims; missing optional telemetry
or diagnostics does not erase an independently trustworthy native comparison.

Engineering scope §4: **none**. Reuse existing learner/metadata/output paths;
source≤2000 new lines, runner≤600 lines and30% orchestration as review signal.
One affected-directory suite≤300s and independent action/credit/native-primary
review are selected. No standalone smoke, warm-up, profile, pilot, replay or
full-array publication. B02's80.578s/60s smoke breach and prior zero-exposure
command failures remain historical. All three CM comparison batches are complete;
no fourth enrollment follows. Source is not accepted or launched by this card.
