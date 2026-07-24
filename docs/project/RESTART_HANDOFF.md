# Handoff

Date: 2026-07-24
Branch: `untied-k`
Successor orchestrator: Fable, fresh conversation
Reason: seam handoff after the Codex to Claude Code migration

Read `AGENTS.md`, then this file, then `docs/project/CURRENT_WORK.md`. Nothing
else is needed to start.

## Terminal state

No process is running. No formal or nonformal compute was launched. The working
tree is clean and everything is pushed to `origin/untied-k`. `aggressive` was
not touched and stays at `4af01cd`.

## What this branch is for

`untied-k` explores making the skill period of an **individual agent** variable,
where today every agent shares one global period. Skill cardinality (`n_Z = 6`,
`n_z = 6`) and variable agent count are not the subject — the round question
states those exclusions explicitly.

## Your first action

```text
docs/external-review/rounds/20260724_untied_k_direction_bootstrap/21_PRO_OPEN_RAW.md
```

711 lines, archived verbatim with byte equality confirmed, **not reconciled**.
Read it and reconcile it code-side into
`30_PM_CODE_SIDE_RECONCILIATION.md`. Nothing downstream has started: no design
frozen, no plan written, no implementation.

The round asked whether per-agent variable period resolves the fast/slow credit
impasse that G17, G18 and G19 all ran into, or is a distraction from a different
root cause. The question marks its own provenance — the impasse framing is
Project Manager inference, not an established result, and the round invited the
reviewer to discard it.

Remember the authority split when you read it: **the scientific decision is
Pro's, not yours.** You turn it into code.

## Execution mode

```text
execution_mode=authorized
autonomous_research_grant=ACTIVE_TEN_ITERATION_TOY_FIRST_UAV_PROMOTION_CHAIN
grant_unit=completed_workflow_cycle
intermediate_authorization_prompts=forbidden
iterations_remaining=8
```

Run unattended. Asking for an approval this grant already covers is a defect,
not caution. You stop only at an exhausted grant, a user pause, an unrecoverable
blocker, or a real expansion of protected authority.

`formal_compute_authority` is `user_only`, and this grant is that authorization
for eight completed cycles.

## The three control points, which are different things

- **Checkpoint** — where the loop waits for the user. In this mode there are
  two, neither per-iteration: the grant reaching zero, and a change needing
  authority the grant does not carry.
- **Boundary crossing** — a scientific decision you cannot make. Do not guess
  and do not stall. Open a round and converge with Pro until both sides state
  the same thing, archiving every turn to `22_PRO_CONVERGENCE.md`, then resume
  where you stopped. Convergence turns are not fences; the fence is one per
  round and never resubmitted.
- **Compaction seam** — between iterations only. Write this file, compact,
  resume, continue into the next iteration. It is a context boundary, not a
  control boundary: it asks nothing and waits for no one.

## Setup a fresh clone needs

```powershell
git config core.hooksPath .githooks
```

Without it the drift guard is inert. Nothing else requires setup.

## What is proven and what is not

Exercised: `hmasd-scout`, and `hmasd-review-exchanger` through one complete
unattended 13-minute round — fence submitted, generation watched to stable
completion, raw archived with byte equality, intake written, no Git touched. The
GitHub connector reached all 12 evidence paths at `stage_commit`, so
pointer-only submission works end to end.

Not yet exercised: `hmasd-implementer`, `hmasd-reviewer`, `hmasd-verifier`,
`hmasd-code-scout`, `hmasd-patcher`, `hmasd-monitor`, `hmasd-exp-recorder`,
`hmasd-experiment-operator`. Stages 2, 4 and 5 of the cycle have never run.
Authorized mode is the user's decision made in full knowledge of this.

Watch the first lap. A subagent that returns something structurally wrong is
more likely on its first invocation than later.

## The drift guard

A pre-commit hook runs the three workflow contracts whenever a commit touches
`AGENTS.md`, `CLAUDE.md`, the role charters, the subagent definitions, the hmasd
Skills, `docs/project/`, the reviewer registry, or the contract tests.

It has already caught two real errors, both mine. If it blocks you, repair the
contract — do not weaken the assertion. A weakened check reads as covered
forever after.

## Known open items

1. **`docs/workflows/research-iteration-cycle.md`** carries a build list. Items
   1–4 are done; item 5, the grant-renewal checkpoint brief
   (`docs/report/GRANT_<id>_BRIEF.md`), does not exist and will be needed when
   `iterations_remaining` reaches zero.
2. **The third-party skill pack under `.claude/skills/` is untracked.**
   `.gitignore` negates only `hmasd-*`. Deliberate, but a fresh clone will not
   have the rest.
3. **A UAV G1 formal run on `aggressive` remains deferred** —
   `logs/formal_uav_temp_loss_g1_cpu_20260723_b125efd_r1`, source
   `b125efd205e302666aea78b286d6857f8ecf9286`, token
   `AUTHORIZE_UAV_TEMPORARY_SERVICE_LOSS_G1_FORMAL_CPU_V1`, zero batches
   completed, no iteration consumed. The exact three-phase command block is in
   the previous version of this file: `git log -p -- docs/project/RESTART_HANDOFF.md`.
   It is an `aggressive`-branch decision needing fresh authorization; nothing on
   `untied-k` depends on it.

## Continuity

There is no persistent task. Continuity lives in the repository:
`CURRENT_WORK.md` for the boundary, `ExpRecord.md` for results,
`docs/research/cdc/` for the portfolio, this file for the seam, Git for the
rest. Those must be accurate before a context ends, not after — that is the
whole reason the compaction seam is ordered the way it is.
