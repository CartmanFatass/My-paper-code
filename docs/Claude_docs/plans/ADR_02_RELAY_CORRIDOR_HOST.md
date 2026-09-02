# ADR 02 — Relay corridor host family for duration-plan E2–E4

Provenance: drafted by GPT Pro (GitHub connector on `CartmanFatass/My-paper-code`, branch `main`)
on 2026-09-02 from the prompt in `ADR_REQUEST_PROMPT_GPT_PRO_20260902.md`, pasted into the Claude
Code session by the owner and stored here verbatim (only this header added). Status remains
`proposed`. Adversarial review: `../reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md`. GPT Pro's
shared "could not verify" list is kept at the end of `ADR_01_D2_POLICY_INTERRUPTION.md`.

---

## Title

ADR 02 — Relay corridor host family for duration-plan E2–E4

## Status: proposed

## Context

The plan assigns E2 to UAV scenario 1 and E3/E4 to the relay corridor; this ADR includes its homogeneous point without changing that assignment (plan §§5, 11). Environment advice §§3–4 fixes P1–P8, the parameter set, three references, ragged boundary, entity CRNs, and speed target. Ledger K-1–K-7 and §9.3 require controllable hazard, temporal depth, and renewal durations without a predictable pattern. The corridor is B-EXPLORE, not a proof or transfer gate (evidence spec §11; advice §§6–7). The duration direction holds roster size fixed per object although \(N\) remains a family parameter (spec §11.5).

## Decision

Return ragged entity records at the host boundary; learner packing is external. Per-step task reward lies in \([0,1]\) plus named costs. Each entity has a stream keyed by `(master seed, episode, entity id)`, producing matched tapes without shared RNG state (advice P6, §4).

The homogeneous point has \(\lambda_1=\lambda_2\); E3 has two corridor regions with \(\lambda_1\ne\lambda_2\). E4 uses a renewal process whose durations \(D\) follow the selected deterministic, exponential, or heavy-tailed law. References are: oracle with the latent, greedy on public state, and structure-blind with equal public information/work but the target structure removed. **ADR definition, not a result:** at each registered \(m_q\in\{m_{small},m_{medium},m_{large}\}\), calibrate \(J_O=J_B+m_q\) and require \(J_G\le J_B\le J_O\).

Note only (advice §4): FRRIE is \(K=3,\lambda=\rho=0,N\) swept; VNFC is \(Z=2,\rho>0\), terminal loss, \(N\) swept; SCDMP is swept \(k,\lambda>0\), ordered actions; UCOPE is \(c>0,v\) as margin, \(k\) as probe period; CBSC uses nuisance coordinates as \(Z\).

## Parameters

`N:int`, required, positive integers/no divisibility; `K:int`, required, positive integers; `Z:int`, required, positive integers; `H:int`, default \(10k_{max}\), range \(H\ge10k_{max}\); `k:int`, default 10, sweep unfixed; `lambda: probability`, required, \([0,1]\); `rho: probability`, default 0, \([0,1]\), fixed 0 for E2–E4; `c,v: float≥0`, defaults 0, sweeps unfixed; `m: float>0`, required, three values unfixed; `time_homogeneous: bool`, default `true`, sweep `{true,false}`; `lambda_regions: pair`, default \((\lambda,\lambda)\), equal for E2 and unequal for E3; `renewal_law: enum`, default `deterministic`, E4 sweep `{deterministic,exponential,heavy_tailed}`.

## Invariants

1. Host observations are ragged entity sets with no padding.
2. Each entity stream is keyed only by master seed, episode, and entity id.
3. Every positive \(N\) is valid; no \(N\bmod K\) constraint exists.
4. \(H/k_{max}\ge10\).
5. At all three margins, references satisfy the calibrated return relations.
6. Vectorized NumPy reaches approximately \(10^4\) environment steps/second/core before native code.

## Tests-as-specs

Use `tests/relay_corridor_host_test.py` with `temp/pytest_relay_corridor`, following `CLAUDE.md`'s top-level `*_test.py` and isolated-basetemp rules. Tests 1–6: varying live counts, assert no padding; batch/order permutations, assert entity tapes are unchanged; divisible and non-divisible \(N\), assert reset/step succeed; largest \(k\), assert ten complete segments; three \(m_q\) values on the reference census, assert gap/order; native-disabled, core-pinned vector benchmark, assert the throughput budget.

## Metrics to log

Returns/reference gaps; hazard events by region; realized \(D\); segment lengths, interruption delay, switches, probes/costs, live counts, CRN checks, steps/core-second, and transition/update/evaluation counts.

## Resolution arithmetic

The first HMASD learner uses Adam \(10^{-4}\), 200 rollout updates, explicit gains 1.0/0.01, and eight evaluation episodes (`config_1.py:145–207`; `hmasd/agent.py:HMASDAgent.__init__`; `hmasd/networks.py:SkillCoordinator._init_weights`). **Inference:** the coarse displacement is \(0.02\). Return resolution is \(\sigma/\sqrt8\), or paired \(\sigma_\Delta/\sqrt8\); advice P3 requires \(m\) to be at least three times the largest declared resolution term. The host adds no learner parameters; the exact learner count is absent and must be logged in the spec §11.4 exposure line.

## Consequences and risks

Shared oracles, tapes, and evaluators improve comparability; ragged vectorization, the structure cut, symbolic calibration, and the speed budget are risks.

## Out of scope

Learned termination, \((z,k)\) menus, within-object variable agent count, C contracts, UAV transfer, native kernels, and work beyond E2–E4.

## Open questions

What numeric grids instantiate the parameters? Which heavy-tailed law defines E4? What corridor dynamics realize the calibrated margins?
