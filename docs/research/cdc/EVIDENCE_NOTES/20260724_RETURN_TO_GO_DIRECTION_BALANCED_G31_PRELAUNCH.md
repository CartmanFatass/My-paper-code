# G31 return-to-go direction-balanced formal prelaunch

```text
status=PRELAUNCH_READY
formal_compute_status=AUTHORIZED_BY_ACTIVE_USER_GRANT
iteration_consumed=false
backend=cpu
torch_threads=1
```

The active G30 formal runner and test were migrated to G31 rather than copied.
Twelve focused checks and the 60-check relevant G17/G18/G19/G30/G31 set pass
with the registered CPU interpreter and one thread. They close the frozen
configuration, fresh seeds, token, first-match precedence, checkpoint/cell
identity, RTG target and terminal-tail tamper rejection.

The integrated nonformal path exercise at
`logs/nonformal_return_to_go_g31_formal_path_20260724_9843e39_pm1` completed
train/evaluate/analyze with exit code zero from source
`9843e391bf5cd1fd3c79c248841d5fc4de6e410c`. It contains two training rows,
seven evaluation cells and four bound checkpoints. The analyzer reports
`operational_valid=true`, exact zero replay and terminal-tail errors, maximum
RTG target `19.5706863`, and the registered
`NONFORMAL_RETURN_TO_GO_FORMAL_PATH_EXERCISE_COMPLETE` branch. Re-running the
analyzer with `--require-formal` exits nonzero with
`formal analysis requires formal G31 artifacts`.

The next integrated source may run exactly one three-replicate formal CPU
iteration under token
`AUTHORIZE_RETURN_TO_GO_DIRECTION_BALANCED_G31_FORMAL_CPU_V1`. Any valid
registered branch consumes iteration 21 and closes the package without rescue.
An operational failure consumes no iteration and permits only a separately
accepted execution repair, not a scientific change.
