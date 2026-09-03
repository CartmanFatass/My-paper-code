# First-wave directions against evidence spec §11 — compliance note (2026-09-02)

Written by Claude Code (Fable 5.1) at the owner's request ("原来5个方向是否符合我们当前变更spec后的
要求 之前由于要求太严格 似乎一直在追逐不切实际的数学严谨性"). Part A is the reviewer's reading and
the decisions it puts to the owner. Part B is the audit, stored verbatim; it was produced by a
read-only Opus session over the working tree (committed and uncommitted files) with the instruction
to quote every "must hold before the next run" condition with `file:line`, class it against
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.4/§11.6 (ALLOWED / DEMOTED / UNCLEAR),
and name the cheapest next B run per direction. No file was changed by the audit.

Reviewer verification of the audit's code-gate claims (grep over the working tree, 2026-09-02):
`launch_capable: False` at `production_runner.py:92,208` (FRRIE); `FORMAL_ANALYSIS_BOUND = False`
and `READINESS_DISPOSITION = "REPAIR_REQUIRED"` at `omrc_b01/b1_metrics_artifact.py:41-42`
(CBSC); `ResultExecutionDisabled("RUN-01 performance readiness receipt is required")` at
`multifoundation_reachable_order_value/runner.py:607` (SCDMP); the clean-source and
`PERFORMANCE_READY` refusals at `scripts/run_ucope_bc_conditioning_discriminator_r01.py:82,127`
(UCOPE). All four are as the audit states. The VNFC block is documentary (DIRECTION.md:181-182),
and A0 has no implementation to grep.

## Part A — reviewer reading

### A.1 Summary

| Direction | Live object | Demoted conditions still binding | Calibration acknowledged | Cheapest §11-conforming B run | Blocked by a gate §11.4 does not permit |
| --- | --- | ---: | --- | --- | --- |
| FRRIE | B01 matched curves (B/EXPLORE, no result) | 8 | no | 1 seed × 128 updates PHY/EDGE smoke, then 3 seeds | yes, in code (`launch_capable=False`, panel validators) |
| VNFC | A0 finite-action law (A/RECON) gating R02 (B/EXPLORE) | 9 | no; moved further away today | R02 DEBUG (8 updates) + 3 × 64 updates | yes, in DIRECTION.md (A0 must pass; A0 unimplemented) |
| CBSC | OMRC B01 → B1 three-seed scout (B/EXPLORE; B0 done) | 5 | no | the frozen B1 as is, descriptive curves published directly | yes, in code (`FORMAL_ANALYSIS_BOUND`, readiness, two raises) |
| SCDMP | B01 RUN-01-REPLACEMENT-01 (B/EXPLORE) | 2 + 3 unclear | no | RUN-01-REPLACEMENT-01 exactly as frozen (~350 s projected) | yes, in code (`PERFORMANCE_READY` receipt; only assessment says `REVIEW_REQUIRED`) |
| UCOPE | BC invertible-conditioning discriminator R01 (B/EXPLORE) | 9 | no | exposure ladder on the existing B1 code (~140 s) | yes, twice (budget-enlargement ban; runner refusals) |

Three facts hold across all five:

1. None acknowledges §11. The nine direction documents modified today were written after the
   calibration and do not cite it; §11.6's "record the demotion in the next intake" has not
   happened anywhere.
2. Every direction is held by at least one gate that §11.4 does not allow to hold a B launch, and
   in four of five the operative gate is a code constant or a raise, not a sentence. Editing the
   documents does not unblock anything; each recast needs one small code change that turns the
   gate into a recorded field.
3. Net movement since the 2026-09-01 review is away from §11 in VNFC, UCOPE and SCDMP, split in
   CBSC (exposure telemetry added in `ppo.py`; consumer-recompute boundary entrenched in docs), and
   toward in FRRIE's engineering only.

### A.2 What "recast per §11" means for each, concretely

The recast is the same shape everywhere: keep the frozen scientific object, the §4 integrity items,
the nonzero counts, the resource admission and one exposure line as launch conditions; move
everything else from gate to recorded field; run the cheapest B object; write the result in the E0
format with the demotion recorded in the intake. Per direction:

- **FRRIE.** `launch_capable` and `performance_disposition` become recorded fields; the 98-cell /
  ordered-28 / whole-chain-telemetry panel validators stop raising on the result path and become an
  optional analysis. Run the 1-seed 128-update smoke on the working-tree `b01/` trainer, then the
  three-seed B01. The two theorems (no-contact equality, universal certificate) stay as text, not
  as re-entry conditions. Uncertain: whether the Slice-B trainer in the working tree is complete
  enough to run 128 updates; the audit did not check this.
- **VNFC.** The 304-row A0 law is demoted from conformance condition to optional analysis; a
  ~50-row unit-test-scale presentation check replaces it as an integrity item. R02 DEBUG and three
  64-update seeds run on the R01 runner with the canonical opaque-rank sort. The byte manifests
  (942 sources, 82 modules, DLL build key) are recorded if produced, never required. This is the
  largest reversal: today's edits deepened the binding.
- **CBSC.** `FORMAL_ANALYSIS_BOUND`, `READINESS_DISPOSITION` and the two publication raises become
  recorded fields; the frozen three-seed B1 runs and its descriptive curves (per-checkpoint returns,
  serve rate, actions, competence flags) are published directly rather than as literal nulls for a
  consumer to recompute. B1b (4× updates) is declared now as a named exposure ladder rung.
- **SCDMP.** The `PERFORMANCE_READY` receipt becomes a recorded assessment; telemetry is recorded,
  not gating ("missing measurement invalidates" is the §11.4 undecided clause, resolved here as
  downgrade unless the owner says annul). RUN-01-REPLACEMENT-01 runs exactly as frozen. The intake
  also records the §11.3 point that the `k ∈ {7, 13}` menu is a legitimate suboptimal scheme with
  `τ(1−γ)/(1−γ^τ)` as its target-scale error, and the recast toward D6 noted in
  `flexible_skill_duration` (plan §11 F).
- **UCOPE.** The exposure ladder (existing B1 code, FT-XF-FLEX vs FT-XF-BC, 3 seeds × 2 folds, lr
  3e-3, 160/320 updates) is registered as a named B object, so the "no budget enlargement" sentence
  does not read on it; the whitening discriminator runs alongside, not instead; the exact-oracle
  competence predicate becomes a recorded observation. The runner's clean-source and assessment-03
  refusals become recorded fields (the existing assessment-02 is recorded as what it is).

### A.3 Cost and order

Each recast is one Opus session: a one-page recast note in the direction directory (the §11.6
"demotion recorded in the next intake"), the gate-to-field code change with its test, the run, and
the result document. Estimated wall time per direction, runs included: SCDMP and UCOPE under one
hour each; CBSC two to three hours (B1 is 4 arms × 3 seeds × 48 updates); FRRIE and VNFC unknown
until the runner state is checked. Under the confirmed budget policy (8 h cap per study, two runs
concurrent) these fit around E1 without delaying it if SCDMP and UCOPE go first.

The decisions put to the owner are in A.4; the audit follows.

### A.4 Decisions (owner, 2026-09-02, one question each)

| # | Question | Decision |
| --- | --- | --- |
| 1 | SCDMP | Recast per §11 and run now: the `PERFORMANCE_READY` receipt becomes a recorded field; telemetry is recorded, not gating; RUN-01-REPLACEMENT-01 runs exactly as frozen; the intake records the §11 demotion and the §11.3 reading of the `k ∈ {7, 13}` menu |
| 2 | UCOPE | Recast per §11: the exposure ladder is registered as a named B object and runs first; the whitening discriminator runs alongside, not instead; the exact-oracle competence predicate becomes a recorded observation; the runner's clean-source and assessment-03 refusals become recorded fields |
| 3 | CBSC | Recast per §11 and run the frozen B1: `FORMAL_ANALYSIS_BOUND`, `READINESS_DISPOSITION` and the two publication raises become recorded fields; descriptive curves are published directly; B1b (4× updates) is declared now as the next ladder rung |
| 4 | VNFC | Recast per §11: the 304-row A0 law is demoted to optional analysis and replaced as an integrity item by a ~50-row unit-test-scale presentation check; R02 DEBUG (8 updates) and three 64-update seeds run on the R01 runner; byte manifests are recorded if produced, never required |
| 5 | FRRIE | Recast per §11: `launch_capable` / `performance_disposition` become recorded fields and the panel validators optional analysis; the implementer first checks whether the Slice-B trainer runs 128 updates and reports back if not (no completion of the full chain); then the 1-seed smoke, then three seeds |
| 6 | Order | SCDMP → UCOPE → CBSC → VNFC → FRRIE, one Opus session each, sharing the two-concurrent budget with E1 (E1 still launches on its own trigger after P3) |
| 7 | Telemetry missing (spec §11.4 undecided clause; workflow review R4) | Downgrade, not annul: a run whose resource telemetry (peak RSS, scratch, wall) is missing stays valid and is marked "resources unmeasured"; annulment only when the claim itself is a resource claim. Learner-side instrumentation failure (missing logs or checkpoints) still quarantines under §6.2 |

