# HA-CTSE Research Briefing — for external LLM discussion (2026-07-04)

Self-contained: no file access is assumed. Prepared by CC (Claude,
cross-validation role) from the project's memory ledger. Numbers cited are
from logged runs.

## 1. Problem and benchmark

Cooperative multi-agent RL with sparse team reward. Benchmark: UAV
communication service (Scenario 7): ~6 UAVs must serve ground users AND
maintain a multi-hop relay/backhaul chain to base stations; reward is only
consistently available once a cooperative topology exists. S7-S1 is the
calibration scene (HMASD nearly solves it); S7-S3 is the hard motivating
scene (HMASD struggles).

Parity target: at ~1e6 env steps, at least half of evaluation primitive
steps reach coverage == 1.0, with low zero-service episode fraction and
acceptable variance. Reward-mean spikes do not count. 160k-320k local runs
are mechanism gates only, not comparison verdicts.

Hard boundary (non-negotiable): communication/backhaul/coverage fields are
DIAGNOSTICS. They never enter intrinsic rewards or discriminator inputs. The
algorithm must remain a general MARL method, not a UAV heuristic.

## 2. The two source papers

HMASD (Yang et al., NeurIPS 2023): two-level hierarchy. Every k steps a
transformer coordinator assigns a team skill Z and individual skills z_i
AUTOREGRESSIVELY (z_i | Z, z_{1:i-1}) — complementary assignment. Low level
pi_l(a_i | o_i, z_i). Dense intrinsic reward from two discriminators:
log q_D(Z|s) (team) + log q_d(z_i | o_i, Z) (individual), derived from a
variational lower bound (their Eq. 3: task reward + diversity terms + skill
entropy + action entropy). Their ablations show FOUR load-bearing parts:
team skill, individual skill, intrinsic discriminator reward (NoInRew
"can't work on most scenarios"), and the AR coordinator.

OPT (Liu et al., TPAMI 2024): interaction-pattern disentangling. Entity
attention is decomposed into N sparse prototypes (sparsemax), kept diverse
by a contrastive disagreement loss, and restructured by aggregation weights
omega into a compact interaction representation. It is a REPRESENTATION
module grounded by TD loss inside a QMIX-style stack; per-agent aggregation
weights exist in each agent's utility network, stabilized by a CMI loss.
OPT decides nothing; it recognizes.

## 3. The idea and its evolution (condensed round history)

v1 (HA-CTSE original): decouple per-agent skill LIFETIMES from the shared
check interval k (agents keep/edit skills asynchronously, or pick discrete
durations); use OPT compact c as context with a bridge g replacing Z;
rebuild HMASD's intrinsic pressure for variable-length process segments.
OUTCOME over many cycles: segment-level skill posteriors repeatedly failed
against shortcut baselines (duration/length/reward/context); g was
empirically decorative (interventions ~0 effect); cooperative recovery
credit stayed flat across every temporal/access knob.

