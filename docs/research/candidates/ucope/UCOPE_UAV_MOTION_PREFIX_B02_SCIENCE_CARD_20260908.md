Claim under test: with common per-agent PPO clipping, a learned optional opening velocity commitment improves sampled complete team native return over same-information primitive-step feedback on the fixed five-UAV task at equal training-step and update budgets.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; five co-adapting local actors affect shared service, and the amendment changes the common team-advantage credit path without changing membership or information access.

# UCOPE UAV motion prefix B02 — science card, 2026-09-08

## 1. Authority and present boundary

Object **UCOPE-UAV-MOTION-PREFIX-B02**, **B/EXPLORE**. This is the
outcome-informed successor selected in [P29 intake §8](UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md#8-p29-prospective-question-selection--2026-09-08)
within the opening-prefix family opened by Pro commit
`426513b18b38b477dd255b3e8524424d8deb8a19`, response III–VI.
[P33](../../portfolio/handoffs/2026-09-08-p33-ucope-agent-clipping-spec.md),
commit `75e4c55c98a9d8f50009375f2e2334830a486045`, authorizes this card,
complete code spec and prospective five-item handoff only.

This card fixes the scientific definition. **At the original P33 preparation,
allocation was zero source implementation, scientific imports, model/learner or
environment/evaluation calls, source tests, CM dispatch, Pro Send and launch.**
The three CM comparison batches are complete; P33 explicitly excludes a
fourth. A later named implementation task and execution allocation were then
needed. P47/P48's later allocation and observed implementation are recorded in
§9 below. B01/P21/P24 definitions and results are not rewritten; A/B objects
have no C-class consumption state. No family, recast, Portfolio or UAV-entry
decision is made here.

## 2. Unchanged host, ownership and information

Use the accepted base `MultiUAVEnv` and `ParallelToArrayAdapter`, with the
exact source settings in [B01 card §2](UCOPE_UAV_MOTION_PREFIX_B01_SCIENCE_CARD_20260907.md#2-host-information-and-mechanism):
five UAVs, 50 users, 256 one-second steps, 1000 m area, height [50,150] m,
30 m/s component speed, uniform layout, free-space/vectorized channel,
20 local user and 10 local UAV slots, unchanged default reward, no shadowing,
FDMA, paper reward or new environment variant. No physics/adapter edit is owned.

Each actor receives its own 104 existing local components, three last sent
normalized velocity commands and own remaining hold/4; recurrent state
advances at every primitive step. The separate common critic receives the
same normalized 116-component base state plus 20 prior command/hold values,
assembled before current decisions. No global diagnostic or critic data
enters an actor. Shared actor weights retain separate agent histories.
All five members remain fixed; there is no join, leave, rejoin, replacement
or survivor-state claim. Sorted local slots are not persistent entity IDs.

T samples velocity and duration **1 or 4 only at t=0** for each UAV. For d=4,
the t0 command is held through t=3 and a fresh feedback decision occurs at
t=4; d=1 resumes feedback at t=1. Observations, memory and reward continue
during holds. G may choose any of the same legal velocities every step,
including repeating a command or hovering. The event path remains velocity
→ position/channel/service → owning UAV's local observation → recurrent
state and owned action → actual team reward → learning credit → native
service. No sensing fee, information bonus or flight-energy model is added.

## 3. Common learner amendment

Both T and G now clip **one ratio per agent-owned compound action**. Define
ell_i as the three-coordinate tanh-Gaussian log density at the stored pre-tanh
sample, plus that agent's categorical duration log probability only at T's
t0 decision. Held agents have no fresh action density. For actual velocity
decision mask m_i and the unchanged scalar team advantage A:

`r_i = exp(ell_i,new - ell_i,old)`

`L_policy = -mean_(episode,time)[sum_i m_i * min(r_i*A, clip(r_i,.8,1.2)*A)]`.

Sum over agents **before** averaging primitive rows; never divide by five or
the number of eligible decisions. All-held rows have zero actor term but
retain their critic/recurrent/reward contributions. At the collected policy
this preserves the old unclipped policy-gradient scale, not loss-value
equality or equality of gradients after parameters change. Duration and
velocity remain grouped within their owner, with no separate duration weight
or per-coordinate clipping. Entropy remains the actual-decision sum over
agents, averaged over primitive rows. The new grouping is applied equally
to both learned arms.

Everything else remains fixed: FP32 CPU Linear(108,64)/tanh/GRU-64 actor,
three-dimensional tanh-Gaussian velocity head; T alone has a zero-initialized
two-logit duration head. Common separate critic is 136→128→128→1 with tanh.
Return-to-go uses every primitive native reward, gamma=1, no GAE/bootstrap.
Normalize detached advantages once over each 512-step rollout. Use collected
chunk initial states, 32-step truncated recurrent gradients, four full-rollout
epochs, one joint actor/critic Adam step per epoch (lr=3e-4, betas .9/.999,
eps=1e-8, no weight decay/scheduler), PPO clip .2, value coefficient .5,
entropy coefficient .01 and global gradient clip .5.

This tests amended T versus amended G. It does not causally estimate a
clipping effect against historical B01, diagnose its losses as defects or
claim to implement the full MAPPO framework. The source rationale and
contrary joint-objective evidence are already recorded in P29 intake §8.

## 4. Independent units, seeds and exposure

The two fresh matched training-pair masters are **7001 and 7002**. The
bounded current UCOPE record/source search found no exact match before this
card was written; [preparation facts](UCOPE_UAV_MOTION_PREFIX_B02_PREPARATION_FACTS_20260908.json)
record the search and computed domains, not a universal namespace claim.
Use b=100000*s and the unchanged domains:

| Purpose | Seed |
| --- | --- |
| Common actor-then-critic initialization | b+11 |
| Separate T/G training velocity streams | b+21 |
| T training duration stream | b+22 |
| Training reset e=0..511 | b+1000+e |
| T/G/H evaluation reset e=0..31 | b+2000+e |
| Private T/G evaluation velocity stream per episode | b+3000+e |
| T evaluation duration stream per episode | b+4000+e |

T/G start with equal common parameters and reset inputs, but maintain
separate optimizers, histories and on-policy trajectories; differing action
consumption may diverge streams. No noise replay or common training dataset
is added. The independent training unit is the matched pair, **n=2**.
Agents, episodes, frames and recurrent chunks are not extra training units.

Each fit uses 512 complete training episodes =131,072 team primitive steps,
256 two-episode rollouts and **1,024 actual Adam calls**. Evaluate only final
T/G checkpoints on 32 sampled episodes each. Evaluate H, fixed zero velocity
with no learner/tuning, on those same 32 reset seeds using G's environment.
No best-seed/checkpoint choice, greedy replacement or extra evaluation is
allowed. Run both assigned pairs irrespective of the first valid sign if
later allocated; integrity/cap failures retain the stop rule in §7.

## 5. Native primary, MEI and reading rule

Use `R_t=sum(info['rewards_dict'].values())`; do not use the adapter's extra
per-agent average or recompute reward. Accumulate original native values in
Python float/float64 and set `J=sum_t R_t/256`; learning retains their FP32
representation. For each master s, `Delta_s=mean_e(J_T,s,e-J_G,s,e)` over its
32 whole paired episodes. Primary `Delta=(Delta_7001+Delta_7002)/2`.
Report all T/G/H J values, both pair means, their sample SD, each pair's
conditional evaluation SE and `sqrt(SE_7001^2+SE_7002^2)/2`. Conditional
evaluation uncertainty is distinct from training-population uncertainty.
Do not pool any B01/P21/P24 or finite-host outcome into B02.

**MEI: absolute 0.01 in complete time-average native team reward**, unchanged
from P29 because one percentage point on this 0–1 scale remains meaningful;
for context the coverage term for one continuously served extra user is
.7/50=.014. This is not a measured headroom value or QoS guarantee.

| Reading | Fixed rule and bounded interpretation |
| --- | --- |
| UP | Delta>.01: preliminary advantage of these amended fitted packages under this task/budget; competent-generic and information-path wording require their corresponding evidence. |
| WITHIN | -.01<=Delta<=.01: no gain at the selected scale under this budget; not stable equivalence. |
| DOWN | Delta<-.01: adverse native evidence for this task/prefix/learner budget; local movement or information changes do not compensate. |

There is **no tuned same-information headroom record** on this host. Reuse
the same H reference; it is neither a tuned generic controller nor an upper.
No matching tuned baseline set has been identified. G−H weakness limits
competence wording while leaving trustworthy T−G reportable. Missing optional
diagnostics or resources limit their dependent claims under §11.8.7, rather
than automatically erasing the primary.

## 6. Predictions, contrary evidence and interpretation

Before B02 output: joint reading WITHIN, probability **.60**; both new G−H
means positive, probability **.60**. These retain P29's proposed predictions.
Owner prediction: **not taken (unattended)**. Score against every outcome;
neither prediction creates an extra run or launch condition.

Strongest support is three positive historical T−G pair means and a realized
legal movement/local-information/native-credit path. Strongest contradiction
is 6902's T−G **−0.0503654** and T−H **−0.0332645**, alongside 6901's weak
G−H **−0.0282038** and the outcome-informed four-pair mean **+0.0058553** below
MEI. Retain all four historical signs and their n=4 limits. P21's original
UP, P24's WITHIN, earlier finite-host positives/nulls/harm and actual first
UAV-entry chain stay separate and unchanged.

Above-MEI B02 would motivate bounded continuation of this amended package.
Within-MEI B02 would motivate reassessing this specific combination before
more unchanged seeds. A negative result would favor dropping the amendment
from the next object choice while retaining the harm. The strongest
alternative is that generic feedback benefits equally or more; per-agent
clipping may also permit larger joint updates and worsen co-adaptation.
Geometry, persistence, optimization and information remain unseparated.
None of these branches alone establishes clipping causality, pure information
value, stable superiority, transfer, deployment, family closure or C promotion.

## 7. Work, caps, engineering scope and stop

Two pairs ×two learned arms ×131,072 training steps plus
two pairs ×three evaluation arms ×32 episodes ×256 steps gives
**573,440 team steps**: 524,288 training and 49,152 evaluation. Four fits ×256
rollouts ×four epochs gives **4,096 Adam calls**, with 192 final evaluation
episodes and 2,240 complete episodes overall. Reuse existing selected
diagnostics: 3,200 frames and at most 6,400 local-index calls across both pairs.
There is no candidate search, extra controller forward pass, model ensemble
or diagnostic experiment. Actual counts and exposure, including every failed
attempt, must be retained.

Dense ratio work is 1,024 updates ×512 rows ×five agent terms =2,621,440 per
fit, replacing 524,288 team terms; the extra count is 2,097,152 per fit. The
collected log-probability field grows from 2,048 to 10,240 bytes per 512-step
FP32 rollout, not total peak RSS. Use the existing runner cost law plus this
pointwise/storage increment. Incremental unit wall time is unmeasured;
historical P21 same-loop planning references were 148.27 s for T and 141.37 s
for G including H/publication, and P24 summed complete wall was 564.93 s.
These are context, not timing guarantees or a fivefold whole-run forecast.

Prospective complete caps: **1,800 s/arm, 3,600 s/pair, 7,200 s summed**.
Charge startup/common initialization to T and H/pair publication to G. Use
one CPU FP32 scientific process/thread on the existing remote-first route;
host/device is not itself the estimand. Immediately before any later named
invocation, actual-node resource admission applies as in AGENTS §7. No
admission, warm-up or result-bearing probe is run during P33.

Stop at fixed counts/cap, nonfinite learning or a concrete defect that
prevents faithful reward, information, training or primary measurement.
Preserve complete and partial facts and record a cap breach. No retry,
replacement seed, resumed training, extra evaluation or automatic cap increase
is allocated. Missing resource telemetry is `resources_unmeasured`.
Only evidence-spec §11.4's integrity, nonzero learner counts, resource
admission and exposure requirements may hold a later B launch.

Engineering scope §4: **none**. Use existing source and ordinary scientific
algorithm identity, counters, files and checks; no framework, versioning
layer, registry, validator, resume, worker or resource machinery. Source
additions ≤2,000 lines, runner ≤600, focused directory tests ≤300 s and one
synthetic runner smoke ≤60 s remain the engineering bounds.

## 8. Prepared implementation handoff

The [complete code specification](UCOPE_UAV_MOTION_PREFIX_B02_CODE_SPEC_20260908.md)
binds starting source `b5607f46fea91379582af8bf87e60b61bc4a269b`, exact owned
paths, grouping/storage/reduction, route/result identity and original focused
checks with independent credit review. The [five-item CM task](UCOPE_UAV_MOTION_PREFIX_B02_CM_TASK_20260908.md)
is prepared for Root. The [preparation intake](UCOPE_UAV_MOTION_PREFIX_B02_PREPARATION_INTAKE_20260908.md)
records delegated choices and the owner item. Publication does not dispatch
CM, accept an implementation or create a new UAV-validation entry.

## 9. P47 allocation and implementation binding — 2026-09-08

OWNER_DIRECT P47 at `6dd7570e9e8045fb3818c553953a92c9caa587cb`
supersedes P33's preparation-only boundary for this selected object: fresh
configured CM implementation/review, then masters **7001 followed by 7002**
under §§2–7's unchanged counts, primary, predictions and 1,800/3,600/7,200s
complete caps. It authorizes no fourth CM comparison, third pair, replacement
seed, scientific retry, extra evaluation or automatic successor. The original
P33 card at `1d46ddc2b142a2c2b98922a8f46e2d2609bda859` remains the prospective
scientific definition; this section records allocation and actual state.

Implementation source `6374063408208ba67b8cb7c69ebc0babb0f00259` is committed
and pushed in the existing `codex/ucope` checkout. The [CM technical record](UCOPE_UAV_MOTION_PREFIX_B02_TECHNICAL_ACCEPTANCE_20260908.md)
reports 53 passing focused tests, a complete 80-step/eight-Adam/zero-UAV
synthetic fixture, and independent credit review without a material credit
defect. It also records the **80.578s fixture wall against the 60s engineering
bound**. The overrun remains a conformance fact; no repeated smoke, unique
cause, or conforming time is asserted. The [implementation intake](UCOPE_UAV_MOTION_PREFIX_B02_P47_IMPLEMENTATION_INTAKE_20260908.md)
separates functional source correspondence from that original timing gap.
**P48 at `209804f8bb8120394c0dc14bf346133aa525d512` accepts the existing
functional source and publication evidence for this named task**, preserving
the overrun and removing the demand for another ≤60s fixture. It authorizes
no repeat, warm-up, profiler or speculative patch. The [exact Root route](UCOPE_UAV_MOTION_PREFIX_B02_P47_ROOT_HANDOFF_20260908.md)
now proceeds under the unchanged P47 scientific allocation and caps;
prepared commands still do not assert an actual accepted launch.

[Machine-generated binding facts](UCOPE_UAV_MOTION_PREFIX_B02_P47_BINDING_FACTS_20260908.json)
retain the original work/RNG/cost law and actual fixture exposure: four Adam
calls per arm at lr=3e-4, total relative displacement T=0.018104414 and
G=0.018726143. These establish synthetic learner movement, not UAV performance
or its runtime. The real per-fit budget remains 1,024 Adam calls on
66,441/66,311 T/G parameters. Actual real exposure and both native endpoints
remain unmeasured here; owner predictions remain not taken. The prior UAV
entry, historical joint objectives/results and no-tuned-headroom limit remain.
