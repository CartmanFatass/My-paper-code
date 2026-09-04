# ADR 01 — D2 policy-based interruption on the HMASD base route

Provenance: revision 3, drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`,
branch `main`) on 2026-09-02 after the round-2 review, pasted into the Claude Code session by the
owner and stored verbatim (only this header added). Revision 1 is at commit `ea20bccb0`, revision 2
at `7591f23a1`. Status: `proposed`, **accepted for implementation** by the round-3 review (Part III
of `../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`), with the non-blocking notes there.
Codex implements; the owner and Claude do not.

Line-number errata from the review (values are correct): `lr_coordinator` is `config_1.py:146`
(148 is the discoverer critic, same value); `gamma` 153; `ppo_epochs` 156; `num_envs` and
`rollout_length` 179-180.

---

## Title

ADR 01 — D2 policy-based interruption on the HMASD base route

## Status: proposed

## Context

Plan §11 fixes D2, two-level \(Z\), \(\delta=1\), HMASD-first, scenario 1 for E1/E2, and Codex. Run `main.py --scenario 1 --n_uavs 6`: the CLI defaults to five UAVs and later sets `config.n_agents = env.n_uavs` (`main.py:48-59,410`). This pins \(N=6\), with padded self/user/UAV/time observations (`envs/pettingzoo/uav_env.py:138,353-419`) and the scenario-1 coverage/SINR-quality/height-penalty reward (`envs/pettingzoo/scenario1.py:78-112`). The current route redraws at `env_steps % k == 0`; `SkillCoordinator.assign_and_value_batch` samples \(Z,z_1,\ldots,z_N\) causally (`hmasd/agent.py:1897-1929`; `hmasd/networks.py:787-850`). This is B-EXPLORE.

## Decision

Each step, one canonical teacher-forced pass computes

$$
\ell_i(z)=\log\pi(z_i=z\mid s_t,o_t,Z^{held},z^{held}_{<i}),\qquad
g_i=\max_z\ell_i(z)-\ell_i(z_i^{held}).
$$

Put \(i\) in \(S_t\) when \(g_i\ge c\), its age reaches \(k_{\max}\), or its skill is invalid. Test \(Z\) analogously on global state, with \(c_Z\) and a separate cap \(k_Z\): default \(k_{\max}\), but \(k_Z=H\) for E3/E4. Every team decision, reset, or invalid \(Z\) forces all live agents into \(S_t\); \(k_Z<H\) periodically re-synchronizes them.

Sample in \(O_t=(\text{kept canonically},S_t\text{ canonically})\). The base coordinator accepts \(O_t\), forced tokens, and the sampled mask, returning zero policy terms for forced positions. In `d2`, the high-level buffer stores a per-agent `(valid, reward, elapsed, terminal, value)` segment table of shape `[T,E,N]`, a team table `[T,E]`, and order/forced/sampled metadata for exact PPO replay. Log-probability and entropy sum only over sampled positions; \(Z\) terms exist only at team decisions. The present buffer instead stores most segment fields only on `[T,E]`, and its GAE walks one sequence per environment (`hmasd/utils.py:243-255,721-748`).

For \(x\in\{i,Z\}\),

$$
G_x=\sum_{u<\tau_x}\gamma^u r_{t_x+u}
+\mathbf1_{\neg terminal}\gamma^{\tau_x}V_x(s').
$$

Discriminator ages are \(a_i/k_{\max}\) and \(a_Z/k_Z\). `off` preserves the current global-\(k\), no-age, undiscounted-buffer path and RNG. Fair D0 is `d2`, \(c=c_Z=\infty\), \(k_{\max}=k_Z=k\): boundaries match `off`; targets differ.

## Parameters

`mode:{off,d2}=off`; `delta=1`; `c,c_Z≥0=∞`; `k_max:int=10`, sweep `[1,H]` including `H`; `k_Z:int=k_max`, E3/E4 `H`; `k=10`; `gamma=0.99`; `age_feature:{off,normalized}=off`; `N=6`. The fixed HMASD values \(k=10\), \(\gamma=0.99\), and \(N=6\) are in `config_1.py:25,134,152`.

## Invariants

1. `off` is byte-identical to current HMASD on the same seed.
2. D0 and `off` have identical team/agent boundary masks.
3. Infinite costs permit no policy switch before the relevant cap.
4. At \(c=0,\delta=1\), every live agent is sampled every step.
5. Closed or bootstrapped lengths partition each agent's live steps.
6. Replay log-probability and entropy include sampled positions only.
7. Every team boundary is a boundary for every live agent.
8. Buffer shapes, targets, and normalized ages equal this ADR.

## Tests-as-specs

Use `tests/flexible_skill_duration_d2_test.py`, with scratch directory `temp/pytest_d2_policy_interrupt`. Tests 1–8 assert byte equality; D0 boundary equality and target-scale logging; no pre-cap switch; all-one sampled masks; live-step partition; non-contiguous-\(S_t\) replay with forced zeros; team closure; and `[T,E,N]`/`[T,E]` shapes with hand-computed targets and ages. The top-level `*_test.py` name and isolated `--basetemp` follow `CLAUDE.md`.

## Metrics to log

Gaps, \(|S_t|\), switch rate by agent index, boundary causes, decode order, sampled/forced counts, segment/age distributions, row count \(M\), target variance versus D0, discriminator accuracy, optimizer steps, parameter displacement, and coordinator-inference time.

## Resolution arithmetic

Adam uses \(10^{-4}\); embedding/value-head gains are 1.0/0.01 (`config_1.py:148`; `hmasd/networks.py:733-738`). Batch 128 is the `getattr` default at `hmasd/agent.py:4747`; `config_1.py:158,181-183,196` fixes 15 epochs, 32 environments, 500 steps, 200 rollouts, and **eight-episode in-training evaluation**. **Inference:** D0 has \(M=32\cdot500/10=1600\) rows per rollout, giving \(200\cdot15\cdot\lceil1600/128\rceil=39{,}000\) Adam steps and naive \(lr\times steps=3.9\); the sampler retains its partial final minibatch (`hmasd/utils.py:get_coordinator_sampler`). D2 uses \(200\cdot15\cdot\lceil M/128\rceil\). At \(k_{\max}=H=500\), infinite costs give \(M=32\), one minibatch per epoch, and 3,000 steps; \(M\) is therefore the binding resolution term at long holds. Return resolution is \(\sigma/\sqrt8\), paired \(\sigma_\Delta/\sqrt8\). **Inference:** \(\delta=1\) checks every step, causing 10× `off` coordinator inference at \(k=10\). Exact parameter counts and realized displacement remain machine-reported exposure-line quantities under evidence-spec §11.4.

## Consequences and risks

Risks are causal-prefix index bias, chattering, large-\(k_{\max}\) sample collapse, 10× inference, optimizer saturation, replay/buffer defects, checkpoint incompatibility, and asynchronous shared-reward credit.

## Out of scope

Learned termination, Q heads, \((z,k)\) menus, variable \(N\), add-ons, native ports, UAV transfer, and C contracts.

## Open questions

What finite \(c,c_Z\) grid is used? Which intermediate \(k_{\max}\) values accompany \(H\)? Does age conditioning raise or lower frozen-probe label agreement?

## Could not verify

* The finite \(c\), \(c_Z\), and intermediate \(k_{\max}\) sweep values are not fixed.
* Exact coordinator/discriminator parameter counts and realized parameter displacement are not recorded; the B-launch exposure line must measure them.
