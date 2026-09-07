# DISH B06 bounded CM implementation handoff — 2026-09-06

Prepared under Root's post-VSP-C1 refill instruction and integrated as
`fde638f9c85d86fc01fe003254397b18dfdeacc6`. Root subsequently explicitly authorized dispatch;
DM reactivated the existing CM `/root/dm_amx_dish_seed101/cm_am_dish_seed101` on 2026-09-06
at 23:44 PDT, and the native child is running. **CM is assigned implementation/checks and a
pushed technical return only. A result-bearing B06 launch remains a separate explicit
assignment.** The earlier preparation task completed without dispatch, implementation or
experimental exposure; the current dispatch supersedes that historical preparation status.

Frozen contract: [B06 card](DISH_SAMPLED_EXECUTION_B06_SCIENCE_CARD_20260906.md) §§2–7,
integrated in `0eae162f2` from DM commit `43e2f0ad9f05b51c35ca58664164e35c28566f6e`.
The [post-B05 intake](DISH_POST_B05_CONVERGENCE_INTAKE_20260906.md) §3 supplies the two concrete
implementation dependencies. Current instruction baseline is `f85c8d448`; applicable AGENTS
and the current engineering/evidence specifications control ordinary implementation choices.

1. **Deliverable and goal.** Implement one runnable seed113 LOW_LR B/EXPLORE comparison of
   sampled versus modal execution from the same final checkpoint, with trustworthy primary
   and native companion outputs. Deliver committed/pushed source, focused acceptance evidence,
   independent review and a concise CM record beside the card. No new science contract, mechanism
   diagnosis, training run or performance claim is part of this implementation-only return.

2. **Owned paths and entry points.** New
   `experiments/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06/study.py`,
   `scripts/run_dish_sampled_execution_b06.py` and focused tests under
   `tests/experiments/candidates/degraded_incumbent_shadow_handover/sampled_execution_b06/`.
   Reuse the existing DISH `control_low_lr_b04/study.py`
   (`master/configuration/prepare_shared/run_arm`) and `forecast_package_b02/study.py`
   (`evaluate_episode/terminal_facts`); minimal shared edits needed for explicit master plumbing
   or evaluator reuse are in scope, with B04/B05 defaults preserved. Under
   `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`, reference
   `production_recurrent_trainer.py` sampler/step_rows, `production_backend.py::rng_words_native`
   and `production_population.py::EvaluationCoordinate.canonical_key`; their existing training
   laws/native API remain unchanged. Runtime/check artifacts use the card §7 temp surface.
   CM works in its own branch/worktree, is not alone in the repository, and preserves unrelated
   edits. Implement directly by default; do not create a mandatory implementer chain.

3. **Preserved semantics.** Card §§2–4 bind native float64/policy FP32, one CPU thread,
   seed113 LOW_LR at 3e-5 in both original groups, raw service-Q input and all inherited learner,
   label, renewal, information, normalization and native rules. Keep 16 updates, the four
   conditions, four own-initial modal rows, and one final modal plus two fixed sampled episodes
   per condition. Preserve every native companion, full-horizon terminal handling, first-transfer
   post-step tick/null and the complete-primary reduction. Implement the actual new training/
   environment master consumers and the separate width1 evaluation policy stream exactly as
   card §3 specifies; changing object_name metadata alone is insufficient. Use the frozen
   DISH/RBHR/R06-prefixed evaluation address, physical tick/field/sample/draw coordinates and
   original transforms. No imported-module global mutation, fake lanes, altered TRAIN addresses,
   sampled-row selection, extra reference panel or source fork. Card §5's seven branches remain
   untouched; no outcome has yet been measured.

4. **Acceptance and return.** Apply the card §7 focused coverage once: changed master consumers;
   width1 address/transform and nonrenewal behavior; unchanged modal path; same final weights and
   fixed Welford with fresh native/recurrent state; native promotion; a few synthetic primary
   and first-transfer/null cases. Reuse credible existing LR/renewal/terminal coverage. The RNG
   and scientific semantics require the existing independent high-risk review, with corrections
   returned to the same executor/reviewer and no extra review layer. Relevant authorities are
   evidence-spec §§4, 5.2, 11.4, 11.8.6–11.8.7 and engineering-scope §§4–5. Report changed paths,
   pushed source SHA, exact focused checks and what they establish, review outcome, source-line
   accounting and any remaining concrete gap. Root integrates; DM retains scientific acceptance.
   Before any later result-bearing launch, bind accepted committed/pushed bytes and use the
   configured remote node with fresh same-node memory admission (physical and effective available
   memory each >=4 GiB). This document contains no launch command or run authorization.

5. **Budget and stop.** Card §6 and its existing
   [exposure/cost record](sampled_execution_b06_20260906/EXPOSURE_AND_COST.json) are binding:
   <=2000 new non-test lines, <=600 per runner, existing focused-test budget, and **one complete
   1800s B06 invocation**, including necessary checks/build/load, initialization, labels/training,
   all evaluation, reduction and publication. Account for required checks toward that cap;
   stages/modes do not reset it. Engineering-scope §4 items needed: **none**. No extra A, seed,
   sample, checkpoint selection or budget. Stop this CM implementation task at pushed source and
   acceptance record, or return a concrete unresolved semantic/dependency/budget conflict while
   preserving completed conforming work. Do not silently trim the card or treat this handoff as
   permission to execute the scientific invocation. Ordinary in-scope code/check repairs continue
   to acceptance; they create no experiment retry budget.

Owner boundary: current primary-checkout `item.py reviews --json` returned `[]`; the standing
card/intake P2 items `20260906-dish-006` and `20260906-dish-007` remain the owner surfaces.
This handoff changes no frozen scientific meaning, card, prediction, Portfolio disposition or
exposure. No new P2 item is needed; the technical preparation is recorded in the audit ledger.

Dispatch receipt: the existing child accepted `followup_task` and was observed running under
the identity above. Its task message binds the five items to integrated `fde638f9c`, requires
an owned CM branch/worktree and independent high-risk review, and explicitly forbids a B06
result-bearing initializer/training/evaluation invocation. CM technical delivery and DM result
intake are still pending; no code, check result, source SHA or launch is accepted by this receipt.
