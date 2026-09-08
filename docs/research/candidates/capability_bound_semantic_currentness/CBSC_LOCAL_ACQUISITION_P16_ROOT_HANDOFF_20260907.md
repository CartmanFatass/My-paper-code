# CBSC P16 command preparation and future Root handoff

Engineering command preparation is complete and independently reviewed. No
acquisition or candidate invocation is allocated or executed by this document.
The exact future literal below binds the accepted, pushed source commit.

## Delivered surface and preserved inputs

Card: [Question, primary observable and reading / Named engineering scope and stop](CBSC_LOCAL_ACQUISITION_P16_SCIENCE_CARD_20260907.md).
Contract: [P16 code specification, sections 2-7](CBSC_LOCAL_ACQUISITION_P16_CODE_SPEC_20260907.md).
Authoring checkout: `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`, branch
`codex/cbsc`, tracked-clean start `a3e3c2cba713bc1eda1f18e327f6f188bd16317b`.
Root explicitly released normal production work: the three comparison captures
were exhausted before P16, so this task is not another comparison arm.

Owned files are the new `scripts/run_cbsc_local_acquisition_p16.py`,
`experiments/candidates/capability_bound_semantic_currentness/local_acquisition_p16/`,
its mirrored test directory, and this handoff. Old runners, cards, retained data,
preflight, shared configuration and other writers' paths are unchanged.

The source retains all 21 container names, all 23 install pins and the metadata
acceptance expression from the sole command at
`71131d728a0b5f04663301e3d838e699ce70af41`. Only descriptive object/source/seed
fields change in metadata. Preflight source remains separately bound to
`ec8866b3968fcb1566976ce405d7c552d4d9a5de`. FRRIE metadata at
`aa44d72ec78ee537671012b21202dc315258542f` remains input evidence, not received bytes.

Two complete GETs run sequentially through the existing Windows .NET HttpClient:
Torch 955455844 bytes, then Triton 156503769 bytes, at the exact card URLs.
Proxy, redirects, cookies and credentials are disabled; default TLS validation
is retained. No retry, range, resume, alternate URL or new hash gate exists.
Complete files are streamed sequentially through the configured SSH route to a
bounded receiver; an incomplete stream retains its partial files and never starts
setup. This uses SSH input streaming so no unbounded scp server is introduced.

The remote setup is one fresh system-Python venv, 21 links to the retained A03
containers, one offline full-resolution 23-pin uv install, and one original
NumPy/Torch metadata program with JSON publication/readback. No target import is
used for preparation tests. Thread-limit environment variables remain one.

## Deadline, process ownership and observation

The local origin is captured at runner entry before task imports, CLI parsing,
job creation or clients. All subsequent task work, including local admission,
clock mapping, downloads, transfer, remote admission/setup, metadata and collection,
is charged to that origin. Work stops at 540 s; complete publication/termination
has the original 600 s bound. The final command result records whole elapsed time,
phase, exit/uncertainty, handle and whether primary metadata was actually collected.

Windows child creation uses `STARTUPINFOEX` with the job-list attribute, atomically
assigning the suspended worker to a non-inheritable kill-on-close JobObject. It
then resumes the worker. The sole job handle stays in the controller. Timeout,
normal return or controller loss kills the worker and its descendants, including
PowerShell and SSH. A one-shot in-process 600 s timer also covers controller
publication. It is not a watcher process, loop or service.

Clock domains are seconds on local Windows `time.monotonic()` and remote Linux
`CLOCK_BOOTTIME`. They are never treated as a common epoch. One remote clock sample
is bounded by the existing 1 s timeout command and predates receipt on Windows.
The remote work deadline is sample + `(local remainder at receipt - 1) / 1.01`.
This conservatively charges both transit legs, every earlier local phase and later
dispatch/start delay. Remote phases retain that same absolute BOOTTIME deadline;
they never convert it by adding a stale remainder to a later clock sample.
The sampled boot identifier distinguishes clock domains after a node restart.

Assumptions: local monotonic seconds measure the complete wall bound. Across the
two elapsed clocks, maximum rate / minimum rate is at most 1.01 during the
invocation, with ordinary OS timer scheduling; suspended VMs/hosts or a
clock-domain restart are unsupported. This is a relative-rate bound, not a
separate plus/minus 1% allowance for each clock. No synchronized wall-clock
epoch is assumed.
A detected restart or exhausted deadline starts no next phase and cannot produce
readiness. These are timing limits of this route, not extra candidate probes or
launch gates. Acquisition throughput and installed-runtime readiness remain unknown.

On Linux, a task-local POSIX one-shot timer uses absolute CLOCK_BOOTTIME expiry.
The receiver has no child. The supervisor and tmux clients have direct timeouts.
Only detached setup creates a task process group; its children remain in that
group, and return/failure/work timeout sends SIGKILL to the group. Alarm delivery
is masked only across child creation and ownership registration, then unmasked.
The helper timer also covers terminal/readback/publication and kills an owned
child/group on expiry. HUP is ignored by these bounded helpers so local SSH loss
does not remove the timer. Controller/collection publication expires at the
propagated work deadline + 59 s, within the original 60 s margin.

