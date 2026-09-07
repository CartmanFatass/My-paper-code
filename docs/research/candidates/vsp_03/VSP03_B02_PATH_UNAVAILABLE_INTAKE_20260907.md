# VSP03 B02 intake — configured path unavailable before launch

**2026-09-07; P09-VSP03-SELECTED-B02-01; object-tier technical intake.** Source and independent review are accepted at published SHA `00ebefa5823dbb41e64aed11b90ba26a8ff97020`. The configured SSH operation failed before connection. B02 has no launched invocation, accepted handle, resource admission or scientific result. Its primary is **unmeasured**, with no positive or negative polarity. No object family is closed, no second recast occurs, and no Portfolio lifecycle or sequencing decision is made.

## What this intake checked

- The [technical E0](VSP03_B02_RESULT_EVIDENCE_20260907.md) against the frozen card's [Counts, complete cost and stop](VSP03_B02_SCIENCE_CARD_20260907.md#counts-complete-cost-and-stop) and [Implementation, review and execution boundary](VSP03_B02_SCIENCE_CARD_20260907.md#implementation-review-and-execution-boundary).
- The [raw CM command/result receipt](VSP03_B02_REMOTE_PATH_RECEIPT_20260907.json), including command, local cwd, exit, elapsed time and the absence of any supervisor launch request. DM inspected the recorded output; CM directly observed the operation. Root supplied the same command/error and directed no retry until external route state changes. Root's relayed report is not counted as another independent access observation.
- The accepted [source record](VSP03_B02_SOURCE_ACCEPTANCE_20260907.md) and [independent review](VSP03_B02_SOURCE_REVIEW_20260907.md), previously inspected at the source boundary. No tests, model construction, environment execution or SSH operation were repeated for this intake.
- Root's publication report and the corresponding local commit. The frozen card, RNG realization, selected counts and source bytes remain unchanged. The [dispatch handoff](VSP03_B02_DISPATCH_HANDOFF_20260907.md) is explicitly superseded before dispatch; its commands are unexecuted context.
- Owner review command returned `no unapplied owner instructions` at this boundary; relevant VSP03 audit owner columns were empty. Existing P2 [new-card item 20260907-vsp03-002](../../portfolio/owner/inbox/2026-09-07/20260907-vsp03-002.json) and first-recast item remain in force. This routine technical intake creates no separate owner item.

The directly recorded operation was:

```text
cwd: C:/Projects/HMASD
ssh -o BatchMode=yes -o ConnectTimeout=10 hmasd-wsl-node '/usr/local/bin/agent-task --help'
exit_code: 1
wall_time_seconds: 2.914331
ssh: Could not resolve hostname hmasd-wsl-node: No such host is known.
```

This was supervisor-help discovery. It neither requested nor accepted a B02 launch. The error establishes failure to resolve this hostname in that local SSH operation; it does not establish that the remote computer, Python environment, GPU or supervisor is unhealthy. The cause beyond the recorded error remains undetermined. No remote files were inspected or created by this operation, and no admission, supervisor receipt, process log or result output exists for it. The receipt above is a local record of the tool return, not a remote admission or run receipt.

## Counts, receipts and exposure

| Quantity | Frozen plan | Actual at this boundary |
| --- | ---: | ---: |
| Paired training instances | 1, seed 4 | 0 |
| Learner constructions | 2, T and G | 0 |
| Training joint episodes | 32768 | 0 |
| Final evaluation joint episodes | 6144, six modes/references | 0 |
| Focused-check joint episodes | 8, inside the sole invocation | 0 |
| Complete joint episodes | 38920 | 0 |
| Team ticks / target transitions | 1556800 / 3113600 | 0 / 0 |
| Adam optimizer steps | 256, 128 per arm | 0 |
| Result-bearing invocations | 1, complete cap 120 seconds | 0 |

The [machine-computed counts](VSP03_B02_COUNTS_20260907.json) remain prospective. New scientific exposure is zero models, episodes, transitions, learner updates and evaluations. No seed was consumed or replaced. A and B objects have no C consumption state.

Proposed handle `vsp03-b02-p09-20260907` remains unaccepted. The proposed remote worktree and output/admission paths remain those in the launch boundary; no observation adoption ACK is needed without an accepted process. There is no B02 complete wall, peak RSS, aggregate CPU or learner displacement measurement. The 2.914331-second SSH observation is control-plane access time, not scientific invocation time. This is `not_launched`, rather than a valid run with `resources_unmeasured`.

