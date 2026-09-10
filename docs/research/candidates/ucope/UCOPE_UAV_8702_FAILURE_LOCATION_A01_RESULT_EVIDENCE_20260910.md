# UCOPE 8702 failure location A01 — E0 evidence, 2026-09-10

**VALID COMPLETE A/RECON: bounded nonrecurrence.** The one declared T-prefix
invocation completed all 1740 training episodes and both 64-world evaluation
panels, without an exception. Source/card revision is
**b1d347ef303083824a72dd259c2fbb54e2b5ef75**. This is a repeated original 8702
history with **zero new independent training samples**. The comparison field
remains **INCOMPLETE**, with algorithm polarity null and no F/G/H result.

## Rule applied verbatim and claim boundary

The frozen [card §3](UCOPE_UAV_8702_FAILURE_LOCATION_A01_SCIENCE_CARD_20260910.md#3-primary-observation-and-reading-rule) supplies this row:

| Direct observation | A-level reading and recommended next object-tier choice |
| --- | --- |
| All 1740 T training episodes and both panels complete | No recurrence within this repeated prefix; historical cause remains unresolved. Consider the fresh independent T/F/G discriminator without making another replay obligatory. |

That completed-prefix branch applies. The error did not recur within this
declared replay on the reporting-repaired source. No actionable failing
operation or shape was observed, so the diagnostic location MEI is not met.
The original error's cause remains unresolved; no source repair of that cause
is established. This A observation cannot supply a performance effect,
independent replication, stable reliability or a replacement8702 comparison.
The historical 8702 attempt remains incomplete, and 8701 remains the sole
complete exact-recipe comparison with its bounded DOWN result.

## Direct prefix agreement and its limit

Offline comparison against the original preserved rows found every old
episode row and every old rollout row byte-identical to the new prefix:

| Retained file | Old rows | A01 rows | Matching old-prefix rows | First difference |
| --- | ---: | ---: | ---: | --- |
| episodes.jsonl | 1866 | 1868 | 1866 | none |
| rollouts.jsonl | 869 | 870 | 869 | none |

The old episode file and corresponding A01 prefix both hash to
`834eb8591faa78d63e0ffeae7053277ca5e5bedc75fbde6bc739c01888cd0761`;
the rollout pair both hash to
`cd044b74411e74892b7490ffc238893d02e401c75fa7fb7add7704445fcc8df9`.
A01 then completed training episodes 1738 and1739 and their ordinary four-epoch
update. The previous failure occurred during episode 1738's165th
step attempt, before an episode row was produced. This comparison establishes
agreement of the retained records, not equality of every hidden tensor, action
or unrecorded historical frame. It therefore supplies no unique explanation
for the historical non-recurrence difference.

Native inventory is exactly episodes.jsonl, rollouts.jsonl, summary.json and
final_T.pt. Failure context and a traceback are absent because no exception
was caught. The final T checkpoint is diagnostic at 1740 training episodes;
its byte count/hash were verified and it is preserved, without using a tensor
reload to enlarge this path claim or selecting it for a performance effect.

## Actual exposure and retained native measurements

| Quantity | Observed |
| --- | ---: |
| Diagnostic invocations / new independent training samples | 1 / 0 |
| T fits started / bounded T fits completed | 1 / 1 |
| Training / evaluation episodes | 1740 / 128 |
| Serialized episode / rollout rows | 1868 / 870 |
| Adam calls / finite serialized epoch records | 3480 / 3480 |
| Training / evaluation team steps | 445440 / 32768 |
| Attempted / returned UAV steps | 478208 / 478208 |
| Partial returned episode steps | 0 |
| Explicit / constructor resets | 1868 / 1 |
| Recurrent agent-observation rows | 2391040 |
| Velocity decisions / duration decisions | 1599610 / 1599610 |
| Duration-2 / duration-4 selections | 794585 / 0 |
| Horizon-censored holds / suppressed decisions | 3155 / 791430 |
| T duration-head forward rows | 9169252 |
| F/G/H fitted or evaluated episodes | 0 |

The head-forward count is 6×1492508 training renewals +2×107102 evaluation
renewals; completed training rows are replayed through four update epochs.
One optimizer trains 68553 parameters, including 2242 duration-head parameters.
Final reported whole-head displacement is 1.3016825914382935 (relative
0.3948028560958544); all-parameter displacement is 11.490781784057617.
These are exposure facts, with no causal or return attribution.

| Retained T panel | Mean J | Conditional mean SE |
| --- | ---: | ---: |
| 512 | 0.10497156306673558 | 0.009270105439687574 |
| 1024 | 0.1498504958382924 | 0.007480603341524169 |

Both full 64-vectors are exactly the old retained T panels; both evaluations
have zero optimizer calls and zero reported parameter displacement. They add
no independent training sample and no missing comparator. The SEs describe
evaluation variation conditional on this training history. Every panel,
exposure group, counter and the two additional episode rows is retained in the
[computed summary](UCOPE_UAV_8702_FAILURE_LOCATION_A01_RESULT_SUMMARY_20260910.json).

## Receipts, timing and verification

Root's terminal assignment directed intake, preservation and scoped remote
closeout. The copied Monitor receipt names handle
`ucope-uav-8702-failure-location-a01-20260910`, node `hmasd-wsl-node `,
source b1d347ef3, terminal finished/exit0, PID3100625 and supervisor duration 593s.
Its remote exit literal is 2026-09-11T04:39:31+08:00. The Monitor's local
observation literal 2026-09-10T20:39:56-07:00 has an inconsistent timezone label;
it is preserved as received and is not subtracted from a remote clock.

GNU time recorded **592.44s whole command** and **560896KiB peak RSS**.
The nested summary/T elapsed is592.076381453895s, leaving approximately0.36s
unlocalized outer residual, limited by GNU time's two-decimal resolution.
Neither phases nor supervisor duration are added to whole wall again. Charging
the entire100s support reserve gives a conservative **692.44s**, below the
1000s complete cap; the scientific invocation is below900s. No scope or time
budget breach is recorded. Aggregate CPU work and cgroup-specific resource
telemetry are `resources_unmeasured`; this does not erase the primary path fact.

Adjacent actual-node memory admission passed at 2026-09-10T20:29:38.661154Z:
physical/effective available15631753216 bytes, required4294967296 bytes,
empty failure reasons, /proc/meminfo source. The accepted CPU FP32/thread1
route and private streams remain those bound in the card and launch facts.

Collection verified byte counts and SHA256 for all **11 native/supervisor
files** and all **14 declared source/test paths**, with clean tracked remote
status and exact launch HEAD. Offline analysis passed **25 checks** covering
all 1868 episode rows, all 870 rollout identities, all 3480 finite epoch records,
reward-sum/256 identities, chronological resets/panels, every declared counter,
physical-duration support, frozen evaluation, absent comparison and whole cost.
It created no model, RNG, optimizer, environment or evaluator. The script
summarize_runs.py was inapplicable: this A object has no independent final
comparison endpoint, and repeated panels cannot be used as training samples.

Collection took2.7281758999743033s internally /3.0375629s outer command;
offline analysis took0.10431229998357594s before its final JSON write
/0.319996s outer command. Each pair is nested, not additive. Existing source
acceptance and two synthetic checks remain in the
[launch facts](UCOPE_UAV_8702_FAILURE_LOCATION_A01_LAUNCH_FACTS_20260910.json); no check was repeated at intake.
Raw evidence, source receipts and analysis scripts remain under
`temp/directions/ucope/exp/ucope-uav-8702-failure-location-a01-20260910/`.

## Prediction and next boundary

Prospective P(same recorded ValueError before 1740 episodes)=0.70; observed
event **false**, Brier loss **0.49**. Owner prediction **not taken**; main and
direction owner review queries both returned `[]` at this intake boundary.

The [intake](UCOPE_UAV_8702_FAILURE_LOCATION_A01_INTAKE_20260910.md#4-terminal-result-and-scientific-intake)
records the technical decisions and bounded reading. This one-invocation
allowance ends; it has no C consumption state. Fresh independent T/F/G remains
a next object-tier choice to consider, with no automatic budget or mandatory
replay. Chinese owner brief:
[2026-09-10_failure-location-a01.md](../../portfolio/owner/briefs/ucope/2026-09-10_failure-location-a01.md).
