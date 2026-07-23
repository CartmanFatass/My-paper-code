# COUNT_PRESERVING_ROSTER_G4 prelaunch acceptance

Date: 2026-07-23

```text
implementation_base_commit=f3bd0e17ed40ee0e2e5fdfd76d67405c5ef8643d
formal_launch_source=next_integrated_git_commit
exercise=logs/nonformal_count_preserving_roster_g4_20260723_pm1
backend=cpu
torch_threads=1
formal=false
result=SOURCE_NON_IDENTIFIABLE_COUNT_ROSTER_G4
iteration_cost=0
iterations_remaining=1
```

## Accepted algorithm path

`ROSTER_SUM` keeps the exact G3 useful-effect source and adds one deterministic
set statistic: the sum of current standing-record effect one-hots. It combines
that raw count skip with a learned masked token mean. Float64 accumulation makes
the learned mean invariant to the order of the at-most-three standing records
at the registered 1e-7 boundary; outputs remain float32.

The direct `ROSTER_ATTN` comparator preserves the closed G3 normalized-attention
path. `TEAM_REC` preserves the ordinary recurrent public-history path. All three
arms instantiate the same complete policy/critic inventory, share paired source
ledgers inside each replicate and own independent optimizer/action RNG state.
Only the active treatment path receives actor gradients.

The G4 runner changes source identity, schemas, independent seeds, estimands,
tested-arm access and first-match labels. It keeps the G3 environment, reward,
PPO, 120-update formal budget, evaluation profiles, 0.90 access threshold, 0.10
gain threshold and consequence battery exactly unchanged.

## Proof-sized evidence

```text
focused_test_command=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/ha_ctse_process_count_preserving_roster_g4_test.py tests/run_count_preserving_roster_g4_test.py
focused_test_result=12_passed
exercise_checkpoints=3
exercise_evaluation_references=24
exercise_causal_audits=16
exercise_operational_valid=true
exercise_source_control_pass=true
exercise_evaluation_ledger_balance_pass=true
exercise_natural_quota_pass=false
formal_validator_rejects_exercise=true
```

The tests cover complete source controls, deficit mates, balanced ledgers,
attention permutation, exact count recovery, count-path permutation, every-arm
PPO/replay/gradient fences, checkpoint optimizer/RNG restore, selector
boundaries, reference/source/audit-utility/audit-arm tampering and formal
rejection of exercise artifacts.

The exercise closes train/evaluate/analyze with three checkpoints, 24 evaluation
references and 16 `ROSTER_SUM` audits. Its source-identifiability branch is
expected because 16 audit rows are below the formal quota of 128 per replicate;
it is operational evidence only.

## Protected-semantics audit

- G0 through G3 results and first-match meanings remain frozen. G4 does not
  rename or relabel G3 and uses independent seeds/artifact identity.
- No reward, observation, lifecycle, source distribution, PPO, budget,
  threshold, replay, checkpoint, backend or thread contract changes.
- The count skip reads only current standing commitment tokens. It contains no
  deficit, demand-derived target, future result, identity or reward.
- The centralized critic remains unchanged; actor treatment modules retain the
  registered gradient fences.
- The old G3 executable filenames are removed from the active line. Durable G3
  design/evidence/report and Git history remain.

## Launch disposition

Project Manager accepts G4 implementation and bounded nonformal evidence. The
only next admissible action is one formal CPU iteration 5 from the integrated
Git source, executed once by the registered silent experiment operator with
token `AUTHORIZE_COUNT_PRESERVING_ROSTER_G4_FORMAL_CPU_V1`.

After a valid terminal result, Project Manager must revalidate artifacts,
recompute the frozen selector and write `docs/report/ITERATION_5.md` in Chinese
before recording the terminal five-iteration project disposition.
