# The frozen replicate volume cannot pay its compute bill: necessity, reduction, or downscope

One decision, pre-walked. This round carries no verification work — the
instrument is accepted (152 focused tests, conformance derivation committed)
and nothing here reopens the event definition, horizons, thresholds, seeds or
branch system you froze on 2026-07-26.

## What happened

The joint audit you ordered was launched today at the frozen volume
(8 topologies x [8 calibration + 8 audit] episodes, n_select=4, n_eval=8) as
8 topology shards, and was **closed by the user before completion**: the
measured cost projection was 2-4 days wall clock on the registered 16-core
CPU machine. Concurrently the user installed a hard cost policy
(`docs/project/EVIDENCE_COMPLEXITY_POLICY.md`): a formal conclusion-bearing
iteration must project to at most **8 hours** wall at the intended sharding
width; a violation is `NON_EXECUTABLE_EVIDENCE_DESIGN`, the Project Manager
must prefer the cheapest bounded realization that preserves the scientific
predicate, and where no bounded realization can, **you** decide the
scientific necessity or the retirement of the predicate. That is this round.

## Measured cost model (provenance stated, no confirmation requested)

- Environment step rate, single core, registered CPU env: **0.10-0.30 s/step**
  (ep64 record: ~25 min per 6-arm x 1500-step episode ~= 0.17 s/step; the
  event-aligned smoke runs bracket it on both sides).
- Fork cost: one replicate = prefix replay (up to t_e <= 950 steps) + one
  continuation (H_flex 550 + guard), i.e. up to ~1,500 steps ~= **2.5-7.5 min**.
- Forks per qualifying joint event at the frozen volume:
  `2 limbs x (n_eval KEEP + |legal set| x (n_select + n_eval))` =
  `2 x (8 + |Z| x 12)`. At the smoke-observed legal-set sizes (|Z| ~ 3-8)
  that is **88-208 forks per event**, one event per qualifying episode.
- Whole-audit projection: 64 audit episodes x (4-26 h each) + 64 calibration
  episodes -> **hundreds of CPU-hours; 19-56+ h wall at 8-way sharding**.
  Over the 8 h cap by roughly **2.5x-7x at minimum**.

The 8 h cap admits approximately: shared-prefix realization (one replay per
event, continuations forked from a cloned state) **plus** smoke-scale
replicates (n_select=1, n_eval=2), which lands near 6-8 h wall at 8-way
sharding. Either lever alone does not fit.

## Q1 - the decision (first-match, walk the branch you rule)

**(a) Volume reduction.** Rule the minimal (n_select, n_eval) under which the
Section-8 inference (shared-stream hierarchical bootstrap, 10,000 iterations,
one-sided 95%, T_m materiality bounds, equal topology weighting) remains
valid and worth running. If n_select=1/n_eval=2 is acceptable, rule it and
state any interpretation consequence (wider intervals are understood and
accepted; the question is validity and decision-worthiness, not comfort). If
that floor is too low, name the floor - and note that any floor above
n_select=1/n_eval=4 does not fit the cap even with (b), which forces branch
(c) or (d).

**(b) Realization: shared prefix replay.** One evaluator-certified prefix
replay per event; all replicates fork continuations from a snapshot of the
post-replay state, each fork receiving its own registered continuation RNG
stream exactly as now (stream_seed hash unchanged; only the mechanical
re-walking of an identical certified prefix is deduplicated). Confirm this
preserves the frozen evaluator-certified-history and CRN semantics, or name
the property it breaks. This is a realization ruling, not a new design; if
confirmed, the PM implements it and Stage B (code-science alignment diff)
runs on the diff before any launch.

**(c) The frozen volume is scientifically indispensable.** Say so explicitly.
Consequence under the policy: the joint audit does not run on this machine;
it waits for a user-named exception or different compute. D7.3 and D8 remain
blocked; the paper claim rests meanwhile on part A (structural lossy
exchange) plus the ep64 single-topology diagnostic, scoped as such.

**(d) Downscope the claim.** If the joint audit's marginal evidence over
part A + the ep64 diagnostic does not justify its cost at any admissible
volume, rule the downscope: state the smallest claim the existing evidence
supports and what, if anything, replaces the audit on the critical path
toward the `RESEARCH_GOAL.md` thesis.

## Q2 - only if (a) and/or (b)

The frozen contract text must change (Section 8 constants and/or a
realization note). Confirm the amendment is ruled in this same round and the
contract refreezes on your answer - no separate freeze round.

## Evidence to read

- `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md`
- `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`
- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/project/RESEARCH_GOAL.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `scripts/audit_d7_s_event_aligned.py`
- `scripts/pool_d7_s_event_aligned_shards.py`
- `docs/research/cdc/EVIDENCE_NOTES/20260726_D7_S_EVENT_ALIGNED_CONFORMANCE_DERIVATION.md`
- `docs/report/ITERATION_24.md`
