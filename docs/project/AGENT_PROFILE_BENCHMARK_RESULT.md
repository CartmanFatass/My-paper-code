# HMASD implementer/reviewer profile benchmark result

```text
benchmark_status=COMPLETE
formal=false
conclusion_bearing=false
scientific_iteration_cost=0
base_commit=22a2e9e398d3a011e61f8392b880a4fb47845bc2
implementer_winner=gpt-5.6-terra/high
reviewer_winner=gpt-5.6-luna/max
token_usage=unavailable_from_native_child_runtime
monetary_cost=unavailable_from_native_child_runtime
selection_basis=critical_quality_then_accumulated_end_to_end_cost_proxy
```

This benchmark selects code workers only. It makes no algorithmic or scientific
claim and consumed no conclusion-bearing iteration.

The rows and raw terminal facts below are retained as historical benchmark
evidence. They do not define the current route: the persistent Workflow Design
Manager route is `gpt-5.6-sol/high`, and ticket/worktree identity is superseded
policy rather than a child admission or authority requirement.

## Frozen task and fairness

Three implementers received the same member-state-rebinding contract from one
base commit in isolated worktrees. Three reviewers received the same anonymous
diff and read-only review assignment. Same-class developer instructions were
byte-identical; only registered model and reasoning effort differed. The PM
froze the implementer oracle and reviewer gold manifest before the respective
launches.

One orchestration defect initially routed the Sol implementer to the wrong
worktree path. It failed before implementation began, was corrected, and then
completed. This is recorded as `harness_cost`, not a model-quality failure or a
code-repair round. The benchmark continued throughout.

## Implementer results

| Profile | Final focused check | PM hidden oracle | Code repair turns | Observed elapsed | Implementation quality |
|---|---|---|---:|---:|---|
| Sol-high | 13 passed in 1.89 s | pass | 0 | 488.17 s total, attribution invalid because it includes harness recovery and user wait | Correct batched pairwise match; broad public probes; `O(batch*old*new)` matching tensor. |
| Terra-high | 5 passed in 1.88 s | pass | 0 | 107.86 s | Correct sort/search realization; exact zero/gradient/validation behavior; best asymptotic and active-line simplicity. |
| Luna-max | 6 passed in 2.34 s | pass | 0 | 439.60 s | Correct batched pairwise match and empty-layout gradient handling; `O(batch*old*new)` matching tensor. |

All three changed exactly the two assigned paths and passed survivor,
new/departed/inactive, gradient, nonmutation, dtype/device, malformed-input,
all-inactive/mixed-batch and moderate-batch oracle gates. No candidate crossed
the hard quality floor.

### Implementer raw terminal facts

```text
Sol-high:
  first_terminal=FAILED
  harness_failure=worktree_path_resolution
  recovery_attempts=1
  model_quality_failure=false
  final_status=COMPLETE
  public=13_passed_in_1.89s
  hidden_oracle=IMPLEMENTER_ORACLE_PASS
  limitation=pairwise_matching_tensor_scales_batch_x_old_x_new

Terra-high:
  first_terminal=COMPLETE
  recovery_attempts=0
  final_status=COMPLETE
  public=5_passed_in_1.88s
  hidden_oracle=IMPLEMENTER_ORACLE_PASS
  limitation=focused_public_and_pm_hidden_oracle_only

Luna-max:
  first_terminal=COMPLETE
  recovery_attempts=0
  final_status=COMPLETE
  public=6_passed_in_2.34s
  hidden_oracle=IMPLEMENTER_ORACLE_PASS
  limitation=focused_public_and_pm_hidden_oracle_only
```

### Implementer selection

`gpt-5.6-terra/high` is selected. It meets every hard gate, finished fastest
among valid attributable timings, and produced the only sort/search
implementation rather than a quadratic old-width/new-width match tensor. Sol's
harness failure is excluded from model quality, but its frontier tier offers no
observed quality advantage. Luna reaches the same correctness floor but is
slower here and produces the less scalable realization.

## Reviewer gold contract

The anonymous fixture contained six gold findings:

1. critical: survivor autograd severed by `state.detach()`;
2. critical: caller-owned `new_member_keys` mutated in place;
3. critical: new-layout sentinel/duplicate validation absent;
4. high: nonfinite inactive source state accepted;
5. high: forbidden member loops plus `.tolist()`/`.item()` host paths;
6. medium: value-only public test admits every defect.

