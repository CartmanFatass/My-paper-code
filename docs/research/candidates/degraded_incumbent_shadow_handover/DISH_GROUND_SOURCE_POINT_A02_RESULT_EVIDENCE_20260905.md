# DISH A02 — complete native ground-source point evidence

Date: 2026-09-05 PDT. Object `DISH-GROUND-SOURCE-POINT-A02`, **A / RECON**.
Card: `DISH_GROUND_SOURCE_POINT_A02_SCIENCE_CARD_20260905.md`, including the prospective
module-entry wording at `ed2cf34b1`. This is a measurement of one original prepared point,
not a learned source contrast, altered-host result or universal radio-reception claim.

## 1. Identity, input and evidence

Exactly one accepted task `dish_ground_source_a02_seed11_a1`, PID 1653258, node
`wsl_4070`, source `dd0e01bbc4aa0efd3c22b475585511232c1de4fc`, detached cwd
`/home/wu/hmasd-worktrees/dish-ground-a02-dd0e01bb`. The exact command is preserved in
`DISH_GROUND_SOURCE_POINT_A02_CM_RETURN_20260905.md`: destination `admit-memory` and
`python -m scripts.run_dish_ground_source_point_a02 run --seed 11` joined by `&&`,
with the separate receipt and output paths below. No extra invocation occurred.

Original input is `seed_master(11), panel()[0], _reset_row`, block 0, original
TARGET_VISUAL_MASK/K8/speed 4/slot 0, owner 0, reflection 1, mask enabled, normal mode 0.
The exact coordinate is `DISH/RBHR/R06/EVALUATION_COORDINATE/0/CLAIM/TARGET_VISUAL_MASK/K8/0`.
Native and action ticks are 0; initialized is 1 and terminal is 0. One prepare call was
made; no completed native tick, checkpoint load, policy, model or optimizer was invoked.

Runtime root relative to cwd:
`temp/directions/degraded_incumbent_shadow_handover/exp/ground_source_point_a02_20260905/`.
Original files are `a1/summary.json`, `a1_admission.json` and supervisor
`/home/wu/.agent-tasks/dish_ground_source_a02_seed11_a1/task.log`.
Local originals are in that relative root in CM's
`C:/Projects/HMASD-worktrees/cm-n3-dish-funnel-a01-20260904` checkout.
CM collection is `4205dbab6`; its tracked `DISH_GROUND_SOURCE_POINT_A02_SUMMARY_20260905.json`
is exactly 4,509 bytes, SHA256 `2b63587a58d13c243e2139226ed420b681adfc9e14247d6312b04d40eb4eda07`.
DM compared the original bytes with that Git blob; they are identical. This is collection
provenance, not a new runtime guard.

## 2. Rule applied verbatim

> Complete measurements with both declared near-ground samples failing their respective
> strict-clearance conditions and both native camera flags missing give
> **A02-ENDPOINT-CLEARANCE-WITNESS**. Report each source-hop margin eligibility separately;
> an eligible noisy margin does not invalidate the obstruction witness.

> Any disagreement between the specified coordinate/boundary, derived witness and native
> camera behavior gives **A02-POINT-DISCREPANCY**; CM reproduces the relevant step on recorded
> bytes before classifying its cause. Missing required data or exceeding the cap is incomplete,
> not a scientific negative. No branch authorizes changed physics or a new learner.

The complete expected coordinate/boundary matches. Both receivers have the two specified
failing clearance samples and absent native camera flags. Independently reading the raw
numbers selects **A02-ENDPOINT-CLEARANCE-WITNESS**. Neither source hop is send-margin eligible.
There is no discrepancy branch or missing measurement to classify.

## 3. Actual signals and derived geometry

Native ground-source horizontal position is (-168, -120); its declared height is 0.
The two UAV heights are the declared 90. Horizontal positions, camera flags and margins
below are actual native outputs; sample positions, distances and terrain are derived
from those outputs and the inherited float64 equation, not exported native ray flags.

