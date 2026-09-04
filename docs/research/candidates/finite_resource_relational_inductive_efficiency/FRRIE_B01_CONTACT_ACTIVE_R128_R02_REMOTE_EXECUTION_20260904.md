# FRRIE contact-active R128 R02 remote execution — 2026-09-04

Status: `TERMINAL_FAILURE_BEFORE_NATIVE_OR_LEARNER / NO_SCIENTIFIC_RESULT`. Engineering observation only.

The owner resumed automated research; Root/DM assigned the unchanged
`FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904` invocation. This supersedes the old drain pause
recorded in `FRRIE_B01_CONTACT_ACTIVE_R128_R02_REMOTE_DRAIN_BOUNDARY_20260904.md`.

## Contract and ownership

Run the existing real learner and evaluator at committed source
`36b538ba1b91eede9f528dd315fa624f8c1d53e5`. Preserve seed 1, literal root
`2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`, raw paired 35,513-parameter
initialization, five initially clipped tight coordinates, unchanged optimizer moments during
projection, CPU FP32 Adam 0.0003, 128 full-batch updates, `(9,15)*32` episodes per update,
INTACT evaluation at 0/32/64/128 with 256 episodes per roster/cell, and shared UNIFORM_LEGAL.
The treatment remains `PHY_TRUST_004` versus containing `EDGE_FLEX_150`. The science card's
first-match branches apply only after completion; no scientific inference follows from launch.
No checkpoint/resume, root substitution, outcome-sensitive stop, or source repair is assigned.

The scientific question is whether activated projection develops a 0.005 update-128 return gap
at both seen rosters. Competing explanations remain a small effect, beneficial or harmful generic
shrinkage, common K0 dominance, weak EDGE competence, and literal-root variation. Acceptance here
means one admitted invocation over unchanged source with observable supervisor ownership.

CM owns this receipt and request-local temporary evidence, in isolated local worktree
`C:/Projects/HMASD-worktrees/cm-frrie-r02-resume-20260904`, branch
`codex/cm-frrie-r02-resume-20260904`. DM owns scientific intake. No primary-checkout or source
edits are made. Engineering scope specification section 4 additions: none.

## Readiness and source facts

The existing implementation commit adds 1,268 non-test lines and 182 test lines. Its runner
implementation is 510 lines, with a 16-line entry point; no source is added in this execution
slice. Prior engineering acceptance is reused without another smoke.

The retained `contact-r02-real-smoke/test_frozen_projection_counts_0/result/summary.json` in
`C:/Projects/HMASD-worktrees/codex-frrie-dirty-intake-20260904/temp/directions/finite_resource_relational_inductive_efficiency/test/`
reports `TEST_ONLY_NON_RESULT`, completion true, one paired real update, 4,928 training slots
per arm, 768 factual transitions per arm, one backward/Adam step per arm, and 23.743083 s total.
It uses the separate test root. It establishes toy end-to-end publication, not the production
128-update outcome. Post-learner path coverage: toy publication was exercised; a formal-sized
end-to-end publication test is not recorded and remains an open engineering item. This invocation
does not follow a post-learner failure.

On the actual remote node, HEAD is the exact source SHA, `git status --porcelain=v1
--untracked-files=all` is empty, and the required source diff against HEAD is empty. The canonical
`git ls-tree -r HEAD -- experiments/candidates/finite_resource_relational_inductive_efficiency
scripts/hmasd_resource_preflight.py scripts/run_frrie_b01_contact_r02.py` listing contains 61 files
and reproduces SHA-256 `4f027476d4b051df3920a4902b74f39d0d26bb4550952708353b717b6e7fe34d`.
These are direct checkout facts, not new runner guards. The retained commit pack is already
materialized; no fetch or source transfer was needed.

Before submission, task `frrie_b01_contact_r02_36b538ba_01` was `not_found`, no matching runner
process existed, and the remote worktree's entire `temp/` directory was absent. The prior exact
output/admission paths were not discoverable in retained receipts. The assignment's fallback
path convention below is therefore fixed before invocation.

