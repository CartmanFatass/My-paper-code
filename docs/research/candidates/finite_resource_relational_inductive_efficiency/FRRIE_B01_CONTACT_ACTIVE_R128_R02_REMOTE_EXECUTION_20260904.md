# FRRIE contact-active R128 R02 remote execution — 2026-09-04

Status: `TASK_03_TERMINAL / INTERMEDIATE_BIT_IDENTITY_FAILURE_REPRODUCED / REPAIR_PROPOSED`. Engineering observation only.

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
branch, contact observation, or learner evidence. At that boundary all three supervisor tasks were
terminal; no process remained to hand off. DM and Root's shared tracker received those terminal
facts. DM owned the next outcome-blind technical decision. The
original source, frozen scientific object, failed logs, and passed diagnostic remain in place.

## Fresh unchanged invocation `_03`

DM subsequently selected one fresh unchanged invocation after the exact tape expression passed,
over expanding diagnosis without a reproduced defect or leaving the object unobserved. This is
the owner-delegated technical selection recorded by DM as owner item `20260904-frrie-012`, under
the 2026-09-03 instruction. The `_02` cause remains unclassified and has no scientific polarity.
No further probe, test, source edit, partial-state reuse, or repair was performed.

Before launch, exact remote SHA remained `36b538ba1b91eede9f528dd315fa624f8c1d53e5`, source diff
including restored `hmasd_platform.py` was empty, `_03` was `not_found`, new output and admission
paths were absent, and no FRRIE runner existed. The new paths preserve the earlier invocation's
evidence; they change no seed/root/card/CPU FP32/work/evaluation/budget/stop semantics. The same
per-arm cost projection, resource bounds, and publication coverage limitation above apply.

Exact accepted command:

```sh
/usr/local/bin/agent-task run frrie_b01_contact_r02_36b538ba_03 'cd /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r03_admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_frrie_b01_contact_r02.py --output-root /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r03 --admission-receipt /home/wu/hmasd-worktrees/frrie-contact-r02-36b538ba/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r03_admission.json --seed 1'
```

Task `_03` was accepted at 2026-09-04T21:45:48Z. Fresh memory admission at
21:45:48.033417Z passed both physical and effective floors: each available value was
13,205,676,032 bytes against minimum 4,294,967,296 bytes, `/proc/meminfo`, no failure reasons.
At one second, status was `running`, `exit_code=null`, supervisor PID 75958, `tmux_active=true`;
the exact full-runner argv was visible as PID 75963, parent 75958, RSS snapshot 334,368 KiB.
This is direct launch acceptance, not measured full-run resource conformance or a learner result.

CM sent node/SHA/cwd/task/root/admission facts to DM and shared observer
`/root/tracker_lxh_experiments`, which owns routine status/log observation after acknowledgment.
CM retains technical diagnosis. Follow only this task; observation loss never permits a duplicate.
Its log/status/accepted command are under
`/home/wu/.agent-tasks/frrie_b01_contact_r02_36b538ba_03/`; expected publication is
`temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r03/summary.json`
under the exact remote worktree. Completion and scientific result remain unobserved at acceptance.

## Task `_03` terminal correction and reproduced actor boundary

The shared observer reported `_03` failed; CM then obtained authoritative supervisor status
`failed / exit_code=1 / tmux_active=false`. It ended 2026-09-04T21:46:23Z, 35 seconds after start.
The full traceback ends at `b01/batch_collector.py:369`:
`B01ContractError: B01 factual suffix actor trace differs`, called by R02 collector line 154
and experiment line 235. The `r03` result directory exists but contains no files. No
`summary.json`, persisted learner count, curve, or scientific branch exists. The running
snapshot above remains historical evidence only.

