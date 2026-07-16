# GPT-5.6 Pro Clarification — R46-HMRV-G0 Launch-Exact Contract

Review the repository state at the exact commit supplied in the handoff prompt.
This is a read-only contract clarification. Do not edit files or launch an
experiment, and do not reopen the accepted R45 verdict or select another route.

## Accepted boundary

We accept the response in `GPT5_6_PRO_RESPONSE_RAW.md`:

- `CONFIRM VALID_FAIL_R45_SDRA_IDENTIFIABILITY`;
- the pre-result M2 ratio-gain clarification is valid;
- Alice--Bob `K=50` natural-support asynchronous timing is retired;
- the only next route is `R46-HMRV-G0`;
- R46 is local CUDA, fixed `N=2`, `k0=5`, `H=40`, 16 environments,
  100 episodes/updates per environment, 64,000 primitive steps, fixed
  independent Bernoulli-0.5 KEEP/RENEW behavior, zero policy/intrinsic updates,
  and four cross-fitted `6 -> 32 GELU -> 2` critics.

No implementation or experiment has started. A bounded code audit found a few
values that the otherwise exact response leaves implicit. They affect the
registered estimand or reproducibility and must be fixed before launch.

## Repository files to inspect

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/ExpRecord.md` (R45 boundary)
- `docs/external-review/gpt5_6_pro/20260716_r45_sdra_result/GPT5_6_PRO_RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260716_r45_sdra_result/DISPOSITION.md`
- `scripts/r45_sdra.py` (`SDRAQHead` and cross-fit critic contract)
- `scripts/analyze_r45_sdra.py` (DR and bootstrap reference)

## Requested decision

Return one launch-exact clarification containing only the following decisions:

1. **Three-block discount.** Give the numeric `gamma` for
   `G_tau^(3) = sum_{r=0}^{3*k0-1} gamma^r r_env[tau*k0+r]`. Confirm that it
   includes the action's current block and the following two blocks. The
   proposed value is `0.99`.
2. **First-factor prefix encoding.** Give the numeric value of `b_<i` when
   `prefix_valid=0` for the first agent. The proposed encoding is
   `[prefix_valid, b_<i] = [0, 0]`; the second agent uses `[1, actual_b0]`.
3. **Critic optimizer and deterministic schedules.** Confirm whether R46 reuses
   R45's Adam `lr=5e-4`, `eps=1e-5`, default betas, identical true/sham
   initialization, and identical 15-epoch shuffle schedule within each fold.
   State the exact model-initialization and shuffle seeds for folds A and B.
4. **Bootstrap unit.** Choose the scientific bootstrap cluster: independent
   source episode or persistent environment rank. Keep the M1 maximum-weight
   share grouped by persistent environment rank exactly as written. State
   whether all M2/M3 intervals and both role-stratified discordance intervals
   use the same selected cluster unit.
5. **Evaluation stream.** Give the exact action-RNG seed for the 100 evaluation
   episodes and confirm that "paired" means the same 100 role assignments and
   action draws are replayed before and after critic fitting solely for M0
   trace equality, not a trained-policy scientific arm.
6. **Role-stratified M3.** Confirm that the two strata are the ordered
   assignments `(d_agent0,d_agent1)=(1,2)` and `(2,1)`, and that each stratum
   separately requires the sign-discordance lower 95% bound to exceed `0.10`.

Do not change the R46 environment, budgets, critic capacity, thresholds,
branches, or prohibitions. Do not propose a second route. End with one compact
launch contract block that can be copied verbatim into `memory/ExpRecord.md`.
