# UCOPE shared-data return model B04 technical and execution evidence

## Implementation and acceptance

Assignment P09-UCOPE-HALF-DATA-01; [card sections 2–5](UCOPE_SHARED_DATA_RETURN_MODEL_B04_SCIENCE_CARD_20260907.md), frozen at `414cd77e50061f1dee102645b980886057942183`.
The shared B02 runner accepts an explicit batch count, resolves its omitted default to the existing
1024 constant and reports the selected count in collection, summary and cost law. The new B04 entry
fixes 512 batches and seeds 6601/6602 with B04 result identity. B02/B03 entry defaults, model/evaluator,
B02 RNG family, binary64 row/update order, native host, costs, rules and full 4096 evaluation are unchanged.
No global seed or batch mutation occurs. ENGINEERING_SCOPE_SPEC section 4 additions: none, per card section 4.
Source delta: 5 additions/4 deletions in shared runner and 23-line B04 entry; no learner/host changes.

Focused acceptance (synthetic host returns only, zero scientific exposure):

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/shared_data_return_model_b04/test_budget_binding.py tests/experiments/candidates/ucope/shared_data_return_model_b03/test_seed_binding.py tests/experiments/candidates/ucope/shared_data_return_model_b02/test_shared_return.py::test_synthetic_changed_path_and_publication --basetemp temp/directions/ucope/test/shared-return-b04-synthetic-01
```

Result: **3 passed in 7.87 s**, only the existing unknown `cache_dir` config warning. The B04 fixture
executes all 512 batches on synthetic rows and all 4096 evaluation indices/context/policy for each new
seed, checks selected counts/cost law and summary publication, and captures unchanged B02/B03 default
1024 arguments using one synthetic historical batch. Existing seed/default/publication checks pass.
This covers the affected post-learner publication path without a real-host smoke or replay. Independent
review by the reused `review_ah_ucope_b01` reviewer found no material finding against base `414cd77e5`.
The reviewer inspected B04 synthetic training/update/evaluation artifacts and historical defaults/partial
publication without rerunning tests or science. New test: 62 lines; source total 28 additions/4 deletions.
At source acceptance, no result-bearing invocation had been dispatched; real-host performance and
timing were then unmeasured. The later terminal observations are recorded below.

## Cost and execution boundary

Per-arm projection from existing B03 whole-path evidence: 10.46 s/dataset, 20.92 s summed, with reduced
training work but unchanged evaluation. Cost law `T_init + 512*T_batch256_shared_fit + 32768*T_three_policy_eval + T_publish`.
No phase coefficients or aggregate CPU estimate is available and no calibration run follows. Each complete
command cap is 600 s including adjacent fresh admission, interpreter/startup, learning, evaluation,
publication and exit; 1200 s summed. Staging/control intervals are separate from summed invocation wall.
Each selected dataset has 131072 training and 98304 final evaluation episodes (229376 total),
196608 scalar updates, 65536 histogram increments and 264 initially zero values.

Remote-only `wsl_4070` / `hmasd-wsl-node`, CPU Python binary64, one scientific process/thread,
`/home/wu/.venvs/hmasd/bin/python`; `.codex/hmasd-compute.toml` controls exact execution facts.
The prospective plan required source integration and push by Root before its acknowledgment and exact prelaunch
binding. Then exactly seed 6601 followed by 6602 after terminal reconciliation, irrespective of first
valid score, with distinct handles/roots and fresh same-node admission. No local fallback, extra pilot,
replay, retry or third seed. Root receives accepted handles; CM observes to adoption ACK or terminal
and collects. A dependent defect/admission gap returns completed/partial facts without a new invocation.

## Launch binding and collection

Root integrated and pushed the card/accepted source at main `98ee9ec0f` (integration commits
`942a3ec86`, `98ee9ec0f`) and acknowledged execution, relayed by DM before this binding.
The exact accepted launch source is `71433bfabb70481def4329e622a838fa0cd9eeec` on `codex/ucope`;
Git surface comparison with integrated main shows no differences in the B02/B03/B04 runners
or UCOPE experiment tree. Both authoring checkout and bound source surface are clean.

Node `wsl_4070`, detached cwd `/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907`;
full-history named-reference Git bundle/SCP stages the committed source, using
`/home/wu/hmasd-inputs/ucope-b04-source-20260907.bundle`. Handles are
`ucope-shared-return-b04-seed6601-20260907` and `ucope-shared-return-b04-seed6602-20260907`.
Both handles were confirmed absent and proposed remote source/bundle locations unused before binding.
Each supervisor log is `/home/wu/.agent-tasks/<handle>/task.log`. Each output root is
`temp/directions/ucope/exp/shared-data-return-b04-seed<seed>/` beneath the bound cwd, containing
`summary.json` and adjacent `resource_admission.json`. The outer timeout includes admission and
all runner work; admission failure prevents the adjacent runner. Same selected host, no fallback.

Exact remote supervisor command strings, recorded before either output:

### Seed 6601

```sh
/usr/local/bin/agent-task run ucope-shared-return-b04-seed6601-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b04-seed6601/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b04.py --seed 6601 --out temp/directions/ucope/exp/shared-data-return-b04-seed6601'"'"''
```

### Seed 6602

```sh
/usr/local/bin/agent-task run ucope-shared-return-b04-seed6602-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b04-seed6602/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b04.py --seed 6602 --out temp/directions/ucope/exp/shared-data-return-b04-seed6602'"'"''
```

## Terminal collection

Exactly seeds 6601 then 6602 were dispatched once each, after Root source integration acknowledgment.
Both finished with exit code 0. Seed 6601 was terminal and its saved required outputs reconciled before
seed 6602 started; the smaller first score did not change the selected second invocation. No pilot,
replay, retry, extra evaluation or third seed occurred. Both summaries identify the bound source
`71433bfabb70481def4329e622a838fa0cd9eeec`. CM sent Root accepted handles and followed both to terminal;
no process remains live and no observation transfer/relaunch was needed.

The two external complete-command walls are **4.71 s each, 9.42 s summed**, below each 600 s and the
1200 s summed cap. First admission to second exit is about 70 s including intermediate control/collection;
earlier integration/staging intervals are separate. Aggregate CPU and scratch peak are unmeasured.
Raw runner summaries retain `resources_unmeasured`; the external whole wall/RSS measurements below
supply those two quantities only. No optional resource gap changes this non-resource primary.

### Seed 6601: COMPLETE, recorded branch RM-B

Fresh admission `2026-09-07T19:07:43.844963Z`: physical/effective available **15653625856 / 15653625856 bytes**, both pass 4 GiB.
External `whole_wall_seconds=4.71 peak_rss_kib=21088`; runner wall 4.6556750729796477 s.

| Paired endpoint | Mean | Conditional MC SE |
| --- | ---: | ---: |
| delta_native | -0.00087353515624999552 | 0.00074464571821423466 |
| delta_information | -0.00087353515624999552 | 0.00074464571821423466 |
| blind_minus_immediate | 0 | 0 |

| Phase/policy | Episodes | Transitions | Probe episodes | Committed period units | Probe time units |
| --- | ---: | ---: | ---: | ---: | ---: |
| training | 131072 | 655360 | 65536 | 590774 | 131072 |
| FULL | 32768 | 114688 | 8192 | 131984 | 16384 |
| BLIND | 32768 | 65536 | 0 | 131072 | 0 |
| IMMEDIATE-4 | 32768 | 65536 | 0 | 131072 | 0 |

| Fitted component | Entries / occupied | Updates | Displacement L2 | Maximum movement |
| --- | --- | ---: | ---: | ---: |
| shared_immediate | 8 / 8 | 65536 | 2.2351955672363504 | 0.7954404296875015 |
| full | 224 / 224 | 65536 | 9.9276804476287488 | 0.90412297734627833 |
| blind | 32 / 32 | 65536 | 3.7207442767464158 | 0.75643365047571487 |

Initial L2 is zero, first observation step is 1; histogram increments 65536, occupied bins 56. No finite relative movement ratio to zero is reported.

| Policy | Mean return | Mean paid component | Probe frequency |
| --- | ---: | ---: | ---: |
| FULL | 0.79423120117187496 | -0.012384033203124999 | 0.25 |
| BLIND | 0.79510473632812495 | 0 | 0 |
| IMMEDIATE-4 | 0.79510473632812495 | 0 | 0 |

All context outcomes, including losses, and final plans follow. BLIND and IMMEDIATE-4 coincide throughout, with no acquisition or paid component; their difference is zero, and native/information contrasts coincide. IMMEDIATE-4 always chooses period 4. FULL tails correspond to displayed counts 0 through 6; unexecuted tail plans remain plans only.

| Context | FULL return | BLIND / IMMEDIATE-4 return | Native / information difference | FULL paid mean | FULL root / tails | BLIND root / tail |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| LINKED-p13_20-c9_100 | 0.77618749999999992 | 0.79800390624999995 | -0.021816406250000003 | -0.049736328124999993 | PROBE / [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p13_20-c7_50 | 0.79751562499999995 | 0.79751562499999995 | 0 | 0 | IMMEDIATE / [4, 6, 4, 4, 4, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c9_100 | 0.81380859375000003 | 0.79898046874999995 | 0.014828125000000039 | -0.049335937499999996 | PROBE / [6, 8, 6, 2, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c7_50 | 0.79360937499999995 | 0.79360937499999995 | 0 | 0 | IMMEDIATE / [6, 8, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| SEVERED-p13_20-c9_100 | 0.79409765624999995 | 0.79409765624999995 | 0 | 0 | IMMEDIATE / [6, 4, 4, 2, 4, 4, 6] | IMMEDIATE / 4 |
| SEVERED-p13_20-c7_50 | 0.79067968749999995 | 0.79067968749999995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 6, 4, 6] | IMMEDIATE / 4 |
| SEVERED-p17_20-c9_100 | 0.79507421874999995 | 0.79507421874999995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 6, 4, 6] | IMMEDIATE / 4 |
| SEVERED-p17_20-c7_50 | 0.79287695312499995 | 0.79287695312499995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 6, 4, 4, 4] | IMMEDIATE / 4 |

### Seed 6602: COMPLETE, recorded branch RM-A

Fresh admission `2026-09-07T19:08:49.160077Z`: physical/effective available **15668584448 / 15668584448 bytes**, both pass 4 GiB.
External `whole_wall_seconds=4.71 peak_rss_kib=20856`; runner wall 4.6286776349879801 s.

| Paired endpoint | Mean | Conditional MC SE |
| --- | ---: | ---: |
| delta_native | 0.0029493001302083339 | 0.00056417739281877741 |
| delta_information | 0.0029493001302083339 | 0.00056417739281877741 |
| blind_minus_immediate | 0 | 0 |

| Phase/policy | Episodes | Transitions | Probe episodes | Committed period units | Probe time units |
| --- | ---: | ---: | ---: | ---: | ---: |
| training | 131072 | 655360 | 65536 | 589958 | 131072 |
| FULL | 32768 | 90112 | 4096 | 130932 | 8192 |
| BLIND | 32768 | 65536 | 0 | 131072 | 0 |
| IMMEDIATE-4 | 32768 | 65536 | 0 | 131072 | 0 |

| Fitted component | Entries / occupied | Updates | Displacement L2 | Maximum movement |
| --- | --- | ---: | ---: | ---: |
| shared_immediate | 8 / 8 | 65536 | 2.2529880157051223 | 0.80606054687500328 |
| full | 224 / 224 | 65536 | 9.9367973315066429 | 0.92528753180661605 |
| blind | 32 / 32 | 65536 | 3.7145716417218666 | 0.75817934871543036 |

Initial L2 is zero, first observation step is 1; histogram increments 65536, occupied bins 56. No finite relative movement ratio to zero is reported.

| Policy | Mean return | Mean paid component | Probe frequency |
| --- | ---: | ---: | ---: |
| FULL | 0.79677229817708328 | -0.006362711588541666 | 0.125 |
| BLIND | 0.79382299804687495 | 0 | 0 |
| IMMEDIATE-4 | 0.79382299804687495 | 0 | 0 |

All context outcomes, including losses, and final plans follow. BLIND and IMMEDIATE-4 coincide throughout, with no acquisition or paid component; their difference is zero, and native/information contrasts coincide. IMMEDIATE-4 always chooses period 4. FULL tails correspond to displayed counts 0 through 6; unexecuted tail plans remain plans only.

| Context | FULL return | BLIND / IMMEDIATE-4 return | Native / information difference | FULL paid mean | FULL root / tails | BLIND root / tail |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| LINKED-p13_20-c9_100 | 0.79556249999999995 | 0.79556249999999995 | 0 | 0 | IMMEDIATE / [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p13_20-c7_50 | 0.79531835937499995 | 0.79531835937499995 | 0 | 0 | IMMEDIATE / [6, 8, 6, 4, 4, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c9_100 | 0.80304361979166661 | 0.77944921874999995 | 0.023594401041666671 | -0.050901692708333328 | PROBE / [6, 6, 6, 2, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c7_50 | 0.79434179687499995 | 0.79434179687499995 | 0 | 0 | IMMEDIATE / [6, 8, 8, 4, 2, 2, 2] | IMMEDIATE / 4 |
| SEVERED-p13_20-c9_100 | 0.79678320312499995 | 0.79678320312499995 | 0 | 0 | IMMEDIATE / [6, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p13_20-c7_50 | 0.79824804687499995 | 0.79824804687499995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p17_20-c9_100 | 0.79287695312499995 | 0.79287695312499995 | 0 | 0 | IMMEDIATE / [2, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p17_20-c7_50 | 0.79800390624999995 | 0.79800390624999995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 2, 4, 4, 4] | IMMEDIATE / 4 |

## Technical acceptance and next owner

CM parsed existing JSON only: exact seed/object/source, terminal exit, fresh admission, selected batch/cost
and evaluation counts, full row/update/histogram totals, finite 264-value inventory, complete eight-context
three-policy endpoint coverage, and paired aggregate means/SE from saved context moments agree. Each dataset
has 229376 total episodes and 196608 scalar updates; no source or endpoint was changed after output.
Both required datasets are technically complete. These checks establish conformance, not a scientific
explanation or stable superiority. DM owns the two-seed average, sample SD, conditional MC SE, branch,
prediction scoring and comparison with retained prior evidence; B02/B03 are excluded from this primary.

Original outputs remain under `/home/wu/hmasd-worktrees/ucope-shared-return-b04-20260907/temp/directions/ucope/exp/shared-data-return-b04-seed<seed>/`.
Local collection is `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/exp/shared-data-return-b04-seed<seed>/`.
Each root retains `summary.json`, `resource_admission.json`, full combined `supervisor.log`, authoritative
`status.json` and verbatim `whole_time.txt`. Summaries preserve complete fitted values/counts, plans,
context moments and costs. Original supervisor records remain in `/home/wu/.agent-tasks/<handle>/`.

No live process or technical dependency remains. Root integrates the prospective binding and collection
before original DM joint scientific intake/Chinese brief. CM returns shared checkout writer ownership
to DM at delivery. No additional invocation is authorized by this evidence.
