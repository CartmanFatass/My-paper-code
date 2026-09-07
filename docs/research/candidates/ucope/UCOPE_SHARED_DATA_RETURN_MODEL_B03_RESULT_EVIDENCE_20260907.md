# UCOPE shared-data return model B03: technical and execution evidence

## Contract and accepted implementation

P08-UCOPE-TWO-DATASETS-01; [frozen card sections 2–5](UCOPE_SHARED_DATA_RETURN_MODEL_B03_SCIENCE_CARD_20260907.md).
Source: `af7c7d516bbd9466a2775d9cb1e29582be1aaa36`, pushed on `codex/ucope`.
Explicit seed arguments now reach private collection RNG, training ancestry and final paired evaluation.
B02 family literal and default seed 6401 remain unchanged. B03 has its own result identity.
The four native host modules, binary64 update order, budgets and observation boundary are unchanged.
Owned source changes: B02 `model.py`, `evaluation.py`, `scripts/run_ucope_shared_data_return_model_b02.py`; B03 script; focused B02/B03 tests.
Source delta 37 additions/14 deletions (new runner 23 lines); tests 79 additions/1 deletion.
ENGINEERING_SCOPE_SPEC section 4 additions: none; ordinary argument plumbing only.

## Focused acceptance and post-learner coverage

