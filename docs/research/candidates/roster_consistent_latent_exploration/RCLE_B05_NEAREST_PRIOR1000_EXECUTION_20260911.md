# RCLE B05 execution and technical acceptance

The [card](RCLE_B05_NEAREST_PRIOR1000_SCIENCE_CARD_20260911.md) fixes the one new
final1000/master25 comparison,600/10/140/750s caps, B ceiling and end condition.
Source/card commit `3ffa65cb4e1a67182b90dce3822d0018ac623c72` is published on
`codex/rcle`; shared authoring checkout remains
`C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`. No starting changes were present.

Two changed-contract checks passed (pytest2.22s; full invoked command3.1091643s).
They used two supplied FP64 scalars,1000 stubbed update calls, one fixed tensor
change and two checkpoint-tensor loads. Full scientific models, real backward,
optimizer, RNG masters, native episodes and performance observations were zero.
They check old defaults/new root domains, exactly1000 updates, no200 panel,
post-update999 checkpoint and initialization/final/reference primary publication.
The unchanged six B04 checks were reused, not rerun. Independent Astra/high
reviewer `rv_ah_rcle_b04` returned PASS without material findings, read-only command
wall1.1534143s. Actual native completion/runtime remain unmeasured at preparation;
an interrupted batch can remain outside completed-block counters. Technical
acceptance does not pre-accept a future scientific result.

Source changes are explicit arguments on the existing nearest-prior run plus a
fixed B05 adapter/entry/wrapper; B04 script/wrapper retain their exact bytes and
defaults. No §4 machinery or budget exception. Card details, counts and review are
in [PREPARATION_FACTS.json](b05_nearest_prior1000_20260911/PREPARATION_FACTS.json).
Owner new-card item20260911-rcle-001 is recorded with an object-selection audit row;
live main owner reviews were[] at restart and publication.

## Exact remote inputs and planned acceptance

- Node `wsl_4070`, SSH `hmasd-wsl-node`; Linux CPU FP64, one compute thread.
- Interpreter `/home/wu/.venvs/hmasd/bin/python`; supervisor `/usr/local/bin/agent-task`.
- Handle `rcle-b05-nearest-prior1000-s25-20260911`.
- Detached cwd `/home/wu/hmasd-worktrees/rcle-b05-nearest-prior1000-s25-20260911`.
- Output cwd/`temp/directions/roster_consistent_latent_exploration/exp/b05-nearest-prior1000-s25-20260911`.
- Supervisor receipt `/home/wu/.agent-tasks/rcle-b05-nearest-prior1000-s25-20260911`.
- Source staging `/home/wu/hmasd-inputs/rcle-b05-nearest-prior1000-s25-20260911/source.bundle`.

Exact source was fetched from the published direction bundle into the remote
repository, then checked out detached at3ffa65cb4. The new cwd and supervisor handle
were absent before staging. `bash -n` accepted the literal LF wrapper; the staged
HEAD equals the source above. [STAGING_FACTS.json](b05_nearest_prior1000_20260911/STAGING_FACTS.json)
retains the command and shell evidence. No model/environment/admission/run was
executed during staging. Current live main compute/Monitor configuration controls
observation; it is independent of the frozen source checkout.

The committed [LAUNCH_COMMAND.txt](b05_nearest_prior1000_20260911/LAUNCH_COMMAND.txt)
is submitted exactly once. Sequential learned/reference arms each run destination
memory admission&&runner inside their complete600/10 external timeout; internal
598/8 limits leave a reporting margin, and the entire native chain has610s outer
timeout. Native arm timings include startup and exit; chain wall is not added
again to those arm walls. All additional support is charged separately once.

Acceptance, actual Monitor dispatch/adoption and terminal collection are pending
until direct receipts are recorded. After accepted launch DM sends MONITOR_ADD to
the endpoint in live main `.codex/hmasd-monitor.toml`; dispatch alone is not adoption.
DM stops routine polling, returns pending collection and resumes on Root's routed
terminal fact. No extra seed, panel, retry, successor or local fallback is selected.

## Retention and cleanup inventory

At terminal collection preserve all checkpoints, panels, completed-block records,
summaries, admissions and supervisor/timing logs, then take in the result against
the card and publish E0/intake/brief/audit. Preserve unique source/evidence before
authorized completed remote checkout/staging reclamation. Root integrates and
accepts retention/reclamation; shared authoring checkout remains in use.

The B05 test creator's exact scratch at
`temp/directions/roster_consistent_latent_exploration/test/b05-nearest-prior1000-20260911`
contains6 files/189324B. Automatic approval review rejected the one exact-path
checked PowerShell removal before process creation as `blocked by policy`.
It remains with DM creator ownership; no bypass/repeated removal. The historical
B04 scratch has its separate existing exception and was untouched.
