# External Pro open question: G40 code-science alignment

```text
review_type=CODE_SCIENCE_ALIGNMENT_AUDIT
audit_mode=read_only_contract_diff
compute_budget=zero
audit_target_commit=8fbc4964724b9eebdbecfb060a297d2ff55f60ed
implementation_code_commit=8fbc4964724b9eebdbecfb060a297d2ff55f60ed
index=docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md
frozen_contract=docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/21_PRO_OPEN_RAW.md
formal_compute_started=false
nonformal_compute_started=false
allowed_outputs=ALIGNED|MISMATCH|SCIENTIFIC_AMBIGUITY
```

## Exact evidence allow-list

- `.agents/roles/EXTERNAL_PRO.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/project/SCIENTIFIC_ASSERTION_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260727_continuous_roster_native_six_credit_reduction_g40_design_assertion_audit/50_MECHANICAL_INTAKE_RECORD.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40.md`
- `docs/research/designs/CONTINUOUS_ROSTER_NATIVE_SIX_CREDIT_REDUCTION_G40_CODE_SCIENCE_INDEX.md`
- `ha_ctse_process/continuous_roster_native_six_credit_reduction_g40.py`
- `scripts/run_continuous_roster_native_six_credit_reduction_g40.py`
- `tests/ha_ctse_process_continuous_roster_native_six_credit_reduction_g40_test.py`
- `tests/run_continuous_roster_native_six_credit_reduction_g40_test.py`
- `ha_ctse_process/continuous_roster_native_six_coordinate_training_g39.py`
- `scripts/run_continuous_roster_native_six_coordinate_training_g39.py`
- `ha_ctse_process/continuous_roster_toy_cpp_backend.py`
- `ha_ctse_process/native/continuous_roster_toy_backend.cpp`
- `ha_ctse_process/continuous_roster_random_process_g34.py`
- `ha_ctse_process/runtime_capacity_continuous_roster_g32.py`
- `ha_ctse_process/return_to_go_direction_balanced_full_actor_g31.py`

You are External Pro acting only under `.agents/roles/EXTERNAL_PRO.md`.
Inspect the exact pushed audit target and the allow-list in
`01_SHARED_SOURCE_MANIFEST.md`. The index is navigation, not a substitute
for reading the named implementation.

## Question

Does Code Project Manager's accepted implementation instantiate the exact
frozen G40-P0 comparison between `NATIVE6_G31` and
`NATIVE6_TEAM_GAE1` after one common native-six fast-access anchor, without
introducing a result-changing actor, critic, source, capacity, optimizer,
RNG, exposure, checkpoint, confidence or evaluation route?

Check only these conformance points:

1. Common phase and branch identity: one accepted G39 native-six actor at
   capacity 8 and unchanged G32 fixed process is trained for 100 fast updates
   with 8 environments/update and 2 PPO passes; the anchor optimizer is
   discarded, every actor/critic/head/log_std/buffer tensor is cloned bitwise
   into two separately-owned arms, and each arm receives 100 branch updates,
   8 environments/update, 2 PPO passes and final-only checkpoint selection.
   Both paired trajectories are materialized and validated before either arm
   updates.
2. Exact model/head inventory: actor, log_std, centralized true-current-state
   critic, immediate baseline and successor baseline have equal keys, shapes,
   trainable masks, parameter counts, initial bytes and optimizer-group order.
   In the ordinary arm the two auxiliary heads are shadow-only, fit the same
   detached targets with the same optimizer exposure, have no actor/critic or
   metric read, share no storage, and their omission leaves ordinary actor and
   slow-critic updates bitwise unchanged while the shadows update.
3. Exact credit semantics: `gamma=0.99`, terminal bootstrap zero, no
   membership reset, `G_t` and `S_t=G_{t+1}` computed after the full real
   trajectory; G31 uses the accepted immediate/successor streams and the
   byte-identical direction-balancing operator; ordinary uses one shared-team
   `lambda=1` GAE stream, verifies `A_GAE1=G-V` within `1e-6`, centers/scales
   once per batch, broadcasts to active factors and performs no split,
   direction balancing, per-agent return or active-count scaling.
4. Exact optimizer and exposure: Adam beta1=.9, beta2=.999, eps=1e-8,
   weight decay 0, learning rate 1e-3, no clipping or minibatches; the actor,
   log_std and both baselines use the actor-credit optimizer, the centralized
   critic is separate, each takes one step per PPO pass, and baseline
   gradients never enter the G31 norm. The C++ `ContinuousRosterToyBatch`
   backend is required for collection/evaluation with no Python fallback;
   Python remains orchestration/ledger/fail-closed validation only.
5. Exact seeds, pairing and evaluation: formal seed bases are
   10401000/10402000/10403000/10404000/10405000/10406000/10407000/10408000/
   10409000, bootstrap 10410040, formal replicate `+r` once and nonformal
   `+900000` to every seed. Arms share the anchor, ledgers, episode IDs,
   action noise, process signatures, evaluation noise and bootstrap plan.
   Evaluation is zero-update, has five cells per arm/capacity at capacities
   6/8/12, 3 replicates and 64 episodes/cell, with the registered G34 tuple,
   order and paired-stream law.
6. Exact gates and estimands: fixed/random deterministic and stochastic
   access floors, learned-gain strict `LCB>0`, equal-capacity
   `Delta_credit=U_G31-U_TEAM_GAE1`, inclusive noninferiority UCB `<=.05`,
   strict material advantage LCB `>.05` with every capacity-specific LCB `>0`,
   10,000 whole-episode hierarchical bootstrap, equal capacity weights and
   the exact first-match order INVALID, SOURCE_OR_COMMON_ACCESS_FAILURE,
   ORDINARY_TEAM_GAE_CREDIT_SUFFICIENT, G31_REALIZED_TAIL_CREDIT_ADVANTAGE,
   MIXED_UNDERPOWERED. Diagnostics may not relabel an earlier branch.
7. Exact evidence complexity and authority: `H=48`, `K_search=0`, zero
   hypothetical transitions, no nested rollout/replanning, nonformal
   20,160 transitions/100 optimizer steps/250 draws and formal 622,080
   transitions/3,000 optimizer steps/10,000 draws within the 1,200/28,800
   second caps. Formal authority must remain fail-closed to the exact G40
   token, same-source ALIGNED audit and all required preflight artifacts;
   no nonformal artifact may authorize formal execution.

Determine whether malformed parameters, gradients, shadow heads, source
backend identity, pairing, RNG, checkpoints, cells, episode identities,
confidence resampling or route labels can bypass a conclusion-bearing branch.
Do not evaluate style, general code quality, performance claims, workflow
design or unregistered scientific scope. This is a contract diff only.

Return exactly one disposition:

- `AUDIT_DISPOSITION=ALIGNED` if the exact target instantiates the frozen
  contract and no indexed test/probe can pass through a result-changing wrong
  mechanism.
- `AUDIT_DISPOSITION=MISMATCH` only with the exact frozen assertion and exact
  conflicting code path or behavior, plus the smallest in-contract correction.
- `AUDIT_DISPOSITION=SCIENTIFIC_AMBIGUITY` only with one previously unstated
  result-changing scientific choice that prevents conformance judgment.

Do not introduce or request a new algorithm, controller, solver, source,
search, threshold, evidence volume, experiment or formal run. Do not accept
or redesign PM code. Stop after the single scoped disposition.
