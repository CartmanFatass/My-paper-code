**Continue the existing first-application-valid RETAIN/COPY/SHADOW exploratory family through one bounded A/RECON ordinary-renewal interface correction and native acceptance observation. Do not retrain, scale B02, change its forecast objective, or reopen its result rule.** The new evidence identifies a concrete action-delivery discrepancy: on the two measured windows, fresh commands were emitted when native would not incorporate them, while native admission received the copied held command. Correcting that boundary and observing actual incorporation can change the next learning decision without requiring a source effect, a historical training census, or a complete explanation of B02.

This is **CONTINUE, not RECAST**, at the ordinary action-interface branch of the existing family. It selects one prospective correction object, not accepted code, an experiment launch, or a Portfolio change. The corrected-window observation must finish before another learner is purchased on this path. Its subsequent ordinary intake may qualify only interpretations that depend on the demonstrated mismatch; it may not replace historical results. The previous complete response explicitly reserved precisely this later correction after its disagreement branch. [Previous response §§3–5][previous]; [A01 result intake §§2–4][a01-intake].

## 1. What the completed observation establishes

Here, A01 means **DISH-RENEWAL-BOUNDARY-A01**, not the earlier retained-prefix diagnostic with the same short suffix. It used the original FORECAST_PACKAGE seed-61 update-16 checkpoint, two fresh recurrent states and two initial 32-tick windows of the unchanged B02 ordinary evaluator. Both windows remained live. The complete machine summary and accepted intake report:

| Initial window | Native admission, policy renewal false | Policy renewal, native admission false | Both true | Both false | Held-command changes |
| --- | ---: | ---: | ---: | ---: | ---: |
| K8, phase 4 | 4 | 4 | 0 | 24 | 0 |
| K4_TO_K12, initial K4, phase 2 | 8 | 8 | 0 | 16 | 0 |
| Total | 12 | 12 | 0 | 40 | 0 |

The native admissions occurred at K8 ticks 4, 12, 20, 28 and initial-K4 ticks 2, 6, …, 30. On those ticks, the policy consumed false renewal and emitted the held zero vector. On the following ticks it consumed true renewal and emitted fresh nonzero motion, but native did not incorporate it. The inspected raw example at K8 tick 5 is `[-1.1745903491973877, 1.3738329410552979, 0.7294883131980896, -1.0287286043167114]`, with native pre-countdown 7 and an unchanged zero held vector. The initial-K4 tick-2/tick-3 pair independently exhibits the same ordering within that second window. These are command-incorporation observations, not merely unequal flags. [Formal summary, counts and windows][a01-summary]; [raw rows, window 1 ticks 4–5 and window 2 ticks 2–3][a01-rows]; [intake §1][a01-intake].

The retained parameter norm was 39.149200792042365 before and after each window, with no optimizer or parameter-update activity. There were zero new training instances and 64 ordinary native ticks, plus the separately recorded four-tick check. One distinct checkpoint artifact was reused; that must not be confused with the number of policy constructions. The measurement source constructs a checkpoint-loaded policy for each window. Its two windows are not independent training seeds. [Formal summary][a01-summary]; [exposure record][exposure]; [measurement source, run_measurement][measurement].

The reset flags were correct at the two observed nonzero phases. Neither a phase-zero reset nor a later K4-to-K12 switch was observed. No legal transfer occurred. The reported 60 service ticks and energy context do not measure the service that would have resulted from incorporating the fresh commands. The DM's disagreement prediction was supported; its card's suggestion that a previous fresh command would later become held must not replace the actual finding that the held vector never changed. [A01 card §§5–6][a01-card]; [intake §§1–3][a01-intake].

**The strongest support for correction** is this contemporaneous link between the consumed flag, native countdown, emitted vector and held-vector consequence. **The strongest contradiction to a performance interpretation** is that the retained learner may have learned poor commands: none of the measured fresh motion was applied, so no native benefit from applying it was observed. Correct delivery can reduce service, increase energy, or expose other failures. The correction is warranted as an interface intervention, not because those outcomes are expected to be favorable.

## 2. The exact contract selected for correction

### Current decision permission is distinct from completed-transition history

For an ordinary live decision at primitive tick n, define the policy's operational renewal permission as:

`renew_now(n) = [the corresponding current native countdown is zero]`.

