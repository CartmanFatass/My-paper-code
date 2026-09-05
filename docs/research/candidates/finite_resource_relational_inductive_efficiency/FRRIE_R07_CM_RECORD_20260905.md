# FRRIE R07 CM record — 2026-09-05

Status: TERMINAL_COLLECTED / TECHNICALLY_CONFORMANT / R07_N15_WITHIN_MEI.
One scientific invocation; running observations below are historical. DM owns intake.

Original runner SystemExit(0), complete publication and separate supervisor exit0
observed at2026-09-05T10:45:16Z. Start10:30:13Z gives903supervisor seconds,
not later906s observer uptime. Fixed debugger re-entry stopped at scriptline1
before a second computation. Runner844.9199158800038s; PHY150.0812525627989s,
EDGE149.90698258804332s; peak RSS614817792bytes. All22 completion checks pass,
128 paired updates/18cells/256curve rows/8checkpoint states complete.
Actual initial clip count3 at[3,5,14]; separately firstcontact0.
Technical branch R07_N15_WITHIN_MEI, N9within-MEI. Full evidence and limits are
in FRRIE_R07_RESULT_20260905.md and unchanged RESULT_EVIDENCE JSON.
No new code/test/invocation at collection; DM next selection remains pending.

## Frozen contract and exact source

Card FRRIE_R07_SECOND_ROOT_SCIENCE_CARD_20260905.md at DM c44f7f9,
integrated/pushed CM2046ee352. Baseline accepted R06 source72b1bd001.
Exact launch source **10ae9781f74ae26931fa8231918844f4921b80f2**, pushed on
codex/cm-frrie-r04-diagnosis-20260904, byte-identical owned surfaces to reviewed
implementer dd76f3e23. Independent reviewer and CM found no material issue.

Numeric seed2 is bound before evaluation/initialization/training to literal
0000000000000000000000000000000000000000000000000000000000000002,
label FRRIE-B07-CONTACT-BLOCK-002, object
FRRIE-B01-CONTACT-R128-LR003-R07-SECOND-ROOT-20260905.
Inside the fixed seed==2 branch, 064x formatting encodes this exact integer;
no random generation, selection, old packet slot or generic seed service.
Both actual Adam LRs0.003 precede initial audit/projection, no schedule.
Old R02/R06 seed1/root/defaults/exact-five/contact0 rules remain.

CPU FP32/Torch1/native32,35513 paired parameters, boxes[-.04,.04]/[-1.5,1.5],
same information/RNG/address serialization/actions/recurrence/learner/evaluation,
full128 paired updates, N9/N15, all18 cells are preserved. Only new tape label
is added to the existing direction-local acceptance tuple. Shared trainer,
codec,RNG,collector,evaluator,checkpoint/native dynamics are untouched.
No previous native build/tape/model/checkpoint/result is reused.

Initial clip count is the actual inventory size. Separately, first contact is
0 when initial indices are nonempty, otherwise first changed post-Adam update
or null. Existing
trainer supplies later contact; independent initial inventory/update indices
reconstruct first-contact truth. Completion compares direct-clip/contact
predicates, never observed count echoed as expected. Zero activation never
stops the128updates. Six R07 branches use primary N15 with original MEI.005;
N9 remains fully reported. Scientific outcomes cannot be inferred from tests.

## Scope and pre-edit plan

Before editing CM/reviewer agreed the minimal seed binding/contact rule design.
Initial rough45–65 additions estimate was revised to about+90/-25=115,
32 orchestration27.83%; these were forecasts only.
Actual first candidate was+79/-17=96 production lines. Implementer counted33
orchestration; reviewer corrected missing binding predicate to **34/96=35.42%**.
Candidate was unaccepted and never run; no scientific polarity.

One genuinely different reduction removed8 constant/import indirection lines:
fixed root encoding/label in existing seed2 branch, literal tape label and
publisher identity. No science padding, copied runner, whitespace compression,
new guard or changed counting convention. Final measured **+72/-16=88**,
**26/88=29.545%** orchestration: module9,contact import1,execute signature2,
root selection2,identity1,seed publication2,CLI/forwarding6,tapes label2,binding1.
Production files: experiment34,semantics43,tapes2,newrunner9 changed lines.
New focused test137 lines; total+209/-16. Runner9,all hard size caps respected.
Scope:none. Only already-named optional fixed pdb exception telemetry is reused;
no new §4 machinery. Formal-sized publication-test coverage remains open.

