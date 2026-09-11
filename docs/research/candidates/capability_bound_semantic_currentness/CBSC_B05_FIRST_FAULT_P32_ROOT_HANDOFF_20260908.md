# CBSC B05 first-fault P32: Root handoff

**Preparation accepted; CM has not launched.** Root receives this handoff through
DM acceptance, executes the single bound observation, and notifies this same CM
at terminal for collection. There is no STRUCT, retry or extension.

## Frozen bindings and scope

[P32 card](CBSC_B05_FIRST_FAULT_P32_SCIENCE_CARD_20260908.md) at
`04254e7ffab87e8ea85024f6542d7b88fecb1cfd`; Portfolio assignment
`0c6bf8e175632098e46fcff1417d5d3c078962c9`.
Authoring checkout: `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`,
`codex/cbsc`, clean at entry. No source changes. Reuse DM's empty source diff and
P20 checks/review; no new runtime readiness suite or comparison batch.

Exact scientific source **d2753be86c12bfa63c404ac2cac513b914371115**, already in
`/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907`. Preflight **ec8866b3968fcb1566976ce405d7c552d4d9a5de** is present
unchanged. Interpreter `/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`, P17/P28 CPython 3.12.3 / Torch 2.7.0+cu118.
Same wsl_4070 CPU FP32, Torch1 and numeric-library limits. Fresh model/optimizer,
B1_RUN namespace and seed21223; RAW public host/adapters/rewards/credit, original
48x8 training/768Adam ceiling, update0/48 evaluations and three rule panels remain.
No checkpoint resume or output reuse. Artifact inner object stays B05; this P32
card, output root and supervisor handle distinguish the diagnostic.

New output parent: `/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908`; runner creates `raw/`, and adjacent admission
is `raw-admission.json`. Handle: `cbsc-b05-first-fault-p32-20260908`. Stderr, including any fatal report,
goes to the existing `/home/wu/.agent-tasks/cbsc-b05-first-fault-p32-20260908/task.log`. No separate fatal
file is promised, no core census is requested, and no signal is injected.

