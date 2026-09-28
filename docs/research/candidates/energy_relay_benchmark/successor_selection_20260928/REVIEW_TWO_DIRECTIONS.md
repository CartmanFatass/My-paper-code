# Independent scientific review: Oracle memo `MEMO_TWO_DIRECTIONS.md`

Saved verbatim by the DM from the hmasd-research-critic hand-back (separate context, read-only), 2026-09-28, main at b0467a6b9.

Independent scientific review: MEMO_TWO_DIRECTIONS.md (Oracle memo selecting directions A and B). ResearchCritic, separate context, read-only.

**Context disclosure.** I am a fresh subagent. I did not inherit the DM, Root or Oracle conversations. The assignment brief did carry the DM's list of checks and a one-line summary of the memo. I read the memo early because it is the object of review. I then rebuilt each load-bearing premise from the primary files before judging it. Scratch files (two pure-arithmetic scripts, `linkbudget.py` and `geom.py`) are under `temp/directions/energy_relay_benchmark/scratch/critic-two-directions-20260928/`. Nothing else was written, and nothing was run on the node. Checkout: main at b0467a6b9.

Tags: [V] read first-hand; [I] inferred from [V] facts; [C] conjecture.

---

## Verdict in brief

- **B (coordinator label credit on S1): reject.**
  - The memo labels B "RECORDED, never fitted". That is false. B's first form was fitted (B13, six fits) and read adverse.
  - FSD's recorded reopening condition is not met.
  - The possible effect is below seed noise at n = 3.
  - S1 is an additive host with no coordination term, so B is off the cooperative-planning line.
- **A (autoregressive-link ablation on a reduced relay host): revise.**
  - The proposed 4 km / N4 host probably loses the relay coupling that makes the question matter.
  - The preset is not "config fields only": the shared validator pins N = 8.
  - A's "coupled host" premise re-cites statements this notebook has already withdrawn.
  - The project's own measured assignment stake predicts the modal null for cell 2.
- **[DECIDE] items:** DECIDE-1 revise; DECIDE-2 reject; DECIDE-3 is operational, not an owner item; DECIDE-4 conditional.

---

## Findings, most consequential first

### 1. B is a new name for a scheme that was fitted and failed; DECIDE-2 asks the owner to override a recorded reopening condition, not to satisfy it

**1a. I1 was fitted, and read adverse.** [V]
- The memo row C2 and §2B say "FSD I1/I2/I3 … never run" and "RECORDED, never fitted".
- `docs/research/candidates/flexible_skill_duration/NOTES.md` 3352–3380: "Idea I1, first form" is B13. It is an external additive label bandit driven by B12's count regression, with six fits.
- NOTES 3910–3997 reads B13:
  - P1 held: the exposure mechanism engaged.
  - P2–P4 failed. BANDIT J45 minus D1280 was −.053 / +.087 / −.071.
  - A coordinator that takes no optimizer step matched D1280 (UNIFORM R − D late window, mean +.042).
  - The DM wrote: "I do not build the in-learner form" and "stop spending fits on high-level label credit here".
- NOTES 4073–4140 narrowed this to a resource judgment. Reopening needs "a competent matched-information baseline on this host, or a mechanism with a native prediction for an unfixed duration — not a small η², a high entropy, an unused head, or a new name for a failed scheme."
- NOTES 4201–4250: B14 (zero fits) gave mean G = +.005 at the UNIFORM checkpoints. It was the named reversal test, and it did not reverse the judgment.
- NOTES 4252–4285: the owner rested the direction ("可以 那么做好收尾吧").

**1b. B rests on exactly the evidence the condition rules out.** [I]
- B is the in-learner form of I1.
- It is justified by η² ≈ 10⁻⁴ and entropy 1.78, which the reopening condition names as insufficient.
- The shared index still holds the stop. `docs/research/RESEARCH.md` 1052 (FSD row): B13/B14 did not reverse the stop, and no new positive has overturned it. RESEARCH 1342 and 1542 list the FSD pause among retained shared controls. [V]

