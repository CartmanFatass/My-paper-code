---
name: hmasd-research-engineering
description: Implement, delegate, check, review and execute HMASD code as a DM, Implementer or Reviewer under docs/project/OPERATING_CONSTITUTION.md section 6 - L0 scope, Implementer handoff, core versus disposable code, carried-over engineering standards, independent review, commit-preflight-detached launch. Not for status or mechanical collection.
---

# Research engineering

Authority: `docs/project/OPERATING_CONSTITUTION.md` section 6. Node, interpreter and supervisor
values come from `.codex/hmasd-compute.toml`. Nothing below is a launch gate; the launch
conditions are in "Execution and admission".

## L0 and the Implementer

Before a code task the DM records a concise L0 scope in the current `NOTES.md` entry: deliverable;
owned paths and entry points; semantics that must not change; checks; budget and stop. Add
interface, state-flow or skeleton detail only where there is real risk. Read the nearest
directory `AGENTS.md`.

The DM may implement directly or delegate a bounded task to the Implementer (Claude: Opus, high
effort; Codex: Sol, high effort) with the scope note, the checkout and branch, and the entry.
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
default compatibility promise. Reuse small helpers or shared abstractions where actual consumers
benefit; avoid designing a general framework for hypothetical future experiments. Provide explicit argparse runner entry
points with seed, launch sha and a `summary.json` carrying the readings named in the notebook entry
or claim note, including learner movement relative to initialisation and actual transition,
optimizer-update and evaluation counts when reporting learning or fixed-policy evaluation.
Zero new updates in fixed-policy evaluation are explicit, not new training. Small correctness tests
and assertions are welcome. Archiving stops maintenance; the sha that produced a recorded
result stays recoverable, and its required outputs are preserved before scratch is deleted.

## Carried-over engineering standards (review signals, not gates)

- **Implementation judgment**: choose facilities by the actual task, semantic risk, resource
  cost and maintenance burden. Existing libraries, parallel execution, validation, recovery,
  profiling and reuse are available techniques, not forbidden categories. Prefer the simplest
  adequate path; explain material additional machinery in the existing scope note or commit.
  No mandatory scope trailer or separate record is needed. Routine choices
  within the task do not need the L0 to enumerate every utility or another approval. This does
  not grant extra fits, alter frozen execution semantics or permit blind retries of external effects.
- **Scope and structure**: judge complexity by the scientific task, interfaces and maintenance
  burden, not line counts or orchestration percentages. Explain necessary machinery and avoid
  splitting changes merely to conceal their logical scope.
- **Tests**: use focused checks sufficient for the changed behavior and risk. Do not cap their
  duration or count; report concrete coverage gaps and actual costs. Reuse unchanged evidence
  instead of repeating smoke checks solely because another launch or slice begins.
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
- **Host choice and recovery**: choose a suitable local or remote node prospectively for a
  new experiment; the configured default is a convenience, not a remote-first requirement.
  For an existing attempt, reconcile its process before a replacement and preserve its frozen
  dtype/device/RNG/comparator/horizon semantics. If a new host changes those semantics, label
  the new attempt accordingly rather than treating it as continuation. Admit on the destination.

## Checks and review

Self-check the changed behaviour and the primary output with proportionate focused tests or a short run.
Trace collector, storage, recurrent replay, loss and update, evaluator and publication. Look at
actor and critic leakage, snapshot cadence, masks, resets, normaliser state, termination and
truncation bootstrap, RNG addresses, optimizer exposure and train/eval isolation. For numerical
changes inspect intermediates and affected gradients over the real domain, choosing tolerances
from dtype, scale, conditioning, accumulation and actual action/order/metric consequences.
Distinguish deterministic numerical replay for a code path, statistical replication across
independent training runs, and algorithm/semantic equivalence. A fixed input sha does not promise
equal outputs; neither ordinary performance replication nor a device change implies universal
bit equality or a project-wide tolerance. A failed publication limits only its dependent claim.

An independent numerical checker cannot reuse the candidate answer as its proof. Keep outputs
promised as diagnostics even when the main branch does not consume them. Future experiments
may drop unnecessary diagnostics with an honest narrower claim; omitting required work is not
an equivalent optimization of the original experiment.

