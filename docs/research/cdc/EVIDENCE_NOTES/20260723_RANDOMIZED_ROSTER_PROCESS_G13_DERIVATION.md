# Randomized roster-process G13 derivation

Date: 2026-07-23

## Counterexample

Formal G12 establishes frozen-policy transport through N=80, but each domain
repeats one hand-authored membership schedule across every episode. Random wave
and priority ledgers do not exclude a controller that is only robust to those
few count trajectories.

Increasing N again would probe a more distant scale limit while leaving this
nearer process-distribution counterexample open. The smallest separating action
is to sample a fresh valid roster process for every evaluation episode.

## Source construction

Every process contains three independently sampled four-event motifs:
temporary leave, rejoin, terminal leave and fresh join. Initial count and keys,
the affected keys, batch magnitudes and safe inter-wave event times are all
drawn from an episode-owned ledger stream. Rejoin/join occur before the next
wave opens; removals occur only after the preceding wave has closed. This keeps
constructive utility one while randomizing the roster trajectory.

Three distributions cover moderate capacity 48, wide capacity 96 and ultra
capacity 96 with declared count ceilings 40, 64 and 80. The generator is
deterministic from `(domain_seed, episode_id)`, produces a unique profile name
per episode and records the full event signature. This is randomized evidence,
not untracked ambient RNG.

## Evidence correction

The frozen-checkpoint core now validates source controls for every evaluation
episode rather than one representative profile. It records and recomputes the
exact event signature, roster schedule, wave demand and constructive outcome;
one lifecycle trajectory per domain validates shared hidden-state semantics.
Formal/nonformal identity, checkpoint, model-state and first-match checks remain
fail closed.

The first probe allowed removals during an open wave and correctly failed the
constructive-utility control. Restricting only the removal-time support repaired
source identifiability. No policy, reward, threshold, seed budget or scientific
result was changed, so the failed probe consumes no iteration.

```text
selected_action=RANDOMIZED_ROSTER_PROCESS_G13
training_operation=none_frozen_g8_checkpoint_import
conclusion_bearing_iteration=14
iterations_remaining_before_run=4
```
