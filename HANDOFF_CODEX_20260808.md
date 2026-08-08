# Handoff — Claude takeover branch → merge to aggressive, Codex resumes

```text
date=2026-08-08
branch=claude/hmasd-full-takeover-20260805 (tip 2848500a, pushed, remote verified)
base=dd1a9bb4 (takeover base, 2026-08-05)
span=40 commits, 91 files changed, +30,863 / −35 vs base
working_tree=clean (everything described here is committed)
authority=AGENTS.md unchanged; External Pro holds ALL scientific authority
merge_decision=user's own (this document is inventory + state, not a merge plan)
```

## 0. Read-this-first merge facts

1. **The Codex boundary is intact.** `git diff dd1a9bb4 -- AGENTS.md .agents/
   .codex/ docs/project/ scripts/hmasd_workspace_ticket.py
   scripts/hmasd_workspace_boundary_guard.py` is EMPTY. Nothing in the
   protected surface moved; a merge cannot conflict there.
2. **Almost everything is NEW files.** The only pre-existing production code
   modified in the whole branch:
   - `ha_ctse_process/variable_roster_event.py` (+178/−~1),
     `variable_roster_event_models.py` (+65), `variable_roster_event_types.py`
     (+53) — commits `aa4dfcb9` (opt-in S03 direct-kernel witness hooks,
     inert unless explicitly enabled), `1ec21052` (FOLR seven-component
     object graph), `75174d98` (MSSR support-native P interface). All
     additive/opt-in; default behavior covered by regression tests.
   - `experiments/candidates/vsp_05/semantic_veto_census.py` (±10, Pro-
     directed correction to survival-weighted executed actions, `ebf1ee15`).
   - `.gitignore` (±14) and `CLAUDE.md` (±120) — config only.
   Everything else lives in new files under `experiments/candidates/`,
   `tests/`, `.claude/`, `scripts/`, `envs/` untouched.
3. **`local_research/` is gitignored and does NOT travel with the merge.**
   It holds every Pro review archive (verbatim responses + SHA-256),
   portfolio build records, and `RESEARCH_CONTINUITY.md` (the longitudinal
   state). Durable copy: `C:/Users/fires/OneDrive/HMASD_local_research_backup/`
   (robocopy /MIR, refreshed 2026-08-08). Codex needs this directory (or the
   backup) to resume any science thread.
4. **`.gitignore` has a bare `*.md` rule** — new markdown (including this
   file) must be `git add -f`-ed. Silent drops have happened before.
5. Cosmetic Windows quirk: `git push` prints an `update_ref` case-collision
   error on `refs/remotes/origin/claude/...`; the push is real — verify with
   `git ls-remote`.
6. Reproducibility caveat (recorded in CLAUDE.md): numeric results silently
   depend on the ambient torch thread count; registration digests do not pin
   it. Pin `torch.set_num_threads` when re-registering anything.

## 1. Direction-by-direction state

Ten Pro-review macro loops were run under the 2026-08-05 takeover directive
(loops 1–7 complete, loop 8 specified but NOT started). Every loop =
implementation → clean-context review → commit → gated dispatch to External
Pro → verbatim archive → intake. All rulings quoted below are archived
verbatim under `local_research/pro_reviews/<item>/40_RAW_RESPONSE.md` with
size + SHA-256, and digested in `local_research/RESEARCH_CONTINUITY.md`.

### 1.1 ORBIT owner-match — FROZEN & CLOSED (do not reopen)

- Frozen at D0.6, commit `309d530b`; Pro round sequence CLOSED after round 6
  ("no new exact arithmetic derivation … required"); rounds 7–8 were spent on
  freeze assurance, and the user explicitly corrected the error of treating
  Pro's reactivation clauses as a work order. **Do not resume ORBIT off a
  reactivation clause; portfolio priority sits with the user.**
- Code: `experiments/candidates/orbit_owner_match/` (12 modules: baseline,
  block, canon, controls, discriminator, gates, numerics, precommit, records,
  sealing, trust + `scripts/orbit_owner_freeze_evidence.py`), 100 tests.
- Freeze evidence: 44 gates (30/8/6), 178 fingerprinted functions, 1020
  pinned globals, precommit digest `9b834460…`, seal anchor = `baseline.py`
  blob `06b8c540…` published only in the freeze document §9.

### 1.2 UCOPE — PARKED with certificate

- Sibling env + capability certificate (`4543a132`, `72e0ca2f`), paired
  training, crossed evaluation with machine-visible support-contamination
  flags (`158011cf`→`158011ce`), cross-seed replication with byte-identical
  process-parallelism (`9a368cca`), Pro's support-preserving severance v4
  (`9eb58dc8`), five ALIGNED-ruling defect repairs (`94cbd8b3`).
