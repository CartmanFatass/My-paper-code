# Adversarial review of ADR 01 (D2 interruption) and ADR 02 (relay corridor), 2026-09-02

Reviewer: Claude Code (Fable 5.1), session `session_015hGLzLCuJLFFtZTboKg2bd`. Objects reviewed:
`../plans/ADR_01_D2_POLICY_INTERRUPTION.md` and `../plans/ADR_02_RELAY_CORRIDOR_HOST.md`, drafted
by GPT Pro on 2026-09-02 from `../plans/ADR_REQUEST_PROMPT_GPT_PRO_20260902.md`. Every code claim
below was re-read against the working tree at commit `1f52513c3` plus the pre-existing uncommitted
Codex changes. Nothing was run. Tutoring-protocol role: the owner keeps the design; this document
attacks it and lists the decisions that only the owner can take.

Verdict in one line each:

- **ADR 01: REVISE before implementation.** The citations are sound, but the interruption
  statistic is not a quantity the current coordinator can produce, the forced boundary is
  undefined in a way that decides whether E3 can succeed at all, the team-code rule is incomplete,
  invariant 3 contradicts the decision text, and the resolution arithmetic is wrong by roughly two
  orders of magnitude.
- **ADR 02: REVISE before implementation.** It records parameters, references, and invariants
  faithfully from the environment advice, but it does not define the host: no state, action, latent,
  hazard mechanism, or reward rule. Its own third open question ("what corridor dynamics realize the
  calibrated margins") is the entire content an ADR for a host has to supply.

The rest is organised as: 0 citation audit, 1 ADR 01 findings, 2 ADR 02 findings, 3 what to keep,
4 decisions the owner must take, 5 predict-then-verify prompts.

## 0. Citation audit

| ADR claim | Verified location | Status |
| --- | --- | --- |
| Reassignment at `env_steps % k == 0`, joint autoregressive sampling | `hmasd/agent.py:1897`, `1921` | correct |
| Horizon-window forced masks "drifted to 2067–2095" | `hmasd/agent.py:2077-2095` | correct, but see F1.6: that call goes to `hmasd/ha_ctse.py:633`, the HA-CTSE editor, not the base coordinator |
| Elapsed-step storage | `hmasd/agent.py:2797` | correct |
| Undiscounted within-segment reward sum | `hmasd/agent.py:3019-3026` (mean over agents of the shared reward, summed) | correct |
| Discriminators around 3340–3465 omit age | `hmasd/agent.py:3340` (`_compute_intrinsic_rewards_batch`); inputs are next state, next obs, team skill | correct |
| Per-agent value heads | `hmasd/networks.py:726-729` | correct |
| Gains 1.0 (embeddings) and 0.01 (value heads); `SkillDecoder` default init | `hmasd/networks.py:733-738`; no `_init_weights` inside `SkillDecoder` (525-) | correct |
| `gamma^elapsed` bootstrap | `hmasd/utils.py:737-741` | correct |
| `k = 10`, `gamma = 0.99`, `lr_coordinator = 1e-4`, `ppo_epochs = 15`, `num_envs = 32`, `rollout_length = 500`, `total_timesteps = ×200`, `eval_episodes = 8` | `config_1.py:134,148,152,158,181-183,196` | correct |
| "Scenario 1 defaults to five UAVs" | `config_1.py:25` has `n_agents = 6`; five is the `main.py` CLI default `--n_uavs 5` | ambiguous, must pin one |
| Scenario 1 reward: coverage, SINR quality, height penalty | `envs/pettingzoo/scenario1.py:78-112` (coverage weight 0.7, SINR quality, energy penalty 0.1 × normalised height) | correct |
| Coarse exposure `1e-4 × 200 = 0.02` | see F1.8; the coordinator takes about 3.9e4 Adam steps, not 200 | wrong |
| `VariableRosterEventCore._close_trace` | not re-verified here | unverified |

Line numbers above are from the current working tree, which carries 96 uncommitted Codex paths;
the committed `hmasd/agent.py` may differ by a few lines.

## 1. ADR 01 findings, ranked

### F1.1 (blocking) The interruption statistic is not computable by the current coordinator

The decision defines `ℓ_i(z) = log π(z_i = z | s_t, o_t, Z, z_{-i}^{held})`, "force other held skills
as tokens". The decoder is causal in a fixed agent order: at step `i` it sees `Z0, Z, z_1 … z_{i-1}`
with positional encoding, and agent identity enters only through `agent_specific_query`
(`hmasd/networks.py:614-644`; sampling loop `networks.py:815-835`). There is no conditional on
`z_{-i}` for any agent but the last one. To obtain it one would have to place the other `N−1` held
skills before agent `i`, which is a (position, agent) arrangement the network never sees in training,
because PPO replays the stored joint action by teacher forcing in canonical order
(`evaluate_training_batch`, `networks.py:868-876`). The trigger would then be evaluated on an
out-of-distribution ordering while the training signal is evaluated on the canonical one.

Three repairs, one to be chosen by the owner (section 4, decision 1):

- (a) **Causal-prefix test.** `ℓ_i(z) = log π(z | Z, z^{held}_{<i})` in canonical order; one
  teacher-forced pass over the held joint action gives every agent's conditional at once. In
  distribution, cheapest, identical to what the PPO ratio evaluates. Cost: agent `i`'s test ignores
  agents after it, so the first agent in canonical order switches on the least information. This is
  an order artefact that must be logged (switch rate by agent index).
- (b) **Agent-last test.** Put `i` last; accept the distribution shift or remove it by training the
  coordinator with random decode orders (permutation augmentation). Changes the base learner; invariant
  1 then only holds if the augmentation is inside the mode switch.
- (c) **Marginal by sampling.** Correct but needs several forward passes per agent per step; rejected
  on cost at δ = 1.

Recommendation: (a) for E1/E2. It is also the only option under which "kept agents first, S in
canonical order" costs nothing extra, because kept agents are simply the teacher-forced prefix.

### F1.2 (blocking) "Forced k-boundary" is undefined, and one reading makes E3 unwinnable

Two readings of "no renewal before a forced k-boundary":

- **Global clock**: the existing `env_steps % k == 0` trigger stays. Interruptions can only shorten
  segments; every agent re-synchronises every `k` steps; no segment ever exceeds `k`. The E3
  hypothesis (plan §5: D2 beats the best fixed `k` on a heterogeneous-hazard host) needs longer
  holds where hazard is low. Under a global clock that gain is impossible by construction; D2
  degenerates to "fixed k with early exits" and can at best match the best fixed `k`.
- **Per-agent clock**: agent `i` is forced to re-decide `k_max` steps after its own last switch.
  Boundaries drift apart; segment length is bounded by `k_max`, and the owner's Q4 prediction (mean
  length saturates at `H`) requires `k_max = H` or no cap.

The ADR must state which. Recommendation: per-agent cap `k_max`, swept, with `k_max = H` as one
point. Note that `config_1.py:719` asserts `episode_length % k == 0`; under per-agent clocks the
assertion is meaningless but still fires, so the mode switch must bypass or keep it deliberately.