It must refer to the same lane and pre-action state that the next ordinary native step will consume. The raw native output flag retains its present meaning: whether renewal applied in the transition just completed. These are different temporal quantities. Do not change the native ABI or rewrite the native transition to make the old output appear current. The source shows that native advances countdown after command processing and returns the earlier Boolean; both `_decode_step_outputs` and ordinary `NativeBatch.step` presently pass that Boolean through. [Native complete_prepared_tick and step_one][native]; [wrapper _decode_step_outputs, observe and step][backend].

Select a **Python ordinary-decision boundary correction**, deriving the operational flag from the matching current countdown, without advancing the environment. It must cover initial ordinary observation, subsequent ordinary-step observations and selected-lane resets. A fresh phase-zero reset must expose current renewal, not inherit the blanket false transition-output initialization. Repeated reads must not advance state or acquire another observation. Handle each lane's own current state rather than broadcasting one lane's flag.

The current countdown is already represented in causal actor feature 42. Thus using that same clock value to set the existing scheduling permission does not grant target truth, another agent's private history, future noise or SOURCE payload contents. The independent acceptance reference remains the actual native pre-step countdown, not the corrected flag compared with itself. [Native actor_row][native]; [wrapper observe and reset_selected][backend].

**Do not relabel the generic decoder indiscriminately.** It also serves prepared and cloned outputs whose boundary meanings differ. Limit the changed meaning to ordinary decision observations; preserve raw completed-transition data and do not silently alter the older prepared first-application path, source-clone semantics or unrelated consumers. The implementation must make this distinction explicit in its small existing Python boundary, not introduce a registry, compatibility framework or new native export. [Wrapper prepared/ordinary methods][backend].

### What preservation means

Preserve the native service reward definition, its primitive-tick indexing, terminal handling, energy accounting, dynamics, host geometry, clock recurrence, action projection, ownership law, certificates, source/readiness prerequisites and passive-label algorithm. Preserve the checkpoint, its forecast-package flag, model parameters, actor/critic/snapshot representations, normalization rules and ordinary recurrent-forward order. There is no additional sensing, physics call, policy forward, action search or A03-style prepare/complete substitution before a decision.

Only the ordinary top-level scheduling permission and its consistent consumption change. Do not shift rewards or actions between stored time indices, retrospectively remask old fragments, change discounting, or use a different observation normalization to obtain a convenient result. Raw actor/critic fields remain as currently supplied in this bounded correction; it is not a general reconstruction of every observation's temporal semantics.

Preservation is **preservation of these laws and information access**, not equality of realized trajectories. Moving fresh motion and proposal sampling to their intended clock can change commands, message contents, future observations, label eligibility and return. Existing addressed RNG laws remain; a later stochastic run can consume draws at different decision ticks because the corrected decision permission is different. That is an explicit behavior change, not a bit-identical optimization or a silent repair of B02. [B02 card §§2–4][b02-card]; [recurrent policy and collection][recurrent]; [evidence specification §§4, 11.8.5–7][method].

### Prepare/commit: policy gating is inside; native legality is unchanged

The shared top-level renewal flag gates fresh motion **and the policy's prepare/commit sampling**. All those policy-side consumers are inside this correction. Correcting only motion while leaving proposal sampling, behavior-log-probability eligibility or stored renewal masks on the old clock would leave two incompatible action contracts. The same corrected pre-action permission must be the one seen by the ordinary policy, its behavior-log-probability calculation and, when the collector is later used, its `renew`, `prepare_mask` and `commit_mask` fragment fields. The loss formula and update algorithm are not changed. [Recurrent step_rows, collect_update and _fragments][recurrent].

The native gates are not identical to one another. Native preparation can latch when the degradation predicate and prepare proposal hold; that statement is **not** guarded by native renewal. Native intent emission additionally requires renewal, version readiness, the preparation latch and a commit proposal. The later CAS has its own application conditions. Therefore zero CAS in A01 does not demonstrate that preparation was rejected in the same way as motion, or that fixing policy renewal will make a commit legal. Record actual proposal timing and resulting events, but do not force any proposal, readiness, certificate, intent or ownership transfer. No threshold is lowered. [Native complete_prepared_tick, preparation latch and intent/application branches][native].

This rejects the overly broad reading that the correction leaves all control behavior unchanged. It leaves native rules and learned parameters unchanged while deliberately changing when their policy inputs are produced.

