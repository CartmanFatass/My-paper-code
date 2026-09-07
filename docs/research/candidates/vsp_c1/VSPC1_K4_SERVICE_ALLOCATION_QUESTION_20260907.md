Claim under consideration: A duration-conditioned value learner may improve completed work when a held allocation must divide two workers among three persistent queues, and its value must be judged against both a fully conditioned learner and a legal queue-based policy.
Binding MARL structure: (b) temporal abstraction — holding one worker's allocation changes which competing queue can receive service while a fixed partner responds every tick.

# Next independent K4 question — proposal only, 2026-09-07

**Not a frozen card, selected host or launch budget.** Root resumed distinct-question
preparation from integrated B01 intake `effad6eb7`. That object selected no additional
invocation. This proposal goes to `em:vsp_c1:convergence` because it changes the host and
introduces a policy reference; DM does not silently extend the accepted two-queue object.
No code, environment, model, optimizer, test or performance evaluation has run for this question.

## 1. What the next observation must decide

Would multiplicative duration conditioning yield a useful learned allocation policy when
there are more active service queues than workers, compared with a fully conditioned Q
learner, and does either learned policy improve on a simple legal queue-based controller?
The concrete use is choosing the value representation for a worker that can change its
allocation only at renewals. A positive difference between two weak learners alone would
remain an optimization observation; the policy reference exposes that limitation directly.

The old pair's endpoint −0.000325521, positive AUC +0.000254313, high starting returns and
recorded-tape upper gap 0.013997396 are all retained. They do not identify a unique failure
cause or prove that another workload helps FACTOR. They make another same-endpoint precision
run unhelpful at the old MEI. The proposed distinction is a concrete allocation regime:
two workers cannot simultaneously cover three nonempty queues. Changing seed, optimizer,
training length or reward on the old two-queue task would not test that regime.

This is still a **stationary, fully observed renewal-state control problem with one learner
and a known non-learning partner**. It does not supply partner co-adaptation, learned duration,
decentralized multi-learner credit, a rank restriction or a general MARL result. If this small
allocation question remains too remote from useful K4 learning, the node should decline it
with that reason; physical coupling alone is not a claim of decision value.

## 2. One concrete candidate, not a task sweep

Proposed host: 3 queues, capacity 4 each, H=48 ticks, two persistent workers, initial queues
(2,2,2), previous focal allocation h uniform in {0,1,2}. Each queue receives independent
Bernoulli(0.5) arrivals after service at every tick; clipping and overflow remain explicit.
The expected offered load is 1.5 jobs/tick against at most 2 served/tick, avoiding deliberate
total overload. Actual usable headroom and runtime are unknown. There is no queue-count,
arrival-rate, horizon, partner or period sweep and no pilot used to pick this setting.

At renewal the focal observes (q0,q1,q2,h,t,d), chooses a queue and holds it for the fixed
episode period d in {2,6}. It receives no intervening policy input. Every tick the fixed
partner chooses a longest queue; ties are resolved by the cyclic preference
[(h+1) mod 3,(h+2) mod 3,h]. The partner reads old h and cannot see a simultaneously chosen
new focal action. Distinct queues may each serve one job; coincident workers serve at most
one total. After service, arrivals and capacity clipping occur, then h becomes the held action.
The task reward remains complete served work/96, including empty/collision ticks in the
denominator. Overflow, ending backlog and unused capacity are descriptive, not reward changes.

Event → role → information → action/credit → learning exposure → native consequence:
three streams of arriving work → persistent focal/partner service ownership → renewal-only
focal state and per-tick partner state → held allocation plus actual segment reward/TD credit →
equal-episode real updates → work completed across all queues. A new allocation can serve a
queue the partner would leave waiting, but may also create collisions later in the hold.
That action consequence is an inference from the proposed rules, not an executed witness.

### Learners and competent policy reference

- **FACTOR:** [q0/4,q1/4,q2/4,t/48,one_hot(h),one_hot(a)] gives 10 inputs;
  10→24 tanh→4 biased features dotted with a learned 2×4 period embedding: 372 parameters.
- **GENERIC:** the same features plus one_hot(d), 12→28 tanh→1: 393 parameters.
  Keep the old hidden widths rather than tune parameter matching; the 21-parameter excess
  is explicit. Both share features, and four factors for two periods do not impose low rank.
