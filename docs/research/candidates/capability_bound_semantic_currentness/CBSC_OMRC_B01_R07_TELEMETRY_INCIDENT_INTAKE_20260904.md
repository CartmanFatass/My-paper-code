# CBSC-OMRC-B01 r07 telemetry incident intake — 2026-09-04

- Object/rung: `CBSC-OMRC-B01 / CBSC-OMRC-B1-THREE-SEED-SCOUT`, **B/EXPLORE**
- Attempt/task: `b1_scout_r07` / `cbsc-b1-r07-b230e476ec-01`
- Exact launch source: `b230e476ec72ca6ac93f9fe3f78bfe5d1d2852c2`
- Node/checkout: `wsl_4070`, `/home/wu/hmasd-worktrees/cbsc-b1-r07-b230e476ec-01`
- Terminal fact: exit **6**, `2026-09-04T21:41:56Z`, 90 seconds after start
- Classification: **technical incomplete assignment after resource-supervision abort; quarantined**
- Original triggering syscall and actual historical child exit/kill: **unresolved**
- Scientific result/polarity: **none**. A and B objects have no consumption state.

This intake supersedes the running status, not the timestamped observations, in
`CBSC_OMRC_B01_R07_RUNNING_RECEIPT_20260904.md`. It authorizes one bounded repair of the reproduced
resource-only refusal path. It does not authorize r08, resume r07, or alter the scientific card.

## What I checked

Root delivered the shared tracker's terminal notification because that runtime could not send its
native sibling callback. I read its `EXPERIMENT_TRACKING.md` and returned a terminal acknowledgment;
that transport problem has no scientific meaning. The same CM collected the preserved remote
incident and performed three short offline probes over the exact launch source. I inspected its
`DIAGNOSIS.md`, `reproduction.json`, `counts-check.json`, `publication-predicate.json` and original
`supervisor-incident.json`, and compared them with the original assignment and current telemetry
rule. These probes created no scientific learner, optimizer, checkpoint or RNG stream and no new
B invocation.

The immutable remote incident is:

`temp/directions/capability_bound_semantic_currentness/exp/incidents/b1-f1fcc35b4d79452d8cf1350f2fa54012-a56baec561a64e829cb699c46bb493ad`

CM captured the complete incident as `r07-incident.tar`, SHA-256
`214861a11247e43c6e58eab2d2bcef224bc5d4dcf8e16aeb036f26acdd5af105`, matching remote and local bytes.
A preceding directory copy exceeded Windows path lengths; that partial extraction is not the
complete evidence package. The tar, original remote directory, task log and exit code are preserved.

Local diagnostic evidence and scripts are under:

`C:/Projects/HMASD-worktrees/cm-cbsc-r07-launch-20260904/temp/directions/capability_bound_semantic_currentness/control/r07-diagnostic/`

The fresh outer admission had already passed with 13,225,099,264 physical and effective available
bytes. The failing third-slice snapshot records 707 samples, 37.067529054998886 seconds observed
wall, 39.660000000000004 seconds observed CPU, 620,785,664 bytes observed peak RSS, and no cap
failure. It records `measurement_complete=false`, `reason=TELEMETRY_FAILURE` and a null scientific
branch. The supervisor discarded the underlying exception, syscall/path, traceback and actual
child returncode. Its generic error alone cannot identify the original cause.

## Counts against the assignment

All three first-slot worker result files exist. The exact worker-wrapper/stage-work reconciliation,
formal training merge (`test_only=False`), and existing checkpoint byte/digest/envelope/order
validation pass. The observed slot is `STRUCT-CURRENTNESS-GRU`, seed `21101`.

| Quantity | Observed first slot | Required full B1 |
| --- | ---: | ---: |
| Training episodes / transitions / decisions | 384 / 58,368 / 9,216 | 4,608 / 700,416 / 110,592 |
| Rollout updates / Adam rows | 48 / 768 | 576 / 9,216 |
| Evaluation episodes / transitions | 256 / 38,912 | 3,072 / 466,944 |
| Checkpoint updates | `0,12,24,48` | same four for each of 12 arm-seeds |
| Worker error files | 0 | 0 |
| Policy-replay files | 0 | complete replay for all 12 arm-seeds |
| Complete arm-seeds in ledger | 0 | 12 |
| Full publication | absent | complete summary and manifest |

