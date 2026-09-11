# CBSC: the next direct-learning family decision after two local zeros

The DM recommends parking the current unchanged 48-update RAW/STRUCT comparison
family, as an investment decision with a narrow scope. Two completed independent
run seeds show real learning but the same fixed-refresh greedy behavior and zero
representation advantage. A specifically motivated, bounded new learning object
remains a reasonable alternative. Convergence should select between them or give
a better concrete direct-learning proposal. No family disposition is applied yet.
This is not a request to close CBSC, alter Portfolio priority, promote to C, or
reopen a failed historical attempt.

## What was actually measured

B02 and the separately delegated B03 are valid B/EXPLORE objects on
CBSC-DYNAMIC-CACHE-2R-1C-v1. Both compared RAW-GRU with
STRUCT-CURRENTNESS-GRU at the fixed update-48 endpoint, using 32 matched
procedural evaluation worlds within each run seed. The seed changes model
initialization, training randomness and evaluation worlds together. There are
two independent paired run seeds, not 64 independently trained policies.

| Recorded run | RAW endpoint | STRUCT endpoint | Paired gap | Common curve at updates 0/12/24/48 | Complete RAW/STRUCT seconds |
| --- | ---: | ---: | ---: | --- | --- |
| B02, seed 21203 | 10.7125 | 10.7125 | 0 | 0.6875 / 10.7125 / 10.7125 / 10.7125 | 79.69 / 90.78 |
| B03, seed 21209 | 10.5875 | 10.5875 | 0 | 2.415625 / 10.5875 / 10.5875 / 10.5875 | 59.53 / 58.67 |

Every one of the 32 endpoint differences is zero in each pair. All trained
greedy checkpoints chose REFRESH for all 768 opportunities per arm. Same-panel
ALWAYS_REFRESH equals the learned endpoint; ALWAYS_SAFE scores 4.0625 and
4.0375 respectively. These fixed policies are contextual references, not a
tuned generic optimum or proof that all legal policies are bounded by REFRESH.
MEI was 0.25 native-return units. The two paired gaps are inside it; this is not
an equivalence test, a confidence interval or a population-negative claim.

Each of the four formal arms actually completed 48 rollout updates, 768 Adam
steps with finite recorded losses, 384 training episodes, 58,368 training
transitions and 128 evaluation executions. Initial-relative parameter movement
was 19.6469845% / 18.7238672% in B02 and 20.3270553% / 18.6828676% in B03.
Movement proves learning activity, not mechanism value. B03 sampled training
actions include RAW 243 SERVE, 8,515 REFRESH, 458 SAFE and STRUCT 237 SERVE,
8,569 REFRESH, 410 SAFE, out of 9,216 decisions each. Final batches were
191 REFRESH plus one SAFE for RAW and 192 REFRESH for STRUCT. Those observations
permit an optimization/exploration hypothesis; they do not establish its cause.

The four complete formal calls sum to 288.67 seconds, with fresh remote memory
admission and trustworthy primary readback. B02's unique engineering check
took another 6.97 seconds; B03 added no simulation check. These sums exclude
control-plane waiting and are not study elapsed time or aggregate CPU work.
They are not a measured C++/batching speedup or a historical-inflation ratio.
All original checkpoints, raw summaries, update rows, pairings and costs remain
available in the result documents and their cited artifact directories.

## The mechanism and the alternative explanations

Binding structure: **systems / information flow**. Public ownership, content and
capability events change which receiver-specific cache entries can support a
legal action. A single learning controller observes the shared public stream;
two receiver entities do not make this a multi-learner co-adaptation experiment.
The controller's adapter feeds the recurrent policy, whose actions affect native
decision and settlement rewards. This is a bounded information-flow question
arising from partial observability; it does not establish variable-population,
distributed credit or general MARL coordination value.

RAW sees the full public primitive history with its generic FIFO; STRUCT is a
deterministic function of that same history. RAW is the containing-information
null. Both have the same recurrent PPO model, native reward, action legality,
CPU FP32 execution and training budget. A valid STRUCT advantage would be a
finite-learning representation benefit, not access to extra information.

Strongest evidence against more unchanged comparisons is the repeated fixed
policy and zero paired return alongside the older exact RAW equality and mixed
LR01. Strongest reason to retain a new learning question is that the direct path
is now trustworthy and measured cost is bounded, while the current training
package may favor an easy fixed policy. Simple-policy adequacy on this host and
an optimization limitation both survive. Neither a unique cause nor matched
tuned-baseline/upper headroom is known. Missing headroom is not a launch gate.

