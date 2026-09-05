# FRRIE B01 three-seed root 003 — result evidence (2026-09-04)

Status: `VALID COMPLETE SINGLE-SEED / B01_SEED_VALID_DIRECT`

This is the E0 result record for root `FRRIE-B01-FRESH-BLOCK-003` of
`FRRIE-B01-THREE-SEED-SECTION11-20260904`, frozen in
`FRRIE_B01_THREE_SEED_SECTION11_SCIENCE_CARD_20260904.md` before any of the three invocations.
The cross-seed branch is applied separately in
`FRRIE_B01_THREE_SEED_AGGREGATE_RESULT_EVIDENCE_20260904.md`.

## 1. Question, class, and claim ceiling

On the last prospectively ordered root, do byte-paired `PHY_TRUST` and the containing
same-information `EDGE_FLEX` comparator complete 512 real RSCF updates and the planned fixed-host
98-cell panel, and does the tight projection contact its wall?

Evidence class: `B/EXPLORE`.

The single-seed claim ceiling is root 003 on the same local Windows host as roots 001–002,
training rosters `N={9,15}`, evaluation rosters `N={6,9,15,21}`, interventions `INTACT` and
`SEMANTIC_COLUMN_ROTATE`, and updates `{0,32,64,128,256,512}`. It supports only this root's direct
learner path, work, exposure, return cells, within-model reassociation sensitivity, and
observed-path equality before contact.

| Fact | Direct value |
| --- | --- |
| Object | `FRRIE-B01-THREE-SEED-SECTION11-20260904` |
| Seed validity | `B01_SEED_VALID_DIRECT` |
| Per-invocation aggregate status | `NOT_APPLIED_SINGLE_SEED_INVOCATION` |
| Seed | `FRRIE-B01-FRESH-BLOCK-003` |
| Process-acceptance SHA | `5d0255dcd2aa221378d457c9519312996b0a3f45` |
| Summary-observed HEAD | `60a2a986120524822977ad0e137dc56c2c51f412` |
| Execution route | `local_windows / CARD_PINNED_LOCAL_FIXED_HOST` |
| Process start | `2026-09-04T16:22:46.3392282Z` |
| Detached PID at dispatch | `25984` |
| Summary write time | `2026-09-04T17:32:55.6079646Z` |
| Terminal observation | `2026-09-04T17:35:34.1219942Z` |
| Summary SHA-256 | `f963b380f44974340b4edb9771bababe4585a37e4436edfb49baf00a586b0b90` |
| Summary size | `59,240` bytes |
| stdout / stderr | `0 / 0` bytes |

The accepted process began at `5d0255dc`; while it materialized addressed evaluation tapes, DM
committed only its launch record, so the summary observed `60a2a986`. The three declared source
blobs are identical at both commits: helper `5a2dcf2eee7b4ed81ab34c537807ea5d51121316`, runner
`dcc6db68cba72c6cb76cefee2ea9bc66de9108e4`, and focused test
`cecaa34123a815ffcf56c62f662cfd0af600e6d6`. This is a doc-only identity change, not a source
change.

## 2. Launch conditions and receipts

The fixed-host placement inherited roots 001–002; no remote task was created. Fresh local
admission completed immediately before process creation:

| Admission field | Direct value |
| --- | ---: |
| assessed at | `2026-09-04T16:22:46.285388Z` |
| measurement source | `GlobalMemoryStatusEx` |
| physical available | `15,509,004,288` bytes |
| effective available | `15,509,004,288` bytes |
| required floor | `4,294,967,296` bytes |
| physical / effective / overall pass | `true / true / true` |

The machine-generated exposure line was present exactly:

`updates=512; adam_lr=0.0003; nominal_lr_exposure=0.1536; init_half_range=0.05; nominal_exposure_over_init_half_range=3.072`

The exact argv is in `FRRIE_B01_THREE_SEED_ROOT003_LAUNCH_20260904.md`. Runtime evidence is under:

`temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_three_seed_root003_5d0255dc_20260904T162246Z/`

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| five-root packet | 651 | `3b661df5cacb15aebae8d2bcc0ee8b68d7c769da2ef478881cf8408481e62ce9` |
| admission receipt | 511 | `25a8af2523985d41bb8669f5439139c0bbb76fe3b75a8f357e632e35e262c2a4` |
| `summary.json` | 59,240 | `f963b380f44974340b4edb9771bababe4585a37e4436edfb49baf00a586b0b90` |
| package-native DLL | 120,320 | `6264aad6bbd68a8c8b944acf7388deea6f14db2f98e1855fb919c4e8ad70824a` |