The last slice has 29,184 train transitions and 9,728 evaluation transitions, exactly its declared
38,912 work count. Across the slot, 97,280 train-plus-evaluation transitions are recorded. The
remaining eleven arm-seeds, all policy replay and full publication are absent. First-slot learner
record completeness at these checks is not complete B1 evidence. No return, loss, gradient or
action-value contrast was used for this repair decision; the prediction is not scored.

## Reproduction and its limit

For each script, CM used the recorded source and configured virtual environment:

```powershell
Get-Content -Raw <local-script> | ssh hmasd-wsl-node '/usr/bin/env -C /home/wu/hmasd-worktrees/cbsc-b1-r07-b230e476ec-01 /home/wu/.venvs/hmasd/bin/python -'
```

`check_counts.py`, `reproduce_predicate.py` and `check_publication_predicate.py` each returned remote
exit 0; the latter two catch and report expected failures. Their outputs are respectively
`counts-check.json`, `reproduction.json` and `publication-predicate.json`. The existing
`control/r07-predicate-reproduction` output must not be overwritten by another probe.

The exact sampler on the now-terminated recorded PID `75194` raises `psutil.NoSuchProcess` from
`telemetry.py:467`; the current traceback attempts `/proc/75194/stat` and gets ENOENT. This is a
present-time observation, not recovery of the historical syscall. In the controlled replay, that
exception, the archived 707-sample/no-cap snapshot and the original readable last-slice output are
passed to unmodified `supervise_child`, with **explicitly simulated `poll()=None`**. The production
function calls a simulated kill and raises the same generic `TelemetryError` at `b1.py:826`.
No real child is killed. This reproduces a reachable resource-only abort predicate; it does not
prove that a process-exit race caused the historical incident or determine its actual returncode.

A second controlled probe copies a genuine resource measurement and changes only
`measurement_complete` to false. The exact formal publication predicate then raises
`B1MetricsTrainingAssemblyError: direct telemetry measurement is invalid`, caused by
`TelemetryError: telemetry measurement is incomplete`, despite intact real learner counts.
This demonstrates a separate downstream resource-only refusal. Fixing only the supervisor could
move the failure to publication rather than implement the owner's rule.

## Rule applied and bounded reading

The controlling owner rule in `AGENTS.md` section 8 is:

> a run whose resource telemetry (peak RSS, scratch, wall) is missing stays valid and is marked
> `resources_unmeasured`; annulment applies only when the claim itself is a resource claim.

The same section preserves quarantine for incomplete implementation and learner-side
instrumentation failure. The original B1 requires all twelve complete arm-seeds and their replay
and publication. The quarantine here follows **the missing assignment**, not the missing resource
measurement. It cannot be relabelled a complete result with a resource flag. Existing first-slot
records remain engineering evidence and are not resumed or salvaged into a result.

Direct evidence establishes an incomplete assignment, a resource-supervision refusal and two
reachable policy-conflicting predicates. It does not establish the unique historical trigger or a
currentness effect. The strongest support for a repair is that actual first-slot work and
checkpoints validate while resource-only predicates reject them. The strongest limit is the
discarded original exception and the absence of a complete B1. RAW's information containment
remains the strongest scientific alternative, untested by a complete comparison here.

The B/EXPLORE ceiling, headroom record `HC-M / CANDIDATE_ASSETS_MISMATCHED`, existing MEI boundary,
predictions and seven interpretation labels remain unchanged. No science branch, Portfolio
priority, lifecycle, fusion or direction-tier decision follows. `DIRECTION.md` remains unchanged.

## Decisions this intake produces

Object tier, technical:

- **(a)** add a narrow process-exit recheck/wait after a sampler error; this might reduce one race,
  but assumes a cause that is not established and leaves the demonstrated publication refusal;
- **(b)** quarantine the incomplete r07 assignment and repair resource-only failure handling through
  the existing training, replay and publication path, preserving all actual learner and wall-stop
  requirements; or
- **(c)** resume/salvage r07 or interpret the first slot as a complete B1 result.

Recommendation: **(b)**. It repairs directly reproduced behavior at the current owner-declared
boundary and avoids treating a guessed syscall as the scientific cause. The alternatives are not
close: (a) leaves the policy conflict and (c) changes the assignment after partial execution.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (b).** Provenance:
`OWNER_DELEGATED`, executing the current owner's resource-telemetry rule and resumed automation.
This is a reversible code repair and preservation decision. There is no automatic scientific
relaunch, and no new evidence class, object family or Pro request.

