# Skill and teammate drift learning

## 2026-09-20 06:20 PDT — direction opened; primary-source reading and first comparison

**Ownership and adopted control.** Direction B is owned by Codex DM
`/root/dm_teammate_drift` under the independent FSD Root. Author checkout:
`/home/fires/.codex/worktrees/fsd-b/hmasd-wsl`, branch
`codex/skill-teammate-drift-learning`, initial HEAD `45945dd7f`. The 2026-09-20
constitution amendment is loaded and adopted: fits record cost, with no allowance,
refund, reset or six-fit cap. The old skill wording is superseded. The owner pause
is lifted. A/B/C are owner-selected; at this entry their active rows are published
only on the Root branch. Reading, design and isolated implementation proceed;
result execution waits for canonical integration and native admission. Root owns
that shared integration; this DM does not edit main or RESEARCH.

**Question and boundary.** With a fixed macro clock, when do actual changes in the
ego low-level controller and a teammate make old macro transitions unhelpful, and
does using the recorded joint behaviour improve high-level learning more than a
simple replay rule? No learned termination, skill discovery, current-PPO diagnosis
or change to Claude's coordinator is proposed. The first object uses an independent
fully observed two-agent host and scripted controller versions. Its finding will
concern exogenous joint behaviour drift, not endogenous co-learning or the utility
of present HMASD learned labels.

### Evidence already read and current explanation

The owner's supplied proposal was read in full. Exact-title queries of the available
Inst-sci catalog did not locate the two named starting papers; that is a retrieval
miss in this snapshot, not a novelty review. Primary originals were therefore read:

