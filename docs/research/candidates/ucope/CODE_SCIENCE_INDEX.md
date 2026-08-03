# UCOPE count-state D1: code-science index

Candidate: `CAND-VSP-07-UCOPE@adversarial-revision-v6`

Treatment: proof-sized deterministic `UCOPE-COUNT-STATE-D1`

Status: exact finite-family implementation evidence only. It does not establish
task return, acquisition, retirement, transfer, or multi-step value.

## Frozen contract

The family has anonymous equal-weight cells `c1,c2`, effective periods
`{s}->S`, `{ell,ell_prime}->L`, durations `d_S=1,d_L=2`, and a persistent
latent `Theta` with prior `1/2`. `ell` and `ell_prime` share one exact execution
law. The four forced trials are `(c1,S),(c2,S),(c1,L),(c2,L)`; the fifth trial
chooses `S` or `L` at `c1`. Coverage resets each trial and the physical horizon
is three.

```text
h(theta,p)=9/10 when theta=p, otherwise 1/10
rho=L_S/(L_S+L_L)
h_S=1/10+(8/10)rho
h_L=9/10-(8/10)rho
UCOPE(S)=2h_S
UCOPE(L)=h_L
```

The objective-matched count-blind null uses the same prior and physical-time
AUC objective but cannot read realized `N,E`; it therefore selects `S` with
value `1`. The secondary `SG-RATE` diagnostic is explicitly `argmax(h_S,h_L)`
with the same precommitted `S` tie-break. It does not enter the primary pass or
the reported `Delta_AUC`.

All count, likelihood, posterior, hazard, score, probability, expectation, and
margin calculations use `fractions.Fraction`; no floating approximation enters
the result.

## Complete 16-history output

`E` and `N` use order `(S,c1),(S,c2),(L,c1),(L,c2)`. `J5` is the selected
fifth-trial expected physical-time AUC.

|bits|E|N|rho|hS|hL|U_S|U_L|CB|SG|action|J5|
|---|---|---|---|---|---|---|---|---|---|---|---|
|0000|(1, 1, 1, 1)|(0, 0, 0, 0)|1/2|1/2|1/2|1|1/2|S|S|S|1|
|0001|(1, 1, 1, 1)|(0, 0, 0, 1)|1/82|9/82|73/82|9/41|73/82|S|L|L|73/82|
|0010|(1, 1, 1, 1)|(0, 0, 1, 0)|1/82|9/82|73/82|9/41|73/82|S|L|L|73/82|
|0011|(1, 1, 1, 1)|(0, 0, 1, 1)|1/6562|657/6562|5905/6562|657/3281|5905/6562|S|L|L|5905/6562|
|0100|(1, 1, 1, 1)|(0, 1, 0, 0)|81/82|73/82|9/82|73/41|9/82|S|S|S|73/41|
|0101|(1, 1, 1, 1)|(0, 1, 0, 1)|1/2|1/2|1/2|1|1/2|S|S|S|1|
|0110|(1, 1, 1, 1)|(0, 1, 1, 0)|1/2|1/2|1/2|1|1/2|S|S|S|1|
|0111|(1, 1, 1, 1)|(0, 1, 1, 1)|1/82|9/82|73/82|9/41|73/82|S|L|L|73/82|
|1000|(1, 1, 1, 1)|(1, 0, 0, 0)|81/82|73/82|9/82|73/41|9/82|S|S|S|73/41|
|1001|(1, 1, 1, 1)|(1, 0, 0, 1)|1/2|1/2|1/2|1|1/2|S|S|S|1|
|1010|(1, 1, 1, 1)|(1, 0, 1, 0)|1/2|1/2|1/2|1|1/2|S|S|S|1|
|1011|(1, 1, 1, 1)|(1, 0, 1, 1)|1/82|9/82|73/82|9/41|73/82|S|L|L|73/82|
|1100|(1, 1, 1, 1)|(1, 1, 0, 0)|6561/6562|5905/6562|657/6562|5905/3281|657/6562|S|S|S|5905/3281|
|1101|(1, 1, 1, 1)|(1, 1, 0, 1)|81/82|73/82|9/82|73/41|9/82|S|S|S|73/41|
|1110|(1, 1, 1, 1)|(1, 1, 1, 0)|81/82|73/82|9/82|73/41|9/82|S|S|S|73/41|
|1111|(1, 1, 1, 1)|(1, 1, 1, 1)|1/2|1/2|1/2|1|1/2|S|S|S|1|

Exact aggregate result:

