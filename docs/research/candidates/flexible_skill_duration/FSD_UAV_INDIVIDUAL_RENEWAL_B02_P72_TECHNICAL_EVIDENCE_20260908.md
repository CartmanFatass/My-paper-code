# FSD UAV B02 P72 technical evidence

## Source acceptance

The explicit B02 binding is implemented and technically accepted. Contract: [five-item handoff §§1–5](FSD_UAV_INDIVIDUAL_RENEWAL_B02_P72_CM_HANDOFF_20260908.md) and [B02 card §§2–4](FSD_UAV_INDIVIDUAL_RENEWAL_B02_SCIENCE_CARD_20260908.md). Authoring checkout `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`, clean start `42693cbdafb3143d012e2b78e160bedca439fff4`; complete starting science is unchanged from `52609ba8438836de9805014dc783e818010dcc06` / accepted B01 `ca36e2f941d6c4d4e996a9bd919378af44ea0e93`.

Shared runner `scripts/run_fsd_uav_individual_renewal_b01.py` now passes explicit keyword values through summary/manifest, training process RNG/private lanes/config, evaluator construction/RNG/private lanes/config, and pair expectations. New `scripts/run_fsd_uav_individual_renewal_b02.py` selects object/card B02 and training770603/evaluation780603. It forwards ordinary argv to the same loop. B01 defaults remain770503/780503 and retain their original identity after B02 runs. Selected card identity is checked alongside the existing selected object/seed checks, so two old card labels do not supply a B02 pairing. Launch SHA remains reported metadata, not an equality predicate.

No module constants are rebound; no loop, model, environment or configuration implementation is cloned. Existing training collection, actual actions/step metadata, raw rewards, terminal storage followed by reset of both inputs, updates/credit/normalizers, evaluator synchronization/RNG preservation and primary publication remain unchanged. Underlying learner/environment/config/E0/admission/platform helpers and original B01 fake tests are read-only and unchanged. Engineering scope §4: none per B02 card §4. Shared runner428 lines; thin wrapper16 lines; non-test diff +45/−25, comfortably within600/2000 budgets. New B02 tests124 lines.

## Focused checks

