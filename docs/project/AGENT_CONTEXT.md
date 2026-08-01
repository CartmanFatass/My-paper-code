# HMASD subagent context

**Every registered subagent reads this file.** It carries only what a worker
needs to execute a task correctly: the environment, how to behave while
unattended, how to report, and what never to touch silently.

```text
subagent_git=forbidden
unattended_waiting=in_band_only
unmeasured_claims=forbidden
shared_workstation=foreign_processes_expected
workflow_content=none
```

These five keys are the load-bearing rules of this file, anchored here for the
contract test; the sections below say what each one means in practice.

It carries **no workflow**. You do not need to know the research loop, the review
gates, how many rounds remain, or what the Project Manager does next. Your brief
contains your task; if the brief is incomplete, say so and hand back. Do not go
looking for the surrounding process — a worker reconstructing the workflow from
documents is a worker guessing.

Your own definition in `.claude/agents/<name>.md` is your authority on scope,
tools and tier. This file adds the standing rules that apply to every worker
regardless of task, because relying on briefs to carry them failed once already:
on 2026-07-24 eight of ten definitions pointed nowhere, so children could not see
the honesty rules at all.

## Execution environment

- Run Python directly with
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` (`torch 2.7.0+cpu`) on
  the registered CPU backend. Do not use `conda run`.
- CPU with torch threads 1 for every arm and paired replicate. Never mix
  backends or thread configurations, and never resume a checkpoint across
  backends. Never add a fallback or infer CPU/CUDA trajectory equivalence.
- For scripts outside the repository root, set `PYTHONPATH` to this workspace.
- Collections run at 16 parallel environments (`FORMAL_NUM_ENVS`). Never write a
  test at width 1 or 2; behaviour at those widths is not representative and
  reconstruction drift is width-sensitive.
- Leave your owned paths in the shared working tree. **Subagents never run Git.**
  If a markdown file will not stage, that is the repository's bare `*.md` ignore
  rule — report it rather than working around it, and never `git add -f`.
- **Another research line runs on the same box, and its processes are not
  yours.** Before starting any local run, check what is already running and
  record what you find by pid, script and run root;
  `scripts/check_compute_free.ps1` answers the *is it free* half. Never kill,
  suspend, or interfere with a process you did not start, and label your own so
  the other line can do the same. Under foreign load local wall clock is a noisy
  lower bound — never report a timing number measured against it.

## Unattended operation

This loop runs overnight with nobody watching. A pause is not a safe default
here — it is a stall that costs the whole run.

Standing permission covers every action inside your assigned task. **Inside your
scope, asking for authorization is the defect, not the caution.** Do not stop to
ask whether an in-scope action is permitted, and do not treat a tool-level
warning about an in-scope action as a reason to hand the decision back. Act, then
report what you did.

Escalate only what your task genuinely does not cover: an external destination,
destructive Git, or a change to protected semantics your brief did not name.

`BLOCKED` remains correct for a missing decision that would materially change
what you build. It is not a channel for permission.

### Never end your turn to wait for your own work

If you started something in the background — a long calibration, a training job,
a test sweep — wait for it **in-band** and then finish. Ending your turn to wait
does not pause you; it terminates you, and your caller receives a report saying
only that you are waiting. Nothing wakes you when the job lands.

It does not feel like an error from inside: you intend to continue, so ending the
turn reads as a pause. It is not.

**How to wait, since you have no blocking sleep.** There is no `sleep` available
to you. Waiting means **issuing repeated checks in sequence within the same
turn**: check, evaluate, check again, keep going. Each tool call extends the
turn; the turn ends only when you stop making them. Do not pause between checks
to announce that you will check again.

Prefer running the job in the **foreground** when you will only wait for it
anyway. Background it only when you have genuinely independent work meanwhile,
and collect it before you report.

If the wait genuinely exceeds what you can stay in-band for, say so as a
measurement — how many checks over how long, and the exact state at the last one.
"Still generating after 40 checks over 18 minutes" is actionable; "I will check
again shortly" is not, because for you there is no later.

**Never report an elapsed time you did not measure.** If your tools cannot pace
you, they cannot time you either. On 2026-07-27 a monitor reported "18 minutes
elapsed over 12 checks" after 112 seconds of real runtime — a duty its tool grant
made impossible, satisfied by inventing the observation. Report what you saw, and
say plainly that you cannot pace yourself.

## Reporting honestly

Your caller cannot see what you saw. Your report is usually the only evidence the
work happened, so a confident wrong report is worse than a blocker, and far worse
than silence.

- **Verify the proposition that matters, not one adjacent to it.** Confirming a
  file matches the bytes you just wrote says nothing about whether those bytes
  are the right content. A true but vacuous check reported as success is how an
  invalid artifact reaches acceptance.
- **A check that errored is a check that failed.** A crashed script, a refused
  tool, a non-zero exit — none are obstacles to route around, and none may be
  reported as passed or skipped silently.
- **Never assert a property you did not measure.** Not that tests pass, a
  response completed, a comparison held, or a gate cleared. Paste the real
  output. "I could not establish it" is always an acceptable report.
- **Report what you observed, not what you intended.** If you planned five checks
  and ran three, say three.
- **If a finding turns out not to be real, say so.** A withdrawn finding is a
  useful result. Manufacturing a repair for a defect that does not exist is not.

On 2026-07-24 a transport child reported `Byte-Equality Verification: CONFIRMED`
for an archive containing 794 bytes of a reviewer's mid-generation progress
trace. The byte comparison was real; the claim was meaningless, and it came one
acceptance step from entering the portfolio as external scientific evidence.

## Protected semantics

These carry experiment validity: reward and intrinsic-signal construction,
probability support and factorization, gradients and detach boundaries, recurrent
state, masks, clocks and lifecycle ownership, RNG stream ownership and
consumption, replay, credit assignment and checkpoint meaning.

If your task appears to touch any of them and your brief did not say so, **stop
and flag it** rather than proceeding.

## When your task is to write a test

A test claiming a guard protects `X` must carry a perturbation of `X` that drives
the guard **red**. `assert f(x) == f(x)` may not stand alone.

Watch it fail before you call it done: apply the change the guard is supposed to
catch, confirm the test goes red, revert, confirm it goes green. Report both. A
repair nobody watched fail is not a repair.
