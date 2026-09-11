# FOLR B02 execution selection and scientific intake — 2026-09-09

**Accepted valid B/EXPLORE at 2026-09-09T20:50:22Z: RESET_ABOVE_MEI.** The new pair's
RETAIN-minus-RESET difference is -1.9228125. Sections 3–6 record scientific intake; the
following before-output selection and prediction remain unchanged.

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

## 3. Completed result: what I checked and the rule applied

CM returned the [complete result evidence](FOLR_PUBLIC_LIFECYCLE_B02_RESULT_EVIDENCE_20260909.md)
and [paired summary](FOLR_PUBLIC_LIFECYCLE_B02_RESULT_SUMMARY_20260909.json) at
`429e4df7bbb1712ffe98917ca50183093374203d`, pushed on the shared direction branch. I checked
HEAD/upstream and the clean checkout after CM released writer/index ownership. Execution
changed only B02 evidence documents; the accepted source remained
`434f10cf95f16dd342cbf754382aa76155fcd2b7`. The allocation/card revision is
`8a6b11b14515faf91db9894b443ce7349489f34f`.

I read the result document against card §§2–6, the complete paired record and all 64 final
returns, and each collected arm's external `process.time`. I checked seeds, source, complete
counts, event exposure, memory receipts, terminal facts and the reported local/remote
checkpoint/summary digest agreement. The independent stdlib analysis recomputed the means
from every return and applied the frozen rule; no model, environment, learner, checkpoint
reload, policy evaluation or repeated CM test was invoked. The paired summary read has
SHA256 `e15843540cd7f9d923084cdd104dfa8053812af948f5a283a78a74df2d55b07b`.

Card §3, applied verbatim:

- `d_02 >= 1.0`: `RETAIN_ABOVE_MEI` for this new pair.
- `d_02 <= -1.0`: `RESET_ABOVE_MEI` for this new pair.
- `-1.0 < d_02 < 1.0`: `WITHIN_MEI` for this new pair, not equivalence.

`J_RETAIN=1.3278124999999996`, `J_RESET=3.250625`, hence
`d_02=-1.9228125000000003`: **RESET_ABOVE_MEI**. This classification uses B02 alone.

| Preserved endpoint | B01 | B02 |
| --- | ---: | ---: |
| Training / final evaluation seeds | 7801 / 107801 | 7802 / 107802 |
| RETAIN final native mean | 2.104375 | 1.3278125 |
| RESET final native mean | 4.1065625 | 3.250625 |
| RETAIN minus RESET | -2.0021875 | -1.9228125 |
| Each object's own branch | RESET_ABOVE_MEI | RESET_ABOVE_MEI |

The [four endpoint rows](evidence/2026-09-09-folr-public-lifecycle-b02-run-endpoints.csv)
identify both objects separately under their common host/recipe. The standard scientific
tool's [paired run analysis](evidence/2026-09-09-folr-public-lifecycle-b02-run-analysis.json)
has two training instances per arm and two matched differences, not evaluation-episode rows.
Its two-pair mean difference -1.9625 is descriptive. Neither that mean nor its small
two-point sample SD rewrites an object's branch or estimates population certainty reliably.

## 4. Observation, exposure and scientific interpretation

Each B02 arm has **5,000 training episodes, 100,000 real native training ticks, 4,969 RMSprop
steps and one 32-episode final greedy evaluation spanning 640 native ticks**. Total B02
exposure is 200,000 training ticks, 9,938 updates and 64 final episodes/1,280 evaluation
ticks, hence 201,280 native ticks. No partial prefix or missing arm was substituted.

| Recorded lifecycle quantity | RETAIN training | RESET training | RETAIN final | RESET final |
| --- | ---: | ---: | ---: | ---: |
| Births | 21,110 | 22,474 | 136 | 174 |
| Departures | 7,855 | 10,395 | 36 | 99 |
| Survivor control opportunities | 46,125 | 50,469 | 292 | 389 |
| Actual survivor resets | 0 | 50,469 | 0 | 389 |

These counts use the card's terminal exclusions for control opportunities/resets and its
inclusion of terminal native births/departures. Both arms had real survivor control
opportunities; RESET applied its rule there. No learner-side instrumentation defect was
reported. Event totals are endogenous to the trained policies: equal seeds did not create
identical traffic. They are exposure observations, not event-conditioned return weights or
a causal normalization.

