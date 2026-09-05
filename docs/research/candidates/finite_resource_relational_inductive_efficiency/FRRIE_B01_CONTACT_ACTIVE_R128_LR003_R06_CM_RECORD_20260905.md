# FRRIE R06 CM record — 2026-09-05

Status: ACCEPTED_RUNNING / TECHNICALLY_CONFORMANT / TRACKER_ADOPTED.
This is the single fresh R06 invocation. No scientific outcome is yet observed.

## Source and acceptance

Frozen card FRRIE_B01_CONTACT_ACTIVE_R128_LR003_R06_SCIENCE_CARD_20260904.md,
resume ef792027 and prospective module-layout overlay c2f421d8 govern this work.
CM integrated/pushed each historical and current document commit separately.
Exact source **72b1bd001f7aff4d383f7cbec296bed2edf675dd**, pushed CM branch
codex/cm-frrie-r04-diagnosis-20260904, matches reviewed implementer 2feb5676f.
Old unaccepted f0bfe7a import defect was reproduced separately in
FRRIE_R06_TECHNICAL_EVIDENCE_20260905.md; historical r04/attempt02 causes remain unresolved.

Independent reviewer and CM found no material defect in the final diff against
2ec53827d. Production +61/-18 =79 physical changed lines: experiment29,
semantics41, runner9. Orchestration23/79=29.11%: runner9, import replacement2,
execute LR parameter1, initialization selection/call replacement5, object identity
publication4, argparse1, main forwarding1. Tests119 lines, total additions180/
deletions18. No padding or copied science. Scope:none; no new §4 machinery.
The fixed existing pdb inspection input is already named exception telemetry.

The original main(argv) and public initializer export/default wrappers remain.
One fixed --lr003 flag supplies only selected Adam LR; module runner removes
manual sys.path bootstrap and redundant identity/prefix forwarding.
Both actual fresh optimizer LRs are set to0.003 before initial codec audit and
projection; initial/final per-arm LR is measured and classified. Original R02
defaults stay0.0003. Shared trainer/codec/RNG/tapes/collector remain unchanged.

Protected science: literal root
2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807,
seed1/FRRIE-B02-CONTACT-BLOCK-001, CPU FP32/thread1/native32,128 paired updates,
rawpaired35513 parameters, initial5 tight clips, PHY[-.04,.04]/EDGE[-1.5,1.5],
all original information/work/evaluation/projection-moment laws and first-match
branches/MEI0.005. No old tape/model/native build/checkpoint/results reused.

## Focused verification

Exact same72b1bd00 source, detached cwd
/home/wu/hmasd-worktrees/frrie-r06-check-72b1bd00.
Task frrie_r06_focused_72b1bd00, PID1649957,09:18:59Z–09:19:13Z,
14 supervisor seconds, exit0, pytest **1 passed in12.58s**.
Fresh actual-node admission09:19:00.000706Z physical/effective12,950,806,528bytes.
The command after admission was timeout120s configured Python -m pytest -q
-p no:cacheprovider, with absolute request-specific --basetemp under cwd
temp/directions/finite_resource_relational_inductive_efficiency/test/r06_focused,
target tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r06/test_experiment.py.
Admission and test were joined by && in existing agent-task. Test checked
defaults/export, actual LR pairing before initial projection, exposure, branch
precedence/mismatch, and real toy module-entry publisher. No repeated suite.
Original logs/receipt remain in that remote task/cwd. Peak RSS unmeasured.
Formal-sized end-to-end publication coverage remains an open engineering item.

Actual configured Python resolves to uv CPython3.10.21. Read-only stdlib
pdb.py inspection confirmed module mode uses _runmodule/code and the same main
quit/SystemExit/postmortem loop; relevant inner up2/up6 frames remain unchanged.
Existing fixed q/EOF stops terminal re-entry before another script computation;
pdb exit0 alone never proves learner success. SIGINT changes; timeout uses TERM.

## Exact accepted invocation

Node wsl_4070 / SSH hmasd-wsl-node / configured Python3.10.
Fresh detached cwd /home/wu/hmasd-worktrees/frrie-contact-r06-72b1bd00
was clean before launch. Accepted09:19:47Z, epoch1788599987, PID1650501;
at6seconds running, exit_code=null, tmux_active=true.
Admission09:19:47.084784Z physical/effective12,939,055,104bytes, both >=4GiB.

```sh
/usr/local/bin/agent-task run frrie_b01_contact_r06_72b1bd00 'cd /home/wu/hmasd-worktrees/frrie-contact-r06-72b1bd00 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-contact-r06-72b1bd00/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r06_admission.json && timeout --signal=TERM --kill-after=5s 28795s /home/wu/.venvs/hmasd/bin/python -m pdb -c continue -m scripts.run_frrie_b01_contact_r06 --output-root /home/wu/hmasd-worktrees/frrie-contact-r06-72b1bd00/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r06 --admission-receipt /home/wu/hmasd-worktrees/frrie-contact-r06-72b1bd00/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r06_admission.json --seed 1 < docs/research/candidates/finite_resource_relational_inductive_efficiency/FRRIE_R04_RECONSTRUCTION_A01_PDB_COMMANDS_20260904.txt'
```

Supervisor log/terminal witnesses:
 /home/wu/.agent-tasks/frrie_b01_contact_r06_72b1bd00/
Output/receipt paths are literal above. TERM28795s plus maximum5s grace
respects8h total; original4h directly attributed per-arm caps retained.
Outer bound2026-09-05T17:19:47Z. Stop natural complete128, first exception,
or existing deadline; no automatic retry or successor.

## Prospective cost, exposure and handoff

Not a sweep.655360 native slots/arm;1316864 total including shared uniform.
Same-node R05 anchors: PHY160.198718s, EDGE159.292060s;898.65runner seconds,
937supervisor seconds, peak615534592bytes. Shared work is additional; all
within unchanged4h/arm8h total planning caps. Admission is not peak-resource
conformance. Actual new runtime cost/peak remain unobserved.

Exposure: updates=128; adam_lr=0.003; nominal_lr_exposure=0.384;
init_half_range=0.05; nominal_exposure_over_init_half_range=7.68;
tight_box_half_width=0.04; initial_projection_changed_coordinates=5.
Nominal exposure is not measured displacement. Full native B curves/returns
and original R06 first-match interpretation are reserved for completed evidence.

Tracker /root/tracker_tl_experiments directly acknowledged adoption of the
exact task/SHA; routine polling released. DM /root/dm_amx_frrie_continue has
all identities, paths and bounds. CM retains terminal collection/engineering
acceptance; DM science intake. Loss of observation never authorizes relaunch.
No R07 or further repair is selected. Owner reviews were[] at current boundary.

