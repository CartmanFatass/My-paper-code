**Retain the reversible PARK boundary for the current selected-panel balanced residual family, and select no further B experiment at this node. B08 yielded a common low-regret native action vector with genuine historical gains and REPLAN losses, but no additional aligned action value against either matched control. Its recorded new RAW baseline also leaves less possible improvement than the original 0.0025 alignment margin. No distinct next discriminator is sufficiently specified to justify extending this comparison now.**

This is an investment decision about this family and its current question, not CLOSE, RECAST, a competent residual negative, or a finding that useful further learning is impossible. Preserve B08 as **WEAK_NEW_RAW_LONG_DIAGNOSTICS_ONLY**. The failed exact-count qualifier does not erase trustworthy native measurements; the positive historical comparisons do not replace the failed matched comparisons. The concrete yield is a successful real-learning observation with lower aggregate regret than the historical references, a visible KEEP/REPLAN tradeoff, zero measured alignment contrasts, and an outcome-informed limit on this fixed-baseline improvement claim. [P71 intake, §§2–3][intake]; [readiness, “The one decision and the DM recommendation”][readiness].

## What the completed observation establishes

B08 is complete, not awaiting its first allocation. The card's original zero-allocation status describes its prospective freeze. The later accepted P71 intake records the authorized invocation, terminal collection, complete primary measurements, and scientific reading. The runtime receipts report 96 checked legal native decisions, zero maximum regret-recalculation discrepancy, and agreement of the historical comparison rows with the fixed input. This is observed comparator weakness, not a missing-output or execution failure. I use those accepted checks and the directly read result fields; I have not rerun their numerical validation. [Card, opening status and §§1–4][card]; [P71 intake, allocation history and §1][intake]; [runtime receipts, `technical_collection_checks.json`][receipts].

The native action vectors agree across RAW, TRUE_RESIDUAL, and CALIBRATED_DERANGEMENT at both update 33 and update 258. Each contains eleven KEEP decisions and five RELAY-L decisions. The endpoint summaries are identical:

| Quantity, for each arm at each observed endpoint | Recorded result |
| --- | ---: |
| KEEP exact actions | 8/8 |
| KEEP mean regret | 0 |
| REPLAN exact actions | 5/8 |
| REPLAN mean regret | 0.004258908986119771 |
| Equal-side native regret | 0.0021294544930598857 |

New RAW-LONG satisfies both side-mean regret limits, but five exact REPLAN decisions do not satisfy the required six. Historical RAW-LONG competence cannot be substituted. Nor can the sixth-action threshold be relaxed after observing how little separates the count from its criterion. Conversely, the failed qualifier is not a total ordering of native value: B08's aggregate regret is lower than historical competent B04 RAW-LONG's 0.0037814300857039115. [Original result, `representations.RAW`, `representations.TRUE_RESIDUAL.LONG`, `representations.CALIBRATED_DERANGEMENT.LONG`][result]; [DM analysis, `endpoints` and `observed_policy`][analysis]; [card, §4][card].

With positive differences favoring new TRUE, the three distinct native comparisons are:

| Endpoint | New RAW minus TRUE | New DERANGED minus TRUE | Historical B04 RAW minus new TRUE |
| --- | ---: | ---: | ---: |
| SHORT, 33 | 0 | 0 | +0.0044524264964700775 |
| LONG, 258 | 0 | 0 | +0.0016519755926440258 |

No endpoint meets the original conjunction. At SHORT the historical-reference gain exceeds 0.0025, but both matched contrasts are zero and new RAW-LONG is weak. At LONG the historical-reference gain is also below 0.0025. It exceeds the separate 0.000625 diagnostic margin, which does not replace the residual MEI. The historical-reference protection therefore does its intended job without turning improvement against an older policy into alignment success. [Original result, `contrasts.SHORT` and `contrasts.LONG`][result]; [P71 intake, §2][intake].

The correct interpretation is stronger than “nothing can be said” and narrower than “residuals failed.” All measured paired native gains against the two new controls are zero. That remains a direct fact even without the competence qualifier. What remains unavailable is the registered competent-comparator residual polarity. Identical actions on sixteen histories at two readouts do not establish identical functions, representations, logits, learning trajectories, or behavior at unobserved updates and histories. The agreement at 33 and 258 does not certify a constant policy at every intervening update. [DM analysis, `all_three_action_vectors_identical`, `observed_policy`, and arm exposure records][analysis]; [P71 intake, §§2–3][intake].

