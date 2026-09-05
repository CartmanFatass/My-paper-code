# VNFC N7 direct-return B01: source feasibility and CM handoff

Date: 2026-09-05. Science card:
`VNFC_N7_DIRECT_RETURN_B01_SCIENCE_CARD_20260905.md`.
Card/archive commit: `4cee529e2ee2ab685b9314fea5637fe7aea6c623`.
Responsible DM: `/root/dm_am_vnfc_direct_b`; existing CM: `/root/cm_am_vnfc_e01`.

This records the completed read-only CM mapping and freezes a bounded implementation objective
for the selected B. It records no source acceptance, experiment, new timing or performance result.
Root integrates direction records and owns the shared Portfolio, audit and owner-console
application. No duplicate Pro request is needed.

## Completed source mapping

CM inspected source at `df9ac9fa7a75edbd9ba276ba9d9a0423976baa52` in the clean independent
worktree `C:/Projects/HMASD-worktrees/cm-vnfc-direct-b-map-20260905`. It read the full Pro response
and current evidence-spec §11.8–11.9. It ran no experiment, test or build and edited no source.
The following is a DM summary of that completed return.

| Existing surface | Reusable computation | Necessary adaptation or limit |
| --- | --- | --- |
| `scripts/run_vnfc_bpcr_b_explore.py` | `_SeedRNG`, `_build_world`, initialization, rollout/PPO and physical action decoding | `_build_world` supports N7; old configuration, rosters and fixed 96-transition arrays need adaptation |
| `scripts/run_vnfc_bpcr_r02.py` | `CanonicalOpaqueRankForward`, `build_canonical_model_classes` | Use corrected canonical forward/forced-command/inverse mapping; do not install the historical gate/publication system |
| R09 `empirical_training.py` | `_model_inputs`, `make_optimizer` and initialization shape work | Do not call the old `train_update` path that reruns sampled actions rather than replaying the collected forced command |
| R09 `training.py` | `gae_terminal`, `normalize_advantages`, `ppo_loss` | `frozen_minibatches` requires 96 entries; the new 192-transition permutation/minibatch loop is explicit |
| R09 `torch_models.py` | Actual MAPR4 and DirectSetAR topology | Use the R02 canonical wrappers, retain zero residual output at DIRECT initialization, report actual learning |
| R09 `native_backend.py` | `NativeInteractiveBatch` reset/step/BCRH/close | The default loader assumes MSVC/DLL; a scoped Linux shared-library adapter is needed for `wsl_4070` |

Here R09 means `experiments/candidates/variable_n_fleet_churn_bpcr_r09/`.
`NativeInteractiveBatch` supports the real environment path without the old
`PairedPrimaryShadowBatch` dual-host verification chain. Its
`bcrh(include_candidate_records=False)` still executes the native scorer/checker; it omits Python
candidate records, not controller semantics. The existing headroom Linux build uses an
`intrin.h` compatibility header and suitable native compilation flags. Reuse that narrow pattern
without changing R09 C++ environment dynamics or adding E01's four-thread team.

CM confirmed N7 construction, six post-loss decisions, 240 accumulated native ticks, the repaired
canonical action path and CPU float64 implementation. This is source evidence, not an executed
new N7 training chain.

## Exact planned optimization and work

Preserve CPU float64, terminal reward, actual GAE/PPO functions and AdamW configuration:
learning rate 3e-4, betas (0.9, 0.999), epsilon 1e-8, decay 1e-4 on the existing decay group and
zero on the existing plain group, gradient-norm clipping 0.5. Current PPO uses ratio clip
[0.8, 1.2], value coefficient 0.5 and entropy coefficient 0.01. Keep the existing terminal
GAE/advantage semantics; do not substitute a superficially similar trainer default.

| Planned work | Per learning arm | Entire object |
| --- | ---: | ---: |
| Training episodes | 2,048 | 4,096 |
| Training joint transitions | 12,288 | 24,576 |
| Collect/update rounds | 64 | 128 across arms |
| PPO epochs × minibatches per round | 4 × 8, minibatch 24 | matched arms |
| Optimizer steps / backward calls | 2,048 | 4,096 |
| Learned-policy evaluation episodes | 192 | 384 |
| Fixed BCRH evaluation episodes | none | 64 |
| All complete episodes | 2,240 | 4,544 including BCRH |
| All joint decisions | 13,440 | 27,264 including BCRH |
| All native ticks | 537,600 | 1,090,560 including BCRH |

These totals derive from the selected card and inspected trainer arithmetic, not actual exposure.
The old R02 result's 2,048 total optimizer steps belong to both arms; its phrase “2,048 steps
each per seed” is erroneous. The new 2,048 per-arm count follows from 32 episodes per round.
The new runner must print actual counts and the parameter-displacement exposure line.

## Bounded engineering objective and owned paths

