# The Codex control plane, reviewed against the §11 calibration and the 2026-09-02/03 practice

Scope: `AGENTS.md` (HEAD `ad1aff499`, 2026-09-01), `.codex/config.toml`, the sixteen
`.codex/agents/*.toml` definitions, the four HMASD skills under `.agents/skills/` plus the
third-party skills tracked beside them, the two empty authority surfaces (`.agents/roles/`,
`.codex/prompts/`), the untracked `.codex/runtime/`, and the eight uncommitted control-plane edits
dated 2026-09-03 09:57 PDT in the working tree. Read against `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`
§11 (2026-09-02), the three Portfolio decision records since then, and what the two-day practice
under those rules actually produced (`FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` Parts C–F,
`ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` Parts IX–XII). The earlier
`CODEX_SCIENCE_WORKFLOW_REVIEW_20260901.md` reviewed the same surfaces as a research process; this
document does not repeat it. Its recommendations R3, R6, R7, R8 were left as "need an
`AGENTS.md` edit"; §5 below says what that edit is.

Facts are from a read-only inventory of the working tree at 2026-09-03 17:45 PDT. Judgments are
the reviewer's. Nothing here edits an authority file; §7 lists what only the owner can decide.

## 1. What the control plane is, in one paragraph

`AGENTS.md` makes the user request the authority, Root the single coordinator and integrator,
and three persistent ChatGPT Pro conversations the deciders: `em:<direction>:innovator` before an
object is frozen, `em:<direction>:convergence` before any lifecycle recommendation, and
`portfolio:cross_direction` for priority, capacity, lifecycle, fusion and investment. "A complete
Pro decision is final for its node." Three fixed native subagents (DM, EM, CM) prepare evidence
and execute; thirteen optional specialists are read-only analysts, fenced writers or a one-shot
launcher. Two skills carry packets to and from Pro (`hmasd-pro-research-prompt-author`,
`hmasd-chatgpt-pro-transport`), one skill governs Portfolio decisions, one governs outsourcing of
control-plane edits. Integrity rules: memory admission before every result-bearing launch; no
silent change of scientific meaning; an incomplete attempt is quarantined and consumes nothing;
commit then push immediately.

## 2. What happened under it since the calibration, measured

| Measure | Value | Source |
| --- | --- | --- |
| Pro-node rounds archived, 2026-09-01 | 6 (five innovator, one convergence), last at 20:09Z | transport registry, 11 bindings |
| Pro-node rounds, 2026-09-02 → 09-03 | 0 | registry mtime 09-01 13:10; no new intake files |
| Portfolio decision records since 09-02 | 3, all `OWNER_DIRECT` or owner-delegated; none `PRO_FINAL` | `decisions/2026-09-0{2,3}-*.md` |
| Intake sections written by the reviewer, 09-02 → 09-03 | 50 (Parts C–F of the compliance note) | heading count |
| Decision points recorded in them | 16 "Decisions this intake produces" sections; 7 owner-delegated selections since 13:58 PDT 09-03 | grep |
| Result documents produced, 09-02 → 09-03 | 17 (UCOPE 12, SCDMP 2, VNFC 1, FSD E0/E1) | file listing |
| Commits to `main`, 09-02 → 09-03 | 92, one author identity, at least three concurrent sessions | git log |
| CBSC B1 attempts, 09-03 | 4 failed, none scientific: `MAX_PATH`, unsatisfiable provenance predicate, evaluation key + hard-coded count, HEAD-currentness guard | E.6–E.9 |
| Reviewer errata in two days | 3, all from diagnosing by reading rather than reproducing (E.6, XII.5, E2 false alarm) | E.7, XII.6, D2a |
| Agents killed at once by one rate limit | 4 (13:30 PDT); owner then capped concurrency at 2 | session record |
| Runners calling `scripts/hmasd_run.py` | 0 of 99 `scripts/run_*.py` | grep |
| Runners or September evidence citing `scripts/hmasd_operator_result.py` | 0 | grep |

Read together: the decision path `AGENTS.md` describes (Pro nodes final, DM/EM/CM prepare) has
not been exercised since the calibration. The path that produced the seventeen results is a
different one: an owner-direct or owner-delegated decision, taken in a reviewer's intake section
against a science card, executed by an implementer subagent that owns card → run → result
document. The prior review measured one valid learner observation per wave under the old path;
this path produced seventeen result documents in two days with decision documents at roughly
one-to-one. The control plane should describe the path that works.

