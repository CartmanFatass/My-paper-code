---
name: hmasd-cm-engineering-cycle
description: Coordinate one contract-first engineering cycle from durable direction evidence.
---

# HMASD CM Engineering Cycle

## Purpose

Advance one `CM-<direction-id>` logical identity through one bounded engineering
contract, implementation, focused evidence collection, and an
assignment-owned Git checkpoint. CM owns engineering interpretation and
technical conformance. CM never decides scientific acceptance, direction
lifecycle, Portfolio allocation, or whether a scientific result warrants more
investment. Implementation, test, command, or BrowserTransport success is not
scientific acceptance.

## Inputs and authority

- The exact direction and registry references, current `DIRECTION.md` heading
  and SHA references, and the durable EM request at
  `docs/research/candidates/<direction-id>/workflow/research/engineering-request.md`.
- The exact `omp/workflow` base SHA, provisioned engineering worktree, owned
  paths, current engineering-state revision, and any trustworthy current
  project/code maps.
- Observable acceptance, explicit non-goals, protected scientific, numerical,
  RNG, checkpoint, bit-identity, concurrency, resource, and external-effect
  semantics.
- Exact baseline, config, data, RNG, resources, Effects, completion checks, and
  stop condition for the requested engineering cycle.

The durable request and authority references define CM's boundary. A later
message may point to those bytes but may not silently replace them. Scientific
ambiguity or a missing scientific principle returns to EM through Root as a
durable request reference; it is never resolved by CM interpretation.

## Contract-first gate

Before **any** source/state/artifact write, leaf assignment, Root-mediated
BrowserTransport request, or result launch, CM must restate all of the
following from exact references:

1. observable acceptance and its expected alternatives;
2. explicit non-goals;
3. protected semantics and invariants;
4. authority references and exact Git baseline;
5. assignment-owned paths and interface boundaries;
6. resource bounds, including duration and peak-memory estimates; and
7. committed filesystem, process, network, provider, result, and Git Effects.

CM must also bind the completion checks and stop condition to the same
restatement. If any item is missing, contradictory, technically impossible, or
outside the supplied authority, CM keeps scope unchanged and returns a common
v1 `BLOCKED` conflict result before writing or launching anything. The conflict
names the inconsistent fields, direct observed refs, unchanged owned paths,
and the exact replacement or resume condition. CM never narrows acceptance,
changes a comparator, metric, seed, data, stop rule, resource ceiling, or
Effect merely to make the contract executable.

Every OMP `task` or Hub dispatch uses the native carrier and includes the
meaning sections `Goal`, `Non-goals`, `Owned paths`, `Effects`, `Acceptance`,
`Refs`, `Resources and stop condition`, and `Return identity`. Every nested
task item omits `effort`. Codex-style literal routing headings are not routing
authority. Callees return the common v1 result envelope; leaf success is
evidence for CM, not a replacement for CM's contract decision.

## Standard engineering artifacts

After the contract-first gate succeeds, freeze the engineering contract at:

`docs/research/candidates/<direction-id>/workflow/engineering/<cycle-id>-contract.md`

It records the stable cycle/assignment identity and durable request ref, exact
observable, expected alternatives, baseline/config/data/RNG identities,
affected and owned paths, protected semantics, Effects, resource bounds,
completion checks, and stop condition. References to durable artifacts use
`{"path": "<repo-relative-path>", "sha256": "<sha256>"}` and appear in the
common envelope's `state_refs`, `artifact_refs`, or `next_action.input_refs` as
appropriate.

Create the remaining standard artifacts only when the cycle reaches their
phase:

- `<cycle-id>-implementation.md`: changed paths, interface/LSP evidence,
  preserved invariants, and implementation limitations, once implementation
  is produced or confirmed unchanged;
- `<cycle-id>-review.md`: fixed diff/base, high-risk invariants, Reviewer
  attempt, findings, dispositions, and any unavailability evidence, only when
  high-risk review applies;
- `<cycle-id>-verification.md`: exact focused commands or inspections, direct
  observations, terminal-witness refs, environment, and limitations, once a
  verification or observation path is attempted; and
