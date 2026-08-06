# HMASD Claude Code Entry

`AGENTS.md` is the sole project authority and routing contract for this
repository; it is hard read-only from this branch. Since the 2026-08-05
takeover the Codex role sessions are dormant: a Claude session here does NOT
resolve a Codex role. Instead the Claude orchestrator (the main session)
operates per `.claude/ORCHESTRATOR_WORKFLOW.md`, which fixes the actual
logical model: the orchestrator holds the local Explorer remainder plus all
Code Manager (cm/cpm) duties inline; ALL scientific judgment is externalized
to External Pro review (adversarial validation before any freeze, alignment
audit after every science commit); subagents are task tools, not roles.
That document organizes Claude-side work only and adds no authority over
`AGENTS.md`.

## The subagent workflow is mandatory, not optional

Work runs as **orchestrator → implementer → reviewer**, defined in
`.claude/ORCHESTRATOR_WORKFLOW.md` §6 and registered in
`.claude/CAPABILITY_MAP.md`. Read §6 before doing implementation work; the
short form:

- Freeze the assignment first — frozen brief, writable scope, focused tests,
  completion condition, forbidden paths. If that block cannot be written, the
  unit is not ready to delegate.
- **`hmasd-reviewer` is REQUIRED before technical acceptance of any
  claim-bearing change, and before any document goes to External Pro.** A
  clean-context reader is the one thing this session structurally cannot be:
  having written the code, it has also written the reasoning that makes the
  code look correct.
- `hmasd-implementer` when the brief is already frozen **and** this session
  holds reasoning the implementation should not inherit (typically: it argued
  the science, so it will build toward its own argument) — or, regardless of
  that second condition, when two or more independent bounded units exist and
  should run concurrently. §6.2 has the exact conjunction.
- `hmasd-verifier` (long suites, CLI exercises), `hmasd-experiment-operator`
  (registered runs of minutes or hours), `hmasd-scout` (read-only existence
  and semantics), `hmasd-mechanic` (read-only mechanical facts) exist to keep
  raw output out of the orchestrator's context.
- Children return raw facts and **never accept their own work**. Re-run their
  tests here before accepting; give every finding an explicit disposition
  (`APPLIED` / `RISK_ACCEPTED(reason)` / `REJECTED(reason)`); technical
  acceptance, git and all science stay with the orchestrator.

These six contracts in `.claude/agents/` are self-contained and Claude-native.
They operate inside `AGENTS.md` authority boundaries, do not load Codex session
charters, and grant no new authority. `.claude/CAPABILITY_MAP.md` is the full
logical migration of the Codex role/skill/agent structure — including the
capabilities deliberately NOT migrated (all research-critic roles stay with
External Pro; the workflow control plane is dormant) — written out in full so
no Codex surface has to be read to act on it.

Before dispatching anything to External Pro, use the `hmasd-science-dispatch`
skill. Its gate script exits non-zero and is not advisory; the clean-context
document review it requires can be waived only by writing a
`document_review_waiver_reason` into the manifest, which then travels in the
receipt.

## Research before you edit

- **Read a file before editing it** — in full, not just the region you intend
  to change.
- **Before modifying a function, grep for all of its callers** and check each
  one. A signature or return-shape change that compiles is not a safe change.
- **Research first, edit second.** Establish what the code actually does before
  writing the change, not while writing it.

## Experiment performance: backend, batching, parallelism — under one hard constraint

Experiments here run far slower than they should when they step a pure-Python
env one transition at a time and run independent seeds sequentially. Three
levers, in order of leverage:

1. **Compiled backend over pure Python.** Where a native/C++ backend exists for
   an environment (e.g. `envs/continuous_roster/cpp_backend.py` →
   `native/continuous_roster_toy_backend.cpp`) and covers the dynamics a
   candidate needs, route through it instead of re-stepping the Python env. A
   pure-Python reimplementation of an env that already has a compiled backend is
   the first thing to question — that is exactly why the UCOPE sibling
   (`runtime_capacity.py`, pure Python + numpy) is far slower than the Codex-era
   cpp-backed toy env.
2. **Batch the policy forward.** Thousands of batch-size-1 torch calls are
   dominated by dispatch overhead, not compute. Step N envs in lockstep and do
   one batch-N forward where the design allows.
3. **Parallelize independent runs.** Independent (seed, arm) runs are
   embarrassingly parallel; dispatch them across a process pool sized to the
   machine (this box: AMD 8745H, 8 cores / 16 threads).

**The hard constraint that governs all three:** a speedup must be EITHER
behavior-preserving — byte-identical outputs, proven by a local same-seed
comparison of old vs new — OR treated as a **new registered design**: re-freeze
the registration digest, and re-dispatch to Pro any result whose licensed
reading carries numbers. Bit-identity is a LOCAL mechanical check
(`ORCHESTRATOR_WORKFLOW.md` §3 routing rule), never a Pro question.

Which lever is which:

- **Process-parallelism of independent deterministic runs is byte-identical** —
  dispatch order cannot change a self-contained computation. Safe; only the
  source-content digest moves, and equality is proven locally.
- **Batching the rollout, changing the torch thread count, or swapping to a C++
  backend with different float ops all CHANGE the numbers** (RNG consumption
  order, matmul batch size, reduction order). Each is a new registration whose
  reading goes back to Pro.

Reproducibility note: results already silently depend on the ambient torch
thread count (`torch.get_num_threads()` was 8 on this box), which the
registration digest does not pin. Pin it explicitly when re-registering, and
prefer `torch.set_num_threads(1)` inside a parallel worker so the pool does not
oversubscribe.

Historical handoffs, archived results and unreferenced files are not active
instructions.

Longitudinal state lives in `local_research/RESEARCH_CONTINUITY.md` — read it
before resuming candidate work. This worktree and its branch
(`claude/hmasd-full-takeover-20260805`) are the permanent workspace; merges
to mainline happen only on explicit user instruction.
