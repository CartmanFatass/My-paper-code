# V-K0 realization design conformance check

Touchpoint 2 of workflow 5. One question only: **does the completed code
design in `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md` conform
to the V-K0 ruling you issued in round
`20260801_variable_k_algorithm_direction`?** No alternative is argued; zero
experiments have run. Discarding this question's structure is a legitimate
answer.

## Variable-k relevance

This design realizes the ruled V-K0 package — the first experiment whose
outcome is a statement about variable k on this branch.

## Frozen inputs (not review surface)

- The V-K0 ruling itself; the user's algorithm-first course ruling; the R30
  carrier and goal statement.
- Code anchors were scout-mapped at this round's `stage_commit` and
  PM-spot-checked: the toy env is exactly deterministic given `reset(seed)`
  and actions with no external handles; local observations are constant
  zero; the four-skill executor is the policy-side zero-parameter
  `FixedSkillPrimitivePolicy.action_table`
  (`ha_ctse_process/standalone_agent.py:341`); the forced-token surface
  draws the KEEP uniform and skill categorical before forcing
  (`ha_ctse_process/r30_fixed_clock.py:398-421`); the only replay precedent
  is from-reset byte-verified replay
  (`scripts/audit_d7_2b_toy_positive_control.py:169-288`, `:611-635`); the
  low-level path in this config is feedforward and stateless; `agent_order`
  is hardcoded ascending at the single call site
  (`ha_ctse_process/standalone_agent.py:4084`).

## The design, in one paragraph (full detail in the ledger)

VK-D1 drives the real env in the oracle (seed-scan for the four sign
combinations, deepcopy at the check, five table-action steps). VK-D5
threads an optional `agent_order=None` parameter through
`maybe_assign_skills` for the reversed bank (training never passes it; the
three pinned forced-token tests stay authoritative). VK-D6 freezes the two
JSONL schemas verbatim from your ruling with a `trace_schema_version`.
VK-D7 derives every evaluation/counterfactual/bootstrap seed from a new
frozen namespace `VK0_TOY_RENEWAL_URGENCY`; training seeds are your six
literals. VK-D8 launches six otherwise-untouched
`config_d7_2b_toy_learned_keep` trainings differing only in seed and output
directory, final checkpoint only, actual-exposure recording without
rescaling. VK-D9 implements the seed-first nested bootstrap (10,000
iterations, one frozen seed) and your eight-row first-match result system.
VK-D10 splits drivers: a training-free V-K0A oracle script whose validity
and acceptance checks map one-to-one to your eight INVALID and five
acceptance conditions, and a V-K0B screen that refuses to run without an
IDENTIFIED verdict artifact.

## Points where the design interprets the ruling (flagged for the check)

1. **VK-D2 — panel incumbents.** `U_src` at a check depends on the
   incumbent pair, which your 112-row panel does not enumerate. The design
   binds: incumbents at check t are those reached by the
   joint-return-maximizing legal edit sequence from the initial assignment
   (the oracle plays optimally between checks), deterministic tie-break to
   the lexicographically smallest pair, every row recording the incumbent
   pair and tie occurrence. If you intended a different incumbent
   definition (for example exhaustive enumeration over incumbent pairs,
   which multiplies the panel), say so.
2. **VK-D3 — snapshot semantics realized by from-reset replay.** Your
   ruling lists an immutable snapshot's components. No mid-episode
   snapshot machinery exists; the design realizes the semantics with the
   proven from-reset pattern: reseed, re-execute the identical prefix,
   verify admissibility byte-for-byte (every prefix action array, step
   reward, and check incumbents), drop-and-count mismatches, reseed the
   continuation stream after the forced check so branches share base
   draws. Every listed snapshot component is either re-derived
   bit-identically or structurally absent in this config (stateless
   low-level, per-check MLP with no cross-check state). The alternative —
   building a new snapshot subsystem — adds apparatus your course context
   argues against. If from-reset realization is not acceptable, say so.
3. **VK-D4 — serial branches, global RNG pattern kept.** Branch families
   execute serially in one process; the six trainings are separate
   processes. No per-branch generator plumbing is added.

## Required response sections

1. `CONFORMANCE` — CONFORMS, or the exact ledger items that deviate.
2. `INTERPRETATIONS` — accept/correct each of the three flagged readings.
3. `CONVERGENCE_DECISION` — your closing decision for this touchpoint.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/VK0_REALIZATION_DECISION_LEDGER.md`
- `docs/external-review/rounds/20260801_variable_k_algorithm_direction/21_PRO_OPEN_RAW.md`
- `envs/pettingzoo/two_timescale_role_free_actions.py`
- `config_d7_2b_toy_learned_keep.py`
- `ha_ctse_process/r30_fixed_clock.py`
- `ha_ctse_process/standalone_agent.py`
- `scripts/audit_d7_2b_toy_positive_control.py`
