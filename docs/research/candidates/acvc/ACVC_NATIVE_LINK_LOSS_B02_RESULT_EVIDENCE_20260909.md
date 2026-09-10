# ACVC-NATIVE-LINK-LOSS-B02 — P79 technical evidence

## Engineering acceptance

**Complete B02/P79 native comparison technically accepted.** The sole invocation exited 0,
all required outcomes were collected, and scientific intake remains with DM. Contract:
[B02 card §§1–5](ACVC_NATIVE_LINK_LOSS_B02_SCIENCE_CARD_20260909.md) and
[P79 prospective facts](ACVC_NATIVE_LINK_LOSS_B02_P79_PROSPECTIVE_FACTS_20260909.json)
at `56ce830386cfab6be30b217e5cc5b0d0f8109120`. The designated `codex/acvc` checkout
`C:/Projects/HMASD-worktrees/codex-acvc` began clean at that revision. Shared native,
UCOPE/MGTAP, fixed checkpoint, DM-owned inputs and all P78 evidence remain unchanged.

The sole source adaptation adds seed 8902 to the existing runner CLI, publishes the
corresponding B02/P79 identity, and uses a dedicated `launch_b02.sh` with the new run root
and admission path. `binding.py`, `model.py`, `learner.py`, `report.py`, PPO, initialization
laws, recurrence and sampling are unchanged from accepted P78 source `f42902116`.
The new master flows through those already-parameterized private streams. P78 gate
checkpoints are never loaded. The source reference and retained P78 bytes remain recoverable
at their original revisions; there is no compatibility shim or generic registry.

Scope §4 additions: **none**, as required by B02 card §5. Source change is 20 added /
5 removed non-test lines, including the dedicated 14-line launch command. The reused
attempt now has 484 non-test lines and the runner 150 lines, within 2000/600 limits.

## Focused checks and reused review

Reuse the accepted P78 independent semantic review and unchanged information/identity,
recurrent replay, credit/masking, common-initialization/containment and primary-output
coverage documented in [P78 evidence](ACVC_NATIVE_LINK_LOSS_B01_RESULT_EVIDENCE_20260909.md).
No second semantic implementation or full-suite repetition is needed for this identity change.

Current synthetic invocation, local scientific Python:

```text
python -m pytest -q -p no:cacheprovider --basetemp <new owned P79 temporary directory>/pytest
  tests/experiments/candidates/acvc/native_link_loss_b01/test_link_loss.py::test_primary_rules_and_complete_synthetic_publication[8902]
  tests/experiments/candidates/acvc/native_link_loss_b01/test_link_loss.py::test_b02_stream_identity
```

Result: **2 passed**, pytest 4.16 s; complete command wall **5.4396806 s**, charged to the
logical study and both learned arms. The Python wrapper reported 5.234 s internally and
confirmed its new `temp/directions/acvc/test/p79_identity_*` directory was absent after
standard temporary-directory teardown. There was no native environment or scientific
training/evaluation exposure. The old P78 blocked scratch path was neither touched nor retried.

Checks cover B02 object/allocation/master publication, CLI propagation, fresh reset identities
in every synthetic phase, checkpoint master fields, all-arm post-learner output publication,
2240 distinct action streams shifted exactly 100000 from P78, separation from all initialization/
reset streams (2789 distinct declared values total), and the dedicated P79 launch identity.
The synthetic fixture is not scientific performance evidence. Complete native output and
actual process-exit accounting are established separately by the sole invocation below.

## Prospective cost and publication coverage

The complete work law is unchanged: T/G each 512×256 collection steps, 1024 Adam updates
with chunk32 recurrent replay and 32×256 final steps; C/F each 32×256 final steps. Together:
294912 team steps, 2048 Adam calls, 512 rollouts, 1152 scored resets and 4 unscored constructor
resets. G retains its additional recurrent residual cost. Required checks, imports/startup,
C/F evaluation and publication/exit are charged to both learned arms; the other learned
fit is excluded from an arm's bill. No native pilot or alternative configuration is added.

P78 same-count costs are the measured reference (work multiplier 1): process 359.17 s,
T 199.8208294 s, G 215.5117409 s, whole 373.4069735 s including 14.2369735 s checks. Substituting
the current 5.4396806 s check cost while retaining P78 scientific-path costs gives a planning
projection of **T 191.0235365 s, G 206.7144480 s, whole 364.6096806 s**. New initialization,
trajectory and machine contention remain unknown; this is a reuse-based projection, not
a timing observation of P79. Caps remain 1800 s per complete arm and 3600 s complete study.

