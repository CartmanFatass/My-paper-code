**Grant the single TRDL-B01 Q32-versus-SCALAR learning pair and its minimum direction-local implementation, focused verification and closeout. Keep TRDL ACTIVE/MEDIUM/recasts0 in its existing occupied slot.** The completed A01 now supplies a concrete native comparison between two baselines serving the same lower-tail actor objective. I judge one actual learning-and-evaluation realization worth purchasing to decide whether the distributional package merits further development, rather than retaining the scalar design without observing the comparison. This is a qualitative investment choice, not a prediction of Q32 superiority or a finding of measured affordability. [A01 intake, decisions and strongest null][S1]; [B01, question and interpretation][S2].

**The new allowance is exactly two original result-bearing arm invocations, one fresh SCALAR fit and one fresh Q32 fit, with the card's 512 training and 256 final stochastic-evaluation episodes per arm.** It includes the necessary small implementation and support campaign described below. The historical 900-second whole-arm / 1,800-native / 1,200-support / 3,000-complete offer never authorized work. For this new allocation I adopt those figures only as initial ordinary runtime plans, prospectively adjustable by the DM under current rules; I do not impose new hard wall-time ceilings or assert that the work will fit those estimates. The fixed invocation, scientific-exposure, source-scope and actual resource limits remain binding. [Original registration, §5][S6]; [B01, resource plan][S2]; [evidence specification, §11.8.1][S9].

## 1. What changed, and why this first purchase is justified

The earlier vacancy decision purchased zero-exposure preparation, not a learner. A01 has delivered that assignment: a verified reusable host/actor path, the precise score and critic targets, a 137-entry pre-action critic context, finite exposure and an implementation outline. Its observed activity remains zero fits, model constructions, native/evaluation calls, optimizer updates, pilots and historical numerical reruns. Static acceptance is neither independent runtime review nor accepted executable TRDL code. The original registration and completed vacancy choice remain intact; this decision crosses their expressly ungranted numerical-investment boundary prospectively. [A01 E0, source facts and receipts][S3]; [counts, actual_A_exposure][S4]; [prior assignment, §§3–5][S7].

The useful next observation concerns an actual development choice: whether to retain Q32's return-distribution fitting and transformed baseline, or prefer the directly fitted scalar tail-score baseline. Their idealized purpose can coincide while finite fitting behaves differently. My inference is that Q32 could reuse information about full returns across changing empirical thresholds, but it may instead introduce quantile error and less favorable optimization. That possibility motivates a test; it is not an observed benefit or a variance-reduction theorem. Another static assessment cannot answer the native learning question that A01 has now specified. [B01, two trained baselines][S2]; [FOUNDATIONS, §4][S12].

**The strongest alternative is to decline Q32 development and retain the simpler scalar route.** An adequately fitted scalar conditional score predictor already targets the quantity subtracted from the actor's score. Q32 has no established information or representation necessity. Sixteen-episode batches, changing thresholds, different loss scales and joint actor/critic gradient clipping may all favor SCALAR. With distinct batch returns, only three observations have strictly negative W; nominal lower-quarter membership does not supply four nonzero score observations. More ties can reduce that number further. There is no empirical TRDL scalar success to cite, however: scalar retention here is a design/investment preference, not retention of a validated trained policy or an implicit unpaired scalar grant. [S1, observation and counterargument][S1]; [S2, null and threshold convention][S2].

I accept that countercase and nevertheless purchase the comparison. A useful tail increment, a small difference, or an adverse result can each change the choice between these two concrete packages without resolving population uncertainty. The design pays for two actual learners and their required final panels, not a preliminary performance pilot, a tuning grid or an exact diagnostic followed by the same experiment. It reuses the native host and actor while replacing only the incompatible learning/collection logic locally. The decision accepts uncertain runtime and a possible inconclusive result; it does not calculate positive value of information, rank sibling returns, or require a successful comparator-tuning exercise first. [A01 recommendation][S1]; [B01, minimum implementation][S2]; [specification, §§8.1 and 11.8–11.9][S9].

## 2. Preserve the actual same-objective comparison

