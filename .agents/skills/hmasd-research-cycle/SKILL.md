---
name: hmasd-research-cycle
description: Use only when the user explicitly invokes $hmasd-research-cycle or docs/project/CURRENT_WORK.md records an ACTIVE Autonomous Boundary for one authorized autonomous HMASD iteration. Do not trigger for routine continuation, status or result reporting, interpretation of an already registered result, a valid result alone, or ordinary implementation work.
---

# HMASD Research Cycle

Confirm the entry condition before doing work. If neither an explicit invocation
nor an `ACTIVE` autonomous boundary exists, return control without starting a
cycle. Also require `docs/project/CURRENT_WORK.md` to point to one accepted
convergent-Pro disposition that fixes the scientific route and next evidence
source. If that pointer is absent, enter `$hmasd-review-round` or return
`BLOCKED_MISSING_PRO_DISPOSITION`; do not design the route locally.

Read `docs/project/CURRENT_WORK.md`,
`docs/project/ALGORITHM_PRINCIPLES.md`, and the current contract in
`docs/project/IMPLEMENTATION_PLAN.md`. Read
`docs/project/MARL_ENGINEERING_PRINCIPLES.md` only if this iteration changes or
reviews executable MARL code.

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
   lifecycle is required, enter `$hmasd-experiment`; implementation completion
   itself is not launch authority.
6. Apply the registered outcome branch to one accepted evidence source. If the
   result leaves a new algorithm, portfolio, or next-evidence decision open,
   stop and enter `$hmasd-review-round`; do not invent the successor.

Retry only a concrete operational failure under the same contract and within
the experiment protocol's retry limit. A valid scientific negative closes its
line without rescue.

## Stop

Stop after one accepted evidence source and return to the controller. Record the
result and autonomy state once in their owning files. Do not invoke this Skill
again from its own result. Another iteration requires a still-`ACTIVE` standing
boundary with remaining scope or a new explicit user instruction.
