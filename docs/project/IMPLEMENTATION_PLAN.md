# HA-CTSE Active Implementation Plan

Updated: 2026-07-23
Status: `COMPLETE_VALID_TYPED_SMOKE`
Work ID: `cpu-natural-branch-typed-contract-20260723`
Source boundary: branch `Claude`, `b0e65cebde2f6ce8170672922c8163ee98dddf6c`

## Authority

Scientific source: `docs/external-review/rounds/20260723_cpu_natural_branch_typed_contract_resume/21_PRO_OPEN_RAW.md`, bound to evidence commit `6e47623bd534cfad88f2f5481e98eadec6e64991`.

Controller adoption: `50_DISPOSITION.md`. The Controller/main conversation authored and froze this executable plan after comparing implementation approaches; local agents only execute its bounded tasks. The user's active autonomous grant authorizes one clean typed implementation, focused correctness checks, one collective final Reviewer+Verifier gate over the complete stable code package and exactly one unchanged non-formal registered-CPU `formal_path_exercise`. There is no per-task or per-debug-attempt review. Formal training, evaluation, analysis and use of the formal authorization token are prohibited.

The implementation changes measurement and evidence classification only. It does not change the task, reward, observations, model, policy factorization, gradients, optimizer, seed, budget, threshold, treatment, primary estimand `G`, three arms or branch precedence for complete evidence.

Terminal result: the one authorized non-formal registered-CPU smoke exited 0
after 12m34s and produced `FORMAL_PATH_EXERCISE_COMPLETE` with a complete typed
audit over 64/64 selected rows. This closes the implementation plan; no second
smoke or formal execution is authorized here.

## Outcome

Replace the heterogeneous scalar natural-branch classifier with one shared typed contract that:

1. proves source-natural binding before interpreting comparisons;
2. separates exact causal identity from derived-record fidelity;
3. records the event, mark and primitive sampler values actually executed;
4. returns either `complete`, narrowly `unavailable`, or `INVALID_OPERATIONAL`;
5. quarantines all C evidence when fork capability is validly unavailable;
6. removes `natural_errors`, the natural-audit `continuous_error` key and every scalar caller without an adapter.

The first valid typed real-path terminal record ends the scheduled action.

## Write scope

Only these implementation files are authorized:

- `ha_ctse_process/event_held_commitment_link.py`
- `ha_ctse_process/dynamic_roster_direct.py`
- `ha_ctse_process/noncalendar_commitment_testbed.py`
- `scripts/run_noncalendar_commitment_benchmark_g0.py`
- `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`

Project control, CDC records and review artifacts remain Controller-owned. Local agents do not use Git.

## Frozen typed contract

### Field partition

Exact structural/discrete fields:

`actions`, `active_mask`, `orders`, `terminal`, `event_kind`, `event_categorical_actions`, `event_cat_mask`, `event_mark_mask`, `q_before`, `membership_epoch`, `segment_id`.

Exact causal float/state/payload fields:

`observations`, `rewards`, `hidden_before`, `hidden_after`, `prefix_counts`, `primitive_z`, `event_inputs`, `event_u`, `event_z_pre`, `event_new_z`, `candidate_u`, `candidate_z`.

Derived-only fields:

`old_values`, `old_log_probs`, `event_old_cat_logp`, `event_old_mark_component_logp`, `event_old_joint_logp`.

A causal tensor comparison requires identical native dtype, shape and bytes, including the sign bit of zero, and every float leaf must be finite. Record the first failing field/coordinate plus magnitude and ULP diagnostics, but use no tolerance or ULP admission rule. Ordered segment records and complete `TrackingOutcome`/reward traces remain exact.

The unrelated `compare_continuations()["continuous_error"]` checkpoint/state-restoration metric remains. Only the natural-audit key and scalar acceptance role are deleted.

### Executed sampler evidence

Capture only when causal-audit evidence is requested; ordinary training/replay must not allocate trace payloads.

Each event call records contemporaneously:

- call site, monotonically assigned collection call ID, packed width and row;
- scientific row coordinate and input/parameter digests;
- event logits/probabilities as diagnostics;
- the exact two-entry CDF, converted uniform and selected categorical action before overwrite;
- final installed action;
- mark `mu`, `sigma`, noise/epsilon, `u`, `tanh(u)` and candidate mark.

Each active primitive autoregressive decision records:

- continuation time, lifecycle/focal key and autoregressive position;
- call site, call ID, packed width, row, input and parameter digests;
- exact three-entry CDF, converted uniform and selected action;
- logits/probabilities as diagnostics.

`DirectPrimitiveARPolicy.forward_step` receives an optional audit capture path. When absent it returns no extra tensors or records and keeps the normal runtime path unchanged.

The original source trajectory and the natural branch both retain executed evidence. The focal natural event is not exempt: pair the source call with the natural branch's pre-force sampled call and separately require the final installed action to equal the original natural action. A forced overwrite never substitutes for the pre-force kernel gate.

### Bijective binding

Every source-natural pair carries and validator-rederives:

