# FSD_NATIVE_RENEWAL_CONTROL_A01 — complete CM task and code spec

2026-09-07, P15 prospective engineering assignment. **Coding has not started.** Root must
capture this new assignment under `docs/project/CM_MODEL_COMPARISON_20260907.md` before any
solo CM implementation. All five arms receive these same complete bytes, the linked card,
the same applicable instructions and the same committed source. Comparison copies add no
scientific invocation; normal independent review/integration follows the measured returns.

## 1. Five-item assignment

1. **Deliverable/goal:** implement the selected fixed-checkpoint C/H/G native-renewal
   measurement as one lean research runner and focused tests. Deliver a reviewable diff,
   original check output and actual remaining gaps. Implement all policy, load/reset,
   scoring and publication paths; no scientific execution is part of this assignment.
2. **Ownership:** production authoring checkout is `C:/Projects/HMASD-worktrees/codex-fsd`,
   branch `codex/fsd`. New code only at `scripts/run_fsd_native_renewal_control_a01.py` and
   `tests/experiments/candidates/flexible_skill_duration/native_renewal_control_a01/test_control.py`.
   Root maps repository-relative paths into each isolated comparison worktree. You are not
   alone in this repository: preserve other edits; do not edit the card, shared code/config,
   historical evidence or another arm. No new authoring branch, package or dependency.
3. **Preserve semantics:** card sections 2–5 bind the exact artifact, host, state/action seam,
   RNG, C/H independent trajectories, G, primary units/counts and complete wall caps. The
   interface below makes those choices concrete; do not reinterpret them as synchronized
   D2 sampling/credit or learning evidence. Existing source is read-only.
4. **Acceptance:** sections 3–5 below, card sections 3–5, evidence-spec sections 4, 5.1,
   11.8.5–7 and 11.9, and engineering-scope sections 3–5. Run the exact original commands in
   section 5. Scientific-risk review of loading, feedback and reward/paired output occurs
   after the comparison; test success alone does not establish a measurement result.
5. **Budget/stop:** common 3,600 s engineering limit including startup, implementation and
   checks; focused pytest ≤300 s and one 24-step engineering fixture as specified below.
   No checkpoint load of the selected artifact, real HMASD learner construction, scientific
   episode, resource-admitted launch, transport request or additional scientific budget.
   Comparison arms leave files for collection and do not commit, push, spawn, message other
   tasks or modify shared/runtime configuration. Return partial work on a concrete blocker.

## 2. Required committed inputs and focused source pointers

Scientific binding: `FSD_NATIVE_RENEWAL_CONTROL_A01_SCIENCE_CARD_20260907.md` sections 1–6.
Read the card and this complete spec. Use the following implementation-relevant source at
input `9fce9e70276ee7e92d29eb51a71a674e3d351621`; the publication commit delivered to Root
adds this task/card and leaves these source bytes unchanged. Root records the complete
publication SHA as the matched starting source, with no working changes. The selected
checkpoint is external frozen evidence, not required or permitted in comparison checks.

| Source | Relevant entry points/ranges |
| --- | --- |
| `envs/relay_corridor/config.py` | `RelayCorridorConfig`, entity mappings and parameter record, lines 43–169 |
| `envs/relay_corridor/adapter.py` | constructor/reset/step, lines 38–154; batched shapes, scoring-time info versus next state |
| `envs/relay_corridor/host.py` | `step`/observations, lines 266–405; score before renewal/transition |
| `envs/relay_corridor/references.py` | `GreedyOnPublicState.reset/act`, lines 436–468 |
| `scripts/run_flexible_skill_duration_e2.py` | module-level `E2CorridorConfig`, lines 165–172; evaluator sync/reset, lines 456–508 |
| `scripts/run_flexible_skill_duration_e3.py` | `PairedEvaluator.run`, lines 239–299 |
| `hmasd/agent.py` | constructor/device/config, lines 377–420; `train`, `clear_buffers`, `reset_env_state`; deterministic `step`, lines 3087–3160; saved network/config/normalizer fields, lines 7143–7293; normalizer restore, lines 7621–7644 |
| `config.py`, `config_1.py`, `hmasd/networks.py`, `hmasd/utils.py` | existing imports and configuration dependencies; expand only for a concrete field/state question |
| `AGENTS.md`, `docs/AGENTS.md`, `scripts/AGENTS.md`, `tests/AGENTS.md` | applicable focused-reading, ownership, research runner and testing instructions |
| `.codex/hmasd-compute.toml` | card-bound future remote CPU/runtime route; no launch during comparison |

