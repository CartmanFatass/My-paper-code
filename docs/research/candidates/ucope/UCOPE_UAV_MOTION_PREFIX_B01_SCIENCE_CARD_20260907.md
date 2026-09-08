Claim under test: on the fixed five-UAV task, one learned optional opening velocity commitment can improve sampled complete team native return over same-information primitive-step recurrent PPO under the same training-step and update budget.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; five jointly learning actors receive their own local observations and affect shared service, with fixed membership throughout each episode.

# UCOPE UAV motion prefix B01 — science card, 2026-09-07

## 1. Authority, class and present boundary

Object: **UCOPE-UAV-MOTION-PREFIX-B01**, **B/EXPLORE**. The direction selection is the complete [Convergence response](pro_packets/20260907_uav_interface_convergence/archive/RESPONSE.md), immutable commit `426513b18b38b477dd255b3e8524424d8deb8a19`, sections III–VI, accepted in [the intake](UCOPE_UAV_INTERFACE_CONVERGENCE_INTAKE_20260907.md). [P15's UCOPE assignment](../../portfolio/handoffs/2026-09-07-p15-rolling-refill-after-transport-split.md#ucope--complete-the-selected-uav-cardspec-then-comparison) authorizes this card, one complete code spec and the new engineering assignment.

This card is fixed for that engineering handoff. **P15 allocates zero UAV scientific invocations and no formal UAV-validation entry.** Root captures the same complete committed task/spec/source for comparison batch03 before any CM coding. Later accepted implementation and a named execution command are still needed; publication of this card is not that command. A/B objects have no consumption state. Current AGENTS and evidence-spec §11 control over historical stronger wording.

## 2. Host, information and mechanism

Use base `envs.pettingzoo.uav_env.MultiUAVEnv` through the existing `ParallelToArrayAdapter`. Existing source at `521da9b267b623d7368ff1ed46807ff413dc095b` is byte-identical on these UAV paths to the Pro input. No scenario subclass or environment-code change is selected.

| Fixed setting | Value |
| --- | --- |
| UAVs / users / horizon | 5 / 50 / 256 primitive steps |
| Area / height / component speed / primitive time | 1000 m / [50,150] m / 30 m/s / 1 s |
| Layout / channel / evaluation backend | uniform / free_space / vectorized |
| Observation limits | 20 local users, 10 local UAV slots |
| Other settings | shadowing=False, FDMA=False, paper_reward=False, step_path_loss_cache=True, render_mode=None; other constructor constants unchanged |

Each actor receives all 104 existing local observation components, its last normalized velocity command actually sent to the environment, and its own remaining hold count divided by four: 108 inputs. The last command starts at zero. The base has no separate velocity sensor; position clipping is observed through the unchanged local observation, not through an added privileged field. Actors share weights but keep separate recurrent state, updated every primitive step and reset only at episode reset. Training uses a separate common centralized critic: normalized base state plus all prior velocity commands and remaining holds, sampled **before** current decisions. No current sampled action, global diagnostic, another agent's observation or critic representation enters an actor.

Treatment **T**: at t=0 each agent samples velocity and duration 1 or 4; it holds that velocity for the selected number of actual environment steps, then uses ordinary feedback for the rest of the episode. There is only one duration decision per agent per episode. Generic **G**: every step can choose the same legal velocity, including hover or repeating a command. It has the same local information, memory and training-critic permissions. All five agents co-adapt inside each fit; there are no frozen partners, roster changes, replacement or identity persistence across reset layouts. Sorted observation slots are not persistent entity IDs.

The path under study is actual velocity → position/channel/connection → the owning UAV's next local observation → recurrent state and subsequent owned velocity → real primitive rewards → PPO credit → team service. During a hold, the world, other UAVs, local observations, memory and reward continue. “Paid” means native service opportunity consequences; no new sensor fee, information reward, flight-energy model or positive displacement charge is introduced. Geometry, time structure, optimization and ordinary feedback remain alternative explanations.

## 3. Learner, comparator and independent units

Both fits use FP32 recurrent PPO with a tanh 64-unit encoder, GRU-64, three-dimensional tanh-Gaussian velocity head and a separate two-layer 128-unit critic. T alone adds a two-logit duration head initialized at probability one-half. Common initial parameters are equal within each pair; optimizers, recurrent states and on-policy data are separate. Exact standard-library/module choices, distribution regularizer, primitive credit, chunking and RNG domains are fixed in [CODE_SPEC §§2–5](UCOPE_UAV_MOTION_PREFIX_B01_CODE_SPEC_20260907.md#2-model-and-information-boundaries).

Each arm-seed trains for 131,072 team primitive steps: 512 complete episodes, 256 rollouts of 512 steps, four full-rollout epochs per rollout and **1,024 actual joint actor/critic Adam steps**. Adam lr=3e-4, PPO clip=.2, value coefficient=.5, entropy coefficient=.01 and gradient clip=.5. Full finite-episode reward-to-go with gamma=1 is used; no GAE or terminal bootstrap. Recurrent gradients are truncated at 32-step chunks with their collected initial hidden states. Held commands supply no new actor likelihood samples, although their observations and critic targets remain.

The two independent training-pair masters are **6801 and 6802**. No exact match was found in the current UCOPE scientific/code records before writing this card. This is a bounded freshness check, not a universal historical namespace assertion. Within each pair, T/G share initial parameters and prescribed reset seeds; their trajectories and later random-stream consumption may differ. Agents, episodes, chunks and evaluation replicates are not additional training units.

Use only the final T and G checkpoints, each evaluated on 32 sampled episodes; no best-checkpoint, best-seed or action-greedy replacement. Add **H**, fixed zero velocity, on the same 32 reset seeds per pair. H has no learner or tuning. It is a competence reference inside this B, not a tuned generic baseline or headroom upper bound. No reusable tuned baseline package matching this newly selected local-information/controller/budget combination has been identified.

## 4. Primary, uncertainty and reading rule

For each episode, let `R_t = sum(info['rewards_dict'].values())`. The adapter scalar is the additional per-agent average and is not this team primary. Accumulate the unmodified native values in float64/Python float, and set `J=sum(R_t)/256` over the complete episode. Training targets use the corresponding FP32 rewards; the environment's internal precision and reward remain unchanged.

For pair s, `Delta_s = mean_e(J_T,s,e - J_G,s,e)`, e=0..31. Joint primary is `Delta=(Delta_6801+Delta_6802)/2`. Report raw T/G/H returns, both pair endpoints, sample SD across the two endpoints, and each pair's conditional evaluation SE from the 32 whole-episode differences. The joint conditional SE is `sqrt(SE_6801^2+SE_6802^2)/2`; it does not replace training-population uncertainty. Do not pool B01–B05 into these quantities.

**MEI: absolute 0.01 in time-average team reward.** The default native scale is 0–1; .01 is an average percentage point over the full episode. For scale, the coverage contribution from continuously serving one additional user is .7/50=.014. This is an object-specific interpretation scale, not observed headroom or an engineering QoS guarantee.

| Joint point reading | Rule and bounded interpretation |
| --- | --- |
| `UP` | Delta > .01: preliminary advantage of these fitted control packages under this task and budget. Competent-generic or information-path wording additionally depends on its actual corresponding evidence. |
| `WITHIN` | -.01 <= Delta <= .01: no gain at the selected scale under this budget; not stable equivalence. |
| `DOWN` | Delta < -.01: adverse native evidence for this task/prefix/learner budget. More observations or changed actions do not compensate for it. |
| Partial | Missing T/G primary data do not become zero. Preserve completed facts and identify the damaged dependent claim. |

How the result will be interpreted: above MEI would justify considering a narrowly named follow-up, with opposite-sign pairs and comparator limits retained. Inside MEI would favor reassessing this prefix's value relative to ordinary feedback before expanding it. An opposite-sign effect would restrict this tested package. No branch automatically starts another run or closes the direction. A missing hover or information diagnostic limits competence or attribution; independently trustworthy T−G remains reportable. Native losses are reported separately from any favorable local diagnostic.

Record final-evaluation prefix rewards (t=0..3), suffix rewards (t=4..255), duration use, actual movement and the t=0..4 observation/action timing trace for T/G. Diagnostic source indices identify selected local entries within an episode only and never reach actors. These observations can support a possible information path; they do not identify a pure information price or uniquely cause a native gain.

## 5. Budget, exposure and stops

The prospective execution unit is **one complete pair invocation per master**, T then G then H, serial in one scientific CPU process with one compute thread. H reuses the resettable G environment; its evaluation and pair publication are charged inside G's allowance. Complete caps selected here are **1,800 s per arm-seed, 3,600 s per pair, 7,200 s summed across two pairs**. Startup/imports, the constructor's internal reset, initialization, learning, final evaluation, diagnostics and publication are included. These are stop limits, not measured runtime estimates or a current run allocation. No cap resets for a phase, checkpoint, new script or dataset slice.

| Planned work | Count |
| --- | ---: |
| Main training | 2 pairs × 2 arms × 131,072 = 524,288 team steps; 2,048 episodes |
| Actual optimizer calls | 4 fits × 256 rollouts × 4 = 4,096 |
| Learned-policy evaluation | 128 episodes / 32,768 team steps |
| Added H evaluation | 64 episodes / 16,384 team steps |
| All scored episodes and steps | 2,240 episodes / 573,440 team steps |
| Constructor resets, outside scored episodes | 4, included in whole invocation time |
| T/G diagnostic work | 3,200 agent frames; at most 6,400 local-index method calls |
| Nested candidate/trajectory/controller search | none |

The machine-generated [preparation facts](UCOPE_UAV_MOTION_PREFIX_B01_PREPARATION_FACTS_20260907.json) calculate **G=66,311 / T=66,441 trainable parameters**, with 1,024 permitted positive-lr Adam steps per fit. This is a planning exposure line: the learner has an update path, not a claim of already measured parameter motion. Every actual fit reports initial/final parameter norm, absolute/relative displacement, actual optimizer and true velocity/duration decision counts. New actual exposure during this preparation is zero.

Dominant unknown work coefficients remain `init + 131072*c_env_actor + 1024*c_update + 8192*c_eval + publication`, with H's extra 8192 evaluation steps charged to G. There is no measured UAV wall/CPU forecast or tuned headroom. B05's 9.51 s and its 600/1200 s caps do not transfer. If the selected cap cannot accommodate the question, return the fact and reconsider scope/evidence; do not automatically increase the cap, add parallelism or commission a cost pilot.

Future result work follows `.codex/hmasd-compute.toml`: `hmasd-wsl-node`, `/home/wu/.venvs/hmasd/bin/python`, exact committed detached source, CPU FP32 learner, single thread. Host identity is not the estimand; no cross-platform bit-equality claim or automatic fallback is selected. Immediately before each later named pair invocation, the actual node must pass the existing physical/effective >=4 GiB admission, joined to the runner by `&&` under `agent-task`. P15 performs neither admission nor a launch.

Stop at prescribed counts, cap, a nonfinite learner, or a defect that prevents faithful reward/information/training/primary data. Preserve completed rows, errors and exposure. No retry, resumed learning, replacement seed or extra evaluation is allocated. A cap breach is recorded as engineering nonconformance; independently trustworthy completed facts remain explicit. Only §11.4's four conditions may hold a B launch.

Engineering scope §4: **none**. Reuse the existing resource/supervisor route; scientific counters and selected observations are measurements of this question, not new resource telemetry. No new guards, registries, validators, resume, workers, telemetry service or provenance machinery. Research code <=2,000 new lines, runner <=600; 30% orchestration is a review signal. The original engineering checks in CODE_SPEC §8 use a synthetic non-UAV fixture, a single <=60 s runner smoke and focused tests within the existing <=5 min directory budget.

## 6. Predictions and contrary evidence

Predictions recorded before UAV output:

1. Joint reading is `WITHIN` (subjective probability .65): only one opening prefix differs, while G retains all useful legal control opportunities.
2. At least one G−H pair mean is nonpositive (.60): generic competence under this untested finite budget is uncertain; hover can already provide service.
3. Each T fit's final sampled d=4 frequency lies strictly between .1 and .9 (.60): the sparse opening duration head may retain substantial mixed use.

Owner prediction slot: **not taken (unattended)**. These predictions choose no extra metric, run-until-positive rule or outcome-dependent checkpoint. They will be scored against all outcomes, including incomplete evidence when their quantities are unavailable.

B05's finite-host useful paid acquisition motivates this new question. B04's harmful extra purchase/negative endpoint, B01's two nulls and older false-probe/unchanged-competence limits remain the strongest contradictions to broad usefulness. Prior literature retrieval in [the return-model proposal §5](UCOPE_POST_B01_RETURN_MODEL_QUESTION_PROPOSAL_20260907.md#5-question-driven-source-check) keeps downstream native benefit and real cost central; VIL2C/DACOM provide no UAV interface, performance or novelty finding here. No pure information value, unique COUNT representation, stable superiority, transfer, safety or deployment claim is sought.

## 7. Deliverables and present handoff

The [complete code spec](UCOPE_UAV_MOTION_PREFIX_B01_CODE_SPEC_20260907.md) and [five-item CM task](UCOPE_UAV_MOTION_PREFIX_B01_CM_TASK_20260907.md) bind all missing implementation choices, owned paths, exact original checks and current no-UAV boundary. The [preparation intake](UCOPE_UAV_MOTION_PREFIX_B01_PREPARATION_INTAKE_20260907.md) records the object choices, runtime evidence, owner item and Root return. Scientific result files will later follow the ordinary E0/card/intake route. No result or formal UAV entry is claimed by this preparation.

## 8. Current P21 execution allocation — 2026-09-07

[P21's UCOPE continuation](../../portfolio/handoffs/2026-09-07-p21-fsd-ucope-frrie-continuations.md#ucope--accepted-uav-b-implementation-through-two-fixed-pairs), committed at `d3f03ffa4`, supersedes the historical P15 zero-invocation boundary in §§1,5,7 **only for the following two complete scientific pairs**. Scientific meaning, predictions, original reading rule, exposure, settings, information permissions and complete caps remain those in §§2–6 and the frozen CODE_SPEC at `f718134f210889ff14f07deb3846cde853abd7b4`.

Run master **6801**, then after its CM technical acceptance run **6802 irrespective of the first score**. Each is one serial **T → G → H** invocation: 131,072 training team steps and 1,024 actual Adam calls per learned arm, 32 final sampled evaluation episodes for each T/G/H; fixed five UAVs, CPU FP32 learner, one scientific process/compute thread. Complete caps stay **1,800 s per arm, 3,600 s per pair, 7,200 s summed**; startup/common initialization is charged to T, and H plus pair publication to G. The second pair is already allocated, with no all-positive, MEI or competence prerequisite.

The baseline implementation was committed at `78dd2a461e838b9d863b81ed9e2d5946d011f33a`. Its original 12 focused tests, 80-step/eight-update synthetic fixture and independent review provide bounded engineering evidence; no real UAV call or measured cap feasibility follows from them. The same CM supplies exact committed source, remote cwd, output roots, supervisor handle/literals and technical acceptance. Root integrates/pushes the named source, performs each fresh actual-node admission immediately before its runner in the detached supervisor command, launches and observes. A document-only descendant does not change the accepted source surface or scientific seed allocation.

Root does not dispatch the second invocation until the first's technical integrity is accepted. Card-defined nonfinite, cap or scientific-integrity failures stop their dependent route and preserve independently trustworthy completed facts; an unallocated retry or unresolved scientific conflict returns through Root. No extra seed/evaluation, resumed learning, pilot, environment change, local fallback or automatic cap increase is released.

Actual UAV-validation entry will be recorded with the accepted scientific invocation and observed UAV execution, linked to this card and Pro direction decision `426513b18b38b477dd255b3e8524424d8deb8a19`. This allocation and the prepared command alone are not entry. There is no promotion, successor or change to Portfolio lifecycle/priority in this release.

## 9. Observed P21 completion and UAV entry — 2026-09-07

Both allocated masters, **6801 and 6802**, completed at exact source
`536949660fee3ab9ac92aba29c2c0455ffe9f6e1` on `hmasd-wsl-node`, with passed
fresh admissions and terminal exit0. Actual total exposure is **573,440 UAV
team steps, 4,096 Adam calls and 192 final evaluation episodes** across four
real fits; all 2,240 training/evaluation episodes completed. The original
counts, final-only selection, information/reward boundaries, MEI, predictions
and reading rule above remain unchanged.

The [complete E0](UCOPE_UAV_MOTION_PREFIX_B01_RESULT_EVIDENCE_20260907.md) and
[scientific intake](UCOPE_UAV_MOTION_PREFIX_B01_INTAKE_20260907.md) accept
**joint UP**: T−G endpoints 0.006714032239188856 / 0.023720809005454126,
mean **0.015217420622321492**, endpoint sample SD 0.012025607177551996 and
joint conditional evaluation SE 0.007523816216520829. This is preliminary
fitted-package evidence at B, with the per-pair and adverse-episode limits in
the intake; it is not stable superiority or pure-information attribution.

**Actual UAV-validation entry is recorded for this B card.** Its first
accepted scientific invocation, `ucope-uav-motion-prefix-b01-6801-p21-20260907`,
began at **2026-09-08 04:15:06 UTC / 2026-09-07 21:15:06 PDT**, and completed
286,720 observed UAV steps with actual learning/native evaluation by
04:19:55 UTC. The exact first `env.step` clock is unlogged; supervisor start
anchors the accepted invocation. This actual-execution evidence, linked to
the Pro decision in §8, satisfies entry without treating preparation or
synthetic checks as UAV work. The second allocated pair also completed.

Summed external whole invocation wall is **575.24 s**, within the original
complete caps; aggregate CPU/scratch are `resources_unmeasured`. The E0 retains
6801's CR-suffixed remote output-path/collection correction separately from
valid science. One of three prospective predictions matches; the owner's
prediction is not taken (unattended). P21's allocation is complete; this result
appendix grants no rerun, successor, new seed, promotion or Portfolio change.

## 10. Prospective P24 fresh-pair continuation and P26 plumbing — 2026-09-07

[P24](../../portfolio/handoffs/2026-09-07-p24-ucope-fresh-uav-pairs.md), full
commit `63c3f6a9ae736e56146e62772278d414481e0dbb`, allocates exactly two
additional fresh training-pair masters, now fixed as **6901 then 6902**.
This is **outcome-informed B/EXPLORE continuation** selected after P21's joint
UP; these fresh predictions and identities are recorded before either new
output. No exact-word 6901/6902 match was found in the current UCOPE scientific
and code records before this amendment; this is a bounded freshness check.
P21's completed result, predictions, all adverse episodes and original UAV-entry
chain in §9 remain intact. New pairs are additional observations of the same
direction, not additional UAV entries or a new C object.

The question is whether the optional opening-commitment package retains a
native-return advantage across two newly trained pairs at the same task and
budget, with G−H retained as competence context. All §§2–5 numerical, model,
host, reward, information, history, hold, credit, RNG-domain, duration, endpoint,
evaluation and MEI semantics remain unchanged except the expressly selected
master values and the plumbing needed to propagate them. Common initial
parameters/reset seeds still pair T/G within each master; optimizers, memory
and on-policy trajectories remain separate. H remains zero velocity.

Each new master keeps T → G → H, **131,072 training team steps / 1,024 actual
Adam calls per learned arm**, and **32 final sampled evaluation episodes per
policy**, CPU FP32 / one scientific process and compute thread. Master 6902
runs only after 6901's CM technical acceptance, irrespective of its native
sign, MEI branch, G−H or duration observations. Complete caps remain **1,800 s
per learned arm, 3,600 s per pair, 7,200 s summed for P24**. Common startup is
charged to T; H and pair publication remain within G. No phase, correction,
script, checkpoint or evaluation slice resets a complete invocation's cap.

**Prospective reading.** Apply §4's original two-pair mean, conditional SE and
UP/WITHIN/DOWN/Partial rule to **6901/6902 only**. Preserve the separate P21
6801/6802 primary and its original reading. Also report the four named
training-pair endpoints descriptively with equal weight, sample SD (ddof=1),
and conditional evaluation SE `sqrt(sum_s SE_s^2)/4` when all four are complete.
That combined mean is a declared outcome-informed descriptive summary, not a
replacement P21/P24 primary, prospective four-pair confirmation or a stable
population conclusion. No agents/episodes/steps are added as training units.
Missing primary values remain missing, with the applicable subset and
dependent interpretation stated explicitly; no unobserved value becomes zero.

**P24 predictions, before new output:**

1. The new 6901/6902 joint reading is UP (subjective probability .60): the
   original mean favors T, but its margin and training variation remain uncertain.
2. Both new G−H pair means are positive (.60): there is prior evidence against
   hover, with the weaker original margin retained.
3. Each new T final sampled d4 frequency lies strictly between .1 and .9 (.80):
   prior mixed use and the unchanged single-opening learner suggest continued
   mixing, without a claim that mixing is beneficial.

Owner prediction: **not taken (unattended)**. Score all outcomes; a missing
dependent quantity is unassessable, not a forecast success. The earlier three
P21 predictions are not changed or rescored against new data.

[Computed exposure/cost](UCOPE_UAV_MOTION_PREFIX_B01_P24_EXPOSURE_AND_COST_20260907.json)
binds the seed domains and dominant work: **2 pairs × 2 learned arms × 131,072
training steps + 2 × 3 × 32 × 256 evaluation steps = 573,440 team steps**,
**4 fits × 256 rollouts × 4 = 4,096 Adam calls**, 2,240 scored episodes, four
constructor resets, 3,200 selected diagnostic frames / 6,400 source-index
calls. H adds 64 evaluation episodes / 16,384 steps inside these totals.
There is no nested policy/candidate/trajectory search or extra validation run.
If both new pairs complete, P21+P24 describe four training pairs, eight fits,
**1,146,880 team steps / 8,192 Adam calls / 4,480 scored episodes**.

At the unchanged loop counts, a per-arm projection takes the largest observed
P21 arm time, charging external-minus-runner time to T as common startup:
**T 148.267067 s / G including H and publication 141.371892 s**, or
**579.277918 s** across the two prospective pairs. This is a forecast from
observed same-scale work, not a guaranteed bound; both arm projections are
below the existing 1,800 s cap. P21 actual complete wall remains 575.24 s.
The learner has 66,441 T / 66,311 G parameters and 1,024 positive-lr updates
per fit; P21 observed total relative displacement 0.5183454–0.5983579 supports
its ability to move at this budget. New actual exposure here is zero. No
tuned headroom record exists; CPU/scratch remain unmeasured.

**Source and current engineering boundary.** Historical source
`536949660fee3ab9ac92aba29c2c0455ffe9f6e1` hardcodes real CLI and two-pair
aggregation to 6801/6802. The [amendment/source-gap intake](UCOPE_UAV_MOTION_PREFIX_B01_P24_AMENDMENT_INTAKE_20260907.md)
records that direct source finding and zero executed rejection. [P26](../../portfolio/handoffs/2026-09-07-p26-ucope-fresh-pair-plumbing.md),
full commit `a8502f9a7af53a7854bbd964e85608f3c7f8ff01`, expressly supersedes
P24's no-code-change boundary **only for seed/aggregation plumbing**. The same
CM preserves original 6801/6802 and engineering9001, admits this declared new
pair with actual Config/RNG propagation, rejects duplicate/mismatched/mixed
inputs, keeps exactly two summaries and the same uncertainty arithmetic, and
labels actual pair/card information truthfully. Four-unit descriptive analysis
stays outside the two-pair runner. No new scientific parameter or learner,
environment, optimizer, reward, evaluation or deadline change is authorized.

Only focused boundary fixtures and independent scientific-boundary review
are needed; **zero UAV/learner smoke or runtime/import probe**, and no fourth
CM comparison. Engineering scope §4: **none**; existing §5 code/runner/test
budgets remain. The corrected full source SHA and exact commands must be
accepted, committed/pushed and bound before Root dispatches either pair.
The amended card alone does not make the original CLI executable for P24.

The intended node/interpreter remain `hmasd-wsl-node` /
`/home/wu/.venvs/hmasd/bin/python`. Prospective detached cwd:
`/home/wu/hmasd-worktrees/ucope-uav-motion-prefix-b01-p24-20260907`.
Prospective handles are `ucope-uav-motion-prefix-b01-6901-p24-20260907` and
`ucope-uav-motion-prefix-b01-6902-p24-20260907`; relative output roots are
`temp/directions/ucope/exp/uav-motion-prefix-b01-<master>-p24-20260907`, each
with `resource_admission.json`. These are bindings to prepare, not accepted
handles or asserted-absent paths. CM retains P21's LF transport correction.
Root performs a fresh physical/effective >=4 GiB admission immediately before
each detached runner, observes accepted handles and returns original terminal
facts to the same CM. Nonfinite/cap/integrity stops and dependency-specific
partial reporting remain §8's rules. No local fallback, pilot, tuning, third
new pair, retry, cap reset, promotion or automatic successor is allocated.

**P26 source release, before P24 output.** The [readiness intake §6](UCOPE_UAV_MOTION_PREFIX_B01_P24_AMENDMENT_INTAKE_20260907.md#6-p26-correction-accepted-p24-ready-for-root--2026-09-07)
accepts corrected full source `9c541a8047b8c33e90f09aa65e326180343a23a0`
(containing this prospective amendment at8cb59913be). The exact
[P24 handoff](UCOPE_UAV_MOTION_PREFIX_B01_P24_ROOT_HANDOFF_20260907.md) is
committed at `4fdf6fb73c06d26fdb84a33b33edde6206c907cb`. Focused boundary
fixtures20 passed in0.50 s and reused independent review found no material
defect; no UAV/learner/import probe or admission was added. The declared
6901/6902 route is ready for Root under existing P24/P26 authority and the
unchanged stops above. Actual new exposure and accepted handles are still
zero at this source release; all prospective predictions and reading rules
above remain fixed.
