# HA-CTSE Active Implementation Plan

Updated: 2026-07-20
Status: IMPLEMENTATION_COMPLETE_AWAITING_FORMAL_RUN
Work ID: `clean-supplied-executor-high-path-g0-20260720-v2`
Assignment base/source commit: `7e289a107bafd47666c802555e23a7d625e8794f`
Implementation commit: `2d66d253d8b129e4c58e7cf4762b4ca96125dd31`

## 1. Accepted executable boundary

Implement only `CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0` on the unchanged clean
dynamic-roster carrier. The one learned parameter graph is the existing F1
`VariableRosterEventCore` commitment actor plus event critic. Skill values have
the exact primitive meaning `0=IDLE`, `1=PERSIST`, and `2=SHORT`; execution is a
parameterless identity lookup and creates no low-policy distribution,
likelihood, replay row, optimizer, update, or gradient.

The three comparison arms are:

1. `learned_high`: stochastic F1 event actions during training and deterministic
   F1 event actions during registered evaluation; only the commitment actor and
   event critic receive PPO updates.
2. `frozen_high`: a strict byte-equal copy of the learned arm's update-zero high
   state, never optimized, evaluated on the same evaluation episode IDs and
   event RNG ledgers.
3. `routing_oracle`: the existing environment-owned constructive routing rule
   is queried only when an owner is on the event frontier, then teacher-forced
   through the same lifecycle/opportunity runtime. It has no trainable state and
   is not an actor comparator.

The formal learned exposure is exactly 16 environments, horizon 80, 250 outer
updates, 320,000 primitive environment transitions, four PPO passes per update,
1,000 high optimizer steps, and zero low optimizer steps. Deterministic learned,
frozen, and oracle evaluations use the same 256 episode IDs. The frozen arm is
the update-zero parameter control; it does not receive synthetic optimizer
steps.

Use the registered seed ledger without secondary folding:

- model initialization: `57_057`;
- training task ledgers: `67_057`, episode IDs `0..3999`;
- opportunity gaps and frontier order: `77_057`, streams 0 and 1;
- learned policy action sampling: `87_057`, stream 0;
- evaluation task ledgers: `97_057`, episode IDs `0..255`;
- paired bootstrap: `107_057`, 10,000 resamples.

## 2. Files, symbols, and ownership

The Code Implementation Manager is the sole writer of this plan. The accepted
implementation package comprises the coupled executable/test files below:

- `ha_ctse_process/variable_roster_event.py`
  - add an explicit supplied-executor/no-low-path runtime mode with the existing
    mode remaining the default;
  - keep the same `EventCommitmentPolicy`, `EventHighCritic`, event token ledger,
    owner GAE, exact legal mask, opportunity schedule, lifecycle records, and
    checkpoint payload structure;
  - add a high-only packed replay/loss/update API that is algebraically identical
    to the high half of current event PPO and never reads low replay;
  - in supplied mode, advance reward, active age, opportunity gap, open owner
    trace, and physical time without a low transition row; low inference/update
    entry points fail closed.
- `ha_ctse_process/dynamic_roster_supplied_executor.py` (new)
  - own the parameterless skill-to-primitive executor, learned/frozen/oracle
    evaluation helpers, formal seed/budget constants, paired bootstrap, strict
    branch classification, checkpoint/resume helpers, and the deterministic M0
    contract audit.
- `scripts/run_clean_process_supplied_executor_high_path.py` (new)
  - own CLI/status/result/checkpoint plumbing, formal contract enforcement,
    smoke/dry validation, learned training, frozen/oracle paired evaluation, and
    terminal result serialization.
- `tests/ha_ctse_process_clean_supplied_executor_high_path_test.py` (new)
  - one focused deterministic contract test over the complete new boundary.

Do not edit `dynamic_roster_clean_process_testbed.py`,
`dynamic_roster_direct.py`, `r30_fixed_clock.py`, `standalone_agent.py`,
`train.py`, existing tests/runners, or any project-control/review file.

## 3. Replacement and deletion ledger

- Replace the learned low actor/critic execution path only inside the new
  supplied runtime mode with the identity executor and high-only PPO path.
- Retain the existing default learned-low event runtime behavior and keep its
  public calls as the default.
- Add no adapter from old checkpoints and no legacy CLI alias. A checkpoint
  whose runtime mode, schema, arm, model shape, seed ledger, counter ledger, or
  collector capability differs from this diagnostic is rejected.
- No existing executable or evidence file is obsolete at this boundary, so no
  tracked file is deleted.

## 4. Data, tensor, and control flow

For each environment episode, the clean event adapter supplies the existing
pre/post membership transaction. `VariableRosterEventCore.bind_due_frontier`
adds only due opportunity owners. `apply_transaction` samples or teacher-forces
one high categorical action per frontier owner and records the existing exact
token row. The supplied executor reads only `active_skills()` and returns the
same integer per active lifecycle; those primitive actions go directly to
`CleanProcessDynamicRosterEventEnv.step_event_runtime`.

The external team reward is accumulated once into each active owner's open
trace with `gamma^elapsed_physical_time`. Supplied mode then increments the
owner's active skill age, decrements its private opportunity gap, and increments
physical time. It does not allocate or mutate low actor/critic hidden state,
emit a `LowTransitionRow`, or create low likelihood.

