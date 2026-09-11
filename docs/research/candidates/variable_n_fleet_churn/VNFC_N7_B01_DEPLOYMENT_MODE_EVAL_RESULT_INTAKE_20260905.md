# VNFC-N7-B01-DEPLOYMENT-MODE-EVAL result and intake (2026-09-05)

Direction `variable_n_fleet_churn` (VNFC, N2/N7). Card
`VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_SCIENCE_CARD_20260905.md`; CM record
`VNFC_N7_B01_DEPLOYMENT_MODE_EVAL_CM_RECORD_20260905.md` (Opus `hmasd-cm`, integrated at
`6fc57456131300e8f6adbec7d6b044d50a22f783`). Intake by the Claude research hub as Root and DM.
Evidence: `evidence/b01_depmode_formal_20260905_01/` (summary, evaluation and BCRH episode rows,
run log, memory receipt, `/usr/bin/time` record) and `evidence/b01_depmode_check_20260905_01/`.

## 1. What was checked (observation)

- **Launch facts.** Node `wsl_4070`, worktree `/home/wu/hmasd-worktrees/vnfc_b01_depmode_6fc574561`
  at the pushed launch sha (source bytes identical to the CM worktree commit); task
  `vnfc_b01_depmode_formal_6fc574561_20260905_01`, exit 0. Memory receipt passed both floors
  (14.6 GiB available) immediately before the runner. One invocation, no retry. The engineering
  check `…_check_…_02` ran first (exit 0, 5.5 s) and its `b01_greedy_replay` compared **64 of
  64** recorded B01 evaluation rows for the formal MAPR checkpoint on all twelve compared fields:
  the new entry's GREEDY path reproduces the B01 evaluation decoding.
- **Frozen inputs.** Four checkpoints and the B01 reference rows staged at the digests the CM
  record declares and re-verified on the node; loaded parameter counts 89,090 (MAPR) and 148,739
  (DIRECT) per record; `round == 64`; parameter displacement 0.0 for all four.
- **Exposure line.** Training instances 0, rounds 0, optimizer steps 0, backward calls 0,
  parameter updates 0. Policy cells 8, evaluation episodes 512, BCRH episodes 64, policy joint
  decisions 3,072, evaluation action draws 6,144, BCRH complete calls 384, native ticks 138,240.
  Exactly the card's plan. Training seeds counted: 2 (the B01 records; none new).
- **Panel and RNG.** Namespace `VNFC-N7-B01-DEPLOYMENT-MODE-20260905`, world master 2026090505,
  action master 2026090506, 64 worlds (32 per failed zone); GREEDY consumed no draws; SAMPLE drew
  one uniform per token from `eval-actions/<record>/<arm>` under the registered separation label
  (ledger row 2026-09-05T22:25). Single CPU thread for torch and native.
- **Primary result, paired `SAMPLE − GREEDY` on `R_fail_60` (all 64 worlds, mean ± SE):**

  | Policy | all | zone 1 | zone 2 | `U_total` all |
  | --- | ---: | ---: | ---: | ---: |
  | formal_02 / MAPR | −0.0065 ± 0.0178 | −0.0137 | +0.0007 | −0.0330 |
  | formal_02 / DIRECT | −0.0036 ± 0.0036 | 0.0000 | −0.0073 | −0.0435 |
  | seed02 / MAPR | −0.0056 ± 0.0082 | −0.0112 | 0.0000 | −0.0252 |
  | seed02 / DIRECT | +0.0169 ± 0.0121 | +0.0032 | +0.0306 | −0.0224 |

- **Context contrasts (not learner results).** Same-mode MAPR−DIRECT on `R_fail_60`: +0.004,
  +0.001 (formal_02), +0.019, −0.003 (seed02), all inside noise. Every learner cell sits below
  BCRH on `R_fail_60` by 0.055 to 0.074 in both modes and in both zones (BCRH 0.326 overall;
  learners 0.252 to 0.271). SAMPLE lowers `U_total` in all four policies (−0.022 to −0.044) and
  `J_ext` in all four; that service cost is retained as the card requires.
- **Integrity.** Zero safety and zero exclusivity violations across the 512 evaluation and 64
  BCRH episodes; every episode reached its terminal.
- **Telemetry.** Complete wall 44.47 s (runner) and 45.69 s (`/usr/bin/time`), against the
  180 s cap; peak RSS 415 MB (runner) and 413 MB (time); cells 0.77 to 0.83 s each, BCRH 34.9 s,
  native build 1.9 s. Budget: B01 cumulative formal time 783.29 + 44.47 = 827.76 s of 2,700 s
  (the 5.5 s check is a non-target chain).

## 2. Rule applied (verbatim from the card, "Reading rule, written before the data")

> 3. Mixed signs or all within `(−.10, +.10)`: no useful deployment-mode signal at this
> exposure; the question closes at this exposure without escalation to temperature, more
> draws, more panels or more checkpoints.

**Reading: branch 3.** All four primary differences lie within (−.10, +.10) and the signs are
mixed (three negative, one positive); the largest magnitude is 0.017 against the .10 scale.
Deployment mode does not explain a useful part of the learner-versus-BCRH gap for these four
policies at this exposure.

## 3. Bounding observation and the four boundaries

- **Direct observation:** the paired differences above on one shared 64-world panel with the
  four saved final policies; single-draw sampling only.
- **Inference:** none required for the reading. The consistent `U_total` cost of sampling is a
  descriptive observation on this panel, not a tested claim.
- **Scientific result versus engineering conformance:** the reading is a scientific null at the
  declared scale; the engineering check's 64/64 replay is conformance and is what makes the
  GREEDY column comparable to B01.
- **Direction-local advice versus Portfolio action:** direction-local; lifecycle, priority and
  recast count unchanged (recasts 2, lowest sequencing priority among ACTIVE stands).
- **Historical provenance versus current authority:** the B01 two-seed result (both learners
  below BCRH on all four metrics in both zones) stands unchanged; this object neither adds a
  learner sample nor revises it.

Predictions: DM predicted branch 3, with any effect more likely negative for SAMPLE and
smaller than the learner-versus-BCRH gap; observed branch 3, three of four negative, all far
smaller than the gap. Owner slot: not taken (unattended).

## 4. Decisions this intake produces

1. **Object tier:** accept the complete evaluation as a valid branch-3 observation (alternative:
   quarantine for the domain-label deviation). Recommend and select accept: the label choice
   affects only the separation tag of a dedicated stream whose independence is carried by its
   own master and purpose (ledger 2026-09-05T22:25). Owner-delegated decision (unattended,
   2026-09-03 instruction): **accept, branch 3**. `OWNER_DELEGATED`, technical, reversible,
   owner flag none. B objects have no consumption state.
2. **Object tier:** no escalation to temperature, multiple draws, more panels or more
   checkpoints (rule). Selected by the rule.
3. **Direction tier:** the next VNFC object after this closed question belongs to
   `em:variable_n_fleet_churn:convergence` (the node that selected this evaluation). The hub
   authors the post-evaluation Convergence packet with this intake and the B01 two-seed intake as
   evidence, sends it once through the Sonnet transport, and parks VNFC at this clean boundary.
   The packet states the direction's headroom record (none; BCRH is a native reference) and its
   second-recast standing.

Ledger rows appended in `docs/research/portfolio/audit/2026-09-06.md`.
