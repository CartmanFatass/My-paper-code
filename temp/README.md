# Local temporary workspace

`temp/` is the only repository-local scratch root. Everything below this file
is ignored by Git and may be deleted after the command or task that owns it has
finished.

Use these conventional subdirectories:

| Path | Purpose |
| --- | --- |
| `temp/directions/<direction-id>/exp/` | one direction's disposable experiment runs, checkpoints, profiles, and captured output |
| `temp/directions/<direction-id>/test/` | one direction's pytest base directory, fixtures, test databases, and build probes |
| `temp/tests/` | pytest base directories and synthetic fixtures |
| `temp/runtime/` | local process state, sockets, receipts, and transient databases |
| `temp/cache/` | rebuildable compiler, model, and benchmark caches |
| `temp/handoffs/` | short-lived large payloads passed between local collaborators |
| `temp/downloads/` | disposable downloads and extracted third-party material |
| `temp/sessions/` | compatibility location for older scripts that already use it |

Direction-specific work always uses `temp/directions/<direction-id>/`. The
shared `temp/tests/`, `temp/runtime/`, and `temp/cache/` paths are reserved for
genuinely cross-direction infrastructure and legacy compatibility.

Do not create new root-level `temp_*`, `tmp_*`, cache, runtime, or ad-hoc
worktree directories. Code that needs the operating system's temporary
directory should use the standard `tempfile` API and clean up its context.

Git worktrees are not temporary files and must not be nested in this checkout.
New HMASD worktrees belong under the single sibling root
`C:/Projects/HMASD-worktrees/<name>`. The primary checkout remains
`C:/Projects/HMASD`. Use `scripts/new_hmasd_worktree.ps1` for new linked
worktrees so they do not spread across `C:/Projects`, OneDrive, or the checkout.

Durable source, research decisions, and results that must survive cleanup do
not belong here; move them to their documented project or research directory
before deleting the owning scratch directory.
