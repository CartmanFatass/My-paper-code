# Continuous service roster proxy G17

Status: bounded prototype implemented; exploration-scale discriminator active;
formal evidence contract not yet frozen.

## Scientific question

Can the accepted active-set sum, `log1p(active_count)`, lifecycle-owned
recurrence and active-fraction autoregressive prefix support a freshly trained
continuous primitive controller under within-episode roster changes?

G17 is an absolute-usability probe. It does not compare against another
algorithm and does not claim UAV efficacy. A positive result only licenses a
later physical promotion candidate.

## Independent source boundary

G17 is not a rerun or repair of the retired Iteration-5 spatial carrier:

- the action is a continuous two-coordinate service allocation, not
  left/stay/right;
- the observation has ten freshly named current-service fields, not the old
  fifteen-channel spatial/Generic-SHORT layout;
- the reward is dense two-service target error, not persistent/short terminal
  utility;
- the horizon is 48 with roster counts changing at steps 12, 24 and 36;
- every checkpoint is trained from scratch; G8 and spatial checkpoints are
  forbidden imports.

The source uses three training schedules (`4->3->6->5`, `5->3->7->6`,
`6->4->8->6`) and two held-out schedules (`3->2->5->4`, `6->3->8->5`). A
temporary leave freezes the same lifecycle row, rejoin restores it, fresh join
starts a zero row, and terminal leave ends its physical action exposure.

Each step exposes the current load, service mix, active count, lifecycle age,
previous executed allocation and anonymous current capability. It never
exposes future membership keys, event times or future demand. The registered
constructive action maps current load and mix directly into the continuous
support and reaches utility one up to float32 arithmetic.

## Algorithm and implementation boundary

The environment-neutral shared core is
`ha_ctse_process/continuous_roster_policy.py`. It computes member embeddings,
active-set context and critic input once per step, then retains the causal
autoregressive loop only for focal lifecycle state and normalized action
prefix. Inactive rows receive zero action/log-probability and no hidden-state
update.

The G17 carrier, collection, exact teacher replay, GAE and PPO are isolated in
`ha_ctse_process/continuous_service_roster_proxy_g17.py`. UAV physics, workers,
communication calculations and scenario rewards are absent.

The first two nonformal runs used `initial_log_std=0`, learning rate `3e-4`,
eight environments and two PPO passes. Sixty and 180 updates both plateaued at
joint deterministic utility about `0.666`, despite a zero-to-final gain about
`0.174`, exact replay and constructive utility about one. Increasing exposure
alone is therefore rejected.

## Completed exploration-scale discriminator

Two fresh variants held the source, representation, network, reward, seeds,
screen gates and evaluation fixed. Neither crossed access. Their conditional
effort correlations were `0.0166` and `0.0228`; mix correlations were `0.1131`
and `0.1748`. Both learned near-constant actions. More budget and additional
exploration-scale tuning are closed for this prototype.

This screen consumes zero conclusion-bearing iterations. A formal contract may
be frozen only if one bounded variant passes all of:

```text
source_control_minimum_utility >= 1 - 2e-7
maximum_replay_error <= 1e-6
finite_updates = true
iid_mean >= 0.80
heldout_mean >= 0.75
final_minus_zero_joint >= 0.08
```

Screen thresholds are selection diagnostics, not formal result gates. The
current continuous-PPO realization is `NO_CONDITIONAL_PPO_ACCESS_G17_V1`.

## Active representation discriminator

Fit the same network directly to the constructive current-action mapping while
holding observations, active masks and architecture fixed. This non-RL probe
answers only whether the representation can express and optimize the mapping.
It cannot establish task access. Passing isolates shared team-reward PPO/credit
as the next algorithm boundary; failing retires the representation. The base
path returned `0.00100230` against the exact `1e-3` absolute gate and is not
accepted.

The active bounded correction adds a learned current-observation linear
residual to the action mean. It is environment-neutral, optional, and disabled
for UAV G1, so the accepted shared recurrent mechanics remain unchanged. The
same 200-step probe and thresholds apply without modification.

The residual passes representation fit but fails its sole PPO screen, so it is
not a formal candidate. The active correction is a fixed active-count
curriculum using the same residual policy and total 100 updates:

```text
singleton_static_updates=25
small_dynamic_2_to_1_to_3_to_2_updates=25
registered_dynamic_updates=50
```

Training reward, observation, action distribution, model, seeds, final IID and
held-out evaluation and every screen threshold remain unchanged. Curriculum
success would support a staged learning-path hypothesis only; it would not
establish comparative advantage or UAV transport.

## Protected interpretation

- G8-G16 and the retired spatial carrier remain closed exactly as recorded.
- G17 cannot be called UAV, S7-S1, arbitrary-N, advantage, skill-lifetime or
  intrinsic-reward evidence.
- CPU-only, one thread; no CUDA comparison or mixed-backend resume.
- The two completed nonformal screens are diagnostic artifacts and consume no
  iteration.
