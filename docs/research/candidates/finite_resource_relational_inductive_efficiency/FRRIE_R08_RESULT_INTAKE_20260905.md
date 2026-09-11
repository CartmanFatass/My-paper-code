# FRRIE R08 result intake — 2026-09-05

Status: `VALID_B_EXPLORE / R08_INTERACTION_WITHIN_MEI / PREDICTION_MATCHED`.

## What DM checked

DM read the frozen R08 card, CM E0/terminal commit
`7f636b3fbb51d6795e2067132994dd519e65f0e1`, the unchanged 125,717-byte
`FRRIE_R08_RESULT_EVIDENCE_20260905.json` and `FRRIE_R08_RESULT_20260905.md`.
DM inspected actual identity/root/LR, all 22 completion predicates, 22 cell coordinates,
eight original curves, both full cut contrasts, actual paired tape use, model preservation,
256 learner/projection rows, eight checkpoint-state summaries, counts, exposure, resources
and original termination. Native deltas below are read-only subtraction of existing cells,
not a replay, evaluation, test or another result-bearing invocation.

CM directly observed original SystemExit(0), complete publication and subsequent fixed-pdb
reentry before module line 1, followed by q without a second computation. This is independent
of debugger/supervisor exit 0. There was no original uncaught exception or timeout. Remote
HEAD and tracked surfaces remained at the accepted source; only that fresh native build was
untracked. Collection changed no source, test, publisher or runtime meaning.

## Original rule applied verbatim, in order

| branch | rule and bounded reading |
| --- | --- |
| `R08_INVALID_INCOMPLETE` | Common integrity fails; actual root/label/seed/LR or protected training differs; fresh node admission is missing or below 4 GiB; nonzero planned learner/update/evaluation work or exposure/curves are missing; raw information/work/initialization pairing, direct initial five-coordinate clipping or projection-moment preservation fails; the declared existing cut or shared tapes are not used; required cells/labels/INTACT descriptors are absent or wrong; or evaluation adapts the model. Quarantine, no result. |
| `R08_INTACT_EDGE_BELOW_UNIFORM` | Complete valid N15 e_I < 0. The intact containing comparator is below its minimum reference; report all values, no identifying conditional package interpretation. |
| `R08_NO_MATERIAL_POSITIVE_ANCHOR` | N15 e_I >= 0 but d_I < +0.005. The new intact endpoint does not provide the material positive anchor targeted by this conditional question. Report literal sign/magnitude, including an adverse gap; do not infer a technical defect or rewrite R06. |
| `R08_ROTATED_EDGE_BELOW_UNIFORM` | N15 has the material positive intact anchor but e_C < 0. The perturbed containing comparator is below its minimum reference; report the interaction as nonidentifying for the conditional package question. |
| `R08_MATERIAL_ATTENUATION` | N15 e_I >= 0, d_I >= +0.005, e_C >= 0 and a >= +0.005. Material conditional attenuation under this common role-prior-column cut; disclose any sign reversal, no semantic/population claim. |
| `R08_MATERIAL_AMPLIFICATION` | N15 e_I >= 0, d_I >= +0.005, e_C >= 0 and a <= -0.005. Material conditional amplification under the cut, contrary to an attenuation account; no direction closure. |
| `R08_INTERACTION_WITHIN_MEI` | Complete valid identifying result reaches none of the earlier branches. N15 a is strictly inside (-0.005,+0.005); no material differential cut response at this margin. |

The invalid row is false: complete actual counts, root/label/seed/LR, paired information,
direct initial clipping, moments, preserved evaluation, declared cut and common tapes agree.
At primary N15, e_I is positive, d_I exceeds +0.005 and e_C is positive. Thus all three
nonidentifying rows are false. The interaction is neither >=+0.005 nor <=-0.005.
The first match is **R08_INTERACTION_WITHIN_MEI**. N9 is a full secondary report;
its positive intact gap is below the primary anchor threshold and its interaction is
also inside MEI. It does not replace the N15 rule.

| N | d_I | d_C | a = d_I - d_C | e_I | e_C |
| --- | --- | --- | --- | --- | --- |
| 9 | 0.0010669079143553993 | 0.0010653388919308789 | 0.0000015690224245204498 | 0.0071992404681319976 | 0.007199197976539531 |
| 15 | 0.0055482935315618875 | 0.0055381194377938925 | 0.000010174093767995052 | 0.014761398957731823 | 0.014770166405166183 |

| arm / N | J_INTACT | J_ROTATE | J_INTACT - J_ROTATE |
| --- | --- | --- | --- |
| PHY / 9 | 0.02694512805901468 | 0.026943516544997693 | 0.000001611514016987281 |
| EDGE / 9 | 0.02587822014465928 | 0.025878177653066815 | 0.00000004249159246683121 |
| PHY / 15 | 0.046322306897491214 | 0.04632090025115758 | 0.0000014066463336348534 |
| EDGE / 15 | 0.040774013365929326 | 0.04078278081336369 | -0.000008767447434360198 |

