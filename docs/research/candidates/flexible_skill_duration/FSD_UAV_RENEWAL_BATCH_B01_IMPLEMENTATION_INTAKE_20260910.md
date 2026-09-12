# FSD I1280/D0 implementation intake — 2026-09-10

**Accepted for configuration binding, sampler traversal and synthetic primary
publication only. One fixture passed in 4.8851396 seconds; zero real B exposure.**
This record closes the one implementation allocation; it cannot allocate
the prospective pair or its proposed 3000-second envelope.

## 1. Assignment, actual checkout and governing rule

Root assigns the [exact execution mapping](../../portfolio/pro_packets/20260910_fifth_slot_implementation_selection/EXECUTION_MAPPING.md),
the conforming Portfolio option A from immutable response
`ade6a687d53b97b5f6cc2fe97da39daa2ad9bfa9`, integrated on
main `75d4fa18e1a0a6dbda50b11f5b9f9a6467cc86ef`. The work uses the existing
`C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`, initially clean at
`eb8be143b8449606d8e00e4ec0a1a43dfd350e02`. Merge `eec2ec260` was pushed
immediately. Its only conflict was the shared 2026-09-10 audit: retained main's
current rows plus the unique historical Portfolio recommendation row. No source
or evidence was discarded. Root retains main integration and control-plane ownership.

The allocation rule applied verbatim is:

> Stop at **one committed implementation/acceptance return**, including a failed,
> unavailable or incomplete check. No real B launch, new master, fallback, MGTAP
> implementation, repeat test or automatic successor is funded.