## Exact focused check

Task frrie_r07_focused_10ae9781,PID1657509, same source on wsl_4070.
Detached cwd /home/wu/hmasd-worktrees/frrie-r07-check-10ae9781.
2026-09-05T10:29:11Z–10:29:22Z,11supervisor seconds,exit0;
**1 passed in10.15s**. At10:29:11.854312Z fresh actual-node admission measured
physical/effective12,893,884,416bytes. Admission && timeout120s configured Python
-m pytest -q -p no:cacheprovider, absolute --basetemp under cwd
temp/directions/finite_resource_relational_inductive_efficiency/test/r07_focused,
target tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r07/test_experiment.py.

This one check tests root binding at first evaluation-tape call before model
creation; zero/later/no-contact and incorrect inventories; six-branch
precedence, old defaults/branches; one actual module toy publisher. Frozen
seed2 binding is retained in toy execution; it is TEST_ONLY_NON_RESULT, not
scientific128 work. No native-return values were inspected for selection.
No repeated suite or additional test gate. Original log/exit witnesses live
at /home/wu/.agent-tasks/frrie_r07_focused_10ae9781/ and receipt under checkcwd.
Peak RSS for focused check unmeasured.

## Accepted scientific command and observation

Configured node wsl_4070/SSH hmasd-wsl-node,Python3.10.21 at
/home/wu/.venvs/hmasd/bin/python. Current integration compute read, reviews[].
Fresh detached cwd /home/wu/hmasd-worktrees/frrie-contact-r07-10ae9781 clean
before launch; Git preparation uses configured zsh login network shell.

```sh
/usr/local/bin/agent-task run frrie_b01_contact_r07_10ae9781 'cd /home/wu/hmasd-worktrees/frrie-contact-r07-10ae9781 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-contact-r07-10ae9781/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r07_admission.json && timeout --signal=TERM --kill-after=5s 28795s /home/wu/.venvs/hmasd/bin/python -m pdb -c continue -m scripts.run_frrie_b01_contact_r07 --output-root /home/wu/hmasd-worktrees/frrie-contact-r07-10ae9781/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r07 --admission-receipt /home/wu/hmasd-worktrees/frrie-contact-r07-10ae9781/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r07_admission.json --seed 2 < docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt'
```

Accepted2026-09-05T10:30:13Z,epoch1788604213,PID1657968.
At7seconds running/exit_code=null/tmux_active=true. Admission assessed
10:30:13.585327Z physical/effective12,896,010,240bytes, each>=4GiB.
This is admission, not observed peak/resource conformance.

Task/log witnesses /home/wu/.agent-tasks/frrie_b01_contact_r07_10ae9781/.
Output and receipt paths are literal in command. Original4h/arm cap retained;
TERM28795s+maximum5s grace stays within8h. Outerbound18:30:13Z.
Stop natural128,first original exception,or existing cap; no retry/successor.
The already verified pdb module route uses fixed q/EOF and may re-enter debugger
before first statement; no second computation. Original SystemExit/exception
must be read independently of debugger exit0. SIGINT differs; timeout usesTERM.

## Prospective cost, exposure and handoff

Not a sweep. Cost655360 slots/arm,1316864 total. R06 same-node anchors:
PHY148.041537s,EDGE147.028060s;843.355731runner/895supervisor seconds,
peak614965248bytes. Shared work adds to arm attribution. Both arm projections
fit4h and total8h; this is no performance claim.
Exposure128*.003=.384,init half-range.05,nominal ratio7.68,tight half-width.04;
actual initial clip count/first contact will be published. Nominal exposure
is not a displacement bound. New runtime cost/result remains unobserved.

Tracker /root/tracker_tl_experiments directly ACKed exact task adoption; CM
released routine polling. DM /root/dm_amx_frrie_continue has handle/SHA/cwd/
output/receipt/bound. CM collects/accepts at terminal; DM interprets and selects.
Loss of observation never authorizes duplicate execution. Historicalr04/
attempt02 causes remain unresolved. No R08 or further repair selected.
