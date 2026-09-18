# Result execution through the admission kernel

New result-bearing Python entries use `scripts/hmasd_launch.py launch` on the actual
executing node. It selects the configured interpreter, detaches the admitted process and
returns a JSON manifest with native identity and output paths. Do not generate a per-run
PowerShell wrapper or call the scientific runner directly. This method does not authorize
research or lift the owner's pause.

## Prepare and invoke

Commit and publish the exact inputs; use a source worktree kept unchanged during execution.
Read the node, interpreter and canonical project location from `.codex/hmasd-compute.toml`.
The live canonical checkout must have current `docs/research/RESEARCH.md` and compute config;
a frozen source worktree cannot override the owner's current pause or assigned lead.
An explicitly resumed index uses `**Owner pause: lifted**`; missing, ambiguous and unfamiliar
states fail closed. Only an owner-authorized update can change that state.

The following is command syntax, not a ready-to-run experiment. Substitute a full published
SHA, the exact active direction's Lead runtime cell, a fresh output tag and the frozen
scientific argv. The runner's output argument must name the same directory as `--output`.

```text
<configured-python> scripts/hmasd_launch.py launch
  --node <executing-node> --source-root <unchanged-source-checkout>
  --direction <direction> --lead "<exact-current-lead>" --sha <full-sha>
  --output runs/<direction>/<fresh-tag>
  -- scripts/run_<object>.py --out runs/<direction>/<fresh-tag> <scientific-arguments>
```

On Windows invoke the configured Python directly: the kernel hides and detaches the child;
there is no second `Start-Process` wrapper to maintain. On a remote node invoke the same
kernel in the configured supervisor's command. Do not treat the supervisor accepting its
command as scientific-run admission; retain the returned native manifest as well.
Remote sparse checkouts must include the current compute config and research index in their
canonical repo; unavailable or stale policy is a refusal, never a reason to fall back to an
old source snapshot. Synchronizing policy does not resume research.

The kernel serializes admission through the child handshake. It rechecks policy and source,
applies the existing actual-node memory-floor check immediately before release, and preserves
a claim before uncertain external effects. Changing only the output tag cannot bypass that
claim within the same node and Git common directory, including its linked worktrees.
Independent clones and other nodes do not share that claim store; reconcile their accepted
handles before moving execution. A lost acknowledgement, timeout or missing PID is unknown; inspect the same outputs
and process identity rather than launching a replacement. A short-lived admission is
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
The manifest's `process` identifies the detached supervisor; `runner_process` identifies the
scientific child. Record both native identities and artifact paths in the existing NOTES.md
entry and pass the same facts to any observer. The supervisor waits for the child's actual
OS exit before writing the terminal witness; it does not certify scientific success. Loss
of the supervisor can prevent that write; preserve uncertainty rather than inventing an exit.
Runner summaries, curves and complete scientific outputs remain required.

Historical frozen runners and `hmasd_run.py` retain their old interfaces at their recorded
SHAs. They are not silently claimed to have this new boundary. The first migrated existing
entry is `run_folr_entity_augmentation_repeat_b01.py`; all new result entries must adopt the
guard. The not-yet-implemented FSD matched-information B01 entry must do so when implemented,
without changing its frozen scientific contract or starting it during the pause.

This is cooperative mistake/replay prevention, not OS isolation from a same-user process
with arbitrary shell and source-write access. That process could alter the guard itself.
An admission also does not certify scientific fit budgets or externally stored artifact
contents; preserve their prospective scope and declared digests in the existing run contract.
