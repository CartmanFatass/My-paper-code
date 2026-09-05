Claim: On the unchanged B01 finite panel and exact seed-0 RAW trajectory, updates 252 through 264 provide a bounded measurement of local checkpoint-phase sensitivity around the comparator-weak update-256 observation.
Binding MARL structure: `systems / information flow`; the RAW gate acts on a four-agent common-history packet under partial observability, but this A/RECON isolates learner-order exposure and does not estimate an effect of multi-agent non-stationarity or residual information.

# CRTO RAW phase-trace A01 science card

- Object: `CRTO-RAW-PHASE-TRACE-A-RECON-R01`
- Direction: `commitment_residual_triggered_options`
- Frozen: `2026-09-04T09:46:08-07:00`
- Evidence class: `A/RECON`
- Result-bearing: `true`
- Claim ceiling: one exact RAW learner-path measurement on the declared finite panel, seed,
  execution node, numerical path, and update bracket; no algorithm-effect or residual-effect claim
- Object-tier design provenance: `OWNER_DELEGATED`

## 1. Question, claim ceiling, and non-goals

On the exact `48` TRAIN / `16` EVAL population used by balanced-residual B01-R1, with the same
seed-0 RAW packet, gate initialization, Adam law, cyclic row order, batch size `32`, and FP32
learner path, what native action choices and G16 regrets occur after every update
`u in {252,253,...,264}`?

The direct question is whether the B01 update-256 side asymmetry is locally sensitive to the
three-update order phase induced by `32` examples per update over `48` cyclic TRAIN rows. The
claim ceiling is only the observed vector of RAW actions, regrets, competence predicates, and
parameter displacement over this bracket. The EVAL panel is deliberately exposed at all thirteen
checkpoints, so no checkpoint selected from this trace may later be called held out, independently
tuned, or a competent deployable comparator on this same panel.

This object does not compare RAW with TRUE_RESIDUAL or CALIBRATED_DERANGEMENT, estimate a residual
effect, change B01, lower either competence threshold, reopen a consumed natural-support object,
search new addresses, estimate natural K8 prevalence, read the untouched confirmation, or support
policy-return, transfer, safety, deployment, lifecycle, priority, fusion, or Portfolio claims.

## 2. Why this remains the smallest runnable object

Accepted B01-R1 was valid `BR-E — COMPARATOR_WEAK`. At update 256, RAW was KEEP-perfect (`8/8`,
zero mean regret) but REPLAN-weak (`4/8`, mean regret `0.0066464623737892345`) against the unchanged
requirements of at least `6/8` exact and mean regret at most `0.005` on each side. At update 32 the
same path was REPLAN-perfect and KEEP-weak. That side flip leaves checkpoint phase, insufficient
exposure/model capacity, and one-initialization variation live without granting residual polarity.

The current source already contains the exact B01 population, predictor, RAW packet, seed-0 gate,
Adam update, evaluation, and exposure primitives. Its non-result `project-cost` command executes
successfully on current source. The trace therefore adds only thirteen declared in-memory RAW
snapshots and their evaluations. A larger-budget three-path rerun would pay for two irrelevant
representations before localizing RAW; replacing the RAW architecture would change the comparator
before diagnosing the accepted path; and a new population would abandon the observed phase
question. No smaller read of the existing tracked result can reveal the unobserved checkpoints.

## 3. Population and environment-to-consequence trace

Regenerate exactly the B01 rows frozen in
`CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md`:

- source RNG namespace `2026083192`;
- source slots `0..7`, source split coordinate `EVALUATION`, K8, episode range `832..895`;
- the same exact `48` TRAIN and `16` EVAL membership, without replacement, resampling, threshold
  change, or post-launch row selection; and
- the same event, onset, replanning cost `4.0`, elapsed horizon `4`, side, boundary, legal mask,
  G16 denominator, charge-once law, and common-future evaluator.

The runner reconstructs the rows from the generator and fixed addresses. It does not read the B01
summary as scientific input. Confirmation namespace `2026083001` is neither read nor instantiated.

