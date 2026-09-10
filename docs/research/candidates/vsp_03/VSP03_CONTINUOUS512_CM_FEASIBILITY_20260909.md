# VSP03 continuous512 â€” source-aware CM feasibility, 2026-09-09

**Technically feasible as a small new driver change; 60 s per complete fit is a
credible planning cap from retained evidence, not a measured upper or a launch
acceptance.** The proposed totals **8,847,360 team ticks and 1,536 Adam steps are
correct** for three fresh continuous512 fits and two full four-mode evaluation
panels per fit. The shared model/environment/objective need no redesign. This
read-only assessment selects no fit keys, implements nothing and launches nothing.
DM must resolve the stopped-family scope through Convergence before implementation.
The DM clarification recorded below resolves the proposed key/tape/entropy choices.

## Contract, source and reading boundary

Assignment: Root's OWNER_DIRECT synthesis preparation through the existing DM.
Read [fixed synthesis](https://github.com/CartmanFatass/My-paper-code/blob/dae6a74bbf8e402a3ea47256176f5795eb277206/docs/research/portfolio/pro_packets/20260909_third_party_planning_comparison/RESEARCH_PLAN_SYNTHESIS_CODEX_20260909.md)
Â§5.3 VSP03 and Â§6, read from C:/Projects/HMASD and linked at the fixed revision
dae6a74bbf8e402a3ea47256176f5795eb277206. No main synchronization is planned;
DM pins newer method sources separately and uses its current renderer/config read-only. Source checkout is
C:/Projects/HMASD-worktrees/dm-vsp03-p07-prep-20260907, branch
codex/pro-vsp03-shared-service-convergence-20260906, clean on entry at
47f8983ed0a241106cdbe8368cb37851f50c7ebd. No synchronization or index operation.

Inspected scripts/run_vsp03_b05.py; vsp03_b03/b03.py run; vsp03_b02/b02.py Model,
worlds, action_tapes, rollout, rule_actions and difference; and the actual
vsp03_b04 launch.sh/control.py/deadline.py chain. The one necessary dependency
expansion was vsp03_b01/b01.py objective, because the inherited entropy schedule
is defined there. Reused [P76 card Â§Â§2â€“6](VSP03_B05_P76_SCIENCE_CARD_20260909.md),
[P76 intake Â§Â§3â€“5](VSP03_B05_P76_INTAKE_20260909.md), and the retained P67/P76 complete
timing/CPU evidence. Current main AGENTS and scientific-tools scientific-reading
mode were read; no method-source edits. Relevant explanatory reading was
FOUNDATIONS Â§6 and topic-notes/04_EMPIRICAL (checkpoint versus training unit,
conditional evaluation variation and selection), with evidence-spec Â§Â§11.8.1â€“7.
Those concepts inform the inference limits below; they create no extra experiments,
seed quota, causal prerequisite or approval layer. No external retrieval was needed.

## Exact workload from current loop shapes

The current driver trains128 batches of128 full joint episodes and evaluates four
1024-world endpoints once. A continuous512 fit trains512 such batches and evaluates
four endpoints after both update128 and update512. Both targets advance all40
primitive transitions in every episode, even after submission. Evaluation R0/R
panels are counted twice as requested, although their deterministic same-world
outputs would be identical; this proposal does not silently cache/delete an arm.

| Quantity | Per new fit | Three fits |
| --- | ---: | ---: |
| Training joint episodes:512Ã—128 | 65,536 | 196,608 |
| Training team ticks:episodesÃ—40 | 2,621,440 | 7,864,320 |
| Evaluation joint episodes:2Ã—4Ã—1024 | 8,192 | 24,576 |
| Evaluation team ticks:episodesÃ—40 | 327,680 | 983,040 |
| Total joint episodes | 73,728 | 221,184 |
| Total team ticks | 2,949,120 | 8,847,360 |
| Total target transitions:2Ã—ticks | 5,898,240 | 17,694,720 |
| Backward calls / Adam steps | 512 /512 | 1,536 /1,536 |
| Fresh G constructions | 1 | 3 |
| Rollout-policy batch-forward upper:17Ã—(512+2Ã—2) | 8,772 | 26,316 |

The forward bound excludes objective/critic/backward computations and rule-only
panels. Decision/gradient row counts remain data dependent. Each fit has512 curve
rows, two fixed panel records and one selected512 primary. No model/world/RNG was
constructed to derive these numbers: Python standard-library integer arithmetic
only. There is no15-fit grid, independent128 fit,2048 budget or extra evaluation.

## Cost projection and proposed caps

Retained P67 complete invocation wall is3.253184s, aggregate unit CPU3.278770s;
P76 complete wall4.191728s, CPU3.500596s. Both include admission/imports, initialization,
128 updates, one full evaluation panel, output/readback and task termination on
wsl_4070 CPU FP32/one compute thread. Their process peak RSS was about493/491MB;
this does not measure a512-fit peak or fresh resource availability.

Logical per-fit cost is startup/admission/import + one initialization +
512 C(128,40,2) +2Ã—4 E(1024,40,2) + both panels' checking/publication + final exit/
descendant termination. Learning scales4Ã—; evaluations scale2Ã—; fixed startup
should not scale4Ã—. Total tick ratio is3.6Ã—. Tick scaling is only a rough reference
because a gradient batch and rule-only evaluation tick do not cost the same.

| Extrapolation using retained complete paths | P67 basis | P76 basis |
| --- | ---: | ---: |
| Tick-scaled per-fit wall (3.6Ã—) | 11.711462s | 15.090221s |
| Fourfold whole-path per-fit wall | 13.012736s | 16.766912s |
| Three fits, summed fourfold wall | 39.038208s | 50.300736s |
| Fourfold per-fit aggregate CPU | 13.115080s | 14.002384s |
| Three fits, summed fourfold CPU | 39.345240s | 42.007152s |

Fourfold whole-path scaling is a deliberately generous *projection relative to
linear component scaling*, not a statistical upper or measured bound: policy-dependent
rows, longer-training numerics, filesystem costs and host contention can differ.
With the existing10s shutdown/publication reserve, a60s fit offers50s for work;
that is about2.98Ã— the larger16.766912s projection. Therefore known work/timings
support the proposed60s fit cap as plausible without a new pilot. They do not
prove all three fits finish under it or produce finite useful measurements.

Three60s per-fit caps imply at most180s **summed complete invocation wall**.
If sequential, study elapsed additionally includes inter-invocation staging/admission
setup gaps outside each already defined fit boundary and collection/control-plane
latency. If concurrent, elapsed is neither the sum nor guaranteed60s because of
scheduling and resource contention. Thus reject interpreting180s as a measured or
enforced end-to-end three-fit study elapsed bound. Freeze180s as summed invocation
budget unless DM explicitly means a separate complete-study deadline; that alternate
meaning would require a different bound/stop contract, not silently added machinery.
No parallel scheduler, global deadline service or profiling requirement is warranted.

## Minimum implementation boundaries and correctness risks

1. **Continuous training driver.** Current b03.run fixes range(1,129), saves final
   exposure at128, evaluates only after training and labels a single primary. A new
   thin object driver should keep one Model and one Adam instance alive for updates
   1â€¦512 and insert fixed panels after completed optimizer steps128 and512. No call
   to the old run twice, reseed, optimizer reset, checkpoint-resume or restart at128.
   Preserve shared b01 objective and b02 model/environment functions and old runners.
   Training episode offsets continue `(update-1)*128`:0â€¦65535, with no reused prefix
   after128. Model initialization remains40000+the new fit key; G arm remains1.

2. **Original entropy schedule is already fully specified by source.** Objective
   uses `0.01*max(0,(64-update)/63)`:0.01 at update1, zero at64 and every later update.
   Preserve the global update index through512. Restarting the schedule at129 or
   stretching its decay to512 changes the requested algorithm; it is not an ordinary
   implementation choice. Adam lr0.001/betas(0.9,0.999)/eps1e-8/weight_decay0,
   unchanged actor/critic loss,14 features and2083 parameters remain intact.

3. **Evaluation state and RNG isolation.** Existing worlds/action_tapes instantiate
   addressed local PCG64 generators; rollout allocates fresh environment arrays,
   reads draws/phase without mutating them and computes model actions under no_grad.
   Current MLP has no dropout, batch normalization or recurrent/buffer state.
   Evaluating the same live model without constructing another Model does not consume
   Torch randomness or update parameters/Adam; retain that property, do not call the
   objective/backward/step on evaluation data. The next training batch remains fresh
   with its own address. Keep evaluation accounting separate from learning counts,
   though whole-task exposure includes both. Avoid retaining training graphs/batches
   across all512 updates; streaming curve writes and small panel rows suffice.

4. **Same held-out panel across checkpoints.** Reuse within each fit the same
   `worlds(fit_key,200,0,1024)` draws/phase at128 and512, training split100. Three
   distinct fresh fit keys must separate initialization, training and held-out
   streams from old fits and each other. DM has proposed10801/10802/10803, mapping to Torch50801/50802/50803.
   DM reports no use in its bounded direction-card/request/source search; CM does not
   claim an independent exhaustive collision search. Existing action address `[303,key,split,mode,arm,episode]` supports a private
   evaluation namespace without global RNG state. DM has selected the same evaluation action tapes at both checkpoints:
   `[303,key,200,1,1,episode]`, common randomness private to evaluation and disjoint
   from training. This is source-compatible and fixes the within-fit covariance
   design prospectively; do not substitute checkpoint-specific keys during implementation. Greedy strictlogit>0 and R0/R consume no action tapes.

5. **Publication, partial failure and primary identity.** Existing filenames and
   summary fields hold only one endpoint panel; writing twice would overwrite128.
   Use explicitly checkpoint-keyed panel/contrast records and primary512, with512
   curve rows and initial/first/final displacement. For the selected128 weight bytes,
   serialize detached tensors immediately at the actual128 panel boundary: a saved
   Python state_dict of live tensor references can later reflect512 weights. Do not reload/reconstruct a model
   merely to evaluate128. DM-selected coverage is exactly128/512 snapshots; no universal all-intermediate checkpoint obligation follows. A failure
   after128 retains that panel and actual counts but has missing primary512, not a
   completed128 replacement result. Preserve every fit's failures and no best-panel
   selection; the DM failure policy below controls subsequent predeclared fits.

6. **Entrypoint and task deadline.** New fit keys/object/output/handle need thin
   bindings; canonical admission and its dependency must remain in staged source.
   Existing launch.sh/control.py/deadline.py already accept cap60 and reserve10:
   manager kill59s, work50s, cleanup58s, all derived from one pre-start origin.
   No shared adapter algorithm change is needed. The scientific driver's hardcoded
   `started+120` must instead use the same declared60s bound so rollout and final
   publication checks agree with outer containment. Per-fit process isolation also
   preserves Torch's one-time interop-thread setup; looping old runners three times
   in one interpreter risks set_num_interop_threads failure and mis-bound clocks.
   Prefer three ordinary exact detached invocations, each with adjacent fresh admission
   and unique short paths; long private TMUX_TMPDIR socket paths have a finite Linux
   address limit. Reuse existing receipt/termination chain and legacy adapter-tag
   mapping explicitly or select a minimal identity update; no registry/worker pool.

## Interpretation and exact unresolved choices

Three fits are three training units; two checkpoints and eight endpoint panels per
fit do not create six or24 independent training samples. Within-fit128â†’512 change
can use the declared common world panel, but includes finite evaluation variation;
private/common action tape choices affect its covariance. Same fixed R0/R panel
scores should match between checkpoints by deterministic construction, not by
fitting a new comparator. Preserve .02 MEI and all modes/rules. Existing stochastic
losses and mixed small greedy outcomes do not diagnose convergence, and longer
training alone does not establish stable superiority, a unique coordination cause
or necessity of the architecture. This follows the read explanatory material and
P76 intake, not a new scientific selection by CM.

No concrete source or measured-cost obstacle currently rules out this bounded
candidate. DM subsequently fixed fresh keys10801/10802/10803, common eval200 worlds/phase
and action tapes at128/512, continuous model/Adam state, original entropy zero
after64, and the three final512 primary scores with descriptive mean/SD. These
choices are compatible with the inspected source and resolve those scientific
ambiguities. DM has now also resolved the remaining candidate details:

- Save exactly the two selected128/512 weight snapshots, serializing detached
  tensors immediately at their actual panel boundaries. Retain512 curve rows and
  checkpoint-keyed panels. No additional model reconstruction, optimizer-resume
  checkpoint or all-intermediate weight archive. This is compatible with the
  existing tensor serialization path; avoid holding live state_dict references
  until after further training.
- The180s proposal is summed complete fit invocation wall, not a study-elapsed
  deadline. Each fit has60s complete cap, work50s, cleanup58s and hard kill59s.
  Existing adapter arguments support these values without a new study supervisor.
- Plan at most one accepted invocation for each of the three predeclared fits,
  without sign-based stopping. No failed-fit replacement, retry, resume or extra
  fit. A concrete shared defect threatening reward, information, training or
  primary pauses dependent launches for repair/allocation reconciliation, retaining
  valid partials. A local process/admission failure supplies no zero endpoint and
  does not impose a requirement to obtain three successes. Separate existing
  per-fit handles/receipts support this policy without new machinery.

No unresolved candidate choice remains among the questions raised in this note.
These are documented DM proposal choices and source-compatibility findings, not
execution allocation; stopped-family scope still returns through Convergence.
The projected runtime is not an empirical upper. After Convergence scope resolution,
implementation acceptance should focus on continuous optimizer/update/RNG state,
nonmutating128 evaluation, checkpoint-specific output and the matching60s clock;
existing environment/scientific/lifecycle evidence remains reusable. No checks are
executed or allocated by this feasibility note.

Work performed here: read-only local source/docs plus pure known-configuration
arithmetic. Zero scientific/test/profiling invocation, model/world/RNG construction,
source edit, staging, remote call, empirical timing or index operation. Only this
uncommitted document is delivered to DM for its single publication.