## Native improvement is real, and includes losses

All three arms improve descriptively over their own historical B04 endpoint regrets:

| Representation | SHORT improvement over its own history | LONG improvement over its own history |
| --- | ---: | ---: |
| RAW | +0.0044524264964700775 | +0.0016519755926440258 |
| TRUE_RESIDUAL | +0.015984557591254618 | +0.008786079220940025 |
| CALIBRATED_DERANGEMENT | +0.007361613692673553 | +0.007521890372510694 |

These are useful native measurements on the exposed panel. They are not three independent replications, and the large recovery of TRUE from its older, worse value does not identify an advantage over the new containing RAW or the derangement. “Improvement observed under the common objective” describes the intervention and result; it does not prove a generic-objective or preprocessing mechanism. [DM analysis, `endpoints.*.arms.*.native_improvement_over_own_history`][analysis]; [P71 intake, §3][intake].

The historical RAW comparisons retain the following accounting:

| New TRUE versus historical RAW | SHORT | LONG |
| --- | ---: | ---: |
| Gain / loss / unchanged rows | 7 / 3 / 6 | 3 / 2 / 11 |
| Sum of positive native gains | +0.10531009583247941 | +0.04913810886352182 |
| Sum of negative native gains | −0.03407127188895817 | −0.02270649938121741 |
| Net gain over sixteen rows | +0.07123882394352124 | +0.026431609482304413 |
| KEEP mean native gain | +0.013163761979059926 | +0.003754710220270765 |
| REPLAN mean native gain | −0.004258908986119771 | −0.00045075903498271314 |

At SHORT, seven KEEP improvements outweigh three REPLAN losses. At LONG, two KEEP gains and one REPLAN gain coexist with two REPLAN losses; the REPLAN side still worsens in aggregate. The absence of an adverse aggregate primary contrast does not imply absence of harmed rows. Similarly, the recorded `mixed_budget=false` reading does not erase this within-panel tradeoff. [P71 intake, §§2–3][intake]; [DM analysis, `endpoints.*.comparisons.historical_B04_RAW`][analysis].

The common action vector has three remaining errors, all KEEP where TRANSIT-R is the native oracle:

| Row identity | Native regret |
| --- | ---: |
| `0/EVALUATION/K8/850/156/0` | 0.011387685355538746 |
| `1/EVALUATION/K8/858/156/0` | 0.011318814025678664 |
| `7/EVALUATION/K8/879/108/0` | 0.011364772507740761 |

All three are losses relative to historical RAW at SHORT. The first two are also losses at LONG; the third remains a native error but is not an additional loss relative to historical RAW-LONG. These identities are recorded evaluation evidence, not a selected training curriculum or permission to target the exposed mistakes. [DM analysis, `observed_policy.mistakes` and historical comparison `loss_details`][analysis]; [original result, sampled native rows and signed historical contrasts][result].

The strongest countercase to retaining PARK is therefore substantial: the objective package reaches much better native decisions than historical TRUE, the containing learner also improves, and meaningful errors remain. One could conceivably improve some of those actions. A failed exact-count qualifier cannot turn that learning into a null, and the existence of only one reused seed cannot annul a trustworthy B observation. These facts keep narrower learning questions alive; they do not by themselves specify another original-margin alignment discriminator.

## What the recorded-baseline ceiling means

The card's equally weighted eight KEEP and eight REPLAN rows make native regret a sixteen-row mean. For the same rows and labels, let G_i(a) denote the native consequence and G_i* the best legal label. Then the accounting is

$$
R(T)=\frac{1}{16}\sum_i\bigl[G_i^*-G_i(a_{T,i})\bigr],\qquad
R(RAW)-R(T)=\frac{1}{16}\sum_i\bigl[G_i(a_{T,i})-G_i(a_{RAW,i})\bigr].
$$

Every correction and every new loss enters that second expression. Because native regret is nonnegative, the improvement against the recorded new RAW cannot exceed its measured regret:

$$
R(RAW)-R(T)\le 0.0021294544930598857 < 0.0025.
$$

This is the supplied recorded-byte arithmetic, not a new learner result or an optimization performed in this consultation. The corresponding maximum total gain is 0.03407127188895817, below the required strictly greater than 0.04. It applies at both observed endpoints, independently of whether the exact-count qualifier passes. [Card, §4][card]; [EXPOSURE, recorded gain ceilings][exposure]; [DM analysis, endpoint arithmetic bounds][analysis].

