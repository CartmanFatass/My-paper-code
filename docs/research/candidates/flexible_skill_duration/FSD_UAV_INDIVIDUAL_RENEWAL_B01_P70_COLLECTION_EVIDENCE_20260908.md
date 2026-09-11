# FSD UAV B01 P70 technical collection

Technical owner: CM `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47`; scientific intake: DM `/root/dm_fsd_p47_resume`. [Execution evidence](FSD_UAV_INDIVIDUAL_RENEWAL_B01_P70_EXECUTION_EVIDENCE_20260908.md) fixes source, literal inputs, node/cwd/outputs, admission and accepted handles. Source `ca36e2f941d6c4d4e996a9bd919378af44ea0e93`; no scientific source changes or extra invocations. Complete B01 P70 allocation is one sequential D0/I pair.

**Complete technical acceptance: both original arms and their paired publication pass.** Exactly one accepted submission per arm; both finished with exit0. No remaining shared integrity error or live handle. This establishes implementation/result conformance, not broader scientific truth.

## Terminal and resource evidence

| Arm | Supervisor outcome | Complete wall s | Peak RSS KiB | User CPU s | System CPU s |
| --- | --- | ---: | ---: | ---: | ---: |
| D0 | finished, exit0 | 471.89 | 1610396 | 1844.48 | 15.18 |
| I | finished, exit0 | 1221.49 | 1623988 | 4829.98 | 32.63 |

D0 admission was fresh on the execution node, physical/effective available15615131648 bytes, both above4294967296. I independently passed with15640535040 bytes. D0 3600s/I18000s outer caps cover admission through closed-file publication. Time and peak RSS are measured by existing GNU time; its user+system counters supply aggregate CPU work, not wall. Measured study critical path is1817s at the supervisor timestamps’1s resolution (05:08:56Z D0 start to05:39:13Z I terminal), including the between-arm collection/staging gap. Sum of complete command walls is1693.38s; aggregate CPU is6722.27s (D01859.66s; I4862.61s). Each arm and summed wall fit3600/18000/21600s. Neither per-arm invocation reaches the UAV 43200s engineering-investigation threshold. Admission is a launch-time memory fact; peak process RSS is measured separately, not a continuous system-free-memory trace. No fallback, retry/resume, pilot, smoke or additional evaluator occurred.

D0 scientific output and supervisor files were archived after terminal exit. Remote/local archive SHA256 `4151ca1015db678fe1d8407f316360981ee5bbded941dfa5bb90d49760e54d47` matches. Control root in authoring checkout: `temp/directions/flexible_skill_duration/exp/uav_b01_p70_control_20260908`; archive D0_evidence.tar, admission/time files, launch stdout and D0_readback.json are retained there. Extracted paths preserve the remote relative `temp/directions/.../D0` and `.agent-tasks/fsd_uav_b01_p70_D0_ca36e2f94` layout. No output was fabricated or overwritten to complete a companion.

## Count, configuration and source acceptance

D0 local readback over collected JSON passed finite scientific numbers, exact source SHA/object/arm, numeric-cost configuration metadata, seeds770503/780503 and private lane lists, CPU4/FP32 boundaries, five complete original training JSONL rows matching summary rows, and all required counts. It has40000 collected/stored transitions,80 training episodes,5 update stages,2500 training batch calls,16000 scoring steps,32 final episodes,500 evaluation batch calls,2 model constructions,1 training start and0 checkpoint loads. Final evaluation is after update5 with32 ordered IDs,500 steps each and0 evaluation optimizer calls. Config consumers retain D0 Infinity/Infinity and dimensions16/32,6 UAVs/50 users,k/caps10,n_Z/n_z6,delta1,ageoff. The source’s actual reset/storage/evaluator/RNG behavior remains covered by P69 checks and independent review; collection checks recorded outcomes and source binding, without replaying learning or adding a full-trajectory census.

