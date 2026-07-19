# HA-CTSE Active Implementation Plan

Updated: 2026-07-19

This file contains only the current staged contract. Scientific principles live
in `ALGORITHM_PRINCIPLES.md`, engineering principles in
`MARL_ENGINEERING_PRINCIPLES.md`, formal run contracts and dispositions in
`ExpRecord.md`, and removed plans in Git history.

## Clean-Process Dynamic-Roster Direct-Access Qualification

Status: authorized for one complete autonomous research iteration by the user
on 2026-07-19. This is the single next evidence source selected by the accepted
post-Iteration-5 convergent disposition. It is not an Iteration-5 rescue and
does not implement B, C, hierarchy, skills, or intrinsic reward.

### Controller Design

- **Core decision:** qualify one new dynamic-roster carrier that retains the
  learnable Generic-SHORT task and adds a separate task-neutral physical process
  channel, then test the unchanged active-set direct recurrent learner.
- **Reuse:** `DirectPrimitiveARPolicy`, direct collection/PPO/replay/checkpoint
  code, Generic-SHORT membership/task ledger, typed event runtime, constructive
  controller, exposure, seeds, and Stage-A/B thresholds.
- **Replace/delete:** replace the Iteration-5 spatial carrier and all C1
  semantic-on/off paths with one clean-process carrier and a three-control
  qualification. Do not add an alternate learner path.
- **Data flow:** task observation and critic state remain exactly the existing
  15/8-dimensional Generic-SHORT inputs. A separate per-lifecycle two-scalar
  actuator process state updates only on active primitive steps, freezes during
  temporary absence, resumes on REJOIN, starts at zero on genuine JOIN, and is
  removed from active execution on terminal leave. It is audit-only and never
  enters actor, critic, reward, GAE, PPO, or checkpoint selection.
- **Gradient/probability flow:** unchanged direct primitive autoregressive
  likelihood over active members only; no event, membership, process-channel,
  high, skill, survival, or semantic probability factor. Gradients enter only
  the existing direct actor-critic through terminal external reward.
- **RNG:** retain model/train/action/evaluation/bootstrap streams
  `57056/67057/87057/97057/107057`; use independent random-control stream
  `117057`. Process dynamics are deterministic conditional on executed actions.
- **Checkpoint:** retain strict schema-3 direct checks; carrier snapshots also
  own process state and must round-trip exactly. Missing live state hard-fails.
- **Expected behavior:** constructive P/S/U is at least 0.95; uniform-random
  positive utility fraction is at least 0.20 with mean below 0.55; direct must
  pass the frozen Stage-B access thresholds. Process readout alone is not skill
  evidence.

### Exact Files and Symbols

1. `ha_ctse_process/dynamic_roster_clean_process_testbed.py`: carrier ledger,
   environment, event adapter, factories and contract audit.
2. `scripts/run_dynamic_roster_stage_b.py::run_stage_b`: factory injection
   only; model, optimization, thresholds and result semantics remain frozen.
3. `ha_ctse_process/dynamic_roster_direct.py`: preserve the frozen direct
   algorithm while removing per-member CUDA scalar synchronization and packing
   each rollout onto the device once for all PPO passes.
4. `scripts/run_clean_process_direct_access.py`: controls, direct-core reuse,
   result branches, status and stage timings.
5. `tests/ha_ctse_process_clean_process_direct_test.py`: one focused carrier
   and runner smoke contract.

Frozen interfaces are the direct policy architecture and factorization,
collection/update/replay ordering, task observation, critic features, terminal
reward, membership schedule `4 -> 2 -> 6 -> 4`, horizon 80 and active masks.

### Formal Evidence Contract

- Local CUDA; 16 batched environments; horizon/rollout 80; 250 updates;
  320,000 transitions; PPO4; 1,000 optimizer steps; 256 deterministic and 256
  paired stochastic exact-final evaluation episodes.