### F1.3 (blocking) The team-code rule does not say what a Z switch does to held individual skills

Individual skills were sampled conditioned on the old `Z` (decoder prefix, `networks.py:626`), and
the individual discriminator is conditioned on `Z` (`agent.py:3405-3420`, team skill tensor passed
to `_individual_discriminator_logits`). After `Z` is resampled, every held `z_i` is a token drawn
from a different conditional and rewarded by a discriminator that now reads a different `Z`. Two
options: a `Z` switch forces `S_t` = all live agents (every agent segment closes when the team
segment closes), or `z_i` is held across the `Z` change and drifts. Recommendation: force all. That
gives a clean invariant the ADR currently lacks: team-segment boundaries are a subset of every
agent's segment boundaries.

The `Z` value target is also missing: the state value head `V(s)` (`networks.py:726`) needs its own
segment `τ_Z`, discounted reward, and `γ^{τ_Z}` bootstrap. The decision only writes the agent target.

### F1.4 (blocking, definitional) Invariant 3 contradicts the decision text

The test is strict, `max_z ℓ_i(z) − ℓ_i(z_i^{held}) > c`. At `c = 0` an agent whose held skill is
already the conditional argmax has gap 0 and is not re-selected, so "every live agent re-selects every
step" is false. The ADR patches this with a definitional override ("At c = 0, S_t is all live
agents"), which makes `c = 0` discontinuous from `c = 0+`. Choose one: define the rule with `≥ c`, or
restate invariant 3 as "at c = 0 every agent whose held skill is not the conditional argmax
re-selects", and keep `c = 0` continuous. Decision 4 in section 4.

Related: with default `c = c_Z = +∞`, mode `d2` at defaults is fixed-`k` with a different target
definition. Say so explicitly; it is the baseline of F1.5.

### F1.5 (blocking for E2, not for the mechanism) The fair baseline is `d2` at `c = ∞`, not `off`

Mode `d2` replaces the undiscounted segment sum (`agent.py:3026`) with a discounted one and changes
the bootstrap. So `d2` with `c = c_Z = ∞` is not numerically `off`. E2's comparison "D2 versus D0
swept over k" must use `d2, c = ∞` as D0; comparing against `off` confounds the reward-definition
change with the interruption effect. Add invariant 7: at `c = c_Z = ∞`, `d2` produces the same segment
boundaries as `off` on the same seed (only targets differ), with a test that checks boundary
equality and logs the target-scale ratio (the bias factor τ(1−γ)/(1−γ^τ) ≈ 1.05 at τ = 10, γ = 0.99).

### F1.6 (must fix) The "existing keep/edit mask path" does not exist on the base route

Plan §8 item 2 and the ADR's context lean on forced keep/edit masks. Those live in the HA-CTSE
editor (`hmasd/ha_ctse.py:633-660`, `forced_keep_mask`, `forced_edit_mask`), which decision D
rejected as the first route. The base coordinator's `assign_and_value_batch`
(`hmasd/networks.py:787`) takes `(state, observations, deterministic)` and nothing else. D2 needs a
new argument set on the base coordinator: forced prefix tokens for kept agents, a sampled set, and a
return of per-agent log-probabilities with zeros on forced positions. The ADR's touch-point list
should say this, because it is the largest code change in the object.

### F1.7 (must fix) The rollout buffer must store the decode ordering and forced set

Invariant 5 and its test presuppose that PPO replay can recompute `Σ_{i∈S_t} log π` under new
parameters. `evaluate_training_batch` teacher-forces the stored joint action in canonical order.
With "kept first, then S", the replay must reproduce the same ordering, so each high-level sample
needs: the kept set, the order used, and the forced tokens. The decision does not require this
storage. Add it to the decision and to the metrics (sampled versus forced counts already listed).
The high-level entropy bonus (`lambda_h`, `config_1.py:165`) must likewise sum over `S_t` only.

### F1.8 (must fix) Resolution arithmetic is wrong by about 200×

The coordinator update samples minibatches of `coordinator_batch_size = 128`
(`hmasd/agent.py:4747`). Per rollout there are `32 × 500 / 10 = 1,600` high-level samples, so about
13 minibatches per epoch, `15` epochs, `200` rollout updates:

| Quantity | Value |
| --- | --- |
| Adam steps for the coordinator | ≈ 13 × 15 × 200 ≈ 3.9e4 |
| Displacement bound lr × steps | ≈ 3.9 per coordinate |
| GPT Pro's figure | 0.02 |

`200` is the rollout-update count, not the optimiser-step count. The conclusion flips: at this budget
the displacement bound exceeds every initialisation scale (1.0 and 0.01), so exposure is not the risk;
saturation and instability are. The spec §11.4 exposure line should therefore be *measured*
(parameter displacement norm relative to the initial norm at each checkpoint), not bounded from
lr × steps. The `σ/√8` return-resolution statement is fine, but `eval_episodes` is 8 in
`config_1.py:196` and 10 on the `main.py:51` CLI; pin the entry point.

### F1.9 (should fix) Invariant 4 holds only because rollout length equals episode length

`rollout_length = episode_length = 500` (`config_1.py:39,182`). If either changes, segments are
truncated at rollout boundaries and bootstrapped, and "closed segment lengths sum to the episode
length" fails. Restate: the sum of segment lengths (closed, or truncated with bootstrap) equals the
number of steps the agent was live in the episode; an episode end closes every open segment with the
terminal flag (close reasons at `agent.py:2798-2800`).

### F1.10 (should fix) Name the credit-unit change as the main risk

Under asynchronous segments, agent `i`'s segment reward is the mean shared reward over its own window
while other agents switch inside that window (`agent.py:3019-3026`). This is the credit change the
ledger §9.1 describes, accepted as suboptimal under spec §11.3, but the ADR's risk list does not name
it. Log per-agent target variance in `d2` against `d2, c = ∞`, which the metrics section almost does.

### F1.11 (minor) Compatibility switch is a tuple, not one flag

`off` must imply `age_feature = off`, the undiscounted sum, the global clock, and no extra RNG
draws. Define `off` as that tuple. Test 1 should state what "byte equality" covers: per-step
`(Z, z, log-prob, high-level reward)` sequences and the checkpoint state dict; if the `d2` code path
consumes any RNG in `off` mode, equality fails silently on the first sample.

### F1.12 (minor) Age feature under per-agent clocks

If decision 2 picks per-agent caps, `elapsed_over_k` should be `a_i / k_max`, and `a_Z / k_Z` for the
team code, since `k` alone no longer names the bound.

## 2. ADR 02 findings, ranked

### F2.1 (blocking) The host is not defined

