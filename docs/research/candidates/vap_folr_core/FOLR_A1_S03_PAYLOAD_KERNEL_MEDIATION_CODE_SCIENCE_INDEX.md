# FOLR A1 S03 payload-kernel mediation — code/science index

Status: accepted raw result materialized for CPM integration and push;
Explorer scientific intake remains pending. Publication is not complete until
CPM integrates and pushes the bounded result.

## Bound question

For `CAND-VAP-FOLR-CORE@constructive-revision-v6`, this A-level probe asks only
whether a private payload installed into the target owner's S03 at the frozen
post-commit/pre-logits hook reaches the target's fresh first deterministic
policy kernel. It does not measure learning, return, task value, general FOLR
quality, or environment behavior.

The production cell is fixed as
`experiments.candidates.folr_core.registration.registered_cell()` with identifier
`folr_s03_constructed_sensitivity_v1`, target `owner_t@0`, shadow `owner_q@0`,
positive registered logit witness, and legal-action support `[true, true, true]`.
The single accepted raw result contains the six frozen complete deterministic
float32 kernel readouts and six policy forwards from one common snapshot/model,
non-S03 preimage, owner epoch, and token identity.

## Responsibility map

- `experiments/candidates/folr_core/s03_payload_kernel_mediation.py` owns the
  exact six-arm roster, prerequisite admission, same-snapshot execution,
  target-only first-kernel sentinel, lossless float32 kernel serialization,
  equality/freshness witnesses, full-vector total variation, frozen decision
  precedence, validation, analysis, and JSON I/O.
- `scripts/run_folr_a1_s03_payload_kernel_mediation.py` owns wiring only:
  production `run`, read-only `validate`, and read-only `analyze`. The explicit
  `--technical-smoke` route uses `development_registration()` and marks its
  artifact `technical_only=true` and `scientific_terminal_admitted=false`.
- `tests/experiments/candidates/folr_core/test_s03_payload_kernel_mediation.py`
  uses only the development registration and synthetic decision cases. It
  rejects arm, snapshot, identity, clock, legal-support, cached/pending/action,
  RNG, ledger, second-forward, reset-neutral, vector-completeness, resource-cap,
  TV-source, and precedence defects.

The package reuses the stable low-level owners
`s03_binding`, `branch_snapshot`, `reset_manifest`, and `registration`, plus
`VariableRosterEventCore.apply_transaction`. It neither calls nor changes the
historical eight-arm `branches.BRANCHES` / `execute_registered.execute` path.

## Observable invariant

All six arms originate from one captured common pre-write snapshot. Branch
identity is result provenance metadata only. Each transplant arm restores the
same snapshot, writes only target `LifecycleRecord.high_hidden` at the terminal
preframe hook, and invokes the authoritative target-first transaction. Each
reset arm records the same source snapshot, constructs a fresh manifest runtime
with neutral target S03, and invokes the same transaction.

`FirstKernelComplete` is raised immediately after the target sink has delegated
capture of the complete float32 masked logits and softmax probability vector.
Thus the scientific cap is exactly six kernel-producing policy forwards and six
complete kernel readouts, while action selection, action/opportunity RNG,
ledger rows, later-owner forwards, environment transitions, learner/trainer,
optimizer, and return evaluation remain unreachable.

Every kernel records values, shape, dtype, exact little-endian bytes, byte
SHA-256, and typed-vector digest. The actor-preimage digest excludes exactly
S03. Exact TV is `0.5 * sum(abs(p - q))` over the complete probability vectors;
there is no sample, Monte Carlo approximation, epsilon, or materiality gate.

## Frozen decision order

1. `PREREQUISITE_UNAVAILABLE_OR_INVALID`
2. `BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE`
3. `RESET_DOES_NOT_ERASE`
4. `NO_S03_PAYLOAD_EFFECT`
5. `S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED`

The last branch requires exact fixed-payload branch nulls, at least one strictly
positive within-branch payload TV, an exact reset null, and every completed
admission/equality/freshness witness. The code does not authorize rescue, cell
replacement, additional arms, B/C work, or External Pro.

Artifact validity is deliberately separate from positive admission. A complete
six-arm artifact whose raw witnesses canonically recompute to
`BRANCH_LABEL_OR_ALTERNATE_PATH_LEAKAGE` remains a valid frozen negative result;
the validator does not turn that scientific branch into an engineering error.
It still rejects an unsynchronized stored analysis/decision, a partial roster,
an incomplete vector, a non-single-forward/sentinel arm, or activity counters
outside the exact cap.

A failed pre-readout prerequisite has its own canonical zero-arm lifecycle. It
retains the exact failure reasons and cell/config/source identity, requires zero
kernel readouts, policy forwards, lifecycle transactions and all other activity,
and validates/analyzes directly to
`PREREQUISITE_UNAVAILABLE_OR_INVALID`. Any partial arm or nonzero activity makes
that artifact structurally invalid. The CLI treats every successfully
materialized frozen decision as a successful run; only structural, execution or
I/O failures are process failures.

## Publication lifecycle

Canonical result:
`docs/research/candidates/vap_folr_core/FOLR_A1_S03_PAYLOAD_KERNEL_MEDIATION_RESULT.json`.
It is a byte-for-byte materialization of the accepted raw result
`logs/folr_a1_s03_payload_kernel_mediation_eed89a4c_r1/raw_result.json`, whose
SHA-256 is `c8b0165f55d8f0392ece80bf58d72c9f4d696203557e06a8e28d6f1fbcb3a973`.

The accepted source commit is `eed89a4c870a185b5caeac641c52a3fd57dc70b3` and
the run ID is `folr_a1_s03_payload_kernel_mediation_eed89a4c_r1`. Its frozen
decision is `S03_PAYLOAD_MEDIATION_ACCESS_SUPPORTED`: all completed admission
checks are true; fixed-payload TVs are `0` and `0`; reset TV is `0`; and both
within-branch payload TVs are `0.5252223461866379`. The artifact records six
complete deterministic float32 kernel readouts and six policy forwards, with
zero environment episodes, environment transitions, hypothetical transitions,
learner calls, trainer calls, optimizer updates, and return evaluations.

CPM owns technical acceptance and the remaining integration/push lifecycle;
Explorer scientific intake remains pending. No result commit is asserted here,
because it is not known until CPM integrates and pushes this exact file set.
Development smoke output is technical evidence only and is not the candidate
result.

The finite claim boundary is unchanged: this is exact deterministic
S03-to-kernel access in one registered cell only. It establishes no learning,
return, task-value, generalization, promotion, retirement, B/C work, or
External Pro authorization.