Shared uniform J is 0.018678979676527284 at N9 and 0.026012614408197503 at N15.
The EDGE N15 drop is negative: its cut return increases slightly. No sign or absolute-value
relabeling is applied.

## Native consequence and interpretation

The cut changes common prior-probability and latency sender columns by (2,0,1) and recomputes
K0 weights. It does not permute beta indices, message contents, raw observations, role counts,
legal masks or physics. Fresh 12-slot cells share the original addressed exogenous fields
and action uniforms while allowing different endogenous action/state trajectories.

For both arms and rosters, final D_W, D_E, mean minimum basin deliveries and total successful
deliveries are unchanged by the cut. At N15 PHY/EDGE still make 92/80 deliveries; at N9
they still make 50/48. The small return changes are entirely in the observed waste term.
This is not absence of execution: some actions and native events differ.

Rotated-minus-intact action counts follow [SCAN, UPLINK, LISTEN_WEST, LISTEN_EAST,
FORWARD_BASE, HOLD]:

| arm / N | action-count delta | native event deltas |
| --- | --- | --- |
| PHY / 9 | [-1,+2,0,0,0,-1] | empty radio +1; radio +2; waste +2 |
| EDGE / 9 | [+1,+1,0,0,0,-2] | collisions +2; empty radio +1; radio +1; waste +1 |
| PHY / 15 | [-2,+4,0,0,0,-2] | empty radio +2; expired +4; radio +4; waste +4 |
| EDGE / 15 | [-2,+4,-1,+1,0,-2] | collisions -1; empty radio +4; radio +4; waste +2 |

Waste-fraction changes are respectively +0.000016115140169858932,
+0.00000042491592466831207, +0.000014066463336348534 and
-0.0000876744743436575 in that table order. Complete values and all earlier intact curves
remain in the original JSON. The optional shadow-TV field is null because it was not
selected by this card; no required learner observation is absent.

The selected-path N15 tight advantage survives this specific chart cut almost unchanged.
There is no material differential chart sensitivity at the declared 0.005 margin, and
there is no large common return collapse in these cells either. That contradicts the
specific attenuation account on this path; it does not prove equality, semantic irrelevance,
universal cut insensitivity or absence of any useful relational representation.

The strongest support for a conditional package signal remains the above-MEI N15 gap on
root 1. R08's intact endpoint numerically matches R06, but it uses the same literal root,
configuration and addressed tapes and is not another independent root. Historical equality
was not an acceptance gate. R07's sub-MEI opposite-sign N15 result remains the strongest
contradiction to assuming recurrence across paths. Neither root supplies a material N9 gap.

Generic projected-Adam geometry/shrinkage, path-specific initialization/tapes/co-adaptation,
and roster dependence survive. This cut is an evaluation intervention on the common chart;
it does not isolate the training influence of that chart or rotate all relation information.
The ceiling remains **B/EXPLORE on the selected root, actual Linux CPU FP32 surface,
128-update work, seen N={9,15} and this cut**. No C, direction/family closure, lifecycle,
priority, semantic or population conclusion follows.

## Exposure, integrity and counts

Numeric seed 1, literal root
`2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`,
label `FRRIE-B02-CONTACT-BLOCK-001` and distinct R08 identity match the card. Both actual
initial/final LR groups are [0.003]. Initialization is byte-paired across 35,513 parameters;
direct tight clipping changes the known five coordinates [2,4,11,12,16]. Wide initial
projection is identity and first contact is 0.

PHY contacts in 125 of 128 subsequent updates, with 437 coordinate events over 14 distinct
coordinates; EDGE has no contact. Initial and every later projection preserve optimizer
moments. Cumulative tight projection displacement is 0.30848179012537, maximum overshoot
0.008026394993066788. Final raw-relative Linf displacement is
0.21827195584774017 / 0.2057093381881714, about 4.37 / 4.11 initial half-ranges;
L1 is 683.9115600585938 / 648.8775634765625.

The machine-generated exposure is `updates=128; adam_lr=0.003;
nominal_lr_exposure=0.384; init_half_range=0.05;
nominal_exposure_over_init_half_range=7.68; tight_box_half_width=0.04;
initial_projection_changed_coordinates=5`. The nominal index is not a displacement bound.
The cut adds zero learner updates or adaptation.

