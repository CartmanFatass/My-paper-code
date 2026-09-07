Claim under test: ordinary sampled execution of one newly trained LOW_LR controller can change complete native service relative to its modal execution enough to affect development choice.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; causal local observations, actual messages and role-owned recurrent state determine motion and handover proposals under the two execution laws.

# DISH-SAMPLED-EXECUTION-B06 — frozen B/EXPLORE card, 2026-09-06

## 1. Question, authority and claim ceiling

For one new seed113 LOW_LR final controller, is ordinary sampled action execution versus
its existing modal execution worth developing on the four declared native conditions?
Direction choice is **PRO_FINAL**, complete post-B05 Convergence response at immutable
`db0bbfd8e1d96b06e8c6e8aa9bfa70787fe9a9cd`,
`pro_packets/20260906_post_b05_convergence/archive/RESPONSE.md` §§三–七.
Application: `DISH_POST_B05_CONVERGENCE_INTAKE_20260906.md`. This is outcome-informed
**B/EXPLORE**, one independent training instance and finite action samples. It cannot establish
stable superiority, safety, optimality, a unique cause of prior LR gains, or source value.
No C object, third LR pair, preceding A, source fork or forecast-package reopening is selected.
The current Root assignment freezes this card only; it authorizes no implementation or launch.

MEI is **+24 mean native service ticks**, 0.02 of the fixed 1200-tick horizon: a development
scale large enough to matter to this finite comparison. The opposite scale is -24 and the
open band is (-24,+24). Above the positive scale with a worthwhile native trade-off I would
retain sampled execution as a candidate for a separately selected bounded follow-up; inside
the band I would report unresolved value/heterogeneity; below the negative scale or with severe
native cost I would favor the modal default in this instance. The §5 table controls the reading.

Headroom: no tuned same-information baseline versus stated upper reference is established on
this host. B04/B05 initial controllers are neither uppers nor tuned baselines. Reuse the accepted
LOW_LR learner and modal evaluator because observation/action/information and training budget
match; both final modes share one learner. New seed113 requires its own four raw modal initial
rows, measured early inside this B, without using their outcome to qualify training. There is
no separate headroom experiment or exact upper prerequisite.

## 2. Preserved learner, host and consequence path

Use GROUND-TERMINAL-LINEAR-CLEARANCE-A03, corrected ordinary renewal
(`observation['renew'] = countdown == 0`, raw `renew_completed`), native float64 and policy
FP32, one Torch/BLAS CPU compute thread. Planned node is `wsl_4070` via the existing
`.codex/hmasd-compute.toml` remote-first route, with the accepted native backend; no GPU or
Windows/native substitution is selected. Source acceptance and actual node binding come later.

Retain STRUCTURED, `forecast_package=False`, **raw service-Q logits**, original mean-MSE,
BCE-with-logits, PPO, link/missingness auxiliaries, private labels, masks, recurrent replay,
Welford training updates and gradient clipping. AdamW is constant **3e-5 in both original
parameter groups**; all other coefficients, including weight decay, remain unchanged. The
existing prepare/commit sigmoid probabilities do not reopen the ended service-Q sigmoid/NLL
package. Preserve the original 32-lane training distribution, ABI, reward, information, labels,
action space, projection, certificates, entity/role ownership and protocol timing.

Degradation/renewal -> the two physical entities' causal observations and actual messages ->
current-role active/shadow recurrent state -> permitted modal or sampled motion and intent ->
native projection/certificates/owner application -> full service, energy and events. Ordinary
sampled training and private auxiliary labels expose the learner to those consequences through
recurrent PPO/AdamW. Private label-clone promotions are supervision, not ordinary legal transfers;
privileged future labels never enter actor information. No membership, slot replacement or
source-state intervention is added. Preserve `apply_native_promotion` after legal application.

## 3. One training instance, initialization and final execution laws

Training/environment master is `SHA256(ASCII('DISH-SAMPLED-EXECUTION-B06/seed/113'))`.
Use it for actual initialization, training resets/random streams, four evaluation resets and
metadata. One master-addressed initial state has empty actor/snapshot/critic Welford. Evaluate
that state's four raw-interface MODAL reference rows, with fresh native/zero recurrent states
and no fitting of statistics, then train from that same initial state. This reference is an
ordinary controller with motion/protocol outputs, not held-only, oracle or a safety baseline.
Do not reuse seed101 phases, resets, initial/final parameters or its 297.25 reference mean.

