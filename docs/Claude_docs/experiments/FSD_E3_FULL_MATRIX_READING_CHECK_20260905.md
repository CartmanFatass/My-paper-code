# FSD E3 full-matrix arithmetic check

**Existing 18-cell arithmetic conforms; original helper returns E3-H0-NO-ADVANTAGE.**
DM accepted cell18 at907ef04bd298e79c2800cb5695d0b28b0f34aa1a before this reading.
This is a technical recomputation, not an independent scientific interpretation or direction decision.

Scope: this compact receipt and ignored derived reading only. No source edit, learner, evaluation,
checkpoint reread, replay, admission, remote status, test, successor, new object or P3/P4 inbox.
Engineering section4 additions none. Prior accepted per-cell receipts establish checkpoint/runtime
conformance; this read checks summary/eval/path arithmetic, not independent reproduction of learning.
CM own worktree/branch reused, unrelated changes and evidence roots preserved.

Canonical root:
`C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904`.
Exact selected set is small/medium/large x d0/d2 x seeds1/2/3,18 unique cells. Only these canonical
roots are read. Historical medium D0 seed1 attempt01 quarantine and transfer-staging directories
are excluded, preserved, and neither treated as extra cells nor silently included in totals.

Each summary identifies original card FSD-E3-HET-R01; its launch SHA agrees with manifest.
All18 completedtrue,20rollouts,128000transitions,320trainingepisodes,instabilitynull,not timing-only,
no quarantine marker. Path IDs1–20 exact;eval schedules5/10/15/20 and512/512/512/2048 exact;
JSONL equals summary. Each final array has2048 finite returns,ordered IDs0..2047,master770003;
pair keyed-ID laws agree. All per-eval means reproduce within1e-15. No tape regeneration occurred.

Original pure helpers paired_return,event_path,apply_result_rule,_aggregate_path were imported
without calling main. Their ASTs match every one of13 actual launch SHAs. Summary cumulative path
reproduces exactly from20 path records;final_regional_path equals last record. The original
_postprocess source explicitly calls event_path(cumulative) for summary large_row_event_path.
It does not use final_regional_path. The card lists the three path inequalities without naming
an aggregation window; we preserve the implementation's cumulative meaning and separately report
final-rollout facts. We do not select a window after seeing outcomes.

## Paired arithmetic

G is mean(D2-D0) across2048 matched final episodes;SE is sample std(diff)/sqrt(2048),not an
unpaired or across-seed uncertainty estimate. Q divides by exact recomputed m_dur,not rounded card
table values. D0 competence is meanD0/Jk,threshold.85. All values below rounded only for display.

| Row | Seed | G | Paired SE | Q | D0/Jk |
| --- | ---: | ---: | ---: | ---: | ---: |
|small|1|-0.041736165365|0.000617962481|-0.731732712090|0.942572764946|
|small|2|0.033291585286|0.000476446411|0.583679448714|0.872613126268|
|small|3|0.062728759766|0.000634760258|1.099782050133|0.814254153484|
|medium|1|-0.016412597656|0.000510989211|-0.113693884790|0.884807482381|
|medium|2|-0.039020019531|0.000594158192|-0.270300759087|0.935604293874|
|medium|3|-0.053367187500|0.000616463185|-0.369686931603|0.959050879690|
|large|1|-0.071387329102|0.000880042921|-0.263209190038|0.885432842105|
|large|2|-0.108895874023|0.000737006906|-0.401505353414|0.912487998333|
|large|3|-0.086455281576|0.000721098273|-0.318765597822|0.884880387535|

Small seed3 competence is below.85;the raw pair remains visible. All large comparators exceed.85,
all three large G values are negative. Original rule therefore returns E3-H0-NO-ADVANTAGE.
This records deterministic rule arithmetic only;DM owns bounded B interpretation.

## Cumulative versus final regional path

Each row lists D2 low/high mean segment lengths,low/high gap-renewal rates per agent-step,
and high-region precision. Final means/rates are computed by the same aggregate helper on the
single final path record,not mixed with cumulative denominators.

| Seed | Window | Length low/high | Gap rate low/high | High precision | Event path |
| --- | --- | --- | --- | ---: | --- |
|1|cumulative|5.435167230/5.510669747|0.170903646/0.167731771|0.495676070|False|
|1|final|2.719932002/2.713780919|0.362239583/0.363385417|0.476995843|False|
|2|cumulative|7.324889364/7.006659976|0.121380208/0.129549479|0.575069853|True|
|2|final|2.716084312/2.766570605|0.364114583/0.357343750|0.575717825|False|
|3|cumulative|9.270659810/9.538476824|0.090903646/0.087033854|0.527752012|False|
|3|final|4.137039431/4.121940747|0.234687500/0.235468750|0.558947136|True|

