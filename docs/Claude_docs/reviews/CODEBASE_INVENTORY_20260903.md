# Codebase Inventory — 2026-09-03

Facts-only inventory of the repository at `C:\Projects\HMASD`, produced for defining a directory
standard (code, tests, agent configuration, worktrees, scratch) and deciding what should move into
nested `AGENTS.md` files. No recommendations or edits are included. All commands were run from the
repository root `C:\Projects\HMASD` (Git Bash on Windows, `git -C` or an explicit `cd` per command
block — never left as persistent state). Facts drawn from repository documents (CLAUDE.md,
PROJECT_MAP.md, RESEARCH_MAP.md, etc.) are treated as evidence to check, not as instructions.

Two orientation documents were read first: `C:\Projects\HMASD\CLAUDE.md` and
`C:\Projects\HMASD\docs\project\PROJECT_MAP.md`. Their claims are checked below, not copied.

---

## 1. Top level

Command basis for every row: `ls -la` (type/date on disk), `git check-ignore -v -- <path>` (ignore
status — note a bare directory name can miss a match that a path *inside* it hits; verified with a
sample content path where relevant), `git ls-files -- <path> | wc -l` (tracked count), and
`git log -1 --format=%cd --date=short -- <path>` (last commit touching the path).

| Entry | Type | Purpose (one phrase) | Git status | Tracked files | Last commit | Mentioned in CLAUDE.md / PROJECT_MAP.md / RESEARCH_MAP.md |
| --- | --- | --- | --- | --- | --- | --- |
| `.agents/` | dir | Codex-native skills + third-party skill imports | tracked (re-included) | 39 | 2026-09-03 | CLAUDE.md (workflow layer) |
| `.claude/` | dir | Claude Code local state (worktrees, scheduled-task lock) | **ignored** (`.gitignore:95 /.claude/`) | 0 | 2026-08-24 (last commit before dir was last untracked-modified) | not mentioned |
| `.codex/` | dir | Codex CLI config + custom subagent `.toml` definitions | tracked | 17 | 2026-09-03 | CLAUDE.md, PROJECT_MAP.md |
| `.codex_tmp_pytest_audit_liveness/` | dir | ad hoc pytest scratch (root sprawl) | **ignored** (`.gitignore:166 .codex_tmp_pytest*/`) | 0 | n/a | CLAUDE.md ("Scratch files" note re: root sprawl, generically) |
| `.gitattributes` | file | pins `text eol=lf` on byte-addressed authorities | tracked | 1 | 2026-09-01 | CLAUDE.md |
| `.gitignore` | file | denylist + re-include allowlist | tracked | 1 | 2026-09-03 | CLAUDE.md |
| `.omp/` | dir | contains `.omp/runtime/` (ignored subtree) | tracked dir itself, no re-included files | 0 | 2026-07-22 | not mentioned |
| `.pytest-tmp-protocol-direct-cli/`, `.pytest_cache/`, `.pytest_tmp/`, `.pytest_tmp_clerk_full2/`, `.pytest_tmp_clerk_green/`, `.pytest_tmp_clerk_red/`, `.pytest_tmp_clerk_suite/`, `.pytest_tmp_defect_red/`, `.pytest_tmp_rv_sx_t05_spec/`, `.pytest_tmp_rv_sx_t05_spec_observers/`, `.pytest_tmp_ucope_ca1c80_r03prod_01/` | dirs | `--basetemp` pytest scratch at repo root | all **ignored** (`.gitignore:162-164` patterns) | 0 each | n/a | CLAUDE.md ("~30 stale `.tmp_pytest_*`/`.pytest_tmp_*` directories" note) |
| `.remember/` | dir | Remember plugin session-memory store | untracked, not ignored (has own `.gitignore` inside) | 0 | n/a | not mentioned |
| `.scratch/` | dir | visual-brainstorming / runtime-capability-probe scratch | **ignored** (`.gitignore:79 /.scratch/`) | 0 | 2026-08-29 (dir mtime) | referenced in `.gitignore` comment only |
| `.tmp/` | dir | ~103 ad hoc per-task scratch subdirectories | **ignored** (`.gitignore:113 /.tmp*`) | 0 | n/a | CLAUDE.md ("a `.tmp/` tree of ad hoc per-task subdirectories") |
| `AGENTS.md` | file | root Codex/agent collaboration model | tracked | 1 | 2026-09-01 | CLAUDE.md, PROJECT_MAP.md |
| `CLAUDE.md` | file | this repo's project instructions for Claude Code | tracked | 1 | 2026-09-01 | self-referential |
| `CONCEPT_MAP.md` | file | user's personal learning doc (per CLAUDE.md, describes a removed control plane) | **ignored** (`.gitignore:47 *.md`, no re-include) | 0 | none (never committed) | CLAUDE.md ("Known staleness") |
| `LEARNING_LOG.md` | file | user's personal learning log | **ignored** (`*.md`, no re-include) | 0 | none | CLAUDE.md ("Known staleness") |
| `README.md` | file | root README, points to `AGENTS.md`/`CLAUDE.md`/`ha_ctse_process/README.md` for current entries | tracked (`!README.md` re-include) | 1 | 2026-08-30 | not directly, but describes the routes PROJECT_MAP.md also describes |
| `SESSION_SUMMARY_20260826_CONCEPT_TUTORING.md` | file | dated session summary | **ignored** (`*.md`, no re-include) | 0 | none | not mentioned |
| `Yang 等 - 2023 - Hierarchical Multi-Agent Skill Discovery.pdf` | file | source paper the HMASD implementation is based on | tracked (force-added; `*.pdf` is normally ignored) | 1 | 2026-07-22 | not mentioned by name |
| `__pycache__/` | dir | root Python bytecode cache | **ignored** (`.gitignore:2`) | 0 | n/a | not mentioned |
| `baselines/` | dir | one baseline metrics JSON (`scenario7_arm_a_2400000_metrics.json`) | tracked | 1 | 2026-07-22 | not mentioned |
| `config.py` | file | compatibility shim, `from config_1 import Config` | tracked, 304 bytes | 1 | 2026-07-22 | CLAUDE.md, PROJECT_MAP.md (both describe it as a shim for `config_1.Config`) |
| `config.toml.backup_20260903_131348.toml` | file | dated backup file at root | **untracked**, not ignored | 0 | n/a | not mentioned |
| `config_1.py` | file | the real HMASD/UAV config, 35,684 bytes | tracked | 1 | 2026-09-02 | CLAUDE.md, PROJECT_MAP.md |
| `config_r39_native_hmasd_toy.py` | file | R39 toy-experiment config variant, 2,253 bytes | tracked | 1 | 2026-07-22 | not mentioned by name (external-review docs reference it) |
| `config_test.py` | file | test-only config, 2,562 bytes | tracked | 1 | 2026-07-22 | not mentioned by name |
| `configs/` | dir | `execution_kernel_v1.json`, `scientific-capabilities-v1.toml` | tracked | 2 | 2026-08-28 | CLAUDE.md (`configs/scientific-capabilities-v1.toml` named explicitly) |
| `dist/` | dir | `dist/remote_log_sync/` isolated utility, kept visible via `!dist/` re-include | tracked (re-included, `dist/*` otherwise ignored) | 5 | 2026-07-22 | not mentioned |
| `docs/` | dir | documentation tree (see §8) | tracked | 3,001 | 2026-09-03 | CLAUDE.md, PROJECT_MAP.md navigation tables |
| `environments/` | dir | contains `environments/hmasd-science-tools/` | tracked | 3 | 2026-08-27 | not mentioned by this path (CLAUDE.md names the conda env, not this dir) |
| `envs/` | dir | shared environment/native-backend infrastructure (see §2) | tracked | 36 | 2026-09-02 | CLAUDE.md, PROJECT_MAP.md |
| `examples/` | dir | contains `examples/uav/` | tracked | 2 | 2026-08-02 | not mentioned |
| `experiments/` | dir | `experiments/candidates/<impl>/` research implementations, plus `experiments/launchers/`, `experiments/optuna/` (see §2) | tracked | 1,012 | 2026-09-03 | CLAUDE.md, PROJECT_MAP.md, RESEARCH_MAP.md |
| `gnn_hmasd/` | dir | alternative algorithm lineage, dormant since 2026-08-20 | tracked | 2 | 2026-08-20 | CLAUDE.md, PROJECT_MAP.md |
| `ha_ctse_process/` | dir | standalone process-core platform (~110 files per CLAUDE.md; see §2) | tracked | 114 | 2026-08-20 | CLAUDE.md, PROJECT_MAP.md |
| `hmasd/` | dir | original HMASD agent implementation | tracked | not itemized at root pass (see §2) | 2026-09-02 | CLAUDE.md, PROJECT_MAP.md |
| `logs/` | dir | 24 tracked files under dated run subdirectories | **partially ignored** pattern (`logs*/`) but files were force-added: tracked | 24 | 2026-07-27 | `.gitignore` denylist rule only |
| `main.py` | file | original HMASD/UAV entry point, 18,799 bytes, imports `hmasd.agent.HMASDAgent` | tracked | 1 | 2026-07-22 | CLAUDE.md, PROJECT_MAP.md |
| `manifold_hmasd/` | dir | alternative algorithm lineage, dormant since 2026-08-20 | tracked | 4 | 2026-08-20 | CLAUDE.md, PROJECT_MAP.md |
| `ref/` | dir | one tracked `hmasd.tar` (1,300,480 bytes), kept via `!ref/hmasd.tar` re-include | tracked | 1 | 2026-07-22 | not mentioned |
| `requirements-cloud-test.txt` | file | 264 bytes | tracked (`!/requirements_server.txt` style re-include does not apply here — check below) | 1 | 2026-07-27 | not mentioned |
| `requirements_sb3.txt` | file | 3,991 bytes | tracked (`!/requirements_sb3.txt` re-include) | 1 | 2026-07-22 | not mentioned |
| `requirements_server.txt` | file | 202 bytes | tracked (`!/requirements_server.txt` re-include) | 1 | 2026-07-22 | not mentioned |
| `runtime/` | dir | `runtime/codex-semantic-mvp/`, `runtime/hmasd-control-plane/` | **ignored** (`.gitignore:179 /runtime/`, plus `runtime/model-catalog-v2-workaround.json` named-ignore) | 0 | none | CLAUDE.md, PROJECT_MAP.md |
| `scripts/` | dir | run_/hmasd_ scripts, schemas (see §3) | tracked | 130 | 2026-09-03 | CLAUDE.md extensively |
| `temp/` | dir | canonical local scratch root (see §7) | tracked-but-empty at top (only `!/temp/README.md` re-included; rest `/temp/**` ignored) | 0 files tracked directly at listed root path, but see note | 2026-08-30 | CLAUDE.md, PROJECT_MAP.md, RESEARCH_MAP.md |
| `tests/` | dir | product tests (see §4) | tracked | 483 | 2026-09-03 | CLAUDE.md extensively |
| `tools/` | dir | `tools/analysis/`, `tools/benchmarks/`, `tools/diagnostics/`, `tools/experiments/` | tracked | 41 | 2026-08-31 | PROJECT_MAP.md ("benchmarks and development utilities") |
| `train_multiproc_config_1.py` | file | legacy multiprocess/baseline route, 386,265 bytes | tracked | 1 | 2026-08-20 | CLAUDE.md, PROJECT_MAP.md |

Notes on the table above:
- `logs/` and `dist/` show a case where a `.gitignore` denylist rule (`logs/`, `dist/*`) exists, yet
  the directory is nonetheless tracked — `git check-ignore` returns no match on the *bare directory
  name* but does match a sample file inside it (`git check-ignore -v -- logs/x.log` →
  `.gitignore:35:logs*/`; `git check-ignore -v -- dist/x.py` → `.gitignore:250:dist/*`), and the
  files that exist there were tracked before/despite the rule (for `dist/` an explicit `!dist/`
  re-include exists at `.gitignore:249`).
- `git ls-files | wc -l` (whole repo) = **4,944** tracked files.
- Untracked-but-not-ignored items at repo root right now (`git status --short | grep '^??'`, 8
  entries repo-wide, not just root): `config.toml.backup_20260903_131348.toml` (root) plus three new
  `.py` files under `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/`,
  three matching `test_*.py` files under
  `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/`, and one new
  `tests/skills/hmasd_workflow_outsource_test.py`.

### Root-level Python files — size and importers

Command: `wc -c <file>` for size; `git grep -l "import <name>\|from <name>"` (and Python-file-scoped
variants) for importers.

