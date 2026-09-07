# DISH B06 scientific intake — 2026-09-07

**Accept one complete B/EXPLORE result: joint sampled execution loses 77.5 mean native
service ticks to modal execution of the same trained controller.** The frozen adverse and
zero-transfer branches apply. Retain the modal default in this instance and stop adding runs
of this tested joint sampling rule now. This is a bounded development decision, not a general
claim against stochastic policies or a closure of the RETAIN/COPY/SHADOW direction.

## 1. Evidence, rule and independent unit checked

Root/Portfolio task `P07-DISH-INTAKE-REFILL-01` requests this intake and next-question preparation,
with no invocation, source edit or Pro Send. No earlier B06 scientific intake was present.
The [E0 result](DISH_SAMPLED_EXECUTION_B06_RESULT_EVIDENCE_20260907.md), integrated at
`33db0d86016882d3e6d1c4dc1058dc0d8fe55bf6`, is compared with the unchanged
[frozen card](DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md) §§4–7 and evidence-spec
§§4, 5.2, 11.4 and 11.8. Current source/scope specifications introduce no change to this rule.

I read the raw summary, paired primary, actual learner curves/configuration and all sixteen
episode rows, final stdout, CM technical acceptance, resource receipt, OS time and supervisor
start/exit evidence under `sampled_execution_b06_20260907_run01/`. Read-only Python recomputed
the primary and native comparisons from those rows; [DM readback](sampled_execution_b06_20260907_run01/DM_READBACK.json)
records the results and checked mapping. Summary and paired primary agree; stdout adds only
the two final wall fields. All four coordinate groups retain identical reference/modal/sample
resets, exactly samples0/1, and the declared checkpoint updates. All16 learner curves have
finite loss/gradient receipts and both original groups at3e-5. Actual master digests match the
two frozen laws. I reused the already accepted source review/checks, without executing a model,
learner, native episode, source test or historical replay.

The independent training unit is **one seed113 LOW_LR controller**. The four conditions are a
fixed panel; the two stochastic episodes per condition are finite measurements of that same
controller, not eight training replicates. Average the samples within condition, then average
the four contrasts. No training-population CI, bootstrap over conditions or all-seeds-positive
test is warranted. Source is `373d187200a91942385e9380770dcf9f8098aada`, `wsl_4070`, native
float64/policy FP32 and one CPU compute thread. The comparison changes ordinary execution law
jointly while holding final weights, log_std, prediction heads and checkpoint Welford fixed.

## 2. Service result and initialization comparison

| Condition | Initial modal | Final modal | Sample0 | Sample1 | Sample mean minus modal | Modal minus initial | Sample mean minus initial |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 250 | 459 | 362 | 371 | -92.5 | +209 | +116.5 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 359 | 593 | 497 | 607 | -41 | +234 | +193 |
| TERRAIN_RELAY_MASK / K8 | 417 | 454 | 364 | 356 | -94 | +37 | -57 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 453 | 1143 | 1146 | 975 | -82.5 | +690 | +607.5 |
| Equal-condition mean | 369.75 | 662.25 | — | — | **-77.5** | **+292.5** | **+215** |

Final sampled mean is584.75. Delta_exec is -11.70% of this modal mean, -6.46% of the fixed
1200-tick horizon, and -3.23 times the card's24-tick scale. All four condition means are below
-24. These observations support the bounded adverse reading without a claim of stable
superiority of modal execution. Two individual samples beat their modal comparator (+14 and
+3); keeping them does not change the fixed two-sample primary or justify best-sample selection.

`D_modal=+292.5` is a same-interface before/after observation including learned weights and
Welford changes. `G_sampled_vs_init=+215=D_modal+Delta_exec` combines learning and an interface
change; it is not a third independent learning result. The positive overall sampled/initial
mean retains TERRAIN/K8's -57 row. No reference row is an upper, tuned baseline or source-value
estimate. The host still has no tuned same-information baseline versus stated upper headroom
record. B06 is not another CONTROL/LOW_LR pair and does not revise the earlier paired LR effects.

## 3. Native adverse facts and limits on mechanism meaning

| Panel | Episodes / stepped ticks | Invalid commits, raw total | Mean per episode | Energy mean | Legal transfers |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial modal | 4 / 4800 | 31 | 7.75 | 268778.5278 | 0 |
| Final modal | 4 / 4800 | 14 | 3.5 | 273979.2808 | 0 |
| Final sampled | 8 / 9600 | 255 | 31.875 | 278621.9235 | 0 |

The means use the declared equal-condition weighting after averaging each two-sample group;
the255-versus14 raw totals alone are not the comparison because the episode counts differ.
Sampled invalid commits increase by28.375 per episode on average, and by56/4/45/8.5 in the
four condition means. Energy increases in every condition mean, overall +4642.6427 (+1.69%).
Every row executes its complete1200 ticks, so these energy contrasts do not hide shorter
survival. All other six evaluation hard-event classes are zero. Event counts are not failure
probabilities per commit opportunity, and zero recorded events do not establish safety.

