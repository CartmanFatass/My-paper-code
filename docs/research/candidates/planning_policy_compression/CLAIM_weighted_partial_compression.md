# Prospective claim: recurrence of the fixed WBC completion increment

2026-09-25. **Proposed for Pro criticism; not yet selected for execution.** The DM will
record the decision and any pre-execution revision before freezing this claim. This is a
new batch; exploratory B01 is excluded from the confirmation sample and decision rule.

## Claim, unit and scope

Under the unchanged CrossingHost distribution, lawful information, approximate P_k4_M32
teacher and fixed two-stage shared-collection procedure, WBC more often than not improves
completed jobs over matched ordinary BC in an independently generated training/evaluation
block. A block contains one independently trained BC/WBC pair and one fresh shared panel
of 256 H96 deployment contexts. The probability is over the declared training and deployment
sampling procedure, not over an arbitrary host, teacher, trained checkpoint or UAV task.

The formal primary claim concerns the probability of a strictly positive block effect,
not a lower bound on expected effect magnitude, uniform-world improvement or teacher
noninferiority. Report magnitudes as well; a tiny consistently positive effect may have
little value. We preserve the earlier finding as a computation/completion tradeoff, not
full teacher retention or causal evidence for decision-consequence prioritization.

## Selection exposure and comparison

B01 exposed two training pairs on one common 256-context panel. WBC−BC totaled +17/+10
jobs; teacher−AF +34; WBC still lost 12/15 jobs to the teacher. Architecture, features,
weight constants, epochs, optimizer, shared augmentation, teacher and batch size stay
exactly as B01. No best B01 model, epoch or context is reused as a confirmation unit.
No parameter search, extra roll-in, larger model or teacher-budget change is included.

Ordinary BC has identical data, initialization, lawful actor information, model capacity,
sequence order, optimizer exposure and two-stage continuity. Data collection is a joint
procedure: both stage1 policies contribute equal predetermined roll-ins and receive the
same merged data. WBC−BC identifies the weighting intervention inside this procedure;
it does not compare two independently collected imitation algorithms. All approximate
teacher/filter limitations recorded in B01 remain in force.

## Fixed batch proposed

Five new independent blocks; five fits per arm, ten started fits total. Each fit is the
same 40+40 epochs / 960 optimizer updates / 5,898,240 processed agent time rows as B01.

| Block | Training/initialization seed | Training query/permutation seed | Evaluation seed | Evaluation query seed |
| --- | ---: | ---: | ---: | ---: |
| 0 | 925951 | 926151 | 925961 | 926161 |
| 1 | 925952 | 926152 | 925962 | 926162 |
| 2 | 925953 | 926153 | 925963 | 926163 |
| 3 | 925954 | 926154 | 925964 | 926164 |
| 4 | 925955 | 926155 | 925965 | 926165 |

Each block collects teacher contexts 0..255, BC roll-in 256..383, WBC roll-in 384..511;
collection phases 70/71/72 and evaluation phases 80/81/82 remain unchanged. Each final
pair, P_k4_M32 and AF runs on that block's own fresh common 256 contexts, ids0..255.
Panels are independent across blocks. They are not crossed or pooled as extra training n.
No new environment/query calls are bought for intermediate diagnosis; reuse purchased
labels exactly as in B01. Student evaluation has no shadow filter or teacher query.

## Endpoint, uncertainty and fixed decision

For each block b, d_b = mean_context(completed_jobs_WBC − completed_jobs_BC).
Let S be the number of strictly positive d_b among all five blocks; ties count as failures
for this test, so there is no data-dependent sample-size reduction. Test the one-sided
null Pr(d_b > 0) <= 1/2 with the exact binomial upper-tail probability at n=5, p=1/2.
At alpha .05, confirmation requires **all five d_b > 0** (p=1/32=.03125). Otherwise
the primary claim is not confirmed; the five estimates, losses and uncertainty remain.
No additional seeds follow a non-confirmation and no B01 block enters the test.

Report all five d_b, their arithmetic mean/range, and an exact one-sided 95% lower bound
on Pr(d_b>0) (Clopper–Pearson; zero when S=0). This is intentionally a narrow recurrence
claim. The five-block mean is descriptive and does not acquire a distribution-free
mean-effect interval from the sign test. Within-panel context summaries are conditional
descriptions, never substituted for between-block training uncertainty.

For every block also report BC−AF, WBC−AF, both students−teacher, teacher−AF and all native
service/wait/conflict/packet components and adverse contexts. These contextual comparisons
prevent a positive WBC−BC result from being presented as full planning retention or useful
compression when the teacher opportunity or WBC−AF gain fails to recur. They are not new
formal primary claims selected after seeing outcomes. The complete evidence can justify
declining deployment despite a positive primary sign test.

## Cost, technical failure and completion

Configured node wsl_4070; one scientific process, CPU float32, one Torch/BLAS thread and
batch16 as B01. Ten fits; 245,760 collection + 491,520 evaluation = 737,280 team ticks.
3,840 four-move calibrations / closed-form fits = 15,360 calibration moves; 9,600 optimizer
updates, 58,982,400 optimization rows and 1,474,560 endpoint-diagnostic forward rows.
Conditional branch upper bound is (245,760+5*256*96)*32*2*32 = 754,974,720.
Count actual branches and all calibration, filter, query, feature, network, environment,
optimization, output, checkpoint and support costs. Never split away shared collection cost.

B01 rates imply roughly 242s shared collection + 197s fit occupancy + 134s deployment,
about ten scientific minutes with additional output/startup work, conditional on the same
node performance. This is not a reservation or a full engineering/reading quote. Primary
value is the new independent finite-learning/deployment blocks, not a required positive result.
Deployment timing includes the same full boundaries and is not online latency. No deployment
noninferiority margin, global speed guarantee or unpriced amortization claim is introduced.

Every started fit and partial failure is retained. No early scientific stopping, automatic
retry, replacement seed, outcome-dependent endpoint or batch extension. A technical failure
leaves an incomplete confirmation attempt; it is not a negative policy result. Source SHA,
native admission and exact output tag are frozen with accepted implementation before launch.

## Result

Not run. Awaiting the focused scientific decision and fixed-plan criticism in NOTES.md.
