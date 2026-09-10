Claim under test: a fixed direct input of each vehicle's own applied acceleration into its motion mean may improve complete native service over the same-information direct-mean learner at equal training exposure.
Binding MARL structure: systems / information flow. The own-input path acts under partial observations, moving partners and role-owned recurrent state; this is a control parameterization hypothesis, not an identified uniquely multi-agent advantage.

# DISH-OWN-COMMAND-MEAN-B07 — frozen B/EXPLORE card, 2026-09-08

## 1. Question, authority and ceiling

Does OWN_COMMAND_MEAN improve the four-condition mean of complete update16 modal native
service over a newly trained DIRECT_MEAN comparator in one matched seed127 pair?

The direction decision is complete **PRO_FINAL** at immutable
`ddb4c9ff20167837c99d146b2177c3e784066411`,
`pro_packets/20260908_p53_own_command_mean/archive/RESPONSE.md` §§二–七, accepted in
`DISH_P53_NATIVE_PROPOSAL_SOURCE_INTAKE_20260908.md` §9. Root's subsequent named route
requests this card and full CM specification only. This freeze constructs no model or RNG
master, launches no CM or experiment, and adds no seed exposure or Pro Send.

Class: **B/EXPLORE**, outcome-informed after P52/P53 and B06, prospective for this named
pair. One paired training root is the independent unit. Four conditions, two arms and
initial rows do not create additional independent training pairs. The ceiling is a finite
native-service signal on the accepted A03 information/ownership host, with no training-
population interval, stable superiority, unique cause, safety, source-value or UAV-transfer
claim. A and B have no consumption state; the frozen definition does not turn this into C.

Strongest support is the verified existing own-input path in live and recorded replay and
a competent same-information learner comparator. Strongest contradiction: the network
already sees this input, native projection already limits applied slew, and persistence
can retain an unhelpful acceleration. Other certification conditions may remain limiting.
The verified literature caution in source intake §6 is reused; it does not establish this
mean's effectiveness or novelty.

Preserve P52/post-B06 and P53 contrary evidence: B06's complete sampled-minus-modal
−77.5 service mean and condition means −92.5/−41/−94/−82.5; modal/sample invalid-commit
means 3.5/31.875; sampled energy +4642.6427; zero legal transfers in all 16 reference/final
rows. Training separately has 1030 invalid commits, 3 separation breaches and 35 terminal
events. Two individual sampled wins (+14/+3), modal/initial +292.5 and sampled/initial +215
with TERRAIN/K8 −57 remain visible. The last comparison mixes learning and execution law.
B04/B05 positive LR means and their adverse conditions remain separate, including B05's
−277 condition/209 invalid commits and B04's initial-relative loss/early termination.
These do not diagnose command discontinuity or prove the new parameterization.

The tested joint-sampling extension stays stopped. No LR/noise/forecast-package reopening,
forced origin, source fork, legality mask, headroom census, causal diagnostic or stronger C
prerequisite is selected. COPY−RETAIN/SHADOW−COPY value remains unestimated. There is no
whole-direction PARK/CLOSE/RECAST, C promotion, UAV-validation entry or Portfolio disposition.

## 2. Fixed treatment, comparator and information/action path

At ordinary renewal, for physical vehicle `i` and the **decision-input** owner `o`, use
copy `c_i = 2*i + 1[i != o]`, its current motion-head output `m_i`, and its pre-decision
FP32 raw actor input `a_prev,i = actor_raw[..., c_i, 8:10]`:

```text
OWN_COMMAND_MEAN: mu_i = 3 * tanh(m_i + a_prev,i / 3)
DIRECT_MEAN:      mu_i = 3 * tanh(m_i)
```

Coefficient 1 and divisor 3 are fixed. Both arms have the same graph and parameter count.
The additional input is current **applied** own acceleration, not the previous unprojected
proposal, a post-projection state, a snapshot command or Welford-normalized feature.
Encoder/GRU normalization remains unchanged. At zero own acceleration the means agree;
at `m=0` the candidate is a damped prior command, not an exact hold or delta-action bound.