## 3. Clauses that are now stale, with the fix for each

| # | Clause (where) | What changed | Effect if left | Fix |
| --- | --- | --- | --- | --- |
| S1 | "Scientific and portfolio decisions pass through the persistent ChatGPT Pro decision nodes… A complete Pro decision is final" (`AGENTS.md` operating model; `hmasd-em.toml`; `hmasd-portfolio-task`) | Since 09-02 every decision was owner-direct or owner-delegated; decision records already use `FINAL / OWNER_DIRECT / ROOT_INTEGRATED`, a label no authority file defines | Two authority systems: the written one nobody follows and the practiced one nobody wrote down. An agent reading `AGENTS.md` cold would refuse to proceed without a Pro round | Define a decision ladder (§5, T2): object-level decisions by the reviewer intake under delegation; lifecycle by the owner; Pro nodes optional consultants with a dissent channel |
| S2 | EM must send an innovator packet "before adopting a new direction-level mechanism or freezing a new conclusion-bearing C object" (`hmasd-em.toml`) | §11.1: B is entered directly from an inspiration model; frozen contracts are C-time obligations | An innovator round becomes a B launch gate, which §11.4 forbids | Innovator round only before a C freeze or on request |
| S3 | "Mandatory performance readiness": a `PERFORMANCE_READY / PILOT_ONLY / REPAIR_REQUIRED` disposition with 1/2/4-worker equivalence "before any … materially result-bearing path can launch" (`hmasd-cm.toml`) | §11.4 names the only things that may hold a B launch; a capacity or performance gate is not among them. And the gate mis-targets: E2's cost law (`M ∝ 1/k`, 6.8 h in one arm) was missed because the doctrine measures throughput of one path, not the per-arm budget of a sweep; CBSC's four failures were in the post-learner publication path the doctrine never asks to exercise | A heavy gate that does not catch the two failure classes this wave actually had | Demote to two recorded lines: a per-arm cost projection before any sweep, and an offline end-to-end exercise of the post-learner path against existing evidence before a fresh attempt (§5, T3) |
| S4 | An attempt that omits "resource observation" is incomplete and quarantined (`AGENTS.md` integrity; `hmasd-em.toml` "Missing admission, telemetry…") | Owner decision 2026-09-02 (recast record): missing resource telemetry keeps the run valid, marked `resources_unmeasured`; only learner-side instrumentation quarantines | The written rule annuls runs the owner has ruled valid | Copy the recast record's telemetry rule into `AGENTS.md` verbatim |
| S5 | "Root is the single top-level coordinator and owns final integration"; `max_concurrent_threads_per_session = 40` (`config.toml`); DM/EM told to run branches in parallel | Reality: at least three top-level sessions (Codex, the Claude reviewer, Opus implementers in worktrees) commit to `main` concurrently; the binding resource is the rate limit, which the owner capped at two implementer sessions | The shared-index incident (a reviewer commit swept in an implementer's staged files, 09-03) and the CBSC `BLOCKED_UNCOMMITTED` refusals are both consequences of a single-integrator assumption in a multi-session repo | Write the concurrency model: pathspec commits, worktree per implementer, surface-hash currentness guards, a capacity field that is a number (§5, T4–T5) |
| S6 | Push policy and sandbox rule (`AGENTS.md` Git) | Still correct; three of the last four `AGENTS.md` commits were about push/retry/sandbox mechanics | None scientific; note only that control-plane effort has gone to transport plumbing | Keep; move to a "Codex specifics" appendix |
| S7 | `$hmasd-workflow-outsource` sends to a fixed thread UUID (committed) versus spawns one Terra/high agent with `spawn_agent` (uncommitted 09-03) | The uncommitted rewrite is a different mechanism; `AGENTS.md` still says "one dispatch to the named target" | Skill and authority disagree until one is committed | Owner: commit or discard the 09-03 edits (§7) |
| S8 | Prompt author: "The normal path returns to this exact source thread; it must not rely on Transport fallback routing" versus transport (uncommitted): "force every `destination_thread_id`" to one fixed session | The two halves of one pipeline now contradict each other on where the receipt goes | A receipt that the author says must not use the fallback is always routed to it | Pick one; the fixed-session route is the simpler and matches the uncommitted state schema |
| S9 | `docs/external-review/README.md`: "Canonical authority is in `AGENTS.md` and `.agents/roles/`"; outsource skill lists `.agents/roles` as a control-plane surface | `.agents/roles/` is empty (retired in `898fc82f5`) | Dangling authority pointer | Delete the reference or the directory |
| S10 | CM and operator cite `scripts/hmasd_run.py` and `scripts/hmasd_operator_result.py` as the run wrapper | No runner calls either; September evidence cites per-run manifests written by the runners themselves | The wrapper is advisory in practice; the TOMLs present it as the frozen entry point | Either make one runner use it as the reference pattern or drop the citation |
| S11 | Effort and model assignments (uncommitted 09-03): CM and DM `max → high`; routine implementer `terra/high → luna/max` | Owner's choice; noted because the routine implementer now runs the cheapest model at the highest effort while the semantic implementer runs the strongest model at `high` | Possible inversion of where reasoning is spent | Owner to confirm the intent (§7) |
| S12 | `AGENTS.md` names Codex only; `CLAUDE.md`, `docs/Claude_docs/`, the reviewer role, predict-then-verify, the unattended-delegation record and the two-direction cap appear nowhere in it | Two runtimes share the repository, git, the evidence spec and the portfolio, but not the authority document | An agent on either runtime cannot learn the other's standing rules from the repo | One runtime-neutral `AGENTS.md` with two short appendices (§5, T1) |

Two small staleness items outside the table: `CLAUDE.md` says of itself that it is gitignored
(it is tracked since `71b2bba2b`); and the `hmasd-em.toml` reading list starts with
`docs/project/ALGORITHM_PRINCIPLES.md`, a 2026-07 document that predates the evidence spec and
is not in `CLAUDE.md`'s navigation table, so its current standing is unclear.

## 4. Topology: what is written and what runs

Written (from `AGENTS.md` and the TOMLs):

```
owner ──request──▶ Root ──▶ DM(direction) ──▶ EM ──packet──▶ Pro innovator / convergence (final)
                     │                        └──objective──▶ CM ──▶ implementer / scout / reviewer / verifier / operator
                     └──packet──▶ Pro portfolio (final) ──▶ Root records in PORTFOLIO.md
```

Five hops from the owner to a run. Three of them (DM, EM, the Pro round) each add an intake
document and, per the prior review, no check the reviewer or critic does not already perform.

Practiced 2026-09-02 → 09-03:

```
owner ──decision / delegation──▶ reviewer (Claude) ──card + prediction──▶ implementer (Opus, worktree)
   ▲                                  │                                      │ preflight, detached run,
   │                                  │◀──result document + facts────────────┘ result doc, commit, push
   └──intake with options + recommendation, decisions recorded, PORTFOLIO row──┘
```

Two hops. The reviewer holds four functions at once: adversarial intake, prediction on record,
decision recording under delegation, and integration (merge, portfolio row, README). The
implementer holds the whole card → run → result chain for one direction and nothing across
directions. The Pro nodes are absent; the owner is present at lifecycle decisions and, since
13:58 PDT 09-03, delegated at object-level ones.

What the practiced topology got wrong this wave, so the proposal does not idealise it:

1. **Reviewer diagnosis by reading.** Three errata in two days, each corrected by the implementer
   reproducing the failure. The reviewer should not classify a failure it has not reproduced or
   had reproduced.
2. **No pre-launch cost projection.** E2 launched eighteen runs on a one-arm projection; the
   cost law was measured after six rollouts of the wrong arm.
3. **Post-learner paths untested.** CBSC's four failures were all in orchestration code after
   the learner, none covered by the direction's end-to-end test.
4. **Single-integrator assumptions in code.** The HEAD-currentness guard and the shared git
   index both failed under concurrent sessions.
5. **No resume model.** One rate limit killed four agents and lost one worktree; the cron
   heartbeat and the "commit early, launch detached" rule were improvised afterwards.

## 5. Recommendations, in the order to adopt them

T1. **One authority document, two runtimes.** Rewrite `AGENTS.md` runtime-neutral: operating
model, decision ladder (T2), integrity rules with the 09-02 telemetry rule, concurrency and git
rules (T4, T5), and the standing owner instructions that are currently only in decision records
and memory (two-direction cap, unattended delegation with its exclusion list). Append "Codex
specifics" (sandboxed push, task naming, TOML roster) and "Claude Code specifics" (pointer to
`CLAUDE.md` and `docs/Claude_docs/`, commit trailers). Cost: one document. What it would have
changed: every rule in §3 rows S4, S5, S12 would have been visible to the implementer agents
before they hit it.