- contract version, `audit_id`, replicate, batch, source episode, focal time, source environment, lifecycle key, membership epoch, segment ID, natural action, natural branch, continuation offset and primitive position/focal key when applicable;
- sampler family, call site, per-collection call ID, packed width, row, input digest, parameter digest and CDF/uniform/noise payload digest on each side;
- one pair digest committing to both complete identities.

Require exactly one source and one natural record for every expected event/mark/primitive decision, identical ordered scientific coordinates, and no missing, duplicate or extra calls. Width is evidence, never a grouping heuristic. The evidence-bearing real path must show the registered width 16 from both actual bound calls.

Existing raw-trace origin, donor, RNG schedule, stream-position, consumption and end-state validators remain necessary. Add realized variates and call positions to the pair evidence. A shared generator state or same input observed elsewhere is not pair proof.

### Derived-record fidelity

Use the existing shared replay report and validator; do not copy constants or create a fork tolerance. Preserve component mixed bounds, ratio cap, support/detach checks, state absolute rule, joint compositional/reduction/assembly evidence and ULP diagnostics.

The typed natural audit records the stored/reconstructed derived report and recomputes:

`derived_record_fidelity_passed = critic_record_valid and likelihood_components_valid and joint_record_valid`.

A derived-validator failure is always `INVALID_OPERATIONAL`, never causal mismatch or partial availability.

### Shared validator and statuses

Replace `_audit_row_errors` and the scalar acceptance role of `_AUDIT_CONTINUOUS_FIELDS` with one typed continuation validator used by the batched natural branch and sequential support paths.

The v2 record exposes evidence from which validators recompute:

`causal_identity_passed = binding_passed and structural_exact and causal_float_exact and segment_exact and outcome_exact and rng_exact and event_kernel_exact and mark_kernel_exact and primitive_kernel_exact`.

Serialized verdict booleans are summaries, not authority.

Admissible terminal classes:

- `complete`: every operational, causal, kernel and derived check passes.
- `unavailable`: binding, instrumentation, donor, schema, RNG, discrete, segment, outcome and derived checks pass, and the only failure is an exact causal float/payload or executed CDF/uniform comparison. Record the first failure and attempted/completed row counts; stop causal auditing and quarantine every C row.
- `INVALID_OPERATIONAL`: every other failure, including nonfinite values, malformed or incomplete evidence, missing/duplicate calls, action mismatch, binding/RNG/donor/schema error, outcome/segment mismatch or derived failure.

Sequential helpers are non-evidence oracles. They must stop using the scalar classifier and share typed field/derived checks, but cannot fabricate registered-width or call-binding evidence.

## Runner and artifact cutover

Use no compatibility reader. Increment exactly:

- causal audit `event_held_commitment_link_g0.causal_audit.v1` to `.v2`;
- `EVALUATION_CELL_SCHEMA` 8 to 9;
- formal evaluation cell `.formal_evaluation.v8` to `.v9`;
- exercise evaluation cell `.formal_path_exercise.evaluation.v6` to `.v7`;
- `EVALUATION_MANIFEST_SCHEMA` 5 to 6;
- formal evaluation manifest `.v5` to `.v6`;
- exercise evaluation manifest `.v4` to `.v5`;
- formal analysis artifact `.formal_analysis.v5` to `.v6`;
- exercise terminal manifest `.manifest.v3` to `.v4`.

Update `registered_contract()["evidence_streaming"]`. Training schemas, checkpoints and operational-failure schema remain unchanged; old embedded contracts fail strict equality naturally.

Replace every `natural_errors` serializer/validator with the v2 typed record. Complete evidence continues through `select_result_branch` unchanged.

For valid unavailable evidence:

- evaluation cell status is `COMPLETE_PARTIAL_EVIDENCE` and `causal_audit.status` is `unavailable` with reason `natural_branch_causal_identity_failed`;
- evaluation root and exercise terminal preserve valid natural evidence and report branch `FORK_EVIDENCE_UNAVAILABLE`;
- analysis creates no zero C values, confidence intervals or causal counts and never calls `select_result_branch`;
- no already-computed C row enters bootstrap or summary selection.

Operational invalidity keeps the existing fail-closed publication path.

## Implementation graph

The Controller/main conversation owns the full implementation graph and every
interface decision. It compared the viable decompositions, froze the two write
scopes below and supplied exact assignments; children only execute them:

1. Core scope: `event_held_commitment_link.py` and
   `dynamic_roster_direct.py` — optional executed-call capture, typed
   field/kernel/binding/RNG evidence, shared validator, batched and sequential
   cutover.
2. Runner scope: `noncalendar_commitment_testbed.py`, the runner and focused
   test file — v2 serialization/revalidation, schema increments, unavailable
   propagation/analyzer bypass and focused tests.

The Controller integrates all tasks and bounded repairs first. Exactly one
parallel Reviewer+Verifier collective gate then evaluates the complete stable
package; there is no per-task or per-debug-attempt review.

## Controller-owned collective-review repair plan

