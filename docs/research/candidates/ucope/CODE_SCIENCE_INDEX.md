# UCOPE code-science index

Candidate: `CAND-VSP-07-UCOPE@adversarial-revision-v6`

Current treatment: `UCOPE-A1-COUNT-STATE-EXACT-ENUMERATION`

Stage: derivation; treatment `A`; `formal=false`.

Status: technically accepted registered result. The source was frozen at
`61f84b6f419df4c64078e37fdba9eff080a0361f`; the single registered probe was
`ucope_a1_count_state_exact_enumeration_61f84b6f_r1`. Its retained artifact
passed independent mechanical verification and is published byte-for-byte as
`UCOPE_A1_COUNT_STATE_EXACT_ENUMERATION_RESULT.json`. Scientific intake and any
later direction decision remain with Explorer.

## Accepted registered result

The unique frozen branch is
`A1_COUNT_STATE_DECISION_RELEVANCE_SUPPORTED` with `first_failure_id=null`.
The artifact retains all 48 rows over 16 reused histories and exactly 96
regime-conditioned rational cells. It records UCOPE expected physical-time AUC
`26571/20000`, count-blind AUC `1`, exact gain `6571/20000`, terminal coverage
`1097/1250`, and terminal-coverage gain `236/625`. All eleven prohibited
activity counters are zero. This is a family-local A1 technical result only;
it does not authorize B, C, External Pro, or a portfolio decision.

The published JSON is byte-identical to the accepted raw artifact (SHA-256
`67f234b3dee9931d13cc98bc705fee6cdf64a273f51d4ad702b198827720e7a5`).

## Narrow question and frozen scope

A1 asks whether, inside one frozen finite block-persistent marked-renewal
family, completed first-hit counts can change the Bayes-optimal trial-5
effective period when every allowed non-count state is matched. It makes no
task-return, acquisition, retirement, transfer, learner, or portfolio claim.

The exact family has anonymous cells `c1,c2`, each with weight `1`; raw periods
`s,long_a,long_b` quotient to `S,L,L`; durations are `d_S=1,d_L=2`; the
physical horizon is three. `long_a` and `long_b` have byte-identical execution
laws. The persistent latent regime has prior `1/2` and hazards `9/10` when
period and regime align and `1/10` otherwise. The pre-outcome prefix is
`(c1,S),(c2,S),(c1,L),(c2,L)` and trial 5 chooses at `c1`.

For the completed version-closed ledgers,

```text
rho = L_THETA_S / (L_THETA_S + L_THETA_L)
h_S = 1/10 + (4/5)rho
h_L = 9/10 - (4/5)rho
UCOPE(S) = 2h_S
UCOPE(L) = h_L
```

The primary count-blind comparator is objective-matched `CB-AUC`, with scores
`S=1,L=1/2` and canonical `S`-before-`L` ties. `SG-RATE` is emitted only as a
secondary diagnostic and uses the same frozen count-blind scores
`S=1,L=1/2`; it selects `S` for HS, HL and every row in all three modes. Every
acceptance value is represented with `fractions.Fraction` and serialized as a
canonical rational string; float and epsilon admission are rejected.

## Enumeration and invariant surface

The pure enumerator makes exactly three `enumerate_histories` calls over the
canonical 16 lexicographic histories: primary persistent hazards, homogeneous
`1/2` hazards, and an independently redrawn trial-5 regime. The same 16
histories are reused in each mode: 48 serialized rows and exactly 96
regime-conditioned rational cells. Alias, identity, state, tape and censor
checks operate only on retained rows or structural projections and never add a
fourth enumeration.
The primary rows include all 32 regime-joint weights, pooled `N/E`, posterior,
hazards, UCOPE/CB-AUC/SG-RATE scores and actions, margins, and conditional AUC
under both regimes. Independent-redraw prefix history weights remain the
primary persistent mixture, while each row's two trial-5 regime cells are both
exactly half that history weight. They therefore represent a fresh independent
`1/2` current-regime prior rather than the prefix's persistent-regime joint.

The frozen exact aggregate identities checked by source and focused evidence
are:

```text
E[J_AUC^UCOPE] = 26571/20000
E[J_AUC^CB-AUC] = 1
Delta_AUC = 6571/20000
terminal coverage UCOPE = 1097/1250
terminal coverage always-S = 1/2
terminal coverage gain = 236/625
HS=(1,1,0,0): action S, margin 11153/6562
HL=(0,0,1,1): action L, margin 4591/6562
```