- **LQ-EXCLUDE**, a fixed same-information policy reference: at each renewal compute the
  partner's immediate action using its public rule; select a longest queue among the other
  two, breaking ties by lowest queue index, then hold for d. It has no future arrivals,
  extra observations, intermediate action choice, training, search or tuned parameter.
  It is a credible greedy null, **not** a claimed optimal semi-Markov controller.

The intended real learner is the already accepted actual-segment Double-Q/Adam path:
16 new complete episodes per update, 8 per d; equal episode/period mean TD loss; normalized
actual segment service, gamma=1, detached target, zero terminal bootstrap; one Adam step;
target copies after each 16 updates. Dense initialization, epsilon schedule, clipping and
optimizer settings follow B01 card §§3–4 without tuning. Greedy ties choose lowest index;
score all 3 actions during behavior even on exploration. No replay or unexecuted-duration rows.
New root seed 402 is proposed only; arm-specific initializations and named shared exogenous/
exploration streams retain the B01 separation, with evaluation independent of training.

The policy reference would be evaluated once on the same 128 episodes per period used for
the final learned policies. It is never used as training data, action masking, model selection,
a reward term, an oracle or a prerequisite baseline-tuning study.

## 3. Smallest sufficient observation and proposed reading

Class B/EXPLORE is sufficient. Primary: FACTOR minus GENERIC mean full native return at
the fixed update-256 endpoint, equal weight on d2/d6, retaining each period. Also report
each endpoint against LQ-EXCLUDE on exactly the same exogenous tapes. Five fixed checkpoints
0/64/128/192/256 retain initial/learning-path context without adding the old nine-point
schedule by default. Any full-curve AUC is descriptive with divisor 256 and cannot replace
the endpoint. The old object's nine checkpoints and result remain unchanged.

Proposed MEI remains absolute **0.025 = 2.4 jobs/48-tick episode**: the same service scale and
practical amount of completed work, not a lowered threshold chosen to rescue the old sign.
No tuned-headroom record exists for this host. The old two-queue supply bound does not
transfer, and neither a new exact upper nor a preliminary performance probe is selected.

If a useful FACTOR endpoint benefit reaches MEI without material period harm, retain it as
one-instance evidence and consider a separately selected one- or two-seed follow-up. If both
learners lag the fixed policy, report any FACTOR/GENERIC difference but do not sell it as a
competent allocation gain. An inside-MEI, adverse or period-tradeoff outcome retains all signs
and has no automatic extra run, budget extension or host search. A useful gain over the
reference with no factorization advantage is evidence about learning this allocation task,
not this factorization. Missing primary/comparison facts limit only dependent claims.

Working prediction before any candidate execution: the greedy reference will match or beat
at least one learner at the fixed endpoint; a clear FACTOR advantage over GENERIC and the
reference on both periods is not expected. Both-period gains of at least 0.025 over both
comparators would contradict that expectation. This is a proposal prediction, not a frozen
ladder or an owner reply; the selected card must restate its actual prediction prospectively.

## 4. Known work and budget boundary

The [machine arithmetic](VSPC1_K4_SERVICE_ALLOCATION_PREPARATION_COUNTS_20260907.json) records
**zero new experiment exposure** and the candidate's prospective work. Root has authorized
preparation, not a transferable unused B01 budget. No resource admission or launch is selected.
Convergence must either select a concrete bounded next object or leave none selected; this
packet does not confer any additional allowance by calling the counts small.

For comparison, candidate planning retains the former maximum of 256 updates/4,096 training
episodes per learner and the former 2,700 s complete-arm cap (5,400 s summed caps, not a
forecast). It reduces the learned checkpoints to five and includes one fixed-reference batch
inside the second complete invocation. These are requested constraints for a possible new
card, not permission to spend an old cap. Any requirement exceeding that ceiling needs an
explicit new decision; no invented expansion, automatic retry, separate cost probe or slice.

| Prospective quantity | FACTOR | GENERIC | LQ-EXCLUDE | Total |
| --- | ---: | ---: | ---: | ---: |
| Training episodes / ticks | 4,096 / 196,608 | 4,096 / 196,608 | 0 / 0 | 8,192 / 393,216 |
| Actual renewal TD rows / optimizer steps | 65,536 / 256 | 65,536 / 256 | 0 / 0 | 131,072 / 512 |
| Evaluation episodes / ticks | 1,280 / 61,440 | 1,280 / 61,440 | 256 / 12,288 | 2,816 / 135,168 |
| Evaluation decisions | 20,480 | 20,480 | 4,096 | 45,056 |
| All joint ticks | 258,048 | 258,048 | 12,288 | 528,384 |
| Scalar Q predictions | 569,344 | 569,344 | 0 | 1,138,688 |

