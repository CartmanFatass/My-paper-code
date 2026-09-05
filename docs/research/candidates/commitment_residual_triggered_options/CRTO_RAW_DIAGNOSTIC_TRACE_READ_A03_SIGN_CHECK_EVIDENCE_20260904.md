# CRTO A03 offline G16 sign-check evidence

Date: 2026-09-04. Engineering conclusion: all thirteen recorded row-measurement issues reproduce
exactly. Their sole failing conjunct is **legal G16 >= 0**, not action legality, finiteness or
regret. Native G16 is a signed return; nonnegativity applies to native regret, not generally to
G16. This identifies a concrete conflict between the original A01 validity requirement and the
native scoring domain. It does not change either requirement, accept A03, or interpret phase.

## Bounded reproduction

DM assigned one pure offline check after A03 stopped at the original summary's completeness
issues. Authority read: `CRTO_RAW_DIAGNOSTIC_TRACE_READ_A03_SCIENCE_CARD_20260904.md`, pushed
in DM commit `919e0ba4`. Only this evidence document is owned. No source, gate, test, runtime,
dependency, scientific card or other session's work changed. Section-4 additions: **none**.

Input was the preserved A02 diagnostic summary at
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_phase_native_repro_a02_20260904/attempt01_artifacts/summary.json`,
303,260 bytes, SHA-256 `0d9319231c55775568e1d374e2968741a4edc765ebdfd9067e4a9211845ab8f7`.
The file's bytes and digest matched before the single read. Generating source remains
`8d1c597871b38edc7d5f139f34f5a3ce2941c7d0`; source files inspected locally are unchanged from it.

The check used Python standard-library JSON, math and AST only. It obtained the original source
with `git show 8d1c597871b38edc7d5f139f34f5a3ce2941c7d0:experiments/candidates/commitment_residual_triggered_options/raw_phase_trace_a01/experiment.py`,
extracted `trace_measurement_issues` verbatim (lines 477–506), and executed only that pure
function with its `math` and fixed `TRACE_UPDATES` bindings. No experiment module, NumPy or Torch
was imported, and no source learner function was run. The extracted function's text SHA-256 is
`f5de04623f7df636955a39d1f83036488a7b03dc2069506097c1b89c48e81169`.

The A03 card permits this short local evidence check. Fresh local admission at
2026-09-04T22:04:43.571642Z passed both physical/effective 4-GiB floors with
12,029,145,088 bytes available. Execution used
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` in
`C:/Projects/HMASD-worktrees/cm-crto-resume-20260904`.
The one read took 0.08203190000494942 seconds, below the 30-second cap. Expected RSS was below
256 MiB; peak RSS was not measured. This is not a resource claim. No sweep or per-arm learning
projection applies; no new environment steps, models, predictor/RAW updates or evaluations ran.
The original source and adverse data remain untouched. Post-learner formal-publication test
coverage remains the previously recorded open engineering item; this predicate read is not an
end-to-end publication test.

The local command was fresh `scripts/hmasd_resource_preflight.py admit-memory --out <root>/admission.json`,
followed only on exit 0 by `python <root>/read.py`. Here `<root>` is
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/raw_diagnostic_trace_read_a03_20260904/cm_sign_check/`.
That directory preserves the exact small read script, receipt, and full `sign_check.json` output.

## Exact predicate and row evidence

[experiment.py:495](../../../../experiments/candidates/commitment_residual_triggered_options/raw_phase_trace_a01/experiment.py#L495)
uses this combined predicate:

```python
if (not legal[selected] or not legal_g16
        or not all(math.isfinite(value) and value >= 0.0 for value in legal_g16)
        or not math.isfinite(regret) or regret < 0.0):
    issues.append(f"UPDATE_{update}_ILLEGAL_OR_NONFINITE_ROW_MEASUREMENT")
    break
