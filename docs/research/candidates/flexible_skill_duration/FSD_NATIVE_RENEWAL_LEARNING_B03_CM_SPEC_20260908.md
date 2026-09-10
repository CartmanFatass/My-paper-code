# FSD native-renewal B03 — bounded authentic-D0 implementation specification

P46 prepares this complete assignment; it does not dispatch implementation or
execute code, tests, models, hosts or fixtures. A later named coding assignment
reuses CM `/root/fsd_cm_baseline_a01` and its existing independent reviewer.
P46 explicitly requests no fourth CM model comparison. Root receives this same
complete specification and original checks before any later CM dispatch.

## 1. Deliverable and exact starting source

Make the selected one-pair H/authentic fair-D0 k5/G comparison runnable with
training770403/evaluation770404, correct comparator identity and complete caps,
while retaining B01/B02 defaults and outcomes. Reuse the existing learning path;
do not copy its runner or change the scientific contract.

Designated checkout: `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd`.
Complete starting revision: **a74ed196f8c7b7dbabd1492d5aa077366be65f40**.
The accepted shared B01/B02 runner/wrapper/test source is the same as
`d961c58268353f215d3ffddf0d83927e6318541d`. Reconcile this published spec/card
commit before future dispatch and record that HEAD and any starting changes.
Document descendants do not change these source bytes; no new authoring branch
or worktree is needed. Other writers may be active: preserve their edits and
serialize overlapping edit/index ownership through check, commit and push.

Scientific authority is [B03 card](FSD_NATIVE_RENEWAL_LEARNING_B03_SCIENCE_CARD_20260908.md)
§§2–7, implementing [P45 RESPONSE](pro_packets/20260908_post_b02_convergence/archive/RESPONSE.md)
§§三–五 and the actual implementation boundary§六. Reuse
[B02 technical acceptance](FSD_NATIVE_RENEWAL_LEARNING_B02_TECHNICAL_ACCEPTANCE_20260908.md)
for the unchanged24 fake cases and current RNG/evaluator path. Do not replay the
old experiments, read the full history or write another science-contract document.

## 2. Owned paths and concrete source findings

- `scripts/run_fsd_native_renewal_learning_b01.py`: the CAPS mapping,
  `base_summary`, `build_learner`, `summarize_panel` and `main`, with only the
  selector/configuration/metadata/primary-output changes in§3.
- New `scripts/run_fsd_native_renewal_learning_b03.py`: a thin fixed B03 entry
  delegating to the shared implementation, following the existing B02 pattern.
- `tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py`:
  extend the existing fake-only changed-boundary tests. Preserve the24 existing
  cases and their original assertions/semantics; no separate fixture framework.
- New `FSD_NATIVE_RENEWAL_LEARNING_B03_TECHNICAL_ACCEPTANCE_20260908.md` in this
  direction directory: concise delivered diff, focused checks/reviewer findings
  and future argv. DM owns card, predictions, science intake and owner records.

Keep `applied_mask`, `collect_training`, `evaluate`, `final_evaluation`,
`paired_statistics`, `completed_arm`, finite/deadline/publication behavior and
core/environment/E0/E2/E3 code unchanged except any strictly necessary call-input
threading in the named surface. No B02 wrapper edit or historical evidence edit
is needed. B03-specific spread reporting belongs in its pair assembly, not a
changed legacy statistical rule.

Source facts that determine the change:

1. `build_learner` currently always calls `arm_parameters("large","d2")`.
   E3 `arm_parameters` supplies authentic D0 with numeric infinite costs and
   k5/caps5; `build_corridor_learner_config` sets config.k and those overrides.
2. `applied_mask` already applies the authentic internal mask for every learned
   policy other than H. Both training and evaluation pass the actual sampled
   mask into it and store the original learner data. No external k5 mask is needed.
3. `final_evaluation` already forwards the returned arm overrides into the
   existing E2 CorridorEvaluator, which rebuilds the actual matching config,
   syncs own weights/normalizers and isolates all RNG. Keep that connection.
4. `write_summary(...allow_nan=False)` needs a readable representation of the
   two declared D0 +inf configuration costs. E0 `_jsonable` already represents
   positive infinity as the JSON string `"Infinity"`. Runtime tensors and loss
   or reward outputs must not be sanitized by this helper.
5. `summarize_panel` currently requires equal learner_config and labels C/H.
   Authentic H/D0 intentionally differs in clocks/costs and derived buffer sizing;
   deleting the whole config check or retaining the C label would be wrong.