The single complete 120-second cap and all selected work remain intact. N2 unit and per-arm wall costs remain unknown. The historical 23.62029694-second whole-pair planning anchor is unchanged and does not become a per-arm estimate or a measured N2 upper. No calibration, pilot, partial training, separate R0 call or alternate-node attempt was made.

## Scientific reading and predictions

The frozen reading rule is retained verbatim:

> Reading rule: apply final greedy T−R as primary; retain R0 and G interpretations and every opposite-sign stochastic result. T above R and R0 exceeds these selected fixed references on this sample; T−G addresses initialization. G above both rules with small T−G supports ordinary scheduling learning. T>G without beating rules remains a local initialization/configuration difference. T>R but T≤R0 retains the explanation that R is weak or initial readiness already suffices. Rules matching/exceeding learners weaken this configuration at this budget, not the whole direction. G's complete non-submission limits a strong generic-comparator claim without erasing an independently sound learned-versus-rule fact.

No branch can be applied because none of the six final means or the primary paired differences exists. The result does not support a local gain, local loss, equivalence, comparator failure or any learner conclusion. Evidence-spec §11.8.6 requires the real learner and readable primary comparison; §11.8.7 limits a dependent claim when its measurement is absent. A failed access path is not evidence about the scientific mechanism.

The card's MEI remains 0.02 absolute team-return units. The prospective DM event `abs(final greedy T−G) <= 0.02`, low confidence, is **not scored: no outcome**. The absent result is not a failed prediction. Owner prediction is **not taken (unattended)**; no reply was present to score.

The intended independent unit remains one paired training instance. The B claim ceiling remains a local fixed-N=2 comparison at the stated budget, with conditional evaluation uncertainty only; this boundary reaches no empirical claim. N2 tuned headroom remains absent. Strongest support for the selected question remains the specified shared-slot loss of partner opportunities. Strongest empirical contradiction remains the three historical N1 final T=G=F observations. The alternatives that ordinary G, R or R0 suffice, or that readiness initialization submits too early, survive unchanged. No new retrieval is needed to classify an access error; the accepted local-library evidence and mechanism selection are unchanged.

## Engineering conformance and owner flags

Accepted source totals are 422 non-test lines, including a 28-line runner; this object requested none of ENGINEERING_SCOPE_SPEC §4's optional machinery. No section 5 source budget breach was identified. Three zero-trajectory helper checks passed in 4.57 seconds using local Conda `hmasd-amd-cpu`; independent source review found no material issue. Root's separate Windows interpreter lacking NumPy was a distinct collection failure, not a remote result or a reversal of the accepted helper evidence. No duplicate check followed it.

Runtime conformance, the in-invocation eight-episode check, real learner exposure, complete counts, publication/readback and the 120-second complete-process bound remain untested. Source acceptance is not runtime acceptance or scientific value. There is no damaged result to quarantine and no uncertainty about experiment acceptance: the sole observed operation did not request a launch.

Owner flags: `none`. There is no close call, material critic dissent, second recast or Portfolio recommendation about investment. The [Chinese owner brief](../../portfolio/owner/briefs/vsp_03/2026-09-07_VSP03_B02_PATH_UNAVAILABLE.md) explicitly reports the absence of a scientific result.

## Decisions this intake produces

1. **Object-tier technical classification.** Options: (a) accept the recorded pre-acceptance `PATH_UNAVAILABLE` boundary with the primary unmeasured; (b) return a concrete mismatch between E0, receipt or acceptance facts before classification. Recommendation and selected option: **(a)**; no mismatch was found. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This decision preserves the current card and all source evidence and is recorded in the shared audit ledger.
2. **Current execution boundary.** Options: (a) retain the unstarted invocation and make no further remote attempt until the configured route's external state changes; (b) request a different node, local fallback or changed scientific scope. Recommendation and selected option: **(a)**, as explicitly directed by Root after the observed error and required by the current launch boundary. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** No retry, alternate route, second invocation or different comparison is commissioned. This is a technical stop at the current task boundary, not a direction-tier PARK or recast.

The next discriminator remains the selected real seed-4 B02 comparison: final greedy T−R, interpreted alongside T−R0, T−G and all selected modes. Return the concrete dependency through Root to Portfolio: restoration of the configured access route, then continuation of the still-unstarted sole invocation with the same card and published source, fresh adjacent destination admission, existing complete cap and same CM for technical collection. This intake does not choose a new research task, launch a follow-up or ask Root to interpret scientific polarity.