The decision section lists what the host returns and how it is seeded, but not what it is. Missing:
the state (what a cell, a relay, a demand entity carries), the per-agent action (choose a zone, a
role, a relay target?), the latent (which demand pattern is active), the hazard mechanism (how λ
switches the latent, what "two regions" means for an agent), how the per-step reward in `[0, 1]` is
produced, what the probe observes, and what the structure-blind cut removes. Without these,
invariant 5 cannot be instantiated and tests 4 to 6 cannot be written. The environment advice §4 is
one paragraph of parameters for the same reason: it invited the owner to write the mechanism. That
is the owner's design task under the tutoring protocol; the checklist above is what the revised ADR
has to contain, in the order state, action, latent, hazard, reward, probe, cut.

### F2.2 (blocking) The reference ordering and margin definition are inconsistent with the advice

The advice names oracle (has the latent), heuristic (greedy on public state), and structure-blind
(the learner with the mechanism cut), and defines `m` as the reward gap between the oracle plan and
the best structure-blind plan. The ADR asserts `J_G ≤ J_B ≤ J_O` and calibrates `J_O = J_B + m_q`.
Two problems: `J_B` is a training outcome, so a margin defined against it cannot be calibrated before
training; and there is no reason a greedy heuristic sits below a learned structure-blind policy.
Fix: define `m` from the host's own contrast, computable without learning (oracle plan value minus the
best open-loop or fixed-plan value, both closed-form or exhaustively enumerable at toy scale), and
report `J_G` as a reference with no ordering asserted.

### F2.3 (blocking) The structure-blind cut for the duration direction must be named

For this direction the mechanism under test is interruption. The structure-blind control is therefore
the same learner at `c = c_Z = ∞` (D0), and the "structure removed" is the ability to end a segment
early. The ADR should say this rather than leave "target structure removed" abstract, because it
fixes what test 5 compares.

### F2.4 (must fix) Heavy-tailed law needs a finite mean and a matched mean

E4 compares deterministic, exponential, and heavy-tailed `D`. "At least ten segments" and any
stationary hazard comparison need `E[D] < ∞`; the plan's E4 signal "D0 and D8 degrade with Var(D)"
needs `Var(D) < ∞`. A Pareto with `α ≤ 2` breaks the second. Recommendation: lognormal with the
three laws matched on `E[D]` so that the comparison is about the law, not the scale. The
deterministic law is also the point where a fixed `k = D` is optimal; the oracle at that point is
"fixed `k* = D`", which is the natural D0 tuning target for E4.

### F2.5 (must fix) "Two λ regions" must say whether heterogeneity is across agents or across time

If agents are pinned to regions, heterogeneity is across agents and the E3 hypothesis is tested with
per-agent clocks only (F1.2). If agents move between regions, heterogeneity is across time for one
agent and a global clock could in principle also profit. The cheaper, sharper object is agent-pinned
regions; say which.

### F2.6 (should fix) Invariant 6 is a benchmark, not an invariant

"≈ 1e4 steps/s/core" is not falsifiable across machines. Make it a logged metric with a target and a
pinned machine description (as `docs/project/EFFICIENCY_PRACTICES.md` does), or state the test as
"ratio to a reference numpy loop on the same machine".

### F2.7 (should fix) Events need identities for the per-entity RNG rule

Renewal events (E4) and hazard switches are not entities; invariant 2 keys streams by entity id only.
Give each region's event process its own stream keyed by `(master seed, episode, region id)`, or
declare events as entities.

### F2.8 (minor) Resolution arithmetic is copied from ADR 01

Same 200× error (F1.8), and the E3/E4 learner will have a different observation layout and parameter
count from scenario 1. Defer the numbers to the exposure line; do not repeat them here.

### F2.9 (minor) Test location

`tests/relay_corridor_host_test.py` is valid for a host under `envs/`. If the host lands under
`experiments/candidates/<impl>/`, the tests must be `tests/experiments/candidates/<impl>/test_*.py`
(CLAUDE.md, `.gitignore` rule). Decide with the implementation path.

## 3. What to keep from the drafts

- The citation audit is honest: drift was flagged where it existed, and the "could not verify" list
  names exactly the numbers the repository does not contain.
- Scope discipline is intact: no learned termination, no menu, no variable `N`, no C-class contract,
  two-level `Z` respected, Codex as implementer respected.
- Invariants 1, 2, 5, 6 of ADR 01 and 1, 3, 4 of ADR 02 are the right falsifiable statements and
  survive unchanged.
- The parameter tables are complete against the advice and plan; only defaults and the `c = 0`
  semantics need repair.

## 4. Decisions the owner must take before the ADRs are re-issued

1. Interruption statistic (F1.1): causal-prefix test, agent-last test, or random-order training.
2. Forced boundary (F1.2): global clock or per-agent cap `k_max`.
3. Effect of a `Z` switch on held `z_i` (F1.3): force all agents to re-decide, or hold.
4. `c = 0` semantics (F1.4): rule with `≥ c`, or restated invariant 3.
5. Corridor mechanics (F2.1): the owner writes state, action, latent, hazard, reward, probe, cut, or
   asks for a candidate to attack (which reverses the protocol for this one object).
6. Heavy-tailed law (F2.4): lognormal mean-matched, or Pareto with `α > 2`.

Everything else in sections 1 and 2 is a wording or bookkeeping repair Codex can make once these six
are fixed.

### 4.1 Decisions taken with the owner, 2026-09-02 (confirmed one by one in session)

| # | Decision |
| --- | --- |
| 1 | Causal-prefix test: `ℓ_i(z) = log π(z | Z, z^{held}_{<i})` in canonical order, one teacher-forced pass; switch rate by agent index is a required metric |
| 2 | Per-agent forced boundary: agent `i` re-decides `k_max` steps after its own last switch; `k_max` swept, `k_max = H` included; the `episode_length % k` assertion at `config_1.py:719` is handled inside the mode switch |
| 3 | A `Z` switch forces `S_t` = all live agents; new invariant: team-segment boundaries are a subset of every agent's segment boundaries |
| 4 | Interruption rule uses `gap ≥ c`; invariant 3 stands as written; `c` is continuous at 0 |
| 5 | The owner writes the corridor mechanics (state, action, latent, hazard, reward, probe, cut), GPT Pro may draft; Claude attacks the result |
| 6 | E4 heavy-tailed law is lognormal, with the three laws matched on `E[D]` |

Next step: the owner re-issues both ADRs with these six decisions and the must-fix items F1.5 to
F1.8, F2.2 to F2.5 applied; Claude reviews the re-issue; Codex implements only after that.

## 5. Predict-then-verify prompts for the owner

- P1. Under the causal-prefix test, which agent index switches most often, and why? (Answer to be
  recorded before E1 runs; the metric "switch rate by agent index" is the check.)
- P2. At `c = 0` with the `≥ c` rule, `δ = 1`, `n_z = 6`, and an untrained coordinator, what fraction
  of agents switch per step? (Reason from a near-uniform policy: the held skill is the argmax with
  probability about 1/6, so roughly 5/6 of agents switch each step. This is the chattering floor
  that any finite `c` must clear.)
- P3. If `E[D]` is matched across the three renewal laws in E4, which law gives the fixed-`k` learner
  the largest loss at its best `k`, and does the ranking change if only the median is matched?

