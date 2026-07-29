# HA-CTSE current work — attention pointer

Last updated: 2026-07-29

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
next_boundary=PICK UP HERE. Loop 13 of a 10-loop goal; loops 11 and 12 are closed. THE BIG ONE: STEP H RETURNED AND IS INVALID. Run 30403322062 finished 2026-07-29T00:14:58Z, 8/8 shards, mechanically clean -- but at head a00612ad, which does NOT contain the source-assignment repair 23fecff3, so every episode ran on the arm-specific double-assignment defect. Branch PART_A_CONTRADICTION, stable AFFIRMATIVE_NONMATERIAL, flex UNRESOLVED; that JSON stays immutable. Charging fires 49 times across the population, so "the mechanism never ran" does NOT rescue it. ROUND 4 THEREFORE NEEDS THE R4 MEASUREMENT RE-RUN at a commit containing 23fecff3, same frozen population 20260734..20260741, no pooling across that boundary -- CONCLUSION-BEARING, SO USER AUTHORITY, ASK BEFORE LAUNCHING. Note 20260729_H_RETURNED_AND_CANNOT_CLOSE_ROUND_4.md. OBLIGATIONS A, B AND C ARE ALL NOW GREEN WITH REAL POWER: A rerun and passing with A3 rescued (2180 injective / 1820 non-injective, power guard refuses unless both classes occur); B has a LEAVE/REJOIN power guard as of ad083ade and measures 560/560 full-derangement feasibility over 5600 steps with 19 LEAVE and 15 REJOIN -- at the old 400-step default it is 0/0 events and returns OBLIGATION_B_INCONCLUSIVE, which is a SECOND independent reason the retired 1200/1200 is worthless; C needs NO revision, it runs clean at 120/120 same-support with all five mutations caught and unconstructible=0 -- and that zero on "non-eligible incumbent moved" is independent confirmation the repair killed double-holding, because that bucket only ever filled when two duties shared one holder. NEXT: resume D-F, then the re-run decision. ONE INSTRUMENT GAP, worth closing inside the re-run change: the R4 artifact records leaves and charging but NO rejoin field and no injectivity-check counter, which is why H's disposition had to be argued from the commit graph instead of from the measurement. ENVIRONMENT IS FASTER AND THE NATIVE PATH IS PROVEN: the generic-SHORT toy env is 1.59x (2839 -> 4526 steps/s) with its caller-visible bytes unchanged, pinned by tests/dynamic_roster_testbed_equivalence_test.py at digest 50f7385f...0445e7; the UAV geometry kernel is adopted at ha_ctse_process/uav_cpp_backend.py and is BITWISE EXACT against scenario_base (312/312 elements, max_ulp 0, tests/uav_cpp_backend_oracle_test.py) -- an oracle its own design doc had only ever described in the future tense. NOT INTEGRATED YET, deliberately: no production path calls it. Measured payoff when it is wired into _update_channel_state -- path loss is 17.5% of a 0.0937 s/step scenario7 step, but the CACHE machinery around it is another 24%, so one native call per step retires both. THREE GENERIC TRAPS, ALL LIVE: (a) a rate is evidence only if the triggering event fired -- count occurrences or exit INCONCLUSIVE; (b) hand-rolled mutations miss silently, use .claude/skills/hmasd-acceptance-gate/scripts/paired_negative.py which reads the mutation back off disk; (c) a refusal is CONCLUSIVE and must dominate a power guard, and its counters must increment before anything that can raise.
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
D' conformance repair                   DONE  28d6933f -- R1-R5, 309 passed
E proof-sized exercise on 20260725      DONE  13 outcomes, STEP_E_ASSEMBLED_PATH_OK
F Stage B re-review of D'                REJECT -- conformance and semantics, two blocking
F' repair D''                            DONE  0193de1a -- 291 passed, 8 paired negatives
G Stage B review of D''                  APPROVE -- conformance and semantics
G' hardening D''' (NB-1 and guard shapes) DONE  928b6e68 + a00612ad, 264+32 passed
H formal R4 measurement                  RETURNED -- INVALID, ran pre-repair
```

**H returned, 8/8 shards, and it still cannot close round 4.** Run
`30403322062` finished 2026-07-29T00:14:58Z at head `a00612ad`; the
source-assignment repair is `23fecff3` and is NOT an ancestor of it. Every
episode was rolled by the `constructive_mixed` whose REJOIN branch can
double-assign, in exactly one of the two arms `D_A` contrasts.

It is mechanically clean otherwise -- `smoke=False`, 8/8 support both limbs,
conformance ok, zero invalidated pairs, `all_seed_controlled`, and it is the
first whole-population artifact to pass `r4_freshness_sentinel`, which the
pooler now runs as a hard gate. Branch `PART_A_CONTRADICTION`; stable
`AFFIRMATIVE_NONMATERIAL`, flex `UNRESOLVED`. That JSON stays immutable.

The "the mechanism never fired" escape does not apply: charging occurs 49 times
across the population inside the registered horizon. What is NOT established is
that a double assignment actually occurred -- the artifact records leaves and
charging but **no rejoin field**, so it cannot answer that about itself, which is
why the disposition rests on the commit graph. Full reading:
`docs/research/cdc/EVIDENCE_NOTES/20260729_H_RETURNED_AND_CANNOT_CLOSE_ROUND_4.md`.

Closing round 4 needs the R4 measurement re-run at a commit containing
`23fecff3`, same frozen population, no pooling across that boundary. That is
conclusion-bearing compute and therefore **user authority**.

**Step F existed because the gate was skipped, not because it was scheduled.**
`COMPUTE_ROUTING.md`: "A conclusion-bearing run needs its gate passed first —
Stage B for claim-bearing code." Step D *was* that gate and it returned REJECT;
D' repaired it and the PM verified the repair personally, but nothing
adversarial ever read the repair. D' → E skipped it. Both defects below were in
the tree while `CURRENT_WORK` said A–E COMPLETE.

**The two blocking defects, reproduced by the PM rather than taken on report:**

```text
B-1  a DUPLICATED topology seed inside a declared shard produces a nine-slot
     "eight-topology" artifact that PASSES all five sentinel conditions.
     measured: r4_declared_population_identity([...734, 734, 735, 736, 737])
       -> EARNED; resolve_run_plan returns it verbatim, NOT deduplicated;
       pooled artifact topology_seeds=8 / topology_records=9;
       r4_freshness_sentinel -> ok=True, all five True.
     One topology carries double weight in topology_weighted_point_estimate.
     THIS SHAPE IS NEW WITH D'. r4_artifact_identity's exact-list check refuses
     the same list (measured: None). The declared path D' added to fix the
     sharding provenance gap admits a shape the old path refused -- an artifact
     carrying a PASSING proof of a population it does not have.

