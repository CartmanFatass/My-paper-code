# VSPC1 restart handoff — owner soft stop, 2026-09-09

**STOPPED after complete P73 intake. No live experiment, pending scientific
submission or Pro Send remains. Do not start new scientific work until the owner
explicitly resumes.** This is the owner's operational soft stop, not a scientific
PARK, family closure, recast, priority change, C promotion or formal UAV entry.

## Actual result and scientific boundary

B08/8401, the first normalized GATED versus ordinary width133 MLP comparison
at768 training episodes per arm, is **valid complete DOWN**:
GATED−MLP−.03386492041295242, conditional SE .012832801495252571,24/32 adverse
primary identities. Mean J: GATED .11587725095166812, MLP .14974217136462054,
H .1564698252671263. GATED−H−.04059257431545819 and
MLP−H−.0067276539025057655 retain23/19 adverse identities. Both learned means
are below H. Prospective UP(.55) missed, Brier .3025; owner prediction not taken.

Old512 pairs8301/8302/8303 remain separate: +.0165919114/−.0066345182/+.0333779164,
descriptive mean .0144451032 and SD .0200924195. Keep earlier normalized-width128
and unnormalized results/failures as well. This new counterexample does not
identify a causal budget effect, stable inferiority, specialized hold-credit
mechanism or complete comparator competence. The two old UP pairs remain the
strongest positive evidence;8401 DOWN and both H losses are the strongest current
contradiction. Matching tuned headroom remains absent.

Durable science:

- [Frozen card §§1–7; result §8](VSPC1_NATIVE_HOLD_VALUE_B08_SCIENCE_CARD_20260908.md)
- [DM result intake and decisions §6](VSPC1_NATIVE_HOLD_VALUE_B08_INTAKE_20260908.md#6-p73-valid-result-intake-and-decisions--2026-09-09)
- [E0](VSPC1_NATIVE_HOLD_VALUE_B08_RESULT_EVIDENCE_20260908.md),
  [complete collected evidence](results/native_hold_value_b08_8401_20260908/evidence.json),
  [DM analysis](results/native_hold_value_b08_8401_20260908/dm_analysis.json)
- [Chinese owner brief](../../portfolio/owner/briefs/vsp_c1/2026-09-09_VSPC1_NATIVE_HOLD_VALUE_B08.md)
- [Accepted mechanism-level position](DIRECTION.md#greater-training-exposure-a-native-counterexample--2026-09-09)

## Execution, observer and budget

| Field | Actual state |
| --- | --- |
| Scientific source | `e9a05af5d51da571642f51c5b7b8f00c96f1c6b5` |
| Node /device | hmasd-wsl-node (wsl_4070), CPU FP32, one process/numerical thread |
| Handle /PID | `vspc1_hold_value_b08_8401_e9a05af5d51d` /3032870 |
| Accepted /terminal | 2026-09-09T06:58:00Z /2026-09-09T07:06:25Z |
| Terminal fact | finished, exit0, tmux inactive; no live process |
| Remote detached cwd | `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b08-8401-e9a05af5d51d` |
| Remote payload | `/home/wu/hmasd-inputs/vspc1_hold_value_b08_8401_e9a05af5d51d.sh` |
| Remote output | `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b08_8401_e9a05af5d51d` |
| Admission | same remote output prefix plus `_admission.json`; passed fresh physical/effective4GiB floors |
| Local raw collection | `temp/directions/vsp_c1/collection/native_hold_value_b08_8401_e9a05af5d51d/` in designated authoring checkout |
| Observer | CM `/root/dm_vspc1_p49_value_question/cm_am_vspc1_hold_value_b01` completed sole observation/collection and is stopped; no adoption required |

Actual work:417792 native steps,393216 training/24576 evaluation;3072 Adam,
768 rollouts/moment merges,393216 targets/1572864 epoch-target terms;1536 training
episodes and96 final evaluations. Two fits, one independent matched pair.
One accepted submission of one allowed is spent; **zero scientific submissions,
retries, extra evaluations or successor pairs remain allocated**. B has no
object-consumption state. There is no scientific partial or uncertain acceptance.

Whole505.00s and conservative arm bounds293.7102160760/226.9720271720s satisfy
the original1800s complete-arm/3600s whole caps. Peak RSS544.87109375MiB.
Aggregate CPU/component overhead remain unmeasured; native `resources_unmeasured`
is retained beside independent wall/RSS facts. No observed scope/cap breach.
Focused source checks15 passed/4.3296454s; artifact-only checks passed/2.3562994s.
No model/forward/native replay was added during collection or DM intake.

## Checkout, commits and ownership

Reuse **`C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`**, branch
**`codex/direction-vsp_c1`**, upstream `origin/codex/direction-vsp_c1`.
CM returned edit/index ownership to DM at terminal collection. At completed
delivery the intake/handoff changes are committed and pushed; no tracked dirty
paths or untracked authoring files remain. Ignored runtime collection is retained
at the path above; no evidence or worktree cleanup was performed. Root owns any
later integration/reclamation, with evidence preservation under AGENTS §6.

P73 commits after already completed P72 `dd27e6fed955385da55637290895d27992ecf34e`:

| Commit | Delivery |
| --- | --- |
| `a08b97fa89319050e844973db28deb18859df746` | prospective B08 card/key/prediction/counts, owner item014, audit99 |
| `e9a05af5d51da571642f51c5b7b8f00c96f1c6b5` | fixed768 source/reporting and15 focused checks |
| `8ba5f2debe62834839f5acb348d73f70ac140084` | DM source acceptance and exact P73 binding, audit100 |
| `6a433b46e8240b4dd50d67e2f247017a88e5e582` | seven-line literal execution wrapper |
| `8dc99a6dff7c257e1ea03b3ab214831b42c95e79` | verified exact remote staging |
| `c391309174c443020336d5dc5d96dadd8850572f` | sole accepted handle/admission |
| `760f30aac27871be9de326a0f4c05be9431bade6` | complete terminal collection/E0 and CM stop |
| `3bbd810d6c9092b6e23b003ee35bde0ecc3c8997` | Root-directed policy sync from `3e3357c858f068d171a618925e4085d8511f2995`, already present on main by origin |
| this handoff's committed revision | DM all-outcome intake/analysis, card result, DIRECTION, brief,2026-09-09 audit and stopped restart state |

Root must reconcile already integrated patches, especially the policy sync,
and preserve concurrent main/DIRECTION/audit/owner files during integration.
No scientific source or exact live-run binding changed at policy sync; nine role
files match the originating commit and parse with approval_policy=never. The
behavioral rule was forwarded to CM before terminal; no model/budget change or
runtime hot reload is claimed. There are no active overlapping authoring writers.

## Exact next unexecuted step held for restart

**Immediate held state: await the owner's explicit restart; do not dispatch a
new CM scientific task, seed/object, evaluation or Pro Send.** Root's remaining
current action is to integrate this completed return and record the stopped
handoff, preserving the exhausted P73 allocation.

DM's object-tier recommendation, advice only, is one additional independent
matched768-episode normalized GATED/width133 MLP/H pair with32 final evaluations
each to assess variation, preserving8401 DOWN/H losses and all old-budget results.
After an owner restart **and a separate explicit allocation**, the first
unexecuted research step is to freeze that new card with a fresh unused master,
prospective prediction and unchanged417792-step/3072-Adam/96-evaluation,
1800s-arm/3600s-whole bounds, then send the minimal binding change to the same CM
in this checkout. No fresh master, card, prediction, code assignment or run has
been created for it. No same-key retry, sign repair, tuning, extra evaluation or
causal-budget claim follows. This recommendation is not a scientific lifecycle
decision and gives Root no instruction to resume without the owner.
