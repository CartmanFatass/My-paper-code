# VSPC1 restart handoff — P76 allocated, 2026-09-09

P76 current boundary: Root separately allocates the same-trajectory512/768
comparison recommended after P74. The prospective
[B10 card](VSPC1_NATIVE_HOLD_VALUE_B10_SCIENCE_CARD_20260909.md) and
[intake](VSPC1_NATIVE_HOLD_VALUE_B10_INTAKE_20260909.md) select8501 and one
matched pair with434176 steps/3072 Adam/160 evaluations, continuous1800s
arm/3600s whole limits. No P76 result or scientific submission exists yet;
the original DM/CM and shared direction checkout carry the authorized batch.
P74 completion and the older P73 stop below are historical boundaries.

P74 current boundary: the owner explicitly resumed research; Root's committed
[P74 allocation](../../portfolio/handoffs/2026-09-09-research-resume-p74.md)
at main `b52d0e1562376cdf833fc30d0543cce64e910e1a` allocated one further
independent768 pair. **B09/8402 is now valid complete DOWN and its intake is
complete; no live experiment remains, and P74 has zero submissions left.** The
[B09 card](VSPC1_NATIVE_HOLD_VALUE_B09_SCIENCE_CARD_20260909.md) and
[intake §6](VSPC1_NATIVE_HOLD_VALUE_B09_INTAKE_20260909.md#6-p74-valid-result-intake-and-decisions)
carry the result and next object-tier recommendation. The stopped P73 account
below is historical; P74 did not reuse its spent allowance. The final section
records current source/receipt/ownership and the next unexecuted step.

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


## P74 complete boundary and next unexecuted step

Current allocation is complete, not an owner stop or direction PARK. The owner
explicitly resumed research, then Root allocated one new B09/8402 pair. It
completed at scientific SHA `4c9dc8b3de9b7827612b962aa4a4d085dc7cd411`,
wrapper `f4afd81a0b1d986b56d08bf3187cb2fccbd84ffe`, collection
`2d8bc1322fc1c64fe166295b5ba4b7cd357fde41`. B09 intake §6 and card §8 are
current evidence; the P73 stopped account above remains historical.

Result: DOWN, GATED−MLP−.013534955848536409 (conditional SE .009898214718212823,
20 adverse identities), GATED−H+.03640871339430369 (6 adverse) and
MLP−H+.0499436692428401 (7 adverse). DOWN(.55) hit/Brier .2025; owner prediction
not taken. Both768 primary point estimates are DOWN, but H-relative signs differ
between8401/8402. The old512 three-pair regime and every earlier result remain
separate. Claim ceiling is local package performance; no stable inferiority,
causal budget effect, tuned competence or specialized hold-credit conclusion.

Execution was on hmasd-wsl-node, CPU FP32/one thread. Handle
`vspc1_hold_value_b09_8402_4c9dc8b3de9b`, PID3035657, ended
2026-09-09T08:35:20Z, exit0/inactive tmux. Whole483.27s, conservative arms
256.3274/244.2363s, peak RSS547.703125MiB;417792 steps/3072 Adam/96 final
evaluations. Actual-node admission passed. P74 accepted submissions:1/1 spent,
zero remain; B has no object-consumption state. CM observation/collection has
ended, no live process or pending scientific action. Optional aggregate CPU/
component overhead remain unknown; existing resources_unmeasured qualifies them.

- Authoring checkout/branch: `C:/Projects/HMASD-worktrees/dm-vspc1-next-20260906`,
  `codex/direction-vsp_c1`; DM's final explicit-path commit contains this intake,
  analysis, audit rows11–14,401-character Chinese brief and accepted DIRECTION
  update. Scientific/technical CM return was clean, with ownership returned to DM.
  Native/relay return supplies the exact final DM commit and clean status.
- Exact detached execution cwd:
  `/home/wu/hmasd-worktrees/vspc1-native-hold-value-b09-8402-4c9dc8b3de9b`.
  Remote output:
  `/home/wu/projects/HMASD/temp/directions/vsp_c1/exp/native_hold_value_b09_8402_4c9dc8b3de9b`.
  Local raw collection:
  `temp/directions/vsp_c1/collection/native_hold_value_b09_8402_4c9dc8b3de9b/`.
  Durable E0/evidence/analysis:
  `VSPC1_NATIVE_HOLD_VALUE_B09_RESULT_EVIDENCE_20260909.md` and
  `results/native_hold_value_b09_8402_20260909/` in this direction directory.
- New pre-final commits, in order:313feb739e420809481cb5765ca1f065e5345028,
  4c9dc8b3de9b7827612b962aa4a4d085dc7cd411,
  732ded23095d70b6ec96eaf4829177d71c8c9147,
  f4afd81a0b1d986b56d08bf3187cb2fccbd84ffe,
  76ea7f2b542eecf5257b7268b02c85e305fc43bb,
  6968ece2bcf5448a5662286d4f9a13d6a319c81c,
  2d8bc1322fc1c64fe166295b5ba4b7cd357fde41. Root integrates the new bounded
  paths/audit additions without rolling back later shared UCOPE/main work.

Next selected object-tier advice: in one fresh training pair, prospectively
measure the same GATED/ordinary-width133 comparison at fixed512 and768 training
endpoints, retaining both and one H bank. This would observe a local exposure
response without using different masters for the two budgets. Real training
remains two768 fits/3072 Adam; four learned endpoints plus H give160 evaluations,
434176 total steps and proposed1800s complete-arm/3600s whole caps. Added work is
64 learned evaluations/16384 steps (3.9215686% total steps);524.8039s uniformly
scaled prior wall is only a planning proxy. Preserve training RNG/data/moments
across midpoint evaluation; no historical state or favorable checkpoint selection.

The first unexecuted step is Root's separate execution allocation, followed by
DM freezing a new prospective B card/master/prediction and the same CM's bounded
implementation/acceptance. No new card/master/prediction/task/run/Pro Send has
been created, no extra P74 evaluation is allowed, and no family/lifecycle/priority/
recast/C/formal-UAV-entry decision follows. Root owns integration, allocation and
reclamation; DM retains the scientific recommendation and this designated
checkout for its next actual assignment. Any exact-SHA remote checkout retirement
must preserve the named output/receipt evidence and follow Root's normal cleanup
ownership; no evidence is deleted by this return.