## Concrete alternatives and their decision value

**Park this unchanged comparison family (DM recommendation).** End investment
in further same-host, same-PPO, 48-update RAW/STRUCT repeats. Preserve both zero
results and their limited interpretation. The basis is diminishing information
from this comparison, not proof that currentness is useless or the host optimal.
No experiment is added. The direction's ACTIVE/HIGH Portfolio state is outside
this question. A later distinct learning question can be proposed through the
normal ladder; parking the family does not erase any accepted evidence.

**One new bounded exposure comparison (concrete runner-up, not selected).**
Keep both legal information arms, model/PPO/reward and portable CPU FP32 path,
but train one fresh paired run for 192 updates per arm. Evaluate the same 32
within-run worlds at updates 48 and 192 only; update 192 is the primary endpoint,
while update 48 describes when behavior changes without choosing a best checkpoint.
Each arm needs 1,536 training episodes, 233,472 training transitions, 3,072 Adam
steps and 64 evaluation executions. The pair has two complete invocations and
no policy/trajectory search. Proposed full cap remains 600 seconds per arm,
including admission/startup/training/evaluation/checkpoint/readback and finish.
This is a new direct B, not the old four-arm/three-seed B1b or its competence gate.

The question would be whether additional learning changes the native comparison
or sampled fixed policy. A positive STRUCT gap could justify one or two new
independent runs; a zero or adverse gap would be retained without automatic
further compute. One run cannot isolate a population exposure effect or prove
why optimization changes. More exposure is not assured to help after both
policies become REFRESH by update 12. Its specific information value must
justify selecting it; low projected cost alone is insufficient.

This alternative uses existing host, adapter, rollout, trainer, checkpoint and
native evaluator APIs. The current small direct runner fixes updates/checkpoints
locally; a new object would need a bounded explicit profile change there and in
the CLI. No implementation or run is authorized by this proposal alone. It needs
none of engineering-scope section 4's new machinery. The existing credible
primary path does not require another simulation smoke merely at a new launch.

Convergence may instead select another concrete symmetric training or host
intervention if its native decision value is better supported. State what changes,
which comparison remains fair, necessary counts, costs and the narrow reading.
Do not constrain the choice to our exact proposal, a larger budget or PARK.
Do not require oracle search, a bounded/beam policy search, exact maxima, full
support census, a tuned upper, or unique-cause diagnosis before ordinary learning.
Such work needs its own explicit purpose and comparison of decision value.

## Cost, exposure and protected history

EXPOSURE_AND_COST.json is machine-computed from recorded arm counts/movement and
complete times. Consultation adds zero optimizer steps, evaluations or new
parameter-displacement measurement. For the proposed 192-update alternative,
dominant work is two arms times one independent run, each 192 eight-episode
rollouts and 4 PPO epochs times 4 minibatches, plus two 32-episode evaluations.
No nested candidate/trajectory/solver calls are added. Initial evaluation and
extra intermediate evaluations are omitted because they do not serve this
specific endpoint question; primary final measurement and an update-48 context
remain. Checkpoint format and reward/information semantics remain unchanged.

Using B03's measured host/update phases, holding other full-call cost fixed and
tripling the added host/update work gives about 224.57 / 224.94 seconds per arm.
This deliberately claims no saving from two fewer evaluation points. Four times
the entire B02 calls gives 318.76 / 363.12 seconds as another rough scenario.
Neither is a guaranteed upper, a measured new run or an acceleration estimate;
state/action-dependent costs and host/runtime variation remain unknown. Existing
measurements suffice for this proposal; no calibration experiment is requested.

The old execution/publication repair ended incomplete, with an observed SIGSEGV
followed by a different TypeError on the only reproduction. Their causes remain
unknown. The new direct in-memory native measurement bypasses the old rehydrate
and fifteen-table publication path, but shares host primitives. Its success
supports this path on these executions, not absence of all host defects or
acceptance of old B1/r05 artifacts. Nothing here restarts or reclassifies them.

Please return a formed family decision in conclusion-first natural language,
including the smallest selected unit, evidence ceiling, strongest support and
contradiction, next discriminator and any concrete uncertainty. If retaining a
new B, select a proportionate real-learning question and bounded cost; if parking,
state exactly which family stops. Apply current evidence sections 11.8 and 11.9.