## 3. Declared versus observed work

All 23 completion comparisons are `true`.

| Quantity | Frozen | Observed |
| --- | ---: | ---: |
| paired updates | 512 | 512 |
| factual training episodes per arm | 32,768 | 32,768 |
| factual learner/native slots per arm | 393,216 | 393,216 |
| factual-suffix audit slots per arm | 638,976 | 638,976 |
| nonfactual suffix slots per arm | 1,490,944 | 1,490,944 |
| audit + counterfactual slots per arm | 2,129,920 | 2,129,920 |
| total training slots per arm | 2,523,136 | 2,523,136 |
| backward calls per arm | 512 | 512 |
| Adam steps per arm | 512 | 512 |
| learned evaluation episodes per arm | 12,288 | 12,288 |
| learned evaluation transitions per arm | 147,456 | 147,456 |
| learned cells | 96 | 96 |
| shared uniform cells | 2 | 2 |
| total evaluation episodes | 25,088 | 25,088 |
| total evaluation transitions | 301,056 | 301,056 |
| total invocation slots | 5,347,328 | 5,347,328 |
| successful paired / pre-contact checks | 512 / 512 | 512 / 512 |

The expected 24/25/25/24 cell uses reused the same addressed tapes at rosters 6/9/15/21.
Evaluation preserved model and optimizer state. Runtime facts were CPU FP32, native width 32, and
one Torch intra-op thread.

## 4. Return cells and central estimands

PHY and EDGE return, primitive, and action-count rows were directly equal in every learned cell.
The table prints that shared value once. `e_u` is EDGE intact minus uniform; `I_u=0` because both
arm differences are zero. `V_u` is within-PHY intact-versus-rotated action-probability TV, not an
arm contrast.

