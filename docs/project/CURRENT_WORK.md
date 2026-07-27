# HA-CTSE current work — attention pointer

Last updated: 2026-07-27

**This file points attention. It is not a journal and not an archive.** It
answers three questions and nothing else: what is live, what blocks it, and what
standing constraint would make a decision wrong.

Before adding a line, ask where it belongs:

| The thing you want to record | Where it goes |
|---|---|
| A finding, a measurement, a mechanism | an evidence note under `docs/research/cdc/EVIDENCE_NOTES/` |
| A rule for how work is done | `AGENTS.md` if it binds the orchestrator, the subagent's own definition if it binds a worker |
| A ruling and its reconciliation | the round directory under `docs/external-review/rounds/` |
| Which machine runs what | `docs/project/COMPUTE_ROUTING.md` |
| What is live *right now* | here |

It grew to 302 lines of `key=value` and started contradicting itself — naming a
closed round as awaiting answer, pointing at a superseded contract, naming an
older iteration report as the latest. A continuity record nobody can read is not
one. **When a line here stops being about the present, move it or delete it.**

## Live

```text
working_branch=untied-k
execution_mode=authorized
active_assignment_id=D7_S_EVENT_ALIGNED_SOURCE_AUDIT
next_boundary=PRO_ROUND_ON_THE_D7S_AUDIT_RESULT
workflow_position=result in hand and mechanically validated; step 8 Pro round is next
```

**The audit ran and returned a valid, non-affirmative result.** Run
`30289161086`, tag `d7s-audit-2`, stage commit `1b17dfb0`, 8/8 shards success in
one wave, none near the 355-minute self-stop. Artifacts and full reading:
`logs/d7s_audit_2_30289161086/` and
`docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_AUDIT_2_RESULT_AND_A_MISLABELLED_BRANCH.md`.

Mechanical validation clean: `smoke=False`, conformance ok, zero invalidated
pairs, zero topology-hash failures, `arm_distinct_ok`, support 8/8 on both
limbs, `all_seed_controlled=True`.

```text
b_stable_lcb  -0.077367      t_stable_ucb  +7.206993   t_stable_lcb  -2.189143
b_flex_lcb    -8.648833      t_flex_lcb   -14.293054   t_flex_ucb    +3.115871
recorded branch = SOURCE_NECESSITY_UNRESOLVED       part_a = NOT_APPLICABLE
```

### The recorded branch label is wrong, and that is the round's question

`assemble_audit_result` passes `primary_g_degenerate_flag=False` as a hardcoded
literal and never calls `primary_g_degenerate`, so branch 3
`PRIMARY_G_DEGENERATE` is unreachable. Evaluated post hoc with the instrument's
own functions on its own output, the flag is `True` and the branch would be
`PRIMARY_G_DEGENERATE`.

Nothing is inflated — both labels are non-affirmative — and the run is valid.
What changes is the next experiment: *unresolved* invites more replicates and
topologies; *degenerate* says B_m established no positive source-control
contrast at all, so more replicates would be a power rescue of a degenerate
design.

**This is External Pro's call, not this conversation's.** Wiring the flag is a
change to a result branch. The mapping from recorded bounds to
`b_m_positive_lcb` is Project Manager **inference** — there is no production
derivation, because the function is never called.

Do not write `docs/report/ITERATION_30.md` before that round rules. Step 8 is
Pro-decision-then-report, and 30 is the conclusion-bearing report.

### Guard state — what is now covered, and what is not

Ten unfailable guards were repaired on 2026-07-27 across the instrument and the
Scenario-7 environment; each was watched red under a mutation the Project
Manager ran itself. `tests/audit_d7_s_event_aligned_test.py` is **183 passed**,
`tests/scenario7_energy_aware_test.py` is **47 passed**.

Still open, and deliberately not repaired here:

