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
active_assignment_id=D7_S_NORMALIZER_IDENTIFIABILITY_AUTOPSY
next_boundary=R4_CLOSURE -- ledger, smallest delta, realization-conformance review, proof-sized exercise. No run.
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

### Ruled: the run is `PRIMARY_G_DEGENERATE`, and this measurement route closes

Round `20260727_d7_s_audit_2_result_disposition`, stage commit `76c1ce32`,
ruling archived at that round's `21_PRO_OPEN_RAW.md`.

The recorded branch `SOURCE_NECESSITY_UNRESOLVED` is **mislabelled**; the
frozen-contract disposition is branch 3 `PRIMARY_G_DEGENERATE`. Not
`INVALID_EVENT_ALIGNED_AUDIT` — the run stays valid and quantitatively usable.
Leave the historical JSON byte-unchanged and attach the disposition; do not
rerun to rewrite a string.

Pro's durable conclusion: *"D7.S R3 produced a valid matched observation but an
unidentifiable materiality scale. The result closes this measurement route, not
the heterogeneous-renewal research question."*

Smallest retired unit: the **signed** `B_m = G(constructive_mixed) − G(null)`
as an *identified positive materiality scale* on this frozen route. Primary `G`
is retained under question; the S7-S3 source-necessity proposition is
**unjudged**. `D7.3` and `D8` stay blocked.

**Expansion is inadmissible** and this does not depend on the label: §9 forbids
expansion on a wrong-direction point, and both `T_m` points have the wrong sign
(`T_stable = +1.272` where it must be negative, `T_flex = -4.551` where it must
be positive). Do not add topologies `20260734–20260741`, do not add replicates,
and do not use the positive `B_m` points to bypass their non-positive bounds.

Technical closure owed, and explicitly *not* the next scientific action: wire
branch 3 **disjunctively** across limbs (`b_stable_lcb > 0 OR b_flex_lcb > 0`,
with per-limb `stable_b_identified` / `flex_b_identified` recorded separately and
a failed limb labelled `NORMALIZER_NOT_IDENTIFIED`); record point estimates in
the artifact, which today carries only the six bounds; and enforce §9 in
`main()`.

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

### Superseded: the partial R4 freeze

`docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md`, authority
`rounds/20260728_r4_materiality_derivation/21_PRO_OPEN_RAW.md`.

```text
stable clears  iff  UCB95(U*_stable) < -5.0
flex clears    iff  LCB95(U*_flex)   > +5.0
```

No denominator. Five is the smallest nonzero coefficient on a discrete
task-semantic safety event in the frozen objective, fixed from the weights alone.
**It is not mathematically unique** — Pro said so, and it must not be inherited as
forced.

**Two corrections this conversation must not repeat.** The ratio/linear
divergence I reported was **not** an R3 design defect: the contract registers the
*linear* gate plus the separate `LCB95(B_m) > 0` requirement, and that
requirement is what keeps the linear form inside the domain where it equals the
ratio; a negative-`B` run terminates before the contrast is interpreted. And
`U* = V_SET − V_KEEP`, so **`U*_stable = −3` means SET is WORSE than KEEP** —
which is why it points toward stable persistence.

**Branch 3's pair set changed.** Under R4 it is the focal `(KEEP, SET(z))`
evaluation pairs, **not** the R3 calibration pair — that aggregation rule was
R3-specific because it tied component separation to the normalizer source
controls, and R4 has no normalizer.

