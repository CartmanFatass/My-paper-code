# Claude_docs

Deliverables written by Claude Code (Fable 5.1) for the repository owner, kept outside the
research authority tree on purpose: nothing here is a science card, contract, or decision record.
Everything is evidence for the owner to evaluate. Dates in file names are the date the document
was closed; several carry a later dated addendum inside.

Provenance for all of them: Claude Code session `session_015hGLzLCuJLFFtZTboKg2bd`,
2026-09-01 to 2026-09-02, repository HEAD `71b2bba2b` at the time of review, 96 dirty paths in
the working tree. Sub-agents used: Sonnet scouts (local and web literature, repository tie points,
workflow inventory, environment inventory), an Opus numeric toy study, and a Fable red-team pass
whose corrections are incorporated. No experiment was run and no scientific object was consumed.

## Layout

| Directory | Contents |
| --- | --- |
| `reviews/` | Independent assessments of existing work: the five first-wave directions, and the Codex science workflow. |
| `research_notes/` | Scientific synthesis on a question the owner asked, with labelled literature and toy numbers. |
| `environment_design/` | Design advice for toy hosts and the UAV environment. |
| `toy_studies/` | Small self-contained numeric studies (numpy, fixed seeds) that back a research note. |
| `plans/` | Follow-up plans written for alignment with the owner: concern registers, candidate schemes, experiment ladders, and the decisions still open. |
| `artifacts/` | Rendered, published forms of the above and the script that builds them. |
| `experiments/` | B-class experiment designs and result documents for the duration direction (E0 onward). |

## Documents

### reviews/

- `FIRST_WAVE_INDEPENDENT_REVIEW_20260901.md` — independent review of the five `ACTIVE/HIGH`
  first-wave directions (FRRIE, VNFC, CBSC, SCDMP, UCOPE) against the packet in
  `docs/research/review_packets/2026-09-01-first-wave-latest-model/`. Dispositions: SCDMP, CBSC,
  FRRIE `CONTINUE`; UCOPE, VNFC `RECAST`. The 2026-09-02 addendum records the owner's calibration
  and what it removes from each direction's next object.
- `FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` — compliance note: the five first-wave
  directions audited against evidence spec §11.4/§11.6 after the calibration. Every
  pre-launch condition quoted with `file:line` and classed ALLOWED / DEMOTED / UNCLEAR; none of
  the five acknowledges §11 and each is held by a gate §11.4 does not permit (four in code). Part
  A gives the reviewer's reading, the concrete recast per direction, and the owner's decisions.
- `CODEX_SCIENCE_WORKFLOW_REVIEW_20260901.md` — the Codex workflow (`AGENTS.md`,
  `.codex/agents`, skills, gates, portfolio) read as a research process: measured output, seven
  failure modes F1–F7, nine recommendations R1–R9, and a 2026-09-02 addendum mapping them onto the
  owner's calibration. R4 (telemetry as a recorded field) is left open for the owner.
- `CODEX_CONTROL_PLANE_REVIEW_20260903.md` — the Codex control plane (`AGENTS.md`, sixteen
  `.codex/agents` TOMLs, the HMASD skills, the empty authority surfaces, the uncommitted 09-03
  edits) reviewed against evidence spec §11 and the 2026-09-02/03 practice. Measured: zero Pro
  rounds and seventeen result documents since the calibration under an owner-and-reviewer loop
  the authority files do not describe. Twelve stale clauses S1–S12 with fixes, written versus
  practiced topology, nine recommendations T1–T9 (decision ladder, runtime-neutral `AGENTS.md`,
  two recorded lines in place of the performance gate, capacity as numbers, a git model for
  concurrent sessions, diagnosis by reproduction, roster 16 → 8, housekeeping, codified
  unattended mode), and eight owner decisions.
- `CODEBASE_INVENTORY_20260903.md` — facts-only inventory of the whole checkout (Sonnet agent,
  three forks): top level, code modules, scripts, tests, agent configuration, worktrees and
  branches, scratch, documentation tree and map-document staleness, `.gitignore` structure, sizes;
  every count names its command. Basis for the layout standard.
