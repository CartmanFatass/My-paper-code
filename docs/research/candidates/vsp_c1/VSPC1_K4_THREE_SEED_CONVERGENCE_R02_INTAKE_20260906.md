# VSP-C1 three-seed Convergence intake, second dispatch (r02) — 2026-09-06

Direction `vsp_c1` (K4). Node `em:vsp_c1:convergence`, conversation
`6a9cfac6-4d34-83e8-9f0a-088c03f4fb0c` (first binding of this key, 2026-09-05). Request
`2026-09-05-vspc1-k4-three-seed-convergence-02`; packet
`pro_packets/20260905_three_seed_convergence_r02/` (evidence pinned at
`4cb615bbe75a3b2ddf1f6ffb8788e2c66199adb7`). Intake by the Claude research hub as Root and DM.

## 1. Transport facts (observation)

- One Send, hub-direct through Agentify Desktop (the last hub-direct run before the Sonnet
  transport became the standard), labels `Latest` / `Pro`, `COMPLETE`. The short chat receipt
  claimed a GitHub write gap; the direct readback showed the response file and the Issue 5
  comment landed minutes later through the ChatGPT GitHub connector (commit `d650cd966` on
  `codex/pro-vspc1-k4-three-seed-r02-20260905`). Archive:
  `pro_packets/20260905_three_seed_convergence_r02/archive/{RESPONSE.md (37,519 bytes, sha256
  5839aa00…), DELIVERY_COMMENT.json, SHORT_RECEIPT_R02_CLAUDE.md,
  TRANSPORT_FACTS_R02_CLAUDE.json}`; committed at `558007836`. Registry bound
  `DIRECTION_VERIFIED`, `active_request_id` null.
- The earlier misrouted answer (request `…-01`, sent into the Portfolio conversation) is
  preserved as untrusted evidence and is not this node's decision; the r02 response states it did
  not use that text.

## 2. The formed decision (read from the full response file)

**CONTINUE, with exactly one B:** "公开计划下的跨周期价值：新种子 128→512 更新预算对照". FACTOR
and the existing same-information GENERIC each train one fresh seed 3 continuously to 512
updates, keeping the update-128 measurement inside the same training instance. No separate
original-budget seed, no third arm, no exact reference, policy search or mechanism audit first,
no new multi-agent host. The investment ends at the archive and reading of the two complete
invocations; updates beyond 512, other seeds, tuning and any new host receive no budget from it.

Its content, which the card `VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_SCIENCE_CARD_20260906.md`
freezes verbatim in meaning:

- Host, information, treatment and comparator unchanged (two roles, H = 6, p ∈ {2, 6},
  τ ∈ {2, 4}, c ∈ {0, 1}, eight contexts at 1/8, R = (1/6) Σ 1[a_t = b_t]; FACTOR 188 and
  GENERIC 191 parameters, CPU FP32, Xavier gain 1, zero bias, embedding std 0.5).
- One fresh pair, seed 3, serial FACTOR then GENERIC, new model and Adam state each; existing
  seed formulas at seed 3 (NumPy `[3,101]`, `[3,102]`; torch 3201/3202 and 3301). Greedy
  deterministic evaluation, no training-stream consumption.
- 32 real episodes per cycle, one full-batch update; lr 0.01, Adam (0.9, 0.999, 1e-8, wd 0),
  clip 5; segment credit g = Σ r_t / 6 with stop-gradient bootstrap, terminal continuation 0,
  γ = 1; per-episode mean of renewal errors then mean over 32 episodes.
- Exploration: cycles j = 1…128 use ε_j = 1 − 0.9 (j − 1)/127; cycles 129…512 use ε = 0.1.
  No change of the 127 denominator, no optimizer reset, no exploration restart, no checkpoint
  selection at 128. The 128 point is read out inside the same continuous instance.
- 33 fixed evaluation states u = 0, 16, …, 512, eight free legal-policy episodes each (one per
  context), J_a(u) the eight-context mean. Quantities: ΔJ_512 (primary endpoint), AUC(0:512)
  with divisor 32, J_128 and AUC(0:128) with divisor 8, D = ΔJ_512 − ΔJ_128 with L_F and L_G,
  and the descriptive late-segment AUC(128:512) with divisor 24. All 33 points and all context
  strata retained; no best point; no merging of new 0:512 AUC with the old 0:128 values.