| update | N | J INT | D_W INT | D_E INT | min INT | WASTE INT | J ROT | D_W ROT | D_E ROT | min ROT | WASTE ROT | e_u | I_u | V_u |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 6 | 0.010940155 | 0.0390625 | 0.0273438 | 0.0000000 | 0.962538559 | 0.010939321 | 0.0390625 | 0.0273438 | 0.0000000 | 0.962546894 | — | 0 | 0.000053532 |
| 0 | 9 | 0.016773963 | 0.0664062 | 0.0429688 | 0.0000000 | 0.950749955 | 0.016773350 | 0.0664062 | 0.0429688 | 0.0000000 | 0.950756083 | -0.002428312 | — | — |
| 0 | 15 | 0.028294845 | 0.1171875 | 0.0976562 | 0.0039062 | 0.953054158 | 0.028292343 | 0.1171875 | 0.0976562 | 0.0039062 | 0.953079171 | -0.003705321 | — | — |
| 0 | 21 | 0.019576265 | 0.0859375 | 0.0507812 | 0.0039062 | 0.955604538 | 0.020011188 | 0.0898438 | 0.0507812 | 0.0039062 | 0.955487079 | — | 0 | 0.000116015 |
| 32 | 6 | 0.011819288 | 0.0312500 | 0.0429688 | 0.0000000 | 0.962210763 | 0.011790405 | 0.0312500 | 0.0429688 | 0.0000000 | 0.962499600 | — | 0 | 0.000038022 |
| 32 | 9 | 0.019213080 | 0.0781250 | 0.0507812 | 0.0039062 | 0.950772842 | 0.019213080 | 0.0781250 | 0.0507812 | 0.0039062 | 0.950772842 | +0.000010806 | — | — |
| 32 | 15 | 0.033769436 | 0.1367188 | 0.1250000 | 0.0078125 | 0.952344700 | 0.033791651 | 0.1367188 | 0.1250000 | 0.0078125 | 0.952122553 | +0.001769271 | — | — |
| 32 | 21 | 0.024001065 | 0.0976562 | 0.0781250 | 0.0078125 | 0.956929450 | 0.024019723 | 0.0976562 | 0.0781250 | 0.0078125 | 0.956742872 | — | 0 | 0.000090319 |
| 64 | 6 | 0.011800864 | 0.0390625 | 0.0351562 | 0.0000000 | 0.962395011 | 0.011800864 | 0.0390625 | 0.0351562 | 0.0000000 | 0.962395011 | — | 0 | 0.000046612 |
| 64 | 9 | 0.019662232 | 0.0781250 | 0.0546875 | 0.0039062 | 0.950513102 | 0.019662801 | 0.0781250 | 0.0546875 | 0.0039062 | 0.950507408 | +0.000459957 | — | — |
| 64 | 15 | 0.031195556 | 0.1328125 | 0.1093750 | 0.0039062 | 0.953669437 | 0.031187298 | 0.1328125 | 0.1093750 | 0.0039062 | 0.953752022 | -0.000804609 | — | — |
| 64 | 21 | 0.025321347 | 0.0976562 | 0.0898438 | 0.0078125 | 0.956421949 | 0.025734657 | 0.1015625 | 0.0898438 | 0.0078125 | 0.956520621 | — | 0 | 0.000106230 |
| 128 | 6 | 0.012297794 | 0.0390625 | 0.0390625 | 0.0000000 | 0.961657473 | 0.012297794 | 0.0390625 | 0.0390625 | 0.0000000 | 0.961657473 | — | 0 | 0.000040006 |
| 128 | 9 | 0.019624519 | 0.0781250 | 0.0546875 | 0.0039062 | 0.950890227 | 0.019625204 | 0.0781250 | 0.0546875 | 0.0039062 | 0.950883379 | +0.000422244 | — | — |
| 128 | 15 | 0.032919946 | 0.1367188 | 0.1210938 | 0.0039062 | 0.953352623 | 0.032919817 | 0.1367188 | 0.1210938 | 0.0039062 | 0.953353909 | +0.000919781 | — | — |
| 128 | 21 | 0.026128336 | 0.1093750 | 0.0859375 | 0.0078125 | 0.956815596 | 0.026141938 | 0.1093750 | 0.0859375 | 0.0078125 | 0.956679583 | — | 0 | 0.000094208 |
| 256 | 6 | 0.013241380 | 0.0390625 | 0.0468750 | 0.0000000 | 0.960685160 | 0.013241380 | 0.0390625 | 0.0468750 | 0.0000000 | 0.960685160 | — | 0 | 0.000040928 |
| 256 | 9 | 0.019178912 | 0.0781250 | 0.0507812 | 0.0039062 | 0.951114521 | 0.019178912 | 0.0781250 | 0.0507812 | 0.0039062 | 0.951114521 | -0.000023362 | — | — |
| 256 | 15 | 0.032904791 | 0.1367188 | 0.1171875 | 0.0078125 | 0.952527615 | 0.032890617 | 0.1367188 | 0.1171875 | 0.0078125 | 0.952669350 | +0.000904625 | — | — |
| 256 | 21 | 0.025308361 | 0.0937500 | 0.0898438 | 0.0117188 | 0.955575248 | 0.025308266 | 0.0937500 | 0.0898438 | 0.0117188 | 0.955576196 | — | 0 | 0.000065582 |
| 512 | 6 | 0.013394805 | 0.0390625 | 0.0468750 | 0.0000000 | 0.959150909 | 0.013390227 | 0.0390625 | 0.0468750 | 0.0000000 | 0.959196691 | — | 0 | 0.000085936 |
| 512 | 9 | 0.021787973 | 0.0859375 | 0.0625000 | 0.0078125 | 0.949437983 | 0.021788563 | 0.0859375 | 0.0625000 | 0.0078125 | 0.949432075 | +0.002585698 | — | — |
| 512 | 15 | 0.036134856 | 0.1484375 | 0.1328125 | 0.0078125 | 0.949849356 | 0.036133483 | 0.1484375 | 0.1328125 | 0.0078125 | 0.949863089 | +0.004134691 | — | — |
| 512 | 21 | 0.032874176 | 0.1367188 | 0.1093750 | 0.0195312 | 0.954135841 | 0.032873931 | 0.1367188 | 0.1093750 | 0.0195312 | 0.954138294 | — | 0 | 0.000143250 |

Uniform cells were `J=0.019202274`, `D_W=0.0781250`, `D_E=0.0507812`, `min=0.0039062`,
`WASTE=0.950880901` at `N=9`; and `J=0.032000165`, `D_W=0.1289062`, `D_E=0.1171875`,
`min=0.0078125`, `WASTE=0.953110326` at `N=15`.

At update 512, EDGE's margins over uniform were `+0.002585698` and `+0.004134691`; the maximum
held-out `V_u` on this root was `0.000143250`.

## 5. Action and native-event counts

The action order is `[0,1,2,3,4,5]`. Event tuples are
`(duplicate, expired, collision, empty_radio, radio_actions, waste_actions,
successful_deliveries)`. PHY and EDGE rows were directly equal.

