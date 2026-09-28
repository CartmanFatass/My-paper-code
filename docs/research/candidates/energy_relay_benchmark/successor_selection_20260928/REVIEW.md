# Independent scientific review of the Oracle memo "W" (hmasd-research-critic, separate context, 2026-09-28)

Saved verbatim by the DM from the critic's hand-back (the role body forbids its own record writes). Tags: [V] verified first-hand by the critic, [I] inferred, [C] conjecture. DM annotation: finding 1 re-verified by the DM in `experiments/candidates/energy_relay_benchmark/b01/heuristic.py:318–324` (velocity = delta / dt, scaled down only above cruise; a target > 30 m away is flown at full speed, then hover).

## Findings, most consequential first

**1. The memo misreads the executor. W does not learn "where" while leaving "how" to an ordinary planner. It learns a trajectory, built from 10 s straight moves.** [V]
- `b01/heuristic.py:318–324` sets `velocity = delta / time_step_s`, then scales it down only when the speed exceeds cruise (30 m/s). Any target more than 30 m away is flown at full speed, and the UAV hovers once it arrives.
- The 300 m disk equals exactly one commitment's reach (30 m/s × 10 s). The executor adds nothing beyond one straight fly-then-hover segment; there is no persistent destination that an ordinary planner reaches.
- The memo's rationale for r_max (§3: "a larger disk would make most exploration samples full-speed moves") is contradicted: with targets uniform in the disk about 99 % of samples have |Δ| > 30 m and start at full speed; roughly two thirds of the steps are at full speed [I: E|Δ|/300 = 2/3].
- Consequences: W is effectively the old SET velocity interface re-parameterised with a 10-step hold and a fly-then-hover speed profile. Its §6 "complement of `uav_joint_transition`" claim is mislabelled (the estimands still do not collide: joint_transition holds R destinations common, `inbox/20260928_joint_transition_scope_ROOT.md:7`; W learns no station, return or dwell choice). Root's reviewer already records that "existing free-action SET learning also prevents claiming that spatial control has never been attempted" (`RESEARCH.md:1333`). Full-speed flight is not harmful in itself (planners fly at full speed on .26–.29 of steps with return cost 3.4–4.8, `NOTES.md:2507–2520, 5945`); the point is that the memo's energy and minimality argument rests on a wrong reading of the executor, and only the random-target floor would show how costly W's initial high-motion regime is.

**2. This is a package comparison, not "component attribution". Both belief rows of the outcome table go beyond what the design can support.** [V] list of changes, [I] consequence.
- Against SET, W changes at least six things at once: action parameterisation, cadence, PPO decision horizon (300 vs 3000 decisions per episode), samples per update, speed profile, and a fixed 100 m altitude (the memo folds the last two into one "executor prior").
- The altitude change is not controlled: SET c06 spends ≈ .47 of normal-mode UAV-steps at the 50 m altitude floor (`NOTES.md:3259`); planners fly at ≈ 98 m, N at 67.9 m (`NOTES.md:2507ff`). Whether altitude alone moves service is unverified [I], but it is a free ordinary prior bundled into W.
- "Positive → the deficit was in the interface/cadence, not the placement decision" does not follow (gain could come from altitude, speed profile or horizon). "Flat → placement learning is the deficit" also does not follow (memo concedes, §4 row 3, §11.4).
- No single-member fit arm should be bought: withdraw the attribution claims and call W a learner-package comparison; a velocity + k-hold arm doubles the cost without changing any planning choice.
- If W proceeds, add two zero-fit controls: the random-target floor (already in the memo) and **frozen c06 with its vertical command replaced by the executor's 100 m height controller** (C_SW_FULL pattern, ≈ 15 min; a control inside the declaration, not a diagnosis successor).

