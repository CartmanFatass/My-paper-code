# Claude Capability Map — workflow, skills, subagents

```text
document_kind=claude_capability_registry
revision=2026-08-06 v1
authority_note=adds_no_authority_over_AGENTS.md; AGENTS.md remains the sole
  project authority and routing contract, hard read-only from this branch.
  This registry describes Claude-side capabilities only.
companion=.claude/ORCHESTRATOR_WORKFLOW.md (the procedure; this is the registry)
self_contained=true
```

## Why this document is a migration and not a pointer

The Codex-era workflow is a large control plane: seventeen role charters, seven
skills, thirteen registered agent profiles. Since the 2026-08-05 takeover those
sessions are dormant and their surfaces (`AGENTS.md`, `.agents/`, `.codex/`,
`docs/project/`) are **hard read-only from this branch** — a Claude session does
not resolve a Codex role and does not load a Codex charter as instructions.

A registry that said "behaves like `.agents/roles/VERIFIER.md`" would therefore
be unusable in two ways. It would be **incompatible**: those charters assume
Codex-native transports, ticket scripts, session records and authority fields
that do not exist here. And it would be **non-strict**: a pointer defers the
definition, so two readers get two behaviours and neither is wrong.

So every row below states the Claude-side realization **in full**. Reading
`.agents/` or `.codex/` is never required to act on this document, and where a
Codex object has no Claude counterpart the row says so and gives the reason
rather than leaving a hole. The Codex names appear only as provenance — what a
capability was called before — never as a definition.

## The frame: three holders, and what may never move between them

| Holder | Holds | Never holds |
|---|---|---|
| **Orchestrator** (this session) | the local Explorer remainder (drafting, reconciling, longitudinal state) + the entire Code Manager duty set: implementation, tests, review dispatch, technical acceptance, boundary checks, commits, pushes | scientific judgment; it does not self-certify science |
| **External Pro** | ALL scientific judgment — estimand, population, null, identification, registration admissibility, what a result may be claimed to establish, park/closure | code execution; it never runs anything here |
| **Subagents** | bounded task work, returning raw facts | acceptance, git, science, or any authority at all |

Subagents are **task tools, not roles**. They are single-shot and stateless,
their output is advisory, and one unit has exactly one acceptance owner: the
orchestrator.

## Registry A — subagents (`.claude/agents/`)

Six exist. Each is self-contained; the file is the contract.

| Agent | Model / effort | Bounded job | Returns | Was (Codex provenance) |
|---|---|---|---|---|
| `hmasd-implementer` | opus / high | one implementation unit against a **frozen** brief, inside a named writable scope | changed files, essence of each change, exact test commands with output tails, deviations from the brief | `hmasd-implementer` |
| `hmasd-reviewer` | opus / xhigh | independent review of one change set in a context that has **not** seen the implementation reasoning | findings ranked by severity with file:line and a concrete failure scenario, plus what was verified as satisfied | `hmasd-reviewer` |
| `hmasd-verifier` | sonnet / high | one long verification exercise — full suite, end-to-end CLI, post-change sweep. **Not** the Codex six-phase readiness receipt; see the non-migration note below | per-command `PASS` / `CODE_DEFECT` / `OPERATIONAL_FAILURE` / `PRE_EXISTING` / `UNDECIDED` with minimal verbatim evidence, then one terminal | `hmasd-verifier` (name only) |
| `hmasd-experiment-operator` | sonnet / high | one **already-registered** experiment run, design fixed | artifact path, bytes, sha256, terminal, elapsed, named summary fields, then `RUN_COMPLETED` / `RUN_REFUSED` / `RUN_FAILED`; or, when the run outlives its turn, a handback (PID + durable stderr path) and `RUN_HANDED_BACK` for the orchestrator to monitor | `hmasd-experiment-operator` |
| `hmasd-scout` | sonnet / medium | read-only object-existence / semantics reconnaissance | per-object `FOUND` (file:line, type, producer/consumer, lifecycle) or `ABSENT` (patterns tried, nearest misses) | `hmasd-code-scout` |
| `hmasd-mechanic` | haiku / low | one read-only mechanical check — inventory, byte compare, count, checksum, log tail | the requested raw facts and the exact commands run | **none — Claude-native addition** |

Three properties are shared by all six and are load-bearing:

- **No acceptance claim.** A child never says its work is good. It reports what
  it observed; the orchestrator decides. Four of the six end with a terminal
  line (`UNIT_COMPLETE`, `FINDINGS_REPORTED`, `VERIFICATION_PASSED`,
  `RUN_COMPLETED` and their negatives) — those report an observation, never an
  acceptance, and every contract says so in the same words.