## Bounded CM repair contract

Repair only the demonstrated resource-only refusal behavior. When begin/poll/finish resource
sampling fails, training and policy replay continue to observe the actual child and an independent
monotonic wall deadline. A resource error alone never kills a worker or refuses an otherwise valid
result. Propagate the existing `resources_unmeasured` meaning through publication and consumer
readback; retain real available samples and represent missing measurements explicitly, without
fabricated zeroes or a false claim of full resource measurement.

Preserve actual nonzero child exit handling, missing/malformed learner-result refusal, real raw-work
and stage-count reconciliation, admission, checkpoint bytes/envelopes/order, complete policy replay,
all fifteen scientific tables and scientific nulls. Protect the original host, observations,
adapters, action masks, FP32 CPU learner, PRF/action draws, initialization, within-seed pairing,
seeds, 384 episodes/48 updates/768 Adam steps per slot, evaluation panels, checkpoints and zero
selection exposure. The 7,200-second wall stop and existing numerical/scientific semantics remain.

Runtime ownership is limited to the following existing files under
`experiments/candidates/capability_bound_semantic_currentness/omrc_b01/`, using only those needed:
`b1.py`, `telemetry.py`, `b1_metrics_training_assembly.py`, `b1_metrics_rehydrate.py`,
`b1_metrics_production.py`. Focused tests are the affected existing orchestration, section-11,
assembly, rehydrate, production and formal-path files under
`tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/`.
No runner, core, learner, host, workflow, `.codex/`, `.agents/` or science-authority edits are included.

Engineering-scope section 4: **none added**. Use existing assessment/publication structures and
remove refusing predicates. Do not add a telemetry service, schema validator, incident tree,
retry/lease, supervisor, compatibility layer or registry. Report actual added/deleted lines and
orchestration accounting; name any section-5 breach rather than hiding it or expanding machinery.
The 2,000 new-line and 600 runner-line caps remain; runner growth is zero. Keep the affected focused
profile within the five-minute test budget excluding its existing end-to-end smoke.

CM uses isolated implementation and independent review, then one focused exact-source validation
covering successful training/replay with missing sampling at begin/poll/finish, independent wall
expiry, nonzero exit, malformed/missing learner output and work-count corruption. Replace the
existing test that asserts `poll_failure_kills_child`; that behavior is the reproduced conflict.
Exercise publication and consumer readback offline at the real formal constants using the existing
complete quarantined r05/defect-8 evidence, including absent training/replay resource measurements.
r07 is not a complete fixture. Existing evidence remains engineering-only and is not republished
as a valid scientific result. Do not repeat unrelated suites.

Commit and push exact source before remote validation and use the configured remote-first route.
If a validation invokes a learner or becomes result-bearing/compute-intensive, use its own fresh
node-local admission immediately before the exact command. No B1 learner or r08 is part of this
repair contract. Stop at independent review plus the bounded technical acceptance record; a fresh
attempt requires a later DM intake, new pushed SHA/task/root and fresh admission.

Technical success can establish compliance of the repaired resource handling, not mechanism value.
The next discriminator within this assignment is the unchanged formal publication path accepting
missing resource measurements while still rejecting incomplete or corrupt learner evidence.

## CM-discovered dependency — bounded contract extension

Before editing, the implementer traced `_build_mechanical_facts` into the existing
`b1_mechanical.py` resource loop (launch-source lines 623–650), and its resource-cap contribution
to completeness (lines 931–947). Its unconditional numeric reads of wall/RSS/scratch/durable
quantities reject explicit null resource measurements. Omitting the row would lose its strict
admission check; inventing zeroes would misreport unknown measurements. Merely accepting nulls
while folding a false resource-cap flag into `all(components.values())` would still reject the
otherwise complete learner assignment.

Options are **(a)** extend ownership to this existing resource loop only, preserving its admission
check while carrying the existing unmeasured-resource meaning; **(b)** drop the row or fabricate
zeroes; or **(c)** leave a known downstream resource-only rejection after repairing earlier stages.
Recommendation: **(a)**. It is a directly traced dependency of the selected end-to-end repair, with
no new scientific or infrastructure feature.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Object tier, technical,
`OWNER_DELEGATED`. The one additional owned runtime file is
`experiments/candidates/capability_bound_semantic_currentness/omrc_b01/b1_mechanical.py`, limited
to resource handling and that resource-only completeness contribution. Unknown measurements/cap
facts remain unknown and explicitly unmeasured; resource-only unknowns or recorded budget
exceedances do not invalidate learner completeness. The independent wall stop, admission and all
non-resource mechanical/scientific facts remain strict.
All other scope, testing, numerical, evidence and no-launch limits above continue unchanged.