**Open before any R4 run:** the expansion rule (freeze one, or freeze no
expansion — R3's is void) and a fresh evidence population. **The R3 artifact may
not be rethresholded at ±5 and reported as an R4 result.**

### Superseded: the global normalizer is retired for this claim

Round `20260728_d7_s_autopsy_result`, stage commit `6430ef96`.

> The completed artifact provides no positive evidence that the global
> `constructive_mixed − null` contrast is a useful scale for the focal one-Δ
> SET-versus-KEEP effect.

Status `GLOBAL_ROTATION_NORMALIZER_RELEVANCE_NOT_DEMONSTRATED`. **Say "relevance
not demonstrated", never "unrelated"** — that stronger reading was this
conversation's inference and Pro rejected it: the association intervals span
strong relationships in both directions and the leave-one-out estimates are
unstable.

**Selected next action, zero compute:** derive and pre-freeze an R4 absolute
task-unit materiality criterion (or the positive pre-treatment scale as live
alternative), construct its zero-denominator and sign counterexamples, freeze
its branch semantics, and decide whether it is scientifically meaningful
**before any implementation or environment run**. S7-S3 carrier retirement is
the conditional fallback. Topology stratification is **not selected**; higher
selection volume is parked. `D7.3` and `D8` remain blocked.

**Standing constraint from this ruling:** a future measurement may not use a
global source-control contrast to scale a focal renewal effect merely because
both are measured in `G`. It must use an arm-independent task scale, or
establish analytically **before data** that the normalizer is commensurate with
the focal one-Δ intervention.

**The aggregation blocker is closed.** `components_separate_m` is the
disjunction of not-exactly-equal over the complete **calibration** source-control
pairs; no fraction threshold is permitted; completeness is load-bearing and a
missing record leaves the run fail-closed. Wire it as part of the **R4**
instrument closure — do **not** rerun R3 merely because branches 4–10 become
reachable.

### The launch gate is closed

All seven guard areas Pro made a precondition on any future environment run now
have paired negatives, watched failing: `window_g_from_step_metrics`, baseline
masks, calibration arm ordering, audit-limb assignment, seed-controlled
provenance, qualifying-event construction, and clone conditions 2/3/5. The suite
went 203 → 215. Production code was not changed; these were purely missing tests.

The widest of them: no test had ever driven the real event-selection algorithm
to a qualifying event. That positive case now exists.

### The autopsy's first evidence matrix is partly superseded

`logs/d7s_autopsy_1/` ran with three classifier defects Pro then found. **The N1
row is discarded outright**; N4's "material" was overstated; N2's vocabulary was
too conjunctive. All three are repaired and `logs/d7s_autopsy_2/` is the
corrected run. The sentinel result, the four standalone distributions and the R4
decision are unaffected — the ruling says so explicitly.

Quote the corrected run, and the reconciliation at
`docs/external-review/rounds/20260728_d7_s_autopsy_result/30_PM_SCIENTIFIC_RECONCILIATION.md`.

### The converged next action, and a precondition it set

Round `20260727_d7_s_normalizer_autopsy_plan`, stage commit `f1d79b17`:
**APPROVED WITH MODIFICATIONS**. The artifact-only autopsy runs locally against
the byte-unchanged artifact; *"no environment compute is selected by this
ruling."* Six modifications, of which the load-bearing ones are a **fail-closed
input sentinel** that must reproduce all six frozen R3 bounds before any
statistic is emitted, and **N5 — comparator-scale mismatch**, an explanation this
conversation had missed: `B_m` measures global proactive rotation versus none
while `U*_m` measures a focal one-Δ reassignment, so the normalizer can be
measured correctly and still be the wrong scale.

`N3 = UNDISCRIMINATED_FROM_STORED_ARTIFACT` — the artifact holds no component
data, and Pro rejected reconstructing it.

**A hard precondition on any future environment run.** Before one may launch, the
guard gaps in `window_g_from_step_metrics`, baseline masks, calibration arm
ordering, audit-limb assignment, seed-controlled provenance, qualifying-event
construction, and clone conditions 2/3/5 **must** be closed with paired negatives
or another independent conformance mechanism. This is a gate, not a backlog item.

**The wording of the last result was downgraded by Pro itself.** The run is no
longer "a valid matched observation" but *"a provenance-recorded, CRN-paired,
executed-code observation that remains admissible for diagnostic reanalysis, but
is not independently validated at every conclusion-bearing transformation."*
Quote that form, not the earlier one.

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
- **The back half has now been swept, and the primary result path has almost no
  guards** —
  `docs/research/cdc/EVIDENCE_NOTES/20260727_D7_S_THE_INSTRUMENT_BACK_HALF_SWEEP.md`.
  Verified by the Project Manager personally, each at 183 passed: `B_stable`'s
  sign can be flipped at its production fold, `all_seed_controlled` can be
  hardcoded `True`, and the entire qualifying-event construction branch can be
  made unreachable. **No test drives event selection through to a real
  qualifying event.**

  This does not make the recorded result wrong — the production code is correct
  and the run executed it. It makes "mechanical validation clean" weaker evidence
  than it reads, which matters because the ruling leaned on it. Carried to the
  next plan review, not to a follow-up Pro turn.

- **The clone conditions and the `G` accumulator are the worst of it.** Region B
  returned: three of the five R2 blocking conditions — 2, 3 and 5 — can each be
  replaced by `if False:` at 183 passed, and reachability probes prove all three
  execute on every clone. That is what "zero invalidated pairs" is made of.
  `window_g_from_step_metrics` and `_baseline_masks`, which produce every
  `g_total` in the run, have **no test at all**: 22 of 22 mutations green,
  including halving the total, which the Project Manager verified personally.

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

- ~~**Ownership of `untied-k`**~~ — **settled by direction 2026-07-27.** The user
  granted this session ten workflow rounds with full permission on this branch,
  which is an instruction to drive it. `d3e0f72` from another session asked that
  ownership be established; it now is. Recorded rather than assumed silently.
- ~~Authorization for a further formal run~~ — covered by `workflow_round_grant`
  above for the ten rounds it names. The next action is artifact-only anyway and
  needs no environment compute.
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
