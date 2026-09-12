# ACVC after C01 — proposed original-Convergence question

**Status: DM recommendation for the designated Portfolio author, not a selected object, card, Pro request or allocation.** Root's 2026-09-12 bounded assignment authorizes these materials only. C01's final intake is accepted on main `77c17d111`; its source, data, consumption and limitations are unchanged. No fit, evaluation, outcome analysis, Pro Send or cleanup is authorized by this note.

## The one proposed question and its use

> Having found qualified expected value for training the C proposer and then deploying the fixed F package in C01, should the next ACVC object be one bounded B comparison of **training through the same fixed F execution rule versus training C and adding F only at deployment**, with F used for both final evaluations? Or should ACVC retain F as a same-host reference asset without another standalone fit?

Recommend asking the original `em:acvc:convergence` node to choose this one learning-performance question. Its practical use is to decide whether F should remain a deployment correction or also enter the training loop, allowing the proposer and its teammates to adapt to the actual corrected motion and resulting local observations. Binding structure is **(d) multi-agent partial observability and other-agent non-stationarity during learning**. This is not a new learned gate, reopening of the ended T/G selective-retrace family, pure-retrace attribution, C promotion or formal UAV entry.

The native path would be: local retained-user loss and proposed away-motion → each UAV's own fixed F predicate → actual corrected command → joint geometry/service and private recurrent feedback → real PPO exposure to those consequences → final native team return. There is no roster change, option/duration choice, trajectory search or new global execution information.

The alternative is concrete: retain the consumed C01 result and its exact F rule as a qualified same-information reference where a receiving task actually matches the host, observation/action interface and budget. That selects no additional standalone ACVC training. It is not a local whole-direction PARK or Portfolio disposition. A receiving task must declare its own use and comparison; F is not installed into other directions by this recommendation.

## Existing evidence for and against this investment