Each row is one complete service-relay history for a fixed four-agent roster. One persistent slot
owns the active option; there is no join, leave, rejoin, replacement, survivor-state change, or
censoring. At the first eligible review the RAW gate receives the same 42-vector history and
52-vector target/predictor-mean/Cholesky packet, selects one printed legal action, pays the native
replacement charge once when applicable, and is scored against the unchanged 16-step common
future. Primitive environment time, review opportunity, learner update, processed-example
exposure, and checkpoint evaluation remain separate counts. Partner co-adaptation is absent.

## 4. Subject, reference, and live explanations

There is no treatment-effect arm. The measured subject is the exact B01 same-information RAW
comparator trajectory, extended from update 256 through update 264 solely so all thirteen declared
checkpoints are observed in one uninterrupted from-genesis run. The strongest available
same-information comparator is therefore the RAW path itself; its competence is what this object
measures and is not assumed. `LEGAL-G16-ORACLE` remains the privileged row-wise scoring reference,
not an available policy or a same-information learner.

The live explanations kept separate are:

1. the cyclic order phase creates local side-specific action oscillation;
2. the seed-0 RAW model or budget remains inadequate throughout the bracket;
3. a cross-node numerical or RNG-semantic mismatch prevents reproduction of the B01 trajectory;
4. the outcome-informed panel magnifies local instability;
5. predictor or finite-sample variation, rather than RAW gate phase, bounds the observation; and
6. a scientific, numerical, RNG, count, or information-boundary defect invalidates the attempt.

No result branch assigns any of these explanations residual-mechanism polarity.

## 5. Exact learner path and protected anchor

Use seed `0` and recreate the B01 predictor from namespace `2026090401`: K4 episodes `0..63` and
K8 episodes `64..127` under `PREDICTOR_FIT`, exactly `100` Adam updates, batch `128`, FP32, learning
rate `1e-3`, and the existing Gaussian-NLL target. Build only the RAW packet needed by this object.
TRUE_RESIDUAL and CALIBRATED_DERANGEMENT learner updates, checkpoints, evaluation rows, contrasts,
and result fields are exactly zero/absent. Residual calibration and derangement are not scientific
inputs to this RAW-only trace.

Initialize one `CommonHistoryGate` from the same namespace, stream, and seed as B01. Train on the
same ordered `48` TRAIN rows with `np.resize(arange(48), 264*32)`, batch `32`, FP32, Adam
`lr=1e-3`, betas `(0.9,0.999)`, epsilon `1e-8`, zero weight decay, gradient clip `1.0`, and native
legal-action MSE. Do not resume from or write a learner checkpoint. Deep-copy one in-memory
evaluation snapshot immediately after each update `252..264`.

The seed-0 initialization anchor is L2 `18.87916908516977`, RMS `0.10402732933491829`, and Linf
`0.28862619400024414`. Each must reproduce within relative tolerance `1e-7`; otherwise the
attempt is numerically incomplete before any trace interpretation.

Update 256 is an integrity anchor, not a selectable result. It must reproduce the tracked B01 RAW
aggregate:

```text
KEEP:   exact 8/8, mean regret 0
REPLAN: exact 4/8, mean regret 0.0066464623737892345
equal-side regret 0.0033232311868946172
```

Exact-action counts must match exactly; reported mean regrets must match these constants within
absolute tolerance `1e-12`. An anchor mismatch is an incomplete numerical-path attempt. It is not
evidence for or against checkpoint phase, RAW competence, or the residual mechanism.

## 6. Observable, estimand, and result branches

For every update `u=252..264`, publish:

- `u`, `u mod 3`, the post-update cyclic cursor `(32*u) mod 48`, processed examples `32*u`, and
  nominal learning-rate exposure `0.001*u`;
- the seed-0 initial parameter L2/RMS/Linf and checkpoint parameter-displacement L2 and Linf ratios;
- every EVAL row key, side, legal mask, full legal G16 vector, oracle action/G16, RAW selected
  action/G16, native regret, and exact-action indicator;
