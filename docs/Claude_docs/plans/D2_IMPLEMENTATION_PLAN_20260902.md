# D2 implementation plan — policy-based interruption on the HMASD base route

Written 2026-09-02 for the implementer the owner assigns. The specification is
`ADR_01_D2_POLICY_INTERRUPTION.md` (revision 3, accepted); the non-blocking notes in Part III of
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` are part of the specification for tests. This
plan orders the work, names the files and functions, and fixes the acceptance checks. It does not
change any decision in the ADR. Where the plan and the ADR disagree, the ADR wins; report the
disagreement instead of resolving it.

## 0. Ground rules (from `CLAUDE.md` and the evidence spec §11)

- Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Never install anything into
  either conda env.
- Scope is the HMASD base route only: `config_1.py`, `hmasd/networks.py`, `hmasd/agent.py`,
  `hmasd/utils.py`, one new test file. Do not touch `ha_ctse_process/`, `hmasd/ha_ctse.py`, `envs/`,
  or any `experiments/candidates/*`.
- `mode = off` must stay byte-identical to the current route: same modules, same parameter shapes,
  same RNG draws, same buffer arrays, same checkpoint format. Every `d2` branch is guarded by the
  mode switch; no `d2` code path may execute, allocate, or draw RNG in `off`.
- Tests go to `tests/flexible_skill_duration_d2_test.py` (top-level `*_test.py`; `test*.py` is
  gitignored at top level). Run every test with
  `--basetemp C:/Projects/HMASD/temp/pytest_d2_policy_interrupt`. Run `git check-ignore -v` on any
  new file before committing.
- No experiments. E0 and later are the owner's. The implementer runs unit tests and one short smoke
  rollout per mode to produce the report in section 10; nothing from those is evidence.
- Commit at the end of each phase with a message naming the phase; push after each commit.
- Do not decide the open items in ADR §"Open questions" (finite `c`, `c_Z` grid; intermediate
  `k_max` values). They stay parameters with the ADR defaults.

## 1. Vocabulary used below

| Symbol | Meaning | Where it already exists |
| --- | --- | --- |
| `N` | agents, 6 for E1/E2 | `config.n_agents`, set by `main.py:410` from `--n_uavs` |
| `k` | current global skill interval, 10 | `config_1.py:134` |
| `k_max`, `k_Z` | per-agent cap, team cap (new) | — |
| `c`, `c_Z` | interruption costs (new), default `inf` | — |
| `a_i`, `a_Z` | steps since agent `i`'s / the team's last decision | `env_skill_ages` (`agent.py:802,1553,2027`), team age new |
| `g_i`, `g_Z` | log-probability gaps | new |
| `S_t` | agents re-decided at step `t` | new |
| `O_t` | decode order: kept agents (canonical) then `S_t` (canonical) | new |
| `M` | high-level rows per rollout | logged |

## 2. Phase 0 — baseline fingerprint (before any edit)

Purpose: invariant 1 needs a reference that predates the change.

1. Build a small deterministic configuration: scenario 1, `--n_uavs 3`, `num_envs 2`,
   `rollout_length 40`, `k 10`, `episode_length 40`, one seed. Reuse the environment and agent
   construction pattern of `tests/hmasd_run_test.py`.
2. Run two rollouts with the current code and record, per step and env: team skill, agent skills,
   team and agent log-probabilities, the high-level reward at each closed segment, and the SHA-256 of
   the coordinator and discriminator `state_dict` tensors after one `update_coordinator`.
3. Save the fingerprint as JSON under `temp/pytest_d2_policy_interrupt/fingerprint_off.json` and
   copy it into the test file as the expected value of test 1 (small enough to inline; if not, store
   it under `tests/fixtures/` and check `git check-ignore`).

Commit: "D2 phase 0: baseline fingerprint for invariant 1".

## 3. Phase 1 — configuration (`config_1.py`)

Add, with the ADR defaults:

```
policy_interruption_mode = "off"      # {"off", "d2"}
interruption_delta = 1                 # fixed at 1
interruption_cost_c = float("inf")     # c
interruption_cost_c_Z = float("inf")   # c_Z
skill_cap_k_max = 10                   # k_max
team_cap_k_Z = None                    # k_Z; None -> k_max
age_feature = "off"                    # {"off", "normalized"}
```

Validation: the assertion `episode_length % k == 0` at `config_1.py:719` stays in `off`; in `d2`
replace it with `1 <= k_max <= episode_length` and `k_max <= k_Z <= episode_length`. Keep `k`
untouched so D0 (`d2`, `c = c_Z = inf`, `k_max = k_Z = k`) is reachable without changing `k`.

Commit: "D2 phase 1: parameters and validation".

## 4. Phase 2 — coordinator API (`hmasd/networks.py`, `SkillCoordinator`)

Two new methods; `assign_and_value_batch` (`networks.py:787`) and `evaluate_training_batch`
(`networks.py:868`) stay untouched for `off`.

1. `evaluate_held_batch(state, observations, held_Z, held_z)` — one teacher-forced pass in
   canonical order over the held joint action. Returns: `Z_logits`, per-agent `z_logits`
   `[B, N, n_z]`, `state_values`, `agent_values`. From these the caller computes
   `g_Z = max_Z log pi(Z) - log pi(held_Z)` and `g_i = max_z ell_i(z) - ell_i(held_z_i)` with
   `ell_i(z) = log pi(z | Z_held, z_held_{<i})`. This method must not sample and must not draw RNG.
2. `assign_partial_batch(state, observations, held_Z, held_z, sample_Z_mask[B], sampled_mask[B, N],
   deterministic)` — decode in order `O_t`: the team token first (sampled where `sample_Z_mask`,
   forced to `held_Z` otherwise), then kept agents in canonical order as forced tokens, then `S_t`
   agents in canonical order sampled. Positional encoding follows decode position, exactly as the
   current decoder does with `step`. Returns the new joint assignment, per-agent log-probabilities
   with zeros at forced positions, team log-probability zero where not sampled, values, and the
   decode order `O_t` as an index tensor `[B, N]`.
3. `evaluate_training_batch_ordered(state, observations, team_skills, agent_skills, order[B, N],
   sampled_mask[B, N], sample_Z_mask[B])` — teacher-forced replay in the stored order; returns
   per-agent log-probabilities and entropies with zeros at forced positions, team terms zero where
   not sampled. This is what PPO calls in `d2`.

Note for the decoder: `SkillDecoder.forward` (`networks.py:525-`) takes `z[:, :step-1]` as the
prefix and `agent_specific_query` for the agent being decoded; in `d2` the prefix is the held or
newly sampled skills in `O_t` order and the query is the encoded observation of the agent at that
position. No new parameters are introduced (ADR: "D2 adds no coordinator parameters").

Commit: "D2 phase 2: held-evaluation, partial assignment, ordered replay on SkillCoordinator".

## 5. Phase 3 — rollout logic (`hmasd/agent.py`, `_batched_assign_skills` at 1865)

Guard the whole block with `mode == "d2"`; `off` keeps lines 1885-1975 as they are.

Per step, for every env:

1. Ages: `a_i` from `env_skill_ages` (already maintained on the HA-CTSE path; make the base path
   maintain it in `d2`), new `env_team_ages[env]`.
2. Reset, done, or invalid skills (the existing `invalid_skills_mask`, `dones_batch`): team decision,
   all agents sampled, ages reset. Boundary cause code `reset`.
3. Otherwise call `evaluate_held_batch`; compute `g_Z`, `g_i`.
4. Team decision if `g_Z >= c_Z` or `a_Z >= k_Z`. If team decision: `sampled_mask = all`, cause
   `team_gap` or `team_cap`.
5. Else `sampled_mask[i] = (g_i >= c) or (a_i >= k_max)`, cause `gap` or `cap` per agent.
6. If any sampled: `assign_partial_batch`; update held skills for sampled positions; ages of sampled
   agents to 0, others `+1`; team age to 0 if team decision else `+1`. If none sampled: ages `+1`,
   no RNG draw, no buffer row.
7. Hand to storage (Phase 4): the sampled mask, order, sample-Z flag, log-probabilities, values,
   cause codes.

Metrics per step (accumulate, log at rollout end): `g_i`, `g_Z` histograms, `|S_t|`, switch rate by
agent index, boundary-cause counts, sampled/forced counts, coordinator inference time
(`_add_transition_profile` exists at `agent.py:1131`).

Invariant checks that belong in code (cheap asserts, `d2` only): `c = inf` implies no `gap` cause;
team decision implies `sampled_mask.all()`.

Commit: "D2 phase 3: per-step interruption test and partial re-assignment".

## 6. Phase 4 — storage (`hmasd/utils.py` `RolloutBuffer`, `hmasd/agent.py` storage helpers)

`off` keeps the `[T, E]` arrays at `utils.py:243-255` and the helpers
`_should_close_high_level_sample` (2724), `_store_coordinator_experience` (2743),
`store_transition` (2990) unchanged.

`d2` adds, allocated only in `d2`:

- Per-agent segment table `[T, E, N]`: `valid`, `reward` (discounted within-segment sum),
  `elapsed`, `terminal`, `value` (bootstrap value at segment start), `old_log_prob`,
  `sampled_mask`, `order` (int), plus `Z` and `z` tokens of the assignment the row belongs to.
- Team table `[T, E]`: `valid`, `reward`, `elapsed`, `terminal`, `value`, `old_log_prob`,
  `sample_Z`.
- Open-segment bookkeeping per `(env, agent)` and per env for the team: start step, running
  discounted sum `sum_u gamma^u r`, age. A row is written at the segment's start index when the
  segment closes (as the current code does at `agent.py:2797`, `elapsed_steps`).
- Close rules: an agent segment closes when the agent is sampled, at episode end (`terminal`), or at
  rollout end (bootstrap with the value of the next state, as `compute_high_level_advantages` does
  today via `high_level_last_values`). The team segment closes on a team decision, episode end, or
  rollout end. A team decision closes every agent segment (invariant 7).
- Within-segment reward: the shared reward is the mean over agents (`agent.py:3019-3022`); keep that
  scalar `r_t` and accumulate `gamma^u r_t` in `d2`, undiscounted in `off`.

Commit: "D2 phase 4: per-agent and team segment tables".

## 7. Phase 5 — advantages (`compute_high_level_advantages`, `utils.py:681`)

`off` unchanged. `d2`: run the existing discounted-GAE routine (`_compute_gae_with_discounts_torch`,
`utils.py:803`) once per `(env, agent)` sequence over that agent's valid rows with
`discounts = gamma^elapsed`, and once per env for the team table. Value normalisation is per head
(`use_valuenorm`, `config_1.py:199`; `_denormalize_values`, `agent.py:1294`): agent columns use the
existing per-column path (`agent.py:1931-1942`); add the team normaliser for the team table.

Commit: "D2 phase 5: per-agent SMDP advantages".

## 8. Phase 6 — update (`update_coordinator`, `agent.py:4678`; `get_coordinator_sampler`, `utils.py:1026`)

`off` unchanged. `d2`:

- Sampler rows are `(t, e)` pairs where at least one agent row or the team row is valid; each row
  carries the `[N]` masks and tables.
- Replay with `evaluate_training_batch_ordered`.
- Ratios: the current code forms `agent_ratios` as `[B, N]` (`agent.py:4876-4879`); multiply the
  per-agent policy loss and entropy by `sampled_mask` and by the agent's `valid`; team ratio and
  entropy by `sample_Z`. Value losses per agent row and team row use their own returns.
- The high-level entropy coefficient `lambda_h` applies to the masked sums (ADR: entropy sums over
  sampled positions only).
- Log: `M` (rows per rollout), optimiser steps, `||theta - theta_0|| / ||theta_0||` for the
  coordinator (store `theta_0` at construction), target variance and scale versus D0.

Commit: "D2 phase 6: masked PPO update and exposure logging".

## 9. Phase 7 — discriminator age input (`networks.py` `TeamDiscriminator` 1475, `IndividualDiscriminator` 1534; `agent.py` `_compute_intrinsic_rewards_batch` 3340)

`age_feature = "off"`: modules unchanged (checkpoint compatibility for `off`).
`age_feature = "normalized"`: input dimension grows by one; append `a_i / k_max` to the individual
discriminator input and `a_Z / k_Z` to the team discriminator input, both at reward computation
(`agent.py:3340-3420`) and at discriminator training (`agent.py:5516-5600`, where the buffer must
also store the ages alongside the discriminator samples). The ages are those at the step the
transition was collected.

Commit: "D2 phase 7: discriminator age feature".

## 10. Phase 8 — tests and report

`tests/flexible_skill_duration_d2_test.py`, all with the Phase 0 small configuration unless stated:

| Test | Invariant | Setup | Assertion |
| --- | --- | --- | --- |
| 1 | 1 | `off`, Phase 0 seed | fingerprint equal to Phase 0; no `d2` attribute allocated |
| 2 | 2 | D0 (`d2`, `c = c_Z = inf`, `k_max = k_Z = k`) vs `off`, same seed, with one mid-rollout reset | team and agent boundary masks equal; logged target-scale ratio close to `tau(1-gamma)/(1-gamma^tau)` on a constant-reward episode (about 1.046 at `tau = 10`) |
| 3 | 3 | `d2`, `c = c_Z = inf`, `k_max = 7`, `k_Z = 40` | no `gap` cause; every agent boundary at age 7; team boundary only at reset or age 40 |
| 4 | 4 | `d2`, `c = c_Z = 0` | `sampled_mask` all ones every step |
| 5 | 5 | scripted `S_t` (monkeypatch the gap) | per-agent closed or bootstrapped lengths sum to live steps |
| 6 | 6 | one stored row with non-contiguous `S_t` and a known order | replay log-probability equals the sum over sampled positions; forced positions zero; entropy likewise |
| 7 | 7 | force a team decision at a chosen step | every agent segment closes at that step |
| 8 | 8 | hand-built three-step rewards | `[T, E, N]` and `[T, E]` shapes; targets equal the ADR formula; ages equal `a_i / k_max`, `a_Z / k_Z` |
| 9 | III.1.3 | two `d2` runs at `c = inf`, same seed | identical rollouts (trigger path draws no RNG) |

Report, saved as `docs/Claude_docs/plans/D2_IMPLEMENTATION_REPORT_<date>.md` (check
`git check-ignore`): the test command and full output, the Phase 0 fingerprint hash, one smoke
rollout per mode with the metric summary (`|S_t|`, causes, `M`, inference time ratio `d2 / off`),
the diff stat per phase, and any place where the plan and the ADR disagreed. Record the answers to
P1 and P2 from the smoke rollout at `c = 0` (Part I §5, Part III §III.2); do not interpret them.

## 11. Acceptance checklist (reviewer side)

- All nine tests pass under the explicit interpreter with the isolated basetemp.
- `git diff` shows no change inside any function reachable in `off` except added guarded branches,
  and no change to checkpoint keys in `off`.
- No new file outside the four source files, the test file, and the report.
- The ADR's eight invariants each map to a passing test; III.1 items 2 and 3 are covered by tests 2
  and 9.
- The report's smoke rollout at `c = 0` shows the chattering floor near 5/6 for an untrained
  coordinator (P2); a value far from it is a bug in the gap computation, not a result.

## 12. Sizing

Phases 2, 4, and 6 carry most of the work (new coordinator methods, the per-agent tables, the masked
update); phases 1, 3, 5, 7 are small; phase 0 and 8 are bookkeeping. Order is fixed: 0 before any
edit, 2 before 3, 4 before 5 before 6. Expect the diff to be dominated by `hmasd/utils.py` and
`hmasd/agent.py`.