---

# Part II — round-2 review of the re-issued ADRs (2026-09-02, later)

Objects: revision 2 of both ADRs (stored at the same paths; revision 1 is at commit `ea20bccb0`).
Citations re-verified against the working tree at `9cc2a8ff2` plus uncommitted Codex paths.

Verdict in one line each:

- **ADR 01: ACCEPT WITH TWO CHANGES.** All six §4.1 decisions and every must-fix item from Part I
  are applied, and the arithmetic is now correct. Two structural gaps remain: the team cap
  re-synchronises every agent, which undoes most of the per-agent-clock decision at any
  `k_max < H` (II.1), and the per-agent segment storage the decision needs is not named (II.2).
  Both are additions, not reversals. After them Codex can start.
- **ADR 02: HOLD, as it says itself.** The contract part is now consistent. One addition is
  required before the owner writes the mechanics: the margin it registers is not the quantity E3
  measures (II.7).

## II.0 Citation audit, round 2

| ADR claim | Verified location | Status |
| --- | --- | --- |
| `SkillCoordinator.assign_and_value_batch` samples causally | `hmasd/networks.py:787-835` | correct |
| Forced masks only in `HorizonSkillEditor.assign_and_value_batch` | `hmasd/ha_ctse.py:284` (class), `633-660` (method) | correct |
| `get_coordinator_sampler` keeps the partial batch | `hmasd/utils.py:1026`, batching loop `range(0, n, batch)` with `min(...)` end | correct, so the ceiling is right |
| Coordinator batch 128 "in the pinned Config" | `hmasd/agent.py:4747` is a `getattr` default; `config_1.py` has no `coordinator_batch_size` | wording: an agent-side default, not a Config field |
| Adam steps about 39,000, lr times steps about 3.9 | recomputed | correct |
| `Config` `N = 6`, `n_uavs = 6` | `config_1.py:25` has 6, but `main.py:58` defaults `--n_uavs 5` and `main.py:410` overwrites `config.n_agents = env.n_uavs` | the pin only holds if the run passes `--n_uavs 6`; say so |
| Observation layout at `uav_env.py:122-126` | those lines are SINR threshold and power-cost parameters; the layout is `uav_env.py:138` (obs_dim formula) and `_get_observation` at `353` | wrong lines, right content |
| Scenario 1 reward | `envs/pettingzoo/scenario1.py:78-112` | correct |
| Eight evaluation episodes | `config_1.py:196` for in-training evaluation; `main.py:51` CLI default is 10 for `--mode eval` | still unpinned; state which |

## II.1 (must fix) The team cap re-synchronises all agents at every `k_max`

The decision says a team decision, team cap, reset, or invalidity makes `S_t` all live agents, and
that the team clock uses the same `k_max` cap as the agent clocks. Consequence: the team cap fires
`k_max` steps after the last team decision, and at that moment every agent is forced. An agent that
switched early has a younger age than the team, so its own cap never fires before the team cap.
Per-agent caps therefore never bind; the only asynchrony left is early exits, and the whole roster
re-synchronises at multiples of `k_max`. At `k_max < H` this is the global-clock reading of Part I
F1.2 with `k` renamed, and the E3 mechanism (hold longer where hazard is low) is again capped and
re-synchronised. At `k_max = H` the problem vanishes, which is why the draft does not notice it.

D0 parity does not need the shared cap: at infinite costs there are no early exits, every agent age
equals the team age, and all caps fire together whether or not they are the same parameter.

Fix, an added parameter rather than a rule change: a separate team cap `k_Z`, default `k_max`
(parity with D0 and with `off`), swept to `H` for E3/E4 so that the team code is re-decided only by
interruption or reset. Keep "every team decision forces all agents" (decision 3, invariant 7). State
explicitly that at `k_Z < H` the team cap re-synchronises the roster, so the E3 object must run with
`k_Z = H`.

## II.2 (must fix) Per-agent segment storage is missing from the decision

The buffer stores one high-level row per `(step, env)`: scalar `high_level_valid_mask`,
`high_level_rewards`, `high_level_elapsed_steps`, `high_level_terminal`, `high_level_close_reason`
(`hmasd/utils.py:243-255`); only the log-probabilities and advantages already carry an agent axis
(`utils.py:250, 285-287`). The GAE at `utils.py:721-748` walks one sequence per env. With per-agent
segments, each agent needs its own valid mask, segment reward, elapsed length, terminal flag, and
bootstrap value, and the team code needs the same set with its own length. The decision names three
stored objects (order, forced tokens, sampled mask) and none of these. Add: in `d2` the high-level
buffer holds a per-agent segment table `(valid, reward, elapsed, terminal, value)` of shape
`[T, E, N]` plus a team table `[T, E]`; `off` keeps the current arrays. This is the largest code
change in the object and belongs in the touch points; invariant 8 would fail without it, but the ADR
should not rely on a test to discover a design element.

## II.3 (should fix) Sample-count collapse at large `k_max` is the binding resolution term

At `k_max = H = 500` and infinite costs, each agent has one segment per episode, so `M = 32` rows
per rollout, one minibatch, 3,000 Adam steps, and 32 high-level samples per update. `M` scales as
`32 x 500 / mean segment length`. The exposure line covers optimiser steps; the ADR should name `M`
per rollout as the quantity that shrinks with long holds and record it beside displacement. It is
already in the metrics list ("high-level samples"); the risk section should say why it matters.

## II.4 (should fix) The interruption check multiplies coordinator inference by `k`

At `delta = 1` the teacher-forced pass runs every step for every env instead of every `k` steps. At
`k = 10` that is ten times the coordinator inference of `off`. Not a correctness issue; it belongs in
the risks and in the plan speed budget, since scenario 1 on CPU is already slow.

## II.5 (minor) Wording repairs

- `n_uavs = 6`: state the entry-point pin (`--n_uavs 6`, or a preset) because `main.py:410`
  overrides `Config`.
- `eval_episodes`: pin "in-training evaluation, `config_1.py:196`, eight episodes".
- Observation-layout citation: `uav_env.py:138` and `353`.
- "The pinned `Config` has coordinator batch 128": it is the `getattr` default at `agent.py:4747`.
- Age normalisation: with `k_Z` separate, the team age is `a_Z / k_Z`.

## II.6 ADR 02: what round 2 fixed

Mechanics deferred to the owner with an explicit block; `m` defined from enumerable plans rather
than a trained policy; greedy carries no ordering; D0 named as the duration-structure-blind cut;
agent-pinned regions; region-keyed event streams; lognormal with matched mean; speed as a
recorded-machine target. All consistent with Part I §4.1.

## II.7 (must fix before the mechanics) The registered margin is not what E3 measures

`m = J*(oracle plan) - J*(best open-loop or fixed plan)` is the latent-structure margin from the
environment advice: it measures how much knowing the latent is worth. The E3 claim is different: D2
beats the best fixed-`k` policy on a heterogeneous-hazard host. The quantity that has to be
resolvable is a duration margin,

    m_dur = J*(oracle that knows the latent and switches at hazard events)
          - max over k of J*(oracle that knows the latent but may switch only every k steps),