## 3. One bounded native acceptance observation

### Inputs, comparison and scope

Use the original seed-61 FORECAST_PACKAGE update-16 checkpoint identified by SHA256 `504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`, its original normalization, the original B02 master and the accepted A03 host. Run two sequential width-one instances with fresh zero recurrent states: TARGET_VISUAL_MASK/K8 and TARGET_VISUAL_MASK/K4_TO_K12, each at speed 4, slot 0, block 0, for at most its original first 32 ordinary ticks. Keep deterministic sampling and the existing FP32-policy/float64-native, single-thread configuration. The historical input identity was accepted; current availability must be checked through existing input handling, not replaced by training a new checkpoint or building a provenance service. [A01 card §2][a01-card]; [intake §1][a01-intake].

There is one retained-controller configuration and one prospective interface correction, not a new two-arm learning trial. The original A01 rows remain the unmodified reference; **do not rerun an unmodified arm merely to reproduce its known discrepancy**. The decisive comparator for each corrected tick is native's actual current admission condition and its unchanged command-projection law. This is the strongest direct reference for the selected interface claim; a tuned performance baseline is irrelevant to whether that contract is met.

Reuse the bounded measurement approach, but publish new correction-specific results rather than reporting the old A01 as having passed. In particular, the current recorder obtains `returned_renew` from the wrapper's returned observation. After correction that can denote the next decision permission, not the raw C++ completed-transition flag. Keep those meanings separately identified, using existing raw output access when needed; never compare one relabelled quantity against itself or silently change what an archived field meant. [Measurement make_row and run_window][measurement]; [wrapper output storage and decoding][backend].

### Acceptance requires actual command handling, not just agreement of Booleans

For every live observed tick, retain the actual policy-consumed flag, current pre-step countdown/tick, emitted raw vector, held vector before/after completion, proposal outputs, and native service/energy/event/terminal facts. Distinguish current decision permission from the raw completed-transition flag.

The intended local result is zero same-tick permission disagreements, together with:

- At native admission, the actually held vector equals the result of native's unchanged projection of **that tick's emitted command** from the previous held vector.
- Away from admission, the held vector remains unchanged under the ordinary native hold law.

The projection limits raw magnitude to 3, command change to 1.5, and the resulting magnitude to 3 for each vehicle. Consequently, acceptance must compare against the projected vector, not require raw-command equality. Use the independent reporting computation or an equivalent independent check at the appropriate float64 scale; do not copy native's answer into its own reference. [Native project and motion-update branch][native]; [measurement project_command][measurement].

If both full windows remain live and their clocks are unchanged, the prospective expected counts are 4 matched renewals plus 28 matched non-renewals for K8 and 8 plus 24 for initial K4: **12 matched renewals, 52 matched non-renewals, zero disagreements** overall. Those are expectations for the new observation, not already measured results. Early termination must not be suppressed to obtain them.

There is no requirement that a competent command differ from the previous held vector on every admission. Legitimate equal choices remain. Conversely, if the chosen policy supplies no value-distinguishing command, report flag alignment and the observed hold behavior without claiming demonstrated recovery of a nonzero command. Do not force a command, choose another checkpoint, lengthen the windows or introduce an epsilon-separation admission rule. At a value-distinguishing admission, the command record must show its corresponding projected incorporation.

The earlier four-tick check stops before the first K8 admission and cannot by itself accept the correction. Use **one consolidated focused regression invocation** covering the changed clock boundary and its measurement, including the two initial periods, phase-zero/reset handling and consistent pre-action flag propagation. Retain the existing B02 focused coverage and expectations for the unchanged loss/interface/host components; do not repeat a second smoke merely because the corrected windows are launched. Small fixed synthetic boundary/mask fixtures are engineering checks, not fresh learning or evidence about historical collector activity. There is no all-phase, all-schedule or historical-fragment census. [A01 intake §1][a01-intake]; [B02 CM verification record][b02-cm]; [scope §§3–5][scope].

### Reading and stopping

