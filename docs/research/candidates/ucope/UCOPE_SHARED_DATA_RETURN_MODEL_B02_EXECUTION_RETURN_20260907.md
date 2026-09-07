# UCOPE B02 — P07-UCOPE-EXEC-01 staging return

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