CM also located the complete r05 snapshot (`snap_r05`: 385 files, 311,364,169 bytes, 36 worker and
12 replay results). The earlier accepted profile used `TEST_ONLY` publication; its acceptance is
evidence for that test path, not evidence that missing-resource records pass production formal
mode. The current contract therefore still requires an offline check using the real formal
constants and this complete historical engineering evidence. No scientific polarity transfers.

Frozen offline input binding before remote staging: original
`C:/Projects/HMASD/temp/directions/capability_bound_semantic_currentness/exp/snap_r05`, packaged as
74,799,401 bytes with archive SHA-256
`70c72b8c075093d7ddc3682ae0e2e45a36a9b04e0dadcbb81175b7194ee00d4f`. The configured staging target
is `/home/wu/hmasd-inputs/cbsc-r07-resource-repair-20260904/r05-snapshot.tar.gz`. CM's original
binding record is `temp/directions/capability_bound_semantic_currentness/control/r07-repair/r05-input-binding.json`
in its local worktree. This is evidence staging, not uncommitted source transport. Read the
matched copy for the offline engineering check; preserve the original and its non-scientific status.

## Prospective engineering-budget return

Before a source freeze, CM reported a mutable diff of five existing runtime files, 179 additions
and 251 deletions (net minus 72), and four existing tests, 123 additions and 21 deletions. The
runtime changes concern supervision, resource handling and publication, so the conservative literal
accounting is **430 orchestration lines of 430 changed runtime lines, 100%**, above section 5's
30% ratio. Zero runner growth and zero added section-4 machinery do not make that ratio conformant.
The final return must replace these provisional counts with the exact committed counts.

Options: **(a)** finish the already-authorized minimal reversible repair, focused validation and
independent review, returning the exact diff and its orchestration lines as the scope specification
requires; or **(b)** return the currently unvalidated diff and leave its technical properties unknown.
Recommendation: **(a)**. A concrete tested return is necessary to assess this requested bug repair.
Padding the patch with unrelated science code is not an option.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** Object tier, technical,
`OWNER_DELEGATED`. This authorizes completion of the existing repair work, not a repository budget
change, a claim of scope conformance, final technical acceptance, or a fresh B attempt. The
independent review must name the budget breach and return the relevant lines beside its correctness
findings. DM will take that concrete return in before any technical acceptance or next-run decision;
Root has been informed. No unrequested machinery is accepted as the price of a result.

## Owner surface and integration

Owner reviews were empty in both DM and Root checkouts; no CBSC owner override was present. The
owner's prediction remains `not taken (unattended)` and is not scored on incomplete evidence.
This technical incident is not a valid-result brief. The decision item and exact daily-ledger row
are supplied to Root for shared integration.

Owner item: `docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-013.json`.
Shared-ledger insertion anchor: `cbsc-r07-telemetry-incident`.

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T15:07:23-07:00 | capability_bound_semantic_currentness | object | technical | (a) exit recheck only; (b) quarantine incomplete r07 and repair resource-only downgrade through existing publication; (c) resume or interpret partial r07 | (b) bounded resource-only repair; strict learner and independent wall checks; no r08 | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (b) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-013.json` | none | |
| 2026-09-04T15:12:53-07:00 | capability_bound_semantic_currentness | object | technical | (a) include existing mechanical resource handling/completeness dependency; (b) drop rows or fabricate zeroes; (c) retain known downstream refusal | (a) bounded existing resource handling only; strict admission and non-resource facts retained | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-014.json` | none | |
| 2026-09-04T15:23:40-07:00 | capability_bound_semantic_currentness | object | technical | (a) finish minimal repair validation/review and return exact orchestration breach; (b) return current unvalidated diff | (a) concrete reviewed return with budget breach explicit; no final acceptance or r08 | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-015.json` | none | |

The second row's shared-ledger anchor is `cbsc-r07-resource-dependency` and its owner item is
`docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-014.json`.
The third row's shared-ledger anchor is `cbsc-r07-repair-budget-return` and its owner item is
`docs/research/portfolio/owner/inbox/2026-09-04/20260904-cbsc-015.json`.
