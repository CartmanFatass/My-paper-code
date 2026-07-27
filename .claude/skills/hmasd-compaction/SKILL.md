---
name: hmasd-compaction
description: Use at an iteration seam when context is running short — the handoff, the cadence, and the fixed sequence that keeps the loop alive across the boundary.
---

# Compaction and the handoff seam

Project Manager only. Load this at an iteration seam, never mid-iteration.

## Context compaction

Compaction is a **context boundary, not a control boundary**. It exists so the
loop survives losing its context, not so a human can inspect it. It never
pauses the loop, never ends the work, and is never a checkpoint — the only
points where the loop waits for the user are the ones the execution mode names.

**Re-entry is driven by the attached driver, not by this document.** A turn ends
when the orchestrator stops emitting tool calls, and no policy sentence
re-invokes it — the language here about continuing automatically states *intent*;
the driver supplies the *mechanism*. See **The loop does not stop** above for
which driver and why. Without one attached the loop stalls between delegations,
in the gap where nothing is in flight and the next step is the orchestrator's to
start; that is where it stalled repeatedly on 2026-07-24 despite this section
already saying it would not.

Event notifications from background children are the primary driver and cover
most of the loop; the driver's wakeup is the fallback for the gap they cannot
cover. It is session-bound and does not survive session death —
`CURRENT_WORK.md` does, which is why the boundary, not the driver, is the
continuity record. `CURRENT_WORK.md` records whether a driver is attached.

It happens at one place: the seam between iterations, once the current one has
closed out. Never mid-iteration.

**Cadence: every second iteration seam, not every one.** Compacting at every
seam throws away the live reasoning of an iteration that has only just closed,
so the next one restarts colder than it needs to. Carrying one full iteration
across the seam makes the handoff smoother, because the successor inherits the
thinking behind the boundary and not only the boundary.

The count must survive the thing it governs, so `CURRENT_WORK.md` carries
`iterations_since_last_compaction`. Increment it when an iteration closes; reset
it to `0` immediately after compacting. Without that key the cadence is
unexecutable across the very boundary it describes.

Context pressure overrides the cadence **downward, never upward**. If the window
runs short before the second seam, compact at the first seam available rather
than pushing on degraded — and never defer a compaction the context actually
needs in order to hit the cadence. The cadence is a default, not a quota.

The handoff is written as step 1 of the sequence below, so it too lands every
second seam. That is safe: `CURRENT_WORK.md` is updated every iteration and is
the real continuity record, so a handoff one iteration behind still resumes
correctly.

The sequence is fixed and ordered:

1. write the handoff to `docs/project/RESTART_HANDOFF.md` — active boundary,
   execution mode, what is committed and pushed, the one open deliverable, and
   the exact next action;
2. compact;
3. resume from the handoff and **continue straight into the next iteration**.

Step 3 is automatic in both modes. Nothing is asked here and nothing waits for
an answer; an unauthorized-mode loop still crosses this seam on its own and
pauses only at that mode's two checkpoints.

A handoff written mid-iteration is a snapshot of an unfinished thought, not a
resume point. If context runs short first, finish the smallest step that makes
the state describable, then follow the sequence — do not compact in the middle
and do not carry an undescribed state across.

The handoff is the seam and nothing more. Everything else a successor needs is
already in `CURRENT_WORK.md`, `ExpRecord.md`, `docs/research/cdc/` and Git.

