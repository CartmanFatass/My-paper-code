# ADR 02 — Relay corridor host family for duration-plan E2–E4

Provenance: revision 4, finalised after Part IV of
`../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`. Revision 1 is at commit `ea20bccb0`,
revision 2 at `7591f23a1`, and revision 3 at `149bd7c4e`. Normative companion:
`RELAY_CORRIDOR_MECHANICS_20260902.md`, now finalised. This revision applies Part IV §IV.8.1
decisions 1–3 and items IV.4, IV.5, and IV.7 as wording only; every formula, proposed grid, and
margin value is unchanged. Status remains `proposed`; Part IV states that no further architecture
review is required before host implementation, after which the host diff is reviewed against the
nine invariants below.

---

## Title

ADR 02 — Relay corridor host family for duration-plan E2–E4, revision 4

## Status: proposed

## Context

The duration plan §§5–6 and 11 assign E3/E4 to the relay corridor under B-EXPLORE. Environment
advice §§3–4 requires three references, resolvable margins, ragged CRNs, ten fixed-\(k\) segments,
and vectorized-NumPy speed. Review Part I F2.1–F2.9, §4.1, Part II II.6–II.10.1, and Part IV
§§IV.1–IV.8.1 fix agent-pinned regions, the full-stack HMASD adapter, mean-matched renewal laws,
D0 as \(c=c_Z=\infty\), both \(m\) and \(m_{\mathrm{dur}}\), \(K=2\) for the first object, and the
ten-segment rule only for fixed-\(k\) D0. ADR 01 revision 3 supplies \(k_{\max}\), \(k_Z=H\) for
E3/E4, per-agent segments, and \(M\)-row exposure accounting; ADR 01 is unchanged. The finalised
`RELAY_CORRIDOR_MECHANICS_20260902.md` is the normative mechanics companion.

## Decision

The host has two regions, \(Z\) zones, and \(N\) fixed-roster agents pinned to region and zone.
Region \(r\) has \(\theta_r\in\{0,\ldots,K-1\}\); zone \(q\) requires role
\((q+\theta_r)\bmod K\). An event changes \(\theta_r\) and invalidates regional leases. The full
HMASD stack runs with `n_z = K`: the low-level policy emits a continuous \(K\)-vector each step and
the host takes its argmax as the role. The ADR-01 adapter emits `RENEW` for exactly \(i\in S_t\) and
`KEEP` otherwise; `RENEW` opens the segment, stamps the epoch, and causes one zero-service step. The
learner receives the shared mean reward, and every per-agent service indicator is logged. The team
code remains present, but a reserved E5 coupling switch and state field are fixed off/zero; the
coupling rule is designed only when E5 is scheduled (review §IV.8.1 decisions 1 and 3).

E3 uses Bernoulli hazards \(\lambda_1,\lambda_2\). E4 uses positive-integer deterministic,
geometric—discrete exponential—or rounded-lognormal \(D\), matched only on \(E[D]\), with
\(\operatorname{Var}(D)\) reported. A deterministic episode starts with a full dwell \(D\), so
events and fixed boundaries occur at \(D,2D,\ldots\); fixed \(k=D\) is therefore its restricted
oracle. Public cue \(y_{r,t}=\theta_{r,t-1}\) is one step behind the current latent; the change flag
is immediate, and oracle latent is excluded. At \(K=2\), the old cue plus the fact that a switch must
choose the only different latent reveals the new latent, so greedy equals the switching oracle and
the learner ceiling is \(J_{\mathrm{sw}}\). Accordingly, \(m\) is registered and reported but is
not an E2–E4 acceptance criterion; \(K=3\) is the registered family point where \(m\), the cue, and
probe value \(v\) become meaningful. E2–E4 have \(c_{\text{probe}}=0\) and no probe action, while
reserved fields preserve the state layout (review §§IV.2, IV.4, IV.5, and IV.8.1 decision 2).

References are the switching oracle, each fixed-\(k\) oracle, the best open-loop zone-role map/fixed
period, and greedy. Exact DP/enumeration registers

$$
m=J^*_{\mathrm{switch}}-J^*_{\mathrm{open}},\qquad
m_{\mathrm{dur}}=J^*_{\mathrm{switch}}-\max_kJ^*_k.
$$

The E3/E4 acceptance scale is \(m_{\mathrm{dur}}\). D0 is the same learner with
\(c=c_Z=\infty\) and cannot renew between fixed boundaries.

Family coordinates from advice §4 remain: FRRIE uses \(K=3,\lambda=\rho=0\) with \(N\) swept;
VNFC uses two contexts and \(\rho>0\); SCDMP sweeps \(k\) at \(\lambda>0\); UCOPE enables
\(c_{\text{probe}},v,k\); CBSC uses nuisance contexts.

## Parameters

`N,K,Z,H: positive int`, fixed within an object; first-object `K=2`, registered family point `K=3`;
`n_z=K`; `low_level_action_dim=K`; `role_decode=argmax`; `rho=0`; `Delta: float in (0,1]`;
`lambda_regions: pair in [0,1]^2`; `D0_k_set: positive-int set`;
`renewal_law ∈ {deterministic, geometric, lognormal}`; `renewal_mean, lognormal_shape > 0`;
`c_probe=0`, `v` inactive; `e5_coupling_enabled=false`. D2's `c,c_Z,k_max,k_Z` follow ADR 01,
with `k_Z=H` for E3/E4. `time_homogeneous` is removed: renewal age is explicit state and service
mechanics are time-homogeneous. The registered proposal is unchanged in the companion mechanics
page.

