# Accepted Disposition — Benchmark Identifiability G0 Field 5

## Decision

`ACCEPT_CODE_READY_NONCALENDAR_HETEROGENEOUS_TRACKING_G0`

The focused clarification is complete and valid. The executable scientific
contract is the full Convergent response in:

- `docs/external-review/rounds/20260720_benchmark_identifiability_contract_followup/41_PRO_CONVERGENT_RAW.md`

with exactly one repaired observation-table row from:

- `docs/external-review/rounds/20260720_benchmark_identifiability_field5_clarification/41_PRO_CONVERGENT_RAW.md`

No other part of the frozen contract is reopened or changed.

## Exact Repair

Common observation field 5 is:

```text
mean_{i in A_t}(abs(g_i-x_i)/4)
```

Its closed numerical range is `[0,1]`. The ordinary-access arm `D` retains the
field. The matched calendar/static recurrent null `C` replaces it with exactly
zero before actor, critic, rollout storage and replay, together with the other
already registered masked fields.

## Authorized Next Boundary

The Code Implementation Manager may implement the unchanged
`NONCALENDAR_HETEROGENEOUS_TRACKING_G0` contract using the minimal file boundary
and reuse ledger frozen by the full Convergent response. This disposition
authorizes implementation and focused code verification only. It does not
launch training, alter the registered budget or thresholds, select a successor,
or count as an evidence-bearing research iteration.
