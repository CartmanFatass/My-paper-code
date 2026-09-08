The existing native UAV learner admits one same-information hold-conditioned critic comparison with the duration-capable actor held fixed.
Binding MARL structure: (b) temporal abstraction or termination; five co-adapting agents retain separate partial-observation histories.

# P49 source intake and one proposed native hold-value question

Status: source-backed preparation, **no selected new family/object and no performance result**.
P49 authorizes this preparation and one conditional Convergence consultation, not its conclusion.

## 1. Assignment, source and retained boundary

[P49](../../portfolio/handoffs/2026-09-08-p49-vspc1-native-value-question.md) is the
current OWNER_DIRECT command. The designated checkout is
`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`, branch `codex/direction-vsp_c1`.
It began clean at `4b1759c5f44fa3b7382137f71e0084af2cd218b4`. Current committed
instruction/input copies from main `65883d41d1ba2cb481adfe34d23436803ed5260a`
were committed/pushed as `e050c8990` and `31e1559fa`; these are input synchronization,
not UCOPE source edits or new authority. No unrelated work was present or removed.

The P10 yield's open-question/limits and completed service-allocation intake §§4–5
remain binding at their own scope. Rule J=0.785196940 exceeded FACTOR=0.758911133
and GENERIC=0.752400716; the learner difference +0.006510417 was below MEI .025.
No old rule evaluation, seed, similar queue host, public-plan family or A01/D6
boundary is reopened. K4 remains open; ACTIVE/MEDIUM and recasts are unchanged.
The Portfolio direction/headroom rows still describe the earlier incomplete
service-allocation result; P49 and the complete intake supply the current task/facts.
Portfolio owns that factual refresh; this document makes no Portfolio edit.

The new concrete input is read directly with `git show` at implementation
**6374063408208ba67b8cb7c69ebc0babb0f00259**, integrated on main at `d911f8346`:

- [environment.py](https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py): `make_real`, feature assembly and `HoldState`.
- [policy.py](https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py): `Actor`, `Critic`, `templates`, `arm_copy`, `sample`, `joint_terms`.
- [learner.py](https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py): `collect_episode`, `returns_to_go`, `recurrent_outputs`, `update`.
- [study.py](https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/study.py): B02 configuration, serial fitting, sampled endpoint, hover and counters.
- The concrete observation/reward question required expanding into
  [uav_env.py](https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/envs/pettingzoo/uav_env.py)
  (`step`, `_get_state`, `_get_observation_vectorized`, local-entry methods,
  `_compute_reward`) and
  [env_adapter.py](https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/envs/pettingzoo/env_adapter.py)
  (`reset`, `step`, `_state_array`). No module was imported or executed.

The [machine facts](VSPC1_NATIVE_HOLD_VALUE_P49_PREPARATION_FACTS_20260908.json)
record source symbol ranges and arithmetic. UCOPE [B02 card §§2–7](../ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md)
and [P24 intake §§2–5](../ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md)
are input evidence. Source availability is not UCOPE B02 outcome evidence.

## 2. Actual information, ownership and credit consumers

