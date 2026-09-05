# CRTO RAW phase-trace A01 resume R02 attempt evidence

Date: `2026-09-04`

Object: `CRTO-RAW-PHASE-TRACE-A-RECON-R01`

Evidence class: `A/RECON`

Attempt disposition: `INCOMPLETE_NO_SUMMARY / NATIVE_CAUSE_UNREPRODUCED`

Scientific result branch emitted: **none**

Claim ceiling: direct execution and artifact facts for one newly admitted remote attempt. No
checkpoint trace, update-256 reproduction, RAW competence, phase measurement, or residual effect
was observed. The old failed task remains preserved separately.

## Question and protected meaning

The unchanged card is `CRTO_RAW_PHASE_TRACE_A01_SCIENCE_CARD_20260904.md`. It asks for the exact
seed-0 RAW path on the B01 48 TRAIN / 16 EVAL panel at every update `252..264`, with the fixed
CPU FP32 initialization, predictor, cyclic row order, batch 32, Adam law, and update-256 anchor.
The deliberate thirteen-checkpoint EVAL exposure cannot select a held-out comparator. There is
no TRUE/DERANGED arm, confirmation read, residual-effect comparison, or policy/MARL claim.

The recovery authority and prospective object-tier decision are recorded in
`CRTO_RAW_PHASE_TRACE_A01_RESUME_BOUNDARY_20260904.md`. The original prediction remains unchanged
and unscored.

## Source and transport recovery

CM's engineering return is
`CRTO_RAW_PHASE_TRACE_A01_RESUME_ENGINEERING_EVIDENCE_20260904.md`. The fresh local source and
remote launch SHA is `8d1c597871b38edc7d5f139f34f5a3ce2941c7d0`, verified as pushed at
`origin/codex/cm-crto-resume-20260904`. The declared CRTO runtime/core surfaces are unchanged
from accepted implementation `c8247c2d19ac7965208c397a2a87519a1efb6310`.

CM transferred only committed Git objects, not uncommitted source copies. The pack was
`10,330,528` bytes, SHA-256
`70ec056d40b360879d999ad8d2a88ad5bca973d53d6bce0e0572a08ba8edacdd`. The new detached worktree was:

```text
/home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02
```

All `1,954` selected files, including `1,938` configured-surface files, matched Git blobs and
porcelain was empty. The configured file count differs from the historical `1,903` because this
is the later integrated tree, not a changed CRTO scientific surface.

One non-result supervisor task `crto_raw_phase_probe_8d1c5978_r02` finished in one second with
exit 0. Its recorded script preserved the complete single-argument `cd && admit-memory &&
project-cost` payload. Its project-cost output kept the sole-arm projection
`3*434.7066687=1304.1200061` seconds below the `1800`-second cap, emitted all thirteen prospective
exposure lines, and established the technical one-thread contract. Six accepted-source focused
tests passed in `1.72` seconds. These are conformance observations, not a scientific trace.

## One fresh result invocation

The newly accepted task was `crto_raw_phase_a01_8d1c5978_resume_r02`, supervisor PID `73153`,
learner command PID `73156`. Its authoritative script contains this complete payload:

```sh
cd /home/wu/hmasd-worktrees/crto-resume-a01-8d1c5978-r02 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_crto_raw_phase_trace_a01.py run --seed 0 --admission-receipt temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_admission.json --output-dir temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02 --execution-node wsl_4070
```

The remote admission, assessed at `2026-09-04T21:37:51.040763Z`, reported physical and effective
available memory of `15,424,868,352` bytes, both above the `4,294,967,296`-byte floor, with
`passed=true` and no failure reasons. The preflight and runner were joined immediately in the
same task command.

The task log records start `2026-09-05T05:37:50+08:00`, end
`2026-09-05T05:38:08+08:00`, duration `18` seconds, and exit `139`. Its stderr line reports
`73156 Segmentation fault (core dumped)`. Final supervisor state is `failed`,
`tmux_active=false`; the later status field `uptime_seconds=134` is the status-query age, not
the run duration. The new scientific output directory exists but is empty: no `summary.json`,
checkpoint, or other scientific output is present.

Read-only runtime metadata reports Python `3.10.21` built with Clang `22.1.3`, NumPy `1.26.3`,
and Torch `2.7.0+cu118`; the invoked interpreter is `/home/wu/.venvs/hmasd/bin/python`.
WSL CaptureCrash directly names PID `73156`, signal `11`, and the underlying uv-managed
CPython executable. An adjacent kernel excerpt uses PID `74008`; that adjacent instruction
pointer is not independently bound to the CRTO failing step. No local core, `/var/crash`
artifact, or systemd coredump was available for an offline stack diagnosis.

No failing learner step was reproduced. A fresh learner run was outside this bounded intake;
therefore the native-runtime cause remains **provisional**, not classified from stderr.

## Counts, receipts, exposure, and cost