both computable by enumeration at toy scale once the mechanics exist. `m_dur` is the number the
ledger min-over-k max-regret bound predicts from the two hazard rates, and it is the number the E3
evaluation budget must exceed by the factor three the advice requires. Register both margins: `m`
for the host calibration, `m_dur` as the E3/E4 acceptance scale, and require `m_dur` to be at least
three times the declared resolution term. Without `m_dur`, a host can pass all three `m`
calibrations and still make E3 undecidable, because the best fixed `k` may already be within noise
of the switching oracle.

## II.8 (should fix) "Ten segments at the largest cap" conflicts with `k_max = H`

ADR 02 requires `H` at least ten times the largest swept cap, and invariant 4 repeats it; ADR 01
sweeps `k_max` up to `H`, where an episode-long hold is the intended behaviour. The ten-segment rule
is for the fixed-`k` D0 sweep, so the D0 sample count is not degenerate. Restate: `H` at least ten
times the largest fixed `k` in the D0 sweep; the D2 cap sweep is exempt, and its sample count is
handled by II.3.

## II.9 (minor) ADR 02 wording

- "sharing an owner-set finite mean and finite variance": only the mean can be matched across
  deterministic (variance 0), exponential (variance equal to mean squared), and lognormal. Match the
  mean; report the variance.
- `time_homogeneous` has no defined effect in either round. With agent-pinned regions and stationary
  hazard it is inert for E2-E4; define it or drop it from this ADR.
- The deterministic law has the fixed `k = D` policy as its oracle; it is the natural D0 tuning
  target for E4 and worth one sentence.

## II.10 Decisions for the owner, round 2

1. Separate team cap `k_Z` (II.1): add it with default `k_max` and `k_Z = H` for E3/E4, or keep a
   single cap and accept that E3 runs only at `k_max = H`.
2. Register `m_dur` (II.7) as the E3/E4 acceptance scale next to `m`, or keep only `m`.
3. Ten-segment rule (II.8): apply to the fixed-`k` D0 sweep only, or to both sweeps.

After these, ADR 01 goes to Codex with II.2 to II.5 folded in as text; ADR 02 waits for the owner
mechanics page, which Part I F2.1 lists in order.

### II.10.1 Decisions taken with the owner, round 2 (confirmed one by one in session)

| # | Decision |
| --- | --- |
| 1 | Separate team cap `k_Z`, default `k_max` (D0 parity), `k_Z = H` for E3/E4; "every team decision forces all agents" and invariant 7 stay |
| 2 | ADR 02 registers both margins: `m` (latent-structure, host calibration) and `m_dur` (switching oracle minus best fixed-`k` oracle, the E3/E4 acceptance scale, at least three times the declared resolution term) |
| 3 | The ten-segment rule binds only the fixed-`k` D0 sweep; the D2 `k_max` sweep is exempt and reports `M` per rollout |

Status after round 2: ADR 01 may go to Codex once revision 3 folds in decision 1 and II.2 to II.5.
ADR 02 waits for the owner's mechanics page (Part I F2.1 order: state, action, latent, hazard,
reward, probe, cut), then a revision that adds `m_dur` and the II.8, II.9 wording.

---

# Part III — round-3 review of ADR 01 revision 3 (2026-09-02, later)

Object: revision 3 of ADR 01 (same path; revisions 1 and 2 at `ea20bccb0` and `7591f23a1`).
ADR 02 was not re-issued and stays on HOLD for the owner's mechanics page.

**Verdict: ACCEPT. ADR 01 goes to Codex.** Round-2 decision 1 (`k_Z`) and items II.2 to II.5 are
applied as text: the per-agent segment table `[T, E, N]` plus team table `[T, E]` with replay
metadata, `M` named as the binding resolution term at long holds, the ten-fold inference cost, the
`--n_uavs 6` entry-point pin, the in-training evaluation pin, the corrected observation citation,
and team age `a_Z / k_Z`. No invariant was weakened between revisions.

## III.0 Citation audit, round 3

| ADR claim | Verified location | Status |
| --- | --- | --- |
| `--n_uavs` default 5, `config.n_agents = env.n_uavs` | `main.py:58`, `main.py:410` | correct |
| Observation layout | `uav_env.py:138` (obs_dim), `_get_observation` `353-419` | correct |
| `lr_coordinator` at `config_1.py:148` | 148 is `lr_discoverer_critic`; `lr_coordinator` is 146; both `1e-4` | value right, line off by two |
| `gamma`, `ppo_epochs`, `num_envs`, `rollout_length` at 152, 158, 181-183 | 153, 156, 179-180 | values right, lines off by a few; Part I's audit carried the same offsets |
| `eval_episodes = 8` at 196 | 196 | correct |
| Sampler keeps the partial minibatch | `hmasd/utils.py:1026` onward | correct |

## III.1 Non-blocking notes for the implementer (no change to the decision)

1. **The switch event is outside the likelihood.** `S_t` is a deterministic function of the policy
   (gap at least `c`), so the PPO ratio covers only the skill chosen for sampled positions, never the
   decision to re-decide. The gradient of the rule with respect to the parameters is dropped, and
   the old and new policies would produce different `S_t` on the same state. This is the accepted
   approximation of an interruption rule without learned termination (plan §3, D2), and it is exactly
   where the suboptimality term of plan §7 enters. Name it in the risks in the next revision; nothing
   to implement.
2. **D0 boundary parity (invariant 2) rests on reset alignment.** `off` redraws at
   `env_steps % k == 0` on a per-env counter that restarts at reset; D0 redraws when every age reaches
   `k` after a reset. They coincide because `episode_length % k == 0` and all ages restart together.
   Test 2 should include at least one mid-rollout reset so that the alignment is exercised, not
   assumed.
3. **The per-step pass must not draw RNG.** The teacher-forced pass computes log-probabilities and
   values only; sampling happens for `S_t` positions alone. Test 1 (byte equality in `off`) will not
   catch an extra draw in `d2`; add a check that two `d2` runs at `c = ∞` with the same seed produce
   identical rollouts (determinism of the trigger path).
4. **Value normalisation.** `use_valuenorm = True` (`config_1.py:199`); the discounted targets in
   `d2` have a different scale from `off`, and the normaliser statistics are per head. The
   per-column denormalisation already exists (`agent.py:1931-1942`, `_denormalize_values` at `1294`); the team table needs its own.
5. **Where the tests live.** Top-level `tests/flexible_skill_duration_d2_test.py` is correct for a
   base-route change (`hmasd/`), per CLAUDE.md. Run with the explicit interpreter and
   `--basetemp C:/Projects/HMASD/temp/pytest_d2_policy_interrupt`.

## III.2 Predict-then-verify prompts carried into implementation

