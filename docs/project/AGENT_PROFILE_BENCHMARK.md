# Implementer and reviewer profile benchmark

```text
purpose=select_lowest_cost_profile_without_quality_loss
formal=false
conclusion_bearing=false
scientific_iteration_cost=0
implementer_variants=sol_high|terra_high|luna_max
reviewer_variants=sol_high|terra_high|luna_max
same_class_instructions=byte_identical
same_task=true
blinded=true
project_acceptance_owner=project_manager_code_side
```

This is a code-worker selection experiment, not an algorithm experiment. It
tests the user's hypothesis that HMASD implementation difficulty is dominated
by a Pro-frozen scientific contract while the code realization itself may not
need the most expensive worker profile.

## Fairness boundary

- Launch the three implementers concurrently from one exact base commit in
  separate isolated worktrees with the same assignment, named interfaces,
  write scope, runtime and focused-check budget.
- The three implementer profile `developer_instructions` blocks must be byte
  identical. Only profile name/description, model and reasoning effort differ.
- Launch the three reviewers concurrently against the same anonymous candidate
  diff and same review assignment. Reviewer instructions are also byte
  identical within class.
- No variant may read sibling worktrees, outputs, model identities, gold tests,
  seeded-defect manifest or other reviews.
- PM freezes quality gates and gold evidence before launches. Model outputs
  never define their own acceptance criteria.

## Shared implementer task

Implement one pure CPU/PyTorch runtime member-state rebinding primitive in the
benchmark worktree only:

```python
rebind_member_state(
    state,            # [batch, old_width, hidden]
    old_member_keys,  # int64 [batch, old_width]
    old_active,       # bool [batch, old_width]
    new_member_keys,  # int64 [batch, new_width]
    new_active,       # bool [batch, new_width]
) -> Tensor           # [batch, new_width, hidden]
```

Frozen semantics:

- active keys are nonnegative and unique within each batch row; inactive keys
  are exactly `-1`;
- a key active in both layouts copies its complete hidden vector exactly;
- a newly active key and every inactive destination slot receive exact zero;
- departed keys do not appear in output; input tensors are not mutated;
- output preserves state dtype/device and survivor autograd connectivity;
- validation fails closed on shape, dtype, device, sentinel, duplicate-key or
  nonfinite-state violations;
- no RNG, global state, serialization, compatibility adapter or per-member
  Python/Tensor `.item()` loop is allowed.

Each variant owns only the assignment-created benchmark module and focused test
file in its worktree. It may inspect named existing member-key/lifecycle helpers
for conventions but may not change them. It runs the same public focused command.
PM later runs one held-out oracle, absent from all assignments, covering
permutation, expansion, contraction, empty rows, gradient routing, nonmutation,
malformed layouts and a moderate batched case.

## Shared reviewer task

After implementer terminals, PM freezes one anonymous candidate diff and one
private defect manifest before any reviewer launch. The fixture contains the
same contract and a realistic mixture of critical semantic defects, operational
defects and correct code that must not be flagged. Every reviewer sees the same
diff and exact review rubric.

Review only:

- survivor/new/departed/inactive semantics and gradient routing;
- validation, mutation, batching and hidden host synchronization;
- whether public tests could pass through an unintended mechanism;
- exact frozen scope and minimal repair direction.

Style, coverage, compatibility and speculative refactoring are out of scope.

## Scoring and selection

Freeze before launch:

### Implementer quality

- hard floor: all held-out semantic/gradient/nonmutation gates pass, no scope
  violation, and no protected-semantics invention;
- secondary: public test validity, batched realization, simplicity and accurate
  limitation reporting.

### Reviewer quality

- hard floor: find every gold critical defect with correct causal reasoning and
  no critical false positive;
- secondary: weighted defect recall, precision, severity calibration, location
  tightness and minimal repair quality.

Quality is compared first. A cheaper profile is eligible only if it meets the
hard floor and is non-inferior to the best observed profile on critical quality.
Among eligible profiles, select the lowest measured cost separately for
implementer and reviewer. Use platform-reported token/compute usage when
available; otherwise record that it is unavailable and use elapsed wall time
plus the declared model tier only as an explicit proxy, never as exact currency.

Record raw outputs, PM gold scoring and the selection in
`docs/project/AGENT_PROFILE_BENCHMARK_RESULT.md`. After selection, update the
normal registered implementer/reviewer profile, delete losing benchmark
profiles and temporary fixtures/worktrees, and restart before using the winner.
