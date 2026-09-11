# UCOPE renewal B03 P72 — native result evidence

**B/EXPLORE, valid DOWN on new matched training pair7501.** T−G is
**−0.03094711061890552**, conditional evaluation SE **0.010056196158593048**.
Both learned arms have positive sampled hover contrasts; G exceeds T here.
P70/P71 remain separately UP. The three observed effects change sign and do
not support a stable superiority or harm claim. The
[machine-computed summary](UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_RESULT_SUMMARY_20260909.json) retains every final return and signed vector.

## E0.1 Object, frozen inputs and actual invocation

Object `UCOPE-UAV-RENEWAL-COMMITMENT-B03`, master **7501**, selector
`renewal_b03`, [prospective card §§1–7](UCOPE_UAV_RENEWAL_COMMITMENT_B03_SCIENCE_CARD_20260908.md). P72's one-third-pair
allocation/card/predictions were committed at
`5bdb7aba1fbfcc872a675c97734ee8481924cbee`.

- Accepted scientific source: `7d3aaab4646360e2473ae352b09c3933ccf8dacf`.
- Original check record: `769e67b97fe53303a13aaef70aad341869269c15`.
- DM source acceptance: `28e7833213f788f498bbc874e6e59b9326b22dca`.
- Literal execution payload: `171e4c80712f73f4a4d29234afe4032b3de21e0e`.
- CM terminal collection: `616e8649d5a29373815d04f519d4b8a3eb6d05c7`.
- Node: configured `hmasd-wsl-node`, CPU FP32, one Torch thread.
- Supervisor: `ucope-uav-renewal-b03-7501-p72-20260908`.
- Remote cwd: `/home/wu/hmasd-worktrees/ucope-uav-renewal-b03-7501-p72-20260908`.
- Output relative to cwd: `temp/directions/ucope/exp/ucope-uav-renewal-b03-7501-p72-20260908`.
- Local collection: that relative path under
  `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`.

Exactly one accepted detached submission. CM was the sole observer through
collection. Raw supervisor boundaries are start **2026-09-09T14:51:53+08:00**,
end **2026-09-09T14:58:24+08:00**, exit **0**; terminal PID3031759 is finished,
tmux inactive. Snapshot uptime444s is not invocation wall. Native status
**COMPLETE**, limits empty, no cap breach or partial steps.