## Frozen command and bounds

Node: `wsl_4070` via SSH `hmasd-wsl-node`; detached existing `/usr/local/bin/agent-task` supervisor.
Working directory: `/home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba`.
Interpreter: `/home/wu/.venvs/hmasd/bin/python`. Host portability is prospective Linux/Windows
CPU FP32, preserving RNG/work/meaning without a cross-compiler bit-identity claim. This accepted
remote invocation will not be migrated or duplicated.

Exact successful supervisor command (single shell command argument; the first failed submission
used identical content with task-name suffix `_01`):

```sh
/usr/local/bin/agent-task run frrie_b01_contact_r02_36b538ba_02 'cd /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_frrie_b01_contact_r02.py --output-root /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02 --admission-receipt /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_admission.json --seed 1'
```

Fresh remote admission must pass physical and effective available memory of at least 4 GiB and
is immediately followed by the runner through `&&`. Stop condition is completion at update 128
and publication, or the existing technical/resource-cap stop; no salvage or automatic retry.
Caps remain 14,400 attributed seconds per arm and 28,800 seconds total.

Per-arm cost projection: the retained real toy measured PHY 3.3998224 s and EDGE 3.3123950 s
per 4,976 total slots. The runner's production law is 655,360 slots per arm, yielding about
447.771 s PHY and 436.256 s EDGE using those local toy rates. Both are below their own 14,400 s
cap. The card's same-shape prior anchor is about 383.3 s per arm and 2,017.96 s total. These are
planning estimates, not guarantees about this remote host; no arm is dropped.

Machine-generated before launch by importing the committed pure cost/exposure functions on the
remote node, without model/RNG/environment construction:

```text
training_slots_per_arm=630784; learned_evaluation_slots_per_arm=24576; total_slots_per_arm=655360;
shared_uniform_slots=6144; invocation_slots=1316864; optimizer_steps_per_arm=128;
evaluation_cells=18; evaluation_episodes=4608; factual_transitions_per_arm=98304
updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5
```

## Acceptance and handoff

The single submission of task `frrie_b01_contact_r02_36b538ba_01` was accepted at
2026-09-04T21:37:22Z, supervisor PID 73051, and terminated at the same second with exit 1.
Its preserved log at `/home/wu/.agent-tasks/frrie_b01_contact_r02_36b538ba_01/task.log` shows
`ModuleNotFoundError` for `scripts`, followed by `hmasd_platform`, in resource preflight.
The exact preflight argv was reproduced over the recorded SHA and failed identically before
writing an admission receipt. The learner command after `&&` never ran; the output root is absent.
This is a reproduced sparse-materialization failure, with no scientific output or polarity.

The retained sparse list selected the FRRIE subtree, preflight, and runner, but omitted the
preflight's committed dependency `scripts/hmasd_platform.py`. Exact SHA tracks its 2,599-byte blob
`eb54e7c31170ad14c903ba87e55b1a479416b51b`, already present in the remote object database.
The bounded repair was `git sparse-checkout add --no-cone /scripts/hmasd_platform.py`. Its
working-file Git hash now matches that blob; the source diff and full status remain empty.
No source bytes, scientific arguments, or numerical semantics were changed.

A fresh supervisor identity `frrie_b01_contact_r02_36b538ba_02` was confirmed `not_found`, with
both result root and admission path absent. DM selected the exact committed-dependency restoration
and unchanged fresh invocation as an owner-delegated technical decision, owner item
`20260904-frrie-011`. The failed supervisor identity and log remain untouched.

Task `_02` was accepted at 2026-09-04T21:39:23Z. At uptime 9 seconds, supervisor status was
`running`, PID 74125, `exit_code=null`, `tmux_active=true`. The exact learner argv above was
directly visible as PID 74130, parent 74125. Fresh node-local admission at
2026-09-04T21:39:23.278562Z passed: physical available and effective available were each
15,425,867,776 bytes; minimum was 4,294,967,296 bytes, measurement source `/proc/meminfo`,
both floor checks true, no failure reasons. Admission and runner were joined by `&&` in the
same supervisor command. A process snapshot reported RSS 334,696 KiB at nine seconds; this is
not peak RSS and does not establish full-run resource conformance.

