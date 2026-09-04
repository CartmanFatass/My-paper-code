# EOCIV-B10 receiver-credit frozen-score exposure curve — DM intake

- Direction: `eociv_lite`
- Object: `EOCIV-B10-RECEIVER-CREDIT-FROZEN-SCORE-EXPOSURE-CURVE`
- Evidence class / claim ceiling: **B/EXPLORE**, fixed-vector exposure on the frozen
  three-initialization, three-profile, eight-root toy population
- Result branch: **`B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED`**
- Intake date: 2026-09-04

## What I checked

I compared the sole full `summary.json` against the prospectively committed card, the exact
36-coordinate manifest and the corrective `PRO_FINAL — CONTINUE` response. The card/manifest were
pushed at `bb1e7d66`; implementation and technical acceptance were pushed at `6fece582`; the same
implementation bytes were integrated on this DM branch at `d745bbb72`. The CM worktree and branch
were clean and upstream-synchronized before launch.

Independent review found two prelaunch engineering issues: the smoke had been labelled as B
evidence, and the summary carried an unrequested wall-per-Adam derived telemetry field. Both were
removed; follow-up review found no material issue. The final implementation is 782 production
physical lines with a 46-line runner and conservative orchestration `208/703 = 29.59%`. It adds no
§4 machinery beyond the already committed carded static manifest and breaches no §5 budget.

Immediately before the only result invocation, the fresh receipt passed with physical and
effective available memory both `4,927,365,120` bytes. The hidden detached process exited `0`,
printed only the frozen branch, left stderr empty and wrote one complete summary. I checked the
exact command and launch SHA, all required counts, `common_trajectory_and_complete_score_identity`,
the three 12-trajectory/288-term common batches, six pre-mutation gradient computations, zero
recomputations, six paired unchanged-actor/empty-Adam facts, all 96 fixed-gradient step rows, value
invariance, actual displacement, 72 matched cells, global/initialization/leave-one aggregates,
resource telemetry and publication.

I then applied the frozen rule in order. `INVALID_ATTEMPT` does not apply. The terminal edge branch
fails on multiple independent clauses: global `Delta_R16<0`; A0 and A2 `Delta_R16<0`; A0 `J_16<0`;
every leave-one-profile/root `Delta_R16<0`; global and A0/A2 `R16-v0<0`; and A0 `R16-vS<0`.
Therefore every valid-result condition for
`B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED` is met. The `m=1` and `m=4` evidence was retained
and did not select, rerun or rescue the terminal branch.

## Observation that bounds the result

Direct observation: the fixed receiver-gradient intervention reached the intended cumulative
exposure, but did not become a robust or absolute native semantic edge. Globally, as `m` increased
from 1 to 4 to 16, `J` increased from `0.0004073653` to `0.0015616835` to `0.0049095036`, while
`Delta_R` became more negative (`-0.0001466050`, `-0.0006137633`, `-0.0022498172`) and receiver
CORRECT versus unchanged became more negative (`-0.0004184196`, `-0.0016652472`,
`-0.0065118308`). The source arm at `m=16` was harmed even more (`S16-v0=-0.0083092915`), explaining
the positive relative receiver contrast without establishing receiver value.

A1 is the strongest positive local observation: at `m=16`, `Delta_R16=0.0008574619`,
`J_16=0.0088780254`, `R16-v0=0.0000219287` and `R16-vS=0.0015495348`. A0 reverses `J_16` and
`Delta_R16`; A2 has `J_16=0.0126124339` but negative `Delta_R16` and
`R16-v0=-0.0073048683`. Every leave-one `Delta_R16` is negative.

Bounded reading: increased fixed-vector exposure amplifies receiver-versus-source differentiation,
but primarily against a more damaged source control and with strong initialization dependence. It
does not rescue the B9R1 receiver-addressed effect under the prospective absolute and robustness
requirements.

Strongest support: A1 satisfies every terminal initialization-level sign and absolute guard and
the global relative contrast increases with exposure. Strongest contradiction: negative global and
all leave-one `Delta_R16`, negative global absolute receiver reward, the A0 relative reversal, and
A2 absolute harm. Surviving alternatives outside this consumed question include endogenous
on-policy co-adaptation or genuinely new evidence about another mechanism, neither of which B10
tests or authorizes.

## Predictions

The DM predicted `B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED`; the prediction was borne out. The
prediction also anticipated that A1 relative `J` might persist while the cross-initialization
absolute/robust conjunction failed. Owner prediction was `not taken (unattended)`.

## Flags for the owner

- This is a valid complete B result with no consumption state; only C objects consume.
- Positive `J` is not receiver value when receiver absolute reward is negative and the source arm
  is harmed more.
- A1 is a real bounded positive local observation and must not be erased by the global branch; it
  is insufficient for the frozen robust claim.
- The `PRO_FINAL` response already decided the valid-falsifier consequence: park the
  receiver-addressed credit family at B/EXPLORE pending genuinely new evidence.
- That park does not close `eociv_lite`, change Portfolio lifecycle/priority/capacity, or transfer
  polarity to CBSC.
- The local full was accepted and completed before the subsequent `REMOTE_FIRST` routing update;
  it is not duplicated or migrated. No new result-bearing invocation is planned.

## Decisions this intake produces

### Decision 1 — accept the completed result (object tier)

Options:

- (a) accept the complete summary as the valid B10 result and publish the frozen falsifier branch;
- (b) quarantine it because the result is negative despite passing every integrity condition;
- (c) rerun, select `m=1/4`, or add seeds to seek a favorable branch.

Recommendation: **(a)**. The attempt conforms to the card, and result polarity is never a
quarantine condition. Options (b) and (c) would rewrite or evade the prospective rule.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. Reversible at the next clean boundary if the owner fills the audit override.
The B object completes without a consumption label and without a rerun.

### Decision 2 — execute the contingent family disposition (direction tier)

The corrective full convergence response prospectively decided that a valid failure of the B10
terminal edge rule **parks the receiver-addressed credit family at B/EXPLORE pending genuinely new
evidence**. B10 is such a valid falsifier. This intake executes that decision unchanged with
provenance `PRO_FINAL`; it does not solicit or substitute a local direction judgment.

The park boundary excludes same-object repetition, favorable endpoint/seed/root selection, an
ordinary adaptive curve justified only by this result, and transfer to CBSC. It does not park or
close the whole `eociv_lite` direction. Any choice of a different direction-local mechanism or any
Portfolio lifecycle action remains outside this intake and returns to Root.

## Evidence paths

- Card:
  `docs/research/candidates/eociv_lite/EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_SCIENCE_CARD_20260904.md`
- Full result evidence:
  `docs/research/candidates/eociv_lite/EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_RESULT_EVIDENCE_20260904.md`
- Complete durable result:
  `docs/research/candidates/eociv_lite/EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_RESULT.json`
- Convergence response:
  `docs/research/candidates/eociv_lite/external/2026-09-04-eociv-b9r1-convergence-01/PRO_RESPONSE_FULL_RECOVERY.md`
- Runtime summary:
  `temp/directions/eociv_lite/exp/b10_20260904_01/summary.json`
- Implementation launch SHA: `6fece58293f7e1f02ad678adcd8321132c415193`