B-2  main() never calls r4_freshness_sentinel, and the no-flag default IS a
     whole-population R4 run.
     measured: resolve_run_plan(no flags) -> TOPOLOGY_SEEDS_R4 at 8/8 episodes,
       identity EARNED; 'r4_freshness_sentinel' occurs once inside main() and
       it is IN A COMMENT (:4722) asserting the check runs. Section 3's "fail
       closed unless" has no executable closure on the lowest-effort route.
     Also: --population r4 with the eight seeds REVERSED earns identity and
       would fail the sentinel (exact_seed_list=False) if anything ran it.
```

**The path-proof that protects the run itself, measured after D''.** The new
`main()` sentinel gate is the one change that could have made the formal run
produce nothing: if it fired on a shard, all eight jobs would refuse.

```text
--population r4 --topology-seeds 20260734   identity EARNED   gate fires=False
--population r4 --topology-seeds 20260735   identity EARNED   gate fires=False
--population r4 --topology-seeds 20260741   identity EARNED   gate fires=False
all eight, one process, no flags                              gate fires=True
all eight declared REVERSED                                   gate fires=True
                                              -> then exact_seed_list refuses
```

Shards keep identity and are not put through a whole-population gate they
cannot satisfy; both whole-population routes are gated. That is exactly the
intended shape, and it is the CI matrix's exact invocation.

**One correction the PM did NOT adopt from the review.** Its minimal fix for B-1
re-points sentinel condition 1 at `topology_records`. A topology failing the
pinned-coordinate hash contributes no record and no unit (`:4744-4750` appends
to `topology_hash_failures` and continues), so that would turn a lawful
`INVALID_EVENT_ALIGNED_AUDIT` run into a pooler `SystemExit` instead of a
reportable branch-1 result. Condition 1 stays on the declared list; a separate
subset-and-distinct condition closes the hole without touching branch 1.

**Three implementation bindings the Project Manager decided in D'/D'', owed to
Pro as disclosure at the next touchpoint — none reopens a frozen decision:**

```text
the length gate compares against the registered horizon h (139/550), NOT
  window_series_length(h). That function's own docstring pins h+1 as the LATCH
  series convention; window_g_from_step_metrics builds the QoS series with
  n = min(len(step_metrics), h). The repair spec named the wrong constant, and
  implementing it literally would have failed EVERY conforming record, making
  PRIMARY_G_DEGENERATE structurally unreachable while `complete` stayed True.
  Contract section 4's own words are "at the registered horizon".

