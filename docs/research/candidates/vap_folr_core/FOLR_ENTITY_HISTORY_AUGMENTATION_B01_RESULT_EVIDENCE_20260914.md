# FOLR augmentation B01 result — 2026-09-14

Object `FOLR_ENTITY_HISTORY_AUGMENTATION_B01_781601`, B / EXPLORE.
[Fixed card](FOLR_ENTITY_HISTORY_AUGMENTATION_B01_SCIENCE_CARD_20260914.md),
execution source `d9977dc18baf33b78dc626764c252391f1ddaa9d`, technical acceptance
`50bbaa5e9b4cadba8ac8361f704b46b17590ba24`.

## Frozen rule and actual reading

Both original fresh programs finished exit0 with their full final endpoints.
A mean4.329921875 minus G mean−0.966484375 gives **d_A−G=+5.29640625**.
The fixed rule is strict d>1 AUGMENTED_ABOVE_MEI; inclusive[-1,1] WITHIN_MEI
with sign retained; strict d<−1 GENERIC_ABOVE_MEI. Actual classification:
**AUGMENTED_ABOVE_MEI**,4.29640625 above the positive MEI boundary.
MEI1 is an effect scale, not a significance/equivalence or competence test.
The selected publisher was recomputed from both original summaries and matched
A's published primary; separate NumPy calculation gave the same contrast up to
ordinary floating-point summation. No historical score supplied this comparator.

| Final fitted-policy fact | Generic G | Augmented A |
| --- | ---: | ---: |
| Mean native return | −0.966484375 | 4.329921875 |
| Sample SD | 7.311570982 | 8.237034431 |
| Conditional episode SE | 0.646257678 | 0.728057863 |
| Negative returns /128 | 75 | 42 |
| Minimum | −16.56 | −15.20 |
| Maximum | 20.08 | 23.64 |
| Actor learnable parameters | 103173 | 192741 |
| Actor parameter-change L2 | 31.432660529 | 47.836202113 |
| Complete native wall, seconds | 1178.68 | 2796.80 |
| Aggregate CPU, seconds | 1177.50 | 2795.46 |
| Peak RSS, KiB | 741336 | 866572 |

Each arm is one fresh training instance,5000 complete training episodes /
100000 native ticks /4969 RMSprop updates, one final checkpoint, then128
non-learning greedy episodes /2560 ticks. Total2 fresh fits,10000 training
and256 final episodes,205120 native ticks,9938 optimizer updates. Seeds are
train781601/eval1781601 in each arm. Python/global NumPy/Torch were freshly
reset as fixed; equal labels and aligned compatible initialization establish
neither paired episode worlds nor independent arm draws. The publisher's
`training_pairs=1` counts the selected comparison block; it is not a statistical
pairing certificate. Conditional episode SEs do not estimate training-population
uncertainty. No paired-difference interval, p-value or population rank is claimed.

## Source, execution and technical acceptance

G handle `folr-augmentation-b01-781601-generic`,PID3674297, accepted
2026-09-14T15:36:55.744043Z, finished15:56:34Z. A handle
`folr-augmentation-b01-781601-augmented`,PID3679958, accepted19:39:55.755736Z,
finished20:26:32Z. A terminal was observed/delivered20:26:49.622Z; direct DM
collection at20:27:40.958451Z independently confirmed exit0, no tmux activity,
fixed clean source and original G digest. No result-bearing retry or third fit.

Both run on configured remote CPU FP32, Torch2.7.0+cu118 / NumPy1.26.3,
Torch threads1/1, original H20 five-slot easy native public-lifecycle Traffic
Junction. The legal-information contract, same-role Generic initialization,
independent learner/target/replay state, full double-Q updates and final128 panel
remain as accepted. G was first; A followed technical G collection independent
of G's score. Fresh physical AND effective memory>=4GiB passed for both.