Retain the registered homogeneous five-UAV/fifty-uniform-user, H=256 native task, unchanged legal DENSE/GRU64 stochastic motion actors and native team return

    G = J = sum_t r_t / 256,
    r_t = sum of the five native rewards_dict entries.

Do not substitute the adapter's averaged scalar or a return-to-go target. The inspected environment helper directly supports the named constructor settings and reward summation; deeper native reward/state and DENSE implementation details remain attributed to A01's source report, not a new inspection of those unlisted files. [environment.py, make_real/actor_features/critic_features/team_reward][S14]; [A01 E0, source table][S3].

For each arm's own batch of 16 episodes, retain alpha=.25, the detached fourth-smallest FP32 return eta, and

    f_eta(g) = (g - eta) * 1[g <= eta] / .25,
    W_e = f_eta(G_e).

SCALAR fits W by factual mean-squared error. Q32 fits full episode G by the card's factual midpoint-quantile pinball loss, then uses the average of f_eta over its detached pre-update quantile predictions as its baseline. Both critics receive the same pre-action context137: existing critic136 plus accumulated past team reward/H. No cumulative reward, threshold, quantile or centralized critic input reaches the actor. Future return is a fitting target, never an input. [B01, information and baseline table][S2].

The actor advantage is the complete W minus the frozen baseline, including on non-tail episodes. Eta must remain in the score transform; the learned baseline does not replace eta inside the indicator. Preserve the four-epoch frozen behavior inputs, chunk-start hidden states, scores, baselines and advantages. Sum the three velocity-coordinate log densities within each UAV, clip each UAV's ratio separately, sum across all five UAVs and average over episode/tick. Do not replace this with one team ratio or an additional division by five. The inspected clipping reducer supports that sum when used with the agent mask, and recurrent_outputs supports detached behavior chunk starts. [B01, actor update][S2]; [learner.py, clipped_policy_loss/recurrent_outputs][S15].

The shared update function is not the TRDL learner: it explicitly computes returns-to-go, standardizes advantages and includes an entropy term. Its direct reuse would change the selected scientific comparison. The card already identifies the adequate correction: a local collector and tail-target/baseline/loss path, reusing valid replay, density, clipping and Adam primitives without modifying shared scientific defaults. This correction is included in the purchase, not a separate prerequisite study. Preserve lr=.0003, four epochs, loss actor_loss+.5*critic_loss, joint norm clipping .5 and the other specified optimizer settings. No new scientific redesign or specification exception is required for this investment. [learner.py, optimizer_for/update][S15]; [A01 E0, mismatch and smallest correction][S3].

The resulting comparison includes quantile-versus-scalar loss scale, fitting and joint-clipping consequences. Raw unsorted Q32 outputs and empirical eta remain the selected approximation; no new sorting penalty, target cross-product or baseline standardization is added. The proposal is CVaR-oriented, not exact or unbiased CVaR optimization. Richer predictions, nonzero updates and legal CTDE inputs do not establish an adequate critic, convergence or correct individual causal credit. [B01, common target and exclusions][S2]; [FOUNDATIONS, §§2–4][S12].

## 3. Exact selected scientific and implementation allowance

| Item | Selected boundary |
|---|---|
| Training identity and original invocations | One prospectively specified matched instance, master9601 with the card's seed partition; two original arm invocations, one per method. No screened seed, old checkpoint or replacement fit. |
| Training per arm | 512 complete H256 episodes; 32 batches of16; four full-batch epochs; 128 joint actor/critic Adam calls. All actor and critic parameter groups train. |
| Final measurement per arm | One final immutable checkpoint; 256 complete stochastic episodes with common reset worlds, private action randomness and no evaluation updates or checkpoint selection. |
| Pair exposure | 1,024 training plus512 evaluation episodes; 262,144 training plus131,072 evaluation team ticks =393,216 scored ticks; 256 joint Adam calls. |
| Implementation | The B01 direction-owned learner/study, run_trdl_b01.py and matching tests; reuse codex/trdl and its existing authoring worktree. No shared learner/host modification or optional infrastructure. |
| Verification/support | One proportionate focused validation campaign, independent high-risk code review and necessary corrections; source/command publication, staging/admission, observation, collection, technical/scientific intake, full scientific-review response and preservation/assigned closeout. No extra native validation or performance invocation. |

