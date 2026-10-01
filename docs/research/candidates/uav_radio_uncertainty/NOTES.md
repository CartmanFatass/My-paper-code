# UAV radio uncertainty

<a id="b01-selected-contract"></a>
## 2026-10-01 — B01 selected: complete expected-power versus distribution integration

Lead: the same nonarchived native `/root/dm_user_waiting`, now assigned by Root to
`uav_radio_uncertainty`. One active study: `b01_correlated_shadow_a01`. The waiting
direction is moving to reserve; its B07 and scoped longer-planner stop remain closed.
No experiment or runtime query had occurred when this entry was begun.

Question: under an explicit approximate correlated-shadowing host and equally priced
current link measurements, does integrating joint RF outcomes improve complete delivered
native service over a competent adaptive expected-power controller after sensing,
transmission and computation delays? The contribution sought is conditional ordinary
cooperative-control capability and its execution boundary. No learning or field-validity
claim is selected.

The entire selected source contract and eight-part bill remain canonical at
[70cf2ca28bed654cf19329cbc55bda7ab10b3edd](https://github.com/CartmanFatass/My-paper-code/blob/70cf2ca28bed654cf19329cbc55bda7ab10b3edd/docs/research/candidates/uav_user_waiting/NOTES.md#radio-uncertainty-complete-source-price),
with source facts and original exchanges at
[0136d45b06e4bd71e0eb0e8b5a035529ba0ecf9a](https://github.com/CartmanFatass/My-paper-code/blob/0136d45b06e4bd71e0eb0e8b5a035529ba0ecf9a/docs/research/candidates/uav_user_waiting/NOTES.md#radio-uncertainty-source-assessment).
They are inputs to this study, not a new positive result. Root's selected comparison and
refinements are published at
[e8a2e9b275deb2cad08cbec36484660986424096](https://github.com/CartmanFatass/My-paper-code/blob/e8a2e9b275deb2cad08cbec36484660986424096/docs/research/RESEARCH.md#radio-uncertainty-selected-20261001).
The original Oracle recommendation and Root disposition are preserved separately below.

The current published RESEARCH background on information/representation, native radio
activation and complete-package value changes the design concretely: P receives the same
new pilot measurements and correct known stochastic law; both retain the same restricted
C proposal menu, physical commitments, native objective and delivery budget. A wrong
free-space manager is not the sole ordinary comparator. Finite-model B02 is an adverse
antecedent: P32−AF completed jobs +.125/context, U32−P32 −.00390625 and U256−P256
+.01171875 with U−P intervals crossing zero. Its persistent-parameter/hidden-peer setting
does not answer this RF-realization question. Accurate deterministic-host forecasts and
poor complete continuity in B07 likewise do not identify RF error as their cause.

Both arms use N5/U50/H256, 2 GHz free-space mean, 23 dBm transmit power, −80 dBm
noise, 3 dB eligibility, capacity ten, stable greedy native allocation/J, static users,
componentwise 30 m commands and height [50,150] m. Only user-link excess dB loss changes:
z0=4.14 epsilon0 and z'=rho z+4.14 sqrt(1−rho²) epsilon, with
rho=exp(−actual three-dimensional displacement/17.62). Independent addressed link
innovations are consumed for all 250 links on every physical tick, including hover and
payload silence. No getters, mask refresh or model call advances that physical stream.
The A2A law remains unchanged. This path-length Markov approximation freezes on hover;
returning to a position need not restore its previous loss.

Each manager receives five 75-byte reports: the waiting protocol's 25 bytes plus fifty
uint8 current total-loss values per member. Encode ties-to-even round((L−40)/.5),
clip [0,255], decode 40+.5 code, retaining saturation. These ideal calibrated reciprocal
measurements include all registered links and payload-silent receivers. Keep the same
400-byte rounded XY map and native C104/private navigation. With the 16-byte command,
391 bytes at 2,000 bit/s plus fifty 2 ms sounding slots consume 1.664 s. Delivery after
three ticks leaves 1.336 s for all C-plus-manager computation; commands hold four ticks.
Any miss retains both old commands and old mask atomically. Record actual partial work
and traffic. The sensor observes the report-boundary state; sounding adds no sub-tick
state evolution. Report transitions receive .9 payload weight, the others one.

Both use the original two-order S2 search over one rotating member's 27 commands and
31 masks, common current C proposals, 116 requests and 57/83/87/112 unique pairs when
complete. Propagate three committed transitions, then score only the delivered block
(four transitions, except the final report at 252 has one). P propagates conditional
Gaussian moments from the common decoded point estimate and evaluates native service
at analytic expected received powers. U averages actual service/J over 16 Gaussian
tapes and their 16 antithetic negatives, shared across every candidate within a decision.
Generate all seven future-noise slots even at the final short block. Quantization is a
common point-estimate convention, not exact Bayesian filtering. No future C is needed
by this clock. Preserve original native tie order using payload J/served; quality is in J.

Primary: paired-world difference in complete payload-J/256, descriptive mean ±1.96 SE.
All 32 signed world effects and raw/payload levels, fifty-user age/gaps with boundary
censoring, outages, service min/p10, travel, transmitter exposure, delivered changes,
deadlines, fallbacks and full work stay visible. Worlds, not particles, are the units.
A mean gain does not erase user-level harm or establish broad default adoption.
Active adverse/unresolved U value or sparse/fallback-dominated deployment ends this fixed
purchase without automatic extra seeds, particles, deadline, severity or learning.
P remains a matched reference; U failure alone does not make P a useful default.

### Exact seed, arithmetic and exposure binding before any query

Main geometry/channel worlds: integers 29641000 through 29641031 inclusive, alternating
arm order P/U32 on even offsets and U32/P on odd offsets. Geometry uses the native
RandomState(world) initialization without a changed draw order. Main constructor world
29641999 is discarded but saved/audited. The four H8 correctness episodes share geometry
world 29641900: frozen free-space and sigma-zero matched fixed commands/masks, then one
P and one U32 correlated episode. They use three additional environment instances
(old free-space, sigma-zero, correlated P/U32 reused), hence four constructors total,
68 explicit resets and four constructor resets. Their constructor seeds are respectively
29641996, 29641997 and 29641998. These are distinct from all main worlds.

Physical noise root 29640001 and namespace hexadecimal 0x52465048; model noise root
29640002 and namespace 0x52464D43. Each addressed block uses NumPy 1.26.3
Generator(Philox(SeedSequence([namespace, root, world, tick]))) and standard_normal
in float64/C order. Physical tick zero initializes z; physical tick k is the innovation
used to reach state k, shape (5,50), including all silent/hovering links. U's report tick
indexes one shape (16,7,5,50) base block; concatenate its negative along axis zero.
These addressed blocks comprise one declared model stream per U/world. Model and
physical namespace/root separation precludes reading physical future noise.
No randomness for P, decoding, allocation or search tie breaking. Synthetic namespaces
and their finite invocation schedule will be frozen with the tests before execution.

State/model arithmetic is float64; native C observations/proposals retain their source
float32 contract, reports use the inherited little-endian int16 metre positions and quantized
int8 commands/nav byte, and link codes are uint8. The reader checks exact integer/
command/assignment identities; numerical tolerances will be stated for independent
floating-point formulations before checks. Native core is unchanged.

The selected bill is zero fits/calibration examples/updates, 64 H256 scientific episodes
(16,384 native steps) plus the four H8 episodes (32): 16,416 total. Combined worker/
two-pass-reader C calls, including H8, are 61,500 when complete. The complete immutable
bill prices all constructor/reset geometry, physical/model innovations, all-candidate
reader work, pilot resources, partial work and bounded synthetic checks. Its complete
planning estimates are 2–5 worker-plus-reader CPU hours, .02–.10 correctness CPU hours,
.5–1.5 GiB/process, .10–.20 GB canonical evidence, 2–3 GB remote snapshot-inclusive
incremental peak (4–5 GB under observed local snapshots), and 14–28 further support hours.
These are estimates and prospective exposure, not measured work or a fit allowance.
Already-incurred source/adviser work remains real and incompletely metered.

<a id="b01-l0"></a>
### L0: one exact complete RF implementation

Deliverable: direction-owned adapter, protocol, P/U32 manager with exact particle batching,
full collector and independent reader for every actually executed native and candidate
calculation, compact run records and all required adverse/partial outcomes. Entrypoints:
`experiments/candidates/uav_radio_uncertainty/b01/run.py` and `read.py`; tests mirror b01.
Use existing reusable physics/allocator/controller kernels where compatible. No shared or
frozen executable edit is currently needed. Author on shared main, preserve other writers.
DM owns notebook/index/Git and all files except a specifically delegated bounded subset.

The first Implementer task owns only b01 `environment.py`, `randomness.py`, and matching
`test_environment.py`, `test_randomness.py`: construct a masked native subclass/adapter
with the exact user-link channel lifecycle above, immutable snapshots and monotone
constructor/reset/step/draw counters. `make_env(seed, horizon=256, sigma=4.14)` returns the
native ParallelToArrayAdapter; underlying `.env` exposes `physical_snapshot()` (copies,
no new channel generation), the inherited mask setter, and a public copy of counters.
`physical_normals(world,tick)` returns (5,50); `model_normals(world,report_tick)` returns
the fresh (16,7,5,50) block; both validate inputs and use contract.py constants. The
subclass must initialize its own state before the base constructor's implicit reset and
advance residuals exactly once per physical step after actual clipped motion, never during
observation/mask refresh. Sigma zero still consumes its addressed normals. The old
free-space fixture is built by the collector using its unchanged factory, not copied code.

Checks: static syntax/import graph and independent numerical/RNG engineering review;
then the declared bounded pure-kernel/synthetic-search checks and four H8 episodes after
exact inputs are committed/published. The Implementer writes checks but initially runs
only static syntax/diff checks; it does not construct native objects, sample normals,
call models/C/allocators or run pytest before DM publishes the exact check inputs. It
spawns no child, changes no science/arm/seed/budget, launches nothing, edits no notebook
or other paths and performs no Git index/commit mutation. It returns diff/check facts and
open risks; DM accepts the result. Additional correctness work after a concrete finding
is prospectively recorded and counted; no timing pilot or sweep is selected.

The historical scalar scorer proxy predicts U32 1.542–3.030 s/round against 1.336 s.
Exact batching is selected implementation work, with no measured speedup promised.
Fallback remains part of the eventual complete result. Stop at a genuine technical
failure with its actual exposure preserved, or at the complete independently read panel;
do not automatically extend the experiment to secure a positive result.

<a id="radio-uncertainty-original-root-question"></a>
## Original Root RF question — received by Oracle 2026-10-01 05:37:39 UTC

The following is the complete original question from the artifact-only native handoff;
its source-only restrictions describe that earlier assignment, before Root's selection.

Root NEW bounded SOURCE/IDEA assignment for the SAME nonarchived /root/dm_user_waiting after its fully closed B07 and the scoped stop of an ordinary longer-horizon/service-floor continuation. Detailed discovery and innovation remain Astra Max's job under owner's four-DM assignment. This is a materially different scientific question; it is not a request to reverse the previous Oracle's continuity decision, fix C2 or extend your already selected C/M/V user-motion study.

Question: can lawful UAV cooperation retain or develop useful complete native service when radio-link predictions face physically meaningful propagation/channel uncertainty, against competent ordinary controllers given the same legitimate uncertainty knowledge? The programme's many S1 controls and readers presently use a known deterministic free-space/SINR law, yet accurate within-block predictions already failed to ensure complete use. Uncertainty is therefore NOT an asserted cause of those old failures or a promised route to a learning win. Its possible value is a distinct, consequential application contract in which decisions affect coupled interference/eligibility while the future link quality is not exactly known. Consider ordinary adaptive/robust control and retained learned capability honestly; do not prescribe memory, a learner or new architecture.

Start by reconstructing the ACTUAL host/channel/observation laws and any existing result or July/external review that already studied such uncertainty. A RESEARCH keyword miss is not evidence of novelty; I found no current owner row from its obvious fading/shadowing/propagation terms. Distinguish physical RF propagation and its temporal correlation from delayed message delivery, transport loss, user movement, load reweighting, permanent member loss and native reversible S4 failure. Those are not interchangeable uncertainties. Respect Claude's pause/ownership and all frozen G33/FSD controls. If there is real overlap with an owned question, surface it instead of carving an artificial residual.

Use all three local libraries and read the load-bearing primary passages; use primary web sources as needed for an application-grounded simple model. Check relevance and assumptions, not generic claims that all real systems are noisy. Prefer an existing meaningful native option if present. A justified narrowly owned host extension may be considered, but do not manufacture a hidden parameter/noise process solely to make an old algorithm fail or an RNN necessary. Distinguish unknown fixed parameters from temporally varying realizations and state exactly what agents know/measure/delay. Any new uncertainty knowledge, true channel state or future realization privilege must be equal/accounted for; a deliberately wrong-model ordinary baseline is not competent. Calibration, model/policy queries, training examples, predictor fits, adaptation, branch rollouts and offline readers all cost real work.

The owner wants a useful complete scientific comparison or a reasoned stop, not a new benchmark-name/corruption sweep. Identify one consequential cooperative decision, strongest matched-rights ordinary alternative, a testable added capability, what outcomes would change our judgment and the full practical price. A zero-fit retained-policy comparison is acceptable only if it answers a consequential use question; a changed-physics leaderboard alone is weak. No required positive toy, preliminary opportunity screen, theorem, outside utility price, fixed number of candidates or multiple severity/seed sweeps. Novelty is unknown until primary/records support a scoped claim; new names/known algorithms do not create novelty.

Same waiting DM owns bounded source/feasibility and eventual notebook continuity, and may challenge this premise. Obtain one concrete exact source/worker/reader/engineering/support/RSS/storage price from that DM after narrowing your strongest idea. It can inspect source via CodeGraph first, published records and metadata; source/support work is paid, not a free result. No native/model/C/controller/allocator query, saved-output reduction, data generation, prototype, implementation, benchmark, fit or experiment is authorized by this source assignment. Return one fully specified costed comparison OR a substantive grounded no-purchase recommendation. Do not stop merely because choosing the model/objective/search would require research design—that is part of this assignment—but no rescue or positive idea is owed if comparative value is weak.

Relevant cumulative evidence: RESEARCH current background radio/activation, local-history/peer-forecast, ordinary stochastic Q/G, inherited learning, B08 local gate; waiting B04 K/B05LRS/B06S_F/B07C2. B07 all64 C2−S_F maxgap+80.328 despite almost exact count forecasts, while C2 service+3; fixed-path no-link bound is about eligibility, not radio-model-error causation. Previous longer-planner source stop remains scoped and will be preserved by /root/age_control_interface; it is not a general prohibition on physical-control or uncertainty questions. Other three DMs already own actual-S2 motion development, mixed-controller focal response and S7 anonymous-user tracking; no duplicate study. Root will make the final cross-question investment choice from your complete recommendation.

<a id="radio-uncertainty-original-oracle-recommendation"></a>
## Original Oracle recommendation — returned 2026-10-01 06:20:56 UTC

Complete original wording follows; later Root disposition and DM application are separate.

I recommend **one complete P/U32 comparison on the declared approximate RF host**. This is a worthwhile systems question: does integrating possible link outcomes improve complete service within the delivery deadline, compared with a competent controller using expected received powers?

The price is substantial: **2–5 worker-plus-reader CPU hours and 14–28 further engineering/support hours**, plus correctness checks and already-incurred source work. The strongest objection is feasibility: the historical scalar-scoring proxy gives U32 **1.54–3.03 seconds per round**, exceeding its **1.336-second allowance**. An exact batched scorer could fit, but that remains unimplemented and unmeasured. I still recommend this single bounded comparison; its outcome must include that execution risk.

The complete original proposal and eight-part factual response are preserved in the [immutable source-price section](https://github.com/CartmanFatass/My-paper-code/blob/70cf2ca28bed654cf19329cbc55bda7ab10b3edd/docs/research/candidates/uav_user_waiting/NOTES.md#radio-uncertainty-complete-source-price). I read the entire section, including its corrections and limitations.

The supported diagnosis is limited but consequential:

- The current N5 studies use deterministic free-space propagation. The existing `probabilistic` option also returns a deterministic mean loss. The stochastic `3gpp-36777` branch redraws link states each physical generation without persistent spatial or temporal correlation. Its name does not certify implementation of the full standard.
- Changing propagation while retaining the old free-space controller as the sole comparator would confound uncertainty handling with known-model mismatch. **P must receive the same new measurements, correct stochastic law, action rights and deadline as U.**
- Earlier failures do not identify RF uncertainty as their cause. B07’s stored results show C2−S_F service **+2.9999 users/tick** alongside maximum-gap **+80.3281 ticks** under deterministic propagation. B04 likewise retained useful ordinary planning while a valid local modeled floor failed to preserve the complete trajectory.
- The earlier finite-model study already warns against assuming that uncertainty integration pays. In B02, ordinary P32 improved completed jobs over AF, whereas U32−P32 and U256−P256 remained small and uncertain. Increasing particles eightfold did not establish a useful differential gain. That result concerns uncertain persistent movement parameters and hidden peer state; it does not answer this RF-realization question. [B02 evidence](https://github.com/CartmanFatass/My-paper-code/blob/70cf2ca28bed654cf19329cbc55bda7ab10b3edd/docs/research/candidates/finite_model_decision_value/NOTES.md#2026-09-25--b02-complete-precision-changed-native-budget-response-remains-small-and-uncertain).

The physical bridge supports a limited model, not a calibrated deployment claim. Zhang et al. measured large-scale UAV-to-ground variation and fitted Gaussian dB residuals and exponential correlation. Their UE1/70 m case supplies the prospective **4.14 dB standard deviation and 17.62 m correlation distance**. Their campus geometry, frequency, speed and fitted mean differ from our host; even their distance variable is not our proposed three-dimensional path increment. I read the measurement and modeling passages and Table 3 directly. [Zhang et al., 2023](https://leizhanggg.github.io/files/5Experimental%20study%20on%20low-altitude%20UAV-to-ground.pdf).

I also checked the relevant ETSI passages supplied by Root. They describe distance-correlated shadowing and additional spatial-consistency procedures while permitting basic generation for specified evaluation purposes. This supports using an explicit approximation; it neither validates our proposed law nor requires a full channel simulator before exploration. [ETSI TR 138 901, §§7.4.4–7.6.3](https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/19.03.00_60/tr_138901v190300p.pdf).

All three local libraries were checked. The load-bearing distinctions from their primary passages are:

- [B01, §3.4](/home/fires/hmasd-wsl/docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf): noisy or incomplete observation changes the decision process; it does not establish a need for recurrence or training.
- [MARL-0451, pp. 2–4](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0451.json): its robust-game formulation uses prescribed uncertainty sets and nominal generative access. Its guarantees do not transfer to this known-law RF process.
- [ICLR-2024-c8b2f897e45770595656a79a9ad91e89, pp. 3–5](/mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2024/c8b2f897e45770595656a79a9ad91e89/arxiv-2307.12062.pdf): temporally coupled adversarial state/action perturbations are different from physical channel realizations.

The July and external records inspected included original G34/G51 evidence, G33’s unchanged-propagation contract and the September stochastic-channel engineering checks. They supplied no applicable RF-control result. This is bounded coverage, not a novelty verdict.

The comparison I recommend is the following.

1. **Keep one explicit native task.** Use a new direction-owned adapter of masked N5/U50/H256: static users, existing movement, free-space mean loss, interference, 3 dB eligibility, capacity ten, stable greedy allocation and native J. Add user-link excess loss
   \[
   z_{t+1}=\rho_tz_t+\sigma\sqrt{1-\rho_t^2}\epsilon_t,\qquad
   \rho_t=\exp(-\|\Delta p_t\|/17.62),\quad \sigma=4.14.
   \]
   Parameters are known to both programs. Future realizations are unknown. Every physical tick consumes all addressed innovations, including for silent or hovering UAVs. Observations, mask changes and model calculations consume no additional physical innovations. Paired arms share initialization and innovation addresses; their realized losses may diverge after movement diverges.

   This is a path-length Markov approximation. Hover freezes the residual; returning to a location need not restore its previous loss. It does not represent a persistent learned RF map.

2. **Price and match the new measurement right.** Both managers receive current calibrated reciprocal pilot estimates for all 250 registered links, including payload-silent UAV receivers. Encode total loss in the declared 0.5 dB uint8 representation, retaining saturation evidence. This is an idealized sensor assumption, not information already contained in C’s anonymous 104-value observation.

   Five expanded reports and the command total **391 bytes**. At 2,000 bit/s, with **0.1 seconds of sounding**, the physical communication allowance is **1.664 seconds**. Delivery therefore occurs after **three ticks**, leaving **1.336 seconds for the entire C-plus-manager computation**. Hold commands for four ticks and preserve atomic command-and-mask fallback.

   The sensor samples the report-boundary state. Sounding is an explicit airtime charge, without invented sub-tick movement. Report transitions receive weight 0.9 in payload J/service; other transitions receive weight one. Retain raw native outcomes too. Positive 0.9-weighted service still resets the one-second waiting metric; this does not measure sub-second gaps.

3. **Compare competent ordinary programs.** Both use the same existing two-order S2 search: one rotating member’s 27 commands, 31 nonempty masks, common current C proposals, 116 logical requests and **57–112 distinct candidate pairs** when complete.

   P propagates the decoded current residual and its conditional variance through the actual commitment prefix and candidate motion. It evaluates native SINR/allocation using analytic expected received power:
   \[
   \mathbb E[P_{\rm rx}]
   =P_{\rm FS}\exp(-a\mu+\tfrac12a^2v),\qquad a=\ln(10)/10.
   \]
   This accounts for the known lognormal law.

   U uses **32 joint conditional trajectories**, formed from 16 Gaussian tapes and their antithetic negatives, shared across candidates at that decision. It averages each trajectory’s complete native J and service outcome. Preserve the existing tie order, using payload-weighted J/service. Quality already enters J.

   The scientific bridge is the difference between evaluating a nonlinear service function at expected powers and averaging that function over powers. Thresholds, capacity and interference permit different decisions. They do not guarantee useful decisions: finite sampling, adaptive search paths, quantization and subsequent trajectories remain part of the package.

4. **Buy one complete observation.** Use 32 prospectively fresh paired geometry/channel worlds, alternating arm order: **64 H256 episodes, 16,384 native steps, zero fits**. Freeze seed namespaces, normal transformation, precision, rounding and indexing before execution.

   At each report, propagate three already-committed transitions before scoring the delivered block. The final report at 252 arrives at 255 and has only one candidate transition. Thus each episode has **253 scored candidate transitions plus three startup transitions**. No future C query is required by this particular clock.

   The primary is the paired difference in complete **payload J divided by 256**. Retain all raw J, service and quality; all-user waits, gaps and boundary censoring; outages, minimum/p10 service, travel, transmitter exposure, deadlines, fallback and every world’s signed difference. Use the declared descriptive paired-world intervals. Worlds are the independent units; particles and controller calls add no replication.

5. **Retain the full verification cost.** The reader reconstructs every actual native RF update, observation, grant, command, sensor packet and outcome, plus **all executed P/U candidate calculations** from their separate model streams. It checks partial work at the recorded interruption point; it must not finish unexecuted decisions as extra counterfactual policies.

The principal quantities in the complete bill are:

| Work or resource | Prospective quantity |
|---|---:|
| Scientific native steps | 16,384 |
| Four fixed H8 correctness episodes | 32 additional steps |
| Total native steps | **16,416** |
| Constructors / explicit resets / constructor resets | 4 / 68 / 4 |
| Current C calls, worker plus reader including H8 | **61,500** |
| Main-panel candidate fleet scores, worker | **15.229–29.923 million** |
| Full reader | Repeats those candidate scores |
| Main-panel candidate user-SINR entries, worker plus reader | **7.614–14.961 billion** |
| Fresh model/kernel normals, including stated synthetic bounds | At most **115.584 million** |
| Worker plus reader CPU | **2–5 hours**, estimated |
| H8 and bounded synthetic correctness CPU | **0.02–0.10 hours**, estimated |
| RSS | **0.5–1.5 GiB per process** |
| Canonical new evidence | **0.10–0.20 GB** |
| Incremental peak disk | **2–3 GB remote**, approximately **4–5 GB** under observed local snapshot sizes |
| Further engineering/support | **14–28 hours**, estimated |

These are counts and planning estimates, not measurements of new execution or reserved resources. Source and adviser work has already occurred and is not comprehensively metered. Prior study costs remain sunk. The complete bill preserves the sensor, setup, RNG, partial-work and synthetic-check accounting behind this table.

The strongest consequential objection remains that the investment may purchase a deadline failure or a benefit peculiar to the approximation. Three unclipped 30 m prefix steps reduce the current residual’s mean coefficient to approximately **0.00605**; hovering preserves it. The intended test therefore concerns conditional nonlinear uncertainty integration and motion-dependent persistence, not long-lived channel memory. The common C proposal mechanism also limits both managers: only one member receives the exhaustive command override.

I judge the comparison worth buying because it preserves the consequential joint decision, gives the cheaper alternative the correct law and identical measurements, and charges implementation and delivery costs. A positive toy, severity sweep, larger sample count or learned replacement is unnecessary.

The outcome would change the decision as follows:

- **Useful complete payload-J gain with acceptable observed service tradeoffs and timely execution:** retain U32 as a conditional operating option on this host. This would establish neither field validity nor a learning contribution.
- **Active interventions with adverse or unresolved complete benefit:** retain P and stop this U32 purchase. Better model scores would not rescue it.
- **Sparse or absent delivered differences:** conclude that the added computation did not demonstrate useful deployment in this population; do not infer that uncertainty generally has no value.
- **Deadline-dominated fallback:** record an adverse execution result for this implementation. It would not refute distribution integration generally or automatically justify changing the deadline or particle count.
- **Mean benefit accompanied by serious user-level losses:** retain the measured tradeoff rather than claim service preservation.

I checked current source, frozen contracts, consequential stored positive/adverse results and the primary passages described above. I did not rerun historical readers or recompute outcomes. No new runtime query, fit, test, benchmark or implementation was performed. Root’s selection and concrete ownership assignment remain the next action.

MATERIAL_DISSENT: **no** — recommend this single bounded P/U32 investment with the explicit model, sensor, cost and deadline limitations above.

<a id="radio-uncertainty-primary-source-coverage"></a>
## Original primary-source identities and actual coverage

These specify the bounded primary reading underlying the original recommendation, not a new review or whole-library reading claim.

1. Zhang et al., “Experimental study on low-altitude UAV-to-ground propagation characteristics in campus environment,” Computer Networks 237 (2023), 110055; author PDF https://leizhanggg.github.io/files/5Experimental%20study%20on%20low-altitude%20UAV-to-ground.pdf. Direct reading: measurement setup §2, modeling §§3.3–3.5, and §4.1/Table 3, printed pp. 2–6. The recommendation borrows the UE1/70 m sigma and correlation distance only; it does not adopt or validate the complete measurement environment, mean law, radio frequency, sensor implementation, multi-link independence, or three-dimensional path-length process. Table 3 and the source's separation-distance variable were checked. No whole-paper or full small-scale-fading-results reading is claimed.

2. ETSI TR 138 901 V19.3.0, primary PDF https://www.etsi.org/deliver/etsi_tr/138900_138999/138901/19.03.00_60/tr_138901v190300p.pdf. Direct reading: §7.4.4 and the opening of §7.5 (printed pp. 41–42), spatial-consistency §7.6.3.1 and opening §7.6.3.2 (pp. 61–62), and §7.6.3.4 (pp. 66–67). The inspected distance-correlation definition concerns horizontal two-dimensional separation. This is not a full-standard audit, a certificate for the existing native `3gpp-36777` branch, or evidence that the proposed adapter implements all standardized spatial consistency.

3. Local foundations library B01: /home/fires/hmasd-wsl/docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf, §3.4, pp. 51–54. Direct passage reading for partial observability, history and decision-process distinctions; no inference that recurrence, training or a new architecture is required.

4. Inst-sci MARL-0451: /home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0451.json, “Breaking the Curse of Multiagency in Robust Multi-Agent Reinforcement Learning,” primary text corresponding to pp. 2–4. Prescribed uncertainty sets, robust-game information assumptions and nominal generative access differ from the proposed known-law physical realization process; no transfer of its guarantees is claimed.

5. My-lib ICLR-2024-c8b2f897e45770595656a79a9ad91e89: /mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2024/c8b2f897e45770595656a79a9ad91e89/arxiv-2307.12062.pdf, “Game-Theoretic Robust Reinforcement Learning Handles Temporally-Coupled Perturbations,” primary pp. 3–5. Its adversarial state/action perturbation formulation is distinct from the channel law under consideration. Index hints were locators, not evidence.

The targeted project checks covered the original G34/G51 result records, the G33 external-review passages retaining unchanged propagation, and the September throughput/channel engineering record including the shadow-off equivalence limitation. No project-wide novelty verdict follows. Consequential B04/B06/B07 stored outcomes and finite_model_decision_value B02's actual comparison/cost were read; historical outcomes were not recomputed and historical full readers were not rerun in this source task. Source/configuration/RNG details and historical identities are preserved in the original source-facts and full-price sections linked below. No Gudmundson or full 3GPP 36.777 primary reading is claimed.

Original source facts: https://github.com/CartmanFatass/My-paper-code/blob/0136d45b06e4bd71e0eb0e8b5a035529ba0ecf9a/docs/research/candidates/uav_user_waiting/NOTES.md#radio-uncertainty-source-assessment

Original complete eight-part source price/contract: https://github.com/CartmanFatass/My-paper-code/blob/70cf2ca28bed654cf19329cbc55bda7ab10b3edd/docs/research/candidates/uav_user_waiting/NOTES.md#radio-uncertainty-complete-source-price

Context scope: this reviewer was originally created without Root/DM conversation inheritance and reused its own prior project reviews. This was a continuation in that independent reviewer context, not a new blind review devoid of project knowledge.

<a id="radio-uncertainty-root-selection"></a>
## Separate original Root adoption/disposition — received 2026-10-01 06:25:29 UTC

Root read your FULL final recommendation, the COMPLETE70cf2ca28 eight-part original price/contract,0136d45b0 source facts, finite_model_decision_value B02's complete result/cost/stop, and Zhang's primary measurement/§3.5/Table3 passages. I SELECT the one P/U32 comparison and assigned the SAME /root/dm_user_waiting to the new direction uav_radio_uncertainty with the full fixed contract, all explicit sensor/timing/physics/RNG/reader/correctness costs and risk. Exact batching is authorized with proportional independent engineering checks; no performance pilot, particle/severity/deadline sweep or automatic repair. A fallback-dominated deployment remains in the result. This is ordinary conditional-use development, not a field-validity, training or broad default claim. Clarification to your outcome wording: U failure retains P as matched reference, not proof that P is a useful default on the new host; mean payload-J gain does not erase individual service harm. No material design contradiction found. Zhang's1/e definition and stated sigma/distance values checked; its separation-distance and our3D path-length difference remains an explicit approximation.

### DM response and current source access

I read the complete original recommendation and adopt the selected comparison and Root's
reading refinements. This reuses the applicable independent selection review; routine
implementation is not another scientific selection pass. The positive prediction is a
useful complete delivered payload-J increment from integrating nonlinear joint outcomes.
The competing prediction is no useful increment once finite particles, adaptive search,
quantization, actual delay and full computation are included. Timely changed actions are
required to attribute any outcome to delivered U decisions, but no positive activation or
timing pilot is a prerequisite to the complete comparison.

The original source/advice wording above is retained as received, without silently upgrading
its coverage. On 2026-10-01 my direct browser/urllib opening of the Zhang author URL returned
HTTP 404, while web search retained indexed primary-PDF pages. The Oracle's artifact-only
reply states: “I have no existing local PDF copy or already-verified alternate direct locator.
My primary reading used the web tool’s cached full-PDF text at the exact cited author URL
(10 pages; 943 extracted lines); direct URL opening sometimes failed during the original
review too, while reopening the indexed PDF text succeeded.” No alternate identity or
replacement calibration is inferred. Root independently reported reading the same relevant
primary passages. This access limitation does not change the declared approximate host
or count as a new empirical result.


### DM primary-passage access resolved before implementation

The indexed primary PDF became accessible through its cached text. I directly read
Zhang’s measurement system/environment opening and Table 1 (printed p.2), path-loss
extraction and Gaussian residual discussion (§§3.3–3.4, p.4), exponential correlation
and its 1/e definition (§3.5, p.5), and Table 3 with its explanatory PLE discussion
(p.6). UE1/70m gives 4.14dB and 17.62m; its separation-distance variable differs
from our actual 3D path increments. I also directly read ETSI §§7.4.4 and the opening
of7.5 (pp.41–42): horizontal distance correlation, ideal reciprocity assumption and
the stated basic-generation evaluation scope. This supports the declared limited
analogy, not calibration, full-standard equivalence or a new novelty claim. The
earlier HTTP404 observation remains accurate; no alternate paper or parameter was used.
The original URLs and original reviewer coverage above remain unchanged.
