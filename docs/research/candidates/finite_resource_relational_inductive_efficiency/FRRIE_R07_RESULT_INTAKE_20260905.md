# FRRIE R07 result intake — 2026-09-05

Status: `VALID_B_EXPLORE / R07_N15_WITHIN_MEI / N9_WITHIN_MEI`.

## What DM checked

DM read the frozen R07 card, CM E0/terminal commit
`900f525410e65928c91987a76a6051f8a992c7ce`, the unchanged 123,996-byte publisher JSON,
and the existing-artifact inventory addendum
`edad03b5e6f150474d7c5d84af85a26e5012c5a4`. DM inspected all 22 completion predicates,
actual seed/root/label/LR, rule inputs, eight gap rows, complete native cells, projection/contact
and moment observations, work, admission and original termination. Native-component subtraction
below is read-only arithmetic over existing cells, not another invocation.

CM directly observed original SystemExit(0), complete publisher and later fixed-pdb reentry
before module line 1, followed by q without a second computation. Original completion is
independent of debugger/supervisor exit 0. There was no original exception or deadline exit.
No source, test, runtime or publication change occurred during collection.

## Original rule applied verbatim, in order

| branch | rule and bounded reading |
| --- | --- |
| `R07_INVALID_INCOMPLETE` | Common integrity fails; actual seed/root/label/LR binding differs from this card; fresh actual-node admission is missing or below 4 GiB; nonzero planned learner/update/evaluation work or exposure/curves are missing; information/work/raw initialization pairing fails; actual initial projection disagrees with direct clipping; contact history is misreported; or projection changes optimizer moments. Quarantine, no result. Zero initial clipping itself is valid. |
| `R07_NO_OBSERVED_CONTACT` | Complete valid result has no initial or post-Adam tight coordinate changes. Report all native curves; this literal path did not activate the differing box, so it does not test an activated-projection benefit. Do not infer universal equality. |
| `R07_N15_EDGE_BELOW_UNIFORM` | Complete valid contact-observed result has e128(15) < 0. Report both rosters; the containing comparator is not minimally competent for the primary N15 question, so that arm contrast is nonidentifying. |
| `R07_N15_MATERIAL_TIGHT_FAVORED` | N15 EDGE is at least uniform and d128(15) >= +0.005. Preliminary material N15 tight advantage on this second literal path; report N9 qualifier, no stable/population claim. |
| `R07_N15_MATERIAL_TIGHT_ADVERSE` | N15 EDGE is at least uniform and d128(15) <= -0.005. Material opposite/adverse sign on this literal path; no direction closure. |
| `R07_N15_WITHIN_MEI` | Complete valid contact-observed result reaches none of the preceding rows. N15 is strictly inside (-0.005,+0.005); no material repeat on this path. |

The invalid row is false: all common requirements, complete counts/curves, actual seed-2
binding and actual initial/final LR [0.003] hold. Initial three-coordinate clipping and
later contact are observed. N15 e128 is positive and d128 is strictly within the margin.
The first matching branch is **R07_N15_WITHIN_MEI**. N9's mandatory qualifier is also
within-MEI, with EDGE above uniform. This does not establish equivalence.

| update | N9 d | N15 d | N9 e | N15 e |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | +0.000367088135 | -0.000064296392 |
| 32 | +0.000046856492 | -0.000036818697 | +0.000845594580 | +0.006003285099 |
| 64 | +0.000759873205 | -0.000024536089 | +0.000935304925 | +0.007162071244 |
| 128 | +0.000910016910 | -0.001948094523 | +0.014817785945 | +0.026623984248 |

Exact final d: N9 `0.0009100169098625599`, N15 `-0.0019480945232013894`.
Exact final e: N9 `0.014817785945100088`, N15 `0.026623984247756503`.
All 18 cells and 256 learner/projection rows remain in the original E0 JSON.

## Native consequence and exposure

At N15, PHY/EDGE final J is 0.046723146953930456 / 0.048671241477131845. They make
95 / 98 deliveries over 256 episodes: west 48 / 48, east 47 / 50. Mean minimum basin
deliveries is 0.0078125 / 0.015625. Waste fractions are 0.9412971762940288 /
0.9410219602286816. The d15 components are -0.00126953125 delivery, -0.000651041667
balance and -0.000027521607 waste. The tight arm also has more radio actions (21,323 /
21,120) and collisions (780 / 719). These observations describe native consequences,
not a causal attribution to a particular coordinate.

At N9, PHY/EDGE J is 0.0361931250585864 / 0.03528310814872384, with 69 / 68 deliveries.
The d9 components are +0.000423177083 delivery, +0.000325520833 balance and
+0.000161318993 waste. Both roster gaps are smaller than the predeclared absolute MEI 0.005.

