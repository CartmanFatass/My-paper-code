# GPT-5.6 Pro Review Request: Route After R31-CFEI FAIL

Please inspect the repository implementation and the tracked result JSON. The
R31 design you accepted was implemented without online reward and its frozen
reward-off causal gate returned `FAIL`.

Primary evidence:

- `logs/r31_cfei_reward_off_gate_20260714_181038/result/r31_causal_effect_gate.json`
- `scripts/r31_causal_effect_gate.py`
- `ha_ctse_process/r31_effect_information.py`
- `ha_ctse_process/process_posterior.py`
- `ha_ctse_process/standalone_agent.py`
- `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
- `memory/LTM/R29_R31_EFFECT_REWARD_FAILURE_REVIEW_20260714.md`
- prior raw review: `docs/external-review/gpt5_6_pro/20260714_r30_sparse_exploration_review/RESPONSE_RAW.md`

Observed result:

- Natural heldout `G_nat = 0.487866` nats, cluster CI
  `[0.319984, 0.638954]`; the full posterior fit natural windows.
- Forced-skill causal median between/within ratio `0.889613`, cluster CI
  `[0.763227, 1.078315]`; pooled ratios for skills 0 and 1 were below one.
- Matched-shuffle residual was `-2.068` nats.
- The gate used 1,024 natural windows and 1,024 forced stochastic windows with
  common random numbers; policies were frozen and forced rows never trained the
  posterior.

Please do four things, without offering a menu of unrelated algorithms:

1. Audit whether this is a valid scientific FAIL of R31 or a concrete defect in
   the registered estimator/intervention implementation. In particular, assess
   whether the absolute near-zero matched-shuffle threshold is mathematically
   coherent for `log q_full(z|E_shuf,C) - log q_context(z|C)`; the M2 hard fail
   remains even if that null is revised.
2. Retire R31 if valid. Do not rescue it by coefficient, window, prior,
   posterior-capacity, epoch, bin, or threshold tuning.
3. Select exactly one next causal edge and one implementable algorithm route
   that can create persistent task-agnostic skill effects under sparse reward,
   while retaining R30 fixed-clock asynchronous lifetimes and keeping
   environment shaping absent.
4. Specify the smallest Alice--Bob reward-off or mechanism experiment that can
   falsify that route, including comparator, estimator inputs, gradients,
   stochastic execution, metrics, numerical thresholds, compute, and exact
   PASS/FAIL branches. State what must remain diagnostic-only and what evidence
   would permanently retire the route.

Do not claim cooperation, task improvement, HMASD parity, or S7 transfer from
this single frozen-policy Alice--Bob result.
