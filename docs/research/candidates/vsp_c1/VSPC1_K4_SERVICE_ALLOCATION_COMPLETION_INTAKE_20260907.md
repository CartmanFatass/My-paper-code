# Service-allocation B01: completed rule comparison, 2026-09-07

The outcome-informed amended comparison is complete. LQ-EXCLUDE scored above both saved
learners in each period mean. FACTOR minus GENERIC remains +0.006510417, below MEI 0.025;
this is a small learner-ranking gain with no useful learner-over-rule signal. Apply the
card's object-boundary stop. K4 and the reactive family remain open; this is no family
closure, B consumption, recast, stable-superiority claim or Portfolio disposition.

## 1. What was checked and which authority applies

Read the CM's complete [E0 return](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_EXECUTION_20260907.md#e0-technical-return-outcome-informed-completion-succeeded),
the collected admission/terminal/resource records, publication checks and saved endpoint
arrays against the [frozen card §§1,4–7](VSPC1_K4_SERVICE_ALLOCATION_B01_SCIENCE_CARD_20260907.md)
and the [accepted amendment](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_AMENDMENT_INTAKE_20260907.md).
The complete amendment response at immutable commit
`99151a4a0f2da264a2c13695591a56867e1add3c` permits this one 120-second rule-only completion;
it does not authorize retraining, new tapes or another invocation. Evidence-spec §§4,
5.2,11.4,11.8–11.9 control integrity, B interpretation and proportional checking.

Root integrated CM E0 commit `f0a04ac91f0b82d004302c5754a2263af349c326` at
`016a091dd4bb880a277b3d079c9738b0c7cc2556`; the execution record's bytes agree. DM accepted
the scoped source diff, sole pure-publication fixture and independent read-only review
in the [technical acceptance](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_TECHNICAL_ACCEPTANCE_20260907.md).
DM did not repeat CM's tests, learner execution, rule evaluation or collection commands.

For scientific intake, DM read the saved arrays only and computed every paired endpoint
contrast and conditional SE from the 128 aligned episode rows in each period. Arithmetic
agrees with publication at ordinary numeric tolerance (relative 1e-8, absolute 1e-9).
The [analysis record](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_ANALYSIS_20260907.json)
retains all means, contrasts, consequences, five-point curves, AUC and actual work totals.
The scientific-tools `summarize_runs.py --paired --baseline LQ-EXCLUDE` output is retained
as the [run summary](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_RUN_SUMMARY_20260907.json).
Its single seed402 row is the original paired training instance; LQ-EXCLUDE is a fixed
reference evaluated on its tapes, not another independent training run. No population
CI or success classification was calculated. The independently summed rule J differs
from the published 0.7851969401041667 by about 1e-16 through ordinary summation rounding.

The [original learner-only intake](VSPC1_K4_SERVICE_ALLOCATION_B01_INTAKE_20260907.md)
remains correct at its historical boundary: GENERIC exited 1 during publication before
the rule ran. Its trustworthy learner endpoints survive. This new accepted completion
repairs the missing comparison under the explicit amendment; it does not relabel the
failed original call as successful or erase the original narrower result.

## 2. Counts, receipts and engineering conformance

Exact completion source: `ec8866b3968fcb1566976ce405d7c552d4d9a5de`.
Original learner source: `faf786e135b3f55e535c898e17e646dcc341bdec`.
Remote node `wsl_4070`, CPU float32 and one compute thread, configured Python with
NumPy 1.26.3; original FACTOR/GENERIC summaries were read in place without modification.
The [execution binding and E0](VSPC1_K4_SERVICE_ALLOCATION_COMPLETION_EXECUTION_20260907.md)
record the full argv, source, detached cwd, original input paths and supervisor receipts.

The sole completion handle `vspc1-service-allocation-b01-completion402-20260907` was
accepted at 2026-09-07T18:36:40.585409Z, PID 2743851, and terminal at 18:36:41Z with exit 0
and inactive tmux. It completed before adoption ACK; CM sent the terminal facts directly
to Root. The immediately adjacent node-local admission at 18:36:40.629822Z measured both
physical and effective available memory as 15,639,351,296 bytes, above 4 GiB.

| Work quantity | Original two learner calls | New rule completion | Amended actual total |
| --- | ---: | ---: | ---: |
| Paired independent training instances | 1 | 0 | 1 |
| Training episodes / joint ticks | 8,192 / 393,216 | 0 / 0 | 8,192 / 393,216 |
| Adam updates / TD rows | 512 / 131,072 | 0 / 0 | 512 / 131,072 |
| Evaluation episodes / joint ticks | 2,560 / 122,880 | 256 / 12,288 | 2,816 / 135,168 |
| All joint ticks | 516,096 | 12,288 | 528,384 |
| Scalar Q predictions | 1,138,688 | 0 | 1,138,688 |
| Result-bearing invocations | 2 | 1 | 3 |