T2. **A decision ladder that matches §11.** Three tiers, each with its provenance label:

| Tier | Decides | Who | Record |
| --- | --- | --- | --- |
| Object | next rung, card wording, arm drops, budget deviations inside a cap, quarantine of an attempt | reviewer intake; owner-delegated when unattended | intake section with options, recommendation, `Owner-delegated decision (…)` line |
| Direction | open or close an object family, park, recast, next object after a consumed C | owner, on the reviewer's recommendation; a Pro convergence round when the owner asks for one | decision record `OWNER_DIRECT` or `PRO_ADVISED` |
| Portfolio | priority, capacity, fusion, separation, registration, investment | owner; `portfolio:cross_direction` on request | decision record, PORTFOLIO row |

Pro nodes stop being a launch condition anywhere and become a consultation the owner or reviewer
invokes with the exposure card and a dissent channel (prior review R2, R3). The transport
machinery is kept as is; it is simply no longer on the critical path of a B object.

T3. **Replace the performance gate with the two lines this wave was missing.** In CM's method
(or its successor role): (a) before any sweep, a per-arm cost projection from the runner's own
cost law, recorded in the card, with the cap applied per arm rather than to the sum; (b) before
any fresh attempt after a post-learner failure, an offline end-to-end exercise of the publication
path against existing quarantined evidence, and an end-to-end test profile that reaches the
formal path with its real constants. Both are recorded fields, not gates, except that (a) is
required for a sweep because a sweep without it cannot state its budget. Drop the 1/2/4-worker
equivalence and the disposition vocabulary from the B path; keep them as C-time obligations.