- **`primary_g_degenerate`, `qos_component_saturated`, `expansion_allowed` are
  dead code.** The first makes a registered result branch unreachable — the
  round question above. The third means the §9 "one permissible expansion"
  predicate **is not enforced by any code**: expansion happens by a human
  passing `--topology-seeds`. The rule below reads as mechanized and is not.
- **Over half of `scripts/audit_d7_s_event_aligned.py` is unswept**, function by
  function, listed in
  `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_A_RESULT_BRANCH_THAT_CANNOT_FIRE.md`.
  Neither file may be read as audited.

### On a killed shard — the ruling's rule, which replaces ours

A topology is indivisible. Never pool a partial topology; preserve every
completed whole-topology shard; rerun the failed topology **whole at the same
stage commit and contract**; pool only once the seed union matches a frozen set.

### Two conditional re-review triggers

- Introducing **arbitrary user-controlled strings** into environment state — the
  encoder's string branch has no length prefix, tolerable only while no reachable
  string carries a structural delimiter (measured: 61 distinct, zero such).
- `observation_spaces`/`action_spaces` ceasing to be immutable configuration, or
  the audit ever calling `.sample()` on them.

### Open decisions that are the user's, not mine

- **Ownership of `untied-k`.** Another session committed `d3e0f72` asking that
  ownership be established before either continues. Unresolved.
- ~~The OS-entropy construction seed~~ — **ruled, and the answer is "not now."**
  The station-logistics reorder would change step-zero state and every
  trajectory. It is a **parked** environment correction; reactivate only if a
  future estimand reads graph-PBRS state, a conclusion-bearing path needs
  fresh-environment replay, a result must reproduce the whole event state from
  registered seeds, or the stale logistics are shown to alter event support,
  source-control actions or primary-`G` components.

### Cost — three hosted samples, and the ceiling worry mostly dissolves

```text
0.0864 s/step   run 30245735762   pre-rewrite commit
0.0923 s/step   run 30278575924   stage_commit
0.0784 s/step   run 30280427538   stage_commit + workflow-only diff
```

Spread ±9% around `0.0857`. The `0.0923 > 0.0864` step that looked like a cost
of the fingerprint rewrite is **runner variance** — the third sample is below
both. `|Z|=8` projects to 5.3–6.3 h against a 5.92 h self-stop.

**The question document quotes only the first two samples** and calls the
projection "straddling the ceiling", because the third landed after the fence.
It declines to attribute the difference, so the ruling stays usable; the
corrected band goes in the reconciliation.

`--workers 4` is now wired into the audit shard. The runner has **4 real cores**
(`nproc --all`, run `30280427538`; the `nproc=1` in the logs is coreutils
honouring `OMP_NUM_THREADS=1` and is not the core count). The pool worker runs
`_compute_audit_episode`, which calls `run_audit_event` for both limbs, so the
parallelism covers the dominant continuation cost rather than only the prefix.
Determinism proved byte-identical at run `30270540138`, on a descendant of the
fingerprint rewrite.

## Standing constraints

```text
branch_scope=untied-k only, never touch another branch (user ruling 2026-07-27)
aggressive_branch=another line's, never push
formal_compute=user authority only
review_transport=project_manager_direct
autonomous_research_grant=ACTIVE_TWENTY_ITERATION_OVERNIGHT_GRANT_20260726
overnight_session_grant=FULL_PERMISSION_TEN_ITERATIONS_20260727 (user, this session)
d7s_compute_authorization=GRANTED_20260727 (tag d7s-audit-2 pushed by this session under that grant)
iterations_remaining=17
conclusion_bearing_iterations_consumed=20
git_integration_status=project_manager_direct_authorized
intermediate_authorization_prompts=forbidden
experiment_orchestration=hmasd-experiment-operator only, never an ad hoc child
experiment_operator_fallback=forbidden
subagent_dispatch=user-granted 2026-07-27; before that the session prompt barred it
iteration_report_requirement=required_before_successor
workflow_hash_validation=disabled
uav_user_scope=transient_demand_coverage_plus_charging_roster_change_plus_temporary_detach_failure_robustness
uav_physical_fleet_boundary=fixed_slots_distinct_from_dynamic_service_roster
```

