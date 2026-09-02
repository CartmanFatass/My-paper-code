# ADR 02 — Relay corridor host family for duration-plan E2–E4

Provenance: revision 2, drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`,
branch `main`) on 2026-09-02 after the round-1 review, pasted into the Claude Code session by the
owner and stored verbatim (only this header added). Revision 1 is in Git history at commit
`ea20bccb0`. Status remains `proposed`; implementation is blocked until the owner supplies the
corridor mechanics. Round-2 review: Part II of `../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`.
GPT Pro's shared "could not verify" list is kept at the end of `ADR_01_D2_POLICY_INTERRUPTION.md`.

---

## Title

ADR 02 — Relay corridor host family for duration-plan E2–E4

## Status: proposed

## Context

The plan keeps E1/E2 on UAV scenario 1 and assigns E3/E4 to the relay corridor. Advice §§3–4 require ragged entities, matched randomness, three references, declared resolution, ten largest-\(k\) segments, and vectorized-NumPy speed. Review §4.1 fixes agent-pinned \(\lambda\) regions, deterministic/exponential/lognormal renewal laws matched on \(E[D]\), and owner authorship of the mechanics. Evidence-spec §11 makes this B-EXPLORE and fixes \(N\) within each duration object.

## Decision

This ADR fixes only the surrounding contract. Before implementation, the owner supplies the entity/state schema, action, latent, hazard, reward, probe, and structure cut; these must yield task reward in \([0,1]\) before costs and computable reference returns. No corridor dynamics are selected here.

The host emits ragged entity sets; packing is learner-owned. Entities use streams keyed by `(master seed, episode, entity id)` and each regional event process uses `(master seed, episode, region id)`. Agents are pinned to one region per episode: E3 has \(\lambda_1\ne\lambda_2\), while the homogeneous point has equality. E4 uses deterministic, exponential, and lognormal \(D\), sharing an owner-set finite mean and finite variance.

References are oracle with the latent; greedy on public state, with no asserted ordering; and duration-structure-blind D0, the same learner with \(c_{\text{switch}}=c_Z=\infty\). Define

$$
m=J^*_{\text{oracle plan}}-J^*_{\text{best open-loop/fixed plan}},
$$

closed-form or exhaustively, not from trained D0. At each of three registered margins, \(J_O^*=J_F^*+m\); greedy and trained-D0 returns are merely reported.

Note: FRRIE is \(K=3,\lambda=\rho=0,N\) swept; VNFC is \(Z=2,\rho>0,N\) swept; SCDMP sweeps \(k,\lambda>0\); UCOPE has \(c_{\text{probe}}>0,v,k\); CBSC maps nuisance coordinates to \(Z\).

## Parameters

`N:int`, default unset, positive owner grid but fixed per object; `K:int`, default unset, positive owner grid; `Z:int`, default unset, positive owner grid; `H:int`, default unset, \(H\ge10k_{\max}^{sweep}\); `k:int`, default `10`, owner grid; `lambda: probability`, default unset, range `[0,1]`; `rho: probability`, default `0`, family range `[0,1]` but fixed `0` here; `c_probe,v: float≥0`, defaults unset, owner grids; `m: float>0`, default unset, three owner values; `time_homogeneous: bool`, default `true`, sweep `{true,false}`; `lambda_regions: pair`, default equal, sweep equal/unequal; `renewal_law: enum`, default `deterministic`, sweep `{deterministic,exponential,lognormal}`; `renewal_mean: positive float`, default unset, common across laws.

## Invariants

1. Host observations are ragged and unpadded.
2. Entity and regional-event streams are key-stable and independent.
3. Every positive \(N\) is admissible; no \(N\bmod K\) rule exists.
4. \(H\) contains at least ten segments at the largest registered \(k\)/cap.
5. For each \(m\), exhaustive arithmetic gives \(J_O^*-J_F^*=m\); greedy has no required order.
6. Agents retain their region, and all E4 laws share \(E[D]\).
7. Native-disabled vectorized NumPy targets \(10^4\) steps/s/core on a recorded CPU.

## Tests-as-specs

Use `tests/relay_corridor_host_test.py` and `--basetemp C:/Projects/HMASD/temp/pytest_relay_corridor`. Tests 1–7 assert: no sentinel padding; unchanged entity/event tapes under batch and enumeration-order changes; divisible and non-divisible \(N\) both run; rejection below ten segments; exact three-margin identities with unconstrained greedy output; fixed regions and matched law means; recorded-machine throughput with native loading disabled. The top-level path follows `CLAUDE.md`; it presumes the host is placed under `envs/`.

## Metrics to log

Reference returns and \(m\); hazards by region; realized \(D\); probes/costs; delays, switches and segment lengths; CRN audit; live counts; throughput/machine identity; transitions, high-level samples, optimizer updates and evaluations.

## Resolution arithmetic

With \(M\) valid high-level rows per rollout, batch 128 (`hmasd/agent.py:4747`), 15 epochs and 200 rollouts, **inference:** Adam steps are \(200\cdot15\cdot\lceil M/128\rceil\), and naive displacement budget is \(10^{-4}\) times that count. At D0, \(M=32\cdot500/10=1600\), giving 39,000 and 3.9; actual corridor-D2 \(M\), parameter counts and norm displacement are exposure-line measurements rather than host assumptions. Eight paired episodes resolve \(\sigma_\Delta/\sqrt8\); each \(m\) must be at least three times the largest declared resolution term.

## Consequences and risks

Implementation is blocked until the owner supplies mechanics. Risks are structure leakage, non-enumerable margin, RNG coupling, and machine-dependent speed.

## Out of scope

Inventing mechanics, within-object variable \(N\), learned termination, \((z,k)\) menus, native kernels, UAV transfer, and C contracts.

## Open questions

What owner-supplied mechanics definition applies? What numeric parameter, margin and lognormal-shape grids apply? What CPU profile owns the speed target?
