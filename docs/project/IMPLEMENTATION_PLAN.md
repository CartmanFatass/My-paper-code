# Continuous service roster G17 implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
active_implementation=CURRENT_OBSERVATION_RESIDUAL_ONE_STEP_CREDIT_G17
design=docs/research/designs/CONTINUOUS_SERVICE_ROSTER_PROXY_G17.md
status=FORMAL_RUNNER_IMPLEMENTED_FOCUSED_TESTS_PASS
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=18
iterations_remaining=10
formal_contract=frozen
formal_compute=not_running
```

## Accepted active line

1. `continuous_roster_policy.py` is the capacity/action-dimension generic
   tanh-Gaussian active-roster policy. The G17 model enables its optional
   current-observation residual; UAV G1 retains its unchanged default.
2. `continuous_service_roster_proxy_g17.py` owns the independent 48-step toy
   ledger, environment, constructive oracle, collection, replay and PPO.
3. `run_continuous_service_roster_proxy_g17.py` is now the only G17 runner. It
   owns fresh train/evaluate/analyze checkpoints, CPU/runtime/source closure,
   hierarchical intervals, mapping diagnostics and first-match result logic.
   The superseded screen/probe/curriculum CLI is deleted; its artifacts remain
   evidence in `logs/` and Git history.
4. The focused suite proves generic masking, the exact residual parameter delta,
   constructive source access, lifecycle/replay invariants, one-step credit,
   finite PPO, first-match precedence, nonformal closure, formal rejection and
   source-identity fail-closed behavior.

## Prelaunch sequence

1. Commit and push the frozen implementation and contract.
2. Through the fixed `hmasd-experiment-operator`, run one fresh bounded
   `exercise` from that commit. Accept only three complete manifests,
   operational validity and the nonformal branch; then confirm the formal
   analyzer rejects it.
3. Record the prelaunch evidence and integrate it. No scientific iteration is
   consumed.
4. Assign formal Iteration 18 to one fixed experiment operator with the exact
   integrated source, fresh run root and these commands in order:

```text
python scripts/run_continuous_service_roster_proxy_g17.py train --run-root <root> --source-commit <commit> --formal --authorization-token AUTHORIZE_CONTINUOUS_SERVICE_ROSTER_G17_FORMAL_CPU_V1
python scripts/run_continuous_service_roster_proxy_g17.py evaluate --run-root <root>
python scripts/run_continuous_service_roster_proxy_g17.py analyze --run-root <root> --require-formal
```

Only a valid formal analysis consumes Iteration 18. The Project Manager then
writes `docs/report/ITERATION_18.md` in Chinese, integrates the closure, and
selects the next in-grant toy-first boundary. Heavy UAV execution remains
forbidden unless the formal evidence justifies promotion or a later question is
intrinsically physical.
