# EOCIV-B10 receiver-credit frozen-score exposure curve — result evidence

Date: 2026-09-04  
Direction: `eociv_lite`  
Object: `EOCIV-B10-RECEIVER-CREDIT-FROZEN-SCORE-EXPOSURE-CURVE`  
Evidence class / claim ceiling: **B / EXPLORE**, fixed-vector cumulative Adam exposure on the
declared three-initialization, three-profile, eight-root EOCIV population only  
Status: **`VALID_COMPLETE`**  
Result branch: **`B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED`**

This is the E0-format record of the sole full invocation of the prospectively frozen B10 card. The
complete 72-cell, seven-endpoint result and all 96 optimizer-step rows are retained in
`EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_RESULT.json`. Its values and ordering are an
LF-normalized copy of the runtime `summary.json`; the runtime source was 210,569 bytes with SHA-256
`f99edcb85f3314d4200d68c50e21814d324793fc604e70663255709577ce4dd5`.

## 1. Launch, implementation, and review receipts

| Fact | Direct observation |
| --- | --- |
| Launch implementation SHA | `6fece58293f7e1f02ad678adcd8321132c415193` |
| Equivalent implementation integrated on DM branch | `d745bbb72` |
| CM branch | `codex/cm/eociv-b10-frozen-score-20260904`, pushed and clean |
| Run root | `temp/directions/eociv_lite/exp/b10_20260904_01/` in the CM worktree |
| Detached process | hidden PID `17980`; exactly one full launch |
| Exit / logs | exit `0`; stdout is the 47-byte branch line; stderr is empty |
| Admission time | `2026-09-04T13:02:54.900931Z` |
| Available memory | physical = effective = `4,927,365,120` bytes; required `4,294,967,296` |
| Process time | wall `51.32498520001536 s`; CPU `49.984375 s` under the `300 s` cap |
| Peak RSS | `276,660,224` bytes; `resources_unmeasured=false` |
| Boundary observations | `1,044` episode boundaries and `96` Adam-step boundaries |
| Engineering scope | implementation added no §4 item; the one carded static manifest preceded implementation |
| Scope budgets | 782 production physical lines; 46-line runner; conservative orchestration `208/703 = 29.59%`; no §5 breach |

Exact invocation:

```text
C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe
C:\Projects\HMASD-worktrees\cm-eociv-b10-frozen-score-20260904\scripts\run_eociv_b10_receiver_credit_frozen_score_exposure_curve.py
--mode full --seed 991001
--run-root C:\Projects\HMASD-worktrees\cm-eociv-b10-frozen-score-20260904\temp\directions\eociv_lite\exp\b10_20260904_01
```

The post-edit suite reported `6 passed in 17.94s`; the final prelaunch suite reported
`6 passed in 16.87s`. One real-host smoke reported `SMOKE_COMPLETE`, explicitly
`NONE / SMOKE_ONLY`, `result_bearing=false` and `scientific_polarity=null`; it executed 26 episodes,
1,248 transitions and 32 Adam steps and is not part of this B result. Independent review initially
found smoke evidence mislabelling and an unrequested wall-per-Adam derived field. Both were removed
before commit; follow-up review reported no material finding.

## 2. Counts and common-information integrity

| Quantity | Card | Observed |
| --- | ---: | ---: |
| Collection episodes | 36 | 36 |
| Evaluation episodes | 1,008 | 1,008 |
| Total episodes | 1,044 | 1,044 |
| Environment transitions | 50,112 | 50,112 |
| Policy calls | 50,112 | 50,112 |
| Actor optimizer calls | 96 | 96 (`48` receiver, `48` source) |
| Initial gradient computations | 6 | 6 |
| Gradient recomputations | 0 | 0 |
| Critic/value-gradient/global-clip calls | 0 | 0 |
| Retry/rescue/search/sweep/checkpoint selection | 0 | 0 |
| Cells | 72 | 72 |
| Optimizer-step rows | 96 | 96 |
| Branch initial/empty-Adam facts | 6 | 6 |

`common_trajectory_and_complete_score_identity=true`. For every initialization, the summary records
12 common trajectories, 288 ordered score terms, one complete score-tensor computation per stored
trajectory, GAE computed once, both gradients computed before mutation, and the same complete tensor
contracted for the receiver and authenticated distinct-source branches. Every branch began at the
unchanged actor with a separate empty Adam instance. All 96 rows retain the same fixed gradient
before and after each step, the expected optimizer step, finite displacement and unchanged value
parameters. Counts of bad fixed-gradient, value, optimizer-step and initial-state facts are all
zero. Every cell records matched held-out root, shock, lifecycle, action noise and boundaries.

