# P59 corrected input-factory Root handoff — 2026-09-08

Status: READY FOR ONE ROOT DISPATCH; no runtime observation yet.
Authority: [P59](../../portfolio/handoffs/2026-09-08-p59-frrie-corrected-input-factory.md).
This supersedes P47's no-relaunch boundary only for the single corrected check.
No R09 retry, new scientific seed, production repair or second invocation follows.

## Binding and acceptance

- Exact source: `5831dafaab0e47d0c13fe1cbefcc94e5a817b1bc`; standalone
  `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/test_training_input_factory.py`.
- Root stages/launches/observes; same CM collects, same DM intakes.
  CM: `/root/dm_frrie_p47_repair/cm_am_frrie_p47_repair`;
  DM: `/root/dm_frrie_p47_repair`. No alternative executor.
- Host: `hmasd-wsl-node` / configured `wsl_4070`, CPU.
  Historical interpreter: `/home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python`.
  Do not substitute the configured generic3.10 environment.
- Fresh accepted-handle name: `frrie-p59-input-factory-20260908`.
- Fresh detached cwd: `/home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908`.
- Output/admission: `/home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908/temp/directions/finite_resource_relational_inductive_efficiency/exp/p59_input_factory/admission.json`.
- Supervisor log/time: `/home/wu/.agent-tasks/frrie-p59-input-factory-20260908/task.log`
  and sibling `process-time.txt`.
- Exactly one complete120s bound: TERM115s plus5s grace, covering admission,
  imports, factory/checks, output and exit. Fresh adjacent memory admission
  requires physical/effective available memory at least4GiB.
- Existing TEST_ROOT_HEX/TEST_SEED_LABEL, coordinates1–8; eight groups of64:
  maximum512 tapes/512 origin rows/1,536 selections. Zero models, learners,
  optimizer steps, project-native calls or scientific evaluations. Count
  input-coordinate groups separately from learner updates.

Source/static acceptance reuses P47's accepted AST/diff checks and the supported
Torch import correction. The current authoring test has an empty diff against
the bound source. Authoring start `252a8993d14fe301263f35883d5b3fc16a4a1278`
was clean. No production source/test changes are made for P59.

Per-invocation cost: original128-tape3.39s observation suggested approximately14s
generation plus imports/checks for512 tapes, with limited predictive value.
The P47 harness failure1.58s measured no factory work. No timing pilot, warm-up,
sweep or setup experiment. Cap120s for this sole logical invocation; aggregate CPU
unknown, and measured process wall is distinct from staging/collection elapsed.

Primary observation: progress group counts plus terminal JSON, exact exit/trace,
admission and wall/RSS. A pass supports only this TEST factory boundary. A failure
retains trustworthy completed counts/location; missing output alone is not zero.
No historical crash clearance, shared cause, learner result or R09 MEI claim.
Post-learner publication is not exercised or claimed; the bounded diagnostic's
stdout/supervisor receipts are its publication path.

DM prediction: complete all eight coordinate groups/512 TEST tapes and terminal
JSON, low confidence. The repaired import and prior small tape checks support
that forecast; intermittent historical failures and the broader import/grouping
path limit it. Owner prediction: not taken (unattended).

## Exact single launch (remote shell)

Root first stages the exact committed source into the detached cwd above using
the configured network shell. Existing ref-name collisions must be preserved;
a full-SHA fetch with empty refmap can fetch objects without updating the
conflicting remote-tracking name. Staging is not a diagnostic invocation.
Confirm source/path and no accepted handle before the sole Send; uncertainty
requires inspecting this handle, never another launch.

```sh
/usr/local/bin/agent-task run frrie-p59-input-factory-20260908 '/usr/bin/time -f '\''process_wall_seconds=%e peak_rss_kib=%M'\'' -o /home/wu/.agent-tasks/frrie-p59-input-factory-20260908/process-time.txt /usr/bin/timeout --signal=TERM --kill-after=5s 115s /usr/bin/env -u BASH_ENV -u ENV PYTHONPATH=/home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908 PYTHONPYCACHEPREFIX=/home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908/temp/directions/finite_resource_relational_inductive_efficiency/exp/p59_input_factory/pycache OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /bin/bash --noprofile --norc -c '\''cd /home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908 && /usr/bin/python3.12 scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908/temp/directions/finite_resource_relational_inductive_efficiency/exp/p59_input_factory/admission.json && exec /home/wu/.venvs/hmasd-frrie-system312-r09-offline-p21-20260907/bin/python -X faulthandler tests/experiments/candidates/finite_resource_relational_inductive_efficiency/native_crash_repair/test_training_input_factory.py'\'''
```

The only extra placement setting relative to P47 is
`PYTHONPYCACHEPREFIX=/home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908/temp/directions/finite_resource_relational_inductive_efficiency/exp/p59_input_factory/pycache`, so import-generated cache files stay in
this invocation's owned temp scratch under the current AGENTS/tests instruction.
This can change import/cache timing; no exact historical allocation/timing
equivalence is claimed. It changes no source, fixture, dtype, RNG law or counts.
All such startup cost remains inside120s. Thread limits1 and PYTHONPATH=exact cwd
remain as frozen. No new ENGINEERING_SCOPE_SPEC §4 machinery.

## Collection, cleanup and return

Root follows the same accepted handle to terminal and resumes this CM. CM
retains necessary launch/admission/log/time/primary evidence in
`temp/directions/finite_resource_relational_inductive_efficiency/exp/p59_input_factory`
in the authoring checkout and the compact E0 record
`NATIVE_CRASH_P59_INPUT_FACTORY_RESULT_20260908.md`, with a JSON receipt if useful.
After terminal collection, CM verifies/removes only this invocation's
`pycache` scratch directory; evidence receipts and both P47 attempts remain.
Root owns detached-checkout reclamation after verified evidence retention and
completed delivery; the authoring checkout retains its active direction use.
No cleanup of unrelated paths or scientific evidence.

Return terminal/source/admission/counts/wall/RSS and deviations to DM for
all-outcome intake. Failed or restricted operations are reported precisely;
no rerouting around an actual restriction. No independent high-impact
production review is triggered or claimed. An in-scope static diagnostic
correction may be returned with its missing check, but P59 supplies no second run.