Exact combined affected command, once, on the fixed scientific Python:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/uav_b02_p72_binding_20260908 tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b02/test_binding.py
```

Observed output:

```text
..........................................                               [100%]
42 passed, 14 warnings in 7.67s
pytest_exit=0; complete_check_wall_seconds=8.9337842
syntax_exit=0; syntax_wall_seconds=0.0777327
```

All3 changed/new Python files passed in-memory `compile(source, path, 'exec')`, avoiding bytecode output. Combined check process wall9.0115169s <300s. `git diff --check` passed. Warnings are existing matplotlib/pyparsing deprecations. `PYTHONDONTWRITEBYTECODE=1` and disabled pytest cache kept generated artifacts within the exact invocation scratch. No suite rerun, real model/environment, source fixture, smoke, pilot or scientific invocation occurred.

The9 new cases exercise full fake B02 D0/I publication then full fake B01 D0/I in the same interpreter; actual Python/NumPy/Torch constructor draws and RNG preservation; private lane/config consumers; native6U/H arithmetic; selected object/card/seed and evaluator-lane expectations; changed document SHA remaining acceptable; and old B01 companion rejection while retaining the B02 own endpoint. Existing33 cases retain the original collector/config/reset/primary/failure coverage. The fake helper loads the identical shared source under its isolated test name; the B02 wrapper delegates to that fake seam. No production global rebinding follows.

## Independent review

Reused reviewer `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47/rv_ah_fsd_b03_p47` inspected only this changed RNG/binding/comparison boundary. **No material finding.** Its static comparison confirms only the six assigned definitions changed; collection/config/scaling/finite/publication helpers and the old B01 tests are unchanged. It verified explicit propagation, rejection of old companions, later B01 defaults, no loop clone or SHA predicate, scope and budgets. Reviewer inspected coverage and CM output without a test/model/host execution. Fake checks establish binding conformance; B02 native outcome and complete runtime remain unmeasured.

## Cost/publication coverage and next phase

Per-arm cost projection reuses same-method P70 complete walls D0471.89s / I1221.49s and historical scenarios1617.82s /16178.2s. Work stays five16×500 training rollouts and one32×500 final endpoint per arm; caps remain D03600/I18000/sum21600s. References are planning evidence, not guaranteed current bounds. No source fixture, pilot or multiplier change is required or added.

Post-learner publication coverage: the combined fake suite exercises complete new B02 D0/I publication and unchanged B01 publication afterward; damaged/old companions preserve own-arm facts. Later real collection will distinguish endpoint sampled counters from unmeasured duration statistics in empty evaluation storage buffers, and sum wall from critical path/aggregate CPU. No performance or treatment-activity acceptance threshold is introduced.

Future production argv, only after DM source acceptance, from the accepted-source detached remote checkout:

```text
/home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b02.py --arm D0 --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/D0
/home/wu/.venvs/hmasd/bin/python scripts/run_fsd_uav_individual_renewal_b02.py --arm I --output-root temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/I --d0-summary temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/D0/summary.json
```

DM source acceptance precedes scientific submission under this P72 handoff; existing P72 then authorizes one D0→I batch without another Root request. Literal cwd/source/handles/admission/payloads will be committed and staged before each submission. Fresh on-node physical/effective≥4GiB admission and outer3600/18000s caps include imports, learning and closed publication with zero grace/retry/resume. Same CM remains sole observer/collector; DM owns science/owner/audit/Root relay. P70 evidence and old blocked P69 scratch are untouched.

P72 scratch cleanup: after retaining check output above, the exact invocation directory was resolved under this checkout's direction test root. Automatic approval review rejected native PowerShell `Remove-Item -LiteralPath` for that exact P72 scratch with “blocked by policy”; no deletion occurred and no bypass followed. The ignored P72 scratch/checks.log remains. This housekeeping limitation does not alter source or fake-check acceptance. The separately blocked P69 scratch was never targeted.

## P72 exact execution binding

DM source acceptance was published at `f95ebcb037865bd0020dfc0e14b3e09302ba4562` before this phase. Accepted scientific source is exactly `08199a932671d9bacdbe4eb0bfebab38c37fca1f`. Configured node/interpreter/supervisor are unchanged from the handoff. Detached execution cwd `/home/wu/hmasd-worktrees/fsd-uav-b02-p72-08199a932` was created at that exact SHA with sparse checkout disabled. Actual source and staged LF syntax/digest checks follow before submission; no fake suite is repeated.

Literal inputs are the only explicitly tracked files under `temp/directions/flexible_skill_duration/exp/uav_b02_p72_control_20260908`: `D0.sh` and `I.sh`. Remaining control artifacts stay scoped/ignored. Remote staging `/home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908`. Scripts change to the exact cwd and join canonical fresh on-node admit-memory directly with `&&` to the exact B02 argv above. Admission receipts remain outside the scientific roots. Scientific outputs are the new B02 root; I reads only its original B02 D0 summary.

| LF input | SHA256 |
| --- | --- |
| D0.sh | bbb490d21391dc839c9a234d4651446398588f15616b50740bd9f2a6e39f40f8 |
| I.sh | c51de29af52b338b329d622e981d7df94ea90262d1b8ef2305c618d6f7f5f515 |

Literal supervisor payloads, sequential D0 then I after terminal collection; at most one accepted submission each:

```text
/usr/local/bin/agent-task run fsd_uav_b02_p72_D0_08199a932 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/D0_process_time.txt /usr/bin/timeout --signal=KILL 3600s /bin/bash /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/D0.sh'
/usr/local/bin/agent-task run fsd_uav_b02_p72_I_08199a932 '/usr/bin/time -f elapsed_seconds=%e,peak_rss_kib=%M,user_seconds=%U,system_seconds=%S,exit_status=%x -o /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/I_process_time.txt /usr/bin/timeout --signal=KILL 18000s /bin/bash /home/wu/hmasd-inputs/fsd-uav-b02-p72-20260908/I.sh'
```

Outer timeouts cover the whole script from adjacent admission through imports/setup/learning/own evaluation/closed pair publication, with KILL and zero grace. Time/RSS and minimal aggregate user+system CPU accounting remain outside scientific output roots. Supervisor directories `/home/wu/.agent-tasks/<handle>/` preserve actual command, log, status, PID/start and exit facts. Acceptance, fresh admission and scientific execution remain separate observations. Both handles are proposed, not accepted, at this input-binding boundary. No retry/resume, additional scientific endpoint, source repair or old-data rescue is allocated.

Before D0 submission: literal-input commit `3b872c848` was pushed; each script was exported from its committed Git blob and staged via SCP. Actual remote HEAD is08199a932671d9bacdbe4eb0bfebab38c37fca1f, tracked checkout clean. All2111 actual tracked Python files match their Git blob bytes, including configs/config_1.py, B01/B02/E0, agent/UAV/adapter and both canonical preflight/platform helpers. Configured host LAPTOP-U9TDKC8A and Python3.10.21; installed metadata NumPy1.26.3/Torch2.7.0+cu118/Gymnasium1.0.0/PettingZoo1.24.3/SB3 2.6.0. No scientific imports or constructors were used for source verification. Staged D0/I438/542 bytes, zero CR, hashes above match, bash-n exit0. Python/time/timeout/supervisor executable; both proposed handle roots and the B02 scientific parent absent. Raw source_verification.json is retained in remote staging and local control. This is source/input observation, not memory admission or supervisor acceptance.

D0 accepted once at2026-09-09T06:30:06Z as `fsd_uav_b02_p72_D0_08199a932`, PID3029317, running/null exit/tmux active at20s. Fresh adjacent on-node admission assessed06:30:06.778598Z passed both physical/effective floors: available15633887232 bytes, minimum4294967296, no failure reasons. Control D0_launch.stdout retains supervisor acceptance; remote D0_admission.json is the sole original receipt. CM notified DM and retains sole observation. I remains unsubmitted pending this exact D0's terminal fact; no parallel observer or fresh scientific check was added.

D0 terminal at2026-09-09T06:37:58Z: finished/exit0, complete wall471.50s, peakRSS1659568KiB, user1840.09s+system17.63s. Remote/local archive SHA256 `f63c968552da6c9cd287bf0be2c80ae3a74936ec2403e1b863c3fd50a31a5638` matches; original summary hash `6d84eaf98151954e0ad21fab301123d5cf0b33cbc17ade05eb9f50de83f08891`. Archive/output/supervisor/admission/time/readback files retained under P72 control. Own-arm readback passed source/object/card and actual770603/780603 config/lane bindings,40000 stored transitions/80 episodes/5 updates,16000 scoring steps/32 endpoints,2 models/1 start/0 loads, no evaluator updates, finite numbers and6U/500. Mean rawU40.45100240104888; meanJ0.4854120288125866. No shared integrity error found. This original B02 D0 remains the I comparator; P70 was not copied or read by the scientific runner. I remains unsubmitted at this terminal/readback record and uses its unchanged committed input with a fresh adjacent admission next.

I accepted once (supervisor start2026-09-09T06:40:19Z) as `fsd_uav_b02_p72_I_08199a932`, PID3030457; running/null exit/tmux active at19s. Fresh on-node admission assessed06:40:20.027389Z passed physical/effective available15635578880 bytes against4294967296, with no failure reasons. Original I_admission.json and I_launch.stdout retained; no reused receipt or comparator. CM sent the accepted-handle fact to DM and remains sole observer. The allocation now has exactly one accepted D0 and one accepted I; no further scientific submission is authorized.


## P72 complete terminal collection

**Technical acceptance: PASS for both original arms and their complete new B02 pair.** Exactly one accepted supervisor submission per arm; no live process, retry, extra evaluator or source rescue remains. I finished/exit0 at2026-09-09T07:01:57Z. This accepts source/result conformance; scientific interpretation and the two-instance P70/B02 intake remain with DM.

| Arm | Complete wall s | Peak RSS KiB | User CPU s | System CPU s |
| --- | ---: | ---: | ---: | ---: |
| D0 | 471.50 | 1659568 | 1840.09 | 17.63 |
| I | 1297.28 | 1610200 | 5128.39 | 30.74 |

Sum complete wall **1768.78s**; aggregate CPU **7016.85s**. Study critical path **1911s** at supervisor1s resolution (D0 start06:30:06Z to I terminal07:01:57Z), including the between-arm collection/binding gap. Complete external timings include startup/shutdown; I's earlier summary publication timestamp1255.4191s is not its complete wall1297.28s. Both arms and sum fit original3600/18000/21600s caps; neither arm reaches the UAV43200s investigation threshold. Fresh original admissions passed separately; process peak RSS does not imply continuous system-free-memory measurement.

Both complete output directories and supervisor files were archived after terminal exit and copied to the P72 control root named above. Archive SHA256 matches between remote and local bytes:

| Arm | Archive SHA256 | Original summary SHA256 |
| --- | --- | --- |
| D0 | `f63c968552da6c9cd287bf0be2c80ae3a74936ec2403e1b863c3fd50a31a5638` | `6d84eaf98151954e0ad21fab301123d5cf0b33cbc17ade05eb9f50de83f08891` |
| I | `802529e4a523e451bab6156bcd0b1325bf228adb7c67f09a417101447f769fc2` | `ce88a406fee0f0eb2784af8650be74a458460df36ca04276f9b0ed2c14f95573` |

Raw artifacts: `D0_evidence.tar`, `I_evidence.tar`, original admission/time files, launch stdout and `source_verification.json` in `temp/directions/flexible_skill_duration/exp/uav_b02_p72_control_20260908`. Extracted archives preserve nested `temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b02_770603/{D0,I}` and `.agent-tasks/<handle>` paths within that control directory. `collect_readback.py` reads only these archived bytes; `pair_readback.json` and `resource_readback.json` retain its arithmetic/activity and resource readbacks. D0 summary hash is unchanged after I; P70 data never supplies a B02 companion. Remote tracked source remained clean after both runs.

### Acceptance coverage and limits

Both manifest/summary object/card/source bindings, actual770603/780603 private lane/config seeds, CPU4/FP32, actual exits and original physical/effective admission receipts passed readback. Both arms have40000 collected/stored transitions,80 episodes,5 updates,2500 training batch calls,16000 scoring steps,32 final episodes,500 evaluation batch calls,2 model constructions,1 training start and0 checkpoint loads. Five JSONL rows match each summary and have8000 stored transitions/16 episodes apiece. Final endpoint IDs0–31 each run500 steps after update5 with0 evaluation optimizer calls. Learner/evaluator configurations match across arms except the specified individual cost (.25 versus Infinity), with team Infinity, k/caps10, latent6/6, ageoff/delta1. Selected source tests cover actual reset/storage/RNG behavior; collection does not reconstruct unseen trajectories or rerun learning.

Scientific finiteness, cost-only Infinity metadata, optimizer delta sums, raw U/native6U/500, native reward components, all32 paired differences, mean/sample SD/conditional SE and frozen inclusive MEI branch passed artifact-only checks. No extra scientific invocation, model/host construction, test rerun or diagnostic experiment was introduced. Missing evaluation storage segments/rows_M measure no endpoint duration distribution: evaluation does not store or update; these empty statistics are **unmeasured duration**, not zero-duration native skills. Decision/cause/token-switch counters remain separate observations.

### Primary and native components

D0 mean J **0.4854120288125866**; I mean J **0.45009930351470057**. I−D0 mean **-0.035312725297886094**, sample SD **0.070843557299347326**, conditional SE **0.012523489942436556**. Frozen runner/card reading **`opposite_sign`**. Independent training unit: one new matched pair; endpoint SE does not estimate training-seed uncertainty. No broad scientific disposition follows from CM acceptance.

| Arm | Mean raw U | Coverage | Quality | Altitude penalty | Native total |
| --- | ---: | ---: | ---: | ---: | ---: |
| D0 | 40.451002401048882 | 0.62218999999999958 | 0.18192697255677431 | 0.004699062954445523 | 0.48541202881258672 |
| I | 37.50827529289171 | 0.56959125000000066 | 0.18367311867020852 | 0.0037165070863620468 | 0.45009930351470051 |

### Training activity and parameter exposure

Rollouts below use1–5 display numbering. Each has800 team decisions (16 reset/784 team-cap causes),0 team gaps/individual-cap causes,800 team segments of length10 totaling8000 steps. Individual segments total48000 agent-steps per rollout. Joint rows_M differs from individual segment count.

| Arm/rollout | Individual sampled | Individual gaps | Token switches | Joint rows_M | Segment mean | Min/max |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| D0/1 | 4800 | 0 | 3866 | 800 | 10 | 10/10 |
| D0/2 | 4800 | 0 | 3947 | 800 | 10 | 10/10 |
| D0/3 | 4800 | 0 | 3987 | 800 | 10 | 10/10 |
| D0/4 | 4800 | 0 | 3977 | 800 | 10 | 10/10 |
| D0/5 | 4800 | 0 | 4007 | 800 | 10 | 10/10 |
| I/1 | 16949 | 12149 | 13653 | 6192 | 2.83202548823 | 1/10 |
| I/2 | 17546 | 12746 | 14195 | 6208 | 2.73566624872 | 1/10 |
| I/3 | 18535 | 13735 | 15149 | 6552 | 2.5896951713 | 1/10 |
| I/4 | 17660 | 12860 | 14348 | 6218 | 2.71800679502 | 1/10 |
| I/5 | 19071 | 14271 | 15590 | 6651 | 2.51691049237 | 1/10 |

Final evaluation per arm records1600 team decisions and9600 individual samples,32 reset/1568 team-cap causes,0 gap causes across32 episodes. Evaluation token-switch totals are D0760 and I1272. Training activity is not substituted for deterministic endpoint activity; neither requires an activity minimum.

| Arm | Group | Optimizer calls | Initial norm | Displacement update1 | Displacement update5 |
| --- | --- | ---: | ---: | ---: | ---: |
| D0 | coordinator | 525 | 104.790455898 | 0.0250319364369 | 0.0433575116847 |
| D0 | discoverer_actor | 11250 | 41.0410861902 | 0.155503980781 | 0.406697345453 |
| D0 | discoverer_critic | 11250 | 41.4520220456 | 0.0730923347722 | 0.156561889297 |
| D0 | team_discriminator | 75 | 50.4777179888 | 0.00992246153654 | 0.0259595804189 |
| D0 | individual_discriminator | 300 | 55.0999095374 | 0.0244798208668 | 0.0516547626079 |
| I | coordinator | 3765 | 104.790455898 | 0.0656054887017 | 0.14762830773 |
| I | discoverer_actor | 11250 | 41.0410861902 | 0.155803355565 | 0.427071413137 |
| I | discoverer_critic | 11250 | 41.4520220456 | 0.0729782446235 | 0.156843372645 |
| I | team_discriminator | 75 | 50.4777179888 | 0.0108194785019 | 0.0272077126653 |
| I | individual_discriminator | 300 | 55.0999095374 | 0.0235781691315 | 0.044707247635 |

### Complete ordered primary vectors

Episode IDs0–31 use evaluation lane780603+ID. Values are emitted from the collected readback, without endpoint selection.

| ID | D0 raw U | D0 native J | I raw U | I native J | I−D0 native J |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 43.175892296456333 | 0.51811070755747601 | 39.098368989140077 | 0.46918042786968089 | -0.04893027968779512 |
| 1 | 42.746238011591153 | 0.51295485613909386 | 40.238398576938721 | 0.48286078292326468 | -0.030094073215829187 |
| 2 | 37.051757507826913 | 0.44462109009392292 | 37.032115674458701 | 0.44438538809350436 | -0.00023570200041855838 |
| 3 | 40.632579562913939 | 0.48759095475496722 | 39.502807753687648 | 0.4740336930442518 | -0.013557261710715418 |
| 4 | 31.77450632271492 | 0.38129407587257902 | 38.406481572683681 | 0.46087777887220421 | 0.079583702999625194 |
| 5 | 39.250100560546166 | 0.47100120672655393 | 36.870915586345276 | 0.44245098703614333 | -0.028550219690410605 |
| 6 | 33.950266007050736 | 0.40740319208460879 | 29.206176654176975 | 0.35047411985012372 | -0.056929072234485067 |
| 7 | 42.10061554344388 | 0.50520738652132657 | 44.509457941590711 | 0.53411349529908858 | 0.028906108777762007 |
| 8 | 30.249354026636929 | 0.36299224831964316 | 33.467415821049137 | 0.40160898985258964 | 0.038616741532946475 |
| 9 | 42.135464233305747 | 0.50562557079966897 | 42.247897312026446 | 0.50697476774431727 | 0.001349196944648301 |
| 10 | 48.874345262628161 | 0.58649214315153786 | 39.873144882446695 | 0.47847773858936032 | -0.10801440456217754 |
| 11 | 37.995489196099307 | 0.45594587035319173 | 44.553355393009028 | 0.53464026471610826 | 0.078694394362916531 |
| 12 | 44.917154867341296 | 0.53900585840809545 | 30.06716494539609 | 0.36080597934475311 | -0.17819987906334234 |
| 13 | 38.745757073259924 | 0.46494908487911907 | 36.384104026377159 | 0.43660924831652592 | -0.028339836562593146 |
| 14 | 44.688591549698927 | 0.53626309859638721 | 40.644293314145123 | 0.48773151976974144 | -0.048531578826645771 |
| 15 | 39.798949793615115 | 0.47758739752338136 | 37.51813515739078 | 0.45021762188868936 | -0.027369775634692006 |
| 16 | 45.655163083451704 | 0.54786195700142049 | 39.518527783025228 | 0.47422233339630271 | -0.073639623605117777 |
| 17 | 35.551162762866497 | 0.42661395315439798 | 36.55662331632184 | 0.43867947979586208 | 0.012065526641464097 |
| 18 | 34.031439669147105 | 0.40837727602976526 | 36.40505357699093 | 0.43686064292389121 | 0.02848336689412595 |
| 19 | 36.729848182833166 | 0.44075817819399798 | 36.518373223562882 | 0.43822047868275454 | -0.0025376995112434408 |
| 20 | 43.296758509600856 | 0.51956110211521023 | 34.553989559548434 | 0.41464787471458125 | -0.10491322740062897 |
| 21 | 33.359920533783374 | 0.4003190464054005 | 39.096983101308169 | 0.46916379721569801 | 0.068844750810297506 |
| 22 | 37.794000909251011 | 0.45352801091101214 | 33.252531940777963 | 0.39903038328933554 | -0.054497627621676592 |
| 23 | 40.812255502532281 | 0.48974706603038737 | 19.684531849876507 | 0.23621438219851809 | -0.25353268383186928 |
| 24 | 32.27136481960482 | 0.38725637783525779 | 27.773303986313628 | 0.33327964783576353 | -0.053976729999494266 |
| 25 | 45.722868872129851 | 0.5486744264655582 | 40.256164973035602 | 0.48307397967642723 | -0.065600446789130962 |
| 26 | 46.691501249224785 | 0.56029801499069742 | 43.461027241793751 | 0.52153232690152507 | -0.038765688089172357 |
| 27 | 42.080879583196058 | 0.50497055499835264 | 43.433061615656385 | 0.52119673938787658 | 0.016226184389523945 |
| 28 | 44.894474147408232 | 0.53873368976889879 | 32.470216539623436 | 0.38964259847548122 | -0.14909109129341758 |
| 29 | 48.530783601220747 | 0.58236940321464892 | 46.882290390869301 | 0.56258748469043163 | -0.01978191852421729 |
| 30 | 44.350868439507387 | 0.53221042127408857 | 40.434891047654169 | 0.48521869257185007 | -0.0469917287022385 |
| 31 | 44.571725152677097 | 0.5348607018321252 | 40.347005625314345 | 0.48416406750377211 | -0.050696634328353085 |

### Closeout

Both accepted handles are terminal and collection is complete; no technical result blocker remains. P70 evidence and both blocked scratch directories are preserved. No model/effort/config hot reload or live-source change occurred. CM releases the clean direction index after pushed evidence; DM owns all-outcome science intake/brief/audit, the two-instance descriptive summary and final Root relay, then the requested clean config input sync. Existing P72 authority contains no second new pair or scientific successor.

OWNER_DIRECT soft stop: this collection closeout is the final CM action. After committing and pushing this evidence, CM remains stopped; no next arm, seed, object, retry, resume or Pro request follows. DM owns the restart handoff and clean config sync.
