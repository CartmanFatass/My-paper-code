# DISH A04 — reconstruction of four recorded origin rejections

Date: 2026-09-05. Object `DISH-ORIGIN-CERTIFICATE-A04`, **A / RECON**.
Card: `DISH_ORIGIN_CERTIFICATE_A04_SCIENCE_CARD_20260905.md`, frozen at `70ad81cfc`.
The complete result is **A04-RECORDED-REJECTION-RECONSTRUCTED**. This is adaptive
analysis of retained A03 evidence, with no new trajectory or algorithm-effect estimate.

## 1. Identity, original evidence and comparator

One accepted task `dish_origin_certificate_a04_a1`, PID 1668923, node `wsl_4070`,
source `d543146cc11ccf880da1245bfb6884356772dd38`, exact detached cwd
`/home/wu/hmasd-worktrees/dish-certificate-a04-d543146c`. The command recorded in
`DISH_ORIGIN_CERTIFICATE_A04_CM_RETURN_20260905.md` joins actual-node memory admission
and the runner by `&&`. The sole shared tracker observed terminal exit 0; CM collected
the original artifacts and DM acknowledged that terminal handoff. No successor ran.

The only input is the original A03 paired trace, source
`818b2566d1bac7cafcc71ed0bbb90b8abd1c6b65`, collection `e58b9f1f8`. Exactly four
new-host origins 340/364/388/596 and following records 341/365/389/597 are reconstructed.
They belong to `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`, retained seed 11, original panel 0.
The original trace has no separate per-tick coordinate key; its fixed panel provenance
comes from the accepted A03 generation and input digest, not an invented field.

Treatment is decomposition of the unchanged certificate conjunction. Its strongest
same-input comparator is the native certificate recorded at that actual call. No
relaxed threshold, replacement prediction, altered position or hypothetical service
outcome is a comparison arm. The fixed retained policy, host, roles and protocol
semantics remain the original A03 provenance.

Original output root relative to the exact cwd:
`temp/directions/degraded_incumbent_shadow_handover/exp/origin_certificate_a04_20260905/`.
Output is `a1/summary.json`, receipt `a1_admission.json`, and original supervisor log
`/home/wu/.agent-tasks/dish_origin_certificate_a04_a1/task.log`. Local originals use
the same relative output root in
`C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904`, with `task.log` inside `a1`.
The original A03 trace remains under that worktree's
`temp/directions/degraded_incumbent_shadow_handover/exp/ground_endpoint_path_a03_20260905/a1/trace.jsonl`
and the corresponding original remote `dish-endpoint-a03-818b2566` worktree.

| Original artifact | Bytes | SHA256 checked by DM |
| --- | ---: | --- |
| A04 summary.json | 62,118 | `81b71bdd8984bb99540aeb4833e029458f013c3b0ab21639aa710943476e2f50` |
| A04 a1_admission.json | 504 | `ae76cf68ad6ba8a4ba872ae0715706136acbbcb665bdff8df333ed07b500fff0` |
| A04 task.log | 40,047 | `46863e651a9e14ca89c2c175d0b2f6c192f5af2971c7d2dbc2457a92671de8ca` |
| Retained A03 trace.jsonl | 39,140,340 | `f2c612928529f30b0566c8895cb40644071dd87c2db03b14cededd98e0dbf45d` |

CM's accepted collection is `ae18bc88cf08808496d256222ec1e54c6875d1e7`, documented in
`DISH_ORIGIN_CERTIFICATE_A04_COLLECTION_20260905.md`. DM compared the committed Git
blob of `DISH_ORIGIN_CERTIFICATE_A04_SUMMARY_20260905.json` with the local original:
all 62,118 bytes are identical. These are provenance checks, not new launch guards.

## 2. Rule applied verbatim

> - Complete outputs for all four origins, reconstructed certificate equal to its recorded
>   native value each time, and at least one numerically non-close failed predicate per
>   rejected origin: **A04-RECORDED-REJECTION-RECONSTRUCTED**. Report the contributing
>   predicate set per origin; this does not show how changing it would affect native service.
> - Otherwise, with complete data/arithmetic: **A04-RECONSTRUCTION-DISCREPANCY**. State
>   whether the issue is a boolean mismatch or only close-boundary support. No local
>   defect classification or scientific polarity is assigned without exact-step reproduction.

All four outputs are complete. Each reconstructed certificate is false and equals
the recorded native false value. Each has two numerically non-close failed predicates.
Apply branch 1: **A04-RECORDED-REJECTION-RECONSTRUCTED**. Both discrepancy flags are
false; the original A03 branch and native rejection records are unchanged.

## 3. Actual boundaries, readout and DM checks

DM independently read the original summary and eight selected records from the retained
trace, without importing the runner, calling its reconstruction helper or creating a
native/model instance. Policy outputs, pre-motion prepared positions, post-increment
latch/warmup, post-projection held commands, owner/intent identity and following rejection
facts match the original fields exactly. Source sequence/existence and other state
predicate values also match. Final moved positions and earlier unprojected commands
were not substituted. All four intents still belong to the initial physical owner U0.

The original derived readout contains all 14 predicates in native order and all 21
service-tail probabilities per origin. DM checked the literal value/threshold comparisons,
signed distances, numeric-close flags, descending tail identities, first passing tail's
q95, failed lists and conjunction/recorded Boolean agreement. This is intake verification
of the original outputs, not another reconstruction experiment or independent replication.

