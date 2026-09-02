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
- `CODEX_SCIENCE_WORKFLOW_REVIEW_20260901.md` — the Codex workflow (`AGENTS.md`,
  `.codex/agents`, skills, gates, portfolio) read as a research process: measured output, seven
  failure modes F1–F7, nine recommendations R1–R9, and a 2026-09-02 addendum mapping them onto the
  owner's calibration. R4 (telemetry as a recorded field) is left open for the owner.
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
  used. The result document is written by the executing session when the runs finish.

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