The nine-second running observation above is historical. Before final handoff, `_02` was observed
terminal: exit 1, `tmux_active=false`, ending 2026-09-04T21:39:36Z after 13 supervisor seconds.
No production result exists. The exact retained task can be inspected with:

```sh
ssh hmasd-wsl-node '/usr/local/bin/agent-task status frrie_b01_contact_r02_36b538ba_02'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs frrie_b01_contact_r02_36b538ba_02 50'
```

Do not submit another task if observation is lost. Missing optional RSS is `resources_unmeasured`;
learner-instrumentation failure needs reproduction before classification. Admission is not proof
of runtime resource conformance, and child process acceptance is not scientific completion.


## Terminal tape-construction failure and bounded diagnostic

The `_02` traceback is in `experiment.py:156`, constructing evaluation tapes, through
`tapes.py:217` (uplink address), `_address` at line 181, and `validate` at line 71:

```text
for field, upper in bounds.items():
TypeError: '�' object is not iterable
```

The failure preceded `output_root.mkdir` (line 165), native build, uniform evaluation,
model/optimizer creation, and learner updates. Only the production admission receipt exists;
the result root and `summary.json` are absent. The literal source declares `bounds` as a dict,
so the error text alone does not establish a source defect, bytecode defect, native effect, or
host fault. None of those causes is claimed.

An address-only check called one legal uplink address's `validate()` 100,000 times on the same
remote source/interpreter and passed. It created no RNG, environment, or learner and did not
reproduce the failure. DM then explicitly assigned one bounded exact tape-expression diagnostic,
without a full runner or source edit.

Diagnostic task: `frrie_contact_r02_tape_diag_36b538ba_01`, same node/cwd/source/interpreter.
It executed fresh `admit-memory --out` with absolute path
`/home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_tape_diag_admission.json`,
joined by `&&` to `timeout 120 /home/wu/.venvs/hmasd/bin/python -c` with the following exact
Python payload. For SSH quoting, the actual `-c` argument was `exec(bytes.fromhex("<hex>"))`,
where `<hex>` is the lowercase UTF-8 hex encoding of this body, including its terminal newline;
the complete accepted shell command remains in the diagnostic supervisor's `runner.sh`.

```python
import time
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.tapes import evaluation_tape
from experiments.candidates.finite_resource_relational_inductive_efficiency.b01_contact_r02.semantics import ROOT_HEX, SEED_LABEL, ROSTERS
started=time.monotonic()
root=bytes.fromhex(ROOT_HEX)
seed_label=SEED_LABEL
eval_episodes=256
evaluation_tapes={roster:tuple(evaluation_tape(root,seed_label=seed_label,roster=roster,episode=episode) for episode in range(eval_episodes)) for roster in ROSTERS}
print({"tape_counts":{roster:len(tapes) for roster,tapes in evaluation_tapes.items()},"wall_seconds":time.monotonic()-started})
```

Diagnostic admission passed at 2026-09-04T21:42:31.649560Z with physical/effective available
13,165,150,208 bytes. It finished at 21:42:56Z, exit 0, 25 supervisor seconds. Output was
`{'tape_counts': {9: 256, 15: 256}, 'wall_seconds': 22.849624478003534}`. The exact production
root/rosters/256-episode tape expression therefore completed, but the original failure did not
reproduce. Source diff against the bound SHA remained empty. No pyc removal, native invocation,
interpreter replacement, or source modification was performed; none is implicated by direct
evidence.

The second failure remains an unclassified technical observation. There is no scientific result,
branch, contact observation, or learner evidence. All three supervisor tasks are terminal; no
process remains to hand off. DM and Root's shared tracker received these terminal facts. DM owns
the next outcome-blind technical decision; this receipt authorizes no fresh invocation. The
original source, frozen scientific object, failed logs, and passed diagnostic remain in place.
