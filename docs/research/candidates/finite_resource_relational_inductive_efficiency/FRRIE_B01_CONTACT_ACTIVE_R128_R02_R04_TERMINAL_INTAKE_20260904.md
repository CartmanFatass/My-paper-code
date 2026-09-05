# FRRIE contact-active R128 R02 — attempt 04 terminal intake (2026-09-04)

Status: `R04_FAILED / CAUSE_PROVISIONAL_UNRESOLVED / NO_SCIENTIFIC_RESULT / OWNER_DIRECT_HOLD`.

The owner requested an end-of-round handoff for a later Root/configuration restart and a stop
before any fresh attempt. This supersedes the earlier authority to continue the resume slice.
Attempt 04 is terminal; **there is no authorized attempt 05 or continuing repair-run loop**.
This is an execution hold, not a direction lifecycle or Portfolio decision.

## What DM checked

DM compared CM's terminal collection with the unchanged
`FRRIE_B01_CONTACT_ACTIVE_R128_R02_SCIENCE_CARD_20260904.md`, the accepted repaired-source launch
record `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R04_LAUNCH_20260904.md`, and the earlier R03 failure
intake. The direct runtime observations below are CM's, read by DM in
`FRRIE_B01_CONTACT_ACTIVE_R128_R02_REMOTE_EXECUTION_20260904.md` at committed and pushed
`e8df4b6d4836d00c7fb408d58a7831061967a03b`. Root had independently reported the same terminal task.
DM checked the reported source identity, task and output identity, original artifact inventory,
admission, terminal wall time, missing counts, and reproduction limit. No new experiment or
verification run was used for this intake.

The object remains `FRRIE-B01-CONTACT-ACTIVE-R128-R02-20260904`, `B/EXPLORE`: one literal-root
comparison of `PHY_TRUST_004` and containing same-information `EDGE_FLEX_150` after 128 real
RSCF/Adam updates, at seen `N={9,15}` on the actual CPU FP32 node. The literal root, initialization,
five-coordinate initial tight clip, optimizer, work, evaluation, MEI and first-match rule are
unchanged. No held-out-N, churn, relation-specific, stable-superiority or population claim exists.

The card's exposure line remains prospective; it is not a measurement of this incomplete attempt:

`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`

## Observed terminal facts and counts

| quantity | retained evidence |
| --- | --- |
| Execution node | `wsl_4070`, SSH alias `hmasd-wsl-node`, CPU FP32 |
| Exact source | `732cc2b2299821a58d644e202c4b95c392932447`; CM's source diff against it was empty |
| Task | `frrie_b01_contact_r02_732cc2b2_04` |
| Worktree | `/home/wu/hmasd-worktrees/frrie-contact-r02-r04-732cc2b2` |
| Start / end | `2026-09-04T22:14:20Z` / `2026-09-04T22:26:33Z` |
| Terminal state | `failed`, exit 1, `tmux_active=false`; supervisor PID 98520 was historical |
| Supervisor wall | 733 seconds from the terminal log, not the later status uptime |
| Admission | `22:14:20.624055Z`; physical and effective availability each 12,882,489,344 bytes, above 4 GiB |
| Scientific output | Original result directory exists and is empty; no summary or partial result |
| Learner / optimizer / evaluation counts | Unknown; no original persisted counter, curve, checkpoint or saved learner state |
| Resource limits of the observation | Per-arm wall and full-run peak RSS unavailable; earlier RSS was a snapshot |

The terminal traceback reaches `execute` at `experiment.py:231`, during
`production_training_inputs(root, seed_label, number)`, then episode-tape uplink generation,
`SemanticRNGAddress.canonical_bytes`, `asdict(self)`, and Python 3.10's `dataclasses._asdict_inner`:

```text
value = _asdict_inner(getattr(obj, f.name), dict_factory)
AttributeError: 'tuple_iterator' object has no attribute 'name'
```

This locates the failing operation, not its cause. The committed runner writes its summary only
after the loops; the exception is in training-input preparation, not the publication write.
Source order places it before collection for some update in 1..128. Neither the exact update nor
the number of prior successful updates is recoverable from an original artifact. Elapsed time
and RSS cannot establish zero or nonzero learner exposure. The intended 128 updates per arm,
18 evaluation cells and 4,608 evaluation episodes are not accepted as completed counts.

## Card rule and bounded reading

Card §8's first integrity row is reproduced verbatim:

> `R02_INVALID_INCOMPLETE`: A common-integrity item fails; remote/local admission is absent or below 4 GiB; real learner transition/update/evaluation counts or exposure are zero/missing; information/work differs; raw initialization is not paired; the initial tight clip does not change exactly five coordinates; optimizer moments change during projection; or required learner-side curves/counts are absent. Quarantine; no result.