- P1 (switch rate by agent index under the causal-prefix test) and P2 (chattering floor at `c = 0`:
  about 5/6 of agents per step for an untrained six-skill coordinator) stand from Part I §5. Both
  are answerable from the first E0 rollout and should be recorded before it.
- P4 (new): at `c = ∞`, `k_max = k_Z = k = 10`, what is the ratio of `d2` to `off` high-level target
  scale? The undiscounted-to-discounted factor `τ(1−γ)/(1−γ^τ)` at `τ = 10`, `γ = 0.99` is about
  1.046; test 2's logged ratio should match it to three digits on a constant-reward episode.

## III.3 Hand-off

Codex implements ADR 01 revision 3 on the HMASD base route under plan §8 touch points, with tests
1 to 8 as specifications and III.1 items 2 and 3 added to tests 2 and 1. Claude reviews the diff
against the eight invariants; the owner runs E0 (exposure and probe set) before E1.

---

# Part IV — review of the corridor mechanics page and ADR 02 revision 3 (2026-09-02, later)

Objects: `../plans/RELAY_CORRIDOR_MECHANICS_20260902.md` (GPT Pro draft, owner to finalise) and
ADR 02 revision 3 (same path as before; revisions 1 and 2 at `ea20bccb0`, `7591f23a1`).

**Verdict: the mechanics are sound and the margins are real; HOLD for three owner decisions,
then the owner finalises the page and ADR 02 is accepted.** The host does what E3 and E4 need:
a visible change, a physical switching cost, a hazard that differs by region, and reference
values computable without training. What is missing is the seam to the learner: the page never
says how HMASD's `(Z, z_i, low-level action)` becomes the host's `(role, KEEP/RENEW)`, and at
`K = 2` the latent is public by construction, which makes one of the two registered margins a
measurement against a straw man.

## IV.0 Numeric and citation check

| Claim | Check | Status |
| --- | --- | --- |
| `C(20, 0.005) = 0.9539`, `C(20, 0.02) = 0.8310` | `toy_studies/untied_k_n/RESULTS.md:20` | correct |
| Margin table (three rows, `m` and `m_dur`) | recomputed from the page's closed forms with `H = 400`, `w_r = 1/2`, `k in {1,2,5,20,40}`: `0.2260 / 0.0570`, `0.3565 / 0.1444`, `0.5807 / 0.2712`; best `k` = 20, 5, 5 | matches to four digits; the "exact enumeration" values equal the closed form, as they should for independent regions |
| Geometric variance `mu(mu-1) = 380` at `mu = 20`; lognormal shape 1 variance `687` | `CV^2 = e - 1 = 1.718`, times `400` | correct |
| DP size `2 x 2 x 40 x 401 = 64,160` | arithmetic | correct |
| `J_sw`, `J_k`, `J_open,k = J_k / K` | derivation re-read: one lost step per event for the switching oracle; `C - 1/k` served fraction per fixed window; `+1/H` for the free initial lease; open-loop correct with probability `1/K` per window | consistent with the stated conventions (initial lease at reset, one-step outage per `RENEW`) |
| Base-route low-level actor action type | `config_1.py:30` `action_space_type = 'continuous'`; no categorical head in `R_Actor` (`hmasd/networks.py:1131-1305`) | continuous-only as far as read; the implementer must confirm |

## IV.1 (must fix before finalising) The HMASD adapter is one sentence and it is not enough

The page says "the ADR-01 adapter emits `RENEW` when a high-level segment opens". It does not say
what the skill `z_i` is on this host, what the low-level policy outputs each step, or what the team
code `Z` does. Three readings, one to be chosen (decision 1):

- (a) **High-level only.** `z_i` is the role, `n_z = K`; the low-level policy is the identity and
  is not trained; discriminators idle. Cleanest for E3/E4 but it is a different learner from the
  one E1/E2 run on scenario 1, so E2 to E3 comparisons change two things at once.
- (b) **Full stack, discrete low-level.** `n_z = K`; the low-level policy chooses the role each step
  from a categorical head conditioned on `z_i`. The base-route actor is continuous-only as read, so
  this adds a head to the learner.
- (c) **Full stack, continuous low-level, host argmax.** The low-level policy emits a `K`-vector as
  today; the host takes the argmax as the role. No learner change; the low-level must learn to
  place the argmax where `z_i` says, which the individual discriminator rewards (the held role is in
  the observation). `RENEW` is emitted for `i in S_t` by the adapter, exactly as the page says.

Recommendation: (c). It keeps ADR 01 untouched and makes the corridor a drop-in host for the same
learner. State in the page: `n_z = K`, low-level action dimension `K`, host role = argmax, and that
the reward is delivered to the learner as the shared mean `r_t` (per-agent components logged).

## IV.2 (must fix before finalising) At `K = 2` the latent is public and `m` is a straw-man margin

A switch draws a *different* `theta_r`. With `K = 2` the new value is `1 - theta_r`, so the
immediate change flag reveals it; the one-step-lag cue is redundant; greedy on public state renews
at the same step as the switching oracle with the same role, so `J_greedy = J_sw` exactly. The
latent-structure margin `m` is then measured against open-loop plans that ignore the flag, which is
not "how much knowing the latent is worth" but "how much reacting is worth". `m_dur` is unaffected:
it compares two latent-aware oracles and is the quantity E3 needs.

Options (decision 2):

- Keep `K = 2` for the first object and demote `m`: registered, reported, not an acceptance
  criterion for E2 to E4; say in the ADR that at `K = 2` greedy equals the switching oracle by
  construction, so the learner's ceiling is exactly `J_sw`.
- Move to `K = 3`: the flag no longer reveals the new latent; greedy loses two steps per event
  (flag, then cue), the oracle one; `m` becomes meaningful; open-loop census `3^4 x 6 = 486`,
  still trivial. Adds one learning problem (map cue to role) that E3 does not need.