Post-learner coverage uses the same synthetic publication path as the actual runner,
with new identity/reset/checkpoint fields read back. All training/final native S/J outcomes,
gate choices, update records and five fixed paired contrasts will be retained separately
from P78. Conditional SE uses 32 paired joint episodes; no selected-max SE or pooling with
P78's evaluation episodes is introduced. Final T/G checkpoints are the only learned outputs.

## Execution boundary

One accepted scientific invocation is allocated, with master 8902 and the unchanged frozen
DENSE input digest `f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790`.
Route: configured `wsl_4070`, CPU/FP32, Torch intra/inter-op 1, unchanged native NumPy;
detached exact-source worktree and configured `agent-task`. Fresh actual-node admission
is joined by `&&` to the committed B02 launch command. Runtime root:
`temp/directions/acvc/exp/native_link_loss_b02_8902_p79_20260909/`.
No dependency on the old P78 remote worktree, local fallback, scientific retry, resume,
extra evaluation, tuning or second new instance is allocated. CM is sole observer through
terminal collection and technical acceptance; DM owns all-outcome scientific intake.

## Accepted invocation

- Exact pushed source: `4e019ca35b930c2216fdfe110ba587e222ca7384`.
- Node/cwd: `wsl_4070` / `/home/wu/hmasd-worktrees/acvc-p79-4e019ca35`, clean detached
  worktree at the exact source SHA; no dependency on the P78 execution checkout.
- Handle: `acvc-p79-native-link-loss-8902-4e019ca35`; supervisor PID 3049045.
- Run root: `<cwd>/temp/directions/acvc/exp/native_link_loss_b02_8902_p79_20260909`.
- Input: `/home/wu/hmasd-inputs/acvc/p79/final_DENSE.pt`; both local original and remote
  staged bytes verified against the fixed SHA256 above.
- Admission: `<cwd>/temp/directions/acvc/p79_admission.json`, assessed at
  `2026-09-09T11:59:10.378280Z`; physical/effective available **15627145216 bytes**, both
  above 4 GiB, passed. It immediately precedes this runner through the same `&&` command.
- Supervisor initially running, exit null, tmux active. CM remains sole observer;
  native DM received these facts without a monitoring handover.

Exact command submitted once under `agent-task run acvc-p79-native-link-loss-8902-4e019ca35`:

```bash
cd /home/wu/hmasd-worktrees/acvc-p79-4e019ca35 && HMASD_PYTHON=/home/wu/.venvs/hmasd/bin/python bash experiments/candidates/acvc/native_link_loss_b01/launch_b02.sh 4e019ca35b930c2216fdfe110ba587e222ca7384 /home/wu/hmasd-inputs/acvc/p79/final_DENSE.pt 5.4396806 3594.5603194
```

The configured `zsh -lic` network shell fetched the committed source with an empty
refmap into FETCH_HEAD (preserving the old remote-tracking prefix conflict), and created
the exact detached checkout. Its unrelated interactive gitstatus warning did not prevent
fetch/checkout; both operations exited 0. No scientific retries or source changes followed.

## Terminal acceptance and accounting

Same supervisor handle finished with exit 0, tmux inactive; task log exit timestamp
`2026-09-09T20:05:07+08:00` (`12:05:07Z`), integer duration 357 s. External `/usr/bin/time`
measured **357.55 s** through actual process exit and **549380 KiB = 0.523930 GiB** peak RSS.
The runner-to-summary versus outer-process difference is **17.5826431 s**, included in
the complete bill rather than omitted as free publication/exit work.

| Complete cost | Seconds |
|---|---:|
| Current focused checks | 5.4396806 |
| Scientific process through exit | 357.55 |
| Logical study / summed serial machine wall | **362.9896806** |
| Shared work charged to both learned arms | 35.8139178 |
| T complete bill | **191.5703530** |
| G complete bill | **207.2332454** |

Both learned arms are below 1800 s, study below 3600 s, and focused checks below 300 s.
The serial machine execution critical path equals the summed machine wall above; human
authoring/review waits, Git/SSH staging and gaps between invocations are outside the card's
machine bill. Aggregate CPU and scratch high-water remain unmeasured, with no claims on
either. The actual summary reports CPU/FP32 and Torch intra/inter-op 1; native geometry
and its single-thread environment are unchanged. Admission is separate from actual wall/RSS.