Reuse the prior P13/state analysis linked by the card. No literature retrieval, whole-history
reproduction, E4 census, baseline retuning or source survey is part of this engineering task.

## 3. Runner CLI and fixed-policy restoration

Provide standard `argparse` and `main(argv=None)` with these common external modes:

```text
--policy G|C|H --seed 770103 --launch-sha <accepted-implementation-sha>
--out <this-policy-root> [--checkpoint <selected-checkpoint.pt>]
[--panel-inputs <completed-G-summary.json> <completed-C-summary.json>]

--engineering-fixture --seed 770103 --launch-sha ENGINEERING_FIXTURE --out <fixture-root>
```

Production mode fixes N6/K2/Z4/R2/H400/Delta1/hazards(.02,.20), IDs0…31, lanes32,
constructor seed2, CPU/4 threads and a 180 s complete-policy deadline. `--seed` records the
selected host master seed; this assignment supports the card value, not a seed sweep. Require
the checkpoint for C/H; G must not load it. `--panel-inputs` is required only for H and means
the two completed prior policy outputs in that order. No flag to change horizon, lane count,
weights, dtype, device, cap, retry or resume the scientific profile. The fixture mode needs
neither policy nor checkpoint arguments and rejects a supplied checkpoint.

Resolve repository imports relative to this script, not an absolute user directory. Keep
actual HMASD/checkpoint imports behind the production C/H loading path. Resolve the real
`run_flexible_skill_duration_e2.E2CorridorConfig` pickle class before trusted local
`torch.load(..., map_location='cpu', weights_only=False)`; do not invent a replacement class.
Read the selected checkpoint once per C/H process. Deep-copy its `config`, change only
`num_envs` to32, and pass an explicit CPU device and log directory beneath this policy root
to `HMASDAgent`. Keep source/checkpoint dimensions, D2 settings and recurrence intact.

Restore active modules from the existing save keys with strict state-dict loading:
`skill_coordinator`, `ha_ctse_editor`, `low_level_compact_extractor`, `process_encoder`,
`process_outcome_predictor`, `process_contrastive_head`, `skill_discoverer`,
`team_discriminator`, `individual_discriminator`. Disabled/None components remain disabled;
the list does not assert all nine are active. A missing/mismatched active field is a concrete
loading error, not permission to use initialization or non-strict residuals. Do not restore
optimizers/schedulers or training-progress state for fresh evaluation.

Copy both enabled ValueNorm mean/var/count from `valuenorm_state`, retaining their recorded
values and dtypes. Missing required statistics must fail the dependent load. Preserve disabled
observation/state normalization; no default-stat substitution, updates or normalizer redesign.
Use `train(False)` and no-gradient deterministic action calls. Standard constructors may create
optimizer objects, but no optimizer.step, training update or storage-for-learning call occurs.
The required module/stat restore is local measurement logic, not a new checkpoint format,
runtime hash guard, universal validator or full-resume equivalence system.

## 4. Evaluation, measured output and time

Expose these two small inspectable computational seams; other internal structure is CM's choice:

- `apply_renew_mask(policy, internal_mask, public_flag, t)`: C returns an independent copy
  of internal_mask; H does the same at t=0 and returns a copy of public_flag thereafter.
  Inputs are Boolean `[lanes,N]`; neither input nor the controller's step_data is mutated.
- `summarize_panel(policies)`: input is the three policy summaries keyed G/C/H. Produce all
  paired quantities defined below. Check the directly necessary common key/order, host,
  horizon and completed-count correspondence; never silently align/filter nonmatching rows.
  No internal JSON schema package or generalized validation framework is needed.

