Proposed question: Can a fresh sampled-return model use the paid count to improve native net return over a count-blind model trained on the same episodes and the strongest immediate reference?
Binding structure: **systems / information flow**. The finite coordinator host does not instantiate multi-agent partial observability or non-stationarity; this proposal makes no MARL population claim.

# P07-UCOPE-PREP-01 — next independent-value question

Status: **PROPOSAL ONLY**. No card, experiment, provider Send or new budget is selected.
Inputs are [B01 intake §§2–6](UCOPE_NATIVE_RETURN_ACQUISITION_B01_INTAKE_20260907.md) at Root
`99e587f6b` and [DIRECTION.md, current scientific position — 2026-09-07](DIRECTION.md#current-scientific-position--2026-09-07).
Their bytes are unchanged at preparation base `28fecc4342c61bfd91bd3130388112f0e8491ea3`.
Root's P07 assignment authorizes this analysis and delivery to Portfolio and Root only.

## Original proposal text

I recommend preparing a B/EXPLORE question about whether learned conditional returns can make
paid information useful. Train two simple return models on the same fresh, deliberately exploratory
episodes: one may condition the duration decision on the paid displayed count, while the other
uses public context only. Both learn from realized full native return and decide whether probing
beats their learned immediate value. Compare their final policies with each other and IMMEDIATE-4.

B01 remains a valid NR-B result: both final policies were immediate everywhere, with zero native
gain despite 126,242 training probes and 2,048 updates. That does not establish that probe exposure
vanished or that information has no value. Historical PA-B/TW-B benefits, their competence and
false-probe contradictions, and all quarantines remain. The retained-policy/numerical-locus
branch stays stopped.

The minimum observation that could change the decision is one fresh shared-data training pair
whose count-conditioned final policy actually acquires information and exceeds both the blind
model and IMMEDIATE-4 in sampled, cost-inclusive return across all eight contexts, with the
proposed 0.001 mean-return effect size and every context loss retained. This would justify a
bounded independent-seed follow-up, not stable superiority or an explanation of B01. A difference
from the blind model without a gain over IMMEDIATE-4 would not establish useful acquisition.

Scientific selection of this learner/comparator inside the accepted paid-information mechanism
is object tier. Portfolio retains investment and sequencing; no direction-tier recast or family
disposition is proposed. The recommended next task is for this DM to select or revise this
question and prepare its source-bound B card and focused CM handoff. The illustrative work below
is not an allocation: this preparation performs zero new training or evaluation and authorizes
no next invocation.

## 1. Retained evidence and the independent decision value

| Evidence retained | What it changes here |
| --- | --- |
| B01 seeds 6301/6302: `Delta_s=0/0`, `Delta_bar=0`, all final modal roots IMMEDIATE-4; 65,536 evaluation episodes per seed | Another identical invocation or changing the reported endpoint alone would not test the proposed return-model question. B01 is not relabelled or retuned. |
| B01 training: 524,288 episodes, 126,242 probes, 2,048 joint updates; every batch tail-active; nonzero root/tail movement | A literal absence of learning/probe exposure is excluded. Credit quality, finite budget, exposure allocation and modal deployment remain unlocalized alternatives. |
| B01 formal whole-process wall 8.80/9.67 s, summed 18.47 s; CPU FP32, one thread, existing real-host sampler/publication accepted | The native source is available for a new bounded learner. These are existing costs, not a timing guarantee for the proposed algorithm. |
| PA-B treatment 5/6 versus reference 6/6; TW-B tail coverage 6/6 versus 4/6 | Paid information is not globally refuted. These outcomes do not prove that the new learner will succeed. |
| TW-B full competence 3/6 in both arms; two false probes lose 0.028562899 each | Counting learned predictions, changed tail actions or probe frequency is insufficient. The primary comparison must retain native cost and losses in other contexts. |
| Historical oracle/reference gap 0.00267963765625; no tuned generic current-host headroom record | A generic learned return-model baseline is a useful next reference, not a novel-method claim. A positive single B would still not create a tuned headroom record. |

The new decision is whether useful acquisition can be recovered by a simple same-host value
learner whose final root choice evaluates its learned conditional tail values. B01 used a joint
score-function objective on full sampled return; it did not fit this return model. The proposed
comparison asks a bounded performance question rather than locating the cause of B01's null.
It could supply a competent generic learned baseline for later work, or a second specifically
bounded null. Neither outcome changes the direction's broader evidence ceiling by itself.

The information-blind model is important: training uses the same exploratory episodes and full
reward labels for both models. Any gain over that model cannot be explained merely by collecting
more paid episodes than B01. IMMEDIATE-4 separately prevents a weak or loss-making blind model
from turning a relative improvement into a claim of positive native value.

## 2. Concrete proposed learner and legal information path

Use B01's unchanged eight contexts, even periods `{2,4,6,8}`, native return, paid service/time/energy
terms and count-only host callback. The source anchor is `a0b00f561159ddeedf66b65711cf3f7d2ec93b04`,
using the four bound `conditioning_discriminator_r01` modules in B01 card §1. This is fresh data
and fresh parameters; no retained policy, historical offset, oracle label or unchosen return is used.

The proposed pilot would collect one fresh dataset in 1,024 batches of 256 real episodes. Each
context contributes 16 IMMEDIATE-4 and 16 PROBE episodes per batch. After paying, a probe's tail
action is uniform over the four legal periods. That is a declared exploration policy, not free
information or a policy search. Every episode's native cost and exposure is counted. The behavior
differs from B01; no matched-dose or architecture-superiority claim against historical B01 follows.

Fit observed-return means with ordinary incremental updates, `q <- q + (R-q)/N`, starting from
zero. Update only the value entry for the action actually executed, after the complete episode:

- Shared immediate estimate `q_I(c)` from the immediate episodes.
- Count-conditioned estimate `q_F(c,n,k)` from paid episodes' displayed count and chosen period.
- Blind estimate `q_B(c,k)` from those same paid episodes, discarding the displayed count.
- Empirical displayed-count frequencies `p_hat(n|c)` from the paid training episodes.

These are learned tables and their ordinary sample counts. They do not access the hidden regime,
actual marks, simulator probability function or analytic optimal action. The full native return
is the target for both tail estimates; no reward-component subtraction or privileged causal label
is introduced. Unseen full-model cells use the corresponding learned blind estimate; unseen
contexts/actions retain the declared zero initialization and modal tie rule. No complete-support
census is required to train or evaluate the learner.

The full model's final root compares `sum_n p_hat(n|c) max_k q_F(c,n,k)` with `q_I(c)`. If it
probes, its tail chooses `argmax_k q_F(c,n,k)` after receiving the current displayed count.
The blind model compares `max_k q_B(c,k)` with `q_I(c)` and, if probing, chooses that same
context-only period regardless of the display. Ties choose immediate at the root and the lowest
period at the tail. The small sums and four-action maxima are the proposed policy's ordinary
action calculation over learned values, not a search over policies or future trajectories.

Thus the path is: real hidden host event → coordinator's public-context purchase decision → paid
displayed count → duration choice → full realized native reward → observed-action value update →
the next trained policy's purchase/action consequence. Current-episode count or reward cannot
reach the root before purchase. In SEVERED, the callback sees only the independent displayed
count; actual-mark reward arrives after duration choice. The blind policy never uses that display
for its current action. Membership and lifetime do not vary in this host; no roster claim follows.

This is a deliberately small tabular learner, not a proposed replacement of the core trainer.
It tests attainable sampled-return performance on the declared finite population. It makes no
representation, transfer, generic MARL, oracle-competence or exact-policy-maximum claim.

## 3. Minimum observation and interpretation

Evaluate only the final fitted policies on fresh host addresses, with the same 4,096 sampled
indices per context for full, blind and IMMEDIATE-4 policies. A training dataset/seed is the
independent unit; the two models share that dataset intentionally. Contexts, action cells and
evaluation episodes do not add independent learning runs. Compute paired differences and their
conditional Monte Carlo uncertainty, retaining all eight contexts and each policy's paid cost.

Primary native observable: `Delta_native = mean_8contexts(R_full - R_IMMEDIATE-4)`.
The question's information discriminator is
`Delta_information = mean_8contexts(R_full - R_blind)`.
The blind/reference comparison, probe frequencies and paid components remain visible.

Proposed minimum effect of interest: **0.001 absolute** for the two comparisons. This reuses
B01's meaningful scale because host, native units and immediate reference are unchanged:
Python gives 37.318% of the historical 0.00267963765625 reference gap. It is a proposed card
choice, not a repository-wide threshold or post-result change to B01.

- A complete first pair above that scale on both comparisons, with actual paid acquisition,
  would support one or two separately bounded independent training-data seeds. It would not
  require every future seed to improve and would not establish stable superiority.
- Gain against blind but no gain against IMMEDIATE-4 would show that conditioning affects the
  learned action comparison without demonstrating that its information is worth its native cost.
- Gain against IMMEDIATE-4 without a corresponding gain against blind would leave the claimed
  information increment unsupported; the full native comparisons would still be reported.
- Null or adverse outcomes would bound this learner and data budget. They would not identify
  B01's failure, close paid-information research or automatically authorize another run.

These are prospective interpretations, not a frozen decision rule. The next card must settle the
reading branches before output; this memo selects no seed, run, extra endpoint or invocation.
No exact diagnostic, replay, oracle maximum or full causal explanation is a prerequisite. A
sampled measurement of the old stochastic B01 policies could answer its own narrower question,
but it would not supply this independent return-model comparison or another training sample.

## 4. Dominant work and proposed engineering boundary

Python calculated this illustrative **one-dataset** shape; no learner or simulator was executed:

| Quantity | Prospective work, not allocated |
| --- | ---: |
| Independent fresh datasets / learned controllers / fixed references | 1 / 2 / 1 |
| Shared real training episodes | 1,024 × 256 = 262,144 |
| Paid / immediate training episodes | 131,072 / 131,072 |
| Scalar observed-return mean updates | 393,216 across full, blind and shared immediate estimates |
| Empirical count-frequency updates | 131,072 |
| Learned value entries | 8×7×4 + 8×4 + 8 = 264 |
| Evaluation episodes | 3 × 8 × 4,096 = 98,304 |
| Total sampled episodes | 360,448 |
| Host-event transitions, including possible full/blind evaluation probes | 1,507,328–1,900,544; actual required |
| Candidate-policy / trajectory search | none |

Dominant work is one real-host collection, two small fitted tables sharing its labels and three
final sampled evaluations. The table maxima cost at most seven counts × four periods per
context; there is no `4^(8*7)` policy enumeration, nested controller rollout or validation sweep.
The 393,216 value updates are incremental parameter updates, not Torch `optimizer.step` calls;
the eventual exposure line must name their true units and value-table movement from initialization.
The two fitted models do not double the environment-episode count.

Actual runtime of this learner is unmeasured. B01's measured 8.80/9.67 s and earlier 53.394 s
projection are available context only. A **600 s complete one-dataset invocation** is a candidate
upper bound for a later card, including collection, both fits, all evaluation and publication;
it is not allocated here and cannot be split into fresh per-model allowances. Unknown unit time
does not require a separate cost experiment. The next card/CM handoff must retain the real cap
and return any concrete inability to complete within it.

Prospectively use the existing `remote_first` route, CPU numerical semantics explicitly bound
on the new card, one scientific process/compute thread, existing detached execution and fresh
destination resource admission. Neither a specific processor nor wall time is the estimand.
**ENGINEERING_SCOPE_SPEC §4: needs none.** No new framework, guard, registry, retry, supervisor,
telemetry system or compatibility layer is proposed. Ordinary research source/runner budgets apply.
Additional validation is one focused changed-path check: table updates from actual actions,
blindness/current-count ordering, root value calculation and primary publication. Reuse existing
host checks; no old full-array or numerical-locus verification is inherited.

## 5. Question-driven source check

The retrieval question was whether acquisition should be valued by its learned downstream return,
and what simpler null is needed when a policy can change without improving native performance.
Verified My-lib `coverage` still exposes only two `synthetic-core` fixtures; they were excluded.
Inst-sci's `llm-index/catalog.v2.jsonl` contains 190 real-corpus index records. Bounded title/method
queries for communication, value of information, credit and actor-critic identified the source
below; index metadata was not treated as substantive evidence. No unified real-corpus integration
or comprehensive novelty search is claimed.

Reused evidence: DACOM, Yuan et al., AAAI 2023, DOI `10.1609/aaai.v37i10.26389`, as verified in
[B01 preparation §5](UCOPE_NATIVE_RETURN_ACQUISITION_B01_QUESTION_PREP_20260906.md#5-evidence-check-risks-and-next-action).
Its learned waiting/action-value treatment continues to support charging native delay and service
cost. It does not imply this tabular learner will outperform the B01 policy-gradient learner.

New source read: Zhang et al., **VIL2C**, AAAI 2026, DOI `10.1609/aaai.v40i35.40234`,
[publisher record](https://ojs.aaai.org/index.php/AAAI/article/view/40234), local source
`C:/Projects/Inst-sci/papers/MyLib/json/MARL-0203.json`, page 4 element IDs 227, 229, 230 and
page 5 IDs 295, 303, 304 (JSON indices 88, 90, 91, 148, 155, 156). The paper measures message
importance through effects on recipient decisions relative to latency, and trains its communication
objective alongside MAPPO with a critic. Metadata verifies the official title and publisher-open
nine-page PDF, no quality warning; its library screening coverage is PARTIAL, not a full-field census.

**What this changes in the proposal:** action change or an information-importance score will not
be the primary outcome. The paired blind learner and IMMEDIATE-4 comparison make the incremental
native value explicit. This is DM inference from the source, not a claim that VIL2C used this
return table, that its VoI proxy is invalid, or that the proposed question is novel. No additional
communication stack or MAPPO adapter is commissioned. CM would need only the native sampler
pointers and §2's learned-value equations, not the paper corpus.

## 6. Tier, next bounded task and delivery

**Scientific tier: object.** This proposes a changed learner and comparator inside the accepted
paid-acquisition mechanism. It does not open a new direction, replace its host, promote to C,
recast the mechanism or reopen the retained-policy root-residual family. If a later proposal did
one of those things, it would go to the appropriate direction Pro node; no such Send is part of P07.
**Portfolio tier remains separate:** selecting this preparation for investment/sequencing is
Portfolio's task. This memo recommends one usable question and makes no cross-direction choice.

Recommended next bounded task, if Portfolio continues this question:

1. **Target/action:** the existing UCOPE DM, `/root/dm_ucope_question_prep`, selects or revises
   the one-dataset return-model question and writes its source-bound B card and concise CM handoff.
2. **Inputs:** this proposal §§2–4, unchanged B01 host/card §§1 and 3, and accepted B01 intake
   §§2–6. No historical numerical-locus files or source interfaces are inputs.
3. **Bounds:** documentation/source binding and ordinary implementation planning only; no
   experiment or provider Send. Selection must explicitly settle initialization/update units,
   fresh RNG/seeds, final endpoint, MEI/rule and complete-invocation cap. It adds no prerequisite
   A measurement or extra cost pilot. A card alone is not a CM execution dispatch.
4. **Return:** card or concrete scientific revision/blocker to Portfolio and Root. Only after
   that object decision should Root dispatch the same available CM with the five-item handoff.
5. **Report:** name a missing source, target, capacity assignment or scientific conflict directly;
   do not substitute another direction. Inputs and both return targets are available now:
   Root is the native parent `/root`; Portfolio is configured task
   `01a07a3e-29bf-7f52-bc1e-cfa214b8d94a` in `.codex/hmasd-portfolio.toml`. No execution capacity
   was measured or reserved; fresh seeds and the actual cap remain for the later object decision.

Options returned: **(a) prepare this object's card (recommended); (b) defer this question without
changing lifecycle; (c) revise this specific comparison.** No option is auto-applied as an
investment or experiment decision. The only completed action is the P07 proposal. The owner
review command returned `[]`; the recommendation is published as P1 Portfolio item
[`20260907-ucope-002`](../../portfolio/owner/inbox/2026-09-07/20260907-ucope-002.json), with no
auto-applied option, without waiting for an owner reply. No new card or result brief is created.
Both prior formal handles remain terminal. All accepted science, historical quarantine,
retained-policy/numerical-locus stop, lifecycle, priority and recast count remain unchanged.
