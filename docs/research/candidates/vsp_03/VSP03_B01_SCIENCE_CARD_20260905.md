An event-rule initialization may improve finite-budget native return over an otherwise identical generic learner on the selected persistent-target task.
Binding structure: temporal abstraction / termination, fixed N=1; this is a single-controller question with no multi-agent-specific claim.

# VSP03 B01 — event-rule initialization

Evidence class **B/EXPLORE**. Direction selection: **PRO_FINAL**, complete Innovator response
at `pro_packets/20260905_k1_host_innovator/archive/RESPONSE.md`, especially “下一步：只实施这个最小 B 比较”.
This is the selected new object, not a restart or repair of the old event-source audit or FSD's
parked fixed-K2 policy-gap family. No result has been observed and B has no consumption state.
Current evidence-spec sections 11.8 and 11.9 apply.

## Question, ceiling and prior evidence

Does the selected trainable initialization bias improve mean native task return after the
declared training budget against an equally informed and equally parameterized generic learner?
The maximum claim is a finite-budget comparison on this new N1 task. No exact upper, optimality
gap, authenticated historical event source, irreducible MARL effect, stable population advantage,
transfer or deployment claim is made. Missing headroom is recorded, not estimated as zero.

VSP-03 A01 established missing host/population/upper/generic baseline/exposure. Its older audit
had zero learner/runtime activity and an unbound event source. FSD E4's public greedy explained
the reported switching opportunity; E3's competent small-seed-2 positive and competent larger
losses remain opposite evidence to universal claims. None supplies this new task's baseline.

MEI is **0.02 return units per episode**, one four-tick waiting cost. It is a descriptive scale,
not a launch, significance or all-positive threshold. A margin above it is an interesting bounded
signal; a positive margin within it is smaller evidence; equality or an adverse sign weakens this
initialization at this budget. The branches below, not MEI alone, control interpretation.

## Environment and complete native consequence

One agent has the fixed task-submitter role; one target has a fixed identity for the whole episode.
There are no partners, joins, leaves of agents, replacements, probes, communication restrictions
or private information cuts. Target occupancy changes are not population changes.

- Primitive state times are 0 through 40; every episode executes all 40 transitions, including
  time after task submission and service completion. Initially y=1 and dwell age d=0.
- At half-integer transition times, an occupied target leaves with probability 1/(d+4); an
  absent target re-enters with probability 1/2. Staying occupied increments d; departure,
  absence or re-entry sets d=0. A negative event is this simulator's own 1-to-0 transition.
- Decisions occur at t=0,4,...,32, at most nine. CONTINUE waits four ticks except at t=32,
  where it waits through t=40 with no submission. COMPLETE submits an irreversible task and
  consumes the next eight ticks; service samples are states t+1,...,t+8 inclusive.
- Delivery succeeds only if all eight service samples are occupied. One failure makes delivery
  fail but does not skip the remaining service or episode tail. No further task or decision
  follows submission. Earlier departure/re-entry is not itself future delivery failure.
- Integer task accounting is `200*success - 10*attempt - waiting_ticks`, divided by 200 once.
  Waiting counts actual pre-submission primitive ticks; unsubmitted episodes pay all 40. There
  is no extra waiting charge after submission. Reward is neither certifier agreement nor
  reward per decision. Actual delivery, failed attempts and missed deadlines remain visible.

The trace is simulator departure -> fixed target/controller -> public history/state -> actual
COMPLETE/CONTINUE action -> task service and native reward -> return-to-go and learner update.
Environment law and task utility are new toy assumptions, not field evidence.

## Information, treatment and strongest selected comparator

Both arms use the same history processor: a is the previous continuing boundary's positivity;
e is an armed negative-event latch, sticky through re-entry; b=a*y*(1-e). Initially a=e=0.
Read a,e,b before boundary updates. CONTINUE sets a=y,e=0; COMPLETE and reset clear both bits.
All primitive negative events update the latch before the next integer decision.

Both networks receive exactly `(t/40, y, d/40, a, e, b)`. Both also know the same constant identity
and role. The host is Markov in y,d and the remaining opportunities are determined by t; no
hidden-history reconstruction disadvantage is imposed on the generic arm. Derived b is shared.

T and G have the same actor, `6->32->32->1` with tanh hidden layers plus one trainable direct-b
coefficient, and the same tanh critic `6->32->1`. Corresponding hidden/critic weights are paired.
The residual actor output weight and bias start at zero. G's direct-b coefficient starts at zero.
T's coefficient starts at `2*log(3)` and its residual output bias at `-log(3)`. Consequently T
starts with submission probabilities 0.75/0.25 for b=1/0, while G starts at 0.5. All coefficients
train thereafter: no veto, permanent rule constraint, action mask or distinct policy class.

