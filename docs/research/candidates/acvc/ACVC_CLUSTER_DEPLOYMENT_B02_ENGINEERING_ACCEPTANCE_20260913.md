# B02 engineering review and execution acceptance

## Bound scope and independent review

Source commit: `be76f696cb773f2e5db8f4d55ebff1f3b6335ae6`, published on `origin/codex/acvc`. The B02 science card supplies the L0; code only parameterizes the old publication's expected identities, binds the new original fit and adds synthetic tests and the narrow launch wrapper. DM owns implementation and technical acceptance. Native independent Reviewer `/root/acvc_b02_review` examined this commit read-only, including `launch.sh`; no tests or fit were executed by the Reviewer.

Full substantive final review, received natively 2026-09-13:

> No material correctness finding in `be76f696cb773f2e5db8f4d55ebff1f3b6335ae6`.
>
> - B02 identities reach training, checkpoint metadata, evaluation rows and final publication consistently. B01 defaults remain `21457/31457`.
> - Paired episodes share initial-world seeds; action streams remain separate. Each arm privately loads the checkpoint and resets recurrent state, bindings and previous commands.
> - Final reductions retain float64 differences, sample SD, conditional SE, signed counts and the specified ±.01 boundaries. Damaged panels invalidate only dependent contrasts.
> - Computed configuration counts match the card: 256 rollouts, 1,024 optimizer steps, 192 evaluations and 180,224 team ticks. The source changes total 80 added/5 deleted lines; the runner is 46 lines.
>
> One scope declaration discrepancy: `experiments/candidates/acvc/cluster_deployment_b02/launch.sh:6` adds an output-existence refusal, while card §4 declares no added guard. This does not threaten the declared fresh-directory run. Minimum reconciliation: explicitly name its narrow original-output preservation purpose in the card, or remove the unnecessary check. No other prohibited machinery was added.
>
> Residual limits: no tests or scientific fit were run by this reviewer. The launch wrapper fixes 580 seconds internally; the planned outer TERM595/KILL+1 command must enclose admission, both publications and exit. Actual runtime threads, completion, measured wall/support costs and remote checks remain execution evidence for DM acceptance. Scientific reading supports only uncertainty conditional on one fitted endpoint, not training-population superiority.

DM response: retain the narrow output-preservation refusal and explicitly declare its purpose in card §4. This is a documentation repair with no source/identity/science change. The code review is not the separate Convergence scientific review.

## Actual remote checks and DM technical acceptance

The configured remote node received a Git bundle containing only committed, already published history from the accepted K source through `be76f696cb773f2e5db8f4d55ebff1f3b6335ae6`. Bundle verification passed; the detached checkout at `/home/wu/hmasd-worktrees/acvc-cluster-b02-be76f696c` reports that exact HEAD and a clean source tree. No uncommitted source was copied. Direct GitHub fetch and an accidental lazy-fetch lookup stalled; only those owned synchronization processes were stopped, and the bundle route recovered source availability. This did not launch, retry or stop a scientific invocation.

The two focused files initially collided as `test_protocol` under pytest's prepend import mode (collection-only exit 2, 0.17 s whole check). Repeating the identical synthetic tests with `--import-mode=importlib` and a new unique basetemp produced **18 passed in 0.07 s**, whole check 0.16 s, exit 0. This is a concrete collection repair, not a repeated scientific test. Both checks used the exact published source, CPU/thread environment fixed to one, `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`; no model fit, scientific RNG output or result-bearing invocation occurred. Preserve both receipts. The corrected scope wording resolves the Reviewer's sole finding.

**DM accepts the unchanged published source for the one original B02 invocation.** The exact detached command, timeout enclosing admission through both publications/exit, output identity and finite limits are in `ACVC_CLUSTER_DEPLOYMENT_B02_EXECUTION_FACTS_20260913.json`, published before launch. Runtime acceptance remains conditional on actual adjacent admission and the original handle's facts; test/review completion is not a scientific result. Convergence independently reviews the new evidence and proposed development conclusion at intake. Support coverage is incomplete and is not reported as zero or fully certified.
