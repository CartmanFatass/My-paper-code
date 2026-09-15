# ACPS-B02 exact launch binding

Scientific source is `dd91ea3d81970485a8d562db47e30c70ed063524`, published on `codex/acps`. This binds exactly master9102 and the new450/900/600/1500 caps from the card. The B01 reference remains2302072e2; its old outputs, master and allowance are not reused. [Machine plan](acps_b02_execution/LAUNCH_PLAN.json) fixes both handles and argv.

Use configured remote `hmasd-wsl-node`, repository `/home/wu/projects/HMASD` and `zsh -lic` for network-dependent fetch/worktree preparation. Create exactly the detached worktree `/home/wu/hmasd-worktrees/acps-b02-9102-20260912` at the published source; exact wrappers are copied from that commit to `/home/wu/hmasd-inputs/acps-b02-9102-20260912`, with byte checks and `bash -n`. Prepare only the two empty output directories before the first launch.

## SHARED preselected whole arm

```text
ssh hmasd-wsl-node /usr/local/bin/agent-task run acps-b02-shared-9102-20260912 /usr/bin/time -q -f %e -o /home/wu/hmasd-worktrees/acps-b02-9102-20260912/temp/directions/actuator_conditioned_partial_sharing/exp/acps_b02_9102/SHARED/process_wall_seconds.txt bash /home/wu/hmasd-inputs/acps-b02-9102-20260912/run_shared.sh
```

## ACPS preselected whole arm

```text
ssh hmasd-wsl-node /usr/local/bin/agent-task run acps-b02-acps-9102-20260912 /usr/bin/time -q -f %e -o /home/wu/hmasd-worktrees/acps-b02-9102-20260912/temp/directions/actuator_conditioned_partial_sharing/exp/acps_b02_9102/ACPS/process_wall_seconds.txt bash /home/wu/hmasd-inputs/acps-b02-9102-20260912/run_acps.sh
```

Every wrapper starts the wall origin before adjacent memory admission, then execs the fixed B02 runner. The outer time receipt encloses admission/import/model/learning/sole-final evaluation/checkpoint/publication/readback and process exit. It is authoritative for whole-native cost; internal timing is partial. At most these two accepted scientific launches; first-arm score never drops or selects the companion. Each launch requires its own fresh actual-node physical/effective availability≥4GiB.

Actual source/command readback, launch acceptance, Monitor dispatch, actual goal adoption, terminal delivery and technical acceptance are distinct facts appended to execution. Current Monitor/Root/Relay endpoints are read from `C:/Projects/HMASD/.codex/hmasd-*.toml`; there is no source-frozen endpoint substitution or new monitoring service. Source/card and commands are published before launch.