- KEEP and REPLAN row counts, exact-action counts, and mean regrets separately;
- equal-side regret `R(u)=0.5*(mean_KEEP(u)+mean_REPLAN(u))`;
- signed local differences `D(u)=R(256)-R(u)` and the best/worst update with a fixed smallest-update
  tie break; and
- the unchanged B01 competence predicate at each update: both sides have at least `6/8` exact and
  mean regret at most `0.005`.

Also publish predictor tapes/examples/updates, environment transitions, common-future branch steps,
RAW gate updates, processed examples, evaluation rows, exact argv, launch SHA, execution node,
result root, fresh admission receipt, wall time, and peak RSS when measured.

Apply this rule verbatim:

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

A valid A/RECON result has no consumption state. Process exit or test success cannot substitute for
the measured trace.

## 7. Minimum effect of interest, headroom, and interpretation narrative

The card's descriptive MEI is an **absolute `0.0025` native-G16 change** in equal-side regret from
the fixed update-256 anchor. This reuses B01's existing absolute comparison margin and does not
lower any threshold. No relative MEI is used because side regrets can be exactly zero, making a
percentage unstable. The MEI describes what merits a later decision; it is not a result branch or
competence rewrite.

- If one or more nearby updates improve on update 256 by more than `0.0025`, or directly meet the
  unchanged two-sided competence predicate, local checkpoint phase remains decision-relevant. I
  would recommend designing the next comparator rung without treating the best exposed checkpoint
  as held out.
- If every `D(u)` lies inside `[-0.0025,+0.0025]` and no update is competent, the local phase
  explanation is weakened and RAW budget/model limitation remains the leading local alternative.
- If nearby checkpoints are worse than update 256 by more than `0.0025` with none materially
  better, the opposite sign indicates local deterioration or instability, not residual advantage;
  I would not reopen or retune residual arms from this A result.

The direction has **no completed headroom record** on this host under evidence spec section 11.7:
B01 reports oracle-minus-RAW gaps, but its one-seed RAW-LONG path failed registered competence and
is not a tuned same-information generic baseline with reusable seeds and curves. The tracked
`scenario_1` and `relay_corridor` baseline sets do not match this object's observation, action,
information, population, or update budget, so they are not reused.

## 8. Predictions on record

- **DM:** `A01-RAW-PHASE-TRACE-MEASURED`. I predict the update-256 anchor will reproduce and the
  side metrics will oscillate with the three-update cyclic phase, but no update in `252..264` will
  satisfy both unchanged competence conditions.
- **Owner:** `not taken (unattended)`; this is a successor diagnostic in the already open ladder,
  not a new ladder prediction request.

## 9. Per-arm cost projection, exposure line, resource bound, and stop rule

There is exactly one RAW arm and one result-bearing invocation. The runner's non-result
`project-cost` mode must emit the following fixed planning law before launch:

```text
prior complete B01 invocation                         = 434.7066687 seconds
projected RAW-trace arm seconds = 3 * 434.7066687      = 1304.1200061 seconds
per-arm and invocation wall cap                       = 1800 seconds
```

The complete prior invocation included the same predictor/panel path plus three 256-update learner
paths; it is a heavier work reference than this one RAW path. Factor `3` covers node load,
implementation variation, eight extra updates, and thirteen rather than two RAW evaluation
checkpoints. The cap applies to this sole arm. A machine-generated projection above `1800` refuses
launch.

Prospective work bounds are one predictor fit (`100*128=12,800` predictor examples), one RAW gate
trajectory (`264*32=8,448` processed examples), and `13*16=208` checkpoint-evaluation rows. The
runner reports exact environment and common-future counts from execution.

**Exposure line.** For every `u=252..264`, emit initialization L2/RMS/Linf, updates `u`, batch
`32`, processed examples `32*u`, Adam learning rate `0.001`, nominal exposure `0.001*u`, and actual
parameter-displacement L2/initial-L2 and Linf/max(initial-Linf,`1e-12`). The initial scales must
reproduce the seed-0 B01 initialization within ordinary FP32 numerical tolerance; zero or nonfinite
movement makes the attempt incomplete.

