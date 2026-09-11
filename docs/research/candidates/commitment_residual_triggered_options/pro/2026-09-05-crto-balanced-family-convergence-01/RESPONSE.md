REQUEST_ID=2026-09-05-crto-balanced-family-convergence-01
PINNED_REFERENCE=4d1572b9282af887e238ad1c7e3d0af45d72d027

DECISION_FORMED
**PRO_FINAL=PARK_CURRENT_SELECTED_PANEL_BALANCED_RESIDUAL_FAMILY**

## SMALLEST_SUPPORTED_CONCLUSION

**Reversibly park this selected-panel balanced residual family. Retain the direction’s finite-budget inductive-bias question, but select no additional learner run at this node.**

The evidence supports one competent-comparator negative: **B04 seed 0’s aligned residual intervention is materially worse than RAW at both declared endpoints.** The two subsequent joint seeds do not extend that negative because their RAW comparators fail the unchanged exact-action competence qualifier. B06 and B07 reject two particular comparator repairs, while preserving actual native learning and action sensitivity. They establish neither residual-family failure nor general RAW unlearnability. These distinctions are explicit in the current `DIRECTION.md` sections “Residual complete-cycle endpoints B04,” “Joint-seed B05 result,” “RAW exposure B06,” and “RAW centered loss B07.”

My selection is an **investment judgment about the next step in this family**, not a finding that another useful B experiment is impossible. The outstanding explanations remain plausible, but the evidence does not sufficiently prioritize one further generic learner modification as a discriminator of residual native value. A new intervention that merely changes predictions, parameter movement, or an exact-action count is not yet a reason to resume this residual family.

### CLAIM_CEILING

**B/EXPLORE only:** adaptive finite-budget inductive-bias and comparator diagnostics on the explicitly outcome-informed 64 selected members: 48 TRAIN and 16 repeatedly exposed EVAL rows, with eight KEEP and eight REPLAN EVAL members, fixed four-agent K8/elapsed-4/cost-4 histories, and the recorded joint seed packages.

There is no stable superiority or equivalence conclusion; no independent confirmation, natural-prevalence estimate, information or function-class gain, full-policy value, variable-K/N result, general MARL result, transfer, safety, theorem, or resource-efficiency claim. This is the scope of B01 §§1–5 and the later accepted intakes.

All repository citations below refer to the pinned reference above. Exact paths actually read are recorded under **READ_PATHS**; section names identify the relevant source passages.

## EVIDENCE_FOR

### 1. B04 is a material adverse result, not merely an absent positive

In the B04 intake, “Direct observation and rule applied verbatim,” RAW at update 258 satisfies both competence conditions on both sides: KEEP 6/8, REPLAN 6/8, with equal-side regret \(0.0037814300857039115\).

| Endpoint |            RAW regret | TRUE_RESIDUAL regret | RAW-minus-TRUE regret |
| -------- | --------------------: | -------------------: | --------------------: |
| SHORT 33 |  0.006581880989529963 | 0.018114012084314506 | −0.011532131094784542 |
| LONG 258 | 0.0037814300857039115 | 0.010915533713999911 |    −0.007134103628296 |

Both adverse differences exceed the residual MEI of 0.0025 in magnitude. TRUE also loses to DERANGED by more than the MEI at SHORT; their LONG difference is within the MEI. DERANGED itself does not improve on RAW. The supported reading is therefore **BR-D—NO_TRUE_GAIN for this seed/exposure/representation intervention**, not equivalence and not a residual-family theorem.

### 2. The earlier diagnostics explain the endpoint choice, not independent confirmation

The current `DIRECTION.md` records that A03 found competence at phase-0 updates, B02’s three-score mean stabilized the action vector without achieving competence, and B03’s paired TRAIN order remained REPLAN-incompetent while canonical order was competent. Those observations supported returning to canonical order and complete-cycle endpoints for B04. They did not isolate cyclic order as the cause or create independent residual evidence. The subsequent endpoint comparison remains development-informed.

### 3. B05–B07 preserve a competence problem distinct from mean native regret

