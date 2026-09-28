# Independent scientific review: Oracle programme memo (`successor_selection_20260928/MEMO_PROGRAMME.md`)

Saved verbatim by the DM from the hmasd-research-critic hand-back (separate context, read-only; the role body forbids its own record writes), 2026-09-28. The critic ran against HEAD after Root's selections at `613c8bcfc`/`99a248180`; the Pro answer was still empty at its read time.


**Context disclosure.** I ran in a separate context and inherited no DM or Root conversation. The assignment named the object and the items to check, so this was not a blinded review. I rebuilt the evidence (b05 readers, Root's round-3 notebooks, the restoration-host source, Root's current inbox and RESEARCH) before relying on the memo's reading. The Pro answer is still empty (`energy_relay_benchmark/NOTES.md:6834`). I made no edits and ran nothing result-bearing. The only file written was one arXiv PDF, downloaded to my session scratchpad for a first-hand read.

Tags: [V] verified first-hand, [I] inferred, [C] conjecture.

---

### Findings, most consequential first

**1. The memo is stale against HEAD, and its allocation and breadth sections are overtaken by Root's adopted selections. [V]**
- The memo is stamped "HEAD `eeac6e93a`" (MEMO:3). Since then Root has done four things:
  - opened the programme review (`1b5bde758`);
  - received two proposals (`e2ff83480`, `838b93b25`);
  - adopted both at `613c8bcfc`: O_H/P at H12000 (0 fits, ≤192k steps) and C/H/L message-content learning on base `MultiUAVEnv` (3 arm fits, 442,368 teamsteps) (`docs/research/RESEARCH.md:1454–1473`; inbox `20260928_joint_next_round_plan_ROOT.md:14–32`).
- **D1 (O⊕R assigned to Root, MEMO:59–66, 150)** competes with a depth study Root has already selected. Root's reviewer explicitly accepted leaving R out: "Omitting R is acceptable because this is not a search for the best complete long-mission controller" (RESEARCH.md:1382).
- **B1 ("not ready; the record answers it") and §6 ("B1/B2 remain unfunded reserve until a host exists", MEMO:83–89, 151)** are contradicted. Communication learning is now funded on a host that does have delayed RR transport (RESEARCH.md:1343–1352, 1408–1452).
- **B2 ("a UAV host with exogenous roster change … does not exist", MEMO:96)** is contradicted:
  - G0 over S7-S1 has "One exogenous service leave/return over eight fixed physical slots" (`uav_roster_memory/NOTES.md:106`).
  - Root named G0 as its changing-team candidate and deferred it for a different reason: no consequential comparison, and G1's ordinary reassignment was adverse (inbox:20; RESEARCH.md:1356–1363).
- **What works in the memo's favour:**
  - Root says it has "not … taken your alternative-host choice" for T3 (inbox:22).
  - Root keeps T3 "data-dependent while discussing Claude's other-host option" (RESEARCH.md:1291).
  - Root assigns "No competing W/offset or restoration study" (RESEARCH.md:1471).
  - So the restoration host is uncontested territory for Claude. But §6 must be rewritten around those facts, not around assignments Root has already superseded.

**2. B3's readiness study is already TRIED, its decision rule is fixed in advance, and its information-structure claim is contradicted. [V]**
- **Step (1) is already done.** The memo proposes running the four diagnostic controllers on the fixture and reading static-vs-planner (MEMO:108). That was run on 2026-09-17 (`docs/Claude_docs/changes/2026-09-17-uav-service-restoration-v0.md:181–194`):

  | Controller | Satisfaction | Restored |
  |---|---|---|
  | backhaul_aware_greedy | .9833 | .9373 (recovers in 38 s) |
  | random | .9658 | — |
  | static | .7333 | — |

- **The gap was built into the fixture.** The preset's own note says "UAVs start clustered near the western site so that a static controller leaves the eastern demand unserved … That is a property of this fixture, not evidence about any algorithm" (`configs/uav_service_restoration/smoke_fixture.json`, `notes`).
  - The fixture's event is explicit and deterministic: site 1 at 120 s, `start_s_range [120,120]`.
  - Demand is analytic, so "≥ 16 event seeds" may vary almost nothing [I].
  - The memo's rule "static-vs-planner gap ≥ .10 → the host carries a learned comparison" is therefore already met by construction and discriminates nothing.
  - On the fixture, the headroom of any learner over the competent ordinary greedy is ≤ .017 satisfaction (≈ .06 on "restored") [V numbers, I reading].