**3. W is weakly exposed to the owner's main-line decision.** [I]
- Ordinary planning sits at H_central@10 .769 (`NOTES.md:2507`) and H_central .774 (`:3250`); SET c06 .437/.438 (`:3248`); C_SW .4574/.4635 dev (`:6611`).
- Only the memo's "W ≥ .70" row changes the answer to "does MARL enhance cooperative planning here", and the memo gives that row no probability (its guesses: 45 % flat, 20 % adverse, 30 % positive with positive defined as ≥ +.05 above control ≈ .49+).
- In every other row ordinary planning stays the answer and the only change is an internal learner reference plus a second-seed purchase — continuing work on why the flat learner lags, the diagnosis/attribution continuation the owner excluded (`NOTES.md:6731–6733`).
- The primary comparator should be H_central@10 (package reuse), SET secondary, and the declaration should state beforehand what the modal outcome concedes.

**4. Instance noise makes the ±.05 and +.10 bands weak.** [V] numbers, [I] reading.
- S7 seed SD unmeasured; the replication attempt in `energy_relay_baselines` ended with two technically failed fits.
- b05 B vs SET at matched checkpoints: c02 −.027/+.010, c03 +.120/+.073, c04 −.007/+.032 (`NOTES.md:6679–6681, 6690–6694, 6722–6727`) — not a seed SD (frame condition differs, evaluator thread settings cross) but a spread between instances and checkpoints of ≈ .05–.12. So +.05 sits inside plausible instance noise and +.10 is marginal; a flat result is uninterpretable. The declaration cannot freeze before b05's c06 read.

**5. Novelty and the owner's stance.** [V] searches, [I] owner reaction.
- No waypoint-interface learner in the July R29–R54 record; `docs/new-libs/LIBRARY_INDEX.md` has no hierarchy/goal content beyond `:63`; MyLib titles hold seven hierarchical-MARL papers (HAVEN, HCPO, HMASD, HMARL-CBF, L2M2, …), none a fixed-executor waypoint learner.
- The memo itself calls the pattern standard applied UAV-MARL practice with no novelty claim; with finding 1 (a re-parameterised velocity action), W is at high risk of being judged an old idea — a re-skinned action space for an existing baseline; on the "engineering innovation" branch it offers no new pattern either.
- HMARL-CBF (MARL-0621) is not what the memo says: its low level is a *learned* parametric CBF-QP trained jointly with the high level (p.4 Fig. 1 caption; p.7 "learning the parameters of the QP"); its high level picks discrete skills. "Fixed CBF-based safe low-level execution" is contradicted; not a close neighbour.

**6. Other claims checked.**
- Reference levels H_central .774, H_central@10 .769, H_local .597, SET c06 .437/.438 (hold-out .462/.440), C_SW .4574/.4635 dev, .4631/.4774 hold-out: **verified** (`NOTES.md:2507, 3248–3251, 6611–6612`).
- Full-fit wall: 0.02736 s/transition (`b02_s1_set_a01`), 0.03401 (`…a01r`), 0.03006 (`b05_canonical_frame_a01`) → 9.1–11.3 h per 1.2 M; Stage 1 recorded 11.0 h (`NOTES.md:3342`); the brief's 5.6 h is a01r's 600k half-fit: **verified**. Slip: b05 a01 records 112 rollouts, not 113.
- b04 phenomenon (e_ROT 158°/146°, WSW heading at t = 0, full-speed share .0003 vs planners .262/.293): **verified** (`NOTES.md:5925–5932, 5945`); the mechanism is open (`:5943`).
- active_sensing: B01's critic named sparse service exposure and near-maximal entropy: **verified** (`uav_active_sensing/NOTES.md:797–801`); but B02 had balanced semantic exposure (1618 service / 1793 probe) and still no package value, its critic pointing to weak finite optimisation (value loss ≈ 1.2e5, explained variance ≈ 0, clip fraction 0; `:1216–1235, 1297–1320`). The memo's citation of `:1305–1320` as "sparse exposure" **mischaracterises B02**.
- cooperative_planning B02 L−P −.016488, holds 4,575/4,582: **verified** (`uav_cooperative_planning/NOTES.md:1051ff`).
- persistent_service non-overlap: **verified**.
- "Residual-over-planner TRIED/declined" (§10) is **contradicted**: RECORDED — designed in `uav_transit_handoff/NOTES.md:161–230` (citing Silver 2018), declined before running.

