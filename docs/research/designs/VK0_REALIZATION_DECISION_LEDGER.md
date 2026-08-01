# V-K0 realization — Project Manager decision ledger

Status: **complete code design for touchpoint 2 conformance.** Implements the
V-K0 ruling (round `20260801_variable_k_algorithm_direction`). Every binding
is an implementation decision; the two places where the ruling's text
underdetermines the realization are FLAGGED for the conformance check. Zero
experiments run at design time. Code anchors are from the scout map at
`c20ee143`, PM spot-checked.

## VK-D1 — V-K0A drives the real environment, no reimplementation

`TwoTimescaleRoleFreeActionsEnv` is exactly deterministic given
`reset(seed)` and actions, owns no external handles, and is deepcopy-safe
(scout, full read). The oracle constructs the real env; the four initial
sign combinations are obtained by scanning reset seeds `0,1,2,...` until all
four `(slow_sign, fast_sign)` combinations appear, recording the
seed→combination map in the panel artifact (no private-attribute writes).
The five-step window return for a joint skill pair is computed by
deep-copying the env at the check and stepping five times with
`FixedSkillPrimitivePolicy.action_table` actions (`standalone_agent.py:341`,
imported as a pure table; no agent stack, no checkpoint, no learned policy).
Window = 5 primitive steps = exactly one check interval, so "no inner high
check" holds structurally; asserted anyway from step counts.

## VK-D2 — FLAGGED: panel incumbents follow the oracle-optimal edit sequence

`U_src` at a check depends on the incumbent pair (KEEP means keep the
incumbent; SET support excludes it). The ruling's 112-row panel (4 signs × 2
permutations × 7 noninitial checks × 2 focals) does not enumerate
incumbents, and its initial check "is recorded but excluded" because no
incumbent exists. Binding: the panel's incumbents at check t are those
reached by the joint-return-maximizing legal edit sequence from the initial
assignment onward (the oracle plays optimally between checks), with a
deterministic tie-break: lexicographically smallest `(z_agent0, z_agent1)`.
Every row records the incumbent pair and whether a tie occurred.
**Interpretation flagged for the conformance check** — the alternative
(enumerating all incumbent pairs) multiplies the panel beyond the ruled 112
rows.

## VK-D3 — FLAGGED: snapshot semantics realized by from-reset byte-exact replay

