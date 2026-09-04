# CRTO RAW phase-trace A01 attempt evidence

Date: `2026-09-04`

Object: `CRTO-RAW-PHASE-TRACE-A-RECON-R01`

Evidence class: `A/RECON`

Attempt disposition: `QUARANTINED_PRE_RUN_LAUNCHER_PAYLOAD_LOSS`

Frozen scientific branch: **none; the scientific runner did not execute**

Claim ceiling: direct engineering facts about the accepted implementation and one remote
supervisor task whose executed script lost the preflight/runner payload. This evidence does not
contain a RAW path measurement, checkpoint-phase observation, update-256 anchor, competence fact,
resource observation, or residual-mechanism polarity.

## Accepted implementation

The card was committed and pushed before engineering at
`2bbb289add4f30c6e2f03b87641bf05b0dc753b4`. The accepted implementation is the exact pushed SHA
`c8247c2d19ac7965208c397a2a87519a1efb6310`, reachable from both
`origin/codex/cm/crto-raw-phase-trace-a01-20260904` and
`origin/codex/impl/crto-raw-phase-trace-a01-20260904`.

The bounded change touches only the four declared files under the new attempt package, runner, and
mirrored test directory. It has `751` non-test lines, a `50`-line runner, `176` test lines, and a
conservative orchestration share of `208/751 = 27.7%`. It adds no item from engineering-scope
specification section 4; all implementation commits carry `scope: none`.

Independent review found no material issue after two bounded repairs. The final exact-commit
focused suite passed `6` tests in `3.38` seconds with one pre-existing unknown-`cache_dir` warning.
The implementation fixes native thread variables before NumPy/Torch import, asserts and publishes
Torch intra/inter-op `1/1`, compares the full A01 selected population directly with B01, constructs
only RAW packets, and creates exactly one trained gate. These are engineering-conformance facts,
not scientific observations.

## Machine-generated cost and exposure projection

The non-result `project-cost` mode emitted:

```text
prior complete B01 invocation                         = 434.7066687 seconds
projected RAW-trace arm seconds = 3 * 434.7066687      = 1304.1200061 seconds
per-arm and invocation cap                            = 1800 seconds
projection within cap                                 = true
```

It also emitted prospective counts of `128` predictor tapes, `100*128=12,800` predictor processed
examples, `264*32=8,448` RAW processed examples, `13` checkpoints, and `13*16=208` evaluation rows,
plus all thirteen prospective exposure lines. The seed-0 initialization anchors were exactly L2
`18.87916908516977`, RMS `0.10402732933491829`, and Linf `0.28862619400024414`. No actual
parameter displacement was observed because the result runner never ran.

## Remote task: direct observations

One supervisor task was accepted on `wsl_4070`:

```text
task       crto_raw_phase_a01_c8247c2d_01
pid        42387
status     finished
exit       0
started    2026-09-05T01:28:42+08:00
ended      2026-09-05T01:28:42+08:00
duration   0 seconds
task root  /home/wu/.agent-tasks/crto_raw_phase_a01_c8247c2d_01/
```

Direct inspection of the exact executed bytes found:

- `runner.sh` SHA-256
  `9089b7dedfcc8602837121d046c5f6a2e924eb24662947b43d1e9537b611ccb1`;
- `task.log` SHA-256
  `2cb2620564993115f10061a690925d01db8b83c66cad2b66f3ebc7ecdcffe05a`;
- the task root contains only supervisor control files (`exit_code`, `pid`, `runner.sh`,
  `start_time`, `status`, and `task.log`); and
- the intended admission receipt, stdout, stderr, result root, and `summary.json` do not exist.

The authoritative executable line in `runner.sh` is exactly:

```text
eval 'bash -lc cd /home/wu/hmasd-worktrees/crto-raw-phase-a01-c8247c2d'
```

The task log contains only the start and exit lines. The configured joined remote preflight and
scientific runner were lost during `agent-task` command-argument reconstruction. Exit code `0`
therefore describes a successful `cd`, not successful admission, training, evaluation, or result
publication.

The remote worktree currently resolves HEAD to the correct launch SHA but has `5,193` tracked
deletions in porcelain status, including required sparse surfaces. No scientific command ran from
that state. This dirty materialization is a second direct technical nonconformance, not a result.

## Counts, receipts, and side effects

| quantity | direct count/state |
| --- | ---: |
| mandatory remote admission | not run |
| admission receipts | `0` |
| scientific runner processes | `0` |
| RNG masters / predictor models / RAW gates / optimizers | `0 / 0 / 0 / 0` |
| predictor tapes / predictor updates / predictor examples | `0 / 0 / 0` |
| RAW updates / processed examples | `0 / 0` |
| checkpoints / evaluation rows | `0 / 0` |
| update-256 anchor | not observed |
| TRUE/DERANGED learner or evaluation exposure | `0` |
| confirmation-namespace reads | `0` because only `cd` executed |
| summary/result files | `0` |
| resource telemetry | not measured; no result invocation began |

The telemetry exception does not apply: this is not a valid result marked `resources_unmeasured`,
because the mandatory admission and scientific invocation never occurred.

## Frozen rule applied without reinterpretation

The card's branches remain:

1. `A01-RAW-PHASE-TRACE-MEASURED` only after the complete 64-row, 264-update, 13-checkpoint trace
   and update-256 anchor exist;
2. `A01-RAW-PHASE-INFORMATION-BOUNDARY-INVALID` only after a listed EVAL/old-result/residual-path
   contamination occurs; and
3. `A01-RAW-PHASE-INCOMPLETE` for missing admission, counts, measurements, anchors, or cap stop.

The first branch cannot match because every scientific observable is absent. No information-flow
contamination was observed because no learner path ran. Missing admission and all required counts
fit the third branch's incomplete condition, but the runner did not emit a summary or branch.
Accordingly the durable disposition is the narrower
`QUARANTINED_PRE_RUN_LAUNCHER_PAYLOAD_LOSS`, with **no scientific branch output and no polarity**.

This failure classification is not inferred from an error string. It is reproduced by the exact
executed `runner.sh` bytes, the two-line task log, the supervisor control files, and direct absence
of every admission/result artifact.

## Preparation deviations retained

Before the accepted task:

1. an exact-SHA fetch/cat-file preparation timed out with exit `124` before task/worktree
   acceptance;
2. a later command used invalid `agent-task start` and was rejected before acceptance;
3. the operator twice reported a clean worktree incorrectly;
4. the first checkout remained in a partial-clone HTTPS blob fetch and held `index.lock`; only that
   abandoned preparation process tree and broken empty worktree were cleaned; and
5. the final accepted wrapper truncated the command to `cd`.

The pre-accept failures created no scientific root, receipt, RNG, model, or process. They are
transport/preparation history, not retries and not evidence. The incorrect clean claims are
explicitly superseded by the authoritative `5,193`-deletion porcelain observation.

## Bounded reading and dependency

Engineering implementation is accepted; execution transport is not. The precise dependency is a
verified `wsl_4070` exact-SHA sparse-worktree materialization plus an `agent-task` single-command
transport that preserves the complete joined `admit-memory && runner` payload. Until that
dependency is repaired independently, A01 is not runnable on the required route.

No retry, resume, local fallback, tolerance change, threshold change, row change, or second task
was attempted after supervisor acceptance. A/RECON objects have no consumption state, so this
technical failure consumes no scientific object. The same RAW phase trace remains unobserved.