The incomplete invocation has no required learner-side curves/counts or complete summary, so
there is no valid scientific result to interpret. Preserve it as incomplete and uninterpreted.
This integrity reading does not classify the exception's cause or manufacture a favorable,
adverse, comparator-competence or small-effect observation. No arm gap, loss, native return or
measured contact follows. B objects have no consumption state.

The DM prediction remains unscored; the owner slot remains `not taken (unattended)` with no
prediction reply found. No valid-result brief is produced. Missing resource telemetry alone
would not invalidate this non-resource claim; the absent learner evidence and incomplete
execution are the relevant limitation here. The valid admission and 733 seconds do not establish
resource exhaustion or full-run resource conformance.

The strongest accepted scientific evidence remains the earlier three-root B01 path equivalence
under zero contact. It establishes neither support nor contradiction for this contact-active
comparison. R03's reproduced intermediate-tensor mismatch and exact sampled-action/native suffix
support the accepted narrow guard repair only. Attempt 04's later exception does not prove that
repair failed or succeeded scientifically. Attempt 02's separate TypeError remains unresolved;
no common cause with attempt 04 is inferred. `DIRECTION.md` is unchanged.

## Reproduction boundary and recovery

The log does not retain the failing update/address, dataclass field contents or process-local
state. No checkpoint or memory evidence reconstructs that state. A representative new address
would be a different state; reconstructing the preceding learner execution would require a fresh
run. Neither was performed under the owner's bounded stop instruction. **Cause remains
provisional/unresolved**: no source, native-memory, host, interpreter, instrumentation or
scientific classification is established from the error text.

The original evidence remains on the remote node:

- Supervisor: `/home/wu/.agent-tasks/frrie_b01_contact_r02_732cc2b2_04/`, retaining `task.log`
  (3,182 bytes), `runner.sh` (1,762), `status` (7), `exit_code` (2), `pid` (6), `start_time` (11).
- Result root: `/home/wu/hmasd-worktrees/frrie-contact-r02-r04-732cc2b2/temp/directions/finite_resource_relational_inductive_efficiency/exp/frrie_b01_contact_r02_r04`, empty.
- Admission: `/home/wu/hmasd-worktrees/frrie-contact-r02-r04-732cc2b2/temp/directions/finite_resource_relational_inductive_efficiency/technical/frrie_b01_contact_r02_r04_admission.json`, 504 bytes.
- The existing 24,488-byte `libfrrie_ridgegate2z_external.so` remains in the source worktree;
  CM preserved it without loading it.

CM also retained byte copies under
`C:/Projects/HMASD-worktrees/cm-frrie-r02-resume-20260904/temp/directions/finite_resource_relational_inductive_efficiency/technical/r04-terminal-handoff/`.
That ignored recovery folder contains the six supervisor files in
`frrie_b01_contact_r02_732cc2b2_04/`, the empty original output in
`frrie_b01_contact_r02_r04/`, the library in `_native/`, and the admission JSON at its root.
The originals and all prior attempts, diagnostics and verification evidence remain intact.

No source repair, native/model/RNG execution, proxy probe, interpreter change, fresh admission,
attempt 05, new Pro request, artifact deletion, or other-process modification occurred in this
stop slice. The shared observer was notified that this terminal event is acknowledged and no
next invocation is authorized; routine FRRIE retry/reminder activity must not restart it.

## Decisions this intake produces

Options: (a) preserve evidence, finish this intake, and hold before a fresh attempt;
(b) launch attempt 05; (c) continue a repair-and-run loop.

Recommendation and selection: **(a)**, `OWNER_DIRECT`, object tier, kind `technical`, owner flag
`none`. This implements the owner's current safe-handoff instruction. Alternatives (b) and (c)
are outside that instruction. Owner item `20260904-frrie-015` and its audit row record the applied
hold; this is not a new science card, direction park, Portfolio disposition or approval request.
Owner reviews at the boundary contain no unapplied instruction; the audit owner cells are empty.

The next possible technical step, after separate authorization to resume, is a prospectively
bounded capture of the failing update, address and runtime state on the same committed source,
before choosing any source repair. No such execution is queued by this intake. The accepted
focused regression and real-learner toy are not to be rerun without a new concern. Formal-sized
publication-path coverage remains an open engineering item, not an added B launch gate.

The next scientific discriminator remains a complete unchanged-card contact-active R128 result
with actual counts and curves. It is currently unavailable. Root can restart from these durable
facts while preserving the owner's stop and without repeating a launch.
