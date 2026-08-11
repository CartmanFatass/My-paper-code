# HMASD Desktop Workflow-Subagents to Codex CLI: Final Audit

**Date:** 2026-08-10
**WDM-frozen disposition:** `OPERATIONALLY_ACCEPTABLE_WITH_BOUNDED_LIMITATIONS`

## Disposition and scope

The completed migration provides an operationally acceptable Root -> two-level
L1/L2 control plane, subject to the limitations below. This is a workflow
audit: it does not accept code, runtime behavior, scientific conclusions,
scheduler behavior, a hash gate, or any undocumented runtime guarantee.

The highest-signal evidence is the second fresh normal smoke: the exact
non-ephemeral `codex exec -C C:\Projects\HMASD --sandbox read-only` completed
in 116.8 s with literal `FRESH_NORMAL_WDM_L2_SMOKE_OK` and
`FRESH_CATALOG_AUDITOR_EXECUTED`. It observed Root -> registered WDM
(`fork_turns=1`) -> registered Workflow Auditor (`fork_turns=none`), with WDM
configured as `gpt-5.6-sol/high`, canonical cwd/Git top, generated catalog,
hooks 0, expected config keys, and no Hook failure. The outer Root CLI process
reported `gpt-5.3-codex-spark/medium`; that is not the WDM L1 model. An earlier
normal non-ephemeral WDM smoke also succeeded. The first post-catalog-path
smoke failed before spawn because the generated catalog began with a UTF-8 BOM;
that P1 was repaired and the smoke was rerun successfully. Ephemeral
collaboration remains a separate bounded failure, not a successful mode.

## Verified final control plane

- `C:\Projects\HMASD` is the only work root. The old OneDrive repository and
  approximately 296 legacy linked worktrees were not repaired, migrated, or
  deleted; they are outside the managed lifecycle.
- CLI Root at depth 0 is the sole user-contact, agent-tree/lifecycle,
  cross-owner-relay, physical-canonical-write, and final-Git-integration actor.
  Root has no WDM workflow, CPM code/runtime, or Explorer scientific acceptance
  authority.
- Same-level read-only task-scoped L1 managers are WDM (Sol/high), CPM
  (Sol/high), and Explorer (Sol/max). Their dispatch caller action is
  `fork_turns=1`. A later
  CLI invocation starts a fresh Root and reloads canonical state; it does not
  resume a Desktop thread/session successor.
- Registered L2 specialists are leaves. Normal self-contained dispatch is
  `fork_turns=none`, with only the specialist exceptions explicitly present in
  current Role contracts. The temporary native-default exception is
  specialist-first, Luna/high with `fork_turns=1`, temporary/read-only by
  default, and grants no owner, runtime, Git, spawn, or acceptance authority.
- Any tracked writer uses an exact Root-provisioned managed worktree. The
  current checkout is reserved for read-only, ignored-only, or temporary-only
  work; mixed tracked+ignored work is a tracked writer. A worktree supplies
  isolation/provenance, not identity, ticket, or runtime admission. Root alone
  provisions, records, integrates, releases, or retains worktrees and owns
  Git.
- The CPM runtime pool remains three units independent of worktree count. Two
  code directions advanced in separate worktrees; VSP02 consumed 1/3 actual
  runtime, VSP06 consumed 0, and the final pool was 0/3.

Configuration and catalog checks are as follows:

- `[agents] max_threads=10` and `max_depth=2` are present; retired
  `max_concurrent_threads_per_session` is absent. These config values are
  policy intent only for depth: a prior real runtime allowed L3, no repeat
  depth/saturation test was run, and runtime `max_depth=2` enforcement is
  explicitly unclaimed. L2 Role policy still forbids spawning.
- `.codex/hooks.json` is valid with `hooks={}`. Hooks remain disabled and
  non-authoritative by user instruction; no hook was re-enabled and no Hook
  failure occurred in normal tests or smokes.
- The self-contained ignored/generated workaround catalog is
  `C:\Projects\HMASD\runtime\model-catalog-v2-workaround.json`: 245221 bytes,
  prefix `7B-0D-0A-20`, strict UTF-8 JSON, nine models, Luna/Spark v2, and all
  profile routes. It is not committed. Windows PowerShell 5.1 regeneration
  passed; `pwsh.exe` was unavailable. Native workaround deletion remains
  unproven. The byte/hash details are evidence locators, not admission,
  routing, identity, or acceptance rules.

