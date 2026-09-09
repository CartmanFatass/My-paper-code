Claim under test: repeatedly choosing action-conditioned commitments at each UAV's own expiry improves complete sampled native team return over same-information stepwise recurrent PPO at the fixed real training budget.
Binding MARL structure: (b) temporal abstraction or termination; a fixed partially observed, co-adapting five-UAV team chooses asynchronous one- or four-step commitments while retaining private recurrent histories.

# UCOPE UAV renewal commitment B01 — science card, 2026-09-08

## 1. Authority, question and claim ceiling

Object **UCOPE-UAV-RENEWAL-COMMITMENT-B01**, **B/EXPLORE**. The
[Convergence response at a54cda020bbcdb5a8fefdd5323fcc5221705f9e8](https://github.com/CartmanFatass/My-paper-code/blob/a54cda020bbcdb5a8fefdd5323fcc5221705f9e8/docs/research/candidates/ucope/pro_packets/20260908_post_b04_renewal_convergence/archive/RESPONSE.md)
selects a **RECAST** from opening-only to renewable commitment and exactly one
fresh matched training pair, **master 7301**. The
[intake](UCOPE_POST_B04_RENEWAL_CONVERGENCE_INTAKE_20260908.md) applies that decision.
This card fixes the new scientific scope and engineering acceptance; accepted
implementation and a concrete execution allocation remain subsequent work.
P61's completed allowance is not reused. No prior card or result is amended.

The next observation asks whether this package earns native return over legal
feedback. B04's duration decision saw the processed reset observation only;
it never chose duration from evolved within-episode history. Repeated expiry
exposes the same head to that later history. This source-defined opportunity
justifies one comparison, not a claim that sparse credit caused old losses.
The strongest null is ordinary feedback using the same history and repeating
commands whenever useful. Commitment can instead delay adaptation and amplify
poor motion. Different exposure, optimization, persistence, capacity and partner
co-adaptation prevent an isolated renewal or information-value interpretation.

Preserve separate history: P21 UP +0.0152174206; P24 WITHIN −0.0035067780
with harmful 6902; B02 DOWN −0.026701655118179134 with both T−H negative;
B03 DOWN −0.010093085146628955; B04 WITHIN −0.003948225944122139,
conditional evaluation SE 0.010191826216031805, G−H +0.0238187196536019
and T−H +0.019870493709479763. These are separate objects and fitted histories,
not an additional arm or pooled renewal evidence. The old retained-policy/
root-residual family remains paused. No C, transfer, deployment or lifecycle
conclusion follows from this prospective B.

## 2. Host, ownership, information and renewal law

Reuse the accepted `uav_motion_prefix_b01/environment.py::make_real` path:
five UAVs, 50 users, uniform 1000 m area, altitude 50–150 m, velocity scale 30,
256 one-second steps, free-space channel, vectorized backend, no shadowing or
FDMA, `paper_reward=False` and the existing default native reward. Keep all
other B04 environment/observation settings, including the 20-user/10-UAV local
limits. No membership change, replacement, paid sensor, count channel or
information charge is introduced.

Each actor keeps its own **108-component input** and private GRU history:
existing local observation, own previous normalized command and own remaining
hold divided by four. Shared weights do not expose another agent's history.
The separate critic keeps the **136-component predecision input**, including
existing global state and established commitments. Diagnostic IDs, other
agents' newly sampled commands and future information never enter actors.

At the start of primitive step t, advance every actor on its current local
observation. A T owner with `remaining == 0` samples velocity latent u and
then d in {1,4}, conditioned on its current recurrent feature and actual
owned `tanh(u)`. Only that owner is duration-eligible. A held owner draws
neither a fresh velocity nor duration. Execute new commands for eligible
owners and the stored commands for held owners, take one common real
environment step, record native reward/observations, then decrement remaining
counts once. Each owner chooses both quantities again at its next expiry.
An expiry never triggers a held teammate's decision. All actors and the critic
process every primitive observation, including all-held rows; no team barrier,
time jump, interruption or hidden-state reset occurs at a renewal.

G is freshly trained ordinary same-information recurrent feedback: every legal
velocity, zero and repetition are available on every primitive step. T/G have
separate trajectories, optimizers and private histories. H remains untuned
zero velocity on the same final reset identities through G's environment.
There is no restricted-feedback null, tuned baseline search or third trained arm.

The native route is: **own expiry amid ongoing team movement → legal current
private history and owned command → persistence versus earlier feedback →
positions/channels/service and later free observations → subsequent owned
decisions → full primitive native reward and masked PPO → complete team return**.
The team remains fixed for each episode; entity identity is not a reusable slot.
Recurrence, commands and timers reset between episodes only.

### Administrative horizon censoring

A selection starting at s retains its original duration label, but executes
only `ell = min(d, 256-s)` steps. It is horizon-censored exactly when
`s+d > 256`. Recompute the likelihood of the selected d, never a relabelled
effective duration. At t255, d1 and d4 both have one physical step remaining,
but their sampled labels stay distinct. No action at t256, terminal bootstrap,
extra reward, command carryover or cross-episode recurrence is introduced.

Retain phase-separated aggregate selected-d4, horizon-censored-hold and
**actually suppressed decision** counts in existing rows/counts/summary.
For a completed segment, suppression is `ell-1`, not three per d4: a d4
at t254 suppresses one remaining decision; at t255 it suppresses none.
Count suppression only on actually executed held primitive steps. Incomplete
attempts retain actual selection/execution counts; do not project unexecuted
holds or declare horizon censoring before an episode actually reaches its horizon.
No complete renewal-event dump or new diagnostic trajectory is needed.

## 3. Architecture, initialization and true PPO credit

Keep B04's 108→64 encoder, GRU-64, 3D Gaussian velocity head, trainable log_std
and separate critic. T retains **Linear(67,32) → tanh → Linear(32,2)** on
`[private recurrent64, detached tanh(u)3]`; parameter totals remain
**T 68553, G 66311**, with T's 2242 duration parameters. This is a package
comparison with no added parameters over B04, not capacity matching against G.
Initialize the T head on private seed b+12 with ordinary Linear initialization,
zeroing only final weights/biases so initial duration probabilities are uniform.
Common actor/critic initialization b+11 is preserved exactly between arms.

Sampling, behavior density and PPO recomputation must share the same actual
per-owner renewal mask. The compound eligible-owner density is
`log pi_v(a_i|h_i) + log pi_d(d_i|h_i,a_i)`. Retain the transformed-Gaussian
Jacobian; condition on the **stored detached latent's tanh**, not the current
velocity mean, a new draw, displacement or teammate command. Recomputed
recurrent features and duration parameters retain likelihood gradients.
Evaluate the duration head only on true duration-mask rows; an all-held row
has no fresh actor likelihood. Existing recurrent gradients through held
observations to later eligible decisions remain. No reparameterized gradient
through a new conditioning command is added.

Both arms retain **agent-compound PPO clipping**. Sum eligible owner
surrogates, then average over **all primitive rollout rows**, including
all-held rows. Do not divide by active decisions or add a sparsity multiplier.
Keep detached behavior logp and normalized scalar advantages, full native
undiscounted `R_t=sum_{tau=t}^{255} sum_i r_native(i,tau)`, gamma=1 and no
terminal bootstrap. Intermediate rewards are retained; no option-only return,
new semi-Markov discount clock or credit reweighting is introduced.

Keep predecision critic rows, scalar advantage normalization, two complete
episodes per rollout, recurrent chunk32 with detached stored chunk-start
states, four full-rollout epochs, Adam lr0.0003/betas(.9,.999)/eps1e-8/
weight_decay0/amsgrad false/foreach false/fused false, PPO clip0.2, value
coefficient0.5 and global gradient clip0.5. Explicit entropy coefficient is
zero in both arms; sampling and trainable variance remain. This preserves
the implemented truncated recurrent PPO approximation, not an exact-gradient claim.

## 4. Independent unit, RNG and complete work

One fresh matched training pair **7301**, b=730100000. Common initialization
b+11; T head b+12; training velocity/duration b+21/b+22; training resets
b+1000+e, e0..511; final T/G/H reset b+2000+e and private velocity/duration
b+3000+e/b+4000+e, e0..31. Preserve this law without new draw alignment:
renewal changes T's draw consumption, trajectories and co-adaptation. The
preparation's 215-file current-UCOPE nonreuse check is bounded provenance,
not a global RNG census. Independent training n=1 matched pair; owners,
decisions, rollout chunks and 32 final episodes are not training replicates.

Each learned arm trains **512 complete episodes, 131072 native team steps,
256 two-episode rollouts and 1024 Adam calls**. Evaluate only final
checkpoints, stochastically, on 32 complete matched-reset episodes per T/G/H.
No checkpoint/seed/configuration is selected from evaluation.

Computed complete work: `2*512*256 + 3*32*256 = 286720` native team steps;
`2*256*4 = 2048` Adam calls; 1120 episodes/explicit resets, two constructor
resets and 96 final evaluations. Retain the existing 1600 T/G final t0..4
diagnostic rows. Extra phase-separated renewal counts use the same invocation.
There is no added environment/GRU step, nested candidate, search, trajectory
enumeration, solver, ensemble, replay or learned arm.

T has 163840–655360 owned training renewals and 10240–40960 final renewals.
Head-forward rows are `6*training_renewals + 2*final_renewals` =
**1003520–4014080**, including sample, behavior density and four PPO epochs.
This is **64–256× B04's 15680 rows**. At 2208 dense multiply-adds per row,
forward work is **2215772160–8863088640 multiply-adds**, plus categorical
sampling, activation, backward and optimizer work. These bounds derive from
64–256 renewals per owner episode; they are neither policy search nor a learned
duration prediction. G's owned train-plus-final velocity samples total696320;
T's equal its actual renewals. Report actual counts, not a preferred bound.
The existing [computed preparation facts](UCOPE_POST_B04_RENEWAL_P67_FACTS_20260908.json)
retain the arithmetic; their dated `unselected` status is superseded only by
the present Pro decision, not rewritten retrospectively.

Machine-generated prospective exposure: `training_pairs=1; learned_arms=2;
native_steps=286720; optimizer_steps=2048; final_eval_episodes=96;
lr=0.0003; T_parameters=68553; G_parameters=66311; T_duration_parameters=2242`.
The real learner can move at this nonzero budget; output reports its own
initial/final norms and displacement for common actor, critic, duration, hidden
and final head layers and totals. A zero initial norm has absolute displacement
and undefined relative displacement, not a fabricated epsilon-normalized effect.
No minimum favorable movement is a launch or result requirement.

## 5. Primary, MEI, predictions and all-outcome reading

`J_a(e)=sum_t sum(info['rewards_dict'].values())/256` uses the original native
per-UAV dictionary, not the adapter scalar that averages the sum again.
Primary `Delta=mean_e[J_T(e)-J_G(e)]` over the 32 paired final episodes.
Preserve all 96 J values, signed paired differences, arm means, T−G, T−H and
G−H. Each contrast's conditional evaluation SE is
`sample_sd(paired_episode_differences)/sqrt(32)`, conditional on the fitted
policies. Training-population SD/interval is unavailable at n=1. No old master,
objective, finite-host result or historical aggregate enters this primary.

**MEI: absolute0.01**, the existing one-percentage-point investment scale for
horizon-average native team return. The coverage component0.7/50=0.014 for
one continuously served additional user supplies scale context, not a guaranteed
total-return gain. **Headroom: absent** on this host; there is no upper/tuned
same-information baseline record. Reuse G/H because host, actions, information
and training budget match. G is ordinary feedback, H is untuned; competence is
assessed through the separate G−H contrast rather than assumed.

| Reading | Fixed rule and bounded recommendation |
| --- | --- |
| UP | Delta>+0.01: preliminary favorable renewable-package evidence on this task, fit and budget; consider a separately justified bounded follow-up, without allocating it automatically. |
| WITHIN | −0.01≤Delta≤+0.01: no demonstrated point gain at the selected scale/budget; prefer no unchanged continuation, not equivalence or proof that renewal cannot help. |
| DOWN | Delta<−0.01: adverse native package evidence; drop unchanged continuation from the next default choice. Motion, information or duration diagnostics cannot compensate. |

Use unrounded boundaries and report proximity to the margin with conditional
uncertainty. Weak/negative G−H narrows improvement-over-competent-control wording
without erasing trustworthy T−G. Positive T−H never reverses primary loss.
The contrary observation is failure to earn the native margin, especially a
loss while G also exceeds hover. This tests the bounded investment premise,
not every renewable policy.

Predictions before new output: **WITHIN, probability0.45**; **G−H>0,
probability0.60**. The adverse opening history and strength of ordinary feedback
favor expecting no above-MEI gain; repeated renewal changes enough that neither
sign is strongly predicted. Recent positive G−H supports only a modest generic
prediction. Owner prediction: **not taken (unattended)**. Score both at intake;
neither controls launch or selection. B04's two previously scored predictions
remain historical, not a prediction score for this new object.

How the result will be interpreted: above MEI merits discussion of a separately
bounded follow-up; inside it favors no unchanged continuation; the opposite sign
strengthens adverse package evidence. **Every sign ends this single allocation
at intake.** No automatic second pair, replacement master, retry, extra H or
evaluation, post-result tuning, successor or C consumption is selected. No stable
superiority/harm/equivalence, isolated renewal/conditioning/clipping/entropy effect,
pure-information value, tuned headroom, transfer or deployment follows. This is
outcome-informed exploration, not prospective confirmation of renewal causality.

## 6. Cost, scope and implementation/execution boundaries

Caps: **1800 seconds per complete arm; 3600 seconds through whole publication
and exit**. T carries startup/common initialization; G carries hover and final
publication. Per-arm cost law is initialization +131072 native/recurrent steps
+1024 Adam calls +8192 final learned-policy steps +publication; add8192 H steps
to G and actual renewal-dependent sampling/head/density/backward work to T.
B04 measured T137.6704245s, G139.2941963s and whole277.51s. These are same-loop
references, not a renewal forecast. The head multiplier is not a whole-wall
multiplier; incremental seconds, aggregate CPU and engineering effort are unknown.
A concrete over-cap projection refuses that launch; a cost refusal returns the
question and necessary work, not a timing pilot, substitute host, parallel workaround,
hidden phase or enlarged cap. Preserve late indivisible-publication overruns.

Portable remote-first **CPU FP32, one Torch thread**, using
`.codex/hmasd-compute.toml`'s `hmasd-wsl-node`, configured interpreter and
`agent-task`. Host identity is not the estimand; no device/dtype change follows.
Exact accepted source is committed and pushed before detached execution in an
exact-SHA remote worktree. Fresh actual-node admission must show physical and
effective available memory≥4GiB before scientific roots, models or RNG work.
No launch occurs in the present intake/card assignment. After source acceptance
and a concrete Root execution allocation, the same CM owns staging, bounded
execution, one actual observer, collection and technical acceptance; Root receives
the accepted handle and integrates, and DM intakes every outcome. Observation
transfer follows EXPERIMENT_MONITOR and never relaunches an accepted invocation.

Stop at selected counts/caps, failed admission, nonfinite learning, or a concrete
defect affecting reward, information, density, training, comparison or primary.
Preserve completed endpoints, actual partial counts and failures. A damaged
primary limits its dependent claim; missing optional diagnostics/resource telemetry
does not erase an independently trustworthy native comparison. No unallocated
completion or retry is implied by partial success or engineering repair.

Engineering scope §4: **none**. Ordinary source≤2000 new lines and runner≤600
lines apply; orchestration30% is a review signal. Added validation is **one
affected-directory suite within300s** plus existing independent review of the
changed high-risk behavior and native primary. Reuse unchanged checks. No standalone
smoke, warm-up, profiling, replay, full trajectory dump or cost experiment is selected.

## 7. Original engineering acceptance

Reuse `experiments/candidates/ucope/uav_motion_prefix_b01/{environment,policy,
learner,study}.py`, the existing runner and mirrored test directory. Add the
small named selector **`--pair renewal_b01 --seed 7301`**, with distinct object/
card/config identity and no multi-pair aggregation. Ordinary implementation details
remain CM's; no new framework, moved historical directory or base-environment edit.
The original source surface is accepted B04 `7693b7af6b7d89cdaa028659d606a37dee9eb68e`,
unchanged in the Pro delivery commit. Preserve historical p21/p24/b02/b03/b04 laws
and outputs; a new selector does not grant historical reruns.

Acceptance covers the connected collector/sampler/timer change: heterogeneous
own expiries, d1/d4 release times, held teammates getting no draw or likelihood,
all-held rows retaining observations/critic/primitive loss denominator, and
private recurrence continuing across expiries. Check actual stored-command
conditioning and behavior/recomputed compound density under the same owner masks,
including gradients to eligible head/recurrent features and no action reparameterization.
Check t254/t255 selected labels, physical truncation, no post-terminal work and
phase-separated actual suppression/censor counts, including partial-attempt semantics.

Within that same focused suite, use the existing short synthetic fixture to
check the changed real learner/collector/plumbing and final native-sum primary,
all three contrasts, original RNG/reset/checkpoint identities, counts and new
config labels. Reject a wrong real master or multi-pair aggregate before native
work; retain historical selector behavior. No synthetic check is a scientific
UAV observation. Independent review inspects these original acceptance conditions;
it does not commission another scientific invocation or impose a stronger claim.
Return credible focused-suite/review evidence, the complete diff, exact committed
source and any concrete semantic/verification-budget gap. Source acceptance
is a technical finding; it is not a favorable scientific result.

## 8. P69 accepted source and execution readiness — 2026-09-08

Original §§1–7 remain frozen at
`ec82119adb83044ac9eff346a4779d3aceffa334`. The P69 implementation/check/review
phase accepts source **`a453447cb011d50c6bb63ed7fc40180134a914b5`**, tree
`e2372f46fcf50ad10eddb04f3e30aafc288651b3`, under that unchanged contract.
The [CM technical record](UCOPE_UAV_RENEWAL_COMMITMENT_B01_TECHNICAL_ACCEPTANCE_20260908.md)
is corrected at `d4f32a1d8e1d339bbdcaf394259346c4b52372b7`; the
[DM source intake](UCOPE_UAV_RENEWAL_COMMITMENT_B01_P69_IMPLEMENTATION_INTAKE_20260908.md#3-completed-source-phase-and-acceptance-evidence)
records the full diff, raw receipts and original rule applied.

One exact-source remote affected-directory suite: 81 passed, 3.97s complete
wall of 300s allowed; independent review found no material gap. Scope §4 none.
Scientific staging, admission, invocation and real 7301 output are all zero
in P69. Native return and complete-invocation timing remain unmeasured; the
§5 predictions remain pending.
Source acceptance does not select a favorable result or another object.
The same CM's scientific execution requires Root's concrete allocation and
the original §6 admission/caps/stop rules. No original budget, contrast,
information/RNG law, all-outcome branch or historical route is changed.