The ruling orders counterfactual families to "begin from one immutable
snapshot" listing env, controller, hidden and RNG state. No mid-episode
snapshot/restore machinery exists; the codebase's one replay precedent
(`ToyAuditHost.rollout`, `scripts/audit_d7_2b_toy_positive_control.py:169-288`)
realizes exactly this semantics by **from-reset replay**: reseed
(`env.reset(seed)`, `torch.manual_seed`, `np.random.seed`), re-execute the
identical prefix, verify admissibility byte-for-byte (`_prefix_matches`
compares every prefix action array and step reward; `_focal_state_matches`
compares incumbents at the check), drop-and-count any mismatched pair, and
reseed the continuation stream (`post_seed`) after the forced check so
branches share base draws. Binding: V-K0B uses this proven pattern — the
"snapshot" is `(episode_seed, policy_seed, prefix token record)` and
"restore" is verified re-execution — rather than a new snapshot subsystem.
The toy episode is 40 steps, so the replay overhead is negligible, and no
new apparatus is built (the algorithm-first ruling's own economy).
**Flagged for the conformance check as realizing, not weakening, the
snapshot list**: every listed component is either re-derived bit-identically
(env state, skills, ages, mask, steps_to_check, RNG streams — all seeded) or
structurally absent in this config (low-level hidden state: feedforward,
never written; high controller per-check MLP holds no cross-check state —
scout-verified).

## VK-D4 — RNG and parallelism

Branches within one evaluation run execute serially in one process (the
global `torch`/`numpy` seed pattern of the precedent is kept; parallel
branches would race the process-global generators). The six training runs
execute as separate processes, sequentially by default. No new generator
plumbing.

## VK-D5 — reversed roster: an optional `agent_order` parameter

`agent_order` is hardcoded ascending at the single call site
(`standalone_agent.py:4084`). `maybe_assign_skills` and
`_r30_maybe_assign_skills` gain an optional `agent_order=None` keyword
(None → `torch.arange`, exactly today's behavior); the evaluation driver
passes the reversed order for the reversed bank. The three pinned forced-token
tests must stay green unmodified; one new focused test covers reversed-order
propagation. Training never passes the parameter.

## VK-D6 — trace schema frozen verbatim from the ruling

`renewal_check_trace.jsonl` and `renewal_counterfactual_units.jsonl` carry
exactly the ruling's field lists (transcribed into the implementation as a
schema constant with a `trace_schema_version`), plus
`source_oracle_panel.json`, `train_and_checkpoint_manifest.json`, and
`summary.json` recomputable solely from the row files. Segment-ending
authority enumerates: voluntary_set, initial_assignment,
episode_termination, active_mask_change, team_intent_boundary,
forced_renewal. The analyzer is a separate module developed against this
frozen schema.

## VK-D7 — namespace and seeds

New constant `VK0_CONTRACT_ID = "VK0_TOY_RENEWAL_URGENCY"`. The evaluation
episode seed bank (64 per training seed, one frozen common bank), the
counterfactual select/evaluate streams (disjoint by phase and replicate
index), and the bootstrap seed derive via SHA-256 from
`(VK0_CONTRACT_ID, purpose, indices)` — mirroring the audit script's
`stream_seed` pattern. Training seeds are the ruled literals
2026080101–2026080106. Nothing is derived from checkpoint contents.

## VK-D8 — training and artifacts

Six runs of `python -m ha_ctse_process.train --config
config_d7_2b_toy_learned_keep` with per-run overrides limited to: the
training seed and `output_root` (one directory per seed under
`logs/vk0b/<seed>/`). Config file untouched. Final checkpoint only
(`latest.pt` at completion); `train_and_checkpoint_manifest.json` records
actual exposure (environment interactions, check counts, optimizer steps,
aborted batches) read from the run's own metadata plus the trace driver's
recount; a deviation is invalid, never rescaled.

## VK-D9 — analyzer and result system

New `scripts/analyze_vk0_result.py`: consumes the row files only;
seed-first nested bootstrap (resample training seeds, then episodes within
seeds; 10,000 iterations; one frozen derived seed); equal seed weighting;
one-sided 95% bounds at the ±0.5 materiality boundary; two one-sided
equivalence tests for the STABLE window; the eight-row first-match result
system verbatim; WRONG_DIRECTION only on a UCB at/below the boundary.
Boundary rows (`U_src = 0.5` exactly) retained in artifacts, excluded from
binary comparisons.

## VK-D10 — drivers

`scripts/audit_vk0a_source_urgency_oracle.py` (V-K0A: panel, validity
checks mapped one-to-one to the ruling's eight INVALID conditions,
acceptance mapped to the five structural-pattern conditions, verdict) and
`scripts/audit_vk0b_r30_access.py` (V-K0B: checkpoint loading via
`process_train.load_checkpoint`, forced-token families
KEEP / SET(named z) / SET(sampled) via the existing
`maybe_assign_skills(..., forced_tokens=...)` surface, from-reset paired
replay per VK-D3, support/competence floors, trace emission). V-K0B refuses
to run unless the V-K0A verdict artifact says IDENTIFIED.

## Cost (informational)

V-K0A: ≤ 112 rows × ≤ 16 joint edits × 5 steps ≈ 9k env steps of a trivial
env — seconds; no training. V-K0B training: 6 × 640k toy steps (existing
config's own shape); a ≤20-minute single-seed microbenchmark establishes
the rate before the six launches; evaluation ≈ 6 × (64 episodes × 40 steps
+ ~896 rows × ~6 branches × ≤45 replay steps) — minutes. All local;
`check_compute_free.ps1` gates timing.

## Deliberately not done

- No constrained renewal-class mechanism, no V-K1 shared-period arms, no
  UAV work, no credit instrumentation (ruling's NOT SELECTED list).
- No mid-episode snapshot subsystem (VK-D3).
- No change to training-time behavior of the forced-token surface; the
  three pinned tests stay authoritative.
- No primitive-step training trace (ruling correction 3).
