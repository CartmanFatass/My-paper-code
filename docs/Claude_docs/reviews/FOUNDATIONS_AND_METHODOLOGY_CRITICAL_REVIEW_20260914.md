# Critical review: starting assumptions, methodology and direction selection

Date: 2026-09-14. Author: Claude Code (Fable 5.1), at the owner's request after the owner wrote
that repeated failures had made them question their original assumptions, methodology and
conclusions. Read-only: no experiment was run, no card or decision record was touched.

Provenance note the reader should weigh: earlier Claude sessions wrote several of the documents
this review criticises, including evidence-spec §11 (2026-09-02), the untied-K/N trade-off
ledger, ADR-01/02 for the duration direction, and `MARL_EXPLORATION_GUIDANCE_20260904.md`. Where
those documents contributed to the problem, this review says so.

Sources read: the HMASD paper (Yang et al., NeurIPS 2023, PDF in `docs/new-libs/papers/`); OPT
(Liu et al., "Interaction Pattern Disentangling for Multi-Agent Reinforcement Learning", IEEE
TPAMI 2024, not in the repository, assessed from the published paper and the repository's own
summaries); `ALGORITHM_DESCRIPTION_v6.md`, `ALGORITHM_KNOWLEDGE_BASE.md`,
`HACTSE_P4_highlevel_design_inspiration.md`, `ALGORITHM_PRINCIPLES.md`; the R21 and R35–R40
failure reviews; the evidence spec; `ExpRecord.md`; all 27 `DIRECTION.md` files and their latest
intakes; four recent science cards in full (ACVC, FOLR, FSD, MGTAP); the Portfolio decisions of
July–September; the audit ledgers; and the scenario-1 environment source.

---

## 1. Verdict in one page

The programme has a sound reproduction of its starting point, several real negative lessons, and
one genuinely promising empirical signal. It does not have a validated premise, a benchmark, or an
inference procedure that can turn its experiments into knowledge. The repeated "failures" are
mostly not failures of the mechanisms; they are the expected output of a pipeline that tests
one-seed, small-budget mechanisms on bespoke toys against a decision rule finer than the noise.

The five findings that matter most, in order of consequence:

1. **The hierarchy premise was never tested on the target task.** HMASD is a sparse-reward
   exploration method. The UAV base-station task is dense-reward (0.7 coverage + 0.3 SINR
   quality − altitude). No flat MAPPO or MAT result exists on scenario 1 in this repository (the
   2026-09-04 baseline set says so explicitly). So it is unknown whether team/individual skills
   help at all on the host that motivates the whole "untie k, untie N" programme.
2. **The decision rule is finer than the seed noise.** Almost every September object trains one
   policy per arm and reads a paired difference against a minimum effect of 0.01 J with an
   evaluation-only standard error. The one direction with five independent pairs (FSD) shows an
   across-seed standard deviation of about 0.08 J, eight times the MEI. Under that variance a
   single pair "inside MEI" or "adverse" carries almost no information, yet single pairs have
   parked MGTAP, LCAC, DISH, UCOPE and ACPS.
3. **Positive results are mostly measured on undertrained learners.** ACVC's headline "+0.117 J
   for the fixed package over the learned proposer" is measured while the learned proposer sits at
   J ≈ 0.15 after 4,096 episodes. The standing HMASD reference on the same family of hosts reaches
   coverage 0.96, which implies J ≳ 0.67. A heuristic beating a policy at a fifth of achievable
   performance is not evidence about the mechanism.
