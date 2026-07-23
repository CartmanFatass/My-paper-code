# CDC ruling — CPU Natural-Branch Typed Contract

**Evidence boundary.** I treated the review request at branch `Claude`, commit `32ac55f19880293ba4d4cae7e8e6e291569f0c38`, as the question only. All repository evidence and implementation facts below are bound exclusively to commit **`6e47623bd534cfad88f2f5481e98eadec6e64991`** and the paths listed in `docs/external-review/rounds/20260723_cpu_natural_branch_typed_contract_resume/01_SHARED_SOURCE_MANIFEST.md`; local files, later changes and aborted-run artifacts are excluded.

## Decision

**Schedule: bounded implementation of the typed natural-branch contract, followed by exactly one non-formal real-path `formal_path_exercise` smoke.**

**Formal training, formal evaluation and formal analysis are not authorized.**

The new `continuous_error=9.5367431640625e-07` observation proves that the production implementation still applies the superseded heterogeneous scalar gate. It does **not** establish that the CPU natural branch violates causal identity, because the scalar does not identify the field, coordinate, operation, source-natural pair or whether the difference occurred before or after the generated decision. The observation is operational prelaunch evidence only, as the canonical question and current project record explicitly state.

---

# 1. Still-legal conjectures

## C1 — Derived-record-only arithmetic drift

**Scope:** the exercised registered-CPU smoke coordinates only; not all CPU executions and not future trained formal coordinates.

**Mechanism:** source and natural branch have exact causal state, intervention payloads, RNG variates and decision-producing CDFs, but one or more post-decision records differ because transformed-density or reduction arithmetic is evaluated under different packed shapes.

**Strongest simpler explanation:** this is currently the most parsimonious explanation, though not yet an accepted finding. The prior real fork was localized to `event_old_mark_component_logp` at four float32 ULPs and its derived `event_old_joint_logp` at one ULP, while discrete decisions, segment identity and outcome identity remained exact. Those fields are calculated after the mark and action have already been selected. The new scalar magnitude alone cannot show that the same fields moved again.

**Consequences**

- **Intervention:** Replacement-C counterfactual outcomes are admissible if the actual source-natural CDFs, uniforms, mark kernel, causal fields, RNG and binding all pass exactly. The likelihood drift is then auxiliary fidelity drift.
- **Natural execution:** the original natural trajectory remains valid, and the reconstructed natural branch may still be the same causal trajectory.
- **Held-out:** a passing typed smoke would establish capability only for the exercised held-out smoke rows. It would not establish held-out utility, G, C, transport or a host-wide theorem.

## C2 — Actual categorical decision-kernel divergence

**Scope:** one or more actual source-natural event or primitive sampler calls in this smoke.

**Mechanism:** the full categorical CDF used for sampling differs bitwise, even though the realized uniform lies in a region that produces the same factual action. The current discrete, segment and outcome fields can therefore remain equal while the fork estimand is still inadmissible.

**Strongest simpler explanation:** a local floating-point evaluation difference at one actual call and value configuration, not a general “CPU cannot fork” property. The earlier instrumentation observed exact event CDFs over hundreds of repeated cross-width rows, but it did not bind those observations to the actual source-natural pair. The primitive sampler was observed only at width 16 and therefore had zero cross-width pair comparisons.

**Consequences**

- **Intervention:** any nonzero event or primitive CDF difference makes the associated counterfactual outcomes inadmissible, regardless of whether the factual action happened to remain unchanged.
- **Natural execution:** the originally collected trajectory can remain valid; the counterfactual reconstruction is the unavailable instrument.
- **Held-out:** fork-independent held-out evidence could remain representable under the partial-evidence contract, but no C interval and no complete G0 selector may be produced.

## C3 — Exact causal-state or intervention-payload drift

**Scope:** one or more fields such as recurrent state, observation, prefix count, installed commitment or retained intervention candidate on this exercised natural continuation.

**Mechanism:** a small numerical difference occurs in a value that either feeds a later decision or defines the intervention being contrasted. It happens not to cross a categorical boundary or alter the terminal outcome on this factual continuation.

**Strongest simpler explanation:** batch/reconstruction arithmetic in the recurrent continuation, rather than any failure of the EHC scientific mechanism. The current continuous tuple mixes these causal values with critic and likelihood records, so its scalar maximum cannot distinguish this conjecture from C1.

**Consequences**

