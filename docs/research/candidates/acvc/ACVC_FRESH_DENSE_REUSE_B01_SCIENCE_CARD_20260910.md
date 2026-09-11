Claim under test: On one prospectively selected fresh DENSE fit, fixed own-history retracing F improves native team return relative to always-apply C and own-cue dwell.
Binding MARL structure: (d) multi-agent partial observability: each UAV uses its own link history while teammates' simultaneous motions change interference, service and later observations.

# ACVC fresh DENSE reuse B01 — science card

Date: 2026-09-10. **B/EXPLORE; original8921 and separately allocated8931 results complete.**
Section8 records the later Portfolio allocation. The original design-stage statements in
§§1,6–7 below remain historical; §8 supersedes their no-execution boundary prospectively.
The [design intake](ACVC_FRESH_DENSE_REUSE_B01_DESIGN_INTAKE_20260910.md) records the decision;
the [prospective facts](ACVC_FRESH_DENSE_REUSE_B01_PROSPECTIVE_FACTS_20260910.json) contain
tool-computed counts and retained-timing arithmetic. They contain no new empirical outcome.

## 1. Question, authority and scope

Does the fixed F package retain a useful mean advantage over C and the simpler motion-suppression
rule after a prospectively chosen, independently initialized and trained DENSE base?
This addresses the retained-base selection limitation of
[E01 intake §§5–9](ACVC_FIXED_RETRACE_REUSE_E01_INTAKE_20260909.md). One fresh fit with all
three rules has direct decision value; no exact optimum, controller search, tuned upper,
mechanism census or preliminary performance qualification is needed.

