# VSP-C1 K4 prospective native-return design

Proposed claim: on a finite fixed-population task, a specified sharing rule may help or harm
native action selection under limited learning exposure across identity and period combinations.
Binding structure proposed: temporal abstraction or termination; partner actions affect team
utility, but fixed partner programs alone do not establish co-adaptation or strategic MARL value.

Date: 2026-09-05. Status: proposal for Innovator selection, not a frozen card or launch assignment.
The inherited census establishes no executable native-return host and no numerical headroom.
The current SCDMP D6 family remains stopped; this is not a new duration-sign/source-state search.

## Decision requested

Choose the smallest worthwhile next object for K4 through VSP-C1: a finite no-learner host/action
reconnaissance, a directly specified bounded B learner comparison, or no new object because the
proposed intervention has no useful distinction. State the exact selected mechanism, host,
population, weights, same-information reference and minimum controls. A may establish execution
and measurement facts only; a learner or baseline tuning is B. No theorem, production four-clone
host or complete headroom package is a generic prerequisite for B.

The DM recommends constructing the small research-tier host within a direct one-seed B learner
comparison, as concretized below. The missing executable host is a real implementation need;
it does not imply a separate exact reference A must run first. The 40-mission enumeration is an
optional cheap diagnostic, not a prerequisite. This adopts the owner's 2026-09-05 clarification
that exploration and paper-claim rigor differ: a genuine single-run performance improvement can
justify bounded independent-seed follow-up before full mechanism attribution or exact reference
work. A scripted generic rule matching an upper reference also does not by itself disprove
finite-budget learning value. Pro may choose an A only if it resolves a concrete implementation
or measurement question more economically than the direct B.

## A concrete candidate host, offered for revision

Use a disposable two-role service task with fixed `N=2`, no membership events and six scored
primitive ticks. The focal agent selects one of two service modes; the partner occupies the
matching service channel. The task is deliberately small enough to enumerate without learning.

| Quantity | Proposed value and ownership |
| --- | --- |
| Focal identity | `i in {0,1}` is the first renewal action, selecting the held service mode. It is not entity identity or a privileged context label. |
| Period | `p in {2,6}`, externally assigned, determines the focal renewal boundaries `0,p,2p,...<6`. The learner does not select period in this object. No learned hazard. |
| Partner strata | Two fixed partner programs: switch the service channel once at primitive tick `tau=4` or `tau=2`. They are two explicit behavioral strata, not two agent IDs. |
| Mirrored context | `c in {0,1}`, independent and uniformly weighted. The partner emits `b_t=c` for `t<tau` and `b_t=1-c` thereafter. |
| Decision information | Before tick 0, both agents receive `c` and the partner's announced switch schedule `tau`; subsequent boundary observations include the last observed partner action and the ordinary clock. The schedule is a public task signal; hiding it only from a comparator is forbidden. |
| Primitive transition | The partner executes its declared channel action each tick; the focal mode is held between legal boundaries. At a boundary, the focal may set mode 0 or 1 before that tick's reward. |
| Native reward | `r_t = 1[a_t=b_t]`, a joint-action service completion; full utility `R=(1/6) sum_(t=0..5) r_t`, in `[0,1]`. No identity, factorization, duration or prediction bonus. |
| First action intervention | Force `a_0=i` for the first segment; after it, each evaluated policy chooses legally at the remaining boundaries. Keep this conditional action-value estimand distinct from a selector's free-choice policy return. |

The event/action trace is: partner's public plan -> partner-owned channel switch -> common
decision information -> focal held service action until its next exogenous boundary -> any
learner's renewal transition/update -> joint service completion. Here period changes which
future native actions are available. It is not merely a discount label or extra elapsed-time
credit. Fixed membership eliminates slot/entity/rejoin ambiguity. Initial and final segments are
uncensored, and all arms score the same six physical ticks.

Public schedules deliberately make the same-information reference simple. That also makes the
task reducible to a fully observed control problem with a fixed partner. Its value, if any, is a
small composition/negative-transfer diagnostic. A successful result cannot establish that MARL
non-stationarity or decentralized information is necessary. If that makes the question too weak,
Pro should identify a different concrete partner-owned information/action path rather than add
an unmeasured MARL label or demand a large production host.

## Population, weights and references

The complete crossed table has `2 identities x 2 periods x 2 partner strata = 8` cells. Within
each cell, the two mirrored contexts have weight `1/2`; each cell has weight `1/8` in the reported
uniform cell summary. Publish the 16 context-level conditional returns as well as all eight
cell means. Identity is an action intervention, so averaging forced identities is a diagnostic
summary, not the achievable performance of a free identity selector.

For an actual selector return, weight the exogenous `(p,partner,c)` contexts uniformly (`1/8`
each), allow the same two first actions to every arm, and compare its realized native return to
the best same-information legal boundary policy on that population. Do not substitute the
forced-action average into policy headroom.