## 3. Actual exposure

| init | endpoint | receiver L2 / init ratio | source L2 / init ratio |
| --- | --- | ---: | ---: |
| A0 / 990031 | 1 | `0.00681463905971524 / 0.0006808181628451928` | `0.006489571893504928 / 0.0006483422490130309` |
| A0 / 990031 | 4 | `0.02725855871409308 / 0.0027232728986694345` | `0.02595829281528251 / 0.00259336951968175` |
| A0 / 990031 | 16 | `0.1090342282887586 / 0.010893090938538701` | `0.10383317634083866 / 0.010373478586216518` |
| A1 / 990032 | 1 | `0.00681467091246623 / 0.0008410038291636608` | `0.006599898906678764 / 0.0008144986491506393` |
| A1 / 990032 | 4 | `0.027258685361562986 / 0.0033640155278966306` | `0.026399597785734946 / 0.003257994863048878` |
| A1 / 990032 | 16 | `0.109034749410196 / 0.013456063094423043` | `0.105598381967379 / 0.013031978319832433` |
| A2 / 990033 | 1 | `0.006814632937823418 / 0.0007375832556807186` | `0.006600621268441052 / 0.0007144196568050425` |
| A2 / 990033 | 4 | `0.027258529579574732 / 0.0029503327876664095` | `0.026402486090910886 / 0.0028576787373112587` |
| A2 / 990033 | 16 | `0.10903409765043666 / 0.011801328913675139` | `0.1056099390711097 / 0.011430714376406501` |

All receiver endpoints remain just below the prospective triangle bound
`0.006814690014960328 * m`; source endpoints are slightly smaller. The intervention therefore
delivered the intended approximately 16-fold displacement rather than reproducing the B9R1
one-step exposure.

## 4. Exposure-curve observables

Global native observables:

| endpoint m | phi_R | phi_S | Delta_R | J | R-v0 | R-vS | S-v0 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.020333144529454963 | 0.019925779196482682 | -0.00014660499981922112 | 0.0004073653329722825 | -0.0004184196113929137 | 0.00021190148144162982 | -0.0006303210928345435 |
| 4 | 0.019865986233807767 | 0.018304302778547426 | -0.0006137632954664215 | 0.0015616834552603393 | -0.001665247154235373 | 0.0007750829423438144 | -0.0024403300965791875 |
| 16 | 0.018229932370226708 | 0.013320428783889414 | -0.0022498171590474747 | 0.0049095035863372955 | -0.006511830807355812 | 0.00179746069486719 | -0.008309291502223003 |

The unchanged global `phi_0` is `0.020479749529274185`. With exposure, relative `J` increases,
but `Delta_R` and receiver absolute CORRECT reward become progressively more negative. The source
arm is harmed more strongly, so positive global `R-vS` does not establish receiver value.

Terminal initialization means:

| init | phi_0 | phi_R16 | phi_S16 | Delta_R16 | J_16 | R16-v0 | R16-vS | S16-v0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A0 | 0.06442254079112526 | 0.057587997957901794 | 0.0643499465228872 | -0.006834542833223471 | -0.006761948564985405 | -0.012252552892108992 | -0.007552520461797957 | -0.004700032430311036 |
| A1 | -0.0018291511148685203 | -0.0009716891876432435 | -0.009849714587987444 | 0.0008574619272252765 | 0.0088780254003442 | 0.00002192872138378768 | 0.0015495347972195293 | -0.0015276060758357421 |
| A2 | -0.0011541410884341845 | -0.001926511659578416 | -0.014538945583231504 | -0.0007723705711442304 | 0.01261243392365309 | -0.00730486825134223 | 0.011395367749179998 | -0.018700236000522227 |

A1 alone meets the terminal initialization-level sign and absolute guards. A0 reverses both
`Delta_R16` and `J_16`; A2 has large positive relative `J_16` but negative `Delta_R16` and
receiver absolute CORRECT harm.

Every leave-one robustness aggregate retains negative `Delta_R16`:

| omitted unit | Delta_R16 | J_16 | R16-v0 | R16-vS |
| --- | ---: | ---: | ---: | ---: |
| profile `train_4_3_6_5` | -0.0014987310650824142 | 0.005320622830392964 | -0.005256229192309023 | 0.0022134013874327237 |
| profile `train_5_3_7_6` | -0.002098728148576352 | 0.00471099644391072 | -0.007320595286462586 | 0.001561860368079018 |
| profile `train_6_4_8_6` | -0.003151992263483659 | 0.0046968914847082014 | -0.006958667943295825 | 0.001617120329089828 |
| root 991001 | -0.0018860046199902425 | 0.005419755034945469 | -0.005603558839675696 | 0.002424934865757258 |
| root 991002 | -0.0024396562237195534 | 0.005161699211864439 | -0.0068025147938023155 | 0.0023581596549331297 |
| root 991003 | -0.0021327405762049958 | 0.0044685518456367805 | -0.006655700474686316 | 0.000841430455786403 |
| root 991004 | -0.0021330011036481524 | 0.004790723909089144 | -0.007129939355961276 | 0.0023057879182741803 |
| root 991005 | -0.002221461845253668 | 0.005275964387022394 | -0.006384522600900274 | 0.0020369319940887706 |
| root 991006 | -0.0025228408996877632 | 0.004983361790805231 | -0.006708939315514453 | 0.0017457463741334905 |
| root 991007 | -0.0023188936910706246 | 0.00426620769949192 | -0.006352165947579844 | 0.0009175270517244981 |
| root 991008 | -0.0023439383128047993 | 0.004909764811842986 | -0.006457305130726323 | 0.0017491672442397905 |

Cell signs remain heterogeneous. At `m=16`, positive/zero/negative counts are
`Delta_R 33/2/37`, `J 50/2/20`, `R-v0 23/2/47`, and `R-vS 37/2/33`. The complete cell-level
`Y`, `phi`, `Delta`, `J` and absolute comparisons at `m=1,4,16` are retained in the durable JSON;
no cell was omitted from branch computation.

## 5. Frozen rule applied verbatim

1. `INVALID_ATTEMPT`: any common-integrity failure; nonfinite required observable; missing common
   trajectory/complete-score identity; learner-side instrumentation failure; initial-state,
   count, fixed-gradient, step-receipt, value-invariance or endpoint mismatch; or CPU-cap stop.
2. `B10_FIXED_SCORE_EXPOSURE_EDGE`: at `m=16`, `J_16 > 0` and `Delta_R16 > 0` globally, in each
   initialization mean, every leave-one-profile and every leave-one-root aggregate; `R16-v0 >= 0`
   and `R16-vS >= 0` globally and separately for every initialization; and all required identity,
   count, observable and displacement records complete and finite.
3. `B10_FIXED_SCORE_EXPOSURE_RESCUE_NOT_SUPPORTED`: every other valid complete result.

Branch 1 does not apply: the implementation, resource, identity, instrumentation, count, fixed
gradient, optimizer, value, cell and exposure records all pass. Branch 2 fails independently because
global `Delta_R16 < 0`, A0 and A2 `Delta_R16 < 0`, A0 `J_16 < 0`, every leave-one `Delta_R16 < 0`,
global `R16-v0 < 0`, A0/A2 `R16-v0 < 0`, and A0 `R16-vS < 0`. Therefore branch 3 applies. The
mandatory `m=1` and `m=4` rows were retained but did not select or rescue the result.

## 6. Bounded reading

Direct observation: increasing fixed receiver-gradient exposure from one to 16 Adam steps did not
rescue a robust or absolute native semantic edge. It increased the global receiver-versus-source
contrast, but the receiver's own `Delta_R` and absolute CORRECT reward worsened with exposure, while
the source arm worsened even more. A1 shows a small absolute and strong relative terminal benefit;
A0 reverses the relative sign; A2 is relative-only with substantial source harm.

Strongest support for receiver-credit value is the A1 terminal mean, which satisfies positive
`Delta_R16`, `J_16`, `R16-v0` and `R16-vS`. Strongest contradiction is the negative global and every
leave-one `Delta_R16`, negative global absolute receiver effect, A0 reversal and A2 absolute harm.

The maximum supported negative conclusion is exactly: **the prospectively bounded fixed-vector
exposure range did not rescue the B9R1 receiver-addressed effect.** This does not test endogenous or
on-policy sustained learning, establish receiver-local mediation, imply general receiver-content
harm or source superiority, transfer polarity to CBSC, support C or Portfolio action, or close
`eociv_lite` generally.

## 7. Evidence paths

- Card:
  `docs/research/candidates/eociv_lite/EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_SCIENCE_CARD_20260904.md`
- Complete durable result:
  `docs/research/candidates/eociv_lite/EOCIV_B10_RECEIVER_CREDIT_FROZEN_SCORE_EXPOSURE_CURVE_RESULT.json`
- Runtime summary:
  `temp/directions/eociv_lite/exp/b10_20260904_01/summary.json`
- Admission:
  `temp/directions/eociv_lite/exp/b10_20260904_01/resource_admission.json`
- Implementation launch SHA: `6fece58293f7e1f02ad678adcd8321132c415193`