| Boundary | Direct source observation and its implication |
| --- | --- |
| Native event | Five UAVs, 50 uniform-layout users, 256 one-second steps, area 1000 m, heights 50–150 m, component speed 30 m/s, free-space/vectorized channels, no shadowing/FDMA/paper reward. Velocity updates position with physical bounds, then channel/service, reward and next observation. No forced event, toy replacement or environment change is proposed. |
| Actor information | 104 local values: own normalized xyz; 20 sorted local-user slots of relative xy and normalized SINR; 10 local-UAV slots of relative xyz and normalized SINR; normalized primitive time. Append own previous command xyz and remaining hold/4: 108 values. Source-index diagnostics are not actor inputs. Slots are SINR-sorted observations, not persistent entity IDs. |
| Critic information | Normalized 116 global-state values (15 UAV positions, 100 user coordinates, time), plus five ordered blocks of prior command xyz and remaining hold/4: 136 values. This is existing centralized training information. It does not enter the actor and will not be enlarged. |
| Owned action | A shared-weight actor maintains five separate GRU histories. Each UAV samples its three-coordinate tanh-Gaussian velocity at an eligible decision; duration 1 or 4 is sampled **only at t=0** when its duration head exists. A long choice holds the opening command through t=3; every agent returns to ordinary feedback by t=4. No new termination, renewal or duration menu is proposed. |
| Timing | Features/value are assembled **before** current sampling. At t=0 every remaining value is zero; the proposed critic cannot condition the opening baseline on the just-chosen duration. Remaining holds can be nonzero only at t=1,2,3. At each held step observations, GRU state and native reward still advance. There is no observation censoring or chunk-length-as-duration interpretation. |
| Reward | Base default reward is .7 times served connections/50 plus .3 times mean normalized SINR quality. Base per-agent rewards divide it by five; `team_reward` sums those original values. The adapter's extra average is ignored. Primary is the complete primitive time average, not movement, prefix reward, an information statistic or a recomputed reward. |
| Value consumer | One scalar feed-forward critic is evaluated each primitive step. Full-episode return-to-go uses all actual rewards, gamma=1, no terminal bootstrap and no GAE. Collected value is subtracted, and detached advantages are normalized once over 512 primitive rows. No duration-Q table, counterfactual rollout or value-based action search exists. |
| Actor/critic coupling | B02 uses one compound PPO ratio per actual agent decision, duration plus velocity at its t0 decision, with held agents masked. The common scalar advantage is used for every acting agent, sum before row mean. Four full-rollout epochs use one joint actor/critic Adam call each and a **joint global gradient norm clip .5**. Thus a changed critic can affect both later advantages and the clipping scale applied to actor gradients. Critic MSE also learns on all-held rows. |
| Recurrence and population | Actor 108→64/tanh/GRU64, 32-step recurrent gradient chunks with collected initial states; critic has no recurrence and receives no actor hidden state. Five persistent agents co-adapt; no join/leave/rejoin, replacement, survivor-state, variable-roster or transfer claim. Primitive-time credit is retained, without extra skip transitions or duration reweighting. |

**Inference:** this interface supports a narrow comparison of explicit hold-conditioned
value features against generic nonlinear value sharing. It cannot support a claim that
the current duration decision was chosen by a duration-conditioned critic. Its legitimate
route is past hold/command and native state → value estimate → subsequent normalized
advantages and joint clipping → updated local recurrent policies → native trajectories.
The proposed change has no direct actor-input or action-law intervention.

## 3. The sole candidate: GATED-V versus MLP-V

Both arms use **the same existing duration-capable actor**, including its initially
zero two-logit duration head, t0 duration {1,4}, eligible velocity masks and B02
`agent_compound` PPO. MLP-V is the exact full 136→128→128→1 tanh critic; it already
shares features across durations and can learn interactions. It is not a duration-blind,
smaller, separately tabulated or deliberately weakened control. Both actors can learn
d=1 and then act every step; both can repeat commands or hover. UCOPE's historical
primitive-only G is a different policy package and is **not** renamed as this comparator.
No superiority over that wider feedback package is requested.

Partition the existing critic input without losing/reordering its meaning: `r` is the
five remaining-hold/4 fields; `x` is the other 131 values (state and prior commands).
Write the generic first preactivation as `z = W_x x + b1`, with `B r` its ordinary
remaining-hold contribution. GATED-V replaces only the first hidden layer:

```text
MLP-V:   h1 = tanh(z + B r)
GATED-V: h1 = tanh(z * (1 + A r) + B r)
both:    V  = W3 tanh(W2 h1 + b2) + b3
```