Key diagnoses that reshaped the program:
- Duration co-selected with skill by one head = the shortcut engine ("the
  disentangling device is the entangling device").
- g was decorative because NOTHING IN ANY OBJECTIVE REQUIRED it to carry
  information (now generalized as the channel-pressure rule, §5).
- The program over-invested in the individual half (skill
  distinguishability) while HMASD's own ablations say the cooperative half
  (team skill + team discriminator + AR complementarity) is equally
  load-bearing — and HA-CTSE had structurally removed it.
- Category error: OPT's compact is a bottom-up DESCRIPTION of current
  interactions; HMASD's Z is a top-down COMMITMENT paid for by a
  discriminator on future states. Deriving g from OPT made it
  informationally redundant by construction.

v2 (Round 12, recognition-first reframing — user's original intent): the
category error is inverted into the design. OPT provides a continuously
RECOGNIZED situation (omega -> discrete slow class kappa). Skills become
RESPONSES to the situation. Decoupled lifetimes then FALL OUT: a skill
persists while its situation persists (validity hazard beta_i), rather than
being a committed duration. A pre-registered SUBSTRATE GATE was required
before building on this: G-DWELL (situation classes dwell vs block-shuffled
null), G-OUTCOME (early-window omega predicts episode success beyond a
simple-features baseline), G-ROLE (omega membership aligns with
counterfactual role labels). The gate PASSED on local 16-env checkpoints
(dwell margin ~0.24, outcome AUC 0.65-0.71 vs baseline 0.58, role MI above
threshold). A first naive mechanism — force renewal when global kappa
changes — FAILED (hurt stability), diagnosed as wrong event semantics plus
a structural issue (global kappa renews everyone: near-synchronized churn).

v3 (Round 14, prototype-basis design): decompose HMASD's high level into
five jobs: J1 abstraction, J2 selection, J3 commitment, J4 coordination,
J5 label supply for intrinsic reward. OPT natively covers J1 only. Design:
skills = PROTOTYPE-RESPONSE CODES (z_i in {1..N}, "respond to interaction
prototype n"); commitment = target in omega-space with validity-based
termination; coordination = omega-weighted set-coverage of active
prototypes; J5 splits (see v4). Staged build with gates; parallel track of
premise tests (recognition-Z control, HMASD current-env re-verification,
per-agent kappa, offline actionability gate).

v4 (Round 15, the Steering Objective — the paper-level core):

  VACUITY LEMMA: substitute recognized kappa = f(s) for sampled Z in
  HMASD's bound: H(kappa|s) = 0, so the team discriminator reward is
  trivially perfect from step one — ZERO policy gradient. The team
  identifiability reward CANNOT be transplanted under recognition, even in
  principle. (Corollary: its prior-corrected remnant degenerates to a
  count-based situation-novelty bonus — exploration survives, coordination
  dies.) Team pressure must therefore be FORWARD-LOOKING.

  THE OBJECTIVE:
    J = E[Sigma r_env]
      + lambda_ind  Sigma_{t,i} [ log q_d(z_i | o_i_{t+1}, kappa)
                                - log pi_h(z_i | kappa, z_{1:i-1}) ]
      + lambda_team Sigma_tau   [ log q(kappa' | kappa, xi)
                                - log q(kappa' | kappa) ]
      + entropy terms

  The individual term is a COORDINATOR-RESIDUAL reward: the null model is
  the sequential assignment policy itself. It is HMASD Eq. 3's diversity +
  skill-entropy pair FUSED pointwise (not a new bolt-on), and it supplies
  three things at once: identifiability pressure on the low level,
  assignment entropy on the high level, and anti-duplication (a response
  the coordinator predictably duplicates earns low reward). It is immune by
  construction to usage-imbalance (null = usage distribution) and duration
  shortcuts (per-step form, label = currently ACTIVE skill, which is
  well-defined under variable lifetimes). The team term is a DADS-style
  transition residual over situation space (xi = joint response profile).

v5 (Round 16, roster-docking — forced by measurement): the first run showed
the AR prefix diagnostic at exactly 0. A mechanical intervention test proved
wiring healthy. The measured cause: renewal_agents_mean = 1.44 of 6,
full_sync_rate = 0.0 — asynchronous renewal WORKS, and precisely because it
works, the same-check prefix z_{1:i-1} is empty for most renewals. HMASD's
sequential assignment presupposes synchronization; kept unmodified, it is
structurally starved by the very asynchrony the algorithm exists to create.
AMENDMENT: the prefix becomes the STANDING ROSTER — teammates' currently
active skills + skill ages. The sequence is over TIME (docking against a
persistent configuration), not over an agent list within one synchronized
instant. Full-sync renewal provably reduces roster mode to HMASD's original
AR (strict generalization). Diagnostics: KL vs zeroed roster (capability)
and KL vs SHUFFLED roster (coordination content — the binding one).

## 4. Current algorithm in one screen

```text
Encoder (OPT-style): state+obs -> sparsemax weights omega over N=4 learned
  prototypes -> compact c; per-agent relevance rel_i; discrete slow
  situation kappa (per-env now; per-agent kappa_i queued).
High level (per check interval k): for agents whose skill expired/renews,
  AR selection pi_h(z_i | omega, c, o_i, z_prev_i, prefix), where prefix ->
  roster of teammates' active skills+ages (Round 16). Skill = prototype-
  response code, n_skills = N. Duration from a discrete candidate set
  (legacy; hazard/validity termination is the design target, Stage 2).
Low level: pi_l(a_i | o_i, z_i) ONLY — no c/omega/kappa/g leaks (skill
  bottleneck invariant; the hierarchy collapses without it).
Intrinsic (Stage 1): coordinator-residual reward, low-level only,
  bootstrap-scale coef 0.1, warmup 20k, clip 2.0. Team transition term:
  Stage 4, after commitment (Stage 2) and coverage (Stage 3).
Training: two-level PPO, on-policy contract, renewal-time snapshots stored
  for logp consistency, EMA prototype bank for stable skill semantics.
```

## 5. Transferable key principles (hard-won)

1. CHANNEL-PRESSURE RULE: every latent channel ships either with a training
   pressure that requires it, or with an explicit "decorative until Stage X"
   label. Never gate on reward-off emergence. (Paid for twice: g, then the
   AR prefix.)
2. BOOTSTRAP vs SEMANTICS: HMASD's intrinsic reward is primarily a dense
   exploration bootstrap, only secondarily semantics. Residual-gating every
   intrinsic term to epistemic purity deletes the engine. Split the roles:
   crude-but-dense drive; validation as diagnostics.
3. VACUITY: identifiability rewards on any recognized (state-derived)
   latent are provably dead. Pressure on recognition-based designs must
   target the FUTURE (transitions, effects).
4. SHORTCUT DISCIPLINE: skill classifiers are eaten by duration / length /
   reward-sum / context / usage-imbalance shortcuts. Per-step active-skill
   labels + a null equal to the actual selection distribution kill most of
   them structurally rather than by gating.
5. SUBSTRATE GATES: before building on a learned representation, pre-register
   and test the properties the mechanism needs (dwell, outcome-relevance,
   role alignment, actionability) against nulls — and remember
   situation-ness can be TRAINED FOR, not just tested for (one retrain
   cycle cap to avoid probe loops).
6. CARDINALITY TRAPS: with N=4 skills and 6 agents, raw duplication is
   pigeonhole-forced (~0.76 by chance); anti-duplication must be judged as
   an EXCESS over an independence null with matched marginals.
7. SEQUENTIAL COORDINATION UNDER ASYNCHRONY = temporal docking against a
   standing configuration; instantaneous AR ordering is a synchronized-world
   special case.
8. PROCESS DISCIPLINE: one variable per run; pre-register gates AND stop
   rules before looking; seed 2 before any claim; timestamped log dirs;
   never conclude from reward_mean alone.

## 6. Engineering state (facts as of 2026-07-04)

Implemented and validated (unit tests + smoke + tiny trains):
- OPT-style encoder with prototypes/omega/compact; situation substrate
  (kappa, dwell tracking, debounce); substrate-gate exporter/analyzer.
- Prototype-response selection (AR-first) + per-step discriminator with
  coordinator-residual reward (R15-aligned; learned-prior variant kept only
  as labeled fallback ablation). Full metric plumbing (CSV/TB/console).
- Situation-hazard renewal controls (oracle_change + conservative guards).
- Legacy HMASD baseline path intact for comparisons.

Experiment results so far (local, 16 env, 320k, seed 1 unless noted):
- Substrate gate: PASS (omega and compact-cluster branches; compact-cluster
  dwell median 100 vs omega 8 — relevant for later per-agent kappa choice).
- R12-1a global-kappa-change renewal: FAIL (coverage 0.100 vs 0.137
  control; churn), reframed by the Round 16 structural finding.
- A0 control (legacy labels, n=4): weak, high-variance baseline
  (160k eval reward 31.8, coverage 0.145; 320k eval reward 26.3,
  zero-throughput 0.75).
- A1 probe (prototype-response + AR, reward OFF): guards clean, no
  collapse; classifier weakly above chance (acc 0.27-0.36 vs 0.25) —
  expected without force (HMASD NoInRew profile); ar_kl = 0 explained by
  prefix starvation (renewal_agents_mean 1.44/6), wiring proven healthy by
  init-time intervention test. A1 evals notably below A0 — the added
  architecture costs learning speed reward-off; A2 must be judged vs BOTH.
- proto_rel_dwell = 2.0 checks: per-agent relevance churns — flagged risk
  for Stage-2 validity hazard; per-agent kappa may need compact clustering.

In flight / queued (pre-registered with gates and stop rules):
- A2: coordinator-residual reward-pressure test (same-check prefix),
  outcome matrix decides Stage-1 exit.
- Roster implementation (4 guards incl. snapshot-logp unit test and
  full-sync reduction test) -> A2r, judged on roster_ar_kl_shuffled
  (>=0.02 / <0.01), selection_independence_deficit, task vs A2.
- HMASD-original ~1e6 baseline on CURRENT env (parity anchor; owed).
- Recognition-Z HMASD control (commitment-vs-context premise test).
- G-ACTIONABILITY offline gate (do kappa boundaries carry decision value).

Pre-registered stop rules exist at every level, up to: if roster + reward
still shows no coordination content across 2 seeds, sequential assignment
is dropped from the mainline and complementarity moves to coverage
pressure; if the fused reward fails separation in both quadrants, fall back
to the kappa-prior form, then to a faithful-HMASD anchor configuration.

## 7. Questions worth pressing (for the discussing models)

Q1. Commitment vs recognition: is the vacuity lemma airtight, and is the
    team transition residual really the UNIQUE surviving team pressure, or
    are there other forward-looking forms (e.g. reachability/empowerment
    over kappa) with better data efficiency? (The transition term trains
    only on kappa transitions; dwell length trades against sample count.)
Q2. Moving null: the coordinator-residual reward shrinks as pi_h sharpens.
    Feature (annealing) or fatal (self-extinction before separation)?
    What schedule or floor would you impose?
Q3. N=4 skills for 6 agents is coarse and pigeonhole-bound. Raise N (needs
    substrate re-gate), add composite codes, or accept coverage-style
    complementarity as the only meaningful coordination claim?
Q4. Does roster-docking preserve the complementarity guarantees that
    motivated HMASD's AR coordinator, or does conditioning on standing
    skills (vs simultaneous assignment) change the game-theoretic content?
Q5. Is S7-S1 the wrong scene to demand lifetime heterogeneity from (the
    project predicts collapse there is CORRECT), and what is the cleanest
    minimal environment where heterogeneous tempos are provably load-bearing?
Q6. The biggest unread premise: recognition-Z control (does HMASD's Z work
    because it is a commitment, or merely a shared context?). Any argument
    that settles this without the experiment?