The recorded later endpoints are:

| Reading               | Seed | KEEP exact | REPLAN exact |     Equal-side regret | Competent? |
| --------------------- | ---: | ---------: | -----------: | --------------------: | ---------- |
| B05 RAW, 258          |    1 |        8/8 |          5/8 | 0.0021294544930598857 | No         |
| B05 RAW, 258          |    2 |        6/8 |          5/8 |  0.004055601013485903 | No         |
| B06 RAW, 516          |    1 |        8/8 |          5/8 | 0.0021294544930598857 | No         |
| B06 RAW, 516          |    2 |        7/8 |          5/8 |  0.003127712855602898 | No         |
| B07 centered RAW, 516 |    1 |        8/8 |          5/8 |  0.002127840061573334 | No         |
| B07 centered RAW, 516 |    2 |        7/8 |          5/8 |  0.003127712855602898 | No         |

**All side-mean regret limits pass in these rows. REPLAN exact count alone fails.** The completed rule cannot be relaxed because only one additional correct action is needed. Conversely, failing that rule must not be described as generally poor native performance: seed 1’s aggregate regret is below competent seed 0’s B04 aggregate regret. The competence predicate is not a total ordering of native value. Sources: B05 “Direct observations,” B06 “Direct observation and rule,” and B07 intake “Observation and rule applied.”

B05’s residual signs remain visible, including seed 1’s positive SHORT difference of \(0.00280321561048486\). That observation neither identifies alignment—DERANGED is better than TRUE there—nor supplies competent-comparator polarity. Neither new seed is a competent residual replication.

### 4. B06 and B07 supply precise, limited intervention negatives

B06’s additional exposure leaves both REPLAN action vectors unchanged. Seed 2 nevertheless corrects one KEEP action, producing native gain

$$
0.014846210526128084/16
=0.0009278881578830053,
$$

above the diagnostic MEI \(0.000625\). This is real native improvement, but not the missing REPLAN competence. Rejecting the doubling as a competence repair does not erase that gain.

B07 changes two seed-1 REPLAN decisions. Correcting KEEP to TRANSIT-R gains \(0.011387685355538746\); changing a correct RELAY-L to TRANSIT-R loses \(0.011361854451753917\). Their nearly cancelling contributions produce the recorded mean gain \(0.0000016144314865518261\). Seed 2 changes no action. Thus the intervention reaches native decisions, but fails to deliver the predicted competence-plus-material-gain outcome. Source: B07 intake, “Observation and rule applied” and “Prediction, support, contradiction and ceiling.”

## STRONGEST_CONTRADICTION

The strongest contradiction to an aggressive stopping conclusion is that **the learners demonstrably remain capable of useful change**.

TRUE’s B04 SHORT-to-LONG regret improvement is \(0.007198478370314595\). B06 produces a genuine above-diagnostic-MEI correction. B07 changes native actions rather than merely internal statistics. A competent same-information RAW path already exists in seed 0. These facts contradict claims that the learner cannot use its information, that all further optimization is futile, or that the residual transformation cannot learn anything.

They also make **CONTINUE_B a close runner-up**, rather than an excluded option. The reason to park is narrower: these changes have not yet supplied a sufficiently discriminating account of how the *next* intervention would create residual-specific native value against competent RAW, rather than another small rearrangement of comparator errors.

## LIVE_ALTERNATIVES

**The leading simpler explanation is ordinary finite-budget surrogate optimization on a small, selected development surface.** Different joint initializations, representations, and objectives produce different legal-score orderings; low overall regret can coexist with several exact-action misses. The calibrated residual has no demonstrated optimization advantage in the competent comparison, and the later diagnostics have not identified which remaining optimizer or representation effect should be preferred.

This is an inference, not an identified causal diagnosis. Generic preprocessing, calibration, coupled predictor/gate initialization, capacity, loss weighting, gradient scale, clipping, Adam dynamics, TRAIN order, and selected-support effects remain live as applicable. In particular, B07 changes several optimizer consequences together. Its failure rejects that centered-loss package at the stated budget, **not common-return fitting as a general explanation**.

