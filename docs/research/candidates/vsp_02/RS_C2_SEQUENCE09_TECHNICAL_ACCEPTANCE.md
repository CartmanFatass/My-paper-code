# VSP-02 sequence 09 technical acceptance

```text
assignment_id=rs_c2_vsp02_sequence09_acceptance_20260809_28d9758
owner_role=code_project_manager
owner_mode=treatment
parent_portfolio_assignment=rs_cycle1_portfolio_bootstrap_20260809_28d9758
candidate=CAND-VSP-02@adversarial-revision-v8
requested_action=A
source_commit=3cf48f783b361b4b1708eb8d49e9d561e5e96be8
technical_disposition=CODE_ACCEPTED
formal=false
execution_readiness=not_triggered
blockers=none
```

## Conclusion

The existing exact duration-escrow oracle and zero-training duration-exposure
mapping package are technically accepted at source commit
`3cf48f783b361b4b1708eb8d49e9d561e5e96be8`.

The accepted proposition is deliberately narrow:

- On the represented registered 16-branch finite synthetic mixture, the
  candidate adds no value over the registered `Z0` finite comparator.
- The inspected runtime interface does not expose an owner-selected duration.
- The inspected runtime boundary vocabulary does not expose the oracle's
  distinct `CLAIM`, `RELEASE`, or `TERMINAL_HORIZON` lifecycle objects.

This is one technical acceptance of the named package. It is not scientific
acceptance, retirement, or authorization for a build or experiment.

## Exact accepted inputs

- `experiments/candidates/vsp_02/duration_escrow_oracle.py`
- `experiments/candidates/vsp_02/duration_exposure_mapping.py`
- `tests/experiments/candidates/vsp_02/test_duration_escrow_oracle.py`
- `tests/experiments/candidates/vsp_02/test_duration_exposure_mapping.py`
- `docs/research/candidates/vsp_02/CODE_SCIENCE_INDEX.md`

Public source-commit locators:

