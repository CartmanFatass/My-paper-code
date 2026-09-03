# CBSC-OMRC-B01 — section 11 recast intake (2026-09-02)

- Direction: `capability_bound_semantic_currentness`
- Object continued here: `CBSC-OMRC-B01` (`B/EXPLORE`), next run
  `CBSC-OMRC-B1-THREE-SEED-SCOUT`, seeds `21101, 21121, 21143`
- Object registered here: `CBSC-OMRC-B1B-FOUR-TIMES-EXPOSURE` (`B/EXPLORE`), rung 2 of a named
  exposure ladder, declared before any B1 data exists
- Controlling documents whose frozen bodies are unchanged:
  `CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md`, `CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md`,
  `CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md` (each gets a dated addendum, not an edit)
- Governing method: `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, §11 controlling

This is the §11.6 record of the demotion ("Direction owners SHOULD record the demotion in the
direction's next intake rather than rewrite historical documents"). It changes no scientific factor
of `CBSC-OMRC-B01` — not the host, arms, adapters, learner, PPO settings, seeds, budgets,
checkpoints, held-out tapes, competence predicate or claim ceiling — and it produces no currentness
observation.

## 1. Provenance of the decisions implemented here

- `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`, Part A.4, decisions 3
  and 7; the CBSC audit with `file:line` for every gate is Part B section 3 of the same file.
- `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`
  (`FINAL / OWNER_DIRECT / ROOT_INTEGRATED`, portfolio node `portfolio:cross_direction`).
- The object and the ladder come from `docs/Claude_docs/reviews/FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md`
  §3 (`smallest_next_object`, disposition `CONTINUE`) and its 2026-09-02 addendum row for CBSC.

Decision 3, verbatim from A.4:

> Recast per §11 and run the frozen B1: `FORMAL_ANALYSIS_BOUND`, `READINESS_DISPOSITION` and the
> two publication raises become recorded fields; descriptive curves are published directly; B1b
> (4× updates) is declared now as the next ladder rung

Decision 7, verbatim from A.4:

> Downgrade, not annul: a run whose resource telemetry (peak RSS, scratch, wall) is missing stays
> valid and is marked "resources unmeasured"; annulment only when the claim itself is a resource
> claim. Learner-side instrumentation failure (missing logs or checkpoints) still quarantines under
> §6.2

The reviewer's concrete reading of decision 3, from A.2, verbatim:

> **CBSC.** `FORMAL_ANALYSIS_BOUND`, `READINESS_DISPOSITION` and the two publication raises become
> recorded fields; the frozen three-seed B1 runs and its descriptive curves (per-checkpoint returns,
> serve rate, actions, competence flags) are published directly rather than as literal nulls for a
> consumer to recompute. B1b (4× updates) is declared now as a named exposure ladder rung.

The 2026-09-02 addendum to the independent review states the same recast for this direction:

> CBSC | `CONTINUE` | `FORMAL_ANALYSIS_BOUND = False` and the consumer-recompute and capacity gates
> may not hold a B launch (§11.4). | The three-seed B1 with a budget ladder, launched without the
> gates.

## 2. What §11 demotes in this direction

Each row is quoted from the compliance note's CBSC audit (Part B section 3) with the `file:line`
that note gives. "CM contract" is `CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md`, "DIRECTION.md" is
this direction's file, and the code paths are relative to
`experiments/candidates/capability_bound_semantic_currentness/`. All are as committed unchanged in
`Record CBSC working-tree state before the section 11 recast` (`335559bcf`).

| # | Demoted condition (quoted) | file:line | Class in the audit | Now |
| --- | --- | --- | --- | --- |
| 1 | `FORMAL_ANALYSIS_BOUND = False` → `blockers.append("formal .03 metrics analysis/publication law is not bound")`; `if READINESS_DISPOSITION != "READY": blockers.append(...)` | `omrc_b01/b1_metrics_artifact.py:41-42`; `omrc_b01/b1.py:102-105` | DEMOTED (§11.6, formal-analysis-bound flags that refuse a complete learner chain) | **recorded fields.** Both constants keep their historical values in the source so the history stays visible; the two `blockers.append` lines are deleted, and `formal_analysis_record()` publishes `formal_analysis_bound`, `readiness_disposition`, `gating: false`, the demoting clause and the two provenance paths. It appears in `readiness_document()` and in every manifest |
| 2 | `raise B1MetricsProductionError("REPAIR_REQUIRED: formal metrics publication awaits whole-pipeline CLEAN review")` | `omrc_b01/b1_metrics_production.py:1580-1583, 1913-1916` | DEMOTED (§11.4 capacity gate) | **both raises deleted**, each replaced by a comment quoting what stood there. A third refusal on the same path, `MetricsArtifactError("FORMAL_ANALYSIS_BOUND is false and caller manifests cannot replace canonical attempt reconstruction")` at `b1_metrics_artifact.py:1331-1335`, and the `or not FORMAL_ANALYSIS_BOUND` clause of `"formal metrics manifest is not currently bound"` at `:1477`, are removed with them. The caller-manifest and transaction-witness refusals that do not read the flag are unchanged |
| 3 | "Implementation readiness does not authorize result execution. Before B1, CM must first establish literal-law conformance, full recurrent-PPO rather than Q/replay realization, B0 completeness, resource admission/telemetry, create-only publication, and every parity audit." | CM contract:156-159 | Mixed: PPO-realization + parity ALLOWED (§4.2/§4.5); "create-only publication" + "every parity audit" as a launch gate DEMOTED (§11.4) | split as the audit splits it. Literal-law conformance, real recurrent PPO (not Q/replay), the parity audits and adaptation-free evaluation remain and still run — they are §4/§5.2 items. "Create-only publication" remains as a *publication* property (nothing is overwritten) but is no longer a pre-launch condition. "B0 completeness" is section 6 below |
| 4 | "It must set every derived AUC/mean/regret, diagnostic, separation/concentration/instability, adverse-seed, promotion, B2-trigger, branch, and polarity field to literal null." | CM contract:123-127; DIRECTION.md:285-291 | DEMOTED (§11.6, consumer-recompute gate that does not change a B decision) | **superseded for descriptive quantities only**; see section 3. The interpretive fields (`scientific_branch`, `scientific_polarity`, `promotion_eligible`, `b2_extension_trigger`) and the named AUC/diagnostic *definitions* stay literal null, because engineering still has no threshold or branch authority. What the runner now computes and publishes is a `descriptive_curves` block |
| 5 | "False or null competence blocks both STRUCT interpretation and B2" (mechanical RAW-competence gate: beat `ALWAYS_REFRESH`/`ALWAYS_SAFE`, ≥ 80% serve, ≥ 2 actions, zero missing records) | DIRECTION.md:293-298 | **ALLOWED** (§4.2; the review also classes it `SCIENTIFICALLY_NECESSARY`) | **unchanged and still in force.** It is computed by the runner itself in `b1_mechanical.compute_raw_competence`, published per seed in `mechanical.raw_competence_by_seed`, in the `raw_competence` table, and again in `descriptive_curves.raw_competence_flags`. A false or null result still emits `RAW_COMPETENCE_FAILURE` / `RAW_COMPETENCE_UNESTABLISHED` |
| 6 | "`CBSC-OMRC-B2-TWO-SEED-STABILITY` may add unchanged seeds `21161, 21179` only after the mandatory interim `em:…:convergence` decision returns `RUN_FIXED_B2_STABILITY`." | DIRECTION.md:279-281 | DEMOTED (§11.1; §5.2 permits adaptation between named B runs) | **recorded as the direction's own sequencing**, not as an external gate; see section 5. B2 keeps its exact frozen definition — seeds `21161, 21179`, unchanged, no replacement — and is simply no longer chained behind an external convergence decision |
| 7 | "Immediately before every B0 arm or B1/B2 arm-seed invocation or slice, run `python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require at least 4 GiB physical and effective available memory." | CM contract:115-117 | **ALLOWED** (§11.4 resource admission) | **unchanged and still gating.** Enforced per arm-seed invocation and per slice by `b1.validate_bound_admission`, which binds the receipt to the exact invocation, executable, script bytes and command line |
| 8 | "Per invocation, peak RSS is capped at 4 GiB and scratch at 2 GiB; B0 wall time is capped at 30 minutes and B1/B2 at 120 minutes." | CM contract:117-119 | ALLOWED as budget; DEMOTED if used as an invalidator | **recorded budgets.** `telemetry.assess_resource_telemetry` records every measured exceedance in `cap_exceedances`; `STOPPING_CAPS = ("wall_seconds",)`, so only the 120-minute wall cap stops a run. The 4 GiB RSS, 2 GiB scratch and 512 MiB durable caps are published, not enforced, and `b1_metrics_training_assembly.RECORDED_BUDGET_CAPS` stops them refusing inside the assembly |
| 9 | "The implementation must exercise the real environment, policy, recurrent learner, PPO trainer, and adaptation-free held-out evaluator with nonzero transitions, optimizer updates, and evaluations." | CM contract:23-25 | **ALLOWED** (§5.2 / §11.4 nonzero counts) | **unchanged and still gating.** The assembly reconciles each slice's `scientific_work_transitions` and stage sums against the raw `slice_counts` exactly, and refuses on any difference |
| 10 | "Implementation/instrumentation failure, leakage, support failure, unequal exposure, evaluator overlap, recurrent-reset defect, or RAW incompetence is a blocking mechanical fact" | CM contract:129-132 | UNCLEAR (§11.4's final sentence left instrumentation-failure semantics undecided) | **resolved by decision 7, and split.** *Resource* telemetry that is missing, unreadable or invalid downgrades: `resources_unmeasured: true` with `unmeasured_reasons`, and the attempt stays valid. *Learner-side* instrumentation failure — absent or unreadable worker result, recurrent-reset defect, checkpoint round-trip failure, learner leakage, unequal exposure, illegal action, incomplete twins — still refuses and still quarantines under §6.2 |

Rows 1, 2 and 8 were live code; rows 3, 4, 6 and 10 were prose; rows 5, 7 and 9 stay.

Two further gates in the untracked-until-today metrics-only spec belong to the same family and are
recorded here rather than edited: `CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md:192-217`
(the literal-null derived-field list) is superseded exactly as row 4 supersedes the CM contract's
sentence, and `:246` ("If any B1 RAW seed is false or null, engineering cannot declare STRUCT
supported or contradicted and B2 cannot launch") stays in force as row 5, with the B2 clause read
under row 6.

## 3. The consumer-recompute boundary, superseded

The sentences superseded, quoted in full so that the change is visible without reading the diff.

`DIRECTION.md:285-291`:

> Engineering publishes exact undiscounted per-tape episode returns at updates `0,12,24,48`, every
> paired raw seed curve, complete evaluator truth and potential ledger, policy decisions, motif/twin
> identities, event order, body age, training/optimizer exposure, support indexes, and all conformance
> facts. It does not compute AUC, terminal or panel means, oracle-regret summaries, diagnostic rates or
> effects, arm contrasts, thresholds, signs, or branches. Those fields remain literal null until a
> separate Convergence decision.

`CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md:125-127`:

> It must set every derived AUC/mean/regret, diagnostic, separation/concentration/instability,
> adverse-seed, promotion, B2-trigger, branch, and polarity field to literal null.

`CBSC_OMRC_B01_METRICS_ONLY_CONVERGENCE_SPEC.md:48-52`:

> Every named action/currentness diagnostic is likewise deferred. Engineering publishes exact truth,
> policy action, potential ledger, motif/twin identity, event order, body age, and support, but no
> numerator, denominator, eligible-support rule, panel scope, split pooling, per-seed aggregation,
> checkpoint reduction, paired unit, minimum support, zero-denominator rule, effect, or interpretation.

What replaces them, and what does not. The runner now computes from its own materialized tables and
publishes a `descriptive_curves` block (`omrc_b01/b1_descriptive.py`, schema
`cbsc_omrc_b01_b1_descriptive_curves_v1`), carrying:

- `heldout_return_curves` — per `(seed, arm, split)`, the mean, minimum and maximum per-tape episode
  return at each of updates `0, 12, 24, 48`, as exact reduced fractions;
- `heldout_action_counts` — per `(seed, arm, split, checkpoint)`, the SERVE / REFRESH /
  SAFE_FALLBACK counts, the decision count, the number of distinct actions, and the serve rate as an
  exact fraction;
- `training_episode_action_counts` — per `(seed, arm)`, the training-side action counts and the
  first and last episode returns;
- `exposure_line` — per `(seed, arm)`, the realized Adam step count, whether the parameter digest
  actually changed across those steps, and the first, last, minimum, maximum and summed post-clip
  gradient norms;
- `raw_competence_flags` — the mechanical gate's own per-seed pass flag, its five components, the
  RAW / ALWAYS_REFRESH / ALWAYS_SAFE mean returns, the easy-OPEN serve fraction and counts, the RAW
  and oracle action counts, and the four integrity counts.

Everything the superseded sentences said engineering may *not* choose is still not chosen. There is
no AUC normalization (no x divisor, y normalization, panel pooling, seed aggregation or pairing
rule), no arm contrast, no threshold, no sign, no promotion flag and no branch. The manifest's
`derived_fields`, `auc_metadata`, `diagnostic_metadata`, `scientific_branch`, `scientific_polarity`,
`promotion_eligible` and `b2_extension_trigger` remain literal null, and the null-packet validator is
unchanged. The lossless 15-table raw publication is unchanged: per-tape returns, per-decision actions
and truth, per-step losses and the `postclip_gradient_norm_fp32_bits` /
`parameter_sha256_after_step` exposure line are still published row by row.

The reason for the change is §11.6's: the delegation is a "consumer-recompute gate that does not
change a B decision". A descriptive mean of 64 held-out episode returns is not an interpretation; a
branch is. The former is now published, the latter still is not.

## 4. `CBSC-OMRC-B1B-FOUR-TIMES-EXPOSURE`, registered now

### 4.1 Why this is a named rung and not a budget enlargement

`DIRECTION.md:311-313` says "No sixth seed, selected checkpoint, larger budget, or altered adapter
belongs to B01", and `CM contract:112-113` says "There is no sixth seed, selected checkpoint, silent
budget increase, or adapter/host/reward redesign inside B01". Both stand. B1b is **not inside B01**:
it is a separate named B object with its own launch, its own admission, its own artifact and its own
result document, declared here before any B1 datum exists. Under §5.2 the EM "MAY revise
architecture, hyperparameters, reward-independent mechanism details, host, budget, measurement, and
comparator **between named runs**", and under §11.1 the B-EXPLORE ladder is the default early mode.
The words "silent budget increase" are the ones that matter: this rung is declared in advance, in
writing, with its reading rule fixed before the data, which is the opposite of silent.

Nothing else in either sentence is superseded. No sixth seed, no selected checkpoint, no altered
adapter, no host or reward redesign.

### 4.2 The object

| | B1 (rung 1) | B1b (rung 2) |
| --- | --- | --- |
| Seeds | `21101, 21121, 21143` | same three, unchanged |
| Arms | STRUCT / RAW / PI / DERANGED | same four, unchanged |
| Training episodes per arm-seed | 384 | 1,536 |
| Rollout updates | 48 | 192 |
| Adam steps per arm-seed | 768 | 3,072 |
| Checkpoints | `0, 12, 24, 48` | `0, 48, 96, 192` |
| Held-out episodes per checkpoint | 64 | 64, unchanged |
| Everything else | frozen | identical to B1 |

"Everything else" means: the `CBSC-DYNAMIC-CACHE-2R-1C-v1` host and its event probabilities and
ledger, the eight-token preamble, 24 opportunities and 152 primitive transitions per episode, the
four adapters, the `168 → Linear(128) → ReLU → GRU(128) → actor(4), value(1)` learner with `121,349`
parameters, PPO `gamma=1` / GAE `0.95` / clip `0.20` / value `0.50` / entropy `0.01` / Adam `3e-4`
with betas `(0.9, 0.999)`, eps `1e-8`, no weight decay and gradient cap `0.5`, four PPO epochs and
four two-episode minibatches per update, the held-out stochastic and fixed-motif tape families, the
counter-addressed PRF, and the mechanical RAW-competence predicate at its exact thresholds. The
single declared axis is **optimizer exposure**, four times B1's.

The exposure ladder respects the object-level exposure cap in `DIRECTION.md:281-283`
("B0+B1+B2 is capped at two million primitive transitions; B1+B2 has at most 15,360 Adam steps") the
way §5.2 requires: that cap belongs to B01, and B1b is a separate object whose own budget is stated
here (4 arms × 3 seeds × 1,536 episodes × 152 transitions ≈ 2.80 M primitive transitions, 36,864 Adam
steps). This is a declared change with its reason recorded, not a silent enlargement of B01.

### 4.3 The two mechanisms and what distinguishes them

Both are candidate explanations of whatever B1 shows, and the ladder exists because they are not
separable at one budget.

- **Mechanism A — the typed currentness register is an inductive bias that saves optimizer
  exposure.** The direction's own prediction (`FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md` §3,
  `mechanism_prediction`): "STRUCT reaches RAW-competence earlier (updates 12–24 rather than 48) and
  holds a return edge at 48; DERANGED does not". If A holds, the STRUCT−RAW gap is largest early and
  narrows as RAW is given enough steps to learn the same function from 136 raw channels over 152
  transitions with delayed settlement.
- **Mechanism B — the budget is simply too small for any arm.** The review's first-listed
  alternative: "48 PPO updates (384 episodes, 768 Adam steps) is a very small budget for a 121,349-
  parameter GRU on a 24-opportunity POMDP with delayed settlement… the most likely outcome is that
  RAW fails the mechanical competence gate, yielding `NO_B2_INTERPRETATION_BLOCKED` with no learning
  read at all". If B holds, every arm sits near its initialisation and the four curves are
  indistinguishable for a reason that has nothing to do with currentness.

**What distinguishes them.** B1b multiplies optimizer exposure by exactly four while holding the
host, tapes, seeds, arms, learner, adapters, PPO settings, evaluator and competence predicate fixed,
so exposure is the only quantity that differs. Under A, RAW's competence and the four arms' ordering
should be *more* resolved at 192 updates than at 48, and any early STRUCT advantage should be
visible as a shift in the update at which competence is first reached. Under B, quadrupling exposure
moves the arms off their initialisation; if it does not, exposure was never the binding constraint
and the host or the package is. The `exposure_line` published by both runs is what makes this
checkable rather than assumed: it states, per arm-seed, whether the parameters moved at all and by
how much gradient the optimizer was driven.

### 4.4 Differentiating measurement and reading rule — written before any B1 or B1b data

Applied verbatim after B1b, using only quantities defined here and computed by the runner.

Definitions, all from the frozen objects:

- `competent(seed)` = the mechanical `raw_competence_pass` for RAW at that run's terminal checkpoint
  (`48` for B1, `192` for B1b), unchanged in threshold and in components.
- `first_competent_update(seed)` = the smallest checkpoint at which a given arm satisfies the same
  four competence components computed against the same reference arms. Null if none does.
- `moved(arm, seed)` = `descriptive_curves.exposure_line[arm, seed].parameters_moved`, i.e. the
  parameter digest changed across the run's Adam steps.
- `terminal_mean(arm, seed, split)` = the mean per-tape held-out episode return at the terminal
  checkpoint, from `heldout_return_curves`.

Branches, evaluated in order:

- **L2-A — exposure resolves the comparison.** No RAW seed is competent in B1 and at least one RAW
  seed is competent in B1b. Reading: B1's null was a budget null (mechanism B for B1), B1b is the
  informative rung, and the STRUCT/DERANGED/PI comparison is read at B1b's terminal checkpoint, not
  at B1's.
- **L2-B — exposure changes nothing and the learner did move.** No RAW seed is competent in either
  run and `moved` is true for all twelve arm-seeds in B1b. Reading: a four-fold exposure increase
  does not make this host learnable by this package; the direction's next question is the host or the
  package, not the budget. Neither run supports or contradicts the currentness mechanism.
- **L2-C — exposure changes nothing and the learner did not move.** No RAW seed is competent in
  either run and `moved` is false for any arm-seed in B1b. Reading: an instrumentation or
  optimizer-configuration fact, not a mechanism fact; the run is a technical failure, quarantined
  under §6.2, and creates no polarity and no retry budget.
- **L2-D — competence is already reached in B1.** At least one RAW seed is competent in B1. Reading:
  B1 is itself informative, B1b is a stability-and-ordering check rather than a competence check, and
  the ordering of the four `terminal_mean` values at each run's terminal checkpoint is compared
  between the two rungs. A currentness reading requires the same ordering in both.

In every branch, `min`, `max` and per-seed spreads are reported alongside means, adverse seeds are
reported, and no branch is a direction decision. The claim ceiling of section 4.5 binds all four.

B1b runs only after B1 completes as a valid attempt. If B1 is quarantined as a technical failure,
B1b is not a repair substitute and does not run on B1's account.

### 4.5 Claim ceiling and non-goals for both rungs

Unchanged from `DIRECTION.md:315-320`: at most one preliminary recurrent-PPO learning signal, null,
instability diagnosis, generic-control explanation, predictive-index-sufficiency observation, or
adverse counterexample on `CBSC-DYNAMIC-CACHE-2R-1C-v1`. No stable or general superiority, no
representation necessity, no natural frequency, no proactive acquisition, no
authentication/security, no communication or credit value, no variable-population/lifetime or MARL
coordination value, no UAV transfer, no safety, no deployment, no direction convergence, and no
reinterpretation of the exact factorial or of `CBSC-LR01 = UNRESOLVED`. Both remain consumed as
recorded.

## 5. B2, as the direction's own sequencing

`DIRECTION.md:279-281` and `CM contract:110-111` chain `CBSC-OMRC-B2-TWO-SEED-STABILITY` behind a
mandatory external `em:capability_bound_semantic_currentness:convergence` decision returning
`RUN_FIXED_B2_STABILITY`. §11.1 makes consumption semantics and prospective decision authority
C-time obligations; §5.2 permits adaptation between named B runs. The external convergence decision
is therefore recorded here as **no longer a launch condition**.

What is unchanged: B2 is still exactly seeds `21161` and `21179`, unchanged, with no seed
replacement and no altered adapter, host or reward. What replaces the chain is the direction's own
sequencing, stated now: B2 runs only after three complete valid B1 seeds and only as an
outcome-informed stability extension, labelled `outcome_informed_from_B1 = true` and
`confirmatory = false` exactly as `DIRECTION.md:309-311` already requires. The formulas B2 would be
read by, if it runs, must still be recorded before it runs. `convergence_required` stays `true` in
every B1 manifest as a recorded routing fact; it no longer blocks anything in code.

The exposure ladder and B2 are different objects answering different questions: the ladder asks
whether the budget binds, B2 asks whether a B1 signal repeats on two more seeds. The ladder comes
first, because a stability extension of an uninformative budget is not informative either.

## 6. B0 completeness — what was found

`CM contract:157-158` requires "B0 completeness" before B1. The finding, recorded as an observation
and not an inference:

- `CBSC-OMRC-B0-INSTRUMENT` ran. Its artifact is
  `temp/directions/capability_bound_semantic_currentness/exp/cbsc_omrc_b0_instrument_888bd9f50_r02`.
- **No direction document records its acceptance.** A repository-wide search of
  `docs/research/candidates/capability_bound_semantic_currentness/` returns no B0 result intake, no
  B0 technical acceptance and no B0 result evidence document. The compliance note's own
  "what I could not determine" list says the same: "whether CBSC's B0 artifact
  `cbsc_omrc_b0_instrument_888bd9f50_r02` was accepted as complete (I did not open it)".
- The **only** acceptance record is in code: `omrc_b01/b1.py`'s `B0_REVIEWED_AUTHORITY` constant,
  which records `review_disposition: "CLEAN"`, `reviewer_scope: "B0_ENGINEERING_EVIDENCE_COMPLETE"`,
  `source_commit: 888bd9f50eeea2f6b99d23b9b53b9f4724e19939`, a manifest of `733,056` bytes with
  SHA-256 `c7c6f73b…`, an inventory of `33` files totalling `12,807,274` bytes, and an inventory
  digest `184fa6ad…`. Who reviewed it, and against what, is not recorded anywhere.
- **The artifact is currently unreadable.** As of 2026-09-02 the directory denies enumeration and
  file access to the repository owner's account (`PermissionError [WinError 5]` on `iterdir` and on
  `manifest.json`; `icacls` cannot read its ACL; `dir /q` cannot resolve its owner). Every sibling
  artifact under the same parent is owned by `JACOB\fires` and is readable. So none of the recorded
  digests can be verified today, and `b1.locate_b0_evidence`, which reads all 33 files and rehashes
  them, cannot run. This is recorded as an engineering fact; the cause is not established.

