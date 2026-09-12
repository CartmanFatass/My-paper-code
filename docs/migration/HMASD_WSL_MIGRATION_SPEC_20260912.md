# HMASD Windows-to-WSL project migration specification

Owner authorization: 2026-09-12, detailed migration specification and parallel Luna/xhigh execution.
Coordinator: current task 01a094b3-67ae-7653-9b4d-49fd9d7f1ccb. ALL migration reports go only to this task (native parent /root). The research Root 01a07249-b095-7821-8ce2-e9c32ba85267 in repository configs is NOT this migration parent. Do not send any migration messages to research Root, Relay, Monitor, or Transport. This is infrastructure migration, not authorization to resume research.

## L0 and completion target

Move daily HMASD authoring to /home/fires/projects/HMASD on native Linux storage, retain Windows Desktop and its existing task identities, preserve scientific assets and every source recovery path. Windows source /mnt/c/Projects/HMASD and its sibling/app worktrees remain intact for rollback. Existing WSL trial is updated, not discarded. Remote execution node, scientific meanings, invocation budgets, Pro bindings, monitor/relay IDs and paused research state remain unchanged.

Completion means: latest committed source state and real uncommitted changes preserved; ignored evidence copied; source refs and worktree states accounted for; Linux control-plane dependencies and configuration verified; Desktop project/task path cutover prepared and applied through a supported interface or a stopped-app operation, with any pending user restart reported explicitly. Do not claim the running task moved merely because a directory was copied.

## Ownership and sequencing

1. repo (Luna/xhigh): exclusive target Git/index/refs and working files except root temp/. Reconcile source and target history, preserve target config before syncing, carry real source changes while separating CRLF-only checkout differences. Own sibling target /home/fires/projects/HMASD-worktrees and migration of currently registered authoring/app worktrees. Retain snapshots/refs for any incompatible target state. Commit nothing; report ready for Root integration. Coordinate any final worktree registration within this same owner.
2. evidence (Luna/xhigh): exclusive target root temp/. Copy all source temp content, including hidden and ignored data, preserving bytes/symlinks and relative paths. Never treat temp as disposable. No delete, no overwrite of a differing target file without a retained conflict backup. Source stays unchanged. Record exclusions (normally none), counts/bytes, missing/error/conflict paths and content verification.
3. runtime (Luna/xhigh): own isolated /home/fires/.venvs/hmasd-control and records/runtime/. Read configs/scripts, prepare exact minimal patches outside target until repo owner finishes. Inventory old Windows path references in active control-plane entrypoints; preserve historic evidence literals and Windows Agentify arguments. Verify Linux Git/Python/Node, config TOML and seven agent files, SSH alias and read-only remote access. No experiments, browser Send, package upgrades of global/shared environments, or live monitor rebinding. Propose dependency set from repository declarations, install only needed local control-plane dependencies in isolated env, record versions and limits.
4. desktop (Luna/xhigh): own records/desktop/. Inspect actual installed Desktop project/task storage and documented supported path-edit mechanisms. Prepare reversible project + task cwd cutover for this HMASD project only, preserving project ID, conversations, model/config overrides and sibling endpoints. Never directly modify live SQLite or global state. Do not restart/terminate Desktop. Provide an exact offline cutover procedure/script with backups, recovery, validation, and clearly scoped mappings; no broad string replacement or unrelated user config edits. Report whether UI-supported mutation is available.
5. Root: specification, coordination, accept results, apply runtime patches after repo handback, commit explicit approved paths and push checked-out branch immediately, write final receipt, decide/apply supported Desktop cutover and record any restart boundary. Only Root finalizes repository commits. Workers are not alone; preserve others' work and avoid root temp for migration reports.

## Data and Git rules