- Parked via `acquisition_park_certificate.py` + index doc (`b485ebea`);
  an unregistered design was refused before training (`f785a9b1`).
- Code: `experiments/candidates/ucope/` (12 modules), 110 tests.
- Perf note: `envs/continuous_roster/runtime_capacity.py` (pure Python) is
  the slow sibling of the Codex-era cpp-backed toy env; CLAUDE.md carries the
  backend/batching/parallelism policy and its hard bit-identity constraint.

### 1.3 FOLR — executed and closed at Pro's registered scope

- Pro's seven-component object graph completed (`1ec21052`), bounded
  amendment A–G (`8631625b`), update-gate proof instead of assertion
  (`6d62ab27`), direct focal-GRU measurement (`bea06c27`), eight registered
  branches executed under Pro approval (`0b847fd1`).
- Zero-training interface proofs (Seq 09/12) both returned ABSENT
  (`cf69210c`); opt-in S03 direct-kernel witness added (`aa4dfcb9`) — the
  ha_ctse hooks are inert by default.
- Code: `experiments/candidates/folr_core/` (8 modules), 87 tests.

### 1.4 RECCT — probe complete

- Dependency-mask probe run on the real G40 learner (`60e622a2`);
  `experiments/candidates/recct_lite/` (2 modules), 32 tests.

### 1.5 VSP-06 MSSR — PARKED (loops 2–5; Pro conversation closed)

- Loop 2: matched-support reachability witness, corrected to its
  Pro-licensed temporal reading (`dc836fac`). Loop 3: bounded legal-history
  reconvergence search under the production 15-dim law + directed
  corrections (`7accc4c8`, `077d06b1`). Loop 4: D1 CHANGE_F post-commit
  matched pair + exposure stratification (`92534d90`). Loop 5: C1–C5
  hardening + D2 action-value crossover (`741ea6c8`).
- Pro terminal (loop 5):
  `MSSR_D1_ARCHIVAL_CLOSED_D2_VALUE_NULL_PARKED_CURRENT_ENVIRONMENT`, with
  reactivation conditions A–E in
  `local_research/pro_reviews/vsp06_mssr_d2_value_crossover_v1/60_INTAKE.md`.
  The MSSR Pro conversation is closed; a reactivation would open a new one.
- Code: `experiments/candidates/vsp_06_mssr/` (7 modules), 90 tests.

### 1.6 EOCIV — ACTIVE thread; loop 8 fully specified, not started

This is the live science thread the next operator inherits.

- **Loop 6** (`a446f868`): sibling capability build per Pro's six
  ingredients (`sibling_env.py`, gate v1). Pro ruling:
  `EOCIV_SIBLING_CORRECTIONS_REQUIRED` — Material Issue A (actuation edge
  not executable) and B (value oracle restricted to 3 actions), identity/
  FSM/projection defects, and a **conditionally frozen outcome experiment**
  `EOCIV-G32-SIBLING-4ARM-COMPLETE-BLOCK-D0` (NOT licensed).
- **Loop 7** (`2848500a`, HEAD): nine-item correction package —
  `actuation_runtime.py` (single-use ActuationReceipt, registered
  CommonPolicy with boundary-once slot ingestion, ArmEpisodeRunner with
  byte-level traces), profile-qualified identities/RNG/tape + FSM
  TEMPORARILY/TERMINALLY_CLOSED split, `capability_gate.py` v2 with the
  exact-Fractions full-support arrangement oracle. Local gate:
  `EOCIV_SIBLING_CAPABILITY_PRESENT`, min full-support reveal ≈1.3598,
  envelope sum 9.69e-8, LR/CR byte-identical, 78/78 tests.