Consequence, stated plainly: the frozen B1 as implemented **cannot launch** until that directory is
readable again, because `run_b1_start` binds and copies the B0 evidence into the B1 artifact before
anything else. This is not a §11 gate and this intake does not demote it — it is a filesystem
permission fact about a file the frozen publication schema requires. The remedy is the owner
restoring access with elevated rights, exactly as with the `%LOCALAPPDATA%\Temp\hmasd_*_native`
caches cleared for SCDMP on the same day. If access cannot be restored, the B0 byte binding is
itself a §11.4 byte-manifest gate and demoting it is a separate decision that this intake does not
take.

B0 keeps `B0_NONPOLARITY = ABSOLUTE` regardless: it audits arithmetic, replay, masks, checkpoints,
publication and telemetry, and it selects no formula, threshold, branch, endpoint, seed, budget or
comparator.

## 7. What remains a launch condition

Unchanged and still binding for B1 and B1b:

- the §4 common integrity requirements, in full;
- the §5.2 requirement that the real environment, policy, recurrent learner, PPO trainer and
  adaptation-free held-out evaluator run and report nonzero transition, optimizer-update and
  evaluation counts — audit row 9 (CM contract:23-25), classed ALLOWED. Every slice's
  `scientific_work_transitions` and stage sums are reconciled exactly against the raw `slice_counts`
  and the run stops on any difference;
