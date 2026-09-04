# CRTO RAW phase-trace A01 remote-prerequisite engineering evidence

Date: `2026-09-04`

Object waiting on this prerequisite: `CRTO-RAW-PHASE-TRACE-A-RECON-R01`

Engineering disposition: `REMOTE_SPARSE_MATERIALIZATION_NOT_ESTABLISHED`

Scientific branch: **none; no technical probe or scientific task was accepted**

Claim ceiling: direct engineering facts returned by CM about one bounded attempt to materialize a
new exact-SHA sparse worktree on `wsl_4070`. This record does not contain resource admission for a
scientific invocation, RAW training, a checkpoint trace, an update-256 anchor, competence, or
residual-mechanism polarity.

## Frozen prerequisite objective

Before any fresh A01 invocation, CM had to establish both of these facts:

1. a new direction-specific worktree at exact pushed SHA
   `c8247c2d19ac7965208c397a2a87519a1efb6310` is clean and contains every configured frozen
   runtime surface; and
2. one non-result `agent-task` probe preserves and executes a single command argument containing
   the complete joined remote `admit-memory && CRTO runner project-cost` payload.

The second stage was prohibited until the first passed. The bounded phase could not launch the
A01 `run` subcommand, create a scientific result root, or recover/reuse the earlier failed task.

## Exact identities and direct return

CM bound the pushed ref `origin/codex/cm/crto-raw-phase-trace-a01-20260904` to the required SHA and
created only this new remote worktree identity:

```text
/home/wu/hmasd-worktrees/crto-raw-phase-probe-c8247c2d-02
```

The reserved but never accepted technical task identity was:

```text
crto_raw_phase_transport_probe_c8247c2d_02
```

The authoritative supervisor query returned:

```json
{"task":"crto_raw_phase_transport_probe_c8247c2d_02","status":"not_found"}
```

No technical task root, runner script, task log, admission receipt, project-cost output, or
scientific result root exists.

## Sparse materialization observation

The new detached worktree has the correct `HEAD` and the configured nine sparse surfaces. Its
sparse specification is:

```text
/*
!/*/
/environments/
/envs/
/experiments/
/ha_ctse_process/
/hmasd/
/manifold_hmasd/
/scripts/
/tests/
/tools/
```

The sparse-specification SHA-256 is
`4b0ff61ada37c6be9df91651516f3a1b0be7a8d1cac6c5d79c443b4694a5d769`.

Direct counts after `sparse-checkout set` and `sparse-checkout reapply` both returned zero were:

| quantity | observed |
| --- | ---: |
| all tracked files | `5,193` |
| tracked files in the required sparse surfaces | `1,903` |
| required files present | `0` |
| porcelain entries | `5,193` tracked deletions |
| untracked probe files | `0` |

Required absent files included the admission tool, CRTO runner, A01 experiment, accepted B01
experiment, CRTO host, and common-history training module. Runner/preflight importability therefore
was not reached.

## Failure reproduction and stop

CM next invoked `git read-tree -mu HEAD`. The observed process tree was:

```text
git read-tree -mu HEAD
└─ git fetch origin --filter=blob:none
   └─ git-remote-https origin https://github.com/CartmanFatass/My-paper-code.git
```

It remained blocked in the partial clone's on-demand promisor fetch for `3m48s`. CM stopped exact
CRTO process-tree PIDs `45458` through `45461` within the phase's `300`-second machine-time bound.
Post-stop checks found those PIDs gone and no worktree `index.lock`. An unrelated concurrent remote
Git fetch was not touched.

Because the clean and complete worktree prerequisite failed, no `agent-task` argument-transport
probe was attempted. The one-argument encoding is therefore still unverified end to end rather
than negative. No preflight, CPU/GPU learner work, predictor, RNG master, model, optimizer,
checkpoint, evaluation, old result, or confirmation namespace was accessed.

## Bounded dependency

The reproduced dependency is the `wsl_4070` repository's HTTPS/promisor-blob transport needed to
materialize a clean, complete exact-SHA sparse execution surface. This is an execution dependency,
not scientific evidence or polarity. Bypassing the clean-worktree gate would make any later
supervisor acceptance nonconformant.

The unchanged A01 trace remains unobserved. A later attempt requires an independently verified
materialization repair first, then a successful single-argument transport proof, and only then a
new task identity, new result root, exact pushed SHA, and fresh remote 4-GiB admission joined
immediately to the exact runner.