**1c. The possible effect is below noise at n = 3.** [V → I]
- B12 (NOTES 3198–3298) puts the whole all-equal label spread at cap 10 at .02–.03 J.
- B14 realised a mean of +.005.
- Seed SD on S1 is about .08 J (B13 technical paragraph; memo cites .055–.08).
- A difference of three block-paired fits has SE ≈ .08/√3 ≈ .046. So:
  - "J reaches FLAT" (about +.045 over D) is about one SE.
  - "J up vs native, < FLAT" is unreadable.
- Only the law readings are readable, and B13 already showed that a sharper law does not become J. B's conceded modal outcome ("law sharpens, J within noise") is therefore a known result.

**1d. B is off the main line.** [V]
- S1 has no coordination structure: B12's homogeneity term is slightly negative, i.e. diminishing returns, not a coordination requirement.
- S1 is `UAVBaseStationEnv`: "不考虑回程和中继" (no backhaul, no relay) — `envs/pettingzoo/scenario1.py` header.
- A credit fix there is not cooperative swarm planning.

**1e. The "SCC E3 win" is overstated.** [V]
- `sequential_coordinator_credit/NOTES.md` 380 carries forward that the one regime where credit wins (annealed entropy) "is confounded by joint-normalisation scale acting as a smaller effective entropy coefficient".
- SeqAU's microhost gain was learning speed, not endpoint. It bought "nothing at the host-like endpoint".

**1f. The k = 50 arm, as the memo specifies it, would silently run k = 10.** [V]
- `hmasd/agent.py` 491–504 reads `skill_cap_k_max` only when `policy_interruption_mode == 'd2'`. In `off` mode, `d2_k_max = config.k`.
- FSD's I2 record (NOTES 3302–3306) keeps `config.k = 10` as the low-level BPTT chunk and sets caps through the D (d2, infinite-cost) construction.
- The memo says "authentic D0 fixed clock as the base (no interruption) … k = 50 via `skill_cap_k_max` … needs no code". That is under-specified. Implemented literally in `off` mode, the two cap arms are identical.
- The five-fold fewer coordinator samples per rollout is real under d2 caps (B12: 800 / 160 team rows per rollout). This only matters if B were kept.

**Simplest competing explanation.** The FSD coordinator does not matter on S1 at all (B13 R − D). Any credit change can only reshuffle a label law whose largest attainable effect is a few hundredths of a J.

### 2. A's reduced host probably removes the coupling that justifies A; the preset is not config-only

**2a. The memo misidentifies the link range.** [V]
- The "1,500 m 3-D radius" is `observation_radius` (`configs/config_1.py` 115), not a link range.
- Links are SINR thresholds (`min_sinr` 3 dB) on absolute path loss: free-space A2A, urban A2G mixture (`envs/pettingzoo/relay/channel_geometry.py` 33–137; `routed_core.py` 3237–3288, 4360–4450).
- Capacity comes from the MCS table (`routed_core.py` 346–358).
- Under FDMA (`use_fdma=True`, config 43), per-link bandwidth is 20 MHz / n_uavs (`routed_core.py` ≈ 4433). N4 therefore doubles per-link capacity relative to N8.
- Base-station and cluster geometry scale with `area_size` (`routed_core.py` 596–760; the remote cluster is placed at the corner opposite the base station).
- `n_clusters`, `n_remote_clusters` and `area_size` are real attributes (config 35, 71–76).

**2b. Link budget from those constants.** [I]
- Assumptions: interference-free, UAV at 170 m, native backend not run.
- UAV→BS uplink reaches 3 dB at about 4.2–4.4 km. At 4.0 km it is 10 Mbps at N4 (5 Mbps at N8).
- UAV–UAV links reach about 5.9 km.
- Sampled base-station → remote-cluster-centre distance with the host's placement formulas:
  - 4 km arena: median 4.39 km (5–95 %: 3.93–4.89 km); 28 % under 4.2 km.
  - 8 km arena: 7.9–9.8 km.
