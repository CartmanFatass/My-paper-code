Claim: Reconstructing the four recorded origin certificates can identify which unchanged predicates rejected ordinary handover intents on A03's ground-terminal trajectory.
Binding MARL structure: systems / information flow. Multi-agent handover requires legal agreement between two role-indexed predictions, service confidence and safe physical commands after actual shared information arrives.

# DISH origin-certificate reconstruction A04 — science card

Date: 2026-09-05. Object `DISH-ORIGIN-CERTIFICATE-A04`, **A / RECON**.
Selected under object-tier delegation in `DISH_GROUND_ENDPOINT_PATH_A03_INTAKE_20260905.md`.
This card precedes predicate arithmetic or any A04 result. The existing family remains
PRO_FINAL CONTINUE; A03 remains a valid downstream-stage gap, not full qualification.

## 1. Question, comparison and ceiling

A03 restored actual SOURCE, snapshot, readiness and 299 incumbent service ticks, but
its four emitted intents all had certificate 0 and no legal application. Which existing
certificate predicates are false at those four actual call boundaries? The ceiling is
reconstruction of four observed rejections, not a new learner result, calibrated value
claim, source effect, remedy, universal protocol failure or implementation-defect finding.

Treatment is read-only decomposition of the existing conjunction; comparator is the
recorded native certificate at the same call, not a weakened controller or altered
threshold. Live explanations are the fixed policy's prediction/service-confidence
inputs, an ordinary state/action condition, and a mismatch in reconstructing the exact
call boundary or numeric law. Multiple predicates can fail; do not force one cause.

No new native episode/point, checkpoint/model/optimizer, RNG/master, policy forward,
physics or threshold change, replayed counterfactual, payload leak or source fork.
No subset selected for favourable reconstruction, extra seed, control law or threshold
sweep. This is adaptive analysis of A03's retained evidence, not independent replication.

## 2. Fixed retained inputs and actual call boundary

Input is A03's original `a1/trace.jsonl`, 39,140,340 bytes, SHA256
`f2c612928529f30b0566c8895cb40644071dd87c2db03b14cededd98e0dbf45d`.
Its source is `818b2566d1bac7cafcc71ed0bbb90b8abd1c6b65`, collection `e58b9f1f8`.
Read exactly the new-host records at **origins 340, 364, 388, 596**, retaining their
ordinary next-tick rejection facts from 341, 365, 389, 597 as recorded comparisons.
Host `GROUND-TERMINAL-LINEAR-CLEARANCE-A03`, seed 11, original panel 0. No literal
trace becomes another analysis arm; the fixed original trace contains both hosts.

Local original: `C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904/temp/directions/degraded_incumbent_shadow_handover/exp/ground_endpoint_path_a03_20260905/a1/trace.jsonl`.
Remote original: `/home/wu/hmasd-worktrees/dish-endpoint-a03-818b2566/temp/directions/degraded_incumbent_shadow_handover/exp/ground_endpoint_path_a03_20260905/a1/trace.jsonl`.
CM compares the fixed retained bytes before launch; no runtime hash validator is added.

At source 818b2566, native `native_origin_certificate` runs after preparation latch/
warmup increment and ordinary command projection, before motion and tick advance.
Use this existing-field mapping, checked by CM without predicate arithmetic:

| Quantity at the call | Existing trace field |
| --- | --- |
| Ordinary renewal | `arrivals.renewal`, with prepared countdown as context |
| Pre-motion positions, handover-used, terminal, SOURCE existence and sequences | `prepared` state |
| Post-increment latch/warmup, post-projection held commands | `completion.native.prepare_latched`, `warmup`, `a` |
| Mean, covariance, service-Q and raw command inputs | `policy_output` |
| Actual emitted certificate, origin and sender identity | `completion.native.intent_certificate`, `intent_origin_tick`, `intent_owner` |
| Next-tick native rejection | following record's `completion.native.application_reason` and invalid-commit increment |

At these four origins no transfer occurred. The listed latch/warmup/command values do
not change again between certificate call and completion. Final `completion.native.p`
has already moved and is not used for separation; `prepared.a` is before projection
and is not used as the certificate's held command. Existing physical U0/U1/owner/standby
and active/shadow copy meanings stay intact. There is no roster, clock or exposure change.

## 3. Exact existing arithmetic and predicates

Transcribe only source-818b2566 helpers `predictive_q95`, `mahalanobis_position`,
`clipped`, `norm`, `separation` and `native_origin_certificate` as data arithmetic.
Use Python binary64 scalars in the same explicit operation order; no NumPy reduction,
reordered/vectorized sum, extra precision, policy call or training computation.

For the twenty service inputs, clip each `p` to `[1e-6, 1-1e-6]`. Start a 21-entry
probability array at `[1,0,...,0]`. For j=0..19, update m=j+1 down to 0 as
`keep=dp[m]*(1-p)`, `add=dp[m-1]*p` for m>0 else 0, then `dp[m]=keep+add`.
For m=20 down to 0, sum `dp[k]` in increasing k=m..20; return the first `m/20`
whose tail is at least 0.95. Do not replace this with a Gaussian approximation or
the mean service probability. Record the resulting q95 and all 21 tails.

Let `dx=mean[0]-mean[4]`, `dy=mean[1]-mean[5]`,
`s00=cov[0]+cov[16]+1e-6`, `s01=cov[1]+cov[17]`,
`s11=cov[5]+cov[21]+1e-6`, `det=s00*s11-s01*s01`.
If det is not positive finite, native Mahalanobis value is positive infinity;
otherwise compute `(dx*dx*s11-2*dx*dy*s01+dy*dy*s00)/det` with the displayed
left-associative operation order. Infinity is a named nonfinite result in JSON, not
silently a finite surrogate.