The actual seed is 2, root is the declared 256-bit integer-2 encoding and label is
`FRRIE-B07-CONTACT-BLOCK-002`. Paired raw initialization agrees. Initial direct tight
clipping changes **three** coordinates [3,5,14], raw beta range
[-0.039780594408512115,0.04983894154429436]. The first contact is separately **0**.
The historical exact-five boolean is false, as expected; it is not a R07 validity predicate.

PHY contacts in 127/128 post-Adam updates, with 995 coordinate events over 17 distinct
coordinates; EDGE has no contact. Cumulative tight projection displacement is
0.7565990835428238, maximum overshoot 0.009838942438364029 including initialization.
Initial and every later projection preserve optimizer moments. Contact history agrees
with the independently reconstructed inventory/update history.

Final Linf displacement from raw initialization is PHY 0.2250594049692154 and EDGE
0.2287365198135376, about 4.50 and 4.57 initial half-ranges. L1 displacement is
646.3432006835938 / 651.237548828125. Nominal exposure remains 128 × 0.003 = 0.384,
normalized 7.68; it is not a displacement bound. Actual initial/final group LR is [0.003]
for each arm. No-contact or negligible-motion explanations do not describe this run.

## Counts, receipts and cost

| quantity | retained observation |
| --- | --- |
| source / task | `10ae9781f74ae26931fa8231918844f4921b80f2` / `frrie_b01_contact_r07_10ae9781` |
| node | wsl_4070, CPython 3.10.21, CPU FP32, Torch thread 1, native width 32 |
| start / end | 2026-09-05T10:30:13Z / 10:45:16Z |
| fresh admission | 10:30:13.585327Z, physical/effective each 12,896,010,240 bytes |
| per-arm Adam / backward / updates | 128 / 128 / 128 |
| per-arm factual episodes / transitions / training slots | 8,192 / 98,304 / 630,784 |
| per-arm learned evaluation episodes / slots | 2,048 / 24,576 |
| full evaluation | 18 cells, 4,608 episodes, 55,296 transitions |
| total native slots | 1,316,864 |
| completion | all 22 flags true, 256 ordered learner rows, eight checkpoint-state summaries |
| supervisor / runner wall | 903 / 844.9199158800038 seconds |
| attributed PHY / EDGE wall | 150.0812525627989 / 149.90698258804332 seconds; shared work additional |
| peak RSS | 614,817,792 bytes; `resources_unmeasured` for scratch high-water only |

Observer uptime 906 seconds is not the execution duration. All cells contain 256 episodes,
3,072 transitions and full action/event counts; action sums equal roster × transitions.
Evaluation preserves model bytes and uses common tapes nine times per roster. Both four-hour
per-arm and eight-hour total caps hold. Accepted scope remains 26/88 = 29.545%; the initial
rejected 34/96 = 35.42% candidate remains recorded and was never run.

R05/R06/R07 form a three-valid-B remote window: 2,586.9272801779953 runner seconds,
862.3090933926651 per valid result; 2,735 supervisor seconds, 911.6666666666666 per result.
This is not all-attempt efficiency or a lifetime total; A01, tests, failures and the old
Windows window remain separate. Actual full publication succeeded, while formal-sized
publication-test coverage remains open. Host headroom still lacks tuned/upper references.

Read-only output inventory found only summary JSON in R06/R07 (122,511 / 123,996 bytes).
Their checkpoint entries contain hashes and moment summaries, not reloadable trained model
or optimizer bytes. No offline counterfactual evaluation of those trained states is available
from these artifacts. This is an engineering fact, not result invalidity or scientific polarity.

## Bounded reading and prediction score

The R06 material N15 gap did not reappear on the second prespecified literal path: it changes
from +0.005548293532 to -0.001948094523 under the same nominal LR, work and boxes. Both
paths have active clipping and substantial parameter movement; R07's wide comparator is
well above uniform. This is strongest evidence against assuming that the first-root material
gap is stable across the chosen paths. It is not a sampled-root population test, a confidence
bound, an equivalence claim or evidence that no configuration can help.

R06 remains the strongest supporting observation for a conditional positive package effect.
R07 is its strongest current contradiction to material reappearance, and neither root has a
material N9 benefit. Root-specific initialization, training/evaluation tapes and co-adaptation,
common K0 alignment, generic shrinkage/Adam geometry and roster dependence remain live.
More contact alone is not mechanism value; R07 has more coordinate events without a material
native advantage. Relation specificity, held-out transfer and arbitrary-N behavior remain open.

