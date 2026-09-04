# FRRIE contact-active R128 R02 — repaired attempt 04 (2026-09-04)

Status: `REPAIR_ACCEPTED / R04_FAILED / CAUSE_PROVISIONAL_UNRESOLVED / OWNER_DIRECT_HOLD`.

Superseding terminal intake:
`FRRIE_B01_CONTACT_ACTIVE_R128_R02_R04_TERMINAL_INTAKE_20260904.md`.
Task `_04` ended at `2026-09-04T22:26:33Z`, exit 1 after 733 seconds, with an empty output root.
The owner directed a safe handoff before any fresh attempt. No attempt 05 or continuing repair
loop is authorized. The acceptance/running snapshots below are preserved historical observations.

R04 is an execution-attempt label, not a new scientific object. The existing
`FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904` card remains unchanged, at `B/EXPLORE` ceiling.
The claim remains one literal fresh-root R128 package comparison at seen `N={9,15}` on the
actual CPU FP32 execution node. No held-out-N, churn, relation-specific, stable-superiority,
or seed-population claim is added.

## Technical acceptance of the minimum repair

Source commit: `732cc2b2299821a58d644e202c4b95c392932447`, committed and pushed on the CM and
implementer branches. DM inspected its exact three-file diff and CM's independent review and
remote verification results against the R03 failure intake's protected semantics.

The private shared factual-suffix audit has one new keyword,
`require_intermediate_bit_equality=True`. Only the R02 caller sets it false. This skips precisely
three intermediate tensor identity predicates: incoming recurrent state, postdecision recurrent
state, and action probabilities. The shared default remains unchanged for other callers. R02's
old full-trace-equality flag is now false, so it does not claim a check it no longer performs.

Exact sampled-action equality, native pre/post snapshots, observations, roles, masks, primitive
steps, terminal returns, model preservation, factual replay, and work inventories remain. The diff
changes no policy/native computation, batch width, grad mode, dtype, rounding, tolerance, RNG,
root, optimizer, evaluation, or result rule. It contains ten source insertions and four deletions
and adds 76 test lines. No engineering-scope §4 machinery or §5 budget breach is added.

CM's independent review found no material issue. The focused regression passed once, showing
that intermediate differences are allowed for R02 while default strict callers still reject them,
and changed actions or native trajectories still fail. The existing real learner toy passed once
in 15.19 seconds, reaching publication. The combined test invocation's first attempt had failed
only at pytest scratch-directory setup before the toy ran; CM reproduced the absent-parent
mkdir failure, created the required scratch parent, and ran only the unexecuted toy. No passing
test was repeated and no scientific outcome was read from a test.

The successful toy task was `frrie_contact_repair_check_732cc2b2_02`, exit 0 at
`2026-09-04T22:10:53Z`, 16 supervisor seconds. Fresh admission measured physical/effective
availability `12,875,837,440` bytes. Tests establish technical conformance, not R02 mechanism
value. A formal-sized end-to-end publication test remains unrecorded; this is an open engineering
item and not a B launch gate.

## Decisions this launch record produces

Options: (a) one fresh R02 invocation at the accepted repaired source; (b) repeat satisfied
engineering checks; (c) leave the repaired object unobserved.

Recommendation and selection: **(a)**. The reproduced failure is repaired without changing
scientific computation or its native integrity checks. The card's question, literal root,
prediction, exposure, comparator, and budget remain fixed. Prior failure artifacts are preserved;
no tape, partial model, optimizer, result, or checkpoint is reused.

Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, labelled
`OWNER_DELEGATED`, kind `selection`, owner flag `none`. Owner item `20260904-frrie-014` records
the next invocation. The existing card and prediction surfaces are not recreated, and no Pro
round or owner reply is a launch condition.

## Frozen invocation boundary

- node: `wsl_4070`, SSH `hmasd-wsl-node`;
- new detached worktree: `/home/wu/hmasd-worktrees/frrie-contact-r02-r04-732cc2b2`;
- exact source: `732cc2b2299821a58d644e202c4b95c392932447`;
- task: `frrie_b01_contact_r02_732cc2b2_04`;
- output: the worktree's
  `temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r04`;