| New observation | Bounded reading and consequence |
| --- | --- |
| Current permission agrees with actual native admission, and value-distinguishing commands are incorporated through the unchanged projection | Accept local ordinary-renewal/command-delivery correction on the observed windows. Complete the correction intake; no return gain, calibration, general protocol competence or source value follows. A later learning comparison must be separately selected. |
| Permission aligns, but commands happen to equal held commands | Report the verified clock relation and limited value-discrimination support. Do not call this lost-service recovery, force a witness, or automatically expand the object. |
| A disagreement remains, incorporation differs from the applicable native law, or a protected semantic changes | Do not accept the dependent correction claim. Preserve the exact boundary and return the concrete defect/scope gap. No automatic retraining or open-ended repair programme follows. |
| Corrected behavior causes an early terminal, adverse energy/event outcome, or otherwise truncates a window | Preserve the adverse behavior and the live boundaries actually observed. Distinguish a correct interface with poor behavior from an incorrect interface. Do not manufacture the planned counts or claim full-window coverage. |
| Input unavailable, required measurement missing, or the complete spending bound is exhausted | Report the precise missing input/observation or cost gap, retaining independently trustworthy narrower facts. No checkpoint replacement, added run, hidden extension or scientific negative is implied. |

Neither positive service nor legal transfer is an acceptance condition. The original 60/64 service observation is context, not a target to equal or exceed. A01's one-discrepancy resolution, B02's +24-tick performance MEI and B01's source-effect scale are not interchangeable.

## 4. Training-side evidence and the later reinterpretation intake

**No additional result-bearing training-collection measurement is required before a narrowly worded reinterpretation intake.** The current source read is sufficient to identify a concrete dependency and to state its limits. It is not sufficient to turn the historical training-side inference into an observed fact.

The listed wrapper demonstrably passes through the completed-transition flag. The listed ordinary collector stores that same pre-action observation flag and uses it for the policy, behavior probability and fragment masks. B02's study calls this collector and its ordinary evaluator directly. The accepted A01 observes the evaluation-side consequence on two windows. Together these justify qualifying the claim that B02 assessed a controller whose fresh motion was delivered on the intended decision tick. They do **not** measure all past training lanes, all old B01 consumers, later switches, every proposal gate, or the counterfactual return with correct delivery. [Wrapper ordinary methods][backend]; [recurrent collection and masks][recurrent]; [B02 study run_arm and evaluate_episode][study].

For the new correction, source review and the focused boundary/fragment fixture must establish that the corrected pre-action flag is not discarded before a later collector would store it. This is prospective implementation conformance, not a historical gradient or learning measurement. Running the existing complete collector merely to strengthen the old causal story would buy 32×128 ordinary transitions per update collection plus passive-label work; the full update then adds optimizer computation. That is not the selected zero-training acceptance observation, and it is not required by the interpretation below. [Recurrent collect_update][recurrent]; [B02 card §§3, 6][b02-card].

The later intake may append the following qualifications, with observation and source inference separated:

**B02:** retain the four paired returns 572/447/433/428 in each arm, mean difference zero, energy/event observations, completed training counts, parameter movement and original inside-MEI reading. State that these are outcomes of the executed ordinary interface; the new local finding prevents using them as evidence that the package has no benefit when fresh motion is delivered at the intended tick. Mark the analogous training-side exposure concern as source-supported inference. Do not declare the native sums fabricated, erase the real learning, retroactively change the primary, or call the null explained by timing alone. [B02 intake, Reading rule and Real learning sections][b02-intake].

**B01:** retain its recorded insufficient-trigger-support result and unestimated source contrasts. Do not infer universal command non-incorporation across its historical training or its different first-application evaluation path from the two B02 windows. Any dependency statement about B01 must name the actually established shared path and remain an inference where no corresponding measurement exists. The earlier A03 prepared-path observations and A04/A05 findings are not invalidated by this ordinary-wrapper diagnosis. [Direction record, B01/A03–A05 sections][direction]; [previous response §§1–2][previous].

No blanket quarantine or retroactive promotion is selected. A future claim that every historical training command was discarded, that all gradients were invalid, or that timing caused B02's entire zero difference would require additional evidence appropriate to that claim. **Do not buy that stronger claim as a prerequisite to ordinary future B exploration.** A later B on corrected delivery would be a newly named, outcome-informed study, not a repaired readout or fresh independent replication of the old interface. [Method §§11.8.5–7, 11.9][method].

## 5. Complete work, cost and burden