Endpoint buffer segments and rows_M are empty/zero because evaluation performs no transition storage or learner update. **Endpoint segment lengths are unmeasured by those buffer statistics**, not observed zero-duration native skills. Endpoint sampled-decision/cause/switch counts remain readable. Training segment records are measured before clearing each rollout buffer. Updates, actual optimizer calls, sampled decisions and changed tokens remain distinct.

## D0 own-arm facts

D0 mean raw U22.455079362317562; native J0.26946095234781076. All32 native scores equal6U/500. Native component means: coverage0.3257012499999996, quality0.1576304797918256, altitude penalty0.005819066589736964; `.7*coverage+.3*quality-altitude` equals the primary. No training reward scaling or component selection occurred.

D0 actual optimizer calls: coordinator525, discoverer actor11250, critic11250, team discriminator75, individual discriminator300. All five active parameter groups have finite, nonzero displacement from initialization; raw first/fifth update values remain in D0_readback.json and summary. Evaluation has1600 team decisions and9600 individual sampled decisions,0 individual gap causes, with612 total token switches across six UAVs. These counters do not impose treatment-activity or competence thresholds.

## Final I and pair readback

The collected I archive SHA256 `ca1edf76e003f1ef4391b5cf80e909285ad00edcf6d1e5bc4723de4c5adb7289` matches the remote archive. The original I admission receipt is retained as I_admission.json; no new admission or invocation was run during collection. Both original summary bytes match remote readback after I completion:

| Arm | Summary SHA256 |
| --- | --- |
| D0 | `c7b8f32ddfa949147a29c4b3847bf3ac07d388d0258bfe8fc1ec0acfff979906` |
| I | `e60fddb3e99719e1a7e760f7e05791d39c48df3b94d1f3a8204de3c46a3b8b0f` |

Final local `collect_readback.py` reads only the archived bytes; `pair_readback.json` retains its numerical output and per-rollout records, and `resource_readback.json` retains measured resource/clock arithmetic. All are under the control root named above. No scientific runner was imported or rerun. Checked both manifest/summary source bindings, actual supervisor exits and fresh original admissions, scientific finiteness with only cost Infinity metadata, five JSONL rows equal summary rows, exact lane/config/count/endpoint fields, all optimizer delta sums, and original reward-component/6U/500 identities. Paired32 differences, mean, sample SD(ddof1), conditional SE and inclusive±.01 branch agree with I's in-cap publication. The readback applies no new acceptance threshold to learning, parameter movement, treatment activity or sign. Remote tracked source remained clean after both arms.

I has the same prescribed training/evaluation counts as D0, own construction/config/seeds and0 evaluator updates. Its individual cost is.25 in both learner/evaluator; team cost remains Infinity. All other compared learner/evaluator configuration fields match the original D0. The independent training unit is one pair; conditional endpoint SE does not estimate training-seed uncertainty.

Native means: D0 **0.26946095234781076**, I **0.21979038918069888**. Paired I−D0 mean **-0.049670563167111874**, sample SD **0.13442151634285882**, conditional SE **0.023762591435853447**; runner/card branch **`opposite_sign`**. DM owns the scientific disposition and all-outcome intake; the original comparator and result are preserved.

| Arm | Coverage mean | Quality mean | Altitude penalty mean | Native reward mean |
| --- | ---: | ---: | ---: | ---: |
| D0 | 0.32570124999999961 | 0.1576304797918256 | 0.0058190665897369636 | 0.26946095234781076 |
| I | 0.34988499999999967 | 0.12905957852058067 | 0.063846984375475424 | 0.2197903891806989 |

## Activity and optimizer/exposure facts

Each training row has800 team decisions, including16 resets/784 team-cap causes, and0 team-gap/individual-cap causes. The following are recorded native counters, with rollout numbering1–5 for display. Joint rows_M differs from individual segment count.