The rule made 4,096 focal renewal decisions, with zero model construction, trainable
parameters, optimizer updates, learner evaluation or nested candidates. Its 16,384 partner
choices are inferred from the fixed execution path (12,288 tick choices plus 4,096 renewal
choices), not a separate instrumented measurement. Original nonterminal TD rows remain
122,880. Shared exogenous tapes do not force common endogenous queue trajectories.

Whole completion wall was 1.37 seconds; user 0.82 plus system 0.25 = 1.07 aggregate CPU
seconds, inside the 120-second cap. Peak RSS was 347,971,584 bytes. Runner-internal wall
1.132487788 seconds covers a narrower scope and does not replace the complete timer.
Across the three calls, summed complete invocation wall is 12.73 seconds and aggregate
CPU is 9.65 seconds. These are not study elapsed time or total control-plane/engineering
cost. Scratch remains unmeasured; original GENERIC peak RSS remains unmeasured. These
optional resource gaps do not damage the primary result (`resources_unmeasured`).

Engineering scope §4 additions: **none**. The accepted repair has 75 non-test changed
lines (74 additions, 1 deletion), including the 69-line entry, within the amendment's
150-line total and 100-line entry bounds. The sole three-case pure-publication fixture
completed in 6.9159413 seconds, within 300 seconds, without model/environment/RNG work.
Independent review found no remaining material issue. No §5 budget breach is recorded;
the original publication defect and failed call remain explicit. There was no extra
fixture, admission, experiment retry or scientific execution during this intake.

## 3. Primary result and native consequence

| Controller at final endpoint | Period 2 J | Period 6 J | Equal-period J |
| --- | ---: | ---: | ---: |
| FACTOR | 0.753092448 | 0.764729818 | 0.758911133 |
| GENERIC | 0.751383464 | 0.753417969 | 0.752400716 |
| LQ-EXCLUDE | 0.790201823 | 0.780192057 | 0.785196940 |

| Paired contrast | Period 2 | Period 6 | Mean | Conditional evaluation SE | Served jobs per episode |
| --- | ---: | ---: | ---: | ---: | ---: |
| FACTOR − GENERIC | +0.001708984 | +0.011311849 | +0.006510417 | 0.002109066 | +0.6250000 |
| FACTOR − rule | −0.037109375 | −0.015462240 | −0.026285807 | 0.001805490 | −2.5234375 |
| GENERIC − rule | −0.038818359 | −0.026774089 | −0.032796224 | 0.002076850 | −3.1484375 |

SE = 0.5 sqrt(s2²/128 + s6²/128), using sample variances of within-period paired episode
differences. It concerns evaluation noise conditional on these fixed policies only.
The three contrasts share data and satisfy E_F − E_G = Delta; they are not three
independent replications. The rule leads both period means, not necessarily every episode.

MEI 0.025 is 2.4 jobs per 48-tick episode. FACTOR's small learner gain is inside it.
Its mean loss to the rule nominally exceeds MEI by only 0.001285807, smaller than that
contrast's conditional SE. Do not claim a resolved MEI-sized rule advantage over FACTOR.
The negative learner-minus-rule signs and below-MEI FACTOR-minus-GENERIC contrast suffice
for the card's no-useful-continuation reading without settling that stronger boundary.
FACTOR's rule-relative period2 loss and GENERIC's losses in both periods cross −0.025;
neither learner-relative period loss does. Every period is retained.

| Native consequence, equal-period mean | FACTOR | GENERIC | Rule |
| --- | ---: | ---: | ---: |
| Completed jobs | 72.85546875 | 72.23046875 | 75.37890625 |
| Overflow jobs | 0.75390625 | 1.22656250 | 0.00781250 |
| Final backlog | 4.51171875 | 4.66406250 | 2.73437500 |
| Unused service | 23.14453125 | 23.76953125 | 20.62109375 |

The action path is concrete: two persistent workers observe the renewal state; the focal
worker chooses a queue and holds it for period2 or period6 while the known non-learning
partner continues responding. The legal rule avoids the partner's immediate allocation
and serves the longest remaining queue from the same available information. Own queue
trajectories then determine native service, overflow and backlog. The observed rule
advantage is a controller consequence on this host, not evidence of optimality.

