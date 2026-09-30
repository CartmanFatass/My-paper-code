# Completed allocation review: local-controller inheritance

Retired2026-09-30 after the independent review and Root decision. This is unmaintained
research-index history; current standing is in [RESEARCH](../../RESEARCH.md).
Source main before this publication: `4d3b30dbe9871f156ddb2a854139a026b5ae8b5e`.
Prospective design: `4d3b30dbe9871f156ddb2a854139a026b5ae8b5e`,
[complete direction note](../../candidates/uav_fleet_adaptation/NOTES.md#search-amortization-design-20260930).

## Allocation question and source scope

Following complete N8 warm-start reading, decide whether a bounded local-controller imitation
programme supplies a useful learned starting asset, compared with the strong ordinary
computation alternatives, a distinct constructive question and stopping. Keep the new local
C teacher distinct from fleet C_N/E; preserve all earlier positive/adverse exposure and the
current C-prior/continuity work. The exact design and final six-arm cost correction above
are the proposal evaluated. Root's initial computation-saving rationale was challenged by
historical exact-cache evidence; learned-initialization value was then assessed independently.
No result exposure occurred during selection.

## Independent Answer

Original complete final answer from the existing separate-context ResearchCritic
`/root/deep_report_review` (actual gpt-6-astra/max); preserved verbatim below.

**Recommend selecting the revised one-fit study to construct a competent learned starting policy.** The published design at `4d3b30dbe9871f156ddb2a854139a026b5ae8b5e` incorporates the consequential corrections: competent ordinary comparisons, initialization, separate greedy/sampled evaluation, and complete cost accounting. This recommendation concerns capability development; the evidence does not establish a deployment computation problem. [Prospective design](/home/fires/hmasd-wsl/docs/research/candidates/uav_fleet_adaptation/NOTES.md:532)

I reconstructed the new fleet results and costs before reading its interpretation, then reused the completed independent raw-evidence audit. No DM/Root conversation fork was inherited. This follow-up checks the new allocation, rather than repeating the fleet or C-prior reviews.

The fleet reading remains unchanged: F/E improves native J over A/E by `.010358`, but service changes by `−.113500`; F/E does not improve the retained parent’s mean capability and remains below C_N/E. Complete worker/reader cost was approximately **8.66 CPU-hours**. Active learning and management opportunity therefore did not establish useful development under that recipe. This supports ending unchanged A/F investment, without identifying a repair or closing learning generally.

The proposed teacher is a different controller: lawful **local C, N5/all-on/H256**, rather than fleet C_N/E. Its historical mean service was `19.916` and `21.738` users/tick across two panels. Those are motivation, not fresh matched references: the new study correctly gives every arm the same current host.

**The strongest objection is that a student could merely become an inferior copy of an already inexpensive controller.** That objection became stronger during this review:

- The DM’s source-grounded scan found exact memoization hits at **88.46% and 86.20%** of historical C decisions, with no recorded command/navigation conflicts. C already vectorizes its 27 candidates.
- Full C took approximately **0.396–0.423 seconds per H256 episode** historically. Neither those times nor the saved-data cache counts establish current cached runtime.
- One adverse world required **319/320 searches**, so average reuse supplies no worst-case guarantee.
- I independently verified all 32 B02 C raw hashes and counted its commands: **69.56% hover**, and **94.67% hover or coordinate-axis commands**. This supports including C7, while providing no guarantee about C7’s complete trajectories.

Consequently, neither eliminated searches nor high imitation accuracy would justify this purchase by itself. Memoized C and memoized C7 are essential comparisons.

The closest completed precedent reinforces that caution. I recomputed the coupled-host distillation comparisons from all 32 saved world records: final student service share was `.400410` versus teacher `.758656`, losing in every world. The DAgger milestone increment was only `+.016996`, SE `.033401`, despite substantially cheaper inference. The cheaper ordinary teacher retained `.732738`. That was real learning above initialization, but unsuccessful capability inheritance. [Native results](/home/fires/hmasd-wsl/runs/coupled_host_planner_distillation/b01_eval_dev_a01/summary.json)

Nevertheless, **a competent learned starting policy is a consequential capability distinct from immediate computation savings**. The current C-prior study retains online C; this study would produce an actor whose commands can subsequently be developed without C’s candidate ranking. It supplies a concrete alternative starting asset for a later bounded learning comparison. Such a continuation is structurally feasible, but requires a rollout/input adapter, critic, optimizer and declared sampling law; it is neither implemented nor included for free.

The constructive prediction is therefore specific: this finite supervised program can bring the final actor within the declared native competence tolerances of C on fresh worlds. Deterministic categorical labels and an explicit sufficient navigation state make that conjecture credible enough for one complete observation. They do not guarantee learnability. Repeated observations and neighboring decisions also mean that 81,920 label requests are not 81,920 independent examples.

DAgger supplies the relevant method: collect expert labels on learner-visited states and aggregate them. Its recoverability and learning assumptions do not certify this finite neural fit, and its validation-selection result cannot be imported into a fixed-final-endpoint study. [Ross, Gordon and Bagnell, Algorithm 3.1 and associated guarantees](https://proceedings.mlr.press/v15/ross11a/ross11a.pdf) July R54, S7 imitation, planning-policy compression and the coupled-host result likewise prevent treating a computable teacher as proof of successful inheritance. No algorithmic novelty is claimed.

The lawful interface is now coherent. The student receives current local observation fields, its own predecision waypoint state, and a cheap model-derived fallback bit. It receives no nominal C command, unseen-user cache, other agent’s private observations or future truth. Teacher queries during aggregation use the student’s actual observations and navigation state. The result would be **search-free, model-assisted execution**, since the analytic fallback computation remains.

The fallback derivation is plausible: eligibility extrema can replace exhaustive ranking for determining whether every candidate has zero modeled service. Its finite-precision equivalence near thresholds and clipping boundaries remains an engineering requirement. It has not yet been established by an implementation.

**The smallest worthwhile complete purchase is the published six-arm envelope:**

| Work | Episodes | Native steps |
|---|---:|---:|
| 128 C episodes, then two 64-episode student aggregation rounds | 256 | 65,536 |
| S0, BC, final-greedy, final-sampled, C_memo and C7_memo; 32 common worlds each | 192 | 49,152 |
| **Total** | **448** | **114,688** |

This is **one initialized training lineage with three optimization phases**, not three independent fits: 8,000 Adam updates and 4,096,000 sample presentations. Final−BC is a milestone comparison with additional data and updates, not isolated evidence for DAgger.

Before cache savings, the complete program requests:

- **92,160 full-C rankings**, including training labels and C evaluation;
- **10,240 C7 rankings**;
- **10,240,000 modeled candidate ticks** across those rankings;
- up to **133,120 analytic-helper calls** and **81,920 neural forward rows** outside optimization.

Actual misses, link calculations, shared setup, CPU, wall time and memory must be measured. The proposed **10–40 CPU-minutes worker plus 1–5 minutes reading**, and **2–4 hours engineering/review**, are planning estimates. No final-policy expert-query diagnostics are hidden in that price.

The added sampled panel materially improves the decision. A successful greedy policy need not be a competent categorical-PPO starting policy. Temperature-one sampling is fixed prospectively; cache hits must retrieve logits and navigation state, then receive a fresh indexed categorical draw. Caching sampled commands would change the policy law.

The proposed research screen is defensible if read exactly as declared: final-greedy versus C mean J at least `−.01`, service at least `−.5` user/tick, mean per-world service-p10 at least `−1`, no newly zero-service world, and positive complete mean J/service change over S0. These are **exploratory continuation tolerances**, not operational requirements or evidence of statistical equivalence. Conditional intervals and every adverse world remain consequential even when the point screen passes.

The outcomes would change real choices:

- **Greedy and sampled competence both retained:** retain a conditional learned starting asset and consider a separately priced native-development comparison. This establishes neither improvement beyond C nor successful future PPO.
- **Greedy passes, sampled fails:** retain deterministic capability; the default stochastic-initialization bridge remains adverse or unresolved. Do not silently change temperature.
- **BC passes, final fails:** retain the milestone observation without replacing the declared endpoint.
- **C7 supplies stronger complete capability or cost:** preserve that ordinary result and reassess the reason for further student investment.
- **Label fitting improves but native competence fails:** end this fixed inheritance package. Do not automatically add rounds, capacity or training.
- **Little consequential action change occurs:** distinguish decoder nonactivation or sparse useful exposure from an active adverse intervention.

I also considered a distinct constructive allocation: **forecasting visible-peer motion inside competent local C**, comparing complete native service against its stationary-peer approximation and an ordinary constant-velocity forecast. This targets task performance directly. It remains plausible, but anonymous-peer association, occlusion, causal forecast inputs and the forecast-to-ranking interface are not yet concretely priced. Simultaneous decisions also make previous-block velocity potentially stale.

The existing B04 result is consequential here: forecasts improved on their own trajectories, yet F−O averaged `−.009810 J/−.720988 service`, with mixed training signs. That does not refute prediction inside C, but prevents accuracy improvement from serving as its justification. The *Models as Agents* primary methods also emphasize coupled model/policy errors under joint-information assumptions that cannot simply be transferred to this local interface. [MARL-0016, pp.2–4](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0016.json)

I rank the concrete inheritance observation ahead of that presently unspecified prediction program and an unchanged A/F repeat. Choosing no third study would also be defensible; the active-question count supplies no scientific reason to run. My positive recommendation rests on the distinct starting-asset use, corrected decision exposure and bounded complete cost.

I checked the entire published prospective section and final addendum. I have not verified executable implementation, numerical fallback equivalence, current-node timing or admission. No experiment was launched. Existing pauses and accepted operations remain intact; this review selects no later fine-tuning and requires no additional routine scientific-review pass.

**MATERIAL_DISSENT: no — recommend the revised one-fit developmental study. The unsupported computation-use rationale and the greedy-only initialization gap have been corrected in the published comparison.**

## Root decision

Root,2026-09-30: select the final one-fit design at4d3b30dbe9871f156ddb2a854139a026b5ae8b5e.
The full independent recommendation above has been read and adopted. This is a bounded
conditional construction of a learned starting asset, not a response to a measured latency
requirement, a novel algorithm claim, confirmation, or permission for later PPO. The same
non-archived DM keeps `uav_fleet_adaptation` and its owned paths; B01's result, negative
comparisons, cost and cleanup remain unchanged. No new DM or renamed fresh scientific slate
is created. Ordinary code/check/run/read/publication work within this selection needs no
routine Root acknowledgment.

The fixed programme is128 expert episodes,64+64 pure-student aggregation episodes and
six32-world evaluation arms S0/BC/final-greedy/final-sampled(T=1)/C_memo/C7_memo:
448 H256 episodes,114688 native steps,one training lineage,8000 Adam updates and4096000
sample presentations. Keep the final endpoint, class frequencies and two aggregation rounds;
no score-dependent data/epoch/seed/decoder expansion. The original one-fit design's earlier
five-arm cost table is explicitly superseded by its final correction, not added to it.
Expert-label requests81920 plus full-C evaluation10240 give92160 full-C requests; C7 adds
10240. Before cache savings these require10240000 candidate model ticks, up to133120
helper calls and81920 neural rows outside optimization. Worker10–40CPU-min, reader1–5min
and engineering/review2–4h remain estimates; report actual full costs and unknown support.

Retain exact memoized ordinary C and C7. The hash-checked old cache counts and high axis/hover
share strengthen those alternatives but do not prove their current runtime or C7's new native
performance. A319/320-miss world prevents a worst-case speed claim. The student is model-assisted:
its cheap fallback/navigation helper is real online computation. Verify numerical equivalence
to the full-C fallback predicate and preserve fresh indexed stochastic draws even on cache hits.
Input/RNG/world identities and exact executable semantics must be fixed before normal source
publication/admission; these are prospective implementation tasks, not new scientific pilots.

Read the declared exploratory competence screen on point outcomes alongside conditional
intervals and all adverse trajectories: final-greedy−C J>=−.01, service>=−.5, service-p10>=−1,
no newly zero-service world, and positive mean J/service change versus S0. These tolerances
select a research asset; they are not operational requirements, statistical noninferiority
or a guarantee of successful later optimization. Apply the competence comparison separately
to the fixed sampled endpoint before calling it a competent stochastic starting policy.
Greedy-pass/sampled-fail retains only the supported capability; BC-pass/final-fail does not
replace the declared final endpoint. No sampled-S0 learning-effect claim is available. A
stronger C7 outcome remains consequential even when the C-based point screen passes.

The strongest rejected rationale was immediate computation savings: C already costs little
historically and exact reuse is strong. The different retained rationale is an executable
learned initialization whose future policy-development comparison would not need full C
ranking. That later comparison still needs a rollout/input adapter, critic and sampling law;
none is selected or priced as free. If this package fails native inheritance, retain its
positive and adverse observations and end this fixed recipe rather than buy an automatic
repair. One lineage supports conditional asset evidence, not empirical training-population
superiority. The competent-C peer-motion prediction alternative remains unselected because
its association/occlusion/interface and total comparison cost are not yet concrete; the prior
B04 prediction-without-native-gain evidence remains relevant rather than a proof against it.

Root read the published design in full, the original independent recommendation, complete
fleet result/disposition and the coupled-host distillation native summary plus its corrected
prospective/result notes. Root also read Ross et al.2011's primary Algorithm3.1 and Theorems2.2,
3.1–3.4 (printedpp629–630; surrounding analysis onp631), and Tang et al.'s MARL-0590 primary
PDFpp1–2,6–7 and its indexed JSON. DAgger motivates aggregation on learner-visited states;
its recoverability/no-regret assumptions and best-policy existence do not certify this neural
fixed-endpoint programme. The MAIL joint-policy value bridge does not remove local-information
or strategic-regret limits. No additional Pro round has distinct unresolved value here; the
separate already accepted C-prior Pro question remains open and is not substituted as advice
about this student.

The pending C-prior and accepted continuity work proceed independently. Preserve Claude's
pause/ownership, FSD/PPC pause, G33 freeze and Milan dependency. This selection completes the
allocation review; exact publication, engineering checks and fresh actual-node admission still
precede the new result operation.

## Superseded fleet allocation

The prior fleet allocation from source main is preserved verbatim below. The still-current
continuity and pending C-prior targets remain in RESEARCH and are not retired here.

**`uav_fleet_adaptation`: develop native N8 learning under E.** Prior E management improved H6
N8 service in every world, while C/E remained the stronger mean complete-use reference. Two
warm-start continuations from exact H6 final45 compare 512 N8/H500 episodes under E against
512 under all-on; deploy I/E, A/E, F/E and C/E on 32 fresh common worlds. Primary F/E−A/E tests
these finite training programs; own-parent and C/E comparisons decide retained capability/use.
The original parent trained at N6, so ordinary additional N8 training is a consequential control.
Keep original local actor, critic, skill clock, raw-Gaussian replay/environment clipping and
fixed deterministic evaluation. Modules/normalizers are retained, optimizers/runtime are fresh;
this is not checkpoint-resume or a diagnosed missing-mask-input repair. E remains deterministic,
uses the original lawful boundary snapshot and applies after the actor under the old mask.
Two fits and 128 evaluation episodes total 576,000 steps; 8.16 million mask requests and 3.456 million
C_N motion requests, plus neural replay, initialization, output and full reading. The historical
~7,713-second fit-wall anchor excludes added E/reader work and is neither quote nor upper bound.
A useful F increment may be retained even if C/E remains preferable; absent/adverse improvement
ends this fixed recipe without automatic architecture repair or added fit.

