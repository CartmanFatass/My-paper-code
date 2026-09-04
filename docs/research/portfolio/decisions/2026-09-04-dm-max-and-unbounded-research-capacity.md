# DM max reasoning and unbounded research capacity

Date: 2026-09-04

Decision: `FINAL / OWNER_DIRECT / ROOT_INTEGRATED`

## Provenance

- Owner instruction in the active Root session, 2026-09-04 02:06 PDT: change the Direction
  Manager to `gpt-5.6-sol` with `max` reasoning effort and remove the research-capacity limit.
- This is a direct Portfolio-tier capacity decision. No local or Pro model substitutes for it.

## Decisions

1. The native `hmasd-direction-manager` definition uses model `gpt-5.6-sol` with
   `model_reasoning_effort = "max"`.
2. The repository no longer caps concurrent implementer sessions or concurrent result-bearing
   runs. Root and the DMs may advance every independent, admitted direction that the runtime and
   machine can safely support.

## Unchanged constraints

- `max_concurrent_threads_per_session = 40` remains a runtime fan-out setting, not a research
  capacity policy.
- Every result-bearing invocation still requires a fresh memory admission with both physical and
  effective available memory at least 4 GiB.
- Science-card budgets, per-arm cost projections, machine-time caps, dependency ownership,
  worktree isolation, the decision ladder, and the evidence-class requirements remain binding.
- Historical handoffs, reviews, and earlier capacity decisions remain unchanged as evidence of the
  policy that applied at their dates.

## Transition

Direction Manager turns already running at `high` effort when this instruction arrived are stopped
at their current clean file state. Continued DM work is dispatched at `gpt-5.6-sol` / `max`.