4. **Each direction built its own environment.** Twenty-two candidate directories contain their own
   `step()`; 41 host files exist. Results therefore cannot be compared, pooled or transported, and
   the July lesson ("the next substrate must inherit positive evidence from the algorithm being
   extended", R35–R40 review) was re-violated at scale.
5. **Throughput replaced judgment.** In the eleven days 2026-09-04 to 09-14 the loop produced 226
   science cards, 141 Pro packets, 859 intake documents and 1,716 audited decisions. That is about
   twenty new scientific objects per day, each decided by a language model reading documents it
   also wrote. No human research group could digest that rate, and the record shows the loop
   could not either: the direction set went 33 → 15 → 9 routes → 5 new registrations → 2 occupied
   slots in six weeks without a single replicated positive result.

The recommendation (§6) is to stop the loop, run one properly powered headroom experiment on the
real host, choose one external benchmark per untying axis, and restart with two directions, five
seeds each, and the owner deciding what runs.

---

## 2. What HMASD actually claims, and what was inherited

**The paper's claim.** HMASD (Yang et al., 2023) is a two-level algorithm for *sparse-reward*
cooperative tasks. A transformer coordinator assigns a team skill Z and individual skills z_i
every k steps autoregressively; a shared low-level PPO actor executes; two discriminators
(q_D(Z|s), q_d(z_i|o_i,Z)) supply intrinsic reward so that skills visit distinguishable states.
The objective is a variational lower bound of a maximum-entropy control-as-inference model.

**What the paper's own evidence supports.** On Alice_and_Bob, SMAC with 0–1 reward and Overcooked
it beats MAPPO, MAT and MASER with five seeds. The appendix is candid: on SMAC only 24% of
learned skills are useful; only 26 of 35 runs learn anything; final performance is bimodal (0 or
1); performance "varies greatly" with k, n_Z and n_z; on hard tasks the extrinsic weight λ_e = 100
so the intrinsic reward is a bootstrap that the task reward then dominates. The paper's
contribution is therefore *exploration under sparse reward via diverse skills and complementary
assignment*, and the paper itself flags instability and hyperparameter sensitivity as limitations.

**What the repository verified.** The R41B run (2026-07-16) reproduced HMASD on the paper's
Alice_and_Bob with win rate 0.89 (CI 0.83–0.95). That is a real positive anchor and the project
was right to insist on it.

**What the repository assumed without verifying.** That HMASD's hierarchy is the right base for a
dense-reward UAV coverage task. The paper reports that on dense-reward SMAC MAPPO and MAT already
reach near 100%. On scenario 1 the reward is dense every tick. The standing HMASD reference
(REF-20260617, coverage 0.96) has no MAPPO comparator, and the baseline set of 2026-09-04 records
"no located flat MAPPO result on `envs.pettingzoo.scenario1.UAVBaseStationEnv`". Every subsequent
question ("does variable k help HMASD?", "does variable N break HMASD?") is conditional on
hierarchy mattering here, and that conditional was never discharged.

## 3. What OPT is, and why the fusion was decorative by construction

OPT (Liu et al., 2024) learns a small set of sparse interaction prototypes with sparsemax and a
disagreement/contrastive term, and uses the resulting compact interaction representation inside a
*value-decomposition* learner (QMIX family) on dense-reward SMAC. It is a representation module
for the mixing network. It has no controller, no skills and no hierarchy.

HA-CTSE v6 (July) put OPT's prototypes as a "recognition" layer under HMASD's "commitment" layer
Z and a "response" layer z_i. The repository then derived, correctly, the *vacuity lemma*: a
recognised variable is a function of state, so an identifiability reward on it has zero policy
gradient. That lemma is the strongest theoretical result in the repository, and it says the
fusion's central component could never be paid to do anything. The empirical record agrees:
R21 measured forced-Z skill KL ≈ 0.002 at both initialisation and convergence ("Z never
actionable"), and the roster channel was "measured DECORATIVE, kl_shuf ≈ 4e-6". The v6 status
block itself lists the async-lifetime advantage, the whole point of the design, as "ZERO
confirmatory reads".

So the OPT half of the starting point was abandoned in July for a sound reason, and nothing in
the current 27 directions depends on it. The residue is vocabulary: "situation", "commitment",
"docking", "renewal", "receipt", which the later direction names inherit without the mechanism.

## 4. Are "untie k" and "untie N" well-founded research objects?

**Untie k (variable skill duration).** The trade-off ledger of 2026-09-01 lists the costs (K-1 to
K-7): termination collapse, age-confounded discriminator reward, SMDP bookkeeping, semigroup
inconsistency, loss of the team-skill window, higher variance, matched-duration measurement. Its
one robust conclusion is that a flexible duration only pays when the *latent that the plan tracks
changes at a hazard rate comparable to 1/k*. The UAV scenario-1 host has static uniform users and
no exogenous events; there is no latent to react to. The relay-corridor host was built precisely
to supply a hazard (λ_regions = 0.005, 0.02) and is the right kind of host, but the September
FSD objects that produced the positive signal ran on the UAV host (6 UAVs, H500), not on the
corridor. The question is well-founded; the host on which it was answered is the one where it
should matter least.

**Untie N (variable roster).** Permutation-invariant architectures, parameter sharing and
train-N/test-N′ transfer are settled literature (the deep dive found InforMARL, ExpoComm, Sable,
ACE). The novel sub-question, within-episode leave/join with survivor state continuity under
on-policy learning, is real but is largely a *systems* question: what to do with hidden state,
optimiser state and advantage grouping when an entity disappears. The 2026-09-04 guidance said
this ("several directions are systems questions in MARL clothing") and it still holds. Where the
project asked an actual learning question (FOLR: does persistent entity memory help?) the answer
on easy Traffic Junction H20 was no, three times, and that host is one where memory is not
needed. A negative on a host that does not require the capability is not evidence about the
capability.

**The joint premise.** Both untyings are framed as properties the *final algorithm* must have
("one general MARL algorithm that can learn under variable membership and variable lifetime",
`ALGORITHM_PRINCIPLES.md` §1). No benchmark in the repository or the literature deep dive requires
both, and no benchmark in the repository requires either in a way that a fixed-k, fixed-N
learner demonstrably fails. The research objects are therefore not wrong, but they are premature:
the necessity experiment (a host where fixed k or fixed N provably loses) was skipped.

## 5. Methodology

### 5.1 The inference procedure cannot separate effect from noise

Facts from the card audit of all 227 September cards:

| Property | Observed |
| --- | --- |
| Training seeds per arm | one, in about 215 of 227 cards; zero multi-seed cards after 2026-09-08 |
| Uncertainty reported | evaluation-episode SE only (32–128 worlds, common random numbers) |
| Decision rule | paired mean vs an absolute MEI (0.01 J on UAV hosts; 1.0 on Traffic Junction) |
| MEI justification | "the existing local development scale", never derived from variance |

The only direction with repeated independent pairs is FSD. Its five I−D0 differences are +0.057,
+0.206, −0.012, +0.013, +0.074 J. The across-pair standard deviation is about 0.08 J. Any single
pair therefore has roughly a one-in-three chance of landing inside or below the 0.01 J band even
if the true effect is +0.07. The same logic in reverse: MGTAP's sequence (+0.024, −0.026, −0.005)
is consistent with a true effect of zero *and* with a true effect of +0.02; the PARK decision
treated it as informative. LCAC (−0.004, +0.002, −0.018), DISH (one pair), UCOPE (one pair),
ACPS (two pairs, −0.037 and −0.005) were all parked on evidence that cannot exclude a positive
effect the size of the MEI.

The spec's §11.8 (which a Claude session helped write) is partly responsible. It removed the
July over-formalisation, correctly, but it also wrote that "one real, trustworthy result may
justify a bounded follow-up" and that "one or two independent training seeds" is the default.
Read by an unattended loop, that became "one pair decides". The correction should have been a
*variance-derived* minimum effect (for example, an effect must exceed twice the across-seed SD
measured on that host), not a fixed 0.01 J convention.

### 5.2 Comparators are weak and learners are undertrained

- ACVC B01: the learned proposer C improves from J 0.135 to 0.147 over 4,096 episodes. Achievable
  J on this host family is ≳ 0.67. The "package" F is a fixed retrace heuristic. "F > C" at this
  point on the learning curve says the heuristic is better than an almost untrained policy.
- MGTAP: the learning rate 1e-4 was selected at episode 256 in a prior object and then found not
  to help at 512. The whole direction's evidence is at ≤ 512 episodes on a host where the
  reference needed 800k steps to reach coverage 0.9.
- FOLR: QMIX-family learner, 5,000 episodes on easy Traffic Junction; the Generic baseline
  itself is at return ≈ 1.6 with SD 7.2. Both arms are noisy and far from the task ceiling.
- Every direction's Oracle row (2026-09-12) records "no complete tuned-headroom record". The
  2026-09-04 guidance made headroom a *prerequisite*; the same-day revision after Codex Root's
  review made it "a diagnostic, never a reason to stop investing". That revision let twenty
  directions proceed without ever measuring whether their generic baseline was competent.

### 5.3 Bespoke hosts destroy comparability

Each direction constructed the environment in which its mechanism would be necessary. That
produces identifiability results ("the structured learner can use this information") rather than
value results ("this information matters on a task anyone cares about"). It also means there is
no shared learning curve, no common baseline, and no way to say whether a 0.01 J effect on ACVC's
cluster host is large or small. The July R35–R40 review had already concluded that "the project
must not select another convenient toy"; the September loop built 41 of them.

### 5.4 The decision loop is optimised for producing decisions

The audit ledger shows 78–219 decisions per day. Every decision is made by a language model
(the DM) whose recommendation is auto-selected under the unattended delegation of 2026-09-03,
then checked by another language model (Pro) that cannot see the code (Codex workflow review,
finding F1). Direction hypotheses and names ("expressibility-gated renewal credit relay",
"semantic graphon shared policy", "covariance-calibrated information clock") were generated from
the paper library by the same models. The record of consolidations (33 labels, then five
families, then nine routes, then five new registrations, then two slots) shows the selection
process oscillating rather than converging, because nothing in it is anchored to a measured
quantity on a fixed task.

The owner's own 2026-09-05 note put it precisely: "repeatedly proposing very expensive
verification and then stopping at a resource cap can be a methodology failure." The
2026-09-04 guidance said the pattern was "a selection problem, not an execution problem". Both
diagnoses were correct and neither changed the loop's structure; the loop absorbed them as more
rules.

### 5.5 What the methodology got right

- Insisting on a positive source anchor (R41B) before extending.
- Quarantining incomplete attempts and refusing post-hoc rescue of frozen results.
- Recording predictions before results and scoring them (ACVC's Brier sums are a good habit).
- Common random numbers for paired evaluation.
- Retaining every adverse world and refusing to erase earlier nulls.
- The vacuity lemma and the R21 actionability floor.
- The 2026-08-31 observation that five directions shared the same inference defect (small-block
  t-tests asked to carry population claims).

These are the parts to keep.

## 6. What was actually learned (defensible claims)

1. HMASD reproduces on Alice_and_Bob (win 0.89). Nothing else about HMASD has been established on
   any other host in this repository.
2. A recognised (state-function) team latent cannot be paid an identifiability reward; a sampled
   team latent is decorative unless its actionability is forced. (Vacuity lemma; R21.)
3. Convenient public toys (simple_spread, custom sparse Alice–Bob variants) are not accessible to
   the base learner under the frozen contracts; substrate search by convenience fails.
   (R35–R40.)
4. On several toys the "containing" generic learner matches the structured one when both are
   exact or near-exact (RCLE, EGRCR, CRTO, CBSC). At these scales the proposed inductive biases
   are not needed. This is a real, if narrow, negative.
5. On the UAV host, policy-based interruption of fixed-k skills (FSD, treatment I1280 vs D0) is
   positive in four of five independent pairs with mean ≈ +0.07 J. This is the single most
   promising empirical signal in the repository, it is on the original host and the original
   question, and it is the direction the Portfolio chose not to fund further.

## 7. Recommendations

Stated as decisions, with the reasoning above as justification.

**R1. Run the headroom experiment before anything else.** On scenario 1 (and the cluster
variant), train flat MAPPO, MAT and HMASD (fixed k = 10) for the same number of environment
steps as the standing reference, five seeds each, and publish learning curves with 95%
intervals. Three outcomes, each decisive: (a) HMASD ≫ MAPPO: the hierarchy premise holds, keep
the host; (b) HMASD ≈ MAPPO: the host does not need skills, either switch to a sparse-reward UAV
variant (reward only on full coverage events, or event-triggered service) or drop the hierarchy
and study k/N on MAPPO directly; (c) HMASD < MAPPO: the base implementation or tuning is wrong
and every downstream result is suspect. Cost: about fifteen runs of the reference length, on the
GPU node.

**R2. Choose one external benchmark per untying axis and freeze it.** For k: a host with a
latent hazard, either the relay corridor at λ = 0.02 or Alice_and_Bob with button/diamond
relocation at a fixed hazard; the success criterion is that fixed-k HMASD at its best k loses
measurably to the latent-aware oracle. For N: Overcooked or SMAC with scripted mid-episode agent
loss/arrival, or the UAV host with UAV failure/replacement; the criterion is that a fixed-N
learner measurably degrades. Retire every per-direction host. Do not admit a mechanism until the
necessity experiment on the frozen host shows the gap it is supposed to close.

**R3. Replace the inference rule.** Five independent training seeds per arm, learning curves,
and a minimum effect derived from the measured across-seed SD on that host (effect > 2 SD and
positive in ≥ 4/5 seeds to count as a signal; inside ±1 SD to count as null). Keep common random
numbers for evaluation. Abolish the fixed 0.01 J convention.

**R4. Cut to two directions and slow the cadence.** FSD (untie k) and one roster direction
(VNFC or FOLR, chosen after R2). One card per direction per week. The Pro nodes review; they do
not decide. The owner selects what runs. End the unattended object-tier delegation for direction
science; keep it for mechanical execution only.

**R5. Concrete first object for FSD.** Five seeds × {D0, I1280} on the scenario-1 host at three
times the current budget (240,000 training ticks), plus the MAPPO arm from R1 as the absolute
reference, with learning curves. Decision: mean I−D0 > 2 × across-seed SD. If it holds, repeat on
the hazard host from R2 to show the effect grows with hazard. That is the first result in this
programme that could be written up.

**R6. Archive, do not delete.** The 27 directions, 273 cards and evidence trees remain evidence.
Mark everything not covered by R4 as historical in `RESEARCH_MAP.md`; do not spend further
compute on closeouts, reviews or Pro rounds for parked directions.

## 8. Answers to the owner's three questions, briefly

*Were the original assumptions sound?* HMASD as a sparse-reward exploration method is sound and
reproduced. HMASD as the base for a dense-reward UAV task is untested. OPT as a recognition layer
under a sampled commitment was shown vacuous by the project's own lemma. "Untie k and N" are
reasonable long-term goals whose necessity was never demonstrated on any task.

*Was the methodology reasonable?* July over-formalised; September over-corrected into one-seed
decisions on bespoke toys at machine cadence. The good parts (anchors, quarantine, predictions,
CRN) should be kept; the inference rule, the host policy and the decision cadence should be
replaced.

*Are the conclusions drawn from the experiments justified?* The negatives on exact toys (RCLE,
EGRCR, CRTO, CBSC) are justified at their narrow scope. The parks of MGTAP, LCAC, DISH, UCOPE and
ACPS are not justified by their evidence; they are consistent with small positive effects. The
FSD positive is the only result with enough replication to be called a signal, and it is
under-powered rather than over-claimed.