The negative-boundary projection retains every homogeneous and independent-
redraw row and requires exact zero AUC difference. Additional pure invariants
cover alias split/merge, administrative-limit-1 censoring, pre-outcome
exposure, fixed tape, matched non-count state, identity permutations,
version-mixing rejection, comparator identity, absence of reward/retirement/
online update/post-outcome filtering, canonical history order, and exact
resource counts. The result retains byte-identical HS/HL non-count-state
witnesses covering opportunity, uncovered set, horizon, Q, costs, censor law,
E, action sequence, executor/partner generations and empty non-count
recurrent/policy state. It also retains the identity-free canonical projection
and the exact zero-activity/forbidden-field witness. Identity labels never
enter a score or key.

## Branch and artifact lifecycle

`build_a1_manifest` emits one total source-revision/run-bound manifest.
`run_a1_probe` applies the fixed precedence:

1. `A1_INVALID_MANIFEST`;
2. `A1_INVALID_ENUMERATION`;
3. `A1_SCIENTIFIC_STOP` with the lowest applicable `S01`-`S12` identifier;
4. `A1_COUNT_STATE_DECISION_RELEVANCE_SUPPORTED`.

Structural/literal/derived-table failures are retained as self-consistent
`enumeration_errors` and select `A1_INVALID_ENUMERATION`. A complete retained
predicate witness whose correctly derived S predicate is false instead selects
`A1_SCIENTIFIC_STOP`, records the full ordered stop list and uses its lowest
identifier. The payload-only validator independently derives both diagnostics
and rejects any branch, list or first-failure mismatch without rerunning the
enumerator.

The CLI writes every manifest or artifact once through a same-directory atomic
replacement and refuses an existing destination. `exercise` accepts only
`technical_only=true`, emits no rows or boundary evidence, sets `branch=null`,
and cannot admit a scientific terminal. `registered-probe` rejects a
technical-only manifest. After a branch exists, the validator inspects only
the retained payload against frozen literal tables and branch precedence. It
does not call `run_a1_probe`, `_build_a1_evidence`, or `enumerate_histories`, so
validation cannot become a second probe. It rejects drift, floats, incomplete
activity counters, nonzero runtime activity, or missing/tampered witnesses.

Before a registered claim, the CLI verifies that all four claim-bearing source
paths are tracked and byte-clean relative to the declared HEAD. It then
atomically creates `registered_claim.json` in the run root, binding assignment,
candidate, run ID and source revision before enumeration. The only result name
is `raw_result.json`; an existing claim or result fails closed, and the CLI has
no alternate output option. After the claim exists, any failure is terminal and
cannot be recovered by another output path or second invocation.

The registered artifact has zero environment transitions, policy, learner,
trainer, optimizer and evaluation calls, stochastic draws, seeds, gradients,
retirement actions, and task-return observations. The runner neither retries
nor provides a rescue or alternate family.

## Traceability