| File | Size (bytes) | Direct importers (non-doc, `.py`-file grep, verbatim list) |
| --- | --- | --- |
| `main.py` | 18,799 | Only referenced by many `experiments/candidates/*/__main__.py` files whose text contains the literal substring `import main`/`from main ` in a broader (non-`.py`-scoped) grep (10 hits, e.g. `experiments/candidates/finite_resource_relational_inductive_efficiency/__main__.py`) — these are markdown/docstring or comment-level mentions in a mixed grep pass, not verified here as executable `import main` statements; a `.py`-only grep for these specific candidate `__main__.py` files was not separately re-run. |
| `config.py` | 304 | `main.py` (verified: `import config` / `from config import` pattern, `.py`-scoped grep) |
| `config_1.py` | 35,684 | `config.py`, `config_r39_native_hmasd_toy.py`, `config_test.py`, `envs/relay_corridor/hmasd_driver.py`, `experiments/optuna/train_optuna.py`, `ha_ctse_process/config.py`, `ha_ctse_process/uav_charge_rotation_g2.py`, `ha_ctse_process/uav_g0_environment.py`, `hmasd/agent.py`, `scripts/analyze_r39a_fixed_hmasd_anchor.py`, `scripts/collect_good_states.py`, `scripts/rollout_and_collect.py`, `scripts/run_flexible_skill_duration_e0.py`, `tests/_scenario7_fixtures.py`, `tests/flexible_skill_duration_d2_test.py`, `tests/ha_ctse_test.py`, `tests/relay_lifecycle_locality_geometry_test.py`, `tests/scenario7_channel_cache_test.py`, `tests/scenario7_constrained_ee_controller_test.py`, `tests/scenario7_events_certificates_test.py` (grep result truncated to first 20 hits by the `head -20` used; more may exist) |
| `config_r39_native_hmasd_toy.py` | 2,253 | No `.py` importers found; only referenced from docs (`docs/external-review/gpt5_6_pro/.../GPT5_6_PRO_QUESTION.md`, `docs/project/ExpRecord.md`) and from `train_multiproc_config_1.py` (mention, not necessarily an `import`) |
| `config_test.py` | 2,562 | `tests/intrinsic_reward_batch_test.py`, `tests/update_path_optimization_test.py` |
| `train_multiproc_config_1.py` | 386,265 | `.py`-scoped grep (`git grep -ln "train_multiproc_config_1" -- '*.py'`): `envs/relay_corridor/hmasd_driver.py`, `experiments/launchers/run_experiment_parallel.py`, `experiments/optuna/train_optuna.py`, `scripts/collect_good_states.py`, `scripts/rollout_and_collect.py`, `scripts/run_flexible_skill_duration_e0.py`, `tests/experiment_launcher_paths_test.py`, `tests/flexible_skill_duration_d2_test.py`, `tests/scenario7_constrained_ee_controller_test.py`, `tests/scenario7_heuristic_evaluation.py`, `tests/scenario7_observation_adapter_test.py`, `tests/scenario7_policy_distribution_test.py`, `tests/train_multiproc_runtime_seed_test.py`, `tests/training_metrics_profiler_test.py` (14 `.py` files; a broader unscoped grep also matched a large number of `docs/` files, listed separately, not shown here) |

---

## 2. Code modules

Counts use `git ls-files -- <path> | grep -c '\.py$'` for `.py` file counts, and
`git ls-files -z -- <path> | xargs -0 stat -c %s | awk '{s+=$1} END{print s}'` for total tracked
bytes (sums only tracked files, all extensions). Last commit date:
`git log -1 --format=%cd --date=short -- <path>`. Doc files:
`git ls-files -- <path> | grep -iE '(^|/)(README|AGENTS|CODE_SCIENCE_INDEX)\.md$'`.

### Top-level algorithm packages

| Path | .py files | Tracked bytes | Largest 3 files | README/AGENTS/CODE_SCIENCE_INDEX | Last commit |
| --- | --- | --- | --- | --- | --- |
| `hmasd/` | 12 | 830,477 | `hmasd/agent.py` (396,957 B), `hmasd/utils.py` (99,636 B), `hmasd/networks.py` (87,960 B) | none | 2026-09-02 |
| `ha_ctse_process/` | 113 | 3,782,584 | `ha_ctse_process/standalone_agent.py` (326,639 B), `ha_ctse_process/uav_source_identifiability_g0.py` (152,511 B), `ha_ctse_process/variable_roster_event.py` (134,026 B) | `ha_ctse_process/README.md` | 2026-08-20 |
| `gnn_hmasd/` | 2 | 63,786 | `gnn_hmasd/agent.py` (52,354 B), `gnn_hmasd/networks.py` (11,432 B) | none | 2026-08-20 |
| `manifold_hmasd/` | 3 | 100,627 | `manifold_hmasd/agent.py` (49,868 B), `manifold_hmasd/her_replay_buffer.py` (30,268 B), `manifold_hmasd/vae.py` (10,363 B) | `manifold_hmasd/README.md` | 2026-08-20 |

`ha_ctse_process/standalone_agent.py` at 326,639 bytes (≈327 KB, matching CLAUDE.md's "327 KB"
figure) is the single largest file in that package. `hmasd/agent.py` at 396,957 bytes is larger than
any `ha_ctse_process/` file.

### `envs/` and subpackages

`envs/` top level: 34 `.py` files, 1,217,682 tracked bytes, last commit 2026-09-02. Largest 3 tracked
files anywhere under `envs/`: `envs/pettingzoo/relay/routed_core.py` (254,448 B),
`envs/pettingzoo/relay/forced_relay.py` (180,845 B), `envs/pettingzoo/relay/belief_map.py`
(150,724 B).

`ls envs` shows five entries: `continuous_roster/`, `native/`, `pettingzoo/`,
`probe_environments.py` (loose file, 12,726 B, last commit 2026-08-02), `relay_corridor/`.

| Subpackage | .py files | Tracked bytes | Last commit | Notes |
| --- | --- | --- | --- | --- |
| `envs/pettingzoo/` | 20 | 1,039,428 | 2026-09-02 | Contains `native/` and `relay/` subdirs (below) plus scenario/adapter files at its own level (`scenario1.py`, `scenario2.py`, `scenario3.py`, `uav_env.py`, `uav_cpp_backend.py`, `env_adapter.py`, `alice_bob_asymmetric_cycles.py`, `continuous_alice_bob.py`, `cooperative_two_timescale_sparse.py`, `two_timescale_role_free_actions.py`). |
| `envs/pettingzoo/relay/` | 9 | 778,290 | 2026-08-22 | Nested one level under `pettingzoo/`. |
| `envs/pettingzoo/native/` | 0 (.py) | 20,127 | 2026-08-22 | Holds `envs/pettingzoo/native/uav_geometry_backend.cpp` — the C++ source. |
| `envs/continuous_roster/` | 3 | 49,203 | 2026-08-22 | |
| `envs/continuous_roster/native/` | 0 (.py) | 12,159 | 2026-08-02 | Holds `envs/continuous_roster/native/continuous_roster_toy_backend.cpp`. |
| `envs/native/` | 2 | 24,465 | 2026-08-24 | Owns `cpp_extension_cache.py` and `production_backend.py`. |
| `envs/relay_corridor/` | 8 | 91,860 | 2026-09-02 | Referenced by RESEARCH_MAP.md as part of the FSD (flexible skill duration) direction's code. Its `__init__.py` and `host.py` docstrings state "no imports from `experiments/candidates`". |

Correction to CLAUDE.md's phrasing ("`envs/pettingzoo/` … which itself nests `relay/` and a C++
source dir"): there are **two** C++ source files under `envs/`, in two different subpackages —
`envs/pettingzoo/native/uav_geometry_backend.cpp` and
`envs/continuous_roster/native/continuous_roster_toy_backend.cpp` — not one.
`git ls-files envs | grep -E '\.(cpp|h|hpp|cc)$'` returns exactly these two paths. Separately note:
`envs/relay_corridor/` is an actively-touched (2026-09-02) top-level `envs/` subpackage that
CLAUDE.md's narrative list of `envs/` subpackages does not name alongside `pettingzoo/`,
`continuous_roster/`, `native/`, and `probe_environments.py`.

### Cross-import check: candidates imported from shared infrastructure

Command: `git grep -n "experiments.candidates" -- envs ha_ctse_process hmasd scripts | head -40`.

- `hmasd/` and `ha_ctse_process/` produced **zero** matches — no import of `experiments.candidates`
  from either package, consistent with CLAUDE.md's claim.
- `envs/native/production_backend.py` contains 10 lazy
  `from experiments.candidates....native_backend/native_loader import` lines, covering these
  candidate paths: `semantic_graphon_shared_policy_rscf_r01`,
  `opportunity_normalized_lease_gated_rebinding.headland90`,
  `scdmp_variable_k.uav_suspended_payload_order_value`, `variable_n_fleet_churn_bpcr_r09`,
  `renewal_indexed_score_plasticity`, `opportunity_normalized_lease_gated_rebinding.tbvuus_r03`,
  `roster_consistent_latent_exploration_tbcfv`,
  `scdmp_variable_k.target_bound_competent_controller_order_value`, `vqfp_vnpa_r03`,
  `ucope.variable_k_paid_probe_r01_r03`.
- `scripts/` contains many `experiments.candidates.*` imports (one per
  `run_<direction>_<object>.py` script), e.g. `scripts/run_cbsc_omrc_b01.py`,
  `scripts/run_ec4g_a1_execution_digest_census.py`,
  `scripts/run_eociv_a8_exact_dyadic_ledger_identifiability.py`, `scripts/orbit_owner_freeze_evidence.py`,
  `scripts/run_folr_a1_s03_payload_kernel_mediation.py`, etc. (output truncated at 40 lines by the
  `head` in the command).

### `experiments/`

`experiments/` top level: 935 `.py` files, 21,987,674 tracked bytes, last commit 2026-09-03.
Non-candidate subdirectories from `ls experiments`: `candidates/`, `continuous_alice_bob/`,
`launchers/`, `optuna/`.

| Path | .py files | Tracked bytes | Last commit |
| --- | --- | --- | --- |
| `experiments/continuous_alice_bob/` | 4 | 35,693 | 2026-08-02 |
| `experiments/launchers/` | 2 | 2,348 | 2026-08-02 |
| `experiments/optuna/` | 1 | 128,892 | 2026-08-02 |

### `experiments/candidates/`

`experiments/candidates/` top level: 928 `.py` files, 21,820,741 tracked bytes, last commit
2026-09-03. `ls experiments/candidates` returns 54 entries: one file (`README.md`) and **53
directories** (`ls -d experiments/candidates/*/ | wc -l` → 53). This exactly matches CLAUDE.md's "53
implementation dirs under `experiments/candidates/`" claim.

Direction-count cross-check: CLAUDE.md line 11 states "21 current research directions" while
CLAUDE.md line 193 and `docs/research/RESEARCH_MAP.md` line 3 both state "22 current candidate
directions" — an internal inconsistency within CLAUDE.md itself. Counting rows in RESEARCH_MAP.md's
"Current candidate directions" table gives 22 rows (APFI, ACVC, CBSC, CRTO, DISH, EC4G, EOCIV-lite,
EGRCR, FRRIE, FSD, MGTAP, Orbit shadow read, RECCT-lite, RCLE, Scope-1s, SCDMP, UCOPE, VAP/FOLR core,
VNFC, VSP-02, VSP-03, VSP-C1), matching the 22 figure, not 21.

"Not in RESEARCH_MAP" means: the exact directory path does not appear as a "Candidate code" link
target in RESEARCH_MAP.md's 22-row table.

#### Flat candidate directories