- Constructive minimum P/S/U `>=0.95`. Random positive-utility fraction
  `>=0.20` and mean utility `<0.55`.
- Direct deterministic U `>=0.70`, P/S `>=0.65`, stochastic U `>=0.60`, and
  paired deterministic final-minus-zero utility LCB95 `>0.15`.
- M0 covers counts, replay `<=1e-6`, finite nonzero update, exact checkpoint,
  lifecycle/mask ownership, process freeze/resume/new-join zero, process
  snapshot round-trip and exclusion, independent RNG, and stage wall time.

Branches are `PASS_CLEAN_CARRIER_DIRECT_ACCESS`,
`NO_ACCESS_CLEAN_CARRIER_DIRECT`, `RETIRE_CLEAN_CARRIER_CALIBRATION`, and
`INVALID_CLEAN_CARRIER_IMPLEMENTATION`. A valid outcome is terminal for this
iteration and is not rescued.

No result-contingent observation, reward, horizon, task, model, optimizer,
budget, seed, threshold, checkpoint or process change is allowed. No high,
skill, KEEP/SET, posterior, intrinsic reward, graph, slot, latent,
communication, identity/role/task field, learned timing, scheduler, duration
catalogue, or renamed retired objective may enter.

Completion requires one focused CPU smoke, one controller semantic/efficiency
review, the exact CUDA run, registered disposition and one external-review round
if the result leaves a portfolio or next-evidence decision open. No second
research iteration starts automatically.

## Completed Prior Contract — Iteration 5 Spatial Process-Semantics Comparison

Status: complete. The fresh formal run closed as valid
`RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS`; M0 passed, but the C3 direct arm did
not meet the registered short-duty or final-minus-zero gain requirements on
this carrier. The C1 utility differences therefore remain quarantined from an
algorithmic claim, and the material-semantics audit independently failed. The
exact contract is retired without rescue and the five-iteration autonomous
boundary is exhausted.

### HMASD Contract

Final capability:

```text
one shared anonymous algorithm
+ runtime-variable team membership
+ survivor/rejoin continuity
+ variable realized skill lifetime
+ task-independent process semantics
```

Causal question:

```text
clean local motion process
-> conditional process-posterior intrinsic pressure
-> material and persistent z -> behavior control
-> natural skill use
-> sparse terminal-task access beyond semantic-off hierarchy
```

Live explanations tested by one evidence source:

1. **C3 / direct active-set control:** recurrence and primitive-time
   autoregression suffice; explicit skills add no load-bearing value.
2. **C1 / missing semantic pressure:** the hierarchical executor is capable,
   but sparse external reward does not create distinct process modes.
3. **C1-null / arbitrary diversity:** distinguishable modes may emerge without
   helping the cooperative task.
4. **Carrier mismatch:** a carrier without a clean physical process view cannot
   test environment-agnostic semantics.

C2 event-context execution is dormant. Conditional SMDP/assignment credit stays
closed. The strongest ordinary baseline is the unchanged C3 direct recurrent
controller on the same carrier and exposure.

### Replacement Ledger

Retain:

- anonymous `4 -> 2 -> 6 -> 4` membership, temporary leave, genuine join,
  rejoin, terminal leave, and survivor recurrent continuity;
- schema-3 event runtime, F0 initial-summary event selector, exogenous
  opportunity gaps, categorical KEEP/SET likelihood, owner-event
  `gamma^Delta` return, and physical-time low PPO;
- batched low inference and once-per-rollout recurrent PPO packing;
- the Stage-B direct active-set actor/critic as C3;
- sparse terminal external utility and 16-env CUDA exposure.

Delete from this evidence source:

- F1 applied-working-prefix treatment;
- Generic-SHORT action/observation deltas as semantic input;
- old process, transition, team-latent, `q_D`, learned-timing, scheduler,
  graph/field/slot, and task-shaped reward paths.

Add only:

