# Native crash investigation, 2026-09-08

Status: diagnosis incomplete; no production repair accepted. The owner's research
goal remains paused. This is engineering evidence, with zero learning steps and
zero new scientific exposure. Work was performed directly in the parent session.

## Preserved historical evidence

Nine existing WSL Python core dumps were preserved with hard links under
`/mnt/c/Users/wu/AppData/Local/Temp/hmasd-native-crash-20260908-preserved/`
on `hmasd-wsl-node`. No new crash was induced to obtain these dumps.
The following four system-Python dumps were inspected with offline GDB, automatic
loading and debuginfod disabled, and the matching CPython helper explicitly loaded.
No live process was attached to or started by GDB.

| Dump filename prefix (`wsl-crash-…-_usr_bin_python3.12-11.dmp`) | Identified historical process | Observed location |
| --- | --- | --- |
| `1788848678-2765962` | FRRIE A05 P27, source `43eec21e9584c83e5e8d940402d7e4570b454e59` | Interpreter `0x4960ac`, null R14; Python frame enters `SemanticRNGAddress.validate`, through tape generation |
| `1788848720-2766079` | CBSC B05 RAW P28, source `d2753be86c12bfa63c404ac2cac513b914371115` | Same interpreter address and null R14; Python frame enters `Enum.value`, through token validation and projection |
| `1788852523-2766940` | CBSC process, identified by its venv executable | Original signal frame at `list_iter+147` (`ret`); stack return value `0x0003000000000057`; Python frame could not be recovered |
| `1788856616-2768586` | FRRIE A07 P35, identified by frozen checkout path | Original signal frame again in interpreter cold code; Python frame enters `SemanticRNGAddress.validate` |

The latter two cores first show the faulthandler signal re-raise in libc; that is
distinct from the original signal frame below it. The CBSC return-stack anomaly
is evidence of invalid execution state, not identification of the writer or cause.

The executable is Ubuntu `python3.12` 3.12.3-1ubuntu0.16, build ID
`dc79f2c659038743f8f0c7ec18623284365df091`. Matching debug symbols were downloaded
as a package and extracted into the task input directory; no system package or
research environment was upgraded. The executable SHA256 is
`a92f0f95e883390c7256b2e441484aac06b1002dbe1d924141a77c8d82f96223`.
The inspected CBSC core's first ELF page matches the current executable's first
page, including the build ID. Executable text was not retained in that core's
PT_LOAD data; this is not a full historical text-byte comparison.

At `0x4960ac`, optimized source mappings disagree between a decref and the shared
unreachable CACHE cold path. The preceding target address equals opcode target
zero, while the current code object's first instruction is RESUME. This does not
identify the corrupting operation. A stripped-symbol approximation to
`PyErr_WarnExplicit` was misleading and must not be used as a cause.

In the inspected CBSC P28 core, the interpreter eval-frame override, trace/profile
callbacks, tracing flag and monitoring version are zero. This describes crash-time
state only. The host reports WSL kernel 6.6.87.2 and an i9-13900H. The owner reports
no hardware adjustments or other noticed crashes; the local WHEA query found no
matching events. Neither establishes or excludes a hardware cause.

## Bounded call-path discriminator

Source: `e55454c633faba6f3bb6cc6e574607821e684834`,
`tests/experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/test_call_dispatch.py`.
The test validates fixed records and Enum getters through a generator. It does
not load the project native ABI, generate scientific outputs, or instantiate a
model, optimizer or learner.

One invocation was accepted by `agent-task` as `native-call-dispatch-20260908`,
using detached source `/home/wu/hmasd-worktrees/native-call-dispatch-20260908`
at that exact commit and the historical FRRIE system-3.12 venv. The outer timeout
was 115 seconds plus a 5-second termination grace. Fresh memory admission passed
with 15,640,944,640 available bytes against the 4 GiB floor. Thread counts were one.

| Sequential stage in the same process | Iterations | Checksum | Stage wall seconds |
| --- | ---: | ---: | ---: |
| stdlib | 2,000,000 | 15,000,000 | 0.670946 |
| NumPy imported | 2,000,000 | 15,000,000 | 0.674132 |
| PyTorch imported, threads set to one | 2,000,000 | 15,000,000 | 0.691626 |

All passed with exit 0. Process elapsed time was 3.48 seconds and peak RSS was
375,344 KiB. Supervisor timestamps were 2026-09-08 15:39:32–15:39:35 UTC.
Trace and profile callbacks were inactive throughout. The successful test shows
that these simplified call patterns, with imports alone, are insufficient to
reproduce the historical failure. It does not clear the complete initialized
runtime or prove a production fix.

## Evidence locations and remaining gap

Raw GDB outputs for the four cores, the kernel excerpts, launch JSON, supervisor
log and time output are retained locally under
`C:/Projects/HMASD/temp/native-crash-repair-20260908/`. The supervisor retains its
original log at `/home/wu/.agent-tasks/native-call-dispatch-20260908/task.log`.
The checked-in companion `NATIVE_CALL_DISPATCH_LOG_20260908.txt` preserves the
complete short runtime receipt. Earlier static review found no concrete native
ABI signature or buffer-length mismatch at the inspected boundaries.

The missing acceptance evidence is a reproducible failing case tied to a specific
defect, followed by a passing affected-boundary check after its repair. Current
evidence supports neither a speculative project-code patch nor acceptance of an
interpreter/environment replacement. Historical failures remain failures. No
scientific card, budget, evidence polarity or continuation decision changes here.