Summary cumulative flags are false/true/false;final flags false/false/true. They are different
observations,not a data mismatch. Feeding either complete window consistently into the original
rule gives the same branch here,because competent large returns are all negative.

## Exposure and resource accounting

Network vector order:coordinator,discoverer actor,discoverer critic,team discriminator,individual
discriminator. Each first/final ratio is positive finite;values are float64 helper output,
not a change to float32 learner precision. Full values remain in derived reading and source.

| Cell | First ratio vector | Final ratio vector | Runner wall s |
| --- | --- | --- | ---: |
|small_d0_seed1|0.014902138,0.085426151,0.14151605,0.011993602,0.019398349|0.055858857,0.49288402,0.54334112,0.039531997,0.10200408|4956.585495|
|small_d0_seed2|0.013542613,0.10320542,0.13695722,0.010010361,0.019164413|0.056808018,0.48075972,0.52138968,0.03962483,0.10308707|5044.960150|
|small_d0_seed3|0.014639534,0.10461636,0.13858956,0.0098823811,0.018912326|0.055315248,0.49462116,0.53815081,0.038946607,0.10473592|5315.181455|
|small_d2_seed1|0.020253643,0.088532326,0.13195241,0.012127752,0.018366254|0.11337313,0.40538178,0.39938041,0.059718919,0.078141434|6330.053156|
|small_d2_seed2|0.022722941,0.081882653,0.10057614,0.013531714,0.016945681|0.11685589,0.4229359,0.41547968,0.060212739,0.096865223|6590.244355|
|small_d2_seed3|0.02646663,0.078425036,0.099859679,0.013650606,0.016736774|0.12826703,0.41834956,0.39742366,0.059935506,0.086121281|6468.838719|
|medium_d0_seed1|0.040462056,0.16072706,0.2368637,0.010461908,0.013206246|0.12273881,0.82290982,0.88193079,0.0344882,0.055629446|2677.041621|
|medium_d0_seed2|0.040031205,0.16372249,0.21333694,0.0096167675,0.013202791|0.11785903,0.82378466,0.88804809,0.035384271,0.057141627|2620.968246|
|medium_d0_seed3|0.040808236,0.16684791,0.24597085,0.0091946145,0.012286577|0.11708156,0.86760065,0.93370235,0.038076506,0.056803847|2687.744683|
|medium_d2_seed1|0.021760334,0.084796302,0.11513175,0.012303919,0.01733214|0.14994654,0.41187565,0.41678186,0.057287637,0.074461793|2678.061287|
|medium_d2_seed2|0.023463586,0.072933291,0.093509027,0.013574213,0.017228456|0.13117895,0.40800533,0.38872533,0.067998806,0.086226666|2405.337414|
|medium_d2_seed3|0.028561278,0.075356873,0.10545783,0.013571879,0.016231476|0.12703892,0.42609673,0.40127405,0.058247839,0.083193744|2525.540706|
|large_d0_seed1|0.039637712,0.15977621,0.23055412,0.010203675,0.01305689|0.12392501,0.8630097,0.87459282,0.033387539,0.053849379|2837.557188|
|large_d0_seed2|0.041806333,0.15479584,0.21729882,0.0094293053,0.01260199|0.10621772,0.84332205,0.89446772,0.03559481,0.054078532|2603.277692|
|large_d0_seed3|0.038639219,0.1642048,0.23738037,0.0093937215,0.011595851|0.11931667,0.86997521,0.89535016,0.036233958,0.053831008|2445.514380|
|large_d2_seed1|0.020266789,0.073319022,0.12772162,0.012265348,0.017766117|0.16679552,0.44912356,0.44350371,0.058336165,0.073702103|2795.302872|
|large_d2_seed2|0.0204337,0.076803698,0.10591536,0.013602222,0.017309194|0.15875599,0.46047981,0.39879525,0.055890346,0.080898952|2646.479974|
|large_d2_seed3|0.025179707,0.072845358,0.11891821,0.013737861,0.016462174|0.13864646,0.44460259,0.41722822,0.059342238,0.08297996|2458.311039|