Correct forward zeroing, old-layout validation, shapes/dtypes/device, exact
two-file scope and absence of RNG/global/compatibility behavior were protected
nonfindings.

## Reviewer results

| Profile | Critical semantic recall | All-gold recall | False positives | Severity calibration | Elapsed |
|---|---:|---:|---:|---|---:|
| Sol-high | 3/3 | 6/6 | one high subclaim: aggregate validation bools incorrectly treated as forbidden | under-called all three critical defects as high | 84.82 s |
| Terra-high | 3/3 | 6/6 | 0 | best overall; over-called inactive nonfinite as critical | unavailable: returned fabricated identical midnight timestamps |
| Luna-max | 3/3 | 6/6 | 0 | detach critical; two other critical defects called high; lower defects under-called | 43.75 s |

All three reached the hard floor: every critical defect was identified with the
correct causal mechanism and no critical false positive. No review repair turn
was needed. Terra's timestamp is an output-metadata defect, so its elapsed cost
is unavailable rather than guessed.

### Reviewer raw terminal facts

```text
Sol-high:
  status=COMPLETE
  findings=6
  gold_semantics_found=6_of_6
  critical_semantics_found=3_of_3
  false_positive=multiple_aggregate_validation_bools
  elapsed_seconds=84.817

Terra-high:
  status=COMPLETE
  findings=6
  gold_semantics_found=6_of_6
  critical_semantics_found=3_of_3
  false_positive=none
  elapsed_seconds=unavailable_invalid_self_report

Luna-max:
  status=COMPLETE
  findings=6
  gold_semantics_found=6_of_6
  critical_semantics_found=3_of_3
  false_positive=none
  elapsed_seconds=43.747
```

### Reviewer selection

`gpt-5.6-luna/max` is selected. It is non-inferior on the hard critical-quality
contract, has no false positive, supplied a valid measured duration, and is the
fast/affordable declared model tier. Its severity under-calibration is retained
as residual risk: normal assignments must state that every protected-semantics
violation is acceptance-blocking even when labelled `high` rather than
`critical`.

## Cost accounting limitation

The native-child runtime exposed model identity and self-reported timestamps,
but no per-agent token, compute or billing amount. Therefore exact monetary
cost is recorded as `monetary_cost_unavailable` for every variant. No synthetic
dollar estimate is used. Selection uses hard quality first, then valid elapsed
time, repair count, implementation complexity and the platform's declared model
tier as explicit proxies. A future benchmark should consume platform-native
usage telemetry if that surface becomes available.

## End-to-end retry rule adopted

A first failure never blocks sibling variants or the benchmark. The failed
variant may receive bounded repair turns under the unchanged contract until it
passes; every model turn, test and review cycle is accumulated. Harness defects
are recorded separately. A profile is compared only by the total cost required
to reach accepted completion, while a genuinely exhausted non-completion
remains a valid failed sample.

## Control-plane impact and closure

| Changed surface | Consumer | Required closure |
|---|---|---|
| normal implementer/reviewer profiles | native child registry after startup | set selected model/effort; harness audit; session restart |
| temporary benchmark profiles and roles | `.codex/config.toml` and harness discovery | remove registrations and files together |
| benchmark contract test | workflow regression suite | assert winners and retirement instead of six live variants |
| current work and restart handoff | root Project Manager | record completed benchmark and safe restart boundary |

The selected profiles own no scientific authority. External Pro remains the
scientific authority; Project Manager remains the sole code-side acceptance
owner.

## Historical harness repair adopted from the A rerun (superseded policy)

The first Sol-high failure was caused by a copied worktree UUID from another
task, not by implementation reasoning. Isolated-worktree identity is now
machine-resolved by `scripts/hmasd_workspace_ticket.py`:

- PM creates a ticket from the actual worktree, Git administrative identity,
  exact base commit and allowed paths;
- a child resolves the ticket before editing and never receives authority to
  guess or substitute the absolute path;
- PM verifies the same ticket after return, including the exact changed-path
  scope;
- a mismatch fails before task code is touched and is recorded as harness cost.

The focused harness tests cover correct resolution without child Git,
cross-UUID substitution, path traversal, base mismatch and out-of-scope writes.