| Input owner | Vehicle0 motion/own-input copy | Vehicle1 motion/own-input copy | Prepare copy | Commit copy |
| --- | --- | --- | --- | --- |
| 0 | 0, vehicle0 incumbent | 3, vehicle1 shadow | 0 | 3 |
| 1 | 1, vehicle0 shadow | 2, vehicle1 incumbent | 2 | 1 |

Motion/raw-action ordering stays **vehicle0 x,y, then vehicle1 x,y**, including both live
and recurrent replay. Existing RNG field names containing OWNER/STANDBY do not reorder
physical components. Prepare is decided by the incumbent and commit by the standby shadow;
both are then serialized in the native owner slot. Preserve owner-before promotion and
never reindex an already recorded action by its post-CAS owner.

The same arm-specific mean must reach generation, stored behavior likelihood, PPO replay
likelihood and the training engine's repeated mean/motion-likelihood calculation. Live
uses the pre-action raw actor; replay uses recorded `actor_raw`, owner and raw action.
Old behavior probability remains the actual collected value. Current-parameter replay
retains gradient through motion and tanh; neither the environment nor the whole detached
mean is differentiated. Density remains Gaussian over **unprojected raw actions**. Tanh
transforms the mean, so no squashed-action Jacobian, rejection sampling or extra clipping
is introduced. Original diagonal noise/log_std law, Bernoulli terms/masks and entropy stay.

Nonrenewal keeps existing applied physical commands and zero new intents while recurrent
state advances. Native norm3/slew1.5 projection and application are unchanged. Pending
application is checked before the new projection; projection updates `s.a` before a new
origin certificate. That certificate and later application have other joint state,
prediction, geometry, timing and version conditions. The new own input guarantees neither
origin eligibility nor a legal transfer.

Information ceiling: native partner fields 29:38 read current partner values under retained
presence; field44 depends on current owner degradation; fields45:54 mostly repeat native
prepare/warmup/handover summaries. They are not actor-queryable readiness/version/origin
certificates. Preserve this existing host literally; no strict fresh-message decentralized
claim or wider observation-interface repair follows. The new direct input uses only own
acceleration. Private future labels remain auxiliary supervision, never actor information
or ordinary legal-transfer evidence.

Consequence path: ordinary event/renewal → the two physical vehicles' existing observations,
messages and active/shadow state → own raw acceleration plus recurrent motion → this arm's
mean and ordinary training sampling → unchanged native projection/communication/application
and service → ordinary transitions and original private labels → recurrent PPO/AdamW →
complete update16 modal consequences. Membership, replacement, survivor state, entity/slot
identity, role promotion, primitive-time discounting, termination and partner co-adaptation
laws are inherited; no population/lifetime intervention is introduced.

## 3. Learner, seed pairing and fixed evaluation

Host: **GROUND-TERMINAL-LINEAR-CLEARANCE-A03**, corrected ordinary renewal
`observation['renew'] = countdown == 0`, with original `renew_completed` kept distinct.
Native float64, policy FP32, CPU, one Torch/BLAS compute thread. The planned result route
is `wsl_4070` under `.codex/hmasd-compute.toml` remote_first; no GPU/device or native-host
substitution is selected. This is not formal UAV validation.

Both arms use underlying **STRUCTURED**, `forecast_package=False`, raw service-Q logits,
original PPO/AdamW, mean-MSE, BCE-with-logits, link/missingness auxiliaries, private labels,
all masks, gradient clipping, Welford and recurrent replay. Both original optimizer groups
have constant LR **3e-5**; weight decay and other coefficients stay. Learned noise, intent
and prediction parameters may diverge through learning; they are not newly frozen.

