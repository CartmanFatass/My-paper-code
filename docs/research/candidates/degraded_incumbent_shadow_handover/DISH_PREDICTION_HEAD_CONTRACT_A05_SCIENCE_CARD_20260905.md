Claim: A synthetic call through the existing prediction interfaces can reproduce their logit/probability mapping and the Cholesky head's connection to the formal training-head outputs.
Binding MARL structure: systems / information flow. Multi-agent handover compares role-indexed predictions and service confidence after partial observations; a mismatch in their training and native-input meanings can restrict the available legal action path.

# DISH prediction-head contract A05 — science card

Date: 2026-09-05. Object `DISH-PREDICTION-HEAD-CONTRACT-A05`, **A / RECON**.
Selected at object tier in `DISH_ORIGIN_CERTIFICATE_A04_INTAKE_20260905.md` (`b0699846e`).
This card precedes model construction, autograd or native-helper output for A05.

## 1. Question, alternatives and claim ceiling

A04 located both prediction-disagreement and service-confidence failures at four real
origins, with no legal transfer. The static source map then found a service BCE-with-logits
loss, raw service outputs passed to native probability clipping, and no Cholesky output
in formal `training_heads`. Reproduce those interface facts with synthetic inputs before
classifying a defect or proposing a changed controller.

The comparison is between actual existing function outputs and their explicit same-input
reference/control: selected raw service logits versus their sigmoid link; raw versus
explicitly clipped versus sigmoid-linked input to the same native probability helper;
and the real training-head graph versus a real full-head Cholesky positive control.
No comparator changes the information set or chooses a favourable physical trajectory.
Live alternatives are a probability conversion already present at the actual boundary,
role mapping different from the static reading, native-consumer behaviour different
from the read helper, and a Cholesky connection hidden by the static API inspection.

Ceiling: reproduced synthetic interface and graph-connection facts at the recorded
source, not a calibrated forecast, actual learner-gradient coverage, trained-parameter
displacement, legal-handover competence, native remedy or RETAIN/COPY/SHADOW effect.
This is engineering reconnaissance inside the existing PRO_FINAL CONTINUE family.
It neither invalidates A04 nor rewrites B01/A01/A02/A03. A05 has no consumption state.

No historical checkpoint or trace is read; no B01 master is created; no optimizer is
initialized or stepped; no training rollout, label generation, PPO loss/replay/update,
native reset/prepare/step/episode or source fork occurs. No production model, native
threshold, host definition or probability conversion is repaired in this object.

## 2. Bound existing source and precision

Existing paths, all under
`experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/`, remain byte-identical
to `818b2566d1bac7cafcc71ed0bbb90b8abd1c6b65`:

- `production_training_engine.py`: `ExactPolicyGraph`, including `heads` and `training_heads`;
- `production_recurrent_trainer.py`: `RecurrentRolloutState`, `BatchedRecurrentPolicy.step_rows`;
- `production_backend.py`: existing row dtype and native compile flags;
- `native/rbhr_r06_production_backend.cpp`: unchanged `predictive_q95` helper.

The head/trainer/backend bytes also match original B01 source `e0541d0c`; A03's changed
native endpoint law is present but never exercised here. CM compares these declared
source surfaces before execution; no HEAD-identity or runtime provenance gate is added.

Use CPU PyTorch FP32, one Torch thread, NumPy/native binary64, and existing C++ build
flags including no fast math. One synthetic PyTorch initialization seed is **50511**.
Set it before `BatchedRecurrentPolicy` constructs its one `ExactPolicyGraph`; it is
not a B01 training seed/master. Do not replace library initialization or change weights.
The model remains in the existing constructor's evaluation mode; autograd is enabled
only for the explicitly declared synthetic graph probes. There is no host/device
estimand: this is portable over configured nodes able to run these exact source and
numeric/toolchain requirements; use the declared remote-first route.

## 3. One fixed synthetic policy mapping

Construct `RecurrentRolloutState.fresh("STRUCTURED", width=2)` and
`BatchedRecurrentPolicy(arm="STRUCTURED", checkpoint_bytes=None, state=state)`.
Use the genuine constructor and methods, without monkeypatching model outputs, dummy
policy objects, copied trainer logic, source-string extraction or replacement factories.

One observation has actor shape `[2,4,54]`. Every feature of lane `l`, copy `c` is
the FP32 value `0.01 * (1 + 4*l + c)`. Owners are `[0,1]`, renewal is true for both,
snapshot payload `[2,18]` is zero and snapshot-delivery mask is zero. Initial recurrent
state and Welford state come from the existing fresh constructor, with no updates.
Call `step_rows` once at `global_tick=0`, deterministic true, sampler `None`, normal
recurrent preparation. This is a synthetic function call, not an environment tick.