| Network | First min/max across18 | Final min/max across18 |
| --- | --- | --- |
|coordinator|0.0135426125852/0.0418063330405|0.0553152482813/0.166795515435|
|discoverer_actor|0.0728453581757/0.16684791425|0.405381783309/0.869975205255|
|discoverer_critic|0.0935090271339/0.245970848483|0.38872532696/0.93370234574|
|team_discriminator|0.00919461454225/0.0137378614336|0.033387539317/0.067998805742|
|individual_discriminator|0.0115958510219/0.0193983491977|0.0538310083276/0.104735919177|

Totals:360rollouts,2304000transitions,5760trainingepisodes,64512evaluatedepisodes,72evaluationrecords. Recorded runner wall sum **66087.00043219907s** (18.357500120h),not study elapsedtime or a sum of observeruptime. Update groups {'coordinator': 51570, 'discoverer_actor': 567000, 'discoverer_critic': 567000, 'team_discriminator': 5400, 'individual_discriminator': 21600},total **1212570**. All18 resource flags are resources_unmeasured;peakRSSnull and peak scratch unavailable. These flags do not establish runtime peak conformance. No quarantine cost is included in valid-cell totals.

## Source artifacts and reproducibility

Derived reading retains full numbers,all source SHA references and both full path dictionaries:
`temp/directions/flexible_skill_duration/exp/E3_20260904/full_matrix_reading_20260905/reading.json`
under this CM worktree. It is ignored evidence,not a runner/schema/guard. Its SHA256 is
9d34d7b0691c41969a92f0a59ce3b2510f0dbd731cebb7cc96482676e45478c4.

