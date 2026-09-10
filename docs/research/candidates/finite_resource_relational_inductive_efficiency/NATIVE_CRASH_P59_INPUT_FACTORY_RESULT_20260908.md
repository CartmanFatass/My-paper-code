# P59 corrected input-factory collection — 2026-09-08

Status: TERMINAL / SIGSEGV IN GROUPED TEST INPUT FACTORY. Technical A/RECON
evidence only; no production correction or scientific result is accepted.

Authority: P59 and the committed
[Root handoff](NATIVE_CRASH_P59_INPUT_FACTORY_ROOT_HANDOFF_20260908.md)
at `d9b0f98b044df65a5091b8f0756571aeadabc320`. This documentation-only collection
uses the terminal facts supplied by Root and the same-handle readback already
obtained. The latest Root instruction prohibits further commands for diagnosis,
source inspection, process launches or cleanup. No such work follows this record.

## Bound attempt and direct observations

One accepted handle: `frrie-p59-input-factory-20260908`, `hmasd-wsl-node`, CPU.
Detached source: `5831dafaab0e47d0c13fe1cbefcc94e5a817b1bc`; cwd
`/home/wu/hmasd-worktrees/frrie-p59-input-factory-20260908`.
The corrected standalone `test_training_input_factory.py` used the historical
system312 interpreter, thread limits1, exact-cwd PYTHONPATH, existing TEST
root/label and coordinates1–8. The handoff records the additional owned-temp
pycache placement and its possible import-timing effect. No alternate executor,
runtime or access route was used.

| Quantity | Retained fact |
| --- | --- |
| Admission | Passed at2026-09-08T21:22:54.354782Z; physical/effective available15,637,053,440 bytes against4,294,967,296 |
| Terminal | Supervisor failed, exit139, tmux inactive; process terminated by signal11; fatal Python report says Segmentation fault |
| Supervisor time | Started21:22:54Z, exited21:23:12Z; reported duration18s |
| Whole process wall / peak RSS |18.59s /618,760KiB |
| Published progress | Coordinates1,2,3,4,5; cumulative TEST tapes64,128,192,256,320 |
| Complete groups | Five groups,320 tapes and320 checked origin rows,960 origin selections; any additional partially generated sixth-group work is unmeasured |
| Final test JSON | Not emitted; no all-eight-group completion or512-tape success |
| Learning/scientific exposure | Zero models, learners, optimizer steps, project-native calls and scientific evaluations, by the standalone invoked code path |
| Source state | Root reported remote worktree clean; collection makes no source change |

Fatal traceback location: `rng.py:133 validate -> rng.py:204 canonical_bytes ->
rng.py:251 block -> rng.py:273 uniform_float32`, called by
`tapes.py:373 generate_episode_tape`, then the generator in
`b01_contact_r02/tapes.py:247` and `production_training_inputs:246`, then the
diagnostic's `main:22`. This is the recorded Python caller path, not an identified
corrupting operation or proof that validation itself caused the fault.

The progress records establish at least320 completed tapes. They do not establish
that exactly320 individual tapes had been materialized at the fatal signal.
There is no missing-output-to-zero inference: zero learner/native exposure follows
the test's explicit call boundary; partial sixth-group tape work remains unknown.

## Acceptance, evidence location and remaining boundary

Under evidence-spec §§3–4,5.1,11.8.5–7, accept the invocation's bounded fatal-path
and completed-group observations. The corrected import passed its former failure
point and the actual grouped factory completed five groups before SIGSEGV. This
is stronger than the previous harness exception, but does not clear or causally
explain historical production failures, establish a shared CBSC cause, or support
an algorithm effect. The P47 native fixture pass and harness failure retain their
original meanings. Static syntax/import acceptance is separate from runtime facts.

Necessary raw evidence remains in the original supervisor directory
`/home/wu/.agent-tasks/frrie-p59-input-factory-20260908/`: `task.log` and
`process-time.txt`. Admission is in the detached cwd's
`temp/directions/finite_resource_relational_inductive_efficiency/exp/p59_input_factory/admission.json`.
The earlier same-handle readback retained these exact counts, admission, traceback
and timing in the collection conversation. No new local raw archive is claimed.
The diagnostic published progress and fatal/terminal evidence through the
supervisor; it did not emit its final summary or any learner publication.

One allocated invocation ran once,18.59s within the complete120s bound. No
relaunch, timing probe, warm-up, new source check or native-check repeat occurred.
Aggregate CPU is unmeasured. Control-plane staging/collection is not included in
process wall. No high-impact production review is triggered or claimed because
production/native semantics were not changed.

The owned `pycache` directory was present at the existing terminal readback.
Cleanup is explicitly deferred by Root's latest documentation-only instruction;
no cache/evidence/worktree is deleted. Root retains the declared detached-checkout
reclamation route after verified evidence retention and completed delivery.

Next owner: `/root/dm_frrie_p47_repair` for bounded all-outcome intake. P59 supplies
no second invocation and no R09 learner remainder. Any further observation or
repair must identify its concrete task and allocation. The current missing fact
is a specific fault/correction tied to credible affected-boundary evidence;
this caller location alone supports no speculative production or interpreter fix.