One LOW_LR learner: **16 updates ×32 lanes ×128 ticks =65,536 ordinary transitions**;
four epochs ×eight minibatches per update =**512 optimizer steps**. Select/save only update16
for this comparison, with no best/intermediate selection. Record actual counts, per-update
service/loss/gradient statistics and finite flags, both parameter-group LR read-backs, initial
and final norm/displacement, eligible E/next-mask counts and ordinary training events. Engine
reconstruction or evaluation model loads are not extra independent training seeds.

Four conditions are TARGET_VISUAL_MASK/TERRAIN_RELAY_MASK × K8/K4_TO_K12, speed4, slot0,
block0. Derive and retain full resets with the new master and inherited
`EvaluationCoordinate(0, regime, schedule, 'SPEED_4', 0).canonical_key()` law. Each condition's
initial modal, final modal, final sample0 and final sample1 share that reset and environment
master; sample j changes only the evaluation policy stream. Final MODAL has one episode per
condition and SAMPLED has exactly two, j=0,1, both retained.

Both final modes start each episode from the **same update16 parameters, learned log_std,
prediction heads and fixed checkpoint Welford**, with fresh native and zero recurrent state.
No evaluation Welford fitting, learning or optimizer updates. Recurrent states then evolve on
the actual observations/messages each tick; action-induced trajectory differences remain real.

| Ordinary renewal output | MODAL (existing evaluator) | SAMPLED |
| --- | --- | --- |
| Four motion components, `mu=3*tanh(motion)` | `mu_f` | `mu_f + exp(clamp(log_std_f,-5,1))*Z_f` |
| prepare intent | `1[p_prepare>=0.5]` | `1[U_prepare<p_prepare]` |
| commit intent | `1[p_commit>=0.5]` | `1[U_commit<p_commit]` |

Map each native RNG word to `U=((word>>11)+0.5)/2^53`. Each independent normal uses two
separate uniforms as `sqrt(-2*log(U0))*cos(2*pi*U1)`; each Bernoulli uses its own uniform.
Fields are `MOTION_OWNER_X`, `MOTION_OWNER_Y`, `MOTION_STANDBY_X`, `MOTION_STANDBY_Y`,
`PREPARE_BERNOULLI`, `COMMIT_BERNOULLI`. No temperature/noise adjustment, cached sine draw,
bad-action resampling or bypass of ordinary native projection/rejection. At non-renewal ticks
take no new action/intent draws; preserve held commands, zero intents and ordinary recurrent
updates. Owner/standby fields follow current roles, not permanent physical UAV identifiers.

Evaluation policy master is
`SHA256(ASCII('DISH-SAMPLED-EXECUTION-B06/EVAL_POLICY/seed/113'))`.
The exact ASCII address is frozen here under Pro's delegated concrete-format choice:

```text
DISH/RBHR/R06/DISH-SAMPLED-EXECUTION-B06/EVAL_POLICY/{canonical_key}/sample/{j}/tick/{t}/field/{f}/draw/{d}
```

`canonical_key` is the complete unmodified inherited string; j=0 or 1; t is the zero-based
physical pre-step episode tick, not renewal count and not reset on handover; f is one literal
field above; d=0,1 for a normal and d=0 for a Bernoulli. Integers are unpadded decimal, no
hidden salt or shared addresses. The existing backend requires `DISH/RBHR/R06/`; including
that namespace preserves its API and Pro's logical coordinates. This card has not invoked
the new master/address. The original TRAIN32 sampler is unsuitable for a width1 evaluator:
use a small object-local adapter, no fake extra lanes or global sampler changes.

Current `control_low_lr_b04.study.master(seed)` hardcodes B04, and `object_name` alone does not
change its consumers. Later CM must pass the selected family/master explicitly through
configuration/initialization/training/reset, preserving B04/B05 defaults and original training
address laws. Do not mutate an imported module's global OBJECT/SEED.

## 4. Primary, references and native companions

Each J is the sum of service on the fixed 1200-tick range. Native early termination stops native
stepping and contributes zero service for the remaining ticks; retain actual stepped/unstepped
counts and native cause. Do not shorten all rows to a common observed duration, normalize by
survival, drop bad rows, select the better sample, stop at first success or relaunch terminal rows.