Every reference and final row has zero legal transfers, a null first-transfer tick, zero
post-transfer service and no unstepped remainder. Native terminal is the fixed-horizon end;
there is no early evaluation termination. Ordinary training separately records1030 invalid
commits,3 separation breaches,35 terminal events,26159 service ticks over65536 transitions,
and zero legal transfers. Do not pool these training events with final-evaluation rates.

The causal chain remains degradation/renewal -> local observation and messages -> role-owned
recurrent state -> joint motion/prepare/commit execution -> native projection/certificate/
ownership consequences -> service, energy and events. Sampling changes trajectories and later
recurrent inputs; the comparison does not isolate motion noise, intent noise, their interaction,
label quality, normalization or a cause of past LR gains. A larger invalid-commit count does not
uniquely locate the cause in Bernoulli intent sampling. There is still no observed first legal
application cut for origin eligibility or matched COPY–RETAIN/SHADOW–COPY value. Zero transfer
here does not prove transfer impossible or SHADOW worthless.

Strongest support for retaining modal is the negative fixed primary, all four adverse condition
means, and increased event/energy costs. Strongest limit is one training instance and two finite
samples per condition; the two positive individual samples, positive overall learned/initial
means and untested execution alternatives remain visible. Earlier B05 support (+236.25 LR mean)
and contradictions (-277 condition,209 invalid commits), plus B04's initial-relative loss,
retain their original scope. No historical result is reclassified.

## 4. Frozen branches applied verbatim and prediction scored

The following two card §5 rules apply verbatim:

> `Delta_exec<=-24`，或正均值伴随严重 native 代价
>
> 在本例倾向保留模态默认、不扩展该联合抽样规则；预测命中也不是原因定位。若仍有换主，则是带成本的路径事实，不能挽救服务负结果为“来源成功”。

> 全部最终评价无合法换主
>
> 原生执行法则比较仍可读，来源量仍未估计；不说宿主不可能换主、抽样无支持的普遍定理或 SHADOW 无价值。

| Frozen row | Application |
| --- | --- |
| 1: Delta_exec>=+24 with worthwhile native trade-off | Not triggered: -77.5 |
| 2: sampled improves relative to modal but remains clearly below initialization | Not triggered: the relative difference is negative and the overall initial-relative mean is positive; keep the negative TERRAIN/K8 row separately |
| 3: mean in band, or finite sample/condition variation leaves development value unclear | Not the selected primary reading: all four condition means are below-24 with adverse mean costs; finite-sample and seed uncertainty still limit generalization |
| 4: Delta_exec<=-24 or severe native cost | Triggered by the numerical predicate itself; no new severity threshold is needed |
| 5: an ordinary legal transfer occurs in either final mode | Not triggered |
| 6: no final legal transfer | Triggered for all12 final rows |
| 7: learning/input/primary damaged or incomplete | Not triggered: the complete learner and primary are readable; optional resource gaps do not damage them |

The recorded DM and Pro prediction **Delta_exec<=-24, low confidence**, is a **magnitude/sign
hit** at -77.5. No probability was recorded, so this is not calibration or mechanistic evidence.
The competing >=+24 worthwhile-gain observation did not occur. Owner prediction: **not taken**;
current reviews supplied no prediction reply. No minimum-transfer prediction was made or scored.

## 5. Exposure, receipts, cost and engineering conformance

One initializer and one real learner complete16×32×128=65536 ordinary transitions and
16×4×8=512 optimizer steps; update16 is the only selected final checkpoint. Parameter L2
movement is1.7112413585 from initial norm38.2481838816, relative0.04474046046. Evaluation is
4 initial +4 final modal +8 sampled =16 complete episodes and19200 actual ticks. There is no
source fork, extra training instance, resampled bad row or checkpoint search.

Eligible private-label E=7631, next-label steps65536 and next-mask count65501 remain separate
from ordinary exposure. H is unmeasured with0<=H<=152620, so native training calls2N+2E+H
are bounded146334–298954. Sampled evaluation R=1240 gives4960 normals,2480 Bernoullis and12400
uniform draws; these are original algorithm work, not added validation or independent episodes.

The sole handle `dish_b06_seed113_20260907_run01` starts2026-09-07T12:55:15Z and exits0 at
12:58:50Z, supervisor duration215s. Actual same-node admission at12:55:15.489434Z passes both
memory floors with15665545216 bytes versus4294967296 required. Git HTTPS/lazy-fetch failures
and the committed-object bundle repair occurred before scientific launch and remain staging
facts; they are neither negative scientific evidence nor additional accepted invocations.

OS whole-chain wall215.02s plus earlier10s checks and CM's conservative1s collection readback
charge gives **226.02s for this valid result**, below the original1800s complete cap. The
runner's narrower204.713815717s plus resolved prior11s is not substituted for that whole-chain
measurement or added again. OS user+system CPU221.09s covers this chain; earlier-check CPU is
unmeasured. Supervisor elapsed215s is integer precision; status uptime was query age. Control-
plane staging, interpretation and Git integration are not another result invocation. Unused
cap is not permission for another seed or retry.