| Arm/rollout | Individual sampled | Individual gap causes | Token switches | Joint rows_M | Individual segment mean | Individual segment min/max |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| D0/1 | 4800 | 0 | 3798 | 800 | 10 | 10/10 |
| D0/2 | 4800 | 0 | 3919 | 800 | 10 | 10/10 |
| D0/3 | 4800 | 0 | 3969 | 800 | 10 | 10/10 |
| D0/4 | 4800 | 0 | 3968 | 800 | 10 | 10/10 |
| D0/5 | 4800 | 0 | 3953 | 800 | 10 | 10/10 |
| I/1 | 13580 | 8780 | 10820 | 5102 | 3.53460972018 | 1/10 |
| I/2 | 15013 | 10213 | 12121 | 5581 | 3.19722906814 | 1/10 |
| I/3 | 15990 | 11190 | 13072 | 5722 | 3.00187617261 | 1/10 |
| I/4 | 16427 | 11627 | 13457 | 5886 | 2.92201862787 | 1/10 |
| I/5 | 17380 | 12580 | 14293 | 6060 | 2.76179516686 | 1/10 |

Each training row’s measured individual segments sum48000 agent-steps; team segments count800 and sum8000, with min/max/mean10 in both arms. Endpoint D0/I each has1600 team decisions,9600 individual sampled decisions,32 reset/1568 team-cap causes and0 gap causes. Endpoint token-switch totals are612/1421; the empty endpoint storage buffers do not measure skill segment lengths. No absence-of-activity condition was imposed.

| Arm | Parameter group | Actual optimizer calls | Initial norm | Displacement after update1 | Displacement after update5 |
| --- | --- | ---: | ---: | ---: | ---: |
| D0 | coordinator | 525 | 104.247538133 | 0.0243295341537 | 0.0430935273745 |
| D0 | discoverer_actor | 11250 | 41.0333938901 | 0.157653605036 | 0.411458848414 |
| D0 | discoverer_critic | 11250 | 41.5159650217 | 0.0721347152357 | 0.15784072109 |
| D0 | team_discriminator | 75 | 50.4777180856 | 0.0107149589641 | 0.0270273083408 |
| D0 | individual_discriminator | 300 | 55.0999094519 | 0.0237973056253 | 0.0524269376764 |
| I | coordinator | 3345 | 104.247538133 | 0.0637248447729 | 0.141682419824 |
| I | discoverer_actor | 11250 | 41.0333938901 | 0.170897583144 | 0.451968603733 |
| I | discoverer_critic | 11250 | 41.5159650217 | 0.0742860384615 | 0.158344274695 |
| I | team_discriminator | 75 | 50.4777180856 | 0.010592617027 | 0.0263809484867 |
| I | individual_discriminator | 300 | 55.0999094519 | 0.0232486832914 | 0.0483230096826 |

## Complete ordered primary values

Episode IDs0–31, evaluation lane seeds780503+ID. Values below are emitted directly from the collected readback without selecting endpoints.