- **Intervention:** fork evidence is unavailable because treatment is no longer the sole permitted difference.
- **Natural execution:** exact factual action and outcome equality are retained observations but are insufficient to rescue causal identity.
- **Held-out:** no inference about the EHC mechanism follows; only an exercised backend/reconstruction capability has failed.

## C4 — Source-natural provenance or pairing defect

**Scope:** the audit evidence-generation path, not necessarily the underlying sampler or trajectory.

**Mechanism:** the purported source and natural observations correspond to different coordinates, call instances, packed rows, widths or parameter/input instances. A scalar field comparison can then report a difference that is neither a valid causal mismatch nor valid derived-fidelity evidence.

**Strongest simpler explanation:** missing production provenance rather than real kernel divergence. The previous review explicitly left exact source-natural coordinate, call and width binding outstanding; repeated global input digests were not sufficient because they did not identify the actual pair being certified.

**Consequences**

- **Intervention:** no counterfactual row is admissible.
- **Natural execution:** no conclusion about natural-branch equality can be drawn from the malformed audit record.
- **Held-out:** this is `INVALID_OPERATIONAL`, not `FORK_EVIDENCE_UNAVAILABLE`; partial degradation is forbidden because the capability measurement itself is not valid.

---

# 2. Smallest refuted and unresolved propositions

## Refuted proposition

Define:

P scalar : max ⁡ f ∈ 17 mixed continuous fields ∥ f natural branch − f source ∥ ∞ > 0 ⟹ causal identity failed .

`P_scalar` is refuted.

The concrete counterexample at evidence commit `6e47623…` is the previously localized fork record:

- `continuous_error = 4.76837158203125e-07`;
- discrete mismatch zero;
- segment and outcome equal;
- the only nonzero fields were `event_old_mark_component_logp`, four ULPs at `[4,1,7]`, and its derived `event_old_joint_logp`, one ULP at `[4,1]`;
- those likelihood records are generated after the decision and do not feed the installed mark, primitive action or environment continuation.

That counterexample does **not** prove complete CPU fork capability, because actual event/primitive kernel evidence and exact pair binding were still incomplete. It is nevertheless sufficient to disprove the scalar maximum as a classifier of causal identity.

The present production implementation still computes precisely that maximum and rejects unless it is zero, while the runner independently accepts a different scalar literal, `<=1e-7`. Both are superseded.

## Proposition left unresolved

P CPU-smoke : Every actual source-natural pair in the new registered-CPU smoke satisfies the typed causal-identity contract.

The new `9.5367431640625e-07` failure leaves this proposition **unresolved**, rather than refuting it. The record provides no field localization, no exact decision-kernel result and no actual-pair provenance.

## Retained lemmas

- **Exact actions and outcomes are necessary but not sufficient.** An arbitrarily small CDF or recurrent-state difference can leave the realized factual action unchanged while invalidating the claim that treatment was the sole difference.
- **Derived records are not causal state.** Once causal state, intervention payloads, RNG and executed decision kernels are exact, bounded post-decision critic or likelihood drift cannot change the generated trajectory.
- **A fixture pass is local.** It licenses only an attempt to measure fork evidence on later actual rows; it is not a theorem about every CPU coordinate, every parameter state or every formal run.
- **Primitive width 16 is not itself proof.** The production primitive sampler is evaluated over the actual batch and autoregressive member positions; its executed CDF and uniform still require pair-bound evidence even when source and natural widths are both 16.
- **Malformed provenance is operational invalidity.** Missing or inconsistent binding, RNG, donor, schema or instrumentation evidence cannot be converted into structured fork unavailability.

---

# 3. Cheapest next scheduled action

## Selected: bounded implementation plus one non-formal real-path smoke

Derivation is no longer the cheapest action: the typed distinction between causal identity and derived-record fidelity has already been derived and accepted. Accepted-evidence reanalysis cannot answer the new question because the production smoke did not emit the missing field, CDF, uniform and actual-pair observations. Another synthetic probe would repeat the already-refuted proxy error.

The smallest discriminating action is therefore to make the actual production path emit and validate the already-specified evidence, then exercise that exact shared path once. This follows the project rule that implementation is selected only when it is the cheapest necessary evidence action, with at most one focused operational check.