| Claim ID | Code path and symbol | Observable invariant | Focused evidence | Alternate explanation excluded |
|---|---|---|---|---|
| `UCOPE_A1_MANIFEST` | `experiments/candidates/ucope/exact_enumerator.py::build_a1_manifest`; `::validate_a1_manifest` | Total exact literals, frozen source/run identity, full-mode caps, no float/epsilon | `test_a1_manifest_is_total_exact_and_rejects_float_or_literal_drift` | Configuration drift or an unfrozen source revision cannot be interpreted as A1. |
| `UCOPE_A1_ENUMERATION` | `::enumerate_histories`; `::_build_a1_evidence`; `::_mode_payload` | Exactly three calls produce canonical 16 primary rows, 32 joint weights, 16 rows per negative boundary, 48 rows/96 regime cells, exact AUC and coverage aggregates | `test_a1_primary_table_has_all_exact_joint_weights_and_named_aggregates`; `test_a1_validator_rejects_history_missing_duplicate_and_order_drift`; `test_a1_registered_cli_enumerates_exactly_three_modes_and_validator_never_reruns` | Sampling, omitted histories, duplicate histories, extra invariant enumerations, redraw of the primary regime, or approximate arithmetic cannot produce the table. |
| `UCOPE_A1_LEDGER` | `::update_ledger`; `::posterior` | Pre-outcome at-risk `E`, uncensored first-hit `N`, immutable family/executor generation | `test_censoring_is_unknown_and_ledgers_are_immutable_and_version_closed`; `test_a1_validator_rejects_frozen_semantic_corruptions` | Censor-as-failure, outcome-derived exposure, or version pooling cannot drive the switch. |
| `UCOPE_A1_COMPARATORS` | `::_evaluate_history`; `::_a1_row_payload` | `CB-AUC` is primary; secondary `SG-RATE` has frozen count-blind `S=1,L=1/2` and selects S in every mode | `test_matched_histories_have_exact_posterior_hazards_actions_and_margins`; `test_a1_primary_table_has_all_exact_joint_weights_and_named_aggregates`; `test_a1_boundaries_alias_identity_tape_state_and_censor_are_explicit` | A posterior-dependent SG comparator cannot be mistaken for the frozen secondary null. |
| `UCOPE_A1_BOUNDARIES` | `::_build_a1_evidence`; `::_alias_projection_witness`; `::_identity_projection_witness`; `::_matched_noncount_state_witness`; `::_stop_failures` | Homogeneous/redraw exact zero effect; structural alias proof; byte-identical matched state and identity-free projections; censor/tape/version witnesses | `test_a1_boundaries_alias_identity_tape_state_and_censor_are_explicit`; `test_a1_matched_state_identity_and_forbidden_dependency_witnesses_are_tamper_evident` | Alias representation, label leakage, unmatched non-count state, filtering, or lifecycle bookkeeping cannot manufacture the result. |
| `UCOPE_A1_BRANCH` | `::select_a1_branch`; `::_assemble_a1_result`; `::validate_a1_artifact` | Manifest before structural enumeration diagnostics before correctly derived lowest `S01-S12` before support; technical-only has no terminal | `test_a1_branch_precedence_and_lowest_scientific_failure_are_frozen`; `test_a1_invalid_and_scientific_stop_artifacts_are_self_consistent_and_cli_writable`; `test_a1_technical_only_exercise_never_materializes_or_admits_a_branch` | Structural invalidity cannot masquerade as scientific stop, and a valid unfavorable predicate cannot be rejected merely for being false. |
| `UCOPE_A1_ZERO_ACTIVITY` | `::zero_activity`; `::_validate_activity` | All eleven prohibited runtime/activity counters exist and equal zero | `test_a1_zero_activity_is_total_and_nonzero_activity_fails_closed` | Environment, policy, optimization, evaluation, stochastic, retirement, or task-return evidence cannot enter A1. |
| `UCOPE_A1_ONE_SHOT` | `scripts/run_ucope_a1_count_state_exact_enumeration.py::_require_clean_claim_sources`; `::_claim_registered_run`; `::_registered_probe_command` | Four tracked clean source paths; source-bound claim before enumeration; only `raw_result.json`; second claim and alternate output rejected | `test_a1_registered_preflight_and_claim_fail_closed_before_enumeration`; `test_a1_invalid_and_scientific_stop_artifacts_are_self_consistent_and_cli_writable` | Dirty/untracked source, output-path substitution and post-claim retry cannot create another result. |

## Direct consumer compatibility

`tests/experiments/candidates/ucope/test_acquisition_park_certificate.py`
continues to consume `build_family`, `enumerate_histories`,
`run_registered_audit`, the existing dataclasses, and `Terminal.PASS`. The
legacy `ell`/`ell_prime` nominal accessors map read-only to the frozen
`long_a`/`long_b` aliases, so the accepted acquisition-park certificate retains
its exact family constants and historical values. This compatibility surface
does not turn that earlier certificate into the new A1 registered probe.

## Public locators

- `experiments/candidates/ucope/exact_enumerator.py`
- `scripts/run_ucope_a1_count_state_exact_enumeration.py`
- `tests/experiments/candidates/ucope/test_exact_enumerator.py`
- `docs/research/candidates/ucope/CODE_SCIENCE_INDEX.md`
- `docs/research/candidates/ucope/UCOPE_A1_COUNT_STATE_EXACT_ENUMERATION_RESULT.json`

Accepted source commit:
`61f84b6f419df4c64078e37fdba9eff080a0361f`. The accepted result commit is the
Git commit containing this index update and the byte-identical public result.