Recommendation: `K = 2` with `m` demoted, and `K = 3` registered as the family point where `m` and
the cue matter (UCOPE's probe value `v` also needs `K >= 3` to be non-zero).

## IV.3 (should fix, not blocking E3/E4) Agents do not interact, so `Z` is inert and E5 cannot run here

The reward is a mean of independent per-agent indicators and regions are independent. The team
code `Z` has nothing to condition on, so its discriminator reward is noise and E5 (two-level
interruption, "no collapse of `Z` semantics on probes") has no signal on this host. This is fine
for E3/E4 and matches the single-agent inspiration model, but plan §5 places E5 on the corridor.
Add, off by default, one coupling term to be switched on for E5: for example a zone serves only if
both roles are present among its agents, or a region bonus when all its agents are fresh. Design it
when E5 is scheduled (decision 3), not now.

## IV.4 (should fix) Define the cue and replace open question 3

"One-step-lag cue `y_r`" is not defined; presumably `theta_r` at `t - 1`. Under IV.2 it is
redundant at `K = 2`. Define it, and replace open question 3 ("is the lagged cue sufficient
without probing?"), which the construction already answers (greedy matches the oracle up to one
step per event at `K = 2`, two at `K >= 3`), with the real open item: the finite `c` grid at which
D2 stops chattering on the change flag.

## IV.5 (should fix) State the initial-dwell convention for the deterministic law

"Deterministic `D` has fixed `k = D` as its restricted oracle" holds only if the first dwell after
reset is a full `D`, so that boundaries at `0, D, 2D, ...` coincide with events. Under a stationary
residual-life convention the phase would be random and `k = D` misaligned, giving `m_dur > 0` at
zero variance. Test 8 (`D = 20, k = 20` equality) depends on this; write the convention down.

## IV.6 (minor) The evaluation budget is loose in a safe direction

`sigma_Delta <= 1` is a bound; the per-episode mean over `400 x 6` indicators will have a standard
deviation closer to a few hundredths, so 4,096 matched episodes resolve far below `m_dur`. The
cost is `4,096 x 400 = 1.6e6` steps per policy per evaluation, about three minutes per policy at
the target speed. Acceptable as a proposal; invariant 5 should use the measured `sigma_Delta` from
the reference tapes, which test 5 already does.

## IV.7 (minor) Wording

- "Ragged" is vacuous at `rho = 0`; keep it as a family property, say so.
- Metrics already list reward components; make explicit that per-agent service indicators are
  logged so the asynchronous-credit question (Part I F1.10) can be examined later.
- The `m_dur` approximation line says `0.0580` from the `C`-table and `0.057037` exact; the
  difference is the `1/H` term and the rounding of the table, not a finite-`H` DP effect.

## IV.8 Decisions for the owner

1. Adapter (IV.1): (a) high-level only, (b) discrete low-level head, (c) continuous low-level with
   host argmax.
2. `K` (IV.2): `K = 2` with `m` demoted, or `K = 3`.
3. Coupling term for E5 (IV.3): design later when E5 is scheduled, or now.

After these, the owner finalises the mechanics page (adds the adapter paragraph, the cue
definition, the initial-dwell convention, and the `m` disposition) and ADR 02 revision 4 is a
wording pass; no further review round is needed before the host is implemented.

### IV.8.1 Decisions taken with the owner, round 4 (confirmed one by one in session)

| # | Decision |
| --- | --- |
| 1 | Adapter (c): full HMASD stack; `n_z = K`; the low-level policy emits a `K`-dimensional continuous action and the host takes the argmax as the role; `RENEW` is emitted by the adapter for `i in S_t`; the learner receives the shared mean reward, per-agent components logged. ADR 01 is untouched |
| 2 | `K = 2` for the first object; `m` is registered and reported but is not an acceptance criterion for E2 to E4; at `K = 2` greedy equals the switching oracle by construction and the learner's ceiling is `J_sw`; `K = 3` is registered as the family point where `m`, the cue, and the probe value `v` are meaningful |
| 3 | The agent-coupling term for E5 is designed when E5 is scheduled; the mechanics page reserves a default-off switch and state layout for it |

Finalisation: the owner adds to the mechanics page the adapter paragraph (decision 1), the cue
definition and the `m` disposition (decision 2, IV.4), the initial-dwell convention (IV.5), and the
reserved coupling switch (decision 3); ADR 02 revision 4 folds the same items in as wording. No
further review round is required before the host is implemented; Claude reviews the host diff
against ADR 02's nine invariants when it exists.

---

# Part V — acceptance of the finalised mechanics page and ADR 02 revision 4 (2026-09-02, later)

Objects: `../plans/RELAY_CORRIDOR_MECHANICS_20260902.md` as finalised at commit `5c4a32f77` and
ADR 02 revision 4 at `cd1d1b5be`. Both were written by GPT Pro through the GitHub connector and
pushed to `main` directly, authored under the owner's name; the provenance headers inside the
files record this. Checks were made against the round-4 versions at `33f009211`.

**Verdict: ACCEPT ADR 02 revision 4 and the mechanics page. The host can be implemented.**

## V.0 What was checked

| Check | Method | Result |
| --- | --- | --- |
| Display-math blocks unchanged | extracted every `$$` block from both files at `33f009211` and `HEAD`, compared with whitespace removed | identical (14 blocks in the mechanics page, 4 in the ADR) |
| Margin table, variances, DP size, evaluation budget unchanged | grep counts of `.057037`, `.356468`, `.144358`, `.580747`, `.271219`, `687.309`, `64,160`, `4,096`, `0.046875` before and after | same counts in both files |
| Decision 1 (adapter) present | mechanics "Action"; ADR "Decision", "Parameters" (`n_z=K`, `low_level_action_dim=K`, `role_decode=argmax`), invariant 7, test 7 | present; ADR 01 not touched |
| Decision 2 (`K = 2`, `m` demoted) present | mechanics "Structure cut", "Probe", "Reference policies and margins", "Proposed grids"; ADR "Decision", invariant 5, test 8 | present; `K = 3` registered as the family point |
| Decision 3 (coupling switch) present | mechanics "State", "Action", "Speed note"; ADR "Parameters" (`e5_coupling_enabled=false`), invariant 7 | present, rule deferred |
| IV.4 cue definition and open question 3 | mechanics "State" (`y_{r,t} = theta_{r,t-1}`, flag immediate); ADR "Open questions" | done; the question now asks for the finite `c` grid at which D2 stops chattering on the flag |
| IV.5 initial-dwell convention | mechanics "Hazard"; ADR "Decision", invariant 4, tests 4 and 8 | done: first dwell is a full `D`, events at `D, 2D, ...`, boundaries at `0, D, 2D, ...` |
| IV.7 wording | raggedness as a family property; per-agent indicators logged; `0.0580` vs `0.057037` attributed to `1/H` and table rounding | done |

## V.1 Errata (non-blocking)

- Both provenance headers say revision 3 is at `149bd7c4e`. It was stored at `33f009211`;
  `149bd7c4e` contains it unchanged, so the pointer resolves, but the storing commit is
  `33f009211`.
- ADR 02 test 1 now reads "distinct fixed-`N` family instances, asserting ragged records without
  padding" where revision 3 said "variable entity counts". This follows invariant 1 (raggedness is
  a family property) and is consistent; test 3 still exercises divisible and non-divisible `N`.
  The implementer should not read test 1 as requiring variable `N` inside one object.
- ADR status line still says `proposed`. This review is the acceptance record; the ADR text is
  stored as delivered and is not edited.

## V.2 Notes for the host implementer

1. The step order the mechanics page fixes: the event is realised in the transition into state
   `t`, the change flag is visible at `t`, the cue at `t` still shows the old latent, `RENEW` at
   `t` is one zero-service step, service resumes at `t + 1`. The `D = 20, k = 20` equality in
   test 8 and the `K = 2` greedy equality both depend on this order; write it into the step
   function's docstring and test it directly.
2. The learner side is ADR 01's implementation, whose phases 1 and 2 landed at `a85fe706c` and
   `368206861` while this part was written. The host needs only the adapter surface named in
   ADR 02's "Parameters"; it must not depend on ADR 01 phases that are still open.