All six remote scientific artifacts' digests matched their collected copies. Final T/G
checkpoints deserialize with master 8902, correct arm tags, 11425/26306 gate parameters,
and finite gate/critic tensors. The complete local runtime copy, including checkpoints, is
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/exp/native_link_loss_b02_8902_p79_20260909`.
Original P78 runtime and evidence were untouched. The P79 remote worktree/output remains
available for Root's normal integration/reclamation; all scientific bytes have verified
local copies. No live scientific process or observation handover remains.

Published artifacts: [summary](native_link_loss_b02_p79_20260909/summary.json),
[all episode outcomes](native_link_loss_b02_p79_20260909/episodes.jsonl),
[all rollout/update records](native_link_loss_b02_p79_20260909/updates.jsonl),
[collection acceptance and digests](native_link_loss_b02_p79_20260909/collection_acceptance.json),
[admission](native_link_loss_b02_p79_20260909/admission.json),
[external process time](native_link_loss_b02_p79_20260909/process_time.txt),
[supervisor terminal](native_link_loss_b02_p79_20260909/supervisor_terminal.json),
and [complete task log](native_link_loss_b02_p79_20260909/task.log).

Post-collection read-only arithmetic established **1024 training episodes, 128 final
episodes, 1152 scored resets, 4 additional constructor resets, 294912 team steps,
1474560 base agent forwards, 1392640 gate collection agent forwards, 512 rollout records
and 2048 Adam records**. T/G each retain the entire training reset range
890201000–890201511 and all arms retain final reset range 890202000–890202031, in order.
All episode records have 256 steps and S=256J. Every gate aggregate matches its episode
rows. Each paired mean, conditional SE, signed rule and quarter-S condition was recomputed
from its own B02 panel and matched summary. There was no new environment, model fitting,
native diagnostic or evaluation exposure during collection/acceptance.

## Native primary outputs and card rule

Native `S=sum_t r_team[t]`, `J=S/256` remains unchanged. Final arm means:

| Arm | Mean J |
|---|---:|
| T | 0.2239949255 |
| G | 0.2305895069 |
| C | 0.1704037145 |
| F | 0.2782482889 |

Verbatim rule: **UP if mean difference >0.01 J; DOWN if <−0.01 J; otherwise WITHIN**.
The separate inherited test is **mean difference >0.25 S**.

| Fixed contrast | Mean ΔJ | Conditional SE J | Mean ΔS | Rule | >0.25 S |
|---|---:|---:|---:|---|---|
| T−C (primary) | +0.0535912110 | 0.0109472169 | +13.7193500 | UP | yes |
| T−F (primary) | −0.0542533634 | 0.0109171556 | −13.8888610 | DOWN | no |
| T−G | −0.0065945815 | 0.0108858343 | −1.6882129 | WITHIN | no |
| G−C | +0.0601857925 | 0.0113997635 | +15.4075629 | UP | yes |
| G−F | −0.0476587820 | 0.0107632723 | −12.2006482 | DOWN | no |

Primary `min(mean(T−C),mean(T−F))` is **−0.0542533634 J** (−13.8888610 S).
There is no selected-max SE and no episode-wise oracle. Each fixed contrast uses 32 paired
joint episodes conditional on this fitted instance. P78's panels are kept separate; no
pooling, training-population inference or scientific reinterpretation is part of this return.
Every favorable, adverse and within-MEI outcome remains visible.

## Actual gate exposure

| Arm/phase | Opportunities | Apply on opportunity | Retrace | Distinguishable b/c |
|---|---:|---:|---:|---:|
| T train | 50137 | 22816 | 27321 | 50137 |
| T final | 3301 | 1464 | 1837 | 3301 |
| G train | 49920 | 22579 | 27341 | 49920 |
| G final | 3190 | 1486 | 1704 | 3190 |
| F final | 3877 | 0 | 3877 | 3877 |

C does no anchor matching; its zero counter denotes unmeasured opportunities, not proven
absence. C always applies the sampled base command. All ineligible rows in every arm also
apply the base command, outside the eligible-choice counts above. Both learned arms received
1024 Adam updates. Gate and critic movement are measured independently:

| Arm/group | Initial norm | Absolute displacement | Relative displacement |
|---|---:|---:|---:|
| T gate | 9.4158669 | 1.6698216 | 0.1773413 |
| T final projection | 0 | 0.1196913 | undefined |
| T critic | 9.2905779 | 6.9057150 | 0.7433031 |
| G gate | 13.2589827 | 2.2648809 | 0.1708186 |
| G common final projection | 0 | 0.0757322 | undefined |
| G residual final projection | 0 | 0.0952114 | undefined |
| G critic | 9.2905779 | 7.3091612 | 0.7867284 |

All common/residual path norms and movement are retained in summary. Gate movement is
not inferred from critic movement and does not replace the native endpoints.

## Remaining responsibility

This allocated scientific/engineering batch has no remaining technical acceptance gap.
DM owns all-outcome scientific intake and next unallocated recommendation; Root owns
integration and terminal remote worktree reclamation. The previously blocked P78 publication
scratch path remains untouched, with its original CM cleanup ownership and recorded runtime
policy rejection. P79 created no leftover test scratch. No retry, resume, extra native panel,
third instance, tuning, new allocation or Pro Send is implied by this return.