The scientific counts are the supplied prospective arithmetic, not work performed by A01 or this response. Both preselected methods remain in scope regardless of the first score. A genuine integrity/resource limitation can hold affected work; a disappointing score cannot cancel its comparator, substitute a historical arm or buy another draw. Where only one endpoint is trustworthy, preserve it without inventing the paired primary. [B01, exposure/RNG and finite boundary][S2]; [counts, design/work][S4]; [specification, §11.8.7][S9].

The support allowance now permits the card's controlled-array tests and minimal synthetic learner checks, including test-only model construction/backward work. They are implementation verification, not scientific fits: no native rollout, master9601 screening, cost pilot or empirical efficacy claim. Cover the changed reward/context boundary, eta/ties/scaling and pinball sign, detached baselines/frozen advantages, nonfrozen actor/critic gradients, recurrent/RNG ownership, the agent-summed reducer and own-arm tail publication. Reuse unchanged-path evidence rather than add repeated launch smokes. [B01, L0 acceptance][S2]; [engineering, §§3 and 7.3][S11].

Keep the existing maximum2,000 new non-test research-code lines, maximum600 runner lines and cumulative five-minute research-directory test budget, with its stated runner-smoke exclusion; this decision allocates no separate native smoke under that exclusion. The 30% orchestration ratio is a review signal, not a veto. A necessary coverage or source-scope excess is a concrete gap to address under the existing rules, not permission to omit required checks or silently extend this grant. No framework migration, generic worker pool, retry/resume framework, schema guard, telemetry service, provenance gate or new agent layer is selected. [Engineering specification, §§3–5/7.1/7.3][S11].

## 4. Runtime plans are not scientific endpoints

**Select the work now; use 900 seconds per complete arm, 1,800 seconds summed native work, 1,200 seconds support and 3,000 seconds combined only as initial ordinary plans.** These numbers are not measured rates, a guaranteed total price, new paid capacity or inherited unused funds. DM may prospectively revise these ordinary estimates/watchdogs, recording reason, actual progress and costs, without another Root ACK or Portfolio vote merely for revising an estimate. Do not label an unknown or exceeded estimate a scientific failure. Real owner/platform limits, the two-original invocation bound, fixed scientific exposure and unchanged code/test constraints cannot be relaxed on that basis. A materially different experiment or additional invocation is outside this purchase. [Original offer, §5][S6]; [B01, cost qualification][S2]; [specification, §11.8.1][S9]; [AGENTS, §5][S10].

Complete work is substantial despite the small model. The supplied counts give 1,966,080 collection/evaluation agent rows and5,242,880 replayed actor rows across the pair. Each arm presents524,288 critic context rows over its training epochs. Q32 requires16,777,216 scalar pinball terms and4,194,304 frozen-baseline quantile transforms; SCALAR requires524,288 MSE entries. Those32 output terms are intrinsic estimator work, not32 trajectories, independent replications or a32-by-32 Bellman target grid. There is no policy, controller, solver or trajectory search. [Counts, work][S4].

Preserve the card's whole-arm accounting: non-reset initialization;769 resets, including the constructor reset;512×256 training ticks;32 frozen-baseline batches;128 update calls;256×256 final-evaluation ticks; serialization/publication and exit. No evaluation or publication stage is moved outside native accounting. Sum of arm wall, study critical path, support invocation time and provider/agent labor are distinct. All unit rates, actual peak RSS, total future wall and full support/provider/maintenance costs remain UNKNOWN. [B01, complete cost law][S2].

The 34,902 actor parameters and34,305/38,304 critic parameters do not prove affordability. Nor do the reported8,847,360-byte observations,5,242,880-byte hidden-state storage and2,244,608-byte contexts estimate total peak memory; actions, optimizer state, copies and autograd add work/storage. The nominal128×.0003=.0384 schedule scale is not parameter displacement. Report actual movement during the selected fits without manufacturing an extra exposure experiment now. [Counts, architecture/resources][S4].

