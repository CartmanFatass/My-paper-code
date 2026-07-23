# Access-positive mechanism-matched EHC G1 implementation plan

> **Required project procedure:** use `$hmasd-agile-research-development`.
> Generic Superpowers execution and workflow hash handoffs are disabled.

```text
active_implementation=ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1
implementation_status=PM_ACCEPTED_PRELAUNCH
design=docs/research/designs/ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1.md
backend=cpu
torch_threads=1
formal_run_status=authorized_pending_controller_integration_and_launch
G0_mutation=forbidden
backward_compatibility=not_required
```

**Goal:** replace the completed synthetic G1 measurement prototype with the
smallest independent learned OR/DUM/EHC source, trainer, evaluator, causal
audit, and first-match analyzer that instantiate the frozen formal contract.

**Architecture:** `temporal_duty_g1.py` owns stochastic exogenous ledgers and
the anonymous environment. A new `ehc_g1.py` owns the separated actor/critic,
event-held state, collection, replay, PPO and checkpoints. A new formal runner
owns train/evaluate/analyze artifact schemas. G0 remains untouched.

## Global invariants

- Exact six-field actor input; critic tensors never enter actor/event paths.
- Segment success is both 75% whole-segment accuracy and final-two correctness.
- Reward sum equals `U=0.75A+0.25B`; no intrinsic reward.
- JOIN/reset, temporary freeze/restore, terminal censor and opportunity clocks
  follow the design.
- OR/DUM/EHC base initialization is matched; DUM/EHC event exposure is matched;
  only EHC executes `W_z(m*z)`.
- Separate RNG namespaces, stored-draw replay, CPU one-thread checkpoint fence.
- Access and source identification precede every mechanism interpretation.
- No per-file hash handshake, compatibility layer, G0 import, or legacy schema.

## Task 1 — Formal temporal-duty source

**Status:** complete and PM accepted.

**Own:**

- Modify `ha_ctse_process/temporal_duty_g1.py`.
- Replace `tests/ha_ctse_process_temporal_duty_g1_test.py`.

**Implement:** formal train/IID/held-out ledgers, sign mates, stochastic duty and
opportunity streams, exact actor/critic views, lifecycle transitions, corrected
completion, reward identity, snapshot/restore, oracle and history-free controls.

**Focused proof:** distribution balance/independence, no leakage, cue expiry,
75%+last-two boundary, membership pattern transport, freeze/restore, censoring,
reward identity, RNG ownership, source-identification controls.

## Task 2 — Learned arms and collection

**Status:** complete and PM accepted.

**Own:**

- Create `ha_ctse_process/ehc_g1.py`.
- Create `tests/ha_ctse_process_ehc_g1_test.py`.

**Implement:** separated 6-field actor and 10-field critic, 32-unit recurrent
base, OR/DUM/EHC masks, event/mark heads, commitment lifecycle, exact
factorization, stochastic/deterministic draws, 16x80 collection and natural
KEEP/RENEW/spell records.

**Focused proof:** matched initialization/capacity/exposure, EHC-only logit
treatment, actor/critic separation, hidden/reset/freeze ownership, action/event/
mark probability support, no extra RNG draw, row provenance and mixed lifecycle
packing.

## Task 3 — Replay, PPO and checkpoint

**Status:** complete and PM accepted.

**Own:** same Task-2 files.

**Implement:** stored-draw replay, joint ratios, GAE, four full-rollout PPO
passes, base/event gradient fences, optimizer counters, atomic rolling/final
checkpoint and exact CPU resume.

**Focused proof:** replay equality and corruption negatives, detach/parameter
ownership, finite ratios/gradients, counter/exposure totals, RNG restoration,
same-backend continuation and foreign/non-G1 checkpoint rejection.

## Task 4 — Formal runner, audit and result

**Status:** complete and PM accepted.

**Own:**

- Create `scripts/run_access_positive_ehc_g1.py`.
- Create `tests/run_access_positive_ehc_g1_test.py`.

**Implement:** `train`, `evaluate`, `analyze`, and bounded `exercise` commands;
exact manifests and reference closure; four evaluation cells; oracle/reactive
controls; 10,000 paired hierarchical bootstrap; held-out EHC causal branches;
the independent eight-branch G1 selector.

**Focused proof:** exact exposure/evaluation inventories, cluster resampling,
natural quotas, K/I-TV/C-total definitions, selector equality and exhaustive
first-match precedence, schema/tamper rejection, nonformal exercise rejection by
formal analyzer, and no G0 result/schema import.

## Task 5 — Active-line deletion

**Status:** complete.

After Tasks 1--4 pass, delete:

- `ha_ctse_process/ehc_sequence_mediation_g1.py`;
- `scripts/run_ehc_sequence_mediation_prototype_g1.py`;
- `tests/ha_ctse_process_ehc_sequence_mediation_g1_test.py`;
- `tests/run_ehc_sequence_mediation_prototype_g1_test.py`.

Keep the prototype design, CDC evidence note, and Git history. Update workflow
contract tests to the new active implementation only.

## Task 6 — Bounded prelaunch acceptance

**Status:** complete and PM accepted.

Run the focused G1 suite with the registered CPU interpreter and one thread,
then one small `formal=false exercise` covering collection, replay, one PPO
update, checkpoint reload, evaluation, causal audit and analyzer rejection.
Inspect the changed path for leakage, RNG drift, recurrent contamination,
scalar transfer, repeated packing, premature synchronization, excess
persistence and serial evaluation.

Project Manager freezes the final artifact/command contract and accepts or
repairs the package. The exercise consumes zero conclusion-bearing iterations.
After acceptance, Controller may launch the already-authorized formal CPU run
without another user prompt.

Accepted nonformal evidence:

- artifact: `logs/nonformal_access_positive_ehc_g1_prelaunch_20260723_pm2`;
- focused suite: 36 passed;
- exercise: CPU one thread, one update, three final checkpoints, 12 reduced
  evaluation cells, two causal-audit continuations, eight bootstrap repetitions;
- result: `formal=false`, `SOURCE_NON_IDENTIFIABLE_G1`, no operational errors;
- formal validator: rejected the exercise because `formal=true` was absent.

The accepted analyzer persists cluster-level source-control utilities and
recomputes source summaries, episode/audit metrics, source identifiability,
predicate inputs and first-match selection from referenced evidence. Observed
evidence supplies all point estimates; bootstrap samples supply confidence
bounds only. A formal `analyze` command validates this complete binding before
it can return success.

The formal command contract is `train -> evaluate -> analyze`, all against one
new run directory. `train` requires the exact integrated 40-character source
commit and authorization token
`AUTHORIZE_ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_CPU_V1`; all three
commands use the registered CPU interpreter and one thread. Controller fills
only the integrated commit and run-directory identity, then launches and
monitors the already-authorized run. No scientific field or result gate is
filled at launch time.