Card [§7](FSD_UAV_RENEWAL_BATCH_B01_DESIGN_CARD_20260910.md#7-selected-implementation-boundary-and-l0)
contains the five L0 facts. Applicable reads: current Portfolio FSD row,
DIRECTION's P70/P72/P74 sections, prospective card §§2–7 and design intake
§§2–5, execution mapping, governing/nearest AGENTS, Engineering Scope §§3–5,
7.1–7.3, ROOT_OPERATIONS owner/integration sections, and evidence-spec §11.4,
§§11.8.1–11.8.8. The Portfolio choice is applied, not decided again by this DM.

## 2. Implementation and protected meaning

The new entry `scripts/run_fsd_uav_renewal_batch_b01.py` binds
`FSD_UAV_RENEWAL_BATCH_B01`, this prospective card, training seed 770703,
evaluation seed 780703 and the proposed future caps D0 900/I1280 1800 seconds.
CLI/summary arm `I` denotes I1280 under the new object; historical fields and
commands retain their meanings. Caps in source are prospective limits, not
spending authority; a later launch assignment and destination admission remain absent.

The small shared-runner change passes the default-false `renewal_batch` argument
through learner setup, evaluator setup and the paired reducer. Enabling it sets
`coordinator_batch_size` to 1280 for I and 128 for D0 before model construction.
Both configuration snapshots retain the value. The reducer demands those exact
arm-specific values and allows only that extra difference beyond the original
.25/infinity individual cost. It still compares every other recorded field.
The existing deadline reads the summary's selected cap; old defaults still
supply their original 3600/18000-second limits.

Protected `hmasd/agent.py`, `hmasd/utils.py`, shared config defaults, environment,
reward and duration-credit source are unchanged. Collection/reset/terminal
storage, private recurrence, segment targets, RNG isolation, PPO exposure and
the one final endpoint are reused. No model/checkpoint construction path is
executed by the fixture. No new scientific information is added or withheld.

The primary remains 32 raw adapter returns U, `J=6U/500`, ordered I−D0
differences, sample SD with `ddof=1` and SD/sqrt(32) conditional SE. One matched
training pair remains the learning unit; malformed primary has no paired polarity.
The unchanged all-sign .01 rule is not rewritten by a synthetic outcome.

## 3. Focused evidence and independent review

Before the single check, inspected the new entry/shared runner, E0 config and
snapshot builders, Config constructor/validation/dimension derivation,
RolloutBuffer allocation/full-data getter/sampler, and reachable repository
import setup. Config has no preset-dependent work in this path; repository
imports define classes/functions and do not construct models or environments.
The unchanged sampler performs its existing internal timing/cache bookkeeping;
no explicit profiler or support probe is introduced or invoked.

Independent read-only Astra/high Reviewer `rev_ah_fsd_i1280` returned no material
finding. It inspected changed binding before both constructor boundaries, exact
config comparison, primary meaning, old defaults and reachable imports. It ran
no code/imports/tests and made no edits. It confirmed 437/29 runner lines and
no new §4 machinery. Its residual boundary is explicit: a synthetic pass does
not measure learner numerics/gradients, larger-batch activation memory, actual
native thread use, complete runtime or native return.

The sole fixture is
`tests/experiments/candidates/flexible_skill_duration/uav_renewal_batch_b01/test_binding.py`.
It constructs four real lightweight Configs using only inert dimension metadata,
then one deterministic buffer with 1281 valid rows and one excluded invalid row.
Two real sampler traversals use one epoch each, at 1280 and 128. Four reducer
calls use supplied 32-score arms: above-MEI, opposite sign, undeclared gamma
difference, and missing U. The two valid synthetic readouts check ordering,
scaling, sample SD and conditional SE; rejected cases retain no paired result.
Old defaults and the unchanged inside-MEI branch use static/prior evidence;
no fifth Config, third traversal, extra readout or full learner smoke is allowed.

The numerical fixture and runner first published at source `9dcb4bb79`.
The outer PowerShell launch/timeout/cleanup wrapper was rejected before
CreateProcess with only `rejected: blocked by policy`; the runtime supplied
no narrower reason. Neither its scratch nor its evidence directory existed
on readback. No fixture was accepted or numerical allowance spent by that
rejection. No escalation or repeat of that wrapper was requested.

A simpler foreground entry now owns a unique `TemporaryDirectory` under this
checkout's `temp/`, sets MPLCONFIGDIR inside it before scientific imports,
copies the useful report and removes the scratch in the same process. It runs
with the existing `hmasd-amd-cpu` interpreter and `-B`. This removes the external
launch/kill and shell-recursive-removal wrapper; it changes no fixture cases.
The correction published at
`0207d0b3cf307f656b5f46b298b74efa438608b8`. The one subsequent foreground fixture
returned exit 0 at those unchanged source/test bytes. Its internal receipt
records 4.299593 seconds through imports, primary publication and scratch
cleanup; the retained foreground receipt records **4.8851396 seconds through
stdout and process exit**, below the complete 60-second cap. No second fixture,
replay or numerical analysis was executed.

Actual evidence inspected directly, then independently read back by the same
Reviewer without rerunning or importing the fixture:

- [Synthetic configuration, traversal and primary report](uav_renewal_batch_b01_implementation_20260910/synthetic_primary.json).
  Both phases record I=1280/.25 and D0=128/Infinity, common team Infinity,
  gamma .99 and fifteen future PPO epochs. The two sampler traversals themselves
  each used one fixture epoch. Chunk lengths are [1280,1] and ten 128s plus 1;
  both visit every valid row exactly once and exclude the invalid row.
  The valid supplied readouts retain means ±.0175, ordered differences,
  sample SD .022860022860034298 and conditional SE .004041119295602437.
  Undeclared gamma rejects with `pair mismatch: learner_config`; absent U
  rejects with `I missing primary values`. These are synthetic inputs/results,
  not training or performance observations.
- [Internal command receipt](uav_renewal_batch_b01_implementation_20260910/FIXTURE_COMMAND_RECEIPT.json)
  records pass and scratch absence. Subsequent filesystem readback by DM and
  Reviewer also found the exact leaf absent.
- [Foreground tool receipt and exact command](uav_renewal_batch_b01_implementation_20260910/FOREGROUND_EXEC_RECEIPT.json)
  supplies source SHA, interpreter, working directory, raw output, exit and
  complete command wall; it closes the internal receipt's before-exit timing limit.

Final [Reviewer disposition](uav_renewal_batch_b01_implementation_20260910/INDEPENDENT_REVIEW.md): no material finding after actual artifact readback.
Binding/traversal/synthetic primary publication is supported at the stated
ceiling; full learner, activation-memory and native-return limits remain.

## 4. Scientific intake and interpretation ceiling

Scientific-tools reading reused the accepted design's source/literature trace,
and consulted FOUNDATIONS §§5–6 and empirical topic sections on comparison,
randomness and attribution. Concrete assumption: the new flag reaches the
existing sampler argument and changes batch/update/normalization grouping;
the source supports that operation. Its limit is that this is a whole-package
comparison, not a numerical-equivalence or pure optimizer-count intervention.
Thirty-two supplied or future endpoint scores do not make 32 training instances.
No unresolved mechanism or comparator choice requires a new literature search.

The strongest implementation support is the existing D2 consumer and accepted
old collection/evaluation path. The strongest contradiction to scientific
benefit remains the two prior native I−D0 losses,
**−.049670563167111874 (P70)** and **−.035312725297886094 (P72)**, with greater I
work. P70 coverage gain, P72's higher sampled training returns on rollouts 2–5,
small quality/altitude benefits and positive episode contrasts retain their
original scope. This fixture changes none of that evidence. Headroom remains
absent; new performance, memory and cost remain unknown. DIRECTION accepted
mechanism-level science therefore stays unchanged.

Prediction: prospective I1280−D0 below −.01, low confidence, remains unscored;
owner prediction **not taken**. No valid new empirical result exists, so there
is no empirical result evidence or valid-result Chinese brief to fabricate.

## 5. Decisions this intake produces

1. Object/technical implementation: (a) accept the scoped source binding with
   the single selected check's actual limit; (b) add a model smoke or change
   protected algorithms. Recommend and execute (a).
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a)**,
   within Root's exact Portfolio-selected assignment. No new treatment, family
   or Portfolio choice is made here.
