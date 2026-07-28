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
active_assignment_id=D7_S_R4_ABSOLUTE_FOCAL_MARGIN
next_boundary=R4_CLOSURE step D' (conformance repair of four blocking defects, in flight) then re-review, then E. No run.
workflow_position=workflow 3 CLOSED; complete R4 contract frozen at docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
```

An iteration **is** one whole Pro-to-Pro loop. The three-access rule that
governs it lives in `AGENTS.md`, **Convergence belongs to touchpoint 2** — not
restated here, because a second copy of a rule is what made this file start
contradicting itself before.

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

### R4 is COMPLETELY frozen -- read the _COMPLETE file, not the partial one

`docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`.
The earlier `D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md` is the **partial** freeze and is
immutable; it left expansion and population undecided while its own header
claimed they were frozen. Do not quote it.

```text
expansion         = NONE
topology seeds    = 20260734..20260741   (repurposed, NOT inherited via R3 expansion)
episodes          = 8 Part-A control + 8 focal audit, per topology
n_select/n_eval   = 2 / 2
R3 data pooling   = forbidden
```

**Fresh means fresh at the highest inferential unit.** New episodes under the
eight R3 topologies are fresh *conditional* observations, not new draws from
`P_T` -- topology is the top-level bootstrap unit. Such a run is retainable only
as `R4_ORIGINAL_PANEL_CONDITIONAL_REPLICATION`, never pooled or substituted.

**R3 support does not pre-pass R4 support.** The new topologies must
independently satisfy minimum support before any focal margin is read; on failure
`SOURCE_EVENT_SUPPORT_INSUFFICIENT` fires with no substitution and no expansion.

**Guard closure is a PM-owned premise, not an adjudicated fact.** The sweep and
pooler claims were not reviewed -- the evidence fence did not carry the tests or
the mutation notes. Check them at the realization gate.

### An ambiguity in the freeze ruling, and how it was read

The R4 contract-completion ruling ends *"This review authorizes neither
implementation nor compute"*, while its own NEXT_ACTION lists **C. Implement the
smallest R4 delta** and **E. Run a proof-sized assembled-path exercise**. Read
literally those conflict.

**Resolved in favour of proceeding with A-E**, on the strength of E's closing
sentence: *"Only after those close may the fixed R4 run return to the project's
separate conclusion-bearing compute-authorization path."* That sentence only
makes sense if A-E are the authorized work and the closing guard is on the
**formal R4 measurement**. Under the opposite reading the ruling would name a
next action nobody may perform, and the closure sequence could never begin.

This is a Project Manager reading of an ambiguous ruling, not a ruling. It is
recorded here rather than buried in a commit message so it can be challenged. If
it is wrong, the wrong thing is the R4 result-layer implementation, which is
uncommitted-to-a-run and reversible; no compute was spent on it.

### R4 closure progress

```text
A supersede the partial freeze          DONE  D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
B decision ledger, nine bindings        DONE  D7_S_R4_DECISION_LEDGER.md
C implement the smallest R4 delta       DONE  3de74552 + 7fa90070
D realization-conformance review        REJECT -- 6 of 10 clean, four blocking
D' conformance repair                   IN FLIGHT -- R1-R5, hmasd-implementer
E proof-sized exercise on 20260725      blocked on D'
```

**Step D returned REJECT.** Four blocking defects, all re-verified by the Project
Manager rather than taken on the child's report:

```text
B1  the sharded production route earns no R4 identity, and r4_freshness_sentinel
    is called by NO production code -- contract section 3's "fail closed" has no
    executable closure
B2  --episodes-* overrides survive on the formal path: a conclusion-bearing R4
    artifact at 2 episodes per topology instead of the frozen 8
B3  the completeness gate is `if not pairwise` -- a truncated audit reads as
    exactly invariant and routes to PRIMARY_G_DEGENERATE
B4  section 7 precedence inverted: support is checked before missing-audit, so an
    instrument failure is reported as a population failure