Dominant work: one fixed host × two learned arms × one paired training seed; each learner
has 256 × 16 × 48 training ticks, one update/cycle and 5 × 256 × 48 evaluation ticks.
The fixed policy adds 256 × 48 ticks once. There are 3 ordinary action scores/decision,
one target value/nonterminal row and one partner call/tick, no nested candidate trajectory
or policy search. Relative to B01, trajectory work decreases but scalar Q predictions increase
because there are 3 actions. Neither step count nor the old measured 10.32 s pair forecasts
the new runtime; widths, action scoring and reference publication change work. Extra reference
evaluation is added comparison work, not part of FACTOR's algorithm or a launch gate.

If selected: portable CPU float32, one compute thread, ordinary in-process batch16,
remote_first, fresh per-invocation memory admission, detached exact-source agent-task and
Root observation. The fixed-policy evaluation and paired publication stay inside the
second learner's complete cap. No model/information/dtype change is licensed by routing.
Engineering-scope §4: **needs none**. Normal research/runner/check budgets apply. Prospective
code would use a new mapped VSP-C1 attempt; all prior code and evidence stay preserved.

## 5. Question-driven source checks and what they change

Reused prior verified library evidence from
[B01 proposal §5](VSPC1_K4_REACTIVE_QUEUES_PROPOSAL_20260906.md): ACAC (MARL-0449, pp2–3,
elements405/410/415–416) motivates correct asynchronous observation/credit timing; UTE
(VS-0005, p3, elements95–100/120–146) distinguishes actual holding segments from extra
skip-transition exposure; VSP (MARL-0530, pp1–2, elements126–133) concerns inter-agent
multiplicative dependencies, not a demonstrated duration-factorization advantage here.
Those pointers retain their already verified limitations; no new download or blanket reread.

Fresh formal-index check: `C:/Projects/Inst-sci/papers/MyLib/llm-index/catalog.v2.jsonl`
still has 190 real-paper records. A targeted title/abstract/metadata search for queueing,
queuing, MaxWeight, longest queue, parallel queues, backpressure or server allocation found
no match. Broader asynchronous/duration matches recover ACAC/VSP/UTE; a model-history queue
is not service-allocation literature. My-lib's previously verified two synthetic fixtures
are excluded, not repurposed as evidence; no completed unified real-corpus index is claimed.

The specific scheduling gap was checked against Tassiulas & Ephremides, *Stability Properties
of Constrained Queueing Systems and Scheduling Policies for Maximum Throughput in Multihop
Radio Networks* (1992), [author-institution report/abstract](https://drum.lib.umd.edu/items/571fda52-aefb-4497-9a2d-69d8c7c907b9).
Its problem is server activation under queue/service constraints with stability-region
throughput as the criterion. **DM inference:** a transparent queue-aware control deserves
comparison here; a generic small neural learner alone need not represent competent scheduling.
The paper does not validate LQ-EXCLUDE as optimal under our held-action, fixed-partner,
finite-capacity and 48-tick return. No asymptotic stability theorem or numerical result is
transferred. This verification adds the fixed greedy reference and narrows the claim; it
does not establish novelty or require a MaxWeight/DP solver before B exploration.

## 6. Decision requested and clean boundary

Options for the proper node: select this single constrained-allocation B after any precise
scientific correction; decline this host while keeping the broader duration-value question
open; or explicitly change/close/recast the relevant family within direction authority.
DM recommends evaluating the **one concrete candidate above**, not automatically repeating
the old object. The strongest alternative is that the fixed greedy rule leaves too little
useful learning room and the result would again rank small-network optimization. The node
should resolve that decision value, not demand an exact policy maximum to certify it first.

There is no C freeze, lifecycle/priority proposal, source acceptance or result launch in this
request. If the node selects no object, preserve that specific scientific reason; a transport
or evidence-access blocker is not a scientific decision. Until the complete immutable answer
is intaken, preparation is recoverable and no successor is commissioned. Owner reviews at
this preparation boundary returned `[]`; old object rules and the current P1/P2 cutoff stand.
