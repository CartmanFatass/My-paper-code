# B3-L realization design conformance check

Touchpoint 2. One question only: **does the completed code design in
`docs/research/designs/D7_S_B3L_DECISION_LEDGER.md` conform to the B3-L
ruling you issued in round `20260801_d7_s_local_only_successor_reruling`?**
This is not a route question and no alternative is argued. Zero experiments
have run. Discarding this question's structure is a legitimate answer.

## Frozen inputs (not review surface)

- The B3-L ruling itself, and `D7_S_SUCCESSOR_POPULATION_SELECTION_RULE_R2.md`
  which froze its amendments.
- R4 estimand, gates, vocabulary, and the R1 selection rule's preserved
  sections — the design moves none of them.
- Code anchors cited in the ledger were verified against the tree at this
  round's `stage_commit` (a scout mapped them; the Project Manager
  spot-checked the load-bearing ones: `build_pinned_env` order and its
  missing barrier re-invocation, the component-digest loop, the barrier's
  single-code-path guard test).

## The design, in one paragraph each (full detail in the ledger)

D1 relocates assertion 6 as caller-side wiring: a new
`finalize_preaction_state(env)` re-runs the canonical barrier after
topology + world + energy are final, then takes `full_state_fingerprint` as
the episode's pre-action fingerprint — because the barrier today runs only
inside `reset()`, against unpinned coordinates. D2 does not extend the
barrier preemptively; only a gate branch-A failure authorizes repair, which
then lands inside `_post_pin_initialization_steps` so reset and barrier stay
one code path. D3 defines the strict `certified_local_execution_class`
(workstation, OS/arch, Python, NumPy/SciPy, BLAS + CPU features, worker
count, spawn method now pinned explicitly, PYTHONHASHSEED required-set, the
four thread vars enforced in the parent too, git commit + dirty-flag as
source identity, configuration digest; `class_id` = SHA-256 of the whole).
D4 realizes the gate as two fresh subprocess workers running one dev episode
key end-to-end (construct→pin→world→energy→D1→prefix→event→complete 2/2
fork set at H_stable=139 / H_flex=550), exact-equality comparison, verdicts
named by your fail-closed tree; a dev key with no qualifying event is
refused (`GATE_EPISODE_KEY_HAS_NO_EVENT`) and another dev index is used.
D5 adds per-step exogenous digests (nine world arrays + step index) as
gate-mode-only instrumentation. D6 adds an `rpgm_regen_count` liveness
counter, excluded from fingerprints as instrument state but recorded in the
gate artifact. D7 pins `user_cluster_assignments` to `np.int32` at creation
and records `component_dtypes` for all nine components; the digest stays
width-sensitive; the gate asserts `"<i4"`. D8 mints
`FINGERPRINT_ALGORITHM_VERSION="fpalg-1"` (unchanged algorithm) and
`PROVENANCE_CONTRACT_VERSION="prov-2"` (bumped), single shared location.
D9 adds `--population successor` requiring `--inventory`. D10 implements
step N as a write-once inventory generator that refuses without a current
PASS. D11 wires `LOCAL_PROVENANCE_NOT_CERTIFIED` with your six reasons
(two reserved to the gate). D12 makes the PASS certificate a committed
artifact whose currency = source_tree and class_id both match live.

## Points where the design interprets the ruling (flagged for the check)

1. **D10 coordinate generation timing.** Your inventory list includes
   "topology coordinate records and hashes", and your prohibition ends at
   the gate PASS. The design reads this as: post-PASS mechanical
   generation-and-hashing of successor coordinates at step N is sanctioned;
   support probes, user-world generation, and value-reading inspection
   remain forbidden. If instead coordinates must not be generated until the
   formal run itself, D10 changes shape — say so.
2. **D5 scope.** Per-step trajectory digests are built as gate-mode-only
   instrumentation; the formal run's per-episode duties record the
   fingerprints and digests your §4 lists but not per-step sequences. If you
   intended per-step digests on formal episodes too, D5 widens.
3. **D11 partition.** `FULL_HORIZON_REPLAY_MISMATCH` and
   `DYNAMIC_PATH_NOT_EXERCISED` are reserved to the gate; the formal run's
   own per-episode identity checks use the other four reasons. If the formal
   run must itself detect full-horizon divergence (beyond its recorded
   digests), the design under-checks — say so.
4. **D6 fingerprint exclusion.** The liveness counter is instrument state
   excluded from `full_state_fingerprint` (it would otherwise make the
   fingerprint sensitive to a diagnostic). If you class it as environment
   state, it moves inside.

## Required response sections

1. `CONFORMANCE` — CONFORMS, or the exact ledger items (D1–D12) that
   deviate and in what way.
2. `INTERPRETATIONS` — accept/correct each of the four flagged readings.
3. `CONVERGENCE_DECISION` — your closing decision for this touchpoint.

## Read boundary declaration

No run is in flight alongside this round. Nothing will be read from any
in-flight artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/designs/D7_S_B3L_DECISION_LEDGER.md`
- `docs/research/designs/D7_S_SUCCESSOR_POPULATION_SELECTION_RULE_R2.md`
- `docs/external-review/rounds/20260801_d7_s_local_only_successor_reruling/21_PRO_OPEN_RAW.md`
- `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`
- `scripts/audit_d7_s_event_aligned.py`
- `envs/pettingzoo/scenario7_energy_aware.py`
- `envs/pettingzoo/scenario_base.py`
- `tests/scenario7_canonical_initialization_test.py`