- **The host is not a Dec-POMDP.** The memo claims it offers "(b) a real Dec-POMDP information structure" (MEMO:104). The observation module says the central management channel "aggregates UAV poses … and redistributes them … it does not establish decentralised execution under bandwidth limits" (`envs/uav_service_restoration/observations.py:3–9`). Both presets set `telemetry_delay_s: 0.0`, so "aged telemetry" is TTL/sensing staleness only.
- **Consequence [I]:** the memo's own risk statement ("the learned question must be the decentralised/aged-information one, or it will be a second planner host", MEMO:106) is realised by the host's actual information condition. The eventual question becomes learned-over-a-competent-central-planner: the same family the memo calls unreadable at one instance on S7.
- **What an informative readiness read needs [I]:**
  - It measures ordinary planner vs an oracle/ideal-information bound on real data. `ideal_full_current_demand` exists as a declared diagnostic mode (`observations.py:24–27`; `config.py:452`).
  - It needs the Milan cache. The memo found no local cache; Root independently confirms the cache is absent and that acquisition and preparation are unpriced (inbox:21–22).
  - So the binding next item is the owner's data decision, not a fixture run.
- **Cost figures.** The memo says fit cost is "unmeasured [C]" (MEMO:106). Part of it is measured: 0.0525 s per decision step on the fixture (changes doc:178). At that rate one 180-step episode takes ≈ 9.5 s single-process, so a few-thousand-episode MARL fit is hours, not minutes [I]. The Milan preset (4 UAVs, 25 demand points, 4,096 paths) is unmeasured.