- The remote cluster's demand is about 6 users × 1 Mbps. At 4 km, a UAV stationed slightly toward the base station can serve it and backhaul directly in many worlds.
- The coupling drops from a multi-hop chain to 0–1 relay. The memo's own "≥ 1 hop in ≥ 90 % of worlds" host test is likely to fail or pass only marginally.
- This corroborates Pro's earlier derivation, adopted in `energy_relay_benchmark/NOTES.md` 5804–5830 (entry 2): 3 dB at ≈ 4.3 km A2G, ≈ 6 km A2A, "connectivity needs at most one relay hop anywhere on the 8 km square". It is not a new dispute.

**2c. The preset needs a shared-contract edit.** [V]
- `_validate_scenario7_preset` (config 650–664) requires `n_agents == 8` and `max_observed_uavs == 8`.
- `S7-S1m` therefore needs an edit to the shared contract plus engineering review. That edit is not costed in the memo.

**2d. A's premise re-cites withdrawn statements.** [V]
- Memo §0 bullet 3 cites "reward conjunctive (coverage ∧ backhaul)" and "the learner's deficit is a deployment that is not a function of the world".
- Entry 2's withdrawal table (NOTES ≈ 5837–5854) withdrew both:
  - replaced by "graded QoS + smooth potential; non-zero at t = 0 in ≥ half the worlds";
  - "withdrawn as fact → map-frame heading bias keyed to index/spawn slot".
- Entry 2 item 3 also records "chains were never the hard part of this host".
- The measured b03 hop statistics (.908 share, 3.28 intermediaries) stand. The memo builds "remote cluster reachable only through a relay chain, conjunctive reward" on the withdrawn half.

### 3. A's cell 2 is predicted null by the record's own stake, and its likely paid outcome is an instrument failure whose stated belief change does not follow

**3a. The record's measured stake predicts the modal null.** [V → I]
- Stage 2-0 (NOTES 5069ff; SCC NOTES ≈ 386): Hungarian − identity = +.007 ± .007, while independent-nearest = −.324.
- The work the z_<i link could do is de-duplicate agents. A fixed identity-keyed assignment already captures almost all of the gain over optimal matching.
- In the `team_only` control, identity still reaches the head through `agent_specific_query` and the entity positional encoding (`hmasd/networks.py` 786–790, 825–832).
- Root's accepted narrowing (SCC NOTES 386–390) says the stake is **not** an upper bound. So this is a source-supported prior for AR ≈ control, not a bound.

**3b. The decoder read is correct; the control has two design issues.** [V]
- Correct: z_i is decoded from [Z0, Z, z_1..z_{i−1}], concatenated with the agent's encoded observation before `agent_skill_head` (`networks.py` 636–668).
- `team_only` would also change sequence length and the index of the last token's position. A same-length control with a constant token in place of z_<i isolates teammate *content*. This is a design refinement, not a fatal confound.
- "Width-matched head": parameter counts are already identical, apart from the unused `agent_skill_embedding`.

**3c. The likelier paid outcome is gate failure in cell 1.** [I]
- HMASD's own paper reports 26/35 runs learning meaningful behaviour (MARL-0553 appendix F, p. 17–18).
- S7 HMASD records are QoS .15–.19 at 180k (`uav_service_auxiliary/NOTES.md` 270–384) and .339 per planned step at 360k (10318–10332). The memo's ".24" is wrong; direction unchanged.
- The S7 instance spread is .05–.12.
- Gate (ii) asks for seed SD ≤ .025 estimated from three seeds; that estimate is itself close to a coin flip.
- At n = 3 with SD near .05, the paired SE is about .03–.045. The .05 threshold is therefore 1–1.5 SE.
- If cell 1 fails, the memo's stated belief ("deficit is conjunctive-reward/exposure, not arena scale") does not follow. That fit would be 300k on a host whose FDMA physics and coupling changed.

