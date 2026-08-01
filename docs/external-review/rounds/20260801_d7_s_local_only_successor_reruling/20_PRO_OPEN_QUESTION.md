# Re-rule the successor-population route under local-only execution

Touchpoint 1 of this workflow. One decision is requested (see **Decision
requested**), tree-structured because its branches are dependent. Discarding
the framing of any branch — or of the whole tree — is a legitimate answer.

## Frozen inputs (not review surface)

- **User ruling 2026-08-01: the cloud / cross-device comparison line is
  cancelled; all compute runs on the single local workstation.** A user
  resource ruling, not reviewable here.
- The deletion it caused (repository fact, commit `3194c006`):
  `scripts/d7_s_manifest_replay_probe.py`, `scripts/d7_s_manifest_replay_gate.py`,
  `scripts/d7_s_world_manifest.py`, the manifest store and the GitHub Actions
  vehicle are deleted from the working tree. They remain in git history and can
  be re-instated if the ruling here requires it.
- The R4 estimand and design are unchanged
  (`docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`). No
  threshold moves.
- The successor selection RULE is frozen
  (`docs/research/designs/D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md`). No
  population has been selected, generated or inspected; the probe-refusal
  discipline has held.
- Your prior rulings stand except where this round explicitly asks for
  re-ruling: round `20260730_d7_s_provenance_correction_result` (Route A
  amended; design-now, population-later), and the one-machine provenance
  requirement — a registered episode key must identify one reproducible world.

## What changed, and what it breaks

[External evidence + repository fact]

Your Route-A amendment ordered the A1 selection precondition: a cross-machine
`MANIFEST_REPLAY_PASS` before the successor population may be generated (steps
N and O of the R4 closure ledger). With one machine by user ruling, a
cross-machine PASS is **unsatisfiable by design** — not failed, unsatisfiable.
The escalated cross-machine two-job gate never ran; its escalation is
withdrawn
(`docs/research/cdc/EVIDENCE_NOTES/20260801_CLOUD_CROSS_DEVICE_COMPARISON_LINE_RETIRED_BY_USER.md`).

Steps N (generate the immutable fresh inventory) and O (the formal successor
run) are HELD pending this re-ruling.

## What is measured (claims to falsify, with each instrument's fate)

1. Local cross-PROCESS manifest replay reproduced every registered quantity
   across two independent executions — nine world arrays, post-roll world
   after the full prefix roll, event identity, both limbs' units
   (H_STABLE=139, H_FLEX=550) — with `replaced_a_different_world=True` on both
   sides. The one failing assertion (6, complete pre-step environment
   identity) failed on construction-borne state: 6 of 273 fingerprinted
   attributes, at least two stale-initialization families per your §5
   correction
   (`docs/research/cdc/EVIDENCE_NOTES/20260730_MANIFEST_REPLAY_GATE_FIRST_RESULT.md`;
   its banner records that correction verbatim).
   CONFIDENCE: these measurements predate the deletion; the instruments are
   now deleted, and the residue's status after subsequent `scenario_base.py`
   refactors is UNMEASURED. The note's OS-entropy anchor
   (`scenario_base.py:328`) has drifted: at stage_commit that region
   initializes the seeded RandomState, and no unseeded `np.random.*` call
   remains in the file (verified by grep at stage_commit).
2. Two plain constructions in ONE process with identical seeds agree on
   `episode_world_fingerprint` (the nine world arrays) without any manifest
   (same note; repository-recorded measurement).
3. The `user_cluster_assignments` divergence is CLOSED as a value question,
   6/6: it was serialized byte width (int32 on Windows, int64 on LP64 Linux),
   never values. The component digest hashes `name + shape + tobytes()` and
   not dtype (`scripts/audit_d7_s_event_aligned.py:1652-1663`, verified by
   reading at stage_commit); the array is created with platform-dependent
   width at `envs/pettingzoo/scenario_base.py:369` (verified by reading)
   (`docs/research/cdc/EVIDENCE_NOTES/20260731_USER_CLUSTER_ASSIGNMENTS_DIVERGENCE_IS_DTYPE_WIDTH_NOT_VALUES.md`).
4. The cloud-versus-cloud 3-of-8 fingerprint divergence remains UNRESOLVED and
   is now unresolvable (its artifacts and vehicle are retired). Its scope was
   narrowed before retirement: two independently provisioned runners agreed
   byte-for-byte on the dev vehicle (one SHA-256 across four artifacts).
   Disclosed as a permanently open historical observation about the retired
   cross-machine surface.

