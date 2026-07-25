# Proposal: drive the unattended loop with `/loop`

```text
status=ACCEPTED_AND_IN_FORCE
accepted=2026-07-24
accepted_by=user
date=2026-07-24
```

In force. The user accepted `/loop` as the fallback driver for the autonomous
workflow and started it. `AGENTS.md` carries the mechanism note under **Context
compaction**; `CURRENT_WORK.md` carries `loop_driver`.

## The problem, stated honestly

`AGENTS.md` says the loop continues automatically and never waits except at the
points the execution mode names. That is true of the *policy* and false of the
*mechanism*: a turn ends when the assistant stops emitting tool calls, and
nothing re-enters it. The constitution describes a driver that does not exist.

On 2026-07-24 I wrote "I will not come back for authorization" three separate
times and stopped anyway, each time waiting for a nudge. That is not a
discipline failure to be promised away — it is the same defect this session
catalogued elsewhere: **a rule written where nothing executes it.** The kit's
law 6 now states this directly and cites this episode.

## What `/loop` fixes, and what it does not

| | |
|---|---|
| **Fixes** | re-entry. The loop is re-invoked after each wakeup, so an unattended stretch advances without the user prompting. |
| **Does not fix** | correctness. It guarantees I come back, not that I come back right. Judgment errors still need the audits and gates. |
| **Does not survive** | session termination. `/loop` is session-bound. If the session dies overnight, the loop dies with it. |

The last row matters and I will not paper over it. True cross-session
autonomy would need `/schedule` (a cron cloud agent), and that is the wrong
tool here: the work needs the local conda environment, the local repository and
local CPU compute, none of which a cloud runner has. So the honest scope is
**"does not stall inside a live session"**, not "runs while the machine sleeps".

## Design

### Mode — dynamic, not fixed-interval

`/loop` with no interval, so I self-pace with `ScheduleWakeup`. Fixed intervals
are wrong here because loop stages differ by orders of magnitude: a derivation
is minutes, a bounded screen is tens of minutes, a formal run is hours. A fixed
5-minute tick would fire mid-work and invite duplicate starts; a fixed hourly
tick would idle after short stages.

### Delay policy per wakeup

Following the `ScheduleWakeup` guidance rather than inventing one:

| Situation | Delay | Why |
|---|---|---|
| a background subagent or run is in flight | 1200–1800 s | the harness notifies on completion, so this is only a fallback in case it hangs — polling is waste |
| waiting on the external reviewer's browser response | 300–600 s | not harness-tracked; matched to how fast that state actually changes |
| nothing specific pending, boundary just advanced | 60–300 s | there is real work to start; come back promptly |
| grant exhausted, user pause, or unrecoverable blocker | `stop: true` | the loop ends rather than idling |

### The prompt

Deliberately names no task, so it survives boundary changes and compaction:

```text
Continue the HMASD loop. Read docs/project/CURRENT_WORK.md for the active
boundary, then execute the next in-authority action per AGENTS.md.

Before starting anything: if a background subagent or run is still in flight,
do not begin duplicate work — reschedule and report what you are waiting on.

Stop the loop when iterations_remaining reaches 0, when a blocker needs the
user, or when user_pause is set.
```

### Exit conditions, encoded not remembered

- `iterations_remaining=0` → stop and produce the grant-renewal brief.
- `user_pause` set in `CURRENT_WORK.md` → stop.
- A blocker outside the standing grant → stop and report.
- Anything else → keep going.

## Expected effect, stated so it can be checked

1. No turn ends with an intention to continue and then waits.
2. Between user messages, the boundary in `CURRENT_WORK.md` advances on its own.
3. Every wakeup either advances one loop stage or reschedules **with a stated
   reason** — a silent wakeup that does nothing is a defect.
4. The user's messages become direction and review, not ignition.

Failure mode to watch: if wakeups fire and consistently do nothing but
reschedule, the loop is masking a blocker rather than working. That should be
reported, not absorbed.

## Risks

| Risk | Mitigation |
|---|---|
| duplicate work when a wakeup lands mid-flight | the prompt checks background tasks first and reschedules |
| runaway token spend | bounded by the grant; the loop stops at `iterations_remaining=0` |
| wasted wakeups polling harness-tracked work | long fallback delays only; completion arrives by notification |
| loop keeps running after the user wants to talk | wakeups are interruptible; a user message takes precedence |

## What changes if accepted

1. The user invokes `/loop` with the prompt above — I cannot start it for them.
2. `AGENTS.md` gains one paragraph under **Context compaction** stating that the
   loop's re-entry is driven by `/loop`, and that policy language about
   continuing automatically describes intent, not a mechanism.
3. `CURRENT_WORK.md` gains `loop_driver=user_invoked_dynamic_loop` and
   `loop_prompt_ref=docs/project/LOOP_DRIVER_PROPOSAL.md` so a successor knows
   whether a driver is attached.

Nothing else moves. No subagent definition, gate or test changes.
