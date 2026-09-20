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