The one collective review gate returned two implementation defects inside the
accepted scientific contract: unavailable artifacts omit non-contrast
provenance, and natural action does not bijectively constrain the natural branch
label. These are `CODE_ENGINEERING`; they do not change evidence meaning and do
not require Pro clarification.

The Controller compared three implementation approaches:

1. Duplicate the complete-row checks in the unavailable branch. Rejected:
   validation logic would drift across two status-specific copies.
2. Build and validate one common non-contrast provenance projection for every
   attempted row, then add outcomes/contrasts only for complete artifacts.
   **Selected:** one deep private seam preserves quarantine and makes operational
   prerequisites status-independent.
3. Serialize all branch outcomes and contrasts for unavailable rows and ignore
   them downstream. Rejected: this violates C-evidence quarantine.

### Repair task 1 — natural action/branch bijection

Files: `ha_ctse_process/event_held_commitment_link.py`,
`scripts/run_noncalendar_commitment_benchmark_g0.py`, and the focused test file.

The only legal mapping is `KEEP -> KEEP_HELD_MARK` and
`RENEW -> RENEW_CANDIDATE_MARK`. Enforce it in
`validate_typed_natural_audit`, `_typed_binding_matches_causal_row`, and the live
engine-result-to-outer-row check. The top-level engine label, nested binding
label and outer natural action must agree before publication. A legal but wrong
`RENEW_DERANGED_MARK` label must fail even after dependent pair digests are
recomputed.

Red/green checks: one fixture-light nested-record mutation and one runner
outer-result mismatch, both failing before outcome or contrast interpretation;
the clean KEEP and RENEW records remain valid.

### Repair task 2 — unavailable non-contrast provenance

Files: `scripts/run_noncalendar_commitment_benchmark_g0.py` and the focused test
file.

Before status projection, construct for every attempted row the cyclic donor
record, selected payload binding, executed branch evidence, all-branch RNG
bindings, stream consumption and end-RNG digests. Validate the same common
provenance seam for both `complete` and `unavailable` artifacts. An unavailable
row persists those fields plus natural outcome/audit, but omits branch outcomes,
contrasts, additivity, C values, intervals and selector inputs. Any donor,
executed-payload, branch-label, RNG schedule/consumption or end-state mutation
must be `INVALID_OPERATIONAL`, never `FORK_EVIDENCE_UNAVAILABLE`.

Red/green checks: a fixture-light unavailable row with complete common
provenance validates; removing or mutating each provenance class fails; forbidden
outcome/contrast keys fail exact schema; existing complete rows and unavailable
analysis quarantine remain valid.

The Controller verifies both repairs with the fast recurrences, all typed
classes and workflow contracts. Because these repairs enforce rather than
change the frozen semantics, no second collective review is scheduled; a second
review would be required only if implementation proves that the frozen
provenance contract itself must change.

## Focused tests

Delete or replace scalar fixtures and assertions. Retain existing raw-trace, donor, RNG, full-outcome and replay validators. Keep the checkpoint continuation `continuous_error` test because it is a different contract.

Exactly three typed test classes carry new coverage:

1. Hypothesis discriminator: one-to-four-ULP drift confined to derived mark/joint records leaves causal identity true and is decided only by the frozen derived validator.
2. Key-invariant negative: parameterized one-bit mutations of a causal leaf, event CDF, primitive CDF, compared uniform and pair binding fail the named typed class; no tolerance rescues them.
3. Real recurrence regression: registered-CPU real-path output reaches shared Stage 2 and is either valid typed `complete` or valid structured `unavailable`, never the old scalar `RuntimeError`.

The static active-line check must forbid `natural_errors`, the natural-audit `continuous_error` key and scalar gates without rejecting the unrelated restore metric.

## Verification and stop rule

Before the conclusion-bearing smoke:

- run only the focused typed, replay, raw-trace/donor/RNG/outcome and schema/publication checks;
- inspect the end-to-end path for per-field device synchronization, repeated packing/transfer, ordinary-path trace allocation, recurrent leakage, RNG consumption drift and serial evaluation;
- complete the one collective Reviewer+Verifier gate, then close any findings
  under the Controller-owned repair plan and direct focused verification;

Then run exactly once with the registered interpreter:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_noncalendar_commitment_benchmark_g0.py --mode formal_path_exercise --device cpu --output-root logs/20260723_cpu_natural_branch_typed_contract
```

Do not pass `--authorize-formal`.

A valid smoke must show shared training/evaluation cores, actual Stage-2 selected rows, v2 round-trip, nonempty actual-pair event and primitive CDF/uniform evidence, exact call/coordinate/width binding, exact RNG evidence, a separate derived verdict and no natural-audit scalar field.

Stop at the first valid `complete` or `unavailable` record. If the first run is `INVALID_OPERATIONAL`, repair only the first identified implementation defect under this unchanged plan and run one final bounded check. A second operational failure is a blocker. No alternate seed, tolerance, width, synthetic proxy or second smoke for a preferred conclusion is permitted.
