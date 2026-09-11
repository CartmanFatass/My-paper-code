REQUEST_ID=2026-09-05-dish-a02-host-convergence-01
PINNED_REFERENCE=06c05c1f52736d7f274e1e6491611b8d7d528a90

## PRO_FINAL_DECISION: CONTINUE

**Smallest applicable unit:** the accepted **first-application-valid RETAIN/COPY/SHADOW source-selection exploratory family** within `degraded_incumbent_shadow_handover`.

Continue this family **through a prospectively distinct, bounded host qualification**. Do not interpret this as continuing unchanged training on the literal host, repairing B01 retrospectively, reopening R02, or authorizing a successor experiment.

The smallest supported scientific conclusion is:

> B01 did not expose the source intervention. A01 locates the observed interruption upstream of source selection, despite substantial preparation activity. A02 supplies native point measurements consistent with a deterministic near-endpoint clearance obstruction in the inherited definition. These findings explain why host qualification is now decision-relevant; they do not estimate the value, equality, or nonharm of RETAIN, COPY, or SHADOW.

This is not “continue because the mechanism is untested.” The positive reason for continuation is narrower: **the evidence identifies a concrete host-information obstruction, and a small native-path comparison can distinguish whether one explicitly changed host restores the necessary causal path or merely moves the interruption downstream.** That comparison can be informative without favoring SHADOW.

B01 remains valid `FTS-B0`; A01 and A02 remain valid A observations. The historical R02 closure remains unchanged. The direction record distinguishes that closure from the later accepted B re-entry. No new learner, altered-physics run, forced trigger, or Portfolio transaction is authorized here.   

## OBSERVATION_VS_INFERENCE

### Observed point and prefix facts

| Evidence                              | What was observed                                                                                                                                                                                                                                                                                                                                                                                              | What it does not establish                                                                                                                                                                |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **B01 — complete B/EXPLORE**          | Original seeds **11, 29, 47**, each with **262,144 training transitions, 64 updates and 2,048 optimizer steps**. All **48 panel rows** completed, totaling **57,600 prefix ticks**, with **zero triggers, zero usable seeds and zero branch-consequence ticks**. The first ordered branch is `FTS-B0 — TRIGGER_SUPPORT_INSUFFICIENT`.                                                                          | Source equality, nonharm, positive or negative source effects, or the five-service-tick MEI. Empty-support reducer zeros and `shadow_nonharm=true` are not empirical comparisons.         |
| **A01 — retained-checkpoint A/RECON** | The seed-11 checkpoint reproduced all original sixteen prefixes: **19,200 live inputs**, no early terminal padding, **2,720 renewal opportunities, 2,234 prepare proposals, 1,131 commit proposals and 19,148 completion-latch ticks**. Common-source support, snapshot/readiness delivery, emitted intents and native service were all zero. Every row received `PREPARATION_SUPPORT_GAP(snapshot_delivery)`. | Absence of preparation, failure caused by early padding, or competence of later protocol stages. The ordered first-absent-stage label does not mean every later gate would pass.          |
| **A02 — one-point A/RECON**           | At the original seed-11, block-0, `TARGET_VISUAL_MASK/K8/speed 4/slot 0` coordinate, normal mode, native tick 0: camera flags **`[0,0]`** and source-hop margins **`[-9.303396681040274, -10.285571482315484] dB`**. Both margins are below the 6-dB send threshold. There was **one prepared native point and no completed native tick**.                                                                     | A packet arrival, a learned preparation proposal, a handover, a changed-host result, or a whole-prefix reception law. A prepared native point is not an additional learned prepare event. |

These readings follow the B01 result’s **E0 and Counts and exposure**, A01’s **E0 and Counts, timing and exposure**, and A02’s **§§1–4**, including the raw JSON’s `native_boundary`, `receivers` and `new_exposure` fields.

B01’s recorded relative total parameter displacements were **0.42465718774783356, 0.419585027483137 and 0.4196544358013136**. They establish nonzero recorded optimization movement, not trigger competence. The material per-tensor outliers—approximately **1.2535×10³⁰⁰, 1.0764×10³⁰⁰ and 1.1525×10³⁰⁰**—remain visible: the evidence explains that initially zero tensors use a `1e-300` denominator. They are not meaningful percentage changes or nonfinite failures. A01’s new parameter displacement is exactly zero; A02’s is **null/not applicable**, because no model exists.

### Static implication: a clearance obstruction, not a universal reception theorem

The inherited definition fixes ground-source height at 0, UAV height at 90, nonnegative terrain, and ray samples at \(j/128\), \(j=1,\ldots,127\). Thus the first ground-to-UAV sample and the last reverse-camera sample both have height