## Strongest simpler alternative and competing question

**Strongest simpler alternative [I]:** ordinary planning is the answer on this host, and SET's gap is ordinary finite-learning incompetence at 1.2 M transitions. W's modal outcome is consistent with this and adds little to it.

**Competing question (to weigh against W, not a verdict):** keep W's engineering (macro wrapper, executor, controller) and change only the anchor: target = H_central@10's assigned target + a learned bounded offset; per agent, k = 10, same executor, shield and guard.
- Comparator built in at zero fits: c00 ≈ H_central@10 (not bitwise; SET c00's deterministic mean is near zero, `NOTES.md:5292`, but drifts slightly — an exact identity needs a zero-initialised output mean). R (Root's radio-aware target asset) gives a second reading: R−G +.029, R−H +.027 on 8 worlds, J interval crossing zero.
- Decision exposure: answers directly "does MARL add to competent cooperative layout planning?"; every non-shielded agent chooses at every boundary; offsets are simultaneous, relay-chain and coverage overlaps create externalities, team reward shared.
- Overlap: complements joint_transition (Root's review puts learned destination construction on the Claude side, `RESEARCH.md:1346`; radio_placement excludes planner-side learning, `inbox/20260928_expanded_question_scope_ROOT.md:12`); one SCOPE message to Root still owed (DM3 holds the broader reserved question).
- Cost ≈ W's (1 fit, 9–11 h, plus panels).
- Outcomes: positive vs H_central@10 and near R → a learned layout increment over ordinary planning (the owner's line); collapse to zero offset → a declared nonactivation reading; negative → a third learned-over-planner failure on S7-S2, arguing for moving MARL investment to another host.
- Risks: two prior learned-over-planner nulls (coop B02, active_sensing); exploration around H degrades H early; the only evidence of layout headroom is ≈ +.03 from ordinary search; residual policy learning is an ordinary technique and must not be presented as new.

## MATERIAL_DISSENT: yes

Items to resolve before any declaration: (a) correct the executor reading, the r_max rationale and the "destinations vs transitions" complement claim; (b) reframe W as a package comparison and withdraw "interface, not placement" / "placement is the deficit" from the outcome table; (c) make H_central@10 the primary comparator and state beforehand what the modal outcome concedes; (d) add the zero-fit altitude-held c06 control beside the random floor; (e) state that bands under ≈ .10 sit inside the observed instance spread; (f) fix the labels (HMARL-CBF, active_sensing B02, residual = RECORDED); (g) have the DM, and Pro under section 5, weigh W against the anchored-offset alternative before choosing.

## Not verified

S7 seed SD; W's actual wall (env-step share of collection); whether the 306-d snapshot carries the user positions H_central@10 uses; whether altitude (50 vs 100 m) moves service on this channel; node occupancy; the b05 c05/c06 outcomes; the memo's web-cited UAV-MARL papers.

## Recommendation

**Revise; do not retain as written.** As framed, W buys an uninterpretable package reading of the flat learner: a positive result cannot be attributed and a flat one is indistinguishable from instance noise. Its most likely outcomes leave H_central@10 as the planning answer, so it mainly continues the learner-deficit line the owner closed. Its central design rationale rests on a misread executor, and its likely classification as a re-skinned action space is a real owner-level risk. If the session still wants a MARL fit on S7-S2 after b05 closes, the same engineering applied to the anchored-offset question has direct exposure to the owner's decision, a competent comparator built in at zero fits, and every outcome changes a planning or host-investment choice; let Pro weigh W against it. A justified alternative is no new fit on this host: close the flat-learner line with b05's reading and move MARL investment elsewhere. That is preferable to running W unchanged.