- **No git.** No child commits, stages, pushes, merges or rebases.
- **No forbidden-path writes.** `AGENTS.md`, `.agents/`, `.codex/`,
  `docs/project/`, `scripts/hmasd_workspace_ticket.py` and
  `scripts/hmasd_workspace_boundary_guard.py` are never writable by a child at
  all — **an assignment naming one of them is itself the error**, and the child
  reports it rather than complying, because §7's boundary check requires the
  diff over those paths to be empty at every commit. `.claude/` is the one
  conditional case: writable only when the assignment names a specific path
  inside it.

## Registry B — skills (`.claude/skills/`)

| Skill | What it governs | Enforcement | Was (Codex provenance) |
|---|---|---|---|
| `hmasd-science-dispatch` | which questions reach External Pro and in what condition: route → measure-then-write → clean-context document review → run the gate → dispatch once → archive verbatim | **blocking script** `scripts/hmasd_dispatch_receipt.py`, exit non-zero on `DISPATCH_BLOCKED`; requires `15_DOCUMENT_REVIEW.md` terminating `DOCUMENT_MATCHES_SOURCE`, waivable only with a written `document_review_waiver_reason` that travels in the receipt | `hmasd-independent-research-pro-review` + `hmasd-agentify-transport` |

The Codex side kept transport and review-composition in separate skills. They
are merged here because the transport rule that actually matters — *a
`fetch failed` roughly five minutes after submission means the question was
SUBMITTED; never resend* — is a rule about the dispatch decision, not about a
separate operator, and splitting it across two documents is how it gets lost.

## Registry C — Codex roles and skills, and where each one went

Nothing below requires reading the Codex surfaces. Rows marked **not migrated**
are deliberate; each states why, so nobody "restores" a capability that was
removed on purpose.

### Migrated into the orchestrator (inline, never delegated)

| Codex object | Claude-side realization |
|---|---|
| `CODE_PROJECT_MANAGER` | the orchestrator itself. Exact assignments, file ownership, child dispatch, technical acceptance, boundary check, isolated commits, push — `ORCHESTRATOR_WORKFLOW.md` §6 (workflow), §7 (boundaries), §8 (house rules) |
| `INDEPENDENT_RESEARCH_EXPLORER` | **split.** The drafting/reconciling/longitudinal remainder is the orchestrator's (`ORCHESTRATOR_WORKFLOW.md` §2 steps 1, 3, 4, 9). Every judgment call in it goes to External Pro |
| `AGENTIFY_TRANSPORT_OPERATOR` | **not an agent.** One script invocation the orchestrator makes inline (`hmasd-science-dispatch` Step 5). A separate agent would add a hop to a single command and, worse, would not hold the submission state — which is precisely what the never-resend rule depends on |
| `hmasd-agile-research-development` (skill) | `ORCHESTRATOR_WORKFLOW.md` §2 (the nine-step science cycle) and §8 (small-change shape, exact arithmetic, byte-stable serialization, proof-sized tests). Its **six-phase execution-readiness exercise is NOT migrated** — see below |
| `hmasd-independent-research-exploration` (skill) | `ORCHESTRATOR_WORKFLOW.md` §2 steps 1–4. Its bundled research-methodology references are historical material, not active instructions |
| `hmasd-explorer-project-validation` (skill) | `ORCHESTRATOR_WORKFLOW.md` §2 step 8 (post-commit alignment audit) and §7 (boundary check at every commit) |

### Held by External Pro — no Claude agent, by design

`RESEARCH_CRITIC`, `RESEARCH_INNOVATOR`, `RESEARCH_PRINCIPLES_ANALYST`,
`RESEARCH_SCOUT`, and the `hmasd-research-*` profiles: **not migrated.**

This is the single most important row in the document. A local research critic
would produce the *appearance* of scientific validation without the one property
that makes validation worth anything — independence from the session that wrote
the proposal. Every scientific question goes to a fresh External Pro session:
adversarial validation before any freeze, alignment audit after every science
commit. Pro is never simulated and its responses are archived verbatim with a
byte comparison. `EXTERNAL_PRO` maps to External Pro unchanged.

If a future session feels the need for a local critic, the correct action is to
dispatch a Pro round, not to create the agent.

### Dormant — the workflow control plane