The existing `formal_path_exercise` is suitable for that single smoke because it executes one update, one replicate, the shared training core, all evaluation cells and the real batched Stage-2 causal audit at registered width 16. It is explicitly non-formal and the CLI rejects a formal authorization token for that mode.

The action is deliberately narrow:

- no general instrumentation platform;
- no compatibility reader;
- no sampler redesign unless the typed smoke actually identifies a sampler defect;
- no additional seed, width or repeated-smoke search;
- only the typed contract, its validator, its partial-evidence state and minimal tests.

---

# 4. Exact scientific contract

## 4.1 Typed predicates

The production record shall expose two separate recomputable predicates:

causal_identity_passed = binding_passed ∧ structural_exact ∧ causal_float_exact ∧ segment_exact ∧ outcome_exact ∧ rng_exact ∧ event_kernel_exact ∧ mark_kernel_exact ∧ primitive_kernel_exact

and

derived_record_fidelity_passed = critic_record_valid ∧ likelihood_components_valid ∧ joint_record_valid .

Neither predicate may be reconstructed from a global maximum or from a serialized boolean alone. Validators must recompute each verdict from the named evidence.

## 4.2 Causal-identity fields

### Exact structural/discrete fields

Use the current discrete set, with exact dtype, shape and value equality:

- `actions`
- `active_mask`
- `orders`
- `terminal`
- `event_kind`
- `event_categorical_actions`
- `event_cat_mask`
- `event_mark_mask`
- `q_before`
- `membership_epoch`
- `segment_id`

The current implementation already names these fields.

### Exact causal float/state/payload fields

From the current mixed continuous set, causal identity owns:

- `observations`
- `rewards`
- `hidden_before`
- `hidden_after`
- `prefix_counts`
- `primitive_z`
- `event_inputs`
- `event_u`
- `event_z_pre`
- `event_new_z`
- `candidate_u`
- `candidate_z`

`candidate_u` and `candidate_z` remain exact even when discarded by natural KEEP because they define the candidate-mark intervention payload. They are not ordinary likelihood diagnostics.

### Exact non-tensor structure

Require exact equality of:

- trajectory length and source start offset;
- ordered segment sequences, including every segment field;
- the complete outcome record and reward trace, not utility alone;
- ledger and lifecycle identities represented in the binding;
- source-natural RNG schedules, consumption positions, realized variates and end states.

### Equality rule

For causal float leaves:

- same native dtype;
- same shape;
- all leaves finite;
- identical bit patterns in the native dtype.

A numeric `==`, `allclose`, absolute tolerance, relative tolerance or ULP allowance is not the equality rule. ULP distance is recorded only for diagnosis after a failure.

This also avoids treating `+0.0` and `-0.0` as silently interchangeable or letting non-finite values pass threshold comparisons.

## 4.3 Derived-record-fidelity fields

The following are explicitly removed from the causal exact predicate:

| Natural-branch field | Derived class | Validator |
| --- | --- | --- |
| `old_values` | post-decision critic record | existing absolute-only state rule, `REPLAY_STATE_ATOL` |
| `old_log_probs` | primitive selected-action likelihood | existing mixed absolute-relative component rule plus ratio-drift cap |
| `event_old_cat_logp` | event categorical selected-action likelihood | same component rule and support rule |
| `event_old_mark_component_logp` | transformed mark-density components | same component rule and support rule |
| `event_old_joint_logp` | derived categorical-plus-mark joint | existing compositional component-sum, float32 reduction, assembly and ratio validator |

At evidence commit, the frozen replay constants are:

- component absolute term `1e-6`;
- component relative term `8 × 2^-24`;
- log-ratio drift cap `1e-4`;
- state absolute term `1e-6`;
- exact support-leak checks;
- a nine-factor event-joint compositional record rather than a scalar joint tolerance.

The natural audit must call the same shared validator implementation. It must not copy these constants into a second “fork tolerance” implementation.

Every derived field must retain:

- stored and reconstructed values;
- maximum absolute error;
- deciding coordinate;
- mixed bound where applicable;
- ratio drift and cap;
- float32 ULP size and distance;
- for the joint, component sum, reduction allowance, bound, excess, assembly residual, assembly allowance and assembly excess.

A derived-fidelity failure beyond the frozen validator is **not** a causal-identity failure and is **not** the narrowly degradable CPU capability condition. It is `INVALID_OPERATIONAL` for this action.

## 4.4 Event decision-kernel evidence

For every actual source-natural non-CREATE event decision being certified, record contemporaneously from the sampler:

- exact event logits and probability vector as localization diagnostics;
- the complete two-entry CDF actually compared against the uniform;
- the actual uniform tensor after dtype/device conversion;
- the categorical action selected **before any forced-event overwrite**;
- the final installed event action;
- `mu`;
- `sigma`;
- actual mark noise/epsilon;
- realized `u`;
- realized `tanh(u)` /candidate mark.

The exact CDF, uniform and pre-force selected action are gating. Exact logits are useful diagnostic evidence but do not substitute for the executed CDF. This matters because the collector computes the CDF and selected event before subsequently applying the forced branch; checking only the stored post-force action could mask a kernel divergence.

## 4.5 Primitive decision-kernel evidence

For every active sequential primitive decision from the focal opportunity through the end of the natural continuation, record contemporaneously:

- continuation time;
- autoregressive position;
- focal lifecycle key;
- complete three-entry CDF actually used by the sampler;
- actual primitive uniform at that position;
- selected primitive action;
- logits and probability vector as diagnostics;
- source and natural packed width.

The primitive gate is:

source_cdf bits = natural_cdf bits ∧ source_uniform bits = natural_uniform bits ∧ source_action = natural_action .

The source CDF must be captured from the original executed sampler call, not reconstructed later from stored logits or selected log probability. The current primitive actor forms `log_softmax`, exponentiates it, forms `cumsum`, and compares the registered uniform at each autoregressive position; selected log probability alone does not expose the complete decision boundary.

The expected structural observation is that both source and natural primitive calls use registered width 16. That width must be asserted from the actual bound calls; there is no synthetic primitive width sweep.

## 4.6 Exact source-natural coordinate/call/width binding

Each paired kernel observation must carry a bijective binding containing at least:

### Scientific coordinate

- contract version;
- `audit_id`;
- replicate;
- batch index;
- source episode ID;
- focal time;
- source environment index;
- lifecycle key;
- membership epoch;
- segment ID;
- natural action;
- natural branch name;
- continuation offset;
- primitive autoregressive position and focal key when applicable.

### Executed-call identity

For source and natural sides separately:

- sampler family: `event`, `mark` or `primitive`;
- concrete call-site identifier;
- monotonically assigned call ID within the collection;
- packed width;
- row index within the packed call;
- input digest;
- relevant parameter digest;
- CDF/uniform/noise payload digest.

### Binding rule

- exactly one source record and one natural record for every expected decision;
- no missing, duplicate or extra records;
- source and natural decision sequences have the same ordered scientific coordinates;
- the pair digest commits to both sides and all identity fields;
- the validator re-derives the pair digest;
- width is evidence, not a grouping heuristic;
- global “same input observed elsewhere” counters are non-gating diagnostics only.

Any binding failure returns `INVALID_OPERATIONAL`. It must never be translated into “fork unavailable.”

## 4.7 Fail-closed partial-evidence quarantine

There are three admissible terminal classes.

### A. Complete audit

Conditions:

- all bindings, RNG, donor and schemas valid;
- all discrete fields, segments and outcomes exact;
- every causal float/payload field exact;
- all event, mark and primitive kernel checks exact;
- derived-record fidelity passes.

Result:

```text
causal_audit.status = complete
causal_identity_passed = true
derived_record_fidelity_passed = true
```

Counterfactual rows may enter C analysis, subject to all other registered gates.

### B. Narrow fork-capability unavailability

Allowed only when:

- binding, donor, schema, instrumentation and RNG evidence are valid;
- discrete fields, segments and outcomes remain exact;
- natural collection and replay are valid;
- the only failure is a nonzero exact causal-float or executed decision-kernel comparison.

On the first such selected row:

- stop the causal-audit subtask;
- quarantine every already calculated branch contrast from that run;
- retain none of the earlier passing rows for bootstrap analysis;
- record the first failure and all attempted/completed row counts;
- permit fork-independent natural evidence to continue through its own validators.

Artifact semantics:

```text
evaluation.status = COMPLETE_PARTIAL_EVIDENCE causal_audit.status = unavailable causal_audit.reason_code = natural_branch_causal_identity_failed analysis.branch = FORK_EVIDENCE_UNAVAILABLE
```

The unavailable record must include backend, Torch version, thread count, contract version, failed coordinate, per-field evidence, CDF/uniform evidence, binding evidence, RNG evidence and the separate derived-fidelity verdict.

