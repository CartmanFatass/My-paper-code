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
