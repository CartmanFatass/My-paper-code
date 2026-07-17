# Canonical HMASD Brief Template

Create one copy at `.codex/collaboration/active/<task-id>/BRIEF.md`. Keep it
short enough for every implementer and reviewer to read completely.

```markdown
# <Task> Brief

## Authority and Outcome
- User authorization:
- Single outcome:
- Observable completion:
- Explicitly unauthorized:

## Causal Question and Relevant History
- Active question or engineering objective:
- Necessary accepted facts:
- Competing explanations, when scientific:
- Evidence that separates them:

## Contracts and Invariants
- Owning project contracts:
- Probability, clock, reward, gradient, mask and checkpoint invariants:
- Dirty-worktree boundary:

## Work Packages
| Package | Owner | Goal | Exclusive write scope | Dependency | Frozen interface |
| --- | --- | --- | --- | --- | --- |

## Non-goals and Prohibitions
-

## Focused Evidence
- Check:
- Required observation:

## Completion and Stop Conditions
- COMPLETE when:
- BLOCKED when:
```

Information priority is current user instruction, then this brief, then current
repository contracts, then inherited context. Amend the same brief when the
controller changes scope; never create a second task plan.
