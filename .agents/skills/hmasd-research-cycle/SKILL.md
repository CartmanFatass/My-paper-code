---
name: hmasd-research-cycle
description: Use only when the user explicitly invokes $hmasd-research-cycle or docs/project/CURRENT_WORK.md records an ACTIVE Autonomous Boundary for one authorized autonomous HMASD iteration. Do not trigger for routine continuation, status or result reporting, interpretation of an already registered result, a valid result alone, or ordinary implementation work.
---

# HMASD Research Cycle

Confirm the entry condition before doing work. If neither an explicit invocation
nor an `ACTIVE` autonomous boundary exists, return control without starting a
cycle. Also require `docs/project/CURRENT_WORK.md` to point to one accepted
convergent-Pro disposition that fixes the scientific route and next evidence
source. If that pointer is absent, return `BLOCKED_MISSING_PRO_DISPOSITION` so
the controller can prepare an evidence boundary and message the External Review
Manager; do not design the route locally.

Read `docs/project/CURRENT_WORK.md`,
`docs/project/ALGORITHM_PRINCIPLES.md`, and the current contract in
`docs/project/IMPLEMENTATION_PLAN.md`. If this iteration changes executable
MARL code, dispatch it through `$hmasd-implementer`; if the controller must
implement directly after two failed attempts, it assumes that role for the
implementation turn.

## Run One Evidence-Bearing Iteration

1. Read the accepted convergent raw and disposition named by
   `docs/project/CURRENT_WORK.md`; do not reconstruct or re-rank the portfolio.
2. Translate the selected causal question, replacement ledger, comparator,
   outcome branches, and evidence source into the single active implementation
   plan without changing their scientific meaning.
3. Resolve only engineering details needed to make that frozen decision
   executable. A missing scientific choice returns to Pro rather than being
   filled by Codex.
4. Implement under the collaboration rules in `AGENTS.md`. Do not create a
   second brief, an internal reviewer, a task report, or a task commit.
5. Let the controller inspect the integrated path once. If a real experiment
   is authorized, launch it under `ExpRecord.md`, then assign its authoritative
   status path to the persistent monitor; implementation completion itself is
   not launch authority.
6. Apply the registered outcome branch to one accepted evidence source. If the
   result leaves a new algorithm, portfolio, or next-evidence decision open,
   stop and send the immutable evidence boundary to the External Review
   Manager; do not invent the successor.

Retry only a concrete operational failure under the same contract and its
registered `ExpRecord.md` retry limit. A valid scientific negative closes its
line without rescue.

## Stop

Stop after one accepted evidence source and return to the controller. Record the
result and autonomy state once in their owning files. Do not invoke this Skill
again from its own result. Another iteration requires a still-`ACTIVE` standing
boundary with remaining scope or a new explicit user instruction.