`A` is one bias-free 5→128 linear map, initialized to zero. All common parameters
are copied from the same source initialization, including critic columns and actor.
No new RNG draw is needed for the zero gate. GATED-V has 34,817 critic parameters
versus 34,177; both actors have 32,264. Extra capacity is 640 parameters (1.87% of
the critic, 0.96% of the generic complete learner), explicitly part of this B package.
The generic function is contained at A=0. Numerical initialization correspondence
needs an ordinary FP32 check, not an exact scientific theorem or bit-equality gate.

The gate shares native state/command features across observed remaining durations and
allows those durations to modulate the features multiplicatively. It is **not** a
strict low-rank value theorem, inter-agent value decomposition, option-specific Q,
unseen-duration generalization or a separation of shared from unshared learning.
At most three rows per episode have nonzero r; their actual count depends on sampled
durations and must be reported, not forced. A nonzero A gradient can change joint
gradient clipping from the first update even when both starting values agree.

This separates the question from UCOPE's treatment-versus-feedback action package and
its per-agent clipping amendment, which is held common here; it also separates it
from FSD's applied-renewal intervention, since hold timing/action execution is unchanged.
The strongest null is that the full MLP already captures all useful hold structure at
this budget. Extra capacity, critic optimization and actor-step scaling remain
alternatives to a uniquely causal value-sharing explanation, even if native return rises.

## 4. Smallest proposed B, exposure, cost and interpretation

Proposed name: `VSPC1-NATIVE-HOLD-VALUE-B01`; **not selected or frozen**.
One fresh matched training-pair master **8101**, two real fits. The bounded current
UCOPE/VSPC1 Markdown/source search found no exact-word use of that master; no universal
seed-namespace claim is made. Use the existing b=100000*s domains: common initialization
b+11, per-arm private train velocity b+21 and duration b+22, training resets b+1000+e
(e=0..511), evaluation resets b+2000+e and private velocity/duration streams b+3000+e /
b+4000+e (e=0..31). Pairing matches initial common parameters and exogenous reset inputs;
on-policy trajectories, optimizers and random-stream consumption may diverge.

Preserve the source learner: 512 complete episodes ×256 steps per fit, two episodes
per rollout, 256 rollouts ×four epochs =1,024 actual Adam calls per fit. Learning rate
3e-4, betas .9/.999, epsilon 1e-8, no decay/scheduler, value weight .5, entropy weight
.01, PPO clip .2, joint gradient clip .5, CPU FP32/one scientific process/thread.
Primary is final sampled GATED-V minus MLP-V J on 32 matched whole episodes.
Evaluate fixed zero-velocity H on those same 32 resets once; it has no model, tuning
or selection and is an attained reference, not an upper or competent tuned baseline.
No checkpoint, seed, metric or architecture selection and no second pair is requested.

The independent unit is the matched training pair, **n=1**. Report each complete
arm/H J, all 32 paired differences and conditional evaluation SE. That SE does not
estimate training-population uncertainty. Retain training summaries, actual update
counts, parameter displacement, final checkpoints, duration decisions and sampled
long-hold frequency. Count existing nonzero-hold rows from collected inputs. There
is no extra actor/critic call for that count. Local-index/frame diagnostics are not
needed for this value/native-return claim; no new information-value conclusion uses them.

**Prospective MEI: absolute .01** complete time-average native team reward. One extra
continuously served user contributes .7/50=.014 from the coverage term, making .01 a
legible finite-budget improvement scale. This is a rationale, not measured headroom,
a deployment requirement or a promise of attribution. Tuned same-information
upper/baseline headroom is **absent**. Historical G/H evidence is reusable context;
the old G actor law and old clipping differ, so it is not a matched baseline set for
this new pair. Missing headroom is not a prerequisite or the reason to decline it.