| quantity | direct retained observation |
| --- | --- |
| source / task | `58710424a6b25f3e4bdf019dc337423d2d54a75b` / `frrie_b01_contact_r08_58710424` |
| node | wsl_4070, CPython 3.10.21, CPU FP32, Torch thread 1, native width 32 |
| start / end | 2026-09-05T11:30:34Z / 11:45:08Z |
| fresh admission | 11:30:34.490719Z, physical/effective each 12,880,740,352 bytes |
| per-arm updates / Adam / backward | 128 / 128 / 128 |
| per-arm factual episodes / transitions / training slots | 8,192 / 98,304 / 630,784 |
| per-arm learned evaluation episodes / slots | 2,560 / 30,720 |
| evaluation | 18 INTACT + 4 final rotation = 22 cells; 5,632 episodes / 67,584 transitions |
| native slots | 661,504 per arm / 1,329,152 whole invocation |
| completion | 22/22 flags; 256 ordered learner rows; eight checkpoint-state summaries |
| tape reuse | same actual objects, 11 uses per roster; models preserved in all 22 cells |
| supervisor / runner wall | 874 / 813.7514705510112 seconds |
| PHY / EDGE attributed wall | 144.4043835529883 / 144.22931573199457 seconds |
| peak RSS | 615,481,344 bytes |

All cells have 256 episodes and 3,072 transitions, and their action sums equal roster times
transitions. Both four-hour per-arm and eight-hour whole caps hold. Observer uptime
935 seconds is not the execution duration. The separate per-cut wall values were not
retained, but executed code charged those cells into the reported arm totals; the card
does not require separate per-cell wall publication. Scratch high-water is absent,
marked `resources_unmeasured` for that optional resource quantity only.

The earlier 4,515-second whole / about 1,956-second-per-arm allowance was deliberately
conservative, not an observed marginal rate. Actual full runtime is smaller than R07
despite extra cells; that difference is not a measured speedup or a basis to subtract a
negative cut cost. Source remains 31/119=26.05% orchestration, experiment 562 lines;
one focused check passed before launch. No source or test changed at collection.
Formal-sized publication-test coverage remains open despite this full publisher completion.
Historical r04/attempt02 causes remain unresolved. Host tuned-baseline/upper headroom
references remain absent.

R05–R08 are a four-valid-B remote accounting window: **3,400.6787507290064 runner
seconds, 850.1696876822516 per valid result; 3,609 supervisor seconds, 902.25 per result**.
This is a compute-accounting window, not four independent roots or an all-attempt/lifetime
efficiency claim. A01, focused checks, failures and old Windows results stay separate.

## Prediction score and decisions this intake produces

DM's low-confidence conditional `R08_INTERACTION_WITHIN_MEI` prediction **matches**:
the positive intact anchor and both comparator-competence conditions hold, and neither
material attenuation nor amplification falsifier fires. This match does not validate a
complete mechanistic explanation. The owner's existing ladder prediction remains
`not taken (unattended)`; current reviews and audit owner columns contain no override.
R06's distinct mixed score and R07's matched conditional score remain unchanged.

Options: (a) accept the complete original-rule result and bounded prediction score;
(b) treat cut insensitivity as equivalence, semantic proof or family closure;
(c) count this selected-root repeat as independent root support; (d) invalidate absent
optional shadow-TV, per-cut wall or scratch telemetry.

Recommendation and selection: **(a)**, object tier, kind `technical`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
B has no consumption state. The result closes at most the proposed material differential
response for this root and exact cut, not the family or direction.

The next unresolved scientific discriminator is recurrence on another prospectively fixed
literal path, without another outcome-selected chart cut. CM completed two bounded
read-only layouts for seed 3/root integer 3 at unchanged LR/work. Even the layout reusing
the existing module has about 34 necessary lines and an orchestration lower bound of
24/34=70.59%, above the unchanged 30% ceiling. This is prospective source accounting,
not a failed implementation or empirical result. The exact recoverable boundary is in
`FRRIE_R09_THIRD_ROOT_IMPLEMENTATION_BOUNDARY_20260905.md`. No successor card, root,
source edit, check or invocation is selected; no code was added to dilute that fraction.
The old A1 headroom census remains a separate read-only boundary; no missing reference
has been relabeled into it or used as an extra B gate.

## Owner surfaces, tracking and append-ready audit

The owner-directed P1/P2-only review change relayed by Root on 2026-09-05 is applied:
no new independent ordinary decision, prediction, technical or brief inbox item is created,
backfilled or chased. Historical owner015 remains evidence. The Chinese result brief
`../../portfolio/owner/briefs/finite_resource_relational_inductive_efficiency/2026-09-05_r08_role_column_cut.md`
is a result document, not a new review item. Existing owner instructions remain readable
and binding; a future real new card/close-call would retain its required P1/P2 item.

Tracker terminal event is acknowledged and the same evidence was collected by CM.
There are zero active FRRIE handles. No retry, reevaluation or successor has been launched.
Root integrates CM E0 `7f636b3f` after the accepted source/run records, then this intake.

Root appends the following row under `frrie-r08-result-intake`. This DM changes no shared
Portfolio/audit file; without a new ordinary inbox item its evidence points directly here.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T04:53:33-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) original-rule complete result and prediction score; (b) equivalence/semantic/family closure; (c) independent-root relabeling; (d) invalidate optional telemetry | (a) VALID B/EXPLORE R08_INTERACTION_WITHIN_MEI, N15 attenuation 0.000010174094, conditional prediction matched | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R08_RESULT_INTAKE_20260905.md` | none | |