| update | N | intervention | action counts, PHY = EDGE | native events, PHY = EDGE |
| ---: | ---: | --- | --- | --- |
| 0 | 6 | INT | `[4082,4002,1618,1381,1475,5874]` | `(3,92,76,4773,8476,8154,17)` |
| 0 | 6 | ROT | `[4078,4006,1618,1381,1475,5874]` | `(3,93,76,4778,8480,8158,17)` |
| 0 | 9 | INT | `[6239,5929,2462,2094,2242,8682]` | `(2,187,189,7075,12727,12103,28)` |
| 0 | 9 | ROT | `[6237,5931,2463,2093,2242,8682]` | `(2,187,189,7077,12729,12105,28)` |
| 0 | 15 | INT | `[10408,9780,4236,3307,3655,14694]` | `(11,343,553,11724,20978,20008,55)` |
| 0 | 15 | ROT | `[10405,9783,4239,3304,3655,14694]` | `(11,343,553,11727,20981,20011,55)` |
| 0 | 21 | INT | `[14793,13559,5950,4623,5106,20481]` | `(2,448,1138,16174,29238,27940,35)` |
| 0 | 21 | ROT | `[14796,13556,5955,4620,5104,20481]` | `(2,448,1136,16168,29235,27934,36)` |
| 32 | 6 | INT | `[4046,4190,1556,1484,1546,5610]` | `(2,96,82,5008,8776,8440,19)` |
| 32 | 6 | ROT | `[4043,4191,1556,1484,1546,5612]` | `(2,95,82,5012,8777,8443,19)` |
| 32 | 9 | INT | `[6144,6335,2360,2278,2340,8191]` | `(3,198,216,7517,13313,12658,33)` |
| 32 | 9 | ROT | `[6144,6335,2361,2277,2340,8191]` | `(3,198,216,7517,13313,12658,33)` |
| 32 | 15 | INT | `[10210,10677,3936,3756,3945,13556]` | `(9,365,628,12795,22314,21262,67)` |
| 32 | 15 | ROT | `[10208,10681,3937,3756,3946,13552]` | `(9,366,628,12797,22320,21263,67)` |
| 32 | 21 | INT | `[14417,15033,5481,5324,5564,18693]` | `(3,470,1318,17861,31402,30051,45)` |
| 32 | 21 | ROT | `[14417,15034,5482,5325,5566,18688]` | `(3,475,1312,17863,31407,30050,45)` |
| 64 | 6 | INT | `[4072,4127,1538,1489,1569,5637]` | `(3,96,78,4976,8723,8391,19)` |
| 64 | 6 | ROT | `[4071,4128,1538,1489,1569,5637]` | `(3,96,78,4977,8724,8392,19)` |
| 64 | 9 | INT | `[6206,6202,2323,2300,2376,8241]` | `(4,195,204,7436,13201,12548,34)` |
| 64 | 9 | ROT | `[6204,6200,2323,2300,2376,8245]` | `(4,194,206,7433,13199,12546,34)` |
| 64 | 15 | INT | `[10317,10396,3868,3782,4033,13684]` | `(5,361,636,12608,22079,21068,62)` |
| 64 | 15 | ROT | `[10317,10391,3868,3782,4034,13688]` | `(5,360,636,12606,22075,21066,62)` |
| 64 | 21 | INT | `[14633,14600,5365,5387,5692,18835]` | `(2,472,1263,17606,31044,29694,48)` |
| 64 | 21 | ROT | `[14633,14598,5366,5387,5695,18833]` | `(2,475,1267,17604,31046,29699,49)` |
| 128 | 6 | INT | `[4048,4144,1553,1475,1572,5640]` | `(3,97,82,4985,8744,8405,20)` |
| 128 | 6 | ROT | `[4047,4144,1553,1475,1572,5641]` | `(3,97,82,4986,8744,8405,20)` |
| 128 | 9 | INT | `[6142,6240,2354,2265,2381,8266]` | `(4,198,212,7470,13240,12590,34)` |
| 128 | 9 | ROT | `[6142,6239,2354,2265,2381,8267]` | `(4,198,212,7470,13239,12589,34)` |
| 128 | 15 | INT | `[10178,10499,3924,3721,4039,13719]` | `(8,368,632,12718,22183,21161,66)` |
| 128 | 15 | ROT | `[10179,10494,3924,3721,4043,13719]` | `(8,369,632,12717,22182,21160,66)` |
| 128 | 21 | INT | `[14356,14812,5459,5286,5697,18902]` | `(3,473,1284,17801,31254,29907,50)` |
| 128 | 21 | ROT | `[14356,14808,5462,5284,5701,18901]` | `(3,474,1282,17799,31255,29904,50)` |
| 256 | 6 | INT | `[4023,4127,1523,1499,1542,5718]` | `(3,98,82,4942,8691,8345,22)` |
| 256 | 6 | ROT | `[4022,4128,1523,1499,1543,5717]` | `(3,98,82,4943,8693,8347,22)` |
| 256 | 9 | INT | `[6103,6204,2299,2301,2334,8407]` | `(4,195,219,7387,13138,12496,33)` |
| 256 | 9 | ROT | `[6103,6203,2299,2301,2334,8408]` | `(4,195,219,7386,13137,12495,33)` |
| 256 | 15 | INT | `[10097,10375,3826,3801,3919,14062]` | `(7,364,639,12471,21921,20894,65)` |
| 256 | 15 | ROT | `[10096,10375,3826,3801,3921,14061]` | `(7,364,641,12473,21923,20899,65)` |
| 256 | 21 | INT | `[14211,14641,5310,5399,5498,19453]` | `(3,481,1262,17429,30848,29478,47)` |
| 256 | 21 | ROT | `[14211,14642,5311,5399,5498,19451]` | `(3,481,1262,17430,30850,29480,47)` |
| 512 | 6 | INT | `[4028,4184,1530,1512,1580,5598]` | `(3,108,92,4977,8806,8441,22)` |
| 512 | 6 | ROT | `[4028,4181,1530,1512,1581,5600]` | `(3,107,90,4977,8804,8440,22)` |
| 512 | 9 | INT | `[6128,6250,2306,2341,2381,8242]` | `(3,213,243,7402,13278,12607,38)` |
| 512 | 9 | ROT | `[6128,6250,2306,2341,2381,8242]` | `(3,213,243,7402,13278,12607,38)` |
| 512 | 15 | INT | `[10123,10459,3854,3847,4006,13791]` | `(6,389,718,12484,22166,21065,72)` |
| 512 | 15 | ROT | `[10121,10462,3855,3846,4007,13789]` | `(6,389,718,12487,22170,21069,72)` |
| 512 | 21 | INT | `[14236,14696,5345,5547,5576,19112]` | `(3,504,1395,17375,31164,29733,63)` |
| 512 | 21 | ROT | `[14236,14696,5345,5548,5578,19109]` | `(3,504,1395,17377,31167,29736,63)` |