DM assigned exact-step diagnosis, no full retry or source repair. Acceptance was a quantitative
reproduction over unchanged SHA plus separation of intermediate differences from factual native
action/transition/return differences. The protected contract remains CPU FP32, literal root,
paired initialization and clipping, same tapes, actor/recurrence, legal action sampling, factual
Q reuse, optimizer semantics and work. Diagnostics perform no optimizer update or scientific
comparison. They preserve all earlier logs, receipts and native artifacts.

### Observed state ownership and comparison

`_collect_factual_roster` collects 32 native lanes with the actor graph enabled, saving each
lane's observations, roles, masks, incoming/postdecision hidden tensors, probabilities, sampled
actions, native state snapshots and transition results. These transient traces live within one
immutable-model collection and are not serialized. Origin records select three role suffixes
per factual episode. `_audit_factual_suffixes` restores their native snapshots and postdecision
hidden states, groups suffixes by origin slot into variable-width chunks, and replays them under
`torch.no_grad()`. The failing condition demands `torch.equal` for hidden state, full
probabilities, and sampled actions. A preceding check separately demands exact native pre-state,
observation/role/mask arrays and incoming hidden state. Subsequent checks compare native steps,
post-state snapshots and returns. The caller uses the factual terminal return as factual-action
Q; nonfactual Q is generated by separate native suffix rollouts.

This makes discrete/native replay agreement question-relevant, while bit identity of intermediate
floating tensors across batch widths is stronger than the current R02 card. DM explicitly
confirmed this distinction for R02 under evidence specification section 11.4.

### Exact reproduction and artifact constraint

The first diagnostic task, `frrie_contact_r02_actor_diag_36b538ba_01`, was admitted in the original
worktree at 21:57:42.695261Z with physical/effective available 13,022,531,584 bytes. It stopped in
one second before model construction because `_build_adapter()` rejects the native artifact
left by `_03`: `package native artifact already exists outside this fresh build transaction`.
That artifact was preserved. This diagnostic did not reach the actor.

A fresh detached worktree at the identical SHA was then materialized at
`/home/wu/hmasd-worktrees/frrie-contact-r02-diag-36b538ba`, retaining the same FRRIE subtree,
runner, preflight and committed platform dependency. No source bytes were transferred or edited;
its bound source diff remained empty.

The exact-step task was `frrie_contact_r02_actor_diag_36b538ba_02`, interpreter
`/home/wu/.venvs/hmasd/bin/python`, cwd the fresh diagnostic worktree. One existing supervisor
command executed fresh `admit-memory --out`
`<diagnostic-worktree>/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_actor_diag_admission.json`
immediately `&& timeout 180 <python> -c <payload>`. Admission at 21:59:14.316871Z passed with
physical/effective available 12,966,584,320 bytes. It ended 21:59:21Z, seven supervisor seconds,
exit 1 because the original guard exception was deliberately allowed to propagate after capture.

The payload calls the committed native builder, `initialize_contact_pair()`,
`production_training_inputs(bytes.fromhex(ROOT_HEX), SEED_LABEL, 1)`, then
`collect_r02_arm_update(model=models["PHY_TRUST"], ... update=1 ...)`, with one Torch thread.
It omits the full runner, checkpoint-0 evaluator and optimizer update. A Python exception trace
reads the failing function's locals; it does not patch or suppress production assertions.
Same-input controls reevaluate the actor with gradients enabled and with lane padding to width
32, without changing parameters. The diagnostic then directly continues only the affected
seven-lane native suffix, using unchanged actor/native calls and literal uniforms, comparing
every action/step/snapshot/observation and final return. No control output enters a learner.

The exact accepted payload is recoverable in
`/home/wu/.agent-tasks/frrie_contact_r02_actor_diag_36b538ba_02/runner.sh`; it is supplied through
`python -c 'exec(bytes.fromhex("<UTF-8 payload hex>"))'` to preserve shell quoting. Full stdout,
admission and traceback are in the adjacent `task.log`. Both were copied as evidence to this
CM worktree's ignored
`temp/directions/finite_resource_relational_inductive_efficiency/technical/r03-actor-diagnosis/`
as `actor_diag_02_runner.sh` and `actor_diag_02.log`, alongside `actor_diag_01.log` and
`production_03.log`. These are diagnostic command/evidence archives, not new production code.