Formal and bounded runs use only the registered nonpersistent
`hmasd-experiment-operator`, fixed to `haiku` with `low` effort. It stays silent
and returns exactly one `COMPLETE` or `ERROR` terminal payload.

No Controller, persistent Monitor, dispatcher, callback route, global write
lease or compatibility line is active.

**Subagent dispatch was blocked by the session prompt, not by this repository.**
The roster, the routing in `CLAUDE.md` and every `.claude/agents/*.md`
registration were intact throughout; the binding constraint was one line in the
session system prompt — *do not call the AgentTool unless the user requested
it* — which by its own wording a single user sentence lifts. It was lifted on
2026-07-27. Recorded here because an unused dispatch table looks like a broken
one, and the next reader should not go looking for the wrong defect.

Iteration reports 1–29 are complete. 24 through 29 are all supporting work and
consume no conclusion-bearing quota; the next conclusion-bearing report is 30,
and it will be the audit result itself.
`conclusion_bearing_iterations_consumed` counts the **lifetime** total, not
consumption against the current grant — an exhausted-looking pair is not an
exhausted grant.

The workstation is shared with another research line. Check for foreign
processes before any local run and never touch them. Routing rules:
`docs/project/COMPUTE_ROUTING.md`.

## Accepted scientific state

- **D7.S contract frozen at R3** —
  `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT_R3.md`. Direct live event
  capture, complete-state fingerprint, conditions 1A/1B/1C, cross-limb
  conformance, episode-world provenance.
- **Estimand** — `U*_stable,src / B_H <= -0.10`, `U*_flex,src / B_H >= +0.10`.
  Agent-level; do not reframe to duty level.
- **Scenario-7 is a lossy-exchange source** (part A structural fact); the margin
  quantification awaits the audit.
- **The toy positive control is retired** (swap degeneracy); its retained lemma is
  in `AGENTS.md`.
- **Topology provenance rule** — reused results must prove shared topology or
  scope their claim (`AGENTS.md`, Result interpretation).
- **The ep64 diagnostic is retired as causal evidence.** Its former headline
  numbers must never be quoted; unpaired reanalysis is forbidden, because the
  user-world samples and their provenance do not exist.
- **No D7.S result has ever been published from this instrument**, so nothing is
  retracted by any defect found in it.

## Runtime and protected semantics

```text
python        = C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch         = 2.7.0+cpu
torch_threads = 1
backend       = cpu
```

No CUDA fallback, backend mixing, or cross-backend resume. Preserve every closed
source, result and first-match meaning.

```text
concurrency_policy         = file ownership only
same_file_concurrent_writes = forbidden
disjoint_file_parallelism   = allowed
```

## Where things live

| | |
|---|---|
| Project Manager instructions — authority, the loop, Stage A/B, acceptance, task sizing, dispatch, review | `AGENTS.md` |
| Standing context every subagent reads | `docs/project/AGENT_CONTEXT.md` |
| Which machine runs what | `docs/project/COMPUTE_ROUTING.md` |
| Scientific method contract | `docs/project/ALGORITHM_PRINCIPLES.md` |
| Cost ceilings and violation semantics | `docs/project/EVIDENCE_COMPLEXITY_POLICY.md` |
| What the paper is about, and the standing check | `docs/project/RESEARCH_GOAL.md` |
| Findings and measurements | `docs/research/cdc/EVIDENCE_NOTES/` |
| Review rounds, questions, rulings, reconciliations | `docs/external-review/rounds/` |
| Closed generations G2–G16 | `docs/research/cdc/CLOSED_GENERATION_BOUNDARY_ARCHIVE_G2_G16.md` |
| Latest Chinese iteration report | `docs/report/ITERATION_29.md` |

Closed generations G17–G20R, UAV G1/G2, the contract-grill mechanism and the D7
part-B margin-instrument era are retired; their evidence notes and round
directories remain under the paths above.
