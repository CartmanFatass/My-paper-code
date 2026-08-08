# EOCIV-B2 payload-content learnability code/science index

## Implemented boundary

`EOCIV-B2-PAYLOAD-CONTENT-LEARNABILITY` is an opt-in B-level real toy
experiment. It asks only whether ordinary external team reward can train the
existing recurrent actor to use A/B payload content when the receiver
representation makes the four legal slot states separable.

- Implementation: `experiments/candidates/eociv_lite/payload_content_learnability.py`
- Shared actor and default-compatible encoder seam:
  `experiments/candidates/eociv_lite/real_valve_learning.py`
- Real runner body-selection seam:
  `experiments/candidates/eociv_lite/actuation_runtime.py`
- CLI: `scripts/run_eociv_b2_payload_content_learnability.py`
- Focused tests:
  `tests/experiments/candidates/eociv_lite/test_payload_content_learnability.py`

The production packages under `ha_ctse_process/` and `envs/` do not import the
candidate. The experiment never trains or evaluates the B1 valve.

## Fixed configuration

- Encoders: `raw_byte`, `content_separating`.
- Seeds: `86031`, `86032`, `86033`.
- Profiles: the three registered B1 training profiles.
- Horizon: 48; hypothetical search candidates: zero.
- Training: 32 root-major episodes per encoder/seed/profile, one real
  actor/critic update per episode, 27,648 transitions and 576 updates.
- Evaluation: 8 fresh roots per encoder/seed/profile and three matched real
  runner arms (`CORRECT`, `SWAPPED`, `NATIVE_NEUTRAL`), 20,736 transitions and
  432 episodes.
- Maximum total: 48,384 real transitions. No result-dependent root, seed,
  budget, encoder, or arm change.

Training critical events carry the registered A/B body and the neutral event
carries registered native-neutral. Evaluation swaps only A/B content or makes
all events native-neutral. Every arm remains the same always-real route with
the same slot width, cost, lifecycle, world root, action noise, and initial
hidden state.

## Observable invariants

- The raw encoder remains the default and retains the legacy `/255` linear slot
  path. Both encoder conditions instantiate identical modules in identical
  order and therefore share actor/recurrent/value initialization by seed.
- The content encoder reads only actual `slot_block` bytes and fail-closes on
  anything other than empty, registered A, registered B, or native-neutral.
- Actor loss consumes only the real environment reward trace; it has no shock,
  route, valve, or outcome-label supervision.
- Evaluation freezes the actor, preserves per-root reward traces, segment
  returns, routes, input/kernel/action/recurrent digests, and reports raw
  full-episode and elementwise segment correct-minus-swapped and
  correct-minus-neutral contrasts with per-segment mean and dispersion.
- Initial and trained A/B distances replay their own recurrence over captured
  real evaluation observations, masks, slots, and noise; no zero-observation
  probe supplies the reported diagnostic.
- A/B/native-neutral coverage and per-root labels are derived from exact
  delivered registered body bytes; the experiment never reads environment
  private shock-state storage. The result also reports episode order, losses,
  gradients, counts and dispersion. Its scientific disposition is null and
  the registered C experiment remains unlicensed.

## Interpretation limits

This B run is a payload-content learnability diagnostic. It cannot establish
valve quality, B1 four-arm effects, natural-distribution value, superiority,
promotion, retirement, deployment, or a C-level outcome claim. Missing
support, instability, encoder equivalence, or an indistinguishable contrast is
an exploratory diagnosis rather than a direction decision.
