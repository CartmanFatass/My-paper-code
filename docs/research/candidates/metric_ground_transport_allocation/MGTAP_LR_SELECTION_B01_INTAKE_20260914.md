# MGTAP-LR-SELECTION-B01 — completed selected-procedure intake

## 中文结论与当前处理

本次有限学习率选择程序完整完成。COND 与 DENSE 均按各自验证 J 选中
slow=1e-4；全新8252训练配对的最终32世界主量为
**COND−DENSE=+0.023704897713093642 J**，严格超过预定MEI0.01，故按卡片原规则
读为 **COND_ABOVE_MEI**。这支持本次所选 COND 程序的局部开发价值，改变了
DM此前偏向inside/adverse的预期；不是稳定排序、调参收益或几何机制证明。

DM接受本批技术完整性和这一有界B观察，保留全部正负世界及旧不利证据。
当前实际下一工作是发布完整证据并请求独立实际结果/后续问题审查，再形成
方向级Portfolio报告。建议的最强下一辨别是固定本轮选中的1e-4做一对全新训练，
检验这个具体配置的重复性；它尚不是新冻结卡片或已派发实验。本轮不追加拟合、
网格、世界、训练步数或重跑。DENSE通用默认不变，MGTAP占槽不被释放。
方向级CONTINUE/RECAST/PARK/CLOSE由当前Portfolio协议最终解释，不由本intake擅自应用。

## What was checked

Frozen scientific/code/command source:2d351d48604396ce478aa900584bd24b3255def5.
The [card](MGTAP_LR_SELECTION_B01_SCIENCE_CARD_20260914.md),
[launch receipt](reentry_20260914/LAUNCH.md) and
[engineering record](reentry_20260914/ENGINEERING.md) preserve prospective selection,
protected native semantics, independent changed-path review, actual source/admission
and the single accepted supervisor handle. Both timing/scratch findings were repaired
before launch. The complete independent [design review and DM response](pro_packets/20260914_lr_selection_design_review/INTAKE.md)
are retained; that review did not inspect these later empirical results.

DM collected all14 native files, including eight checkpoints, plus six original supervisor
files from the finished handle. All20 local member hashes match direct remote SHA256
reads. [NATIVE_EVIDENCE.zip](reentry_20260914/NATIVE_EVIDENCE.zip) retains original bytes;
each member was read back and matched. The6666445-byte archive has SHA256
8fa3b022cf32a38c229ebabb0b87caf43952879a9a4194d850588adf9656123d.
[COLLECTION.json](reentry_20260914/COLLECTION.json) records all member sizes/hashes;
no source, model, native record or existing evidence was deleted.

The one data-only [audit](reentry_20260914/analyze_intake.py) passed: exact launch source,
all eight stage/rate/arm fits in prescribed order; all256 training and32 evaluation rows
per fit, H256, original reward_sum/256 J and declared RNG addresses;128 two-episode
rollouts with four complete epochs/optimizer steps per fit; selected rates and all six
candidate records; saved-selection byte hash; and exact raw-panel recomputation of the
published primary through the already reviewed pure protocol. Actor, critic, branch
inner and branch-projection displacement are finite/nonzero for every fit. Top/fit
limits are empty. No Torch/model/RNG construction, checkpoint loading, learning,
evaluation or native calls were performed by collection/analysis.

The save-before-holdout claim rests on the independently inspected producer/consumer
path plus these completed records, not on a hash or file timestamp alone. Selection
weights/optimizer state do not cross the fresh8252 factory boundary. The raw summary
is preserved as [RUN_SUMMARY.json](reentry_20260914/RUN_SUMMARY.json), with derived
checks in [INTAKE_ANALYSIS.json](reentry_20260914/INTAKE_ANALYSIS.json).

## Selection result — not the final comparison

All candidates used selection master8251, corresponding-arm matched initialization
across rates, new optimizers/private streams,256 train+32 validation at H256.

| LR candidate | Actual LR | COND validation mean J | DENSE validation mean J |
| --- | ---: | ---: | ---: |
| base | 3e-4 | 0.14112299987893276 | 0.026265496601253702 |
| slow | 1e-4 | 0.16492958901611127 | 0.1687065165636938 |
| fast | 1e-3 | 0.13031716182818406 | 0.14945226312362142 |

