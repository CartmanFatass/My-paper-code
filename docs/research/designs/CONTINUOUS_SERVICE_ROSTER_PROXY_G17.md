# Continuous service roster proxy G17

Status: formal executable definition frozen for Iteration 18; formal result not
yet run.

## Scientific question

Can one freshly trained, capacity-generic recurrent policy learn a
demand-conditioned continuous service allocation while the active roster
changes inside an episode, when policy credit is aligned to the source's
immediate service objective?

This is an absolute-usability question. It does not compare algorithms and does
not establish UAV, S7-S1, arbitrary-N, skill-lifetime or intrinsic-reward
performance.

## Independent source boundary

G17 is not a rerun or repair of the retired Iteration-5 spatial carrier:

- two continuous service coordinates replace left/stay/right;
- ten fresh current-service observation fields replace the old spatial layout;
- dense mean step utility replaces terminal persistent/short utility;
- the horizon is 48 with roster edits at steps 12, 24 and 36;
- all checkpoints are fresh; spatial, G8 and UAV checkpoint import is forbidden.

Training profiles are `4->3->6->5`, `5->3->7->6` and `6->4->8->6`.
Held-out profiles are `3->2->5->4` and `6->3->8->5`. Temporary leave freezes
the lifecycle row, rejoin restores it, fresh join starts a zero row, and
terminal leave ends physical action exposure. Current load and service mix are
observed; future demand, membership keys and event times are not.

The constructive current action is
`effort=2*load-1, mix=2*target_mix-1`. It must retain per-step utility at least
`1-2e-7` and exact registered roster schedules.

## Frozen algorithm

```text
algorithm=CURRENT_OBSERVATION_RESIDUAL_ONE_STEP_CREDIT_G17
shared_representation=active_set_sum_plus_log1p_count
lifecycle_state=per_member_GRU_row
autoregressive_context=active_fraction_action_prefix
continuous_distribution=tanh_Gaussian
current_observation_residual=true
credit_gamma=0.0
gae_lambda=0.95_irrelevant_when_gamma_zero
hidden_dim=32
learning_rate=1e-3
initial_log_std=-1.0
active_count_curriculum=false
```

The linear residual exposes the already-observed current demand directly to the
action mean. `gamma=0` makes the PPO advantage equal current reward minus
current value. This is an algorithm/source credit choice: independent future
demand is no longer assigned to the current action. It changes neither source
reward nor evaluation return and is not automatically transferable to a
long-horizon UAV objective.

Inactive rows retain hidden state and receive exactly zero action and
likelihood. Teacher replay must retain every log probability, joint log
probability, value, hidden row and autoregressive prefix within `1e-6`.

## Formal evidence contract

```text
authorization_token=AUTHORIZE_CONTINUOUS_SERVICE_ROSTER_G17_FORMAL_CPU_V1
backend=cpu
torch=2.7.0+cpu
torch_threads=1
replicates=3
updates_per_replicate=100
environments_per_update=8
ppo_passes=2
evaluation_episodes_per_domain=128
bootstrap_repetitions=10000
model_seed_base=1817000
train_ledger_seed_base=1827000
action_seed_base=1837000
evaluation_ledger_seed_base=1847000
evaluation_action_seed_base=1857000
bootstrap_seed=1867017
```

Each replicate evaluates paired zero/final checkpoints deterministically on IID
and held-out profiles. Final held-out stochastic utility is diagnostic. The
formal estimands are hierarchical-bootstrap 95% intervals over replicate and
episode for final IID utility, final held-out utility, and paired held-out
`final-zero` gain; held-out replicate minimum; and per-replicate deterministic
effort/mix correlations and mean absolute errors.

The registered first-match branches are:

1. any artifact, source, runtime, schedule, replay, finite-update, checkpoint or
   inventory failure -> `INVALID_CONTINUOUS_SERVICE_ROSTER_G17`;
2. IID utility CI lower bound `<0.90` ->
   `NO_IID_ACCESS_CONTINUOUS_SERVICE_G17`;
3. held-out utility CI lower bound `<0.90` ->
   `NO_HELDOUT_ACCESS_CONTINUOUS_SERVICE_G17`;
4. minimum effort or mix correlation `<0.90`, or maximum effort or mix MAE
   `>0.05` -> `NO_CONDITIONAL_MAPPING_CONTINUOUS_SERVICE_G17`;
5. paired held-out gain CI lower bound `<=0.10` ->
   `NO_LEARNING_GAIN_CONTINUOUS_SERVICE_G17`;
6. minimum held-out replicate mean `<0.85` ->
   `UNSTABLE_CONTINUOUS_SERVICE_ROSTER_G17`;
7. otherwise -> `USABLE_ONE_STEP_CONTINUOUS_ROSTER_G17`.

Lower-precedence diagnostics never rescue or relabel an earlier branch.
Nonformal exercise artifacts always return
`NONFORMAL_CONTINUOUS_SERVICE_G17_EXERCISE_COMPLETE` and the formal analyzer
must reject them.

## Selection evidence and interpretation guard

The sole `gamma=0` screen reached IID `0.944228`, held-out `0.936913`, joint
`0.940571`, minimum episode `0.893811`, gain `0.290062`, effort correlation
`0.988565`, mix correlation `0.991414`, and both MAEs below `0.019`. Replay
errors were exactly zero and constructive access remained effectively one.
This licenses the formal contract; it is not itself conclusion-bearing.

A positive formal branch supports a usable conditional controller only for the
registered immediate-service toy source. UAV promotion remains a separate PM
decision based on this evidence and the physical source mismatch. Every earlier
G0-G16 result remains closed and unchanged.
