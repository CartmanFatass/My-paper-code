# DISH forecast package B02 â€” complete technical result evidence

Object DISH-FORECAST-PACKAGE-B02, B/EXPLORE, one original paired seed61.
Both original arms completed at exact committed/pushed source
`47f81c15c536c2b4c4ee463eaa7a35f720ec08c7`, detached wsl_4070 worktree
`/home/wu/hmasd-worktrees/n3-b02-20260905`. Frozen commands and acceptance records
are in `b02_20260905/`; CM contract/independent source review is in
`DISH_FORECAST_PACKAGE_B02_CM_RECORD_20260905.md`. No source or scientific
configuration changed after either result, and no formal invocation was repeated.

## Frozen measurement and observed readout

Card section4: "The primary difference is `Delta_package = mean_r(J[FORECAST_PACKAGE,r]-J[CONTROL,r])`
over all four paired rows, with no trigger-support filter. Publish both arm means and all
four paired differences."

Card section5: "An inside-margin or mixed result does not establish substantial gain at this exposure.
Keep every row; do not claim equivalence or automatically extend training."

The actual primary is0 mean service ticks, CONTROL470 and FORECAST_PACKAGE470,
against MEI+24. All four paired differences are0; no row was filtered. This is the
complete finite observed comparison, not an exact-bit performance requirement or
an equivalence/stable-superiority claim. No native legal transfer occurred; all
recorded service is before transfer. Component and source contrasts remain
unestimated. DM owns scientific interpretation and the next decision.

| Development condition, speed4/slot0/block0 | CONTROL service | Package service | Difference | Energy each arm |
| --- | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 |572|572|0|169692.20416642696|
| TARGET_VISUAL_MASK / K4_TO_K12 |447|447|0|162885.33075914986|
| TERRAIN_RELAY_MASK / K8 |433|433|0|164828.901961202|
| TERRAIN_RELAY_MASK / K4_TO_K12 |428|428|0|161669.57931834974|

All eight ordinary episodes step1200 ticks and terminate at the fixed horizon,
with zero unstepped remainder. Each arm/row has zero invalid_commit, token_gap,
dual_owner, dual_payload, buffer_clear, command_slew_breach and separation_breach.
Raw summaries preserve batteries, separation, owner/actuator owner, actual terminal
causes, temporal service partitions and complete row configuration. Equal selected
outcomes do not assert every unrecorded internal trajectory byte is identical.

## Actual learning and exposure

Both use the ground-terminal A03 instance for resets, ordinary steps and unchanged
passive labels; STRUCTURED/block0 role, master
`ef9ec35ce27cf52e4c1d82292b22cfbe4926183ec1f29b19657280f6234814b1`, FP32 training,
float64 native storage and configured single-thread CPU. Package is the card's
joint Gaussian NLL coefficient0.025 plus FP32 sigmoid native service interface;
raw-logit BCE remains. Control is inherited mean-MSE/raw service. Initial model
norm38.24157533891136 is common; each arm has separate evolving state.

| Observed quantity | CONTROL | FORECAST_PACKAGE |
| --- | ---: | ---: |
| Ordinary training transitions |65536|65536|
| Complete updates / optimizer steps |16 /512|16 /512|
| Next-label calls / next-mask count |65536 /65504|65536 /65504|
| Service-label eligible E |8641|8649|
| Delay calls2E |17282|17298|
| H actual consequence calls |unmeasured|unmeasured|
| H upper20E |172820|172980|
| Total native training call lower/upper |148354 /321174|148370 /321350|
| Ordinary evaluation ticks |4800|4800|
| Training service sum |36615|36607|
| Training energy sum |8968683.269300953|8968698.629300952|
| Training terminal count |32|32|
| Final model norm |39.30807845434155|39.149200792042365|
| Absolute L1 parameter displacement |2923.5314606231263|2729.5323303272066|
| L2 displacement |9.020952382577892|8.515494924525886|
| Relative L2 displacement |0.23589384858313983|0.22267636333122617|