At a fresh episode start, reset the adapter once, use its observation **and** state, clear
the C/H buffers and reset each lane, set env_steps=0/dones=false, or reset G's plan. Preserve
the existing evaluator's observation float32/global-state float64 conversions. Execute exactly
H400 scoring steps in one batch; no additional hidden-state reset or episode-ID advancement.
Use the existing deterministic `agent.step(..., return_step_data=True, build_infos=False)`
for C/H. Save the original mask for counters, read H's **current pre-step public flag** from
its host, choose the applied copy, and call `adapter.step(actions, renew_mask=applied)`.
G calls existing `GreedyOnPublicState.act` then maps integer roles to K2 one-hot actions.
Every next input comes from that policy's actual adapter result. Correctness labels never
become controller inputs. No controller weights or state are shared between policy processes.

Accumulate reward in float64 and scoring-time masks/correctness from the returned step info.
Do not substitute `state_info` after transition for `lease_fresh` at scoring. Return per-episode
arrays in the original ID order. For each policy's `summary.json`, include these concrete keys:

| Key | Meaning |
| --- | --- |
| `object_id`, `mode`, `policy`, `launch_sha` | ID `FSD_NATIVE_RENEWAL_CONTROL_A01`; mode `checkpoint_observation` or `engineering_fixture`; actual policy and source label |
| `master_seed`, `episode_ids`, `host`, `counts` | Common inputs and actual counts; count keys are `completed_episodes`, `scoring_steps`, `agent_observations`, `agent_step_batches`, `greedy_act_batches`, `model_constructions`, `checkpoint_loads`, `training_starts`, `training_transitions`, `optimizer_steps` |
| `checkpoint`, `normalization`, `controller_seed`, `device`, `torch_threads` | Selected identity/path and successful required-load facts for C/H; G uses null where inapplicable; no historical-weight claim for fixture |
| `return_full`, `return_post` | Per-episode shared native reward means, denominators400 and399 in production |
| `eligible_full`, `eligible_post`, `wrong_full`, `wrong_post` | Per-episode agent-opportunity and wrong-role counts |
| `role_loss_full`, `role_loss_post`, `wrong_rate_full`, `wrong_rate_post` | Reward loss Delta×wrong/(H×N) or Delta×wrong/((H−1)×N); conditional rates are null when eligibility=0 |
| `internal_renew_full`, `internal_renew_post`, `applied_renew_full`, `applied_renew_post` | Per-episode agent-mask counts; internal fields null for G |
| `status`, `failure`, `wall_seconds_before_publication` | Status `complete` or `incomplete`, and any concrete failure; this wall field alone is not complete invocation wall |

The panel contains `policies` (the three summaries), `paired` and total `counts`. `paired`
has `h_minus_c_full`, `h_minus_c_post`, `g_minus_h_full`, `g_minus_h_post`; each holds
`differences`, `mean`, `stderr` using ddof1. H's successful `summary.json` additionally carries
this `panel`, using the base H summary before attachment so there is no recursive object.
The standalone fixture writes the panel as its own `summary.json`, with
`object_id`, `mode='engineering_fixture'`, `launch_sha` and total counts at its top level.
All JSON values are finite numbers or explicit null; no NaN/Infinity. No pass/fail science,
significance, equivalence or automatically selected next object is computed.

Start the runner's absolute deadline at process entry, before heavy imports, model/host setup
or reading earlier summaries. Check it through loading, evaluation and publication. After all
files have been closed, emit a final one-line JSON status to stdout with `status`,
`complete_wall_seconds` and `cap_breached`; success requires finishing within the deadline.
This final wall includes publication; do not reset a timer around only the loop or declare
success from a pre-publication timestamp. Existing external wall enforcement at a later launch
also counts interpreter startup. A late publication returns nonzero/cap-breached even if
numerical data were written; Root/CM use the final process facts for conformance. Preserve
partial outputs and actual counts where available; do not recover/retry or infer scientific
polarity from a load, cap or publication failure. No mandatory RSS implementation is needed.

