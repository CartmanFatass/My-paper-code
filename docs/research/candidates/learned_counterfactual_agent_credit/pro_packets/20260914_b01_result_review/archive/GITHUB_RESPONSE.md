The DM's small-negative, within-MEI reading is scientifically supportable. I narrowly prefer one fresh, symmetric **1024-train/32-final comparison** over immediately repeating 256/32: the more useful development question is whether this package warrants pursuit at a substantially later finite endpoint, not merely whether early-budget near-parity recurs. This preference is uncertain, not evidence that 1024 is necessary or sufficient. A concrete prospective correction is required: carrying the existing reset-seed offsets unchanged into 1024 episodes would overlap training and final worlds. B01 itself is unaffected. [Frozen card, “Pair, exposure, records and native primary”][card]; [DM intake, alternatives][intake].

## Result integrity and its exact meaning

The raw summary and archived intake arithmetic agree on Q−V=−0.003626428416, V=0.180680770130 and Q=0.177054341714. This lies inside the card's inclusive ±.01 band; it is not the below−.01 branch, equivalence, or positive evidence. Preserve all 32 worlds: 16 are adverse, with descriptive SD .01318814 and range [−.04021500,+.02108230]. Equal positive/negative counts do not cancel unequal magnitudes or justify deleting adverse worlds. The low-confidence positive prediction missed the sign; its uncertainty does not convert that miss into success. [summary.json, `primary`][summary]; [ANALYSIS.json, `primary`][analysis]; [result, “Frozen rule and observed result”][result].

Both arms report 256 training and 32 final episodes, 128 rollouts and 512 Adam calls; pair totals are 147,456 native ticks and 1,024 updates. The supplied records show no primary/count inconsistency requiring invalidation. They support one completed B/EXPLORE learning-package comparison, not an independent reproduction of its execution. The 32 final worlds describe these trained policies under the fixed paired panel; neither a training-population interval nor an equivalence test belongs in this frozen descriptive result. [summary.json, `arms`, `complete`][summary]; [card][card]; [empirical topic, randomness hierarchy][empirical].

## Real learning occurred; competence remains uncertain

The scalar comparator was not merely a fixed rule: V actor/critic relative displacements are .175213/.525791, versus Q .176046/.522030, with movement in every rollout. This is meaningful evidence of actual optimization and rules out complete accidental freezing at the recorded parameter-block level. Parameter displacement is not policy improvement, calibrated values, or adequate finite-budget competence. [ANALYSIS.json, `arms.*.total_movement` and movement counts][analysis].

A useful additional deduction follows from the recorded norms and the card's separate .5 thresholds: V's critic minimum preclip norm is 1.36034, so every recorded V critic epoch clipped; both actors' maximum norms are below .055, so their own clipping never activated. This does not establish an Adam update bottleneck, and the separate blocks prevent the old global-clip coupling. Do not prescribe changed clipping or normalized critic targets as a demonstrated repair. [ANALYSIS.json, `epoch_extrema`][analysis]; [card, algorithms][card].

V prefit MSE falls from 450.94 to 245.41 across the first/last 16-rollout averages; Q falls from 448.07 to 237.05. Those changing-world, changing-policy residuals neither prove underfit nor establish calibration. Q's factual `G−Q(s,a)` residual is also not the marginalized actor baseline residual `G−b_i`, much less policy-gradient variance. Entropies near 1.94 versus log(7)=1.94591 raise a legitimate concern about limited policy differentiation, not proof of useless policies or a guaranteed benefit from longer training. Absolute returns and descriptive training-score shifts lack a matched initial-policy evaluation establishing learning gain. [ANALYSIS.json, residuals, entropy and training scores][analysis]; [result, “Learning and claim limits”][result].

The strongest competing explanation is that action conditioning supplies little useful baseline differentiation, or extrapolation offsets its benefit, rather than merely needing more updates. The prefit freeze, factual targets, identical decentralized actors/private recurrence and separate clipping retain comparison integrity as specified; Q's extra 4,480 parameters, normalized/clipped PPO and approximate recurrent replay remain part of the package. No isolated causal-credit or variance-reduction conclusion follows. [Card, algorithms][card]; [prior review, material findings][prior]; [FOUNDATIONS §§3–4][foundations].

## Which next observation changes the decision?

One fresh same256/32 master9412 pair is a legitimate, economical replication. Its strongest value is revealing a substantially different early-budget outcome without changing the algorithm or endpoint. However, a fresh master also changes final worlds/action draws: between-pair differences mix training variation and finite-panel variation, not pure training-seed variance. Another within-band result would still leave the main finite-budget concern open. Two pairs would not establish stable near-equality. The DM should not select it simply because seed variation is unknown or the first runner was inexpensive. [Card, seed schedule][card]; [intake][intake]; [empirical topic][empirical].

I instead recommend asking: **at a preselected 1024-episode budget, does Q deliver a practically interesting same-task advantage over an equally trained V?** Use one newly initialized matched pair, unchanged algorithms, four epochs, one final checkpoint and all 32 final worlds per arm. Retain the existing learning records, without extra diagnostics, intermediate evaluations, checkpoint selection, or hyperparameter changes. This extends the development range rather than repeating the already observed short-budget question.

The strongest objection is substantial extra work for another single training unit, with no guarantee of more competent policies. Moreover, comparing its result with B01 cannot identify a causal training-duration effect: training identity and panel also change. Accept that narrower claim instead of adding a budget-by-seed matrix. The earlier 256 preference was first-observation advice, not a permanent endpoint rule; the observed active-but-high-entropy learning now makes later-budget exploration a reasonable close-call preference. [Prior review, contrary case][prior]; [intake][intake]; [specification §§11.8–11.9][spec].