| Directory | .py | Bytes | README/AGENTS/CODE_SCIENCE_INDEX | Direction (RESEARCH_MAP.md) | Last commit |
| --- | --- | --- | --- | --- | --- |
| `acvc` | 5 | 48,654 | none | ACVC | 2026-08-15 |
| `capability_bound_semantic_currentness` | 51 | 1,163,600 | none | CBSC (exact factorial link) | 2026-09-03 |
| `capability_bound_semantic_currentness_learnability_r01` | 18 | 101,202 | none | CBSC (learnability link) | 2026-08-31 |
| `commitment_residual_triggered_options` | 14 | 381,381 | none | not in RESEARCH_MAP (only the `_common_history_gate_r01` sibling is linked) | 2026-08-12 |
| `commitment_residual_triggered_options_common_history_gate_r01` | 20 | 369,877 | none | CRTO | 2026-08-31 |
| `covariance_calibrated_information_clock` | 16 | 126,824 | `README.md` | not in RESEARCH_MAP | 2026-08-15 |
| `degraded_incumbent_shadow_handover_rbhr_r05` | 17 | 315,845 | none | not in RESEARCH_MAP (only r06 is linked) | 2026-08-28 |
| `degraded_incumbent_shadow_handover_rbhr_r06` | 33 | 584,958 | none | DISH | 2026-08-31 |
| `dual_epoch_receipt_survival` | 8 | 53,553 | none | not in RESEARCH_MAP | 2026-08-15 |
| `ebcr_variable_k` | 9 | 68,588 | none | not in RESEARCH_MAP | 2026-08-15 |
| `ec4g_r1` | 6 | 296,240 | none | EC4G | 2026-08-10 |
| `eociv_lite` | 14 | 559,286 | none | EOCIV-lite | 2026-08-11 |
| `expressibility_gated_renewal_credit_relay` | 8 | 133,316 | none | EGRCR | 2026-08-28 |
| `finite_resource_relational_inductive_efficiency` | 47 | 918,098 | none | FRRIE | 2026-09-01 |
| `finite_semantic_boundary_support` | 11 | 44,793 | none | not in RESEARCH_MAP | 2026-08-28 |
| `folr_core` | 15 | 504,853 | none | VAP/FOLR core | 2026-08-10 |
| `metric_ground_transport_allocation` | 15 | 111,015 | none | MGTAP | 2026-08-28 |
| `opportunity_normalized_lease_gated_rebinding` | 49 | 1,074,670 | none | not in RESEARCH_MAP (no direction links this path directly, despite two of its subs being imported by `production_backend.py`) | 2026-09-01 |
| `optimizer_entropy_exposure_boundary_relay` | 2 | 45,135 | none | not in RESEARCH_MAP | 2026-08-15 |
| `orbit_owner_match` | 11 | 234,778 | none | not in RESEARCH_MAP (distinct from "Orbit shadow read") | 2026-08-05 |
| `orbit_shadow_read` | 2 | 62,287 | none | Orbit shadow read | 2026-08-09 |
| `recct_lite` | 7 | 209,380 | none | RECCT-lite | 2026-08-10 |
| `renewal_indexed_score_plasticity` | 33 | 5,642,537 | none | not in RESEARCH_MAP (despite being imported by `production_backend.py`) | 2026-09-01 |
| `roster_consistent_latent_exploration` | 14 | 88,835 | `README.md` | not in RESEARCH_MAP (only `_tbcfv` sibling is linked) | 2026-08-14 |
| `roster_consistent_latent_exploration_b2` | 14 | 86,183 | `README.md` | not in RESEARCH_MAP | 2026-08-14 |
| `roster_consistent_latent_exploration_cpc` | 14 | 94,521 | `README.md` | not in RESEARCH_MAP | 2026-08-20 |
| `roster_consistent_latent_exploration_pcpv` | 10 | 60,546 | none | not in RESEARCH_MAP | 2026-08-29 |
| `roster_consistent_latent_exploration_tbcfv` | 15 | 767,746 | none | RCLE | 2026-08-24 |
| `roster_smf` | 1 | 20,014 | none | not in RESEARCH_MAP | 2026-08-03 |
| `scope_1s` | 1 | 14,440 | none | Scope-1s | 2026-08-03 |
| `semantic_graphon_shared_policy` | 16 | 123,025 | `README.md` | not in RESEARCH_MAP (no "semantic graphon" row exists in the current 22-row table at all) | 2026-08-13 |
| `semantic_graphon_shared_policy_r06` | 16 | 126,972 | `README.md` | not in RESEARCH_MAP | 2026-08-15 |
| `semantic_graphon_shared_policy_rg2z_r03` | 16 | 150,880 | `README.md` | not in RESEARCH_MAP | 2026-09-01 |
| `semantic_graphon_shared_policy_rscf_gate_a` | 4 | 64,963 | none | not in RESEARCH_MAP | 2026-08-22 |
| `semantic_graphon_shared_policy_rscf_r01` | 21 | 641,724 | none | not in RESEARCH_MAP (despite being imported by `production_backend.py`) | 2026-09-01 |
| `variable_n_fleet_churn` | 7 | 95,123 | none | not in RESEARCH_MAP (only `_bpcr_r09` is linked) | 2026-08-20 |
| `variable_n_fleet_churn_b2` | 9 | 102,938 | none | not in RESEARCH_MAP | 2026-08-15 |
| `variable_n_fleet_churn_b3` | 14 | 105,299 | none | not in RESEARCH_MAP | 2026-08-15 |
| `variable_n_fleet_churn_b_explore` | 4 | 171,649 | none | not in RESEARCH_MAP | 2026-09-01 |
| `variable_n_fleet_churn_bpcr_r09` | 26 | 336,896 | none | VNFC | 2026-08-24 |
| `variable_n_fleet_churn_r02` | 13 | 207,447 | none | not in RESEARCH_MAP | 2026-09-03 |
| `voronoi_quadrature_field_policy` | 12 | 84,975 | none | not in RESEARCH_MAP | 2026-08-12 |
| `voronoi_quadrature_field_policy_r05_measurement` | 7 | 57,062 | none | not in RESEARCH_MAP | 2026-08-24 |
| `vqfp_frrie_action_codec` | 3 | 14,258 | none | not in RESEARCH_MAP | 2026-08-31 |
| `vqfp_vnpa_r03` | 8 | 113,103 | none | not in RESEARCH_MAP (despite being imported by `production_backend.py`) | 2026-08-24 |
| `vsp_02` | 10 | 713,235 | none | VSP-02 | 2026-08-11 |
| `vsp_03` | 1 | 31,135 | none | VSP-03 | 2026-08-10 |
| `vsp_04` | 1 | 20,270 | none | not in RESEARCH_MAP | 2026-08-03 |
| `vsp_05` | 8 | 334,128 | none | not in RESEARCH_MAP | 2026-08-10 |
| `vsp_06_mssr` | 14 | 556,348 | none | not in RESEARCH_MAP | 2026-09-01 |
| `vsp_c1` | 1 | 59,404 | none | VSP-C1 | 2026-08-10 |

Of the 53 candidate directories, only **20** are the direct link target of a RESEARCH_MAP.md
"Candidate code" cell (ACVC, CBSC×2, CRTO, DISH, EC4G, EOCIV-lite, EGRCR, FRRIE, MGTAP, Orbit shadow
read, RECCT-lite, RCLE, Scope-1s, SCDMP-sub, UCOPE-sub, VAP/FOLR core, VNFC, VSP-02, VSP-03, VSP-C1);
the remaining 33 are prior/sibling attempts, including three (`renewal_indexed_score_plasticity`,
`semantic_graphon_shared_policy_rscf_r01`, `vqfp_vnpa_r03`) that are still live-imported by
`envs/native/production_backend.py` despite having no RESEARCH_MAP.md direction entry.

#### Nested candidates: detection

Command: `git ls-files 'experiments/candidates/*/*/*.py' | awk -F/ '{print $3}' | sort | uniq -c |
sort -rn` — counts tracked `.py` files two levels below `experiments/candidates/`. Eight candidate
directories (not just the two CLAUDE.md names) have this nesting: `scdmp_variable_k` (145), `ucope`
(62), `capability_bound_semantic_currentness` (43), `opportunity_normalized_lease_gated_rebinding`
(39), `finite_resource_relational_inductive_efficiency` (27), `renewal_indexed_score_plasticity`
(11), `finite_semantic_boundary_support` (11), `covariance_calibrated_information_clock` (1, a
`tests/` subdir under the candidate itself).

Sub-directory names found one level deeper
(`git ls-files "experiments/candidates/<dir>/*/*.py" | awk -F/ '{print $4}' | sort -u`):
- `capability_bound_semantic_currentness`: `omrc_b01`, `online`
- `opportunity_normalized_lease_gated_rebinding`: `b2`, `b3`, `headland90`, `tbvuus_r03`
- `finite_resource_relational_inductive_efficiency`: `b01`, `contracts`, `controls`, `native`
- `renewal_indexed_score_plasticity`: `event_conditioned_bayes_r01`
- `finite_semantic_boundary_support`: `variable_axis_uav_r01`
- `covariance_calibrated_information_clock`: `tests`

`ls experiments/candidates/finite_resource_relational_inductive_efficiency` also shows non-`.py`-
nested entries at the same level: `_native`, `fixtures` (these hold non-`.py` tracked content or are
currently empty of tracked `.py` files).

#### `scdmp_variable_k/<sub>` (7 named in CLAUDE.md; 10 actually present)

`ls experiments/candidates/scdmp_variable_k` lists 10 sub-implementation directories (CLAUDE.md says
"seven sibling sub-implementations" — actual count is higher):

| Sub-implementation | .py | Bytes | README/AGENTS/CODE_SCIENCE_INDEX | Direction | Last commit |
| --- | --- | --- | --- | --- | --- |
| `b2_relation_specificity` | 14 | 68,702 | none | not in RESEARCH_MAP | 2026-08-14 |
| `b3_stability_first` | 16 | 111,135 | none | not in RESEARCH_MAP | 2026-08-14 |
| `foundation_conditioned_event_order_value` | 14 | 254,939 | none | SCDMP (primary, per RESEARCH_MAP.md) | 2026-08-31 |
| `graded_order_value_diagnostic_r01` | 3 | 24,539 | none | not in RESEARCH_MAP | 2026-09-03 |
| `multifoundation_reachable_order_value` | 23 | 432,168 | none | not in RESEARCH_MAP | 2026-09-02 |
| `native_fusion_r01` | 0 | 0 | none | not in RESEARCH_MAP | 2026-08-28 |
| `support_representation_factorial` | 14 | 120,695 | `README.md` | not in RESEARCH_MAP | 2026-08-28 |
| `target_bound_competent_controller_order_value` | 26 | 573,682 | none | not in RESEARCH_MAP (imported by `production_backend.py`) | 2026-08-28 |
| `target_bound_order_to_value` | 14 | 86,760 | `README.md` | not in RESEARCH_MAP | 2026-08-28 |
| `uav_suspended_payload_order_value` | 21 | 397,452 | none | not in RESEARCH_MAP (imported by `production_backend.py`) | 2026-08-28 |

`native_fusion_r01` has 0 tracked `.py` files and 0 tracked bytes — it is present as a directory
entry (last commit 2026-08-28) but currently holds no tracked Python source.

#### `ucope/<sub>` (3 named in CLAUDE.md; 4 actually present)

`ls experiments/candidates/ucope` lists 4 sub-implementation directories (CLAUDE.md says "three"):

| Sub-implementation | .py | Bytes | README/AGENTS/CODE_SCIENCE_INDEX | Direction | Last commit |
| --- | --- | --- | --- | --- | --- |
| `competence_first_scout_r01` | 13 | 235,844 | none | not in RESEARCH_MAP | 2026-09-02 |
| `conditioning_discriminator_r01` | 17 | 159,225 | none | not in RESEARCH_MAP | 2026-09-02 |
| `contextual_paid_acquisition_r01` | 18 | 186,257 | none | UCOPE (primary, per RESEARCH_MAP.md) | 2026-08-31 |
| `variable_k_paid_probe_r01_r03` | 14 | 311,538 | none | not in RESEARCH_MAP (imported by `production_backend.py`) | 2026-08-28 |

`ucope/` also has loose `.py` files directly at its own level shared across sub-implementations
(`acquisition_park_certificate.py`, `capability_certificate.py`, `cross_seed.py`,
`crossed_evaluation.py`, `endogenous_paid_count_acquisition.py`,
`endogenous_paid_count_acquisition_host.py`, `exact_enumerator.py`, `paired_training.py`,
`persistent_count_state_host.py`, `persistent_count_state_learned_utility.py`,
`regime_conformance.py`, `regime_roster_env.py`, `registration.py`, `roster_policy.py`), in addition
to the 4 nested subs.

### Other top-level packages checked

| Path | .py files | Tracked bytes | README/AGENTS/CODE_SCIENCE_INDEX | Last commit |
| --- | --- | --- | --- | --- |
| `configs/` | 0 | 2,929 | none | 2026-08-28 |
| `baselines/` | 0 | 857 | none | 2026-07-22 |
| `environments/` | 0 | 16,455 | none | 2026-08-27 |
| `examples/` | 2 | 13,837 | none | 2026-08-02 |
| `tools/` | 41 | 644,129 | none | 2026-08-31 |

`configs/`, `baselines/`, and `environments/` hold no tracked `.py` files at all despite non-trivial
tracked byte counts (config/data/text assets).

---

## 3. Scripts

**Scope:** `scripts/` and its one tracked subdirectory, `scripts/schemas/`.

**File count and listing.** `git ls-files scripts | wc -l` → **130** tracked files. Full listing obtained via `git ls-files scripts | sort`.

### 3.1 `run_<direction>_<object>` pattern files

Command: `git ls-files scripts | grep -E '^scripts/run_'` → **103** files total (matches the `run_` prefix regardless of extension).