The [accepted final intake](ACVC_FRESH_DENSE_PACKAGE_C01_INTAKE_20260911.md#final-scientific-intake-2026-09-12) reports all five complete fits: F-C +0.095915968685 J [0.074850455698,0.116981481673], F-dwell +0.065133768997 J [0.038286385582,0.091981152413]. Both frozen lower bounds exceed .01 J. C01 is consumed; inference remains provisional under the prespecified iid-normal complete-fit-panel model, whose actual neural-training calibration is unestablished. This supports investigating use of the already useful F package, not assuming training through F will improve it.

The strongest contrary facts are 46/320 adverse F-dwell worlds, minimum -0.113308313985 J, and useful dwell-C +0.030782199688 J. F and dwell intervened 37,100/25,949 times on unequal histories. Training through F may help adaptation, may merely teach proposals already overridden by F, or may reduce useful exploration; the existing result does not distinguish these outcomes. The attained **train-C → deploy-F** package is consequently the strong null. Comparing only against deploy-C would not answer whether the new training arrangement is worth using. Tuned same-information headroom remains absent. Current recasts:2 and lowest contention priority remain unchanged.

## Candidate B, only if selected and funded

One matched training pair comprises **two fresh fits with separate model, optimizer and mutable runtime state**: one uses the unchanged C training path; one executes fixed F throughout training. Both retain the existing native five-UAV/fifty-user H256 task, DENSE actor, centralized training-only critic, CPU FP32/thread1 and the same 512-episode/1,024-Adam learning budget. Evaluate each final checkpoint through its own F history on 64 paired initial worlds. Prespecify the pairing/RNG law before outcomes; no old C01 checkpoint or new seed identity is selected here.

The proposed primary is the paired-world mean final J difference, train-through-F minus train-C, **both deployed through F**. A .01 J MEI is suggested because the task/reward scale and practical decision remain the same; the node/card may set it prospectively. One training pair supplies a bounded exploratory observation, not independent training-population uncertainty. Above that margin would support considering a separately funded follow-up; inside it supplies no equivalence; an opposite sign favors keeping the deployment-only reference at this tested budget. All outcomes remain, with no second pair, extra panel, best-checkpoint choice or favorable replacement supplied by this proposal. Final rule and forecasts belong to any later selected card.

Dominant work, computed directly from the candidate's stated loop counts rather than from a new experiment:

| Quantity | Complete two-arm candidate |
|---|---:|
| Fresh fits / independent training pairs | 2 / 1 |
| Training episodes / final F evaluation episodes | 1,024 / 128 |
| Native team steps, H256 | 294,912 |
| Adam calls / replay actor rows | 2,048 / 5,242,880 |
| Training-collection actor rows / evaluation actor rows | 1,310,720 / 163,840 |
| F predicate agent-tick call opportunities | 819,200 |

The last row is `(512 training episodes on the treatment + 2×64 evaluation episodes) ×256×5`; it is an invocation opportunity count, not predicted triggers or measured cost. There are no nested candidate controllers, alternate trajectories or exhaustive state/cue censuses. No C/dwell evaluation panel or causal audit is added. Necessary source/semantic review and focused checks are support work, separately charged from this intrinsic learner/control work.

## Concrete engineering fact and inferential assumption

Current `scripts/run_acvc_fresh_dense_reuse_b01.py:241` trains through UCOPE `collect_episode`; F is currently applied only by the separate ACVC evaluation collector. The UCOPE path stores the sampled pre-tanh proposal `u`, its old density and the actual input/history used by recurrent replay. It has no F-training hook. The ACVC collector's existing training storage is for the learned gate; changing `phase` to `train` with `gate=None` is not an implemented F actor-training path (the gate branch owns `h0`, and no actor proposal density is supplied there). The candidate is therefore **not launch-ready**.

A bounded implementation would have to retain the sampled proposal and its density for PPO while recording **actual F-sent commands** in subsequent observation/hold/history feedback. It must not substitute the many-to-one overridden displacement for the Gaussian sample when computing old/new likelihood ratios. This is the concrete acceptance risk: rollout state → stored proposal/old density → recurrent replay/loss → final checkpoint → F evaluation. Shared UCOPE defaults and all other callers must remain intact. Implementation ownership and independent high-risk review are required if this path is selected; no code is added now and no generic guard, scheduler or new learner framework is requested.

Scientific-reading use: FOUNDATIONS §6 and the empirical note support one training pair as the inferential unit and the package claim ceiling; the RL note's data/update and policy-gradient passages distinguish behavior data from the evaluated action likelihood. The primary PPO paper, *Proximal Policy Optimization Algorithms*, arXiv:1707.06347v2, §§2–3, equations (6)–(7), defines the ratio using the same sampled action under new and old policies. [Primary PDF](https://arxiv.org/pdf/1707.06347). **DM inference:** treating the sampled proposal as the policy action, with the fixed history-dependent F mapping as part of the execution dynamics, is the intended formulation. The paper does not establish improvement, convergence or safety for this ACVC mapping; the rollout/feedback implementation still has to satisfy that formulation. This source check adds a precise semantic risk, not a proof or mechanism-diagnosis prerequisite.

Question-driven local coverage was checked first on Windows: `C:/Projects/My-lib/README.md`, `collections/README.md` and the existing read-only indexes (no available default page rows; the inspected mechanism example was not verified real-paper evidence), then all 190 entries of `C:/Projects/Inst-sci/papers/MyLib/llm-index/catalog.v2.jsonl` for action replacement/shield/masking/policy-gradient candidates. MARL-0180's offline-MARL title/abstract is a different setting and was not used as support for this on-policy proposal. No local source passage was claimed from an index match. The exact likelihood-source gap was filled only by the original PPO paper. This is bounded coverage, not a novelty or absence-of-related-work verdict; no index was built, download pipeline installed or library purpose presumed.

## Requested investment and present boundary

The necessary next scientific authority is **one new original-Convergence question plus its complete DM intake**. No Innovator round is requested for this B candidate. C01's two consultations and five-fit allocation are ended; there is no saved balance to reuse. The present writing task has zero scientific exposure and sends no Pro.

If Portfolio chooses to fund a conditional complete path, the DM proposes an **application ceiling**, subject to the proper decisions: native ≤270 s per complete arm, ≤540 s native sum; all invoked support ≤660 s; complete logical chain ≤1,200 s. Support includes that consultation's preparation/archive/intake, minimal source and focused checks/review, exact source transfer, Monitor, collection/reduction/publication/integration and scoped cleanup. Provider/client/deliberation and any uncovered time must remain separately explicit, never zero by assumption. These are proposed investment bounds, not an admitted forecast, new authority or a claim of sufficient measured support coverage.

The unchanged C01 complete units cost 170–178 s inclusively; the old 222.5 s planning projection included one fit plus three evaluation panels. Neither is a complete cost projection for putting F into 512 training episodes. Controller work and the changed training path have unknown cost; do not scale wall time just by episode counts. Any selected runner's complete per-arm cost law must include that work and required publication before admission. Cost refusal returns the question to the asset-retention alternative; it does not commission a mandatory cost experiment or move the same prerequisite into an A.

Portfolio may instead fund only the bounded consultation, leaving all future numerical work explicitly unfunded, or retain the completed reference without a new question. The designated Portfolio DM authors that investment comparison and its owner item; this ACVC note supplies an independent option, not a local Portfolio decision. The original Convergence node chooses the next scientific object. No broader family enumeration, causal reconstruction, additional fit or cross-direction wait is needed to consider this option.

The exact C01 retention inventory and current DM's cleanup responsibility remain in `ACVC_FRESH_DENSE_PACKAGE_C01_EXECUTION_FACTS_20260911.json.finalization_20260912`. No unique checkpoint/evidence is removed or rehashed by this authoring assignment.
