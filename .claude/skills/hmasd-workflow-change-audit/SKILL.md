---
name: hmasd-workflow-change-audit
description: Use before changing the control plane — CLAUDE.md, AGENTS.md, a subagent definition, a Skill, or a contract test. Carries the impact matrix, the structural checker, and the rule that a change is not done until a guard has been watched failing.
---

# Control-plane change audit

Project Manager only. Load this **before** touching any of:

- `CLAUDE.md` or `AGENTS.md`;
- `.claude/agents/*.md` or `.claude/skills/*/SKILL.md`;
- `tests/*_contract_test.ps1`.

Not for algorithm code, run artifacts, or `docs/research/`. Those are the
research loop. `docs/project/CURRENT_WORK.md`, `ExpRecord.md` and the round
directories are **state**, not control plane — they record what happened, they
do not bind an actor, and they are outside this procedure.

This grants no scientific authority. A change that alters what External Pro
decides, or what a result means, is not a workflow change.

## Why this exists

On 2026-07-28 a rule was found that had never once been executable. The
compaction Skill said the cadence "must survive the thing it governs, so
`CURRENT_WORK.md` carries `iterations_since_last_compaction`" — and that key had
never been written to that file in any revision. The rule was read on many turns
and followed on none. Nothing compared the claim against the file it named.

That is the failure class this procedure exists to catch: **a rule that names
something which does not exist.** It is invisible to review, because reading the
rule tells you nothing about whether its referent is real.

## The loop

**1. Inventory.** Search the control plane for the changed identity, path,
authority term, and every retired name. Historical narration — a document
recording that something *was* deleted — is evidence, not a repair target.

**2. Classify.** Before editing, build a task-local impact matrix, one row per
surface found:

```text
path | relation | action | evidence
```

`action` is exactly one of `modify`, `add`, `delete`, `unchanged-valid`,
`historical-exempt`. Declare the owned path set up front and preserve any dirty
changes outside it — a background child's uncommitted work is not yours to stage.

**3. Probe before implementing.** Run the smallest existing contract that
*should* already catch this change.

- If it fails, good: the guard works and you now know its shape.
- **If it passes despite a relation you know is missing, that guard is the
  defect.** Add one negative regression for that relation. Do not expand a
  coverage suite; add the one assertion that would have failed.

**4. Implement.** Close the smallest dependency set. Every agent definition is
routed by a document someone actually loads; every Skill is named in `AGENTS.md`
or `CLAUDE.md`; every registered name exists on disk. Delete superseded paths
rather than keeping aliases — a compatibility alias in a control plane is a
second live rule.

**5. Verify closure.** All four, no substitutions:

```powershell
& 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe' `
  .claude/skills/hmasd-workflow-change-audit/scripts/check_control_plane.py --repo .
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tests/hmasd_research_workflow_contract_test.ps1
```

Then the targeted stale-name searches from your matrix, and `git status --short`
to confirm the actual staged path set equals the declared one.

Retiring a name? Add it to the checker's `DEFAULT_FORBIDDEN` in the same commit
that retires it, so the next document to resurrect it fails. `--allow-forbidden`
exists for the single commit that performs the retirement, nothing else.

**The checker is structural.** It proves referents exist. It cannot tell you a
rule is *wrong*, only that it is *unbacked*.

**6. Reload smoke.** Skills and agent definitions are discovered at session
start. If you added, renamed or deleted one, a fresh session is required before
anything can dispatch it — say so explicitly rather than assuming this session
can use what it just wrote.

## A guard is not done until it has been watched failing

Every new assertion, in the checker or a contract test, must be seen red before
green, under a change that breaks exactly the property it names. Record the
mutation and the message.

The cheapest paired negative in this repo is ordering: edit the *expected* set
first and run — the guard should fail naming the drift — then make the change
that satisfies it. That costs one extra run and proves the guard can fail.

A guard that has never gone red is indistinguishable from a comment.

## Accept / stop

**Accept** when: the matrix is classified, the checker passes, the focused
contract tests pass, stale-name searches are explained, the staged path set was
inspected, and every new guard was watched red.

**Stop** and return to the user for: a change to who decides something, an
ambiguity about whether a surface is active or historical, a same-file collision
with a running child, or a rule you cannot make executable by the actor it binds.

That last one is the important stop. A duty the bound actor has no affordance for
does not produce a refusal — it produces an invention. Delete the rule or give it
a mechanism; do not write it down and hope.
