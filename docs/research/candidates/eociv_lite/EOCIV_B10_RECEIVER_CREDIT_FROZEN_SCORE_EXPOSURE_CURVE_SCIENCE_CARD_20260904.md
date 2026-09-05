# EOCIV-B10 receiver-credit frozen-score exposure curve — science card

Date: 2026-09-04  
Direction: `eociv_lite`  
Object: `EOCIV-B10-RECEIVER-CREDIT-FROZEN-SCORE-EXPOSURE-CURVE`  
Evidence class: **B / EXPLORE**  
Direction authority: **`FINAL_DECISION=PRO_FINAL — CONTINUE`** from
`em:eociv_lite:convergence`  
Decision source: `external/2026-09-04-eociv-b9r1-convergence-01/PRO_RESPONSE_FULL_RECOVERY.md`,
SHA-256 `6a2f94bf2ee12aa0e9bc8e1c455a14b68f6f905df8f597aebed4b64eb18e4628`

The corrective full response is the only scientific decision source. The earlier 679-byte archive
is an incomplete excerpt and remains transport-defect evidence only. The correction is classified
`ARCHIVE_INCOMPLETE_RECOVERED`; it involved no provider resend and no receipt resend.

## 1. Question, claim ceiling, and non-goals

Question: on the same finite EOCIV sibling host, does bounded cumulative Adam exposure to a
receiver-addressed credit vector produce a robust and absolute native CORRECT-versus-SWAPPED
semantic edge over the authenticated-source-addressed vector, or does the B9R1 sign remain
initialization-specific or relative-only?

Maximum positive conclusion:

> On the declared three-initialization, three-profile, eight-root EOCIV population, increasing
> cumulative Adam exposure to a fixed receiver-addressed credit vector produced a robust native
> semantic edge over the equivalently exposed authenticated-source vector and the unchanged
> endpoint.

Maximum negative conclusion:

> The prospectively bounded fixed-vector exposure range did not rescue the B9R1
> receiver-addressed effect.

Neither outcome establishes endogenous or on-policy sustained learning; receiver-local mediation;
general receiver-content value or harm; general source-addressing superiority; static-content
polarity, which remains a CBSC axis; arbitrary initialization or root generalization; C promotion,
freeze or consumption; cross-direction attribution; transfer; safety; deployment readiness;
general MARL superiority; or any Portfolio or lifecycle action.

Non-goals: no fresh direction-local mechanism; no ordinary adaptive/on-policy multi-update curve;
no gradient, trajectory or score recomputation after the common batch; no favorable seed, root,
profile or rung selection; no checkpoint selection; no critic update, global clip, reward change,
auxiliary loss, rescue, retry, hyperparameter search, C contract, or CBSC static-content claim.

## 2. Finite population and prospectively frozen collection tapes

- initializations: A0/A1/A2 with seeds `990031`, `990032`, `990033`;
- profiles: `train_4_3_6_5`, `train_5_3_7_6`, `train_6_4_8_6`;
- held-out roots: `991001..991008`;
- horizon: 48;
- critical segments: `[12,24)` and `[36,48)`;
- native bodies: `CORRECT`, `SWAPPED`;
- endpoints: `0`, `R1`, `S1`, `R4`, `S4`, `R16`, `S16`.

The 36 collection tapes were enumerated and byte-bound before implementation in
`EOCIV_B10_FROZEN_COLLECTION_TAPE_MANIFEST_20260904.json`, SHA-256
`5ad9a8e1456cc4263e0359929269957d2dd46d87ad6de6b68271be628825ef84`. The ordered roots are:

| initialization | profile | ordered roots for shocks `(A,A),(A,B),(B,A),(B,B)` |
| --- | --- | --- |
| A0 / 990031 | `train_4_3_6_5` | `990100,990101,990102,990103` |
| A0 / 990031 | `train_5_3_7_6` | `990110,990111,990112,990113` |
| A0 / 990031 | `train_6_4_8_6` | `990120,990121,990122,990123` |
| A1 / 990032 | `train_4_3_6_5` | `990200,990201,990202,990203` |
| A1 / 990032 | `train_5_3_7_6` | `990210,990211,990212,990213` |
| A1 / 990032 | `train_6_4_8_6` | `990220,990221,990222,990223` |
| A2 / 990033 | `train_4_3_6_5` | `990300,990301,990302,990303` |
| A2 / 990033 | `train_5_3_7_6` | `990310,990311,990312,990313` |
| A2 / 990033 | `train_6_4_8_6` | `990320,990321,990322,990323` |