- MEI stays descriptive absolute 1/12; no winning line for D or the late AUC.
- Pro's working prediction: with more same-budget opportunity GENERIC may correct part of its
  short-period errors, so a seed-3 gap at 128 is more likely to shrink than reliably widen.
- Seven result branches (section 5 of the response), reproduced on the card.
- Exposure per arm: 16,384 training episodes, 98,304 joint native steps, 32,768 renewal
  samples, 512 Adam updates, 33 checkpoints, 264 evaluation episodes, 1,584 evaluation joint
  steps, 99,888 joint steps in total; two arms 199,776 joint steps and 1,024 updates. Nominal
  Σ lr = 5.12; displacements of θ0→θ128, θ0→θ512 and θ128→θ512 recorded; no displacement gate.
- Cost: 2,700 s complete-invocation cap per arm (imports through readback), 5,400 s cap sum is
  not an elapsed target; measured 128-update invocations were 1.76–3.95 s wall, the 7.04–15.8 s
  per-arm figure is a conditional linear scenario only. CPU FP32, one process and compute
  thread, batch 32, remote-first with a fresh ≥ 4 GiB admission per invocation. Stop at the cap
  or an actual failure; keep completed exposure; no seed swap or continuation.
- Engineering: ordinary research changes only (new B identity and seed 3, prefix schedule plus
  0.1 tail, extended loop and evaluation points, three AUC windows, parameter readouts, counts);
  reuse the host, model, update and publication paths; one focused check for the changes; no
  new scope-spec machinery; do not rewrite the old card, results or the old AUC divisor.
- Boundaries kept: old A01 gap missing, not zero; D6 stop boundary unchanged; no Portfolio
  change; no C promotion on "four seeds".

## 3. Check against current instructions and specifications

- Decision tier: direction (next object after a consumed extension), inside the node's
  authority; no Portfolio disposition requested or made. `PRO_FINAL`.
- Evidence spec §11: a B/EXPLORE with fair same-information comparison, prospective reading,
  all outcomes retained, no significance gate; conforms. §11.4 launch conditions apply to the
  CM, not to this intake.
- Engineering scope: new lines well under budget; no default-prohibited machinery; the
  runner's seed choices must be extended without touching the accepted seed-0/1/2 path.
- Runtime spec: 2,700 s per complete arm invocation, toy threshold 2,700 s; consistent.
- No conflict found; nothing returned to the node.

## 4. Decisions this intake produces

1. **Direction tier (PRO_FINAL applied):** open `VSPC1-K4-FACTOR-VALUE-B02-BUDGET512` as the
   next and only object of this family at this round. Recorded, not decided locally.
2. **Object tier, card wording:** freeze the card now with the CM stop condition "two complete
   arm invocations at seed 3 with the 33-point curves, three AUC windows and the parameter
   readouts published", versus freezing after a scout pass over `experiment.py`. Recommend and
   select freeze now: the source was read in this session (loop, checkpoints, counts, reporting
   divisor) and the change list is fully specified by the response. Owner-delegated decision
   (unattended, 2026-09-03 instruction): **freeze now**. `OWNER_DELEGATED`, selection, reversible.
3. **Object tier, implementation route:** Opus `hmasd-cm` versus Grok Build headless
   (`hmasd-grok-cm`). Select Grok Build: the owner routed one direction's CM code tasks to Grok
   to save Claude quota (2026-09-05 22:40 PDT), DISH has parked, and the change is a bounded
   extension of one package with the accepted 128-update path protected by tests; the hub
   reviews, runs the focused tests and commits by pathspec; `hmasd-reviewer` if the diff touches
   `experiment.py` semantics. `OWNER_DIRECT` (routing), technical.
4. **Predictions on record** (card §5): DM and Pro predictions written before any run; owner
   slot `not taken (unattended)`.

Ledger rows appended in `docs/research/portfolio/audit/2026-09-06.md`. Owner item: new-card
with packet.
