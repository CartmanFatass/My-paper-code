# UCOPE B02 — execution and staging record

Current status under **P07-UCOPE-STAGE-REPAIR-02: the original sole invocation completed and is technically accepted**. The first section below preserves the earlier zero-exposure staging stop; the final section records the completed invocation.

**Staging failed; no scientific invocation was dispatched or accepted.** This ends only
Portfolio-directed action `P07-UCOPE-EXEC-01`, under Root's explicit instruction that any
staging failure ends the action without retry. The B02 implementation remains technically
accepted; this failure has no scientific polarity and does not consume a dataset or seed.

## Binding and direct facts

Root assigned committed source `bcd55750b29014e21dd855df5ac320296256b62e` and
[card §§1–5](UCOPE_SHARED_DATA_RETURN_MODEL_B02_SCIENCE_CARD_20260907.md), frozen at `c4687f6f2`.
The local source commit exists. Its B02 learner/evaluator/runner surface matches reviewed
`b44143f9e2c27543f19ce6cbc375918c51937a03` by Git comparison.

Assigned destination: `wsl_4070` / `hmasd-wsl-node`, interpreter
`/home/wu/.venvs/hmasd/bin/python`, prospective detached cwd
`/home/wu/hmasd-worktrees/ucope-shared-return-b02-seed6401-20260907`, prospective handle
`ucope-shared-return-b02-seed6401-20260907`. The planned single runner was
`scripts/run_ucope_shared_data_return_model_b02.py --seed 6401 --out
temp/directions/ucope/exp/shared-data-return-b02-seed6401`, with a complete 600 s cap including
admission and publication. Neither runner nor admission was called.

Initial supervisor/worktree checks returned `not_found` and `WORKTREE_ABSENT`. The remote
read-only command `git cat-file -t bcd55750b29014e21dd855df5ac320296256b62e` in
`/home/wu/projects/HMASD` triggered the partial clone's automatic lazy fetch. Process inspection
showed cat-file PID 2738866, fetch PID 2738869, remote-https PID 2738870 and transport PID 2738871
pending for more than 30 s without source-availability output. CM terminated those exact observed
probe processes and selected the already authorized committed bundle/SCP staging route.
This was not an experiment launch or acceptance ambiguity.

The first local bundle creation command, from `C:/Projects/HMASD`, was:

```text
git bundle create temp/directions/ucope/staging/ucope-b02-bcd55750b-20260907.bundle bcd55750b29014e21dd855df5ac320296256b62e ^a0b00f561159ddeedf66b65711cf3f7d2ec93b04
```

It returned **exit 1** with the exact error:

```text
fatal: Refusing to create empty bundle.
```

This is a direct source-staging engineering failure. No root-cause diagnosis beyond that
command/error is claimed. No amended bundle command, fetch retry, source substitution or
alternate device/budget was attempted after the failure. No SCP of source followed it.

Final authoritative remote readback remained:

```text
{"task": "ucope-shared-return-b02-seed6401-20260907", "status": "not_found"}
WORKTREE_ABSENT
BUNDLE_ABSENT
```

## Exposure and return boundary

Actual exposure: **0 scientific invocations, 0 real host episodes, 0 scalar updates,
0 evaluations, 0 resource admissions, 0 provider Sends**. No scientific result root or summary,
whole-process timing, learner stdout/stderr or accepted supervisor receipt exists. Staging and
read-only process time are not scientific wall consumption. No existing remote path/handle
was overwritten; committed source and prior technical evidence are unchanged.

Root was notified immediately of pending staging and of the terminal bundle failure. There is
no accepted handle to adopt and no live scientific process to collect. This record is the
technical return for the failed action, not a B02 result. Root returns these facts to Portfolio
for any separately supplied next command; CM selects no repair or retry in this action.

Changed path: this execution-return document only. ENGINEERING_SCOPE_SPEC §4 additions: none.

## P07-UCOPE-STAGE-REPAIR-02 continuation and exact launch record

Root relayed Portfolio's new command superseding only the ended P07-UCOPE-EXEC-01 staging
stop, while preserving the zero-exposure record above (integrated as `688f4f70e`). Reversible
local named-ref bundle/SCP/import repairs are authorized; the original sole seed, scientific
source, device and complete 600 s budget are unchanged. No remote HTTPS probe was used in
this continuation. The runner seed argument below is the separate argv `--seed 6401`.

