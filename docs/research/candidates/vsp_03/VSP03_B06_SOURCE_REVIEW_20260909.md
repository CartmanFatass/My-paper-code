# VSP03 B06 independent semantic source review

**No material finding found** in the assigned new B06 driver, package initializer
and thin runner, inspected as working-tree additions over
`8a9280c6d0b86b850150e09c2e19460fb15c1ccc`. Contract:
[science card §§2–4,6–7](VSP03_B06_CONTINUOUS512_SCIENCE_CARD_20260909.md) and
[CM proposal/assignment](VSP03_B06_CONTINUOUS512_CM_PROPOSAL_20260909.md).
Owned only this review; no source/index edits or scientific/runtime execution.
The exact launcher was subsequently inspected in the bounded follow-up below.
Actual exact-SHA remote staging remains CM's execution responsibility.

## Continuity and scientific identity

`b06.py:54–75` constructs Model and Adam once, outside `range(1,513)`. Each update
gets fresh addressed training data starting at `(update-1)*128`, one backward and
one optimizer step. The same live model/optimizer then continue at129 after the
128 panel; no reinitialization, load, optimizer reset or second learner appears.
The unchanged B01 objective receives the global update number and retains
`0.01*max(0,(64-update)/63)`, hence zero from64 onward, without a restart or stretch.
The first/128/512 exposure records share the same detached initial parameter vector.

The runner permits only10801/10802/10803 and requires an explicit seed. The seed
reaches the inherited B02 Model/worlds/action_tapes helpers, giving Torch50801/50802/
50803, split100 training episodes0…65535, split200 evaluation worlds0…1023 and
G arm1 throughout. No old state loads. Scientific summary object is VSP03_B06,
with one independent_training_instance per invocation. The inherited adapter's
B04 command variable remains connected. A scoped comparison against32ce8a735 shows
no changes to B01/B02/B03 scientific code or the accepted adapter files.

## Evaluation isolation and publication

`b06.py:50–51` generates the evaluation worlds/phase and stochastic tape once per
fit, outside the learner loop. Both128/512 panels reuse those exact arrays. Each
rollout allocates its own mutable environment state; direct inspection of the
unchanged rollout confirms the shared draws/phase/uniforms are only read.
Evaluation is under no_grad and calls no optimizer/objective. The inherited MLP
has no dropout, batchnorm or recurrent state; inference introduces neither RNG
draws nor mutable model buffers. Addressed local PCG64 generators separate learning
and evaluation. Residual training gradients are not modified by evaluation and are
cleared by the next update's existing zero_grad before backward.

`b06.py:94–128` evaluates greedy G, stochastic G, R0 and R at each selected boundary,
including both rule panels. All native rows, five paired contrasts and absolute
metrics are keyed by update in filenames and summary.checkpoints. The strict greedy
tie rule and native credit/outcome accounting remain the inspected B02 behavior.
Snapshot state is detached and cloned, immediately serialized and read back at the
actual128/512 boundary before any later update. No live state_dict survives as an
unsaved128 snapshot, and no extra model or optimizer checkpoint is constructed.

The128 checkpoint JSON and endpoint/weight files are written before continuation,
so later failure cannot overwrite that panel. Ordinary exceptions retain summary
error and actual counts; hard termination can leave only earlier flushed artifacts,
which must be reported at their available scope. No128 substitution for a missing512
primary exists. Complete-run publication preserves512 curve rows, actual training/
gradient/rollout counts, exposure and selected snapshots/readback.

## Primary, paired change and counts

`b06.py:130–133` fixes primary to checkpoint512's G_greedy−R0. The helper at17–23
forms each world's `b = late[G_greedy-R0] - early[G_greedy-R0]`, then reports its
mean, sample SD(ddof1) and SD/sqrt(n). Both complete lists are constructed in the same
world order with1024 entries, so this implements paired Q and SE=SD/32, rather than
adding independent-panel variances. Output preserves each world's b and phase.
There is no best-checkpoint selection or across-fit aggregation inside this per-fit
driver; the card's all-outcome aggregate remains an intake responsibility.

Plain arithmetic over the literal loops gives65536 training and8192 evaluation
episodes,73728 total,2949120 team ticks,5898240 target transitions and at most8772
rollout model batch calls per fit. These match the card; actual eligible rows are
counted, not topped up. Arithmetic did not import or execute scientific code.