Each manifest row fixes initialization, profile, real-environment root and ordered forced critical
shock tuple. The manifest is scientific assignment input, not a result, a launch refusal predicate,
or permission to add source/HEAD/output provenance machinery.

## 3. Treatment, strongest comparator, and live explanations

For each initialization `a`, collect the one common B9R1-style batch across all profiles and four
ordered forced critical tuples. Before any parameter mutation, compute detached normalized GAE
material and the complete member-by-term score tensor once.

Treatment `RECEIVER_ADDRESSED`: contract that complete tensor with the authenticated receiver row
to obtain one fixed actor-gradient vector `g_R^a`. Starting from the unchanged actor `theta_0^a`
and an empty Adam state, apply exactly that same gradient vector for 16 consecutive actor-only Adam
steps. Never recompute trajectories, scores, GAE or gradients. Retain mandatory in-memory endpoint
states at cumulative steps `m in {1,4,16}`.

Strongest competent same-information comparator
`AUTHENTICATED_SOURCE_ADDRESSED_CONTROL`: use the same complete score tensor, but contract the
authenticated distinct-source row to obtain fixed `g_S^a`; then apply it with the identical Adam
algorithm, hyperparameters, empty initial state and 16-step schedule.

Receiver and source arms share collection trajectories, complete score tensors, initialization,
the active 516-parameter set, detached GAE material, optimizer algorithm and hyperparameters,
endpoint schedule and native evaluation material. The unchanged `theta_0^a` remains the
absolute-harm anchor. The six branch initial receipts must show, within each initialization, the
same actor bytes and separate empty optimizer states.

Live explanations:

1. magnitude/exposure: one approximately `7e-4..8e-4` initialization-relative displacement was
   insufficient, while more exposure to the same receiver vector may become useful;
2. initialization dependence: receiver credit is useful in some local basins and harmful in others;
3. relative-only/source-harm: receiver addressing may remain only less harmful than source
   addressing, with no absolute native value;
4. repeated fixed-vector Adam exposure may amplify a wrong receiver direction rather than reveal a
   semantic edge.

## 4. Learner, numerical, RNG, and side-effect semantics

Preserve the real B9R1 host and scientific kernel: real `EocivSiblingRosterEnv`, real shared
recurrent actor/value model, `content_separating`, `SEGMENT_LATCH_RNN`, authenticated `EdgeIdentity`
source/receiver ownership, receiver-only critical content latch, and native environment step.

Use episode-local terminal GAE with `gamma=0.99`, `lambda=0.95`, population normalization epsilon
`1e-8`, float32 model/update semantics, Adam `lr=3e-4`, and the active actor path
`log_std`, `obs.weight`, `recurrent.weight`, `actor.weight`, `actor.bias`,
`content_embedding.weight`. Compute `g_R^a` and `g_S^a` before either branch mutates. At every step,
set the corresponding fixed gradient tensor on exactly that active path and call the branch's Adam
optimizer once; optimizer moments evolve, but gradient values do not. Value parameters remain
unchanged.

Evaluation retains B9R1 matching: within every initialization/profile/root cell, endpoint/body
comparisons share held-out root, critical shock material, lifecycle, action-noise innovations and
boundaries. Endpoint 0 is the exact unchanged initialization. No result, checkpoint, optimizer
state or outcome from B9R1 is read; B9R1 supplies only prospectively declared source semantics and
historical evidence.

The single full invocation writes only to a fresh
`temp/directions/eociv_lite/exp/b10_<run>/` root. It publishes one `summary.json`, ordinary stdout,
stderr, exit and resource receipts, and no repository result claim or compatibility artifact.

## 5. Native observables and retained aggregates

For `x in {R,S}` and `m in {1,4,16}`:

`phi_(x,m) = Y_CORRECT(theta_(x,m)) - Y_SWAPPED(theta_(x,m))`

`Delta_(R,m) = phi_(R,m) - phi_0`

`J_m = phi_(R,m) - phi_(S,m)`

where `Y` is native mean reward over the 24 critical steps and
`phi_0=Y_CORRECT(theta_0)-Y_SWAPPED(theta_0)`. Also retain:

- `R_m-v0 = Y_CORRECT(theta_(R,m)) - Y_CORRECT(theta_0)`;
- `R_m-vS = Y_CORRECT(theta_(R,m)) - Y_CORRECT(theta_(S,m))`;
- `S_m-v0 = Y_CORRECT(theta_(S,m)) - Y_CORRECT(theta_0)`;
- actual actor-parameter L2 displacement from initialization and its ratio to initialization L2 at
  `m=1,4,16` for both arms.

Report every underlying initialization/profile/root cell at all seven endpoints, plus the global
mean, each of the three initialization means, every leave-one-profile aggregate and every
leave-one-root aggregate. The 72 cells and all 1,008 endpoint/body observations remain visible;
no averaging may replace their retention.

## 6. Frozen terminal rule

Apply this precedence exactly, without tolerance or a favorable-rung substitute:

1. `INVALID_ATTEMPT`: any common-integrity failure; nonfinite required observable; missing common
   trajectory/complete-score identity; learner-side instrumentation failure; initial-state,
   count, fixed-gradient, step-receipt, value-invariance or endpoint mismatch; or CPU-cap stop.
   Quarantine the attempt and assign no scientific polarity.
2. `B10_FIXED_SCORE_EXPOSURE_EDGE`: at the predeclared terminal endpoint `m=16`, all of these hold:
   - `J_16 > 0` and `Delta_(R,16) > 0` globally, in each of the three initialization means, in
     every leave-one-profile aggregate and every leave-one-root aggregate;
   - `R_16-v0 >= 0` and `R_16-vS >= 0` globally and separately for every initialization;
   - all required counts, common-tensor identity checks, observables and displacement records are
     complete and finite.
3. `B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED`: every other valid complete result, meaning at
   least one terminal condition above fails.

The `m=1` and `m=4` endpoints are mandatory trajectory-shape evidence but cannot replace `m=16`,
support favorable-rung selection, change the terminal branch, trigger a rerun, or rescue the rule.
A valid falsifier parks the receiver-addressed credit family at B/EXPLORE pending genuinely new
evidence. It does not close `eociv_lite`, transfer polarity to CBSC, or create a Portfolio action.

## 7. Counts, cost law, budget, and stop rule

Exact activity:

- collection: `3 initializations x 3 profiles x 4 tuples = 36` episodes;
- evaluation: `3 x 3 x 8 roots x 7 endpoints x 2 bodies = 1,008` episodes;
- total: **1,044 episodes and 50,112 environment transitions/policy calls**;
- actor optimizer calls: `3 x 2 x 16 = 96`;
- zero critic updates, value-gradient calls, global clips, gradient recomputations, hypothetical
  transitions, retries, rescues, sweeps, searches and checkpoint selections.

Runner cost law: `M = 1,044 x 48 real transitions + 96 fixed-gradient Adam actor steps`. This is
one fixed finite grid, not a tunable sweep, so no per-arm sweep projection applies. Scaling the
B9R1 observed `20.171875` process-CPU seconds by the episode/transition ratio projects
`67.498197115384613` CPU seconds before the additional fixed-step overhead; B10 has a conservative
**300 process-CPU-second cap**, checked only at episode boundaries and after each Adam step. The cap
applies to the single full invocation. Crossing it is a technical stop with no scientific polarity.

Stop after exactly the declared workload and one complete summary. An implementation or
learner-instrumentation failure quarantines the attempt. Missing post-run wall/peak-RSS telemetry
alone leaves this non-resource result valid and is marked `resources_unmeasured`.