A genuinely action-directed objective is still conceivable. But an algebraically equivalent pairwise squared-difference loss would not constitute a new discriminator: the B07 card explicitly identifies its equivalence to the centered objective with matching weights. Ranking or cost-sensitive objectives would be different interventions, whose effects would still need native-action and return interpretation.

## OPTIONS_AND_SELECTION

| Option                                                              | Assessment                                                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PARK_CURRENT_SELECTED_PANEL_BALANCED_RESIDUAL_FAMILY — selected** | Preserves the competent negative, the comparator limitation, and the real learning counterexamples without automatically extending the generic repair sequence. Re-entry remains available on a concrete native-value discriminator.                                                     |
| **CONTINUE_B — close runner-up**                                    | A genuinely decision-directed RAW objective or another specifically motivated intervention could be legitimate B work. It is not selected merely because another surrogate can be named: its native-value prediction and connection back to residual discrimination need to be explicit. |
| **CLOSE_CURRENT_SELECTED_PANEL_BALANCED_RESIDUAL_FAMILY**           | Too strong for the unresolved family-level question. Only one joint seed supplies competent residual polarity; the other two are comparator-limited, and action-sensitive alternatives remain. Ending the completed unchanged interventions does not establish family exhaustion.        |
| **RECAST**                                                          | Not supported by a concrete new mechanism in this record. Renaming another optimizer intervention is not a mechanism recast, and no new host or ownership/information intervention is selected.                                                                                          |

The DM’s PARK recommendation is advisory, not evidence. I agree with its selected option after weighing the close call, not because the recommendation determines the result. 

The decisive consideration is **expected discrimination, not implementation inconvenience or accumulated cost**. Even assuming another small run is feasible, repairing a count qualifier is not automatically a material residual-value experiment. Nor is this decision based on missing independent seeds, transfer splits, formal proof, or oracle-retuned baselines: the controlling specification expressly excludes those as B launch requirements. Sources: evidence specification §§11.1–11.4 and 11.7.

## NEXT_DISCRIMINATOR_OR_REENTRY

### Native-value accounting

For these sixteen equally weighted EVAL rows, write \(G_i(a)\) for the recorded native G16 consequence and \(G_i^*=\max_{a\in A_i}G_i(a)\). Then

$$
R(\pi)=\frac1{16}\sum_i\bigl[G_i^*-G_i(\pi_i)\bigr],
$$

so, for the same rows and native labels,

$$
R(\mathrm{RAW})-R(T)
=\frac1{16}\sum_i
\bigl[G_i(T_i)-G_i(\mathrm{RAW}_i)\bigr].
$$

These are algebraic consequences of the B01 estimand, not new experimental results. They make the relevant distinction explicit:

* Residual improvement **above 0.0025** requires net summed native gain **above 0.04** across the sixteen rows.
* Diagnostic improvement **above 0.000625** requires net summed native gain **above 0.01**.

All losses from newly incorrect choices must be included. An arbitrary exact-action correction need not carry the minimum KEEP-versus-REPLAN advantage. The original residual MEI is one quarter of the selected minimum absolute advantage; the later diagnostic MEI is \(0.01/16\). Sources: B01 §§6–7 and B07 card, “Fixed historical evidence and result reading.”

A useful additional bound follows without constructing an accessible oracle policy:

$$
R(\mathrm{RAW})-R(T)\le R(\mathrm{RAW}),
$$

because regret is nonnegative. **Against seed 1’s recorded LONG RAW baseline, a LONG gain above 0.0025 is unattainable even at zero treatment regret**, since the baseline regret is \(0.0021294544930598857\). The same observation applies to its B07 centered value. This is only an arithmetic ceiling against those fixed baselines, not the missing tuned-baseline headroom package, not a competence finding, and not a reason to exclude B work. SHORT-budget value remains possible, and the seed-0 and seed-2 recorded regrets do not impose that same ceiling.

### Precise re-entry condition

**Re-enter on specification of one B discriminator whose possible results distinguish a native-value mechanism—not on prior experimental success.**