The sole extra reference F is the fixed greedy b rule: COMPLETE exactly when b=1. It has no
model or learning and uses the same 1,024 main evaluation episode identities. It is not an upper
or tuned generic learner. Generic competence is assessed from its actual learning, absolute task
outcomes and comparison with F; its name does not certify competence. No complete comparator
tuning or additional one-hit/dwell/debounce/hysteresis grid is selected.

## Learning, randomness and object-tier numerical details

Use a small episodic actor-critic with complete episodes and Monte Carlo return-to-go; primitive
gamma=1, terminal bootstrap zero. For any duration Delta the target has the semi-Markov form
`sum(gamma**j * reward_j) + gamma**Delta * V(next)`; it is the actual remaining task reward here.
Both final CONTINUE's eight ticks and COMPLETE's service/tail belong to their actual duration.

One joint Adam step follows each batch of 128 complete episodes. Learning rate is 1e-3; no replay,
target network, hidden epoch, sweep, reward normalization or advantage standardization is added.
The following implementation details are DM selections inside Pro's chosen mechanism:

- Actor loss is the negative batch-episode average of the sum of valid decision log-probabilities
  times detached advantages. Critic loss is 0.5 times mean squared Monte Carlo error over valid
  decision rows. Entropy uses the episode-average sum over those rows. Padding and post-submit
  states never become gradient samples. This preserves the episode-return objective despite
  policy-dependent decision counts; it does not normalize the actor objective by that count.
- Entropy coefficient at update u=1,...,128 is `0.01*max(0,(64-u)/63)`. Adam has standard
  betas (0.9,0.999), epsilon 1e-8, zero weight decay, and no gradient clipping. There is one
  backward and one joint optimizer.step, not separate actor/critic optimizer counts.
- Use CPU float32 models/learning and integer task-accounting units. Corresponding hidden/critic
  layers use paired PyTorch Linear initialization; apply the selected output/prior changes
  before recording each arm's initial parameter vector. No cross-host bit-equality claim follows.
- Training seed pair is 1: one separately trained T and one G, not two independent estimates
  of the treatment difference. Environment randomness is addressed by seed, split, episode and
  primitive tick, independent of actions; corresponding T/G episodes share it. Evaluation is
  separate from training, and the final F uses the same final-evaluation environment draws.
- A concrete permitted stream layout is PCG64/SeedSequence(seed, split, episode) with 40 uniform
  draws per episode, training split 100 and evaluation split 200+update. Use separate recorded
  CPU Torch action generators for T/G and a paired initialization seed. Future draws cannot
  enter observation. CM records its exact stream constants before any question-relevant run.

Evaluate the current model greedily, with logit exactly zero choosing CONTINUE, at updates 32,
64 and 128; learning is disabled during evaluation. The main endpoint is fixed at 128. Preserve
final actor/critic states, every prescribed endpoint, learning curves, exposure and failures;
there is no best-checkpoint selection or requirement to reconstruct every intermediate state.

## Counts, exposure and cost

The prospective constants and tool-computed ledger are `VSP03_B01_PLAN_20260905.json` and
`VSP03_B01_COUNTS_20260905.json`. These do not instantiate a model or run a simulation.

| Quantity | Per learner arm, seed 1 |
| --- | ---: |
| Actor / critic / total trainable parameters | 1,314 / 257 / 1,571 |
| Training batches / joint optimizer.step calls | 128 / 128 |
| Training episodes / primitive ticks | 16,384 / 655,360 |
| Actual decision rows | At most 147,456; measure actual |
| Maximum decision rows per update | 1,152 |
| Evaluation episodes at updates 32 / 64 / 128 | 128 / 128 / 1,024 |
| Total evaluation episodes / ticks | 1,280 / 51,200 |

F adds 1,024 episodes/40,960 ticks; one eight-episode focused check adds 320 ticks. The complete
pair is **1,454,400 primitive ticks and 256 joint optimizer steps**, not 1,454,400 independent
episodes. Its 36,360 complete episode executions include the check and shared reference.
There is no policy/trajectory search, solver or support-enumeration multiplier. The dominant
work is two arms times 128 batches times 128 episodes times 40 ticks, plus prescribed evaluation.

Record actual parameter counts, initial L2/RMS, first/final displacement and their ratio to
initialization, valid decision and gradient rows, optimizer.step, policy forward calls,
episodes/ticks, fixed evaluation points and one selected configuration. A zero denominator is
undefined, not a zero ratio. Current new learner/model/update/evaluation counts are all zero;
initial scales/displacements and unit times are not yet measured.