- Resource envelope: one CPU process, one computational thread, no child/worker pool, expected
  peak RSS below 2 GiB.
- Immediately before the invocation, the execution node must emit a fresh `admit-memory` receipt
  with physical and effective availability at least 4 GiB.
- Stop after one complete summary, or at the first admission, integrity, learner-measurement, or
  wall-cap failure. There is no result-sensitive early stop, row replacement, arm drop, resume,
  retry loop, or expansion inside R01.

## 10. Execution portability and protected semantics

The physical CPU is not part of the estimand. The object is prospectively portable between the
configured local CPU and `wsl_4070` CPU because it uses the existing CPU-only deterministic host,
counter-based RNG streams, and FP32 learner, and claims no bit identity across devices. The first
result-bearing route is nevertheless `remote_first`: an exact pushed SHA in a unique detached
remote worktree, with the fresh remote preflight and exact runner joined in one `agent-task`
command. GPU execution is not permitted. Local fallback is legal only under the repository's
predeclared portability rule, before any remote process is accepted, and after a fresh local
admission.

The update-256 anchor is the prospective cross-node numerical check. A remote anchor mismatch is
an incomplete attempt and a named portability blocker; it is not repaired by tolerance changes or
silently rerun locally.

Protected semantics are the exact panel and split; source generator and namespaces; predictor and
RAW packet equations; seed and RNG ownership; gate architecture and initialization; FP32/CPU Adam
update order; cyclic examples; batch size; updates and snapshot timing; legal-action order;
G16/charge/denominator/regret laws; EVAL isolation; untouched-confirmation exclusion; admission;
and one-output-root side effects. No old model or optimizer state is read. Technical conformance
can establish only that the declared path ran; it cannot establish checkpoint-phase importance or
residual value.

Permitted side effects are one fresh receipt, stdout/stderr/task-supervisor logs, and one
`summary.json` under
`temp/directions/commitment_residual_triggered_options/exp/raw_phase_trace_a01_20260904/`.

## 11. Engineering scope and owned paths

This object needs **none** of the default-prohibited machinery in
`docs/project/ENGINEERING_SCOPE_SPEC.md` section 4: no distributed or resumable execution, worker
pool, queue, scheduler, retry/lease/lock/heartbeat, tamper evidence, byte manifest, provenance or
HEAD-currentness guard, incident tree, schema framework, registry, telemetry beyond wall time and
peak RSS, compatibility shim, or repeated smoke loop. Remote placement is external execution of
one ordinary process, not machinery added to the research code.

CM owns only:

- `experiments/candidates/commitment_residual_triggered_options/raw_phase_trace_a01/`;
- `scripts/run_crto_raw_phase_trace_a01.py`; and
- `tests/experiments/candidates/commitment_residual_triggered_options/raw_phase_trace_a01/`.

The accepted B01 implementation and historical evidence are read-only dependencies. The new
attempt stays below 2,000 non-test lines, the runner below 600 lines, orchestration below 30 percent,
and tests consist of one under-60-second toy end-to-end smoke plus focused trace-rule, anchor,
count, and information-boundary checks. Any section 5 budget breach is returned rather than
accepted as the price of a result.

## 12. Object-tier unattended decision

Options checked at the current clean boundary:

- **(a)** freeze and implement the already selected RAW-only update-`252..264` A/RECON trace on
  the unchanged B01 panel;
- **(b)** bypass localization and pay for a larger-budget RAW/TRUE/DERANGED B rerun; or
- **(c)** replace/enlarge RAW or lower its registered side thresholds before diagnosing the
  current path.

Recommendation: **(a)**. It is the smallest runnable object because it reuses the accepted B01
population and learner primitives, observes only the missing thirteen checkpoints, and preserves
the exact comparator meaning. Options (b) and (c) change or enlarge the comparison before the
accepted checkpoint-phase alternative is measured.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** The action is reversible,
opens no direction family, changes no frozen result, and makes no Direction- or Portfolio-tier
decision.