The proposal must identify a particular intervention and predict how it changes legal-action ordering or credit from already available information. It must connect that change to the paired native estimand above, retain a legal same-information RAW null, and explain how a competence-qualified result could resolve aligned residual value at the original 0.0025 MEI.

For an alignment claim, the test must distinguish improvement over RAW from improvement over the calibrated derangement, rather than crediting any easier preprocessing to alignment. A proposed comparator repair may be part of that experiment; **seeds 1/2 need not become competent before a B experiment may launch**. Competence remains an interpretation qualifier. A repair yielding competence within the diagnostic MEI may be useful if it unlocks a specified residual comparison with an attainable native contrast; it is not itself residual-value evidence.

The environment-to-consequence account must remain explicit:

**event and physical history → the existing option-owning agent slot → shared 42-vector history plus the declared 52-vector packet → legal KEEP/replacement score ordering or training credit → stated learner exposure → one charged replacement and the common 16-step native future.**

There is no entity replacement, roster change, or partner co-adaptation in the current host. A proposal introducing any of those would be a new scientific object, not an implicit repair of this family. Source: B01 §3 and B07 card, “Question and exact intervention.”

The required branch-to-action reading at re-entry is:

| Possible result                                                                                 | Scientific reading and action                                                                                                            |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Competent RAW; aligned treatment exceeds the declared native margin against RAW and derangement | Resume investigation of the bounded alignment-specific finite-budget mechanism. No C promotion follows automatically.                    |
| Gain is derangement-insensitive, or disappears with declared additional RAW exposure            | Attribute only the supported generic-preprocessing or exposure effect; do not label it aligned residual value.                           |
| RAW competence improves, but native gain is within diagnostic MEI                               | Record a comparator candidate without a material-value claim; proceed only through the specified residual discriminator.                 |
| Native cost or no material residual gain against competent RAW                                  | Reject the tested intervention at its stated boundary.                                                                                   |
| Comparator remains weak                                                                         | Preserve the diagnostic and signed changes; assign no residual polarity and do not automatically add another budget, seed, or objective. |

These are the decision contents of a re-entry proposal, **not additions to the specification’s launch gates**.

### Seeds, budget, and the exact missing specification

No new seed set, endpoint, budget, sweep, or invocation is selected by this PARK decision.

Any claim to repair the observed two-seed comparator problem must preserve the **seed-1 and seed-2 joint packages**, rather than silently retaining a successful seed. A different seed scope is possible as a transparently new B object, not as a reinterpretation of B05. Predictor initialization/fitting and gate initialization change together; derangement also changes where used. Sources: B05 “Next discriminator” discussion and B07 card’s intervention definition.

The missing scientific specification is **which single intervention, at which declared exposure, predicts a consequential legal-action change without offsetting losses, and why its result distinguishes residual alignment from ordinary comparator optimization**. A proven diagnosis is not required; a falsifiable action/native-value prediction is.

### Recorded exposure and cost anchors—not a new projection

B07 provided 516 Adam updates per seed, learning rate 0.001, nominal exposure 0.516, 16,512 gate examples, and 344 visits per TRAIN row. Its actual movement was finite and positive:

| Seed | Initial L2 / RMS / Linf                                       | Displacement-to-initial L2 / Linf ratios |
| ---- | ------------------------------------------------------------- | ---------------------------------------- |
| 1    | 18.92643228704128 / 0.10428775735716496 / 0.287416011095047   | 0.10900415513564093 / 0.9725612593361669 |
| 2    | 18.844772502567565 / 0.10383779850280324 / 0.2884293794631958 | 0.1206322176206708 / 1.0175024256157004  |

These measurements establish finite movement, not adequate optimization, efficacy, or convergence. Source: B07 technical evidence, “Actual resources, scales and exposure.”

B07’s prospective law was \(3(P+516t_s+E_s)\), with \(P=62.425374370999634\) seconds. The recorded \((t_s,E_s)\) values were \((0.05216934772284702,0.007404837990179658)\) and \((0.047116037356571785,0.007313847003388219)\), yielding projections of 268.05648790193663 and 260.2336904819822 seconds. Centering overhead was prospectively unmeasured, so these were estimates, not strict bounds.