All five learner checkpoints remain. Full-grid AUC is FACTOR 0.759221395 versus GENERIC
0.757858276 (difference +0.001363118). Initial J values are 0.748453776 and 0.751139323;
initial-to-final changes are +0.010457357 and +0.001261393. Initial-minus-final-rule
comparisons are −0.036743164 and −0.034057617. There is no initial/intermediate rule
evaluation or rule AUC. These secondary observations do not replace the fixed endpoint
or uniquely attribute a difference to learning rather than initialization/optimization.

## 4. Rule applied verbatim, prediction and bounded interpretation

Frozen card §5 observation:

> Delta inside MEI with no useful learner-over-rule signal, or evaluation uncertainty leaves the relevant boundary unresolved

Frozen card §5 reading:

> No practical continuation reason from this object; preserve sign and uncertainty and stop at this object boundary. No automatic extension, extra evaluation or search for another similar host; no equivalence or optimality claim.

This row applies to the complete amended comparison. The amendment's first completed-result
branch is consistent with it. The runner's `no_practical_continuation_reason` string is
publication output; the DM applies the card's rule to the actual observations above.

The recorded prediction J_R >= min(J_F,J_G) is **matched**: 0.785196940 exceeds both
0.758911133 and 0.752400716. Owner prediction: **not taken (unattended)**. The earlier
unscoreable entry remains historical; the newly measured rule now scores the prediction.

Strongest support for multiplicative conditioning is the small positive FACTOR-minus-GENERIC
native contrast after 256 real updates in each learner and in both period means. Strongest
contradiction to its practical usefulness here is that both learned policies trail the
legal same-information rule, with fewer completed jobs and more overflow/backlog.
The simpler rule may perform most useful control on this stationary known-partner host.
Both networks share features, and initialization, finite optimization and common training
remain alternatives; this experiment does not isolate a unique value-sharing mechanism.

Claim ceiling: descriptive B evidence from one paired training instance, with an explicitly
outcome-informed rule completion. No training-population uncertainty, stable superiority,
causal sharing, transfer, partner co-adaptation, equivalence or optimality follows. The
host's tuned baseline/upper-reference headroom record is still **absent**: the observed
untuned rule is an attained comparator, not an upper bound or tuned baseline certificate.

## 5. Decisions this intake produces

| Option | Recommendation and disposition |
| --- | --- |
| (a) Accept the complete amended comparison, retain the rule reference and stop this B01 at its object boundary | **Recommended and selected.** Preserve every outcome and return the completed intake through Root to Portfolio. No further call is selected. |
| (b) Add learner seeds, more evaluation or another similar host | Not selected: the card gives no practical continuation reason here, and the current completion assignment provides no such invocation. |
| (c) Discard intact learner/rule evidence because the original GENERIC publication failed | Not selected: the defect's historical dependency limit is retained; the explicitly authorized fresh completion supplies the missing comparison without erasing that failure. |

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Tier: object;
reversible selection; owner flag: none. This is not a close call about extending B01:
uncertainty at the stronger rule-minus-FACTOR MEI boundary does not supply learned usefulness.
No new direction decision or Pro request is formed. K4 and the reactive family stay open;
the old public-plan family remains ended, historical two-queue/A01 boundaries stand,
and no recast or Portfolio priority/lifecycle change follows. B has no consumption state.

Owner review/intake checks found no relevant unapplied override or prediction reply; the
2026-09-07 review file is absent and existing relevant ledger owner cells are empty.
Record this ordinary object selection in the [audit ledger](../../portfolio/audit/2026-09-07.md).
No separate P1/P2 item is needed for this valid-result brief and ordinary object decision.
The [Chinese owner brief](../../portfolio/owner/briefs/vsp_c1/2026-09-07_SERVICE-ALLOCATION-B01-COMPLETION.md)
is separate from the preserved original learner-only brief.

The selected missing discriminator—whether either saved learner beats the fixed rule on
the original tapes—is now resolved at this limited B ceiling. No next measurement is
selected here. Root integrates this result; Portfolio owns the next bounded assignment.

## 6. Evidence and handoff boundary

Collected raw completion files are under
`temp/directions/vsp_c1/exp/k4_service_allocation_b01_completion402_20260907/` in the
designated `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906` checkout and the exact remote
worktree named in E0: `summary.json`, `paired_summary.json`, `resource_admission.json`,
`supervisor.log` and `collection_checks.json`. Original learner roots remain preserved.
All handles are terminal. No extra run, retry, new seed, metric selection or source
change is pending. Durable scientific evidence is this intake, its two analysis JSONs,
the E0/technical records, the owner brief and the accepted-science DIRECTION addition.