The **1,800-second cap covers the complete logical invocation**, including import, shared check,
both sequential learner arms, reference, evaluation, output and necessary read-back. It is an
allowance, not a runtime estimate, and does not reset per arm, script or phase. The phase law per
arm is `I_q + 128*C_q(128,40) + 10*E_q(128,40) + O_q`; shared work adds import/check, eight F
batches and summary/publication. C includes rollout, returns and the joint update. Unit times
and projected seconds remain unknown; do not import FSD timings or divide time by core count.
Measure ordinary complete batches during this invocation to update cost projections; retain
their training exposure. No extra pilot, discarded first run or fast-configuration search.

This card needs none of engineering-scope section 4's default-prohibited new machinery. Use
one research module and a thin runner, existing 2,000-line/600-line-runner/test budgets, one
process, one compute thread and in-process batching. Required scientific counts are not a new
profiler. No C++, GPU, worker pool, remote-service framework or old publication dependency.

Execution is prospectively portable across configured CPU-capable local/remote nodes, not pinned
to host bit identity. CM uses current remote_first (`wsl_4070`, configured Python, CPU device),
an exact committed/pushed source worktree and existing detached agent-task. Fresh memory
admission on the actual node must pass immediately before the invocation. Local fallback needs
no accepted remote process, compatible declared CPU semantics and fresh local admission.

## Focused check, stopping and result branches

One eight-episode, full-40-tick check covers initial latch state, evaluate-before-update,
departure/re-entry, a failure during future service including its final tick, the final decision
and an unsubmitted terminal episode, plus native accounting/publication. Check the selected
behavior and primary output; do not repeat unchanged smoke merely at a launch boundary or add
an all-support oracle. Integer rewards/ticks may be checked exactly because they are the task
law; learned floating-point outputs have no universal extreme tolerance obligation.

Stop at the complete comparison, the whole-invocation cap or a concrete failure of a required
path. No shortened episode, skipped service/tail, partial endpoint labelled update 128, or
post-hoc checkpoint substitution. Credible earlier *paired* endpoints can be reported at their
actual budget if the main endpoint is incomplete; disclose the incompletion. A damaged primary
measurement cannot support its dependent claim; trustworthy narrower facts remain reportable.
Unrelated old failures create no obligation for this independent path; no old quarantine changes.

Primary estimand is mean paired-episode `(R_T-R_G)` at update 128, with absolute T/G/F returns,
success rate, waiting, attempts, failed attempts and non-submission. Record submission time and
small event/re-entry diagnostics with sample counts. Do not call a failed task a counterfactual
optimal-action error without an oracle. Read the result as follows:

1. T>G: retain a bounded initialization/configuration signal. If T also exceeds F and observed
   policy changes improve native outcomes relative to F, that supports learning beyond the
   fixed rule here, without proving learning necessity or uniquely attributing a mechanism.
2. T>G but T<=F: retain the positive comparison, limited to the initialization/budget; no
   beyond-script learning claim. A visibly weak G or a large F deficit is reported alongside it,
   not erased or used to claim a strong generic victory. Intermediate-only gains remain local.
3. Equality or G>T weakens this prior on this task/budget. Waiting, missed deadlines or failed
   submissions may explain an adverse result; they do not refute every event-aware termination
   mechanism. A specifically evidenced B adjustment may follow; no blind budget/host escalation.
4. Incomplete or damaged measurements get their actual narrower reading, not scientific
   negative polarity or invented completion.

Episode-pair standard error describes evaluation noise conditional on these trained policies.
One training pair cannot estimate across-training-seed variability. After a credible positive,
prefer one or two new independent training pairs of the same comparison; retain all signs and
failures. This is ordinary object-tier continuation, not permission to run until all-positive.
Nothing here automatically opens another family or promotes to paper-stage evidence.

## Predictions on record

DM prediction: the prior may help early learning, but shared dwell age makes the rule feature
redundant for the host law; my leading expectation is a final T-G difference within the 0.02
MEI rather than a robust beyond-F improvement. Contrary possibility: finite optimization retains
a useful initialization advantage; adverse possibility: the prior causes over-waiting near expiry.
Owner prediction: **not taken (unattended)**. Preserve any later owner prediction as later, not
as a pre-run statement. The intake records predictions against the actual outcomes.

DM routine details above are **Owner-delegated decision (unattended, 2026-09-03 instruction):
use the specified episodic objective and paired/default numerical details inside Pro's B**.
Root records the corresponding audit/owner items on integration; those surfaces do not hold
implementation or launch. The selected new family is PRO_FINAL, not a local override.
