# GPT-5.6 Pro R37/R38 Disposition

Date: 2026-07-15

Source model: GPT-5.6 Pro (`Pro` web conversation)

Reviewed commit: `53862548674484ca915eeb9f285b730018514d56`

## Verdict

- **Accept** `VALID_FAIL_R37_ACCESS` and retire the 80-step
  `alice_bob_asymmetric_cycles` access gate. R37 validly established that task
  identity was an access carrier, while its registered cycle-success floor
  still failed.
- **Accept with modification** the single R38 direction: build one new minimal
  cooperative two-timescale sparse benchmark and validate it with functionally
  ordinary constant-code recurrent MAPPO against a paired uniform-random null.
- **Reject** direct implementation of Pro's R38 v1.0/v1.1 state machines. Both
  allowed one agent to satisfy the short and long predicates sequentially, so
  they did not structurally require cooperation or simultaneous distinct
  per-agent lifetimes.

## Accepted R38 Causal Edge

```text
swap-equivariant simultaneous anchor/shuttle duties
-> ordinary recurrent MAPPO accesses both duties and their joint sparse success
-> benchmark is eligible for one later shared-fixed-k versus per-agent-lifetime gate
```

The access gate is not an algorithm result. It may establish benchmark
viability only.

## Controller Modification

The implementation plan freezes the following role-free state machine:

- continuous world `[0,6]^2`, direct two-dimensional actions scaled by `0.5`;
- one anchor zone at `(3,3)` and two shuttle zones at `(1,3)` and `(5,3)`, all
  radius `0.75`;
- a valid attempt starts only when exactly one agent contacts the anchor;
- that agent becomes the locked holder for the current attempt; only the other
  agent may advance the fixed shuttle sequence `left -> right -> left -> right`;
- the holder must remain continuously in the anchor for `40` post-action
  states, while the visitor completes all `4` shuttle stages during that same
  unbroken attempt;
- a holder break resets the current streak, shuttle stage, and completion
  flags before any same-step visitor contact is considered;
- either agent may become holder; swapping agent identities, positions, and
  actions leaves transitions and reward unchanged;
- full success gives the only shared external reward, `+1`, and terminates the
  episode; all partial contacts, stages, streaks, and breaks give zero reward;
  failure truncates at `200` steps.

This corrects the same-agent and non-simultaneity defects without assigning an
agent identity to either duty.

## Information Boundary

The actor receives only its position, teammate-relative position, and the
relative positions of the public anchor and two shuttle zones. It does not
receive holder identity, shuttle stage, anchor streak, contact flags, success
flags, reward, a role label, or future state. The recurrent policy must infer
the current attempt from observable trajectories.

The centralized critic may receive both absolute positions, current holder
one-hot, current shuttle stage, current anchor streak, and completion flags.

## Intrinsic-Reward Boundary

R38 uses `r_intrinsic = 0`. No novelty, count, RND, ICM, discriminator,
classifier, skill, process, or environment-derived auxiliary reward may repair
the access floor.

Any future intrinsic mechanism must keep one environment-agnostic mathematical
form and input contract across benchmarks. It may not be redesigned around, or
explicitly consume, R38 anchor/shuttle identities, contacts, stages, distances,
success predicates, or external reward.

## Baseline And Exposure

- functional baseline: constant skill code `0`, no high-policy update, no
  process/intrinsic injection, recurrent low actor and centralized low critic;
- this is functionally ordinary recurrent MAPPO, although the existing model
  still physically contains dormant skill/high/process modules;
- train seed `39031`, CUDA, `16` spawn environments, rollout `200`, total
  `320,000` environment steps, exactly `100` outer low PPO updates;
- five PPO epochs, recurrent sequence length `20`, sequence batch size `64`;
- final stochastic MAPPO evaluation uses reset seeds `139031..139286`;
- uniform-random actions use the same `256` resets and independent action RNG
  seed `49031`;
- paired percentile bootstrap: `10,000` repetitions, seed `59031`.

## Decision Boundary

Implementation validity is evaluated before science. A valid access PASS must
meet the registered absolute short, long, and full-success floors, positive
paired MAPPO-minus-random lower confidence bounds, and the four-block
repeatability requirement. A valid FAIL retires this benchmark without adding
intrinsic reward, shaping, steps, seeds, or threshold changes. A PASS authorizes
only registration of one shared-fixed-k versus per-agent-lifetime mechanism
gate.
