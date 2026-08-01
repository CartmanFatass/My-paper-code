# B3-L realization — Project Manager decision ledger

Status: **complete code design for touchpoint 2 conformance.** Implements the
B3-L ruling (round `20260801_d7_s_local_only_successor_reruling`,
`D7_S_SUCCESSOR_POPULATION_SELECTION_RULE_R2.md`). Every binding below is an
implementation decision inside the Project Manager's authority; none moves a
threshold, estimand, gate vocabulary or result branch beyond what the ruling
itself orders. Zero experiments run at design time.

Code anchors verified against stage `2436e6ed` (scout map, PM spot-checked).

## D1 — assertion-6 relocation is caller-side wiring, not a barrier change

New function `finalize_preaction_state(env)` in
`scripts/audit_d7_s_event_aligned.py`: re-invokes
`env.canonicalize_post_pin_initialization()` (idempotent and randomness-free
by its own asserted contract, `scenario7_energy_aware.py:639-690`) **after**
topology restore + user-world generation + energy-profile installation, then
computes and returns `full_state_fingerprint(env)` as the episode's
`preaction_fingerprint`. Wired into `run_calibration_episode` and the
audit-episode driver immediately after `apply_energy_profile`, before any
prefix stepping. `build_pinned_env`'s contract is unchanged (keeps the test
fixture and every caller stable). Rationale: the scout map shows the barrier
runs today only inside `reset()` against *unpinned* coordinates and is never
re-run after the registered inputs are final — the exact defect the ruling's
temporal boundary names.

## D2 — the barrier is not preemptively extended

The ruling's decision tree drives repair: run the gate first; only branch A
(pre-action identity differs) authorizes canonicalization repair, and then
the repair lands in `_post_pin_initialization_steps` so `reset()` and the
barrier stay one code path (guarded by
`tests/scenario7_canonical_initialization_test.py::test_reset_runs_the_barrier_exactly_once`).
No speculative barrier steps are added at design time.

## D3 — CERTIFIED_LOCAL_EXECUTION_CLASS

New function `certified_local_execution_class(*, workers, start_method)` next
to `runtime_identity()` (which stays descriptive, per C7 of the ruling's
spirit — no renaming). Fields, all strict (a lookup failure raises, unlike
`runtime_identity`): workstation node name; OS + architecture; Python
version; NumPy and SciPy versions; BLAS implementation, version and detected
CPU features; declared formal `worker_count`; `process_start_method`
(explicitly `"spawn"`, now pinned in code via
`ProcessPoolExecutor(mp_context=multiprocessing.get_context("spawn"))` rather
than platform default); `PYTHONHASHSEED` (the run refuses to start unless it
is set — bound value recorded); the four BLAS/OpenMP thread variables (must
equal "1", as `_PinnedWorkerEnv` already enforces for children — the parent
process now sets them for itself too before any numpy work); `source_tree` =
the git commit of the running tree plus a dirty flag (repository identity is
`code_identity=git_commit_and_exact_path_set`; a dirty tree refuses
certification); `configuration_digest` = SHA-256 over the canonical-JSON
resolved config. `class_id` = SHA-256 over the canonical JSON of all fields.

## D4 — gate mechanism: two subprocess runs of one worker entry point

New dev-only script `scripts/d7_s_local_replay_gate.py`. Driver mode spawns
the registered interpreter twice (`subprocess`, fresh processes, same
command line) in `--worker` mode; each worker builds the dev episode
(`TOPOLOGY_SEED_DEV=20260725`, audit block, `--episode-index`, default 0),
runs the full registered pipeline — construct, pin, world, energy, D1
finalization, prefix roll to the qualifying event, complete R4 fork set for
both limbs (H_stable=139, H_flex=550) — and emits one JSON replay record.
The driver compares records field-by-field and classifies strictly by the
ruled tree: `LOCAL_EPISODE_KEY_REPLAY_FAIL:<surface>` naming branch A/B/C
consequences, or `LOCAL_EPISODE_KEY_REPLAY_PASS`. The two workers may run
concurrently (independence is process-level); comparison is loss-less (exact
equality, no tolerances). An episode key whose prefix finds no qualifying
event is refused as `GATE_EPISODE_KEY_HAS_NO_EVENT` (choose another dev
index) — a dev-instrument property, never a successor-selection filter.

## D5 — per-step exogenous trajectory digests are gate-mode instrumentation

`fork_continuation` gains an optional collector (default off, formal runs
unaffected): when enabled, after each step it records SHA-256 over the nine
`WORLD_COMPONENT_ORDER` arrays plus the step index. The gate enables it for
the prefix roll and every fork; equality of the digest sequences is the
ruled "lossless per-step exogenous user/cluster trajectory digests" surface.
The collector never mutates state and never appears on conclusion-bearing
paths.

## D6 — dynamic-path liveness counter

`scenario_base.py` gains `self.rpgm_regen_count = 0` (created in `__init__`),
incremented in the post-initialization waypoint/cluster-target regeneration
branch (the `:2507` write path when reached during stepping). The gate
requires `rpgm_regen_count >= 1` on both sides across the exercised
trajectory, else `DYNAMIC_PATH_NOT_EXERCISED`. The counter is diagnostics
(excluded from fingerprints via `FINGERPRINT_EXCLUDED_ATTRS`, since it is
instrument state, not environment state — recorded in the gate artifact).

## D7 — dtype pin and component_dtype provenance