The selected result-bearing workload is **one corrected-interface configuration, one distinct retained checkpoint, two policy/recurrent instances and resets, and at most 64 ordinary native steps and 64 recurrent forwards**. It contains no new independent training seed, training update, optimizer step, passive-label request, source fork or trajectory/policy search. Existing unit/regression verification is separate work within the same purchase, not an additional scientific sample. If the retained B02 focused checks construct synthetic models, use backward, or exercise a passive-label path, preserve and count that verification work rather than claiming that the entire engineering invocation has zero such calls. No full learner update is authorized to stand in for a boundary check. [Measurement source][measurement]; [B02 CM focused-profile description][b02-cm].

**Select a new 120-second complete compute spending limit for this correction object.** It includes imports, any dedicated native build/load, the single consolidated focused regression invocation, checkpoint handling, both corrected windows, reduction and publication. Shared work is charged once. This is a new finite allocation, not carried-over A01 balance, the A05 exception or B02's unused allowance. Source/runner and existing test budgets remain; the total selected compute limit does not grow when work is split into scripts.

The work law is:

`build/import/load + one focused regression invocation + checkpoint handling + 2 × (policy construction + reset) + up to 64 × (ordinary forward + native step) + reduction/publication`.

The existing A01 formal runner reported approximately 0.090 seconds and its check approximately 0.065 seconds after the native library had already been built. Those are the reported runner scopes, not established cold full-process or corrected-code costs. The CM record also reports a distinct approximately 5.16-second local check and a composite planning calculation based partly on B02 wall. Neither that calculation nor the documentary “about 2 seconds” cold-build description establishes a measured matching cost law for this correction. Preserve them as scoped historical observations/estimates; do not promote a whole-arm-time attribution or a mixed test/build time into a measured unit or compiler upper bound. [A01 intake §1][a01-intake]; [CM cost section][a01-cm]; [documentary cost record][exposure].

B02's 642.66-second external pair wall and 669.61 aggregate CPU-seconds cover a different workload: two sixteen-update learners, evaluations and shared preparation. They are not a speedup baseline for 64 corrected ticks. There is no established new corrected-learner cost, and no claim that all future corrections fit 120 seconds. If concrete implementation facts cannot support this finite purchase, return the gap rather than invent linear scaling, remove decisive measurement or add a calibration experiment. [B02 intake, Whole work and cost][b02-intake]; [runtime General requirements §§1–8][runtime].

| Retained or omitted burden | Decision served |
| --- | --- |
| Real retained-policy forward and ordinary native step | Required to observe actual incorporation rather than merely repair a displayed Boolean. |
| Compact same-tick clock, raw/projected/held command and consequence records | Required for the selected action-delivery claim and to preserve value-equal, adverse and terminal cases. No full hidden-state dump is needed. |
| Focused clock/consumer regression and retained B02 conformance coverage | Required to keep the chosen boundary consistent without changing forecast, reward, host or learner semantics; not a statistical replicate. |
| Whole-invocation wall and scoped peak RSS | Required honest spending/resource account. Optional missing coverage limits resource claims, not independently trustworthy boundary facts. No new telemetry service is selected. |
| Full PPO collection/replay, optimizer updates and label-clone trajectories | Not run as scientific work in this A. They remain intrinsic to any future B retaining the old objective and cannot be silently deleted to claim acceleration. |
| Historical training reconstruction, calibration, exact upper/headroom, source forks, support census and all-schedule equality | Deferred or omitted because this local correction claims none of them. Their absence is not a new launch gate. |

Use the existing remote-first route, exact committed/pushed source, detached supervision and a fresh physical/effective memory admission of at least 4 GiB immediately before each actual invocation. Keep single-thread numerical settings and existing batch interfaces. No worker team, scheduler, guard, registry, new approval tier or framework migration is selected. The ordinary 2,000-line source and 600-line runner limits remain; the orchestration ratio is a review signal. Existing reviewers should inspect this one logical correction and its consumers, not expand it into a system rewrite. Grok's historical implementation role changes neither the scientific authority nor the meaning of the rows. [Scope §§3–5][scope]; [runtime §§4, 7–8][runtime]; [AGENTS §§2, 5, 7–8 and Appendix C][agents].

## 6. Why this decision rather than the alternatives

**Interpretation alone** can already attach the bounded caveat above, but leaves the measured action-delivery problem in place. It is not a substitute for the selected next observation.

