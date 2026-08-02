# HA-CTSE current work — attention pointer

Last updated: 2026-08-01

**This file points attention. It is not a journal and not an archive.** It
answers three questions and nothing else: what is live, what blocks it, and what
standing constraint would make a decision wrong.

Before adding a line, ask where it belongs:

| The thing you want to record | Where it goes |
|---|---|
| A finding, a measurement, a mechanism | an evidence note under `docs/research/cdc/EVIDENCE_NOTES/` |
| A rule for how work is done | `AGENTS.md` if it binds the orchestrator, the subagent's own definition if it binds a worker |
| A ruling and its reconciliation | the round directory under `docs/external-review/rounds/` |
| What is live *right now* | here |

It has twice grown into a contradicting journal and been cut back; a second
copy of anything is how that happens. **When a line here stops being about the
present, move it or delete it.**

## Live

```text
working_branch=untied-k
execution_mode=authorized
active_assignment_id=D7_S_R4_ABSOLUTE_FOCAL_MARGIN
next_boundary=Workflow 6 OPEN, inheriting the disposition of round 20260801_vk0_result_disposition as its first touchpoint. V-K0A STANDS (first valid positive variable-k statement); V-K0B is INVALID_VARIABLE_K_URGENCY_AUDIT / REQUIRED_TRAINING_EXPOSURE_NOT_AUDITABLE (row-4 output historical only; diagnostic OBSERVED_AR_SERIALIZATION_ORDER_COMPETENCE_ASYMMETRY retained, canonical 0.996/0.993 vs reversed 0.440/0.596 LCB95, no access-failure label licensed). ORDERED NEXT: (1) artifact-only exposure recovery audit over logs/vk0b/2026080101..106 -- all fields recoverable -> corrected immutable exposure manifest + analyzer rerun only; any unrecoverable -> instrument counters + IDENTICAL-contract V-K0B rerun (ruled permitted); trace fixes first (target vectors; segment_ending_authority = ending authority). (2) If a valid analysis lands row 4 again: V-K0C order-transport localization (no training). V-K1 and constrained mechanism blocked; R30 live. D7.S/B3-L stays HELD.
workflow_position=workflow 5 CLOSED (V-K0A valid positive; V-K0B invalid realization; ITERATION_35 written); workflow 6 open at step 1-2 (exposure recovery engineering + code decisions)
```

An iteration **is** one whole Pro-to-Pro loop. The three-access rule that
governs it lives in `AGENTS.md`, **Convergence belongs to touchpoint 2** — not
restated here, because a second copy of a rule is what made this file start
contradicting itself before.

## R4 — frozen contract and closure state

**R4 is COMPLETELY frozen — read the _COMPLETE file, not the partial one.**
`docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`. The earlier
`D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md` is the partial freeze, immutable, and its
own header overclaims what it froze. Do not quote it.

```text
expansion         = NONE
topology seeds    = 20260734..20260741   (repurposed, NOT inherited via R3 expansion)
episodes          = 8 Part-A control + 8 focal audit, per topology
n_select/n_eval   = 2 / 2
R3 data pooling   = forbidden
```

**Fresh means fresh at the highest inferential unit.** New episodes under the
eight R3 topologies are fresh *conditional* observations, retainable only as
`R4_ORIGINAL_PANEL_CONDITIONAL_REPLICATION`, never pooled or substituted.
**R3 support does not pre-pass R4 support** — on failure
`SOURCE_EVENT_SUPPORT_INSUFFICIENT` fires with no substitution and no expansion.

**The freeze ruling's closing ambiguity was resolved in favour of proceeding
with its own NEXT_ACTION list A–E**, on the strength of E's closing sentence
gating only the formal R4 measurement. This is a Project Manager reading of an
ambiguous ruling, recorded here so it can be challenged; if wrong, the wrong
thing is reversible result-layer code, and no compute was spent on it.

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
H formal R4 measurement                  INVALID_R4_REALIZATION stands (ruled)
H' post-repair R4 re-run                 RETURNED 8/8 -- REJECTED as formal result
I  provenance correction + localization   RULED -- steps 1-4 accepted as done,
                                          cloud cause recorded UNRESOLVED
J  Route A amendment + B1-B5 repair       DONE  69c95e61 -- schema 2, 36 passed,
                                          6 paired negatives watched red
K  manifest-replay development gate       DONE  fd3087ac -- probe + gate, 22 passed,
                                          12 paired negatives watched red
