# VSP03 B03 independent source review

No material finding was found in the assigned source and launch boundary. This is
independent technical evidence, not approval or a scientific disposition.

Reviewed the working-tree additions against base
`6d45dee87753a0f3f0fe82cf4c2b68524f3aa45c` in the shared VSP03 checkout, under the
[CM assignment](VSP03_B03_CM_ASSIGNMENT_20260908.md) and
[card](VSP03_B03_SCIENCE_CARD_20260908.md) §§3,4,6,7. Owned only this review file;
no source edits or index operations. Applied the runtime specification General
requirements §§2–8 and engineering scope §§4–5. No object-specific runtime appendix
applies to B03. Used the scientific-tools count guidance without scientific execution.

## Direct evidence

- `experiments/candidates/vsp_03/vsp03_b03/b03.py:40–87` constructs one G outside the
  update loop, explicitly keeps `arm_index=1`, and uses that identity in train and final
  stochastic action tapes. The seed5-only runner and inherited Model give Torch40005;
  the accepted PCG64 address functions preserve split/mode/calendar indexing. No T,
  old focused fixture, checkpoint load or call to B02 run is reachable from this driver.
- B03 imports the unchanged B02 scientific helpers and B01 objective/publication
  helpers. A scoped Git diff against the base returned no B01/B02 changes. Direct
  inspection confirmed float64 world tapes, float32 observations and CPU model,
  serial40-tick event evolution, actual remaining team credit, strict positive-logit
  greedy selection, and unchanged R/R0 rules. The inherited objective retains detached
  team advantage, episode-normalized actor/entropy, valid-row critic mean, and the
  selected entropy schedule. Each of128 batches has one backward and Adam step.
- `b03.py:78–109` reuses the same immutable evaluation draws/phase for exactly two
  G modes and two rules. Per-rollout mutable arrays are newly allocated; the model is
  unchanged during evaluation. Endpoint files are read back by inherited `write_json`
  before all five contrasts are calculated. `difference` uses per-world paired
  differences, sample SD(ddof1), and SD/sqrt(1024). Primary is explicitly G_greedy−R0;
  the summary identifies one independent training instance.
- `b03.py:90–128` saves and reads final weights without constructing another model,
  retains initial/first/final parameter exposure and128 curve rows, and reads back
  primary, activity, optimizer/model counts and arm records. Endpoint job quantities,
  phase and opportunity counts come from the inspected inherited rollout. No replay
  or recurrent-state compatibility is implicated.
- Independent arithmetic over the literal loop dimensions produced16384 training
  episodes,4096 evaluation episodes,20480 total joint episodes,819200 team ticks,
  1638400 target transitions, and at most2210 rollout model batch calls. Parameter
  arithmetic gives1570 actor/direct and513 critic parameters,2083 total. These match
  the machine-count record; they are prospective counts, not observed execution.
- The [launch boundary](VSP03_B03_LAUNCH_BOUNDARY_20260908.md) places the timestamp
  helper, adjacent destination admission, runner imports, construction, learning,
  evaluation, publication/readback and exit inside one `timeout --signal=KILL 120s`.
  Admission uses `&&`; inspected preflight returns nonzero for a failed/missing memory
  measurement. The runner sets BLAS/OpenMP environment limits before Torch imports;
  B03 sets Torch intra/inter-op limits to1 before construction. There is one scientific
  process and ordinary independent-world batching, with no native team, worker pool,
  nested compute team, retry or fallback added. The configured node is wsl_4070.

## Scope and validation limits

Prohibited §4 additions without a card line: **none found**. Required scientific
counts/exposure and simple file readback serve card §4; no schema validator or new
execution machinery was introduced. Source count:128 driver lines plus28 runner
lines, below2000 new source/600 runner limits; mirrored tests52 lines. The substantial
publication/orchestration portion has a concrete card purpose and adds no identified
budget or semantic breach. No separate orchestration-ratio gate was imposed.

Inspected the static/literal tests and consumed CM's recorded3-pass/1.79s result after
the documented temporary-directory setup repair. CM also reports remote `bash -n`
exit0 for the launch body. Neither was repeated. This review used file inspection,
Git comparison and plain arithmetic only: zero models, worlds, RNG draws, rollouts,
optimizer steps, fixtures or profiling calls.

Residual uncertainty is the sole run's actual completion, realized counts/outputs and
runtime resource behavior. Internal elapsed and G-arm wall are narrower than complete
process wall; outer wall/exit evidence must accompany output intake. Aggregate CPU
remains unmeasured, as disclosed, and no speedup or CPU-compliance claim is established.
The summary's complete label alone cannot supersede a timeout/nonzero exit or failed
final readback. Static connections and literal helper checks do not establish scientific
value. No repair is requested from this inspection; CM retains normal-run collection
and technical acceptance, with scientific interpretation belonging to DM.