Use the card's remote-first CPU FP32, single-compute-thread route and in-process replay batching. Each actual arm needs its own immediately adjacent physical AND effective available-memory admission of at least4GiB, on the executing node, with exact published source and command. Existing sibling commitments and actual resource risk remain respected; historical wall or component bytes cannot supply admission. Stop an invocation for actual failure, resource danger or a terminating watchdog and retain its partial facts. Reconciliation of an uncertain existing effect is not permission for a duplicate process or scientific retry. [B01, route][S2]; [AGENTS, §§5–7][S10].

## 5. Outcome-dependent development, not stronger claims

Keep the primary exactly

    L_a = mean of that arm's own 64 lowest J values among its 256 final episodes,
    Delta_tail = L_Q32 - L_SCALAR.

The two selected lower tails need not contain the same worlds. Sorting paired differences, selecting only mutually adverse worlds or interpreting an ordinary paired-mean SE as tail uncertainty would change the question. Retain all512 final returns, both ordinary means, both lower-quarter means and thresholds, ordinary-mean difference and all adverse outcomes. Sampling uncertainty remains conditional and order-statistic based; this investment adds no bootstrap, extra panel or population-inference requirement. [B01, final measurement][S2]; [empirical topic, randomness and comparison][S13].

Retain the registered absolute MEI=.01 lower-tail J. Its local interpretation is2.56 summed team-reward units over256 ticks, or approximately .714 average connected-user equivalents with the quality component fixed. This supports its service-scale meaning without importing another direction's margin or turning it into a safety threshold. [Registration, §5][S6]; [counts, MEI][S4].

| Complete result | Bounded development implication |
|---|---|
| Delta_tail strictly above+.01 | Q32 has a locally useful poor-episode increment and may merit bounded follow-up. Ordinary-mean harm remains a real tradeoff and can weaken the investment case; do not call this unqualified overall benefit. |
| Inclusive−.01 to+.01 | Retain the sign and uncertainty; prefer the simpler scalar recipe at this boundary without declaring equivalence or adequate statistical power. |
| Delta_tail strictly below−.01 | Favor SCALAR for this tested recipe and reconsider Q32's current design. This does not refute distributional learning generally. |
| Missing/nonfinite/incomplete required endpoint | Preserve trustworthy arm facts and actual costs; no invented two-arm tail result, score-based replacement or automatic retry. |

These are interpretation directions, not automatic lifecycle or spending rules. One paired training instance cannot estimate training-population uncertainty. Common reset/initialization laws do not equate endogenous trajectories, and private random streams do not create independent method replications. The ceiling is B/EXPLORE: no stable superiority, scalar-class inadequacy, exact CVaR optimization, isolated representation/credit cause, expected-return superiority, tuned headroom, novelty, safety or transfer claim. [B01, claim limits][S2]; [FOUNDATIONS, §§4/6][S12]; [empirical topic][S13].

## 6. Application and revisit boundary

The existing TRDL Astra/max DM in `C:/Projects/HMASD-worktrees/codex-trdl`, branch `codex/trdl`, intakes this complete decision and proceeds through the selected implementation, focused independent review, source acceptance/publication, admission, two originals and complete result/review/retention response. The prospective card's unallocated status is updated through that normal application; its scientific laws remain. No new DM, writer, conversation, specification layer or per-step permission is needed. Concrete scientific/specification conflicts return to this same Portfolio node while independent conforming work continues. [A01 intake, workspace/handoff][S1]; [AGENTS, §§2/4.7–4.8/5][S10].

The pinned current snapshot is three occupied directions—ACVC, FOLR and TRDL—with no reservation or vacancy. ACVC/FOLR have their own accepted work and observation responsibilities. This decision preserves their allocations and priorities, TRDL's ACTIVE/MEDIUM/recasts0 status and all unselected PARK evidence. It does not reopen MGTAP or infer any sibling result. Matching tuned lower-tail headroom remains absent; different-host baseline records and other directions' returns supply neither TRDL headroom nor a ranking score. [Current Portfolio snapshot][S8]; [A01 E0, baseline limits][S3].

