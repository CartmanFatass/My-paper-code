# FRRIE r04 reconstruction A01 result evidence — 2026-09-04

**The unchanged full production chain completed through 128 paired updates without the recorded
r04 serialization fault. This is an A/RECON observation; r04's cause remains unresolved.**

Object `FRRIE-R04-RECONSTRUCTION-A01-20260904`; frozen card
`FRRIE_R04_RECONSTRUCTION_A01_SCIENCE_CARD_20260904.md` at
`43a67cb1be0b06c02859e6dcf024d9f4495fc602`. Exact invocation, verification, adoption and raw
artifact locations are in `FRRIE_R04_RECONSTRUCTION_A01_CM_RECORD_20260904.md`. Compact
machine-readable execution facts are in the adjacent `FRRIE_R04_RECONSTRUCTION_A01_RESULT_EVIDENCE_20260904.json`.

## Rule applied and observation boundary

The first matching card branch is:

> `A01_NO_FAULT_WITHIN_BOUND`: the original path reaches normal completion or the declared deadline
> without the recorded fault. State the actual reached boundary; r04 is not exonerated or repaired.

The actual boundary was **natural completion**, not the deadline. Admission, source/node and
fixed execution semantics were preserved. No original exception occurred; matching-signature
frame capture is therefore not applicable, not missing required capture. The original runner
reports `The program exited via sys.exit(). Exit status: 0`; the separate debugger/supervisor
also exits 0. Fixed pdb queries after normal exit report absent r04-specific locals before the
first script statement, exactly as in the verified lifecycle test. Those query errors are not
learner failures. No second learner computation, retry, repair or attempt05 was performed.

## Direct counts and resources

| Quantity | Observation |
| --- | --- |
| Node / dtype | `wsl_4070`, configured Python 3.10, CPU FP32, one torch thread |
| Launch source | `b41a6ba779e514937e35c9b0c1dbc69a50ec68d5` |
| Task | `frrie_r04_reconstruction_a01_b41a6ba7` |
| Start / end UTC | 2026-09-05 00:05:30 / 00:20:57 |
| Supervisor / runner wall | 927 / 902.2496755629982 seconds |
| Maximum boundary | 1800 seconds plus 5 seconds kill grace; not reached |
| Admission physical / effective bytes | 12,857,679,872 / 12,857,679,872 |
| Peak RSS bytes | 615,354,368, measured by the unchanged runner |
| Paired updates | 128 |
| Adam steps / backward calls per arm | 128 / 128 |
| Factual training episodes per arm | 8,192 |
| Factual learner transitions per arm | 98,304 |
| Training native slots per arm | 630,784 |
| Learned evaluation episodes / slots per arm | 2,048 / 24,576 |
| Total evaluation episodes, including shared uniform | 4,608 |
| Completion checks | 22 of 22 true |
| Original summary bytes | 118,881 |

PHY and EDGE attributed wall are respectively 160.52530051894428 and 160.3020884220823 seconds;
the total includes additional shared work. This was one diagnostic, not a sweep or throughput
claim. Its 927 seconds are diagnostic usage, not usage per accepted B result. The historical
733-second failure was the prospective cost anchor; it was not used to infer completed work.
Scratch usage is not measured; the non-resource diagnostic remains valid at its stated ceiling.

Literal seed/root, arm boxes and native/RNG chain remain unchanged. The summary records seed 1,
label `FRRIE-B02-CONTACT-BLOCK-001`, root
`2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`, and exposure:

`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`.

## Scope, limitations and next handoff

Production source diff is zero against the recorded r04 surface. The only implementation
additions are six stdlib test-fixture lines and nine fixed existing-debugger input lines; the
card explicitly names exception-state telemetry. There is no new research framework or
orchestration. One two-case lifecycle check passed before launch; no test was repeated afterward.

Raw supervisor/admission/summary artifacts remain on the accepted remote node and as byte
copies in the CM collection directory. No failed evidence or native artifact was deleted.
The one temporary SSH observation loss was resolved by one read-only reconnect and did not alter
the supervisor or deadline.

Native return/gap fields and the unchanged runner's B branch were not used for this intake.
The diagnostic does not retroactively salvage r04 or become a valid B result. Nonrecurrence
does not identify a transient fault or exclude source/input, process-state, native or interpreter
causes. Attempt02's TypeError remains a separate unresolved event. Original process state is
still unavailable. Real publication completed here, but formal-sized end-to-end test coverage
remains unrecorded. DM owns prediction scoring and any next diagnostic/scientific selection;
CM has launched no follow-on operation.