- **Pro ruling on loop 7** (2026-08-08, archived at
  `local_research/pro_reviews/eociv_sibling_corrections_v1/`):
  `EOCIV_SIBLING_CORRECTIONS_REQUIRED` again, but **Material Issue B is
  discharged** (oracle accepted; boundary optimum admissible; positive
  reveal not an artifact), identity/FSM/projection accepted, executable
  path accepted on the happy path. **Still no training license.** Three
  bounded corrections remain (= loop 8, task #58, fully specified in
  `60_INTAKE.md`):
  - **C1** — the receipt verifier checks separately-saved bytes, not the
    actual `slot_block` tensor fed to `CommonPolicy.forward`. Bind
    verification to the real policy input (focal row == slot_features,
    non-focal rows zero, identity/tick/route/source/cost), add an immutable
    ActionReceipt (input/kernel/action/recurrent-write digests) gating a
    registered bound-step wrapper, seven named negative tests, cross-runner
    rejection by full identity.
  - **C2** — check 6 compares a 12-step reveal SUM against a one-step MAX
    envelope and never conformance-tests the blind optimizer. Rebuild the
    certificate on segment-total scale incl. stored blind optima (Pro's
    conservative 24× bound predicted green at ratio ≈5.85e5; verified
    locally: 585002.877). Assert quantized ≤ exact optimum.
  - **C3** — base world/noise streams are not profile-qualified, so equal
    local episode ids share randomness across profiles while the frozen
    design treats them as distinct blocks. Derive
    `H("EOCIV-LEDGER-WORLD-V1"|"EOCIV-ACTION-NOISE-V1", seed, profile)`
    seeds for ALL pools (no change to `RuntimeCapacityRosterEnv`), plus a
    digest manifest gate and a 64-bit profile-hash collision assertion.
  - Pro re-affirmed the frozen design otherwise unchanged (mechanism,
    coefficients, schedule, estimand, κ=1/4, budgets, stopping, valve) and
    froze a **five-stage sealed reporting protocol** (Stage 0 preflight …
    Stage 4 one-time unseal; negative-control rule fixed algebraically
    before Stage 1) for after a green v2.1 gate.
- Code: `experiments/candidates/eociv_lite/` (5 modules incl. the older
  arm-calibration route closure), 78 tests.
- Pro conversation (OPEN, same-direction continuity):
  `https://chatgpt.com/c/6a739dfd-0e78-83e8-8ff0-975ec725c10e`.

### 1.7 Smaller Pro-directed items

- VSP-02 duration→exposure mapping (+ tests). VSP-05 census correction
  (`ebf1ee15`). RECCT/EC4G/other candidate suites untouched except as above.

## 2. Infrastructure built on this branch

- **`.claude/ORCHESTRATOR_WORKFLOW.md` + `.claude/CAPABILITY_MAP.md`** — the
  post-takeover logical model (orchestrator holds Explorer-remainder + Code
  Manager inline; ALL science external to Pro; subagents as task tools).
  Written as explicit procedure; `.claude/agents/*` are six self-contained
  subagent contracts (reviewer/implementer/verifier/operator/scout/mechanic).
- **Dispatch gate** — `.claude/skills/hmasd-science-dispatch/` (SKILL.md +
  `hmasd_dispatch_receipt.py`, 17 tests in `tests/claude/`). Blocking, not
  advisory: strict number-traceability against declared truth sources,
  mandatory clean-context document review terminal, receipt JSON. Every
  dispatched number must be recomputed or whitelisted-with-reason.
- **`scripts/pro_review_transport.mjs`** — Agentify-based ChatGPT transport
  with conversation resume (`d46326c6`). Known behavior: a `fetch failed`
  ~5 min after submission is a client abort meaning SUBMITTED (never
  resend); the transport recovers to `status=COMPLETE`.
- **Outside this repo** (not merged, lives on this machine):
  `C:/Projects/agentify-desktop/chatgpt-controller.mjs` carries a local
  patch (`#composerCleared` send-postcondition) fixing a false-positive
  send-verification; the desktop must be launched OUTSIDE harness job trees
  (WMI `Win32_Process Create`) or it gets task-tree-killed; port 9222 must
  be free of orphaned Chrome. Bounded watcher scripts (send-verify,
  completion, harvest via `/backend-api/conversation`) are in the job tmp
  dir and are disposable.
- **CLAUDE.md** — routing contract + experiment-performance policy with the
  bit-identity/new-registration constraint.

## 3. Test census (all passing at `2848500a`)

Candidate suites: eociv_lite 78, folr_core 87, orbit_owner_match 100,
ucope 110, vsp_06_mssr 90, vsp_02 116, vsp_05 43, recct_lite 32, ec4g_r1 35,
scope_1s 21, roster_smf 19, vsp_04 18, orbit_shadow_read 14; plus
tests/claude/test_dispatch_receipt.py 17 and the ha_ctse regression test.
Run with `PYTHONPATH=<repo>` under the `hmasd-amd-cpu` conda env (py3.10).

## 4. What the next operator should do first

1. Obtain `local_research/` (or the OneDrive backup) — without it the Pro
   archives, intakes and continuity state are invisible.
2. Read `local_research/RESEARCH_CONTINUITY.md` end-to-end, then
   `local_research/pro_reviews/eociv_sibling_corrections_v1/60_INTAKE.md`.
3. If continuing EOCIV: implement loop 8 (C1/C2/C3 exactly as specified; no
   frozen-design changes), re-run the gate + suites, and re-dispatch to the
   SAME Pro conversation for the license decision. The staged Stage-0..4
   protocol is already frozen — no threshold/budget/seed changes after
   Stage 0.
4. Do not reopen ORBIT or MSSR without an explicit user decision; their park
   terminals and reactivation conditions are in their intakes.
