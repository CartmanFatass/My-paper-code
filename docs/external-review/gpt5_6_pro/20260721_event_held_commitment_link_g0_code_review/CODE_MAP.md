# EVENT_HELD_COMMITMENT_LINK_G0 Code Review Map

Target commit: `ce0d0ec2ee1dc9e2ceee15ee0b76f19ebd84573c`

Line numbers are orientation aids. Use class/function names as stable anchors.

## Confidence declaration

The controller verified the treatment, initialization and optimizer wiring by
direct reading, and verified collector/replay/GAE behavior **only** through the
numerical tests. The unread-by-human paths are therefore the highest-value
audit targets: `collect_trajectory`, `_replay_primitive`,
`_replay_event_heads`, `compute_gae` and `optimize_update`. Passing tests are
evidence, not proof; look for invariants the tests do not sample.

## `ha_ctse_process/event_held_commitment_link.py` (new, 1362 lines)

### Treatment and capacity — lines 148-193

- `CommitmentArm.__init__`, 151-164: `W_z: Linear(8,3,bias=False)`,
  `event_head: Linear(87,2)`, `mark_head: Linear(87,16)`; all `None` for `OR`.
- `primitive_bias`, 178-181: the sole treatment,
  `W_z(float(self.treatment) * z.detach())`.
- `event_parameters` / `base_optimizer_parameters`, 183-193: `W_z` is owned by
  the **base** optimizer; event and mark heads by the event optimizer.

Verify: that `float(treatment)` multiplication is the only arm-conditioned
branch anywhere in sampling, storage, replay, loss and execution; that the
`DUM` zero input yields a permanently exact-zero gradient for `W_z` so its Adam
moments never leave zero; and that no `z` path reaches the critic.

### Initialization and pairing — lines 210-291

- `_seed` / `authoritative_seed_map`, 210-229: `1000*r` replicate stride.
- `initialize_arms`, 246-291: base cloned from the `OR` init under seed 58058;
  additions initialized once under event/mark seeds and cloned `DUM`→`EHC`;
  global CPU/CUDA RNG saved and restored around the whole block; fail-closed
  parameter-count asserts.

Verify: no arm's branch can advance another arm's stream; the try/finally RNG
restore actually covers every allocation path; ledger/order/primitive pairing
across all three arms holds without consumption coupling.

### Collector and lifecycle — lines 312-683

- `_new_cursor` 312, `_close_segment` 326, `collect_trajectory` 335-683.

Verify against plan section "Clocks, lifecycle and execution": the five-step
physical row order; genuine `JOIN` resetting `h=0` and forcing `CREATE`;
temporary leave freezing and rejoin restoring `h,z,q` and segment state; a due
opportunity processed **before** the rejoin action; `q` decremented exactly
once per active primitive action and never during inactive physical time;
episode end forcing `CLOSE` after the final reward with remaining segments
right-censored; and a rollout cutoff preserving `z,q`/tables, detaching `h` in
all arms, bootstrapping the critic and creating **no** synthetic event row.
Confirm lifecycle keys never enter a model input.

### Probability and replay — lines 294-311, 684-936

- `_normal_parameters` 294, `transformed_mark_component_logp` 299,
  `_event_input` 305.
- `ReplayOutput` 684, `_replay_primitive` 702, `_replay_event_heads` 746,
  `replay_trajectory` 812, `replay_errors` 841, `validate_replay` 917.

Verify: `sigma = 0.1 + 0.9*sigmoid(s)`; `z = detach(tanh(u))`; the Jacobian
computed as `2*(log2 - u - softplus(-2u))` and its numerical behavior at large
`|u|`; exact factor support (`CREATE` mark-only, `KEEP` categorical-only,
`RENEW` both, `CLOSE` no row); that teacher replay recomputes identical inputs,
masks and factors from stored `u` rather than resampling; and that no gradient
reaches either head through sampled `u`/`z`.

### Credit and update — lines 937-1092

- `_pack_trajectory_once` 937, `compute_gae` 955, `optimize_update` 962-1092.

Verify: `gamma=0.99`, `lambda=0.95`, correct terminal vs continuation vs
bootstrap masking; that **every event row receives the same scalar advantage as
the primitive action it precedes**; separate Adam optimizers and separate
grad-norm clipping at 0.5; mark entropy bonus exactly zero and forced `CREATE`
contributing no categorical entropy; the trajectory packed once and reused
across all four epochs; and exposure accounting at 1092 incrementing base by
four for every arm and event by four for `DUM`/`EHC` only.

### Checkpoint — lines 1093-1362

- `save_checkpoint` 1130, `load_checkpoint` 1184, `compare_continuations` 1291,
  `parameter_and_optimizer_counts` 1360.

Verify: strict versioned key set; rejection on arm/replicate/shape/seed/
threshold/budget/key-set mismatch; that every dedicated RNG stream plus global
Python/NumPy/CPU/CUDA state round-trips; `normalizers=None` explicit; and that
`compare_continuations` genuinely proves exact discrete/RNG equality rather
than comparing only tolerances.

## `ha_ctse_process/dynamic_roster_direct.py` (modified)

`DirectPrimitiveARPolicy` gains `prepare_step` (new, around line 137) and an
optional primitive-logit-bias interface.

Verify the plan's hard requirement: with no bias supplied, the `OR` path must
be **exactly** equal to the pre-change implementation in parameters, state,
actions, log probabilities, values, hidden transitions and PPO algebra under
matched weights and RNG. Any drift here silently invalidates the access null.

## `scripts/run_noncalendar_commitment_benchmark_g0.py` (rewritten)

- `_require_cuda` 64, `_no_op_equal` 95, `validate_operational_records` 106,
  `_lifecycle_valid` 222, `run_smoke` 233, `formal_train` 334,
  `formal_evaluate` 505, `aggregate_analysis` 607.

Verify: formal modes are unreachable without the explicit authorization flag
and default invocation cannot start training; `formal_evaluate` accepts only a
strict `update_250.pt`; and `aggregate_analysis` implements the eight result
branches as genuine first-match precedence that is mutually exclusive at
equality and interval-crossing boundaries, with the "behavior confidently
fails" dual (`UCB <= threshold`) introducing no new threshold.

## `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`

`test_initialization_rng_isolation_and_capacity` 70,
`test_ledger_rejoin_epoch_due_event_and_partial_continuity` 117,
`test_semantic_replay_corruption_negatives` 207,
`test_checkpoint_strict_continuation_and_cuda_smoke` 273,
`test_authoritative_seed_maps_and_independent_cells` 370,
`test_fail_closed_operational_manifest_negatives` 465,
`test_result_branch_first_match_and_boundaries` 509.

Assess these as an auditor, not a reader: which plan invariants are asserted
only indirectly, which negatives are absent, and where a wrong implementation
would still pass. Name the specific missing test if you find one.
