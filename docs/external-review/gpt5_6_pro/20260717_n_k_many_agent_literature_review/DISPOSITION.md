# Literature Architecture Review Disposition

## Source

- Model: GPT-5.6 Pro
- Date: 2026-07-17
- Related claim: literature-informed architecture for variable active-team size
  `N` and heterogeneous per-agent event duration `T_i`
- Verdict: `ACCEPT_WITH_MODIFICATION: ARES-SMDP`
- Disposition: **accept as the selected architecture sequence and R54 design
  candidate; defer implementation and launch until the separate R53 terminal
  review is archived**

## Accepted

- Replace the proposed simultaneous four-mechanism bundle with the ordered
  `ARES-SMDP` program: representation sufficiency, ordinary learning transport,
  exogenous dynamic membership, fixed-roster exogenous heterogeneous time, and
  only then the joint exogenous `N_t + T_i` gate.
- Use ACE only for readiness/member-loss runtime ideas, ACAC for agent-owned
  event histories and duration-correct SMDP credit, and InforMARL for the
  permutation-safe full active-set reference.
- Keep Sable, CT-MARL and IARO diagnostic-only; absorb ExpoComm only if a later
  large-`N` cost gate requires bounded sparse topology; do not absorb
  Safe-M3-UCRL.
- Treat active-set GNNs, slots, masses, `log(1+N)`, residual selection and masks
  as deterministic representations with no policy log-probability. Only real
  ready-member KEEP/SET actions remain autoregressive sampled policy factors.
- Use `(member_key, membership_epoch)` solely in the collector/buffer ledger;
  rejoin creates a new epoch, survivors retain skill/age/hidden/event history,
  and only sampled ready-member actions enter PPO ratios.
- Preserve primitive-reward accumulation, `gamma^T_i` bootstrap, agent-owned
  event GAE and policy-version truncation semantics. Do not multiply an already
  discretized primitive reward by duration.
- Accept `R54-HFSR-G0` as the sole post-R53 design candidate: a supervised
  `full_active_set_reference` versus deterministic `hybrid_m8_l2`
  representation-sufficiency gate, with the exact model, data, M0/M1/M2 and
  abandonment contract in the raw response.

## Clarifications

- `ABSORB NOW` means entry into the architecture/data contract, not immediate
  implementation across the trainer. Each behavioral component remains gated
  by the serial R54--R58 sequence.
- The reviewed commit intentionally lacked a terminal R53 JSON. R53 completed
  afterward and is handled by a separate result-review entry; no intermediate
  R53 value influenced this architecture verdict.
- R54 remains a Level-0 supervised representation test. It provides no evidence
  for PPO learning, cooperation, skills, dynamic membership, variable time or
  UAV transfer even if it passes.

## Rejected or deferred

- No first-stage combination of sparse GNN, learned population slots, critical
  residuals, dynamic membership and asynchronous time.
- No stochastic slot directives or claim that deterministic slot transforms
  are MAT actions.
- No learned admission/readiness/termination, environment-specific intrinsic
  reward, skill reward redesign, mean-field substitution, cold-start low actor,
  or UAV-scale training.
- No R54 implementation or launch until the R53 terminal result review closes
  the current controller boundary.
