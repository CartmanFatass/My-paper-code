# Compute routing — which machine runs what

This project has **more than one machine**. Until 2026-07-27 every instruction
assumed one, and the assumption cost a wrong decision: an apparatus-verification
run was launched on the shared workstation while a GitHub Actions vehicle sat
idle and free. Nothing in the instructions was violated. Nothing in them applied.

The old rule answered *is the box free* (`scripts/check_compute_free.ps1`). It
never answered **which machine should this run on**, so the default was always
local. That question is answered here.

The Project Manager routes every unit of compute. It is a decision, never a
question to the user.

## Classify the work first

| Class | What it is | Machine |
|---|---|---|
| **Conclusion-bearing** | Output can appear in the paper — a formal run, a registered audit, anything pooled as a result | **Cloud**, once authorized |
| **Apparatus verification** | Proves the instrument behaves — determinism proofs, byte-identity comparisons, conformance checks, benchmarks | **Cloud** |
| **Development feedback** | Focused tests, smoke exercises, reproducing one failure, a bisect | **Local** |
| **Interactive diagnosis** | Anything where you read the output and immediately decide the next step | **Local** |

The split is latency against contention. Local buys a fast loop; cloud buys
parallelism and costs nothing on a public repo. Work you will not read for twenty
minutes has no business competing for local cores.

**The common error is running class 2 locally** because it feels like testing.
Ask instead: *am I going to read this output within the next few minutes?* If no,
it goes to the cloud.

## The workstation is shared

Another research line runs formal training on the same box. It is not this
session's and must not be touched.

Before any local run over a few minutes: check for foreign processes, and record
what you find by pid, script and run root. Label your own runs so the other line
can do the same. `scripts/check_compute_free.ps1` still answers the *is it free*
half; it does not authorize the local choice, it only confirms the machine can
take one you have already justified.

A shared box also makes local wall-clock a **noisy lower bound**. Never register
a timing number measured against foreign load.

## Cloud vehicle

GitHub Actions, `.github/workflows/d7s-audit.yml`, public repo, minutes are free.

**Tags are the trigger, not a convenience.** `workflow_dispatch` only works once
the workflow file is on the default branch (`new-test`); work scoped to another
branch cannot use it. A tag push runs from the tagged commit on whatever branch
it lives on, and a tag is not a branch, so tagging respects branch scope exactly.

```bash
git tag d7s-benchmark-<n> && git push origin d7s-benchmark-<n>   # measure s/step
git tag d7s-workers-<n>   && git push origin d7s-workers-<n>     # determinism proof
git tag d7s-audit-<n>     && git push origin d7s-audit-<n>       # formal sharded run
```

Constraints that decide job shape:

- **6 h hard kill** per hosted job. Jobs stop at 355 min so an overrun is a clean
  failure with the log intact rather than an abrupt kill.
- **An overrun is recoverable.** A topology cannot be split, but it can be re-run
  whole and pooled afterwards, because the pooler keys on the seed set rather
  than run identity. With `fail-fast: false` the surviving shards keep their
  artifacts, so a slow shard costs wall clock, not the run.
- **Concurrency is limited.** Only about 5 of 8 matrix shards execute at once, so
  wall clock is roughly two waves regardless of per-shard speed. Do not model a
  sharded run as fully parallel.
- **The runner is ~1.4× slower than local** (0.0864 vs 0.0615 s/step, measured
  2026-07-27, run 30245735762).
- **Unpushed work is invisible.** The runner checks out the tagged commit. Push
  before tagging, always.
- **Dependencies:** `requirements_d7s_audit.txt` only. Never
  `requirements_sb3.txt` — it is a cu118 CUDA lock from a different machine, and
  the audit imports neither torch nor stable-baselines3.

A self-hosted runner on a cloud VM removes the 6 h ceiling and is the better
vehicle if several shards come back near it.

## Authorization is separate from routing

Routing says *where*. It never says *whether*.

- **Formal compute authority is the user's.** Routing a run to the cloud does not
  authorize it.
- **A conclusion-bearing run needs its gate passed first** — Stage B for
  claim-bearing code, per `AGENTS.md`. Cloud capacity is not a reason to start
  early.
- **Apparatus verification needs no scientific gate** and should be running
  whenever it would otherwise block a decision.

## An unauthorized result is void, not failed

If a run's output is disqualified by a ruling, say so in exactly those terms and
mark the artifacts `VOID_NOT_EVIDENCE`. A healthy run whose cargo was disqualified
is not a failed run, and reporting it as one misleads.

**Declare the read boundary before launching anything speculative.** State which
fields may be read from an in-flight run before a ruling lands — typically wall
clock, conformance and provenance, never margins or estimates. Declaring it in
advance is what makes a NO-LAUNCH ruling cost nothing; declaring it afterwards is
just choosing the convenient answer.

Cancel a run whose output can no longer be evidence, unless its wall clock is
still worth having and the minutes are free. Say which reason applies.