- Preflight capture source/target HEAD, branch refs, status, source worktree registry and relevant file digests. Source HEAD currently 64561c64f47fed8a86b39ccf27601db25d4d77df; trial HEAD 678f069e1b0b70271fba742332d0871ae22028cd; re-read before action.
- Reconcile ancestry before fast-forward; preserve each side's unique commits and dirty changes. Existing config includes intentional model selector fix; target adds Windows Node bridge command. Preserve both.
- Linux Git initially sees thousands of CRLF differences in source. Detect normalized equality; never stage/commit a mass line-ending rewrite or change byte-bound scientific captures.
- Never git reset/stash, force-push, history rewrite, source deletion, worktree prune, or removal of evidence. Do not interpret Windows C:/ registry paths as missing without converting them to /mnt/c.
- Maintain named authoring branches and their bound SHA/dirty contents. Rebuild Linux Git worktree links instead of using .git files pointing to Windows. Do not advance a worktree to another SHA merely to simplify copying. Inactive nonregistered historical scratch is retained in source unless separately inventoried/copied as evidence; it is not silently accepted or deleted.
- Preserve .remember/, personal docs, ignored research logs and runtime receipts outside temp. Exclude regenerable Python caches only when explicitly logged. Do not copy Windows virtual environments as Linux executables.
- Use rsync without --delete; preserve conflicts before replacement. Verify copied evidence with a checksum-based comparison or equivalent per-file digest manifest. Record source mutation during copying and reconcile to a stable boundary. A source file that changes prevents declaring that file verified, not independent migration progress.

## Runtime/path boundaries

- Local WSL control plane is distinct from remote wsl_4070 (/home/wu/...); do not replace remote paths with /home/fires paths.
- Windows Agentify remains Windows; command may be /mnt/c/Program Files/nodejs/node.exe and file arguments must remain Windows-readable paths, converting Linux paths via wslpath at actual interfaces.
- Active scripts/configuration may change only the concrete local path/runtime boundary. Historic requests, launch commands, hashes, artifacts and scientific cards retain their recorded original values.
- Existing accepted run observation and task IDs are not replaced. Migration checks are read-only/import/short engineering checks; no new result-bearing runs, resumes or Pro requests.

## Acceptance and rollback

Each worker produces a concise JSON/Markdown receipt in its records subdirectory: actual actions, source/destination, preserved/excluded/conflicting items, commands/check outcomes, artifacts/digests as relevant, unresolved limitations, and handback state. Root verifies material evidence and integration changes without repeating expensive successful checks.

Acceptance checks: Git history/refs/recoverability and status delta; no remaining accidental Windows Git linkage in runnable Linux worktrees; evidence reconciliation; TOML/config and seven agents; minimal imports + one meaningful control-plane check; SSH routing; Windows bridge read-only handshake only if needed; Desktop actual project root and task cwd after cutover.

Rollback: original Windows source/worktrees remain usable; restore explicit backed-up Desktop path records while app is stopped. Preserve new Linux commits/evidence before reverting daily authoring. Agent WSL setting is already working and must not be toggled unnecessarily. Any required app restart is the final boundary after concrete cutover artifacts and backups are ready.

Budget: one migration and focused fixes/checks, no scientific compute. Continue independent work during copy/build waits. Stop the affected action on ambiguous destructive effects, active overlapping writer, incompatible dirty history, or missing credentials; report exact evidence and continue independent authorized work. No standing background service or recurring automation is introduced.

## Accepted scope refinements during execution

- Runtime may add the missing local WSL SSH stanza for the existing hmasd-wsl-node only, preserving existing configuration/known_hosts and reusing the existing Windows identity in a Linux mode-600 task-specific key. Record exact local files and backups; no new remote credentials, DNS/VPN changes or remote mutation. This resolves a migration prerequisite within owner authorization.
- All migration reports target this migration task only. One runtime progress message reached the historical research Root; that task performed read-only checks and its attempted corrections were rejected by automatic approval. No files changed or research resumed; the routing has been corrected.
- Root independently reproduced project/create rejection of UNC roots by the installed Linux backend and success with native /home paths in an isolated CODEX_HOME. The records/desktop staging script is not authorized for live installation merely by its existence; it must address native paths and actual backend/cache reconciliation, then pass review. Current running Desktop state is unchanged.
- ACL-denied source temp directories remain a concrete evidence-copy limitation after both Windows and Linux read attempts fail. Preserve exact denied-path inventory and Windows originals; do not remove ACLs or claim their unknown contents were copied. Complete and checksum-verify accessible content independently.
