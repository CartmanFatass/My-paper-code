# GPT-5.6 Pro raw response — follow-up (localization + decision kernel)

Conversation `6a60edf9-2a58-83e8-ae93-caffa5092163`, second turn. Received
2026-07-22. Model badge: Pro. Reported reasoning time: 9m 13s.

**Capture method, disclosed.** Extracted with the browser `get_page_text` tool.
Bold, table borders and code-fence markers are the renderer's; wording,
ordering and content are verbatim and unedited.

---

Ruling: the observed mismatch is benign Case B, but full fork capability is not yet established

Your localization changes the disposition materially.

The two nonzero fields are both auxiliary likelihood records. They do not feed the sampled event, installed mark, recurrent state, primitive action, environment transition, or terminal outcome. In the collector, the mark components are calculated from u, mu, and sigma; candidate_z, event_new_z, and primitive_z are constructed independently of those likelihood values; the component and joint likelihoods are then only stored.

Therefore:

The event_old_mark_component_logp and event_old_joint_logp differences do not invalidate the counterfactual outcomes.

However, I do not yet confirm the stronger statement that causal_identity_passed is fully established, because the instrumentation stops one operation before both categorical sampling kernels.

## 1. Case B classification

### Confirmed: the two measured discrepancies are derived-record-only

The evidence is strong and internally coherent:

every structural, recurrent, intervention, and realized-sample field is bitwise identical;

all discrete decisions are identical;

segment and outcome equality hold;

the event-head logits and the mark parameters mu and sigma are bitwise identical for repeated identical queries;

event_u, candidate_u, candidate_z, event_new_z, and primitive_z are bitwise identical;

only the transformed mark density and its derived joint differ.

That is exactly the benign half of Case B. The four-ULP mark-component difference is a post-decision arithmetic difference. The one-ULP joint difference is its downstream reduction/assembly consequence.

### Not yet confirmed: the complete event categorical kernel

_row_stable_event_heads is not the whole stochastic event decision kernel. It emits logits and mark_output. The collector subsequently computes:

```python
softmax(logits) -> cumulative CDF -> comparison with event_uniform
```

to select KEEP versus RENEW. It separately computes log_softmax(logits) to store event_old_cat_logp.

Consequently, exact logits do not by themselves establish exact executed binary32 CDF arithmetic at different packed widths. Nor does exact selected categorical log probability establish the other probability or the threshold actually compared against the uniform.

This is the same distinction your density measurement just demonstrated: identical mathematical inputs can still produce a width-dependent result in a later floating-point operation.

So my precise answer is:

Yes, the observed mark-component and joint discrepancies are benign. No, Measurement 2 as currently defined does not yet prove the entire decision kernel is exact.

### Numerical correction

The mixed mark-component bound is slightly larger than the number in your message. The frozen rule is

10^-6 + (8 * 2^-24) max(|x|, |y|).

At magnitude 0.2560406625, that is approximately:

1.1220897e-6,

not 1.0000122e-6. The observed 1.1920929e-7 is about 10.6% of that bound, so the correction strengthens rather than weakens the pass. The implementation uses exactly this mixed formula.

For the joint, retain the existing full compositional validation. A joint does not pass merely because 4.768e-7 is below a quoted scalar. Its record must show:

component sum;

reduction allowance;

joint excess;

stored and replayed assembly residuals and allowances;

assembly excess;

ratio drift.

That is the frozen joint contract. Treat the stated 3.02e-6 as established when it is emitted by that shared validator, not by a separate hand calculation.

## 2. Remaining measurements required before crediting this AMD host

### Direct primitive-kernel instrumentation: required

The primitive collector computes complete categorical probabilities and their cumulative distribution, then compares the registered uniform against that CDF. old_log_probs contains only the log probability of the action that happened to be selected.

Exact action plus exact selected log probability does not prove exact full distribution. For example, nonselected probabilities could move without changing the selected scalar or crossing the realized uniform on this factual path.

The formal audit should therefore compare, source versus natural branch, at every active sequential primitive decision:

the complete categorical CDF actually used by the sampler, exactly;

the realized primitive uniform, exactly;

preferably the probability vector and logits as diagnostic evidence.

The CDF is the causal gate. Logits are useful localization evidence but are not a substitute for the executed sampling threshold.

### Event categorical CDF instrumentation: also required

Add the same exact comparison for the event sampler:

complete KEEP/RENEW CDF;

realized event uniform;

selected action.

Your exact logits measurement remains valuable, and exact mu, sigma, mark noise, and realized event_u are sufficient for the continuous mark-sampling side. But the categorical softmax/CDF step still needs direct coverage.

### Binding to the actual source-natural pair: required

The 203 cross-width repeated keys make the measurement nonvacuous, but they do not identify whether the relevant natural-branch queries were among those cross-width pairs.

