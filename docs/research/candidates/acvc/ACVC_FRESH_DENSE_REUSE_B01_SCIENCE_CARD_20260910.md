Claim under test: On one prospectively selected fresh DENSE fit, fixed own-history retracing F improves native team return relative to always-apply C and own-cue dwell.
Binding MARL structure: (d) multi-agent partial observability: each UAV uses its own link history while teammates' simultaneous motions change interference, service and later observations.

# ACVC fresh DENSE reuse B01 — science card

Date: 2026-09-10. **B/EXPLORE; the sole allocated scientific result is complete.**
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
