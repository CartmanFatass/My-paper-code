# Review Prompt: HMASD Codex Supervisor Synthetic Control Plane

Copy everything below the line to another model that can read
`origin/aggressive`. This prompt is for a **synthetic code/architecture
review**. It is not Phase 1, Stage 3, or Stage 4 acceptance. It does not
authorize live App Server work.

---

## Assignment

Review the HMASD Codex App Server supervisor on branch `aggressive` at
commit `c1e2d2e260e1b4765a2f35e4f64309f7bd0e1fe9`.

Repository: the HMASD git remote the operator pointed you at.
Branch: `aggressive`.
Review range:

```text
136d2904^..c1e2d2e2
```

That range is five commits:

```text
136d2904  feat: add Codex App Server observer foundation
c249fa40  docs: defer Phase 1 live review and start Stage 3 schema
1ba2d702  feat: add managed actor bridge, bindings, and provisioning
eec138ea  feat: add managed turns, gateway, activation, and operators
c1e2d2e2  feat: add synthetic managed mailbox and wake scheduler
```

This is operational control-plane infrastructure, not a research
direction and not Portfolio work.

## Read these first

```text
AGENTS.md
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/CAPABILITY_BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/PHASE_1_LIVE_AND_REVIEW_DEFERRED.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/PROTOCOL_EVIDENCE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/STAGE_3_CAPABILITY_BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/STAGE_4_CAPABILITY_BASELINE.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/QUOTA_BLOCKED_HANDOFF.md
docs/research/workflow-runs/2026-08-18_codex-managed-actors/SESSION_CONTINUE_HANDOFF.md
```

Then inspect only this surface:

```text
tools/codex_supervisor/
tests/codex_supervisor/
scripts/codex-app-server-observer-*.ps1
scripts/codex-managed-actor-*.ps1
scripts/codex-mailbox-*.ps1
docs/project/CODEX_APP_SERVER_OBSERVER_POLICY.md
docs/project/CODEX_MANAGED_ACTOR_AND_MAILBOX_POLICY.md
docs/research/workflow-runs/2026-08-18_codex-app-server-observer/
docs/research/workflow-runs/2026-08-18_codex-managed-actors/
```

Do not review or comment on unrelated dirty or historical trees
(`ha_ctse_process`, `hmasd`, `envs`, research candidates, experiment
runs). They are out of scope.

Do not require live App Server. Do not ask for Codex quota. Do not treat
missing `LIVE_CANARY_REPORT.md` / `PHASE_1_ACCEPTANCE.md` /
`STAGE_3_ACCEPTANCE.md` / `STAGE_4_ACCEPTANCE.md` as a code defect; those
files are intentionally absent until quota restore.

## Known host facts (do not contradict)

```text
Codex CLI 0.147.0
wire is JSONL-lite: no outbound "jsonrpc":"2.0"
handshake: initialize request, then initialized notification
-32001 retry only for thread/list and thread/read
mutating methods are never automatically retried
unexpected server-initiated requests terminate the owned process
clientUserMessageId exists on local TurnStartParams; not in official docs
thread/loaded/list exists in official docs and local schema
ThreadStatus types: notLoaded | idle | systemError | active
thread/memoryMode/set does not exist on this host
activation uses OPERATOR_CONFIRMED_GLOBAL_DISABLED
identity is only threadId → binding_id → actor_context_id
user authorized synthetic Stage 3/4 before Phase 1 live acceptance
live canaries are deferred, not failed
```

## Questions the review must answer

Answer each with evidence (file + function / table / test name). Separate
**observed fact** from **inference**.

1. Can a model impersonate another actor by putting `actor_context_id`,
   `binding_id`, `thread_id`, `source_kind`, or `user_authority` in a
   command envelope or payload?
2. Can a thread name, preview, `agentRole`, or prose establish identity?
3. Can an adopted legacy thread create semantic authority?
4. Can an unverified Memory policy become ACTIVE?
5. Can Stage 3 start a turn without an explicit operator intent?
6. Can Stage 4 start more than one `turn/start` for one wake batch?
7. Can an active turn be steered automatically (`turn/steer`)?
8. Can an uncertain mutating submission be resent?
9. Can mailbox prose, lexical names such as `FAILED.md`, or raw child
   text become a routing key, ACL input, or semantic state transition?
10. Can EM/CM/Leaf receive automatic wake delivery in this stage?
11. Can a packet send bypass the Root↔Portfolio ACL or self-declare the
    source actor?
12. Can a revoked or non-ACTIVE binding receive a wake?
13. Can a PREPARED wake batch after restart be resent, or are messages
    correctly returned to ELIGIBLE?
14. Are DELIVERED messages preserved across restart?
15. Does `-32001` retry leak onto `thread/start`, `thread/resume`,
    `turn/start`, or `thread/loaded/list`?
16. Are forbidden event kinds (`BLOCKED`, `FAILED`, `SUCCESS`, `RETIRED`,
    `PAUSED`, `PARKED`, `RELEASED`) used as supervisor or mailbox states?
17. Does the supervisor write canonical repository artifacts, ADRs,
    science cards, or Portfolio decisions?
18. Is the runtime database kept outside the repo
    (`%LOCALAPPDATA%\HMASD\codex-supervisor`) with tests using `tmp_path`
    / repo `--basetemp` only?
19. Are protocol fields limited to the local 0.147.0 schema plus the
    recorded docs/schema distinctions in `PROTOCOL_EVIDENCE.md`?
20. What is the strongest remaining synthetic defect, and what is only
    untestable until a live canary?

## Required output shape

```text
review_kind=synthetic_control_plane
reviewed_commit=c1e2d2e260e1b4765a2f35e4f64309f7bd0e1fe9
reviewed_range=136d2904^..c1e2d2e2
live_acceptance=absent
```

Then:

- **Conclusion** — one paragraph: is the synthetic design coherent, and
  what must stay blocked until live quota work.
- **Findings** — each finding: severity (`Critical` / `High` /
  `Medium` / `Low` / `Note`), exact object, evidence, why it matters,
  smallest fix. Do not use `BLOCKED` / `FAILED` / `SUCCESS` as a routing
  status for this review.
- **Answers** — numbered 1–20 with evidence.
- **Not reviewed** — live transport, quota, and any file outside the
  listed surface.
- **Does not decide** — Phase 1 / Stage 3 / Stage 4 acceptance, Portfolio
  investment, or whether to run a live canary.

If you cannot see a file, say `UNOBSERVED` for that point. Do not invent
protocol fields, acceptance files, or live results.
