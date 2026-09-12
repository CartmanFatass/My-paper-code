# Desktop WSL project creation failure

## Observed behavior

The owner can select `\\wsl.localhost\Ubuntu-24.04\home\fires\projects\HMASD` in the Windows folder picker, but Create Project displays a generic red failure. Windows Node can stat the directory and read `.git/HEAD` through both `wsl.localhost` and `wsl$` forms.

Installed package: `OpenAI.Codex_26.908.4834.0_x64__2p2nqsd0c76g0`. The installed WSL app-server reports `Codex Desktop/0.154.0-alpha.6.2` and runs with Windows CODEX_HOME mounted in WSL. Agent environment is already WSL.

## Independent backend reproduction

Root started the installed binary with an isolated CODEX_HOME and sent initialize (experimentalApi enabled), then project/create with a name, idempotencyKey and roots array.

- A root path using the owner’s UNC form returned JSON-RPC -32600: `Invalid request: AbsolutePathBuf deserialized without a base path`.
- The native root `/home/fires/projects/HMASD` succeeded in the same isolated process.
- No production project, task, model turn, or session database was changed by this probe. The owned probe scratch was removed after its receipt was retained.

The installed Desktop source forwards project rootPaths as roots[].path to project/create or project/update. A production startup assignment-sync log also contains the AbsolutePathBuf error. These facts identify a concrete UNC/Linux boundary failure consistent with the UI symptom; no create-specific detailed UI error was captured, so the isolated probe is not presented as a captured production request.

## Current boundary

Native-path backend acceptance does not establish that the Windows Desktop file, workspace and existing-task flows accept that same representation. Changing a project root also does not prove an existing task has changed cwd. No installed application patch, live database rewrite, or production project replacement was performed. Existing task IDs and project associations remain intact.

The old staging script in the external migration records is diagnostic only. It is not a verified end-to-end cutover tool. Desktop project and existing-task path acceptance remain pending; this issue prevents declaring the whole migration complete.

## Local evidence and recovery

Records: `/home/fires/migration-records/hmasd-wsl-20260912/ROOT_PATH_PROBE.json` and `.stderr.log`; installed protocol schemas under `protocol/`; consistent read-only Desktop database backup and configuration snapshots under `root-desktop-backup/`.

The Windows repository remains at `C:\Projects\HMASD`. The Linux copy is at `/home/fires/projects/HMASD`. The former Linux candidate is sealed under `/home/fires/migration-backups/hmasd-before-root-redo-20260912T020931/`. Research remains paused.