Two focused synthetic tests passed in 0.56 s (existing cache_dir warning only):

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider tests/experiments/candidates/ucope/shared_data_return_model_b03/test_seed_binding.py tests/experiments/candidates/ucope/shared_data_return_model_b02/test_shared_return.py::test_synthetic_changed_path_and_publication --basetemp temp/directions/ucope/test/shared-return-b03-synthetic-01
```

They check independent private streams, both selected training/evaluation ancestry bindings, fresh states,
unchanged default 6401 and compact summary publication. All host calls are synthetic: zero scientific exposure.
Independent affected-path review by the reused `review_ah_ucope_b01` reviewer found no material issue;
it inspected five saved synthetic summaries without repeating execution. Existing native host/rule checks
are reused. These checks establish the seed/publication contract, not empirical performance.

## Prospective execution record (before either result)

Exactly seed 6501 followed by seed 6502 after terminal reconciliation, irrespective of first valid score.
Per-arm cost projection: same complete-path B02 shape, 7.73 s/dataset; 15.46 s summed.
Complete cost law and exposures are card section 4. No fresh calibration or scientific smoke was run.
Each cap is 600 s including fresh admission, interpreter, learner, final evaluation, publication and exit;
1200 s summed cap. Study critical path additionally includes control/staging intervals. Aggregate CPU is
unmeasured; single scientific process/compute thread, CPU Python binary64. Remote only; no local fallback.

Node `wsl_4070`, SSH `hmasd-wsl-node`; interpreter `/home/wu/.venvs/hmasd/bin/python`.
Detached exact-source cwd `/home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907`.
Full-history named-reference Git bundle/SCP stages the committed source; no live source copying.
Handles: `ucope-shared-return-b03-seed6501-20260907`, `ucope-shared-return-b03-seed6502-20260907`.
Supervisor log for each is `/home/wu/.agent-tasks/<handle>/task.log`.
Output roots are `temp/directions/ucope/exp/shared-data-return-b03-seed<seed>/` beneath that cwd;
each has its own adjacent `resource_admission.json` and `summary.json`.
Stop at terminal success/failure/600 s. No third seed or retry is authorized. A shared primary defect
or failed admission returns an execution gap; all partial evidence is retained.

Exact supervisor command arguments, passed as one remote shell string via SSH:

### Seed 6501

```sh
/usr/local/bin/agent-task run ucope-shared-return-b03-seed6501-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b03-seed6501/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b03.py --seed 6501 --out temp/directions/ucope/exp/shared-data-return-b03-seed6501'"'"''
```

### Seed 6502

```sh
/usr/local/bin/agent-task run ucope-shared-return-b03-seed6502-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b03-seed6502/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b03.py --seed 6502 --out temp/directions/ucope/exp/shared-data-return-b03-seed6502'"'"''
```

## Terminal collection

Exactly two invocations were accepted, in selected order; both finished with exit code 0.
Seed 6501 was terminal and its saved primary/counts reconciled before seed 6502 was dispatched.
No pilot, replay, retry, third seed or extra evaluation was executed. Both source identities are
`af7c7d516bbd9466a2775d9cb1e29582be1aaa36`. Root was sent each accepted handle and terminal facts;
CM observed both to terminal before adoption was necessary. Terminal source checkout remained clean.

The external whole times sum to **18.46 s**, against the 1200 s summed and 600 s individual caps.
The observed study interval from first admission to second exit was about 90 s including control/collection;
source staging was earlier. Aggregate CPU and scratch peak are unmeasured. The raw runner retains
`resources_unmeasured`; external whole wall and peak RSS are measured below and do not fill scratch/CPU.
No missing optional resource value limits this native-return comparison.

### Seed 6501: COMPLETE, recorded branch RM-A

Admission at `2026-09-07T17:47:01.749948Z`: physical/effective available **15666896896 / 15666896896 bytes**, both pass 4 GiB.
External `whole_wall_seconds=8.00 peak_rss_kib=20960`; runner wall 7.9078076899750158 s.

| Paired endpoint | Mean | Conditional MC SE |
| --- | ---: | ---: |
| delta_native | 0.0033094889322916716 | 0.00057048590059409542 |
| delta_information | 0.0033094889322916716 | 0.00057048590059409542 |
| blind_minus_immediate | 0 | 0 |

| Phase/policy | Episodes | Transitions | Probe episodes | Committed period units | Probe time units |
| --- | ---: | ---: | ---: | ---: | ---: |
| training | 262144 | 1310720 | 131072 | 1180154 | 262144 |
| FULL | 32768 | 90112 | 4096 | 132966 | 8192 |
| BLIND | 32768 | 65536 | 0 | 131072 | 0 |
| IMMEDIATE-4 | 32768 | 65536 | 0 | 131072 | 0 |

| Fitted component | Entries / occupied | Updates | Displacement L2 | Maximum movement |
| --- | --- | ---: | ---: | ---: |
| shared_immediate | 8 / 8 | 131072 | 2.2410312731767577 | 0.79702734374999851 |
| full | 224 / 224 | 131072 | 9.9177599495857418 | 0.9183809523809523 |
| blind | 32 / 32 | 131072 | 3.7197132332147977 | 0.74729409841425731 |

Initial L2 is zero; first observation step is 1; histogram increments 131072, occupied bins 56. A relative movement ratio to zero is undefined.

| Policy | Mean return | Mean paid component | Probe frequency |
| --- | ---: | ---: | ---: |
| FULL | 0.79588126627604161 | -0.0061946614583333328 | 0.125 |
| BLIND | 0.79257177734374995 | 0 | 0 |
| IMMEDIATE-4 | 0.79257177734374995 | 0 | 0 |

All context results and learned root/tail plans follow. BLIND and IMMEDIATE-4 coincide in every context (zero paid component/probes), so information and native differences coincide. IMMEDIATE-4 always chooses period 4.

| Context | FULL return | BLIND / IMMEDIATE-4 return | Native / information difference | FULL paid mean | FULL root / tail periods | BLIND root / tail period |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| LINKED-p13_20-c9_100 | 0.80483984374999995 | 0.80483984374999995 | 0 | 0 | IMMEDIATE / [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p13_20-c7_50 | 0.79483007812499995 | 0.79483007812499995 | 0 | 0 | IMMEDIATE / [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c9_100 | 0.81300520833333334 | 0.78652929687499995 | 0.026475911458333373 | -0.049557291666666663 | PROBE / [6, 8, 6, 6, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c7_50 | 0.79214453124999995 | 0.79214453124999995 | 0 | 0 | IMMEDIATE / [6, 8, 6, 2, 2, 2, 2] | IMMEDIATE / 4 |
| SEVERED-p13_20-c9_100 | 0.78677343749999995 | 0.78677343749999995 | 0 | 0 | IMMEDIATE / [6, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p13_20-c7_50 | 0.79409765624999995 | 0.79409765624999995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p17_20-c9_100 | 0.79141210937499995 | 0.79141210937499995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p17_20-c7_50 | 0.78994726562499995 | 0.78994726562499995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |

### Seed 6502: COMPLETE, recorded branch RM-A

Admission at `2026-09-07T17:48:21.606275Z`: physical/effective available **15664783360 / 15664783360 bytes**, both pass 4 GiB.
External `whole_wall_seconds=10.46 peak_rss_kib=21068`; runner wall 8.4417680469923653 s.

| Paired endpoint | Mean | Conditional MC SE |
| --- | ---: | ---: |
| delta_native | 0.0015751139322916715 | 0.00051655307453576634 |
| delta_information | 0.0015751139322916715 | 0.00051655307453576634 |
| blind_minus_immediate | 0 | 0 |

| Phase/policy | Episodes | Transitions | Probe episodes | Committed period units | Probe time units |
| --- | ---: | ---: | ---: | ---: | ---: |
| training | 262144 | 1310720 | 131072 | 1179370 | 262144 |
| FULL | 32768 | 90112 | 4096 | 132686 | 8192 |
| BLIND | 32768 | 65536 | 0 | 131072 | 0 |
| IMMEDIATE-4 | 32768 | 65536 | 0 | 131072 | 0 |

| Fitted component | Entries / occupied | Updates | Displacement L2 | Maximum movement |
| --- | --- | ---: | ---: | ---: |
| shared_immediate | 8 / 8 | 131072 | 2.2497513090224315 | 0.79855322265624951 |
| full | 224 / 224 | 131072 | 9.9493435747729144 | 0.90732060461416142 |
| blind | 32 / 32 | 131072 | 3.7272074008063214 | 0.74357938013915281 |

Initial L2 is zero; first observation step is 1; histogram increments 131072, occupied bins 56. A relative movement ratio to zero is undefined.

| Policy | Mean return | Mean paid component | Probe frequency |
| --- | ---: | ---: | ---: |
| FULL | 0.79576432291666666 | -0.0062447102864583324 | 0.125 |
| BLIND | 0.79418920898437495 | 0 | 0 |
| IMMEDIATE-4 | 0.79418920898437495 | 0 | 0 |

All context results and learned root/tail plans follow. BLIND and IMMEDIATE-4 coincide in every context (zero paid component/probes), so information and native differences coincide. IMMEDIATE-4 always chooses period 4.

| Context | FULL return | BLIND / IMMEDIATE-4 return | Native / information difference | FULL paid mean | FULL root / tail periods | BLIND root / tail period |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| LINKED-p13_20-c9_100 | 0.79263281249999995 | 0.79263281249999995 | 0 | 0 | IMMEDIATE / [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p13_20-c7_50 | 0.79458593749999995 | 0.79458593749999995 | 0 | 0 | IMMEDIATE / [8, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c9_100 | 0.81182552083333337 | 0.79922460937499995 | 0.012600911458333372 | -0.049957682291666659 | PROBE / [6, 8, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| LINKED-p17_20-c7_50 | 0.79653906249999995 | 0.79653906249999995 | 0 | 0 | IMMEDIATE / [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE / 4 |
| SEVERED-p13_20-c9_100 | 0.79043554687499995 | 0.79043554687499995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p13_20-c7_50 | 0.79556249999999995 | 0.79556249999999995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 2, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p17_20-c9_100 | 0.79800390624999995 | 0.79800390624999995 | 0 | 0 | IMMEDIATE / [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |
| SEVERED-p17_20-c7_50 | 0.78652929687499995 | 0.78652929687499995 | 0 | 0 | IMMEDIATE / [6, 4, 4, 4, 4, 4, 4] | IMMEDIATE / 4 |

## Collection acceptance and handoff

CM parsed the saved JSON only: seed/object/source identity, terminal exit, admission, full batches,
behavior/episode/update counts, 264-entry inventory, finite fitted values/counts, complete eight-context
three-policy evaluation, and uniform-context paired means/SE recomputed from saved context moments agree.
No learner/host replay was needed. Each dataset has 360448 episodes, 393216 scalar value updates and
131072 histogram increments. Both complete selected primary outputs are present; technical acceptance
establishes conformance, not scientific generality. Per-dataset RM-A inputs are retained without pooling
prior seed 6401. DM owns the joint average, sample SD, conditional MC SE, prediction scoring and science.

Original outputs remain at `/home/wu/hmasd-worktrees/ucope-shared-return-b03-20260907/temp/directions/ucope/exp/shared-data-return-b03-seed<seed>/`.
Collected copies are at `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906/temp/directions/ucope/exp/shared-data-return-b03-seed<seed>/`.
For each seed retain `summary.json`, `resource_admission.json`, full combined `supervisor.log`,
authoritative `status.json` and verbatim `whole_time.txt`. Original supervisor directories are unchanged.
The summaries retain complete fitted values/counts, all final plans, counts, paired context moments and costs.

No technical dependency remains open and no process remains live. Root integrates the explicit CM source,
tests and this evidence; the original DM then authors joint intake and Chinese brief. This return supplies
no authorization for any further invocation. Shared direction checkout writer ownership returns to DM.