```text
terminal=PASS_NARROW_COUNT_STATE_RELEVANCE
E[J_AUC^UCOPE]=26571/20000
E[J_AUC^CB-AUC]=1
Delta_AUC=6571/20000
H_S action=S, rho=6561/6562, margin=11153/6562
H_L action=L, rho=1/6562, margin=4591/6562
homogeneous-hazard count effect=0
independent-redraw count effect=0
```

## Traceability

| claim_id | frozen_assertion_path_and_section | code_path::symbol | observable_invariant | focused_test::test_name | alternate_explanation_excluded |
|---|---|---|---|---|---|
| UCOPE_D1_QUOTIENT | this file §Frozen contract | `experiments/candidates/ucope/exact_enumerator.py::validate_family` | Exact family/version, equal cells, `{s}->S`, `{ell,ell_prime}->L`, alias-law equality, structural Qstr, durations and pre-outcome tape | `tests/experiments/candidates/ucope/test_exact_enumerator.py::test_effective_period_alias_split_and_merge_are_execution_equivalent`; `::test_family_contract_failures_stop_before_enumeration` | Nominal aliases, partner labels, malformed support, and post-outcome schedule choice cannot manufacture a count effect. |
| UCOPE_D1_LEDGER | this file §Frozen contract | `experiments/candidates/ucope/exact_enumerator.py::update_ledger` | Immutable version-keyed `N/E`; censoring makes no observation rather than a miss | `::test_censoring_is_unknown_and_ledgers_are_immutable_and_version_closed` | Censor-as-failure, stale version, and shared mutable state are rejected. |
| UCOPE_D1_EXACT_ENUMERATION | this file §Complete 16-history output | `experiments/candidates/ucope/exact_enumerator.py::enumerate_histories`; `::_evaluate_history` | All 16 histories have exact posterior, hazards, UCOPE, CB-AUC, SG-RATE, action, probability and fifth-trial AUC | `::test_all_histories_are_exact_complete_and_canonical_output_is_byte_stable` | Sampling noise, float rounding, history omission, or output-order effects cannot explain the result. |
| UCOPE_D1_MATCHED_SEPARATION | this file §Exact aggregate result | `experiments/candidates/ucope/exact_enumerator.py::run_registered_audit` | `H_S` selects S and `H_L` selects L with the registered exact margins while CB-AUC selects S in both | `::test_matched_histories_have_exact_posterior_hazards_actions_and_margins` | The separation is not a non-count-state or objective mismatch. |
| UCOPE_D1_BOUNDARIES | this file §Exact aggregate result | `experiments/candidates/ucope/exact_enumerator.py::run_registered_audit` | Homogeneous hazards and an independent pre-trial-five redraw both make realized counts redundant with exact zero increment | `::test_homogeneous_and_independent_redraw_boundaries_are_exact_zero_effect` | A generic preference for S, raw duration, or count bookkeeping alone is not reported as identification. |
| UCOPE_D1_INVARIANTS | this file §Exact aggregate result | `experiments/candidates/ucope/exact_enumerator.py::run_registered_audit` | Alias split/merge, pre-outcome tape, state-clone order, recurrence/version closure, censoring and partner-label permutation all hold | `::test_pre_outcome_tape_state_clone_and_partner_labels_cannot_change_result`; `::test_registered_audit_passes_exact_narrow_count_state_contract` | Identity, enumeration order, mutation, recurrence drift, and alias representation cannot drive the result. |

## Bounded execution

The run enumerates sixteen exact histories and performs no environment step,
training update, task-return rollout, parameter tuning, or rescue experiment.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "from experiments.candidates.ucope.exact_enumerator import run_registered_audit as run; r=run(); print('terminal='+r.terminal.value); print('rows='+str(len(r.rows))); print('expected_ucope_auc='+str(r.expected_ucope_auc)); print('expected_cb_auc='+str(r.expected_cb_auc)); print('delta_auc='+str(r.delta_auc)); print('all_invariants='+str(all(v for _,v in r.invariants)))"
```

```text
terminal=PASS_NARROW_COUNT_STATE_RELEVANCE
rows=16
expected_ucope_auc=26571/20000
expected_cb_auc=1
delta_auc=6571/20000
all_invariants=True
```

Fresh focused validation:

```text
12 passed in 0.14s
```

The complete row-level canonical output was also emitted by
`run_registered_audit().to_bytes()`; the table above records every row and
field needed to reproduce it. The accepted revision is the exact commit
containing this index, source, and mirrored test.
