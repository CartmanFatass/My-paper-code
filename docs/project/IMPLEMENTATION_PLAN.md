# Continuous service roster proxy G17 implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
active_implementation=CONTINUOUS_SERVICE_ROSTER_PROXY_G17
design=docs/research/designs/CONTINUOUS_SERVICE_ROSTER_PROXY_G17.md
status=RESIDUAL_REPRESENTATION_PASS_PPO_FAIL_ACTIVE_COUNT_CURRICULUM_ACTIVE
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=18
iterations_remaining=10
formal_contract=not_frozen
formal_compute=not_running
```

## Implemented active line

1. `continuous_roster_policy.py` provides one capacity/action-dimension generic
   tanh-Gaussian policy. UAV G1 now wraps the same core with its unchanged
   eight-member/four-action defaults; focused equivalence tests protect that
   shared surface.
2. `continuous_service_roster_proxy_g17.py` owns the new 48-step toy ledger,
   environment, observations, reward, constructive oracle, batched collection,
   exact replay and PPO.
3. `run_continuous_service_roster_proxy_g17.py` owns bounded nonformal screens,
   current-demand mapping diagnostics and one nonformal checkpoint. It has no
   formal mode or conclusion-bearing analyzer yet.
4. The focused test proves capacity-generic shapes, inactive exclusion,
   deterministic source reconstruction, exact roster schedule, constructive
   access, exact replay, lifecycle freeze and one finite update.

## Closed PPO discriminator

The source and implementation close operationally, but `initial_log_std=0`
plateaus after both 60 and 180 updates. Two fixed exploration-scale variants
also fail conditional access:

- candidate A: `initial_log_std=-1.0`, `learning_rate=3e-4`;
- candidate B: `initial_log_std=-1.5`, `learning_rate=1e-3`.

Each used 100 updates, eight environments, two PPO passes and 48 episodes per
domain. Both return `NONFORMAL_G17_NOT_PROMISING`; no third hyperparameter
variant is admissible.

## Current discriminator

The base representation probe returned `0.00100230` and is not accepted against
the exact `<=1e-3` gate. Add the optional current-observation linear residual
to the action mean and rerun the same representation-only constructive mapping
probe for 200 optimization steps. If final full-dataset MSE is at most `10%` of
initial MSE and at most `1e-3`, run one RL screen with the residual,
`initial_log_std=-1.0`, learning rate `1e-3`, 100 updates, eight environments
and two PPO passes. Otherwise retire the continuous policy realization.

The residual probe passes, but that exact RL screen returns only `0.6583888`
joint utility and `0.0078801` gain with negative demand correlations. It is
closed. Run exactly one active-count curriculum screen with the same total 100
updates: 25 singleton, 25 small-dynamic and 50 registered-dynamic updates. Keep
the residual, `initial_log_std=-1.0`, learning rate `1e-3`, eight environments,
two PPO passes and the existing screen gates.

## After the screen

- If the representation probe passes, derive and screen exactly one
  team-credit correction; do not freeze the failed token-wise PPO path.
- If a later bounded RL candidate passes, freeze its complete train/evaluate/analyze evidence
  contract, implement only the missing formal runner/analyzer surface, run one
  bounded nonformal closure exercise, commit/push, then assign formal iteration
  18 to the fixed experiment operator.
- Only a valid formal result consumes an iteration and triggers
  `docs/report/ITERATION_18.md` in Chinese.

No current action promotes G17 to the heavy UAV environment.
