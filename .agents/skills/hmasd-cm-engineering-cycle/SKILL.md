---
name: hmasd-cm-engineering-cycle
description: Coordinate one bounded HMASD engineering scope from frozen scientific authority.
---

# HMASD CM Engineering Cycle

Own one CM-<direction-id> identity and generation for one bounded assignment.
Reconcile authority refs, engineering state, worktree, base SHA, owned paths,
and effect refs before acting.

1. Map interfaces and decompose only into disjoint owned paths. Use
   responsibility-relevant genuine direct leaves when useful; every child is a
   leaf.
2. Give implementers frozen goal, non-goals, authority refs, interfaces, and
   exact paths. A material scope change creates new bounded work.
3. Delegate each real result command to exactly one Experiment Operator under
   `hmasd-result-run`.
4. Write CM engineering state through the existing CLI. Direction-owned work
   may modify, test, commit, and push when its assignment authorizes it.
   The path tier policy only classifies/records; it never replaces
   `allowed_paths` or creates an approval service. Root enforces the one user
   confirmation bound to an exact shared-core action.
5. Publish exact candidate/result authority refs through an immutable Work
   Packet and stop. Same-`work_id` delivery is at-least-once and idempotent;
   unchanged authority refs do not create a new packet. Root mechanically
   integrates candidates and does not edit conflicts.

Refuse stale/conflicted worktrees, CAS conflicts, and out-of-scope paths.
Unknown effects are observed, never repeated; local failure does not block other
directions.