## Invariants

1. Host-boundary entities are ragged and unpadded as a family property, although \(\rho=0\) keeps cardinality fixed within E2–E4 objects.
2. Entity and regional-event RNG streams are key-stable and order-independent.
3. Every positive \(N\) is valid; no \(N\bmod K\) rule exists.
4. Agents remain pinned; hazards and dwell laws follow registration, deterministic initial dwell is full-length, and the laws share only \(E[D]\).
5. Enumeration reproduces every stated \(m\) and \(m_{\mathrm{dur}}\); \(m\) is reported, while \(m_{\mathrm{dur}}\ge3\sigma_\Delta/\sqrt{E_{\mathrm{eval}}}\) is the acceptance-scale requirement.
6. \(H\ge10\max(\text{D0\_k\_set})\); D2 \(k_{\max}\) is exempt and reports \(M\) rows per rollout.
7. The continuous-action argmax and ADR-01 renew mask determine roles and `KEEP/RENEW`; pre-cost shared reward is in \([0,1]\), per-agent indicators are logged, and probe/coupling-off behavior is exact.
8. References, D0 cut, setup outage, deterministic \(k=D\) equality, cue timing, and \(K=2\) greedy equality match the mechanics page.
9. Native-disabled NumPy is checked against the recorded \(10^4\)-steps/s/core target.

## Tests-as-specs

Run:

`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/relay_corridor_host_test.py --basetemp C:/Projects/HMASD/temp/pytest_relay_corridor`

Tests 1–9 use, respectively: distinct fixed-\(N\) family instances, asserting ragged records without
padding; permuted batch/enumeration order, asserting identical keyed tapes; divisible and
non-divisible \(N\), asserting both execute; scripted Bernoulli and three-law dwell tapes, asserting
pinning, a full deterministic initial dwell, matched means, and reported variances; the three
unchanged proposal points plus measured \(\sigma_\Delta\), asserting both margins, reporting \(m\),
and applying the resolution inequality to \(m_{\mathrm{dur}}\); too-short \(H\) and large-
\(k_{\max}\) D2, asserting only fixed-\(k\) D0 is rejected and \(M\) is emitted; continuous
\(K\)-vectors, scripted \(S_t\), and reward/probe/coupling boundary cases, asserting argmax roles,
exact renew masks, shared mean reward, logged per-agent indicators, reward range, and disabled
fields; exhaustive reference traces including \(D=20,k=20\), cue timing, and \(K=2\), asserting
oracle equality, D0 cut, and greedy \(=J_{\mathrm{sw}}\); and a pinned-CPU native-disabled
benchmark, recording target disposition. The interpreter, top-level `*_test.py` naming, and isolated
scratch convention follow root `CLAUDE.md` §§Environment and Commands/Tests.

## Metrics to log

\(m\), \(m_{\mathrm{dur}}\), all reference returns, regional hazards, \(D\) and
\(\operatorname{Var}(D)\), cue/change timing, renew masks, stale-service loss, per-agent service
indicators, shared reward, segment lengths, \(M\), CRN audit, greedy gap, probe/coupling switch
state, transition/update/evaluation counts, throughput, and machine identity. Per-agent indicators
are retained specifically so the asynchronous-credit issue identified in review Part I F1.10 can be
examined later.

## Resolution arithmetic

**Proposal:** \(4{,}096\) matched evaluation episodes, so resolution is

$$
\frac{\sigma_\Delta}{\sqrt{4096}}=\frac{\sigma_\Delta}{64}.
$$

Per-episode mean-return differences lie in \([-1,1]\), hence \(\sigma_\Delta\le1\); the smallest
proposed \(m_{\mathrm{dur}}=0.057037\) exceeds \(3/64=0.046875\). The corridor learner's \(M\),
parameter count, optimizer-step count, and norm displacement are machine-generated exposure-line
measurements; ADR-01 optimizer totals are not copied. This follows ADR 01 revision 3's identification
of \(M\) as the binding long-hold term and evidence-spec §11.4's machine-generated exposure
requirement.

## Consequences and risks

Both margins remain auditable without learner training, but only \(m_{\mathrm{dur}}\) gates the
first-object duration question. Risks are lease-stamp structure leakage, low-level argmax learning,
chattering on the immediate change flag, renewal discretization, long-\(k\) sample collapse,
team-code inertness while coupling is off, and machine-dependent speed. The E5 coupling rule is
intentionally deferred.

## Out of scope

Learned termination, a \((z,k)\) menu, variable \(N\) within an object, churn in E2–E4, active E5
coupling mechanics, native code, UAV transfer, and any C-class contract. These exclusions preserve
plan §11 and evidence-spec §11.

## Open questions

Which finite D2 \(c,c_Z,k_{\max}\) grid is paired with these points? Which CPU owns the speed
record? Which finite \(c\) grid is sufficient for D2 to stop chattering on the immediate change
flag?

## Could not verify

* No measured corridor \(\sigma_\Delta\), \(M\), parameter count, parameter displacement, or vectorized-NumPy throughput exists in the reviewed evidence; the evaluation and speed figures remain prospective.
* The finite D2 \(c,c_Z,k_{\max}\) sweep—including the \(c\) threshold that suppresses change-flag chattering—remains unfixed in ADR 01 revision 3.
* The E5 coupling rule is intentionally not defined; only its default-off switch and reserved state field are fixed.
* The unchanged margin table and renewal variances are analytic design values reviewed in Part IV, not executed repository results; host tests must reproduce them before they become implementation evidence.