Even correcting all three recorded errors without creating another error cannot establish original-MEI improvement against this fixed new RAW. Correcting one may produce a useful diagnostic gain and alter a competence count; it is not sufficient for the distinct 0.0025 alignment question. Perfect correction is an upper allowance in this arithmetic, not a claim that such a policy is accessible to the learner. The smaller diagnostic margin stays 0.000625 and is not promoted to replace the residual margin.

The bound does **not** establish a maximum over the policy class, a tuned same-information headroom record, an information limit, a global equivalence, or impossibility on another independently motivated population or exposure definition. It does not establish that no smaller native improvement is valuable. It also does not invalidate B08 retrospectively: the experiment legitimately revealed the low-regret comparator that now limits this particular contrast. [P71 intake, §3][intake]; [evidence specification, §§11.7–11.8.2][spec].

This is a reason not to keep repairing the present comparison in pursuit of its unchanged margin. It is not a reason to require an exact upper, a headroom-training experiment, or a positive pilot before a different justified B. A worse post-hoc reference, removal of these low-regret RAW results, a reduced MEI, or a search for a favorable seed or panel would change the question rather than answer it.

## Why retain the boundary rather than extend the ladder

The strongest support for PARK is the combination of an informative completed intervention, no aligned action difference against either common-objective control, the fixed-reference arithmetic limit, and the absence of a particular new action-credit proposal that resolves something beyond this outcome. It is not the REPLAN count alone, an infrastructure problem, accumulated expense, or missing C-level evidence. The DM recommendation reaches the same choice, but remains advice rather than supporting evidence. [Readiness, recommendation and countercase][readiness]; [P71 intake, §§2–3 and 5][intake].

The completed intervention addressed the previously specified gap. Its source uses equal-row expected native cost over a masked softmax, constant labels, scale 0.01, and the same objective in all three arms. Training preserves the real gate, Adam updates, canonical batches, and deterministic native readout. The option-owning slot still receives its partial common history and declared packet; replacement is charged once and measured over the common sixteen-step four-agent future. There is no new information, roster intervention, partner adaptation, or changed host consequence. [Accepted source, `expected_native_cost_loss`, `train_path`, `paired_contrast`, and `score_summary`][code]; [card, §§2–4][card].

Common objective behavior, probability saturation, shared-parameter effects, calibration, and seed-dependent optimization remain plausible explanations for agreement. None is identified uniquely. In particular, lower expected softmax TRAIN loss need not change the deterministic legal EVAL argmax; changed losses and parameter displacement can coexist with the same endpoint actions. The source's probability-weighted credit makes saturation a plausible question, not an empirical diagnosis. Likewise, agreement after derangement does not prove that packets are ignored: the common histories remain available, and no history-only or packet-removal comparison was run. [Source, loss and readout functions][code]; [card, §§2–3][card]; [DM analysis, arm exposure and policy records][analysis].

A distinct credit intervention is the strongest continuation alternative. However, naming another loss, an entropy term, a different temperature, or more updates is not yet a decision-relevant answer here. On the unchanged sixteen-row comparison, success limited to correcting the three current errors remains below the original margin against the retained RAW result. A larger or differently scoped learning question could be legitimate, but its scientific purpose cannot be inferred merely from those errors or from the need to create more measurable room. I select no such change now.

An independent-training-seed comparison could legitimately study repeatability under §11.8.3. It is not inherently a forbidden experiment or a demand for all-positive seeds. But the present choice does not automatically select that follow-up, reinterpret another seed as a repair of the known seed-0 ceiling, or use seed variation to search for an alignment-positive outcome. The missing item is a specifically justified next observation for this direction, not evidence that every plausible mechanism has already been disproved. [Evidence specification, §§11.8.2–11.8.3][spec].

CLOSE or a mechanism recast would overstate the result. B04 remains the one competent seed-0 residual negative under its own objective and endpoints. B05's comparator limitation, B06's KEEP-side native gain, and B07's offsetting legal-action changes retain their meanings. B08 neither adds an independent competent negative nor rescues the B04 intervention. The prior re-entry selected B08 only, not an arbitrary repair ladder. A/B objects have no consumption state; completing the allocated B08 batch is not exhaustion of a scientific family. [Direction, final three sections][direction]; [prior complete response, “Preserve the contrary evidence” and “Limits and direction effect”][prior]; [P68 intake, §§3–4 and 6][p68intake].

