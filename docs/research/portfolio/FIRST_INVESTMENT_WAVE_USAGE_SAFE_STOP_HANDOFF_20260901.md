# HMASD first-investment-wave usage-safe-stop handoff — 2026-09-01

This handoff is the restart boundary for the five current first-investment-wave directions:
CBSC, FRRIE, SCDMP, UCOPE, and VNFC. It consolidates the latest checkpoints reported by each
Direction Manager and its EM/CM tree. It does not change any Portfolio lifecycle or priority.

## Codex account usage stop condition

`STOP_USAGE_0` means that the remaining **Codex account usage** shown by the signed-in Codex
account has reached 0%. It does not mean a child context, task token counter, model context window,
or repository budget reached zero.

The dedicated read-only monitor is `/root/mon_ll_codex_usage` (Luna/low). It must use one local
Codex CLI PTY and `/status`; it must not log in, copy credentials, redeem a reset, modify the
repository, or run research. Root acts only on an exact 0% reading or the platform's own account
limit event; it must not infer an account percentage from thread or subagent usage.

First successful host reading: the account weekly limit showed `5% left`, resetting at `12:08 on
7 Sep` as displayed by the CLI. The separate Spark 5-hour and weekly limits both showed `100% left`
and do not override the main account-weekly stop condition.

On `STOP_USAGE_0`:

1. Do not spawn, dispatch, admit, launch, resume, retry, or start another test or experiment.
2. A process already writing an artifact may only reach its existing atomic terminal or quarantine
   boundary. Do not interpret its values or begin another process.
3. Each live DM reports its current facts and stops at the next file-safe boundary. Root does not
   ask it to complete the next planned slice.
4. Root updates this handoff, stages only reviewed direction-owned paths and this file, commits, and
   immediately pushes the checked-out branch.
5. Restart only after account capacity is available. Re-read this handoff and the cited direction
   authority before sending any follow-up.

At this snapshot no result-bearing process is running.

## Git and workspace boundary

- Integrated and pushed baseline: `5f0e4ef4` on `origin/main`.
- The shared checkout is intentionally dirty with concurrent CBSC and UCOPE implementation work
  and unrelated control-plane edits. Preserve all of it.
- The two VNFC science cards reported as modified are line-ending noise and are not part of the
  current VNFC work.
- Never integrate the isolated VNFC R01 diagnostic worktree.

## Direction summary

| Direction | Scientific state | Engineering state | Exact next boundary |
| --- | --- | --- | --- |
| CBSC | No B1 observation; B0 is instrumentation-only and nonpolar | B1 15-table production assembly is incomplete and uncommitted | Finish current bounded fixes, full non-result regression, reviewer, then one TEST_ONLY E2E |
| FRRIE | No B01 algorithm observation; object unconsumed | FP32 primitive derivation repair is CLEAN and pushed; production remains `REPAIR_REQUIRED` | Full512 Slice A non-effecting contract/tests only |
| SCDMP | No valid replacement result; old RUN is technical incomplete evidence | Orchestration/telemetry is CLEAN and pushed | Obtain one lawful replacement-identity decision before A-R2 or RUN |
| UCOPE | Valid B1: all arms `0/3` competent; acquisition unassessed | Odd/even read-only audit implementation remains reviewer NON-CLEAN | Close four binding/telemetry tamper boundaries, reviewer CLEAN, then Root decides audit launch |
| VNFC | R01 object closed and revised; direction remains open | R02 A0 finite physical-action law is still being frozen | Root reviews exactly one law freeze before any CM implementation |

## CBSC — capability-bound semantic currentness

### Scientific state

- Direction remains `ACTIVE / HIGH` on the current Portfolio snapshot.
- B0 r02 is complete and clean but absolutely nonpolar.
- The `.03` Pro decision is `METRICS_ONLY_CONVERGENCE_CLASSIFIES`, response SHA prefix
  `7a3bd74e`.
- B1 must publish lossless raw facts, mechanical conformance, and RAW competence. AUC, aggregate
  diagnostics, branch, polarity, promotion, and B2 trigger remain literal null.
- No B1 run or new scientific observation exists. LR01 remains `UNRESOLVED`.

### Engineering state

- Pre-`.03` foundation: `241 passed`; TOCTOU panel: `27 passed`.
- Implemented surfaces include contract, resume, admission, supervisor and incident chain, source
  and B0 authority, 1,344 unique tapes / 204,288 transitions, 48 checkpoints / 73,728 policy rows /
  768 curves, training and optimizer records, mechanical/RAW competence, the 15-table artifact,
  and 12 admitted replay workers.
- Formal production gate remains `FALSE / REPAIR_REQUIRED`.
- The latest bounded E2E reached 15-table preparation and stopped on mixed-type support canonical
  ordering. A localized sort fix exists, but no passing whole E2E or final reviewer verdict exists.
