# PM reconciliation — 20260726_d7_s_event_aligned_contract_freeze

Raw: `21_PRO_OPEN_RAW.md` (33,355 chars, byte-verified). Verdict: **FREEZE
AFTER MODIFICATION**, eleven amendments. Nothing disputed. All eleven are
incorporated verbatim into `docs/research/designs/D7_S_EVENT_ALIGNED_SOURCE_AUDIT.md`,
now marked FROZEN; the draft's own text survives only where the ruling
confirmed it.

Deltas from the draft worth naming (the contract records all of them):

- The flex anchor moved off the harness's unregistered 0.25 trigger onto the
  registered G2 LEAVE/CHARGE_ABSENT boundary, and `H_flex` moved from 450 to
  **550** — Pro's own derivation subtracts hover power from charging power
  (540.3 → next check 550), a term neither the draft nor the grill had.
- One repository-fact correction to the grill's F07: `uav_target_stations`
  is also set by pre-capture dock requests but is reset each step — the
  LEAVE lifecycle edge, not any per-step field, is the event.
- `heldout_low` becomes the profile for everything, with the claim scoped to
  it explicitly; training profile allowed only as an unpooled diagnostic.
- One joint mixed-urgency event per episode, both limbs at the same `t_e` —
  stronger than either the draft's or the grill's alternatives.
- X=50 m (not the 150 m scale the question proposed — S7 overrides user
  speed to 5 m/s; the grill's generic 15 m/s figure was wrong for this
  preset), Y=10, Z=139.
- The branch system grew to ten first-match branches with three affirmative
  negative resolutions; `SOURCE_NECESSITY_UNRESOLVED` is now a genuine
  residual, not a catch-all.
- One bounded expansion (8 → 16 topologies, seeds frozen) and never more.
- The PM topology-pinning mechanism was accepted **with an ordering fix**:
  coordinates must be restored after every episode reset, because
  `reset` re-initializes charging stations.

Transport: fence sent once, one wedged-tab replacement, capture on first
sentinel-verified attempt; details in `50_MECHANICAL_INTAKE_RECORD.md`.

Next per the frozen contract: evidence action 1, the zero-compute
conformance derivation.