| Quantity | U0, owner | U1, standby |
| --- | ---: | ---: |
| Native UAV horizontal position | (-88, -240) | (-248, 0) |
| Native camera flag | 0 | 0 |
| Native G_TO_U margin, dB | -9.303396681040274 | -10.285571482315484 |
| Margin >= 6, send eligibility only | false | false |
| Derived source-hop distance | 170 | 170 |
| Radio j=1 / reverse-camera j=127 sample | (-167.375, -120.9375, 0.703125) | (-168.625, -119.0625, 0.703125) |
| Derived terrain height | 0.8467255467868863 | 0.7901657174358243 |
| Terrain + radio clearance 8 | 8.846725546786887 | 8.790165717435825 |
| Terrain + camera clearance 5 | 5.846725546786886 | 5.7901657174358245 |

DM independently recomputed distances, interpolation, reflected terrain and thresholds
within 1e-12; both strict `sample_z > terrain + clearance` conditions fail for each receiver.
No native call, master or policy was created by this data-only intake. No completion/arrival
tick was observed, so margin eligibility is not a statement about a received packet.

## 4. Exposure, resources and implementation deviations

Machine-generated exposure fields from the raw summary:
`models_initialized=0; policies_initialized=0; optimizers_initialized=0; training_transitions=0;
learner_updates=0; optimizer_steps=0; prepared_native_points=1; completed_native_ticks=0;
parameter_displacement=null (not applicable)`.
No A01/B01 learner exposure or source contrast was added.

Fresh actual-node receipt was assessed at `2026-09-05T09:53:33.113076Z`; physical and
effective available memory are each **12,932,448,256 bytes**, above the 4,294,967,296-byte
floor, with all pass flags true. The accepted shell command supplies the adjacent
admission-before-run ordering. No second internal receipt validator is used.

Supervisor start/end are `2026-09-05T09:53:33Z` and `09:53:34Z`, exit 0, **1 second**.
Runner wall is **0.0061659040075028315 seconds**, sampled after point/readout/Git/RSS and
before JSON serialization; it is not full process wall. Measured peak RSS is
**342,839,296 bytes**, `resources_unmeasured=false`. Complete summary publication is
observed. Prospective cost law `1.5 * (5 + 5)` was 15 seconds against a 60-second cap;
the full one-point charge and both measured durations are below the cap. No sweep exists.

The initial unlaunched draft was returned for **52/147 = 35.37%** orchestration.
The bounded prospective reduction removed real startup and duplicate admission plumbing;
final independently reviewed scope is **40/135 = 29.63%**, with 79 test lines excluded.
Scope section 4 adds none. Three focused synthetic tests passed at the exact source;
their smoke forbade the native factory and master. Tests did not observe the carded point.
The accepted result did not breach an engineering budget. The prelaunch draft breach
remains recorded in `DISH_GROUND_SOURCE_POINT_A02_IMPLEMENTATION_INTAKE_20260905.md`.

## 5. Prediction, bounded reading and unresolved questions

The DM predicted the witness branch and both actual margins below 6; all three predictions
match this point. Owner prediction is `not taken (unattended)`. The card's one-event MEI
is measurement resolution, not a return-effect threshold. The B01 five-service-tick MEI
and tuned same-information headroom remain unestimated.

Read-only source/spec mapping establishes that the native code follows its inherited
R05 host definition, incorporated by R06. Static implication, separately from this
point: with ground height 0, UAV height 90 and nonnegative terrain, the first radio
sample and last reverse-camera sample have height 90/128 = 0.703125, below even the
minimum respective 8/5 clearance. Learning a different horizontal motion does not
remove that near-endpoint camera obstruction under the unchanged definition.
Radio still includes addressed Gaussian noise; neither the static obstruction nor these
two realized margins proves mathematically impossible reception or a whole-path margin law.

This strengthens the upstream host-information explanation for A01's measured absence.
It does not prove a source-selection remedy, SHADOW/COPY equality, a general learning
failure, an implementation-versus-spec defect, physical realism or benefit from any
height/clearance change. B01 remains valid FTS-B0; A01 remains its complete retained-prefix
measurement. No family or Portfolio disposition follows from the point's branch alone.