`Delta_exec = mean_r((J_S,r,0 + J_S,r,1)/2 - J_M,r)` with four equally weighted conditions.
Publish all sixteen episode rows and the four per-condition primary differences. Also report
`D_modal = mean_r(J_M,r - J_0,r)` and
`G_sampled_vs_init = mean_r((J_S,r,0 + J_S,r,1)/2 - J_0,r) = D_modal + Delta_exec`.
D_modal includes learned weights and Welford changes. G compares different execution interfaces
and combines learning with execution-law change; it is not same-interface learning gain or a
third independent measurement. No initial sampled panel is purchased. One training instance
does not support a training-population CI or bootstrapping conditions as training seeds.

Retain native energy, all seven inherited hard-event counts, legal transfer counts, terminal
facts and before/after-first-transfer service. Add `first_legal_transfer_tick`: the native
**post-step tick of the first nonzero `cas_applied`**, null if absent (never 1200 as a sentinel).
Publish raw events and exposure denominators; compare condition means after averaging the two
sampled episodes, not raw eight-episode totals against four. Energy interpretation must account
for early termination. Do not introduce event-weighted rewards after observing results.

An ordinary legal transfer is a native path fact. Source-origin eligibility needs additional
inputs at an actual first-application cut; COPY−RETAIN/SHADOW−COPY value needs matched source
interventions. Neither follows automatically. Temporal post-transfer service does not establish
packet ownership or causal handover benefit. Zero transfers leaves source value unestimated.

## 5. Predictions and binding result branches

DM and Pro primary prediction: **Delta_exec <= -24, low confidence**. Joint sampling may add
costly motion/intent variability; this is a performance prediction, not a proven noise mechanism.
The competing observation is Delta_exec >= +24 with a native trade-off worth developing.
There is no predicted minimum transfer count or zero-event-rate claim. Score magnitude/sign
on the actual primary; mixed rows alone do not score a magnitude hit. Owner prediction:
**not taken (unattended)** at freeze, subject to any later existing review.

The following seven-row table is copied verbatim from immutable RESPONSE.md §六. Branches may
co-apply. No outcome automatically buys a second training seed, third sample, noise strength,
new threshold, longer training or intermediate checkpoint; any follow-up is a separate decision.

| 新观察 | 本轮之后允许的读法与建议 |
| --- | --- |
| `Delta_exec>=+24`，原生事件／能量／终止权衡仍值得开发 | 本训练实例上抽样执行有有限平均增量，可把它留作执行规则候选，并据完整结果考虑一个有限独立训练跟进；不是默认全方向切换或稳定优势。混合行本身不取消主均值，但所有负行仍限制适用性。 |
| 相对模态改善，但 sampled-versus-init 仍明显负向 | 只称执行法则的相对改善，不能说恢复初始化服务；初始化参照及其接口差异必须同列。 |
| 主量带内，或两个样本／条件差异使开发价值不清楚 | 报告有限未决／异质性，不称等价，不追加样本直到同号，也不按最好一条选择模式。 |
| `Delta_exec<=-24`，或正均值伴随严重 native 代价 | 在本例倾向保留模态默认、不扩展该联合抽样规则；预测命中也不是原因定位。若仍有换主，则是带成本的路径事实，不能挽救服务负结果为“来源成功”。 |
| 抽样或模态出现普通合法换主 | 保留次数、首时刻、完整后果；只能说明所观察路径可发生该事件。是否有来源原点及来源增量留给另一个实际选择，不在本轮自动追加 fork。 |
| 全部最终评价无合法换主 | 原生执行法则比较仍可读，来源量仍未估计；不说宿主不可能换主、抽样无支持的普遍定理或 SHADOW 无价值。 |
| 学习、输入或主测量受损／未完成 | 报告实际缺口、计数及独立可信行，不填造完整 Delta，不连带重判 B05/B04。原生合法终止本身不是这种损坏。 |

## 6. Work, cost, exposure and stop

Machine arithmetic: `sampled_execution_b06_20260906/EXPOSURE_AND_COST.json`.
Algorithm work is one learner, 65,536 ordinary transitions and 512 optimizer steps, plus private
labels. With N=65,536, actual eligible E and private consequence steps H, native training calls
are `2N+2E+H`, `0<=E<=N`, `0<=H<=20E`: **131,072–1,572,864**. This is a call bound, not a
wall multiplier. Retain existing E; if H is unmeasured report it and its bound, without expanding
the native ABI. PPO/critic/forward/backward work is additional to those native-call counts.