```

Full evidence:
`docs/research/cdc/EVIDENCE_NOTES/20260728_D7_S_R4_THE_PLANNED_PRODUCTION_ROUTE_CANNOT_PROVE_IT_IS_R4.md`.

All four are the code failing to do what the **already-frozen** contract says, so
they are conformance repairs under Project Manager authority — no Pro round. The
one item that does cross is `NOT_EVALUATED`, a fifth per-limb state outside the
frozen four-state vocabulary; it joins the list owed to Pro at the next
touchpoint.

**The 249 green tests proved less than they appeared to.** `main()` is invoked by
no test in either suite, and `compute_u_star_bootstrap` appears only as the
`monkeypatch.setattr` that replaces it — so the invariant that matters (an
artifact emitted by the route the formal run actually uses satisfies the
sentinel) was never asserted. Do not read that count as instrument validation.

The R4 instrument exists: absolute five-unit gates, four per-limb states, the
nine-row combined mapping, five-level precedence, branch 3 over focal pairs, the
`20260734-20260741` population with its own seed namespace, a six-condition
freshness sentinel, `PART_A_CONTROL` at the absolute anchor, and the null arm and
both `B_m` quantities deleted from the run path. **249 passed** across the three
suites.

Two carried items for the realization gate, neither of them silent:

- **Pro's launch-gate list named "calibration arm ordering"** as a precondition,
  and R4 satisfies it by **deleting** calibration arm ordering rather than
  guarding it. Satisfied by removal -- check it, do not assume it.
- **`NOT_EVALUATED`** is a fifth per-limb state outside the contract's frozen
  four, emitted only when the focal audit is incomplete (a case already routed to
  branch 1). An implementation binding, disclosed to Pro at the next touchpoint
  rather than left as a detail.
- **`PART_A_FULL_SYNC_MATERIALLY_WORSE`** is a label the contract does not name.

### The road here, in pointers

Each of these is fully recorded in its round directory and its evidence note.
They are pointers because a narrative copy here drifts and this file has been
deleted once for exactly that.

| What happened | Where |
|---|---|
| D7.S audit run 2 returned a valid non-affirmative result | `logs/d7s_audit_2_30289161086/`, note `20260727_D7_S_AUDIT_2_RESULT_AND_A_MISLABELLED_BRANCH.md` |
| Ruled `PRIMARY_G_DEGENERATE`; the measurement route closed, not the research question | round `20260727_d7_s_audit_2_result_disposition` |
| The global normalizer retired for this claim; N5 comparator-scale mismatch raised | round `20260728_d7_s_autopsy_result`, `logs/d7s_autopsy_2/` |
| R4 derived at a five-unit absolute focal margin, ruled derivable | round `20260728_r4_materiality_derivation` |
| The partial R4 freeze, left immutable | `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md` |

**Say "relevance not demonstrated", never "unrelated".** The stronger reading
was this conversation's inference and Pro rejected it.

**Two errors of mine not to repeat.** The ratio/linear divergence was **not** an
R3 design defect -- the contract registers the *linear* gate plus the separate
`LCB95(B_m) > 0` requirement, and that requirement is what keeps the linear form
inside the domain where it equals the ratio. And `U* = V_SET - V_KEEP`, so
**`U*_stable = -3` means SET is WORSE than KEEP**, which is why it points toward
stable persistence.

### Guard state — the launch gate is closed

All seven areas Pro made a precondition on any future environment run now carry
paired negatives, each watched failing: `window_g_from_step_metrics`, baseline
masks, calibration arm ordering, audit-limb assignment, seed-controlled
provenance, qualifying-event construction, and clone conditions 2/3/5. The
pooler's reconstruction whitelist followed.

```text
tests/audit_d7_s_event_aligned_test.py        215 passed   (from 183)
tests/pool_d7_s_event_aligned_shards_test.py   21 passed   (from 15)
tests/d7s_normalizer_autopsy_test.py           12 passed
tests/scenario7_energy_aware_test.py           47 passed
```

**Production code was never changed to close any of these — every one was a
missing test.**

The event-admission surface was swept separately and came back **sound**: 31
independent mutations across `check_leave_eligibility`, `certify_stable`,
`certify_flex`, `legal_set_targets`, the transit helpers,
`arm_distinctness_check` and `compute_conformance_ok` all drove red, including
both operands of every compound condition. That matters most for R4, because a
defect there changes *which events are measured* rather than perturbing a value.
Note `20260728_D7_S_THE_EVENT_ADMISSION_SURFACE_IS_SOUND.md`.

Known and deliberately not repaired: two rejection-map entries and eleven of
fourteen `build_event_conformance_record` fields are unguarded but reach
diagnostics only; `select_joint_event` and `focal_eligible_to_act` are dead in
production — tested, never called.

**Closure is a PM-owned premise, not an adjudicated fact.** Pro declined to rule
on it because the evidence fence did not carry the tests or the mutation notes.
Check it at the realization gate.
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

**None outstanding.** Branch ownership of `untied-k` is settled by direction;
formal-run authorization is covered by `workflow_round_grant`; and the
OS-entropy construction seed is ruled **parked** — reactivate the
station-logistics reorder only if a future estimand reads graph-PBRS state, a
conclusion-bearing path needs fresh-environment replay, a result must reproduce
the whole event state from registered seeds, or the stale logistics are shown to
alter event support, source-control actions or primary-`G` components.

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
active_pm_session=27b7458a-a8c3-4f67-a1bb-011d18759db1 (claimed 2026-07-28; CLAUDE.md Ownership names this key)
branch_scope=untied-k only, never touch another branch (user ruling 2026-07-27)
aggressive_branch=another line's, never push
formal_compute=user authority only
review_transport=project_manager_direct
autonomous_research_grant=ACTIVE_TWENTY_ITERATION_OVERNIGHT_GRANT_20260726
overnight_session_grant=FULL_PERMISSION_TEN_ITERATIONS_20260727 (user, this session)
workflow_round_grant=FULL_PERMISSION_TEN_WORKFLOW_ROUNDS_20260727B (user, this session, granted after the ten-iteration grant above was consumed)
iteration_definition=one complete Pro-to-Pro loop (user ruling 2026-07-27): receive Pro's ruling, make the code decisions, implement, run the experiment, submit the result back to Pro. Nothing smaller is an iteration.
d7s_compute_authorization=GRANTED_20260727 (tag d7s-audit-2 pushed under the earlier grant; formal compute for the ten rounds above is covered by workflow_round_grant)
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

**A counting error, corrected 2026-07-27.** A session reported "ten iterations
complete" for the span after the last Pro ruling landed at `343b757d`. Measured:
23 commits, all guard sweeps, repairs, the audit run and its recording, with
**zero Pro rounds** among them. Under `iteration_definition` above that span is
**one** iteration, and it did not close until the result round was fenced at
`76c1ce32`. The reports numbered 24–29 are the same confusion under another
name — already labelled supporting work, but numbered as though they were
iterations. Do not report a count of work cycles as a count of iterations.

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
