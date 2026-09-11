Claim: one task-isolated system-CPython environment can provide an importable candidate path with B04's recorded NumPy and Torch package versions.
Binding structure: systems / information flow.

# CBSC-SYSTEM-RUNTIME-A01 — A/RECON path preparation

Selected 2026-09-07 under object-tier standing delegation. This is execution
preparation for the existing opportunity-credit question; it does not measure
multi-agent partial observability or non-stationarity. Selection rationale and
handoff: `CBSC_SYSTEM_RUNTIME_A01_SELECTION_20260907.md`.

## Question and evidence ceiling

Can the already installed OS-supplied CPython 3.12 on wsl_4070 support the exact
recorded top-level dependencies in an isolated environment, without modifying
the shared research environment? Existing FRRIE inventory records system CPython
3.12.3 (GCC), without NumPy. B04 used the configured uv CPython 3.10.21 path;
its STRUCT invocation stopped before model creation. These facts motivate a
candidate execution path, not a diagnosis that uv, NumPy or the host caused B04.

Primary observable: actual candidate interpreter path/base build, installed
package versions and successful import of NumPy and Torch in that candidate.
No speed, stability, numerical-equivalence or native-return claim follows.
Headroom remains absent for the scientific host. Minimum change of interest is
one explicitly named importable candidate, rather than the currently incomplete
alternative. No native-return MEI applies to this readiness question; B04's 0.25
representation MEI is unchanged and its missing pair remains unscorable.

## Selected path and preserved boundaries

Use only the existing system CPython 3.12 on wsl_4070, expected through
`/usr/bin/python3`; record its actual executable/build. Create the single isolated
environment `/home/wu/.venvs/hmasd-cbsc-system312-20260907` with ordinary existing
environment/package tools. Keep the lexical virtual-environment Python path when
invoking it; do not replace it with its resolved base executable (the old r06
incident documents why those paths differ).

Resolve/install only binary distributions for **numpy==1.26.3** and
**torch==2.7.0+cu118**, plus their declared dependency closure. Use the existing
configured network route and official package indexes. Availability for this
interpreter is a measured readiness fact, not assumed. Record installed versions
and package origins. Do not silently substitute another version or CPU/CUDA build.

Do not alter `/home/wu/.venvs/hmasd`, system Python, .codex configuration, shared
source, or another direction's environment. Do not compile Python or packages,
install system packages, change hardware settings, or create a second candidate.
Preserve any partial environment and logs on failure. No automatic restart or
new allowance follows. Ordinary command/quoting corrections before acceptance
remain authorized and must not hide work already charged to this objective.

The sole verification imports the installed libraries and records metadata;
it may set Torch compute threads to one. It must not generate host tapes, invoke
B04 runners, create models/optimizers/checkpoints, draw scientific RNG samples,
train, evaluate policies, run a tensor benchmark, or replay any failed arm.
This is not a new B04 engineering check or permission to run either formal arm.

## Work, budget and execution

Dominant work: **one environment x one dependency resolution/installation x one
metadata/import observation**. Algorithm work is zero; host episodes, learned
transitions, optimizer steps and policy evaluations are all zero. Package
download/unpack work and the transitive dependency count remain unmeasured.
The existing wheel cache may reduce cost but is not assumed to do so.

One complete supervised preparation invocation has a **600-second total cap**,
including admission, environment creation, dependency resolution/download/unpack,
the metadata/import observation, output readback and termination grace. Freeze
the exact existing-tool command and output root in the CM record before launch;
use an outer cap that includes grace. There are no per-phase reset clocks.
Stop at successful metadata readback, a concrete dependency/access/version gap,
or the complete cap. This is a newly selected A allocation, not a B04 retry.

Use remote_first on wsl_4070. Commit/push the exact command record and any source
bytes first, then use a detached exact-SHA worktree and existing agent-task.
The actual-node memory preflight must immediately precede the command via `&&`
and pass both 4-GiB floors. It can use the existing system Python for this
stdlib-only admission script. CM owns direct technical observation/collection;
send the accepted handle to current Root under ROOT_OPERATIONS.md and the
current monitoring configuration, retaining observation until adoption ACK.

Engineering-scope section4 needs: **none**. Use existing tools and a short literal
command; no new environment manager, runner framework, retry loop, registry,
provenance guard or telemetry service. Ordinary source/runner limits apply if a
small committed helper is necessary. No standalone test suite or repeated smoke
is selected; the historical focused-test account is not reset.

## Reading rule and prediction

- **PATH_PREPARED:** the candidate exists and the pinned libraries import, with
  the actual paths/versions/build and complete outcome recorded. This supplies
  a candidate for a separately selected real comparison; it does not prove the
  old fault repaired or exclude a shared-host problem.
- **PATH_INCOMPLETE:** installation, exact-version availability, import, access
  or the complete cap prevents that result. Preserve the exact observed gap and
  partial state. Do not assign scientific polarity or automatically try another
  runtime/version/host.

DM prediction: the path is likely preparable, but package availability and total
installation cost are uncertain. Owner prediction: not taken (unattended).
Neither branch authorizes a B04 retry, a new training pair, an FRRIE invocation,
a lifecycle change or a claim about the cause of any historical failure.
