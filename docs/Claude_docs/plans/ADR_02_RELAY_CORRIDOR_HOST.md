# ADR 02 — Relay corridor host family for duration-plan E2–E4

Provenance: revision 3, drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`,
branch `main`) on 2026-09-02 from `ADR_02_CONVERGENCE_PROMPT_GPT_PRO_20260902.md`, pasted into
the Claude Code session by the owner and stored verbatim (only this header added). Revision 1 is
at commit `ea20bccb0`, revision 2 at `7591f23a1`. Normative companion:
`RELAY_CORRIDOR_MECHANICS_20260902.md`. Status: `proposed`; Part IV of
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` lists the changes required before the owner
finalises it.

---

## Title

ADR 02 — Relay corridor host family for duration-plan E2–E4, revision 3

## Status: proposed

## Context

The duration plan §§5–6 and 11 assign E3/E4 to the relay corridor under B-EXPLORE. Environment advice §§3–4 requires three references, resolvable margins, ragged CRNs, ten fixed-\(k\) segments, and vectorized-NumPy speed. Review Part I F2.1–F2.9, §4.1, and Part II II.6–II.10.1 fix agent-pinned regions, mean-matched renewal laws, D0 as \(c=c_Z=\infty\), both \(m\) and \(m_{\mathrm{dur}}\), and the ten-segment rule only for fixed-\(k\) D0. ADR 01 revision 3 supplies \(k_{\max}\), \(k_Z=H\) for E3/E4, per-agent segments, and \(M\)-row exposure accounting. `RELAY_CORRIDOR_MECHANICS_20260902.md` is the normative mechanics companion.

## Decision

The host has two regions, \(Z\) zones, and \(N\) fixed-roster agents pinned to region and zone. Region \(r\) has \(\theta_r\in\{0,\ldots,K-1\}\); zone \(q\) requires role \((q+\theta_r)\bmod K\). An event changes \(\theta_r\) and invalidates regional leases. Agent action is role plus `KEEP/RENEW`; `RENEW` opens the ADR-01 segment, stamps the epoch, and causes one zero-service step. Reward is \(\Delta\) times the fraction keeping a fresh, correct lease, so it lies in \([0,1]\).

E3 uses Bernoulli hazards \(\lambda_1,\lambda_2\). E4 uses positive-integer deterministic, geometric—discrete exponential—or rounded-lognormal \(D\), matched only on \(E[D]\), with \(\operatorname{Var}(D)\) reported. Deterministic \(D\) has fixed \(k=D\) as its restricted oracle. Public state has a lagged latent cue and immediate change/freshness flags; oracle latent is excluded. E2–E4 have \(c_{\text{probe}}=0\) and no probe action, while reserved fields preserve the state layout.

References are the switching oracle, each fixed-\(k\) oracle, the best open-loop zone-role map/fixed period, and greedy. Exact DP/enumeration registers

$$
m=J^*_{\mathrm{switch}}-J^*_{\mathrm{open}},\qquad
m_{\mathrm{dur}}=J^*_{\mathrm{switch}}-\max_kJ^*_k.
$$

D0 is the same learner with \(c=c_Z=\infty\) and cannot renew between fixed boundaries.

Family coordinates from advice §4 remain: FRRIE uses \(K=3,\lambda=\rho=0\) with \(N\) swept; VNFC uses two contexts and \(\rho>0\); SCDMP sweeps \(k\) at \(\lambda>0\); UCOPE enables \(c_{\text{probe}},v,k\); CBSC uses nuisance contexts.

## Parameters

`N,K,Z,H: positive int`, fixed within an object; `rho=0`; `Delta: float in (0,1]`; `lambda_regions: pair in [0,1]^2`; `D0_k_set: positive-int set`; `renewal_law ∈ {deterministic, geometric, lognormal}`; `renewal_mean, lognormal_shape > 0`; `c_probe=0`, `v` inactive. D2's `c,c_Z,k_max,k_Z` follow ADR 01, with `k_Z=H` for E3/E4. `time_homogeneous` is removed: renewal age is explicit state and service mechanics are time-homogeneous. The registered proposal is the companion mechanics-page grid.

