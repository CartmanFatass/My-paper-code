# B02 incomplete-attempt evidence — 2026-09-11

The one accepted INTERVAL/TERMINAL invocation terminated by signal 11 before the
round-64 comparison. No primary recovery score, native tradeoff, learning gain or
scientific polarity is available. Its recorded partial optimizer progress and cost
remain reportable; this is not a complete B/EXPLORE result.

## Bound inputs and rule applied verbatim

Object: [VNFC-N7-NATIVE-SERVICE-CREDIT-B02](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_SCIENCE_CARD_20260911.md).
Conforming direction selection: response `10bb08476ff58afd25b90b21cd2d1a739b25ca4b`,
[re-entry intake section 9](VNFC_NATIVE_SERVICE_CREDIT_REENTRY_INTAKE_20260910.md#9-reconciled-full-response-and-direction-decision--2026-09-11).
Source `76d4afca664f988fbaabca2923a0c891f8a784ff`; exact supervisor command committed at
`8dc043f2f16a1e627f3ed5cb2cf6a43ce07d623f`. Training/evaluation seeds
`2026091101`/`2026091102`, namespace `VNFC-N7-NATIVE-SERVICE-CREDIT-B02-20260911`.
One pair was started, no pair has a complete primary. CPU float64, one computation
thread, configured node `wsl_4070`; no fallback, restart or source substitution.

Card: "Primary: mean paired final `INTERVAL - TERMINAL R_fail_60` over all 64 worlds."
Its reading rule states: "Any invalid primary limits only its dependent claim; credible
partial facts remain. All outcomes end this allocation."

Evidence specification §11.8.7: "A damaged primary measurement cannot support its
dependent performance claim; independently trustworthy narrower facts remain reportable."
The same section requires direct evidence for root-cause attribution. The missing
primary invokes this dependency rule; none of the card's four performance branches
can be evaluated. This B has no C-style consumption state; its named one-invocation
allocation ends under its existing rule and Root's no-retry collection assignment.

## Terminal receipt and preserved bytes

Handle `vnfc-b02-credit-20260911-01`; detached cwd
`/home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01`; output relative to that cwd
`temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01`.
Supervisor records are in `/home/wu/.agent-tasks/vnfc-b02-credit-20260911-01/`.
Actual Monitor adoption was already recorded in the [execution record](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_EXECUTION_20260911.md).
Root routed its terminal fact back to this DM; the DM performed collection without
restarting the experiment or becoming a routine second observer.

The [complete retained log](evidence/b02_credit_20260911_01/task.log) reports start
`2026-09-12T02:26:51+08:00`, terminal `2026-09-12T02:28:09+08:00`, duration 78 s,
`failed`, exit 139. Collection observed inactive tmux. Supervisor uptime at a later
status read is time since dispatch, not experiment wall. The [outer timer](evidence/b02_credit_20260911_01/outer_time.txt)
reports signal 11, **77.84 elapsed seconds**, peak RSS **768,712 KiB = 787,161,088 bytes**.
Its `exit_status=0` field does not supersede signal termination and supervisor exit139.
The timeout's "monitored command dumped core" message is not proof of cap expiration
or a root cause. No `core*` file was observed at the checkout root; global WSL crash
stores were not searched and are not claimed absent.

Destination [memory admission](evidence/b02_credit_20260911_01/memory.json) passed at
`2026-09-11T18:26:52.030302Z`: physical/effective available **15,636,619,264 bytes**,
floor **4,294,967,296 bytes**, source `/proc/meminfo`. It ran immediately before the
timed invocation in the same supervisor command joined by `&&`.

[Raw archive](evidence/b02_credit_20260911_01/raw_artifacts.tgz): 1,416,174 bytes,
SHA256 `1bbcfbe499e8a15bb1d5f4a0d4fdaf0fa8a52feda65da4de4f2f3e2abc575de5`.
Remote `/home/wu/hmasd-inputs/vnfc_b02_partial_20260911.tgz` and the local copy
matched by SHA256. [Collection receipt](evidence/b02_credit_20260911_01/collection.json)
lists all 11 archived files and their individual sizes/digests: two initial checkpoints,
the built native library, admission/time files and six supervisor files. Both initial
checkpoints are 722,421 bytes; the library is 133,704 bytes. They were retained opaquely;
collection did not deserialize checkpoints, load the library or run a model/environment.

The output root contains no summary, training curve, training episode or evaluation
episode JSON, and no midpoint/final checkpoint for either arm. The source publishes
the four JSON documents after both complete learners; scores held only in the terminated
process are unavailable. Two initial checkpoints do not recover a trained comparison.

## Recorded counts and the narrower source-derived inference

Python standard-library parsing of the 15 JSON progress lines produced
[progress.json](evidence/b02_credit_20260911_01/progress.json). Every line records
192 joint training transitions, 32 optimizer steps and 89,090 parameters. The recorded
rounds are consecutive, with no duplicate or omitted round inside each retained sequence.

| Arm | Last logged round | Logged joint transitions | Logged optimizer steps | Implied completed training episodes | Last displacement / initial L2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| INTERVAL | 8 | 1,536 | 256 | 256 | .1473240979506232 |
| TERMINAL | 7 | 1,344 | 224 | 224 | .11922778762530933 |
| Combined | 15 arm-rounds | 2,880 | 480 | 480 | not an arm comparison |

INTERVAL's last logged parameter norm/displacement is 33.89976303834544 /
4.908347691424163; TERMINAL's is 33.72390513345533 / 3.9722723185478834.
These are nonzero parameter-movement facts at different incomplete training depths.
They do not measure return improvement or justify an INTERVAL advantage.

The bound `variable_n_fleet_churn_n7_direct_b01/experiment.py` executes fixed BCRH64
and both initial 64-episode evaluations before the first training round. A progress line
is flushed only after rollout, credit construction, PPO and parameter-state recording.
The unchanged collector has six joint decisions per complete episode, and the unchanged
update makes one backward call per reported optimizer step. Hence the retained lines
and control flow imply **at least 480 completed training episodes, 128 initial policy
evaluation episodes, 64 fixed-reference episodes, 480 backward calls and 384 full BCRH
calls**. The implied complete-episode lower bound is **672**, or **161,280 native ticks**
including 120 prehistory plus 120 post-loss ticks per episode.

These evaluation/backward/tick counts are control-flow inferences, not reconciliations
of surviving episode, gradient or counter arrays. Their scores and arrays were not
published. Source ordering also implies that the credit endpoint/freeze/telescoping
assertions returned for the logged training rounds; collection cannot independently
reconcile the missing numerical counter rows or report their residuals. Unlogged work
may add exposure; no exact final exposure total or last crash-stage identification is
claimed. Planned totals remain 4,544 episodes / 1,090,560 ticks / 4,096 optimizer steps,
and are not substituted for these observed lower bounds.

## Technical acceptance, cost and deviations

Prelaunch source acceptance, focused synthetic checks and independent high-risk review
remain as recorded. The actual run demonstrates partial native/learner execution and
initial publication. It fails the card's complete-exposure and primary-publication
acceptance. There is no numerical final INTERVAL−TERMINAL, final−initial, BCRH difference,
J/intact/zone tradeoff, safety count, conditional SE or MEI classification to accept.
No defect was repaired or reproduced in collection; signal text alone does not identify
whether Python, Torch, native code, an interaction or another component caused the crash.

77.84 s is within the 600 s native cap and includes scientific-process exit. No timeout
or Engineering Scope §5 line-budget breach is observed. New source remains157 non-test
lines, including the35-line runner; no new §4 machinery was added. The original per-arm
cost formula remains intact, but actual per-arm timings were not published. Historical
400.2884091133 s planning cost is not an actual measurement or successful completion.

[Support accounting](evidence/b02_credit_20260911_01/support_costs.json) separates selected
documented components, Root's approximations, nested alternative clocks and missing costs.
At first collection publication the documented components sum to95.1463868 s, with a
further approximate3.7 s Root preparation receipt (approximately98.8463868 s together).
Later closeout entries are appended in that file. The shared1.3 s RCLE+VNFC terminal
query is charged only to RCLE per Root, while VNFC's1.0 s adoption is included here.
Other preparation/admission/Monitor/tracking work is incompletely timed; these values
are not a complete support total. **Full 300 s support /900 s combined conformance is
unestablished**, not silently accepted or classified as a measured breach. Aggregate CPU
work is unmeasured. There is no valid-result cost denominator and no remaining runtime
balance authorizing a second attempt.

## Preservation and cleanup inventory

Unique unpublished TASK/HANDOFF draft, exact source-staging bundle and synthetic test
summary are also preserved in [local_recovery.tgz](evidence/b02_credit_20260911_01/local_recovery.tgz),
with each byte stream compared to its source and indexed in
[local_recovery_manifest.json](evidence/b02_credit_20260911_01/local_recovery_manifest.json).
The draft was never submitted and the synthetic summary is not scientific evidence.
Reviewed source is retained at the published launch SHA and in that bundle.

| Surface | Collection state and ownership |
| --- | --- |
| Remote exact execution checkout above | Terminal; archive preserved. DM removes after Root integrates/accepts this evidence, then verifies disk and Git-registration absence. |
| Remote input files `vnfc_b02_76d4afca6.bundle`, `vnfc_b02_partial_20260911.tgz` | DM staging copies; source/evidence preserved. Same retention acceptance precedes removal. |
| Remote supervisor directory | All six files archived; retain the small terminal handle record unless Root includes it in reclamation. |
| Local `source_staging/b02_76d4afca6.bundle` and `pro_authoring/20260910_native_service_credit_draft01/` | DM-owned; contents preserved in local recovery archive. Cleanup status recorded at closeout. |
| Local `test/b02_credit_20260911_01/test_primary_round_tradeoffs_p0/summary.json` | Creator-owned synthetic scratch remains. Prior PowerShell cleanup was rejected before execution with `blocked by policy`; no bypass or repeated deletion attempt. |
| Shared `C:/Projects/HMASD-worktrees/codex-vnfc`, branch `codex/vnfc` | Retained for this intake/cleanup; Root owns later shared-direction reclamation. No unrelated or active checkout is removed. |

All local relative cleanup paths above are under
`temp/directions/variable_n_fleet_churn/`. Integration acceptance and verified deletion
facts are recorded in the execution record's terminal closeout section when available.
