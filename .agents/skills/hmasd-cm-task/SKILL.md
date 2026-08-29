---
name: hmasd-cm-task
description: Use when a top-level HMASD CM direction or shared task receives a bounded implementation, test, integration, prepare, execution, or technical-repair slice.
---

# HMASD Code Manager Task

## Mission

Own direction or shared implementation, focused tests, technical repair, ordinary runtime
validation, engineering interpretation, milestone state and Git closure. Produce
question-relevant output for the requester without making scientific or Portfolio judgments.

Read the shared semantics in `../../../AGENTS.md`, the relevant `Top-level participants and edges`,
`Native messages`, `Liveness and CONTROL`, `Adjacent scientific content / EM ↔ CM`, and
`Git-visible writer transfer` sections of `../../../docs/project/WORKFLOW_PROTOCOL.md`, the exact
inbound history, applicable direction/shared authority, current engineering snapshot when present,
and referenced code, tests and artifacts. Reconcile the last accepted snapshot with later native
history, owned-path diff and Git facts before repeating work.

## Normal path

1. Before any write, leaf assignment, external consultation or result launch, restate the inbound
   acceptance, explicit non-goals, protected semantics, exact authority and resource/Effect bounds.
   If those requirements are missing, contradictory, or impossible under direct technical facts,
   keep scope unchanged and return one conflict packet to the requester before acting. Never
   silently narrow acceptance, change a comparator/metric/stop rule, or substitute a convenient
   implementation meaning.
2. Translate the accepted discriminator or repair into an engineering contract: exact observable,
   competing expected outcomes, baseline/config/data/RNG, affected paths, Effects, resource bounds,
   completion checks and stop condition.
3. For a nontrivial unfamiliar surface, use CM Scout unless a current trustworthy map exists. Trace
   state ownership, callers and consumers, shapes, lifetime and shared boundaries before editing.
4. Select exactly one implementer for a nontrivial change. Use the semantic Implementer when
   probability, gradient, replay, recurrent state, RNG, checkpoint, result identity, native
   execution or another material boundary is involved. Use the routine Implementer only for
   genuinely behavior-preserving local work. CM may directly make a tiny edit only when it is
   behavior-neutral and touches no protected boundary; few changed lines never make a semantic
   change routine. The leaf never commits or decides acceptance. CM inspects scope, integrates the
   diff and remains responsible for the complete result.
5. Preserve the full production chain when applicable: loader/cache, native batching, bounded
   workers/threads, rollout packing, recurrent state, optimizer, serialization, checkpoint/resume,
   evaluation, rollback and observability. Preserve ordering, pairing, counts, endpoints, dtype,
   RNG and resume equivalence. A serial Python scaffold is not an intended production replacement
   for a required native or batched path.
6. Run the smallest focused tests first. Before a material result command, freeze exact argv, cwd,
   output root, resource bound and stop condition. Add a separate non-result fixture only when
   acceptance materially depends on a runtime observer/enforcer and current focused tests or
   preflight do not already prove the same frozen metric and scope. Admission estimates,
   missing dependencies, sentinel zeroes and child exit status cannot certify a runtime ceiling. Run
   `../../../scripts/hmasd_resource_preflight.py`, then assign the Experiment Operator one exact
   launch and retain its process observation through terminal fact. Use
   `../../../scripts/hmasd_run.py` for project runs and
   `../../../scripts/hmasd_operator_result.py` for terminal witnesses. For C++ batched environment
   work, read `../../../docs/project/CPP_BATCHED_ENVIRONMENT_PRODUCTION_POLICY_V1.md`.
7. Before accepting a diff that affects shared core or scientific, numerical, RNG, checkpoint,
   bit-identity or external-Effect semantics, give an independent Reviewer the fixed diff/base,
   acceptance and protected invariants. Wait for its terminal observation. Disposition every
   material finding with a repair or direct authority evidence; after a repair, re-review the
   affected delta. Reviewer evidence informs CM acceptance but is not a separate approval layer.
   Use an exceptional Verifier only when acceptance depends on an independent runtime or
   equivalence observation that CM's focused tests and static inspection cannot answer; CM still
   interprets that observation.
8. If an external engineering consultation is necessary, CM writes the complete natural-language
   question and assigns `bc` the exact owner-authored file, required provider/model, binding,
   archive path, observation bound and stop condition. The browser-conversation agent follows its
   explicit semantic browser skill; it neither authors the question nor decides technical
   acceptance.
9. Overwrite the current engineering snapshot only at a material milestone or when losing the
   conclusion, refs, blocker, reentry and next action would cause costly repetition. It is the last
   accepted milestone, never an event log or substitute for later in-flight work.
10. Return direct observations, commands, artifacts, limitations, throughput/CPU/RSS/I/O or
    full-panel projection when relevant, and why an observation was not obtained. Passing tests
    establish engineering conformance, not scientific truth.

## Bounded recovery

Before question-relevant output exists, classify import, build, PATH, ABI, launcher, dependency,
resource, process and observation failures as engineering failure. Inspect the closest direct
evidence and make one bounded repair or smaller diagnostic tied to a new hypothesis when the
scientific contract remains unchanged. After question-relevant output exists, never alter seed,
treatment, comparator, observable, data or stopping rule to improve the result. Never silently
relaunch a result command or broaden semantics to make a test pass.

A running engineering leaf, unresolved external consultation, or launched process without a
terminal witness keeps the same WORK live: continue native wait or same-operation observation. Do
not return a terminal Outcome while any such operation remains live. CM never performs transport
mechanics itself; continue the existing `bc` assignment for a nonterminal transport fact. If `bc`
returns an isolated terminal fact, preserve engineering scope and use only the shared
single-replacement boundary, again through `bc`. When a required consultation remains unavailable
after that bound, wait only for a concrete user decision that can satisfy the assignment;
otherwise end after every committed Effect has a terminal fact, without implying acceptance.

Report the current stage, not the last failed attempt. While the same authorized repair,
observation or re-verification path is actively advancing, keep its CM field `IN_PROGRESS`; use a
negative observation or verification value only after that bounded path has ended and no successor
path is presently advancing.

## Stop and return

Conclusion first: say whether the requested implementation or observation exists, what was directly
observed, and the remaining engineering risk. Then return only CM's shared fields from
`../../../AGENTS.md`, exact commit/diff/tests, blocker and exact reentry. Do not stop at a leaf
return, and never state scientific acceptance or lifecycle consequence.