DM prediction **matches its registered conditional branch**: contact occurs, N15 EDGE is
above uniform and the primary gap is within MEI. Neither material primary-gap falsifier
fires. Confidence was low; this one match is not a validation of the whole explanation.
Owner prediction is `not taken (unattended)`; current reviews and ledger owner columns
contain no override or prediction reply. R06's distinct mixed prediction score is unchanged.

## Decisions this intake produces

### Accept the result and bounded interpretation

Options: (a) accept the original within-MEI primary and N9 qualifier, score the prediction,
and retain the non-reappearance boundary; (b) call two roots equivalent or close the family;
(c) pool R05/R06/R07 as independent seed evidence; (d) invalidate because exact-five is false
or resource scratch telemetry is absent.

Recommendation and selection: **(a)**, object tier, kind `technical`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
There is no B consumption state and no historical failure is reclassified from this success.

### Next discriminator inside the accepted projection/optimizer family

Options: (a) a prospective B conditional cut diagnostic of the known R06 positive path,
holding its root/LR/training fixed and adding final role-prior-column rotation; (b) another
literal root at the same configuration; (c) further LR/box tuning; (d) call unavailable
trained-state replay an offline experiment or reopen the old stopped B01 panel.

Recommendation and selection: **(a)**. The two-path boundary already shows that material
reappearance cannot be assumed. The next direct uncertainty is what the one known signal
depends on. Root 1 is explicitly selected because it supplied that signal. This diagnostic
was chosen after observing the result and cannot establish root robustness or a population effect. Root 2 has no
material positive gap to attenuate. Another root would extend recurrence coverage while
leaving this conditional chart-dependence question unresolved.

The existing `SEMANTIC_COLUMN_ROTATE` changes sender-role columns of the common prior
probability/latency chart and recomputes K0; it does not rotate beta indices or raw entity
observations. Native physics and exogenous tapes remain fixed, while actions and subsequent
states may diverge. It can diagnose conditional package dependence on that chart alignment,
not semantic correctness or learned relation specificity.

Because no trained-state bytes survive, R08 must declare a full new root-1 training plus
endpoint evaluation invocation. It is not offline replay, salvage or a retry of R06.
Historical R06/R07 meanings remain immutable; exact historical endpoint reproduction is
not a new validity guard. See the prospective `FRRIE_R08_ROLE_COLUMN_CUT_SCIENCE_CARD_20260905.md`.

Object tier, kind `selection`, owner flag `close-call`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
The runner-up (b) would extend recurrence coverage without selecting the known positive path;
its benefit is not clearly separated from (a), especially while added evaluation wall time
is unmeasured. I choose the existing cut for its direct chart-dependence question and flag
the choice for asynchronous owner review rather than pretend the tradeoff is settled.
No family, recast, Direction, priority or lifecycle change occurs. CM receives a separate
meaning-complete card before any edit/check/launch.

## Owner surfaces and append-ready audit

The Chinese brief, validity decision, brief item, next-selection decision, new-card and close-call items
are written through the owner CLI. Root appends their rows under
`frrie-r07-intake-r08-selection` in the 2026-09-05 ledger.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T04:13:32-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) accept original within-MEI rule and prediction score; (b) equivalence/family closure; (c) pool nonindependent evidence; (d) invalidate initial3 or scratch absence | (a) VALID B/EXPLORE R07_N15_WITHIN_MEI, N9 within-MEI, conditional prediction matched | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-010.json` | none | |
| 2026-09-05T04:13:33-07:00 | finite_resource_relational_inductive_efficiency | object | technical | reading-agreed; reading-disputed | publish R07 Chinese brief; no owner reading imputed | yes | VALID_RESULT_INTAKE | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-011.json` | none | |
| 2026-09-05T04:13:34-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) conditional common-chart cut of known root1 signal; (b) third literal root; (c) more LR/box tuning; (d) unavailable offline replay or reopen stopped panel | (a) new R08 full training plus four final rotation cells, conditional selected-path ceiling | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-012.json` | close-call | |
| 2026-09-05T04:13:34-07:00 | finite_resource_relational_inductive_efficiency | object | technical | accept; reject; revise | freeze R08 card; accept recommended, no owner choice imputed | yes | CARD_RECORDED | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-013.json` | none | |
| 2026-09-05T04:13:35-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) conditional chart diagnosis; (b) third-root recurrence coverage | (a) recommendation executed with unresolved relative value/cost; asynchronous owner override available | yes | OWNER_DELEGATED — close-call notification of the preceding selection | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-014.json` | close-call | |