**Correction plus a new B now** would mix unaccepted interface behavior with a new learning purchase. The prior decision reserved correction tested through native behavior first, and this small directly relevant acceptance can satisfy that boundary without another synthetic forecast diagnosis or a universal diagnosis-first policy. No particular new loss, seed count or larger exposure is selected here. [Previous response §§3–5][previous].

**More unchanged-package seeds or objective tuning** could measure variation behind the same mismatch, but would not answer whether current commands reach native at the declared clock. The large finite package loss and pre-clipping gradient peaks—7,423,381.7265625 and 22,054,892.236206055—remain genuine contrary optimization evidence, not a reason to ignore the demonstrated interface problem or an established explanation of it. [B02 intake, Real learning section][b02-intake].

**PARK or CLOSE** would be broader than needed while this concrete bounded correction can inform the next choice. This is not continuation merely because the source hypothesis is untested: there is a specific observed interference with the ordinary action path and a finite native check of its removal.

Residual uncertainty remains substantial. The applied commands may be poor; preparation/certification and later schedule/owner boundaries may remain limiting; finite exposure, objective scale and checkpoint/partner co-adaptation may matter. COPY or RETAIN may suffice even after a legal opportunity is reached, and replay/replan may contain shadow preparation. Correcting timing supplies none of those source comparisons. The broader question remains prepared SHADOW versus incumbent COPY at the same legal first application, with shell-matched RETAIN separating owner/actuator remap value. R02 stays closed, and FOLR, RCLE and VSP-02 remain separate. No lifecycle, priority, capacity, registration or fusion action follows. [Direction record][direction]; [previous response §5][previous].

## 7. Evidence access and limitations of this consultation

Repository evidence was read through the connected GitHub connector at **04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111**. The fixed task was read at its separately supplied immutable commit. Every listed evidence path was accessible; no unlisted scientific file, moving branch, web mirror or local clone was used. Source/function observations are scoped reads, not a full repository audit. Aggregate A01 findings above come from the complete machine summary and accepted intake, with raw boundary examples inspected directly; I did not claim a new independent programmatic recount of all 64 rows.

For this table, C/ means `docs/research/candidates/degraded_incumbent_shadow_handover/`, R/ means `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`, S/ means `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/`, and P/ means C/`pro_packets/20260906_post_a01_convergence/`. Linked sources are pinned to the evidence commit.

| Actual path read | Scope |
| --- | --- |
| [C/DISH_RENEWAL_BOUNDARY_A01_RESULT_INTAKE_20260905.md][a01-intake] | Complete intake. |
| [C/a01_renewal_boundary_20260905/formal/rows.json][a01-rows] | Initial K8 records including ticks 4–5, and initial-K4 records including ticks 2–3; the requested longer first-window chunk was truncated. Not represented as a full row-by-row census. |
| [C/a01_renewal_boundary_20260905/formal/summary.json][a01-summary] | Complete machine summary through overlapping reads. |
| [C/DISH_RENEWAL_BOUNDARY_A01_SCIENCE_CARD_20260905.md][a01-card] | Complete card. |
| [C/DISH_RENEWAL_BOUNDARY_A01_CM_RECORD_20260905.md][a01-cm] | Complete record. |
| [P/EVIDENCE_AND_OPTIONS.md][options] | Complete proposal, treated as advice. |
| [P/EXPOSURE_AND_COST.json][exposure] | Complete documentary derivation; not a new experiment or measured future forecast. |
| [C/pro_packets/20260905_post_b02_convergence/archive/RESPONSE.md][previous] | Complete previous response, including overlapping recovery of the cost section and reference tail. |
| [C/DISH_POST_B02_CONVERGENCE_INTAKE_20260905.md][previous-intake] | Complete intake. |
| [C/DISH_FORECAST_PACKAGE_B02_INTAKE_20260905.md][b02-intake] | Complete intake, including all reported row outcomes and finite gradient extremes. |
| [C/DISH_FORECAST_PACKAGE_B02_SCIENCE_CARD_20260905.md][b02-card] | Complete card. |
| [C/DISH_FORECAST_PACKAGE_B02_CM_RECORD_20260905.md][b02-cm] | Contract, dependency map, accepted verification and original command records; long command output was truncated at its end. |
| [C/DIRECTION.md][direction] | R02 closure/re-entry and B01/prefix provenance, lines 217–305; A03–A05 and B02 sections, line 350 onward. |
| [S/renewal_boundary_a01.py][measurement] | Complete measurement module. |
| [R/production_backend.py][backend] | Decoder, ordinary observation/reset/step, prepared/clone boundaries and passive interface, scoped windows around lines 265–335 and 520–860. |
| [R/production_recurrent_trainer.py][recurrent] | Ordinary action/proposal mapping, behavior probability, collection, fragment masks and variant propagation, lines 285 onward; final returned tail truncated. |
| [R/native/rbhr_r06_production_backend.cpp][native] | Projection, causal clock features, observation materialization/certificates, ordinary completion and step ordering, lines 255–359 and 430 onward. |
| [S/study.py][study] | Measurement wrapper, ordinary evaluation, complete training loop and exposure law, lines 1–250. |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][method] | Classes/common integrity/A/B, lines 45–130; controlling §§11.4, 11.8–11.9 through the end. |
| [docs/project/ENGINEERING_SCOPE_SPEC.md][scope] | Ordinary scope, machinery and budgets, §§1–5. |
| [docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md][runtime] | Complete General requirements §§1–8. Incidental separate VNFC appendix text was not applied. |
| [AGENTS.md][agents] | Collaboration/decision/integrity sections and Appendices A–C through overlapping reads. No expanded write authority inferred. |
| [docs/project/GITHUB_RESEARCH_COLLABORATION.md][delivery] | Complete delivery document. |
| [P/ISSUE_SNAPSHOT.json][snapshot] | Complete fixed snapshot, including the prior-round comment. |