**3. The "NEW to the record" label for the eventual restoration question is store-relative only; a close primary neighbour exists. [V]**
- All three local stores are ML-venue MARL collections. The Inst-sci catalog has 0 hits for "UAV", "wireless", "base station", "aerial", "disaster". My-lib has 0 for "base station" and "disaster". A miss there says nothing about the wireless/MobiCom literature.
- Primary passage read first-hand: Xu et al., "Scalable UAV Multi-Hop Networking via Multi-Agent Reinforcement Learning with Large Language Models", arXiv 2505.08448v2 (PDF pp. 1–2; builds on their MobiCom'24 paper "Scalable MARL for Effective UAV Scheduling in Multi-Hop Emergency Networks").
  - p.1, Fig. 1: a "Damaged BS" with UAVs forming multi-hop links to an operational BS.
  - p.2: "multiple UAVs are strategically deployed to serve ground UEs. They form a relay network that bridges isolated areas with available BSs"; MAPPO is a baseline.
- Consequence: "event-driven re-deployment with relay chains after site failure, learned by MARL" is an established applied problem family. Put to the owner as-is, it risks the "re-skinned" objection. Any novelty must come from the specific comparison (e.g., learned vs an exact-LP-aware planner under matched TTL telemetry), not from the problem. The memo does defer the literature check to declaration (MEMO:117, 123); the DM should not relay the label as "NEW".

**4. §1.2's derivation mixes a sound direction with three unsupported steps. [V/I]**
- **"The competing explanation predicts exactly the same observations" (MEMO:43) is not fair to the record.** In persistent_service, the ordinary O showed achievable headroom inside L's own interface: "O's result supplies a constructive useful policy within the shared commitment interface" (`uav_persistent_service/NOTES.md:731`); O−P +.063 [.049, .077] (`:553`). "No headroom" is refuted for that decision object, so L ≡ P is a learner/deployment failure there. This supports the memo's direction ("instrument-limited") but refutes "indistinguishable". It discriminates in one of five cases; joint_transition (O−R negative) and b05 do not.
- **Ordinary increments are used as a cap.** "A learned increment … cannot plausibly exceed the ordinary one by much; its expected size is inside .00–.06" (MEMO:39). An ordinary increment is a lower bound on achievable opportunity, not an upper bound on learned value. The project already accepted this point: the stake "is not an upper bound on coordination value" (`sequential_coordinator_credit/NOTES.md:386`). Minor slip: "≤ .06" while listing O−P = +.063.
- **The ".05–.12 instance spread" is re-purposed.** It comes from critic finding 4, which says it is "not a seed SD (frame condition differs, evaluator thread settings cross)" (`successor_selection_20260928/REVIEW.md:39–41`): it is B vs SET across checkpoints, i.e. two recipes. The memo calls it "instance spread" and transfers it to the macro-cadence recipes. Those recipes' deployed outputs were bitwise identical to the ordinary reference (L ≡ P in 16/16 worlds, `uav_persistent_service/NOTES.md:553`; L ≡ R in 8/8, `uav_joint_transition/NOTES.md:615–618`), so they had zero deployment variance. Their failure was nonactivation, not resolution.
- **The optimiser generalisations are partly wrong.**
  - "none has" critic EV materially above 0 (MEMO:51) is contradicted by active_sensing B01, EV −.0005 → .212 (`uav_active_sensing/NOTES.md:745–746`).
  - Clip fraction 0 is verified for joint_transition (`uav_joint_transition/NOTES.md:648`) and active_sensing (`:734, :1235`). It is not recorded for persistent_service: no clip-fraction field in `runs/uav_persistent_service/b01_commitment_a01/training.json`, and NOTES:733 states only near-zero EV.
  - "Each macro-cadence learner was initialised at (or near) the ordinary choice" does not hold for active_sensing, whose entropy was near uniform (5.549 vs log 257, `:734–735`).
- **"SET … is still improving (NOTES.md:6809)" (MEMO:41) is contradicted.** NOTES:6809 says "The 'still improving' rule said no"; NOTES:3332 says "Row 5 (still improving …): flags false in both". b05's own curve peaked at c03 and fell (NOTES:6789).
- **Net reading [I]:** "single-instance learned-over-planner increments on S7-S2 are hard to read" survives. "Instrument, not opportunity" is supported for persistent_service only. The two explanations are not observationally equivalent across the record.

**5. §1.3–1.4 cost and criterion: the n ≥ 3 remedy does not match the diagnosed failure, and option (B) is incoherent as a Claude option. [V/I]**
- **Fit walls are verified:** persistent 27.76 min fit wall (`uav_persistent_service/NOTES.md:747`); joint_transition runner 120.4 min (`uav_joint_transition/NOTES.md:698`); active_sensing 89.56 min (RESEARCH row at `eeac6e93a`:998, cited by the memo as :999).
- **n ≥ 3 does not cure nonactivation [I].** The memo's own item 3 says nonactivation is the modal outcome of those designs regardless of headroom. Three instances of a deterministic-argmax design that stays at the ordinary action plausibly give three bitwise nulls. Only the added clause "ordinary policy as a candidate rather than the initialisation" is a real design change, and it is asserted without evidence.
- **The macro recipes are Root's and were stopped.** Their dispositions explicitly decline unchanged replication (`uav_joint_transition/NOTES.md:806–814, 855–860`; persistent synthesis `RESEARCH-native-round3-synthesis.md:24`). Option (B), "stay on S7-S2 with n ≥ 3 on macro recipes", has no Claude recipe behind it.
- **Fault arithmetic is overstated.**
  - The "≈ 4 faults in ≈ 2.7 M" denominator counts only steps up to each fault. It omits the ≈ 1.2 M fault-free steps of the two resumed processes (a01r 600k→1.2M; b05 a01r 600k→1.2M, NOTES:6758).
  - It mixes signatures: `energy_relay_baselines` recorded one SystemError at 432k and one **SIGSEGV** at 858k (RESEARCH row at `eeac6e93a`:1005).
  - Counting all four events over ≈ 3.9 M steps gives ≈ 1.2 per 1.2 M fit, not 1.8 [I]. The conclusion (SET is expensive) is unchanged.
- **The criterion.** "Readability at the resolution of the purchase" is the right refinement of "one-fit cost", and it is consistent with constitution §8.1 and scientific-tools SKILL.md:274–276. But the memo turns it into a screen: "a decision object with a *predicted* effect ≥ .10" (MEMO:49, 55), plus B3's "gap ≈ 0 → drop the host". The method says "Do not require … proved headroom or a rule-positive screen before direct learning" (SKILL.md:81–82). State it as expected effect vs resolution for the declared purchase, not as a gate.

**6. D2 (ceiling decomposition) should be dropped as written. [V/I]**
- **Its premise is wrong: the record already has a discriminating reading.** The memo says "no clairvoyant reading exists". But:
  - H_central (every-step replan) .774 vs H_central@10 .769 (NOTES:2505–2507), and the replanning-period sensitivity −.005 (NOTES:6816), bound the freshness value of ≤ 9-step user positions at ≈ .005.
  - Clairvoyant anticipation is a different quantity from freshness [I]. Still, with S2 users at 3 m/s (`configs/config_1.py:566–571`), arm (i) is likely to fall in the "< .02 → proposal closes" row. The purchase would mostly re-confirm what the record suggests.
- **The energy-free arm is confounded.** S1 vs S2 differs not only in `battery_enabled` (config_1.py:540) but in user speed 2 vs 3 m/s (:566–571), `episode_length` 500 vs 1500 (:496) and `total_timesteps` (:499–502). "Energy-free H_central@10 = S1 stage" is not an energy-only ablation. A clean arm needs a battery-disabled S2 variant, i.e. a host change.
- **It is excluded diagnosis on the energy-relay host** (NOTES:6731–6733). The memo concedes it is "offered, not recommended". Given the two points above, it should not be on the owner's menu.

**7. D1 is unmeasured, but its outcome readings overclaim. Root owns the choice and has already chosen differently. [V/I]**
- **Unmeasured: verified.** "no cross-panel ranking or combined-component claim follows" (`RESEARCH-native-round3-synthesis.md:55–56`). A common exact P exists on Root's harness (joint_transition P .797 / R .818, `uav_joint_transition/NOTES.md:608–612`).
- **Cost inputs verified:** O/P 1,824.8 / 1,573.8 s per 16 worlds (`uav_persistent_service/NOTES.md:686–687`); R 122.3 s per world (`uav_joint_transition/NOTES.md:611`). "O⊕R ≈ O" is [C].
- **O⊕R is a new controller, not a zero-engineering panel.** O's wrapper removes committed members from H1 matching (`uav_persistent_service/NOTES.md:120–122`), so R's target search must be redefined over the available team [I].
- **Two interpretive errors [I]:**
  - "O⊕R < max(O,R)" is interference, a stronger condition than sub-additivity; the memo conflates them (MEMO:62, 64).
  - A negative interaction between two hand-designed modules measures a bad composition rule, not "the first MARL-relevant coupling … the interaction size is the headroom". It neither bounds nor measures joint-decision headroom.
- **Owner-line tension.** O is charging/commitment control. Presenting O⊕R as the "reusable planning-algorithm" deliverable sits against the owner's "energy-relay optimisation is off track". That is Root's call, but it should not be Claude's headline depth proposal.

**8. Smaller verified corrections.**
- "O under local information … inputs may already be legal-local [I]" (MEMO:79) is contradicted: "All three arms receive current central user/BS xy" (`uav_persistent_service/NOTES.md:49–51`); the synthesis calls it "conditional central-information O".
- RESEARCH.md citations are off by one at `eeac6e93a`: active_sensing is 998 not 999; radio_placement (R−G) is 999 not 1000; roster_memory is 1003 not 1004; energy_relay_baselines is 1005 not 1006; energy_relay_availability is 1009 not 1010.
- The §1.1 summary calls cooperative B02 a "null", but its interval excludes zero on the adverse side (−.016488 [−.026710, −.006266]); the table correctly says "active adverse ranking".
- Root's reset-response clauses are quoted accurately (`RESET_RESPONSE…_20260926.md:131, 224`). But the clause at 224 ties expansion to "the first result", which in that document is the charging return/leave policy study (:127). That first result is O, and it was positive, which argues for S7 depth, not for leaving.
  - "The reason now exists" is a stretch. The clause is better described as moot: Root has since started a communication study itself and named T3 as Claude's open option (inbox:22; RESEARCH.md:1291).
- The SCOPE-message reference is verified: the broader question stays with DM3 (`uav_cooperative_planning/NOTES.md:1125–1126`). Overlap with a restoration-host question is weak but the message is harmless.

**9. Verified as stated.**
- **b05 primary table** (`readers.json` `pairs.B_minus_CSW_*.metrics.qos_per_step.overall`):

  | Cell | Mean (SE) | Negative / positive worlds |
  |---|---|---|
  | dev det | −.0802 (.0179) | 24/8 |
  | dev stoch | −.0838 (.0226) | 22/10 |
  | hold-out det | −.0889 (.0195) | 26/6 |
  | hold-out stoch | −.0288 (.0213) | 19/13 |

- joint_transition nonactivation facts (`:606–620, 630–652`).
- persistent_service L ≡ P and service probability .519–.609 (`:733`).
- active_sensing B02 figures (row 998 at `eeac6e93a`; NOTES:1216–1235).
- uav_information_value contrasts (`uav_information_value/NOTES.md:1432–1434`).
- H_local is a pooled-observation central controller (NOTES:508, 785).
- Restoration host facts: n_uavs 4; 1800 s at 10 s steps; one presampled failure at 300–600 s, site choice {1,2}; fixed per-subinterval path-flow LP; half-duplex backhaul domains; `max_backhaul_hops 2`; TTL/unknown ≠ zero; team-scalar reward; recovery with censoring; no battery or collisions; fixed velocity action; four controllers at `baselines.py:52/72/93/138`; Milan presets refuse to run without a cache.

---

### Strongest simpler alternative and competing programme

**Simpler alternative [I].** Ordinary planning is the answer on S7-S2. The S7 learner pattern is ordinary finite learning plus deterministic-argmax nonactivation, which no replication count repairs. The restoration fixture is already saturated by an ordinary greedy, so no Claude fit is currently worth buying anywhere until real-data opportunity is measured.

**Competing programme for Claude:**
- (a) Close `energy_relay_benchmark` with the already written round-boundary review (NOTES:6805–6824) as the S7 synthesis; no new S7 fit.
- (b) Put the Milan data decision to the owner now (acquisition, licence, `prepare_milan.py`). Root reports it unresolved; it is the binding constraint.
- (c) If the owner provides data, run a zero-fit readiness read on the Milan preset: backhaul-aware greedy vs static vs the `ideal_full_current_demand` diagnostic, plus per-episode wall. Only a greedy-to-bound gap beyond the reading band motivates a MARL declaration, and even then it is framed against the literature neighbour in finding 3.
- (d) If the owner wants a fit now, the only coherent S7 option is O (anchored offset) as one exploratory package fit, with its modal nonactivation/null conceded, as the memo already says.
- A second alternative for Claude is G0 event-contingent reassignment. Root deferred it for lack of a consequential comparison, and G1's ordinary reassignment was adverse (RESEARCH.md:1356–1363). It is on the owner's cooperative-planning line but has no measured interface. I rank it below (b)–(c).

**One constructive challenge to Root [I].** The memo's resolution principle bites hardest where fits are cheap, i.e. on Root's C/H/L. Root's reviewer estimates about ten native minutes per arm by linear scaling and calls it uncalibrated (RESEARCH.md:1352, 1440). There, ≥ 3 instances per arm is affordable and would make the exploratory comparison readable. Root's reviewer judged no extra fit necessary (RESEARCH.md:1450). This is a legitimate peer suggestion, not a correction: CADC-host instance variance is unmeasured.

---

### What the memo gets right

- **The ranking N′ > O > W′ and its reasons against W′** (a re-parameterised velocity action with weak decision exposure), consistent with REVIEW findings 1–3.
- **Relabelling b05 as learner-vs-learner.**
- **The ≈ 10× cost asymmetry between SET and the macro recipes.**
- **The general point that single-instance learned-over-planner increments on S7 sit inside the reading band.**
- **The verified T3 host facts** and the honest statement of T3's planner-host risk (MEMO:106).
- **Its handling of the round-1 critic's O proposal.** It declares O as a package, with H_central@10 primary, the zero-initialised mean caveat (REVIEW:49), a nonactivation reading and the modal outcome conceded. The only loss is the critic's "second reading vs R", which the memo keeps as "by agreement".
- **Root is right on the points the memo concedes:** nonactivation is distinct from active adverse ranking, and cross-panel ranking is invalid.
- **Quoting Root's 09-26 clause back** is a good instinct; the characterisation needs the correction in finding 8.

### Not verified

- The Pro answer (NOTES:6834 empty).
- S7 seed SD; CADC/MultiUAVEnv instance variance.
- Milan-preset per-episode cost, and whether the node holds a Milan cache (not searched; Root reports it absent locally).
- Whether fixture "event seeds" vary anything (inferred from the explicit event and analytic demand; not executed).
- Whether a clairvoyant arm would exceed .02 (inference from freshness evidence only).
- Persistent_service clip fraction (not recorded).
- The MobiCom'24 paper's full text (paywalled; I read the arXiv follow-up 2505.08448v2 pp. 1–3 first-hand).
- Whether O⊕R is implementable without redefining R's search set (inferred from the wrapper text).

---

### MATERIAL_DISSENT: yes

This concerns sending the programme proposal to Root as written, and it rests on the direct evidence above. Three items must be resolved before the DM sends:

1. **Rebase §6 and §3 on Root's adopted selections at `613c8bcfc`.**
   - O_H/P and C/H/L are funded.
   - G0 exists and was deferred.
   - T3 is Claude's uncontested other-host option.
   - Withdraw "Root owns D1", "B1/B2 unfunded until a host exists" and "no host with exogenous roster change". Present D1 at most as an optional suggestion to Root, with its readings corrected (finding 7).
2. **Replace B3's readiness design.**
   - Step (1) is TRIED and its rule is fixed in advance by construction.
   - Correct "real Dec-POMDP / aged telemetry" to the host's actual condition: central shared telemetry, delay 0, TTL staleness.
   - Make the owner's Milan data decision the first gate, and make the informative read greedy-vs-ideal-information bound on real data.
   - Downgrade "NEW to the record" to store-relative, citing the multi-hop emergency-network MARL neighbour.
3. **Drop D2 from the owner menu** (freshness evidence already in the record; S1/S2 confound; excluded diagnosis). Recast option (B) or remove it, since the macro recipes are Root's and were stopped against unchanged replication.

Non-blocking corrections: "still improving"; the fault-rate denominator and signature mix; the off-by-one RESEARCH citations; central vs local inputs for O; "≤ .06" vs +.063; the EV and clip generalisations; "indistinguishable explanations" (persistent_service discriminates); ordinary increments are not caps; restate the ≥ .10 criterion as resolution, not a gate.

### Recommendation

**Revise; do not reject.** The direction survives:
- no new S7-S2 fit for Claude;
- O only as a conceded one-instance exploratory package if the owner wants a fit;
- W′ last;
- the restoration host as Claude's open other-host option.

The route to it does not. The memo predates Root's selections and so misallocates work Root has already assigned. Its B3 readiness step re-buys a recorded, fixture-constructed result. It overstates the host's decentralisation and the question's novelty. D2 is neither clean nor likely to change a decision. Its central "instrument-limited" derivation needs the persistent_service discriminator and the lower-bound correction.

With the three blocking items fixed, the proposal to Root becomes:
- Claude closes S7 with the existing boundary synthesis.
- Claude asks the owner for the Milan data decision and owns a real-data zero-fit readiness read on T3.
- O stays available as an owner-chosen exploratory fit.
- Root is offered, as peer suggestions only, the O⊕R composition and ≥ 3 instances per arm for C/H/L.

Integrate the Pro answer when it arrives. It can change the O vs N′ order; it cannot change the facts in findings 1–3.

---

**Files cited (absolute):**
- /home/fires/hmasd-wsl/docs/research/candidates/energy_relay_benchmark/successor_selection_20260928/MEMO_PROGRAMME.md
- /home/fires/hmasd-wsl/docs/research/candidates/energy_relay_benchmark/successor_selection_20260928/REVIEW.md
- /home/fires/hmasd-wsl/docs/research/candidates/energy_relay_benchmark/NOTES.md
- /home/fires/hmasd-wsl/docs/research/RESEARCH.md
- /home/fires/hmasd-wsl/docs/Claude_docs/inbox/20260928_joint_next_round_plan_ROOT.md
- /home/fires/hmasd-wsl/docs/Claude_docs/inbox/RESEARCH_PROGRAM_RESET_RESPONSE_FOR_CLAUDE_20260926.md
- /home/fires/hmasd-wsl/docs/Claude_docs/changes/2026-09-17-uav-service-restoration-v0.md
- /home/fires/hmasd-wsl/docs/research/candidates/uav_persistent_service/NOTES.md
- /home/fires/hmasd-wsl/docs/research/candidates/uav_joint_transition/NOTES.md
- /home/fires/hmasd-wsl/docs/research/candidates/uav_active_sensing/NOTES.md
- /home/fires/hmasd-wsl/docs/research/candidates/uav_roster_memory/NOTES.md
- /home/fires/hmasd-wsl/docs/research/candidates/sequential_coordinator_credit/NOTES.md
- /home/fires/hmasd-wsl/envs/uav_service_restoration/observations.py
- /home/fires/hmasd-wsl/envs/uav_service_restoration/README.md
- /home/fires/hmasd-wsl/configs/uav_service_restoration/smoke_fixture.json
- /home/fires/hmasd-wsl/configs/uav_service_restoration/milan_site_outage.json
- /home/fires/hmasd-wsl/configs/config_1.py
- /home/fires/hmasd-wsl/runs/energy_relay_benchmark/b05_read_c06_a01/readers.json

**Sources:**
- [Xu et al., Scalable UAV Multi-Hop Networking via MARL with LLMs, arXiv 2505.08448](https://arxiv.org/abs/2505.08448) (PDF pp. 1–3 read first-hand)
- [Xu et al., Scalable MARL for Effective UAV Scheduling in Multi-Hop Emergency Networks, MobiCom 2024](https://dl.acm.org/doi/10.1145/3636534.3694730) (abstract via search only; page returned 403)