- `ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` — adversarial review of the two GPT Pro ADR drafts:
  citation audit, ranked findings (both `REVISE`), the six decisions only the owner can take, and
  three predict-then-verify prompts. Headline: the interruption statistic is not computable by the
  causal decoder as written, the forced boundary decides whether E3 can succeed, and the exposure
  arithmetic is off by about 200×. Part II reviews revision 2: ADR 01 accepted with two additions
  (separate team cap, per-agent segment storage); ADR 02 held for the owner's mechanics page and
  needs a duration margin registered next to the latent margin. Part III accepts ADR 01 revision 3
  with five non-blocking implementer notes and a hand-off to Codex. Part IV reviews the corridor
  mechanics page and ADR 02 revision 3 (adapter, `K = 2` latent publicity, inert `Z`, cue, initial
  dwell) and records three owner decisions; Part V accepts the finalised mechanics page and ADR 02
  revision 4 after checking that no formula, grid, or margin changed. Part VI accepts the relay
  corridor host implementation against the nine invariants (reviewer re-ran the nine tests) with
  one convention for the owner to confirm (cue at reset) and integrates the branch into `main`.
  Part VII accepts the D2 implementation (Phases 3 to 8) against ADR 01's eight invariants
  (reviewer re-ran the ten tests), records eight findings with one owner decision (rollout
  boundary guard), and three reviewer errata to the implementation plan.
  Part VIII accepts the D2 follow-up guards and the corridor integration (26 tests re-run) and
  closes the low-level-actor item: the base route emits a continuous K-vector.
  Part IX takes E0 in as B-class integrity and exposure evidence and launches seed 2.

### research_notes/

- `UNTIED_K_N_TRADEOFF_LEDGER_20260901.md` — the trade-off ledger for untying the skill duration
  k (K-1 to K-7) and the agent count N (N-1 to N-7) in HMASD-style hierarchical MARL, with the
  repository's tie points, toy numbers, literature labelled DIRECT / PARAPHRASE / CURATOR /
  REVIEWER_INFERENCE / UNKNOWN, and three predict-then-verify prompts. The 2026-09-02 addendum
  fixes the two untyings as separate directions and states the theory ceiling (a suboptimality
  bound for the implemented scheme) and the per-direction inspiration-model ladder. Section 9
  (later on 2026-09-02) records the non-stationarity / semantic-drift / credit chain, the
  action-space cost of a duration menu and the interruption rule that replaces it, unpatterned
  event durations, and asynchronous switching against the autoregressive coordinator.

### plans/

- `OWNER_CONSOLE_DESIGN_20260904.md` — design and build record of the owner console
  (`tools/owner_console/`): Codex writes one JSON item per thing needing the owner's eye, the
  local page renders them as grading cards (options with ★ recommended and ✓ executed, free
  comment), replies regenerate `owner/reviews/<date>.md` for Codex and are committed by pathspec;
  the item and review schemas, the four decisions taken with the owner, what was built and what
  is deferred.
- `OWNER_INTERVENTION_WORKFLOW_PLAN_20260904.md` — the plan behind the owner-intervention decision
  of 2026-09-04: intervene in selection pressure and output format, never in execution; the
  owner's four answers (Chinese brief per valid result, soft veto for new cards, no prediction
  wait, MEI 5%/25% and recast budget one, no hard stops added); every file changed and why; how a
  decision flows through ledger, digest, prediction queue and briefs; the owner's rhythm; what
  Codex does first; what is still open.
- `MARL_EXPLORATION_GUIDANCE_20260904.md` — alignment draft for the owner and Codex Root on how to
  explore MARL algorithms after the 2026-09-04 portfolio snapshot: the observed outcome pattern
  (`NEITHER`, comparator weak, generic wins, narrow positives), a three-part diagnosis, five
  principles (headroom before mechanism with a minimum effect of interest, comparator as a
  first-class object, invest only where a MARL structure binds, fewer directions on the production
  host, three readings written before the run), six actions with tiers, a proposed ACTIVE/PARK
  disposition for all 22 directions, and the [DECIDE]/[ASK] items.
- `RESEARCH_STATUS_AND_ADVICE_20260904.md` — read-only status check at the owner-directed pause
  (`origin/main` `e4c0c93c7`, 2026-09-05T02:00Z): loop state and zero live compute verified on
  both nodes, the day's throughput counts, the nine routes' latest results and boundaries, the
  assessment (every learner comparison inside its MEI from one-seed objects; three of six invested
  entries held by the 30% orchestration rule; VNFC census 129× over its cap; 208 inbox items with
  2 answered; serial CPU-only compute), and ten advice items with [DECIDE]/[ASK] markers plus a
  proposed resume order (finish E3 concurrently, amend the rule, park or recast VNFC, no more
  one-seed rungs, E2b on the UAV host next).
- `CODEBASE_LAYOUT_STANDARD_20260903.md` — alignment draft for the directory standard: nine
  principles-to-application sections (target layout, candidate directories, tests, scripts,
  scratch/worktrees/branches/git hygiene, `.gitignore` rewrite, layered `AGENTS.md` with one-line
  `CLAUDE.md` imports), with [DECIDE]/[ASK] markers and the order of application.
