# VNFC B02 execution and technical acceptance — 2026-09-11

## Accepted inputs and implementation

The [card](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_SCIENCE_CARD_20260911.md) and
[direction intake section 9](VNFC_NATIVE_SERVICE_CREDIT_REENTRY_INTAKE_20260910.md#9-reconciled-full-response-and-direction-decision--2026-09-11)
were committed/pushed at `3d177d27c`. Source baseline is
`10bb08476ff58afd25b90b21cd2d1a739b25ca4b`; the authoring checkout was clean before this edit.
New code is the 88-line B02 learning module and 35-line runner; N7 B01 collector/update and
publication helpers gain 34 lines and lose27. Total new non-test source157 lines, deleted27;
the 96-line synthetic test is separate. No Engineering Scope section4 machinery is added.
Unchanged native sources, model/input/action functions, original terminal GAE/PPO/AdamW,
RNG derivation and checkpoint/readback path are reused. No core or old result is modified.

Both arms retain seven native counter snapshots alongside public trajectory records.
The new module creates two independent MAPR models from the same externally materialized
fresh tensors, computes own-trajectory INTERVAL targets or the old TERMINAL recursion,
and reuses the existing real PPO update. Counter checks are directly necessary to the
selected reward definition; they are not a provenance/currentness guard. Full result
publication uses actual arm names, final primary, MEI.02 and all existing native contrasts.
Default B01 behavior, including the engineering profile's2700s projection cap, is preserved.

## Focused verification and independent review

One targeted synthetic file covers counter endpoints and failed-zone cutoff; interval-vs-
terminal GAE, detach and normalization ordering; final-vs-midpoint selection, negative zone
tradeoff preservation, JSON readback and both-arm full cost law. No model initialization,
RNG master, environment interaction or native build occurred in these tests.

Initial pytest invocation: two tests passed; the publication test setup failed because the
new scratch parent did not exist (`WinError 3`, before that test body). Internal full command
wall2.9724392s, pytest2.04s. After creating that parent, only the previously unexecuted test
ran: one passed, command2.705745s, pytest1.84s. There was no repeated successful test or
scientific retry. These are included once in support work; pytest and enclosing clocks are
nested and not added together. `git diff --check` passed.

Independent read-only Astra/high reviewer `review_b02_credit` found no material defect,
unselected machinery or line-budget breach. It inspected the changed files and reachable
native/model/RNG/action/optimizer/publication dependencies. It confirmed counter source and
60/120s windows, own-trajectory and behavior-information separation, unchanged TERMINAL
recursion and PPO, cloned initialization/independent optimizers, exposure and final readout,
single-thread/native-session topology and per-arm complete cost law. No test, model or native
execution was performed by the reviewer. Its support cost is3.251s summed displayed command
wall, approximately8.9s enclosing tool wall: nested alternative scopes, not additive.

Review limit accepted: the runner's internal complete wall stops before final stdout and
interpreter exit. The exact scientific command therefore uses existing `/usr/bin/time`
outside Python and OS `timeout`; outer elapsed and supervisor exit will establish the
process-exit-inclusive cost. This does not require another scientific invocation.
Source is technically accepted for the selected run, conditional on the actual primary and
nonzero learner/exposure observations required at terminal collection; no result is accepted yet.

## Support accounting and cleanup ownership

All support draws from300s and the combined900s allocation. Root integration receipt:
5.3663749s internally timed add/commit/push, plus approximately1.0s prior merge conflict,
2.6s audit inspection and0.1s patch. DM card commit/push5.3832615s displayed command wall;
the two tests total5.6781842s internally timed; reviewer3.251s displayed commands (~8.9s
enclosing tool wall). Other preparation/readback/patch commands, source publication,
staging/admission, Monitor commands and collection/cleanup will be included from their
receipts at collection. Unrecorded time is unknown, never zero. Deliberation and idle
queue/network waits are administrative elapsed; complete-cost conformance requires the
actual support record, not an inference from old native timing.

Scratch ownership: this DM created
`C:/Projects/HMASD-worktrees/codex-vnfc/temp/directions/variable_n_fleet_churn/test/b02_credit_20260911_01/`.
An initial combined test/recursive-cleanup command was rejected before execution with
`blocked by policy`; it ran no tests. Tests then ran through permitted non-destructive
commands. A guarded empty-directory cleanup found the test subdirectory and made no deletion.
A subsequent exact literal-file/empty-directory PowerShell cleanup was also rejected
before execution with `blocked by policy`. The existing
`test_primary_round_tradeoffs_p0` subdirectory is preserved; no alternative-shell deletion
or policy bypass was attempted. Root was informed. Cleanup remains DM-owned pending a
permitted operation; this has no scientific polarity and does not alter the invocation cap.

The shared direction authoring checkout remains active for this implementation/execution
and subsequent intake. The old unpublished request draft remains under the preservation
assignment in re-entry intake section7. Terminal collection will preserve unique evidence,
then inventory exact execution/test artifacts for authorized cleanup. Root confirms
integration/retention and eventual worktree reclamation. No remote run is accepted yet.
## Exact execution command

Reviewed scientific source was committed and pushed at
`76d4afca664f988fbaabca2923a0c891f8a784ff`. This exact SHA, not a later documentary HEAD,
is the execution input. Node `wsl_4070`; prospective detached checkout
`/home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01`; handle
`vnfc-b02-credit-20260911-01`. Source staging alone starts no scientific process.

After committed source staging, the one supervisor command is:

```bash
/usr/local/bin/agent-task run vnfc-b02-credit-20260911-01 "cd /home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01_memory.json && /usr/bin/time -f 'elapsed_seconds=%e\npeak_rss_kib=%M\nexit_status=%x' -o temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01_outer_time.txt timeout --signal=TERM --kill-after=1s 600s /home/wu/.venvs/hmasd/bin/python scripts/run_vnfc_native_service_credit_b02.py --seed 2026091101 --eval-seed 2026091102 --out temp/directions/variable_n_fleet_churn/exp/b02_credit_20260911_01 --launch-sha 76d4afca664f988fbaabca2923a0c891f8a784ff"
```

The timer includes the timeout wrapper, Python imports/build through final process exit.
The600s timeout bounds the complete scientific invocation; any kill-grace overshoot is
reported as a cost breach, not accepted as within600s. Native outputs are under the named
run root. The memory receipt and outer time file are sibling files outside that root.
Supervisor log/status are `/home/wu/.agent-tasks/vnfc-b02-credit-20260911-01/`.

The live Monitor endpoint was reread from
`C:/Projects/HMASD/.codex/hmasd-monitor.toml`: `01a087e5-2044-7301-abb6-7a1709a98197`,
Root `01a07249-b095-7821-8ce2-e9c32ba85267`. On acceptance the DM sends the exact handle,
SHA, node/cwd/run/receipt paths and original owners directly, with observation command
wall charged to this object's support budget. Dispatch and actual adoption are separate.
Owner reviews again returned `[]`. No launch acceptance or model result is asserted here.

## Exact source staging receipt

The first remote HTTPS fetch timed out (exit124), outer wall37.02s; no scientific
process existed. The configured network-login shell was not used for that fetch, so
this is a command-level network timeout, not evidence that remote source is unavailable.
The permitted exact-byte alternative used an incremental Git bundle against the
already-present `2482db44052705b130b3970456415d2309c99e2b`. A first bundle command naming
only the raw commit produced `Refusing to create empty bundle`; it transferred nothing.
Using HEAD at the same bound SHA produced89,959 bytes; `git bundle list-heads` returned
`76d4afca664f988fbaabca2923a0c891f8a784ff HEAD`. Creation plus SCP took0.7596152s internally.
Remote import took0.12s; detached worktree creation took0.21s. The new exact checkout
reported the bound SHA and an empty short status. No uncommitted source was staged.
The37.02s fetch wall is conservatively included in support accounting, including its
network wait; no administrative exclusion is used to hide this failed operation.

Local bundle:
`temp/directions/variable_n_fleet_churn/source_staging/b02_76d4afca6.bundle`.
Remote bundle: `/home/wu/hmasd-inputs/vnfc_b02_76d4afca6.bundle`.
Both are this DM's source-staging artifacts for collection-time cleanup after evidence
preservation; the detached execution checkout remains until terminal collection/acceptance.
Source commit/push command added5.3752014s displayed support wall.

## Launch acceptance and Monitor adoption

The exact command above was committed/pushed at `8dc043f2f`. Immediately before dispatch,
the named supervisor handle returned `not_found`; the one `agent-task run` then returned
acceptance into detached tmux. Its command support wall was0.3628601s internally
(1.5257668s displayed enclosing command, including the pre-dispatch handle read).
The source, identity and scientific command were not changed or retried.

Destination admission at `2026-09-11T18:26:52.030302Z` reported
physical/effective available15,636,619,264 bytes against4,294,967,296 bytes and `passed=true`.
The receipt came from `/proc/meminfo` on this exact node. The one launch-acceptance read
then reported `running`, supervisor wrapper PID3347770, uptime35s, exit null and active tmux.
That combined status/receipt read cost0.5249107s displayed command wall. It is a technical
launch observation, not evidence of final learner exposure or a valid scientific result.

Direct `MONITOR_ADD` to the live singleton endpoint was accepted. Root subsequently
confirmed actual adoption of this same handle/SHA/node/cwd/output, still running, with the
same passed admission; adoption observation command wall1.0s. The Monitor's continuing
status/log command costs belong to this object's support accounting. The DM has stopped
routine polling and retains collection, technical acceptance, scientific intake and cleanup.
Root routes the terminal fact to this original DM; no second observer or new invocation exists.

Pending collection: preserve full native summary, curves, all episode rows and six
checkpoints, plus outer time, admission and supervisor terminal log/status. Read primary
and counter targets against the card; report every arm/zone/native metric and actual
nonzero counts/movement, then write the valid-result intake/Chinese brief if supported.
Inventory the exact detached checkout, source bundles and creator-owned scratch for
cleanup only after unique evidence preservation and Root retention/integration reconciliation.
The exact policy rejection in the scratch section remains unresolved; no deletion bypass.
No extra arm, retry, evaluation or successor is authorized by this handover.

Command/staging documentary commit/push added4.6467948s displayed support wall. Final
support accounting will distinguish internal clocks, displayed enclosing alternatives,
approximations and genuinely unmeasured components without double-counting.

## Terminal collection and closeout

Root routed Monitor's terminal fact on2026-09-11: the same handle failed exit139 at
2026-09-12T02:28:09+08:00 after78s. Collection confirms signal11/77.84s, two initial
checkpoints and15 logged arm-rounds, with no complete primary. The
[E0 collection](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_RESULT_EVIDENCE_20260911.md) and
[DM intake](VNFC_N7_NATIVE_SERVICE_CREDIT_B02_RESULT_INTAKE_20260911.md) preserve this
incomplete attempt without performance polarity. No retry, workaround invocation,
extra test, source change or successor occurred. The earlier pending-collection text
is historical launch state, superseded by these terminal records.

Raw11-file archive SHA256
`1bbcfbe499e8a15bb1d5f4a0d4fdaf0fa8a52feda65da4de4f2f3e2abc575de5`
matched remote/local. The additional local recovery archive preserves the unpublished
draft, source bundle and synthetic scratch bytes. Both archives and complete inventories
are under `evidence/b02_credit_20260911_01/`. Exact source remains published and unchanged.
Root source/launch integration through mainf6fb5606b added10.4s displayed support wall;
the shared1.3s RCLE+VNFC terminal observation is charged only to RCLE per Root. Other
timings and missing scopes are explicit in `support_costs.json`; full cost is unestablished.

At first collection publication, scoped remote checkout/staging cleanup awaits Root's
integration acceptance of the preserved evidence. The scratch `blocked by policy`
rejection remains unresolved; no bypass or repeated deletion attempt is authorized.
The shared authoring checkout is retained for this intake/cleanup, with eventual
reclamation owned by Root. Verified deletion or remaining-path facts will follow here.

### Root acceptance and actual cleanup — 2026-09-11

Root integrated the14-file preservation/intake commit
`94c8fdfa888df014fa9fd83a4014a1cb10b7d501` through published main
`cf93e737ee83f2d78d14c5569874590af8ccd347`, then explicitly returned the named cleanup
inventory. Before remote removal, all11 archived byte streams equalled their originals;
the five noncache ignored files were exactly covered, both input-copy digests matched,
and the detached checkout had clean tracked/untracked source at the bound launch SHA.

[Remote cleanup receipt](evidence/b02_credit_20260911_01/remote_cleanup.json) verifies
the exact checkout `/home/wu/hmasd-worktrees/vnfc-b02-credit-20260911-01` is absent on
disk and from `git worktree list --porcelain`. Input copies
`/home/wu/hmasd-inputs/vnfc_b02_76d4afca6.bundle` and
`/home/wu/hmasd-inputs/vnfc_b02_partial_20260911.tgz` are also absent. The small terminal
supervisor directory and its six files remain. No other checkout or source branch was removed.

The remote cleanup command executed its removals, then its final receipt here-document
terminator reached Python as `PY`, causing `NameError` after the absence assertions/JSON
print. No deletion was repeated. A separate read-only reconciliation verified the actual
absence facts above and produced the receipt. The failed command1.0538243s displayed
wall and read-only reconciliation0.4776158s internal wall are both retained as support.

Automatic approval review rejected the separate exact PowerShell local draft/source-copy
cleanup before execution with `blocked by policy`. This new rejection concerns only
the three preserved draft/source files and their empty draft directory; the earlier
blocked test scratch was not targeted again. No alternative deletion method or repeated
attempt followed. [Local cleanup record](evidence/b02_credit_20260911_01/local_cleanup.json)
confirms all four local files (including the earlier scratch) still exist and match the
committed recovery archive. Local cleanup is blocked, not complete. These exact local
paths remain DM-owned; Root owns the shared direction checkout's lifecycle.

`support_costs.json` now includes the collection publication and these closeout operations;
its selected documented component sum is108.999243 s, plus approximate3.7s Root preparation.
Unmeasured scopes remain explicit; final cleanup-record publication timing is returned
to Root separately. The final owner review read returned `[]` and the intake audit owner
cell remained blank. This closeout changes no scientific interpretation or allocation.