3. The host file location is not fixed by ADR 02. `envs/` is the shared environment package and
   the natural home; the test is a top-level `tests/relay_corridor_host_test.py` per the ADR.
   Run `git check-ignore -v` on any new path before committing.
4. Reference returns and both margins are computed by enumeration inside the test (test 5), not
   copied from the table; the table is the expected value.

## V.3 Hand-off

Claude reviews the host diff against ADR 02's nine invariants and the nine tests when the
implementer delivers it, in the same form as the D2 acceptance checklist in
`../plans/D2_IMPLEMENTATION_PLAN_20260902.md` §11. No further architecture round is open on
either ADR.

---

# Part VI — review of the relay corridor host implementation (2026-09-02, later)

Object: branch `worktree-agent-aeda939d06a5b4fea`, five commits on top of `f8d2dd5b3`
(`22390b48c` host core, `9be152b39` references and margins, `b5a8ac1eb` adapter, `e996bd48f`
tests, `e26063d81` report), written by an Opus implementation session in an isolated worktree.
Files: `envs/relay_corridor/{__init__,config,rng,renewal,host,references,adapter}.py`,
`tests/relay_corridor_host_test.py`, `../plans/RELAY_CORRIDOR_HOST_REPORT_20260902.md`. No file
outside those was changed; the learner files being edited concurrently on `main` were not touched.

**Verdict: ACCEPT. The host meets ADR 02's nine invariants; the branch is integrated into
`main`.** One convention needs the owner's confirmation (VI.2 F1); nothing else is open.

## VI.0 Reviewer's own run

Preflight passed, then the nine tests were re-run by the reviewer in the worktree:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/relay_corridor_host_test.py --basetemp <worktree>/temp/pytest_relay_corridor_review
.........                                                                [100%]
9 passed in 13.47s
```

## VI.1 Invariants against code

| # | Invariant | Where it is met | Reviewer check |
| --- | --- | --- | --- |
| 1 | ragged, unpadded family boundary | `RelayCorridorHost.public_state_records`, `record_padding`; test 1 | records emitted at live cardinality for `N in {3,5,6,9}`; no padding path exists in the host |
| 2 | key-stable, order-independent streams | `rng.stream_generator` keyed `(master seed, episode, stream, id)`; `_build_tapes`; test 2 | one generator per key, fixed draw order (`theta0`, `H` event uniforms, `H` switch uniforms; one role uniform per agent) |
| 3 | every positive `N` valid | `config.__post_init__`, `_balanced_sizes`; test 3 | no `N mod K` rule; `K >= 2` is enforced, which the page implies ("draws a different theta") |
| 4 | pinning, laws share only `E[D]`, full initial dwell | `renewal.py` hazard tables with age `0` at reset; `DeterministicLaw.hazard_table` is `1` at age `D-1`; test 4 | events at `D, 2D, ...`; variances `0 / 380 / 687.309` reproduced by the CDF-bin masses |
| 5 | enumeration reproduces both margins; `m_dur` acceptance scale | `references.dp_service_profile`, `enumerate_references`; test 5 | DP equals the page's closed forms to `1e-12`; three table rows to the printed digits; `sigma_Delta` measured on 512 matched lanes (`0.0133 / 0.0064 / 0.0137`) |
| 6 | `H >= 10 max(D0_k_set)`; D2 exempt, `M` emitted | `validate_horizon`, `rows_per_rollout`; test 6 | only `d0_fixed_k` mode raises |
| 7 | argmax roles, renew mask, shared mean, per-agent indicators, disabled fields exact | `host.decode_roles`, `host.step` part 1, `adapter.step`; test 7 | reward `= Delta/N * sum(service)`; `probe_*` and `coupling` fields are zero arrays; `e5_coupling_enabled=True` raises |
| 8 | references, D0 cut, setup outage, `k = D` equality, cue timing, `K = 2` greedy equality | `host.step` parts 1 to 3; scripted policies in `references.py`; test 8 | step order asserted on tapes (flag at `t` = event realised into `t`; cue at `t` = `theta_{t-1}`; zero service on the RENEW step; service at `t+1`); greedy and switching oracle produce identical service indicators on 64 matched lanes at `K = 2`; `K = 3` strictly short |
| 9 | native-disabled NumPy against the `1e4` target | test 9 subprocess with `sys.modules` guards | `30,935` mechanics steps/s/core single lane; `485,648` env-steps/s/core at batch 64; disposition `meets_target` |

## VI.2 Findings (none blocking)

- **F1 (owner confirms). Cue at reset.** The page defines `y_{r,t} = theta_{r,t-1}`, undefined
  at `t = 0`. The host sets `y_{r,0} = theta_{r,0}`, so the learner sees the true initial latent
  through the cue. This is the reading under which "greedy equals the switching oracle by
  construction" is exact; the alternative (cue zero or random at reset) costs greedy
  `(1 - 1/K) Delta / H` per region, about `5e-4`, and makes the equality approximate. Recommend
  accepting and adding one sentence to the mechanics page's "State" section; the page is the
  owner's.
- **F2. Time in the observation.** `obs_layout` carries `t / H`, which the page's record list
  does not. It cannot be exploited on E3/E4 (a lease renewed before an event is invalidated by
  the event's epoch increment), and HMASD's UAV observation carries a time feature too. Record;
  drop it only if a later object wants a strictly homogeneous public state.
- **F3. Greedy at `K = 2` in the DP is assigned, not computed** (`per_region_greedy =
  per_region_switch`). The falsifiable check is the host-level one in test 8 (identical service
  indicators on matched tapes), which is the right place for it. At `K = 3` the DP computes greedy
  through the `pending-cue` coordinate and test 8 checks it against a closed form.
- **F4. Adapter is not yet wired into the base route.** `RelayCorridorAdapter.step(actions,
  renew_mask)` takes `S_t` as an input, by design (review V.2 note 2). Wiring is a separate
  commit after D2 Phase 8: the rollout loop passes the D2 sampled mask into the env step, and
  `obs_dim`, `state_dim`, `action_dim = K`, `n_z = K` flow into the learner config. The IV.0
  item "base-route actor is continuous-only" stays open until that commit.
- **F5. DP state count differs from the page's `64,160`.** The page's number was a size estimate
  for `(theta, freshness, fixed-phase, age)`; the implementation runs the phase as the step index
  and adds `plan-match` and `pending-cue`. Returns equal the closed forms, so the estimate is
  moot; the report records it (its item 4).
- **F6. Report items 1 to 12** are all readings the reviewer agrees with; items 1 (F1 here), 4
  (F5), and 12 (adapter shapes follow `ParallelToArrayAdapter`) are the ones a later reader
  should know.

## VI.3 Integration

The branch was rebased onto `origin/main` (which by then carried D2 Phases 3 to 7) and pushed to
`main` from the worktree; the two lines touch disjoint files, so the rebase was clean. Part VI
and the README entry were committed with it. The D2 implementer's next push rebases over these
commits as its operating notes prescribe.