- [duration escrow oracle](https://github.com/CartmanFatass/My-paper-code/blob/3cf48f783b361b4b1708eb8d49e9d561e5e96be8/experiments/candidates/vsp_02/duration_escrow_oracle.py)
- [duration exposure mapping](https://github.com/CartmanFatass/My-paper-code/blob/3cf48f783b361b4b1708eb8d49e9d561e5e96be8/experiments/candidates/vsp_02/duration_exposure_mapping.py)
- [oracle tests](https://github.com/CartmanFatass/My-paper-code/blob/3cf48f783b361b4b1708eb8d49e9d561e5e96be8/tests/experiments/candidates/vsp_02/test_duration_escrow_oracle.py)
- [exposure-mapping tests](https://github.com/CartmanFatass/My-paper-code/blob/3cf48f783b361b4b1708eb8d49e9d561e5e96be8/tests/experiments/candidates/vsp_02/test_duration_exposure_mapping.py)
- [code-science index and byte-stable oracle receipt](https://github.com/CartmanFatass/My-paper-code/blob/3cf48f783b361b4b1708eb8d49e9d561e5e96be8/docs/research/candidates/vsp_02/CODE_SCIENCE_INDEX.md)

The native CPM result supplies the exact public commit-pinned locator for this
acceptance record after its evidence commit is created and pushed.

## Oracle receipt

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B experiments/candidates/vsp_02/duration_escrow_oracle.py
```

Terminal receipt:

```text
exit=0
terminal=REGISTERED_Z0_SELECTOR_VALUE_CONFORMANCE
disposition=NO_INCREMENT_OVER_REGISTERED_Z0_COMPARATOR
coverage_total=128
coverage_valid=64
coverage_stale=64
coverage_per_world_valid=32
coverage_per_world_stale=32
future_branches_per_z0_action=16
registered_selector_keys=16
integrated_value_keys=4
registered_remaining_horizon=2
tau_values=100|104
aggregate_invariants_true=14/14
comparator_terminal_gate=true
```

The exact candidate and comparator mixture values were identical:

```text
F|SHORT=71/64
F|LONG=63/64
P|SHORT=135/64
P|LONG=139/64
```

Per-realization record-shape observations were `4 events + 1 score + 1
release + 1 tombstone` for each valid realization and `1 event + 0 scores + 0
releases + 1 tombstone` for each stale realization. The full byte-stable JSON
receipt is bound in `CODE_SCIENCE_INDEX.md` at the source commit above.

## Duration-exposure mapping receipt

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B -m experiments.candidates.vsp_02.duration_exposure_mapping
```

Terminal receipt:

```json
{
  "raw_output_binding": "vsp_02.duration_exposure_mapping.v1",
  "checks": {
    "duration_is_owner_selected": {
      "passed": false,
      "detail": "same opportunity RNG, different skill actions -> gaps {'a': 1, 'b': 1} vs {'a': 1, 'b': 1}; the realized duration is independent of the owner's action"
    },
    "duration_is_exogenous": {
      "passed": false,
      "detail": "same action, different opportunity RNG -> gaps {'a': 1, 'b': 1} vs {'a': 15, 'b': 11}; the realized duration is drawn from the RNG"
    },
    "escrow_lifecycle_present": {
      "passed": false,
      "detail": "runtime boundary kinds = ('ordinary_opportunity', 'rollout_truncation', 'temporary_pre_removal_leave', 'terminal_boundary'); oracle requires 8 states and 8 events; absent from the runtime vocabulary = ('CLAIM', 'RELEASE', 'TERMINAL_HORIZON')"
    }
  },
  "terminal": "VSP02_DURATION_EXPOSURE_ABSENT",
  "scope": "Zero-training interface proof. Establishes object existence only; it licenses no scientific claim about VSP-02 and no build."
}
```

All three `passed=false` values are the intended negative observations; they do
not denote a failed invocation. The action intervention is paired with the RNG
intervention so the action null is not inferred from a dead measurement.

The direct file-path form was not used as the accepted mapping command because
this checkout does not install the repository-root `ha_ctse_process` package
into that script directory's import path. Module execution from the registered
ticket root completed successfully and changed no source or environment.

## Focused verification and activity counts

Command:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -B -m pytest -p no:cacheprovider -q tests/experiments/candidates/vsp_02/test_duration_escrow_oracle.py tests/experiments/candidates/vsp_02/test_duration_exposure_mapping.py
```

Receipt:

```text
exit=0
tests_passed=116
tests_failed=0
warnings=14
pytest_wall_clock=5.16s
```

The warnings are dependency deprecations from Matplotlib/PyParsing reached by
the runtime test factory; they do not alter the proof outputs or acceptance.

Activity/resource counts:

```text
source_files_changed=0
test_files_changed=0
index_files_changed=0
acceptance_records_added=1
training_runs=0
formal_iterations=0
cloud_calls=0
paid_calls=0
gpu_processes=0
network_calls=0
checkpoints=0
artifact_roots=0
environment_transitions=0
H=2
K_search=0
hypothetical_transitions=0
```

Execution readiness was not triggered: this assignment validates existing
finite-oracle and interface-proof sources without changing a runner,
execution-entry surface, serialization path, phase connection, or artifact
lifecycle.

## Explicit nonclaims and exclusions

This acceptance does **not** establish or authorize any of the following:

- same-instance action B;
- learned policy value or policy learning;
- adaptive-duration retirement in general;
- adaptive retirement of this candidate;
- production bookkeeping, return, or deployment semantics;
- a production `CLAIM`/close/cutoff/`RELEASE` lifecycle;
- full-`Z0` conditioning or value outside the registered 16-branch mixture;
- new physical worlds or transfer beyond the fixed synthetic instance;
- scientific acceptance or scientific retirement;
- formal compute, training, cloud, paid, or GPU work;
- a main-checkout write or integration decision.

The bookkeeping claim remains `PER_REALIZATION_RECORD_SHAPE_ONLY`. The exposure
claim remains an absence result for the inspected interface and vocabulary,
not a global proof that no alternate runtime object exists elsewhere.