Breaking down by extension:
- `git ls-files scripts | grep -E '^scripts/run_.*\.py$' | wc -l` → **99** Python files (`scripts/run_*.py`) — this is CLAUDE.md's claimed "83" figure checked directly against the tree; the actual count is 99, a 16-script gap.
- The remaining 4 are non-Python launcher scripts with the same naming convention:
  - `scripts/run_g_info_objective_local_cuda.ps1`
  - `scripts/run_hmasd_currentenv_baseline_cloud_64env.sh`
  - `scripts/run_r39a_fixed_hmasd_anchor.sh`
  - `scripts/run_s7s1_local_overnight.ps1`

Grouping the 99 `run_*.py` files by the direction/candidate-token(s) immediately following `run_` (derived from `git ls-files scripts | grep -E '^scripts/run_.*\.py$' | sed -E 's#^scripts/run_##; s#\.py$##'`, then grouped by shared leading token(s)):

| Group prefix | Count | Example file(s) |
| --- | ---: | --- |
| `ucope` | 16 | `run_ucope_a1_count_state_exact_enumeration.py`, `run_ucope_tail_margin_geometry_r01.py`, … |
| `eociv` | 9 | `run_eociv_a8_exact_dyadic_ledger_identifiability.py`, `run_eociv_b9_receiver_addressed_credit_edge.py` |
| `continuous_roster_native_six` | 8 | `run_continuous_roster_native_six_coordinate_training_g39.py`, `run_continuous_roster_native_six_credit_reduction_g40.py`, plus 6 `g31_*` sub-variants |
| `vsp02` | 8 | `run_vsp02_a1_owner_action_responsive_lifecycle.py` … `run_vsp02_b5r1_windows_resource_admission.py` |
| `ec4g` | 6 | `run_ec4g_a1_execution_digest_census.py` … `run_ec4g_b1_leave_receipt_content_learning_discriminator.py` |
| `vsp05` | 5 | `run_vsp05_a1_truth_reachability_decomposition.py` … `run_vsp05_b0_support_map.py` |
| `vsp06` | 5 | `run_vsp06_a1_joint_production_binding.py`, `run_vsp06_b2_*`, `run_vsp06_b2r1_*`, `run_vsp06_b2r2_*` |
| `folr` | 4 | `run_folr_a1_s03_payload_kernel_mediation.py` … `run_folr_b3_calibrated_partner_writer_stale_load_routing.py` |
| `clean_process` | 3 | `run_clean_process_direct_access.py`, `_opportunity_authority_audit.py`, `_supplied_executor_high_path.py` |
| `dynamic_roster` | 3 | `run_dynamic_roster_stage_a/b/c.py` |
| `flexible_skill_duration` | 3 | `run_flexible_skill_duration_e0.py`, `_e1.py`, `_e1_aggregate.py` |
| `open_roster` | 3 | `run_open_roster_deployment_mixture_g16.py`, `_direct_g5.py`, `_high_churn_g9.py` |
| `recct` | 3 | `run_recct_a1_directed_edge_masked_update_binding.py`, `_a3_*`, `_b1_*` |
| `vnfc` | 3 | `run_vnfc_bpcr_b_explore.py`, `_bpcr_r02.py`, `_bpcr_r02_a0.py` |
| `cbsc` | 2 | `run_cbsc_omrc_b01.py`, `run_cbsc_omrc_b01_b1.py` |
| `scdmp` | 2 | `run_scdmp_graded_order_value_diagnostic_r01.py`, `run_scdmp_mf_rs_mk_b01.py` |
| `async_commitment_roster` | 1 | `run_async_commitment_roster_g3.py` |
| `continuous_roster_random_process` | 1 | `run_continuous_roster_random_process_g34.py` |
| `continuous_roster_reactive_reduction` | 1 | `run_continuous_roster_reactive_reduction_g35.py` |
| `continuous_roster_six_coordinate_cs` | 1 | `run_continuous_roster_six_coordinate_cs_g38.py` |
| `continuous_service_roster_proxy` | 1 | `run_continuous_service_roster_proxy_g17.py` |
| `count_preserving_roster` | 1 | `run_count_preserving_roster_g4.py` |
| `iteration5_process_semantics` | 1 | `run_iteration5_process_semantics.py` |
| `optimizer_entropy_exposure_boundary_relay` | 1 | `run_optimizer_entropy_exposure_boundary_relay.py` |
| `orbit` | 1 | `run_orbit_a2_verified_owner_binding_reachability.py` |
| `return_to_go_direction_balanced_full_actor` | 1 | `run_return_to_go_direction_balanced_full_actor_g31.py` |
| `runtime_capacity_continuous_roster` | 1 | `run_runtime_capacity_continuous_roster_g32.py` |
| `stage_c_semantics_provenance_audit` | 1 | `run_stage_c_semantics_provenance_audit.py` |
| `uav_charge_rotation` | 1 | `run_uav_charge_rotation_g2.py` |
| `uav_source_identifiability` | 1 | `run_uav_source_identifiability_g0.py` |
| `vsp03` | 1 | `run_vsp03_a1_event_certified_boundary_confirmation.py` |
| `vspc1` | 1 | `run_vspc1_a1_constrained_fourth_corner_logit_completion.py` |
| **Total** | **99** | |

Group sizes sum to 99, matching the `.py` count exactly. Grouping is by shared leading token(s) in the filename only; no cross-check was performed against `docs/research/RESEARCH_MAP.md`'s direction-id/impl mapping, so a single research direction may correspond to more than one prefix group above (e.g. several `continuous_roster_*` groups may or may not be the same direction) and this table should not be read as a direction count.

### 3.2 `hmasd_*.py` workflow tools (directly in `scripts/`)

Command: `git ls-files scripts | grep -E '^scripts/hmasd_[^/]+\.py$'` → **6** files:

| File |
| --- |
| `scripts/hmasd_file_fingerprint.py` |
| `scripts/hmasd_operator_result.py` |
| `scripts/hmasd_platform.py` |
| `scripts/hmasd_resource_preflight.py` |
| `scripts/hmasd_run.py` |
| `scripts/hmasd_science_capabilities.py` |

