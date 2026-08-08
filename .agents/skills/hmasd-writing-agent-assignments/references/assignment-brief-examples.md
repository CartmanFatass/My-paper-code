# HMASD Agent Assignment Examples

These examples demonstrate information-rich natural-language assignments. They
are not templates, mandatory headings, schemas, or admission gates. A shorter
brief is correct when the task is simple and complete. A different structure is
correct when it communicates the task better.

The exact assignment remains the source of task scope and completion. Forked
turns are background only. The situations below are illustrative and do not
claim that the current branch contains these defects.

## Example 1 — Local helper defect

The current scenario normalization rejects one documented alias before any
environment is constructed. This is a local lookup defect: it does not change
environment physics, observations, reward, seeding, or the active algorithm.

Please correct the alias handling in `ha_ctse_process/env_factory.py` and add or
adjust the smallest focused test that proves the documented alias reaches the
same normalized scenario as its canonical spelling. Preserve every other alias
and the existing unknown-scenario failure.

Read only the target function, its direct CLI caller if needed, and the focused
test. Do not reorganize the alias table, rename scenarios, or refactor
environment construction.

Completion is a focused failing-before/passing-after check plus a concise
explanation of the defect and changed paths.

## Example 5 — Non-code transport with an observable conflict

An external-review transport child must answer a self-contained product-
research question. The page reported that generation was complete, but the
visible answer ended halfway through the requested comparison; a short
response is not evidence that the requested outcome was completed. Treat this
observed Agentify false completion as the RED baseline for the assignment.

Read the context brief and the exact question, choose a matching conversation,
and inspect the current composer state. If it shows High, open the model picker,
select Pro, and verify that the composer visibly shows Pro after the selection
before sending the question once. Treat an `expectedModel=Pro` argument, an
available option or other recognition metadata as a capability hint only; none
proves that the switch occurred. Completion also requires a nonempty
natural-language answer that addresses every requested comparison and the
visible page to be idle. If the page and structured status conflict, use local
judgment to inspect the answer, preserve any completed rows, and recover without
duplicating an active send.

Do not infer completion from a `COMPLETE` token, provider-home URL, selected
model label, or a response fragment. Do not redesign the transport protocol,
add an admission schema, or decide the research conclusion. The child may
retry one reversible page/session action when inspection shows it is safe, and
must report the actual answer or the concrete unresolved conflict.

Completion is a natural-language conclusion stating whether the requested
comparison was answered, followed by the exact question/result paths and
observable page evidence. A tool-recognition receipt without proof that the
question was actually sent and answered is insufficient.

## Example 2 — Cross-module, behavior-preserving storage change

The event collector snapshot is becoming expensive to copy. The requested work
is to reduce the internal packing cost without changing the snapshot's semantic
identity.

`ha_ctse_process/collectors.py` owns the collector-side snapshot envelope. Its
consumers rely on worker order, active-presentation order, pending membership
transactions, pending command/response state, worker environment snapshots, and
environment RNG state remaining aligned by environment. Restore must see the
same logical snapshot that capture produced.

Inspect the collector snapshot builder and validator, the immediate
snapshot/restore consumer, and the focused event-snapshot tests. Choose an
internal representation improvement only if those ordering and round-trip
properties remain equivalent.

Do not change the environment capability version, add a compatibility reader,
move policy inference into workers, alter RNG consumption, or refactor unrelated
collector commands.

If a direct consumer must change for the new representation to be correct,
explain that dependency and include only the necessary consequential change. Do
not modify a nearby path merely because it could also be simplified.

Completion is the implementation, a focused equivalence/round-trip check, the
paths changed, and any residual performance limitation. No scientific result is
claimed.

## Example 3 — Load-bearing checkpoint correction

A checkpoint currently reloads successfully but does not preserve the exact
controller/lifecycle state required by the assignment-named treatment. The
problem is semantic persistence, not generic serialization style.

Read the exact design, its live `CODE_SCIENCE_INDEX.md`, the state owner, the
relevant part of `ha_ctse_process/checkpoint_io.py`, the production reload path,
and the focused checkpoint/replay tests. Establish which state must survive
reload and which old state is intentionally invalid.

The repair must preserve model and optimizer ownership, normalizer state,
controller identity, RNG and lifecycle meaning, and the assignment's resume
boundary. Do not synthesize missing state, silently accept an incompatible
checkpoint, broaden migration support, or change the scientific result branch.

A newly discovered missing state field is not automatically a blocker. Determine
whether it is a reversible persistence detail inside the frozen contract. Ask
for a scientific decision only if two possible reconstructions would change the
treatment or result meaning.

Completion requires the smallest regression that distinguishes a
syntactically-loadable but semantically-invalid checkpoint from the corrected
round trip. Report the conclusion first, then exact paths and commands.

## Example 4 — Integrated reviewer assignment

Review the complete integrated change that updates collector snapshot packing
and its direct consumer. The implementation claim is behavior-preserving:
worker ordering, event capability identity, pending membership state,
environment RNG state, and snapshot/restore round trip must remain unchanged.

Read the integrated diff, the assignment, the focused tests, and only the
immediate interfaces needed to evaluate those invariants. Look for a normal-path
defect with material effect and a proportionate repair. Do not redesign the
event runtime, request broad cleanup, add an admission schema, or start another
review layer.

Return either:

- a concise no-finding conclusion naming the checked risks and accepted residual
  risk; or
- an actionable finding with the exact location, observed effect, and smallest
  repair whose project value exceeds its complexity and delay.

The result begins with the review conclusion. Exact evidence follows.
