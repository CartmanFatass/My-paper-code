# EGRCR-B1 retained-result technical intake

Owner: `direction:expressibility_gated_renewal_credit_relay` Code Project Manager  
Treatment: `EGRCR-B1-ORDERED-JOINER-WAITER-CREDIT-v1`  
Recorded: 2026-08-12 PT

## CM conclusion

The calibration and confirmation artifacts are problem-relevant, technically
complete, and accepted for same-direction EM scientific intake. No unchanged-
science recovery or relaunch is warranted. This is technical acceptance only;
the observed association criteria are reported without scientific
interpretation.

Exactly one calibration command and exactly one confirmation command were
launched. Calibration has a child terminal exit of zero. During confirmation,
the observer transport timed out before it emitted its separate terminal JSON;
the child exit code and external peak-RSS observation are therefore unavailable.
The confirmation process no longer exists and was not relaunched. Its retained
result was atomically installed, parses completely, declares
`stage=confirmation_complete`, contains all twelve registered roots and all
required panels, internally records 3.888 seconds, one worker, 306,910 physical
ticks, cap compliance, complete interpretation surface, binding exposure, and
zero anomalies. These direct retained-output facts are sufficient for technical
result intake; they do not repair or invent the missing transport receipt.

## Calibration facts

- Launch: 2026-08-12 03:14:52.458679 PT; terminal 03:14:52.783922 PT; child
  exit code 0; stderr/direct error absent.
- Retained artifact:
  `EGRCR_B1_CALIBRATION_RESULT.json` (10,891 bytes).
- Six registered roots, 128 opportunities per root, each exactly 116 correct / 12
  flipped cues with realized accuracy 0.90625.
- Question-relevant activity did begin: every root retains paired JOINT/SOLO
  quartet witness keys and waiter-action/exposure facts; minimum `X=3`.
- All four frozen gates explicitly passed: source-to-target first stage,
  downstream exposure, joiner-record update expressibility, and cut support.
- Mean root kappa was +0.18333333333333315 for JOINT and
  -0.18333333333333318 for SOLO.
- Frozen `c=7.298102156175058`, `delta=0.40133465713194216`, and calibration
  held-out KL=0.019999999999999928.
- Accounting: 30,720 physical ticks, one worker, cap respected, zero anomalies.

## Confirmation execution and completeness facts

- Exactly one confirmation launch is logged. Its retained result was written at
  03:15:50 PT and is 174,500 bytes. The observer reported timeout 124 and no
  surviving process; it produced no separate confirmation-terminal JSON.
- Every registered root `[17,31,47,61,79,97,109,127,149,167,191,211]` supplies
  128 eligible edges before the 512-block cap. Collection ranged from 226 to
  293 blocks.
- Every root has eight rows in every
  `(type,lag,ordered_role,sampled_action)` cell, 64 request / 64 no-request
  actions at stored probability 0.5, and 116 correct / 12 flipped retained cues.
- Every cut is complete, fixed-point-free, bijective and opposite-type. Raw
  signed-kappa, centered-target, and action-conditioned advantage multisets are
  preserved for every root.
- All arms retain one gradient evaluation, one update, equal work and identical
  displacement `0.401334657131942`; all waiter GAE is untouched, no noneligible
  advantage changes, no clipping, debit, or reverse relay occur.
- All 3 arms x 2 contexts x 12 roots contain normalized utility, selectivity,
  common-uniform requests, allocation, closure/renewal counts, periods, packet
  success, downtime, and cue-stratified probabilities. Every held-out JOINT and
  SOLO panel independently has 116 correct / 12 flipped cues.
- Accounting: 306,910 physical ticks, one worker, cap respected, complete
  interpretation surface, binding question exposed, zero anomalies.

## Result packet for EM

All association criteria did not pass. The retained aggregate reports:

| Effect | Mean | 95% lower | 95% upper |
|---|---:|---:|---:|
| `D_IG_N` | 0.000000 | 0.000000 | 0.000000 |
| `D_IC_N` | 0.144444 | 0.076664 | 0.212225 |
| `D_IG_Y` | 0.000000 | 0.000000 | 0.000000 |
| `D_IC_Y` | 0.001562 | -0.001877 | 0.005002 |
| `Psi_G` | 0.000000 | 0.000000 | 0.000000 |
| `Psi_C` | 0.142882 | 0.075750 | 0.210014 |

Native selectivity effects were positive: INTACT minus GAE mean 0.004711
(95% CI 0.002960 to 0.006462), and INTACT minus BINDING-CUT mean 0.031668
(95% CI 0.023330 to 0.040005).

The artifact records these criterion facts:

- passed: native selectivity above both comparators;
- failed: native utility above both, because INTACT and GAE utility are exactly
  equal at every root (`D_IG_N=0`);
- failed: both native-minus-yoked interactions, because `Psi_G=0`;
- passed: yoked absence;
- passed: probability effect reaches actual requests;
- passed: fixed token and renewal counts are equal; and
- passed: mapping/work/clock/optimizer controls.

The missing confirmation transport terminal means external child exit and
peak RSS remain unknown. It does not leave any source or artifact-repair action:
the retained output is complete, under all internally accounted caps, and the
process is terminal. Re-execution would violate the registered exact-one run.
