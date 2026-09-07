# SERVICE-ALLOCATION-B01 — scientific intake, 2026-09-07

**Accept a narrow B observation: FACTOR exceeds GENERIC by 0.00651042 on the fixed final
evaluation, below the card's 0.025 minimum effect of interest.** Both period differences are
positive. The rule was never evaluated, so learned-policy usefulness relative to LQ-EXCLUDE
and the complete three-controller assignment remain unresolved. The failed publication is
not a negative learning result. No additional invocation is selected by this intake.

## 1. Evidence checked and applicable rule

Read the complete final [CM E0 technical return](VSPC1_K4_SERVICE_ALLOCATION_B01_EXECUTION_20260907.md)
at `c3c31a83b`, integrated at `66e0e3b4df38a50842ebedde206727e349b11616`.
The integrated execution record is byte-identical to that return. The exact launch source is
`faf786e135b3f55e535c898e17e646dcc341bdec`. Read the saved FACTOR/GENERIC JSON summaries and
CM's derived collection against [card §§4–7](VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md):
arm/seed/source/configuration, real counts, five fixed checkpoints, ordered endpoint rows,
initial norm/final movement, complete-call receipts, rule absence and the failure boundary.
CM's source/AST check and saved budgets support the publication-only classification; DM
did not repeat the experiment, CM tests or a model/environment diagnostic.

The applicable card §5 rule is, verbatim:

> No conclusion on the damaged dependency; preserve trustworthy independent facts and name
> the gap, not a negative experiment. If only the rule is missing, retain a trustworthy Delta
> and leave rule-relative value unresolved; no automatic third call.

Also applied, verbatim:

> Report all, keep the complete fixed endpoint primary; no best checkpoint, seed or metric
> declared the winner.

Evidence-spec §§11.8.2–11.8.7 keep the intact native-return observation reportable without
turning a missing dependent measurement into scientific polarity. The larger-gain branch's
`Delta >=0.025` condition is not met. Its rule-relative conditions cannot be evaluated;
missing rule evidence is not evidence that either learner trails or beats it.

## 2. Native observation and its bounds

J is served jobs divided by 96 over one 48-tick episode. Endpoint is update256, with equal
weight for periods 2 and 6 and 128 paired evaluation episodes per period.

| Measurement | Period 2 | Period 6 | Equal-period mean |
| --- | ---: | ---: | ---: |
| FACTOR final J | 0.753092447917 | 0.764729817708 | 0.758911132812 |
| GENERIC final J | 0.751383463542 | 0.753417968750 | 0.752400716146 |
| FACTOR minus GENERIC | +0.001708984375 | +0.011311848958 | **+0.006510416667** |
| FACTOR full-grid AUC | 0.755727132161 | 0.762715657552 | 0.759221394857 |
| GENERIC full-grid AUC | 0.754018147786 | 0.761698404948 | 0.757858276367 |
| FACTOR final minus initial | +0.006754557292 | +0.014160156250 | +0.010457356771 |
| GENERIC final minus initial | +0.000081380208 | +0.002441406250 | +0.001261393229 |

The primary difference is **0.625 additional served jobs per episode**, 26.04% of the
declared MEI (2.4 jobs). Its conditional paired evaluation SE is **0.002109066044**, computed
from the same indexed episode differences using the card's equal-period formula. This is
evaluation noise for these two fixed policies. There is **one paired training instance**;
neither the 256 final episodes nor the five checkpoints supply training replicates, and no
training-population uncertainty or stable superiority is estimated.

Both period endpoint contrasts favor FACTOR; neither is a material opposite-sign period
loss. Full-grid AUC also favors FACTOR, by only **0.001363118490**. All five points and
256 loss records per learner, each containing both periods, remain retained. GENERIC's period6 value
at update64 is above its final value, and both learners' update192 means exceed their finals;
those transients do not replace the selected endpoint. Initial means were 0.748453776042
and 0.751139322917. The larger FACTOR initial-to-final change is descriptive of this instance,
not an isolated causal effect of multiplicative conditioning or shared representations.

There is no J_R, E_F, E_G, initial-relative-to-rule value or new-host headroom estimate.
The strongest useful support is a real positive native learner contrast in both periods,
with measurable parameter movement and a small positive fixed-curve difference. The
strongest limitation for practical factorization value is the below-MEI size, coupled with
the missing same-information reference. The known non-learning partner, non-bottleneck
factorization, initialization and finite optimization remain alternatives. No transfer,
partner co-adaptation, optimality, equivalence or unique sharing explanation is established.

## 3. Scientific result versus engineering conformance

Both real learners completed 256 Adam updates and all five evaluations. FACTOR exited 0.
GENERIC wrote its complete learner summary, then exited 1 in learner-only paired publication
before the rule call. The two saved budgets are equal and match the frozen values. The
production call compared JSON-loaded FACTOR checkpoint **list** with in-memory GENERIC
checkpoint **tuple**, causing the equality check at reporting.py:69 to reject them.
This observed mixed representation does not change training, information or reward.

The former synthetic publication fixture omitted checkpoints from its budget and round-tripped
both inputs, so its pass did not cover this production boundary. The earlier source intake's
expectation of complete publication is contradicted at this boundary; historical acceptance
and tests remain recorded, but future use of this path requires the focused repair. No source
change or replay has been used to relabel the failed GENERIC invocation as complete.

Native learner endpoints were preserved independently of the failed comparison file. The
post-collection readout below uses their frozen metric and indices. It is not a replacement
for the absent runner paired publication and does not complete the missing rule dependency.
The status `complete` inside each summary describes its learner work, not the full assignment.