The sole observation option is startup `-X faulthandler` before the script.
[Python 3.12 documentation](https://docs.python.org/3.12/library/faulthandler.html)
confirms startup activation and default stderr reporting of fatal Python frames.
The page was read during preparation. It supports reported active call paths,
not a native C backtrace, corrupting writer or historical cause. No watchdog,
custom handler, profiler, source patch or package change is introduced. Scope:
one invocation's diagnostic reporting per card line150.

## Optional source inspection, never another probe

DM's source equality and existing execution checkout are already established.
Only if Root needs to recover checkout identity, this read-only literal prints
it and tracked state; it invokes no interpreter or admission and is not a new
currentness gate. No source fetch, staging or worktree creation is needed.

```python
import subprocess
subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hmasd-wsl-node', "/bin/bash --noprofile --norc -c '/usr/bin/git -C /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 rev-parse HEAD && /usr/bin/git -C /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 status --short'"], check=True)
```

## One detached launch, Root only after DM acceptance

This standalone local Python control-plane literal dispatches exactly once.
Admission is inside the same timed envelope and joined by `&&` to the runner.
The preflight creates its receipt parent; do not pre-create the fresh `raw/`.

```python
import subprocess
subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hmasd-wsl-node', '/usr/local/bin/agent-task run cbsc-b05-first-fault-p32-20260908 \'/usr/bin/time -f \'"\'"\'process_wall_seconds=%e peak_rss_kib=%M\'"\'"\' /usr/bin/timeout --signal=TERM --kill-after=5s 115s /usr/bin/env -u BASH_ENV -u ENV OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /bin/bash --noprofile --norc -c \'"\'"\'cd /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 && /home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908/raw-admission.json && exec /home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python -X faulthandler scripts/run_cbsc_opportunity_credit_b04.py --b05 --arm RAW-GRU --seed 21223 --output /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908/raw\'"\'"\'\''], check=True)
```

GNU time is outside timeout; TERM115 plus KILL5 encloses environment/shell setup,
admission, interpreter startup/imports, learning/evaluation, fatal reporting,
normal publication/readback and termination. Its stderr wall/RSS lands in task.log.
Configured timeout alone does not prove observed complete wall <=120s. Collect
outer time and supervisor terminal; internal runner wall cannot replace them.
The original full-RAW 159.38s planning reference may exceed this cap; P32's endpoint
is the first terminal/cap context, not forced learner completion. P28's39.83s is a
prior failed observation, not a forecast. Capture overhead is unknown and charged
inside the same cap. Schedule ceilings:384 train episodes/58368 transitions/
9216 decisions/768Adam,64 evaluations and96 rule passes; actual durable work may
be a strict prefix. One process exposure, zero new independent training seeds.

Root records actual accepted handle/PID/start/source/cwd/log/output/admission and
120s bound under the current goal-driven observation route. No automation is
created or reactivated. Root handles its own launch/adoption and remains observer;
notify `/root/dm_amx_cbsc_next/cm_cbsc_opportunity_b04` at terminal (or use
followup_task if idle), and DM `/root/dm_amx_cbsc_next`. Acceptance uncertainty
requires observing this same handle, never repeating the launch.

## Observation literal

Use the existing status command within Root's active goal; add logs only when
useful. It makes no learner call. A missing SSH response is uncertain observation,
not terminal success or permission to retry.

```python
import subprocess
subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hmasd-wsl-node', '/usr/local/bin/agent-task status cbsc-b05-first-fault-p32-20260908'], check=True)
```

## Terminal all-outcome collection, same CM

Run this standalone local Python literal only after terminal notification. It
retains status/log stderr and return codes, copies the output and supervisor
records, and continues collecting supervisor evidence if an output path is absent.
It runs no target interpreter, evaluator or pair reconstruction.

```python
import subprocess
from pathlib import Path
local = Path("C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906/temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908_collection")
local.mkdir(parents=True, exist_ok=True)
for command, filename in [("/usr/local/bin/agent-task status cbsc-b05-first-fault-p32-20260908", "status.txt"), ("/usr/local/bin/agent-task logs cbsc-b05-first-fault-p32-20260908 100000", "logs.txt")]:
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hmasd-wsl-node", command], capture_output=True)
    (local / filename).write_bytes(result.stdout)
    (local / (filename + ".stderr")).write_bytes(result.stderr)
    print(filename, result.returncode)
for remote in ["/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908", "/home/wu/.agent-tasks/cbsc-b05-first-fault-p32-20260908"]:
    print(subprocess.run(["scp", "-r", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hmasd-wsl-node:" + remote, str(local)]).returncode)
```

Read retained bytes only: actual terminal exit/signal/wall/RSS and admission;
first fatal report's frame text, filename/function/line when present; complete
JSONL prefix and last durable counters; initial/final artifact presence and
published identity/runtime/seed/summary if available. Unrecorded work beyond the
last complete row stays unknown. Copy partial evidence before classifying its
limits; missing primary files are not synthesized. Full copied task.log is the
fatal report path, even if the report is absent or truncated. No exhaustive dump
search, additional target import or signal-triggered collection is authorized.

Reading/stop, verbatim from the card:

> A location-bearing fatal stack supports only the active reported call path in
> this execution; it does not identify the corrupting writer or historical cause.
> A fatal event without a usable stack, a timeout or nonreproduction leaves the
> missing context unresolved and never clears P28 or authorizes a retry.
> A complete normal RAW output receives a separate validity review as diagnostic
> execution evidence; it does not replace P28 RAW or form its absent pair.
> Every outcome ends this allocation. Retain terminal facts and durable work;
> no repair, extra probe, STRUCT, new seed, repeat or extension follows.

Report the frame locations as operation context only, with source correspondence
when readable. A normal completion is retained for separate validity review; no
new pair or historical relabelling follows. CBSC and FRRIE causes/exposure remain
independent. CM writes RESULT_EVIDENCE, commits/pushes the explicit path and returns
to DM for diagnostic interpretation/prediction/intake/brief/audit; Root integrates.

## Preparation acceptance

Accepted static checks: all four standalone Python blocks AST-parse; shlex
round-trip confirms exact handle, source-cwd/runtime, startup flag position,
RAW/21223 arguments, adjacent admission and complete time/115+5 timeout ordering.
Local `C:/Program Files/Git/bin/bash.exe --noprofile --norc -n` accepted the whole
agent-task command, whole time/timeout payload and inner admission/runner shell
as three no-execution syntax inputs (exit0, empty stderr). Check command wall
1.014s. Receipt:
`temp/directions/capability_bound_semantic_currentness/exp/b05_first_fault_p32_20260908_control/syntax_acceptance.json`.
No new source review or scientific test was required; accepted P20 boundaries
are reused. No literal above has been executed during preparation. No target-
runtime/import/smoke/package/learner call occurred. These checks establish literal
syntax/bindings, not remote runtime success or a guaranteed fatal-stack capture.
