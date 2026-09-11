# DISH post-A01 Convergence intake (Claude hub, 2026-09-06)

Direction `degraded_incumbent_shadow_handover` (DISH, N3). Node
`em:degraded_incumbent_shadow_handover:convergence`, conversation
`6a9bec54-df00-83e8-9840-46440458f316`. Request `2026-09-06-dish-post-a01-convergence-01`,
packet `pro_packets/20260906_post_a01_convergence/` (evidence base
`04db4a5a74e69e0c76f5b9aa21eb1ba4aad5f111`, TASK at `e818631ee`). Intake by the hub as Root
and DM.

## 1. Transport facts (observation)

- One Send by the Sonnet transport (phase 1, click count 1, `sendAttempted` 2026-09-06
  10:36:45Z, labels `Latest` / `Pro`, prompt sha256 `19df0c70…`). The delivery landed through
  the ChatGPT GitHub connector on `codex/pro-dish-a01-convergence-20260906` at
  `ed4363a2e4c0b578eac64ca19da6ef5e27b64a17` (2026-09-06 10:50:18Z, one commit above base),
  response path present, 39,132 bytes, sha256
  `866736a28d6a95a7022220f7b567bc961e1b91dd7ae2c3c874ab32f3851b9e1a`; Issue 4 comment count
  1 → 2. Phase 2 (receipt, archive under `archive/`, registry confirmation, tab close) was
  executed by the same agent after this readback; its facts file sits beside the prompt.
- Lesson recorded in the transport skill: the hub's wait must watch the GitHub branch head,
  not the Agentify state file (the owner noticed the finished reply before the hub did).

## 2. The formed decision (read from the full response)

**CONTINUE, not RECAST:** one bounded A/RECON ordinary-renewal interface correction and native
acceptance observation. No retraining, no B02 scaling, no forecast-objective change, no
reopening of B02's rule. The corrected-window observation must finish before another learner
is purchased on this path.

Content the card `DISH_RENEWAL_BOUNDARY_A02_CORRECTION_SCIENCE_CARD_20260906.md` freezes:

- **Contract.** For an ordinary live decision at tick n the policy's scheduling permission is
  `renew_now(n) = [current native countdown of that lane is zero]`, the same pre-action state the
  next ordinary native step consumes. The raw native output flag keeps its meaning (renewal
  applied in the transition just completed) and stays available separately. A Python
  ordinary-decision boundary correction derives the operational flag from the matching current
  countdown per lane, without advancing the environment, covering the initial ordinary
  observation, subsequent ordinary-step observations and selected-lane resets (a phase-zero
  reset must expose current renewal). No native ABI change, no relabelling of the generic
  decoder that also serves prepared and cloned outputs; the changed meaning is limited to
  ordinary decision observations.
- **Consumers inside the correction.** The corrected pre-action permission is what the
  ordinary policy, its behaviour-log-probability and, when the collector is later used, its
  `renew`, `prepare_mask` and `commit_mask` fragment fields see. Loss and update algorithm
  unchanged. Native gates (preparation latch, intent emission, CAS) unchanged; no proposal,
  readiness, certificate, intent or transfer is forced; no threshold lowered.
- **Preservation** means the laws and information access (reward, tick indexing, terminal
  handling, energy, dynamics, host, clock recurrence, action projection, ownership law,
  certificates, source/readiness prerequisites, passive-label algorithm; checkpoint, forecast
  flag, parameters, representations, normalization, recurrent order; no extra sensing, forward,
  search or A03-style substitution). Not equality of realized trajectories: a later stochastic
  run may consume draws at different ticks. The current countdown is already actor feature 42,
  so no new information is granted.