- a 1-D spatial dynamic-roster carrier with a task-neutral local process state;
- one conditional process posterior with online estimator and frozen rollout
  scorer;
- one lifecycle/window ledger per environment;
- paired `semantic_on` / `semantic_off` hierarchy arms and the same-carrier C3
  arm in one result.

### Spatial Carrier

Owner: `ha_ctse_process/dynamic_roster_spatial_testbed.py`.

- Horizon/rollout: 80.
- Roster: four at `t=0`; two temporary leaves at 20; both rejoin and two new
  members join at 40; two terminal leaves at 60.
- Positions: anonymous cells `{0,1,2}`. Temporary leave freezes position and
  rejoin restores it.
- Actions: `LEFT=0`, `STAY=1`, `RIGHT=2`; movement occurs before duty accounting.
- Persistent duty: one active owner at cell 0, target 64 units; duplicate
  occupants add no work.
- Reactive duty: eight hidden short-wave arrivals; target cell is 1 or 2;
  `N_t-1` distinct contributors must occupy it for two consecutive post-action
  steps within the fixed deadline.
- External reward: terminal
  `U = 0.5 * (persistent_score + short_score)` only.
- Task, opportunity, action, semantic-sampler, and model RNG streams remain
  separate.

The actor keeps the existing 15-D anonymous observation contract and the critic
the existing 8-D global contract. Lifecycle keys are routing-only. The semantic
ledger receives only pre/post `process_state = position / 2`; it receives no
target, reward, task progress, owner/contact flag, identity, roster slot, clock,
age, duration, or action.

Constructive and uniform-random controls belong to the result. Constructive
`P/S/U` must each be at least 0.95. Uniform random must have positive-utility
fraction at least 0.20 and mean utility below 0.55. Carrier failure stops all
learning interpretation.

### Conditional Process Posterior

Owner: `ha_ctse_process/process_semantics.py`.

For each closed window `w` of at most 12 active transitions:

```text
C_w = stopgrad(start actor observation, start low hidden, valid mask)
X_w = stopgrad([x_t - x_start, x_t - x_(t-1)] for active t)
Z_w = current individual skill

q_phi(z | X,C,M) = softmax(W * (context(C,M) + process_GRU(X,M)))
b_phi(z | C,M)   = softmax(W * context(C,M))
L_phi            = CE(q_phi,Z) + CE(b_phi,Z)
```

The context tower and classifier are shared. Posterior batches are balanced by
skill and valid length. Inputs are detached. No reward, return, target,
distance, identity, roster slot, age, duration, action, team code, or centralized
critic state enters `X`.

The frozen scorer is fixed for one rollout. The first rollout has zero intrinsic
reward. After posterior updates, hard-copy online to frozen for the next
rollout. For a closed window:

```text
s_w = clip((log q_frozen(Z|X,C,M) - log b_frozen(Z|C,M)) / log(3), -1, 1)
r_int(t in w) = beta * s_w / |w|
beta_on = 0.05
beta_off = 0.00
```

This detached signed reward enters only linked low rewards before low GAE. It
never enters high/event rows, event critic targets, KEEP/SET advantages, or
lifetime selection.

Window ownership:

- KEEP continues the window;
- SET closes the incumbent before the next primitive action;
- another member's event does not close a survivor window;
- temporary leave closes a partial window and freezes skill/hidden/position;
- rejoin opens a new window with restored skill and hidden state;
- terminal leave, episode terminal, and PPO truncation close the window;
- every low transition belongs to exactly one window and no window crosses a
  policy version.

### Runtime, Probability, RNG, and Checkpoints

- `ha_ctse_process/train.py` owns a distinct Iteration-5 branch; it does not
  widen the terminal Stage-C dispatch.
- Hierarchical arms reuse `batched_low_step`, `pack_event_ppo_data`, and
  `apply_event_ppo_update`.
- C3 reuses `DirectPrimitiveARPolicy`, `collect_direct_trajectory`, and
  `evaluate_direct_policy`; no duplicate recurrent PPO implementation exists.
