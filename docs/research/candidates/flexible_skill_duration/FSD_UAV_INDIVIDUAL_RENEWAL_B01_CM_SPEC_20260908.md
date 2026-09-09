# FSD UAV individual-renewal B01 — bounded CM assignment

This is the complete prospective implementation handoff for Root. No CM has
been dispatched and no experiment is allocated by its publication.

## 1. Deliverable and starting source

Make the selected I/authentic-D0 native UAV comparison runnable, test the
changed behavior and primary output, obtain independent high-impact review,
then return one accepted implementation with exact future per-arm argv and
remaining execution facts. Do not run either scientific arm during this
implementation assignment. Root can issue the full subsequent technical
execution/observation/collection assignment without another scientific vote.

Use the existing `C:/Projects/HMASD-worktrees/codex-fsd` checkout, `codex/fsd`
branch, and existing CM `/root/dm_fsd_p47_resume/cm_am_fsd_b03_p47` when available.
Complete starting code revision: **335425e92cda16677fd1f4181e2c31730887e911**.
Relevant source matches the Pro input `de9af8f93d311426f2af069b1a0039765cdeef93`.
Reconcile the published card/spec commit before starting; document-only
descendants do not change that code surface. You are not alone in this checkout:
preserve others' edits and serialize overlapping files/index through commit/push.

Scientific contract: [card](FSD_UAV_INDIVIDUAL_RENEWAL_B01_SCIENCE_CARD_20260908.md)
§§2–6, implementing [P67 response](pro_packets/20260908_p67_uav_internal_renewal/archive/RESPONSE.md)
§§二–六. Its current [intake](pro_packets/20260908_p67_uav_internal_renewal/CONVERGENCE_INTAKE.md)
§§2–4 supplies conformance and the source findings. Read those scoped sections
and the owned/direct code below; do not reload the research history or rewrite
the card as a second contract.

## 2. Owned paths and code entry points

- New `scripts/run_fsd_uav_individual_renewal_b01.py`: one fixed-object arm runner
  and its in-process pair readout. Keep the whole runner within600 lines.
- New `tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py`:
  focused fake-only behavior/output tests, using local ordinary fixtures.
- New `docs/research/candidates/flexible_skill_duration/FSD_UAV_INDIVIDUAL_RENEWAL_B01_TECHNICAL_ACCEPTANCE_20260908.md`:
  delivered diff, focused checks/review, limits, committed source and exact future
  commands. DM owns card, predictions, intake, evidence interpretation and owner files.

Read-only reuse: E0 `_preserve_rng`, `_StepCounter`, parameter/exposure helpers,
configuration-field names and `_make_envs`/`_reset_all`; the ordinary
`HMASDAgent.step`, `store_transition_batch`, `update`, buffer clearing and
`get_d2_metrics`; `configs/config_1.py`; scenario1 and its adapter. Reuse their
accepted computation rather than copying the entire E0 script or introducing a
general runner framework. Core learner/config/environment, E0, corridor runners,
old tests and historical evidence remain unchanged. Ordinary local implementation
choices inside the owned runner belong to CM.

Concrete source facts affecting this deliverable:

1. E0 `_make_config`237–260 makes D0 for every non-off arm. `Evaluator.__init__`
   303–315 calls that builder again. Merely adding an I label or setting costs
   only on the learner would evaluate D0. Both fresh learner and evaluator must
   receive I's numeric costs and common caps before `HMASDAgent` construction.
2. E0 training647–689 stores a terminal transition, then replaces only the next
   policy observation after reset. The new loop must take **both** observation
   and state from reset info. Preserve the recorded terminal next values in
   storage and original done/reset semantics; do not edit or reinterpret E0.
3. `agent.step`3042–3133 dispatches the actual returned skills to the primitive
   actor and exposes authentic D2 metadata for storage. No external renewal
   mask or synthetic decision record belongs here. Ordinary actor2897–2980
   retains GRU memory across skill decisions.