R4 identity is DECLARED (--population r4), not inferred from the seed list. A
  strict subset is admitted so the sharded route can carry identity; any seed
  outside the population is a hard refusal; an accidental subset still gets
  None/None.

the freshness sentinel gains an EIGHTH artifact-level condition beyond the
  contract's registered seven: the seeds that actually produced units are
  pairwise distinct and all members of the population. Contract conditions 1-7
  are NOT renumbered. This is D'''s repair of B-1 and it exists because the
  declared path (binding 2 above) made a duplicate reachable with identity --
  a binding whose own failure mode needed a second binding to close.
```

**Provenance rule created by D', and it binds any future run.** With
`--population r4` the `run_contract_id` becomes the R4 namespace, which changes
every derived seed for that process. **A shard produced before `28d6933f` and one
produced after are not the same measurement**, so existing shard artifacts must
never be pooled with new ones.

`window_series_length` is now dead production code and was already dead at the
commit the review ran against — referenced by docstrings and its own unit test,
consulted by no production path. That is the constant the repair spec picked up
as authoritative. A convention documented in a docstring and exercised only by
its own test is exactly what the next reader mistakes for the governing rule.

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

## Control plane — what now enforces itself (2026-07-28)

Prompted by finding a rule that had never been executable: the compaction Skill's
cadence depended on `iterations_since_last_compaction`, a key `CURRENT_WORK.md`
had never carried in any revision. Read on many turns, followed on none.

```text
check_control_plane.py    referents exist: routed agents/skills, backticked paths,
                          retired names, and check H -- a document naming a state
                          key its named file does not contain. In pre-commit.
check_test_reality.py     what the SUITE executed: STUB_ONLY (patched everywhere,
                          invoked nowhere), ENTRY_UNRUN, DEAD_PROD. Gate-time only.
paired_negative.py        one mutation, read back off disk, restored; an ERROR is
                          reported INCONCLUSIVE, never as a red test.
archive_pro_response.ps1  the round capture rediscovered by hand five times.
new_review_round.ps1      round scaffold; refuses if the resolved root has no AGENTS.md.
launch_and_watch_run.ps1  preflight + status. Does NOT launch -- see below.
pretooluse_guard.ps1      --no-verify, push-before-tag, branch scope. NEEDS the
                          user to create .claude/settings.json before it binds.
```

Guards that could not fail, now able to: the drift guard's path set excluded
`.githooks/` and `.claude/settings*.json`, so a commit neutering the guard ran no
contract; the review-round rejection probe asserted only `status` over a fixture
illegal in two ways; the subagent tier check accepted any non-blank `model:`; the
no-Git hook covered 2 of 6 shell-holding children and its test named them instead
of discovering them.

**No script can detach a run here.** `Start-Process` and `nohup` from the
PowerShell tool both leave a child dead within seconds; only a backgrounded Bash
call survives. That is the cause of both 2026-07-27 orphans, and it is why the
launcher hands back a command rather than running it.

Five errors in this tooling were caught by its own tests before anything was
trusted: an omitted `tools` key read as a defect, a false `ENTRY_UNRUN` from
importlib binding, a false negative from the `pytest.main` footer, stdout
existence read as output, and a scaffolder writing outside the repository while
reporting success.

## Standing constraints

```text
active_pm_session=bab4b1f6-1b57-4eca-bebe-ed516b15ff65 (claimed 2026-07-29 at a53e8b30; the prior session declared HANDOFF and its boundary is behind HEAD)
branch_scope=untied-k only, never touch another branch (user ruling 2026-07-27)
aggressive_branch=another line's, never push
formal_compute=user authority only
review_transport=project_manager_direct
autonomous_research_grant=ACTIVE_TWENTY_ITERATION_OVERNIGHT_GRANT_20260726
overnight_session_grant=FULL_PERMISSION_TEN_ITERATIONS_20260727 (user, this session)
workflow_round_grant=FULL_PERMISSION_TEN_WORKFLOW_ROUNDS_20260727B (user, this session, granted after the ten-iteration grant above was consumed)
iteration_definition=one complete Pro-to-Pro loop (user ruling 2026-07-27): receive Pro's ruling, make the code decisions, implement, run the experiment, submit the result back to Pro. Nothing smaller is an iteration.
d7s_compute_authorization=GRANTED_20260727 (tag d7s-audit-2 pushed under the earlier grant; formal compute for the ten rounds above is covered by workflow_round_grant)
r5_reanchor_compute_grant=GRANTED_20260728 (user, "launch it anyway", given in advance of Pro's ruling). Covers the full formal run a re-anchored successor contract requires -- including a fresh topology population -- with no cost preview and no check-back before launch. It removes the AUTHORIZATION gate only. It does not authorize launching before Pro's ruling names the branch, and it does not authorize running an unregistered contract: a margin re-anchor is pre-registered first, always, because the same edit after a result is observed is a rescue and not a repair.
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

### The source-assignment defect — what is settled, not what happened

Moved here out of `next_boundary` on 2026-07-29, because these are accepted
state rather than news. The reasoning behind each is in its round directory.

- **`duty_map` is a PARTIAL INJECTION** from executable duties to physical UAVs.
  A UAV may hold at most one executable duty, because the controller emits
  exactly one physical action per UAV and obtains it by inverting the map. A
  non-injective map is an internally inconsistent controller state, not a
  legitimate multi-duty one.
- **A phantom duty is UNCOVERED.** A map key is an assignment claim only;
  coverage requires an executable, action-bearing incumbent (`m_raw` / `m_exec`
  / `C = dom(m_exec)`).
- **The defect is arm-specific.** `constructive_mixed`'s REJOIN branch can
  double-assign; `full_sync_set_update` is injective by construction. It is
  present in exactly one of the two arms `D_A` contrasts. Measured at 33% of
  check boundaries on the development topology, all 8 episodes.
- **Both halves of the timing are true, at different boundaries.** At the STEP
  boundary the duplication is persistent after onset — that bounds the
  contamination. At the PHASE boundary the LEAVE re-match repairs it and the
  REJOIN phase re-creates it — that locates the repair.
- **R4's artifact is `INVALID_R4_REALIZATION:
  DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`.** The JSON stays immutable and
  `PART_A_CONTRADICTION` is not rewritten; it is citable ONLY as a descriptive
  external-return observation of the historical code paths.
- **Obligation A is reopened at A1-A4** with its solver and Hall-witness lemmas
  RETAINED. A3 is **rescuable, not to be replaced** — it follows once the domain
  becomes the injective executable assignment relation.
- **Obligation B's 1200/1200 is RETIRED** as feasibility evidence: it was
  computed through the lossy inversion and must be repeated on corrected
  trajectories, which may themselves change.
- **Obligation C was never closed** and needs an injectivity / executable-
  coverage precondition.
- **The defect does NOT reach results only through flown actions** — a claim of
  mine that Pro falsified. `_stable_candidates_at` iterates raw `(d, u)` pairs so
  a double-holding UAV appears twice as a stable-certification candidate, and
  `_flex_survivors_at` keys by UAV so its two entries collapse to one. Both are
  fixed by injectivity itself, so neither needs a separate change.

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
