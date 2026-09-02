# ADR 01 — D2 policy-based interruption on the HMASD base route

Provenance: revision 2, drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`,
branch `main`) on 2026-09-02 after the round-1 review, pasted into the Claude Code session by the
owner and stored verbatim (only this header added). Revision 1 is in Git history at commit
`ea20bccb0`. Status remains `proposed`. Round-2 review: Part II of
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`.

---

## Title

ADR 01 — D2 policy-based interruption on the HMASD base route

## Status: proposed

## Context

Plan §11 fixes D2, two-level \(Z\), \(\delta=1\), HMASD-first, scenario 1 for E1/E2, and Codex; this ADR pins `Config` \(N=6\) and `n_uavs=6`, whose padded local observation is self/user/UAV/time and whose reward combines coverage, SINR quality, and height penalty (`config_1.py:25`; `envs/pettingzoo/uav_env.py:122-126`; `envs/pettingzoo/scenario1.py:78-112`). Ledger §§0, 1 and 9.4 identify the lost common clock, age-confounded reward, variable-segment SMDP credit, and partial autoregressive assignment. The base route redraws all skills on `env_steps % k == 0`; `SkillCoordinator.assign_and_value_batch` samples \(Z,z_1,\ldots,z_N\) causally (`hmasd/agent.py:1897-1929`; `hmasd/networks.py:787-850`). Forced masks exist only in `HorizonSkillEditor.assign_and_value_batch`, while the base rollout lacks dynamic-order metadata (`hmasd/ha_ctse.py:633-660`; `hmasd/utils.py:get_coordinator_sampler`). This is B-EXPLORE under evidence-spec §11.

## Decision

Every step, teacher-force the held assignment in canonical order. For agent \(i\),

$$
\ell_i(z)=\log\pi(z_i=z\mid s_t,o_t,Z^{held},z^{held}_{<i}),\qquad
g_i=\max_z\ell_i(z)-\ell_i(z_i^{held}).
$$

Put \(i\) in \(S_t\) when \(g_i\ge c\), its age reaches \(k_{\max}\), or its skill is invalid. Apply the analogous global-state gap \(g_Z\ge c_Z\) to \(Z\); a team decision, team cap, reset, or invalidity makes \(S_t\) all live agents. **Inference required to preserve D0 boundary parity and permit long holds:** the team clock uses the same \(k_{\max}\) cap as the independent agent clocks. Therefore \(c=0,\delta=1\) re-selects every agent each step, and \(k_{\max}=H\) permits episode-long holds.

Sample in \(O_t=(\text{kept agents canonically},S_t\text{ canonically})\). The base coordinator must accept \(O_t\), forced tokens, and a sampled mask, returning zero policy terms for forced positions. Store those three objects; PPO teacher-forces the same order. Individual log-probability and entropy sum only over \(S_t\); \(Z\) terms exist only at team decisions.

For \(x\in\{i,Z\}\),

$$
G_x=\sum_{u<\tau_x}\gamma^u r_{t_x+u}
+\mathbf1_{\neg terminal}\gamma^{\tau_x}V_x(s').
$$

Discriminators receive \(a_i/k_{\max}\) or \(a_Z/k_{\max}\). In `d2`, validation replaces `episode_length % k == 0` with the cap constraint; `off` retains the current assertion and untouched global-\(k\), no-age, undiscounted, current-storage path with no extra RNG. The fair D0 is `d2`, \(c=c_Z=\infty\), \(k_{\max}=k\): its boundaries match `off`; its discounted targets do not.

## Parameters

`mode: enum`, default `off`, sweep `{off,d2}`; `delta: int`, default `1`, sweep `{1}`; `c,c_Z: float≥0`, default `∞`, fixed sweep in `[0,∞]`; `k_max: int`, default `10`, sweep in `[1,H]` including `H`; `k: int`, default `10`, fixed for compatibility/D0; `gamma: float`, default/fixed `0.99`; `age_feature: enum`, default `off`, sweep `{off,age_over_k_max}`; `N: int`, default/fixed `6` for E1/E2.

## Invariants

1. `off` is byte-identical to current HMASD on the same seed.
2. D0 and `off` have identical team/agent boundary masks.
3. Infinite costs allow no policy switch before the relevant cap.
4. At \(c=0,\delta=1\), every live agent is sampled every step.
5. Closed or bootstrapped segment lengths sum to each agent's live steps.
6. Replay log-probability and entropy contain sampled positions only.
7. Every team boundary is a boundary for every live agent.
8. Targets and discriminator ages equal the formulas above.

## Tests-as-specs

Use `tests/flexible_skill_duration_d2_test.py` with `--basetemp C:/Projects/HMASD/temp/pytest_d2_policy_interrupt`. Tests 1–8 assert: seeded `(Z,z,log-prob,reward)` plus checkpoint equality; boundary equality and logged target-scale ratio; no pre-cap switch; all-one sampled masks; exact live-step partition; non-contiguous \(S_t\) replay with stored order and forced zeros; team closure of all segments; hand-computed targets and normalized ages. The top-level `*_test.py` and isolated scratch path follow `CLAUDE.md`.

## Metrics to log

Gaps, \(|S_t|\), switch rate by agent index, boundary causes, sampled/forced counts and order, segment/age distributions, target variance and scale versus D0, discriminator accuracy, label agreement, high-level samples, optimizer steps, and parameter displacement.

## Resolution arithmetic

Adam uses \(10^{-4}\); embedding/value-head gains are 1.0/0.01 (`hmasd/agent.py:HMASDAgent.__init__`; `hmasd/networks.py:733-738`). The pinned `Config` has coordinator batch 128 (`hmasd/agent.py:4747`), 15 PPO epochs, 32 environments, 500 steps, \(k=10\), 200 rollouts, and eight evaluation episodes. **Inference:** D0 has \(M=32\times500/10=1600\) high-level rows per rollout; `RolloutBuffer.get_coordinator_sampler` keeps the partial batch, so steps \(=200\cdot15\cdot\lceil1600/128\rceil=39{,}000\), and naive \(lr\times steps=3.9\). Finite-cost D2 uses \(200\cdot15\cdot\lceil M/128\rceil\) with measured \(M\); the exposure line logs \(\|\theta-\theta_0\|/\|\theta_0\|\). Return resolution is \(\sigma/\sqrt8\), paired \(\sigma_\Delta/\sqrt8\). D2 adds no coordinator parameters; exact coordinator and age-expanded discriminator counts are machine-reported.

## Consequences and risks

Risks are causal-prefix index bias, chattering, optimizer saturation, dynamic-order replay defects, enabled-mode checkpoint incompatibility, and shared-reward credit changing while teammates switch.

## Out of scope

Learned termination, Q heads, \((z,k)\) menus, variable \(N\), add-ons, native ports, UAV transfer, and C contracts.

## Open questions

What finite \(c,c_Z\) grid is used? Which intermediate \(k_{\max}\) values accompany \(H\)? Does age conditioning raise or lower frozen-probe label agreement?

---

## Could not verify (GPT Pro's revision-2 list, covering both ADRs)

* The owner-supplied corridor state, action, latent, hazard, reward, probe, and structure-cut mechanics are not present in the reviewed repository material; ADR 02 is therefore not implementation-ready.
* The finite \(c,c_Z,k_{\max}\) sweeps, three numeric corridor margins, common renewal mean, and lognormal shape are not fixed.
* Exact coordinator/discriminator parameter counts, realized parameter displacement, and achieved vectorized-NumPy throughput are not recorded; the B-launch exposure line and pinned benchmark must measure them.