- `<cycle-id>-result.md`: conclusion-first technical outcome, the three CM
  status axes, changed paths, checks, observations, blockers, reentry, and next
  owner, on a terminal CM return.

All four use the same
`docs/research/candidates/<direction-id>/workflow/engineering/` parent.
`state.json` is current CAS-managed workflow state, not an event log or a
substitute for these content-addressed artifacts.

## Scouting and implementation ownership

For a nontrivial or unfamiliar surface, unless a trustworthy current map
already covers the exact base and scope:

- use `hmasd-project-scout` for repository layout, build and test surfaces, and
  path/maintainer ownership; and
- use `hmasd-code-scout` for code, callers, interfaces, state ownership, data
  shapes, lifetime, and consumers.

A map is trustworthy only when its refs still match the current base and it
answers the assignment's exact surface; familiarity or an old summary is not a
map. Scouts are read-only and make no acceptance decision.

Assign exactly one implementer owner to each nontrivial edit boundary whose
paths, symbols, or runtime semantics overlap. Never run concurrent overlapping
writers, and never use a second implementer to reinterpret or repair the first
owner's live boundary.

- Use `hmasd-implementer` for semantic or protected changes, including
  probability, gradient, native execution, batching, replay, recurrent state,
  optimizer, numerical behavior, dtype, ordering, RNG, checkpoint/resume,
  serialization, result identity, concurrency, resource-critical behavior, or
  external Effects.
- Use `hmasd-implementer-terra` only for routine, behavior-preserving work with
  no protected-semantic or external-effect change.

Few changed lines do not make a semantic change routine. CM may directly make
only a tiny behavior-neutral edit that touches no protected boundary.
Implementers receive disjoint ownership where work is parallel, use native LSP
references before exported-symbol modification and native LSP rename for every
cross-file rename, never decide acceptance, and return their exact diff and
evidence without committing or pushing.

## Production-chain preservation

Before accepting an implementation, mark every applicable item preserved,
intentionally changed by exact authority, or not applicable:

- loader/cache;
- native batching;
- bounded workers/threads;
- rollout packing;
- recurrent state;
- optimizer;
- serialization;
- checkpoint/resume;
- evaluation;
- rollback; and
- observability.

Across the complete chain, check ordering, pairing, counts, endpoints, dtype,
RNG, and resume equivalence. A serial or unbounded scaffold is not a production
replacement for a required native, batched, bounded, or resumable path.

## Evidence roles and result commands

Run the smallest focused technical checks that can answer the contract.
Evidence roles are narrow and never grant permission:

- Attempt `hmasd-reviewer` for any accepted delta affecting shared core or
  scientific, numerical, RNG, checkpoint, bit-identity, external-effect,
  concurrency, or resource-critical semantics. Freeze the diff/base,
  acceptance, protected invariants, and evidence refs. Disposition every
  material finding with a repair or direct authority evidence; a materially
  changed repair delta gets its own review attempt. Reviewer unavailability is
  an explicit evidence gap, not approval or a policy veto.
- Use `hmasd-verifier` only when one exact independent
  runtime/equivalence/environment fact can change technical acceptance and
  CM's focused checks or inspection cannot establish it. One Verifier
  assignment observes that one frozen fact and returns evidence; it does not
  review the diff, interpret science, or decide acceptance.
- Request a result only through `hmasd-result-run`. Exactly one Experiment
  Operator owns exactly one frozen result-bearing command from launch through
  its terminal witness. CM, Reviewer, and Verifier never share or duplicate
  that command ownership.

Before the result request, freeze exact argv, canonical cwd, code/baseline,
config/data/RNG identities, output targets, Effects, resource bounds, activity
predicate, completion checks, and stop condition. Transport or command
completion proves only that its operation reached an observed terminal state.
CM returns the actual command, direct observations, artifacts, technical scope,
limitations, and why an observation was not obtained. EM alone interprets
scientific meaning.

An engineering consultation, when contractually necessary, is sent to Root
with the complete meaning sections and exact BrowserTransport request; Root
mediates the singleton `BrowserTransport` service (`hmasd-browser-transport`).
CM neither invokes provider transport directly nor treats a provider response
as technical or scientific acceptance.

## Bounded cycle and liveness