Implement the one new scientific card as a fresh, readable research runner, preserving its two
actual learners, fixed BCRH reference, fresh seeds, N7 population, complete task return and final
checkpoint as the primary readout. Keep the cumulative complete 2,700s bill and report actual
implementation cost separately from the old exact-census burden.

Owned write paths:

- `scripts/run_vnfc_n7_direct_b01.py`: one argparse entry, fixed default card seeds, one result root.
- `experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`: object-specific computation or
  the narrow Linux loader if it keeps the runner readable; no framework or registry.
- `tests/experiments/candidates/variable_n_fleet_churn_n7_direct_b01/`: focused changed-path check.
- Direction-local implementation/review evidence for this object under
  `docs/research/candidates/variable_n_fleet_churn/`.

Existing R01/R02, R09, headroom native sources and shared core are read-only reuse inputs for this
slice. If implementation requires a modification there, return the concrete function, scientific
impact and minimal change for DM/CM scope adjustment. Do not silently broaden ownership or
reconstruct an old scientific object. CM and implementer are not alone in the codebase: use
isolated worktrees and preserve other sessions' edits.

The minimal path is:

1. Build paired fresh N7 worlds from the new train/evaluation seed domains. Use 16 episodes per
   failed zone per round. Separate initialization/action RNG domains from paired exogenous worlds.
2. Construct the two canonical R02 models and existing optimizer. Collect 192 joint transitions
   per round and replay the collected forced commands during four-epoch PPO. Form eight
   24-transition minibatches per epoch. No opaque identity, world tape or administrative
   seed/episode metadata enters actors.
3. Evaluate initial, round 32 and round 64 on the fixed 64-episode panel, 32 per failed zone.
   Evaluate BCRH once there. Keep training/evaluation episode identities disjoint.
4. Publish a compact summary, episode-level native primary/context measurements, actual exposure
   and readable initial/mid/final checkpoints. Report all selected contrasts, each failed zone,
   DIRECT parameter/residual activity and per-round training information. Final stays primary.
5. Use the real R09 environment through the Linux adapter with one scientific process and
   existing single-thread CPU computation. Ordinary in-process arrays/tensors may batch same-N7
   work while preserving collection/forced-command semantics. No pools, parallel E01 resources,
   shadow-host replication or generic execution machinery.

Engineering Scope Spec §4 additions: none. Standard source/runner/test budgets apply. Report
actual additions and necessary dependency changes; orchestration share is a review signal,
not a reason to pad code or refuse a necessary short output path.

## Focused check and cost boundary

One proportionate check reaches changed N7 collection, real update, evaluation and output, with
the known mapping risks: zone-2 token permutation, presentation-to-physical entities, null/fixed
occupants and forced-command PPO replay. Check primary metrics from native service/demand with
full terminal, matched public learner inputs, nonzero optimizer work, readable summary/checkpoints.
Reuse applicable checks. This is not the old 52/304-row law panel, all-candidate census, full
history replay, double-shadow execution or a new approval gate.

Historical Windows timing is useful but insufficient for new costs:

| Old R02 seed | Recorded complete stage wall | Recorded outer runner wall |
| --- | ---: | ---: |
| 2026090311 | 624.511s | 626.079s |
| 2026090321 | 689.369s | 691.121s |
| 2026090331 | 583.283s | 584.934s |

Those runs trained on N3/N5 with half the new episodes and included old diagnostics/shadow work.
New N7 size, more evaluation, Linux toolchain and batching alter cost. These values do not
establish the new 2,700s fit; E01's 28.11s is not a learner benchmark. Current unknowns are Linux
build/import, each learner's collection/update/evaluation, 384 complete BCRH calls and publication.
Capture applicable timing in the necessary focused engineering check if needed, then use the
card's complete cost law. No independent exact feasibility A or mandatory profiling round is
selected. Do not replace an unknown component with zero or infer savings from a cap ratio.

For any compute-intensive check or result-bearing invocation, commit/push exact source first,
use the configured remote exact-SHA worktree and detached `agent-task`, and run destination-node
memory admission immediately before the invocation. The new first-round cap includes setup/build
and required publication. Freeze the actual focused-check command and non-target inputs in the
existing CM assignment before running it; it must not consume or select the formal new training
seed based on performance. No experiment was run by this source mapping.

Return a concrete correctness/ownership/cost gap if the selected schedule cannot be implemented
within the task. No automatic retries, arm truncation, best-checkpoint selection, R03/E01 reopening
or algorithm-failure declaration follows from an engineering gap. A valid B needs real training
and the primary comparison; source acceptance or process exit alone cannot supply its value.

## Root integration and owner surfaces

Root can use `pro_packets/20260905_validation_method_convergence/OWNER_NEW_CARD_PACKET.json`
with the existing owner-console command for the new-card item and linked VNFC highlight. The
prediction is in the card; no owner prediction was taken and no reply is awaited. Update the
shared record to “new N7 B selected; CM implementation preparation”, keeping recasts two and
Portfolio lifecycle/priority. Transport factual reconciliation remains tracked in the intake;
the raw archive is not overwritten.
