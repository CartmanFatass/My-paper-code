# G38 fold-equivalence operational repair

```text
algorithm_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
assignment_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FOLD_EQUIVALENCE_REPAIR
repair_scope=exact_operational_defect_under_unchanged_contract
technical_acceptance_owner=project_manager
technical_acceptance=ACCEPTED
formal_retry_resume_restart=none
code_science_alignment_correction_recheck=ALIGNED
repaired_source_nonformal_preflight=COMPLETE_operational_valid
fresh_formal_attempt_2_authority=ACTIVE_USER_AUTHORIZED
fresh_formal_attempt_2_token=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1
fresh_formal_attempt_2_run=logs/formal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_ea93b15_r2
next_boundary=ONE_EXACT_REPAIRED_SOURCE_FORMAL_CPU_EXECUTION
```

## Root cause and exact repair

The rejected formal attempt proved that the algebraically equivalent ten-wide
pre-fold and six-wide folded float32 affine kernels can accumulate different
rounding errors. Individual action errors remained below the frozen limit, but
autoregressive prefix sums exceeded it in 34 FOLD6 cells.

The repair installs one actual, shared factorized affine kernel in both
pre-fold arms. Each of the two registered raw-input affines computes the
retained six-coordinate term and then combines a fixed-order four-coordinate
term with its bias. FULL10 supplies its actual coordinates 6:10; FOLD6 supplies
the registered constants. After folding, the true six-coordinate actor uses
the identical retained kernel and stored effective bias.

This remains exactly the frozen affine function. It does not add a raw-input
path, audit-only override, donor, filler or proxy. Before folding both ten-wide
matrices and every removable column remain real trainable parameters; after
folding exactly 136 actor weights are absent. The scientific tolerance, graph,
seeds, budgets, PPO/RNG, checkpoints, lifecycle, evidence volume and branch
order are unchanged.

## PM verification

The isolated-worktree ticket resolved and reverified with only these three
changed paths:

- `ha_ctse_process/continuous_roster_six_coordinate_cs_g38.py`
- `tests/ha_ctse_process_continuous_roster_six_coordinate_cs_g38_test.py`
- `docs/research/designs/CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_INDEX.md`

PM integrated line-normalized content exactly and independently obtained:

```text
G38_tests=16_passed
G34_G35_regressions=35_passed
py_compile=passed
project_manager_contract=passed
research_workflow_contract=passed
```

PM then loaded the failed formal run's replicate-0 final FOLD6 checkpoint
read-only into the repaired code and freshly folded it in memory. A formal-like
capacity-12 random-process audit used 128 episodes and H48:

```text
lifecycle=true
fold_passed=true
reward_comparisons=6144
membership_edit_checks=6144
summary_comparisons=1280
pre_tanh_mean_error=0.0
action_error=0.0
prefix_action_sum_error=0.0
token_log_probability_error=0.0
reward_trace_error=0.0
summary_error=0.0
all_exact_fields=true
```

The failed formal run root was never modified or resumed, and no nonformal or
formal experiment was run during repair acceptance. A fresh conclusion-bearing
execution remains forbidden until External Pro confirms that this correction
preserves code-science alignment and the required runtime authority is present.

External Pro subsequently returned exactly `AUDIT_DISPOSITION=ALIGNED` in the
single naturally completed correction-recheck round. The transport used zero
recovery submissions, no Answer Now action, one completed monitor and two
stable exact raw snapshots. This authorizes only one bounded nonformal
preflight from the repaired source; it does not authorize a formal retry.

## Repaired-source bounded preflight

The registered Experiment Operator executed exactly one bounded nonformal
exercise from repair commit `ea93b15eabf68c35ba8e459ca8527e56d2988db8`:

`logs/nonformal_continuous_roster_six_coordinate_cs_g38_cpu_20260726_ea93b15_r1`

```text
exit_code=0
formal=false
operational_valid=true
operational_errors=[]
branch=NONFORMAL_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_EXERCISE_COMPLETE
replicates=1
arms=2
evaluation_cells=30
evaluation_episodes_per_cell=8
real_transitions=26880
optimizer_steps=120
bootstrap_resamples=250
K_search=0
train_seconds=61.2549091999972
evaluate_seconds=10.290152500005206
analyze_seconds=0.16526929999963613
total_seconds=71.71033100000204
formal_projection_seconds=2922.731710000189
formal_projection_executable=true
```

PM independently ran the complete read-only preflight validator. Source,
configuration, inventory, artifact digests, analysis branch and the exact
projection formula passed. All 15 FOLD6 cells passed their fold audit, and the
maximum pre-tanh, action, prefix, log-probability, reward-trace and summary
errors were each exactly `0.0`.

This closes the repaired-source technical prerequisites. It does not inherit
or revive the already consumed formal token: the prior formal attempt ended
operational invalid, and its assignment explicitly prohibited retry, resume or
restart. The user subsequently authorized completion of all nine remaining
conclusion-bearing rounds. The frozen scientific contract permits only its V1
token, so the fresh attempt is distinguished by its new assignment and run root
while the user reauthorizes that exact token for one execution. Any operational
failure still costs zero iterations and authorizes no automatic retry, resume
or restart.
