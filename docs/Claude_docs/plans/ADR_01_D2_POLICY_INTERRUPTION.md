# ADR 01 — D2 policy-based interruption on the HMASD base route

Provenance: drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`, branch `main`)
on 2026-09-02 from the prompt in `ADR_REQUEST_PROMPT_GPT_PRO_20260902.md`, pasted into the Claude
Code session by the owner and stored here verbatim (only this header added). Status remains
`proposed`. Adversarial review: `../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`, which lists
the changes required before Codex implements anything. Line numbers below were read by GPT Pro
against a working tree with uncommitted changes; the review re-verified them.

---

## Title

ADR 01 — D2 policy-based interruption on the HMASD base route

## Status: proposed

## Context

Plan §11 fixes D2, two-level \(Z\), \(\delta=1\), HMASD-first, scenario 1 for E1/E2, and Codex; scenario 1 defaults to five UAVs with padded self/user/UAV/time observations and a shared coverage, SINR-quality, and height-penalty reward. The ledger identifies fixed-\(k\) synchronization and four asynchronous-coordinator changes (ledger §§0, 1 K-1–K-7, 9.4). The base path redraws at `env_steps % k == 0`; one coordinator call autoregressively samples \(Z,z_1,\ldots,z_N\) (`hmasd/agent.py:1897–1929`; `SkillCoordinator.assign_and_value_batch`). HA-CTSE has horizon controls and forced masks (`config_1.py:239–259`; current `hmasd/agent.py:2067–2095`, drifted from 2010–2031); the discriminator references drifted to `_compute_intrinsic_rewards_batch` around 3340–3465 and omit age; elapsed storage, reward sum, values, and bootstrap are at `agent.py:2797,3024–3027`, `networks.py:725–729`, and `utils.py:731–748`. This is B-EXPLORE; no invariance proof or C contract gates launch (spec §11).

## Decision

At each check, compute \(g_Z=\max_Z\log\pi(Z\mid s_t)-\log\pi(Z^{held}\mid s_t)\); sample \(Z\) only at the forced boundary or when \(g_Z>c_Z\). For agent \(i\), force other held skills as tokens and compute \(\ell_i(z)=\log\pi(z_i=z\mid s_t,o_t,Z,z_{-i}^{held})\); \(S_t\) contains forced renewals and agents with \(\max_z\ell_i(z)-\ell_i(z_i^{held})>c\). At \(c=0\), \(S_t\) is all live agents. Decode kept agents first as forced tokens, then \(S_t\) in ascending index. Store \(\log p_t^h=\sum_{i\in S_t}\log\pi(z'_i\mid\cdot)\); forced agents contribute no gradient, and a separate \(Z\) term exists only when sampled (ledger §9.4).

Agent \(i\)'s segment has length \(\tau_i\), reward \(R_i=\sum_{u<\tau_i}\gamma^u r_{t_i+u}\), and target \(R_i+\mathbf1_{\neg terminal}\gamma^{\tau_i}V_i(t_i+\tau_i)\). Storage is ragged per agent; `VariableRosterEventCore._close_trace` is reference only. Discriminators receive \(a_i/k\) individually and \(a_Z/k\) globally. With `policy_interruption_mode=off`, execute untouched fixed-\(k\) modules, RNG calls, reward sum, and storage.

## Parameters

`policy_interruption_mode: enum`, default `off`, sweep `{off,d2}`; `delta: int`, default 1, range `{1}`; `c,c_Z: float≥0`, default \(+\infty\), conceptual range \([0,+\infty]\), finite grid unfixed; `k: int`, default 10, sweep unfixed; `gamma: float`, default 0.99, fixed; `age_feature: enum`, default `off`, D2 value `elapsed_over_k`; `canonical_order: enum`, default/range `ascending_agent_index`.

## Invariants

1. `off` is rollout-identical to current HMASD on the same seed.
2. \(c\to\infty\) permits no renewal before a forced \(k\)-boundary.
3. \(c=0,\delta=1\) re-selects every live agent every step.
4. Each agent's closed segment lengths sum to episode length.
5. Individual high-level log-probability sums over \(S_t\) only.
6. Stored targets use discounted segment rewards and \(\gamma^{\tau_i}\) bootstrap.

## Tests-as-specs

Use `tests/flexible_skill_duration_d2_test.py` with `temp/pytest_d2_policy_interrupt`, following `CLAUDE.md`'s top-level `*_test.py` and isolated-basetemp rules. Tests 1–6: seeded scenario-1 twin rollout, assert byte equality; \(c=\infty\), renewals only at boundaries; \(c=0\), \(S_t\) is all live agents; scripted interruptions, each length sum is \(H\); known forced/sampled tokens, stored log-probability is the sampled-term sum; hand-calculated ragged rewards, target matches the formula.

## Metrics to log

\(g_i,g_Z,|S_t|\), switch and \(Z\)-fire counts, segment-length and age distributions, sampled/forced counts, target variance, discriminator accuracy, label agreement, and run counts.

## Resolution arithmetic

Adam uses \(10^{-4}\); configuration gives 32 environments × 500 steps × 200 rollout updates, 15 PPO epochs, and eight evaluation episodes (`config_1.py:145–207`; `HMASDAgent.__init__`; `update_coordinator`). **Inference:** coarse exposure is \(10^{-4}\times200=0.02\): twice the explicit 0.01 value-head gain and 0.02 of the 1.0 embedding gain; Adam-step count depends on collected batches. Return resolution is \(\sigma/\sqrt8\), or paired \(\sigma_\Delta/\sqrt8\). Exact parameter count is not recorded; the spec §11.4 exposure line must supply it.

## Consequences and risks

No head is added, but conditional forwards, order dependence, moving triggers, ragged credit, and enabled-mode checkpoint incompatibility remain. Costs suppress chattering; `off` contains regression risk.

## Out of scope

Learned termination, \(Q\) head, \((z,k)\) menu, variable agent count, prediction/hazard add-ons, scenario-7 transfer, native ports, and C contracts.

## Open questions

What finite \(c,c_Z\) grid represents the endpoints? Does age conditioning raise or lower label agreement?

---

## Could not verify (GPT Pro's list, covering both ADRs)

* An exact parameter count for the scenario-1 coordinator, or for the not-yet-implemented D2 age-conditioned discriminators, is not present in the inspected configuration or model definitions.
* There is no single configured coordinator initialization scale: embeddings and value heads have explicit gains 1.0 and 0.01, while `SkillDecoder` retains framework-default initialization.
* The repository does not yet fix the finite \(c,c_Z\) grid, numeric corridor grids or margins, heavy-tail family parameters, numeric reference returns, or an achieved corridor throughput; \(10^4\) steps/second/core is a design target, not a measured result.