Only seed **127**. Record the master law now; generate it only in the later authorized path:
`SHA256(ASCII('DISH-OWN-COMMAND-MEAN-B07/seed/127'))`. It supplies common initialization,
training resets/semantic RNG streams and evaluation resets. OWN/DIRECT are treatment
labels, not new native arms or different arm substreams. Reuse one master-addressed initial
parameter state with count-0 actor/snapshot/critic Welford; each arm thereafter has separate
native, optimizer, recurrent and Welford evolution. Common streams do not force equal
actions, labels, trajectories, eligible counts or endpoints.

Per arm: **16 updates ×32 lanes ×128 primitive ticks =65536 ordinary transitions**;
**16 ×4 epochs ×8 minibatches =512 optimizer steps**. Retain the original 32-lane training
distribution. Select/save only update16 for final comparison; no intermediate/best selection.
Retain actual learning counts, per-update LR readbacks, service/loss/gradient finite flags,
parameter norms/displacement, eligible/next-mask counts and ordinary training events/transfers.

Evaluation conditions, in inherited order: TARGET_VISUAL_MASK then TERRAIN_RELAY_MASK,
each with K8 then K4_TO_K12; speed4, slot0, block0. Use
`EvaluationCoordinate(0, regime, schedule, 'SPEED_4', 0).canonical_key()` and the inherited
reset law with the new master; retain all four full resets. Initial/final and OWN/DIRECT
share each condition's reset/exogenous law. Reuse no old seed's reset or checkpoint.

Each arm has **four own initial raw-interface modal rows and four final modal rows**:
16 episodes for the pair. Equal initial weights do not make the two parameterizations'
initial controllers equal; one reference set cannot stand for both. These rows belong to
this B, not a preceding A or initialization gate. Every episode starts with fresh native
and zero recurrent state. Initial Welford remains count0; final evaluation fixes that
arm's own final Welford. No evaluation fitting or learning. Modal motion uses this arm's
mean; prepare/commit keep their original sigmoid probability threshold `>=0.5`.
No sampled final panel, second DIRECT learner, extra seed or condition is purchased.

## 4. Primary, complete consequences and uncertainty

Let `J_A,u,r` be native service summed over the fixed 1200-tick episode scope. Native
termination stops stepping and contributes zero for the unstepped remainder; retain its
reason and actual/unused ticks. Do not drop bad rows, normalize by survival, match shorter
lifetimes, stop at the first service/transfer or relaunch a terminated episode.

```text
Delta_mean = mean_r(J_OWN,16,r - J_DIRECT,16,r), four equally weighted conditions
D_OWN = mean_r(J_OWN,16,r - J_OWN,0,r)
D_DIRECT = mean_r(J_DIRECT,16,r - J_DIRECT,0,r)
```

Publish all 16 rows, four final differences and both arms' initial/final means. The primary
is not a difference of learning changes and is not rebased after seeing initialization.
Initial-relative changes are companion facts; final differences alone do not identify
faster learning or isolate learning from the changed initial controller.

Per row retain energy with actual duration; terminal facts and actual/zero-remainder ticks;
seven hard-event counts (buffer_clear, command_slew_breach, dual_owner, dual_payload,
invalid_commit, separation_breach, token_gap); ordinary legal-transfer count; and
`first_legal_transfer_tick`, the first nonzero `cas_applied` **native post-step tick** or
null. Retain service split temporally before/after first transfer. Continue ordinary
evaluation after any legal transfer; create no source fork. Report raw counts and existing
exposure denominators, with TRAIN and EVAL separate. Without an opportunity denominator,
invalid-commit counts are not rejection probabilities. Early termination's lower energy
is not equal-service efficiency; zero hard events are not safety. Post-transfer service
does not identify packet ownership, source-origin eligibility or causal handover benefit.

One pair cannot estimate training-population uncertainty. No condition bootstrap, p-value
or seed-population CI is requested. Every adverse condition and trusted partial observation
is retained. Missing nonessential resource telemetry is `resources_unmeasured`; an input,
learner or primary failure limits the conclusions depending on it under §11.8.7.

## 5. MEI, predictions and binding result branches