For the proposed A, enumerate all legal continuation sequences after the forced first action.
For `p=2`, four suffixes exist at ticks 2 and 4. For `p=6`, the suffix is empty. Hence the entire
candidate computation is `2*2*2*4 + 2*2*2*1 = 40` six-tick missions, or 240 joint primitive steps
(480 agent actions). No simulator outputs have been computed in this preparation.

The upper is the best legal continuation/first choice with the same public schedule, information
and boundaries. It has no privileged advantage here. A direct generic controller recomputes the
remaining schedule's service sum for each legal action at every boundary, with a fixed smallest-
action tie rule. Report whether it matches the enumerated reference, without renaming that rule
as a trained baseline. If a revised host hides information, separately label a privileged upper
and its information advantage, and use a Bayes/history-matched legal reference for efficiency.

Headroom remains missing now. The proposed A can produce exact action/reference measurements;
it cannot produce the tuned generic-learner headroom required for a learning claim.

## What a selected B must decide rather than inherit by name

### Concrete direct-B option for selection

Train on both periods, both partner strata and both mirrored contexts. No corner or partner is
held out in this first exploration. The complete 2x2x2 forced-first-action table is a final
diagnostic; the primary measurement is each learned selector's free-choice native return.
This asks about finite-budget sharing and negative transfer on seen support, not held-out
composition. A later named run may select a withheld corner or partner if it changes the question.

The proposed treatment is a small learned factorized action-value model
`Q_shared(s,i,p)=u(s,i)^T v(p)`, with a rank-four learned embedding and a 16-unit nonlinear state
encoder. The generic comparator is a fully conditioned nonlinear action-value model receiving
the same `s`, identity action and period, without this factorization. Both can condition their
first identity choice on period; the candidate does not impose a duration-blind selector.
`s` contains the public context, schedule, primitive clock and last partner action. Because that
is sufficient state for this proposed deterministic host, a recurrence requirement is unnecessary
for the first B; recurrence remains an alternative if a revised host hides history. Pro should
fix the generic width so capacity and actual work are comparable, report both parameter counts,
and avoid a deliberately weak generic arm. Exact equality of parameter counts is not itself a
new launch gate or proof of fair learning difficulty.

Use ordinary epsilon-greedy Q learning on real complete episodes, with identical prospective
epsilon schedule and optimizer settings across arms. One transition spans one actual held
segment. Its target is that segment's native reward divided by six, plus the next-boundary
maximum Q when nonterminal; the terminal continuation is zero. Undiscounted six-tick utility
uses `gamma=1`, so period does not generate a reward/discount artifact. Each policy acts on its
own generated trajectory; pair only the exogenous context schedule and random seeds, not
outcome-dependent action histories. Model, policy selection, trainer update and evaluator must
all execute, with nonzero counts and the implemented displacement/initialization exposure line.

Proposed first size: seed 0, batch 32 with 16 lanes per period and balanced partner/context
strata; 128 cycles of six-tick rollouts followed by one full-batch optimizer update. This gives
4,096 complete training episodes, 24,576 joint primitive steps, 8,192 renewal transitions and
128 optimizer updates per arm. Evaluate the free-choice policy at initialization and every 16
updates on all eight exogenous contexts: nine evaluations, 432 additional joint steps per arm.
At the final checkpoint, evaluate the 16 forced-first-action context cells once (96 steps).
Thus the proposed complete two-arm first B costs 25,104 joint steps per arm, 50,208 in total,
before a separately disclosed smoke check; no tuning sweep, future seed or exact census is hidden
in those counts. The same complete evaluator supplies baseline and treatment results.

Record the native-return learning curves, final paired difference, nonzero learner counts and
real parameter displacement. A real positive difference or useful learning-curve improvement
may justify a bounded seed-1/seed-2 follow-up even if below the descriptive MEI; do not require
exact reproduction, a certified upper, a full mechanism account or a paper-ready conclusion.
An apparent improvement from mismatched information, omitted evaluation or a failed learner is
not an improvement to follow up. Flat/equal returns remain valid exploration and may motivate
a different budget or comparison; they do not close K4. Pro selects the first object here; no
additional seeds are launched or irrevocably selected by this proposal.

### Remaining interpretation choices

The old additive centered-logit completion is not automatically the candidate learner. Pro must
name the actual shared parameter path and how it changes a legal policy: for example, whether
identity-conditioned low-level execution is shared across periods while a period-aware selector
or critic remains free to change the identity choice. A duration-blind selector is a restriction
that may cause negative transfer; it must not be silently substituted for a duration-blind
identity executor. A plain additive value model can also forbid action-rank reversals. Distinguish
that representational failure from optimization or sample-efficiency evidence.

The principal comparator should be a competent generic recurrent/value learner receiving the
same observation history, public schedule, identities/actions and period. Match primitive
environment exposure, action availability, model-selection work and meaningful parameter/update
budgets. A period-only controller with less useful information is an ablation, not the efficiency
null. Neither an untrained network nor a scripted optimum is a learned comparator. The first B
may honestly report that its generic tuning is provisional; exhaustive tuning or oracle-level
competence is not a precursor to exploratory comparison. A candidate signal motivates a stronger
generic/independent-seed check before any stronger claim.

