# Prompt handed to GPT Pro to converge ADR 02 (relay corridor host)

Owner-facing note: ADR 02 revision 2 is on hold because the host mechanics do not exist yet. Round-2
decision 5 lets GPT Pro draft the mechanics page; the owner finalises it. Paste the block below into
a GPT Pro conversation with the GitHub connector on `CartmanFatass/My-paper-code`. Save the reply as
`docs/Claude_docs/plans/RELAY_CORRIDOR_MECHANICS_20260902.md` (the mechanics page) and overwrite
`docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md` with revision 3, then hand both to Claude
for review (Part IV).

Repository facts: `https://github.com/CartmanFatass/My-paper-code`, branch `main`, commit
`dd1e17b5a` or later.

---

```text
You are converging ADR 02 (relay corridor host family) for a research repository you can read
through the GitHub connector: CartmanFatass/My-paper-code, branch main, commit dd1e17b5a or later.
Two outputs in one reply: (1) a one-page mechanics definition the ADR was missing, and (2) ADR 02
revision 3 with that definition folded in. Read before writing; cite file paths and document
sections. Do not write code, do not run anything, do not reopen decisions listed as taken.

READ IN THIS ORDER
1. docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md — Part I section 2 (F2.1 to
   F2.9), section 4.1 (decisions 5 and 6), Part II sections II.6 to II.10 and II.10.1 (decisions
   2 and 3). These are fixed: agent-pinned lambda regions; deterministic / exponential / lognormal
   renewal laws matched on E[D] only; two margins m and m_dur registered; the ten-segment rule
   binds only the fixed-k D0 sweep; the structure-blind control is the same learner with
   c = c_Z = infinity.
2. docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md — revision 2, the contract you are
   completing.
3. docs/Claude_docs/plans/ADR_01_D2_POLICY_INTERRUPTION.md — revision 3, accepted; the learner
   that will run on the host (k_max, k_Z, c, c_Z, per-agent segments).
4. docs/Claude_docs/environment_design/TOY_HOST_AND_UAV_ENV_DESIGN_ADVICE_20260901.md — sections
   3 (P1-P8) and 4.
5. docs/Claude_docs/plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md — sections 4 (renewal-process
   toy and moving-goal grid, the inspiration models), 5 (E2-E4), 6, 11.
6. docs/Claude_docs/research_notes/UNTIED_K_N_TRADEOFF_LEDGER_20260901.md — section 1 (K-1 to
   K-7), section 9.2 (interruption rule, regret about delta/2 + c x switches) and 9.3 (unpatterned
   durations, the four conditions), and the toy tables in
   docs/Claude_docs/toy_studies/untied_k_n/RESULTS.md (commitment fraction C(k, lambda)).
7. docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md section 11, and CLAUDE.md at the root for
   test naming, the scratch directory, and the two conda interpreters.

OUTPUT 1 — MECHANICS PAGE (at most one page, about 600 words), headings exactly:
  State / Entities / Action / Latent / Hazard / Reward / Probe / Structure cut / Reference
  policies and margins / Enumeration recipe / Proposed grids / Speed note

Constraints the mechanics must satisfy (each one is a test later):
- Toy scale: the latent per region is a small discrete variable; the per-step reward is in [0, 1]
  before named costs; the horizon H, agent count N, roles K, zones Z are parameters, not fixed.
- Agents are pinned to one of two regions per episode; each region has its own hazard rate
  lambda_r: per step, with probability lambda_r the region's latent switches (E3 uses
  lambda_1 != lambda_2; the homogeneous point has equality).
- E4 replaces the geometric hazard with a renewal process: the latent holds for a duration D drawn
  from the selected law (deterministic, exponential, lognormal), all three matched on E[D]; state
  which law has which variance at the matched mean.
- The oracle that knows the latent and may switch at any step, the oracle that knows the latent but
  may re-decide only every k steps (for each k in the D0 sweep), and the best open-loop or fixed
  plan must all be computable by enumeration or a small dynamic programme on the latent chain, not
  by training. Give the recipe: what is enumerated, its size at the proposed grid, and why it is
  exact.
- Define both margins: m = J*(oracle plan) - J*(best open-loop or fixed plan), and
  m_dur = J*(switching oracle) - max_k J*(k-restricted oracle). Give m_dur as a formula in
  lambda_1, lambda_2, k, and the reward contrast, labelled "inference", and show it agrees with the
  commitment fraction C(k, lambda) in the toy tables where they overlap.
- Ragged entity sets at the host boundary; one random stream per entity keyed by (master seed,
  episode, entity id); one per region for the hazard or renewal process keyed by (master seed,
  episode, region id); no N mod K constraint.
- The structure cut for this direction is the same learner at c = c_Z = infinity (D0). Say what a
  fixed-k D0 loses on this host in one sentence, and what the greedy-on-public-state heuristic sees.
- The probe (c_probe, v) exists in the family but is fixed off (c_probe = 0, no probe action) for
  E2-E4; state how it would be switched on later without changing the state layout.
- Speed: what the vectorised NumPy step does per env so that 1e4 steps/s/core is plausible; no
  measured number, no native code.
- "Proposed grids" are proposals, labelled as such: three margins (small, medium, large) with the
  lambda pairs and reward contrast that realise them, one renewal mean, the D0 k sweep, H at least
  ten times the largest k in that sweep.

OUTPUT 2 — ADR 02 REVISION 3, same headings as revision 2 (Title / Status: proposed / Context /
Decision / Parameters / Invariants / Tests-as-specs / Metrics to log / Resolution arithmetic /
Consequences and risks / Out of scope / Open questions), at most one page, with:
- Decision now containing the mechanics in words and small formulas (summarised from Output 1,
  which the ADR cites by file name).
- Both margins registered; invariant 5 restated as: for each registered margin, enumeration gives
  m and m_dur to the stated values, m_dur is at least three times the declared resolution term.
- The ten-segment rule scoped to the fixed-k D0 sweep (H >= 10 x largest fixed k); the D2 k_max
  sweep exempt, with M rows per rollout reported (ADR 01 revision 3, resolution arithmetic).
- Renewal laws matched on E[D] only; Var(D) reported. The deterministic law's oracle is fixed
  k = D; say so.
- time_homogeneous: define its effect or remove it from this ADR.
- One test per invariant in tests/relay_corridor_host_test.py (top-level *_test.py naming, host
  under envs/), each with inputs and the assertion, run with the explicit interpreter and
  --basetemp C:/Projects/HMASD/temp/pytest_relay_corridor.
- Resolution arithmetic: do not repeat ADR 01's numbers; state that the corridor learner's M,
  parameter count, and displacement are exposure-line measurements, and give sigma / sqrt(episodes)
  for the evaluation budget you propose (label the budget as a proposal).

RULES
- Every claim from a document carries its section; every code claim a file path and line or symbol.
  Label inference as "inference" and proposals as "proposal".
- Do not invent measured numbers. Design choices (grids, contrasts, means) are allowed only under
  "Proposed grids" and must be internally consistent with the enumeration recipe.
- Do not add learned termination, a (z, k) menu, variable agent count within an object, or a
  C-class contract. Do not change ADR 01.
- End with a "could not verify" list.
```
