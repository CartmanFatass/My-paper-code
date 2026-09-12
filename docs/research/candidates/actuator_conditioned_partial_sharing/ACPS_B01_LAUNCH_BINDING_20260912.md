# Exact ACPS-B01 launch inputs

DM `/root/dm_acps_start`, canonical `actuator_conditioned_partial_sharing`, `codex/acps` at `C:/Projects/HMASD-worktrees/codex-acps`. Root source integration `6d42661be` preserves original scientific source **2302072e2dcb7aa0c4ee2f71572ef8ca67cd9a46**. Both one-arm invocations use that detached source at `/home/wu/hmasd-worktrees/acps-b01-9101-20260912` on configured `hmasd-wsl-node`, Python `/home/wu/.venvs/hmasd/bin/python`, CPU FP32/thread1. Remote shared repo and unrelated artifacts are retained untouched.

The two committed LF payloads are [run_shared.sh](acps_b01_execution/run_shared.sh) and [run_acps.sh](acps_b01_execution/run_acps.sh). Stage them without modification under `/home/wu/hmasd-inputs/acps-b01-9101-20260912/`. The shell exports wall start before its adjacent `admit-memory && exec` command. Outer `/usr/bin/time` encloses shell start, admission, Python imports, training, sole-final evaluation, checkpoint/summary publication, last write/printing and actual process exit. It writes `process_wall_seconds.txt`; the runner's internal `elapsed_wall` is partial and is not substituted for this complete measurement.

SHARED whole-arm command (one Send to the existing supervisor):

```text
ssh hmasd-wsl-node /usr/local/bin/agent-task run acps-b01-shared-9101-20260912 /usr/bin/time -q -f %e -o /home/wu/hmasd-worktrees/acps-b01-9101-20260912/temp/directions/actuator_conditioned_partial_sharing/exp/acps_b01_9101/SHARED/process_wall_seconds.txt bash /home/wu/hmasd-inputs/acps-b01-9101-20260912/run_shared.sh
```

ACPS whole-arm command (separate fresh admission and private state; preselected regardless of SHARED score):

```text
ssh hmasd-wsl-node /usr/local/bin/agent-task run acps-b01-acps-9101-20260912 /usr/bin/time -q -f %e -o /home/wu/hmasd-worktrees/acps-b01-9101-20260912/temp/directions/actuator_conditioned_partial_sharing/exp/acps_b01_9101/ACPS/process_wall_seconds.txt bash /home/wu/hmasd-inputs/acps-b01-9101-20260912/run_acps.sh
```

Output roots are the respective SHARED/ACPS directories shown above; create those empty directories during staging so external timing can open its output before admission. This mkdir/staging work is support, not omitted or charged twice as native. SHARED then ACPS is a local one-arm sequence, without outcome selection or a global/sibling-result barrier. T retains priority only under actual contention. Exact transfer readback and shell syntax are checked without scientific execution. Before each launch the supervisor identity is reconciled to prevent duplicate acceptance; no retry budget exists.

Hard future limits are450 seconds for each whole arm,900 summed native,900 support and1,800 complete. A measured complete overrun is reported with its actual value and bounded scientific facts; no internal timestamp erases an outer tail. Unknown rates do not imply a known projection violation or require a cost pilot. No capability-permutation search, extra arm/fit/panel or shortened learner follows. Accepted handle facts are sent directly to the live Monitor endpoint; actual goal adoption is tracked separately from ADD delivery.

Root attributed the shared Portfolio discovery intake/registration/control application overhead once to ACPS support because this is the first newly registered funded direction. That shared item is **unknown**, not zero; MGTAP T and CADC exclude it. Existing Portfolio provider/author history remains unmeasured provenance, not a native charge or experimental balance. ACPS's own source/test/review/binding/staging/Monitor/collection/intake/cleanup costs remain separate support entries. Partial coverage cannot establish full support compliance or an unobserved breach.
