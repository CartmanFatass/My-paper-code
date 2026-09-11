# UCOPE native-return acquisition B01 — scientific intake

**Valid complete B/EXPLORE result: NR-B, `Delta_bar = 0`.** Both independently trained final
modal policies choose IMMEDIATE-4 in all eight contexts. This learner at the frozen budget did
not produce useful acquisition or a native-return improvement over the immediate null. The
outcome prediction matches; no additional invocation is selected by this intake.

## 1. What was checked

DM read the complete [result evidence](UCOPE_NATIVE_RETURN_ACQUISITION_B01_RESULT_EVIDENCE_20260907.md)
at CM commit `d234f7648`, integrated on Root main as `fba696098`, against frozen
[card §§1–5](UCOPE_NATIVE_RETURN_ACQUISITION_B01_SCIENCE_CARD_20260907.md), card commit
`3520ccd2ce90e8aca3c7bec8e838e403d00068db`. The formal assignment is
[technical intake §6](UCOPE_NATIVE_RETURN_ACQUISITION_B01_TECHNICAL_INTAKE_20260907.md#6-formal-execution-assignment--prepared-not-dispatched),
integrated `98c43eca05f5d0b09cb673a5de3a894abc8985a5` and subsequently dispatched by Root.
The recorded launch/source SHA is `a0b00f561159ddeedf66b65711cf3f7d2ec93b04` for both seeds.
The source surface matches intake base `e476f2d2bbf639e41f13a4a195ac5dde8bca74a9`.

DM directly read both original summaries: science profile, COMPLETE status, selected seeds,
all eight complete context rows with 4,096 pairs each, primary differences/conditional SE,
modal actions, counts and parameter movement. Both destination admission receipts, external
process-time files and collected terminal status files were read and agree with CM's evidence.
CM's final-state and ordered-training-log readback is accepted without repeating it. Its focused
information/reward/RNG/gradient review remains applicable because source and argv did not change.
No missing primary or learner-exposure dependency was found under evidence spec §4, §5.2,
§11.4 and §11.8.5–7. No historical replay or new experiment was needed for this intake.

Raw files remain at `temp/directions/ucope/exp/native-return-b01-seed6301/` and
`native-return-b01-seed6302/` under remote exact-source worktree
`/home/wu/hmasd-worktrees/cm-ucope-native-return-b01-20260907`, with CM's collected copies under
`C:/Projects/HMASD-worktrees/cm-ucope-native-return-b01-20260907/`. The result evidence names
all summaries, final states, training logs, receipts and supervisor artifacts. Raw summaries'
`batch_branch: INCOMPLETE` is an intentional per-process placeholder; the actual per-seed
`status` fields are COMPLETE. DM applies the two-seed function without rewriting those bytes.

## 2. Rule applied verbatim, independent unit and endpoint

Card §4: "For a complete two-seed result, apply the first matching branch:"

| Branch | Reading rule | Bounded interpretation |
| --- | --- | --- |
| `NR-A` | `Delta_bar > 0.001` | Mean improvement above the MEI; retain adverse seeds/contexts and recommend a separately bounded independent-seed follow-up of this comparison |
| `NR-B` | `-0.001 <= Delta_bar <= 0.001` | No material mean signal at this budget; any seed-specific gain remains local and selects no automatic extra invocation |
| `NR-C` | `Delta_bar < -0.001` | Native mean loss; recommend no unchanged extension of this learner |

Python called the accepted `evaluation.reading_rule` on the two complete original summaries:
`{"branch": "NR-B", "delta_bar": 0.0}`. Both context-mean recalculations also equal zero.
The independent learning unit is **one fresh training seed**, giving **n = 2**. The score is
each seed's already aggregated, uniform-context native-return difference. Evaluation pairing
is fixed by card §3; the fixed IMMEDIATE-4 reference is not another trained replicate.

| Seed | Actor mean native return | IMMEDIATE-4 mean | Delta_s | Conditional MC SE | Final modal roots |
| --- | ---: | ---: | ---: | ---: | --- |
| 6301 | 0.79122900390625 | 0.79122900390625 | 0 | 0 | all 8 IMMEDIATE-4 |
| 6302 | 0.791259521484375 | 0.791259521484375 | 0 | 0 | all 8 IMMEDIATE-4 |

All sixteen seed/context differences are zero, and neither evaluation policy probes. Therefore
the aggregate is not cancellation between local gains and native losses. Conditional MC SE zero
is consistent with identical final action paths under the declared paired host randomness; it
does not say that native returns are noiseless or that training-population uncertainty is zero.
Two zero run differences give descriptive sample SD zero, not a stable equivalence claim.

DM also used the scientific-tools run summarizer with one `Delta_s` row per training seed,
without treating episodes/contexts as runs and without adding a second pairing operation:

```text
python .agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py temp/directions/ucope/exp/native-return-b01-intake/scores.csv --out temp/directions/ucope/exp/native-return-b01-intake/run_summary.json
```

Output: n=2, mean=0, sample SD=0, min=max=0. The input, `reading_rule.json` and descriptive output
are retained under that directory in the DM worktree. Intake analysis created **zero episodes,
optimizer steps or evaluations**. No seed, context, checkpoint or adverse outcome was excluded.

## 3. Exposure, receipts, cost and conformance

| Seed | Training episodes / probes | Evaluation episodes | Total host-event transitions | Joint steps / tail-active batches | Whole-process wall s / peak RSS KiB |
| --- | --- | ---: | ---: | --- | --- |
| 6301 | 262,144 / 62,521 | 65,536 | 1,030,486 | 1,024 / 1,024 | 8.80 / 510,200 |
| 6302 | 262,144 / 63,721 | 65,536 | 1,037,686 | 1,024 / 1,024 | 9.67 / 506,720 |

Python totals: **655,360 episodes, 2,068,172 host-event transitions, 2,048 joint optimizer steps,
126,242 probes, 2,638,802 committed period units and 252,484 probe time units**. The two formal
training probe fractions are 0.2384986877 and 0.2430763245. Every training batch was tail-active;
literal absence of probe/learner exposure is not an explanation of this result. The separate
technical seed 9006301 remains excluded from this formal population and its counts.

The machine-generated movement lines are present: root displacement L2 4.46557664871 and
4.32141971588 from zero initialization; tail displacement/initial L2 0.67262218153 and
0.88208824277. The full initial/displacement/max-movement table is retained in result evidence.
Nonzero movement supplies exposure evidence, not a competence or benefit judgment.

Fresh remote receipts passed at 2026-09-07T07:47:47.878406Z and 07:48:45.967189Z, with physical
and effective availability respectively 15,670,321,152 and 15,664,181,248 bytes (4 GiB floor).
Both `ucope-native-return-b01-seed<seed>` handles are finished, exit 0, tmux inactive. The
CPU FP32 / one-process / one Torch intra/inter-op thread topology and accepted source remained.
No timeout, retry, resume, tuning, repeated evaluation or extra seed occurred.

Summed complete invocation wall is **18.47 s**, within each 600 s cap and 1,200 s summed cap;
the reported supervisor study elapsed is 68 s including the collection/dispatch gap. Formal
aggregate CPU work is unmeasured and is not inferred from wall. External time covers imports
through final publication/exit. Raw summaries retain `resources_unmeasured` because they do
not ingest external RSS; the measured external wall/RSS remain valid facts. No dependent resource
claim is made. The earlier 53.394 s per-seed projection remains a prospective estimate, not
rewritten from the observed 8.80/9.67 s. No further profiling or cause-of-speed claim follows.

ENGINEERING_SCOPE_SPEC §4: **needs none**, as frozen. Execution/intake added no source or
machinery. Existing implementation acceptance records 295 non-test lines including the
111-line runner, within §5 budgets; this result records **no budget breach**. Scientific validity
rests on the complete native-return comparison, separately from that engineering conformance.

## 4. Prediction and scientific interpretation

Prospective DM prediction was **NR-B, with at least one final policy immediate in all eight
contexts**. Score: **matched** for both components; two of two final policies are all-immediate.
The suggested explanation that costly early probes might suppress useful tail learning remains
unproven. All training batches had some tail exposure, and endpoint identity does not identify
whether credit quality, exposure allocation, finite budget or modal evaluation is decisive.
Owner prediction: **not taken (unattended)**; no prediction reply was present at intake.

Native path: the coordinator owns the public-context root decision; a paid probe exposes only
the displayed count before duration choice, with actual-mark reward arriving afterward. The
joint learner did visit and update this path during training. At the frozen final modal endpoint
both root policies choose immediate, so the acquired-information/tail-action path contributes no
native gain. Learned tail parameters or unused tail outputs cannot be reported as acquisition value.

The bounded conclusion is that this specific sampled-return actor, optimizer, 1,024-update budget
and modal evaluation failed to show improvement on these two training seeds. It does not establish
that paid information is useless, that all direct-return learners fail, that larger budgets help,
or that stochastic-policy evaluation would improve. This finite systems/information-flow host
does not instantiate multi-agent partial observability/non-stationarity; no MARL population claim
or stable-performance/transfer claim follows. A/B objects have no consumption state.

Strongest support for the present null reading is the complete paired native endpoint and identical
immediate actions in every context, despite real training and movement. Strongest contrary evidence
to a broader paid-information rejection remains historical PA-B (5/6 versus 6/6) and TW-B tail
coverage (6/6 versus 4/6). TW-B's full competence remains 3/6 in both arms, with two false probes
losing 0.028562899 each. All earlier positives, contradictions and quarantines remain intact.
The prior oracle/reference headroom diagnostic 0.00267963765625 and MEI 0.001 are unchanged;
there is still no tuned generic current-host headroom record. No new literature or mechanism
recast is needed to read this predicted endpoint; the card's verified retrieval remains background.

## 5. Decisions this intake produces

1. **Result classification, object tier / technical.** Options: (a) accept the complete batch
   and record NR-B; (b) limit a dependent claim if a concrete missing primary requirement is
   found. Recommendation and selection: **(a)**, from the complete counts and exact frozen rule.
   Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
2. **Next invocation, object tier / selection.** Options: (a) finish this selected measurement
   with no additional invocation now; (b) prepare a separately justified, outcome-informed B
   change; (c) seek an unchanged additional seed. Recommendation and selection: **(a)** for this
   bounded intake. There is no above-MEI or local acquisition gain and no new scientific question
   or exposure assignment in the present request. This is not a universal positive-result gate:
   evidence spec §11.8.2 permits a specifically justified new B after a null. No family is closed
   or parked, and the direction's standing continuation is not revoked.
   Owner-delegated decision (unattended, 2026-09-03 instruction): (a).

Owner flags: **none**; this is not a close threshold call or overruled critic dissent. Reviews
returned `[]`, audit owner cells were empty, and no owner takeover or prediction reply applies.
The classification and brief commands returned `skipped P4`, and the selection command returned
`skipped P3`, under item.py's current P1/P2-only policy; no inbox item was created. Existing frozen
card item `20260907-ucope-001` is unchanged. The [Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-07_native-return-b01.md)
and [audit](../../portfolio/audit/2026-09-07.md) retain the result and executed choices.

## 6. Clean boundary and next discriminator

No further discriminator is frozen or launched. A future selected B needs a specifically
justified learning question and a test of useful paid acquisition in native return
against this competent immediate null. It need not first diagnose the historical root residual;
causal explanation, extra seeds and a larger budget are not conclusions of the present result.
Root receives this completed scientific intake and the new evidence delta for Portfolio's
separate queue judgment. The retained-policy/numerical-locus family remains parked under its
existing direction-tier decision; lifecycle, priority, recast count and all historical boundaries
are unchanged. Both formal processes are terminal and the repository records the complete state.