```

The exact original function returned `UPDATE_u_ILLEGAL_OR_NONFINITE_ROW_MEASUREMENT` for every
u in 252..264, in original order, matching `summary.completeness_issues` exactly. Disaggregating
the predicates over all 208 recorded rows gave:

| Predicate/fact | Count |
| --- | ---: |
| Illegal selected actions | 0 |
| Empty legal G16 vectors | 0 |
| Nonfinite legal G16 values | 0 |
| Legal-vector versus printed legal-mask mismatch | 0 |
| Nonfinite native regrets | 0 |
| Negative native regrets | 0 |
| Native-regret recomputation disagreement at absolute tolerance 1e-12 | 0 |
| Rows containing negative legal G16 | 208 |
| Negative legal G16 scalar entries, counting repeated checkpoints | 689 |

Regret was checked only as `max(legal G16) - selected G16`, clamped at zero as in native source;
no side means, phase aggregates, competence predicates or best/worst checkpoints were accessed.

At every checkpoint the function breaks on row `0/EVALUATION/K8/850/156/0`. Its finite legal
values that fail the nonnegative-G16 condition are:

| Legal action | Recorded G16 |
| --- | ---: |
| KEEP | -0.21869770296967378 |
| TRANSIT-L | -0.26169344944535616 |
| TRANSIT-R | -0.20731001761413503 |

The full adverse values for all 16 unique rows and the first failing row for every checkpoint
are preserved in `sign_check.json`, as well as in the immutable original summary. None was
removed, clipped or replaced. The combined issue name does not distinguish negative G16 from
illegal/nonfinite data; this reproduction does.

## Native sign law and the unresolved scientific contract

The unchanged scoring source supports finite negative G16:

- [host.py:1091](../../../../experiments/candidates/commitment_residual_triggered_options/host.py#L1091)
  computes reward as deliveries minus queue/buffer, overflow, energy and decision-charge costs.
- [host.py:360](../../../../experiments/candidates/commitment_residual_triggered_options/host.py#L360)
  makes terminal potential a negative queue/buffer and energy-deficit cost.
- [host.py:1154](../../../../experiments/candidates/commitment_residual_triggered_options/host.py#L1154)
  computes discounted G16 as the 16-reward discounted sum plus discounted terminal potential,
  divided by a positive episode denominator, with a finiteness check and no zero floor.
- [host_bridge.py:171](../../../../experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/host_bridge.py#L171)
  stores the returned common-future value directly in the legal action vector. There is no
  normalization shift or clipping that would require G16 to become nonnegative.
- [contracts.py:136](../../../../experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/contracts.py#L136)
  requires every legal G16 label to be finite, without requiring a nonnegative sign.
- [evaluation.py:43](../../../../experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/evaluation.py#L43)
  defines native regret as legal maximum minus selected value, rejects materially negative
  regret and returns `max(0.0, regret)`. Its nonnegative domain is distinct from that of G16.

Negative legal G16 is therefore within the native scoring domain; its presence alone is not
evidence of corrupted labels. This read did not regenerate the environment, so it establishes
the recorded sign/predicate conflict and native domain, not independent environment reproduction.

Crucially, [the original A01 card:149](CRTO_RAW_PHASE_TRACE_A01_SCIENCE_CARD_20260904.md#L149)
explicitly requires all G16 values and regrets to be finite and nonnegative. The implementation
matches that literal requirement. Silently dropping its G16-sign condition would alter A01
acceptance, not merely relabel an error message. The current A01 completeness flags and A02
technical branch are preserved.

The minimal question for the DM is whether the separately named A03 reading may explicitly
apply the unchanged native domain—finite signed legal G16 and finite nonnegative regret—while
retaining the original A01 requirement and incomplete disposition. This is a scientific-contract
interpretation for the DM, not a gate change performed here. No A03 measurement, phase effect,
RAW competence or residual interpretation is accepted by this engineering note. Stop reached:
one pure reproduction and concrete conflict returned; no repair or rerun follows automatically.