T4. **Model the capacity that binds.** PORTFOLIO's `Investment capacity: UNBOUNDED` becomes two
numbers: concurrent implementer sessions (owner: 2) and concurrent result-bearing runs (2). Set
`max_concurrent_threads_per_session` to match rather than 40. Record usage per valid result
(prior review R6) as the ranking currency; the seventeen results of 09-02/03 against four CBSC
attempts is the first data point. Make the resume mechanism explicit: commit before launch, launch
detached, a heartbeat that resumes killed agents, agent state recoverable from the repo alone.

T5. **A git model for concurrent sessions.** Written once, applied by every runtime: every
implementer works in its own worktree and branch; commits stage by explicit path and commit by
pathspec; `git add -A`, stash and reset are forbidden in agent instructions; the integrator
merges; any "is the code current" guard compares the bound commit's surface hash with HEAD's
surface, never the commit id (the CBSC repair now under way is the reference pattern); `.codex`
`config.toml` and `CLAUDE.md` both point at this section.

T6. **Diagnosis by reproduction.** Add to the integrity section: a failure classification
(technical, instrumentation, scientific) is recorded only after the failing step has been
reproduced over the recorded bytes, by the reviewer or by the implementer at the reviewer's
request; a classification from error text alone is provisional and says so. This is the single
rule that would have removed all three errata.

T7. **Fold the roster to what the practice uses.** Keep: implementer (with the semantic fences),
routine implementer, scout, reviewer, critic, verifier, operator, design reviewer. Fold DM into
Root and EM into the implementer's card-writing duty (the card already carries the class, ceiling,
predictions and stop rule EM was to supply). Retire innovator, principles analyst, research scout
and workflow designer until a wave shows a check nobody else performs; their TOMLs can stay in
git history. Sixteen definitions become eight.

T8. **Housekeeping** (no scientific content; list for the owner, since deletion is theirs):

- empty directories presented as authority: `.agents/roles/`, `.codex/prompts/`,
  `.agents/skills/{hmasd-cm-task,hmasd-em-task,hmasd-root-task,hmasd-agentify-transport,hmasd-browser-conversation}/`;
- `.codex/runtime/` (untracked, 2026-08-26/27 clerk and dashboard leftovers of the retired
  control plane, including a 65 KB dashboard output);
- third-party skills tracked beside the HMASD ones (`ask-matt`, `grill-me`, `grilling`, `tdd`,
  `to-spec`, `to-tickets`, `implement`, `setup-matt-pocock-skills`): not referenced by
  `AGENTS.md`; move under a clearly non-authoritative path or untrack;
- `docs/external-review/README.md` pointing at `.agents/roles/`;
- the uncommitted 09-03 09:57 edits to three TOMLs, two skills, one state schema and
  `transport_contract.py` (273/231 lines): commit as one control-plane change or discard, and
  resolve S8 in the same commit;
- `scripts/hmasd_operator_result.py`: unused by runners and evidence; keep only if a runner adopts it.