- `FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` — alignment draft for the duration direction: the
  claim in two parts, a ten-item concern register (C1–C10) with mitigations and measurables, the
  scheme ladder D0–D8 with the policy-based interruption rule as the proposed first B object,
  inspiration models, the B-class experiment ladder E0–E6, hosts, the theory ceiling, repository
  touch points, and the decisions marked [DECIDE] / [ASK] that the owner has to make. Section 11
  records the decisions taken with the owner on 2026-09-02.
- `ADR_REQUEST_PROMPT_GPT_PRO_20260902.md` — the prompt and repository facts handed to GPT Pro
  (GitHub connector) to draft the two ADRs below.
- `ADR_01_D2_POLICY_INTERRUPTION.md` — GPT Pro's ADR for the D2 policy-based interruption rule
  on the HMASD base route, revision 3 stored verbatim (revision 1 at commit `ea20bccb0`, revision
  2 at `7591f23a1`); accepted for implementation by the review's Part III; Codex implements.
- `D2_IMPLEMENTATION_PLAN_20260902.md` — phase-ordered implementation plan for ADR 01 revision 3
  handed to the implementer: ground rules, file and function touch points per phase, the nine
  tests, the report format, and the reviewer's acceptance checklist. Section 11.1 carries the
  reviewer's errata recorded after implementation.
- `D2_EXECUTION_HANDOFF_20260902.md` — the Codex implementer's handoff after Phases 0 to 2:
  state, Phase 3 design notes, plan-versus-code discrepancies, operating notes.
- `D2_IMPLEMENTATION_REPORT_20260902.md` — the implementer's report for Phases 3 to 8: status
  and commits, the fingerprint, test output, smoke-rollout numbers (P1, P2, the inference
  ratio), the discrepancy list, new `d2` behaviour and the design points the plan did not fix,
  the acceptance checklist as observed, and what could not be verified.
- `RELAY_CORRIDOR_HOST_REPORT_20260902.md` section 7 — the integration of the HMASD stack on the
  corridor (`envs/relay_corridor/hmasd_driver.py`): what the driver does, the five readings it
  fixed, the actor-head answer, verbatim test results, could-not-verify.
- `RESEARCH_ADVANCEMENT_PLAN_20260902.md` — the sequence after E0: refactor R0/R1, E1, E2 on the
  homogeneous corridor then E2b on scenario 1, E3, E4, the C-BENCH gate, E5/E6, UAV transfer; what
  each step needs from the owner (a prediction, the post-intake decisions), the launch and budget
  policy, budget estimates, stop conditions, and the four decisions confirmed on 2026-09-02.
- `ENV_THROUGHPUT_REFACTOR_PLAN_20260902.md` — engineering plan to speed up the scenario-1 loop:
  cProfile shares (environment 81%, update 12%, inference 2%), phases P0 to P4 (reference tape
  and equivalence harness, vectorised channel model, observations from matrices, fingerprint
  re-freeze and re-timing, update phase), expected effect, integrity policy, two owner decisions.
- `ENV_THROUGHPUT_REFACTOR_REPORT_20260902.md` — P0–P3 report: harness bit-identical across the
  five channel models, per-step 24.6 ms → 0.47 ms, E0 collection 240 s → 18 s per rollout at 32
  lanes, fingerprint unchanged (re-freeze unspent), six plan-versus-code discrepancies, could-not-
  verify. Accepted in the ADR review's Part X. P4 addendum (2026-09-03): the update is 87%
  of the rollout and autograd-bound; four candidates measured, none taken (the segmented RNN
  backend gives −12.6% but is not equivalent at 1e-9); fingerprint unchanged. Review Part XII.
- `ADR_02_CONVERGENCE_PROMPT_GPT_PRO_20260902.md` — prompt for GPT Pro to draft the corridor
  mechanics page and re-issue ADR 02 as revision 3 with both margins registered.
- `RELAY_CORRIDOR_MECHANICS_20260902.md` — the corridor mechanics (state, entities, action,
  latent, hazard, reward, probe, cut, references and margins, enumeration recipe, proposed grids),
  drafted by GPT Pro and finalised at commit `5c4a32f77` after the review's Part IV; normative
  companion of ADR 02.
- `ADR_02_RELAY_CORRIDOR_HOST.md` — GPT Pro's ADR for the relay-corridor host family (E2–E4),
  revision 4 (revisions 1 to 3 at `ea20bccb0`, `7591f23a1`, `33f009211`); accepted by the
  review's Part V; implemented under `envs/relay_corridor/` with `tests/relay_corridor_host_test.py`.
