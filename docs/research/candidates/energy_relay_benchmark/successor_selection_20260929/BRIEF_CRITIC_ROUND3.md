# Critic brief — round 3: independent review of the Oracle memo selecting two Claude directions (2026-09-29)

Object: `successor_selection_20260929/MEMO_ROUND3_TWO_DIRECTIONS.md` (c03aeb75a), answering the brief
`BRIEF_ROUND3_TWO_DIRECTIONS.md`. The memo proposes D1 `anchored_joint_target_refinement_s7s2` (learned
bounded offset over H_central@10 on S7-S2, identity-anchored, one CUDA fit, needs the owner's concession under
Pro's standing dissent) and D2 `coupled_host_joint_skills_stage1` (scenario-2 parameterisation as a cheap
coupled host; planner-proven coupling gate; HMASD D-route ×3 vs matched-information SET ×3 on CPU; B12
interaction reader; gated SeqAU credit cell). Separate context; evidence-first reconstruction; you own
MATERIAL_DISSENT. Read-only, no writes anywhere.

Round-2 failure modes to check against (read `successor_selection_20260928/REVIEW_TWO_DIRECTIONS.md` and the
Pro answer under `## Pro question 2026-09-28 two-directions-selection` in
`docs/research/candidates/energy_relay_benchmark/NOTES.md`): fabricated host facts (arena/coupling),
re-cited withdrawn premises, an experiment instance called a new question, a sensitivity reading used as a
screen, cost with gaps, an attribution study presented as an algorithm direction.

Withdrawn premises (must not appear): ".05–.12 is a seed SD"; "I1 never fitted"; "4 km / 6 km restores relay
coupling"; "1,500 m hard cut-off"; "k = 50 needs no code"; "N4 is a config change"; "first reward requires
joint connectivity"; "deployment not a function of the world".

Answer in order:
1. Host and code facts, file:line, recomputed yourself: (a) the channel constants the memo's link-reach
   DERIVATION uses — `envs/pettingzoo/uav_env.py` 117–121 gives noise −80 dBm while `configs/config_1.py`
   83 gives −94 dBm: which applies to `scenario2.UAVCooperativeNetworkEnv` as the launcher/runner would
   construct it, and does the 2.39 km / 3.87 km forced-relay reach survive? (b) `ground_bs_tx_power`
   pass-through, static users, cluster clipping, absence of an n_uavs pin, the reward composition
   (769–838) and the O(N²)/BFS per-step cost; (c) for D1: H1r10 = `H1` at replan 10, `switch_margin_m`, the
   SET recipe (`b02/configuration.py`), whether the S7 state carries H's replan inputs, and whether the
   "macro learner 10× smaller PPO batch" difference is real and what it does to the comparison;
   (d) whether `hmasd/ha_ctse.py` is a live consumer that makes the prefix-usage reader a genuine
   decision object; (e) the cost anchors (S7 SET rates; S1-class CPU fit times; R's query cost ×3).
2. D1: is the identity contract complete (deterministic c00 = H per action; stochastic c00 calibration
   before any fit; no post-score adjustment)? Is "R re-matched under the O contract" a legitimate secondary
   comparator or a re-skinned Codex asset? Does D1 satisfy Pro's dissent conditions verbatim, or does it need
   the owner's concession — and is [DECIDE-1] stated honestly? Which outcome row is modal, and does any row
   change a real deployment/investment decision?
3. D2: (a) is the planner gate (P_relay − P_flat ≥ .05, re-optimised no-relay member of the same search)
   the right coupling proof under the adopted rule, and is one declared re-parameterisation (6 km) a
   legitimate pre-declared branch or a search for a positive gate? (b) Is D2 an FSD reopening in disguise
   (the FSD reopening condition text at `flexible_skill_duration/NOTES.md` 4120–4139), an SCC re-entry, or
   a genuinely new decision object? (c) Is the matched-information SET arm the "competent flat baseline on
   this host" FSD named, and is the recipe choice (D-route d2 for the B12 collector; D128) defensible?
   (d) Are P1–P4 falsifiable intermediate predictions with honest odds, and is cell 2's gating (P3 ∧ P4)
   a legitimate constructive continuation or an automatic retry allowance? (e) Type label: does D2 count as
   a cooperative-planning algorithm direction in the owner's sense, an instrument stage with a gated
   algorithm cell (the memo's label), or neither — and how must it be presented?
4. Independence: by decision object and comparator, D1 and D2 against each other, Codex Q1
   (`uav_persistent_service` deadline-aware reassignment before F) and Q2 (`uav_message_content` scalar slot),
   `uav_joint_transition`, `uav_radio_placement`, `uav_cooperative_planning`, `complementary_skill_learning`,
   `agent_count_generalization`, FSD and SCC reserves.
5. Constructive-development method (1d65ea4ca; item 6(b)): for each direction, which recorded positive it
   develops, whether its prediction/stop/cumulative-cost line is stated, whether the ordinary comparator gets
   the same addition; and, looking back, whether any Claude-line stop that D1/D2 build on was premature and
   what derivation would have been warranted. Also judge the memo's disagreements with the brief (JDSL AR gap
   not a positive; FLAT as flat competence; two algorithm directions not purchasable).
6. TRIED / RECORDED / NEW for D1 and D2 against the stores, the July record and the RESEARCH rows; a miss
   in a store is not novelty.
7. Cost completeness for each (fits, steps, panels, engineering, review, node queueing, resume risk) and
   the smallest change that makes each worth its cells.
8. Ranking; [DECIDE] items only where the owner's; MATERIAL_DISSENT yes/no with the specific change that
   resolves it. Tag [V]/[I]/[C]; cite file:line and paper ids with paths.
