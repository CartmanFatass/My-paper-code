# FRRIE contact-active R128 R02 R05 result evidence — 2026-09-04

**R05 completed validly at B/EXPLORE ceiling: `R02_SMALL_OR_ROSTER_MIXED`.** The final arm
differences are +0.000467050572 at N=9 and -0.000867790232 at N=15; both absolute values are
below the original MEI 0.005. EDGE is slightly above uniform at both final rosters.

Object: `FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904`. Authority is the original R02 science
card plus `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R05_EXECUTION_ADDENDUM_20260904.md`.
This is the fresh R05 scientific execution, not a reuse or upgrade of A01 evidence. The
adjacent `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R05_RESULT_EVIDENCE_20260904.json` is the unchanged
118,913-byte publisher output, including every learner row, evaluation cell, event/action
count, projection inventory and checkpoint description. It is the full-curve evidence artifact.
Exact command and raw receipts are recorded in the R05 CM record.

## Original rule applied verbatim, in order

| branch | rule and bounded reading |
| --- | --- |
| `R02_INVALID_INCOMPLETE` | A common-integrity item fails; remote/local admission is absent or below 4 GiB; real learner transition/update/evaluation counts or exposure are zero/missing; information/work differs; raw initialization is not paired; the initial tight clip does not change exactly five coordinates; optimizer moments change during projection; or required learner-side curves/counts are absent. Quarantine; no result. |
| `R02_EDGE_BELOW_UNIFORM` | The result is valid and contact-active, but `e_128 < 0` at either seen roster. Report every direct curve and gap; the containing comparator is not competent on the affected cell, so the arm gap is nonidentifying. |
| `R02_FAVORABLE_BOTH` | EDGE is at least uniform on both rosters and `d_128 >= +0.005` at both. Preliminary one-root favorable activated-projection signal only. |
| `R02_ADVERSE_OR_MIXED` | EDGE is at least uniform on both rosters and `d_128 <= -0.005` at either. Bounded adverse or roster-mixed evidence for this configuration only. |
| `R02_SMALL_OR_ROSTER_MIXED` | The complete valid contact-active result reaches none of the earlier branches. Report literal signs/magnitudes; no stable effect claim. |

The first row does not apply: all original integrity inputs and 22/22 completion checks pass,
the measured counts below are nonzero and complete, and required curves exist. Final e128 is
positive at both N, so the second row does not apply. Neither favorable nor adverse thresholds
is met. Therefore the first matching row is `R02_SMALL_OR_ROSTER_MIXED`, agreeing with the
unchanged publisher's branch. No fallback or additional diagnostic condition changes this rule.

## Every native evaluation cell

Each row has 256 episodes and 3,072 transitions/native slots, INTACT. Shared uniform cells are
reused at all checkpoints. Display values are rounded; the JSON retains full precision and
all action/native-event inventories. `min_D` is mean min(D_W,D_E), not min of the two means.

| Arm | Update | N | J | D_W | D_E | min_D | WASTE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UNIFORM_LEGAL | shared | 9 | 0.018678979677 | 0.04296875 | 0.08593750 | 0.00390625 | 0.956113849068 |
| UNIFORM_LEGAL | shared | 15 | 0.026012614408 | 0.11718750 | 0.07421875 | 0.00390625 | 0.950485835085 |
| PHY_TRUST_004 | 0 | 9 | 0.017465127058 | 0.05078125 | 0.06640625 | 0.00390625 | 0.955557062756 |
| PHY_TRUST_004 | 0 | 15 | 0.027431379065 | 0.12109375 | 0.07421875 | 0.01171875 | 0.947040376021 |
| EDGE_FLEX_150 | 0 | 9 | 0.017464270427 | 0.05078125 | 0.06640625 | 0.00390625 | 0.955565629061 |
| EDGE_FLEX_150 | 0 | 15 | 0.027430338288 | 0.12109375 | 0.07421875 | 0.01171875 | 0.947050783783 |
| PHY_TRUST_004 | 32 | 9 | 0.020397891981 | 0.05859375 | 0.08593750 | 0.00390625 | 0.955851809354 |
| PHY_TRUST_004 | 32 | 15 | 0.027235077453 | 0.11718750 | 0.08203125 | 0.00781250 | 0.949979954632 |
| EDGE_FLEX_150 | 32 | 9 | 0.020398574408 | 0.05859375 | 0.08593750 | 0.00390625 | 0.955844985088 |
| EDGE_FLEX_150 | 32 | 15 | 0.027235217664 | 0.11718750 | 0.08203125 | 0.00781250 | 0.949978552526 |
| PHY_TRUST_004 | 64 | 9 | 0.019543757662 | 0.05468750 | 0.08203125 | 0.00390625 | 0.955929610878 |
| PHY_TRUST_004 | 64 | 15 | 0.028588855701 | 0.12109375 | 0.08984375 | 0.00781250 | 0.949137484655 |
| EDGE_FLEX_150 | 64 | 9 | 0.019551580027 | 0.05468750 | 0.08203125 | 0.00390625 | 0.955851387233 |
| EDGE_FLEX_150 | 64 | 15 | 0.028526588452 | 0.12109375 | 0.08984375 | 0.00781250 | 0.949760157149 |
| PHY_TRUST_004 | 128 | 9 | 0.019653054909 | 0.05078125 | 0.08593750 | 0.00390625 | 0.954836638412 |
| PHY_TRUST_004 | 128 | 15 | 0.025629587619 | 0.10546875 | 0.08203125 | 0.00390625 | 0.950084332144 |
| EDGE_FLEX_150 | 128 | 9 | 0.019186004337 | 0.05078125 | 0.08203125 | 0.00390625 | 0.955275373301 |
| EDGE_FLEX_150 | 128 | 15 | 0.026497377851 | 0.10546875 | 0.08984375 | 0.00390625 | 0.949869971490 |

