# G38 folded six-coordinate CS prelaunch acceptance

```text
algorithm_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
source_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_P0
scientific_disposition=IDENTIFIABLE_FRESH_FOLDED_SIX_COORDINATE_CS_G38_DESIGN
implementation_code_commit=0fd5f73cc783d5056fdd8019e820965e522c7977
technical_acceptance_owner=project_manager
technical_acceptance=ACCEPTED
formal_compute_started=false
nonformal_compute=COMPLETE_operational_valid_same_source
next_boundary=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_ALIGNMENT_AUDIT
```

## Accepted realization

PM accepted the exact five-path G38 implementation package after the registered
implementer returned through a verified isolated-worktree ticket and PM copied
only the ticket-authorized files into the main worktree:

- `ha_ctse_process/continuous_roster_six_coordinate_cs_g38.py`
- `scripts/run_continuous_roster_six_coordinate_cs_g38.py`
- `tests/ha_ctse_process_continuous_roster_six_coordinate_cs_g38_test.py`
- `tests/run_continuous_roster_six_coordinate_cs_g38_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_INDEX.md`

The common pre-fold graph has exactly the two frozen raw-observation affines:
`member_input: Linear(10,32)` and `current_readout: Linear(10,2)`. FULL10 and
FOLD6 have byte-identical initial serialized state, shapes, trainable masks and
parameter count. Both run with CS carry, the unchanged critic and G31 credit.

The FOLD6 collector is G38-owned and constructs, passes, serializes, replays,
audits and optimizes only six-coordinate observations. Its model entry rejects
ten-coordinate tensors. Constants are written only after the six-coordinate
boundary and only for active rows; inactive rows remain zero. FULL10 collection
is tensor/outcome identical to the inherited G32 collector under the same
source and action noise.

The exact fold updates both biases from their corresponding pre-fold removable
columns, retains columns `0:6`, copies every other tensor, removes exactly 136
actor weights and performs no post-fold optimizer step. The deployed actor is a
true six-coordinate graph.

The fold-equivalence path advances one environment trajectory per episode. It
evaluates both actors on the same pre-step state and action noise, computes both
immediate rewards without a second environment advance, compares the complete
reward traces and recomputed utility/event-window/segment summaries, and
validates each observed membership edit against the registered fixed/random
schedule. Fault-injection tests prove that wrong membership edits and divergent
reward algebra fail the gate.

## PM verification

The first implementer return exposed two PM-detected pre-acceptance defects:
the inherited collector still stored ten-coordinate FOLD6 observations, and
three fold gates were constant rather than evidence-bearing. The same ticket
was repaired before acceptance. These were not accepted artifacts and did not
launch any experiment.

Final proof-sized checks on the integrated main worktree:

```text
G38_focused_tests=15_passed
combined_G34_G35_G38_tests=50_passed
py_compile=passed
project_manager_contract=HMASD_PROJECT_MANAGER_CONTRACT_OK
research_workflow_contract=HMASD_RESEARCH_WORKFLOW_CONTRACT_OK
ticket_changed_path_set_exact=true
diff_check=passed
```

The tests cover the no-read six-wide collection/replay path, byte-identical
paired initialization, live gradients for all eight removable affine columns,
the exact 136-weight fold, evidence-bearing one-trajectory equivalence,
inventory, bootstrap pairing, equality semantics, branch priority, CPU/runtime
identity and formal authority plus three-artifact preflight digest binding.

## Evidence complexity and authority

```text
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
nonformal_total_real_transitions=26880
nonformal_optimizer_steps=120
nonformal_wall_clock_cap_seconds=1200
formal_total_real_transitions=1013760
formal_optimizer_steps=3600
formal_wall_clock_cap_seconds=28800
```

The realization is within the user-owned evidence ceiling. This acceptance
does not authorize training. External Pro must first return `ALIGNED` from the
single read-only G38 code-science audit. Only then may the registered Experiment
Operator execute the exact same-source bounded nonformal preflight. Formal work
additionally requires the preflight bindings and the dedicated frozen token.

## Same-source bounded preflight

After External Pro returned `AUDIT_DISPOSITION=ALIGNED`, the registered
Experiment Operator executed the exact source commit once at:

`logs/nonformal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_0fd5f73_r1`

```text
exit_code=0
formal=false
operational_valid=true
operational_errors=[]
branch=NONFORMAL_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_EXERCISE_COMPLETE
replicates=1
arms=2
fast_updates_per_arm=10
return_to_go_updates_per_arm=10
environments_per_update=8
ppo_passes=2
evaluation_cells=30
evaluation_episodes_per_cell=8
real_transitions=26880
optimizer_steps=120
bootstrap_resamples=250
train_seconds=54.891060499998275
evaluate_seconds=9.751860000000306
analyze_seconds=0.1641401999986556
nonformal_total_seconds=64.80706069999724
formal_projection_seconds=2651.7333787498865
formal_projection_executable=true
```

PM independently reran the read-only artifact validator. The training and
evaluation error list was empty; source commit, replicate/cell inventory,
training/evaluation digests and the exact projection formula all matched the
serialized artifacts. No retry, resume or second run occurred.

The standing user CPU grant now permits exactly one formal G38 execution from
the same source, with the aligned audit, all three preflight digests and the
token `CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1`.

No G33 path was read, restored, staged or reactivated.