- Nachum et al., *Data-Efficient Hierarchical Reinforcement Learning*, NeurIPS 2018,
  [arXiv v4 PDF](https://arxiv.org/pdf/1805.08296), section 3.3, equation 5,
  pages 5–6, and appendix A, pages 12–13. HIRO relabels a past high-level goal to
  make its observed primitive actions likely under the current low-level policy.
  Its Gaussian case searches ten candidate goals; this is approximate relabelling.
  Appendix A describes trajectory importance ratios and reports poor practical
  performance from their high variance in the tested continuous-control domains.
  This motivates retaining behaviour records and a variance diagnostic; it is
  contrary evidence to expecting an importance-weighted method to work merely
  because the ratio is formally available. B01 below adapts known importance
  weighting, not HIRO's relabelling algorithm or a claimed new algorithm.
- Foerster et al., *Stabilising Experience Replay for Deep Multi-Agent Reinforcement
  Learning*, ICML 2017, [PMLR PDF](https://proceedings.mlr.press/v70/foerster17b/foerster17b.pdf),
  sections 4.1–4.2, pages 4–5, equation 4. Their fully observed construction weights
  replay using the current-to-collection probability of the other agents' actions.
  Under partial observability they explicitly call the analogous ratio an
  approximation because additional history-dependent terms remain. Their alternative
  conditions values on training iteration and exploration rate. This supports a
  fingerprint baseline and forbids extending a one-agent likelihood correction to
  an unqualified joint/POMDP correction claim.

The nearest local warning is the [FSD B07 interpretation](../flexible_skill_duration/NOTES.md#2026-09-20-0530-pdt--persistence-b07-read-redrawing-every-skill-every-step-changed-neither-behaviour-nor-attained-j-on-the-one-block-that-has-it-the-batch-is-closed-with-two-cells-missing):
changing label cadence tenfold did not establish a behavioural change; persistence
as the explanation of the observed learning advantage weakened. That is a reason
to make behaviour explicit in this independent object, not evidence of replay
failure in PPO. B08 source, operations and partial scores remain outside this task.
The [RCLE joint-quota reading](../roster_consistent_latent_exploration/RCLE_JOINT_QUOTA_PHASE_FAMILY_INTAKE_20260912.md#scientific-knowledge-support-contradiction-and-claim-ceiling)
also distinguishes fixed exogenous changes from teammate-learning nonstationarity;
that limitation carries into this design.

**Working explanation.** Joint drift can change the conditional macro transition
even with a fixed skill label and clock. Behaviour records can distinguish an old
compatible trajectory from a newer incompatible one; age cannot generally do so.
However, a competent fingerprint can already preserve useful old information, and
importance weights can spend most of their effective samples on a few trajectories.
The unresolved question is finite-learning value beyond these simple alternatives,
not mathematical availability of a correction. No native evidence for B exists yet.

### B01 prospective: joint trajectory weighting versus competent replay

**Host and intervention.** Two agents occupy a five-cell line, positions 0–4. At a
macro decision the ego chooses a left/right endpoint skill; the teammate independently
chooses its own endpoint once. Each fixed closed-loop skill attempts one cell toward
its endpoint per primitive tick and otherwise stalls; it holds at the endpoint.
Macro duration is always 3 ticks, and an episode is 10 macro decisions (30 ticks).
Reward after each move is half the number of distinct endpoints occupied: 0, .5 or 1.
Both positions and remaining macro decisions are public to the high-level actor;
the teammate's newly drawn goal is not revealed before the ego chooses. There is
no communication learning, recurrence, padding, changing roster or hidden simulator
state. Discount is .95 per primitive tick, with correctly discounted macro rewards
and continuation discount `.95 ** 3`; the last macro is terminal, not a truncation.

Controller versions are `A = (ego move probability .8, teammate right probability .8)`
and `B = (.6, .2)`; the teammate's primitive move probability stays .8. Versions are
held for 60 episodes in the fixed sequence A/B/A/B/A (300 episodes total). A version
is revealed only when current. Both low-level and teammate behaviour change; neither
is trained here. The reappearance of A/B makes compatibility distinct from recency.
At each reset both positions are sampled uniformly and independently. Actions have
full common support; at a target the only legal primitive action is hold with
probability 1. All arms can access current version parameters and historical
positions, actions, teammate goal, collection version and behaviour probabilities
at training. No arm gets future draws or future versions in its decisions.

**Arms, one candidate change.** All arms use the same finite-horizon tabular Q learner,
epsilon .2 at training, deterministic argmax with left tie-breaking at evaluation,
zero Q initialisation, one replay minibatch of 32 after every collected macro,
and learning rate .025. Terminal row Q[0] stays zero. A minibatch uses pre-update
targets and applies simultaneous updates, averaging contributions within each
visited Q entry. Replay samples with replacement. The complete buffer holds all
3,000 collected macro transitions; there is no tuning search.

1. `joint_is` (candidate): uniform full-buffer replay, multiplied by the full current/
   behaviour likelihood ratio of the recorded macro. This contains the teammate
   macro-goal factor and both agents' primitive conditional-action factors. The
   fixed teammate low-level factors cancel, but remain recorded and checked.
   Normalize weights by their minibatch mean; do not clip, relabel, synthesize
   trajectories or alter recorded rewards/next states. This self-normalized finite-
   sample update is biased; it is not an unbiased-loss theorem claim. The minibatch
   size and learning rate bound the largest individual normalized step by .8.
2. `fingerprint` (primary): full-buffer replay with separate value tables conditioned
   on the exact current/collection `(ego probability, teammate probability)` pair.
   Replay updates the table for the recorded version and bootstraps that same table.
   This is deliberately more informative than an age-only fingerprint and has twice
   the Q entries. It is a simple lawful baseline under this host's public version
   access; beating an age-only baseline would not justify ignoring it.
3. `recent`: uniform replay from the most recent 300 macros, otherwise the same
   unconditioned Q learner. This is a fixed 30-episode window, half a drift block.
4. `uniform`: unweighted uniform full-buffer replay, the exposure/scale control.

For `joint_is`, `recent` and `uniform`, the actor uses the current adaptive Q table;
for `fingerprint`, it selects the current version's table. Every arm is permitted
the same current version information; how it organizes its values differs. One
ego high-level learner is trained against a scripted changing teammate. The
experiment does not claim two independently learning high-level agents or component
causality for the fingerprint's capacity difference.

**Why the likelihood has the stated scope.** Conditional on the recorded starting
state and ego skill, a trajectory probability is the teammate goal probability
times both agents' per-tick action probabilities. The deterministic physical
transition rule is unchanged, so it cancels in the ratio. No correction of the
ego high-level sampling probability is needed for tabular off-policy Q learning.
This statement depends on full state, recorded actual actions, common support,
fixed segment length and unchanged physics. It would not survive hidden recurrent
state or an omitted changing teammate factor without additional work. We keep old
trajectories as factual samples with weights, never as counterfactual rollouts.

**Predictions and reading.** The mechanistic prediction is lower current-version
Bellman residual for `joint_is` than `uniform` just after a switch, accompanied by
nontrivial effective sample size and actual contribution from older data. Its
task prediction is higher native expected return than `recent` during those
adaptation windows. The stronger complete-package prediction is improvement over
`fingerprint`; this is uncertain, because exact reusable contexts may make the
simple baseline sufficient. We will not credit success against `uniform` alone
as a useful advance. In a stable version all ratios equal 1, so candidate and
uniform must be identical under the same random draws (a correctness invariant,
not a separate empirical claim about arbitrary stable MARL).

Evaluate the frozen greedy high-level policy every 10 episodes, including episode 0.
The primary endpoint is the mean native normalized discounted service return at
episodes 70/80/90, 130/140/150, 190/200/210 and 250/260/270: the first 30 episodes
after each switch. Report the final return and full curves as secondary, with no
checkpoint selection. The finite host permits exact dynamic-programming evaluation
over all 25 equally weighted reset states under the *current* version, with no
evaluation episodes or parameter updates. Only the evaluator knows the transition
model. Its optimal policy/value is an informational reference, not a tuned baseline
or a UAV headroom estimate. The native measure divides discounted service by
`sum(.95 ** t for t in range(30))`. Bellman residual is reported over all remaining-
time/state/action entries; the main endpoint remains service, not value error.

If weighting improves residual but not service, practical control value weakens.
If recent or fingerprint matches/beats it, the need for this added correction in
these conditions weakens. If weights collapse and learning fails, that is adverse
evidence about the finite-sample package, consistent with HIRO's warning, not proof
that old data is inherently unusable. A failure of `uniform` alone establishes no
advantage over competent replay. A positive result supports this small fully
observed scripted-drift host only; endogenous drift, partial observations, long
skills, unknown teammate likelihoods and UAV transfer remain unmeasured.

**Cost and stopping.** Twelve planned exploratory fits: four arms × independent
training seeds 91001/91002/91003. These are three common-random-number blocks, with
reset positions, teammate draws, primitive execution uniforms and exploration
draws addressed by episode/macro/tick; equal seed labels alone are not the pairing
justification. Every fit is 300 episodes, 3,000 macros, 9,000 primitive transitions,
3,000 tabular minibatch updates and 96,000 replay sample uses; 31 exact evaluation
panels. Total is 108,000 primitive transitions and 1,152,000 replay sample uses.
The small matrix evaluator is computed once per version and reused, not recursive
trajectory search. Planned node `local_linux`, CPU float64 NumPy, one sequential
fit at a time, single native numeric thread. No training of lower skills or teammate
is hidden in this cost. Actual wall time and process RSS are unknown until run and
will be reported. This fixed batch will not be extended after scores. Three seeds
permit per-seed descriptions but this development object is not confirmation; no
CLAIM file or significance verdict is implied. Technical attempts are retained and
counted separately from adverse scientific evidence.

### L0: bounded B01 implementation

Implement the above single replay comparison under
`experiments/candidates/skill_teammate_drift_learning/joint_replay_b01/` with tests
mirroring it under `tests/experiments/candidates/skill_teammate_drift_learning/`.
The DM owns `scripts/run_stdl_joint_replay_b01.py` and this notebook. No shared
learner/environment, Claude path, main or index is changed. The scientific module
exports `Config`, `run_fit(config, *, arm, seed)` returning `summary`, `curves`,
`transitions` (plain NumPy arrays) and `q_values`; the DM adds the admitted CLI and
artifact publication. A bounded Implementer may edit only module/tests, with no
index, commit, notebook or runner writes; the DM alone stages and accepts.

Preserve fixed clocks, version schedule, information rights, simultaneous tabular
updates, explicit terminal bootstrap and independent evaluation. Test analytic
probabilities/ratio support (including a teammate-only change), stable-weight
identity, no-op probability 1, native reward, finite-horizon boundaries, replay
scope, actual learner movement/counts and deterministic exact evaluation. Scratch
uses pytest-owned `temp/` paths. Tiny fixture fits are engineering checks, do not
answer the prospective learning question, and must not output scientific scores
as evidence. No production test/bypass flag is allowed. The CLI must call
`require_admission` before environment, model, output or result effects and require
its explicit launch SHA to match admission. Retain config/SHA/status, all curves,
raw macro trajectories, learned Q values, per-panel policies and weight/ESS/age/
version diagnostics. Write technical failures without erasing partial outputs.
Independent high-risk review is required for trajectory weighting, training/eval
semantics and admission/publication before accepting this implementation. Stop
only the dependent action for a real conflict; no result execution before Root's
canonical-index coordination and normal admission.

## 2026-09-20 06:34 PDT — prospective baseline strengthening before implementation/results

On inspecting the small tabular setting, full-buffer sampling for a separate-table
fingerprint would spend current adaptation updates on an unrelated version's
table. A simple same-information baseline can do better without a new inference
method: sample uniformly from **all recorded macros matching the current behaviour
version**, retaining that version's Q table between visits. The current version has
at least the just-collected macro when replay starts, so the subset is never empty.

B01's `fingerprint` arm therefore uses this version-matched replay selection in
addition to its existing exact behavioural context. Old compatible samples remain
available without any age cutoff, and all 3,000 minibatches update the current
table. Everything else, including four arms, seeds, horizon, endpoints and costs,
stays as prospectively stated. This is a stronger behavioural-fingerprint baseline,
not a reproduction of Foerster's neural fingerprint implementation. It makes the
candidate's incremental question sharper: is off-version data worth correcting
beyond retaining all on-version experience and its learned table? This refinement
was made from the algorithm's state/update structure before any learning score or
result launch, not to respond to observed performance.

Clock clarification: the preceding draft heading's `06:34` was a clerical time
label; the entry was already present at the tool-observed 06:27:56 PDT. Its
scientific specification is unchanged. No result fit has started.

## 2026-09-20 06:36 PDT — B01 implementation self-check; independent review next

The bounded Implementer returned `joint_replay_b01/study.py`, its package entry,
and scientific tests without index/notebook writes. The DM read the complete
implementation and its later changed portions, adopted the strengthened
version-matched fingerprint, and owns the admitted CLI/publication code. During
self-check, the DM required cached immutable per-version matrices, an explicit
optimal informational reference, and reporting zero learner movement as an
observation rather than automatically calling it technical failure. No scientific
arm, horizon or endpoint changed.

The combined focused command was
`/home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q tests/experiments/candidates/skill_teammate_drift_learning/joint_replay_b01 tests/scripts/test_run_stdl_joint_replay_b01.py`:
**15 passed in 0.22 s**. This includes actual-action support and joint likelihood
factors, independent branch enumeration of the physical macro model, global
minibatch normalization, simultaneous/terminal updates, matched-version replay,
stable candidate/uniform bit identity, counts and movement, admission/SHA refusal,
real non-admitted CLI refusal, and output/failure retention. The tiny fixed-fixture
learner calls establish code properties only; their scores are not scientific
evidence and no production/default fit ran.

The saved `effective_sample_size` diagnostic is Kish weight concentration over
replay draws. Repeated draws and sequential updates are dependent; it is neither
the number of independent trajectories nor a replacement for the three independent
training blocks. Raw replay indices, weights, versions and ages are retained so
concentration and actual old-data use can be read together.

The implementation is being published for independent high-risk numerical and
admission review, not yet accepted for result execution. Scientific judgment is
unchanged/unresolved: this is a concrete test of whether off-version data adds
finite-learning value beyond a strong exact-context baseline. The pending shared
dependency remains canonical active/lead integration by Root; no result request,
native process handle or consumed scientific fit exists.

## 2026-09-20 06:40 PDT — B01 implementation accepted; scientific result still unrun

Published implementation commit: `fa4fb2cfed3724cdf517103fa8d036966fdaf2e4`, branch
`codex/skill-teammate-drift-learning`. Independent read-only Reviewer
`/root/dm_teammate_drift/review_joint_replay` read the complete changed numerical,
collection, replay, evaluator and runner paths against this contract, ran the 15
focused checks and whitespace check, and returned **no material finding / no repair
requested**. Its scope did not include a successful native admission or production
fit. The reviewer also identified the existing coverage limit: stable candidate
learning had an end-to-end fixture, whereas drifted likelihood composition had
component tests and static tracing.

The DM closed that test coverage gap with a tiny A/B/A candidate fixture. An
independent calculation from recorded actual actions and controller parameters
reconstructs every raw joint likelihood ratio and global normalization across
drift; it does not call the candidate likelihood helper. The scientific executable
bytes are unchanged from the reviewed commit. Combined check now: **16 passed in
0.23 s**, `git diff --check` clean. These checks establish implementation properties,
not a native learning comparison. The DM accepts the implementation and its revised
primary baseline; review advice itself is not empirical scientific evidence.

**Boundary.** Direction remains exploring, with one prospective B01 and zero
started production fits. There is no scientific result to read, and the judgment
about corrected off-version replay versus strong exact-context replay remains
unresolved. No baseline superiority, co-learning, current-HMASD skill utility or
UAV claim follows from the source or tests. The concrete next observation is the
predeclared 12-fit local-CPU batch and its full curves/diagnostics. Its current
dependency is Root's shared-writer coordination and canonical active/lead index
integration, followed by the existing actual-node admission. There is no duplicate
request, live run handle, periodic watcher or owner science approval to invent.

## 2026-09-20 — canonical activation and first pre-training admission refusal

Root reported the owner's explicit continuing experiment authority and canonical
integration. Direct readback verified both published main and the actual control
checkout `/home/fires/hmasd-wsl` at `b254ed1ea86cf8c39d925d87ded4fee368c5e0a1`,
pause lifted, B exploring with lead `Codex DM`. The relevant constitution, compute
configuration, methods and admission code are unchanged from the loaded controls.
Published B source `167da1073f95fd35b01b3418f9ea84db60e3040a` also matched readback.

At 13:48:24 UTC the DM submitted the first cell, `joint_is` / 91001, through the
native local_linux snapshot launcher. It exited 4 before training with:
`runner must contain exactly one require_admission(__file__, direction='skill_teammate_drift_learning') call before it can be spawned`.
The runner used the same-valued `DIRECTION` constant; the launcher's static AST
contract accepts only a literal. This is a reproduced launch-compatibility defect,
not adverse scientific evidence. Inspection found no B operation claim and no
output directory. Source ordering confirms this refusal preceded claim creation,
output creation and runner spawn. A retained source snapshot may exist and is not
deleted. Started production fits remain **0**. Exact failed-launch wall was not
instrumented; request and refusal inspection fell within 13:48:24–13:48:59 UTC,
which includes interaction time and is not a measured process duration.

The repair replaces only the call's direction argument with the required literal
and adds a regression invoking the actual static validator on this runner.
Seven runner tests passed (DM .24 s; independent Reviewer .21 s). The same Reviewer
returned no material finding, confirmed the refusal-before-effects ordering and
that `study.py` is unchanged. DM accepts this compatibility repair. The next native
request will use the published repaired SHA and the still-uncreated first-cell
output tag. No accepted operation is rebound or duplicated. All scientific arms,
seeds, horizon, endpoints and the twelve-fit batch are unchanged; no extra owner
or Root permission is needed for these ordinary steps.

## 2026-09-20 07:07 PDT — B01 read: active correction, no benefit over recent replay

**Execution and retained evidence.** The fixed twelve-fit batch is complete at
`d97b26c70b88d1b899148f3ee9acce14bf1822d6`: every native process exited 0 and every
scientific summary is complete. The DM retained each accepted handle until its
same-operation terminal record, launching its own fits serially. There was no
training failure, retry, added seed or score-conditioned change. The earlier
pre-training compatibility refusal remains separately recorded above. All outputs,
including raw trajectories, replay draws/weights, Q arrays, per-panel policies and
native manifests, are retained in Git under `runs/skill_teammate_drift_learning/`.
Each score below links its native manifest; `summary.json`, `curves.json`,
`transitions.npz` and `q_values.npy` are siblings.

Primary normalized-service adaptation endpoint (the twelve predeclared panels):

| Seed | joint_is | fingerprint | recent | uniform |
| --- | ---: | ---: | ---: | ---: |
| 91001 | [.609685](../../../../runs/skill_teammate_drift_learning/b01_joint_is_91001/launch-manifest.json) | [.600465](../../../../runs/skill_teammate_drift_learning/b01_fingerprint_91001/launch-manifest.json) | [.611987](../../../../runs/skill_teammate_drift_learning/b01_recent_91001/launch-manifest.json) | [.610273](../../../../runs/skill_teammate_drift_learning/b01_uniform_91001/launch-manifest.json) |
| 91002 | [.602737](../../../../runs/skill_teammate_drift_learning/b01_joint_is_91002/launch-manifest.json) | [.590282](../../../../runs/skill_teammate_drift_learning/b01_fingerprint_91002/launch-manifest.json) | [.617788](../../../../runs/skill_teammate_drift_learning/b01_recent_91002/launch-manifest.json) | [.591958](../../../../runs/skill_teammate_drift_learning/b01_uniform_91002/launch-manifest.json) |
| 91003 | [.596615](../../../../runs/skill_teammate_drift_learning/b01_joint_is_91003/launch-manifest.json) | [.595648](../../../../runs/skill_teammate_drift_learning/b01_fingerprint_91003/launch-manifest.json) | [.591326](../../../../runs/skill_teammate_drift_learning/b01_recent_91003/launch-manifest.json) | [.586429](../../../../runs/skill_teammate_drift_learning/b01_uniform_91003/launch-manifest.json) |
| Mean | .603012 | .595465 | .607034 | .596220 |

Paired joint-minus-fingerprint values are +.00922031 / +.01245509 / +.00096720
(mean +.00754753); joint-minus-recent are -.00230173 / -.01505165 / +.00528857
(mean -.00402160); joint-minus-uniform are -.00058761 / +.01077840 / +.01018608
(mean +.00679229). These are three independent development blocks, not a stable
ranking, an equivalence reading, or confirmation. The primary fingerprint contrast
is retained even though recent has the higher mean; the comparator is not changed
after observing scores.

**Actual learning and implementation checks.** Every fit records 300 episodes,
3,000 macro transitions, 9,000 primitive transitions, 3,000 minibatch updates,
96,000 replay uses and 31 exact frozen-policy panels (zero simulated evaluation
episodes or evaluation updates). Direct recomputation from the saved twelve panels
matches every emitted primary endpoint. Q movement is substantial, not absent;
terminal rows remain zero. Read-only raw-array reconstruction checks actual
positions/actions, endpoint service, discounted macro rewards, terminal/remaining
time, causal replay indices, the recent window and fingerprint version matching.
The five exogenous reset/exploration/teammate/primitive random-slot arrays match
bit-for-bit across all four arms within each seed. A separate vector calculation
from actual recorded actions reproduces all twelve behavior-likelihood streams and
all 288,000 candidate replay ratios/normalizations, without calling the scientific
likelihood helper. These checks found no scientific implementation defect.

**Predictions and contrary evidence.** Candidate mean absolute Bellman residual at
the primary panels is 2.1513 / 2.2856 / 2.3249 versus uniform 2.3049 / 2.4159 /
2.5285. This predicted intermediate change occurs on all three blocks. Candidate
Kish concentration divided by replay-draw count is about .419 on each block;
about .764 / .774 / .777 of normalized weight comes from outside the 300-macro
recent window, and only .445 / .424 / .437 from the current behavior version.
Maximum normalized single-draw weights are 13.45 / 19.49 / 14.08. Correction and
old/off-version use are active and not an age-filter alias. The residual gain does
**not** establish useful control improvement: the pre-result prediction of better
native adaptation than recent fails on two blocks and in the mean. Nor does
weight concentration by itself establish independent sample efficiency.

The sharper limitation is common poor B-version learning. Across arms the early
B windows are roughly .46–.49, while the runner's informational optimum for B is
.746564. Initial all-LEFT in A already yields .763942 versus the A informational
optimum .765398; final A values are roughly .726–.755. This is not a tuned-baseline
headroom estimate. It also does not mean no parameter learning occurred. Saved
policies favor LEFT strongly: fingerprint's last B panels choose RIGHT on only
4.8% / 2.8% / 6.0% of the 250 nonterminal state/time cells, and 291 / 291 / 288 of
its 500 B action values are still exactly zero. In each 60-episode B block only
26–37 state/time cells across the twelve fits observe both actions (out of 250);
RIGHT collection is about 11%–22%, not balanced exploration. Low RIGHT frequency
alone is not proof that every state should choose RIGHT. Together with the native
B underperformance and exact zero values, it supports testing a coverage/initial
value bottleneck before treating fingerprint as competent.

**Judgment and next useful observation.** The complete B01 correction package is
not retained as superior and is not advanced to confirmation. The ability to form
lawful, active joint weights is strengthened; incremental finite-learning value
beyond simple replay is weakened/unresolved. The positive fingerprint contrast is
not a matched-competent-baseline gap. A new, post-result hypothesis is that
pessimistic zero initialization under nonnegative reward, LEFT tie-breaking and
sparse epsilon exploration locks in an early action. This is an inference to test,
not an identified causal explanation. The next comparison should repair this
common learner issue with a single information-fair change and predict both
coverage/behavioral movement and B-native performance. It must preserve the replay
correction, clocks, task and B01 reading. An independent bounded ResearchCritic is
checking that inference while the DM audits the raw evidence; its advice is not
empirical replication. No UAV, endogenous teammate-learning, current-HMASD skill
or Claude-PPO diagnosis follows from this scripted host.

**Cost.** Twelve started/completed fits, 108,000 primitive transitions and 1,152,000
replay uses. Runner wall seconds, ordered joint/fingerprint/recent/uniform per seed:
91001 = 1.094 / .751 / .774 / .731; 91002 = .946 / .799 / .722 / .864;
91003 = 1.138 / .951 / .711 / .733. Sum runner wall 10.2134 s and CPU user+system
9.0470 s. Maximum single-scientific-process peak RSS is 44,872 KiB, not a sum or
simultaneous node peak. Numeric libraries use one thread; own fits were serial on
`local_linux` on the shared WSL host. First native acceptance to last process exit
is 369.349 s, including admission and interaction gaps, not occupancy or a speed
claim. External launch/preparation time is not fully instrumented and is not zero.
The earlier pre-training refusal's process wall remains unknown. Fits are cost,
not an allowance to exhaust or replenish.

### B01 reading refinement from independent criticism (same boundary)

The bounded critic separated the already-declared panels by current version; the
DM independently recomputed its numbers from saved curves. Joint-minus-fingerprint
on the A portions is +.007102 / +.030751 / +.019316; on the B portions it is
+.011339 / -.005840 / -.017382. Thus the all-positive combined primary contrasts
do not show replicated adaptation improvement in B: preserving performance in A,
where initial LEFT is already near its informational optimum, drives much of the
combined observation. This is a post-result diagnostic, not a replacement primary
endpoint. The initial all-state A Bellman residual is 1.305712, below the trained
A residuals; improvement versus uniform is only relative, not evidence of an
absolute fitted solution. DM adopts both limits. They strengthen the decision not
to promote B01's small positive fingerprint contrast as useful replay benefit.

## 2026-09-20 07:13 PDT — B02 prospective common-initialization repair

**Reason and adviser response.** B01 is closed/read, with all raw outcomes published
at `f830125994bb0e5f8b57ddabf5ae3026a290b7da`. Its sparse action coverage, unchanged
zero values and poor B-native behavior motivate one targeted common-learner
revision, not an extension of that batch or a renamed correction. The independent
ResearchCritic read the evidence and endorsed this minimal intervention/control
with no material dissent. The DM adopts its central limitation: an initialization
contrast can identify the total effect on both coverage and return, but cannot
establish coverage as the causal mediator because bootstrap and action ordering
also change. The critic also noted policy-table changes can leave native return
unchanged; therefore actual collected actions and native B scores remain beside
table-wide counts. Adviser agreement is not new empirical evidence.

**One change.** Replace pessimistic zero Q initialization with the known reward
upper bound `U(h) = sum(gamma**t for t in range(3*h))` for every nonterminal
state/action with `h` macro decisions remaining. Initialize once at fit start;
`Q(0)=0`, LEFT ties remain, and no table is reinitialized on a version switch.
Fingerprint initializes both version tables identically and retains each. The
bound uses only shared reward range [0,1], discount and fixed duration, not the
transition model, future data, current teammate draw or exact optimal policy.
The joint correction, per-entry update law, full buffers, exact behavioral
fingerprint, recent window, actor information and evaluation all stay unchanged.
This is a common exploration/value-initialization repair, not an extra replay
correction, relabeling or age filter.

**Arms and comparisons.** Five arm labels in this fixed batch:
`joint_is`, `fingerprint`, `recent`, `uniform` all with reward-upper initialization;
`fingerprint_zero` with B01's original zero initialization and otherwise identical
fingerprint learner. The primary replay contrast remains joint-minus-fingerprint
at the same twelve adaptation panels as B01. Recent is a required strong
same-information competitor because it had the best B01 mean; a positive
fingerprint contrast alone is not enough to retain a useful package if recent
still wins. Uniform retains the active-correction comparison. The paired
fingerprint-minus-fingerprint_zero contrast is the initialization diagnostic,
not a candidate modification selected by its score. It does not estimate the
candidate's initialization treatment effect; new-vs-B01 seed comparisons are only
descriptive. This design is outcome-informed exploration, not confirmation.

**Predictions and reading.** Relative to paired fingerprint_zero, optimistic
fingerprint should collect more alternative actions / visit more state-time cells
with both actions, then improve B-native service. Track the six B adaptation
panels (70/80/90/190/200/210) separately, with A adaptation panels as the retained
native cost. Also read collected RIGHT fractions for each B block, cumulative
current-version distinct state-action/both-action coverage at every panel, greedy
RIGHT fraction and Q movement from the actual initial table. Coverage is a
diagnostic, never a surrogate success criterion. The replay hypothesis remains
lower current residual versus optimistic uniform plus higher native adaptation
than simple replay; weight concentration and off-version/old-data use stay visible.

If coverage and B return both improve while A is retained/recovered, keep the
initialization repair and strengthen its practical-use judgment, without claiming
mediation or a unique explanation. If coverage rises without native B benefit,
weaken the claim that sparse exploration adequately explains B01. If B improves
without coverage movement, credit the initialization intervention but weaken the
coverage story. If neither improves, reject this repair at this horizon; do not
call that proof of intrinsically unusable macro experience. If a simple replay
baseline matches/beats correction after this common repair, lower the value of
explicit correction in this recurrent, known-version host. Negative A consequences
remain in the combined primary and are not hidden by the B diagnostic. No
post-result checkpoint/arm selection or batch extension is allowed.

**Fixed exposure and cost.** Fifteen planned fits = five arms × three new independent
development seeds 92001/92002/92003. The same event-addressed common random numbers
pair arms within a seed. Every fit retains B01's 300 episodes / A-B-A-B-A blocks of
60 / 3,000 macros / 9,000 primitive transitions / 3,000 minibatch updates /
96,000 replay uses / 31 exact evaluation panels. The twelve primary panels,
epsilon .2, alpha .025, batch 32, gamma .95 and recent capacity 300 are unchanged.
Total planned work: 135,000 primitive transitions, 1,440,000 replay uses, 465 exact
panels; zero sampled evaluation episodes/updates. No hidden lower-level training,
warm start from a learned B01 table or model-based learning is introduced. Expected
single-process runner work is on B01's roughly one-second scale, but actual costs
will be measured; this is not a deadline or performance claim. Planned node
`local_linux`, CPU float64 NumPy, one numeric thread and own fits serial on shared
WSL. The extra three zero-FP fits are justified by within-batch initialization
attribution, not by a generic quota. No claim note or confirmation rule is implied.

### L0: implement B02 without changing the frozen B01 result

Reuse the direction's B01 scientific module for an optional initialization mode,
defaulting to zero. Add the named B02 runner
`scripts/run_stdl_joint_replay_b02.py` and its focused tests, restricting its CLI to
these five arms/three seeds and its frozen configuration. Scientific source and
test ownership for a bounded Implementer is only
`experiments/candidates/skill_teammate_drift_learning/joint_replay_b01/` and mirrored
`tests/experiments/candidates/skill_teammate_drift_learning/joint_replay_b01/` in
the fsd-b checkout; the DM owns runner/tests, notebook, index and all Git actions.
Other authors are active; nobody edits their paths or reverts their changes.

The optional initialization must use actual finite remaining time, handle gamma=1,
keep terminal zero and leave default numerical/RNG/training semantics unchanged.
Movement in curves/summary must be `Q-Q_initial`, not norm(Q); retain initial norm,
and do not call initialized nonzero entries evidence of learning. Expose an
explicit optional object name for the B02 summary identity (B01 default retained).
Add diagnostic coverage derived solely from collected arrays, including current
version sample count/RIGHT fraction, distinct state-actions, both-action cells,
greedy RIGHT fraction and changed entries relative to initialization. Use safe
integer widths for state keys. Do not change likelihoods, updates, evaluation
numerics, buffers, seed addressing, reward, clocks or terminal rules. Retain raw
arrays/policies/Q and existing publication/admission semantics. Check the bound,
fingerprint table independence/no reset, truthful movement and coverage, stable
candidate/uniform identity with optimism, default behavior and B02 CLI refusal /
identity / output retention. Tiny fixtures are engineering checks only. Obtain
independent high-risk review of the changed initialization/instrumentation and
runner, then DM accepts, commits/publishes and performs native admission before
any B02 result fit. Stop only dependent work for a real conflict.

### B02 implementation self-check; independent review next

The Implementer returned only its two assigned scientific/test files, without
index or notebook writes; the DM read the full diff and owns the new runner and
runner tests. The new mode initializes once from the finite reward bound, records
movement from a copied actual initial table, retains separate fingerprint tables,
and derives coverage from already collected arrays. The B02 CLI fixes the five
arm mappings/three seeds, uses the native literal admission guard before science,
and records replay arm separately from the `fingerprint_zero` study-arm label.
Its A/B adaptation diagnostics do not replace the common primary endpoint.

Combined focused command:
`/home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q tests/experiments/candidates/skill_teammate_drift_learning/joint_replay_b01 tests/scripts/test_run_stdl_joint_replay_b01.py tests/scripts/test_run_stdl_joint_replay_b02.py`
returned **33 passed in 0.36 s**, with `git diff --check` clean. Checks cover bound
arithmetic including gamma=1, independent/persistent fingerprint tables, truthful
initial-relative movement, tuple-based coverage reconstruction, stable optimistic
joint/uniform identity, default-zero behavior, native static/missing-admission
refusal, SHA/seed/arm identity and output/failure retention. These are correctness
fixtures, not B02 scientific evidence. B02 production fits started: **0**.
Publication is for independent high-risk review; scientific acceptance/launch
awaits the DM's reading of that review, not a new owner or Root authorization.

### B02 implementation accepted for the declared batch

Independent read-only Reviewer `/root/dm_teammate_drift/review_joint_replay` reviewed
published `37ceaeb993039a1248a0359f72b92e6dea318faf` against the B01 result commit,
returned **no material finding / no repair requested**, and independently ran the
33 focused tests (0.34 s) and whitespace check. It checked the one-time reward bound,
independent fingerprint tables, no model leakage, initial-relative movement,
current-version coverage, preserved replay/numerics, frozen runner mapping,
literal admission guard and retained outputs. Review did not perform a production
fit or successful native admission, and default-preservation evidence in that
review is static tracing rather than cross-revision runtime equivalence.
The DM accepts the changed code after reading that review and the implementation.

Fresh readback found published main and the actual canonical control checkout at
`6ee15d7dda2a82688f60e25ae225c030ab8a6043`; its pause/direction index, constitution,
compute configuration and both affected methods are byte-unchanged from the
previously adopted canonical controls. The no-allowance cost regime and B's active
Codex DM assignment remain adopted. Next is the fixed fifteen-fit B02 batch through
native local_linux admission. No result has yet been read, and no scientific
prediction or budget is changed by review acceptance.

## 2026-09-20 07:31 PDT — B02 read: initialization matters; joint correction not retained

**Execution and validity.** The full declared fifteen-fit batch completed at
`3ac44381f093748ffe57f3da87fcb1ac201943ed`, with fifteen native exit-0 witnesses,
complete summaries and consistent same-operation identities. There was no refused
B02 admission, training failure, duplicate, retry, missing cell or mid-batch
scientific change. The DM held every observer through terminal readback, then read
the entire batch. All native records, configurations, curves/policies, replay
trajectories/weights and final Q arrays are retained in Git. The primary scores
below link each native manifest; the scientific files are in the same directory.

| Seed | joint_is | fingerprint | recent | uniform | fingerprint_zero |
| --- | ---: | ---: | ---: | ---: | ---: |
| 92001 | [.591040](../../../../runs/skill_teammate_drift_learning/b02_joint_is_92001/launch-manifest.json) | [.646963](../../../../runs/skill_teammate_drift_learning/b02_fingerprint_92001/launch-manifest.json) | [.596169](../../../../runs/skill_teammate_drift_learning/b02_recent_92001/launch-manifest.json) | [.649188](../../../../runs/skill_teammate_drift_learning/b02_uniform_92001/launch-manifest.json) | [.608502](../../../../runs/skill_teammate_drift_learning/b02_fingerprint_zero_92001/launch-manifest.json) |
| 92002 | [.619018](../../../../runs/skill_teammate_drift_learning/b02_joint_is_92002/launch-manifest.json) | [.653075](../../../../runs/skill_teammate_drift_learning/b02_fingerprint_92002/launch-manifest.json) | [.609529](../../../../runs/skill_teammate_drift_learning/b02_recent_92002/launch-manifest.json) | [.658481](../../../../runs/skill_teammate_drift_learning/b02_uniform_92002/launch-manifest.json) | [.614882](../../../../runs/skill_teammate_drift_learning/b02_fingerprint_zero_92002/launch-manifest.json) |
| 92003 | [.611206](../../../../runs/skill_teammate_drift_learning/b02_joint_is_92003/launch-manifest.json) | [.658984](../../../../runs/skill_teammate_drift_learning/b02_fingerprint_92003/launch-manifest.json) | [.606526](../../../../runs/skill_teammate_drift_learning/b02_recent_92003/launch-manifest.json) | [.648152](../../../../runs/skill_teammate_drift_learning/b02_uniform_92003/launch-manifest.json) | [.610819](../../../../runs/skill_teammate_drift_learning/b02_fingerprint_zero_92003/launch-manifest.json) |
| Mean | .607088 | .653007 | .604075 | .651941 | .611401 |

The fixed joint-minus-fingerprint primary differences are **-.05592306 /
-.03405732 / -.04777791** (mean **-.04591943**). Joint-minus-uniform is -.05814847 /
-.03946323 / -.03694680 (mean -.04485283); joint-minus-recent is -.00512907 /
+.00948878 / +.00467938 (mean +.00301303). Candidate loses to both fingerprint and
ordinary whole-buffer replay in all three development blocks, while its contrast
with recent is mixed. Ordinary replay and fingerprint themselves are mixed across
seeds; their close means are not an equivalence result or proof that context is
unnecessary. No arm/checkpoint was selected to replace the primary.

**The targeted repair has a real native effect, with a cost.** The paired
optimistic-minus-zero fingerprint contrasts are:

| Seed | Combined primary | B adaptation | A adaptation | B both-action cells at episode 90, optimistic / zero |
| --- | ---: | ---: | ---: | ---: |
| 92001 | +.038461 | +.131469 | -.054547 | 60 / 13 |
| 92002 | +.038193 | +.145381 | -.068996 | 53 / 15 |
| 92003 | +.048165 | +.138371 | -.042041 | 69 / 9 |

Mean B benefit is +.138407, A cost -.055195 and combined benefit +.041606. Thus the
prediction of greater coverage and better B-native learning occurs on all three
paired blocks; the stronger hope of retaining/recovering A without a cost does
not. At episode 210 the cumulative B both-action counts are 124/115/115 versus
34/31/37. First-B-block collected RIGHT fractions are .652/.598/.642 versus
.178/.122/.092; second-B-block fractions are .800/.817/.817 versus .180/.148/.092.
This is changed collected behavior, not merely more initialized nonzero entries.
At the last B evaluation optimistic fingerprint yields .708314/.701563/.733195
versus zero fingerprint .482951/.477877/.493369; the informational B optimum is
.746564, not a tuned achievable headroom estimate. Final A changes are mixed
and negative on two blocks (+.005517/-.030619/-.030914).

The paired intervention supports a useful initialization **total effect** on this
combined endpoint and a much stronger B-learning reference. It is compatible with
B01's action-lock-in explanation, but does not isolate coverage as the mediator
or make this a fully tuned/optimal baseline. Retain this preparation only with its
A adaptation cost, not as an unqualified improvement. The correction arm has no
paired zero control in B02, so its initialization treatment effect is not inferred
by subtracting the different-seed B01 results.

**Correction predictions fail after the common repair.** Candidate's primary
mean absolute current Bellman residual is 1.27114 / 1.30471 / 1.28172 versus
ordinary replay 1.20894 / 1.21087 / 1.19190: the predicted improvement reverses
sign on all three blocks. Candidate is also worse than fingerprint on each seed's
B adaptation component (-.014976/-.014355/-.049227), not just the A component.
Candidate residual remains below fingerprint's, but that proxy does not override
the latter's better native result. Correction is active: Kish concentration/draw
count is .4031/.3972/.4014; .7730/.7629/.7834 of weight is outside the recent window,
only .4324/.4345/.4447 is from the current version, and maximum normalized draw
weights are 17.04/14.69/20.02. These observations neither identify weight variance
as the sole cause nor justify claiming a correct conditional ratio must improve
finite bootstrapped control. The uniform contrast uses the same representation,
initialization, sampling scope and update count, so fingerprint's separate tables
are not sufficient to explain the candidate's adverse package comparisons.

**Raw evidence and counts.** Every fit executed the declared 300 episodes, 3,000
macros, 9,000 primitive transitions, 3,000 minibatch updates, 96,000 replay uses
and 31 exact evaluation panels, with no evaluation updates. The DM recomputed
each combined/A/B endpoint from saved curves. A read-only independent calculation
reconstructed all fifteen actual-action behavior likelihood streams and 288,000
candidate replay ratios/normalizations; physical positions/rewards, terminal
semantics, replay causality and baseline eligibility pass. All five arms share
the exact saved exogenous random slots within each seed. All 465 current-version
coverage panels agree with independent tuple-set counts. Reconstructed reward-bound
initial arrays give the emitted Q movement and changed-entry counts; terminal rows
stay zero and values stay within the finite reward bound. No new training or
result-bearing evaluation was used for this readback, and no scientific defect
was found that would turn the adverse result into a technical failure.

**Cumulative judgment and stopping this idea.** Do not retain or confirm the
unconditioned, globally minibatch-normalized joint-trajectory IS package on this
known recurrent-version host. B01's weak positive fingerprint contrast did not
survive a common repair that made B learning substantially more effective; B02
fails both its current-target proxy prediction against uniform and its native
comparison against stronger simple replay. I will not add seeds, clip weights,
change the endpoint or increase the horizon to rescue this batch. This retires
the selected package in these conditions, not the direction or the mathematical
possibility of reusing old macro experience. Plain and context-matched replay
already reuse old data and provide contrary evidence to a general old-data
unusability story. No inference is made about endogenous co-learning, hidden
teammate policies, nonrecurring behavioral drift, learned HMASD skills, Claude's
PPO coordinator or UAV benefit.

The direction is now **idle after a read scientific boundary**, not blocked on an
owner decision, adviser, monitor or missing artifact. No immediate successor is
selected: the present evidence does not justify more machinery on this small
recurrent-version object. A concrete re-entry condition would be an independently
motivated target with unavailable/nonrecurring behavior contexts and evidence
that obsolete transitions—not the common learner's initialization—limit native
learning; that could justify a new prospective comparison with the right simple
baseline. No producer or periodic check is invented for that condition. The DM
owns this judgment; Root alone integrates the current index. All B handles are
terminal and no additional fit is queued.

**Cost and exposure.** Fifteen started/completed B02 fits; 135,000 primitive
transitions, 1,440,000 replay uses and 465 exact panels. Runner wall seconds,
ordered joint/fingerprint/recent/uniform/fingerprint_zero per seed:
92001 = .940/.786/.702/.709/.790;
92002 = .960/.857/.716/.711/.765;
92003 = .966/.761/.713/.718/.746.
Sum runner wall 11.8406 s; summed single-child user+system CPU 10.4807 s;
maximum single-child peak RSS 45,700 KiB. Own fits were serial, with one native
numeric thread, on the admitted local_linux shared WSL host. First acceptance to
last process exit is 377.246 s, not active occupancy; launch/publication/interaction
time is not fully instrumented and no speed claim is made. Total development
exposure for this selected correction is **27 started/completed fits** across B01
and B02, 243,000 primitive transitions and 2,592,000 replay uses, plus the one
separately retained B01 pre-training refusal. B02 is an outcome-informed targeted
revision, not fresh confirmation; three seed blocks do not establish a universal
ranking or population precision. No claim note or confirmation batch was started.
