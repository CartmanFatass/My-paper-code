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
