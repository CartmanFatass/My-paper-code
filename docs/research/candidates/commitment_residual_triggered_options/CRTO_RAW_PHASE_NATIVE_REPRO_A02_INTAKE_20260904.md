# CRTO native-reproduction A02 intake

Date: `2026-09-04`. Object: `CRTO-RAW-PHASE-NATIVE-REPRO-A02`. Class: `A/RECON`.

Disposition: **`A02-NO-FAULT-WITHIN-BOUND` — normal completion**, accepted only as a technical
path observation. The original R02 attempt remains incomplete and its native cause unlocalized.

## What this intake checked

I compared the A02 card with CM's exact-source/runtime/admission and terminal return, then directly
read the preserved summary's technical fields and artifact hashes. Source is the same pushed
`8d1c597871b38edc7d5f139f34f5a3ce2941c7d0`, runtime Python 3.10.21 / NumPy 1.26.3 / Torch
2.7.0+cu118, CPU FP32 with one intra/inter-op thread. The authoritative task script includes
the external `timeout --signal=KILL 90s` and Python `-X faulthandler`; the summary's script argv
omits the interpreter flag because Python strips it. The actual script is the execution authority.

Task `crto_raw_phase_native_repro_a02_8d1c5978_01` completed with exit 0 at
`2026-09-04T21:52:18Z`, after 85 supervisor seconds, before the external limit. No fatal stack was
printed. Admission at `21:50:53.773859Z` reported physical/effective availability of
`12,920,348,672` bytes and was 0.895226 seconds old when accepted.

The 303,260-byte summary has SHA-256
`0d9319231c55775568e1d374e2968741a4edc765ebdfd9067e4a9211845ab8f7`, matching the remote copy.
Local raw files are under
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01_artifacts/`.

Printed counts are predictor tapes/examples/updates/processed examples
`128/32,256/100/12,800`, environment transitions `38,464`, common-future branch steps `3,520`,
RAW updates/examples `264/8,448`, snapshots `13`, and checkpoint-evaluation rows `208`.
Forbidden representation counts are zero. There are thirteen finite positive displacement lines.
Measured invocation wall is `80.505860614001` seconds and peak RSS `1,276,755,968` bytes.
This is completion evidence, not phase or residual interpretation.

The card's applicable rule, verbatim, is:

> **`A02-NO-FAULT-WITHIN-BOUND`**: no signal-11 event occurs before normal completion or the
> external 90-second stop. Report which endpoint occurred. This neither clears R02 nor establishes
> that the full scientific path is reliable.

The normal-completion endpoint matches. The other branches require signal 11 or an incomplete
diagnostic, neither observed here. The DM predicted fault recurrence with a location; that
prediction was not supported. The owner prediction is `not taken (unattended)`.

## Observation that bounds the result

One invocation with fault reporting completed and produced the fixed runner's full output before
the cap. The strongest support for the narrow conclusion is the complete summary plus terminal
task evidence. Its strongest contradiction to a broad reliability claim is the immediately prior
same-source R02 SIGSEGV. Fault reporting changes signal handling and may affect timing; load and
process state also differ. No evidence identifies which difference explains the contrast.

The A02 card explicitly reserves an unexpected summary as technical evidence. This intake does
not promote it to an A01 result, declare the original failed task successful, or read its phase
metrics. No code/runtime repair occurred. The completed formal invocation exercised publication,
but the existing toy E2E test profile still does not cover the full formal constants.

## Flags for the owner

The original A01 prediction stays unscored. A02's different technical prediction is scored above.
No residual, competence, safety, stable runtime, or deployment claim follows. No engineering-scope
item was added. The A/RECON object has no consumption state. Owner reviews returned `[]` at this
boundary; the owner surfaces contain no CRTO override.

## Decisions this intake produces

Options: **(a)** accept the declared A02 normal-completion/no-fault observation while preserving R02
and the diagnostic identity; **(b)** label the original failed A01 task successful; **(c)** repeat
the learner to seek another crash. Recommendation: **(a)**. The preserved bytes decide the
technical question, and another learner invocation is unnecessary for this intake.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Object tier, technical,
reversible. No Direction- or Portfolio-tier decision is made, and `DIRECTION.md` is unchanged.

Root subsequently instructed the DM to assess a separately named A/RECON reading of the already
complete RAW artifact under standing object-tier delegation if the common integrity and original
RAW-only question permit it. That is the cheapest next scientific discriminator: read the existing
thirteen-checkpoint artifact with diagnostic provenance explicit, without new learner exposure,
checkpoint selection, or retroactive relabeling of R02/A02. Its separate card and decision precede
the metric reading.