### Quantitative facts

The same exception reproduced in first PHY collection, update 1, N=9, origin slot 0, future slot
1, replay chunk width 7 versus factual width 32. The first differing replay lane was 6, factual
episode lane 31, role 2. Incoming hidden state was exactly equal.

| Quantity at failing lane | Unequal values | Maximum absolute difference | Expected versus observed at maximum |
| --- | ---: | ---: | --- |
| hidden, FP32 [9,64] | 10/576 | 2.9802322387695312e-8 | -0.2180071473121643 versus -0.2180071771144867, index [5,33] |
| probabilities, FP32 [9,6] | 1/54 | 2.9802322387695312e-8 | 0.33068668842315674 versus 0.33068665862083435, index [5,5] |
| sampled actions, int64 [9] | 0/9 | 0 | identical |

Enabling gradients for the same seven-lane inputs retained exactly the same mismatch. Padding
the same inputs to 32 lanes made both hidden and probabilities exactly match the factual lane.
This directly isolates a batch-width-dependent numerical difference at this actor call; it does
not identify a particular BLAS/GRU kernel as its cause.

The direct diagnostic continuation covered all seven lanes for slots 1 through 11: all sampled
actions, native transition results, complete native snapshots and next observations matched the
factual traces exactly at every slot. The largest later hidden discrepancy was
5.960464477539063e-8, and the largest probability discrepancy was 2.9802322387695312e-8.
The seven final returns were exactly equal:

`[0.0068181812763214115, 0.0, 0.0, 0.0, 0.0037037014961242678, 0.0037037014961242678, 0.015789473056793214]`.

The reproduction completed 32 factual N=9 episodes (384 native transitions), then reached the
first seven-origin audit chunk before any nonfactual suffix, N=15 collection, backward call or
Adam step. The diagnostic continuation adds 77 native transitions. These stage counts follow
the directly identified trace and committed loop bounds; the original `_03` did not persist
its counters. It is consistent with this first-update failure, but no original update-counter
artifact exists. The diagnostic's initial clip changed exactly five coordinates; raw parameters
were paired and optimizer state was unchanged by projection. No learning-effect reading follows.

### Engineering conclusion and smallest proposed repair

The reproduced failing boundary is intermediate FP32 bit identity across actor batch widths.
The observed seven-lane replay preserved factual actions, native trajectories and final returns.
This supports removing the unclaimed intermediate exactness requirement for the R02 consumer,
not changing the numerical computation to force bit identity.

The proposed repair is confined to the R02 factual-suffix audit path: stop rejecting unequal
floating hidden/probability tensors (including the later incoming-hidden exact check), while
retaining exact sampled-action equality, native pre/post snapshot equality, observation/role/mask
agreement, native primitive/terminal/return checks, immutable model checks and existing work
inventory. Do not round tensors, copy factual hidden states over replay states, change batch width,
turn gradients on, alter RNG/tapes or adopt a numerical tolerance that could admit different
actions/native outcomes. Preserve the existing shared B01 callers' declared audit meaning;
the implementation must make any R02 audit wording accurately describe native trajectory
reproduction rather than claim intermediate tensor identity.

This is a repair recommendation, not an implemented change or a new launch authorization.
The observation covers one first-update chunk, not every suffix, roster, arm, later update,
return distribution, or full-run conformance. Future actual native divergence must still stop.
Existing native-artifact freshness also means a subsequent diagnostic or production invocation
needs a fresh exact-source worktree unless a separate artifact-handling change is selected.

All currently assigned diagnostic/production tasks are terminal. Source and scientific contract
remain unchanged; `_01`'s fixed sparse omission, `_02`'s unresolved TypeError and `_03`'s
reproduced actor-boundary failure remain separate facts. No valid scientific result exists.