- Active work is code/tests only; no B0/B1/B2 or result process is running.

### Uncommitted scope

Direction-owned modified paths:

- `docs/research/candidates/capability_bound_semantic_currentness/DIRECTION.md`
- `docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md`
- `docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_LITERAL_BINDING_SPEC.md`
- `docs/research/candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_INNOVATOR_INTAKE_20260901.md`
- `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/ppo.py`

New scope comprises the metrics-only convergence spec, `b1*.py` implementation modules,
`scripts/run_cbsc_omrc_b01_b1.py`, and the matching `test_b1*.py` suite under the CBSC test package.
These paths are not commit-ready until the running fixes, full regression, final reviewer, and one
non-result TEST_ONLY E2E are clean.

### Resume rule

Let only the already-started bounded fixes reach terminal. Then run one full non-result CBSC
regression and final independent review. If clean, run one bounded TEST_ONLY E2E to close canonical
assembly. Do not run B1, rerun B0, start B2, interpret B0 values, or trigger Convergence.

Authority: [`CBSC DIRECTION`](../candidates/capability_bound_semantic_currentness/DIRECTION.md) and
[`B1 implementation contract`](../candidates/capability_bound_semantic_currentness/CBSC_OMRC_B01_CM_IMPLEMENTATION_CONTRACT.md).

## FRRIE — finite-resource relational inductive efficiency

### Scientific state

- No new valid algorithm observation exists; B01 is unconsumed and Convergence has not fired.
- The claim ceiling remains a fixed 3/5-seed, finite-budget PHY_TRUST versus containing EDGE_FLEX
  projection/optimizer-package signal or counterexample.

### Engineering state

- The `_03` TEST-only artifact was correctly quarantined and no value was read. Its defect was a
  duplicated FP64 validator ratio against the ABI/producer FP32 waste value.
- One authoritative `derive_native_primitive_endpoint` now derives and verifies the FP32 primitive
  and endpoint for producer and validator.
- Verification: `94 passed, 3 actual-native deselected`; independent focused review `1 passed` and
  `CLEAN`.
- Commit `5f0e4ef4` is integrated and pushed.
- Production remains `REPAIR_REQUIRED`, `launch_capable=false`; the sole gate is
  `FULL_PANEL_RUNNER_AND_FULL_CHAIN_TELEMETRY_INCOMPLETE`.

### Resume rule

Proceed only with full512 Slice A: non-effecting formal plan/source gate and worker-local fresh
admission contract plus tests. Keep `launch_capable=false`. Do not create roots, RNGs, models, or
optimizers; do not run `_04`, actual native execution, seeds, production, or any result-bearing
command; do not read or reuse quarantined values.

Authority: [`FRRIE DIRECTION`](../candidates/finite_resource_relational_inductive_efficiency/DIRECTION.md),
[`engineering milestone`](../candidates/finite_resource_relational_inductive_efficiency/FRRIE_B01_CM_ENGINEERING_MILESTONE_20260901.md),
and [`production plan`](../candidates/finite_resource_relational_inductive_efficiency/FRRIE_B01_PRODUCTION_CHAIN_ENGINEERING_PLAN_20260901.md).

## SCDMP — semigroup-consistent duration-model policy

### Scientific state

- No valid new result exists. The old RUN ended in `telemetry_measurement_failed`, is quarantined,
  has no scientific polarity, and did not consume the object.
- Its q/master cannot be read or salvaged, while the frozen science card also forbids silently
  redrawing the identity. There is therefore no unique lawful replacement attempt yet.

### Engineering state

- Telemetry traversal, atomic-write race handling, stable tree identity, and create-once
  artifact-bound performance readiness are implemented.
- Verification: full SCDMP package `514 passed`; focused `91 passed`; independent reviewer `CLEAN`.
- Commit `92a3b7c2` is integrated and pushed.
- The Innovator replacement-law packet exists at
  `temp/pro-research-packets/scdmp-em-innovator-replacement-law-20260901-03/`, but dispatch was not
  accepted. No Pro replacement decision formed.

### Resume rule

Resolve exactly one replacement identity law through the existing Innovator node. Only then may a
fresh 4 GiB A-R2 be created, reviewed, and used to form performance readiness before any replacement
RUN. Do not run A-R2 or RUN, inspect quarantined q/master/outcomes, redraw silently, resume, or
salvage the old attempt.

Authority: [`SCDMP DIRECTION`](../candidates/semigroup_consistent_duration_model_policy/DIRECTION.md)
and [`B01 science card`](../candidates/semigroup_consistent_duration_model_policy/SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md).

## UCOPE — uncertainty-conditioned observation and paid evidence

