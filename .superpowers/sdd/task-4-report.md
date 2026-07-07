# R24 Task 4 Report

Commit target: R24 Team-Conditioned Individual q_d Probe module.

## Files changed
- `ha_ctse_process/team_conditioned_qd.py`
- `tests/r24_team_conditioned_qd_test.py`
- `.superpowers/sdd/task-4-report.md`

## Tests
- `& "C:\Users\wu\.conda\envs\SB3\python.exe" -m pytest tests\r24_team_conditioned_qd_test.py -q`

## Concerns
- `TeamConditionedQDProbe.losses` explicitly detaches `effect` and `condition`, satisfying the policy-graph isolation requirement.
- Metric fields are prefixed with `r24_qd_`; no reward/runner/CLI changes were made (diagnostic-only probe module).