The [Issue 4][issue] body and all-comments endpoint were accessible. The discussion readback was completed by **2026-09-06 10:46:40 UTC / 03:46:40 PDT**. It showed one [previous-round delivery comment][prior-comment], not a delivery for this new correction decision; its linked prior response was read through the explicitly listed archive. The issue's reported last update was 2026-09-06T05:06:00Z. Mutable discussion was not substituted for pinned scientific evidence, and its unlisted links were not followed.

There is no evidence/access blocker to this bounded decision. Current remote checkpoint availability and the new correction's full implementation cost remain unverified at their stated scopes. This consultation performed zero model constructions, native states/steps, backwards, optimizer steps, tests or experiments. Only the separately authorized response-file and Issue-comment delivery is performed.

[a01-intake]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A01_RESULT_INTAKE_20260905.md
[a01-rows]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/a01_renewal_boundary_20260905/formal/rows.json
[a01-summary]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/a01_renewal_boundary_20260905/formal/summary.json
[a01-card]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A01_SCIENCE_CARD_20260905.md
[a01-cm]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_RENEWAL_BOUNDARY_A01_CM_RECORD_20260905.md
[options]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a01_convergence/EVIDENCE_AND_OPTIONS.md
[exposure]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a01_convergence/EXPOSURE_AND_COST.json
[previous]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260905_post_b02_convergence/archive/RESPONSE.md
[previous-intake]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_POST_B02_CONVERGENCE_INTAKE_20260905.md
[b02-intake]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B02_INTAKE_20260905.md
[b02-card]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B02_SCIENCE_CARD_20260905.md
[b02-cm]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DISH_FORECAST_PACKAGE_B02_CM_RECORD_20260905.md
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/DIRECTION.md
[measurement]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/renewal_boundary_a01.py
[backend]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py
[recurrent]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_recurrent_trainer.py
[native]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/native/rbhr_r06_production_backend.cpp
[study]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/study.py
[method]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[scope]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/project/ENGINEERING_SCOPE_SPEC.md
[runtime]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/project/MARL_RUNTIME_ENGINEERING_SPEC.md
[agents]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/AGENTS.md
[delivery]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/project/GITHUB_RESEARCH_COLLABORATION.md
[snapshot]: https://github.com/CartmanFatass/My-paper-code/blob/04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111/docs/research/candidates/degraded_incumbent_shadow_handover/pro_packets/20260906_post_a01_convergence/ISSUE_SNAPSHOT.json
[issue]: https://github.com/CartmanFatass/My-paper-code/issues/4
[prior-comment]: https://github.com/CartmanFatass/My-paper-code/issues/4#issuecomment-5557093321
