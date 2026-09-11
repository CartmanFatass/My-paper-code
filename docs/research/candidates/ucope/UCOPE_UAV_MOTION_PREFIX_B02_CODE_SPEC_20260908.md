# UCOPE UAV motion prefix B02 — complete CM code specification

This implements the common per-agent clipping amendment in the
[B02 card §§2–7](UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md#2-unchanged-host-ownership-and-information).
The card supplies the fixed host, T/G/H comparison, RNG domains, independent
units, primary, MEI, branches and prospective scientific caps. This is a
prepared specification under P33, not a coding or runtime dispatch.

## 1. Starting source, checkout and ownership

Use the existing `codex/ucope` checkout at
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`. Exact
committed starting source is **b5607f46fea91379582af8bf87e60b61bc4a269b**;
the package/runner/test surfaces below are byte-identical to accepted
**9c541a8047b8c33e90f09aa65e326180343a23a0**. The starting merge includes
published P33 inputs and retains the complete direction source. Main P33's
tree did not contain several accepted package/test paths; do not substitute
that incomplete tree for this starting source. Later document-only commits
do not change the bound code surface.

Owned changes, only for this complete amendment:

- `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py`: expose
  agent-owned compound log densities while retaining the existing joint
  calculation for historical modes; same models, sampling and entropy.
- `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`: collect
  old agent densities and use the correctly masked summed-agent clipped loss
  in B02. Entry points are `collect_episode`, `clipped_policy_loss`, `update`
  and the existing recurrent reconstruction.
- `experiments/candidates/ucope/uav_motion_prefix_b01/study.py`: route B02
  through collection/update, preserve exact counts/clocks, and label its
  configuration, checkpoints and pair aggregate correctly.
- `scripts/run_ucope_uav_motion_prefix_b01.py`: add the explicit `--pair b02`
  route for real mode, its engineering fixture and read-only aggregation.
- `tests/experiments/candidates/ucope/uav_motion_prefix_b01/test_agent_clipping.py`
  for the new credit checks; existing `test_motion_prefix.py` and
  `test_pair_plumbing.py` only where their coverage needs the new route.

Do not copy/move the study or add another runner/framework. `environment.py`,
model architecture/initialization, base environment/adapter, other candidate
paths, runtime/governance configuration and historical evidence are preserved.
Internal helper signatures and harmless factoring are CM choices; the
scientific behavior, public CLI/result identity and checks below are fixed.
No third algorithm, clipping sweep, head weighting or broader baseline work.

## 2. Preserved collection and model semantics

Keep the exact accepted factory arguments, five-agent order, 108-component actor
and 136-component critic feature ordering, pre-decision critic input, separate GRU
histories and native reward selection. Architecture, tanh density/Jacobian,
stored pre-tanh u, separate generators and duration sampling remain the
accepted source and card §§2–4. Parameters remain G 66,311/T 66,441 including
T's 130 duration parameters. No normalization, sensor, ID or privileged
feature is added. G retains every legal velocity; neither arm's observed
step/action/optimizer budget changes.

T's one t0 duration sample is 1 or 4. Actual-decision masks remain generated
by `HoldState`: d4 omits fresh velocity samples at t1–3, resumes at t4,
and never opens another duration choice. Every primitive observation,
hidden-state advance and reward stays in collection. H remains zero velocity
with no actor or optimizer. Constructor/reset/partial-step accounting and
diagnostic dependency behavior remain unchanged.

## 3. Agent density, old storage and masks

For B02 retain the agent dimension after summing only the three velocity
coordinates. For each agent i:

`ell_i = where(velocity_mask_i, tanh_velocity_logp_i, 0)
         + where(duration_mask_i, selected_duration_logp_i, 0)`.

Duration mask is true only for T at t0, where the same agent also has a
velocity decision. The compound ratio contains that owner's velocity and
duration together. No duration-only clip/loss coefficient or per-coordinate
ratio is permitted. A change to another agent's selected density cannot
enter this agent's ratio through a team sum.

Collect/detach old ell as shape **[H,5]** in each B02 episode and **[2,H,5]**
in a two-episode rollout, beside unchanged values/rewards [H] and action
masks [H,5]. H's unused density can be a zero five-vector. Inactive density
entries are zero, and inactive actor terms are explicitly masked in the
loss. Update finite checks for the vector shape (all required entries),
preserving existing nonfinite-stop semantics; scalar truth conversion of
a five-element tensor is not valid. Do not sum old values over agents,
recompute them after an update, resample u or detach new densities.

Keep `joint_terms` and the historical scalar joint-loss behavior available
for existing P21/P24 routes and their focused checks. B02 selects the new
grouping explicitly; no historical run is silently relabelled or reinterpreted.
These are two named scientific objectives in the existing study, not an
extensible configuration/versioning or compatibility subsystem.

## 4. Update and normalization

Targets and normalized advantages remain [2,H]: sum all remaining primitive
team rewards within an episode, no GAE/bootstrap/duration division, subtract
collected old scalar values, normalize once over all 512 rows using population
SD+1e-8, detach. Broadcast A along the final agent dimension only when forming
the surrogate. Reconstruct new ell [2,H,5] through the same 32-step chunks and
collected initial h0; no new observations, reset or gradient boundary.

Set r=exp(new_ell−old_ell). For B02:

`policy_loss = -mean_(E,H)(sum_i velocity_mask_i *
    min(r_i*A, clamp(r_i,.8,1.2)*A))`.

Do not flatten into a mean over 512×5, divide by active-agent count, drop
all-held rows from the primitive denominator, or normalize A again by head.
An all-held row has zero actor contribution; critic loss and recurrent
processing remain. At r=1, the policy gradient matches the old joint
objective's scale under the same masks/advantages. Its scalar loss may
differ by constants; away from the behavior policy the gradients need not
match. This is the selected algorithm change.

Entropy remains the existing velocity/duration actual-decision sum over
agents, then mean over primitive rows. Critic MSE uses every row.
Total loss is policy +.5*value −.01*entropy, with the same joint Adam,
global .5 gradient clip, four full-rollout epochs and actual update counters.
No target-KL early exit, actor/critic split, extra learning or optimizer reset.

## 5. B02 route, identity and historical separation

Extend `declared_masters` with **b02 → (7001,7002)**. Public future forms:

~~~text
python scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --seed 7001 --out <new-run-directory>
python scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --seed 7002 --out <different-new-run-directory>
python scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --aggregate <7001-summary.json> <7002-summary.json> --out <aggregate-directory>
python scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --engineering-fixture --seed 9001 --out <fixture-directory>
~~~

The first three lines specify interfaces, not permission to launch. Default
P21 and explicit P24 CLI/aggregation behavior remain as at starting source.
The existing legacy 9001 fixture remains; only the B02 fixture smoke in §8
is required for the later CM task. Do not multiply smoke executions.

B02 real summary identifies `object="UCOPE-UAV-MOTION-PREFIX-B02"`,
`pair="b02"`, `declared_masters=[7001,7002]`,
`ratio_grouping="agent_compound"`, the new B02 card path and `card_section=5`.
Its `configuration` (also saved in final checkpoints) includes the selected
pair and ratio grouping. Fixture mode stays `ENGINEERING_FIXTURE`, with
zero UAV calls, fixture dimensions/seed, selected B02 algorithm/card and
`card_section="CODE_SPEC §8"`; preserve its fixture pair/declared-seed labelling.
Episode/rollout rows retain their existing seed/arm/phase/time association.

The B02 aggregate selects exactly the two fresh distinct real-mode summaries
with matching B02 object, pair, card and grouping. Reject mixed old/new
objectives, duplicate/wrong masters or a synthetic/UAV mixture in this
primary; do not infer B02 labels from missing metadata. Preserve existing
P21 historical metadata defaults and P24 checks unchanged. Extend only the
existing question-specific pairing check, not a JSON validator or manifest
system. Include the B02 identity in its aggregate result. No runtime source
hash/currentness or new launch-permission guard is requested.

## 6. RNG, measurements, arithmetic and publication

Use card §4's exact b+domain seeds, equal common initialization and separate
arm generators. Old/new ratio calculation consumes no random numbers.
Keep every episode/rollout/exposure/diagnostic measurement already selected,
final sampled T/G/H evaluation and ordinary files. No clipping telemetry
series or additional checkpoint evaluation is required. Collect 32 evaluation
episodes per arm/pair,256 actual steps each. Independent unit remains a
training pair, n=2. Native arithmetic and UP/WITHIN/DOWN follow card §5;
conditional evaluation SE never replaces training-population uncertainty.

Preserve actual optimizer, true velocity/duration decisions and parameter
displacement counts. G training has 655,360 velocity decisions/fit; T has
655,360−3*n_d4 with 2,560 duration decisions. Each final G evaluation has
40,960 velocity decisions; T has 40,960−3*n_d4 and 160 duration decisions.
All 4,096 proposed Adam calls and 573,440 team steps remain real work if later
allocated. Do not manufacture nonzero head movement or favorable results.

Keep complete clocks and stop/dependency semantics in accepted `run_pair`:
startup/common initialization charged to T; G includes H/pair publication;
preserve partial records and record any late overrun. The proposed 1,800/3,600/
7,200-second caps are unchanged and no retry/resume/automatic fallback is
introduced. Algorithm identity is a scientific configuration fact, not a
new schema version. No optional diagnostic failure erases independently
trustworthy native returns.

## 7. Engineering scope and future dispatch boundary

Engineering scope §4: **none**. No dependency installation, copied framework,
worker, profiler, validator, generic registry, versioning/resume layer or new
resource machinery. Preserve source≤2,000 added lines, runner≤600 and the
existing focused test/smoke bounds. Ordinary in-scope corrections use the
same CM; a concrete scope/scientific conflict returns with its affected fact.

P33 executes none of the code/checks below. When separately commissioned,
CM may implement and perform §8's synthetic checks and independent credit
review. No real UAV constructor/reset/step, tuned-headroom run, source API
probe or scientific evaluation is part of engineering acceptance. Three CM
comparison enrollments are complete; P33 explicitly selects no fourth.
No old comparison administrative timeout/delegation restriction is imported.
Long committed-source checks use the remote-first route; ordinary short
checks may use the installed local scientific interpreter. Do not copy
uncommitted source into the remote execution checkout or upgrade interpreters.

## 8. Original focused acceptance and independent credit review

Retain the existing tests' information/critic timing, mixed-duration history,
native reward/MC targets, stable stored-u density, initialization/RNG/chunks,
actual updates, primary/uncertainty/dependency, clock/cap and readback coverage.
Preserve the historical single-joint-clip tests on their historical mode.
Add focused deterministic B02 checks for these changed boundaries:

1. **Grouping and signs:** five active agent ratios 1.05 at A=+1 produce
   summed B02 loss −5.25 with nonzero individual gradients; the historical
   team ratio 1.05^5 clips at 1.2. Mixed ratios above/below the interval with
   positive and negative A exercise the actual `min` rule. An inactive
   agent contributes zero value/gradient; all-held rows stay in the denominator.
2. **Gradient scale:** at new=old, compare gradients of the summed-agent
   objective with a directly formed joint log-probability reference under
   mixed masks and signed advantages. Check gradients, not equal scalar
   losses; forbid division by five or active count. Use ordinary FP32
   numerical tolerance (rtol1e-5/atol1e-6), not bit equality.
3. **Duration/storage wiring:** verify per-agent stored old shape and
   detachment, three-coordinate plus owned duration grouping only at t0,
   unchanged held sample counts, vector finite handling and nonzero eligible
   policy gradient. Inspect a B02 rollout/update so a helper-only test cannot
   leave the real path using joint clipping. All observations/critic targets
   remain, with no requirement that every parameter/head move.
4. **Route and primary:** dispatch both 7001/7002 through the actual CLI into
   Config/study with an injected synthetic collector (no real UAV call);
   verify b+domains and B02 grouping reach collection/update and checkpoint
   configuration. Pure aggregation uses synthetic difference arrays [1,3]
   and [4,6]: means 2/5, joint 3.5, conditional SE sqrt(.5), endpoint SD sqrt(4.5).
   Preserve negative/incomplete cases and reject cross-object/grouping inputs.

Use one complete B02 synthetic CLI fixture: master 9001, H=8, two training
episodes/fit, one 16-step rollout/fit, chunk 8, four epochs, two final episodes
per T/G/H. It uses the real B02 model/collector/Adam/publication path on the
existing synthetic adapter: **32 training +48 evaluation =80 synthetic team
steps;8 actual Adam calls;10 complete episodes;100 diagnostic frames;0 UAV
calls**. A favorable return or universal parameter motion is not acceptance.

Original commands for the later CM, from this checkout (not executed in P33):

~~~powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q tests/experiments/candidates/ucope/uav_motion_prefix_b01
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' scripts/run_ucope_uav_motion_prefix_b01.py --pair b02 --engineering-fixture --seed 9001 --out temp/directions/ucope/test/uav_motion_prefix_b02_fixture
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -c "import json,pathlib; p=pathlib.Path('temp/directions/ucope/test/uav_motion_prefix_b02_fixture'); s=json.loads((p/'summary.json').read_text()); c=s['counts']; assert s['mode']=='ENGINEERING_FIXTURE' and s['scientific_uav_calls']==0; assert s['object']=='UCOPE-UAV-MOTION-PREFIX-B02' and s['ratio_grouping']=='agent_compound'; assert s['configuration']['pair']=='b02' and s['configuration']['ratio_grouping']=='agent_compound'; assert (c['train_team_steps'],c['eval_team_steps'],c['team_steps'],c['optimizer_steps'])==(32,48,80,8); assert s['primary']['complete']; rows=[json.loads(x) for x in (p/'episodes.jsonl').read_text().splitlines() if x]; assert len(rows)==10; print('B02 fixture readback: 80 synthetic steps, 8 Adam, 0 UAV calls')"
git diff --check
~~~

One focused pytest command≤300 s; one CLI smoke≤60 s plus readback. Existing
direction scratch fixtures/paths remain; focused reruns need a concrete
correction. No broad UAV suite or additional diagnostics experiment.

Before technical acceptance, **independent credit review** inspects the actual
diff and focused evidence for grouping, sum/mean scale, old/new density
detachment, masks, t0 duration contribution, and their real collector/update
wiring. Retain original information/reward/RNG/count/primary and cap checks.
The reviewer verifies facts proportionately; no duplicate learner execution
or scientific inference is required. CM returns accepted commit/diff,
checks/fixture counts, review evidence and any concrete gap. Root handles
integration; DM retains science and a later named command owns real execution.