- the mandatory resource admission — audit row 7 (CM contract:115-117), classed ALLOWED. Run per
  arm-seed invocation and per slice as
  `python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>`, requiring at least
  4 GiB physical *and* effective available memory, with the receipt bound to the exact invocation,
  interpreter, script bytes and command line;
- one machine-generated **exposure line** (§11.4): `descriptive_curves.exposure_line`, computed by
  the runner per arm-seed from its own optimizer-step records — realized Adam step count, whether
  the parameter digest moved, and the post-clip gradient-norm magnitudes;
- the leakage and equal-exposure boundary: identical primitive histories, masks, initialisation
  outside the declared adapter, parameter count and precision, interactions, full-episode BPTT, PPO
  epoch and minibatch order, Adam exposure, checkpoints, held-out roots, common action-uniform draws
  and zero model-selection exposure within a seed; STRUCT/DERANGED adapter-work parity; train and
  held-out separation. Every one of these is still an audited mechanical component that refuses;
- the mechanical RAW-competence gate (audit row 5), unchanged in threshold and in components;
- the 120-minute wall cap, the only resource cap that stops a run;
- create-only publication, and the §6.2 quarantine of an incomplete attempt. **Learner-side
  instrumentation failure still quarantines**; only resource telemetry is downgraded.

Also unchanged, though not launch conditions: at most 4 torch threads per process (the engine sets
`torch.set_num_threads(1)` and runs `worker_count = 1`), and one arm-seed at a time.

