# UAV temporary service loss G1 implementation plan

> **Required procedure:** use `$hmasd-agile-research-development` for the
> active implementation. Generic Superpowers execution, compatibility work and
> workflow hashes remain disabled.

```text
active_implementation=UAV_TEMPORARY_SERVICE_LOSS_G1
implementation_status=IMPLEMENTED_AND_ACCEPTED_FORMAL_READY
scientific_raw=docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/21_PRO_OPEN_RAW.md
reconciliation=docs/external-review/rounds/20260723_uav_dynamic_service_roster_source_contract/30_PM_SCIENTIFIC_RECONCILIATION.md
design=docs/research/designs/UAV_TEMPORARY_SERVICE_LOSS_G1.md
backend=cpu
torch_threads=1
formal_iteration=18
uav_chain_iterations_remaining=10
focused_acceptance=38_passed_plus_1_final_delta_passed
nonformal_artifact=logs/nonformal_uav_temp_loss_g1_20260723_pm2
independent_review=ACCEPT
```

## Goal

Test whether explicit compact service-lifecycle ownership improves S7-S1
temporary-loss service and rejoin continuity beyond the strongest correctly
masked fixed-slot recurrent controller. A mask-sufficient result is admissible
and must not be rescued.

## Active-line implementation

### 1. Source overlay and ledger

Add one small Scenario-7 temporary-service-loss source that samples the exact
IID and held-out laws, applies service LEAVE before action collection, holds the
absent UAV position at zero velocity, disables its communication links and
restores the same lifecycle after the frozen duration.

Expose current service-active state to both arms but never expose the future
owner, onset, duration or rejoin time. Keep underlying S7-S1 physical and reward
semantics unchanged.

Focused proof: exact distribution boundaries, deterministic reconstruction,
one/two-owner overlap, no future leakage and complete recovery windows.

### 2. Matched continuous recurrent arms

Implement one shared continuous four-action recurrent policy core with two
routing modes:

- `FIXED_MASK_REC` keeps eight physical state slots and excludes inactive rows
  from action/log-probability/PPO loss while freezing/restoring their hidden
  state;
- `PREFIX_NORMALIZED_OPEN_ROSTER` compacts service-active lifecycle rows and
  routes hidden state by lifecycle ownership.

Both modes use the same active-set sum, `log1p(active_count)`, active-fraction
autoregressive prefix, tanh-Gaussian action support and exact trainable
parameter count. The critic receives identical current centralized state.

Focused proof: inactive likelihood exclusion, exact hidden freeze/restore,
survivor continuity, row/slot permutation behavior, parameter/action/exposure
matching and checkpoint continuation.

### 3. Controls, metrics and analyzer

Implement the evaluation-only constructive and no-reallocation controls,
`J_event`, `J_rejoin`, `Q_ordinary`, worst-cell access, paired hierarchical
bootstrap and the exact seven first-match branches. Treat the no-disturbance
empty event union as `J_event=1.0`.

Focused proof: metric boundary arithmetic, strict/equality comparisons,
source-identifiability precedence, tampered provenance rejection and formal
analyzer rejection of nonformal artifacts.

### 4. Bounded nonformal acceptance

Run focused CPU one-thread tests and one small nonformal train/evaluate/analyze
exercise using reduced implementation-only exposure. It must prove operational
closure, not produce or preview a scientific result. Artifacts remain under
`logs/` and outside tracked source.

### 5. Formal iteration 18

After PM accepts the implementation and freezes the exact executable evidence
contract, commit and push the source, then assign exactly one foreground
CPU-only `train -> evaluate -> analyze` run to the registered
`hmasd-experiment-operator`. The same immutable command may resume only through
the validated update/batch journal; it may not change source, seeds, exposure
or parameters.

The `train` phase first evaluates the exact formal constructive and
no-reallocation controls. This is first-match compute pruning, not a new gate:

- if `mean_constructive_J_event < 0.90` or the paired 95% lower bound of
  `constructive - no_reallocation` is `<= 0.10`, perform zero learned training
  and return the registered `SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1` after
  exact artifact validation;
- otherwise continue the unchanged learned budget and reuse those exact
  control rows in evaluation.

The representative prelaunch control result (`0.943997` constructive versus
`0.967834` no-reallocation) makes source failure plausible but is not itself a
formal conclusion.

The accepted runner persists source-screen, update and evaluation-batch
progress with direct immutable writes and same-command recovery. This is an
operational safeguard for the multi-hour CPU path and does not change final-only
checkpoint selection or any scientific gate.

Formal exposure per learned arm and paired replicate is 16 environments × 500
steps × 200 updates = 1,600,000 transitions, four PPO passes per update. Use
three paired replicates and final checkpoints only. Evaluate four cells under
deterministic and stochastic action with 128 episodes each. Write
`docs/report/ITERATION_18.md` only after a valid terminal result.