Each arm's OWN argmax is slow; neither winner is an exact tie. Choosing the largest
arm difference would have favored a different validation comparison and was not done.
DENSE was not kept at its weak base candidate. The saved selection JSON/hash precedes
holdout construction in the fixed runner. Both winners are the lower grid boundary;
this is finite selection, not a bracketed/global optimum or a reason to extend the grid.

These native candidate observations now supply a local setting-sensitivity observation
under8251, beyond the earlier toy-only motivation. They do not identify the cause of
older native losses, population LR responses or out-of-panel tuning gain. Their six
fits are intentionally correlated configurations under one selection master, not six
independent replications of the complete selected learning procedure.

## Fresh holdout and verbatim reading

New master8252 actors/critics, optimizers, environments and private RNGs were trained
from fresh initialization at each arm's fixed selected LR1e-4,256 episodes each. The
sole32 final worlds per arm were not used for configuration choice.

| Quantity | Observed value |
| --- | ---: |
| Final COND mean J | 0.15031149414404593 |
| Final DENSE mean J | 0.12660659643095226 |
| Ordered mean32(COND−DENSE) J | +0.023704897713093642 |
| Conditional paired-world SE | 0.004197354694630503 |
| Positive / negative / zero paired worlds | 29 / 3 / 0 |
| Independent final training pairs | 1 |
| Independent selection replications | 1 |

Verbatim card rule: strict Delta>+0.01 is COND_ABOVE_MEI; strict Delta<−0.01 is
COND_ADVERSE; the inclusive interior is INSIDE_MEI. The positive branch applies.
All32 signed world rows are in [PAIRED_FINAL_SCORES.csv](reentry_20260914/PAIRED_FINAL_SCORES.csv),
including the three adverse worlds. MEI remains the inherited local useful-development
scale, not a p-value or a population equivalence/superiority conclusion.

The supplied scientific-tools run summarizer consumed only the two final run endpoints,
with explicitly declared matching and DENSE baseline. It reports n=1 per arm/pair and
sample_sd=null, correctly not turning32 worlds or six candidates into training runs.
[Its descriptive difference](reentry_20260914/FINAL_RUN_DESCRIPTIVE.json)
0.02370489771309367 subtracts rounded arm means; the final-bit arithmetic difference
does not replace the carded ordered-world primary above. No training/selection-population
SE, stable ranking, learning curve or sample-efficiency estimate is available.

## Hypothesis update and retained contrary evidence

The observation is more favorable than DM's stated leading inside/adverse prediction;
no calibrated probability or owner prediction was supplied. It strengthens the case
that a finitely selected COND option can be useful locally against equally selected
intact-DENSE. It does not establish that tuning caused this advantage: there is no
untuned same-holdout comparator. Both final LRs being equal does not isolate geometry
from the full representations/learning procedures, or show that an LR selector is needed
for every future use. Return and branch displacement do not identify a mechanism.

Early2568241+0.015128847632690413 and8242−0.05684388886006531 J remain valid.
Equal5128212+0.005761321371348559,8213−0.02246957345594415 and
8214+0.02447811898058116 remain separate. TOP8221−0.0684509798102144,
unequal-exposure8231−0.02933437223896382 and the distinct REL observations also
remain contrary evidence for their own procedures. No pooled sign vote or common
estimand is created by appending the new positive programme. The earlier full review's
clarification remains: inability to establish mechanism/stable ordering is not itself
a reason to forbid another B, nor does positive evidence entitle an automatic successor.

## Actual work and cost scope

Completed exposure:6 selection fits plus2 fresh holdout fits;2048 training episodes,
192 validation+64 final episodes;589824 team ticks;1024 rollouts;4096 Adam calls;
13434880 actor collection/evaluation/replay row uses computed from completed records.
Each fit supplies73728 team ticks/512 Adam calls. None is a reused historical fit.

GNU time reports **658.02 seconds full-command wall**,559984 KiB peak RSS
(546.859375 MiB), exit0. It surrounds shell/admission, imports/setup, all fitting and
evaluation, checkpoints/summary/stdout and process exit. Sum fit-body wall is
638.3876269828761s; study body before summary is638.4077481810236s. Neither is substituted
for full-command wall. The prior15–30-minute native estimate was UNMEASURED; this
realization was shorter, not a guarantee for future work. The4GiB physical/effective
admission passed on the actual node. No resource/technical watchdog was reached.