**MEI: +24 mean service ticks**, 2% of the 1200-tick horizon; opposite scale −24, open
band (−24,+24). This gives a modest no-extra-parameter intervention a comparable development
scale; it is not a numerical tolerance, per-condition minimum, significance gate or
repository-wide threshold. Headroom is **absent**: no tuned same-information generic
baseline/stated-upper pair on this host. Reuse the accepted LOW_LR direct-mean baseline
configuration because observation, action, information and budget match; retrain it here.
Initial references are not an upper or a newly tuned oracle. Missing headroom does not hold B.

How the result will be interpreted: above +24 with worthwhile native tradeoffs, recommend
considering one or two independent paired seeds; inside the band, report weak/heterogeneous
value and favor no automatic expansion; at or below −24 or with overriding native harm,
retain DIRECT and stop this candidate's current extension. The table below controls the
reading and retains own-initial loss and source-event limitations separately.

DM and Pro prediction: **Delta_mean >0, low confidence; crossing +24 uncertain**. Score
the sign on the measured primary without inventing a numerical/probabilistic forecast.
Competing observation: <=−24, including fewer invalid commits but worse service. No
minimum legal-transfer count is predicted. Owner prediction: **not taken (unattended)**
at freeze; apply any actual later prediction review at intake.

The following seven rows are verbatim from the immutable response §五; rows may co-apply.
No row automatically purchases another seed, checkpoint, source fork, tuning or Pro round.

| 完整新观察 | 对这个候选的有限读法与后续建议 |
| --- | --- |
| `Delta_mean>=+24`，原生服务／事件／能量权衡仍值得开发 | 一个新配对实例上的有用原生信号，可据全部行考虑一至两个独立配对种子的有限跟进；不是自动加种子、稳定优势或全方向采用。混合行仍保留，不因其存在否认均值。 |
| 有相对 DIRECT 的增量，但 `D_OWN<=−24` | 仍低于本臂自己的初始化；不能称为恢复初始化能力或一般学习改进。保持初末和相对比较同时可见。 |
| `−24<Delta_mean<+24`，或伴随代价使开发价值不清楚 | 报告本曝光下弱／未决／异质性，不称等价；倾向不自动扩展，不增加样本、种子或checkpoint直到出现同号。 |
| `Delta_mean<=−24`，或收益伴随足以否定其开发价值的原生损害 | 保留 DIRECT，停止该 OWN_COMMAND_MEAN 候选的当前扩展；不以无效提交减少、平滑代理指标或一次换主挽救负服务结果。不得据此关闭整个来源议程。 |
| 无普通合法换主 | 原生服务主量仍有效；收益只能称普通／incumbent服务证据，来源原点及 COPY−RETAIN／SHADOW−COPY 仍未估计。 |
| 出现普通合法换主 | 报告次数、首次 native post-step `cas_applied` 时刻和完整后果；它只是路径事实，不自动证明来源原点可用、换主受益或 prepared-state价值，不追加fork。 |
| 输入、真实学习或主比较受损／未完成 | 保留实际计数、失败和独立可信行，不填造完整配对主量；具体缺口只限制依赖结论。非主张必需的资源量未测，不连带否定原生服务。 |

## 6. Work, exposure, budget and stop

Configuration arithmetic was recomputed without importing learner/native modules from
`control_low_lr_b04/study.py:74–85` at source
`5b9390ba2da7c2002a512505c2a13f3045a57ab1` and agrees with the immutable proposal's
`pro_packets/20260908_p53_own_command_mean/EXPOSURE_AND_COST.json`. That older JSON's
"proposed/not selected" labels remain historical; this card records the accepted allowance.

| Dominant algorithm work | Each arm | One pair |
| --- | --- | --- |
| Ordinary transitions, 16×32×128 | 65536 | 131072 |
| Optimizer steps / replay minibatches, 16×4×8 | 512 | 1024 |
| Ordinary batched policy forwards, 16×128 | 2048 | 4096 |
| Recurrent replay steps per minibatch | 64 | 64 per minibatch |
| Own-initial + final modal episodes | 4+4 | 16 |
| Evaluation ticks / width1 policy calls, upper bound | 9600 | 19200 |
| Native training calls, lower–upper | 131072–1572864 | 262144–3145728 |