All sixteen ordered per-update curves in each raw summary have32 actual optimizer
steps and finite loss/gradient flags. Their service and mask sums reconcile.
Package per-update mean loss spans10.566485837101936 to7423381.7265625 and mean
pre-clipping gradient norm16.111391201615334 to22054892.236206055; these large
finite observations remain in the original curves, without reclassification or repair.
Both training streams record zero legal transfers and zero seven-category hard
events. H is null, with complete native clone computation retained and the upper
shown as an upper, per DM optional-observability clarification. There is one paired
training replicate, not four independent seeds or two independent arm replicates.
Final checkpoint16 only was used; final checkpoint digests differ, as do actual
learning measurements. No historical checkpoint or earlier/best selection entered.

## Exact process, cost and resource evidence

| Scope | Whole command wall s | CPU user+system s | Peak RSS KiB | Charged wall s |
| --- | ---: | ---: | ---: | ---: |
| Shared focused profile + admission |6.83|6.25+0.46|581340|count once|
| CONTROL admission + complete runner |337.23|289.24+63.55|612084|340.645|
| Package admission + complete runner |298.60|261.09+49.02|609420|302.015|
| Pair including shared preparation |642.66|669.61|not summed|642.66|

Each charged arm is below1800s; pair is below3600s. Exact own caps were1796.585s
with3.415s shared charge in each frozen argv. External `/usr/bin/time` includes
adjacent actual-node admission and complete subprocess/publication. Runner stdout
records narrower completed walls336.65946624400385 and298.0301556159975s;
its prepublication CPU/RSS samples are retained without calling them full-command
CPU. Summary and stdout agree on every shared field; stdout adds only completed
and charged runner-wall fields. Full-command values above govern complete billing.
Scratch and exact H remain unmeasured; separate self/child RSS maxima are not added.

Fresh physical/effective available memory was15305568256bytes for focused checking,
15308656640 for CONTROL and15370407936 for package, each passing4GiB immediately
before its invocation. Original tasks `n3_b02_focused_20260905` (PID1706554),
`n3_b02_control_20260905` (PID1707289), `n3_b02_forecast_package_20260905`
(PID1819511) all exited0; tracker witnessed inactive tmux. Supervisor rounded
7/337/299s durations are not experimental billing. No live process remains here.

The single five-test conformance profile passed in6.00s and covered real NLL/mask
backward, genuine raw-BCE optimizer update, FP32 service link, ground ordinary/passive
binding, policy reload, default snapshot restoration, native terminal/paired
publication and nonfinite partial JSON. It was nonformal and charged once; no extra
smoke/pilot/verification model run occurred. Independent reviewer accepted source
and focused evidence, then read original raw arms without re-executing them. Final independent raw-pair
review found both arms and published pair technically conformant, no material defect;
it independently reconciled all counts, masks, configuration, curves, paired rows,
resources and642.66s/669.61CPU-seconds. No numerical model was loaded for review.

## Engineering scope, batching and limits

Source A447/D20 (test172 separate), runner113, within2000/600. Conservative
orchestration ceiling245/467=52.46% includes computational hooks; necessity/consumers
are recorded in the CM record. Scope section4:none. No new native law, retry,
worker pool, schema service, compatibility framework or extra calibration. The
new per-instance library hook preserves legacy defaults. Source acceptance does
not make a new universal production route or establish scientific benefit.

Existing policy batches32 lanes and four recurrent copies; native ordinary/passive
batch entry points execute C++ lane loops, with existing recurrent replay/minibatches.
This is batching, not a claim of new parallel speedup. OMP/MKL/OpenBLAS and Torch
threads were configured1. Actual whole time is now measured for this pair; neither
24N nor historical B01 scaling/core count supplied a matched pre-run projection.
No throughput comparison or performance attribution follows from the arm wall difference.

Compact raw evidence lives in `b02_20260905/`; final checkpoint files are retained
in the remote arm roots and local `temp/b02_transport/` with recorded SHA256 files.
The local transport collector only copied existing files and computed byte digests;
it did not load models, run helpers or reinterpret numerical outputs. Raw negative
or null findings remain intact. This closes CM technical collection for this pair;
no successor, automatic extension or source repair is selected.
