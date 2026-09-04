# EOCIV-B9R1 receiver-addressed credit — DM intake

- Direction: `eociv_lite`
- Object: `EOCIV-B9R1-RECEIVER-ADDRESSED-CREDIT`
- Evidence class / claim ceiling: **B/EXPLORE**, immediate one-step total effect on the frozen
  two-anchor, three-profile, eight-root toy population
- Result branch: **`B9R1_GENERIC_OR_SOURCE_HARM_ONLY`**
- Intake date: 2026-09-04

## What I checked

I compared the sole full `summary.json` against every item frozen in the prospective science card.
The card and first object-tier selection were committed and pushed at `f6cb58175`; the accepted
implementation was committed and pushed by CM at `1bb80619` and integrated byte-for-byte on this
DM branch as `5ed346254`. Independent engineering review found four material defects before launch
(historical digest/receipt paths still reachable, orchestration over 30%, incomplete failure
counts, and non-sticky RSS failure); CM repaired all four and the follow-up review closed each one
without a new material finding. The final scope is 836 production lines, a 43-line runner, 26.5%
conservative orchestration, no engineering-scope §4 item, and no §5 breach.

Immediately before the only result invocation, the fresh central receipt passed with both physical
and effective available memory at `8,264,916,992` bytes. The run was detached, used the committed
implementation, exited `0`, wrote one complete summary, printed only the declared branch, and left
stderr empty. I checked the exact command and launch SHA; `24 + 288 = 312` episodes; `14,976`
transitions and policy calls; four actor updates split `2/2`; all prohibited counters at zero; 48
finite cells; 312 CPU-cap boundary observations; wall, CPU and peak RSS receipts; matched within-cell
materials; common trajectories and score tensors; empty optimizer states; value-head invariance;
and every prospective exposure quantity.

I checked the global, both-anchor, all three leave-one-profile, all eight leave-one-root, and every
cell observable against the card. Then I applied its precedence verbatim. `INVALID_ATTEMPT` does not
apply. The semantic-edge branch fails because global and A0 `Delta_R` are negative, A0 `J` is
negative, every leave-one robustness `Delta_R` is negative, and the two required global absolute
CORRECT comparisons are negative. `B9R1_GENERIC_OR_SOURCE_HARM_ONLY` applies through negative
global source-vs-anchor, receiver-vs-anchor, and receiver-vs-source CORRECT effects and through all
the robust `Delta_R <= 0` conditions. The generic-gain clause is not the trigger: global generic
gain is itself negative.

## Observation that bounds the result

Direct observation: the receiver-addressed update did not produce a robust immediate semantic edge.
Global `Delta_R=-0.0001933415862` and every leave-one-profile/root `Delta_R` are negative. A0 has
`Delta_R=-0.0004180923731` and `J=-0.0004397614920`. A1 has a relative receiver-over-source effect
(`Delta_R=0.0000314092007`, `J=0.0006159866179`), but the receiver and source CORRECT endpoints are
both below the unchanged anchor. The global receiver CORRECT effect is `-0.0003982771720`.

Bounded reading: receiver addressing is not supported as a robust one-step semantic improvement on
this frozen population. The positive A1 relative contrast prevents a general receiver-addressing
negative and shows initialization sensitivity. It also does not rescue an absolute native-value
claim because both learned A1 arms harmed CORRECT reward.

Strongest support: positive A1 `J` and `Delta_R`, with the receiver endpoint less harmful than the
source endpoint. Strongest contradiction: the A0 reversal, negative global absolute receiver
effect, and uniformly negative leave-one `Delta_R`. Surviving alternatives: the addressing effect
may require sustained optimizer exposure; it may be confined to some initializations; or the
one-step displacement may be too small or locally misaligned for the native evaluator.

## Predictions

The DM predicted `B9R1_MIXED_UNIDENTIFIED`. That prediction missed the recorded branch: the result
met the earlier `B9R1_GENERIC_OR_SOURCE_HARM_ONLY` rule because absolute CORRECT harms and robust
nonpositive `Delta_R` were already sufficient. The prediction's qualitative expectation of
anchor/root heterogeneity was borne out. Owner prediction was `not taken (unattended)`.

## Flags for the owner

- This is a valid complete B observation, not a C consumption event.
- It neither closes the direction nor changes lifecycle, priority, capacity, CBSC ownership, or
  any Portfolio field.
- A1's positive relative effect is paired with absolute CORRECT harm; it must not be reported as
  receiver-addressed value.
- The exact-zero A1 / `train_5_3_7_6` / root 991005 cell is matched and finite, not missing
  instrumentation.
- The historical invalid B9 artifact remains immutable evidence and was not rewritten.
- Selecting a multi-update recast, parking, or closing this object family is direction tier and is
  not decided by this intake.

## Decisions this intake produces

### Decision 1 — disposition of the completed attempt (object tier)

Options:

- (a) accept the summary as the valid complete B9R1 result and publish the carded branch;
- (b) quarantine it despite passing integrity, instrumentation, counts, exposure and admission;
- (c) rerun the same object to seek a different outcome.

Recommendation: **(a)**. The result matches every frozen scientific and technical condition.
Quarantine has no evidentiary basis, and a duplicate outcome-seeking run would violate the
one-attempt object discipline.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. Reversible: yes at the next clean boundary if the owner fills the audit override.
The B object is complete without a consumption label and without a rerun.

### Decision 2 — what follows the one-step initialization dependence (direction tier)

Options to place before `em:eociv_lite:convergence`:

- (a) recast as a small B10 short-curve object: three prospectively fixed initializations, a short
  multi-update exposure ladder, the same receiver/source comparator plus the unchanged endpoint,
  and the same native CORRECT/SWAPPED consequence;
- (b) park receiver-addressed credit after repeated heterogeneous or nonconfirmatory B evidence,
  leaving static receiver-content questions with CBSC;
- (c) close only the receiver-addressed credit family on this one-step result;
- (d) repeat the same one-step object with more roots or initialization seeds.

Recommendation: **(a)**, narrowly framed to discriminate sustained learning from the observed
one-step initialization sensitivity. Option (b) is the strongest alternative if the direction no
longer merits additional exposure. Option (c) overreads one B result; option (d) expands the same
weak-exposure panel without resolving the main alternative. This intake does **not** select among
these direction-tier options. It escalates them and parks `eociv_lite` at the clean pushed boundary
until the persistent convergence node decides.

## Next discriminator

Pending the direction node, the smallest recommended discriminator is a short, prospectively capped
multi-update curve that preserves authenticated receiver/source addressing, records actual
parameter displacement and competence, and compares every learned endpoint to the unchanged
anchor. It must ask whether receiver-over-source semantics becomes sustained and absolute rather
than merely less harmful at one initialization. This is a proposal to the direction node, not a
registered card or launch authorization.

## Evidence paths

- Card: `docs/research/candidates/eociv_lite/EOCIV_B9R1_RECEIVER_ADDRESSED_CREDIT_SCIENCE_CARD_20260904.md`
- Result: `docs/research/candidates/eociv_lite/EOCIV_B9R1_RECEIVER_ADDRESSED_CREDIT_RESULT_EVIDENCE_20260904.md`
- Runtime summary: `temp/directions/eociv_lite/exp/b9r1_20260904_01/summary.json`
- Admission: `temp/directions/eociv_lite/exp/b9r1_20260904_01/resource_admission.json`
- Implementation launch SHA: `1bb80619dc91bbd341cb1d9a709fe2615d03afbd`