## Three research rounds and owner-separated results

Exactly three migration-validation rounds exist under
`local_research/migration_validation/2026-08-10_cli_two_level_workflow/`:
`round_1.md`, `round_2.md`, `round_3.md`, plus `summary.md`; there is no
round 4. Evidence locators are round 1 SHA
`95f859478954a1baffdd8dd545c6a54b6b31017ead63338583e781f904de3a04`, round 2
SHA `cbe810b307a65cac1d3a342708adcc287f6d09bbed8b450db95ed9186202c7b2`, round
3 SHA `dacf1abc9b8107b43c1921ca2036f000fa96eb08562d9f2a5cf4bc10f831f829`,
and summary SHA `ab2777ed1d6e3839c115f6c152ae013e584c76791f4d42327f48e08914a81549`.

The canonical Explorer revision-4 evidence is
`local_research/RESEARCH_CONTINUITY.md` (7760 bytes, SHA
`f93e4ac8ee2e3b584cf0ff0edb807eec922756578b7da79ac513c8deb40d6172`) and the
direction map (48555 bytes, SHA
`937bd9dde2253ce2df28494a7dd49dda4ac553684e9a473701c13b62a69599b1`). These
locators identify evidence and do not establish workflow admission.

The following are owner results, not cross-owner reinterpretations:

- **Explorer / VSP02:** Explorer accepted the single CPM result as
  `B3_SIGN_ONLY_INSUFFICIENT`; the sign-only route is closed and VSP02 is
  retained/parked pending an exact single-axis discriminator, with no CPM now.
  CPM's technical run was exactly one full run—no retry, rescue, or sweep—of
  five units, 5120 train episodes, 1280 optimizer updates, 1280 evaluation
  episodes, 27001 transitions, and 10 checkpoints; both arms were 0/5 and
  activity/exposure were valid. This is not a universal scientific claim.
- **Explorer / VSP06:** The old B2 identity was closed at zero runtime because
  pre-fixation canonical rows had been observed and used to repair final-KEEP
  support. B2R1 is only a prospective, non-executable identity/salt/parent
  binding: no fresh handoff, final source commit, CPM admission, selector, or
  full run occurred. Missing exact `ortools==9.12.4544` is an independent
  technical gate. VSP06 runtime is 0 and its result is absent.
- CPM technical acceptance and Explorer scientific disposition remain distinct
  from WDM workflow acceptance; this report does not merge or override them.

## Recovered incidents

| Incident | Classification and recovery |
|---|---|
| Early WDM migration/test loops had stale contract assertions and Windows default pytest Temp ACL failures. | Verification defect/environment issue; repository-controlled temp restored focused checks. |
| `--ephemeral` collaboration spawn failed on CLI 0.147.0 with `collab spawn failed: no thread with id ...`; normal non-ephemeral dispatch succeeded. | Bounded CLI limitation; not a Hook failure and not evidence that ephemeral works. |
| Round 3 Artifact Writer first used an adjacent hyphen path. | Artifact-path error; the same Writer corrected to the byte-identical underscore path and removed the wrong empty directory. |
| Large map Writer transport repeatedly truncated data, omitted destinations, used wrong archive semantics, and emitted malformed literal backtick-n/pipe/locator text. | Transport failure; Root replaced monolithic payload transport with minimal deterministic transforms, after which Explorer performed full reads and accepted revisions 3 and 4. This directly supports lazy/minimal context plus semantic acceptance. |
| VSP02 source worktree contained implementation-test residue. | Freshness failure; CPM refused the source, Root provisioned a distinct fresh execution worktree, and one full run then executed exactly once. |
| VSP06 synthetic-only prospectivity was violated when pre-fixation tests observed canonical generator rows and Reviewer used them to repair final-KEEP support. | Scientific identity/provenance failure; no selector/full/runtime ran, Explorer closed the old identity and selected `REBIND`. |
| Root's first revision-3 post-install check used the wrong local `round_count=3` anchor even though exact copies/hashes were correct. | Local semantic-check error; corrected to verify 3/3, no round 4, and VSP06 awaiting at that revision. No rollback or science failure. |
| Final Auditor found external catalog path `C:\project\HMASD` (P1). | Workflow acceptance withheld; path was repaired to canonical root, Workflow Implementer `fork_turns=none` and Root-managed tracked writing were aligned, and Reviewer accepted. |
| First fresh post-repair smoke found the BOM P1 before any spawn (`EF BB BF`; Codex reported `expected value at line 1 column 1`). | Acceptance/reporting withheld again; catalog writing was changed to explicit `.NET UTF8Encoding(false)`, a byte-level contract was added, catalog regenerated, Reviewer accepted, and the second fresh smoke passed. |
| Initial report worktree was released empty. | Correct lifecycle response while P1 repairs blocked acceptance; reporting resumed only after repair integration and fresh evidence. |