Reconciliation found the original supervisor handle `not_found`, the intended worktree absent,
and the new transfer path absent. CM created local named ref
`refs/hmasd/ucope-b02-stage-repair-02-source-20260907` at `bcd55750b29014e21dd855df5ac320296256b62e`.
Full-history bundle creation and local verification succeeded:

```text
git bundle create temp/directions/ucope/staging/stage-repair-02/source.bundle refs/hmasd/ucope-b02-stage-repair-02-source-20260907
git bundle verify temp/directions/ucope/staging/stage-repair-02/source.bundle
```

The bundle is 94,127,192 bytes and advertises the exact assigned SHA. SCP placed it at the
previously absent `/home/wu/hmasd-inputs/ucope-b02-stage-repair-02-bcd55750b.bundle`. Remote
`git bundle verify` succeeded; `git fetch` from that local bundle imported the named ref;
`git worktree add --detach` created the originally assigned cwd. Its `rev-parse HEAD` is
`bcd55750b29014e21dd855df5ac320296256b62e` and `git status --short` is empty.
No uncommitted code or source change was staged. The prior failed bundle/path was not reused.

### Exact sole invocation, frozen before dispatch

The following exact SSH remote command supplies one command-string argument to the existing
`agent-task` supervisor. Its noninteractive, no-profile Bash process includes admission inside
the external timeout and whole-process timing. Fresh same-node memory admission requires both
physical/effective availability >=4 GiB and is adjacent via `&&` to the runner. No result root,
admission, scientific process or accepted handle exists at this record freeze.

```sh
/usr/local/bin/agent-task run ucope-shared-return-b02-seed6401-20260907 '/usr/bin/time -f '"'"'whole_wall_seconds=%e peak_rss_kib=%M'"'"' /usr/bin/timeout --signal=KILL 600s /bin/bash --noprofile --norc -c '"'"'cd /home/wu/hmasd-worktrees/ucope-shared-return-b02-seed6401-20260907 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/ucope/exp/shared-data-return-b02-seed6401/resource_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_ucope_shared_data_return_model_b02.py --seed 6401 --out temp/directions/ucope/exp/shared-data-return-b02-seed6401'"'"''
```

`--signal=KILL 600s` enforces the complete cap without extra scientific allowance. The supervisor
retains complete stdout/stderr, exit and start/end witnesses. GNU time's final line records whole
wall and peak RSS in that same log, covering admission, Python startup/import, streamed fit, all
three final evaluations, both summary writes and exit. Existing partial files and logs stay in
place on failure; no scientific retry or resume is authorized. No local fallback or extra seed,
pilot, smoke, provider Send or new machinery is selected.

