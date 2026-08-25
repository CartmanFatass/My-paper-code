# Open-roster direct MVP G5 derivation

## Decision

The new primary axis is dynamic agent count. Asynchronous skill lifetime is
temporarily frozen and the skill controller is absent. The near-term target is
one usable algorithm, not a mechanism-advantage result.

## Retained evidence

- Direct primitive recurrence previously accessed the fixed dynamic-roster
  carrier at deterministic utility about `0.9991` with exact replay.
- R49 established an active-only, permutation-equivariant interface whose
  parameter shapes do not depend on `N`, including structural reads through
  `N=16`.
- G3/G4 show that adding roster mechanisms before natural policy access is
  stable does not create a usable algorithm.

## Counterexample to the current implementation

The existing direct learner can score nearly perfectly while collection,
hidden storage, replay and evaluation are all built around
`MAX_LIFECYCLES=6` and one `4 -> 2 -> 6 -> 4` schedule. That observation does
not distinguish a genuinely open-roster policy from schedule memorization or
fixed-capacity dependence.

## Smallest correction

Keep the proven direct recurrent algorithm and change only its roster domain:
derive batch width from runtime data, train over several within-episode count
profiles and evaluate on unseen counts under a larger padding capacity. Use an
absolute utility contract. Do not add attention, commitments, skills, lifetime
reward, intrinsic reward or a fixed-`N` advantage comparator.

This derivation costs zero conclusion-bearing iterations. Its implementation
and bounded nonformal exercise are the next active action.