## Decision requested

**Under local-only execution, what is the provenance / certification mechanism
for the successor population, and may steps N and O proceed under it once it
holds?**

Pre-walked branches — take one, modify one, or replace the structure:

- **B1 — local replay certification.** Re-instate the manifest + replay
  probe/gate from git history, re-scoped to cross-process on the one machine.
  If so, the dependent question: does certification require the
  construction-borne pre-step residue repaired (canonicalize or replace
  construction-derived state at the pre-step boundary), or is the gate scoped
  to the surfaces the manifest defines (world arrays, post-roll world, event
  identity, units) with the `state`-vector residue tolerated and disclosed?
  (Your §5.2 correction: replay "is not exonerated as a complete
  evidence-population reconstruction mechanism.")
- **B2 — A2 required.** Persist the exogenous trajectory or random tape. Name
  the smallest local evidence that certifies it.
- **B3 — seed-provenance on one machine.** The manifest mechanism was built to
  cross a machine boundary that no longer exists; measurement 2 bears on
  same-process determinism. If this suffices, name what must still be recorded
  and checked per run (for example `runtime_identity`, the world fingerprint
  at t_e) for a registered episode key to identify one reproducible world.
- **B4 — none of these.** Name the smallest missing evidence.

Also decide, because it feeds the registered fingerprint definition:

- **DTYPE.** Leave the component digest as-is (width-sensitive; all evidence
  is now produced on one int32 machine), canonicalize dtype inside the digest,
  or pin `dtype=np.int64` at creation
  (`envs/pettingzoo/scenario_base.py:369`). Historical fingerprints (R3/R4
  artifacts) were computed over int32 bytes; a definition change re-keys
  comparability with them and would be disclosed, never silent.

## Disclosures from the closed workflow (no decision requested unless one contradicts a prior ruling)

Implementation bindings decided during the D'/D''/D''' repairs (recorded in
`docs/project/CURRENT_WORK.md`; none reopens a frozen decision): the length
gate compares against registered h, not `window_series_length(h)`; R4 identity
is DECLARED (`--population r4`); strict subsets admitted for sharding; foreign
seeds hard-refused; the freshness sentinel gains an eighth artifact-level
condition (produced seeds pairwise distinct and in-population) without
renumbering 1–7; `NOT_EVALUATED` added as a fifth per-limb state; the
`PART_A_FULL_SYNC_MATERIALLY_WORSE` label added outside the frozen vocabulary.
Provenance rule created by D': with `--population r4` the `run_contract_id`
becomes the R4 namespace, changing every derived seed — shards from before
`28d6933f` and after are never pooled.

## Required response sections

1. `RULING` — branch selection or replacement structure; the certification
   gate definition for the successor route.
2. `ASSERTION_6_SCOPE` — what pre-step identity must hold for a successor run
   to be valid under the mechanism you rule.
3. `DTYPE_BINDING` — the digest / width decision.
4. `N_AND_O` — whether steps N and O may proceed once the ruled gate holds,
   and any amendment to `D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md`
   (including its §6 open slot, A1 versus A2).
5. `CORRECTIONS` — any claim above that is wrong, and anything this question's
   structure hides.

## Read boundary declaration

No run is in flight alongside this round. Nothing is read from any in-flight
artifact before this ruling lands.

## Evidence to read

- `docs/project/ALGORITHM_PRINCIPLES.md`
- `docs/external-review/OPEN_REVIEW_PRINCIPLES.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260801_CLOUD_CROSS_DEVICE_COMPARISON_LINE_RETIRED_BY_USER.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260730_MANIFEST_REPLAY_GATE_FIRST_RESULT.md`
- `docs/research/cdc/EVIDENCE_NOTES/20260731_USER_CLUSTER_ASSIGNMENTS_DIVERGENCE_IS_DTYPE_WIDTH_NOT_VALUES.md`
- `docs/research/designs/D7_S_SUCCESSOR_POPULATION_SELECTION_RULE.md`
- `docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`
- `docs/research/designs/D7_S_WORLD_MANIFEST_REPLAY.md`
- `docs/external-review/rounds/20260730_d7_s_provenance_correction_result/21_PRO_OPEN_RAW.md`
- `scripts/audit_d7_s_event_aligned.py`
- `envs/pettingzoo/scenario_base.py`
