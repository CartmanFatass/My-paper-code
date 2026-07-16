# GPT-5.6 Pro Review — R53-RCMA-G0 Terminal Result

## Review purpose

Audit the registered R53 terminal result and decide its exact scientific
meaning. The runner emitted `NO_ACCESS_R53_RCMA_SPECIALISTS`, but the raw result
contains a narrower pattern: every specialist and the shared model reached
perfect final deterministic utility; the failed checks are the preregistered
final-minus-zero learning-gain lower bounds.

Do not rescue, rerun, rename or retune the experiment. The question is whether
the registered status and retirement boundary are scientifically interpreted
at the correct level, and which single post-result causal edge remains.

## Repository files to inspect

- `docs/external-review/gpt5_6_pro/20260717_r53_rcma_result/R53_RCMA_RESULT.json`
- `docs/external-review/gpt5_6_pro/20260717_r53_rcma_result/DISPOSITION.md`
- `ha_ctse_process/r53_rcma.py`
- `scripts/run_r53_rcma_gate.py`
- `scripts/run_r53_rcma_local.ps1`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/ExpRecord.md`
- `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/GPT5_6_PRO_R53_FEASIBILITY_RESPONSE_RAW.md`
- `docs/research/literature/n_k_many_agent_deep_dive/SYNTHESIS.md`
- `docs/research/candidates/field_slot_coordination/README.md`

## Frozen contract and terminal facts

- One shared model and fixed-`N` specialists for `N in {2,3,4,5,6}`.
- Exactly 128,000 transitions and 512,000 agent-token decisions per arm.
- 500 shared optimizer steps and 100 steps per specialist; PPO epoch 1.
- Anonymous `N+1` unit-capacity productive entities plus one idle entity with
  capacity `N`; no ID, skills, intrinsic reward or shaping.
- M0 passed every registered check. All replay, prefix, residual-capacity,
  dynamic-mask, previous-relation, hidden and checkpoint errors are zero.
- Every specialist's training positive-return rate is `1.0`.
- Specialist final stochastic utility by `N` is
  `0.9218, 0.9604, 0.9488, 0.9627, 0.9720`.
- Every specialist's final deterministic utility, persistent fraction and burst
  fraction are `1.0`; every 32-episode block mean is `1.0`.
- Shared final deterministic utility and both component fractions are `1.0`
  for every `N`.
- Specialist final-minus-zero 95% CI lower bounds are approximately
  `0.2929, 0.1835, 0.1572, 0.1139, 0.1193`. The registered requirement is
  strictly greater than `0.15` for every `N`, so `N=5,6` fail.
- Shared final-minus-zero deterministic macro CI is approximately
  `[0.1746, 0.1766, 0.1784]`; the registered lower-bound requirement is
  strictly greater than `0.20`, so it also fails.
- All other M1 and M2 checks pass. The exact runner status is therefore
  `NO_ACCESS_R53_RCMA_SPECIALISTS`, and its registered next action says to
  retire exact AMQA/idle-RCMA access and quarantine the shared arm.

## Interpretation tension

The gate did not show lack of executable access: both specialist and shared
policies end at the optimal deterministic policy. Instead, random zero-step
policies already score strongly, especially as `N` grows, leaving insufficient
registered causal improvement margin. Changing the thresholds or dynamics
after seeing the result is prohibited, so the terminal status remains binding;
however, it may be overbroad to infer that residual-capacity autoregression or
shared variable-`N` learning failed.

## Requested decision

1. Confirm or reject M0 validity with a concrete code/result defect. If M0 is
   valid, do not request a rerun.
2. Confirm the registered terminal branch, while separately deciding whether
   `NO_ACCESS` is an overbroad scientific label for the observed result.
3. State the strongest reusable causal conclusion. Distinguish:
   - representational/action support;
   - final policy competence;
   - causal learning gain over initialization;
   - shared-versus-specialist variable-`N` transport.
4. Specify exactly what is permanently retired. Do not retire broader
   variable-`N` learning, dynamic membership, field/set representations or
   event-time credit unless the evidence directly supports that scope.
5. Select one next falsifiable causal edge, considering the curated literature
   synthesis but not merging its separate review into this result audit. Give
   one smallest toy gate with exact arms, budget, metrics, numerical thresholds,
   PASS/FAIL/INVALID branches and prohibited rescues.
6. Do not authorize a same-task threshold repair, harder/easier AMQA variant,
   larger budget, more updates/epochs/seeds, alternate decode, best checkpoint,
   environment-specific intrinsic reward, skills/KEEP/SET, joint variable-`N`
   plus learned timing, or UAV-scale training.

Return one explicit verdict, one scoped retirement statement and one next
causal route.