Managed-worktree evidence records three new VSP02 receipts as `RELEASED` and
the VSP06 receipt as `RETAINED_FOR_RECOVERY`, ref
`refs/hmasd/root-managed-recovery/cpm_vsp06_b2_source_bound_exact_feasibility_f1`
-> `523612c0099c84524f66b88d4d08dc5daec3ec84`; those four checkouts and
registrations are absent. Catalog-role and UTF-8 repair receipts are
`RELEASED`; their pytest residues were moved, not deleted, to ignored
`temp/disposable/wdm_catalog_role_repair_f1_pytest` and
`temp/disposable/wdm_catalog_utf8_repair_f1_test_tmp`, 87 entries each. The
first empty report-worktree receipt is `RELEASED`; the current f2 report
worktree remains Root-lifecycle-owned until Root integrates and releases or
retains it.

## Verification, limitations, and fresh-root procedure

The authoritative integrated workflow Python result is **111 passed, 1 skipped**
(the earlier pre-repair record, **110 passed, 1 skipped**, is
historical). PowerShell delegation, agent-profile benchmark,
experiment-operator, CPM, research-workflow, WDM delegation/current focused
contracts, and the applicable focused checks passed. Harness counts were
`profiles=21 roles=22 skills=9`.

Current local integration is branch `aggressive`, HEAD
`334fbe94c67a13e2244fa52f455b8ffc5c31d3c8`, with tracked files clean at report
assignment; unrelated existing untracked files were preserved. High-value
local commits are `669a4a4d` (Root-first migration), `900e78cc` (disabled-hook
clean-clone repair), `a7dbb65b` (managed-worktree helper),
`b79f603b`..`26b8a800` (context/worktree/contract chain), `37aaa31e` (VSP02
source), `6230cb4c` (VSP02 result), `898af9e8` (VSP06 fail-closed source),
`527ee57d` (catalog path and Workflow Implementer repair), and `334fbe94`
(UTF-8 no-BOM repair). Both `origin` and `My-paper-code` name
`https://github.com/CartmanFatass/My-paper-code.git`, target `aggressive`; no
push occurred and the remote was not updated.

The accepted workflow still does not claim runtime `max_depth=2` enforcement,
ephemeral collaboration support in CLI 0.147.0, or `pwsh.exe` execution. The
generated catalog workaround remains required until native deletion conditions
are independently proven. No push/remote update, legacy-worktree repair or
deletion, global subagent cleanup, OR-Tools installation, VSP06 full run,
additional research round, or scientific/code reinterpretation is part of this
acceptance.

For a fresh Root: reload `AGENTS.md`, the relevant profile/Role, compact owner
continuity (Explorer must read `RESEARCH_CONTINUITY.md`), and action-triggered
Skills; if the ignored catalog is absent, regenerate it before starting Codex;
then start Codex from `C:\Projects\HMASD`. Hooks remain off. The invocation is
a fresh Root, not a resumed Desktop session.

## Evidence locators

The principal evidence is the integrated test/smoke record, the three round
files and summary above, Explorer revision-4 continuity and direction-map
locators, the managed-worktree lifecycle receipts, and the local commit chain.
Content hashes and byte counts in this report are reproducibility locators only;
they are never workflow admission, routing, identity, or acceptance rules.
