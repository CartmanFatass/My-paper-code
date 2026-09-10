# DISH B07 E0 result evidence — 2026-09-08

The sole matched seed127 pair is a complete **B/EXPLORE native-service result**:
`Delta_mean=-135.25` ticks. Both real learners completed their fixed exposure; all16 modal
evaluation rows completed1200 ticks. This is one independent training pair, not16 seeds.
Scientific interpretation and executed decisions are in the adjacent result intake.

## 1. Frozen question and rule

Card: `DISH_OWN_COMMAND_MEAN_B07_SCIENCE_CARD_20260908.md` §§2–6, frozen at
`fc52d630de39429383cb12ad7ec8e7b2877f67b6`. OWN uses `3*tanh(m+a_prev/3)` with raw own
applied acceleration; DIRECT uses `3*tanh(m)`. Both use the same-information STRUCTURED
LOW_LR learner, paired initialization/exogenous streams and update16 selection. MEI is+24
mean ticks, opposite scale−24. Initial-relative changes are companions, not the primary.

The two applicable card §5 rows, verbatim:

| 完整新观察 | 对这个候选的有限读法与后续建议 |
| --- | --- |
| `Delta_mean<=−24`，或收益伴随足以否定其开发价值的原生损害 | 保留 DIRECT，停止该 OWN_COMMAND_MEAN 候选的当前扩展；不以无效提交减少、平滑代理指标或一次换主挽救负服务结果。不得据此关闭整个来源议程。 |
| 无普通合法换主 | 原生服务主量仍有效；收益只能称普通／incumbent服务证据，来源原点及 COPY−RETAIN／SHADOW−COPY 仍未估计。 |

No input, learner or primary defect was found. H/resource and syntax-cost gaps below limit
those quantities rather than the service result under evidence-spec §§4,5.2,11.8.6–11.8.7.

## 2. Execution, bytes and technical acceptance

Root submitted the one accepted handle `dish_b07_seed127_20260908_run01` on `wsl_4070`
via `hmasd-wsl-node`, detached cwd
`/home/wu/hmasd-worktrees/dish-b07-seed127-20260908-run01`, scientific source
**`a4612a020921d24269a19a3471cc03fa62c082c8`**. The literal payload comes from CM record
commit **`ae5cdea0f292d632c59eb79e655f6d4861a81224`**. Root reports supervisor exit0;
retained OS timing also says exit0 and the terminal JSON says COMPLETE. No relaunch,
additional arm, checkpoint selection or scientific retry occurred during collection/intake.

The local full envelope is
`temp/directions/degraded_incumbent_shadow_handover/exp/own_command_mean_b07_seed127_20260908_run01`
in the designated direction checkout, and the same relative path under the remote cwd.
Runtime checkpoints and stdout remain there. The compact durable evidence directory
[`own_command_mean_b07_20260908_run01/`](own_command_mean_b07_20260908_run01/) retains exact
raw summary, CM collection, admission, resets and timing receipts. Its
[`manifest.json`](own_command_mean_b07_20260908_run01/manifest.json) records byte counts/SHA256
for those files and the runtime stdout/wrapper/initial/update16 checkpoints.

DM checked the collected copy of the staged wrapper:
`2fb1d2bd447b0bb84594869cd50610de94518ac85a10c69ed400eaac382ceedd`,2432 LF bytes, matching
the accepted literal payload. Source IDs in summary/CM evidence agree. The observed master is
`e3426c64f47fff20f417f005c1b1b85e2eb64de28cb48b7c2ba25472426b6764`, matching the card law
for seed127. This was a readback of the completed run, not a new stochastic initialization.

Recorded configuration is CPU, native float64, policy FP32 and one Torch/BLAS thread.
One shared initializer has model norm38.29155618292703 and count0 actor/snapshot/critic
Welford. Its optimizer defaults are3e-4; the retained arm path rewrites them before learning.
All16 actual update receipts in each arm report both learning rates3e-5, finite loss and
gradient flags,65536 ordinary training transitions and512 optimizer steps per arm. CM read
both real update16 checkpoints and found all model tensors finite. Relative L2 movement is
0.04690254949701972 DIRECT and0.0484554855508188 OWN. Final actor/critic Welford counts are
262144/65536 in both; snapshot counts12321/12309 respectively. Separate evolution is retained.

DM inspected the actual summary/configuration/curves/rows and reused CM's checkpoint readback
and accepted independent source review. No learner or test suite was rerun at scientific intake.
Both initial and final panels use the same four recorded resets, appropriate mode and own
checkpoint/Welford. All rows end at fixed_horizon with native tick1200, zero unstepped remainder,
zero legal transfers, null first post-step transfer tick, and zero post-transfer service.

## 3. All service outcomes and native companions

| Condition | DIRECT initial | DIRECT final | OWN initial | OWN final | Final OWN−DIRECT | DIRECT change | OWN change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 |604|770|473|549|−221|+166|+76|
| TARGET_VISUAL_MASK / K4_TO_K12 |446|400|495|474|+74|−46|−21|
| TERRAIN_RELAY_MASK / K8 |699|910|655|581|−329|+211|−74|
| TERRAIN_RELAY_MASK / K4_TO_K12 |365|692|385|627|−65|+327|+242|
| Equal-condition mean |528.5|693|502|557.75|**−135.25**|**+164.5**|**+55.75**|

