# VSP03 B01 seed 1 — valid complete B/EXPLORE

The selected primary comparison is **T=G=F=0.3755859375**, with T-G=0 at update 128.
This is one trained pair on the selected N1 task. All 1,024 sampled main episode records,
including native components and submission time, match across T/G/F. This is sampled behavior,
not universal policy equivalence or proof that all event-aware learning lacks value.

## E0 scope, source and rule

Card: `VSP03_B01_SCIENCE_CARD_20260905.md`. Source/launch commit:
`2c7d7ae08f978aa63d58468f3de1adb372f1339a`; CM technical collection at
`7ae597324a696c15721dca2c8d227892b011c225`. The selected one seed pair, real environment,
actor/critic/optimizer, all fixed endpoints, fixed F, eight-case check and publication completed.
B has no consumption state. No failed scientific attempt preceded this invocation.

Relevant card rule, verbatim:

> Equality or G>T weakens this prior on this task/budget.

> Intermediate-only gains remain local.

The first rule applies at the fixed main endpoint. The second preserves the two earlier gains
at their actual budgets; neither endpoint is substituted for update 128. The descriptive MEI
is 0.02, and the main difference lies inside it. A zero conditional episode SE is not a zero
training-seed population variance; one trained pair cannot estimate that variance.

## Observations and tool analysis

| Update | Evaluation episodes per arm | T return | G return | T-G | Conditional paired-episode SE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 32 | 128 | 0.365390625 | -0.2 | 0.565390625 | 0.0446985064 |
| 64 | 128 | 0.3671875 | -0.2 | 0.5671875 | 0.0444654573 |
| 128, primary | 1,024 | 0.3755859375 | 0.3755859375 | 0 | 0 |

Main F return is 0.3755859375. Every main method/reference has success 0.482421875, attempt
0.951171875, failed attempt 0.46875, non-submission 0.048828125 and mean waiting 11.85546875 ticks.
The 565 submitted-after-reentry episodes have conditional mean return 0.4039469027; this is a
diagnostic subset, not a new endpoint or proof of useful event memory.

G made no submissions in either early greedy evaluation (128/128 unsubmitted at each point).
Thus those T-G differences include a plainly weak *greedy evaluated policy* at those budgets.
They do not establish superiority against a competent generic policy, nor learning beyond F.
Training itself was stochastic and active; early greedy non-submission is not zero learner
exposure. There was no early F evaluation, so no early T-F result is invented.

The DM read the complete CM technical collection, required source/contract scope and collected
summary, then recomputed all endpoint means and paired differences from existing integer-return
episode rows. The outputs are in `results/b01_seed1/ANALYSIS.json`. Original summary, terminal log,
memory receipt and CM collection checks are preserved there; the analysis lists hashes of all
raw artifacts. Raw episode/curve/state files remain in both recorded execution/collection roots.

The scientific-tools `summarize_runs.py` was applied only to the two **main per-training-run**
T/G means in `PRIMARY_RUN_SCORES.csv`, producing `PRIMARY_RUN_SUMMARY.json`. F is a non-training
reference and is reported separately. Episodes and earlier checkpoints were not submitted as
independent training runs. Analysis performed no new rollout, model construction or optimizer step.

## Actual exposure and integrity

| Quantity | T | G |
| --- | ---: | ---: |
| Actor / critic parameters | 1,314 / 257 | 1,314 / 257 |
| Training episodes / ticks | 16,384 / 655,360 | 16,384 / 655,360 |
| Joint optimizer steps / training backward calls | 128 / 128 | 128 / 128 |
| Valid training decisions / gradient rows | 53,473 / 53,473 | 42,139 / 42,139 |
| Evaluation episodes / ticks | 1,280 / 51,200 | 1,280 / 51,200 |
| Initial total L2 / RMS | 6.427330494 / 0.162159562 | 5.939346313 / 0.149847865 |
| First displacement / initial-L2 ratio | 0.017058313 / 0.002654028 | 0.017058399 / 0.002872100 |
| Final displacement / initial-L2 ratio | 2.616672277 / 0.407116497 | 3.095903397 / 0.521253221 |

Final direct-b coefficients are T 2.2572817802 and G 0.0886396989; the differing parameter values
do not override the observed native-return parity. Equal episodes/updates coexist with different
policy-dependent decision-row exposure, as the card anticipated. One configuration and one fixed
primary checkpoint were used; there was no best-seed/checkpoint selection.

The full invocation ran 36,360 complete episodes and **1,454,400 ticks / 256 joint steps**.
F supplied 40,960 ticks and zero updates. The check supplied 320 ticks, 32 decision/gradient rows,
one backward and zero optimizer steps, with cleared gradients and no training-action RNG consumed.
CM verified all 128 curve entries per arm, native integer accounting/means/IDs, all endpoints,
final finite float32 states and publication read-back. Independent review had no material finding;
five non-rollout tests and the selected eight-episode runtime check passed. No missing required
measurement, scope-budget breach or concrete semantic defect was reported or found in intake.

## Execution, resources and cost

Node `wsl_4070`, exact-SHA cwd `/home/wu/hmasd-worktrees/vsp03-b01-seed1-r01`, task
`vsp03-b01-seed1-r01-20260905`; runner `scripts/run_vsp03_b01.py --seed 1` under the existing
supervisor and `timeout 1800s`, immediately after successful actual-node memory admission.
Remote output is that cwd's `temp/directions/vsp_03/exp/vsp03_b01_seed1_r01/`; local complete
collection is `C:/Projects/HMASD-worktrees/cm-vsp03-b01-20260905/` with the same relative output.
Admission is the sibling `vsp03_b01_seed1_r01_memory.json`; supervisor originals are at
`/home/wu/.agent-tasks/vsp03-b01-seed1-r01-20260905/`.

Admission measured physical/effective available memory 15,388,168,192 bytes against the 4GiB
floor. Runner wall from import through publication/read-back was **2.364870157s**, supervisor
window 3s, peak main-process RSS **484,868,096 bytes (462.40625MiB)**. Exit was 0, within the
whole-pair 1,800s cap. Single-thread CPU settings were in source; no live thread census or
aggregate CPU-seconds measurement was taken. No acceleration or cross-host equality claim.

Measured `I+128*C+10*E+O` was T 1.037851087s and G 0.568588821s. C means were 0.003704108s and
0.003596722s; E means 0.002640264s and 0.006999185s. Shared import/check/reference/publication
accounts for the remaining 0.758430249s. O is an arm-wall residual, not an isolated disk benchmark.
Every timing batch belonged to actual training/evaluation; no pilot or timing retry occurred.

The tracker adopted and reported termination directly; the DM acknowledged both notifications.
CM retained collection ownership. An earlier Git fetch problem occurred before any scientific
process acceptance and changed neither the data nor experiment polarity.

## Bounded conclusion and non-conclusions

The generic learner caught up to the same observed fixed-rule behavior by the declared endpoint.
The chosen initialization added no main return in this one training pair. Early greedy policy
differences remain real, but the comparator's early non-submission sharply limits their reading.
There is no observed learning advantage beyond F at the primary endpoint. Exact headroom remains
unknown, and task/seed generality, learning necessity, MARL specificity and old-source
authentication are not established. The next decision is in the accompanying scientific intake.