## The missing discriminator that could change this decision

Re-entry remains possible on the specification of a justified B, not on prior experimental success. The missing discriminator is a concrete legal-action or credit intervention whose next native measurement answers a question not already reduced to this common low-regret vector or to a sixth-action repair. It must identify how the intervention uses the available history and packet, what native consequence it is intended to change, and why the containing same-information RAW and calibrated derangement separate the relevant competing explanations. A complete causal diagnosis is unnecessary.

For the same original-margin alignment claim, retaining these sixteen rows and this recorded RAW reference leaves the demonstrated ceiling in force. A proposal changing population, review boundary, comparator exposure, or primary estimand must make that change explicit and justify it by a research question rather than by a desire for a weaker baseline or a larger observed gain. No particular change is selected here, and none is an implicit recast or reopening of the old natural-support family. A smaller-effect or pure comparator-learning question may be worth studying in its own right, but it cannot be presented as satisfying the unchanged 0.0025 alignment claim.

A later proposal would state the actual learner and native observable, matched information and work, declared seed scope and endpoints, and the known dominant cost factors. It would retain all native losses and interpret a weak comparator diagnostically rather than borrowing historical competence. An aligned gain would need the applicable matched comparisons; improvement without them would remain a performance fact without that attribution. Failure or native cost would update the tested intervention without automatic escalation. These are the meanings the next observation should distinguish, not a new mandatory approval layer or a requirement to freeze C-style rules before B.

No new seed, budget, dataset, host, loss, card, profile, or search is selected in this decision. No claim is made that a particular next configuration has already been costed or that it would work. The current specification allows bounded follow-up after either positive or adverse trustworthy evidence, with only the §11.4 launch conditions. Missing held-out transfer, statistical significance, independent confirmation, tuned headroom, exact support, or a unique cause is not the basis for retaining this boundary. [Evidence specification, §§11.4, 11.7, 11.8.1–11.8.7, and 11.9][spec]; [readiness, “Exposure, cost and question burden”][readiness].

## Exposure and work: what is measured and what is not

The accepted B08 work was one reused joint seed package, not six independent runs. Its dominant factors were shared host/predictor/calibration preparation and three gate trajectories, with two readouts of each trajectory:

| Actual scientific work | Recorded amount |
| --- | ---: |
| Gate optimization | 3 × 258 = 774 Adam updates |
| Gate processed examples | 3 × 258 × 32 = 24,768 |
| Shared predictor optimization | 100 × 128 = 12,800 processed examples |
| Endpoint readouts | 3 × 2 × 16 = 96 decisions on 16 identities |
| Environment transitions | 54,848 |
| Common-future native-label branch steps | 3,520 |
| Per-arm SHORT exposure | 33 updates; 1,056 examples; 22 visits per TRAIN row |
| Per-arm LONG exposure | 258 updates; 8,256 examples; 172 visits per TRAIN row |

The label work was a single legal-action fan-out with a fixed continuation. It was not a search over all joint actions or a recursively branching trajectory tree. The card's prospective host upper was 73,728 primitive team steps, including at most 64 × 8 × 16 branch steps, and its softmax-cost arithmetic upper was 198,144 action terms. Those planning bounds are distinct from the recorded actual counts. Reading historical decisions and reducing receipts add no scientific-model or native-evaluator calls. [EXPOSURE, `historical_B08`][exposure]; [P71 intake, §4][intake]; [card, §6][card].

Actual learning exposure is visible. All arms start with L2/RMS/Linf scales 18.87916908516977 / 0.10402732933491829 / 0.28862619400024414. LONG displacement-to-initial L2 ratios are 0.21999455794994616 for RAW, 0.21182928158673486 for TRUE, and 0.22742086472745415 for DERANGED. The corresponding SHORT measurements and finite last-batch losses are also retained. Movement establishes nonzero optimization exposure, not alignment value or convergence. [DM analysis, `endpoints.*.arms.*.exposure`][analysis]; [P71 intake, §4][intake].

