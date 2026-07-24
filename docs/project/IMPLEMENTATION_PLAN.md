# Continuous service roster proxy G17 implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
active_implementation=CONTINUOUS_SERVICE_ROSTER_PROXY_G17
design=docs/research/designs/CONTINUOUS_SERVICE_ROSTER_PROXY_G17.md
status=BOUNDED_PROTOTYPE_IMPLEMENTED_EXPLORATION_SCALE_SCREEN_ACTIVE
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

## Current discriminator

The source and implementation close operationally, but `initial_log_std=0`
plateaus after both 60 and 180 updates. Do not increase budget again. Run a
small fixed exploration-scale screen using fresh roots and the same code
identity:

- candidate A: `initial_log_std=-1.0`, `learning_rate=3e-4`;
- candidate B: `initial_log_std=-1.5`, `learning_rate=1e-3`.

Use 100 updates, eight environments, two PPO passes and 48 episodes per domain.
The registered experiment operator may execute each exact nonformal command in
parallel. The PM selects at most one passing candidate by held-out utility,
then mapping MAE/correlation; a tie selects the smaller learning-rate change.

## After the screen

- If no candidate passes, record `NO_BOUNDED_CONTINUOUS_ACCESS_G17` as a
  nonformal prototype disposition and derive a new algorithmic correction.
- If one candidate passes, freeze its complete train/evaluate/analyze evidence
  contract, implement only the missing formal runner/analyzer surface, run one
  bounded nonformal closure exercise, commit/push, then assign formal iteration
  18 to the fixed experiment operator.
- Only a valid formal result consumes an iteration and triggers
  `docs/report/ITERATION_18.md` in Chinese.

No current action promotes G17 to the heavy UAV environment.