| Origin / following tick | Native / reconstructed | Mahalanobis, limit 5.99 | q95, minimum 0.60 | Non-close failed predicates |
| --- | --- | ---: | ---: | --- |
| 340 / 341 | false / false | 4135.21963947819 | 0.20 | mahalanobis_limit, predictive_q95 |
| 364 / 365 | false / false | 5637.997396171908 | 0.20 | mahalanobis_limit, predictive_q95 |
| 388 / 389 | false / false | 6693.99393802707 | 0.20 | mahalanobis_limit, predictive_q95 |
| 596 / 597 | false / false | 1056.9161411453172 | 0.15 | mahalanobis_limit, predictive_q95 |

These quantities are arithmetic derived from the observed policy outputs. The native
certificate, its actual inputs and the following rejection are direct observations.
Each next tick records application reason 2 and an invalid-commit increment of 1.
All eight state/support predicates, finite-Mahalanobis checks and three physical/action
predicates pass at every origin. Preparation warmup is 57/81/105/313 ticks. Prepared
separation is 178.27069254883617/193.05400995202896/220.38105120869872/639.1444807573085 m.
The largest bounded-raw/held-command norm is 1.4337300687094967, below 1.500000000001.

There are zero close flags among 56 predicates and 84 tail-to-0.95 comparisons. The
smallest absolute distance among non-discrete predicate comparisons is
0.06626993129150338; among service-tail comparisons it is 0.006922610419248132.
Both exceed the card's 1e-10 disclosure band. Discrete equalities are correctly excluded
from that band. No comparison is relaxed or rounded before the reading.

The two failures are each sufficient to make this conjunction false at the recorded
inputs. This is a statement about the existing Boolean law, not an intervention: the
data do not establish that changing either input or threshold would produce a legal
application or service. Four rejection locations on one adaptively inspected trajectory
are not four independent seeds and support no general rejection-rate estimate.

## 4. Exposure, resources and engineering conformity

Machine exposure: one retained trace read, four origin reconstructions and four following
comparisons. Native prepared/completed ticks, model/policy/optimizer initializations,
training transitions, learner updates and optimizer steps are all zero. Parameter
displacement is not applicable, because A04 instantiates no model. B01 training and A03
trace creation remain input provenance and are not counted as new A04 exposure.

Fresh actual-node admission assessed at `2026-09-05T11:49:08.633521Z`: physical and
effective available memory each 12,912,066,560 bytes, minimum 4,294,967,296, both floor
flags and overall passed true. The recorded adjacent command establishes ordering.

| Resource quantity | Observation |
| --- | ---: |
| Prepublication runner wall in original summary | 0.2899738739943132 s |
| Completed runner wall in original stdout | 0.2929954849969363 s |
| Final metadata/publication interval | 0.0030216110026231036 s |
| Prepublication peak RSS | 16,220,160 bytes |
| Completed peak RSS | 16,384,000 bytes |
| Prospective cost law / cap | 1.5 * (5 + 4 * (1 + 1)) = 19.5 s / 60 s |

DM verified that original stdout equals the summary after removing only its three
postpublication resource fields. The summary was not rewritten. The publication interval
includes final metadata work and publication; it is not an isolated filesystem benchmark.
`resources_unmeasured=false`, and the measured full runner time satisfies the cap.

Supervisor start and finish both display `2026-09-05T19:49:08+08:00` (11:49:08Z).
Its 0-second integer-duration field has insufficient resolution to measure this run;
it does not mean zero compute. Tracker uptime 28 seconds is observation latency scope,
not experiment runtime. The valid-result cost is the measured 0.2929954849969363 runner
seconds; no precise combined verification-plus-result or lifetime direction denominator
is inferred from the integer supervisor fields.

CM and its independent reviewer accepted the exact source: 238 new non-test lines,
64 runner lines, 128 test lines excluded, orchestration 71/238 = 29.83%, engineering
scope section 4 adds none. The small arithmetic module sits directly in the direction
namespace to avoid importing B01's learner/native dependencies; this DM-acknowledged
placement changes no scientific quantity. Existing native, loader, API and old runners
are unchanged. There is no accepted-attempt engineering-budget breach.

The one focused exact-source verification passed five synthetic tests in 0.03 seconds,
including a toy publication smoke of 0.01 seconds. It covers the scalar law, full readout,
boundary-field distinctions and publication; it does not establish native bit identity
or mechanism value. No repeated suite, actual-card fixture arithmetic in tests or new
native equivalence study occurred. No open publication-profile omission remains.

## 5. Prediction, MEI and claim boundary

The DM's predicted reconstructed-rejection branch and prediction/service-confidence
failure at every origin both match. q95 fails 4/4, tied with the Mahalanobis limit at
4/4; it is co-most-common, with no support for uniquely dominant q95 failure. The
predicted alternative of state/action restriction with adequate confidence does not
describe these four calls. Owner prediction: `not taken (unattended)`.

The card's diagnostic MEI, at least one non-close false predicate per rejection, is
met at all four origins. It is not a return-improvement threshold. No tuned same-information
headroom is available, B01's five-tick source-effect MEI remains unestimated, and A03's
299 incumbent service ticks remain unrelated to post-transfer source advantage.

Strongest support is complete same-call native agreement with two well-separated
prediction-related failures and passing state/action conditions. The continued absence
of a legal transfer is the strongest contradiction to full host-path qualification.
The result does not establish calibrated predictions, a remedy, a native implementation
defect, universal policy incapacity or any RETAIN/COPY/SHADOW effect. Learned-head semantics,
training signal and finite exposure remain explanations to examine separately. Existing
PRO_FINAL CONTINUE authority, B01/A01/A02/A03 readings and N3's other source IDs remain intact.