OS maximum RSS656375808 bytes and runner self/reaped-child maxima635867136 bytes have different
scopes; do not sum the latter as a simultaneous process-tree peak. Scratch is unmeasured,
`resources_unmeasured` remains true, and the native primary remains valid. No engineering-scope
§4 addition or §5 budget breach is recorded; no source changed in this intake. Technical
conformance and scientific adverse performance are distinct findings. New scientific exposure
from this read-only intake and next-question preparation is zero.

## 6. Question-driven source coverage and what it changes

The narrow retrieval question was whether local primary evidence supplies a reason to expand
joint sampled execution after this result, or isolates a specific component explanation.
The existing My-lib registry still contains only P-SYN-001/P-SYN-002 in `synthetic-core`, both
explicitly synthetic; exclude them. This is verified coverage of that entry point, not a claim
that all local literature is synthetic. Inst-sci's real `llm-index/catalog.v2.jsonl` has190
records. Searches over exploration, stochastic/deterministic policy, hybrid/parameterized action,
continuous control and action masking returned47 broad candidates; the narrower execution-law
terms left MARL-0056, *TAPE: Leveraging Agent Topology for Cooperative Multi-Agent Policy Gradient*
(AAAI2024, DOI10.1609/aaai.v38i16.29699).

I checked its metadata and source `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0056.json`,
abstract/Introduction and the agent-topology definition. The topic is which agents' utilities
enter policy-gradient updates for stochastic or deterministic MAPG. It does not supply a
same-checkpoint Gaussian-motion/Bernoulli-intent comparison or a diagnosis of B06. This verified
scope prevents treating the keyword hit as support for a new noise arm; no novelty verdict or
universal literature absence is inferred. The development recommendation rests on the native
comparison. A causal explanation remains open and is not a prerequisite for accepting it.

## 7. Decisions this intake produces and prepared next question

1. **Object-tier scientific acceptance.** Options: (a) accept the complete B result and apply
   rows4/6 with all costs/limits; (b) limit the primary for a concrete missing dependency;
   (c) treat a resource gap or staging failure as scientific annulment. Recommend/select **(a)**.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
2. **Object-tier bounded development stop.** Options: (a) retain modal here and stop adding
   runs of this tested joint sampling rule now; (b) buy another unchanged training seed;
   (c) select a component/noise/source search after seeing the result. Recommend/select **(a)**.
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This stops the named
   treatment's current extension; it does not declare a population null, consume a B object,
   close the broader family, PARK the direction or change Portfolio state.
3. **Direction-tier recommendation, prepared only.** The proper next node is
   `em:degraded_incumbent_shadow_handover:convergence`, `caller_role=em`, `em_convergence`.
   Ask whether to stop this joint-execution exploration branch with no new object, or select
   exactly one specifically justified bounded B inside the still-open source agenda. Recommend
   the narrow stop on the tested rule and **no additional invocation now**. The strongest
   concrete alternative is one new independent LOW_LR training seed with the unchanged
   modal/two-sample comparison, if training-seed uncertainty is valuable enough to buy. A
   component-only law could behave differently, but B06 did not isolate its benefit; do not
   silently turn that possibility into an arm sweep, action search or mandatory diagnosis.

The existing B06 reduction already answers the selected finite performance question. Another
sample, exact action maximum, source-support census or replay is unnecessary for that reading.
The one-seed B alternative would genuinely measure a new training instance:65536 transitions,
512 optimizer steps and16 episodes/at most19200 ticks, private calls2N+2E+H with new E/H/R
unknown. B06's226.02s is a planning anchor, not a completion promise. A proposed fresh1800s
whole cap would include changed-input checks, build/load and publication; it is not inherited
unused balance and is **not selected here**. A negative result does not forbid a justified new
B under §11.8.2; the current evidence supplies no automatic entitlement to one either.

The preparation-only GitHub handoff is in `pro_packets/20260907_post_b06_convergence/`.
It pins this intake, result, card and controlling specifications, reuses Issue4 and the existing
Convergence conversation, and requests a direction-local choice only. No new question has been
sent or answered. A broad closure/recast, C promotion or Portfolio priority/lifecycle change is
not locally substituted. The direction returns at this clean boundary to Root/Portfolio for
the command that operates the prepared handoff; this is not a new owner approval gate.

Owner flags: **none**. No material critic dissent is overruled, no close call or second recast
is recorded. Primary-checkout `item.py reviews --json` returned `[]`; relevant audit owner
columns were empty. No review required marking answered. The existing P1/P2-only owner skill
keeps ordinary intake/prediction/technical decisions in this document and the audit, without
manufacturing a higher-priority item. The required [Chinese owner brief](../../portfolio/owner/briefs/degraded_incumbent_shadow_handover/2026-09-07_B06.md)
is written. DIRECTION.md receives the bounded accepted science; Portfolio owns its own snapshot.
