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