- admission: the worktree's
  `temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r04_admission.json`;
- interpreter: `/home/wu/.venvs/hmasd/bin/python`;
- runner: `scripts/run_frrie_b01_contact_r02.py`, `--seed 1` and the absolute output/receipt paths.

CM confirms no duplicate task or populated paths, materializes the committed source including
its existing preflight dependency, and submits one detached existing `agent-task` command with
fresh node-local `admit-memory && runner`. Both physical and effective available memory must
pass 4 GiB immediately before this invocation. The test worktree's native artifact is retained;
this new worktree avoids reusing that artifact under the existing builder semantics.

The literal root remains
`2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`, label
`FRRIE-B02-CONTACT-BLOCK-001`. `PHY_TRUST_004` and containing `EDGE_FLEX_150` retain paired raw
initialization, initial tight clipping of five coordinates, unchanged optimizer moments,
128 real full-batch RSCF/Adam updates, 64 episodes/update in `(9,15)*32` order, and intact
evaluation at `{0,32,64,128}` with 256 episodes/cell and one shared uniform reference per roster.

Per arm, the runner's unchanged law is 630,784 training plus 24,576 evaluation slots, totaling
655,360 slots and 128 optimizer steps. Shared uniform evaluation adds 6,144 slots; total
invocation work is 1,316,864 slots. The same-node repaired-source toy measured 1.280900390 seconds
for PHY and 1.190476307 seconds for EDGE per 4,976 total slots. The runner's law therefore projects
168.700 seconds for PHY and 156.791 seconds for EDGE, both below their own 14,400-second cap.
These are planning estimates, not full-run guarantees. The total cap remains 28,800 seconds.
No result-sensitive stopping or retry budget is added.

The unchanged machine-generated exposure line is:

`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`

## Observation ownership and interpretation

The exact acceptance/receipt will be appended to the CM execution record and summarized here.
The shared observer receives the new handle and reports terminal changes to DM, CM, and Root;
Root may relay if its direct sibling channel is unavailable. CM owns technical diagnosis and DM
owns science intake. Observation loss never authorizes a duplicate launch.

The R03 diagnostic's exact native replay supports the repair only on its observed suffix. It is
not learning-effect evidence; future actual native divergence must still fail. `_02`'s earlier
TypeError remains separately unresolved. No scientific result is accepted at this launch boundary.
The original card §8 first-match rule and `0.005` absolute MEI control the terminal intake.

## Direct acceptance

CM observed task `frrie_b01_contact_r02_732cc2b2_04` accepted at `2026-09-04T22:14:20Z`, with
supervisor PID `98520` and runner PID `98525`. At two seconds, it was `running`, `tmux_active=true`.
Fresh node-local admission at `2026-09-04T22:14:20.624055Z` passed with physical and effective
available memory both `12,882,489,344` bytes, above the 4 GiB floor. The repaired source and new
worktree/output/admission identities are exactly those above. No artifacts or partial state from
an earlier invocation were reused.

The next direct CM check found the same task still running at 92 seconds, supervisor `98520`,
`tmux_active=true`, `exit_code=null`. Runner `98525` remained alive at 90 seconds; its RSS
snapshot was 598,688 KiB, not peak RSS. No exception appeared in the log tail. No published
result or learner counter was read. This was the running snapshot at the earlier execution
handoff and is superseded by the terminal intake linked above.

This is accepted-process evidence, not a measured optimizer count or native return. The observer
receives the same task and retains routine observation; no duplicate may be submitted when
observation is delayed. Recovery commands:

```sh
ssh hmasd-wsl-node '/usr/local/bin/agent-task status frrie_b01_contact_r02_732cc2b2_04'
ssh hmasd-wsl-node '/usr/local/bin/agent-task logs frrie_b01_contact_r02_732cc2b2_04 50'
```

The expected artifact was `<output>/summary.json`; none was produced. The terminal intake records
the missing counts and exact reproduction limit. Cause remains unresolved and no scientific
result or polarity is accepted. The current owner hold supersedes earlier execution instructions.
The repaired launch and incomplete terminal attempt do not change the accepted DIRECTION science
or create a valid-result brief.
