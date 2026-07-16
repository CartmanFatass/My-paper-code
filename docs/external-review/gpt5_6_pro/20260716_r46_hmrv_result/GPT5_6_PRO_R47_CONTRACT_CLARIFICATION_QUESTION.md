# GPT-5.6 Pro Clarification — R47-NSOPM-G0 Launch-Exact Contract

Review the repository state at the exact commit supplied in the handoff prompt.
This is a read-only contract clarification. Do not edit files, launch an
experiment, reopen R42--R46, or select another route.

## Accepted boundary

We accept the response in `GPT5_6_PRO_RESPONSE_RAW.md`:

- `CONFIRM VALID_FAIL_R46_HMRV_SUBSTRATE`;
- the scientific claim is narrowed to learned Q/DR sign-transport failure, not
  absence of oracle sign heterogeneity in the finite HMRV dynamics;
- the exact R46 line is permanently retired without rescue;
- the sole next route is `R47-NSOPM-G0`;
- R47 uses natural task-blind process support, a frozen four-mode basis, and
  forced-skill branches only for causal audit;
- R47 has zero policy, high, critic, and intrinsic optimizer steps and reads no
  external reward.

No R47 implementation or experiment has started. A repository audit found that
the proposed direction is exact at the causal level but not yet launch-exact:
the current Alice--Bob environment exposes only the position-only
`intrinsic_effect_view`, and no tracked file defines the proposed seven-field
process view or the spectral estimator. The decisions below affect the
estimand and cannot be chosen by the implementer.

## Repository files to inspect

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/ExpRecord.md`
- `docs/external-review/gpt5_6_pro/20260716_r46_hmrv_result/GPT5_6_PRO_RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260716_r46_hmrv_result/DISPOSITION.md`
- `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
  (`intrinsic_effect_view`, `get_probe_snapshot`, `set_probe_snapshot`)
- `ha_ctse_process/r31_effect_information.py`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/config_alice_bob_asymmetric.py`
- `logs/r31_cfei_reward_off_gate_20260714_181038/result/r31_causal_effect_gate.json`
- `logs/r32_ifepg_paired_gate_20260714_193304/result/r32_ifepg_pair.json`
- `logs/r33_irsc_gate_20260714_214411/result/r33_irsc_gate.json`

## Requested decision

Return one launch-exact clarification containing only the following decisions.
Keep the accepted R47 route, budgets, thresholds, branches, and prohibitions
unchanged.

1. **Frozen source policy and natural schedule.** Name the exact source
   checkpoint, environment/config, controller, action mode, and recurrent-state
   treatment. The available fixed-`N=2`, `K=4`, `k0=10` source used by R31--R33
   is
   `logs/r30_alice_bob_paired_64k_20260714_163908/runs/adaptive_keep_set/seed30031/standalone_process_core_final.pt`.
   State whether R47 must use it. Define exactly how 64 reset groups yield eight
   natural windows per group, four per agent, from 80-step episodes, including
   the selected window indices and whether only complete naturally executed
   `k0=10` windows are eligible.

2. **Exact seven-dimensional process view.** Give component-by-component
   equations and ordering for
   `v_i,t = [delta p_i,t; delta mu_i,t^rel; delta vech Sigma_i,t^rel]`.
   Specify what each delta is relative to, which points enter the relative mean
   and covariance when `N=2`, covariance normalization, `vech` ordering, spatial
   normalization, and the resulting exact seven values. Clarify whether this is
   computed solely from normalized agent positions and whether it requires any
   environment code change.

3. **Exact mode estimator.** Define the order of train-only standardization and
   initial centering; the exact 35-value `chi(u)` ordering; covariance and
   lagged-covariance estimators for lags 1 and 5; whitening regularization and
   any rank/eigenvalue floor; whether the operator is symmetrized; the formula
   mapping a seven-value sample to each scalar mode `m_q,t`; eigenvalue ordering,
   sign convention, and frozen-anchor alignment. Define the 256 within-window
   temporal null construction and which null statistic supplies each 95th
   percentile.

4. **Stability and nuisance audits.** Define the two independent fit halves,
   the held-out rows used for Hungarian alignment, correlation/sign handling,
   and how the minimum `>=0.70` score is computed. Define the exact lag-1 and
   lag-5 coherence statistic and reset-cluster bootstrap. For the audit-only
   nuisance regression, give the target, feature vector, fit/evaluation split,
   model and aggregate `R^2` whose registered maximum is `<0.10`; clarify the
   permitted meaning of initial context, age, and action variance without
   leaking forbidden task or skill fields into mode fitting.

5. **Forced-skill causal branches.** Define how 64 causal contexts select focal
   agent and natural time, which teammate roster/skill and actor/critic recurrent
   states are restored, how a focal skill is forced and held for `H=40`, how the
   two stochastic replicas and common-random-number policy are seeded, and how
   resets before H=40 are treated. Confirm that the 20,480 branch steps equal
   `64 contexts * 4 skills * 2 replicas * 40 steps` and that no forced row enters
   normalization, basis fitting, alignment, or nuisance fitting.

6. **M2 scoring and support.** Define `H10`, `H40-late`, and the exact window
   used for each `C_q^H`, `X_q^H`, and `g_q^H`; define natural-support-valid and
   OOD exclusion numerically. State how `D_H,z`, pooled `D_H`, between-skill
   distance, within-skill replica distance, `rho_H`, and the persistence ratio
   aggregate contexts/agents/replicas. State the reset-cluster bootstrap unit,
   repetitions, and seed for every M1/M2 interval.

7. **Implementation boundary.** Name the smallest allowed tracked files for the
   standalone gate and confirm whether the source environment and trainer stay
   unchanged. Confirm that M0 is the only pre-science validity layer and that a
   single focused dry run may check shapes/finite values before the formal local
   CUDA gate without adding another validation stage.

Do not add a neural encoder, kernel, classifier, reward, actor update, new
environment, task field, second route, or rescue option. End with one compact
launch contract block that can be copied verbatim into `memory/ExpRecord.md`.
