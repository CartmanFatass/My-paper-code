# G38 fold-equivalence operational repair

```text
algorithm_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
assignment_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FOLD_EQUIVALENCE_REPAIR
repair_scope=exact_operational_defect_under_unchanged_contract
technical_acceptance_owner=project_manager
technical_acceptance=ACCEPTED
formal_retry_resume_restart=none
code_science_alignment_correction_recheck=ALIGNED
next_boundary=ONE_REPAIRED_SOURCE_BOUNDED_NONFORMAL_PREFLIGHT
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
