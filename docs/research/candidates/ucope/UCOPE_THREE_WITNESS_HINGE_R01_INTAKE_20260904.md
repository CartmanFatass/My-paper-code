# UCOPE three-witness hinge R01 — DM intake

- Direction: `ucope`
- Object: `UCOPE-B-EXPLORE-THREE-WITNESS-HINGE-R01`
- Evidence class / claim ceiling: **B/EXPLORE**, six-policy finite-host mechanism observation
- Result branch: **`TW-B — COVERAGE_CLOSES_TAIL_ONLY`**
- Intake date: 2026-09-04

## What I checked

I compared `summary.json` against every frozen card item and the committed launch surface. The
card preceded implementation (`fdc6068e3`); implementation and technical acceptance are
`71f693ae1`; the branch was pushed before launch and the worktree was clean. CM reported no §4
addition or §5 breach, 596 research-code lines, a 61-line runner, `13 passed` post-edit and
`13 passed` in the independent pre-launch review. The third smoke prohibited by the card was not
run.

The resource receipt passed once immediately before the sole detached invocation at
`12,701,573,120` physical and effective available bytes. I checked the exact argv, launch SHA, arm
order, shared rows, seeds/folds, support split, hyperparameters, nonzero counts, zero nonfinite
events, exposure rows, exact reference, per-policy agreement, competence components, root actions,
regrets, every held-out signed-gap family, final witness margins, cost projection and measured wall.
The process published exactly one complete summary; stderr is empty. RSS and the detached Windows
exit code are unavailable and recorded as such.

I then applied the card rule in its written order. `TW-A` fails only because treatment `C_even` is
3/6 rather than 6/6. `TW-B` holds with `N_T=6`, `N_C=4`, and `C_even<6`; no later branch is reached.

## Observation that bounds the result

Direct observation: equal-total-dose direction coverage changes the tail gate from 4/6 to 6/6 and
makes all three held-out direction gaps positive, with the comparator pass set preserved. The two
new tail passes become root false positives at the more expensive `p=17/20` context, so `C_root`
falls from 5/6 to 3/6 and `C_even` stays 3/6. The existing target-context refusal also remains.

Bounded reading: coverage, not hinge dose alone, is sufficient to close this draw's observed tail
residual. It is not sufficient to improve full competence because tail shaping changes native root
targets/actions. The next uncertainty is the root-safe joint objective, not another claim that the
two tail directions were uncovered.

Strongest support: the paired 6-versus-4 gate, strict pass-set containment, and removal of every
negative `(2,4)/(4,6)/(6,8)` cell while the dose-matched comparator satisfies its own hinge.

Strongest contradiction: no `C_even` gain and two treatment-induced root actions that buy a probe
with net value `-0.028563`. The exact reference is root-correct 6/6 but tail-competent only 3/6,
showing the finite-row least-squares objective and the shaped decision objective remain in tension.

Surviving alternatives: a root-safe or bilevel shaping rule may retain the tail closure; the two
false positives may arise from shifted root targets, finite root optimization, or both; draw
variation may change the panel; an oracle-signed diagnostic need not yield a deployable objective.

## Predictions

The DM's branch and both agreement counts were exactly borne out (`TW-B`, 6 and 4). The predicted
4–5 treatment competence count was not: observed 3. Owner prediction was `not taken (unattended)`.

## Flags for the owner

- The result does not change `PAID_ACQUISITION_STATUS`, the PA-B record, `COUNT_RAW_STATUS`,
  lifecycle, priority, or capacity.
- Tail coverage is now directly observed; the scientific cost is two root over-probes, not merely a
  parameter-space deviation.
- RSS is unmeasured but the result remains valid under the standing telemetry decision.
- This B object is complete but has no consumption state. It must not be called a consumed C object.
- Choosing a root-safe successor, a fresh-draw repeat, or parking/recasting the family is a
  direction-tier decision, not a local object-tier extension.

## Decisions this intake produces

### Decision 1 — accept the completed result (object tier)

Options:

- (a) accept the complete summary as valid B/EXPLORE and publish `TW-B`;
- (b) quarantine it because RSS or the detached exit code is missing;
- (c) rerun to obtain those execution fields.

Recommendation: **(a)**. The learner-side record and rule inputs are complete, the one launch is
identified, and the owner telemetry rule forbids treating missing resource telemetry as an
annulment of this non-resource claim. Options (b) and (c) would invent a gate and duplicate a valid
result.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. The exact object is closed as a completed B observation without a consumption
label and without a rerun.

### Decision 2 — what follows the tail/root tradeoff (direction tier)

Options to place before `em:ucope:convergence`:

- (a) open a root-safe/bilevel margin object that preserves the three tail witnesses while directly
  constraining the two observed false-positive root actions;
- (b) repeat the three-witness comparison on a fresh draw before any objective redesign;
- (c) return to the single paid-acquisition root refusal as the next local subject;
- (d) park the direction with PA-B measured and this tail/root tradeoff recorded.

Recommendation: **(a)**, with (b) as the strongest alternative. The paired result identifies a
specific native consequence, so a root-safe discriminator is more informative than repeating the
already closed direction-coverage question. This intake does **not** select among them locally.
It escalates the direction-tier choice and parks UCOPE at the clean pushed boundary until the
persistent convergence response lands.

## Next discriminator

Pending the direction node: the smallest proposed discriminator is a same-draw, dose-matched
root-safe objective that keeps the three odd-support witnesses and adds a prospectively fixed
penalty only for the two root false positives. It must compare against the present three-witness
arm, record the same tail and root consequences, and make no paid-acquisition, COUNT/RAW, fresh-draw,
or deployability claim. This is a recommendation for the direction node, not a registered object.

## Evidence paths

- Card: `docs/research/candidates/ucope/UCOPE_THREE_WITNESS_HINGE_R01_CARD_20260904.md`
- Result: `docs/research/candidates/ucope/UCOPE_THREE_WITNESS_HINGE_R01_RESULT_EVIDENCE_20260904.md`
- Runtime summary:
  `temp/directions/ucope/exp/three_witness_hinge_r01_20260904/summary.json`
- Admission:
  `temp/directions/ucope/exp/three_witness_hinge_r01_20260904_admission.json`
- Implementation: `71f693ae1f1634e3e9c45461cc3c6d61c18394b8`
