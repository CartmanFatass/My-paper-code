# Long-window cooperative schedule value — exploratory claim contract

**Status (2026-09-27 owner re-review): WITHDRAWN; investment ended before execution.** The
original exploratory contract below is retained for provenance. It is not an accepted experiment
or a confirmation plan. The [final disposition](NOTES.md#2026-09-27--owner-requested-re-review-end-the-binary-selector-investment)
records the missing ordinary adaptive comparator, cost judgment and independent challenge.

## Hypothesis

On S7-S2/H3000, choosing at 300-step boundaries between fixed H_local@10 and anticipatory
ordinary rematching using observed 300-step native team return will improve native service over
the same option set selected using only the next 10-step return.

## Comparison and exposure

Two return predictors use the same 64-world, 640-block collection from seeds 970001–970064,
with five randomized blocks per fixed schedule per world. The only target difference is the
actual un-discounted native reward sum over 10 versus 300 subsequent steps. One initialization
per target (two started fits total), 50 passes × 10 minibatches = at most 500 updates per model;
no validation selection or refit. Evaluation is once on 32 paired fresh worlds 971001–971032,
under fixed H_local, fixed anticipatory rematching, the 10-step selector and the 300-step
selector (128 H3000 episodes / 384,000 evaluation transitions). Collection adds 64 H3000
episodes / 192,000 transitions.

## Endpoints and rule

Primary endpoints are per-episode mean native QoS satisfaction per actual step and raw native J.
The long-window exploratory rule requires the 300-step selector to exceed each of the 10-step
selector and both fixed schedules by at least 0.03 mean QoS per step, with positive mean paired
raw-J difference to each and no greater aggregate cutoff or depletion count than either fixed
schedule. Report all paired per-world differences and 95% paired t intervals; zero-service and
battery/risk tails remain visible.

## Limits

The intervals are conditional on one learned fit per horizon and do not estimate training-seed
variation. A pass is exploratory evidence about these two schedule options and these matched
worlds only. It does not establish general MARL value, mechanism causality or confirmed empirical
learning. Any confirmation needs a new predeclared 3–5 independent fit seeds per learned arm;
there is no automatic continuation, seed replacement or rescue sweep.