Weights-only checkpoint collection verified arm and4969-update identities,
finite actor/mixer/target/optimizer tensors, FP32 CPU values and source-grounded
buffer counts. G has103173 parameters+26 buffers; A192741+27 buffers
(labels25, Generic attention scale1, entity attention scale1). Targets match
these state dimensions; mixer state has284292 elements in each. Finite trained
parameters and changing returns establish exercised learning paths, not convergence
or useful-memory attribution. The earlier G checker conflated buffers with
parameters; that diagnostic failed before archive, was corrected against source
and changed no scientific invocation or output.

## Preservation, costs and deviations

[Compact complete result](entity_history_augmentation_b01_781601/RESULT_SUMMARY.json)
and [cost record](entity_history_augmentation_b01_781601/COST_SUMMARY.json) link the
actual native facts. Full5000 training and128 final returns remain in each original
summary. `TRAINING_RUN_ENDPOINTS.csv` has one row per fitted program, not episode
rows; the existing scientific-tool summarizer ran without `--paired` and reports
only descriptive single-run facts. Exploratory1000-episode training bins in the
result are changing-policy context, not extra final endpoints or selected checkpoints.

G [collection](entity_history_augmentation_b01_781601/GENERIC_COLLECTION.json)
was published at`b881dd67c2a89aaa95ab5741541d98ff265653ff`; A
[collection](entity_history_augmentation_b01_781601/AUGMENTED_COLLECTION.json)
recomputed its original G-bound primary. G summary SHA256
`152b1b807f148a9d7004f8b0208d30ce2fa1c147734c11d4d7cb01f84216336c`;
A summary SHA256
`ac8a8e647eb18f6028af2743ae7fa0a9634ac24b388124f80bbf89f23298ff0e`.
G's14 raw archive members are4,298,469bytes,
SHA256`8bfe7c3d711d85ae51e70a932503538415afc059e2bffd7a4d6ff5d39f5d2efc`;
A's15 are5,282,464bytes,
SHA256`0190acfca2c38ac45963abbc425b0de4620bbe707880994733b65ac6880a06bd`.
Original output/checkpoint, commands, admission, timing and supervisor files
are preserved. All transferred archive/member hashes and original summary bytes
passed local readback; the complete terminal monitor snapshot is retained.

Summed complete native wall is3975.48s; aggregate CPU3972.96s. Study elapsed
at supervisor second resolution is17377s, including13401s inter-arm gap.
The precise G-terminal-to-A-preparation control interval is13401.737549s;
source timestamp granularities differ and are named in the cost record. The
unsupported-effort parent control failure and recovery contributed to the delay;
it is not extra G native wall or all measured active support. Neither postexit
supervisor uptime nor model waiting is relabeled invocation runtime.

The known E/F/B02/B03 native subtotal12538.44s plus this object is16513.92s.
This is not complete direction-lifetime cost. Full support/provider/engineering
cost remains UNKNOWN; nested measured collection/transfer windows are not blindly
summed. Native G3600s/A5400s plans were not exceeded; full1800s support-reference
compliance is UNKNOWN. Plans were not scientific stop gates. The observed A/G
wall ratio2.3728 is one sequential implementation fact, not an efficiency study.
No frozen reward/information/exposure change, score stop, favorable-output selection,
extra panel, best checkpoint or additional paid/cross-direction resource followed.

## Prediction and closeout

Prospective DM prediction was GENERIC_ABOVE_MEI, low confidence: **miss**.
Owner prediction remains not taken (unattended). This result is preserved even
though it reverses the DM forecast. It does not rewrite old replacement BANK B02
(d=−4.830859375) or B03(d=−6.63671875), E's missing fresh contrast or F's
outcome-informed retained-reference result.

Owner event OWNER_PAUSE_AFTER_INFLIGHT_20260914 requires completing this object
and its necessary scientific review/intake/handoff, then awaiting explicit resume.
Scientific CONTINUE/MEDIUM and slot occupancy remain. No successor is selected.
See [DM intake](FOLR_ENTITY_HISTORY_AUGMENTATION_B01_INTAKE_20260914.md) and
[Chinese brief](../../portfolio/owner/briefs/vap_folr_core/2026-09-14_FOLR_ENTITY_HISTORY_AUGMENTATION_B01_781601.md).