## 4. Exposure, receipts and analysis

| Quantity | Each learner | Actual total |
| --- | ---: | ---: |
| Training episodes / joint ticks | 4,096 / 196,608 | 8,192 / 393,216 |
| TD rows / nonterminal rows | 65,536 / 61,440 | 131,072 / 122,880 |
| Optimizer steps / target copies | 256 / 17 | 512 / 34 |
| Learner evaluation episodes / ticks | 1,280 / 61,440 | 2,560 / 122,880 |
| All joint ticks / scalar Q predictions | 258,048 / 569,344 | 516,096 / 1,138,688 |
| Selection steps | 0 | 0 |
| Rule episodes / ticks | — | **0 / 0** |

The unperformed rule work is 256 episodes / 12,288 ticks. FACTOR initial norm and final
displacement are 4.7401924 and 2.1032240; GENERIC values are 4.2803783 and 1.0033300.
This confirms a real can-move path without imposing a displacement-ratio threshold.

Both calls ran once on `wsl_4070`, CPU float32, one compute thread and batch16, with adjacent
same-node memory admission. FACTOR physical/effective available memory was 15,665,508,352
bytes and GENERIC's was 15,667,646,464, both above 4 GiB. Complete walls were **6.52 s** and
**4.84 s**, below the independent 2,700 s caps. Summed invocation wall is **11.36 s** and
aggregate CPU **8.58 s**. About 138 s from first acceptance to final terminal log includes
inter-call collection/commit time and is not summed machine time. Earlier staging and later
intake are outside that elapsed interval. No further scientific call occurred.

FACTOR peak RSS was 478,146,560 bytes. GENERIC did not reach final RSS metadata; scratch is
unmeasured for both. These resource portions are `resources_unmeasured`; no resource claim
or resource-based annulment is made. Scope §4 additions: none. Runtime execution changed no
source and introduced no section 5 line-budget breach. Both exact handles are terminal and
Root acknowledged their observation; no experiment remains live.

DM used the scientific-tools run summarizer on one endpoint per arm with declared pairing:
`summarize_runs.py endpoint_runs.csv --paired --baseline GENERIC`, plus short stdlib arithmetic
over preserved endpoint arrays and all five curve points. The
[run-level summary](VSPC1_K4_SERVICE_ALLOCATION_B01_RUN_SUMMARY_20260907.json) correctly reports
n=1 and no sample SD. The [derived analysis](VSPC1_K4_SERVICE_ALLOCATION_B01_ANALYSIS_20260907.json)
retains formulas' outputs, fixed curves, actual totals, native consequences and source paths.
DM analysis performed zero model, environment, RNG, optimizer or rule calls. No values or
curves were selected after looking at outcomes; complete production publication remains failed.

Raw summaries, receipts, losses, indexed endpoints and supervisor logs remain at the remote
cwd and CM collection root named in the E0 record. The local collection root is
`C:/Projects/HMASD-worktrees/cm-vspc1-service-allocation-exec402-20260907/temp/directions/vsp_c1/exp/k4_service_allocation_b01_seed402_20260907/`.
No raw artifact was overwritten. The ended zero-exposure staging probe has its separate
[technical intake](VSPC1_K4_SERVICE_ALLOCATION_B01_STAGING_INTAKE_20260907.md).

## 5. Prediction and decisions this intake produces

DM prediction `J_R >= min(J_F,J_G)` is **not scoreable** because J_R is missing; record
neither a hit nor a miss. Owner prediction is **not taken (unattended)**. Current owner
reviews returned `[]`; no unapplied override was found. The
[Chinese owner brief](../../portfolio/owner/briefs/vsp_c1/2026-09-07_SERVICE-ALLOCATION-B01.md)
reports the valid narrower observation and missing dependency.

Options: (a) accept the trustworthy learner contrast at its narrow ceiling, preserve the
missing rule/publication dependency and return the concrete gap to Portfolio through Root;
(b) discard the intact learner data because the process failed; (c) execute an unselected
repair, rule call or fresh training to obtain a complete comparison.

Recommendation and executed choice: **(a)**. **Owner-delegated decision (unattended,
2026-09-03 instruction): (a).** Object tier, technical; reversible yes; owner flag none.
The [audit ledger](../../portfolio/audit/2026-09-07.md) records this intake. There is no new
card, direction disposition, recast, close call or material critic dissent, so no separate
P1/P2 owner item. B has no consumption state; the complete three-controller assignment is
incomplete and cannot be called a complete successful B result. The valid narrower native
observation remains part of this direction's evidence.

## 6. Next discriminator and return

The result does not provide the declared MEI-sized FACTOR-over-GENERIC reason for a new
seed expansion. The smallest remaining measurement for the original usefulness question is
the **already-declared 256-episode LQ-EXCLUDE endpoint on the same tapes**, followed by all
three comparisons against the saved learner endpoints. If Portfolio commissions completion,
repair the loaded/in-memory serialization boundary and cover that exact path; repeating the
learners would not answer the missing-reference question more directly. This is a bounded
next-command recommendation, not a new invocation, budget, card or authorization.

Current Root/Portfolio instruction selects no new execution. Return this intake and the
concrete remaining gap to Portfolio. K4 and the accepted reactive family remain open;
historical two-queue B01 and the ended public-plan family retain their boundaries. There is
no local Portfolio action, new host search or stronger-class prerequisite.
