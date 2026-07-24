# Shared source manifest

All paths are read from the remote at `stage_commit` through the GitHub
connector. Nothing is uploaded; the repository is the evidence.

## Scientific contracts — read first

| Path | Why |
|---|---|
| `docs/project/ALGORITHM_PRINCIPLES.md` | project-wide scientific constraints |
| `docs/external-review/OPEN_REVIEW_PRINCIPLES.md` | how to explore within them, and your output responsibility |
| `docs/research/designs/ALGORITHM_DESCRIPTION_v6.md` | where `K_team` is defined as the team skill-holding interval |

## The evidence line this round builds on

| Path | Why |
|---|---|
| `docs/report/ITERATION_18.md` | G17 accepted. The credit-window / causal-window misalignment finding, and the `gamma = 0` alignment that fixed it |
| `docs/report/ITERATION_19.md` | G18. Delayed source learnable; shared actor does not preserve G17; critic isolation insufficient |
| `docs/project/IMPLEMENTATION_PLAN.md` | the current executable contract: what is closed, the G19 screen outcome, and the G20 derivation now in flight |
| `docs/project/CURRENT_WORK.md` | live boundary and grant accounting |

## The modules under discussion

| Path | Role |
|---|---|
| `ha_ctse_process/continuous_roster_policy.py` | the shared policy; carries the action-mean hook G19 added |
| `ha_ctse_process/continuous_service_roster_proxy_g17.py` | the accepted immediate-service controller |
| `ha_ctse_process/delayed_battery_roster_g18.py` | the delayed battery source |
| `ha_ctse_process/separated_credit_g18.py` | the closed separated-credit candidates |
| `ha_ctse_process/anchored_residual_g19.py` | the retired fast anchor plus zero-initialized delayed residual and conflict projection |
| `tests/ha_ctse_process_anchored_residual_g19_test.py` | what the G19 boundary actually proved: zero-residual equivalence, bitwise fast-policy invariance, nonnegative projected gradient dot product |
| `ha_ctse_process/config.py` | process-core configuration, including realized segment length and skill cardinality |

## The two skill-duration mechanisms that coexist today

**Fixed global period, HMASD trunk.** A single integer `k` (`config_1.py:134`).
Reassignment fires on `env_steps_batch % self.config.k == 0`
(`hmasd/agent.py:1756`, `:1857`, `:2328`; `hmasd/core/state_manager.py:186`;
`hmasd/core/training_orchestrator.py:117`, `:130`). The high-level sample closes
only at `skill_timer == self.config.k - 1` (`hmasd/agent.py:2587`, `:2600`,
`:2615`; `hmasd/core/training_orchestrator.py:285`). Recurrent chunking uses the
same constant: `chunk_length=self.config.k` (`hmasd/agent.py:4945`). Episode
length is constrained to divide by it (`config_1.py:719`).

**Per-agent variable duration, HA-CTSE.** `H_min`/`H_max` bounds and a discrete
`skill_lifetime_candidates` tuple sampled per agent at assignment
(`hmasd/ha_ctse.py:287-301`), with termination masked by skill age
(`hmasd/ha_ctse.py:611-631`). Process-core records realized `segment_length`
rather than assuming one.

## Where the team skill comes from

`Z` originates as an information set compressed out of the OPT module, not as a
mandatory state. Read `OPT`, `StateEncoder`, `SkillCoordinator` and
`SkillDecoder` in `hmasd/networks.py`, and `OPTCompactExtractor`,
`CompactTeamBridge` and `CompactTeamDiscriminator` in `hmasd/ha_ctse.py`.
Whether `Z` needs a period, persists at all, or is compressed from something
else is part of this question rather than a constraint on it.

## Not the subject

Skill cardinality is fixed: `n_Z = 6` team codes and `n_z = 6` individual codes
(`config_1.py:132-133`, `ha_ctse_process/config.py`). This round is about
period, not count. Anything under `docs/archive/` is not an active instruction.