Git/SSH/partial-clone materialization, repairs, code checks/review, observation recovery,
collection/analysis/archive/intake and Pro work are real support work outside that timer.
Their full wall/CPU/provider/lifecycle totals remain UNKNOWN, not zero. The prospective
eight-fit design cost four times the fits/ticks/Adam of one unchanged two-fit recurrence.

The original supervisor log fixes exit at2026-09-14T16:06:39+08:00 (08:06:39Z),
consistent with07:55:41Z start and658s duration. DM's direct fresh UTC observation at
08:10:39Z confirmed finished/exit0/tmux inactive. The monitor's terminal message
contained an inconsistent future08:18:48Z label, and its earlier local-time-as-Z error
and premature finals were also retained. These observer timestamps are not execution
timing evidence. Supervisor uptime continues increasing after exit and is not run wall.
The native source/log/counts and scientific evidence are independently intact.

## Decisions this intake produces

OWNER_DELEGATED ordinary decisions: accept this complete bounded B observation; retain
all original bytes and negative evidence; request meaningful independent review of actual
results, inference and the strongest useful successor. No changed default or new experiment
is applied here. At the clean boundary, owner-item reviews returned[], so there is no
unapplied owner instruction or invented owner reply. Ordinary result facts stay in this
intake, not an artificially promoted owner-approval item.

The strongest stopping alternative is still substantive: the record is mixed, this is
one adaptive selected programme, both winners lie at a grid edge, and one favorable point
may not justify continued branch maintenance. This result does not prove PARK wrong.
DM nevertheless now favors bounded optional-branch continuation because the declared
changed comparison actually produced a beyond-scale fresh contrast against a DENSE arm
chosen by its own best validation return, rather than merely promising tunable headroom.

The leading next discriminator is one fresh **fixed-selected-LR** pair at1e-4, retaining
the same256/32/H256 learning/comparison semantics. Its2 fits would cost147456 team ticks,
1024 Adam and3358720 actor row uses, without six new selection fits. A rough3–6-minute
native working estimate is UNMEASURED, informed by this holdout pair's159.58792896196246s
body plus observed startup/publication; fresh admission and ordinary watchdog planning
would still be needed. This asks recurrence of these fixed configurations, not repetition
of the complete LR-selection programme. No seed or next card is frozen by this proposal.

Repeating the entire three-rate selection with new selection+holdout masters is a different
programme-repeatability question and costs8 fits. Extending the lower grid asks a different
optimization question. Neither is automatically selected because both current winners
are at the edge. PARK remains the cheaper alternative if the best feasible next observation
does not merit further development effort. Independent review should challenge this actual
tradeoff, not grant lifecycle/resource permission. A full signed report and recommendation
then go to Portfolio for its conforming direction-level decision under the current protocol.

## Independent actual-results review received

DM has read the complete166-line response at68144bc0123397fbdc5184fcc4e86055c05c20d8
and recorded its substantive [intake](pro_packets/20260914_lr_selection_results_review/INTAKE.md).
No material defect requires changing the local primary or its COND_ABOVE_MEI reading.
The review favors the specific fixed-selected-rate recurrence over a new selection
programme or PARK, as scientific advice only. DM accepts that recommendation for
the direction report, not as an applied lifecycle/launch decision.

One contrary observation is now explicit: at the selected slow rate, validation
means favor DENSE0.1687065165636938 over COND0.16492958901611127, whereas fresh8252
favors COND. Different fitted policies/panels permit that reversal; the selection-
used candidate is not a second favorable independent replication. Any future fixed-
rate pair is adaptively proposed after8252, not an originally frozen two-pair study.
All earlier evidence, the native source/endpoint and current generic default remain.

## Subsequent Portfolio direction decision

The complete18,522-byte Portfolio answer is now preserved with its exact original
hash and read in full. The [direction intake](pro_packets/20260914_lr_selection_portfolio_direction/INTAKE.md)
applies CONTINUE for one prospective fixed-selected-rate1e-4 fresh pair, preserves
the title-only actual prompt delivery deviation and all source/claim limits,
and updates later peer facts. The intended20,627-byte prompt was not actually sent
in full; Portfolio located the matching immutable report/manifest and materially
addressed it. No duplicate request or historical input rewrite repairs that fact.
This is an applied direction disposition, not an executed successor. No new seed,
card, two-fit driver or native invocation exists at this intake boundary.
