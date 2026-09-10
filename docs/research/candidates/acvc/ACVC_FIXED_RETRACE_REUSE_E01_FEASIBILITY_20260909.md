# Fixed retrace reuse: preparation-only engineering feasibility

Both named retained DENSE checkpoints are available and byte-identical to their accepted
collection records. A small fixed-evaluation adaptation is feasible by source inspection;
the current runner is **not ready unchanged** for C/F/dwell. No model construction/load,
tensor inspection, native import/run, test, profile, fit or reevaluation occurred here.
Only file reads/digests and arithmetic over retained records were executed. No source changed.

Starting checkout: `C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`, clean at
`57484569fafc34e7a6981093fac325d64321e6e7`. Contract is Root's owner-synthesis preparation
assignment via DM. Read the [owner synthesis](../../portfolio/pro_packets/20260909_third_party_planning_comparison/RESEARCH_PLAN_SYNTHESIS_CODEX_20260909.md)
§§3.6, 4 ACVC row, 5.3 ACVC and 6. The old selector package remains stopped. This document
chooses neither evidence class nor scientific authority and allocates no evaluation.

## Checkpoint availability

Both files are **282893 bytes**. Their common parent is
`C:/Projects/HMASD/temp/directions/metric_ground_transport_allocation/exp/`:

| Retained base | Relative file | Actual SHA256, equal to accepted record |
|---|---|---|
| DENSE8201 | `mgtap_b01_8201_4f65eefb1b15e44b42d694376630fba0c230cc6c/final_DENSE.pt` | `f648f2b100d07335ccd9c79c0476b8e9dba0c1644ae837d622b0c5f711030790` |
| DENSE8202 | `mgtap_b01_8202_4f65eefb1b15e44b42d694376630fba0c230cc6c/final_DENSE.pt` | `cf883f4591c4bc72b2178004cf0ff6c78126080be81e0cbc900f62acf0e40c15` |

Accepted record sources:
[8201 technical collection](../metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_8201_TECHNICAL_COLLECTION.json),
[8202 technical collection](../metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_8202_TECHNICAL_COLLECTION.json).
Their historical DENSE checks report identity/FP32/finite true. Those historical checks
are not new model-load validation; this preparation confirms availability and byte identity
only. No fallback archive was needed or searched. Exact absolute paths and computed facts
are in [feasibility facts](ACVC_FIXED_RETRACE_REUSE_E01_FEASIBILITY_FACTS_20260909.json).

These are two **old** base fits. Prior ACVC B01/B02 both used DENSE8201, selected with both
old DENSE outcomes known; adding8202 does not retroactively remove that selection or create
two new independent training pairs. No retained ACVC learned gate is needed.

## Minimal prospective implementation map

Source inspection at the starting revision, without importing any module:

1. `experiments/candidates/acvc/native_link_loss_b01/learner.py:collect` already executes
   C/F with `gate=None`, `critic=None`, `phase="eval"`. It creates neither a gate/critic
   nor an optimizer and never calls `update`; it samples the recurrent frozen base each
   primitive step and feeds `last=sent.copy()` back into that arm's next input. Base hidden,
   command history and binding reset each episode. Imported class/helper definitions are
   not constructions or learner invocations. The unused gate RNG for fixed arms is harmless
   but need not be retained in a purpose-specific fixed collector.
2. Dwell is **not currently supported**. `model.py:action_generators` accepts only T/G/C/F;
   simply passing a new arm raises at its tuple lookup. `collect` assigns the opportunity
   choice only for F and always names interventions `retrace`. Minimal future change:
   add the frozen dwell stream identity, use the exact `Binding.observe(obs,b)` mask for
   F and dwell, send its returned realized-retrace command for F and zero xyz for dwell,
   otherwise send b. Preserve b sampling even when overridden. Report dwell separately
   from retrace and compare distinguishability against the command actually substituted.
3. Reuse `binding.py:Binding.observe` unchanged: private FP32 observation bytes converted
   to float64 for coordinate matching, one-transition anchor, positive-SINR nonpadding,
   ambiguity exclusions, current visible count1–19, and positive away-dot with the current
   sampled proposal. Dwell's predicate is the same function **on its own trajectory**;
   opportunities need not occur at the same times as F. Never borrow F's mask or history.
4. Reuse `model.py:load_base`/`base_architecture` for the same read-only `NativeGeometryActor`
   actor state, frozen parameters and private constructor stream. In future execution this
   constructs the base actor, not a gate/critic; `torch.load` deserializes the old checkpoint
   container including unused critic tensor bytes, without constructing a critic network.
5. `scripts/run_acvc_native_link_loss_b01.py:run` currently hardcodes T/G/C/F, learned fits,
   B01/B02 identity and learned-arm billing. Do not invoke it with zero train episodes as
   a substitute. A short fixed-only runner should iterate two explicit checkpoint inputs ×
   C/F/dwell ×64 worlds, calling the accepted collector with no gate/critic. Six sequential
   panel initializations (one base load and environment constructor per panel) are a simple
   costed topology. No new learner checkpoints, optimizer, gate or training loop is needed.