The complete quoted command ran from 05:28:32 to 05:31:21 UTC on September 9, 2026, for 169 seconds at one-second resolution, including admission/startup, scientific work, publication, and shutdown. The inner pre-publication value of 164.3972584879957 seconds is separate. The accepted conservative arm charges are RAW 139.1011370769702, TRUE 137.73502852593083, and DERANGED 138.23890201293398 seconds; they each include the shared remainder and must not be summed as machine time. All 1,200-second arm and 1,500-second shared caps passed. [Runtime receipts, `task.log`, `complete_accounting.json`, and `account_receipt.json`][receipts]; [P71 intake, §4][intake].

Fresh actual-node admission recorded 14,403,616,768 physical and effective available bytes, above the 4 GiB floor. Peak RSS was 1,543,303,168 bytes. CPU FP32 and one compute thread were retained. Aggregate CPU time is unmeasured; 169 wall seconds is neither aggregate CPU work nor a resource-efficiency result. The old 515.3820955440096-second shared value was a projection, not actual B08 time or an available successor budget. The final receipts close the historical complete-time accounting question for this invocation without rewriting its inner summary. [Receipts, admission and complete accounting][receipts]; [P71 intake, §4][intake].

This consultation adds zero result-bearing invocations, environment/scientific-model/native/evaluator calls, and optimizer updates. Future configuration and cost remain unselected and unallocated, not free and not presumed to equal 169 seconds. There is no scientific reason to commission a full policy maximum, support census, beam search, or fresh cost pilot merely to choose this boundary. For a later justified question, a small real learner/native comparison should be preferred to a costly diagnostic unless that diagnostic has distinct decision value. A two-arm run would relinquish the existing derangement-based alignment comparison; fewer arms are not equivalent evidence for that claim. Added validation should address changed behavior and the primary output, not manufacture extra scientific arms or repeated-smoke prerequisites. [EXPOSURE, `new_scientific_exposure` and `future_work`][exposure]; [evidence specification, §§11.8.6 and 11.9][spec].

## Claim ceiling and direction effect

The empirical unit remains one reused joint training-seed package on 64 outcome-informed members, including sixteen repeatedly exposed EVAL identities, with two endpoint facets. No EVAL fitting in the new invocation removes the earlier selection of the panel, seed, objective, and endpoints. The paired arms and checkpoints cannot estimate a training-seed population variance, and their repeated rows must not be pooled as independent confirmations. The recorded arithmetic adds an A/RECON fact over the existing output, not another experiment. [Card, §1][card]; [DM analysis, `independent_unit`][analysis].

The result supports neither stable superiority/equivalence nor family exhaustion, a policy-class or information limit, tuned headroom, natural prevalence, full-policy MARL/UAV return, variable K/N value, transfer, safety, or resource efficiency. The actor's action gate and its common sixteen-step consequence are the measured object, not a learned closed-loop multi-agent policy with co-adapting partners. Common endpoint actions do not prove residual inputs unnecessary throughout that larger system. [Card, §§1–2][card]; [P71 intake, §3][intake].

The old natural-support closure and A01's unresolved crash remain separate. Later successful work does not diagnose A01; an unrelated historical failure is not a universal prerequisite for future B. The current accepted primary measurements are not discounted because the cause of that historical event remains unknown. [Direction, final three sections][direction]; [evidence specification, §11.8.7][spec].

The direction decision is to retain the prior reversible selected-panel family PARK boundary with the concrete B08 yield recorded above. Select no successor, no recast, and no change to either MEI. This disposition is not a Portfolio lifecycle, priority, capacity, working-set, or scheduling judgment. Root retains allocation, integration, and execution-checkout management. No code, scientific-state file, old response, or experiment record is changed by this consultation.

## Evidence access and provenance

All thirteen listed repository paths were accessed through the connected GitHub connector at `eb25f0993ac6882e56e4c2115d82c6399f006498`. The references below pin that source version. Read scope follows the relevant sections, functions, and result fields; it is not a claim that every one of the 96 primary rows or every imported dependency was independently audited. No repository code, learner, evaluator, numerical validation, profile, or test was executed, and no local clone or outside literature substituted for the manifest.