2. Technical completion: (a) return one source/check/review acceptance with all
   residual gaps; (b) repeat a test, run the real pair, Send, or start a fallback.
   Recommend and execute (a).
   **Owner-delegated decision (unattended, 2026-09-03 instruction): (a)**.
   The next empirical discriminator remains the separately unallocated
   fresh I1280/D0 pair; nothing in this return launches it.

Owner flags: none. Owner review on current main at the starting clean boundary
and again on main `6b2e4ffc0` before final publication returned `[]`; relevant
ledger owner cells were empty. No instruction was available to apply or mark
answered. The existing FSD card item `20260910-fsd-001` and Portfolio
selection item `20260910-root-007` preserve their historical scopes. Ordinary
technical facts stay here and in the audit; no duplicate P1/P2 item is needed.
The FSD item's execution trace links this completed implementation back to the
separate Portfolio authority without inventing an owner reply or changing the
original design-only option's meaning.

## 6. Final acceptance, accounting and cleanup

**Technical acceptance: PASS, limited to the exact source/check/review contract.**
Source commits are `9dcb4bb79` (binding) and `0207d0b3c` (owned fixture cleanup);
no source/test edit follows the passing execution. This final documentation
commit retains actual outputs and records acceptance; Root receives named
commits for integration rather than a request to merge historical branch work.

| Actual assignment work | Observed |
| --- | --- |
| Accepted fixture commands / complete wall | 1 / 4.8851396 s |
| Config objects / buffers / valid rows | 4 / 1 / 1281 |
| Real sampler traversals / synthetic paired readouts | 2 / 4, 32 supplied scores per arm per readout |
| Models, checkpoint loads, environments, native/simulated steps | 0 |
| Collection/training starts, optimizer calls, real endpoint evaluations | 0 |
| Scientific invocations, replay, explicit profiling, support search, Pro Sends | 0 |
| Parameter displacement | Not applicable: no learner |

Machine-generated exposure is retained in the synthetic report. Its supplied
arm metadata counts are visibly fixture data, not actual learning counts.
The complete test wall also fits the existing five-minute limit for this new
attempt test directory, which has no other invoked tests. No allowance was
transferred from a sibling or from old B01/B02. Peak RSS, aggregate CPU and total
authoring/support cost are unmeasured, not zero; the future 3000-second real-B
envelope remains wholly unallocated.

Compared with reconciled source `eec2ec260`, production source adds **54 lines**
and removes **16** across the two runners (437 and 29 total lines); the new
test is 197 lines. This is inside the 2000/600-line limits. Parameter plumbing
and required output comparison are the majority of this small change; the
Reviewer found no unnecessary orchestration. No separate ratio census is
required by §11.8.8. Engineering Scope §4 needs/additions: **none**; no breach.

Cleanup: this invocation's exact
`temp/directions/flexible_skill_duration/test/i1280_binding_9pxdob0x` directory
was removed by its owning process, with absence independently read back.
The rejected wrapper's prospective scratch/evidence roots never existed at
that boundary. The three retained check evidence files and review above remain in docs.
No scientific execution root, detached worktree, remote process or accepted
handle was created, so there is no Monitor handover or execution-worktree
registration to retire. The active shared `codex/fsd` checkout remains for
Root's accepted-commit integration and future direction authoring; Root owns
its eventual reconciliation/reclamation. Unrelated/shared work is intact.

**Next authorized action:** Root integrates the named implementation/acceptance
commits and records this allocation complete. No further check or real B runs
from this return. The next empirical discriminator, if separately allocated,
is the card's one fresh I1280/D0 five-rollout/final-32-episode pair. It remains
unmeasured, with both old losses and unknown new performance/memory/cost intact.
