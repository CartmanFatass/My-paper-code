# FSD interruption × batch B01 — result evidence

## Result and rule applied verbatim

**Valid complete B/EXPLORE: eight original fits, two independent training blocks.
The high-batch renewal primary mean is above the declared .01J MEI, with mixed
block signs and weak training precision.** The [card](FSD_INTERRUPTION_BATCH_B01_PROSPECTIVE_CARD_20260914.md)
states:

> How the result will be interpreted: a primary mean above +.01 is a bounded local
> high-batch renewal signal; within [−.01,+.01] is an unresolved/small observed contrast,
> not equivalence; below −.01 is adverse for this specific intervention/budget.
> Opposite simple-effect signs or a large interaction motivate a narrower dependence
> question. Even a precise two-arm zero says nothing by itself about MB. Supported
> MB plus the other factorial contrasts is needed for a batch explanation. No branch
> automatically parks the direction, switches D0 default, promotes C, adds a seed or
> changes the selected endpoint. Record uncertainty and the next useful question.

Primary I1280−D1280 is −.026440300139166675 and+.08464985087421936J in the
two blocks, mean **+.029104775367526342J**, training sample SD.07855259910460288,
SE.05554507550669301. The predeclared iid-normal/df1 working-model95% interval is
**[−.6766623261067976,+.7348718768418502]**. With two blocks the model assumption
is uncheckable and coverage is not established. The wide interval and one adverse
block remain prominent; the mean branch is not evidence of stable superiority.

## All newly trained endpoints and factorial contrasts

Each entry is the sole final32-world mean after five training updates.

| Training block / evaluation base | D128 | D1280 | I128 | I1280 |
| --- | ---: | ---: | ---: | ---: |
| 772003 / 782003 | .374894942897 | .403281382362 | .378108279375 | .376841082223 |
| 772103 / 782103 | .311076549329 | .316919684909 | .445736846121 | .401569535783 |

| Contrast | Block772003 | Block772103 | Mean | Training SD | Training SE | Working-model95% interval |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| SI1280, primary | −.02644030 | +.08464985 | +.02910478 | .07855260 | .05554508 | [−.67666233,+.73487188] |
| SI128 | +.00321334 | +.13466030 | +.06893682 | .09294704 | .06572348 | [−.76615918,+.90403281] |
| MI | −.01161348 | +.10965507 | +.04902080 | .08574982 | .06063428 | [−.72141075,+.81945234] |
| MB | +.01355962 | −.01916209 | −.00280123 | .02313774 | .01636085 | [−.21068560,+.20508313] |
| INT | −.02965364 | −.05001045 | −.03983204 | .01439444 | .01017840 | [−.16916093,+.08949685] |
| PKG | +.00194614 | +.09049299 | +.04621956 | .06261208 | .04427342 | [−.51632762,+.60876675] |

MI/MB use the card's one-half scaling; INT is SI1280−SI128, and PKG is
I1280−D128. The same eight fits supply these dependent contrasts; the table is
not six independent studies. Only the declared high-batch comparison is primary.
All intervals use the same explicitly conditional working model, not a verified
normality/coverage claim or a new significance gate.

[RESULT_SUMMARY.json](interruption_batch_b01_20260914/RESULT_SUMMARY.json) was
produced by the exact168e61295 reducer on the original remote summaries, exit0.
[TRAINING_ENDPOINTS.csv](interruption_batch_b01_20260914/TRAINING_ENDPOINTS.csv)
contains exactly eight once-aggregated training endpoints; scientific-tools
[TRAINING_RUN_SUMMARY.json](interruption_batch_b01_20260914/TRAINING_RUN_SUMMARY.json)
uses their declared within-block pairing with D1280. Its arm-level intervals do
not replace the factorial estimand or the card's working-model interval.
[PAIRED_ENDPOINT_EPISODES.csv](interruption_batch_b01_20260914/PAIRED_ENDPOINT_EPISODES.csv)
retains all64 matched world rows, all four U/J values and all contrast signs.
The primary has15 positive/17 adverse worlds in block1 and28 positive/4 adverse
in block2. These nested endpoint worlds are not training replicates.

## Native meaning, exposure and cost

All arms use the same Scenario1 six-UAV/fifty-user/H500 native objective,
CPU FP32/four Torch threads,16 training lanes and32 sole-final evaluation lanes.
D128/D1280 are authentic D2 with infinite individual/team gaps; I128/I1280
have individual gap.25 and team gap infinite. All have k/caps10, opportunity1,
ageoff, the same primitive-reactive private recurrent actors, reset/bootstrap,
native credit/reward, lower PPO and separate evaluator/RNG/mode/synchronization.
Both renewal paths legally use global state and joint observations at the
coordinator; actors act from their private observation, supplied skill and memory.
Holding a skill does not hold velocity or remove primitive observations.