The final mean loss is11.2708% of the fixed1200-tick horizon and19.5166% of DIRECT's final
mean. The horizon scale is the card's MEI reference; neither percentage supplies uncertainty.
One positive final condition and all initial-relative losses remain visible. Both positive
initial-relative means are direct companions, not evidence of superiority or faster learning.

| Final condition | DIRECT invalid commits | OWN invalid commits | DIRECT native energy | OWN native energy | OWN−DIRECT energy |
| --- | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 |0|0|289057.1847|297840.2236|+8783.0389|
| TARGET_VISUAL_MASK / K4_TO_K12 |75|0|274505.0281|298727.3146|+24222.2865|
| TERRAIN_RELAY_MASK / K8 |4|0|289220.1344|298386.3429|+9166.2085|
| TERRAIN_RELAY_MASK / K4_TO_K12 |40|32|282166.0942|294856.9197|+12690.8255|
| Mean |29.75|8|283737.1103|297452.7002|**+13715.5899**|

Final invalid-commit totals are119 DIRECT and32 OWN. Initial totals are32 and91; initial
energy means266703.9264 and296285.8062. Raw values for all16 rows are retained. All other
six evaluation hard-event counts are zero. Each arm/phase has4800 actual evaluation ticks;
these counts are not rejection probabilities without a proposal-opportunity denominator.
Every final energy comparison has the same1200-tick duration; no survival normalization or
early-termination energy advantage is involved. Zero evaluation events do not establish safety.

Training is separate from evaluation:

| TRAIN quantity | DIRECT | OWN |
| --- | ---: | ---: |
| Ordinary transitions / optimizer steps |65536 /512|65536 /512|
| Service ticks |29426|29548|
| Native energy |15122722.5574|15933012.0818|
| Invalid commits |4366|4405|
| Separation breaches |1|2|
| Native terminal events |32|32|
| Ordinary legal transfers |0|0|
| Service-label eligible E |24846|24835|
| Next mask count |65504|65504|

All remaining training hard-event counts are zero. OWN's slightly higher training service
and higher training invalid/separation counts are retained alongside its final service loss;
they do not identify its cause. Checkpoint movement alone is not mechanism value.

## 4. Work, resources and accounted cost

Actual exposure is two learners×16×32×128 =131072 ordinary transitions and
two×16×4×8 =1024 optimizer steps,16 evaluations/19200 actual ticks. The native training law
`2N+2E+H` gives DIRECT180764–677684 calls and OWN180742–677442; pair361506–1355126.
H remains unmeasured, with per-arm upper bounds496920/496700 (pair993620). Zero ordinary
transfers do not imply zero private consequence work. This tightens the known bound using E;
it is not another diagnostic invocation or an exact call count.

Admission at2026-09-08T20:29:34.858367Z passed physical/effective memory15638478848 bytes,
above4294967296. GNU supervised wall is444.72s at its stated resolution; whole-chain readback
is444.730543686s. Its0.02s final closure allowance is stated, not observed final completion.
The terminal runner clock is narrower:444.380098802s, with prior11.8611445s including startup.
Do not add that prior/startup again to the whole-chain quantity.

CM accounting is **463.243287086s pair**, DIRECT231.564313254s and OWN231.678973832s:
checks11.7811445 + whole-chain444.730543686 + closure allowance0.02 + collection6.7115989.
The last term includes5.7115989s observed command wall and1s final-write allowance. DM's
necessary primary/evidence publication and run-summary commands add0.2882093+0.3020878
=0.5902971s once, giving the **accounted subtotal463.833584186s**, DIRECT231.859461804s,
OWN231.974122382s. These allocations subtract measured exclusive arm wall then share S/2.
Ordinary control-plane scientific writing/Git work is separate.

Root explicitly reports **no separately measured syntax-check charge**. It remains an
additional unmeasured component; no value is inferred. Thus the accounted part is below
1800s/arm and3600s/pair with no observed cap breach, but this is not an exact complete-cost
conformance claim. Preserve this gap and the closure/write allowances. They do not damage
the independent native-service measurement. Full aggregate CPU work is unmeasured.

Runner self and reaped-child RSS maxima are each629612544 bytes, separate maxima rather than
a simultaneous sum. Scratch peak and H remain unmeasured, so `resources_unmeasured` stays true.
Blocked synthetic scratch cleanup in the CM record also remains unresolved; no bypass occurred.
No engineering-scope §4 machinery is added by this result; implementation stayed within §5
budgets. This evidence publication changes no source, card, arm or scientific exposure.

## 5. Reproducible descriptive reduction

[`run_scores.csv`](own_command_mean_b07_20260908_run01/run_scores.csv) has only two final
endpoint rows, each already aggregated over four conditions. The card supplies their paired
seed127 training unit. The existing scientific-tools command was:

```text
python .agents/skills/hmasd-scientific-tools/scripts/summarize_runs.py docs/research/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07_20260908_run01/run_scores.csv --paired --baseline DIRECT_MEAN --out docs/research/candidates/degraded_incumbent_shadow_handover/own_command_mean_b07_20260908_run01/run_summary.json
```

It reports one paired difference−135.25 and null sample SD, without a CI or significance
classification. [`dm_analysis.json`](own_command_mean_b07_20260908_run01/dm_analysis.json)
retains independently recomputed condition/initial/native companions and receipt checks.
No condition bootstrap, seed exclusion, best-checkpoint selection or replay was performed.
