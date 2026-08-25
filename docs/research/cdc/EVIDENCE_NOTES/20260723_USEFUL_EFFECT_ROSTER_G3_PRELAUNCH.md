# USEFUL_EFFECT_ROSTER_G3 prelaunch acceptance

Date: 2026-07-23

```text
implementation_base_commit=56b595fd36f2b9cde988edd95e74f50a85c3a51e
formal_launch_source=next_integrated_git_commit
exercise=logs/nonformal_useful_effect_roster_g3_20260723_pm1
backend=cpu
torch_threads=1
formal=false
result=SOURCE_NON_IDENTIFIABLE_USEFUL_ROSTER_G3
iteration_cost=0
iterations_remaining=2
```

## Accepted implementation boundary

The active source implements the frozen three-arm comparison exactly:
`NO_ROSTER`, `TEAM_REC` and permutation-equivariant `ROSTER_ATTN` share the
registered query/base inventory, while only their declared memory input and
logit route differ. The task samples complete balanced demand/deficit/event
ledgers, uses realized demand-served external utility and retains duplicate
optimal effects plus zero-demand labels. Training uses N=2/3; evaluation also
contains held-out N=4, long gaps and the joint held-out profile.

The runner owns train, evaluate, analyze and exercise phases; checkpoints bind
source, optimizer, exposure and RNG state. The artifact validator reconstructs
evaluation and intervention utilities, closes reference counts and ledgers,
checks CPU/one-thread/token/budget identity, replays the pure first-match
selector and rejects temporary residue. It rejects a nonformal exercise when
formal evidence is required.

## Proof-sized evidence

```text
focused_test_command=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/ha_ctse_process_useful_effect_roster_g3_test.py tests/run_useful_effect_roster_g3_test.py
focused_test_result=11_passed
exercise_checkpoints=3
exercise_evaluation_references=24
exercise_causal_audits=16
exercise_operational_valid=true
exercise_source_control_pass=true
exercise_evaluation_ledger_balance_pass=true
exercise_natural_quota_pass=false
formal_validator_rejects_exercise=true
```

The reduced exercise is intentionally too small for the frozen formal natural
audit quota: 16 total audit rows are below 128 per replicate. Therefore its
first-match `SOURCE_NON_IDENTIFIABLE_USEFUL_ROSTER_G3` label is expected and has
no scientific meaning. It demonstrates only that the complete CPU execution
path closes and fails closed when presented as formal evidence.

## Protected-semantics inspection

- G0, G1 and G2 sources, results, thresholds and first-match meanings remain
  frozen; their closed executable implementations are removed only from the
  active line and remain in Git history and durable evidence.
- G3 uses external demand-served utility without intrinsic, diversity or
  uniqueness reward. The 18,400-case structural roster gate is retained only as
  source-control evidence.
- Query inputs exclude the deficit, standing service counts, physical identity
  and future references. The centralized critic alone receives standing counts.
- Stored action draws are replayed; each arm owns RNG, optimizer and checkpoint
  state; inactive treatment parameters receive zero gradient.
- The registered CPU-only torch 2.7.0+cpu, one-thread condition is preserved.

## Launch disposition

Project Manager accepts the implementation and bounded exercise. The only next
admissible evidence action is one conclusion-bearing formal iteration 4 from
the integrated Git source, executed by the registered silent experiment
operator with token `AUTHORIZE_USEFUL_EFFECT_ROSTER_G3_FORMAL_CPU_V1`.

After a valid result, Project Manager must validate and interpret the frozen
first-match selector, write `docs/report/ITERATION_4.md` in Chinese, and only
then select the next boundary. No external review is required before launch.
