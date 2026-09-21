# VSP-03 B09: fitted public opportunity scheduling versus G512

## Prospective plan — 2026-09-21, before confirmation

Claim: on the fixed public two-target H40 shared-eight-tick-slot host, the declared fitted
finite-horizon opportunity rule O achieves higher complete team J than ordinary G at
512 updates. This is a conditional algorithm-package claim: O has a correctly specified
age-Markov independent-target family and known task accounting, and estimates its unknown
parameters from G's own eligible public training observations. It is not equal compute,
model-free knowledge, decentralized MARL, an explanation of G's internal mechanism, or UAV
performance. O_known's additional true-law knowledge is never part of the primary claim.

Development/selection: historical G128/B06/B07 outcomes and the complete 2026-09-21 Portfolio
advice motivated O. B08 seeds21801–21803 then compared this one estimator/planner to G/R0/R,
O_self and O_known (three G + three O fits, no hyperparameter or family search).
O−G was +.023081055/+.022924805/+.020360107; O−O_self was positive but smaller/more
variable. All O/O_self first disagreements were earlier O submissions. More own waiting/
expiry costs accompanied O−G gains. Development data selected this claim; they will not
enter the confirmation estimate. Complete B08 evidence is at
`294982aa1302ab3f4eff5d6c471d2e91145eb3c7:runs/vsp_03/opportunity_b08_21801_21803/`.

**Fixed fresh units:** seeds **21901,21902,21903,21904,21905**, five independent blocks.
Every block trains one fresh G from the inherited initialization/address law: 512 updates,
128 complete H40 episodes/update, unchanged B06 model, objective, Adam and FP32/thread1.
One O MLE fits the same eligible training x/episode/time endpoints as B08, preserving
identity and actual gaps. Fixed c6/p.4 start, c[1.01,30]/p[.01,.99] bounds, L-BFGS-B
maxiter200/ftol1e-12/gtol1e-7; no family, checkpoint, seed or hyperparameter selection.
The O policy solves the unchanged full remaining-team recursion from the fitted c,p.
Both methods have the same public actor-information/reward/raw-history access; they use
it differently. O_self shares the fit and assumes isolated own scheduling. Rewards,
actions, timing, horizon, service failure occupancy and public observation cadence stay fixed.

**Endpoint:** after update512 and O fitting, evaluate G greedy and O on exactly4,096 fresh
split200 exogenous worlds per block, shared within the block. Pairing is justified by
these common exogenous tapes, phase and shared training dataset; blocks are independent.
Retain the same seven B08 panels (G,G_stochastic,O,R0,R,O_self,O_known), all zero-update.
The primary estimand is the across-block mean of the paired complete-world mean **O−G**.
The primary baseline is G512; R0/R preserve historical context, and the other panels
are secondary. Independent training/data blocks, not worlds/checkpoints, are inference units.

**Reading rule:** compute five signed block differences, mean, SD and a two-sided95%
Student t interval, df4. A lower bound above zero supports this narrow superiority claim;
an upper bound below zero supports G in this comparison; an interval including zero is
inconclusive. Report signs even when mixed. The old .02 J practical scale is retained as
context: only a lower bound above .02 would support superiority exceeding that scale.
Do not infer equivalence or justify more seeds from a small/inconclusive result. The t
interval assumes independent approximately normal block contrasts; n5 still limits
precision and no distribution-free population guarantee is claimed.

Secondary O−O_self, O−R0, G−R0/G−R, O_known−O and stochastic−greedy G are descriptive,
with no multiplicity-adjusted discovery claim. Report full successes, attempts, failures,
waiting, expiry, non-submission and final-clock blocking. Record every world's first
O/O_self action disagreement and both directions before histories diverge. This contrast
tests coupled versus isolated-job planning, not a pure partner-loss mediator. Do not
postselect favorable worlds or demand all cost components improve to count total J.

**Cost and stopping:** ten planned fits (five G plus five learned O transition models),
327,680 unique training episodes /13,107,200 team ticks, 143,360 evaluation episodes /
5,734,400 team ticks; total471,040 episodes /18,841,600 team ticks /37,683,200 target
transitions. G has2,560 backward/Adam calls; MLE/planning work is measured separately.
No extra collection for O, no optimizer training for rules or evaluations. Expected
scientific-process time is roughly a minute based on B08's35.3 s for three blocks;
this is an estimate, not a scientific time stop and excludes preparation/readback.
Configured local_linux CPU, one thread, sequential blocks; fresh admission at published SHA.

Run once after Pro criticism and technical acceptance. No same-batch addition, deletion or
endpoint movement after scores. A technical failure is retained separately, not zero-filled,
and no automatic retry or replacement seed is authorized by this plan. Interpret a complete
batch by the rule above. Any warranted changed plan is appended before execution; it does
not rewrite this prospective text. Preserve the claim and append results.

## Result

Not run. Pro criticism of this actual plan is pending.

## Pre-execution adoption — 2026-09-21

Pro answer `1473a1ebe0c1b81535adb2a9aabf4a18821051ca` was read in full; the DM response
is appended in NOTES.md. No scientific plan change. Proceed with the original five blocks,
ten fits, endpoints and reading rule. The implemented B09 wrapper at `815040cf4` fixes
five-block completeness, O−G sign and df4 aggregation and passed independent engineering
review. Expiry/blocking remain diagnostic events; only success, attempts and waiting
enter J. Pro's optional O_guard was not added. No confirmation outcome exists at adoption.

## Appended result — 2026-09-21

Complete at source `5510e015b99c6cbaa50543480a1b81fec1db45c1`, ten of ten fits successful,
no retries or batch extension. Five O−G means in declared order:
`+.02466308594, +.00957641602, +.01584350586, +.01990600586, +.01790039062`.
Mean **+.01757788086**, between-block SD.00553976096, df4 t95
**[+.01069935912,+.02445640260]**. Prospective reading **O_SUPERIOR**.
The lower bound is below .02, so a gain exceeding the old practical scale is not established.
No equivalence, neural-mechanism or broader-domain claim.

Secondary descriptive means: G−R0+.012848145, G−R+.013103027, O−R0+.030426025,
O−O_self+.012602783. O−G trades +.070214844 success/team against +.042285156
attempts and +6.588964844 waiting ticks; failed attempts decrease .027929688,
expiry diagnostic events increase .579492188. Full costs and contrary evidence are in
NOTES.md. B08 development blocks were not pooled; the separate later B10 development
guard probe does not alter this confirmation's sample or reading.

Actual cost471,040 episodes/18,841,600 team ticks/37,683,200 target transitions,
2,560 Adam calls; scientific-process wall55.610939 s, CPU55.477193 s, peak RSS446,210,048
bytes on local_linux. All110 artifact hashes and143,360 native evaluation rows/arrays,
curves and paired statistics were read back successfully. Results:
[`runs/vsp_03/opportunity_b09_21901_21905/summary.json`](../../../../runs/vsp_03/opportunity_b09_21901_21905/summary.json).