(This count excludes non-`.py` files with an `hmasd`-flavored name that live loose at `scripts/` top level but don't match this regex — see §3.4 — and excludes `scripts/schemas/hmasd_*.schema.json`, covered separately in §3.3.)

### 3.3 `scripts/schemas/`

Command: `git ls-files scripts/schemas` → **5** files:

| File |
| --- |
| `scripts/schemas/hmasd_accepted_result.schema.json` |
| `scripts/schemas/hmasd_engineering_state.schema.json` |
| `scripts/schemas/hmasd_operator_result_v1.schema.json` |
| `scripts/schemas/hmasd_research_state.schema.json` |
| `scripts/schemas/hmasd_run_manifest.schema.json` |

`schemas/` is the only tracked subdirectory under `scripts/` — confirmed via `git ls-files scripts | awk -F/ 'NF>2{print $2}' | sort -u`, which returns only `schemas`.

### 3.4 `scripts/dashboard/`

CLAUDE.md's claim was checked directly:

- `git ls-files scripts/dashboard | wc -l` → **0** tracked files.
- `git ls-files scripts | grep -i dashboard` → no output (no dashboard-named file is tracked anywhere under `scripts/`, including `scripts/hmasd_dashboard.py`, which is not present).
- `test -d scripts/dashboard` → the directory **does exist** on disk (working tree), and `ls -la scripts/dashboard` shows only `.` and `..` — no files or subdirectories.

**Verdict: the claim holds.** `scripts/hmasd_dashboard.py` is not tracked (consistent with "was removed"), and `scripts/dashboard/` exists as an empty directory in the working tree with zero tracked contents ("empty leftover").

### 3.5 Remaining files (not `run_*`, not `hmasd_*.py`, not `schemas/`)

No subdirectories other than `schemas/` exist under `scripts/` (per the `awk -F/ 'NF>2{print $2}'` check above).

**Loose top-level `scripts/*.py` files not matching `run_*` or `hmasd_*`** — 13 files, via `git ls-files scripts | grep -E '^scripts/[^/]+\.py$' | grep -vE '^scripts/(run_|hmasd_)'`:

| File |
| --- |
| `scripts/analyze_r39a_fixed_hmasd_anchor.py` |
| `scripts/analyze_stage_c_skill_semantics.py` |
| `scripts/codex_cost_role_weekly.py` |
| `scripts/collect_good_states.py` |
| `scripts/orbit_owner_freeze_evidence.py` |
| `scripts/rollout_and_collect.py` |
| `scripts/screen_continuous_roster_td0_g18.py` |
| `scripts/screen_direction_balanced_full_actor_g30.py` |
| `scripts/screen_fast_policy_anchored_residual_g19.py` |
| `scripts/screen_fast_slow_separated_credit_g18.py` |
| `scripts/screen_return_to_go_direction_balanced_full_actor_g31.py` |
| `scripts/train_vae.py` |
| `scripts/uav_g0_artifact_io.py` |

**Non-`.py` top-level files** — 7 files (all at `scripts/` top level, none matching `run_` for the `.sh`/`.ps1` ones already listed in §3.1 where applicable):

| File | Type |
| --- | --- |
| `scripts/export_gemini_live_response.ps1` | PowerShell |
| `scripts/hmasd-resource-preflight.ps1` | PowerShell (note hyphen, not underscore — does not match the `scripts/hmasd_[^/]+\.py$` regex in §3.2 on two counts: extension and separator) |
| `scripts/invoke_hmasd_hook.ps1` | PowerShell |
| `scripts/run_g_info_objective_local_cuda.ps1` | PowerShell (also counted in §3.1's 103 `run_`-prefixed total) |
| `scripts/run_hmasd_currentenv_baseline_cloud_64env.sh` | Shell (also counted in §3.1) |
| `scripts/run_r39a_fixed_hmasd_anchor.sh` | Shell (also counted in §3.1) |
| `scripts/run_s7s1_local_overnight.ps1` | PowerShell (also counted in §3.1) |

### 3.6 Hard-coded absolute Windows paths

**Forward-slash form** — `git grep -n "C:/Users" -- scripts`:

| File:Line | Matched path | Notes |
| --- | --- | --- |
| `scripts/run_flexible_skill_duration_e0.py:21` | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` | Matches the documented main env interpreter; appears in a comment/docstring-style usage example. |
| `scripts/run_flexible_skill_duration_e1.py:28` | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` | Same, main env. |
| `scripts/run_flexible_skill_duration_e1_aggregate.py:22` | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe` | Same, main env. |
| `scripts/run_ucope_structural_competence_certificate.py:31` | `C:/Users/fires/AppData/Local/Programs/Python/Python311/python.exe` | Not one of the two documented conda interpreters — a third, separate Python 3.11 install path. Assigned to `FROZEN_PYTHON_EXECUTABLE` alongside a sibling `FROZEN_PROJECT_ROOT = Path("C:/Projects/HMASD")` (line 29, not counted here since it doesn't contain `C:/Users`). |
| `scripts/run_vnfc_bpcr_r02_a0.py:166` | `C:/Users/fires/.conda/envs/hmasd-amd-cpu/Lib/site-packages` | Main env, `sys.path.append:` value inside a string. |
| `scripts/run_vnfc_bpcr_r02_a0.py:238` | `C:/Users/fires/.conda/envs/hmasd-amd-cpu` | Main env, assigned to `python_prefix`. |

6 matches, 5 distinct files.

**Backslash form** — `git grep -n 'C:\\Users' -- scripts`:

| File:Line | Matched path | Notes |
| --- | --- | --- |
| `scripts/run_g_info_objective_local_cuda.ps1:2` | `C:\Users\wu\.conda\envs\SB3\python.exe` | Neither documented conda env — different username (`wu`), different env name (`SB3`), default `-Python` parameter value. |
| `scripts/run_s7s1_local_overnight.ps1:2` | `C:\Users\wu\.conda\envs\SB3\python.exe` | Identical value, same role, different file. |

2 matches, 2 distinct files.

**Combined total across both forms: 8 matched lines in 7 distinct files** (`run_vnfc_bpcr_r02_a0.py` contributes 2 lines). Of the 8: 5 reference the documented main env (`hmasd-amd-cpu`), 1 references an undocumented standalone Python 3.11 install, and 2 reference an undocumented `SB3` conda env under a different user profile (`wu`). None reference the documented `hmasd-science-tools` env.

### 3.7 Size

Command: `git ls-files -z scripts | xargs -0 stat -c %s 2>/dev/null | awk '{s+=$1} END{print s+0}'` → **3,236,933 bytes** (≈3.09 MiB) total tracked under `scripts/`.

Three largest tracked files, via `git ls-files -z scripts | xargs -0 stat -c '%s %n' 2>/dev/null | sort -rn | head -3`:

| Rank | Size (bytes) | File |
| --- | ---: | --- |
| 1 | 188,226 | `scripts/run_vnfc_bpcr_b_explore.py` |
| 2 | 128,074 | `scripts/run_uav_charge_rotation_g2.py` |
| 3 | 123,636 | `scripts/run_continuous_roster_native_six_g31_phase_a_shadow_baseline_module_reduction_g51.py` |

---

## 4. Tests

### Top-level `*_test.py` files

Command: `git ls-files tests | grep -E '^tests/[^/]+_test\.py$' | wc -l` → **107** tracked files
directly at `tests/` top level (not in a subdirectory), all following the `<name>_test.py`
convention CLAUDE.md describes for `tests/` (as opposed to the `test_*.py` convention used one level
down under `tests/experiments/candidates/`). Representative sample from the full listing:
`tests/analyze_r39a_fixed_hmasd_anchor_test.py`, `tests/continuous_alice_bob_entrypoints_test.py`,
`tests/experiment_launcher_paths_test.py`, `tests/flexible_skill_duration_d2_test.py`,
`tests/flexible_skill_duration_e1_test.py`, `tests/ha_ctse_process_stage_c_test.py`,
`tests/ha_ctse_test.py`, `tests/hmasd_resource_preflight_test.py`,
`tests/hmasd_rnn_sequence_test.py`, and 17 files matching the
`ha_ctse_process_continuous_roster_native_six_g31_*_test.py` naming family alone.

### `tests/experiments/candidates/<impl>/`

Command: `ls tests/experiments/candidates` → **48** directories. Per-directory `test_*.py` counts via
`git ls-files tests/experiments/candidates/<d> | grep -c 'test_.*\.py$'`:

| Test directory | `test_*.py` count |
| --- | ---: |
| `acvc` | 1 |
| `capability_bound_semantic_currentness` | 5 |
| `capability_bound_semantic_currentness_learnability_r01` | 8 |
| `capability_bound_semantic_currentness_omrc_b01` | 23 |
| `capability_bound_semantic_currentness_online` | 1 |
| `commitment_residual_triggered_options_common_history_gate_r01` | 12 |
| `degraded_incumbent_shadow_handover_rbhr_r05` | 4 |
| `degraded_incumbent_shadow_handover_rbhr_r06` | 8 |
| `dual_epoch_receipt_survival` | 3 |
| `ebcr_variable_k` | 4 |
| `ec4g_r1` | 6 |
| `eociv_lite` | 13 |
| `expressibility_gated_renewal_credit_relay` | 1 |
| `finite_resource_relational_inductive_efficiency` (own level, excl. `b01/`) | 17 |
| `finite_resource_relational_inductive_efficiency/b01/` (nested) | 17 |
| `finite_semantic_boundary_support` | 0 |
| `folr_core` | 8 |
| `metric_ground_transport_allocation` | 3 |
| `opportunity_normalized_lease_gated_rebinding` | 13 |
| `optimizer_entropy_exposure_boundary_relay` | 1 |
| `orbit_owner_match` | 5 |
| `orbit_shadow_read` | 2 |
| `recct_lite` | 5 |
| `renewal_indexed_score_plasticity` | 17 |
| `roster_consistent_latent_exploration` | 1 |
| `roster_consistent_latent_exploration_b2` | 1 |
| `roster_consistent_latent_exploration_cpc` | 1 |
| `roster_consistent_latent_exploration_pcpv` | 3 |
| `roster_consistent_latent_exploration_tbcfv` | 10 |
| `roster_smf` | 1 |
| `scdmp_variable_k` (flat, no nested subdirs) | 36 |
| `scope_1s` | 1 |
| `semantic_graphon_shared_policy_rg2z_r03` | 1 |
| `semantic_graphon_shared_policy_rscf_gate_a` | 1 |
| `semantic_graphon_shared_policy_rscf_r01` | 6 |
| `ucope` (own level, excl. subdirs below) | 44 |
| `ucope/competence_first_scout_r01/` (nested) | 7 |
| `ucope/conditioning_discriminator_r01/` (nested) | 2 |
| `ucope/contextual_paid_acquisition_r01/` (nested) | 10 |
| `variable_n_fleet_churn` | 2 |
| `variable_n_fleet_churn_b_explore` | 6 |
| `variable_n_fleet_churn_bpcr_r09` | 7 |
| `variable_n_fleet_churn_r02` | 9 |
| `voronoi_quadrature_field_policy_r05_measurement` | 1 |
| `vqfp_frrie_action_codec` | 2 |
| `vqfp_vnpa_r03` | 1 |
| `vsp_02` | 10 |
| `vsp_03` | 1 |
| `vsp_04` | 1 |
| `vsp_05` | 7 |
| `vsp_06_mssr` | 9 |
| `vsp_c1` | 1 |

Notes on nesting shape:
- `scdmp_variable_k` has 10 nested sub-implementations under `experiments/candidates/` but its test
  directory is **flat** — 36 `test_*.py` files sit directly under
  `tests/experiments/candidates/scdmp_variable_k/` with no per-sub subdirectories (filenames encode
  the sub via prefix, e.g. `test_tbcc_*.py` for `target_bound_competent_controller_order_value`,
  `test_mf_rs_mk_*.py` for `multifoundation_reachable_order_value`, `test_fceov_*.py` for
  `foundation_conditioned_event_order_value`) — matching PROJECT_MAP.md's "flattened with
  underscores" description.
- `ucope` is a **mixed** case: 44 loose `test_*.py` files sit directly under
  `tests/experiments/candidates/ucope/`, but three of its four nested sub-implementations *also* have
  their own nested test subdirectories (`competence_first_scout_r01/`, 7 files;
  `conditioning_discriminator_r01/`, 2 files; `contextual_paid_acquisition_r01/`, 10 files) — the
  fourth sub, `variable_k_paid_probe_r01_r03`, has no nested test subdirectory; its tests are among
  the 44 loose files (`test_variable_k_paid_probe_r01_r03_s0.py`, `_s1.py`, `_s2.py`,
  `_production.py`).
- `finite_resource_relational_inductive_efficiency` mirrors its experiments-side `b01/` nesting with
  its own `tests/.../finite_resource_relational_inductive_efficiency/b01/` directory (17 files),
  alongside 17 more loose `test_*.py` files at its own level plus a `conftest.py` at both levels (see
  below) — this is the one candidate whose test nesting exactly mirrors its implementation nesting.

**Mismatches between `tests/experiments/candidates/` and `experiments/candidates/`** (48 test dirs vs
53 implementation dirs, `ls` compared by name):

Test directories with **no matching implementation directory at the same name**:
- `tests/experiments/candidates/capability_bound_semantic_currentness_omrc_b01/` — the real
  implementation is nested one level deeper at
  `experiments/candidates/capability_bound_semantic_currentness/omrc_b01/`; the test path flattens
  the nesting with an underscore, exactly the case CLAUDE.md's RESEARCH_MAP.md section calls out.
- `tests/experiments/candidates/capability_bound_semantic_currentness_online/` — same pattern,
  implementation at `experiments/candidates/capability_bound_semantic_currentness/online/`. (This
  second flattened case is not the one CLAUDE.md's own worked example names — CLAUDE.md names only
  the `omrc_b01` case.)

Implementation directories with **no matching test directory at the same name** (i.e. present under
`experiments/candidates/` but absent, under that exact name, from `tests/experiments/candidates/`):
- `commitment_residual_triggered_options` (only its `_common_history_gate_r01` sibling has a test dir)
- `covariance_calibrated_information_clock` (no test directory at all, despite having a `README.md`
  and its own `tests/` sub-tree per §2)
- `degraded_incumbent_shadow_handover_rbhr_r05` — **has** a matching test dir (4 files); not a
  mismatch, included here only to note both r05 and r06 have separate test dirs unlike other
  paired-variant cases below
- `semantic_graphon_shared_policy` (base) and `semantic_graphon_shared_policy_r06` — neither has a
  test directory; only `_rg2z_r03`, `_rscf_gate_a`, and `_rscf_r01` do
- `variable_n_fleet_churn_b2` and `variable_n_fleet_churn_b3` — no test directories (siblings
  `variable_n_fleet_churn`, `_b_explore`, `_bpcr_r09`, `_r02` all do)
- `voronoi_quadrature_field_policy` (base) — no test directory; only `_r05_measurement` has one

`finite_semantic_boundary_support`'s test directory **exists on disk** (`ls -la` shows only `.`, `..`,
and an untracked `__pycache__/`) but is **empty of tracked files** — `git ls-files
tests/experiments/candidates/finite_semantic_boundary_support` returns nothing, so it counts as
present-but-content-free rather than a true absence.

### `tests/skills/`

Command: `git ls-files tests/skills` → **3** tracked files: `hmasd_chatgpt_pro_transport_test.py`,
`hmasd_pro_conversation_binding_test.py`, `hmasd_pro_research_prompt_author_test.py`. (A fourth file,
`tests/skills/hmasd_workflow_outsource_test.py`, exists on disk right now but is untracked — see §1
and §7.)

### `tests/fixtures/`

Command: `ls tests/fixtures` → 9 subdirectories, tracked counts via
`git ls-files tests/fixtures/<sub> | wc -l`:

| Subdirectory | Tracked files |
| --- | ---: |
| `dish_rbhr_r05` | (counted among fixture set; not separately re-verified beyond directory listing) |
| `flexible_skill_duration_d2` | " |
| `hmasd_external_review` | tracked, and this subtree's `.json` files and `prompts/*.md` are pinned `text eol=lf` per `.gitattributes` |
| `hmasd_phase4` | " |
| `hmasd_portfolio` | " |
| `hmasd_recovery` | " |
| `hmasd_science` | tracked; `.gitattributes` pins `text eol=lf` on this whole subtree |
| `hmasd_state` | " |
| `hmasd_worktree` | " |

(Per-subdirectory exact tracked-file counts were not individually re-run as a separate command in
this pass beyond confirming all 9 names exist; CLAUDE.md names exactly two fixture sets —
`tests/fixtures/hmasd_external_review` and `tests/fixtures/hmasd_science` — as `eol=lf`-pinned, which
both `.gitattributes` and the directory listing confirm are present. CLAUDE.md's phrase "the two
VNFC science cards a native loader byte-addresses" refers to files under
`docs/research/candidates/variable_n_fleet_churn/`, not this fixtures tree.)

### `conftest.py` locations (repo-wide)

Command: `git ls-files | grep -i conftest.py` → exactly **2** tracked files, both under the same
candidate, confirming CLAUDE.md's claim precisely:
- `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/conftest.py`
- `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/conftest.py`

No `conftest.py` exists anywhere else in the tracked tree (not at `tests/` top level, not under any
other candidate's test directory).

### Untracked files under `tests/` caused by ignore rules

Command: `git status --short --ignored tests | grep '^!!' | wc -l` → **47** ignored/untracked paths
reported under `tests/`. The listing is dominated by `__pycache__/` directories (one per test
directory that has been run at least once locally), e.g. `tests/__pycache__/`,
`tests/experiments/candidates/acvc/__pycache__/`,
`tests/experiments/candidates/capability_bound_semantic_currentness/__pycache__/`, …, plus one
non-`__pycache__` entry: `tests/experiments/candidates/finite_semantic_boundary_support/` itself is
listed as `!!` at the directory level (consistent with it holding no tracked files, only its
untracked `__pycache__/`). None of the 47 entries are untracked *source* `test_*.py`/`*_test.py`
files caused by the `test*.py` global-ignore rule specifically — that rule's practical effect is
neutralized for `tests/` by the `!tests/experiments/` and `!tests/experiments/**/*.py` re-includes
(and separately by `!tests/codex_semantic_mvp/`, `!tests/codex_context_lifecycle/`,
`!tests/codex_supervisor/`); the only currently-untracked test *source* files in the whole repo are
the 4 identified in §1/§7 (3 under `finite_resource_relational_inductive_efficiency/b01/` and 1 under
`tests/skills/`), and those are untracked because they are simply new/unadded, not because of an
ignore-rule mismatch.

### Stale `__pycache__` entries in `tests/`

Command: `ls tests/__pycache__ | wc -l` → **109** compiled entries at the top-level `tests/__pycache__`
directory (one or more `.pyc` per source module, across `cpython-310` and `cpython-311` variants).
Cross-checking two names sampled from that listing against tracked sources:
- `hmasd_codex_tasks_test.cpython-310-pytest-9.1.1.pyc` / `hmasd_codex_tasks_test.cpython-310.pyc` /
  `hmasd_codex_tasks_test.cpython-311-pytest-9.1.1.pyc` exist, but
  `git ls-files | grep -i hmasd_codex_tasks_test` returns **nothing** — the source test file no
  longer exists in the tracked tree at all. This directly corroborates CLAUDE.md's "Known staleness"
  claim that `hmasd_codex_tasks.py` (and by extension its test) is "gone," while the compiled
  bytecode artifact for its test persists locally.
- `hmasd_clerk_instruction_test.cpython-310-pytest-9.1.1.pyc` /
  `hmasd_clerk_instruction_test.cpython-311-pytest-9.1.1.pyc` similarly have no matching tracked
  source (`git ls-files | grep -i hmasd_clerk_instruction_test` returns nothing) — a second stale
  `__pycache__` entry for a test file that no longer exists in the tree. (A full enumeration of every
  stale basename among the 109 `__pycache__` entries was not separately re-run in this pass; these
  two were spot-checked and confirmed stale.)

### `--basetemp` directories under `temp/` and root

Command: `ls -d temp/pytest* .tmp_pytest_* .pytest_tmp_* 2>/dev/null | wc -l` → **819** combined.
Broken down:
- `ls -d temp/pytest* | wc -l` → **789** directories/files directly under `temp/` matching the
  `pytest*` prefix (sample: `temp/pytest`, `temp/pytest-b0-final-unit`,
  `temp/pytest-b0-raw-evidence-full`, `temp/pytest-b01-bounded`, `temp/pytest-b01-cleanup-bounded`,
  …) — this is the dominant location for `--basetemp` output today, using the flat
  `temp/pytest-<slug>` naming CLAUDE.md notes as the "dominant" pattern, not the nested
  `temp/directions/<direction-id>/test/<run-tag>` layout the standard prescribes.
- Root `.tmp_pytest_*`: **22** (also reported in §7).
- Root `.pytest_tmp_*` (plus the bare `.pytest_tmp`): **9** (also reported in §7).

None of these 819+ directories were opened; only their names were listed, consistent with the task's
caution against recursing into `temp/`.

---

## 5. Agent configuration and control plane

Command basis: `git ls-files <path>`, `git check-ignore -v`, `ls -la`, `wc -c`,
`git log -1 --format=%cd --date=short -- <path>`.

| Surface | Tracked? | Size / count | Last commit |
| --- | --- | --- | --- |
| `AGENTS.md` (root) | tracked | 7,505 bytes on disk (per `ls -la`); only nested `AGENTS.md` in the whole repo (`git ls-files \| grep -i agents.md$` returns exactly `AGENTS.md`) | 2026-09-01 |
| `CLAUDE.md` (root) | tracked | 20,497 bytes on disk; only nested `CLAUDE.md` in the whole repo tracked set (`git ls-files \| grep -i claude.md$` returns exactly `CLAUDE.md` — two other files matching the substring, `docs/external-review/R27_G2_design_review_20260712_Claude.md` and `docs/external-review/legacy/HMASD_HACTSE_research_review_20260701_Claude.md`, are review documents whose filenames merely contain "Claude", not project-instruction files) | 2026-09-01 |
| `.codex/config.toml` | tracked | 2,593 bytes | 2026-08-30 |
| `.codex/agents/*.toml` | tracked | 16 files: `hmasd-cm-scout.toml`, `hmasd-cm.toml`, `hmasd-design-reviewer.toml`, `hmasd-direction-manager.toml`, `hmasd-em.toml`, `hmasd-experiment-operator.toml`, `hmasd-general-leaf.toml`, `hmasd-implementer.toml`, `hmasd-research-critic.toml`, `hmasd-research-innovator.toml`, `hmasd-research-principles-analyst.toml`, `hmasd-research-scout.toml`, `hmasd-reviewer.toml`, `hmasd-routine-implementer.toml`, `hmasd-verifier.toml`, `hmasd-workflow-designer.toml` | 2026-09-03 (repo-wide `.codex/` last-touch) |
| `.agents/skills/` | tracked | 15 tracked files across `hmasd-chatgpt-pro-transport/`, `hmasd-portfolio-task/`, `hmasd-pro-research-prompt-author/`, `hmasd-workflow-outsource/` | 2026-09-03 |
| `.agents/third_party/` | tracked | 24 tracked files: `ask-matt/`, `grill-me/`, `grilling/`, `implement/`, `setup-matt-pocock-skills/`, `tdd/`, `to-spec/`, `to-tickets/` (each with `SKILL.md` + `agents/openai.yaml` + assorted reference `.md`) | 2026-09-03 |
| `.claude/` (root-level) | **untracked, ignored** (`.gitignore:95 /.claude/`) | On-disk contents: `scheduled_tasks.lock` (124 bytes) and `worktrees/` (5 subdirectories, see §6) | 2026-08-24 (last tracked-history touch, predates the ignore) |
| `.remember/` | **untracked, not ignored** (has its own local `.remember/.gitignore`) | `archive.md`, `now.md`, `recent.md`, `remember.md`, `today-*.done.md`/`today-2026-09-03.md`, plus `logs/` and `tmp/` subdirs | n/a (never committed) |
| `.github/` | absent | `ls .github` → "No such file or directory" | n/a |
| `.cursor/`, `.windsurf/`, `.copilot/` | absent | all three return "No such file or directory" | n/a |

No nested `AGENTS.md` or `CLAUDE.md` exists anywhere else in the tracked tree — both control files
are single, root-level documents.

---

## 6. Worktrees and branches

Command: `git worktree list`; `git branch --merged main`; `git branch -a | wc -l`;
`git for-each-ref --sort=-committerdate --format='%(refname:short) %(committerdate:short)' refs/heads | head -10`;
`git stash list | wc -l`; per-worktree HEAD date via
`git for-each-ref --format='%(refname:short) %(objectname:short) %(committerdate:short)' refs/heads`.

`git branch -a | wc -l` = **94**.
`git stash list | wc -l` = **4**.

### `git worktree list` (20 entries total, including the primary checkout)

| Worktree path | Branch | HEAD (short) | HEAD date | Location kind | Merged into `main`? |
| --- | --- | --- | --- | --- | --- |
| `C:/Projects/HMASD` | `main` | `a411fd870` | 2026-09-03 | primary checkout | — (is main) |
| `.claude/worktrees/agent-a5ae2957862d225cd` | `worktree-agent-a5ae2957862d225cd` | `04ca3b57f` | 2026-09-02 | inside repo | yes (`+` in `git branch --merged main`) |
| `.claude/worktrees/agent-a88287f2315bb99a0` | `worktree-agent-a88287f2315bb99a0` | `1f19d9eaf` | 2026-09-03 | inside repo, **locked** | no |
| `.claude/worktrees/agent-aeda939d06a5b4fea` | `worktree-agent-aeda939d06a5b4fea` | `665877730` | 2026-09-02 | inside repo | yes |
| `.claude/worktrees/agent-afe41c8fd8f898719` | `e1-age-input-20260902` | `39bf7e626` | 2026-09-03 | inside repo | no |
| `.claude/worktrees/control-plane-20260903` | `control-plane-revision-20260903` | `4ca97fd61` | 2026-09-03 | inside repo (this session's own worktree) | no |
| `C:/Projects/HMASD-app-server-availability-runtime` | `codex-app-server-availability-first-v1` | `5d71dc40e` | 2026-08-24 | sibling | no |
| `C:/Projects/HMASD-vnfc-debug-98c96af0` | (detached HEAD) `98c96af0f` | `98c96af0f` | 2026-09-01 | sibling | n/a (detached, no branch) |
| `C:/Projects/HMASD-worktrees/control-plane-free-20260824` | `codex/control-plane-free-20260824` | `07b3046e0` | 2026-08-24 | sibling (`HMASD-worktrees/`) | no |
| `C:/Projects/HMASD-worktrees/controlplane-engineering-native-chain-smoke-20260826-a` | `omp/controlplane/engineering/native-chain-smoke-20260826-a` | `ee06a078c` | 2026-08-25 | sibling | no |
| `C:/Projects/HMASD-worktrees/expressibility_gated_renewal_credit_relay` | `codex/expressibility_gated_renewal_credit_relay` | `2035cec86` | 2026-08-28 | sibling | **yes** |
| `C:/Projects/HMASD-worktrees/finite_semantic_boundary_support-engineering-bc2db89b-...` | `omp/finite_semantic_boundary_support/engineering/bc2db89b-...` | `35e658f55` | 2026-08-27 | sibling | no |
| `C:/Projects/HMASD-worktrees/fsbs-a394-runtime-v2` | `omp/finite_semantic_boundary_support/engineering/a394938d-runtime-v2` | `180e37e03` | 2026-08-27 | sibling | no |
| `C:/Projects/HMASD-worktrees/fsbs-c520-identity-v3` | `omp/finite_semantic_boundary_support/engineering/c520049b-identity-v3` | `27adce9af` | 2026-08-27 | sibling | no |
| `C:/Projects/HMASD-worktrees/legacy-control-plane-20260824` | `codex/legacy-control-plane-20260824` | `832d68dc3` | 2026-08-24 | sibling | no |
| `C:/Projects/HMASD-worktrees/mgtap-runtime-fb0b680a` | `omp/metric_ground_transport_allocation/git/b92ac060-...` | `3a373cf21` | 2026-08-27 | sibling | no |
| `C:/Projects/HMASD-worktrees/opportunity_normalized_lease_gated_rebinding` | `codex/opportunity_normalized_lease_gated_rebinding` | `2035cec86` | 2026-08-28 | sibling | **yes** |
| `C:/Projects/HMASD-worktrees/ucope-engineering-4b52642b-...` | `omp/ucope/engineering/f49bbbc8-...` | `346b2536e` | 2026-08-27 | sibling | no |
| `C:/Projects/HMASD-worktrees/ucope-engineering-s2c1` | `omp/ucope/engineering/s2c1` | `ee06a078c` | 2026-08-25 | sibling | **yes** |
| `C:/Projects/HMASD-worktrees/ucope-root-ucope-r03-complete-20260827-01-prep` | `omp/ucope/root/ucope-r03-complete-20260827-01-prep` | `50052d1e4` | 2026-08-27 | sibling | no |
| `C:/Projects/HMASD-worktrees/ucope-v3` | `codex/ucope-v3` | `8d4e9a3f3` | 2026-08-28 | sibling | **yes** |

### Ten most recent branches by commit date (`git for-each-ref --sort=-committerdate ... | head -10`)

```
main                                  2026-09-03
control-plane-revision-20260903       2026-09-03
worktree-agent-a88287f2315bb99a0      2026-09-03
e1-age-input-20260902                 2026-09-03
worktree-agent-afe41c8fd8f898719      2026-09-02
worktree-agent-a5ae2957862d225cd      2026-09-02
worktree-agent-aeda939d06a5b4fea      2026-09-02
codex/egrcr-2026-08-28-7-pilot        2026-08-29
omp/onlgr-b3-clean-successor-02       2026-08-28
codex/work-direction-portfolio-objective-start  2026-08-28
```

Fact check against `.gitignore`'s own comment: the comment at `.gitignore:120-121` states "Linked
Git worktrees live outside the checkout under `C:/Projects/HMASD-worktrees/`" — the actual
`git worktree list` output shows worktrees in **three** distinct locations, not one: inside the repo
under `.claude/worktrees/*` (5, ignored via `/.claude/`), directly as repo-root siblings
(`C:/Projects/HMASD-app-server-availability-runtime`, `C:/Projects/HMASD-vnfc-debug-98c96af0` — not
under a `-worktrees` suffix at all), and under `C:/Projects/HMASD-worktrees/*` (11) as the comment
describes.

---

## 7. Scratch and generated output

Commands used throughout: `ls <dir> | head -N` and `ls <dir> | wc -l` with a `timeout 15-30`
wrapper; `git status --short --ignored <path> | head` (aborted for `temp/` itself — see note); no
`find`/`du` recursion into `temp/` or `.tmp*` trees; nothing under `models/`, `results/`, `logs/`,
`runtime/`, `temp/` was opened.

- `temp/` top level: **1,158 entries** (`ls temp | wc -l`). First 40 (`ls temp | head -40`) are a mix
  of loose `*_admit_memory.json` resource-preflight receipts, `_verify_work_packet*` directories, and
  many `b01_*_pytest` / `b1_*` basetemp-style directories — i.e. `temp/` is not exclusively organized
  by the `temp/directions/<direction-id>/{exp,test}` convention PROJECT_MAP.md and RESEARCH_MAP.md
  describe; large amounts of loose, non-direction-keyed scratch sit directly at `temp/`'s own top
  level.
- `temp/directions/` present ids: **41** (`ls temp/directions | wc -l`), listed in full:
  `active_post_churn_population_flow_identification`, `acvc`, `capability_bound_semantic_currentness`,
  `commitment_residual_triggered_options`, `control-plane`, `covariance_calibrated_information_clock`,
  `crto`, `degraded_incumbent_shadow_handover`, `dual_epoch_receipt_survival`, `ec4g_r1`,
  `eociv_lite`, `event_triggered_budgeted_cooperative_renewal`,
  `expressibility_gated_renewal_credit_relay`, `field_slot_coordination`,
  `finite_semantic_boundary_support`, `flexible_skill_duration`,
  `metric_ground_transport_allocation`, `opportunity_normalized_lease_gated_rebinding`,
  `optimizer_entropy_exposure_boundary_relay`, `orbit_shadow_read`, `path-normalization`,
  `recct_lite`, `renewal_indexed_score_plasticity`, `roster_consistent_latent_exploration`,
  `roster_smf`, `scope_1s`, `semantic_graphon_shared_policy`,
  `semigroup_consistent_duration_model_policy`, `ucope`, `vap_folr_core`, `variable_n_fleet_churn`,
  `voronoi_quadrature_field_policy`, `vsp_02`, `vsp_03`, `vsp_04`, `vsp_05`, `vsp_06_mssr`, `vsp_c1`,
  `workflow`, `workflow-codex-migration`. This set is **41 ids against 22 current directions in
  RESEARCH_MAP.md** — it contains legacy/abbreviated ids not in the current 22 (e.g. `crto` as a
  separate abbreviation alongside the full `commitment_residual_triggered_options`,
  `active_post_churn_population_flow_identification` which RESEARCH_MAP.md itself marks as having no
  live candidate code), and non-direction scratch buckets that are not direction ids at all:
  `control-plane`, `path-normalization`, `workflow`, `workflow-codex-migration`.
- `.tmp/` top level: **103 entries** (`ls .tmp | wc -l`); sample of names from `ls -la .tmp | head -40`
  shows short task-slug directories (`adj-related`, `bprime-codex-full`, `bprime-compact`, …,
  `cm_scdmp_b01_final`, `cm_scdmp_final_green1`, `cmrefs-green`, `final-cases`, …), dated 2026-08-26
  through 2026-09-01.
- Root `.tmp_pytest_*` directories: **22** (`ls -d .tmp_pytest_* | wc -l`).
- Root `.pytest_tmp*` directories (including the plain `.pytest_tmp`): **9**
  (`ls -d .pytest_tmp_* .pytest_tmp | wc -l`).
- `models/`: **absent** on disk (`[ -d models ]` false). Listed in `.gitignore:80` (`models/`) as a
  denylist rule even though the directory does not currently exist.
- `results/`: **absent** on disk. Listed in `.gitignore:81` (`results/`).
- `logs/`: **present**, tracked (24 files — see §1), contains dated run subdirectories such as
  `controller_cpu_stage2_nonformal_20260722`,
  `formal_continuous_roster_native_six_g31_channel_scale_normalization_attribution_g44_cpu_20260727_96e35dd_r1`,
  `r29_t10_paired_320k_20260714_010026`, …, `r38_cts_access_320k_20260715_140641_retry2`, dated
  2026-07-14 through 2026-08-25 by directory mtime.
- `runtime/`: **present**, ignored, contains `codex-semantic-mvp/` and `hmasd-control-plane/`
  subdirectories.
- Untracked-but-not-ignored items at repo root (`git status --short | grep '^??' | head -30`, full
  list, 8 entries total repo-wide): `config.toml.backup_20260903_131348.toml`; three new `.py` files
  under `experiments/candidates/finite_resource_relational_inductive_efficiency/b01/`
  (`b4_induction_pilot.py`, `training_runner.py`, `training_shards.py`); three matching `test_*.py`
  files under the mirrored `tests/experiments/candidates/.../b01/` path; and
  `tests/skills/hmasd_workflow_outsource_test.py`.
- `git status --short --ignored temp` was attempted and produced Windows permission-denied warnings
  for several `temp/b01_*_pytest/` subdirectories before being interrupted (not fully enumerable
  cheaply given 1,158+ top-level entries); it was not run to completion — `ls`/`git ls-files` counts
  above are the basis for the `temp/` facts instead, per the task's caution against expensive
  recursion into this tree.

---

## 8. Documentation tree

Command: `git ls-files docs/<sub> | wc -l` per immediate subdirectory of `docs/`; then the same one
level deeper for `docs/research/<sub>`.

### `docs/` immediate subdirectories (tracked file counts)

| Subdirectory | Tracked files | Declared authority in CLAUDE.md's navigation table? |
| --- | --- | --- |
| `docs/Claude_docs/` | 31 | yes (documented convention; not itself an authority row but named explicitly) |
| `docs/agents/` | 2 | no |
| `docs/archive/` | 16 | no |
| `docs/benchmarks/` | 6 | referenced as `docs/project/EFFICIENCY_PRACTICES.md`'s subject matter, not this path directly |
| `docs/external-review/` | 1,148 | yes (Collaboration/authority model row points to AGENTS.md, but external-review is named in PROJECT_MAP.md and CLAUDE.md prose) |
| `docs/migration/` | 0 (directory exists on disk, empty — `!docs/migration/*.md` re-include has nothing to re-include right now) | no |
| `docs/new/` | 16 | no |
| `docs/new-libs/` | 178 | no |
| `docs/operations/` | 2 | no |
| `docs/plans/` | 0 (directory exists on disk, empty) | no |
| `docs/project/` | 13 | yes — multiple rows (`PROJECT_MAP.md`, `PROBLEM_CACHE.md`, `EFFICIENCY_PRACTICES.md`, `ENGINEERING_ADDITIONS.md`) |
| `docs/report/` | 40 | no |
| `docs/research/` | 1,544 | yes — multiple rows (`RESEARCH_MAP.md`, `portfolio/PORTFOLIO.md`, `specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, `legacy/directions/`) |
| `docs/superpowers/` | 4 | no |
| (loose) `docs/SCIENTIFIC_CAPABILITY_LAYER_REQUIREMENTS.md` | 1 | no |

### `docs/research/` immediate subdirectories

| Subdirectory | Tracked files |
| --- | --- |
| `docs/research/RESEARCH_MAP.md` (file) | 1 |
| `docs/research/candidates/` | 723 |
| `docs/research/cdc/` | 135 |
| `docs/research/decisions/` | 10 |
| `docs/research/designs/` | 87 |
| `docs/research/legacy/` | 460 |
| `docs/research/literature/` | 12 |
| `docs/research/portfolio/` | 34 |
| `docs/research/review_packets/` | 7 |
| `docs/research/specs/` | 1 |
| `docs/research/workflow/` | 0 (empty on tracked content) |
| `docs/research/workflow-runs/` | 74 |

### Map/authority documents

| Document | Size | Last commit | One concrete claim checked against the tree |
| --- | --- | --- | --- |
| `docs/project/PROJECT_MAP.md` | 9,471 bytes | 2026-09-01 | Line 32-33 states: "`RESEARCH_MAP.md` is the per-direction inventory: it records **the 21 current direction keys**". `docs/research/RESEARCH_MAP.md` itself (read directly) states "This is the human navigation map for the repository's **22 current candidate directions**" and its table has 22 rows (APFI, ACVC, CBSC, CRTO, DISH, EC4G, EOCIV-lite, EGRCR, FRRIE, FSD, MGTAP, Orbit shadow read, RECCT-lite, RCLE, Scope-1s, SCDMP, UCOPE, VAP/FOLR core, VNFC, VSP-02, VSP-03, VSP-C1). **PROJECT_MAP.md's own "21" figure is stale relative to the file it is describing.** |
| `docs/research/RESEARCH_MAP.md` | 8,546 bytes | 2026-09-02 | Claims 22 current + 14 legacy directions (36 total); consistent with CLAUDE.md's "22 + 14 = 36 labels" statement. No staleness found against CLAUDE.md in a five-minute check, but see the PROJECT_MAP.md mismatch above and the `temp/directions/` mismatch in §7 (41 on-disk ids vs 22 current directions). |
| `CONCEPT_MAP.md` (root) | 19,449 bytes | never committed (untracked, `*.md`-ignored) | Per CLAUDE.md itself: "concepts 1–6 describe an entire task-database / lease-registry / return-witness control plane that no longer exists" — this claim was not independently re-verified against file content in this pass (file was not opened, per the task's document-reading scope for this inventory being about structure, not content re-litigation) but is recorded as CLAUDE.md's own stated staleness. |
| `LEARNING_LOG.md` (root) | 8,990 bytes | never committed | Same status as `CONCEPT_MAP.md` — untracked, personal document per CLAUDE.md. |
| `CODE_SCIENCE_INDEX.md` files | 61 total tracked paths matching `*CODE_SCIENCE_INDEX.md` (`git ls-files \| grep -i CODE_SCIENCE_INDEX.md \| wc -l` — counted from the listed paths) | varies | CLAUDE.md states "About 9 of the 21 directions also carry a `CODE_SCIENCE_INDEX.md`" — the actual count of *files* is 61 (many directions carry several dated/object-specific ones, e.g. `eociv_lite/` alone has 8, `vsp_02/` has 6), spread across `docs/research/candidates/` (ec4g_r1, eociv_lite, orbit_shadow_read, recct_lite, scope_1s, ucope, vap_folr_core, vsp_02, vsp_03, vsp_c1 = 10 directions), `docs/research/designs/` (17 files, mostly `CONTINUOUS_ROSTER_*` design docs unrelated to a current candidate directory), and `docs/research/legacy/directions/` (roster_smf, vsp_04, vsp_05, vsp_06_mssr = 9 files across 4 legacy directions). Directory-count (10) is close to CLAUDE.md's "~9" if `docs/research/designs/` entries are excluded, but the file-count (61) is far higher than a naive reading of "about 9" would suggest. |
| `IMPLEMENTATION_THRESHOLD.md` files | 11 total (`git ls-files \| grep -i IMPLEMENTATION_THRESHOLD.md`) | varies | CLAUDE.md states "roughly a third an `IMPLEMENTATION_THRESHOLD.md`" — 11 files span 8 unique candidate/legacy directories (capability_bound_semantic_currentness has 2: a base one and `CBSC_LR01_IMPLEMENTATION_THRESHOLD.md`); against 22 current directions that is 8/22 ≈ 36%, roughly consistent with "a third," though 3 of the 8 directories (`opportunity_normalized_lease_gated_rebinding`, `renewal_indexed_score_plasticity`, `voronoi_quadrature_field_policy`) are under `docs/research/legacy/directions/`, not current candidates. |

### `docs/Claude_docs/` layout

Tracked files (`git ls-files docs/Claude_docs`, 31 total, matching the top-level count above):
`README.md` (top level), then subdirectories `artifacts/` (2 files: a `.py` builder and an `.html`
output), `environment_design/` (1), `experiments/` (5: `E0_EXPOSURE_PROBE_SET_20260902.md`,
`E0_EXPOSURE_PROBE_SET_RESULT_20260902.md`, `E0_probe_set_sample_seed1.json`,
`E1_AGE_INPUT_20260902.md`, `E1_AGE_INPUT_RESULT_20260902.md`, `E2_INTERRUPTION_COST_SWEEP_20260903.md`
— 6 actually listed), `plans/` (10: `ADR_01_D2_POLICY_INTERRUPTION.md` through
`RESEARCH_ADVANCEMENT_PLAN_20260902.md`), `research_notes/` (1), `reviews/` (5), `toy_studies/` (2,
under `untied_k_n/`). This matches the `.gitignore:77` re-include comment: "Claude Code session
deliverables (reviews, research notes, design advice, toy studies)."

---

## 9. `.gitignore`

252 lines total (`wc -l .gitignore`).

### Structure summary

- **Lines 1-46**: unconditional denylist rules with no re-include — Python bytecode/build artifacts
  (`__pycache__/`, `*.py[cod]`, `dist/` — later re-included, `build/`, `*.egg-info/`), virtual-env
  dirs (`env/`, `venv/`, …), IDE dirs (`.idea/`, `.vscode/`), and a broad data/log denylist:
  `logs/`, `logs*/`, `tf-logs/`, `*.log`, `*.tfevents.*`, `*.csv`, `*.dat`, `*.out`, `*.pid`, `*.gz`,
  `*.zip`, `data/`.
- **Line 46**: `*.pdf` (global PDF denylist, no re-include block exists for it anywhere in the file).
- **Line 47**: `*.md` (global Markdown denylist) followed immediately (lines 48-136 roughly) by a very
  long, hand-maintained sequence of `!`-prefixed re-include rules, one area at a time:
  `!README.md`, `!CONTEXT.md`, `!AGENTS.md`, `!CLAUDE.md`, `!memory/*.md`, `!docs/project/*.md`,
  `!docs/agents/`, `!docs/report/*.md`, `!docs/plans/*.md`, `!docs/migration/`,
  `!tests/fixtures/hmasd_external_review/prompts/*.md`, `!docs/research/portfolio/**`,
  `!docs/external-review/directions/**`, `!docs/research/RESEARCH_MAP.md`,
  `!docs/research/cdc/**/*.md`, `!docs/research/designs/*.md`, `!docs/research/specs/*.md`,
  `!docs/research/candidates/**/*.md`, `!docs/research/legacy/directions/**/*.md`, a Codex-skills
  block (`!/.agents/...`), `!.codex/prompts/*.md`, several named single-file re-includes
  (R27_G2 design docs, external-review round directories, `!memory/LTM/*.md`, …), a literature-review
  block (`!docs/research/literature/n_k_many_agent_deep_dive/**/*.md`), a `docs/new-libs` block
  (`!docs/new-libs/*.md`, `!docs/new-libs/corpus/**/*.md` variants), and finally
  `!docs/Claude_docs/**`.
- **Line 53** area: `*.txt` denylist with 2 re-includes (`!/requirements_server.txt`,
  `!/requirements_sb3.txt`) plus one named script artifact
  (`!scripts/r27_g2_runtime_package_manifest.txt`).
- **Line 57-60**: `*.tar` denylist with one re-include (`!ref/hmasd.tar`), plus `ref/hmasd/` and
  `ref/OPT-main/` explicitly denied.
- **Line 61**: `*.png` denylist, no re-include block anywhere.
- **Lines 79-85**: generated model/result denylist — `models/`, `results/`, `*.pt`, `*.pkl`, `*.npy`,
  `evaluation/`.
- **Lines 87-108**: temp-file and cache denylist — OS/editor junk, `.pytest_cache/`,
  `.pytest_tmp*/`, `.pytest-*/`, `.codex_tmp_pytest*/`, `.tmp_pytest*/`, `.mypy_cache/`,
  `.ruff_cache/`, `.coverage*`, `htmlcov/`.
- **Lines 110-128**: the canonical local-scratch block — `/.tmp*`, `/artifacts/`, `/runtime/`,
  `/tmp/`, `/.charter/cache/`, `/temp/**` with exactly one re-include (`!/temp/README.md`), plus
  `/.cache/`, `/cache/`, `/scratch/`, `/work/`, `/worktrees/`, `/.worktrees/`.
- **Lines 131-252**: a long tail of narrower/one-off rules — candidate-local result/checkpoint
  patterns (`/experiments/**/RISP_*_RESUME_*/`, `RISP_*_RESULTS_*/`, `RISP_*_CHECKPOINTS_*/`,
  `RCLE_*_RESULTS_*/`), `*.npz`, `*.sqlite3`, root scratch (`/temp_*.json`, `tmp_pytest*/`,
  `pytest_tmp*/`), **the global `test*.py` rule** with its `tests/experiments/**`,
  `tests/codex_semantic_mvp/**`, `tests/codex_context_lifecycle/**`, `tests/codex_supervisor/**`
  re-includes, `*.doc`/`*.docx`, `debug/`, `temp_collection_log/`, `/local_research/`,
  `/runtime/codex-semantic-mvp/`, and finally a `dist/` re-include block (`!dist/`, `dist/*`,
  `!dist/remote_log_sync/`, `!dist/remote_log_sync/**`).

### Three concrete "silently ignored" cases

1. A new `*.md` file dropped anywhere under `docs/archive/`, `docs/benchmarks/`, `docs/new/`,
   `docs/operations/`, `docs/superpowers/`, or `docs/research/decisions/`, `docs/research/legacy/`
   (outside `legacy/directions/**`), or `docs/research/review_packets/`, or `docs/research/cdc/`
   (outside the `**/*.md` re-include's exact shape) — none of these paths have a `!`-re-include
   entry, so it would be silently ignored by the line-47 `*.md` rule despite `docs/` otherwise
   holding 3,001 tracked files. (Verified: `docs/archive/` holds 16 tracked files today, but none
   are `.md` — its content is tracked via other extensions or was force-added before the rule
   existed.)
2. A new plain file at repo root with a `.tmp` or root-scratch-shaped name, or any file placed
   directly under a fresh `temp/<anything>/` directory that isn't `temp/README.md`, is silently
   ignored by `/temp/**` (only the single file `temp/README.md` is re-included).
3. A new `*.png` or `*.pdf` anywhere in the repo (e.g. a diagram dropped next to a `DIRECTION.md`, or
   a downloaded paper under a research directory) is silently ignored — neither pattern has any
   re-include block anywhere in the 252-line file, unlike `*.md`, `*.txt`, and `*.tar` which each got
   one.

---

## 10. Sizes

### `git count-objects -vH`

```
count: 6
size: 57.29 KiB
in-pack: 70139
packs: 4
size-pack: 524.09 MiB
prune-packable: 0
garbage: 46
size-garbage: 716.10 MiB
```

(46 loose "garbage" objects — `tmp_pack_*` and `tmp_obj_*` files under `.git/objects/` — totaling
716.10 MiB, larger than the 524.09 MiB of legitimate packed history, were reported by
`git count-objects -vH` alongside a matching set of `warning: garbage found: .git/objects/...`
lines.)

### Tracked file total

`git ls-files | wc -l` = **4,944**.

### Tracked bytes by top-level directory

Command per directory: `git ls-files -z -- <dir> | xargs -0 stat -c %s | awk '{s+=$1} END{print s}'`
(root loose tracked files summed individually with `stat -c %s`).

| Directory | Tracked bytes |
| --- | --- |
| `docs/` | 395,807,472 (~377 MiB) |
| `logs/` | 59,236,866 (~56.5 MiB) |
| `experiments/` | 21,987,674 (~21.0 MiB) |
| `tests/` | 6,769,785 (~6.5 MiB) |
| `ha_ctse_process/` | 3,782,584 (~3.6 MiB) |
| `scripts/` | 3,236,933 (~3.1 MiB) |
| `root loose tracked files` (AGENTS.md, CLAUDE.md, README.md, main.py, config*.py, train_multiproc_config_1.py, .gitattributes, .gitignore, requirements*.txt, the Yang PDF) | 2,264,886 (~2.2 MiB) |
| `hmasd/` | 830,477 |
| `tools/` | 644,129 |
| `envs/` | 1,217,682 |
| `ref/` | 1,300,480 |
| `.agents/` | 231,818 |
| `manifold_hmasd/` | 100,627 |
| `.codex/` | 44,566 |
| `gnn_hmasd/` | 63,786 |
| `environments/` | 16,455 |
| `dist/` | 18,598 |
| `examples/` | 13,837 |
| `configs/` | 2,929 |
| `baselines/` | 857 |
| `.claude/` | 0 (untracked/ignored) |

`docs/`'s 377 MiB (measured via `git ls-files -z -- docs | xargs -0 stat -c %s`, working-tree byte
size) is driven by large tracked `RESULT.json` evidence files, not markdown — the three largest
tracked files anywhere in the repo were found there (`git ls-files -z docs | xargs -0 stat -c
'%s %n' | sort -rn | head`):

| File | Bytes |
| --- | --- |
| `docs/research/candidates/vsp_02/VSP02_B5R1_WINDOWS_RESOURCE_ADMISSION_RESULT.json` | 83,663,399 |
| `docs/research/candidates/vsp_02/VSP02_B4_SELF_GENERATED_CLOSED_LOOP_FEEDBACK_RESULT.json` | 75,634,958 |
| `docs/research/legacy/directions/opportunity_normalized_lease_gated_rebinding/ONLGR_B1_RESULT.json` | 45,186,023 |
| `docs/research/legacy/directions/optimizer_entropy_exposure_boundary_relay/OEER_BOUNDARY_RELAY_RESULT.json` | 29,231,031 |
| `docs/research/candidates/vsp_02/VSP02_B2_PAIRED_SHADOW_LEARNER_LOCALIZATION_RESULT.json` | 26,164,353 |
| `docs/research/candidates/vsp_02/VSP02_B3_LIFECYCLE_CREDIT_SIGN_BRIDGE_RESULT.json` | 24,251,654 |
| `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/formal_evidence/train_manifest.json` | 23,446,417 |
| `docs/external-review/rounds/20260728_g31_shared_baseline_conditioning_attribution_g45_formal_result_review/formal_evidence/evaluation_manifest.json` | 19,565,025 |
| `docs/research/candidates/ec4g_r1/EC4G_B1_LEAVE_RECEIPT_CONTENT_LEARNING_DISCRIMINATOR_RESULT.json` | 15,285,019 |

(`.gitignore` has no `*.json` rule anywhere, so these evidence files are tracked in full regardless
of size.) A cross-check with `git ls-tree -r -l HEAD | awk '{s+=$4} END{print s}'` — which sums Git's
own recorded blob sizes rather than restatting the working tree — returned 485,562,664 bytes
(~463.1 MB) total tracked repo-wide and ~386 MB for `docs/` alone, a few percent higher than the
working-tree `stat`-based figures above; the two measurement methods (working-tree `stat` vs. Git's
internal blob-size ledger) agree on the order of magnitude and on which files dominate, but not to
the byte, most plausibly from line-ending normalization differences between the checked-out files and
the stored blobs.

---

## Facts that surprised me

- `.git/objects/` currently holds **716.10 MiB of "garbage"** (46 loose `tmp_pack_*`/`tmp_obj_*`
  objects) — more than the 524.09 MiB of legitimate packed history — per
  `git count-objects -vH`'s own `garbage:`/`size-garbage:` fields and matching
  `warning: garbage found: ...` lines.
- `docs/` is **~377-386 MiB** of tracked content (depending on measurement method — working-tree
  `stat` vs. Git's internal blob-size ledger) despite `*.md` being the dominant `.gitignore` rule for
  that tree — the actual weight comes from un-ignored `*.json` result-evidence files (no `*.json`
  rule exists anywhere in `.gitignore`), the largest single tracked file in the whole repo being
  `docs/research/candidates/vsp_02/VSP02_B5R1_WINDOWS_RESOURCE_ADMISSION_RESULT.json` at roughly
  81.5-83.7 MB.
- `temp/directions/` (the canonical per-direction scratch root per PROJECT_MAP.md/RESEARCH_MAP.md)
  currently holds **41 ids** against only **22 current directions** in RESEARCH_MAP.md — it includes
  clearly non-direction scratch buckets (`control-plane`, `path-normalization`, `workflow`,
  `workflow-codex-migration`) and an abbreviated duplicate (`crto` alongside the full
  `commitment_residual_triggered_options`) living at the same directory level as real direction ids.
- `docs/project/PROJECT_MAP.md` itself states RESEARCH_MAP.md "records the 21 current direction
  keys," but `docs/research/RESEARCH_MAP.md` (read directly) says "22 current candidate directions"
  and its table has 22 rows — the map-of-maps document is stale about the very count it exists to
  report.
- Both `scdmp_variable_k/` and `ucope/` under `experiments/candidates/` have **more sub-implementation
  directories than CLAUDE.md claims** — 10 vs. the stated "seven," and 4 vs. the stated "three."
  Similarly, the actual `run_*.py` script count is **99, not CLAUDE.md's stated 83** — a 16-script
  gap.
- `logs/` and `dist/` are both named by *unconditional denylist* rules in `.gitignore` (`logs/`,
  `logs*/`, and `dist/*`), yet both are tracked directories (24 and 5 files respectively) — `dist/`
  has an explicit later re-include (`!dist/` + `!dist/remote_log_sync/**`), but `logs/`'s 24 tracked
  files exist with **no re-include rule anywhere in the file**, meaning they were added before the
  rule existed (or force-added) and Git's ignore rules never retroactively untrack them.
- `git worktree list` shows worktrees in **three different physical locations** — inside the repo
  under `.claude/worktrees/*` (5), as direct repo-root siblings with no `-worktrees` suffix
  (`C:/Projects/HMASD-app-server-availability-runtime`, `C:/Projects/HMASD-vnfc-debug-98c96af0`), and
  under the documented `C:/Projects/HMASD-worktrees/*` convention (11) — even though `.gitignore`'s
  own comment (lines 120-121) describes only the third location as where "Linked Git worktrees live."
- `CONCEPT_MAP.md` and `LEARNING_LOG.md` at repo root are **19,449 and 8,990 bytes respectively on
  disk but have never been committed** (`git log -1` returns nothing) — they are pure local files
  that happen to sit at the repository root next to tracked control documents.
- `scripts/dashboard/` exists on disk as a genuinely **empty directory** (no files, no
  subdirectories) with zero tracked content, and `scripts/hmasd_dashboard.py` is confirmed absent —
  CLAUDE.md's specific characterization of both facts holds exactly as stated.
- `tests/__pycache__/` contains compiled bytecode (`hmasd_codex_tasks_test.cpython-*.pyc`,
  `hmasd_clerk_instruction_test.cpython-*.pyc`) for test source files that no longer exist anywhere
  in the tracked tree — stale local artifacts directly corroborating CLAUDE.md's "Known staleness"
  claim that the underlying workflow-layer modules are "gone."

---

*Sections 2 and 3 (Code modules, Scripts) were produced by delegated sub-agents covering the same
factual scope and command discipline as the rest of this document, then inserted above verbatim.
Section 4 (Tests) was gathered and written directly. All other sections were gathered and written
directly against the repository at `C:\Projects\HMASD`.*