4. `get_d2_metrics`2272–2330 already separates decisions, token-switch counts,
   causes, rows and segment lengths. Tables/metrics needed for each rollout are
   read before clearing buffers; distinguish cumulative totals and deltas.
5. Scenario1 reward80–125, UAV `step`265–351 and adapter248–274 establish scalar
   reward=team reward/6. The primary's6/500 factor applies only to published
   episode sums. Existing reward-info components are available without new
   trajectory logging or a reward redesign.

## 3. Preserved semantics and required behavior

### Arm, environment and learning loop

The production entry accepts only `--arm D0|I`, `--output-root <arm-dir>` and,
for I's pair readout, `--d0-summary <completed-D0-summary>`. Freeze other
scientific values to card§§2–3; no seed/threshold/budget sweep CLI. Keep the
existing defaults not explicitly changed by that card. Use real numeric
positive infinity for costs, not strings. JSON metadata may display `Infinity`
without turning nonfinite scientific outputs into valid values.

Each arm has one ordinary CPU4/FP32 HMASD learner, training seed770503 and
private environment seeds770503…770518. Use the genuine scenario1 observations,
states, continuous movement actions and unmodified scalar rewards. Every
primitive call's original step data and actual terminal next state/observation
reach storage. Subsequent policy input after done uses both fresh reset values.
Each rollout ends all16 lanes at H500; keep done-masked bootstrap and D2
terminal/credit semantics, without extra boundary sampling. Run five actual
updates with buffers cleared at the ordinary point. Preserve all outcomes.

Do not match the arms' sampled skills, realized gaps, token switches, endogenous
trajectories or optimizer counts. Both have common **team timing**, not common
team tokens. An I draw of its existing skill remains a real decision; zero
additional I gaps remains valid. Do not turn weak learning into invalidity or
require every parameter group to exceed a displacement threshold.

### Independent final evaluator and RNG

Create each arm's own evaluator only for the unique endpoint after update five.
Use32 environment lanes at780503…780534. Under the existing CPU RNG-preservation
context, seed evaluation RNG with780503, construct its own correctly configured
agent, sync that arm's final active modules and enabled normalizers, clear
evaluation buffers and reset all evaluation lane state. Use deterministic eval
mode, no optimizer update or normalizer learning. Keep learner model/buffers/
normalizers and its subsequent RNG state isolated through construction, sync,
reset and scoring. No shared evaluator, cross-arm weights, disk checkpoint
selection, corridor masks or forced same trajectory.

### Output and pair completion

Ordinary JSON/JSONL output is sufficient: `manifest.json`, five training rows,
endpoint per-episode arrays and `summary.json`, with runtime failures/partial
facts left in place. Retain card§4's count/exposure/renewal and native component
fields. Count real optimizer.step calls using existing helpers; update stages
or decisions are not optimizer counts. Required scientific counters are not a
request for broader profiling or an all-array archive.

D0 publishes its own final summary first. I publishes its own result and the
paired32-vector/native mean/sample SD/conditional SE inside its cap when the
named D0 output completes the card's comparison. Retain unscaled U and scaled
J=6U/500 values, and apply card§5's unchanged positive/within/opposite rule.
Check companion identity, endpoint IDs/seed law, specified arm configuration
and required counts where they affect comparison meaning; no byte manifests,
HEAD guard or generic internal schema layer. Missing/damaged D0 leaves readable
I-only facts and an incomplete pair, not a fabricated sign or a changed run.

Actual nonfinite action/reward/loss/parameter/primary output or a genuine
reward/information/update error stops affected work. Intentional cost infinities
and unused-group null exposure are distinct. No rescue evaluation after an
early failure, silent short-budget completion, replacement seed or automatic
retry. A final complete own-arm outcome and an incomplete pair are distinct.

## 4. Original acceptance checks