Select the smallest control set that changes the next decision. The historical dummy-code,
shuffled-code, persistent-noise and recurrence alternatives remain visible; do not require five
full new learner families if a simpler containing comparator settles this first B. Bijective
relabeling of the two action names alone is not evidence against semantic identity. Any dummy
input must be separated from the legal action itself and must not remove information.

The 2x2 identity-period training rectangle can omit `(i=1,p=6)` for a composition diagnostic,
but this must mean precisely which action-conditioned experience is withheld. Such action
coverage restriction affects both arms' data and training support; it cannot be disguised as
equal ordinary on-policy exploration. Alternatively train all four cells and measure finite-
budget sharing/negative transfer first. Pro should choose, and limit the conclusion accordingly.
Held-out corners and partners are design choices for this question, not C-time gates on B.

Similarly, decide whether both fixed partner strata appear in the first B's training data, or
one is reserved for evaluation. With both trained, there is no held-out-partner claim; with one
held out, an observed difference may be behavior distribution shift or unseen schedule input.
No partner trains or adapts in the proposed host, so neither choice establishes co-adaptation.
Do not alter a frozen arm or split after seeing its result.

## Cost, exposure and implementation scope

Present preparation: zero scientific invocations. The separate machine-generated exposure
record reports zero displacement and no initialized model. It is not a future learner's exposure
certificate. Proposed A: one complete invocation, 40 missions/240 joint steps, no seeds or learner;
one process and one compute thread, ordinary in-process array batching permitted. Proposed cap:
60 s wall including initialization, complete evaluation, checks and publication, with actual RSS
reported. No C++ speedup or measured sub-second completion is asserted. A missing/failed resource
measurement or actual runtime failure is not a negative mechanism result.

For the concrete proposed B above, batch 32, six primitive ticks and 128 rollout/update
cycles give 24,576 training joint transitions per arm and seed. Including all proposed evaluation
work gives 25,104. These are proposed counts, not an admitted budget or a measured projection.
At fixed period `p`, renewal
rows are `M=32*6/p` per cycle: 96 at period 2 and 32 at period 6. If the design instead conditions
on three training cells or batches variable periods, count those rows explicitly; do not credit
both periods with equal optimizer exposure merely because primitive exposure matches.

The complete per-arm/per-seed wall projection must include host construction, model setup,
training, all evaluations/checks and publication, using the selected runner's measured cost law.
No seconds-per-update or total B duration is available yet. Suggested first B scale is one to
three paired seeds with a complete invocation cap no larger than 2700 s per arm/seed; Pro must
choose the actual first object before this becomes a card. A future machine-generated exposure
line must state the implemented learner's displacement relative to initialization, not reuse
this preparation's zeros. Toy 2700 s and UAV 43200 s are investigation thresholds, not extra
budget; this proposed task is a toy, not a UAV proxy.

Implementation, if selected, belongs in `experiments/candidates/vsp_c1/<new_attempt>/`, its
mirrored tests, and one thin `scripts/run_vspc1_<new_attempt>.py`. Reuse ordinary array operations
and a compact finite evaluator; no dependency installation, core package edits, new registry,
clone machinery, resume service, generic worker pool, added gate or telemetry framework is
needed. Keep the normal 2000-line attempt/600-line runner budgets. A future CM owns the exact
source/fixture/command and independent review. Exact accepted bytes must be committed and
pushed before execution on the configured remote-first node with immediate node-local admission.
The pure discrete host is prospectively portable; a future learner's dtype/RNG/device choice
must be fixed by its own card before output. No VNFC-specific four-thread exception transfers.

## Predictions and interpretation for Pro to assess

DM design prediction: the public-schedule generic rule will match the proposed upper, and the
finite table will expose where an overly restricted sharer changes an action. The unknown is
whether any selected finite-budget learned sharing rule answers more than this elementary
control calculation. This is a prediction, not an observed return or a direction negative.
Owner prediction: not taken (unattended).

For a future normalized-return B, a provisional MEI of `1/12` would mean half one service step
per six-tick episode, making the scale concrete. It is an offered DM design choice, not a
repository threshold or a frozen branch. Above it would motivate an independent-seed/stronger
generic check; a genuine positive effect inside it may also justify bounded independent seeds,
with its smaller magnitude stated. No detectable effect can favor a cheaper control or a different
discriminator; opposite sign can motivate locating representation/optimization negative transfer.
The selected card's actual
branches remain the reading rule. A feasibility A has no efficacy MEI.

The requested final answer should select or revise one next object and explain what observation
would change the next decision. If it cannot do so, identify the exact scientific design gap.
No lifecycle, priority, capacity, source fusion, old-family reopening or code acceptance is
requested. Return a conclusion-first natural-language decision with evidence and limits.