Uniform action/event rows were `[6154,6118,2303,2311,2306,8456]` /
`(3,192,198,7302,13038,12399,33)` at `N=9` and `[10120,10273,3833,3785,3841,14228]` /
`(6,348,585,12377,21732,20727,63)` at `N=15`.

## 6. Exposure, contact, rule input, and resources

- `L_inf(theta_512-theta_0)/0.05 = 2.147961259` in both arms; absolute displacement was
  `0.107398063`.
- First tight contact: none; changed tight coordinates: 0; maximum overshoot and cumulative tight
  displacement: 0; wide-boundary contact: false.
- All 512 pre-contact full-state, information/work, and evaluation equality checks passed.
- Total wall: `4,207.513025 s` (`70.125 min`, `1.169 h`); PHY/EDGE attributed wall:
  `788.283428 / 775.643771 s`; throughput: `1,270.900` declared slots/s.
- Peak RSS is unavailable; the valid result is `resources_unmeasured`.
- After terminal, the untracked native DLL was hash-preservingly moved into this exact run root;
  the worktree returned clean.

## 7. Single-seed disposition and prediction

Admission, exposure, learner/update/evaluation counts, pairing, state preservation, and all
completion checks pass. `B01_INVALID` does not fire. Root 003 is `B01_SEED_VALID_DIRECT`; its own
summary correctly does not apply a cross-seed rule.

The DM prediction `B01_WIDE_INCOMPETENT` was conditional on at least one seed contacting. Root 003
also did not contact, so after all three roots the condition is false and the prediction is not
scored; its predeclared no-contact alternative is the relevant branch input. The owner slot was
`not taken (unattended)`.

This seed's strongest support is the complete paired trace. Its strongest contradiction to a
tight-package value claim is nonactivation. It cannot identify behavior after contact or a
competent treatment contrast. Cross-seed disposition is recorded in the aggregate evidence.