- The only behavior-probability factors are the high categorical KEEP/SET token
  and low primitive action. Windows, posterior outputs, and intrinsic rewards
  add no likelihood factor.
- Sampling/replay use stored likelihoods. High time is owner-event time; low GAE
  and process windows advance only on focal active physical steps.
- Global checkpoint schema remains 3. Iteration 5 additionally requires nested
  `event_semantic_schema_version=1` state containing online/frozen posterior,
  posterior optimizer, readiness, semantic RNG, all ledgers, and intrinsic
  counters. Iteration-5 mode rejects absent/extra/wrong-version semantic state;
  other modes reject a semantic bundle.

### Formal Evidence Source

Runner: `scripts/run_iteration5_process_semantics.py`.

Parallel local-CUDA arms:

- `c1_semantic_on`: F0 shell, process posterior, `beta=0.05`;
- `c1_semantic_off`: byte-equal policy initialization and posterior exposure,
  `beta=0`;
- `c3_direct`: unchanged direct architecture on the same carrier.

Frozen learned-arm exposure:

| Field | Value |
|---|---:|
| seed family | 57057 / independent registered ledgers |
| environments | 16 per arm |
| horizon / rollout | 80 / 80 |
| outer updates | 250 |
| transitions | 320,000 per arm |
| PPO passes | 4 |
| high/low optimizer steps | 1,000 per hierarchy arm |
| posterior steps | 1,000 per hierarchy arm |
| direct optimizer steps | 1,000 |
| Adam learning rate | 3e-4 |
| gamma / GAE lambda | 0.99 / 0.95 |
| policy/value clip | 0.20 / 0.20 |
| entropy / grad clip | 0.01 / 0.50 |
| evaluation | exact update 0 and 250 only |

No best-checkpoint selection. C1 arms share initial policy and registered
environment/action streams until treatment changes trajectories. Posterior RNG
is isolated. C3 uses its registered independent model stream.

### Result Contract

M0 requires carrier/snapshot correctness, constructive/random bounds, finite
updates, exact budgets and optimizer counts, prohibited-field exclusion, zero
posterior-to-policy/high gradient, zero high intrinsic application, exact
high/low replay, on/off initial equality, semantic-off reduction, and strict
fresh/save/resume parity.

Material semantic evidence requires one held-out skill pair satisfying all:

```text
LCB95(same-input primitive-action TV) > 1/12
LCB95(12-step forced process-effect distance) > 1/12
each selected skill natural active-step share >= 0.10
held-out natural-to-forced overlap-margin LCB95 > 0
context/mask matched-shuffle residual LCB95 > 0
```

Task access for C1-on requires deterministic `U>=0.60`, `P>=0.55`, `S>=0.55`,
final-minus-zero utility LCB95 `>0.10`, and on-minus-off utility LCB95 `>0.03`.
C3 requires `U_det>=0.70`, `P_det>=0.65`, `S_det>=0.65`, `U_stoch>=0.60`, and
final-minus-zero utility LCB95 `>0.15`.

Priority-ordered mutually exclusive outcomes:

1. `INVALID_ITERATION5_IMPLEMENTATION` — repair only the concrete operational
   defect under the same contract.
2. `RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS` — carrier or C3 access fails;
   retire this carrier and make no C1 claim.
3. `FAIL_C1_NO_MATERIAL_SEMANTICS` — retire this exact posterior/reward/view;
   strengthen C3; C2 and credit stay closed.
4. `FAIL_C1_SEMANTICS_WITHOUT_TASK_VALUE` — record arbitrary diversity and do
   not integrate; C3 remains leader.
5. `PASS_C1_PROCESS_SEMANTICS` — promote C1 only at this testbed level and move
   to a load-bearing transfer/commitment comparison with C3 retained as null.

Any valid result closes this evidence source. No budget, seed, beta, window,
threshold, reward, model, task, or skill-count rescue is permitted.

