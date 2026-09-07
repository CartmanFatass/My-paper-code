# Pro delivery reconciliation after branch cleanup — 2026-09-07

OWNER_DIRECT: reconcile stale branch registrations and update related workflow files.
This receipt concerns transport and branch routing; it changes no scientific result or budget.

## Observed failure and current correction

The DISH post-B06 accepted prompt linked TASK at `0502fea77541337fdb7106068d6fbc7a31c0772f`.
Its complete archived reply reported branch HEAD `f3d6a158598e55f843eaff2894d907c288e27f39`
against the TASK's `6b45ea47bea500bea11f1215080653a8df19bdd6` baseline, response404 and no
matching Issue4 comment. It explicitly reported zero write requests. The branch was retained;
the direct failure was sending the old fixed-base TASK despite a refreshed prepared handoff.
This observation does not establish an intrinsic conversation-to-branch restriction.

P09's distinct delivery-only correction is already accepted once in conversation
`6a9bec54-df00-83e8-9840-46440458f316`, user message
`94e79976-b462-4c76-8994-31f6c41c5c60`. Its TASK is at
`25c93b776b8d8a8d706ef1259601775d15210594`, HANDOFF at
`8a5cf6205b2ea0c0df8541b4c461234d81ec615a`, delivery baseline
`dba5cfc8a58eba9a0c1b2cefb9e954f3c92a7e71`. Local ancestry check passed; fresh remote
read found the retained DISH branch at the HANDOFF commit. Scientific inputs remain at
`6b45ea47`; the new TASK allows descendant advances and names a distinct response path.
Registry observation was WAITING_GENERATION. Root observes and archives that request;
the old blocker does not justify another Send. The current terminal receipt, when available,
belongs in Root's existing transport records.

Root subsequently returned complete archival: response commit
`f7b58f1b88d7282f98ca6be531e9b4c27f85b690`, Issue4 comment `5574756410`, short reply SHA256
`64197894d124d07a947ef5823ccf51a062bfbe6230c501e1dd41eb39b1f36147`, full response SHA256
`a2e4e03f1631c3b24e7e70b9397d0c6a08e37c79716eda10b43232d38297fdd5`.
Portfolio read back the current registry archive hashes, ARCHIVED state and closed tab.
Scientific conformance/intake follows P09 through the original DM; archive completion alone
does not make that scientific decision locally.

## Branch and registration audit

Fresh local worktree and remote-ref reads found these current authoring locations:

| Direction | Branch | Existing authoring checkout under `C:/Projects/HMASD-worktrees/` |
| --- | --- | --- |
| CBSC | `codex/cbsc` | `dm-cbsc-next-20260906` |
| DISH | `codex/pro-dish-post-b06-20260907` | `dm-dish-b06-scientific-intake-20260907` |
| UCOPE | `codex/ucope` | `dm-ucope-native-return-prep-20260906` |
| VSPC1 | `codex/direction-vsp_c1` | `dm-vspc1-next-20260906` |

RCLE post-A02's declared target `codex/pro-rcle-post-a02-20260906` still exists at its
`5a335eaff0f2242c515f6867e22d04bdd8d832ef` baseline. VSP03's shared-service target
`codex/pro-vsp03-shared-service-convergence-20260906` still exists remotely at its
delivered response commit `a62defbbe843149c836c132d6a8f6bb5540506a2`; local branch was at
its earlier `585fe948` baseline. Reconcile that remote delivery before the next local push.
These retained names serve their existing requests; this receipt creates no branch or task.

The shared Transport registry also contained stale current fields: DISH's correction record
carried an old B04 delivery note/commit; its direction mirror differed from the current binding
state. VSPC1's amendment binding was DIRECTION_VERIFIED while its mirror was ARCHIVED;
VNFC's post-depmode record retained the preceding two-seed TASK Send link. Other old mirror
states also differed. These observations require request-specific evidence reconciliation,
not wholesale replacement of bindings or an inference that an old request is pending.
Portfolio assigned Root, the existing registry writer, a bounded backup/reconciliation with
original fields retained in matching history. Completion of that operational repair requires
Root's receipt; this workflow change alone does not claim the registry is repaired.
The DISH archive return passed the focused archive readback, but its current `delivery` field
still named B04. Portfolio returned that precise gap to Root for correction, retaining the
old B04 delivery in its proper history and the verified new delivery as current. Other stale
records remain subject to the assigned evidence reconciliation.

## Workflow changes and validation

ROOT_OPERATIONS now couples branch reclamation with affected-request and current-routing
reconciliation. GITHUB_RESEARCH_COLLABORATION and the Author/Transport/dispatch skills specify
full-commit handoff retrieval, current remote delivery checks, legacy fixed-base correction,
and preservation of request-specific history. The existing renderer already emits descendant-
HEAD delivery wording; no runtime source, validator or scheduler was added.

The archived DISH failure is the concrete regression case. Independent read-only application
of the changed guidance passed four scenarios: stale same-path handoff, ordinary descendant
advance, accepted legacy fixed-base refusal, and retirement with uncertain delivery/prior-round
registry fields. All three changed skills passed quick_validate; focused diff whitespace
checks passed. Historical packets and scientific evidence were not rewritten.

## Shared heartbeat adjustment

The owner subsequently selected a15-minute Root heartbeat after observing long idle gaps
with30 minutes. The existing `hmasd-experiment-monitor` automation was updated through the
app tool and read back ACTIVE with the same Root target and notification policy. Its full
prompt was preserved except for the cycle text. `.codex/hmasd-monitor.toml`, ROOT_OPERATIONS,
EXPERIMENT_MONITOR and Transport's skill/state reference now agree on15 minutes. No additional
automation or experiment invocation was created; unchanged observations remain silent.
