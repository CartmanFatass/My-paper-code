# CBSC P47 source-only technical observation — 2026-09-11

**PASS_SOURCE_ONLY / NO_ATTRIBUTABLE_REPAIR.** The current explicitly authorized
source-only operation completed. No target operation was attempted, and no claim
is made that the old automated restriction was reversed.

## Assignment and reading rule

Root's 2026-09-11 owner-directed technical unblocking assignment permits bounded
static or tiny synthetic source-only checks without model/environment/training/
evaluation or result-bearing exposure. It does not select or release retained52.
The [intake L0](CBSC_P47_TECHNICAL_UNBLOCKING_INTAKE_20260911.md#current-assignment-and-l0)
was written before the check. Its applicable reading, verbatim:

> Static acceptance does not
> release a target invocation or establish runtime success.

## What ran

One stdlib checker using the existing local interpreter with `-I -S -B`, bounded
by a parent `subprocess.run(..., timeout=10)`. Source entry is
`63fba179f309870a5b510b6e50739e4e5b50f063` in the shared `codex/cbsc` checkout.
The source file was unchanged from `7e7ebd22bb21234332c8d8039e229b39d02ccdfa`.
The [result JSON](CBSC_P47_SOURCE_ONLY_CHECK_20260911.json) preserves the exact
checker program, executed argv, stdout/stderr, source references and timings.

Three source inputs were read: the old test at
`d843b5f903663dcc5a699c0a85fbae4e5252d20f`, its saved `edit_prefix.py`, and the
published `test_initial_train_episode.py`. Four AST parses and six literal
replacements reconstructed the published source exactly, comparing text after
ordinary text newline decoding and AST without line-location attributes.
Each literal replacement matched once. The saved edit script itself was never
executed, and the target module was never imported or executed.

The checker found no loaded `torch`, `numpy`, `experiments`, `envs`,
`environments` or `ha_ctse_process` module. It observed the unchanged target's
module-scope run import and the source order placing reference reading after
tuple construction. Those are static facts, not a run of either branch.

## Counts and cost

| Quantity | Result |
| --- | --- |
| Checker exit / stderr | 0 / empty |
| Source-only checker invocations | 1 |
| Source inputs / AST parses / literal replacements | 3 / 4 / 6 |
| Text and AST reconstruction | equal |
| Target invocations / research-native calls / tapes | 0 / 0 / 0 |
| Model calls / optimizer updates / score evaluations | 0 / 0 / 0 |
| Checker subprocess wall, complete child | 0.08437399999820627 s / limit 10 s |
| Checker body wall | 0.019082700018770993 s |
| Prior local Git blob retrieval wall | 0.06213229999411851 s |
| Control work before evidence write | 0.14990530000068247 s |
| Complete shell-tool wall for that command | 0.3969885 s |

Timing layers overlap. Full session/publication wall, CPU and RSS are unmeasured.
No scientific resource admission, remote operation, package change, learner,
debugger or result-bearing invocation occurred. No old diagnostic cap was spent.

## Historical event and limits

The retained P47 E0 reports a possible-cybersecurity-risk restriction of the CM
turn without naming a rejected command. Its recorded last completed preparation
edited the source, parsed its AST and passed `git diff --check`; a reviewer return
followed. No retained52 publication/staging/launch was attempted then. The saved
edit script reconstructs that source change but cannot reveal the enclosing
tool payload or classifier trigger.

Local copies of the three previously accepted handles report failed/139,
finished/0 and finished/0 for minimal prefix, offline new-core observation and
isolated TRAIN51 respectively. No new remote status query or target was used.
The unexecuted retained52 source still implies 7,904 tokens, 15,808 pack calls and
2,584 final comparison bytes; none were constructed or compared in this check.

No source or transport defect attributable to the turn event was found. The
engineering result is the successful source-only path and consistent preparation
bytes. It does not diagnose a crash, clear a runtime method, support a production
patch, or supply a performance result. Scientific selection remains outside this
assignment. The intake specifies the missing event record and the completed
technical exit condition.

## Separate cleanup rejection

After preserving the checker/result bytes, `exec_command` rejected the guarded
PowerShell `Remove-Item -LiteralPath $cbscScratchResolved -Recurse -Force`
operation before process creation, with “blocked by policy.” Its target was only
the known five-file invocation scratch directory; the command included resolved
path and exact-content checks. No removal was accepted. This is a directly
observed current operation, separate from the old unlocalized CM-turn event.

All five scratch files remain. The linked JSON records this cleanup target,
method, rejection and retained inventory alongside the unchanged checker result.
DM remains the cleanup owner; no alternate executor/deletion method was tried.
The remaining exit condition is permitted cleanup of that exact directory and
verification of its absence. It is a retention limit, not a failed source check
or a new scientific stop. All historical P47 evidence remains untouched.