The analyzer must not:

- substitute zero C values;
- construct empty C confidence intervals;
- pass zero causal counts to `select_result_branch`;
- call the existing complete G0 selector;
- report `BENCHMARK_NON_IDENTIFIABLE`;
- retain earlier rows selected by surviving the numerical audit.

This is required because the current evaluator requires a valid causal audit and treats every exception as `INVALID_OPERATIONAL`, while the current analyzer represents invalid operation with zero-filled causal inputs and always calls the complete selector. Neither path can represent valid natural evidence with an unavailable causal instrument.

### C. Invalid operational evidence

Return `INVALID_OPERATIONAL` for:

- binding failure;
- missing or duplicate calls;
- instrumentation errors;
- RNG schedule, consumption or end-state divergence;
- donor mismatch;
- malformed or incomplete schema;
- missing selected rows;
- discrete mismatch;
- segment mismatch;
- outcome mismatch;
- non-finite evidence;
- derived-record validator failure;
- arbitrary exceptions;
- any indication that the original natural collection is itself invalid.

These conditions do not use partial degradation.

## 4.8 Superseded paths and schemas to delete

### Production code

At `ha_ctse_process/event_held_commitment_link.py`:

- delete `_audit_row_errors` as a four-value scalar API;
- delete the heterogeneous `_AUDIT_CONTINUOUS_FIELDS` acceptance role;
- replace it with explicit causal-exact and derived-record field classes;
- delete the `continuous_error` key;
- delete the literal `continuous_error == 0.0` gate in `audit_opportunities_batched`;
- remove the same scalar contract from the sequential audit path or route that oracle through the one shared typed validator;
- do not retain an adapter producing legacy `natural_errors`.

At `scripts/run_noncalendar_commitment_benchmark_g0.py`:

- delete the validator’s four-key `natural_errors` schema;
- delete the runner’s independent `continuous_error <= 1e-7`;
- validate the typed record with the same shared contract implementation;
- add the explicit partial-evidence terminal and analyzer bypass;
- leave `select_result_branch` itself unchanged for complete evidence.

### Minimum clean schema cutover

Use a clean break with no compatibility reader:

- causal audit: `event_held_commitment_link_g0.causal_audit.v1` → `.v2`;
- `EVALUATION_CELL_SCHEMA`: `8` → `9`;
- formal evaluation cell: `.formal_evaluation.v8` → `.v9`;
- exercise evaluation cell: `.formal_path_exercise.evaluation.v6` → `.v7`;
- `EVALUATION_MANIFEST_SCHEMA`: `5` → `6`;
- formal evaluation manifest: `.v5` → `.v6`;
- exercise evaluation manifest: `.v4` → `.v5`;
- formal analysis artifact: `.formal_analysis.v5` → `.v6`;
- exercise terminal manifest: `.manifest.v3` → `.v4`.

Update the corresponding `registered_contract()["evidence_streaming"]` values. Do not change training schemas. Do not add checkpoint migration; old checkpoints naturally fail the changed embedded registered-contract equality.

### Tests

Delete or replace every fixture and assertion that serializes or accepts `continuous_error`, including the hard-coded zero dictionary in `test_three_branch_width16_batched_audit_matches_sequential_oracle`. Replace `test_no_active_legacy_or_scalar_audit_cuda_path` with an actual static assertion that production source contains no `continuous_error`, global scalar natural gate or legacy schema.

Retain:

- exact row-stability tests for identical inputs to the identical head evaluator;
- existing replay component, support and joint validators;
- raw-trace, donor, RNG and full-outcome invariants.

Add only three focused tests:

- **Hypothesis discriminator:** an injected one-to-four-ULP drift confined to derived mark/joint records leaves causal identity true and is judged only by the frozen derived validators.
- **Key invariant negative:** one-bit perturbations in a causal field, event CDF, primitive CDF, compared uniform or actual-pair binding fail the correct typed class; no tolerance rescues them.
- **Real recurrence regression:** the registered-CPU `formal_path_exercise` reaches the shared Stage-2 path and emits either a valid complete typed audit or a valid structured-unavailable audit—never the old scalar `RuntimeError`.

Do not restore the dense `F.linear` proxy or add a synthetic width-sweep licensing test. The active-line contract explicitly requires the shortest real discriminator, deletion of superseded paths and only hypothesis, key-invariant or real-regression tests.

