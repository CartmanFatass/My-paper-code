Question: does a remaining-hold gate in the existing centralized critic improve sampled native return over the full MLP critic at the same fixed learning budget?
Binding MARL structure: (b) temporal abstraction or termination, with five co-adapting agents retaining separate partial-observation histories.

# VSPC1-NATIVE-HOLD-VALUE-B01 — prospective B/EXPLORE

## 1. Selection and claim ceiling

Selected by the complete `em:vsp_c1:convergence` response at
`7ac8ccb01543f82715f38ad33d846c2ec649ecc2`, request
`2026-09-08-vspc1-native-hold-value-convergence-01`, **PRO_FINAL**
([immutable response](pro_packets/20260908_native_hold_value_convergence/archive/RESPONSE.md),
[DM intake](VSPC1_NATIVE_HOLD_VALUE_CONVERGENCE_INTAKE_20260908.md)).
The OWNER_DIRECT P49 continuation at `dff0694dc` authorizes implementation,
independent review, accepted-source binding, this single pair, collection and intake
([current handoff](../../portfolio/handoffs/2026-09-08-p49-vspc1-native-value-question.md)).
At continuation entry, no code acceptance, scientific launch or formal
UAV-validation entry has occurred.

This one matched training pair can produce a local finite-budget native-return
signal or counterexample for the gated critic package. It cannot establish stable
superiority, equivalence, unique sharing causality, strict low rank, optimality,
unseen-duration/roster transfer, safety/deployment, or superiority to UCOPE's
historical primitive-only G. B has no consumption state. Earlier service-allocation,
public-plan, two-queue and A01/D6 boundaries remain unchanged; no recast or Portfolio
priority/lifecycle action is selected.

## 2. Host, information, ownership and actual value consumer

