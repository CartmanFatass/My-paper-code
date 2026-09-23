# Result execution through the admission kernel

New result-bearing Python entries use `scripts/hmasd_launch.py launch` on the actual
executing node. It selects the configured interpreter, detaches the admitted process and
returns a JSON manifest with native identity and output paths. Do not generate a per-run
PowerShell or shell wrapper or call the scientific runner directly. This method does not authorize
research or lift the owner's pause.

## Prepare and invoke

Commit and publish the exact inputs. `--snapshot` prepares a retained detached linked worktree
from that SHA; author edits are excluded and may continue. Without that option, the supplied
source worktree must remain clean and unchanged. Snapshot preparation shares the original Git
common directory and claim store; it does not clone, evict, or clean old snapshots.
Read the node, interpreter and canonical project location from `.codex/hmasd-compute.toml`.
Without `--node` the kernel takes `HMASD_CONTROL_PLANE_NODE`, then the file's
`[control_plane_by_platform]` entry for this platform, then `control_plane_node`; one tracked
file therefore serves the Windows and the WSL checkout. A remote node is always named.
The live canonical checkout must have current `docs/research/RESEARCH.md` and compute config;
a frozen source worktree cannot override the owner's current pause or assigned lead.
`control_source.remote` and `control_source.ref` pin the authority independently of the
canonical checkout's branch (currently origin / refs/heads/main). Relevant pause/state/lead
must agree with the fresh published version; unrelated prose need not match. Preserve the
assignment's expected lead in `--lead`; do not silently substitute a newly assigned lead.
An explicitly resumed index uses `**Owner pause: lifted**`; missing, ambiguous and unfamiliar
states fail closed. Only an owner-authorized update can change that state.

The following is command syntax, not a ready-to-run experiment. Substitute a full published
SHA, the exact active direction's Lead runtime cell, a fresh output tag and the frozen
scientific argv. The runner's output argument must name the same directory as `--output`.

```text
<configured-python> scripts/hmasd_launch.py launch
  --node <executing-node> --source-root <author-checkout> --snapshot
  --direction <direction> --lead "<exact-current-lead>" --sha <full-sha>
  --output runs/<direction>/<fresh-tag>
  -- scripts/run_<object>.py --out runs/<direction>/<fresh-tag> <scientific-arguments>
```

On Windows invoke the configured Python directly: the kernel hides and detaches the child;
there is no second `Start-Process` wrapper to maintain. On a Linux node (`local_linux`
included) do the same: the kernel starts the child in its own session, so no `nohup` or
`setsid` wrapper is needed, and it prepends the node's `path_prefix` to the child's `PATH`
(the native C++ loader resolves `ninja` from there, not from the interpreter). On a remote node invoke the same
kernel in the configured supervisor's command. Do not treat the supervisor accepting its
command as scientific-run admission; retain the returned native manifest as well.
Remote sparse checkouts must include the current compute config and research index in their
canonical repo; unavailable or stale policy is a refusal, never a reason to fall back to an
old source snapshot. Synchronizing policy does not resume research.

Snapshot output remains at the declared author-checkout run path; the returned manifest gives
the actual execution cwd/source and stable operation reference. Relative code inputs refer to
the snapshot. The migrated FOLR `--generic-summary` path remains caller-relative and requires
`--generic-summary-sha256`; its bytes are verified and saved before training, then interpreted
after the completed fit. Other consumers need their own declared external-input contract.
Snapshot launch removes PYTHONPATH/PYTHONHOME/PYTHONUSERBASE and disables user site and bytecode
writes. Configured site packages, editable dependencies and remaining numerical environment
are still environment dependencies, not proven immutable by Git or isolated from the same UID.

The kernel serializes admission through the child handshake. It rechecks policy and source,
applies the existing actual-node memory-floor check immediately before release, and preserves
a claim before uncertain external effects. Changing only the output tag cannot bypass that
claim within the same node and Git common directory, including its linked worktrees.
Independent clones and other nodes do not share that claim store; reconcile their accepted
handles before moving execution. A lost acknowledgement, timeout or missing PID is unknown.
Ordinary replay of the same request returns the existing operation before new-effect gates;
it never retries even a known spawn/preflight failure. Changed inputs at an existing output
tag refuse with a mismatch. Explicit new attempts are not implemented; changing tags, deleting
outputs or TTL expiry does not provide that capability. A short-lived admission is
single-use and bound to the child, parent, interpreter, source, direction and exact argv.

## Runner integration and observation