---

# 5. Minimum conclusion-bearing evidence and stop condition

## Required observation

Run **one** unchanged non-formal registered-CPU `formal_path_exercise` after the typed implementation and focused review.

A valid smoke must demonstrate:

- entry into the shared training and evaluation cores;
- execution of actual Stage-2 selected rows;
- valid typed schema and validator round-trip;
- nonvacuous actual-pair event CDF/uniform evidence;
- nonvacuous actual-pair primitive CDF/uniform evidence;
- exact source-natural call, coordinate and width binding;
- exact RNG evidence;
- a separate derived-fidelity verdict;
- absence of the scalar gate and `continuous_error` field.

## Conclusion branches

### Typed pass

If every exercised row passes:

> The registered CPU demonstrates typed fork capability for the exercised non-formal fixture coordinates.

Nothing broader follows.

### Typed causal capability failure

If a validly bound row has an exact causal-field or CDF mismatch while the narrow degradation preconditions hold:

> Fork evidence is unavailable for the exercised registered-CPU fixture under the typed contract.

The partial quarantine must itself pass. Do not change tolerance, retry with a different seed or search for a passing coordinate.

### Operationally invalid smoke

If binding, instrumentation, RNG, schema, discrete, segment, outcome or derived fidelity fails:

> No CPU capability conclusion is available; the implementation remains operationally invalid.

Repair only the first identified implementation defect under the identical contract. The first subsequent valid typed record ends the action. A second operational failure after that bounded correction is the stop condition and must be reported as a blocker rather than expanded into more instrumentation or retries.

## Stop rule

The scheduled action stops at the **first valid typed terminal record**, whether `complete` or `unavailable`.

There is:

- no second smoke to obtain a preferred answer;
- no alternate seed;
- no tolerance adjustment;
- no wider synthetic sweep;
- no formal execution within this action.

The code change alone is support work. The valid typed real-path classification is the conclusion-bearing observation.

---

# 6. What this action does not authorize

This ruling does **not** authorize:

- formal training;
- formal evaluation;
- formal analysis;
- use of the formal authorization token;
- a complete EHC G0 result branch;
- any claim about G, V, C, access, natural commitment, lifetime behavior or held-out utility;
- treating the smoke as a scientific result;
- a CPU-wide or CUDA-wide capability theorem;
- changing tolerance, seed, budget, reward, model, optimizer, threshold or estimand;
- feeding partial audit rows into bootstrap analysis;
- invoking `select_result_branch` when fork evidence is unavailable;
- integrating EHC into a larger algorithm;
- building a general instrumentation or compatibility platform.

The project record says no usable formal checkpoint or scientific disposition exists, formal compute still requires an exact Controller-authorized run, and the current resume point permits review, derivation, evidence reanalysis and local code work but not a formal run.

## Parked legal directions and reactivation conditions

- **Accepted-evidence reanalysis:** reactivate only after a typed record exists and an old raw artifact contains enough source-bound evidence to be classified without inventing missing calls.
- **Sampler-local numerical correction:** reactivate only if the typed smoke identifies an actual event or primitive CDF mismatch. The correction must preserve the frozen sampler and estimand, not add a general numerical layer.
- **Partial-only formal research route:** reactivate only if the typed smoke returns `FORK_EVIDENCE_UNAVAILABLE`, the fork-independent claims remain scientifically worthwhile, and a new partial-result preregistration receives separate explicit formal authorization.
- **Complete formal G0 route:** reactivate only after a typed smoke pass, implementation acceptance, restored execution controls and a separate formal-run decision. A smoke pass is not that decision.

---

# 7. 中文用户简报

**裁决：实施最小的 typed natural-branch contract，并只运行一次非正式真实路径 smoke；禁止正式训练、正式评估和正式分析。** 当前 `9.5367431640625e-07` 只证明旧的混合字段 scalar gate 仍在误判，不能证明 CPU fork 已失效。因果状态、干预载荷、实际 event/primitive CDF、均匀数、RNG 和 source-natural 调用绑定必须逐项位级相等；critic 与 likelihood 派生记录继续使用既有 replay validator。若 smoke 的合法绑定因果项失败，则隔离全部 C 证据并仅保留经验证的自然证据；若 binding、RNG、schema、离散状态、segment 或 outcome 失败，则仍判 `INVALID_OPERATIONAL`。
