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

<a id="b01-source-and-check-binding"></a>
## 2026-10-01 07:30 UTC — complete source and fixed correctness binding

The one selected study is unchanged. I accepted the bounded Implementer adapter/RNG
and independent native-reader source after reading the complete diff and native host
interfaces. The DM authored protocol/model/search, collection, persistence, outcomes,
the all-particle reader, entries and integration checks. All work remains on shared main
inside this direction's paths. No native environment, model, C, allocator, RNG block,
pytest run or scientific execution has occurred through this source-review boundary.
The source was parsed statically with stdlib AST only (25 Python files including the
two package initializers).

Independent Engineering Reviewer `/root/dm_user_waiting/engineering_review` traced the
full executable route without DM conversation inheritance: actual constructor/reset/
step/mask hooks, addressed physical and model randomness, report0 startup C, three-tick
arrival and final short block, native arithmetic and search, every completed partial
model unit, both C audits, wire/pilots, payload service and all user ages/gaps. Three
reachable P2 findings were accepted and repaired before any execution: final record
allocation previously followed the deadline sample; a successful movement could lose
its saved physical state if the arrival refresh failed; and a file-write/hash failure
could omit an already collected episode's model/C work from the summary. Both atomic
success/fallback records now precede the final clock classification; postmove state is
saved before arrival checks; paid-work rows and intended output bindings precede all
fallible persistence, with final/partial paths, sizes and errors retained. Close errors
also preserve the summary. Zero-science doubles cover the latter two failures; a fake
clock covers the finalization overrun. The Reviewer's final source disposition is
“No material finding remains in the full B01 source review”; its reviewed 24-file
fingerprint is `7ac4fc67ac9cec8e0717c64985cb3a0239c91ce21d2410a51877d8482e8eb6b7`.
Runtime acceptance remains pending. These engineering corrections change no comparator,
clock allowance, exposure, scientific claim or selected investment.

The full reader uses an independently written physical/observation reconstruction and
the unchanged original scalar user-SINR, global stable greedy allocation and native
service reduction for **every actually completed particle calculation**. It does not
use the producer's disjoint-row allocation shortcut as proof. It regenerates recorded
conditional prefixes/geometries and candidate-dependent correlations, checks typed
hashes of all completed intermediates and all particle SINR/grants/native scores, audits
the complete logical search prefix and never finishes an unexecuted request. Every
actual draw or kernel completed before a reader rejection is charged before its digest
is checked. First-pass C consumes saved observations; second-pass C consumes the
independently reconstructed observations from the same paid native audit. The gap/age
reader uses scalar per-user loops, including initial and terminal censoring; the paired
mean/1.96SE audit independently reconstructs every ordered world contrast without RNG.

Precision checks are prospectively fixed: physical/model intermediates, observations,
codec fields, commands, masks, grants and candidate scores/hashes are exact on the bound
NumPy1.26.3 float64/float32 routes. Native team reward versus its divided/summed return
has absolute tolerance1e-12; independent scalar outcome sums have1e-10 absolute tolerance;
summed path lengths have1e-9m absolute tolerance; independently accumulated paired
summaries use1e-12 relative or1e-10 absolute tolerance. None relaxes action/tie identity.
The current-state sensor/anchor introduces one counted nominal geometry per decoded
round (at most4,096 main plus4 H8,250 links each, and its reader repeat), separately from
the already priced candidate geometry. Collection also makes one explicit native service
diagnostic reduction per completed movement to retain quality; this does not add radio,
allocation, a counterfactual world or a policy decision. Hashing, copies, serialization,
these diagnostics and verification are real support costs, included in actual CPU/RSS/
storage observations rather than described as free work.

The fixed H8 source entry is `b01/check.py`: exactly the three additional constructors
and four explicit H8 resets/32 native steps previously priced. The unchanged old masked
factory's one discarded constructor reset is captured by a temporary return-recording
wrapper around its original reset; no extra getter/reset is called. That original
factory constructs at H256, so its discarded state is labeled H256; the subsequent
fixed old-host episode is set to H8 before its explicit reset. The sigma0 and correlated
instances are constructed directly at H8. The fixed command for tick t/member i is
grid index `(3*t+5*i)%27`; both old/sigma0 episodes start mask31 and set mask5 at state3,
mask18 at state7. They make no C/manager/pilot/map-transmission query. The P/U H8 pair
uses its two actual three-tick arrivals each and the already declared world/seeds. All
four episodes and three discarded snapshots are stored before their offline checks.
This preserves the priced eight fixture mask refreshes,7,250 physical-normal
materializations and805 geometry uniforms per side,47 native radio-state calculations
per side,20 worker C calls plus40 reader C calls,200 sounding slots, and zero fits.
Constructor/partial technical failures remain evidence and do not silently restart.

The source-only synthetic suite is now concrete. Address checks use namespace
0x54535048 for physical tests and0x54534D43 for model tests, with the declared roots
29640001/29640002 and fixture world29641900. Five physical API blocks (ticks0,0,1,
constructor-world29641996/tick0, then world29641900/tick0), three model API blocks
(report ticks0,0,4), and one independent physical plus one independent model reference
at world29641900/tick0 total113,500 scalar normals:1,500 physical and112,000 model.
Invalid-input/version and lifecycle-double cases draw none. Other pure cases check
hover/clipped motion, stationary variance, expected-power algebra, codec ties/endpoints/
saturation, timing weights and stable native allocation:16 batched fleet items and16
original scalar native references, zero new normals or native/C calls.

Exactly eight synthetic manager rounds (zero native or C queries) and their eight
actual-prefix reader attempts use fixed synthetic positions/sites/codes, fake clocks
and the model-test namespace above: P full; U32 full; U32 terminal report252; P late at
entry; U32 late after its noise block; P late after two geometry units; U32 late after
its first full radio batch; U32 late only during finalization. Every U case generates
the complete16×7×5×50 block. The after-noise reader attempt deliberately rejects an
altered completed noise digest, retaining its already generated block in the cost.
Both sides therefore generate140,000 normals each; their completed particle work is
bounded by the original229,376 fleet/57,344,000 SINR-entry envelope, not a benchmark
sweep. Native/model/channel query counts of the collector/storage failure doubles are
zero. There are393,500 synthetic normal materializations in total, within the original
784,000 pure/pipeline envelope. If every selected main/H8 U round reaches its noise
block, model-plus-synthetic-kernel materializations are115,193,500, below the previously
priced115,584,000; actual early cutoffs retain their smaller counts. The original full
bill remains canonical and all actual attempts, CPU, RSS and generated bytes will be
recorded. A technical correctness discrepancy permits a proportionate, prospectively
counted repair; it neither authorizes a new scientific panel nor changes deadline
fallbacks into retries.


<a id="b01-source-checks"></a>
## 2026-10-01 07:48 UTC — published-source checks and actual-node preparation

Source `9b6f493b343c2939b374a1ce21384266d3257456` is published. The single frozen
pure/synthetic pytest invocation on configured `local_linux` passed all43 tests:
13.187272507988382s wrapper wall,7.948977999999999s child CPU and258648KiB peak child
RSS. [Config and compact telemetry](../../../../runs/uav_radio_uncertainty/b01_source_checks_a01/summary.json)
and its `config.json`/`pytest.txt` preserve the exact argv and complete output. This
consumed393500 synthetic normal materializations, zero native episodes and zero
current-C queries. The eight manager/reader attempts completed32832 candidate fleet
scores and8014 candidate fleet updates per side, with actual partial prefixes retained;
the deliberate altered-noise rejection retained its paid block. The unrelated dependency
warnings are deprecations. The pytest lifecycle removed its successful scratch. This
accepts the implemented numerical/lifecycle checks, not the native host or scientific
hypothesis; no synthetic timing is a deployment timing measurement.

The four fixed H8 episodes and selected complete worker/reader use configured
`wsl_4070`. The read-only destination probe reported about14.5GiB available and no
active CPU load; fresh runner-side memory admission remains required at each actual
launch. An attempted canonical fast-forward refused its existing dirty control files;
no overwrite, sparse-selection change or whole-tree update occurred. Root reconciled
the canonical control at `/home/wu/projects/HMASD` under its main-writer lock by adding
only the published direction row (1376bytes) from9b6f493b. Its inverse-byte check retained
all other RESEARCH bytes; SHA256 changed03950de7eb0c0537924108d00cc43290ee71402146ec7168b9e97a34ee242e53
to2bbc7098aebea4d92530e8f1a27f90cc685a6d5fc57885b2c8bfa8911b24e848. Pause is lifted;
this direction is exploring with lead `Codex DM (native child)`. Canonical HEAD remains
570fd45646ea62f4e28d86c74770e835b2e0a963. Its maintained compute/launcher overlays are
byte-identical to9b6f493b (SHA2562bb704e31e08a6a3489e80ea6851826740dfbf71461e0f7e70c4394694e65e6f
and6a22fef75e7bbc0997b2f4b0096d278de793d43e466497b36bba49884cab23f9). Existing Git auto-GC/
gitstatus warnings remain unrelated unresolved control observations. Source uses the
launcher's immutable snapshot, without altering the retained canonical checkout.
No H8/main scientific operation had yet been accepted at this preparation boundary.


<a id="b01-native-correctness"></a>
## 2026-10-01 07:50 UTC — four fixed H8 episodes verified

The [native manifest](../../../../runs/uav_radio_uncertainty/b01_correctness_a01/launch-manifest.json)
binds the accepted9b6f493b snapshot, actual node, command and operation. The first
`agent-task` shell invocation lost nested quoting and failed before opening the launch
kernel (`/home/wu/scripts/hmasd_launch.py` absent); its supervisor exited2 and the run
output did not exist. The corrected supervisor command preserved one shell command
argument, then obtained this single native acceptance. That shell failure consumed no
scientific query and created no scientific operation or duplicate attempt.

The accepted check exited0 with consistent terminal witness and both native processes
absent. The complete [summary](../../../../runs/uav_radio_uncertainty/b01_correctness_a01/summary.json)
reports VERIFIED_COMPLETE: three constructors/discarded constructor resets, four explicit
H8 resets,32 steps,20 current-C queries,7250 physical normals,805 geometry uniforms,
eight mask refreshes and200 sounding slots,0fits/updates. All three discarded snapshots,
old/sigma0 exact equality, the two managed episodes, all actually computed candidate
particles, both C passes and all native/outcome audits passed. No extra reset, episode,
world, benchmark or repair was needed. The reader made40 current-C calls,7250 physical
normals,47 native SINR/grant states,16665 candidate fleet scores and4455 candidate fleet
updates. U made56000 model-normal materializations on each worker/reader side. The four
managed decisions all completed within the fixed deadline; this tiny correctness fixture
is not a deployment-performance estimate or an efficacy panel.