- **Acceptance observation.** Same checkpoint (sha256 `504329d6…dc66`), same normalization,
  B02 master, A03 host; two sequential width-one instances with fresh zero recurrent states,
  TARGET_VISUAL_MASK/K8 and TARGET_VISUAL_MASK/K4_TO_K12, speed 4, slot 0, block 0, at most the
  first 32 ordinary ticks each; deterministic sampling, FP32 policy / float64 native, single
  thread. No rerun of the unmodified arm. Per tick retain the consumed flag, current pre-step
  countdown/tick, emitted raw vector, held vector before/after, proposal outputs, service,
  energy, events, terminal, and separately the raw completed-transition flag
  (`returned_renew` may denote the corrected permission after the change; both meanings kept
  distinct). Intended result: zero same-tick permission disagreements; at admission the held
  vector equals native's unchanged projection (raw magnitude ≤ 3, change ≤ 1.5, result ≤ 3 per
  vehicle) of that tick's emitted command from the previous held vector, checked by the
  independent reporting computation at float64 scale; away from admission the held vector is
  unchanged. Expected counts if both windows stay live: 12 matched renewals, 52 matched
  non-renewals, 0 disagreements. Equal-to-held choices remain legitimate; no forced command,
  other checkpoint, longer window or epsilon rule.
- **Verification.** One consolidated focused regression invocation covering the changed clock
  boundary and its measurement (two initial periods, phase-zero/reset handling, consistent
  pre-action flag propagation to the collector's fragment fields); retain the existing B02
  focused coverage; no second smoke; small fixed synthetic fixtures are engineering checks.
- **Reading rule** (five rows, reproduced on the card): accept the local correction; permission
  aligns but commands equal held; disagreement/incorporation mismatch/protected semantic changed
  → not accepted, return the defect; adverse or truncated behaviour preserved, no manufactured
  counts; input or measurement missing → report the gap. Neither positive service nor legal
  transfer is an acceptance condition.
- **Later reinterpretation intake** (after acceptance): B02 keeps 572/447/433/428 in each arm
  and its inside-MEI reading, qualified as outcomes of the executed interface; the training-side
  concern is source-supported inference; B01, A03–A05 not invalidated; no blanket quarantine, no
  "timing explains the null". No training-collection measurement is required first.
- **Cost.** New 120 s complete compute limit (imports, native build/load, the consolidated
  focused invocation, checkpoint handling, both windows, reduction, publication); work law
  `build/import/load + one focused regression + checkpoint + 2 × (policy + reset) + ≤ 64 ×
  (forward + native step) + publication`; not carried-over A01, A05 or B02 balance; ordinary
  2,000/600-line limits; remote-first, fresh ≥ 4 GiB admission per invocation, single thread.

## 3. Check against current instructions and specifications

Direction tier, inside the node's authority; conforms to evidence spec §11.4/§11.8 (a bounded
A with prospective reading and no gate beyond the four conditions) and the scope spec (a small
boundary change, no registry, no compatibility framework, no new native export). The
correction touches the shared `rbhr_r06` wrapper and recurrent trainer: under `AGENTS.md`
Appendix C the diff therefore goes to `hmasd-reviewer` as well as the hub. No conflict found;
nothing returned to the node. `PRO_FINAL`.

## 4. Decisions this intake produces

1. **Direction tier (PRO_FINAL applied):** open `DISH-RENEWAL-BOUNDARY-A02-CORRECTION` as the
   next and only DISH object; DISH re-enters the working set for it.
2. **Object tier, card wording:** freeze now from the response and the source lines already
   read (wrapper `step`/`rollout` copy `raw["renew"]`; `observe`/`reset_selected` at
   `production_backend.py:548/552`; `step_rows` reads `observation["renew"]` at
   `production_recurrent_trainer.py:311`; fragments at 506–508), versus scouting first.
   Recommend and select freeze now. Owner-delegated decision (unattended, 2026-09-03
   instruction): **freeze now**. `OWNER_DELEGATED`, selection, reversible.
3. **Object tier, implementation route:** Grok Build implements in a fenced worktree with
   `experiment`-level paths opened for the wrapper and trainer boundary, and `hmasd-reviewer`
   (Opus) reviews the diff before the hub commits (protected surface, Appendix C); versus Opus
   `hmasd-cm` end to end. Select Grok plus reviewer (owner quota instruction 2026-09-05 22:40
   and 2026-09-06 06:48 PDT). `OWNER_DIRECT` (routing), technical.
4. **Predictions on record** (card §5): DM predicts the first row (12/52/0 with incorporated
   nonzero commands on every K8 and K4 admission after the first, since A01 showed nonzero fresh
   commands on the following ticks); Pro states the expected counts, not an outcome. Owner slot
   `not taken (unattended)`.

Ledger rows appended in `docs/research/portfolio/audit/2026-09-06.md`. Owner item: new-card
with packet.