Immediately before every full result-bearing invocation, run
`python scripts/hmasd_resource_preflight.py admit-memory --out <run-root>/resource_admission.json`
and require physical and effective available memory each at least 4 GiB. Commit and push before
launch, launch detached, and record launch SHA, exact command, exit, stdout/stderr, wall, CPU and
peak RSS. There is no resume or scientific retry; a repaired implementation is a fresh attempt at
a new SHA.

## 8. Exposure line

The active path has 516 parameters. The per-step Adam L2 displacement upper bound is
`lr*sqrt(516) = 0.006814690014960328`; the 16-step triangle bound is
`0.10903504023936525`. Machine-generated initial norms and prospective ratios are:

| initialization | initial active L2 | one-step upper ratio | 16-step upper ratio |
| --- | ---: | ---: | ---: |
| A0 / 990031 | 10.009484810505533 | 0.0006808232535412728 | 0.010893172056660365 |
| A1 / 990032 | 8.103020076903935 | 0.0008410061866172912 | 0.013456098985876659 |
| A2 / 990033 | 9.23913725716857 | 0.0007375894334368576 | 0.011801430934989721 |

For context only, B9R1 actually observed receiver/source one-step displacement ratios
`0.0006808181628451928 / 0.0006483422490130309` for A0 and
`0.0008410038291636608 / 0.0008144986491506393` for A1. These historical observations do not set
B10 outcomes. B10 must record actual receiver and source displacement at all three mandatory
endpoints for all initializations.

## 9. Predictions on record

DM prediction before implementation/result: `B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED` is
more likely. Fixed-vector exposure may preserve or enlarge A1's relative `J`, but A0's reversal,
negative global absolute CORRECT effects, uniformly negative B9R1 leave-one `Delta_R`, and B2--B6
failure to turn mechanism diagnostics into stable absolute semantics make simultaneous positivity
across all three initializations and every leave-one aggregate unlikely. A useful curve shape at
`m=1` or `m=4` does not change this terminal prediction.

Owner prediction: `not taken (unattended)`.

## 10. Engineering scope and owned surfaces

Engineering-scope §4 item named by this card: **one tamper-evidence/byte-manifest artifact covering
exactly 36 prospective collection-tape coordinate rows**, because the PRO_FINAL response requires
those tapes to be enumerated and byte-bound before implementation. The committed JSON and its one
SHA-256 satisfy that quantity. Do not add a hash chain, source/HEAD/currentness guard, create-once
file, output provenance predicate, result claim, schema framework or runtime digest refusal.

All other §4 items: none. In particular, no distributed execution, worker pool, scheduler,
checkpoint/resume/recovery, retry/lease/lock/heartbeat, incident tree, attempt ledger, multi-phase
orchestrator, internal schema validator, registry, plugin/factory layer, telemetry beyond wall and
peak RSS, compatibility shim, or repeated smoke system.

Owned implementation surfaces:

- `experiments/candidates/eociv_lite/b10/`;
- `tests/experiments/candidates/eociv_lite/b10/`;
- one runner `scripts/run_eociv_b10_receiver_credit_frozen_score_exposure_curve.py`;
- the frozen collection manifest and fresh ignored run root.

Research-code budget is at most 2,000 new production lines, runner at most 600 lines, orchestration
under 30%, and total test wall under five minutes. Technical success establishes only that the
frozen real learner/trainer/evaluator path executed with complete identities, counts, exposures and
observables. It cannot establish receiver-credit value beyond the terminal B claim ceiling.

## 11. Object-tier operational decision

Options:

- (a) commit one flat 36-row coordinate manifest before implementation, reuse the B9R1
  300-process-CPU-second cap, and implement one sequential fixed loop;
- (b) generate collection coordinates only inside implementation, leaving no preimplementation
  byte binding;
- (c) build a digest chain, result claim, registry and multi-phase provenance guard around the
  manifest.

Recommendation: **(a)**. It satisfies the exact PRO_FINAL requirement, keeps the workload within
the already demonstrated host envelope, and adds only the one named §4 quantity. Option (b) omits a
required prospective fact; option (c) adds unrequested machinery without scientific value.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Provenance:
`OWNER_DELEGATED`. Reversible before launch; no scientific meaning, equation, comparator, count,
endpoint or branch is changed.