Proposed descriptive reading: Delta>.01 motivates one or two independent paired
training seeds with every sign retained; -.01≤Delta≤.01 supplies no selected-scale
gain in this instance and motivates stopping this object before unchanged repeats;
Delta<-.01 is adverse evidence for this gated package at this budget. GATED-V/MLP-V
losses to H stay visible separately. A native loss is not rescued by critic fit,
duration usage or movement. These are proposals for the node to select, not a result
or a silent family-close rule. Working prediction: WITHIN, probability .65; owner
prediction not taken (unattended). It cannot be scored before any selected run.

Tool-computed work: two fits ×131,072 training steps +three final arms ×32×256
evaluation steps =**286,720 native team steps**, 2,048 Adam calls, 96 evaluation
episodes, 1,120 complete scored episodes and two constructor resets. Per fit,
at most 512×3=1,536/131,072 training rows (1.171875%) carry nonzero remaining holds;
all 2,560 opening duration decisions occur with r=0. The gate adds one 5→128 map
and 128 element products to an existing critic forward; there is no extra model,
rollout, ensemble, candidate/trajectory search, solver or controller call.

Per-arm cost law stays initialization +131072*c_env_actor +1024*c_update +8192*c_eval
+publication; the second arm additionally carries 8192 hover steps and pair publication.
Gate arithmetic and having the duration-capable actor in both arms are explicit
increments with unmeasured unit wall time. P21 observed planning references were
148.2671 s for T and 141.3719 s for G including H/publication; P24's two complete pairs
sum to 564.93 s. These indicate the scale of the reused loop, not an exact forecast
for the new pair or a guarantee. Proposed complete caps are **1,800 s per learned
arm and 3,600 s for the pair**, startup charged to the first arm and H/publication
to the second. No extra calibration, timing probe or diagnostic experiment is proposed.

Preparation exposure is machine-recorded **zero** model constructions, simulations,
profiling, training, evaluation or scientific invocations. The exposure line reuses
historical UCOPE's observed total relative displacement range .518345–.598358 only
as evidence that the existing learner moved; it is not a measured new gate/seed result.
The proposed new fit's displacement must be recorded by its actual execution.
An exact maximum or finite search would not answer the finite-budget training question
better and is not needed before this direct B comparison (§§11.8–11.9).

Engineering scope §4 needs **none**. Future implementation, if selected, should reuse
the native environment, actor and learner without editing UCOPE or core; a small VSPC1
critic/study entry and focused checks would carry the different arm names and budget.
Ordinary limits: 2,000 new non-test lines, 600 runner lines, five minutes focused tests,
one bounded synthetic engineering smoke if needed for changed plumbing (never UAV evidence).
No implementation or check is run now. Use the existing remote-first exact-commit route
for any later authorized scientific run; host/device is not itself the estimand.
Stop at fixed counts/cap or a defect threatening reward/information/training/primary,
preserving partial facts. No retry, replacement seed or added evaluation is allocated.

## 5. Existing literature and what it changes here

Question: does the prior duration/credit literature justify a duration-value consumer
or privileged timing information that this actual primitive-step critic does not have?
Reuse the verified passages in [reactive proposal §5](VSPC1_K4_REACTIVE_QUEUES_PROPOSAL_20260906.md)
and [service-allocation question §5](VSPC1_K4_SERVICE_ALLOCATION_QUESTION_20260907.md).
The current formal Inst-sci catalog query reads 190 real-paper records and recovers
the relevant titles; a metadata hit alone is not scientific support. The prior My-lib
CLI had two synthetic fixtures and no real page/semantic rows; those fixtures remain
excluded. No claim is made that a unified real search index now exists, or that the
libraries exhaust prior work. No new paper download or broad survey was commissioned.

- Jung et al., ACAC, ICML 2025, `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0449.json`,
  pp2–3, elements405/410/415–416: its macro-observation/credit timing motivates mapping
  actual availability. Here fresh primitive observations and GRU updates continue
  during holds; imposing ACAC's action-completion-only observation law would change
  this experiment. No ACAC architecture or claim is imported.
