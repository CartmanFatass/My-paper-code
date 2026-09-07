# Shared Portfolio/Root dispatch skill — 2026-09-07

OWNER_DIRECT: after the concurrency correction, the owner asked whether Portfolio/Root
documents or a skill should be adjusted to stabilize both sessions' behavior. This change
consolidates that already-authorized workflow; it changes no model, scientific decision tier,
lifecycle, priority, execution budget or external-effect authority.

## Observed failure before this change

Root's actual native inventory contained only the VSPC1 chain despite available runtime
capacity. DISH and CBSC intakes had not reached active DMs; UCOPE's pre-launch staging stop
remained uncontinued. Portfolio had handled successive VSPC1 receipts without refilling the
whole working set. Root also cited an old DISH implementation return despite the later B06
E0 at33db0d860, and carried an old staging stop into an explicitly authorized continuation.

The owner-directed refill produced four actual advancing chains, recorded at42a6683a4.
The first documentation correction was integrated at7fcb87ace. These are observed baseline
failures and the live correction's evidence, not a claim that native runtime capacity was one.

## Maintained entry points

- `.agents/skills/hmasd-loop-dispatch/SKILL.md`: one role-specific operating procedure for
  whole-working-set planning, five-item handoffs, batch dispatch, current-state receipts,
  vacancies, recipient recovery and scoped continuations.
- `.agents/skills/hmasd-portfolio-task/SKILL.md`: keeps scientific Portfolio judgment and
  delegates dispatch procedure to the shared skill; its duplicate procedure is removed.
- `docs/project/ROOT_OPERATIONS.md`: keeps role boundaries, endpoints and observation rules,
  with direct shared-skill entry links, including for sessions with an older skill catalog.
- `AGENTS.md`: directs both Portfolio and Root to that shared procedure on the relevant events.

No new polling service, registry, scheduler, role or recurring task is introduced. Existing
research assignments continue during this documentation work. A packet or an empty native queue
does not create new experiment authority or authorize a duplicate provider request.

## Focused validation

Both skill frontmatters passed the existing skill-creator `quick_validate.py`. The changed
document links resolve, and `git diff --check` passed. Existing model/compute/automation
configuration and DM/CM role files are not edited.

An independent reused reviewer applied the new skill to five bounded, read-only scenarios:

1. Portfolio receives one packet while three other directions have actionable returns.
2. Root receives three independent commands, one preparation-only and one unavailable target
   with an explicit same-role replacement route.
3. New staging-repair authority supersedes an old stop, followed by unknown launch acceptance.
4. A first arm admits a preselected second arm while another direction yields for a decision.
5. All native work ends with two Pro waits and no justified fifth task.

The responses dispatched independent work before waiting, preserved actual current counts,
kept unknown acceptance from becoming a duplicate launch, executed prewritten dependencies
without another approval exchange, and retained external waits without invented work. No
material contradiction or routing loss was found. A completed packet was correctly excluded
from the active count even when a stale inventory still called its DM active.

These are application exercises, not five fresh runtime executions or a guarantee of future
compliance. The subsequent live receipt remains the operational check: exact current recipients,
advancing count, original evidence and named next events. No scientific experiment or provider
action was performed for skill validation.