| Source actually accessed | Material used |
| --- | --- |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §11, especially 11.4, 11.7–11.9; proportional question selection and interpretation. |
| [pro_packets/20260908_post_b08_convergence/READINESS.md][readiness] | Complete current question, recommendation, countercase, yield, and limits. |
| [pro_packets/20260908_post_b08_convergence/EXPOSURE.json][exposure] | Complete consultation exposure, historical counts/time, fixed-baseline bound, and unselected future work. |
| [CRTO_NATIVE_COST_B08_P71_INTAKE_20260908.md][intake] | Historical allocation and final §§1–5, including accepted science and complete time. |
| [CRTO_NATIVE_COST_B08_P71_RESULT_20260908.json][result] | Sampled native rows, RAW SHORT/LONG and residual LONG summaries, all three contrast summaries at both endpoints, and sampled signed losses. |
| [CRTO_NATIVE_COST_B08_P71_DM_ANALYSIS_20260908.json][analysis] | Both endpoint arm summaries, all paired native comparisons/loss details, common action/error identities, recorded-baseline arithmetic, resources and counts. |
| [CRTO_NATIVE_COST_B08_P71_RUNTIME_RECEIPTS_20260908.json][receipts] | Staging/submission, admission, complete accounting, collection checks, and terminal task log. |
| [CRTO_NATIVE_COST_B08_SCIENCE_CARD_20260908.md][card] | §§1–6 and the historical prospective status; unchanged scope, objective, reading and work. |
| [DIRECTION.md][direction] | Final three sections: prior family boundary, bounded P68 re-entry, and accepted B08 science. |
| [pro_packets/20260908_native_cost_reentry_convergence/archive/RESPONSE.md][prior] | Complete prior decision, including weak-RAW interpretation, comparator floor, limited re-entry and time correction. |
| [CRTO_NATIVE_COST_P68_CONVERGENCE_INTAKE_20260908.md][p68intake] | Complete-response acceptance, bounded authority, historical evidence, and retained transport mismatch. |
| [experiments/candidates/commitment_residual_triggered_options/native_cost_b08/experiment.py][code] | Expected-cost loss, training, contrast/reading/scoring, wall accounting, and their direct call context; read only. |
| [pro_packets/20260908_post_b08_convergence/ISSUE_SNAPSHOT.json][snapshot] | Pinned Issue 13 body and preserved prior delivery comment. |

The abbreviated direction-document paths in this table are under `docs/research/candidates/commitment_residual_triggered_options/`; the reference URLs give every exact repository path. The original result is reported as 411,368 bytes with SHA-256 `5fa2fcb91a643f1d377393994e38d390ae64ee3b39b270616ea788985e08fb61` in the accepted collection and analysis. That is the recorded integrity witness, not a new hash computation here. Its runtime source is `d9f643b761d57584de313b1f837d6c2c0becc931`; a later evidence commit is not a new execution. [P71 intake, §1][intake]; [receipts, collection verification][receipts].

The live [Issue 13 body][discussion] and its relevant comments were also read through the connector during this consultation, initially around September 9, 2026, 06:27 UTC. The read showed the post-B08 question and the preserved [P68 delivery comment][priorcomment]; that comment is not this round's delivery. Its contents agree with the preserved discussion in the pinned snapshot. These mutable discussion observations establish communication context, not scientific authority replacing the fixed evidence.

The prior complete GitHub response remains scientifically accepted while its one inexact provider Send remains historical transport evidence. This consultation neither calls that Send exact nor repeats, repairs, or erases it. Library and paper motivation is used only as recorded in the allowed prior decision/intake; no new library coverage, causal attribution, or novelty claim is made. There is no unresolved listed-source access gap preventing the direction decision above. [P68 intake, §§1–3][p68intake]; [snapshot][snapshot].

[spec]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[readiness]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/pro_packets/20260908_post_b08_convergence/READINESS.md
[exposure]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/pro_packets/20260908_post_b08_convergence/EXPOSURE.json
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_INTAKE_20260908.md
[result]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_RESULT_20260908.json
[analysis]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_DM_ANALYSIS_20260908.json
[receipts]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_P71_RUNTIME_RECEIPTS_20260908.json
[card]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_B08_SCIENCE_CARD_20260908.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/pro_packets/20260908_native_cost_reentry_convergence/archive/RESPONSE.md
[p68intake]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_P68_CONVERGENCE_INTAKE_20260908.md
[code]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/experiments/candidates/commitment_residual_triggered_options/native_cost_b08/experiment.py
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/eb25f0993ac6882e56e4c2115d82c6399f006498/docs/research/candidates/commitment_residual_triggered_options/pro_packets/20260908_post_b08_convergence/ISSUE_SNAPSHOT.json
[discussion]: https://github.com/CartmanFatass/My-paper-code/issues/13
[priorcomment]: https://github.com/CartmanFatass/My-paper-code/issues/13#issuecomment-5595668035