| B02 descriptive quantity | RETAIN | RESET |
| --- | ---: | ---: |
| Mean training native return | -4.716158 | -3.798230 |
| Final episode sample SD | 5.519984 | 9.253385 |
| Final episode minimum / maximum | -8.93 / 11.33 | -16.02 / 24.70 |
| Negative final episodes, of 32 | 17 | 13 |

All negative episodes remain in the primary. Episode spread is conditional on each trained
policy and does not supply additional training seeds. B02's RESET training mean is also
higher; B01's contrary training ordering remains -5.225858 RESET versus -5.044872 RETAIN.
The shared gamma-0.99 approximate Q-learning method does not guarantee exact optimization
of the undiscounted final-return endpoint, so these training and final observations stay separate.

**Bounded conclusion.** The RESET-favoring final point repeated beyond MEI in this second
fresh fitting/evaluation instance. Two recorded matched pairs now support a preliminary
trained-package preference for RESET on this explicitly public-lifecycle easy Traffic
Junction host at the fixed exposure. This is a native-return result on that declared
information variant, with no new proxy or original-CAMA comparison.

**Strongest support.** Both separately generated/trained pairs have the same above-MEI
ordering against the same generic RETAIN actor/mixer package; nonzero learning and real
survivor-control exposure are observed, with complete unfiltered final measurements.

**Strongest limitations and surviving alternative.** There are only two training instances,
each with 32 conditional final episodes; B02 was selected after B01, and rollout spread is
wide. Generic RETAIN remains a competent same-information comparator. Finite optimizer/data
paths, partner co-adaptation and evaluation variation remain alternatives to beneficial
erasure of any particular memory content. Public E/own-B cues, fresh entrants and full
survivor history remain as declared; this result supplies no strictly-self, typed-state,
information-necessity, stable-superiority, transfer or UAV claim. Tuned same-information
headroom on this host remains absent.

**Knowledge applied.** Reused preparation intake §2's current Foundations §§1–4/6 and
empirical/MARL topic reading: fresh complete fitting/evaluation processes justify the new
unit under the ordinary PRNG assumption; labels alone do not establish it, and same labels
do not imply matched exogenous event tapes. Reused the verified CAMA/Sable corpus retrieval
in B01 intake §4 and P68/P77 for the legal comparator and lifecycle information boundary.
Those sources do not establish a cause for this particular within-episode clearing gain.
The second point therefore changes the repeatability evidence, not the mechanism attribution;
no new broad search or stronger-class prerequisite was introduced.

## 5. Receipts, resources and engineering conformance

Both commands used source `434f10cf95f16dd342cbf754382aa76155fcd2b7` in detached remote cwd
`/home/wu/hmasd-worktrees/folr-public-lifecycle-b02-434f10cf`, node `hmasd-wsl-node`, configured
Python, CPU FP32 and Torch compute/interop threads `[1,1]`. Each newly seeded process created
fresh learner/replay/optimizer/environment state; no B01 state/data were loaded.

| Direct process fact | RETAIN | RESET |
| --- | --- | --- |
| Supervisor handle suffix after `folr-public-lifecycle-b02-` | retain-20260909 | reset-20260909 |
| Accepted / exited, UTC | 20:09:12 / 20:22:00 | 20:23:41 / 20:36:14 |
| Original PID / final exit | 3066045 / 0 | 3067605 / 0 |
| Fresh physical/effective available bytes | 15,637,336,064 | 15,635,468,288 |
| Complete external wall, seconds | 767.84 | 753.11 |
| OS user / system CPU seconds | 755.86 / 12.87 | 735.19 / 19.38 |
| External peak RSS, KiB | 658,116 | 666,984 |

Admission receipts at 20:09:12.751945Z and 20:23:41.064931Z each passed the physical and
effective 4,294,967,296-byte floors immediately before its runner. Their unavailable cgroup
fields remain null; no cgroup-headroom claim follows. Full wall and RSS are measured.
Narrower runner pre-publication wall values 767.480854s/752.809354s and RSS
642,872/638,404 KiB remain separately available; no cause is assigned to their difference
from the external measurements. Peak RSS values are per invocation and are not summed.