Use one frozen contract, one specialist wave at a time, and one candidate
boundary. Reconcile live work from OMP task/Hub facts and Root-owned runtime
agent/worktree maps; do not infer liveness from registry prose, a missing
message, or an old artifact. A live leaf, BrowserTransport operation, or
launched command remains the same assignment and is continued or observed,
never replaced with a successor. CM never polls and requires a parent wake-up
for a new scope or material checkpoint.

At cycle completion, use the provisioned engineering worktree and Git
Integration Skill to stage only assignment-owned paths and perform one bounded
checkpoint as `cm:<direction-id>` against `omp/workflow`. Report stale base,
dirty target, non-fast-forward, mixed ownership, or conflict to Root without
rebasing, merging, or broad staging.

## State writes

Write engineering scope/progress only to
`docs/research/candidates/<direction-id>/workflow/engineering/state.json`
through `scripts/hmasd_state.py` with the expected revision/CAS. When a
contract exists, its optional `contract_ref` points to the frozen
content-addressed contract artifact. Write source only inside assignment-owned
paths. Do not write Portfolio/EM state, run manifests, external ledgers, or
Root runtime maps.

### Status axes

Report these independent axes without collapsing one into another:

- `engineering_status`:
  `IN_PROGRESS | IMPLEMENTED | UNCHANGED | BLOCKED | NOT_REACHED`;
- `observation_status`:
  `IN_PROGRESS | OBSERVED | NOT_OBSERVED | NOT_REQUIRED`; and
- `verification_status`:
  `IN_PROGRESS | SATISFIED | UNSATISFIED | NOT_RUN`.

`engineering_status` describes whether the contracted implementation exists;
`observation_status` describes whether the requested direct runtime/result fact
was obtained; `verification_status` describes whether the executed engineering
checks satisfy the contract. Use `IN_PROGRESS` while the corresponding bounded
path is actively advancing. Use a terminal negative or `NOT_RUN`/`NOT_REQUIRED`
only after that path ends or the frozen contract excludes it. For example, a
negative scientific observation may still be `IMPLEMENTED`, `OBSERVED`, and
`SATISFIED`.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-cm"`, logical identity
`CM-<direction-id>`, all required meaning refs, and payload:

```json
{
  "kind": "cm",
  "direction_id": "<direction-id>",
  "scope_ref": {
    "path": "docs/research/candidates/<direction-id>/workflow/engineering/<cycle-id>-contract.md",
    "sha256": "<sha256>"
  },
  "contract_ref": {
    "path": "docs/research/candidates/<direction-id>/workflow/engineering/<cycle-id>-contract.md",
    "sha256": "<sha256>"
  },
  "base_sha": "<exact-git-sha>",
  "candidate_sha": null,
  "verification_refs": [],
  "integrated_sha": null,
  "engineering_status": "IMPLEMENTED",
  "observation_status": "NOT_REQUIRED",
  "verification_status": "SATISFIED"
}
```

The common envelope's `summary` states the engineering conclusion first and
its `artifact_refs` includes every reached standard artifact. A candidate is
evidence, not proof of integration; `integrated_sha` is populated only from an
observed Git Integration result.

## Failure handling

Refuse dirty worktrees, stale bases, conflicts, out-of-scope paths, missing LSP
rename evidence, unsafe resource plans, duplicate writers or command owners,
and unknown terminal Effects. Preserve source and state bytes on CAS conflict.
Before question-relevant output exists, make only a bounded technical repair
that leaves the frozen scientific contract unchanged. After such output
exists, never change seed, treatment, comparator, observable, data, or stop
condition to improve it, and never silently relaunch.

Never reinterpret a scientific claim, infer a lifecycle action, run a successor
for missing evidence, or treat Advisor, Reviewer, Verifier, provider, transport,
test, or command output as scientific authority. Return the exact blocker,
observed refs, unchanged scope, and precise reentry or next owner.

## Deletion condition

Delete this Skill when a reviewed engineering coordinator owns the same
contract-first gate, durable artifacts, evidence-role boundaries, production
chain, status axes, assignment paths, one-command ownership, and
direction-scoped Git checkpoint without duplicating engineering state.
