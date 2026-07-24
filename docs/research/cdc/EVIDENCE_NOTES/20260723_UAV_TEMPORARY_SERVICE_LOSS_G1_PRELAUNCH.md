# UAV temporary service loss G1 prelaunch

Date: 2026-07-23

Status: implementation accepted; formal iteration 18 not yet launched

## Scientific boundary

This source asks whether explicit compact service-lifecycle ownership improves
temporary-loss service and rejoin continuity beyond a correctly masked
fixed-slot recurrent reduction in unchanged S7-S1 physics. Charging, demand
bursts, terminal loss and composed disturbances remain outside G1.

The external-Pro source contract and PM reconciliation remain authoritative:

- `docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/30_PM_SCIENTIFIC_RECONCILIATION.md`
- `docs/research/designs/UAV_TEMPORARY_SERVICE_LOSS_G1.md`

## Accepted realization

- The physical fleet remains eight UAVs; the dynamic object is the
  service-active roster.
- Loss is applied before action collection, removes communication and actor
  likelihood exposure, freezes the absent lifecycle hidden state and restores
  the same lifecycle on rejoin.
- Both learned arms retain the existing S7-S1 local physical and communication
  information. Fixed owner blocks are anonymously repacked and inactive peers
  are removed; no future ledger or new global observation is exposed.
- Actions use an exact tanh-Gaussian transform with stored pre-tanh replay
  latents.
- Access is the minimum over exactly four cells. Deterministic and stochastic
  modes are retained separately but averaged within each cell.
- The constructive control uses the complete ledger; no-reallocation is
  ledger-blind. Both are evaluation-only.

## Proof-sized acceptance

The PM combined run passed 38 focused tests in 139.23 seconds. After the final
training-manifest content binding was added, its focused mutation regression
also passed independently. The settled package passed compilation and diff
checks. One independent integrated review returned `ACCEPT` with no actionable
findings.

The registered experiment operator completed:

```text
run=logs/nonformal_uav_temp_loss_g1_20260723_pm2
formal=false
backend=cpu
torch_threads=1
train_status=TRAIN_COMPLETE
evaluation_status=EVALUATION_COMPLETE
analysis_status=COMPLETE
operational_valid=true
result=NONFORMAL_UAV_TEMP_LOSS_G1_EXERCISE_COMPLETE
```

The formal validator rejected this artifact as nonformal, as required. It is
operational evidence only and consumes no conclusion-bearing iteration.

## Control residual

A bounded 500-step representative exact-ledger diagnostic produced:

| Control | J_event | Q_ordinary | J_rejoin |
|---|---:|---:|---:|
| one-relay constructive | 0.788971 | 0.572962 | 0.788802 |
| two-relay constructive | 0.943997 | 0.682727 | 0.944687 |
| ledger-blind no-reallocation | 0.967834 | 0.754232 | 0.956037 |

Two relays are the frozen constructive realization. Its absolute event score
clears 0.90 in this episode, but it trails the blind control by 0.02384 rather
than exceeding it by the required strict margin. This is legitimate risk that
the disturbance is not load-bearing; it is not permission to tune a preferred
result.

## Formal compute order

The formal `train -> evaluate -> analyze` command first evaluates the complete
registered control support with three paired replicates, four cells and 128
episode IDs, then applies the frozen 10,000-resample paired bootstrap.

- `mean_constructive >= 0.90` passes at equality.
- `LCB95(constructive - no_reallocation) > 0.10` is strict; equality fails.
- If either predicate fails, zero learned optimization is performed and the
  existing first-match branch
  `SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1` is returned.
- If both pass, the exact registered learned exposure proceeds and reuses the
  already committed control rows.

Source screening, training updates, final checkpoints and evaluation batches
use direct-write, content-bound continuation records. Repeating the identical
command may resume; source, configuration, seeds, episode coordinates,
optimizer, RNG, audit state and evidence content may not change. These runtime
integrity digests are not workflow or Git handoff hashes.

The next conclusion-bearing iteration is 18. Ten UAV-chain iterations remain.