Four initial MODAL episodes <=4800 ticks, four final MODAL <=4800 and eight final SAMPLED
<=9600: **16 episodes, <=19,200 native step/width1 policy calls**. For R sampled-evaluation
renewals, new policy draws are 4R normals, 2R Bernoullis and 10R uniforms; R<=9600, hence at
most 96,000 uniforms, separate from training RNG work. Two retained samples are finite
measurement, not a candidate search. There are no trajectory trees or nested source forks.

**One complete B06 cap: 1,800 seconds.** Charge necessary focused checks, native build/cache
load, initialization/model loads, training/labels, all sixteen evaluations, reduction and complete
publication once to that same logical invocation. Scripts/stages do not reset the cap. No extra
A300/reference120/mode budget or inherited balance. B05 LOW_LR's complete 212.86s and shared
initial/reference 7.11s are measured planning anchors, not sampled-episode prices or an exact
sum forecast. New E/H/R, width1 sampling, required adapter checks/cache/load remain unmeasured.
Do not buy a cost experiment. Return a known whole-task cap conflict instead of trimming science.

Added validation is the focused changed-input/sampler/primary coverage in §7, inside the cap;
no all-history replay, exact upper, support census, headroom prerequisite or cause-first work.
Stop for exhausted budget, actual nonfinite learning state or a real fault threatening the
primary, preserving all exposure and independently trustworthy rows. Finite large gradients
are not nonfinite failure; native early termination is a valid outcome. Report complete wall
and scoped peak RSS; optional missing resources remain `resources_unmeasured`, while a missing
dependent primary/learner measurement limits that claim under evidence-spec §11.8.7.

Actual new exposure at this documentation freeze: **0 initializers, 0 learner updates,
0 transitions, 0 optimizer steps, 0 evaluation episodes**. Proposed counts are not observed.
Engineering-scope §4 items needed: **none**; use existing execution/observation facilities.
Ordinary §5 budgets: <=2000 new non-test lines, <=600 per runner, existing five-minute research
directory test budget; orchestration 30% is a review signal, not an automatic refusal.

## 7. Future CM handoff; not dispatched by this freeze

1. Deliver a runnable B06 comparison and trustworthy primary/native companions for §§2–6;
   no source implementation or result-bearing execution is commissioned by the current DM task.
2. Proposed owned entries: `experiments/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06/study.py`,
   `scripts/run_dish_sampled_execution_b06.py`, focused tests under
   `tests/experiments/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06/`.
   Reuse `control_low_lr_b04/study.py` (master/configuration/prepare_shared/run_arm),
   `forecast_package_b02/study.py` (evaluate_episode/terminal_facts) and
   `degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py` (sampler/step_rows).
   Any necessary shared edit preserves B04/B05 defaults. Runtime
   artifacts belong under `temp/directions/degraded_incumbent_shadow_handover/exp/`; E0 evidence
   and CM record belong beside this card. Concrete code facts/pointers are in intake §3.
3. Preserve §§2–4; especially actual new master consumers, unchanged training RNG/address laws,
   raw-Q input, ordinary renewal, both LR groups and same-final-state/fixed-statistics evaluation.
4. Accept by one focused check of changed master consumers, width1 physical-tick/field/sample
   addressing, original transforms/no draws at nonrenewal, unchanged modal behavior, fresh
   native/recurrent state and fixed Welford, native promotion, and a few synthetic primary and
   first-transfer/null rows. Reuse credible LR/renewal/terminal coverage. Independent review of
   the new scientific/RNG semantics is the existing high-risk review, with no new layer. Apply
   evidence-spec §§4, 5.2, 11.4, 11.8.6–11.8.7; tests/process exit alone do not accept science.
5. The complete §6 cap and stop apply. A later launch follows committed/pushed accepted bytes,
   detached exact-sha remote execution and same-node immediate `admit-memory` (physical/effective
   available memory each >=4 GiB), then existing independent monitor handoff. No launch is
   authorized here. The later CM retains direct observation/collection/technical acceptance;
   DM retains result interpretation. No implementation, resource receipt or run handle exists
   for B06 at this freeze.