| ID | D0 raw U | D0 native J | I raw U | I native J | I−D0 native J |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 25.518798740171391 | 0.3062255848820567 | 17.121449062316181 | 0.20545738874779418 | -0.10076819613426252 |
| 1 | 28.693278469420818 | 0.34431934163304984 | 11.910007948455304 | 0.14292009538146366 | -0.20139924625158617 |
| 2 | 27.760367615356994 | 0.33312441138428389 | 18.322678369303034 | 0.21987214043163641 | -0.11325227095264748 |
| 3 | 15.131500789857736 | 0.18157800947829281 | 17.026044389691311 | 0.20431253267629573 | 0.022734523198002926 |
| 4 | 19.369285275241143 | 0.23243142330289374 | 14.196067020201538 | 0.17035280424241844 | -0.062078619060475293 |
| 5 | 16.693484900374429 | 0.20032181880449315 | 26.926202087721585 | 0.32311442505265903 | 0.12279260624816588 |
| 6 | 22.503315743697453 | 0.27003978892436942 | 15.533121251329918 | 0.18639745501595903 | -0.083642333908410388 |
| 7 | 22.564724482179521 | 0.27077669378615427 | 8.608631220325158 | 0.1033035746439019 | -0.16747311914225238 |
| 8 | 21.736813598642243 | 0.26084176318370694 | 1.5504159915970797 | 0.018604991899164959 | -0.24223677128454199 |
| 9 | 33.484144292595886 | 0.40180973151115063 | 12.76028018960184 | 0.15312336227522205 | -0.24868636923592857 |
| 10 | 22.022572413758173 | 0.2642708689650981 | 28.648796331661671 | 0.34378555597994004 | 0.079514687014841934 |
| 11 | 13.892827415916349 | 0.16671392899099619 | 34.284622442855337 | 0.41141546931426404 | 0.24470154032326785 |
| 12 | 14.603813325911197 | 0.17524575991093436 | 20.229039805820058 | 0.2427484776698407 | 0.067502717758906344 |
| 13 | 21.076110108336227 | 0.25291332130003474 | 22.548549175181194 | 0.27058259010217434 | 0.017669268802139593 |
| 14 | 23.337812518031527 | 0.28005375021637829 | 11.076489602057224 | 0.1329178752246867 | -0.14713587499169159 |
| 15 | 27.605083314960684 | 0.33126099977952822 | 11.869235229958173 | 0.14243082275949809 | -0.18883017702003013 |
| 16 | 18.37532926684548 | 0.22050395120214575 | 23.440989415216155 | 0.28129187298259389 | 0.060787921780448145 |
| 17 | 23.265196716679647 | 0.27918236060015578 | 17.592109800553136 | 0.21110531760663764 | -0.068077042993518133 |
| 18 | 15.701305578592452 | 0.18841566694310941 | 40.063359967829264 | 0.48076031961395121 | 0.29234465267084181 |
| 19 | 21.077141962793135 | 0.25292570355351762 | 23.19279690358875 | 0.27831356284306502 | 0.025387859289547399 |
| 20 | 24.123805183811921 | 0.28948566220574307 | 18.897066894127519 | 0.22676480272953023 | -0.062720859476212837 |
| 21 | 19.401827229043988 | 0.23282192674852786 | 4.2217793265777113 | 0.050661351918932541 | -0.18216057482959533 |
| 22 | 21.064100767084252 | 0.252769209205011 | 16.631931011007151 | 0.19958317213208579 | -0.053186037072925213 |
| 23 | 19.420890066507056 | 0.23305068079808466 | 27.381848729740533 | 0.32858218475688639 | 0.095531503958801722 |
| 24 | 19.076215977131366 | 0.22891459172557638 | 8.0851851439042797 | 0.097022221726851363 | -0.131892369998725 |
| 25 | 29.636049787079394 | 0.35563259744495268 | 12.41971325026433 | 0.14903655900317195 | -0.20659603844178073 |
| 26 | 19.697897499752109 | 0.23637476999702531 | 20.694219593943437 | 0.24833063512732123 | 0.011955865130295923 |
| 27 | 27.568641991425682 | 0.33082370389710819 | 19.372292925847066 | 0.23246751511016481 | -0.098356188786943383 |
| 28 | 25.991937401746146 | 0.31190324882095377 | 26.988612205621536 | 0.3238633464674584 | 0.01196009764650463 |
| 29 | 22.329240585425435 | 0.26795088702510522 | 20.090379059566562 | 0.24108454871479876 | -0.026866338310306465 |
| 30 | 36.369055554005904 | 0.43642866664807084 | 16.368947531683926 | 0.19642737038020711 | -0.24000129626786373 |
| 31 | 19.469971021786254 | 0.23363965226143507 | 18.054842604315681 | 0.21665811125178816 | -0.016981541009646911 |

## Remaining boundary and next owner

No remaining technical collection blocker or live process. No new arm/seed/evaluation is allocated. Training-seed reproducibility, broader UAV superiority, tuning/headroom and scientific continuation remain outside this technical acceptance. DM owns science intake/Chinese brief/audit and the completed Root-action relay; Root owns integration. Raw scientific roots and supervisor evidence remain preserved. The previously blocked P69 scratch remains untouched; no deletion or bypass was attempted in P70.
