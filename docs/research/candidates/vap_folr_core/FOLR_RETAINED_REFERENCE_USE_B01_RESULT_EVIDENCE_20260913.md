# FOLR retained-reference use B01 — E0 result

Status: both required endpoints accepted; **GENERIC_ONLY_BANK_WORSE** for the
fixed historical BANK's optional executable-reference use on this exact host.
[Frozen card](FOLR_RETAINED_REFERENCE_USE_B01_SCIENCE_CARD_20260913.md),
[machine summary](retained_reference_use_b01_781301/RESULT_SUMMARY.json),
[scientific intake](FOLR_RETAINED_REFERENCE_USE_B01_INTAKE_20260913.md).

## Rule, units and observed result

Apply the card verbatim: **strict >+1 OPTIONAL_BANK_REFERENCE; inclusive [-1,+1]
GENERIC_ONLY_WITHIN_MEI preserving sign; strict <-1 GENERIC_ONLY_BANK_WORSE.**
The primary is `d_use = mean(new fixed-BANK returns) - mean(new Generic returns)`.
Observed `d_use = -5.932421875`, strictly below-1. No rule or checkpoint was
selected after seeing the result. This is an outcome-informed fixed-reference
use comparison, with one new Generic fit and zero new BANK fits.

| Quantity | Fresh Generic64 RETAIN | Fixed historical BANK16 |
| --- | ---: | ---: |
| New training instances |1|0|
| New training episodes / native ticks |5000 /100000|0 /0|
| New optimizer steps |4969|0|
| Training seed |781301|781201, historical only|
| Fresh evaluation seed |1781301|2781301|
| New final episodes / native ticks |128 /2560|128 /2560|
| Final native mean |1.055|-4.877421875|
| Episode sample SD |6.03218820066|3.28004326985|
| Conditional episode SE |0.533175147760|0.289917604837|
| Episode minimum / maximum |-13.46 /22.16|-19.80 /1.46|
| Negative / zero / positive return episodes |62 /0 /66|125 /0 /3|
| Actor parameters |103173|89573|
| Actor parameter displacement L2 |32.9618060401|0|
| Complete native wall, seconds |2156.67|3.18|
| Whole invocation peak RSS, KiB |769632|394876|
| Exit |0|0|

There are105120 new native team ticks,4969 updates and256 final episodes total.
All5000 training and256 final returns are finite. The complete new panels are
preserved separately; old BANK episodes are not pooled. Negative-return counts
describe reward outcomes, not inferred collision counts. BANK's full invocation
RSS includes startup/preflight coverage and exceeds its runner-only353920KiB;
the larger complete value is reported. The3.18s fixed evaluation versus2156.67s
new training/evaluation is not a like-for-like speed comparison.

The task-specific arithmetic recomputed every final mean/SD/SE/extreme from the
recorded arrays and matched native publication at1e-12 numerical tolerance, then
applied the unchanged primary rule. Existing `summarize_runs.py` receives only
the one new Generic endpoint in RUN_LEVEL.csv: n1, training-run SD null, no paired
differences. Historical BANK is represented as a retained policy, not another
new training row. Each panel's128 episodes describe its own fixed policy.
No paired SE, training-population uncertainty or resampled success criterion is
reported. No new rollout, model load or scientific invocation occurred in analysis.

## Technical acceptance and immutable evidence

Both commands used published source `5dce539ed54afd4334d09db9dcd94df38c52c2fc`
on the configured hmasd-wsl-node, CPU FP32, NumPy1.26.3, Torch2.7.0+cu118 and
intra/inter-op1/1. [Technical acceptance](retained_reference_use_b01_781301/TECHNICAL_ACCEPTANCE.md)
records exact source self-review, independent high-risk review, proportional
checks, initial support repairs and the complete Generic acceptance before BANK.
No scientific source changed between the two invocations.

The original five-slot H20 reward/information/transition/collection path is
unchanged. Generic uses the accepted full learner and native coupled
environment/replay NumPy stream. BANK loads only the actor from the fixed old
checkpoint, creates no learner/replay/optimizer, resets the new evaluation stream
after construction and initializes private recurrent state per episode. Full
public lifecycle information and observer-private physical/history constraints
are unchanged. Generic learning movement is nonzero; fixed BANK movement is zero.
This supports execution integrity, not a component-memory explanation.

The historical BANK input member is4,532,819 bytes, SHA256
`2385b6ea0f03b36fd4e0f05006acbe64922a8dd9c2c8fa7d0cd396d5ed090989`, staged from
the original E archive and verified before use. It is never refitted or selected
again. Generic's new final.pt is4,694,195 bytes, SHA256
`649804697fe74a7432fcbae4e9ec33e0ff3d9332b3ca894f1932e024f511edd9`.

The Generic summary SHA256 is
`e9929a131c57a6bbb4e5bbc11cdd4296d1563bd9506ec29bd1e01e0a2dd51174`; BANK's is
`ae302602f8469d3d8334b982c1f42c7f4f35b819131f7316c7eb64abc0713a79`.
Raw tar archives preserve original bytes before Git text normalization. Member
digests, exact native logs/admissions/timing and source/command references are in
GENERIC_COLLECTION.json, BANK_COLLECTION.json and CLEANUP_INVENTORY.json.

Native Monitor directly adopted Generic and returned its exit0 terminal, then
adopted BANK already terminal and returned exit0/n128. The full supervisor exit
clocks are20:43:15Z and20:48:33Z respectively. Generic's event identifier embeds
an earlier clock; it is retained as an identifier rather than substituted for
the collected terminal time. Same-handle native evidence and full outputs close
the observation chain without another launch. There were exactly two scientific
submissions in this F unit, one new Generic and one fixed BANK panel.

## Cost, exposure and preservation limits

Both adjacent admissions passed the4GiB physical/effective floor: Generic
15,630,262,272 bytes and BANK15,627,558,912 bytes. Native wall sum is2159.85s;
aggregate user+system CPU work is2160.78s. Measured invocations meet their2700s
and300s caps and the native3000s cap. No section5 source-budget breach or failed
scientific invocation is observed. Focused check support includes an initial
fixture setup error and a corrected narrow rerun; a pre-supervisor missing-Git-
blob connection failure also counts as support, with no accepted model/RNG run.

The known measured support lower bound is144.192s, with components in
RESULT_SUMMARY.json; native plus that lower account is2304.042s. Other attributable
Git/staging/observation/review/intake/integration/preservation/cleanup/provider
coverage remains UNKNOWN. The support1200s and complete invoked4200s caps still
apply to all attributable work once. These lower values do not establish full
cap compliance, zero missing cost or a newly observed breach. Historical E,
completed consultation and unrelated documentary scopes retain their original
accounts. No spare seconds fund another fit, panel, retry or automatic successor.

Unique source/checkpoints/panels and20 support/supervisor files are retained before
reclamation. CLEANUP_INVENTORY.json names the five exact terminal remote paths;
no removal has run at this intake. Root confirms integration/retention and accepts
the assigned reclamation. Shared direction authoring checkout remains available.

The bounded result rejects optional retention of this particular BANK reference.
It does not repair the old E comparison, establish Generic population superiority,
exclude useful entity histories elsewhere, close the entity-history family or
pause FOLR. Matching tuned headroom remains absent; no C/UAV or transfer claim follows.