Use one focused fake-only suite for the changed production functions; fixtures
may shorten fake loops but cannot create a different scientific invocation.
The checks must assess these behaviors rather than only a completion flag:

- Both learner/evaluator constructions carry the correct I/D0 numeric costs,
  caps, seeds, CPU/ordinary dimensions and evaluation mode. No off/corridor path
  or evaluator silently reverting to D0.
- Fake actual skill/step-data/action markers reach environment and storage
  unchanged; store terminal next values first, then feed the next call both
  reset observation and reset state. A no-gap/same-token sample is valid.
- Five update stages feed later fake rollouts; only the fifth endpoint is
  evaluated. Recorded optimizer counts are real wrapped calls in the fixture,
  and evaluator operations change neither learner state nor its RNG sequence.
- A known scalar-return fixture verifies6/500 native scaling, paired ordering,
  sample SD(ddof1), SE/sqrt32 and inclusive MEI endpoints. Wrong/missing companion
  data cannot yield a complete paired sign; own-arm facts remain readable.
- A relevant nonfinite primary/action/loss fixture takes the incomplete/failure
  path, while intended numeric cost+infinity remains a valid configuration.

Exact original local check commands, after implementation:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m py_compile scripts/run_fsd_uav_individual_renewal_b01.py tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/flexible_skill_duration/uav_individual_renewal_b01/test_learning.py
git diff --check
```

The fake suite and syntax checks add no production model, environment, training,
evaluation or cost probe. Do not rerun E0 fingerprint/probes, old corridor suites
or historical experiments by default. Require one independent high-impact
review of configuration propagation, actual action/storage/reset boundary,
RNG/evaluator isolation and primary measurement. CM resolves in-scope findings
and returns the actual diff, captured focused test evidence and reviewer result;
DM checks the affected artifact and interprets science without repeating all tests.

## 5. Budget, stop and return

Engineering-scope§4: none; new non-test research code≤2000 lines, runner≤600,
the research-directory test budget≤300s excluding any separately authorized
smoke. No real-learner smoke or profile is authorized by this implementation
handoff. Ordinary implementation/check repairs continue to acceptance or a
concrete scientific/scope conflict; they create no scientific retry allowance.

The three-batch CM comparison has completed all progress rows01–03 in
`docs/project/CM_MODEL_COMPARISON_20260907.md`; no fourth enrollment. Root receives
this complete common spec, exact starting source and original checks before any
coding dispatch. This records the completed temporary program, not an exclusion
invented for a new assignment.

After explicit-path commit and immediate push, return the accepted source SHA,
owned changed paths, focused test/review evidence, source/runtime limitations,
and the exact future D0/I argv with card seeds/paths. Scientific root when later
allocated: `temp/directions/flexible_skill_duration/exp/uav_individual_renewal_b01_770503/`.
Use its D0/I subdirectories, without creating them now. A future portable run
uses the configured remote node, an exact-SHA detached execution worktree and
existing task supervisor. Outer timing must cover fresh admission/imports
through each closed-file publication: D03600s, I18000s, sum21600s, no grace or
reuse of time. Merely returning a process handle would not finish CM's later
observation/collection/technical acceptance assignment.

The supplied [machine cost record](FSD_UAV_INDIVIDUAL_RENEWAL_B01_PREPARATION_FACTS_20260908.json)
contains the accepted old-work1617.82s/16178.2s scenarios and their limits. Check
whether the implemented work changes those known multipliers; a concrete
over-cap projection returns the exact gap. Unknown remote rate does not mandate
a new pilot. No source-currentness machinery or additional launch gate follows.

Root integrates accepted code and supplies any future full execution allocation;
DM `/root/dm_fsd_p47_resume` receives technical results and owns the all-outcome
scientific intake. A defect in this implementation is corrected here before
acceptance; a required mechanism/comparator/budget change returns its exact
decision need to DM through Root. No experiment, broader family, new Pro request
or automatic successor is authorized by this specification.