Actual B07 supervisor durations were 124 and 126 seconds; runner times were 114.58920120599214 and 115.89204864800558 seconds, with peak RSS 1,285,758,976 and 1,284,915,200 bytes. The six B05/B06/B07 invocations sum to **807 supervisor seconds**: 368 + 189 + 250. That is a recorded window, not lifetime cost, efficiency, or a next-object estimate.

For a different objective or architecture, the missing cost facts are its preparation reuse, actual per-update overhead, evaluation work, and actual-node resource demand. No numerical projection is invented here. The completed CPU FP32/thread-1, remote-first execution record does not authorize a device or bit-identity claim.

## UNCERTAINTY_AND_LIMITS

**Adaptive exposed support.** The selected population was constructed using previously observed outcomes, and the same sixteen EVAL identities have informed successive designs. Repeated scoring does not create additional independent members. B exploration remains legitimate, but none of these results becomes independent confirmation.

**Coupled seeds.** The observed seed dependence cannot be attributed to gate initialization alone. Neither changing the label nor averaging away a weak seed repairs that limitation.

**Competence and value remain separate.** Exact-count weakness cannot be waived retrospectively, but passing a future count threshold without meaningful return change cannot be promoted to native-value superiority. B06’s gain and B07’s offsetting changes remain part of the record.

**Untuned headroom.** No tuned same-information RAW/compatible-upper package with seed curves is recorded. The zero-regret label oracle is privileged, not an accessible policy. Missing headroom is a sequencing input, not a B launch gate and not the scientific basis for this park.

**Unresolved A01.** A01’s original native crash remains unexplained. A02’s NO-FAULT-WITHIN-BOUND result and later successful runs do not diagnose it. No infrastructure failure is converted into mechanism polarity. Source: `DIRECTION.md`, “Diagnostic RAW trace reading A03,” and B07 intake’s integrity discussion.

**Verification boundary.** This decision uses the listed cards, technical evidence, accepted intakes, and current direction synthesis. I did not retrieve their unlisted JSONs or source files, execute code, rerun learners, or independently reproduce the archived numerical validation procedures.

## DIRECTION_EFFECTS

Park only the **current selected-panel balanced residual family**. Preserve B04’s competent seed-0 negative, B05’s comparator-limited seed extension, B06’s KEEP-side gain, and B07’s small action-sensitive result at their original meanings.

Do not automatically repeat the unchanged residual intervention, extend the budget ladder, search seeds, relax competence, or change the residual MEI. Re-entry is the native-value condition above.

The historical natural K8 first-boundary family remains closed. The later September 1 authority opened this scientifically distinct balanced B family; neither event is overwritten by this decision. No historical confirmation namespace or support search is reopened. Source: `DIRECTION.md`, “Mandatory convergence node” and “Empirical-standard Portfolio reopening.”

## PORTFOLIO_EFFECTS

**None executed or ratified.** This is the direction-local convergence disposition of the named family. It does not set or confirm cross-direction lifecycle, priority, capacity, scheduling, absorption, or resource allocation. It does not promote to C and is not a launch gate on an already-frozen B card.

## READ_PATHS

All nine listed paths were successfully read through the connected GitHub connector in `CartmanFatass/My-paper-code` at exactly `4d1572b9282af887e238ad1c7e3d0af45d72d027`. No connector/ref/path blocker was encountered, and no unlisted repository path was retrieved.

```text
docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md

docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_INTAKE_20260904.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_JOINT_SEED_B05_INTAKE_20260905.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_RAW_EXPOSURE_B06_INTAKE_20260905.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_RAW_CENTERED_LOSS_B07_SCIENCE_CARD_20260905.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_RAW_CENTERED_LOSS_B07_RESULT_EVIDENCE_20260905.md

docs/research/candidates/commitment_residual_triggered_options/CRTO_RAW_CENTERED_LOSS_B07_INTAKE_20260905.md
```