Each new entry calls the following after argument validation and before creating an output,
environment, learner, checkpoint loader or result-bearing evaluator:

```python
from scripts.hmasd_admission import require_admission

admission = require_admission(__file__, direction="<direction-id>")
# If the scientific CLI carries --launch-sha, require it to equal admission["sha"].
```

Keep the CLI import path resolvable from the repository root, as in the migrated FOLR entry.
The new-runner source regression checks for this call; runtime tests cover missing, expired
and mismatched admission. Review still verifies that the call precedes scientific effects.
Tests isolate the scientific loop with an explicit mocked admission; production runners have
no test/bypass switch.

Retain the manifest, preflight, stdout/stderr and `process-exit.json` in the run's output.
Use `<configured-python> scripts/hmasd_launch.py status <operation_ref>` on the original
executing node. A manifest path or original output directory is also accepted. This is read-only
and works during a pause, dirty author edits or control-network failure; it never grants retry.
The response separates admission, runner/supervisor identity, exit witness and basic artifact
presence. Missing or conflicting evidence stays unknown; presence alone does not certify
scientific completeness. A copied remote record does not establish a local process identity.
The manifest's `process` identifies the detached supervisor; `runner_process` identifies the
scientific child. Link this manifest/operation from the existing NOTES.md entry and pass the
same reference to any observer, without retyping its fields. The supervisor waits for the child's actual
OS exit before writing the terminal witness; it does not certify scientific success. Loss
of the supervisor can prevent that write; preserve uncertainty rather than inventing an exit.
Runner summaries, curves and complete scientific outputs remain required.

## Source and publication worktree reclamation

`--snapshot` creates a locked, complete linked worktree per operation. These copies are
disposable source material, but Git does not automatically remove them when a runner exits.
After collecting and verifying the outputs, run the collector from the maintained control
checkout on the original executing Linux node:

```bash
<configured-python> scripts/hmasd_snapshot_gc.py
<configured-python> scripts/hmasd_snapshot_gc.py --snapshot <snapshot-basename>
<configured-python> scripts/hmasd_snapshot_gc.py --apply --snapshot <snapshot-basename>
```

Repeat `--snapshot` to select multiple previewed candidates. The default is read-only.
If Linux denies inspection of a protected same-user process (for example `systemd --user`),
the command refuses. On hosts with existing passwordless sudo, explicitly add
`--sudo-process-scan` to run only the read-only `/proc` probe via `sudo -n`; all Git checks
and removal still run as the original user. Missing sudo access remains a refusal.
Apply rechecks each selected snapshot under the admission lock and removes only its Git
worktree, without force. A terminal exit witness, absent native processes, consistent
claim/source identity, externally retained outputs, durable branch/tag reachability and
absence of dirty, untracked or ignored files are required. Local process references also
block reclamation. Unknown/unclaimed operations and unsupported process inspection remain
preserved; age, exit-zero alone or an apparently idle direction does not grant deletion.
Keep claims, manifests, exit witnesses and run artifacts: they retain status and duplicate
prevention after the source directory is gone. Cleanup grants no relaunch.

On sparse remote checkouts, a missing manifest can be a checkout omission. Check the
published commit for the exact operation's original records and match its claim, SHA,
host, source, output and native process identities before recovering them. Materialize
the relevant run directories with `git sparse-checkout add` (preserving existing paths
and untracked outputs), then preview again. Do not synthesize terminal records or treat
a copied record from another node as local evidence. Retain the run directories in the
sparse selection so a later checkout does not discard the recovered status handles.

Ordinary authoring/publication worktrees are outside this collector. At a completed
publication boundary, remove an owned temporary publication checkout with ordinary
`git worktree remove <path>` only after verifying its commits are durably reachable,
including ignored/untracked evidence in the clean-tree check, and ensuring no active task,
process or accepted operation depends on the path. Retain branches and run evidence.
Never sweep all worktrees, delete by age or use `--force` to bypass these checks.

Historical frozen runners and `hmasd_run.py` retain their old interfaces at their recorded
SHAs. They are not silently claimed to have this new boundary. The first migrated existing
entry is `run_folr_entity_augmentation_repeat_b01.py`; all new result entries must adopt the
guard. The not-yet-implemented FSD matched-information B01 entry must do so when implemented,
without changing its frozen scientific contract or starting it during the pause.

This is cooperative mistake/replay prevention, not OS isolation from a same-user process
with arbitrary shell and source-write access. That process could alter the guard itself.
An admission also does not certify scientific fit budgets or externally stored artifact
contents; preserve their prospective scope and declared digests in the existing run contract.
