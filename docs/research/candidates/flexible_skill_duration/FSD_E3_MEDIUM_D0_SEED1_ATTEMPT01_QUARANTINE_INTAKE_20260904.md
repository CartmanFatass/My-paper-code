# FSD E3 medium D0 seed 1 attempt 01 — technical quarantine intake

Intake date: 2026-09-04

Direction: `flexible_skill_duration`

Object: frozen B/EXPLORE `FSD-E3-HET-R01`

Tier of the decision below: **object**

Provenance: `OWNER_DELEGATED` under the owner's unattended instruction of 2026-09-03

## Intake disposition

**QUARANTINE as an incomplete evidence attempt.** The attempt is neither an E3 result nor a
scientific failure. It does not satisfy the frozen output contract, it contributes no value to the
E3 result rule, and it does not change or consume the B object.

The attempt ran once as remote task `fsd_e3_medium_d0_seed1_20260904_01` in detached worktree
`/home/wu/hmasd-worktrees/fsd_e3_medium_d0_seed1_20260904_01` at pushed SHA
`e6108e466eeea3df31db52c53e49eef828bde41a`. Its wrapper PID was `11443`. The immediately preceding
remote admission passed at `2026-09-04T13:45:42.145553Z` with physical and effective availability
both `15438573568` bytes. The supervisor later reported terminal `failed`, exit code `1`, and no
live tmux process; it exited at `2026-09-04T14:30:45Z` after `2703` seconds.

## What I checked

1. **Admission and single launch.** One `agent-task` payload performed the remote memory admission
   immediately before the exact runner. The earlier refused local receipt was not reused. No
   duplicate or migrated process exists.
2. **Learner-side work.** The remote root contains 20 interruption records, the four scheduled
   evaluations, the final checkpoint, and the inherited base summary. These facts show where the
   failure occurred; they do not make the attempt a result.
3. **Frozen E3 publication contract.** The inherited summary lacks required E3 fields including
   `d0_competence_ratio_input`, `cumulative_regional_path`, and `resource_telemetry_status`.
   Therefore the frozen E3 observable and receipt set is incomplete.
4. **Terminal step.** After learning and evaluation, E3 `_postprocess` called
   `peak_rss_bytes()`. That function accessed `ctypes.windll`, which does not exist in the remote
   Linux interpreter, and raised `AttributeError`. The publication step only handled `OSError`, so
   it terminated before writing the E3 summary and manifest fields.
5. **Reproduction over recorded bytes.** I copied the attempt's `interruptions.jsonl`,
   `summary.json`, and `manifest.json` to
   `/home/wu/hmasd-inputs/fsd_e3_medium_d0_seed1_postprocess_repro_20260904_01` and invoked the exact
   SHA's `_postprocess` with the remote interpreter. It reproduced the same `AttributeError` at the
   same `ctypes.windll` access. Source and reproduction-copy SHA-256 values matched:

   | recorded input | SHA-256 |
   | --- | --- |
   | `interruptions.jsonl` | `1055cc19512ca137dd99bf2b06d4e8d2fb6fc718ad99f0d1aaf4ea9c63dd3348` |
   | `summary.json` | `05905ec12b68a404d9177ed1ed753c3d76ddea1d5358d0e548266dc9697d8591` |
   | `manifest.json` | `e0706c8301ea69cc21236f61b6ed2f4265e73eaebbbe6951fe13019a02d990f9` |

6. **Failure classification.** The reproduced defect is an engineering portability failure in
   the post-learner publication path. Missing peak-RSS telemetry is permitted and should have been
   recorded as `resources_unmeasured`; it should not have prevented publication. Because required
   learner/result fields were never published, the attempt remains incomplete under the
   quarantine rule.

The already-produced return numbers are deliberately not copied into this intake and were not
used to select a repair, change a branch, or alter another arm. A fresh attempt after an
outcome-blind repair is a new launch, not a resume or salvage operation.

## Observation that bounds this intake

Direct observation establishes only that the exact E3 publication implementation at SHA
`e6108e466eeea3df31db52c53e49eef828bde41a` is not portable to this Linux node's `ctypes` surface.
It establishes no sign or magnitude for D0 return, no comparator competence, no D2 mechanism
value, and no E3 result branch. The claim ceiling remains the frozen B/EXPLORE ceiling after a
future complete 18-invocation study.

## Flags for the owner

- The learner and evaluations consumed machine time, but the attempt is not scientific evidence.
- The original remote artifact root remains untouched as historical technical evidence. It must
  not be rewritten into a successful root.
- A replacement attempt requires a new pushed SHA, a different detached task/worktree identity,
  and a fresh remote 4 GiB admission immediately before the exact runner.
- The direction end-to-end test must exercise the real E3 publication path with representative
  constants before that replacement launch. Test success will establish only engineering
  conformance.

## Decisions this intake produces

### Decision 1 — disposition after reproduced post-learner failure

Options:

- **(a)** Quarantine attempt 01; implement only the smallest cross-platform missing-RSS handling
  and publication-path test; then perform a fresh `medium_d0_seed1` attempt at a new pushed SHA
  after a new remote admission.
- **(b)** Salvage the inherited summary by running the corrected postprocessor over the completed
  learner artifacts and count it as the E3 invocation.
- **(c)** Treat the supervisor failure or unpublished return as scientific evidence and alter the
  remaining E3 sequence.

Recommendation: **(a)**. It is outcome-blind, reversible, preserves the frozen object, and follows
the incomplete-attempt and post-learner-path rules. Option (b) would retrofit required prospective
publication fields into an incomplete attempt; option (c) would convert an engineering defect
into scientific polarity.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

Provenance label: `OWNER_DELEGATED`.

No direction- or Portfolio-tier decision is produced. The remaining E3 card, treatment/comparator
pairing, row order, seeds, budgets, cost projections, result branches, and claim ceiling stay
unchanged.

## Clean next boundary

Accept and push the minimal CM repair only if its focused test reaches the formal E3 postprocess
path and writes the required fields while recording unavailable RSS as `resources_unmeasured`.
Then create a new detached remote worktree at the exact pushed SHA and launch one fresh
`medium_d0_seed1` attempt only after its own passing remote admission. Do not apply the frozen E3
result rule until all 18 invocation cells are validly complete.