### Scientific state

- The valid B1 result contains 122,880 episodes, 614,400 transitions, 8,640 optimizer updates,
  18 policies, and 72 checkpoints.
- Every arm is `0/3` competent. Acquisition was not assessed; COUNT and RAW remain locked.
- Convergence Pro decided `CONTINUE` and retired an unchanged B1 repeat.
- The only current object is the read-only odd-training-support versus even-heldout competence
  A/RECON audit. It has not run; no odd score has been read.

### Engineering state

- The prospective contract and B1/convergence evidence are committed.
- Three untracked implementation paths are in scope:
  - `experiments/candidates/ucope/competence_first_scout_r01/support_audit.py`
  - `scripts/run_ucope_b1_odd_support_audit_r01.py`
  - `tests/experiments/candidates/ucope/competence_first_scout_r01/test_support_audit.py`
- Reviewer remains `NON-CLEAN`. The remaining boundaries are deep top/row checkpoint binding,
  final visible receipt immutability, embedded admission/telemetry schema and ranges, and the exact
  prospective read-I/O envelope after provenance rereads.
- No result-bearing audit process is running.

### Resume rule

Finish the exact I/O envelope, rerun the four tamper reproductions, focused/full tests, and the same
reviewer. Only a `CLEAN` verdict may return an audit CLI to Root. Do not run the real audit, read odd
scores, access old B1 attempts, train, create environments/optimizers/checkpoints, select policies,
assess acquisition, or unlock COUNT/RAW.

Authority: [`UCOPE DIRECTION`](../candidates/ucope/DIRECTION.md),
[`B1 evidence`](../candidates/ucope/UCOPE_COMPETENCE_FIRST_SCOUT_R01_B1_RESULT_EVIDENCE_20260901.md),
and [`odd/even audit contract`](../candidates/ucope/UCOPE_A_RECON_B1_ODD_SUPPORT_VS_EVEN_HELDOUT_COMPETENCE_AUDIT_R01_PROSPECTIVE_CONTRACT_20260901.md).

## VNFC — variable-N fleet churn

### Scientific state

- Pro final for R01 is `CLOSE_AND_REVISE_R01`. The only DEBUG was incomplete/non-consuming and has
  no algorithm-return polarity. The direction remains open; commit `c5f689b7` is authoritative.
- The sole successor is `VNFC-BPCR-R02-FINITE-PHYSICAL-ACTION-LAW-A0`, A/RECON and non-result.
- A fixed EM with critic, innovator, and MARL-principles children is freezing exactly one finite
  physical-action law. The freeze is not complete, so no R02 CM/A0 work has begun.
- The claim ceiling is finite registered-panel conformance and, if A0 passes, permission to request
  one fresh R02 DEBUG. It is not performance, learnability, return, or general invariance.

### Required law surface

The one law must bind canonical physical ordering; CPU float64 finite forward and reductions;
deterministic tie/null/prefix behavior; physical categorical/CDF sampling with a fresh RNG
coordinate; collection, forced-logprob, entropy, gradient, and optimizer semantics; zero-residual
MAPR-to-DIRECT containment; and an address-resolved conformance panel.

There is no intentional VNFC R02 dirty path in the shared checkout. The isolated R01 diagnostic
WIP and the two line-ending-only science-card modifications are excluded from integration.

### Resume rule

Wait for the EM's single exact law/object freeze and audit it at Root before assigning non-result A0
implementation to CM. Do not rerun, repair, resume, or inspect R01; do not repeat Pro/Transport; do
not edit R02 code before the freeze; do not run R02 DEBUG before valid A0, and do not run PRIMARY or
OPTIONAL. Every later result-bearing command still requires a fresh >=4 GiB admission receipt.

Authority: [`VNFC DIRECTION`](../candidates/variable_n_fleet_churn/DIRECTION.md) and
[`R01 close / R02 intake`](../candidates/variable_n_fleet_churn/VNFC_BPCR_R01_CLOSE_R02_FINITE_ACTION_LAW_INNOVATOR_INTAKE_20260901.md).

## Restart order

Capacity is not capped. Resume all safe non-result work in parallel, but use this decision-latency
order for Root attention:

1. UCOPE audit implementation to reviewer CLEAN, then one read-only audit after fresh admission.
2. VNFC exact R02 A0 law freeze and non-result conformance implementation.
3. SCDMP replacement-identity decision, then fresh A-R2.
4. CBSC canonical 15-table assembly to TEST_ONLY E2E, then B1 readiness.
5. FRRIE full512 production-chain slices, with launch disabled until the complete gate is clean.

Formal lifecycle, priority, fusion, capacity, or new-direction changes still require the persistent
`portfolio:cross_direction` decision node. This handoff makes no such change.