## Clock, scope and remaining boundary

`b06.py:29` derives its work deadline as original started+50, passes that same value
to every training/evaluation rollout, and retains it through final output/readback.
The runner requires the original monotonic start and introduces no reset at128 or
512. Matching manager cap60/reserve10 and actual admission/handle/output routing
still need inspection in the forthcoming exact command. Existing adapter lifecycle
evidence is reusable if its bytes and declared topology remain unchanged.

Applied runtime-spec General requirements before engineering-scope §§4–5. One CPU
learner/thread setting and ordinary independent-world batching are unchanged;
time/update order stays serial. **No uncarded prohibited §4 addition was found.**
The two parameter snapshots are explicitly required scientific outputs, with no
resume/recovery orchestration. Card §7 expressly names reuse of the deadline adapter.
Driver151 + initializer1 + runner28 =180 new non-test lines, within2000/600 limits.
The considerable publication/orchestration portion serves requested checkpoint,
count, primary and partial-output evidence; no unnecessary framework or concrete
ratio-related risk was found, and no ratio-only gate was imposed.

CM owns the planned mocked orchestration/literal-arithmetic checks; this review did
not duplicate or claim results from them. No models, worlds, training updates,
scientific evaluations, fixture runs or profiling were performed. Residual risk is
the not-yet-reviewed exact launch plus actual normal-run completeness/clock/resource
evidence. Static correctness does not establish scientific value or actual runtime.
No semantic source repair is requested; CM retains technical acceptance and DM
all-outcome interpretation. This is independent evidence, not approval or disposition.

## Exact launch-binding follow-up

**No material finding found** in the new8-line B06 launch.sh. Its positional inputs
are the caller's exact-SHA cwd and one selected fit. The quoted cwd supplies both
the inherited B04 launch.sh path and systemd working directory; the declared remote
cwd is `/home/wu/hmasd-worktrees/vsp03-b06-<full launch SHA>`. Each separate
10801/10802/10803 invocation gets name `vsp03-b06-${fit}-20260909`, scientific root
`/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b06_${fit}_20260909` and distinct
admission/terminal siblings. The launcher contains no loop, retry or fourth fit.

The child-shell argv is `bash -c <literal command> bash <admission> <fit> <root>`.
Accordingly `$0` is bash and `$1/$2/$3` are exactly the admission path, selected fit
and scientific output. Quoted variable use prevents word splitting, and the outer
single quotes preserve `$VSP03_B04_STARTED` until the contained shell expands it.
Canonical admission is directly joined by `&&` to the seed-restricted B06 runner.
The runner is the last command, so its actual status is the shell status; retaining
the shell instead of exec does not escape the accepted descendant containment.
No wrapper-level command executes science before the original manager clock.

Passing cap60/reserve10 to the unchanged adapter gives work50, cleanup58 and manager
hard timeout59 seconds from its original monotonic origin. The controller exports
VSP03_B04_COMMAND for the complete actual argv, propagates the manager start into
deadline.py, and that helper supplies VSP03_B04_STARTED to the child. The B06 runner
passes that start unchanged to its `started+50` work deadline. There is no inherited
120s allowance or checkpoint clock reset in this route. Legacy raw technical object
VSP03_B04 remains the explicitly permitted envelope tag; B06 seed/command/roots and
scientific summary identify the actual fit.

The declared staging set includes B01 objective/publication, B02 model/environment,
B06 driver/package marker/launcher, B04 launch/control/deadline, the B06 runner and
both canonical admission scripts. This covers the changed path's repository
dependencies already inspected; CM must still stage the actual committed bytes and
record the exact launch SHA/cwd. Including the new launcher raises this reviewed
source count from180 to188 lines, still within ordinary limits. No new optional
machinery or budget breach appears.

Consumed CM's report that three distinct mocked/literal checks passed after mocking
the local Windows peak_rss fallback, whose psutil dependency is absent locally.
That harness adjustment does not change production bytes or the declared Linux
resource path. No checks were repeated in this review, and no scientific/model/world
execution is claimed. Actual admission, output completeness, complete clock and
termination remain normal-invocation evidence. No further source repair is requested.
