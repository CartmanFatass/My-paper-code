# UCOPE — section 11 recast intake (2026-09-02)

- Direction: `ucope`
- Objects registered or continued here:
  - `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01` (`B/EXPLORE`) — **new named object**, rung 1 runs first
  - `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01` (`B/EXPLORE`) — continues, **alongside**
- Controlling contract for the discriminator:
  `UCOPE_B_EXPLORE_FT_XF_BC_INVERTIBLE_CONDITIONING_DISCRIMINATOR_R01_PROSPECTIVE_CONTRACT_20260901.md`
  (frozen body unchanged; a dated addendum records the same demotion)
- Governing method: `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, §11 controlling

This is the §11.6 record of the demotion ("Direction owners SHOULD record the demotion in the
direction's next intake rather than rewrite historical documents"). It changes no scientific factor
of either object and produces no competence, conditioning or acquisition observation.

## 1. Provenance of the decisions implemented here

- `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`, Part A.4, decisions 2
  and 7; the UCOPE audit with `file:line` for every gate is Part B section 5 of the same file.
- `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`
  (`FINAL / OWNER_DIRECT / ROOT_INTEGRATED`, portfolio node `portfolio:cross_direction`).
- The objects themselves come from `docs/Claude_docs/reviews/FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md`
  §5 (`smallest_next_object`, disposition `RECAST`) and its 2026-09-02 addendum row for UCOPE.

Decision 2, verbatim from A.4:

> Recast per §11: the exposure ladder is registered as a named B object and runs first; the
> whitening discriminator runs alongside, not instead; the exact-oracle competence predicate becomes
> a recorded observation; the runner's clean-source and assessment-03 refusals become recorded
> fields

Decision 7, verbatim from A.4:

> Downgrade, not annul: a run whose resource telemetry (peak RSS, scratch, wall) is missing stays
> valid and is marked "resources unmeasured"; annulment only when the claim itself is a resource
> claim. Learner-side instrumentation failure (missing logs or checkpoints) still quarantines under
> §6.2

The 2026-09-02 addendum to the independent review states the same recast for this direction:

> UCOPE | `RECAST` | The exact-oracle competence criterion stops being a pass/fail gate on a B run
> and becomes a recorded observation; the exposure arithmetic becomes the one mandatory exposure
> line. | Exposure ladder first, whitening discriminator alongside; competence at training durations
> is a B observation, and the odd/even duration split is the later C-time obligation.

## 2. What §11 demotes in this direction

Each row is quoted from the compliance note's UCOPE audit (Part B section 5) with the `file:line`
that note gives. "Contract" is
`UCOPE_B_EXPLORE_FT_XF_BC_INVERTIBLE_CONDITIONING_DISCRIMINATOR_R01_PROSPECTIVE_CONTRACT_20260901.md`
and "DIRECTION.md" is the working-tree file, both as committed in
`Record UCOPE working-tree state before the section 11 recast` (`3423d5aca`).

| # | Demoted condition (quoted) | file:line | Class in the audit | Now |
| --- | --- | --- | --- | --- |
| 1 | "Before any result-bearing invocation, CM must return implementation evidence showing: 1. … 8. create-once manifest/checkpoint/result binding, full activity and resource telemetry, complete-only publication, and incomplete-attempt quarantine" | prospective contract:462, 478-479 | DEMOTED (§11.4) | the create-once binding, complete-only publication and incomplete-attempt quarantine are unchanged and still in force; only "full … resource telemetry" as a *pre-launch* condition is demoted, to a recorded `resources_unmeasured` field per decision 7 |
| 2 | "CM must also produce outcome-blind A/RECON performance evidence for the exact implementation." | prospective contract:483-484 | DEMOTED (§11.4 capacity gate) | recorded: `performance_assessment` in the run manifest and in `recast-record.json` carries whichever assessment exists, with `gating: false` |
| 3 | "Otherwise it remains `REPAIR_REQUIRED` with no science. … A later manifest may bind only the exact create-once `assessment-03` bytes, their source aggregate, V3 schema, V2 projection law, frozen topology, and `PERFORMANCE_READY` disposition." | prospective contract:705-708 | DEMOTED (§11.4 byte manifest + capacity gate) | recorded. `assessment-03` does not exist. `temp/directions/ucope/controls/ucope-bc-conditioning-r01/assessments/assessment-02.json` exists, is schema `…_V2`, and carries `"disposition": "PERFORMANCE_READY"`; contract:561 declares it `ASSESSMENT_02_READINESS=INVALID_NOT_ADOPTED`. **Both facts are recorded and neither gates.** |
| 4 | `if status.stdout.strip(): raise RunnerRefusal("prepare-run requires clean committed source inventory")` | `scripts/run_ucope_bc_conditioning_discriminator_r01.py:82` | DEMOTED (§11.4 byte manifests) | replaced by `source_binding()`, which records the `git status --porcelain --untracked-files=all` lines, `clean`, and the HEAD SHA, then proceeds. The per-file size/SHA-256 inventory is still recorded |
| 5 | `if observed != record or assessment["disposition"] != "PERFORMANCE_READY": raise RunnerRefusal(...)` | `scripts/run_ucope_bc_conditioning_discriminator_r01.py:127` | DEMOTED (§11.4 capacity gate) | replaced by `recorded_assessment()` / `_validate_bound_assessment()`, which record the resolved assessment, its disposition, the contract's declaration for it, and whether it matches the manifest — with `gating: false` |
| 6 | "The result manifest must bind a clean committed source revision, source-byte inventory, exact config, three seeds, RNG/data ancestry law…" | prospective contract:711-714 | DEMOTED (§11.4 byte manifests) | the exact config, three seeds, RNG/data-ancestry law, batch law, transform implementation and zero-effect firewall are still bound and still validated. Only "clean committed" is demoted; the revision and inventory are recorded either way |
| 7 | `C_even(P) = … AND exact_eight_context_oracle_root_vector AND maximum_expected_regret <= 1/50 AND minimum_forced_PROBE_tail_agreement >= 19/20`; "Update 320 alone controls competence." | prospective contract:324-333 | DEMOTED (§11.1 oracle-retuned comparator as a pass/fail condition) | **recorded observation, reported per run.** The predicate is computed unchanged at exactly the same thresholds and published per arm/seed/fold/checkpoint. It is not a gate on the run's completion, on publication, on the ladder, or on the discriminator |
| 8 | "even a conditioning competence pass cannot open either automatically" (acquisition and COUNT/RAW stay locked) | DIRECTION.md:62-63 | DEMOTED (§11.1 / §11.4) | recorded as the **direction's own sequencing choice**, not as a §11 gate. This intake does not open the acquisition evaluation or COUNT/RAW; opening either needs a separately named object |
| 9 | "No unchanged B1 repeat, audit rerun, extra B1/audit score read, budget enlargement, acquisition evaluation, or COUNT/RAW work is permitted." | DIRECTION.md:228-230 | DEMOTED (§11.1/§5.2) | **superseded for named ladder rungs**; see section 4 |
| 10 | "A late, different, or unverifiable topology is `REPAIR_REQUIRED`" (deterministic algorithms, 1 thread) | prospective contract:589-592 | DEMOTED as a gate; ALLOWED as a recorded fact | the topology is still configured to `torch.get_num_threads() == 1`, `get_num_interop_threads() == 1`, deterministic algorithms on, and is recorded in the manifest and the run record. It no longer refuses |

Rows 4, 5 and 7 are the three that were live code. Rows 1–3, 6, 8–10 were prose.

## 3. What remains a launch condition

Unchanged and still binding for both objects:

- the §4 common integrity requirements, in full;
- the §5.2 requirement that the real learner, trainer and evaluator run and report nonzero
  transition, optimizer-step and evaluation counts — audit row 2, "9. real environment, learner,
  trainer, checkpoint, and evaluator calls with nonzero transitions, updates, and evaluations in the
  result path" (prospective contract:480-481), classed ALLOWED. Both runners reconcile every
  activity counter against the exact expected total and stop if any differs;
- the mandatory resource admission — audit row 8, "Immediately before every result-bearing attempt,
  run the central memory admission and require both physical and effective available memory to be at
  least `4,294,967,296` bytes" (prospective contract:710-711), classed ALLOWED. Run per invocation
  as `python scripts/hmasd_resource_preflight.py admit-memory --out <run_dir>/preflight.json`,
  immediately before any RNG master, model, optimizer, checkpoint or result exists;
- one machine-generated **exposure line** (§11.4): parameter displacement relative to initialisation
  scale, computed by each runner from that run's own final checkpoints against the exact
  deterministic initialisation of the same arm/seed/fold. The ladder refuses to publish if the
  minimum absolute per-coordinate move is zero;
- the leakage boundary — audit row 13, "Group-disjoint folds", odd/even support separation, "It may
  not read B1 or audit runtime rows" (prospective contract:305-311), classed ALLOWED under §4.5;
- the no-outcome-informed-repair rule — audit row 12, "Non-positive-definite `G` stops rather than
  admitting ridge, truncation, or outcome-dependent repair" (DIRECTION.md:215-216), classed ALLOWED;
- the create-once manifest/checkpoint/result binding, complete-only publication, and §6.2
  quarantine of an incomplete attempt. **Learner-side instrumentation failure still quarantines**;
  only resource telemetry is downgraded.

The frozen objects themselves do not change: three seeds, two group-disjoint folds, 5,120 episodes
per context, batch 256, `160` tail / `320` root updates, checkpoints `{40, 80, 160, 320}`, the
eight-context host and its exact oracle, the `C_even` thresholds, the data-ancestry law, and one
thread with deterministic algorithms. The exposure ladder changes exactly one of these and says so
below.

## 4. The exposure ladder, registered as a named B object

### 4.1 Why DIRECTION.md:228-230 does not read on it

DIRECTION.md:228-230 says, verbatim:

> No unchanged B1 repeat, audit rerun, extra B1/audit score read, budget enlargement, acquisition
> evaluation, or COUNT/RAW work is permitted.

That sentence is recorded here as **superseded for named ladder rungs**, and for nothing else. The
reason, per §5.2 and §11.1:

- §5.2: "The EM MAY revise architecture, hyperparameters, reward-independent mechanism details,
  host, budget, measurement, and comparator **between named runs** after seeing earlier results.
  Each material change and its reason MUST be recorded." A ladder rung is a new named run with a
  recorded change and reason; it is not an enlargement of a running object.
- §11.1: the B-EXPLORE ladder is the project's default early mode — "One-to-three-seed runs on the
  real learner, **changed between named runs as the results suggest**, with each change and its
  reason recorded."
- The independent review's `overformalization_audit` classes
  "`AUTOMATIC_BUDGET_ENLARGEMENT=false` applied as a scientific rule" as `REMOVE_OR_DOWNGRADE`:
  "Right as a ban on silently enlarging a running object; wrong as a ban on a named exposure-ladder
  object, which tests the direction's own first-listed alternative and has never run."

The rest of that sentence stands unchanged and is not superseded: no unchanged B1 repeat, no audit
rerun, no extra B1 or audit score read, no acquisition evaluation, and no COUNT/RAW work. The ladder
reads no B1 or audit runtime row; it regenerates its own data from the counter-addressed host.

### 4.2 The object

`UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01`, evidence class `B/EXPLORE`. Implemented on the existing
B1 code (`experiments/candidates/ucope/competence_first_scout_r01/`), run by
`scripts/run_ucope_exposure_ladder_rung1.py`, configured by `ScoutConfig.ladder_rung_1()`.

Held fixed from the B1 object: the eight-context host and its exact oracle, the three fresh B1 seeds
`ucope-scout-r01-b1-fresh-{00,01,02}`, two group-disjoint folds, 5,120 episodes per context, batch
256, `160` tail / `320` root updates, checkpoints `{40, 80, 160, 320}`, the frozen-target
cross-fitted clock, the `C_even` competence predicate at its exact rational thresholds, the sampled
diagnostic at 64 paired episodes, FP32, AdamW betas/eps/weight-decay, gradient-norm clipping at 1.0,
one thread and deterministic algorithms.

Changed, and only this: **the learning rate**, which is the ladder's single declared axis, and the
**arm inventory**, which is the review's `FT-XF-FLEX` / `FT-XF-BC` pair (the `MT-XF-FLEX` arm is
omitted; the target-schedule question it carried is not this object's question). Because the RNG is
counter-addressed on `(namespace, seed, fold, index)` and never on arm order, omitting an arm leaves
the remaining two arms' data, initialisation and batches bit-identical to the three-arm B1 layout.

### 4.3 The rungs

Registered verbatim from the independent review's `smallest_next_object` for UCOPE
(`FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md`), which specifies them: "arms `FT-XF-FLEX` and
`FT-XF-BC`; 3 seeds; 2 folds; three named runs: lr `3e-3` at the frozen 160/320 updates, lr `3e-4`
at 1,600/3,200 updates, and both."

| Rung | Learning rate | Tail / root updates | Status |
| --- | --- | --- | --- |
| 1 | `3e-3` | 160 / 320 (frozen) | run 2026-09-02, branch `R1-C` |
| 2 | `3e-4` | 1,600 / 3,200 | run 2026-09-02, branch `R1-C` |
| 3 | `3e-3` | 1,600 / 3,200 | declared, not run |

Rung 1 is registered as a distinct configuration in code
(`ScoutConfig.ladder_rung_1()`, mode `LADDER1`, run id `ucope-scout-r01-exposure-ladder-rung-1`).
Rungs 2 and 3 are declared here so that running them later is a declared rung and not a fresh
budget argument; each will need its own launch, admission and result document.

### 4.4 The two mechanisms and what distinguishes them

Both are candidate explanations of the B1 observation "0/18 policies competent at any of 72
checkpoints; closest regret `0.0214` against a `0.02` gate; max tail agreement `0.829` against a
`0.95` gate".

- **Mechanism A — finite optimizer exposure.** The direction lists this first among its own
  alternatives and has never tested it. The review's source audit of
  `competence_first_scout_r01/{model,training}.py` states it concretely: the Bellman coefficients are
  Glorot-uniform on a `1 x 5` (tail) or `1 x 7` (root) matrix, so of order 1; AdamW at lr `3e-4` with
  gradient-norm clipping moves each coordinate by about the learning rate per step, so 160 tail /
  320 root updates displace a coefficient by roughly `0.05` (tail) to `0.1` (root), against an
  initial distance from the least-squares solution of order `0.5`–`1` and a target resolution of
  `0.01`–`0.04` between adjacent `k`. Under A the learner simply cannot reach the region where
  `C_even` can be satisfied, whatever else is true.
- **Mechanism B — everything invariant to exposure.** The host margin (the sole positive-probe
  context has net acquisition value `+0.051`, adjacent-`k` value gaps of order `0.01`–`0.04`), the
  objective and target package, the span of the twelve-coefficient basis, the conditioning of the
  Bellman design matrix, fold coupling, and seed instability. Under B, more exposure does not help.

**What distinguishes them.** Rung 1 multiplies the per-step displacement budget by ten while holding
the host, data, folds, seeds, batch law, target schedule, checkpoint cadence, arms and competence
criterion exactly fixed. It therefore produces a within-arm comparison against B1 for the two arms
B1 also ran, in which optimizer exposure is the only quantity that differs. A change in competence
is attributable to exposure; an absence of change **at a verified ten-fold displacement** removes
exposure as a sufficient explanation and leaves mechanism B. The exposure line is what makes the
second half of that sentence checkable rather than assumed, which is why the displacement magnitude
is part of the reading rule below and not an afterthought.

### 4.5 Reading rule for rung 1 — written before the data

Applied verbatim after the run, using only the quantities named here.

Definitions, all from the frozen object:

- `C_even(P)` is unchanged: `all_scores_finite AND all_choices_unique AND
  exact_eight_context_oracle_root_vector AND maximum_expected_regret <= 1/50 AND
  minimum_forced_PROBE_tail_agreement >= 19/20`, evaluated on even held-out support
  `K_eval = {2,4,6,8}` at root update 320 only.
- A seed passes an arm when both of its final fold policies pass `C_even`. An arm is `B_COMPETENT`
  when at least 2 of its 3 seeds pass.
- `m` is the **minimum**, over all 12 policies and both stages, of the largest absolute
  per-coordinate change of the Bellman coefficient vector from its exact initialisation, taken at
  the final checkpoint (root update 320, tail update 160).

Branches, evaluated in order; exactly one applies:

- **R1-A — `EXPOSURE_EXPLAINS_INCOMPETENCE`.** At least one arm is `B_COMPETENT`.
  Reading: on this host, the B1 incompetence at lr `3e-4` is at least partly an artefact of finite
  optimizer exposure, and mechanism B is not the whole story. The conditioning question the
  whitening discriminator asks stops being the direction's binding constraint. Next: a separately
  named object may read acquisition on the competent policies; rungs 2 and 3 become calibration
  rather than discrimination.
- **R1-B — `EXPOSURE_MOVED_BUT_NO_COMPETENCE`.** No arm is `B_COMPETENT` **and** `m >= 0.30`.
  Reading: an order-of-magnitude larger displacement budget, actually realised, does not produce
  competence on this host at this criterion. Mechanism A is not a sufficient explanation. The
  surviving suspects are the host margin, the objective/target package, the basis span, conditioning,
  fold coupling and seed instability. Next: the margin-scaled competence falsifier held in reserve
  by the review (same host, one arm plus the immediate-commit null, the probe's information value
  scaled so the target-context net acquisition margin is about `0.25` instead of `0.05`, relative
  competence criterion) becomes the direction's next named object.
- **R1-C — `EXPOSURE_DID_NOT_MOVE`.** No arm is `B_COMPETENT` **and** `m < 0.30`.
  Reading: rung 1 did not deliver the intended exposure increase, so it says nothing about
  mechanism A. It is uninformative for the ladder's question. Next: rung 2 (lr `3e-4` at 1,600/3,200
  updates) must run before any exposure conclusion is drawn.

Why `0.30`: at lr `3e-3` with gradient-norm clipping, 320 Adam steps have a theoretical
per-coordinate ceiling of `320 x 3e-3 = 0.96`; the review's arithmetic for lr `3e-4` gives about
`0.05`–`0.1` over the same schedule. `0.30` sits at roughly a third of the rung-1 ceiling and three
to six times the lr-`3e-4` figure, so it separates "the ten-fold increase was realised" from "it was
not" without requiring the ceiling to be reached. The threshold is fixed here, before the run.

Descriptive and claim-free, reported but deciding nothing: per-arm/seed/fold/checkpoint regret, tail
agreement, PROBE rate, root-vector Hamming distance, sampled external return, the `FT-XF-FLEX` versus
`FT-XF-BC` dominance count at each checkpoint, and the odd-support (`K_train`) diagnostics. At three
seeds no arm-comparison polarity, stable superiority or seed-population claim is available.

### 4.6 Claim ceiling and non-goals

Ceiling: "On this exact finite eight-context host, with these two learner packages, three seeds, two
folds and this competence criterion, a ten-fold larger optimizer-exposure budget did / did not
produce even-support competence." Cannot support: acquisition polarity, COUNT/RAW polarity, a
conditioning or representation attribution, stable superiority, a seed-population claim, generic
UCOPE, variable-`k`, variable-`N`, MARL/UAV, transfer, safety, deployment, flight, energy or
real-world QoS.

## 5. The whitening discriminator, alongside

`DIRECTION.md:130-131` says, verbatim:

> The unchanged B1 configuration is retired as a low-value repeat. The direction
> continues only through the read-only A/RECON object

and `DIRECTION.md:194` records `NEXT_DISCRIMINATOR_COUNT=1`. Read together with the 2026-09-01
conditioning selection, that phrasing made the whitening discriminator the *sole* continuation.
Under decision 2 this is corrected to **alongside**: the discriminator runs, and the exposure ladder
runs first and independently of it. The correction is recorded in DIRECTION.md's status area and
here; the historical sentences are not rewritten.

The discriminator's frozen object is unchanged in every scientific respect: arms `FT-XF-BC-RAW` and
`FT-XF-BC-WHITENED`, three fresh seeds `ucope-bc-conditioning-r01-fresh-{00,01,02}`, two folds,
`160`/`320` updates at lr `3e-4`, batch 256, the target-blind deterministic positive-diagonal
Cholesky transform `G = XᵀX/n = LLᵀ`, `z_w = L⁻¹z`, function-space-matched initialisation
`β̃₀ = Lᵀβ₀`, and the same `C_even` criterion. Its reading rule is its own contract's, restated
here unchanged before the data:

> A positive requires whitened even-support `B_COMPETENT`, raw noncompetence, and a clear paired
> whitened advantage at both updates 160 and 320. The exact falsifier is whitened noncompetence plus
> no clear paired advantage at both checkpoints. A negative rejects only this intervention's
> sufficiency at the fixed exposure.

Three boundaries the review attaches to it, recorded here because they bound what its result can
mean: its ceiling is the least-squares fit of the same twelve-coefficient basis, which the
structural certificate already showed passes regret in 20/20 policies but tail agreement in only
17/20; whitening changes the metric of Adam's steps, not their number or size, so a raw-versus-
whitened null is the expected outcome under the exposure-shortfall reading; and by the direction's
own sequencing a BC-only competence pass cannot open COUNT/RAW or acquisition. **A both-arms-
noncompetent outcome is not PARK support on its own** and is not to be read as such before the
exposure ladder has run.

## 6. Relation to `flexible_skill_duration`

`docs/research/candidates/flexible_skill_duration/DIRECTION.md`, "Relations to other directions"
(line 48), states:

> `ucope`: independent; its paid-probe period is a candidate D2 special case, and its odd/even
> duration split is a candidate C-time transfer test for this direction (plan §11 G).

So the paid-probe period UCOPE holds fixed is a candidate special case of that direction's D2
scheme, and UCOPE's odd training / even held-out duration split is a candidate C-time transfer test
*there*. Neither relation gates, blocks or redirects UCOPE: both objects registered here continue
independently under their own contracts. Per §11.5 the untied-`k` and untied-`N` programmes remain
separate directions, and this intake opens no joint object. Per the 2026-09-02 addendum, UCOPE's own
odd/even split remains "the later C-time obligation" and is not a launch condition for either
B object here.

## 7. What this intake does not do

It records no competence, conditioning, exposure or acquisition observation; changes no seed, fold,
host, oracle, criterion, update count, batch law, checkpoint cadence, comparator or claim ceiling;
opens neither the acquisition evaluation nor COUNT/RAW; and consumes no scientific object. It
establishes no algorithm performance, stability, promotion, retirement, lifecycle, transfer, safety
or general-MARL claim. The consumed objects
`UCOPE-CPA-SAME-DATA-BELLMAN-STRUCTURAL-COMPETENCE-R01` and
`UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01` stay consumed and are neither reused, rescued
nor reinterpreted, and no B1 or audit runtime row is read by either object registered here.

One consequence of the code change is recorded for honesty: `ScoutConfig` gained an explicit
`learning_rate` field so the ladder's declared axis is part of the frozen configuration rather than
a hidden literal. Its B1 and ASSESS value is unchanged at `3e-4`, and `ScoutConfig.from_dict`
accepts pre-recast payloads that lack the field, so every artifact written before today still loads
and still validates as the same configuration.

## 8. Result

Both objects were launched on 2026-09-02 at commit `ce361d40ac7db9cc8ba7714fee278bb62dbf8793`, the
ladder first and the discriminator alongside it, one at a time, each with its own fresh `4 GiB`
physical and effective admission immediately before launch (10.74 GiB and 10.91 GiB available). One
completed and one did not.

**Exposure ladder rung 1 — complete, valid, `R1-C EXPOSURE_DID_NOT_MOVE`.** 89.3 s wall, 12 policies,
122,880 episodes, 3,840 root and 1,920 tail optimizer updates, 48 checkpoints, every activity counter
reconciled exactly, no non-finite event, telemetry fully measured (`resources_unmeasured: false`,
peak RSS 411.5 MiB). The competence observation, recorded and deciding nothing: 0 of 12 policies
competent, 0 of 12 matching the exact oracle root vector, branch `NO_ARM_COMPETENT`, both arms
`false`. The reading rule of section 4.5 applied verbatim: no arm `B_COMPETENT`, and
`m = 0.046434 < 0.30`, so branch **R1-C**, whose registered reading is that rung 1 did not deliver the
intended exposure increase and is uninformative about mechanism A; rung 2 must run before any exposure
conclusion. The branch is unchanged if `FT-XF-BC` is taken alone, where the Bellman vector is the
whole model and the minimum move is `0.250245`. Closest approaches at update 320: regret `0.0285629`
against the `0.02` gate, tail agreement `1.000000` against the `0.95` gate — but no policy matched the
oracle root vector. Full evidence: `UCOPE_EXPOSURE_LADDER_R1_RESULT_EVIDENCE_20260902.md`.

**Whitening discriminator R01 — quarantined incomplete attempt, no polarity, object not consumed.**
The recast let this object attempt a launch for the first time: both refusals were exercised as
recorded fields (`assessment-02` recorded as `PERFORMANCE_READY` on disk and `INVALID_NOT_ADOPTED` by
contract:561, `gating: false`; source clean and recorded). It then failed 22 s in, inside its own
frozen numerical core, at
`experiments/candidates/ucope/conditioning_discriminator_r01/conditioning.py:106` with
`ConditioningTransformError: recorded Gram/Cholesky relation is invalid`, during
`prepare_fold_data` and before any model, optimizer, target, checkpoint or evaluation existed. It was
quarantined under §6.2 and not rerun with changes. An outcome-free post-hoc diagnostic shows the
failure is deterministic and universal at science scale: all twelve seed/fold/stage designs give
`max|LLᵀ − G|` of `9.12e-06` to `9.69e-06` against the frozen `16·eps_fp32` ceiling of `3.81e-06`,
about 2.4 to 2.5 times over, at Gram condition numbers `7.2e2` (tail) and `5.0e3` (root). The object
produced no competence observation, its reading rule is not applicable, and **its falsifier is not
satisfied** — a falsifier needs an observed noncompetence and nothing was observed. Full record:
`UCOPE_BC_CONDITIONING_DISCRIMINATOR_R01_RESULT_EVIDENCE_20260902.md`.

Consequence for the direction, recorded without deciding it: as frozen, the whitening discriminator
appears not to be executable at science scale on this platform, and the FP32 tolerance that stops it
was calibrated at the 40-episode technical scale the two assessments used. Whether that becomes a
`REPAIR_REQUIRED` disposition, a fresh object with an outcome-blind scale-appropriate tolerance, or a
different conditioning intervention is an owner decision. Nothing here supports `PARK`.

**Exposure ladder rung 2 — complete, valid, `R1-C EXPOSURE_DID_NOT_MOVE`.** Rung 1 was accepted in
Part D of the compliance note, and its reading rule named rung 2 as the required next step; the owner
directed it to run. Launched 2026-09-02 with HEAD `ba8d165fc193cfb0582b15f96fc68c4a9dd3afa6` and a
**dirty, recorded** working tree — the first launch to exercise the clean-source demotion in its
intended direction. Admission 12.77 GiB physical and effective. 359.3 s wall, 12 policies, 38,400 root
and 19,200 tail optimizer updates (ten times rung 1), 60 checkpoints at roots
`{40, 80, 160, 320, 3200}`, every activity counter reconciled, no non-finite event, telemetry fully
measured (`resources_unmeasured: false`, peak RSS 411.1 MiB). Competence observation, recorded and
deciding nothing: 0 of 12 policies competent, 0 of 12 oracle root-vector matches, branch
`NO_ARM_COMPETENT`, both arms `false`. Reading rule of section 4.5 applied verbatim: no arm
`B_COMPETENT` and `m = 0.025254 < 0.30`, so branch **R1-C** again; unchanged on `FT-XF-BC` alone,
whose minimum move is `0.249392`. At update 3,200 the closest regret is `0.030221` against the `0.02`
gate and the maximum tail agreement `0.788446` against the `0.95` gate. Ten times the update budget
moved the Bellman coefficients no further than rung 1 did. Full evidence:
`UCOPE_EXPOSURE_LADDER_R2_RESULT_EVIDENCE_20260902.md`.

Two of the three registered rungs have now returned `R1-C` for the same structural reason: `m` is a
minimum over 24 stage-policies and a single low-displacement `FT-XF-FLEX` tail policy fixes it below
`0.30` while most policies move far more. Whether to run rung 3, to recast the exposure statistic, or
to move to the margin-scaled falsifier held in reserve is an owner decision; neither the threshold nor
the statistic is changed here, because moving a prospective rule after seeing two outcomes would be an
outcome-informed rewrite.

**Exposure ladder R02 rung 1 — complete, valid, `R2-D NEITHER_ARM_MOVED`.** Registered in section
9 below and launched 2026-09-02 at commit `9ef1b36b68b27160975df202a00bda08f1214c28` with the bound
14-file source inventory clean at that HEAD; admission 10.19 GiB physical and effective; 108.7 s
wall, 198.3 s CPU at four intra-op threads, 12 policies, 122,880 episodes, 3,840 root and 1,920 tail
optimizer updates, 48 checkpoints, every activity counter reconciled, no non-finite event, telemetry
fully measured (`resources_unmeasured: false`, peak RSS 412.97 MiB). Because R02 reuses R01's
workload and the counter-addressed RNG never keys on the object label, the 48 evaluation rows are
**byte-identical** to R01 rung 1's, and every exposure field R01 recorded is identical too; both were
checked row by row rather than assumed. Competence observation, recorded and deciding nothing: 0 of
12 policies competent, 0 of 12 oracle root-vector matches, branch `NO_ARM_COMPETENT`, both arms
`false`. The per-arm rule of section 9.4 applied verbatim: no arm `B_COMPETENT`;
`m_FT-XF-FLEX = 0.108116 < 0.30` (all-coordinate minimum, residual included, at seed `…fresh-02`
fold 1 tail) and `m_FT-XF-BC = 0.250245 < 0.30`, so both arms `NOT_MOVED` and the branch is
**R2-D**, which is registered as uninformative for the ladder's question. Counting FLEX's residual
raises that arm's minimum by a factor of 2.33 over R01's beta-only `0.046434`, so R01's statistic did
understate FLEX's movement — but not enough to change the branch, and R01 rung 1's published `R1-C`
is not disturbed. Rung 2 of R02 is registered and **not run**. Full evidence:
`UCOPE_EXPOSURE_LADDER_R02_R1_RESULT_EVIDENCE_20260902.md`.

**Exposure ladder R02 rung 2 — complete, valid, `R2-D NEITHER_ARM_MOVED`; the ladder closes.** Run
2026-09-02 on the owner instruction to close the ladder (compliance note D.8), at commit
`905ca924661024d734d29cac773b59323626862b` with the bound 14-file source inventory clean; admission
10.70 GiB physical and effective; 631.1 s wall, 1,515.8 s CPU at four intra-op threads, 12 policies,
38,400 root and 19,200 tail optimizer updates, 60 checkpoints at roots `{40, 80, 160, 320, 3200}`,
every counter reconciled, no non-finite event, telemetry fully measured (`resources_unmeasured:
false`, peak RSS 412.50 MiB). The 60 evaluation rows are byte-identical to R01 rung 2's and every
exposure field R01 recorded is identical too, both checked row by row. Competence observation,
recorded and deciding nothing: 0 of 12 competent, 0 of 12 oracle root-vector matches,
`NO_ARM_COMPETENT`. Per-arm rule of section 9.4 applied verbatim: `m_FT-XF-FLEX = 0.107457 < 0.30`
(all-coordinate minimum, residual included, seed `…fresh-02` fold 1 tail) and
`m_FT-XF-BC = 0.249392 < 0.30`, so both arms `NOT_MOVED` and the branch is **R2-D**. Across the two
rungs — a ten-fold change in learning rate traded against a ten-fold change in update count, so that
`steps x lr` is `0.96` at both — the per-arm displacement floors are essentially unchanged
(`FT-XF-FLEX` 0.108116 to 0.107457, −0.61 %; `FT-XF-BC` 0.250245 to 0.249392, −0.34 %), set by the
same policy and stage at both rungs. Ten times the optimizer budget at one tenth the step size moved
the least-moving coordinate of each arm by less than one percent. Rung 3 was not run. Full evidence:
`UCOPE_EXPOSURE_LADDER_R02_R2_RESULT_EVIDENCE_20260902.md`.

Consequence for the direction, recorded without deciding it: with both rungs read per arm and the
instrumentation verified, the ladder has said what it can say and the open question has moved. It is
no longer "was the exposure budget realised" but "why does the learned Bellman coefficient vector
settle far from the optimum its own basis can represent exactly, and why does an order-of-magnitude
change of schedule not move it". That question is carded as
`UCOPE-A-TRAINING-TARGET-DIAGNOSTIC-R01` in
`UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_CARD_20260902.md`, written but **not run**: it awaits the
owner's prediction among the candidate mechanisms listed at the end of that card.

**Instrumentation check — passed, no defect.**
`UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01` (card and result dated 2026-09-02, 77
tests, all passing) established that the tail-agreement, regret, oracle-root-vector, competence and
displacement measurements are correct on both arms; that the competence predicate returns `True` for
an exactly-optimal policy on both arms; and that both recorded anomalies are properties of the
trained policies and of the frozen FT clock rather than of the instrument. No R01 record or document
was altered. Card: `UCOPE_INSTRUMENTATION_CHECK_R01_CARD_20260902.md`; result:
`UCOPE_INSTRUMENTATION_CHECK_R01_RESULT_20260902.md`.

## 9. `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R02` — registered 2026-09-02

### 9.1 Why a second ladder object rather than an edit to R01

Two of R01's three registered rungs returned `R1-C` for the same structural reason: `m` is a single
minimum taken over all 24 stage-policies of both arms, so one low-displacement `FT-XF-FLEX` tail
policy fixes the branch for the whole rung while most policies move far more. Changing R01's rule
after seeing two of its outcomes would be an outcome-informed rewrite of a prospective rule. Under
the spec's own wording an outcome-informed redesign is *a different scientific object*, so it is
registered here as one. R01's rungs 1 and 2, their records, their `R1-C` branches and their reading
stand exactly as published and are not reinterpreted.

The instrumentation check `UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01` (card and
result dated 2026-09-02) passed on every measurement, so the numbers R01 recorded are correct
measurements and R02 inherits the same instrument with no repair. That check also established the
two facts this object acts on: `exposure_line` reads the whole `state_dict()` for the aggregate
displacement — for `FT-XF-FLEX` that is `beta` plus 4,865 residual coordinates — and reads only
`state_dict()["beta"]` for the per-coordinate move that R01's `m` is built from.

### 9.2 What R02 keeps, byte for byte

Arms `FT-XF-FLEX` and `FT-XF-BC`; seeds `ucope-scout-r01-b1-fresh-{00,01,02}`; two group-disjoint
folds; 5,120 episodes per context; batch 256; the frozen host, oracle, competence predicate
`C_even` and checkpoint cadence; and the same two coded rungs — rung 1 at `lr 3e-3` with 160/320
tail/root updates, rung 2 at `lr 3e-4` with 1,600/3,200. The counter-addressed RNG is keyed on
`(namespace, seed, fold, index)` and never on the object label, so R02 rung 1 reproduces R01 rung 1's
training exactly. Nothing about the execution changes; the runner records which object the rung was
run for, and nothing else differs.

The competence observation is recorded **per arm** exactly as in R01: a seed passes an arm when both
of its final fold policies pass `C_even`, an arm is `B_COMPETENT` when at least 2 of its 3 seeds
pass, and the observation decides nothing on its own.

### 9.3 The displacement statistic, per arm, with the residual handled explicitly

For each arm `A` and each of that arm's 12 rows (6 policies x 2 stages), at the final checkpoint:

`move(row)` = the largest absolute per-coordinate change, from the exact deterministic
initialisation of the same arm/seed/fold, over **all trained coordinates of that arm**.

- For `FT-XF-BC` the trained coordinates *are* the Bellman vector (7 at root, 5 at tail), so `move`
  is identical to R01's `beta_max_abs_coordinate_move` for this arm. Nothing is added and nothing is
  dropped.
- For `FT-XF-FLEX` the trained coordinates are the Bellman vector **together with** the paired
  residual (`residual.{0,2,4}.{weight,bias}`, 4,865 tail coordinates). The residual is therefore
  **inside** this arm's statistic. R01's `m` excluded it, which is why a FLEX policy that moved its
  residual freely could still register as not having moved.

`m_A` is the minimum of `move(row)` over that arm's 12 rows. Both `m_A` and the beta-only minimum
`b_A` are recorded for both arms; only `m_A` decides. The runner emits them in
`exposure_line.per_arm`, and the R01 fields (`minimum_beta_max_abs_coordinate_move` and the rest)
are untouched, so R01's published records keep their meaning.

### 9.4 Reading rule — written before any R02 run

Applied verbatim after each rung, using only the quantities named here.

- Arm `A` is `MOVED` when `m_A >= t_A`, and `NOT_MOVED` otherwise.
- `t_FT-XF-FLEX = 0.30` and `t_FT-XF-BC = 0.30`.

Branches, evaluated in order; exactly one applies:

- **R2-A — `EXPOSURE_EXPLAINS_INCOMPETENCE`.** At least one arm is `B_COMPETENT`. Reading and next
  steps as R01's `R1-A`.
- **R2-B — `BOTH_ARMS_MOVED_NO_COMPETENCE`.** No arm `B_COMPETENT` and **both** arms `MOVED`.
  Reading: on this host, at this rung, a realised displacement budget of this size does not produce
  even-support competence in either learner package. Mechanism A is not a sufficient explanation for
  either arm. Next: the margin-scaled competence falsifier held in reserve by the review becomes the
  direction's next named object.
- **R2-C — `ONE_ARM_MOVED_NO_COMPETENCE`.** No arm `B_COMPETENT` and **exactly one** arm `MOVED`.
  Reading: the rung is informative for the moved arm only, and for that arm it reads as `R2-B` does.
  For the unmoved arm the rung says nothing about mechanism A. Next: the rung is repeated for the
  unmoved arm only if a later object is registered to do so; the moved arm's reading stands.
- **R2-D — `NEITHER_ARM_MOVED`.** No arm `B_COMPETENT` and neither arm `MOVED`. Reading: the rung
  did not deliver the intended exposure increase for either arm and is uninformative for the
  ladder's question, as R01's `R1-C` was.

### 9.5 How the thresholds were chosen, and why they coincide

Both thresholds come from the same arithmetic that fixed R01's `0.30`, and that arithmetic depends
only on the optimizer, the learning rate and the number of steps — which the two arms share. AdamW's
per-step per-coordinate displacement is bounded by approximately the learning rate for every
coordinate, whichever tensor it sits in, so the per-coordinate ceiling over a rung is `steps x lr`:
`320 x 3e-3 = 0.96` at the root stage of rung 1 and `3,200 x 3e-4 = 0.96` at the root stage of rung
2 (tail stages `0.48` at both rungs). `0.30` is about a third of that ceiling and three to six times
the `lr 3e-4` figure the review's arithmetic gives over the frozen schedule, so it separates "the
intended increase was realised" from "it was not" without requiring the ceiling to be reached.

The two numbers therefore coincide at `0.30`. They are still *per-arm* thresholds, applied separately
to per-arm statistics: the point of the rule is that neither arm's number can decide the other arm's
branch, not that the numbers must differ. Both are fixed here, before any R02 run.

### 9.6 What is already known before the run, stated openly

`FT-XF-BC` has no residual, so `m_FT-XF-BC` is numerically identical to R01's per-arm beta minimum
for that arm, and that number is already published: `0.250245` at rung 1 and `0.249392` at rung 2.
Both are below `0.30`, so `FT-XF-BC` is known in advance to be `NOT_MOVED` at both rungs, and branch
`R2-B` is therefore unreachable at rung 1 and rung 2. This is recorded here rather than discovered
later; the rule is not adjusted to make `R2-B` reachable, because that would be exactly the
outcome-informed edit section 9.1 refuses.

`m_FT-XF-FLEX` under this definition has not been computed for any rung: `exposure_line` did not
record an all-coordinate move before today, so the FLEX statistic is genuinely unseen at the moment
this rule is fixed. R01's beta-only FLEX minima (`0.046434`, `0.025254`) are not that statistic.

### 9.7 Claim ceiling

Unchanged from section 4.6, with the statistic read per arm: "On this exact finite eight-context
host, with these two learner packages, three seeds, two folds and this competence criterion, a
displacement budget of this size was / was not realised **by this arm**, and did / did not produce
even-support competence **for this arm**." R02 supports no acquisition polarity, no COUNT/RAW
polarity, no conditioning or representation attribution, no stable superiority, no seed-population
claim, and nothing about generic UCOPE, variable-`k`, variable-`N`, MARL/UAV, transfer, safety,
deployment, flight, energy or real-world QoS. At three seeds no arm-comparison polarity is available,
so `R2-C` must not be read as one arm outperforming the other.

### 9.8 Result

Both registered rungs were run on 2026-09-02 and both returned `R2-D NEITHER_ARM_MOVED`. Rung 1:
`UCOPE_EXPOSURE_LADDER_R02_R1_RESULT_EVIDENCE_20260902.md`, `m_FT-XF-FLEX = 0.108116`,
`m_FT-XF-BC = 0.250245`. Rung 2, run on the owner instruction to close the ladder:
`UCOPE_EXPOSURE_LADDER_R02_R2_RESULT_EVIDENCE_20260902.md`, `m_FT-XF-FLEX = 0.107457`,
`m_FT-XF-BC = 0.249392`. Both outcomes are summarised in section 8 above. Rung 3 was not run and
is not registered for R02.
