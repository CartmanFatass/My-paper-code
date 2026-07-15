# R35--R40 Cooperative-Substrate Failure Review

Date: 2026-07-15

## Decision

R40 is a valid `VALID_FAIL_R40_ACCESS`. Retire PettingZoo 1.24.3
`simple_spread_v3` under the frozen discrete-action recurrent-MAPPO contract.
Do not rescue it with more steps, seeds, continuous actions, another network,
reward/observation shaping, intrinsic reward, altered thresholds, or checkpoint
selection.

Together, R35--R40 close the current custom/public substrate-search loop. The
project must not select another convenient toy and hope that ordinary MAPPO or
a modified credit objective learns it. The next substrate must inherit positive
evidence from the algorithm being extended.

## Cross-Round Failure Matrix

| Gate | Valid evidence | Failed implication | Reusable constraint |
| --- | --- | --- | --- |
| R35 | Both ordinary MAPPO and reward-pure R30 completed 320K steps | Neither accessed the sparse Alice--Bob cycle | No hierarchy comparison is interpretable there |
| R36 | Exact episodic joint-cell novelty expanded coverage `3.855x` | Coverage did not produce collection or cycle success | Undirected visitation breadth is not sparse cooperative access |
| R37 | Actor-visible task identity causally improved collection and coverage | The registered reliable-cycle floor still failed | Information repair alone did not make the custom task a comparison substrate |
| R38 | Ordinary recurrent MAPPO mechanics and paired random evaluation were valid | The role-free CTS task had zero full success | Do not invent a third custom sparse task |
| R39 | AR roster capacity, sampled reward alignment, exact replay, and native high PPO mechanics were valid | The fixed-`N` native-HMASD toy did not learn the registered roster mapping | Expressivity and aligned returns do not establish a learned joint-credit anchor |
| R40 | 500 updates, 2,500 low optimizer steps, exact recurrent replay, zero high updates, and paired evaluation were valid | MAPPO return `-52.3922` was indistinguishable from random `-52.5873` | `simple_spread` is not a positive access anchor under this frozen contract |

## R40 Evidence Boundary

- M0 passed with replay error `2.384185791015625e-07`.
- The paired MAPPO-minus-random mean was `0.1950303`, with 95% interval
  `[-1.448355, 1.903356]`; the registered lower floor was `>5`.
- MAPPO mean return was `-52.392238`, below the `-35` floor.
- All four block means were below `-35`; M2 required three passing blocks.

This is evidence against this exact substrate/training contract, not against
MAPPO in general and not against HMASD, R30, variable skill lifetime, or open
rosters.

## Baseline Matrix For The Next Decision

| Candidate | Positive anchor | Blocking issue |
| --- | --- | --- |
| Another custom or public toy | None under the repository's current learners | Repeats the R35--R40 substrate-search loop |
| S7-S1 immediately | Existing original-HMASD service reference | High compute and conflicts with the user's toy-first iteration requirement |
| Existing R27 forced-capacity substrate | Persistent forced conditional behavior | Reward-off mechanism evidence, not a learned fixed-`k` anchor |
| Exact HMASD-paper Alice--Bob task plus unchanged fixed-`k` HMASD | Published positive algorithm/task evidence, including the original environment-agnostic `q_D/q_d` objective | The repository's later Alice--Bob variants are not the paper environment; exact reconstruction and reference reproduction are required |
| Open-roster / variable `N` now | Architectural motivation only | Fixed-`N` learned anchor is still absent; membership complexity would confound the failure |

## Controller Recommendation For Review

Use one route only: reconstruct the HMASD paper's Alice--Bob environment and
re-establish the unchanged standard fixed-`k` HMASD positive anchor, including
its original environment-agnostic `q_D/q_d` intrinsic objective. Do not use any
of the repository's custom asymmetric-cycle or CTS variants as substitutes.

Only if that exact baseline is positive may the next experiment introduce the
native categorical R30 per-agent `KEEP/SET` temporal controller on the same
environment and checkpoint. Variable team size remains a later, orthogonal
axis; membership transitions must not renew surviving agents' skills.

External review must accept, modify, or retire this one route and define its
minimum abandonment gate before implementation.