At each full-horizon training boundary, owner GAE and stored event tokens are
packed once. Four PPO passes replay the immutable high pack. Gradients flow only
through the current commitment actor log probability and current event critic
value. Stored observations, masks, actions, old log probabilities, old values,
advantages, returns, recurrent hidden inputs, and RNG draws are detached replay
truth. The frozen and oracle arms run under `torch.no_grad()`.

## 5. State and invariant ownership

- The environment owns task state, clean process state, membership deltas,
  external reward, and its pre-sampled task ledger.
- The event core owns lifecycle epochs/status, active skill and age, private
  opportunity gap, survivor high hidden state, physical/event/lifetime clocks,
  open/closed owner traces, high token replay, and the three PCG64 streams.
- Temporary leave freezes the complete lifecycle-owned state; rejoin increments
  the membership epoch and resumes survivor high state. Genuine join starts from
  zero high state and undefined skill until its mandatory SET.
- Active masks and exact all-three-action legal masks remain model inputs;
  lifecycle keys and membership epochs remain routing-only.
- Event action probability is the existing single categorical probability on
  the exact stored support. Replay must reproduce old high log probability and
  owner value within `1e-6`. Order probability remains the exact frontier
  permutation factor and owner credit remains unique.
- The executor consumes no RNG. Task, opportunity, frontier, learned-action,
  evaluation, and bootstrap streams remain distinct and are never reseeded from
  global Python/NumPy state.
- A live checkpoint is a strict joint boundary containing high model and
  optimizer state, disabled-low sentinel state, every lifecycle/open trace and
  ledger, policy version, all core RNG states, task/environment snapshot and
  environment RNG ledger, pending transaction/current boundary, global Torch
  CPU/CUDA RNG states, and exact counters. Restore rejects missing/extra fields
  and must reproduce a mid-segment continuation exactly.
- The frozen checkpoint is produced from the same serialized update-zero high
  tensors as learned training and remains byte-equal after the learned arm
  changes. Oracle outputs must be invariant to high-model tensor changes.

## 6. Result contract and registered branches

`M0` is implementation validity only. It requires exact executor actions and
zero executor parameters/low likelihood/low rows/low updates; arm isolation;
formal counts and ledger IDs; clean-carrier audit; exact active masks, high
probability/value replay, owner-specific physical-time credit, RNG separation,
leave/rejoin/genuine-join continuity, deterministic mid-segment continuation,
strict checkpoint round trip, finite learned updates, nonzero learned high
drift, and zero frozen drift.

If M0 fails, status is `INVALID_CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0` and the
only action is repair of the named defect. Otherwise M1 applies the accepted
branches in this priority:

1. oracle mean persistent/short/utility below `0.95` ->
   `INVALID_CLEAN_SUPPLIED_EXECUTOR_OPPORTUNITY_CONTRACT`;
2. frozen deterministic mean utility at least `0.60` and persistent/short each
   at least `0.55` -> `FROZEN_HIGH_SUFFICIENT_CLEAN_SUPPLIED_EXECUTOR`;
3. learned deterministic mean utility at least `0.60`, persistent/short each at
   least `0.55`, and paired learned-minus-frozen utility LCB95 strictly above
   `0.10` -> `PASS_CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0`;
4. otherwise -> `VALID_FAIL_CLEAN_SUPPLIED_EXECUTOR_HIGH_PATH_G0`.

No runner code selects or launches a successor.

## 7. Performance structure

Pack ragged active rows once per rollout boundary and reuse the high replay pack
for all four PPO passes. Share one high parameter graph across the 16 cores,
batch or coalesce model work where existing APIs permit, keep environment loops
only for simulator/lifecycle causality, and transfer/reduce metrics only at
update/evaluation boundaries. Formal mode requires CUDA; focused tests and smoke
mode use CPU and reduced counts without changing formulas.

## 8. Focused evidence and implementation state

Focused verification completed with exactly the new focused pytest file plus
the directly affected existing event-runtime test. The new test covers in one
deterministic contract:

- exact `IDLE/PERSIST/SHORT` execution and absence of low likelihood/state rows;
- byte-equal learned/frozen initialization, learned-only drift, frozen zero
  drift, and oracle independence;
- active mask/support, high log-probability/value replay, owner credit, and
  registered count/seed headers;
- genuine join, temporary leave, rejoin, terminal leave, survivor high-state
  continuity, and distinct clocks;
- checkpoint strictness, tensor/optimizer/counter/collector/RNG round trip, and
  exact continuation from an open mid-segment boundary.

The formal 320,000-step diagnostic has not been run. Implementation is complete
and awaiting that registered formal run. The accepted implementation boundary
is commit `2d66d253d8b129e4c58e7cf4762b4ca96125dd31`; its focused checks passed and
the package was accepted with `acceptance=MANAGER_ACCEPTED`.

## 9. Non-goals

No learned executor or low-policy update, intrinsic reward, B/C executor,
delayed carrier, UAV integration, new reward/critic/latent/graph/communication
module, threshold/budget/seed/model/task/carrier change, compatibility path,
formal compute, external review, Git operation, or successor route is part of
this implementation.