`WORKFLOW_DESIGN_MANAGER`, `WORKFLOW_AUDITOR`, `WORKFLOW_IMPLEMENTER`,
`WORKFLOW_REVIEWER`, the `hmasd-workflow-*` profiles,
`hmasd-collaborative-workflow-design`, `hmasd-workflow-change-audit`:
**not migrated.**

They govern the Codex control plane, which is hard read-only from this branch
and is not edited here at all. The Claude control plane (`CLAUDE.md`,
`.claude/`) is maintained by the orchestrator directly, always in dedicated
configuration commits never mixed with science commits. There is no separate
Claude workflow-design authority and no approval gate for editing `.claude/`.

### Consolidated

| Codex object | Why there is no separate Claude counterpart |
|---|---|
| `hmasd-implementer-terra` (routine) vs `hmasd-implementer` (protected) | the split existed to route behaviour-preserving packages to a cheaper profile. Here that is a per-call `model` override on the one implementer contract, so the same economy costs one parameter instead of a second contract that can drift from the first. The criterion that made the split useful is preserved verbatim in `ORCHESTRATOR_WORKFLOW.md` §6.5: routine = behaviour-preserving modularization, localized repair, test maintenance, script cleanup, bounded performance; protected = estimand, RL/MARL mechanism, numerical or training semantics, registration, or any other protected invariant |
| `IMPLEMENTER` / `REVIEWER` / `CODE_SCOUT` / `VERIFIER` / `EXPERIMENT_OPERATOR` role charters | folded into the corresponding `.claude/agents/` contract, which is self-contained. There is no charter layer above the agent file |

### The six-phase execution-readiness exercise — not migrated

The Codex `VERIFIER` had one specific mechanism: a spec-driven wrapper script
running six named phases exactly once (`interface_smoke`, `bounded_exercise`,
`artifact_validation`, `artifact_reload`, `evaluate_entry`, `analyze_entry`),
terminating `HMASD_EXECUTION_READINESS_PHASES_OK`, then a separate `finalize`
pass writing a Git-private receipt bound to the commit and the exact accepted
paths — with readiness accepted only against that receipt.

**None of that is present here, and `hmasd-verifier` is not it.** The Claude
verifier runs the exact commands its assignment names and classifies each
outcome; it has no phase list, no wrapper script, and writes no receipt.

Two reasons, both structural. The wrapper lives under `.agents/skills/`, which
is hard read-only from this branch and belongs to a control plane that is
dormant. And the mechanism presupposes a production entry point with a
train → evaluate → analyze artifact lifecycle; the candidates worked on here are
self-contained experiment modules whose readiness question is answered by their
own registration gate and focused tests.

If a candidate ever grows that lifecycle, this is a real gap and building the
equivalent is the correct response. **Do not treat a `VERIFICATION_PASSED` from
`hmasd-verifier` as an execution-readiness receipt** — it binds no commit and
covers no phase list.

## Context budget — the reason most of these exist

Delegation here buys two different things, and confusing them is why the
subagents went unused for so long.

**Independence** — only `hmasd-reviewer` buys this, and the orchestrator
cannot buy it any other way. Once this session has written the code it has also
written the reasoning that makes the code look correct, and it cannot un-read
it.

**Context** — everything else. The orchestrator's window is the scarce resource
in a long session; raw output that no one will re-read is the largest consumer
of it. Delegating moves the reading elsewhere and returns a verdict.

| Pressure source | Typical size | Absorbed by |
|---|---|---|
| Full test-suite run | 300–800 lines of output | `hmasd-verifier` |
| Long registered training run | minutes to hours; artifact 100s of KB | `hmasd-experiment-operator` |
| Project-wide existence / semantics search | dozens of files skimmed | `hmasd-scout` |
| Inventory, byte compare, hashing, log tails | tens of lines each, repeated | `hmasd-mechanic` |
| Reading a whole change set closely enough to judge it | full files, not diffs | `hmasd-reviewer` |
| Building against a frozen brief | brief + every touched file read in full | `hmasd-implementer` |

A verdict that hides a discrepancy is worse than the raw output it replaced. All
six contracts state this: a mismatch is the most important fact a child can
return, and it is never compressed away.

## Maintenance

When a Claude agent or skill is added, changed or removed, update this registry
**in the same commit**. The failure this document exists to fix is a capability
that is defined but not reachable: `.claude/agents/` held four working contracts
for a full day of sessions while every task ran inline, because nothing said
when to reach for them. A capability absent from this registry and from
`ORCHESTRATOR_WORKFLOW.md` §6.2 will not be used.
