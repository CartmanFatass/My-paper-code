# FOLR B02 execution selection and scientific intake — 2026-09-09

**Before-output selection recorded at 2026-09-09T20:05:36Z.** No B02 scientific result had
been observed when this section and the prediction below were committed. Preparation and
technical acceptance remain separately recorded in the
[preparation intake](FOLR_PUBLIC_LIFECYCLE_B02_PREPARATION_INTAKE_20260909.md).

## 1. New execution authority, options and prediction

Root accepted source `434f10cf95f16dd342cbf754382aa76155fcd2b7`, technical evidence
`8183830ac99196f044ee7024e097e927bfb54a43` and DM acceptance
`5f0e2ffb8a6a995f759bb3db621722aef7f3e6b8`, integrated as main `5a9f23629`, `dad01d32a`
and `cd6b63f63`, and then explicitly allocated one frozen independent training pair.
The shared authoring checkout started this selection clean at `5f0e2ffb8` on
`codex/vap-folr`. Main's previous technical audit mapping is branch L13 to main L144;
this execution selection is a new row, not a rewrite of that technical acceptance.

**Object tier.** Options: (a) execute the already-frozen RETAIN/RESET pair at 7802/107802;
(b) defer the pair and retain the single B01 observation. Recommend/select **(a)**.
The new independent fitting process directly answers repeatability of the full trained
package. Additional evaluation of B01 weights would not add that independent unit.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a), within Root's new
explicit two-arm allocation.** This adds no Portfolio priority/lifecycle decision and
changes no mechanism, comparator, result branch or seed choice.

**Prediction before output: RESET_ABOVE_MEI remains the leading branch**, as frozen during
preparation. B01's trustworthy `d_01=-2.0021875` is the strongest support; its lower RESET
training mean, broad final-return spread and single training pair limit confidence.
WITHIN_MEI and RETAIN reversal remain possible and will be preserved. Owner prediction:
**not taken (unattended)**; all-age owner reviews were empty at this boundary.

## 2. Bound execution and interpretation

The [card §§2–6](FOLR_PUBLIC_LIFECYCLE_B02_SCIENCE_CARD_20260909.md) controls the unchanged
science and this new authority. Source `434f10cf95f16dd342cbf754382aa76155fcd2b7` starts fresh
learner/environment/replay/optimizer/hidden state in each new process, with no B01 state or
data reuse. Actual training/evaluation seeds are 7802/107802. Each arm has 5,000 training
episodes, 4,969 RMSprop steps and one 32-episode final greedy evaluation. RETAIN is followed
by RESET regardless of an intact first-arm sign. The three inclusive-boundary branches
read `d_02` only; B01 stays separate and no average rewrites either pair's branch.

Exactly two accepted arm submissions are permitted, one per arm, on the configured remote
node using detached `agent-task` and fresh destination admission immediately before each
runner. The original CM owns implementation/execution evidence, sole observation, complete
exit/publication and verified collection. DM owns scientific acceptance; Root owns final
integration and any successor. No accepted scientific attempt is replaced, no missing arm
is silently paired and uncertain acceptance requires reconciliation rather than resubmission.

Complete caps are 1,800s per arm/3,600s per pair. Supporting checks/readbacks have 60s total,
including already spent 3.0730197s CM plus 0.0661974s DM; executable arithmetic gives
3.1392171s spent and **56.8607829s remaining** at allocation. Existing semantic review and
the two controlled seed cases are reused. There is no pilot, retry, extra evaluation, tuning,
extra seed/arm, diagnostic, local fallback or automatic successor. A pre-acceptance technical
failure can be repaired within the stated rules and remaining budget; a failed scientific
attempt returns retained evidence. Previously blocked scratch remains under CM ownership.

Per-arm planned exposure remains 100,000 training ticks/4,969 optimizer steps/32 final greedy
episodes; the whole pair has 201,280 total native ticks and 9,938 updates. The dominant
replay work remains `2 arms × 4969 updates × 32 episodes × 21 positions × 5 slots × 2 passes`.
Historical B01 full wall 1,517.58s is a same-workload point reference, not B02 actual cost.
CM will distinguish summed invocation wall, aggregate CPU work and study elapsed critical
path, retaining actual publication and collection facts.

The current scientific-reading/independent-unit and information limits in preparation intake
§2 are reused. Fresh complete training, not a changed seed label alone, supplies the intended
new unit; equal within-pair labels do not force equal endogenous traffic. No new literature
or semantic gap was identified by this allocation. Final-return evidence will address only
the full trained package on the declared host/exposure, with no stable-superiority, causal
memory-content, original-CAMA information, strictly-self or transfer claim.