6. Existing caps/CLI/pair keys encode C900/H900/G60,sum1860. B03 must select
   D01200/H900/G60,sum2160 without altering B01/B02's C/H defaults.

The only expanded source read was for these concrete questions: E3
`arm_parameters`; E0 `_jsonable`/CONFIG_DUMP_FIELDS; corridor
`build_corridor_learner_config`; config_1.py `calculate_and_set_buffer_sizes`;
E2 CorridorEvaluator constructor/sync/reset. Same CM's P46 read-only trace also
found no intentional D0 nonfinite sentinel in step_data, get_d2_metrics or
update_info. Source pointers: hmasd/agent.py private gap initialization2396–2397,
step_data3118–3138, finite-filtered gap accumulation2605–2610,
get_d2_metrics2272–2330, update return7110–7141. Private diagnostic NaNs do not
enter these public finite-checked records. Retain strict checks; no extra runtime
exception or additional scientific verification is selected.

## 3. Complete behavioral change contract

### Fixed entry, identity and caps

The B03 wrapper fixes training_seed770403,evaluation_master770404,
object_id`FSD_NATIVE_RENEWAL_LEARNING_B03`, this B03 card path and the D0
comparison. Use explicit arguments with existing B01 defaults, as B02 already
does. A minimal shared selector is keyword-only `control_policy="C"`, with
B03 passing `"D0"`; ordinary local names may differ. Do not mutate module globals
at runtime, monkeypatch production bindings, add a generic configuration layer
or expose arbitrary scientific parameters on the CLI.

B03 accepts only `--policy G|D0|H`, fixed `--seed 770403`, `--launch-sha`, `--out`,
and H's `--d0-summary`/`--g-summary`. Only H reads companion summaries. B01/B02
retain G|C|H, their seeds and `--c-summary`; they must not silently accept D0.
Reject the wrong fixed seed/policy through argparse before output/model creation.
Shared constants may include D0's1200s cap; existing C/H/G values stay unchanged.
Every existing D0 deadline call must use1200, its summary cap1200 and panel sum2160;
H/G in B03 report900/60 and sum2160. Old objects continue to report sum1860.

Pass the fixed seed/master/object/card to actual summary, training and evaluation
consumers, not just JSON labels. Python/NumPy/Torch, the training adapter and
learner config use770403; all final adapters use770404 and IDs0–31. G's seed stays
null and it constructs no learner. No input is derived from time, path or prior
results. A later B01/B02 call in the same process retains its original defaults.

### Authentic learner and evaluator configuration

Choose `arm_parameters("large","d0")` only for the B03 D0 policy and the
existing `"d2"` parameters for H (and legacy C/H). Build with mode d2 and
k=overrides["skill_cap_k_max"]. Return those exact numeric overrides for the
independent evaluator. Positive infinity remains numeric in both real configs;
it must not become a finite stand-in, off mode, a string or null in computation.

| Configuration | B03 H | B03 D0 |
| --- | ---: | ---: |
| k / skill_cap_k_max | 40 / 40 | 5 / 5 |
| interruption_cost_c / interruption_cost_c_Z | .25 / .25 | +inf / +inf |
| team_cap_k_Z | 400 | 5 |
| high_level_buffer_size, training16×400 | 160 | 1280 |
| high_level_batch_size, training | 128 | 128 |
| high_level_buffer_size, evaluator32×400 | 320 | 2560 |
| high_level_batch_size, evaluator | 128 | 128 |

The last four entries follow the unchanged config_1 calculation from each arm's
own k and lane count. Do not override them to manufacture identical workloads.
All other declared architecture, losses, normalization, training schedule and
information/reward settings remain the same. No real config/model/host is
constructed in this preparation; these quantities were computed from source.

Encode only the two declared +infinity configuration costs as `"Infinity"` in
the stored config snapshot, reusing the existing helper on those metadata values.
Keep actual overrides/config numeric and `allow_nan=False`. Do not sanitize
arbitrary summary data, NaN/inf actions/rewards, sampled data, metrics, update
output or parameter exposure. Existing failure publication must retain its
last trustworthy boundaries. The full-stack D0 learner must not be replaced
with a fixed role reference, open-loop action replay or external periodic mask.

### Actual mask/storage path and pair assembly

D0's actual `step_data["d2_sampled_mask"]` is applied in training and evaluation;
current continuous actions and original step_data reach the host and storage.
H still applies the public mask only at t>0 with authentic internal credit.
No changes to reset/terminal, recurrence, reward, log probabilities, segment
returns, optimizer schedule or the final evaluator's sync/RNG/reset are needed.