The executed707-byte LF wrapper has SHA256
`2c51898fb65bae7597873edaa2f2ac7cd541130e56d35a5bf3736b335b824b9c`.
Fresh canonical actual-node admission at **2026-09-09T06:51:53.985797Z** measured
physical/effective available memory both **14574497792 bytes**, above
**4294967296**, before scientific creation. Its supervisor and output copies
are one byte-identical admission, not separate measurements. See
[CM intake §§4–7](UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_INTAKE_20260908.md#7-cm-terminal-collection-and-technical-acceptance).

## E0.2 Native estimand and rule applied verbatim

`J=sum_t sum(info['rewards_dict'].values())/256`. The primary is the mean of
32 paired final-episode T−G differences for7501 alone. DM's read-only analysis
checks all1120 recorded episode identities/resets/J values, all96 final returns,
three signed paired vectors and their native means/conditional SEs. No scientific
rollout, simulator, checkpoint evaluation, CM suite or tensor verification is repeated.

Card§5 DOWN rule, verbatim:

> Delta<−0.01: retain an adverse native reversal on this third fit and drop unchanged continuation from the next default choice; earlier gains cannot compensate.

Comparator qualification, verbatim:

> Weak/negative G−H narrows improvement-over-competent-control wording without erasing trustworthy T−G. Positive T−H never reverses primary loss.

The native point lies **0.02094711061890552 below −0.01**. Its conditional
evaluation SE is **0.010056196158593048**; the reading uses the unrounded
point rule, not an added significance condition. This card's independent
training n=1 has no training-population SD or interval. H is a fixed reference,
not a trained replicate. No earlier fit enters or compensates this primary.

## E0.3 Complete outcomes and three separate fitted observations

| Arm | Final mean J | Final episodes |
| --- | ---: | ---: |
| Renewal T | 0.16159104017261458 | 32 |
| Ordinary feedback G | 0.19253815079152012 | 32 |
| Untuned hover H | 0.14048393970863335 | 32 |

| Contrast | Native mean | Conditional evaluation SE | Positive / negative / zero episodes |
| --- | ---: | ---: | ---: |
| T−G | -0.03094711061890552 | 0.010056196158593048 | 10 / 22 / 0 |
| T−H | +0.021107100463981232 | 0.014144010759846842 | 19 / 13 / 0 |
| G−H | +0.052054211082886756 | 0.010175312737684957 | 26 / 6 / 0 |

T beats hover on its sampled point but loses to the legal same-information G.
G−H is positive with26 positive and6 negative paired episodes. This is the
strongest sampled G−H among these fits; it does not establish a tuned baseline
or general competence. T−hover cannot replace the primary comparator.

| Separate fit | T−G | Conditional evaluation SE | T−H | G−H |
| --- | ---: | ---: | ---: | ---: |
| P70, 7301 | +0.055673191348834944 | 0.011556059794903147 | +0.05305453732049459 | -0.002618654028340355 |
| P71, 7401 | +0.024658177040921356 | 0.011145715505143731 | +0.03714831826363973 | +0.012490141222718373 |
| P72, 7501 | -0.03094711061890552 | 0.010056196158593048 | +0.021107100463981232 | +0.052054211082886756 |

As prospectively allowed in B03§1, an explicitly secondary, outcome-informed
description uses one T/G endpoint per independently trained pair. The
scientific-tools utility gives paired mean **0.016461419256950254**,
sample SD **0.043888031476388346**, n=3. All three endpoints remain,
including the loss. Last-digit differences between differences of arm means
and native means of paired differences are floating-point reductions, not
changed primary values. This descriptive mean is **not another UP reading**
and never reverses P72 DOWN. Endpoint variation includes finite evaluation noise;
training histories and final panels both differ, so it is not a pure
training-variance estimate or a population guarantee. These were sequential
exploratory follow-ups after earlier UPs, not prospective three-seed confirmation.

## E0.4 Actual learner exposure and native path

Each T/G arm completed512 training episodes,131072 native training steps,
256 two-episode rollouts and1024 Adam calls, then32 final stochastic evaluations.
H completed32. Total: **286720 native steps,2048 Adam calls,96 final evaluations**,
1120 explicit resets, two constructor resets,512 rollouts and1600 prescribed
diagnostic rows; zero partial steps.

| T phase | Owned velocity/duration selections | d4 selections | Actually suppressed decisions | Horizon-censored holds |
| --- | ---: | ---: | ---: | ---: |
| Training | 259729 | 132898 | 395631 | 1538 |
| Final evaluation | 16135 | 8339 | 24825 | 102 |

G retains655360 training/40960 final velocity decisions and no duration choices.
The fixed path gives `6*259729+2*16135=1590644` duration-head forward rows,
**3512141952** dense forward multiply-adds. Selected-d4 fractions are
0.5116794813055145/0.5168267740935854 in training/final evaluation. These are
same-execution counts, not a timing experiment or a success rule.

Parameter totals remain T68553/G66311/head2242. Absolute displacement is
T8.163847923278809/G8.415543556213379, with duration1.044926404953003,
hidden1.0394105911254883 and final0.10722218453884125. Full groups remain
in the summary; zero-initial final-layer relative displacement is undefined.
CM checked stored FP32 tensors with the existing tolerance; DM did not repeat it.

Own expiry in the moving team exposes current private history and owned command
to the duration choice; persistence changes executed movement, later observations
and service, while primitive rewards enter masked PPO. Every such path is
actually exposed here, alongside a negative native T−G. Exposure or head movement
therefore cannot stand in for value. Persistence, geometry, capacity, gradient
exposure and partner co-adaptation remain unseparated explanations.

## E0.5 Resources, conformance and receipts

External whole wall **390.73s**, peak RSS **559132KiB**. Runner whole
**377.34080735302996s**; T/G complete-arm walls **204.3931929190294s /
172.94761272502365s**, sum **377.34080564405303s**. Both fit1800s and
whole fits3600s. Timer differences and the slower wall than P70/P71 are not
assigned to an unmeasured cause. Aggregate CPU and system-wide peak memory
remain `resources_unmeasured`; the native primary is independently trustworthy.

One accepted invocation/one valid new fit costs390.73s whole wall. The three
accepted complete renewal fits total **1001.62s**, **333.8733333333334s per
valid fit**, excluding engineering and older opening regimes. This sum is not
session critical path or aggregate CPU work. Their total exposure is860160
native steps,6144 Adam calls and288 final evaluations.

Source changed only binding/routes (+27/−21 production, +18/−12 tests), runner54
lines. One exact-source affected suite passed99 tests,3.75s complete wall of300s.
Engineering scope§4 **none**, no§5 breach. DM inspected the actual diff and
original acceptance; no substantive credit amendment or independent-review need arose.
Later owner-authorized role-config synchronization changes no scientific source.

CM's all-seven-output remote/local SHA256 checks and finite checkpoint/phase/
rollout acceptance are retained in its report and this summary. DM independently
checked collected summary/episode/admission digests and the executed wrapper,
then read supervisor/readback facts. Raw roots retain source/check receipts,
submission, summary, episodes, rollouts, diagnostics, final T/G checkpoints,
admission and supervisor/verification records. No new scientific work follows.

## E0.6 Scientific reading, predictions and completed boundary

Strongest contrary evidence to simple recurrence is this below-MEI primary
while G has a substantial positive sampled hover contrast. Strongest support
for a still-possible package benefit is the two earlier UPs and positive T−H
in all three fits. Neither overrides the other: no stable superiority, stable
harm, equivalence, causal renewal/information effect or family closure follows.
Prior opening-family nulls/losses and gains remain separate and unchanged.

For interpretation of the reversal, the local-library route reuses the verified
UTE/ACAC passages recorded in [P67 intake§3](UCOPE_POST_B04_RENEWAL_CONVERGENCE_INTAKE_20260908.md#3-scientific-reading-counts-and-contrary-evidence)
and inherited by B02§2/B03§2. Those passages support the renewal-event distinction;
they do not predict this UAV sign or identify a cause. No new corpus-coverage,
novelty, tuning or causal claim is made from them. The new evidence changes the
accepted record from two recurrences to two gains plus one adverse reversal.

UP0.60 misses; G−H>0 at0.55 hits: **1/2**, mean Brier **0.28125**.
Owner prediction **not taken (unattended)**. Earlier predictions and scores stay
intact. DM accepts DOWN and ends P72; no fourth unchanged pair is recommended.
The later owner soft stop additionally holds every successor/Pro request for
restart. See [intake§§8–11](UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_INTAKE_20260908.md#8-dm-all-outcome-check-and-reading),
[Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-09_UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72.md) and [restart handoff](UCOPE_RESTART_HANDOFF_20260909.md).