Afterward, under no-grad, call the genuine `model.service_q(state.hidden)` once.
Record its `[2,4,20]` raw FP32 values, the two returned native-row service vectors,
and the float64-expanded selected raw vectors and FP32 sigmoid references. The expected
standby-shadow copy indices are 3 and 1; owner-active indices 0 and 2 are recorded as
role context, not additional Q inputs or treatment arms. Retain all values/differences.

Record whether each row equals its selected raw vector exactly and whether it matches
the sigmoid reference within absolute 1e-7. A max difference above 1e-6 is a separated
contrast, not a relaxed production comparison. Report both owner cases independently:
raw exact plus separated from sigmoid is `RAW_LOGIT_PASS_THROUGH`; sigmoid match plus
separated from raw is `LINKED_PROBABILITY_MAPPING`; otherwise `OTHER_MAPPING_READOUT`.
The observed mapping does not establish the quality of either prediction vector.

## 4. Real training-head graph and positive control

Reuse the one model. Use an independent FP32 leaf hidden tensor `[2,4,128]`, all 0.125,
with requires-grad true. Call actual `training_heads` once, sum all elements of all
actually returned tensors to one synthetic scalar, and backward once. This scalar is
explicitly not the PPO objective or an auxiliary training loss.

Record actual returned keys; for every named model parameter, its shape, requires-grad,
whether grad is None, and, when present, gradient finiteness and L1 norm. Record the
same connection/finite facts for the synthetic hidden input. A zero gradient value is
not an absent graph path. In particular retain mean, service-Q and Cholesky weight/bias
facts. Static expectation is eight returned heads and 16 connected parameter tensors,
with Cholesky absent; the measurement, not that count, controls the report.

Clear parameter/leaf gradients without an optimizer. Call actual `heads` once on the
same fixed hidden values; sum only `prediction_cholesky` and backward once as positive
control. Record the Cholesky weight/bias and hidden connection/finiteness/L1 values.
Do not run a third graph or change parameters. Record before/after parameter norms,
L2 and relative displacement; expected displacement is exactly zero.

With finite outputs, Cholesky weight/bias absent from the training graph and both
connected with nonzero finite gradients in the positive control yields
`CHOLESKY_OMITTED_FROM_TRAINING_HEAD_GRAPH`. Otherwise report
`OTHER_TRAINING_HEAD_CONNECTION`. This concerns the actual API and this synthetic
scalar only. It cannot measure old B01 mask support, its full learner gradients,
training convergence or indirect changes through the shared encoder/GRU.

## 5. Exact native helper with three synthetic controls

The existing C++ helper is not exported. Add only an A05-specific thin translation
unit that normally includes the existing production `.cpp` and exports a direct call
to `predictive_q95(const double*)`. It must not copy the helper, edit the old source/ABI,
extract/execute source strings, create native state or call an episode/protocol probe.
Compile once with the existing declared flags and load that one measurement library.

Use exactly three 20-entry constant binary64 vectors: all -2, all 0.25, and all 2.
For each, call the same real helper on (1) raw input, (2) explicit clip to
`[1e-6,1-1e-6]`, and (3) componentwise binary64 `1/(1+exp(-x))`. This is nine helper
calls total. Record all three vectors and q95 values per case. These synthetic linked
values are a reference contrast, not an accepted repair or substituted actual prediction.

Raw and clipped q95 equality in all three cases, with at least one raw/linked absolute
difference at least `0.05-1e-12`, yields `NATIVE_CLIP_CONTRAST_REPRODUCED`. Equality of
raw and clip with no such separated linked contrast yields
`NO_DISCRIMINATING_CONSUMER_CONTRAST`. A raw/clip discrepancy yields
`OTHER_NATIVE_CONSUMER_READOUT`. Do not force a desired downstream effect or compute
any native service/transfer counterfactual from these helper outputs.

## 6. Complete reading, predictions, MEI and headroom

Publish all mapping, graph/control and helper outputs, including alternatives. Complete
finite output with two `RAW_LOGIT_PASS_THROUGH` rows,
`CHOLESKY_OMITTED_FROM_TRAINING_HEAD_GRAPH` and `NATIVE_CLIP_CONTRAST_REPRODUCED` yields
**A05-SYNTHETIC-BOUNDARY-REPRODUCED**. Any other complete finite combination yields
**A05-ALTERNATE-SYNTHETIC-READOUT**, naming each component without combining its meaning.
Missing required measurements, changed protected bytes, unintended parameter update,
extra environment/learner exposure or cap breach is incomplete, not a negative.
Any failure classification cites the exact reproduced step; a process error alone
does not become a scientific or technical diagnosis.

DM predicts the first joint branch, based on the pre-card static map; exact synthetic
numbers have not been calculated. Owner prediction: `not taken (unattended)`, same
existing B01 diagnostic ladder, no duplicate opening request. Predictions remain in
the card despite the owner's stop on ordinary prediction inbox maintenance.