`scenario_base.py:369` → `np.zeros(self.n_users, dtype=np.int32)` (writers
`:791`/`:2507` assign scalars into the typed array and need no change).
`episode_world_fingerprint`'s component loop additionally records
`component_dtypes[name] = arr.dtype.str` for all nine components (digest
bytes unchanged on this machine); the gate and the formal runner assert
`component_dtypes["user_cluster_assignments"] == "<i4"`. Historical
fingerprints are not re-keyed.

## D8 — versioning: one shared location

Two new constants in `scripts/audit_d7_s_event_aligned.py`:
`FINGERPRINT_ALGORITHM_VERSION = "fpalg-1"` (names the current digest
algorithm; unchanged by this design) and
`PROVENANCE_CONTRACT_VERSION = "prov-2"` (bumped by the dtype binding and
the new provenance fields, per the ruling). The gate, the execution class,
the inventory and per-run artifacts all import these — no second minting
site.

## D9 — successor namespace and CLI surface

New constant `SUCCESSOR_POPULATION_NAMESPACE =
"D7_S_SUCCESSOR_FRESH_POPULATION"`. `--population` gains choice
`successor`, which requires `--inventory <path>` and enters the D11 refusal
chain. The successor topology list is computed only by the inventory
generator from the frozen R1 rule (first K=8 ascending from 20260742,
exclusions as frozen — pure arithmetic, no construction; C5's wording:
precommitted, not instantiated).

## D10 — step N: input-inventory generator

New script `scripts/d7_s_successor_input_inventory.py`. Refuses to run
unless a current PASS certificate exists (D12) whose `class_id` and
`source_tree` match the running environment. Emits the inventory the ruling
lists: namespace, topology list from the rule, coordinate records and hashes
— generated mechanically at step N via the registered coordinate derivation
and immediately hashed. Reading of the ruling, disclosed for the
conformance check: the prohibition ends at `LOCAL_EPISODE_KEY_REPLAY_PASS`
("before the complete local gate passes"), and the ruled inventory itself
lists coordinate records — so post-PASS mechanical generation-and-hashing
of coordinates is sanctioned; support probes, user-world generation and any
value-reading inspection remain forbidden. Then all Part-A and focal-audit
episode keys, the
episode/energy/user-world seed table (existing derivation functions, new
namespace), replicate/continuation derivation version, source-tree and
configuration digests, `class_id`, both D8 versions, dtype binding, episode
count and the inventory set hash (SHA-256 over canonical JSON of all
entries). Write-once; regeneration refuses if the file exists.

## D11 — LOCAL_PROVENANCE_NOT_CERTIFIED refusal chain

In `main()` under `--population successor`, before any episode work, refuse
with `LOCAL_PROVENANCE_NOT_CERTIFIED:<reason>` on: missing/stale PASS or
runtime mismatch (`LOCAL_RUNTIME_MISMATCH`), inventory absent or set-hash
mismatch or key-set mismatch (`EPISODE_KEY_INVENTORY_MISMATCH`); during the
run, per-episode: initial-world digest/dtype mismatch against the recorded
provenance (`INITIAL_WORLD_REPLAY_MISMATCH`), pre-action fingerprint
mismatch across the run's own paired construction check
(`PREACTION_STATE_REPLAY_MISMATCH` — the formal run re-verifies its own
episode identity, not a second full replay), and the gate-only reasons
(`FULL_HORIZON_REPLAY_MISMATCH`, `DYNAMIC_PATH_NOT_EXERCISED`) reserved to
the gate. Refusal happens before conclusion-bearing computation wherever
structurally possible.

## D12 — PASS certificate is a committed artifact

The gate writes full records under `logs/replay_gate/<stamp>/` (runtime
evidence, gitignored) plus a compact certificate
`docs/research/cdc/CERTIFICATIONS/LOCAL_EPISODE_KEY_REPLAY_PASS.json`
(committed): verdict, episode key, all top-level digests, `class_id`, both
versions, source_tree, timestamp. "Current" means: certificate exists, its
`source_tree` equals the running commit, its `class_id` equals the live
recomputed class. Any mismatch is `LOCAL_RUNTIME_MISMATCH`.

## Per-episode recording duties (formal run)

`topology_unit_for_serialization` gains: `runtime_class_id`, episode-key
identity fields, `component_dtypes`, `preaction_fingerprint`,
`full_fingerprint_at_te` (already captured on the event), event-snapshot
fingerprint, and the actual derived seeds. `runtime_identity()` remains in
the top-level artifact unchanged.

## Cost (informational, EVIDENCE_COMPLEXITY_POLICY)

Gate: 2 fresh processes × (prefix ≤950 + full 2/2 fork set ≈ 8 forks ×
139/550 steps ≈ 2.8k steps) ≈ ~3.7k steps ≈ ~4 min/process at 0.0615 s/step;
run concurrently ≈ ~5 min wall — inside the 20-minute nonformal cap.
Formal successor run: unchanged R4 shape (8 topologies × 16 episodes, 2/2),
~4.2 h at `--workers 4` on this box; no wall-clock cap applies to step 7.

## Deliberately not done

- No manifest code resurrected; `D7_S_WORLD_MANIFEST_REPLAY.md` stays a
  fallback design (B1) selected only by the ruled tree.
- `seed_controls_generation` untouched (ruling C7).
- No successor topology constructed, no coordinate inspected, no support
  probe (R1 §2 discipline; C5 wording adopted).
- No barrier extension without a gate-measured branch-A failure (D2).