The [2026-09-10 Portfolio execution mapping, ACVC](../../portfolio/pro_packets/20260910_next_five_chains/EXECUTION_MAPPING.md#acvc--ordinary-b-fresh-base-design-only)
selects this ordinary-B design only. Its immutable Pro response is commit
`08e989073839fe5f0f91c6a8ad90a399bee37b6c`,
`docs/research/portfolio/pro_packets/20260910_next_five_chains/archive/RESPONSE.md`, ACVC and
cost sections. Root supplied synchronized authoring input
`db1834ebc8b329f3efb2edd7d615faedb2f5939a` on `codex/acvc`.
The finite fitting recipe below is an object-tier selection inside the accepted fixed-rule
question; it does not reopen a family or allocate compute. Ordinary-B §11.4 applies in full.
The E01-only §11.4.1 zero-new-training exception and its 180-second cap do not extend here.

P80's learned T/G package remains ended. There is no T/G fitting, REL comparison, replacement
with retained 8201/8202, best-of-many base/checkpoint selection, transfer claim, C promotion
or formal UAV-validation entry. ACVC remains at recasts: 2 and lowest contention priority;
Root retains Portfolio execution and sequencing.

## 2. Native host, information and learner

Use the accepted `make_real(horizon=256)` native host: five fixed UAVs, 50 users, 256 primitive
steps, area 1000, altitude 50–150, speed 30, time step 1, uniform users, free-space propagation,
20 visible-user slots and 10 UAV slots, shadowing off, paper reward off, FDMA off, bandwidth
20e6, BS power 30, step cache on and vectorized SINR. The implementation source is
`experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` at the authoring input.
Preserve its observation normalization, action clipping and actual-command feedback.

The shared stochastic actor receives only each UAV's 104-dimensional native observation,
its last actual three-dimensional command and remaining duration, giving 108 inputs. Remaining
duration is zero because every primitive step opens a velocity decision. Each UAV has a private
64-dimensional GRU state. The DENSE encoder adds a 108→16 tanh→64 residual to a 108→64 raw
linear map; tanh, GRU(64,64), linear velocity mean(64,3) and learned three-coordinate log standard
deviation follow. There is no duration head or gate. All 34,902 actor parameters are trainable.

The 34,177-parameter critic is a 136→128→128→1 tanh MLP. Its training-only input is the
normalized 116-dimensional global state plus all five actual commands and remaining durations
(20 values). No critic/global state is supplied to actor decisions. Both actor and critic learn
from the sum of the five native agent rewards at each primitive step, without a shaping term.
Report episode sum `S = sum_t sum_i reward[t,i]` and native mean `J = S/256`.

## 3. Exactly one fresh fitting law

Training master **m = 8921** is selected before any new model or native output. Create common
Actor then Critic with `templates(m)` under isolated torch seed `100000*m+11`; construct only
`NativeGeometryActor(common_actor, "DENSE", 100000*m+12)` and use the fresh common critic.
The DENSE raw encoder, GRU, mean and log_std copy this new Actor. The branch hidden weights use
the accepted private uniform ±1/sqrt(108), zero hidden bias and zero final context projection.
Preserve constructor draw order, including the existing overwritten initializations. No REL
model/fit is needed to obtain this DENSE law. Source: MGTAP `geometry.py` and UCOPE `policy.py`.

Fit for **512 complete 256-step episodes**, grouped sequentially into **256 two-episode
rollouts**. Keep a single optimizer for the whole fit. Each rollout uses four full-rollout PPO
epochs, so the fixed endpoint is **1,024 Adam/backward calls** after **131,072 team steps**.
This reuses the accepted native DENSE fitting law, not a universal minimum training budget.

Use UCOPE `collect_episode` with `real=True`, `diagnostics=False`,
`ratio_grouping="agent_compound"`, `value_moments=None`, `renewal=False`,
`duration_support=(1,4)`, `velocity_mode="sampled"`, and actor `duration=None`.
All five agents sample three ordered Normal draws every primitive step, using learned log_std
clamped to [-5,2] and tanh squashing. Always apply the sampled proposal during fitting.
Do not apply F or dwell to training data. Reset private hidden states and command/duration
features each episode; preserve within-episode recurrence and actual sent commands.

Use the existing `returns_to_go`, `clipped_policy_loss` and `update` without changing their
objective: undiscounted Monte Carlo team returns (gamma 1), no bootstrap or GAE, raw critic
units, advantages `(return - stored_value)` standardized with population SD +1e-8 over the
two-episode rollout and detached before all four epochs. Velocity log probabilities include
the existing tanh correction and compound the three coordinates separately for each agent.
Clip each agent's ratio to [.8,1.2], sum the five surrogates, then average over the 512 team
rows. Do not replace this with one joint-five-agent ratio or average away the five-agent sum.
Loss is policy loss +0.5 critic MSE −0.01 mean Gaussian entropy, with entropy summed over
the five agents' three coordinates as in the source helper.

Recurrent replay uses chunk length **32**, detached stored hidden states at chunk starts,
32 time positions ×80 episode/chunk/agent sequences per update, with ordinary in-process
array batching. Each epoch recomputes the full rollout, zeroes gradients, backpropagates,
clips the combined actor/critic gradient norm to 0.5 and steps Adam once. Adam has lr 3e-4,
betas (.9,.999), eps 1e-8, weight_decay 0, amsgrad False, foreach False and fused False.
No value normalization, duration learning, minibatch selection or extra optimizer phase is added.

Training constructor seed is `100000*m+1000`; episode e=0..511 resets with
`100000*m+1000+e`. The constructor's initial unscored reset duplicates the first training
reset, as in the accepted host. One persistent velocity generator seeded `100000*m+21`
advances across all 512 episodes. Preserve the per-episode unused duration-generator seed
`100000*m+4000+e`; duration=None means zero duration draws. Initial seed and all ranges are
expanded in the prospective facts; no RNG has been initialized during design.

Save the final actor and critic after episode 512. Preserve every training episode, each
rollout's four update records, actual counts and actor/critic initial/final norm and displacement.
Evaluate this final checkpoint regardless of its mean training return, apparent learning speed
or base attractiveness. There is no minimum-performance gate, substitute seed, early best
checkpoint, repeated initialization, pilot or train-until-good rule. Nonfinite or broken
training is a technical failure with retained partial facts; a weak intact fit still receives
all three panels. There is no initial-policy panel or claim of improvement over initialization.

## 4. Fixed evaluation and rule binding

After the fit, freeze the final actor and load its checkpoint into three separate model
instances. Evaluate **C, then F, then dwell**, 64 complete episodes each. Critic and optimizer
do not run during evaluation. Use existing `load_base`/`base_architecture` with evaluation
namespace **q = 8922** (construction seed `100000*q+14`). This namespace is not a second fit.
The three environment constructors use `100000*q+60+a`, with a=2,3,4 respectively.
For e=0..63, all arms reset with `100000*q+2000+e`, pairing the initial world. Private proposal
generators use `100000*q+30000+100*a+e`. If the existing helper constructs its unused gate
generator, retain `100000*q+40000+100*a+e`, with zero gate draws and no gate network.

All arms sample proposals and evolve all five private recurrent states on every primitive
step, including overridden proposals. Every arm feeds back its own actual sent commands and
owns its own subsequent observations, binding history and joint trajectory.

| Arm | Executed command |
|---|---|
| C | Always the sampled proposal b. |
| F | `Binding.observe(obs,b)` retrace command on its accepted mask; otherwise b. |
| dwell | Zero xyz on the same predicate evaluated on dwell's own history/proposal; otherwise b. |

Use `experiments/candidates/acvc/native_link_loss_b01/binding.py` unchanged. The preceding
observation's unambiguous lowest-SINR nonpadding user coordinate supplies the anchor; a
saturated preceding list may supply it. A current count of 1–19, anchor absent within the
accepted normalized L-infinity vicinity 2e-6, and positive proposal away-dot are required.
Reset, empty, ambiguous and currently saturated cases do not qualify. F reverses the prior
actual realized displacement, divides by 30 and clips to [-1,1]. Dwell does not borrow F's
mask, event times or dose. C bypasses the cue observer: zero C cue counters are unmeasured
cue incidence, not evidence that no loss occurred.

The causal path is joint motion/interference → own link observation → retained anchor and
proposal → actual command → changed joint geometry/service → future private observations
and native team return. Own-link loss may be a useful handoff rather than global service
failure. Training includes partner co-adaptation; evaluation freezes all parameters, while
teammates still react through their own recurrent observations. Membership and entity identity
are fixed: no join/leave/replacement, censoring or semi-Markov time is introduced.

## 5. Observable, MEI, predictions and reading rule

Retain all **192 evaluation rows** with base, rule, episode/reset key, S and J, plus every
paired contrast vector and cue/opportunity/intervention/distinguishability count. No world is
filtered because it lacks a cue or produces an adverse return. Primaries are **F−C** and
**F−dwell**, separately; dwell−C is secondary. Calculate each mean and sample SD/sqrt(64)
over the 64 paired initial-world episodes. These SEs are conditional on one trained checkpoint
and the prescribed private proposal streams. They do not estimate training-seed uncertainty.

MEI is **0.01 J = 2.56 S**, an absolute practical margin retained for the same native
fixed-package question. It is not a normalized percentage or significance cutoff. The inherited
quarter remains 0.25 S =0.0009765625 J. No tuned same-information baseline/upper headroom
record exists on this native host; F is an attained comparator, not an upper bound. Existing
C and dwell are reused because observation, action, information and final-panel budget match.

Apply this rule independently to each primary and the secondary contrast:

> **UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**, retaining the sign.

DM predictions before any new output: **P(F−C is UP)=.75; P(F−dwell is UP)=.65**. They are
unscored. Owner prediction: **not taken (unattended)**. The complete pattern, including dwell−C
and adverse worlds, informs the next bounded recommendation; positive signs are not required
on every world or every future seed.

Above the MEI against both comparators would support fixed-package reuse on this new fit
and motivate consideration of another bounded independent-fit observation. F above C but
within or below dwell leaves motion suppression competitive. Inside the MEI gives little
observed practical separation at this budget, without proving equivalence. An opposite sign
weighs against the package on this fresh fit and would motivate reconsidering further reuse
investment. All readings retain the old selected-fit support and stopped T/G losses. No
branch launches a successor, diagnoses a pure retrace effect, closes the direction or proves
stable superiority, history necessity, optimality, headroom or transfer.

## 6. Prospective exposure and complete cost

**Current design exposure:** scientific_invocations=0; model_constructions/loads=0;
training/evaluation/native_steps/optimizer_updates=0; tests/profiles/probes=0.
The machine-generated facts record prospective learner mobility: all **69,079** parameters
are unfrozen with nonzero-lr loss-dependent Adam for 1,024 calls. Actual movement relative to
initial scale and actual nonzero training/update/evaluation counts belong in the future
exposure line; no positive displacement or B execution conformance is claimed from authoring.

| Intrinsic algorithm work | Proposed quantity |
|---|---:|
| Independent fits / selected final checkpoints | 1 / 1 |
| Training episodes / native team steps | 512 / 131,072 |
| Training collection actor-agent / critic forwards | 655,360 / 131,072 |
| Adam/backward / recurrent update batch calls | 1,024 / 1,024 |
| Replayed actor-agent steps / critic update rows | 2,621,440 / 524,288 |
| Evaluation panels / episodes / native team steps | 3 / 192 / 49,152 |
| Evaluation actor-agent forwards | 245,760 |
| Total scored episodes / native team steps | 704 / 180,224 |
| Total collection actor-agent forwards | 901,120 |
| Environment constructors / unscored constructor resets | 4 / 4 |
| Fresh DENSE initialization / post-fit loads | 1 / 3 |
| Gate or duration heads / selector or evaluation updates | 0 / 0 |

Dominant factors are `512×256×5` training collection, `256×4` updates each replaying
`2×256×5` agent steps, and `3×64×256×5` evaluation forwards. F/dwell add at most
`2×64×256×5×20×2 = 6,553,600` coordinate-pair checks. These are exposure counts, not a
claim of one Python call per agent. There are no nested candidates, alternate trajectories,
support search, old DENSE/H evaluation panels or separate cost experiments.

Whole cost law is preflight/startup/imports and fresh construction +131,072 training
environment/actor/critic steps +1,024 recurrent replay/backward/Adam updates +three
checkpoint loads/constructors +49,152 evaluation steps and F/dwell checks +publication and
actual process exit +supporting checks/readback. Fixed initialization and exit work are
part of the same complete chain. Per-panel measurements do not reset its budget.

Retained timing inputs are MGTAP P75's accepted 512-episode DENSE fits and E01's complete
panel receipts. The larger historical DENSE-through-exit tail is **180.166 s**; this proxy
deliberately retains old 32-DENSE and 32-H evaluation/publication work that is not part of
the new algorithm. The maxima of the corresponding E01 C/F/dwell windows sum to **39.455 s**.
E01's 81 s conservative whole-task charge minus its six measured windows contributes
**2.579 s** of nonpanel accounting. Thus nominal new process projection is **222.200 s**;
with the proposed 30 s support allowance, nominal complete projection is **252.200 s**.
The facts file preserves exact inputs and arithmetic, not a timing measurement of this fit.
Standalone imports/learner initialization, new trajectories, contention and focused-check
cost remain unmeasured; the residual is not proof that these costs fit.

Proposed numerical limits are **330 s for the entire supervised scientific task** and
**at most 30 s supporting checks/readback**, both inside **360 s complete charged work**.
Nominal margin is 107.800 s. Support includes any future runtime acceptance and numerical
result reduction; ordinary reading, authoring, Git and independent review are not invented
environment exposure. Actual invocation wall, support and complete charge remain separate
from study elapsed time and any available CPU work. No old 89.35 s charge or unused E01
allowance funds this proposal. **Allocated seconds and scientific invocations are both zero.**

## 7. Implementation dependency and stop boundary

The fitting recipe is fully specified; the remaining dependency is a concrete, separate Root
implementation/execution mapping and allocation. Existing MGTAP `runner.py` hardcodes its
two historical masters and REL/DENSE/H study; the E01 script evaluates two retained bases.
Neither is an accepted runner for this one-fit binding. A later small ACVC runner may reuse
MGTAP `geometry.py`, UCOPE policy/learner/environment and the ACVC fixed-rule collector/report;
the candidate entry is `scripts/run_acvc_fresh_dense_reuse_b01.py`. No such source is created,
no launch SHA or accepted handle exists, and this design does not claim execution readiness.

Use the same authoring checkout `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`.
Future execution is one serial, portable native CPU FP32, torch intra/inter-op thread-1 process
via `.codex/hmasd-compute.toml` remote-first route. No device/dtype substitution is proposed.
The later bounded mapping must preserve exact committed/pushed source, detached execution,
fresh actual-node memory admission immediately before initialization/RNG/models, and an
accepted Monitor handle under the current responsibility map. This adds no new Pro gate.

Engineering-scope specification §4: **none needed**. Existing checkpoint, exposure, admission
and detached-task paths suffice; no guard framework, registry, retry system or profiler is
requested. A later source batch remains under 2,000 new research lines, 600 per runner and
the existing cumulative directory-test budget; those limits are not renewed by this card.
Required independent semantic review targets the changed fitting/optimizer, RNG, checkpoint,
private recurrence/command-feedback and primary-reduction boundaries. Reuse accepted checks;
any focused runtime verification must fit the proposed 30 s support allocation if allocated.

Stop on the fixed endpoint after all three panels, actual publication and exit. A hard-cap
exit or damaged training/primary output retains observed counts and trustworthy partial facts;
it is not a negative effect or permission to retry, split a fresh budget, drop a panel or
extend training. A weak but intact fit continues to all panels within the same cap. Missing
optional resource telemetry is recorded as resources_unmeasured; §11.8.7 limits only claims
dependent on damaged measurement. This authoring assignment stops at published design and
Root return, with zero numerical work and no local allocation.

## 8. Prospective execution allocation after complete Pro intake

The [Portfolio decision](../../portfolio/decisions/2026-09-10-acvc-fresh-dense-allocation.md)
records full conformance intake of immutable Pro response
`caf8cf61d92fb3a669f93439a0e2b9967eca943c`. Option A now allocates exactly this study
under AGENTS§4.8; Root accepted the conformance and assigned its complete implementation,
independent review, verification, execution and all-outcome intake to the existing ACVC DM.
This supersedes only the historical design-only/no-allocation statements above. The
scientific recipe, data/RNG, final endpoint, comparator set, predictions and reading rule
remain exactly those selected at28e99edc7. No implementation or process is accepted by Pro.

Allocated limits are **330s whole supervised task**, **30s cumulative runtime support**,
**360s complete charge**. Admission/startup through actual descendant exit stays inside330s;
checks and numerical readback share one30s allowance with the existing directory-test limit.
Unused time cannot enlarge either sublimit. No retry, resumed slice, replacement, extra or
smaller panel, tuning, retained-base substitute or automatic successor is allocated.
A weak intact fit still receives all panels; broken dependent output is a technical limit.
The [execution mapping](../../portfolio/pro_packets/20260910_acvc_fresh_dense_allocation/EXECUTION_MAPPING.md)
supplies the five engineering facts and current DM/Monitor responsibilities. Scope§4:none.

At application publication, source implementation/independent review/runtime checks/launch
are pending, and new scientific exposure remains zero. Actual command, published source SHA,
resource receipt, supervised handle and complete costs belong in the execution/result record.

## 9. Completed observation and accounting boundary

The exact recipe above completed once at source60d42dd739ef125a505772f2b1d698b099b43a16.
The [E0 result](ACVC_FRESH_DENSE_REUSE_B01_RESULT_EVIDENCE_20260910.md) and
[scientific intake](ACVC_FRESH_DENSE_REUSE_B01_INTAKE_20260910.md) retain all512 training
episodes,1024 update records and192 final evaluation rows. F−C +0.1229328560 J and
F−dwell +0.0877164686 J are UP under the unchanged rule; dwell−C +0.0352163875 J is UP.
Both prospective predictions are now scored in the intake; the original probabilities
above remain the pre-output record. Owner prediction was not taken. One fit is not a
training population, and the old retained fits are not pooled into this fresh result.

The native task's conservative charge is172s and measured DM runtime support8.0564878s.
Independent Monitor bookkeeping reports a separate retained tool-wall lower bound>44.34s
with exact aggregate unavailable. Thus full support≤30/complete≤360 conformance is
unestablished if Monitor observation is included; the intake records this budget/accounting
deviation without changing the scientific rule or exempting the Monitor surface.
All raw evidence and the checkpoint are preserved; scoped remote closeout is complete.
No retry, successor, T/G restart, C promotion, disposition or additional budget follows.

## 10. Prospectively bound independent follow-up 8931

The [rolling Portfolio allocation](../../portfolio/decisions/2026-09-10-rolling-successor-allocation.md)
at main `674f246a2` selects exactly one new unscreened fit under this accepted recipe.
Root assigned the complete batch on 2026-09-10. This section supersedes the earlier
no-successor boundary only for that new allocation; §§1–9 and the 8921 evidence remain
historical. There is no retry or successor after this new allowance.

Select training master **8931** and evaluation namespace **8932** before constructing
any new learner, RNG master or native episode. Replace m/q in §§3–4 with these values;
all other scientific quantities, constructor/draw ordering and private streams stay
unchanged. The source remains `scripts/run_acvc_fresh_dense_reuse_b01.py` and its shell
wrapper. The [8931 facts](ACVC_FRESH_DENSE_REUSE_B01_8931_PROSPECTIVE_FACTS_20260910.json)
expand the seeds and complete count/cost law. Prior namespaces include 8921/8922;
8931/8932 had no occurrence in the owned ACVC card/facts/intake records when selected.

The unchanged endpoint is 256 sequential two-episode rollouts, four full-rollout PPO
epochs each: 512 episodes, 1,024 Adam/backward calls, final checkpoint and C→F→dwell
64-episode panels. All 69,079 actor/critic parameters can move under nonzero-lr,
loss-dependent Adam. Always apply proposals during training. No initial/H/T/G panel,
retained-base substitution, screening, replacement, additional evaluation or early
best-checkpoint selection is allowed. A weak intact fit receives every final panel.

Apply §5 separately and verbatim: **UP** if mean difference >0.01 J; **DOWN** if
<−0.01 J; otherwise **WITHIN**, retaining sign. Thus both exact MEI boundaries are
included in WITHIN. F−C and F−dwell remain separate primaries; dwell−C is secondary.
New pre-output predictions: P(F−C is UP)=.75; P(F−dwell is UP)=.65. Owner prediction:
**not taken (unattended)**. The prior fit's predictions remain already scored.

This question buys one further independent training realization with the same conditional
paired panel reading. Scientific-reading mode used FOUNDATIONS §6 and 04_EMPIRICAL:
the complete fit is the independent training unit; common initial worlds justify these
conditional pairs, while divergent own histories and private proposal streams remain
part of the packages. Even a second favorable fresh fit does not establish training-
population uncertainty or isolate a retrace component. Existing 8921 support (+.12293 J
F−C, +.08772 J F−dwell) coexists with five adverse F−dwell worlds and dwell's +.03522 J
gain. No tuned native headroom record exists. The §5 interpretation narrative and
stopped learned T/G package continue unchanged; recasts remain two.

The new caps are **270 s whole supervised native task**, **90 s all additional runtime
support including Monitor**, **360 s total**, with no savings transfer between task and
support. Support includes required checks, observation, collection/readback, numerical
analysis, preservation and closeout. Existing 8921 costs are not reclassified: its old
inclusive support is >52.3964878 s with exact aggregate/full 360 s conformance unknown.
The retained 172 s conservative native task and the older 222.200 s projection support
feasibility, not a guarantee for new trajectories or contention. Proposed support is
30 s DM plus 60 s Monitor within the inclusive 90 s; actual components must be retained.
No profiler or accounting experiment is added. Cap failure preserves partial evidence
and required terminal facts, without replacement, budget transfer or negative polarity.

Engineering-scope §4: **none needed**. The existing CPU FP32 Torch1/1 route, joined
destination admission, supervisor, checkpoint and summary paths suffice. L0, exact
source, focused check, independent review, actual handle and Monitor adoption are in
the [8931 execution record](ACVC_FRESH_DENSE_REUSE_B01_8931_EXECUTION_20260910.md).
Existing source/runner/test budgets are inherited, not reset.

Object-tier options: (a) bind the one allocated fit to fresh 8931/8932 with the unchanged
law; (b) substitute a retained or screened base; (c) alter panels or seek another law.
Recommend/select (a), the only conforming realization of the Portfolio allocation.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

## 11. Completed independent fit8931

The §10 binding completed once at dfee6e8a3cecfde866da07fef60ffcdd319956b5.
All512 training episodes,1024 updates and192 final evaluations are intact. F−C
+.0915279844J and F−dwell +.0638998669J are UP; dwell−C +.0276281175J is UP.
Four F−C and eleven F−dwell adverse worlds remain. The new predictions are scored
in the [8931 intake](ACVC_FRESH_DENSE_REUSE_B01_8931_INTAKE_20260910.md); prospective
probabilities and the older result above remain unchanged.

The169s conservative native charge passes270s. The inclusive90s support/360s total
bill is not fully established because Monitor measured only part of its work; the
known components and missing overhead are explicit in the new collection/intake.
This does not rewrite the old8921 accounting deviation or the new valid primaries.
The new numerical allocation is finished; no retry or successor is authorized.

## 12. Prospectively bound independent follow-up 8941

The [four-slot Portfolio mapping, ACVC](../../portfolio/pro_packets/20260910_four_slot_rolling_refill/EXECUTION_MAPPING.md#acvc-one-further-unscreened-fresh-dense-fit-360-seconds)
allocates exactly one further unscreened fresh fit under §§2–5,10–11, with the
complete conforming response at1ea43d8fbc846807d71d4d894136f357f65551b6. Root assigned
this batch to the replacement DM on2026-09-10. This allocation supersedes only
the earlier no-successor boundary for this new fit; no fourth fresh fit follows.

Select training master **8941** and evaluation namespace **8942** before any new
learner/RNG/native output. Replace m/q in §§3–4; all other quantities, draw order,
native semantics and fixed final endpoint remain unchanged. Existing8921/8922 and
8931/8932 are historical. The [8941 prospective facts](ACVC_FRESH_DENSE_REUSE_B01_8941_PROSPECTIVE_FACTS_20260910.json)
expand the seed ranges, count law, movable parameters and retained cost projections.
No retained checkpoint, screened initialization or best-of-many endpoint is used.

Exactly512 training episodes,256 sequential two-episode rollouts and1024 Adam/
backward calls fit all69079 parameters under the existing nonzero-lr learner.
Always apply proposals while fitting, then preserve the final checkpoint and
evaluate C→F→dwell64 episodes each, including an intact weak fit. There are704
scored episodes/180224 team steps, plus four unscored constructor resets. Intrinsic
dominant factors remain512×256×5 collection,256×4 updates replaying2×256×5 agent
steps each, and3×64×256×5 evaluation forwards. No nested search or extra panel.

Apply the unchanged rule separately to F−C, F−dwell and secondary dwell−C:
**UP** if mean difference >0.01 J; **DOWN** if <−0.01 J; otherwise **WITHIN**,
retaining the sign. Both exact boundaries remain WITHIN. MEI.01J is the retained
native practical margin. New pre-output predictions: **P(F−C is UP)=.75;
P(F−dwell is UP)=.65**. Owner prediction: **not taken (unattended)**. These forecasts
remain distinct from the already scored8921/8931 forecasts.

Scientific-reading mode used FOUNDATIONS§6 and04_EMPIRICAL: the entire fit is the
independent training unit; paired initial worlds support only checkpoint-conditional
SEs because private streams, histories, commands and reactive teammates diverge.
A third favorable fit would extend the observed package support, not establish
stable superiority, pure retrace causality or transfer. Above the MEI against both
comparators supports continued consideration of this package; a competitive dwell
or opposite sign weakens that recommendation; within the MEI does not prove
equivalence. All outcomes survive. The two preceding fresh observations remain
separate from selected8201/8202 assets and the ended learned T/G losses. Their
F−dwell gains coexist with5 and11 adverse worlds and positive dwell−C means.
No new comparator/mechanism or unresolved source claim needs another corpus search.
Tuned same-information native headroom remains absent; F is attained, not an upper.

Caps remain **270s complete supervised native chain +90s all additional runtime
support, including Monitor =360s complete**, with no transfer, retry, replacement,
resumed slice, panel reduction, T/G reopening or automatic successor. Earlier
accounting gaps remain historical. Native CPU FP32/Torch1/1, remote-first routing,
committed exact source, joined destination admission and detached execution persist.
Engineering-scope §4: **none needed**. Existing source/runner/test budgets are not
renewed. L0, acceptance, exact launch and accounting belong in the
[8941 execution record](ACVC_FRESH_DENSE_REUSE_B01_8941_EXECUTION_20260910.md).

Object-tier options: (a) bind the one allocated unchanged fit to fresh8941/8942;
(b) substitute retained/screened data; (c) alter fitting or panels. Recommend/select
(a), the conforming realization. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).** Recasts2 and lowest contention remain unchanged.

## 13. 8941 preparation stop with no scientific output

The §12 source/card/prediction binding was published atcafef130c9d4d89febda8fd788ad9458b6985aca
and independently reviewed without a material finding. The one remote source-
preparation command then exceeded the inclusive90s support cap: its matching
local transport was stopped after102.1040615s without output. Root confirmed
technical no-ready and one bounded read-only reconciliation; that12.0324544s
call reached a remote shell but returned no Git/path fact before timeout.
Remote preparation effects remain unknown and are preserved without another query.

No synthetic target, admission, scientific submission, model/RNG construction,
training/update/evaluation or Monitor assignment occurred. The forecast stays
unscored, and no8941 primary or polarity exists. The
[technical intake](ACVC_FRESH_DENSE_REUSE_B01_8941_INTAKE_20260910.md) records the
support breach and exact no-ready return. This allocation ends; no retry,
replacement, budget transfer or new fit is authorized. All previous scientific
results and their limits remain unchanged.

The later, separately assigned [technical recovery](ACVC_FRESH_DENSE_REUSE_B01_8941_INTAKE_20260910.md#6-separately-assigned-remote-effect-recovery)
verified the exact remote checkout absent/unregistered and stopped the directly
identified abandoned reconciliation tree. The remaining recorded helper tree was
also absent at the final read; its initially uncertain origin stays explicit.
No named cleanup dependency, scientific output or new execution allowance remains.

## 14. New allocation: unscreened fit8951 with explicit preparation support

The [2026-09-11 Portfolio mapping, ACVC](../../portfolio/pro_packets/20260911_remaining_capacity_refill/EXECUTION_MAPPING.md#acvc--one-new-unchanged-fresh-fit-explicit-preparation-investment),
complete response0dbbcbf807509ccc34a3a1de353114be88896897 and Root assignment
allocate one new unchanged fit. The failed8941 allocation stays ended and unscored.
Select training master **8951** and evaluation namespace **8952** before any new
scientific output; neither appeared as a binding in the scoped ACVC cards/intakes/
facts searched at selection. This is an unscreened choice, not a global registry claim.

Use §§2–5 unchanged with m=8951/q=8952: one DENSE fit,512 training episodes,
256 sequential two-episode rollouts,1024 Adam/backward calls, all69079 actor/critic
parameters eligible for nonzero-lr loss-dependent updates, and only the final
checkpoint. Evaluate C→F→dwell64 episodes each even for an intact weak fit.
Intrinsic work is512×256×5 collection actor rows,256×4 updates replaying2×256×5
agent rows, and3×64×256×5 evaluation rows:704 scored episodes/180224 team steps.
There are nine top-level model constructions,3 post-fit loads and4 unscored
constructor resets. No numerical fixture, smoke, pilot, profiling or added panel.
The [prospective facts](ACVC_FRESH_DENSE_REUSE_B01_8951_PROSPECTIVE_FACTS_20260911.json)
calculate the full seed/count/cost law without constructing a model or RNG.

Read F−C and F−dwell separately, with dwell−C secondary: **UP** if mean>+.01J,
**DOWN** if mean<−.01J, otherwise **WITHIN**, retaining sign and both boundaries.
MEI.01J retains the native practical-margin rationale. Pre-output predictions are
**P(F−C is UP)=.75; P(F−dwell is UP)=.65**; owner prediction **not taken (unattended)**.
The independent learning unit is the whole fit. SD/sqrt64 describes conditional
paired initial worlds, not training-population uncertainty. Scientific-reading
mode reuses FOUNDATIONS§6 and04_EMPIRICAL: divergent own histories/private streams
are part of the compared packages; no pure-retrace or matched-dose claim follows.

Above the MEI against both comparators extends the observed package support;
inside it is not equivalence; an opposite sign or competitive dwell weakens further
investment. Every intact outcome and adverse world is retained. Existing8921/8931
F−dwell gains coexist with5/11 adverse worlds and positive dwell−C means. No tuned
same-information native headroom record exists; F is attained performance, not an
upper reference. No unresolved mechanism or comparator change needs new retrieval.
Recasts2, lowest contention and the ended learned T/G package remain unchanged.

This allocation fixes **270s complete native chain +330s all invoked support =600s
complete**, with no transfer. Support includes source preparation, actual review/check
commands, Monitor, collection/reduction/preservation/publication and Root integration,
charged once. Every preparation command receives a whole-lifetime bound; connection
timeout alone is insufficient. Existing169/172s native observations and the retained
222.1996846s projection are analogies, not guaranteed new costs. Unknown components
remain unknown. No repeated preparation, retry, replacement, resumed slice or successor.
Cap/technical failure preserves evidence without scientific polarity.

Engineering-scope§4: **none needed**. CPU FP32/Torch1/1, exact committed source,
joined destination memory admission and detached remote execution remain. Existing
engineering/test budgets are not reset. The [execution record](ACVC_FRESH_DENSE_REUSE_B01_8951_EXECUTION_20260911.md)
contains L0, changed-risk review, one allowed static/stub publication check, exact
command, actual Monitor adoption, full collection and cleanup ownership.

Object-tier options: (a) bind the allocated unchanged fit to fresh8951/8952;
(b) use a retained/screened identity; (c) alter learning or panels. Recommend/select
(a), the conforming realization. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).**

## 15. 8951 technical no-ready boundary

Published sourcee61facdff70091cd9cdd33bc231a149ed9106d35 passed actual changed-risk
review and the single allowed stub publication check. Full source bundling and
transfer succeeded once; the one bounded remote preparation exited128 because
Windows text-mode shell input carried carriage returns in commands and paths.
No memory admission, scientific submission, model/RNG construction, training or
evaluation occurred. The exact checkout and registration were later directly
verified absent during scoped closeout; the staged duplicate was preserved then
removed. The [8951 intake](ACVC_FRESH_DENSE_REUSE_B01_8951_INTAKE_20260911.md)
records the rule, receipts and accounting limits. Forecasts stay unscored.

The allocation ends without repeating preparation or launching a substitute.
This supplies no new performance evidence and changes no prior scientific result,
mechanism conclusion, lifecycle or priority. Unused native time grants no retry.

## 16. New Portfolio allocation: fresh8961 fit and8962 final panels

The new [Portfolio response §§1,5,7,9](../../portfolio/pro_packets/20260911_open_directions_program/archive/RESPONSE.md),
immutable source6c32ade3216c374ecf2f5179b15d559729cd45c9, selects one new unchanged
ACVC unit under PRO_FINAL / OWNER_DELEGATED. Root assigned it on2026-09-11.
This does not retry8951 or reuse its preparation, learner state, namespace or cap.
Its separately accepted LF/binary-input repair supplies the preparation method.

Select unscreened training master **8961** and evaluation namespace **8962** before
any scientific output; the scoped ACVC card/facts/intake search found no previous
binding for either. This is a direction-local identity check, not a global registry.
Use §§2–5 with m=8961/q=8962 and otherwise unchanged law:512×256 training,
256 sequential two-episode rollouts,1024 full-rollout Adam/backward calls,
final checkpoint, then C→F→dwell64 episodes each, including an intact weak fit.
The [prospective facts](ACVC_FRESH_DENSE_REUSE_B01_8961_PROSPECTIVE_FACTS_20260911.json)
calculate every seed and count without model/RNG/native execution.

The Portfolio clarification is binding: **C always sends the sampled proposal**.
**Dwell sends zero only on its own evolving history's accepted predicate, otherwise
its sampled proposal**. It borrows neither F's event times nor dose. F retains
`binding.py`'s prior unambiguous lowest-SINR anchor, loss/away-motion cue and clipped
reversal of its own preceding actual displacement/30. Every arm advances private
recurrence each tick and receives its own actual command. Current code already
implements these facts; no comparator, binding or native learner change is needed.
C cue counters remain unmeasured incidence. The erroneous shorthand in the old
Portfolio brief supplies no alternative controller law.

Read F−C and F−dwell separately, dwell−C secondary: **UP** if mean>+.01J,
**DOWN** if mean<−.01J, otherwise **WITHIN**, retaining sign and both boundaries.
MEI.01J=2.56S retains the native practical-margin rationale. New pre-output
predictions: **P(F−C is UP)=.75; P(F−dwell is UP)=.65**. Owner prediction:
**not taken (unattended)**. Historical forecasts remain separately scored/unscored.

Scientific-reading mode reuses FOUNDATIONS§6 and04_EMPIRICAL: the complete fit is
the independent learning unit. Paired initial worlds support conditional SD/SE,
not training-population uncertainty; private proposals, histories and intervention
opportunities diverge. A third above-MEI fresh-fit observation would extend bounded
package support. Competitive dwell, within-MEI differences or reversal weaken
further spending; inside does not prove equivalence. Preserve every adverse world
and all final rules. No pure-retrace, matched-dose, stable-superiority, headroom,
transfer, C or formal UAV-entry claim follows. No unresolved new mechanism or
comparator question requires another corpus search. Tuned native headroom remains
absent; prior positive means and5/11 F−dwell adverse worlds remain separate.

This fresh allocation caps **the whole native chain at270s**, **all additional
invoked support at330s**, and **complete work at600s**. The three panels share the
270s native cap. No transfer, pilot, numerical fixture, extra panel, screening,
retry/replacement, old namespace/state or automatic successor is authorized.
Intrinsic work remains704 scored episodes/180224 team steps,655360 collection
actor rows,2621440 replay actor rows,524288 critic-update rows,245760 evaluation
actor rows,9 top-level constructions,3 loads and4 unscored constructor resets;
up to6553600 coordinate-pair checks belong to the algorithm. Prior172/169s native
observations and222.1996846s projection are planning anchors, not new timing facts.
Source preparation/review/check, Monitor, collection/reduction/publication,
integration and scoped cleanup are charged once to support. Unknowns remain unknown.

Engineering-scope§4: **none needed**. Preserve CPU FP32/Torch1/1, remote exact
published source, joined destination memory admission and detached execution.
Reuse the LF helper/sender with local syntax checking before new remote effects;
do not repeat its unchanged byte-echo test. The [execution record](ACVC_FRESH_DENSE_REUSE_B01_8961_EXECUTION_20260911.md)
holds L0, review, exact command, actual Monitor adoption and collection/cleanup.
Recasts2/lowest contention persist; ready HIGH VNFC precedes ready ACVC, while
unready VNFC creates no hold. Root coordinates contention.

Object-tier options: (a) realize the allocated unchanged unit with fresh8961/8962;
(b) reuse a failed identity/state; (c) alter training or the comparator/panels.
Recommend/select **(a)**. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).**