$$
z_{\text{near}}=\frac{90}{128}=0.703125.
$$

For every horizontal sample location under that definition,

$$
0.703125 < 5 \le H+5,\qquad
0.703125 < 8 \le H+8.
$$

Therefore that sample fails the camera clearance and sets the radio obstruction condition. **Changing horizontal motion cannot remove this particular camera obstruction while those height and clearance clauses remain unchanged.** R06 retains the relevant host clauses, and the inspected native terrain/ray/physics definitions implement them. This is a definition-level implication, not additional sampled evidence. See the R05 host manifest **§§1–3**, R06 composite **§§1 and 3**, and backend **lines 204–226**.

At the actual A02 point, the separately derived terrain heights were **0.8467255467868863** and **0.7901657174358243**; both corresponding terrain-plus-clearance thresholds exceed 0.703125. Those derived samples are not native-exported ray flags. The native evidence consists of the reported positions, camera flags and margins.

**Camera obstruction and SOURCE delivery must remain distinct.** The radio law includes addressed Gaussian noise; the obstruction witness and two below-threshold margins do not establish universal zero reception. Native SOURCE arrival is separately margin-gated, and snapshot emission requires both receivers to hold a common SOURCE sequence. Consequently, camera absence alone is not a proof of the entire A01 common-source failure. The combined evidence strengthens an upstream host-information explanation, without identifying the complete radio history or every downstream cause. See backend **lines 373–396 and 452–456**.

### Strongest contradiction and surviving null

The strongest contradiction to simply purchasing more unchanged learning is that **the learner cannot overcome the demonstrated camera obstruction through horizontal control**. However, the strongest contradiction to a source-family negative is equally decisive: **the source intervention never acted**.

The strongest same-information null remains:

> Once an actionable opportunity is reached, COPY may supply all useful recovery state; RETAIN may already be sufficient, or any gain may come from owner/actuator remap rather than shadow preparation. A competent deadline-bound replay/replan may absorb a later SHADOW increment, and a SHADOW-trained checkpoint may favor its customary hidden-state source through co-adaptation.

All current observations are compatible with that null—and with useful shadow preparation hidden behind the missing exposure. COPY and RETAIN are the declared same-information comparators; **their empirical competence on this literal host has not been established**. Replay containment is a live explanation, not an observed theorem or an additional B launch requirement.

## SCIENTIFIC_QUESTION_AFTER_DECISION

The retained family question is:

> At an endogenously proposed, first application-valid handover, does promoting the recipient’s prepared shadow state improve the next 100 native service ticks relative to copying the incumbent state, and does the identical owner/actuator remap improve recovery relative to shell-matched retention?

The two contrasts remain separate:

$$
\Delta_{\text{copy}}
=\operatorname{mean}_{\text{triggered}}
\!\left(J_{100}^{\text{COPY}}-J_{100}^{\text{RETAIN}}\right),
$$

$$
\Delta_{\text{shadow}}
=\operatorname{mean}_{\text{triggered}}
\!\left(J_{100}^{\text{SHADOW}}-J_{100}^{\text{COPY}}\right).
$$

With no triggered rows, these contrasts are **unestimated**, not zero. COPY–RETAIN is owner/actuator remap relative to the matched transaction shell, not natural no-transaction value. SHADOW–COPY isolates promoted-source selection within the declared checkpoint process, not unique information or necessary shadow preparation. These are the B01 card’s **§§3–6** estimands.

A new host would change the **host-specific estimand and information distribution**. It would not retroactively change B01. CONTINUE is appropriate only because the causal question above can remain intact across separately named exploratory objects; it is not a claim that evidence transfers between hosts.

## SEMANTIC_HOST_BOUNDARY

### What must remain intact

There remain two physical UAV entities, an incumbent physical vehicle, a current owner role, a standby role, and distinct active/shadow recurrent slots. These are not interchangeable identities. The degradation remains attached to the designated physical incumbent, rather than following the owner after a transfer. There is no population join/leave or variable-\(N\) claim.

The actor must retain its causal observation interface and opaque SOURCE-payload boundary. A host qualification must not make the task “work” by leaking ground truth or payload content into the actor, privileging SHADOW, degrading COPY artificially, or manufacturing accepted snapshot/readiness state. The inspected actor interface and native protocol distinguish observation, packet possession, recurrent state and transaction eligibility.

For a later source comparison, the common checkpoint, normalization, prefix, origin action, transaction shell/cost and branch-common future tape remain matched. Source selection must affect the recipient’s ordinary policy action, which must then affect native service and costs; a hidden-state difference alone is not recovery value.

### The exact prospective fact still needed

**No supported numerical height/clearance remedy has been selected or tested.** The next host definition must explicitly settle:

> What are the world-coordinate elevations of the radio emitter and visual target relative to local terrain, what altitude reference applies to the UAVs, and how does clearance apply near the ground endpoint?

Changing these clauses is a **new ground-endpoint access model**, not an implementation-versus-spec repair. That semantic change must be named before native evaluation. The A02 intake correctly leaves it unexecuted.

For an alternative with endpoint heights \(z_g,z_u\), the relevant near-ground sample becomes

$$
z_{\text{near}}=\frac{127z_g+z_u}{128}.
$$

Removing the old unavoidable inequality at that sample is only a necessary local check. It does not establish clearance along the remaining ray, camera range, actual radio delivery, common sequence support, protocol timing, or useful control.

A candidate should be chosen from an explicit intended host interpretation—not by increasing a height or lowering clearance until SHADOW wins. If the proposed remedy instead changes who knows what, makes acquisition automatic, or replaces endogenous handover with prescribed success, it changes the mechanism question enough to require a fresh family decision, potentially RECAST.

## NEXT_DISCRIMINATOR

### Recommended next object: bounded A/RECON host-path qualification

The cheapest useful next discriminator is **one proposed host law against the literal-host reference**, using the original A02 coordinate and a small, prospectively bounded native trace. It is not another one-point ray calculation and not another learner purchase.

A suitable proposed scope is one paired fixture, with at most one ordinary episode per host and a stated finite tick bound. Fix the diagnostic control/proposal rule before observation, keep its information set causal and identical across the pair, and use normal native transitions. Every proposal may fail normally. Do not override source margins, accepted state, readiness, first-valid flags or ownership.

The fixture must inspect the two paths separately and then their connection:

| Path                             | Required observable                                                                                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Observation → representation** | Actual camera availability and permitted actor observations, followed by the ordinary filter/recurrent inputs—not privileged target access.          |
| **SOURCE → protocol support**    | Actual send margins **and completed arrival ticks**, receiver sequence/age records, common-source support, snapshot delivery and readiness delivery. |
| **Proposal → legal action**      | Ordinary prepare/commit proposals, renewal and eligibility facts, emitted intent, and any application-valid owner/actuator transition.               |
| **Action → native consequence**  | Actual relay/base delivery and native service, with energy and failure events. Neither a clear ray nor a legal handover substitutes for service.     |

These observables follow the native arrival, snapshot, intent and service path; the A02 point stopped before arrivals, while A01 never exposed the later stages.

**Prospective interpretation must allow informative failure.**

* If the new host still exhibits the obstruction or no actual common SOURCE delivery, restoration is not demonstrated.
* If observations or SOURCE delivery appear but snapshot/readiness or application does not, the measurement identifies a remaining stage gap. It does not establish universal host impossibility or general policy incapacity.
* If the ordinary chain reaches legal action and native service, the host is qualified **on that fixture under that controller**. It still supplies no SHADOW–COPY effect and no tuned headroom estimate.

A qualification can therefore succeed while the strongest same-information null remains entirely true. That is what prevents it from being a disguised search for treatment benefit.

This is transparently outcome-informed follow-up to A01/A02, not independent confirmation. Keep every observed failure and partial restoration visible; no sweep until success, favorable-coordinate replacement, or silent relabeling of B01. The named fixture’s scope and interpretation are needed to say what was measured, not to reconstruct a C-class certificate stack. The evidence specification expressly permits adaptive host changes between named B runs and keeps the burden proportional to the claim.

### What follows only after that measurement

A later source-effect study, if recommended, is a **new B object** with its own card, learner exposure, costs and ordinary fresh-resource admission. It must exercise the real learner and retain RETAIN/COPY/SHADOW, the two separate contrasts, native consequences, and visible no-trigger rows.

The existing five-service-tick MEI remains a descriptive scale for B01; its sign-based result rule is not rewritten. Replay/replan, co-adaptation discrimination, and tuned headroom can motivate later work, but are not mandatory gates imported from stronger evidence classes. Exact replay containment, the 24-root stack, formal equality, transfer and deployment guarantees remain outside this next A/B question.

### Cost and exposure boundary

| Completed object | Recorded cost                                                                                                                                                                              |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **B01**          | Aggregate runner **3,041.225029119014 seconds** across three seeds; each seed under its **1,800-second** cap.                                                                              |
| **A01**          | Runner **115.94635876399116 seconds**, against a **600-second** cap. No new learning.                                                                                                      |
| **A02**          | Prospective law **\(1.5(5+5)=15\) seconds**, cap **60 seconds**. Supervisor **1 second**; runner pre-serialization wall **0.0061659040075028315 seconds**; peak RSS **342,839,296 bytes**. |