| quantity | direct state |
| --- | --- |
| fresh result tasks accepted in this resume slice | `1` |
| mandatory result admission | passed, one receipt |
| scientific result directory | exists, empty |
| complete summary / checkpoint trace / update-256 anchor | absent / absent / unobserved |
| reconstructed panel rows | unknown |
| predictor tapes / updates / processed examples | unknown / unknown / unknown |
| RAW updates / processed examples / evaluations | unknown / unknown / unknown |
| actual parameter displacement | unobserved |
| TRUE/DERANGED scientific exposure | not authorized or present in the RAW-only source; no completed runtime count receipt |
| confirmation read | excluded by the accepted source; no completed runtime receipt |
| task wall duration | `18` seconds, supervisor observation |
| peak RSS | unmeasured |
| post-acceptance local fallback / additional result launch | none / none |

The single process was observed at RSS `709,756` KiB while running; that sample is not peak RSS.
No zero learner count is inferred from the absent summary. Prospective counts remain
`100*128=12,800` predictor examples, `264*32=8,448` RAW examples, and `13*16=208` EVAL rows,
but none is promoted to an observed count. The original initialization anchors and cost-law
exposure outputs remain planning/technical evidence, not the missing result-path displacement.

The telemetry exception does not make this a valid `resources_unmeasured` result: all mandatory
learner-side result measurements are absent. This is not a failure of the memory floor or wall cap.

## Frozen rule applied verbatim

1. **`A01-RAW-PHASE-TRACE-MEASURED`.** All `64` rows reproduce; the predictor and RAW gate counts
   are nonzero and exact; updates `252..264` each have all `16` EVAL rows and finite exposure;
   every selected action is legal; all G16 values and regrets are finite and nonnegative; and the
   update-256 anchor matches. Report all measurements, including null, unstable, and adverse
   values, without residual polarity or post-hoc checkpoint selection.
2. **`A01-RAW-PHASE-INFORMATION-BOUNDARY-INVALID`.** EVAL actions or G16 values affect predictor
   fitting, RAW training, example order, stopping, checkpoint creation, or selection; an old result
   supplies learner state; TRUE/DERANGED receives learner or evaluation exposure; or the untouched
   confirmation is read. Quarantine the attempt with no path measurement.
3. **`A01-RAW-PHASE-INCOMPLETE`.** Any row is missing/replaced, source semantics change, update or
   evaluation count is missing, action is illegal, learner measurement is absent/nonfinite, the
   update-256 anchor mismatches, mandatory admission fails, or the wall cap stops the run. It has
   no scientific branch. Missing wall/peak-RSS telemetry alone leaves an otherwise valid result
   marked `resources_unmeasured`.

The required rows, counts, displacement, and anchor are unobserved, so the measured predicate is
not established. There is no observed information-boundary violation. The third rule covers the
absent counts and measurements and supplies **no scientific branch**. The runner itself emitted
no result branch. This is an incomplete evidence attempt with no A/B consumption state; it cannot
be interpreted or salvaged as a RAW or residual result.

## Artifacts and direct DM inspection

Remote task root: `/home/wu/.agent-tasks/crto_raw_phase_a01_8d1c5978_resume_r02/`.
Remote output root: the relative `resume_r02` directory in the exact command above.
Local byte-preserving copies inspected by the DM are under:

```text
C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/resume_r02_artifacts/
```

| artifact | bytes | SHA-256 |
| --- | ---: | --- |
| `runner.sh` | 1686 | `904d935f00785349c61718ec98fd84b7d178dd103365dab9b93500ceb9b58fff` |
| `task.log` | 1470 | `be94234da279be9712b58a822ffbf420d769f26f5156a864a187ed9e828bef50` |
| `admission.json` | 504 | `fe1029e1bee859bc6e90a23ab0489e60adbc01f55f077a8bfb6a19ec1f53f709` |
| `status.json` | 148 | `2e07d2dd4494a136016c4ca9d0f53522f7ff952c1f472085343dad089d8f502d` |
| `root_listing.txt` | 87 | `32e73efeb12689d2385c3d5fa8589609587b7b1f9858a89e99a73a9d9c2e31ad` |

The same directory retains the old/probe scripts and logs, dependency metadata, and kernel
excerpt. The old task's script/log digests still match the previously archived failed attempt.
No old artifact, failed result directory, or committed source was deleted or overwritten.

## Bounded engineering reading and next discriminator

Exact-source sparse materialization and joined-command transport are now established on the
configured node; they no longer explain this attempt's lack of a trace. The unresolved dependency
is the native-runtime failure before result publication, at a step not yet localized. No code or
scientific semantics changed and no engineering-scope item was added.

The accepted toy E2E profile does not exercise publication with the formal constants; this remains
an open engineering item. The present failure has not been localized before or after the learner.
If reproduction places it after the learner, the repository's offline publication-path check and
formal-path test obligation apply before a fresh attempt.

The next operational discriminator is a separately bounded, freshly admitted reproduction of the
recorded path on the same runtime with crash-location output, for example external Python
faulthandler. That diagnostic must retain source, numerical, RNG, and card meaning and use a new
task/output identity if it invokes the learner. It is recommended, not launched in this slice.
The next scientific discriminator remains the original complete RAW trace.
