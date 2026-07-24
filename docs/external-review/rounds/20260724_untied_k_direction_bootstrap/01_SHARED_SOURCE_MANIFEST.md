# Shared source manifest

All paths are read from the remote at `stage_commit` through the GitHub
connector. Nothing here is uploaded; the repository is the evidence.

## Scientific contracts — read first

| Path | Why |
|---|---|
| `docs/project/ALGORITHM_PRINCIPLES.md` | project-wide scientific constraints |
| `docs/external-review/OPEN_REVIEW_PRINCIPLES.md` | how to explore within them, and your output responsibility |
| `docs/research/designs/ALGORITHM_DESCRIPTION_v6.md` | where `K_team` is defined as the team skill-holding interval |

## Active state

| Path | Why |
|---|---|
| `docs/project/CURRENT_WORK.md` | live boundary, grant accounting, what is already closed |
| `docs/project/IMPLEMENTATION_PLAN.md` | the current executable contract, and the G18/G19/G20 line this branch departs from |
| `docs/workflows/research-iteration-cycle.md` | the loop this round is the first stage of, and the authority split now in force |
| `docs/workflows/NOTES.md` | runtime, roles, terminology |

## The mechanism under question

Two skill-duration mechanisms coexist in the tree today. That coexistence is the
repository fact this round is about.

**Fixed period, HMASD trunk.** A single integer `k` (`config_1.py:134`, value
`10`). Reassignment fires on `env_steps_batch % self.config.k == 0`
(`hmasd/agent.py:1756`, `:1857`, `:2328`;
`hmasd/core/state_manager.py:186`; `hmasd/core/training_orchestrator.py:117`,
`:130`). The high-level sample closes only at `skill_timer == self.config.k - 1`
(`hmasd/agent.py:2587`, `:2600`, `:2615`;
`hmasd/core/training_orchestrator.py:285`). Recurrent chunking is bound to the
same constant: `chunk_length=self.config.k` (`hmasd/agent.py:4945`). A structural
assumption follows it: `episode_length` must be divisible by `k`
(`config_1.py:719`).

**Per-agent variable duration, HA-CTSE.** `H_min`/`H_max` bounds and a discrete
`skill_lifetime_candidates` tuple, sampled per agent at assignment
(`hmasd/ha_ctse.py:287-301`), with termination masked by skill age
(`hmasd/ha_ctse.py:611-631`). Process-core records realized `segment_length`
rather than assuming one (`ha_ctse_process/config.py`,
`ha_ctse_process/train.py`).

**Where the team skill comes from.** `Z` originates as an information set
compressed out of the OPT module, not as a mandatory state. Read `OPT`,
`StateEncoder`, `SkillCoordinator` and `SkillDecoder` in `hmasd/networks.py`,
and `OPTCompactExtractor`, `CompactTeamBridge` and `CompactTeamDiscriminator` in
`hmasd/ha_ctse.py`. Whether `Z` needs a period, or needs to persist at all, is
part of this question rather than a constraint on it.

**Not the subject.** Skill cardinality is fixed: `n_Z = 6` team codes and
`n_z = 6` individual codes (`config_1.py:132-133`, `ha_ctse_process/config.py`).
This round is about period, not count.

Tests that pin the current semantics: `tests/ha_ctse_test.py` asserts both the
`k`-boundary closure conditions and the variable-lifetime configuration.

## What is not evidence here

Anything under `docs/archive/`. Historical rounds, retired modules, and closed
G-generation artifacts are not active instructions. Do not reinterpret a closed
G18 or G19 result from this round.
