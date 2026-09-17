---
name: hmasd-research-engineering
description: Implement, delegate, check, review and execute HMASD code as a DM, Implementer or Reviewer under docs/project/OPERATING_CONSTITUTION.md section 6 - L0 lines, Implementer handoff, core versus disposable code, carried-over engineering standards, independent review, commit-preflight-detached launch. Not for status or mechanical collection.
---

# Research engineering

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 6. Node, interpreter and supervisor
values come from `.codex/hmasd-compute.toml`. Nothing below is a launch gate; the launch
conditions are in "Execution and admission".

## L0 and the Implementer

Before any code task the DM writes five lines in the current `NOTES.md` entry: deliverable;
owned paths and entry points; semantics that must not change; checks; budget and stop. Add
interface, state-flow or skeleton detail only where there is real risk. Read the nearest
directory `AGENTS.md`.

Small edits the DM makes directly. A bounded task goes to the Implementer (Claude: Opus, high
effort; Codex: Sol, high effort) with the five lines, the checkout and branch, and the entry.
The Implementer returns the diff or commit, the check output, deviations with reasons and open
risks. It chooses no science, adds no seed, arm or endpoint, launches nothing result-bearing
and spawns nothing. The DM reads the diff, runs or reads the checks, and accepts; acceptance is
the DM's, never the Implementer's or the Reviewer's.

## Core versus experimental

**Core** is the shared learner, runners, environments and evaluators, including
`ha_ctse_process/`, `envs/`, `hmasd_*.py` and the core launchers. Preserve public interfaces,
numerical and RNG behaviour and checkpoint compatibility unless the change is the point and is
recorded. Run the relevant smoke test. Core acquires no research dependencies.

**Experimental** code under `experiments/candidates/<direction>/` is disposable: no
compatibility promise, no shared abstractions built for reuse. One argparse runner per idea
with seed, launch sha and a `summary.json` carrying the readings named in the notebook entry
or claim note, including learner movement relative to initialisation. Small correctness tests
and assertions are welcome. Archiving stops maintenance; the sha that produced a recorded
result stays recoverable, and its required outputs are preserved before scratch is deleted.

## Carried-over engineering standards (review signals, not gates)

- **Do not build** unrequested distributed or multiprocess workers, pools, schedulers, retries,
  leases, heartbeats, recovery orchestration, hash or authority guards, incident trees, JSON
  validators, registries, single-use abstractions, telemetry frameworks or compatibility
  shims. A facility beyond wall time and peak RSS needs its need written in the notebook entry
  and `scope: <item> per <NOTES.md entry>` in the commit; otherwise `scope: none`.
- **Size**: 2,000 new non-test lines per attempt and 600 per runner. Orchestration above
  30 percent of a diff is a review signal. Name any excess; never split commits to hide it.
- **Tests**: research-directory tests total under five minutes excluding one runner smoke; no
  repeated smoke per launch or slice. Return a concrete coverage gap rather than exceed it.
- **Staging**: only committed source and declared artifacts at their recorded digest reach the
  node; never dirty source. Currentness is the byte content of the declared paths, not the
  commit id, so an unrelated commit does not refuse a run.
- **Telemetry rule**: a run whose wall, peak RSS or scratch telemetry is missing stays valid
  and is marked `resources_unmeasured`; only a resource claim is annulled by it. Missing
  learner-side instrumentation (logs, checkpoints, required measurements) quarantines the
  dependent claim. Report RSS with its scope; sums of per-process peaks are not a simultaneous
  peak. Unknown time is not zero.
- **Quarantine**: a launch that omits required instrumentation or part of the recorded plan
  is an incomplete implementation, not a result. Repair, then make a fresh outcome-blind
  attempt at a new sha. Technical failure creates neither a negative result nor extra fits;
  narrower trustworthy facts remain reportable.
- **Diagnosis by reproduction**: exception, exit, missing-output and count facts are reported
  immediately; root cause from error text stays provisional until reproduced over recorded
  bytes. Repair or verify a defect when the next claim depends on it; an unrelated historical
  failure does not block a credible alternative path.
- **Local fallback**: allowed only when host portability was established before any
  question-relevant output, no remote process was accepted, and a fresh local admission
  passes. Routing never changes dtype, device, RNG, comparator, horizon or claim meaning.

## Checks and review

Self-check the changed behaviour and the primary output once with focused tests or a short run.
Trace collector, storage, recurrent replay, loss and update, evaluator and publication. Look at
actor and critic leakage, snapshot cadence, masks, resets, normaliser state, termination and
truncation bootstrap, RNG addresses, optimizer exposure and train/eval isolation. For numerical
changes inspect intermediates over the real domain with tolerances chosen from dtype and
scale, not bit equality. A failed publication limits only the claim that depends on it.

**Independent review** (`hmasd-reviewer`, read-only) is required for a change to core, to
scientific meaning, numerics, RNG, replay or recurrent state, checkpoint or result identity, or
external effects, including launch and Pro tooling. Give the reviewer the contract, invariants,
diff and evidence, not the conversation. A finding names the reachable failure and its impact.
The DM repairs and accepts; the reviewer decides neither science nor permission.

## Execution and admission

1. Commit and push the exact inputs.
2. On the executing node, `scripts/hmasd_resource_preflight.py admit-memory --out <receipt>`
   must show physical and effective available memory of at least 4 GiB, immediately before
   the runner, in the same supervised command (`preflight && runner` under `agent-task`).
   Concurrent checks reserve nothing: serialise launch and acceptance, then remeasure.
3. Launch detached in an exact-sha worktree with the configured interpreter. Record command,
   node, handle, sha, cwd and output root in `NOTES.md`.
4. Hand the accepted handle to the monitor (Codex) or a bounded tracker window (Claude).
   Timeout or a lost connection is unknown, not terminal. Never launch a duplicate; reconcile
   the same handle.
5. On terminal notice collect outputs into `runs/<direction>/<tag>/` and verify the local
   artifact before any remote cleanup. Exit zero is not a result; the DM reads it.

Runtime notes: ordinary in-process batching and a fixed synchronous native team inside one
named function are fine; no dynamic executor service, no standing profiler, no automatic GPU,
JIT, language or dependency migration. Report measured wall and peak RSS with their scope.
Preserve live handles; a killed run stays killed.

## Stops

A real scope, semantics, writer, resource or uncertain-effect conflict stops only the dependent
action; report the evidence and the owner of the decision and continue independent work. Clean
only your own verified scratch under `temp/`.