## Invariants

1. Host-boundary entities are ragged and unpadded.
2. Entity and regional-event RNG streams are key-stable and order-independent.
3. Every positive \(N\) is valid; no \(N\bmod K\) rule exists.
4. Agents remain pinned; hazards and dwell laws follow registration and share only \(E[D]\).
5. Enumeration reproduces every stated \(m\) and \(m_{\mathrm{dur}}\), with \(m_{\mathrm{dur}}\ge3\sigma_\Delta/\sqrt{E_{\mathrm{eval}}}\).
6. \(H\ge10\max(\text{D0\_k\_set})\); D2 \(k_{\max}\) is exempt and reports \(M\) rows per rollout.
7. Pre-cost reward is in \([0,1]\), and probe-off behavior is exact.
8. References, D0 cut, setup outage, and deterministic \(k=D\) equality match the mechanics page.
9. Native-disabled NumPy is checked against the recorded \(10^4\)-steps/s/core target.

## Tests-as-specs

Run:

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/relay_corridor_host_test.py --basetemp C:/Projects/HMASD/temp/pytest_relay_corridor`

Tests 1–9 use, respectively: variable entity counts, asserting no padding; permuted batch/enumeration order, asserting identical keyed tapes; divisible and non-divisible \(N\), asserting both execute; scripted Bernoulli and three-law dwell tapes, asserting pinning, means, and reported variances; the three proposal points plus measured \(\sigma_\Delta\), asserting both margins and the resolution inequality; too-short \(H\) and large-\(k_{\max}\) D2, asserting only fixed-\(k\) D0 is rejected and \(M\) is emitted; reward/probe boundary cases, asserting range and disabled fields; exhaustive reference traces including \(D=20,k=20\), asserting oracle equality and D0 cut; and a pinned-CPU native-disabled benchmark, recording target disposition. The interpreter, top-level `*_test.py` naming, and isolated scratch convention follow root `CLAUDE.md` §§Environment and Commands/Tests.

## Metrics to log

\(m\), \(m_{\mathrm{dur}}\), all reference returns, regional hazards, \(D\) and \(\operatorname{Var}(D)\), renewals, stale-service loss, segment lengths, \(M\), CRN audit, reward components, greedy gap, transition/update/evaluation counts, throughput, and machine identity.

## Resolution arithmetic

**Proposal:** \(4{,}096\) matched evaluation episodes, so resolution is

$$
\frac{\sigma_\Delta}{\sqrt{4096}}=\frac{\sigma_\Delta}{64}.
$$

Per-episode mean-return differences lie in \([-1,1]\), hence \(\sigma_\Delta\le1\); the smallest proposed \(m_{\mathrm{dur}}=0.057037\) exceeds \(3/64=0.046875\). The corridor learner's \(M\), parameter count, optimizer-step count, and norm displacement are machine-generated exposure-line measurements; ADR-01 optimizer totals are not copied. This follows ADR 01 revision 3's identification of \(M\) as the binding long-hold term and evidence-spec §11.4's machine-generated exposure requirement.

## Consequences and risks

Both margins become auditable without learner training. Risks are lease-stamp structure leakage, an inadequate public cue, renewal discretization, long-\(k\) sample collapse, and machine-dependent speed.

## Out of scope

Learned termination, a \((z,k)\) menu, variable \(N\) within an object, churn in E2–E4, native code, UAV transfer, and any C-class contract. These exclusions preserve plan §11 and evidence-spec §11.

## Open questions

Which finite D2 \(c,c_Z,k_{\max}\) grid is paired with these points? Which CPU owns the speed record? Is the lagged cue sufficient without probing?

## Could not verify

* No measured corridor \(\sigma_\Delta\), \(M\), parameter count, parameter displacement, or vectorized-NumPy throughput exists in the reviewed evidence; the proposed evaluation and speed figures are prospective.
* The finite D2 \(c,c_Z,k_{\max}\) sweep remains open in ADR 01 revision 3.
* The margin table and renewal variances are analytic outputs of this proposed mechanics definition, not executed repository results; they require Part IV review and later tests before being treated as implementation evidence.