L  full-horizon replay exercise (dev)     RAN -- MANIFEST_REPLAY_FAIL on
                                          assertion 6 ONLY; replay itself
                                          reproduced everything. Note
                                          20260730_MANIFEST_REPLAY_GATE_FIRST_RESULT.md
M  freeze fresh-population selection RULE DONE  fd3087ac --
                                          D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md
N  generate immutable fresh inventory     ROUTE CANCELLED 2026-08-01 -- awaits
                                          Pro's re-ruling under local-only
O  formal successor run                   HELD, awaits the same re-ruling
```

**RULED 2026-07-30 (round 2): ROUTE A, AMENDED. Do not wire the manifest in.**
Round `20260730_d7_s_provenance_correction_result`:

```text
5a  must cloud-cloud localization finish first   NO
5b  Route A or Route B                           ROUTE A, AMENDED
5c  may fresh evidence be designed now           DESIGN + SELECTION RULE yes;
                                                 POPULATION no
5d  wire the manifest now                        NO -- six blockers first
```

**RULED 2026-07-30: the re-run does NOT reverse H and is not a formal R4
result.** Round `20260730_d7_s_r4_rerun_disposition`:

```text
4a  retract H's invalid disposition           NO
4b  retract it for the earlier R4 artifact    NO
6a  does the rerun carry R4's conclusion      NO
6b  missing property   reproducible evidence-population identity
6c  classification     EXPLORATORY_BRANCH_ROBUSTNESS_UNDER_UNREGISTERED_WORLD_VARIATION
D3  severity           claim-blocking repair
```

Run `30479940700` (tag `d7s-audit-4`, 8/8 shards) is preserved as a conditional
within-run observation with **no confirmatory weight**. The full mechanism
record — the REJOIN counter blind spot, the corrected probe firing 3/950-step
rolls, what survives (225,048 injectivity checks, 0 refusals) — lives in that
round directory and its evidence notes, not here.

**The claim-blocking defect.** Same pinned topology hash, same seeds, ->
three different world fingerprints; the two cloud runs disagree on 3 of 8
topologies. Ruled a population-provenance failure: a registered episode key
must identify one reproducible world or one validated probability law, and it
currently identifies neither. The cross-machine localization of this was
cancelled with the cloud line (user ruling 2026-08-01, evidence note
`20260801_CLOUD_CROSS_DEVICE_COMPARISON_LINE_RETIRED_BY_USER.md`); the
one-machine provenance requirement itself still stands.

**Implementation bindings decided in D'/D''/D''', owed to Pro as disclosure at
the next touchpoint** (none reopens a frozen decision): the length gate
compares against registered h, not `window_series_length(h)`; R4 identity is
DECLARED (`--population r4`), strict subsets admitted for sharding, foreign
seeds hard-refused; the freshness sentinel gains an eighth artifact-level
condition (produced seeds pairwise distinct and in-population) without
renumbering 1–7; plus `NOT_EVALUATED` as a fifth per-limb state and the
`PART_A_FULL_SYNC_MATERIALLY_WORSE` label, both outside the frozen vocabulary.

**Provenance rule created by D', binding any future run.** With
`--population r4` the `run_contract_id` becomes the R4 namespace, changing
every derived seed: shards from before `28d6933f` and after are not the same
measurement and must never be pooled.

Steps D and F returned REJECT before repair; every defect was re-verified by
the Project Manager rather than taken on report, and the evidence lives in
`20260728_D7_S_R4_THE_PLANNED_PRODUCTION_ROUTE_CANNOT_PROVE_IT_IS_R4.md` and
the round directories. A green test count is not instrument validation —
`main()` was invoked by no test when 249 passed.

Two carried items for the realization gate, neither silent: Pro's launch-gate
precondition "calibration arm ordering" is satisfied by **deletion** — check
it, do not assume it; and the disclosure list above goes to Pro at the next
touchpoint.

### The road here, in pointers

| What happened | Where |
|---|---|
| D7.S audit run 2 returned a valid non-affirmative result | `logs/d7s_audit_2_30289161086/`, note `20260727_D7_S_AUDIT_2_RESULT_AND_A_MISLABELLED_BRANCH.md` |
| Ruled `PRIMARY_G_DEGENERATE`; the measurement route closed, not the research question | round `20260727_d7_s_audit_2_result_disposition` |
| The global normalizer retired for this claim; N5 comparator-scale mismatch raised | round `20260728_d7_s_autopsy_result`, `logs/d7s_autopsy_2/` |
| R4 derived at a five-unit absolute focal margin, ruled derivable | round `20260728_r4_materiality_derivation` |
| The partial R4 freeze, left immutable | `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN.md` |

**Say "relevance not demonstrated", never "unrelated".** The stronger reading
was this conversation's inference and Pro rejected it.

**Two errors of mine not to repeat.** The ratio/linear divergence was **not**
an R3 design defect — the registered linear gate plus `LCB95(B_m) > 0` keeps
the linear form where it equals the ratio. And `U* = V_SET - V_KEEP`, so
`U*_stable = -3` means SET is WORSE than KEEP.

### On a killed shard — the ruling's rule, which replaces ours

A topology is indivisible. Never pool a partial topology; preserve every
completed whole-topology shard; rerun the failed topology **whole at the same
stage commit and contract**; pool only once the seed union matches a frozen set.

### Two conditional re-review triggers

- Introducing **arbitrary user-controlled strings** into environment state —
  the encoder's string branch has no length prefix, tolerable only while no
  reachable string carries a structural delimiter (measured: 61 distinct, zero
  such).
- `observation_spaces`/`action_spaces` ceasing to be immutable configuration,
  or the audit ever calling `.sample()` on them.

### Open decisions that are the user's, not mine

**None outstanding** (beyond the action-8 escalation in `next_boundary`).
Branch ownership of `untied-k` is settled; formal-run authorization is covered
by the active grant; the OS-entropy construction seed is ruled **parked** with
its four named reactivation conditions in the round record.

### Cost

Local measured rate 0.0615 s/step (2026-07-27); `|Z|=8` projects to ~4.2 h on
this box. `--workers 4` is wired into the audit shard; determinism proved
byte-identical at run `30270540138`. Cloud rates retired with the vehicle.

## Standing constraints

```text
active_pm_session=4c20178a-f062-40b8-a625-f385d2c65136 (claimed 2026-08-01 in the agentify-transport commit; the prior claim's boundary 97c62107 was behind HEAD 43086567, a stale claim is not a lock)
branch_scope=untied-k only, never touch another branch (user ruling 2026-07-27)
aggressive_branch=another line's, never push
formal_compute=user authority only
review_transport=project_manager_direct
autonomous_research_grant=ACTIVE_TEN_ITERATION_WORKFLOW_ROUND_GRANT_20260801 (user /goal 2026-08-01, "10轮完整的工作流自动迭代"; one iteration = one workflow round, per iteration_definition below)
iterations_remaining=9
conclusion_bearing_iterations_consumed=35
grant_history=TWENTY_ITERATION_OVERNIGHT_20260726 and FULL_PERMISSION_TEN_ITERATIONS_20260727 both consumed and closed; TEN_ITERATION_WORKFLOW_ROUND_GRANT_20260727B superseded 2026-08-01 with 7 remaining by the new ten-round grant; details in git history of this file
iteration_definition=one complete Pro-to-Pro loop (user ruling 2026-07-27): receive Pro's ruling, make the code decisions, implement, run the experiment, submit the result back to Pro. Nothing smaller is an iteration.
d7s_compute_authorization=GRANTED_20260727 (formal compute for the ten rounds is covered by the active grant)
r5_reanchor_compute_grant=GRANTED_20260728 (user, "launch it anyway", in advance of Pro's ruling; removes the AUTHORIZATION gate only -- it does not authorize launching before Pro's ruling names the branch, and a margin re-anchor is pre-registered first, always)
git_integration_status=project_manager_direct_authorized
intermediate_authorization_prompts=forbidden
experiment_orchestration=hmasd-experiment-operator only, never an ad hoc child
experiment_operator_fallback=forbidden
subagent_dispatch=user-granted 2026-07-27
iteration_report_requirement=required_before_successor
uav_user_scope=transient_demand_coverage_plus_charging_roster_change_plus_temporary_detach_failure_robustness
uav_physical_fleet_boundary=fixed_slots_distinct_from_dynamic_service_roster
```

Accounting: the active grant (2026-08-01) is ten workflow rounds; workflow 4
was cancelled by user course ruling (consumes none), workflow 5 closed as
iteration 1 (report 35), so `iterations_remaining=9`. Workflows 1–3 closed
under the superseded 20260727B grant. `conclusion_bearing_iterations_consumed` is the
**lifetime count of iteration reports** — the machine-checkable anchor for
`docs/report/ITERATION_<n>.md` (1–34 exist; 24–29 were supporting work) — not
consumption against the current grant. The stale "next report is 30" claim this
paragraph used to carry is the drift this file warns about: reports 30–34 had
already been written. Never report a count of work cycles as a count of
iterations.

Formal and bounded runs use only the registered nonpersistent
`hmasd-experiment-operator`, fixed to `haiku` with `low` effort. It stays silent
and returns exactly one `COMPLETE` or `ERROR` terminal payload.

No Controller, persistent Monitor, dispatcher, callback route, global write
lease or compatibility line is active. Subagent dispatch was blocked by the
session prompt, not this repository, and was lifted 2026-07-27.

The workstation is shared with another research line, and it is the only
machine: the cloud vehicle is retired (user ruling 2026-08-01). Check for
foreign processes before any local run (`scripts/check_compute_free.ps1`) and
never touch them.

### Guard state — a PM-owned premise, not an adjudicated fact

All seven areas Pro made a precondition on any future environment run carry
paired negatives, each watched failing; the event-admission surface swept sound
(31/31 mutations red). Pro declined to rule on closure because the evidence
fence did not carry the tests — **check it at the realization gate.** Known and
deliberately unrepaired: diagnostics-only fields and two dead-in-production
functions. Details: `20260728_D7_S_THE_EVENT_ADMISSION_SURFACE_IS_SOUND.md`.

### Control plane — what enforces itself

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
launch_and_watch_run.ps1  preflight + status. Hands back the launch command; only
                          a backgrounded Bash call survives detachment.
pretooluse_guard.ps1      --no-verify and core.hooksPath, branch scope.
```

The design charter governing all of this — budgets, single-source, incident
threshold, the hash whitelist — is the `Design charter` fence in
`$hmasd-workflow-change-audit`.

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

### The source-assignment defect — what is settled

- **`duty_map` is a PARTIAL INJECTION** from executable duties to physical UAVs;
  a non-injective map is an internally inconsistent controller state.
- **A phantom duty is UNCOVERED** — coverage requires an executable,
  action-bearing incumbent (`m_raw` / `m_exec` / `C = dom(m_exec)`).
- **The defect is arm-specific**: `constructive_mixed`'s REJOIN branch can
  double-assign; `full_sync_set_update` is injective by construction. Measured
  at 33% of check boundaries on the development topology.
- **Both halves of the timing are true at different boundaries**: persistent
  after onset at STEP; repaired-and-recreated at PHASE.
- **R4's artifact is `INVALID_R4_REALIZATION:
  DUTY_ASSIGNMENT_NOT_EXECUTABLY_WELL_DEFINED`** — immutable, citable only as a
  descriptive external-return observation of historical code paths.
- **Obligation A reopened at A1–A4** (solver and Hall-witness lemmas RETAINED;
  A3 rescuable, not to be replaced). **Obligation B's 1200/1200 is RETIRED**
  (computed through the lossy inversion). **Obligation C was never closed.**
- **The defect does NOT reach results only through flown actions** — Pro
  falsified that claim of mine; both certification-path leaks are fixed by
  injectivity itself.

## Runtime and protected semantics

```text
python        = C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
torch         = 2.7.0+cpu
torch_threads = 1
backend       = cpu
```

No CUDA fallback, backend mixing, or cross-backend resume. Preserve every closed
source, result and first-match meaning. Concurrency is file ownership only —
the fence in `AGENTS.md` is the single source.

## Where things live

| | |
|---|---|
| Project Manager instructions — authority, the loop, Stage A/B, acceptance, task sizing, dispatch, review | `AGENTS.md` |
| Standing context every subagent reads | `docs/project/AGENT_CONTEXT.md` |
| Scientific method contract | `docs/project/ALGORITHM_PRINCIPLES.md` |
| Cost ceilings and violation semantics | `docs/project/EVIDENCE_COMPLEXITY_POLICY.md` |
| What the paper is about, and the standing check | `docs/project/RESEARCH_GOAL.md` |
| Findings and measurements | `docs/research/cdc/EVIDENCE_NOTES/` |
| Review rounds, questions, rulings, reconciliations | `docs/external-review/rounds/` |
| Closed generations G2–G16 | `docs/research/cdc/CLOSED_GENERATION_BOUNDARY_ARCHIVE_G2_G16.md` |
| Latest Chinese iteration report | `docs/report/ITERATION_35.md` |

Closed generations G17–G20R, UAV G1/G2, the contract-grill mechanism and the D7
part-B margin-instrument era are retired; their evidence notes and round
directories remain under the paths above.
