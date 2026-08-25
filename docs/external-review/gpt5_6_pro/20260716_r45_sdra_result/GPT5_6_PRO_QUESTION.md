# GPT-5.6 Pro Review — R45 Natural-Support Identifiability Failure

Review the repository state at the exact commit supplied in the handoff prompt.
This is a read-only scientific and implementation review. Do not edit files,
launch experiments, or substitute a neighboring commit.

## Question

R45-SDRA-G0 was the only successor authorized after valid R44 failure. It kept
the complete R41B source skill system and zero renewal residual frozen, sampled
natural source-exact KEEP/RENEW actions, and trained only fold-A/B true action-Q
and action-blind sham critics. It did not update any policy and did not add a
reward, intrinsic term, task field, forced action, or simulator clone.

Before launch, the user explicitly approved the nontrivial interpretation of
the Pro response's M2 notation:

```text
LCB95(WMSE_sham / WMSE_true - 1) > 0
```

The literal `LCB95(WMSE_sham/WMSE_true)>0` would be tautological for finite
positive losses and could not test whether true-Q beats the sham.

The formal result is:

```text
status: VALID_FAIL_R45_SDRA_IDENTIFIABILITY

M0 implementation and data:          PASS
M1 source service and overlap:        FAIL
M2 action-specific informativeness:  PASS
M3 sign heterogeneity:                FAIL

source final win/key0/key1: 0.93 / 1.00 / 0.93
zero/final full traces:      exact
source and renewal-actor drift: 0
source/actor optimizer steps:  0

true-Q weighted MSE:          0.038299
action-blind weighted MSE:    0.376669
ratio-gain 95% interval:      [3.362305, 18.424622]
top-bottom DR-score interval: [0.408256, 0.705869]

agent-0 KEEP ESS / max cluster share: 33.586 / 0.1475
agent-1 KEEP ESS / max cluster share:  3.298 / 0.6156
agent-1 RENEW max cluster share:                0.1353

agent-0 bottom DR interval: [0.475347, 0.577949]
agent-1 bottom DR interval: [0.049455, 0.540281]
same-check sign discordance: 0.000314
95% interval:                [0, 0.000942]
```

Thus action-conditioned prediction is useful, but the estimated renewal value
is almost universally RENEW-positive rather than sign-changing by agent and
context; natural KEEP support is also insufficient and highly concentrated.
The registered branch retires Alice--Bob `K=50` natural-support renewal credit
and this asynchronous temporal-mechanism substrate without rescue.

We need a validity and failure-boundary review, followed by exactly one new
causal edge. The next route must decide whether the evidence calls for a new
substrate with genuine heterogeneous timing demand, a joint co-adaptive skill
and renewal mechanism, or another structurally different upstream question;
it must select only one and justify why the others are deferred.

## Repository files to inspect

Read all of the following before answering:

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md` (R41B--R45 boundary)
- `memory/ExpRecord.md` (R41B--R45 contracts and decisions)
- `docs/external-review/gpt5_6_pro/20260716_r45_sdra_result/r45_sdra_identifiability.json`
- `docs/external-review/gpt5_6_pro/20260716_r45_sdra_result/DISPOSITION.md`
- `scripts/r45_sdra.py`
- `scripts/run_r45_sdra_gate.py`
- `scripts/analyze_r45_sdra.py`
- `scripts/run_r45_sdra_local.ps1`
- `docs/external-review/gpt5_6_pro/20260716_r44_fsnrc_result/GPT5_6_PRO_RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260716_r44_fsnrc_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r44_fsnrc_result/r44_frozen_source_nrc_compact.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/r42_irr_native_roster_residual.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/seed1_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/FINAL_DISPOSITION.md`

## Requested decision

Return one integrated answer containing:

1. **Validity verdict.** Confirm or reject
   `VALID_FAIL_R45_SDRA_IDENTIFIABILITY`. Identify any concrete collection,
   propensity, context, cross-fit, critic, weighting, bootstrap, reset, freeze,
   evaluation, or analyzer defect that changes the branch.
2. **M2 clarification verdict.** Decide whether the pre-launch replacement of
   the tautological literal ratio gate by
   `LCB95(WMSE_sham/WMSE_true - 1)>0` faithfully implements the intended
   action-specific-informativeness claim.
3. **Reusable causal conclusion.** Reconcile M2's strong action-conditioned
   predictive gain with failed overlap and failed sign heterogeneity. Separate
   predictive information, causal support, common-mode renewal value,
   agent-specific timing value, and task service.
4. **Retirement boundary.** Confirm, narrow, or reject retirement of
   Alice--Bob `K=50` natural-support renewal credit and this temporal substrate.
   State precisely what remains untested about general asynchronous skills,
   joint co-adaptation, other substrates, S7, open rosters, and variable `N`.
5. **Exactly one next causal edge.** Select one structurally different,
   falsifiable route and explicitly defer the alternatives. It must explain why
   it is not a hidden data/seed/capacity/threshold/forced-action rescue of R45.
6. **Exact algorithm and substrate contract.** Specify environment/task
   requirements, policy factorization, time/reset semantics, information and
   intrinsic-reward boundaries, updated/frozen parameters, credit estimand,
   comparator, checkpoint migration, and why the selected substrate can expose
   the claimed heterogeneous timing without reward shaping.
7. **Minimum abandonment gate.** Give exact local-vs-cloud target, arms, seeds,
   env count, steps, optimizer exposures, evaluation, M0 checks, scientific
   metrics and thresholds, and mutually exclusive PASS/FAIL/INVALID branches.
8. **Prohibitions and strongest objection.** No R42--R45 rescue, extra data,
   seed substitution, critic expansion, propensity clipping, threshold change,
   forced renewal, simulator clone, reward shaping, environment-specific
   intrinsic reward, immediate S7 promotion, open-roster promotion, or
   variable-`N` implementation. Give the strongest objection to the selected
   route and whether it changes the decision.

Choose one route and one minimum evidence boundary, not a menu or parallel
plan. Do not equate Q-prediction gain, label/action entropy, actor drift, or
renewal frequency with heterogeneous temporal abstraction, skill semantics,
cooperation, or task improvement.