**Independent review** (`hmasd-reviewer`, read-only) is required for core or high-risk executable
changes affecting scientific meaning, numerics, RNG, replay/recurrent state, checkpoint/result
identity or external effects, including executable configuration and launch/Pro code. Non-code
documentation, skill prose and descriptive control changes use author self-checks for source
consistency, intent and affected consumers; no automatic or repeated Reviewer pass. File extension
alone does not determine whether a change alters executable behavior. Give a required reviewer the contract, invariants,
diff and evidence, not the conversation. A finding names the reachable failure and its impact.
The DM repairs and accepts; the reviewer decides neither science nor permission.

## Execution and admission

1. Commit and push the exact inputs.
2. New result-bearing entries use `scripts/hmasd_launch.py launch` and call
   `scripts.hmasd_admission.require_admission` before scientific effects. The kernel checks
   current canonical pause/direction/lead, published SHA, source and invocation identity,
   then applies the same physical/effective memory floor as
   `scripts/hmasd_resource_preflight.py admit-memory` immediately before releasing the child.
   It serializes launch through acceptance and preserves uncertain claims. Follow the
   [execution method](references/local-execution.md) for both local and remote nodes.
   Historical frozen launch interfaces stay at their original SHA; they are not silently migrated.
3. Launch detached from the committed sha with the configured interpreter. The kernel returns
   a native JSON manifest; supervisor command acceptance is not child admission. Use a worktree or
   source snapshot when necessary to keep active inputs unchanged while authoring continues. Record command,
   node, handle, sha, cwd and output root in `NOTES.md`.
4. Observe directly or delegate to a monitor/tracker when useful. On transfer, retain observation
   responsibility until the recipient adopts the accepted handle. Timeout or a lost connection is
   unknown, not terminal. Never launch a duplicate; reconcile the same handle.
5. On terminal notice collect outputs into `runs/<direction>/<tag>/` and verify the local
   artifact before any remote cleanup. Exit zero is not a result; the DM reads it.

Runtime notes: ordinary in-process batching and a fixed synchronous native team inside one
named function are routine options. Select topology, profiling, device, JIT, language and
dependencies for demonstrated task needs and actual costs under the existing scope. A larger
execution design is not justified merely by its availability; a named technique is not itself
a reason to refuse a useful implementation. Preserve frozen conditions and avoid unrelated
environment changes. Report measured wall and peak RSS with their scope.
Preserve live handles; a killed run stays killed.

Batch only genuinely independent axes with explicit state ownership. Preserve causal,
autoregressive and recurrent order unless an applicable equivalence argument supports the
change. Check RNG consumption, masks/reset/bootstrap, sample/update frequency, replay ratio,
policy freshness, reductions and tail handling; padding or dropping samples is not automatically
equivalent. A fixed native team has bounded participants/lifetime, private mutable state and
outputs, necessary synchronization, and logical-order merging of results/errors. Account for
nested BLAS/OpenMP teams to avoid oversubscription; existing object-specific topology stands.

Optimize the complete actual path: locate repeated construction, fine cross-language calls,
Python loops, pack/copy and equivalent reuse at measured hotspots. Consider sampler, training,
buffer and output placement with transfers and synchronization when choosing a device. A forward
microbenchmark or increased samples/updates/model copies does not establish faster equal-work
training. Use existing evidence where adequate; no compulsory device or worker-count sweep.

Ordinary wall estimates and engineering watchdog plans can be adjusted prospectively, including
during a live run, using progress, resource health and remaining work; note time and reason in
the existing run entry. This never changes frozen training/evaluation exposure, a wall-based
scientific endpoint, or genuine owner/platform hard limits. Exceeding an estimate alone does
not invalidate a run. A terminated invocation remains terminated; adjustment does not grant a retry.

## Stops

A real scope, semantics, writer, resource or uncertain-effect conflict stops only the dependent
action; report the evidence and the owner of the decision and continue independent work. Clean
only your own verified scratch under `temp/`.