### Exact Implementation Scope and Next Boundary

Implemented files:

- `ha_ctse_process/dynamic_roster_spatial_testbed.py`;
- `ha_ctse_process/process_semantics.py`;
- `ha_ctse_process/dynamic_roster_direct.py`;
- `ha_ctse_process/variable_roster_event.py`;
- `ha_ctse_process/train.py`;
- `scripts/run_iteration5_process_semantics.py`;
- `tests/ha_ctse_process_iteration5_process_semantics_test.py`.

Generic-SHORT, Stage-B/Stage-C result artifacts, original HMASD, Alice-Bob, and
retired mechanism files are out of scope.

The next permitted boundary is engineering-only: inspect the actual end-to-end
runner once under `MARL_ENGINEERING_PRINCIPLES.md`, implement accepted
efficiency fixes once, and inspect changed paths once. This must preserve every
scientific field above. A formal relaunch still requires explicit user
instruction and `$hmasd-experiment`.

### Accepted Engineering Refactor for the Authorized Relaunch

The controller accepted the following active-line replacement. No algorithm,
reward, sample, optimizer, exposure, threshold, model, seed, RNG stream, result
branch, or checkpoint schema changes.

1. `ProcessSemanticTrainer.update_posterior` owns all four registered posterior
   passes in one call. It invokes the existing balanced sampler four times in
   the original order, preserving the exact sampler-RNG advancement and one
   selected batch per optimizer step; it packs and transfers their concatenated
   tensors once, performs four ordered optimizer steps, and hard-copies online
   to frozen only after the fourth step. `train.py` invokes this interface once
   per rollout and retains the exact count of 1,000 posterior optimizer steps.
2. `scripts/run_iteration5_process_semantics.py` adds one seven-branch audit
   batch for the canonical order `skill 0 replica 0/1`, `skill 1 replica 0/1`,
   `skill 2 replica 0/1`, then natural replica 0. Each branch restores the same
   source checkpoint and retains its registered independent PCG64 state; equal
   replica indices retain common random numbers across skills. Twelve physical
   steps use the existing `batched_low_step`; recurrent state, membership,
   masks, environment transitions, and output layout remain branch-owned.
   Three same-input skill action distributions are also evaluated as one tensor
   batch.
3. `_evaluate_iteration5_spatial_model` constructs the registered evaluation
   episodes as one runtime batch and uses `batched_low_step` once per physical
   time. Environment transitions, membership transactions, recurrent state,
   action RNG and metric rows remain episode-owned and retain episode order.
4. The hierarchy arm builds and writes its full live checkpoint only at the
   existing `--save_interval` boundary and the final update, rather than every
   update. `latest.pt`, strict resume, final reload, semantic-v1 state, and the
   schema-3 payload remain unchanged; a recovery resumes from the latest saved
   registered boundary.

Write scope is limited to
`ha_ctse_process/process_semantics.py`, `ha_ctse_process/train.py`,
`scripts/run_iteration5_process_semantics.py`, and
`tests/ha_ctse_process_iteration5_process_semantics_test.py`. One focused check
must show that four-pass packing preserves sampler state, ordered optimizer
count, and final online/frozen state; batched evaluation and audit outputs must
match their scalar references under the registered episode/RNG/CRN schedules.
The controller then inspects the integrated execution path once and enters
`$hmasd-experiment` for the unchanged fresh formal run. The explicit 2026-07-19
instruction already satisfies the relaunch authority; it is not requested
again.

Focused acceptance evidence: four-pass posterior state/RNG equivalence,
batched-versus-scalar evaluation equivalence, seven-branch CRN equivalence, and
the reduced three-arm CUDA checkpoint/roundtrip path all passed in one focused
pytest selection (`4 passed`). Controller review also required replay maxima and
both isolation booleans to persist through the sparse live checkpoint, so a
resume cannot erase previously accumulated M0 evidence.