## 8. Limits of the D7 implementation, recorded

Decision 7 is implemented where a resource measurement is first read and judged:
`telemetry.assess_resource_telemetry` never raises, and `b1._load_slot_evidence` records
`resources_unmeasured`, `unmeasured_reasons` and `recorded_cap_exceedances` on the slot's telemetry
record instead of refusing. The measured-cap refusals inside `b1_metrics_training_assembly` are
relaxed to `RECORDED_BUDGET_CAPS`, so a measured exceedance is published rather than refused.

What is **not** implemented, and is recorded rather than claimed: the frozen 15-table publication
schema requires a complete, finite, nonzero-work measurement per invocation, because the work
reconciliation against `slice_counts` is a §4 integrity item that reads the same record. A run whose
resource telemetry is entirely absent therefore downgrades at the slot boundary but would still not
reach a published 15-table artifact. Threading a null measurement through the frozen schema is a
larger change to a frozen publication than this recast authorizes, and it has not been made. If a
real run meets that case, the downgrade is recorded and the case is brought back to the owner.

## 9. What this intake does not do

It records no currentness, competence, exposure or return observation; changes no host, adapter,
arm, learner, PPO setting, seed, tape family, checkpoint, competence threshold, comparator or claim
ceiling; and consumes no scientific object. It establishes no algorithm performance, stability,
promotion, retirement, lifecycle, transfer, safety or general-MARL claim. `CBSC-EXACT-FACTORIAL-V1`
and `CBSC-LR01` stay consumed exactly as recorded, and neither is rerun, rescued or reinterpreted.