Check process wall5.022877895040438s,CPU4.511872s,waited-childCPU.004657s,peakRSS419276KiB.
Canonical NPZ evidence is330780bytes across nine files at the manifest's remote output
root; the complete summary lists each absolute path,size and SHA256. All are retained
there, without a second raw-data copy. Its eight top-level compact/native record files
were collected and hash/size verified locally; summarySHA256
c1cfbd65658bf5385e390f8f8d4ee03796e5679c2376f4a41a5007aa27399818.
The same-session observer registered generation59 and read READY. Its queue delivery
was rejected for a native child(-32600); this continuously active child drained the
terminal fact directly and rearmed generation60 without restarting the worker.

I accept the fixed correctness boundary. The already-selected32-world complete P/U32
worker and full independent reader remain the next operations at the unchanged source,
seeds,clock,particle count and cost. Correctness observations do not alter that plan.


### 2026-10-01 07:52 UTC — selected complete worker accepted

The [main native manifest](../../../../runs/uav_radio_uncertainty/b01_correlated_shadow_a01/launch-manifest.json)
records the accepted unchanged9b6f493b source and frozen32-world invocation. Destination
memory/source/current-policy admission passed. Same-session deterministic observation
uses that exact operation; this native child remains active through terminal collection
and full reading. Registration alone is not a completed experiment. No additional panel,
fit, tuning query, revised deadline or particle-count choice is selected.


### 2026-10-01 08:02 UTC — complete worker collected; full reader accepted

The main worker exited0 with consistent terminal witness and both native processes
absent. The original659764byte summary remains at its canonical remote run root,
SHA2566dca1d6ed767d689b36bcd7aa932e8076a616613ececfeadafb111a03341c140;
a verified temporary local reading copy is under this direction's scratch. All64
H256 episodes completed:16384 native steps,20480 current-C queries,4112250 physical
normals,4096 full manager decisions and zero fits/updates. U generated57344000 model
normals. Both managers completed475136 logical requests collectively,326045 actual
candidate batches,20529026 candidate fleet scores and5132256500 candidate SINR entries;
all actual partial-work counters remain in the original summary. Canonical NPZ artifacts
total150807102bytes, with every file bound by the summary's size/SHA256. No second raw
copy was made. Process resources:380.244082554942s wall,392.74938399999996s CPU,
.001143s waited-childCPU and426208KiB peak process RSS. These are worker measurements;
full reading, source preparation and support are additional work.

Worker observation generation61 returned READY; native-child queue delivery again
rejected(-32600), and this active child drained and rearmed generation62. The
[full reader manifest](../../../../runs/uav_radio_uncertainty/b01_correlated_shadow_read_a01/launch-manifest.json)
binds its accepted unchanged9b6f493b input, original worker hash/source, current
policy and fresh actual-node admission. It creates no native episode, reset or fit;
it performs the already priced complete independent reconstruction. Its same-session
observer is armed against that exact operation. The worker's scores are provisional
until that reader finishes. Independent ResearchCritic reading of the original complete
contract, source and worker evidence has begun in the existing separate reviewer context;
it receives terminal reader evidence before any unconditional scientific disposition.
No result-dependent source, comparator, deadline or particle count has changed.


### Live source consumer reported during complete reading

Root selected the separate `uav_radio_information_cost` P_FULL/P_PRIOR acquisition
comparison under `/root/dm_parent_adaptation`. That direction owns disjoint paths and
uses the published9b6f493b `environment.py`, `randomness.py` and genuinely unchanged
helpers by exact hash, without editing or forking the physical host. Its own codec,
manager and integration fixtures are separate. It may reuse the published4020c5c24
physical-lifecycle correctness. This is a concrete live consumer to preserve during
RF cleanup, not an extra arm/query, changed source or scope extension of this study.


### Completed correctness snapshot reclaimed during independent reading