Summed complete invocation wall is **1,520.95s**, versus 1,800s per arm/3,600s per pair caps.
Aggregate user+system CPU is **1,523.30 CPU-seconds**. First supervisor start to final exit
is **1,622s**, including the 101s between arms and rounded timestamps; this elapsed window
excludes prior staging and final collection. These are distinct quantities. Source/history,
Git/network staging, ordinary observation and all control-plane/intake labor are not a
complete aggregated study-cost series here.

CM's cumulative supporting checks/readbacks, including the earlier 0.0564545s DM RETAIN
readback, were 7.1517154s. Added DM final readback was 0.0749846s, the complete analysis
command 0.3421748s, and analysis-output readback 0.0655182s: **7.634393s through scientific
analysis**, within the 60s total cap. The analysis program's narrower internal pre-publication
time was 0.1083586s and is not substituted for its charged command wall. Final document
consistency checking took 0.2124487s: three verbatim rules, 14 local links, four endpoint rows,
two matched pairs, unchanged result bytes and a 405-character Chinese brief with six headings
passed. Thus measured supporting checks/readbacks total **7.8468417s of 60s**. Complete
scientific wall plus these measured supporting operations is **1,528.7968417s per this one
valid paired result**, with the above scope exclusions and no additional target invocation.

Exactly two accepted scientific submissions ran, one per arm, sequentially. There were zero
failed scientific attempts, retries, extra seeds/arms, diagnostics, native smoke, extra final
evaluations, local fallbacks, source edits during execution or automatic successors. No
§4 machinery was added beyond the already-declared four reused counters; the accepted seed
change remains within the 102-line runner and ordinary source limits. No §5 budget breach
or primary/information/comparison/training defect was identified. Engineering conformance
and the observed native-return result are separate conclusions.

CM's local/remote summary and checkpoint digest agreement is recorded in the execution
evidence. Both local roots `temp/directions/vap_folr_core/exp/public_lifecycle_b02_seed7802_<arm>`
retain the summary, final checkpoint, process timing, task log and memory receipt. The remote
detached worktree and two scoped supervisor directories are retained pending Root's verified
preservation/reclamation trigger; the original CM remains the closeout executor. No deletion
occurred here. Previously blocked B01/B02 test scratch remains CM-owned under the recorded
automatic-approval rejection `rejected: blocked by policy`; no retry or bypass was made.

## 6. Decisions this intake produces

**Object tier, validity and bounded reading.** Options: (a) accept the intact new pair under
its frozen rule; (b) quarantine a concrete primary, comparison or training defect. Recommend
and select **(a)** because the card, complete returned observations and receipts agree and
no such defect was identified. **Owner-delegated decision (unattended, 2026-09-03 instruction):
(a), valid B02 RESET_ABOVE_MEI with a two-instance claim ceiling.** The finite allocation is
finished. A/B objects have no C consumption state; this accepts neither a C conclusion nor
a family closure/recast/park or Portfolio disposition.

**Next discriminator, direction-local advice only.** Options: (a) recommend another fresh
matched training comparison under the same package to probe repeatability further; (b) no
immediate follow-up; (c) substitute a mechanism diagnostic/tuning search or promote the claim
from these points. Recommend **(a)**: two above-MEI native points justify considering one
more independent observation, at a known same-workload cost near the current 1,520.95s pair,
without first requiring causal localization. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a), recommendation only.** No new seed, card, cap, invocation or
Pro Send is selected/allocated here. This is not a fixed seed quota or a prerequisite for
other class-correct performance exploration. Root integrates this return and chooses later
execution capacity/successor work; any new scientific selection remains explicitly recorded
at its proper tier.

**Prediction score and owner surface.** The B02 leading RESET_ABOVE_MEI prediction, fixed
before its output, **matched**. B01's earlier WITHIN_MEI prediction remains a miss. Owner
prediction: **not taken (unattended)**. All-age owner reviews were empty and all ten current
main FOLR audit owner cells were empty at intake; no owner override was inferred. The
[Chinese brief](../../portfolio/owner/briefs/vap_folr_core/2026-09-09_public_lifecycle_b02.md)
records the result and limits. Ordinary validity/advice stay in this intake and audit; no
new P1/P2 item or material critic dissent is manufactured. Existing item 20260909-folr-004
and Root's main integration traces are preserved.

Root receives the allocation/admission/completion/DM commits and cleanup inventory for
integration and the preservation trigger. No live scientific process or uncertain accepted
operation remains. A later monitoring-policy cutover does not change this completed batch's
actual CM observation and collection history.