**3d. Smallest worthwhile observation.** [I]
- On cell-1 checkpoints, at zero fits: intervene on z_<i at fixed state and read the change in z_i's distribution (KL, or argmax flips).
- If the trained decoder ignores z_<i, cell 2's three fits buy nothing.
- This changes whether cell 2 is bought. It is not a gate before cell 1.

### 4. Novelty labels and the constructive-exploration claim are overstated

- **HMASD paper** (MARL-0553; `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0553.json`, `pdf/MARL-0553.pdf`): §4.3 ablations are NoTeam / NoIndi / NoExRew / NoInRew / NoHigh. Appendix D (p. 16) covers only k, n_Z and n_z. The z_<i link is unattributed in the paper; the memo is right. [V]
- **The general AR-vs-independent question is already recorded.** [V abstract level; PDF not read]
  - Fu et al., ICML 2022, "Revisiting Some Common Practices in Cooperative MARL": auto-regressive policies represent multi-modal joint behaviour that independent or shared policies miss ([PMLR](https://proceedings.mlr.press/v162/fu22d.html), [arXiv](https://arxiv.org/abs/2206.07505)).
  - MAT; ACE (MARL-0002); Sable (MARL-0485).
  - The memo's neighbour list omits this family. A is correctly RECORDED as a question; "NEW" applies only to the single-link, coupled-host instance.
- **JDSL's "AR" is not the z_<i link.** [V] In JDSL, "AR" is a *duration mode* (`joint_duration_skill_learning/NOTES.md` 1019–1062). It is also one instance per arm with different seeds, and below fixed at every learned panel. §2b's "JDSL's AR > factored (+.019)" is not a positive about the z_<i link.
- **Neither direction embodies the owner's constructive-exploration request.** [I] The memo concedes that neither adds a resource. B extends a result already read negative. A builds on host facts (coupling, dispersal) rather than a capability to extend.

### 5. Premature stops by the constructive standard

- **C6 (relational goal decoding).** [V → I]
  - Entry 2's pre-written decision table (NOTES ≈ 5866, row A) says "R + A returns only if B fails to move the deployment readings".
  - b05 (6776–6805) read P1 and P2 as not met.
  - So the notebook's own condition for returning a *rewritten* relational candidate was met. Entry 2 lists the rewrites: continuous fraction, centroid endpoints, common low level, composite-ablation wording.
  - The memo rejects C6 on entry-1 grounds (R51, T′ closed, Pro's dissent against entry 1's readings). None of those address the rewritten form.
  - The warranted step was that derivation. Relational goals are also where teammate conditioning is load-bearing by construction; entry 2's reframing ("symmetry breaking through autoregressive conditioning on teammates' goals") is exactly A's link.
  - Any revival must still answer Pro's §7 reasoning and the owner's exclusions. The choice belongs to the owner and Pro, not this review.
- **C5.** Correctly excluded: the owner barred energy-relay diagnosis continuation, and the fit falls inside Pro's dissent.
- **C14 and C8.** Defensible. C8 is dead by the +.007 stake.
- **C9.** The Root-owned richer contracts are legitimately declined on ownership. But no Claude-owned richer contract was derived either.

### 6. Pro's S7-S2 dissent and the flat arm (items 9, DECIDE-4)

[V] Pro §7.1 and §8 (NOTES 6834+254 to +302) are worded for the S7-S2 host and the SET family: "不购买新的 S7-S2 fit" and "相同宿主…第三次". A central-input (CF) flat learner on a mini host is not literally the "third same-family fit".

[I] Pro's reasoning about decision exposure still applies to any learned-vs-planner claim. A escapes it only while it stays attribution-only.

DECIDE-4:
- **No** for attribution-only A.
- **Buy the flat row only if** A is reframed as a competence question: "can any learner reach planner-relative competence on a reduced coupled host?" In that case the flat row is the ordinary learning comparator.

### 7. Overlap (item 8)

[V] Neither A nor B shares a decision object or comparator with any current Root or Codex row: uav_*, energy_relay_*, cooperative_planning, transit_handoff, G0, O⊕R, C/H/L (RESEARCH 1000–1100, 1299–1347).

A inherits the archived `complementary_skill_learning` (1063) and JDSL evidence. B has no Root collision, but it does collide with the FSD pause.

### 8. Cost (item 6)

- [V] .046 s/transition (180k in 8,318 s; `uav_service_auxiliary/NOTES.md` 272).
- [C] The mini-host projection of .02–.046 s is plausible.
- [I] Not costed:
  - the validator edit and its review;
  - adapting the planners to N4 (`b01` H_central uses `n_relay = 2` at the ⅓ / ⅔ points), which is more than a "0-fit regeneration".
- B's 12 CPU fits (15–25 h) are plausible but moot.

---

## What the memo gets right

- Premise (1) holds on the S7 records: arm C .152/.191 at 180k; June arm A .143. Small error in the B09 number (see 3c).
- The decoder read is correct.
- The memo flagged DECIDE-1's precondition itself, named the k = 50 sample confound, and says openly in §5 that A's first cells are instrument, not contribution.
- It correctly declines S7-S2 package fits and untied-k standalone. B12 shows no duration structure on S1; relay_corridor's E-series is exhausted.
- It correctly ranks untied-N as crowded: `agent_count_generalization` archived, `variable_n_fleet_churn` reserve, `uav_roster_memory` Root's.

---

## Strongest simpler alternative programme (item 12)

- **One direction may be better than two.** Constitution §2 owes no replacement or quota. The second slot is better left empty than filled with B.
- **Keep A, revised** (see recommendation below).
- **If the owner wants a second direction,** the warranted candidate is the rewritten relational/teammate-conditioned goal decoder (§5 above), on the same reduced coupled host. It needs a fresh §5 review and has to answer Pro's §7. It could merge with A, with the autoregressive ablation as its internal control.
- **Untied-N and A-stage-2-first remain constrained** as the memo says. Their instrument and host dependencies are real.

---

## Not verified

- HMASD history on coupled hosts other than S7 (no RESEARCH row found; archives not read).
- Whether the b01 planners parameterise on N.
- JDSL and FSD CF wall times.
- S7 seed SD (unmeasured on record).
- Current `wsl_4070` occupancy.
- The primary passage of Fu et al. (abstract level only).
- My link budget omits interference and does not run the native geometry backend.

---

## MATERIAL_DISSENT: yes

Tied to two specific investments:

1. **B's 12 fits and the DECIDE-2 reopening.** Direct evidence:
   - FSD NOTES 3352–3997 (B13 is I1's fitted form, P2–P4 failed);
   - 4073–4140 (the reopening condition);
   - 4201–4285 (B14 and the rest);
   - RESEARCH 1052 and 1342.
2. **A's cell 2 and the S7-S1m host as declared.** Direct evidence:
   - config 115 and 650–664;
   - FDMA at `routed_core.py` ≈ 4433;
   - the link budget [I] matching NOTES 5804–5830;
   - the withdrawn premises (NOTES ≈ 5837–5854);
   - the stake +.007 as a prior.

**What resolves it:**
- (i) Withdraw B and DECIDE-2. Or bring new evidence that meets FSD's recorded condition.
- (ii) For A:
  - choose the arena from the link budget, so that ≥ 1 relay is needed under N4 FDMA (likely ≥ ~6 km), and pass the hop test before any fit;
  - price the validator edit;
  - remove the withdrawn "conjunctive / not a function of the world" premise;
  - make cell 2 conditional on the zero-fit z_<i-sensitivity reading, with a same-length constant-token control;
  - state gate failure as the likely modal outcome, with a belief line limited to "not competent at 300k on this reduced host".

## Recommendation per item

| Item | Recommendation |
|---|---|
| B | Reject |
| A | Revise (as above) |
| DECIDE-1 | Revise: arena from the link budget, validator edit priced, hop test first |
| DECIDE-2 | Reject |
| DECIDE-3 | Operational, handled by node admission and the one peer message; not an owner decision |
| DECIDE-4 | No for attribution-only A; yes only if A is reframed as the competence question |