The card's cost law remains `T_init + 1024*T_batch256_shared_fit +
32768*T_three_policy_eval + T_publish`; real-host coefficients remain unmeasured. No B01 or
synthetic timing is substituted, and no new measurement prerequisite is imposed. Required
publication coverage is the accepted B02 synthetic complete/partial check and affected-path
review; they are not repeated at launch. Actual whole wall, counts, learned exposure and primary
outputs will be collected from this one handle. Aggregate CPU remains unmeasured by this command.

This continuation/command record is committed and pushed before dispatch. CM sends the accepted
handle and exact node/source/cwd/log/result/receipt paths to Root immediately, observing until
adoption ACK or terminal fact. Root owns adopted observation; CM owns terminal collection and
technical acceptance; the original DM owns scientific intake, and Portfolio receives the return.

## Sole B02 invocation: terminal collection and technical acceptance

Command record `fddc126fd` was committed and pushed before dispatch. Immediately before launch, the original handle was still `not_found` and the result root absent. CM dispatched the exact command once; native supervisor acceptance returned exit 0 and started tmux `agent_ucope-shared-return-b02-seed6401-20260907`. No scientific retry, pilot, additional seed, local fallback or source change occurred.

The same-handle terminal read returned `finished`, exit **0**, PID **2741107**, tmux inactive. The supervisor log starts at **2026-09-07T15:39:44Z** and ends at **2026-09-07T15:39:52Z** (8 s rounded duration). Root received the accepted-handle packet immediately; completion preceded adoption ACK. Root recorded/ACKed terminal delivery under tracking commit `09091e3fc`, with its shared heartbeat remaining ACTIVE. No scientific process remains live.

### Resource and cap observations

Fresh admission at **2026-09-07T15:39:44.574164Z** passed physical and effective availability of **15,668,400,128 bytes**, each above 4 GiB. GNU time reports **whole_wall_seconds=7.73**, **peak_rss_kib=21440**. The outer timeout enclosed no-profile Bash, admission, interpreter/import startup, streamed collection/both fits, all three evaluations, both summary writes and exit. It did not fire. Whole invocation and summed scientific wall are both **7.73 s**, below the single complete 600 s cap. No cleanup or extra compute allowance was consumed.

The runner's internal **7.6646056 s** excludes preflight/interpreter startup and its final refresh write; external wall covers them. The rounded 8 s supervisor interval is a scheduling observation, not extra CPU work. Aggregate CPU is unmeasured by the frozen command. Source bundle creation/transfer and prelaunch agent/commit intervals are staging overhead, not scientific invocation time; no staging cost is silently added to the learned dataset. The numeric cost coefficients were unknown before launch, and no B01 or synthetic timing was substituted.

The summary retains `resources_unmeasured` because it does not ingest the external RSS line. That label is preserved; the direct whole-process wall/RSS facts above remain available. The frozen non-resource primary claim has no missing required resource measurement.

### Dataset, exposure and endpoint completeness

Summary status is **COMPLETE**, seed **6401**, independent datasets **1**, launch SHA **bcd55750b29014e21dd855df5ac320296256b62e**. Runtime reports Python 3.10.21, float mantissa 53 bits, CPU and one compute thread. The shared streaming dataset remains one learning unit, although it fits two policies.

| Stage / policy | Episodes | Probes | Host-event transitions | Committed period units | Probe time units |
| --- | ---: | ---: | ---: | ---: | ---: |
| training shared by both fits | 262144 | 131072 | 1310720 | 1181190 | 262144 |
| FULL | 32768 | 4096 | 90112 | 132718 | 8192 |
| BLIND | 32768 | 0 | 65536 | 131072 | 0 |
| IMMEDIATE-4 | 32768 | 0 | 65536 | 131072 | 0 |
| **Total** | **360448** | **135168** | **1531904** | **1576052** | **270336** |

All 1,024 batches completed. Training used 262,144 behavior uniforms, with 131,072 paid and 131,072 immediate episodes. The 393,216 scalar value updates comprise 131,072 full, 131,072 blind and 131,072 once-only shared-immediate updates; histogram increments total 131,072. These are incremental scalar updates, not optimizer steps. All eight contexts have 4,096 paired indices for all three final policies.

| Component | Value entries / occupied | Scalar updates | Initial L2 | Displacement L2 | Maximum absolute movement |
| --- | --- | ---: | ---: | ---: | ---: |
| full | 224 / 224 | 131072 | 0.0 | 9.9484771134191 | 0.91089247311828 |
| blind | 32 / 32 | 131072 | 0.0 | 3.72939480791767 | 0.751061813412036 |
| shared_immediate | 8 / 8 | 131072 | 0.0 | 2.24467922935158 | 0.798797363281247 |

All 56 histogram bins were occupied. Occupancy is reported exposure, not a sampling prerequisite or retrospective validity gate. Initial value scale is zero, so no finite relative-displacement ratio is reported.

### Recorded primary measurements and final actions

| Paired difference | Uniform-context mean | Conditional MC SE |
| --- | ---: | ---: |
| delta_native | 0.0030012207031250046 | 0.00055331390870418866 |
| delta_information | 0.0030012207031250046 | 0.00055331390870418866 |
| blind_minus_immediate | 0 | 0 |

The runner reports **RM-A**. Both measured means exceed 0.001 and FULL has 4,096 actual evaluation probes. This records the implemented rule and its inputs; DM owns scientific intake, prediction scoring, uncertainty interpretation and any next-object selection. The conditional SE describes evaluation noise for this single fitted dataset and is not training-seed uncertainty.

| Policy | Mean native return | Probe frequency | Mean paid component |
| --- | ---: | ---: | ---: |
| FULL | 0.79569506835937498 | 0.125 | -0.0062890624999999995 |
| BLIND | 0.79269384765624995 | 0 | 0 |
| IMMEDIATE-4 | 0.79269384765624995 | 0 | 0 |

All context outcomes are retained below. BLIND and IMMEDIATE-4 have zero paid components and zero probes in every context; BLIND-minus-IMMEDIATE-4 is zero throughout.

| Context | FULL mean | BLIND mean | IMMEDIATE-4 mean | Native difference | Information difference | FULL mean paid component |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| LINKED-p13_20-c9_100 | 0.79360937499999995 | 0.79360937499999995 | 0.79360937499999995 | 0 | 0 | 0 |
| LINKED-p13_20-c7_50 | 0.80313085937499995 | 0.80313085937499995 | 0.80313085937499995 | 0 | 0 | 0 |
| LINKED-p17_20-c9_100 | 0.81029492187499996 | 0.78628515624999995 | 0.78628515624999995 | 0.024009765625000037 | 0.024009765625000037 | -0.050312499999999996 |
| LINKED-p17_20-c7_50 | 0.79531835937499995 | 0.79531835937499995 | 0.79531835937499995 | 0 | 0 | 0 |
| SEVERED-p13_20-c9_100 | 0.79238867187499995 | 0.79238867187499995 | 0.79238867187499995 | 0 | 0 | 0 |
| SEVERED-p13_20-c7_50 | 0.79141210937499995 | 0.79141210937499995 | 0.79141210937499995 | 0 | 0 | 0 |
| SEVERED-p17_20-c9_100 | 0.78872656249999995 | 0.78872656249999995 | 0.78872656249999995 | 0 | 0 | 0 |
| SEVERED-p17_20-c7_50 | 0.79067968749999995 | 0.79067968749999995 | 0.79067968749999995 | 0 | 0 | 0 |

FULL acquires only in LINKED-p17_20-c9_100. Its native/information paired sample variance in that context is 0.080257032274708318; both are zero in every other context. These measurements follow final-only evaluation, with no retained-policy or intermediate-checkpoint selection.

Final learned plans (FULL tail columns correspond to displayed counts 0 through 6; BLIND tail ignores the current count):

| Context | FULL root | FULL tail periods | BLIND root | BLIND tail period |
| --- | --- | --- | --- | ---: |
| LINKED-p13_20-c9_100 | IMMEDIATE | [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE | 4 |
| LINKED-p13_20-c7_50 | IMMEDIATE | [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE | 4 |
| LINKED-p17_20-c9_100 | PROBE | [8, 6, 6, 4, 2, 2, 2] | IMMEDIATE | 4 |
| LINKED-p17_20-c7_50 | IMMEDIATE | [6, 6, 6, 4, 2, 2, 2] | IMMEDIATE | 4 |
| SEVERED-p13_20-c9_100 | IMMEDIATE | [4, 4, 4, 4, 4, 4, 4] | IMMEDIATE | 4 |
| SEVERED-p13_20-c7_50 | IMMEDIATE | [2, 4, 4, 4, 4, 4, 4] | IMMEDIATE | 4 |
| SEVERED-p17_20-c9_100 | IMMEDIATE | [4, 4, 6, 4, 4, 4, 4] | IMMEDIATE | 4 |
| SEVERED-p17_20-c7_50 | IMMEDIATE | [4, 4, 6, 4, 4, 4, 4] | IMMEDIATE | 4 |

The fixed reference always chooses IMMEDIATE-4. Tail plans are retained even where the final root does not probe; those entries are not additional executed episodes.

### Collection evidence and next owner

Original remote artifact root: `/home/wu/hmasd-worktrees/ucope-shared-return-b02-seed6401-20260907/temp/directions/ucope/exp/shared-data-return-b02-seed6401/`. Collected local root: `C:/Projects/HMASD-worktrees/cm-ucope-shared-data-return-b02-20260907/temp/directions/ucope/exp/shared-data-return-b02-seed6401/`. Both original outputs (`summary.json`, `resource_admission.json`) are retained. Local collection also preserves complete combined stdout/stderr as `supervisor.log`, authoritative `supervisor_status.json` and the verbatim external time/RSS line as `whole_time.txt`. Original supervisor records remain under `/home/wu/.agent-tasks/ucope-shared-return-b02-seed6401-20260907/`.

CM parsed the existing JSON only, with no host execution or learner replay: exact seed/source/status, one dataset, complete batch and behavior counts, both fits/shared-immediate update totals, value/count inventory and finiteness, occupied-entry totals, histogram total, complete eight-context three-policy endpoint counts, per-policy transitions/probes, and aggregate paired means/SE recomputed from saved context moments all agree. Admission, terminal status and complete-process cap readback agree. This establishes technical completeness of the selected output path, not a scientific causal explanation.

No technical dependency remains incomplete and no further invocation is authorized by this result. Root integrates/pushes this evidence and routes the accepted collection to the original UCOPE DM; DM performs scientific intake and returns through Root to Portfolio. Source and prior zero-exposure evidence remain unchanged.