- Lee et al., UTE, AAAI 2024, `.../json/VS-0005.json`, p3 elements95–100/120–146:
  actual extension and additional skip-transition exposure are distinct. The present
  comparison adds neither unrealized duration targets nor extra training transitions.
- Liang et al., *Asynchronous Credit Assignment for Multi-Agent Reinforcement Learning*,
  IJCAI 2025, `.../json/MARL-0530.json`, pp1–2 elements126–133: inter-agent multiplicative
  dependency is not evidence of useful duration conditioning in this scalar critic.
  It does not select value decomposition or a factorization theorem for this B.

These verified limitations **narrow** the proposal to the actual baseline/optimization
consumer. They provide no native value-gate gain, novelty verdict or mandatory
mechanism proof. CM would need only the fixed native source pointers and this timing
boundary, not the paper set or old queue implementation.

## 6. Support, contradiction and the single direction decision

Support: an existing real actor/learner/evaluator already accepts hold-conditioned
centralized values and produces native outcomes; the gate has a legal, unchanged-information
path into actual learning, and the full generic null is retained. Historical UCOPE
has three positive T−G pairs and realized movement/local-input changes. These facts
motivate asking about the interface; they do **not** support this new gate's effect.

Contradiction: P24 master6902 had T−G **−.0503654225** and T−H **−.0332644846**;
master6901's +.0433518665 was against G−H **−.0282038164**. P24 mean −.0035067780
and the outcome-informed four-pair mean +.0058553213 were within MEI. Larger opening
displacement occurred in both signs. The present gate additionally acts directly on
very few rows, and the MLP already shares across all holds. A generic improvement
from optimization/capacity is a surviving explanation; practical benefit is unknown.

### Decisions this source intake produces

| Option | Recommendation / action |
| --- | --- |
| (a) Put this one exact proposed B to the existing Convergence node | **Recommended and executed as the P49 consultation preparation.** It resolves whether this specific value path warrants a first native B; no new family or run is locally selected. |
| (b) Return a source/meaning-based yield now | Not recommended: the source supplies a real legal value-to-credit-to-native-return path and an intact generic comparator. Few affected rows/uncertain gain are material objections for the one authorized decision, not missing-interface facts. |
| (c) Repeat the service-allocation object, implement the gate, or run a diagnostic now | Outside P49; not executed. |

This is an **OWNER_DIRECT preparation action**, not a delegated local new-family
decision. The proper direction-tier question is exactly: **select the proposed
native hold-value family and one B object, or retain the current no-successor
position because this specific comparison lacks sufficient decision value?**
P49 authorizes that one consultation. The node's answer must be complete and conform
to current owner instructions/evidence §11 before a selected card/CM specification
is prepared. A transport/evidence blocker produces no decision; no substitute host,
extra consultation, C freeze, lifecycle/priority action or actual UAV entry follows.

At this clean boundary `item.py reviews --json` on both designated checkout and main
returned `[]`; relevant main 2026-09-08 VSPC1 audit owner cells were absent/empty.
No override or prediction reply was invented. A technical audit row records this
preparation. No new-card/direction-decision owner item is due before the node decides.
The [Chinese source brief](../../portfolio/owner/briefs/vsp_c1/2026-09-08_P49-NATIVE-HOLD-VALUE-SOURCE.md)
is explicitly a source result, not a learning result. DIRECTION remains unchanged
because no new mechanism-level conclusion has been accepted.

Next route: commit/push one fixed TASK/HANDOFF on this shared branch → Root → existing
Transport → Root → this DM. Park preparation at that clean boundary. The DM reads
the complete immutable response, checks scientific/spec meaning, records intake,
and prepares any selected card and full common CM specification. **No CM dispatch
is authorized during preparation.** Root receives the exact spec/task/source and
original checks before any later eligible five-arm comparison/implementation dispatch.