Two code consequences are recorded for honesty. First, `omrc_b01/b1_descriptive.py` is a new module
on the publication path and is added to `b1.CANONICAL_SOURCE_SURFACE`, so it must be tracked and
clean at launch like every other formal source file. Second, `readiness` with no arguments now
reports `start_authorized: true` and exits 0, where it previously reported `false` and exited 4; the
source-conformance and B0 bindings that `start` performs itself are unchanged, so nothing that
`start` checked before is unchecked now.

## 10. Relation to `flexible_skill_duration`

`docs/research/candidates/flexible_skill_duration/DIRECTION.md`, "Relations to other directions"
(line 50), states:

> The relay corridor host family reserves parameter points for FRRIE, VNFC, SCDMP, UCOPE and CBSC
> (ADR 02 "Decision"); the host is shared infrastructure, not a claim of this direction.

That is the whole relation: a reserved parameter point on a shared host family. `flexible_skill_duration`
lists no CBSC mechanism, comparator or transfer test, and CBSC contributes none to it. Nothing there
gates, blocks or redirects `CBSC-OMRC-B01`, and CBSC's objects continue independently on
`CBSC-DYNAMIC-CACHE-2R-1C-v1`, not on the corridor host. Per §11.5 the untied-`k` and untied-`N`
programmes remain separate directions; this intake opens no joint object.

## 11. Result

Pending. `CBSC-OMRC-B1-THREE-SEED-SCOUT` had not launched when this intake was written; the run and
its E0-format evidence document (`CBSC_OMRC_B1_THREE_SEED_SCOUT_RESULT_EVIDENCE_20260902.md`) follow
in a later commit, and the blocker recorded in section 6 must be cleared first.