PARK remains defensible when neither observation is expected to change development choices enough to justify complete cost. It is not warranted by a missing theorem, positive pilot, tuned headroom, or failure to obtain all-positive seeds. [Specification §§5.2, 11.8–11.9][spec].

## Work and the narrow prospective repair

Both alternatives use two arms, one independent pair, H256 and one 32-episode final panel per arm:

| Endpoint | Pair native ticks | Adam calls | Q baseline rows | Total factual-fit rows |
|---|---:|---:|---:|---:|
| 256/32 | 147,456 | 1,024 | 2,293,760 | 524,288 |
| 1024/32 | 540,672 | 4,096 | 9,175,040 | 2,097,152 |

These supplied counts include intrinsic 35-row focal marginalization, not `7^5` native calls or trajectory search. Fourfold learning work is not a measured runtime bound. Native stepping, recurrent collection/replay, backward passes and publication remain material. [Intake, work factors][intake]; [card, work accounting][card].

The recorded 129.80 seconds is complete runner wall, not complete research cost. V/Q body clocks of 61.8005/63.7314 seconds omit shared setup/publication and do not establish a stable marginal Q cost. Peak 569,916 KiB is process RSS; CPU, full support/provider and lifetime costs remain unknown. Overlapping check/SSH timings must not be blindly summed. No mandatory profiler follows from those gaps, and ordinary wall plans are not scientific endpoints. [Result, “Complete cost and execution”][result]; [ANALYSIS.json, `cost`][analysis]; [runtime specification §§1–3,6][runtime].

**Prospective leakage risk:** the card sets training resets to `base+1000+episode`, finals to `base+2000+episode`. At 1024 training episodes, training indices 1000–1023 reuse final reset seeds 0–23. This is a deduction from the formulas, not an observed B01 defect or a claim about unlisted implementation code. Prospectively move final resets to a disjoint range, for example `base+3000+episode`, retaining across-arm pairing and independent action streams. A focused seed-range/count binding check suffices; no native pilot is needed. [Card, seed schedule][card].

Any successor stops at its declared pair. Above-MEI performance may motivate independent replication at that endpoint; another small/adverse result may favor PARK. Neither outcome automatically authorizes continuation or refutes counterfactual methods. Keep endpoint budgets separate in the existing per-master summarization; do not pool worlds as training replicates.

## Preservation and access limits

All eleven listed evidence paths were accessible at their manifest-pinned versions; source links below identify each version. I read the card, result, intake, summary, analysis, prior review and applicable methods/foundational passages. No code, tests, models or scientific execution occurred. Unlisted execution source, raw episode/rollout logs, checkpoints, collection hashes and technical-review artifacts were not independently inspected: their verification remains reported provenance, not new certification.

Preserve the first-design advice, historical unallocated 512 offer, zero recasts and contrary MGTAP history retained there. No convergence, optimality, continuous-action, tuned-headroom, scale, safety or C claim follows. DM owns the successor/lifecycle/resource decision and must answer these findings. The task's explicit three-slot limit supersedes the pinned AGENTS' older four-slot wording; this review changes no global layout. [Prior review][prior]; [card][card]; [FOUNDATIONS §6][foundations]; [AGENTS §§1–5][agents]; [task, caller constraints][task].

[card]: https://github.com/CartmanFatass/My-paper-code/blob/22260a8e3a5b352412e34b25a779f299ab781f54/docs/research/candidates/learned_counterfactual_agent_credit/LCAC_B01_SCIENCE_CARD_20260914.md
[result]: https://github.com/CartmanFatass/My-paper-code/blob/631ffab0142b2e548120cd483350472ce124293e/docs/research/candidates/learned_counterfactual_agent_credit/LCAC_B01_RESULT_EVIDENCE_20260914.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/631ffab0142b2e548120cd483350472ce124293e/docs/research/candidates/learned_counterfactual_agent_credit/LCAC_B01_INTAKE_20260914.md
[summary]: https://github.com/CartmanFatass/My-paper-code/blob/631ffab0142b2e548120cd483350472ce124293e/docs/research/candidates/learned_counterfactual_agent_credit/evidence/b01_seed9411/raw/summary.json
[analysis]: https://github.com/CartmanFatass/My-paper-code/blob/631ffab0142b2e548120cd483350472ce124293e/docs/research/candidates/learned_counterfactual_agent_credit/evidence/b01_seed9411/ANALYSIS.json
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/b98a5f084107143fc8650b34a3ff8b06312002fe/docs/research/candidates/learned_counterfactual_agent_credit/pro_packets/20260914_first_design_review/archive/RESPONSE.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/c627c78a7a760bbe0e61533ee505702675cb224f/AGENTS.md
[spec]: https://github.com/CartmanFatass/My-paper-code/blob/c627c78a7a760bbe0e61533ee505702675cb224f/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/c627c78a7a760bbe0e61533ee505702675cb224f/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[foundations]: https://github.com/CartmanFatass/My-paper-code/blob/c627c78a7a760bbe0e61533ee505702675cb224f/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[empirical]: https://github.com/CartmanFatass/My-paper-code/blob/c627c78a7a760bbe0e61533ee505702675cb224f/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[task]: https://github.com/CartmanFatass/My-paper-code/blob/03cf46b88065eb141b9b6be015785590bb1054a7/docs/research/candidates/learned_counterfactual_agent_credit/pro_packets/20260914_b01_result_review/TASK.md