Generalize the existing pair assembly only for the selected comparator. For
legacy C/H retain the full learner_config equality rule and old output names.
For B03 retain common identity, seed/master, population, device/precision,
endpoint and completed-learning checks. Permit only the declared arm differences:
k,interruption_cost_c,interruption_cost_c_Z,skill_cap_k_max,team_cap_k_Z and
the two high-level buffer/batch sizes derived from k and lane/horizon counts.
Check their expected H/D0 construction rather than accepting arbitrary drift.
At production sizing the table above applies; fake-sized checks follow the same
source arithmetic. No other common config mismatch is accepted. This adapts
existing comparison assembly; it is not a new schema/provenance framework or
launch gate. Old C or a different object's summaries cannot become B03 D0.

B03 panel names are `h_minus_d0_full/post`, `g_minus_h_full/post`, and
`g_minus_d0_full/post`; comparison_inputs names D0 and G. The primary includes
all32 differences, mean, sample_sd and conditional stderr. Reuse the existing
paired_statistics arithmetic and derive sample_sd from those same primary
differences at assembly; no new estimator or validation panel. Preserve the
full/post reference statistics and H-role-loss accounting residual. Do not
derive G−D0 from role loss or enforce either accounting residual as zero.
The unchanged .01 reading applies to h_minus_d0_full, using card§5's branches.

Missing/damaged D0 prevents pair polarity while retaining H's completed endpoint.
Missing/damaged G leaves reference_status incomplete and its actual failure;
independently credible H/D0 facts remain reportable. An H or pair completion
field does not declare the three-policy card complete when G is missing. Preserve
all partial observations and the existing dependence-based publication behavior.
No old companion, post-cap fill, additional endpoint or selected favorable pair
may supply an absent measurement. Weak valid D0 remains in the result.

## 4. Focused acceptance and independent review

Run one extended version of the existing24-case file, with no real HMASDAgent or
RelayCorridorHost construction. Its prior4.6721191s complete process wall is an
anchor, not a promised new duration. Total focused tests stay<=300s in the
research directory. Use the existing scientific interpreter and direction-scoped
basetemp from tests/AGENTS.md; this short fake-only suite may run locally. Do not
run the production script as a smoke test or create a separate cost/profiling run.

Required changed-boundary evidence:

- **Preserved old contract.** Keep the24 accepted B01/B02 cases and assertions:
  original defaults, masks/storage/update/reset, evaluator isolation, pair math,
  missing dependencies, deadlines and finite/publication failures. Changes to
  fixture call plumbing preserve the original scientific assertions.
- **Real parameter/config consumers with fakes.** B03 D0 reaches actual E3
  parameter selection and the real config builder with mode d2,numeric positive
  infinities,k5,caps5,age off and four threads before fake model construction.
  H remains finite-cost40/400. Check the source-derived buffer values and
  preserved common settings; verify770403 at actual seed/config/adapter calls.
  JSON publication/readback uses the declared cost strings, while actual learner
  and evaluator configs still carry numeric +inf. Preserve strict failures for
  runtime nonfinite values; no broad conversion to strings.
- **Mask and native storage wiring.** Exercise D0 through actual shared
  collector/evaluator functions with a fake sampled mask deliberately distinct
  from public flags and an externally recomputed periodic mask. Its actual mask,
  current actions, original step_data, native reward and next-state/reset values
  must be the ones applied/stored. This checks connection, not a new empirical
  proof of unchanged internal D0 logic. Retain the old3-step fixture cases; use
  a tiny legal horizon>=5 for new D0 config paths (e.g.10), not a changed D0 cap
  chosen to fit the old3-step fixture. No real-host mini experiment is allowed.
- **Independent evaluation and fixed wrapper.** The existing E2 constructor
  with fakes receives each arm's actual overrides, seed770403/master770404,
  own final modules/ValueNorm, clean lane state and preserved RNG. All evaluator
  optimizer counts stay zero. Exercise B03's thin shared-main G/D0/H delegation;
  G constructs no learner. Check subsequent B01/B02 defaults and wrong-policy/
  wrong-seed argparse rejection before output/model creation.
- **Pair meaning and primary output.** Fake complete H/D0 summaries with the
  expected config differences assemble successfully and produce directly
  checked full/post H−D0/G gaps, primary sample SD/conditional SE and positive,
  inclusive±.01 and negative branches. A nondeclared config difference, finite
  D0-cost substitution, old C/object/master or missing learned endpoint cannot
  supply the pair. Missing/bad G limits reference claims while retaining a
  trustworthy primary; nonzero G−D0 minus D0-role-loss is legal accounting.
