# Technical self-check — ACVC cluster MAPPO comparison B01

Source belongs to `C:/Projects/HMASD-worktrees/codex-acvc`, `codex/acvc`; exact source revision follows the commit containing this record. Current frozen card: `2f90398a865a0eaebc78f2af603cb4d4a54487de`. The selected external source is unchanged `marlbenchmark/on-policy` at `de66d7a4b23fac2513f56f96f73b3f5cb96695ac`; local fixture imports use its read-only collection checkout. Remote execution will use an isolated source copy at that commit, with no interpreter upgrade.

## Checked contract and actual result

The focused suite has 17 cases. Sixteen passed initially; the C fixture incorrectly used H8 while preserving chunk32, so the protected replay helper rejected its impossible reshape before any optimizer step. The fixture was corrected to H32, without a production-source or scientific-card change; its focused rerun passed. Pytest times were4.73s and3.91s (command walls6.187s and5.584s), far below the five-minute directory budget. No native UAV simulator, scientific fit, scored panel or extra allocation was invoked. Known synthetic support work:376 transition calls and12 optimizer steps (M actor4/critic4, C joint4); one density-only backward is also check work.

Tests cover scalar summed tanh density (including extreme raw actions), replacement-head parameter membership/gradients; private actor independence from global and other-agent rows/state; actual adapter reward and terminal masks, terminal GAE, replay likelihood agreement; all80 selected chunks at the actual256-step buffer shape; separate actor/critic Adam steps and finite nonzero actor/critic/head movement; final model/ValueNorm serialization/reload and actor-only evaluation with critic/global access unavailable; unchanged C collect/update arguments and three private final loads; all primary boundaries, adverse worlds, offline reducer, partial independent operands and wrong seed/snapshot/length/nonfinite rejection.

Commands used the existing Python3.10 scientific interpreter, `-X utf8 -m pytest -q -p no:cacheprovider`, explicit `HMASD_ON_POLICY_ROOT`, `PYTHONDONTWRITEBYTECODE=1` and two task-specific `--basetemp` directories. Initial target was the complete new test directory; rerun targeted only the corrected C fixture. Exact counts and test paths are in `SELF_CHECK.json`. `git diff --check` passed. Protected C/native source remains reused rather than altered. No native smoke or runtime-cost pilot is selected.

The three-coordinate summed likelihood must occupy one buffer column; otherwise upstream broadcasting duplicates the PPO term. The new adapter fixes that width and creates the actor optimizer after replacing its action head. The declared upstream GAE/ValueNorm/clipped Huber/standardization behavior is retained as a complete-method recipe. Synthetic conformance does not establish native performance, tuned competence or the F−M comparison. Scientific reading reuses the card's explicit private-information assumption and fixed-source analysis; no new mechanism or comparator selection follows from these implementation checks.

## Remaining technical acceptance

Required independent Astra/high review remains pending at this record. DM will inspect its complete findings, repair material issues and publish exact source/dependency/commands before each original's fresh remote admission. Runtime wall/RSS/CPU and full raw/checkpoint retention will be reported from actual executions. Synthetic success neither spends nor enlarges the two-original grant.

## Local scratch cleanup

The creating DM attempted native PowerShell `Remove-Item -LiteralPath ... -Recurse -Force` after verifying both resolved targets were exact children of this checkout's `temp/directions/acvc/test`. Runtime automatic approval rejected the command with `rejected: blocked by policy` before execution. Both `cluster_mappo_b01_20260914_01` and `cluster_mappo_b01_cfixture_20260914_01` are retained. No alternative deletion or escalation was attempted. This is a local cleanup limitation, not scientific polarity or a native invocation.