6. `report.py:panel` hardcodes learned contrasts and must not be reused unchanged. The future
   small reducer must retain all384 S/J rows with base/arm/world identity and calculate the
   later card's explicit fixed contrasts per base. Reuse `write_json` and the basic paired
   arithmetic where meanings match; do not silently carry over a T-based min-of-means rule.

All future changes remain proposed. DM must freeze the fresh reset/action/constructor seed
law, matching across arms/bases, primary contrasts/rule and output identity. Observation,
native S/J reward, horizon256, CPU FP32/Torch1 intra/inter-op and native geometry stay as
assigned. No privileged identity/service inputs, changed predicate, base reuse across mutable
trajectories, training or scientific selection follows from this engineering map.

## Complete cost projection

Retained [P78](native_link_loss_b01_p78_20260909/task.log) and
[P79](native_link_loss_b02_p79_20260909/task.log) completion timestamps yield the following
differences. These are evaluator **panel windows**, including each panel's base load and
environment constructor, not isolated `env.step` microbenchmarks:

| Existing complete32-episode window | P78 seconds | P79 seconds |
|---|---:|---:|
| C: completion(C) − completion(G) | 5.263435943 | 5.201145001 |
| F: completion(F) − completion(C) | 6.231096152 | 6.420700665 |
| Other shared scientific-process overhead after removing C/F and checks | 16.194091239 | 18.752391501 |

The last row is computed from accepted `collection_acceptance.json:shared_bill_s` minus
current checks and those C/F windows. It conservatively retains old import/startup and
outer publication/exit work; component attribution is not separately timed. Original full
ACVC runs included two learned fits and are not multiplied wholesale as evaluator costs.

Proposed one serial invocation: **2×3×64=384 episodes; 98304 team steps; 491520 base-agent
forwards; 384 scored resets plus6 unscored constructor resets; zero new fits/Adam/gates/critics**.
F/dwell bookkeeping upper bound is2 bases×2 rules×64×256×5×20×2 = **13107200 coordinate
pairs** for preceding-anchor matching plus new-anchor ambiguity checking. No trajectory
search, panel selection, replay/backward or training is included.

Use the larger observed C/F panel costs and F as dwell's **unmeasured proxy**:

- C64 per base: `2×5.263435943 = 10.526871886 s`.
- F64 per base: `2×6.420700665 = 12.841401330 s`; dwell64 uses the same proxy.
- Six panels: `2×(10.526871886 + 12.841401330 + 12.841401330) = 72.419349092 s`.
- Add18.752391501 s retained shared process overhead: **91.171740593 s** process projection.
- Recommend a **30 s current focused-check allowance**, explicitly separate from science:
  nominal complete projection **121.171740593 s**; recommend **180 s complete invocation
  cap**, including those checks, all imports/loads/constructors, all384 evaluations,
  publication and actual exit. This leaves58.828259407 s planning headroom, not a measured
  guarantee or a universal overhead factor. A larger chosen check budget changes this bill.

Scaling whole32-episode windows by2 conservatively charges their fixed load/constructor cost
twice per64 panel; the proposed actual topology has six loads/constructors, not twelve.
Dwell trajectories,8202 evaluation throughput, new publication/check work, startup/exit and
node contention remain unmeasured. File availability cannot resolve those unknowns. There
is no measured cost gap above the proposed cap and no reason from these timings to add a
pilot. The future run must measure complete wall through exit and preserve any partial
outputs if its selected cap is reached; this preparation allocates no retry or fallback.

With one scientific process and sequential panels, summed process wall and its execution
critical path coincide; the complete logical bill additionally charges focused checks.
Human editing, staging and waits are separate. Aggregate CPU and scratch high-water are
unknown, not zero. Use the configured remote node, unchanged thread/device settings,
fresh actual-node admission and existing detached supervisor only once a card and execution
allocation exist. No scope§4 machinery is needed; future source remains within normal
2000-line attempt/600-line runner limits.

## Applied knowledge and remaining gap

Read evidence-spec §§4,5.1–5.3,11.4,11.8–11.10 and scope§§4–5; applied scientific-tools
scientific-reading with foundations§§1–2,6, RL topic “任务和策略/数据与更新” and empirical
topic “先分清在比较什么/随机性有层级”. The concrete consequence is to preserve dynamic
private recurrence and stochastic proposal sampling despite frozen parameters; deterministic
F/dwell rules do not make the complete controller deterministic or untrained. Evaluation
worlds are conditional execution units per retained base, not new training replications.
Pairing requires the later frozen reset/stream design, not merely equal episode labels.

DM relayed Root's concrete class-wording conflict during this preparation: A cannot carry
the proposed execution-rule effect, while current §5.2/§11.4 require nonzero learner updates
for B. Zero new fits is preserved. Root assigned DM a same-node Convergence question for
a narrowly scoped exception/interpretation under owner §4.7. This technical feasibility
does not resolve that conflict, change a rule, add token training or promote the object to C.

No availability gap remains. Future code, focused changed-path acceptance, model loading
and complete native execution are **not performed or validated here**. DM owns class,
scientific/card choices and authority reconciliation; execution awaits its actual allocation.
The old P78 cleanup blocker is untouched. Only these feasibility documents are published.