Write outputs only below the caller's named `temp/directions/flexible_skill_duration/exp/`
root. For later production, G→C→H is a simple operator command list with one existing fresh
admission before each process, stopping on a failure. Reading G/C and publishing the panel
belongs to H's 180 s. No fourth postprocessing scientific invocation or new queue supervisor.

## 5. Original focused acceptance checks

Implement a single focused test file. Use small arrays, standard monkeypatch and stateful fakes;
no selected weights, actual `HMASDAgent` construction or new training. It must check these
changed boundaries, without replaying unchanged historical suites:

1. C versus H applied-mask rules before/after reset, copying and preservation of internal
   mask/step_data. A public flag must be read before the host action, not after transition.
2. Fresh observation **and** state, buffer/lane reset once at entry, deterministic calls and
   normal recurrence across steps. A stateful fake host/controller must produce differing
   later inputs after differing applied renewals; H must receive H's future, not C's.
3. Hand-computable reward and scoring-time eligible/wrong arrays, full versus post denominators,
   paired sign/mean/ddof1 standard error, null rates for zero eligible opportunities, and a
   deliberately mismatched episode order that is not silently paired. Include G's reset
   convention and an example where post-transition freshness would give the wrong answer.
4. A synthetic checkpoint payload with tiny module state dicts: all active fields restore,
   required missing/mismatched network and ValueNorm fields fail, disabled fields stay off,
   config changes only num_envs, statistics remain unchanged, and no optimizer.step is called.
   Standard monkeypatch replaces checkpoint reading/agent construction; do not build a factory
   or registry to support this test. No real learner is needed to check the restore contract.
5. An injected/monkeypatched clock shows that loading and final publication consume the same
   absolute budget: crossing it in either stage produces non-success and no renewal of the
   deadline. Do not wait 180 s, load real weights or run an extra timing probe to check this.

The one CLI engineering fixture uses N6/K2, **2 lanes and H4**, the same three policy loops
with a stateful fake C/H controller and existing adapter/Greedy. Use hazards(0,1); all other
host parameters match production. The fake controller keeps a per-lane call counter, reset
to zero only at episode entry, and emits an internal renewal at counter values 0 and 2.
It emits one-hot role 1 when its own current normalized `segment_age` observation is ≥.5,
role 0 otherwise, reading the existing host's named observation slice; increment its counter
after each step. This fixed fake supplies a later action/state difference without a learned
model. It is **24 scoring steps / 144 agent observations**, not a result for
this card; C/H weights, training, actual HMASD construction and checkpoint loads are all zero.
The fixture exercises the changed action/feedback/output path; label every output accordingly.
No second fixture run is needed when the original one and focused tests pass without change.

Run exactly these original commands from each supplied worktree, using the same existing
interpreter. Root's common prompt remaps only the checkout root, never the source/spec/checks:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/native_renewal_control_a01 tests/experiments/candidates/flexible_skill_duration/native_renewal_control_a01/test_control.py
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_fsd_native_renewal_control_a01.py --engineering-fixture --seed 770103 --launch-sha ENGINEERING_FIXTURE --out temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_engineering_fixture
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -c "import json,pathlib; s=json.loads(pathlib.Path('temp/directions/flexible_skill_duration/exp/native_renewal_control_a01_engineering_fixture/summary.json').read_text(encoding='utf-8')); assert s['mode']=='engineering_fixture' and s['launch_sha']=='ENGINEERING_FIXTURE'; assert set(s['policies'])=={'G','C','H'}; assert s['counts']['scoring_steps']==24 and s['counts']['agent_observations']==144; assert s['counts']['checkpoint_loads']==0 and s['counts']['optimizer_steps']==0; assert all(len(v['differences'])==2 for v in s['paired'].values()); print('fixture readback OK')"
```

The readback reads only the already-written fixture; it adds no environment call. Record exit
codes, focused check wall, fixture counts and any unmet condition with the diff. Stop the measured
task at that return. No scientific smoke/load at the selected path is authorized. A future
actual load/reset or runtime failure is still possible and is not hidden by these engineering
checks; it limits the dependent future measurement under the frozen cap.