Here d=J_PHY-J_EDGE and e=J_EDGE-J_UNIFORM. All eight rows were independently recomputed by
cell subtraction during read-only collection and match the publisher exactly.

| Update | N | d | e |
| --- | --- | --- | --- |
| 0 | 9 | +0.0000008566305041285416 | -0.0012147092493250966 |
| 0 | 15 | +0.0000010407762601957748 | +0.0014177238801494248 |
| 32 | 9 | -0.0000006824266165494919 | +0.0017195947313060345 |
| 32 | 15 | -0.00000014021061360905418 | +0.0012226032558828592 |
| 64 | 9 | -0.000007822364568713103 | +0.0008726003502185151 |
| 64 | 15 | +0.00006226724945008685 | +0.002513974043540656 |
| 128 | 9 | +0.00046705057223637644 | +0.0005070246600856372 |
| 128 | 15 | -0.0008677902321020704 | +0.0004847634428491142 |

## Exposure, contact and completed work

Literal seed 1 / `FRRIE-B02-CONTACT-BLOCK-001`, root
`2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`.
CPU FP32, one Torch thread, native width 32, original `(9,15)*32` training order and both
original boxes were retained. Raw paired arm/model bytes agree. Raw beta range is
[-0.038080986589193344, 0.048026394098997116]. The initial tight clip changes exactly five
coordinates [2,4,11,12,16], matches direct clipping, and leaves optimizer state unchanged;
wide initial projection is identity. First tight contact is update 0.

`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`.

PHY contacts the box in 50/128 subsequent updates, with 99 coordinate-clipping events across
those updates; the five initial changes are separate. The maximum tight overshoot is
0.008026394993066788 and cumulative displacement including initialization is
0.028062518686056137. Wide boundary contact is false, with zero changed-coordinate events.
Initial and every subsequent projection preserve optimizer moments. Both full 128-row curves
have sequential update numbers, 128 backward calls and 128 Adam calls. Final parameter movement
from raw initialization: PHY L1 87.00852966308594 / Linf 0.02603882923722267; EDGE L1
87.8931655883789 / Linf 0.026373978704214096. These are implementation observations, not
independent evidence of relational specificity.

| Work | Per learned arm | Whole invocation |
| --- | --- | --- |
| Updates / backward calls / Adam steps | 128 / 128 / 128 | 128 paired / 256 / 256 |
| Factual training episodes | 8,192 | 16,384 |
| Factual learner transitions | 98,304 | 196,608 |
| Training native slots, including suffix work | 630,784 | 1,261,568 |
| Learned evaluation episodes | 2,048 | 4,096 plus 512 shared uniform |
| Learned evaluation slots | 24,576 | 49,152 plus 6,144 shared uniform |
| Total native slots | 655,360 | 1,316,864 |

There are 18 cells total (16 learned, 2 shared uniform), 4,608 evaluation episodes and
55,296 evaluation transitions. All cell action totals equal N times transitions. Shared tapes
are reused nine times per roster; model preservation during evaluation, information/work
pairing, raw initialization pairing and required curve/count presence all pass. Original
runtime native/replay checks remain enabled. No independent learner execution was added.

## Execution, resources, deviations and limitations

Node `wsl_4070`, configured Python 3.10; launch SHA
`5e6d47f0cc05dfdf345bfe7f3f8661d1ffcf7ecc`. Task
`frrie_b01_contact_r02_5e6d47f0_05` started 2026-09-05T00:53:58Z and ended 01:09:35Z:
937 supervisor seconds. Original runner exited via SystemExit(0); pdb's separate exit 0 alone
was not used as validity evidence. Its post-terminal missing-local queries are expected and
do not represent a second learner invocation or learner failure.

Admission physical/effective memory each 12,670,226,432 bytes at 00:53:58.408321Z. Measured
runner wall is 898.6516333679974 seconds, peak RSS 615,534,592 bytes. Attributed PHY/EDGE wall
is 160.1987184420359 / 159.29206010704365 seconds; optimizer portions are
12.825379254041763 / 12.751058346024365 seconds. Shared work is additional, so attributed
values are not a replacement for total wall. The same-node prospective anchors were
160.52530051894428 / 160.3020884220823 per arm and 927 supervisor seconds. Both per-arm and
total caps were met. No sweep or resource-performance claim is made. Per-cell wall/RSS and
scratch were not separately measured; the existing run/arm measurements are retained.

Production source diff against the recorded r04 surface and final launch SHA is empty. No
scientific, RNG, numerical, information, evaluation or work deviation was selected or observed
in the retained checks. No new source or framework was added and no test repeated for R05.
The original publisher provides the full required learner/cell curves; no post-hoc scaffold
was needed. Raw supervisor/admission/summary artifacts remain at the accepted remote paths
and CM's ignored `technical/r05-collection/` directory. No prior evidence was modified.

This is one literal root on seen N={9,15}; small opposite signs do not establish equivalence,
stable superiority, held-out transfer, seed-population behavior or a relation-specific effect.
EDGE's small positive margin is a minimal competence check, not a tuned baseline or headroom
measurement. R04 and attempt02 failure causes remain unresolved; this completed run is not a
diagnosis or retroactive salvage. A01 remains a separate A/RECON result. Real publication ran
successfully, but formal-sized end-to-end test coverage remains an open engineering item.
DM owns prediction scoring and the next object; no R06, retry or new direction decision occurs here.