MEI is a 1e-6 separated raw/link mapping contrast, one 0.05 native q95 bin, and binary
absence/presence of the Cholesky path with positive control. These are the smallest
interface resolutions useful here, not return improvements. Above these resolutions,
identify the concrete interface fact for the next decision; inside them retain an
undiscriminating synthetic result; an opposite mapping/connection updates the static
interpretation. Every branch requires intake before any repair or controller study.
No tuned host headroom exists. A03's incumbent service and B01's unestimated five-tick
source MEI are not changed by synthetic API evidence.

## 7. Exposure, route, budget and stop

Machine-generated exposure must report: one model/policy initialization; one complete
synthetic policy recurrent forward; one extra service-Q linear-head call; one
training-head graph call; one full-head positive-control call; two backward passes;
one compile/load and nine scalar native-helper invocations. Report the two synthetic
policy rows and all three fixed helper cases. No optimizer/checkpoint/training master,
native state or actual trace is initialized/read, and no training transition/update,
optimizer step or native reset/prepare/completion/episode occurs. Autograd work is
reported explicitly, not hidden behind zero learner-update counts.

Nested-call accounting: `heads()` executes twice in total (inside the policy and in
the positive control), the service-Q linear layer four times, and the Cholesky linear
layer twice. These are nested within the listed top-level calls, not extra probes.

Parameter displacement is measured against the one synthetic model's initialization
scale and must remain zero. No before/after value is taken from the retained B01 model.

One result invocation, no sweep or additional seed. The runner's direct `project-cost`
law is `1.5*(10 seconds import/model allowance + 5 seconds compile/load allowance +
2 seconds for all mapping/graph/helper/readout work) = 25.5 seconds`, cap **60 seconds**.
These allowances are prospective, not measured performance. Report full runner wall
including import/compile and final publication, peak RSS and exact timing scopes.
Start its timer before importing the probe or Torch. The lightweight `project-cost`
path does not import the model/compile path or construct question-relevant inputs.
If an outer supervisor has only integer duration, retain that resolution honestly.

Use `wsl_4070`, exact committed/pushed source in a detached worktree, and existing
`agent-task`. Fresh actual-node physical/effective available memory must each exceed
or equal 4 GiB via adjacent `admit-memory --out <receipt> && <runner>`, before model,
input, compiler or result construction. Receipt is outside the fresh output child.
No duplicate in-run validator. Portable fallback is allowed only within the declared
numeric/toolchain boundary, before any remote process acceptance, with fresh destination
admission. Stop after this single complete readout; no repeat, repair, extra vectors,
head tuning, native episode or scientific successor is automatic.

## 8. Engineering contract and owner surface

**Engineering-scope section 4: this object needs none of the default-prohibited
machinery.** Graph and helper readouts are the experiment's quantities, not a runtime
telemetry system. The thin direct measurement export is not a compatibility shim or
replacement API. Reuse the existing supervisor and admission; no new execution/control
plane, provenance gates, cache framework or abstract layer is built.

Owned surfaces: the A05 probe may live directly in
`scripts/run_dish_prediction_head_contract_a05.py` or in its small direction module;
the thin C++ translation unit remains in
`experiments/candidates/degraded_incumbent_shadow_handover/`, with matching focused
tests and result documents. This layout clarification preserves every quantity and
call above; see `DISH_PREDICTION_HEAD_CONTRACT_A05_SCOPE_INTAKE_20260905.md`.
Preserve all old source. Aim for 150–250 non-test lines; hard limits are
2,000 new non-test, runner 600 and orchestration <30%, tests excluded. Return excess
with named lines; do not pad the denominator or replace real calls with duplicated logic.

One toy end-to-end publication smoke and reading-rule tests use non-card synthetic
fixtures (seed 50512 and helper levels -1/0.5/1), over exact committed remote bytes;
the smoke has a 60-second cap. No repeated original A05 invocation
is a verification step. The card's seed/levels and all call counts above belong only
to its admitted result. CM records the verification profile and its separate exposure,
accepts technical completeness, then gives the unique accepted result handle directly
to `/root/tracker_tl_experiments`. DM takes in the original collected result.

Runtime root:
`temp/directions/degraded_incumbent_shadow_handover/exp/prediction_head_contract_a05_20260905/`.
The genuine new card remains a P2 owner item, with its Chinese decision packet. No
ordinary decision, technical, prediction or brief inbox item is created under the
2026-09-05 OWNER_DIRECT cutoff. Existing replies are read/applied without waiting.

## 9. Append-ready card audit for Root

The object selection is already recorded in A04 intake; this row records its separate
prospective card. No synthetic output has been obtained at carding. Anchor
`n3-prediction-head-contract-a05-card`.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T05:26:14-07:00 | degraded_incumbent_shadow_handover (N3) | object | selection | accept; reject; revise | A05 card frozen; recommendation accept, no output yet | yes | DM_CARD | docs/research/portfolio/owner/inbox/2026-09-05/20260905-dish-018.json | none | |