Do not add another synthetic sweep. Instead, make the production audit self-binding:

source trajectory coordinate;

natural-branch coordinate;

source call identifier and packed width;

natural call identifier and packed width;

exact input/parameter digest;

exact CDF, mu, and sigma comparison;

associated realized uniform or noise.

For the present mismatch, the record should explicitly bind the source and natural evaluations corresponding to:

joint coordinate [4, 1];

component coordinate [4, 1, 7].

This is largely provenance for the measurement you have already performed, rather than a new numerical hypothesis.

### Result after those checks

Once the actual-pair event CDF and full primitive CDF comparisons are exact:

The fixture demonstrates valid fork capability on this AMD host under the corrected typed contract.

It still does not establish a permanent host-wide theorem that all future trained coordinates will pass.

## 3. Revised prelaunch correction list

Your reading is mostly right.

### Unchanged and still required

Items 1, 3, 4, 5, 6, and 7 remain required:

versioned per-field localization with values, coordinates, and ULP evidence;

separate causal_identity and derived_record_fidelity;

one shared engine/validator contract, eliminating both the global zero scalar and runner 1e-7;

removal of dense_batch_invariant as a licensing proxy;

structured partial-evidence degradation;

alignment of the replay test with the frozen replay contract.

The current engine collapses the 17 continuous fields to one maximum and then rejects any nonzero value. The runner separately accepts a literal 1e-7, so those contracts still have to be unified.

### Item 2 becomes the production form of the measurements

Yes, but broaden it from "head outputs" to the actual executed sampling kernels:

event categorical CDF and uniform;

event mark mu, sigma, noise, and realized u;

primitive categorical CDF and uniform;

exact coordinate-bound source-natural matching.

The wrapper you used is a good prototype. The permanent implementation should emit structured audit evidence rather than global digest counters.

### Item 8 requires a more careful rewrite

P1 should be closed as stale. At this commit, the batched audit reconstructs and branches stochastically, and formal evaluation invokes it on EHC held_out_stochastic.

For P1b:

keep it open until the event-CDF, primitive-CDF, and actual-pair bindings pass;

after they pass, retire the blanket conclusion that "the fork engine cannot run on CPU";

record that the corrected typed contract passes the exercised AMD fixture;

do not convert that into an unconditional assertion that every formal coordinate on this host will pass.

The Intel record should be preserved, but its interpretation changes. Under the corrected contract, an old report of a nonzero event_old_joint_logp is not evidence that Intel CPU could not produce causal fork outcomes. Without equivalent per-field and kernel localization, its proper status is:

historical exact-all-fields mismatch under the superseded audit contract; typed-contract capability undetermined.

It should not remain cited as proof of a CPU-wide prohibition.

## 4. Complete G0 disposition and the partial-evidence machinery

### A fixture pass licenses an attempt, not the final disposition

After the remaining direct kernel checks pass and the implementation corrections are complete, the AMD host may be used to launch a complete-capable G0 run. The run may attempt all registered evidence, including Replacement C.

It does not pre-authorize a complete scientific disposition.

Formal fork capability is established row by row on:

the trained parameters;

the formally selected coordinates;

the realized held-out stochastic trajectories;

the actual packed widths encountered in that run.

The current test uses initialized/test parameters and a bounded coordinate set. Floating-point path equality can depend on actual values as well as shapes. Therefore a test-fixture pass cannot replace the natural audit on every selected formal row.

### Partial-evidence machinery remains required before launch

Yes. It remains necessary even after this host passes the corrected fixture.

The formal evaluation must be able to represent two possible outcomes:

All selected formal rows pass causal identity and derived-record validation.
The complete Replacement-C evidence is admissible, and the ordinary complete G0 selector may run.

Any selected formal row fails causal identity or the decision-kernel contract.
The fork audit becomes unavailable for the run; already computed fork contrasts are quarantined; fork-independent natural evidence remains publishable; the complete G0 selector is prohibited.

A late formal-row failure must not turn the entire natural evaluation into an operational crash, and successful earlier fork rows must not be selectively retained. That is why structured degradation is not merely accommodation for a currently known-bad CPU. It is the fail-closed representation of a row-validated numerical capability.

### Final disposition

At this point:

derived likelihood mismatch: benign and correctly classified;

mark sampling kernel: established for the exercised repeated queries;

event categorical kernel: incomplete until exact CDF comparison;

primitive categorical kernel: incomplete until exact CDF comparison;

actual source-natural width binding: not yet explicit;

AMD fixture fork capability: provisional, not yet credited;

formal G0 launch: not yet authorized from this branch;

complete G0 evidence on CPU: permitted to be attempted once the remaining kernel checks and all prelaunch contract changes are in place.