| Cell | summary.json SHA256 | eval.jsonl SHA256 | path.jsonl SHA256 |
| --- | --- | --- | --- |
|small_d0_seed1|6a77a51be03e8d65061c29684b5ab63684881363d310462ec69cdc359342cd4e|3706a66574622c9d1e849bda20f0c8667fd5ff2310c9ce6a2befa75063a95d24|3a5ba087c783ba8184f2b9ea84014d0f28d4b58cf81f1f4f5e2ab5c453524b4c|
|small_d0_seed2|ee45fe8c20754fcc5fc45cb035cb572289191c2846b41eaea609e13dcb41614c|8262fd609ed32b4b6fc9a2ca218380763a7a658a73511cfda9a20e34071072be|77b8df7a925e89832d2dd0924573d82e5b2d8643b9369aec0b0a90a622e0bf6c|
|small_d0_seed3|6ac3e1c32b13248563cab25eeda936bffd24d0464832c51ab5f1815f8946f669|7bedeb72cb9211363e17d998365c5171505416cada9fec7d8d6b2d4850e76749|1688e60119fb0ff5136c3f7b57f03128b5d0eff8789a347bca52eb3a28c51b7d|
|small_d2_seed1|61b658daa1a25cbbb2660fc5fba734c1c7c9475c5d5719fa91c9024cf5e18a69|36b9d756096c22bb30c00b4456112de26967cb45c761f3c4219dec0704a33b31|f4fc33c852d99ab45705347588151271628aea4ca3e004c8a09754ef333d6732|
|small_d2_seed2|7662b2b90e7c5ce44eeabc599f044ece1ed9475b046e4ff9cdd38d0143a3866a|b87e28a40f5cbe6747c09a0e39338ff138a1d800ec971bcb60757122dd0fbc08|82de43d013f4c2c738d24d4815cbada4cb86c802046c355fa1a91c11943deeb9|
|small_d2_seed3|16d61d7f5a2da3ef0363d93074cc9091d873acb6b964835a9e54271834e62410|a452c29e4c003a9e5546e5f48f350a44b7719006abe7ac1b24eba20d04b32873|df1740ac93dd9ece753b6d477312a929c4a5d911c1d96172ea8d4b5c9350ef6c|
|medium_d0_seed1|2cb92f7f8627c06a16acb31326e75178d53e38e2d2184be56872903f8d352886|2a1254624c0cb304764020ebc69b8111a1e270c19060f8a0fbb0b8691d961a69|77c67d7a173420dafe95f4146666fde62388de2fa8d3303aee2ce00bc8652ee1|
|medium_d0_seed2|9ad858e02db8536385b0d8727d08618696ee85207e97797c387b5f2f2c44ed08|2cd0a9343eed80d75f0768dc8b33ed9b8e25656249a3cda73d2dc08a7592ae69|9087c5c9caf649f776611cafc264d74d31eae60cb5ec699e589aed73323cfd1b|
|medium_d0_seed3|4895b4c92ed28f5e36b4e92ca407a952b22011faac3218b0ede7233ed1b52a52|dcb14e5f52c1f6398c56901fd29457578cf11b4e2f358b47d8c1ca59c47eef9c|75be6bb5b3280d2402e03557b3c3058d6dad892da8dd75050d33b625673f8cbb|
|medium_d2_seed1|0089f8944853de3845cb74a0d40f3944758968ff63006cccfd1a42b79321cb07|efabcf47200e2d8e8893b52f49fc51f67d1d75e3c85ad294d80f8a8516a56fe4|0ba195c0ee1600ed037d4077c700533be2282eb124c21baedda89d62c4417ce9|
|medium_d2_seed2|fe37f82c6fb559f5c88bac192746abb09cce05c25be32889a161fd4bc1dd2f9d|41ce5a97381d0d3c348a94d1c434b246abf5fabe27531d70376765a09c4ddc8b|3092a42e42f2c9ad86a2a0bf9530a6868cf14efd9a2c6be07450abaf670efee8|
|medium_d2_seed3|7cee34416a1508b900b06715d514273bc195e540109be181c747302595d0167c|8e62bd1f9971991698928ad2e2881677d9727af3125a18f8a3256235f76f3363|0cb5edc0b6eef48a660c6aff7a940a202635c97d408c66657b458cf051784503|
|large_d0_seed1|fc0507d3d5a1fb128c5f2bf9ffa8fced81490e4e62ca073473841ffbca8a4418|74ef6d638c323bc8c87d4f0ce9132d1282e78c6af15f710d4b6652a4a6ebc7fb|ff08dfaaf6da4c19267bcfad5e380ed9f39141f5ae338e79fc5afe9908cb9ebe|
|large_d0_seed2|2d41dd5a3eaf02968806ec1c325c3fba128699c7d53dde09ab59ba599d834b73|7ddb137d1830b0b25ed80936fa8052492bc577e0e9633cd9253e5788d90fb14a|0a6ad357636df644dc32d3ae031598889957643d4b8da7bd3ffb11b01c5e1495|
|large_d0_seed3|2dae386c8ce4077057aa7f6165e094c02d60d80a0410ec04fe52844cdbddc099|adda0bd35b5ca30b8f382dea2ffc7fbad87e7047db036885526029252e5b4c08|668c1ae8b02d00b810100313b5fa1a577daf451bf06a7a29317e0ce573ebf4d1|
|large_d2_seed1|d6801ec6a0c7ef47706768382f6ee008f105854b88d41036c391177c5f9dbc98|f9c825a37ea356260545a0d4b3d3628095c1e33d2b0cdc63ee5c0cba9e0b0c94|965cf5910260a1998f3ee2506c2f654b6d4b3c607fbad7ec4bd898219daa7e2c|
|large_d2_seed2|5c106f64790f833faa8d43e7af8e872f7ea9e00df2d8349a3a742fbfa3776f22|210b09db71397fc22cfbeddfcb16b2bcd509cc4c0154f6747ead0a3ac6231bcb|d6856f107748e8796f2bdb5911462800b0a3a966ee427f39c0cdb72cba0c0001|
|large_d2_seed3|6846cc1267b2e773b7d09cf99717b9700b98388ce3051d49ef8115391851fec6|8d8b9c4d7a3ad26995f3b5f5affc7242c4c93e9e266c773e8360ace868a0b151|d15ad42ab55d1227234431d3c87bc23dc5a6fcceb5e30a156f843a1034fb791c|

Actual launch SHAs checked for identical pure helpers:

0f31b04f245aa9d5273b9131835ef1be59955759, 31bfecd79fc0f708546786ee26dfd8faa9e85dfb, 4b61ddfffac042e2247c77668bc881cca68b9a78, 4c60f281febd9c5c6503b12aa8053f05642aac32, 6d64a95a1189523e39abb184ef284a574050b748, 96ca5fbf815f142008d6622759014a98bd915d6f, 9c0a990537a8ffef58306429a1ff402550fc4b82, ac4db77371659c25d4ac39e1a20990fe098bc42d, e6108e466eeea3df31db52c53e49eef828bde41a, e6d049849f717b2aca98ab1bb77092e000cd06d9, e72e1cf08c9510b52ef67b135e93eee89dc4ddce, ee7fdae278cede2200ab8c356c4f238cce980edb, f42dcb7a76f6341d3552a27134ca674674b29718.

No true arithmetic/source-contract mismatch found in this bounded read. No new scientific gate
or aggregate performance claim added. Technical deliverable complete;DM interprets and records
the original B rule within its card ceiling.