- **Complete cap mapping.** Existing fake-clock boundaries demonstrate D01200,
  H900,G60 and panel2160 for B03, with1860 unchanged for B01/B02. Preserve existing
  deadline checks; final pair arithmetic and publication remain inside the cap.
  Retain the outer complete-command timeout requirement in the technical return.
  No real waiting, admission, detached setup or runtime launch is part of testing.

Reuse CM's independent Reviewer for this high-impact config/action/comparison/RNG
change. Its bounded question is whether the real D0 construction reaches both
training and evaluation and the actual sampled-mask/reward/storage path, while
the pair handles only intended configuration differences, declared infinity
metadata and correct caps/identity without changing old behavior. Supply this
spec/card's current sections, the source diff and focused results. The reviewer
reads the changed source independently; no second execution, new Scout or full
historical audit is required absent a concrete gap. CM keeps scientific choices
with DM and returns any scope/semantics conflict.

## 5. Budget, future argv and stop

Owned work is the bounded shared change, one thin B03 wrapper, extended fake
checks and technical acceptance record. Existing600-line runner and2000 new
non-test-code-line budgets apply; do not move/copy the runner to satisfy a ratio.
Engineering scope§4 additions: none. No generic selector framework, guard,
registry, retry/resume/checkpoint machinery, telemetry or repeated smoke follows.
The three-batch comparison enrollment is exhausted under P46; this is not a
fourth comparison or an additional scientific invocation.

Future CLI shape only, not launch binding or an allocation:

```text
python scripts/run_fsd_native_renewal_learning_b03.py --policy G --seed 770403 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/G
python scripts/run_fsd_native_renewal_learning_b03.py --policy D0 --seed 770403 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/D0
python scripts/run_fsd_native_renewal_learning_b03.py --policy H --seed 770403 --launch-sha <accepted-implementation-sha> --out temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/H --d0-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/D0/summary.json --g-summary temp/directions/flexible_skill_duration/exp/native_renewal_learning_b03_770403/G/summary.json
```

The later runtime task binds accepted source, on-node admission and complete
outer G60,D01200,H900 timeouts in that order. Card§6 contains its resource,
companion/failure and no-automatic-successor rules. Neither preparation nor
code acceptance creates a result root, detached cwd, handle, resource receipt,
command script or production model/host. No scientific run, extra pair, cap
extension, Pro Send or automatic launch is authorized by the coding assignment.

Stop at a complete inspectable implementation/check/review return or a concrete
owned-surface, semantics or budget gap. In-scope corrections return to the same
CM; no arbitrary retry limit replaces engineering acceptance. Commit owned paths
explicitly with attribution and scope:none, push immediately, and return the
full source/check/review commit plus actual remaining issue and future CLI to
DM/Root. Root integrates; subsequent readiness/runtime allocation is separately named.

## 6. Complete five-item handoff for Root's next named implementation command

1. **Deliverable/goal:** implement B03's one fresh H/authentic fair-D0 k5/G
   entry and truthful comparison/output path, with770403/770404; return technical
   acceptance under card§§2–7, not an empirical result.
2. **Owned paths/entry points:** shared B01 CAPS/base_summary/build_learner/
   summarize_panel/main, one thin B03 wrapper, the existing fake test file and
   B03 technical record (§2). Reuse `C:/Projects/HMASD-worktrees/codex-fsd`,
   `codex/fsd`, exact starting sourcea74ed196f8c7b7dbabd1492d5aa077366be65f40;
   reconcile the committed card/spec and preserve other writers' changes.
3. **Preserved semantics:** card§§2–6 and spec§3; authentic numeric infinite-cost
   D0 internals and sampled-mask application, own learning/evaluator/RNG,
   unchanged H/public G, and old B01/B02 defaults. No broad config-equality
   deletion, nonfinite-output sanitization, copied learner or scientific run.
4. **Acceptance:** spec§4's changed-boundary fake checks and independent review,
   retaining24 existing cases. Card§§3–5 and evidence-spec§§4,5.2,11.4,11.8.3,
   11.8.6–7 fix RNG, primary, exposure and failure meaning. D0 costs/clocks,
   actual consumers, permitted derived-config differences and H−D0 output
   must be visible in the delivered evidence.
5. **Budget/stop:** <=300s focused fake suite,600/2000-line limits,scope§4 none;
   zero production model/host/probe/runtime, no fourth comparison or launch
   binding. Stop at accepted bounded implementation or the exact missing
   technical/semantic fact; commit/push and return to DM/Root for the later route.