Revisit the development investment after the completed pair and full scientific response, or at a concrete integrity/resource/scope limitation. A useful Q32 tail difference with acceptable observed tradeoffs may warrant one separately selected recurrence; little separation or scalar advantage strengthens the simpler-route preference. A newly identified target/leakage/publication defect changes only its dependent claims. No result automatically selects another seed, longer endpoint, risk grid, larger quantile model, extra evaluation, C promotion or successor. Completion ends this allocation, not the direction or its slot. [Spec, §§7–8.1/11.8][S9]; [AGENTS, §5][S10].

## 7. Actual source access and limitations

All15 scientific manifest paths were accessed through GitHub at their declared versions. Except the Portfolio snapshot at `d725c677f33412bd4b73b908b22069317582ab04`, they were read at `80511fa6cddd907177b011af767bce5039e316ad`. The fixed TASK was separately read at its specified revision. References identify exact paths and full versions; section locators identify the material used.

| Sources | Actual material used |
|---|---|
| [A01 intake][S1], [B01 card][S2], [A01 E0][S3], [counts][S4], [DIRECTION][S5] | Complete texts/record: disposition, registered/current design, source findings, actual zero activity, prospective counts, counterargument and work boundaries. |
| [Original discovery response][S6]; [vacancy response][S7] | Registration §5 and prior assignment §§3–5. Neighboring text returned by line windows was not used to enlarge this investment or revive historical allocations. |
| [Portfolio][S8] | Complete current snapshot, occupancy and peer/author responsibilities; no later producer state inferred. |
| [Evidence specification][S9] | §§4/5.1–5.2/7/8.1/11.4/11.7–11.10. No named exception for another object applied. |
| [AGENTS][S10]; [engineering specification][S11] | AGENTS §§2/4.7–4.8/5–7, including explicit resume; engineering §§3–5/7.1/7.3. |
| [FOUNDATIONS][S12]; [empirical topic][S13] | Foundations §§2–4/6 and empirical comparison/randomness/whole-method passages; applied to actor/critic legality, finite learning and actual units. |
| [environment.py][S14]; [learner.py][S15] | Named constructor/feature/reward functions and clipped_policy_loss, recurrent_outputs, optimizer_for/update, with nearby collector context. Static reading only. |

No listed decision-critical source remains unavailable. Unlisted actor/native-environment dependencies, external papers, local-library contents and runtime state were not independently inspected. A01's primary-paper retrieval, native reward/state-layout investigation and static checks remain attributed to its E0, not claimed as this node's own external search or execution. No model, environment, optimizer, test, profiling or numerical reanalysis was run in this consultation. Unknown learning effectiveness, tail sampling behavior, implementation correctness and complete costs remain unknown rather than becoming new admission gates.

**Final: purchase exactly the specified TRDL-B01 pair and its minimum implementation/support on the terms above.** This is the new investment decision, not a receipt that its scientific work has already run. Preserve the simpler-scalar countercase, zero historical TRDL exposure and the existing three-direction working set.

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/candidates/tail_return_distributional_learning/TRDL_A01_INTAKE_20260914.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/candidates/tail_return_distributional_learning/TRDL_B01_SCIENCE_CARD_20260914.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/candidates/tail_return_distributional_learning/TRDL_A01_RESULT_EVIDENCE_20260914.md
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/candidates/tail_return_distributional_learning/TRDL_A01_COUNTS_20260914.json
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/candidates/tail_return_distributional_learning/DIRECTION.md
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/portfolio/pro_packets/20260912_new_direction_discovery/archive/RESPONSE.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/portfolio/pro_packets/20260914_mgtap_vacancy_replacement/archive/RESPONSE.md
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/d725c677f33412bd4b73b908b22069317582ab04/docs/research/portfolio/PORTFOLIO.md
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/AGENTS.md
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/project/ENGINEERING_SCOPE_SPEC.md
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/80511fa6cddd907177b011af767bce5039e316ad/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