After the complete H8 result/hash verification, the supported native snapshot collector
previewed and removed exactly
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/2df8b39b75684520824fa178ccb43788`.
It checked the terminal claim, absent processes/consumers, clean source and durable Git
reachability, using the configured passwordless read-only process scan. Allocated bytes
were818282496 before and0 after; the directory and Git worktree registration are absent.
Net measured reclamation:818282496bytes, with no relocated/archived copy. The canonical
H8 summary still matches its original SHA256 and all nine bound evidence files remain
outside that snapshot. Main worker/reader snapshots and the live acquisition direction's
published source dependencies were untouched. Existing shell gitstatus warnings did not
block this successful cleanup.


Reader observer generation63 reached its bounded checkpoint with the same native
operation still running. Direct drain/rearm advanced observation to generation64;
no worker or reader restarted. Its saved progress at this checkpoint had verified37/64
episodes and11536772 candidate fleet scores without discrepancy (1518.382731s process
CPU,1475.2596817531157s wall,401740KiB peak RSS). This is partial verification, not a
complete scientific result. The Scientific Reviewer has completed its original-source
and saved-witness reading, awaiting terminal audit evidence; it created no scratch,
downloads or duplicate evidence, and released its raw consumers. Its reading support
was unmetered, not zero-cost.


<a id="b01-complete-reading"></a>
## 2026-10-01 08:48 UTC — complete independent numerical reading

The unchanged full reader exited0 with a consistent native witness and both processes
absent. Its original [reading.json](../../../../runs/uav_radio_uncertainty/b01_correlated_shadow_read_a01/reading.json)
is277952bytes, SHA256099d634bc5ee3536193f36e3e2a76382ca9cb6e0edf9d8f9448d52bab38721dd,
collected with size/hash verification. It reports VERIFIED_COMPLETE: all64 episodes,
the discarded constructor,4096 decisions,20529026 original scalar candidate fleet
scores,5132256500 candidate SINR entries,57344000 model-normal materializations,
4112250 physical normals,20545 native radio/observation states,40960 current-C audit
calls,7475 geometry uniforms and819200 per-user age updates. All saved gaps, including
initial/terminal censoring, and every paired scalar summary passed. No new environment,
native reset/step, fit or optimizer update was used by the reader. There was no failed
reference prefix, numerical discrepancy, source correction or repeat.

I read the complete structured report and checked all64 ordered episode identities,
verified flags, raw bindings and per-episode model counts against the bound worker;
its full paired and physical/model totals match, and each source-C counter is exactly
twice the worker's. This final structural check used only saved JSON, no scientific
kernel. Reader process CPU2761.467347s,wall2678.822373185074s,waited-childCPU.004582s,
peakRSS402112KiB. The full reader is additional verification cost, distinct from the
worker's intrinsic decision computation. Source/adviser/support work remains incompletely
metered rather than free. Observation generation64's terminal fact was drained directly,
consumed into generation65 and observation stopped; no operation was restarted or queued
to another task. The complete terminal evidence has been sent to the existing independent
ResearchCritic for its final interpretation and disposition.


### Paired endpoints, exposure and cost

The compact [result.json](../../../../runs/uav_radio_uncertainty/b01_correlated_shadow_a01/result.json)
is an exact projection of the already-verified worker JSON, retaining every paired scalar's
32 world values, level/contrast summaries, full work counters, runtime and all129 canonical
artifact identities. It also binds the complete reader and its costs. The projection was
checked against the worker/reader without another scientific kernel or counterfactual query.
The original659764byte worker summary remains remote at its recorded path/hash; this compact
projection does not replace or silently rewrite it. The per-user arrays and full gap records
remain in that summary and its hash-bound canonical outcomes/NPZ files.

The fixed primary is complete payload-J/256. Worlds are the32 independent paired units;
the intervals below are the declared descriptive mean±1.96SE, not simultaneous confidence
coverage, training replication or confirmatory inference. Positive waiting/gap differences
are adverse. P/U32 levels and U32−P follow:

| Endpoint | P | U32 | Difference [descriptive interval] |
| --- | ---: | ---: | ---: |
| Payload J | .444107595 | .451637183 | +.007529588 [+.004058439,+.011000736] |
| Raw J | .455542010 | .463229479 | +.007687470 [+.004121300,+.011253639] |
| Payload served/tick | 26.966027832 | 27.225659180 | +.259631348 [−.034785562,+.554048257] |
| Raw served/tick | 27.660156250 | 27.924072266 | +.263916016 [−.038355944,+.566187975] |
| Payload quality | .221944017 | .234926514 | +.012982496 [+.006254137,+.019710856] |
| Mean user age | 1.915839844 | 2.856250000 | +.940410156 [+.135011600,+1.745808713] |
| Worst-user mean age F | 6.822631836 | 11.552856445 | +4.730224609 [+1.327564410,+8.132884809] |
| Maximum unserved gap | 39.968750 | 58.375000 | +18.406250 [+6.763120,+30.049380] |
| Maximum closed gap | 39.343750 | 53.937500 | +14.593750 [+4.205668,+24.981832] |
| Maximum right-censored gap | 17.281250 | 28.625000 | +11.343750 [+.844519,+21.842981] |
| Mean per-user maximum gap | 14.791875 | 18.805625 | +4.013750 [+.600561,+7.426939] |
| Service p10 | 24.343750 | 25.218750 | +.875000 [−.026799,+1.776799] |
| Mean UAV path, metres | 6680.578509 | 6231.543159 | −449.035350 [−832.599127,−65.471574] |
| Transmitter-on UAV-ticks | 869.343750 | 811.906250 | −57.437500 [−76.737838,−38.137162] |

Payload-J improves in26worlds and declines in6:29641000,29641003,29641009,
29641017,29641021and29641031.
All32 signed primary, service, waiting, resource and companion values are retained in
result.json; no adverse world was filtered. Maximum unserved gap worsens in22worlds,
improves in9 and ties in1; mean age worsens in26 and improves in6. There are no fleet-wide
zero-service ticks or never-served users in either arm. Mean episode minimum served is
14.8125/15.25, with U−P+.4375 [−.001983,+.876983]; this does not establish a service floor
or continuity guarantee. Sensor clipping/saturation counts are zero for both arms.

All4096whole C-plus-manager rounds complete within1.336s. The maximum actually observed
round wall is P .049592430s/U32 .253561227s; mean per-episode accumulated round wall is
1.382269930s/9.435088751s and round CPU1.431300776s/9.757962022s. These are measured
node/runtime outcomes, not an equal-work speed comparison against the historical scalar
proxy or a deadline guarantee on other machines. Per episode, both transmit24000report
bytes plus1024command bytes, with400setup-map bytes,3200sounding slots/6.4s and249.6
payload-weighted ticks. Positive .9 report-tick service still resets the discrete age;
no sub-tick continuity or hardware calibration was tested. Delivered command changes
from each arm's previous command average63.4375/62.90625 per episode, and mask changes
20.46875/15.34375. These are within-arm changes, not same-state causal ablations.

The main worker/reader sum is3154.216731process CPU-s. Including the fixed H8 process
and the published source-test child gives3166.677581measured CPU-s, with waited-child
CPU and incompletely metered preparation/adviser/support work separately retained.
Source/H8/main/reader invocation wall sums to3077.276606s; this sum is not batch elapsed
or occupied-node time. Per-process peak RSS values are not summed as a simultaneous peak.
The full scientific/native exposure is64H256+4H8 episodes,16416native steps,0fits/updates;
all required constructor/discarded-reset and pure-check exposure remains above. Main
worker/reader each uses20529026candidate fleet scores and5132256500SINR entries; model
normal materializations are57344000per side. Including H8 and the bounded source suite,
model-plus-synthetic normal materializations total115193500, within the priced ceiling.
Worker+reader current-C calls total61500including H8. Verification is paid work distinct
from the controller's intrinsic search. No failed native episode, repair panel, repeated
fit or changed scientific rule was hidden in those totals.


<a id="b01-independent-review-and-disposition"></a>
## 2026-10-01 09:00 UTC — complete independent scientific review and disposition

The existing ResearchCritic (`scientific_reading`, configured Astra/max role) received the
original selected question, source contract, supportive/adverse sources and complete
worker/reader evidence. Its original context was separate; this follow-up reused that
context, as the reviewer explicitly discloses. Its full answer is preserved below before
my resolution. It generated no extra experiment or numerical-reader run and holds no live
raw-data, process or scratch consumer.

### Original reviewer answer

I recommend **retaining U32’s conditional payload-J capability, closing this fixed purchase, and buying no automatic replication or repair**. The result is an active package benefit with substantial user-waiting costs. Those costs constrain adoption; they do not retroactively change the prespecified payload-J endpoint.

This follow-up reused the existing separate reviewer context. I reconstructed the result before considering the recorded interpretation and prior advice; this was not a fresh blinded review of the study.

The frozen source is `9b6f493b343c2939b374a1ce21384266d3257456`. The [config](/home/fires/hmasd-wsl/runs/uav_radio_uncertainty/b01_correlated_shadow_a01/config.json), launch manifests and terminal [reading.json](/home/fires/hmasd-wsl/runs/uav_radio_uncertainty/b01_correlated_shadow_read_a01/reading.json) agree. The original worker summary at `/home/wu/projects/HMASD/runs/uav_radio_uncertainty/b01_correlated_shadow_a01/summary.json` matches SHA256 `6dca1d6ed767d689b36bcd7aa932e8076a616613ececfeadafb111a03341c140`.

All 32 paired worlds completed. The fixed primary reading is:

| Outcome | P | U32 | U32−P, descriptive 1.96-SE interval |
|---|---:|---:|---:|
| Payload J/256 | 0.444108 | 0.451637 | **+0.007530 [0.004058, 0.011001]** |
| Payload served/tick | 26.9660 | 27.2257 | +0.2596 [−0.0348, 0.5540] |
| Mean user age | 1.9158 | 2.8563 | **+0.9404 [0.1350, 1.7458]** |
| Maximum unserved gap | 39.9688 | 58.3750 | **+18.4063 [6.7631, 30.0494]** |
| Worst-user mean age | 6.8226 | 11.5529 | **+4.7302 [1.3276, 8.1329]** |

Payload J improved in **26 worlds and declined in six**. Its service-count companion remains uncertain around zero; the quality increment contributes to the objective benefit. Neither arm had a fleet-wide zero-service tick or a never-served user, but those coarse facts plainly do not establish satisfactory continuity.

I directly inspected hash-matched raw and saved outcome artifacts for worlds `29641005`, `29641019`, `29641020` and `29641031`, under the worker’s `raw/` and `outcomes/` directories:

- **Strongest objective gain, world 29641005:** payload J increased **0.0324744** and raw service increased **1.953125 users/tick**. Nevertheless, maximum gap rose **28→129 ticks**. U32’s user 28 had a **closed** gap `[118,247)`, so terminal censoring cannot explain away this harm.
- **World 29641019:** payload J increased **0.0180351**, while maximum gap rose **44→138** and mean age **1.8752→12.4266**. U32’s user 34 remained unserved over `[118,256)`. That is a right-censored 138-tick observed gap, not evidence that service resumed at 256.
- **World 29641020:** payload J increased **0.0109988**, alongside a **closed 127-tick gap** for user 48, versus P’s maximum of 29.
- **Strongest objective loss, world 29641031:** payload J declined **0.0163034** and raw service declined **1.554688 users/tick**, even though maximum gap improved **51→35**. Neither policy dominates every world or every service criterion.

The proposed nonlinear-integration explanation receives useful, bounded support. P is a competent ordinary comparator: it receives the same measurements, known stochastic law, search rights and delivery budget, and uses analytic expected received powers. U32’s gain therefore cannot be dismissed as merely correcting an uninformed free-space baseline. All **4,096 manager decisions met the deadline**, and delivered command/mask changes were frequent. This is not nonactivation or fallback-dominated evidence.

The result establishes the **finite U32 program’s** increment, however. It does not isolate exact expectation integration from finite Monte Carlo selection, different adaptive search paths or subsequent policy–trajectory interaction. The 32 particles are nested calculations, not independent experimental replication; there are 32 paired worlds and zero training fits.

The strongest consequential limitation is the interaction between **the native objective and the host’s persistence law**. J contains service and quality, but no individual waiting penalty. U32 used fewer transmitter-on ticks and less travel on average. The saved stationary ending in world 29641019 is consistent with concentrating service on a persistent beneficiary set. Because this host freezes channel residuals during hover, persistence may help both the objective gain and prolonged exclusion. That is a plausible constructive explanation and limitation, not an identified causal decomposition. The closed adverse gaps also show that censoring alone is not the explanation.

The prior deadline concern is weakened for this implementation on the measured node. Mean whole-round computation accumulated per mission was **1.3823 s for P versus 9.4351 s for U32**, with no decision exceeding its 1.336-second allowance. This does not establish performance on another computer or a controlled speedup over historical scalar estimates.

The actual bill is substantial but below the original numerical-runtime forecast:

- **Zero fits/updates; 64 H256 scientific episodes and 16,384 steps**, plus four H8 correctness episodes and 32 steps.
- Worker: **380.244 s wall, 392.749 s CPU**, peak RSS **426,208 KiB**.
- Full numerical reader: **2,678.822 s wall, 2,761.467 s CPU**, peak RSS **402,112 KiB**.
- Correctness: **4.512 s CPU**; published synthetic tests: **7.949 s child CPU**.
- Main canonical NPZ evidence: **150,807,102 bytes**; correctness NPZ evidence: **330,780 bytes**.
- Worker and reader each processed **20,529,026 candidate fleet scores**. Verification cost must remain separate from intrinsic controller computation.
- Both programs paid the declared measurement, traffic, sounding and delivery charges. Source/adviser/support work and the separate launch-shell failure’s overhead remain incompletely metered, not free. Terminal scientific rows contain no failed native episode.

My correction is to retain the result as **conditional ordinary cooperative-control capability**, with its adverse continuity witnesses attached. Do not call it service preservation, field validity, learning, or evidence that the common sensing package pays for itself. Equally, do not discard the positive merely because a different adoption criterion would reject it.

**No additional native observation is worth purchasing automatically here.** The already-owned `uav_radio_information_cost` P_FULL/P_PRIOR comparison is the smallest currently selected complete observation addressing a consequential missing premise: whether buying this central CSI package benefits ordinary control after its acquisition and timing costs.

Its possible outcomes change different judgments:

- A favorable complete result would strengthen the case for purchasing that information under its declared comparator and service tradeoffs.
- An adverse or unresolved result would require any future deployment case for U32 to confront a cheaper ordinary reference directly.
- Neither outcome can be added algebraically to U32−P, nor establishes U32’s performance without the common sensor. Any resulting integrated comparison needs its own prospective contract and complete price; this review selects none.

I checked source governing physical-channel lifecycle, separated random streams, moments/particles, wire information, deadlines and outcome reading; all signed primary world effects and consequential companion summaries; terminal audit identities/counts; and the positive/adverse artifacts named above. I did **not** rerun numerical readers, generate new scientific calculations, independently reproduce every candidate score, validate physical calibration, or establish an acceptable user-waiting threshold. The completed numerical audit and engineering review retain those distinct responsibilities. I created no scratch or duplicate evidence and hold no live raw-file consumer.

**MATERIAL_DISSENT: no** — retain the bounded positive and complete adverse evidence, close the fixed purchase, and make no automatic new investment.

### DM resolution and changed explanation

I accept that recommendation without a material scientific disagreement. The prospective
positive payload-J prediction is supported conditionally by the finite complete P/U32
comparison, with26positive/6adverse worlds. The anticipated numerical-cost risk did not
turn into deadline failure on the actual node; this weakens the claim that U32 is currently
unusable under this clock. The previously unmeasured complete benefit is now an active
ordinary capability. The service-count gain remains unresolved and the new adverse
waiting evidence blocks any service-preserving or broad default-adoption interpretation.
The prespecified J result is retained; waiting harms do not retroactively change its endpoint.

The useful explanation is narrower than exact-expectation superiority: integrating joint
RF trajectories with the declared finite search changes native outcomes relative to a
matched informed expected-power controller. Finite sampling/search-path and subsequent
trajectory interactions remain unseparated. Neither common-sensor acquisition value nor
channel-field validity was compared. The absence of an individual waiting term, native
greedy grants and hover-persistent residuals plausibly help explain stable beneficiary
sets; no new suffix replay or modified model was bought to isolate those links. The
closed129/127tick exclusions mean that terminal censoring cannot be their sole cause.
Fewer Tx ticks/path length remain measured exposure, not battery or hardware-energy gains.

This updates the shared nonlinear-model/decision-value judgment without overturning
finite_model_decision_value B02: a distinct complete RF-realization comparison now has a
positive conditional objective increment, while that persistent-parameter/hidden-peer
study's unresolved U−P results remain valid. Deterministic-host continuity failures are
still not diagnosed as RF-model error. Representation and actual action use are established;
learnability was not tested, and a method novelty or field-use claim is not selected.

For next investment I compared unchanged replication, more particles/another deadline,
a continuity-focused revision and ending the fixed purchase. Repetition could refine this
population effect, but does not answer whether the common information package is worth
buying or supply an acceptable service/waiting contract. Particle/deadline changes have no
observed failure here to repair. A continuity-constrained full controller could be useful,
but would change the objective/comparator, require a competent ordinary controller with the
same information/resources, and pay a fresh complete comparison; its usefulness is currently
a conjecture, not a consequence of this positive J result. The concrete already-owned
P_FULL/P_PRIOR study addresses information purchase. It is independent work under the other
lead, not another arm of this study, not a dependency required to close it, and its effects
cannot be added to U32−P. Any later integrated comparison belongs to Root's cross-question
selection with its own prospective price. No conditional experiment is silently registered.

I therefore close B01 with U32 as a conditional payload-objective option, P as its cheaper
matched reference, all waiting/service tradeoffs and canonical positive/adverse evidence
retained. There is no new fit, native panel, open adviser, queued producer or automatic
repair here. The broader question remains open. Concrete re-entry would require a selected
use decision with a specified continuity criterion or a direct cheaper-reference comparison,
not simply an invitation to repeat the positive. The one adequate independent reading
covers this scoped closure; no distinct unresolved disagreement warrants a second Pro pass.


<a id="b01-final-cleanup"></a>
## 2026-10-01 09:04 UTC — published evidence and measured closure

Complete outcomes, the numerical reader and full original scientific advice/disposition
are published at `1e363409be4502f81fb1f91a847d83162a38a325`. Useful P/U32 source remains
published at9b6f493b. Direct import inspection confirms a live selected consumer in
`uav_radio_information_cost/b01`: its host, model, protocol, I/O and readers use this
package. The conditional U32 capability, its executable checks and the independent
readers also remain useful retained code. No source file was deleted or refactored
under that consumer; no required canonical positive/adverse evidence was discarded.

The supported exact-target collector previewed then reclaimed the worker and reader
source snapshots after checking terminal identities, clean inputs, process references
and durable Git reachability. Their directories and worktree registrations are absent.
Deleted targets, measured allocated bytes before→after:

- `/home/wu/projects/HMASD/.git/hmasd-launch-sources/2df8b39b75684520824fa178ccb43788`
  (the earlier completed H8 cleanup):818282496→0.
- `/home/wu/projects/HMASD/.git/hmasd-launch-sources/58bb94a971024c3eb35b5215eaa224ef`
  (main worker):818274304→0.
- `/home/wu/projects/HMASD/.git/hmasd-launch-sources/c7d012083adb4ec3a05a57514b71f91d`
  (full reader):818282496→0.
- `/home/fires/hmasd-wsl/temp/directions/uav_radio_uncertainty/`:688128→0.
  This held the verified temporary worker-summary copy, three consumed observer-request
  files and empty primary/tests directories.
- Empty local `stdout.log`/`stderr.log` in the correctness, main-worker and reader run
  directories were removed; these six redundant zero-byte files reclaimed0allocated bytes.

Net measured allocation reclaimed across those targets is**2455527424bytes**;
there is no moved/archive copy or concrete cleanup blocker. This is target allocated
usage, not a claim about Git-object pruning or total filesystem capacity. The
[cleanup record](../../../../runs/uav_radio_uncertainty/b01_correlated_shadow_a01/cleanup.json)
contains before/after values and exact current collector results. After removal, all129
canonical main artifacts were rehashed successfully (150807102bytes), and the worker
summary and reader still match their recorded hashes. The nine unique H8 evidence files
(330780bytes) remain in their canonical remote run root. These retained files support
the complete fixed contract, positive/adverse traces and active host consumer; no second
raw-data copy was created. Compact local Git evidence is retained, including the exact
165233byte result projection and277952byte original reader report.

The final same-session observer drain shows generation65,stopped=true,no unconsumed
events and all three RF operation statuses ready. Workers/readers are terminal, no
scientific helper holds a raw-data consumer and no open adviser remains. Publication
of the direction standing and changed shared-model judgment follows this closure on
shared main. This is a complete read result; no collection or interpretation is pending.


### 2026-10-01 09:10 UTC — concurrent acquisition result read before standing publication

While I waited for the other direction's shared-index transaction, its complete
P_FULL/P_PRIOR evidence and original independent scientific diagnosis were published at
[0052b7dd5de658ac24b911a3ca9847a5602d632f](https://github.com/CartmanFatass/My-paper-code/blob/0052b7dd5de658ac24b911a3ca9847a5602d632f/docs/research/candidates/uav_radio_information_cost/NOTES.md#b01-complete-reading).
I read its full paired results, cost, opposite censored tails, original critique and DM
resolution. FULL−PRIOR payload-J is −.015929915 [−.019169458,−.012690371], negative in
all32 new worlds including a near tie; payload service is −.994323730/tick. FULL has
scoped waiting positives, with opposite203/150tick right-censored adverse spells across
both arms. Its current lead closed the fixed purchase and released all active source,
worker/reader/critic consumers; the useful acquisition code and its exact RF imports
remain retained. No source or evidence of that direction was changed here.

This realizes the adverse branch already addressed by my original reviewer above. It
strengthens the need for any eventual U32 deployment claim to confront the cheaper
ordinary PRIOR package directly. It does not invalidate the measured U32−P increment,
identify a shared causal failure or supply a direct U32−PRIOR effect. The panels,
information acquisition and timing differ; no arithmetic addition/subtraction of their
effects is a tested controller comparison. My adopted closure and conditional capability
standing therefore remain unchanged. No extra fit, query, reduction, new review round or
successor is selected; Root owns the next cross-question allocation. The broad acquisition
question is now also idle, so it is neither a pending producer nor a dependency of this
completed RF study. Retained reusable P/U32 implementation, explicit acquisition imports,
checks and full numerical readers justify keeping the published RF package; no active
operation is asserted by those code dependencies.


<a id="post-b01-source-support"></a>
## 2026-10-01 — one source-only whole-episode policy-search question

RF B01 remains closed exactly as published. Root assigned this same nonarchived DM one
bounded source/complete-price response after the independent Oracle narrowed a candidate.
This is preparation, not direction activation, code implementation or a selected result study.
The current published main is3ecbf6a84 at the first source read. Relevant RESEARCH topics2/4
retain stochastic P0/Bstar/Hdirect competence, actual-S2 and B04–B10 learning adverses and
separate task use from mechanism/learning-population claims. That affects this response:
check actual observation/action/gate semantics, preserve strong ordinary controls and sunk
acquisition, and count complete native search plus numerical reading rather than pricing
only the low-dimensional update. No named old route is reopened by this source question.

Authorized exposure for this response: **zero** new native/controller/model/allocator/RNG/
teacher calls, saved-output reductions, tests, benchmarks, prototypes, implementation,
fits or scientific launches. Reading existing code/records and integer cost arithmetic only.
Unknown activation, initial numerical identity, performance and new runtime stay unknown.
Only this existing notebook is edited; proposed new owned paths await any Root selection.
CodeGraph was used first to locate P0, hidden features and comparator call paths.

### Root's original assignment (verbatim)

Your complete RF B01 result, original scientific diagnosis and published closure are read and retained. Keep its scoped U32 positive/waiting harms and all original stops unchanged; no RF rerun or new result-bearing study is selected. Next source-support assignment for this SAME nonarchived DM: /root/deep_report_review is independently assessing a worthwhile, materially different policy-development question grounded in inherited stochastic competence, ordinary Bstar/Hdirect positives and the cumulative B04–B10/actual-S2 learning adverses. This is distinct from /root/age_control_interface's RF/information/continuity assessment and /root/oracle_next_capability's CJ silence/next-observation question. After that Oracle narrows one candidate, provide ONE complete source-feasibility/cost answer from existing code/records/count arithmetic only: zero new native/controller/model/allocator/RNG/teacher queries, saved-output reductions, tests, benchmarks, prototypes/implementation, fits or scientific launches. Preserve original source request/reply and complete Oracle advice in your existing owned notebook; propose new direction/owned paths before any eventual Root selection. Unknown facts remain unknown without a pilot. It may recommend no purchase; Root selects any new investment after reading the complete advice. Your current RF publication and cleanup stand; no ACK or additional closure work is required.

### Oracle's original source request (verbatim)

Root assigned you the ONE source-and-complete-cost support request for my SOURCE-ONLY policy-development opportunity assessment. One candidate has survived provisional scientific comparison: whole-episode parameter search of a bounded contextual readout on frozen P0, against identically exposed ordinary global calibration. This is NOT a selection, implementation or launch request. Please use existing sources/code/records and count arithmetic only: 0 new native/controller/model/allocator/RNG/teacher queries, saved-output reductions, tests, benchmarks, prototype/implementation, fits or launches. Read CodeGraph first for code mapping as required. Preserve your B01 stop. Return feasibility/source facts and a complete priced contract; unknown runtime stays unknown. Keep complete original exchange and later full final advice/coverage in your existing NOTES, with Root adoption separate. No extra lead/candidate bill or App relay.

Concrete candidate to price (please identify an inconsistency, do not silently substitute a recipe): N5/U50/free-space original all-transmitter-ON H256 host, actor decision every4ticks, original P0 B02 asset and lawful114-field local features/helper/navigation, 27 categorical motion actions and the existing private addressed action tapes. No RF, silence, extra history, centralized actor, new communication or latent public action correlation. Frozen P0 produces logits l0(o) and second hidden vector h(o) in R128. Compute hbar=h/max(1,||h||2). CAL logits are l0/exp(tau)+tanh(b), with tau clipped to[-ln2,+ln2], b27. CONT logits are l0/exp(tau)+tanh(b+W hbar), W27x128. Elementwise tanh, amplitude1. Initial tau,b,W exactly0; actual initial law must be checked under eventual implementation, no policy evaluation now. Temperature plus global bias CAL has28 search parameters; CONT3484. These are separate direct-search centers, no neural gradient/critic/teacher/Adam/auxiliary fit; all P0 body/output asset parameters stay frozen. Shared center controls all5 actors; one parameter perturbation stays fixed for the WHOLE jointly evolving episode, while actions remain independently sampled conditional on actor-local input.

Training exposure: 2 independently randomized paired blocks, each CAL and CONT (4 fits). 16 fixed iterations/fit; 16 isotropic standard-normal directions/iteration; antithetic center +/-0.05 delta; 2 fresh worlds plus action tapes per direction pair (same worlds/tapes within +/- and between CAL/CONT in that block; independent across directions, iterations and the2blocks). Thus64 complete episodes/iteration,1024/fit,4096total,1048576native teamsteps. Search update ARS-V1-style with ALL16 directions, no elite/ranking: for each direction use mean complete J over its2worlds, then center +=0.02/(16*max(population_sd(the32 signed mean Js),1e-8))*sum_k[(Jplus_k-Jminus_k)*delta_k]; project tau to bounds after update; no other projection. No partial-horizon fitness, validation/tuning/checkpoint choice, adaptive budget, KL/entropy regularization, rollout bootstrap or surrogate reward. Final center only. The 2worlds are distinct per direction (512 unique trainworlds/block); pairing is exposure control, not more independent learned replicates. Fixed exploration scale/steps are engineering assumptions, not proven good or a repair diagnosis. Native complete J is exact fitness sample; normalized finite search is not claimed an unbiased gradient of unsmoothed endpoint J.

Evaluation: 32 NEW heldout worlds,2 shared private action tapes, final CONT0/1,CAL0/1 plus frozen P0_ZERO, retained Bstar_ZERO, ordinary Hdirect_ZERO, G and C (8 stochastic programs*64eps + C32 deterministic =544eps; if G actual stochastic/deterministic differs, flag and give exact corrected count). Total planned4640eps/1187840native steps before any source-required extra identity instrumentation. No extra initial native rollouts assumed: law-check source instrumentation during existing training/reader only if meaningful, price any extra requests openly. Primary contrasts paired CONTb-CALb and eachfinal-P0_ZERO/Bstar_ZERO/Hdirect_ZERO, with complete J/service/travel/tails/zero-service readout. Hdirect ordinary model-cost stays charged. Need retained comparator exact source/program semantics, including ZERO original meaning and correct G/C determinism; if described host/reference cannot be reused directly, flag source work, don't query.

Please price: all fitting and endpointnative episodes/steps, world/tape coverage, actor/P0/helper/head/model/solver calls, C/G/Hdirect candidate trajectories and modeledticks, nested searches, search-vector/update CPU-work count, scalar reader/full policy trace reconstruction work, source/FP/RNG/identity correctness support, full worker/reader/support wall+CPU with known anchors versus extrapolation/unknown separated, RSS, output/storage/required retained evidence. Include inherited P0 acquisition and strong comparator acquisition (exact already-paid counts/cost), distinguish sunkshared costs from marginal newstudy cost, and retain B02–B10/adverse ancestry. List no automatic100% action-distribution identity assertion from zero parameters until actual source arithmetic known. Do not run to resolve unknowns. One source-based feasibility and complete bill is sufficient.

### Source correction returned before completing the bill (verbatim)

Source inconsistency found before pricing: retained *_ZERO is a physical transmission gate, not an all-on name. In fleet b10_joint_control/policies.py query, the rotating eligible member requests OFF when capped_count(answer)==0; *_A leaves it ON. This is inherited from B08 and B10 ZERO means can have <100% transmitter exposure. Your all-ON host therefore cannot literally reuse P0_ZERO/Bstar0_ZERO/Hdirect_ZERO unchanged. The all-on references are the original P0/Bstar0/Hdirect or their *_A wrappers. G is stochastic; C is deterministic, so the proposed 544 endpoint episodes still hold if the all-on references are explicitly chosen. I will continue source/count work while leaving that semantic correction for your decision; no policy query or experiment has run.


### Oracle's comparator correction (verbatim)

Thank you; that is a consequential correction. Retain an all-ON training/candidate contract and use P0_A/Bstar_A/Hdirect_A as the exact matched references. Also price the existing P0_ZERO/Bstar_ZERO/Hdirect_ZERO as three explicitly richer action-contract endpoint references, not matched training arms: this avoids excluding the best retained ordinary packages from practical benefit/cost reading. No new silence mechanism or policy development is proposed; they keep their exact frozen B08 semantics. This is a correction of this ONE candidate's comparator identity, not another candidate bill. If the accepted B08 host can run fixed all-ON policies and these frozen gates side by side without changed physics/observation meanings, use it source-only in the bill and identify the authoritative source; flag otherwise. Updated endpoint 11 stochastic programs*64 + C32 =736episodes,4832 total,1236992 teamsteps. Interpretation must separate CONT vs CAL/P0_A/etc under matched action rights from comparison with ZERO under richer rights. No run/query to validate equivalence. Please include all unchanged hidden binding/reader consequences and actual gates' known failures/tails.

### Oracle's normalization correction (verbatim)

One source-only mathematical correction to the SAME candidate, before final pricing: use population SD of the 32 within-pair-centered signed mean returns, i.e. for each direction let d_k=(Jplus_k-Jminus_k)/2 and normalize over {+d_k,-d_k}, rather than SD of raw signed Js across different worlds. The numerator remains sum[(Jplus-Jminus)*delta]; denominator floor1e-8 and0.02/16 coefficient remain. Distinct fresh world pairs across directions remain. This avoids making the update scale depend mainly on unrelated between-world return levels; it does not create an unbiased-gradient claim or variance guarantee. Call it an ARS-inspired paired normalized search, explicitly a declared adaptation, not exact ARS-V1. All episode/model/search-vector counts are unchanged; only this scalar arithmetic contract changes. I have run no outcome reduction/model/probe to choose it. Keep P0 initialization and all earlier fixed bounds/exposure unchanged.

### Oracle's final source-scope reminders (verbatim)

Scientific reading is complete; the full bill/feasibility is the remaining input to my recommendation. Please send your bounded source findings when ready, retaining unknown runtime/storage where sources do not determine them rather than expanding into a probe. I will then return the full final advice/coverage for your existing NOTES as Root requested. A useful accounting observation: proposed training exactly matches B05's already-paid1,048,576 acquisition steps, but it is not a controlled ES-vs-B05 comparison (different parent randomization/data use/parameterization); B04/B10 PPO training was smaller, so no method-efficiency claim.

Root has relayed owner handoff boundary: finish THIS existing bounded source assessment, preserve full answer/exchanges as UNSELECTED successor in your owned NOTES and handoff, then stop; Root will select/launch no next native round before handoff. No broadening/execution. My scientific reasoning is complete; awaiting your bounded complete source price and feasibility gaps. I will send full final original advice/coverage immediately after your bill.

<a id="episode-search-complete-source-price"></a>
### Complete source-feasibility and price reply

**The corrected candidate is source-feasible, with a new search/collector/reader implementation required. It remains UNSELECTED.** The B08 host can retain its all-ON behavior and run frozen ZERO gates in separate episodes without adding actor information or changing physics. The marginal purchase would be **four fits,4,832 H256 episodes and1,236,992 native team steps**, plus the support below. My unbenchmarked allowance is **0.6–2.0 worker CPU-hours +0.75–2.5 full-reader CPU-hours**, approximately **1.5–6 sequential node-wall hours**, and **14–24 focused support-hour equivalents**. These are forecasts, not measurements, ceilings, elapsed Codex hours or authorization. This reply used only source/record reads and count arithmetic: zero new native/controller/model/allocator/RNG/teacher calls, saved-output reductions, tests, benchmarks, prototypes, fits or launches.

**Actual host and policies.** Authoritative sources are `experiments/candidates/uav_fleet_adaptation/b08_local_gate/{environment,collect,policies,fit,reference,physics}.py`, original B02 `{model,policies,controllers}.py`, B07 `targets.py`, transmission B05 `policies.py`, and `envs/pettingzoo/uav_env.py:224`. B08 is the original N5/U50/H256/free-space factory with masking enabled. It preserves layout, motion bounds,27 commands/four-tick holds, greedy grants, radio parameters and104-field observation. A installs all true mask bits. The setter reuses the physical channel generation, changes neither position nor time, and returns a refreshed observation that the collector deliberately discards for the current decision. All five motion queries use OLD returned rows. Source all-true user/peer-radio branches introduce no intended all-ON physics change; this is not a new measured parity result.

ZERO turns OFF only eligible physical slot `(tick//4)%5` for four ticks when `min(count_nonzero(features[3:63].reshape(20,3)[:,2]>0),10)==0`. Every other transmitter is forced ON. That is capped visible own-user count, not granted service. Preserve old-row timing: a previously silent actor can receive a blank row, and mask changes alter subsequent visibility and navigation histories. There is no fitted gate or gate RNG in A/ZERO.

Original B02 P0 is114→128ReLU→128ReLU→27,34,715 FP32 parameters. Its canonical file is `wsl_4070:/home/wu/projects/HMASD/runs/uav_fleet_adaptation/b02_inheritance_a01/assets/S.pt`,424,487bytes,SHA256 `b9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a`, state SHA256 `6fa2eddc542d8f5293f5daf6a989b97a9d7d5f56f484f1eb6bddc6a87d27de0c`, acquired at `e945483b85c7f8ddfc315c57f36938d6c14201c7`. These are existing pinned identities, not a fresh load/rehash. Eventual staging must verify them. Neither B03's checkpoint nor a HIDDEN gate asset is required.

The114 inputs are first103 FP32 observation entries, private navigation one-hot10 and analytic fallback bit; the observation clock is excluded. B08 captures h128 from the second ReLU during the SAME original one-row forward as l0, using a local hook. CONT therefore needs no second P0 forward. Episode-private keys are those ordered103 values plus navigation byte. Actors keep separate navigation/cache, reset each episode; a changed parameter version must never inherit head-output cache entries. The helper is charged analytic model work.

P0_A is original FP64 softmax of FP32 logits. Requested Bstar_A means exactly **Bstar0_A**, the already selected P0 temperature-two law, with no new calibration. Hdirect is `.9*softmax(l0)+.1*one_hot(C)` from the frozen B07/B08 program. It pays full C and P0, reusing C's features rather than adding a standalone helper; its implementation constructs BOTH T/H vectors on every request, including cache hits. G is stochastic: C gets.9 mass, the other26 commands share.1 proportional to `exp((score-max_alternative_score)/.014)`; exact flat scores return Q10. C is deterministic original first-maximum/fallback control. Here G/C are **G_A/C_A**. Every stochastic request draws the addressed private uniform, including hits. Shared episode-fixed parameters change the jointly evolving policies; they add no deployment public action coin.

The retained references have limits. B08's world29831016/tape1 had an all-ON-prefix outage shared by P0_A/P0_ZERO, and Bstar0_A had two consecutive zero-service ticks in29831020/tape1. Its ZERO−A mean-J intervals all crossed zero. B10's three retained ZERO endpoints had no observed zero-service tick and all five ordinary ZERO families improved mean episode-minimum service, while mean-J/service intervals crossed zero. Its severe30012025 common-prefix service `[10,10,10,10]→[1,0,0,0]` adverse belongs to **HIDDEN/INIT90**, not ZERO. Team minima/p10 and finite absence of outages are not individual-user continuity or guarantees.

**Fixed exposure and search.** I use the corrected within-pair-centered scale: `d=(mean_J_plus-mean_J_minus)/2`, population SD over `{+d,-d}`, floor1e-8, unchanged all-direction numerator and.02/16, then center-tau projection. This is the declared ARS-inspired adaptation, not exact ARS-V1 or an unbiased unsmoothed-return gradient.

| Work | Count |
| --- | ---: |
| Paired blocks / fits |2 /4|
| Iterations per fit / all center updates |16 /64|
| Directions per iteration / total vectors |16 /1,024|
| Training episodes / native steps |4,096 /1,048,576|
| Distinct training worlds |512 per block;1,024 total|
| Final stochastic programs |CONT0/1,CAL0/1,P0_A,Bstar0_A,Hdirect_A,G_A,P0_ZERO,Bstar0_ZERO,Hdirect_ZERO|
| Evaluation episodes / steps |11×32×2 + C_A×32 =736 /188,416|
| All episodes / team steps / UAV ticks |4,832 /1,236,992 /6,184,960|
| Scientific resets / extra constructor reset |4,832 /1|
| Team decision clocks / all-agent requests |309,248 /1,546,240|
| Addressed categorical draws |1,536,000; C_A draws0|

Each training world/tape is shared between signs and families in its block; the two worlds per direction are distinct. There are1,024 distinct training world/tape pairs and64 held-out pairs, or348,160 distinct actor-clock innovation addresses if that pairing is implemented exactly. All repeated draw executions remain paid. Held-out32 worlds must be fresh relative to training and earlier development. Average tapes within world; retain each fitted endpoint. There are two paired training units conditional on one P0, not4,832 independent learned replications.

CAL28/CONT3,484 coordinates imply **1,798,144 scalar normal outputs** (14,336 CAL;1,783,808 CONT),3,596,288 signed perturbed coordinates,1,798,144 weighted-coordinate accumulation terms,112,384 center-coordinate writes and64 tau projections. There are2,048 signed two-world fitness means,1,024 pair differences and64 scale reductions over32 signed values each. Full reading repeats direction generation/update arithmetic against pinned domains, saved directions/centers and reconstructed returns. No teacher/critic/gradient/Adam, fitted surrogate, elite search or nested native rollout is present. Training exposure equals fleet B05's1,048,576 acquisition steps; different data use/parents/programs prevent a controlled efficiency claim.

**Worker and full-reader work.** Price one sequential B08-style host, including mask refreshes for A. Omitting repeated A refreshes would be a declared implementation change, not an assumed saving. These are exact requests or conservative no-cache ceilings; actual misses/n/p stay unknown.

| Work in EACH worker and complete policy-replay pass | Count / ceiling |
| --- | ---: |
| Head requests, train+final |1,392,640;696,320 each family|
| Standalone P0/helper requests |1,474,560|
| Frozen one-row P0 forwards including Hdirect |≤1,515,520|
| Standalone helper links |≤206,438,400|
| Full-C family requests |71,680|
| Full-C candidate paths / modeled ticks |≤1,935,360 /≤7,741,440|
| Full-C power links |≤161,996,800|
| All helper+C power links |≤368,435,200|
| Hdirect calls / both T+H vectors |40,960 /81,920|
| G tail reductions |20,480|
| ZERO decisions / gate draws |12,288 /0|

Helper≤140 links/request is `(1+p)n+2n`, n≤20,p≤4, using extrema rather than27-way scoring. C pays27 four-tick paths/108 score reductions per miss and≤108n+(1+p)n=2,260 links. It fixes visible peers/users, calibrates unknown interference and scores current own users; it is not a privileged complete-world solver. There is no additional solver/allocator search beyond C and native/scalar greedy assignment.

CONT costs at most **2,406,481,920** matrix-vector multiply-accumulate terms per pass (696,320×27×128), plus hidden normalization/bias/tanh/temperature/logit/probability work. Both families together have≤37,601,280 tanh outputs per pass. The frozen P0 ceiling entails52,182,384,640 dense multiply-accumulate terms plus biases/activations. These are arithmetic counts, not benchmark FLOPs/CPU. Cache/episode-level reuse can reduce head/norm/temperature calculations; it cannot erase fresh draws and trace checks. Equal native exposure is not equal parameter/computation cost.

Native reset/step states including constructor total1,241,825, costing341,501,875 dense power slots and322,874,500 unique distance-pair evaluations. The309,248 mask installations add85,043,200 dense SINR-refresh slots; distances/powers are reused. Grants and refreshed local observations still execute. All-ON repetitions stay charged.

Full scalar reading adds **1,551,072** scientific initial/poststep/refresh states,7,755,360 local rows,418,789,440 power links,403,278,720 distance pairs,426,544,800 logical dense SINR slots and1,551,072 greedy assignments. The constructor is separate worker overhead. Reader native scientific steps/refits are0. Audit every episode and all1,546,240 decisions: source/assets, geometry/radio/grants/reward/termination, helper/features/nav/cache, original h/logits, head/probabilities/innovations/categories, holds/masks/old-row timing, returns, directions and every center update, final hashes and paired summaries. Existing B08 scalar/reference code is reusable but does not implement the new heads/search. Unlike older limited Adam-ledger checks, this small explicit update can be reconstructed in full. Policy work is a second pass of the table, not free verification.

**Numerical/identity support and freeze gaps.** Preserve the original one-row FP32 P0 order and hook, rather than changing to a batched actor. An explicit proposed binding is FP64 h normalization, head parameters/residuals/logits, fitness and search reductions, then the original FP64 decoder. This is a proposal, not verified source. Still freeze seeds/domains, CAL/CONT direction coupling, reduction order, tau treatment for perturbed policies as well as center projection, finite-value/failure behavior, contrast list and uncertainty rule. No pilot is required to choose those engineering identities.

Zero tau/b/W is mathematically P0 but currently supplies no100% numerical distribution/trajectory identity assertion. I separately price useful optional instrumentation on all already-paid first-iteration contexts:4fits×64episodes×320 = **81,920 zero-head reconstructions per worker and reader**, reusing paid l0/h with0 additional P0 forwards/native steps/RNG draws. Half are CONT, adding≤141,557,760 zero-W multiply-accumulate terms per pass. Compare original probabilities, same-innovation category and clipped physical command and retain actual errors/aliases. This is observed-context initialization fidelity, not a separate initial-policy rollout, proof for all inputs or causal shadow outcome. Record the initial zero center regardless of whether this optional instrumentation is selected.

Synthetic shape/finite/address/cache/antithetic/normalization/projection/failure/tamper checks and independent numerical/RNG engineering review are included in support. A selected DM must prospectively name finite fixtures in L0; an unwritten suite has no honest exact call count yet. Forecast **0.01–0.05 CPU-hours** for these checks/imports. This bill includes **zero extra native/canonical-P0 correctness episodes**: use synthetic fixtures and existing paid training/reader contexts. Any demonstrated need for a native correctness stream must be separately priced before exposure. No hidden pilot is included. Source/advice, staging/hash checks/admission/transfer/publication/cleanup also cost incompletely metered support.

The request fixes14 matched primary contrasts:2CONTb−CALb and four endpoints versus the3 matched A references. Richer endpoints are added, but the full contrast list is not yet explicit. Four endpoints versus all8 references plus2paired contrasts gives34; adding3ZERO−A gives37. These are options on the same paid panel, not selected analyses. B08's20,000 shared world-bootstrap is reusable if explicitly chosen. Keep blocks and signed world vectors separate. Native p10/minimum/zero measures are team-service tails; individual-user waiting would be an explicitly added derived reading.

**Forecast resources and required evidence.** Published B08 measured638.832 worker+849.524 reader CPU-s for1,984 episodes, peak566,320KiB; B10 measured860.761+918.283 for1,376, peak731,560KiB. B10 P0_A/Bstar0_A/Hdirect_A/G_A/C_A episode CPU means were.385111/.442751/.429654/.367979/.259080s. These are other programs/trajectories/hosts under observed load, not a benchmark here. Episode-count scaling alone gives worker1,556–3,023s and reader2,069–3,225s; new head/trace/replay/cache/I/O costs are unknown. My broader0.6–2.0worker/0.75–2.5reader CPU-hour allowance is not a guarantee. Including synthetic support gives **1.36–4.55 marginal machine CPU-hours**, before unmetered source/staging/final-write work. Actual node admission remains necessary only if a launch is selected.

Budget **0.5–1.5GiB RSS per sequential process**, streaming episodes rather than retaining all raw. Direction vectors in FP64 occupy14,385,152bytes; all17centers for each of four fits occupy955,264bytes. Keep these once with per-episode fitness/provenance/update ledgers; signed parameter vectors and duplicate finals are reconstructible/referencable. P0's original asset is424,487bytes; its parameter array payload is138,860bytes. Runtime/caches dominate these small arrays.

Retain one complete canonical raw set: coordinates/users, observations, native radio/grants/reward/termination, masks and refresh evidence, features/P0 logits/h/probabilities/innovations/nav, attempt/timing/cost counters and bound head/center/direction identities. Reconstruct hbar/residuals rather than retain duplicate arrays unnecessarily. Preserve partial failures and all adverse outcomes. A B08/B10-like schema suggests **9–12GB uncompressed,3–6GB compressed** evidence; trace schema/compression is unknown. B10's2,876,729,536 uncompressed/998,859,132 compressed raw bytes scale to10.10GB/3.51GB only as a planning proxy. Allow12–16GB available output/scratch space for serialization, one accepted snapshot and compact records. Keep one necessary bulk copy; publish compact hashed records and reclaim transients after consumer checks.

The **14–24 focused support-hour-equivalent** estimate covers new search/collector implementation, full physics/policy/update reader, FP/RNG checks and engineering review, complete scientific reading/publication/cleanup. It is not measured labor, model-hours, remaining budget or fit permission. Sunk/shared acquisition remains incurred:

- **P0 B02:**1fit;128C roll-in+64+64aggregation =256training episodes/65,536steps,81,920 labels,8,000updates/4,096,000 presentations. Its192final episodes make448/114,688steps total. Worker/reader CPU101.990390+5.553432=107.543822s; wall100.363925+5.227979=105.591904s. That reader was much lighter. Prior teacher/support cost is additional.
- **Bstar0:** B04's8candidates×32worlds calibration paid256episodes/65,536steps,40,960C-family and40,960P0-family requests,61,440stochastic draws,0new neural fit. Its32world final arm added8,192steps. Published two-lineage calibration CPU139.828009s is aggregate; inspected records supply no separate Bstar0-only CPU. Do not halve it as a measurement. Whole B04 cost2actor–critic fits,2calibrations,1,312episodes/335,872steps/517.602806chain CPU-s. B03/P1 is historical evidence, not a needed asset here.
- **Hdirect/G/ZERO:**0new fits/calibrations to reuse the laws, with prior development/evaluation paid. Fleet B07's2target fits/672new episodes/172,032steps/16,000updates/8,192,000presentations/560.463chain CPU-s supplied Hdirect/Tdirect and the failed amortization comparison; Hdirect needs neither fitted endpoint. Transmission B05 supplied G with0fits/416episodes/106,496steps/140.041chain CPU-s. B08 paid2ridge fits/1,984episodes/507,904steps/1,488.812103chain CPU-s; ZERO needs neither acquired labels nor HIDDEN. Do not rebuy these studies as prerequisites or declare their historical computation free.

Fleet **B02–B10 totals22fits,2calibrations/4,055,080native steps**, already including the named fleet studies; do not add them again. Older B01's2fits/576,000steps/31,190.348worker+reader CPU-s remains separate. Actual-S2 parent B09 is another adverse under a different contract, not included by making these one cost/treatment. This candidate would ADD4fits/1,236,992steps if selected. Preserve B04 active full-policy losses, B05 consequence/CAL-CONT limits, B07 strong ordinary controls, B09's zero executed history response and B10's active joint-policy losses. No diagnosed optimizer repair, promised larger-budget gain or method-efficiency conclusion follows.

**Proposed ownership and boundary.** Unowned successor slug `uav_episode_policy_search`: code `experiments/candidates/uav_episode_policy_search/b01/`; tests `tests/experiments/candidates/uav_episode_policy_search/b01/`; notebook/claim `docs/research/candidates/uav_episode_policy_search/`; runs `runs/uav_episode_policy_search/<tag>/`; scratch `temp/directions/uav_episode_policy_search/`. No paths were created or direction activated. Reuse pinned B02/B08 modules/assets without editing another lead's code or reopening B04–B10. Waiting/RF closures stand. This establishes source feasibility and conditional complete price, not likely gain, novelty, verified initialization/runtime or adoption. Root owns any later selection after full independent advice and the handoff; no next implementation/fit/native study is selected now.

### Root's round-completion and handoff instruction (verbatim)

Owner now requests completion of this round without interruption, then one standalone handoff with Root overview and each DM's own section. Finish your already requested source-only policy-search feasibility/full-cost reply to /root/deep_report_review and preserve the full originals and eventual complete Oracle answer in your owned notebook. No next implementation, fit or native study is selected before handoff. Keep all completed waiting/RF positive and adverse evidence. Root will create docs/research/HANDOFF_20261001_ROOT_AND_FOUR_DMS.md and assign exclusive section-writing turns; do not edit that file yet. Your section should preserve question continuity, latest RF P/U32 results/critic/cost/cleanup/canonical evidence, meaningful earlier waiting capabilities and limits, the fully costed policy-development candidate and its decision status as UNSELECTED, and recovery conditions. Complete current bounded source work rather than ending it at this message.

<a id="episode-search-original-advice"></a>
### Complete original independent policy-search advice and reading coverage

The following is the complete native message from `/root/deep_report_review`, received after
it read the published source reply623ab06fb. It is scientific advice, not Root selection.
No new experiment, implementation or numerical reduction was performed to receive it.

--- BEGIN ORIGINAL ORACLE MESSAGE ---

Complete original independent recommendation and reading coverage for preservation in your existing NOTES and assigned handoff section follows. This closes my bounded source assessment. Preserve it substantively and distinguish it from Root's later disposition; do not implement, activate or launch. The source price at623ab06fb29cba36299e0a3e385267ce3feb2a6f is part of this recommendation.

I recommend retaining ONE concrete future pivot: complete-episode parameter search of a bounded contextual readout on frozen P0, compared with equally exposed global calibration. It is worth one complete exploratory comparison if research is later resumed and Root allocates to policy development. It remains UNSELECTED now, and the owner's handoff-and-stop boundary takes precedence. Retain the B04–B10 stops; this proposal neither repairs B10 nor licenses another parameter-search recipe after an adverse result.

I worked in the existing separate reviewer session without a DM/Root conversation fork, reusing my own earlier focused reviews. This is a follow-up, not a blinded or bias-free review. I reconstructed the original fleet B02–B10 and parent B06–B09 evidence before reading B10's complete new critic/disposition. I checked consequential existing artifact identities/counts and selected original precomputed positive/adverse world contrasts directly, including B04/B05/B07 and B10; I did not create new saved-output reductions or rerun numerical readers. The complete B10 independent reconstruction remains the adequate result review. I do not claim a second replay of its101raw episodes or of later-epoch Adam arithmetic.

The supported diagnosis is retained learned competence plus unresolved, often adverse development—not a common optimizer, forgetting, credit or information cause. B02/B03 constructed recurrent stochastic capability from supervised acquisition; sampled deployment materially outperformed greedy decoding and C within their boundaries. B04's two R−S means were−.040278 and−.005212; only the first corresponding interval excluded zero. B05 was already critic-free, used complete native counterfactual futures and made active parameter/choice changes, yet CONT−S was−.005135/−.005498 and CONT−CAL−.005819/+.001451, all intervals spanning zero. Its positive world29481125 was almost equally improved by CAL; in world29481131 only13same-history changed decisions accompanied CONT−S J−.112368. A bounded residual therefore does not bound whole-episode harm. Preserve the later correction to B05's erroneous no-outage prose.

B06's active count development did not establish superiority over reuse. B07's direct target already failed to improve P0, while its learned target closely fit the small intended change; an optimization-only rescue is weak. Hdirect−P0 was+.007329 on that panel, but Hdirect−Bstar0 was−.010493 with a negative interval, making ordinary calibration a consequential comparator. B08's HIDDEN−RAW+.007318 and HIDDEN−P0_A+.010576 are useful conditional representation evidence, with travel/tail costs and no established advantage over stronger Bstar/Hdirect. They concern a different gate/decision package, not a guarantee for the proposed motion readout. B09's mixed/focal/history evidence did not establish a native improvement; its history intervention had no executed same-uniform choice changes. Parent B06/B07 prediction or shortlist improvements did not substitute for complete native value; B08 ordinary exact reuse materially reduced the planning bill. Actual-S2 parent B09 retained lower-travel CONT behavior with unresolved J/service gains. Those are distinct results, not repetitions of one known cause.

B10 is active adverse evidence: both full54-category fits lose to actual INIT90 by J−.0229865[−.0323034,−.0140403] and−.0261492[−.0342395,−.0179911], with service about−1.61. All512actor and512critic updates per fit executed, OFF choices were exposed, both halves lost, and aggregate OFF frequency moved in opposite directions. Initial executed-row joint-law fidelity and the actual INIT90 comparator matter. Gains over C/CJ retain inherited competence; they do not demonstrate useful new learning. Keep its complete cost and stop. None of these results supports general unlearnability, and none establishes that a better optimizer is waiting to be found.

The constructive change is the unit of optimization. Every proposed perturbation controls all five actors for the complete episode, and every fitness sample evaluates that currently perturbed, jointly evolving policy. B05 instead intervened at one action and continued with fixed P0 to create labels; B04/B10 and parent S2 already collected complete trajectories, so it would be false to say that they ignored complete returns. The new package changes their finite update/data-use construction. It does not identify which earlier component caused failure, and it is not an ES-versus-PPO efficiency experiment.

The primary-source bridge is narrow but real. Salimans et al., arXiv1703.03864, §§2–3, derives Gaussian parameter-smoothed expected-return search and explicitly allows stochastic policies/discrete actions; Sehnke et al., ICANN2008, §2 Eqs6–10, factors whole-history likelihood through one episode-level parameter draw. This supports treating the decentralized shared controller as one complete policy-valued black box without giving actors global state. It does not remove shared-policy expressiveness limits or promise a variance advantage here. The deployment object remains the final parameter center, while exploration samples a neighborhood; improvement of smoothed training fitness need not improve that center. Primary links: https://arxiv.org/pdf/1703.03864 and https://people.idsia.ch/~juergen/icann2008sehnke.pdf .

Mania, Guy and Recht, arXiv1803.07055, §§2–3, supplies the simple all-direction random-search/return-scaling precedent and a strong warning about ordinary baselines and finite-run variability. Its empirical algorithms use deterministic continuous-control policies. Our paired normalization, stochastic categorical actions and coupled partial-observation team are declared departures; its convex analysis and locomotion results do not transfer as UAV guarantees. https://arxiv.org/pdf/1803.07055 .

All three local libraries were searched for the actual policy-development/parameter-search question, and load-bearing primary passages were read. Actual coverage is not whole-library reading or a novelty claim:
- Foundations B01: docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf, PDFpp259–261 and305–307 (§§9.4,9.7.1), on local/history information and the restriction imposed by parameter sharing. The P16 catalog entry was also located; its advertised local PDF was absent, so I do not claim local-PDF reading or use it for a guarantee.
- Inst-sci MARL-0061: /home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0061.json, pp2–5 (corresponding pdf/MARL-0061.pdf). AgentMixer's exact identifiability premises and mode-consistency restriction caution against assuming a privileged correlated teacher transfers to sampled local policies. MARL-0593.json pp2–3 was also read: its cooperating learners interact with separate parallel MDPs, so it is not a direct coupled-UAV guarantee. Other catalog hits were locators, not evidence of completed reading.
- My-lib ERL-Re2, idiclr-2023-virtual-12045: /mnt/c/Projects/My-lib/.local-formal-capture/corpus/papers/iclr-2023/iclr-2023-virtual-12045/arxiv-2210.17375.pdf, methodpp4–7 with surrounding setup. Separating a nonlinear representation from a small searched readout is a useful construction analogy. Its population members are single-agent candidate policies; the full method also learns representation with critics and uses bootstrapped partial fitness. Those empirical results do not establish frozen-P0, full-horizon MARL success.

I also read the July R29–R31 effect/reward failure review, the original parent selection passage at NOTES:1574 where parameter search was already considered, and the G50 original result review. G50 supports a smaller normalized immediate-credit route only under its bounded H48/two-phase/reset/shadow-control contract; it does not diagnose the present UAV failures. Its adviser allow-list did not expose individual intervals, so none are inferred. The G46 file inspected contained only AUDIT_DISPOSITION=MISMATCH. Historical continuation rules and G33 do not reactivate anything. Primary records: docs/research/decisions/R29_R31_EFFECT_REWARD_FAILURE_REVIEW_20260714.md and docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_formal_result_review/21_PRO_OPEN_RAW.md.

The proposed future comparison is concrete. Keep the accepted B08 N5/U50/H256/free-space host, all-ON training,27motion categories and four-tick holds. Preserve P0's114lawful features:103observation entries, private navigation one-hot10 and fallback bit, excluding the observation clock. Freeze all34,715P0 parameters. Reuse its original one-row FP32 forward to obtain logits l0 and second hidden h128. Let hbar=h/max(1,||h||2). CAL has28coordinates and logits l0/exp(tau)+tanh(b). CONT has3,484coordinates and logits l0/exp(tau)+tanh(b+W hbar), W27×128. Start all new coordinates at zero. There is no added actor information/history, public action coin, centralized actor, teacher, critic, learned value function or gradient/Adam update. Global complete native J is training fitness; the actor's deployment information remains unchanged.

Use two independently randomized paired blocks, each containing CAL and CONT: four fits. Per fit use16iterations,16Gaussian directions/iteration, perturbation scale.05 and two fresh distinct worlds/tapes per direction, shared between signs and families within that block. Directions use separate fit-addressed streams; matching worlds/tapes does not make the different-dimensional perturbations identical. Each signed policy stays fixed for its two complete episodes. Define Jplus/Jminus as their two-world means and d_k=(Jplus−Jminus)/2. The paired scale is sqrt(sum_k d_k^2/16), floored at1e−8. Update the center by.02/(16*scale)*sum_k[(Jplus−Jminus)*delta_k], retaining all directions. Clip tau to[−ln2,+ln2] INSIDE every perturbed policy, and project the updated center's tau to that interval. This fixes the perturbation ambiguity in the price reply. Use the proposed FP64 head/normalization/fitness/search arithmetic and ordered reductions, while preserving original FP32 P0 execution. The normalized finite algorithm is not an unbiased gradient of unsmoothed J and has no monotonicity guarantee.

There is no partial fitness, elite/rank selection, validation, hyperparameter sweep, checkpoint choice or extra center rollout. Evaluate only all four final centers. This is16finite updates, not an assertion of optimization sufficiency. Exact seed values/domains, failure handling, serialization and numerical fixtures remain future L0 engineering bindings; no implementation or RNG query is authorized now.

The source-support correction changes the comparison materially. *_A is all-ON. *_ZERO turns off the rotating eligible transmitter when capped visible own-user count is zero; that count is not granted service. ZERO changes subsequent observation visibility and navigation history. Therefore matched references are exactly P0_A, Bstar0_A (retained temperature two) and Hdirect_A. Include G_A and C_A, plus P0_ZERO/Bstar0_ZERO/Hdirect_ZERO as separately labelled richer action-contract references. The B08 host supports these separate episodes with the existing old-row timing and unchanged physics. Do not describe ZERO as all-on or assume its mean-J benefit is established: the prior ZERO−A mean intervals span zero. B08's P0_A/P0_ZERO outage in29831016/tape1 shared an all-on prefix; Bstar0_A had two zero-service ticks in29831020/tape1. B10's severe30012025 HIDDEN/INIT90 witness is not a ZERO adverse.

Use32new held-out worlds and two fixed private action tapes, averaging tapes within world. The12endpoint programs require736episodes:11stochastic×64 plus deterministic C_A×32. Declare37contrasts on this one paid panel: four fitted endpoints against all eight retained references, two paired CONTb−CALb, and the three ZERO−A reference contrasts. The14matched comparisons named in the bill are the two CONT−CAL and four endpoints against three A references; the remaining comparisons assess ordinary alternatives and richer rights. Use20,000shared world-bootstrap resamples, generated once (640,000index entries), for descriptive conditional intervals across the fixed contrasts. No new native exposure follows from this reading declaration. Keep each training block and signed world vector separate. Two blocks conditional on one P0 are not independent new parent lineages; episodes are not learned replications.

Read native J with mean service, quality, travel, team p10/minimum/zero-service ticks and full computation cost. No individual-user continuity or physical energy claim follows from those fields. Include the bill's zero-head instrumentation on the81,920already-paid first-iteration contexts per worker/reader: reuse l0/h and the same innovation, adding no native/P0/RNG calls. This supplies observed-context initialization fidelity, not an initial-policy outcome rollout or universal identity proof. Nonactivation, sparse action changes and active adverse changes have different readings; none selects a scale, epoch, architecture or information repair automatically.

The strongest simpler alternative is that global calibration captures the useful movement, while CONT spends a much larger parameter-search variance/computation bill without a native increment. The most serious feasibility uncertainty is informative search in3,484coordinates with only16updates, compounded by smoothing-versus-center mismatch and trajectory sensitivity. Current evidence supplies neither a lower bound on learnable gain nor a convergence guarantee. I nonetheless prefer keeping this one future purchase to declaring the whole learning family exhausted: it uses the complete current joint policy's native consequences, has an already competent starting asset, matches a genuinely capable simpler learner, and can return an actionable complete endpoint without a separate teacher/headroom pilot.

Read outcomes prospectively. Consistent CONT gains over paired CAL and the retained matched A references, with world uncertainty and complete service/travel/tail costs supporting the statement, would establish this conditional whole-policy development capability. It would not prove the old PPO losses were caused by their estimator. If CAL matches/beats CONT, retain any useful calibration result and reject a necessary-contextual-readout story. If either improves P0 but not Bstar0/Hdirect, ordinary retained competence absorbs the practical increment. If matched gains coexist with worse richer ZERO performance, report the smaller-rights capability separately from adoption value; do not automatically add a gate to the learner. Mixed blocks, unresolved intervals, sparse/nonexistent choice effects or active native harm close this finite purchase without automatic tuning or extra seeds. A narrow positive may be retained without replication; any later investment must answer a further decision, not merely seek a nicer interval.

The complete source price is substantial. It is four fits,4,096training+736endpoint episodes,1,236,992native team steps,6,184,960UAV ticks and1,546,240agent decision requests. Training alone equals B05's1,048,576acquisition steps; that is not a controlled cross-study efficiency comparison, and B04/B10 PPO had smaller training exposure. There are1,024distinct training worlds,32held-out worlds,1,536,000executed categorical draws,1,024search direction vectors/1,798,144normal coordinates and64center updates. Equal episode exposure is not equal compute.

Per worker AND full policy replay, price1,392,640head requests; at most1,515,520P0 forwards;71,680full-C requests,1,935,360candidate paths/7,741,440modeled ticks; at most368,435,200helper+C power links;40,960Hdirect calls constructing81,920T/H vectors;20,480G reductions;12,288ZERO decisions. CONT adds up to2,406,481,920readout MAC terms per pass; the frozen P0 ceiling is52,182,384,640dense MAC terms. Cache misses and actual visible n/p remain unknown. The full scalar reader additionally checks1,551,072initial/poststep/refresh states,7,755,360local rows,418,789,440power links,403,278,720distance pairs and every policy/update/return binding. Reader native steps/refits are zero, but all this work is paid. The independent engineering/numerical review and complete reading remain separate from my source recommendation.

Forecast marginal worker CPU is0.6–2.0h, full reader0.75–2.5h and synthetic correctness0.01–0.05h:1.36–4.55machine CPU-h, approximately1.5–6sequential node-wall h, plus incompletely metered staging/source/publication costs. Implementation, full reader, checks/review and publication/cleanup are estimated14–24focused support-hour equivalents. These are unbenchmarked allowances, not actual runtime, guarantees, ceilings or elapsed Codex labor. Anchors are B08's638.832worker+849.524reader CPU-s for1,984episodes and B10's860.761+918.283 for1,376; program/miss/trace differences remain. RSS allowance is0.5–1.5GiB/process, canonical evidence3–6GBcompressed (9–12GBuncompressed), available output/scratch12–16GB. Keep one necessary bulk copy. Neither runtime feasibility nor current node admission has been measured for this unselected implementation.

Inherited acquisition stays incurred. P0 B02 cost one fit,256training+192endpoint episodes/114,688steps,81,920labels,8,000updates/4,096,000presentations and107.543822worker+reader CPU-s, plus support. Its exact file SHA isb9e25fca68109bb50fa64fadfc90939ad6a4669058c1c0ccd1351c8bbcefe12a; eventual staging must verify it. Bstar0's256episode/65,536step calibration and32world endpoint are paid; the139.828009s published calibration CPU is two-lineage aggregate, not an attributable half. Hdirect/G/ZERO need no new fit to reuse but their historical development/evaluation and ongoing model queries are not free: retain the bill's B07/transmission-B05/B08 costs. Fleet B02–B10 already totals22fits,2calibrations and4,055,080steps; do not double-count their components. B01 and parent S2 remain separately incurred. The present literature/source assessment also consumes support; zero fits does not make it free.

Remaining gaps are explicit: new code/reader do not yet exist; seeds/failure/fixture contracts and accepted input identities are not frozen; actual cache behavior, trace compression, initialization fidelity, runtime and node resources are unverified; no observed conditional learning advantage exists. These gaps require ordinary engineering resolution only after a later selection, not a pilot now. The existing source price and this full advice are sufficient for handoff. The proposed uav_episode_policy_search slug is unowned and unactivated. Preserve all waiting/RF closures, the separate silence/history and RF-information questions, and accepted S7 C/H/F work unchanged. Stop at the owner's handoff boundary.

MATERIAL_DISSENT: no — I support the completed-study stops, UNSELECTED status and current handoff stop. My constructive recommendation is one fully priced future pivot, not an adopted claim, present allocation or launch authority.

--- END ORIGINAL ORACLE MESSAGE ---

<a id="episode-search-dm-response"></a>
### DM reading and boundary after the full independent advice

I read the entire answer and coverage statement. The source-feasibility/cost claims agree
with the actual code and existing records I read for the bill. Its101raw-episode reference
is the B10 scientific critic's selected direct inspection, not B10's complete1,376-episode
worker/full numerical audit. The original critic's scope in fleet NOTES explicitly confirms
that distinction. Library/primary-paper coverage above is the Oracle's disclosed reading,
not a claim that I reread all those papers or that adviser agreement supplies new evidence.

The advice resolves concrete prospective gaps without changing native exposure: independent
fit-addressed perturbation streams; FP64 head/norm/fitness/search; clipping tau inside each
perturbed policy and projecting center tau;37fixed contrasts;20,000shared world-bootstrap
resamples/640,000indices; and the separately priced81,920zero-head identity contexts per
worker/reader. Exact seeds, ordered arithmetic details, serialized source/input bindings,
finite-value/failure rules and meaningful finite checks still belong in a future selected L0.
The full reader would reconstruct every simple search update, not merely trust checkpoints.
No RNG, actor, native or saved-outcome computation was run to make these selections.

My working explanation remains retained stochastic competence with repeated, materially
adverse or unresolved policy-development attempts. Whole-episode parameter search changes
which complete jointly evolving policy each fitness evaluates and how those samples update
it. It does not establish an old critic/optimizer/credit failure or remove the shared-policy
information/representation restriction. The strongest competing explanation is that global
calibration captures the useful change; CONT's3,484-coordinate search may be uninformative
at this budget, and neighborhood fitness need not improve the final center. Bounded logits
cannot guarantee bounded trajectory harm. These uncertainties are reasons for an honest
conditional complete comparison, not positive predictions secretly verified by a pilot.

I accept retaining this single fully priced future candidate, its simpler CAL and strong
ordinary/richer-rights controls, and the fixed stop branches as useful advice for a later
Root investment choice. There is no material scientific disagreement to resolve. Advice is
not adoption: **uav_episode_policy_search remains UNSELECTED, unowned and unactivated**;
no new code, direction directory, fit, native episode, test/prototype or reader exists.
Waiting B01–B07 and RF B01 remain closed, all positive/adverse/technical evidence and prior
cost retained. The present source assessment is now complete. Under the owner's explicit
round boundary, I will finish only the assigned handoff section when Root grants its
exclusive editing turn, then stop. A status question, reading this recommendation or idle
node capacity does not resume research. Root's subsequent allocation/disposition, if any,
must stay distinct from the original Oracle advice above.

### Root's separate handoff disposition (verbatim)

I have now read the entire published original source bill, complete Oracle advice and your response at d9183bdf. Retain the single priced whole-episode search versus CAL option, the corrected A/ZERO rights, full 37-contrast proposal and all feasibility limits as UNSELECTED. I adopt no new run or claim at this handoff boundary. Your section remains third in the serialized handoff order: fleet adaptation has the current exclusive turn, parent adaptation next, then you. I will grant your file turn explicitly; no additional source/review work is requested.

This is the resolved current allocation: no successor purchase or new claim. The complete
source/advice assessment is retained for recovery, and only the already requested handoff
writing remains. I performed no further scientific source/review work after this disposition.
