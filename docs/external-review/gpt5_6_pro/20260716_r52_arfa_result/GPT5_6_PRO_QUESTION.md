# GPT-5.6 Pro review request: R52-ARFA-G0 terminal result

## Review boundary

Perform a read-only scientific and implementation review of the exact R52
terminal result. Do not edit code, launch experiments, change the registered
contract, or rescue the failed line through tuning.

R52 was selected in the prior response as the unique launch-exact successor to
R51. The implementation was committed before the formal run. The run completed
all 625 registered N-specific batches and returned:

```text
NO_ACCESS_R52_ARFA_SPECIALISTS
```

M0 is fully valid. M1 fails, so the shared result is quarantined even though it
is numerically perfect.

## Repository files to inspect

Read these files in full before deciding:

1. `memory/ALGORITHM_PRINCIPLES.md`
2. `memory/CURRENT_WORK.md`
3. the R52 row and full R52 contract in `memory/ExpRecord.md`
4. `ha_ctse_process/r52_arfa.py`
5. `scripts/run_r52_arfa_gate.py`
6. `scripts/run_r52_arfa_local.ps1`
7. `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/GPT5_6_PRO_RESPONSE_RAW.md`
8. `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/R52_ARFA_RESULT.json`
9. `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/R52_ARFA_TRAIN_UPDATES.csv`
10. `docs/external-review/gpt5_6_pro/20260716_r52_arfa_result/DISPOSITION.md`

The result JSON is authoritative for gates and metrics. The CSV is supplied to
inspect learning dynamics, not to redefine the registered decision.

## Exact observed result

Implementation and exposure:

```text
implementation_valid = true
all M0 checks = true
transitions/arm = 320,000
tokens/arm = 1,280,000
shared optimizer steps = 625
specialist optimizer steps = 125 per N, 625 aggregate
sample/replay logp max error = 0
prefix replay max error = 0
hidden replay max error = 0
focal-relation max error = 0
masked probability mass = 0
```

Fixed-N specialists:

```text
training P(U>0), N=2..6:
0.9575, 0.9985, 0.9920, 0.9975, 0.9940

exact-final deterministic evaluation, every N:
M = 1.0
J = 0.0
U = 0.0

all final-minus-zero 95% intervals = [0, 0]
all four 32-episode block means/N = 0
specialist macro U = 0
```

Shared variable-N policy:

```text
exact-final deterministic evaluation, every N:
M = 1.0
J = 1.0
U = 1.0

shared macro U = 1.0
shared final-minus-zero macro 95% interval = [1, 1]
shared-minus-specialist macro 95% interval = [1, 1]
```

M2 is numerically true, but the contract requires M1 first; therefore all
shared evidence is quarantined.

## Questions that must be resolved

1. Audit whether any concrete implementation, probability, recurrent-state,
   environment, evaluation, checkpoint, exposure, pairing, or analyzer defect
   invalidates M0 or changes the registered estimand. Name the exact line-level
   defect if one exists. Do not infer invalidity merely from the surprising
   result.
2. Explain the causal meaning of specialists having an almost universal
   stochastic training carrier while every deterministic final specialist
   chooses complete station reliability and zero job fulfillment, whereas the
   shared policy reaches perfect fulfillment for every N.
3. Decide whether the registered branch
   `NO_ACCESS_R52_ARFA_SPECIALISTS` remains binding. In particular, inspect the
   pre-registered 625 shared versus 125-per-specialist update/data allocation,
   but do not retroactively change it or authorize a same-contract budget
   rescue.
4. State what can and cannot be reused from R52. Separate task dynamics,
   focal-relation observability, graded terminal utility, recurrent set-pointer
   control, specialist comparison, and deterministic evaluation.
5. Select exactly one genuinely new falsifiable successor edge toward a
   learnable variable-team algorithm. It must first run in a small anonymous
   toy environment, use no environment-specific intrinsic reward or reward
   shaping, and must not reactivate the exact R51 or R52 line under a different
   name.
6. Give the smallest abandonment gate for that one successor: causal claim,
   comparator, model/information boundary, exact exposure, evaluation, M0,
   numerical PASS/FAIL thresholds, mutually exclusive terminal branches, and
   prohibited rescue changes.

## Requested decision

Return all of the following:

1. one explicit verdict, choosing `CONFIRM_NO_ACCESS_R52_ARFA_SPECIALISTS`,
   `INVALID_R52_ARFA_WIRING`, or a precisely justified modified disposition;
2. the strongest implementation-validity argument and strongest objection;
3. the reusable causal conclusion from the carrier/final-policy divergence;
4. one and only one next algorithmic route;
5. its exact minimal abandonment gate;
6. a clear list of routes or rescue variants that are permanently prohibited.

Do not provide parallel routes, generic tuning advice, an environment-specific
intrinsic reward, or a claim that the quarantined shared arm already proves
variable-N learning.