T9. **Codify unattended mode.** The 2026-09-03 delegation record is the right content; it should
live in `AGENTS.md` as a standing clause with its exclusion list (lifecycle, priority, fusion,
capacity, investment, destructive actions), its audit format, its expiry ("until the owner says
otherwise"), and the heartbeat as the resume mechanism, so that a fresh session on either runtime
inherits it without the memory files.

## 6. What to protect while doing the above

The parts of the control plane that produced this wave's results and should survive any rewrite:
the quarantine rule with its 09-02 telemetry refinement; the memory admission; the implementer
fences on numerics, RNG, backend and topology; read-only critics with no acceptance authority; the
one-launch operator rule (a fresh attempt at a new sha is a new launch, not a retry, which is how
CBSC r01–r05 were handled); predict-then-verify with predictions on record before launch; and the
decision-record format with options, recommendation and provenance label.

## 7. Decisions for the owner

These are control-plane changes and are outside the unattended delegation. The reviewer's
recommendation is marked.

1. [DECIDE] Adopt the decision ladder T2 and remove Pro rounds as launch conditions. Recommended: yes.
2. [DECIDE] Rewrite `AGENTS.md` runtime-neutral per T1 with T4, T5, T6, T9 as sections. Recommended: yes, one commit, reviewer drafts, owner edits.
3. [DECIDE] Roster fold T7 (16 → 8 TOMLs). Recommended: yes; keep the retired definitions in history only.
4. [DECIDE] Replace the CM performance gate with the two recorded lines of T3. Recommended: yes.
5. [DECIDE] The 09-03 09:57 uncommitted control-plane edits: commit (with S8 resolved toward the fixed-session receipt) or discard. Recommended: commit, since the state schema and script already assume the fixed route.
6. [ASK] The routine-implementer model/effort swap (S11): intended?
7. [DECIDE] Housekeeping deletions in T8. Recommended: all of them; none carries scientific content.
8. [ASK] Standing of `docs/project/ALGORITHM_PRINCIPLES.md` after the evidence spec: still a required reading for implementers, or historical?

## 8. One-sentence verdict

The control plane still describes a five-hop, Pro-final, C-shaped process that has not run since
the calibration, while the two-hop owner-and-reviewer loop that produced seventeen results in two
days exists only in intake sections and memory files; write down the loop that works, keep the
integrity rules that made it safe, and cut the roster and gates to what that loop uses.

## 9. Addendum, 2026-09-03 18:07 PDT: the owner's intent for the Pro nodes

The owner clarified why the Pro nodes exist: the Codex side is meant to run a highly automated
research loop, unattended most of the time, with the owner stepping in only at key decisions and
only from the records. That changes the reading of §3 S1 and §5 T2. The Pro nodes are not a
ceremony to demote; they are the Codex side's substitute for the absent owner, the same role the
reviewer has played on the Claude side since the 13:58 PDT delegation. The two runtimes have the
same goal and differ only in who decides when the owner is away.

What the measurements then say is narrower than §2 put it: not "the Pro path does not work" but
"the Pro path is too expensive to sit on every object-level decision". Two days produced sixteen
object-level decision points and three direction- or portfolio-level records. A Pro round costs a
packet, a browser transport with a 15-minute heartbeat, a 20–60 minute generation, an archive and
a receipt; under those costs, the loop chose not to use it at all. Sixteen rounds a day is not an
unattended loop; three is.

Revised recommendations (they replace T2 and amend T7; the rest of §5 stands):

T2′. **Three tiers, Pro at the top two, local at the bottom.** Object-level decisions (next rung,
card wording, arm drops, budget deviations inside a cap, quarantine of an attempt) are taken
locally by the loop driver under the written delegation policy: options, recommendation, selection,
provenance line, reversible actions only. Direction-level decisions (open or close an object
family, park, recast, the next object after a consumed C) go to `em:<direction>:convergence`
automatically, with the exposure card attached, and the owner audits from the record. Portfolio-
level decisions go to `portfolio:cross_direction`, which proposes; the owner ratifies from the
record, or the proposal takes effect after a stated audit window if the owner is silent and the
action is reversible. This keeps the Pro nodes exactly where the owner wants to look and takes
them off the path that was stalling.

T2″. **A blocker must not stall the loop.** `AGENTS.md` says a connector, evidence or transport
blocker "never transfers final authority back to a local model". Under unattended operation that
clause halts the direction until a human returns, which is the opposite of the intent. Replace it
with: on a Pro blocker, the loop driver takes the recommended option as a *provisional* decision
labelled `PRO_BLOCKED / LOCAL_PROVISIONAL`, restricted to reversible actions, queues the Pro round
for retry, and lists the item first in the owner's audit ledger. Authority is not transferred;
progress is.

T7′. **Keep DM as the loop driver.** For an unattended Codex loop the per-direction manager is
the natural analogue of the Claude reviewer-plus-implementer pair: it holds the card, the
prediction on record, the delegation policy, the intake and the escalation to Pro. Fold EM into it
(the card already carries class, ceiling, predictions and stop rule); keep CM and the fenced
implementers, scout, reviewer, critic, verifier and operator. Sixteen definitions become nine.

Three things the unattended Codex loop needs that this session had to improvise on the Claude
side, and that should be written into `AGENTS.md` once for both runtimes:

1. **An owner audit ledger.** One file per day or per wave listing every automatic decision with
   its tier, options, chosen option, reversibility, provenance label, and an empty owner column.
   The owner's intervention is editing that column; a non-empty entry overrides the decision and
   the loop applies it at the next boundary. This is the concrete form of "介入关键决策".
2. **A resume model.** Commit before launch, launch detached, a heartbeat that resumes killed
   agents, and every agent's state recoverable from the repository alone. One rate limit killed
   four agents on 09-03; the cron heartbeat that now resumes them is not in any authority file.
3. **A cost model the loop can read.** The rate limit, not compute, bounds both runtimes. The
   loop needs the per-arm cost projection (T3a) before a sweep and a usage budget per direction
   (T4) so that it can decide, unattended, what not to launch.

The prior review's R2 (exposure card in every packet) and R3 (engineering dissent record) become
the mechanism that makes the two Pro tiers affordable: the card gives the node the facts that
decided this wave, and the dissent record lets a wrong engineering premise be corrected in one
message instead of a round.

## 10. Addendum, 2026-09-03 18:12 PDT: Pro is the cheaper and stronger decider

The owner corrected §9's cost premise: Pro time is worth spending. The Pro model performs better
than the local models, and it runs on an independent quota, so a Pro round does not draw on the
rate limit that bounds the Codex and Claude sessions. On both axes, cost and performance, Pro is
the better decider. §9's "sixteen rounds a day is not an unattended loop" was an argument from
the wrong currency and is withdrawn.

What survives of §9 once cost is removed is only latency and blocking: a round takes 20–60
minutes of wall time plus transport, and the current design serialises requests per binding key
and puts the round on the direction's critical path. Neither is a reason to keep Pro off a
decision. Both are reasons to make the loop asynchronous.

Revised again (this replaces T2′; T2″ and T7′ stand):

T2‴. **Pro decides wherever judgment is needed; the loop does not wait for it.** Every decision
that selects what to run next, at any tier, goes to the direction's Pro node with the exposure
card attached: the next rung, a card's treatment and comparator, whether an arm is dropped, what
follows a consumed object, lifecycle, and Portfolio. The direction's loop then parks that
direction at a clean boundary (committed, runs detached, state in the repository) and the driver
moves to another direction; when the archive lands, the driver resumes the parked direction and
executes the decision. With independent quota the right number of rounds is the number of
judgments, not a budget. What stays local is what needs no judgment: applying a frozen rule to a
measured number (cap exceeded, quarantine after reproduction, preflight refusal), and the
mechanical intake of a result into its record. The owner audits from the ledger of §9 item 1,
where every Pro decision appears with its packet, archive hash and the action taken.

Two consequences for the transport. First, the serial-per-binding rule ("only one request may be
active per binding") is right for one conversation but must not serialise the loop: with twenty
ACTIVE directions and separate innovator and convergence conversations per direction, the driver
can have many rounds in flight, and the heartbeat must multiplex them (the skill already allows
one heartbeat over several directions). Second, the exposure card (prior review R2) becomes
mandatory in every packet, because the only failure of the Pro path the record shows is a
decision made without the arithmetic that decided the outcome (F1 in the prior review), and that
is fixed by what the packet carries, not by who decides.

Why zero rounds ran on 09-02/03 is then explained without a cost story: the owner was present and
decided directly, and the Claude reviewer took the object-level selections under delegation from
13:58. When the owner is absent and the Codex loop drives, the same selections go to Pro. The
Claude-side delegation of 09-03 is the fallback for a runtime without a Pro transport, not the
model for the Codex side.
