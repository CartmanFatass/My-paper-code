# Prompt handed to GPT Pro (GitHub connector) to draft the two ADRs

Owner-facing note: paste the block below into a GPT Pro conversation that has the GitHub connector
attached to `CartmanFatass/My-paper-code`. Save the reply as
`docs/Claude_docs/plans/ADR_01_D2_POLICY_INTERRUPTION.md` and
`docs/Claude_docs/plans/ADR_02_RELAY_CORRIDOR_HOST.md`, then hand both to Claude for adversarial
review before Codex implements anything.

Repository facts for the connector:

- Repository: `https://github.com/CartmanFatass/My-paper-code` (local clone `C:\Projects\HMASD`)
- Branch: `main`; the plan and decisions are at commit `871cac235` or later
- Source PDFs, corpus chunk files, and `temp/` are intentionally not in the repository

---

```text
You are drafting two one-page architecture decision records (ADRs) for a research repository you
can read through the GitHub connector: CartmanFatass/My-paper-code, branch main, commit 871cac235
or later. Read before writing; cite file paths (and line numbers where you quote code). Do not
write code, do not propose experiments beyond what the plan already fixes, and do not reopen the
decisions listed as taken.

READ IN THIS ORDER
1. docs/Claude_docs/plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md — all sections; section 11 holds
   the decisions already taken (D2 policy-based interruption; two-level interruption for the team
   code Z; check interval delta = 1; HMASD base route first; UAV scenario 1 for E1/E2 and the relay
   corridor for E3/E4; Codex implements). Treat these as fixed.
2. docs/Claude_docs/research_notes/UNTIED_K_N_TRADEOFF_LEDGER_20260901.md — sections 0, 1 (K-1 to
   K-7), 8 and 9. Section 9.4 describes the four changes asynchronous switching needs against the
   autoregressive coordinator.
3. docs/Claude_docs/environment_design/TOY_HOST_AND_UAV_ENV_DESIGN_ADVICE_20260901.md — sections 3
   (principles P1-P8), 4 (the relay corridor family), 6 and 7.
4. docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md — section 11 (owner calibration: B-EXPLORE
   first, no invariance proofs, suboptimal schemes are legitimate, what may gate a B launch).
5. Code you must open and cite, HMASD base route: hmasd/agent.py around lines 1897 (skill
   reassignment trigger), 1921-1929 (joint autoregressive sampling of Z and z_i), 2010-2031
   (keep/edit masks of the horizon-window path), 2797 (elapsed-step storage), 3026 (undiscounted
   within-segment reward sum), 1094-1102 and 3441-3452 (per-state discriminators and intrinsic
   reward); hmasd/networks.py 727-729 (per-agent value heads); hmasd/utils.py 741 (gamma^elapsed
   bootstrapping); config_1.py 134 and 239-259 (skill interval k = 10; horizon-window options);
   ha_ctse_process/variable_roster_event.py (smdp_gae, ragged segments) for reference only.
   Line numbers may have drifted; search for the construct if a number is off, and say so.
6. envs/ — only enough to state what scenario 1 exposes (agent count, observation layout, reward),
   and CLAUDE.md at the repository root for test-naming and scratch-directory rules.

WHAT TO PRODUCE
Two markdown ADRs, each at most one page (about 500-650 words), in one reply, followed by a short
"could not verify" list. Use exactly these headings in each ADR:

  Title / Status: proposed / Context (at most five sentences, cite the plan and ledger sections) /
  Decision (the mechanism, precisely, in words and small formulas) / Parameters (name, type,
  default, sweep range) / Invariants (numbered, each a falsifiable statement) / Tests-as-specs
  (one test per invariant: file path following CLAUDE.md naming, inputs, the assertion) /
  Metrics to log / Resolution arithmetic (what the learner can resolve at the planned budget) /
  Consequences and risks / Out of scope / Open questions (at most three)

ADR 01 - D2 policy-based interruption on the HMASD base route
- Decision must specify: the per-step interruption test for agent i (conditional distribution of
  the coordinator given the other agents' currently held skills forced as tokens; switch when the
  log-probability of the held skill trails the best skill by more than c); the subset S re-decided
  at a step and the "kept agents first, S in canonical order" convention; the two-level rule for Z
  on the global state with its own cost c_Z; per-agent segments with their own tau_i, SMDP
  discounting by gamma^tau_i, log-probabilities summed over sampled agents only; within-segment
  discounting; the discriminator age input; and a compatibility switch under which the code path
  reproduces current fixed-k HMASD behaviour exactly.
- Invariants must include at least: (i) with interruption disabled the rollout is identical to the
  current route on the same seed; (ii) with c -> infinity no agent switches before its forced
  boundary; (iii) with c = 0 and delta = 1 every agent re-selects every step; (iv) the sum of
  per-agent segment lengths equals the episode length for every agent; (v) log-probability of a
  step's high-level action is the sum over S only.
- Resolution arithmetic: parameter count, initialisation scale, optimiser, learning rate, planned
  updates, and the displacement budget lr x steps against initialisation scale, read from the
  actual HMASD configuration files; state what return difference the evaluation budget can
  resolve (sigma / sqrt(episodes)).

ADR 02 - Relay corridor host family
- Parameters exactly as the environment advice lists them: N, K, Z, H, k, hazard lambda, churn rate
  rho, probe cost c and information value v, margin m, time-homogeneity flag; plus the two features
  the plan needs: two lambda regions along the corridor (E3) and a renewal event process whose
  durations D follow deterministic, exponential, or heavy-tailed laws (E4).
- Invariants must include: ragged entity sets at the host boundary (no padding); one random stream
  per entity keyed by (master seed, episode, entity id); no divisibility constraint on N; at least
  ten segments at the largest k; three reference policies (oracle with the latent, greedy on public
  state, structure-blind control) with their expected returns at three margins; a speed budget of
  about 1e4 environment steps per second per core in vectorised numpy before any native code.
- State where the five first-wave directions sit as parameter points, as the advice does, but only
  as a note; the ADR's scope is E2-E4 of the duration plan.

RULES
- Every code claim carries a file path and line or symbol. Every claim taken from a document
  carries its section. Label anything you infer as "inference".
- No results, no numbers you did not read in the repository. If a fact is missing, put it in the
  "could not verify" list rather than guessing.
- Do not add learned termination, a (z, k) menu, variable agent count, or any C-class contract;
  those are out of scope by decision.
- Plain markdown, no tables wider than five columns, no images.
```