- `RELAY_CORRIDOR_HOST_REPORT_20260902.md` — the implementer's report for the corridor host:
  what was built and where, how each invariant is met, enumeration results next to the table
  values, throughput and machine identity, twelve reading choices, and what could not be
  verified (no learner ran; the adapter is not yet wired into the base route).

### environment_design/

- `TOY_HOST_AND_UAV_ENV_DESIGN_ADVICE_20260901.md` — inventory of the five first-wave hosts and
  the UAV family, diagnosis D1–D6, host principles P1–P8, the proposed relay-corridor parametric
  family, UAV recommendations U1–U7, and an invitation for the owner to write the one-page ADR.
  The 2026-09-02 addendum places the bandit and single-agent bridge below the toy hosts.

### toy_studies/untied_k_n/

- `untied_toys.py` — numpy study (fixed seeds, about 0.4 s): commitment fraction C(k, λ),
  window identifiability, k-step model composition versus direct prediction, role coverage
  probability, single-loss coverage gap, joint-assignment versus composition counts.
- `RESULTS.md` — the tables the research note quotes, with the study's stated limits.

### experiments/

- `E0_EXPOSURE_PROBE_SET_20260902.md` — launch contract for E0 on scenario 1: question and
  claim ceiling (B, integrity and exposure only), the two arms (`off`, D0), measurements, budget
  and stop rule, the frozen probe set recipe for C1/C2, outputs, and why `hmasd_run.py` is not
  used.
- `E0_EXPOSURE_PROBE_SET_RESULT_20260902.md` — the E0 result: timing run, the 16-lane deviation,
  both arms complete (80,000 transitions, nonzero optimizer and evaluation counts, monotone exposure
  lines in every network), the three first-rollout integrity checks (zero mismatches; target-scale
  ratio 1.04589 against 1.04583), the frozen 1,536-probe set with its content digest, deviations
  D1 to D4, and what could not be verified; section 12 adds seed 2 for both arms (same counts,
  checks pass, evaluation ordering reverses between seeds). Accepted by the review's Part IX.
- `E1_AGE_INPUT_20260902.md` — launch contract for E1 (D0 versus D1 at fixed k = 10 on scenario 1):
  the prediction on record, arms, the probe measurements (adjacent-checkpoint label agreement,
  probe accuracy split by age bucket, value-target drift, age-weight share), three seeds, R = 20,
  the reading rule written before the data. Launches after the throughput refactor P3.
- `E1_AGE_INPUT_RESULT_20260902.md` — E1 result: six runs (D0/D1 × seeds 1–3, 32 lanes, R = 20),
  the §5 rule applied verbatim (prediction on record unrefuted, supported on three of four
  applications), age-feature weight share at the equal-column baseline, eleven deviations,
  could-not-verify. Accepted in the ADR review's Part XI.
- `E2_INTERRUPTION_COST_SWEEP_20260903.md` — E2 contract: D2 at `c ∈ {0.25, 0.5, 1, 2}` (cap 40)
  against the D0 `k` sweep `{1, 2, 5, 20, 40}` on the homogeneous corridor (λ = 0.02 both regions),
  two seeds, 4,096 matched evaluation episodes against the exact references, event-alignment and
  segment-length measurements, the two mechanisms and the reading rule written before the data.
  Launches after P4 with the owner's prediction on record.
- `E0_probe_set_sample_seed1.json` — the first 32 probes of the frozen set, for checking the recipe.

### artifacts/

- `clocks_and_rosters_20260902.html` — the published page that bundles the research note, the
  workflow review, and the environment advice with a schematic and part navigation. Live copy:
  <https://claude.ai/code/artifact/10bdcf8f-32f2-44b6-a9f3-8050e5547304>.
- `build_clocks_and_rosters_page.py` — rebuilds the HTML from the three markdown sources in this
  tree (`python docs/Claude_docs/artifacts/build_clocks_and_rosters_page.py`); it performs a
  structural HTML check and writes next to itself.

## Related change outside this tree

The owner's 2026-09-02 calibration (inspiration model → B-EXPLORE → C-BENCH; no invariance
proofs, at most a suboptimality bound; suboptimal schemes are legitimate; only integrity, nonzero
learner counts, resource admission, and one exposure line may hold a B launch; duration and roster
untying are separate directions) is normative in
`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11, commit `a615cbd9b`.

## Git

`.gitignore` re-includes `docs/Claude_docs/**` so files here are visible to Git; the repository's
default `*.md` rule would otherwise hide them.