The native training law is `2N+2E+H`, `N=65536`, `0<=E<=N`, `0<=H<=20E` per arm:
ordinary transitions plus next labels, eligible delay steps and private consequence work.
Actual E/H may differ between arms. Retain existing E; if H is not measured, report that
fact and the bound without expanding the native ABI. Forward/critic/backward/optimizer,
build/load and publication are additional work. No action/trajectory candidate search,
extra controller tree or new scientific source fork is added.

Machine-generated exposure line: **2 arms ×1 paired seed ×16×32×128 =131072 ordinary
transitions; 2×16×4×8 =1024 optimizer steps; 16 modal episodes <=19200 ticks; native
training 262144–3145728 calls plus evaluation.** Same-learner historical B06 at this LR
and exposure moved by relative parameter L2 **0.04474046045735298** (evidence commit
`33db0d86016882d3e6d1c4dc1058dc0d8fe55bf6`): a prior observed ability to move, not a
prediction or observation of seed127. Actual new exposure at this authoring boundary is
**0 models/initializers/learners/native calls/transitions/optimizer steps/episodes**.

Complete new cap: **1800 seconds per arm, 3600 seconds for the pair**. Shared necessary
checks/build/load/common initialization/reduction/publication work is S, counted once
and allocated S/2 to each arm. Each arm's four initial rows, training/labels, four final
rows and arm-local I/O count to that arm. Do not share the charge of DIRECT's initial
episodes or duplicate publication charges. Include all necessary check attempts and leave
publication inside the cap; scripts/stages or a failed test do not reset it. Report
complete charged wall, shared and per-arm allocations; study elapsed and any measured CPU
work are separate. This is not an unused historical balance.

Per-arm planning uses B05's complete pair 432.82s and B06's complete single 226.02s as
same-scale anchors. New mean/check overhead, E/H, trajectories, load and wall are unknown;
no exact price, speedup or completion guarantee follows. No calibration experiment is added.
Added validation is the single focused mean/mapping/likelihood/mode/master/primary check
specified in the CM spec §4, charged once as shared work. Existing trusted host/renewal/
terminal/learner coverage is reused; no historical replay, upper or support census is added.

Stop after this pair's fixed training, all evaluations and publication, or on exhausted
complete budget, actual nonfinite training state or a defect threatening a dependent
measurement. Preserve all counts and trusted partial rows. Finite large gradients and native
termination are not technical retry triggers. No effect-based early stop, seed/reset
replacement, bad-row rerun, longer training or coefficient change. A known inability to
complete within the cap returns the concrete cost/scope conflict; it does not silently
remove labels, evaluation rows or learning exposure.

Engineering-scope §4 needs **none newly**: reuse existing learner checkpoints and existing
remote execution/observation facilities. §5 remains <=2000 new non-test lines, <=600 runner
lines and the existing five-minute research-directory test budget. The orchestration share
is a review signal. Resource admission is immediately before each actual invocation on its
execution node, physical/effective available memory both >=4GiB. No admission is run here.

## 7. Implementation and return route

The complete five-item engineering handoff and original focused acceptance are in
`DISH_OWN_COMMAND_MEAN_B07_CM_SPEC_20260908.md` §§1–5, using the existing DISH checkout.
The card and source intake fix science; CM implements/observes and retains technical
acceptance, with the existing independent review for changed action-distribution/training
semantics. Root receives this committed handoff before any CM dispatch. Implementation
acceptance is distinct from launch and from DM's later scientific intake.

A later named launch uses accepted committed/pushed code and detached exact-SHA execution
through the configured remote route. Existing `EXPERIMENT_MONITOR.md` and
`ROOT_OPERATIONS.md` govern accepted-handle adoption; transferring observation never
relaunches. No handle or result exists at this freeze. The next scientific discriminator
remains the selected pair's native final-service contrast, bounded by §§4–5.