The switches compare implemented renewal learning paths and batch arrangements.
Renewal changes decisions, segment credit, collected rows and subsequent policies;
batch size changes optimizer chunks and normalization groups. The factorial does
not isolate every mediator or prove a pure-duration mechanism. The native reward
reconstruction .7×coverage+.3×quality−altitude penalty agrees with all256 J values
to maximum absolute error5.28e−15. The historical field name `energy_penalty`
denotes this native altitude penalty; reward accounting is not behavioral causation.

Actual totals: eight real training starts,16 model constructions,40 update stages,
320000 trained/stored team transitions/640 episodes,128000 final team steps/256
episodes,24000 batched controller calls and2688000 agent-step opportunities.
Every fit has real positive actor/critic update counts, all recorded update losses
finite, and zero evaluator optimizer calls. There are zero checkpoint loads,
replacement fits, retries, model smokes or interim/fresh evaluation panels.

| Original | Whole-command wall s | User+system CPU s | Peak RSS KiB | Coordinator steps |
| --- | ---: | ---: | ---: | ---: |
| 772003 D1280 | 487.60 | 1920.49 | 2589996 | 75 |
| 772003 I1280 | 1075.13 | 4250.10 | 3534244 | 330 |
| 772003 D128 | 463.64 | 1827.95 | 1634088 | 525 |
| 772003 I128 | 1204.05 | 4778.34 | 1700200 | 3120 |
| 772103 D1280 | 594.97 | 2331.06 | 2540840 | 75 |
| 772103 I1280 | 1319.23 | 5226.84 | 3558196 | 360 |
| 772103 D128 | 515.18 | 2025.42 | 1638784 | 525 |
| 772103 I128 | 1159.59 | 4602.62 | 1644080 | 3240 |
| Sum | **6819.39** | **26962.82** | — | **8250** |

Coordinator counts match15×sum ceil(valid joint rows/batch) in every fit;
[PROVENANCE.json](interruption_batch_b01_20260914/PROVENANCE.json) retains each
rollout's rows and all actual costs. Actor/critic steps are90000 each across8 fits,
team/individual discriminator steps600/2400. More/fewer coordinator steps alone
do not imply complete-command speed or equal overall learning work. CPU is summed
once, not multiplied by threads. GNU time covers adjacent admission, imports,
training, final evaluation and publication. The approximate first-start to last
timed-command-end span is7762.59s, based on integer-second supervisor starts;
it is distinct from summed walls and not a recorded terminal timestamp. Support
preparation/review/transport/collection/preservation and supervisor/cleanup tails
are `resources_unmeasured`, not zero. Ordinary900/1800s forecasts were never caps;
there was no process deadline or observed source-budget breach. Scope §4: none.

## Support, contradiction and claim ceiling

The second block supports renewal benefit at both batches; the primary mean and
package mean are positive. The first block contradicts a uniformly beneficial
high-batch renewal switch. Training variability is large relative to the primary
mean. Both observed interactions are negative, suggesting a narrower dependence
of renewal's effect on the batch arrangement, but two blocks and the broad interval
do not establish a stable interaction. MB is small in mean and opposite in sign
between blocks: this does not prove batch equivalence or a general batch benefit.
The eight planned fits were retained irrespective of their scores.

The five historical package observations retain their own accepted conditions;
none is pooled into this factorial primary or retroactively rescored. Missing
tuned same-information baseline competence/headroom still limits absolute method
value. The completed [baseline work plan](FSD_RESTART_PREPARATION_INTAKE_20260914.md#baseline-information-audit-and-bounded-work-plan)
distinguishes direct fixed-k, private-flat and central-input alternatives; none
received a hidden fit or tuning allocation. Stable superiority, equivalence,
pure-duration attribution, longer-budget value, transfer, C promotion and a D0
default change remain outside this result.

## Technical acceptance and preservation

All eight originals ran from168e612956d098c017fe67377eadeb68589bf81d under the
complete F grant ca27db8d5. All adjacent memory floors passed; all supervisors
finished/exit0 and all endpoints passed the committed contract checks. Required
prelaunch independent review and26 distinct synthetic cases passed; see
[EXECUTION.md](interruption_batch_b01_20260914/EXECUTION.md).
The Monitor's handwritten times, premature healthy finals and duplicate-key
state were observation-control faults. DM resumed the same observer, used native
terminal returns, preserved the old raw state and repaired the aggregate. Original5
had no directly readable adoption while live; no earlier adoption is invented.
These faults neither changed the learner nor supplied outcome polarity. The
terminal [state](interruption_batch_b01_20260914/MONITOR_TERMINAL_STATE.json)
contains8 received terminal facts and an empty active set.

Eight unchanged raw archives preserve88 files/138032 compressed bytes. Their
archive and per-file digests, supervisor facts, admissions and resources are in
PROVENANCE.json. Source remains published in Git. The [intake](FSD_INTERRUPTION_BATCH_B01_INTAKE_20260915.md)
records independent result-review acceptance and owner pause application. Remote
cleanup occurs only after Root confirms this preservation/integration; receipts
are linked there. Completion is not scientific PARK: owner requested a safe
execution pause after this finite chain.