Decision 7 closes the item left open in `CODEX_SCIENCE_WORKFLOW_REVIEW_20260901.md` (R4) and
in spec §11.4's last sentence; the formal record is
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`.

Execution: each recast is one Opus session in the main tree (the directions' uncommitted
working-tree changes must be included, so a worktree at HEAD is not usable), touching only its
direction's paths, staging by explicit path, and pushing `main`. The reviewer intakes each result
as a new part of this file.

## Part B — audit (verbatim)

# Section-11 calibration audit — five first-wave directions

Working-tree state as of 2026-09-02. Modification status verified with `git diff --stat`:

| Direction | Direction-dir files modified vs HEAD |
| --- | --- |
| FRRIE | none (docs clean; only `experiments/.../b01/{trainer,checkpoint}.py` changed) |
| VNFC | `DIRECTION.md`, `VNFC_BPCR_R02_A0_EM_FREEZE_INTAKE_20260901.md`, `VNFC_BPCR_R02_FINITE_PHYSICAL_ACTION_LAW_A0_FREEZE_20260901.md` |
| CBSC | `DIRECTION.md`, `CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md`, `CBSC_OMRC_B01_INNOVATOR_INTAKE_20260901.md`, `CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md` (+ `omrc_b01/ppo.py`) |
| SCDMP | `DIRECTION.md`, `SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md` (+ ~12 impl files) |
| UCOPE | `DIRECTION.md` |

**Global finding on (d):** `grep -rn "§11|section 11|Section 11|2026-09-02|20260902|calibration"` over all five direction directories returns **zero** hits referring to the calibration. No direction's documents acknowledge §11 in any form, including the files modified today.

---

## 1. FRRIE — finite_resource_relational_inductive_efficiency

**(a) Live object.** `FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901`, a `B/EXPLORE` family (DIRECTION.md:259-261; intake status line `PRO_FINAL_SELECT_PROPOSED_B_FAMILY / B_EXPLORE / NO_RESULT`, FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md:3). Claim ceiling: "a preliminary finite-budget tight-versus-containing projection/optimizer-package signal or counterexample on the literal three- or five-seed panel" (DIRECTION.md:268-270). No B01 result activity has occurred.

| # | Condition (quoted) | file:line | Class | Clause |
|---|---|---|---|---|
| 1 | "Production remains `REPAIR_REQUIRED` under the single direction-level blocker `FULL_PANEL_RUNNER_AND_FULL_CHAIN_TELEMETRY_INCOMPLETE`." | DIRECTION.md:279-280 | DEMOTED | §11.4 (telemetry completeness beyond the run's own claim; capacity gate) |
| 2 | "there is no complete 512-update production orchestrator, no complete 98-cell-per-seed evaluation publication, and no atomic whole-panel artifact binding the ordered shadow, between-arm action-TV, parameter-distance, process-tree, and all 28 frozen quantities" | FRRIE_B01_CM_ENGINEERING_MILESTONE_20260901.md:11-14 | DEMOTED | §11.4; §11.6 (gates that cannot change a B decision) |
| 3 | "The current source is also dirty and uncommitted, so the formal source gate correctly refuses a result-bearing launch." | FRRIE_B01_CM_ENGINEERING_MILESTONE_20260901.md:14-15 | DEMOTED | §11.4 (byte manifests / capacity gates) |
| 4 | "Only after all preceding gates are CLEAN may a fresh 4 GiB admission precede the initial three result-bearing seeds." | FRRIE_B01_CM_ENGINEERING_MILESTONE_20260901.md:152-153 | DEMOTED | §11.4 (chains a §11.4-allowed admission behind five disallowed gates) |
| 5 | "`launch_capable=false` until every downstream validator below is complete and Root records a commit-bound source milestone." | FRRIE_B01_PRODUCTION_CHAIN_ENGINEERING_PLAN_20260901.md:71-72 | DEMOTED | §11.4 (capacity gate / prospective contract) |
| 6 | "Long initial-three-seed launch is forbidden unless the actual formal chain is `PERFORMANCE_READY` and the source remains commit-bound and scoped-clean." | FRRIE_B01_PRODUCTION_CHAIN_ENGINEERING_PLAN_20260901.md:181-183 | DEMOTED | §11.4 (capacity gate) |
| 7 | "Stop and keep `REPAIR_REQUIRED` if any of the following remains: … missing one of the 98 cells; non-streamable raw inventory; … unavailable exact ordered-28 validation; incomplete process-tree telemetry" | FRRIE_B01_PRODUCTION_CHAIN_ENGINEERING_PLAN_20260901.md:189-196 | DEMOTED | §11.4/§11.6 |
| 8 | "Immediately before every result-bearing launch, resume, repair, or slice, require fresh physical and effective available memory of at least 4 GiB." | FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md:169-170 | ALLOWED | §11.4 (mandatory resource admission) |
| 9 | "Any arm difference before first tight contact is structural invalidity." | FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md:198 | ALLOWED | §4.2/§4.5 integrity (defines the paired estimand) |
| 10 | "deterministic raw-only balanced accuracy must be exactly `1/2` … any other value is implementation/leakage invalidity" | FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md:202-203 | ALLOWED | §4.5 (leakage) |
| 11 | "A valid seed must reach update 512; only structural, resource, or technical failure can stop it early" | FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md:138-140 | ALLOWED | §5.2/§4.7 (bounds interpretation to observed budget) |
| 12 | "Before any B01 model, tape, or outcome is materialized, one B01 packet must contain five ordered, unique, fresh 32-byte roots" | FRRIE_B01_INNOVATOR_DECISION_INTAKE_20260901.md:101-102 | ALLOWED | §4.5 (RNG reporting); prevents result-informed seed selection |
| 13 | "V2 preflight must return `SIMULTANEOUS_MEAN_INFERENCE_UNRESOLVED_AT_24_BLOCKS`, `ready=false`, and perform no result activity." | IMPLEMENTATION_THRESHOLD.md:227-228 | DEMOTED | §11.1 (a C-time inference obligation applied as a launch condition); also stale — the threshold file still says `R01_CLOSED_NO_RESULT_IMPLEMENTATION` / `PARK` (IMPLEMENTATION_THRESHOLD.md:3,10) |
| 14 | "each selected origin now physically replays the retained post-GRU/pretransition factual suffix, directly compares the full path" (physical factual-label replay before `J_base` reuse) | DIRECTION.md:111-114; IMPLEMENTATION_THRESHOLD.md:191-197 | DEMOTED | §11.6 (exact-equality conformance condition inherited from R01/R02) |

**(d) Calibration acknowledged:** **no**. Nothing in the FRRIE directory mentions §11 or 2026-09-02; the DIRECTION.md is unmodified since HEAD. The demoted conditions are all still stated as binding.

**(e) Formal products still required as prerequisites:** the "exact no-projection-contact equality theorem … available only if non-contact is proved over every reachable supported training path" (DIRECTION.md:141-143) and the "universal certificate covering every root, all 512 updates, every claim-relevant evaluation transition, and equality through the complete native return" (DIRECTION.md:222-224). §11.2 demotes both explicitly ("exact equality theorem … not admission conditions"); the addendum names the first one directly. Neither is formally required *for B01* by the 2026-09-01 recast, but both remain live text as re-entry conditions for the direction.

**(f) Cheapest next B run:** a one-seed 128-update `PHY_TRUST`/`EDGE_FLEX` smoke on the existing `b01/` trainer+collector with INTACT evaluation at `N={9,15}` only, publishing curves, contact update, competence, wall/RSS, and the cumulative-projection-displacement exposure line. **Blocked by a disallowed gate: yes.** The block is in code, not only in docs: `production_runner.py:92,208` and `training_runner.py:89,349,441` hard-code `"launch_capable": False` / `"performance_disposition": "REPAIR_REQUIRED"`, and `analysis.py:398` / `panel.py:1148` raise `PRODUCTION_ANALYSIS_UNAVAILABLE` / `PRODUCTION_PANEL_VALIDATION_UNAVAILABLE` until the full 98-cell, ordered-28, whole-chain-telemetry inventory validates. §11.4 does not allow any of these to hold a B launch.

**Review comparison.** The 2026-09-01 review recommended `CONTINUE` with a stripped chain (B01-smoke → 3-seed B01, "matched curves only", review lines 170-187), and the addendum removed "the ordered-28 / TV / parameter-distance panel is not a launch condition". **Moved toward, in code only.** The working-tree changes to `b01/trainer.py` (+246) and `b01/checkpoint.py` (+209) are Slice-B work toward the 512-update chain — real progress toward the smoke. But no document was changed: the full-panel/ordered-28/telemetry/source-gate conditions the addendum demoted are still stated as launch blockers in all four B01 documents and still enforced in `production_runner.py`. Net: engineering toward, governance unchanged.

---

## 2. VNFC — variable_n_fleet_churn

**(a) Live object.** `VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0` at `A/RECON`, `result_bearing=false` (DIRECTION.md:36-37; A0 freeze lines 6-8). It is a conformance object standing between the direction and its actual B question (`VNFC-BPCR-BEXP-PRESENTATION-SAFE-RETURN-R02` at `B/EXPLORE`, DIRECTION.md:28-29). A0's ceiling: "finite-panel conformance sufficient to justify one fresh R02 DEBUG" (A0 freeze:26).

| # | Condition (quoted) | file:line | Class | Clause |
|---|---|---|---|---|
| 1 | "No R02 result-bearing DEBUG is permitted until the one-law A0 object is complete and passing under its finite claim ceiling." | DIRECTION.md:181-182 | DEMOTED | §11.6 (byte-addressed finite-action law as a conformance condition for a B run) |
| 2 | "Before any R02 DEBUG, exactly one finite physical-action law must prospectively fix: …7. an address-resolved conformance gate for structural predicates, deterministic commands, physically aligned probabilities, and RNG-coupled physical actions." | DIRECTION.md:96,105-106 | DEMOTED | §11.6; §11.1 (frozen contract as launch condition) |
| 3 | "Its frozen panel contains 304 address rows… Every physical CDF boundary, adjacent representable value and adjacent production word is enumerated" | DIRECTION.md:122-126 | DEMOTED | §11.6 (byte-addressed law); §11.4 (byte manifests) |
| 4 | "`PASS_CONFORMANT` requires every top-level row, every token, every CDF probe, every training replay, every containment check, and every independent predicate to pass exactly." | A0 freeze:880-881 | DEMOTED | §11.6; §11.2 (exact-equality obligation) |
| 5 | "binds exactly 942 loaded Python dependency sources plus the content-bound real `scripts/run_vnfc_bpcr_r02_a0.py` `__main__`, 31 opened distribution resources, and 81 compiled modules" | DIRECTION.md:41-44 (added today); A0 EM intake:36-39 | DEMOTED | §11.4 (byte manifests, hash chains) |
| 6 | "the source-keyed `bpcr_backend.dll` at literal build key `7222d990…`, forbids compilation, helper subprocesses, fallback, or cache mutation, and changes the compiled inventory from the frozen 81-row pre-load root to exactly the frozen 82-row post-load root" | DIRECTION.md:47-51 (added today); A0 EM intake:52-58 | DEMOTED | §11.4 (byte manifests / hash chains) |
| 7 | "Framework autograd or a different algebraic derivative association is not an implementation of this law." (memoized scalar reverse DAG) | DIRECTION.md:174-176 (added today) | DEMOTED | §11.2 (bit identity not required to run a B object) |
| 8 | "`FAIL_LAW` … returns this law for revision, has no algorithm polarity, and forbids R02 DEBUG." | A0 freeze:883-886 | DEMOTED | §11.6 |
| 9 | "Forbidden now: … any result-bearing R02 DEBUG, PRIMARY, OPTIONAL, return endpoint, learner training, or B claim" | A0 freeze:903,908 | DEMOTED | §11.4 (prospective contract holding a B launch) |
| 10 | "fresh 4-GiB admission, complete telemetry, create-once quarantine, and B/EXPLORE claim semantics" transfer to R02 | DIRECTION.md:94 | ALLOWED (admission) / DEMOTED (complete telemetry) | §11.4 both halves |
| 11 | "`INCOMPLETE` is missing/invalid source identity, dependency drift, nonfinite value, absent address, artifact/telemetry failure…" | A0 freeze:888-890 | UNCLEAR | §11.4 final sentence explicitly leaves instrumentation-failure annulment undecided |

**(d) Calibration acknowledged:** **no** — and the direction moved further from it today. The three files modified on 2026-09-02 add byte-level bindings (942 sources, 31 resources, 81→82 module transition, the DLL build key, the scalar-reverse-DAG identity law); none removes a condition.

**(e) Formal products still required as prerequisites:** the whole 304-row byte-addressed finite-action law is a prerequisite for any learner run (DIRECTION.md:181-182). §11.6 names precisely this: "byte-addressed finite-action laws as conformance conditions for a B run" are demoted to optional analysis. Also the "finite zero-residual MAPR-in-DIRECT deterministic and stochastic containment" exact-equality requirement (DIRECTION.md:104).

**(f) Cheapest next B run:** swap the canonical opaque-rank sort into the existing R01 runner and run one 8-update R02 DEBUG plus three 64-update seeds at `N={3,5}` with `N=7` evaluation, under a unit-test-scale (~50-row) presentation-conformance check. **Blocked by a disallowed gate: yes** — DIRECTION.md:181-182 forbids any R02 DEBUG until the 304-row A0 passes, and A0 has not been implemented (`implementation_started=false`, A0 freeze:15).

**Review comparison.** The review's disposition was `RECAST`: recast the law to one page, replace the 304-row panel with ~50 rows, "demote the rest from gate to record" (review:326-350); the addendum states "the 304-row binary64 finite-action law is demoted from conformance condition to optional analysis". **Moved away.** Today's edits to `DIRECTION.md`, the A0 freeze (+336 lines) and the EM intake (+102) are all in the direction of more literal byte binding, not less; the panel is now specified down to "80 support-matched candidate children and exactly 512 CDF children" and "292 presentation-specific replay/gradient/optimizer records" (DIRECTION.md:126-130).

---

## 3. CBSC — capability_bound_semantic_currentness

**(a) Live object.** `CBSC-OMRC-B01` (Online Multi-Opportunity Recurrent Currentness Scout) on `CBSC-DYNAMIC-CACHE-2R-1C-v1`, `B/EXPLORE`, status `PRO_INNOVATOR_BOUND_IMPLEMENTATION_READY_WITH_NULL_DERIVED_FIELDS` (DIRECTION.md:18-20,185-186). The next run is `CBSC-OMRC-B1-THREE-SEED-SCOUT`, seeds `21101/21121/21143` (DIRECTION.md:274-278). `B0-INSTRUMENT` has run (artifact `temp/directions/capability_bound_semantic_currentness/exp/cbsc_omrc_b0_instrument_888bd9f50_r02`).

| # | Condition (quoted) | file:line | Class | Clause |
|---|---|---|---|---|
| 1 | `FORMAL_ANALYSIS_BOUND = False` → `blockers.append("formal .03 metrics analysis/publication law is not bound")`; `if READINESS_DISPOSITION != "READY": blockers.append(...)` | `omrc_b01/b1_metrics_artifact.py:41-42`; `omrc_b01/b1.py:102-105` | DEMOTED | §11.6 (formal-analysis-bound flags that refuse a complete learner chain) — named verbatim in the addendum |
| 2 | `raise B1MetricsProductionError("REPAIR_REQUIRED: formal metrics publication awaits whole-pipeline CLEAN review")` | `omrc_b01/b1_metrics_production.py:1580-1583, 1913-1916` | DEMOTED | §11.4 (capacity gate) |
| 3 | "Implementation readiness does not authorize result execution. Before B1, CM must first establish literal-law conformance, full recurrent-PPO rather than Q/replay realization, B0 completeness, resource admission/telemetry, create-only publication, and every parity audit." | CM contract:156-159 | Mixed: PPO-realization + parity ALLOWED (§4.2/§4.5), "create-only publication" + "every parity audit" as a launch gate DEMOTED | §11.4 |
| 4 | "It must set every derived AUC/mean/regret, diagnostic, separation/concentration/instability, adverse-seed, promotion, B2-trigger, branch, and polarity field to literal null." | CM contract:123-127; DIRECTION.md:285-291 | DEMOTED | §11.6 (consumer-recompute gate that does not change a B decision) |
| 5 | "False or null competence blocks both STRUCT interpretation and B2" (mechanical RAW-competence gate: beat `ALWAYS_REFRESH`/`ALWAYS_SAFE`, ≥80% serve, ≥2 actions, zero missing records) | DIRECTION.md:293-298 | ALLOWED | §4.2 (relevant comparator must be competent); the review also classes it `SCIENTIFICALLY_NECESSARY` |
| 6 | "`CBSC-OMRC-B2-TWO-SEED-STABILITY` may add unchanged seeds `21161, 21179` only after the mandatory interim `em:…:convergence` decision returns `RUN_FIXED_B2_STABILITY`." | DIRECTION.md:279-281 | DEMOTED | §11.1 (consumption semantics / adaptation control as a C-time obligation; §5.2 permits adaptation between named B runs) |
| 7 | "Immediately before every B0 arm or B1/B2 arm-seed invocation or slice, run `python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` and require at least 4 GiB physical and effective available memory." | CM contract:115-117 | ALLOWED | §11.4 (resource admission) |
| 8 | "Per invocation, peak RSS is capped at 4 GiB and scratch at 2 GiB; B0 wall time is capped at 30 minutes and B1/B2 at 120 minutes." | CM contract:117-119 | ALLOWED as budget; DEMOTED if used as an invalidator | §11.4 |
| 9 | "The implementation must exercise the real environment, policy, recurrent learner, PPO trainer, and adaptation-free held-out evaluator with nonzero transitions, optimizer updates, and evaluations." | CM contract:23-25 | ALLOWED | §5.2 / §11.4 (nonzero counts) |
| 10 | "Implementation/instrumentation failure, leakage, support failure, unequal exposure … is a blocking mechanical fact" | CM contract:129-132 | UNCLEAR | §11.4 final sentence (instrumentation-failure semantics not decided) |

**(d) Calibration acknowledged:** **no**. Four CBSC documents were modified today; none mentions §11. The edits to `DIRECTION.md` and the CM contract in fact *added* the metrics-only/literal-null delegation (`DIRECTION.md:285-291`, `METRICS_ONLY_CONVERGENCE_CLASSIFIES` at :31) — i.e. they codified the consumer-recompute boundary the addendum demotes.

**(e) Formal products still required:** none of the theorem type. The residue is procedural: the "whole-pipeline CLEAN review" behind `FORMAL_ANALYSIS_BOUND`, and independent consumer recomputation of `compute_b1_mechanical`. §11.6 demotes both ("formal-analysis-bound flags that refuse a complete learner chain… capacity or consumer-recompute gates").

**(f) Cheapest next B run:** the frozen three-seed B1 (four arms × 384 episodes × 48 updates, checkpoints 0/12/24/48, 64 held-out episodes per checkpoint), publishing per-tape returns, per-decision actions and truth, per-step losses, and the new `postclip_gradient_norm` / `parameter_sha256_after_step` exposure line. **Blocked by a disallowed gate: yes** — three code constants (`FORMAL_ANALYSIS_BOUND = False`, `READINESS_DISPOSITION = "REPAIR_REQUIRED"`, and the two `b1_metrics_production` raises) refuse the publication path for a non-test run.

**Review comparison.** The review recommended `CONTINUE`, launching B1 "without the consumer-recompute and capacity-projection gates" plus a pre-declared `B1b` at 4× updates (review:491-500); the addendum: "`FORMAL_ANALYSIS_BOUND = False` and the consumer-recompute and capacity gates may not hold a B launch". **Split.** Toward, in `ppo.py`: the working-tree change adds per-step exposure telemetry (rollout index, post-clip gradient norm, optimizer step count, parameter digest) — exactly the §11.4 exposure line. Away, in docs: the modified `DIRECTION.md`/CM contract entrench the metrics-only literal-null delegation, and `FORMAL_ANALYSIS_BOUND` is still `False`. No budget ladder (`B1b`) has been declared.

---

## 4. SCDMP — semigroup_consistent_duration_model_policy

**(a) Live object.** `SCDMP-MF-RS-MK-ORDER-VALUE-B01`, `B/EXPLORE`, bound to the fresh named base run `…-RUN-01-REPLACEMENT-01` / `…-ATTEMPT-01` (DIRECTION.md:375-377; science card:7-11). The prior attempt is quarantined for `telemetry_measurement_failed` (DIRECTION.md:367-369; confirmed in `temp/scdmp-b01/RUN-01/terminal-no-polarity.json`, `"status":"QUARANTINED_INCOMPLETE_ATTEMPT"`).

| # | Condition (quoted) | file:line | Class | Clause |
|---|---|---|---|---|
| 1 | `raise ResultExecutionDisabled("RUN-01 performance readiness receipt is required")` / `"… receipt is invalid"` | `multifoundation_reachable_order_value/runner.py:606-611` | DEMOTED | §11.4 (capacity gate). The only existing assessment records `"performance_readiness": "REVIEW_REQUIRED"` (`temp/scdmp-b01/A-R2/assessment.json`), so this gate is currently closed |
| 2 | "no scientific artifact may be created until the following order is satisfied: … 3. arm continuous process-tree peak-RSS, scratch-high-water, durable-byte and wall/resource telemetry and record a valid initial observation … 8. only then create models, optimizers, checkpoints…" | science card:72,79-81,88 (added today) | DEMOTED (telemetry arming as a launch precondition) | §11.4 (telemetry completeness beyond the run's own claim) |
| 3 | "2. perform a fresh invocation-specific memory admission and observe at least `4 GiB` physical and effective available memory" | science card:77-78 | ALLOWED | §11.4 (resource admission) |
| 4 | "A missing measurement invalidates the attempt just as a measured cap exceedance does." | science card:530-531 | UNCLEAR | §11.4 final sentence — the downgrade-vs-annul question is explicitly not decided; the review classes this `REMOVE_OR_DOWNGRADE` |
| 5 | "Missing or invalid telemetry, uncertain frontier commitment, escaped partial results, … forbids resume and permanently quarantines that attempt." | science card:96-99 (added today) | UNCLEAR / DEMOTED | §11.4 final sentence; §6.2 quarantine rule unchanged |
| 6 | "failed physical/effective `4 GiB` admission or missing peak-RSS, scratch or durable telemetry" produce no scientific polarity | science card:621 | ALLOWED (admission half) / UNCLEAR (telemetry half) | §11.4 |
| 7 | "A foundation qualifies only when all of these B eligibility counts hold: at least `24/32` missions safely dock in every cell; at least `109/128` safely dock pooled…" — else stop as `FOUNDATION_COMPETENCE_NOT_ESTABLISHED` | science card:201-211 | ALLOWED | §4.2 (comparator/treatment competence); review classes it `SCIENTIFICALLY_NECESSARY` |
| 8 | "Scientific activity requires nonzero training transitions, optimizer steps and real evaluator calls." | science card:513-514 | ALLOWED | §5.2 / §11.4 |
| 9 | "process-tree peak RSS `<= 2 GiB`; scratch high water `<= 256 MiB`; durable output `<= 256 MiB`; and wall time `<= 30 minutes`" | science card:525-528 | ALLOWED as budget; DEMOTED as invalidator (see #4) | §11.4 |
| 10 | "any opening, traversal, read, hash, copy, … of the quarantined old physical root" is invalidating; "An external tombstone … may be checked only to refuse the old path before content access" | science card:616-618; :70-71 | ALLOWED | §6.2 quarantine (explicitly unchanged by §11.4) |
| 11 | "generation or reading of held-out tapes before atomic action-map freeze"; "overlap among training, state-source, development and held-out RNG domains" | science card:641-642 | ALLOWED | §4.5 (leakage) |
| 12 | "a `q_by_cell` vector outside `001110/011100/100011/110001`, or selection after any model, competence, source, development, held-out or outcome observation" | science card:626-627 | ALLOWED | §4.5 / §5.2 (no outcome-informed relabelling) |

**(d) Calibration acknowledged:** **no**. `DIRECTION.md` and the science card were both modified today; neither mentions §11 or 2026-09-02. The card's changes *add* the eight-step ordered-commitment protocol and the zero-access quarantine regime.

**(e) Formal products still required as prerequisites:** none for B01 — DIRECTION.md:311 already says "complete-support proof is not an admission condition", and DIRECTION.md:290-291 states the unresolved theorem/witness dichotomy "does not keep, park, reopen, or recast SCDMP". This is the one direction whose documents were already close to §11.2 before the calibration. (The addendum's further point — that the duration menu `k ∈ {7,13}` is a legitimate suboptimal scheme under §11.3, and `τ(1−γ)/(1−γ^τ)` is its error bound — is not recorded anywhere in the direction.)

**(f) Cheapest next B run:** `RUN-01-REPLACEMENT-01` exactly as frozen — seeds `1709/2903`, 160 updates × 12 episodes, 9-point curves, 128-mission competence, six state twins, 18-action development sweep, 16 held-out tapes; `A-R2` projects ~350 s against a 1,800 s cap. **Blocked by a disallowed gate: yes** — `runner.py:606-611` refuses to run without a `PERFORMANCE_READY` receipt, and the only assessment on disk says `REVIEW_REQUIRED`. Everything else is ready.

**Review comparison.** `CONTINUE`, `RUN_NOW`: "Exactly the frozen card … treat telemetry as recorded, not gating" (review:646-652); the review explicitly flags both the `PERFORMANCE_READY` receipt (review:631) and telemetry-as-invalidator (review:630) as `REMOVE_OR_DOWNGRADE`. **Moved away on both points.** The card edits add the ordered telemetry-arming precondition (:79-81) and a stricter resume/quarantine rule (:96-99), and `RUN_01_PERFORMANCE_DISPOSITION = "REPAIR_REQUIRED"` plus the receipt gate are unchanged from HEAD. The one movement toward the review is the fresh-attempt identity (`REPLACEMENT-01`), which the review itself noted was already resolved by the Innovator intake.

---

## 5. UCOPE — uncertainty-conditioned observation and paid evidence

**(a) Live object.** `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01`, `B/EXPLORE`, `NEXT_DISCRIMINATOR_COUNT=1` (DIRECTION.md:195-196). Two arms, `FT-XF-BC-RAW` vs `FT-XF-BC-WHITENED`, three seeds × two folds at the unchanged 160/320-update exposure (DIRECTION.md:210-216). `PAID_ACQUISITION_STATUS=UNEVALUATED_LOCKED`, `COUNT_RAW_STATUS=LOCKED_UNTIL_COMPETENCE` (DIRECTION.md:197-198).

| # | Condition (quoted) | file:line | Class | Clause |
|---|---|---|---|---|
| 1 | "Before any result-bearing invocation, CM must return implementation evidence showing: 1. … 8. create-once manifest/checkpoint/result binding, full activity and resource telemetry, complete-only publication, and incomplete-attempt quarantine" | prospective contract:462,478-479 | DEMOTED | §11.4 (telemetry completeness / prospective contract as launch condition) |
| 2 | "9. real environment, learner, trainer, checkpoint, and evaluator calls with nonzero transitions, updates, and evaluations in the result path." | prospective contract:480-481 | ALLOWED | §5.2 / §11.4 (nonzero counts) |
| 3 | "CM must also produce outcome-blind A/RECON performance evidence for the exact implementation." | prospective contract:483-484 | DEMOTED | §11.4 (capacity gate) |
| 4 | "Otherwise it remains `REPAIR_REQUIRED` with no science. … A later manifest may bind only the exact create-once `assessment-03` bytes, their source aggregate, V3 schema, V2 projection law, frozen topology, and `PERFORMANCE_READY` disposition." | prospective contract:705-708 | DEMOTED | §11.4 (byte manifests + capacity gate). On disk `assessment-02.json` is already `PERFORMANCE_READY`, but the contract declares it `INVALID_NOT_ADOPTED` (:561) and requires a fresh V3 `assessment-03`, which does not exist |
| 5 | `if status.stdout.strip(): raise RunnerRefusal("prepare-run requires clean committed source inventory")` | `scripts/run_ucope_bc_conditioning_discriminator_r01.py:82` | DEMOTED | §11.4 (byte manifests) |
| 6 | `if observed != record or assessment["disposition"] != "PERFORMANCE_READY": raise RunnerRefusal(...)` | `scripts/run_ucope_bc_conditioning_discriminator_r01.py:127` | DEMOTED | §11.4 (capacity gate) |
| 7 | "The result manifest must bind a clean committed source revision, source-byte inventory, exact config, three seeds, RNG/data ancestry law…" | prospective contract:711-714 | DEMOTED | §11.4 (byte manifests) |
| 8 | "Immediately before every result-bearing attempt, run the central memory admission and require both physical and effective available memory to be at least `4,294,967,296` bytes." | prospective contract:710-711 | ALLOWED | §11.4 (resource admission) |
| 9 | `C_even(P) = … AND exact_eight_context_oracle_root_vector AND maximum_expected_regret <= 1/50 AND minimum_forced_PROBE_tail_agreement >= 19/20`; "Update 320 alone controls competence." | prospective contract:324-333 | DEMOTED | §11.1 (oracle-retuned comparator as a pass/fail condition); addendum names it directly |
| 10 | "even a conditioning competence pass cannot open either automatically" (acquisition and COUNT/RAW stay locked) | DIRECTION.md:62-63 | DEMOTED | §11.1 (consumption semantics / gate chaining); §11.4 |
| 11 | "No unchanged B1 repeat, audit rerun, extra B1/audit score read, budget enlargement, acquisition evaluation, or COUNT/RAW work is permitted." | DIRECTION.md:228-230 | DEMOTED | §11.1/§5.2 (B may be adapted between named runs; a named exposure ladder is a new B object, not enlargement of a running one) |
| 12 | "Non-positive-definite `G` stops rather than admitting ridge, truncation, or outcome-dependent repair." | DIRECTION.md:215-216 | ALLOWED | §4.5 / §5.2 (blocks outcome-informed repair) |
| 13 | "Group-disjoint folds", odd/even support separation, "It may not read B1 or audit runtime rows" | prospective contract:305-311 | ALLOWED | §4.5 (leakage) |
| 14 | "A late, different, or unverifiable topology is `REPAIR_REQUIRED`" (deterministic algorithms, 1 thread) | prospective contract:589-592 | DEMOTED as a gate; ALLOWED as a recorded fact | §11.4 |

**(d) Calibration acknowledged:** **no**. `DIRECTION.md` was modified today (+99 lines) to record the odd-support audit and select the whitening discriminator; it does not mention §11 or the calibration, and it re-states the locks (`:62-63`, `:228-230`).

**(e) Formal products still required:** the exact-oracle competence predicate (exact eight-context oracle root vector, exact rational thresholds — prospective contract:310-314, 324-330) functions as the direction's admission condition for its own scientific question. §11.2/§11.1 demote exact-oracle criteria as gates; the addendum states it "stops being a pass/fail gate on a B run and becomes a recorded observation".

**(f) Cheapest next B run:** the exposure ladder — the existing B1 code, arms `FT-XF-FLEX`/`FT-XF-BC`, 3 seeds × 2 folds, one named run at lr `3e-3` at the frozen 160/320 updates (~140 s), reporting competence flags, regret, tail agreement, PROBE rate, plus the parameter-displacement exposure line. **Blocked by a disallowed gate: yes, twice over.** (i) DIRECTION.md:228-230 forbids a "budget enlargement" and any unchanged-B1 rerun, which reads on the ladder; (ii) for the already-selected whitening discriminator, `run_ucope_bc_conditioning_discriminator_r01.py:82,127` refuse `prepare-run`/`run` without a clean committed source inventory and a `PERFORMANCE_READY` assessment-03 that does not exist — while the `PERFORMANCE_READY` assessment-02 that does exist is declared ineligible by contract line 561.

**Review comparison.** `RECAST`: run the exposure ladder first, whitening discriminator alongside (explicitly "not instead of"), margin-scaled falsifier in reserve; the addendum: "Exposure ladder first, whitening discriminator alongside; competence at training durations is a B observation". **Moved away.** The direction adopted the whitening discriminator *as the sole* continuation ("The direction continues only through…", "`NEXT_DISCRIMINATOR_COUNT=1`", DIRECTION.md:131-132,194) — precisely the substitution the review warned against at :826-828 — kept the exact-oracle competence criterion as the gate, and kept the acquisition/COUNT-RAW locks. No exposure-ladder or margin-falsifier object exists.

---

## Cross-direction summary

| Direction | Live object | Demoted conditions still binding | Formal prerequisites still required | Calibration acknowledged | Cheapest next B run | Blocked by a disallowed gate |
|---|---|---|---|---|---|---|
| **FRRIE** | `FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901` (B/EXPLORE, no result) | **8** (rows 1-7, 13-14; 2 further UNCLEAR-free) | Exact no-projection-contact equality theorem; universal all-update/all-transition absorption certificate (re-entry conditions) — §11.2 demotes both | no | 1-seed 128-update PHY/EDGE smoke, INTACT at `N={9,15}`, curves + contact + competence + RSS | **yes** — `launch_capable=False` and `PRODUCTION_*_UNAVAILABLE` raises pending the 98-cell / ordered-28 / whole-chain-telemetry panel |
| **VNFC** | `VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0` (A/RECON) gating `…R02` (B/EXPLORE) | **9** | The whole 304-row byte-addressed finite-action law + zero-residual containment equality — §11.6 demotes explicitly | no (moved further away today) | R02 DEBUG (8 updates) + three 64-update seeds, MAPR-4 / DIRECT-SET-AR / BCRH-PERSIST, train `N={3,5}`, eval `N=7` | **yes** — DIRECTION.md:181-182 forbids any R02 DEBUG until A0 passes; A0 not implemented |
| **CBSC** | `CBSC-OMRC-B01` → `B1-THREE-SEED-SCOUT` (B/EXPLORE; B0 done) | **5** | none of the theorem type; a "whole-pipeline CLEAN review" and consumer recomputation remain procedural prerequisites (§11.6) | no | The frozen 3-seed, 4-arm B1 (48 updates, checkpoints 0/12/24/48) with descriptive curves published directly | **yes** — `FORMAL_ANALYSIS_BOUND = False`, `READINESS_DISPOSITION = "REPAIR_REQUIRED"`, and two `b1_metrics_production` refusals |
| **SCDMP** | `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01` (B/EXPLORE) | **2 clear + 3 UNCLEAR** (telemetry-as-invalidator sits in §11.4's undecided clause) | none — DIRECTION.md:311 already waives complete-support proof | no | `RUN-01-REPLACEMENT-01` exactly as frozen; `A-R2` projects ~350 s vs a 1,800 s cap | **yes** — `runner.py:606-611` requires a `PERFORMANCE_READY` receipt; the only assessment says `REVIEW_REQUIRED` |
| **UCOPE** | `UCOPE-B-EXPLORE-FT-XF-BC-INVERTIBLE-CONDITIONING-DISCRIMINATOR-R01` (B/EXPLORE) | **9** | Exact-oracle competence predicate (root vector + regret ≤ 1/50 + tail agreement ≥ 19/20) as the gate on the direction's own question — §11.1/§11.2 demote | no | Exposure ladder: existing B1 code, 3 seeds × 2 folds, lr `3e-3` at 160/320 updates (~140 s) | **yes** — DIRECTION.md:228-230 bans "budget enlargement"; runner refuses without clean-committed-source + a nonexistent `PERFORMANCE_READY` assessment-03 |

### Cross-cutting observations

- **Zero of five directions acknowledge the calibration**, including the nine documents modified today. §11.6's instruction ("Direction owners SHOULD record the demotion in the direction's next intake") has not been acted on anywhere.
- **All five are blocked by at least one gate §11.4 does not permit, and in every case the operative block is in code, not only in prose** — `launch_capable=False` (FRRIE), the A0 conformance precondition (VNFC), `FORMAL_ANALYSIS_BOUND` (CBSC), the `PERFORMANCE_READY` receipt (SCDMP, UCOPE). Editing documents alone will not unblock any of them.
- **Net movement since the review**: VNFC away (byte binding deepened), UCOPE away (whitening substituted for the ladder; locks retained), SCDMP away on the two gates the review named while adopting the fresh-attempt identity it endorsed, CBSC split (exposure telemetry added in `ppo.py`; consumer-recompute boundary entrenched in docs), FRRIE toward in engineering only (trainer/checkpoint work) with no governance change.
- **What I could not determine**: whether the FRRIE `b01/` Slice-B work in the working tree is close enough to run a 128-update chain (I read the module inventory and the hard-coded dispositions, not the trainer's completeness); whether a §11.4-conforming exposure line exists for SCDMP (the card requires "every training metric" but no parameter-displacement statement); and whether CBSC's B0 artifact `cbsc_omrc_b0_instrument_888bd9f50_r02` was accepted as complete (I did not open it).

---

## Part C — SCDMP recast intake (2026-09-02, later)

Object: decision 1 of A.4 executed by an Opus session on `main`: commits `c5a10ef4c` (the
direction's uncommitted working-tree state, 21 files, committed unchanged for provenance),
`d9c052ed9` (recast intake `SCDMP_B01_SECTION11_RECAST_INTAKE_20260902.md`, DIRECTION.md entry,
science-card addendum), `c5c1655e9` (receipt and telemetry gates to recorded fields; 17 new test
cases; direction suite 566 passed), `b76d06cec` (result document
`SCDMP_B01_RUN_01_REPLACEMENT_01_RESULT_EVIDENCE_20260902.md`). File scope verified by
`git show --name-only`: every path is under the SCDMP direction, implementation, tests, or its
run script. Verdict: **accepted as a valid, complete B/EXPLORE run; recast in force.**

### C.1 What the reviewer checked

1. **Gates to fields, not weaker integrity.** `runner.py`'s `ResultExecutionDisabled` receipt
   refusal is replaced by `performance_assessment_record()` with `gating: false`, which records the
   receipt (absent), the A/RECON assessment (`REVIEW_REQUIRED`), and the source constant
   `RUN_01_PERFORMANCE_DISPOSITION` (still `REPAIR_REQUIRED`, recorded beside it). Telemetry
   failure reasons are partitioned into unmeasured (`telemetry_missing`,
   `telemetry_measurement_failed`, `telemetry_zero_work` → `resources_unmeasured: true`) and
   invalidating (the four measured cap exceedances, cumulative wall, nonzero exit → still fail and
   quarantine). Unchanged: "published RUN-01 is immutable", 4 GiB admission, competence gates,
   nonzero-count reconciliation, `q_by_cell` law, RNG-domain separation, zero-access quarantine,
   create-once publication, §6.2 learner-side quarantine. This is decisions 1 and 7 exactly.
2. **The run.** Launched at `c5c1655e9`, SCDMP paths clean; preflight 14.47 GiB available;
   wall 348.5 s against the 1,800 s cap (A-R2 projected 350.1 s); telemetry fully measured
   (peak RSS 400 MB of 2 GiB, scratch 459 KB, durable 130 MB); exit 0; nothing quarantined; the
   frozen object executed as written (seeds 1709/2903, 160 × 12, nine curve points, 128/128
   competence both seeds, six twins, 18-action sweep, 16 held-out tapes, realized
   `q_by_cell = 001110`).
3. **Branch.** The card's rule applied verbatim gives branch 5,
   `PRELIMINARY_REPEATABLE_ORDER_VALUE_SIGNAL`: `delta_swap` 0.0611 / 0.0647 and `delta_common`
   0.0260 / 0.0261 per seed, positive in both `k` strata and 6/6 states for each contrast in
   each seed. The card says branches 5–8 are exploratory B observations, never direction
   decisions; the result document says the same and claims nothing beyond §14.
4. **Deviations.** D1 (no receipt) is the decision itself. D2: the native build cache under
   `%LOCALAPPDATA%\Temp\hmasd_scdmp_mf_rs_mk_native\c0aeb83f…` is unreadable and undeletable
   by the owning user, so `TMPDIR/TEMP/TMP` were redirected to a sibling of the run root and
   the DLL rebuilt from the unchanged source (same source sha256, flags, ABI); only the resolved
   path in `source-identity.json` differs. Accepted as a technical deviation with no scientific
   factor touched. D3 (`hmasd_run.py` not used): the card's own runner owns the manifest;
   consistent with E0. D4 (torch interop threads at the platform default 8, intraop 1 as the
   card declares): exceeds the reviewer's "4 threads" instruction, not the card; harmless.

### C.2 The observation that bounds the result

The SWAPPED arm returned `U = 0.0` in all 384 cells: every swapped first action absorbed with
`cable_overload` after 6 transitions and 0 policy queries. So `delta_swap ≡ M`, and the
matched-versus-swapped separation is the swapped control's immediate failure, not a graded return
difference. The COMMON arm absorbed the same way in exactly the 80 cells whose common action was
evaluated under the graph it is not matched to. The informative contrast is therefore
`delta_common` (about 41% of `M`), and even that carries the absorption in 80 of 384 cells. The
result document records this as a direct observation (§8, §13) and the card defines no polarity
for it. Reviewer's reading, not the card's: on this host the "value of order" is dominated by an
absorbing failure of the wrong first action, which is a property of the cable dynamics rather than
of the learner; a graded order-value question needs a host row where the wrong order is costly but
not fatal. That is a different object and is put to the owner in C.4.

### C.3 Flags for the owner

- **Poisoned native caches under `%LOCALAPPDATA%\Temp`.** The undeletable
  `hmasd_scdmp_mf_rs_mk_native` directory is the same reason `tests/production_backend_policy_test.py`
  fails 25 of 74 (`onlgr.*`, `vnfc_bpcr.*`, `scdmp_tbcc.*` loaders). Clearing them needs elevated
  rights; the VNFC recast (its `bpcr_backend.dll` is source-keyed under the same root) will meet
  the same wall and will use the same redirect unless the caches are cleared first.
- **`RUN_01_PERFORMANCE_DISPOSITION = "REPAIR_REQUIRED"`** stays in the source as a recorded
  constant; nothing reads it as a gate any more. Left as is deliberately so the history is visible.

### C.4 Decisions this intake produces

1. SCDMP's next object: `RUN-02A` (seed 4013) and `RUN-02B` (5171, 6361) as the card's promotion
   ladder, now bindable to this base run; or first a cheap diagnostic object on why the swapped
   arm is uniformly fatal (a host row where the wrong first action is costly but survivable), so
   that the order-value contrast becomes graded before more foundations are spent. The reviewer
   recommends the diagnostic first. **Owner decision (2026-09-02): the diagnostic object first;**
   RUN-02A/02B stay as frozen and are not launched until the diagnostic is in. The diagnostic is a
   new scientific object with its own one-page card (host row, reading rule, prediction) written
   before any run; it is scheduled after the UCOPE recast under the two-concurrent budget.
2. Native caches: **owner decision (2026-09-02): the owner clears the `%LOCALAPPDATA%\Temp\hmasd_*`
   directories with elevated rights; later recast sessions do not redirect `TMP` and use the
   default cache root.** Until the clearing is confirmed a session that meets the wall records the
   redirect as a deviation, as SCDMP did. **Cleared 2026-09-02 17:54 PDT** (owner, elevated
   PowerShell; reviewer verified every `hmasd_*_native` root absent). From here on native backends
   rebuild into the default root on first use and no session redirects `TMP`.

PORTFOLIO row for `semigroup_consistent_duration_model_policy` updated by the reviewer in the
commit carrying this part (next-object text and timestamp only; lifecycle, priority, owner
unchanged).

---

## Part D — UCOPE recast intake (2026-09-02, later)

Object: decision 2 of A.4 executed by an Opus session on `main`: commits `3423d5aca` (the
direction's uncommitted working-tree state, 23 files, committed unchanged), `bd8648964` (recast
intake `UCOPE_SECTION11_RECAST_INTAKE_20260902.md`, DIRECTION.md corrections, contract addenda;
the exposure ladder registered as `UCOPE-B-EXPLORE-FT-XF-EXPOSURE-LADDER-R01`), `ce361d40a`
(refusals and the oracle-competence gate to recorded fields; 17 new test cases; direction suite
631 passed, 4 pre-existing failures in `contextual_paid_acquisition_r01`), `06cf712e7` (two result
documents). File scope verified by `git show --name-only`: every path under a UCOPE surface.
Verdict: **recast accepted; ladder rung 1 accepted as a valid complete run; the whitening
discriminator quarantined as an incomplete attempt (object not consumed).**

### D.1 What the reviewer checked

1. **Gates to fields.** The clean-source refusal records the porcelain status, HEAD sha and the
   per-file inventory with `gating: false`; the assessment-03 binding records the assessment that
   exists (`assessment-02`, `PERFORMANCE_READY` on disk, `INVALID_NOT_ADOPTED` by contract line
   561) and gates on neither; the resource-cap refusal records exceedances and, when a field is
   missing, `resources_unmeasured` with reasons (decision 7); `C_even` is computed at unchanged
   thresholds and published per run, with a test asserting that no publication path branches on
   it. DIRECTION.md's "continues only through" became "alongside" with the old sentence quoted;
   the "no budget enlargement" sentence is superseded for named ladder rungs only, citing §5.2
   and §11.1. Still gating: 4 GiB admission, §4 integrity items, nonzero counts, one exposure
   line, §6.2 learner-side quarantine. This is decision 2 exactly.
2. **The ladder as registered.** Rungs verbatim from the 2026-09-01 review: rung 1 lr 3e-3 at
   160/320 updates; rung 2 lr 3e-4 at 1,600/3,200; rung 3 both. Reading rule frozen before the
   data (intake §4.5): `m` = the minimum over 12 policies × 2 stages of the largest absolute
   Bellman per-coordinate move at the final checkpoint; R1-A at least one arm `B_COMPETENT`;
   R1-B none competent and `m ≥ 0.30`; R1-C none competent and `m < 0.30`.
3. **Rung 1.** Preflight 10.74 GiB; wall 89 s; telemetry measured; 0 of 12 policies competent,
   0 oracle root-vector matches, both arms `NO_ARM_COMPETENT`; `m = 0.046` → **R1-C, exposure
   did not move** at this budget. The closest miss at update 320: regret 0.0286 against the
   recorded 0.02 threshold, tail agreement 1.000. By the frozen rule rung 1 is uninformative
   about the exposure hypothesis and rung 2 runs next; the reviewer has instructed the same
   session to run rung 2 (about ten times rung 1's wall) as the registered object prescribes.
4. **The whitening discriminator.** First-ever launch attempt under the recast; it failed in its
   own frozen core (`conditioning.py:106`, `ConditioningTransformError: recorded Gram/Cholesky
   relation is invalid`) in `prepare_fold_data`, before any model or optimizer. Quarantined, not
   rerun, no polarity. An outcome-free diagnostic on the design matrices alone (no learner, no
   quarantined artifact read) shows the failure is deterministic and universal at science scale:
   all 12 seed/fold/stage designs give `max|LLᵀ − G|` of 9.1e-06 to 9.7e-06 against the frozen
   `16·eps_fp32 = 3.81e-06` ceiling, at condition numbers 7e2 to 5e3. The implementer's
   inference, which the reviewer shares: the tolerance was calibrated at the 40-episode technical
   scale of the assessments, so the object as frozen is not executable at science scale.
5. **Deviations** are all recorded and none touches a scientific factor: the ladder runs two arms
   as registered (RNG counter-addressed); no A/RECON assessment for the ladder (the recast);
   E1's two processes ran concurrently (wall times are upper bounds); no native cache is involved
   in either UCOPE package; a post-hoc residual diagnostic is itself listed as a deviation.

### D.2 Reviewer's reading

Rung 1 says the 160/320 exposure is far too small for either arm to move, which is what the
2026-09-01 review predicted when it proposed the ladder. Nothing about the conditioning question
can be read yet. The discriminator's failure is a technical fact, not an outcome: under the
repository's own rule a technical failure creates no retry budget and no polarity, and a redesign
that fixes the tolerance (FP64 Gram, or a scale-appropriate FP32 ceiling) is a different object,
instrumentation-informed rather than outcome-informed, since no outcome was produced. Whether to
register that object is the owner's call (D.4).

### D.3 Flags for the owner

- The 4 pre-existing failures in `contextual_paid_acquisition_r01/test_structural_competence_certificate.py`
  predate the recast and are untouched; they are not native-cache failures.
- The discriminator runner's `prepare-run` lost its `--assessment` flag and its manifest format
  moved to a `…_RECAST_V1` schema; both recorded in the result document.

### D.4 Decisions this intake produces

1. The whitening discriminator: register a successor object with a scale-appropriate Gram /
   Cholesky tolerance (FP64 Gram at science scale; everything else frozen as R01) and run it
   alongside ladder rung 2; or drop the discriminator and continue only through the ladder; or
   park it until rung 2 says whether exposure moves anything. The reviewer recommends the
   third: rung 2 decides whether there is a conditioning question worth a discriminator at all.
   **Owner decision (2026-09-02): the discriminator is held until ladder rung 2 is in;** no
   successor object is registered now and the R01 quarantine stands.

PORTFOLIO row for `ucope` updated by the reviewer in the commit carrying this part (next-object
text and timestamp only).

### D.5 Ladder rung 2 intake (2026-09-02, later)

Commit `7f04b67ce` (result document `UCOPE_EXPOSURE_LADDER_R2_RESULT_EVIDENCE_20260902.md`, the
intake's Result paragraph, and the three files that register rung 2 in the runner; scope
verified). Launched at `ba8d165fc` with the tree dirty for exactly those three files, recorded
by the demoted clean-source field with the 14-file inventory pinned (aggregate `62f91839…`).
Preflight 12.77 GiB; wall 359 s; telemetry measured; 12 policies complete, 122,880 episodes,
614,400 transitions, every counter reconciled, `validate` true. **Accepted as a valid complete
run.**

Outcome by the frozen rule: 0 of 2 arms competent (closest at update 3,200: regret 0.0302
against 0.02, tail agreement 0.788 against 0.95); `m = 0.0253 < 0.30` → **R1-C again.** Ten
times the update budget did not move the minimum-over-24 statistic (rung 1: 0.046). On
`FT-XF-BC` alone the minimum move is 0.249 at both rungs.

Reviewer's reading. Two facts make rung 3 pointless under this rule and call for an integrity
check before any further exposure:

1. **The statistic is dominated by the FLEX arm.** `m` is the minimum over both arms' 24
   stage-policies; the BC arm's own minimum is 0.25 at both rungs, so the 0.025–0.046 that
   decides R1-C comes from FLEX stage-policies whose Bellman coordinates barely move. FLEX carries
   a residual that may absorb the displacement (not verified, listed in both documents). A rule
   whose branch is fixed by the arm that has no reason to move its Bellman head cannot detect
   exposure moving the other arm; rung 3 would return R1-C by construction.
2. **Two measurement anomalies** the implementer recorded and did not investigate: the BC arm's
   tail agreement is exactly `0.000000` in all 30 rows at both rungs, and each FLEX policy's
   agreement is constant across its five checkpoints. A learner does not produce an exact zero
   agreement in every row; this reads as the tail-agreement measurement not being wired for BC
   (or measuring a constant), which is a §4 integrity question, not an outcome. Until it is
   answered the competence observation for BC is not interpretable.

Consequence put to the owner (D.6): no rung 3 under the R01 rule. The next UCOPE object should
be an outcome-free instrumentation check of the tail-agreement and competence measurement on
both arms (unit-scale, no training), and only then a ladder successor R02 whose reading rule
takes the displacement statistic per arm. Both are new named objects; R01's two rungs stay as
recorded evidence that exposure up to 3,200 updates does not produce competence on this host
under either arm.

### D.6 Decisions this intake produces

1. UCOPE ladder: (a) instrumentation check first, then ladder R02 with a per-arm statistic
   (reviewer's recommendation); (b) run rung 3 as declared; (c) park the direction.
   **Owner decision (2026-09-02): (a).** Rung 3 of R01 is not run. The instrumentation check is
   an outcome-free, unit-scale object (no training); ladder R02 is registered only if the check
   passes, with the displacement statistic and the reading rule taken per arm and both fixed
   before its first rung.

### D.7 Instrumentation check and ladder R02 rung 1 intake (2026-09-02, later)

Commits `71fb70a3a` (check card, tests, result), `9ef1b36b6` (R02 registration, intake §9),
`71e33efdb` (R02 rung 1 result); scope verified, all under UCOPE surfaces. **Both accepted.**

**Instrumentation check `UCOPE-A-INSTRUMENTATION-TAIL-AGREEMENT-COMPETENCE-CHECK-R01`: PASS, no
defect.** Card written before the run; 77 test cases are the check. Tail agreement recovers 0,
1 and two intermediate known values on both arms to 1e-12 (exact 1/2 is unattainable on this
host, proved by enumerating all 128 count-mass subsets); the competence predicate can fire and
its four components match a `Fraction` reference; the displacement statistic recomputes every
published row of both R01 rungs to 1e-12. The two anomalies are explained and are not defects:
the FT arms complete the whole tail loop before the first root update (`training.py:226-234`),
so a policy's tail is byte-identical at every checkpoint; and every published BC tail model's
argmax lands on periods 2 or 8 only, while period 8 is never optimal and period 4 is the unique
optimum at belief 1/2 in the four all-or-nothing contexts, so those contexts score exactly 0.
The basis can represent the truth (max error < 1e-6 over 224 points), so the zeros are a
learning outcome. Two design facts recorded: the minimum tail agreement is a minimum over eight
contexts, four all-or-nothing; the R01 exposure line's per-coordinate move read only `beta`,
excluding FLEX's residual.

**Ladder R02 rung 1: `R2-D`, neither arm moved.** Per-arm rule fixed before data: each arm's
minimum over its 12 rows of the largest absolute per-coordinate move over all its trained
coordinates (FLEX's residual inside), threshold 0.30 for both, with the derivation recorded
(steps × lr ceiling 0.96 at the root stage; 0.30 about a third of it). Outcome:
`m_FLEX = 0.108`, `m_BC = 0.250`, both below 0.30; competence 0/6 per arm. Counting the residual
raises FLEX's minimum 2.3× over R01's statistic, not enough to change any branch; R01's records
are undisturbed and the 48 evaluation rows are byte-identical to R01 rung 1. Wall 109 s.

Reviewer's reading. The ladder question is now answered as far as it can be at this budget: BC's
minimum move is 0.250 at 160/320 and 0.249 at 1,600/3,200 updates, so BC is not exposure-limited;
it settles early at coefficients far from the exactly representable optimum (the check recovers
them by least squares with residual under 2e-7 and shows `max|β − β*| > 0.5` for every policy).
That is a property of the objective or its target, not of the update count. Rung 2 of R02 would
tell whether FLEX crosses 0.30 with ten times the budget (about six minutes) and would close the
registered object; it cannot change the BC conclusion. The next scientific object, if the
direction continues, is a diagnostic of the training target: why the learned β lands where it
does when the basis can represent the optimum (target package, bootstrapping, fold coupling are
all untouched by the check and by the ladders).

### D.8 Decisions this intake produces

1. UCOPE: (a) run R02 rung 2 to close the ladder, then register a training-target diagnostic
   object (reviewer's recommendation, since rung 2 is cheap and the diagnostic is where the
   answer is); (b) skip rung 2 and go straight to the diagnostic; (c) park the direction with the
   two ladders and the check as its record. **Owner decision (2026-09-02): (a).** R02 rung 2 runs
   to close the ladder; the training-target diagnostic is written as a card first (question,
   mechanisms, differentiating measurement, reading rule) and waits for the owner's prediction
   before any run.

### D.9 Ladder R02 rung 2 and the diagnostic card (2026-09-02, later)

Commits `3b1c42c92` (R02 rung 2 result) and `d56c5f9b7` (diagnostic card, written, not run);
scope verified. **Rung 2 accepted; the ladder object closes at `R2-D`.** Launch sha `905ca9246`,
bound inventory clean; preflight 10.70 GiB; wall 631 s at 4 threads; telemetry measured; 12
policies complete, every count reconciled, `validate` true. Per-arm rule verbatim:
`m_FLEX = 0.1075`, `m_BC = 0.2494`, both below 0.30; competence 0/6 per arm → neither moved.
The cross-rung fact that matters: with `steps × lr = 0.96` at both rungs, each arm's
least-moving coordinate changed by under one percent between rung 1 and rung 2 (FLEX
0.1081 → 0.1075, BC 0.2502 → 0.2494), set by the same policy and stage both times. Ten times the
optimizer budget at one tenth the step moved nothing; the learners are at a fixed point of
their own objective or their own optimizer, not short of exposure.

Diagnostic card `UCOPE_TRAINING_TARGET_DIAGNOSTIC_R01_CARD_20260902.md`: four mechanisms read
from the code (M1 the tail MSE objective's own fixed point differs from `β*`; M2 an optimisation
shortfall on an ill-conditioned Gram under clipped AdamW with unshuffled cyclic batches, where
the per-coordinate travel budget is identical at both rungs; M3 the root's frozen targets are
built from the learned tail and maximised over the odd training support while competence ranks
over the evaluation support; M4 fold coupling with the tail-before-root freeze), one
differentiating measurement each (X1 solve the tail normal equations and compare the gradient
at `β*` and at the published `β`; X2 rebuild the root targets from the oracle tail, from the
normal-equation tail and from each published tail; X3 an extended `_step` loop only if X1 calls
for it; X4 per-fold solutions), a five-branch reading rule with `ε = 0.10` and a gradient ratio
of 10 fixed before data, and a budget under twenty minutes. One closed-form quantity was
computed while writing the card (the training-versus-evaluation support gap, at most 0.0037,
which makes the target-package branch unlikely) and is disclosed in the card. The card ends with
the prediction request to the owner; nothing runs until the prediction is on record.

### D.10 Decision this intake produces

1. The owner's prediction among M1–M4 or "none of these" (asked directly). **Owner's
   prediction on record (2026-09-02): M2**, optimisation shortfall on the ill-conditioned Gram
   under clipped AdamW with unshuffled cyclic batches; the objective's own optimum is still `β*`.
   The reviewer's prediction, for the record: M1 or M3 (the objective or the root's inherited
   targets), because the sub-one-percent change between rungs at equal `steps × lr` reads more
   like a converged fixed point than a starved optimiser; if M2 is right, X3's extended loop
   should keep moving. The diagnostic runs on 2026-09-03 with both predictions on record.

---

## Part E — CBSC recast intake, run pending (2026-09-02, later)

Object: decision 3 of A.4 executed by an Opus session on `main`: commits `335559bcf` (the
direction's uncommitted working-tree state, 41 files, committed unchanged), `5502f5dcb` (recast
intake `CBSC_OMRC_B01_SECTION11_RECAST_INTAKE_20260902.md`, DIRECTION.md entry, addenda on the
CM contract and the metrics-only spec), `31b21d733` (gates to recorded fields, descriptive
curves published by the runner, tests; direction suite 282 passed with the one pre-existing
failure). Scope verified. Verdict: **recast accepted; the B1 run is held by a filesystem
permission fault, not by any gate.**

### E.1 What the reviewer checked

1. **Gates to fields.** `FORMAL_ANALYSIS_BOUND` and `READINESS_DISPOSITION` keep their historical
   values and are published with `gating: false` by `formal_analysis_record()` in the readiness
   document and every manifest; the two `blockers.append` lines, the `MetricsArtifactError` on
   the flag, the `FORMAL_ANALYSIS_BOUND` clause in the test-only check, and both
   `B1MetricsProductionError("REPAIR_REQUIRED…")` raises are removed (quoted in comments). The
   live supervisor now kills a child only on the wall cap; RSS, scratch and durable exceedances are
   recorded (`RECORDED_BUDGET_CAPS`). Slot telemetry failure records `resources_unmeasured` with
   reasons instead of raising. Still gating: §4 items, nonzero counts, the 4 GiB admission per
   invocation, the exposure line, leakage and equal-exposure audits, the RAW-competence gate, the
   120-minute wall cap, §6.2 quarantine. This is decision 3 and decision 7.
2. **Descriptive curves.** New `b1_descriptive.py` on the canonical source surface publishes
   per-checkpoint held-out mean/min/max returns, held-out action counts and serve rate, training
   action counts, one exposure line per arm-seed, and the RAW-competence flags. The manifest's
   derived fields (`auc_metadata`, `diagnostic_metadata`, branch, polarity, promotion, B2 trigger)
   stay literal null: the recast publishes what the run measures, not the consumer's analysis.
   B1b (4× updates) is declared as the ladder's next rung in the intake.
3. **D7 at the slot boundary only** (implementer's deviation 6, intake §8): a run whose telemetry
   is entirely absent downgrades at the slot but does not reach the 15-table publication, because
   the work reconciliation against `slice_counts` is a §4 item reading the same record. Accepted:
   that reconciliation is an integrity item, and threading a null measurement through the frozen
   schema is outside the recast. Recorded so the next contract does not inherit the coupling.
4. **`verify_source_conformance`'s clean-source requirement** was left gating (implementer's
   flag). It is a byte-manifest gate of the kind §11.4 demotes, as UCOPE's recast did for its
   equivalent. It is satisfied at `31b21d733`, so it does not hold this launch; **registered for
   demotion at CBSC's next code change**, not now.
5. **Tests.** `1 failed, 282 passed` against a baseline of `1 failed, 271 passed`; the failure is
   the pre-existing `test_unified_test_profile_runs_canonical_a_b_c_and_publishes_15_tables`
   (`FINAL_COUNTER_MISMATCH`; the test mixes two fixtures). The implementer tried a one-line fix,
   it moved the failure, and they reverted it: correct. Consequence: the end-to-end 15-table path
   with `descriptive_curves` is covered only by a smoke-scale round trip, so the first B1 run is
   also the first full exercise of the publication path; if it fails there, that is an
   instrumentation failure and the run quarantines under §6.2 without consuming the object.
6. **`tests/production_backend_policy_test.py`**: 12 failed, 62 passed, down from 25 after the
   cache clearing. The remaining 12 are artifact-SHA / build-key mismatches in `onlgr_tbvuus`,
   `rcle_tbcfv`, `scdmp_tbcc` plus the registry-separation test: the rebuilt DLLs hash
   differently from the pinned expectations. Those pins are the byte-manifest gates §11.4
   demotes; they belong to directions outside the first wave and are left for their owners.

### E.2 The blocker

`temp/directions/capability_bound_semantic_currentness/exp/cbsc_omrc_b0_instrument_888bd9f50_r02`
denies read access to the owner's account (`PermissionError [WinError 5]` on `iterdir` and on
`manifest.json`; `icacls` cannot read its ACL; every sibling is owned by the user and readable).
`run_b1_start` rehashes and copies the 33 B0 files first, so B1 cannot start until the directory
is restored with elevated rights (the same class of fault as the native caches). Also recorded:
no direction document records B0's acceptance; the only record is the `B0_REVIEWED_AUTHORITY`
constant in `b1.py` (`CLEAN`, 33 files, 12,807,274 bytes, commit `888bd9f50`). The B1 result
document must state that B0's acceptance rests on that constant and on the rehash at launch.

### E.3 Launch when released

One process, 12 arm-seeds sequential, `torch.set_num_threads(1)`, the runner's own admission
before each of the 36 child invocations; expected 0.5–3 h (no measured B0 timing exists because
the artifact is unreadable). Concurrency: E1 holds the two 4-thread slots of §7 decision 3; a
third, single-thread process is put to the owner in E.4 rather than assumed.

### E.4 Decisions this intake produces

1. Restore read access to the B0 artifact directory (owner, elevated rights); until then B1 is
   held.
2. Whether B1 may run now as a third, single-thread process beside E1's two 4-thread runs, or
   waits for E1 to finish. **Owner decision (2026-09-02): once the directory is restored, B1
   runs immediately as a third single-thread process**, recorded as a one-off deviation from
   §7 decision 3 of the advancement plan (16 logical cores; 4 + 4 + 1 threads). The owner
   reported the directory restored on 2026-09-02; at 02:25 PDT 2026-09-03 the reviewer's
   PowerShell still gets `Access to the path … is denied` on `Get-ChildItem` and `Get-Acl`, so
   the restore did not take and B1 stays held.