Separate distance is the native hypot of the two prepared positions. For each physical
UAV, clip its raw two-component command to norm 3 with the native branch/order, then
compute the Euclidean norm of bounded raw minus the **post-projection** held command.

Report every existing predicate, its input/value and threshold, even if an earlier
predicate already makes the conjunction false:

- renewal true; handover not already used; preparation latched; warmup >=10;
- SOURCE exists at both receivers and their sequences match; nonterminal;
- finite Mahalanobis value <=5.99; predictive q95 >=0.60;
- separation >=15 m; each bounded-raw/held-command norm <=`1.5+1e-12`.

The reconstructed certificate is the conjunction of those unchanged predicates.
Classify failed predicates descriptively as state/support, prediction/service-confidence,
or physical/action; retain all failures and the native condition order. Values from
the source/learner trace are observations; arithmetic and grouping are derived.

## 4. Numeric reading and result branches

One focused test of the formulas and a toy end-to-end publication case establish the
implementation at this class; bit-identity proofs or a new native equivalence study
are not launch conditions. For floating comparison context report the signed distance
to each threshold. Mark a non-discrete comparison within **1e-10 absolute** of its
threshold as numerically close, including any q95 tail-to-0.95 comparison. This is
disclosure of potential cross-language rounding, not a relaxed legal threshold.
Use literal comparisons to form the reported boolean and do not round beforehand.

- Complete outputs for all four origins, reconstructed certificate equal to its recorded
  native value each time, and at least one numerically non-close failed predicate per
  rejected origin: **A04-RECORDED-REJECTION-RECONSTRUCTED**. Report the contributing
  predicate set per origin; this does not show how changing it would affect native service.
- Otherwise, with complete data/arithmetic: **A04-RECONSTRUCTION-DISCREPANCY**. State
  whether the issue is a boolean mismatch or only close-boundary support. No local
  defect classification or scientific polarity is assigned without exact-step reproduction.

Missing required retained inputs, wrong coordinate, silent precision/order change or
time-cap breach makes an incomplete attempt. No branch changes the original A03 rule,
certificates or source family, or authorizes a fresh learner/host intervention.

## 5. Predictions, MEI and headroom

DM prediction: A04-RECORDED-REJECTION-RECONSTRUCTED, with at least one prediction/
service-confidence predicate failing at each origin; expect q95<0.60 to be the most
common failure. The alternative is a state/action restriction despite adequate predicted
service confidence. These predicate values have not been computed at carding.
Owner: `not taken (unattended)`; same existing B01 ladder, no duplicate opening item.

MEI is one non-close false native predicate per recorded rejection: diagnostic resolution,
not a return improvement threshold. Above that resolution, locate the smallest remaining
restriction; inside the numerical boundary band, retain uncertainty; opposite to prediction,
record adequate confidence and the actual state/action failures. All branches recommend
interpretation before any later intervention. No tuned same-information headroom exists;
neither this reconstruction nor A03's incumbent service is such a headroom measurement.

## 6. Exposure, resource route and cost

Machine-generated exposure: one retained trace read, four origin reconstructions,
four recorded next-tick comparisons, zero native prepared/completed ticks, model/policy/
optimizer initializations, training transitions, learner updates and optimizer steps.
Parameter displacement is not applicable because no model is instantiated. Historical
A03/B01 training and trace creation are input provenance, not new A04 exposure.

Portable CPU/binary64 data analysis, no device/host estimand. Use configured remote-first
`wsl_4070`, exact committed/pushed source, detached worktree and existing `agent-task`.
Fresh actual-node physical/effective memory >=4 GiB via `admit-memory --out <receipt>
&& <runner>` precedes input/result creation; no duplicate in-run receipt validator.

One invocation, no sweep. Runner `project-cost` reports
`1.5*(5 seconds full-trace read allowance + 4 origins*(1 second arithmetic + 1 second
readout/publication)) = 19.5 seconds`, below a **60-second** cap. Report actual full
runner/supervisor wall and peak RSS with publication timing scope. This is a conservative
allowance, not a measured throughput claim. Stop after the four origins/comparisons;
no expanded rows, threshold retuning or retry is automatic. Missing resource telemetry
is `resources_unmeasured` and does not annul a non-resource claim.

## 7. Bounded CM implementation

**Engineering-scope section 4 declaration: this object needs none of the default-prohibited
machinery.** CM owns only a small A04-specific arithmetic/readout module if needed in
the existing B01 candidate directory, `scripts/run_dish_origin_certificate_a04.py`,
its focused tests in the matching research test directory, and technical/result docs.
No native kernel, old runner, checkpoint, shared Python API, loader, schema framework,
generic trace validator, provenance gate or additional telemetry is added.

Runtime root: `temp/directions/degraded_incumbent_shadow_handover/exp/origin_certificate_a04_20260905/`.
Stay below 2,000 new non-test lines, runner 600 and orchestration <30% excluding tests;
use a much smaller direct implementation and return any actual excess without padding.
Tests use synthetic four-origin records, never the four actual input values before
the admitted result. Reuse CM/specialists, commit/push every change immediately, verify
focused arithmetic and publication once over exact pushed bytes. CM accepts technical
completeness and hands the unique accepted handle directly to the shared tracker.
CM collects, DM applies the rule; no scientific successor is preauthorized.

## 8. Append-ready owner-card audit for Root

Object selection is already recorded by owner item 20260905-dish-015 in the A03 intake.
This is the separately saved prospective card, not another selection or result.
Anchor: `n3-origin-certificate-a04-card`.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T04:35:29-07:00 | degraded_incumbent_shadow_handover (N3) | object | selection | accept; reject; revise | A04 card frozen; recommendation accept, no arithmetic result yet | yes | DM_CARD | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-017.json | none | |
