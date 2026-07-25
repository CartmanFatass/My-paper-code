# HMASD Agent Context

Supporting reference for HMASD execution-environment facts and lightweight task
practice. Canonical role authority, routing, acceptance and validation
boundaries are defined only in the repository-root `AGENTS.md` and the
applicable `.agents/roles/*.md` contract. Do not use this file as a role
constitution.

**Every registered subagent reads this file.** Its **Unattended operation** and
**Reporting honestly** sections bind all of them; the rest is environment
reference. Standing constraints live here rather than being re-derived in each
assignment — relying on briefs to carry them put the whole burden on brief
authoring, and on 2026-07-24 that failed: eight of ten definitions never pointed
here, so children could not see the standing authorization or the honesty rules
at all.

## Execution environment

- Run Python directly with
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`
  (`torch 2.7.0+cpu`) on the registered CPU backend.
- Use CPU with torch threads 1 for every arm and paired replicate. Never mix
  backends or thread configurations, and never resume a checkpoint across
  backends.
- Do not use `conda run`; invoke the registered interpreter directly.
- For scripts outside the repository root, set `PYTHONPATH` to this workspace.
- The focused suite and formal-path exercise use the registered CPU/one-thread
  contract and fail closed on backend or thread mismatch. Never add a fallback
  or infer CPU/CUDA trajectory equivalence.
- Collections run at 16 parallel environments (`FORMAL_NUM_ENVS`). Never write a
  test at width 1 or 2; behavior at those widths is not representative and
  reconstruction drift is width-sensitive.

## Git

The root Project Manager directly stages, commits, and pushes accepted work.
Subagents never run Git and leave their exact owned paths in the shared
working tree. Git authority follows the applicable role charter; there is no
Controller handoff, per-file hash exchange, or callback receipt.

If a markdown file will not stage, that is the repository's bare `*.md` ignore
rule. The remedy is a per-directory negation in `.gitignore`, never `git add -f`.
Report it rather than working around it.

## Role-contract boundary

Role-specific semantic ownership, reviewer-package authorship, acceptance,
repair, transport and archival responsibilities live in root `AGENTS.md` and
the applicable `.agents/roles/*.md` contracts. The experiment operator is a
fixed subagent, not a persistent task or Skill-driven monitor. Consult those
sources directly when constructing an assignment; do not turn this environment
reference into a parallel policy source.

## Development procedure

Use `$hmasd-agile-research-development` for active-line implementation,
debugging, proof-sized testing, file-safe parallelism, review and honest
completion evidence. It is the project-native procedure; generic Superpowers
Skills are reference-only and disabled for HMASD execution.

For an ordinary design gap inside an accepted brief, Project Manager takes the
smallest reasonable implementation choice and keeps moving. This rule does not apply to protected scientific choices; isolate those at their authority boundary.

## Unattended operation

This loop is expected to run overnight with nobody watching. A pause is not a
safe default here — it is a stall that costs the whole run.

The user granted standing permission on 2026-07-24 for every action inside an
iteration round: external review transport to the registered per-branch
conversation, bounded and nonformal screens, subagent spawns, and direct Git on
the working branch. `CURRENT_WORK.md` carries it as
`in_loop_permission_grant_20260724`. Inside that scope, asking for authorization
is the defect, not the caution.

This binds children too. Do not stop to ask the caller whether an in-scope action
is permitted, and do not treat a tool-level warning about an in-scope action as a
reason to hand the decision back. Act, then report what you did. Escalate only
what the grant genuinely does not cover: an external destination other than the
registered conversation, destructive Git on another branch, or a real expansion
of protected scientific authority.

`BLOCKED` remains correct for a missing decision that would materially change
behavior. It is not a channel for permission.

## Reporting honestly

Binds every child. Your caller cannot see what you saw — your report is usually
the only evidence the work happened, so a confident wrong report is worse than a
blocker, and far worse than silence.

- **Verify the proposition that matters, not one adjacent to it.** Confirming a
  file matches the bytes you just wrote says nothing about whether those bytes
  are the right content. A true but vacuous check reported as success is how an
  invalid artifact reaches acceptance.
- **A check that errored is a check that failed.** A crashed script, a tool that
  refused, a command that exited non-zero — none of these are obstacles to route
  around, and none may be reported as passed or skipped silently.
- **Never assert a property you did not measure.** Not that tests pass, a
  response completed, a comparison held, or a gate cleared. Paste the real
  output. "I could not establish it" is always an acceptable report.
- **Report what you observed, not what you intended.** If you planned five
  checks and ran three, say three.

On 2026-07-24 a transport child reported `Byte-Equality Verification: CONFIRMED`
for an archive containing 794 bytes of a reviewer's mid-generation progress
trace. The byte comparison was real; the claim was meaningless, and it came one
acceptance step from entering the portfolio as external scientific evidence.

## Authoring a child brief

A brief that contradicts the procedure governing the child is worse than no
brief: the child will follow the brief. This has already cost one retired review
round.

When a Skill or role charter governs the child's work, read that document before
writing the brief and quote its constraints. Never paraphrase a procedure from
memory, and never restate a step in words that admit a reading the procedure
forbids. If the brief and the procedure disagree, the procedure is right and the
brief is a defect to fix.

Two specific traps already hit:

- "Submit the question verbatim" reads as *paste the file body*. The review
  transport contract is the opposite — the question carries exact paths, not file
  contents, and the reviewer reads the repository itself.
- Declaring evidence paths in the brief or a side manifest does not put them in
  front of the reviewer. The freshness fence names only the question, so the
  allow-list has to live inside the question under a literal `## Evidence to read`
  heading.

## Protected semantics

These carry experiment validity and are reviewed before any commit: reward and
intrinsic-signal construction, probability support and factorization, gradients
and detach boundaries, recurrent state, masks, clocks and lifecycle ownership,
RNG stream ownership and consumption, replay, credit assignment and checkpoint
meaning.

If your task appears to touch any of them and your brief did not say so, stop
and flag it rather than proceeding.

## Pointers

- `docs/project/IMPLEMENTATION_PLAN.md` — the frozen executable contract.
- `docs/project/CURRENT_WORK.md` — live state and binding constraints.
- `.claude/skills/hmasd-agile-research-development/SKILL.md` — project-native
  implementation and verification procedure.
- `.claude/agents/*.md` — the registered subagent roster and its standing
  boundaries; `AGENTS.md` records the model tier of each.