Reuse the native source at **6374063408208ba67b8cb7c69ebc0babb0f00259**:
`experiments/candidates/ucope/uav_motion_prefix_b01/{environment,policy,learner,study}.py`.
The [source question §2](VSPC1_NATIVE_HOLD_VALUE_P49_QUESTION_20260908.md#2-actual-information-ownership-and-credit-consumers)
maps the actual symbols and fixed links; the [CM specification §1](VSPC1_NATIVE_HOLD_VALUE_B01_CM_SPEC_20260908.md)
identifies the available complete source and current-main dependency gap.

Five fixed UAVs, 50 uniform-layout users, 256 one-second steps, 1000 m area,
height [50,150] m, component speed 30 m/s, free-space/vectorized channels;
retain all `make_real` settings, the base `MultiUAVEnv` and `ParallelToArrayAdapter`.
No environment/physics/adapter change, forced event, new sensing charge or toy
replacement is permitted. Velocity → bounded position → channel/service → owning
agent's next local observation → recurrent policy/action → native team reward is
the realized control path. Membership is fixed; there is no join/leave/rejoin,
replacement, survivor-state or variable-population claim.

Both actors receive the same 104 local values: own normalized xyz, 20 SINR-sorted
local-user slots (relative xy and SINR), 10 local-UAV slots (relative xyz and SINR),
and normalized primitive time; append own prior normalized command xyz and
remaining hold/4, yielding 108. Slots are observations, not persistent IDs.
No centralized state, source-index diagnostic or future/just-chosen duration enters
an actor. Shared actor weights retain five independent GRU histories, advanced at
every primitive step including holds.

The critic receives existing normalized global state116 plus five ordered blocks
of prior command xyz and remaining hold/4: 136 inputs. Assemble these before current
sampling. Each agent chooses duration1 or4 **only at t=0**; d4 holds its opening
velocity through t3, then all agents resume primitive feedback at t4. d1 resumes
feedback at t1. At t0 remaining holds are all zero. Their only possible nonzero
rows are t1,t2,t3, with values3/4,2/4,1/4 for a long hold. No current duration is
backfilled into its own baseline. Original observations/rewards continue during holds.

The critic is scalar and feed-forward. Complete primitive native rewards form
gamma1 return-to-go, without GAE or terminal bootstrap. Subtract collected values,
then normalize and detach advantages once over each512-row rollout; all four
epochs reuse those advantages. The value affects subsequent collected baselines
and also the **joint actor/critic gradient clipping scale in the current step**.
There is no duration-Q or value-based action search. All-held rows retain value
loss, recurrence, rewards and advantage-normalization weight; their actor term is zero.
Direct gate sparsity3/256 is not a bound on its possible complete-return effect.

## 3. The exact two learned arms

Names/order: **GATED-V**, then **MLP-V**. Both receive the existing duration-capable
actor (108→64/tanh/GRU64; three-coordinate tanh-Gaussian head; zero-initialized
two-logit duration head). Both use identical actor/action laws and the B02
`agent_compound` objective. MLP-V is the full original136→128→128→1 tanh critic,
with all information and nonlinear sharing retained. UCOPE's no-duration G and
old two-seed aggregation must not be reused as this comparator or primary.

Let r be input indices119,123,127,131,135 (zero-based); x is the other131 values.
Preserve every first-layer column's original field. For z=W_x x+b1:

```text
MLP-V:   h1 = tanh(z + B r)
GATED-V: h1 = tanh(z * (1 + A r) + B r)
both:    V  = W3 tanh(W2 h1 + b2) + b3
```

A is a bias-free5→128 map initialized exactly to zero without random sampling.
Copy every common parameter from the same original `templates(seed)` initialization
(actor before critic), with independent models/optimizers. Both duration heads start
at zero. Each actor has32,264 parameters; MLP critic34,177, GATED critic34,817;
complete learners66,441 and67,081. The extra640 parameters and changed optimization
are part of the treatment, not a controlled-away capacity effect. The MLP is
contained at A=0 mathematically, with an ordinary FP32 correspondence check.
No identical-update, non-inferiority or unique-factorization claim follows.

This preserves UCOPE's compound clipping as common infrastructure; neither clipping
nor its old duration-versus-feedback action package is the treatment. FSD's renewal
execution is untouched. The strongest null is that the full MLP already learns the
useful hold structure; capacity, normalization and joint clipping remain alternatives.

## 4. Training, sampling and independent unit

One fresh matched training-pair master **8101**, with b=810100000. The bounded
committed source/Markdown search is in the existing preparation facts; no namespace
registry or universal seed-use claim is needed.

| Purpose | Exact domain |
| --- | --- |
| Common initialization | b+11 |
| Private per-arm training velocity / duration streams | b+21 / b+22 |
| Training resets, e=0..511 | b+1000+e |
| Final learned/H evaluation resets, e=0..31 | b+2000+e |
| Private learned evaluation velocity / duration streams per episode | b+3000+e / b+4000+e |

Each fit has512 complete training episodes ×256 team steps =131,072 training steps;
256 two-episode rollouts, four full-rollout epochs each, **1,024 actual Adam calls**.
Preserve32-step truncated recurrent gradients with collected chunk initial states,
lr3e-4, betas(.9,.999), eps1e-8, no decay/scheduler, value weight.5, entropy weight.01,
PPO clip.2 and joint gradient norm clip.5. Per-agent compound densities group
velocity coordinates and that agent's t0 duration together; mask held agents,
sum agent surrogates before averaging every primitive row, without division by
five or the active count. Both collection and update must explicitly pass
`ratio_grouping="agent_compound"`.

Evaluate only the final fixed-budget sampled policy,32 episodes per learned arm.
Then H sends fixed zero velocity on the same32 resets using MLP-V's environment;
H has no model, training or tuning. No greedy replacement, initial/intermediate
evaluation, best checkpoint, extra seed, replacement call or outcome selection.
Pairing matches common initialization and exogenous reset inputs; on-policy data,
histories, optimizers and stream consumption can differ. The independent unit is
**one matched training pair, n=1**. Agent/time/episode/update counts are not new n.

## 5. Native measurement, headroom, reading and predictions

Use the original `sum(info['rewards_dict'][a] for a in the five agents)`, not the
adapter average. Accumulate native rewards in Python float/float64; training retains
FP32 reward/target representations. J=sum of256 rewards /256; the critic target
is the unaveraged return-to-go. Primary Delta is mean of32 paired
J_GATED−J_MLP differences. Retain the three J lists, all paired GATED−MLP,
GATED−H and MLP−H differences, their means and each sample-SD/sqrt(32) conditional
SE. They share data; no training-population uncertainty is estimated from n1.

**MEI: absolute .01** in complete time-average native team reward. Coverage of one
additional continuously served user contributes.7/50=.014, giving a concrete scale;
the quality term can also change, so this is no fixed-user-count guarantee.
Tuned same-information upper/baseline headroom is **absent**. H is an attained
reference, not tuned or optimal. Historical UCOPE G has a different actor/clipping
package and is not a matched baseline result for this object.

| Observation | Selected bounded reading and next implication |
| --- | --- |
| Delta>.01 with trustworthy primary | UP: one local native signal for the complete gated package; consider, but do not automatically allocate, one or two independent paired fits. Preserve H comparisons and every adverse episode. |
| -.01≤Delta≤.01, including endpoints | WITHIN: no selected-scale benefit in this instance; retain sign/SE and stop at this object boundary, without declaring equivalence or extending training/evaluation. |
| Delta<-.01 | DOWN: native counterexample for the gated package at this budget; prefer MLP-V for this specific choice. No K4-wide negative follows. |
| One/both learners below H | Retain trustworthy Delta, but narrow usable-control wording. Even an UP does not automatically justify another pair; do not rescue it by ignoring H. |
| Conditional SE leaves an MEI boundary unclear | Report point-estimate region and conditional noise separately; no training-population conclusion or automatic extra episodes. |
| A primary dependency is incomplete | No dependent performance judgment; preserve independent counts/returns. Missing H alone leaves a trustworthy primary pair reportable, with H-relative use unresolved. |

The narrative is finite-budget performance exploration: a positive native package
signal may justify bounded repetition, inside-MEI gives no local reason to repeat,
and a negative favors the intact MLP. Gate fit, sampled long duration, displacement
or movement cannot compensate native harm. Natural low hold exposure does not permit
forced d4, adding just-chosen duration, a new actor or another host.

Working prediction: **WITHIN, probability .65**. Score its point-estimate region
after a complete pair; UP or DOWN both miss. One probability realization cannot
establish calibration. Owner prediction: **not taken (unattended)**.
Strongest prior contradiction is UCOPE6902 T−G−.0503654/T−H−.0332645, with6901 weak
G−H−.0282038; its outcome-informed four-pair mean+.0058553 is below MEI. Old three
positive pair means and the legal source path are motivation, not new gate evidence.

## 6. Work, exposure, scope and complete stop

Machine arithmetic remains in
[P49 preparation facts](VSPC1_NATIVE_HOLD_VALUE_P49_PREPARATION_FACTS_20260908.json).
Two fits ×131,072 train steps plus three arms ×32×256 evaluation steps gives
**286,720 native team steps**,2,048 Adam calls,96 final evaluation episodes,
1,120 complete scored episodes and two constructor resets. Each learned arm has
2,560 training duration decisions; training velocity decisions lie in647,680..655,360.
At most1,536/131,072 training rows per fit have nonzero r; preserve actual counts
from existing collected inputs, without extra model calls or exposure thresholds.
There is no candidate/trajectory/solver search or additional critic forward.

Preserve actual transitions, updates, reset counts, training summaries/losses,
checkpoints and initial/final norms/displacement. Report the zero-initialized gate's
**absolute** norm/displacement; its relative displacement is undefined, not a ratio
to a fabricated epsilon. Existing common/total norms support their defined ratios.
The machine exposure line cites old UCOPE total relative displacement.518345–.598358
as historical can-move evidence only. Current new-model/training/evaluation exposure
is zero. An actual run must supply its own counts and movement, with no arbitrary
minimum gate displacement or long-hold fraction required.

Cost law per learned arm: initialization +131072*c_env_actor +1024*c_update
+8192*c_eval +publication; MLP-V also carries8192 H steps and pair publication/readback.
Gate adds640 multiply-adds and128 products per existing critic forward; actual
incremental wall remains unknown. Historical P21 planning references148.2671s/141.3719s
and P24 two-pair wall sum564.93s indicate only reused-loop scale, not a new forecast.
No timing calibration or separate diagnostic experiment is selected.

Complete caps: **1,800s per learned arm,3,600s per pair**, serial GATED-V then MLP-V.
Charge process startup/common initialization to GATED-V; H and final publication,
readback/exit to MLP-V. Keep the full logical invocation in its budget, with no
timer resets, slices, suspended accounting or borrowing between arms. Preserve an
indivisible overrun as a breach. Fixed counts, cap, nonfinite learning or a defect
threatening reward/information/training/primary ends execution and preserves partial
evidence. No retry, H completion, replacement seed or extra evaluation is allocated.
A first valid arm's sign never selects whether the second runs.

Use the existing remote-first route, CPU FP32/one process/one scientific thread;
host/device is not the estimand. Actual-node resource admission immediately precedes
the complete invocation; missing/failed admission refuses it. Optional resource
telemetry gaps are `resources_unmeasured`, not retroactive primary invalidation.
Only evidence §11.4's four requirements hold a B launch.

Engineering scope §4: **none**. Source≤2,000 new non-test lines, runner≤600,
focused tests≤300s; at most one≤60s synthetic runner smoke under the engineering
assignment. The earlier preparation had zero code/test/scientific execution.
The full specification and original acceptance commands were supplied to Root.
The three-batch CM comparison is complete (`a6dbacb36`); this continuation uses the
normal CM route, with no fourth comparison or added scientific arms or calls.
