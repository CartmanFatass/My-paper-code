# CADC-B01 preservation and scoped cleanup

Cleanup owner: original DM `/root/dm_cadc_start`. **All four assigned remote terminal targets are removed and verified absent.** Root accepted the complete intake and retained archives on main `9111b9b1e` and `363bda2a0`, then assigned this exact remote closeout. Both archive Git-blob digests were independently verified against main before removal. Source, complete result/checkpoint archive and supervisor evidence remain in [RESULT](CADC_B01_RESULT.md). The shared `codex/cadc` authoring checkout remains this direction's live editing/repository dependency.

## Exact terminal removal inventory

| Target | Preserved content | State |
| --- | --- | --- |
| `/home/wu/hmasd-worktrees/cadc-b01-9302-20260912` | Exact source22e009c93 is published; both complete output/checkpoint trees are in CADC_RESULTS.tar.gz with verified archive/member digests | Removed; absent on disk and from worktree registration |
| `/home/wu/hmasd-inputs/cadc-b01-9302-20260912` | Git-blob commands, staging/admission/wall receipts, raw and supervisor archives and logs | Removed; absent on disk |
| `/home/wu/.agent-tasks/cadc-b01-9302-learned-20260912` | Terminal runner, status, exit_code, PID, start_time and task.log retained in CADC_SUPERVISORS.tar.gz | Removed; absent on disk |
| `/home/wu/.agent-tasks/cadc-b01-9302-rr-20260912` | Same complete supervisor evidence | Removed; absent on disk |

Before removal, all four resolved paths matched the exact inventory without symlinks, runtime source was clean at22e009c93, both recorded PIDs were absent and tmux sessions inactive, and both supervisor statuses were finished/exit0. All8 actual scientific output files were byte-equal to the complete archived members with no additional output files. Runtime removal used `git worktree remove --force` at the exact path; only the three other inventoried roots were then removed. Shared remote repository and local authoring checkout were retained; no extra scientific invocation occurred.

[CLEANUP_RECEIPT.json](execution/CLEANUP_RECEIPT.json), verified2026-09-12T22:59:47Z, records disk absence4/4 and registration absence. The deletion batch executed once. Its final shell here-document terminator was consumed as Python, raising NameError after the absence checks; a separate read-only call recovered the receipt and independently verified absence. No deletion was retried and no runtime configuration was changed. Current owner review query returned[]; no unapplied contrary instruction was found.

## Local synthetic test scratch — separately pending

Exact creator-owned path: `C:/Projects/HMASD-worktrees/codex-cadc/temp/directions/contention_aware_decentralized_communication/test/b01-contract-20260912`. It contains two synthetic fixture outputs,8 files; all necessary check/failure evidence is retained in [TECHNICAL](CADC_B01_TECHNICAL.md). Runtime automatic policy rejected the combined cleanup and then isolated PowerShell `Remove-Item -LiteralPath <exact path> -Recurse -Force` before execution, with only `rejected: blocked by policy`. No alternative-shell/program bypass or repeated permission request follows. This DM retains responsibility; the rejection is not a scientific result or reason to park CADC.

The Root-assigned four-target remote cleanup is complete. The separately restricted local scratch remains explicitly unresolved with its creator and was outside this remote-only follow-up. CADC remains ACTIVE/HIGH, recasts:0; the [next investment/use need](CADC_B01_INTAKE.md) is unchanged.