The existing `agent-task` supplies the detached setup handle. A bounded blocking
`tmux wait-for` notification collects its terminal record and primary JSON; no
polling service or Root monitor is added. SSH success alone is insufficient.
Remote nonzero, missing metadata, `metadata_matches` false, timeout, failed body,
or failed collection remains incomplete. Unknown dispatch acceptance retains the
same handle and deadline; it never retries or reports cancellation from client loss.

## Prospective bindings (not an execution allocation)

Command source: `5828af584c5f5e6764f5a44c9951473d82bf04ad` (pushed on `codex/cbsc`).
Local cwd: `C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`.
Root separately provisions exact committed source at the remote cwd below before
any later selected invocation. P16 performed no source staging or actual admission.
The fixed literal uses the accepted full command-source SHA, independently of
the unchanged preflight binding.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' 'scripts/run_cbsc_local_acquisition_p16.py' `
  --seed 0 --source '5828af584c5f5e6764f5a44c9951473d82bf04ad' `
  --out 'temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_20260907' `
  --powershell 'C:/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe' `
  --ssh 'C:/WINDOWS/System32/OpenSSH/ssh.exe' --ssh-target 'hmasd-wsl-node' `
  --remote-python '/usr/bin/python3' `
  --remote-repo '/home/wu/hmasd-worktrees/cbsc-local-acquisition-p16-20260907' `
  --remote-out '/home/wu/hmasd-worktrees/cbsc-local-acquisition-p16-20260907/temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_20260907' `
  --candidate '/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907' `
  --retained '/home/wu/hmasd-worktrees/cbsc-system-runtime-a03-20260907/temp/directions/capability_bound_semantic_currentness/exp/system_runtime_a03_20260907/wheels' `
  --uv '/home/wu/.local/bin/uv' --supervisor '/usr/local/bin/agent-task' `
  --tmux '/usr/bin/tmux' --handle 'cbsc-local-acquisition-p16-20260907'
```

Node `wsl_4070`; system CPython 3.12.3 is the candidate interpreter input.
Only the .NET acquisition component is Windows-specific. The remote setup uses
its existing uv/runtime and unchanged preflight. The two downloaded body paths
are 194 and 211 characters in the named local checkout; neither requires a changed
machine path policy. All machine-specific paths are arguments, not runner constants.
Helpers locate their own source from their own `__file__`.

## Focused acceptance and independent review

The original specified pytest command initially reported 1 pass and 12 setup
errors in 0.65 s because its basetemp parent did not exist. Creating that ignored
test parent and repeating the same command yielded 13 passes in 2.68 s.

Initial independent review found four material issues: a BOOTTIME-to-monotonic
read-order reset, non-atomic Windows job assignment, multiple remote groups, and
unbounded remote publication. The corrections use the original BOOTTIME deadline,
atomic Windows job-list creation, one setup group, and absolute helper timers.
A later fixture-only run had two Windows MAX_PATH fixture failures (16 other
passes, 3.08 s); replacing those unnecessary file/link operations with the specified
fake link boundary retained all 21 names and removed the platform-irrelevant failure.
The corrected original suite passed 18 cases in 3.04 s before final review.
Final original checks: 18 passed in 2.84 s (command wall 3.344 s), CLI help passed,
and staged/full diff whitespace checks passed. Raw output:
`temp/directions/capability_bound_semantic_currentness/exp/local_acquisition_p16_preparation_20260907/pytest_final.txt`.
Independent native reviewer `review_p16` resolved all four original code findings. Its
remaining documentation finding corrected a too-wide individual-clock allowance
to the actual relative-rate assumption above. The same reviewer then confirmed
that no material findings remain within the declared assumptions. CM inspected the complete staged diff
and accepts P16 code conformance under those stated limits.

The tests execute inert local child/grandchild processes, fake request/transfer/
installer boundaries and small fixture bytes. They cover lost local controller
both before resume and after descendants start, timeout cleanup, an independently
bounded fake remote process after client loss, scheduling delay, expired phases,
partial first body/transfer failure, exact inputs/setup argv and primary readback.
Actual Linux process-group/POSIX-timer execution, real supervisor behavior, body
acquisition, install and target imports are not established by these Windows fixtures.
Independent source review supplies the Linux boundary inspection; this preparation
makes no empirical readiness or throughput claim.

Accepted source count: 764 non-test lines, 91 runner lines;
the five suite invocations total 12.29 s of reported pytest time, below 300 s.
Orchestration dominates this explicit command task; it is reviewed for concrete excess rather than ratio alone.
Engineering-scope section 4 additions are the task-specific multi-node/process
and minimal phase/deadline control expressly named by P16 card lines 92-95.
No other machinery is added. Current real exposure is zero network requests/body
bytes, candidate creations, installations, target imports, probes or scientific calls.

Return route: DM accepts code/card conformance; Root integrates the named commits;
DM may then request the prospective invocation and Portfolio supplies any allocation.
Neither this source nor fixture success launches or reuses an earlier allowance.