These are completed-object measurements, not a selected future purchase. In particular, A02’s pre-serialization point time is not a measured end-to-end episode cost.

The proposed A qualification needs its own bounded full-path cost projection and fresh admission. Its exposure record must separate initialized models/policies, prepared points, completed native ticks and optimizer work. With no model, displacement is not applicable; with an unchanged retained model, it is measured zero. No future sweep, per-arm budget or run is selected by this decision.

## UNCERTAINTY_AND_LIMITATIONS

The unresolved scientific facts are substantive: the alternative endpoint law is not yet specified numerically; no changed-host behavior has been observed; A02 observed no arrivals; A01 is one retained checkpoint; and no scientific source fork has been observed. Common-source absence does not reconstruct each receiver’s full individual receipt history. Opening the physical information path may still leave proposal, prediction, certificate, deadline, motion or service limitations.

There is no tuned same-information headroom record, demonstrated comparator competence, replay-containment result, or separation of source value from checkpoint co-adaptation. None of these gaps converts absent exposure into a negative effect. Conversely, none supports an assumed future SHADOW benefit.

**Evidence/connector blocker: none.** The missing prospective host law is the next specification question, not a blocker to forming this bounded family decision.

## PORTFOLIO_IMPLICATIONS_AS_ADVICE_ONLY

Sequence the small host-path discriminator before additional unchanged-host training. Preserve B01/A01/A02 and their costs rather than treating the new host as a rescue of their results.

This decision neither changes Portfolio lifecycle or priority nor pools DISH with FOLR, RCLE or VSP-02. It is **CONTINUE, not RECAST**; no second-recast count is inferred from historical Portfolio terminology. R02 remains closed. No cross-direction investment or fusion conclusion follows. 

## Retrieval record

REQUEST_ID=2026-09-05-dish-a02-host-convergence-01
PINNED_REFERENCE=06c05c1f52736d7f274e1e6491611b8d7d528a90

All repository reads used the connected GitHub connector for `CartmanFatass/My-paper-code` at that exact reference.

| Actual retrieved allowed path                                                                                              | Read scope                                                                                                                               |
| -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md`                                                 | Historical closure/re-entry and complete current B01/A01/A02 position; overlapping retrieval completed the initially truncated response. |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FIRST_TRIGGER_SOURCE_SCOUT_B01_SCIENCE_CARD_20260904.md` | Complete card, including §13 supplement; overlapping retrieval completed the initially truncated response.                               |
| `docs/research/candidates/degraded_incumbent_shadow_handover/N3_DISH_B01_C04_RESULT_EVIDENCE_20260904.md`                  | Full file.                                                                                                                               |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_PREFIX_TRIGGER_FUNNEL_A01_RESULT_EVIDENCE_20260905.md`   | Full file.                                                                                                                               |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_GROUND_SOURCE_POINT_A02_RESULT_EVIDENCE_20260905.md`     | Full file.                                                                                                                               |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_GROUND_SOURCE_POINT_A02_SUMMARY_20260905.json`           | Full JSON.                                                                                                                               |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_GROUND_SOURCE_POINT_A02_INTAKE_20260905.md`              | Full file; recommendation treated as advice, not an executed decision.                                                                   |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R05_HOST_GENERATOR_AND_RNG_MANIFEST_20260821.md`    | Lines 1–210, including complete §§1–5 and the start of §6.                                                                               |
| `docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RBHR_R06_SCIENCE_COMPOSITE_20260822.md`                  | Complete composite through §10.                                                                                                          |
| `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp`                | Lines 170–235 and 275–479: relevant geometry, observations, eligibility, arrival, snapshot and service paths.                            |
| `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`                                                                      | Complete specification through §11.7.                                                                                                    |

**Unread manifest paths: none.** The two explicitly scoped files were not read in their entirety. No unlisted repository path was retrieved.

## OWNER_VERDICT_ZH

**最终决定：CONTINUE，仅适用于现有 RETAIN/COPY/SHADOW 源选择探索家族。** B01 没有暴露任何源分支；A01 已排除“完全没有准备”和“提前终止填充”这两种解释；A02 的真实信号与继承定义中的近地端点遮挡一致。这不是实现错误，也不是 SHADOW 无效的证据。下一步应先明确一个语义上独立的新宿主端点规则，再用小规模 A/RECON 检查真实到达、共同 SOURCE、快照、合法动作和原生服务是否连通，不能只看射线变清或强制触发成功。新宿主规则、后续协议可达性、比较器能力及 SHADOW 增益都仍未验证。本决定不启动实验、不追加训练、不复活 R02，也不改变 Portfolio 优先级或生命周期。
